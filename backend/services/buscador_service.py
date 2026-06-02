"""
Módulo de Servicio: Buscador — EKI.

Responsabilidad:
    Orquestar las búsquedas de los usuarios, integrando la consulta SQL exacta
    con la lógica de corrección ortográfica (Similitud Léxica de Levenshtein)
    cuando no hay resultados, siguiendo el principio SOLID (SRP).

Componente 5 — Autocompletado y N-gramas:
    Pipeline de búsqueda en 3 capas:
      Capa 1: Búsqueda SQL exacta (LIKE) — sin cambios, O(1) en BD indexada.
      Capa 2: Prefijo (autocompletado) — O(P·log V) con bisect sobre lista ordenada.
      Capa 3: Fuzzy multicapa — N-grama pre-filtra top-15 candidatos, Levenshtein
              refina el ranking final. O(15·L²) en vez de O(V·L²).

Optimización del vocabulario enriquecido:
    El vocabulario se reconstruye una sola vez y se almacena en memoria con un TTL
    de 6 horas (VocabularioCache). Esto elimina el cuello de botella de ir a BD en
    cada query: la primera consulta es O(N_establecimientos + N_categorias + N_etiquetas),
    y las siguientes son O(1) hasta que el TTL expira.
    El vocabulario es una lista ordenada (invariante garantizado por VocabularioCache)
    para que prefix_match use búsqueda binaria.
"""

import logging
import time
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.establecimientos import Establecimiento
from backend.services.establecimiento_service import buscar_establecimientos
from backend.engine.lexical_filter import (
    levenshtein_similarity,
    ngram_similarity,
    prefix_match,
    normalize_text,
)

logger = logging.getLogger(__name__)

# Umbral mínimo de similitud para sugerir una corrección (0.0 a 1.0)
UMBRAL_SIMILITUD_MINIMA: float = 0.70

# Número de candidatos que pasan del pre-filtro N-grama al refinamiento Levenshtein.
# Reducir al mínimo necesario: Levenshtein es O(L²) por candidato.
TOP_CANDIDATOS_NGRAMA: int = 15

# Longitud mínima del prefijo para activar el autocompletado.
# Evita sugerir el vocabulario completo con prefijos de 1-2 caracteres.
MIN_PREFIJO_AUTOCOMPLETE: int = 2


# ─── Caché de Vocabulario en Memoria ────────────────────────────────────────
# Singleton a nivel de módulo: se comparte entre todos los workers del proceso
# dentro del mismo proceso de FastAPI/Uvicorn.
#
# Por qué no Redis:
#   El vocabulario es ~2000 palabras → ~50-200 KB de RAM. Para el tamaño actual
#   del proyecto (Render Free Tier, un solo proceso uvicorn), un dict de módulo
#   es suficiente y no agrega dependencias de infraestructura.
#
# Por qué TTL de 6 horas:
#   Los nombres de establecimientos cambian raramente. El job offline de recomendaciones
#   corre cada 8 horas, así que el vocabulario siempre estará fresco al momento
#   en que el motor genera nuevas recomendaciones.
#
# Coherencia multiworker (si en el futuro se escala a N workers uvicorn):
#   Cada worker tendría su propia copia del caché. El peor caso es que el primer
#   query en cada worker reconstruya el vocabulario una sola vez — aceptable.
# ────────────────────────────────────────────────────────────────────────────

TTL_VOCABULARIO_SEGUNDOS: int = 6 * 3600  # 6 horas

_vocabulario_cache: list[str] = []       # Lista ORDENADA de palabras normalizadas
_vocabulario_ts: float = 0.0             # Timestamp UNIX de la última construcción


def _necesita_rebuild() -> bool:
    """Retorna True si el caché está vacío o su TTL expiró."""
    return not _vocabulario_cache or (time.monotonic() - _vocabulario_ts) > TTL_VOCABULARIO_SEGUNDOS


