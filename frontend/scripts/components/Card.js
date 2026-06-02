/**
 * Card.js — Componente UI Maestro para Tarjetas de Establecimientos
 *
 * Se encarga de ensamblar las "tarjetas" complejas de los establecimientos
 * incluyendo la foto, metadatos, botones interactivos (como el de favorito),
 * insignias y el desglose de caja blanca (en la versión feed).
 * Unifica el renderizado para evitar HTML duplicado en los controladores.
 */
import { escapeHTML } from '../utils.js';
import { Stars } from './Stars.js';
import { Badges } from './Badges.js';

export const Card = {
  // Render para feed principal (con desglose de IA)
  renderFeed: (rec, delay = 0, customAction = null, isFavorite = false) => {
    const estab = rec.establecimiento || rec;
    const rawNombre = estab.nombre || rec.nombre_establecimiento || 'Desconocido';
    const nombre = escapeHTML(rawNombre);
    const es_informal = estab.es_informal;
    const tipo = estab.tipo_establecimiento || 'restaurante';
    const cal_prom = parseFloat(estab.calificacion_promedio) || 0;
    const resenas = estab.total_resenas || 0;

    const score  = Math.min(100, Math.max(0, Math.round((rec.score_total||0) * 100)));
    const distVal = parseFloat(rec.distancia_km);
    const dist   = !isNaN(distVal) ? `${distVal.toFixed(1)} km` : null;
    const img    = `https://picsum.photos/seed/${rec.id_establecimiento}/600/360`;
    const c      = Math.min(100, Math.max(0, Math.round((rec.score_contenido_usado||0) * 100)));
    const col    = Math.min(100, Math.max(0, Math.round((rec.score_colaborativo_usado||0) * 100)));
    const calStr = cal_prom.toFixed(1);
    const hasBreakdown = (c > 0 || col > 0);
    
    const isColdStart = rec.categoria_recomendacion === 'cold_start' || rec.razon_principal === 'cold_start';
    
    const isFav = !!isFavorite;

    const favClass = isFav
      ? 'border-accent bg-accent-faint text-accent'
      : 'border-border-default text-text-secondary';
    const favPressed = isFav ? 'true' : 'false';
    const favLabel = isFav
      ? `Quitar ${nombre} de favoritos`
      : `Guardar ${nombre} en favoritos`;
    const favIconStyle = isFav
      ? 'font-size:20px;font-variation-settings:"FILL" 1'
      : 'font-size:20px;font-variation-settings:"FILL" 0';

    const razonRaw = ({
      'preferencia_categoria': 'Perfecto para tus gustos',
      'historial_similar': 'Visitado frecuentemente',
      'popular_zona': 'Populares de la zona',
      'colaborativo': 'Muy popular en tu comunidad',
      'cluster_similar': 'Recomendado para tu perfil',
      'cercano': 'A pasos de ti',
      'cold_start': 'Sugerencia inicial',
      'descubrimiento': 'Algo nuevo para ti',
      'tendencia_informal': 'Joya informal'
    })[rec.razon_principal] || rec.razon_principal || 'Sugerencia Inicial';

    const detalleRaw = rec.detalle_razon || 'Seleccionado para empezar';

    const razon = escapeHTML(razonRaw);
    const detalle = escapeHTML(detalleRaw);

    const actionAttr = customAction ? `data-action="${customAction}"` : `data-action="toggle-fav"`;

    return `
      <article
        role="listitem"
        class="bg-surface-raised border border-border-default rounded-md overflow-hidden
               hover:border-border-strong hover:shadow-md transition-all duration-200
               cursor-pointer group card-enter"
        style="animation-delay:${delay}ms"
        data-action="go-to-estab-feed"
        data-id="${rec.id_establecimiento}"
        data-rec-id="${rec.id_recomendacion}">

        <!-- Imagen -->
        <div class="relative overflow-hidden bg-surface-dim" style="aspect-ratio:16/9;">
          <img src="${img}"
               alt=""
               aria-hidden="true"
               class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
               loading="lazy"
               onerror="this.src='https://picsum.photos/600/360?grayscale'" />
          ${(isColdStart || score === 0) ? '' : `
          <div class="absolute top-3 right-3 bg-secondary/90 backdrop-blur-sm text-white
                      text-label-md px-2 py-0.5 rounded font-bold tabular-nums shadow-sm"
               aria-label="${score}% de compatibilidad">
            ${score}% match
          </div>
          `}
          ${es_informal ? `
            <div class="absolute top-3 left-3 bg-accent text-white text-label-sm px-2 py-0.5 rounded flex items-center gap-1">
              <span class="material-symbols-outlined" aria-hidden="true" style="font-size:12px;line-height:1;">storefront</span>
              Informal
            </div>` : ''}
        </div>

        <!-- Cuerpo -->
        <div class="p-4">
          <div class="flex items-start justify-between gap-2 mb-2">
            <h3 class="font-heading text-headline-sm text-primary leading-snug flex-1">
              ${nombre}
            </h3>
            <button
              ${actionAttr}
              data-id="${rec.id_establecimiento}"
              class="hover:text-accent transition-colors flex-shrink-0 mt-0.5
                     w-10 h-10 flex items-center justify-center rounded border ${favClass}"
              aria-label="${favLabel}"
              aria-pressed="${favPressed}">
              <span class="material-symbols-outlined pointer-events-none" aria-hidden="true" style="${favIconStyle}">favorite</span>
            </button>
          </div>

          <!-- Meta -->
          <div class="flex items-center flex-wrap gap-x-3 gap-y-1 mb-3">
            <div class="flex items-center gap-1 text-sm"
                 aria-label="${calStr} de 5 estrellas, ${resenas} reseñas">
              ${Stars.render(cal_prom)}
              <span class="text-numeric-sm text-text-secondary ml-1">${calStr}</span>
              <span class="text-label-md text-text-tertiary">(${resenas})</span>
            </div>
            ${dist ? `
              <span class="flex items-center gap-1 text-body-sm text-text-tertiary">
                <span class="material-symbols-outlined pointer-events-none" aria-hidden="true" style="font-size:14px;line-height:1;">near_me</span>
                ${dist}
              </span>` : ''}
            ${es_informal ? Badges.informal() : Badges.tipo(tipo)}
          </div>

          <!-- Caja blanca -->
          <div class="bg-secondary-faint border border-secondary/20 rounded p-3">
            <div class="flex items-start gap-2">
              <span class="material-symbols-outlined pointer-events-none text-secondary flex-shrink-0"
                    aria-hidden="true"
                    style="font-size:15px;margin-top:2px;">shield</span>
              <div class="min-w-0 pointer-events-none">
                <p class="text-body-sm font-semibold text-secondary leading-snug">
                  ${razon}
                </p>
                <p class="text-label-md text-text-tertiary mt-0.5 leading-relaxed">${detalle}</p>
                ${(isColdStart || !hasBreakdown) ? '' : `
                <div class="flex gap-4 mt-2">
                  <span class="text-label-md text-text-tertiary">
                    <strong class="text-secondary font-semibold">${c}%</strong> Tu gusto
                  </span>
                  <span class="text-label-md text-text-tertiary">
                    <strong class="text-secondary font-semibold">${col}%</strong> Tu tribu
                  </span>
                </div>
                `}
              </div>
            </div>
          </div>
        </div>
      </article>`;
  },

  // Render compacto para favoritos y búsqueda
  renderCompact: (e, idx = 0, isFavCard = false, extraHtml = '') => {
    const data = e.establecimiento || e;
    const id = data.id_establecimiento || e.id_establecimiento;
    const rawNombre = data.nombre || data.nombre_establecimiento || '';
    const nombre = escapeHTML(rawNombre);
    const cal = parseFloat(data.calificacion_promedio) || 0;
    const distVal = parseFloat(data.distancia_km);
    const dist = !isNaN(distVal) ? `${distVal.toFixed(1)} km` : null;
    const img = `https://picsum.photos/seed/${id}/${isFavCard ? '128/128' : '120/120'}`;
    const tipoLabel = escapeHTML(Badges.tipoLabel(data.tipo_establecimiento));
    
    const extraContent = extraHtml ? extraHtml : 
      (cal > 0 || dist) ? `
        <div class="flex items-center gap-3 mt-1 pointer-events-none">
          ${cal > 0 ? `
            <div class="flex items-center gap-1 text-sm">
              ${Stars.render(cal)}
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
        data-action="go-to-estab"
        data-id="${id}">

        <div class="w-16 h-16 rounded bg-surface-dim flex-shrink-0 overflow-hidden pointer-events-none" aria-label="Ver ${nombre}">
          <img src="${img}" alt="${nombre}"
            class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy" onerror="this.src='https://picsum.photos/${isFavCard ? '128/128' : '120/120'}?grayscale'" />
        </div>

        <div class="flex-1 min-w-0 pointer-events-none">
          <div class="flex items-start justify-between gap-2">
            <h3 class="font-heading text-headline-sm text-primary truncate">${nombre}</h3>
            ${data.es_informal ? Badges.informalCompact() : ''}
          </div>
          <p class="text-body-sm text-text-secondary mt-0.5">${tipoLabel}</p>
          ${extraContent}
        </div>
      </article>`;
  }
};
