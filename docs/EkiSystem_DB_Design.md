# EkiSystem — Diseño de Base de Datos

> **Proyecto:** Esquina Jach ki' (EKI) · Sistemas de Recomendación de Información  
> **Facultad de Matemáticas, UADY**  
> **Stack:** MySQL / MariaDB (Aiven) · FastAPI · SQLAlchemy / Alembic

---

## Índice

1. [Decisiones de Arquitectura](#1-decisiones-de-arquitectura)
   - 1.1 [Patrón de Herencia: Table-per-Type (TPT)](#11-patrón-de-herencia-table-per-type-tpt)
   - 1.2 [Algoritmo de Recomendación: Clustering + Híbrido en Cascada](#12-algoritmo-de-recomendación-clustering--híbrido-en-cascada)
   - 1.3 [Boosting por Proximidad Geográfica (Haversine)](#13-boosting-por-proximidad-geográfica-haversine)
   - 1.4 [Geografía Escalable](#14-geografía-escalable)
   - 1.5 [Desnormalizaciones Controladas — Inventario Completo](#15-desnormalizaciones-controladas--inventario-completo)
   - 1.6 [Privacidad y Anonimización de Datos](#16-privacidad-y-anonimización-de-datos)
   - 1.7 [Principio Offline-First para el Motor de Recomendación](#17-principio-offline-first-para-el-motor-de-recomendación)
   - 1.8 [Categorías de Recomendación](#18-categorías-de-recomendación)
2. [Cobertura de la Rúbrica](#2-cobertura-de-la-rúbrica)
3. [Convención de Nombres para SQLAlchemy / Alembic](#3-convención-de-nombres-para-sqlalchemy--alembic)
4. [Modelo ER — Tablas por Dominio](#4-modelo-er--tablas-por-dominio)
   - 4.1 [Dominio Usuarios](#41-dominio-usuarios)
   - 4.2 [Dominio Clustering](#42-dominio-clustering)
   - 4.3 [Dominio Establecimientos](#43-dominio-establecimientos)
   - 4.4 [Dominio Contenido](#44-dominio-contenido)
   - 4.5 [Dominio Motor de Recomendación](#45-dominio-motor-de-recomendación)
   - 4.6 [Dominio Interacciones y Gamificación](#46-dominio-interacciones-y-gamificación)
   - 4.7 [Dominio Geografía](#47-dominio-geografía)
5. [Índices Secundarios](#5-índices-secundarios)
6. [Políticas de Retención y Archivado](#6-políticas-de-retención-y-archivado)
7. [Invariantes de Integridad — Responsabilidades de la Capa API](#7-invariantes-de-integridad--responsabilidades-de-la-capa-api)
8. [Resumen de Relaciones del Motor](#8-resumen-de-relaciones-del-motor)
9. [Flujo de Primera Migración Real](#9-flujo-de-primera-migración-real)

---

## 1. Decisiones de Arquitectura

### 1.1 Patrón de Herencia: Table-per-Type (TPT)

Se usa **Joined Table Inheritance (Table-per-Type)** tanto para usuarios como para establecimientos. La regla es: una tabla base con atributos comunes y una tabla hija por cada subtipo con sus atributos propios. La PK de la tabla hija es simultáneamente FK hacia la tabla base.

**Por qué TPT y no las alternativas:**

| Patrón | Problema |
|---|---|
| Single Table (todo en una tabla con nullables) | Viola 3NF: columnas que no dependen de la llave primaria para todos los registros |
| Table-per-Class (duplicar campos comunes) | Redundancia directa, actualizaciones inconsistentes |
| **Table-per-Type (elegido)** | Sin redundancia, sin nullables forzados, cada atributo depende únicamente de su llave |

**Resultado práctico:** para saber el nombre de cualquier establecimiento siempre se consulta `establecimiento`. Para saber el número de piso de un local comercial, se hace JOIN con `local_comercial`. No hay información duplicada entre tablas.

> **Nota para Alembic:** `LOCAL` es una keyword reservada en MySQL. La tabla hija del local se llama `local_comercial` para evitar errores silenciosos en las migraciones autogeneradas.

---

### 1.2 Algoritmo de Recomendación: Clustering + Híbrido en Cascada

Se combinan dos enfoques en lugar de elegir uno. El flujo completo es:

#### Fase 1 — Clustering offline (Minería de Datos · K-Means)

- Se agrupan **usuarios** según su `vector_preferencias` (pesos por categoría, rango de precio tolerado, distancia máxima).
- Se agrupan **establecimientos** según su `vector_caracteristicas` (categorías, precio promedio, etiquetas, `es_informal`).
- Este proceso se ejecuta **fuera de línea** mediante un job periódico (web worker o script programado), tal como confirmó el docente. No bloquea ningún request del usuario.
- Los centroides de cada cluster se persisten en `cluster_usuario.centroide` y `cluster_establecimiento.centroide`.

#### Fase 2 — Cold Start (usuarios nuevos sin historial)

Cuando `perfil_completado = FALSE` o el usuario tiene menos de N interacciones:

1. Se le asigna un cluster provisional calculando la distancia euclidiana entre su `vector_preferencias` (construido en el onboarding) y cada `centroide` de `cluster_usuario`.
2. Las recomendaciones se generan con: popularidad dentro del cluster + filtrado por contenido desde preferencias declaradas.
3. No se usa componente colaborativo hasta acumular historial suficiente.

#### Fase 3 — Recomendación principal (usuarios con historial)

Combinación ponderada de tres señales:

```
score_final = w1 * score_contenido + w2 * score_colaborativo + w3 * score_boost
```

| Señal | Método | Descripción |
|---|---|---|
| `score_contenido` | Similitud coseno | Entre `vector_preferencias` del usuario y `vector_caracteristicas` del establecimiento |
| `score_colaborativo` | Item-to-Item dentro del cluster | "Usuarios de tu cluster también interactuaron con estos lugares" — acotado al cluster para eficiencia |
| `score_boost` | Haversine + bonus informal + popularidad_zona | Ver sección 1.3 |

**Por qué Item-Based y no User-Based:** los establecimientos cambian menos que los usuarios, haciendo las similitudes entre ítems más estables. Además, escala mejor con grandes volúmenes de usuarios.

**Por qué combinar clustering con híbrido:** el clustering reduce el espacio de búsqueda del colaborativo (se compara dentro del cluster, no contra todos los usuarios), y resuelve el cold start de forma natural sin lógica especial separada.

---

### 1.3 Boosting por Proximidad Geográfica (Haversine)

El boosting **no prioriza lo más nuevo** sino **lo más cercano y relevante para la zona**. La fórmula aplicada al momento de generar recomendaciones es:

```
score_boost = w_prox * (1 / (distancia_km + 0.1))
            + w_informal * es_informal
            + w_zona * popularidad_zona
```

- `distancia_km` se calcula con la **fórmula de Haversine** entre la última ubicación del usuario (`ubicacion_usuario`) y las coordenadas del establecimiento (`establecimiento.latitud`, `establecimiento.longitud`). No requiere API externa y es suficiente para el contexto urbano de Mérida.
- `+0.1` en el denominador evita división por cero si el usuario está literalmente encima del establecimiento.
- `es_informal` aplica un bonus fijo a puestos informales para cumplir la naturaleza diferenciadora de EkiSystem.
- `popularidad_zona` es el promedio de interacciones de usuarios dentro de un radio de 2 km del establecimiento, pre-computado en `metrica_establecimiento.boost_proximidad_zona`.
- `distancia_km` se persiste en `recomendacion_generada` en el momento de generación, lo que permite mostrarla en la caja blanca ("A 0.8 km · Popular cerca de ti") sin recalcularla en cada render del frontend.

**Escalabilidad futura:** si se requiere distancia real por calles en lugar de línea recta, el campo `distancia_km` ya está listo para recibir el valor de la Google Maps Distance Matrix API sin cambiar el esquema.

---

### 1.4 Geografía Escalable

Se mantiene la jerarquía completa `pais → estado_geo → municipio → colonia` aunque el proyecto inicia centrado en Mérida, Yucatán.

**Por qué no simplificar:** eliminar `pais` y `estado_geo` ahorraría dos tablas livianas pero forzaría una migración destructiva si el proyecto escala a otras ciudades. Con la jerarquía completa, escalar es solo agregar filas en el seed, sin tocar el esquema.

**Cumplimiento de 3NF:** si la dirección se guardara como texto en `establecimiento`, habría dependencia transitiva (el estado depende del municipio, no del establecimiento). La jerarquía normaliza eso correctamente.

**Nota de nomenclatura:** la tabla de estados geográficos se llama `estado_geo` en lugar de `estado` para evitar colisión con el campo `estado` (ENUM de flujo/moderación) que existe en múltiples tablas. Ver §7 para la convención.

El seed inicial carga `pais = MX`, `estado_geo = Yucatán`, y los municipios relevantes del área metropolitana de Mérida.

---

### 1.5 Desnormalizaciones Controladas — Inventario Completo

> [!IMPORTANT]
> Esta sección lista **todos** los campos que técnicamente violan la 3NF pero son intencionales y correctos. El equipo no debe tratarlos como fuente de verdad para reportes exactos. Para reportes, usar siempre las tablas fuente. La BD **no debe recibir escrituras directas** que pasen por alto la capa FastAPI, ya que estos campos se actualizan exclusivamente por la API o por jobs offline. Ver §7 para las invariantes de integridad.

| Tabla | Campo desnormalizado | Derivado de | Actualizado por | Justificación |
|---|---|---|---|---|
| `establecimiento` | `total_resenas` | `COUNT(*) FROM resena WHERE estado='aprobado'` | FastAPI (al aprobar reseña) | El motor lo consulta en cada generación de scores; un `COUNT` en caliente sería cuello de botella |
| `establecimiento` | `calificacion_promedio` | `AVG(calificacion) FROM resena WHERE estado='aprobado'` | FastAPI (al aprobar reseña) | Señal de contenido usada en cada cálculo de `score_contenido` |
| `establecimiento` | `es_informal` | Derivable de `tipo_establecimiento = 'puesto_informal'` | FastAPI (al registrar establecimiento) | Flag directo para boosting sin JOIN; se usa en cada cálculo de `score_boost` |
| `cluster_usuario` | `total_usuarios` | `COUNT(*) FROM usuario_visitante WHERE id_cluster = X` | Job offline K-Means | Monitoreo operativo; evita conteos frecuentes sobre tablas grandes |
| `cluster_establecimiento` | `total_establecimientos` | `COUNT(*) FROM establecimiento WHERE id_cluster = X` | Job offline K-Means | Igual que el anterior |
| `metrica_establecimiento` | `popularidad_7d` | `COUNT(*) FROM interaccion_usuario WHERE fecha > NOW()-7d` | Job offline periódico | Métrica pre-computada; calcularla en caliente bloquearía cada request |
| `metrica_establecimiento` | `popularidad_30d` | `COUNT(*) FROM interaccion_usuario WHERE fecha > NOW()-30d` | Job offline periódico | Igual que el anterior |
| `metrica_establecimiento` | `score_boost_combinado` | Fórmula derivable de los otros campos de la misma fila | Job offline periódico | Pre-cómputo para evitar recalcular la fórmula en cada request |
| `metrica_establecimiento` | `polaridad_promedio` | `AVG(resena.polaridad) WHERE estado='aprobado'` | Job offline NLP | Señal NLP agregada; el pipeline NLP es asíncrono y no puede correr en caliente |
| `sesion_usuario` | `total_vistas` | `COUNT(*) FROM historial_visita WHERE id_sesion = X` | FastAPI (en caliente) | Telemetría de sesión; se incrementa en el mismo request que registra la vista |
| `usuario_visitante` | `puntos_experiencia` | `SUM(puntos) FROM log_puntos WHERE id_usuario = X` | FastAPI (al otorgar puntos) | `log_puntos` es la fuente de verdad; `puntos_experiencia` es la suma materializada para consultas rápidas de ranking |
| `interaccion_usuario` | `peso_interaccion` | Derivable del `tipo_interaccion` según tabla de pesos fija | FastAPI (al insertar) | Evita CASE/WHEN en cada query del motor colaborativo |

**Script de reconciliación:** ante una desincronización (bug o escritura directa), existe el procedimiento documentado en §7 para recalcular todos estos campos desde las tablas fuente.

---

### 1.6 Privacidad y Anonimización de Datos

EkiSystem almacena datos personales sensibles (`password_hash`, `email`, `fecha_nacimiento`, `rfc`, `documento_verificacion`, coordenadas GPS). Para cumplir con buenas prácticas éticas en sistemas de recomendación (según el curso: *"Privacidad: proteger la información personal. Se debe considerar anonimizar los datos"*), se adoptan las siguientes reglas de diseño:

| Dato sensible | Estrategia aplicada |
|---|---|
| `password_hash` | Hash bcrypt en la capa FastAPI; la BD nunca recibe la contraseña en claro |
| `email` | Solo accesible por el propio usuario o admins; nunca expuesto en endpoints públicos ni en los vectores del motor |
| `fecha_nacimiento` | Se almacena en `usuario` pero el motor solo consume la **edad calculada** como entero; la fecha nunca llega a los vectores de clustering |
| `rfc` / `documento_verificacion` | Columnas de `usuario_propietario`; lectura restringida a admins por permiso en FastAPI |
| Coordenadas GPS (`ubicacion_usuario`) | Se conservan **solo los últimos 3 registros** por usuario (ver §4.1 `ubicacion_usuario`). El motor solo necesita la ubicación más reciente; los dos anteriores son respaldo ante errores de GPS. Esto limita la exposición en caso de acceso no autorizado, impidiendo triangular desplazamientos. Para el job offline de K-Means, las coordenadas se redondean a 3 decimales (~111 m de precisión) |
| `user_agent` / `dispositivo_usuario` | Se almacena el tipo detectado (móvil/tablet/escritorio) pero **no** el `user_agent` raw en producción, solo en desarrollo para depuración |
| Vectores de clustering | Los `vector_preferencias` y `vector_caracteristicas` son vectores numéricos **sin PII**; son seguros para el job offline |

**Regla general para el motor:** ningún campo que identifique directamente al usuario (`email`, `nombre`, `rfc`, coordenadas exactas) debe incluirse en los vectores enviados al job de clustering o al cálculo de scores.

---

### 1.7 Principio Offline-First para el Motor de Recomendación

> [!IMPORTANT]
> **La gran mayoría de los cálculos del motor NO se ejecutan en el momento del request del usuario.** Este principio es fundamental para la escalabilidad del sistema y debe respetarse al diseñar el backend.

Los sistemas de recomendación maduros separan dos fases bien diferenciadas:

| Fase | Cuándo ocurre | Qué se calcula | Quién lo ejecuta |
|---|---|---|---|
| **Offline (batch)** | Periódicamente (noche, cada N horas) | K-Means, scores base, métricas de popularidad, polaridad NLP, score_boost_combinado, listas de recomendación pre-generadas | Job programado (web worker / cron) |
| **Online (request)** | En el momento que el usuario abre la app | Selección de la lista ya generada, cálculo de distancia Haversine puntual, fallback por radio si aplica | FastAPI en tiempo real |

**Por qué offline-first:**
- El K-Means sobre todos los usuarios y establecimientos puede tomar segundos o minutos; es inviable en un request HTTP.
- `popularidad_7d` y `popularidad_30d` requieren agregar sobre tablas con millones de filas; calcularlos en caliente bloquearía la API.
- El pipeline NLP de reseñas (polaridad, subjetividad) es costoso y puede ejecutarse de forma asíncrona sin afectar la experiencia del usuario.
- Pre-generar las listas de recomendación y guardarlas en `recomendacion_generada` permite que el frontend reciba respuesta en milisegundos.

**Lo que sí ocurre online:**
- Calcular la distancia Haversine puntual entre la ubicación actual del usuario y los establecimientos candidatos de su lista pre-generada (el resultado se persiste en `recomendacion_generada.distancia_km`).
- Aplicar el fallback en cascada de radio de búsqueda si la lista pre-generada tiene menos de N resultados válidos.
- Registrar el click (`fue_clickeada = TRUE`) como feedback implícito para el próximo ciclo offline.

**Implicación para el backend:** FastAPI **no debe ejecutar** el K-Means, el cálculo de `score_colaborativo_base`, ni el pipeline NLP dentro de un endpoint HTTP. Estos se activan por separado (endpoint de administración protegido, scheduler, o web worker).

---

### 1.8 Categorías de Recomendación

EkiSystem contempla múltiples tipos de recomendación, cada uno con una lógica distinta y un propósito diferente en la interfaz. Esta categorización existe para que el backend sepa qué algoritmo aplicar y para que el frontend sepa cómo presentar la recomendación en la caja blanca.

> [!NOTE]
> El documento original solo consideraba explícitamente la recomendación por proximidad. Sin embargo, los algoritmos de recomendación implementados (filtrado por contenido, colaborativo, K-Means) producen naturalmente distintos tipos. Se documentan aquí para que el diseño del backend y frontend esté alineado.

| Categoría (`categoria_recomendacion`) | Descripción | Algoritmo principal | Señal dominante | Ejemplo de texto caja blanca |
|---|---|---|---|---|
| `cercania` | Establecimientos en el radio de búsqueda del usuario, ordenados por proximidad | Haversine + score_boost | `distancia_km`, `boost_proximidad_zona` | "A 0.4 km de ti" |
| `popularidad_zona` | Lo más interactuado por usuarios cercanos en los últimos 7–30 días | Métrica pre-computada | `popularidad_7d`, `boost_proximidad_zona` | "Popular cerca de ti esta semana" |
| `preferencia_contenido` | Afinidad entre el vector de preferencias del usuario y las características del establecimiento | Filtrado por contenido (coseno) | `score_contenido_base` | "Coincide con tus categorías favoritas" |
| `colaborativo_cluster` | "Usuarios como tú también van aquí" — colaborativo acotado al cluster del usuario | Item-to-item dentro del cluster | `score_colaborativo_base` | "Popular entre usuarios con gustos similares a los tuyos" |
| `cold_start` | Para usuarios nuevos sin historial: mezcla de popularidad global y preferencias declaradas en el onboarding | Popularidad + vector onboarding | `perfil_completado = FALSE` | "Lugares populares cerca de ti para empezar" |
| `descubrimiento` | Ítems de cluster distinto al habitual del usuario; serendipia intencional | Serendipia (diversity_score alto) | `es_descubrimiento = TRUE`, `diversity_score` | "Algo diferente que podría gustarte" |
| `tendencia_informal` | Puestos y carritos informales con alto boost en la zona; misión diferenciadora de EkiSystem | Haversine + bonus informal | `es_informal = TRUE`, `boost_informal` | "Joya informal cerca de ti" |

**Cómo se usa en el esquema:**

- `recomendacion_generada.categoria_recomendacion` — identifica el tipo de recomendación generada (nuevo campo, ver §4.5).
- `recomendacion_generada.razon_principal` — complementa con el motivo específico dentro de la categoría.
- El frontend puede agrupar la lista por categoría para generar secciones del tipo "Popular cerca de ti", "Para ti", "Descubrimientos", usando `categoria_recomendacion` como discriminador.
- Los jobs offline pre-generan listas por categoría de forma independiente, permitiendo actualizarlas con frecuencias distintas (p.ej. `cercania` se actualiza cuando el usuario se mueve; `tendencia_informal` se actualiza diariamente).

---

## 2. Cobertura de la Rúbrica

| Requisito | Pts | Implementación en el modelo |
|---|---|---|
| Inicio en frío | 5 | `cluster_usuario.centroide` + `usuario_visitante.perfil_completado` + `vector_preferencias` del onboarding + categoría `cold_start` en `recomendacion_generada` |
| Modelo híbrido | 10 | `score_contenido` (coseno) + `score_colaborativo` (item-to-item por cluster) en `recomendacion_generada`; categorías `preferencia_contenido` y `colaborativo_cluster` |
| Ranking y Boosting | 5 | `metrica_establecimiento.score_boost_combinado` con Haversine + bonus informal + popularidad_zona; categorías `cercania`, `popularidad_zona`, `tendencia_informal` |
| Recomendación orgánica y caja blanca | 5 | `recomendacion_generada.razon_principal` + `detalle_razon` + `categoria_recomendacion` + snapshots de scores individuales |
| Usabilidad de interfaz | 5 | Stack Tailwind + Vanilla JS; `categoria_recomendacion` permite al frontend organizar secciones de forma semántica |
| Extras (hasta 4 pts) | +4 | K-Means como minería de datos + Web workers para jobs de clustering offline |

---

## 3. Convención de Nombres para SQLAlchemy / Alembic

| Clase en `models.py` | Tabla en MySQL | Observación |
|---|---|---|
| `Usuario` | `usuario` | Reemplaza placeholder `User` |
| `UsuarioVisitante` | `usuario_visitante` | |
| `UsuarioPropietario` | `usuario_propietario` | |
| `Administrador` | `administrador` | |
| `RangoInformador` | `rango_informador` | |
| `ClusterUsuario` | `cluster_usuario` | **Nueva** |
| `ClusterEstablecimiento` | `cluster_establecimiento` | **Nueva** |
| `UbicacionUsuario` | `ubicacion_usuario` | **Nueva** |
| `SesionUsuario` | `sesion_usuario` | **Nueva** |
| `DispositivoUsuario` | `dispositivo_usuario` | **Nueva** |
| `Establecimiento` | `establecimiento` | Reemplaza placeholder `Vendor` |
| `Restaurante` | `restaurante` | |
| `LocalComercial` | `local_comercial` | `LOCAL` es keyword reservada en MySQL |
| `PuestoInformal` | `puesto_informal` | |
| `PropietarioEstablecimiento` | `propietario_establecimiento` | |
| `Categoria` | `categoria` | |
| `EstablecimientoCategoria` | `establecimiento_categoria` | |
| `Platillo` | `platillo` | |
| `Imagen` | `imagen` | |
| `Horario` | `horario` | |
| `Etiqueta` | `etiqueta` | |
| `EstablecimientoEtiqueta` | `establecimiento_etiqueta` | |
| `MetricaEstablecimiento` | `metrica_establecimiento` | **Nueva** |
| `RecomendacionGenerada` | `recomendacion_generada` | **Nueva** |
| `InteraccionUsuario` | `interaccion_usuario` | **Nueva** |
| `Resena` | `resena` | Reemplaza placeholder `UserRating` |
| `ContribucionInformacion` | `contribucion_informacion` | |
| `LogPuntos` | `log_puntos` | |
| `FavoritoGuardado` | `favorito_guardado` | |
| `HistorialVisita` | `historial_visita` | |
| `PreferenciaUsuario` | `preferencia_usuario` | |
| `Reporte` | `reporte` | |
| `Pais` | `pais` | |
| `EstadoGeo` | `estado_geo` | Renombrado desde `estado` para evitar colisión con el campo `estado` (ENUM de flujo) presente en múltiples tablas. Ver §1.4 |
| `Municipio` | `municipio` | |
| `Colonia` | `colonia` | |

---

## 4. Modelo ER — Tablas por Dominio

> **Notación:** `PK` = llave primaria · `FK` = llave foránea · `UK` = restricción única · `AI` = AUTO_INCREMENT · `nullable` = el campo acepta NULL.

---

### 4.1 Dominio Usuarios

#### `usuario` — Entidad base (TPT raíz)

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_usuario` | INT | **PK AI** |
| `email` | VARCHAR(255) | **UK** NOT NULL |
| `nombre` | VARCHAR(100) | NOT NULL |
| `apellido` | VARCHAR(100) | NOT NULL |
| `password_hash` | VARCHAR(255) | NOT NULL |
| `foto_perfil` | VARCHAR(500) | nullable |
| `fecha_nacimiento` | DATE | nullable — se usa para calcular edad en el motor; no se expone en vectores |
| `genero` | ENUM('masculino','femenino','otro','prefiero_no_decir') | nullable — variable demográfica para filtrado y cold start |
| `tipo_usuario` | ENUM('visitante','propietario','admin') | NOT NULL — discriminador TPT |
| `activo` | BOOLEAN | DEFAULT TRUE |
| `fecha_registro` | DATETIME | DEFAULT NOW() |

---

#### `rango_informador`

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_rango` | TINYINT | **PK AI** |
| `nivel` | TINYINT | **UK** NOT NULL |
| `nombre` | VARCHAR(50) | NOT NULL |
| `puntos_minimos` | INT | NOT NULL |
| `factor_confianza` | DECIMAL(3,2) | DEFAULT 0.50 — rango 0.0–1.0, rige rigor de moderación |
| `descripcion` | TEXT | nullable |
| `color_badge` | CHAR(7) | nullable — hex color para frontend |

> El `factor_confianza` determina qué tan estrictamente los administradores deben revisar las contribuciones de ese rango. A menor rango, mayor rigor.

---

#### `usuario_visitante` — Hereda de `usuario`

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_usuario` | INT | **PK + FK → usuario** |
| `id_rango` | TINYINT | **FK → rango_informador** |
| `id_cluster` | INT | **FK → cluster_usuario** nullable — NULL hasta primera asignación |
| `puntos_experiencia` | INT | DEFAULT 0 — suma materializada de `log_puntos` (ver §1.5) |
| `puntos_reputacion` | INT | DEFAULT 0 |
| `perfil_completado` | BOOLEAN | DEFAULT FALSE — señal de cold start |
| `fecha_ultima_actividad` | DATETIME | nullable — peso en filtrado colaborativo |
| `radio_busqueda_km` | TINYINT | DEFAULT 5 — radio en km que el usuario elige para buscar establecimientos; usado como punto de partida del fallback en cascada |
| `vector_preferencias` | JSON | vector numérico: pesos por categoría y rango de precio tolerado — **no incluye distancia**, que se gestiona mediante `radio_busqueda_km` |

> `vector_preferencias` se construye en el onboarding y se actualiza con cada interacción significativa. Es la entrada del K-Means para asignar cluster y la base del filtrado por contenido.

---

#### `usuario_propietario` — Hereda de `usuario_visitante`

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_usuario` | INT | **PK + FK → usuario_visitante** |
| `razon_social` | VARCHAR(255) | nullable |
| `rfc` | VARCHAR(20) | nullable |
| `telefono_contacto` | VARCHAR(20) | nullable |
| `documento_verificacion` | VARCHAR(500) | nullable — ruta/URL al documento |
| `verificado` | BOOLEAN | DEFAULT FALSE |
| `fecha_verificacion` | DATETIME | nullable |

> Hereda de `usuario_visitante` porque un propietario también es informador y acumula puntos. Evita duplicar los campos de rango y puntos.

---

#### `administrador` — Hereda de `usuario` (rama paralela)

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_usuario` | INT | **PK + FK → usuario** |
| `nivel_admin` | TINYINT | DEFAULT 1 |
| `departamento` | VARCHAR(100) | nullable |

> Hereda directamente de `usuario`, **no** de `usuario_visitante`, porque no participa en el sistema de puntos ni tiene rango de informador.

---

#### `ubicacion_usuario` — Soporte para boosting por proximidad

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_ubicacion` | INT | **PK AI** |
| `id_usuario` | INT | **FK → usuario** |
| `latitud` | DECIMAL(10,8) | NOT NULL |
| `longitud` | DECIMAL(11,8) | NOT NULL |
| `precision_metros` | INT | nullable — precisión del GPS |
| `id_sesion` | VARCHAR(36) | **FK → sesion_usuario** nullable — vincula la ubicación a la sesión activa |
| `fecha_registro` | DATETIME | DEFAULT NOW() |

> **Política de retención (privacidad y eficiencia):** se conservan únicamente los **últimos 3 registros** por usuario. Cada vez que FastAPI inserta una nueva ubicación, elimina en la misma transacción los registros del mismo usuario que superen ese límite. Esto evita que un historial irrestricto permita triangular movimientos del usuario en caso de acceso no autorizado, y mantiene el volumen de la tabla acotado. El motor siempre usa el registro más reciente para Haversine; los dos anteriores sirven de respaldo si el registro activo llega con error de GPS.

---

#### `sesion_usuario` — Unidad de análisis de comportamiento

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_sesion` | VARCHAR(36) | **PK** — UUID v4 generado por FastAPI al recibir el primer request de la sesión; nunca por el cliente |
| `id_usuario` | INT | **FK → usuario** NOT NULL |
| `fecha_inicio` | DATETIME | NOT NULL DEFAULT NOW() |
| `fecha_fin` | DATETIME | nullable — se registra al cerrar la app o tras timeout de inactividad |
| `duracion_segundos` | INT | nullable — calculado al cerrar la sesión |
| `total_vistas` | INT | DEFAULT 0 — contador desnormalizado (ver §1.5); número de establecimientos visualizados en la sesión |
| `id_dispositivo` | INT | **FK → dispositivo_usuario** nullable |

> Una sesión es la secuencia de vistas/interacciones realizadas por un usuario durante una visita continua a la app. Permite calcular el "propósito" de cada visita (búsqueda exploratoria vs. visita directa) y enriquece el filtrado colaborativo. `interaccion_usuario` e `historial_visita` referencian esta tabla vía `id_sesion`.

---

#### `dispositivo_usuario` — Contexto de hardware (capturado automáticamente)

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_dispositivo` | INT | **PK AI** |
| `id_usuario` | INT | **FK → usuario** NOT NULL |
| `tipo_dispositivo` | ENUM('movil','tablet','escritorio','desconocido') | NOT NULL — detectado del User-Agent HTTP |
| `sistema_operativo` | VARCHAR(50) | nullable — ej: 'Android 14', 'iOS 17.4' |
| `es_ultimo` | BOOLEAN | DEFAULT TRUE — solo el dispositivo más reciente tiene TRUE |
| `fecha_deteccion` | DATETIME | DEFAULT NOW() |

> **No se solicita al usuario.** El tipo de dispositivo se extrae automáticamente del header `User-Agent` en cada request a FastAPI. Solo se persiste el tipo clasificado (no el `user_agent` raw en producción, ver §1.6). Se usa como variable de contexto en el ranking: en móvil se priorizan establecimientos más cercanos y se reduce la lista; en escritorio se puede ampliar.

> **Invariante `es_ultimo`:** antes de insertar un nuevo dispositivo para un usuario, FastAPI debe ejecutar `UPDATE dispositivo_usuario SET es_ultimo = FALSE WHERE id_usuario = X AND es_ultimo = TRUE`. Esto garantiza que nunca haya más de un dispositivo con `es_ultimo = TRUE` por usuario. Ver §7.

---

### 4.2 Dominio Clustering

#### `cluster_usuario`

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_cluster` | INT | **PK AI** |
| `nombre_cluster` | VARCHAR(100) | ej: "Exploradores de puestos informales" |
| `centroide` | JSON | vector centroide para asignación de nuevos usuarios |
| `descripcion` | TEXT | nullable |
| `total_usuarios` | INT | DEFAULT 0 — contador desnormalizado (ver §1.5); para monitoreo operativo |
| `fecha_actualizacion` | DATETIME | cuándo se ejecutó el último K-Means |

---

#### `cluster_establecimiento`

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_cluster` | INT | **PK AI** |
| `nombre_cluster` | VARCHAR(100) | ej: "Comida yucateca económica" |
| `centroide` | JSON | vector centroide del cluster |
| `descripcion` | TEXT | nullable |
| `total_establecimientos` | INT | DEFAULT 0 — contador desnormalizado (ver §1.5) |
| `fecha_actualizacion` | DATETIME | |

---

### 4.3 Dominio Establecimientos

#### `establecimiento` — Entidad base (TPT raíz)

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_establecimiento` | INT | **PK AI** |
| `nombre` | VARCHAR(200) | NOT NULL |
| `descripcion` | TEXT | nullable |
| `latitud` | DECIMAL(10,8) | NOT NULL — coordenada para Haversine |
| `longitud` | DECIMAL(11,8) | NOT NULL |
| `direccion_texto` | VARCHAR(500) | nullable — descripción libre complementaria |
| `id_colonia` | INT | **FK → colonia** nullable |
| `id_cluster` | INT | **FK → cluster_establecimiento** nullable |
| `vector_caracteristicas` | JSON | vector para K-Means y contenido: categorías, precio, etiquetas, `es_informal` |
| `tipo_establecimiento` | ENUM('restaurante','local','puesto_informal') | NOT NULL — discriminador TPT |
| `es_informal` | BOOLEAN | DEFAULT FALSE — desnormalizado (ver §1.5); flag directo para boosting sin JOIN |
| `estado` | ENUM('pendiente','aprobado','rechazado','suspendido') | DEFAULT 'pendiente' |
| `es_activo` | BOOLEAN | DEFAULT FALSE |
| `id_usuario_registro` | INT | **FK → usuario** NOT NULL |
| `id_admin_aprobacion` | INT | **FK → administrador** nullable |
| `fecha_registro` | DATETIME | DEFAULT NOW() |
| `fecha_aprobacion` | DATETIME | nullable |
| `total_resenas` | INT | DEFAULT 0 — desnormalizado (ver §1.5) |
| `calificacion_promedio` | DECIMAL(3,2) | DEFAULT 0.00 — desnormalizado (ver §1.5) |

---

#### `restaurante` — Hereda de `establecimiento`

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_restaurante` | INT | **PK + FK → establecimiento** |
| `id_categoria_principal` | INT | **FK → categoria** nullable |
| `capacidad` | INT | nullable |
| `acepta_reservaciones` | BOOLEAN | DEFAULT FALSE |
| `servicio_domicilio` | BOOLEAN | DEFAULT FALSE |
| `telefono` | VARCHAR(20) | nullable |
| `sitio_web` | VARCHAR(500) | nullable |
| `facebook_url` | VARCHAR(500) | nullable |
| `instagram_url` | VARCHAR(500) | nullable |
| `precio_promedio` | DECIMAL(8,2) | nullable |

---

#### `local_comercial` — Hereda de `establecimiento`

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_local` | INT | **PK + FK → establecimiento** |
| `numero_local` | VARCHAR(20) | nullable |
| `nivel_piso` | VARCHAR(10) | nullable |
| `nombre_edificio` | VARCHAR(200) | nullable — ej: "Mercado Lucas de Gálvez" |
| `tiene_area_comedor` | BOOLEAN | DEFAULT TRUE |

---

#### `puesto_informal` — Hereda de `establecimiento`

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_puesto` | INT | **PK + FK → establecimiento** |
| `es_movil` | BOOLEAN | DEFAULT FALSE — food truck vs fijo |
| `ubicacion_referencia` | TEXT | nullable — "frente al Parque Santa Lucía" |
| `dias_tipicos` | VARCHAR(100) | nullable — texto libre por naturaleza informal |
| `horario_aproximado` | VARCHAR(100) | nullable |

> `dias_tipicos` y `horario_aproximado` son texto libre aquí (no FK a `horario`) porque un puesto informal por definición no tiene horarios rígidos. Los restaurantes y locales sí usan la tabla `horario` estructurada.

---

#### `propietario_establecimiento` — Pivote N:M con metadatos

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_propietario` | INT | **PK + FK → usuario_propietario** |
| `id_establecimiento` | INT | **PK + FK → establecimiento** |
| `estado` | ENUM('pendiente','aprobado','rechazado') | DEFAULT 'pendiente' |
| `fecha_solicitud` | DATETIME | DEFAULT NOW() |
| `fecha_aprobacion` | DATETIME | nullable |
| `id_admin_aprobacion` | INT | **FK → administrador** nullable |
| `documento_prueba` | VARCHAR(500) | nullable |

> Un propietario puede tener múltiples establecimientos y cada vinculación requiere aprobación individual del administrador.

---

### 4.4 Dominio Contenido

#### `categoria` — Auto-referencial para subcategorías

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_categoria` | INT | **PK AI** |
| `nombre` | VARCHAR(100) | **UK** NOT NULL |
| `id_categoria_padre` | INT | **FK → categoria** nullable — ej: "Mexicana" → "Yucateca" |
| `descripcion` | VARCHAR(500) | nullable |
| `icono` | VARCHAR(200) | nullable |

---

#### `establecimiento_categoria` — Pivote N:M

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_establecimiento` | INT | **PK + FK → establecimiento** |
| `id_categoria` | INT | **PK + FK → categoria** |

---

#### `etiqueta`

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_etiqueta` | INT | **PK AI** |
| `nombre` | VARCHAR(50) | **UK** NOT NULL |
| `descripcion` | VARCHAR(200) | nullable |

> Separadas de `categoria` porque son descriptores cualitativos ("económico", "familiar", "vegano", "abierto 24h"), no clasificaciones jerárquicas.

---

#### `establecimiento_etiqueta` — Pivote N:M

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_establecimiento` | INT | **PK + FK → establecimiento** |
| `id_etiqueta` | INT | **PK + FK → etiqueta** |

---

#### `platillo`

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_platillo` | INT | **PK AI** |
| `id_establecimiento` | INT | **FK → establecimiento** NOT NULL |
| `nombre` | VARCHAR(200) | NOT NULL |
| `descripcion` | TEXT | nullable |
| `precio` | DECIMAL(8,2) | nullable |
| `disponible` | BOOLEAN | DEFAULT TRUE |
| `id_usuario_registro` | INT | **FK → usuario** NOT NULL |
| `estado` | ENUM('pendiente','aprobado','rechazado') | DEFAULT 'pendiente' |
| `fecha_registro` | DATETIME | DEFAULT NOW() |

---

#### `imagen`

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_imagen` | INT | **PK AI** |
| `id_establecimiento` | INT | **FK → establecimiento** NOT NULL |
| `url_imagen` | VARCHAR(500) | NOT NULL |
| `tipo` | ENUM('exterior','interior','platillo','menu','otro') | DEFAULT 'otro' |
| `id_usuario_upload` | INT | **FK → usuario** NOT NULL |
| `fecha_upload` | DATETIME | DEFAULT NOW() |
| `estado` | ENUM('pendiente','aprobado','rechazado') | DEFAULT 'pendiente' |
| `es_principal` | BOOLEAN | DEFAULT FALSE |

---

#### `horario`

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_horario` | INT | **PK AI** |
| `id_establecimiento` | INT | **FK → establecimiento** NOT NULL |
| `dia_semana` | TINYINT | NOT NULL — 0=Domingo … 6=Sábado |
| `hora_apertura` | TIME | nullable |
| `hora_cierre` | TIME | nullable |
| `cerrado` | BOOLEAN | DEFAULT FALSE |

> **UNIQUE(`id_establecimiento`, `dia_semana`)** — exactamente un registro por día por establecimiento.

---

### 4.5 Dominio Motor de Recomendación

#### `metrica_establecimiento` — Scores pre-computados (actualización offline)

> Todos los campos de esta tabla se calculan y actualizan **exclusivamente por jobs offline** (ver §1.7). FastAPI solo los lee; nunca los escribe directamente salvo el script de reconciliación.

| Campo | Tipo | Descripción |
|---|---|---|
| `id_establecimiento` | INT | **PK + FK → establecimiento** |
| `score_contenido_base` | DECIMAL(5,4) | Promedio de similitudes coseno con perfiles de usuarios que lo visitaron — calculado offline |
| `score_colaborativo_base` | DECIMAL(5,4) | Frecuencia de aparición en listas de usuarios similares dentro del cluster — calculado offline |
| `boost_proximidad_zona` | DECIMAL(5,4) | Popularidad relativa entre usuarios en radio de 2 km — actualizado offline periódicamente |
| `boost_informal` | DECIMAL(3,2) | 0.0 o valor fijo si `es_informal = TRUE` |
| `score_boost_combinado` | DECIMAL(5,4) | Resultado de la fórmula de boosting pre-calculado offline (ver §1.5) |
| `popularidad_7d` | INT | Interacciones en los últimos 7 días — calculado por job offline (ver §1.5) |
| `popularidad_30d` | INT | Interacciones en los últimos 30 días — calculado por job offline (ver §1.5) |
| `polaridad_promedio` | DECIMAL(4,3) | nullable — promedio de `resena.polaridad` de las reseñas aprobadas; calculado por job NLP offline (ver §1.5) |
| `ultima_actualizacion` | DATETIME | Timestamp del último job offline que actualizó esta fila |

---

#### `recomendacion_generada` — Caché del motor + soporte de caja blanca

> Las filas de esta tabla son el resultado de los jobs offline del motor. FastAPI las lee para servir al usuario; el motor las escribe (vía job offline o endpoint de administración). El único campo que FastAPI actualiza en tiempo real es `fue_clickeada` y `fecha_click`, como feedback implícito.

> **Política de retención:** ver §6.1 para la estrategia de TTL y archivado de esta tabla.

| Campo | Tipo | Descripción |
|---|---|---|
| `id_recomendacion` | INT AI | **PK** |
| `id_usuario` | INT | **FK → usuario** |
| `id_establecimiento` | INT | **FK → establecimiento** |
| `categoria_recomendacion` | ENUM('cercania','popularidad_zona','preferencia_contenido','colaborativo_cluster','cold_start','descubrimiento','tendencia_informal') | Categoría del tipo de recomendación (ver §1.8) — el frontend usa este campo para agrupar secciones |
| `posicion` | TINYINT | Ranking dentro de la lista del usuario y categoría (1 = más relevante) |
| `score_total` | DECIMAL(5,4) | Score combinado final en el momento de generación |
| `score_contenido_usado` | DECIMAL(5,4) | Snapshot del score de contenido — para caja blanca |
| `score_colaborativo_usado` | DECIMAL(5,4) | Snapshot del score colaborativo — para caja blanca |
| `score_boost_aplicado` | DECIMAL(5,4) | Snapshot del boost aplicado — para caja blanca |
| `distancia_km` | DECIMAL(8,3) | Distancia Haversine calculada al momento de servir la recomendación al usuario (online) |
| `radio_usado_km` | TINYINT | NOT NULL — radio usado como pre-filtro geográfico de candidatos en el job offline. Aplica a **todas las categorías**, no solo a `cercania`: aunque `preferencia_contenido` o `colaborativo_cluster` no rankean por distancia, el job siempre acota el espacio de candidatos por radio antes de aplicar el scoring (no tiene sentido recomendar un lugar a 40 km aunque coincida perfectamente con las preferencias). Puede ser mayor a `radio_busqueda_km` si se aplicó fallback. El job offline **debe siempre poblar este campo**; ver invariante en §7 |
| `fallback_nivel` | TINYINT | DEFAULT 0 — 0 = radio normal del usuario; 1 = radio expandido al doble; 2 = radio expandido al municipio completo. Si el backend no encontró nada en ningún nivel, devuelve lista vacía y el frontend muestra el mensaje correspondiente |
| `razon_principal` | ENUM('preferencia_categoria','historial_similar','popular_zona','colaborativo','cluster_similar','cercano','cold_start','descubrimiento','tendencia_informal') | Caja blanca — motivo específico dentro de la categoría |
| `detalle_razon` | VARCHAR(200) | Texto legible: "A 0.8 km · Popular entre usuarios como tú" |
| `estrategia_usada` | ENUM('contenido','colaborativo','cold_start','hibrido','cluster','popularidad','serendipia') | Componente del motor que generó esta recomendación |
| `fecha_generacion` | DATETIME | Timestamp del job offline que generó esta recomendación — para invalidación de caché y TTL |
| `fue_clickeada` | BOOLEAN | DEFAULT FALSE — feedback implícito; FastAPI actualiza este campo en tiempo real al recibir el click |
| `fecha_click` | DATETIME | nullable |
| `es_descubrimiento` | BOOLEAN | DEFAULT FALSE — TRUE si el ítem pertenece a un cluster distinto al habitual del usuario (señal de serendipia) |
| `diversity_score` | DECIMAL(5,4) | nullable — `1 - similitud_coseno_promedio` con los demás ítems de la misma lista; mayor valor = más distinto del resto |

> **Mecanismo de serendipia:** al generar la lista para un usuario, se reserva un mínimo de 1–2 posiciones en la categoría `descubrimiento` para ítems con `diversity_score` alto y cluster distinto al del usuario (`es_descubrimiento = TRUE`). Esto evita la burbuja de filtro documentada en el Tema 2 del curso.

> **Caja blanca:** los snapshots de scores individuales permiten al frontend mostrar exactamente qué peso tuvo cada señal en esa recomendación específica. La combinación `categoria_recomendacion` + `razon_principal` + `detalle_razon` da tres niveles de detalle: contexto semántico, motivo técnico y texto legible para el usuario.

---

#### `interaccion_usuario` — Señal granular para filtrado colaborativo

> Esta tabla es la de mayor volumen del sistema. Ver §6.2 para la política de archivado.

| Campo | Tipo | Descripción |
|---|---|---|
| `id_interaccion` | INT AI | **PK** |
| `id_usuario` | INT | **FK → usuario** |
| `id_establecimiento` | INT | **FK → establecimiento** |
| `tipo_interaccion` | ENUM('vista_detalle','guardado_favorito','compartido','llamada_telefono','abrir_maps','resena_dejada','ruta_calculada') | |
| `peso_interaccion` | DECIMAL(3,2) | Desnormalizado (ver §1.5) — peso pre-calculado al insertar: vista=0.1, favorito=0.5, reseña=1.0, ruta=0.9 |
| `id_sesion` | VARCHAR(36) | **FK → sesion_usuario** nullable — permite agrupar interacciones por visita |
| `fecha` | DATETIME | DEFAULT NOW() |

> `ruta_calculada` es la señal de intención más fuerte: el usuario activamente quiere ir al lugar. Se le asigna peso alto (0.9). El campo `peso_interaccion` pre-calculado evita recalcular en cada corrida del motor colaborativo.

---

### 4.6 Dominio Interacciones y Gamificación

#### `contribucion_informacion`

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_contribucion` | INT | **PK AI** |
| `id_usuario` | INT | **FK → usuario_visitante** NOT NULL |
| `id_establecimiento` | INT | **FK → establecimiento** nullable — NULL cuando se registra un lugar nuevo |
| `tipo_contribucion` | ENUM('nuevo_lugar','edicion_info','nueva_foto','nuevo_platillo','nueva_resena') | NOT NULL |
| `descripcion_cambio` | TEXT | nullable |
| `estado` | ENUM('pendiente','aprobado','rechazado') | DEFAULT 'pendiente' |
| `id_admin_revision` | INT | **FK → administrador** nullable |
| `fecha_contribucion` | DATETIME | DEFAULT NOW() |
| `fecha_revision` | DATETIME | nullable |
| `puntos_otorgados` | INT | DEFAULT 0 |

---

#### `log_puntos` — Registro inmutable de auditoría

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_log` | INT | **PK AI** |
| `id_usuario` | INT | **FK → usuario_visitante** NOT NULL |
| `puntos` | INT | NOT NULL — positivo o negativo |
| `motivo` | ENUM('contribucion_aprobada','resena_aprobada','foto_aprobada','nuevo_lugar','penalizacion','subida_rango') | NOT NULL |
| `id_contribucion` | INT | **FK → contribucion_informacion** nullable |
| `fecha` | DATETIME | DEFAULT NOW() |

> Esta tabla **nunca se modifica ni se borra**. Solo crece. Los `puntos_experiencia` en `usuario_visitante` son la suma materializada de este log (ver §1.5). Permite auditoría completa y recalcular el total si fuera necesario.

---

#### `resena`

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_resena` | INT | **PK AI** |
| `id_usuario` | INT | **FK → usuario** NOT NULL |
| `id_establecimiento` | INT | **FK → establecimiento** NOT NULL |
| `calificacion` | TINYINT | NOT NULL — CHECK(1 ≤ calificacion ≤ 5) |
| `comentario` | TEXT | nullable |
| `fecha_resena` | DATETIME | DEFAULT NOW() |
| `estado` | ENUM('pendiente','aprobado','rechazado') | DEFAULT 'pendiente' |
| `id_admin_revision` | INT | **FK → administrador** nullable |
| `polaridad` | DECIMAL(4,3) | nullable — rango [-1.000, 1.000]; valores negativos indican crítica, positivos elogio |
| `subjetividad` | DECIMAL(4,3) | nullable — rango [0.000, 1.000]; 0 = totalmente objetivo, 1 = totalmente subjetivo |
| `sentimiento_label` | ENUM('negativo','neutro','positivo') | nullable — etiqueta derivada de `polaridad` para consultas rápidas |
| `procesado_nlp` | BOOLEAN | DEFAULT FALSE — flag; se pone TRUE tras ejecutar el pipeline de análisis NLP offline |
| `fecha_actualizacion` | DATETIME | nullable — ON UPDATE NOW(); al detectar cambio en `comentario`, FastAPI resetea `procesado_nlp = FALSE` para forzar reprocesamiento |

> Los campos NLP se llenan de forma **asíncrona** (job offline) después de que la reseña es aprobada. El campo `procesado_nlp` evita reprocesar reseñas ya analizadas; `fecha_actualizacion` detecta ediciones posteriores que invalidan el análisis previo.

> **UNIQUE(`id_usuario`, `id_establecimiento`)** — exactamente una reseña por usuario por establecimiento.

---

#### `favorito_guardado` — Pivote N:M

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_usuario` | INT | **PK + FK → usuario** |
| `id_establecimiento` | INT | **PK + FK → establecimiento** |
| `fecha_guardado` | DATETIME | DEFAULT NOW() |

---

#### `historial_visita`

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_visita` | INT | **PK AI** |
| `id_usuario` | INT | **FK → usuario** NOT NULL |
| `id_establecimiento` | INT | **FK → establecimiento** NOT NULL |
| `fecha_visita` | DATETIME | DEFAULT NOW() |
| `origen` | ENUM('recomendacion','busqueda','directo','favorito') | NOT NULL |
| `id_sesion` | VARCHAR(36) | **FK → sesion_usuario** nullable |

> Permite múltiples visitas del mismo usuario al mismo lugar. Alimenta `popularidad_7d` y `popularidad_30d` en `metrica_establecimiento` mediante el job offline de métricas.

---

#### `preferencia_usuario` — Pivote N:M con peso

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_usuario` | INT | **PK + FK → usuario** |
| `id_categoria` | INT | **PK + FK → categoria** |
| `peso` | DECIMAL(3,2) | DEFAULT 1.0 — peso de esta categoría en el perfil |
| `fecha_actualizacion` | DATETIME | DEFAULT NOW() |

---

#### `reporte`

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_reporte` | INT | **PK AI** |
| `id_usuario` | INT | **FK → usuario** NOT NULL |
| `id_establecimiento` | INT | **FK → establecimiento** NOT NULL |
| `tipo_reporte` | ENUM('info_incorrecta','lugar_cerrado','foto_inapropiada','spam','otro') | NOT NULL |
| `descripcion` | TEXT | nullable |
| `estado` | ENUM('pendiente','resuelto','descartado') | DEFAULT 'pendiente' |
| `fecha_reporte` | DATETIME | DEFAULT NOW() |
| `id_admin_resolucion` | INT | **FK → administrador** nullable |

---

### 4.7 Dominio Geografía

> **Nota de nomenclatura:** la tabla de estados geográficos se llama `estado_geo` (no `estado`) para evitar colisión con el campo `estado` ENUM presente en `establecimiento`, `resena`, `contribucion_informacion` y otras tablas. En queries con JOINs, esta distinción previene ambigüedades. Ver §1.4.

#### `pais`

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_pais` | CHAR(2) | **PK** — código ISO (ej: 'MX', 'US') |
| `nombre` | VARCHAR(100) | NOT NULL |

---

#### `estado_geo`

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_estado` | INT | **PK AI** |
| `id_pais` | CHAR(2) | **FK → pais** NOT NULL |
| `nombre` | VARCHAR(100) | NOT NULL |

---

#### `municipio`

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_municipio` | INT | **PK AI** |
| `id_estado` | INT | **FK → estado_geo** NOT NULL |
| `nombre` | VARCHAR(100) | NOT NULL |

---

#### `colonia`

| Campo | Tipo | Restricciones |
|---|---|---|
| `id_colonia` | INT | **PK AI** |
| `id_municipio` | INT | **FK → municipio** NOT NULL |
| `nombre` | VARCHAR(200) | NOT NULL |
| `codigo_postal` | VARCHAR(10) | nullable |

> El seed inicial carga `pais = MX`, `estado_geo = Yucatán`, y los municipios del área metropolitana de Mérida. Escalar a otras ciudades es solo agregar filas, sin modificar el esquema.

---

## 5. Índices Secundarios

> Los índices de PK, FK y UK son creados automáticamente por MySQL. Esta sección documenta los **índices secundarios adicionales** necesarios para el rendimiento del motor de recomendación y los patrones de consulta frecuentes. Deben crearse manualmente en la migración inicial.

### 5.1 Índices de alto impacto (obligatorios)

| Tabla | Índice | Justificación |
|---|---|---|
| `interaccion_usuario` | `IDX(id_usuario, fecha)` | Reconstruir el historial reciente de un usuario — consulta del motor colaborativo |
| `interaccion_usuario` | `IDX(id_establecimiento, fecha)` | Calcular `popularidad_7d` y `popularidad_30d` en el job offline — base de la métrica de trending |
| `recomendacion_generada` | `IDX(id_usuario, categoria_recomendacion, fecha_generacion)` | Recuperar la lista vigente de un usuario por categoría — consulta principal del endpoint de recomendaciones |
| `recomendacion_generada` | `IDX(id_usuario, id_establecimiento)` | Evitar recomendaciones duplicadas en la misma lista |
| `resena` | `IDX(id_establecimiento, estado)` | Calcular `calificacion_promedio` y `total_resenas` sobre reseñas aprobadas |
| `historial_visita` | `IDX(id_usuario, fecha_visita)` | Historial reciente del usuario — consulta frecuente del motor |
| `ubicacion_usuario` | `IDX(id_usuario, fecha_registro)` | Política de retención: obtener los 3 más recientes y eliminar el resto |

### 5.2 Índices de impacto medio (recomendados)

| Tabla | Índice | Justificación |
|---|---|---|
| `establecimiento` | `IDX(estado, es_activo)` | Filtrar establecimientos aprobados y activos — base de todas las queries del motor |
| `establecimiento` | `IDX(id_colonia)` | Búsquedas geográficas por colonia |
| `sesion_usuario` | `IDX(id_usuario, fecha_inicio)` | Sesiones recientes del usuario |
| `contribucion_informacion` | `IDX(id_usuario, estado)` | Dashboard del contribuidor |
| `resena` | `IDX(procesado_nlp)` | Job offline de NLP: encontrar reseñas pendientes de procesamiento |
| `historial_visita` | `IDX(id_usuario, id_establecimiento, fecha_visita)` | Optimizar query "¿ya visitó este lugar hoy?" sin UNIQUE constraint |

---

## 6. Políticas de Retención y Archivado

> Las tablas de `recomendacion_generada` e `interaccion_usuario` crecen ilimitadamente sin una estrategia de retención. Esta sección define las políticas para mantener el volumen manejable.

### 6.1 `recomendacion_generada` — TTL por fecha de generación

**Problema:** cada ciclo del job offline genera N registros por usuario (uno por cada establecimiento recomendado, por cada categoría). Sin política de retención, esta tabla puede alcanzar millones de filas rápidamente.

**Política:**
- **TTL activo:** las recomendaciones con `fecha_generacion` anterior a **7 días** se consideran obsoletas.
- **Archivado:** al inicio de cada ciclo del job offline, antes de insertar las nuevas listas, se eliminan (o mueven a `recomendacion_generada_historico`) las filas con `fecha_generacion < NOW() - INTERVAL 7 DAY`.
- **Excepción:** las filas con `fue_clickeada = TRUE` se retienen por **30 días adicionales** como señal de feedback para el reentrenamiento del K-Means.
- **Implementación:** FastAPI no ejecuta esta limpieza. Es responsabilidad exclusiva del job offline antes de cada ciclo de generación.

```sql
-- Limpieza ejecutada por el job offline antes de cada ciclo:
DELETE FROM recomendacion_generada
WHERE fecha_generacion < NOW() - INTERVAL 7 DAY
  AND fue_clickeada = FALSE;

-- Retener clicadas 30 días más:
DELETE FROM recomendacion_generada
WHERE fecha_generacion < NOW() - INTERVAL 37 DAY
  AND fue_clickeada = TRUE;
```

### 6.2 `interaccion_usuario` — Archivado de interacciones antiguas

**Problema:** cada vista de detalle, favorito, ruta calculada, etc., genera un registro. Es la tabla de mayor volumen del sistema.

**Política:**
- **Ventana activa:** el motor colaborativo solo necesita interacciones de los últimos **90 días** para calcular similitudes relevantes.
- **Archivado periódico:** mensualmente, las interacciones con `fecha < NOW() - INTERVAL 90 DAY` se mueven a `interaccion_usuario_historico` (misma estructura, sin índices secundarios).
- Las métricas ya computadas en `metrica_establecimiento` (`popularidad_7d`, `popularidad_30d`) no se ven afectadas por el archivado porque se calculan antes de mover los datos.
- **Implementación:** script de archivado ejecutado mensualmente, independiente del job offline de recomendaciones.

### 6.3 `ubicacion_usuario` — Política de retención existente

Ya documentada en §4.1: máximo 3 registros por usuario, eliminación en la misma transacción de FastAPI. No requiere job adicional.

---

## 7. Invariantes de Integridad — Responsabilidades de la Capa API

> [!IMPORTANT]
> La BD no tiene triggers ni constraints a nivel de base de datos para estas invariantes. El equipo debe garantizar que **todas las escrituras pasen por FastAPI** y que los endpoints implementen correctamente estas reglas. Una escritura directa a la BD que omita estas reglas desincronizará los campos desnormalizados.

| Invariante | Tabla afectada | Regla que debe implementar FastAPI |
|---|---|---|
| **`es_ultimo` único por usuario** | `dispositivo_usuario` | Antes de INSERT de nuevo dispositivo: `UPDATE SET es_ultimo = FALSE WHERE id_usuario = X AND es_ultimo = TRUE`. Nunca debe haber dos filas con `es_ultimo = TRUE` para el mismo usuario |
| **Máximo 3 ubicaciones por usuario** | `ubicacion_usuario` | En la misma transacción del INSERT de nueva ubicación, DELETE los registros del mismo usuario que excedan el límite (ordenados por `fecha_registro ASC`) |
| **`total_resenas` y `calificacion_promedio` sincronizados** | `establecimiento` | Al aprobar una reseña: recalcular ambos campos con `COUNT` y `AVG` sobre `resena WHERE estado='aprobado' AND id_establecimiento=X` y actualizar en la misma transacción |
| **`puntos_experiencia` sincronizado** | `usuario_visitante` | Al insertar en `log_puntos`: sumar los puntos al campo `puntos_experiencia` del usuario en la misma transacción |
| **`es_informal` consistente con `tipo_establecimiento`** | `establecimiento` | Al registrar un establecimiento: `es_informal = TRUE` si y solo si `tipo_establecimiento = 'puesto_informal'` |
| **No escrituras directas a `metrica_establecimiento`** | `metrica_establecimiento` | Los endpoints HTTP de FastAPI nunca deben hacer UPDATE a esta tabla. Solo el job offline puede escribir en ella. FastAPI solo hace SELECT |
| **No escrituras directas a `recomendacion_generada`** | `recomendacion_generada` | FastAPI solo puede actualizar `fue_clickeada` y `fecha_click`. Todo lo demás lo escribe el job offline |
| **`radio_usado_km` siempre poblado por el job offline** | `recomendacion_generada` | El job offline debe asignar `radio_usado_km` en **todas** las categorías de recomendación, no solo en `cercania`. El radio actúa como pre-filtro geográfico universal de candidatos. Valor mínimo: `radio_busqueda_km` del usuario; si hubo fallback, el valor real expandido. El job nunca debe insertar una fila con `radio_usado_km = NULL` |

**Script de reconciliación de emergencia:** si se detecta una desincronización (p.ej. por bug o mantenimiento directo en BD), ejecutar el siguiente procedimiento para recalcular todos los campos desnormalizados desde sus fuentes de verdad:

```sql
-- Reconciliar total_resenas y calificacion_promedio
UPDATE establecimiento e
SET
  total_resenas = (
    SELECT COUNT(*) FROM resena
    WHERE id_establecimiento = e.id_establecimiento AND estado = 'aprobado'
  ),
  calificacion_promedio = COALESCE((
    SELECT AVG(calificacion) FROM resena
    WHERE id_establecimiento = e.id_establecimiento AND estado = 'aprobado'
  ), 0.00);

-- Reconciliar puntos_experiencia
UPDATE usuario_visitante uv
SET puntos_experiencia = COALESCE((
  SELECT SUM(puntos) FROM log_puntos
  WHERE id_usuario = uv.id_usuario
), 0);

-- Reconciliar es_informal
UPDATE establecimiento
SET es_informal = (tipo_establecimiento = 'puesto_informal');

-- Reconciliar total_usuarios por cluster
UPDATE cluster_usuario cu
SET total_usuarios = (
  SELECT COUNT(*) FROM usuario_visitante
  WHERE id_cluster = cu.id_cluster
);

-- Reconciliar total_establecimientos por cluster
UPDATE cluster_establecimiento ce
SET total_establecimientos = (
  SELECT COUNT(*) FROM establecimiento
  WHERE id_cluster = ce.id_cluster AND es_activo = TRUE
);
```

---

## 8. Resumen de Relaciones del Motor

| Relación | Uso en el motor |
|---|---|
| `usuario_visitante.vector_preferencias` ↔ `establecimiento.vector_caracteristicas` | Similitud coseno para score de contenido (categoría `preferencia_contenido`) |
| `usuario_visitante.id_cluster` ↔ `cluster_usuario.centroide` | Asignación de cold start y acotamiento del colaborativo |
| `ubicacion_usuario.(latitud,longitud)` ↔ `establecimiento.(latitud,longitud)` | Fórmula Haversine para `distancia_km` y boost de proximidad (categorías `cercania`, `tendencia_informal`) |
| `interaccion_usuario.peso_interaccion` | Matriz de interacciones ponderada para filtrado colaborativo item-to-item (categoría `colaborativo_cluster`) |
| `recomendacion_generada.categoria_recomendacion` | Discriminador para que el frontend agrupe la lista en secciones semánticas ("Para ti", "Cerca", "Descubrimientos") |
| `recomendacion_generada.(razon_principal, detalle_razon)` | Texto de caja blanca renderizado en el frontend |
| `recomendacion_generada.fue_clickeada` | CTR del motor — feedback implícito para reentrenamiento del K-Means en el siguiente ciclo offline |
| `metrica_establecimiento.score_boost_combinado` | Componente de boosting en la fórmula `score_final` — pre-computado offline |
| `metrica_establecimiento.(popularidad_7d, popularidad_30d)` | Señales de tendencia para categorías `popularidad_zona` y `tendencia_informal` |
| `resena.(polaridad, subjetividad)` ↔ `metrica_establecimiento.polaridad_promedio` | Señal NLP agregada para enriquecer el `score_contenido` |
| `sesion_usuario` ↔ `interaccion_usuario.id_sesion` | Agrupa interacciones por visita; permite calcular el propósito de la sesión |
| `dispositivo_usuario.tipo_dispositivo` | Ajusta la longitud de la lista de recomendaciones y el radio de búsqueda Haversine según el contexto de uso |
| `usuario_visitante.radio_busqueda_km` ↔ `recomendacion_generada.(radio_usado_km, fallback_nivel)` | Define el radio inicial del usuario; `fallback_nivel` indica si el motor expandió el radio (0 = normal, 1 = doble, 2 = municipio) |
| `recomendacion_generada.(es_descubrimiento, diversity_score)` | Garantiza al menos 1–2 ítems de categoría `descubrimiento` en cada lista; evita la burbuja de filtro |

---

## 9. Flujo de Primera Migración Real

El proyecto tiene actualmente una migración placeholder (`e1785d8860ce`) y modelos provisionales (`Vendor`, `User`, `UserRating`). El procedimiento para la primera migración real es:

```bash
# 1. Reemplazar models.py con los modelos definitivos de este documento

# 2. Asegurarse de que defaultdb esté vacía
alembic downgrade base

# 3. Eliminar el archivo de migración placeholder de backend/migrations/versions/

# 4. Generar la migración inicial real
alembic revision --autogenerate -m "Estructura inicial EkiSystem"

# 5. Revisar CUIDADOSAMENTE el archivo generado antes de aplicarlo.
#    Puntos críticos a verificar:
#    - Que 'local_comercial' no tenga conflictos de keyword con MySQL
#    - Que los campos JSON sean compatibles con la versión de MySQL en Aiven
#    - Que todas las FK apunten a las tablas correctas
#    - Que la tabla 'estado_geo' se genere con ese nombre (no 'estado')
#    - Que los índices secundarios del §5 estén incluidos
#      (Alembic --autogenerate NO genera índices secundarios; deben agregarse manualmente
#       al archivo de migración con op.create_index())
```

> **Cómo agregar índices secundarios en Alembic:** los índices del §5 no son generados por `--autogenerate` porque no están declarados en los modelos SQLAlchemy como `Index(...)`. Hay dos opciones:
>
> **Opción A — Declarar en models.py (recomendada):** agregar `__table_args__` con los índices en cada modelo. Alembic los detectará en la siguiente migración autogenerada.
>
> ```python
> class InteraccionUsuario(Base):
>     __tablename__ = "interaccion_usuario"
>     __table_args__ = (
>         Index("idx_interaccion_usuario_fecha", "id_usuario", "fecha"),
>         Index("idx_interaccion_estab_fecha", "id_establecimiento", "fecha"),
>     )
> ```
>
> **Opción B — Agregar manualmente al archivo de migración:** editar el archivo `.py` generado por Alembic y añadir en `upgrade()`:
>
> ```python
> def upgrade():
>     # ... tablas autogeneradas ...
>     op.create_index("idx_interaccion_usuario_fecha",
>                     "interaccion_usuario", ["id_usuario", "fecha"])
>     op.create_index("idx_interaccion_estab_fecha",
>                     "interaccion_usuario", ["id_establecimiento", "fecha"])
>     # ... resto de índices del §5 ...
>
> def downgrade():
>     op.drop_index("idx_interaccion_usuario_fecha", "interaccion_usuario")
>     op.drop_index("idx_interaccion_estab_fecha", "interaccion_usuario")
>     # ... drop_index por cada create_index ...
>     # ... tablas autogeneradas ...
> ```
>
> Recuerda siempre implementar `downgrade()` por cada `op.create_index()` en `upgrade()`.

> **Sobre los CHECK constraints en Alembic/MySQL:** el constraint `CHECK(1 ≤ calificacion ≤ 5)` de `resena.calificacion` se declara en SQLAlchemy como:
>
> ```python
> calificacion = Column(TINYINT, CheckConstraint("calificacion >= 1 AND calificacion <= 5"), nullable=False)
> ```
>
> **Nota importante:** MySQL 5.7 y MariaDB < 10.2 **parsean** los CHECK constraints pero **los ignoran silenciosamente**. Solo MySQL 8.0+ y MariaDB 10.2+ los hacen cumplir. Verificar la versión exacta del servicio Aiven antes de depender de este constraint para integridad de datos. Si la versión no los soporta, la validación debe estar **obligatoriamente en la capa FastAPI** (validador Pydantic en el schema de entrada). El constraint en el modelo es documentación viva aunque no lo haga cumplir la BD.

```bash
# 6. Aplicar en desarrollo (defaultdb)
python scripts/db/migrate.py

# 7. Verificar en HeidiSQL:
#    - Que todas las tablas existan con la estructura correcta
#    - Que los índices secundarios del §5 estén presentes
#    - Que la tabla se llame 'estado_geo' (no 'estado')
#    - Que 'recomendacion_generada' tenga el campo 'categoria_recomendacion'

# 8. Subir el archivo de migración en el PR
#    Al merge a main, el pipeline lo aplica automáticamente en ekidb (producción)
```

> **Advertencia sobre el tipo JSON en Aiven:** MySQL 5.7+ soporta el tipo JSON nativamente. Verificar la versión exacta del servicio Aiven antes de generar la migración para confirmar compatibilidad con `vector_preferencias`, `vector_caracteristicas` y los campos `centroide` de los clusters.
