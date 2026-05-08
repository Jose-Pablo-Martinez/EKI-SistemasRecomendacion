# Esquina Jach ki' (EKI)
 
**Proyecto Final - Sistemas de Recomendación de Información**  
*Facultad de Matemáticas, UADY*
 
> 🚀 **¿Eres nuevo en el proyecto?** Lee la [Guía de Configuración Local](GUIA_LOCAL.md) para empezar.
 
---
 
## 👥 Integrantes del Equipo
 
| Foto | Información |
| :---: | :--- |
| <img src="assets/foto_integrante1.jpg" width="200"> | **Alejandro Lopez Maldonado** <br> [GitHub Profile](https://github.com/alejandrolopezmldndo) |
| <img src="assets/Rodrigo Alonzo.jpeg" width="200"> | **Rodrigo Alonzo Palacios** <br> [GitHub Profile](https://github.com/AlonPal09) |
| <img src="assets/JoseMartinez.jpg" width="200"> | **José Pablo Martínez Martínez** <br> [GitHub Profile](https://github.com/Jose-Pablo-Martinez) |
 
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
| ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) **Python** | Lenguaje de programación principal para la lógica algorítmica. |
| ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white) **FastAPI** | Framework asíncrono para la construcción de la API REST. |
| ![Uvicorn](https://img.shields.io/badge/Uvicorn-499848?style=flat&logo=gunicorn&logoColor=white) **Uvicorn** | Servidor ASGI para la ejecución del backend. |
| ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat&logo=sqlite&logoColor=white) **SQLAlchemy** | ORM para el mapeo y consulta orientada a objetos. |
| ![PyMySQL](https://img.shields.io/badge/PyMySQL-4479A1?style=flat&logo=mysql&logoColor=white) **PyMySQL** | Driver de conexión entre el backend y la base de datos. |
 
### Base de Datos
 
| Tecnología | Descripción |
| :--- | :--- |
| ![MariaDB](https://img.shields.io/badge/MariaDB-003545?style=flat&logo=mariadb&logoColor=white) **MariaDB** | Sistema de gestión de bases de datos relacional, elegido para garantizar integridad ACID y facilitar la escalabilidad del proyecto a largo plazo. |
 
### Frontend (Interfaz de Usuario)
 
| Tecnología | Descripción |
| :--- | :--- |
| ![Fetch API](https://img.shields.io/badge/Fetch_API-F7DF1E?style=flat&logo=javascript&logoColor=black) **Fetch API** | Consumo nativo de los servicios web (HTTP Requests). |
| ![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=flat&logo=tailwind-css&logoColor=white) **Tailwind CSS** | Framework de utilidades para asegurar los requerimientos de usabilidad y diseño responsivo. |
 
---
 
## 📂 Estructura del Proyecto
 
La organización de carpetas está estandarizada para facilitar el desarrollo concurrente y servir como contexto para asistentes de IA de codificación.
 
```text
ekiSystem/                    ← Raíz del Repositorio
│
├── scripts/                 ← Automatización y Operaciones
│   ├── setup/               ← Inicialización del entorno
│   └── db/                  ← Gestión de Base de Datos y Migraciones
│
├── backend/                 ← Entorno Python / API
│   ├── migrations/          ← Versiones de la BD (Alembic)
│   ├── eki_main.py          ← Punto de entrada de FastAPI
│   └── models.py            ← Esquemas de SQLAlchemy
│
└── frontend/                ← Entorno Web / UI Vanilla JS
    ├── index.html           ← Estructura web
    └── js/app.js            ← Lógica de peticiones
```

---

## ⚙️ Automatización y Despliegue

Este proyecto utiliza un flujo de automatización profesional para mantener la integridad de los datos:

1.  **Gestión de Cambios:** Se utiliza **Alembic** para versionar cualquier cambio en el esquema de la base de datos.
2.  **CI/CD:** Los cambios en la rama `main` disparan un pipeline que aplica automáticamente las migraciones en la base de datos de producción en **Aiven** antes de actualizar el servicio en **Render**.
3.  **Entornos Separados:** Se recomienda usar `defaultdb` para desarrollo local y `ekidb` para producción.
 
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

*Para más detalles sobre las convenciones de despliegue y CORS, consulta el archivo [CONTRIBUTING.md](CONTRIBUTING.md).*
