# Guía de Ejecución: Jobs Offline del Motor de IA

Esta guía documenta el proceso manual para ejecutar los "Jobs Offline" que alimentan el motor de recomendaciones de EkiSystem.

---

## ¿Qué son los Jobs Offline?

Los Jobs Offline son procesos matemáticos pesados que **no pueden correr en tiempo real** durante una petición del usuario porque tomarían demasiado tiempo (segundos o minutos). En su lugar, se ejecutan de forma programada en segundo plano, guardan sus resultados en la base de datos, y cuando el usuario abre la app solo se hace un `SELECT` rápido a esa tabla de resultados.

Este patrón se llama **arquitectura Offline-First** y es el estándar en la industria para sistemas de recomendación a escala (Netflix, Spotify, Amazon lo hacen igual).

> **En un entorno profesional**, estos jobs correrían automáticamente mediante un **cron job** programado (ej. una vez al día a las 2am) o mediante herramientas de orquestación como **Apache Airflow** o **Celery Beat**. En nuestro proyecto académico se ejecutan manualmente cuando se necesita actualizar las recomendaciones.

El archivo que coordina todos los jobs es [`backend/jobs/runner.py`](../backend/jobs/runner.py). Acepta el flag `--job <nombre>` para ejecutar cualquier job síncronamente desde la línea de comandos.

---

## Requisitos Previos

Antes de ejecutar los comandos:

1. Asegúrate de tener configurado tu `.env` apuntando a la base de datos correcta:
   - `defaultdb` → para pruebas en desarrollo local.
   - `ekidb` → para producción (usar con cuidado).
2. Activa el entorno virtual de Python en la raíz del proyecto:
   ```powershell
   venv\Scripts\activate
   ```
3. Verifica que la base de datos tiene datos (seed aplicado). Sin datos de usuarios ni establecimientos, los jobs de clustering y recomendaciones no tendrán nada que procesar.

---

## Orden de Ejecución Obligatorio

Los jobs tienen **dependencias entre sí**. Correrlos en el orden incorrecto produce resultados degradados o errores. El orden correcto es:

### 1. Pipeline de NLP (Análisis de Reseñas)
**¿Qué hace?** Toma todas las reseñas (`Resena`) que tengan `procesado_nlp = False`, traduce el texto al inglés usando la API de traducción de TextBlob, y calcula dos métricas psicológicas del texto:
- **Polaridad** (`-1.0` a `1.0`): qué tan positiva o negativa es la reseña.
- **Subjetividad** (`0.0` a `1.0`): qué tan objetiva o emocional es la opinión.

Luego recalcula el `polaridad_promedio` de la tabla `MetricaEstablecimiento` para todos los lugares afectados.

**¿Por qué primero?** Las métricas de NLP alimentan el score de reputación que usa el job de `metricas` en el siguiente paso.

**Tecnología:** `TextBlob` (Python) + API de traducción automática.

```powershell
python -m backend.jobs.runner --job nlp
```

---

### 2. Métricas de Popularidad y Boosting
**¿Qué hace?** Para cada establecimiento activo, calcula en batch:
- **Popularidad de 7 días**: cuenta las interacciones recientes (vistas, reseñas, guardados) y les aplica un peso según su tipo (`peso_interaccion`).
- **Calificación promedio**: promedio ponderado de todas las estrellas de las reseñas aprobadas.
- **Score de boost**: combina la popularidad de zona, el bonus por ser informal (`es_informal`) y la calificación NLP para generar el `score_boost_combinado` que usará el job de recomendaciones.

**¿Por qué antes del clustering?** Los vectores de características de los establecimientos incluyen sus métricas. Si el clustering corre antes, agrupa con datos desactualizados.

**Tecnología:** SQLAlchemy (consultas batch) + aritmética pura en Python.

```powershell
python -m backend.jobs.runner --job metricas
```

---

### 3. Clustering de Tribus (Machine Learning)
**¿Qué hace?** Agrupa a los usuarios y los establecimientos por similitud usando el algoritmo **K-Means**:
- Extrae todos los `vector_preferencias` de los usuarios.
- Prueba diferentes valores de `K` (número de grupos) y evalúa cuál produce la mejor separación usando el **Silhouette Score** (coeficiente de silueta).
- Asigna el `id_cluster` óptimo a cada usuario en la base de datos.
- Repite el proceso para los establecimientos usando sus `vector_caracteristicas`.

