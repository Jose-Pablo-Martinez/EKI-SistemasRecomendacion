/**
 * Componente genérico que se usa para el modal de reseñas, cada que se quiera incluir
 * el sistema reseñas de usuarios se debe reutilizar este modal. 
 */


import { escapeHTML } from '../utils.js';

// Helper local para fechas
function _fecha(str) {
  if (!str) return '';
  return new Date(str).toLocaleDateString('es-MX', { year:'numeric', month:'short', day:'numeric' });
}

// Helper local para badges de NLP
function _sentimientoBadge(polaridad) {
  if (polaridad === null || polaridad === undefined) return '';
  if (polaridad >  0.1) return `<span class="text-label-sm text-success flex items-center gap-1"><span class="material-symbols-outlined pointer-events-none" style="font-size:13px;">sentiment_satisfied</span>Positiva</span>`;
  if (polaridad < -0.1) return `<span class="text-label-sm text-accent flex items-center gap-1"><span class="material-symbols-outlined pointer-events-none" style="font-size:13px;">sentiment_dissatisfied</span>Negativa</span>`;
  return `<span class="text-label-sm text-text-tertiary flex items-center gap-1"><span class="material-symbols-outlined pointer-events-none" style="font-size:13px;">sentiment_neutral</span>Neutral</span>`;
}

/**
 * Renderiza el HTML de una reseña individual
 */
export function renderReviewItem(r, idx) {
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

/**
 * Modal genérico para mostrar listas largas de reseñas con paginación
 */
export class ReviewsModal {
  constructor() {
    this.page = 1;
    this.pageSize = 10;
    this.resenas = [];
  }

  show(resenas) {
    this.resenas = resenas || [];
    this.page = 1;
    let modalContainer = document.getElementById('modal-todas-resenas');
    if (!modalContainer) {
      modalContainer = document.createElement('div');
      modalContainer.id = 'modal-todas-resenas';
      // Usando bg-primary/70 o bg-surface-overlay en lugar de estilos hardcodeados
      modalContainer.className = 'fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-primary/70 backdrop-blur-sm';
      document.body.appendChild(modalContainer);
      
      // Delegar clicks de este modal internamente
      modalContainer.addEventListener('click', (e) => {
        if (e.target === modalContainer || e.target.closest('[data-action="cerrar-modal-resenas"]')) {
          this.close();
        } else if (e.target.closest('[data-action="cargar-mas-resenas"]')) {
          this.loadMore();
        }
      });
    }

    const visible = this.resenas.slice(0, this.pageSize);
    
    modalContainer.innerHTML = `
      <div class="bg-surface-raised w-full max-w-2xl max-h-[85vh] rounded-lg shadow-xl flex flex-col fade-in">
        <div class="p-4 sm:p-6 border-b border-border-subtle flex justify-between items-center sticky top-0 bg-surface-raised z-10 rounded-t-lg">
          <h2 class="font-heading text-headline-sm text-primary">Todas las reseñas (${this.resenas.length})</h2>
          <button data-action="cerrar-modal-resenas" class="text-text-tertiary hover:text-primary transition-colors p-1">
            <span class="material-symbols-outlined" style="font-size:24px;">close</span>
          </button>
        </div>
        <div class="p-4 sm:p-6 overflow-y-auto" id="modal-resenas-list">
          <div class="space-y-6">
            ${visible.map((r,i) => renderReviewItem(r,i)).join('')}
          </div>
          ${this.resenas.length > this.pageSize ? `
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

  loadMore() {
    this.page++;
    const visible = this.resenas.slice(0, this.page * this.pageSize);
    
    const listContainer = document.getElementById('modal-resenas-list');
    if (!listContainer) return;

    const contentHtml = `
      <div class="space-y-6">
        ${visible.map((r,i) => renderReviewItem(r,i)).join('')}
      </div>
    `;
    
    const footerEl = document.getElementById('modal-resenas-footer');
    
    if (visible.length >= this.resenas.length) {
      if (footerEl) footerEl.remove();
      listContainer.innerHTML = contentHtml + `<p class="text-center text-body-sm text-text-tertiary italic mt-8 pb-4">No hay más reseñas por cargar.</p>`;
    } else {
      listContainer.querySelector('.space-y-6').outerHTML = contentHtml;
    }
  }

  close() {
    const modalContainer = document.getElementById('modal-todas-resenas');
    if (modalContainer) {
      modalContainer.classList.add('hidden');
    }
    document.body.style.overflow = '';
  }
}

export const reviewsModal = new ReviewsModal();
