/**
 * favoritos.js — Lista de establecimientos guardados
 * EkiSystem — Fase 4 Frontend
 */

import { api } from '../api.js';
import { renderView } from '../app.js';
import { Card } from '../components/Card.js';
import { Skeletons } from '../components/Skeletons.js';
import { showToast } from '../utils.js';

// Tarjeta de favorito
function _cardFav(fav, idx) {
  const e = fav.establecimiento || fav;
  const id = e.id_establecimiento || fav.id_establecimiento;
  const fechaGuardada = fav.fecha_guardado
    ? new Date(fav.fecha_guardado).toLocaleDateString('es-MX', { day:'numeric', month:'short', year:'numeric' })
    : null;

  const extraHtml = fechaGuardada ? `<p class="text-label-md text-text-tertiary mt-2">Guardado el ${fechaGuardada}</p>` : '';
  
  const innerCard = Card.renderCompact(e, idx, true, extraHtml);
  
  return innerCard.replace('</article>', `
        <div class="flex flex-col items-end justify-between ml-2 flex-shrink-0">
          <button type="button" aria-label="Quitar de favoritos"
            data-action="quitar-fav" data-id="${id}"
            class="text-text-tertiary hover:text-accent p-2 -mr-2 rounded-full hover:bg-accent-faint transition-colors focus-visible">
            <span class="material-symbols-outlined pointer-events-none" style="font-size:20px;">heart_broken</span>
          </button>
        </div>
      </article>`);
}

// Quitar de favoritos (con animación)
async function _quitarFav(id) {
  const card = document.getElementById(`fav-${id}`);
  const btn = card?.querySelector('button[data-action="quitar-fav"]');
  if (btn) btn.disabled = true;

  try {
    await api.toggleFavorito(id);

    if (card) {
      card.style.transition = 'opacity 220ms ease, transform 220ms ease';
      card.style.opacity    = '0';
      card.style.transform  = 'translateX(12px)';
      setTimeout(() => {
        card.remove();
        _actualizarBadge(-1);
        const lista = document.getElementById('favs-lista');
        if (lista && !lista.querySelector('[id^="fav-"]')) {
          lista.innerHTML = _favEstadoVacio();
        }
      }, 240);
    }

    showToast('Eliminado de favoritos', 'info');
  } catch(_) {
    if (btn) btn.disabled = false;
    showToast('No se pudo eliminar el favorito', 'error');
  }
}

// Actualizar contador del badge
function _actualizarBadge(delta) {
  const badge = document.getElementById('favs-badge');
  if (!badge) return;
  const n = (parseInt(badge.textContent) || 0) + delta;
  badge.textContent = n > 0 ? n : '';
}

// Estado vacío
function _favEstadoVacio() {
  return `
    <div class="flex flex-col items-center justify-center py-20 text-center">
      <span class="material-symbols-outlined text-5xl text-text-tertiary mb-4 pointer-events-none">heart_broken</span>
      <h3 class="font-heading text-headline-md text-primary mb-2">Sin favoritos aún</h3>
      <p class="text-body-md text-text-secondary max-w-xs mb-6">
        Guarda los lugares que más te gusten y aparecerán aquí.
      </p>
      <a href="#/feed"
         class="bg-accent text-white px-6 py-2.5 rounded font-semibold text-label-lg
                hover:bg-accent-hover active:scale-95 transition-all shadow">
        Explorar recomendaciones
      </a>
    </div>`;
}

// Controlador principal
export default async function favoritosController() {
  const loaded = await renderView('favoritos.html');
  if (!loaded) return;

  const viewContainer = document.getElementById('favs-view');
  const lista = document.getElementById('favs-lista');
  if (lista) lista.innerHTML = Skeletons.renderCompact(4);

  // Delegación
  if (viewContainer) {
    viewContainer.addEventListener('click', (e) => {
      const actionEl = e.target.closest('[data-action]');
      if (!actionEl) return;
      const action = actionEl.dataset.action;
      
      if (action === 'quitar-fav') {
        e.stopPropagation();
        const id = actionEl.dataset.id;
        _quitarFav(id);
      } else if (action === 'reintentar-fav') {
        favoritosController();
      }
    });
  }

  try {
    let favoritos = [];
    try {
      favoritos = await api.getFavoritos();
    } catch (e) {
      if(e.status !== 404) throw e;
      favoritos = [];
    }

    const badge = document.getElementById('favs-badge');
    if (!lista) return;

    if (!favoritos.length) {
      lista.innerHTML = _favEstadoVacio();
      if (badge) badge.style.display = 'none';
      return;
    }
    
    if (badge) {
      badge.style.display = '';
      badge.textContent = favoritos.length;
    }
    lista.innerHTML = favoritos.map((f, i) => _cardFav(f, i)).join('');

  } catch(e) {
    const lista = document.getElementById('favs-lista');
    if (lista) lista.innerHTML = `
      <div class="flex flex-col items-center justify-center py-16 text-center">
        <span class="material-symbols-outlined text-4xl text-text-tertiary mb-3 pointer-events-none">wifi_off</span>
        <p class="text-body-sm text-text-secondary mb-4">No se pudieron cargar tus favoritos.</p>
        <button data-action="reintentar-fav"
          class="bg-accent text-white px-4 py-2 rounded font-semibold hover:bg-accent-hover transition-colors">
          Reintentar
        </button>
      </div>`;
  }
}
