# Motor de Recomendaciones Híbrido — EkiSystem

Este documento detalla el funcionamiento interno del Motor de Recomendaciones del proyecto EkiSystem. El sistema utiliza una arquitectura **Offline-First**, donde cálculos matemáticos pesados se ejecutan en segundo plano mediante _Jobs_ y los resultados se almacenan en la base de datos para servirse rápidamente a través de la API.

---

## 1. Visión General: Arquitectura Offline-First

```
[Jobs Offline — en segundo plano]           [Online — tiempo real]
        │                                           │
  nlp → metricas → clustering → recomendaciones    │
        │                           │               │
        └─────── Tabla RecomendacionGenerada ───────┘
                                                    │
                                              Usuario abre la app
                                        (solo un SELECT rápido a BD)
```

El principio central es simple: **ningún algoritmo pesado corre durante una petición del usuario**. Todo se pre-calcula offline, se guarda en la base de datos, y el endpoint de Feed solo lee esos resultados.

---

## 2. Algoritmos del Motor

### A) Similitud Coseno — Filtrado por Contenido
**Tecnología:** `scikit-learn` — `cosine_similarity`  
**Archivo:** [`backend/engine/content_filter.py`](../backend/engine/content_filter.py)

**¿Qué hace?** Compara el `vector_preferencias` del usuario (sus gustos registrados en el onboarding e interacciones) con el `vector_caracteristicas` del establecimiento (categorías, etiquetas, precio, tipo).

Ambos vectores tienen **dimensión 22** (número de dimensiones definido por los centroides de clusters). El resultado es un número entre `0.0` (sin relación) y `1.0` (perfecto match).

**¿Por qué Coseno y no Euclidiana o Pearson?**
- La *Distancia Euclidiana* penaliza injustamente a los usuarios con muchas preferencias contra establecimientos con pocos tags, porque mide magnitud. El Coseno solo mide el **ángulo** (orientación), ignorando la magnitud.
- La *Correlación de Pearson* asume escalas de calificación (1 a 5 estrellas) y resta la media. Nuestros vectores usan presencias fraccionales (0 a 1), sin el sesgo del "usuario que califica todo bajo" que Pearson corrige.

**Normalización:** `cosine_similarity` de scikit-learn aplica normalización L2 automáticamente en tiempo de ejecución. No es necesario pre-normalizar manualmente.

---

### B) K-Means Clustering — Machine Learning No Supervisado
**Tecnología:** `scikit-learn` — `KMeans`, `silhouette_score`  
**Archivo:** [`backend/jobs/clustering.py`](../backend/jobs/clustering.py)

**¿Qué hace?** Divide a la base de usuarios en "Tribus" (Clusters) con comportamientos y gustos similares. Hace lo mismo para los establecimientos.

**¿Cómo elige el número de grupos (K)?** Itera sobre varios valores de K y calcula el **Silhouette Score** (coeficiente de silueta) para cada uno. Este score mide qué tan bien separados están los grupos: un valor cercano a `1.0` indica grupos bien definidos, cercano a `0` indica solapamiento. El K con el mejor score es el que se usa.

**¿Por qué K-Means y no otro algoritmo?**
- **DBSCAN** no requiere especificar K, pero es sensible a la densidad de datos y produce clusters de tamaño muy variable, lo que complica el filtrado colaborativo posterior.
- **Hierarchical Clustering** genera dendrogramas interpretativos, pero es `O(n²)` en memoria — no escalaría con miles de usuarios.
- **K-Means** es `O(n·k·i)` (lineal en usuarios), converge rápido y produce clusters de tamaño uniforme, ideal para el filtrado colaborativo.

**Resultado:** Cada usuario tiene un `id_cluster` asignado en la tabla `usuario_visitante`. Esto es la base del Filtrado Colaborativo.

---

### C) Filtrado Colaborativo Item-to-Item (por Cluster)
**Tecnología:** SQLAlchemy (consultas de co-ocurrencia por cluster)  
**Archivo:** [`backend/engine/collab_filter.py`](../backend/engine/collab_filter.py)

