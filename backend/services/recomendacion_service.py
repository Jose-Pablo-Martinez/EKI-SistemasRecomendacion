"""
Módulo de Servicio: Recomendaciones (Online)
Responsable de procesar la lógica de negocio para entregar recomendaciones
a los usuarios en tiempo real, aplicando filtros de distancia geográfica (Haversine)
y gestionando estrategias de fallback (expansión de radio de búsqueda).
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.models import (
    UsuarioVisitante,
    UbicacionUsuario,
    RecomendacionGenerada
)
from backend.engine.ranking import compute_haversine_km

logger = logging.getLogger(__name__)

MIN_RESULTADOS_POR_CATEGORIA = 10
# 7 secciones = top_picks_hibrido + preferencia_contenido + colaborativo_cluster
#             + popularidad_zona + tendencia_informal + descubrimiento + (cold_start si aplica)
MAX_SECCIONES_FEED = 7
MAX_ITEMS_POR_SECCION = 20

_SECCIONES_ALGORITMO_ORDEN = [
    "top_picks_hibrido",
    "preferencia_contenido",
    "colaborativo_cluster",
    "popularidad_zona",
    "tendencia_informal",
    "descubrimiento",
    "cold_start",
    "cercania",
]

_SECCIONES_ALGORITMO_TITULO = {
    "top_picks_hibrido": "Mejores selecciones para ti",
    "preferencia_contenido": "Basado en tus gustos",
    "colaborativo_cluster": "Personas como tu visitaron",
    "popularidad_zona": "Populares cerca de ti",
    "tendencia_informal": "Apoya el comercio local",
    "descubrimiento": "Descubrimientos recientes",
    "cold_start": "Populares de la semana",
    "cercania": "Cerca de ti",
}


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
    from backend.models.establecimientos import Establecimiento, EstablecimientoCategoria
    from backend.models.interacciones import Resena
    from sqlalchemy.orm import selectinload
    
    fecha_limite = datetime.now(timezone.utc) - timedelta(days=7)
    stmt_recs = (
        select(RecomendacionGenerada)
        .options(
            joinedload(RecomendacionGenerada.establecimiento).options(
                selectinload(Establecimiento.resenas).selectinload(Resena.usuario),
                selectinload(Establecimiento.platillos),
                selectinload(Establecimiento.horarios),
                selectinload(Establecimiento.imagenes),
                selectinload(Establecimiento.categorias).selectinload(
                    EstablecimientoCategoria.categoria
                ),
            )
        )
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
        
        # Truco para separar los híbridos sin necesidad de modificar el ENUM de la base de datos
        if cat == "preferencia_contenido" and str(r.estrategia_usada) == "hibrido":
            cat = "top_picks_hibrido"
            
        if cat not in agrupado:
            agrupado[cat] = []
        agrupado[cat].append(r)
    
    # Deduplicar: el mismo establecimiento puede aparecer en registros de distintos runs
    # (los clickeados sobreviven 30 días). Nos quedamos con el más reciente por establecimiento.
    for cat in agrupado:
        vistos: Dict[int, RecomendacionGenerada] = {}
        for r in sorted(agrupado[cat], key=lambda x: x.fecha_generacion, reverse=True):
            estab_id = int(r.id_establecimiento)  # type: ignore
            if estab_id not in vistos:
                vistos[estab_id] = r
        agrupado[cat] = sorted(vistos.values(), key=lambda x: x.posicion)
    
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
    Filtra los resultados estrictamente por el radio base configurado por el usuario.
    Se eliminó la cascada para respetar la decisión del usuario en el frontend.
    """
    recs_n0 = [r for r in recs if r.distancia_km is not None and r.distancia_km <= radio_base]
    for r in recs_n0:
        r.fallback_nivel = 0  # type: ignore
        r.radio_usado_km = radio_base  # type: ignore
    return sorted(recs_n0, key=lambda x: x.posicion)


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

    # Nota: No hacemos db.commit() aquí para evitar N queries de UPDATE síncronas 
    # por cada petición GET, lo cual volvía inusable el feed.
    return resultados_finales


