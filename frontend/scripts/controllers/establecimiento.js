
const _DIAS = { lunes:'Lunes', martes:'Martes', miercoles:'Miércoles', jueves:'Jueves', viernes:'Viernes', sabado:'Sábado', domingo:'Domingo' };
const _DIAS_ORDEN = ['lunes','martes','miercoles','jueves','viernes','sabado','domingo'];

// Las utilidades visuales (starsE) se movieron a scripts/components/

function _fecha(str) {
  if (!str) return '';
  return new Date(str).toLocaleDateString('es-MX', { year:'numeric', month:'short', day:'numeric' });
}

function _sentimientoBadge(polaridad) {
  if (polaridad === null || polaridad === undefined) return '';
  if (polaridad >  0.1) return `<span class="text-label-sm text-success flex items-center gap-1"><span class="material-symbols-outlined" style="font-size:13px;">sentiment_satisfied</span>Positiva</span>`;
  if (polaridad < -0.1) return `<span class="text-label-sm text-accent flex items-center gap-1"><span class="material-symbols-outlined" style="font-size:13px;">sentiment_dissatisfied</span>Negativa</span>`;
  return `<span class="text-label-sm text-text-tertiary flex items-center gap-1"><span class="material-symbols-outlined" style="font-size:13px;">sentiment_neutral</span>Neutral</span>`;
}

// Subbloques 
function _horarios(list) {
  if (!list || !list.length) return `<p class="text-body-sm text-text-tertiary italic">Sin horarios registrados.</p>`;
  const sorted = [...list].sort((a,b) => _DIAS_ORDEN.indexOf(a.dia_semana) - _DIAS_ORDEN.indexOf(b.dia_semana));
  return `<div class="divide-y divide-border-subtle border border-border-default rounded-md overflow-hidden">
    ${sorted.map(h => `
      <div class="flex justify-between items-center px-4 py-2.5 bg-surface-raised hover:bg-surface-dim transition-colors">
        <span class="text-body-sm font-medium text-text-secondary">${_DIAS[h.dia_semana]||h.dia_semana}</span>
        <span class="text-body-sm text-text-tertiary tabular-nums">
          ${h.hora_apertura?h.hora_apertura.slice(0,5):'—'} – ${h.hora_cierre?h.hora_cierre.slice(0,5):'—'}
        </span>
      </div>`).join('')}
  </div>`;
}

function _platillos(list) {
  const items = (list||[]).filter(p => p.estado === 'aprobado');
  if (!items.length) return `<p class="text-body-sm text-text-tertiary italic">Sin platillos registrados.</p>`;
  return `<div class="grid grid-cols-1 md:grid-cols-2 gap-3">
    ${items.map(p => `
      <div class="flex items-start gap-3 bg-surface-raised border border-border-default rounded-md p-3 hover:border-border-strong transition-colors">
        <div class="flex-1 min-w-0">
          <p class="font-heading text-headline-sm text-primary">${p.nombre}</p>
          ${p.descripcion ? `<p class="text-body-sm text-text-secondary mt-0.5 line-clamp-2">${p.descripcion}</p>` : ''}
        </div>
        ${p.precio ? `<p class="text-numeric-sm text-success flex-shrink-0">$${parseFloat(p.precio).toFixed(0)}</p>` : ''}
      </div>`).join('')}
  </div>`;
}

function _resena(r, idx) {
  const inicial = r.nombre_usuario ? r.nombre_usuario[0].toUpperCase() : '?';
  const cal = r.calificacion || 0;
  return `
    <div class="flex gap-3 card-enter" style="animation-delay:${idx*60}ms">
      <div class="w-9 h-9 rounded-full bg-primary-faint flex items-center justify-center text-primary-ghost font-bold text-sm flex-shrink-0">
        ${inicial}
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 flex-wrap mb-1">
          <span class="text-body-sm font-semibold text-primary">${r.nombre_usuario||'Usuario'}</span>
          <span class="text-warning-subtle" style="font-size:0.85rem;">${'★'.repeat(cal)}${'☆'.repeat(5-cal)}</span>
          ${r.fecha_resena ? `<span class="text-label-md text-text-tertiary">${_fecha(r.fecha_resena)}</span>` : ''}
          ${r.procesado_nlp ? _sentimientoBadge(r.polaridad) : ''}
        </div>
        ${r.comentario ? `<p class="text-body-sm text-text-secondary leading-relaxed">${r.comentario}</p>` : ''}
      </div>
    </div>`;
}

