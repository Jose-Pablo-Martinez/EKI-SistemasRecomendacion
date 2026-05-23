# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.usuarios import UsuarioVisitante
from backend.auth import get_current_user

router = APIRouter(prefix="/gamificacion", tags=["Gamificación"])

@router.get("/mis-puntos")
def mis_puntos(current_user: UsuarioVisitante = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retorna los puntos de experiencia del visitante."""
    return {
        "puntos_experiencia": current_user.puntos_experiencia,
        "rango_actual": current_user.id_rango
    }
