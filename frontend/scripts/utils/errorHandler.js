/**
 * errorHandler.js — Componente para Gestión Centralizada de Errores
 *
 * Captura errores de red, respuestas HTTP no exitosas y excepciones internas,
 * emitiendo un log altamente técnico a la consola para debugging y
 * retornando un string amigable, claro y no ambiguo para el usuario final.
 */
window.errorHandler = {
    handle(error, context = 'Aplicación') {
        // 1. Log técnico para Debugging (Sin exponer el stack trace crudo como texto por seguridad)
        const errorStatus = error.status ? `(HTTP ${error.status})` : '(Sin status HTTP)';
        const apiDetail = error.message || error.detail || 'Sin detalles adicionales';
        
        console.group(`[ERROR] ${context}`);
        console.error(`Status: ${errorStatus}`);
        console.error(`Mensaje API: ${apiDetail}`);
        // Se omite el stack trace explícito. El objeto crudo a continuación permite
        // a los desarrolladores inspeccionarlo en la consola localmente sin quemarlo en texto.
        console.error('Objeto Error:', error);
        console.groupEnd();
        
        // 2. Traducción amigable y no ambigua para el Usuario Final
        
        // Errores de Conexión o Red (Fetch falló completamente)
        if (error.message && error.message.includes('Failed to fetch')) {
            return "Parece que no tienes conexión a internet o nuestros servidores están en mantenimiento. Por favor, verifica tu red.";
        }

        // Errores HTTP
        switch (error.status) {
            case 400: // Bad Request
                return apiDetail && apiDetail !== "Error del servidor" 
                    ? apiDetail 
                    : "Los datos ingresados tienen un error. Por favor, revísalos e intenta de nuevo.";
            case 401: // Unauthorized
                return "Tu sesión ha expirado o tus credenciales son incorrectas. Por favor, inicia sesión de nuevo.";
            case 403: // Forbidden
                return "No tienes los permisos necesarios para realizar esta acción.";
            case 404: // Not Found
                return "No pudimos encontrar lo que buscabas. Es posible que haya sido eliminado o movido.";
            case 409: // Conflict
                return apiDetail && apiDetail !== "Error del servidor"
                    ? apiDetail
                    : "Hubo un conflicto con los datos (ej: el registro ya existe).";
            case 422: // Unprocessable Entity (Típico en FastAPI por fallas de validación)
                return "Faltan datos obligatorios o su formato es incorrecto. Verifica el formulario.";
            case 429: // Too Many Requests
                return "Has realizado demasiadas solicitudes en poco tiempo. Por favor, espera unos minutos.";
        }

        // Errores 500+ (Server Errors)
        if (error.status >= 500) {
            return "Nuestros servidores están experimentando un problema técnico. Ya lo estamos revisando, intenta más tarde.";
        }

        // Fallback genérico para errores no catalogados
        if (error.message && error.message !== "Error del servidor" && error.message !== "Not Found") {
            return error.message; 
        }

        return "Ha ocurrido un error inesperado. Por favor, intenta de nuevo o recarga la página.";
    }
};
