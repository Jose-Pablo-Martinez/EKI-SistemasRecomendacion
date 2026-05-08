"""
Módulo de Filtrado Colaborativo — EKI.

Responsabilidad:
    Calcular la similitud entre usuarios o ítems basada en el historial
    de interacciones (calificaciones) para generar recomendaciones
    del tipo "usuarios similares también calificaron bien...".
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # pyrefly: ignore [missing-import]
    from sqlalchemy.orm import Session
    from models import Vendor

logger = logging.getLogger(__name__)


def get_collaborative_recommendations(
    db: "Session",
    user_id: int,
    limit: int = 10,
) -> list["Vendor"]:
    """
    Genera recomendaciones mediante filtrado colaborativo (user-based o item-based).

    Estrategia base:
        1. Obtener los usuarios más similares al usuario objetivo.
        2. Identificar vendedores bien calificados por esos usuarios similares
           que el usuario objetivo aún no haya visitado.
        3. Retornar los vendedores con mayor puntuación colaborativa.

    Args:
        db: Sesión activa de SQLAlchemy.
        user_id: Identificador del usuario para quien se generan las recomendaciones.
        limit: Número máximo de vendedores a retornar.

    Returns:
        Lista de instancias Vendor ordenadas por puntuación colaborativa.
    """
    # TODO: Implementar similitud coseno o Pearson entre usuarios
    logger.info("collab_filter: generando recomendaciones para usuario %d", user_id)
    return []


def compute_user_similarity(user_a_id: int, user_b_id: int, db: "Session") -> float:
    """
    Calcula el coeficiente de similitud entre dos usuarios basándose
    en sus calificaciones compartidas.

    Args:
        user_a_id: ID del primer usuario.
        user_b_id: ID del segundo usuario.
        db: Sesión activa de SQLAlchemy.

    Returns:
        Valor de similitud entre 0.0 (ninguna) y 1.0 (idénticos).
    """
    # TODO: Implementar similitud coseno sobre la matriz usuario-ítem
    return 0.0
