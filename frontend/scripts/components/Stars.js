/**
 * Stars.js — Componente UI para calificación de estrellas
 *
 * Contiene la lógica visual para generar un bloque de 5 estrellas HTML
 * basándose en un rating promedio. Utilizado en Feed, Búsqueda y Detalles.
 */

export const Stars = {
  /**
   * Genera el HTML de 5 estrellas llenas o vacías según el rating.
   * @param {number} rating - El promedio de calificación (ej. 4.5)
   * @returns {string} String con el HTML de las estrellas.
   */
  render: (rating) => {
    const r = Math.round(rating || 0);
    return [1, 2, 3, 4, 5]
      .map(i => `<span aria-hidden="true" style="color:${i <= r ? 'rgb(var(--warning-subtle))' : 'rgb(var(--border-default))'};">★</span>`)
      .join('');
  }
};
