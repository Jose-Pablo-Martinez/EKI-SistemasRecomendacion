"""
Dominio: CLUSTERS (ML)
Centroides K-Means para usuarios y establecimientos.
Son datos de configuración del modelo ML — no se truncan con --modo limpiar.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import relationship

from backend.database import Base


class ClusterUsuario(Base):
    """
    Clusters de usuarios generados por K-Means offline.
    centroide: vector numérico para asignar nuevos usuarios por distancia euclidiana.
    total_usuarios: desnormalizado — ver §1.5.
    """
    __tablename__ = "cluster_usuario"

    id_cluster          = Column(Integer, primary_key=True, autoincrement=True)
    nombre_cluster      = Column(String(100), nullable=True)
    centroide           = Column(JSON, nullable=True)
    descripcion         = Column(Text, nullable=True)
    total_usuarios      = Column(Integer, default=0)
    fecha_actualizacion = Column(DateTime, nullable=True)

    # Relaciones
    usuarios = relationship("UsuarioVisitante", back_populates="cluster")


class ClusterEstablecimiento(Base):
    """
    Clusters de establecimientos generados por K-Means offline.
    centroide: vector de características (categorías, precio, etiquetas, es_informal).
    total_establecimientos: desnormalizado — ver §1.5.
    """
    __tablename__ = "cluster_establecimiento"

    id_cluster             = Column(Integer, primary_key=True, autoincrement=True)
    nombre_cluster         = Column(String(100), nullable=True)
    centroide              = Column(JSON, nullable=True)
    descripcion            = Column(Text, nullable=True)
    total_establecimientos = Column(Integer, default=0)
    fecha_actualizacion    = Column(DateTime, nullable=True)

    # Relaciones
    establecimientos = relationship("Establecimiento", back_populates="cluster")
