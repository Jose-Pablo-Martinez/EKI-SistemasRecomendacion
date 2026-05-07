"""
Configuración del motor de base de datos y sesiones SQLAlchemy.

Exporta:
    - engine: Motor de conexión a MySQL (Aiven)
    - Base: Clase base declarativa para los modelos
    - get_db: Generador de sesión para inyección de dependencias en FastAPI
"""

import os
import logging

# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine, text
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import sessionmaker, DeclarativeBase
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ─── Construcción del Connection String ───────────────────────────────────────
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_SSL_CA = os.getenv("DB_SSL_CA")

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# ─── Argumentos de Conexión (SSL para Aiven) ──────────────────────────────────
connect_args: dict = {}
if DB_SSL_CA and os.path.exists(DB_SSL_CA):
    connect_args["ssl"] = {"ca": DB_SSL_CA}
    logger.info("Conexión SSL habilitada con certificado: %s", DB_SSL_CA)
else:
    logger.warning(
        "Certificado SSL no encontrado en '%s'. "
        "Conectando sin SSL (solo para desarrollo local).",
        DB_SSL_CA,
    )

# ─── Engine ───────────────────────────────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,      # Verifica la conexión antes de usarla (evita conexiones caídas)
    pool_recycle=1800,       # Recicla conexiones cada 30 min (compatible con Aiven timeouts)
    echo=False,              # Cambiar a True para ver queries en consola durante debugging
)

# ─── Sesión ───────────────────────────────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ─── Base Declarativa ─────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Clase base para todos los modelos SQLAlchemy del proyecto."""
    pass


# ─── Dependencia FastAPI ──────────────────────────────────────────────────────
def get_db():
    """
    Generador de sesión de base de datos para inyección de dependencias.
    Garantiza el cierre de la sesión al finalizar cada request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
