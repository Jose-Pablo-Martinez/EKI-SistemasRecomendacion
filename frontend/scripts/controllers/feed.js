/**
 * feed.js — Feed de Recomendaciones
 * EkiSystem — Fase 3 + Pulido Fase 5
 *
 * Fase 5 añade:
 *  • Carrusel horizontal con snap en móvil (.eki-carousel), grid en md+
 *  • Error handling de spin-down de Render: auto-retry cada 5 s, máx 6 intentos
 *  • role="list" / role="listitem" en secciones
 *  • aria-label en botones de ícono
 *  • aria-pressed en botón de favorito
 */

// Datos de prueba (Mock data) alineado con generador_recomendaciones.py
const _MOCK_RECS = [
  { id_recomendacion:1,  id_establecimiento:101, nombre_establecimiento:"Los Tacos de la Abuela Chole", categoria_recomendacion:"tendencia_informal",    es_informal:true,  calificacion_promedio:4.8, total_resenas:47,  distancia_km:0.9, tipo_establecimiento:"puesto_informal",  razon_principal:"Joya muy popular en tu zona",         detalle_razon:"Visitado frecuentemente por personas con gustos similares a los tuyos", score_total:0.91, score_contenido_usado:0.88, score_colaborativo_usado:0.94, estrategia_usada:"tendencia_informal" },
  { id_recomendacion:2,  id_establecimiento:102, nombre_establecimiento:"Cochinita Pibil Don Rubén",   categoria_recomendacion:"preferencia_contenido", es_informal:false, calificacion_promedio:4.6, total_resenas:112, distancia_km:2.1, tipo_establecimiento:"local_comercial",   razon_principal:"Perfecto para tus gustos yucatecos", detalle_razon:"Alta similitud con tus preferencias de cocina regional",         score_total:0.87, score_contenido_usado:0.93, score_colaborativo_usado:0.78, estrategia_usada:"content_filter"     },
  { id_recomendacion:3,  id_establecimiento:103, nombre_establecimiento:"Marquesitas El Arco",         categoria_recomendacion:"cercania",              es_informal:true,  calificacion_promedio:4.5, total_resenas:89,  distancia_km:0.4, tipo_establecimiento:"puesto_informal",  razon_principal:"A pasos de ti",               detalle_razon:"Uno de los lugares mejor calificados a menos de 500 m",             score_total:0.82, score_contenido_usado:0.75, score_colaborativo_usado:0.72, estrategia_usada:"cercania"            },
  { id_recomendacion:4,  id_establecimiento:104, nombre_establecimiento:"Panuchos Santa Lucía",        categoria_recomendacion:"tendencia_informal",    es_informal:true,  calificacion_promedio:4.9, total_resenas:31,  distancia_km:1.7, tipo_establecimiento:"puesto_informal",  razon_principal:"La joya más escondida del barrio", detalle_razon:"Muy poco conocido pero altísimamente valorado",                  score_total:0.89, score_contenido_usado:0.85, score_colaborativo_usado:0.82, estrategia_usada:"tendencia_informal" },
  { id_recomendacion:5,  id_establecimiento:105, nombre_establecimiento:"Sopa de Lima Doña Esther",    categoria_recomendacion:"colaborativo_cluster",  es_informal:false, calificacion_promedio:4.7, total_resenas:64,  distancia_km:3.2, tipo_establecimiento:"restaurante",      razon_principal:"Muy popular en tu comunidad",  detalle_razon:"Usuarios con preferencias similares lo visitan seguido",         score_total:0.84, score_contenido_usado:0.80, score_colaborativo_usado:0.91, estrategia_usada:"collab_filter"      },
  { id_recomendacion:6,  id_establecimiento:106, nombre_establecimiento:"Tamales Colados La Lupita",   categoria_recomendacion:"cercania",              es_informal:true,  calificacion_promedio:4.4, total_resenas:22,  distancia_km:0.7, tipo_establecimiento:"puesto_informal",  razon_principal:"En tu misma cuadra",          detalle_razon:"Puesto informal con excelente reputación a menos de 1 km",      score_total:0.79, score_contenido_usado:0.72, score_colaborativo_usado:0.68, estrategia_usada:"cercania"            },
  { id_recomendacion:7,  id_establecimiento:107, nombre_establecimiento:"Café de Altura Mirador",      categoria_recomendacion:"preferencia_contenido", es_informal:false, calificacion_promedio:4.3, total_resenas:56,  distancia_km:1.5, tipo_establecimiento:"local_comercial",   razon_principal:"Coincide con tu amor por el café", detalle_razon:"Alta compatibilidad con tus categorías favoritas",            score_total:0.81, score_contenido_usado:0.90, score_colaborativo_usado:0.70, estrategia_usada:"content_filter"     },
];

