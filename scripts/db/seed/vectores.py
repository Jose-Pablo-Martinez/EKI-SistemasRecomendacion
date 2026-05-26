"""
Sembrador de vectores matemáticos (Mock).
Genera embeddings aleatorios de dimensión 5 para usuarios y establecimientos, permitiendo
que los algoritmos de clustering y filtrado de contenido funcionen en desarrollo sin la API NLP real.
"""
import random
from sqlalchemy.orm import Session
from backend.models.establecimientos import Establecimiento
from backend.models.usuarios import UsuarioVisitante

def seed_vectores(db: Session):
    print("Sembrando vectores matemáticos (Mock NLP)...")
    dim = 5  # Dimensión de nuestros vectores matemáticos
    
    # 1. Llenar establecimientos
    establecimientos = db.query(Establecimiento).all()
    for e in establecimientos:
        # Vector aleatorio entre 0 y 1
        e.vector_caracteristicas = [round(random.uniform(0, 1), 4) for _ in range(dim)] # type: ignore[assignment]
        
    # 2. Llenar usuarios visitantes
    usuarios = db.query(UsuarioVisitante).all()
    for u in usuarios:
        u.vector_preferencias = [round(random.uniform(0, 1), 4) for _ in range(dim)] # type: ignore[assignment]
        
    db.commit()
    print(f"¡Éxito! Se generaron vectores matemáticos para {len(establecimientos)} establecimientos y {len(usuarios)} usuarios.")

