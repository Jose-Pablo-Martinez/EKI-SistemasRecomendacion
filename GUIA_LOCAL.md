# 📖 Guía de Configuración Local — EKI

Esta guía explica paso a paso cómo preparar tu entorno de desarrollo para testear el sistema **Esquina Jach ki' (EKI)** en tu máquina local.

---

## 1. Requisitos Previos
*   **Python 3.11 o superior** instalado.
*   **Git** configurado.
*   Acceso a las credenciales de la base de datos (Aiven). *(Opcional para el setup inicial)*, se le puede solicitar al líder del equipo las crecendiales para trabajar con la base de datos de Aiven

---

## 2. Configuración del Entorno (Python)

Abre una terminal en la raíz del proyecto y ejecuta:

### A. Crear el entorno virtual
```powershell
python -m venv venv
```

### B. Activar el entorno
*   **Windows:** `venv\Scripts\Activate.ps1`
*   **macOS/Linux:** `source venv/bin/activate`

> *Nota: Si en Windows recibes un error de permisos, ejecuta primero: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`*

### C. Instalar dependencias
```powershell
pip install -r backend/requirements.txt
```

---

## 3. Configuración de Variables (.env)

El sistema utiliza variables de entorno para no exponer contraseñas.
1.  Localiza el archivo `.env.example` en la raíz.
2.  Crea una copia y cámbiale el nombre a `.env`.
3.  Edita el archivo `.env` con las credenciales de Aiven proporcionadas por el líder de equipo.
    *   *Nota: Si aún no tienes acceso a las credenciales, puedes omitir las variables `DB_*` y el sistema iniciará, aunque algunas funciones de datos no estarán disponibles.*

---

## 4. Certificado SSL de la Base de Datos

Para conectar con Aiven MySQL de forma segura en producción, necesitamos el certificado CA:
*(Nota: Este paso es opcional si solo estás desarrollando la lógica del backend sin conectar a la DB real)*
1.  Descarga el archivo `ca.pem` desde el dashboard de Aiven.
2.  Crea la carpeta `backend/certs/` si no existe.
3.  Guarda el archivo en `backend/certs/ca.pem`.

---

## 5. Ejecutar el Sistema

### Backend (API)
Con el entorno virtual activado, ejecuta:
```powershell
uvicorn backend.eki_main:app --reload --port 8000
```
*   Acceso a la API: `http://localhost:8000`
*   Documentación Interactiva (Swagger): `http://localhost:8000/docs`

### Frontend (UI)
No requiere servidor especial. Simplemente:
1.  Abre `frontend/index.html` en tu navegador.
2.  O usa la extensión **Live Server** de VS Code (recomendado).

---

## 6. Verificación de Funcionamiento
1.  Enciende el backend.
2.  Abre el frontend.
3.  Haz clic en el botón **"Ver Recomendaciones"**. 
4.  Si el servidor responde "healthy" (puedes verificarlo visitando `http://localhost:8000/health`) pero la lista está vacía, ¡felicidades! El sistema está conectado correctamente pero la DB aún no tiene datos.

---

## 7. Verificación de Conexión a la API

Si prefieres usar la terminal para verificar que la API responde, puedes ejecutar:

```powershell
# Verificar estado general
Invoke-RestMethod -Uri "http://localhost:8000/health"

# Verificar respuesta de la raíz
Invoke-RestMethod -Uri "http://localhost:8000/"
```

Si recibes un JSON con `{"status": "healthy"}`, el backend está listo para recibir peticiones.

---
*Equipo EKI — Facultad de Matemáticas, UADY*
