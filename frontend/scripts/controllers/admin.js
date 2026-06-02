/**
 * admin.js — Panel de Administración
 * EkiSystem — Fase 5 Frontend
 * Solo accesible para tipo_usuario === 'admin'
 */
import { api, apiRequest } from '../api.js';
import { appState } from '../state.js';
import { renderView } from '../app.js';
import { showToast } from '../utils.js';
import { Modal } from '../components/Modal.js';

const _ADMIN_TABS = [
  { id:'establecimientos_vis',  label:'Altas Visitantes',     icon:'person_add'  },
  { id:'establecimientos_prop', label:'Altas Propietarios',   icon:'storefront'  },
  { id:'reclamos',              label:'Reclamos de Propiedad',icon:'verified'    },
  { id:'jobs',                  label:'Jobs offline',         icon:'settings'    },
];
let _adminTab = 'establecimientos_vis';

// Jobs
const _JOBS = [
  { id:'clustering',      label:'Clustering',              desc:'Recalcula K-Means sobre los vectores de preferencias y reasigna clusters de usuarios.',    icon:'hub',            tiempo:'~30 s'  },
  { id:'recomendaciones', label:'Generar Recomendaciones', desc:'Motor híbrido para todos los usuarios activos. Puebla la tabla recomendacion_generada.',     icon:'recommend',     tiempo:'~2 min' },
  { id:'metricas',        label:'Actualizar Métricas',     desc:'Recalcula popularidad_7d, popularidad_30d y score_boost_combinado de cada establecimiento.', icon:'monitoring',    tiempo:'~20 s'  },
  { id:'nlp',             label:'Procesar NLP',            desc:'Análisis de sentimiento (TextBlob) sobre reseñas aprobadas pendientes de procesar.',         icon:'psychology',    tiempo:'~1 min' },
  { id:'archivado',       label:'Archivar interacciones',  desc:'Mueve interacciones con más de 90 días a la tabla histórica en batches de 1 000 filas.',      icon:'archive',       tiempo:'~10 s'  },
];

// Helpers
function _fechaAdmin(str) {
  if (!str) return '—';
  return new Date(str).toLocaleDateString('es-MX', {
    day:'2-digit', month:'short', year:'numeric', hour:'2-digit', minute:'2-digit',
  });
}

function _skelAdmin(n) {
  return Array.from({length:n||3}, () => `
    <div class="bg-surface-raised border border-border-default rounded-md p-5 space-y-3">
      <div class="skeleton h-5 rounded w-2/3"></div>
      <div class="skeleton h-4 rounded w-full"></div>
      <div class="skeleton h-4 rounded w-4/5"></div>
      <div class="flex gap-2 mt-3"><div class="skeleton h-8 rounded w-24"></div><div class="skeleton h-8 rounded w-24"></div></div>
    </div>`).join('');
}

// Navegación de tabs
function _setAdminTab(id) {
  _adminTab = id;
  _ADMIN_TABS.forEach(t => {
    const btn = document.getElementById(`atab-${t.id}`);
    if (!btn) return;
    btn.classList.remove('border-b-2','border-accent','text-primary','font-semibold','text-text-tertiary');
    if (t.id === id) {
      btn.classList.add('border-b-2','border-accent','text-primary','font-semibold');
    } else {
      btn.classList.add('text-text-tertiary');
    }
  });
  _renderAdminTab(id);
}

let _adminItemsCache = {};

