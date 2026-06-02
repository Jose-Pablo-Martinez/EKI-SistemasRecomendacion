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
           su vector_caracteristicas. El resultado nativo de sklearn está en [-1.0, 1.0].
        3. Filtrar candidatos con score < 0: un score negativo indica gustos
           OPUESTOS al perfil del usuario — no se deben recomendar.
        4. Retornar los N con mayor score entre los positivos, ordenados
           descendentemente.

    Args:
        db: Sesión activa de SQLAlchemy.
        usuario: Instancia UsuarioVisitante con vector_preferencias poblado.
        candidatos: Lista de Establecimiento pre-filtrados por radio geográfico.
        limit: Número máximo de recomendaciones a retornar.

    Returns:
        Lista de tuplas (Establecimiento, score_contenido) ordenadas por score.
        Solo incluye establecimientos con score_contenido >= 0.0.
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

    user_vec_raw = usuario.vector_preferencias
    if isinstance(user_vec_raw, dict) and "numerico" in user_vec_raw:
        user_vec_raw = user_vec_raw["numerico"]
        
    if not isinstance(user_vec_raw, list):
        return []
        
    cand_dim = len(valid_candidatos[0].vector_caracteristicas) # type: ignore
    
    # Asegurar homogeneidad dimensional (en caso de vectores legados o corruptos)
    if len(user_vec_raw) < cand_dim:
        user_vec_raw = user_vec_raw + [0.0] * (cand_dim - len(user_vec_raw))
    elif len(user_vec_raw) > cand_dim:
        user_vec_raw = user_vec_raw[:cand_dim]
        
    user_vec = np.array(user_vec_raw).reshape(1, -1)
    cand_vecs = np.array([c.vector_caracteristicas for c in valid_candidatos])

    scores = cosine_similarity(user_vec, cand_vecs).flatten()

    # Filtrar scores negativos: indican gustos opuestos al perfil del usuario.
    # Un establecimiento con score coseno < 0 no debe aparecer como recomendación.
    positive_mask = scores >= 0.0
    positive_candidatos = [c for c, keep in zip(valid_candidatos, positive_mask) if keep]
    positive_scores = scores[positive_mask]

    if len(positive_scores) == 0:
        return []

    top_indices = np.argsort(-positive_scores)[:limit]
    return [(positive_candidatos[i], float(positive_scores[i])) for i in top_indices]


def compute_cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    """
    Calcula la similitud coseno entre dos vectores numéricos.

    Usada para comparar vector_preferencias (usuario) con vector_caracteristicas
    (establecimiento). Ambos vectores deben tener la misma dimensión.

    Args:
        vector_a: Vector del usuario (vector_preferencias).
        vector_b: Vector del establecimiento (vector_caracteristicas).

    Returns:
        Similitud en [-1.0, 1.0]. Retorna 0.0 si algún vector es nulo o vacío.
        Un valor negativo indica vectores opuestos (gustos contrarios al perfil).
        Un valor de 0.0 indica ortogonalidad (sin correlación).
        Un valor de 1.0 indica vectores idénticos (afinidad perfecta).
    """
    if not vector_a or not vector_b:
        return 0.0
        
    vec_a_raw = vector_a
    if isinstance(vec_a_raw, dict) and "numerico" in vec_a_raw:
        vec_a_raw = vec_a_raw["numerico"]
        
    if len(vec_a_raw) != len(vector_b):
        return 0.0

    user_vec = np.array(vec_a_raw).reshape(1, -1)
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


def obtener_descubrimientos(
    db: "Session",
    usuario: "UsuarioVisitante",
    candidatos_seleccionados: list["Establecimiento"],
    limit: int = 10,
) -> list[tuple["Establecimiento", float]]:
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
    import logging as _logging
    from typing import cast
    from backend.models import Establecimiento
    from backend.models.interacciones import InteraccionUsuario
    from sqlalchemy import select

    _log = _logging.getLogger(__name__)

    # Subquery para excluir establecimientos con los que el usuario ya ha interactuado (reseñas, favoritos, etc.)
    stmt_interactuados = select(InteraccionUsuario.id_establecimiento).where(
        InteraccionUsuario.id_usuario == usuario.id_usuario
    )

    filtros = [
        Establecimiento.es_activo == True,
        Establecimiento.estado == "aprobado",
        Establecimiento.es_informal == False,
        Establecimiento.id_establecimiento.notin_(stmt_interactuados),
    ]
    if usuario.id_cluster is not None:
        filtros.append(Establecimiento.id_cluster != usuario.id_cluster)

    candidatos_otros = db.query(Establecimiento).filter(*filtros).all()

    if not candidatos_otros:
        _log.warning(
            "content_filter: sin candidatos cross-cluster para descubrimiento (usuario_id=%d) — usando recientes",
            usuario.id_usuario,
        )
        return [
            (e, 0.5)
            for e in db.query(Establecimiento)
            .filter(
                Establecimiento.es_activo == True,
                Establecimiento.estado == "aprobado",
                Establecimiento.es_informal == False,
                Establecimiento.id_establecimiento.notin_(stmt_interactuados),
            )
            .order_by(Establecimiento.fecha_registro.desc())
            .limit(limit)
            .all()
        ]

    vecs_seleccionados = cast(list[list[float]], [
        e.vector_caracteristicas
        for e in candidatos_seleccionados
        if e.vector_caracteristicas
    ])

    scored = []
    for estab in candidatos_otros:
        if not estab.vector_caracteristicas:
            continue
        div_score = (
            calcular_diversity_score(
                cast(list[float], estab.vector_caracteristicas),
                vecs_seleccionados,
            )
            if vecs_seleccionados
            else 0.5
        )
        scored.append((estab, div_score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit]
