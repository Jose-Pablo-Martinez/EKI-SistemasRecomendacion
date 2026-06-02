"""
Sembrador de establecimientos (Restaurantes, Locales, Puestos Informales).
Se encarga de inyectar lugares físicos, asignarles categorías/etiquetas semánticamente
relevantes y generar su menú, horarios e imágenes base.
"""
import random
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.dialects.mysql import insert
from backend.models import (
    Establecimiento, Restaurante, LocalComercial, PuestoInformal,
    MetricaEstablecimiento, Horario, Platillo, Imagen, Colonia,
    ClusterEstablecimiento, Usuario, Categoria, Etiqueta,
    EstablecimientoCategoria, EstablecimientoEtiqueta
)

def seed_establecimientos(db: Session):
    print("Sembrando establecimientos...")
    admin = db.query(Usuario).filter_by(tipo_usuario="admin").first()
    if not admin:
        print("Error: no se encontró usuario admin. Ejecuta seed_usuarios primero.")
        return
    colonias = db.query(Colonia).all()
    clusters = db.query(ClusterEstablecimiento).all()
    categorias = db.query(Categoria).filter(Categoria.id_categoria_padre.isnot(None)).all()
    etiquetas = db.query(Etiqueta).all()
    
    prefijos_rest = ["Restaurante", "Pizzería", "Mariscos", "Asadero", "Bistro", "Cantina", "Steak House", "Casa", "Hacienda", "El Rincón de"]
    sufijos_rest = ["Roma", "El Puerto", "La Chaya", "La Lupita", "El Mesón", "Los Arrayanes", "El Habanero", "La Pigua", "Kuuk", "San Juan", "Mérida"]
    nombres_rest = list(set([f"{p} {s}" for p in prefijos_rest for s in sufijos_rest]))
    
    prefijos_locales = ["Jugos", "Cocina Económica", "Café", "Panadería", "Lonchería", "Fonda", "Taquería", "Cenaduría"]
    sufijos_locales = ["La Raza", "San Marcos", "Central", "Paco", "El Buen Sabor", "Doña Flor", "El Retorno", "Los Abuelos"]
    nombres_locales = list(set([f"{p} {s}" for p in prefijos_locales for s in sufijos_locales]))
    
    prefijos_puestos = ["Tacos", "Sopa de Lima", "El Carrito de", "Antojitos", "Puesto", "Helados", "Marquesitas", "Esquites", "Tortas de", "Tamales"]
    sufijos_puestos = ["El Camarón", "Doña Pati", "Los Compadres", "El Trompo", "Doña Rosa", "Xtabentún", "La Flor", "El Capi", "Cochinita", "Calientitos", "El Paisa", "San Sebastián"]
    nombres_puestos = list(set([f"{p} {s}" for p in prefijos_puestos for s in sufijos_puestos]))
    
    random.shuffle(nombres_rest)
    random.shuffle(nombres_locales)
    random.shuffle(nombres_puestos)
    
    nombres_rest = nombres_rest[:100]
    nombres_locales = nombres_locales[:50]
    nombres_puestos = nombres_puestos[:100]
    
    # GARANTÍA: Al menos 2 establecimientos por cada categoría hija (42 total)
    categorias_hijas = db.query(Categoria).filter(Categoria.id_categoria_padre.isnot(None)).all()
    
    # Vamos a extraer nombres de nuestras listas para forzarles su categoría
    for cat in categorias_hijas:
        # Extraemos 2 establecimientos para cada categoría
        for _ in range(2):
            if nombres_puestos:
                nombre = nombres_puestos.pop()
                nombres_puestos.insert(0, (nombre, cat)) #type: ignore
            elif nombres_locales:
                nombre = nombres_locales.pop()
                nombres_locales.insert(0, (nombre, cat)) #type: ignore
            elif nombres_rest:
                nombre = nombres_rest.pop()
                nombres_rest.insert(0, (nombre, cat)) #type: ignore
    
    total = len(nombres_rest) + len(nombres_locales) + len(nombres_puestos)
    estados = ["aprobado"] * int(total * 0.9) + ["pendiente"] * int(total * 0.05) + ["rechazado"] * int(total * 0.05)
    while len(estados) < total:
        estados.append("aprobado")
    random.shuffle(estados)
    
    def crear_establecimiento(nombres, tipo_enum, offset):
        for i, item in enumerate(nombres):
            # Soporte para tuplas (nombre, categoria_forzada)
            forced_cat = None
            if isinstance(item, tuple):
                nombre, forced_cat = item
            else:
                nombre = item
                
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
                fecha_aprobacion=datetime.now(timezone.utc) if estado == "aprobado" else None
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
            
            # Asignar Categorías y Etiquetas semánticas basadas en el nombre
            nombre_lower = nombre.lower()
            cats_elegidas = []
            etiqs_elegidas = []
            
            # Mapeo simple basado en palabras clave
            if forced_cat:
                cats_elegidas = [forced_cat]
                if etiquetas: etiqs_elegidas = random.sample(etiquetas, k=2)
            elif "taco" in nombre_lower or "taquería" in nombre_lower or "trompo" in nombre_lower:
                cats_elegidas = [c for c in categorias if "Tacos" in c.nombre]
                etiqs_elegidas = [et for et in etiquetas if et.nombre in ["económico", "tradicional", "para_llevar"]]
            elif "cochinita" in nombre_lower or "pibil" in nombre_lower:
                cats_elegidas = [c for c in categorias if "Cochinita" in c.nombre or "Yucateca" in c.nombre]
                etiqs_elegidas = [et for et in etiquetas if et.nombre in ["tradicional", "abierto_temprano", "para_llevar"]]
            elif "mariscos" in nombre_lower or "camarón" in nombre_lower:
                cats_elegidas = [c for c in categorias if "Mariscos" in c.nombre]
                etiqs_elegidas = [et for et in etiquetas if et.nombre in ["familiar", "tradicional"]]
            elif "pizza" in nombre_lower:
                cats_elegidas = [c for c in categorias if "Pizza" in c.nombre or "Rápida" in c.nombre]
                etiqs_elegidas = [et for et in etiquetas if et.nombre in ["para_llevar", "familiar"]]
            elif "café" in nombre_lower:
                cats_elegidas = [c for c in categorias if "Café" in c.nombre]
                etiqs_elegidas = [et for et in etiquetas if et.nombre in ["wifi", "abierto_temprano"]]
            elif "helados" in nombre_lower or "marquesitas" in nombre_lower:
                cats_elegidas = [c for c in categorias if "Helados" in c.nombre or "Dulces" in c.nombre]
                etiqs_elegidas = [et for et in etiquetas if et.nombre in ["para_llevar", "económico"]]
            elif "lima" in nombre_lower or "chaya" in nombre_lower or "lupita" in nombre_lower:
                cats_elegidas = [c for c in categorias if "Yucateca" in c.nombre or "Caldos" in c.nombre]
                etiqs_elegidas = [et for et in etiquetas if et.nombre in ["tradicional", "familiar"]]
            else:
                # Fallback: asignar algo genérico
                if categorias: cats_elegidas = random.sample(categorias, k=1)
                if etiquetas: etiqs_elegidas = random.sample(etiquetas, k=2)
                
            for c_db in cats_elegidas:
                ec = EstablecimientoCategoria(id_establecimiento=e.id_establecimiento, id_categoria=c_db.id_categoria)
                db.merge(ec)
            for et_db in etiqs_elegidas:
                ee = EstablecimientoEtiqueta(id_establecimiento=e.id_establecimiento, id_etiqueta=et_db.id_etiqueta)
                db.merge(ee)
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
                    ultima_actualizacion=datetime.now(timezone.utc)
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
    if not admin:
        print("Error: no se encontró usuario admin.")
        return
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
