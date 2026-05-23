"""
Módulo: services/usuario_service.py
Fecha de modificación: 2026-05-23
Función: Contiene la lógica de negocio pesada para crear, 
actualizar y validar usuarios, separando estas operaciones de los 
controladores (routers).
"""
import uuid
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from sqlalchemy.exc import IntegrityError
from user_agents import parse

from backend.models.usuarios import (
    Usuario, UsuarioVisitante, DispositivoUsuario, SesionUsuario, UbicacionUsuario
)
from backend.schemas.usuarios import UsuarioCreate
from backend.auth import get_password_hash, verify_password

def crear_usuario(db: Session, user_data: UsuarioCreate) -> Usuario:
    """
    Crea un nuevo usuario en la base de datos aplicando el patrón TPT.
    Hashea la contraseña antes de guardarla.
    """
    hashed_pwd = get_password_hash(user_data.password)
    
    nuevo_usuario = Usuario(
        email=user_data.email,
        nombre=user_data.nombre,
        apellido=user_data.apellido,
        password_hash=hashed_pwd,
        tipo_usuario=user_data.tipo_usuario,
        genero=user_data.genero,
        fecha_nacimiento=user_data.fecha_nacimiento
    )
    db.add(nuevo_usuario)
    db.flush()  # Obtener nuevo_usuario.id_usuario
    
    # Crear tabla hija correspondiente
    if user_data.tipo_usuario == "visitante":
        visitante = UsuarioVisitante(id_usuario=nuevo_usuario.id_usuario)
        db.add(visitante)
        
    # TODO: Implementar lógica para propietario/admin si se requiere en el futuro
    
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario

def autenticar_usuario(db: Session, email: str, password: str) -> Usuario | None:
    """
    Busca al usuario por email y verifica la contraseña.
    Retorna el usuario si es exitoso, None en caso contrario.
    """
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario:
        return None
    if not verify_password(password, usuario.password_hash):
        return None
    return usuario

def registrar_dispositivo_sesion(db: Session, id_usuario: int, user_agent_string: str) -> str:
    """
    Registra el dispositivo actual y genera una nueva sesión.
    Garantiza que solo este dispositivo sea `es_ultimo=True`.
    """
    ua = parse(user_agent_string)
    if ua.is_mobile:
        tipo_disp = "movil"
    elif ua.is_tablet:
        tipo_disp = "tablet"
    elif ua.is_pc:
        tipo_disp = "escritorio"
    else:
        tipo_disp = "desconocido"
        
    # Invalidar 'es_ultimo' de dispositivos previos del usuario
    db.query(DispositivoUsuario).filter(
        DispositivoUsuario.id_usuario == id_usuario
    ).update({"es_ultimo": False})
    
    nuevo_disp = DispositivoUsuario(
        id_usuario=id_usuario,
        tipo_dispositivo=tipo_disp,
        sistema_operativo=ua.os.family,
        es_ultimo=True
    )
    db.add(nuevo_disp)
    db.flush()
    
    id_sesion = str(uuid.uuid4())
    nueva_sesion = SesionUsuario(
        id_sesion=id_sesion,
        id_usuario=id_usuario,
        id_dispositivo=nuevo_disp.id_dispositivo
    )
    db.add(nueva_sesion)
    db.commit()
    
    return id_sesion

from datetime import datetime

def cerrar_sesion(db: Session, id_sesion: str):
    """
    Cierra la sesión actual y calcula la duración.
    """
    sesion = db.query(SesionUsuario).filter(SesionUsuario.id_sesion == id_sesion).first()
    if sesion and sesion.fecha_inicio:
        duracion = (datetime.utcnow() - sesion.fecha_inicio).total_seconds()
        sesion.duracion_segundos = int(duracion)
        db.commit()

def actualizar_perfil(db: Session, id_usuario: int, data: dict):
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        return
        
    for key, value in data.items():
        if value is not None and hasattr(usuario, key):
            setattr(usuario, key, value)
            
    visitante = db.query(UsuarioVisitante).filter(UsuarioVisitante.id_usuario == id_usuario).first()
    if visitante and "radio_busqueda_km" in data and data["radio_busqueda_km"] is not None:
        visitante.radio_busqueda_km = data["radio_busqueda_km"]
        
    db.commit()
    db.refresh(usuario)
    return usuario

def registrar_ubicacion(db: Session, id_usuario: int, lat: float, lon: float, precision: int = None, id_sesion: str = None):
    """
    Inserta una nueva ubicación y mantiene un máximo de 3 ubicaciones recientes.
    """
    nueva_ub = UbicacionUsuario(
        id_usuario=id_usuario,
        latitud=lat,
        longitud=lon,
        precision_metros=precision,
        id_sesion=id_sesion
    )
    db.add(nueva_ub)
    db.flush()
    
    # Mantener solo las últimas 3 ubicaciones
    ubicaciones = db.query(UbicacionUsuario).filter(
        UbicacionUsuario.id_usuario == id_usuario
    ).order_by(UbicacionUsuario.fecha_registro.desc()).all()
    
    if len(ubicaciones) > 3:
        for ub_to_delete in ubicaciones[3:]:
            db.delete(ub_to_delete)
            
    db.commit()
    
def procesar_onboarding(db: Session, id_usuario: int, categorias: list[str], precios: list[str]):
    """
    Genera el vector de preferencias basado en el onboarding inicial.
    Actualiza perfil_completado=True.
    """
    visitante = db.query(UsuarioVisitante).filter(UsuarioVisitante.id_usuario == id_usuario).first()
    if visitante:
        # Por simplicidad, guardaremos los arrays tal cual como seed del vector K-Means
        visitante.vector_preferencias = {
            "categorias_preferidas": categorias,
            "precios_preferidos": precios
        }
        visitante.perfil_completado = True
        db.commit()
