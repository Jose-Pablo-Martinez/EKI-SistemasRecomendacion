// frontend/js/app.js

const routes = {
  '':            () => window.controllers.home(),
  '#/':          () => window.controllers.home(),
  '#/login':     () => window.controllers.login(),
  '#/registro':  () => window.controllers.register(),
  '#/onboarding':() => { if (requireAuth()) window.controllers.onboarding() },
  '#/feed':      () => { if (requireAuth()) window.controllers.feed() },
  '#/buscar':    () => window.controllers.busqueda(),
  '#/perfil':    () => { if (requireAuth()) window.controllers.perfil() },
  '#/favoritos': () => { if (requireAuth()) window.controllers.favoritos() },
  '#/admin':     () => { if (requireAuth()) window.controllers.admin() },
  '#/como-funciona': () => window.controllers['como-funciona'](),
};

async function renderView(viewPath) {
  const root = document.getElementById('app-root');
  
  // Guardamos el estado anterior para la transición
  root.style.opacity = 0;
  
  try {
      const response = await fetch(`views/${viewPath}`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const htmlContent = await response.text();
      
      // Asegurar que ocurra después de que la opacidad haya bajado
      setTimeout(() => {
          root.innerHTML = htmlContent;
          root.style.transition = 'opacity 400ms cubic-bezier(0, 0, 0.2, 1)';
          root.style.opacity = 1;
      }, 150);
      
      // Devolvemos la promesa para saber cuándo el HTML ya está en el DOM
      // (asumimos un pequeño retraso artificial para asegurar inyección)
      return new Promise(resolve => setTimeout(() => resolve(true), 200));
  } catch (e) {
      console.error("Error loading view:", e);
      root.innerHTML = `<p class="p-8 text-accent">Error al cargar la vista: ${e.message}</p>`;
      root.style.opacity = 1;
      return false;
  }
}

function renderPage(htmlContent) {
  const root = document.getElementById('app-root');
  root.style.opacity = 0;
  
  setTimeout(() => {
    root.innerHTML = htmlContent;
    root.style.transition = 'opacity 400ms cubic-bezier(0, 0, 0.2, 1)';
    root.style.opacity = 1;
  }, 100); 
}

async function handleRoute() {
  const hash = window.location.hash.split('?')[0]; 
  
  // Rutas dinámicas
  if (hash.startsWith('#/establecimiento/')) {
    const id = hash.split('/')[2];
    await window.controllers.establecimiento(id);
    return;
  }
  
  const routeAction = routes[hash] || routes['#/'];
  await routeAction();
}

function updateHeader() {
  const navMenu = document.getElementById('nav-menu');
  const userActions = document.getElementById('user-actions');
  
  if (appState.isAuthenticated) {
    navMenu.innerHTML = `
      <a href="#/feed" class="text-text-tertiary hover:text-text-primary text-sm font-bold tracking-widest uppercase transition-colors">Feed</a>
      <a href="#/buscar" class="text-text-tertiary hover:text-text-primary text-sm font-bold tracking-widest uppercase transition-colors">Buscar</a>
      ${appState.isAdmin ? '<a href="#/admin" class="text-text-tertiary hover:text-text-primary text-sm font-bold tracking-widest uppercase transition-colors">Admin</a>' : ''}
    `;
    userActions.innerHTML = `
      <a href="#/favoritos" class="text-text-tertiary hover:text-accent transition-colors" title="Favoritos">❤️</a>
      <a href="#/perfil" class="w-8 h-8 rounded-full bg-primary-faint flex items-center justify-center text-text-secondary font-bold hover:ring-2 ring-accent transition-all" title="Perfil">
        ${appState.user?.nombre ? appState.user.nombre[0].toUpperCase() : 'U'}
      </a>
      <button onclick="logout()" class="text-sm text-text-tertiary hover:text-accent">Salir</button>
    `;
  } else {
    navMenu.innerHTML = `
      <a href="#/" class="text-text-tertiary hover:text-text-primary text-sm font-bold tracking-widest uppercase transition-colors">Inicio</a>
      <a href="#/buscar" class="text-text-tertiary hover:text-text-primary text-sm font-bold tracking-widest uppercase transition-colors">Explorar</a>
    `;
    userActions.innerHTML = `
      <a href="#/login" class="bg-accent text-white px-4 py-2 rounded font-semibold text-sm hover:bg-accent-hover transition-colors shadow">Iniciar Sesión</a>
    `;
  }
}

// Inicialización de la aplicación
// Inicialización de la aplicación

window.addEventListener('hashchange', handleRoute);
window.addEventListener('DOMContentLoaded', async () => {
  appState.subscribe(updateHeader);
  await initState(); // Verifica token y carga usuario si existe
  updateHeader(); // Actualiza UI antes del primer render
    if (window.Worker) {
        window.geoWorker = new Worker('scripts/workers/geo-worker.js');
        window.geoWorker.onmessage = ({ data }) => {
          if (data.type === 'LOCATION') {
            appState.setLocation(data.lat, data.lon);
            api.enviarUbicacion(data.lat, data.lon).catch(() => {});
          }
        };
        window.geoWorker.postMessage({ type: 'START' });
      }
  handleRoute();  // Renderiza la página actual
});
