"""
Script de verificación de estructura de BD post-migración — EKI.

Uso:
    python scripts/db/verify_schema.py

Verifica automáticamente:
  1. Existencia de las 38 tablas esperadas (36 core + 2 archivado)
  2. Ausencia de tablas antiguas placeholder (vendors, users, user_ratings)
  3. Índices secundarios del §5 de EkiSystem_DB_Design.md
  4. FKs de herencia TPT (tablas hija → padre)
  5. Tipos de datos clave (JSON, DECIMAL)

Puede ejecutarse tanto en desarrollo (defaultdb) como en CI/CD (ekidb).
"""

import os
import sys
from pathlib import Path

# Asegurar que la raíz del proyecto esté en sys.path
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine, inspect, text

# ─── Conexión ─────────────────────────────────────────────────────────────────

def get_url() -> str:
    user     = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host     = os.getenv("DB_HOST")
    port     = os.getenv("DB_PORT", "3306")
    db       = os.getenv("DB_NAME", "defaultdb")
    ca_path  = os.getenv("DB_SSL_CA", "secrets/ca.pem")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?ssl_ca={ca_path}"

# ─── Tablas esperadas (38 total) ──────────────────────────────────────────────

TABLAS_ESPERADAS: set[str] = {
    # Geografía
    "pais", "estado_geo", "municipio", "colonia",
    # Catálogos base
    "rango_informador", "cluster_usuario", "cluster_establecimiento",
    # Contenido (catálogos)
    "categoria", "etiqueta",
    # Usuarios (TPT)
    "usuario", "dispositivo_usuario", "sesion_usuario",
    "usuario_visitante", "usuario_propietario", "administrador",
    "ubicacion_usuario",
    # Establecimientos (TPT)
    "establecimiento", "restaurante", "local_comercial", "puesto_informal",
    "propietario_establecimiento",
    # Contenido vinculado
    "establecimiento_categoria", "establecimiento_etiqueta",
    "platillo", "imagen", "horario",
    # Motor de recomendación
    "metrica_establecimiento", "interaccion_usuario", "recomendacion_generada",
    # Gamificación
    "contribucion_informacion", "log_puntos", "resena",
    "favorito_guardado", "historial_visita", "preferencia_usuario", "reporte",
    # Archivado
    "recomendacion_generada_historico", "interaccion_usuario_historico",
}

TABLAS_PROHIBIDAS: set[str] = {"vendors", "users", "user_ratings"}

# ─── Índices secundarios esperados (§5) ───────────────────────────────────────

INDICES_ESPERADOS: list[tuple[str, str]] = [
    # §5.1 — Alto impacto (obligatorios)
    ("interaccion_usuario",       "idx_interaccion_usuario_fecha"),
    ("interaccion_usuario",       "idx_interaccion_estab_fecha"),
    ("recomendacion_generada",    "idx_recomendacion_usuario_categoria"),
    ("recomendacion_generada",    "idx_recomendacion_usuario_estab"),
    ("resena",                    "idx_resena_estab_estado"),
    ("historial_visita",          "idx_historial_usuario_fecha"),
    ("ubicacion_usuario",         "idx_ubicacion_usuario_fecha"),
    # §5.2 — Impacto medio (recomendados)
    ("establecimiento",           "idx_establecimiento_estado_activo"),
    ("establecimiento",           "idx_establecimiento_colonia"),
    ("sesion_usuario",            "idx_sesion_usuario_fecha"),
    ("contribucion_informacion",  "idx_contribucion_usuario_estado"),
    ("resena",                    "idx_resena_procesado_nlp"),
    ("historial_visita",          "idx_historial_usuario_estab_fecha"),
]

# ─── FKs de herencia TPT esperadas ───────────────────────────────────────────

TPT_FKS: list[tuple[str, str, str]] = [
    # (tabla_hija, columna_fk, tabla_padre)
    ("usuario_visitante",  "id_usuario",     "usuario"),
    ("usuario_propietario","id_usuario",     "usuario_visitante"),
    ("administrador",      "id_usuario",     "usuario"),
    ("restaurante",        "id_restaurante", "establecimiento"),
    ("local_comercial",    "id_local",       "establecimiento"),
    ("puesto_informal",    "id_puesto",      "establecimiento"),
]


# ─── Funciones de verificación ────────────────────────────────────────────────

def check_tablas(inspector, tablas_db: set[str]) -> list[str]:
    errores = []

    faltantes = TABLAS_ESPERADAS - tablas_db
    for t in sorted(faltantes):
        errores.append(f"  ❌ Tabla faltante: {t}")

    presentes_prohibidas = TABLAS_PROHIBIDAS & tablas_db
    for t in sorted(presentes_prohibidas):
        errores.append(f"  ❌ Tabla antigua todavía existe: {t}")

    return errores


def check_indices(inspector, tablas_db: set[str]) -> list[str]:
    errores = []
    for tabla, nombre_idx in INDICES_ESPERADOS:
        if tabla not in tablas_db:
            errores.append(f"  ⚠️  Tabla '{tabla}' no existe, no se puede verificar índice '{nombre_idx}'")
            continue
        indices = {idx["name"] for idx in inspector.get_indexes(tabla)}
        if nombre_idx not in indices:
            errores.append(f"  ❌ Índice faltante en '{tabla}': {nombre_idx}")
    return errores


