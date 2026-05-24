// frontend/scripts/utils.js
// EkiSystem — Utilidades globales

window.controllers = {}; // Namespace para controladores

// Geolocalización
function solicitarUbicacion() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocalización no soportada'));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
      (err) => reject(err),
      { enableHighAccuracy: true, timeout: 10000 }
    );
  });
}

// Toast notifications
// Cada toast tiene: icono · título · mensaje · barra de progreso · botón cerrar
// aria-live="polite" en el container (puesto en index.html) garantiza accesibilidad.

const _TOAST_CONFIG = {
  info:    { icon: 'info',             title: 'Información', border: 'var(--secondary)',   bg: 'var(--secondary-faint)',  text: 'var(--secondary)' },
  success: { icon: 'check_circle',     title: '¡Listo!',     border: 'var(--success)',     bg: '#EBF4ED',                 text: 'var(--success)'   },
  warning: { icon: 'warning',          title: 'Atención',    border: 'var(--warning)',     bg: '#FBF2E2',                 text: 'var(--warning)'   },
  error:   { icon: 'error',            title: 'Error',       border: 'var(--accent)',      bg: 'var(--accent-faint)',     text: 'var(--accent)'    },
};

function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const cfg = _TOAST_CONFIG[type] || _TOAST_CONFIG.info;

  const toast = document.createElement('div');
  toast.setAttribute('role', 'status');
  toast.setAttribute('aria-live', 'polite');
  toast.style.cssText = `
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 12px 14px;
    border-radius: 8px;
    border: 1px solid ${cfg.border}40;
    border-left: 3px solid ${cfg.border};
    background: ${cfg.bg};
    box-shadow: 0 4px 24px rgba(30,27,24,0.10);
    max-width: 340px;
    width: 100%;
    transform: translateX(110%);
    opacity: 0;
    transition: transform 300ms cubic-bezier(0.22,1,0.36,1), opacity 300ms ease;
    position: relative;
    overflow: hidden;
  `;

  toast.innerHTML = `
    <span class="material-symbols-outlined" style="font-size:18px;color:${cfg.text};flex-shrink:0;margin-top:1px;">${cfg.icon}</span>
    <div style="flex:1;min-width:0;">
      <p style="font-family:Montserrat,sans-serif;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:${cfg.text};margin-bottom:1px;">${cfg.title}</p>
      <p style="font-family:Montserrat,sans-serif;font-size:13px;color:var(--primary-muted);line-height:1.4;">${message}</p>
    </div>
    <button onclick="this.closest('[role=status]').remove()" aria-label="Cerrar notificación"
      style="background:none;border:none;cursor:pointer;color:var(--primary-ghost);padding:0;margin-top:1px;flex-shrink:0;line-height:1;">
      <span class="material-symbols-outlined" style="font-size:16px;">close</span>
    </button>
    <div style="
      position:absolute;bottom:0;left:0;height:2px;background:${cfg.border};
      animation: _toastProgress ${duration}ms linear forwards;
    "></div>
  `;

  // Inyectar keyframe si no existe
  if (!document.getElementById('_toast-style')) {
    const s = document.createElement('style');
    s.id = '_toast-style';
    s.textContent = `
      @keyframes _toastProgress {
        from { width: 100%; }
        to   { width: 0%; }
      }
    `;
    document.head.appendChild(s);
  }

  container.appendChild(toast);

  // Entrada
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      toast.style.transform = 'translateX(0)';
      toast.style.opacity   = '1';
    });
  });

  // Salida automática
  const dismiss = () => {
    toast.style.transform = 'translateX(110%)';
    toast.style.opacity   = '0';
    setTimeout(() => toast.remove(), 320);
  };
  setTimeout(dismiss, duration);
}