**¿Qué hace?** En lugar de comparar al usuario con todos los demás (User-to-User, muy costoso), compara **establecimientos** entre sí según qué tan frecuentemente fueron visitados por la misma tribu de usuarios.

**Flujo:**
1. Identifica el `id_cluster` del usuario.
2. Consulta qué establecimientos han sido más visitados/reseñados por los usuarios de ese mismo cluster.
3. Retorna los establecimientos más populares dentro de la tribu que el usuario **no ha visitado aún**.

**Ventaja:** Es tolerante a la escasez de datos. Incluso si un usuario nuevo tiene pocas interacciones, su tribu (cluster) ya tiene un historial colectivo rico del que se puede nutrir.

---

### D) Fórmula de Haversine — Distancia Geográfica
**Tecnología:** Fórmula trigonométrica (implementación propia)  
**Archivo:** [`backend/engine/ranking.py`](../backend/engine/ranking.py)

**¿Qué hace?** Calcula la distancia en kilómetros (en línea recta, considerando la curvatura de la Tierra) entre las coordenadas GPS del usuario y el establecimiento.

**¿Por qué Haversine y no Pitágoras?** La fórmula de Pitágoras asume un plano plano. A distancias urbanas (2-10km) el error acumulado por la curvatura terrestre es despreciable, pero usar Haversine es la práctica estándar para coordenadas GPS y evita imprecisiones al estar cerca de meridianos o paralelos.

**Uso:** El resultado se convierte en un `boost_proximidad` que favorece establecimientos más cercanos al usuario dentro del score final.

---

### E) Ranking y Boosting — Score Final Híbrido
**Tecnología:** Aritmética ponderada (implementación propia)  
**Archivo:** [`backend/engine/ranking.py`](../backend/engine/ranking.py)

**¿Qué hace?** La función `compute_score_final()` toma los tres scores individuales y los combina en un score final que determina el orden de aparición en el Feed:

```
score_final = (W_contenido × score_contenido)
            + (W_colaborativo × score_colaborativo)
            + (W_boost × score_boost_combinado)
```

Donde `score_boost_combinado` incluye:
- **Bonus Haversine:** mayor puntuación a los establecimientos más cercanos.
- **Bonus Informal:** establecimientos con `es_informal = True` reciben un multiplicador adicional para visibilizarlos frente a restaurantes grandes.
- **Popularidad de zona:** basada en el `score_boost_combinado` pre-calculado por el job de métricas.

> **Decisión de Arquitectura:** El `score_final` **no se normaliza** en escala Min-Max `[0, 1]`. Como el objetivo es el **ranking** (quién va primero), aplicar `(x - min) / (max - min)` requeriría un ciclo `O(N)` adicional sin cambiar el orden final. Se omite intencionalmente para ahorrar recursos.

---

### F) Análisis de Sentimiento NLP
**Tecnología:** `TextBlob` + API de traducción automática  
**Archivo:** [`backend/jobs/nlp_pipeline.py`](../backend/jobs/nlp_pipeline.py)

**¿Qué hace?** Para cada reseña nueva (`procesado_nlp = False`):
1. Traduce el texto del español al inglés (TextBlob tiene mayor precisión en inglés).
2. Extrae dos métricas psicológicas del texto:
   - **Polaridad** (`-1.0` = muy negativa, `0.0` = neutral, `1.0` = muy positiva).
   - **Subjetividad** (`0.0` = hecho objetivo, `1.0` = opinión completamente subjetiva).
3. Marca la reseña como `procesado_nlp = True`.
4. Recalcula el `polaridad_promedio` en `MetricaEstablecimiento` para todos los establecimientos afectados.

**¿Cómo influye en las recomendaciones?** El `polaridad_promedio` de un establecimiento entra como señal positiva o negativa en su `score_boost_combinado`. Un lugar con reseñas muy positivas recibe más visibilidad en el ranking.

---

