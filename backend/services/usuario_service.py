"""
Módulo: services/usuario_service.py
Fecha de modificación: 2026-05-23
Función: Contiene la lógica de negocio pesada para crear, 
actualizar y validar usuarios, separando estas operaciones de los 
controladores (routers).
"""
import uuid
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from user_agents import parse

from backend.models.usuarios import (
    Usuario, UsuarioVisitante, DispositivoUsuario, SesionUsuario, UbicacionUsuario
)
from backend.models.clusters import ClusterUsuario
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
    if not verify_password(password, str(usuario.password_hash)):
        return None
    return usuario

def marcar_actividad_usuario(db: Session, id_usuario: int):
    """
    Actualiza la fecha_ultima_actividad del usuario visitante a la fecha y hora actual.
    """
    db.query(UsuarioVisitante).filter(UsuarioVisitante.id_usuario == id_usuario).update(
        {"fecha_ultima_actividad": datetime.now(timezone.utc)}
    )

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
    
    # Marcar actividad
    marcar_actividad_usuario(db, id_usuario)
    
    db.commit()
    
    return id_sesion

from datetime import datetime, timezone
from typing import Optional

def cerrar_sesion(db: Session, id_sesion: str):
    """
    Cierra la sesión actual y calcula la duración.
    """
    sesion = db.query(SesionUsuario).filter(SesionUsuario.id_sesion == id_sesion).first()
    if sesion and sesion.fecha_inicio:
        duracion = (datetime.now(timezone.utc) - sesion.fecha_inicio).total_seconds()
        sesion.duracion_segundos = int(duracion)  # type: ignore[assignment]
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

def registrar_ubicacion(db: Session, id_usuario: int, lat: float, lon: float, precision: Optional[int] = None, id_sesion: Optional[str] = None):
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

def eliminar_ubicaciones(db: Session, id_usuario: int):
    """
    Elimina todas las ubicaciones almacenadas para el usuario (desactiva geolocalización).
    """
    db.query(UbicacionUsuario).filter(UbicacionUsuario.id_usuario == id_usuario).delete()
    db.commit()
    
def procesar_onboarding(db: Session, id_usuario: int, categorias: list[str], precios: list[str]):
    """
    Genera el vector de preferencias basado en el onboarding inicial.
    Actualiza perfil_completado=True.
    """
    visitante = db.query(UsuarioVisitante).filter(UsuarioVisitante.id_usuario == id_usuario).first()
    if visitante:
        # Verificar si las preferencias realmente cambiaron
        prefs_actuales = visitante.vector_preferencias
        cambiaron_preferencias = True
        
        if isinstance(prefs_actuales, dict):
            cats_actuales = prefs_actuales.get("categorias_preferidas", [])
            precios_actuales = prefs_actuales.get("precios_preferidos", [])
            if set(cats_actuales) == set(categorias) and set(precios_actuales) == set(precios):
                cambiaron_preferencias = False
                
        if not cambiaron_preferencias and visitante.perfil_completado:
            # Si no hubo cambios, no es necesario recalcular el cold_start
            return
            
        # Guardamos el estado de perfil completado
        # El vector de preferencias será guardado en el bloque try de abajo
        visitante.perfil_completado = True  # type: ignore[assignment]
        
        # Asignación provisional de ID al cluster de usuario
        try:
            from backend.engine.cold_start import assign_cluster_provisional
            # Ordenar por id_cluster para asegurar que obtenemos el Cluster 1 (el más confiable)
            clusters = db.query(ClusterUsuario).order_by(ClusterUsuario.id_cluster).all()
            
            # Simulamos un vector numérico simplificado a partir del JSON
            # En producción esto sería un embedding semántico
            dim = 22 # Dimensión base esperada por el modelo (22 características)
            if clusters and clusters[0].centroide:
                # Tomamos la dimensión del cluster activo, asegurando un fallback seguro
                dim = max(len(clusters[0].centroide), dim)  # type: ignore
                vector_simulado = [0.0] * dim
                for i in range(min(len(categorias), dim)):
                    vector_simulado[i] = 1.0
                for i in range(min(len(precios), max(0, dim - len(categorias)))):
                    vector_simulado[len(categorias) + i] = 0.5
                    
                # Guardamos las preferencias junto al vector numérico para K-Means
                visitante.vector_preferencias = {  # type: ignore[assignment]
                    "categorias_preferidas": categorias,
                    "precios_preferidos": precios,
                    "numerico": vector_simulado
                }
                
                id_cluster_prov = assign_cluster_provisional(vector_simulado, clusters)
                if id_cluster_prov is not None:
                    visitante.id_cluster = id_cluster_prov # type: ignore
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("No se pudo asignar cluster provisional en onboarding: %s", e)
            
        db.commit()

        # Generar recomendaciones de inicio en frío (Cold Start) inmediatamente
        try:
            from backend.engine.cold_start import get_cold_start_recommendations
            from backend.models.interacciones import RecomendacionGenerada
            
            # Limpiar recomendaciones cold_start previas para evitar duplicados si se re-evalúa el perfil
            db.query(RecomendacionGenerada).filter(
                RecomendacionGenerada.id_usuario == id_usuario,
                RecomendacionGenerada.categoria_recomendacion == "cold_start"
            ).delete()
            db.commit()
            
            estabs_cold_start = get_cold_start_recommendations(db, visitante, limit=30)
            for i, estab in enumerate(estabs_cold_start):
                nueva_rec = RecomendacionGenerada(
                    id_usuario=id_usuario,
                    id_establecimiento=estab.id_establecimiento,
                    categoria_recomendacion="cold_start",
                    posicion=i,
                    score_total=0.95 - (i * 0.01),
                    score_contenido_usado=0.90 - (i * 0.01),
                    score_colaborativo_usado=0.85 - (i * 0.01),
                    razon_principal="cold_start",
                    detalle_razon="Seleccionado como punto de partida según tus intereses.",
                    estrategia_usada="cold_start",
                    radio_usado_km=visitante.radio_busqueda_km or 5,
                    fallback_nivel=0,
                    fecha_generacion=datetime.now(timezone.utc)
                )
                db.add(nueva_rec)
            db.commit()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Error al generar cold start: %s", e)
