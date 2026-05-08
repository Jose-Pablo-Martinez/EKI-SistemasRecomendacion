"""
Script de utilidad para inicializar la base de datos.
Crea todas las tablas definidas en los modelos de SQLAlchemy (create_all).

Nota: Este script es útil como arranque rápido cuando se están definiendo los modelos
iniciales. Una vez que el esquema sea estable, se debe generar una migración Alembic
(`alembic revision --autogenerate`) y usar `scripts/db/migrate.py` como fuente de verdad.

Ejecutar siempre desde la raíz del proyecto con el venv activo:
    python scripts/db/init_db.py
"""
import sys
import os
from pathlib import Path


def check_venv():
    """Verifica si el script se está ejecutando dentro de un entorno virtual."""
    if os.environ.get("CI") == "true" or os.environ.get("RENDER") == "true" or os.environ.get("GITHUB_ACTIONS") == "true":
        return
        
    if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
        print("\n" + "!"*60)
        print("⚠️  ERROR: NO ESTÁS EN UN ENTORNO VIRTUAL")
        print("!"*60)
        print("Para proteger tu sistema, este script solo debe ejecutarse")
        print("dentro del entorno virtual del proyecto.")
        print("\n👉 Actívalo con: .\\venv\\Scripts\\activate")
        print("!"*60 + "\n")
        sys.exit(1)


# ─── Configuración de Paths ───────────────────────────────────────────────────
# Raíz del proyecto (3 niveles arriba: init_db.py → db/ → scripts/ → raíz)
ROOT = Path(__file__).parent.parent.parent

# Añadir la raíz al path para poder importar backend.*
sys.path.insert(0, str(ROOT))

# Cargar .env con ruta explícita para que funcione sin importar el directorio de trabajo
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from backend.database import engine, Base
from backend.models import Vendor, User, UserRating  # noqa: F401 — necesario para que Base.metadata los incluya


def init_database():
    """Crea todas las tablas en la base de datos según los modelos definidos en models.py."""
    check_venv()
    print("🚀 Iniciando creación de tablas en la base de datos...")
    try:
        # Crea las tablas si no existen (no borra las existentes)
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas con éxito.")
        print("\nℹ️  Recuerda: la base de datos está vacía. Para poblarla con datos de")
        print("   prueba, ejecuta: python scripts/db/seed.py (cuando esté disponible)")
    except Exception as e:
        print(f"❌ Error al crear las tablas: {e}")


if __name__ == "__main__":
    init_database()
