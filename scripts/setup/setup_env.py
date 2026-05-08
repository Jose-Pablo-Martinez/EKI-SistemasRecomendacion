import os
import sys

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

def setup_environment():
    check_venv()
    print("\n" + "="*50)
    print("🛠️   CONFIGURACIÓN DE ENTORNO LOCAL - EKI")
    print("="*50)

    # 1. Crear carpeta secrets (ignorada por git)
    if not os.path.exists("secrets"):
        os.makedirs("secrets")
        print("✅ Carpeta '/secrets' creada.")
    
    # 2. Verificar certificado SSL de Aiven (ca.pem)
    ca_path = os.path.join("secrets", "ca.pem")
    if not os.path.exists(ca_path):
        print("\n⚠️  Certificado 'ca.pem' NO encontrado en /secrets.")
        print("   Este archivo es obligatorio para conectar a la base de datos Aiven (SSL).")
        print("   👉 Cómo obtenerlo:")
        print("      1. Solicita el archivo al líder del equipo.")
        print("      2. El líder lo descarga desde: Aiven Console → Tu Servicio → Overview → 'Download CA Certificate'")
        print("      3. Guarda el archivo como: secrets/ca.pem")
        print("   El script continuará, pero la conexión a la BD fallará hasta que tengas el certificado.")
    else:
        print("✅ Certificado SSL (ca.pem) detectado correctamente.")

    # 3. Configuración interactiva del .env
    if not os.path.exists(".env"):
        print("\n📝 Vamos a configurar tu archivo .env local.")
        print("   (Presiona Enter para usar los valores por defecto)\n")
        
        db_host = input("🔹 Host de Aiven (ver Aiven Console → Overview → Host): ").strip()
        db_user = input("🔹 Usuario (ej. avnadmin): ").strip() or "avnadmin"
        db_pass = input("🔹 Password: ").strip()
        db_name = input("🔹 Nombre de DB de desarrollo (defaultdb): ").strip() or "defaultdb"
        db_port = input("🔹 Puerto (ver Aiven Console → Overview → Port): ").strip()

        try:
            if os.path.exists(".env.example"):
                with open(".env.example", "r") as f:
                    lines = f.readlines()
                
                new_lines = []
                for line in lines:
                    if line.startswith("DB_HOST="):
                        new_lines.append(f"DB_HOST={db_host}\n")
                    elif line.startswith("DB_USER="):
                        new_lines.append(f"DB_USER={db_user}\n")
                    elif line.startswith("DB_PASSWORD="):
                        new_lines.append(f"DB_PASSWORD={db_pass}\n")
                    elif line.startswith("DB_NAME="):
                        new_lines.append(f"DB_NAME={db_name}\n")
                    elif line.startswith("DB_PORT="):
                        new_lines.append(f"DB_PORT={db_port}\n")
                    elif line.startswith("DB_SSL_CA="):
                        # Ruta local estándar
                        new_lines.append(f"DB_SSL_CA=secrets/ca.pem\n")
                    elif line.startswith("CORS_ORIGINS="):
                        dev_urls = "http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000"
                        prod_url = "https://jose-pablo-martinez.github.io/EKI-SistemasRecomendacion"
                        new_lines.append(f"CORS_ORIGINS={dev_urls},{prod_url}\n")
                    else:
                        new_lines.append(line)
                
                with open(".env", "w") as f:
                    f.writelines(new_lines)
                
                print("\n✅ Archivo '.env' generado con éxito.")
            else:
                print("❌ Error: No existe '.env.example'.")
        except Exception as e:
            print(f"❌ Error al procesar el .env: {e}")
    else:
        print("\nℹ️  El archivo '.env' ya existe. Bórralo si quieres reconfigurarlo.")

    print("\n" + "="*50)
    print("🚀 CONFIGURACIÓN FINALIZADA")
    print("="*50 + "\n")

if __name__ == "__main__":
    setup_environment()
