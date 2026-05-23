# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from backend.models.establecimientos import Establecimiento
from backend.models.interacciones import Resena
from backend.services.gamificacion_service import otorgar_puntos

def aprobar_establecimiento(db: Session, id_establecimiento: int) -> bool:
    est = db.query(Establecimiento).filter(Establecimiento.id_establecimiento == id_establecimiento).first()
    if not est or est.estado != "pendiente":
        return False
        
    est.estado = "aprobado"
    # Otorgar puntos al usuario que lo propuso
    otorgar_puntos(db, est.id_usuario_registro, "nuevo_lugar", f"Lugar aprobado: {est.nombre}")
    db.commit()
    return True

def rechazar_establecimiento(db: Session, id_establecimiento: int) -> bool:
    est = db.query(Establecimiento).filter(Establecimiento.id_establecimiento == id_establecimiento).first()
    if not est or est.estado != "pendiente":
        return False
        
    est.estado = "rechazado"
    db.commit()
    return True

def obtener_pendientes(db: Session):
    return db.query(Establecimiento).filter(Establecimiento.estado == "pendiente").all()
