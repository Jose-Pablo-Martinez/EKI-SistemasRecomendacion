import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Añadir el directorio raíz al path para importar modelos si fuera necesario
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

def test_connection():
    """Prueba la conexión a la base de datos usando las variables del .env"""
    print("🔍 Probando conexión a la base de datos...")
    
    # Cargar .env desde la raíz
    dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
    load_dotenv(dotenv_path)

    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASSWORD")
    db_ssl_ca = os.getenv("DB_SSL_CA")

    if not all([db_host, db_user, db_pass]):
        print("❌ Error: Faltan variables de entorno en el archivo .env")
        return

    # Construir URL de SQLAlchemy para PyMySQL
    # Formato: mysql+pymysql://user:password@host:port/dbname
    connection_url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    # Configuración de SSL si existe el certificado
    connect_args = {}
    if db_ssl_ca and os.path.exists(db_ssl_ca):
        connect_args["ssl"] = {"ca": db_ssl_ca}
        print(f"🔒 SSL habilitado usando: {db_ssl_ca}")

    try:
        engine = create_engine(connection_url, connect_args=connect_args)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 'Conexión Exitosa!'"))
            print(f"✅ {result.scalar()}")
            print(f"📊 Conectado a: {db_host}/{db_name}")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    test_connection()
