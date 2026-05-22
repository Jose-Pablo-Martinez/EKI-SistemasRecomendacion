import subprocess
import sys
import os

def check_venv():
    """Verifica si el script se está ejecutando dentro de un entorno virtual."""
    # Omitir verificación en entornos de CI/CD (Render, GitHub Actions)
    if os.environ.get("CI") == "true" or os.environ.get("RENDER") == "true" or os.environ.get("GITHUB_ACTIONS") == "true":
        return

    if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
        print("\n" + "!"*60)
        print("ERROR: NO ESTÁS EN UN ENTORNO VIRTUAL")
        print("!"*60)
        print("Por favor, activa el entorno virtual antes de migrar.")
        print("\n>> Actívalo con: .\\venv\\Scripts\\activate")
        print("!"*60 + "\n")
        sys.exit(1)

def run_migrations():
    check_venv()
    """Ejecuta las migraciones de Alembic (upgrade head)."""
    print("[INFO] Iniciando migración de base de datos...")
    
    # Asegurarnos de que estamos en la raíz del proyecto para que alembic.ini sea visible
    # El script debe ejecutarse como: python scripts/db/migrate.py
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    os.chdir(project_root)

    try:
        # Comando para aplicar todas las migraciones hasta la más reciente
        # Usamos sys.executable para usar el mismo python que está corriendo este script
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("[OK] Migraciones aplicadas con éxito.")
            if result.stdout:
                print(result.stdout)
        else:
            print("[ERROR] Error al aplicar migraciones:")
            print(result.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"[ERROR] Ocurrió un error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()
