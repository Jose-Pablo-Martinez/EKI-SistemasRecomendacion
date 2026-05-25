import threading
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.usuarios import Administrador
from backend.auth import get_current_admin
from backend.services import admin_service

router = APIRouter(prefix="/admin", tags=["Administración"])

@router.get("/establecimientos/pendientes")
def listar_establecimientos_pendientes(current_admin: Administrador = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Lista todos los establecimientos pendientes de aprobación."""
    return admin_service.obtener_establecimientos_pendientes(db)

@router.get("/resenas/pendientes")
def listar_resenas_pendientes(current_admin: Administrador = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Lista todas las reseñas pendientes de aprobación."""
    return admin_service.obtener_resenas_pendientes(db)

@router.post("/establecimientos/{id_establecimiento}/aprobar")
def aprobar_establecimiento(id_establecimiento: int, current_admin: Administrador = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Aprueba un establecimiento y otorga puntos al usuario."""
    exito = admin_service.aprobar_establecimiento(db, id_establecimiento)
    if not exito:
        raise HTTPException(status_code=400, detail="No se pudo aprobar (no existe o no está pendiente)")
    return {"status": "ok", "message": "Aprobado"}

@router.post("/establecimientos/{id_establecimiento}/rechazar")
def rechazar_establecimiento(id_establecimiento: int, current_admin: Administrador = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Rechaza un establecimiento propuesto."""
    exito = admin_service.rechazar_establecimiento(db, id_establecimiento)
    if not exito:
        raise HTTPException(status_code=400, detail="No se pudo rechazar")
    return {"status": "ok", "message": "Rechazado"}

@router.post("/resenas/{id_resena}/aprobar")
def aprobar_resena(id_resena: int, current_admin: Administrador = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Aprueba una reseña pendiente."""
    exito = admin_service.aprobar_resena(db, id_resena)
    if not exito:
        raise HTTPException(status_code=400, detail="No se pudo aprobar")
    return {"status": "ok", "message": "Reseña aprobada"}

@router.post("/jobs/{tipo_job}")
def trigger_job(tipo_job: str, current_admin: Administrador = Depends(get_current_admin)):
    """Dispara un job asíncrono."""
    resultado = admin_service.disparar_job(tipo_job)
    return resultado
