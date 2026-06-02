import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal
from backend.models.usuarios import UsuarioVisitante
from backend.models.establecimientos import Establecimiento
from backend.models.clusters import ClusterUsuario

db = SessionLocal()

print("Cluster centroids dim:")
for c in db.query(ClusterUsuario).all():
    if c.centroide:
        print(f"Cluster {c.id_cluster}: {len(c.centroide)}")

print("\nUsers dim:")
for u in db.query(UsuarioVisitante).limit(10).all():
    v = u.vector_preferencias
    if isinstance(v, dict):
        v = v.get("numerico", [])
    print(f"User {u.id_usuario}: {len(v) if isinstance(v, list) else type(v)}")

print("\nEstablishments dim:")
for e in db.query(Establecimiento).limit(10).all():
    v = e.vector_caracteristicas
    print(f"Est {e.id_establecimiento}: {len(v) if isinstance(v, list) else type(v)}")
