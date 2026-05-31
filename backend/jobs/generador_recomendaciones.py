"""
Job Offline: Generador Masivo de Recomendaciones

Responsabilidad:
Pre-computar y persistir las listas de recomendaciones (cajas) para todos los usuarios
activos. Limpia el caché antiguo y genera recomendaciones por cada categoría (estrategia)
usando los algoritmos de filtrado (contenido, colaborativo, etc.) desarrollados en la Fase 2.

Cumple con SRP al delegar los algoritmos matemáticos a la carpeta `backend.engine` y
enfocarse exclusivamente en la orquestación masiva y persistencia (bulk inserts).

Mejoras aplicadas para mayor personalización:
  3A — Pool personalizado por cluster: en lugar del top-40 global, se construye un pool
       exclusivo del cluster del usuario ordenado por señal colaborativa interna (cuánto
       interactuaron otros usuarios del mismo cluster con cada establecimiento). Esto
       maximiza la personalización sin duplicar la lógica del carrusel de descubrimiento.
  3B — Serendipia real con diversity_score: el carrusel 'descubrimiento' selecciona
       establecimientos de clusters DISTINTOS al del usuario y los ordena por diversity_score
       contra los candidatos ya seleccionados, no por fecha_registro.
  3C — Repeticiones cross-carrusel controladas: un establecimiento puede aparecer en
       máximo 2 carruseles distintos por usuario. Si supera ese límite, se omite.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Any, cast

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from backend.models.usuarios import UsuarioVisitante
from backend.models.establecimientos import Establecimiento, MetricaEstablecimiento
from backend.models.interacciones import RecomendacionGenerada, InteraccionUsuario

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

try:
    from backend.engine.content_filter import get_content_based_recommendations, calcular_diversity_score
except ImportError:
    get_content_based_recommendations = None
    calcular_diversity_score = None

try:
    from backend.engine.collab_filter import get_collaborative_recommendations
except ImportError:
    get_collaborative_recommendations = None


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

# ─── Componente 4 — Umbrales de transición Cold Start ────────────────────────
# Cada interacción significativa otorga 10 puntos_experiencia (diseño §1.5).
# Los umbrales están calibrados coherentemente con MIN_INTERACCIONES_COLABORATIVO
# en cold_start.py (5 interacciones = 50 puntos = UMBRAL_FASE_1).
UMBRAL_FASE_1: int = 50   # ≥5 interacciones → entrar en transición
UMBRAL_FASE_2: int = 150  # ≥15 interacciones → ML completo


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


def determinar_fase(usuario: UsuarioVisitante) -> int:
    """
    Componente 4 — Determina la fase de transición del usuario basándose en
    sus puntos_experiencia y si completó el onboarding.

    Fases:
      0  →  Cold start puro (< 5 interacciones / < 50 puntos).
             El usuario ve solo el carrusel 'Populares de la semana'.
      1  →  Transición (5–15 interacciones / 50–150 puntos).
             Blend: cold start reducido + primer carrusel de contenido.
             El colaborativo aún no se activa (matriz dispersa insuficiente).
      2  →  ML completo (> 15 interacciones / > 150 puntos).
             Todos los carruseles activos: híbrido, contenido, colaborativo.

    La relación 1 interacción = 10 puntos garantiza coherencia con
    MIN_INTERACCIONES_COLABORATIVO = 5 en cold_start.py.

    Args:
        usuario: UsuarioVisitante con puntos_experiencia y perfil_completado.

    Returns:
        int: 0, 1 ó 2 según la fase.
    """
    puntos = int(usuario.puntos_experiencia or 0)  # type: ignore
    if not usuario.perfil_completado or puntos < UMBRAL_FASE_1:
        return 0
    elif puntos < UMBRAL_FASE_2:
        return 1
    else:
        return 2


def obtener_candidatos_por_cluster(
    db: Session,
    usuario: UsuarioVisitante,
    limit: int = 40,
) -> List[Establecimiento]:
    """
    Mejora 3A — Pool personalizado 100% por cluster con señal colaborativa interna.

    En lugar del top-40 global (ordenado por score_boost_combinado sin distinguir
    entre usuarios), este pool se construye exclusivamente con establecimientos del
    cluster del usuario y los ordena por la señal colaborativa interna del cluster:
    cuánto peso acumulado de interacciones generaron otros usuarios del mismo cluster
    en los últimos 90 días.

    Se usa el pool 100% dentro del cluster y ordenarlo por señal colaborativa interna
    maximiza la personalización en los carruseles de preferencia sin duplicar la
    lógica de serendipia.

    Fallback: si el usuario no tiene id_cluster asignado o el cluster no tiene
    suficientes candidatos, se complementa con el top global por score_boost_combinado.

    Args:
        db: Sesión activa de SQLAlchemy.
        usuario: UsuarioVisitante con id_cluster poblado.
        limit: Tamaño máximo del pool.

    Returns:
        Lista de Establecimiento ordenada por señal colaborativa interna del cluster.
    """
    if not usuario.id_cluster:
        # Fallback: sin cluster asignado, usar ranking global
        if get_top_establecimientos:
            return get_top_establecimientos(db, limit=limit)
        return []

    fecha_limite_collab = datetime.now(timezone.utc) - timedelta(days=90)

    # Calcular la señal colaborativa interna del cluster:
    # suma de peso_interaccion de todos los usuarios del mismo cluster en 90 días
    stmt_scores = (
        select(
            InteraccionUsuario.id_establecimiento,
            func.sum(InteraccionUsuario.peso_interaccion).label("score_cluster")
        )
        .join(UsuarioVisitante, InteraccionUsuario.id_usuario == UsuarioVisitante.id_usuario)
        .where(
            UsuarioVisitante.id_cluster == usuario.id_cluster,
            InteraccionUsuario.fecha >= fecha_limite_collab,
        )
        .group_by(InteraccionUsuario.id_establecimiento)
        .order_by(func.sum(InteraccionUsuario.peso_interaccion).desc())
        .limit(limit)
    )
    rows = db.execute(stmt_scores).all()
    ids_ordenados = [r.id_establecimiento for r in rows]

    if ids_ordenados:
        # Traer los establecimientos en el orden calculado, filtrados por cluster y activos
        estabs_map = {
            e.id_establecimiento: e
            for e in db.query(Establecimiento)
            .filter(
                Establecimiento.id_establecimiento.in_(ids_ordenados),
                Establecimiento.id_cluster == usuario.id_cluster,
                Establecimiento.es_activo == True,
                Establecimiento.estado == "aprobado",
            )
            .all()
        }
        # Preservar el orden por señal colaborativa
        candidatos = [estabs_map[eid] for eid in ids_ordenados if eid in estabs_map]
    else:
        candidatos = []

    # Si el cluster tiene pocos establecimientos con interacciones, complementar
    # con los mejor rankeados del mismo cluster por score_boost_combinado
    if len(candidatos) < limit:
        ids_ya_incluidos = {e.id_establecimiento for e in candidatos}
        faltantes = limit - len(candidatos)
        complemento = (
            db.query(Establecimiento)
            .join(MetricaEstablecimiento)
            .filter(
                Establecimiento.id_cluster == usuario.id_cluster,
                Establecimiento.es_activo == True,
                Establecimiento.estado == "aprobado",
                Establecimiento.id_establecimiento.notin_(ids_ya_incluidos),
            )
            .order_by(MetricaEstablecimiento.score_boost_combinado.desc())
            .limit(faltantes)
            .all()
        )
        candidatos.extend(complemento)

    # Fallback final: si el cluster no tiene nada, usar top global
    if not candidatos and get_top_establecimientos:
        logger.warning(
            "Cluster %d sin candidatos — usando top global para usuario_id=%d",
            usuario.id_cluster,
            usuario.id_usuario,
        )
        return get_top_establecimientos(db, limit=limit)

    return candidatos


def obtener_descubrimientos(
    db: Session,
    usuario: UsuarioVisitante,
    candidatos_seleccionados: List[Establecimiento],
    limit: int = 10,
) -> List[tuple]:
    """
    Mejora 3B — Serendipia real con diversity_score.

    Reemplaza el ordenamiento por fecha_registro DESC por una selección basada en
    diversity_score: qué tan DISTINTO es cada candidato respecto a los establecimientos
    ya seleccionados para el usuario. Solo considera establecimientos de clusters
    DISTINTOS al del usuario para garantizar verdadera sorpresa.

    Args:
        db: Sesión activa de SQLAlchemy.
        usuario: UsuarioVisitante con id_cluster poblado.
        candidatos_seleccionados: Establecimientos ya asignados a carruseles del usuario.
        limit: Número máximo de descubrimientos a retornar.

    Returns:
        Lista de tuplas (Establecimiento, diversity_score) ordenadas por diversidad desc.
    """
    # Filtro base: clusters distintos al del usuario, activos y aprobados.
    # Los informales tienen su propio carrusel (tendencia_informal), se excluyen aquí.
    filtros = [
        Establecimiento.es_activo == True,
        Establecimiento.estado == "aprobado",
        Establecimiento.es_informal == False,
    ]
    if usuario.id_cluster is not None:
        filtros.append(Establecimiento.id_cluster != usuario.id_cluster)

    candidatos_otros = db.query(Establecimiento).filter(*filtros).all()

    if not candidatos_otros:
        # Fallback sin cluster: establecimientos recientes para no devolver vacío
        logger.warning(
            "Sin candidatos cross-cluster para descubrimiento (usuario_id=%d) — usando recientes",
            usuario.id_usuario,
        )
        return [
            (e, 0.5)
            for e in db.query(Establecimiento)
            .filter(
                Establecimiento.es_activo == True,
                Establecimiento.estado == "aprobado",
                Establecimiento.es_informal == False,
            )
            .order_by(Establecimiento.fecha_registro.desc())
            .limit(limit)
            .all()
        ]

    # Vectores de los candidatos ya seleccionados (para calcular qué tan distinto es cada candidato).
    # cast() necesario: SQLAlchemy infiere Column(JSON) como Column[Any] a nivel de clase,
    # pero en runtime la instancia retorna el valor Python real (list[float]).
    # cast() es una no-operación en runtime — solo existe para el type checker.
    vecs_seleccionados = cast(list[list[float]], [
        e.vector_caracteristicas
        for e in candidatos_seleccionados
        if e.vector_caracteristicas
    ])

    scored = []
    for estab in candidatos_otros:
        if not estab.vector_caracteristicas:
            continue
        if calcular_diversity_score and vecs_seleccionados:
            # casteamos vector_caracteristicas de Column[Any] a list[float] para el type checker
            div_score = calcular_diversity_score(
                cast(list[float], estab.vector_caracteristicas),
                vecs_seleccionados
            )
        else:
            # Sin vectores disponibles, asignar score neutro
            div_score = 0.5
        scored.append((estab, div_score))

    # Ordenar por diversity_score DESC: el más distinto al perfil ya seleccionado va primero
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit]


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

    # ── 1. Determinar fase de transición (Componente 4) ───────────────────────
    # Se calcula ahora (en el job offline) y se persiste en BD para que el
    # recomendacion_service online pueda consultarla sin recalcular.
    fase = determinar_fase(usuario)
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
        # Mejora 3A: pool personalizado por cluster con señal colaborativa interna.
        # Cada usuario recibe candidatos de su propio cluster, no el mismo top-40 global.
        POOL_CANDIDATOS = 40
        candidatos_usuario = obtener_candidatos_por_cluster(db, usuario, limit=POOL_CANDIDATOS)

        # Mejora 3B: descubrimientos calculados por usuario con diversity_score.
        # Se pasan los candidatos ya seleccionados para maximizar la distancia semántica.
        estabs_descubrimiento = obtener_descubrimientos(
            db,
            usuario,
            candidatos_seleccionados=candidatos_usuario,
            limit=MAX_RECOMENDACIONES_POR_CATEGORIA,
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
