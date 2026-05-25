
// Datos de prueba (Mock data) alineado con generador_recomendaciones.py
const _MOCK_RECS = [
  { id_recomendacion:1, id_establecimiento:101, nombre_establecimiento:"Los Tacos de la Abuela Chole", categoria_recomendacion:"top_picks_hibrido", es_informal:true,  calificacion_promedio:4.9, total_resenas:147,  distancia_km:0.9, tipo_establecimiento:"puesto_informal", razon_principal:"El match perfecto para ti", detalle_razon:"Mezcla tus gustos, tu tribu y distancia cercana", score_total:0.98, score_contenido_usado:0.95, score_colaborativo_usado:0.94, score_boost_aplicado:0.99, estrategia_usada:"hibrido" },
  { id_recomendacion:2, id_establecimiento:102, nombre_establecimiento:"Cochinita Pibil Don Rubén",   categoria_recomendacion:"preferencia_contenido",  es_informal:false, calificacion_promedio:4.6, total_resenas:112, distancia_km:2.1, tipo_establecimiento:"local_comercial",  razon_principal:"Perfecto para tus gustos yucatecos", detalle_razon:"Alta similitud con tus preferencias de cocina regional",          score_total:0.87, score_contenido_usado:0.93, score_colaborativo_usado:0.78, score_boost_aplicado:0.80, estrategia_usada:"content_filter" },
  { id_recomendacion:3, id_establecimiento:103, nombre_establecimiento:"Marquesitas El Arco",         categoria_recomendacion:"popularidad_zona",       es_informal:true,  calificacion_promedio:4.5, total_resenas:89,  distancia_km:0.4, tipo_establecimiento:"puesto_informal", razon_principal:"A pasos de ti",               detalle_razon:"Uno de los lugares más populares a menos de 500 m",              score_total:0.82, score_contenido_usado:0.75, score_colaborativo_usado:0.72, score_boost_aplicado:0.99, estrategia_usada:"popularidad" },
  { id_recomendacion:4, id_establecimiento:104, nombre_establecimiento:"Panuchos Santa Lucía",        categoria_recomendacion:"tendencia_informal",     es_informal:true,  calificacion_promedio:4.9, total_resenas:31,  distancia_km:1.7, tipo_establecimiento:"puesto_informal", razon_principal:"La joya más escondida del barrio", detalle_razon:"Muy poco conocido pero altísimamente valorado por quienes lo visitan", score_total:0.89, score_contenido_usado:0.85, score_colaborativo_usado:0.82, score_boost_aplicado:0.96, estrategia_usada:"tendencia_informal" },
  { id_recomendacion:5, id_establecimiento:105, nombre_establecimiento:"Sopa de Lima Doña Esther",    categoria_recomendacion:"colaborativo_cluster",   es_informal:false, calificacion_promedio:4.7, total_resenas:64,  distancia_km:3.2, tipo_establecimiento:"restaurante",    razon_principal:"Muy popular en tu comunidad",  detalle_razon:"Usuarios con preferencias similares a las tuyas lo visitan seguido",  score_total:0.84, score_contenido_usado:0.80, score_colaborativo_usado:0.91, score_boost_aplicado:0.75, estrategia_usada:"collab_filter" },
  { id_recomendacion:6, id_establecimiento:106, nombre_establecimiento:"Tamales Colados La Lupita",   categoria_recomendacion:"descubrimiento",         es_informal:true,  calificacion_promedio:0.0, total_resenas:0,   distancia_km:1.2, tipo_establecimiento:"puesto_informal", razon_principal:"¡Recién agregado!",          detalle_razon:"Sé de los primeros en probar este lugar",           score_total:0.75, score_contenido_usado:0.0, score_colaborativo_usado:0.0, score_boost_aplicado:0.0, estrategia_usada:"novedad" },
  { id_recomendacion:7, id_establecimiento:107, nombre_establecimiento:"Café de Altura Mirador",      categoria_recomendacion:"cold_start",             es_informal:false, calificacion_promedio:4.3, total_resenas:156, distancia_km:1.5, tipo_establecimiento:"local_comercial",  razon_principal:"Un clásico seguro", detalle_razon:"Lugar muy reconocido en la ciudad",                 score_total:0.81, score_contenido_usado:0.90, score_colaborativo_usado:0.70, score_boost_aplicado:0.74, estrategia_usada:"popularidad_global" },
];

