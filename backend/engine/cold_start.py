"""
Módulo de Inicio en Frío (Cold Start) — EKI.

Responsabilidad:
    Proveer recomendaciones para usuarios nuevos sin historial de interacciones,
    y gestionar la visibilidad inicial de establecimientos recién registrados.

Estrategia de cold start (Implementada con modificaciones de EkiSystem_DB_Design.md:)

    1. Clustering offline previo: los centroides de cluster_usuario ya existen.
    2. Al registrarse, el usuario completa el onboarding → se construye
       vector_preferencias desde sus preferencias declaradas.
    3. Se calcula la distancia euclidiana entre vector_preferencias y cada
       centroide de cluster_usuario para asignar el cluster provisional.
    4. El componente colaborativo se activa cuando perfil_completado=TRUE
       y el usuario acumula suficientes interacciones (N configurable).

Nota arquitectónica (Estrategia Offline-First):
    La asignación de cluster (paso 3) se puede hacer ONLINE al registrarse
    porque solo requiere calcular distancias a los centroides ya pre-computados.
    El K-Means completo (reentrenamiento) es OFFLINE.
"""

import logging
from typing import TYPE_CHECKING

import numpy as np
from sqlalchemy import select

from backend.models import Establecimiento, MetricaEstablecimiento

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from backend.models import UsuarioVisitante, ClusterUsuario
logger = logging.getLogger(__name__)

# Constantes para el Cold Start
COLD_START_LIMIT: int = 15              # Resultados para usuarios nuevos
MIN_INTERACCIONES_COLABORATIVO: int = 5 # Umbral para activar componente colaborativo


def get_cold_start_recommendations(
    db: "Session",
    usuario: "UsuarioVisitante",
    limit: int = COLD_START_LIMIT,
) -> list["Establecimiento"]:
    """
    Genera recomendaciones de categoría 'cold_start' para un usuario nuevo.

    Estrategia:
        1. Asignar cluster provisional por distancia euclidiana a centroides.
        2. Filtrar establecimientos populares (popularidad_7d) cruzados con vector_preferencias.
        3. Si no hay suficientes resultados, rellenar usando el top de populares global.
        4. No usar componente colaborativo (perfil_completado=FALSE).

    Args:
        db: Sesión activa de SQLAlchemy.
        usuario: Instancia de UsuarioVisitante. Debe tener vector_preferencias
                 poblado desde el onboarding.
        limit: Número máximo de establecimientos a retornar.

    Returns:
        Lista de instancias Establecimiento para el cold start.
    """
    logger.info(
        "cold_start: generando recomendaciones para usuario_id=%d (perfil_completado=%s)",
        usuario.id_usuario,
        usuario.perfil_completado,
    )
    from backend.models.establecimientos import EstablecimientoCategoria
    from backend.models.catalogo import Categoria

    base_stmt = (
        select(Establecimiento)
        .outerjoin(MetricaEstablecimiento, Establecimiento.id_establecimiento == MetricaEstablecimiento.id_establecimiento)
        .where(
            Establecimiento.es_activo == True,
            Establecimiento.estado == "aprobado"
        )
    )

    resultados = []
    ids_obtenidos = set()

    # 1. Intentar obtener recomendaciones filtradas por preferencias
    if usuario.vector_preferencias and isinstance(usuario.vector_preferencias, dict):
        categorias_preferidas = usuario.vector_preferencias.get("categorias_preferidas", [])
        if categorias_preferidas:
            stmt_pref = base_stmt.where(
                Establecimiento.categorias.any(
                    EstablecimientoCategoria.categoria.has(
                        Categoria.nombre.in_(categorias_preferidas)
                    )
                )
            ).order_by(MetricaEstablecimiento.popularidad_7d.desc()).limit(limit)
            
            recs_pref = list(db.scalars(stmt_pref).all())
            resultados.extend(recs_pref)
            ids_obtenidos.update(r.id_establecimiento for r in recs_pref)

    # 2. Rellenar con top globales si no hay suficientes
    faltan = limit - len(resultados)
    if faltan > 0:
        stmt_top = base_stmt
        if ids_obtenidos:
            stmt_top = stmt_top.where(Establecimiento.id_establecimiento.not_in(ids_obtenidos))
        
        stmt_top = stmt_top.order_by(MetricaEstablecimiento.popularidad_7d.desc()).limit(faltan)
        resultados.extend(list(db.scalars(stmt_top).all()))

    return resultados


