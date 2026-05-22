"""
Dominio: USUARIOS — TPT (Table-per-Type)
Jerarquía: Usuario → UsuarioVisitante → UsuarioPropietario
                   → Administrador  (rama paralela)
Dispositivos, sesiones y ubicaciones de usuario incluidos aquí.
"""
from datetime import datetime

# pyrefly: ignore [missing-import]
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Enum, JSON,
    Index, ForeignKey, DECIMAL
)
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.mysql import TINYINT
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import relationship

from backend.database import Base


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
