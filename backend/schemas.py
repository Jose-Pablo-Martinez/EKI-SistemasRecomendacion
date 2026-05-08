"""
Esquemas Pydantic v2 — Validación de request y response en la API EKI.

Separados de los modelos SQLAlchemy (models.py) según los lineamientos del proyecto.
Convención: sufijo 'Create' para input, sufijo 'Response' para output.
"""

from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


# ─── Vendor ───────────────────────────────────────────────────────────────────

class VendorCreate(BaseModel):
    """Esquema de entrada para crear un nuevo vendedor."""
    name: str = Field(..., max_length=120, examples=["Tacos El Camarón"])
    category: str = Field(..., max_length=60, examples=["Tacos"])
    description: str | None = Field(None, examples=["Tacos de camarón al pastor, frente al mercado."])
    location: str | None = Field(None, max_length=200, examples=["Mercado Lucas de Gálvez, Mérida"])


class VendorResponse(BaseModel):
    """Esquema de salida para un vendedor, incluye campos calculados."""
    model_config = ConfigDict(from_attributes=True)

    vendor_id: int
    name: str
    category: str
    description: str | None
    location: str | None
    is_active: bool
    rating_avg: float
    review_count: int
    created_at: datetime


# ─── User ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    """Esquema de entrada para registrar un nuevo usuario."""
    username: str = Field(..., max_length=80, examples=["juan_perez"])
    email: str = Field(..., max_length=150, examples=["juan@example.com"])


class UserResponse(BaseModel):
    """Esquema de salida para un usuario."""
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    username: str
    email: str
    created_at: datetime


# ─── UserRating ───────────────────────────────────────────────────────────────

class UserRatingCreate(BaseModel):
    """Esquema de entrada para crear una calificación."""
    user_id: int
    vendor_id: int
    score: float = Field(..., ge=1.0, le=5.0, examples=[4.5])
    comment: str | None = Field(None, examples=["Excelente sazón y precio justo."])


class UserRatingResponse(BaseModel):
    """Esquema de salida para una calificación."""
    model_config = ConfigDict(from_attributes=True)

    rating_id: int
    user_id: int
    vendor_id: int
    score: float
    comment: str | None
    created_at: datetime


# ─── Recomendación ────────────────────────────────────────────────────────────

class RecommendationResponse(BaseModel):
    """
    Esquema de salida para una recomendación del sistema híbrido.
    Incluye el vendedor y el puntaje de relevancia calculado.
    """
    model_config = ConfigDict(from_attributes=True)

    vendor: VendorResponse
    relevance_score: float = Field(..., description="Puntaje final tras aplicar boosting y filtros.")
    boosted: bool = Field(False, description="Indica si el vendedor recibió boosting por pocas reseñas.")
