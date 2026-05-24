import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.models import (
    UsuarioVisitante,
    UbicacionUsuario,
    RecomendacionGenerada,
    Establecimiento
)
from backend.engine.ranking import compute_haversine_km

logger = logging.getLogger(__name__)

MIN_RESULTADOS_POR_CATEGORIA = 5

def obtener_recomendaciones(db: Session, id_usuario: int) -> Dict[str, List[Any]]:
    """
    Obtiene las recomendaciones pre-generadas para el usuario, aplicando
    filtrado por distancia exacto en tiempo real (Haversine) y lógica de
    fallback en cascada.
    """
    # 1. Obtener radio de búsqueda del usuario
    visitante = db.get(UsuarioVisitante, id_usuario)
    radio_base = visitante.radio_busqueda_km if visitante and visitante.radio_busqueda_km else 5

    # 2. Obtener ubicación más reciente
    stmt_ubicacion = (
        select(UbicacionUsuario)
        .where(UbicacionUsuario.id_usuario == id_usuario)
        .order_by(UbicacionUsuario.fecha_registro.desc())
        .limit(1)
    )
    ubicacion = db.execute(stmt_ubicacion).scalar_one_or_none()

    # 3. Leer recomendaciones vigentes
    # Consideramos vigentes las de los últimos 7 días
    fecha_limite = datetime.now(timezone.utc) - timedelta(days=7)
    stmt_recs = (
        select(RecomendacionGenerada)
        .options(joinedload(RecomendacionGenerada.establecimiento))
        .where(
            RecomendacionGenerada.id_usuario == id_usuario,
            RecomendacionGenerada.fecha_generacion >= fecha_limite
        )
    )
    recomendaciones_crudas = list(db.scalars(stmt_recs).all())

    # Agrupar por categoría
    recs_por_categoria: Dict[str, List[RecomendacionGenerada]] = {}
    for r in recomendaciones_crudas:
        cat = str(r.categoria_recomendacion)  # type: ignore
        if cat not in recs_por_categoria:
            recs_por_categoria[cat] = []
        recs_por_categoria[cat].append(r)

    resultados_finales: Dict[str, List[RecomendacionGenerada]] = {}

    for categoria, recs in recs_por_categoria.items():
        # Si no hay ubicación, retornamos todo sin fallback ni cálculo de distancia
        if not ubicacion:
            for r in recs:
                r.fallback_nivel = 2  # type: ignore
                r.radio_usado_km = 99  # type: ignore
            resultados_finales[categoria] = sorted(recs, key=lambda x: x.posicion)
            continue

        # 4. Calcular distancia_km para todas las recomendaciones de esta categoría
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

        # 5. Lógica de Fallback en cascada
        # Nivel 0: Radio base
        recs_n0 = [r for r in recs if r.distancia_km is not None and r.distancia_km <= radio_base]
        
        if len(recs_n0) >= MIN_RESULTADOS_POR_CATEGORIA:
            for r in recs_n0:
                r.fallback_nivel = 0  # type: ignore
                r.radio_usado_km = radio_base  # type: ignore
            resultados_finales[categoria] = sorted(recs_n0, key=lambda x: x.posicion)
            continue

        # Nivel 1: Radio doble
        radio_doble = radio_base * 2
        recs_n1 = [r for r in recs if r.distancia_km is not None and r.distancia_km <= radio_doble]
        
        if len(recs_n1) >= MIN_RESULTADOS_POR_CATEGORIA:
            for r in recs_n1:
                r.fallback_nivel = 1  # type: ignore
                r.radio_usado_km = radio_doble  # type: ignore
            resultados_finales[categoria] = sorted(recs_n1, key=lambda x: x.posicion)
            continue

        # Nivel 2: Municipio completo (sin límite de distancia real)
        for r in recs:
            r.fallback_nivel = 2  # type: ignore
            r.radio_usado_km = 99  # type: ignore
        resultados_finales[categoria] = sorted(recs, key=lambda x: x.posicion)

    # Persistir los cambios calculados (distancia_km, fallback_nivel, radio_usado_km)
    db.commit()

    return resultados_finales

def registrar_click(db: Session, id_recomendacion: int) -> bool:
    """Registra que una recomendación fue clickeada."""
    recomendacion = db.get(RecomendacionGenerada, id_recomendacion)
    if not recomendacion:
        return False
    
    recomendacion.fue_clickeada = True  # type: ignore
    recomendacion.fecha_click = datetime.now(timezone.utc)  # type: ignore
    db.commit()
    return True
