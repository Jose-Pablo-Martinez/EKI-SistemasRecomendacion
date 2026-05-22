import random
from datetime import datetime
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.mysql import insert
# pyrefly: ignore [missing-import]
from backend.models import (
    Establecimiento, Restaurante, LocalComercial, PuestoInformal,
    MetricaEstablecimiento, Horario, Platillo, Imagen, Colonia,
    ClusterEstablecimiento, Usuario
)

def seed_establecimientos(db: Session):
    print("Sembrando establecimientos...")
    admin = db.query(Usuario).filter_by(tipo_usuario="admin").first()
    colonias = db.query(Colonia).all()
    clusters = db.query(ClusterEstablecimiento).all()
    
    nombres_rest = ["La Lupita", "La Chaya Maya", "Mariscos El Puerto", "Pizzería Roma", "El Mesón", "Sushito", "Steak House", "Nuevo Restaurante XYZ"]
    nombres_locales = ["Jugos La Raza", "Cocina Económica Marcelina", "Café Mérida", "Panadería San Marcos", "Lonchería Central", "Taquería Paco", "El Buen Sabor"]
    nombres_puestos = ["Tacos El Camarón", "Sopa de Lima Doña Pati", "El Carrito de los Tamales", "Taquería El Trompo", "Antojitos Doña Rosa", "Puesto Xtabentún", "Helados La Flor", "Papas y Salchichas", "Elotes Don Pancho", "Marquesitas Yucatecas", "Esquites El Capi", "Tacos de Guisado", "Jugos Frescos", "Tortas de Cochinita", "Tamales Calientitos"]
    
    estados = ["aprobado"] * 26 + ["pendiente"] * 2 + ["rechazado"] * 2
    random.shuffle(estados)
    
    def crear_establecimiento(nombres, tipo_enum, offset):
        for i, nombre in enumerate(nombres):
            estado = estados.pop() if estados else "aprobado"
            
            # Verificar si ya existe
            col = random.choice(colonias) if colonias else None
            existe = db.query(Establecimiento).filter_by(nombre=nombre).first()
            if existe:
                continue
                
            es_informal = (tipo_enum == "puesto_informal")
            cl_id = random.choice(clusters).id_cluster if clusters else None
            
            e = Establecimiento(
                nombre=nombre,
                descripcion=f"Descripción de {nombre}",
                latitud=20.9674 + random.uniform(-0.04, 0.04),
                longitud=-89.6233 + random.uniform(-0.04, 0.04),
                id_colonia=col.id_colonia if col else None,
                id_cluster=cl_id,
                tipo_establecimiento=tipo_enum,
                es_informal=es_informal,
                estado=estado,
                es_activo=(estado == "aprobado"),
                id_usuario_registro=admin.id_usuario,
                id_admin_aprobacion=admin.id_usuario if estado == "aprobado" else None,
                fecha_aprobacion=datetime.utcnow() if estado == "aprobado" else None
            )
            db.add(e)
            db.commit()
            db.refresh(e)
            
            if tipo_enum == "restaurante":
                r = Restaurante(id_restaurante=e.id_establecimiento, precio_promedio=random.uniform(150, 500))
                db.add(r)
            elif tipo_enum == "local":
                l = LocalComercial(id_local=e.id_establecimiento, numero_local=f"L-{i}")
                db.add(l)
            elif tipo_enum == "puesto_informal":
                p = PuestoInformal(id_puesto=e.id_establecimiento, dias_tipicos="Lunes a Sábado")
                db.add(p)
            db.commit()
            
            # Si es aprobado, crear métricas
            if e.estado == "aprobado":
                pop_7d = random.randint(5, 120)
                m = MetricaEstablecimiento(
                    id_establecimiento=e.id_establecimiento,
                    score_contenido_base=random.uniform(0.35, 0.85),
                    score_colaborativo_base=random.uniform(0.20, 0.75),
                    boost_proximidad_zona=random.uniform(0.10, 0.60),
                    boost_informal=0.25 if es_informal else 0.00,
                    score_boost_combinado=random.uniform(0.40, 0.90),
                    popularidad_7d=pop_7d,
                    popularidad_30d=pop_7d * random.randint(2, 6),
                    polaridad_promedio=random.uniform(0.3, 0.9),
                    ultima_actualizacion=datetime.utcnow()
                )
                # Usar merge por si ya existía (idempotencia)
                db.merge(m)
                db.commit()

    crear_establecimiento(nombres_rest, "restaurante", 0)
    crear_establecimiento(nombres_locales, "local", len(nombres_rest))
    crear_establecimiento(nombres_puestos, "puesto_informal", len(nombres_rest)+len(nombres_locales))

def seed_horarios_platillos_imagenes(db: Session):
    print("Sembrando horarios, platillos e imágenes...")
    admin = db.query(Usuario).filter_by(tipo_usuario="admin").first()
    estabs = db.query(Establecimiento).all()
    
    for e in estabs:
        # Horarios (sólo restaurantes y locales)
        if e.tipo_establecimiento in ["restaurante", "local"]:
            count = db.query(Horario).filter_by(id_establecimiento=e.id_establecimiento).count()
            if count == 0:
                horarios = []
                for dia in range(6):  # Lunes a Sábado
                    horarios.append({"id_establecimiento": e.id_establecimiento, "dia_semana": dia, "hora_apertura": "08:00:00", "hora_cierre": "20:00:00", "cerrado": False})
                db.execute(insert(Horario).prefix_with("IGNORE").values(horarios))
                db.commit()
                
        # Platillos
        if db.query(Platillo).filter_by(id_establecimiento=e.id_establecimiento).count() == 0:
            platillos = []
            for j in range(random.randint(2, 4)):
                platillos.append({"id_establecimiento": e.id_establecimiento, "nombre": f"Platillo {j} de {e.nombre}", "precio": random.uniform(50, 200), "id_usuario_registro": admin.id_usuario, "estado": "aprobado"})
            db.execute(insert(Platillo).prefix_with("IGNORE").values(platillos))
            db.commit()

        # Imágenes
        if db.query(Imagen).filter_by(id_establecimiento=e.id_establecimiento).count() == 0:
            imagenes = []
            for k in range(random.randint(1, 3)):
                imagenes.append({"id_establecimiento": e.id_establecimiento, "url_imagen": f"https://example.com/img_{e.id_establecimiento}_{k}.jpg", "id_usuario_upload": admin.id_usuario, "estado": "aprobado", "es_principal": (k==0)})
            db.execute(insert(Imagen).prefix_with("IGNORE").values(imagenes))
            db.commit()

def seed_establecimientos_completo(db: Session):
    seed_establecimientos(db)
    seed_horarios_platillos_imagenes(db)
    print("Bloque de establecimientos completado.")
