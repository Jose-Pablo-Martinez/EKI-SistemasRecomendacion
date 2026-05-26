# 📖 Guía de Configuración Local — EKI

Esta guía es el **punto de partida obligatorio** para cualquier desarrollador nuevo.
Sigue los pasos en orden y tendrás el sistema corriendo en tu computadora.

> [!WARNING]
> **Antes de cualquier operación avanzada de base de datos o despliegue**, lee el manual de operaciones completo: [docs/OPERATIONS.md](docs/OPERATIONS.md).

> [!IMPORTANT]
> **Flujo de Git:** Los desarrolladores **NO** hacen `push` directamente a `main`. Todo cambio entra por una rama `feature/` y pasa por Pull Request a `unstable`, y luego a `main`. Ver sección §5 y CONTRIBUTING.md §7 para el detalle.

---

## 1. Requisitos Previos

Antes de empezar, instala:

| Herramienta | ¿Para qué? | Enlace |
|---|---|---|
| **Python 3.11+** | Ejecutar el backend y los scripts | [python.org](https://www.python.org/) |
| **Git** | Clonar el repo y gestionar ramas | [git-scm.com](https://git-scm.com/) |
| **HeidiSQL** *(opcional, recomendado)* | Interfaz gráfica para explorar la BD Aiven | [heidisql.com](https://www.heidisql.com/) |

> *En Windows: durante la instalación de Python, marca la casilla **"Add Python to PATH"**.*

---

## 2. Instalación Paso a Paso

### A. Clonar el repositorio y crear el entorno virtual
```powershell
git clone <url-del-repo>
cd ekiSystem
python -m venv venv
.\venv\Scripts\activate
```
Sabrás que el venv está activo cuando el prompt de tu terminal muestre `(venv)` al inicio.

### B. Instalar dependencias
```powershell
pip install -r requirements.txt
```
Esto instala FastAPI, SQLAlchemy, Alembic, PyMySQL y todas las librerías del proyecto.

### C. Obtener el certificado SSL (`ca.pem`)

La base de datos Aiven **requiere SSL obligatorio**. Sin el certificado, ninguna conexión funcionará.

1. **Solicita el archivo `ca.pem`** al líder del equipo por el canal del equipo.
2. **El líder lo descarga** desde: `Aiven Console → Tu Servicio MySQL → Overview → "Download CA Certificate"`.
3. **Guarda el archivo** exactamente en: `secrets/ca.pem` (dentro de la carpeta raíz del proyecto).

> *La carpeta `secrets/` está ignorada por Git (`.gitignore`), así que el certificado nunca se sube al repositorio.*

### D. Configurar el archivo `.env`
Ejecuta el asistente de configuración:
```powershell
python scripts/setup/setup_env.py
```
El script verificará el certificado y te pedirá los datos de conexión de forma interactiva:
- **Host, Puerto y Password**: pídelos al líder del equipo. Los encontrará en `Aiven Console → Tu Servicio → Overview`.
- **Nombre de BD**: usa `defaultdb` (base de datos de **desarrollo**).

> [!NOTE]
> **Sobre la variable `JWT_SECRET_KEY`:** 
> Esta variable se usa para firmar las sesiones de los usuarios. **Para tu entorno local de desarrollo, puedes inventar cualquier valor** (ejemplo: `JWT_SECRET_KEY=mi_llave_local_123`). Esto es seguro porque solo se usa en tu propia computadora. La llave real, segura y encriptada, **solo existe configurada en la nube (Render)**. Nunca coloques una llave real de producción en tu `.env` local.

Al finalizar, tendrás un archivo `.env` listo en la raíz del proyecto.

---

## 3. Base de Datos — Sincronización y Gestión

El proyecto usa **dos bases de datos en el mismo servicio Aiven**:

| Base de datos | Entorno | ¿Quién accede? |
|---|---|---|
| `defaultdb` | **Desarrollo** (compartida por todo el equipo) | Todos los devs desde local |
| `ekidb` | **Producción** | Solo el pipeline de CI/CD (GitHub Actions) |

> [!WARNING]
> **Nunca configures tu `.env` con `ekidb`**. Esa base de datos es de producción y solo la toca el pipeline automático.

### Paso 1 — Verificar la conexión
```powershell
python scripts/db/ops/check_connection.py
```
Si ves `✅ Conexión Exitosa!`, tu `.env` y certificado están bien configurados.

### Paso 2 — Aplicar migraciones (crear tablas)
```powershell
python scripts/db/ops/migrate.py
```
Esto ejecuta `alembic upgrade head` y crea las tablas en `defaultdb`. Si ves `✅ Migraciones aplicadas con éxito`, la BD está lista.

> [!NOTE]
> **Estado actual del proyecto:** El esquema de BD es definitivo (migración `e1b0a75cd65e` — 38 tablas). Si tu compañero generó una nueva migración, el `migrate.py` la aplicará automáticamente. Para generar una migración propia, consulta `CONTRIBUTING.md §2.1` y `docs/OPERATIONS.md §3`.

### Paso 3 — Población Inicial de Datos (Seed)

Después de aplicar las migraciones, las tablas existen pero **no tienen datos**.
Para poder desarrollar y probar el sistema (entrenar K-Means, etc.), inyectaremos un volumen alto de datos de prueba sintéticos:

```powershell
python scripts/db/seed/seed_orquestador.py --modo desarrollo
```

> **Tip de Mantenimiento:** Si durante el desarrollo necesitas reiniciar tu entorno y borrar los datos de prueba para empezar de cero, usa primero `--modo limpiar` y luego `--modo desarrollo`:
> ```powershell
> python scripts/db/seed/seed_orquestador.py --modo limpiar
> python scripts/db/seed/seed_orquestador.py --modo desarrollo
> ```

Ver [docs/OPERATIONS.md](docs/OPERATIONS.md) §4 para el detalle de todos los comandos y modos del seed.

### Paso 4 — Ejecutar los Jobs Offline del Motor

Después del seed, los datos existen pero el motor de IA aún no ha procesado las recomendaciones. Ejecuta los jobs en este orden exacto para que el sistema quede completamente funcional:

```powershell
# 1. Analizar reseñas con NLP
python -m backend.jobs.runner --job nlp

# 2. Calcular popularidad y métricas de tendencia
python -m backend.jobs.runner --job metricas

# 3. Agrupar usuarios en tribus (K-Means)
python -m backend.jobs.runner --job clustering

# 4. Generar el catálogo de recomendaciones para todos los usuarios
python -m backend.jobs.runner --job recomendaciones
```

> [!NOTE]
> El job de `clustering` puede tardar entre 20-60 segundos dependiendo del volumen de datos. Es normal.
> Para más detalle sobre qué hace cada job y cómo depurar errores, consulta [docs/Ejecutar_Jobs_Offline.md](docs/Ejecutar_Jobs_Offline.md).

---

## 4. Configurar HeidiSQL para Ver la Base de Datos

HeidiSQL permite explorar visualmente las tablas de Aiven sin escribir SQL manualmente.

1. Abre HeidiSQL → `Nueva sesión`.
2. Configura los campos:

| Campo | Valor |
|---|---|
| Tipo de red | **MySQL (TCP/IP)** |
| Hostname / IP | Tu `DB_HOST` del `.env` |
| Usuario | Tu `DB_USER` del `.env` |
| Contraseña | Tu `DB_PASSWORD` del `.env` |
| Puerto | Tu `DB_PORT` del `.env` |

3. Ve a la pestaña **SSL**:
   - Activa "Usar SSL".
   - En **Certificado CA**: navega y selecciona `secrets/ca.pem`.
4. Haz clic en **Abrir** para conectar.
5. En el panel izquierdo verás los schemas: `defaultdb` (desarrollo) y `ekidb` (producción).

> **Trabaja siempre dentro de `defaultdb`** cuando explores datos de desarrollo.

---

## 5. Iniciar el Servidor Backend en Local

Con el venv activo y el `.env` configurado, inicia FastAPI:
```powershell
python -m uvicorn backend.eki_main:app --reload --port 8000
```

Verifica que funcione abriendo en tu navegador:
- **Documentación interactiva (Swagger):** `http://localhost:8000/docs`
- **Health check:** `http://localhost:8000/health` → debe responder `{"status": "healthy"}`

Para el **frontend**, abre `frontend/index.html` con **Live Server** (extensión de VS Code) en el puerto `5500`. El archivo `scripts/app.js` detecta automáticamente que estás en `localhost` y apunta al backend local.

---

## 6. Cómo Subir Cambios y Verlos en Producción

El proyecto tiene CI/CD automatizado. El flujo correcto es:

```
Tu rama feature/ → PR a unstable → (revisión del equipo) → merge a main → Deploy automático
```

> [!IMPORTANT]
> **No hagas `push` directo a `main`**. La rama `main` está protegida. Solo el líder del equipo hace merge a `main` después de revisión.

### 🌐 Cambios en el Frontend (HTML/JS/CSS)
1. Trabaja en tu rama `feature/nombre-tarea`.
2. Crea un PR hacia `unstable`.
3. Tras aprobación y merge a `main`: **GitHub Actions** despliega automáticamente el frontend a GitHub Pages en menos de 1 minuto.
4. URL pública: `https://jose-pablo-martinez.github.io/EKI-SistemasRecomendacion/`

### ⚙️ Cambios en el Backend (Lógica Python)
1. Modifica archivos en `backend/`.
2. Crea PR → merge a `main`.
3. **Render** detecta el push y redespliega el servidor automáticamente.

### 🗄️ Cambios en la Base de Datos (Tablas/Columnas)
Este flujo es más delicado. Ver [docs/OPERATIONS.md](docs/OPERATIONS.md) §3 para el procedimiento completo y todos los casos posibles (agregar columna, eliminar tabla, revertir, etc.).

Resumen del flujo:
1. Modifica `backend/models/` según las convenciones del esquema.
2. Genera la migración: `alembic revision --autogenerate -m "descripcion"`
3. Revisa el archivo generado en `backend/migrations/versions/`.
4. Aplica localmente: `python scripts/db/ops/migrate.py`
5. Sube el nuevo archivo de migración con tu PR.
6. Al hacer merge a `main`: el pipeline activa el GitHub Environment **`ekiEnvironment`** y aplica la migración a producción (`ekidb`) automáticamente.

> **Nota:** `ekiEnvironment` (y los secretos de producción) **solo se activan cuando el push incluye cambios en `models.py` o en `backend/migrations/`**. Un push de frontend o de lógica Python nunca toca la BD de producción.
