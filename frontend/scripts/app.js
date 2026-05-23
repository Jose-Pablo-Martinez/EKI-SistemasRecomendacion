// frontend/js/app.js

const routes = {
  '':            () => window.pages.home(),
  '#/':          () => window.pages.home(),
  '#/login':     () => window.pages.login(),
  '#/registro':  () => window.pages.register(),
  '#/onboarding':() => { if (requireAuth()) window.pages.onboarding() },
  '#/feed':      () => { if (requireAuth()) window.pages.feed() },
  '#/buscar':    () => window.pages.busqueda(),
  '#/perfil':    () => { if (requireAuth()) window.pages.perfil() },
  '#/favoritos': () => { if (requireAuth()) window.pages.favoritos() },
  '#/admin':     () => { if (requireAuth()) window.pages.admin() },
};

function renderPage(htmlContent) {
  const root = document.getElementById('app-root');
  root.style.opacity = 0;
  
  setTimeout(() => {
    root.innerHTML = htmlContent;
    // Ejecutar scripts si los hay (opcional para componentes más complejos)
    root.style.transition = 'opacity 400ms cubic-bezier(0, 0, 0.2, 1)';
    root.style.opacity = 1;
  }, 100); // pequeña pausa para asegurar la animación
}

function handleRoute() {
  const hash = window.location.hash.split('?')[0]; // quitar query params si hay
  
  // Rutas dinámicas
  if (hash.startsWith('#/establecimiento/')) {
    const id = hash.split('/')[2];
    window.pages.establecimiento(id);
    return;
  }
  
  const routeAction = routes[hash] || routes['#/'];
  routeAction();
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
window.pages = {}; // Namespace para las páginas

window.addEventListener('hashchange', handleRoute);
window.addEventListener('DOMContentLoaded', async () => {
  appState.subscribe(updateHeader);
  await initState(); // Verifica token y carga usuario si existe
  updateHeader(); // Actualiza UI antes del primer render
  handleRoute();  // Renderiza la página actual
});
