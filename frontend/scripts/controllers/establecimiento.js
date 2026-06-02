/**
 * establecimiento.js — Ficha detallada de un establecimiento
 * EkiSystem — Fase 4 Frontend
 */
import { api } from '../api.js';
import { appState } from '../state.js';
import { escapeHTML, showToast } from '../utils.js';
import { Stars } from '../components/Stars.js';
import { Favorite } from '../components/Favorite.js';
import { renderView } from '../app.js';

const _DIAS = { 1:'Lunes', 2:'Martes', 3:'Miércoles', 4:'Jueves', 5:'Viernes', 6:'Sábado', 7:'Domingo', lunes:'Lunes', martes:'Martes', miercoles:'Miércoles', jueves:'Jueves', viernes:'Viernes', sabado:'Sábado', domingo:'Domingo' };
const _DIAS_ORDEN = [1, 2, 3, 4, 5, 6, 7, 'lunes','martes','miercoles','jueves','viernes','sabado','domingo'];

// Utilidades
function _fecha(str) {
  if (!str) return '';
  return new Date(str).toLocaleDateString('es-MX', { year:'numeric', month:'short', day:'numeric' });
}

function _sentimientoBadge(polaridad) {
  if (polaridad === null || polaridad === undefined) return '';
  if (polaridad >  0.1) return `<span class="text-label-sm text-success flex items-center gap-1"><span class="material-symbols-outlined pointer-events-none" style="font-size:13px;">sentiment_satisfied</span>Positiva</span>`;
  if (polaridad < -0.1) return `<span class="text-label-sm text-accent flex items-center gap-1"><span class="material-symbols-outlined pointer-events-none" style="font-size:13px;">sentiment_dissatisfied</span>Negativa</span>`;
  return `<span class="text-label-sm text-text-tertiary flex items-center gap-1"><span class="material-symbols-outlined pointer-events-none" style="font-size:13px;">sentiment_neutral</span>Neutral</span>`;
}