// Estrellas interactivas
function _starsInteractivos() {
  return `
    <div id="star-selector" class="flex gap-1 mb-4" role="group" aria-label="Calificación">
      ${[1,2,3,4,5].map(n => `
        <button type="button" data-star="${n}" 
          onclick="_selectStar(${n})"
          onkeydown="_handleStarKeydown(event, ${n})"
          aria-label="${n} estrella${n > 1 ? 's' : ''}"
          aria-pressed="false"
          class="text-3xl leading-none transition-transform hover:scale-110"
          style="color:var(--border-default);">★</button>`).join('')}
    </div>
    <input type="hidden" id="star-value" value="0" />`;
}

function _selectStar(n) {
  document.getElementById('star-value').value = n;
  document.querySelectorAll('#star-selector button').forEach(btn => {
    const starVal = parseInt(btn.dataset.star);
    btn.style.color = starVal <= n ? 'var(--warning-subtle)' : 'var(--border-default)';
    btn.setAttribute('aria-pressed', starVal <= n ? 'true' : 'false');
  });
}

function _handleStarKeydown(e, n) {
  if (e.key === 'ArrowRight' || e.key === 'ArrowUp') {
    e.preventDefault();
    if (n < 5) {
      const next = document.querySelector(`#star-selector button[data-star="${n + 1}"]`);
      if (next) { next.focus(); _selectStar(n + 1); }
    }
  } else if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') {
    e.preventDefault();
    if (n > 1) {
      const prev = document.querySelector(`#star-selector button[data-star="${n - 1}"]`);
      if (prev) { prev.focus(); _selectStar(n - 1); }
    }
  } else if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    _selectStar(n);
  }
}

// Enviar o actualizar reseña
async function _enviarResena(idEstab) {
  const cal = parseInt(document.getElementById('star-value')?.value || '0');
  const comentario = document.getElementById('resena-comentario')?.value?.trim();
  const btn = document.getElementById('btn-enviar-resena');
  if (!cal) { showToast('Selecciona una calificación (1–5 estrellas)', 'warning'); return; }
  btn.disabled = true;
  btn.innerHTML = `<span class="material-symbols-outlined animate-spin text-base" style="font-size:16px;">progress_activity</span> Enviando...`;
  try {
    await api.crearResena(idEstab, { id_establecimiento:idEstab, calificacion:cal, comentario:comentario||null });
    showToast('¡Reseña guardada!', 'success');
    setTimeout(() => location.reload(), 1500); // Reload to show updated reviews
  } catch(e) {
    showToast('No se pudo enviar la reseña.', 'warning');
    btn.disabled = false;
    btn.innerHTML = window._miResenaExistente ? 'Actualizar reseña' : 'Enviar reseña';
  }
}

// Acciones de botones
// _favEstab ha sido reemplazado por window.Favorite.toggle

window._abrirMaps = (idEstab, lat, lng) => {
  if (appState.isAuthenticated) {
    api.registrarInteraccion(idEstab, 'abrir_maps').catch(()=>{});
  }
  window.open(`https://www.google.com/maps/search/?api=1&query=${lat},${lng}`, '_blank');
};

window._compartir = async (idEstab, nombre) => {
  if (appState.isAuthenticated) {
    api.registrarInteraccion(idEstab, 'compartido').catch(()=>{});
  }
  const url = window.location.href;
  if (navigator.share) { try { await navigator.share({ title:nombre, url }); } catch(_) {} }
  else { navigator.clipboard.writeText(url).then(() => showToast('Enlace copiado', 'success')); }
}

