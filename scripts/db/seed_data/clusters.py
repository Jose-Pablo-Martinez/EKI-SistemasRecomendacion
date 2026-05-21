# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from backend.models import ClusterUsuario, ClusterEstablecimiento
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.mysql import insert

def seed_clusters(db: Session):
    print("Sembrando clusters (anclas)...")
    
    # Vectores de centroide extraídos del documento de plan (dimensión 22)
    c1_vector = [0.90, 0.85, 0.30, 0.70, 0.88, 0.50, 0.75, 0.40, 0.80, 0.20, 0.85, 0.30, 0.40, 0.60, 0.70, 0.30, 0.20, 0.10, 0.10, 0.10, 0.10, 0.10]
    c2_vector = [0.30, 0.60, 0.80, 0.85, 0.20, 0.30, 0.20, 0.30, 0.40, 0.75, 0.30, 0.50, 0.30, 0.40, 0.30, 0.40, 0.50, 0.35, 0.45, 0.30, 0.20, 0.25]
    c3_vector = [0.10, 0.15, 0.20, 0.10, 0.20, 0.40, 0.15, 0.10, 0.85, 0.70, 0.60, 0.20, 0.25, 0.15, 0.30, 0.35, 0.30, 0.20, 0.30, 0.90, 0.88, 0.85]
    c4_vector = [0.75, 0.70, 0.40, 0.80, 0.50, 0.40, 0.65, 0.85, 0.45, 0.35, 0.50, 0.20, 0.70, 0.85, 0.60, 0.15, 0.20, 0.10, 0.10, 0.10, 0.10, 0.10]
    
    usuarios_clusters = [
        {"id_cluster": 1, "nombre_cluster": "Exploradores Puestos Informales", "centroide": c1_vector, "descripcion": "Buscan puestos callejeros, mercados, comida barata y tradicional."},
        {"id_cluster": 2, "nombre_cluster": "Exploradores de Restaurantes", "centroide": c2_vector, "descripcion": "Restaurantes formales, variedad gastronómica y experiencias de mayor precio."},
        {"id_cluster": 3, "nombre_cluster": "Exploradores Saludables y Rápidos", "centroide": c3_vector, "descripcion": "Opciones saludables, para llevar y con horarios extendidos."},
        {"id_cluster": 4, "nombre_cluster": "Exploradores de la Familia y Tradición", "centroide": c4_vector, "descripcion": "Lugares amplios, tradicionales, con estacionamiento y para grupos."}
    ]
    
    estab_clusters = [
        {"id_cluster": 1, "nombre_cluster": "Puestos Populares", "centroide": c1_vector, "descripcion": "Alta densidad de puestos informales y carritos en zonas de mercado."},
        {"id_cluster": 2, "nombre_cluster": "Restaurante", "centroide": c2_vector, "descripcion": "Restaurantes con carta, precio medio-alto, zona norte de Mérida."},
        {"id_cluster": 3, "nombre_cluster": "Locales de Mercado", "centroide": c3_vector, "descripcion": "Locales dentro de mercados o plazas populares. Precio económico."},
        {"id_cluster": 4, "nombre_cluster": "Gastronómico Mixto", "centroide": c4_vector, "descripcion": "Establecimientos en corredor gastronómico con precio variado."}
    ]
    
    # Insertar clusters de usuarios
    db.execute(insert(ClusterUsuario).prefix_with("IGNORE").values(usuarios_clusters))
    db.commit()
    
    # Insertar clusters de establecimientos
    db.execute(insert(ClusterEstablecimiento).prefix_with("IGNORE").values(estab_clusters))
    db.commit()
    print("Clusters insertados con éxito.")
