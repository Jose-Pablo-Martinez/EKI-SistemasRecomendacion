import os
import shutil
import sys

# Intentar importar requests para la descarga automática
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# URL pública del certificado CA de Aiven
AIVEN_CA_URL = "https://api.aiven.io/v1/project/public_ca"

def setup_environment():
    print("\n" + "="*50)
    print("🛠️   CONFIGURACIÓN AUTOMÁTICA DE ENTORNO - EKI")
    print("="*50)
    
    # 1. Crear carpeta secrets
    if not os.path.exists("secrets"):
        os.makedirs("secrets")
        print("✅ Carpeta '/secrets' creada.")
    
    # 2. Descargar certificado SSL de Aiven
    ca_path = os.path.join("secrets", "ca.pem")
    if not os.path.exists(ca_path):
        if HAS_REQUESTS:
            print("📥 Descargando certificado SSL de Aiven...")
            try:
                response = requests.get(AIVEN_CA_URL, timeout=10)
                if response.status_code == 200:
                    with open(ca_path, "wb") as f:
                        f.write(response.content)
                    print("✅ Certificado 'ca.pem' guardado en /secrets.")
                else:
                    print(f"⚠️  No se pudo descargar el certificado (Status {response.status_code}).")
            except Exception as e:
                print(f"⚠️  Error de red al descargar el certificado: {e}")
        else:
            print("ℹ️  Librería 'requests' no detectada. No se descargó el certificado automáticamente.")
            print("   👉 Puedes colocarlo manualmente en 'secrets/ca.pem'.")

    # 3. Configuración interactiva del .env
    if not os.path.exists(".env"):
        print("\n📝 No se encontró un archivo .env. Vamos a configurarlo ahora.")
        print("   (Presiona Enter para usar los valores por defecto si aplican)\n")
        
        db_host = input("🔹 Host de Aiven (ej. mysql-eki...): ").strip()
        db_user = input("🔹 Usuario (ej. avnadmin): ").strip() or "avnadmin"
        db_pass = input("🔹 Password: ").strip()
        db_name = input("🔹 Nombre de DB local (ej. defaultdb): ").strip() or "defaultdb"
        db_port = input("🔹 Puerto (ej. 10471): ").strip() or "10471"

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
                        new_lines.append(f"DB_SSL_CA=secrets/ca.pem\n")
                    elif line.startswith("CORS_ORIGINS="):
                        # Configuramos automáticamente los orígenes de desarrollo y producción
                        dev_urls = "http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000"
                        prod_url = "https://jose-pablo-martinez.github.io"
                        new_lines.append(f"CORS_ORIGINS={dev_urls},{prod_url}\n")
                    else:
                        new_lines.append(line)
                
                with open(".env", "w") as f:
                    f.writelines(new_lines)
                
                print("\n✅ Archivo '.env' generado con éxito.")
            else:
                print("❌ Error: No existe '.env.example' para usar como plantilla.")
        except Exception as e:
            print(f"❌ Error al procesar el .env: {e}")
    else:
        print("\nℹ️  El archivo '.env' ya existe. Si deseas reconfigurarlo, bórralo y corre este script de nuevo.")

    print("\n" + "="*50)
    print("🚀 ¡CONFIGURACIÓN COMPLETADA!")
    print("   Ahora puedes ejecutar 'python scripts/db/migrate.py'")
    print("="*50 + "\n")

if __name__ == "__main__":
    setup_environment()
