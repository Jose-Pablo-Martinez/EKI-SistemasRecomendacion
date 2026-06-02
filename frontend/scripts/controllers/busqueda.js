/**
 * busqueda.js — Buscador y explorador de establecimientos
 * EkiSystem — Fase 4 Frontend
 */

import { api } from '../api.js';
import { appState } from '../state.js';
import { renderView } from '../app.js';
import { Card } from '../components/Card.js';
import { Skeletons } from '../components/Skeletons.js';
import { escapeHTML } from '../utils.js';

// Constantes de filtros
const _FILTROS = [
  { valor:'',               label:'Todos',      icono:'apps'       },
  { valor:'puesto_informal',label:'Informales', icono:'storefront' },
  { valor:'restaurante',    label:'Restaurantes',icono:'restaurant' },
  { valor:'local_comercial',label:'Locales',    icono:'shop'       },
];

// Estado interno
let _filtroActivo = '';
let _searchTimeout = null;
let _autocompleteTimeout = null;
let _ultimaBusqueda = '';

// Helper de renderizado HTML
function _renderResultadosHTML(items, query) {
  if (!items || !items.length) {
    const safeQuery = escapeHTML(query);
    return `
      <div class="flex flex-col items-center justify-center py-16 text-center col-span-full fade-in">
        <span class="material-symbols-outlined text-4xl text-text-tertiary mb-3 pointer-events-none">search_off</span>
        <p class="font-heading text-headline-sm text-primary mb-1">Sin resultados para "${safeQuery}"</p>
        <p class="text-body-sm text-text-secondary">Prueba con otro término o cambia los filtros.</p>
      </div>`;
  }
  return items.map((e, i) => Card.renderCompact(e, i, false)).join('');
}

// Búsqueda principal
async function _ejecutarBusqueda(query) {
  const el = document.getElementById('busq-resultados');
  if (!el) return;

  _ultimaBusqueda = query;
  el.innerHTML = `<div class="grid grid-cols-1 md:grid-cols-2 gap-3 col-span-full" role="list">${Skeletons.renderCompact(4)}</div>`;

  try {
    const params = { tipo: _filtroActivo };
    const response = await api.buscar(query, params);
    if (_ultimaBusqueda !== query) return;
    
    let items = response.resultados || [];
    const sugerencia = response.sugerencia_correccion;
    const isInitialState = (!query || query.length < 2);
    
    if (isInitialState) {
      items = items.sort(() => 0.5 - Math.random()).slice(0, 20);
    }
    
    let html = '';
    
    if (isInitialState) {
      html += `
        <div class="flex flex-col items-center justify-center py-8 px-4 text-center col-span-full mb-6 bg-surface-raised border border-border-default rounded-md shadow-sm fade-in">
          <span class="material-symbols-outlined text-5xl text-text-tertiary mb-3 pointer-events-none">restaurant_menu</span>
          <p class="font-heading text-headline-sm text-primary mb-2">¿Qué se te antoja hoy?</p>
          <p class="text-body-sm text-text-secondary">Escribe al menos 2 letras para buscar opciones específicas, o explora estas sugerencias iniciales.</p>
        </div>`;
    }
    
    if (sugerencia && !isInitialState) {
      const safeSug = escapeHTML(sugerencia);
      const safeQuery = escapeHTML(query);
      html += `
        <div class="col-span-full bg-accent-faint border border-accent/30 text-accent rounded-md p-4 mb-2 flex items-center gap-3 fade-in cursor-pointer hover:bg-accent/10 transition-colors shadow-sm" 
             data-action="aplicar-sugerencia" data-sugerencia="${safeSug}">
          <span class="material-symbols-outlined pointer-events-none" style="font-size:24px;">spellcheck</span>
          <p class="font-medium text-body-md pointer-events-none">No encontramos "${safeQuery}". ¿Quizás quisiste decir <strong class="underline">${safeSug}</strong>?</p>
        </div>
      `;
    }
    
    html += _renderResultadosHTML(items, query);
    el.innerHTML = html;
  } catch(e) {
    const safeQuery = escapeHTML(query);
    el.innerHTML = `
      <div class="flex flex-col items-center justify-center py-12 text-center col-span-full">
        <span class="material-symbols-outlined text-4xl text-text-tertiary mb-3 pointer-events-none">wifi_off</span>
        <p class="text-body-sm text-text-secondary mb-4">No se pudo conectar al servidor.</p>
        <button data-action="reintentar-busqueda" data-query="${safeQuery}"
          class="bg-accent text-white px-4 py-2 rounded font-semibold text-label-lg hover:bg-accent-hover transition-colors">
          Reintentar
        </button>
      </div>`;
  }
}