### G) Corrección Ortográfica — Distancia de Levenshtein
**Tecnología:** Algoritmo de Levenshtein (implementación propia)  
**Archivos:**
- Lógica matemática: [`backend/engine/lexical_filter.py`](../backend/engine/lexical_filter.py)
- Orquestación: [`backend/services/buscador_service.py`](../backend/services/buscador_service.py)

**¿Qué hace?** Mide cuántas operaciones (inserción, eliminación, sustitución de un carácter) se necesitan para convertir una palabra en otra. Si el usuario escribe "Tcko" en el buscador, la BD no encontrará nada. El motor léxico:
1. Compara "Tcko" contra todos los nombres de establecimientos en el diccionario.
2. Calcula la similitud como `1 - (distancia / max(len_a, len_b))`.
3. Si la similitud supera el 70%, devuelve la sugerencia al frontend automáticamente.

**¿Por qué Levenshtein y no BM25 o TF-IDF?** BM25 y TF-IDF están diseñados para búsqueda de documentos completos. Levenshtein es perfecto para corrección de palabras sueltas o nombres propios (nombres de negocios), que es exactamente nuestro caso de uso.

---

### H) Serendipia y Diversidad
**Tecnología:** Lógica de selección aleatoria ponderada (implementación propia)  
**Archivo:** [`backend/jobs/generador_recomendaciones.py`](../backend/jobs/generador_recomendaciones.py)

**¿Qué hace?** Dos mecanismos evitan que el Feed se vuelva una "burbuja de filtro" donde el usuario siempre ve los mismos lugares:

1. **Carrusel de Descubrimiento (`descubrimiento`):** Prioriza establecimientos nuevos (ordenados por `fecha_registro` ascendente). Son lugares que el motor no ha podido aprender a recomendar aún, pero que necesitan sus primeros clientes para acumular datos.

2. **Carrusel de Comercio Local (`tendencia_informal`):** Filtra exclusivamente los establecimientos con `es_informal = True` (puestos callejeros, carritos, fondas de mercado) y les da visibilidad independientemente de si su score híbrido es alto o no.

**¿Por qué importa la serendipia?** En teoría de recomendadores, el fenómeno de "overspecialization" ocurre cuando el sistema es demasiado preciso y siempre recomienda lo mismo. La serendipia controlada (introducir sorpresas calibradas) mejora la satisfacción del usuario a largo plazo.

---

### I) Inicio en Frío (Cold Start)
**Tecnología:** Consulta SQL de popularidad global  
**Archivo:** [`backend/engine/cold_start.py`](../backend/engine/cold_start.py)

**¿Cuándo se activa?** Para un usuario que cumple alguna de estas condiciones:
- Es nuevo (recién registrado, sin historial de interacciones).
- No ha completado el onboarding de preferencias (`perfil_completado = False`).
- Tiene menos de 50 puntos de experiencia acumulados.

**¿Qué hace?** En lugar de los algoritmos híbridos (que necesitan datos del usuario), sirve los establecimientos más populares globalmente, ordenados por su `score_boost_combinado` pre-calculado. Es la estrategia más segura para un usuario desconocido: mostrar lo que le gusta a la mayoría.

**Transición Cold Start → Veterano:** Una vez que el usuario acumula suficientes interacciones, el siguiente ciclo del job de recomendaciones lo detectará como veterano y le generará recomendaciones personalizadas con el modelo híbrido completo.

---

## 3. Caja Blanca — Explicabilidad de las Recomendaciones

**Tecnología:** Metadatos persistidos en `RecomendacionGenerada`  
**Archivo:** [`backend/models/interacciones.py`](../backend/models/interacciones.py) (modelo `RecomendacionGenerada`)

EkiSystem implementa lo que se conoce como **recomendación de caja blanca**: el usuario puede saber *por qué* se le está recomendando cada lugar. Esto contrasta con los modelos de "caja negra" (como redes neuronales profundas) donde la razón es opaca.

