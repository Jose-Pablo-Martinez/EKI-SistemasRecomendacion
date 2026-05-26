"""
Dominio: USUARIOS
Schemas de creación y respuesta para los tipos de usuario (TPT).
"""
from __future__ import annotations
from datetime import date, datetime
from typing import Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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

class PerfilUpdate(BaseModel):
    """Actualización de perfil."""
    nombre: Optional[str] = Field(None, max_length=100)
    apellido: Optional[str] = Field(None, max_length=100)
    foto_perfil: Optional[str] = None
    genero: Optional[Literal["masculino", "femenino", "otro", "prefiero_no_decir"]] = None
    fecha_nacimiento: Optional[date] = None
    radio_busqueda_km: Optional[int] = Field(None, ge=1, le=50)


class PreferenciasOnboarding(BaseModel):
    categorias: list[str]
    precios: list[str]

class OnboardingData(BaseModel):
    preferencias: PreferenciasOnboarding

class UbicacionData(BaseModel):
    latitud: float
    longitud: float
    precision_metros: Optional[int] = None

class UsuarioResponse(BaseModel):
    """Datos públicos de un usuario. No expone password_hash ni datos sensibles."""
    model_config = ConfigDict(from_attributes=True)

    id_usuario: int
    email: str
    nombre: str
    apellido: str
    foto_perfil: Optional[str] = None
    tipo_usuario: str
    total_resenas: int = 0
    activo: bool
    fecha_registro: datetime
    perfil_completado: bool = False
    visitante: Optional["UsuarioVisitanteResponse"] = None


class UsuarioPerfilResponse(UsuarioResponse):
    """Perfil extendido con totales de actividad del usuario."""
    puntos_totales: int = 0
    total_resenas: int = 0
    total_favoritos: int = 0
    total_contribuciones: int = 0


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
    vector_preferencias: Optional[Union[dict, list]] = None


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
