/**
 * perfil.js — Perfil de usuario, gamificación y flujo de agregar lugar
 * EkiSystem — Fase 4 Frontend
 */
import { api, apiRequest } from '../api.js';
import { showToast } from '../utils.js';
import { renderView } from '../app.js';
import { appState } from '../state.js';

// Configuración de rangos 
const _RANGOS = [
  { nombre:'Explorador',     min:0,    max:99,         icon:'explore',             color:'rgb(var(--primary-ghost))' },
  { nombre:'Catador',        min:100,  max:299,        icon:'restaurant',          color:'rgb(var(--secondary))' },
  { nombre:'Conocedor',      min:300,  max:699,        icon:'star',                color:'rgb(var(--warning))' },
  { nombre:'Gourmet',        min:700,  max:1499,       icon:'workspace_premium',   color:'rgb(var(--success))' },
  { nombre:'Embajador EKI',  min:1500, max:Infinity,   icon:'verified',            color:'rgb(var(--accent))' },
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

// Utilidades
function _iniciales(nombre, apellido) {
  return ((nombre||'')[0] + (apellido||'')[0]).toUpperCase() || 'U';
}
function _fechaCorta(str) {
  if (!str) return '';
  return new Date(str).toLocaleDateString('es-MX', { year:'numeric', month:'long', day:'numeric' });
}
function _historialIcon(motivo) {
  const m = (motivo||'').toLowerCase();
  if (m.includes('reseña') || m.includes('resena')) return 'rate_review';
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
    const ease = 1 - Math.pow(1 - p, 4);
    el.textContent = Math.round(ease * destino).toLocaleString('es-MX');
    if (p < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

// El esqueleto será cargado desde la vista.

// Utilidades de modal
function _abrirModal(id)  { const m = document.getElementById(id); m?.classList.remove('hidden'); m?.classList.add('flex'); }
function _cerrarModal(id) { const m = document.getElementById(id); m?.classList.add('hidden');    m?.classList.remove('flex'); }

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

  // Evitar update innecesario si no hubo cambios reales
  if (appState.user && appState.user.nombre === nombre && (appState.user.apellido || '') === apellido) {
    showToast('No se detectaron cambios en tu perfil', 'warning');
    _cerrarModal('modal-edicion');
    return;
  }

  btn.disabled = true;
  btn.innerHTML = `<div class="flex items-center justify-center gap-2"><span class="material-symbols-outlined animate-spin pointer-events-none" style="font-size:18px;">progress_activity</span> Guardando...</div>`;
  try {
    await api.actualizarPerfil({ nombre, apellido });
    showToast('Perfil actualizado', 'success');
    _cerrarModal('modal-edicion');
    perfilController();
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
  btn.innerHTML = `<div class="flex items-center justify-center gap-2"><span class="material-symbols-outlined animate-spin pointer-events-none" style="font-size:16px;">progress_activity</span> Enviando...</div>`;

  try {
    await apiRequest('/establecimientos', {
      method: 'POST',
      body: JSON.stringify({ nombre, tipo_establecimiento: tipo, descripcion, direccion_texto: direccion, es_informal }),
    });
    showToast('¡Lugar enviado! Será revisado por el equipo.', 'success');
    _cerrarAgregarLugar();
    // Limpiar formulario
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
export default async function perfilController() {
  const loaded = await renderView('perfil.html');
  if (!loaded) return;

  // Delegación de eventos para la vista completa
  const root = document.getElementById('app-root');
  const _handlePerfilClick = (e) => {
    const actionEl = e.target.closest('[data-action]');
    if (!actionEl) return;
    const action = actionEl.dataset.action;
    
    if (action === 'reload-perfil') {
      perfilController();
    } else if (action === 'abrir-agregar-lugar') {
      _abrirAgregarLugar();
    } else if (action === 'cerrar-modal') {
      _cerrarModal(actionEl.dataset.target);
    } else if (action === 'cerrar-modal-backdrop') {
      if (e.target === actionEl) _cerrarModal(actionEl.dataset.target);
    } else if (action === 'guardar-perfil') {
      _guardarPerfil();
    } else if (action === 'enviar-lugar') {
      _enviarLugar();
    } else if (action === 'abrir-historial') {
      _abrirModal('modal-historial');
      _renderHistorialModal(0);
    } else if (action === 'cargar-mas-contribuciones') {
      window._contribPage = (window._contribPage || 1) + 1;
      _renderContribuciones();
    } else if (action === 'eliminar-contribucion') {
      const id = actionEl.dataset.id;
      _eliminarContribucion(id);
    } else if (action === 'editar-contribucion') {
      const id = actionEl.dataset.id;
      window.location.hash = `#/contribucion?id=${id}`;
    }
  };
  
  // Limpiar eventos anteriores si se vuelve a renderizar
  if (window._perfilClickListener) {
    root.removeEventListener('click', window._perfilClickListener);
  }
  window._perfilClickListener = _handlePerfilClick;
  root.addEventListener('click', window._perfilClickListener);

  let usuario, rango_data, historial, contribuciones;
  try {
    [usuario, rango_data, historial, contribuciones] = await Promise.all([
      api.getPerfil(),
      api.getRango().catch(() => null),
      api.getHistorialPuntos().catch(() => []),
      api.getMisContribuciones().catch(() => []),
    ]);
  } catch(_) {
    document.getElementById('perfil-skeleton')?.classList.add('hidden');
    document.getElementById('perfil-error')?.classList.remove('hidden');
    document.getElementById('perfil-error')?.classList.add('flex');
    
    const reintentarBtn = document.getElementById('perfil-error')?.querySelector('button');
    if (reintentarBtn) {
      reintentarBtn.addEventListener('click', perfilController);
    }
    return;
  }

  appState.setUser(usuario);

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

  // Ocultar esqueleto, mostrar contenido
  document.getElementById('perfil-skeleton')?.classList.add('hidden');
  document.getElementById('perfil-content')?.classList.remove('hidden');

  // Inyectar información del usuario
  const avatarEl = document.getElementById('perfil-avatar');
  if (avatarEl) {
    avatarEl.textContent = iniciales;
    avatarEl.setAttribute('aria-label', `Avatar de ${usuario.nombre || 'usuario'}`);
  }
  document.getElementById('perfil-nombre-completo').textContent = `${usuario.nombre || ''} ${usuario.apellido || ''}`;
  document.getElementById('perfil-email').textContent = usuario.email || '';
  document.getElementById('perfil-tipo-label').textContent = tipoLabel;

  // Acciones
  const btnEditar = document.getElementById('btn-editar-perfil');
  if (btnEditar) {
    btnEditar.addEventListener('click', () => _abrirEdicion(usuario.nombre, usuario.apellido));
  }
  if (esProp) {
    const btnAgregar = document.getElementById('btn-agregar-lugar');
    if (btnAgregar) {
      btnAgregar.classList.remove('hidden');
      btnAgregar.classList.add('flex');
    }
  }

  // Tarjeta de Rango
  document.getElementById('rango-icon').textContent = rango.icon;
  document.getElementById('rango-icon').style.color = rango.color;
  document.getElementById('rango-nombre').textContent = rango.nombre;
  document.getElementById('pts-odometro').style.color = rango.color;

  const rangoProgreso = document.getElementById('rango-progreso-container');
  if (rangoProgreso) {
    rangoProgreso.innerHTML = rangoSig ? `
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
        <span class="material-symbols-outlined text-accent pointer-events-none" style="font-size:18px;">verified</span>
        <p class="text-body-sm text-accent font-semibold">¡Has alcanzado el rango máximo!</p>
      </div>`;
  }

  // Estadísticas
  const statsContainer = document.getElementById('stats-container');
  if (statsContainer) {
    statsContainer.innerHTML = stats.map(s => `
      <div class="bg-surface-raised border border-border-default rounded-md p-4 text-center">
        <span class="material-symbols-outlined text-text-tertiary mb-2 block pointer-events-none" style="font-size:22px;">${s.icon}</span>
        ${s.numerico
          ? `<p class="font-heading text-numeric-md text-primary tabular-nums">${(s.val||0).toLocaleString('es-MX')}</p>`
          : `<p class="text-body-sm text-primary font-semibold leading-snug">${s.val}</p>`}
        <p class="text-label-md text-text-tertiary mt-0.5">${s.label}</p>
      </div>`).join('');
  }

  // Historial
  const historialContainer = document.getElementById('historial-container');
  if (historialContainer) {
    historialContainer.innerHTML = histItems.length ? `
      <div aria-label="Historial de actividad">
        ${histItems.slice(0, 4).map((h, i) => {
          const pts = h.puntos_ganados ?? h.puntos ?? 0;
          const pos = pts >= 0;
          return `
            <div class="flex items-center gap-4 py-3 border-b border-border-subtle last:border-0 card-enter"
                 style="animation-delay:${i*35}ms">
              <div class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
                          ${pos ? 'bg-success-faint text-success' : 'bg-accent-faint text-accent'}">
                <span class="material-symbols-outlined pointer-events-none" style="font-size:15px;">${_historialIcon(h.motivo)}</span>
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-body-sm font-medium text-primary truncate">${h.motivo || 'Actividad'}</p>
                <p class="text-label-md text-text-tertiary">${_fechaCorta(h.fecha)}</p>
              </div>
              <span class="text-numeric-sm font-bold flex-shrink-0 ${pos ? 'text-success' : 'text-accent'}">
                ${pos ? '+' : ''}${pts} pts
              </span>
            </div>`;
        }).join('')}
        ${histItems.length > 4 ? `
          <button data-action="abrir-historial" class="w-full mt-3 py-2 text-sm font-semibold text-white bg-accent hover:bg-accent-hover transition-colors text-center rounded">Ver historial completo</button>
        ` : ''}
      </div>` : `
      <div class="flex flex-col items-center py-12 text-center">
        <span class="material-symbols-outlined text-4xl text-text-tertiary mb-3 pointer-events-none">history</span>
        <p class="text-body-sm text-text-tertiary">Aún no tienes actividad registrada.</p>
        <p class="text-label-md text-text-tertiary mt-1">Deja reseñas o agrega lugares para ganar puntos.</p>
      </div>`;
  }

  // Mis Contribuciones
  window._contribPage = 1;
  window._contribucionesRaw = contribuciones || [];
  
  function _renderContribuciones() {
    const contribContainer = document.getElementById('contribuciones-container');
    if (!contribContainer) return;
    
    if (window._contribucionesRaw.length > 0) {
      const perPage = 4;
      const limit = window._contribPage * perPage;
      const shown = window._contribucionesRaw.slice(0, limit);
      
      let html = shown.map(c => `
        <div class="bg-surface border border-border-default rounded-lg p-4 flex flex-col justify-between hover:border-accent-muted transition-colors">
          <div>
            <div class="flex items-start justify-between mb-2">
              <h3 class="font-heading font-semibold text-primary text-base truncate pr-2">${c.nombre}</h3>
              <span class="text-xs px-2 py-0.5 rounded ${
                c.solicita_baja ? 'bg-accent-faint text-accent border border-accent/20' :
                c.estado === 'aprobado' ? 'bg-success-faint text-success border border-success/20' :
                c.estado === 'pendiente' ? 'bg-warning-faint text-warning border border-warning/20' :
                'bg-accent-faint text-accent border border-accent/20'
              } capitalize whitespace-nowrap">${c.solicita_baja ? 'Pendiente baja' : c.estado}</span>
            </div>
            <p class="text-sm text-text-tertiary mb-3 line-clamp-2">${c.direccion_texto || 'Sin dirección'}</p>
          </div>
          <div class="flex justify-between items-center mt-2 pt-3 border-t border-border-faint">
            <span class="text-xs font-medium text-text-tertiary uppercase tracking-wider">${c.tipo_establecimiento.replace('_', ' ')}</span>
            <div class="flex gap-2">
              ${c.estado !== 'rechazado' ? `<button data-action="editar-contribucion" data-id="${c.id_establecimiento}" class="text-text-secondary text-sm font-medium hover:text-primary transition-colors">Editar</button>` : ''}
              <button data-action="eliminar-contribucion" data-id="${c.id_establecimiento}" class="text-accent text-sm font-medium hover:text-accent-hover transition-colors">Eliminar</button>
            </div>
          </div>
        </div>
      `).join('');
      
      if (limit < window._contribucionesRaw.length) {
        html += `
          <div class="col-span-1 md:col-span-2 flex justify-center mt-2">
            <button data-action="cargar-mas-contribuciones" class="px-6 py-2 bg-surface-dim text-text-primary text-sm font-semibold rounded hover:bg-surface-raised border border-border-default transition-colors">Ver más contribuciones</button>
          </div>
        `;
      }
      contribContainer.innerHTML = html;
    } else {
      contribContainer.innerHTML = `
        <div class="col-span-1 md:col-span-2 flex flex-col items-center py-8 text-center bg-surface border border-border-default rounded-lg">
          <span class="material-symbols-outlined text-4xl text-text-tertiary mb-2 pointer-events-none">storefront</span>
          <p class="text-body-sm text-text-secondary">Aún no has agregado ningún lugar.</p>
          <a href="#/contribucion" class="mt-3 text-sm font-semibold text-accent hover:text-accent-hover transition-colors">¡Haz tu primera contribución!</a>
        </div>
      `;
    }
  }
  _renderContribuciones();
  
  // Guardar items en global para el modal
  window._histItemsRaw = histItems;
  window._renderHistorialModal = (page) => {
    const list = document.getElementById('historial-modal-list');
    const pagination = document.getElementById('historial-modal-pagination');
    if(!list || !pagination) return;
    const size = 10;
    const totalPages = Math.ceil(window._histItemsRaw.length / size);
    if(page < 0) page = 0;
    if(page >= totalPages) page = totalPages - 1;
    
    const slice = window._histItemsRaw.slice(page * size, (page + 1) * size);
    
    list.innerHTML = slice.map((h, i) => {
      const pts = h.puntos_ganados ?? h.puntos ?? 0;
      const pos = pts >= 0;
      return `
        <div class="flex items-center gap-4 py-3 border-b border-border-subtle last:border-0">
          <div class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
                      ${pos ? 'bg-success-faint text-success' : 'bg-accent-faint text-accent'}">
            <span class="material-symbols-outlined pointer-events-none" style="font-size:15px;">${_historialIcon(h.motivo)}</span>
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-body-sm font-medium text-primary truncate">${h.motivo || 'Actividad'}</p>
            <p class="text-label-md text-text-tertiary">${_fechaCorta(h.fecha)}</p>
          </div>
          <span class="text-numeric-sm font-bold flex-shrink-0 ${pos ? 'text-success' : 'text-accent'}">
            ${pos ? '+' : ''}${pts} pts
          </span>
        </div>`;
    }).join('');
    
    pagination.innerHTML = `
      <button onclick="window._renderHistorialModal(${page - 1})" ${page === 0 ? 'disabled' : ''} class="px-2 sm:px-3 py-1 rounded bg-surface-dim border border-border-default disabled:opacity-50 text-xs sm:text-sm whitespace-nowrap">Anterior</button>
      <select onchange="window._renderHistorialModal(parseInt(this.value))" class="bg-surface border border-border-default rounded p-1 pr-6 sm:pr-8 text-xs sm:text-sm outline-none flex-1 mx-2 min-w-0 max-w-[140px] sm:max-w-none">
        ${Array.from({length: totalPages}).map((_, idx) => `<option value="${idx}" ${idx === page ? 'selected' : ''}>Página ${idx + 1} de ${totalPages}</option>`).join('')}
      </select>
      <button onclick="window._renderHistorialModal(${page + 1})" ${page >= totalPages - 1 ? 'disabled' : ''} class="px-2 sm:px-3 py-1 rounded bg-surface-dim border border-border-default disabled:opacity-50 text-xs sm:text-sm whitespace-nowrap">Siguiente</button>
    `;
  };
  
  async function _eliminarContribucion(id) {
    import('../components/Modal.js').then(module => {
      const Modal = module.Modal;
      Modal.showConfirm({
        title: 'Eliminar Contribución',
        message: '¿Estás seguro de que deseas eliminar este establecimiento?',
        confirmText: 'Eliminar',
        onConfirm: async () => {
          try {
            const resp = await api.eliminarContribucion(id);
            if(resp.status === 'soft_delete') {
               showToast(resp.message || 'Solicitud de baja enviada', 'success');
            } else {
               showToast('Contribución eliminada permanentemente', 'success');
            }
            perfilController(); // Recargar
          } catch(e) {
            showToast('Error al intentar eliminar', 'error');
          }
        }
      });
    });
  }

  // Animar odómetro después del render
  setTimeout(() => {
    const el = document.getElementById('pts-odometro');
    if (el) _odometro(el, puntos, 1400);
  }, 180);
}
