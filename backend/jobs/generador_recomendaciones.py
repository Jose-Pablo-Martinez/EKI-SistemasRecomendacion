"""
Job Offline: Generador Masivo de Recomendaciones

Responsabilidad:
    Orquestar los algoritmos de la Fase 2 (engine) para generar y persistir en bulk
    las listas de recomendaciones para todos los usuarios activos. Se limita a:
      1. Limpiar el caché de recomendaciones expiradas.
      2. Coordinar las llamadas al engine (cold_start, content_filter, collab_filter).
      3. Hacer el bulk insert de RecomendacionGenerada.

    La lógica de negocio (umbrales, señales colaborativas, diversity_score) vive en
    los módulos especializados de `backend.engine`, no aquí.

Mejoras aplicadas para mayor personalización:
  3A — Pool personalizado por cluster (collab_filter.obtener_candidatos_por_cluster).
  3B — Serendipia real con diversity_score (content_filter.obtener_descubrimientos).
  3C — Repeticiones cross-carrusel controladas (MAX_APARICIONES_POR_ESTABLECIMIENTO).
  C4 — Transición suave del Cold Start (cold_start.determinar_fase).
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Any, cast

from sqlalchemy.orm import Session

from backend.models.usuarios import UsuarioVisitante
from backend.models.establecimientos import Establecimiento, MetricaEstablecimiento
from backend.models.interacciones import RecomendacionGenerada

# Importaciones seguras de la Fase 2 (Engine)
# Se usa try-except para evitar bloqueos si alguna función aún no está expuesta en su módulo
try:
    from backend.engine.cold_start import (
        get_cold_start_recommendations,
        determinar_fase,
    )
except ImportError:
    get_cold_start_recommendations = None
    determinar_fase = None  # type: ignore

try:
    from backend.engine.ranking import get_top_establecimientos
except ImportError:
    get_top_establecimientos = None

try:
    from backend.engine.content_filter import (
        get_content_based_recommendations,
        obtener_descubrimientos,
    )
except ImportError:
    get_content_based_recommendations = None
    obtener_descubrimientos = None  # type: ignore

try:
    from backend.engine.collab_filter import (
        get_collaborative_recommendations,
        obtener_candidatos_por_cluster,
    )
except ImportError:
    get_collaborative_recommendations = None
    obtener_candidatos_por_cluster = None  # type: ignore


logger = logging.getLogger(__name__)

# Constantes de Retención y Generación
DIAS_EXPIRACION_NO_CLICK = 7
DIAS_EXPIRACION_CLICK = 30
# El carrusel Híbrido (top_picks) es más selectivo — solo muestra los mejores 10.
# Los demás carruseles muestran hasta 20 items para dar más diversidad y serendipia.
MAX_RECOMENDACIONES_HIBRIDO = 10
MAX_RECOMENDACIONES_POR_CATEGORIA = 20

# ─── Mejora 3C — Control de repeticiones cross-carrusel ──────────────────────
# Un establecimiento puede aparecer en máximo 2 carruseles distintos por usuario.
# Si supera el límite, se omite del carrusel actual. Se razonó que un lugar
# puede legítimamente cumplir criterios de 2 carruseles (ej. alta puntuación +
# popularidad en su zona), pero inundar 3-4 carruseles reduce la variedad percibida.
MAX_APARICIONES_POR_ESTABLECIMIENTO: int = 2

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
    estabs_descubrimiento: Optional[List[tuple]] = None,
) -> List[RecomendacionGenerada]:
    """
    Orquesta los algoritmos de la Fase 2 para construir las recomendaciones
    por cada categoría soportada por el frontend.

    Mejora 3C — Control de repeticiones cross-carrusel:
    Se mantiene un conteo_apariciones por id_establecimiento. Si un establecimiento
    ya alcanzó MAX_APARICIONES_POR_ESTABLECIMIENTO (2), se omite de los carruseles
    restantes. Un lugar puede aparecer en 2 carruseles si cumple ambos criterios
    (ej. popularidad + preferencia_contenido), pero no en más.

    Args:
        db (Session): Sesión BD.
        usuario (UsuarioVisitante): Usuario destino de las recomendaciones.
        establecimientos_base (List): Pool personalizado del cluster del usuario (Mejora 3A).
        estabs_informal: Establecimientos informales populares.
        estabs_descubrimiento: Tuplas (Establecimiento, diversity_score) (Mejora 3B).

    Returns:
        List[RecomendacionGenerada]: Lista de objetos listos para inserción masiva.
    """
    nuevas_recomendaciones = []
    ahora = datetime.now(timezone.utc)

    # Mejora 3C: contador de apariciones por establecimiento entre todos los carruseles
    conteo_apariciones: dict[int, int] = {}

    def agregar_recomendaciones(
        estabs: Optional[List[Any]],
        categoria: str,
        razon: str,
        estrategia: str,
        detalle: str = "",
        es_descubrimiento_flag: bool = False,
    ) -> None:
        """
        Helper para instanciar RecomendacionGenerada con control de repeticiones (3C).
        Respeta MAX_APARICIONES_POR_ESTABLECIMIENTO: si un establecimiento ya alcanzó
        su límite de apariciones en otros carruseles, se omite silenciosamente.
        """
        if not estabs:
            return
        pos_efectiva = 0
        for item in estabs:
            if pos_efectiva >= MAX_RECOMENDACIONES_POR_CATEGORIA:
                break

            sc_cont = 0.0
            sc_col = 0.0
            div_score_val = None

            if isinstance(item, tuple):
                estab = item[0]
                score_usado = item[1]
                if len(item) > 2:
                    sc_cont = item[2]
                if len(item) > 3:
                    sc_col = item[3]
            else:
                estab = item
                score_usado = 0.0

            eid = int(estab.id_establecimiento)  # type: ignore

            # Mejora 3C: omitir si ya alcanzó el límite de apariciones cross-carrusel
            if conteo_apariciones.get(eid, 0) >= MAX_APARICIONES_POR_ESTABLECIMIENTO:
                continue
            conteo_apariciones[eid] = conteo_apariciones.get(eid, 0) + 1

            rec = RecomendacionGenerada(
                id_usuario=usuario.id_usuario,
                id_establecimiento=eid,
                categoria_recomendacion=categoria,
                posicion=pos_efectiva + 1,
                radio_usado_km=int(usuario.radio_busqueda_km),  # type: ignore
                razon_principal=razon,
                detalle_razon=detalle,
                estrategia_usada=estrategia,
                fecha_generacion=ahora,
                es_descubrimiento=es_descubrimiento_flag,
            )

            # Asignamos el score a la columna correcta según la estrategia
            if estrategia == "contenido":
                rec.score_contenido_usado = score_usado  # type: ignore
            elif estrategia == "cluster":
                rec.score_colaborativo_usado = score_usado  # type: ignore
            elif estrategia == "hibrido":
                rec.score_total = score_usado  # type: ignore
                rec.score_contenido_usado = sc_cont  # type: ignore
                rec.score_colaborativo_usado = sc_col  # type: ignore
            elif estrategia == "serendipia":
                # Mejora 3B: persiste el diversity_score para caja blanca
                rec.diversity_score = score_usado  # type: ignore

            nuevas_recomendaciones.append(rec)
            pos_efectiva += 1

    # ── 1. Determinar fase de transición — delegado a cold_start.determinar_fase ──
    # Se calcula en el job offline y se persiste en BD para que el
    # recomendacion_service online pueda consultarla sin recalcular.
    fase = determinar_fase(usuario) if determinar_fase else 0
    usuario.fase_transicion = fase  # type: ignore
    logger.debug(
        "generar_para_usuario: usuario_id=%d fase=%d puntos=%s",
        usuario.id_usuario, fase, usuario.puntos_experiencia,
    )

    if fase == 0:
        # ── FASE 0: Cold start puro ───────────────────────────────────────────
        # Solo el carrusel 'Populares de la semana'. El usuario es muy nuevo y
        # no tiene suficiente historial para ML ni para filtrado colaborativo.
        if get_cold_start_recommendations:
            estabs_cold = get_cold_start_recommendations(
                db, usuario, limit=MAX_RECOMENDACIONES_POR_CATEGORIA
            )
            agregar_recomendaciones(
                estabs_cold, "cold_start", "cold_start", "cold_start",
                "Seleccionado para empezar",
            )

    elif fase == 1:
        # ── FASE 1: Blend cold start + contenido (sin colaborativo) ──────────
        # El usuario ya acumuló entre 5 y 15 interacciones: tiene suficiente
        # historial para el filtrado por contenido, pero la matriz dispersa del
        # colaborativo aún no es significativa (< 15 interacciones).
        # Efecto en el frontend: el usuario ve 2 carruseles —
        #   «Populares de la semana» (familiar) + «Basado en tus gustos» (nuevo).
        # El cold start usa un limit reducido para que el carrusel ML pueda
        # "competir" visualmente sin desaparecer entre muchos resultados populares.
        LIMIT_COLD_FASE1 = MAX_RECOMENDACIONES_POR_CATEGORIA // 2  # 10 items
        LIMIT_CONTENT_FASE1 = MAX_RECOMENDACIONES_POR_CATEGORIA    # 20 items

        if get_cold_start_recommendations:
            estabs_cold = get_cold_start_recommendations(
                db, usuario, limit=LIMIT_COLD_FASE1
            )
            agregar_recomendaciones(
                estabs_cold, "cold_start", "cold_start", "cold_start",
                "Seleccionado para empezar",
            )

        if get_content_based_recommendations and establecimientos_base:
            estabs_content = get_content_based_recommendations(
                db, usuario, establecimientos_base, limit=LIMIT_CONTENT_FASE1
            )
            agregar_recomendaciones(
                estabs_content, "preferencia_contenido", "preferencia_categoria", "contenido",
                "Alta similitud con tus categorías favoritas",
            )

    else:
        # ── FASE 2: ML completo ───────────────────────────────────────────────
        estabs_content = []
        estabs_collab = []

        # El pool establecimientos_base ya es personalizado por cluster (Mejora 3A),
        # por lo que content y collab operan sobre candidatos más relevantes para el usuario.
        if get_content_based_recommendations and establecimientos_base:
            estabs_content = get_content_based_recommendations(
                db, usuario, establecimientos_base, limit=MAX_RECOMENDACIONES_POR_CATEGORIA
            )

        if get_collaborative_recommendations and establecimientos_base and usuario.id_cluster is not None:
            estabs_collab = get_collaborative_recommendations(
                db,
                int(usuario.id_usuario),  # type: ignore
                int(usuario.id_cluster),  # type: ignore
                establecimientos_base,
                limit=MAX_RECOMENDACIONES_POR_CATEGORIA,
            )

        # Filtrado Híbrido / Mejores Selecciones (Top Picks)
        if estabs_content or estabs_collab:
            from backend.engine.ranking import compute_score_final
            candidatos_dict = {}

            for estab, score in estabs_content:
                candidatos_dict[estab.id_establecimiento] = {"estab": estab, "sc_cont": score, "sc_col": 0.0}
            for estab, score in estabs_collab:
                if estab.id_establecimiento not in candidatos_dict:
                    candidatos_dict[estab.id_establecimiento] = {"estab": estab, "sc_cont": 0.0, "sc_col": score}
                else:
                    candidatos_dict[estab.id_establecimiento]["sc_col"] = score

            top_picks = []
            for d in candidatos_dict.values():
                estab = d["estab"]
                score_boost = 0.0
                if hasattr(estab, "metrica") and estab.metrica and estab.metrica.score_boost_combinado:
                    score_boost = float(estab.metrica.score_boost_combinado)
                score_final = compute_score_final(d["sc_cont"], d["sc_col"], score_boost)
                top_picks.append((estab, score_final, d["sc_cont"], d["sc_col"]))

            top_picks.sort(key=lambda x: x[1], reverse=True)
            agregar_recomendaciones(
                top_picks[:MAX_RECOMENDACIONES_HIBRIDO],
                "preferencia_contenido", "preferencia_categoria", "hibrido",
                "La mejor combinación entre tus gustos y los de tu comunidad",
            )

        if estabs_content:
            agregar_recomendaciones(
                estabs_content, "preferencia_contenido", "preferencia_categoria", "contenido",
                "Alta similitud con tus categorías favoritas",
            )

        if estabs_collab:
            agregar_recomendaciones(
                estabs_collab, "colaborativo_cluster", "colaborativo", "cluster",
                "Personas con gustos similares lo visitan frecuentemente",
            )

    # ── 3. Estrategias globales / Fallback (Aplican para todos) ──────────────
    if establecimientos_base:
        agregar_recomendaciones(
            establecimientos_base, "popularidad_zona", "popular_zona", "popularidad",
            "Lugares con altas calificaciones cerca de ti",
        )

    if estabs_informal:
        agregar_recomendaciones(
            estabs_informal, "tendencia_informal", "tendencia_informal", "popularidad",
            "Puestos populares para apoyar el comercio local",
        )

    # Mejora 3B: descubrimiento con diversity_score, marcado como es_descubrimiento=True
    if estabs_descubrimiento:
        agregar_recomendaciones(
            estabs_descubrimiento, "descubrimiento", "descubrimiento", "serendipia",
            "Aventúrate a probar opciones diferentes",
            es_descubrimiento_flag=True,
        )

    return nuevas_recomendaciones


def procesar_generacion(db: Session) -> None:
    """
    Coordina el job offline completo: limpia el caché, busca usuarios activos,
    y hace un bulk insert (inserción masiva) con los resultados del engine.

    Mejora 3A: el pool de candidatos ya no es global — se construye por usuario
    dentro de su cluster con señal colaborativa interna (obtener_candidatos_por_cluster).
    Mejora 3B: el carrusel descubrimiento usa diversity_score en lugar de fecha_registro.
    Mejora 3C: el control de repeticiones ocurre dentro de generar_para_usuario.
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

    # 3. Pre-cargar datos globales que son iguales para todos los usuarios
    # (informales populares — no dependen del cluster del usuario)
    estabs_informal = (
        db.query(Establecimiento)
        .join(MetricaEstablecimiento)
        .filter(
            Establecimiento.es_activo == True,
            Establecimiento.estado == "aprobado",
            Establecimiento.es_informal == True,
        )
        .order_by(MetricaEstablecimiento.popularidad_7d.desc())
        .limit(MAX_RECOMENDACIONES_POR_CATEGORIA)
        .all()
    )

    total_generadas = 0

    # 4. Generación por usuario e Inserción Masiva
    for usuario in usuarios_activos:
        # Mejora 3A — pool personalizado delegado a collab_filter.obtener_candidatos_por_cluster
        POOL_CANDIDATOS = 40
        candidatos_usuario = (
            obtener_candidatos_por_cluster(db, usuario, limit=POOL_CANDIDATOS)
            if obtener_candidatos_por_cluster
            else []
        )

        # Mejora 3B — serendipia delegada a content_filter.obtener_descubrimientos
        estabs_descubrimiento = (
            obtener_descubrimientos(
                db,
                usuario,
                candidatos_seleccionados=candidatos_usuario,
                limit=MAX_RECOMENDACIONES_POR_CATEGORIA,
            )
            if obtener_descubrimientos
            else []
        )

        recomendaciones_usuario = generar_para_usuario(
            db, usuario, candidatos_usuario, estabs_informal, estabs_descubrimiento
        )

        if recomendaciones_usuario:
            # Antes de insertar, borrar recomendaciones vigentes del usuario para esta corrida
            # (solo las no-clickeadas, para no perder el feedback del usuario)
            db.query(RecomendacionGenerada).filter(
                RecomendacionGenerada.id_usuario == usuario.id_usuario,
                RecomendacionGenerada.fue_clickeada == False,
            ).delete(synchronize_session=False)
            # bulk_save_objects es altamente optimizado para insertar miles de filas sin hidratar IDs
            db.bulk_save_objects(recomendaciones_usuario)
            total_generadas += len(recomendaciones_usuario)

    logger.info(
        "Generación completada: %d recomendaciones insertadas para %d usuarios.",
        total_generadas,
        len(usuarios_activos),
    )


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
