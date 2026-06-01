"""
Módulo de Similitud Léxica — EKI.

Responsabilidad:
    Proveer métricas matemáticas de similitud de cadenas de texto (strings).
    Se utiliza principalmente para la corrección ortográfica (tolerancia a errores)
    en el motor de búsqueda, implementando la Distancia de Levenshtein.

Componente 5 — Autocompletado y N-gramas:
    Dos algoritmos complementarios al Levenshtein:
    - prefix_match: autocompletado en tiempo real (O(P·log V) con lista ordenada).
    - ngram_similarity: similitud basada en bigramas Jaccard, más rápido que
      Levenshtein para pre-filtrar candidatos antes del refinamiento final.
    - normalize_text: normaliza unicode/tildes para que 'Taqueria' == 'Taquería'.

Este módulo cumple el Principio de Responsabilidad Única (SRP): no interactúa
con la base de datos ni con SQLAlchemy, solo realiza cálculos matemáticos puros.
"""

import unicodedata
import bisect

def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calcula el número mínimo de operaciones (inserciones, eliminaciones, sustituciones)
    necesarias para transformar la cadena s1 en la cadena s2.
    
    Implementación mediante Programación Dinámica (Matriz DP) para máxima eficiencia.
    
    Args:
        s1: Primera cadena de texto.
        s2: Segunda cadena de texto.
        
    Returns:
        Entero representando la distancia absoluta (0 = idénticos).
    """
    s1 = s1.lower().strip()
    s2 = s2.lower().strip()
    
    m, n = len(s1), len(s2)
    # Matriz de (m+1) x (n+1)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
        
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,       # Eliminación
                dp[i][j - 1] + 1,       # Inserción
                dp[i - 1][j - 1] + cost # Sustitución
            )
            
    return dp[m][n]


def levenshtein_similarity(s1: str, s2: str) -> float:
    """
    Convierte la distancia de Levenshtein en un coeficiente de similitud entre 0.0 y 1.0.
    
    Fórmula: Similitud = 1 - (Distancia / max(longitud(s1), longitud(s2)))
    
    Args:
        s1: Primera cadena de texto.
        s2: Segunda cadena de texto.
        
    Returns:
        Flotante entre 0.0 (completamente diferentes) y 1.0 (exactamente iguales).
    """
    # Si ambas son vacías, son idénticas.
    if not s1.strip() and not s2.strip():
        return 1.0
        
    dist = levenshtein_distance(s1, s2)
    max_len = max(len(s1.strip()), len(s2.strip()))
    
    if max_len == 0:
        return 1.0
        
    return 1.0 - (dist / max_len)


# Nuevas funciones (N-gramas + Prefijos)

def normalize_text(text: str) -> str:
    """
    Normaliza un texto a ASCII sin tildes ni caracteres especiales.
    Esto permite que 'Taquería' == 'Taqueria' y 'é' == 'e' en búsquedas.

    Usa NFD (descomposición canónica) para separar el carácter base del diacrítico,
    luego filtra los diacríticos (categoría 'Mn' = Mark, Non-Spacing).

    Args:
        text: Texto a normalizar.

    Returns:
        Texto en minúsculas sin tildes, solo alfanumérico + espacios.
    """
    nfd = unicodedata.normalize("NFD", text.lower())
    sin_tildes = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    return "".join(c for c in sin_tildes if c.isalnum() or c == " ").strip()


def ngram_similarity(s1: str, s2: str, n: int = 2) -> float:
    """
    Similitud basada en bigramas compartidos (Jaccard sobre n-gramas).

    Más rápido que Levenshtein para pre-filtrar candidatos: O(L/n) por cadena
    en lugar de O(L²). Se usa como primer filtro para reducir el conjunto de
    candidatos antes del refinamiento con Levenshtein.

    Ejemplo:
        ngram_similarity('taco', 'taco') = 1.0
        ngram_similarity('tacos', 'taco') = 0.75  (3 bigramas comunes de 4)
        ngram_similarity('takos', 'tacos') = 0.5

    Args:
        s1: Primera cadena (ya normalizada).
        s2: Segunda cadena (ya normalizada).
        n:  Longitud de los n-gramas. 2 (bigramas) es el mejor balance.

    Returns:
        Flotante en [0.0, 1.0]. 1.0 = idéntico, 0.0 = sin n-gramas en común.
    """
    s1 = s1.lower().strip()
    s2 = s2.lower().strip()
    if not s1 or not s2:
        return 0.0

    # Cadenas muy cortas: caen fuera del rango de bigramas, usar similitud directa
    if len(s1) < n or len(s2) < n:
        return 1.0 if s1 == s2 else 0.0

    grams1 = set(s1[i:i + n] for i in range(len(s1) - n + 1))
    grams2 = set(s2[i:i + n] for i in range(len(s2) - n + 1))

    intersection = grams1 & grams2
    union = grams1 | grams2
    return len(intersection) / len(union)  # Jaccard


def prefix_match(prefix: str, vocabulario_ordenado: list[str], limit: int = 10) -> list[str]:
    """
    Retorna palabras del vocabulario que comienzan con el prefijo dado.

    Usa búsqueda binaria (bisect) sobre la lista ordenada para localizar el punto
    de inserción del prefijo en O(log V), luego avanza linealmente solo mientras
    los elementos sigan teniendo ese prefijo: O(P·log V) total vs O(V) con un bucle.

    Requisito: `vocabulario_ordenado` debe estar ORDENADO alfabéticamente.
    El VocabularioCache en buscador_service.py garantiza este invariante.

    Args:
        prefix:              Prefijo ya normalizado (sin tildes, minúsculas).
        vocabulario_ordenado: Lista de palabras ordenadas.
        limit:               Máximo de sugerencias a retornar.

    Returns:
        Lista de hasta `limit` palabras que empiezan con el prefijo, en orden.
    """
    if not prefix or not vocabulario_ordenado:
        return []

    # bisect_left: encuentra el índice de inserción del prefijo
    idx = bisect.bisect_left(vocabulario_ordenado, prefix)
    resultados: list[str] = []
    while idx < len(vocabulario_ordenado) and len(resultados) < limit:
        palabra = vocabulario_ordenado[idx]
        if not palabra.startswith(prefix):
            break
        resultados.append(palabra)
        idx += 1
    return resultados
