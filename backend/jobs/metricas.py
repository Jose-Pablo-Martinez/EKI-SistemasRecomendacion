"""
Job Offline: Métricas y Popularidad (Batch)

Calcula de forma masiva (batch) la popularidad de cada establecimiento basándose
en el volumen de interacciones recientes (7 y 30 días). 
Genera el score_boost_combinado persistente en `metrica_establecimiento` para 
que el motor de recomendación online solo requiera hacer sumas simples.

Cumple con SRP: Su única responsabilidad es el cálculo de scores pre-computados.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models.establecimientos import Establecimiento, MetricaEstablecimiento
from backend.models.interacciones import InteraccionUsuario

logger = logging.getLogger(__name__)

#Constantes de ponderación
W_INFORMAL = 0.25
W_ZONA = 0.75

def calcular_popularidad_agregada(db: Session, dias_atras: int) -> Dict[int, int]:
    """
    Calcula el número de interacciones por establecimiento en los últimos N días.
    Utiliza una consulta agrupada (GROUP BY) directamente en la base de datos
    para evitar cargar todas las filas en memoria y maximizar el rendimiento.

    Args:
        db (Session): Sesión de base de datos activa.
        dias_atras (int): Ventana de tiempo en días.

    Returns:
        Dict[int, int]: Diccionario {id_establecimiento: total_interacciones}.
    """
    fecha_limite = datetime.now(timezone.utc) - timedelta(days=dias_atras)
    
    resultados_bd = db.query(
        InteraccionUsuario.id_establecimiento,
        func.count(InteraccionUsuario.id_interaccion).label("total")
    ).filter(
        InteraccionUsuario.fecha >= fecha_limite
    ).group_by(
        InteraccionUsuario.id_establecimiento
    ).all()
    
    return {fila.id_establecimiento: fila.total for fila in resultados_bd}

def procesar_metricas(db: Session) -> None:
    """
    Calcula los scores offline para todos los establecimientos activos.
    Crea o actualiza los registros en MetricaEstablecimiento, normalizando
    la popularidad para obtener valores entre [0, 1].
    """
    # 1. Extraer conteos usando las funciones optimizadas con GROUP BY
    dic_pop_7d = calcular_popularidad_agregada(db, 7)
    dic_pop_30d = calcular_popularidad_agregada(db, 30)
    
    # Obtenemos el valor máximo absoluto para normalizar [0, 1]
    # Si no hay interacciones, evitamos dividir entre 0 usando 1
    max_interacciones_30d = max(dic_pop_30d.values()) if dic_pop_30d else 1
    
    # 2. Consultar establecimientos activos
    establecimientos = db.query(Establecimiento).filter(
        Establecimiento.es_activo == True,
        Establecimiento.estado == 'aprobado'
    ).all()
    
    if not establecimientos:
        logger.warning("No se encontraron establecimientos activos para procesar métricas.")
        return

    ahora = datetime.now(timezone.utc)
    
    for estab in establecimientos:
        # Recuperamos métrica existente, o la creamos si es un lugar nuevo
        metrica = estab.metrica
        if not metrica:
            metrica = MetricaEstablecimiento(id_establecimiento=estab.id_establecimiento)
            db.add(metrica)
            
        conteo_7d = dic_pop_7d.get(int(estab.id_establecimiento), 0) # type: ignore
        conteo_30d = dic_pop_30d.get(int(estab.id_establecimiento), 0) # type: ignore
        
        metrica.popularidad_7d = conteo_7d
        metrica.popularidad_30d = conteo_30d
        
        # 3. Calcular componentes del Boost
        boost_informal_val = 1.0 if estab.es_informal else 0.0
        
        # Usamos la popularidad normalizada a 30 días como proxy de 'popularidad_zona'
        # ya que la cercanía hiper-local depende del usuario (Haversine Online)
        boost_zona_val = conteo_30d / max_interacciones_30d
        
        metrica.boost_informal = boost_informal_val # type: ignore
        metrica.boost_proximidad_zona = boost_zona_val # type: ignore
        
        # 4. Combinar scores para el engine
        score_combinado = (W_INFORMAL * boost_informal_val) + (W_ZONA * boost_zona_val)
        metrica.score_boost_combinado = score_combinado # type: ignore
        
        metrica.ultima_actualizacion = ahora
        
    logger.info("Métricas calculadas y asignadas a %d establecimientos.", len(establecimientos))

def ejecutar_metricas(db: Session) -> None:
    """
    Orquestador de la transacción atómica para el job de métricas.
    Garantiza que la base de datos no quede en estado inconsistente.
    """
    try:
        procesar_metricas(db)
        db.commit()
        logger.info("Transacción de métricas confirmada (commit) con éxito.")
    except Exception as e:
        db.rollback()
        logger.error("Fallo crítico procesando métricas. Transacción revertida (rollback): %s", e)
        raise e
