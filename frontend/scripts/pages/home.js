window.pages.home = () => {
    renderPage(`
        <div class="flex-1 flex flex-col items-center justify-center p-8 text-center eki-texture-bg relative w-full overflow-hidden">
            <h1 class="font-heading text-display-lg text-primary mb-4 relative z-10">Descubre la verdadera esencia gastronómica</h1>
            <p class="font-sans text-body-lg text-text-secondary max-w-2xl mb-8 relative z-10">Recomendaciones personalizadas con inteligencia artificial para encontrar las joyas culinarias de la ciudad.</p>
            <a href="#/registro" class="bg-accent text-white px-8 py-3 rounded-md font-semibold text-label-lg hover:bg-accent-hover transition-colors shadow relative z-10">Empezar ahora</a>
        </div>
    `);
};
