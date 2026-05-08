"""
Modelos SQLAlchemy — Tablas de la base de datos EKI.

Cada clase representa una tabla en MySQL (Aiven).
Usar sintaxis declarativa con DeclarativeBase (SQLAlchemy 2.x).
"""

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey,
    DateTime, Text, Boolean,
)
from sqlalchemy.orm import relationship

from database import Base


class Vendor(Base):
    """
    Representa un puesto, carrito o vendedor informal en el sistema.
    Es la entidad central del modelo de recomendación.
    """
    __tablename__ = "vendors"

    vendor_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    category = Column(String(60), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    rating_avg = Column(Float, default=0.0, nullable=False)
    review_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    ratings = relationship("UserRating", back_populates="vendor")


class User(Base):
    """
    Representa a un usuario registrado que puede calificar vendedores.
    """
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    ratings = relationship("UserRating", back_populates="user")


class UserRating(Base):
    """
    Registra la calificación que un usuario le da a un vendedor.
    Es la tabla de interacciones usada por el filtrado colaborativo.
    """
    __tablename__ = "user_ratings"

    rating_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vendor_id = Column(
        Integer,
        ForeignKey("vendors.vendor_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score = Column(Float, nullable=False)           # Valor entre 1.0 y 5.0
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    user = relationship("User", back_populates="ratings")
    vendor = relationship("Vendor", back_populates="ratings")
