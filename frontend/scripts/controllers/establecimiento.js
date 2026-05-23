window.controllers.establecimiento = (id) => {
    renderPage(`
        <div class="flex-1 flex flex-col items-start p-8 w-full max-w-4xl mx-auto">
            <a href="javascript:history.back()" class="text-secondary hover:text-secondary-hover mb-4 flex items-center gap-2 font-semibold">← Volver</a>
            <h1 class="font-heading text-headline-lg text-primary mb-6">Detalle del Establecimiento ${id ? '#' + id : ''}</h1>
            <div class="w-full bg-surface-raised p-6 rounded-md shadow-sm border border-border-default text-left">
                <p class="text-text-secondary mb-4">[Ficha de establecimiento en desarrollo...]</p>
            </div>
        </div>
    `);
};
