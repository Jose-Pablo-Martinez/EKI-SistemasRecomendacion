"""
Dominio: GEOGRAFÍA
Schemas de respuesta para los catálogos geográficos.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, ConfigDict


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
