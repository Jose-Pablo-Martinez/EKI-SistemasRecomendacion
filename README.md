# Esquina Jach ki' (EKI)
 
**Proyecto Final - Sistemas de Recomendación de Información**  
*Facultad de Matemáticas, UADY*
 
> 🚀 **¿Eres nuevo en el proyecto?** Lee la [Guía de Configuración Local](docs/GUIA_LOCAL.md) para empezar.
 
---
 
## 👥 Integrantes del Equipo
 
| Foto | Información |
| :---: | :--- |
| <img src="externalAssets/AlejandroLopez.jpeg" width="200"> | **Alejandro Lopez Maldonado** <br> [GitHub Profile](https://github.com/alejandrolopezmldndo) |
| <img src="externalAssets/Rodrigo Alonzo.jpeg" width="200"> | **Rodrigo Alonzo Palacios** <br> [GitHub Profile](https://github.com/AlonPal09) |
| <img src="externalAssets/JoseMartinez.jpg" width="200"> | **José Pablo Martínez Martínez** <br> [GitHub Profile](https://github.com/Jose-Pablo-Martinez) |
 
---
 
## 📝 Descripción del Proyecto
 
**Esquina Jach ki'** es un sistema de recomendación basado en servicios web diseñado para descubrir y dar visibilidad a las verdaderas joyas ocultas de la gastronomía en Mérida, Yucatán. A diferencia de las plataformas tradicionales, nuestro sistema prioriza el descubrimiento de puestos pequeños, carritos y vendedores informales mediante reglas de negocio específicas.
 
El motor del sistema utiliza un **modelo híbrido de recomendación** que atiende el problema de inicio en frío y combina:
 
- **Filtrado Basado en Contenido:** Análisis de las características del puesto y preferencias del usuario.
- **Filtrado Colaborativo:** Sugerencias basadas en interacciones de la comunidad.
- **Ranking y Boosting:** Algoritmos de priorización para visibilizar negocios emergentes.
- **Caja Blanca:** Explicabilidad orgánica de las recomendaciones mostradas en la interfaz.
---
 
## 💻 Stack Tecnológico
 
La arquitectura del proyecto está construida bajo el enfoque de **Monorepositorio**, separando la lógica del servicio web de la interfaz de usuario, y utilizando una base de datos relacional para asegurar la escalabilidad del sistema.
 
### Backend (Servicios Web)
 
| Tecnología | Descripción |
| :--- | :--- |
| ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) **Python 3.11+** | Lenguaje de programación principal para la lógica algorítmica. |
| ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white) **FastAPI** | Framework asíncrono para la construcción de la API REST. |
| ![Uvicorn](https://img.shields.io/badge/Uvicorn-499848?style=flat&logo=gunicorn&logoColor=white) **Uvicorn** | Servidor ASGI para la ejecución del backend en desarrollo local. |
| ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat&logo=sqlite&logoColor=white) **SQLAlchemy 2.x** | ORM para el mapeo y consulta orientada a objetos con sintaxis declarativa. |
| ![Alembic](https://img.shields.io/badge/Alembic-6BA81E?style=flat&logo=python&logoColor=white) **Alembic** | Control de versiones del esquema de base de datos (migraciones incrementales). |
| ![PyMySQL](https://img.shields.io/badge/PyMySQL-4479A1?style=flat&logo=mysql&logoColor=white) **PyMySQL** | Driver de conexión entre el backend y la base de datos MySQL con soporte SSL. |
| ![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=flat&logo=python&logoColor=white) **Pydantic v2** | Validación y serialización de datos de entrada/salida de la API. |
| ![python-dotenv](https://img.shields.io/badge/python--dotenv-ECD53F?style=flat&logo=python&logoColor=black) **python-dotenv** | Carga de variables de entorno desde archivos `.env`. |
 
### Base de Datos
 
| Tecnología | Descripción |
| :--- | :--- |
| ![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=flat&logo=mysql&logoColor=white) **MySQL (Aiven)** | Base de datos relacional administrada en la nube con SSL/TLS obligatorio. Compatible con MariaDB y PyMySQL. Dos instancias separadas: `defaultdb` (desarrollo) y `ekidb` (producción). |
 
### Frontend (Interfaz de Usuario)
 
| Tecnología | Descripción |
| :--- | :--- |
| ![JavaScript](https://img.shields.io/badge/JavaScript_ES6+-F7DF1E?style=flat&logo=javascript&logoColor=black) **Vanilla JS (ES6+)** | Lógica de UI y detección dinámica del entorno (local vs. producción) sin frameworks externos. |
| ![Fetch API](https://img.shields.io/badge/Fetch_API-F7DF1E?style=flat&logo=javascript&logoColor=black) **Fetch API** | Consumo nativo de los servicios web (HTTP Requests). |
| ![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=flat&logo=tailwind-css&logoColor=white) **Tailwind CSS (CDN)** | Framework de utilidades cargado desde CDN para estilos responsivos. |
 
---
 
## 📂 Estructura del Proyecto
 
La organización de carpetas está estandarizada para facilitar el desarrollo concurrente y servir como contexto para asistentes de IA de codificación.
 
```text
ekiSystem/                    ← Raíz del Repositorio
│
├── docs/                    ← Documentación del equipo
│   ├── GUIA_LOCAL.md        ← Guía de onboarding para nuevos devs
│   ├── CONTRIBUTING.md      ← Convenciones de código y Git
│   └── OPERATIONS.md        ← Manual operativo (BD, CI/CD, seeds)
│
├── scripts/                 ← Automatización y Operaciones
│   ├── setup/               ← Inicialización del entorno
│   └── db/
│       ├── ops/             ← Scripts operativos del día a día
│       └── seed/            ← Población de datos de prueba
│
├── backend/                 ← Entorno Python / API
│   ├── migrations/          ← Versiones de la BD (Alembic)
│   ├── models/              ← Modelos SQLAlchemy por dominio
│   ├── schemas/             ← Schemas Pydantic por dominio
│   ├── engine/              ← Motor de recomendación (ML)
│   └── eki_main.py          ← Punto de entrada de FastAPI
│
└── frontend/                ← Entorno Web / UI Vanilla JS (Patrón MVC)
    ├── index.html           ← Estructura web SPA Shell
    ├── views/               ← Archivos HTML estáticos de las vistas
    └── scripts/             ← Lógica de negocio
        ├── controllers/     ← Controladores por página (login, feed, etc)
        ├── utils/           ← Utilidades (validadores, manejo de errores)
        └── app.js           ← Router SPA asíncrono y renderizador de vistas
```

---

## ⚙️ Automatización y Despliegue

Este proyecto utiliza un flujo de automatización profesional con **tres pipelines independientes** activados al hacer merge a `main`:

1. **Deploy Frontend** — Se ejecuta en **cualquier push a `main`**. Publica la carpeta `frontend/` en GitHub Pages automáticamente. La URL del backend se detecta de forma dinámica desde el código JavaScript (`window.location.hostname`).

2. **Database Migrations** — Se ejecuta **solo cuando cambian `backend/models.py` o archivos en `backend/migrations/`**. Utiliza el GitHub Environment **`ekiEnvironment`** (donde están los secretos de producción de Aiven) para:
   - Descargar y verificar el certificado SSL de Aiven.
   - Ejecutar `alembic check` para validar sincronía entre modelos y migraciones.
   - Aplicar `alembic upgrade head` sobre la base de datos de producción (`ekidb`).

3. **Backend Redeploy (Render)** — Render escucha el webhook de GitHub y redespliega el servidor automáticamente en **cualquier push a `main`**.

> **Entornos separados:** `defaultdb` para desarrollo local (todos los devs) y `ekidb` para producción (solo CI/CD).
 
---
 
## 🧠 ¿Cómo Funcionan las Recomendaciones?

EkiSystem utiliza un **motor híbrido de recomendación** con arquitectura **Offline-First**: los algoritmos pesados corren en segundo plano mediante _Jobs_, guardan resultados en base de datos, y el Feed del usuario solo hace un `SELECT` rápido a esa tabla. Esto garantiza respuestas en menos de 200ms.

### Modelo Híbrido

El sistema combina tres señales para calcular la recomendación final de cada usuario:

```
Score Final = (Similitud Coseno × W₁)         ← ¿Hace match con tus gustos?
            + (Colaborativo Item-to-Item × W₂) ← ¿Lo visita gente como tú?
            + (Boost Geográfico × W₃)          ← ¿Está cerca? ¿Es informal?
```

### Algoritmos Implementados

| Algoritmo | Tecnología | ¿Para qué se usa? |
| :--- | :--- | :--- |
| **Similitud Coseno** | `scikit-learn` | Comparar el perfil del usuario con las características del establecimiento |
| **K-Means Clustering** | `scikit-learn` | Agrupar usuarios en "Tribus" con gustos similares (base del colaborativo) |
| **Filtrado Colaborativo Item-to-Item** | SQLAlchemy | Recomendar lo que visitó la tribu del usuario |
| **Fórmula de Haversine** | Implementación propia | Calcular distancia GPS real entre usuario y establecimiento |
| **Análisis de Sentimiento NLP** | `TextBlob` | Extraer polaridad y subjetividad de las reseñas |
| **Distancia de Levenshtein** | Implementación propia | Corrección ortográfica en el buscador |
| **Cold Start (Inicio en Frío)** | Popularidad global | Recomendaciones seguras para usuarios nuevos sin historial |

### Inicio en Frío

Cuando un usuario es nuevo o aún no tiene historial suficiente, el sistema detecta automáticamente este estado y le sirve los establecimientos más populares globalmente como punto de partida seguro. Una vez que acumula interacciones, el siguiente ciclo de jobs lo migra al modelo híbrido completo.

### Caja Blanca (Explicabilidad)

Cada recomendación incluye metadatos que explican la razón al usuario: el carrusel al que pertenece, el algoritmo que la generó, y los scores individuales de cada señal. Esto contrasta con modelos de "caja negra" donde la razón es opaca.

> Para el detalle técnico completo de cada algoritmo, ver [docs/Motor_Recomendaciones.md](docs/Motor_Recomendaciones.md).

---
 
## 🌿 Flujo de Trabajo (Git Flow)
 
Para mantener la integridad del código, el equipo de desarrollo trabaja bajo el siguiente esquema de ramas:
 
| Rama | Descripción |
| :--- | :--- |
| `main` | Rama de producción. Contiene únicamente código estable y funcional listo para ser evaluado. |
| `unstable` | Rama de integración para pruebas de conexión entre Frontend y Backend. |
| `feature/<nombre>-<tarea>` | Ramas de desarrollo individual para la implementación de características (ej. `feature/alejandro-api-coldstart`). |

---

## 🚀 Despliegue (Deployment)

El sistema está configurado para un despliegue automatizado en tres capas:

1.  **Frontend:** Hospedado en **GitHub Pages**. Se despliega automáticamente al hacer merge a `main`.
2.  **Backend:** Hospedado en **Render**. Escucha cambios en la rama `main` para realizar el redeploy.
3.  **Base de Datos:** Instancia gestionada en **Aiven (MySQL)**.

*Para más detalles sobre las convenciones de despliegue y CORS, consulta el archivo [CONTRIBUTING.md](docs/CONTRIBUTING.md).*
