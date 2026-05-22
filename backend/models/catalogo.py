"""
Dominio: CATÁLOGO BASE
Tablas de configuración estática: rangos, categorías y etiquetas.
Se definen antes de Usuarios y Establecimientos porque ambos las referencian.
"""
# pyrefly: ignore [missing-import]
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DECIMAL, CHAR
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.mysql import TINYINT
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import relationship

from backend.database import Base


class RangoInformador(Base):
    """
    Niveles de confianza del sistema de gamificación.
    factor_confianza ∈ [0.0, 1.0]: rige el rigor de moderación por rango.
    Seed inicial: 5 rangos (Turista → Experto Local) — ver §1.5.
    """
    __tablename__ = "rango_informador"

    id_rango         = Column(TINYINT, primary_key=True, autoincrement=True)
    nivel            = Column(TINYINT, unique=True, nullable=False)
    nombre           = Column(String(50), nullable=False)
    puntos_minimos   = Column(Integer, nullable=False)
    factor_confianza = Column(DECIMAL(3, 2), default=0.50)
    descripcion      = Column(Text, nullable=True)
    color_badge      = Column(CHAR(7), nullable=True)   # hex: '#FF5733'

    # Relaciones
    usuarios_visitantes = relationship("UsuarioVisitante", back_populates="rango")


class Categoria(Base):
    """
    Categorías gastronómicas auto-referenciales (soporte de subcategorías).
    Ej: 'Mexicana' → 'Yucateca'. UK en nombre para evitar duplicados.
    """
    __tablename__ = "categoria"

    id_categoria       = Column(Integer, primary_key=True, autoincrement=True)
    nombre             = Column(String(100), unique=True, nullable=False)
    id_categoria_padre = Column(Integer, ForeignKey("categoria.id_categoria"), nullable=True)
    descripcion        = Column(String(500), nullable=True)
    icono              = Column(String(200), nullable=True)

    # Relaciones — Self-referential (adjacency list)
    subcategorias = relationship(
        "Categoria",
        foreign_keys="[Categoria.id_categoria_padre]",
        back_populates="padre_categoria",
    )
    padre_categoria = relationship(
        "Categoria",
        foreign_keys="[Categoria.id_categoria_padre]",
        back_populates="subcategorias",
        remote_side="[Categoria.id_categoria]",
    )
    establecimientos = relationship("EstablecimientoCategoria", back_populates="categoria")
    preferencias     = relationship("PreferenciaUsuario", back_populates="categoria")
    restaurantes     = relationship("Restaurante", back_populates="categoria_principal")


class Etiqueta(Base):
    """
    Etiquetas cualitativas para establecimientos.
    Separadas de Categoria: son descriptores ('económico', 'familiar', 'vegano'),
    no clasificaciones jerárquicas.
    """
    __tablename__ = "etiqueta"

    id_etiqueta = Column(Integer, primary_key=True, autoincrement=True)
    nombre      = Column(String(50), unique=True, nullable=False)
    descripcion = Column(String(200), nullable=True)

    # Relaciones
    establecimientos = relationship("EstablecimientoEtiqueta", back_populates="etiqueta")
