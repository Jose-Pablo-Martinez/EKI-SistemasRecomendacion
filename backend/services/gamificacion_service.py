import logging
from sqlalchemy.orm import Session
from backend.models.interacciones import LogPuntos, ContribucionInformacion
from backend.models.usuarios import UsuarioVisitante
from backend.models.catalogo import RangoInformador
from backend.schemas.recomendaciones import ContribucionCreate
from typing import Optional

logger = logging.getLogger(__name__)

# Diccionario de reglas base
PUNTOS_POR_ACCION = {
    "crear_resena": 10,
    "nuevo_lugar": 50,
    "editar_lugar": 20,
    "reporte_valido": 15,
    "nueva_foto": 15,
    "nuevo_platillo": 10
}

# Mapeo de acciones internas al ENUM del modelo
_MOTIVO_MAP = {
    "crear_resena": "resena_aprobada",
    "nuevo_lugar": "nuevo_lugar",
    "editar_lugar": "contribucion_aprobada",
    "reporte_valido": "contribucion_aprobada",
    "nueva_foto": "foto_aprobada",
    "nuevo_platillo": "contribucion_aprobada",
}

def _accion_a_motivo(accion: str) -> str:
    return _MOTIVO_MAP.get(accion, "contribucion_aprobada")

def registrar_contribucion(db: Session, id_usuario: int, datos: ContribucionCreate):
    contribucion = ContribucionInformacion(
        id_usuario=id_usuario,
        id_establecimiento=datos.id_establecimiento,
        tipo_contribucion=datos.tipo_contribucion,
        descripcion_cambio=datos.descripcion_cambio,
        estado="pendiente",
        puntos_otorgados=0
    )
    db.add(contribucion)
    db.commit()
    db.refresh(contribucion)
    return contribucion

def otorgar_puntos(db: Session, id_usuario: int, accion: str, descripcion: str = "", id_contribucion: Optional[int] = None):
    puntos = PUNTOS_POR_ACCION.get(accion, 0)
    if puntos <= 0:
        return

    # `log_puntos.id_usuario` referencia a `usuario_visitante.id_usuario`.
    # Si el usuario no participa en gamificación (p.ej. admin), evitamos violar la FK.
    visitante = db.query(UsuarioVisitante).filter(UsuarioVisitante.id_usuario == id_usuario).first()
    if not visitante:
        logger.warning("No se otorgaron puntos: usuario %s no es visitante", id_usuario)
        return
        
    log = LogPuntos(
        id_usuario=id_usuario,
        puntos=puntos,
        motivo=_accion_a_motivo(accion),
        id_contribucion=id_contribucion
    )
    db.add(log)
    
    # Actualizar desnormalizado con protección contra None
    visitante.puntos_experiencia = (visitante.puntos_experiencia or 0) + puntos  # type: ignore[assignment]
    
    # Verificar subida de rango automáticamente con base en puntos_experiencia
    nuevo_rango = db.query(RangoInformador).filter(
        RangoInformador.puntos_minimos <= visitante.puntos_experiencia
    ).order_by(RangoInformador.puntos_minimos.desc()).first()
    
    if nuevo_rango and (visitante.id_rango != nuevo_rango.id_rango):
        visitante.id_rango = nuevo_rango.id_rango  # type: ignore[assignment]
        # Opcional: registrar motivo 'subida_rango' en log_puntos para el historial
        log_subida = LogPuntos(
            id_usuario=id_usuario,
            puntos=0,
            motivo="subida_rango"
        )
        db.add(log_subida)
            
    db.commit()
    logger.info(f"Otorgados {puntos} pts a {id_usuario} por {accion}")

def obtener_historial_puntos(db: Session, id_usuario: int):
    return db.query(LogPuntos).filter(LogPuntos.id_usuario == id_usuario).order_by(LogPuntos.fecha.desc()).all()

def obtener_rango_actual(db: Session, id_usuario: int) -> dict:
    visitante = db.query(UsuarioVisitante).filter(UsuarioVisitante.id_usuario == id_usuario).first()
    if not visitante:
        return {"puntos_experiencia": 0, "puntos_totales": 0, "rango_actual": None}
    
    # En un sistema completo, consultaríamos la tabla RangoGamificacion
    # para determinar puntos faltantes para el próximo nivel
    return {
        "puntos_experiencia": visitante.puntos_experiencia,
        # Alias para compatibilidad con el frontend (perfil.js espera puntos_totales)
        "puntos_totales": visitante.puntos_experiencia,
        "rango_actual": visitante.id_rango
    }
