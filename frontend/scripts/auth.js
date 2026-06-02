// frontend/scripts/auth.js

import { appState } from './state.js';

export function parseJWT(token) {
    try {
        const payload = token.split('.')[1];
        return JSON.parse(atob(payload));
    } catch (e) {
        return null;
    }
}

export function isTokenExpired(token) {
    const parsed = parseJWT(token);
    if (!parsed || !parsed.exp) return true;
    return Date.now() >= parsed.exp * 1000;
}

export function saveToken(token) {
    localStorage.setItem('eki_token', token);
}

export function getToken() {
    return localStorage.getItem('eki_token');
}

export function clearToken() {
    localStorage.removeItem('eki_token');
    appState.setUser(null);
}

export function isAuthenticated() {
    const token = getToken();
    return token && !isTokenExpired(token);
}

export function logout() {
    clearToken();
    window.location.hash = '#/';
}

export async function confirmarLogout() {
    // Dynamic import to avoid circular dependency
    const { Modal } = await import('./components/Modal.js');
    Modal.showConfirm({
        title: 'Cerrar Sesión',
        message: '¿Estás seguro de que deseas cerrar sesión?',
        confirmText: 'Cerrar Sesión',
        cancelText: 'Cancelar',
        onConfirm: () => {
            logout();
        }
    });
}

export function requireAuth() {
    if (!isAuthenticated()) {
        window.location.hash = '#/login';
        return false;
    }
    return true;
}
