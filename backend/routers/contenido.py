"""
Módulo: routers/contenido.py
Fecha de modificación: 2026-05-23
Función: Endpoints de solo lectura para obtener catálogos maestros 
estáticos de la aplicación (como la lista de categorías y etiquetas).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.catalogo import Categoria, Etiqueta
from backend.models.geografia import Colonia

router = APIRouter(prefix="/contenido", tags=["Contenido"])

@router.get("/categorias")
def get_categorias(db: Session = Depends(get_db)):
    """Retorna todas las categorías."""
    categorias = db.query(Categoria).all()
    return categorias

@router.get("/etiquetas")
def get_etiquetas(db: Session = Depends(get_db)):
    """Retorna todas las etiquetas."""
    etiquetas = db.query(Etiqueta).all()
    return etiquetas

@router.get("/geografia/colonias")
def get_colonias(id_municipio: int = None, db: Session = Depends(get_db)):
    """Retorna las colonias, opcionalmente filtradas por municipio."""
    query = db.query(Colonia)
    if id_municipio:
        query = query.filter(Colonia.id_municipio == id_municipio)
    return query.all()
