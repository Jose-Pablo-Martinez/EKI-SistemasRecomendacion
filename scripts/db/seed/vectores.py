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
    dim = 22  # Dimensión real usada por los clusters y el frontend (categorías + precios)
    
    # 1. Llenar establecimientos
    establecimientos = db.query(Establecimiento).all()
    for e in establecimientos:
        # Vector aleatorio entre 0 y 1
        e.vector_caracteristicas = [round(random.uniform(0, 1), 4) for _ in range(dim)] # type: ignore[assignment]
        
    # 2. Llenar usuarios visitantes (solo si no tienen un vector numérico válido de dimensión correcta)
    usuarios = db.query(UsuarioVisitante).all()
    for u in usuarios:
        vec = u.vector_preferencias
        # El onboarding guarda el vector como dict {"categorias_preferidas":[], "numerico":[...]}
        # En ese caso extraemos la parte numérica para verificar la dimensión real
        if isinstance(vec, dict):
            vec_numerico = vec.get("numerico", [])
        else:
            vec_numerico = vec or []
        
        # Solo sobreescribir si el vector no existe, no es lista, o tiene dimensión incorrecta
        if not isinstance(vec_numerico, list) or len(vec_numerico) != dim:
            u.vector_preferencias = [round(random.uniform(0, 1), 4) for _ in range(dim)] # type: ignore[assignment]
        
    db.commit()
    print(f"¡Éxito! Se generaron vectores matemáticos para {len(establecimientos)} establecimientos y {len(usuarios)} usuarios.")

