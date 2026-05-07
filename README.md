# 🌮 Esquina Jach ki' (EKI)
 
**Proyecto Final - Sistemas de Recomendación de Información**  
*Facultad de Matemáticas, UADY*
 
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
eki-app/                     ← Raíz del Repositorio
│
├── backend/                 ← Entorno Python / API
│   ├── eki_main.py          ← Punto de entrada de FastAPI y rutas
│   ├── models.py            ← Esquemas de SQLAlchemy para MariaDB
│   ├── logic/               ← Algoritmos del modelo híbrido y recomendación
│   └── requirements.txt     ← Dependencias del entorno virtual de Python
│
└── frontend/                ← Entorno Web / UI Vanilla JS
    ├── index.html           ← Estructura web y carga de Tailwind por CDN
    ├── js/
    │   └── app.js           ← Lógica de peticiones HTTP con Fetch API
    └── css/
        └── styles.css       ← Ajustes de diseño personalizados
```
 
---
 
## 🌿 Flujo de Trabajo (Git Flow)
 
Para mantener la integridad del código, el equipo de desarrollo trabaja bajo el siguiente esquema de ramas:
 
| Rama | Descripción |
| :--- | :--- |
| `main` | Rama de producción. Contiene únicamente código estable y funcional listo para ser evaluado. |
| `unstable` | Rama de integración para pruebas de conexión entre Frontend y Backend. |
| `feature/<nombre>-<tarea>` | Ramas de desarrollo individual para la implementación de características (ej. `feature/alejandro-api-coldstart`). |
