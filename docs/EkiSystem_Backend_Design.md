# EkiSystem — Diseño del Backend

> **Proyecto:** Esquina Jach ki' (EKI) · Sistemas de Recomendación de Información  
> **Facultad de Matemáticas, UADY**  
> **Stack:** FastAPI · SQLAlchemy 2.x · Pydantic v2 · Alembic · PyMySQL

> Para el diseño y justificación del esquema de base de datos, consulta [EkiSystem_DB_Design.md](./EkiSystem_DB_Design.md). Este documento asume que ese diseño ya fue leído.

---

## Índice

1. [Principios Fundamentales del Backend](#1-principios-fundamentales-del-backend)
   - 1.1 [Offline-First: qué resuelve FastAPI y qué no](#11-offline-first-qué-resuelve-fastapi-y-qué-no)
   - 1.2 [Invariantes de integridad como responsabilidad de la capa API](#12-invariantes-de-integridad-como-responsabilidad-de-la-capa-api)
   - 1.3 [Desnormalizaciones: quién actualiza qué](#13-desnormalizaciones-quién-actualiza-qué)
2. [Estructura de Capas](#2-estructura-de-capas)
3. [Capa de Validación — Pydantic Schemas](#3-capa-de-validación--pydantic-schemas)
   - 3.1 [Regla Create / Response](#31-regla-create--response)
   - 3.2 [Validaciones críticas obligatorias](#32-validaciones-críticas-obligatorias)
4. [Capa de Negocio — Módulos engine/ y services/](#4-capa-de-negocio--módulos-engine-y-services)
   - 4.1 [ranking.py](#41-rankingpy)
   - 4.2 [content_filter.py](#42-content_filterpy)
   - 4.3 [collab_filter.py](#43-collab_filterpy)
   - 4.4 [cold_start.py](#44-cold_startpy)
5. [Endpoints REST — Organización por Dominio](#5-endpoints-rest--organización-por-dominio)
   - 5.1 [Usuarios](#51-usuarios)
   - 5.2 [Establecimientos](#52-establecimientos)
   - 5.3 [Contenido](#53-contenido)
   - 5.4 [Recomendaciones](#54-recomendaciones)
   - 5.5 [Gamificación](#55-gamificación)
   - 5.6 [Administración y Jobs Offline](#56-administración-y-jobs-offline)
6. [Jobs Offline — Motor de Recomendación](#6-jobs-offline--motor-de-recomendación)
   - 6.1 [Job de K-Means (Clustering)](#61-job-de-k-means-clustering)
   - 6.2 [Job de Generación de Recomendaciones](#62-job-de-generación-de-recomendaciones)
   - 6.3 [Job de Métricas](#63-job-de-métricas)
   - 6.4 [Job de NLP](#64-job-de-nlp)
   - 6.5 [Job de Archivado](#65-job-de-archivado)
7. [Seguridad y Privacidad](#7-seguridad-y-privacidad)
8. [Flujo de Datos Completo — Request a Response](#8-flujo-de-datos-completo--request-a-response)

---

## 1. Principios Fundamentales del Backend

### 1.1 Offline-First: qué resuelve FastAPI y qué no

Este es el principio más importante del backend y está documentado en §1.7 del diseño de BD. Se resume así:

**FastAPI resuelve en tiempo real:**
- Servir las listas de recomendaciones ya pre-generadas (leer de `recomendacion_generada`)
- Calcular la distancia Haversine puntual entre la ubicación actual del usuario y los establecimientos de su lista
- Registrar el click en una recomendación (`fue_clickeada = TRUE`)
- Aplicar el fallback en cascada de radio si la lista tiene menos de N resultados
- Registrar interacciones, sesiones, ubicaciones y contribuciones

**FastAPI NO resuelve (son responsabilidad de jobs offline):**
- El K-Means sobre usuarios y establecimientos
- El cálculo de `score_contenido_base`, `score_colaborativo_base`, `score_boost_combinado`
- La generación de las listas en `recomendacion_generada`
- El pipeline de análisis NLP de reseñas (`polaridad`, `subjetividad`)
- El cálculo de `popularidad_7d` y `popularidad_30d`
- El archivado de `interaccion_usuario` e `recomendacion_generada` obsoletos

> [!IMPORTANT]
> Ningún endpoint HTTP de FastAPI debe ejecutar K-Means, calcular scores colaborativos sobre toda la tabla de interacciones, ni correr el pipeline NLP. Si un endpoint tarda más de ~200ms en responder, es señal de que algo que debería ser offline está ocurriendo online.

---

### 1.2 Invariantes de integridad como responsabilidad de la capa API

La base de datos no tiene triggers. FastAPI es quien garantiza que el esquema se mantenga consistente. Las invariantes completas están en §7 del diseño de BD. Las más críticas son:

| Invariante | Cuándo aplicarla |
|---|---|
| `es_ultimo = TRUE` único por usuario en `dispositivo_usuario` | Antes de insertar un nuevo dispositivo, se actualiza el anterior a FALSE |
| Máximo 3 registros en `ubicacion_usuario` por usuario | En la misma transacción del INSERT, se eliminan los más antiguos que excedan ese límite |
| `total_resenas` y `calificacion_promedio` sincronizados | Al aprobar una reseña, se recalculan ambos campos en la misma transacción |
| `puntos_experiencia` sincronizado con `log_puntos` | Al insertar en `log_puntos`, se suma en la misma transacción al campo del usuario |
| `es_informal` consistente con `tipo_establecimiento` | Al registrar un establecimiento, se calcula automáticamente sin que el usuario lo envíe |
| FastAPI NO escribe en `metrica_establecimiento` | Solo el job offline escribe ahí; FastAPI solo lee |
| FastAPI solo actualiza `fue_clickeada` en `recomendacion_generada` | El resto de campos los escribe exclusivamente el job offline |

---

### 1.3 Desnormalizaciones: quién actualiza qué

Como se documenta en §1.5 del diseño de BD, hay campos que técnicamente son derivables pero se pre-computan por rendimiento. El backend debe saber exactamente quién actualiza cada uno:

| Campo desnormalizado | Lo actualiza |
|---|---|
| `establecimiento.total_resenas` | FastAPI (al aprobar reseña) |
| `establecimiento.calificacion_promedio` | FastAPI (al aprobar reseña) |
| `establecimiento.es_informal` | FastAPI (al registrar establecimiento, derivado de `tipo_establecimiento`) |
| `sesion_usuario.total_vistas` | FastAPI (al registrar cada vista de detalle, en el mismo request) |
| `usuario_visitante.puntos_experiencia` | FastAPI (al insertar en `log_puntos`) |
| `interaccion_usuario.peso_interaccion` | FastAPI (al insertar, derivado del tipo de interacción según tabla fija de pesos) |
| `metrica_establecimiento.*` (todos los scores) | Job offline **exclusivamente** |
| `cluster_usuario.total_usuarios` | Job offline K-Means |
| `cluster_establecimiento.total_establecimientos` | Job offline K-Means |
| `metrica_establecimiento.polaridad_promedio` | Job offline NLP |

---

## 2. Estructura de Capas

El backend sigue una separación de responsabilidades en tres capas. Cada request HTTP pasa por todas ellas en orden:

```
Request HTTP
    │
    ▼
[Router / Endpoint]     → Recibe el request, llama al schema para validar, orquesta la respuesta
    │
    ▼
[Logic / Service]       → Lógica de negocio pura: reglas, invariantes, cálculos online
    │
    ▼
[Database / ORM]        → SQLAlchemy: consultas, inserciones, transacciones
    │
    ▼
Response HTTP           → Serializado por el schema de respuesta (Response)
```

**Regla de oro:** los routers no deben contener lógica de negocio. Un router solo llama a funciones de `services/` y serializa el resultado. La lógica matemática del motor va en `engine/`.

---

## 3. Capa de Validación — Pydantic Schemas

Los schemas están en `backend/schemas.py`, organizados por dominio. Hay dos tipos:

### 3.1 Regla Create / Response

- **`XxxCreate`**: Valida el cuerpo del request (input). Solo contiene los campos que el usuario debe enviar. Campos como `es_informal`, `fecha_registro`, o `estado` nunca van en el Create porque los calcula o asigna FastAPI, no el usuario.
- **`XxxResponse`**: Define qué campos se exponen en la respuesta. Nunca debe incluir `password_hash`, `rfc`, `documento_verificacion` ni coordenadas exactas en endpoints públicos.

### 3.2 Validaciones críticas obligatorias

Estas validaciones deben vivir en Pydantic porque MySQL <8.0 ignora los CHECK constraints (ver §9 del diseño de BD):

| Campo | Validación |
|---|---|
| `UsuarioCreate.email` | Formato RFC 5322 (`EmailStr`) |
| `ResenaCreate.calificacion` | Entero entre 1 y 5, inclusive |
| `EstablecimientoCreate.latitud` | Decimal entre -90 y 90 |
| `EstablecimientoCreate.longitud` | Decimal entre -180 y 180 |
| `HorarioCreate.dia_semana` | Entero entre 0 y 6 |
| `UsuarioCreate.password` | Mínimo 8 caracteres |

> El campo `es_informal` no debe estar en ningún schema Create de establecimiento. Es un campo que FastAPI calcula internamente basándose en `tipo_establecimiento`.

---

## 4. Capa de Negocio — Módulos engine/ y services/

Los módulos en `backend/engine/` contienen las funciones de cálculo del motor matemático, mientras que `backend/services/` orquesta la lógica de negocio general. En la implementación actual, los métodos de consulta a la BD están marcados como TODO porque se completan cuando los routers estén listos. Las funciones matemáticas puras ya están implementadas.

### 4.1 ranking.py

**Responsabilidad:** Calcular la distancia Haversine entre el usuario y los establecimientos, y componer el score final ponderado.

**Qué ya está implementado:**
- `compute_haversine_km(lat1, lon1, lat2, lon2)` — fórmula de Haversine; devuelve kilómetros en línea recta
- `compute_score_final(score_contenido, score_colaborativo, score_boost)` — combina los tres componentes con los pesos configurables

**Qué falta implementar:**
- `get_top_establecimientos(db, limit)` — consultar la tabla `metrica_establecimiento` ordenada por `score_boost_combinado`, filtrada por `es_activo=TRUE` y `estado='aprobado'`. Esto es el fallback cuando no hay lista pre-generada para el usuario.
- La lógica del fallback en cascada de radio: si la lista de `recomendacion_generada` tiene menos de N resultados dentro del radio normal del usuario, expandir al doble, y si sigue sin haber suficientes, expandir al municipio completo. Actualizar `fallback_nivel` en consecuencia.

**Nota sobre la distancia:** `compute_haversine_km` se ejecuta online cuando el usuario pide sus recomendaciones. El resultado se persiste en `recomendacion_generada.distancia_km` para que el frontend pueda mostrar "A 0.8 km" sin recalcular. El `+0.1` en el denominador del boosting evita división por cero (ver §1.3 del diseño de BD).

---

### 4.2 content_filter.py

**Responsabilidad:** Calcular la similitud entre el perfil del usuario y las características de los establecimientos (score de contenido).

**Qué ya está implementado:**
- `compute_cosine_similarity(vector_a, vector_b)` — similitud coseno entre dos vectores numéricos de la misma dimensión. Devuelve 0.0 si algún vector es nulo o vacío.
- `build_establecimiento_profile(establecimiento)` — extrae el `vector_caracteristicas` y metadatos relevantes de un establecimiento para el motor.

**Qué falta implementar:**
- `get_content_based_recommendations(db, usuario, candidatos, limit)` — dado un usuario y una lista de establecimientos candidatos (pre-filtrados por radio), calcular la similitud coseno de cada uno con `vector_preferencias` del usuario y devolver los N con mayor score. Esta función la llama el job offline, no un endpoint directo.

**Cuándo se usa:** el job offline de generación de recomendaciones llama a esta función para poblar las filas de categoría `preferencia_contenido` en `recomendacion_generada`. FastAPI online no la llama directamente.

---

### 4.3 collab_filter.py

**Responsabilidad:** Calcular scores colaborativos item-to-item dentro del cluster del usuario.

**Qué ya está implementado:**
- `compute_peso_interaccion(tipo_interaccion)` — devuelve el peso pre-definido para un tipo de interacción según la tabla fija: `vista_detalle=0.1`, `guardado_favorito=0.5`, `compartido=0.3`, `llamada_telefono=0.6`, `abrir_maps=0.7`, `resena_dejada=1.0`, `ruta_calculada=0.9`. Este peso es el que FastAPI persiste en `interaccion_usuario.peso_interaccion` al insertar.
- `compute_item_similarity(id_estab_a, id_estab_b, interacciones)` — similitud coseno entre dos establecimientos basada en co-ocurrencias ponderadas de usuarios dentro del cluster.

**Qué falta implementar:**
- `get_collaborative_recommendations(db, id_usuario, id_cluster, candidatos, limit)` — construir la matriz de co-ocurrencia ponderada usando interacciones de los últimos 90 días del mismo cluster, y devolver los establecimientos con mayor score. Solo usa la ventana de 90 días (ver §6.2 del diseño de BD). Esta función la llama el job offline.

---

### 4.4 cold_start.py

**Responsabilidad:** Generar recomendaciones para usuarios nuevos sin historial y gestionar la visibilidad inicial de establecimientos nuevos.

**Qué ya está implementado:**
- `assign_cluster_provisional(vector_preferencias, clusters)` — calcula la distancia euclidiana entre el vector del usuario y cada centroide pre-computado, y asigna el cluster más cercano. Esta función sí se ejecuta online al momento de registro del usuario (no requiere reentrenar el modelo, solo calcular distancias a centroides ya existentes).

**Qué falta implementar:**
- `get_cold_start_recommendations(db, usuario, limit)` — consultar los establecimientos con mayor `popularidad_7d` dentro del cluster provisional asignado, filtrados por `es_activo=TRUE` y `estado='aprobado'`. No usa componente colaborativo (el usuario no tiene historial). Genera filas de categoría `cold_start` en `recomendacion_generada`.
- `handle_new_establecimiento(id_establecimiento, db)` — inicializar la fila en `metrica_establecimiento` con scores en 0.0 y `boost_informal = 0.25` si `es_informal=TRUE`. El job offline calculará los scores reales en el siguiente ciclo.

**Distinción importante:** `assign_cluster_provisional` es la única función del motor que se ejecuta online (en el request de registro), porque solo requiere calcular distancias a centroides ya existentes. El K-Means completo (reentrenamiento de centroides) es siempre offline.

---

## 5. Endpoints REST — Organización por Dominio

Los routers deben crearse en `backend/routers/` con un archivo por dominio. Todos los endpoints devuelven los schemas `Response` correspondientes. Los endpoints que reciben datos de entrada usan los schemas `Create`.

### 5.1 Usuarios

| Endpoint | Método | Descripción |
|---|---|---|
| `/usuarios/registro` | POST | Crea usuario + subtipo TPT según `tipo_usuario`. Hashea la contraseña. Asigna cluster provisional (llama a `assign_cluster_provisional`). |
| `/usuarios/login` | POST | Autentica y devuelve token de sesión. Crea registro en `sesion_usuario`. Detecta y persiste `dispositivo_usuario` desde User-Agent. |
| `/usuarios/logout` | POST | Cierra la sesión: actualiza `sesion_usuario.fecha_fin` y `duracion_segundos`. |
| `/usuarios/perfil` | GET | Devuelve datos del usuario autenticado. |
| `/usuarios/perfil` | PATCH | Actualiza nombre, foto, preferencias. Si cambia `vector_preferencias`, reasigna cluster provisional. |
| `/usuarios/ubicacion` | POST | Registra nueva ubicación. En la misma transacción aplica la invariante de máximo 3 registros (ver §1.2). |
| `/usuarios/onboarding` | POST | Recibe preferencias declaradas del usuario nuevo, construye `vector_preferencias` inicial, marca `perfil_completado = TRUE`. |

---

### 5.2 Establecimientos

| Endpoint | Método | Descripción |
|---|---|---|
| `/establecimientos` | POST | Registra un establecimiento nuevo + su subtipo TPT. Calcula `es_informal` automáticamente. Estado inicial: `pendiente`. |
| `/establecimientos/{id}` | GET | Devuelve los datos públicos de un establecimiento aprobado. |
| `/establecimientos/{id}` | PATCH | Propietario edita sus datos. Solo campos permitidos según el subtipo. |
| `/establecimientos/{id}/horarios` | POST | Registra o actualiza los horarios. Aplica la UNIQUE constraint `(id_establecimiento, dia_semana)`. |
| `/establecimientos/{id}/platillos` | POST | Propietario o informador agrega platillo. Estado inicial: `pendiente`. |
| `/establecimientos/{id}/imagenes` | POST | Sube imagen. Estado inicial: `pendiente`. |
| `/establecimientos/{id}/resena` | POST | Usuario crea reseña. Valida `calificacion` en Pydantic. Aplica UNIQUE por usuario+establecimiento. Estado inicial: `pendiente`. |
| `/establecimientos/{id}/interaccion` | POST | Registra una interacción. Persiste `peso_interaccion` derivado del tipo (llamar a `compute_peso_interaccion`). Incrementa `sesion_usuario.total_vistas` si aplica. |
| `/establecimientos/{id}/favorito` | POST / DELETE | Guarda o elimina favorito. |
| `/establecimientos/{id}/reporte` | POST | Registra un reporte. |

---

### 5.3 Contenido

| Endpoint | Método | Descripción |
|---|---|---|
| `/categorias` | GET | Lista todas las categorías con su jerarquía (padre-hijo). |
| `/etiquetas` | GET | Lista todas las etiquetas. |
| `/geografía/colonias` | GET | Lista colonias con filtro por municipio. Usado en el formulario de registro de establecimiento. |

---

### 5.4 Recomendaciones

Estos son los endpoints más importantes del sistema. Todos aplican el principio Offline-First: solo leen de `recomendacion_generada`, no calculan scores.

| Endpoint | Método | Descripción |
|---|---|---|
| `/recomendaciones` | GET | Devuelve la lista pre-generada del usuario autenticado, agrupada por `categoria_recomendacion`. Calcula Haversine puntual para `distancia_km` usando la ubicación más reciente del usuario. Aplica fallback en cascada si la lista tiene menos de N resultados. |
| `/recomendaciones/{id}/click` | POST | Registra el click: actualiza `fue_clickeada = TRUE` y `fecha_click`. Único campo que FastAPI escribe en `recomendacion_generada`. |

**Lógica del endpoint principal `/recomendaciones`:**
1. Obtener la ubicación más reciente del usuario (`ubicacion_usuario`)
2. Leer las filas vigentes de `recomendacion_generada` para ese usuario (fecha de generación dentro del TTL)
3. Para cada fila, calcular `distancia_km` con Haversine y persistirlo
4. Si hay menos de N resultados, activar el fallback de radio (expandir y repetir)
5. Agrupar por `categoria_recomendacion` y devolver las secciones

---

### 5.5 Gamificación

| Endpoint | Método | Descripción |
|---|---|---|
| `/contribuciones` | POST | Registra una contribución. Si se aprueba (por admin), otorgar puntos: insertar en `log_puntos` y actualizar `puntos_experiencia` en la misma transacción. |
| `/usuarios/puntos` | GET | Historial de `log_puntos` del usuario. |
| `/usuarios/rango` | GET | Rango actual y puntos para el siguiente. |

---

### 5.6 Administración y Jobs Offline

Estos endpoints son de uso interno (protegidos por nivel de admin) y permiten disparar los jobs offline desde la interfaz de administración o por un scheduler externo.

| Endpoint | Método | Descripción |
|---|---|---|
| `/admin/establecimientos/pendientes` | GET | Lista establecimientos con `estado='pendiente'` para moderación. |
| `/admin/establecimientos/{id}/aprobar` | POST | Aprueba o rechaza un establecimiento. |
| `/admin/resenas/pendientes` | GET | Lista reseñas pendientes de moderación. |
| `/admin/resenas/{id}/aprobar` | POST | Aprueba o rechaza una reseña. Al aprobar: recalcular `total_resenas` y `calificacion_promedio` en la misma transacción. |
| `/admin/jobs/clustering` | POST | Dispara el job de K-Means offline. **Nunca se ejecuta dentro del mismo proceso HTTP; debe encolarse en un worker separado.** |
| `/admin/jobs/recomendaciones` | POST | Dispara el job de generación de recomendaciones offline. |
| `/admin/jobs/metricas` | POST | Dispara el job de actualización de métricas. |
| `/admin/jobs/nlp` | POST | Dispara el job de procesamiento NLP de reseñas. |
| `/admin/reconciliacion` | POST | Ejecuta el script de reconciliación de campos desnormalizados (ver §7 del diseño de BD). De emergencia. |

---

## 6. Jobs Offline — Motor de Recomendación

Los jobs son procesos independientes al servidor FastAPI. Pueden implementarse como:
- **Web Worker** (mencionado por el docente): un proceso Python separado que corre en segundo plano
- **Script programado**: ejecutado por un scheduler externo (cron, Celery, etc.)

No deben correr dentro de un endpoint HTTP normal porque pueden tardar minutos.

---

### 6.1 Job de K-Means (Clustering)

**Frecuencia sugerida:** cada noche o cada N horas dependiendo del volumen de usuarios nuevos.

**Lo que hace:**
1. Consultar todos los `vector_preferencias` de `usuario_visitante` (excluyendo usuarios inactivos hace más de 30 días)
2. Ejecutar K-Means sobre esos vectores para encontrar K clusters
3. Actualizar `cluster_usuario` con los nuevos centroides y `total_usuarios` por cluster
4. Actualizar `usuario_visitante.id_cluster` de cada usuario según su nuevo cluster asignado
5. Repetir el mismo proceso para `vector_caracteristicas` de establecimientos y `cluster_establecimiento`

**Decisión de diseño:** K nunca es fijo. El equipo debe elegir K (número de clusters) experimentalmente según el volumen de usuarios. Un K inicial razonable para Mérida con pocos cientos de usuarios es 3–5.

**Privacidad:** los vectores no contienen PII. `vector_preferencias` solo tiene pesos numéricos por categoría y rango de precio. Nunca incluye el email, nombre, coordenadas exactas ni ningún identificador del usuario (ver §1.6 del diseño de BD).

---

### 6.2 Job de Generación de Recomendaciones

**Frecuencia sugerida:** después de cada corrida de K-Means, o periódicamente (cada 6–12 horas).

**Lo que hace, por usuario:**
1. Determinar el radio de búsqueda (`radio_busqueda_km` del usuario)
2. Obtener establecimientos candidatos dentro de ese radio (filtrado geográfico usando coordenadas, no Haversine exacto — puede hacerse con bounding box para eficiencia)
3. Para cada categoría de recomendación (ver §1.8 del diseño de BD):
   - `cercania`: ordenar candidatos por distancia Haversine
   - `popularidad_zona`: ordenar por `popularidad_7d` de `metrica_establecimiento`
   - `preferencia_contenido`: usar `content_filter.get_content_based_recommendations`
   - `colaborativo_cluster`: usar `collab_filter.get_collaborative_recommendations`
   - `cold_start`: si `perfil_completado = FALSE`, usar popularidad dentro del cluster
   - `tendencia_informal`: candidatos con `es_informal=TRUE` ordenados por `score_boost_combinado`
   - `descubrimiento`: ítems de cluster distinto al habitual, con `diversity_score` alto
4. Insertar las filas en `recomendacion_generada` con todos los campos de caja blanca poblados (snapshots de scores, `radio_usado_km`, `fallback_nivel`)
5. **Antes de insertar:** limpiar las recomendaciones obsoletas del usuario anterior (TTL 7 días para no clicadas, 37 días para clicadas — ver §6.1 del diseño de BD)

**Invariante del job:** `radio_usado_km` debe estar poblado en **todas** las categorías, no solo en `cercania`. El radio actúa como pre-filtro geográfico universal.

---

### 6.3 Job de Métricas

**Frecuencia sugerida:** diariamente.

**Lo que hace:**
1. Para cada establecimiento activo, calcular `popularidad_7d` y `popularidad_30d` contando filas en `interaccion_usuario` dentro de las ventanas de tiempo
2. Recalcular `boost_proximidad_zona` (interacciones de usuarios dentro de 2 km del establecimiento)
3. Recalcular `score_boost_combinado` con la fórmula del §1.3 del diseño de BD
4. Actualizar `score_contenido_base` y `score_colaborativo_base` con los promedios de los usuarios del cluster
5. Actualizar `ultima_actualizacion` en cada fila de `metrica_establecimiento`

---

### 6.4 Job de NLP

**Frecuencia sugerida:** cada hora o tras cada ciclo de moderación de reseñas.

**Lo que hace:**
1. Consultar reseñas con `procesado_nlp = FALSE` y `estado = 'aprobado'`
2. Para cada reseña, calcular `polaridad` y `subjetividad` del campo `comentario`
3. Actualizar `resena.polaridad`, `resena.subjetividad` y `procesado_nlp = TRUE`
4. Recalcular `metrica_establecimiento.polaridad_promedio` para los establecimientos afectados

**Nota:** si el comentario de una reseña se edita después de ser aprobada, FastAPI debe resetear `procesado_nlp = FALSE` para que el job la reprocese en el siguiente ciclo.

---

### 6.5 Job de Archivado

**Frecuencia sugerida:** mensualmente.

**Lo que hace:**
1. Mover filas de `interaccion_usuario` con `fecha < NOW() - 90 días` a `interaccion_usuario_historico` y borrarlas de la tabla activa
2. Las métricas ya computadas no se ven afectadas porque se calcularon antes del archivado

> Las tablas `_historico` no tienen FKs por diseño intencional (ver §6 del diseño de BD). Son independientes del esquema vivo para no bloquear operaciones de mantenimiento.

---

## 7. Seguridad y Privacidad

Estas reglas complementan §1.6 del diseño de BD:

**Contraseñas:** FastAPI hashea con `bcrypt` antes de persistir. La BD nunca recibe la contraseña en texto claro. El campo `password_hash` nunca aparece en ningún schema `Response`.

**Campos sensibles restringidos:** `rfc` y `documento_verificacion` de `usuario_propietario` solo son accesibles por endpoints que exijan `nivel_admin >= X`. No deben incluirse en respuestas de endpoints públicos ni en los schemas `Response` generales.

**Email:** no debe exponerse en endpoints de búsqueda de establecimientos, ni en los vectores del motor. Solo el propio usuario y admins pueden verlo.

**Coordenadas GPS:** la política de máximo 3 registros en `ubicacion_usuario` es una invariante de privacidad (ver §1.2 y §1.6 del diseño de BD), no solo de rendimiento. FastAPI la aplica en cada INSERT de ubicación.

**Dispositivo:** solo se persiste el tipo clasificado (`movil`, `tablet`, etc.), no el `user_agent` raw. La detección del tipo se hace desde el header `User-Agent` del request en FastAPI.

**Sesiones:** el `id_sesion` es un UUID v4 generado por FastAPI al recibir el primer request de la sesión. Nunca lo genera el cliente.

---

## 8. Flujo de Datos Completo — Request a Response

### Caso: usuario abre la app y pide sus recomendaciones

```
Usuario abre la app
    │
    ▼
[POST /usuarios/ubicacion]
    │  FastAPI recibe lat/lon
    │  Inserta en ubicacion_usuario
    │  En la misma transacción: elimina registros > 3 del mismo usuario
    ▼
[GET /recomendaciones]
    │  FastAPI obtiene la ubicación más reciente del usuario
    │  Consulta recomendacion_generada (filas vigentes, por TTL)
    │  Para cada fila: calcula distancia Haversine con ranking.compute_haversine_km
    │  Persiste distancia_km en recomendacion_generada
    │  Si hay < N resultados: aplica fallback de radio (incrementa fallback_nivel)
    │  Agrupa por categoria_recomendacion
    ▼
Response JSON con secciones:
    "cercania": [...],
    "preferencia_contenido": [...],
    "colaborativo_cluster": [...],
    "tendencia_informal": [...],
    etc.
```

### Caso: usuario hace click en una recomendación

```
[POST /recomendaciones/{id}/click]
    │  FastAPI actualiza fue_clickeada = TRUE y fecha_click
    │  (Único campo que FastAPI escribe en recomendacion_generada)
    ▼
El siguiente ciclo del job offline considerará este click
como señal de feedback para reentrenar el K-Means
```

### Caso: usuario deja una reseña (flujo con desnormalizaciones)

```
[POST /establecimientos/{id}/resena]
    │  Pydantic valida calificacion (1-5), email del usuario
    │  FastAPI inserta en resena con estado='pendiente'
    │
    ▼
[POST /admin/resenas/{id}/aprobar]
    │  Admin aprueba la reseña (estado='aprobado')
    │  En la misma transacción:
    │    1. Actualizar establecimiento.total_resenas (COUNT)
    │    2. Actualizar establecimiento.calificacion_promedio (AVG)
    │    3. Insertar en contribucion_informacion si aplica
    │    4. Insertar en log_puntos con motivo='resena_aprobada'
    │    5. Actualizar usuario_visitante.puntos_experiencia (sumar puntos)
    │    6. Resetear resena.procesado_nlp = FALSE (para que el job NLP la procese)
    ▼
Job NLP (offline, siguiente ciclo):
    └─ Calcula polaridad y subjetividad
    └─ Actualiza resena.procesado_nlp = TRUE
    └─ Actualiza metrica_establecimiento.polaridad_promedio
```

---

*Para el diseño del esquema relacional, justificaciones de decisiones de arquitectura de datos, tablas completas y políticas de retención, consulta [EkiSystem_DB_Design.md](./EkiSystem_DB_Design.md).*
