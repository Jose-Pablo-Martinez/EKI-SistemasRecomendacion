// frontend/js/utils.js

window.pages = {}; // Inicializar namespace para páginas

function solicitarUbicacion() {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocalización no soportada'));
        return;
      }
      navigator.geolocation.getCurrentPosition(
        (pos) => resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
        (err) => reject(err),
        { enableHighAccuracy: true, timeout: 10000 }
      );
    });
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `p-4 bg-surface-raised border border-border-default shadow text-sm rounded-md transition-all duration-300 transform translate-x-full opacity-0 max-w-sm w-full`;
    
    // Variantes según type
    if (type === 'info') toast.classList.add('border-l-4', 'border-l-secondary');
    else if (type === 'success') toast.classList.add('border-l-4', 'border-l-success');
    else if (type === 'warning') toast.classList.add('border-l-4', 'border-l-warning');
    else if (type === 'error') toast.classList.add('border-l-4', 'border-l-accent');

    toast.innerText = message;
    container.appendChild(toast);

    // Animación de entrada
    requestAnimationFrame(() => {
        toast.classList.remove('translate-x-full', 'opacity-0');
        toast.classList.add('translate-x-0', 'opacity-100');
    });

    // Remover después de 3s
    setTimeout(() => {
        toast.classList.remove('translate-x-0', 'opacity-100');
        toast.classList.add('translate-x-full', 'opacity-0');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
