// frontend/js/auth.js

function parseJWT(token) {
    try {
        const payload = token.split('.')[1];
        return JSON.parse(atob(payload));
    } catch (e) {
        return null;
    }
}

function isTokenExpired(token) {
    const parsed = parseJWT(token);
    if (!parsed || !parsed.exp) return true;
    return Date.now() >= parsed.exp * 1000;
}

function saveToken(token) {
    localStorage.setItem('eki_token', token);
}

function getToken() {
    return localStorage.getItem('eki_token');
}

function clearToken() {
    localStorage.removeItem('eki_token');
    appState.setUser(null);
}

function isAuthenticated() {
    const token = getToken();
    return token && !isTokenExpired(token);
}

function logout() {
    clearToken();
    window.location.hash = '#/';
}

function confirmarLogout() {
    if (window.components && window.components.Modal) {
        window.components.Modal.showConfirm({
            title: 'Cerrar Sesión',
            message: '¿Estás seguro de que deseas cerrar sesión?',
            confirmText: 'Cerrar Sesión',
            cancelText: 'Cancelar',
            onConfirm: () => {
                logout();
            }
        });
    } else {
        if (confirm('¿Estás seguro de que deseas cerrar sesión?')) {
            logout();
        }
    }
}

function requireAuth() {
    if (!isAuthenticated()) {
        window.location.hash = '#/login';
        return false;
    }
    return true;
}