// Config de secciones (fallback local para iconos/estilo)
const _SECCIONES = {
  top_picks_hibrido:     { titulo:"Mejores selecciones para ti", icono:"star",          textura:false },
  preferencia_contenido: { titulo:"Basado en tus gustos",        icono:"favorite",      textura:false },
  colaborativo_cluster:  { titulo:"Personas como tu visitaron",  icono:"group",         textura:false },
  popularidad_zona:      { titulo:"Populares cerca de ti",       icono:"trending_up",   textura:false },
  tendencia_informal:    { titulo:"Apoya el comercio local",     icono:"auto_awesome",  textura:false },
  descubrimiento:        { titulo:"Descubrimientos recientes",   icono:"new_releases", textura:false },
  cold_start:            { titulo:"Populares de la semana",      icono:"explore",       textura:false },
  cercania:              { titulo:"Cerca de ti",                 icono:"near_me",       textura:false },
};

let _favoritosSet = new Set();

// Utilidades para el Feed se han movido a scripts/components/

// Sección con carrusel en móvil
function _resolverSeccion(cat, section) {
  const base = _SECCIONES[cat] || { titulo: cat, icono:'restaurant', textura:false };
  if (!section) return base;
  return {
    titulo: section.title || base.titulo,
    icono: section.kind === 'categoria' ? 'category' : base.icono,
    textura: base.textura,
  };
}

function _seccionFeed(cat, items, favoritosSet, section = null) {
  const cfg   = _resolverSeccion(cat, section);
  const cards = items.map((r, i) => {
    const idEstab = r.id_establecimiento || r.establecimiento?.id_establecimiento;
    const isFav = favoritosSet?.has(idEstab);
    return window.Card.renderFeed(r, i * 70, 'window.Favorite.toggle', isFav);
  }).join('');

  const inner = `
    <div class="flex items-center justify-between mb-5">
      <div class="flex items-center gap-2 text-accent">
        <span class="material-symbols-outlined" aria-hidden="true">${cfg.icono}</span>
        <h2 class="font-heading text-headline-lg text-primary">${cfg.titulo}</h2>
      </div>
      <a href="#/buscar"
         class="flex items-center gap-1 text-label-lg text-secondary hover:text-secondary-subtle transition-colors"
         aria-label="Ver todo en ${cfg.titulo}">
        Ver todo
        <span class="material-symbols-outlined" aria-hidden="true" style="font-size:16px;">arrow_forward</span>
      </a>
    </div>
    <div class="eki-carousel-wrap">
      <button class="eki-carousel-btn hidden md:flex" type="button"
              aria-label="Desplazar a la izquierda en ${cfg.titulo}"
              onclick="window._scrollCarousel(this, -1)">
        <span class="material-symbols-outlined" aria-hidden="true">chevron_left</span>
      </button>
      <!-- Carrusel horizontal (movil + escritorio) -->
      <div class="eki-carousel" role="list" aria-label="Recomendaciones: ${cfg.titulo}">
        ${cards}
      </div>
      <button class="eki-carousel-btn hidden md:flex" type="button"
              aria-label="Desplazar a la derecha en ${cfg.titulo}"
              onclick="window._scrollCarousel(this, 1)">
        <span class="material-symbols-outlined" aria-hidden="true">chevron_right</span>
      </button>
    </div>
    `;

  if (cfg.textura) {
    return `
      <section class="mb-14 eki-texture-bg rounded-md relative p-6 md:p-8">
        <div class="relative z-10">${inner}</div>
      </section>`;
  }
  return `<section class="mb-14">${inner}</section>`;
}