async function _renderAdminTab(id) {
  const box = document.getElementById('admin-body');
  if (!box) return;

  if (id === 'jobs') { _renderJobs(box); return; }

  box.innerHTML = _skelAdmin(3);

  try {
    const items = await api.getPendientes(id);

    if (!items || !items.length) {
      box.innerHTML = `
        <div class="flex flex-col items-center py-16 text-center">
          <span class="material-symbols-outlined text-4xl text-[var(--success)] mb-3 pointer-events-none">check_circle</span>
          <p class="font-heading text-headline-sm text-primary mb-1">Todo al día</p>
          <p class="text-body-sm text-text-secondary">
            No hay ${id === 'establecimientos' ? 'establecimientos' : 'reseñas'} pendientes de revisión.
          </p>
        </div>`;
      return;
    }

    _adminItemsCache[id] = items;

    box.innerHTML = `
      <p class="text-label-md text-text-tertiary mb-4">${items.length} pendiente${items.length!==1?'s':''}</p>
      <div class="space-y-4">
        ${items.map((item, i) => {
          if (id === 'resenas') return _cardResena(item, i);
          if (id === 'reclamos') return _cardReclamo(item, i);
          return _cardEstab(item, i, id);
        }).join('')}
      </div>`;

  } catch(_) {
    box.innerHTML = `
      <div class="flex flex-col items-center py-12 text-center">
        <span class="material-symbols-outlined text-4xl text-text-tertiary mb-3 pointer-events-none">wifi_off</span>
        <p class="text-body-sm text-text-secondary mb-4">No se pudieron cargar los pendientes.</p>
        <button data-action="reintentar-admin" data-tab-id="${id}"
          class="bg-accent text-white px-4 py-2 rounded font-semibold hover:bg-accent-hover transition-colors">
          Reintentar
        </button>
      </div>`;
  }
}

// Tarjeta: establecimiento pendiente
function _cardEstab(e, idx, tabId) {
  const id = e.id_establecimiento;
  const tipoLabel = {
    puesto_informal:'Puesto informal', restaurante:'Restaurante', local_comercial:'Local comercial',
  }[e.tipo_establecimiento] || e.tipo_establecimiento || '—';

  return `
    <div id="estab-${id}"
         class="bg-surface-raised border border-border-default rounded-md p-5 card-enter"
         style="animation-delay:${idx*60}ms">
      <div class="flex items-start justify-between gap-4 mb-3">
        <div class="flex-1 min-w-0">
          <h3 class="font-heading text-headline-sm text-primary">${e.nombre || 'Sin nombre'}</h3>
          <div class="flex items-center gap-2 mt-1.5 flex-wrap">
            <span class="text-label-sm px-2 py-0.5 rounded bg-warning-faint text-warning border border-warning/30">
              Pendiente
            </span>
            <span class="text-label-md text-text-tertiary">${tipoLabel}</span>
            ${e.es_informal
              ? `<span class="text-label-sm px-2 py-0.5 rounded bg-accent-faint text-accent border border-accent/30">Informal</span>`
              : ''}
          </div>
        </div>
        <p class="text-label-md text-text-tertiary flex-shrink-0 whitespace-nowrap">${_fechaAdmin(e.fecha_registro)}</p>
      </div>

      ${e.descripcion
        ? `<p class="text-body-sm text-text-secondary mb-3 line-clamp-3 leading-relaxed">${e.descripcion}</p>`
        : ''}

      ${e.direccion_texto
        ? `<p class="flex items-center gap-1.5 text-body-sm text-text-tertiary mb-3">
             <span class="material-symbols-outlined pointer-events-none" style="font-size:15px;">location_on</span>
             ${e.direccion_texto}
           </p>`
        : ''}

      <div class="flex flex-wrap gap-2 pt-3 border-t border-border-subtle">
        <button data-action="ver-detalles" data-tab-id="${tabId}" data-idx="${idx}"
          class="flex items-center gap-1.5 px-4 py-2 rounded bg-primary text-white
                 font-semibold text-label-lg hover:opacity-90 active:scale-95 transition-all">
          <span class="material-symbols-outlined pointer-events-none" style="font-size:16px;">visibility</span> Revisar Detalles
        </button>
      </div>
    </div>`;
}

