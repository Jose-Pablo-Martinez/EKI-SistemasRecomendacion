// frontend/js/api.js

const API_BASE_URL = window.location.hostname === "localhost"
  ? "http://localhost:8000"
  : "https://esquina-jach-ki.onrender.com";

class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

async function apiRequest(endpoint, options = {}) {
  const token = localStorage.getItem('eki_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    // Token expirado o inválido → redirigir a login
    localStorage.removeItem('eki_token');
    window.location.hash = '#/login';
    throw new Error('Sesión expirada');
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new ApiError(response.status, error.detail || 'Error del servidor');
  }

  // Si la respuesta es 204 No Content, no intentamos parsear JSON
  if (response.status === 204) {
      return null;
  }

  return response.json();
}

// Funciones específicas por dominio
const api = {
  // Auth
  login: (email, password) => apiRequest('/usuarios/login', {
    method: 'POST', body: JSON.stringify({ email, password })
  }),
  registro: (data) => apiRequest('/usuarios/registro', {
    method: 'POST', body: JSON.stringify(data)
  }),
  
  // Recomendaciones
  getRecomendaciones: () => apiRequest('/recomendaciones'),
  registrarClick: (id) => apiRequest(`/recomendaciones/${id}/click`, { method: 'POST' }),
  
  // Establecimientos
  getEstablecimiento: (id) => apiRequest(`/establecimientos/${id}`),
  buscar: (query, filtros) => {
    const params = new URLSearchParams(filtros);
    if (query) params.append('q', query);
    return apiRequest(`/establecimientos/buscar?${params.toString()}`);
  },
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
  toggleFavorito: (id, method) => apiRequest(`/establecimientos/${id}/favorito`, { method }),
  
  // Perfil
  getPerfil: () => apiRequest('/usuarios/perfil'),
  actualizarPerfil: (data) => apiRequest('/usuarios/perfil', {
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
  getHistorialPuntos: () => apiRequest('/usuarios/puntos'),
  getRango: () => apiRequest('/usuarios/rango'),
  
  // Contenido
  getCategorias: () => apiRequest('/categorias'),
  getEtiquetas: () => apiRequest('/etiquetas'),
  
  // Admin
  getPendientes: (tipo) => apiRequest(`/admin/${tipo}/pendientes`),
  aprobar: (tipo, id) => apiRequest(`/admin/${tipo}/${id}/aprobar`, { method: 'POST' }),
  dispararJob: (tipo) => apiRequest(`/admin/jobs/${tipo}`, { method: 'POST' }),
};
