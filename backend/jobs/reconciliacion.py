"""
Script de reconciliación para recalcular los datos desnormalizados del sistema.
Usar solo en caso de emergencia si se detecta desincronización de contadores.
"""

import logging
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from sqlalchemy import text

logger = logging.getLogger(__name__)

def reconciliar_campos_desnormalizados(db: Session):
    """
    Ejecuta las queries SQL de §7 del diseño de BD para recalcular 
    todos los campos desnormalizados desde sus fuentes de verdad.
    """
    logger.info("Iniciando reconciliación de campos desnormalizados...")
    
    try:
        # 1. Reconciliar total_resenas y calificacion_promedio
        logger.info("Reconciliando reseñas y calificaciones...")
        db.execute(text("""
            UPDATE metrica_establecimiento me
            SET total_resenas = COALESCE((
                SELECT COUNT(*) FROM resena_usuario r
                WHERE r.id_establecimiento = me.id_establecimiento
                AND r.estado = 'aprobado'
            ), 0),
            calificacion_promedio = COALESCE((
                SELECT AVG(r.calificacion) FROM resena_usuario r
                WHERE r.id_establecimiento = me.id_establecimiento
                AND r.estado = 'aprobado'
            ), 0.0);
        """))

        # 2. Reconciliar es_informal (basado en subtipo TPT)
        logger.info("Reconciliando bandera es_informal...")
        db.execute(text("""
            UPDATE establecimiento e
            SET es_informal = TRUE
            WHERE e.id_establecimiento IN (
                SELECT id_establecimiento FROM puesto_callejero
            );
        """))
        
        db.execute(text("""
            UPDATE establecimiento e
            SET es_informal = FALSE
            WHERE e.id_establecimiento IN (
                SELECT id_establecimiento FROM local_fijo
            );
        """))

        # 3. Reconciliar puntos de experiencia
        logger.info("Reconciliando puntos de experiencia...")
        db.execute(text("""
            UPDATE usuario_visitante u
            SET puntos_experiencia = COALESCE((
                SELECT SUM(puntos_otorgados) FROM log_puntos l
                WHERE l.id_usuario = u.id_usuario
            ), 0);
        """))

        # 4. Reconciliar contadores de clústeres
        logger.info("Reconciliando contadores de clústeres...")
        db.execute(text("""
            UPDATE cluster_usuario c
            SET total_usuarios = COALESCE((
                SELECT COUNT(*) FROM usuario_visitante u
                WHERE u.id_cluster = c.id_cluster AND u.es_activo = TRUE
            ), 0);
        """))

        db.commit()
        logger.info("Reconciliación completada con éxito.")
        
    except Exception as e:
        db.rollback()
        logger.error("Error durante la reconciliación: %s", e)
        raise e
