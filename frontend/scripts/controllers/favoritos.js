/**
 * favoritos.js — Lista de establecimientos guardados
 * EkiSystem — Fase 4 Frontend
 */

// Esqueleto para favoritos se usa desde scripts/components/Skeletons.js

// Tarjeta de favorito
function _cardFav(fav, idx) {
  const e = fav.establecimiento || fav;
  const id = e.id_establecimiento || fav.id_establecimiento;
  const fechaGuardada = fav.fecha_guardado
    ? new Date(fav.fecha_guardado).toLocaleDateString('es-MX', { day:'numeric', month:'short', year:'numeric' })
    : null;

  const extraHtml = fechaGuardada ? `<p class="text-label-md text-text-tertiary mt-2">Guardado el ${fechaGuardada}</p>` : '';
  
  // Envolvemos el renderCompact de la tarjeta con el botón de quitar favorito.
  const innerCard = window.Card.renderCompact(e, idx, true, extraHtml);
  
  // Reemplazamos la etiqueta de cierre </article> para inyectar nuestro botón custom.
  return innerCard.replace('</article>', `
        <!-- Acciones -->
        <div class="flex flex-col items-end justify-between ml-2 flex-shrink-0">
          <button type="button" aria-label="Quitar de favoritos"
            onclick="event.stopPropagation(); _quitarFav(${id})"
            class="text-text-tertiary hover:text-accent p-2 -mr-2 rounded-full hover:bg-accent-faint transition-colors focus-visible">
            <span class="material-symbols-outlined" style="font-size:20px;">heart_broken</span>
          </button>
        </div>
      </article>`);
}

// Quitar favorito 
async function _quitarFav(id) {
  const card = document.getElementById(`fav-${id}`);
  // Deshabilitar botón inmediatamente
  const btn = card?.querySelector('button[onclick]');
  if (btn) btn.disabled = true;

  try {
    await api.toggleFavorito(id, 'DELETE');

    if (card) {
      card.style.transition = 'opacity 220ms ease, transform 220ms ease';
      card.style.opacity    = '0';
      card.style.transform  = 'translateX(12px)';
      setTimeout(() => {
        card.remove();
        _actualizarBadge(-1);
        // Mostrar vacío si no quedan tarjetas
        const lista = document.getElementById('favs-lista');
        if (lista && !lista.querySelector('[id^="fav-"]')) {
          lista.innerHTML = _estadoVacio();
        }
      }, 240);
    }

    showToast('Eliminado de favoritos', 'info');
  } catch(_) {
    if (btn) btn.disabled = false;
    showToast('No se pudo eliminar el favorito', 'error');
  }
}

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
      <span class="material-symbols-outlined text-5xl text-text-tertiary mb-4">heart_broken</span>
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

// Controlador Principal
window.controllers.favoritos = async () => {
  const loaded = await renderView('favoritos.html');
  if (!loaded) return;

  const lista = document.getElementById('favs-lista');
  if (lista)  lista.innerHTML = window.Skeletons.renderCompact(4);

  try {
    let favoritos = [];
    try {
      favoritos = await api.getFavoritos();
    } catch (e) {
      if(e.status !== 404) throw e;
      favoritos = [];
    }

    const lista  = document.getElementById('favs-lista');
    const badge  = document.getElementById('favs-badge');
    if (!lista) return;

    if (!favoritos.length) {
      lista.innerHTML = _favEstadoVacio();
      if (badge) badge.style.display = 'none';
      return;
    }
    
    if (badge) badge.textContent = favoritos.length;
    lista.innerHTML = favoritos.map((f, i) => _cardFav(f, i)).join('');

  } catch(e) {
    const lista = document.getElementById('favs-lista');
    if (lista) lista.innerHTML = `
      <div class="flex flex-col items-center justify-center py-16 text-center">
        <span class="material-symbols-outlined text-4xl text-text-tertiary mb-3">wifi_off</span>
        <p class="text-body-sm text-text-secondary mb-4">No se pudieron cargar tus favoritos.</p>
        <button onclick="window.controllers.favoritos()"
          class="bg-accent text-white px-4 py-2 rounded font-semibold hover:bg-accent-hover transition-colors">
          Reintentar
        </button>
      </div>`;
  }
};