// Configuración de secciones (Sincronizado con Motor_Recomendaciones.md del Backend)
const _SECCIONES = {
  top_picks_hibrido:    { titulo:"Mejores Selecciones Para Ti",icono:"star",          textura:true  }, // Carrusel Estrella
  preferencia_contenido:{ titulo:"Basado en tus gustos",      icono:"favorite",      textura:false },
  colaborativo_cluster: { titulo:"Gente como tú visitó",      icono:"group",         textura:false },
  popularidad_zona:     { titulo:"Populares cerca de ti",     icono:"near_me",       textura:false },
  tendencia_informal:   { titulo:"Apoya el comercio local",   icono:"storefront",    textura:true  },
  descubrimiento:       { titulo:"Descubrimientos recientes", icono:"new_releases",  textura:false },
  cold_start:           { titulo:"Populares de la semana",    icono:"explore",       textura:false },
};

// Utilidades
function _stars(rating) {
  const r = rating || 0;
  return [1,2,3,4,5].map(i =>
    `<span style="color:${i<=Math.round(r)?'var(--warning-subtle)':'var(--border-default)'};">★</span>`
  ).join('');
}

function _informalBadge() {
  return `<span class="inline-flex items-center gap-1 text-label-sm px-2 py-0.5 rounded bg-accent-faint text-accent border border-accent/30"><span class="material-symbols-outlined" style="font-size:11px;line-height:1;">storefront</span>Puesto informal</span>`;
}

function _tipoBadge(tipo) {
  if (tipo === 'restaurante')    return `<span class="text-label-sm px-2 py-0.5 rounded bg-secondary-faint text-secondary border border-secondary/30">Restaurante</span>`;
  if (tipo === 'local_comercial') return `<span class="text-label-sm px-2 py-0.5 rounded bg-surface-dim text-text-tertiary border border-border-default">Local</span>`;
  return '';
}

function _skeletons(n) {
  return Array.from({length:n||3}, () => `
    <div class="bg-surface-raised border border-border-default rounded-md overflow-hidden">
      <div class="skeleton w-full" style="aspect-ratio:16/9;"></div>
      <div class="p-4 space-y-3">
        <div class="skeleton h-5 rounded w-3/4"></div>
        <div class="skeleton h-4 rounded w-1/3"></div>
        <div class="skeleton h-14 rounded w-full"></div>
      </div>
    </div>`).join('');
}

