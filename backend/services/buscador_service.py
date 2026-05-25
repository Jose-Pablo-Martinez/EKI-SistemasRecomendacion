"""
Módulo de Servicio: Buscador — EKI.

Responsabilidad:
    Orquestar las búsquedas de los usuarios, integrando la consulta SQL exacta
    con la lógica de corrección ortográfica (Similitud Léxica de Levenshtein)
    cuando no hay resultados, siguiendo el principio SOLID (SRP).
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.models.establecimientos import Establecimiento
from backend.services.establecimiento_service import buscar_establecimientos
from backend.engine.lexical_filter import levenshtein_similarity

# Umbral mínimo de similitud para sugerir una corrección (0.0 a 1.0)
# 0.70 significa que la palabra debe ser al menos 70% idéntica.
UMBRAL_SIMILITUD_MINIMA = 0.70

def _obtener_vocabulario_establecimientos(db: Session) -> set[str]:
    """
    Extrae un diccionario de palabras únicas a partir de los nombres
    de los establecimientos activos.
    En un entorno real de altísima concurrencia, esto se almacenaría en Redis.
    Para el tamaño actual, una consulta rápida en memoria es muy eficiente.
    """
    stmt = select(Establecimiento.nombre).where(
        Establecimiento.estado == 'aprobado'
    )
    nombres = db.scalars(stmt).all()
    
    vocabulario = set()
    for nombre in nombres:
        # Separar por espacios para analizar palabras sueltas
        palabras = nombre.lower().split()
        for p in palabras:
            # Limpiar signos de puntuación básicos
            p_limpia = ''.join(c for c in p if c.isalnum())
            if len(p_limpia) > 2: # Ignorar conectores cortos (el, la, de)
                vocabulario.add(p_limpia)
                
    return vocabulario

def buscar_con_correccion(
    db: Session, 
    query: Optional[str] = None, 
    id_categoria: Optional[int] = None, 
    id_colonia: Optional[int] = None,
    tipo_establecimiento: Optional[str] = None
) -> dict:
    """
    Realiza una búsqueda estándar y, si no encuentra resultados y existe un query de texto,
    aplica el algoritmo de Levenshtein para sugerir una corrección.
    
    Returns:
        Diccionario compatible con el esquema BusquedaResponse.
    """
    # 1. Intentar la búsqueda exacta (comportamiento estándar)
    resultados = buscar_establecimientos(
        db=db, 
        query=query, 
        id_categoria=id_categoria, 
        id_colonia=id_colonia,
        tipo_establecimiento=tipo_establecimiento
    )
    
    # Si hay resultados, o si no buscaron por texto, regresar normal sin sugerencias
    if resultados or not query:
        return {
            "resultados": resultados,
            "sugerencia_correccion": None
        }
        
    # 2. Si llegamos aquí: Hay un query de texto pero 0 resultados exactos.
    # Aplicar Filtro Léxico (Levenshtein) para sugerir corrección.
    vocabulario = _obtener_vocabulario_establecimientos(db)
    query_limpio = ''.join(c for c in query.lower() if c.isalnum())
    
    # Manejar query con múltiples palabras dividiéndolas y buscando la mejor aproximación global
    # (Para el MVP nos enfocaremos en corregir la palabra más representativa o asumiendo búsquedas cortas)
    
    mejor_similitud = 0.0
    mejor_sugerencia = None
    
    # Analizamos la distancia de la query contra todo el vocabulario
    for palabra in vocabulario:
        sim = levenshtein_similarity(query_limpio, palabra)
        if sim > mejor_similitud:
            mejor_similitud = sim
            mejor_sugerencia = palabra
            
    # Solo sugerimos si estamos matemáticamente confiados (supera el umbral)
    if mejor_similitud >= UMBRAL_SIMILITUD_MINIMA:
        # Se podría optar por volver a lanzar buscar_establecimientos(query=mejor_sugerencia)
        # para devolver resultados corregidos automáticamente, pero respetar el esquema de sugerencias
        # es más transparente para el usuario final ("Quizás quisiste decir...")
        return {
            "resultados": [],
            "sugerencia_correccion": mejor_sugerencia
        }
        
    # Si ni siquiera con Levenshtein se acercó a algo lógico
    return {
        "resultados": [],
        "sugerencia_correccion": None
    }
