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
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select

from backend.models import InteraccionUsuario, UsuarioVisitante

if TYPE_CHECKING:
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
    logger.info(
        "collab_filter: calculando scores item-to-item para usuario_id=%d cluster=%d",
        id_usuario,
        id_cluster,
    )
    if not candidatos:
        return []

    fecha_limite = datetime.utcnow() - timedelta(days=90)
    stmt = (
        select(
            InteraccionUsuario.id_usuario,
            InteraccionUsuario.id_establecimiento,
            InteraccionUsuario.peso_interaccion
        )
        .join(UsuarioVisitante, InteraccionUsuario.id_usuario == UsuarioVisitante.id_usuario)
        .where(
            UsuarioVisitante.id_cluster == id_cluster,
            InteraccionUsuario.fecha > fecha_limite
        )
    )
    rows = db.execute(stmt).all()

    if not rows:
        return []

    user_ids = sorted(list(set(r.id_usuario for r in rows)))
    estab_ids = sorted(list(set(r.id_establecimiento for r in rows)))
    
    user_idx = {uid: idx for idx, uid in enumerate(user_ids)}
    estab_idx = {eid: idx for idx, eid in enumerate(estab_ids)}

    rows_idx = []
    cols_idx = []
    data = []

    for r in rows:
        rows_idx.append(user_idx[r.id_usuario])
        cols_idx.append(estab_idx[r.id_establecimiento])
        data.append(float(r.peso_interaccion or 0.1))

    # Definición de la matriz dispersa
    matrix = csr_matrix((data, (rows_idx, cols_idx)), shape=(len(user_ids), len(estab_ids)))

    # Similitud coseno entre items (transponer matriz)
    item_sim = cosine_similarity(matrix.T)

    # Items visitados por el usuario
    user_items = {r.id_establecimiento for r in rows if r.id_usuario == id_usuario}

    scores = []
    for candidates in candidatos:
        cid = candidates.id_establecimiento
        if cid in user_items:
            continue
        if cid in estab_idx:
            c_idx = estab_idx[cid]
            sim_sum = sum(
                item_sim[estab_idx[ui], c_idx]
                for ui in user_items if ui in estab_idx
            )
            if sim_sum > 0:
                scores.append((candidates, float(sim_sum)))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:limit]


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

    # Usuarios que interactuaron con al menos uno de los establecimientos
    comunes = set(usuarios_a.keys()) | set(usuarios_b.keys())
    if not comunes:
        return 0.0

    vec_a = np.array([usuarios_a.get(u, 0.0) for u in comunes]).reshape(1, -1)
    vec_b = np.array([usuarios_b.get(u, 0.0) for u in comunes]).reshape(1, -1)

    return float(cosine_similarity(vec_a, vec_b)[0, 0])
