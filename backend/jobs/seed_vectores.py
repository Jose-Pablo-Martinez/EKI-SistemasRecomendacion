import sys
import os
import random
from sqlalchemy.orm import Session

# Asegurar que el backend está en el path para poder importar
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import SessionLocal
from backend.models.establecimientos import Establecimiento
from backend.models.usuarios import UsuarioVisitante

def seed_vectores():
    db: Session = SessionLocal()
    try:
        dim = 5  # Dimensión de nuestros vectores matemáticos
        
        # 1. Llenar establecimientos
        establecimientos = db.query(Establecimiento).all()
        for e in establecimientos:
            # Vector aleatorio entre 0 y 1
            e.vector_caracteristicas = [round(random.uniform(0, 1), 4) for _ in range(dim)]
            
        # 2. Llenar usuarios visitantes
        usuarios = db.query(UsuarioVisitante).all()
        for u in usuarios:
            u.vector_preferencias = [round(random.uniform(0, 1), 4) for _ in range(dim)]
            
        db.commit()
        print(f"¡Éxito! Se generaron vectores matemáticos para {len(establecimientos)} establecimientos y {len(usuarios)} usuarios.")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_vectores()
