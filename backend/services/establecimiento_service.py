from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional

from backend.models.establecimientos import Establecimiento, Platillo, Imagen, Horario, EstablecimientoCategoria
from backend.models.interacciones import InteraccionUsuario, Resena, FavoritoGuardado, Reporte
from backend.engine.collab_filter import compute_peso_interaccion
from backend.schemas.establecimientos import EstablecimientoCreate, EstablecimientoUpdate, HorarioCreate, PlatilloCreate, ImagenCreate
from backend.schemas.recomendaciones import InteraccionUsuarioCreate, ResenaCreate, FavoritoCreate, ReporteCreate

def obtener_establecimiento(db: Session, id_establecimiento: int):
    return db.query(Establecimiento).filter(Establecimiento.id_establecimiento == id_establecimiento, Establecimiento.estado == 'aprobado').first()

def crear_establecimiento(db: Session, id_usuario: int, datos: EstablecimientoCreate):
    nuevo = Establecimiento(
        nombre=datos.nombre,
        descripcion=datos.descripcion,
        latitud=datos.latitud,
        longitud=datos.longitud,
        direccion_texto=datos.direccion_texto,
        id_colonia=datos.id_colonia,
        tipo_establecimiento=datos.tipo_establecimiento,
        id_usuario_registro=id_usuario,
        estado="pendiente",
        es_informal=(datos.tipo_establecimiento == "puesto_informal")
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

def actualizar_establecimiento(db: Session, id_establecimiento: int, id_usuario: int, datos: EstablecimientoUpdate):
    est = db.query(Establecimiento).filter(Establecimiento.id_establecimiento == id_establecimiento).first()
    if not est:
        return None
    
    # Validación de auditoría: Solo el usuario que lo registró puede editar (simplificado para MVP)
    if est.id_usuario_registro != id_usuario:
        return None
        
    data_dict = datos.model_dump(exclude_unset=True)
    for key, value in data_dict.items():
        if hasattr(est, key):
            setattr(est, key, value)
            
    db.commit()
    db.refresh(est)
    return est

def buscar_establecimientos(db: Session, query: Optional[str] = None, id_categoria: Optional[int] = None, id_colonia: Optional[int] = None):
    db_query = db.query(Establecimiento).filter(Establecimiento.estado == 'aprobado')
    
    if query:
        db_query = db_query.filter(or_(
            Establecimiento.nombre.ilike(f"%{query}%"),
            Establecimiento.descripcion.ilike(f"%{query}%")
        ))
        
    # Auditoría Fase 1: Implementación del filtro por categoría faltante
    if id_categoria:
        db_query = db_query.filter(Establecimiento.categorias.any(EstablecimientoCategoria.id_categoria == id_categoria))
        
    if id_colonia:
        db_query = db_query.filter(Establecimiento.id_colonia == id_colonia)
        
    return db_query.all()

def gestionar_horarios(db: Session, id_establecimiento: int, horarios: list[HorarioCreate]):
    db.query(Horario).filter(Horario.id_establecimiento == id_establecimiento).delete()
    nuevos = [Horario(**h.model_dump()) for h in horarios]
    db.add_all(nuevos)
    db.commit()
    return nuevos

def crear_platillo(db: Session, id_establecimiento: int, datos: PlatilloCreate):
    platillo = Platillo(**datos.model_dump(), estado='pendiente')
    db.add(platillo)
    db.commit()
    db.refresh(platillo)
    return platillo

def subir_imagen(db: Session, id_establecimiento: int, datos: ImagenCreate):
    imagen = Imagen(**datos.model_dump(), estado='pendiente')
    db.add(imagen)
    db.commit()
    db.refresh(imagen)
    return imagen

def registrar_interaccion(db: Session, id_usuario: int, datos: InteraccionUsuarioCreate):
    peso = compute_peso_interaccion(datos.tipo_interaccion)
    interaccion = InteraccionUsuario(
        id_usuario=id_usuario,
        id_establecimiento=datos.id_establecimiento,
        tipo_interaccion=datos.tipo_interaccion,
        id_sesion=datos.id_sesion,
        peso_interaccion=peso
    )
    db.add(interaccion)
    db.commit()
    return interaccion

def crear_resena(db: Session, id_usuario: int, datos: ResenaCreate):
    resena = Resena(
        id_usuario=id_usuario,
        id_establecimiento=datos.id_establecimiento,
        calificacion=datos.calificacion,
        comentario=datos.comentario,
        estado='pendiente'
    )
    db.add(resena)
    db.commit()
    db.refresh(resena)
    return resena

def toggle_favorito(db: Session, id_usuario: int, datos: FavoritoCreate):
    fav = db.query(FavoritoGuardado).filter_by(id_usuario=id_usuario, id_establecimiento=datos.id_establecimiento).first()
    if fav:
        db.delete(fav)
        db.commit()
        return {"status": "removido"}
    else:
        nuevo_fav = FavoritoGuardado(id_usuario=id_usuario, id_establecimiento=datos.id_establecimiento, nota_personal=datos.nota_personal)
        db.add(nuevo_fav)
        db.commit()
        return {"status": "agregado"}

def crear_reporte(db: Session, id_usuario: int, datos: ReporteCreate):
    reporte = Reporte(
        id_usuario=id_usuario,
        id_establecimiento=datos.id_establecimiento,
        tipo_reporte=datos.tipo_reporte,
        descripcion=datos.descripcion,
        estado='pendiente'
    )
    db.add(reporte)
    db.commit()
    db.refresh(reporte)
    return reporte
