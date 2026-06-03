from sqlalchemy.orm import Session, joinedload
from backend.models.establecimientos import Establecimiento, PropietarioEstablecimiento
from backend.models.interacciones import Resena
from backend.models.usuarios import Usuario
from backend.services.gamificacion_service import otorgar_puntos
from sqlalchemy.sql import func
from sqlalchemy import or_

def aprobar_establecimiento(db: Session, id_establecimiento: int) -> tuple[bool, str]:
    est = db.query(Establecimiento).filter(Establecimiento.id_establecimiento == id_establecimiento).first()
    if not est:
        return False, "No se encontró el establecimiento."
        
    # Flujo de Baja: Si solicitó baja, la aprobación significa Hard Delete
    if est.solicita_baja:
        nombre = est.nombre
        from backend.services.establecimiento_service import borrar_dependencias_establecimiento
        borrar_dependencias_establecimiento(db, id_establecimiento)
        db.delete(est)
        db.commit()
        return True, f"Aprobada solicitud de baja del establecimiento {nombre}"

    if est.estado != "pendiente":
        return False, "El establecimiento no está pendiente."

    # Flujo de Modificación: Si tiene padre, se actualiza el padre y se borra el clon
    if est.id_establecimiento_padre is not None:
        padre = db.query(Establecimiento).filter(Establecimiento.id_establecimiento == est.id_establecimiento_padre).first()
        if padre:
            padre.nombre = est.nombre
            padre.descripcion = est.descripcion
            padre.latitud = est.latitud
            padre.longitud = est.longitud
            padre.direccion_texto = est.direccion_texto
            padre.id_colonia = est.id_colonia
            padre.tipo_establecimiento = est.tipo_establecimiento
            padre.es_informal = est.es_informal
            
            from backend.services.establecimiento_service import borrar_dependencias_establecimiento
            borrar_dependencias_establecimiento(db, est.id_establecimiento)
            db.delete(est) # Borramos el clon
            db.commit()
            return True, f"Modificación aprobada para {padre.nombre}"
        return False, "No se encontró el establecimiento padre."
        
    es_modificacion = est.fecha_aprobacion is not None
    est.estado = "aprobado"  # type: ignore[assignment]
    if not es_modificacion:
        est.fecha_aprobacion = func.now() # type: ignore[assignment]
        
    # Otorgar puntos al usuario que lo propuso (50 si es nuevo, 20 si es edición)
    accion = "editar_lugar" if es_modificacion else "nuevo_lugar"
    texto = "Modificación aprobada: " if es_modificacion else "Lugar aprobado: "
    otorgar_puntos(db, est.id_usuario_registro, accion, f"{texto}{est.nombre}")
    db.commit()
    return True, f"{texto}{est.nombre}"

def rechazar_establecimiento(db: Session, id_establecimiento: int) -> bool:
    est = db.query(Establecimiento).filter(Establecimiento.id_establecimiento == id_establecimiento).first()
    if not est:
        return False
        
    # Flujo de Baja: Rechazar baja significa solo quitar el flag
    if est.solicita_baja:
        est.solicita_baja = False  # type: ignore[assignment]
        db.commit()
        return True

    if est.estado != "pendiente":
        return False
        
    # TODO: Para el futuro, en lugar de mantener el registro del establecimiento
    # en estado "rechazado" (lo que ocupa espacio en la base de datos como basura), 
    # lo ideal sería hacer un hard delete inmediato aquí mismo y guardar un 
    # registro ligero (ej. solo el nombre y fecha) en una tabla "HistorialRechazos"
    # para que el usuario pueda seguir viéndolo en su panel de "Mis Contribuciones"
    # y borrar la notificación desde ahí. Por ahora en el MVP, se mantiene el 
    # registro como rechazado hasta que el usuario lo borra manualmente.
    est.estado = "rechazado"  # type: ignore[assignment]
    db.commit()
    return True


