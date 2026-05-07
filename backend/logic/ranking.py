"""
Módulo de Ranking y Boosting — EKI.

Responsabilidad:
    Aplicar factores de visibilidad a vendedores con pocas reseñas
    y ordenar los resultados finales del sistema de recomendación.

Regla de boosting (según CONTRIBUTING.md):
    Un vendedor recibe boost si review_count < BOOST_THRESHOLD.
    El factor se controla con la constante BOOST_FACTOR.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from models import Vendor

logger = logging.getLogger(__name__)

# ─── Constantes de Boosting ───────────────────────────────────────────────────
BOOST_THRESHOLD: int = 50       # Número mínimo de reseñas para no aplicar boost
BOOST_FACTOR: float = 1.25      # Multiplicador de relevancia para vendedores con pocas reseñas
MAX_RESULTS: int = 20           # Límite máximo de resultados en cualquier endpoint


def get_top_vendors(
    db: "Session",
    limit: int = 10,
) -> list["Vendor"]:
    """
    Obtiene los vendedores con mayor puntaje de relevancia tras aplicar boosting.

    Combina el rating promedio con el factor de boosting para priorizar
    negocios emergentes con pocas reseñas.

    Args:
        db: Sesión activa de SQLAlchemy.
        limit: Cantidad máxima de vendedores a retornar (máx. MAX_RESULTS).

    Returns:
        Lista de instancias Vendor ordenadas por puntaje de relevancia descendente.
    """
    # TODO: Consultar vendors activos y aplicar apply_boost
    logger.info("ranking: obteniendo top %d vendedores con boosting", limit)
    return []


def apply_boost(vendors: list, threshold: int = BOOST_THRESHOLD) -> list:
    """
    Aplica el factor de boosting a los vendedores con pocas reseñas.

    Un vendedor con review_count < threshold recibe su rating_avg
    multiplicado por BOOST_FACTOR para aumentar su visibilidad en el ranking.

    Args:
        vendors: Lista de instancias Vendor a procesar.
        threshold: Umbral de reseñas. Vendedores por debajo reciben boost.

    Returns:
        Lista de vendedores con sus puntajes ajustados, lista para ordenar.
    """
    # TODO: Implementar lógica de boosting y retornar lista con scores calculados
    boosted: list = []
    for vendor in vendors:
        score: float = vendor.rating_avg
        if vendor.review_count < threshold:
            score *= BOOST_FACTOR
            logger.debug(
                "Boost aplicado a vendor_id=%d (reseñas: %d, score ajustado: %.2f)",
                vendor.vendor_id,
                vendor.review_count,
                score,
            )
        boosted.append({"vendor": vendor, "score": score, "boosted": vendor.review_count < threshold})
    return sorted(boosted, key=lambda x: x["score"], reverse=True)
