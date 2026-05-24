from sqlalchemy.orm import Session
from backend.models import Pais, EstadoGeo, Municipio, Colonia, RangoInformador, Categoria, Etiqueta
from sqlalchemy.dialects.mysql import insert

def seed_geografia(db: Session):
    print("Sembrando geografía...")
    # País
    if not db.query(Pais).first():
        stmt_pais = insert(Pais).prefix_with("IGNORE").values([
            {"id_pais": "MX", "nombre": "México"}
        ])
        db.execute(stmt_pais)
        db.commit()

    # Estado
    if not db.query(EstadoGeo).first():
        estado_stmt = insert(EstadoGeo).prefix_with("IGNORE").values([
            {"id_pais": "MX", "nombre": "Yucatán"}
        ])
        db.execute(estado_stmt)
        db.commit()
    estado = db.query(EstadoGeo).filter_by(nombre="Yucatán").first()
    if not estado:
        print("Error: no se encontró EstadoGeo 'Yucatán' para continuar.")
        return

    # Municipios
    if not db.query(Municipio).first():
        municipios_data = [
            {"id_estado": estado.id_estado, "nombre": n} for n in [
                "Mérida", "Kanasín", "Umán", "Progreso", "Conkal", "Ucú", "Hunucmá", "Motul"
            ]
        ]
        db.execute(insert(Municipio).prefix_with("IGNORE").values(municipios_data))
        db.commit()

    merida = db.query(Municipio).filter_by(nombre="Mérida").first()
    if not merida:
        print("Error: no se encontró Municipio 'Mérida' para continuar.")
        return

    # Colonias (Mérida)
    if not db.query(Colonia).first():
        zonas_colonias = {
            "Centro histórico": ["Centro", "Santiago", "Santa Ana", "Santa Lucía", "San Cristóbal", "Mejorada", "San Sebastián", "Santa Catalina"],
            "Norte residencial": ["Altabrisa", "Montejo", "Chuburná", "La Ceiba", "Cholul", "Fraccionamiento Las Américas", "Gran Santa Fe", "Villas del Sol"],
            "Norponiente": ["Temozón Norte", "Caucel", "Komchén", "Ciudad Caucel", "Dzityá"],
            "Oriente popular": ["Pensiones", "Jesús Carranza", "Morelos", "Emiliano Zapata Norte", "Emiliano Zapata Sur", "Mulsay"],
            "Sur / Periférica": ["García Ginerés", "Itzimná", "Sambulá", "Francisco de Montejo", "Miguel Hidalgo", "Pacabtún"],
            "Corredor gastronómico": ["Paseo de Montejo", "Prolongación Montejo", "Buenavista", "Colonia México", "Residencial Pensiones"],
            "Mercados y zonas informales": ["Chuminópolis", "San Marcos", "La Ermita", "San Rafael", "Salvador Alvarado Norte", "Salvador Alvarado Sur", "San Roque", "San José Tecoh", "San Antonio Xluch", "San José", "San Luis Sur", "San Pedro Cholul", "San Antonio Xluch III", "San Antonio Xluch II", "San Antonio Xluch I"],
            "Periferia y nuevos desarrollos": ["Gran Prado", "Cumbres", "Real Montejo", "Villas del Norte", "Yucalpetén"]
        }
        
        colonias_data = []
        for zona, colonias in zonas_colonias.items():
            for c in colonias:
                colonias_data.append({"id_municipio": merida.id_municipio, "nombre": c})
        
        db.execute(insert(Colonia).prefix_with("IGNORE").values(colonias_data))
        db.commit()
        print(f"Geografía completada: {len(colonias_data)} colonias de Mérida registradas.")
    else:
        print("Geografía ya existente, saltando...")

def seed_rangos(db: Session):
    print("Sembrando rangos de informador...")
    if not db.query(RangoInformador).first():
        rangos = [
            {"nivel": 1, "nombre": "Explorador", "puntos_minimos": 0, "factor_confianza": 0.30, "color_badge": "#9CA3AF"},
            {"nivel": 2, "nombre": "Conocedor", "puntos_minimos": 100, "factor_confianza": 0.50, "color_badge": "#60A5FA"},
            {"nivel": 3, "nombre": "Guía Local", "puntos_minimos": 300, "factor_confianza": 0.70, "color_badge": "#34D399"},
            {"nivel": 4, "nombre": "Experto", "puntos_minimos": 700, "factor_confianza": 0.85, "color_badge": "#F59E0B"},
            {"nivel": 5, "nombre": "Maestro", "puntos_minimos": 1500, "factor_confianza": 1.00, "color_badge": "#8B5CF6"}
        ]
        db.execute(insert(RangoInformador).prefix_with("IGNORE").values(rangos))
        db.commit()
    else:
        print("Rangos ya existentes, saltando...")

def seed_categorias(db: Session):
    print("Sembrando categorías gastronómicas...")
    if not db.query(Categoria).first():
        jerarquia = {
            "Cocina Yucateca": ["Comida de Mercado", "Antojitos Yucatecos", "Mariscos Yucatecos", "Cochinita y Pibil"],
            "Cocina Mexicana": ["Tacos y Taquería", "Tortas y Sandwiches", "Antojitos Mexicanos", "Pozole y Caldos"],
            "Bebidas": ["Jugos y Licuados", "Café y Bebidas Calientes", "Aguas Frescas", "Bebidas Fermentadas"],
            "Repostería y Dulces": ["Panadería", "Dulces Regionales", "Helados y Paletas"],
            "Comida Internacional": ["Comida Rápida", "Hamburguesas", "Pizza", "Asiática"],
            "Saludable": ["Ensaladas y Bowls", "Vegano y Vegetariano", "Proteínas y Fitness"]
        }

        # Insertar padres
        padres_data = [{"nombre": padre} for padre in jerarquia.keys()]
        db.execute(insert(Categoria).prefix_with("IGNORE").values(padres_data))
        db.commit()

        # Insertar hijos
        hijos_data = []
        for padre_nombre, hijos in jerarquia.items():
            padre = db.query(Categoria).filter_by(nombre=padre_nombre).first()
            if not padre:
                continue
            for hijo in hijos:
                hijos_data.append({"nombre": hijo, "id_categoria_padre": padre.id_categoria})
        
        db.execute(insert(Categoria).prefix_with("IGNORE").values(hijos_data))
        db.commit()
    else:
        print("Categorías ya existentes, saltando...")

def seed_etiquetas(db: Session):
    print("Sembrando etiquetas...")
    if not db.query(Etiqueta).first():
        etiquetas = [
            "económico", "familiar", "para_llevar", "abierto_temprano", "abierto_tarde",
            "estacionamiento", "acepta_tarjeta", "solo_efectivo", "picante", "sin_picante",
            "vegetariano", "sin_gluten", "wifi", "aire_acondicionado", "terraza",
            "mercado", "puesto_fijo", "carrito", "tradicional", "premiado"
        ]
        etiquetas_data = [{"nombre": e} for e in etiquetas]
        db.execute(insert(Etiqueta).prefix_with("IGNORE").values(etiquetas_data))
        db.commit()
    else:
        print("Etiquetas ya existentes, saltando...")

def seed_catalogo_completo(db: Session):
    seed_geografia(db)
    seed_rangos(db)
    seed_categorias(db)
    seed_etiquetas(db)
    print("Bloque de catálogo completado con éxito.")