def assign_cluster_provisional(
    vector_preferencias: list[float],
    clusters: list["ClusterUsuario"],
) -> int | None:
    """
    Asigna un cluster provisional calculando la distancia euclidiana entre
    el vector_preferencias del usuario y cada centroide de cluster_usuario.

    Esta operación se ejecuta ONLINE al registrarse (los centroides ya existen).
    El K-Means completo (reentrenamiento de centroides) es OFFLINE.

    Args:
        vector_preferencias: Vector numérico del onboarding del usuario.
        clusters: Lista de instancias ClusterUsuario con centroides pre-computados.

    Returns:
        id_cluster del cluster más cercano, o None si no hay clusters.
    """
    if not clusters or not vector_preferencias:
        return None

    valid_clusters = [c for c in clusters if c.centroide]
    if not valid_clusters:
        return None

    user_vec = np.array(vector_preferencias)
    centroides = np.array([c.centroide for c in valid_clusters])

    distancias = np.linalg.norm(centroides - user_vec, axis=1)
    idx_min = int(np.argmin(distancias))
    mejor_cluster_id = int(valid_clusters[idx_min].id_cluster)  # type: ignore
    menor_distancia = float(distancias[idx_min])

    logger.debug(
        "cold_start: cluster asignado=%s (distancia=%.4f)",
        mejor_cluster_id,
        menor_distancia,
    )
    return mejor_cluster_id


def handle_new_establecimiento(id_establecimiento: int, db: "Session") -> dict:
    """
    Aplica la estrategia de visibilidad para un establecimiento recién registrado.

    Un establecimiento nuevo no tiene métricas, así que:
    - Se inicializa su fila en metrica_establecimiento con valores base.
    - Es elegible para la categoría 'cold_start' y 'tendencia_informal' si aplica.

    Args:
        id_establecimiento: ID del establecimiento recién aprobado.
        db: Sesión activa de SQLAlchemy.

    Returns:
        Diccionario con la información de visibilidad inicial asignada.
    """
    logger.info(
        "cold_start: procesando establecimiento nuevo id=%d", id_establecimiento
    )
    estab = db.get(Establecimiento, id_establecimiento)
    if not estab:
        return {"id_establecimiento": id_establecimiento, "status": "not_found"}

    boost_informal = 0.25 if estab.es_informal else 0.0

    metrica = MetricaEstablecimiento(
        id_establecimiento=id_establecimiento,
        score_contenido_base=0.0,
        score_colaborativo_base=0.0,
        boost_proximidad_zona=0.0,
        boost_informal=boost_informal,
        score_boost_combinado=0.0,
        popularidad_7d=0,
        popularidad_30d=0,
        polaridad_promedio=0.0
    )
    db.add(metrica)
    db.commit()

    return {"id_establecimiento": id_establecimiento, "status": "cold_start_applied"}


# Componente 4 — Transición Suave del Cold Start 
# Cada interacción significativa otorga 10 puntos_experiencia (diseño §1.5).
# Los umbrales están calibrados coherentemente con MIN_INTERACCIONES_COLABORATIVO
# (5 interacciones = 50 puntos = UMBRAL_FASE_1).
UMBRAL_FASE_1: int = 50   # ≥5 interacciones → entrar en transición
UMBRAL_FASE_2: int = 150  # ≥15 interacciones → ML completo


def determinar_fase(usuario: "UsuarioVisitante") -> int:
    """
    Determina la fase de transición del usuario basándose en sus
    puntos_experiencia y si completó el onboarding.

    Fases:
      0  →  Cold start puro (< 5 interacciones / < 50 puntos).
             El usuario ve solo el carrusel 'Populares de la semana'.
      1  →  Transición (5–15 interacciones / 50–150 puntos).
             Blend: cold start reducido + primer carrusel de contenido.
             El colaborativo aún no se activa (matriz dispersa insuficiente).
      2  →  ML completo (> 15 interacciones / > 150 puntos).
             Todos los carruseles activos: híbrido, contenido, colaborativo.

    La relación 1 interacción = 10 puntos garantiza coherencia con
    MIN_INTERACCIONES_COLABORATIVO = 5 en este mismo módulo.

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
