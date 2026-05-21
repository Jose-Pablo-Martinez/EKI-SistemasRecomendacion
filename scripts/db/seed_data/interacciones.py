import random
from datetime import datetime, timedelta
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from sqlalchemy.sql import func
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.mysql import insert
from backend.models import (
    Usuario, UsuarioVisitante, Establecimiento, InteraccionUsuario,
    Resena, FavoritoGuardado, Reporte, SesionUsuario, Administrador
)

PESOS_INTERACCION = {
    "vista_detalle": 0.1,
    "guardado_favorito": 0.5,
    "compartido": 0.3,
    "llamada_telefono": 0.6,
    "abrir_maps": 0.7,
    "resena_dejada": 1.0,
    "ruta_calculada": 0.9
}

def seed_interacciones_ideales(db: Session):
    print("Sembrando interacciones de usuarios ideales...")
    # Usuarios ideales
    usuarios_ideales = db.query(Usuario).filter(Usuario.email.like("%@ideal.eki.internal%")).all()
    if not usuarios_ideales:
        return
        
    estabs_por_cluster = {
        1: db.query(Establecimiento).filter_by(id_cluster=1, estado="aprobado").all(),
        2: db.query(Establecimiento).filter_by(id_cluster=2, estado="aprobado").all(),
        3: db.query(Establecimiento).filter_by(id_cluster=3, estado="aprobado").all() + db.query(Establecimiento).filter_by(id_cluster=4, estado="aprobado").all(),
        4: db.query(Establecimiento).filter_by(id_cluster=3, estado="aprobado").all() + db.query(Establecimiento).filter_by(id_cluster=4, estado="aprobado").all()
    }
    
    tipos_por_cluster = {
        1: ["vista_detalle", "abrir_maps", "ruta_calculada"],
        2: ["llamada_telefono", "resena_dejada", "guardado_favorito"],
        3: ["abrir_maps", "ruta_calculada", "compartido"],
        4: ["vista_detalle", "resena_dejada"]
    }
    
    interacciones = []
    
    for u in usuarios_ideales:
        uv = db.query(UsuarioVisitante).filter_by(id_usuario=u.id_usuario).first()
        estabs = estabs_por_cluster.get(uv.id_cluster, [])
        tipos = tipos_por_cluster.get(uv.id_cluster, ["vista_detalle"])
        
        if not estabs:
            continue
            
        # Verificar si ya tiene interacciones
        count = db.query(InteraccionUsuario).filter_by(id_usuario=u.id_usuario).count()
        if count >= 15:
            continue
            
        for _ in range(15):
            e = random.choice(estabs)
            t = random.choice(tipos)
            dias_atras = random.randint(60, 90)
            fecha = datetime.utcnow() - timedelta(days=dias_atras)
            
            interacciones.append({
                "id_usuario": u.id_usuario,
                "id_establecimiento": e.id_establecimiento,
                "tipo_interaccion": t,
                "peso_interaccion": PESOS_INTERACCION[t],
                "fecha": fecha
            })
            
    if interacciones:
        db.execute(insert(InteraccionUsuario).prefix_with("IGNORE").values(interacciones))
        db.commit()

