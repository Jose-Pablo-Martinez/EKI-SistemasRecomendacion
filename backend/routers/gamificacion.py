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
    logs = gamificacion_service.obtener_historial_puntos(db, current_user.id_usuario)  # type: ignore[arg-type]

    # El modelo guarda `motivo` como ENUM (snake_case). El frontend lo muestra tal cual
    # y decide el ícono por substring ("reseña", "foto", "lugar"), así que lo humanizamos aquí.
    motivo_label = {
        "contribucion_aprobada": "Contribución aprobada",
        "resena_aprobada": "Reseña aprobada",
        "foto_aprobada": "Foto aprobada",
        "nuevo_lugar": "Lugar aprobado",
        "penalizacion": "Penalización",
        "subida_rango": "Subida de rango",
    }

    return [
        {
            "id_log": l.id_log,
            "id_usuario": l.id_usuario,
            "puntos": l.puntos,
            "motivo": motivo_label.get(l.motivo, str(l.motivo)),
            "id_contribucion": l.id_contribucion,
            "fecha": l.fecha,
        }
        for l in logs
    ]

@router.post("/contribucion", response_model=ContribucionResponse)
def crear_contribucion(datos: ContribucionCreate, current_user: UsuarioVisitante = Depends(get_current_user), db: Session = Depends(get_db)):
    """Registra una contribución para ganar puntos tras ser aprobada."""
    return gamificacion_service.registrar_contribucion(db, current_user.id_usuario, datos)  # type: ignore[arg-type]
