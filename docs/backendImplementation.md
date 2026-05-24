# Registro de Implementación del Backend (Fases 0 a 3)

Este documento detalla la implementación, decisiones técnicas y la evolución de la arquitectura del Backend de EkiSystem para las primeras etapas (Fases 0 a 3). El enfoque principal se mantuvo en construir un motor de recomendación híbrido, funcional y académicamente riguroso, priorizando el rendimiento, la robustez y la facilidad de pruebas.

---

## Fase 0: Infraestructura y Andamiaje Base

**Objetivo:** Establecer una fundación segura y estructurada antes de implementar la lógica de negocio, asegurando que las capas de la aplicación se mantuvieran independientes.

### Decisiones Técnicas Implementadas:
1. **Separación de Responsabilidades (Capa de Servicios):** Se optó por separar los controladores (FastAPI `routers/`) de la lógica de negocio (CRUD e invariantes en `services/`). Esto garantiza que los endpoints solo manejen peticiones HTTP, mientras que la validación y operaciones en BD queden aisladas, favoreciendo el Testing.
2. **Autenticación (JWT + bcrypt):** Se implementó autenticación por token usando `python-jose` y `passlib` (para contraseñas). Todos los endpoints protegidos inyectan la dependencia `get_current_user` para validar la identidad y restringir acceso a rutas administrativas con `get_current_admin`.
3. **Manejo de CORS:** Se añadió soporte para métodos `PATCH` en el archivo `eki_main.py` para cumplir con el diseño de Endpoints de Perfil y Establecimientos.
4. **Adopción de Librerías Matemáticas:** Desde el inicio se estipuló que el motor no reinventaría la rueda, adoptando `scikit-learn`, `numpy` y `scipy` en el `requirements.txt` como núcleo analítico para procesamiento vectorial pesado.

---

## Fase 1: Procesamiento Online (CRUD y Lógica de Negocio)

**Objetivo:** Desarrollar todos los endpoints operativos (App Normal) que NO involucraran de manera profunda cálculos del motor de recomendación.

### Componentes Construidos:
1. **Gestión de Usuarios y Onboarding:** Se implementaron los registros de usuario. Al realizar el "onboarding", se calcula el `vector_preferencias` del usuario y se le asigna de inmediato un cluster provisional empleando la distancia Euclidiana a los centroides ya existentes.
2. **Establecimientos e Interacciones:** Creación de endpoints para listado, creación de establecimientos y el registro de interacciones (ej. vistas, favoritos). Destaca el almacenamiento del `peso_interaccion` para uso futuro del filtrado colaborativo.
3. **Gamificación y Administración:** Inserción y validación atómica (Transaccional) del sistema de puntos al registrar lugares nuevos o interacciones para asegurar el principio ACID y mantener consistentes los valores calculados en las vistas (como `total_resenas`).

---

## Fase 2: Algoritmos del Motor (Optimizaciones y Lógica Pura)

**Objetivo:** Dotar de inteligencia al motor en la carpeta `backend/engine/` finalizando los algoritmos matemáticos e integrándolos con librerías estandarizadas para resolver cuellos de botella de rendimiento.

### Soluciones Implementadas:
1. **Filtrado Basado en Contenido (Vectorizado):** 
   - Se reemplazaron las iteraciones manuales con cálculo de `math.sqrt` por la función `sklearn.metrics.pairwise.cosine_similarity`. 
   - **Razón:** El cálculo vectorial en matrices de características completas reduce el tiempo exponencial al procesar catálogos grandes, calculando las distancias de un lote completo de una sola vez.
2. **Filtrado Colaborativo (Item-to-Item con Matrices Dispersas):** 
   - Se aplicó `scipy.sparse.csr_matrix` para modelar la relación *Usuarios x Establecimientos*. 
   - **Razón:** La matriz relacional es sumamente rala (escasa) porque los usuarios interactúan con una minúscula fracción de todo el catálogo. Usar matrices dispersas evita desbordamientos de memoria en RAM al calcular la Similitud de Coseno transpuesta (entre ítems en lugar de usuarios).
