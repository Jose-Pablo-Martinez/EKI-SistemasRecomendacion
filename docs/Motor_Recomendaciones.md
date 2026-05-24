# Motor de Recomendaciones Híbrido - EkiSystem

Este documento detalla el funcionamiento interno del Motor de Recomendaciones del proyecto EkiSystem. El sistema utiliza una arquitectura **Offline-First**, donde cálculos matemáticos pesados se ejecutan en segundo plano mediante _Jobs_ y los resultados se almacenan en la base de datos para servirse rápidamente a través de una API en tiempo real.

---

## 1. Algoritmos Matemáticos Utilizados

El sistema no confía en una sola técnica; es "híbrido" porque mezcla múltiples algoritmos de Inteligencia Artificial y trigonometría para compensar sus debilidades individuales.

### A) Similitud Coseno (Filtrado por Contenido)
- **¿Qué hace?** Compara el `vector_preferencias` del usuario (sus gustos registrados) con el `vector_caracteristicas` del establecimiento (categorías, etiquetas).
- **¿Por qué Coseno y no Euclidiana o Pearson?** 
  - La *Distancia Euclidiana* penaliza injustamente a los usuarios que tienen muchas preferencias registradas contra puestos que tienen pocos tags. El Coseno solo mide la **orientación (el ángulo)**, ignorando la cantidad de datos (magnitud), lo que lo hace perfecto para esto.
  - La *Correlación de Pearson* asume escalas de calificación (como estrellas de 1 a 5) y resta el promedio. En EkiSystem usamos presencias de características binarias o fraccionales (0 a 1), donde no hay usuarios "felices" o "enojones" a los cuales restarles la media.
- **Normalización:** No necesitamos normalizar los datos a mano antes de enviarlos. La función `cosine_similarity` de `scikit-learn` aplica normalización L2 matemáticamente en tiempo de ejecución (dividiendo el producto punto por la magnitud de los vectores).
- **Ubicación en el código:** `backend/engine/content_filter.py`

### B) K-Means Clustering (Machine Learning No Supervisado)
- **¿Qué hace?** Divide a la base de usuarios en "Tribus" (Clusters) con comportamientos similares.
- **¿Cómo funciona?** Extrae los vectores de todos los usuarios, calcula matemáticamente el número perfecto de grupos (`mejor_k`), y agrupa a los usuarios alrededor de centros de datos de gustos similares. Posteriormente, asigna un `id_cluster` a cada usuario en la base de datos.
- **¿Por qué se usa?** Es la base del **Filtrado Colaborativo**. En lugar de comparar a un usuario con un millón de otras personas para ver qué recomiendan, solo se compara con su propio Cluster. 
- **Ubicación en el código:** `backend/jobs/clustering.py` y `backend/engine/collab_filter.py`

### C) Fórmula de Haversine
- **¿Qué hace?** Calcula la distancia geográfica exacta (en kilómetros, en línea recta y considerando la curvatura de la Tierra) entre las coordenadas GPS del usuario y el establecimiento.
- **Ubicación en el código:** `backend/engine/ranking.py`

---

## 2. Dónde y Cómo se Generan las Recomendaciones

El proceso está fuertemente separado por el principio de **Responsabilidad Única (SRP)**:

1. **La Matemática Pura (`backend/engine/`):**
   Aquí residen las funciones matemáticas que no saben de bases de datos. Solo toman variables y devuelven números.
   
2. **La Orquestación Offline (`backend/jobs/generador_recomendaciones.py`):**
   Es el archivo más importante del proceso. Corre en segundo plano y hace lo siguiente por cada usuario activo:
   - Limpia recomendaciones viejas.
   - Ejecuta todos los algoritmos (Contenido, Colaborativo, Híbrido, Descubrimiento).
   - Guarda los resultados en la tabla `RecomendacionGenerada` utilizando la inserción masiva (`bulk_save_objects`).

3. **La Mezcla Híbrida (`backend/engine/ranking.py`):**
   Contiene la función `compute_score_final()`, que toma los scores de los tres métodos (Contenido, Colaborativo y Boost Geográfico) y realiza una suma ponderada. 
   > **Decisión de Arquitectura:** El resultado final de esta suma **no se normaliza** en una escala Min-Max de `[0, 1]`. Como el objetivo final del motor es simplemente el "Ranking" (saber quién va primero y quién va después), forzar la lista matemáticamente para que el máximo sea `1.0` solo consume memoria y tiempo de CPU (un ciclo O(N) innecesario), sin alterar el orden final de la lista.

