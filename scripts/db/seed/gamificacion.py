"""
Sembrador de gamificación.
Asigna puntos de experiencia y registros (logs) por las contribuciones previas de los usuarios,
actualizando sus niveles y recompensas simuladas.
"""
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.dialects.mysql import insert
from backend.models import (
    Usuario, UsuarioVisitante, LogPuntos, Resena, Imagen
)

def seed_log_puntos(db: Session):
    print("Sembrando log de puntos...")
    # Solo visitantes no-ideales
    visitantes = db.query(UsuarioVisitante).join(Usuario).filter(~Usuario.email.like("%@ideal.eki.internal%")).all()
    
    # Pre-calcular puntos para evitar sobreescrituras en múltiples ejecuciones
    count_logs = db.query(LogPuntos).count()
    if count_logs > 0:
        print("Ya existen registros de log_puntos. Se omite para evitar duplicados.")
    else:
        logs_a_insertar = []
        for uv in visitantes:
            # Puntos por reseñas aprobadas
            resenas = db.query(Resena).filter_by(id_usuario=uv.id_usuario, estado="aprobado").all()
            for r in resenas:
                logs_a_insertar.append({
                    "id_usuario": uv.id_usuario,
                    "puntos": 15,
                    "motivo": "resena_aprobada",
                    "fecha": r.fecha_resena
                })
            
            # Puntos por fotos aprobadas
            fotos = db.query(Imagen).filter_by(id_usuario_upload=uv.id_usuario, estado="aprobado").all()
            for f in fotos:
                logs_a_insertar.append({
                    "id_usuario": uv.id_usuario,
                    "puntos": 10,
                    "motivo": "foto_aprobada",
                    "fecha": f.fecha_upload
                })
                
            # Algunos puntos aleatorios por nuevo lugar o contribución
            if random.random() < 0.2:
                logs_a_insertar.append({
                    "id_usuario": uv.id_usuario,
                    "puntos": 50,
                    "motivo": "nuevo_lugar",
                    "fecha": datetime.now(timezone.utc) - timedelta(days=random.randint(1, 45))
                })
            if random.random() < 0.3:
                logs_a_insertar.append({
                    "id_usuario": uv.id_usuario,
                    "puntos": 20,
                    "motivo": "contribucion_aprobada",
                    "fecha": datetime.now(timezone.utc) - timedelta(days=random.randint(1, 45))
                })
                
        if logs_a_insertar:
            db.execute(insert(LogPuntos).values(logs_a_insertar))
            db.commit()

def recalcular_puntos_experiencia(db: Session):
    print("Recalculando puntos_experiencia de usuarios...")
    # Ejecutar SQL directo como especifica el plan
    sql = text("""
        UPDATE usuario_visitante uv
        SET puntos_experiencia = COALESCE(
            (SELECT SUM(puntos) FROM log_puntos WHERE id_usuario = uv.id_usuario), 0
        );
    """)
    db.execute(sql)
    db.commit()

def seed_gamificacion_completo(db: Session):
    seed_log_puntos(db)
    recalcular_puntos_experiencia(db)
    print("Bloque de gamificación completado.")
