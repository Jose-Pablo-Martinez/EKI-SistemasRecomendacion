"""
Modelos SQLAlchemy — Tablas de la base de datos EKI (Esquina Jach ki').

Esquema definitivo: 36 tablas core + 2 de archivado = 38 tablas totales.
Organizado por dominio según §4 de EkiSystem_DB_Design.md.

Patrón de herencia: Table-per-Type (TPT) puro a nivel de schema.
No se usa polymorphic_on de SQLAlchemy — ver §1.1 del diseño.

Índices secundarios del §5 declarados en __table_args__ (Opción A) para
que Alembic --autogenerate los detecte automáticamente.
"""

from datetime import datetime

# pyrefly: ignore [missing-import]
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Date, Time,
    ForeignKey, Enum, JSON, DECIMAL, Index, CheckConstraint,
    UniqueConstraint, CHAR,
)
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.mysql import TINYINT
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import relationship

from backend.database import Base


# ═══════════════════════════════════════════════════════════════════════════════
# DOMINIO: GEOGRAFÍA
# Tablas base sin dependencias externas. Se definen primero.
# ═══════════════════════════════════════════════════════════════════════════════

class Pais(Base):
    """
    Catálogo de países. PK: código ISO 3166-1 alpha-2 (ej. 'MX', 'US').
    Seed inicial: 'MX' — México.
    """
    __tablename__ = "pais"

    id_pais = Column(CHAR(2), primary_key=True)
    nombre  = Column(String(100), nullable=False)

    # Relaciones
    estados = relationship("EstadoGeo", back_populates="pais")


class EstadoGeo(Base):
    """
    Estados / provincias geográficas.
    Nombre 'estado_geo' para evitar colisión con el campo ENUM 'estado'
    que existe en múltiples tablas — ver §1.4 del diseño.
    """
    __tablename__ = "estado_geo"

    id_estado = Column(Integer, primary_key=True, autoincrement=True)
    id_pais   = Column(CHAR(2), ForeignKey("pais.id_pais"), nullable=False)
    nombre    = Column(String(100), nullable=False)

    # Relaciones
    pais       = relationship("Pais", back_populates="estados")
    municipios = relationship("Municipio", back_populates="estado_geo")


class Municipio(Base):
    """Municipios, vinculados a su estado geográfico."""
    __tablename__ = "municipio"

    id_municipio = Column(Integer, primary_key=True, autoincrement=True)
    id_estado    = Column(Integer, ForeignKey("estado_geo.id_estado"), nullable=False)
    nombre       = Column(String(100), nullable=False)

    # Relaciones
    estado_geo = relationship("EstadoGeo", back_populates="municipios")
    colonias   = relationship("Colonia", back_populates="municipio")


class Colonia(Base):
    """
    Colonias / barrios. Nivel más fino de la jerarquía geográfica.
    Permite búsquedas y agrupaciones por zona dentro de un municipio.
    """
    __tablename__ = "colonia"

    id_colonia    = Column(Integer, primary_key=True, autoincrement=True)
    id_municipio  = Column(Integer, ForeignKey("municipio.id_municipio"), nullable=False)
    nombre        = Column(String(200), nullable=False)
    codigo_postal = Column(String(10), nullable=True)

    # Relaciones
    municipio        = relationship("Municipio", back_populates="colonias")
    establecimientos = relationship("Establecimiento", back_populates="colonia")


# ═══════════════════════════════════════════════════════════════════════════════
# CATÁLOGOS BASE — Sin dependencias a Usuarios/Establecimientos
# ═══════════════════════════════════════════════════════════════════════════════

