/**
 * Archivo modificado: 2026-06-02
 * Función: Contiene funciones de validación para correos, 
 * nombres y filtros básicos de texto en el frontend.
 */
export const validators = {
    isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    },
    isValidName(name) {
        if (!name || name.trim().length === 0) return false;
        // Filtro básico de profanidad para el front (el backend hará la validación estricta)
        const profanityList = ["puta", "puto", "mierda", "pendejo", "idiota", "sexo", "verga", "pito", "panocha", "perra"];
        const lowerName = name.toLowerCase();
        for (const word of profanityList) {
            if (lowerName.includes(word)) return false;
        }
        // Solo letras y espacios
        return /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/.test(name);
    }
};
