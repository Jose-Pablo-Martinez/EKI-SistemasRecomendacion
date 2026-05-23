window.errorHandler = {
    handle(error, context) {
        console.error(`[Error en ${context}]:`, error);
        
        let userMessage = "Ha ocurrido un error inesperado. Por favor, intenta de nuevo.";
        
        if (error.message && error.message !== "Error del servidor" && error.message !== "Not Found" && !error.message.includes('Failed to fetch')) {
            userMessage = error.message; // El backend nos mandó un mensaje detallado, lo usamos.
        } else if (error.status === 401) {
            userMessage = "No tienes autorización o tu sesión ha expirado.";
        } else if (error.status === 400) {
            userMessage = "Los datos proporcionados no son válidos.";
        } else if (error.status === 422) {
            userMessage = "Por favor, verifica que todos los campos estén correctamente llenados.";
        } else if (error.message && error.message.includes('Failed to fetch')) {
            userMessage = "No pudimos conectar con el servidor. Verifica tu conexión a internet.";
        } else if (error.status === 404) {
            userMessage = "El servicio solicitado aún no está disponible o no existe (Error 404).";
        } else if (error.status >= 500) {
            userMessage = "El servidor está experimentando problemas técnicos. Intenta de nuevo más tarde.";
        }

        return userMessage;
    }
};