function _horarios(list) {
  if (!list || !list.length) return `<p class="text-body-sm text-text-tertiary italic">Sin horarios registrados.</p>`;
  const sorted = [...list].sort((a,b) => {
    const idxA = _DIAS_ORDEN.findIndex(x => String(x) === String(a.dia_semana));
    const idxB = _DIAS_ORDEN.findIndex(x => String(x) === String(b.dia_semana));
    return (idxA > -1 ? idxA : 99) - (idxB > -1 ? idxB : 99);
  });
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
    ${items.map(p => {
      const nombre = escapeHTML(p.nombre || '');
      const descripcion = escapeHTML(p.descripcion || '');
      return `
      <div class="flex items-start gap-3 bg-surface-raised border border-border-default rounded-md p-3 hover:border-border-strong transition-colors">
        <div class="flex-1 min-w-0">
          <p class="font-heading text-headline-sm text-primary">${nombre}</p>
          ${descripcion ? `<p class="text-body-sm text-text-secondary mt-0.5 line-clamp-2">${descripcion}</p>` : ''}
        </div>
        ${p.precio ? `<p class="text-numeric-sm text-success flex-shrink-0">$${parseFloat(p.precio).toFixed(0)}</p>` : ''}
      </div>`
    }).join('')}
  </div>`;
}

// Reseñas
function _resena(r, idx) {
  const nombreRaw = r.nombre_usuario || 'Usuario';
  const nombre = escapeHTML(nombreRaw);
  const inicial = nombreRaw[0].toUpperCase();
  const comentario = escapeHTML(r.comentario || '');
  const cal = r.calificacion || 0;
  return `
    <div class="flex gap-3 card-enter" style="animation-delay:${idx*60}ms">
      <div class="w-9 h-9 rounded-full bg-primary-faint flex items-center justify-center text-primary-ghost font-bold text-sm flex-shrink-0">
        ${inicial}
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 flex-wrap mb-1">
          <span class="text-body-sm font-semibold text-primary">${nombre}</span>
          <span class="text-warning-subtle" style="font-size:0.85rem;">${'★'.repeat(cal)}${'☆'.repeat(5-cal)}</span>
          ${r.fecha_resena ? `<span class="text-label-md text-text-tertiary">${_fecha(r.fecha_resena)}</span>` : ''}
          ${r.procesado_nlp ? _sentimientoBadge(r.polaridad) : ''}
        </div>
        ${comentario ? `<p class="text-body-sm text-text-secondary leading-relaxed">${comentario}</p>` : ''}
      </div>
    </div>`;
}

function _starsInteractivos() {
  return `
    <div id="star-selector" class="flex gap-1 mb-4" role="group" aria-label="Calificación">
      ${[1,2,3,4,5].map(n => `
        <button type="button" data-action="select-star" data-star="${n}" 
          aria-label="${n} estrella${n > 1 ? 's' : ''}"
          aria-pressed="false"
          class="text-3xl leading-none transition-transform hover:scale-110"
          style="color:rgb(var(--border-default));">★</button>`).join('')}
    </div>
    <input type="hidden" id="star-value" value="0" />`;
}

function _selectStar(n) {
  const valInput = document.getElementById('star-value');
  if (valInput) valInput.value = n;
  document.querySelectorAll('#star-selector button').forEach(btn => {
    const starVal = parseInt(btn.dataset.star);
    btn.style.color = starVal <= n ? 'rgb(var(--warning-subtle))' : 'rgb(var(--border-default))';
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

// Interacciones y API
async function _enviarResena(idEstab, btn) {
  const cal = parseInt(document.getElementById('star-value')?.value || '0');
  const comentario = document.getElementById('resena-comentario')?.value?.trim();
  
  if (!cal) { showToast('Selecciona una calificación (1–5 estrellas)', 'warning'); return; }

  // 1. Obtener valores originales guardados en el DOM
  const formEl = document.getElementById('resena-comentario');
  const origCal = parseInt(formEl?.dataset?.origCal || '0');
  const origComent = (formEl?.dataset?.origComent || '').trim();

  // 2. Validar si hubo cambios reales (solo si ya existía una reseña)
  if (origCal > 0) {
    if (cal === origCal && (comentario || '') === origComent) {
      showToast('No has realizado cambios en tu reseña con respecto a la anterior.', 'warning');
      return;
    }
    // 3. Confirmación modal nativa para actualizar
    if (!window.confirm("Estás a punto de actualizar tu reseña. ¿Deseas continuar?")) {
      return;
    }
  }

  btn.disabled = true;
  const originalText = btn.innerHTML;
  btn.innerHTML = `<span class="material-symbols-outlined animate-spin text-base pointer-events-none" style="font-size:16px;">progress_activity</span> Enviando...`;
  try {
    await api.crearResena(idEstab, { id_establecimiento:idEstab, calificacion:cal, comentario:comentario||null });
    showToast(origCal > 0 ? '¡Reseña actualizada!' : '¡Reseña guardada!', 'success');
    setTimeout(() => {
      establecimientoController(idEstab);
    }, 1500);
  } catch(_) {
    showToast('Error al enviar la reseña', 'error');
    btn.disabled = false;
    btn.innerHTML = originalText;
  }
}

// Lógica para el modal de paginación de reseñas
let modalResenasPage = 1;
const MODAL_RESENAS_PAGE_SIZE = 10;

function _abrirModalResenas() {
  modalResenasPage = 1;
  let modalContainer = document.getElementById('modal-todas-resenas');
  if (!modalContainer) {
    modalContainer = document.createElement('div');
    modalContainer.id = 'modal-todas-resenas';
    modalContainer.className = 'fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6';
    modalContainer.style.background = 'rgba(30, 27, 24, 0.7)';
    document.body.appendChild(modalContainer);
    
    // Delegar clicks en el document para el botón cerrar y backdrop no aplica porque interceptamos directo
    modalContainer.addEventListener('click', (e) => {
      if (e.target === modalContainer || e.target.closest('[data-action="cerrar-modal-resenas"]')) {
        _cerrarModalResenas();
      } else if (e.target.closest('[data-action="cargar-mas-resenas"]')) {
        _cargarMasResenas();
      }
    });
  }

  const resenas = window._currentEstablecimientoResenas || [];
  const visible = resenas.slice(0, MODAL_RESENAS_PAGE_SIZE);
  
  modalContainer.innerHTML = `
    <div class="bg-surface-default w-full max-w-2xl max-h-[85vh] rounded-lg shadow-xl flex flex-col fade-in">
      <div class="p-4 sm:p-6 border-b border-border-subtle flex justify-between items-center sticky top-0 bg-surface-default z-10 rounded-t-lg">
        <h2 class="font-heading text-headline-sm text-primary">Todas las reseñas (${resenas.length})</h2>
        <button data-action="cerrar-modal-resenas" class="text-text-tertiary hover:text-primary transition-colors p-1">
          <span class="material-symbols-outlined" style="font-size:24px;">close</span>
        </button>
      </div>
      <div class="p-4 sm:p-6 overflow-y-auto" id="modal-resenas-list">
        <div class="space-y-6">
          ${visible.map((r,i) => _resena(r,i)).join('')}
        </div>
        ${resenas.length > MODAL_RESENAS_PAGE_SIZE ? `
          <div class="mt-8 text-center" id="modal-resenas-footer">
            <button data-action="cargar-mas-resenas" 
              class="px-5 py-2 border border-border-strong rounded-full text-label-md font-semibold text-primary hover:bg-surface-raised transition-colors">
              Cargar más reseñas
            </button>
          </div>
        ` : ''}
      </div>
    </div>
  `;
  modalContainer.classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

function _cargarMasResenas() {
  const resenas = window._currentEstablecimientoResenas || [];
  modalResenasPage++;
  const visible = resenas.slice(0, modalResenasPage * MODAL_RESENAS_PAGE_SIZE);
  
  const listContainer = document.getElementById('modal-resenas-list');
  if (!listContainer) return;

  const contentHtml = `
    <div class="space-y-6">
      ${visible.map((r,i) => _resena(r,i)).join('')}
    </div>
  `;
  
  const footerEl = document.getElementById('modal-resenas-footer');
  
  // Reemplazar la lista preservando el footer si aplica
  if (visible.length >= resenas.length) {
    if (footerEl) footerEl.remove();
    listContainer.innerHTML = contentHtml + `<p class="text-center text-body-sm text-text-tertiary italic mt-8 pb-4">No hay más reseñas por cargar.</p>`;
  } else {
    listContainer.querySelector('.space-y-6').outerHTML = contentHtml;
  }
}

function _cerrarModalResenas() {
  const modalContainer = document.getElementById('modal-todas-resenas');
  if (modalContainer) {
    modalContainer.classList.add('hidden');
  }
  document.body.style.overflow = '';
}

// Controlador Principal
export default async function establecimientoController(id) {
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
        <span class="material-symbols-outlined text-5xl text-text-tertiary mb-4 pointer-events-none">restaurant</span>
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

  const nombreEscapado = escapeHTML(estab.nombre || '');
  const descripcionEscapada = escapeHTML(estab.descripcion || '');
  const dirEscapada = escapeHTML(estab.direccion_texto || '');
  const telEscapado = escapeHTML(estab.telefono || '');
  const img       = `https://picsum.photos/seed/${estab.id_establecimiento||id}/1200/500`;
  const cal       = parseFloat(estab.calificacion_promedio) || 0;
  const totalR    = estab.total_resenas || 0;
  const resenas   = (estab.resenas||[]).filter(r => r.estado==='aprobado');
  const isAuth    = appState.isAuthenticated;
  const tipoLabel = { puesto_informal:'Puesto Informal', restaurante:'Restaurante', local_comercial:'Local Comercial' }[estab.tipo_establecimiento] || 'Establecimiento';

  container.innerHTML = `
      <a href="javascript:history.back()" class="inline-flex items-center gap-1 text-body-sm font-semibold text-text-tertiary hover:text-secondary transition-colors mb-6 group">
        <span class="material-symbols-outlined group-hover:-translate-x-1 transition-transform pointer-events-none" style="font-size:18px;">arrow_back</span>
        Volver
      </a>

      <div class="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-6">
        <div>
          <h1 class="font-heading text-display-md text-primary mb-3 leading-tight">${nombreEscapado}</h1>
          <div class="flex items-center flex-wrap gap-3">
            <span class="inline-flex items-center gap-1.5 text-label-lg px-3 py-1 rounded-full border
              ${estab.es_informal
                ? 'bg-accent-faint text-accent border-accent/30'
                : 'bg-secondary-faint text-secondary border-secondary/30'}">
              <span class="material-symbols-outlined pointer-events-none" style="font-size:15px;">${estab.es_informal?'storefront':'restaurant'}</span>
              ${tipoLabel}
            </span>
            ${cal > 0 ? `
              <div class="flex items-center gap-1.5">
                <span>${Stars.render(cal)}</span>
                <span class="text-numeric-sm text-text-secondary tabular-nums">${cal.toFixed(1)}</span>
                <span class="text-label-md text-text-tertiary">(${totalR} reseñas)</span>
              </div>` : ''}
          </div>
        </div>

        <div class="flex items-center gap-2 flex-shrink-0 flex-wrap">
          <button data-action="toggle-fav" data-id="${estab.id_establecimiento}"
            aria-label="${isFav ? 'Quitar de favoritos' : 'Guardar en favoritos'}"
            aria-pressed="${isFav}"
            class="flex items-center gap-1.5 px-3 py-2 rounded border 
                   ${isFav ? 'border-accent bg-accent-faint text-accent' : 'border-border-default text-text-secondary'}
                   hover:border-accent hover:text-accent transition-all">
            <span class="material-symbols-outlined pointer-events-none" style="font-size:17px; font-variation-settings: ${isFav ? "'FILL' 1" : "'FILL' 0"}">favorite</span>
            <span class="_fav-label pointer-events-none">${isFav ? 'Guardado' : 'Guardar'}</span>
          </button>
          ${estab.latitud && estab.longitud ? `
            <button data-action="abrir-maps" data-lat="${estab.latitud}" data-lng="${estab.longitud}" data-id="${estab.id_establecimiento}"
              aria-label="Abrir en Maps"
              class="flex items-center gap-1.5 px-3 py-2 rounded border border-border-default
                     text-body-sm text-text-secondary hover:border-secondary hover:text-secondary transition-all">
              <span class="material-symbols-outlined pointer-events-none" style="font-size:17px;">map</span>
              Maps
            </button>` : ''}
          ${estab.telefono ? `
            <a href="tel:${telEscapado}" data-action="llamar" data-id="${estab.id_establecimiento}"
              aria-label="Llamar"
              class="flex items-center gap-1.5 px-3 py-2 rounded border border-border-default
                     text-body-sm text-text-secondary hover:border-border-strong transition-all">
              <span class="material-symbols-outlined pointer-events-none" style="font-size:17px;">call</span>
              ${telEscapado}
            </a>` : ''}
          <button data-action="compartir" data-id="${estab.id_establecimiento}" data-nombre="${nombreEscapado}"
            aria-label="Compartir"
            class="flex items-center gap-1.5 px-3 py-2 rounded border border-border-default
                   text-body-sm text-text-secondary hover:border-border-strong transition-all">
            <span class="material-symbols-outlined pointer-events-none" style="font-size:17px;">share</span>
            Compartir
          </button>
        </div>
      </div>

      <div class="relative rounded-md overflow-hidden mb-8 bg-surface-dim" style="aspect-ratio:21/9;max-height:420px;">
        <img src="${img}" alt="${nombreEscapado}"
          class="w-full h-full object-cover"
          onerror="this.src='https://picsum.photos/1200/500?grayscale'" />
        <div class="absolute inset-0 bg-gradient-to-t from-black/25 to-transparent pointer-events-none"></div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-10">

        <div class="md:col-span-2 space-y-10">

          ${descripcionEscapada ? `
            <div>
              <h2 class="font-heading text-headline-md text-primary mb-3">Sobre este lugar</h2>
              <p class="text-body-md text-text-secondary leading-relaxed">${descripcionEscapada}</p>
            </div>` : ''}

          <div>
            <h2 class="font-heading text-headline-md text-primary mb-3">Menú</h2>
            ${_platillos(estab.platillos)}
          </div>

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
              if (!otrasResenas.length) {
                return `<p class="text-body-sm text-text-tertiary italic">Aún no hay reseñas aprobadas.</p>`;
              }
              const maxVisible = 3;
              const visibleResenas = otrasResenas.slice(0, maxVisible);
              let html = `<div class="space-y-5">${visibleResenas.map((r,i) => _resena(r,i)).join('')}</div>`;
              
              if (otrasResenas.length > maxVisible) {
                // Almacenar globalmente para el modal de paginación
                window._currentEstablecimientoResenas = otrasResenas;
                html += `
                  <div class="mt-6 text-center">
                    <button data-action="ver-todas-resenas" 
                      class="inline-flex items-center gap-2 text-primary font-semibold text-label-lg px-6 py-2.5 rounded-full border border-border-strong hover:bg-surface-raised transition-colors">
                      Ver las ${otrasResenas.length} reseñas
                      <span class="material-symbols-outlined" style="font-size:18px;">open_in_new</span>
                    </button>
                  </div>
                `;
              }
              return html;
            })()}
          </div>

          ${isAuth ? (() => {
            const miResena = resenas.find(r => r.id_usuario === appState.user?.id_usuario);
            const botonTexto = miResena ? 'Actualizar reseña' : 'Enviar reseña';
            const calif = miResena ? miResena.calificacion : 0;
            const coment = miResena ? escapeHTML(miResena.comentario || '') : '';
            setTimeout(() => { if(calif) _selectStar(calif); }, 100);
            return `
            <div class="bg-surface-raised border border-border-default rounded-md p-6">
              <h3 class="font-heading text-headline-sm text-primary mb-4">${miResena ? 'Edita tu reseña' : 'Deja tu reseña'}</h3>
              <p class="text-label-md text-text-secondary mb-2 uppercase tracking-wide">Tu calificación</p>
              ${_starsInteractivos()}
              <textarea id="resena-comentario" placeholder="Comparte tu experiencia (opcional)..." maxlength="1000"
                data-orig-cal="${calif}" data-orig-coment="${coment}"
                class="w-full bg-surface-dim border border-border-default rounded p-3
                       text-body-sm text-text-primary placeholder:text-text-tertiary
                       focus:outline-none focus:border-border-focus focus:ring-2 focus:ring-border-focus/20
                       resize-none h-24 mb-4 transition-colors">${coment}</textarea>
              <button data-action="enviar-resena" data-id="${estab.id_establecimiento}"
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

        <div class="space-y-6">
          <div class="bg-surface-raised border border-border-default rounded-md p-5">
            <h3 class="font-heading text-headline-sm text-primary mb-4">Información</h3>
            <div class="space-y-3">
              ${dirEscapada ? `
                <div class="flex gap-2.5">
                  <span class="material-symbols-outlined text-text-tertiary flex-shrink-0 mt-0.5 pointer-events-none" style="font-size:17px;">location_on</span>
                  <p class="text-body-sm text-text-secondary">${dirEscapada}</p>
                </div>` : ''}
              ${estab.telefono ? `
                <div class="flex gap-2.5">
                  <span class="material-symbols-outlined text-text-tertiary flex-shrink-0 mt-0.5 pointer-events-none" style="font-size:17px;">call</span>
                  <a href="tel:${telEscapado}" data-action="llamar" data-id="${estab.id_establecimiento}" class="text-body-sm text-secondary hover:underline">${telEscapado}</a>
                </div>` : ''}
              ${estab.es_informal !== undefined ? `
                <div class="flex gap-2.5">
                  <span class="material-symbols-outlined text-text-tertiary flex-shrink-0 mt-0.5 pointer-events-none" style="font-size:17px;">storefront</span>
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
      <div class="mt-4 text-center">
        <a href="#/como-funciona"
           class="text-label-md text-text-tertiary hover:text-secondary underline underline-offset-2 transition-colors">
          ¿Cómo funcionan las recomendaciones?
        </a>
      </div>
  `;

  // Attach local event listeners for delegated actions
  const starSelector = document.getElementById('star-selector');
  if (starSelector) {
    starSelector.addEventListener('keydown', (e) => {
      const actionEl = e.target.closest('[data-action="select-star"]');
      if (!actionEl) return;
      const n = parseInt(actionEl.dataset.star, 10);
      _handleStarKeydown(e, n);
    });
  }

  container.addEventListener('click', async (e) => {
    const actionEl = e.target.closest('[data-action]');
    if (!actionEl) return;
    const action = actionEl.dataset.action;
    
    if (action === 'select-star') {
      const n = parseInt(actionEl.dataset.star, 10);
      _selectStar(n);
    } else if (action === 'enviar-resena') {
      const id = actionEl.dataset.id;
      _enviarResena(id, actionEl);
    } else if (action === 'ver-todas-resenas') {
      _abrirModalResenas();
    } else if (action === 'cargar-mas-resenas') {
      _cargarMasResenas();
    } else if (action === 'cerrar-modal-resenas') {
      _cerrarModalResenas();
    } else if (action === 'abrir-maps') {
      const lat = actionEl.dataset.lat;
      const lng = actionEl.dataset.lng;
      const id = actionEl.dataset.id;
      if (appState.isAuthenticated) api.registrarInteraccion(id, 'abrir_maps').catch(()=>{});
      window.open(`https://www.google.com/maps/search/?api=1&query=${lat},${lng}`, '_blank');
    } else if (action === 'llamar') {
      const id = actionEl.dataset.id;
      if (appState.isAuthenticated) api.registrarInteraccion(id, 'llamada_telefono').catch(()=>{});
    } else if (action === 'compartir') {
      const id = actionEl.dataset.id;
      const nombre = actionEl.dataset.nombre;
      if (appState.isAuthenticated) api.registrarInteraccion(id, 'compartido').catch(()=>{});
      const url = window.location.href;
      if (navigator.share) {
        try { await navigator.share({ title: nombre, url }); } catch(_) {}
      } else {
        navigator.clipboard.writeText(url).then(() => showToast('Enlace copiado', 'success'));
      }
    }
  });
};
