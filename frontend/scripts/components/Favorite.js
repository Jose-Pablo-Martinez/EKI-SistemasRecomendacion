/**
 * Favorite.js — Componente Lógico para Gestión de Favoritos
 *
 * Contiene la lógica centralizada para interactuar con el endpoint de favoritos
 * (POST/DELETE). Maneja la micro-interacción visual (actualización optimista del botón)
 * y el manejo de errores (reversión de estado), mostrando notificaciones Toast.
 */

window.Favorite = {
  /**
   * Alterna el estado de guardado/no-guardado de un establecimiento.
   * Modifica el DOM del botón instantáneamente para mejorar la UX y realiza la llamada a la API en segundo plano.
   * @param {number|string} idEstab - ID numérico del establecimiento.
   * @param {HTMLElement} btnElement - El elemento <button> que disparó el evento.
   */
  toggle: async (idEstab, btnElement) => {
    if (!window.appState.isAuthenticated) {
      window.location.hash = '#/login';
      return;
    }

    const isFav = btnElement.getAttribute('aria-pressed') === 'true';
    const method = isFav ? 'DELETE' : 'POST';
    
    // Actualización optimista
    btnElement.setAttribute('aria-pressed', String(!isFav));
    btnElement.setAttribute('aria-label', !isFav ? 'Quitar de favoritos' : 'Guardar en favoritos');
    
    const span = btnElement.querySelector('span');
    if (span) {
      span.style.fontVariationSettings = !isFav ? '"FILL" 1' : '"FILL" 0';
      span.classList.toggle('text-accent', !isFav);
    }
    
    // Text label
    const label = btnElement.querySelector('._fav-label');
    if (label) {
      label.textContent = isFav ? 'Guardar' : 'Guardado';
    }
    
    // Micro-interacción
    btnElement.classList.add('scale-110');
    setTimeout(() => btnElement.classList.remove('scale-110'), 150);
    
    // Toast
    window.Toast.show(isFav ? 'Eliminado de favoritos' : 'Guardado en favoritos', isFav ? 'info' : 'success');
    
    try {
      await window.api.toggleFavorito(idEstab, method);
    } catch (e) {
      // Revertir en caso de error
      btnElement.setAttribute('aria-pressed', String(isFav));
      btnElement.setAttribute('aria-label', isFav ? 'Quitar de favoritos' : 'Guardar en favoritos');
      if (span) {
        span.style.fontVariationSettings = isFav ? '"FILL" 1' : '"FILL" 0';
        span.classList.toggle('text-accent', isFav);
      }
      if (label) {
        label.textContent = isFav ? 'Guardado' : 'Guardar';
      }
      window.Toast.show('Error al actualizar favoritos', 'error');
    }
  }
};
