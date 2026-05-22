"""
backend/models/__init__.py

Re-exporta todos los modelos desde sus módulos de dominio para que los imports
externos de la forma `from backend.models import Usuario` sigan funcionando
sin ningún cambio. El orden de importación garantiza que SQLAlchemy registre
todos los modelos en el mismo Base antes de que Alembic construya el grafo
de relaciones.

Orden de carga (dependencias primero):
    1. geografia   — sin dependencias externas
    2. catalogo    — sin dependencias externas
    3. clusters    — sin dependencias externas
    4. usuarios    — depende de catalogo (RangoInformador) y clusters (ClusterUsuario)
    5. establecimientos — depende de geografia (Colonia), clusters, catalogo, usuarios
    6. interacciones    — depende de usuarios, establecimientos, catalogo
"""

# 1. Geografía
from backend.models.geografia import (
    Pais,
    EstadoGeo,
    Municipio,
    Colonia,
)

# 2. Catálogo base
from backend.models.catalogo import (
    RangoInformador,
    Categoria,
    Etiqueta,
)

# 3. Clusters ML
from backend.models.clusters import (
    ClusterUsuario,
    ClusterEstablecimiento,
)

# 4. Usuarios (TPT)
from backend.models.usuarios import (
    Usuario,
    DispositivoUsuario,
    SesionUsuario,
    UsuarioVisitante,
    UsuarioPropietario,
    Administrador,
    UbicacionUsuario,
)

# 5. Establecimientos (TPT + contenido)
from backend.models.establecimientos import (
    Establecimiento,
    Restaurante,
    LocalComercial,
    PuestoInformal,
    PropietarioEstablecimiento,
    EstablecimientoCategoria,
    EstablecimientoEtiqueta,
    Platillo,
    Imagen,
    Horario,
    MetricaEstablecimiento,
)

# 6. Interacciones, gamificación y motor de recomendación
from backend.models.interacciones import (
    InteraccionUsuario,
    RecomendacionGenerada,
    ContribucionInformacion,
    LogPuntos,
    Resena,
    FavoritoGuardado,
    HistorialVisita,
    PreferenciaUsuario,
    Reporte,
    RecomendacionGeneradaHistorico,
    InteraccionUsuarioHistorico,
)

__all__ = [
    # Geografía
    "Pais", "EstadoGeo", "Municipio", "Colonia",
    # Catálogo
    "RangoInformador", "Categoria", "Etiqueta",
    # Clusters
    "ClusterUsuario", "ClusterEstablecimiento",
    # Usuarios
    "Usuario", "DispositivoUsuario", "SesionUsuario", "UsuarioVisitante",
    "UsuarioPropietario", "Administrador", "UbicacionUsuario",
    # Establecimientos
    "Establecimiento", "Restaurante", "LocalComercial", "PuestoInformal",
    "PropietarioEstablecimiento", "EstablecimientoCategoria", "EstablecimientoEtiqueta",
    "Platillo", "Imagen", "Horario", "MetricaEstablecimiento",
    # Interacciones
    "InteraccionUsuario", "RecomendacionGenerada", "ContribucionInformacion",
    "LogPuntos", "Resena", "FavoritoGuardado", "HistorialVisita",
    "PreferenciaUsuario", "Reporte",
    # Archivado
    "RecomendacionGeneradaHistorico", "InteraccionUsuarioHistorico",
]