// Tarjeta: Reclamo de propiedad
function _cardReclamo(r, idx) {
  const est = r.establecimiento || {};
  const prop = r.propietario || {};
  return `
    <div id="reclamo-${r.id_propietario}-${r.id_establecimiento}"
         class="bg-surface-raised border border-border-default rounded-md p-5 card-enter"
         style="animation-delay:${idx*60}ms">
      <div class="flex items-start justify-between gap-4 mb-3">
        <div class="flex-1 min-w-0">
          <h3 class="font-heading text-headline-sm text-primary">Reclamo de: ${est.nombre || 'Desconocido'}</h3>
          <div class="flex items-center gap-2 mt-1.5 flex-wrap">
            <span class="text-label-sm px-2 py-0.5 rounded bg-warning-faint text-warning border border-warning/30">
              Pendiente
            </span>
          </div>
        </div>
        <p class="text-label-md text-text-tertiary flex-shrink-0 whitespace-nowrap">${_fechaAdmin(r.fecha_solicitud)}</p>
      </div>
      <p class="text-body-sm text-text-secondary mb-3">Usuario (ID ${r.id_propietario}) solicita reclamar este establecimiento.</p>
      
      <div class="flex flex-wrap gap-2 pt-3 border-t border-border-subtle">
        <button data-action="ver-detalles" data-tab-id="reclamos" data-idx="${idx}"
          class="flex items-center gap-1.5 px-4 py-2 rounded bg-primary text-white
                 font-semibold text-label-lg hover:opacity-90 active:scale-95 transition-all">
          <span class="material-symbols-outlined pointer-events-none" style="font-size:16px;">visibility</span> Revisar Detalles
        </button>
      </div>
    </div>`;
}

// La función _cardResena fue removida a petición del usuario

// Moderar
async function _moderar(tipo, id, accion, cardId, idSecundario = null) {
  const card = document.getElementById(cardId);
  card?.querySelectorAll('button').forEach(b => b.disabled = true);

  try {
    if (accion === 'aprobar') {
      await api.aprobar(tipo, id, idSecundario);
    } else {
      await api.rechazar(tipo, id, idSecundario);
    }

    showToast(
      accion === 'aprobar' ? 'Aprobado correctamente' : 'Rechazado',
      accion === 'aprobar' ? 'success' : 'info',
    );

    if (card) {
      card.style.transition = 'opacity 220ms ease, transform 220ms ease';
      card.style.opacity    = '0';
      card.style.transform  = 'translateX(12px)';
      setTimeout(() => {
        card.remove();
        // Si no quedan cards, mostrar estado "Todo al día"
        const body = document.getElementById('admin-body');
        if (body && !body.querySelector('[id^="estab-"],[id^="resena-"],[id^="reclamo-"]')) {
          body.innerHTML = `
            <div class="flex flex-col items-center py-16 text-center">
              <span class="material-symbols-outlined text-4xl text-success mb-3 pointer-events-none">check_circle</span>
              <p class="font-heading text-headline-sm text-primary mb-1">Todo al día</p>
              <p class="text-body-sm text-text-secondary">No hay pendientes.</p>
            </div>`;
        }
      }, 240);
    }
  } catch(e) {
    showToast('No se pudo completar la acción', 'error');
    card?.querySelectorAll('button').forEach(b => b.disabled = false);
  }
}