// Controlador Principal
window.controllers.establecimiento = async (id) => {
  if (!id) { window.location.hash = '#/feed'; return; }

  const loaded = await renderView('establecimiento.html');
  if (!loaded) return;

  const container = document.getElementById('estab-container');
  if (!container) return;

  let estab;
  try {
    estab = await api.getEstablecimiento(id);
  } catch(e) {
    container.innerHTML = `
      <div class="flex flex-col items-center justify-center py-32 text-center px-4">
        <span class="material-symbols-outlined text-5xl text-text-tertiary mb-4">restaurant</span>
        <h2 class="font-heading text-headline-lg text-primary mb-2">Establecimiento no encontrado</h2>
        <p class="text-body-md text-text-secondary mb-6">Este lugar no está disponible o aún no ha sido aprobado.</p>
        <a href="#/buscar" class="bg-accent text-white px-5 py-2.5 rounded font-semibold hover:bg-accent-hover transition-colors">Explorar lugares</a>
      </div>`;
    return;
  }

  let isFav = false;
  if (appState.isAuthenticated) {
    api.registrarInteraccion(id, 'vista_detalle').catch(()=>{});
    try {
      const favs = await api.getFavoritos();
      isFav = favs.some(f => (f.id_establecimiento == id) || (f.establecimiento && f.establecimiento.id_establecimiento == id));
    } catch (e) {}
  }

  const img       = `https://picsum.photos/seed/${estab.id_establecimiento||id}/1200/500`;
  const cal       = parseFloat(estab.calificacion_promedio) || 0;
  const totalR    = estab.total_resenas || 0;
  const resenas   = (estab.resenas||[]).filter(r => r.estado==='aprobado');
  const isAuth    = appState.isAuthenticated;
  const tipoLabel = { puesto_informal:'Puesto Informal', restaurante:'Restaurante', local_comercial:'Local Comercial' }[estab.tipo_establecimiento] || 'Establecimiento';

  container.innerHTML = `
      <!-- Back -->
      <a href="javascript:history.back()" class="inline-flex items-center gap-1 text-body-sm font-semibold text-text-tertiary hover:text-secondary transition-colors mb-6 group">
        <span class="material-symbols-outlined group-hover:-translate-x-1 transition-transform" style="font-size:18px;">arrow_back</span>
        Volver
      </a>

      <!-- Header -->
      <div class="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-6">
        <div>
          <h1 class="font-heading text-display-md text-primary mb-3 leading-tight">${estab.nombre}</h1>
          <div class="flex items-center flex-wrap gap-3">
            <span class="inline-flex items-center gap-1.5 text-label-lg px-3 py-1 rounded-full border
              ${estab.es_informal
                ? 'bg-accent-faint text-accent border-accent/30'
                : 'bg-secondary-faint text-secondary border-secondary/30'}">
              <span class="material-symbols-outlined" style="font-size:15px;">${estab.es_informal?'storefront':'restaurant'}</span>
              ${tipoLabel}
            </span>
            ${cal > 0 ? `
              <div class="flex items-center gap-1.5">
                <span>${window.Stars.render(cal)}</span>
                <span class="text-numeric-sm text-text-secondary tabular-nums">${cal.toFixed(1)}</span>
                <span class="text-label-md text-text-tertiary">(${totalR} reseñas)</span>
              </div>` : ''}
          </div>
        </div>

        <!-- Botones de acción -->
        <div class="flex items-center gap-2 flex-shrink-0 flex-wrap">
          <button id="btn-fav-estab" onclick="window.Favorite.toggle(${estab.id_establecimiento}, this)"
            aria-label="${isFav ? 'Quitar de favoritos' : 'Guardar en favoritos'}"
            aria-pressed="${isFav}"
            class="flex items-center gap-1.5 px-3 py-2 rounded border 
                   ${isFav ? 'border-accent bg-accent-faint text-accent' : 'border-border-default text-text-secondary'}
                   hover:border-accent hover:text-accent transition-all">
            <span class="material-symbols-outlined" style="font-size:17px; font-variation-settings: ${isFav ? "'FILL' 1" : "'FILL' 0"}">favorite</span>
            <span class="_fav-label">${isFav ? 'Guardado' : 'Guardar'}</span>
          </button>
          ${estab.latitud && estab.longitud ? `
            <button onclick="_abrirMaps(${estab.id_establecimiento},${estab.latitud},${estab.longitud})"
              aria-label="Abrir en Maps"
              class="flex items-center gap-1.5 px-3 py-2 rounded border border-border-default
                     text-body-sm text-text-secondary hover:border-secondary hover:text-secondary transition-all">
              <span class="material-symbols-outlined" style="font-size:17px;">map</span>
              Maps
            </button>` : ''}
          ${estab.telefono ? `
            <a href="tel:${estab.telefono}" onclick="if(window.appState.isAuthenticated){ api.registrarInteraccion(${estab.id_establecimiento},'llamada_telefono').catch(()=>{}); }"
              aria-label="Llamar"
              class="flex items-center gap-1.5 px-3 py-2 rounded border border-border-default
                     text-body-sm text-text-secondary hover:border-border-strong transition-all">
              <span class="material-symbols-outlined" style="font-size:17px;">call</span>
              ${estab.telefono}
            </a>` : ''}
          <button onclick="_compartir(${estab.id_establecimiento},'${(estab.nombre||'').replace(/'/g,"\\'")}')"
            aria-label="Compartir"
            class="flex items-center gap-1.5 px-3 py-2 rounded border border-border-default
                   text-body-sm text-text-secondary hover:border-border-strong transition-all">
            <span class="material-symbols-outlined" style="font-size:17px;">share</span>
            Compartir
          </button>
        </div>
      </div>

      <!-- Imagen -->
      <div class="relative rounded-md overflow-hidden mb-8 bg-surface-dim" style="aspect-ratio:21/9;max-height:420px;">
        <img src="${img}" alt="${estab.nombre}"
          class="w-full h-full object-cover"
          onerror="this.src='https://picsum.photos/1200/500?grayscale'" />
        <div class="absolute inset-0 bg-gradient-to-t from-black/25 to-transparent pointer-events-none"></div>
      </div>

      <!-- Contenido: 2/3 + sidebar -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-10">

        <!-- Principal -->
        <div class="md:col-span-2 space-y-10">

          ${estab.descripcion ? `
            <div>
              <h2 class="font-heading text-headline-md text-primary mb-3">Sobre este lugar</h2>
              <p class="text-body-md text-text-secondary leading-relaxed">${estab.descripcion}</p>
            </div>` : ''}

          <div>
            <h2 class="font-heading text-headline-md text-primary mb-3">Menú</h2>
            ${_platillos(estab.platillos)}
          </div>

          <!-- Reseñas -->
          <div>
            <div class="flex items-center justify-between mb-5">
              <h2 class="font-heading text-headline-md text-primary">Reseñas</h2>
              ${cal > 0 ? `
                <div class="flex items-center gap-2">
                  <span class="text-numeric-lg text-primary tabular-nums">${cal.toFixed(1)}</span>
                  <div>
                    <div class="text-warning-subtle">${'★'.repeat(Math.round(cal))}${'☆'.repeat(5-Math.round(cal))}</div>
                    <div class="text-label-md text-text-tertiary">${totalR} reseñas</div>
                  </div>
                </div>` : ''}
            </div>

            ${(() => {
              const otrasResenas = resenas.filter(r => r.id_usuario !== appState.user?.id_usuario);
              return otrasResenas.length
                ? `<div class="space-y-5">${otrasResenas.map((r,i) => _resena(r,i)).join('')}</div>`
                : `<p class="text-body-sm text-text-tertiary italic">Aún no hay reseñas aprobadas.</p>`;
            })()}
          </div>

          <!-- Formulario de reseña -->
          ${isAuth ? (() => {
            const miResena = resenas.find(r => r.id_usuario === appState.user?.id_usuario);
            window._miResenaExistente = !!miResena;
            const botonTexto = miResena ? 'Actualizar reseña' : 'Enviar reseña';
            const calif = miResena ? miResena.calificacion : 0;
            const coment = miResena ? (miResena.comentario || '') : '';
            // Llamar select star asincronamente después de renderizar
            setTimeout(() => { if(calif) _selectStar(calif); }, 100);
            return `
            <div class="bg-surface-raised border border-border-default rounded-md p-6">
              <h3 class="font-heading text-headline-sm text-primary mb-4">${miResena ? 'Edita tu reseña' : 'Deja tu reseña'}</h3>
              <p class="text-label-md text-text-secondary mb-2 uppercase tracking-wide">Tu calificación</p>
              ${_starsInteractivos()}
              <textarea id="resena-comentario" placeholder="Comparte tu experiencia (opcional)..." maxlength="1000"
                class="w-full bg-surface-dim border border-border-default rounded p-3
                       text-body-sm text-text-primary placeholder:text-text-tertiary
                       focus:outline-none focus:border-border-focus focus:ring-2 focus:ring-border-focus/20
                       resize-none h-24 mb-4 transition-colors">${coment}</textarea>
              <button id="btn-enviar-resena" onclick="_enviarResena(${estab.id_establecimiento})"
                class="bg-accent text-white px-6 py-2.5 rounded font-semibold text-label-lg
                       hover:bg-accent-hover active:scale-95 transition-all shadow-sm
                       disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-2">
                ${botonTexto}
              </button>
            </div>`;
          })() : `
            <div class="bg-surface-overlay border border-border-default rounded-md p-5 text-center">
              <p class="text-body-sm text-text-secondary">
                <a href="#/login" class="text-secondary font-semibold hover:underline">Inicia sesión</a>
                para dejar una reseña.
              </p>
            </div>`}
        </div>

        <!-- Sidebar -->
        <div class="space-y-6">
          <div class="bg-surface-raised border border-border-default rounded-md p-5">
            <h3 class="font-heading text-headline-sm text-primary mb-4">Información</h3>
            <div class="space-y-3">
              ${estab.direccion_texto ? `
                <div class="flex gap-2.5">
                  <span class="material-symbols-outlined text-text-tertiary flex-shrink-0 mt-0.5" style="font-size:17px;">location_on</span>
                  <p class="text-body-sm text-text-secondary">${estab.direccion_texto}</p>
                </div>` : ''}
              ${estab.telefono ? `
                <div class="flex gap-2.5">
                  <span class="material-symbols-outlined text-text-tertiary flex-shrink-0 mt-0.5" style="font-size:17px;">call</span>
                  <a href="tel:${estab.telefono}" class="text-body-sm text-secondary hover:underline">${estab.telefono}</a>
                </div>` : ''}
              ${estab.es_informal !== undefined ? `
                <div class="flex gap-2.5">
                  <span class="material-symbols-outlined text-text-tertiary flex-shrink-0 mt-0.5" style="font-size:17px;">storefront</span>
                  <p class="text-body-sm text-text-secondary">${estab.es_informal ? 'Puesto informal — parte del tejido local de Mérida.' : 'Establecimiento formal.'}</p>
                </div>` : ''}
            </div>
          </div>

          <div>
            <h3 class="font-heading text-headline-sm text-primary mb-3">Horarios</h3>
            ${_horarios(estab.horarios)}
          </div>
        </div>
      </div>
      <!-- Enlace caja blanca educativa -->
      <div class="mt-4 text-center">
        <a href="#/como-funciona"
           class="text-label-md text-text-tertiary hover:text-secondary underline underline-offset-2 transition-colors">
          ¿Cómo funcionan las recomendaciones?
        </a>
      </div>
  `;
};
