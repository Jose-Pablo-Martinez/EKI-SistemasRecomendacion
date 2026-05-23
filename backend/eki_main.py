"""
Punto de entrada de la aplicación FastAPI — EKI (Esquina Jach ki').

Registra los routers de cada módulo y configura CORS para permitir
peticiones desde el frontend en GitHub Pages y entornos locales.

Ejecutar en desarrollo:
    uvicorn eki_main:app --reload --port 8000
"""

import logging
import os

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from fastapi.middleware.cors import CORSMiddleware
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
    "http://localhost:5500,http://127.0.0.1:5500,https://jose-pablo-martinez.github.io",
)
ALLOWED_ORIGINS: list[str] = [origin.strip() for origin in _raw_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)

logger.info("CORS configurado para los orígenes: %s", ALLOWED_ORIGINS)

# ─── Manejadores de Excepciones Globales ──────────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error.get("loc", []))
        msg = error.get("msg", "Error de validación")
        errors.append(f"{field}: {msg}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Error de validación de campos", "errors": errors},
    )

@app.exception_handler(IntegrityError)
async def sqlalchemy_integrity_exception_handler(request: Request, exc: IntegrityError):
    msg = str(exc.orig) if exc.orig else str(exc)
    logger.error("Error de integridad en BD: %s", msg)
    if "usuario_visitante_email_key" in msg or "Duplicate entry" in msg or "unique constraint" in msg.lower():
         return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "El correo electrónico ya está en uso por otro usuario."},
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Error de integridad o restricción única en la base de datos."},
    )

# ─── Routers ──────────────────────────────────────────────────────────────────
# Importar y registrar aquí los routers de cada módulo con APIRouter.
from backend.routers import usuarios, establecimientos, gamificacion, contenido, admin

app.include_router(usuarios.router)
app.include_router(establecimientos.router)
app.include_router(gamificacion.router)
app.include_router(contenido.router)
app.include_router(admin.router)

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
