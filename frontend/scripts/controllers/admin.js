/**
 * admin.js — Panel de Administración
 * EkiSystem — Fase 5 Frontend
 * Solo accesible para tipo_usuario === 'admin'
 */

const _ADMIN_TABS = [
  { id:'establecimientos', label:'Establecimientos', icon:'storefront'  },
  { id:'jobs',             label:'Jobs offline',      icon:'settings'     },
];
let _adminTab = 'establecimientos';

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
    // Reiniciar estilos
    btn.classList.remove('border-b-2','border-accent','text-primary','font-semibold','text-text-tertiary');
    if (t.id === id) {
      btn.classList.add('border-b-2','border-accent','text-primary','font-semibold');
    } else {
      btn.classList.add('text-text-tertiary');
    }
  });
  _renderAdminTab(id);
}

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
          <span class="material-symbols-outlined text-4xl text-[var(--success)] mb-3">check_circle</span>
          <p class="font-heading text-headline-sm text-primary mb-1">Todo al día</p>
          <p class="text-body-sm text-text-secondary">
            No hay ${id === 'establecimientos' ? 'establecimientos' : 'reseñas'} pendientes de revisión.
          </p>
        </div>`;
      return;
    }

    box.innerHTML = `
      <p class="text-label-md text-text-tertiary mb-4">${items.length} pendiente${items.length!==1?'s':''}</p>
      <div class="space-y-4">
        ${items.map((item, i) =>
          id === 'establecimientos'
            ? _cardEstab(item, i)
            : _cardResena(item, i)
        ).join('')}
      </div>`;

  } catch(_) {
    box.innerHTML = `
      <div class="flex flex-col items-center py-12 text-center">
        <span class="material-symbols-outlined text-4xl text-text-tertiary mb-3">wifi_off</span>
        <p class="text-body-sm text-text-secondary mb-4">No se pudieron cargar los pendientes.</p>
        <button onclick="_renderAdminTab('${id}')"
          class="bg-accent text-white px-4 py-2 rounded font-semibold hover:bg-accent-hover transition-colors">
          Reintentar
        </button>
      </div>`;
  }
}

// Tarjeta: establecimiento pendiente
function _cardEstab(e, idx) {
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
            <span class="text-label-sm px-2 py-0.5 rounded bg-warning-faint text-[var(--warning)] border border-[var(--warning)]/30">
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
             <span class="material-symbols-outlined" style="font-size:15px;">location_on</span>
             ${e.direccion_texto}
           </p>`
        : ''}

      <div class="flex flex-wrap gap-2 pt-3 border-t border-border-subtle">
        <button onclick="_moderar('establecimientos',${id},'aprobar','estab-${id}')"
          class="flex items-center gap-1.5 px-4 py-2 rounded bg-[var(--success)] text-white
                 font-semibold text-label-lg hover:opacity-90 active:scale-95 transition-all">
          <span class="material-symbols-outlined" style="font-size:16px;">check</span> Aprobar
        </button>
        <button onclick="_moderar('establecimientos',${id},'rechazar','estab-${id}')"
          class="flex items-center gap-1.5 px-4 py-2 rounded border border-accent text-accent
                 font-semibold text-label-lg hover:bg-accent-faint active:scale-95 transition-all">
          <span class="material-symbols-outlined" style="font-size:16px;">close</span> Rechazar
        </button>
        ${e.latitud && e.longitud
          ? `<a href="https://www.google.com/maps?q=${e.latitud},${e.longitud}" target="_blank" rel="noopener"
               class="flex items-center gap-1 px-3 py-2 rounded border border-border-default text-text-secondary
                      text-label-lg hover:border-border-strong transition-all">
               <span class="material-symbols-outlined" style="font-size:15px;">map</span> Ubicación
             </a>`
          : ''}
      </div>
    </div>`;
}

// Tarjeta: reseña pendiente
function _cardResena(r, idx) {
  const id  = r.id_resena;
  const cal = r.calificacion || 0;
  const inicial = (r.nombre_usuario||'?')[0].toUpperCase();

  return `
    <div id="resena-${id}"
         class="bg-surface-raised border border-border-default rounded-md p-5 card-enter"
         style="animation-delay:${idx*60}ms">
      <div class="flex items-start justify-between gap-4 mb-3">
        <div>
          <h3 class="font-heading text-headline-sm text-primary">
            ${r.nombre_establecimiento || `Establecimiento #${r.id_establecimiento}`}
          </h3>
          <div class="flex items-center gap-2 mt-1.5 flex-wrap">
            <span class="text-warning-subtle" style="font-size:1rem;">${'★'.repeat(cal)}${'☆'.repeat(5-cal)}</span>
            <span class="text-label-sm px-2 py-0.5 rounded bg-warning-faint text-[var(--warning)] border border-[var(--warning)]/30">
              Pendiente
            </span>
          </div>
        </div>
        <p class="text-label-md text-text-tertiary flex-shrink-0 whitespace-nowrap">${_fechaAdmin(r.fecha_resena)}</p>
      </div>

      <div class="flex items-center gap-2 mb-3">
        <div class="w-7 h-7 rounded-full bg-primary-faint flex items-center justify-center
                    text-primary-ghost font-bold text-xs flex-shrink-0">
          ${inicial}
        </div>
        <span class="text-body-sm text-text-secondary">${r.nombre_usuario || 'Usuario anónimo'}</span>
      </div>

      ${r.comentario
        ? `<div class="bg-surface-dim rounded p-3 mb-3">
             <p class="text-body-sm text-text-secondary italic leading-relaxed">"${r.comentario}"</p>
           </div>`
        : `<p class="text-body-sm text-text-tertiary italic mb-3">Sin comentario escrito.</p>`}

      <div class="flex gap-2 pt-3 border-t border-border-subtle">
        <button onclick="_moderar('resenas',${id},'aprobar','resena-${id}')"
          class="flex items-center gap-1.5 px-4 py-2 rounded bg-[var(--success)] text-white
                 font-semibold text-label-lg hover:opacity-90 active:scale-95 transition-all">
          <span class="material-symbols-outlined" style="font-size:16px;">check</span> Aprobar
        </button>
        <button onclick="_moderar('resenas',${id},'rechazar','resena-${id}')"
          class="flex items-center gap-1.5 px-4 py-2 rounded border border-accent text-accent
                 font-semibold text-label-lg hover:bg-accent-faint active:scale-95 transition-all">
          <span class="material-symbols-outlined" style="font-size:16px;">close</span> Rechazar
        </button>
      </div>
    </div>`;
}

// Moderar
async function _moderar(tipo, id, accion, cardId) {
  const card = document.getElementById(cardId);
  card?.querySelectorAll('button').forEach(b => b.disabled = true);

  try {
    if (accion === 'aprobar') {
      await api.aprobar(tipo, id);
    } else {
      await apiRequest(`/admin/${tipo}/${id}/rechazar`, { method:'POST' });
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
        if (body && !body.querySelector('[id^="estab-"],[id^="resena-"]')) {
          const tabLabel = tipo === 'establecimientos' ? 'establecimientos' : 'reseñas';
          body.innerHTML = `
            <div class="flex flex-col items-center py-16 text-center">
              <span class="material-symbols-outlined text-4xl text-[var(--success)] mb-3">check_circle</span>
              <p class="font-heading text-headline-sm text-primary mb-1">Todo al día</p>
              <p class="text-body-sm text-text-secondary">No hay ${tabLabel} pendientes.</p>
            </div>`;
        }
      }, 240);
    }
  } catch(e) {
    showToast('No se pudo completar la acción', 'error');
    card?.querySelectorAll('button').forEach(b => b.disabled = false);
  }
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
              <span class="material-symbols-outlined text-secondary" style="font-size:20px;">${job.icon}</span>
            </div>
            <div class="flex-1 min-w-0">
              <h3 class="font-heading text-headline-sm text-primary">${job.label}</h3>
              <p class="text-body-sm text-text-secondary mt-0.5 leading-relaxed">${job.desc}</p>
              <p class="text-label-md text-text-tertiary mt-1.5 flex items-center gap-1">
                <span class="material-symbols-outlined" style="font-size:13px;line-height:1;">schedule</span>
                Duración aprox.: ${job.tiempo}
              </p>
            </div>
          </div>
          <div class="flex-shrink-0">
            <button id="job-${job.id}" onclick="_dispararJob('${job.id}','${job.label}')"
              aria-label="Ejecutar job ${job.label}"
              class="flex items-center gap-2 px-4 py-2.5 rounded bg-primary text-white
                     font-semibold text-label-lg hover:bg-primary-subtle active:scale-95 transition-all
                     disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap">
              <span class="material-symbols-outlined" style="font-size:16px;">play_arrow</span>
              Ejecutar
            </button>
          </div>
        </div>`).join('')}

      <!-- Reconciliación de emergencia -->
      <div class="bg-accent-faint border border-accent/30 rounded-md p-5
                  flex flex-col md:flex-row md:items-center gap-4">
        <div class="flex items-start gap-4 flex-1 min-w-0">
          <div class="w-10 h-10 rounded bg-accent/10 flex items-center justify-center flex-shrink-0">
            <span class="material-symbols-outlined text-accent" style="font-size:20px;">emergency</span>
          </div>
          <div>
            <h3 class="font-heading text-headline-sm text-accent">Reconciliación de emergencia</h3>
            <p class="text-body-sm text-text-secondary mt-0.5 leading-relaxed">
              Restaura consistencia en la base de datos. Usar solo si hay anomalías detectadas.
            </p>
          </div>
        </div>
        <button onclick="_dispararJob('reconciliacion','Reconciliación')"
          class="flex-shrink-0 flex items-center gap-2 px-4 py-2.5 rounded border border-accent text-accent
                 font-semibold text-label-lg hover:bg-accent hover:text-white active:scale-95 transition-all whitespace-nowrap">
          <span class="material-symbols-outlined" style="font-size:16px;">emergency</span>
          Ejecutar
        </button>
      </div>
    </div>`;
}

async function _dispararJob(jobId, label) {
  const btn = document.getElementById(`job-${jobId}`);
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="material-symbols-outlined" style="font-size:16px;animation:_admSpin 1s linear infinite;">progress_activity</span>&nbsp;Encolando...`;
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
      btn.innerHTML = `<span class="material-symbols-outlined" style="font-size:16px;">play_arrow</span>&nbsp;Ejecutar`;
    }
  }
}

// Controlador Principal
window.controllers.admin = async () => {
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
      <button id="atab-${t.id}" onclick="_setAdminTab('${t.id}')"
        aria-selected="${t.id === _adminTab}"
        class="flex items-center gap-2 px-4 py-3 text-label-lg transition-colors whitespace-nowrap
              ${t.id === _adminTab
                ? 'border-b-2 border-accent text-primary font-semibold'
                : 'text-text-tertiary hover:text-primary'}">
        <span class="material-symbols-outlined" style="font-size:17px;">${t.icon}</span>
        ${t.label}
      </button>`).join('');
  }

  const adminBody = document.getElementById('admin-body');
  if (adminBody) adminBody.innerHTML = _skelAdmin(3);

  setTimeout(() => _renderAdminTab(_adminTab), 150);
};