// Scroll de carrusel en escritorio
window._scrollCarousel = (btn, dir) => {
  const wrap = btn?.closest('.eki-carousel-wrap');
  const track = wrap?.querySelector('.eki-carousel');
  if (!track) return;
  const delta = Math.round(track.clientWidth * 0.9) * dir;
  track.scrollBy({ left: delta, behavior: 'smooth' });
};

function _updateCarouselArrows() {
  setTimeout(() => {
    document.querySelectorAll('.eki-carousel-wrap').forEach((wrap) => {
      const track = wrap.querySelector('.eki-carousel');
      if (!track) return;
      // Comprobar si realmente hay scroll disponible
      const overflow = track.scrollWidth > track.clientWidth + 4;
      wrap.classList.toggle('no-arrows', !overflow);
    });
  }, 100);
}

if (!window._carouselResizeBound) {
  window.addEventListener('resize', () => {
    if (window.location.hash.startsWith('#/feed')) _updateCarouselArrows();
  });
  window._carouselResizeBound = true;
}

// Acciones globales 
async function _irEstab(idEstab, idRec) {
  if (appState.isAuthenticated) {
    try { await api.registrarClick(idRec); }          catch(_) {}
    try { await api.registrarInteraccion(idEstab, 'vista_detalle'); } catch(_) {}
  }
  window.location.hash = `#/establecimiento/${idEstab}`;
}

// _favFeed eliminado porque ahora usamos window.Favorite.toggle


// Render del feed a partir de datos 
function _renderFeedData(recs, favoritosSet) {
  let grupos = {};
  if (Array.isArray(recs) && recs.length && recs[0]?.items) {
    return recs
      .filter(s => Array.isArray(s.items) && s.items.length)
      .map(s => _seccionFeed(s.key, s.items, favoritosSet, s))
      .join('');
  } else if (Array.isArray(recs)) {
    recs.forEach(r => {
      if (!grupos[r.categoria_recomendacion]) grupos[r.categoria_recomendacion] = [];
      grupos[r.categoria_recomendacion].push(r);
    });
  } else {
    grupos = recs;
  }

  const orden = Object.keys(_SECCIONES);
  const extra  = Object.keys(grupos).filter(k => !_SECCIONES[k]);
  return [...orden, ...extra]
    .filter(k => grupos[k]?.length)
    .map(k => _seccionFeed(k, grupos[k], favoritosSet))
    .join('');
}

// Estado vacío 
function _feedEstadoVacio() {
  return `
    <div class="flex flex-col items-center justify-center py-24 text-center">
      <span class="material-symbols-outlined text-5xl text-text-tertiary mb-4" aria-hidden="true">restaurant</span>
      <h3 class="font-heading text-headline-md text-primary mb-2">Aún no hay recomendaciones</h3>
      <p class="text-body-md text-text-secondary max-w-sm mb-6">
        Completa tu perfil de gustos para que podamos sugerirte los mejores lugares.
      </p>
      <a href="#/onboarding"
         class="bg-accent text-white px-6 py-2.5 rounded font-semibold text-label-lg
                hover:bg-accent-hover active:scale-95 transition-all shadow">
        Ajustar preferencias
      </a>
    </div>`;
}

