
const _FILTROS = [
  { valor:'',               label:'Todos',      icono:'apps'       },
  { valor:'puesto_informal',label:'Informales', icono:'storefront' },
  { valor:'restaurante',    label:'Restaurantes',icono:'restaurant' },
  { valor:'local_comercial',label:'Locales',    icono:'shop'       },
];

let _filtroActivo = '';
let _searchTimeout = null;
let _ultimaBusqueda = '';

// Helpers 
function _starsB(rating) {
  return [1,2,3,4,5].map(i =>
    `<span style="color:${i<=Math.round(rating||0)?'var(--warning-subtle)':'var(--border-default)'};">★</span>`
  ).join('');
}

function _skeletonsBusq(n) {
  return Array.from({length:n||4}, () => `
    <div class="bg-surface-raised border border-border-default rounded-md p-4 flex gap-4">
      <div class="skeleton w-16 h-16 rounded flex-shrink-0"></div>
      <div class="flex-1 space-y-2">
        <div class="skeleton h-4 rounded w-3/4"></div>
        <div class="skeleton h-3 rounded w-1/3"></div>
        <div class="skeleton h-3 rounded w-1/2"></div>
      </div>
    </div>`).join('');
}

// Tarjeta compacta de resultado
function _tarjetaBusq(e, idx) {
  const cal  = e.calificacion_promedio || 0;
  const dist = e.distancia_km ? `${e.distancia_km.toFixed(1)} km` : null;
  const img  = `https://picsum.photos/seed/${e.id_establecimiento}/120/120`;
  const tipoLabel = { puesto_informal:'Puesto informal', restaurante:'Restaurante', local_comercial:'Local' }[e.tipo_establecimiento] || '';

  return `
    <article role="listitem"
      class="bg-surface-raised border border-border-default rounded-md p-4 flex gap-4
             hover:border-border-strong hover:shadow-sm transition-all duration-150 cursor-pointer group card-enter"
      style="animation-delay:${idx*50}ms"
      onclick="window.location.hash='#/establecimiento/${e.id_establecimiento}'">

      <div class="w-16 h-16 rounded bg-surface-dim flex-shrink-0 overflow-hidden">
        <img src="${img}" alt="${e.nombre}"
          class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          loading="lazy" onerror="this.src='https://picsum.photos/120/120?grayscale'" />
      </div>

      <div class="flex-1 min-w-0">
        <div class="flex items-start justify-between gap-2">
          <h3 class="font-heading text-headline-sm text-primary truncate">${e.nombre}</h3>
          ${e.es_informal ? `<span class="text-label-sm px-2 py-0.5 rounded bg-accent-faint text-accent border border-accent/30 flex-shrink-0">Informal</span>` : ''}
        </div>
        <p class="text-body-sm text-text-secondary mt-0.5">${tipoLabel}</p>
        <div class="flex items-center gap-3 mt-1">
          ${cal > 0 ? `
            <div class="flex items-center gap-1 text-sm">
              ${_starsB(cal)}
              <span class="text-numeric-sm text-text-secondary tabular-nums ml-1">${cal.toFixed(1)}</span>
            </div>` : ''}
          ${dist ? `<span class="text-body-sm text-text-tertiary flex items-center gap-1">
            <span class="material-symbols-outlined" style="font-size:13px;line-height:1;">near_me</span>${dist}</span>` : ''}
        </div>
      </div>
    </article>`;
}

// Renderizar resultados
function _renderResultadosHTML(items, query) {
  if (!items || !items.length) {
    return `
      <div class="flex flex-col items-center justify-center py-16 text-center col-span-full fade-in">
        <span class="material-symbols-outlined text-4xl text-text-tertiary mb-3">search_off</span>
        <p class="font-heading text-headline-sm text-primary mb-1">Sin resultados para "${query}"</p>
        <p class="text-body-sm text-text-secondary">Prueba con otro término o cambia los filtros.</p>
      </div>`;
  }
  return items.map((e, i) => _tarjetaBusq(e, i)).join('');
}

