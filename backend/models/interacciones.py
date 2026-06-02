"""
Dominio: INTERACCIONES, GAMIFICACIÓN Y MOTOR DE RECOMENDACIÓN
Incluye: InteraccionUsuario, RecomendacionGenerada, HistorialVisita,
         Resena, FavoritoGuardado, PreferenciaUsuario, Reporte,
         ContribucionInformacion, LogPuntos,
         + tablas de archivado (InteraccionUsuarioHistorico, RecomendacionGeneradaHistorico)
"""
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Enum,
    ForeignKey, DECIMAL, Index, UniqueConstraint, CheckConstraint,
)
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import relationship

from backend.database import Base


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
    fecha            = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

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
    score_contenido_usado    = Column(DECIMAL(6, 4), nullable=True)
    score_colaborativo_usado = Column(DECIMAL(6, 4), nullable=True)
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
    fecha_contribucion = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
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
    fecha = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

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
    fecha_resena      = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
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
    
    @property
    def nombre_usuario(self) -> str:
        if self.usuario:
            return f"{self.usuario.nombre} {self.usuario.apellido}".strip()
        return "Usuario Anónimo"


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
    fecha_guardado = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
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
    fecha_visita       = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
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
    fecha_actualizacion = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

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
    fecha_reporte       = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
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
    score_contenido_usado    = Column(DECIMAL(6, 4), nullable=True)
    score_colaborativo_usado = Column(DECIMAL(6, 4), nullable=True)
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
