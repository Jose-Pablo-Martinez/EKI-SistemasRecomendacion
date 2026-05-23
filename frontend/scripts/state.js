// frontend/js/state.js

const appState = {
  user: null,           // Datos del usuario autenticado
  location: null,       // { lat, lon } — última ubicación del usuario
  isAuthenticated: false,
  isAdmin: false,
  
  // Callbacks para notificar cambios de estado
  listeners: [],
  subscribe(callback) {
      this.listeners.push(callback);
  },
  notify() {
      this.listeners.forEach(callback => callback(this));
  },
  
  setUser(userData) {
      this.user = userData;
      this.isAuthenticated = !!userData;
      this.isAdmin = userData?.tipo_usuario === 'admin';
      this.notify();
  },
  
  setLocation(lat, lon) {
      this.location = { lat, lon };
      this.notify();
  }
};

// Al iniciar la app, verificar si hay token
async function initState() {
  const token = localStorage.getItem('eki_token');
  if (token && !isTokenExpired(token)) {
      try {
          const perfil = await api.getPerfil();
          appState.setUser(perfil);
      } catch (err) {
          console.error("Error cargando perfil, limpiando token.", err);
          clearToken();
      }
  } else if (token) {
      clearToken();
  }
}
