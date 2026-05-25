/**
 * Badges.js — Componente UI para etiquetas e insignias
 *
 * Contiene funciones para renderizar etiquetas HTML estandarizadas (badges)
 * que indican si un lugar es un "Restaurante", "Local Comercial" o un
 * "Puesto Informal". Se reutilizan en todo el frontend.
 */

window.Badges = {
  /**
   * Genera el badge naranja grande con icono para "Puesto Informal" en el Feed y Detalle.
   * @returns {string} String HTML
   */
  informal: () => {
    return `<span class="inline-flex items-center gap-1 text-label-sm px-2 py-0.5 rounded bg-accent-faint text-accent border border-accent/30">
      <span class="material-symbols-outlined" aria-hidden="true" style="font-size:11px;line-height:1;">storefront</span>
      Puesto informal
    </span>`;
  },
  
  informalCompact: () => {
    return `<span class="text-label-sm px-2 py-0.5 rounded bg-accent-faint text-accent border border-accent/30 flex-shrink-0">Informal</span>`;
  },

  tipo: (tipo) => {
    if (tipo === 'restaurante')     return `<span class="text-label-sm px-2 py-0.5 rounded bg-secondary-faint text-secondary border border-secondary/30">Restaurante</span>`;
    if (tipo === 'local_comercial') return `<span class="text-label-sm px-2 py-0.5 rounded bg-surface-dim text-text-tertiary border border-border-default">Local</span>`;
    return '';
  },

  tipoLabel: (tipo) => {
    return {
      puesto_informal: 'Puesto informal',
      restaurante:     'Restaurante',
      local_comercial: 'Local',
    }[tipo] || '';
  }
};
