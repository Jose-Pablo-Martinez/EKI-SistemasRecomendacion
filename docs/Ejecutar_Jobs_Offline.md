# Guía de Ejecución: Jobs Offline del Motor de IA

Esta guía documenta el proceso manual para ejecutar los "Jobs Offline" que alimentan el motor de recomendaciones de EkiSystem. En un entorno de producción, estos comandos estarán automatizados mediante *cron jobs* o herramientas de orquestación, pero para pruebas o entornos de desarrollo deben correrse manualmente.

## ¿Qué son los Jobs Offline?

Los algoritmos matemáticos pesados de Machine Learning (como K-Means para agrupar tribus gastronómicas o Alternating Least Squares para filtrado colaborativo) residen en `backend/engine`. Sin embargo, los encargados de orquestar estas matemáticas, aplicarlas a todos los usuarios y persistir los resultados en la base de datos están ubicados en `backend/jobs`.

El archivo principal que coordina estas tareas asíncronamente (o síncronamente desde CLI) es `backend/jobs/runner.py`.

## Requisitos Previos

Antes de ejecutar los comandos:
1. Asegúrate de tener activa tu base de datos y configurado correctamente tu archivo `.env` (sea `defaultdb` para pruebas o `ekidb` para producción).
2. Activa el entorno virtual de Python en la raíz del proyecto:
   ```powershell
   venv\Scripts\activate
   ```

## Orden de Ejecución Recomendado

Para que las recomendaciones tengan la data más fresca, los jobs dependen unos de otros. Se recomienda ejecutarlos en el siguiente orden:

### 1. Métricas de Popularidad
Actualiza la popularidad de 7 días y la calificación promedio de cada establecimiento con base en las interacciones recientes.
```powershell
python -m backend.jobs.runner --job metricas
```

### 2. Pipeline de NLP (Opcional, si hay reseñas nuevas)
Analiza el sentimiento de los textos de reseñas recientes que no han sido procesadas para asignar puntajes de polaridad y subjetividad.
```powershell
python -m backend.jobs.runner --job nlp
```

### 3. Clustering (Agrupación K-Means)
Aplica K-Means a los usuarios (según su vector de preferencias) y a los establecimientos (según su vector de características) para agruparlos en "Tribus".
```powershell
python -m backend.jobs.runner --job clustering
```

### 4. Generación de Recomendaciones (Core)
El job principal. Toma el clustering, las métricas y los perfiles de contenido para pre-calcular las recomendaciones (cajas) de cada usuario y almacenarlas en caché (`RecomendacionGenerada`), listas para ser servidas instantáneamente en el Feed.
```powershell
python -m backend.jobs.runner --job recomendaciones
```

---

## Solución de Problemas en Entornos de Desarrollo

### Error: "Insuficientes datos para clustering (0)"
Si ejecutas el job de clustering y la consola reporta que no hay suficientes usuarios o establecimientos (a pesar de que tu base de datos tiene registros), es porque los registros **no tienen vectores matemáticos asignados**. 

El algoritmo ignora a los usuarios cuyo `vector_preferencias` o establecimientos cuyo `vector_caracteristicas` sean `NULL`. En datos de prueba falsos (dummy data), es común que estos vectores falten.

**Solución temporal para desarrollo:**
Existe un script "semilla" (ahora integrado en el flujo principal de `scripts.db.seed.seed`, pero que se puede correr individualmente) que inyecta vectores aleatorios en toda tu base de datos para permitir que el motor funcione:

```powershell
python -m scripts.db.seed.vectores
```

Tras recibir el mensaje de "¡Éxito!", podrás ejecutar los jobs de `clustering` y `recomendaciones` sin problemas.
