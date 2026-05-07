"""
Módulo de Filtrado Basado en Contenido — EKI.

Responsabilidad:
    Analizar las características del vendedor (categoría, ubicación, tags)
    y el perfil del usuario para generar recomendaciones personalizadas
    sin depender del historial de interacciones de otros usuarios.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from models import Vendor, User

logger = logging.getLogger(__name__)


def get_content_based_recommendations(
    db: "Session",
    user_id: int,
    limit: int = 10,
) -> list["Vendor"]:
    """
    Genera recomendaciones basadas en el perfil de contenido del usuario.

    Estrategia base:
        1. Obtener las categorías preferidas del usuario a partir de su historial.
        2. Filtrar vendedores activos que coincidan con esas categorías.
        3. Ordenar por rating_avg descendente como criterio secundario.

    Args:
        db: Sesión activa de SQLAlchemy.
        user_id: Identificador del usuario para quien se generan las recomendaciones.
        limit: Número máximo de vendedores a retornar.

    Returns:
        Lista de instancias Vendor ordenadas por relevancia de contenido.
    """
    # TODO: Implementar lógica de similitud por contenido
    logger.info("content_filter: generando recomendaciones para usuario %d", user_id)
    return []


def build_vendor_profile(vendor: "Vendor") -> dict:
    """
    Construye un vector de características del vendedor para el cálculo de similitud.

    Args:
        vendor: Instancia del modelo Vendor.

    Returns:
        Diccionario con las características relevantes del vendedor.
    """
    # TODO: Implementar extracción de features (categoría, ubicación, tags)
    return {
        "vendor_id": vendor.vendor_id,
        "category": vendor.category,
        "location": vendor.location,
    }
