/**
 * geo-worker.js — Web Worker de Geolocalización
 * frontend/scripts/workers/geo-worker.js
 * EkiSystem — Fase 5 (bonus +4 puntos)
 *
 * Por qué usar un Worker:
 *  - navigator.geolocation.watchPosition puede bloquear el hilo principal
 *    si el dispositivo tarda en obtener señal GPS (cold start de GPS puede
 *    tardar varios segundos en móvil).
 *  - El Worker corre en un hilo separado: la UI jamás se congela.
 *  - Soporta watchPosition continuo para actualizar la ubicación mientras
 *    el usuario navega por el feed sin re-solicitar permiso.
 *
 * Protocolo de mensajes (postMessage):
 *
 *  Worker ← Main:
 *    { type: 'START',  options?: PositionOptions }   — iniciar seguimiento
 *    { type: 'STOP' }                                — detener seguimiento
 *    { type: 'GET_ONCE' }                            — obtener una sola vez
 *
 *  Worker → Main:
 *    { type: 'LOCATION', lat, lon, accuracy, timestamp }  — nueva posición
 *    { type: 'ERROR',    code, message }                  — error de geo
 *    { type: 'UNSUPPORTED' }                              — geo no disponible
 *
 * Uso desde el hilo principal (utils.js o app.js):
 *
 *   const geoWorker = new Worker('scripts/workers/geo-worker.js');
 *
 *   geoWorker.onmessage = ({ data }) => {
 *     if (data.type === 'LOCATION') {
 *       appState.setLocation(data.lat, data.lon);
 *       api.enviarUbicacion(data.lat, data.lon).catch(() => {});
 *     }
 *   };
 *
 *   geoWorker.postMessage({ type: 'START' });
 *
 *   // Al salir de la app / cambiar de página:
 *   geoWorker.postMessage({ type: 'STOP' });
 */

/* global self */

// Estado interno del worker
let _watchId  = null;   // ID de watchPosition activo
let _lastLat  = null;
let _lastLon  = null;
const _MIN_DIST_M = 50; // No notificar si el usuario no se movió más de 50 m

// Haversine simplificado para calcular desplazamiento
function _distMetros(lat1, lon1, lat2, lon2) {
  const R  = 6371000; // radio Tierra en metros
  const φ1 = lat1 * Math.PI / 180;
  const φ2 = lat2 * Math.PI / 180;
  const Δφ = (lat2 - lat1) * Math.PI / 180;
  const Δλ = (lon2 - lon1) * Math.PI / 180;
  const a  = Math.sin(Δφ/2)**2 + Math.cos(φ1)*Math.cos(φ2)*Math.sin(Δλ/2)**2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

// Enviar posición al hilo principal
function _enviar(position) {
  const { latitude: lat, longitude: lon, accuracy } = position.coords;

  // Filtrar ruido: solo notificar si se movió más de _MIN_DIST_M
  if (_lastLat !== null) {
    const dist = _distMetros(_lastLat, _lastLon, lat, lon);
    if (dist < _MIN_DIST_M) return;
  }

  _lastLat = lat;
  _lastLon = lon;

  self.postMessage({
    type:      'LOCATION',
    lat,
    lon,
    accuracy,
    timestamp: position.timestamp,
  });
}

// Enviar error al hilo principal
function _error(err) {
  const mensajes = {
    1: 'El usuario denegó el permiso de ubicación.',
    2: 'La posición no está disponible (señal GPS insuficiente).',
    3: 'Tiempo de espera agotado al obtener la ubicación.',
  };
  self.postMessage({
    type:    'ERROR',
    code:    err.code,
    message: mensajes[err.code] || err.message || 'Error desconocido de geolocalización.',
  });
}

// Opciones por defecto
const _DEFAULT_OPTS = {
  enableHighAccuracy: true,
  timeout:            12000,  // 12 s máximo por lectura
  maximumAge:         30000,  // aceptar cache de hasta 30 s
};

// Manejador de mensajes del hilo principal
self.onmessage = function({ data }) {
  if (!data || !data.type) return;

  switch (data.type) {

    case 'START': {
      // Detener watch anterior si existe
      if (_watchId !== null && self.navigator?.geolocation) {
        self.navigator.geolocation.clearWatch(_watchId);
        _watchId = null;
      }

      if (!self.navigator?.geolocation) {
        self.postMessage({ type: 'UNSUPPORTED' });
        return;
      }

      const opts = Object.assign({}, _DEFAULT_OPTS, data.options || {});
      _watchId = self.navigator.geolocation.watchPosition(_enviar, _error, opts);
      break;
    }

    case 'GET_ONCE': {
      if (!self.navigator?.geolocation) {
        self.postMessage({ type: 'UNSUPPORTED' });
        return;
      }
      const opts = Object.assign({}, _DEFAULT_OPTS, data.options || {});
      self.navigator.geolocation.getCurrentPosition(_enviar, _error, opts);
      break;
    }

    case 'STOP': {
      if (_watchId !== null && self.navigator?.geolocation) {
        self.navigator.geolocation.clearWatch(_watchId);
        _watchId = null;
      }
      _lastLat = null;
      _lastLon = null;
      break;
    }

    default:
      // Mensaje desconocido — ignorar silenciosamente
      break;
  }
};
