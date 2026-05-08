# CONTRIBUTING — Esquina Jach ki' (EKI)
> Guía de desarrollo y estándares del proyecto.  
> **Leer este archivo antes de escribir o modificar cualquier archivo del proyecto.**

---

## 1. Identidad del Proyecto

| Campo | Valor |
|---|---|
| Nombre | Esquina Jach ki' (EKI) |
| Dominio | Sistema de recomendación gastronómica — Mérida, Yucatán |
| Arquitectura | Monorepositorio · Backend API REST · Frontend Vanilla JS |
| Etapa actual | Setup inicial completado |
| Despliegue | GitHub Pages (frontend) · Render (backend) · Aiven MySQL (base de datos) |
| Institución | Facultad de Matemáticas, UADY |

El sistema prioriza la visibilidad de puestos pequeños, carritos y vendedores informales mediante un **modelo híbrido de recomendación** que combina filtrado por contenido, filtrado colaborativo y algoritmos de ranking/boosting.

---

## 2. Estructura de Carpetas (Canónica)

No crear archivos fuera de esta estructura sin que el equipo lo acuerde previamente.

```
ekiSystem/
│
├── CONTRIBUTING.md             ← Este archivo (actualizar solo con consenso del equipo)
│
├── scripts/
│   ├── setup/                  ← Inicialización del entorno local
│   └── db/                     ← Scripts operativos de base de datos
│
├── backend/
│   ├── migrations/             ← Historial de cambios de BD (Alembic)
│   ├── eki_main.py             ← Punto de entrada FastAPI + registro de routers
│   ├── models.py               ← Modelos SQLAlchemy (tablas de MariaDB)
│   ├── schemas.py              ← Esquemas Pydantic
│   ├── database.py             ← Configuración de engine y sesión SQLAlchemy
│   ├── requirements.txt        ← Dependencias
│   └── logic/                  ← Algoritmos de recomendación
│
└── frontend/
    ├── index.html              ← Estructura HTML
    ├── js/app.js               ← Lógica de peticiones HTTP
    └── css/styles.css          ← Ajustes de diseño
```

### 2.1 Gestión de Cambios en la BD
Si modificas `models.py`, **debes** generar una migración:
1.  Activa tu venv.
2.  Ejecuta: `alembic revision --autogenerate -m "Breve descripción del cambio"`
3.  Revisa el archivo generado en `backend/migrations/versions/`.
4.  Aplica el cambio localmente con `python scripts/db/migrate.py`.

---

## 3. Convenciones de Nombrado

### 3.1 Python (PEP 8 — estricto)

| Tipo | Convención | Ejemplo |
|---|---|---|
| Clase | `PascalCase` | `VendorModel`, `RecommendationEngine` |
| Variable | `snake_case` | `vendor_score`, `user_history` |
| Función / Método | `snake_case` | `get_recommendations()`, `apply_boost()` |
| Constante | `UPPER_SNAKE_CASE` | `MAX_RESULTS`, `BOOST_FACTOR` |
| Módulo / Archivo | `snake_case` | `cold_start.py`, `collab_filter.py` |

### 3.2 JavaScript (Frontend)

| Tipo | Convención | Ejemplo |
|---|---|---|
| Variable / Función | `camelCase` | `fetchRecommendations()`, `vendorList` |
| Constante de módulo | `UPPER_SNAKE_CASE` | `API_BASE_URL` |
| Clase | `PascalCase` | `RecommendationCard` |
| Archivo | `kebab-case` | `app.js`, `styles.css` |

### 3.3 Base de Datos (MariaDB)

| Tipo | Convención | Ejemplo |
|---|---|---|
| Tabla | `snake_case` plural | `vendors`, `user_ratings` |
| Columna | `snake_case` | `vendor_id`, `created_at` |
| Clave foránea | `<tabla_singular>_id` | `vendor_id`, `user_id` |
| Índice | `idx_<tabla>_<columna>` | `idx_vendors_category` |

---

## 4. Idioma en el Código

```
Código (variables, funciones, clases, rutas)  →  Inglés
Comentarios y docstrings                       →  Español
Mensajes de error al usuario final             →  Español
Commits de Git                                 →  Español
```

**Ejemplo correcto:**

```python
def get_top_vendors(limit: int = 10) -> list:
    """
    Obtiene los vendedores con mayor puntuación de relevancia.
    Se aplica boosting a negocios con menos de 50 reseñas.
    """
    boosted_vendors = apply_boost(vendor_list, threshold=50)
    return boosted_vendors[:limit]
```

---

## 5. Stack Tecnológico

### Backend

| Tecnología | Rol | Lineamiento |
|---|---|---|
| Python 3.11+ | Lenguaje principal | Usar type hints en todas las funciones |
| FastAPI | Framework API REST | Usar `APIRouter` por módulo; no acumular rutas en `eki_main.py` |
| Uvicorn | Servidor ASGI | Solo para desarrollo local; no configurar para producción en el código |
| SQLAlchemy 2.x | ORM | Usar sintaxis declarativa con `DeclarativeBase` |
| PyMySQL | Driver DB | Configurar en `database.py`; nunca escribir credenciales en el código |
| Pydantic v2 | Validación | Mantener schemas separados de models en `schemas.py` |

