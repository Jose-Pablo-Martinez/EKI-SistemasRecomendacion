import threading
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.usuarios import Administrador
from backend.auth import get_current_admin
from backend.services import admin_service
from backend.jobs.reconciliacion import reconciliar_campos_desnormalizados

router = APIRouter(prefix="/admin", tags=["Administración"])

@router.get("/pendientes")
def listar_pendientes(current_admin: Administrador = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Lista todos los establecimientos pendientes de aprobación."""
    return admin_service.obtener_pendientes(db)

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

@router.post("/jobs/reconciliacion")
def run_reconciliacion(current_admin: Administrador = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Dispara el job asíncrono de reconciliación de datos."""
    # Como placeholder de la arquitectura, usamos un hilo para no bloquear.
    # En producción se usará Celery o colas de AWS.
    thread = threading.Thread(target=reconciliar_campos_desnormalizados, args=(db,))
    thread.start()
    return {"status": "ok", "message": "Job de reconciliación iniciado en background"}
