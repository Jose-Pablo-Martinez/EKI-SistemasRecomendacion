# 🛠️ Manual de Operaciones y Automatización — EKI

Este documento es la referencia técnica interna del proyecto. Detalla el funcionamiento de la infraestructura, los procedimientos operativos y cómo resolver situaciones complejas.

> **Prerrequisito:** Haber completado la configuración inicial de [GUIA_LOCAL.md](../GUIA_LOCAL.md).

---

## 1. Entornos de Base de Datos

El proyecto usa **un único servicio Aiven MySQL** con dos bases de datos separadas:

| Base de datos | Entorno | Acceso | Propósito |
|---|---|---|---|
| `defaultdb` | **Desarrollo** | Todos los devs desde local + pipeline de migraciones dev | Probar cambios del esquema, desarrollo diario |
| `ekidb` | **Producción** | Solo GitHub Actions (secret `DB_NAME_PROD`) | Datos reales, acceso del usuario final |

> [!CAUTION]
> **Regla de oro:** Tu `.env` local siempre debe tener `DB_NAME=defaultdb`. Si accidentalmente apuntas a `ekidb` desde local, cualquier migración o seed que ejecutes afectará producción directamente.

---

## 2. Scripts de Utilidad

Todos los scripts deben ejecutarse desde la **raíz del proyecto** con el **venv activo**.

### `scripts/setup/setup_env.py` — Configurar el entorno local
```powershell
python scripts/setup/setup_env.py
```
**¿Qué hace?**
1. Crea la carpeta `secrets/` si no existe.
2. Verifica que `secrets/ca.pem` esté presente. Si no está, te indica cómo obtenerlo.
3. Genera el archivo `.env` de forma interactiva a partir de `.env.example`.

**Nota sobre el `ca.pem`:** Este certificado **no se descarga automáticamente**. Debe solicitarse al líder del equipo, quien lo obtiene desde:
`Aiven Console → Tu Servicio MySQL → Overview → "Download CA Certificate"`

### `scripts/db/check_connection.py` — Diagnosticar la conexión
```powershell
python scripts/db/check_connection.py
```
Úsalo siempre que dudes sobre si tu `.env` está bien configurado. Verifica:
- Que el host sea alcanzable.
- Que usuario/contraseña sean correctos.
- Que el certificado SSL funcione.

### `scripts/db/migrate.py` — Aplicar migraciones pendientes
```powershell
python scripts/db/migrate.py
```
Ejecuta internamente `alembic upgrade head`. Aplica todos los cambios de esquema pendientes.

**¿Cuándo usarlo?**
- Después de un `git pull` (por si un compañero añadió migraciones nuevas).
- Después de generar tu propia migración para verificar que funciona localmente.

### `scripts/db/init_db.py` — Arranque rápido (solo en fase inicial)
```powershell
python scripts/db/init_db.py
```
Crea las tablas directamente con `create_all()` sin pasar por Alembic. **Útil solo durante la fase inicial** de definición de modelos, cuando las migraciones aún están vacías.

> [!WARNING]
> No usar `init_db.py` como sustituto de las migraciones. Una vez que las tablas estén estables y se hayan generado migraciones reales, usar **siempre** `migrate.py`.

### `scripts/db/seed.py` — Poblar la base de datos con datos de prueba
```powershell
python scripts/db/seed.py   # (disponible cuando las tablas sean definitivas)
```
Ver §4 de este documento para el flujo completo.

---

## 3. Gestión de Migraciones con Alembic

Alembic es el "Git para la base de datos". Registra cada cambio de esquema como un archivo versionado en `backend/migrations/versions/`.

> [!IMPORTANT]
> **Siempre ejecutar los comandos de Alembic desde la raíz del proyecto**, no desde `backend/`.
> Correcto: `alembic upgrade head` (desde la raíz)
> Incorrecto: `cd backend && alembic upgrade head`

### 3.1 Comandos de diagnóstico

```powershell
# Ver en qué versión está la BD actualmente
alembic current

# Ver el historial completo de migraciones
alembic history --verbose

# Verificar si los modelos tienen cambios sin migración generada
alembic check
```

### 3.2 Estado actual del proyecto (fase inicial)

> [!NOTE]
> La migración inicial (`e1785d8860ce`) existe como marcador de posición pero **las tablas definitivas aún están en definición**. Mientras el esquema esté en revisión:
> - Usa `scripts/db/init_db.py` para crear tablas rápidamente durante el desarrollo.
> - Una vez que los modelos en `backend/models.py` sean estables y aprobados por el equipo, se generará la **primera migración real** (ver §3.3).

### 3.3 Casos de migración más comunes

#### Caso A — Primera migración real (cuando los modelos sean definitivos)
```powershell
# 1. Verificar que la BD de desarrollo (defaultdb) esté vacía o en estado base
alembic current

# 2. Generar la migración desde los modelos actuales
alembic revision --autogenerate -m "Estructura inicial de tablas"

# 3. Revisar el archivo generado en backend/migrations/versions/
#    Confirmar que las instrucciones op.create_table() sean correctas

# 4. Aplicar en desarrollo
python scripts/db/migrate.py

# 5. Subir el archivo al repositorio y hacer PR
# Al merge a main, el pipeline lo aplica automáticamente en ekidb (producción)
```

#### Caso B — Agregar una columna
```powershell
# 1. Modificar el modelo en backend/models.py
# 2. Generar la migración
alembic revision --autogenerate -m "Agregar columna X a tabla vendors"
# 3. Revisar el archivo generado (debe contener op.add_column)
# 4. Aplicar en local
python scripts/db/migrate.py
# 5. Subir con el PR
```