// Tarjeta 
function _tarjeta(rec, delay) {
  const score = Math.round((rec.score_total||0)*100);
  const dist  = rec.distancia_km ? `${rec.distancia_km.toFixed(1)} km` : null;
  const img   = `https://picsum.photos/seed/${rec.id_establecimiento}/600/360`;
  const c     = Math.round((rec.score_contenido_usado||0)*100);
  const col   = Math.round((rec.score_colaborativo_usado||0)*100);

  return `
    <article role="listitem"
      class="bg-surface-raised border border-border-default rounded-md overflow-hidden flex-shrink-0 w-72 md:w-auto snap-start
             hover:border-border-strong hover:shadow-md transition-all duration-200 cursor-pointer group card-enter"
      style="animation-delay:${delay}ms"
      onclick="_irEstab(${rec.id_establecimiento},${rec.id_recomendacion})">

      <div class="relative overflow-hidden bg-surface-dim" style="aspect-ratio:16/9;">
        <img src="${img}" alt="${rec.nombre_establecimiento}"
          class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          loading="lazy" onerror="this.src='https://picsum.photos/600/360?grayscale'" />
        <div class="absolute top-3 right-3 bg-primary/70 backdrop-blur-sm text-white
                    text-label-md px-2 py-0.5 rounded font-bold tabular-nums">${score}% match</div>
        ${rec.es_informal ? `<div class="absolute top-3 left-3 bg-accent text-white text-label-sm px-2 py-0.5 rounded flex items-center gap-1">
          <span class="material-symbols-outlined" style="font-size:12px;line-height:1;">storefront</span>Informal</div>` : ''}
      </div>

      <div class="p-4">
        <div class="flex items-start justify-between gap-2 mb-2">
          <h3 class="font-heading text-headline-sm text-primary leading-snug flex-1">${rec.nombre_establecimiento}</h3>
          <button onclick="event.stopPropagation();_favFeed(${rec.id_establecimiento},this)"
            class="text-text-tertiary hover:text-accent transition-colors flex-shrink-0 mt-0.5" title="Guardar">
            <span class="material-symbols-outlined" style="font-size:20px;">favorite</span>
          </button>
        </div>

        <div class="flex items-center flex-wrap gap-x-3 gap-y-1 mb-3">
          <div class="flex items-center gap-1 text-sm">
            ${_stars(rec.calificacion_promedio)}
            <span class="text-numeric-sm text-text-secondary ml-1">${(rec.calificacion_promedio||0).toFixed(1)}</span>
            <span class="text-label-md text-text-tertiary">(${rec.total_resenas||0})</span>
          </div>
          ${dist ? `<span class="flex items-center gap-1 text-body-sm text-text-tertiary">
            <span class="material-symbols-outlined" style="font-size:14px;line-height:1;">near_me</span>${dist}</span>` : ''}
          ${rec.es_informal ? _informalBadge() : _tipoBadge(rec.tipo_establecimiento)}
        </div>

        <div class="bg-secondary-faint border border-secondary/20 rounded p-3">
          <div class="flex items-start gap-2">
            <span class="material-symbols-outlined text-secondary flex-shrink-0" style="font-size:15px;margin-top:2px;">shield</span>
            <div class="min-w-0">
              <p class="text-body-sm font-semibold text-secondary leading-snug">${rec.razon_principal}</p>
              <p class="text-label-md text-text-tertiary mt-0.5 leading-relaxed">${rec.detalle_razon}</p>
              <div class="flex gap-4 mt-2">
                <span class="text-label-md text-text-tertiary">Contenido <strong class="text-secondary tabular-nums">${c}%</strong></span>
                <span class="text-label-md text-text-tertiary">Comunidad <strong class="text-secondary tabular-nums">${col}%</strong></span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </article>`;
}

// Sección 
function _seccionFeed(cat, items) {
  const cfg = _SECCIONES[cat] || { titulo:cat, icono:'restaurant', textura:false };
  const cards = items.map((r,i) => _tarjeta(r, i*70)).join('');

  const inner = `
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-2 text-accent">
        <span class="material-symbols-outlined">${cfg.icono}</span>
        <h2 class="font-heading text-headline-lg text-primary">${cfg.titulo}</h2>
      </div>
      <a href="#/buscar" class="flex items-center gap-1 text-label-lg text-secondary hover:text-secondary-subtle transition-colors uppercase tracking-wide">
        Ver todo <span class="material-symbols-outlined" style="font-size:16px;">arrow_forward</span>
      </a>
    </div>
    <div role="list" aria-label="${cfg.titulo}" class="flex gap-4 overflow-x-auto snap-x snap-mandatory pb-2 -mx-4 px-4 md:grid md:grid-cols-2 md:gap-5 md:overflow-x-visible md:snap-none md:mx-0 md:px-0 lg:grid-cols-3">${cards}</div>`;

  if (cfg.textura) {
    return `<section class="mb-14 eki-texture-bg rounded-md relative overflow-hidden p-6 md:p-8">
      <div class="relative z-10">${inner}</div>
    </section>`;
  }
  return `<section class="mb-14">${inner}</section>`;
}

// Acciones globales 
async function _irEstab(idEstab, idRec) {
  try { await api.registrarClick(idRec); } catch(_) {}
  try { await api.registrarInteraccion(idEstab, 'vista_detalle'); } catch(_) {}
  window.location.hash = `#/establecimiento/${idEstab}`;
}

async function _favFeed(idEstab, btn) {
  const was = btn.dataset.fav === 'true';
  try {
    await api.toggleFavorito(idEstab, was ? 'DELETE' : 'POST');
    btn.dataset.fav = was ? 'false' : 'true';
    btn.querySelector('.material-symbols-outlined').style.color = was ? '' : 'var(--accent)';
    showToast(was ? 'Eliminado de favoritos' : '¡Guardado en favoritos!', was ? 'info' : 'success');
  } catch(_) { showToast('No se pudo actualizar el favorito', 'error'); }
}

