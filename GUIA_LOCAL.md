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

## 3. Configuración del Entorno (.env y secretos)

El sistema utiliza variables de entorno y certificados protegidos para la seguridad.
1.  Ejecuta el script de configuración inicial:
```powershell
python setup_env.py
```
*Este script creará la carpeta `/secrets` y generará un archivo `.env` basado en la plantilla.*

2.  Edita el archivo `.env` recién creado:
    *   **Para Producción (Aiven):** Llena los datos y coloca el archivo `ca.pem` dentro de la carpeta `/secrets`.
    *   **Para Desarrollo Local:** Configura los datos de tu MariaDB y deja `DB_SSL_CA` vacío.

> [!IMPORTANT]
> La carpeta `/secrets` y el archivo `.env` están en el `.gitignore`. **Nunca** intentes forzar su subida al repositorio.

---

## 4. Inicialización de la Base de Datos

Antes de correr el servidor por primera vez, debes crear las tablas:
1.  Asegúrate de tener tu `.env` configurado.
2.  Con el entorno virtual activo, ejecuta:
```powershell
python backend/init_db.py
```
Si ves el mensaje "✅ Tablas creadas con éxito", tu base de datos está lista.

---

## 5. Ejecutar el Sistema

### Backend (API)
Ejecuta el servidor con el siguiente comando:
```powershell
python -m uvicorn backend.eki_main:app --reload --port 8000
```
*   Acceso a la API: `http://localhost:8000`
*   Documentación Interactiva: `http://localhost:8000/docs`

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