def seed_interacciones_normales_y_resenas(db: Session):
    print("Sembrando interacciones normales, reseñas, favoritos y reportes...")
    usuarios = db.query(Usuario).filter(
        Usuario.tipo_usuario.in_(["visitante", "propietario"]),
        ~Usuario.email.like("%@ideal.eki.internal%")
    ).all()
    
    estabs_aprobados = db.query(Establecimiento).filter_by(estado="aprobado").all()
    if not estabs_aprobados or not usuarios:
        return
        
    admin = db.query(Administrador).first()
    
    interacciones = []
    resenas = []
    favoritos = []
    reportes = []
    
    for u in usuarios:
        # 3 a 5 interacciones por usuario
        num_int = random.randint(3, 5)
        uv = db.query(UsuarioVisitante).filter_by(id_usuario=u.id_usuario).first()
        # Sesión del usuario
        sesion = db.query(SesionUsuario).filter_by(id_usuario=u.id_usuario).first()
        sesion_id = sesion.id_sesion if sesion else None
        
        for _ in range(num_int):
            e = random.choice(estabs_aprobados)
            t = random.choice(list(PESOS_INTERACCION.keys()))
            fecha = datetime.utcnow() - timedelta(days=random.randint(1, 45))
            
            interacciones.append({
                "id_usuario": u.id_usuario,
                "id_establecimiento": e.id_establecimiento,
                "tipo_interaccion": t,
                "peso_interaccion": PESOS_INTERACCION[t],
                "id_sesion": sesion_id,
                "fecha": fecha
            })
            
            # Si es reseña_dejada, preparar reseña
            if t == "resena_dejada":
                # Distribución: 80% aprobado, 15% pdte, 5% rechazada
                rand = random.random()
                estado = "aprobado" if rand < 0.8 else ("pendiente" if rand < 0.95 else "rechazado")
                resenas.append({
                    "id_usuario": u.id_usuario,
                    "id_establecimiento": e.id_establecimiento,
                    "calificacion": random.randint(3, 5),
                    "comentario": f"Comentario de prueba para {e.nombre}",
                    "fecha_resena": fecha,
                    "estado": estado,
                    "id_admin_revision": admin.id_usuario if estado != "pendiente" else None,
                    "fecha_revision": datetime.utcnow() if estado != "pendiente" else None,
                    "polaridad": random.uniform(0.1, 0.9) if estado == "aprobado" else None,
                    "subjetividad": random.uniform(0.1, 0.9) if estado == "aprobado" else None,
                    "procesado_nlp": (estado == "aprobado")
                })
                
            if t == "guardado_favorito":
                favoritos.append({
                    "id_usuario": u.id_usuario,
                    "id_establecimiento": e.id_establecimiento,
                    "fecha_guardado": fecha
                })
                
        # Reportes (10-15 en total aprox, probabilidad baja)
        if random.random() < 0.15:
            reportes.append({
                "id_usuario": u.id_usuario,
                "id_establecimiento": random.choice(estabs_aprobados).id_establecimiento,
                "motivo": "spam",
                "descripcion": "Reporte de prueba",
                "estado": "pendiente"
            })
            
    if interacciones:
        # No podemos usar INSERT IGNORE tan fácil porque la PK es autoincrement y
        # podríamos insertar duplicados si corremos el script varias veces,
        # así que verificamos que la tabla esté vacía para normales o usamos una subconsulta.
        # Por simplicidad del seed: si ya hay interacciones normales, evitamos.
        count_norm = db.query(InteraccionUsuario).join(Usuario).filter(~Usuario.email.like("%@ideal%")).count()
        if count_norm == 0:
            db.execute(insert(InteraccionUsuario).values(interacciones))
            db.commit()
            
    if resenas:
        db.execute(insert(Resena).prefix_with("IGNORE").values(resenas))
        db.commit()
        
    if favoritos:
        db.execute(insert(FavoritoGuardado).prefix_with("IGNORE").values(favoritos))
        db.commit()
        
    if reportes:
        count_rep = db.query(Reporte).count()
        if count_rep == 0:
            db.execute(insert(Reporte).values(reportes))
            db.commit()
            
    # Recalcular calificaciones de establecimientos
    print("Recalculando total_resenas y calificacion_promedio...")
    for e in estabs_aprobados:
        resenas_aprobadas = db.query(Resena).filter_by(id_establecimiento=e.id_establecimiento, estado="aprobado").all()
        total = len(resenas_aprobadas)
        if total > 0:
            promedio = sum(r.calificacion for r in resenas_aprobadas) / total
            e.total_resenas = total
            e.calificacion_promedio = promedio
        else:
            e.total_resenas = 0
            e.calificacion_promedio = 0.0
    db.commit()

def seed_interacciones_completo(db: Session):
    seed_interacciones_ideales(db)
    seed_interacciones_normales_y_resenas(db)
    print("Bloque de interacciones completado.")
