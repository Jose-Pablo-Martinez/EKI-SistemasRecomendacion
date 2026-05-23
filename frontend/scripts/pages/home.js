window.pages.home = () => {
    renderPage(`
        <div id="home-hero-section" class="flex-1 flex flex-col items-center justify-center p-8 py-12 md:py-24 2xl:py-32 text-center eki-texture-bg relative w-full">
            <h1 class="font-heading text-display-lg 2xl:text-display-xl text-primary mb-4 relative z-10 transition-all duration-300">Descubre la verdadera esencia gastronómica</h1>
            <p class="font-sans text-body-lg 2xl:text-2xl text-text-secondary max-w-2xl 2xl:max-w-4xl mb-8 relative z-10 transition-all duration-300">Encuentra las joyas culinarias de la ciudad, recomendadas especialmente para tus gustos.</p>
            <a href="#/registro" id="btn-empezar-ahora" class="bg-accent text-white px-8 py-3 2xl:px-12 2xl:py-4 2xl:text-xl rounded-md font-semibold text-label-lg hover:bg-accent-hover transition-colors shadow relative z-10">Empezar ahora</a>
        </div>
    `);
};