// Skeletons del shell inicial
function _shellSkel() {
  return `
    <section class="mb-14" aria-hidden="true">
      <div class="flex items-center gap-3 mb-5">
        <div class="skeleton w-6 h-6 rounded"></div>
        <div class="skeleton h-7 w-44 rounded"></div>
      </div>
      <!-- carrusel -->
      <div class="eki-carousel">${window.Skeletons.renderFeed(3)}</div>
    </section>
    <section class="mb-14" aria-hidden="true">
      <div class="flex items-center gap-3 mb-5">
        <div class="skeleton w-6 h-6 rounded"></div>
        <div class="skeleton h-7 w-56 rounded"></div>
      </div>
      <div class="eki-carousel">${window.Skeletons.renderFeed(3)}</div>
    </section>`;
}

// Spin-down de Render: auto-retry
const _RETRY_MAX      = 6;
const _RETRY_INTERVAL = 5000; // 5 s
let   _retryTimer     = null;

function _cancelarRetry() {
  if (_retryTimer) { clearTimeout(_retryTimer); _retryTimer = null; }
}

function _mostrarSpinDown(intento) {
  const el = document.getElementById('feed-content');
  if (!el) return;
  const segsRestantes = Math.round((_RETRY_MAX - intento + 1) * _RETRY_INTERVAL / 1000);
  el.innerHTML = `
    <div class="flex flex-col items-center justify-center py-20 text-center"
         role="status" aria-live="polite" aria-label="Servidor iniciando, reintentando...">
      <span class="material-symbols-outlined text-5xl text-text-tertiary mb-4 animate-spin"
            aria-hidden="true">autorenew</span>
      <h3 class="font-heading text-headline-md text-primary mb-2">El servidor está despertando...</h3>
      <p class="text-body-sm text-text-secondary max-w-xs mb-1">
        El servidor estuvo inactivo y está iniciando. Esto puede tardar hasta ${segsRestantes} segundos.
      </p>
      <p class="text-label-md text-text-tertiary mb-6">
        Intento ${intento} de ${_RETRY_MAX} — reintentando automáticamente
      </p>
      <!-- Barra de progreso del spin-down -->
      <div class="progress-track w-52 mb-6">
        <div class="progress-fill"
             style="width:${Math.round((intento/_RETRY_MAX)*100)}%;animation:none;background-color:rgb(var(--secondary));">
        </div>
      </div>
      <button onclick="_cancelarRetry(); _mostrarErrorConexion()"
              class="text-label-lg text-text-tertiary hover:text-accent transition-colors">
        Cancelar
      </button>
    </div>`;
}

function _mostrarErrorConexion() {
  const el = document.getElementById('feed-content');
  if (!el) return;
  el.innerHTML = `
    <div class="flex flex-col items-center justify-center py-20 text-center">
      <span class="material-symbols-outlined text-5xl text-text-tertiary mb-4" aria-hidden="true">wifi_off</span>
      <h3 class="font-heading text-headline-md text-primary mb-2">No pudimos conectar</h3>
      <p class="text-body-sm text-text-secondary mb-6">Verifica tu conexión e intenta de nuevo.</p>
      <button onclick="window.controllers.feed()"
              class="bg-accent text-white px-5 py-2.5 rounded font-semibold text-label-lg
                     hover:bg-accent-hover active:scale-95 transition-all">
        Reintentar
      </button>
    </div>`;
}

async function _cargarConRetry(intento) {
  if (intento > _RETRY_MAX) {
    _mostrarErrorConexion();
    return;
  }
  try {
    const recs = await api.getRecomendaciones();
    _cancelarRetry();
    const el = document.getElementById('feed-content');
    const hasData = Array.isArray(recs) ? recs.length : (recs && Object.keys(recs).length);
    if (el) {
      el.innerHTML = hasData ? _renderFeedData(recs, _favoritosSet) : _feedEstadoVacio();
      _updateCarouselArrows();
    }
  } catch(err) {
    // Si el error parece ser de red/servidor (no 4xx del negocio), reintentar
    const esRed = !err.status || err.status === 0 || err.status >= 500;
    if (esRed && intento <= _RETRY_MAX) {
      _mostrarSpinDown(intento);
      _retryTimer = setTimeout(() => _cargarConRetry(intento + 1), _RETRY_INTERVAL);
    } else {
      _mostrarErrorConexion();
    }
  }
}