3. **Ranking y Boosting (Haversine Vectorizado):** 
   - Se construyó una variante del cálculo de distancia geográfica Haversine usando matrices de `numpy`.
   - **Razón:** Permitir a los *Jobs Offline* calcular las distancias de miles de usuarios contra cientos de locales en milisegundos para sus métricas de cercanía local.
4. **Combinación Híbrida y Diversidad:** Se optó por un diseño sin normalización estricta Min-Max (ahorrando tiempo computacional `O(N)`), ya que el Coseno devuelve valores pre-acotados `[-1, 1]`, y al emplear pesos ponderados que suman `1.0` sobre variables controladas, el ordenamiento relativo se preserva perfectamente. Adicionalmente, se implementó el "Diversity Score" basado en el inverso a la similitud coseno (para evitar burbujas de filtro).

---

## Fase 3: Procesamiento Offline (Orquestación de Jobs)

**Objetivo:** Extraer el procesamiento masivo fuera del ciclo de petición HTTP del usuario, para precalcular las recomendaciones por adelantado (cálculo Offline).

### Orquestador (Runner)
Se diseñó un sistema propio en `backend/jobs/runner.py` utilizando `threading.Thread` y mecanismos de candados (`Locks`) que:
- Previene que dos ejecuciones del mismo Job corran en paralelo para evitar corrupción.
- **Razón:** Dado que la aplicación está planificada para el Free Tier de Render (que suspende procesos sin tráfico web), optar por Celery/Redis era sobreingeniería y el servicio hubiese muerto con la instancia. El `runner` asegura el encendido por demanda sincrónica (vía CLI) o asincrónica vía un Panel Admin, manteniendo los costos en cero.

### Jobs Especializados Implementados:
1. **K-Means Clustering (`clustering.py`):** 
   - Utiliza `sklearn.cluster.KMeans` para modelar los nichos de mercado (tanto en Usuarios como en Establecimientos). El número K óptimo se iteraba mediante el *Silhouette Score* como forma de adaptación automática del sistema. Se aseguró corregir *Warnings* del tipado de SQLAlchemy al interactuar con las propiedades del modelo (conversiones de Python `int()` a `Column[Integer]`).
2. **NLP Pipeline (`nlp_pipeline.py`):**
   - Evalúa `polaridad` y `subjetividad` de cada reseña.
   - **Decisión Técnica:** Inicialmente se propuso un esquema donde TextBlob traduciría el texto de español a inglés. Dicha API no oficial fue eliminada en `TextBlob 0.20.0`. La solución adaptada fue retirar la traducción insegura y permitir a TextBlob evaluar de forma nativa la cadena como un *Fallback* consistente, limpiando así cualquier caída por Rate Limits externos.
3. **Métricas Masivas (`metricas.py`):** 
   - Generación de sumatorias en SQL a través de la función `GROUP BY` sobre la tabla `interaccion_usuario`, contando popularidad en ventanas de 7 y 30 días, resultando en un proceso con menor estrés de memoria RAM.
4. **Generador de Recomendaciones (`generador_recomendaciones.py`):** 
   - Fusiona todos los motores implementados en la **Fase 2**. Barre a todos los usuarios activos y escribe de golpe (`bulk_save_objects`) en la tabla de caché `recomendacion_generada`. El motor pre-calcula 6 bloques principales de sugerencias por usuario: Cold Start, Filtrado por Contenido, Colaborativo por Clúster, Popularidad de Zona, Tendencia Informal y Descubrimiento (locales nuevos). Este job alimenta la Explicabilidad (Caja Blanca) del motor indicando la razón por la cual se seleccionó cada lugar.
5. **Archivado (`archivado.py`):** 
   - Gestión del ciclo de vida de los datos, expulsando interacciones pasadas los 90 días a tablas históricas para mantener rápidas las consultas en vivo de los otros Jobs.

---

### Resumen del Estado de Avance
Con estas tres etapas finalizadas, el núcleo inteligente y pesado del **EkiSystem** está activo. La Base de Datos almacena las listas pre-cocinadas de "qué recomendar a quién y por qué". La Fase 4 constará únicamente en diseñar las ventanas o puertas de acceso rápidas (FastAPI) para entregar de manera estructurada estas recomendaciones al Frontend bajo demanda.