4. **El Servicio Online (`backend/services/recomendacion_service.py`):**
   Cuando el usuario abre la app, este servicio es el que le responde. **No calcula algoritmos pesados**. Solo hace `SELECT` a la base de datos para recuperar las cajas guardadas por el Job Offline. Aquí se aplica la lógica de **Fallback en cascada**: si un usuario configuró su radio en 5km, y no hay lugares suficientes, este script dinámicamente expande el radio a 10km o ignora el límite por completo para asegurar que la app nunca se quede en blanco.

---

## 3. Lo que recibe el Usuario (Los Carruseles)

Debido al diseño del generador masivo en `generador_recomendaciones.py`, el sistema guarda las recomendaciones en categorías específicas. Esto permite que el Frontend de EkiSystem muestre múltiples filas deslizables estilo Netflix:

1. **`top_picks_hibrido` (Mejores Selecciones Para Ti):**
   - **Cómo se obtiene:** El resultado estrella de la aplicación. Extrae los puntajes de tu tribu (K-Means), los de tus gustos (Coseno), les suma el boost de distancia y los combina matemáticamente usando `compute_score_final`.

2. **`preferencia_contenido` (Basado en tus gustos):**
   - **Cómo se obtiene:** Resultado puro de la Similitud Coseno.

3. **`colaborativo_cluster` (Personas como tú visitaron):**
   - **Cómo se obtiene:** Resultado de buscar los lugares más frecuentados exclusivamente por las personas de tu mismo cluster de IA.

4. **`popularidad_zona` (Populares cerca de ti):**
   - **Cómo se obtiene:** Simplemente ordenando los establecimientos según su métrica pre-calculada y dándole bonus a los lugares cercanos a ti en tiempo real usando Haversine.

5. **`tendencia_informal` (Apoya el comercio local):**
   - **Cómo se obtiene:** Igual a la popularidad, pero aplica un filtro rígido en SQL (`es_informal = True`) para promover carritos y puestos callejeros dándoles una ventaja algorítmica sobre los grandes restaurantes.

6. **`descubrimiento` (Lugares recién agregados):**
   - **Cómo se obtiene:** Un simple orden por fecha de registro en la base de datos para darle rotación a los negocios nuevos.

7. **`cold_start` (El Salvavidas):**
   - **Cómo se obtiene:** Si el usuario es nuevo, no ha completado su perfil, o tiene menos de 50 puntos de experiencia, el sistema asume un estado de "Inicio en Frío" y le entrega este carrusel genérico (generalmente basado en pura distancia Haversine) hasta que la app logre aprender sus gustos.

## 4. Resumen Ejecutivo de Carruseles (Lo que ve el Usuario)

A continuación, una explicación **sin tecnicismos** de las listas deslizables (carruseles) que aparecen en la aplicación del usuario. Cada carrusel está respaldado por una estrategia distinta:

| Nombre del Carrusel en Pantalla | ¿Qué tipo de recomendación es? | ¿En qué archivo está la lógica? |
|----------------|----------------|----------------|
| **"Mejores Selecciones Para Ti"** | **Híbrida:** Es la predicción más exacta. Mezcla tus gustos, los de la gente similar a ti, y qué tan cerca está el lugar. | `backend/engine/ranking.py` |
| **"Basado en tus gustos"** | **Contenido:** Solo le importa que los ingredientes o etiquetas del puesto hagan "match" perfecto con tu perfil. | `backend/engine/content_filter.py` |
| **"Gente como tú visitó"** | **Colaborativa:** Ignora tus gustos directos. Se basa en el historial de visitas de la "Tribu" (cluster) a la que perteneces. | `backend/engine/collab_filter.py` |
| **"Populares cerca de ti"** | **Tendencia General:** Los lugares con más éxito en los últimos días, ordenados de mayor a menor popularidad. | `backend/jobs/generador_recomendaciones.py` |
| **"Apoya el comercio local"** | **Boosting:** Exclusivo para carritos y puestos informales de la calle, dándoles ventaja frente a los grandes restaurantes. | `backend/jobs/generador_recomendaciones.py` |
| **"Descubrimientos recientes"** | **Novedad:** Lugares que acaban de ser registrados en la app y necesitan sus primeros clientes. | `backend/jobs/generador_recomendaciones.py` |
| **"Populares de la semana"** | **Cold Start (Salvavidas):** Si acabas de descargar la app y aún no sabemos qué te gusta, te mostramos lo más seguro y popular. | `backend/engine/cold_start.py` |