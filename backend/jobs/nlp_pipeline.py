"""
Job Offline: Pipeline de Procesamiento de Lenguaje Natural (NLP)

Responsabilidad:
Extraer la polaridad y subjetividad de las reseñas aprobadas que aún no han sido procesadas.
Aprovecha TextBlob para analizar el texto nativamente en español, luego realiza
el análisis matemático y persiste únicamente los scores numéricos en la base de datos.

Cumple con SRP aislando la integración de la librería NLP externa de 
las reglas de agregación y guardado en base de datos.
"""

import logging
from typing import Set, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func
from textblob import TextBlob

from backend.models.interacciones import Resena
from backend.models.establecimientos import MetricaEstablecimiento

logger = logging.getLogger(__name__)


def analizar_sentimiento_texto(comentario_original: str) -> Tuple[float, float]:
    """
    Traduce el texto al inglés para mayor precisión y extrae sus métricas de NLP.
    Maneja internamente las excepciones de la API de traducción como fallback seguro.
    
    Args:
        comentario_original (str): El texto de la reseña en español.
        
    Returns:
        Tuple[float, float]: Una tupla con (polaridad, subjetividad).
                             Polaridad ∈ [-1.0, 1.0]. Subjetividad ∈ [0.0, 1.0].
    """
    if not comentario_original or not comentario_original.strip():
        return 0.0, 0.0
        
    try:
        blob_original = TextBlob(comentario_original)
        return float(blob_original.sentiment.polarity), float(blob_original.sentiment.subjectivity) # type: ignore
        
    except Exception as e:
        logger.warning(
            "Fallo al analizar '%s': %s", 
            comentario_original[:20], 
            e
        )
        return 0.0, 0.0


def recalcular_polaridad_establecimientos(db: Session, ids_establecimientos: Set[int]) -> None:
    """
    Recalcula y actualiza la `polaridad_promedio` en la tabla MetricaEstablecimiento
    para un conjunto específico de establecimientos.
    
    Utiliza agrupaciones a nivel base de datos para no saturar la memoria.
    
    Args:
        db (Session): Sesión activa de BD.
        ids_establecimientos (Set[int]): Conjunto único de IDs a recalcular.
    """
    if not ids_establecimientos:
        return
        
    # Consulta optimizada GROUP BY para obtener los promedios directamente de la base
    promedios_bd = db.query(
        Resena.id_establecimiento,
        func.avg(Resena.polaridad).label("promedio_polaridad")
    ).filter(
        Resena.id_establecimiento.in_(ids_establecimientos),
        Resena.estado == 'aprobado',
        Resena.procesado_nlp == True,
        Resena.polaridad.is_not(None)
    ).group_by(
        Resena.id_establecimiento
    ).all()
    
    # Transformamos el resultado en un diccionario para acceso rápido O(1)
    mapa_promedios = {fila.id_establecimiento: float(fila.promedio_polaridad) for fila in promedios_bd}
    
    # Consultamos y actualizamos solo las métricas afectadas
    metricas = db.query(MetricaEstablecimiento).filter(
        MetricaEstablecimiento.id_establecimiento.in_(ids_establecimientos)
    ).all()
    
    for metrica in metricas:
        # Si un local se quedó sin reseñas aprobadas, su promedio vuelve a 0.0
        nuevo_promedio = mapa_promedios.get(metrica.id_establecimiento, 0.0) # type: ignore
        metrica.polaridad_promedio = nuevo_promedio # type: ignore
        
    logger.info("Recalculada la polaridad promedio para %d establecimientos.", len(ids_establecimientos))


def procesar_nlp_resenas(db: Session) -> None:
    """
    Función orquestadora interna: 
    1. Obtiene reseñas pendientes.
    2. Delega el análisis de sentimientos.
    3. Marca como procesadas.
    4. Delega el recálculo de promedios para los locales afectados.
    """
    resenas_pendientes = db.query(Resena).filter(
        Resena.procesado_nlp == False,
        Resena.estado == 'aprobado'
    ).all()
    
    if not resenas_pendientes:
        logger.info("No hay reseñas nuevas pendientes de análisis NLP.")
        return
        
    establecimientos_afectados: Set[int] = set()
    total_procesadas = 0
    
    for resena in resenas_pendientes:
        if resena.comentario:
            polaridad, subjetividad = analizar_sentimiento_texto(str(resena.comentario))
            resena.polaridad = polaridad # type: ignore
            resena.subjetividad = subjetividad # type: ignore
        else:
            # Si dejaron una calificación (estrellas) pero ningún comentario escrito
            resena.polaridad = 0.0 # type: ignore
            resena.subjetividad = 0.0 # type: ignore
            
        resena.procesado_nlp = True # type: ignore
        establecimientos_afectados.add(int(resena.id_establecimiento)) # type: ignore
        total_procesadas += 1
        
    # Recalcular el promedio SOLO para aquellos locales que tuvieron reseñas nuevas
    recalcular_polaridad_establecimientos(db, establecimientos_afectados)
    
    logger.info("Análisis NLP finalizado: %d reseñas procesadas con éxito.", total_procesadas)


def ejecutar_nlp(db: Session) -> None:
    """
    Punto de entrada transaccional llamado por el orquestador principal (runner.py).
    Asegura que el procesamiento y los nuevos promedios se guarden de forma atómica.
    """
    try:
        procesar_nlp_resenas(db)
        db.commit()
        logger.info("Transacción NLP confirmada (commit) en base de datos.")
    except Exception as e:
        db.rollback()
        logger.error("Error crítico durante el análisis NLP. Transacción revertida (rollback): %s", e)
        raise e
