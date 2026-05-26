"""
Sembrador de usuarios.
Crea perfiles para administradores, usuarios ideales (anclas de los clusters),
usuarios visitantes comunes y propietarios, inicializando sus sesiones y ubicaciones.
"""
import uuid
import random
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy.dialects.mysql import insert
from backend.models import (
    Usuario, Administrador, UsuarioVisitante, UsuarioPropietario,
    SesionUsuario, UbicacionUsuario, RangoInformador
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Cachear el hash para acelerar el script
PASSWORD_HASH = pwd_context.hash("Testpass123!")

def seed_usuarios(db: Session):
    print("Sembrando usuarios (admin, ideales, visitantes, propietarios)...")
    
    # 1. Admin
    admin_email = "admin@eki.mx"
    if not db.query(Usuario).filter_by(email=admin_email).first():
        usuario_admin = Usuario(
            email=admin_email,
            nombre="Admin",
            apellido="EKI",
            password_hash=PASSWORD_HASH,
            tipo_usuario="admin"
        )
        db.add(usuario_admin)
        db.commit()
        db.refresh(usuario_admin)
        admin = Administrador(
            id_usuario=usuario_admin.id_usuario,
            nivel_admin=2,
            departamento="Operaciones"
        )
        db.add(admin)
        db.commit()

    # Rangos para asignación
    rangos = db.query(RangoInformador).all()
    rango_1 = next((r for r in rangos if r.nivel == 1), None)

    # 2. Usuarios Ideales (20, 5 por cluster)
    from scripts.db.seed.clusters import c1_vector, c2_vector, c3_vector, c4_vector
    clusters_vectors = {
        1: c1_vector,
        2: c2_vector,
        3: c3_vector,
        4: c4_vector
    }
    
    for cluster_id, vector in clusters_vectors.items():
        for i in range(1, 6):
            email = f"ideal_c{cluster_id}_{i}@ideal.eki.internal"
            if not db.query(Usuario).filter_by(email=email).first():
                # Añadir ligera variación (ruido +- 0.05)
                vec_variado = [max(0.0, min(1.0, v + random.uniform(-0.05, 0.05))) for v in vector]
                u = Usuario(
                    email=email,
                    nombre=f"[IDEAL] C{cluster_id}",
                    apellido=f"Ancla {i}",
                    password_hash=PASSWORD_HASH,
                    tipo_usuario="visitante",
                    activo=True
                )
                db.add(u)
                db.commit()
                db.refresh(u)
                uv = UsuarioVisitante(
                    id_usuario=u.id_usuario,
                    id_rango=rango_1.id_rango if rango_1 else None,
                    id_cluster=cluster_id,
                    perfil_completado=True,
                    puntos_experiencia=0,
                    vector_preferencias=vec_variado,
                    fecha_ultima_actividad=datetime.now(timezone.utc)
                )
                db.add(uv)
                db.commit()

    # 3. Usuarios Visitantes (100)
    grupos = [
        {"cluster": 1, "cantidad": 30, "perfil_false": 2, "radio": 4},
        {"cluster": 2, "cantidad": 25, "perfil_false": 1, "radio": 7},
        {"cluster": 3, "cantidad": 25, "perfil_false": 2, "radio": 6},
        {"cluster": 4, "cantidad": 20, "perfil_false": 1, "radio": 11}
    ]
    
    nombres = ["Juan", "María", "Carlos", "Ana", "Luis", "Elena", "José", "Laura", "Pedro", "Sofía"]
    apellidos = ["Pérez", "Gómez", "López", "Martínez", "González", "Rodríguez", "Fernández", "Ruiz"]
    
    # Distribución de rangos normal (1 al 5)
    rangos_list = [1]*45 + [2]*30 + [3]*15 + [4]*7 + [5]*3
    random.shuffle(rangos_list)
    
    for g in grupos:
        for i in range(g["cantidad"]):
            email = f"user_g{g['cluster']}_{i}@eki.test"
            if not db.query(Usuario).filter_by(email=email).first():
                u = Usuario(
                    email=email,
                    nombre=random.choice(nombres),
                    apellido=random.choice(apellidos),
                    password_hash=PASSWORD_HASH,
                    tipo_usuario="visitante",
                    activo=True
                )
                db.add(u)
                db.commit()
                db.refresh(u)
                
                perfil_completado = i >= g["perfil_false"]
                # Asignar un nivel de rango de la lista, si se acaba, nivel 1
                nivel_rango = rangos_list.pop() if rangos_list else 1
                r_id = next((r.id_rango for r in rangos if r.nivel == nivel_rango), None)
                
                uv = UsuarioVisitante(
                    id_usuario=u.id_usuario,
                    id_rango=r_id,
                    id_cluster=g["cluster"] if perfil_completado else None,
                    perfil_completado=perfil_completado,
                    radio_busqueda_km=g["radio"],
                    vector_preferencias=clusters_vectors[g["cluster"]] if perfil_completado else None,
                    fecha_ultima_actividad=datetime.now(timezone.utc)
                )
                db.add(uv)
                db.commit()

    # 4. Usuarios Propietarios (30)
    propietarios_data = []
    nombres_prop = ["Roberto", "Carmen", "Miguel", "Patricia", "Jorge", "Sofía", "Andrés", "Lucía", "Fernando", "Verónica", "Alejandro", "Daniela", "Hugo", "Valeria", "Ricardo", "Camila", "Manuel", "Gabriela", "Javier", "Diana"]
    apellidos_prop = ["Díaz", "Uc", "Tzuc", "Ceh", "Medina", "Canul", "Balam", "Mena", "Dzul", "Poot", "Pech", "Chan", "Cen", "May", "Ayala", "Canto", "Brito", "Cortes"]
    
    for i in range(30):
        propietarios_data.append({
            "n": random.choice(nombres_prop),
            "a": random.choice(apellidos_prop),
            "v": random.random() > 0.2  # 80% verificados
        })
    
    for i, p in enumerate(propietarios_data):
        email = f"propietario_{i}@eki.test"
        if not db.query(Usuario).filter_by(email=email).first():
            u = Usuario(
                email=email,
                nombre=p["n"],
                apellido=p["a"],
                password_hash=PASSWORD_HASH,
                tipo_usuario="propietario",
                activo=True
            )
            db.add(u)
            db.commit()
            db.refresh(u)
            
            # También necesitan UsuarioVisitante
            r_id = next((r.id_rango for r in rangos if r.nivel == 2), None)
            uv = UsuarioVisitante(
                id_usuario=u.id_usuario,
                id_rango=r_id,
                id_cluster=random.choice([2, 4]),
                perfil_completado=True,
                radio_busqueda_km=8,
                fecha_ultima_actividad=datetime.now(timezone.utc)
            )
            db.add(uv)
            db.commit()
            
            up = UsuarioPropietario(
                id_usuario=u.id_usuario,
                razon_social=f"{p['n']} {p['a']} S.A.",
                verificado=p["v"],
                fecha_verificacion=datetime.now(timezone.utc) if p["v"] else None
            )
            db.add(up)
            db.commit()

def seed_sesiones_ubicaciones(db: Session):
    print("Sembrando sesiones y ubicaciones...")
    usuarios_activos = db.query(UsuarioVisitante).filter_by(perfil_completado=True).all()
    # Excluir ideales
    usuarios_activos = [u for u in usuarios_activos if "@ideal.eki.internal" not in u.usuario.email]
    
    sesiones_a_insertar = []
    ubicaciones_a_insertar = []
    
    for uv in usuarios_activos:
        # Verificar si ya tiene ubicación
        tiene_ub = db.query(UbicacionUsuario).filter_by(id_usuario=uv.id_usuario).count() > 0
        if not tiene_ub:
            # Lat/Lon de Mérida (con variación)
            lat = 20.9674 + random.uniform(-0.02, 0.02)
            lon = -89.6233 + random.uniform(-0.02, 0.02)
            
            # Crear 1 sesión histórica por usuario activo
            sesion_id = str(uuid.uuid4())
            inicio = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 80))
            fin = inicio + timedelta(minutes=random.randint(5, 120))
            
            # Ignoramos session creation if we don't want duplicates but UUID is random.
            # We'll just create it directly
            sesiones_a_insertar.append({
                "id_sesion": sesion_id,
                "id_usuario": uv.id_usuario,
                "fecha_inicio": inicio,
                "fecha_fin": fin,
                "duracion_segundos": int((fin - inicio).total_seconds()),
                "total_vistas": 0
            })
            
            ubicaciones_a_insertar.append({
                "id_usuario": uv.id_usuario,
                "latitud": lat,
                "longitud": lon,
                "id_sesion": sesion_id,
                "precision_metros": 15
            })
            
    if sesiones_a_insertar:
        db.execute(insert(SesionUsuario).prefix_with("IGNORE").values(sesiones_a_insertar))
        db.commit()
    if ubicaciones_a_insertar:
        db.execute(insert(UbicacionUsuario).prefix_with("IGNORE").values(ubicaciones_a_insertar))
        db.commit()

def seed_usuarios_completo(db: Session):
    seed_usuarios(db)
    seed_sesiones_ubicaciones(db)
    print("Bloque de usuarios completado.")