### Base de Datos

| Tecnología | Rol | Lineamiento |
|---|---|---|
| MariaDB | Base de datos relacional | Garantizar integridad ACID; definir FK con `ondelete` explícito |

### Frontend

| Tecnología | Rol | Lineamiento |
|---|---|---|
| Vanilla JS (ES6+) | Lógica de UI | No incorporar frameworks externos (sin React, sin Vue) |
| Fetch API | Peticiones HTTP | Manejar siempre errores con `try/catch` y verificar `response.ok` |
| Tailwind CSS (CDN) | Estilos | Cargado desde CDN en `index.html`; no instalar como paquete npm |

---

## 6. Estándares de Escritura de Código

### 6.1 Reglas Globales

- **Nunca escribir** credenciales, IPs ni puertos directamente en el código. Usar variables de entorno o un archivo `.env` (incluido en `.gitignore`).
- **Siempre** incluir docstring en toda función o clase pública.
- **Siempre** usar type hints en Python.
- **Nunca** usar `print()` para debugging en código que se integre a `unstable` o `main`; usar el módulo `logging`.
- **Siempre** validar el input antes de procesarlo (Pydantic en backend, validación básica en frontend).
- **Nunca** colocar lógica de negocio dentro de las rutas. Las rutas en `eki_main.py` solo orquestan llamadas; toda la lógica va en `logic/`.

### 6.2 Plantilla: Ruta FastAPI

```python
# backend/eki_main.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import RecommendationResponse
from logic.ranking import get_top_vendors

router = APIRouter(prefix="/recommendations", tags=["Recomendaciones"])

@router.get("/", response_model=list[RecommendationResponse])
def list_recommendations(limit: int = 10, db: Session = Depends(get_db)):
    """
    Devuelve las recomendaciones principales con boosting aplicado.
    """
    try:
        return get_top_vendors(db=db, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 6.3 Plantilla: Modelo SQLAlchemy

```python
# backend/models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Vendor(Base):
    """Representa un puesto o vendedor informal en el sistema."""
    __tablename__ = "vendors"

    vendor_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    category = Column(String(60), nullable=False)
    rating_avg = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    ratings = relationship("UserRating", back_populates="vendor")
```

### 6.4 Plantilla: Fetch API (Frontend)

```javascript
// frontend/js/app.js
const API_BASE_URL = "http://localhost:8000";

/**
 * Obtiene las recomendaciones principales del servidor.
 * @param {number} limit - Cantidad máxima de resultados.
 * @returns {Promise<Array>} Lista de vendedores recomendados.
 */
