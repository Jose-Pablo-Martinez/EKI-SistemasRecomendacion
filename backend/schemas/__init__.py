"""
backend/schemas/__init__.py

Re-exporta todos los schemas desde sus módulos de dominio para que los imports
externos de la forma `from backend.schemas import UsuarioCreate` sigan
funcionando sin ningún cambio.

Organización:
    - geografia.py    → PaisResponse, EstadoGeoResponse, MunicipioResponse, ColoniaResponse
    - usuarios.py     → UsuarioCreate/Response, UsuarioVisitanteResponse,
                        UsuarioPropietarioResponse, AdministradorResponse
    - establecimientos.py → Establecimiento*, Restaurante*, LocalComercial*,
                            PuestoInformal*, Categoria*, Etiqueta*,
                            Platillo*, Imagen*, Horario*
    - recomendaciones.py  → Resena*, Interaccion*, Favorito*, Historial*,
                            Metrica*, Recomendacion*, Contribucion*,
                            LogPuntos*, Reporte*
"""

from backend.schemas.geografia import (
    PaisResponse,
    EstadoGeoResponse,
    MunicipioResponse,
    ColoniaResponse,
)

from backend.schemas.usuarios import (
    UsuarioCreate,
    UsuarioResponse,
    UsuarioVisitanteResponse,
    UsuarioPropietarioResponse,
    AdministradorResponse,
)

from backend.schemas.establecimientos import (
    EstablecimientoCreate,
    EstablecimientoResponse,
    RestauranteCreate,
    RestauranteResponse,
    LocalComercialCreate,
    LocalComercialResponse,
    PuestoInformalCreate,
    PuestoInformalResponse,
    CategoriaCreate,
    CategoriaResponse,
    EtiquetaCreate,
    EtiquetaResponse,
    PlatilloCreate,
    PlatilloResponse,
    ImagenCreate,
    ImagenResponse,
    HorarioCreate,
    HorarioResponse,
)

from backend.schemas.recomendaciones import (
    ResenaCreate,
    ResenaResponse,
    InteraccionUsuarioCreate,
    InteraccionUsuarioResponse,
    FavoritoCreate,
    HistorialVisitaResponse,
    MetricaEstablecimientoResponse,
    RecomendacionResponse,
    ContribucionCreate,
    ContribucionResponse,
    LogPuntosResponse,
    ReporteCreate,
    ReporteResponse,
)

__all__ = [
    # Geografía
    "PaisResponse", "EstadoGeoResponse", "MunicipioResponse", "ColoniaResponse",
    # Usuarios
    "UsuarioCreate", "UsuarioResponse", "UsuarioVisitanteResponse",
    "UsuarioPropietarioResponse", "AdministradorResponse",
    # Establecimientos
    "EstablecimientoCreate", "EstablecimientoResponse",
    "RestauranteCreate", "RestauranteResponse",
    "LocalComercialCreate", "LocalComercialResponse",
    "PuestoInformalCreate", "PuestoInformalResponse",
    "CategoriaCreate", "CategoriaResponse",
    "EtiquetaCreate", "EtiquetaResponse",
    "PlatilloCreate", "PlatilloResponse",
    "ImagenCreate", "ImagenResponse",
    "HorarioCreate", "HorarioResponse",
    # Interacciones y recomendaciones
    "ResenaCreate", "ResenaResponse",
    "InteraccionUsuarioCreate", "InteraccionUsuarioResponse",
    "FavoritoCreate",
    "HistorialVisitaResponse",
    "MetricaEstablecimientoResponse",
    "RecomendacionResponse",
    "ContribucionCreate", "ContribucionResponse",
    "LogPuntosResponse",
    "ReporteCreate", "ReporteResponse",
]
