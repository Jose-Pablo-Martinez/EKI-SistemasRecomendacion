/**
 * favoritos.js — Lista de establecimientos guardados
 * EkiSystem — Fase 4 Frontend
 */

// Skeleton 
function _skelFavs(n) {
  return Array.from({length:n||4}, () => `
    <div class="bg-surface-raised border border-border-default rounded-md p-4 flex gap-4">
      <div class="skeleton w-16 h-16 rounded flex-shrink-0"></div>
      <div class="flex-1 space-y-2 py-1">
        <div class="skeleton h-4 rounded w-3/4"></div>
        <div class="skeleton h-3 rounded w-1/3"></div>
        <div class="skeleton h-3 rounded w-1/2"></div>
      </div>
    </div>`).join('');
}

// Tarjeta de favorito 
function _cardFav(fav, idx) {
  // La respuesta puede venir como { establecimiento: {...}, fecha_guardado: ... }
  // o directamente como el objeto del establecimiento
  const e   = fav.establecimiento || fav;
  const id  = e.id_establecimiento || fav.id_establecimiento;
  const cal = e.calificacion_promedio || 0;
  const img = `https://picsum.photos/seed/${id}/128/128`;

  const tipoLabel = {
    puesto_informal: 'Puesto informal',
    restaurante:     'Restaurante',
    local_comercial: 'Local',
  }[e.tipo_establecimiento] || '';

  const fechaGuardada = fav.fecha_guardado
    ? new Date(fav.fecha_guardado).toLocaleDateString('es-MX', { day:'numeric', month:'short', year:'numeric' })
    : null;

  const starsHtml = [1,2,3,4,5]
    .map(i => `<span style="color:${i<=Math.round(cal)?'#C08A40':'#DCD4C8'};">★</span>`)
    .join('');

  return `
    <div id="fav-${id}"
         class="bg-surface-raised border border-border-default rounded-md p-4 flex gap-4
                hover:border-border-strong transition-all duration-150 group card-enter"
         style="animation-delay:${idx*50}ms">

      <!-- Miniatura -->
      <div class="w-16 h-16 rounded bg-surface-dim flex-shrink-0 overflow-hidden cursor-pointer"
           onclick="window.location.hash='#/establecimiento/${id}'"
           aria-label="Ver ${e.nombre}">
        <img src="${img}" alt="${e.nombre || ''}"
          class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          loading="lazy"
          onerror="this.src='https://picsum.photos/128/128?grayscale'" />
      </div>

      <!-- Info -->
      <div class="flex-1 min-w-0 cursor-pointer"
           onclick="window.location.hash='#/establecimiento/${id}'">
        <div class="flex items-start gap-2 mb-0.5">
          <h3 class="font-heading text-headline-sm text-primary truncate flex-1">${e.nombre || 'Establecimiento'}</h3>
          ${e.es_informal
            ? `<span class="text-label-sm px-1.5 py-0.5 rounded bg-accent-faint text-accent border border-accent/30 flex-shrink-0 whitespace-nowrap">Informal</span>`
            : ''}
        </div>
        <p class="text-body-sm text-text-secondary">${tipoLabel}</p>
        <div class="flex items-center flex-wrap gap-x-3 gap-y-0.5 mt-1">
          ${cal > 0 ? `
            <div class="flex items-center gap-1 text-sm">
              ${starsHtml}
              <span class="text-numeric-sm text-text-secondary tabular-nums ml-1">${cal.toFixed(1)}</span>
              ${e.total_resenas ? `<span class="text-label-md text-text-tertiary">(${e.total_resenas})</span>` : ''}
            </div>` : ''}
          ${fechaGuardada
            ? `<span class="text-label-md text-text-tertiary flex items-center gap-1">
                 <span class="material-symbols-outlined" style="font-size:12px;line-height:1;">bookmark</span>
                 ${fechaGuardada}
               </span>`
            : ''}
        </div>
      </div>

      <!-- Quitar -->
      <button
        onclick="_quitarFav(${id})"
        aria-label="Quitar ${e.nombre || 'este lugar'} de favoritos"
        title="Quitar de favoritos"
        class="flex-shrink-0 text-text-tertiary hover:text-accent transition-colors self-start mt-0.5">
        <span class="material-symbols-outlined" style="font-size:20px;">heart_minus</span>
      </button>
    </div>`;
}