// Controlador principal
export default async function busquedaController() {
  const loaded = await renderView('busqueda.html');
  if (!loaded) return;

  const chipsContainer = document.getElementById('chips-container');
  if (chipsContainer) {
    chipsContainer.innerHTML = _FILTROS.map(f => `
      <button
        data-action="set-filtro"
        data-tipo="${f.valor}"
        class="chip-filtro flex items-center gap-1.5 px-4 py-2 rounded-full border text-label-lg transition-all
              ${_filtroActivo === f.valor
                ? 'bg-primary text-white border-primary'
                : 'bg-surface-raised border-border-default text-text-secondary hover:border-border-strong hover:text-primary'}">
        <span class="material-symbols-outlined pointer-events-none" style="font-size:15px;line-height:1;">${f.icono}</span>
        ${f.label}
      </button>`).join('');
  }

  const input = document.getElementById('busq-input');
  const clearBtn = document.getElementById('busq-clear');
  
  const guestBanner = document.getElementById('guest-banner');
  if (guestBanner) {
    if (!appState.isAuthenticated) {
      guestBanner.classList.remove('hidden');
    } else {
      guestBanner.classList.add('hidden');
    }
  }

  if (!input) return;

  if (_ultimaBusqueda) {
    input.value = _ultimaBusqueda;
    clearBtn?.classList.remove('hidden');
  }
  _ejecutarBusqueda(_ultimaBusqueda || '');

  input.addEventListener('input', e => {
    const q = e.target.value;
    const qTrimmed = q.trim();
    clearBtn?.classList.toggle('hidden', !qTrimmed);
    
    clearTimeout(_autocompleteTimeout);
    if (qTrimmed.length >= 2) {
      _autocompleteTimeout = setTimeout(() => _fetchAutocomplete(qTrimmed), 150);
    } else {
      _ocultarAutocomplete();
    }

    clearTimeout(_searchTimeout);
    _searchTimeout = setTimeout(() => {
      _ejecutarBusqueda(qTrimmed);
    }, 400);
  });

  input.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      _clearBusqueda();
      _ocultarAutocomplete();
    }
  });
  
  document.addEventListener('click', _handleClickFuera);

  // Delegación de eventos de la vista
  const viewContainer = document.getElementById('busqueda-view');
  if (viewContainer) {
    viewContainer.addEventListener('click', (e) => {
      const actionEl = e.target.closest('[data-action]');
      if (!actionEl) return;
      
      const action = actionEl.dataset.action;
      if (action === 'set-filtro') {
        const val = actionEl.dataset.tipo;
        _setFiltro(val);
      } else if (action === 'aplicar-sugerencia') {
        const sug = actionEl.dataset.sugerencia;
        const inpt = document.getElementById('busq-input');
        if(inpt) inpt.value = sug;
        clearTimeout(_searchTimeout);
        _ultimaBusqueda = sug;
        _ejecutarBusqueda(sug);
      } else if (action === 'reintentar-busqueda') {
        const q = actionEl.dataset.query;
        _ejecutarBusqueda(q);
      } else if (action === 'clear-busqueda') {
        _clearBusqueda();
      } else if (action === 'seleccionar-autocomplete') {
        const sug = actionEl.dataset.sugerencia;
        _seleccionarAutocomplete(sug);
      } else if (action === 'close-guest-banner') {
        const banner = document.getElementById('guest-banner');
        if (banner) banner.classList.add('hidden');
      }
    });
  }

  input.focus();
}

