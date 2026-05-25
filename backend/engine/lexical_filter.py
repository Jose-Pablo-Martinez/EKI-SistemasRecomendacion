"""
Módulo de Similitud Léxica — EKI.

Responsabilidad:
    Proveer métricas matemáticas de similitud de cadenas de texto (strings).
    Se utiliza principalmente para la corrección ortográfica (tolerancia a errores)
    en el motor de búsqueda, implementando la Distancia de Levenshtein.

Este módulo cumple el Principio de Responsabilidad Única (SRP): no interactúa
con la base de datos ni con SQLAlchemy, solo realiza cálculos matemáticos puros.
"""

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
