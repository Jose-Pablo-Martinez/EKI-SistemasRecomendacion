import random
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.dialects.mysql import insert
from backend.models import (
    Establecimiento, Categoria, Etiqueta, EstablecimientoCategoria,
    EstablecimientoEtiqueta, PreferenciaUsuario, UsuarioPropietario,
    PropietarioEstablecimiento, UsuarioVisitante, Usuario, Administrador
)

def seed_establecimiento_contenido(db: Session):
    print("Sembrando categorías y etiquetas de establecimientos...")
    estabs = db.query(Establecimiento).all()
    categorias_hojas = db.query(Categoria).filter(Categoria.id_categoria_padre.isnot(None)).all()
    etiquetas = db.query(Etiqueta).all()
    
    cat_data = []
    eti_data = []
    
    for e in estabs:
        # Solo insertar si el establecimiento no tiene categorías aún
        tiene_cats = db.query(EstablecimientoCategoria).filter_by(id_establecimiento=e.id_establecimiento).count() > 0
        if not tiene_cats:
            num_cat = random.randint(2, min(4, len(categorias_hojas)))
            cats_elegidas = random.sample(categorias_hojas, num_cat)
            for c in cats_elegidas:
                cat_data.append({"id_establecimiento": e.id_establecimiento, "id_categoria": c.id_categoria})
        
        # Solo insertar si el establecimiento no tiene etiquetas aún
        tiene_etis = db.query(EstablecimientoEtiqueta).filter_by(id_establecimiento=e.id_establecimiento).count() > 0
        if not tiene_etis:
            num_eti = random.randint(2, min(5, len(etiquetas)))
            eti_elegidas = random.sample(etiquetas, num_eti)
            for et in eti_elegidas:
                eti_data.append({"id_establecimiento": e.id_establecimiento, "id_etiqueta": et.id_etiqueta})
            
    if cat_data:
        db.execute(insert(EstablecimientoCategoria).prefix_with("IGNORE").values(cat_data))
        db.commit()
    if eti_data:
        db.execute(insert(EstablecimientoEtiqueta).prefix_with("IGNORE").values(eti_data))
        db.commit()

def seed_preferencia_usuario(db: Session):
    print("Sembrando preferencias de usuarios...")
    visitantes = db.query(UsuarioVisitante).filter_by(perfil_completado=True).all()
    categorias_hojas = db.query(Categoria).filter(Categoria.id_categoria_padre.isnot(None)).all()
    
    pref_data = []
    for uv in visitantes:
        num_cat = random.randint(3, min(6, len(categorias_hojas)))
        cats_elegidas = random.sample(categorias_hojas, num_cat)
        for c in cats_elegidas:
            pref_data.append({
                "id_usuario": uv.id_usuario,
                "id_categoria": c.id_categoria,
                "peso": random.uniform(0.5, 1.0)
            })
    
    if pref_data:
        # PreferenciaUsuario usa id_usuario e id_categoria como PK compuesta
        # On duplicate key update peso
        stmt = insert(PreferenciaUsuario).values(pref_data)
        stmt = stmt.on_duplicate_key_update(peso=stmt.inserted.peso)
        db.execute(stmt)
        db.commit()

def seed_vinculos_propietario(db: Session):
    print("Sembrando vínculos de propietarios...")
    admin = db.query(Administrador).first()
    vinculos = [
        ("Roberto", "La Lupita"),
        ("Carmen", "Puesto Xtabentún"),
        ("Miguel", "Cocina Económica Marcelina"),
        ("Miguel", "Jugos La Raza"),
        ("Patricia", "El Carrito de los Tamales"),
        ("Jorge", "La Chaya Maya"),
        ("Sofía", "Taquería El Trompo"),
        ("Sofía", "Antojitos Doña Rosa"),
        ("Andrés", "Mariscos El Puerto"),
        ("Lucía", "Panadería San Marcos"),
        ("Fernando", "Lonchería Central"),
        ("Verónica", "Café Mérida")
    ]
    
    data_vinculos = []
    for n_prop, n_estab in vinculos:
        # Buscar usuario por primer nombre
        u = db.query(Usuario).filter(Usuario.nombre == n_prop, Usuario.tipo_usuario == "propietario").first()
        e = db.query(Establecimiento).filter_by(nombre=n_estab).first()
        
        if u and e:
            # Recuperar prop
            prop = db.query(UsuarioPropietario).filter_by(id_usuario=u.id_usuario).first()
            if prop:
                data_vinculos.append({
                    "id_propietario": prop.id_usuario,
                    "id_establecimiento": e.id_establecimiento,
                    "estado": "aprobado" if prop.verificado else "pendiente",
                    "fecha_aprobacion": datetime.utcnow() if prop.verificado else None,
                    "id_admin_aprobacion": admin.id_usuario if prop.verificado else None
                })
                
    if data_vinculos:
        db.execute(insert(PropietarioEstablecimiento).prefix_with("IGNORE").values(data_vinculos))
        db.commit()

def seed_contenido_completo(db: Session):
    seed_establecimiento_contenido(db)
    seed_preferencia_usuario(db)
    seed_vinculos_propietario(db)
    print("Bloque de contenido completado.")
