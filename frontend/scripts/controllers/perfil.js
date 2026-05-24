/**
 * perfil.js — Perfil de usuario, gamificación y flujo de agregar lugar
 * EkiSystem — Fase 4 Frontend
 */

// Configuración de rangos 
const _RANGOS = [
  { nombre:'Explorador',     min:0,    max:99,         icon:'explore',             color:'#7E756F' },
  { nombre:'Catador',        min:100,  max:299,        icon:'restaurant',          color:'#4A6F8A' },
  { nombre:'Conocedor',      min:300,  max:699,        icon:'star',                color:'#8A6020' },
  { nombre:'Gourmet',        min:700,  max:1499,       icon:'workspace_premium',   color:'#3A6B4A' },
  { nombre:'Embajador EKI',  min:1500, max:Infinity,   icon:'verified',            color:'#8B3A3A' },
];

function _getRango(pts) {
  return _RANGOS.find(r => pts >= r.min && pts <= r.max) || _RANGOS[0];
}
function _getRangoSig(pts) {
  const i = _RANGOS.findIndex(r => pts >= r.min && pts <= r.max);
  return i < _RANGOS.length - 1 ? _RANGOS[i + 1] : null;
}
function _getPct(pts) {
  const r = _getRango(pts);
  if (r.max === Infinity) return 100;
  return Math.min(100, Math.round(((pts - r.min) / (r.max - r.min + 1)) * 100));
}

// Helpers 
function _iniciales(nombre, apellido) {
  return ((nombre||'')[0] + (apellido||'')[0]).toUpperCase() || 'U';
}
function _fechaCorta(str) {
  if (!str) return '';
  return new Date(str).toLocaleDateString('es-MX', { year:'numeric', month:'long', day:'numeric' });
}
function _historialIcon(motivo) {
  const m = (motivo||'').toLowerCase();
  if (m.includes('reseña'))           return 'rate_review';
  if (m.includes('lugar') || m.includes('establecimiento')) return 'storefront';
  if (m.includes('foto'))             return 'photo_camera';
  if (m.includes('edici'))            return 'edit';
  if (m.includes('bienvenida') || m.includes('registro')) return 'celebration';
  return 'add_circle';
}

