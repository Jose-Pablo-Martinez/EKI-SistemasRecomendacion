"""
Job Offline: Clustering (K-Means)

Este módulo se encarga de ejecutar el algoritmo K-Means para agrupar usuarios y 
establecimientos en clusters basados en sus vectores de características/preferencias.
Calcula automáticamente el número óptimo de clusters (K) usando el Silhouette Score.

Cumple con el Principio de Responsabilidad Única (SRP) al dedicarse exclusivamente
a la lógica de agrupación y persistencia de sus resultados en la base de datos.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Tuple

import numpy as np
from sqlalchemy.orm import Session
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from backend.models.usuarios import UsuarioVisitante
from backend.models.establecimientos import Establecimiento
from backend.models.clusters import ClusterUsuario, ClusterEstablecimiento

logger = logging.getLogger(__name__)

# Rango de K a evaluar para el Silhouette Score
RANGO_K_USUARIOS = (3, 10)
RANGO_K_ESTABLECIMIENTOS = (3, 10)
DIAS_INACTIVIDAD = 30

def obtener_vectores_usuarios(db: Session) -> Tuple[List[UsuarioVisitante], np.ndarray]:
    """
    Obtiene los usuarios activos y extrae sus vectores de preferencias.
    
    Retorna:
        Una tupla con la lista de usuarios y un arreglo NumPy de vectores.
    """
    fecha_limite = datetime.now(timezone.utc) - timedelta(days=DIAS_INACTIVIDAD)
    
    # Filtramos usuarios que tengan vector de preferencias y hayan estado activos recientemente
    usuarios = db.query(UsuarioVisitante).filter(
        UsuarioVisitante.vector_preferencias.is_not(None),
        UsuarioVisitante.fecha_ultima_actividad >= fecha_limite
    ).all()
    
    vectores = [u.vector_preferencias for u in usuarios]
    return usuarios, np.array(vectores)

def obtener_vectores_establecimientos(db: Session) -> Tuple[List[Establecimiento], np.ndarray]:
    """
    Obtiene los establecimientos activos y extrae sus vectores de características.
    
    Retorna:
        Una tupla con la lista de establecimientos y un arreglo NumPy de vectores.
    """
    establecimientos = db.query(Establecimiento).filter(
        Establecimiento.vector_caracteristicas.is_not(None),
        Establecimiento.es_activo == True,
        Establecimiento.estado == 'aprobado'
    ).all()
    
    vectores = [e.vector_caracteristicas for e in establecimientos]
    return establecimientos, np.array(vectores)

def buscar_mejor_k(X: np.ndarray, rango_k: Tuple[int, int]) -> int:
    """
    Evalúa diferentes valores de K y retorna el que tiene el mejor Silhouette Score.
    """
    min_k, max_k = rango_k
    # K no puede ser mayor o igual al número de muestras
    max_k = min(max_k, len(X) - 1)
    
    if max_k <= min_k:
        return min_k  # Retorna el mínimo posible si no hay suficientes datos
        
    mejor_k = min_k
    mejor_score = -1.0
    
    for k in range(min_k, max_k + 1):
        km = KMeans(n_clusters=k, random_state=42, n_init='auto')
        labels = km.fit_predict(X)
        score = silhouette_score(X, labels)
        
        if score > mejor_score:
            mejor_k = k
            mejor_score = score
            
    logger.info("Mejor K encontrado: %d con Silhouette Score: %.4f", mejor_k, mejor_score)
    return mejor_k

def procesar_clustering_usuarios(db: Session) -> None:
    """
    Calcula los clusters de usuarios, selecciona el mejor K y persiste 
    tanto los centroides en ClusterUsuario como las asignaciones en UsuarioVisitante.
    """
    usuarios, X = obtener_vectores_usuarios(db)
    
    if len(X) < RANGO_K_USUARIOS[0]:
        logger.warning("Insuficientes usuarios para clustering (%d). Se requiere mínimo %d.", len(X), RANGO_K_USUARIOS[0])
        return

    mejor_k = buscar_mejor_k(X, RANGO_K_USUARIOS)
    
    km = KMeans(n_clusters=mejor_k, random_state=42, n_init='auto')
    labels = km.fit_predict(X)
    centroides = km.cluster_centers_.tolist()
    
    # Obtener o crear entidades ClusterUsuario en BD
    clusters_db = db.query(ClusterUsuario).order_by(ClusterUsuario.id_cluster).all()
    
    # Aseguramos que existan al menos 'mejor_k' clusters en la BD
    if len(clusters_db) < mejor_k:
        for i in range(len(clusters_db), mejor_k):
            nuevo_cluster = ClusterUsuario(nombre_cluster=f"Cluster U{i+1}")
            db.add(nuevo_cluster)
        db.flush() # Ejecutar INSERTs pendientes para obtener IDs generados
        clusters_db = db.query(ClusterUsuario).order_by(ClusterUsuario.id_cluster).all()

    ahora = datetime.now(timezone.utc)
    k_final = mejor_k
    
    # Actualizamos los centroides y total_usuarios de los primeros 'mejor_k' clusters
    for i in range(mejor_k):
        total_en_cluster = int(np.sum(labels == i))
        cluster_actual = clusters_db[i]
        cluster_actual.centroide = centroides[i]
        cluster_actual.total_usuarios = int(total_en_cluster) # type: ignore
        cluster_actual.fecha_actualizacion = ahora # type: ignore
        
    # 5. Resetear a cero los clusters que quedaron vacíos en esta corrida
    for i in range(k_final, len(clusters_db)):
        clusters_db[i].total_usuarios = 0 # type: ignore
        clusters_db[i].fecha_actualizacion = ahora # type: ignore

    # Mapeo de etiqueta kmeans (0 a mejor_k-1) -> id_cluster en BD
    id_por_etiqueta = {i: clusters_db[i].id_cluster for i in range(mejor_k)}

    # Asignar a cada usuario su nuevo id_cluster
    for idx, usuario in enumerate(usuarios):
        usuario.id_cluster = id_por_etiqueta[labels[idx]]
        
    logger.info("Clustering de usuarios completado exitosamente.")

def procesar_clustering_establecimientos(db: Session) -> None:
    """
    Calcula los clusters de establecimientos, selecciona el mejor K y persiste 
    los centroides en ClusterEstablecimiento y asignaciones en Establecimiento.
    """
    establecimientos, X = obtener_vectores_establecimientos(db)
    
    if len(X) < RANGO_K_ESTABLECIMIENTOS[0]:
        logger.warning("Insuficientes establecimientos (%d). Se requiere mínimo %d.", len(X), RANGO_K_ESTABLECIMIENTOS[0])
        return

    mejor_k = buscar_mejor_k(X, RANGO_K_ESTABLECIMIENTOS)
    
    km = KMeans(n_clusters=mejor_k, random_state=42, n_init='auto')
    labels = km.fit_predict(X)
    centroides = km.cluster_centers_.tolist()
    
    clusters_db = db.query(ClusterEstablecimiento).order_by(ClusterEstablecimiento.id_cluster).all()
    
    if len(clusters_db) < mejor_k:
        for i in range(len(clusters_db), mejor_k):
            nuevo_cluster = ClusterEstablecimiento(nombre_cluster=f"Cluster E{i+1}")
            db.add(nuevo_cluster)
        db.flush()
        clusters_db = db.query(ClusterEstablecimiento).order_by(ClusterEstablecimiento.id_cluster).all()

    ahora = datetime.now(timezone.utc)
    k_final = mejor_k
    for i in range(mejor_k):
        total_en_cluster = int(np.sum(labels == i))
        cluster_actual = clusters_db[i]
        cluster_actual.centroide = centroides[i]
        cluster_actual.total_establecimientos = int(total_en_cluster) # type: ignore
        cluster_actual.fecha_actualizacion = ahora # type: ignore
        
    # 5. Resetear a cero los clusters sobrantes
    for i in range(k_final, len(clusters_db)):
        clusters_db[i].total_establecimientos = 0 # type: ignore
        clusters_db[i].fecha_actualizacion = ahora # type: ignore

    id_por_etiqueta = {i: clusters_db[i].id_cluster for i in range(mejor_k)}

    for idx, estab in enumerate(establecimientos):
        estab.id_cluster = id_por_etiqueta[labels[idx]]
        
    logger.info("Clustering de establecimientos completado exitosamente.")

def ejecutar_clustering(db: Session) -> None:
    """
    Función orquestadora principal llamada por el orquestador (runner.py).
    
    Agrupa en la misma transacción (commit atómico) la actualización
    de usuarios y establecimientos para evitar inconsistencias si una falla.
    """
    try:
        procesar_clustering_usuarios(db)
        procesar_clustering_establecimientos(db)
        db.commit()
        logger.info("Transacción de clustering confirmada (commit) en base de datos.")
    except Exception as e:
        db.rollback()
        logger.error("Error durante el clustering. Transacción revertida (rollback): %s", e)
        raise e