// Abrir modal de detalles
function _abrirModalDetalles(tabId, idx) {
  const items = _adminItemsCache[tabId] || [];
  const item = items[idx];
  if (!item) return;

  let contenido = '';
  let idPrimario = null;
  let idSecundario = null;
  let tipoAPI = tabId;

  if (tabId === 'reclamos') {
    const est = item.establecimiento || {};
    idPrimario = item.id_propietario;
    idSecundario = item.id_establecimiento;
    contenido = `
      <div class="space-y-4">
        <div><strong class="text-text-primary">ID Propietario:</strong> ${item.id_propietario}</div>
        <div><strong class="text-text-primary">Establecimiento:</strong> ${est.nombre || idSecundario}</div>
        <div><strong class="text-text-primary">Documento Prueba:</strong> ${item.documento_prueba ? `<a href="${item.documento_prueba}" target="_blank" class="text-accent underline">Ver Documento</a>` : 'No adjunto'}</div>
        <div><strong class="text-text-primary">Fecha Solicitud:</strong> ${_fechaAdmin(item.fecha_solicitud)}</div>
      </div>
    `;
  } else {
    // Es un establecimiento nuevo (visitante o propietario)
    idPrimario = item.id_establecimiento;

    contenido = `
      <div class="space-y-4 max-h-[60vh] overflow-y-auto pr-2" style="font-size: 0.95rem;">
        <h3 class="text-headline-sm text-primary font-heading border-b border-border-subtle pb-2">Información Principal</h3>
        <p><strong class="text-text-primary">Nombre:</strong> ${item.nombre}</p>
        <p><strong class="text-text-primary">Tipo:</strong> ${item.tipo_establecimiento || '—'}</p>
        <p><strong class="text-text-primary">Es Informal:</strong> ${item.es_informal ? 'Sí' : 'No'}</p>
        <p><strong class="text-text-primary">Dirección:</strong> ${item.direccion_texto || '—'}</p>
        <p><strong class="text-text-primary">Ubicación (Coordenadas):</strong> <a href="https://maps.google.com/?q=${item.latitud},${item.longitud}" target="_blank" class="text-accent underline hover:opacity-80">${item.latitud}, ${item.longitud}</a></p>
        <p><strong class="text-text-primary">Descripción:</strong> ${item.descripcion || '—'}</p>
        
        <h3 class="text-headline-sm text-primary font-heading border-b border-border-subtle pb-2 mt-6">Horarios Precisos (${item.horarios?.length || 0})</h3>
        <ul class="list-disc pl-5">
          ${(item.horarios || []).map(h => {
            const diasNombres = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
            const nombreDia = diasNombres[h.dia_semana] || `Día ${h.dia_semana}`;
            const horasTexto = (h.hora_apertura && h.hora_cierre) ? `${h.hora_apertura} - ${h.hora_cierre}` : '<span class="text-accent font-medium">Cerrado</span>';
            return `<li>${nombreDia}: ${horasTexto}</li>`;
          }).join('') || '<li class="text-text-tertiary text-sm">Sin horarios</li>'}
        </ul>
        
        <h3 class="text-headline-sm text-primary font-heading border-b border-border-subtle pb-2 mt-6">Platillos / Menú (${item.platillos?.length || 0})</h3>
        <ul class="list-disc pl-5 space-y-1">
          ${(item.platillos || []).map(p => `<li><strong>${p.nombre}</strong> ($${p.precio})<br><span class="text-text-secondary text-sm">${p.descripcion || ''}</span></li>`).join('') || '<li class="text-text-tertiary text-sm">Sin platillos</li>'}
        </ul>
      </div>
    `;
  }

  const modalHtml = `
    <div id="admin-custom-modal" class="fixed inset-0 z-50 flex items-center justify-center bg-primary/50 backdrop-blur-sm opacity-0 transition-opacity duration-300">
        <div class="bg-surface-raised p-8 rounded-md shadow-lg border-t-4 border-primary max-w-2xl w-full mx-4 transform scale-95 transition-transform duration-300 flex flex-col max-h-[90vh]">
            <h2 class="text-2xl xl:text-3xl font-heading font-bold mb-4 text-primary">Detalles de la Solicitud</h2>
            <div class="text-text-secondary mb-6 flex-1 overflow-hidden">
              ${contenido}
            </div>
            <div class="flex flex-wrap gap-4 pt-4 border-t border-border-subtle">
                <button id="admin-modal-rechazar" class="bg-surface-dim text-accent font-bold py-3 px-6 rounded border border-accent hover:bg-accent-faint transition-colors uppercase tracking-wider">
                  Rechazar
                </button>
                <div class="flex-1"></div>
                <button id="admin-modal-cerrar" class="bg-surface-dim text-text-primary font-bold py-3 px-6 rounded hover:bg-surface transition-colors uppercase tracking-wider">
                  Cerrar
                </button>
                <button id="admin-modal-aprobar" class="bg-success text-white font-bold py-3 px-6 rounded hover:opacity-90 transition-colors uppercase tracking-wider">
                  Aprobar
                </button>
            </div>
        </div>
    </div>
  `;

  document.body.insertAdjacentHTML('beforeend', modalHtml);
  const modalEl = document.getElementById('admin-custom-modal');
  const modalContent = modalEl.querySelector('div');
  
  requestAnimationFrame(() => {
      modalEl.classList.remove('opacity-0');
      modalContent.classList.remove('scale-95');
  });

  const closeModal = () => {
      modalEl.classList.add('opacity-0');
      modalContent.classList.add('scale-95');
      setTimeout(() => modalEl.remove(), 300);
  };

  document.getElementById('admin-modal-cerrar').addEventListener('click', closeModal);
  
  document.getElementById('admin-modal-rechazar').addEventListener('click', async () => {
      closeModal();
      const cardId = tabId === 'reclamos' ? `reclamo-${idPrimario}-${idSecundario}` : `estab-${idPrimario}`;
      await _moderar(tipoAPI, idPrimario, 'rechazar', cardId, idSecundario);
  });

  document.getElementById('admin-modal-aprobar').addEventListener('click', async () => {
      closeModal();
      const cardId = tabId === 'reclamos' ? `reclamo-${idPrimario}-${idSecundario}` : `estab-${idPrimario}`;
      await _moderar(tipoAPI, idPrimario, 'aprobar', cardId, idSecundario);
  });
}

