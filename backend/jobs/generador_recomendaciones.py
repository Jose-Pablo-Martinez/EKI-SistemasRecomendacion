"""
Job Offline: Generador Masivo de Recomendaciones

Responsabilidad:
Pre-computar y persistir las listas de recomendaciones (cajas) para todos los usuarios
activos. Limpia el caché antiguo y genera recomendaciones por cada categoría (estrategia)
usando los algoritmos de filtrado (contenido, colaborativo, etc.) desarrollados en la Fase 2.

Cumple con SRP al delegar los algoritmos matemáticos a la carpeta `backend.engine` y
enfocarse exclusivamente en la orquestación masiva y persistencia (bulk inserts).
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Any

from sqlalchemy.orm import Session

from backend.models.usuarios import UsuarioVisitante
from backend.models.establecimientos import Establecimiento
from backend.models.interacciones import RecomendacionGenerada

# Importaciones seguras de la Fase 2 (Engine)
# Se usa try-except para evitar bloqueos si alguna función aún no está expuesta en su módulo
try:
    from backend.engine.cold_start import get_cold_start_recommendations
except ImportError:
    get_cold_start_recommendations = None

try:
    from backend.engine.ranking import get_top_establecimientos
except ImportError:
    get_top_establecimientos = None

# Agregaremos imports de content_filter y collab_filter simulando su estructura
try:
    from backend.engine.content_filter import get_content_based_recommendations
except ImportError:
    get_content_based_recommendations = None

try:
    from backend.engine.collab_filter import get_collaborative_recommendations
except ImportError:
    get_collaborative_recommendations = None


logger = logging.getLogger(__name__)

# Constantes de Retención y Generación
DIAS_EXPIRACION_NO_CLICK = 7
DIAS_EXPIRACION_CLICK = 30
MAX_RECOMENDACIONES_POR_CATEGORIA = 10


def limpiar_recomendaciones_antiguas(db: Session) -> None:
    """
    Elimina del caché (base de datos) las recomendaciones que ya expiraron.
    - Las no clickeadas expiran a los 7 días.
    - Las clickeadas (feedback positivo) se retienen hasta 30 días.
    """
    ahora = datetime.now(timezone.utc)
    limite_no_click = ahora - timedelta(days=DIAS_EXPIRACION_NO_CLICK)
    limite_click = ahora - timedelta(days=DIAS_EXPIRACION_CLICK)
    
    # Bulk delete: recomendaciones ignoradas y viejas
    borrados_no_click = db.query(RecomendacionGenerada).filter(
        RecomendacionGenerada.fue_clickeada == False,
        RecomendacionGenerada.fecha_generacion < limite_no_click
    ).delete()
    
    # Bulk delete: recomendaciones usadas y muy viejas
    borrados_click = db.query(RecomendacionGenerada).filter(
        RecomendacionGenerada.fue_clickeada == True,
        RecomendacionGenerada.fecha_generacion < limite_click
    ).delete()
    
    logger.info("Caché limpiado: %d ignoradas eliminadas, %d clickeadas eliminadas.", 
                borrados_no_click, borrados_click)


def generar_para_usuario(
    db: Session, 
    usuario: UsuarioVisitante, 
    establecimientos_base: List[Establecimiento],
    estabs_informal: Optional[List[Establecimiento]] = None,
    estabs_descubrimiento: Optional[List[Establecimiento]] = None
) -> List[RecomendacionGenerada]:
    """
    Orquesta los algoritmos de la Fase 2 para construir las recomendaciones
    por cada categoría soportada por el frontend.

    Args:
        db (Session): Sesión BD.
        usuario (UsuarioVisitante): Usuario destino de las recomendaciones.
        establecimientos_base (List): Establecimientos top genéricos como fallback.

    Returns:
        List[RecomendacionGenerada]: Lista de objetos listos para inserción masiva.
    """
    nuevas_recomendaciones = []
    ahora = datetime.now(timezone.utc)
    
    def agregar_recomendaciones(estabs: Optional[List[Any]], categoria: str, razon: str, estrategia: str) -> None:
        """Función helper para evitar duplicación de código al instanciar el modelo."""
        if not estabs:
            return
        for pos, item in enumerate(estabs[:MAX_RECOMENDACIONES_POR_CATEGORIA]):
            # Las funciones de colaborativo y contenido devuelven tuplas (Establecimiento, score)
            if isinstance(item, tuple):
                estab = item[0]
                score_usado = item[1]
            else:
                estab = item
                score_usado = 0.0
                
            rec = RecomendacionGenerada(
                id_usuario=usuario.id_usuario,
                id_establecimiento=int(estab.id_establecimiento), # type: ignore
                categoria_recomendacion=categoria,
                posicion=pos + 1,
                radio_usado_km=int(usuario.radio_busqueda_km), # type: ignore
                razon_principal=razon,
                estrategia_usada=estrategia,
                fecha_generacion=ahora
            )
            # Asignamos el score a la columna correcta según la estrategia
            if estrategia == "contenido":
                rec.score_contenido_usado = score_usado # type: ignore
            elif estrategia == "cluster":
                rec.score_colaborativo_usado = score_usado # type: ignore
                
            nuevas_recomendaciones.append(rec)

    # 1. Estrategia Cold Start (Usuarios nuevos)
    # Se evalúa si el usuario apenas está iniciando.
    if not usuario.perfil_completado or usuario.puntos_experiencia < 50:
        if get_cold_start_recommendations:
            estabs_cold = get_cold_start_recommendations(db, usuario, limit=MAX_RECOMENDACIONES_POR_CATEGORIA)
            agregar_recomendaciones(estabs_cold, "cold_start", "cold_start", "cold_start")
    else:
        # 2. Estrategias Híbridas (Usuarios experimentados)
        
        # Filtrado por Contenido
        if get_content_based_recommendations and establecimientos_base:
            estabs_content = get_content_based_recommendations(db, usuario, establecimientos_base, limit=MAX_RECOMENDACIONES_POR_CATEGORIA)
            agregar_recomendaciones(estabs_content, "preferencia_contenido", "preferencia_categoria", "contenido")
            
        # Filtrado Colaborativo (Basado en Cluster)
        if get_collaborative_recommendations and establecimientos_base and usuario.id_cluster is not None:
            estabs_collab = get_collaborative_recommendations(db, int(usuario.id_usuario), int(usuario.id_cluster), establecimientos_base, limit=MAX_RECOMENDACIONES_POR_CATEGORIA) # type: ignore
            agregar_recomendaciones(estabs_collab, "colaborativo_cluster", "colaborativo", "cluster")

    # 3. Estrategia Global / Fallback (Aplica para todos)
    # Recomendaciones populares por ranking base
    if establecimientos_base:
        agregar_recomendaciones(establecimientos_base, "popularidad_zona", "popular_zona", "popularidad")
        
    # Tendencia Informal
    if estabs_informal:
        agregar_recomendaciones(estabs_informal, "tendencia_informal", "popular_informal", "popularidad")
        
    # Descubrimiento
    if estabs_descubrimiento:
        agregar_recomendaciones(estabs_descubrimiento, "descubrimiento", "nuevo_lugar", "novedad")
            
    return nuevas_recomendaciones


def procesar_generacion(db: Session) -> None:
    """
    Coordina el job offline completo: limpia el caché, busca usuarios activos,
    y hace un bulk insert (inserción masiva) con los resultados del engine.
    """
    # 1. Limpieza de datos expirados
    limpiar_recomendaciones_antiguas(db)
    
    # 2. Obtener usuarios que se hayan conectado en los últimos 30 días
    limite_actividad = datetime.now(timezone.utc) - timedelta(days=30)
    usuarios_activos = db.query(UsuarioVisitante).filter(
        UsuarioVisitante.fecha_ultima_actividad >= limite_actividad
    ).all()
    
    if not usuarios_activos:
        logger.warning("No hay usuarios activos en los últimos 30 días para generar recomendaciones.")
        return
        
    # 3. Pre-cargar una lista general (Fallback de ranking)
    top_establecimientos = []
    if get_top_establecimientos:
        top_establecimientos = get_top_establecimientos(db, limit=MAX_RECOMENDACIONES_POR_CATEGORIA)
        
    from backend.models.establecimientos import MetricaEstablecimiento
    
    estabs_informal = db.query(Establecimiento).join(MetricaEstablecimiento).filter(
        Establecimiento.es_activo == True,
        Establecimiento.estado == "aprobado",
        Establecimiento.es_informal == True
    ).order_by(MetricaEstablecimiento.popularidad_7d.desc().nulls_last()).limit(MAX_RECOMENDACIONES_POR_CATEGORIA).all()
    
    estabs_descubrimiento = db.query(Establecimiento).filter(
        Establecimiento.es_activo == True,
        Establecimiento.estado == "aprobado"
    ).order_by(Establecimiento.fecha_registro.desc()).limit(MAX_RECOMENDACIONES_POR_CATEGORIA).all()
        
    total_generadas = 0
    
    # 4. Generación por usuario e Inserción Masiva
    for usuario in usuarios_activos:
        recomendaciones_usuario = generar_para_usuario(
            db, usuario, top_establecimientos, estabs_informal, estabs_descubrimiento
        )
        
        if recomendaciones_usuario:
            # bulk_save_objects es altamente optimizado para insertar miles de filas sin hidratar IDs
            db.bulk_save_objects(recomendaciones_usuario)
            total_generadas += len(recomendaciones_usuario)
            
    logger.info("Generación completada: %d recomendaciones insertadas para %d usuarios.", 
                total_generadas, len(usuarios_activos))


def ejecutar_generacion(db: Session) -> None:
    """
    Orquestador transaccional llamado por runner.py.
    Asegura el commit atómico de todo el lote de recomendaciones.
    """
    try:
        procesar_generacion(db)
        db.commit()
        logger.info("Transacción de generación de recomendaciones confirmada (commit).")
    except Exception as e:
        db.rollback()
        logger.error("Error durante la generación masiva (rollback): %s", e)
        raise e
