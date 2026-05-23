window.pages.favoritos = () => {
    renderPage(`
        <div class="flex-1 flex flex-col items-start p-8 w-full max-w-5xl mx-auto">
            <h1 class="font-heading text-headline-lg text-primary mb-6">Mis Favoritos</h1>
            <div class="w-full bg-surface-raised p-6 rounded-md shadow-sm border border-border-default text-left">
                <p class="text-text-secondary mb-4">[Lista de favoritos en desarrollo...]</p>
            </div>
        </div>
    `);
};
