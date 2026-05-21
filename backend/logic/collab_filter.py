"""
Módulo de Filtrado Colaborativo — EKI.

Responsabilidad:
    Calcular scores colaborativos item-to-item dentro del cluster del usuario
    para generar recomendaciones de la categoría 'colaborativo_cluster'.

Método (ver §1.2 Fase 3 de EkiSystem_DB_Design.md):

    Enfoque: Item-Based Collaborative Filtering dentro del cluster.

    score_colaborativo = frecuencia_aparicion_en_listas_de_usuarios_similares
                         (acotado al id_cluster del usuario)

    Ventajas de Item-Based vs User-Based (ver §1.2):
    - Los establecimientos cambian menos que los usuarios → similitudes más estables.
    - Escala mejor con grandes volúmenes de usuarios.
    - El clustering reduce el espacio de búsqueda: solo se compara dentro del cluster.

    Señales usadas (tabla interaccion_usuario):
    - peso_interaccion pre-calculado al insertar (desnormalizado — ver §1.5):
        vista_detalle     = 0.1
        guardado_favorito = 0.5
        compartido        = 0.3
        llamada_telefono  = 0.6
        abrir_maps        = 0.7
        resena_dejada     = 1.0
        ruta_calculada    = 0.9

Nota arquitectónica (§1.7 — Offline-First):
    El score_colaborativo_base en metrica_establecimiento se calcula OFFLINE.
    El job offline construye la matriz de interacciones ponderada SOLO sobre
    los últimos 90 días (ver §6.2) y dentro del cluster del usuario.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # pyrefly: ignore [missing-import]
    from sqlalchemy.orm import Session
    from backend.models import Establecimiento, InteraccionUsuario, ClusterUsuario

logger = logging.getLogger(__name__)

# ─── Pesos de interacción (desnormalizados al insertar — ver §1.5) ────────────
PESOS_INTERACCION: dict[str, float] = {
    "vista_detalle":     0.1,
    "guardado_favorito": 0.5,
    "compartido":        0.3,
    "llamada_telefono":  0.6,
    "abrir_maps":        0.7,
    "resena_dejada":     1.0,
    "ruta_calculada":    0.9,
}


def get_collaborative_recommendations(
    db: "Session",
    id_usuario: int,
    id_cluster: int,
    candidatos: list["Establecimiento"],
    limit: int = 10,
) -> list[tuple["Establecimiento", float]]:
    """
    Genera recomendaciones de categoría 'colaborativo_cluster' (item-to-item).

    Estrategia:
        1. Obtener interacciones de usuarios del mismo cluster en los últimos 90 días.
        2. Construir la matriz de co-ocurrencia ponderada por peso_interaccion.
        3. Para cada establecimiento candidato, calcular el score como la suma
           de pesos de interacciones de usuarios similares del cluster.
        4. Excluir establecimientos que el usuario ya visitó.

    Args:
        db: Sesión activa de SQLAlchemy.
        id_usuario: ID del usuario para quien se generan las recomendaciones.
        id_cluster: Cluster al que pertenece el usuario (acota la búsqueda).
        candidatos: Lista de Establecimiento pre-filtrados por radio geográfico.
        limit: Número máximo de recomendaciones a retornar.

    Returns:
        Lista de tuplas (Establecimiento, score_colaborativo) ordenadas por score.
    """
    # TODO: Implementar consulta sobre interaccion_usuario con JOIN a usuario_visitante
    #       WHERE usuario_visitante.id_cluster = id_cluster
    #         AND interaccion_usuario.fecha > NOW() - INTERVAL 90 DAY
    #         AND interaccion_usuario.id_usuario != id_usuario
    #       GROUP BY id_establecimiento
    #       ORDER BY SUM(peso_interaccion) DESC
    logger.info(
        "collab_filter: calculando scores item-to-item para usuario_id=%d cluster=%d",
        id_usuario,
        id_cluster,
    )
    return []


def compute_peso_interaccion(tipo_interaccion: str) -> float:
    """
    Retorna el peso pre-definido para un tipo de interacción.

    Este peso se persiste en interaccion_usuario.peso_interaccion al insertar
    (desnormalizado — ver §1.5) para evitar recalcular en cada corrida del motor.

    Args:
        tipo_interaccion: Valor del ENUM tipo_interaccion.

    Returns:
        Peso en [0.0, 1.0]. Retorna 0.1 (mínimo) para tipos desconocidos.
    """
    return PESOS_INTERACCION.get(tipo_interaccion, 0.1)


def compute_item_similarity(
    id_estab_a: int,
    id_estab_b: int,
    interacciones: list["InteraccionUsuario"],
) -> float:
    """
    Calcula la similitud item-to-item entre dos establecimientos basada en
    co-ocurrencias ponderadas dentro del historial de interacciones del cluster.

    La similitud se define como la cosine similarity sobre el vector de pesos
    de interacción de los usuarios que interactuaron con ambos establecimientos.

    Args:
        id_estab_a: ID del primer establecimiento.
        id_estab_b: ID del segundo establecimiento.
        interacciones: Lista de InteraccionUsuario dentro del cluster y ventana de 90 días.

    Returns:
        Similitud en [0.0, 1.0].
    """
    import math

    # Construir vectores de usuarios para cada establecimiento
    usuarios_a: dict[int, float] = {}
    usuarios_b: dict[int, float] = {}

    for interaccion in interacciones:
        peso = float(interaccion.peso_interaccion or 0)
        if interaccion.id_establecimiento == id_estab_a:
            usuarios_a[interaccion.id_usuario] = (
                usuarios_a.get(interaccion.id_usuario, 0) + peso
            )
        elif interaccion.id_establecimiento == id_estab_b:
            usuarios_b[interaccion.id_usuario] = (
                usuarios_b.get(interaccion.id_usuario, 0) + peso
            )

    # Usuarios comunes (co-ocurrencias)
    comunes = set(usuarios_a.keys()) & set(usuarios_b.keys())
    if not comunes:
        return 0.0

    dot = sum(usuarios_a[u] * usuarios_b[u] for u in comunes)
    norm_a = math.sqrt(sum(v ** 2 for v in usuarios_a.values()))
    norm_b = math.sqrt(sum(v ** 2 for v in usuarios_b.values()))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)