// Pestaña Trabajos (Jobs)
function _renderJobs(box) {
  box.innerHTML = `
    <div class="space-y-4">
      ${_JOBS.map(job => `
        <div class="bg-surface-raised border border-border-default rounded-md p-5
                    flex flex-col md:flex-row md:items-center gap-4">
          <div class="flex items-start gap-4 flex-1 min-w-0">
            <div class="w-10 h-10 rounded bg-secondary-faint flex items-center justify-center flex-shrink-0">
              <span class="material-symbols-outlined text-secondary pointer-events-none" style="font-size:20px;">${job.icon}</span>
            </div>
            <div class="flex-1 min-w-0">
              <h3 class="font-heading text-headline-sm text-primary pointer-events-none">${job.label}</h3>
              <p class="text-body-sm text-text-secondary mt-0.5 leading-relaxed pointer-events-none">${job.desc}</p>
              <p class="text-label-md text-text-tertiary mt-1.5 flex items-center gap-1 pointer-events-none">
                <span class="material-symbols-outlined pointer-events-none" style="font-size:13px;line-height:1;">schedule</span>
                Duración aprox.: ${job.tiempo}
              </p>
            </div>
          </div>
          <div class="flex-shrink-0">
            <button id="job-${job.id}" data-action="disparar-job" data-job-id="${job.id}" data-job-label="${job.label}"
              aria-label="Ejecutar job ${job.label}"
              class="flex items-center gap-2 px-4 py-2.5 rounded bg-primary text-white
                     font-semibold text-label-lg hover:bg-primary-subtle active:scale-95 transition-all
                     disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap">
              <span class="material-symbols-outlined pointer-events-none" style="font-size:16px;">play_arrow</span>
              Ejecutar
            </button>
          </div>
        </div>`).join('')}

      <!-- Reconciliación de emergencia -->
      <div class="bg-accent-faint border border-accent/30 rounded-md p-5
                  flex flex-col md:flex-row md:items-center gap-4">
        <div class="flex items-start gap-4 flex-1 min-w-0">
          <div class="w-10 h-10 rounded bg-accent/10 flex items-center justify-center flex-shrink-0">
            <span class="material-symbols-outlined text-accent pointer-events-none" style="font-size:20px;">emergency</span>
          </div>
          <div>
            <h3 class="font-heading text-headline-sm text-accent pointer-events-none">Reconciliación de emergencia</h3>
            <p class="text-body-sm text-text-secondary mt-0.5 leading-relaxed pointer-events-none">
              Restaura consistencia en la base de datos. Usar solo si hay anomalías detectadas.
            </p>
          </div>
        </div>
        <button data-action="disparar-job" data-job-id="reconciliacion" data-job-label="Reconciliación"
          class="flex-shrink-0 flex items-center gap-2 px-4 py-2.5 rounded border border-accent text-accent
                 font-semibold text-label-lg hover:bg-accent hover:text-white active:scale-95 transition-all whitespace-nowrap">
          <span class="material-symbols-outlined pointer-events-none" style="font-size:16px;">emergency</span>
          Ejecutar
        </button>
      </div>
    </div>`;
}

