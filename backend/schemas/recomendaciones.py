"""
Dominio: INTERACCIONES, GAMIFICACIÓN Y RECOMENDACIONES
Schemas para reseñas, interacciones, favoritos, historial, contribuciones,
puntos, reportes y el motor de recomendación.
"""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


# ─── Reseñas ──────────────────────────────────────────────────────────────────

class ResenaCreate(BaseModel):
    """
    Crear una reseña. Validación de calificación obligatoria en Pydantic
    (complementa el CHECK constraint que MySQL <8.0 ignora) — ver §1.1 del diseño.
    """
    id_establecimiento: int
    calificacion: int = Field(
        ..., ge=1, le=5, description="Calificación de 1 a 5 estrellas."
    )
    comentario: Optional[str] = Field(None, examples=["Excelente sazón y precio justo."])


class ResenaResponse(BaseModel):
    """Reseña con campos NLP (calculados por job offline)."""
    model_config = ConfigDict(from_attributes=True)

    id_resena: int
    id_usuario: int
    id_establecimiento: int
    calificacion: int
    comentario: Optional[str] = None
    fecha_resena: datetime
    estado: str
    polaridad: Optional[Decimal] = None
    subjetividad: Optional[Decimal] = None
    procesado_nlp: bool


# ─── Interacciones ────────────────────────────────────────────────────────────

class InteraccionUsuarioCreate(BaseModel):
    """Registrar una interacción explícita del usuario con un establecimiento."""
    id_establecimiento: int
    tipo_interaccion: Literal[
        "vista_detalle", "guardado_favorito", "compartido",
        "llamada_telefono", "abrir_maps", "resena_dejada", "ruta_calculada",
    ]
    id_sesion: Optional[str] = Field(None, description="UUID v4 de la sesión activa.")


class InteraccionUsuarioResponse(BaseModel):
    """Interacción registrada con peso pre-calculado."""
    model_config = ConfigDict(from_attributes=True)

    id_interaccion: int
    id_usuario: int
    id_establecimiento: int
    tipo_interaccion: str
    peso_interaccion: Optional[Decimal] = None
    fecha: datetime


# ─── Favoritos ────────────────────────────────────────────────────────────────

class FavoritoCreate(BaseModel):
    """Guardar un establecimiento como favorito."""
    id_establecimiento: int
    nota_personal: Optional[str] = Field(None, examples=["Ir los domingos temprano."])


# ─── Historial de Visitas ─────────────────────────────────────────────────────

class HistorialVisitaResponse(BaseModel):
    """Historial de visitas del usuario a un establecimiento."""
    model_config = ConfigDict(from_attributes=True)

    id_visita: int
    id_usuario: int
    id_establecimiento: int
    fecha_visita: datetime
    duracion_segundos: Optional[int] = None
    fue_recomendado: bool


# ─── Motor de Recomendación ───────────────────────────────────────────────────

class MetricaEstablecimientoResponse(BaseModel):
    """Métricas pre-computadas del motor (solo lectura)."""
    model_config = ConfigDict(from_attributes=True)

    id_establecimiento: int
    score_contenido_base: Optional[Decimal] = None
    score_colaborativo_base: Optional[Decimal] = None
    boost_proximidad_zona: Optional[Decimal] = None
    boost_informal: Optional[Decimal] = None
    score_boost_combinado: Optional[Decimal] = None
    popularidad_7d: Optional[int] = None
    popularidad_30d: Optional[int] = None
    polaridad_promedio: Optional[Decimal] = None
    ultima_actualizacion: Optional[datetime] = None


class RecomendacionResponse(BaseModel):
    """
    Recomendación generada por el motor con soporte de caja blanca.
    Los snapshots de scores permiten al frontend explicar CADA recomendación.
    categoria_recomendacion discrimina las secciones de la UI — ver §1.8.
    """
    model_config = ConfigDict(from_attributes=True)

    id_recomendacion: int
    id_usuario: int
    id_establecimiento: int

    # Categoría semántica — para agrupar secciones en el frontend
    categoria_recomendacion: str

    # Ranking y scores (caja blanca)
    posicion: int
    score_total: Optional[Decimal] = None
    score_contenido_usado: Optional[Decimal] = None
    score_colaborativo_usado: Optional[Decimal] = None
    score_boost_aplicado: Optional[Decimal] = None

    # Contexto geográfico
    distancia_km: Optional[Decimal] = None
    radio_usado_km: int
    fallback_nivel: int

    # Explicabilidad (caja blanca) — ver §1.8
    razon_principal: Optional[str] = None
    detalle_razon: Optional[str] = Field(
        None,
        description="Texto legible: 'A 0.8 km · Popular entre usuarios como tú'",
    )
    estrategia_usada: Optional[str] = None

    # Metadatos
    fecha_generacion: datetime
    fue_clickeada: bool
    es_descubrimiento: bool
    diversity_score: Optional[Decimal] = None


# ─── Gamificación ─────────────────────────────────────────────────────────────

class ContribucionCreate(BaseModel):
    """Registrar una contribución de información del usuario."""
    id_establecimiento: Optional[int] = Field(
        None,
        description="NULL cuando se registra un lugar nuevo.",
    )
    tipo_contribucion: Literal[
        "nuevo_lugar", "edicion_info", "nueva_foto", "nuevo_platillo", "nueva_resena"
    ]
    descripcion_cambio: Optional[str] = None


class ContribucionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_contribucion: int
    id_usuario: int
    id_establecimiento: Optional[int] = None
    tipo_contribucion: str
    estado: str
    puntos_otorgados: int
    fecha_contribucion: datetime
    fecha_revision: Optional[datetime] = None


class LogPuntosResponse(BaseModel):
    """Registro inmutable de auditoría de puntos."""
    model_config = ConfigDict(from_attributes=True)

    id_log: int
    id_usuario: int
    puntos: int
    motivo: str
    id_contribucion: Optional[int] = None
    fecha: datetime


class ReporteCreate(BaseModel):
    """Reportar un problema con un establecimiento."""
    id_establecimiento: int
    tipo_reporte: Literal[
        "informacion_incorrecta", "lugar_cerrado", "contenido_inapropiado", "spam", "otro"
    ]
    descripcion: Optional[str] = None


class ReporteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_reporte: int
    id_usuario: int
    id_establecimiento: int
    tipo_reporte: str
    estado: str
    fecha_reporte: datetime
