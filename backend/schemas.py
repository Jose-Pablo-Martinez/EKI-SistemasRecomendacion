"""
Esquemas Pydantic v2 — Validación de request/response en la API EKI.

Organizados por dominio. Convención:
  - Sufijo 'Create'   → input (request body)
  - Sufijo 'Response' → output (serialización de modelos SQLAlchemy)

Todos los Response tienen ConfigDict(from_attributes=True) para
compatibilidad con SQLAlchemy ORM.

Validaciones críticas (complementan CHECK constraints que MySQL <8.0 ignora):
  - ResenaCreate.calificacion       → Field(ge=1, le=5)
  - EstablecimientoCreate.latitud   → Field(ge=-90, le=90)
  - EstablecimientoCreate.longitud  → Field(ge=-180, le=180)
  - UsuarioCreate.email             → EmailStr (requiere email-validator)
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ═══════════════════════════════════════════════════════════════════════════════
# DOMINIO: GEOGRAFÍA
# ═══════════════════════════════════════════════════════════════════════════════

class PaisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_pais: str
    nombre: str


class EstadoGeoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_estado: int
    id_pais: str
    nombre: str


class MunicipioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_municipio: int
    id_estado: int
    nombre: str


class ColoniaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_colonia: int
    id_municipio: int
    nombre: str
    codigo_postal: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# DOMINIO: USUARIOS
# ═══════════════════════════════════════════════════════════════════════════════

class UsuarioCreate(BaseModel):
    """Registro de un nuevo usuario. La contraseña se hashea en el backend."""
    email: EmailStr = Field(..., examples=["usuario@ejemplo.com"])
    nombre: str = Field(..., max_length=100, examples=["Juan"])
    apellido: str = Field(..., max_length=100, examples=["Pérez"])
    password: str = Field(
        ...,
        min_length=8,
        description="Contraseña en texto plano; se hashea con bcrypt antes de persistir.",
    )
    tipo_usuario: Literal["visitante", "propietario", "admin"] = Field(
        default="visitante",
        description="Tipo de usuario. Determina el subtipo TPT a crear.",
    )
    genero: Optional[Literal["masculino", "femenino", "otro", "prefiero_no_decir"]] = None
    fecha_nacimiento: Optional[date] = None


class UsuarioResponse(BaseModel):
    """Datos públicos de un usuario. No expone password_hash ni datos sensibles."""
    model_config = ConfigDict(from_attributes=True)

    id_usuario: int
    email: str
    nombre: str
    apellido: str
    foto_perfil: Optional[str] = None
    tipo_usuario: str
    activo: bool
    fecha_registro: datetime


class UsuarioVisitanteResponse(BaseModel):
    """Respuesta extendida con datos de visitante (gamificación y clustering)."""
    model_config = ConfigDict(from_attributes=True)

    id_usuario: int
    puntos_experiencia: int
    puntos_reputacion: int
    perfil_completado: bool
    radio_busqueda_km: Optional[int] = None
    fecha_ultima_actividad: Optional[datetime] = None
    # id_cluster y id_rango se exponen como IDs (no se carga el objeto completo)
    id_cluster: Optional[int] = None
    id_rango: Optional[int] = None


class UsuarioPropietarioResponse(BaseModel):
    """Respuesta extendida con datos de propietario (verificación y contacto)."""
    model_config = ConfigDict(from_attributes=True)

    id_usuario: int
    razon_social: Optional[str] = None
    telefono_contacto: Optional[str] = None
    verificado: bool
    fecha_verificacion: Optional[datetime] = None
    # rfc y documento_verificacion son sensibles — solo para admins


class AdministradorResponse(BaseModel):
    """Respuesta extendida con datos de administrador."""
    model_config = ConfigDict(from_attributes=True)

    id_usuario: int
    nivel_admin: int
    departamento: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# DOMINIO: ESTABLECIMIENTOS
# ═══════════════════════════════════════════════════════════════════════════════

class EstablecimientoCreate(BaseModel):
    """Registro de un nuevo establecimiento. Estado inicial: 'pendiente'."""
    nombre: str = Field(..., max_length=200, examples=["Tacos El Camarón"])
    descripcion: Optional[str] = Field(None, examples=["Tacos de camarón frente al mercado."])
    latitud: Decimal = Field(..., ge=-90, le=90, examples=[20.9674])
    longitud: Decimal = Field(..., ge=-180, le=180, examples=[-89.5926])
    direccion_texto: Optional[str] = Field(
        None, max_length=500, examples=["Frente al Mercado Lucas de Gálvez"]
    )
    id_colonia: Optional[int] = None
    tipo_establecimiento: Literal["restaurante", "local", "puesto_informal"]


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


# ═══════════════════════════════════════════════════════════════════════════════
# DOMINIO: CONTENIDO
# ═══════════════════════════════════════════════════════════════════════════════

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
    precio: Optional[Decimal] = Field(None, gt=0)
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


# ═══════════════════════════════════════════════════════════════════════════════
# DOMINIO: INTERACCIONES
# ═══════════════════════════════════════════════════════════════════════════════

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


class FavoritoCreate(BaseModel):
    """Guardar un establecimiento como favorito."""
    id_establecimiento: int
    nota_personal: Optional[str] = Field(None, examples=["Ir los domingos temprano."])


class HistorialVisitaResponse(BaseModel):
    """Historial de visitas del usuario a un establecimiento."""
    model_config = ConfigDict(from_attributes=True)

    id_visita: int
    id_usuario: int
    id_establecimiento: int
    fecha_visita: datetime
    duracion_segundos: Optional[int] = None
    fue_recomendado: bool


# ═══════════════════════════════════════════════════════════════════════════════
# DOMINIO: MOTOR DE RECOMENDACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════════
# DOMINIO: GAMIFICACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

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
