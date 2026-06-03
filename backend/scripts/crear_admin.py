import argparse
import sys
import os
from datetime import date

# Agregar el directorio raíz al path para poder importar backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import SessionLocal
from backend.services.usuario_service import crear_usuario
from backend.schemas.usuarios import UsuarioCreate

def main():
    parser = argparse.ArgumentParser(description="Crear un usuario administrador en EkiSystem.")
    parser.add_argument("--email", required=True, help="Correo electrónico del administrador")
    parser.add_argument("--password", required=True, help="Contraseña del administrador")
    parser.add_argument("--nombre", default="Admin", help="Nombre del administrador")
    parser.add_argument("--apellido", default="EkiSystem", help="Apellido del administrador")
    
    args = parser.parse_args()

    db = SessionLocal()
    try:
        user_data = UsuarioCreate(
            email=args.email,
            password=args.password,
            nombre=args.nombre,
            apellido=args.apellido,
            tipo_usuario="admin",
            genero="prefiero_no_decir",
            fecha_nacimiento=date(1990, 1, 1)
        )
        
        # Revisar si ya existe
        from backend.models.usuarios import Usuario
        existente = db.query(Usuario).filter(Usuario.email == args.email).first()
        if existente:
            print(f"Error: El usuario con correo {args.email} ya existe.")
            return

        print(f"Creando administrador {args.email}...")
        admin = crear_usuario(db, user_data)
        print(f"¡Administrador creado con éxito! ID: {admin.id_usuario}")

    except Exception as e:
        print(f"Ocurrió un error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
