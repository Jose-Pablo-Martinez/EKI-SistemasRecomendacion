/**
 * Archivo modificado: 2026-06-02
 * Función: Capa de abstracción para la comunicación HTTP con FastAPI. 
 * Maneja JWT, rutas del sistema, y retries globales (spin-down).
 */

import { showToast } from './utils.js';

export const API_BASE_URL = window.location.hostname === "localhost"
  ? "http://localhost:8000"
  : "https://esquina-jach-ki.onrender.com";

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

// Lógica de spin-down global
const _RETRY_MAX = 6;
const _RETRY_INTERVAL = 5000;
let _currentRetry = 0;
let _retryTimer = null;

function _mostrarSpinDownUI(intento) {
  const el = document.getElementById('loading-screen');
  if (!el) {
    showToast(`El servidor está despertando... Intento ${intento}/${_RETRY_MAX}`, 'info', 4000);
    return;
  }
  const segsRestantes = Math.round((_RETRY_MAX - intento + 1) * _RETRY_INTERVAL / 1000);
  el.innerHTML = `
    <div class="flex flex-col items-center justify-center p-8 text-center text-accent gap-4 fade-in">
      <span class="material-symbols-outlined text-5xl animate-spin" aria-hidden="true">autorenew</span>
      <h3 class="font-heading text-headline-md text-primary mb-2">El servidor está despertando...</h3>
      <p class="font-medium text-text-tertiary mb-1">Esto puede tardar hasta ${segsRestantes} segundos.</p>
      <div class="w-52 mb-2 bg-surface-dim rounded-full h-2 overflow-hidden">
        <div class="bg-secondary h-full transition-all duration-1000" style="width:${Math.round((intento/_RETRY_MAX)*100)}%"></div>
      </div>
      <p class="text-label-sm text-text-tertiary">Intento ${intento} de ${_RETRY_MAX}</p>
    </div>`;
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export async function apiRequest(endpoint, options = {}, isRetry = false) {
  const token = localStorage.getItem('eki_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...options.headers,
  };

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (isRetry && _currentRetry > 0) {
      showToast('¡Servidor conectado exitosamente!', 'success');
      _currentRetry = 0; // Reset
    }

    if (response.status === 401 && !endpoint.includes('/login')) {
      // Token expirado
      localStorage.removeItem('eki_token');
      window.location.hash = '#/login';
      throw new Error('Tu sesión ha terminado por seguridad, por favor vuelve a ingresar.');
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new ApiError(response.status, error.detail || 'Error del servidor');
    }

    if (response.status === 204) return null;
    return response.json();

  } catch (error) {
    // Si es error de red (TypeError) o status 50x, y no es login
    const isNetworkError = error instanceof TypeError || error.status === 0 || error.status >= 500;
    const isGet = !options.method || options.method === 'GET'; // Solo auto-retry en GETs
    
    if (isNetworkError && isGet && _currentRetry < _RETRY_MAX) {
      _currentRetry++;
      _mostrarSpinDownUI(_currentRetry);
      await sleep(_RETRY_INTERVAL);
      return apiRequest(endpoint, options, true);
    }
    
    if (_currentRetry >= _RETRY_MAX) {
      _currentRetry = 0;
      showToast('No se pudo conectar con el servidor', 'error');
    }
    throw error;
  }
}

// Funciones específicas por dominio
export const api = {
  // Auth
  login: (email, password) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    return apiRequest('/usuarios/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData
    });
  },
  registro: (data) => apiRequest('/usuarios/registro', {
    method: 'POST', body: JSON.stringify(data)
  }),
  
  // Recomendaciones
  getRecomendaciones: () => apiRequest('/recomendaciones/sections'),
  registrarClick: (id) => apiRequest(`/recomendaciones/${id}/click`, { method: 'POST' }),
  
  // Establecimientos
  getEstablecimiento: (id) => apiRequest(`/establecimientos/${id}`),
  buscar: (query, filtros) => {
    const params = new URLSearchParams(filtros);
    if (query) params.append('q', query);
    return apiRequest(`/establecimientos/buscar?${params.toString()}`);
  },
  autocompletar: (query) => apiRequest(`/establecimientos/autocomplete?q=${encodeURIComponent(query)}`),
  crearResena: (id, data) => apiRequest(`/establecimientos/${id}/resena`, {
    method: 'POST', body: JSON.stringify(data)
  }),
  actualizarHorarios: (id, horarios) => apiRequest(`/establecimientos/${id}/horarios`, {
    method: 'PUT', body: JSON.stringify(horarios)
  }),
  agregarPlatillo: (id, data) => apiRequest(`/establecimientos/${id}/platillo`, {
    method: 'POST', body: JSON.stringify(data)
  }),
  agregarImagen: (id, data) => apiRequest(`/establecimientos/${id}/imagen`, {
    method: 'POST', body: JSON.stringify(data)
  }),
  registrarInteraccion: (id, tipo) => apiRequest(`/establecimientos/${id}/interaccion`, {
    method: 'POST', body: JSON.stringify({ id_establecimiento: id, tipo_interaccion: tipo })
  }),
  toggleFavorito: (id, data) => apiRequest(`/establecimientos/${id}/favorito`, { 
    method: 'POST', body: JSON.stringify(data || { id_establecimiento: id })
  }),
  
  // Perfil
  getFavoritos: () => apiRequest('/usuarios/me/favoritos'),
  getPerfil: () => apiRequest('/usuarios/me'),
  actualizarPerfil: (data) => apiRequest('/usuarios/me', {
    method: 'PATCH', body: JSON.stringify(data)
  }),
  enviarUbicacion: (lat, lon) => apiRequest('/usuarios/ubicacion', {
    method: 'POST', body: JSON.stringify({ latitud: lat, longitud: lon })
  }),
  
  // Onboarding
  enviarOnboarding: (preferencias) => apiRequest('/usuarios/onboarding', {
    method: 'POST', body: JSON.stringify({ preferencias })
  }),
  
  // Gamificación
  getHistorialPuntos: () => apiRequest('/gamificacion/historial'),
  getRango: () => apiRequest('/gamificacion/mis-puntos'),
  
  // Contenido
  getCategorias: () => apiRequest('/contenido/categorias'),
  getEtiquetas: () => apiRequest('/contenido/etiquetas'),
  
  // Admin
  getPendientes: (tipo) => apiRequest(`/admin/${tipo}/pendientes`),
  aprobar: (tipo, id) => apiRequest(`/admin/${tipo}/${id}/aprobar`, { method: 'POST' }),
  dispararJob: (tipo) => apiRequest(`/admin/jobs/${tipo}`, { method: 'POST' }),
};