class RangoInformador(Base):
    """
    Niveles de confianza del sistema de gamificación.
    factor_confianza ∈ [0.0, 1.0]: rige el rigor de moderación por rango.
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


class ClusterUsuario(Base):
    """
    Clusters de usuarios generados por K-Means offline.
    centroide: vector numérico para asignar nuevos usuarios por distancia euclidiana.
    total_usuarios: desnormalizado — ver §1.5.
    """
    __tablename__ = "cluster_usuario"

    id_cluster          = Column(Integer, primary_key=True, autoincrement=True)
    nombre_cluster      = Column(String(100), nullable=True)
    centroide           = Column(JSON, nullable=True)
    descripcion         = Column(Text, nullable=True)
    total_usuarios      = Column(Integer, default=0)
    fecha_actualizacion = Column(DateTime, nullable=True)

    # Relaciones
    usuarios = relationship("UsuarioVisitante", back_populates="cluster")


class ClusterEstablecimiento(Base):
    """
    Clusters de establecimientos generados por K-Means offline.
    centroide: vector de características (categorías, precio, etiquetas, es_informal).
    total_establecimientos: desnormalizado — ver §1.5.
    """
    __tablename__ = "cluster_establecimiento"

    id_cluster             = Column(Integer, primary_key=True, autoincrement=True)
    nombre_cluster         = Column(String(100), nullable=True)
    centroide              = Column(JSON, nullable=True)
    descripcion            = Column(Text, nullable=True)
    total_establecimientos = Column(Integer, default=0)
    fecha_actualizacion    = Column(DateTime, nullable=True)

    # Relaciones
    establecimientos = relationship("Establecimiento", back_populates="cluster")


# ═══════════════════════════════════════════════════════════════════════════════
# DOMINIO: CONTENIDO — Catálogos (definidos antes de Establecimientos porque
# Restaurante referencia Categoria)
# ═══════════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════════
# DOMINIO: USUARIOS — TPT (Table-per-Type)
# ═══════════════════════════════════════════════════════════════════════════════

class Usuario(Base):
    """
    Entidad base TPT raíz. Atributos comunes a todos los tipos de usuario.
    tipo_usuario: discriminador TPT — no conectado al mapper de SA (ver §1.1).
    password_hash: la BD nunca recibe la contraseña en claro — ver §1.6.
    """
    __tablename__ = "usuario"

    id_usuario       = Column(Integer, primary_key=True, autoincrement=True)
    email            = Column(String(255), unique=True, nullable=False)
    nombre           = Column(String(100), nullable=False)
    apellido         = Column(String(100), nullable=False)
    password_hash    = Column(String(255), nullable=False)
    foto_perfil      = Column(String(500), nullable=True)
    fecha_nacimiento = Column(Date, nullable=True)
    genero           = Column(
        Enum("masculino", "femenino", "otro", "prefiero_no_decir"),
        nullable=True,
    )
    tipo_usuario     = Column(
        Enum("visitante", "propietario", "admin"),
        nullable=False,
    )
    activo          = Column(Boolean, default=True, nullable=False)
    fecha_registro  = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    visitante     = relationship("UsuarioVisitante", back_populates="usuario", uselist=False)
    administrador = relationship("Administrador", back_populates="usuario", uselist=False)
    dispositivos  = relationship("DispositivoUsuario", back_populates="usuario")
    sesiones      = relationship("SesionUsuario", back_populates="usuario")
    ubicaciones   = relationship("UbicacionUsuario", back_populates="usuario")
    establecimientos_registrados = relationship(
        "Establecimiento",
        foreign_keys="[Establecimiento.id_usuario_registro]",
        back_populates="usuario_registro",
    )
    interacciones   = relationship("InteraccionUsuario", back_populates="usuario")
    resenas         = relationship("Resena", back_populates="usuario")
    reportes        = relationship("Reporte", back_populates="usuario")
    historial_visitas = relationship("HistorialVisita", back_populates="usuario")


class DispositivoUsuario(Base):
    """
    Contexto de hardware detectado automáticamente del User-Agent HTTP.
    es_ultimo: solo el dispositivo más reciente tiene TRUE.
    Invariante: FastAPI garantiza unicidad de es_ultimo por usuario — ver §7.
    """
    __tablename__ = "dispositivo_usuario"

    id_dispositivo    = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario        = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    tipo_dispositivo  = Column(
        Enum("movil", "tablet", "escritorio", "desconocido"),
        nullable=False,
    )
    sistema_operativo = Column(String(50), nullable=True)
    es_ultimo         = Column(Boolean, default=True, nullable=False)
    fecha_deteccion   = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    usuario  = relationship("Usuario", back_populates="dispositivos")
    sesiones = relationship("SesionUsuario", back_populates="dispositivo")


class SesionUsuario(Base):
    """
    Unidad de análisis de comportamiento. id_sesion es UUID v4 generado por FastAPI,
    nunca por el cliente.
    total_vistas: desnormalizado — ver §1.5.
    """
    __tablename__ = "sesion_usuario"
    __table_args__ = (
        Index("idx_sesion_usuario_fecha", "id_usuario", "fecha_inicio"),
    )

    id_sesion         = Column(String(36), primary_key=True)   # UUID v4
    id_usuario        = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    fecha_inicio      = Column(DateTime, nullable=False, default=datetime.utcnow)
    fecha_fin         = Column(DateTime, nullable=True)
    duracion_segundos = Column(Integer, nullable=True)
    total_vistas      = Column(Integer, default=0)              # Desnormalizado §1.5
    id_dispositivo    = Column(
        Integer, ForeignKey("dispositivo_usuario.id_dispositivo"), nullable=True
    )

    # Relaciones
    usuario       = relationship("Usuario", back_populates="sesiones")
    dispositivo   = relationship("DispositivoUsuario", back_populates="sesiones")
    ubicaciones   = relationship("UbicacionUsuario", back_populates="sesion")
    interacciones = relationship("InteraccionUsuario", back_populates="sesion")
    historial     = relationship("HistorialVisita", back_populates="sesion")


class UsuarioVisitante(Base):
    """
    Extensión TPT de Usuario para visitantes (PK = FK → usuario).
    vector_preferencias: vector JSON para K-Means y filtrado por contenido.
    perfil_completado: señal de cold start — ver §1.2.
    puntos_experiencia: suma materializada de log_puntos — ver §1.5.
    """
    __tablename__ = "usuario_visitante"

    id_usuario             = Column(Integer, ForeignKey("usuario.id_usuario"), primary_key=True)
    id_rango               = Column(TINYINT, ForeignKey("rango_informador.id_rango"), nullable=True)
    id_cluster             = Column(Integer, ForeignKey("cluster_usuario.id_cluster"), nullable=True)
    puntos_experiencia     = Column(Integer, default=0)         # Desnormalizado §1.5
    puntos_reputacion      = Column(Integer, default=0)
    perfil_completado      = Column(Boolean, default=False, nullable=False)
    fecha_ultima_actividad = Column(DateTime, nullable=True)
    radio_busqueda_km      = Column(TINYINT, default=5)
    vector_preferencias    = Column(JSON, nullable=True)

    # Relaciones
    usuario       = relationship("Usuario", back_populates="visitante")
    rango         = relationship("RangoInformador", back_populates="usuarios_visitantes")
    cluster       = relationship("ClusterUsuario", back_populates="usuarios")
    propietario   = relationship("UsuarioPropietario", back_populates="visitante", uselist=False)
    contribuciones = relationship("ContribucionInformacion", back_populates="usuario_visitante")
    log_puntos    = relationship("LogPuntos", back_populates="usuario_visitante")
    favoritos     = relationship("FavoritoGuardado", back_populates="usuario_visitante")
    preferencias  = relationship("PreferenciaUsuario", back_populates="usuario_visitante")


class UsuarioPropietario(Base):
    """
    Extensión TPT de UsuarioVisitante para propietarios (PK = FK → usuario_visitante).
    Hereda de UsuarioVisitante: un propietario también es informador y acumula puntos.
    Campos sensibles rfc, documento_verificacion: solo accesibles por admins — ver §1.6.
    """
    __tablename__ = "usuario_propietario"

    id_usuario             = Column(
        Integer, ForeignKey("usuario_visitante.id_usuario"), primary_key=True
    )
    razon_social           = Column(String(255), nullable=True)
    rfc                    = Column(String(20), nullable=True)
    telefono_contacto      = Column(String(20), nullable=True)
    documento_verificacion = Column(String(500), nullable=True)
    verificado             = Column(Boolean, default=False, nullable=False)
    fecha_verificacion     = Column(DateTime, nullable=True)

    # Relaciones
    visitante        = relationship("UsuarioVisitante", back_populates="propietario")
    establecimientos = relationship("PropietarioEstablecimiento", back_populates="propietario")


class Administrador(Base):
    """
    Extensión TPT de Usuario para admins (PK = FK → usuario, rama paralela).
    No hereda de UsuarioVisitante: no participa en el sistema de puntos ni de rango.
    """
    __tablename__ = "administrador"

    id_usuario   = Column(Integer, ForeignKey("usuario.id_usuario"), primary_key=True)
    nivel_admin  = Column(TINYINT, default=1, nullable=False)
    departamento = Column(String(100), nullable=True)

    # Relaciones
    usuario = relationship("Usuario", back_populates="administrador")


class UbicacionUsuario(Base):
    """
    Historial de coordenadas GPS para boosting por proximidad (Haversine).
    Política de privacidad: máximo 3 registros por usuario — ver §1.6 y §4.1.
    FastAPI elimina los excedentes en la misma transacción del INSERT.
    """
    __tablename__ = "ubicacion_usuario"
    __table_args__ = (
        Index("idx_ubicacion_usuario_fecha", "id_usuario", "fecha_registro"),
    )

    id_ubicacion     = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario       = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    latitud          = Column(DECIMAL(10, 8), nullable=False)
    longitud         = Column(DECIMAL(11, 8), nullable=False)
    precision_metros = Column(Integer, nullable=True)
    id_sesion        = Column(String(36), ForeignKey("sesion_usuario.id_sesion"), nullable=True)
    fecha_registro   = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    usuario = relationship("Usuario", back_populates="ubicaciones")
    sesion  = relationship("SesionUsuario", back_populates="ubicaciones")


# ═══════════════════════════════════════════════════════════════════════════════
# DOMINIO: ESTABLECIMIENTOS — TPT (Table-per-Type)
# ═══════════════════════════════════════════════════════════════════════════════

class Establecimiento(Base):
    """
    Entidad base TPT raíz para establecimientos gastronómicos.
    tipo_establecimiento: discriminador TPT ('restaurante', 'local', 'puesto_informal').
    es_informal: desnormalizado — ver §1.5. Boosting directo sin JOIN.
    calificacion_promedio, total_resenas: desnormalizados — ver §1.5.
    """
    __tablename__ = "establecimiento"
    __table_args__ = (
        Index("idx_establecimiento_estado_activo", "estado", "es_activo"),
        Index("idx_establecimiento_colonia", "id_colonia"),
    )

    id_establecimiento    = Column(Integer, primary_key=True, autoincrement=True)
    nombre                = Column(String(200), nullable=False)
    descripcion           = Column(Text, nullable=True)
    latitud               = Column(DECIMAL(10, 8), nullable=False)
    longitud              = Column(DECIMAL(11, 8), nullable=False)
    direccion_texto       = Column(String(500), nullable=True)
    id_colonia            = Column(Integer, ForeignKey("colonia.id_colonia"), nullable=True)
    id_cluster            = Column(
        Integer, ForeignKey("cluster_establecimiento.id_cluster"), nullable=True
    )
    vector_caracteristicas = Column(JSON, nullable=True)
    tipo_establecimiento  = Column(
        Enum("restaurante", "local", "puesto_informal"),
        nullable=False,
    )
    es_informal           = Column(Boolean, default=False, nullable=False)   # Desnormalizado §1.5
    estado                = Column(
        Enum("pendiente", "aprobado", "rechazado", "suspendido"),
        default="pendiente",
        nullable=False,
    )
    es_activo             = Column(Boolean, default=False, nullable=False)
    id_usuario_registro   = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    id_admin_aprobacion   = Column(
        Integer, ForeignKey("administrador.id_usuario"), nullable=True
    )
    fecha_registro        = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_aprobacion      = Column(DateTime, nullable=True)
    total_resenas         = Column(Integer, default=0)              # Desnormalizado §1.5
    calificacion_promedio = Column(DECIMAL(3, 2), default=0.00)     # Desnormalizado §1.5

    # Relaciones
    colonia         = relationship("Colonia", back_populates="establecimientos")
    cluster         = relationship("ClusterEstablecimiento", back_populates="establecimientos")
    usuario_registro = relationship(
        "Usuario",
        foreign_keys=[id_usuario_registro],
        back_populates="establecimientos_registrados",
    )
    restaurante     = relationship("Restaurante", back_populates="establecimiento", uselist=False)
    local_comercial = relationship("LocalComercial", back_populates="establecimiento", uselist=False)
    puesto_informal = relationship("PuestoInformal", back_populates="establecimiento", uselist=False)
    propietarios    = relationship("PropietarioEstablecimiento", back_populates="establecimiento")
    categorias      = relationship("EstablecimientoCategoria", back_populates="establecimiento")
    etiquetas       = relationship("EstablecimientoEtiqueta", back_populates="establecimiento")
    platillos       = relationship("Platillo", back_populates="establecimiento")
    imagenes        = relationship("Imagen", back_populates="establecimiento")
    horarios        = relationship("Horario", back_populates="establecimiento")
    metrica         = relationship("MetricaEstablecimiento", back_populates="establecimiento", uselist=False)
    interacciones   = relationship("InteraccionUsuario", back_populates="establecimiento")
    recomendaciones = relationship("RecomendacionGenerada", back_populates="establecimiento")
    resenas         = relationship("Resena", back_populates="establecimiento")
    favoritos       = relationship("FavoritoGuardado", back_populates="establecimiento")
    historial_visitas = relationship("HistorialVisita", back_populates="establecimiento")
    contribuciones  = relationship("ContribucionInformacion", back_populates="establecimiento")
    reportes        = relationship("Reporte", back_populates="establecimiento")


class Restaurante(Base):
    """
    Extensión TPT de Establecimiento para restaurantes formales.
    id_restaurante (PK) = FK → establecimiento.id_establecimiento.
    """
    __tablename__ = "restaurante"

    id_restaurante        = Column(
        Integer, ForeignKey("establecimiento.id_establecimiento"), primary_key=True
    )
    id_categoria_principal = Column(Integer, ForeignKey("categoria.id_categoria"), nullable=True)
    capacidad             = Column(Integer, nullable=True)
    acepta_reservaciones  = Column(Boolean, default=False, nullable=False)
    servicio_domicilio    = Column(Boolean, default=False, nullable=False)
    telefono              = Column(String(20), nullable=True)
    sitio_web             = Column(String(500), nullable=True)
    facebook_url          = Column(String(500), nullable=True)
    instagram_url         = Column(String(500), nullable=True)
    precio_promedio       = Column(DECIMAL(8, 2), nullable=True)

    # Relaciones
    establecimiento    = relationship("Establecimiento", back_populates="restaurante")
    categoria_principal = relationship("Categoria", back_populates="restaurantes")


class LocalComercial(Base):
    """
    Extensión TPT de Establecimiento para locales en mercados o edificios.
    Nombre 'local_comercial' — LOCAL es keyword reservada en MySQL (ver §1.1).
    id_local (PK) = FK → establecimiento.id_establecimiento.
    """
    __tablename__ = "local_comercial"

    id_local           = Column(
        Integer, ForeignKey("establecimiento.id_establecimiento"), primary_key=True
    )
    numero_local       = Column(String(20), nullable=True)
    nivel_piso         = Column(String(10), nullable=True)
    nombre_edificio    = Column(String(200), nullable=True)
    tiene_area_comedor = Column(Boolean, default=True, nullable=False)

    # Relaciones
    establecimiento = relationship("Establecimiento", back_populates="local_comercial")


class PuestoInformal(Base):
    """
    Extensión TPT de Establecimiento para puestos y carritos informales.
    id_puesto (PK) = FK → establecimiento.id_establecimiento.
    dias_tipicos y horario_aproximado son texto libre (no FK a horario)
    porque los puestos informales no tienen horarios rígidos — ver §4.3.
    """
    __tablename__ = "puesto_informal"

    id_puesto            = Column(
        Integer, ForeignKey("establecimiento.id_establecimiento"), primary_key=True
    )
    es_movil             = Column(Boolean, default=False, nullable=False)
    ubicacion_referencia = Column(Text, nullable=True)
    dias_tipicos         = Column(String(100), nullable=True)
    horario_aproximado   = Column(String(100), nullable=True)

    # Relaciones
    establecimiento = relationship("Establecimiento", back_populates="puesto_informal")


class PropietarioEstablecimiento(Base):
    """
    Tabla pivote N:M con metadatos: un propietario puede tener múltiples
    establecimientos. Cada vínculo requiere aprobación individual del admin.
    """
    __tablename__ = "propietario_establecimiento"

    id_propietario      = Column(
        Integer, ForeignKey("usuario_propietario.id_usuario"), primary_key=True
    )
    id_establecimiento  = Column(
        Integer, ForeignKey("establecimiento.id_establecimiento"), primary_key=True
    )
    estado              = Column(
        Enum("pendiente", "aprobado", "rechazado"),
        default="pendiente",
        nullable=False,
    )
    fecha_solicitud     = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_aprobacion    = Column(DateTime, nullable=True)
    id_admin_aprobacion = Column(Integer, ForeignKey("administrador.id_usuario"), nullable=True)
    documento_prueba    = Column(String(500), nullable=True)

    # Relaciones
    propietario    = relationship("UsuarioPropietario", back_populates="establecimientos")
    establecimiento = relationship("Establecimiento", back_populates="propietarios")


# ═══════════════════════════════════════════════════════════════════════════════
# DOMINIO: CONTENIDO — Tablas de contenido vinculadas a Establecimientos
# ═══════════════════════════════════════════════════════════════════════════════

class EstablecimientoCategoria(Base):
    """Pivote N:M entre Establecimiento y Categoria."""
    __tablename__ = "establecimiento_categoria"

    id_establecimiento = Column(
        Integer, ForeignKey("establecimiento.id_establecimiento"), primary_key=True
    )
    id_categoria = Column(Integer, ForeignKey("categoria.id_categoria"), primary_key=True)

    # Relaciones
    establecimiento = relationship("Establecimiento", back_populates="categorias")
    categoria       = relationship("Categoria", back_populates="establecimientos")


class EstablecimientoEtiqueta(Base):
    """Pivote N:M entre Establecimiento y Etiqueta."""
    __tablename__ = "establecimiento_etiqueta"

    id_establecimiento = Column(
        Integer, ForeignKey("establecimiento.id_establecimiento"), primary_key=True
    )
    id_etiqueta = Column(Integer, ForeignKey("etiqueta.id_etiqueta"), primary_key=True)

    # Relaciones
    establecimiento = relationship("Establecimiento", back_populates="etiquetas")
    etiqueta        = relationship("Etiqueta", back_populates="establecimientos")


class Platillo(Base):
    """
    Platillos del menú registrados por usuarios.
    estado: sujeto a moderación por admins ('pendiente' → 'aprobado' / 'rechazado').
    """
    __tablename__ = "platillo"

    id_platillo         = Column(Integer, primary_key=True, autoincrement=True)
    id_establecimiento  = Column(
        Integer, ForeignKey("establecimiento.id_establecimiento"), nullable=False
    )
    nombre              = Column(String(200), nullable=False)
    descripcion         = Column(Text, nullable=True)
    precio              = Column(DECIMAL(8, 2), nullable=True)
    disponible          = Column(Boolean, default=True, nullable=False)
    id_usuario_registro = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    estado              = Column(
        Enum("pendiente", "aprobado", "rechazado"),
        default="pendiente",
        nullable=False,
    )
    fecha_registro = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    establecimiento = relationship("Establecimiento", back_populates="platillos")


class Imagen(Base):
    """
    Imágenes asociadas a un establecimiento.
    es_principal: invariante de FastAPI — solo una imagen principal por establecimiento.
    """
    __tablename__ = "imagen"

    id_imagen          = Column(Integer, primary_key=True, autoincrement=True)
    id_establecimiento = Column(
        Integer, ForeignKey("establecimiento.id_establecimiento"), nullable=False
    )
    url_imagen         = Column(String(500), nullable=False)
    tipo               = Column(
        Enum("exterior", "interior", "platillo", "menu", "otro"),
        default="otro",
        nullable=False,
    )
    id_usuario_upload = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    fecha_upload      = Column(DateTime, default=datetime.utcnow, nullable=False)
    estado            = Column(
        Enum("pendiente", "aprobado", "rechazado"),
        default="pendiente",
        nullable=False,
    )
    es_principal = Column(Boolean, default=False, nullable=False)

    # Relaciones
    establecimiento = relationship("Establecimiento", back_populates="imagenes")


class Horario(Base):
    """
    Horarios estructurados por día de semana (Restaurantes y Locales).
    dia_semana: 0 = Domingo … 6 = Sábado (TINYINT).
    UNIQUE(id_establecimiento, dia_semana): exactamente 1 registro por día.
    """
    __tablename__ = "horario"
    __table_args__ = (
        UniqueConstraint(
            "id_establecimiento", "dia_semana", name="uq_horario_estab_dia"
        ),
    )

    id_horario         = Column(Integer, primary_key=True, autoincrement=True)
    id_establecimiento = Column(
        Integer, ForeignKey("establecimiento.id_establecimiento"), nullable=False
    )
    dia_semana    = Column(TINYINT, nullable=False)   # 0=Domingo … 6=Sábado
    hora_apertura = Column(Time, nullable=True)
    hora_cierre   = Column(Time, nullable=True)
    cerrado       = Column(Boolean, default=False, nullable=False)

    # Relaciones
    establecimiento = relationship("Establecimiento", back_populates="horarios")


# ═══════════════════════════════════════════════════════════════════════════════
# DOMINIO: MOTOR DE RECOMENDACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

class MetricaEstablecimiento(Base):
    """
    Scores pre-computados del motor. Actualización SOLO por jobs offline — ver §1.7.
    FastAPI NUNCA escribe en esta tabla (solo SELECT) — ver §7.
    PK = FK → establecimiento (relación 1:1).
    """
    __tablename__ = "metrica_establecimiento"

    id_establecimiento      = Column(
        Integer, ForeignKey("establecimiento.id_establecimiento"), primary_key=True
    )
    score_contenido_base    = Column(DECIMAL(5, 4), nullable=True)
    score_colaborativo_base = Column(DECIMAL(5, 4), nullable=True)
    boost_proximidad_zona   = Column(DECIMAL(5, 4), nullable=True)
    boost_informal          = Column(DECIMAL(3, 2), nullable=True)
    score_boost_combinado   = Column(DECIMAL(5, 4), nullable=True)   # Desnormalizado §1.5
    popularidad_7d          = Column(Integer, nullable=True)          # Desnormalizado §1.5
    popularidad_30d         = Column(Integer, nullable=True)          # Desnormalizado §1.5
    polaridad_promedio      = Column(DECIMAL(4, 3), nullable=True)    # Desnormalizado §1.5 — job NLP
    ultima_actualizacion    = Column(DateTime, nullable=True)

    # Relaciones
    establecimiento = relationship("Establecimiento", back_populates="metrica")


class InteraccionUsuario(Base):
    """
    Señal granular para el filtrado colaborativo. Mayor volumen del sistema.
    peso_interaccion: desnormalizado al insertar — ver §1.5.
    Política de archivado: 90 días activos → interaccion_usuario_historico — ver §6.2.
    """
    __tablename__ = "interaccion_usuario"
    __table_args__ = (
        Index("idx_interaccion_usuario_fecha", "id_usuario", "fecha"),
        Index("idx_interaccion_estab_fecha", "id_establecimiento", "fecha"),
    )

    id_interaccion     = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario         = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    id_establecimiento = Column(
        Integer, ForeignKey("establecimiento.id_establecimiento"), nullable=False
    )
    tipo_interaccion   = Column(
        Enum(
            "vista_detalle", "guardado_favorito", "compartido",
            "llamada_telefono", "abrir_maps", "resena_dejada", "ruta_calculada",
        ),
        nullable=False,
    )
    peso_interaccion = Column(DECIMAL(3, 2), nullable=True)          # Desnormalizado §1.5
    id_sesion        = Column(String(36), ForeignKey("sesion_usuario.id_sesion"), nullable=True)
    fecha            = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    usuario         = relationship("Usuario", back_populates="interacciones")
    establecimiento = relationship("Establecimiento", back_populates="interacciones")
    sesion          = relationship("SesionUsuario", back_populates="interacciones")


class RecomendacionGenerada(Base):
    """
    Caché del motor: resultado de los jobs offline.
    FastAPI SOLO actualiza fue_clickeada y fecha_click (feedback implícito) — ver §7.
    categoria_recomendacion: discriminador para secciones del frontend — ver §1.8.
    radio_usado_km: obligatorio en TODAS las categorías — ver §7.
    Política de retención TTL 7 días (30 días si fue_clickeada) — ver §6.1.
    """
    __tablename__ = "recomendacion_generada"
    __table_args__ = (
        Index(
            "idx_recomendacion_usuario_categoria",
            "id_usuario", "categoria_recomendacion", "fecha_generacion",
        ),
        Index("idx_recomendacion_usuario_estab", "id_usuario", "id_establecimiento"),
    )

    id_recomendacion         = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario               = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    id_establecimiento       = Column(
        Integer, ForeignKey("establecimiento.id_establecimiento"), nullable=False
    )
    categoria_recomendacion  = Column(
        Enum(
            "cercania", "popularidad_zona", "preferencia_contenido",
            "colaborativo_cluster", "cold_start", "descubrimiento", "tendencia_informal",
        ),
        nullable=False,
    )
    posicion                 = Column(TINYINT, nullable=False)
    score_total              = Column(DECIMAL(5, 4), nullable=True)
    score_contenido_usado    = Column(DECIMAL(5, 4), nullable=True)
    score_colaborativo_usado = Column(DECIMAL(5, 4), nullable=True)
    score_boost_aplicado     = Column(DECIMAL(5, 4), nullable=True)
    distancia_km             = Column(DECIMAL(8, 3), nullable=True)
    radio_usado_km           = Column(TINYINT, nullable=False)
    fallback_nivel           = Column(TINYINT, default=0, nullable=False)
    razon_principal          = Column(
        Enum(
            "preferencia_categoria", "historial_similar", "popular_zona",
            "colaborativo", "cluster_similar", "cercano", "cold_start",
            "descubrimiento", "tendencia_informal",
        ),
        nullable=True,
    )
    detalle_razon            = Column(String(200), nullable=True)
    estrategia_usada         = Column(
        Enum("contenido", "colaborativo", "cold_start", "hibrido", "cluster", "popularidad", "serendipia"),
        nullable=True,
    )
    fecha_generacion  = Column(DateTime, nullable=False)
    fue_clickeada     = Column(Boolean, default=False, nullable=False)
    fecha_click       = Column(DateTime, nullable=True)
    es_descubrimiento = Column(Boolean, default=False, nullable=False)
    diversity_score   = Column(DECIMAL(5, 4), nullable=True)

    # Relaciones
    establecimiento  = relationship("Establecimiento", back_populates="recomendaciones")
    historial_visitas = relationship("HistorialVisita", back_populates="recomendacion")


# ═══════════════════════════════════════════════════════════════════════════════
# DOMINIO: INTERACCIONES Y GAMIFICACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

class ContribucionInformacion(Base):
    """
    Contribuciones de usuarios al sistema (nuevos lugares, ediciones, fotos).
    id_establecimiento nullable: NULL cuando se registra un lugar nuevo.
    """
    __tablename__ = "contribucion_informacion"
    __table_args__ = (
        Index("idx_contribucion_usuario_estado", "id_usuario", "estado"),
    )

    id_contribucion    = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario         = Column(
        Integer, ForeignKey("usuario_visitante.id_usuario"), nullable=False
    )
    id_establecimiento = Column(
        Integer, ForeignKey("establecimiento.id_establecimiento"), nullable=True
    )
    tipo_contribucion  = Column(
        Enum("nuevo_lugar", "edicion_info", "nueva_foto", "nuevo_platillo", "nueva_resena"),
        nullable=False,
    )
    descripcion_cambio = Column(Text, nullable=True)
    estado             = Column(
        Enum("pendiente", "aprobado", "rechazado"),
        default="pendiente",
        nullable=False,
    )
    id_admin_revision  = Column(Integer, ForeignKey("administrador.id_usuario"), nullable=True)
    fecha_contribucion = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_revision     = Column(DateTime, nullable=True)
    puntos_otorgados   = Column(Integer, default=0)

    # Relaciones
    usuario_visitante = relationship("UsuarioVisitante", back_populates="contribuciones")
    establecimiento   = relationship("Establecimiento", back_populates="contribuciones")
    log_puntos        = relationship("LogPuntos", back_populates="contribucion")


class LogPuntos(Base):
    """
    Registro INMUTABLE de auditoría de puntos. Solo crece, nunca se modifica.
    puntos_experiencia en usuario_visitante es la suma materializada — ver §1.5.
    """
    __tablename__ = "log_puntos"

    id_log          = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario      = Column(
        Integer, ForeignKey("usuario_visitante.id_usuario"), nullable=False
    )
    puntos          = Column(Integer, nullable=False)
    motivo          = Column(
        Enum(
            "contribucion_aprobada", "resena_aprobada", "foto_aprobada",
            "nuevo_lugar", "penalizacion", "subida_rango",
        ),
        nullable=False,
    )
    id_contribucion = Column(
        Integer, ForeignKey("contribucion_informacion.id_contribucion"), nullable=True
    )
    fecha = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    usuario_visitante = relationship("UsuarioVisitante", back_populates="log_puntos")
    contribucion      = relationship("ContribucionInformacion", back_populates="log_puntos")


class Resena(Base):
    """
    Reseñas de usuarios sobre establecimientos.
    calificacion: CHECK(1-5) — validación OBLIGATORIA en Pydantic (MySQL <8.0 ignora CHECK).
    polaridad/subjetividad: calculados por job NLP offline.
    UNIQUE(id_usuario, id_establecimiento): una reseña por usuario por establecimiento.
    """
    __tablename__ = "resena"
    __table_args__ = (
        UniqueConstraint("id_usuario", "id_establecimiento", name="uq_resena_usuario_estab"),
        CheckConstraint("calificacion >= 1 AND calificacion <= 5", name="ck_resena_calificacion"),
        Index("idx_resena_estab_estado", "id_establecimiento", "estado"),
        Index("idx_resena_procesado_nlp", "procesado_nlp"),
    )

    id_resena          = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario         = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    id_establecimiento = Column(
        Integer, ForeignKey("establecimiento.id_establecimiento"), nullable=False
    )
    calificacion      = Column(TINYINT, nullable=False)    # CHECK(1-5) en tabla y Pydantic
    comentario        = Column(Text, nullable=True)
    fecha_resena      = Column(DateTime, default=datetime.utcnow, nullable=False)
    estado            = Column(
        Enum("pendiente", "aprobado", "rechazado"),
        default="pendiente",
        nullable=False,
    )
    id_admin_revision = Column(Integer, ForeignKey("administrador.id_usuario"), nullable=True)
    fecha_revision    = Column(DateTime, nullable=True)
    polaridad         = Column(DECIMAL(4, 3), nullable=True)    # Job NLP offline
    subjetividad      = Column(DECIMAL(4, 3), nullable=True)    # Job NLP offline
    procesado_nlp     = Column(Boolean, default=False, nullable=False)

    # Relaciones
    usuario         = relationship("Usuario", back_populates="resenas")
    establecimiento = relationship("Establecimiento", back_populates="resenas")


class FavoritoGuardado(Base):
    """
    Pivote N:M: establecimientos guardados como favoritos por un usuario visitante.
    Genera señal de interacción (peso = 0.5) para el filtrado colaborativo.
    """
    __tablename__ = "favorito_guardado"

    id_usuario         = Column(
        Integer, ForeignKey("usuario_visitante.id_usuario"), primary_key=True
    )
    id_establecimiento = Column(
        Integer, ForeignKey("establecimiento.id_establecimiento"), primary_key=True
    )
    fecha_guardado = Column(DateTime, default=datetime.utcnow, nullable=False)
    nota_personal  = Column(Text, nullable=True)

    # Relaciones
    usuario_visitante = relationship("UsuarioVisitante", back_populates="favoritos")
    establecimiento   = relationship("Establecimiento", back_populates="favoritos")


class HistorialVisita(Base):
    """
    Registro de vistas de detalle de un usuario a un establecimiento.
    fue_recomendado + id_recomendacion: permiten medir el CTR del motor.
    """
    __tablename__ = "historial_visita"
    __table_args__ = (
        Index("idx_historial_usuario_fecha", "id_usuario", "fecha_visita"),
        Index(
            "idx_historial_usuario_estab_fecha",
            "id_usuario", "id_establecimiento", "fecha_visita",
        ),
    )

    id_visita          = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario         = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    id_establecimiento = Column(
        Integer, ForeignKey("establecimiento.id_establecimiento"), nullable=False
    )
    id_sesion          = Column(String(36), ForeignKey("sesion_usuario.id_sesion"), nullable=True)
    fecha_visita       = Column(DateTime, default=datetime.utcnow, nullable=False)
    duracion_segundos  = Column(Integer, nullable=True)
    fue_recomendado    = Column(Boolean, default=False, nullable=False)
    id_recomendacion   = Column(
        Integer, ForeignKey("recomendacion_generada.id_recomendacion"), nullable=True
    )

    # Relaciones
    usuario         = relationship("Usuario", back_populates="historial_visitas")
    establecimiento = relationship("Establecimiento", back_populates="historial_visitas")
    sesion          = relationship("SesionUsuario", back_populates="historial")
    recomendacion   = relationship("RecomendacionGenerada", back_populates="historial_visitas")


class PreferenciaUsuario(Base):
    """
    Pivote N:M: preferencias de categorías con peso de afinidad.
    Fuente de verdad para construir vector_preferencias en el onboarding.
    peso ∈ [0.00, 1.00].
    """
    __tablename__ = "preferencia_usuario"

    id_usuario   = Column(
        Integer, ForeignKey("usuario_visitante.id_usuario"), primary_key=True
    )
    id_categoria = Column(Integer, ForeignKey("categoria.id_categoria"), primary_key=True)
    peso                = Column(DECIMAL(3, 2), default=0.50)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    usuario_visitante = relationship("UsuarioVisitante", back_populates="preferencias")
    categoria         = relationship("Categoria", back_populates="preferencias")


class Reporte(Base):
    """Reportes de usuarios sobre establecimientos (información incorrecta, lugar cerrado…)."""
    __tablename__ = "reporte"

    id_reporte          = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario          = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    id_establecimiento  = Column(
        Integer, ForeignKey("establecimiento.id_establecimiento"), nullable=False
    )
    tipo_reporte        = Column(
        Enum("informacion_incorrecta", "lugar_cerrado", "contenido_inapropiado", "spam", "otro"),
        nullable=False,
    )
    descripcion         = Column(Text, nullable=True)
    estado              = Column(
        Enum("pendiente", "resuelto", "descartado"),
        default="pendiente",
        nullable=False,
    )
    fecha_reporte       = Column(DateTime, default=datetime.utcnow, nullable=False)
    id_admin_resolucion = Column(Integer, ForeignKey("administrador.id_usuario"), nullable=True)

    # Relaciones
    usuario         = relationship("Usuario", back_populates="reportes")
    establecimiento = relationship("Establecimiento", back_populates="reportes")


# ═══════════════════════════════════════════════════════════════════════════════
# TABLAS DE ARCHIVADO — §6 del diseño
# Sin FKs (datos archivados deben ser independientes).
# Sin índices secundarios (no se consultan desde el motor).
# ═══════════════════════════════════════════════════════════════════════════════

class RecomendacionGeneradaHistorico(Base):
    """
    Archivado de recomendacion_generada con fecha_generacion > 7 días.
    Excepción: filas con fue_clickeada=TRUE se retienen 30 días adicionales.
    Sin FKs — datos archivados son independientes del DELETE de usuarios/establecimientos.
    Sin índices secundarios — solo para auditoría, no para el motor.
    Política de archivado: ver §6.1.
    """
    __tablename__ = "recomendacion_generada_historico"

    id_recomendacion         = Column(Integer, primary_key=True)
    id_usuario               = Column(Integer, nullable=False)
    id_establecimiento       = Column(Integer, nullable=False)
    categoria_recomendacion  = Column(String(50), nullable=True)
    posicion                 = Column(TINYINT, nullable=True)
    score_total              = Column(DECIMAL(5, 4), nullable=True)
    score_contenido_usado    = Column(DECIMAL(5, 4), nullable=True)
    score_colaborativo_usado = Column(DECIMAL(5, 4), nullable=True)
    score_boost_aplicado     = Column(DECIMAL(5, 4), nullable=True)
    distancia_km             = Column(DECIMAL(8, 3), nullable=True)
    radio_usado_km           = Column(TINYINT, nullable=True)
    fallback_nivel           = Column(TINYINT, nullable=True)
    razon_principal          = Column(String(50), nullable=True)
    detalle_razon            = Column(String(200), nullable=True)
    estrategia_usada         = Column(String(20), nullable=True)
    fecha_generacion         = Column(DateTime, nullable=True)
    fue_clickeada            = Column(Boolean, nullable=True)
    fecha_click              = Column(DateTime, nullable=True)
    es_descubrimiento        = Column(Boolean, nullable=True)
    diversity_score          = Column(DECIMAL(5, 4), nullable=True)


class InteraccionUsuarioHistorico(Base):
    """
    Archivado de interaccion_usuario con fecha > 90 días.
    Sin FKs — datos archivados son independientes.
    Sin índices secundarios — no se consulta desde el motor.
    Política de archivado: ver §6.2.
    """
    __tablename__ = "interaccion_usuario_historico"

    id_interaccion     = Column(Integer, primary_key=True)
    id_usuario         = Column(Integer, nullable=False)
    id_establecimiento = Column(Integer, nullable=False)
    tipo_interaccion   = Column(String(30), nullable=True)
    peso_interaccion   = Column(DECIMAL(3, 2), nullable=True)
    id_sesion          = Column(String(36), nullable=True)
    fecha              = Column(DateTime, nullable=True)
