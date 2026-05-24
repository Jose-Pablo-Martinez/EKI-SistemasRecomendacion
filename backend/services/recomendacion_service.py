"""
Módulo de Servicio: Recomendaciones (Online)
Responsable de procesar la lógica de negocio para entregar recomendaciones
a los usuarios en tiempo real, aplicando filtros de distancia geográfica (Haversine)
y gestionando estrategias de fallback (expansión de radio de búsqueda).
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.models import (
    UsuarioVisitante,
    UbicacionUsuario,
    RecomendacionGenerada
)
from backend.engine.ranking import compute_haversine_km

logger = logging.getLogger(__name__)

MIN_RESULTADOS_POR_CATEGORIA = 5


def _obtener_radio_base(db: Session, id_usuario: int) -> int:
    """Extrae el radio de búsqueda configurado por el usuario, con fallback a 5km."""
    visitante = db.get(UsuarioVisitante, id_usuario)
    return int(visitante.radio_busqueda_km) if visitante and visitante.radio_busqueda_km else 5  # type: ignore


def _obtener_ubicacion_reciente(db: Session, id_usuario: int) -> Optional[UbicacionUsuario]:
    """Obtiene el último registro de ubicación GPS del usuario."""
    stmt_ubicacion = (
        select(UbicacionUsuario)
        .where(UbicacionUsuario.id_usuario == id_usuario)
        .order_by(UbicacionUsuario.fecha_registro.desc())
        .limit(1)
    )
    return db.execute(stmt_ubicacion).scalar_one_or_none()


def _obtener_recomendaciones_crudas(db: Session, id_usuario: int) -> List[RecomendacionGenerada]:
    """Consulta la base de datos por recomendaciones vigentes (últimos 7 días)."""
    fecha_limite = datetime.now(timezone.utc) - timedelta(days=7)
    stmt_recs = (
        select(RecomendacionGenerada)
        .options(joinedload(RecomendacionGenerada.establecimiento))
        .where(
            RecomendacionGenerada.id_usuario == id_usuario,
            RecomendacionGenerada.fecha_generacion >= fecha_limite
        )
    )
    return list(db.scalars(stmt_recs).all())


def _agrupar_por_categoria(
    recs: List[RecomendacionGenerada]
) -> Dict[str, List[RecomendacionGenerada]]:
    """Agrupa una lista plana de recomendaciones en un diccionario por categoría."""
    agrupado: Dict[str, List[RecomendacionGenerada]] = {}
    for r in recs:
        cat = str(r.categoria_recomendacion)  # type: ignore
        if cat not in agrupado:
            agrupado[cat] = []
        agrupado[cat].append(r)
    return agrupado


def _calcular_distancias(
    recs: List[RecomendacionGenerada],
    ubicacion: UbicacionUsuario
) -> None:
    """Calcula la distancia Haversine in-place para cada recomendación."""
    for r in recs:
        estab = r.establecimiento
        if estab.latitud and estab.longitud:
            dist = compute_haversine_km(
                float(ubicacion.latitud), float(ubicacion.longitud),  # type: ignore
                float(estab.latitud), float(estab.longitud)  # type: ignore
            )
            r.distancia_km = dist  # type: ignore
        else:
            r.distancia_km = None  # type: ignore


def _aplicar_fallback_cascada(
    recs: List[RecomendacionGenerada],
    radio_base: int
) -> List[RecomendacionGenerada]:
    """
    Filtra los resultados expandiendo el radio en cascada hasta cumplir 
    con el mínimo de resultados por categoría.
    """
    # Nivel 0: Radio base
    recs_n0 = [r for r in recs if r.distancia_km is not None and r.distancia_km <= radio_base]
    if len(recs_n0) >= MIN_RESULTADOS_POR_CATEGORIA:
        for r in recs_n0:
            r.fallback_nivel = 0  # type: ignore
            r.radio_usado_km = radio_base  # type: ignore
        return sorted(recs_n0, key=lambda x: x.posicion)

    # Nivel 1: Radio doble
    radio_doble = radio_base * 2
    recs_n1 = [r for r in recs if r.distancia_km is not None and r.distancia_km <= radio_doble]
    if len(recs_n1) >= MIN_RESULTADOS_POR_CATEGORIA:
        for r in recs_n1:
            r.fallback_nivel = 1  # type: ignore
            r.radio_usado_km = radio_doble  # type: ignore
        return sorted(recs_n1, key=lambda x: x.posicion)

    # Nivel 2: Municipio completo
    for r in recs:
        r.fallback_nivel = 2  # type: ignore
        r.radio_usado_km = 99  # type: ignore
    return sorted(recs, key=lambda x: x.posicion)


def obtener_recomendaciones(db: Session, id_usuario: int) -> Dict[str, List[Any]]:
    """
    Orquestador principal: Obtiene las recomendaciones pre-generadas, 
    delega el cálculo de distancia geográfica y aplica la cascada de fallbacks.
    """
    radio_base = _obtener_radio_base(db, id_usuario)
    ubicacion = _obtener_ubicacion_reciente(db, id_usuario)
    recs_crudas = _obtener_recomendaciones_crudas(db, id_usuario)
    recs_por_categoria = _agrupar_por_categoria(recs_crudas)

    resultados_finales: Dict[str, List[RecomendacionGenerada]] = {}

    for categoria, recs in recs_por_categoria.items():
        if not ubicacion:
            # Sin ubicación GPS, forzamos nivel 2 (municipio completo) sin distancias
            for r in recs:
                r.fallback_nivel = 2  # type: ignore
                r.radio_usado_km = 99  # type: ignore
            resultados_finales[categoria] = sorted(recs, key=lambda x: x.posicion)
            continue

        _calcular_distancias(recs, ubicacion)
        resultados_finales[categoria] = _aplicar_fallback_cascada(recs, radio_base)

    db.commit()  # Persiste los cálculos de fallback/distancias
    return resultados_finales


def registrar_click(db: Session, id_recomendacion: int) -> bool:
    """Registra que una recomendación fue clickeada por el usuario."""
    recomendacion = db.get(RecomendacionGenerada, id_recomendacion)
    if not recomendacion:
        return False
    
    recomendacion.fue_clickeada = True  # type: ignore
    recomendacion.fecha_click = datetime.now(timezone.utc)  # type: ignore
    db.commit()
    return True
