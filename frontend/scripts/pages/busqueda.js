window.pages.busqueda = () => {
    renderPage(`
        <div class="flex-1 flex flex-col items-center p-8 w-full max-w-5xl mx-auto">
            <h1 class="font-heading text-headline-lg text-primary mb-6">Buscar</h1>
            <div class="w-full max-w-2xl bg-surface-raised p-4 rounded-md shadow-sm border border-border-default mb-8">
                <input type="text" placeholder="¿Qué se te antoja hoy?" class="w-full bg-surface-sunken border border-border-default text-text-primary rounded-md px-4 py-3 focus:outline-none focus:border-border-focus focus:ring-2 focus:ring-border-focus/30" />
            </div>
            <div class="w-full text-left">
                <p class="text-text-secondary mb-4">[Resultados de búsqueda en desarrollo...]</p>
            </div>
        </div>
    `);
};