// Ocultar al hacer click fuera
function _handleClickFuera(e) {
  const menu = document.getElementById('autocomplete-menu');
  const input = document.getElementById('busq-input');
  if (menu && !menu.contains(e.target) && e.target !== input) {
    _ocultarAutocomplete();
  }
}

// Autocompletado
async function _fetchAutocomplete(query) {
  try {
    const res = await api.autocompletar(query);
    if (res && res.sugerencias && res.sugerencias.length > 0) {
      _renderAutocomplete(res.sugerencias, query);
    } else {
      _ocultarAutocomplete();
    }
  } catch (e) {
    console.error("Error cargando autocompletado:", e);
    _ocultarAutocomplete();
  }
}

function _renderAutocomplete(sugerencias, queryOriginal) {
  const menu = document.getElementById('autocomplete-menu');
  const lista = document.getElementById('autocomplete-list');
  if (!menu || !lista) return;

  lista.innerHTML = sugerencias.map(s => {
    const lowerS = s.toLowerCase();
    const lowerQ = queryOriginal.toLowerCase();
    let displayHtml = escapeHTML(s);
    if (lowerS.startsWith(lowerQ)) {
      displayHtml = `<span class="font-bold text-primary">${escapeHTML(s.substring(0, queryOriginal.length))}</span>${escapeHTML(s.substring(queryOriginal.length))}`;
    }
    
    return `
      <li class="px-4 py-3 hover:bg-surface-raised cursor-pointer flex items-center gap-3 transition-colors text-body-md border-b border-border-default last:border-0"
          data-action="seleccionar-autocomplete" data-sugerencia="${escapeHTML(s)}">
        <span class="material-symbols-outlined text-text-tertiary pointer-events-none" style="font-size:18px;">search</span>
        <span class="text-text-secondary pointer-events-none">${displayHtml}</span>
      </li>
    `;
  }).join('');
  
  menu.classList.remove('hidden');
}

function _ocultarAutocomplete() {
  const menu = document.getElementById('autocomplete-menu');
  if (menu) menu.classList.add('hidden');
}

function _seleccionarAutocomplete(texto) {
  const input = document.getElementById('busq-input');
  if (input) {
    input.value = texto;
    _ocultarAutocomplete();
    
    clearTimeout(_searchTimeout);
    _ejecutarBusqueda(texto);
  }
}

// Filtros
function _setFiltro(valor) {
  _filtroActivo = valor;

  document.querySelectorAll('.chip-filtro').forEach(btn => {
    const activo = btn.dataset.tipo === valor;
    btn.className = btn.className
      .replace(/bg-primary text-white border-primary|bg-surface-raised border-border-default text-text-secondary hover:border-border-strong hover:text-primary/g, '')
      .trim();
    if (activo) {
      btn.classList.add('bg-primary','text-white','border-primary');
    } else {
      btn.classList.add('bg-surface-raised','border-border-default','text-text-secondary','hover:border-border-strong','hover:text-primary');
    }
  });

  const q = document.getElementById('busq-input')?.value?.trim() || '';
  _ejecutarBusqueda(q);
}

// Limpiar búsqueda
function _clearBusqueda() {
  const input = document.getElementById('busq-input');
  const clearBtn = document.getElementById('busq-clear');
  if (input) { input.value = ''; input.focus(); }
  clearBtn?.classList.add('hidden');
  _ultimaBusqueda = '';
  _ocultarAutocomplete();
  _ejecutarBusqueda('');
}
