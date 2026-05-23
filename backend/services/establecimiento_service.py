# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from backend.models.establecimientos import Establecimiento
from backend.models.interacciones import InteraccionUsuario

def obtener_establecimiento(db: Session, id_establecimiento: int):
    return db.query(Establecimiento).filter(Establecimiento.id_establecimiento == id_establecimiento).first()

def crear_establecimiento(db: Session, id_usuario: int, datos: dict):
    # Por defecto se crean como "pendiente"
    nuevo = Establecimiento(
        nombre=datos["nombre"],
        descripcion=datos.get("descripcion", ""),
        latitud=datos["latitud"],
        longitud=datos["longitud"],
        id_categoria=datos.get("id_categoria"),
        id_usuario_registro=id_usuario,
        estado="pendiente",
        es_informal=datos.get("es_informal", True)
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

def registrar_interaccion(db: Session, id_usuario: int, id_establecimiento: int, tipo: str, id_sesion: str = None):
    interaccion = InteraccionUsuario(
        id_usuario=id_usuario,
        id_establecimiento=id_establecimiento,
        tipo_interaccion=tipo,
        id_sesion=id_sesion
    )
    db.add(interaccion)
    db.commit()