def _construir_vocabulario(db: Session) -> None:
    """
    Reconstruye el vocabulario enriquecido y lo almacena en el caché de módulo.

    Fuentes incluidas (vocabulario enriquecido vs. implementación anterior):
      - Nombres de establecimientos aprobados.
      - Nombres de categorías (para buscar 'mariscos', 'tacos', 'yucateca'...).
      - Nombres de etiquetas (para buscar 'economico', 'wifi', 'familiar'...).

    Todas las palabras se normalizan (sin tildes, minúsculas) y se almacenan
    en una lista ORDENADA para que prefix_match pueda usar búsqueda binaria.

    El invariante de orden es responsabilidad exclusiva de esta función.
    """
    global _vocabulario_cache, _vocabulario_ts

    vocabulario_raw: set[str] = set()

    # ── Fuente 1: nombres de establecimientos ──────────────────────────────
    stmt_nombres = select(Establecimiento.nombre).where(
        Establecimiento.estado == "aprobado"
    )
    nombres = db.scalars(stmt_nombres).all()
    for nombre in nombres:
        for token in normalize_text(nombre).split():
            if len(token) > 2:
                vocabulario_raw.add(token)

    # Fuente 2: categorías — solo las que usan establecimientos activos y aprobados
    try:
        from backend.models.catalogo import Categoria
        from backend.models.establecimientos import EstablecimientoCategoria
        stmt_cats = (
            select(Categoria.nombre)
            .join(EstablecimientoCategoria, EstablecimientoCategoria.id_categoria == Categoria.id_categoria)
            .join(Establecimiento, Establecimiento.id_establecimiento == EstablecimientoCategoria.id_establecimiento)
            .where(
                Establecimiento.es_activo == True,
                Establecimiento.estado == "aprobado",
            )
            .distinct()
        )
        cats = db.scalars(stmt_cats).all()
        for nombre in cats:
            for token in normalize_text(nombre).split():
                if len(token) > 2:
                    vocabulario_raw.add(token)
    except Exception:
        logger.debug("buscador_service: categorías no disponibles para vocabulario")

    # Fuente 3: etiquetas — solo las que usan establecimientos activos y aprobados
    try:
        from backend.models.catalogo import Etiqueta
        from backend.models.establecimientos import EstablecimientoEtiqueta
        stmt_etiqs = (
            select(Etiqueta.nombre)
            .join(EstablecimientoEtiqueta, EstablecimientoEtiqueta.id_etiqueta == Etiqueta.id_etiqueta)
            .join(Establecimiento, Establecimiento.id_establecimiento == EstablecimientoEtiqueta.id_establecimiento)
            .where(
                Establecimiento.es_activo == True,
                Establecimiento.estado == "aprobado",
            )
            .distinct()
        )
        etiqs = db.scalars(stmt_etiqs).all()
        for nombre in etiqs:
            for token in normalize_text(nombre).split():
                if len(token) > 2:
                    vocabulario_raw.add(token)
    except Exception:
        logger.debug("buscador_service: etiquetas no disponibles para vocabulario")

    # Ordenar antes de almacenar — invariante requerido por prefix_match (bisect)
    _vocabulario_cache = sorted(vocabulario_raw)
    _vocabulario_ts = time.monotonic()
    logger.info(
        "buscador_service: vocabulario enriquecido reconstruido (%d palabras)",
        len(_vocabulario_cache),
    )


def _obtener_vocabulario(db: Session) -> list[str]:
    """
    Retorna el vocabulario desde el caché (O(1)) o lo reconstruye si el TTL expiró.
    Este es el punto de entrada centralizado para toda lógica que necesite el vocabulario.
    """
    if _necesita_rebuild():
        _construir_vocabulario(db)
    return _vocabulario_cache


def invalidar_vocabulario() -> None:
    """
    Invalida el caché de vocabulario para forzar una reconstrucción en el próximo query.
    Llamar desde el job offline de recomendaciones cuando se aprueban nuevos establecimientos.
    """
    global _vocabulario_ts
    _vocabulario_ts = 0.0
    logger.info("buscador_service: caché de vocabulario invalidado manualmente")


# Pipeline de búsqueda en 3 capas

