/**
 * Card.js — Componente UI Maestro para Tarjetas de Establecimientos
 *
 * Se encarga de ensamblar las "tarjetas" complejas de los establecimientos
 * incluyendo la foto, metadatos, botones interactivos (como el de favorito),
 * insignias y el desglose de caja blanca (en la versión feed).
 * Unifica el renderizado para evitar HTML duplicado en los controladores.
 */

window.Card = {
  /**
   * Genera la tarjeta "Grande" con desglose de caja blanca, utilizada
   * exclusivamente en la ruta #/feed.
   * @param {Object} rec - Objeto de recomendación proveniente de la API.
   * @param {number} delay - Retraso en ms para la animación de entrada.
   * @param {string} onFavClick - Nombre del callback para cuando se hace click en el favorito.
   * @returns {string} String HTML de la tarjeta completa.
   */
  // Tarjeta grande para el Feed
  renderFeed: (rec, delay = 0, onFavClick) => {
    const score  = Math.round((rec.score_total||0) * 100);
    const dist   = rec.distancia_km ? `${rec.distancia_km.toFixed(1)} km` : null;
    const img    = `https://picsum.photos/seed/${rec.id_establecimiento}/600/360`;
    const c      = Math.round((rec.score_contenido_usado||0) * 100);
    const col    = Math.round((rec.score_colaborativo_usado||0) * 100);
    const calStr = (rec.calificacion_promedio||0).toFixed(1);
    
    // onClick para el fav
    const favClick = onFavClick 
      ? `event.stopPropagation(); ${onFavClick}(${rec.id_establecimiento}, this)` 
      : `event.stopPropagation(); window.Favorite.toggle(${rec.id_establecimiento}, this)`;

    // onClick para la tarjeta completa
    const cardClick = `onclick="window.location.hash='#/establecimiento/${rec.id_establecimiento}'"`;
    // Si viene de feed.js, usamos _irEstab para analytics
    const customCardClick = `onclick="if(typeof _irEstab === 'function') { _irEstab(${rec.id_establecimiento}, ${rec.id_recomendacion}); } else { window.location.hash='#/establecimiento/${rec.id_establecimiento}'; }"`;

    return `
      <article
        role="listitem"
        class="bg-surface-raised border border-border-default rounded-md overflow-hidden
               hover:border-border-strong hover:shadow-md transition-all duration-200
               cursor-pointer group card-enter"
        style="animation-delay:${delay}ms"
        ${customCardClick}>

        <!-- Imagen -->
        <div class="relative overflow-hidden bg-surface-dim" style="aspect-ratio:16/9;">
          <img src="${img}"
               alt=""
               aria-hidden="true"
               class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
               loading="lazy"
               onerror="this.src='https://picsum.photos/600/360?grayscale'" />
          <div class="absolute top-3 right-3 bg-primary/70 backdrop-blur-sm text-white
                      text-label-md px-2 py-0.5 rounded font-bold tabular-nums"
               aria-label="${score}% de compatibilidad">
            ${score}% match
          </div>
          ${rec.es_informal ? `
            <div class="absolute top-3 left-3 bg-accent text-white text-label-sm px-2 py-0.5 rounded flex items-center gap-1">
              <span class="material-symbols-outlined" aria-hidden="true" style="font-size:12px;line-height:1;">storefront</span>
              Informal
            </div>` : ''}
        </div>

        <!-- Cuerpo -->
        <div class="p-4">
          <div class="flex items-start justify-between gap-2 mb-2">
            <h3 class="font-heading text-headline-sm text-primary leading-snug flex-1">
              ${rec.nombre_establecimiento}
            </h3>
            <button
              onclick="${favClick}"
              class="text-text-tertiary hover:text-accent transition-colors flex-shrink-0 mt-0.5
                     w-10 h-10 flex items-center justify-center rounded"
              aria-label="Guardar ${rec.nombre_establecimiento} en favoritos"
              aria-pressed="false">
              <span class="material-symbols-outlined" aria-hidden="true" style="font-size:20px;">favorite</span>
            </button>
          </div>

          <!-- Meta -->
          <div class="flex items-center flex-wrap gap-x-3 gap-y-1 mb-3">
            <div class="flex items-center gap-1 text-sm"
                 aria-label="${calStr} de 5 estrellas, ${rec.total_resenas||0} reseñas">
              ${window.Stars.render(rec.calificacion_promedio)}
              <span class="text-numeric-sm text-text-secondary ml-1">${calStr}</span>
              <span class="text-label-md text-text-tertiary">(${rec.total_resenas||0})</span>
            </div>
            ${dist ? `
              <span class="flex items-center gap-1 text-body-sm text-text-tertiary">
                <span class="material-symbols-outlined" aria-hidden="true" style="font-size:14px;line-height:1;">near_me</span>
                ${dist}
              </span>` : ''}
            ${rec.es_informal ? window.Badges.informal() : window.Badges.tipo(rec.tipo_establecimiento)}
          </div>

          <!-- Caja blanca -->
          <div class="bg-secondary-faint border border-secondary/20 rounded p-3">
            <div class="flex items-start gap-2">
              <span class="material-symbols-outlined text-secondary flex-shrink-0"
                    aria-hidden="true"
                    style="font-size:15px;margin-top:2px;">shield</span>
              <div class="min-w-0">
                <p class="text-body-sm font-semibold text-secondary leading-snug">${rec.razon_principal}</p>
                <p class="text-label-md text-text-tertiary mt-0.5 leading-relaxed">${rec.detalle_razon}</p>
                <div class="flex gap-4 mt-2">
                  <span class="text-label-md text-text-tertiary">
                    Contenido <strong class="text-secondary tabular-nums">${c}%</strong>
                  </span>
                  <span class="text-label-md text-text-tertiary">
                    Comunidad <strong class="text-secondary tabular-nums">${col}%</strong>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </article>`;
  },

  // Tarjeta pequeña para Búsqueda y Favoritos
  renderCompact: (e, idx = 0, isFavCard = false, extraHtml = '') => {
    // Si viene de favoritos, a veces trae 'e.establecimiento', lo normalizamos:
    const data = e.establecimiento || e;
    const id = data.id_establecimiento || e.id_establecimiento;
    const cal = data.calificacion_promedio || 0;
    const dist = data.distancia_km ? `${data.distancia_km.toFixed(1)} km` : null;
    const img = `https://picsum.photos/seed/${id}/${isFavCard ? '128/128' : '120/120'}`;
    const tipoLabel = window.Badges.tipoLabel(data.tipo_establecimiento);
    
    const extraContent = extraHtml ? extraHtml : 
      (cal > 0 || dist) ? `
        <div class="flex items-center gap-3 mt-1">
          ${cal > 0 ? `
            <div class="flex items-center gap-1 text-sm">
              ${window.Stars.render(cal)}
              <span class="text-numeric-sm text-text-secondary tabular-nums ml-1">${cal.toFixed(1)}</span>
            </div>` : ''}
          ${dist ? `<span class="text-body-sm text-text-tertiary flex items-center gap-1">
            <span class="material-symbols-outlined" style="font-size:13px;line-height:1;">near_me</span>${dist}</span>` : ''}
        </div>` : '';

    return `
      <article role="listitem" id="${isFavCard ? `fav-${id}` : `search-${id}`}"
        class="bg-surface-raised border border-border-default rounded-md p-4 flex gap-4
               hover:border-border-strong ${isFavCard ? '' : 'hover:shadow-sm'} transition-all duration-150 cursor-pointer group card-enter"
        style="animation-delay:${idx*50}ms"
        onclick="window.location.hash='#/establecimiento/${id}'">

        <div class="w-16 h-16 rounded bg-surface-dim flex-shrink-0 overflow-hidden" aria-label="Ver ${data.nombre || data.nombre_establecimiento || ''}">
          <img src="${img}" alt="${data.nombre || data.nombre_establecimiento || ''}"
            class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy" onerror="this.src='https://picsum.photos/${isFavCard ? '128/128' : '120/120'}?grayscale'" />
        </div>

        <div class="flex-1 min-w-0">
          <div class="flex items-start justify-between gap-2">
            <h3 class="font-heading text-headline-sm text-primary truncate">${data.nombre || data.nombre_establecimiento}</h3>
            ${data.es_informal ? window.Badges.informalCompact() : ''}
          </div>
          <p class="text-body-sm text-text-secondary mt-0.5">${tipoLabel}</p>
          ${extraContent}
        </div>
      </article>`;
  }
};
