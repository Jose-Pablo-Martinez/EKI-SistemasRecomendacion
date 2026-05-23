# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.usuarios import UsuarioVisitante
from backend.auth import get_current_user
from backend.services import establecimiento_service

router = APIRouter(prefix="/establecimientos", tags=["Establecimientos"])

@router.get("/{id_establecimiento}")
def get_establecimiento(id_establecimiento: int, db: Session = Depends(get_db)):
    """Obtiene el detalle de un establecimiento."""
    est = establecimiento_service.obtener_establecimiento(db, id_establecimiento)
    if not est:
        raise HTTPException(status_code=404, detail="Establecimiento no encontrado")
    return est

@router.post("/")
def create_establecimiento(datos: dict, current_user: UsuarioVisitante = Depends(get_current_user), db: Session = Depends(get_db)):
    """Propone un nuevo establecimiento. Queda en estado pendiente."""
    # Validación simple
    for campo in ["nombre", "latitud", "longitud"]:
        if campo not in datos:
            raise HTTPException(status_code=422, detail=f"Falta el campo {campo}")
            
    est = establecimiento_service.crear_establecimiento(db, current_user.id_usuario, datos)
    return est

@router.post("/{id_establecimiento}/interaccion")
def registrar_interaccion(id_establecimiento: int, tipo: str, id_sesion: str = None, current_user: UsuarioVisitante = Depends(get_current_user), db: Session = Depends(get_db)):
    """Registra una interaccion (vista, click, ruta) para los análisis de recomendación."""
    establecimiento_service.registrar_interaccion(db, current_user.id_usuario, id_establecimiento, tipo, id_sesion)
    return {"status": "ok"}
