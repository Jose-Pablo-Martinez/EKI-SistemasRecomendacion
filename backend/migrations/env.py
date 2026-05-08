# ─── IMPORTANTE ───────────────────────────────────────────────────────────────
# Alembic SIEMPRE debe ejecutarse desde la RAÍZ del proyecto.
# Comando correcto: python scripts/db/migrate.py (o alembic upgrade head)
# Ejecutarlo desde backend/ u otra subcarpeta causará errores de importación.
# ──────────────────────────────────────────────────────────────────────────────

import sys
import os
from pathlib import Path
from logging.config import fileConfig
# pyrefly: ignore [missing-import]
from sqlalchemy import engine_from_config
# pyrefly: ignore [missing-import]
from sqlalchemy import pool
# pyrefly: ignore [missing-import]
from alembic import context
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

# ─── Configuración de Paths ───────────────────────────────────────────────────
# ROOT = raíz del proyecto (env.py → migrations/ → backend/ → raíz)
ROOT = Path(__file__).parent.parent.parent

# Insertar la raíz al inicio del sys.path para garantizar que
# 'from backend.database import Base' siempre resuelva correctamente,
# independientemente de alembic.ini prepend_sys_path.
sys.path.insert(0, str(ROOT))

# Cargar .env con ruta explícita desde la raíz
load_dotenv(ROOT / ".env")

from backend.database import Base
from backend.models import Vendor, User, UserRating  # noqa: F401 — necesario para autodetect

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
target_metadata = Base.metadata

def get_url():
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT", "3306")
    db = os.getenv("DB_NAME", "defaultdb")
    ca_path = os.getenv("DB_SSL_CA", "secrets/ca.pem")
    
    # Construir URL compatible con PyMySQL y SSL
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?ssl_ca={ca_path}"

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
