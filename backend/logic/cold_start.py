"""
Módulo de Inicio en Frío (Cold Start) — EKI.

Responsabilidad:
    Proveer recomendaciones para dos escenarios de inicio en frío:
    1. Usuario nuevo: sin historial de interacciones previas.
    2. Vendedor nuevo: recién registrado, sin calificaciones.

    En estos casos, el filtrado colaborativo y por contenido no tienen
    suficiente información, por lo que se aplican estrategias alternativas.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from models import Vendor

logger = logging.getLogger(__name__)

# ─── Constantes de Estrategia Cold Start ──────────────────────────────────────
DEFAULT_CATEGORIES: list[str] = ["Tacos", "Antojitos", "Bebidas"]   # Categorías populares por defecto
COLD_START_LIMIT: int = 10                                           # Resultados para usuarios nuevos


def get_cold_start_recommendations(
    db: "Session",
    limit: int = COLD_START_LIMIT,
) -> list["Vendor"]:
    """
    Genera recomendaciones para un usuario nuevo sin historial.

    Estrategia:
        Retornar los vendedores más populares (por rating_avg y review_count)
        en las categorías más frecuentes del sistema, aplicando boosting
        a negocios emergentes.

    Args:
        db: Sesión activa de SQLAlchemy.
        limit: Número máximo de vendedores a retornar.

    Returns:
        Lista de instancias Vendor representativas para un nuevo usuario.
    """
    # TODO: Consultar los vendedores más populares por categorías predeterminadas
    logger.info("cold_start: generando recomendaciones para usuario nuevo (limit=%d)", limit)
    return []


def handle_new_vendor(vendor_id: int, db: "Session") -> dict:
    """
    Aplica la estrategia de visibilidad para un vendedor recién registrado.

    Un vendedor nuevo no tiene calificaciones, así que se le asigna un
    puntaje base y se registra para recibir boosting automático hasta
    alcanzar el BOOST_THRESHOLD definido en ranking.py.

    Args:
        vendor_id: ID del vendedor recién registrado.
        db: Sesión activa de SQLAlchemy.

    Returns:
        Diccionario con la información de visibilidad inicial asignada.
    """
    # TODO: Implementar registro y asignación de puntaje base para vendor nuevo
    logger.info("cold_start: procesando vendor nuevo vendor_id=%d", vendor_id)
    return {"vendor_id": vendor_id, "status": "cold_start_applied", "initial_boost": True}
