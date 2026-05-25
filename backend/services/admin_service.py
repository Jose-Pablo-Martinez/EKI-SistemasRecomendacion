from sqlalchemy.orm import Session
from backend.models.establecimientos import Establecimiento
from backend.models.interacciones import Resena
from backend.services.gamificacion_service import otorgar_puntos
from sqlalchemy.sql import func

def aprobar_establecimiento(db: Session, id_establecimiento: int) -> bool:
    est = db.query(Establecimiento).filter(Establecimiento.id_establecimiento == id_establecimiento).first()
    if not est or est.estado != "pendiente":
        return False
        
    est.estado = "aprobado"  # type: ignore[assignment]
    # Otorgar puntos al usuario que lo propuso
    otorgar_puntos(db, est.id_usuario_registro, "nuevo_lugar", f"Lugar aprobado: {est.nombre}")
    db.commit()
    return True

def rechazar_establecimiento(db: Session, id_establecimiento: int) -> bool:
    est = db.query(Establecimiento).filter(Establecimiento.id_establecimiento == id_establecimiento).first()
    if not est or est.estado != "pendiente":
        return False
        
    est.estado = "rechazado"  # type: ignore[assignment]
    db.commit()
    return True


def aprobar_resena(db: Session, id_resena: int) -> bool:
    resena = db.query(Resena).filter(Resena.id_resena == id_resena).first()
    if not resena or resena.estado != "pendiente":
        return False
        
    resena.estado = "aprobado"  # type: ignore[assignment]
    resena.procesado_nlp = False  # type: ignore[assignment] — Para que el NLP lo pase a analizar
    
    # Recalcular desnormalizados de establecimiento
    est = db.query(Establecimiento).filter(Establecimiento.id_establecimiento == resena.id_establecimiento).first()
    if est:
        # Calcular nuevo promedio y total
        stats = db.query(
            func.count(Resena.id_resena).label("total"),
            func.avg(Resena.calificacion).label("promedio")
        ).filter(
            Resena.id_establecimiento == resena.id_establecimiento,
            Resena.estado == "aprobado"
        ).first()
        
        est.total_resenas = stats.total if stats else 0  # type: ignore[assignment]
        est.calificacion_promedio = float(stats.promedio) if stats and stats.promedio else 0.0  # type: ignore[assignment]

    otorgar_puntos(db, resena.id_usuario, "crear_resena", f"Reseña aprobada en {resena.id_establecimiento}")
    db.commit()
    return True

def obtener_establecimientos_pendientes(db: Session):
    return db.query(Establecimiento).filter(Establecimiento.estado == "pendiente").all()

def obtener_resenas_pendientes(db: Session):
    return db.query(Resena).filter(Resena.estado == "pendiente").all()

def disparar_job(tipo_job: str):
    from backend.jobs.runner import run_job
    from backend.database import SessionLocal
    return run_job(tipo_job, SessionLocal)
