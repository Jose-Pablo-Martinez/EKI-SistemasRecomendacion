"""
Módulo de Filtrado Basado en Contenido — EKI.

Responsabilidad:
    Calcular la similitud entre el perfil del usuario y las características
    de los establecimientos para generar recomendaciones de la categoría
    'preferencia_contenido'.

Método (ver §1.2 Fase 3 de EkiSystem_DB_Design.md):

    score_contenido = similitud_coseno(
        vector_preferencias (usuario_visitante),
        vector_caracteristicas (establecimiento)
    )

    Ambos vectores son JSON numéricos de la misma dimensión:
    - vector_preferencias: pesos por categoría + rango de precio tolerado
      (construido en el onboarding y actualizado con cada interacción significativa)
    - vector_caracteristicas: categorías del establecimiento, precio promedio,
      etiquetas, es_informal (construido al crear el establecimiento y actualizado
      por el job offline K-Means)

Nota arquitectónica (§1.7 — Offline-First):
    El score_contenido_base en metrica_establecimiento es el PROMEDIO de
    similitudes coseno de todos los usuarios que visitaron el establecimiento,
    calculado OFFLINE. El score individual por usuario se calcula en el job
    offline al generar la lista de recomendacion_generada, NO en el request.
"""

import logging
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # pyrefly: ignore [missing-import]
    from sqlalchemy.orm import Session
    from backend.models import Establecimiento, UsuarioVisitante

logger = logging.getLogger(__name__)


def get_content_based_recommendations(
    db: "Session",
    usuario: "UsuarioVisitante",
    candidatos: list["Establecimiento"],
    limit: int = 10,
) -> list[tuple["Establecimiento", float]]:
    """
    Genera recomendaciones de categoría 'preferencia_contenido' para un usuario.

    Estrategia:
        1. Obtener vector_preferencias del usuario.
        2. Para cada establecimiento candidato, calcular similitud_coseno con
           su vector_caracteristicas.
        3. Retornar los N con mayor score, ordenados descendentemente.

    Args:
        db: Sesión activa de SQLAlchemy.
        usuario: Instancia UsuarioVisitante con vector_preferencias poblado.
        candidatos: Lista de Establecimiento pre-filtrados por radio geográfico.
        limit: Número máximo de recomendaciones a retornar.

    Returns:
        Lista de tuplas (Establecimiento, score_contenido) ordenadas por score.
    """
    # TODO: Implementar consulta de candidatos y cálculo de similitud coseno
    #       con vector_preferencias del usuario
    logger.info(
        "content_filter: calculando similitud coseno para usuario_id=%d, candidatos=%d",
        usuario.id_usuario,
        len(candidatos),
    )
    return []


def compute_cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    """
    Calcula la similitud coseno entre dos vectores numéricos.

    Usada para comparar vector_preferencias (usuario) con vector_caracteristicas
    (establecimiento). Ambos vectores deben tener la misma dimensión.

    Args:
        vector_a: Vector del usuario (vector_preferencias).
        vector_b: Vector del establecimiento (vector_caracteristicas).

    Returns:
        Similitud en [0.0, 1.0]. Retorna 0.0 si algún vector es nulo o vacío.
    """
    if not vector_a or not vector_b or len(vector_a) != len(vector_b):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = math.sqrt(sum(a ** 2 for a in vector_a))
    norm_b = math.sqrt(sum(b ** 2 for b in vector_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def build_establecimiento_profile(establecimiento: "Establecimiento") -> dict:
    """
    Extrae el perfil de contenido de un establecimiento.

    Retorna el vector_caracteristicas y metadatos relevantes para el motor.
    Si vector_caracteristicas es NULL (establecimiento nuevo sin job K-Means),
    retorna un diccionario vacío y el motor usará cold_start.

    Args:
        establecimiento: Instancia del modelo Establecimiento.

    Returns:
        Diccionario con el vector_caracteristicas y campos de contexto.
    """
    return {
        "id_establecimiento": establecimiento.id_establecimiento,
        "vector": establecimiento.vector_caracteristicas or [],
        "es_informal": establecimiento.es_informal,
        "tipo": establecimiento.tipo_establecimiento,
        "calificacion_promedio": float(establecimiento.calificacion_promedio or 0),
    }
