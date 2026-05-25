from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.usuarios import UsuarioVisitante
from backend.auth import get_current_user
from backend.services import gamificacion_service
from backend.schemas.recomendaciones import ContribucionCreate, ContribucionResponse, LogPuntosResponse
from typing import List

router = APIRouter(prefix="/gamificacion", tags=["Gamificación"])

@router.get("/mis-puntos")
def mis_puntos(current_user: UsuarioVisitante = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retorna los puntos de experiencia del visitante."""
    # Obtener_rango_actual implementado
    return gamificacion_service.obtener_rango_actual(db, current_user.id_usuario)  # type: ignore[arg-type]

@router.get("/historial", response_model=List[LogPuntosResponse])
def historial_puntos(current_user: UsuarioVisitante = Depends(get_current_user), db: Session = Depends(get_db)):
    """Obtiene el historial de puntos obtenidos."""
    return gamificacion_service.obtener_historial_puntos(db, current_user.id_usuario)  # type: ignore[arg-type]

@router.post("/contribucion", response_model=ContribucionResponse)
def crear_contribucion(datos: ContribucionCreate, current_user: UsuarioVisitante = Depends(get_current_user), db: Session = Depends(get_db)):
    """Registra una contribución para ganar puntos tras ser aprobada."""
    return gamificacion_service.registrar_contribucion(db, current_user.id_usuario, datos)  # type: ignore[arg-type]
