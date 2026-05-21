"""
Módulo de Inicio en Frío (Cold Start) — EKI.

Responsabilidad:
    Proveer recomendaciones para usuarios nuevos sin historial de interacciones,
    y gestionar la visibilidad inicial de establecimientos recién registrados.

Estrategia de cold start (ver §1.2 Fase 2 de EkiSystem_DB_Design.md):

    1. Clustering offline previo: los centroides de cluster_usuario ya existen.
    2. Al registrarse, el usuario completa el onboarding → se construye
       vector_preferencias desde sus preferencias declaradas.
    3. Se calcula la distancia euclidiana entre vector_preferencias y cada
       centroide de cluster_usuario para asignar el cluster provisional.
    4. Las recomendaciones iniciales son:
       - Popularidad dentro del cluster (metrica_establecimiento.popularidad_7d)
       - Filtrado por contenido desde preferencias declaradas (sin colaborativo)
    5. El componente colaborativo se activa cuando perfil_completado=TRUE
       y el usuario acumula suficientes interacciones (N configurable).

Nota arquitectónica (§1.7 — Offline-First):
    La asignación de cluster (paso 3) se puede hacer ONLINE al registrarse
    porque solo requiere calcular distancias a los centroides ya pre-computados.
    El K-Means completo (reentrenamiento) es OFFLINE.
"""

import logging
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # pyrefly: ignore [missing-import]
    from sqlalchemy.orm import Session
    from backend.models import Establecimiento, UsuarioVisitante, ClusterUsuario

logger = logging.getLogger(__name__)

# ─── Constantes de Cold Start ─────────────────────────────────────────────────
COLD_START_LIMIT: int = 10              # Resultados para usuarios nuevos
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
        2. Retornar establecimientos populares (popularidad_7d) dentro del cluster.
        3. Aplicar filtrado por contenido desde vector_preferencias del onboarding.
        4. No usar componente colaborativo (perfil_completado=FALSE).

    Args:
        db: Sesión activa de SQLAlchemy.
        usuario: Instancia de UsuarioVisitante. Debe tener vector_preferencias
                 poblado desde el onboarding.
        limit: Número máximo de establecimientos a retornar.

    Returns:
        Lista de instancias Establecimiento para el cold start.
    """
    # TODO: Implementar consulta de establecimientos populares en el cluster provisional
    #       JOIN metrica_establecimiento ON id_establecimiento
    #       WHERE es_activo=TRUE AND estado='aprobado'
    #       ORDER BY metrica_establecimiento.popularidad_7d DESC
    #       LIMIT limit
    logger.info(
        "cold_start: generando recomendaciones para usuario_id=%d (perfil_completado=%s)",
        usuario.id_usuario,
        usuario.perfil_completado,
    )
    return []


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

    mejor_cluster_id: int | None = None
    menor_distancia: float = float("inf")

    for cluster in clusters:
        if not cluster.centroide:
            continue
        centroide: list = cluster.centroide
        if len(centroide) != len(vector_preferencias):
            continue
        distancia = math.sqrt(
            sum((a - b) ** 2 for a, b in zip(vector_preferencias, centroide))
        )
        if distancia < menor_distancia:
            menor_distancia = distancia
            mejor_cluster_id = cluster.id_cluster

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
    # TODO: Insertar fila en metrica_establecimiento con scores en 0.0
    #       y boost_informal = BOOST_FACTOR_INFORMAL si es_informal=TRUE
    logger.info(
        "cold_start: procesando establecimiento nuevo id=%d", id_establecimiento
    )
    return {"id_establecimiento": id_establecimiento, "status": "cold_start_applied"}