**¿Cómo funciona?** Cada registro en `RecomendacionGenerada` incluye:
- `categoria_recomendacion`: el tipo de algoritmo que generó esta recomendación (ej. `"top_picks_hibrido"`, `"preferencia_contenido"`, `"cold_start"`).
- `razon_principal`: etiqueta corta legible por humanos.
- `detalle_razon`: explicación completa en texto plano (ej. `"Visitado frecuentemente por personas con gustos similares a los tuyos"`).
- `estrategia_usada`: el nombre técnico del algoritmo.
- `score_contenido_usado`, `score_colaborativo_usado`, `score_boost_aplicado`: los scores individuales que contribuyeron al score final, permitiendo auditar el peso de cada factor.

El frontend consume estos campos y los muestra en la tarjeta del establecimiento como la razón de la recomendación.

---

## 4. Evaluación del Motor (Métricas de Efectividad)

El sistema rastrea la efectividad de las recomendaciones usando **telemetría orgánica** en lugar de métricas offline como RMSE o Precision@K sobre un dataset de prueba. Esto refleja cómo se miden los recomendadores en producción real.

| Métrica | ¿Dónde se captura? | ¿Qué indica? |
|---|---|---|
| **CTR (Click-Through Rate)** | Tabla `historial_visita` — campo `fue_recomendado` | % de recomendaciones que generaron una visita real al perfil |
| **Conversión de Reseña** | Tabla `interaccion_usuario` — tipo `resena_dejada` tras `fue_recomendado=True` | % de visitas recomendadas que terminaron en una reseña |
| **Silhouette Score** | Calculado en tiempo de ejecución en el job de `clustering` | Calidad de la separación entre clusters (tribus) |

---

## 5. Lo que ve el Usuario: Los Carruseles del Feed

El generador offline guarda las recomendaciones categorizadas. El frontend las muestra como filas deslizables estilo Netflix:

| Carrusel en Pantalla | Categoría interna | Algoritmo | Archivo principal |
|---|---|---|---|
| **"Mejores Selecciones Para Ti"** | `top_picks_hibrido` | Híbrido: Coseno + Colaborativo + Haversine | `engine/ranking.py` |
| **"Basado en tus gustos"** | `preferencia_contenido` | Filtrado por Contenido (Coseno puro) | `engine/content_filter.py` |
| **"Gente como tú visitó"** | `colaborativo_cluster` | Filtrado Colaborativo Item-to-Item | `engine/collab_filter.py` |
| **"Populares cerca de ti"** | `popularidad_zona` | Popularidad + Haversine | `jobs/generador_recomendaciones.py` |
| **"Apoya el comercio local"** | `tendencia_informal` | Boosting de informales (`es_informal = True`) | `jobs/generador_recomendaciones.py` |
| **"Descubrimientos recientes"** | `descubrimiento` | Novedad (fecha de registro) — Serendipia | `jobs/generador_recomendaciones.py` |
| **"Populares de la semana"** | `cold_start` | Popularidad global — Inicio en Frío | `engine/cold_start.py` |

---

## 6. Flujo Completo de una Recomendación

```
1. [OFFLINE — Job NLP]
   Reseña nueva → TextBlob → polaridad + subjetividad → guarda en BD

2. [OFFLINE — Job Métricas]
   Para cada establecimiento: calcula popularidad 7 días + calificación
   promedio + score_boost_combinado → guarda en MetricaEstablecimiento

3. [OFFLINE — Job Clustering]
   Lee vector_preferencias de todos los usuarios → K-Means con
   Silhouette Score → asigna id_cluster a cada usuario

4. [OFFLINE — Job Recomendaciones]
   Para cada usuario veterano:
     a. Filtrado Contenido: cosine_similarity(vector_usuario, vector_establecimientos)
     b. Filtrado Colaborativo: top establecimientos del cluster del usuario
     c. Ranking: compute_score_final(a, b, Haversine + boost)
     d. Serendipia: añade carruseles de descubrimiento e informales
   Para cada usuario cold_start:
     a. Top establecimientos por popularidad global

5. [ONLINE — Petición del usuario]
   GET /recomendaciones/feed
   → SELECT * FROM recomendacion_generada WHERE id_usuario = ?
   → Respuesta en < 200ms
```