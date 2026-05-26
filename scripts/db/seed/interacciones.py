"""
Sembrador de interacciones y reseñas.
Simula el comportamiento histórico de los usuarios al interactuar con establecimientos (vistas,
favoritos, reseñas), dejando los datos preparados para los motores NLP y de métricas.
"""
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
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
        if not uv:
            continue
        estabs = estabs_por_cluster.get(uv.id_cluster, [])  # type: ignore
        tipos = tipos_por_cluster.get(uv.id_cluster, ["vista_detalle"])  # type: ignore
        
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
            fecha = datetime.now(timezone.utc) - timedelta(days=dias_atras)
            
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
    id_admin = admin.id_usuario if admin else None  # type: ignore
    
    interacciones = []
    resenas = []
    favoritos = []
    reportes = []
    
    # Garantizar que TODOS los establecimientos tengan reseñas e interacciones
    for e in estabs_aprobados:
        # Cada establecimiento recibe entre 2 y 5 reseñas/interacciones
        num_int = random.randint(2, 5)
        usuarios_muestra = random.sample(usuarios, num_int)
        
        for u in usuarios_muestra:
            # Forzamos que al menos el 70% de las interacciones sean reseñas para garantizar estrellas
            if random.random() < 0.7:
                t = "resena_dejada"
            else:
                t = random.choice(list(PESOS_INTERACCION.keys()))
                
            sesion = db.query(SesionUsuario).filter_by(id_usuario=u.id_usuario).first()
            sesion_id = sesion.id_sesion if sesion else None
            
            # 40% de probabilidad de ser reciente (últimos 7 días) para nutrir métricas de tendencias
            if random.random() < 0.40:
                dias_atras = random.randint(0, 7)
            else:
                dias_atras = random.randint(8, 45)
            fecha = datetime.now(timezone.utc) - timedelta(days=dias_atras)
            
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
                estado = "aprobado"
                procesado = (random.random() > 0.3)
                
                resenas.append({
                    "id_usuario": u.id_usuario,
                    "id_establecimiento": e.id_establecimiento,
                    "calificacion": random.randint(3, 5),
                    "comentario": f"Excelente lugar, recomiendo {e.nombre} ampliamente.",
                    "fecha_resena": fecha,
                    "estado": estado,
                    "id_admin_revision": id_admin if estado != "pendiente" else None,
                    "fecha_revision": datetime.now(timezone.utc) if estado != "pendiente" else None,
                    "polaridad": random.uniform(0.1, 0.9) if procesado else None,
                    "subjetividad": random.uniform(0.1, 0.9) if procesado else None,
                    "procesado_nlp": procesado
                })
                
            if t == "guardado_favorito":
                favoritos.append({
                    "id_usuario": u.id_usuario,
                    "id_establecimiento": e.id_establecimiento,
                    "fecha_guardado": fecha
                })
                
        # Reportes (10% de probabilidad por establecimiento)
        if random.random() < 0.10:
            reportes.append({
                "id_usuario": random.choice(usuarios).id_usuario,
                "id_establecimiento": e.id_establecimiento,
                "tipo_reporte": "spam",
                "descripcion": "Reporte de prueba",
                "estado": "pendiente"
            })
            
    # Además de garantizar reseñas por lugar, añadimos volumen extra por usuario para engordar el historial
    for u in usuarios:
        # Entre 5 y 15 interacciones extra por usuario
        num_extra = random.randint(5, 15)
        sesion = db.query(SesionUsuario).filter_by(id_usuario=u.id_usuario).first()
        sesion_id = sesion.id_sesion if sesion else None
        
        for _ in range(num_extra):
            e = random.choice(estabs_aprobados)
            # Evitamos reseña dejada aquí para no duplicar/saturar estrellas
            tipos_extra = [t for t in PESOS_INTERACCION.keys() if t != "resena_dejada"]
            t = random.choice(tipos_extra)
            
            dias_atras = random.randint(0, 45)
            fecha = datetime.now(timezone.utc) - timedelta(days=dias_atras)
            
            interacciones.append({
                "id_usuario": u.id_usuario,
                "id_establecimiento": e.id_establecimiento,
                "tipo_interaccion": t,
                "peso_interaccion": PESOS_INTERACCION[t],
                "id_sesion": sesion_id,
                "fecha": fecha
            })
            
            if t == "guardado_favorito":
                favoritos.append({
                    "id_usuario": u.id_usuario,
                    "id_establecimiento": e.id_establecimiento,
                    "fecha_guardado": fecha
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
            e.total_resenas = total           # type: ignore
            e.calificacion_promedio = float(promedio)  # type: ignore
        else:
            e.total_resenas = 0              # type: ignore
            e.calificacion_promedio = 0.0   # type: ignore
    db.commit()

def seed_interacciones_completo(db: Session):
    seed_interacciones_ideales(db)
    seed_interacciones_normales_y_resenas(db)
    print("Bloque de interacciones completado.")