async function _dispararJob(jobId, label) {
  const btn = document.getElementById(`job-${jobId}`);
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="material-symbols-outlined pointer-events-none" style="font-size:16px;animation:_admSpin 1s linear infinite;">progress_activity</span>&nbsp;Encolando...`;
  }
  try {
    const res = await api.dispararJob(jobId);
    if (res?.status === 'already_running') {
      showToast(`"${label}" ya está en ejecución`, 'warning');
    } else {
      showToast(`Job "${label}" encolado correctamente`, 'success');
    }
  } catch(_) {
    showToast(`No se pudo disparar "${label}"`, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span class="material-symbols-outlined pointer-events-none" style="font-size:16px;">play_arrow</span>&nbsp;Ejecutar`;
    }
  }
}

// Controlador Principal
export default async function adminController() {
  const loaded = await renderView('admin.html');
  if (!loaded) return;

  // Protección de acceso
  if (!appState.isAdmin) {
    document.getElementById('admin-restricted')?.classList.remove('hidden');
    document.getElementById('admin-restricted')?.classList.add('flex');
    return;
  }

  document.getElementById('admin-content')?.classList.remove('hidden');

  const tabsContainer = document.getElementById('admin-tabs');
  if (tabsContainer) {
    tabsContainer.innerHTML = _ADMIN_TABS.map(t => `
      <button id="atab-${t.id}" data-action="set-admin-tab" data-tab-id="${t.id}"
        aria-selected="${t.id === _adminTab}"
        class="flex items-center gap-2 px-4 py-3 text-label-lg transition-colors whitespace-nowrap
              ${t.id === _adminTab
                ? 'border-b-2 border-accent text-primary font-semibold'
                : 'text-text-tertiary hover:text-primary'}">
        <span class="material-symbols-outlined pointer-events-none" style="font-size:17px;">${t.icon}</span>
        ${t.label}
      </button>`).join('');
  }

  const adminBody = document.getElementById('admin-body');
  if (adminBody) adminBody.innerHTML = _skelAdmin(3);
  
  const adminContainer = document.getElementById('admin-content');
  if (adminContainer) {
    adminContainer.addEventListener('click', (e) => {
      const actionEl = e.target.closest('[data-action]');
      if (!actionEl) return;
      const action = actionEl.dataset.action;
      
      if (action === 'set-admin-tab') {
        _setAdminTab(actionEl.dataset.tabId);
      } else if (action === 'reintentar-admin') {
        _renderAdminTab(actionEl.dataset.tabId);
      } else if (action === 'moderar') {
        _moderar(actionEl.dataset.tipo, actionEl.dataset.id, actionEl.dataset.moderarAccion, actionEl.dataset.card);
      } else if (action === 'ver-detalles') {
        _abrirModalDetalles(actionEl.dataset.tabId, parseInt(actionEl.dataset.idx, 10));
      } else if (action === 'disparar-job') {
        _dispararJob(actionEl.dataset.jobId, actionEl.dataset.jobLabel);
      }
    });
  }

  setTimeout(() => _renderAdminTab(_adminTab), 150);
}
