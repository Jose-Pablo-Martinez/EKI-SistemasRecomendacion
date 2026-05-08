"""
Script de utilidad para inicializar la base de datos.
Crea todas las tablas definidas en los modelos de SQLAlchemy.
"""
import sys
import os

# Añadir el directorio raíz al path para poder importar los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, Base
from backend.models import Vendor, User, UserRating

def init_database():
    print("🚀 Iniciando creación de tablas en la base de datos...")
    try:
        # Crea las tablas si no existen
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas con éxito.")
        print("   - vendors")
        print("   - users")
        print("   - user_ratings")
    except Exception as e:
        print(f"❌ Error al crear las tablas: {e}")

if __name__ == "__main__":
    init_database()