// Quitar favorito 
async function _quitarFav(id) {
  const card = document.getElementById(`fav-${id}`);
  // Deshabilitar botón inmediatamente
  const btn = card?.querySelector('button[onclick]');
  if (btn) btn.disabled = true;

  try {
    await api.toggleFavorito(id, 'DELETE');

    if (card) {
      card.style.transition = 'opacity 220ms ease, transform 220ms ease';
      card.style.opacity    = '0';
      card.style.transform  = 'translateX(12px)';
      setTimeout(() => {
        card.remove();
        _actualizarBadge(-1);
        // Mostrar vacío si no quedan tarjetas
        const lista = document.getElementById('favs-lista');
        if (lista && !lista.querySelector('[id^="fav-"]')) {
          lista.innerHTML = _estadoVacio();
        }
      }, 240);
    }

    showToast('Eliminado de favoritos', 'info');
  } catch(_) {
    if (btn) btn.disabled = false;
    showToast('No se pudo eliminar el favorito', 'error');
  }
}

function _actualizarBadge(delta) {
  const badge = document.getElementById('favs-badge');
  if (!badge) return;
  const n = (parseInt(badge.textContent) || 0) + delta;
  badge.textContent = n > 0 ? n : '';
}

// Estado vacío
function _estadoVacio() {
  return `
    <div class="flex flex-col items-center justify-center py-20 text-center">
      <span class="material-symbols-outlined text-5xl text-text-tertiary mb-4">heart_broken</span>
      <h3 class="font-heading text-headline-md text-primary mb-2">Sin favoritos aún</h3>
      <p class="text-body-md text-text-secondary max-w-xs mb-6">
        Guarda los lugares que más te gusten y aparecerán aquí.
      </p>
      <a href="#/feed"
         class="bg-accent text-white px-6 py-2.5 rounded font-semibold text-label-lg
                hover:bg-accent-hover active:scale-95 transition-all shadow">
        Explorar recomendaciones
      </a>
    </div>`;
}

// Controller
window.controllers.favoritos = async () => {
  renderPage(`
    <div class="w-full max-w-3xl mx-auto px-4 md:px-8 py-10">
      <div class="flex items-center gap-3 mb-8">
        <h1 class="font-heading text-display-md text-primary">Mis favoritos</h1>
        <span id="favs-badge" class="text-headline-md text-text-tertiary tabular-nums"></span>
      </div>
      <div id="favs-lista" class="space-y-3">${_skelFavs(4)}</div>
    </div>
  `);

  try {
    let favoritos = [];
    try {
      favoritos = await apiRequest('/usuarios/me/favoritos');
    } catch(_) {
      favoritos = [];
    }

    const lista  = document.getElementById('favs-lista');
    const badge  = document.getElementById('favs-badge');
    if (!lista) return;

    if (!favoritos || !favoritos.length) {
      lista.innerHTML = _estadoVacio();
      return;
    }

    if (badge) badge.textContent = favoritos.length;
    lista.innerHTML = favoritos.map((f, i) => _cardFav(f, i)).join('');

  } catch(e) {
    const lista = document.getElementById('favs-lista');
    if (lista) lista.innerHTML = `
      <div class="flex flex-col items-center justify-center py-16 text-center">
        <span class="material-symbols-outlined text-4xl text-text-tertiary mb-3">wifi_off</span>
        <p class="text-body-sm text-text-secondary mb-4">No se pudieron cargar tus favoritos.</p>
        <button onclick="window.controllers.favoritos()"
          class="bg-accent text-white px-4 py-2 rounded font-semibold hover:bg-accent-hover transition-colors">
          Reintentar
        </button>
      </div>`;
  }
};