#### Caso C — Eliminar una columna o tabla
> [!CAUTION]
> Eliminar columnas o tablas **destruye datos permanentemente** en producción. Coordinar con el equipo antes de hacer merge a `main`. Considerar hacer una migración de respaldo primero.

```powershell
alembic revision --autogenerate -m "Eliminar columna X de vendors"
# Revisar CUIDADOSAMENTE el archivo generado antes de aplicar
# Alembic puede no detectar automáticamente todas las eliminaciones; revisar op.drop_column
python scripts/db/migrate.py
```

#### Caso D — Renombrar una tabla o columna
> [!WARNING]
> Alembic **no detecta renombrados automáticamente**. Los interpreta como `drop + create`. Debes editar el archivo de migración manualmente para usar `op.rename_table()` o `op.alter_column(new_column_name=...)`.

#### Caso E — Revertir la última migración
```powershell
# Revertir un paso atrás
alembic downgrade -1

# Revertir hasta una revisión específica
alembic downgrade <revision_id>

# Revertir todo (estado base, sin tablas)
alembic downgrade base
```

---

## 4. Flujo de Seed (Población Inicial de Datos)

El seed es el proceso de insertar datos iniciales de prueba en la base de datos. Se ejecuta **manualmente** y **solo después** de que las migraciones sean estables.

### ¿Cuándo hacer el seed?

| Momento | Acción |
|---|---|
| Fase inicial (ahora) | No hay seed todavía. Las tablas están en definición. |
| Cuando los modelos sean definitivos | Generar migración real → aplicar en dev → **correr seed en `defaultdb`** |
| Primera puesta en producción | El administrador corre el seed en `ekidb` manualmente (no automatizado) |
| Cambio de estructura (nueva migración) | Evaluar si el seed sigue siendo compatible. Si no, actualizarlo. |

### Flujo de seed en `defaultdb` (desarrollo)
```powershell
# 1. Verificar que las migraciones estén aplicadas
python scripts/db/migrate.py

# 2. Correr el seed
python scripts/db/seed.py

# 3. Verificar en HeidiSQL (o check_connection) que los datos estén
```

### Subir datos iniciales a Aiven (primera vez en producción — `ekidb`)
El seed de producción **no es automático**. Lo ejecuta el administrador del proyecto:
```powershell
# 1. Cambiar temporalmente en .env: DB_NAME=ekidb
# 2. Verificar conexión
python scripts/db/check_connection.py
# 3. Correr el seed
python scripts/db/seed.py
# 4. Restaurar en .env: DB_NAME=defaultdb
```

> [!CAUTION]
> Ejecutar el seed en `ekidb` con datos incorrectos o duplicados puede requerir limpieza manual. Verificar siempre primero en `defaultdb`.

### Cuando cambia la estructura de tablas
Si se agrega o elimina una columna en una migración nueva:
1. Revisar si `seed.py` inserta datos en las columnas afectadas.
2. Actualizar `seed.py` según corresponda antes de correrlo.
3. Si una columna se elimina, asegurarse de que `seed.py` ya no la referencie.

---

## 5. Flujo de Despliegue y CI/CD

```
git push → main
    │
    ├──→ [Trigger: cualquier archivo]
    │       Job: Deploy Frontend
    │       Publica frontend/ en GitHub Pages automáticamente
    │       URL: https://jose-pablo-martinez.github.io/EKI-SistemasRecomendacion/
    │
    ├──→ [Trigger: models.py o backend/migrations/**]
    │       Job: Database Migrations
    │       1. Descarga ca.pem desde Aiven API (con verificación de integridad)
    │       2. Ejecuta alembic check (valida sincronía modelos ↔ migraciones)
    │       3. Ejecuta alembic upgrade head en ekidb (producción)
    │
    └──→ [Trigger: Render webhook automático]
            Render redespliega el backend con el nuevo código
```

### Seguridad del flujo de migraciones

> [!IMPORTANT]
> **El GitHub Environment `ekiEnvironment` (que contiene los secretos de la BD de producción) se activa ÚNICAMENTE cuando el push a `main` incluye cambios en `backend/models.py` o en `backend/migrations/`.**
> Un push que solo modifique el frontend, el backend Python, o documentación **nunca accede a `ekiEnvironment` ni toca la base de datos de producción**.

- Si la migración falla, el pipeline se detiene y **Render no actualiza el servidor**.
- `alembic check` previene despliegues donde los modelos divergen de las migraciones generadas.
- Los secretos de BD están aislados en `ekiEnvironment` y no están disponibles para el job de deploy frontend.

### Secretos requeridos en GitHub (`Settings → Secrets → Actions → ekiEnvironment`)

| Secret | Descripción |
|---|---|
| `DB_HOST` | Host del servicio MySQL en Aiven |
| `DB_USER` | Usuario administrador (avnadmin) |
| `DB_PASSWORD` | Contraseña del servicio |
| `DB_NAME_PROD` | Nombre de la BD de producción: `ekidb` |
| `DB_PORT` | Puerto del servicio Aiven |

---

## 6. Limitaciones Conocidas

| Limitación | Impacto | Solución |
|---|---|---|
| Render free tier: "spin-down" tras 15 min de inactividad | Cold start de ~30-50 s en el primer request | Aceptable para contexto académico |
| Aiven free tier: 5 GB de storage | Límite de datos totales | Monitorear desde el dashboard de Aiven |
| `ca.pem` no se descarga automáticamente | Requiere coordinación con el líder del equipo | Proceso documentado en §2 y GUIA_LOCAL.md |