// Animación odómetro 
function _odometro(el, destino, ms) {
  const start = performance.now();
  const tick = (now) => {
    const p = Math.min((now - start) / ms, 1);
    const ease = 1 - Math.pow(1 - p, 4); // ease-out quart
    el.textContent = Math.round(ease * destino).toLocaleString('es-MX');
    if (p < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

// Skeleton 
function _skel() {
  return `
    <div class="w-full max-w-4xl mx-auto px-4 md:px-8 py-10">
      <div class="flex items-center gap-5 mb-10">
        <div class="skeleton w-20 h-20 rounded-full flex-shrink-0"></div>
        <div class="space-y-2"><div class="skeleton h-8 w-48 rounded"></div><div class="skeleton h-4 w-32 rounded"></div></div>
      </div>
      <div class="skeleton h-40 rounded-md mb-6"></div>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        ${Array.from({length:4},()=>`<div class="skeleton h-24 rounded-md"></div>`).join('')}
      </div>
      <div class="skeleton h-64 rounded-md"></div>
    </div>`;
}

// Modal helpers
function _abrirModal(id)  { const m = document.getElementById(id); m?.classList.remove('hidden'); m?.classList.add('flex'); }
function _cerrarModal(id) { const m = document.getElementById(id); m?.classList.add('hidden');    m?.classList.remove('flex'); }

// Modal: Editar perfil 
function _abrirEdicion(nombre, apellido) {
  document.getElementById('edit-nombre').value   = nombre  || '';
  document.getElementById('edit-apellido').value = apellido|| '';
  _abrirModal('modal-edicion');
}

async function _guardarPerfil() {
  const btn      = document.getElementById('btn-guardar-perfil');
  const nombre   = document.getElementById('edit-nombre')?.value?.trim();
  const apellido = document.getElementById('edit-apellido')?.value?.trim();
  if (!nombre) { showToast('El nombre es requerido', 'warning'); return; }
  btn.disabled = true;
  btn.innerHTML = `<span class="material-symbols-outlined" style="font-size:16px;animation:spin 1s linear infinite;">progress_activity</span>&nbsp;Guardando...`;
  try {
    await api.actualizarPerfil({ nombre, apellido });
    showToast('Perfil actualizado', 'success');
    _cerrarModal('modal-edicion');
    window.controllers.perfil();
  } catch(_) {
    showToast('No se pudo actualizar el perfil', 'error');
    btn.disabled = false;
    btn.innerHTML = 'Guardar cambios';
  }
}

// Modal: Agregar lugar
function _abrirAgregarLugar() { _abrirModal('modal-lugar'); }
function _cerrarAgregarLugar(){ _cerrarModal('modal-lugar'); }

async function _enviarLugar() {
  const btn = document.getElementById('btn-enviar-lugar');
  const nombre      = document.getElementById('lugar-nombre')?.value?.trim();
  const tipo        = document.getElementById('lugar-tipo')?.value;
  const descripcion = document.getElementById('lugar-desc')?.value?.trim();
  const direccion   = document.getElementById('lugar-dir')?.value?.trim();
  const es_informal = document.getElementById('lugar-informal')?.checked;

  if (!nombre || !tipo) { showToast('Nombre y tipo son requeridos', 'warning'); return; }

  btn.disabled = true;
  btn.innerHTML = `<span class="material-symbols-outlined" style="font-size:16px;animation:spin 1s linear infinite;">progress_activity</span>&nbsp;Enviando...`;

  try {
    await apiRequest('/establecimientos', {
      method: 'POST',
      body: JSON.stringify({ nombre, tipo_establecimiento: tipo, descripcion, direccion_texto: direccion, es_informal }),
    });
    showToast('¡Lugar enviado! Será revisado por el equipo.', 'success');
    _cerrarAgregarLugar();
    // Reset form
    ['lugar-nombre','lugar-desc','lugar-dir'].forEach(id => {
      const el = document.getElementById(id); if (el) el.value = '';
    });
    document.getElementById('lugar-informal').checked = false;
    document.getElementById('lugar-tipo').value = '';
  } catch(_) {
    showToast('No se pudo enviar el lugar. Intenta de nuevo.', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = 'Enviar para revisión';
  }
}

// Controlador principal 
window.controllers.perfil = async () => {
  renderPage(_skel());

  let usuario, rango_data, historial;
  try {
    [usuario, rango_data, historial] = await Promise.all([
      api.getPerfil(),
      api.getRango().catch(() => null),
      api.getHistorialPuntos().catch(() => []),
    ]);
  } catch(_) {
    renderPage(`
      <div class="flex flex-col items-center justify-center py-32 text-center px-4">
        <span class="material-symbols-outlined text-5xl text-text-tertiary mb-4">person_off</span>
        <h2 class="font-heading text-headline-lg text-primary mb-2">No se pudo cargar el perfil</h2>
        <button onclick="window.controllers.perfil()"
          class="bg-accent text-white px-5 py-2 rounded font-semibold hover:bg-accent-hover transition-colors mt-4">
          Reintentar
        </button>
      </div>`);
    return;
  }

  const puntos    = rango_data?.puntos_totales ?? usuario?.puntos_totales ?? 0;
  const rango     = _getRango(puntos);
  const rangoSig  = _getRangoSig(puntos);
  const pct       = _getPct(puntos);
  const iniciales = _iniciales(usuario.nombre, usuario.apellido);
  const esProp    = usuario.tipo_usuario === 'propietario';
  const tipoLabel = { visitante:'Visitante', propietario:'Propietario', admin:'Administrador' }[usuario.tipo_usuario] || 'Usuario';
  const histItems = Array.isArray(historial) ? historial : (historial?.items || []);

  const stats = [
    { label:'Reseñas',         val: usuario.total_resenas        ?? 0, icon:'rate_review',   numerico:true  },
    { label:'Favoritos',       val: usuario.total_favoritos       ?? 0, icon:'favorite',      numerico:true  },
    { label:'Contribuciones',  val: usuario.total_contribuciones  ?? 0, icon:'storefront',    numerico:true  },
    { label:'Miembro desde',   val: _fechaCorta(usuario.fecha_registro), icon:'calendar_month', numerico:false },
  ];

  renderPage(`
    <div class="w-full max-w-4xl mx-auto px-4 md:px-8 py-10 fade-in">

      <!-- ── Header ── -->
      <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-5 mb-10">
        <div class="flex items-center gap-5">
          <!-- Avatar -->
          <div class="w-20 h-20 rounded-full bg-primary flex items-center justify-center
                      font-heading text-2xl font-bold text-white flex-shrink-0 select-none"
               aria-label="Avatar de ${usuario.nombre || 'usuario'}">
            ${iniciales}
          </div>
          <div>
            <h1 class="font-heading text-display-md text-primary leading-tight">
              ${usuario.nombre || ''} ${usuario.apellido || ''}
            </h1>
            <p class="text-body-sm text-text-secondary mt-0.5">${usuario.email || ''}</p>
            <span class="inline-block mt-1.5 text-label-sm px-2 py-0.5 rounded bg-surface-dim
                         text-text-tertiary border border-border-default">${tipoLabel}</span>
          </div>
        </div>

        <!-- Acciones -->
        <div class="flex flex-wrap gap-2 sm:flex-nowrap sm:flex-col sm:items-end">
          <button
            onclick="_abrirEdicion('${(usuario.nombre||'').replace(/'/g,"\\'")}','${(usuario.apellido||'').replace(/'/g,"\\'")}')"
            aria-label="Editar perfil"
            class="flex items-center gap-1.5 px-3 py-2 rounded border border-border-default
                   text-body-sm text-text-secondary hover:border-border-strong hover:text-primary transition-all">
            <span class="material-symbols-outlined" style="font-size:16px;">edit</span> Editar perfil
          </button>
          <a href="#/onboarding"
            class="flex items-center gap-1.5 px-3 py-2 rounded border border-border-default
                   text-body-sm text-text-secondary hover:border-secondary hover:text-secondary transition-all">
            <span class="material-symbols-outlined" style="font-size:16px;">tune</span> Mis preferencias
          </a>
          ${esProp ? `
          <button onclick="_abrirAgregarLugar()"
            class="flex items-center gap-1.5 px-3 py-2 rounded border border-accent-muted
                   text-body-sm text-accent hover:bg-accent-faint transition-all">
            <span class="material-symbols-outlined" style="font-size:16px;">add_location_alt</span> Agregar lugar
          </button>` : ''}
        </div>
      </div>

      <!-- ── Tarjeta de rango ── -->
      <div class="bg-surface-raised border border-border-default rounded-md p-6 mb-6">
        <div class="flex items-start justify-between gap-4 mb-5">
          <div>
            <p class="text-label-md text-text-tertiary uppercase tracking-wide mb-2">Tu rango actual</p>
            <div class="flex items-center gap-3">
              <span class="material-symbols-outlined" style="font-size:32px;color:${rango.color};">${rango.icon}</span>
              <span class="font-heading text-headline-lg text-primary">${rango.nombre}</span>
            </div>
          </div>
          <div class="text-right">
            <p class="text-label-md text-text-tertiary mb-1">Puntos totales</p>
            <p id="pts-odometro" class="font-heading text-numeric-lg tabular-nums" style="color:${rango.color};">0</p>
          </div>
        </div>

        <!-- Barra de progreso -->
        ${rangoSig ? `
          <div>
            <div class="flex justify-between items-center mb-2">
              <span class="text-label-md text-text-tertiary">
                Hacia <strong style="color:${_getRangoSig(puntos)?.color};">${rangoSig.nombre}</strong>
              </span>
              <span class="text-label-md text-secondary tabular-nums">${puntos.toLocaleString('es-MX')} / ${rangoSig.min.toLocaleString('es-MX')} pts</span>
            </div>
            <div class="progress-track">
              <div class="progress-fill" style="width:${pct}%;background-color:${rango.color};"></div>
            </div>
            <p class="text-label-md text-text-tertiary mt-1.5">
              Te faltan <strong>${(rangoSig.min - puntos).toLocaleString('es-MX')} puntos</strong> para subir de rango.
            </p>
          </div>` : `
          <div class="bg-accent-faint border border-accent/20 rounded p-3 flex items-center gap-2">
            <span class="material-symbols-outlined text-accent" style="font-size:18px;">verified</span>
            <p class="text-body-sm text-accent font-semibold">¡Has alcanzado el rango máximo!</p>
          </div>`}
      </div>

      <!-- ── Estadísticas ── -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        ${stats.map(s => `
          <div class="bg-surface-raised border border-border-default rounded-md p-4 text-center">
            <span class="material-symbols-outlined text-text-tertiary mb-2 block" style="font-size:22px;">${s.icon}</span>
            ${s.numerico
              ? `<p class="font-heading text-numeric-md text-primary tabular-nums">${(s.val||0).toLocaleString('es-MX')}</p>`
              : `<p class="text-body-sm text-primary font-semibold leading-snug">${s.val}</p>`}
            <p class="text-label-md text-text-tertiary mt-0.5">${s.label}</p>
          </div>`).join('')}
      </div>

      <!-- ── Historial de puntos ── -->
      <div class="bg-surface-raised border border-border-default rounded-md p-6">
        <h2 class="font-heading text-headline-md text-primary mb-4">Historial de puntos</h2>
        ${histItems.length ? `
          <div aria-label="Historial de actividad">
            ${histItems.slice(0, 20).map((h, i) => {
              const pts = h.puntos_ganados ?? h.puntos ?? 0;
              const pos = pts >= 0;
              return `
                <div class="flex items-center gap-4 py-3 border-b border-border-subtle last:border-0 card-enter"
                     style="animation-delay:${i*35}ms">
                  <div class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
                              ${pos ? 'bg-[#EBF4ED] text-[var(--success)]' : 'bg-accent-faint text-accent'}">
                    <span class="material-symbols-outlined" style="font-size:15px;">${_historialIcon(h.motivo)}</span>
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="text-body-sm font-medium text-primary truncate">${h.motivo || 'Actividad'}</p>
                    <p class="text-label-md text-text-tertiary">${_fechaCorta(h.fecha)}</p>
                  </div>
                  <span class="text-numeric-sm font-bold flex-shrink-0 ${pos ? 'text-[var(--success)]' : 'text-accent'}">
                    ${pos ? '+' : ''}${pts} pts
                  </span>
                </div>`;
            }).join('')}
          </div>` : `
          <div class="flex flex-col items-center py-12 text-center">
            <span class="material-symbols-outlined text-4xl text-text-tertiary mb-3">history</span>
            <p class="text-body-sm text-text-tertiary">Aún no tienes actividad registrada.</p>
            <p class="text-label-md text-text-tertiary mt-1">Deja reseñas o agrega lugares para ganar puntos.</p>
          </div>`}
      </div>

    </div>

    <!-- ── Modal: Editar perfil ── -->
    <div id="modal-edicion" class="hidden fixed inset-0 z-50 items-center justify-center p-4"
         style="background:rgba(30,27,24,0.5);"
         onclick="if(event.target===this)_cerrarModal('modal-edicion')"
         role="dialog" aria-modal="true" aria-labelledby="modal-edicion-titulo">
      <div class="bg-surface-raised border border-border-default rounded-md p-6 w-full max-w-md shadow-xl">
        <div class="flex items-center justify-between mb-5">
          <h3 id="modal-edicion-titulo" class="font-heading text-headline-sm text-primary">Editar perfil</h3>
          <button onclick="_cerrarModal('modal-edicion')" aria-label="Cerrar modal"
            class="text-text-tertiary hover:text-primary transition-colors">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        <div class="space-y-4">
          <div>
            <label for="edit-nombre" class="block text-label-md text-text-secondary uppercase tracking-wide mb-1">Nombre *</label>
            <input id="edit-nombre" type="text" autocomplete="given-name"
              class="w-full bg-surface-dim border border-border-default rounded p-2.5 text-body-sm text-text-primary
                     focus:outline-none focus:border-border-focus focus:ring-2 focus:ring-[var(--border-focus)]/20 transition-colors" />
          </div>
          <div>
            <label for="edit-apellido" class="block text-label-md text-text-secondary uppercase tracking-wide mb-1">Apellido</label>
            <input id="edit-apellido" type="text" autocomplete="family-name"
              class="w-full bg-surface-dim border border-border-default rounded p-2.5 text-body-sm text-text-primary
                     focus:outline-none focus:border-border-focus focus:ring-2 focus:ring-[var(--border-focus)]/20 transition-colors" />
          </div>
        </div>
        <div class="flex gap-3 mt-6 justify-end">
          <button onclick="_cerrarModal('modal-edicion')"
            class="px-4 py-2 rounded border border-border-default text-body-sm text-text-secondary hover:border-border-strong transition-colors">
            Cancelar
          </button>
          <button id="btn-guardar-perfil" onclick="_guardarPerfil()"
            class="flex items-center gap-2 px-5 py-2 rounded bg-accent text-white font-semibold text-label-lg
                   hover:bg-accent-hover active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed">
            Guardar cambios
          </button>
        </div>
      </div>
    </div>

    <!-- ── Modal: Agregar lugar ── -->
    <div id="modal-lugar" class="hidden fixed inset-0 z-50 items-center justify-center p-4"
         style="background:rgba(30,27,24,0.5);"
         onclick="if(event.target===this)_cerrarAgregarLugar()"
         role="dialog" aria-modal="true" aria-labelledby="modal-lugar-titulo">
      <div class="bg-surface-raised border border-border-default rounded-md p-6 w-full max-w-lg shadow-xl max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-5">
          <h3 id="modal-lugar-titulo" class="font-heading text-headline-sm text-primary">Agregar un lugar</h3>
          <button onclick="_cerrarAgregarLugar()" aria-label="Cerrar modal"
            class="text-text-tertiary hover:text-primary transition-colors">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>

        <p class="text-body-sm text-text-secondary mb-5 leading-relaxed">
          Tu propuesta será revisada por el equipo antes de publicarse. Una vez aprobada ganará puntos y aparecerá en el feed.
        </p>

        <div class="space-y-4">
          <div>
            <label for="lugar-nombre" class="block text-label-md text-text-secondary uppercase tracking-wide mb-1">Nombre del lugar *</label>
            <input id="lugar-nombre" type="text" placeholder="Ej: Tacos El Caminante"
              class="w-full bg-surface-dim border border-border-default rounded p-2.5 text-body-sm text-text-primary
                     placeholder:text-text-tertiary focus:outline-none focus:border-border-focus focus:ring-2 focus:ring-[var(--border-focus)]/20 transition-colors" />
          </div>
          <div>
            <label for="lugar-tipo" class="block text-label-md text-text-secondary uppercase tracking-wide mb-1">Tipo *</label>
            <select id="lugar-tipo"
              class="w-full bg-surface-dim border border-border-default rounded p-2.5 text-body-sm text-text-primary
                     focus:outline-none focus:border-border-focus focus:ring-2 focus:ring-[var(--border-focus)]/20 transition-colors">
              <option value="">Selecciona el tipo...</option>
              <option value="puesto_informal">Puesto informal</option>
              <option value="restaurante">Restaurante</option>
              <option value="local_comercial">Local comercial</option>
            </select>
          </div>
          <div>
            <label for="lugar-desc" class="block text-label-md text-text-secondary uppercase tracking-wide mb-1">Descripción</label>
            <textarea id="lugar-desc" placeholder="¿Qué lo hace especial?" rows="3"
              class="w-full bg-surface-dim border border-border-default rounded p-2.5 text-body-sm text-text-primary
                     placeholder:text-text-tertiary resize-none
                     focus:outline-none focus:border-border-focus focus:ring-2 focus:ring-[var(--border-focus)]/20 transition-colors"></textarea>
          </div>
          <div>
            <label for="lugar-dir" class="block text-label-md text-text-secondary uppercase tracking-wide mb-1">Dirección</label>
            <input id="lugar-dir" type="text" placeholder="Calle, colonia, referencias..."
              class="w-full bg-surface-dim border border-border-default rounded p-2.5 text-body-sm text-text-primary
                     placeholder:text-text-tertiary focus:outline-none focus:border-border-focus focus:ring-2 focus:ring-[var(--border-focus)]/20 transition-colors" />
          </div>
          <label class="flex items-center gap-3 cursor-pointer select-none">
            <input id="lugar-informal" type="checkbox"
              class="w-4 h-4 rounded border-border-default accent-accent" />
            <span class="text-body-sm text-text-secondary">Es un puesto o negocio informal</span>
          </label>
        </div>

        <div class="flex gap-3 mt-6 justify-end">
          <button onclick="_cerrarAgregarLugar()"
            class="px-4 py-2 rounded border border-border-default text-body-sm text-text-secondary hover:border-border-strong transition-colors">
            Cancelar
          </button>
          <button id="btn-enviar-lugar" onclick="_enviarLugar()"
            class="flex items-center gap-2 px-5 py-2 rounded bg-accent text-white font-semibold text-label-lg
                   hover:bg-accent-hover active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed">
            Enviar para revisión
          </button>
        </div>
      </div>
    </div>

    <style>
      @keyframes spin { to { transform: rotate(360deg); } }
    </style>
  `);

  // Animar odómetro después del render
  setTimeout(() => {
    const el = document.getElementById('pts-odometro');
    if (el) _odometro(el, puntos, 1400);
  }, 180);
};
