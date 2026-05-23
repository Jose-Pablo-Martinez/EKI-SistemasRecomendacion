"""
Dominio: GEOGRAFÍA
Tablas base sin dependencias externas. Se definen primero.
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy import CHAR, ForeignKey
from sqlalchemy.orm import relationship

from backend.database import Base


class Pais(Base):
    """
    Catálogo de países. PK: código ISO 3166-1 alpha-2 (ej. 'MX', 'US').
    Seed inicial: 'MX' — México.
    """
    __tablename__ = "pais"

    id_pais = Column(CHAR(2), primary_key=True)
    nombre  = Column(String(100), nullable=False)

    # Relaciones
    estados = relationship("EstadoGeo", back_populates="pais")


class EstadoGeo(Base):
    """
    Estados / provincias geográficas.
    Nombre 'estado_geo' para evitar colisión con el campo ENUM 'estado'
    que existe en múltiples tablas — ver §1.4 del diseño.
    """
    __tablename__ = "estado_geo"

    id_estado = Column(Integer, primary_key=True, autoincrement=True)
    id_pais   = Column(CHAR(2), ForeignKey("pais.id_pais"), nullable=False)
    nombre    = Column(String(100), nullable=False)

    # Relaciones
    pais       = relationship("Pais", back_populates="estados")
    municipios = relationship("Municipio", back_populates="estado_geo")


class Municipio(Base):
    """Municipios, vinculados a su estado geográfico."""
    __tablename__ = "municipio"

    id_municipio = Column(Integer, primary_key=True, autoincrement=True)
    id_estado    = Column(Integer, ForeignKey("estado_geo.id_estado"), nullable=False)
    nombre       = Column(String(100), nullable=False)

    # Relaciones
    estado_geo = relationship("EstadoGeo", back_populates="municipios")
    colonias   = relationship("Colonia", back_populates="municipio")


class Colonia(Base):
    """
    Colonias / barrios. Nivel más fino de la jerarquía geográfica.
    Permite búsquedas y agrupaciones por zona dentro de un municipio.
    """
    __tablename__ = "colonia"

    id_colonia    = Column(Integer, primary_key=True, autoincrement=True)
    id_municipio  = Column(Integer, ForeignKey("municipio.id_municipio"), nullable=False)
    nombre        = Column(String(200), nullable=False)
    codigo_postal = Column(String(10), nullable=True)

    # Relaciones
    municipio        = relationship("Municipio", back_populates="colonias")
    establecimientos = relationship("Establecimiento", back_populates="colonia")
