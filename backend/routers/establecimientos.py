# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.usuarios import UsuarioVisitante
from backend.auth import get_current_user
from backend.services import establecimiento_service
from backend.schemas.establecimientos import EstablecimientoCreate, EstablecimientoUpdate, EstablecimientoResponse, HorarioCreate, PlatilloCreate, ImagenCreate
from backend.schemas.recomendaciones import InteraccionUsuarioCreate, ResenaCreate, FavoritoCreate, ReporteCreate

router = APIRouter(prefix="/establecimientos", tags=["Establecimientos"])

@router.get("/buscar")
def buscar_establecimientos(q: str = None, colonia: int = None, db: Session = Depends(get_db)):
    """Búsqueda de establecimientos por query de texto o colonia."""
    return establecimiento_service.buscar_establecimientos(db, query=q, id_colonia=colonia)

@router.get("/{id_establecimiento}", response_model=EstablecimientoResponse)
def get_establecimiento(id_establecimiento: int, db: Session = Depends(get_db)):
    """Obtiene el detalle de un establecimiento aprobado."""
    est = establecimiento_service.obtener_establecimiento(db, id_establecimiento)
    if not est:
        raise HTTPException(status_code=404, detail="Establecimiento no encontrado o no aprobado")
    return est

@router.post("/", response_model=EstablecimientoResponse, status_code=status.HTTP_201_CREATED)
def create_establecimiento(datos: EstablecimientoCreate, current_user: UsuarioVisitante = Depends(get_current_user), db: Session = Depends(get_db)):
    """Propone un nuevo establecimiento. Queda en estado pendiente."""
    return establecimiento_service.crear_establecimiento(db, current_user.id_usuario, datos)

@router.patch("/{id_establecimiento}", response_model=EstablecimientoResponse)
def update_establecimiento(id_establecimiento: int, datos: EstablecimientoUpdate, current_user: UsuarioVisitante = Depends(get_current_user), db: Session = Depends(get_db)):
    """Actualiza datos de un establecimiento."""
    est = establecimiento_service.actualizar_establecimiento(db, id_establecimiento, current_user.id_usuario, datos)
    if not est:
        raise HTTPException(status_code=404, detail="Establecimiento no encontrado")
    return est

@router.put("/{id_establecimiento}/horarios")
def update_horarios(id_establecimiento: int, horarios: list[HorarioCreate], current_user: UsuarioVisitante = Depends(get_current_user), db: Session = Depends(get_db)):
    """Actualiza los horarios de un establecimiento."""
    return establecimiento_service.gestionar_horarios(db, id_establecimiento, horarios)

@router.post("/{id_establecimiento}/platillo")
def add_platillo(id_establecimiento: int, datos: PlatilloCreate, current_user: UsuarioVisitante = Depends(get_current_user), db: Session = Depends(get_db)):
    """Sube un platillo para revisión."""
    if datos.id_establecimiento != id_establecimiento:
        raise HTTPException(status_code=400, detail="ID url no coincide con el body")
    return establecimiento_service.crear_platillo(db, id_establecimiento, datos)

@router.post("/{id_establecimiento}/imagen")
def add_imagen(id_establecimiento: int, datos: ImagenCreate, current_user: UsuarioVisitante = Depends(get_current_user), db: Session = Depends(get_db)):
    """Sube una imagen para revisión."""
    if datos.id_establecimiento != id_establecimiento:
        raise HTTPException(status_code=400, detail="ID url no coincide con el body")
    return establecimiento_service.subir_imagen(db, id_establecimiento, datos)

@router.post("/{id_establecimiento}/interaccion")
def registrar_interaccion(id_establecimiento: int, datos: InteraccionUsuarioCreate, current_user: UsuarioVisitante = Depends(get_current_user), db: Session = Depends(get_db)):
    """Registra una interaccion con su peso correspondiente."""
    if datos.id_establecimiento != id_establecimiento:
        raise HTTPException(status_code=400, detail="ID url no coincide con el body")
    establecimiento_service.registrar_interaccion(db, current_user.id_usuario, datos)
    return {"status": "ok"}

@router.post("/{id_establecimiento}/resena")
def crear_resena(id_establecimiento: int, datos: ResenaCreate, current_user: UsuarioVisitante = Depends(get_current_user), db: Session = Depends(get_db)):
    """Agrega una nueva reseña al establecimiento."""
    if datos.id_establecimiento != id_establecimiento:
        raise HTTPException(status_code=400, detail="ID url no coincide con el body")
    establecimiento_service.crear_resena(db, current_user.id_usuario, datos)
    return {"status": "ok", "message": "Reseña en revisión"}

@router.post("/{id_establecimiento}/favorito")
def toggle_favorito(id_establecimiento: int, datos: FavoritoCreate, current_user: UsuarioVisitante = Depends(get_current_user), db: Session = Depends(get_db)):
    """Agrega o quita de favoritos."""
    if datos.id_establecimiento != id_establecimiento:
        raise HTTPException(status_code=400, detail="ID url no coincide con el body")
    return establecimiento_service.toggle_favorito(db, current_user.id_usuario, datos)

@router.post("/{id_establecimiento}/reporte")
def crear_reporte(id_establecimiento: int, datos: ReporteCreate, current_user: UsuarioVisitante = Depends(get_current_user), db: Session = Depends(get_db)):
    """Reporta un lugar."""
    if datos.id_establecimiento != id_establecimiento:
        raise HTTPException(status_code=400, detail="ID url no coincide con el body")
    establecimiento_service.crear_reporte(db, current_user.id_usuario, datos)
    return {"status": "ok", "message": "Reporte recibido"}
