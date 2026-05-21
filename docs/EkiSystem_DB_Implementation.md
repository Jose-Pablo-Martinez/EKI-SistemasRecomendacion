# EkiSystem — Implementación de Base de Datos

> **Documento de referencia rápida.** Para el análisis completo de decisiones de diseño, justificaciones técnicas y alternativas evaluadas, consulta [EkiSystem_DB_Design.md](./EkiSystem_DB_Design.md).

---

## ¿Qué se implementó?

Se reemplazó el esquema placeholder de 3 tablas (`vendors`, `users`, `user_ratings`) por el **esquema relacional definitivo de EkiSystem**: **38 tablas** organizadas en 6 dominios, diseñadas para soportar el motor de recomendación híbrido.

**Migración Alembic aplicada:** `e1b0a75cd65e` — *Estructura inicial completa EkiSystem*

---

## Dominios y tablas

### Geografía (4 tablas)
Jerarquía `pais → estado_geo → municipio → colonia` para geolocalizar establecimientos con precisión de colonia/barrio en Mérida.

> **Decisión:** La tabla se llama `estado_geo` (no `estado`) para evitar colisión de nombre con el ENUM `estado` presente en múltiples tablas.

### Catálogos base (3 tablas)
`rango_informador`, `cluster_usuario`, `cluster_establecimiento` — catálogos que alimentan el motor de recomendación y la gamificación. Los centroides de clustering se almacenan como `JSON` en la misma tabla.

### Usuarios — Herencia TPT (6 tablas)
```
usuario (base)
  ├── usuario_visitante  → usuario_propietario
  └── administrador
sesion_usuario, dispositivo_usuario, ubicacion_usuario
```
> **Decisión:** Table-Per-Type (TPT) puro sin `polymorphic_on` de SQLAlchemy, para mantener el esquema portable y legible en SQL directo. Ver §1.1 del diseño.

### Establecimientos — Herencia TPT (6 tablas)
```
establecimiento (base)
  ├── restaurante
  ├── local_comercial
  └── puesto_informal
propietario_establecimiento
```
> **Decisión:** `local_comercial` en lugar de `local` (keyword reservada en MySQL). El campo `es_informal` en la tabla base permite filtrar puestos informales sin JOIN, a costo de redundancia controlada. Ver §1.1.

### Contenido vinculado (8 tablas)
`categoria` (auto-referencial para subcategorías), `etiqueta`, `establecimiento_categoria`, `establecimiento_etiqueta`, `platillo`, `imagen`, `horario`.

### Motor de recomendación (3 tablas)
| Tabla | Propósito |
|---|---|
| `metrica_establecimiento` | Scores pre-calculados offline: contenido, colaborativo, boost combinado |
| `interaccion_usuario` | Señales de comportamiento con `peso_interaccion` desnormalizado |
| `recomendacion_generada` | Resultados del motor con campos de caja blanca para explicabilidad |

> **Decisión clave (§1.7 Offline-First):** Los scores del motor se pre-calculan en un job offline y se persisten en `metrica_establecimiento`. FastAPI solo calcula la distancia Haversine puntual en cada request.

### Gamificación e Interacciones (7 tablas)
`resena`, `favorito_guardado`, `historial_visita`, `preferencia_usuario`, `contribucion_informacion`, `log_puntos`, `reporte`.

### Archivado (2 tablas)
`recomendacion_generada_historico`, `interaccion_usuario_historico` — réplicas sin FKs para retención de datos históricos sin afectar rendimiento del esquema activo.

> **Decisión:** Sin foreign keys intencionalmente. El archivado debe ser independiente del esquema vivo para que no bloquee operaciones de mantenimiento (DROP/ALTER). Ver §6 del diseño.

---

## Decisiones transversales

| Tema | Decisión |
|---|---|
| **Validación de calificaciones** | `CHECK(calificacion >= 1 AND calificacion <= 5)` en `resena` + `Field(ge=1, le=5)` en Pydantic. Doble capa porque MySQL <8.0 ignora los CHECK. |
| **Vectores del motor** | Almacenados como `JSON` (`vector_preferencias`, `vector_caracteristicas`, `centroide`). Flexible para cambiar dimensión sin migración. |
| **Peso de interacciones** | Desnormalizado en `interaccion_usuario.peso_interaccion` al insertar, para evitar recalcular en cada ejecución del motor. |
| **Índices secundarios** | 13 índices en tablas de alta frecuencia de lectura (interacciones, recomendaciones, reseñas, historial). |
| **Unicidad de reseñas** | `UNIQUE(id_usuario, id_establecimiento)` — un usuario solo puede dejar una reseña por establecimiento. |

---

## Archivos clave modificados

| Archivo | Cambio |
|---|---|
| `backend/models.py` | Reescrito completo — 38 modelos SQLAlchemy definitivos |
| `backend/schemas.py` | Reescrito completo — ~30 schemas Pydantic v2 organizados por dominio |
| `backend/migrations/env.py` | `import backend.models` (módulo completo, no clases individuales) |
| `backend/migrations/versions/e1b0a75cd65e_...py` | Migración autogenerada y aplicada — 553 líneas |
| `backend/requirements.txt` | + `email-validator==2.2.0` (requerido por `EmailStr`) |
| `scripts/db/verify_schema.py` | Script de verificación post-migración |
| `.github/workflows/database-migrations.yml` | + pasos de validación de imports y verificación de esquema |

---

## Verificación de la migración

El script `scripts/db/verify_schema.py` confirma el estado correcto de la BD tras cada migración:

```
✅ VERIFICACIÓN EXITOSA — BD en estado correcto
   Tablas: 38/38
   Índices secundarios: 13 verificados
   FKs TPT: 6 verificadas
   Tablas de archivado sin FKs: OK
   Nomenclatura 'estado_geo': OK
```

---

## Próximos pasos

1. **Seed inicial** — Insertar datos base: país `MX`, 5 rangos de informador, ~20 categorías gastronómicas yucatecas.
2. **Migración a producción** — Se ejecuta automáticamente vía GitHub Actions (`ekiEnvironment`) al hacer merge a `main`.
3. **Endpoints REST** — Implementar los routers en `backend/routers/` usando los schemas de `schemas.py`.

---

*Para el razonamiento detrás de cada decisión, alternativas evaluadas y justificaciones detalladas, consulta [EkiSystem_DB_Design.md](./EkiSystem_DB_Design.md).*