def aprobar_resena(db: Session, id_resena: int) -> bool:
    resena = db.query(Resena).filter(Resena.id_resena == id_resena).first()
    if not resena or resena.estado != "pendiente":
        return False
        
    resena.estado = "aprobado"  # type: ignore[assignment]
    resena.procesado_nlp = False  # type: ignore[assignment] — Para que el NLP lo pase a analizar
    
    # Recalcular desnormalizados de establecimiento
    est = db.query(Establecimiento).filter(Establecimiento.id_establecimiento == resena.id_establecimiento).first()
    if est:
        # Calcular nuevo promedio y total
        stats = db.query(
            func.count(Resena.id_resena).label("total"),
            func.avg(Resena.calificacion).label("promedio")
        ).filter(
            Resena.id_establecimiento == resena.id_establecimiento,
            Resena.estado == "aprobado"
        ).first()
        
        est.total_resenas = stats.total if stats else 0  # type: ignore[assignment]
        est.calificacion_promedio = float(stats.promedio) if stats and stats.promedio else 0.0  # type: ignore[assignment]

    otorgar_puntos(db, resena.id_usuario, "crear_resena", f"Reseña aprobada en {resena.id_establecimiento}")
    db.commit()
    return True

def obtener_altas_visitantes(db: Session):
    return db.query(Establecimiento).join(Usuario, Establecimiento.id_usuario_registro == Usuario.id_usuario).filter(
        or_(
            Establecimiento.estado == "pendiente",
            Establecimiento.solicita_baja == True
        ),
        Usuario.tipo_usuario == "visitante"
    ).options(
        joinedload(Establecimiento.horarios),
        joinedload(Establecimiento.platillos)
    ).all()

def obtener_altas_propietarios(db: Session):
    # TODO (MVP): El flujo de altas de propietarios no se implementa en este MVP.
    # Requiere una modificación masiva en la lógica de negocio (verificación de identidad,
    # subida de documentos probatorios, RFC, imágenes a la BD/S3, etc.).
    # Por ahora este método puede devolver vacío o seguir la lógica básica sin validación documental.
    return db.query(Establecimiento).join(Usuario, Establecimiento.id_usuario_registro == Usuario.id_usuario).filter(
        or_(
            Establecimiento.estado == "pendiente",
            Establecimiento.solicita_baja == True
        ),
        Usuario.tipo_usuario == "propietario"
    ).options(
        joinedload(Establecimiento.horarios),
        joinedload(Establecimiento.platillos)
    ).all()

def obtener_reclamos_pendientes(db: Session):
    # TODO (MVP): Los reclamos de propiedad tampoco se incluyen en el MVP.
    # Supone recibir y validar documentación legal para que un usuario existente
    # tome control de un lugar que fue dado de alta por un visitante.
    return db.query(PropietarioEstablecimiento).options(
        joinedload(PropietarioEstablecimiento.establecimiento),
        joinedload(PropietarioEstablecimiento.propietario)
    ).filter(PropietarioEstablecimiento.estado == "pendiente").all()

def aprobar_reclamo(db: Session, id_propietario: int, id_establecimiento: int) -> bool:
    reclamo = db.query(PropietarioEstablecimiento).filter_by(
        id_propietario=id_propietario, id_establecimiento=id_establecimiento, estado="pendiente"
    ).first()
    if not reclamo: return False
    reclamo.estado = "aprobado" # type: ignore
    db.commit()
    return True

def rechazar_reclamo(db: Session, id_propietario: int, id_establecimiento: int) -> bool:
    reclamo = db.query(PropietarioEstablecimiento).filter_by(
        id_propietario=id_propietario, id_establecimiento=id_establecimiento, estado="pendiente"
    ).first()
    if not reclamo: return False
    reclamo.estado = "rechazado" # type: ignore
    db.commit()
    return True

def obtener_resenas_pendientes(db: Session):
    return db.query(Resena).filter(Resena.estado == "pendiente").all()

def disparar_job(tipo_job: str):
    from backend.jobs.runner import run_job
    from backend.database import SessionLocal
    return run_job(tipo_job, SessionLocal)
