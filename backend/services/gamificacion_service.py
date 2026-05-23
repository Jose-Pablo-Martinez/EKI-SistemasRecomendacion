import logging
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from backend.models.interacciones import LogPuntos
from backend.models.usuarios import UsuarioVisitante

logger = logging.getLogger(__name__)

# Diccionario de reglas base
PUNTOS_POR_ACCION = {
    "crear_resena": 10,
    "nuevo_lugar": 50,
    "editar_lugar": 20,
    "reporte_valido": 15
}

def otorgar_puntos(db: Session, id_usuario: int, accion: str, descripcion: str = ""):
    """
    Otorga puntos a un usuario visitante según la acción realizada y actualiza 
    su total desnormalizado.
    """
    puntos = PUNTOS_POR_ACCION.get(accion, 0)
    if puntos <= 0:
        return
        
    log = LogPuntos(
        id_usuario=id_usuario,
        accion=accion[:100],
        puntos_otorgados=puntos,
        descripcion=descripcion
    )
    db.add(log)
    
    # Actualizar desnormalizado
    visitante = db.query(UsuarioVisitante).filter(UsuarioVisitante.id_usuario == id_usuario).first()
    if visitante:
        visitante.puntos_experiencia += puntos
        
    db.commit()
    logger.info(f"Otorgados {puntos} pts a {id_usuario} por {accion}")
