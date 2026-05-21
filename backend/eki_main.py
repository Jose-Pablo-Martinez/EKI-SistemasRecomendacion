"""
Punto de entrada de la aplicación FastAPI — EKI (Esquina Jach ki').

Registra los routers de cada módulo y configura CORS para permitir
peticiones desde el frontend en GitHub Pages y entornos locales.

Ejecutar en desarrollo:
    uvicorn eki_main:app --reload --port 8000
"""

import logging
import os

# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

# ─── Configuración de Logging ─────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Instancia de la Aplicación ───────────────────────────────────────────────
app = FastAPI(
    title="EKI — Esquina Jach ki'",
    description=(
        "API REST del sistema de recomendación gastronómica de Mérida, Yucatán. "
        "Motor híbrido: clustering K-Means + filtrado por contenido (similitud coseno) "
        "+ filtrado colaborativo item-to-item por cluster + boosting Haversine. "
        "Prioriza la visibilidad de puestos informales y joyas ocultas de la ciudad."
    ),
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
# Orígenes permitidos: GitHub Pages (producción) + Live Server (desarrollo local)
_raw_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5500,http://127.0.0.1:5500",
)
ALLOWED_ORIGINS: list[str] = [origin.strip() for origin in _raw_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

logger.info("CORS configurado para los orígenes: %s", ALLOWED_ORIGINS)

# ─── Routers ──────────────────────────────────────────────────────────────────
# Importar y registrar aquí los routers de cada módulo con APIRouter.
# Ejemplo (descomentar cuando se creen los módulos de rutas):
# from backend.routers import usuarios, establecimientos, recomendaciones, contenido
# app.include_router(usuarios.router)
# app.include_router(establecimientos.router)
# app.include_router(recomendaciones.router)
# app.include_router(contenido.router)


# ─── Endpoints de Utilidad ────────────────────────────────────────────────────

@app.get("/", tags=["Utilidad"])
def root() -> dict:
    """
    Endpoint raíz. Confirma que la API está activa.
    Útil para el health check de Render (evita el spin-down innecesario).
    """
    return {"status": "ok", "app": "EKI — Esquina Jach ki'", "version": "0.2.0"}


@app.get("/health", tags=["Utilidad"])
def health_check() -> dict:
    """
    Health check explícito para monitoreo externo.
    Render puede configurarse para llamar este endpoint y mantener el servicio activo.
    """
    return {"status": "healthy"}
