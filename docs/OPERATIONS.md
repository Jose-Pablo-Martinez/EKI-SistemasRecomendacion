# 🛠️ Manual de Operaciones y Automatización - EKI

Este documento detalla el funcionamiento interno de la infraestructura y cómo ejecutar cada comando de forma correcta. Es la referencia para resolver problemas y escalar el sistema.

---

## 1. Inicialización del Entorno (`setup_env.py`)
**Comando:** `python scripts/setup/setup_env.py`

### ¿Qué sucede al ejecutarlo?
1.  **Seguridad SSL**: El script descarga el certificado `ca.pem` de Aiven. Sin este archivo, cualquier intento de conexión a la base de datos fallará por razones de seguridad.
2.  **Configuración de Variables**: Crea el archivo `.env`. Si no existe, inicia un modo interactivo donde te pide las credenciales.
3.  **Aislamiento**: Configura la conexión por defecto hacia la base de datos de desarrollo (`defaultdb`), asegurando que no toques datos de producción por accidente.

---

## 2. Gestión de Base de Datos con Alembic

Alembic es nuestro "Git para la base de datos". Nos permite que todos los desarrolladores tengan exactamente las mismas tablas.

### A. Diagnóstico de Conexión
**Comando:** `python scripts/db/check_connection.py`
Úsalo siempre que tengas dudas sobre si tu `.env` está bien configurado. Verifica:
- Si el host es alcanzable.
- Si el usuario/password es correcto.
- Si el SSL funciona.

### B. Aplicar Cambios Pendientes
**Comando:** `python scripts/db/migrate.py`
Este script ejecuta internamente `alembic upgrade head`. 
- **¿Cuándo usarlo?**: Siempre que bajes cambios de GitHub (`git pull`) por si algún compañero añadió tablas nuevas.

### C. Registrar un Cambio en el Esquema
**Comando:** `alembic revision --autogenerate -m "descripción"`
- **¿Cuándo usarlo?**: Solo cuando modifiques el archivo `backend/models.py`.
- **Importante**: Este comando crea un archivo de "versión" en `backend/migrations/versions/`. Debes revisar ese archivo para confirmar que Alembic detectó correctamente tu cambio (ej. añadir una columna).

---

## 3. Flujo de Despliegue y Promoción (Automatización)

Hemos implementado un flujo de **CI/CD (Integración y Despliegue Continuo)** que funciona así:

1.  **El Desarrollador**: Sube su código y sus archivos de migración a la rama `main`.
2.  **GitHub Actions**: Se activa automáticamente al detectar cambios en `models.py` o en la carpeta de versiones de Alembic.
    - Levanta un servidor temporal.
    - Se conecta a la base de datos de **Producción** (usando secretos internos de GitHub).
    - Ejecuta las migraciones pendientes.
3.  **Render**: Una vez que las migraciones terminan con éxito, Render toma el nuevo código del Backend y reinicia el servicio.

### Seguridad del Flujo
- **Bloqueo de Errores**: Si la migración falla (por ejemplo, intentas borrar una tabla que tiene datos críticos), el pipeline se detiene y **Render no actualiza el servidor**, protegiendo la web de quedar fuera de línea.

---

## 4. Gestión de Secretos en Producción
Para que la automatización funcione, el administrador debe configurar en GitHub (Settings > Secrets > Actions):
- `DB_HOST`: Host de Aiven.
- `DB_USER`: Usuario administrador.
- `DB_PASSWORD`: Contraseña.
- `DB_NAME_PROD`: Nombre de la base de datos de producción (ej. `ekidb`).
- `DB_PORT`: Generalmente `10471` para Aiven.
