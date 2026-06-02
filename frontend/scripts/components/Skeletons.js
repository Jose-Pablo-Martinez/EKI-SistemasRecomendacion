/**
 * Skeletons.js — Componente UI para animaciones de carga (Skeleton Screens)
 *
 * Provee funciones estáticas que devuelven HTML para las "tarjetas fantasma"
 * que se muestran mientras los datos son cargados desde la API. Esto mejora
 * la percepción de velocidad (UX) evitando pantallas vacías.
 */

export const Skeletons = {
  /**
   * Genera los skeletons grandes tipo "Feed" con imagen superior 16:9.
   * @param {number} n - Cantidad de skeletons a generar.
   * @returns {string} String HTML
   */
  renderFeed: (n = 3) => {
    return Array.from({length: n}, () => `
      <div class="bg-surface-raised border border-border-default rounded-md overflow-hidden" aria-hidden="true">
        <div class="skeleton w-full" style="aspect-ratio:16/9;"></div>
        <div class="p-4 space-y-3">
          <div class="skeleton h-5 rounded w-3/4"></div>
          <div class="skeleton h-4 rounded w-1/3"></div>
          <div class="skeleton h-14 rounded w-full"></div>
        </div>
      </div>`).join('');
  },

  renderCompact: (n = 4) => {
    return Array.from({length: n}, () => `
      <div class="bg-surface-raised border border-border-default rounded-md p-4 flex gap-4">
        <div class="skeleton w-16 h-16 rounded flex-shrink-0"></div>
        <div class="flex-1 space-y-2 py-1">
          <div class="skeleton h-4 rounded w-3/4"></div>
          <div class="skeleton h-3 rounded w-1/3"></div>
          <div class="skeleton h-3 rounded w-1/2"></div>
        </div>
      </div>`).join('');
  }
};
