window.controllers.home = async () => {
    if (appState.isAuthenticated) {
        window.location.hash = '#/feed';
        return;
    }
    await renderView('home.html');
};
