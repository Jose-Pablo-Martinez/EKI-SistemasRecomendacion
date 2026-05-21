import os
import sys
import argparse
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from sqlalchemy import text

# Añadir el root del proyecto al sys.path para importar modules absolute
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import SessionLocal, DB_NAME
from scripts.db.seed_data.catalogo import seed_catalogo_completo
from scripts.db.seed_data.clusters import seed_clusters
from scripts.db.seed_data.usuarios import seed_usuarios_completo
from scripts.db.seed_data.establecimientos import seed_establecimientos_completo
from scripts.db.seed_data.contenido import seed_contenido_completo
from scripts.db.seed_data.interacciones import seed_interacciones_completo
from scripts.db.seed_data.gamificacion import seed_gamificacion_completo
from scripts.db.seed_data.recomendaciones import seed_recomendaciones_completo

def run_catalogo(db: Session):
    print("=== Iniciando Seed de Catálogo ===")
    try:
        seed_catalogo_completo(db)
        print("=== Seed de Catálogo completado con éxito ===")
    except Exception as e:
        print(f"Error en el seed de catálogo: {e}")
        db.rollback()

def run_desarrollo(db: Session):
    if DB_NAME == "ekidb":
        print("ERROR: No se puede ejecutar el modo desarrollo en la base de datos de producción (ekidb).")
        sys.exit(1)
        
    print("=== Iniciando Seed de Desarrollo Completo ===")
    try:
        seed_catalogo_completo(db)
        seed_clusters(db)
        seed_usuarios_completo(db)
        seed_establecimientos_completo(db)
        seed_contenido_completo(db)
        seed_interacciones_completo(db)
        seed_gamificacion_completo(db)
        seed_recomendaciones_completo(db)
        print("=== Seed de Desarrollo completado con éxito ===")
    except Exception as e:
        print(f"Error en el seed de desarrollo: {e}")
        db.rollback()

def run_limpiar(db: Session):
    if DB_NAME == "ekidb":
        print("ERROR: No se puede ejecutar el modo limpiar en la base de datos de producción (ekidb).")
        sys.exit(1)
        
    print("=== Iniciando limpieza de datos de prueba ===")
    try:
        db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        tablas_a_limpiar = [
            "recomendacion_generada", "recomendacion_generada_historico",
            "historial_visita", "favorito_guardado", "resena", "interaccion_usuario",
            "interaccion_usuario_historico", "reporte", "preferencia_usuario",
            "log_puntos", "contribucion_informacion", "propietario_establecimiento",
            "establecimiento_etiqueta", "establecimiento_categoria", "horario",
            "imagen", "platillo", "metrica_establecimiento", "restaurante",
            "local_comercial", "puesto_informal", "establecimiento", "ubicacion_usuario",
            "sesion_usuario", "dispositivo_usuario", "administrador", "usuario_propietario",
            "usuario_visitante", "usuario", "cluster_usuario", "cluster_establecimiento"
        ]
        
        for tabla in tablas_a_limpiar:
            db.execute(text(f"TRUNCATE TABLE {tabla};"))
            print(f"Tabla {tabla} truncada.")
            
        db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        db.commit()
        print("=== Limpieza completada con éxito ===")
    except Exception as e:
        print(f"Error durante la limpieza: {e}")
        db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        db.rollback()

def main():
    parser = argparse.ArgumentParser(description="Script de Seed para EkiSystem DB.")
    parser.add_argument(
        "--modo", 
        choices=["catalogo", "desarrollo", "limpiar"], 
        required=True, 
        help="El modo de ejecución del script."
    )
    
    args = parser.parse_args()
    
    db = SessionLocal()
    try:
        if args.modo == "catalogo":
            run_catalogo(db)
        elif args.modo == "desarrollo":
            run_desarrollo(db)
        elif args.modo == "limpiar":
            run_limpiar(db)
    finally:
        db.close()

if __name__ == "__main__":
    main()