async function fetchRecommendations(limit = 10) {
    try {
        const response = await fetch(`${API_BASE_URL}/recommendations/?limit=${limit}`);
        if (!response.ok) {
            throw new Error(`Error del servidor: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("No se pudieron obtener las recomendaciones:", error);
        return [];
    }
}
```

---

## 7. Flujo de Trabajo Git

No hacer commits directamente a `main` ni a `unstable`. Todo cambio entra por una rama `feature/`.

```
main               ← Solo código estable aprobado por el equipo
  └── unstable     ← Integración Frontend ↔ Backend
        └── feature/<nombre>-<tarea>   ← Desarrollo individual
```

**Formato de nombre de rama:**
```
feature/alejandro-api-coldstart
feature/rodrigo-collab-filter
feature/jose-frontend-cards
```

**Formato de commit (en español, modo imperativo):**
```
[módulo] descripción corta

Ejemplos:
[backend] Agregar endpoint de recomendaciones con boosting
[frontend] Implementar componente de tarjeta de vendedor
[db] Crear migración inicial de tabla vendors
[fix] Corregir cálculo de score en ranking.py
```

---

## 8. Arquitectura del Modelo de Recomendación

Estos son los cuatro módulos centrales del sistema. Cualquier lógica nueva de recomendación debe ubicarse en el módulo correspondiente.

| Módulo | Archivo | Responsabilidad |
|---|---|---|
| Filtrado por Contenido | `logic/content_filter.py` | Analizar características del puesto (categoría, ubicación, tags) y el perfil del usuario |
| Filtrado Colaborativo | `logic/collab_filter.py` | Calcular similitud entre usuarios o ítems basada en interacciones pasadas |
| Ranking y Boosting | `logic/ranking.py` | Aplicar factores de visibilidad a negocios con pocas reseñas (`review_count < BOOST_THRESHOLD`) |
| Inicio en Frío | `logic/cold_start.py` | Estrategia para usuarios o vendedores nuevos sin historial de interacciones |

**Regla de boosting:** Un vendedor recibe boost si `review_count < 50`. El factor se controla con la constante `BOOST_FACTOR` en `logic/ranking.py`.

---

## 9. Prácticas Prohibidas

- ❌ Agregar dependencias no listadas en el stack sin acuerdo del equipo.
- ❌ Crear archivos fuera de la estructura canónica (Sección 2).
- ❌ Mezclar español e inglés en el mismo identificador (ej. `get_nombre_vendedor`).
- ❌ Usar `SELECT *` en consultas SQLAlchemy; siempre especificar las columnas necesarias.
- ❌ Escribir lógica de recomendación directamente en las rutas de FastAPI.
- ❌ Usar `var` en JavaScript; solo `const` y `let`.
- ❌ Escribir la URL del backend en más de un lugar; centralizar en `API_BASE_URL`.
- ❌ Subir al repositorio credenciales, tokens ni archivos `.env`.

---

## 10. Checklist antes de hacer un Pull Request

Verificar cada punto antes de abrir un PR hacia `unstable` o `main`:

- [ ] ¿Los nombres siguen las convenciones de la Sección 3?
- [ ] ¿El código está en inglés y los comentarios en español?
- [ ] ¿Las funciones tienen docstring y type hints?
- [ ] ¿No hay credenciales ni valores hardcodeados?
- [ ] ¿La lógica de negocio está en `logic/` y no en las rutas?
- [ ] ¿Los errores se manejan con `try/catch` o `HTTPException`?
- [ ] ¿El archivo está en la carpeta correcta según la Sección 2?

---

## 11. Despliegue

La arquitectura de despliegue está dividida en tres capas, todas **gratuitas y con HTTPS automático**:

```
Navegador
    │
    ├─ HTTPS ──→ GitHub Pages (frontend/)
    │              Archivos estáticos: HTML, JS, CSS
    │              URL: https://<tu-usuario>.github.io/EKI-SistemasRecomendacion/
    │
    └─ HTTPS ──→ Render (backend/)
                   FastAPI + Uvicorn
                   URL: https://eki-backend.onrender.com
                       │
                       └─ TCP/SSL ──→ Aiven MySQL
                                        Base de datos remota
                                        Motor: MySQL (compatible con MariaDB)
```

### 11.1 Frontend — GitHub Pages

| Campo | Valor |
|---|---|
| Servicio | GitHub Pages |
| Carpeta publicada | `frontend/` |
| Trigger de despliegue | Push a rama `main` (automático via GitHub Actions) |
| Workflow | `.github/workflows/deploy-frontend.yml` |
| URL | `https://<tu-usuario>.github.io/EKI-SistemasRecomendacion/` |

**Para activar:** Ir a Settings del repositorio → Pages → Source: **GitHub Actions**.

### 11.2 Backend — Render

| Campo | Valor |
|---|---|
| Servicio | Render (free tier) |
| Runtime | Python 3.11+ |
| Build command | `pip install -r backend/requirements.txt` |
| Start command | `uvicorn backend.eki_main:app --host 0.0.0.0 --port $PORT` |
| Health check | `GET /health` |
| Configuración | `render.yaml` (raíz del repositorio) |

> **Limitación conocida:** El servicio se "duerme" tras 15 minutos de inactividad. El primer request después de inactividad tiene un cold start de ~30-50 segundos. Esto es aceptable para el contexto académico del proyecto.

**Variables de entorno sensibles** (configurar manualmente en Render Dashboard → Settings → Environment):
- `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` — credenciales de Aiven
- Certificado SSL de Aiven → subir como **Secret File** con ruta `/etc/secrets/ca.pem`

### 11.3 Base de Datos — Aiven MySQL

| Campo | Valor |
|---|---|
| Servicio | Aiven (free tier permanente) |
| Motor | MySQL (compatible con PyMySQL + SQLAlchemy) |
| Storage | 5 GB |
| Acceso | Remoto con SSL/TLS obligatorio |
| Driver en el código | `PyMySQL` (sin cambios respecto al stack original) |

**Conexión desde código:**
```python
# En database.py — connection string con SSL
"mysql+pymysql://user:password@hostname:port/defaultdb?ssl_ca=ca.pem"
```

### 11.4 CORS

El backend tiene CORS configurado mediante la variable de entorno `CORS_ORIGINS`.

| Entorno | Valor de CORS_ORIGINS |
|---|---|
| Desarrollo local | `http://localhost:5500,http://127.0.0.1:5500` |
| Producción | `https://<tu-usuario>.github.io` |

### 11.5 Flujo de Despliegue

```
git push origin main
    │
    └──→ GitHub Actions detecta el push
            │
            ├──→ Job: Deploy Frontend
            │       Publica frontend/ en GitHub Pages automáticamente
            │
            └──→ Render detecta el push (webhook automático)
                    Rebuilda y redespliega el backend automáticamente
```

---

*Mantenido por el equipo EKI — Facultad de Matemáticas, UADY*  
*Actualizar este archivo cuando cambie el stack, la estructura o las convenciones del proyecto.*