// Main Controller
window.controllers.feed = async () => {
  _cancelarRetry(); // limpiar retry anterior si el usuario re-navega

  // Ubicación en background
  if (!appState.location) {
    solicitarUbicacion()
      .then(({ lat, lon }) => {
        appState.setLocation(lat, lon);
        api.enviarUbicacion(lat, lon).catch(() => {});
      })
      .catch(() => {});
  }

  const nombre = appState.user?.nombre || '';

  const loaded = await renderView('feed.html');
  if (!loaded) return;

  const titleEl = document.getElementById('feed-title');
  if (titleEl) {
    titleEl.textContent = nombre ? `Hola, ${nombre}` : '¡Bienvenido de vuelta!';
  }

  const contentEl = document.getElementById('feed-content');
  if (contentEl) {
    contentEl.innerHTML = _shellSkel();
  }

  // Cargar radio_busqueda_km del perfil actual
  let perfil = null;
  try {
    perfil = await api.getPerfil();
  } catch (_) {}
  
  const sliderEl = document.getElementById('feed-radio');
  const sliderVal = document.getElementById('feed-radio-val');
  if (sliderEl && sliderVal && perfil && perfil.visitante && perfil.visitante.radio_busqueda_km) {
    sliderEl.value = perfil.visitante.radio_busqueda_km;
    sliderVal.innerText = perfil.visitante.radio_busqueda_km + ' km';
  }

  // Escuchar cambios en el slider
  if (sliderEl) {
    sliderEl.onchange = async () => {
      const newRadius = parseInt(sliderEl.value, 10);
      try {
        await api.actualizarPerfil({ radio_busqueda_km: newRadius });
        // Mostrar loading overlay
        const overlay = document.getElementById('feed-loading-overlay');
        if (overlay) {
          overlay.classList.remove('hidden');
        }
        
        // Recargar recomendaciones
        _cancelarRetry();
        await _cargarConRetry(1);
        
        // Ocultar loading overlay
        if (overlay) {
          overlay.classList.add('hidden');
        }
      } catch (err) {
        showToast('Error al actualizar el radio', 'error');
      }
    };
  }

  let favoritos = [];
  try {
    favoritos = await api.getFavoritos();
  } catch (_) {
    favoritos = [];
  }
  _favoritosSet = new Set(
    favoritos
      .map((f) => f.id_establecimiento || f.establecimiento?.id_establecimiento)
      .filter((id) => !!id)
  );

  // Intentar cargar datos reales
  try {
    const recs = await api.getRecomendaciones();
    const el   = document.getElementById('feed-content');
    const hasData = Array.isArray(recs) ? recs.length : (recs && Object.keys(recs).length);
    if (el) {
      el.innerHTML = hasData ? _renderFeedData(recs, _favoritosSet) : _feedEstadoVacio();
      _updateCarouselArrows();
    }
  } catch(err) {
    // Mostrar mock inmediatamente para que no haya pantalla en blanco
    const el = document.getElementById('feed-content');
    if (el) {
      el.innerHTML = _renderFeedData(_MOCK_RECS, _favoritosSet);
      _updateCarouselArrows();
    }

    // Luego iniciar la secuencia de retry silenciosa en background
    // (si el backend responde durante el retry, reemplaza el mock)
    const esRed = !err.status || err.status === 0 || err.status >= 500;
    if (esRed) {
      _retryTimer = setTimeout(() => {
        // Solo mostrar spinner si el usuario sigue en el feed
        if (document.getElementById('feed-content')) {
          _mostrarSpinDown(1);
          _cargarConRetry(1);
        }
      }, 3000);
    }
  }
};