El resultado son "tribus" de usuarios con gustos similares. Esto es la base del **Filtrado Colaborativo**: en lugar de comparar a un usuario con todos los demás, solo se compara con los de su misma tribu.

**¿Por qué antes de recomendaciones?** El job de recomendaciones necesita saber a qué cluster pertenece cada usuario para calcular el score colaborativo.

**Tecnología:** `scikit-learn` (KMeans, silhouette_score).

```powershell
python -m backend.jobs.runner --job clustering
```
> ⏳ Este job puede tardar entre 20-60 segundos. Es normal: está ejecutando múltiples rondas de K-Means.

---

### 4. Generación de Recomendaciones (Job Principal)
**¿Qué hace?** Es el corazón del sistema. Para cada usuario activo en la base de datos:
1. Limpia sus recomendaciones pre-calculadas anteriores.
2. Determina si es usuario **veterano** (con historial) o **cold start** (nuevo/sin historial).
3. Para veteranos: ejecuta los tres algoritmos del modelo híbrido:
   - **Filtrado por Contenido** (`cosine_similarity` entre perfil del usuario y establecimientos).
   - **Filtrado Colaborativo** (item-to-item: qué visitó la gente de su misma tribu).
   - **Ranking y Boosting** (`compute_score_final`: suma ponderada de los scores anteriores + bonus geográfico Haversine).
4. Para usuarios en cold start: usa popularidad global como punto de partida seguro.
5. Guarda todas las recomendaciones categorizadas en la tabla `RecomendacionGenerada`, listas para ser servidas instantáneamente.

**Tecnología:** `scikit-learn` (cosine_similarity), `geopy`/fórmula de Haversine, SQLAlchemy (bulk insert).

```powershell
python -m backend.jobs.runner --job recomendaciones
```

---

### 5. Archivado (Mantenimiento, Opcional)
**¿Qué hace?** Limpia interacciones antiguas (más de 90 días) y sesiones de usuario expiradas para evitar que las tablas crezcan indefinidamente.

```powershell
python -m backend.jobs.runner --job archivado
```

---

## Resumen: Comandos en Orden Completo

```powershell
# Copiar y pegar en orden
python -m backend.jobs.runner --job nlp
python -m backend.jobs.runner --job metricas
python -m backend.jobs.runner --job clustering
python -m backend.jobs.runner --job recomendaciones

# Opcional: limpieza de datos viejos
python -m backend.jobs.runner --job archivado
```

---

## Solución de Problemas

### Error: `"El código del job 'X' aún no está disponible"`
El runner no pudo importar el módulo del job porque falta alguna dependencia en tu entorno virtual.
**Solución:** Activa el venv y reinstala todas las dependencias:
```powershell
venv\Scripts\activate
pip install -r requirements.txt
```

### Error: `"Insuficientes datos para clustering (0)"`
Los registros en tu base de datos **no tienen vectores matemáticos asignados** (`vector_preferencias` o `vector_caracteristicas` son NULL). El algoritmo K-Means ignora registros sin vector.

**Solución:** Ejecuta el sembrador de vectores de forma quirúrgica (sin borrar ningún otro dato):
```powershell
venv\Scripts\python.exe -c "from scripts.db.seed.vectores import seed_vectores; from backend.database import SessionLocal; db=SessionLocal(); seed_vectores(db); db.close()"
```
Tras ver el mensaje `¡Éxito!`, vuelve a ejecutar el job de `clustering`.

### Error: `"Incompatible dimension for X and Y matrices"`
Los vectores de los usuarios tienen una dimensión diferente a la de los establecimientos o los centroides de los clusters.
**Solución:** El mismo que el anterior: corre el sembrador de vectores para alinear todas las dimensiones a 22.

### Error de conexión a la base de datos
Verifica que tu `.env` tiene los valores correctos y que el certificado `secrets/ca.pem` existe. Corre:
```powershell
python scripts/db/ops/check_connection.py
```
