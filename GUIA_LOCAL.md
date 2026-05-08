# 📖 Guía de Configuración Local — EKI

Esta guía es el **punto de partida obligatorio**. Sigue estos pasos para tener el sistema funcionando en tu computadora.

> [!WARNING]
> **IMPORTANTE:** Antes de realizar cualquier operación avanzada de base de datos o despliegue, es obligatorio leer el manual de operaciones: [docs/OPERATIONS.md](docs/OPERATIONS.md).

---

## 1. Requisitos Previos (Lo que debes instalar)

Antes de empezar, asegúrate de tener instalado en tu sistema:
1.  **Python 3.11 o superior**: [Descargar aquí](https://www.python.org/). 
    *   *Nota: Durante la instalación en Windows, marca la casilla "Add Python to PATH".*
2.  **Git**: Para clonar el repositorio y gestionar ramas.
3.  **MariaDB / MySQL Client**: 
    *   Si vas a trabajar con la base de datos en la nube (Aiven), no necesitas instalar el servidor, pero es útil tener un cliente como **DBeaver** o **HeidiSQL** para visualizar los datos.

---

## 2. Instalación Paso a Paso

### A. Clonar y preparar entorno
Abre una terminal (PowerShell o CMD) en la carpeta donde quieras guardar el proyecto:
```powershell
git clone <url-del-repo>
cd ekiSystem
python -m venv venv
.\venv\Scripts\activate
```

### B. Instalar dependencias (Librerías)
Este comando instalará FastAPI, SQLAlchemy, Alembic y otras herramientas necesarias:
```powershell
pip install -r backend/requirements.txt
```

### C. Configuración automática (.env y SSL)
Ejecuta nuestro asistente inteligente de configuración:
```powershell
python scripts/setup/setup_env.py
```
*   **¿Qué hace?**: Descarga el certificado de seguridad SSL (`ca.pem`) necesario para Aiven y te pide los datos de conexión.
*   **¿Qué datos poner?**: Solicita al líder del equipo el **Hostname** y la **Password** de la base de datos de **desarrollo**.

---

## 3. Sincronización de la Base de Datos

Una vez que tengas tu archivo `.env` listo, debes crear las tablas físicamente:
1.  **Verificar conexión:** 
    ```powershell
    python scripts/db/check_connection.py
    ```
2.  **Aplicar tablas iniciales (Migración):** 
    ```powershell
    python scripts/db/migrate.py
    ```
    *Si ves el mensaje "✅ Migraciones aplicadas con éxito", tu base de datos local/nube ya tiene las tablas listas.*

---

## 4. Cómo subir cambios y verlos en Producción

El proyecto está automatizado. Para que tus cambios se vean en la web real, sigue estas reglas:

### 🌐 Cambios en el Frontend (HTML/JS/CSS)
1.  Realiza tus cambios en la carpeta `frontend/`.
2.  Haz `git commit` y `git push origin main`.
3.  **Resultado**: GitHub Actions actualizará [la web](https://jose-pablo-martinez.github.io/EKI-SistemasRecomendacion/) automáticamente en menos de 1 minuto.

### ⚙️ Cambios en el Backend (Lógica Python)
1.  Modifica tus archivos en `backend/`.
2.  Haz `git push origin main`.
3.  **Resultado**: Render detectará el cambio y reiniciará el servidor con tu nueva lógica.

### 🗄️ Cambios en la Base de Datos (Tablas/Columnas)
1.  Modifica `backend/models.py`.
2.  **Genera la versión**: `alembic revision --autogenerate -m "descripcion del cambio"`
3.  Sube el nuevo archivo creado en `backend/migrations/versions/` a GitHub.
4.  **Resultado**: El pipeline de GitHub aplicará el cambio a la base de datos de producción automáticamente antes de que el servidor inicie.