def buscar_con_correccion(
    db: Session,
    query: Optional[str] = None,
    id_categoria: Optional[int] = None,
    id_colonia: Optional[int] = None,
    tipo_establecimiento: Optional[str] = None,
) -> dict:
    """
    Pipeline de búsqueda en 3 capas con tolerancia a errores y autocompletado.

    Capa 1 — Búsqueda SQL exacta (LIKE):
        Sin cambios respecto a la implementación anterior. Si hay resultados,
        retorna inmediatamente sin tocar el vocabulario.

    Capa 2 — Autocompletado por prefijo:
        Si la búsqueda exacta falla y la query tiene al menos MIN_PREFIJO_AUTOCOMPLETE
        caracteres, busca en el vocabulario ordenado con bisect (O(P·log V)).
        Si hay coincidencias de prefijo, re-lanza la búsqueda SQL con el primer match.

    Capa 3 — Corrección fuzzy (N-grama + Levenshtein):
        Pre-filtra los TOP_CANDIDATOS_NGRAMA mejores candidatos con n-gramas Jaccard
        (O(V·L/n)), luego refina con Levenshtein (O(15·L²)) sobre ese subconjunto.
        Mucho más eficiente que correr Levenshtein sobre todo el vocabulario O(V·L²).

    Args:
        db:                   Sesión activa de SQLAlchemy.
        query:                Texto de búsqueda libre del usuario.
        id_categoria:         Filtro por categoría (pasa directo a buscar_establecimientos).
        id_colonia:           Filtro por colonia (pasa directo a buscar_establecimientos).
        tipo_establecimiento: Filtro por tipo (pasa directo a buscar_establecimientos).

    Returns:
        Diccionario compatible con el esquema BusquedaResponse:
        {
            "resultados": [...],
            "sugerencia_correccion": "texto corregido" | None
        }
    """
    # Capa 1: Búsqueda SQL exacta 
    resultados = buscar_establecimientos(
        db=db,
        query=query,
        id_categoria=id_categoria,
        id_colonia=id_colonia,
        tipo_establecimiento=tipo_establecimiento,
    )

    if resultados or not query:
        return {"resultados": resultados, "sugerencia_correccion": None}

    # A partir de aquí: hay query de texto pero 0 resultados exactos.
    vocabulario = _obtener_vocabulario(db)
    query_normalizada = normalize_text(query)
    palabras_query = [p for p in query_normalizada.split() if p]

    if not palabras_query:
        return {"resultados": [], "sugerencia_correccion": None}

    # Capa 2: Prefijo (autocompletado)
    # Solo se activa para queries largas suficientes para evitar falsos positivos.
    if len(query_normalizada) >= MIN_PREFIJO_AUTOCOMPLETE:
        # Busca con el prefijo de la query completa normalizada (sin espacios)
        # y con el prefijo de la primera palabra (más común en mobile)
        prefijo_completo = query_normalizada.replace(" ", "")
        prefijos_candidatos = prefix_match(prefijo_completo, vocabulario, limit=5)
        if not prefijos_candidatos:
            prefijos_candidatos = prefix_match(palabras_query[0], vocabulario, limit=5)

        if prefijos_candidatos:
            resultados_prefijo = buscar_establecimientos(
                db=db,
                query=prefijos_candidatos[0],
                id_categoria=id_categoria,
                id_colonia=id_colonia,
                tipo_establecimiento=tipo_establecimiento,
            )
            if resultados_prefijo:
                return {
                    "resultados": resultados_prefijo,
                    "sugerencia_correccion": prefijos_candidatos[0],
                }

    # Capa 3: Fuzzy multicapa (N-grama → Levenshtein) 
    # Estrategia: corregir cada palabra del query por separado y reensamblar.
    palabras_corregidas: list[str] = []

    for palabra in palabras_query:
        if len(palabra) <= 2:
            # Palabras muy cortas (artículos, preposiciones): no corregir
            palabras_corregidas.append(palabra)
            continue

        # Paso A: Pre-filtro rápido con N-gramas — reduce V a ~15 candidatos
        candidatos_ngrama = sorted(
            vocabulario,
            key=lambda v: ngram_similarity(palabra, v),
            reverse=True,
        )[:TOP_CANDIDATOS_NGRAMA]

        if not candidatos_ngrama:
            palabras_corregidas.append(palabra)
            continue

        # Paso B: Refinamiento con Levenshtein sobre los top candidatos
        mejor_candidato = max(
            candidatos_ngrama,
            key=lambda c: levenshtein_similarity(palabra, c),
        )
        sim = levenshtein_similarity(palabra, mejor_candidato)

        palabras_corregidas.append(
            mejor_candidato if sim >= UMBRAL_SIMILITUD_MINIMA else palabra
        )

    sugerencia_final = " ".join(palabras_corregidas)

    # Solo sugerimos si la corrección es distinta a lo que el usuario escribió
    if sugerencia_final != query_normalizada:
        return {"resultados": [], "sugerencia_correccion": sugerencia_final}

    return {"resultados": [], "sugerencia_correccion": None}


def autocompletar(db: Session, prefijo: str, limit: int = 5) -> list[str]:
    """
    Endpoint de autocompletado en tiempo real.

    Retorna palabras del vocabulario enriquecido que comienzan con el prefijo dado.
    Usa el caché en memoria (O(1) si el TTL no expiró) y búsqueda binaria (O(log V)).

    Args:
        db:      Sesión activa de SQLAlchemy (solo se usa si el caché expiró).
        prefijo: Texto que el usuario está escribiendo.
        limit:   Número máximo de sugerencias a retornar.

    Returns:
        Lista de hasta `limit` palabras sugeridas, en orden alfabético.
    """
    if len(prefijo) < MIN_PREFIJO_AUTOCOMPLETE:
        return []
    vocabulario = _obtener_vocabulario(db)
    prefijo_normalizado = normalize_text(prefijo)
    return prefix_match(prefijo_normalizado, vocabulario, limit=limit)
