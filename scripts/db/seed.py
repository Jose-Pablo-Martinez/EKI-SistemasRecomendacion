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

def run_demo(db: Session):
    print("=== ALERTA: Iniciando Seed de DEMO ===")
    print(f"Base de datos objetivo: {DB_NAME}")
    print("ADVERTENCIA: Este modo inyecta datos sintéticos. Usar solo para la presentación.")
    try:
        seed_catalogo_completo(db)
        seed_clusters(db)
        seed_usuarios_completo(db)
        seed_establecimientos_completo(db)
        seed_contenido_completo(db)
        seed_interacciones_completo(db)
        seed_gamificacion_completo(db)
        seed_recomendaciones_completo(db)
        print("=== Seed de DEMO completado con éxito ===")
    except Exception as e:
        print(f"Error en el seed de demo: {e}")
        db.rollback()

def run_limpiar(db: Session, force: bool = False):
    if DB_NAME == "ekidb" and not force:
        print("ERROR: No se puede ejecutar el modo limpiar en la base de datos de producción (ekidb).")
        print("Si estás seguro de que quieres borrar los datos de evaluación, usa la bandera --force.")
        sys.exit(1)
        
    print("=== Iniciando limpieza de datos de prueba ===")
    try:
        db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        # NOTA: Las siguientes tablas se excluyen INTENCIONALMENTE:
        #   - Catalogó base (pais, estado_geo, municipio, colonia, categoria, etiqueta,
        #     rango_informador): datos permanentes de estructura del dominio.
        #   - cluster_usuario / cluster_establecimiento: centroides K-Means. Son la
        #     configuración del modelo ML, no "datos de prueba". Borrarlos dejaría
        #     a ekidb en estado inválido (usuarios_visitantes sin cluster válido).
        #
        # ⚠️  TRUNCATE es DDL en MySQL: se auto-commitea. Si ocurre un error a mitad
        # del proceso, las tablas ya truncadas NO se pueden revertir con rollback().
        # En ese caso, verifica el estado en HeidiSQL antes de volver a ejecutar el seed.
        tablas_a_limpiar = [
            "recomendacion_generada", "recomendacion_generada_historico",
            "historial_visita", "favorito_guardado", "resena", "interaccion_usuario",
            "interaccion_usuario_historico", "reporte", "preferencia_usuario",
            "log_puntos", "contribucion_informacion", "propietario_establecimiento",
            "establecimiento_etiqueta", "establecimiento_categoria", "horario",
            "imagen", "platillo", "metrica_establecimiento", "restaurante",
            "local_comercial", "puesto_informal", "establecimiento", "ubicacion_usuario",
            "sesion_usuario", "dispositivo_usuario", "administrador", "usuario_propietario",
            "usuario_visitante", "usuario",
        ]
        
        for tabla in tablas_a_limpiar:
            db.execute(text(f"TRUNCATE TABLE {tabla};"))
            print(f"Tabla {tabla} truncada.")
            
        db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        db.commit()
        print("=== Limpieza completada con éxito ===")
        print("(Catálogo base y clusters ML conservados intactos.)")
    except Exception as e:
        print(f"Error durante la limpieza: {e}")
        print("ADVERTENCIA: TRUNCATE es DDL y no puede revertirse. Verifica el estado de la BD antes de continuar.")
        db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        db.rollback()

def main():
    parser = argparse.ArgumentParser(description="Script de Seed para EkiSystem DB.")
    parser.add_argument(
        "--modo", 
        choices=["catalogo", "desarrollo", "limpiar", "demo"], 
        required=True, 
        help="El modo de ejecución del script."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Fuerza la ejecución de comandos peligrosos (como limpiar en ekidb)."
    )
    
    args = parser.parse_args()
    
    db = SessionLocal()
    try:
        if args.modo == "catalogo":
            run_catalogo(db)
        elif args.modo == "desarrollo":
            run_desarrollo(db)
        elif args.modo == "demo":
            run_demo(db)
        elif args.modo == "limpiar":
            run_limpiar(db, force=args.force)
    finally:
        db.close()

if __name__ == "__main__":
    main()
