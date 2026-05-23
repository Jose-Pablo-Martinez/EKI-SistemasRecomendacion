window.errorHandler = {
    handle(error, context) {
        console.error(`[Error en ${context}]:`, error);
        
        let userMessage = "Ha ocurrido un error inesperado. Por favor, intenta de nuevo.";
        
        if (error.status === 401) {
            userMessage = "Tus credenciales son incorrectas o tu sesión ha expirado.";
        } else if (error.status === 400) {
            userMessage = error.message || "Los datos proporcionados no son válidos.";
            // Mapeo específico para correo en uso si el backend responde con eso
            if (error.message && error.message.toLowerCase().includes("correo") && error.message.toLowerCase().includes("uso")) {
                 userMessage = "El correo electrónico ya está en uso por otro usuario.";
            }
        } else if (error.status === 422) {
            userMessage = "Por favor, verifica que todos los campos estén correctamente llenados.";
        } else if (error.message && error.message.includes('Failed to fetch')) {
            userMessage = "No pudimos conectar con el servidor. Verifica tu conexión a internet.";
        } else if (error.status === 404) {
            userMessage = "El servicio solicitado aún no está disponible o no existe (Error 404).";
        } else if (error.status >= 500) {
            userMessage = "El servidor está experimentando problemas técnicos. Intenta de nuevo más tarde.";
        } else if (error.message && error.message !== "Not Found") {
            userMessage = error.message;
        }

        return userMessage;
    }
};
