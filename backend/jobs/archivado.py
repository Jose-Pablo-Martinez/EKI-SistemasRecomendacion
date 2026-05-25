"""
Job Offline: Archivado de Datos (Data Lifecycle Management)

Responsabilidad:
Mantener el rendimiento de la base de datos principal (OLTP) moviendo registros 
antiguos e inactivos (como las interacciones > 90 días) hacia tablas históricas.

Cumple con buenas prácticas al realizar el borrado y movido en lotes (batches),
evitando bloqueos prolongados en las tablas activas.
"""

import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.models.interacciones import InteraccionUsuario, InteraccionUsuarioHistorico

logger = logging.getLogger(__name__)

#Constantes de archivado
DIAS_RETENCION_INTERACCIONES = 90
TAMANO_REGISTRO = 500  # Número de registros a procesar por iteración para evitar Table Locks


def archivar_lote_interacciones(db: Session, limite_fecha: datetime) -> int:
    """
    Archiva un lote específico de interacciones que superen la fecha límite.
    Copia los datos hacia la tabla histórica y los elimina de la tabla principal
    en una única transacción atómica por lote.
    
    Args:
        db (Session): Sesión de base de datos activa.
        limite_fecha (datetime): Fecha límite de antigüedad.
        
    Returns:
        int: Número de registros que fueron exitosamente procesados en este lote.
    """
    # 1. Obtener lote de registros antiguos
    interacciones_antiguas = db.query(InteraccionUsuario).filter(
        InteraccionUsuario.fecha < limite_fecha
    ).limit(TAMANO_REGISTRO).all()
    
    if not interacciones_antiguas:
        return 0
        
    ids_a_borrar = []
    historicos_a_insertar = []
    
    # 2. Mapear de entidad activa a entidad histórica
    for interaccion in interacciones_antiguas:
        historico = InteraccionUsuarioHistorico(
            id_interaccion=interaccion.id_interaccion,
            id_usuario=interaccion.id_usuario,
            id_establecimiento=interaccion.id_establecimiento,
            tipo_interaccion=interaccion.tipo_interaccion,
            peso_interaccion=interaccion.peso_interaccion,
            id_sesion=interaccion.id_sesion,
            fecha=interaccion.fecha
        )
        historicos_a_insertar.append(historico)
        ids_a_borrar.append(interaccion.id_interaccion)
        
    try:
        # 3. Guardar masivamente en la tabla histórica
        db.bulk_save_objects(historicos_a_insertar)
        
        # 4. Eliminar masivamente de la tabla activa
        # synchronize_session=False es la forma más rápida y evita cargar objetos a memoria
        db.query(InteraccionUsuario).filter(
            InteraccionUsuario.id_interaccion.in_(ids_a_borrar)
        ).delete(synchronize_session=False)
        
        # Hacemos commit del lote para liberar memoria y locks
        db.commit()
        return len(ids_a_borrar)
        
    except SQLAlchemyError as error_bd:
        db.rollback()
        logger.error("Error transaccional al archivar lote de %d interacciones: %s", len(ids_a_borrar), error_bd)
        raise error_bd


def procesar_archivado(db: Session) -> None:
    """
    Orquesta el ciclo de archivado iterando hasta vaciar la cola de registros antiguos.
    """
    limite_fecha = datetime.now(timezone.utc) - timedelta(days=DIAS_RETENCION_INTERACCIONES)
    logger.info("Iniciando archivado masivo de interacciones anteriores a: %s", limite_fecha)
    
    total_archivados = 0
    
    while True:
        procesados = archivar_lote_interacciones(db, limite_fecha)
        if procesados == 0:
            break
            
        total_archivados += procesados
        logger.debug("Archivados %d registros en este lote (Total acumulado: %d)", procesados, total_archivados)
        
    logger.info("Archivado completado exitosamente. %d interacciones movidas al almacenamiento histórico.", total_archivados)


def ejecutar_archivado(db: Session) -> None:
    """
    Punto de entrada llamado por el orquestador (runner.py).
    Como el procesamiento realiza commits granulares por lote para no bloquear la BD,
    aquí únicamente capturamos errores fatales y mantenemos la firma estándar del runner.
    """
    try:
        procesar_archivado(db)
    except Exception as e:
        logger.error("Fallo crítico durante el job de archivado: %s", e)
        raise e