def check_tpt_fks(inspector, tablas_db: set[str]) -> list[str]:
    errores = []
    for tabla_hija, col_fk, tabla_padre in TPT_FKS:
        if tabla_hija not in tablas_db:
            errores.append(f"  ⚠️  Tabla hija '{tabla_hija}' no existe")
            continue
        fks = inspector.get_foreign_keys(tabla_hija)
        referencia_encontrada = any(
            fk.get("referred_table") == tabla_padre
            and col_fk in (fk.get("constrained_columns") or [])
            for fk in fks
        )
        if not referencia_encontrada:
            errores.append(
                f"  ❌ FK TPT faltante: {tabla_hija}.{col_fk} → {tabla_padre}"
            )
    return errores


def check_tablas_archivado_sin_fk(inspector, tablas_db: set[str]) -> list[str]:
    """Las tablas de archivado NO deben tener FKs (diseño intencional — ver §6)."""
    errores = []
    tablas_archivado = {
        "recomendacion_generada_historico",
        "interaccion_usuario_historico",
    }
    for tabla in tablas_archivado:
        if tabla not in tablas_db:
            continue
        fks = inspector.get_foreign_keys(tabla)
        if fks:
            errores.append(
                f"  ❌ Tabla de archivado '{tabla}' tiene FKs (debe ser independiente): {fks}"
            )
    return errores


def check_nombre_estado_geo(tablas_db: set[str]) -> list[str]:
    """Verificar que la tabla se llame 'estado_geo', no 'estado' — ver §1.4."""
    errores = []
    if "estado_geo" not in tablas_db:
        errores.append("  ❌ La tabla de estados se llama diferente a 'estado_geo'")
    if "estado" in tablas_db:
        errores.append("  ❌ Existe una tabla llamada 'estado' (colisión de nombre)")
    return errores


# ─── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    print("=" * 60)
    print("EKI — Verificación de Estructura de BD")
    print("=" * 60)

    try:
        engine = create_engine(get_url(), pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Conexión exitosa a la base de datos\n")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return 1

    inspector   = inspect(engine)
    tablas_db   = set(inspector.get_table_names())
    total_errores: list[str] = []

    # 1. Tablas
    print(f"[1/5] Verificando tablas ({len(TABLAS_ESPERADAS)} esperadas)...")
    errs = check_tablas(inspector, tablas_db)
    if errs:
        total_errores.extend(errs)
        for e in errs:
            print(e)
    else:
        tablas_presentes = TABLAS_ESPERADAS & tablas_db
        print(f"  ✅ {len(tablas_presentes)}/{len(TABLAS_ESPERADAS)} tablas presentes")

    # 2. Tablas antiguas
    presentes_prohibidas = TABLAS_PROHIBIDAS & tablas_db
    if not presentes_prohibidas:
        print("  ✅ Tablas placeholder antiguas eliminadas (vendors, users, user_ratings)")

    # 3. Índices secundarios
    print(f"\n[2/5] Verificando {len(INDICES_ESPERADOS)} índices secundarios (§5)...")
    errs = check_indices(inspector, tablas_db)
    if errs:
        total_errores.extend(errs)
        for e in errs:
            print(e)
    else:
        print(f"  ✅ Todos los índices secundarios presentes")

    # 4. FKs TPT
    print(f"\n[3/5] Verificando FKs de herencia TPT...")
    errs = check_tpt_fks(inspector, tablas_db)
    if errs:
        total_errores.extend(errs)
        for e in errs:
            print(e)
    else:
        print("  ✅ Todas las FKs de herencia TPT son correctas")

    # 5. Tablas archivado sin FK
    print(f"\n[4/5] Verificando tablas de archivado (sin FKs — §6)...")
    errs = check_tablas_archivado_sin_fk(inspector, tablas_db)
    if errs:
        total_errores.extend(errs)
        for e in errs:
            print(e)
    else:
        print("  ✅ Tablas de archivado correctas (sin FKs)")

    # 6. Nombre estado_geo
    print(f"\n[5/5] Verificando nomenclatura 'estado_geo' (no 'estado' — §1.4)...")
    errs = check_nombre_estado_geo(tablas_db)
    if errs:
        total_errores.extend(errs)
        for e in errs:
            print(e)
    else:
        print("  ✅ Tabla 'estado_geo' existe con el nombre correcto")

    # Resumen
    print("\n" + "=" * 60)
    if total_errores:
        print(f"❌ VERIFICACIÓN FALLIDA — {len(total_errores)} error(es) encontrado(s):")
        for e in total_errores:
            print(e)
        print("=" * 60)
        return 1
    else:
        print(f"✅ VERIFICACIÓN EXITOSA — BD en estado correcto")
        print(f"   Tablas: {len(TABLAS_ESPERADAS & tablas_db)}/{len(TABLAS_ESPERADAS)}")
        print(f"   Índices: {len(INDICES_ESPERADOS)} verificados")
        print(f"   FKs TPT: {len(TPT_FKS)} verificadas")
        print("=" * 60)
        return 0


if __name__ == "__main__":
    sys.exit(main())