def _flatten(recs_por_categoria: Dict[str, List[RecomendacionGenerada]]) -> Iterable[RecomendacionGenerada]:
    for items in recs_por_categoria.values():
        for r in items:
            yield r


def _secciones_por_categoria(
    recs_por_categoria: Dict[str, List[RecomendacionGenerada]],
    max_secciones: int,
    max_items: int,
) -> List[Dict[str, Any]]:
    cat_map: Dict[str, List[RecomendacionGenerada]] = {}
    for r in _flatten(recs_por_categoria):
        estab = r.establecimiento
        if not estab or not getattr(estab, "categorias", None):
            continue
        for ec in estab.categorias:
            cat = ec.categoria.nombre if ec.categoria else None
            if not cat:
                continue
            cat_map.setdefault(cat, []).append(r)

    secciones: List[Dict[str, Any]] = []
    for cat, items in sorted(cat_map.items(), key=lambda x: len(x[1]), reverse=True):
        if len(secciones) >= max_secciones:
            break
        vistos = set()
        filtrados: List[RecomendacionGenerada] = []
        for r in items:
            if r.id_recomendacion in vistos:
                continue
            vistos.add(r.id_recomendacion)
            filtrados.append(r)
            if len(filtrados) >= max_items:
                break
        if filtrados:
            secciones.append({
                "key": f"categoria:{cat}",
                "title": cat,
                "kind": "categoria",
                "items": filtrados,
            })
    return secciones


def obtener_recomendaciones_secciones(db: Session, id_usuario: int) -> List[Dict[str, Any]]:
    """Devuelve el feed organizado en carruseles mixtos (algoritmo + categoria)."""
    recs_por_categoria = obtener_recomendaciones(db, id_usuario)

    # Detectar si el usuario solo tiene cold_start (usuario nuevo sin jobs offline)
    categorias_presentes = set(recs_por_categoria.keys())
    solo_cold_start = categorias_presentes == {"cold_start"} or (
        categorias_presentes <= {"cold_start", "popularidad_zona", "tendencia_informal", "descubrimiento"}
        and "cold_start" in categorias_presentes
    )

    secciones: List[Dict[str, Any]] = []

    if solo_cold_start:
        # Para usuarios 100% nuevos, no intentamos inventar carruseles por categoría.
        # Simplemente mostramos las recomendaciones bajo un título amigable.
        items = recs_por_categoria.get("cold_start") or []
        if items:
            secciones.append({
                "key": "cold_start",
                "title": "Selecciones para empezar",
                "kind": "algoritmo",
                "items": items[:MAX_ITEMS_POR_SECCION],
            })
    else:
        # Para usuarios con ML: solo secciones de algoritmo, sin duplicar por categoría
        for key in _SECCIONES_ALGORITMO_ORDEN:
            if key == "cold_start":
                continue  # No mezclar cold_start con secciones ML
            items = recs_por_categoria.get(key) or []
            if not items:
                continue
            secciones.append({
                "key": key,
                "title": _SECCIONES_ALGORITMO_TITULO.get(key, key),
                "kind": "algoritmo",
                "items": items[:MAX_ITEMS_POR_SECCION],
            })
            if len(secciones) >= MAX_SECCIONES_FEED:
                break

    return secciones


def registrar_click(db: Session, id_recomendacion: int) -> bool:
    """Registra que una recomendación fue clickeada por el usuario."""
    recomendacion = db.get(RecomendacionGenerada, id_recomendacion)
    if not recomendacion:
        return False
    
    recomendacion.fue_clickeada = True  # type: ignore
    recomendacion.fecha_click = datetime.now(timezone.utc)  # type: ignore
    db.commit()
    return True
