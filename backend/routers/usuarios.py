"""
Módulo: routers/usuarios.py
Fecha de modificación: 2026-05-23
Función: Define los endpoints (API) relacionados con la gestión de usuarios, 
incluyendo registro, login, obtención de perfil y envío de onboarding.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models.usuarios import Usuario
from backend.schemas.usuarios import UsuarioCreate, UsuarioResponse, UsuarioVisitanteResponse, UsuarioPerfilResponse, PerfilUpdate, OnboardingData, UbicacionData
from backend.services import usuario_service
from backend.auth import create_access_token, get_current_user
from backend.models.usuarios import UbicacionUsuario
from backend.models.interacciones import FavoritoGuardado
from sqlalchemy.orm import joinedload
from backend.models.interacciones import Resena, FavoritoGuardado, ContribucionInformacion
from backend.models.establecimientos import Establecimiento
from backend.schemas.establecimientos import EstablecimientoResponse

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

@router.get("/me", response_model=UsuarioPerfilResponse)
def get_my_profile(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Obtiene el perfil del usuario autenticado."""
   

    total_resenas = db.query(func.count(Resena.id_resena)).filter(
        Resena.id_usuario == current_user.id_usuario
    ).scalar() or 0
    total_favoritos = db.query(func.count(FavoritoGuardado.id_establecimiento)).filter(
        FavoritoGuardado.id_usuario == current_user.id_usuario
    ).scalar() or 0
    total_contribuciones = db.query(func.count(ContribucionInformacion.id_contribucion)).filter(
        ContribucionInformacion.id_usuario == current_user.id_usuario
    ).scalar() or 0

    puntos_totales = 0
    if getattr(current_user, "visitante", None) is not None:
        puntos_totales = getattr(current_user.visitante, "puntos_experiencia", 0) or 0
        
   
    tiene_ubicacion = db.query(UbicacionUsuario).filter(UbicacionUsuario.id_usuario == current_user.id_usuario).first() is not None

    return {
        "id_usuario": current_user.id_usuario,
        "email": current_user.email,
        "nombre": current_user.nombre,
        "apellido": current_user.apellido,
        "foto_perfil": current_user.foto_perfil,
        "tipo_usuario": current_user.tipo_usuario,
        "activo": current_user.activo,
        "fecha_registro": current_user.fecha_registro,
        "perfil_completado": current_user.perfil_completado,
        "visitante": current_user.visitante,
        "puntos_totales": puntos_totales,
        "total_resenas": total_resenas,
        "total_favoritos": total_favoritos,
        "total_contribuciones": total_contribuciones,
        "ubicacion_activa": tiene_ubicacion,
    }

@router.patch("/me", response_model=UsuarioResponse)
def update_my_profile(data: PerfilUpdate, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Actualiza el perfil del usuario autenticado."""
    updated = usuario_service.actualizar_perfil(db, current_user.id_usuario, data.model_dump(exclude_unset=True))  # type: ignore[arg-type]
    return updated

@router.get("/me/favoritos")
def get_mis_favoritos(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Obtiene la lista de establecimientos favoritos del usuario."""
    
    
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

@router.delete("/ubicacion")
def eliminar_ubicacion(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Elimina las ubicaciones del usuario (desactiva uso de ubicación)."""
    usuario_service.eliminar_ubicaciones(db, current_user.id_usuario)  # type: ignore[arg-type]
    return {"status": "ok", "message": "Ubicación desactivada."}

@router.get("/me/contribuciones", response_model=list[EstablecimientoResponse])
def get_mis_contribuciones(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Obtiene los establecimientos creados/aportados por el usuario."""
    contribuciones = db.query(Establecimiento).filter(
        Establecimiento.id_usuario_registro == current_user.id_usuario
    ).order_by(Establecimiento.fecha_registro.desc()).all()
    return contribuciones
