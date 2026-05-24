"""
Módulo de Ranking y Boosting — EKI.

Responsabilidad:
    Aplicar el score_boost_combinado a los establecimientos candidatos y
    ordenar los resultados finales del motor de recomendación.

Fórmula de boosting (Implementación basada en EkiSystem_DB_Design.md):

    score_boost = w_prox * (1 / (distancia_km + 0.1))
                + w_informal * es_informal
                + w_zona * popularidad_zona

    score_final = w1 * score_contenido + w2 * score_colaborativo + w3 * score_boost

Nota arquitectónica (§1.7 — Offline-First):
    El score_boost_combinado se pre-calcula en el job offline y se persiste en
    metrica_establecimiento. FastAPI NO recalcula la fórmula completa en cada
    request; solo calcula la distancia Haversine puntual al momento de servir.
"""

import logging
from typing import TYPE_CHECKING

import numpy as np
from sqlalchemy import select

from backend.models import Establecimiento, MetricaEstablecimiento

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ─── Constantes de Boosting ───────────────────────────────────────────────────
BOOST_FACTOR_INFORMAL: float = 0.25    # Bonus fijo para puestos informales (es_informal=TRUE)
RADIO_ZONA_KM: float = 2.0             # Radio en km para calcular popularidad_zona
MAX_RESULTS: int = 20                  # Límite máximo de resultados en cualquier endpoint

# Pesos del score final híbrido (deben sumar 1.0)
W_CONTENIDO: float = 0.40
W_COLABORATIVO: float = 0.35
W_BOOST: float = 0.25


def get_top_establecimientos(
    db: "Session",
    limit: int = 10,
) -> list["Establecimiento"]:
    """
    Obtiene los establecimientos con mayor score_boost_combinado pre-calculado.

    Este método solo se usa como fallback cuando no hay lista pre-generada
    para el usuario. El caso principal es que el job offline ya generó las
    recomendaciones en recomendacion_generada y FastAPI solo las sirve.

    Args:
        db: Sesión activa de SQLAlchemy.
        limit: Cantidad máxima de establecimientos a retornar (máx. MAX_RESULTS).

    Returns:
        Lista de instancias Establecimiento ordenadas por score_boost_combinado.
    """
    limit = min(limit, MAX_RESULTS)
    stmt = (
        select(Establecimiento)
        .join(MetricaEstablecimiento, Establecimiento.id_establecimiento == MetricaEstablecimiento.id_establecimiento)
        .where(
            Establecimiento.es_activo == True,
            Establecimiento.estado == "aprobado"
        )
        .order_by(MetricaEstablecimiento.score_boost_combinado.desc().nulls_last())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def compute_score_final(
    score_contenido: float,
    score_colaborativo: float,
    score_boost: float,
    w1: float = W_CONTENIDO,
    w2: float = W_COLABORATIVO,
    w3: float = W_BOOST,
) -> float:
    """
    Calcula el score final ponderado del motor híbrido.

    score_final = w1 * score_contenido + w2 * score_colaborativo + w3 * score_boost

    Args:
        score_contenido: Similitud coseno entre vector_preferencias del usuario
                         y vector_caracteristicas del establecimiento.
        score_colaborativo: Frecuencia de aparición en listas de usuarios similares
                            dentro del cluster (item-to-item).
        score_boost: score_boost_combinado pre-calculado de metrica_establecimiento
                     (Haversine + bonus informal + popularidad_zona).
        w1, w2, w3: Pesos de cada componente (deben sumar 1.0).

    Returns:
        Score final en [0.0, 1.0].
    """
    # TODO: Implementar cuando se construyan los endpoints de recomendaciones
    return w1 * score_contenido + w2 * score_colaborativo + w3 * score_boost


def compute_haversine_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """
    Calcula la distancia en km entre dos puntos geográficos con la fórmula de Haversine.

    Esta función se ejecuta ONLINE (en el request del usuario), a diferencia del
    score_boost_combinado que es OFFLINE. Ver §1.7 del diseño.

    El resultado se persiste en recomendacion_generada.distancia_km para la caja blanca.
    El "+0.1" en el denominador del boosting evita división por cero — ver §1.3.

    Args:
        lat1, lon1: Coordenadas del usuario (de ubicacion_usuario más reciente).
        lat2, lon2: Coordenadas del establecimiento (establecimiento.latitud/longitud).

    Returns:
        Distancia en kilómetros (línea recta).
    """
    R = 6371.0  # Radio de la Tierra en km

    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)

    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    res = R * c
    if isinstance(res, np.ndarray):
        return res  # type: ignore
    return float(res)
