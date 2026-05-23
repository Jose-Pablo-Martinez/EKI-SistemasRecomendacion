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

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

if TYPE_CHECKING:
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
    logger.info(
        "content_filter: calculando similitud coseno para usuario_id=%d, candidatos=%d",
        usuario.id_usuario,
        len(candidatos),
    )
    
    if not usuario.vector_preferencias or not candidatos:
        return []

    valid_candidatos = [c for c in candidatos if c.vector_caracteristicas]
    if not valid_candidatos:
        return []

    user_vec = np.array(usuario.vector_preferencias).reshape(1, -1)
    cand_vecs = np.array([c.vector_caracteristicas for c in valid_candidatos])

    scores = cosine_similarity(user_vec, cand_vecs).flatten()
    top_indices = np.argsort(-scores)[:limit]

    return [(valid_candidatos[i], float(scores[i])) for i in top_indices]


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

    user_vec = np.array(vector_a).reshape(1, -1)
    item_vec = np.array(vector_b).reshape(1, -1)
    
    return float(cosine_similarity(user_vec, item_vec)[0, 0])


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
        "calificacion_promedio": float(establecimiento.calificacion_promedio or 0),  # type: ignore
    }

def calcular_diversity_score(candidato_vec: list[float], lista_vecs: list[list[float]]) -> float:
    """
    Calcula el diversity score: 1 - avg(cosine_similarity con los demás items de la lista).
    
    Args:
        candidato_vec: Vector de características del candidato.
        lista_vecs: Lista de vectores de los establecimientos ya seleccionados.
        
    Returns:
        Diversity score en [0.0, 1.0].
    """
    if not lista_vecs:
        return 1.0
        
    sims = cosine_similarity(
        np.array(candidato_vec).reshape(1, -1),
        np.array(lista_vecs)
    )
    return 1.0 - float(np.mean(sims))
