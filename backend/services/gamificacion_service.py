import logging
from sqlalchemy.orm import Session
from backend.models.interacciones import LogPuntos, ContribucionInformacion
from backend.models.usuarios import UsuarioVisitante
from backend.schemas.recomendaciones import ContribucionCreate

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

def otorgar_puntos(db: Session, id_usuario: int, accion: str, descripcion: str = "", id_contribucion: int = None):
    puntos = PUNTOS_POR_ACCION.get(accion, 0)
    if puntos <= 0:
        return
        
    log = LogPuntos(
        id_usuario=id_usuario,
        puntos=puntos,
        motivo=_accion_a_motivo(accion),
        id_contribucion=id_contribucion
    )
    db.add(log)
    
    # Actualizar desnormalizado
    visitante = db.query(UsuarioVisitante).filter(UsuarioVisitante.id_usuario == id_usuario).first()
    if visitante:
        visitante.puntos_experiencia += puntos
        
    db.commit()
    logger.info(f"Otorgados {puntos} pts a {id_usuario} por {accion}")

def obtener_historial_puntos(db: Session, id_usuario: int):
    return db.query(LogPuntos).filter(LogPuntos.id_usuario == id_usuario).order_by(LogPuntos.fecha.desc()).all()