// Ejecutar búsqueda
async function _ejecutarBusqueda(query) {
  const el = document.getElementById('busq-resultados');
  if (!el) return;

  if (!query || query.length < 2) {
    el.innerHTML = `
      <div class="flex flex-col items-center justify-center py-16 text-center col-span-full">
        <span class="material-symbols-outlined text-5xl text-text-tertiary mb-4">restaurant_menu</span>
        <p class="font-heading text-headline-md text-primary mb-2">¿Qué se te antoja hoy?</p>
        <p class="text-body-md text-text-secondary">Escribe al menos 2 letras para buscar.</p>
      </div>`;
    return;
  }

  _ultimaBusqueda = query;
  el.innerHTML = `<div class="grid grid-cols-1 md:grid-cols-2 gap-3 col-span-full" role="list">${_skeletonsBusq(4)}</div>`;

  try {
    const params = { tipo: _filtroActivo };
    const response = await api.buscar(query, params);
    if (_ultimaBusqueda !== query) return; // busqueda obsoleta
    
    const items = response.resultados || [];
    const sugerencia = response.sugerencia_correccion;
    
    let html = '';
    
    // Renderizado del banner de Corrección Ortográfica (Levenshtein)
    if (sugerencia) {
      html += `
        <div class="col-span-full bg-accent-faint border border-accent/30 text-accent rounded-md p-4 mb-2 flex items-center gap-3 fade-in cursor-pointer hover:bg-accent/10 transition-colors shadow-sm" 
             onclick="document.getElementById('busq-input').value='${sugerencia}'; _clearTimeout=_searchTimeout; _ultimaBusqueda='${sugerencia}'; _ejecutarBusqueda('${sugerencia}')">
          <span class="material-symbols-outlined" style="font-size:24px;">spellcheck</span>
          <p class="font-medium text-body-md">No encontramos "${query}". ¿Quizás quisiste decir <strong class="underline">${sugerencia}</strong>?</p>
        </div>
      `;
    }
    
    html += _renderResultadosHTML(items, query);
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `
      <div class="flex flex-col items-center justify-center py-12 text-center col-span-full">
        <span class="material-symbols-outlined text-4xl text-text-tertiary mb-3">wifi_off</span>
        <p class="text-body-sm text-text-secondary mb-4">No se pudo conectar al servidor.</p>
        <button onclick="_ejecutarBusqueda('${query}')"
          class="bg-accent text-white px-4 py-2 rounded font-semibold text-label-lg hover:bg-accent-hover transition-colors">
          Reintentar
        </button>
      </div>`;
  }
}

// Main Controller
window.controllers.busqueda = async () => {

  const loaded = await renderView('busqueda.html');
  if (!loaded) return;

  const chipsContainer = document.getElementById('chips-container');
  if (chipsContainer) {
    chipsContainer.innerHTML = _FILTROS.map(f => `
      <button
        data-tipo="${f.valor}"
        onclick="_setFiltro('${f.valor}')"
        class="chip-filtro flex items-center gap-1.5 px-4 py-2 rounded-full border text-label-lg transition-all
              ${_filtroActivo === f.valor
                ? 'bg-primary text-white border-primary'
                : 'bg-surface-raised border-border-default text-text-secondary hover:border-border-strong hover:text-primary'}">
        <span class="material-symbols-outlined" style="font-size:15px;line-height:1;">${f.icono}</span>
        ${f.label}
      </button>`).join('');
  }

  const input = document.getElementById('busq-input');
  const clearBtn = document.getElementById('busq-clear');
  if (!input) return;

  // Restaurar valor previo si lo había
  if (_ultimaBusqueda) {
    input.value = _ultimaBusqueda;
    clearBtn?.classList.remove('hidden');
    _ejecutarBusqueda(_ultimaBusqueda);
  }

  input.addEventListener('input', e => {
    const q = e.target.value.trim();
    clearBtn?.classList.toggle('hidden', !q);
    clearTimeout(_searchTimeout);
    _searchTimeout = setTimeout(() => _ejecutarBusqueda(q), 300);
  });

  input.addEventListener('keydown', e => {
    if (e.key === 'Escape') _clearBusqueda();
  });

  input.focus();
};

// Cambiar filtro 
function _setFiltro(valor) {
  _filtroActivo = valor;

  // Actualizar chips visualmente
  document.querySelectorAll('.chip-filtro').forEach(btn => {
    const activo = btn.dataset.tipo === valor;
    btn.className = btn.className
      .replace(/bg-primary text-white border-primary|bg-surface-raised border-border-default text-text-secondary hover:border-border-strong hover:text-primary/g, '')
      .trim();
    if (activo) {
      btn.classList.add('bg-primary','text-white','border-primary');
    } else {
      btn.classList.add('bg-surface-raised','border-border-default','text-text-secondary','hover:border-border-strong','hover:text-primary');
    }
  });

  // Relanzar búsqueda con el nuevo filtro
  const q = document.getElementById('busq-input')?.value?.trim() || '';
  _ejecutarBusqueda(q);
}

// Limpiar búsqueda
function _clearBusqueda() {
  const input = document.getElementById('busq-input');
  const clearBtn = document.getElementById('busq-clear');
  if (input) { input.value = ''; input.focus(); }
  clearBtn?.classList.add('hidden');
  _ultimaBusqueda = '';
  _ejecutarBusqueda('');
}
