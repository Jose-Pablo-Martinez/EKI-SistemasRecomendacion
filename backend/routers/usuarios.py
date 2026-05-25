"""
Módulo: routers/usuarios.py
Fecha de modificación: 2026-05-23
Función: Define los endpoints (API) relacionados con la gestión de usuarios, 
incluyendo registro, login, obtención de perfil y envío de onboarding.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.usuarios import Usuario
from backend.schemas.usuarios import UsuarioCreate, UsuarioResponse, UsuarioVisitanteResponse, PerfilUpdate, OnboardingData, UbicacionData
from backend.services import usuario_service
from backend.auth import create_access_token, get_current_user

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

@router.post("/registro", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def registro(user_data: UsuarioCreate, db: Session = Depends(get_db)):
    """Registra un nuevo usuario en la plataforma."""
    usuario = usuario_service.crear_usuario(db, user_data)
    return usuario

@router.post("/login")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Inicia sesión, registra el dispositivo y retorna JWT."""
    usuario = usuario_service.autenticar_usuario(db, form_data.username, form_data.password)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Registrar Sesión y Dispositivo
    user_agent = request.headers.get("User-Agent", "")
    id_sesion = usuario_service.registrar_dispositivo_sesion(db, usuario.id_usuario, user_agent)  # type: ignore[arg-type]
    
    # Generar Token JWT
    access_token = create_access_token(data={"sub": usuario.email, "sesion": id_sesion})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UsuarioResponse)
def get_my_profile(current_user: Usuario = Depends(get_current_user)):
    """Obtiene el perfil del usuario autenticado."""
    return current_user

@router.patch("/me", response_model=UsuarioResponse)
def update_my_profile(data: PerfilUpdate, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Actualiza el perfil del usuario autenticado."""
    updated = usuario_service.actualizar_perfil(db, current_user.id_usuario, data.model_dump(exclude_unset=True))  # type: ignore[arg-type]
    return updated

@router.get("/me/favoritos")
def get_mis_favoritos(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Obtiene la lista de establecimientos favoritos del usuario."""
    from backend.models.interacciones import FavoritoGuardado
    from sqlalchemy.orm import joinedload
    
    favoritos_db = db.query(FavoritoGuardado).options(
        joinedload(FavoritoGuardado.establecimiento)
    ).filter(FavoritoGuardado.id_usuario == current_user.id_usuario).all()
    
    resultados = []
    for f in favoritos_db:
        if f.establecimiento:
            resultados.append({
                "id_establecimiento": f.id_establecimiento,
                "fecha_guardado": f.fecha_guardado,
                "nota_personal": f.nota_personal,
                "establecimiento": f.establecimiento
            })
    return resultados

@router.post("/logout")
def logout(id_sesion: str, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Cierra la sesión actual."""
    usuario_service.cerrar_sesion(db, id_sesion)
    return {"status": "ok", "message": "Sesión cerrada"}

@router.post("/onboarding")
def guardar_onboarding(data: OnboardingData, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Guarda las preferencias iniciales de un usuario."""
    usuario_service.procesar_onboarding(db, current_user.id_usuario, data.preferencias.categorias, data.preferencias.precios)  # type: ignore[arg-type]
    return {"status": "ok", "message": "Onboarding completado exitosamente."}

@router.post("/ubicacion")
def actualizar_ubicacion(data: UbicacionData, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Registra una nueva ubicación del usuario (máx. 3 en BD)."""
    usuario_service.registrar_ubicacion(db, current_user.id_usuario, data.latitud, data.longitud, data.precision_metros)  # type: ignore[arg-type]
    return {"status": "ok"}
