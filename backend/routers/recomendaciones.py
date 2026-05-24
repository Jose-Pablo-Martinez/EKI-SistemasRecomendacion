from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth import get_current_user
from backend.models import Usuario
from backend.schemas.recomendaciones import RecomendacionResponse
from backend.services import recomendacion_service

router = APIRouter(
    prefix="/recomendaciones",
    tags=["Recomendaciones"]
)

@router.get("", response_model=Dict[str, List[RecomendacionResponse]])
def get_recomendaciones(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene las recomendaciones personalizadas para el usuario autenticado,
    agrupadas por categoría.
    """
    resultados = recomendacion_service.obtener_recomendaciones(db, current_user.id_usuario)  # type: ignore
    return resultados

@router.post("/{id_recomendacion}/click", status_code=status.HTTP_204_NO_CONTENT)
def registrar_click_recomendacion(
    id_recomendacion: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Registra que el usuario hizo click en una recomendación específica.
    """
    exito = recomendacion_service.registrar_click(db, id_recomendacion)
    if not exito:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recomendación no encontrada"
        )
