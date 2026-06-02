import { appState } from '../state.js';
import { renderView } from '../app.js';

export default async function homeController() {
    if (appState.isAuthenticated) {
        window.location.hash = '#/feed';
        return;
    }
    await renderView('home.html');
}
