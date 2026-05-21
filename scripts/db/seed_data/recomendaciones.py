import random
from datetime import datetime, timedelta
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.mysql import insert
# pyrefly: ignore [missing-import]
from sqlalchemy import text
from backend.models import (
    Usuario, UsuarioVisitante, Establecimiento, InteraccionUsuario,
    HistorialVisita, RecomendacionGenerada, SesionUsuario
)

def seed_historial_y_sesiones(db: Session):
    print("Sembrando historial de visitas y actualizando sesiones...")
    
    # Obtener todas las interacciones de tipo 'vista_detalle'
    vistas = db.query(InteraccionUsuario).filter_by(tipo_interaccion="vista_detalle").all()
    
    # Revisar si ya existen historiales para evitar duplicidad de seed
    count_historial = db.query(HistorialVisita).count()
    if count_historial == 0 and vistas:
        historiales_a_insertar = []
        for v in vistas:
            historiales_a_insertar.append({
                "id_usuario": v.id_usuario,
                "id_establecimiento": v.id_establecimiento,
                "id_sesion": v.id_sesion,
                "fecha_visita": v.fecha,
                "duracion_segundos": random.randint(30, 300),
                "fue_recomendado": False  # Según plan, 'directo' o false para el seed inicial
            })
            
        db.execute(insert(HistorialVisita).values(historiales_a_insertar))
        db.commit()

    print("Actualizando total_vistas en sesion_usuario...")
    # Ejecutar UPDATE con subconsulta para mantener la invariante
    sql = text("""
        UPDATE sesion_usuario su
        SET total_vistas = COALESCE(
            (SELECT COUNT(*) FROM historial_visita WHERE id_sesion = su.id_sesion), 0
        );
    """)
    db.execute(sql)
    db.commit()

def seed_recomendaciones_generadas(db: Session):
    print("Sembrando recomendaciones generadas...")
    
    # Limpiar recomendaciones generadas previas (son volátiles, el K-Means las recrea)
    db.execute(text("DELETE FROM recomendacion_generada"))
    db.commit()
    
    # Visitantes activos no ideales
    visitantes = db.query(UsuarioVisitante).join(Usuario).filter(~Usuario.email.like("%@ideal.eki.internal%")).all()
    estabs_aprobados = db.query(Establecimiento).filter_by(estado="aprobado").all()
    
    if not estabs_aprobados:
        return
        
    recomendaciones = []
    
    for uv in visitantes:
        # Extraer parámetros del usuario
        is_completed = uv.perfil_completado
        
        # cercania: 5, popularidad_zona: 4, preferencia_contenido: 5, tendencia_informal: 3
        categorias_y_cantidades = [
            ("cercania", 5, "cercano"),
            ("popularidad_zona", 4, "popular_zona"),
            ("preferencia_contenido", 5, "preferencia_categoria"),
            ("tendencia_informal", 3, "tendencia_informal")
        ]
        
        if is_completed:
            categorias_y_cantidades.append(("colaborativo_cluster", 4, "colaborativo"))
            if random.random() < 0.6:
                categorias_y_cantidades.append(("descubrimiento", 2, "descubrimiento"))
        else:
            categorias_y_cantidades.append(("cold_start", 8, "cold_start"))
            
        for cat_nombre, cantidad, razon in categorias_y_cantidades:
            estabs_muestra = random.sample(estabs_aprobados, min(cantidad, len(estabs_aprobados)))
            for pos, e in enumerate(estabs_muestra, start=1):
                recomendaciones.append({
                    "id_usuario": uv.id_usuario,
                    "id_establecimiento": e.id_establecimiento,
                    "categoria_recomendacion": cat_nombre,
                    "posicion": pos,
                    "score_total": random.uniform(0.5, 1.0),
                    "score_contenido_usado": random.uniform(0.3, 0.9),
                    "score_colaborativo_usado": random.uniform(0.3, 0.9),
                    "score_boost_aplicado": random.uniform(0.1, 0.5),
                    "distancia_km": random.uniform(0.5, uv.radio_busqueda_km),
                    "radio_usado_km": uv.radio_busqueda_km,
                    "fallback_nivel": 0,
                    "razon_principal": razon,
                    "detalle_razon": "Recomendado sintético de prueba",
                    "estrategia_usada": "hibrido",
                    "fecha_generacion": datetime.utcnow()
                })
                
    if recomendaciones:
        # Se pueden insertar masivamente ya que truncamos antes
        # Ojo: la tabla es auto_increment, así que está bien
        for i in range(0, len(recomendaciones), 200): # batches
            db.execute(insert(RecomendacionGenerada).values(recomendaciones[i:i+200]))
        db.commit()

def seed_recomendaciones_completo(db: Session):
    seed_historial_y_sesiones(db)
    seed_recomendaciones_generadas(db)
    print("Bloque de recomendaciones completado.")
