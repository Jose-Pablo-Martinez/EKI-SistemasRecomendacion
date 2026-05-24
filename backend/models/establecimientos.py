"""
Dominio: ESTABLECIMIENTOS — TPT (Table-per-Type)
Jerarquía raíz: Establecimiento
Subtipos: Restaurante, LocalComercial, PuestoInformal
Tablas de contenido vinculadas: Horario, Platillo, Imagen, MetricaEstablecimiento
Pivotes: EstablecimientoCategoria, EstablecimientoEtiqueta, PropietarioEstablecimiento
"""
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Enum,
    ForeignKey, JSON, DECIMAL, Index, UniqueConstraint, Time,
)
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import relationship

from backend.database import Base


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
    fecha_registro        = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
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
    fecha_solicitud     = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    fecha_aprobacion    = Column(DateTime, nullable=True)
    id_admin_aprobacion = Column(Integer, ForeignKey("administrador.id_usuario"), nullable=True)
    documento_prueba    = Column(String(500), nullable=True)

    # Relaciones
    propietario    = relationship("UsuarioPropietario", back_populates="establecimientos")
    establecimiento = relationship("Establecimiento", back_populates="propietarios")


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
    fecha_registro = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

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
    fecha_upload      = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
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
