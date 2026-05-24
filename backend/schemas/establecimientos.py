"""
Dominio: ESTABLECIMIENTOS
Schemas de creación y respuesta para establecimientos y su contenido asociado
(Restaurante, LocalComercial, PuestoInformal, Platillo, Imagen, Horario,
Categoría, Etiqueta).
"""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class EstablecimientoCreate(BaseModel):
    """Registro de un nuevo establecimiento. Estado inicial: 'pendiente'."""
    nombre: str = Field(..., max_length=200, examples=["Tacos El Camarón"])
    descripcion: Optional[str] = Field(None, examples=["Tacos de camarón frente al mercado."])
    latitud: Decimal = Field(..., ge=Decimal("-90"), le=Decimal("90"), examples=[20.9674])
    longitud: Decimal = Field(..., ge=Decimal("-180"), le=Decimal("180"), examples=[-89.5926])
    direccion_texto: Optional[str] = Field(
        None, max_length=500, examples=["Frente al Mercado Lucas de Gálvez"]
    )
    id_colonia: Optional[int] = None
    tipo_establecimiento: Literal["restaurante", "local", "puesto_informal"]


class EstablecimientoUpdate(BaseModel):
    """Actualización de establecimiento."""
    nombre: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = None
    latitud: Optional[Decimal] = Field(None, ge=Decimal("-90"), le=Decimal("90"))
    longitud: Optional[Decimal] = Field(None, ge=Decimal("-180"), le=Decimal("180"))
    direccion_texto: Optional[str] = Field(None, max_length=500)
    id_colonia: Optional[int] = None


class EstablecimientoResponse(BaseModel):
    """Datos públicos de un establecimiento aprobado."""
    model_config = ConfigDict(from_attributes=True)

    id_establecimiento: int
    nombre: str
    descripcion: Optional[str] = None
    latitud: Decimal
    longitud: Decimal
    direccion_texto: Optional[str] = None
    id_colonia: Optional[int] = None
    tipo_establecimiento: str
    es_informal: bool
    estado: str
    es_activo: bool
    total_resenas: int
    calificacion_promedio: Decimal
    fecha_registro: datetime


class RestauranteCreate(BaseModel):
    """Datos específicos de un restaurante (complementa EstablecimientoCreate)."""
    id_categoria_principal: Optional[int] = None
    capacidad: Optional[int] = None
    acepta_reservaciones: bool = False
    servicio_domicilio: bool = False
    telefono: Optional[str] = Field(None, max_length=20)
    sitio_web: Optional[str] = Field(None, max_length=500)
    facebook_url: Optional[str] = Field(None, max_length=500)
    instagram_url: Optional[str] = Field(None, max_length=500)
    precio_promedio: Optional[Decimal] = None


class RestauranteResponse(BaseModel):
    """Respuesta con datos de restaurante."""
    model_config = ConfigDict(from_attributes=True)

    id_restaurante: int
    id_categoria_principal: Optional[int] = None
    capacidad: Optional[int] = None
    acepta_reservaciones: bool
    servicio_domicilio: bool
    telefono: Optional[str] = None
    sitio_web: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    precio_promedio: Optional[Decimal] = None


class LocalComercialCreate(BaseModel):
    """Datos específicos de un local comercial."""
    numero_local: Optional[str] = Field(None, max_length=20)
    nivel_piso: Optional[str] = Field(None, max_length=10)
    nombre_edificio: Optional[str] = Field(
        None, max_length=200, examples=["Mercado Lucas de Gálvez"]
    )
    tiene_area_comedor: bool = True


class LocalComercialResponse(BaseModel):
    """Respuesta con datos de local comercial."""
    model_config = ConfigDict(from_attributes=True)

    id_local: int
    numero_local: Optional[str] = None
    nivel_piso: Optional[str] = None
    nombre_edificio: Optional[str] = None
    tiene_area_comedor: bool


class PuestoInformalCreate(BaseModel):
    """Datos específicos de un puesto informal."""
    es_movil: bool = False
    ubicacion_referencia: Optional[str] = Field(
        None, examples=["Frente al Parque Santa Lucía"]
    )
    dias_tipicos: Optional[str] = Field(
        None, max_length=100, examples=["Lunes a Sábado"]
    )
    horario_aproximado: Optional[str] = Field(
        None, max_length=100, examples=["7am - 2pm"]
    )


class PuestoInformalResponse(BaseModel):
    """Respuesta con datos de puesto informal."""
    model_config = ConfigDict(from_attributes=True)

    id_puesto: int
    es_movil: bool
    ubicacion_referencia: Optional[str] = None
    dias_tipicos: Optional[str] = None
    horario_aproximado: Optional[str] = None


class CategoriaCreate(BaseModel):
    """Crear una nueva categoría gastronómica."""
    nombre: str = Field(..., max_length=100, examples=["Yucateca"])
    id_categoria_padre: Optional[int] = Field(None, description="ID de la categoría padre (subcategoría).")
    descripcion: Optional[str] = Field(None, max_length=500)
    icono: Optional[str] = Field(None, max_length=200)


class CategoriaResponse(BaseModel):
    """Categoría con soporte de subcategorías."""
    model_config = ConfigDict(from_attributes=True)

    id_categoria: int
    nombre: str
    id_categoria_padre: Optional[int] = None
    descripcion: Optional[str] = None
    icono: Optional[str] = None


class EtiquetaCreate(BaseModel):
    """Crear una nueva etiqueta cualitativa."""
    nombre: str = Field(..., max_length=50, examples=["económico"])
    descripcion: Optional[str] = Field(None, max_length=200)


class EtiquetaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_etiqueta: int
    nombre: str
    descripcion: Optional[str] = None


class PlatilloCreate(BaseModel):
    """Registrar un platillo del menú de un establecimiento."""
    id_establecimiento: int
    nombre: str = Field(..., max_length=200, examples=["Sopa de Lima"])
    descripcion: Optional[str] = None
    precio: Optional[Decimal] = Field(None, gt=Decimal("0"))
    disponible: bool = True


class PlatilloResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_platillo: int
    id_establecimiento: int
    nombre: str
    descripcion: Optional[str] = None
    precio: Optional[Decimal] = None
    disponible: bool
    estado: str
    fecha_registro: datetime


class ImagenCreate(BaseModel):
    """Registrar una imagen de un establecimiento."""
    id_establecimiento: int
    url_imagen: str = Field(..., max_length=500)
    tipo: Literal["exterior", "interior", "platillo", "menu", "otro"] = "otro"
    es_principal: bool = False


class ImagenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_imagen: int
    id_establecimiento: int
    url_imagen: str
    tipo: str
    es_principal: bool
    estado: str
    fecha_upload: datetime


class HorarioCreate(BaseModel):
    """Registrar horario de un día para un establecimiento."""
    id_establecimiento: int
    dia_semana: int = Field(..., ge=0, le=6, description="0=Domingo … 6=Sábado")
    hora_apertura: Optional[str] = Field(None, examples=["08:00:00"])
    hora_cierre: Optional[str] = Field(None, examples=["22:00:00"])
    cerrado: bool = False


class HorarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_horario: int
    id_establecimiento: int
    dia_semana: int
    hora_apertura: Optional[str] = None
    hora_cierre: Optional[str] = None
    cerrado: bool
