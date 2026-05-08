import os
import shutil

def setup_environment():
    print("🛠️ Iniciando configuración del entorno local...")
    
    # 1. Crear carpeta secrets si no existe
    if not os.path.exists("secrets"):
        os.makedirs("secrets")
        print("✅ Carpeta '/secrets' creada (está protegida por .gitignore).")
    
    # 2. Crear .env a partir de .env.example
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            shutil.copy(".env.example", ".env")
            print("✅ Archivo '.env' creado a partir de '.env.example'.")
            print("👉 ¡No olvides editar el '.env' con tus credenciales reales!")
        else:
            print("❌ Error: No se encontró el archivo '.env.example'.")
    else:
        print("ℹ️ El archivo '.env' ya existe. No se realizaron cambios para no sobrescribir tus datos.")

if __name__ == "__main__":
    setup_environment()