// Reintento inteligente para inicio en frío del servidor en Render (spin-down ~20-30s)
async function _fetchRecomendacionesConRetry(maxIntentos = 4, delaySeg = 5) {
  for (let intento = 1; intento <= maxIntentos; intento++) {
    try {
      const recs = await api.getRecomendaciones();
      return recs; // éxito
    } catch (err) {
      if (intento === maxIntentos) throw err;
      // Mostrar UI de "despertando servidor" con contador regresivo
      _mostrarEstadoDespertando(intento, delaySeg);
      await new Promise(r => setTimeout(r, delaySeg * 1000));
    }
  }
}

function _mostrarEstadoDespertando(intento, delaySeg) {
  const el = document.getElementById('feed-content');
  if (!el) return;
  el.innerHTML = `
    <div class="flex flex-col items-center justify-center py-20 text-center fade-in">
      <span class="material-symbols-outlined text-5xl text-accent mb-4 animate-pulse">cloud_sync</span>
      <h3 class="font-heading text-headline-md text-primary mb-2">El servidor está despertando...</h3>
      <p class="text-body-sm text-text-secondary mb-2">
        Esto puede tomar hasta 30 segundos la primera vez del día.
      </p>
      <p class="text-label-md text-text-tertiary">Intento ${intento} — reintentando en ${delaySeg}s</p>
    </div>`;
}

// Controlador Principal
window.controllers.feed = async () => {
  if (!appState.location) {
    solicitarUbicacion()
      .then(({ lat, lon }) => { appState.setLocation(lat, lon); api.enviarUbicacion(lat, lon).catch(()=>{}); })
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
    contentEl.innerHTML = `
      <section class="mb-14">
        <div class="flex items-center gap-3 mb-6">
          <div class="skeleton w-5 h-5 rounded"></div>
          <div class="skeleton h-7 w-44 rounded"></div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">${_skeletons(3)}</div>
      </section>
      <section class="mb-14">
        <div class="flex items-center gap-3 mb-6">
          <div class="skeleton w-5 h-5 rounded"></div>
          <div class="skeleton h-7 w-56 rounded"></div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">${_skeletons(3)}</div>
      </section>
    `;
  }

  try {
    let recs = [];
    try { recs = await _fetchRecomendacionesConRetry(4, 5); } catch(_) {}
    if (!recs || !recs.length) recs = _MOCK_RECS;

    const grupos = {};
    recs.forEach(r => { if (!grupos[r.categoria_recomendacion]) grupos[r.categoria_recomendacion]=[]; grupos[r.categoria_recomendacion].push(r); });

    const orden = Object.keys(_SECCIONES);
    const extra  = Object.keys(grupos).filter(k => !_SECCIONES[k]);
    const html   = [...orden, ...extra].filter(k => grupos[k]?.length).map(k => _seccionFeed(k, grupos[k])).join('');

    const el = document.getElementById('feed-content');
    if (el) el.innerHTML = html || `
      <div class="flex flex-col items-center justify-center py-24 text-center">
        <span class="material-symbols-outlined text-5xl text-text-tertiary mb-4">restaurant</span>
        <h3 class="font-heading text-headline-md text-primary mb-2">Aún no hay recomendaciones</h3>
        <p class="text-body-md text-text-secondary max-w-sm mb-6">Completa tu perfil de gustos para que podamos sugerirte los mejores lugares.</p>
        <a href="#/onboarding" class="bg-accent text-white px-6 py-2.5 rounded font-semibold text-label-lg hover:bg-accent-hover active:scale-95 transition-all shadow">Ajustar preferencias</a>
      </div>`;
  } catch(e) {
    const el = document.getElementById('feed-content');
    if (el) el.innerHTML = `
      <div class="flex flex-col items-center justify-center py-20 text-center">
        <span class="material-symbols-outlined text-5xl text-text-tertiary mb-4">wifi_off</span>
        <h3 class="font-heading text-headline-md text-primary mb-2">No pudimos conectar</h3>
        <p class="text-body-sm text-text-secondary mb-6">Verifica tu conexión e intenta de nuevo.</p>
        <button onclick="window.controllers.feed()" class="bg-accent text-white px-5 py-2.5 rounded font-semibold text-label-lg hover:bg-accent-hover active:scale-95 transition-all">Reintentar</button>
      </div>`;
  }
};
