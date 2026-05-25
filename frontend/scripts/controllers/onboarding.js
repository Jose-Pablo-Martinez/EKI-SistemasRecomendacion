/**
 * Archivo modificado: 2026-05-23
 * Función: Controlador del flujo de bienvenida (Cold Start). 
 * Captura gustos, presupuesto y ubicación inicial.
 */
window.controllers.onboarding = async () => {
    let step = 1;
    let categoriasSeleccionadas = [];
    let preciosSeleccionados = [];
    let categoriasData = [];

    // 1. Cargar Vista HTML base
    const loaded = await renderView('onboarding.html');
    if (!loaded) return;

    // Elementos DOM
    const stepContainer = document.getElementById('step-container');
    const progressBar = document.getElementById('progress-bar');
    const stepIndicator = document.getElementById('step-indicator');
    const prevBtn = document.getElementById('btn-prev');
    const nextBtn = document.getElementById('btn-next');

    const loadCategorias = async () => {
        try {
            categoriasData = await api.getCategorias() || [];
        } catch (err) {
            console.error("Error cargando categorías:", err);
            // Datos de prueba (mocks)
            categoriasData = [
                { id_categoria: 1, nombre: "Yucateca" },
                { id_categoria: 2, nombre: "Antojitos" },
                { id_categoria: 3, nombre: "Mariscos" },
                { id_categoria: 4, nombre: "Postres" },
                { id_categoria: 5, nombre: "Saludable" },
                { id_categoria: 6, nombre: "Café" },
                { id_categoria: 7, nombre: "Gourmet" },
                { id_categoria: 8, nombre: "Rápida" },
            ];
        }
        renderCurrentStep();
    };

    const renderCurrentStep = () => {
        let stepHtml = '';
        if (step === 1) {
            const gruposPredefinidos = {
                "Regionales & Tradicionales": ["yucateca", "mexicana", "antojitos", "cochinita", "pozole", "mercado"],
                "Rápidas & Casuales": ["tacos", "tortas", "rápida", "hamburguesas", "pizza"],
                "Platos Fuertes": ["mariscos", "internacional", "asiática", "carnes"],
                "Postres & Bebidas": ["bebidas", "repostería", "dulces", "panadería", "helados", "café", "aguas", "jugos", "fermentadas"],
                "Fitness & Saludable": ["saludable", "ensaladas", "vegano", "vegetariano", "proteínas"]
            };

            const categoriasAgrupadas = {};
            categoriasData.forEach(c => {
                let grupoEncontrado = "Otras Opciones";
                const nombreCat = c.nombre.toLowerCase();
                for (const [grupo, palabrasClave] of Object.entries(gruposPredefinidos)) {
                    if (palabrasClave.some(palabra => nombreCat.includes(palabra))) {
                        grupoEncontrado = grupo;
                        break;
                    }
                }
                if (!categoriasAgrupadas[grupoEncontrado]) categoriasAgrupadas[grupoEncontrado] = [];
                categoriasAgrupadas[grupoEncontrado].push(c);
            });

            stepHtml = `
                <h2 class="text-2xl xl:text-4xl 2xl:text-5xl font-heading font-bold mb-4 xl:mb-8 text-primary text-center">¿Qué se te antoja?</h2>
                <p class="mb-6 xl:mb-10 text-text-secondary text-sm xl:text-lg 2xl:text-xl text-center">Selecciona las categorías que más te gusten.</p>
                <div class="flex flex-col gap-8 mb-6 w-full max-w-6xl mx-auto text-left">
                    ${Object.entries(categoriasAgrupadas).map(([nombreGrupo, cats]) => `
                        <div class="bg-surface-overlay p-4 xl:p-6 rounded-lg border border-border-default">
                            <h3 class="text-lg xl:text-xl font-bold text-primary mb-4 border-b border-border-strong pb-2">${nombreGrupo}</h3>
                            <div class="flex flex-wrap justify-center gap-4 xl:gap-6 2xl:gap-8">
                                ${cats.map(c => `
                                    <div class="category-card w-full sm:w-[calc(50%-1rem)] md:w-56 xl:w-64 bg-surface-raised border border-border-default rounded-md p-4 xl:p-6 flex flex-col items-center justify-center cursor-pointer hover:border-border-strong hover:-translate-y-1 transition-all ${categoriasSeleccionadas.includes(c.nombre) ? 'border-accent bg-accent-faint scale-[1.02] shadow-sm' : ''}" data-name="${c.nombre}">
                                        <span class="font-bold text-sm xl:text-base 2xl:text-lg text-center ${categoriasSeleccionadas.includes(c.nombre) ? 'text-accent' : 'text-primary'}">${c.nombre}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        } else if (step === 2) {
            const priceIconsMap = {
                "Popular": `
                    <div class="flex justify-center mb-2 text-3xl xl:text-4xl 2xl:text-5xl">
                        <span class="material-symbols-outlined">payments</span>
                    </div>`,
                "Casual": `
                    <div class="flex justify-center mb-2 text-3xl xl:text-4xl 2xl:text-5xl">
                        <span class="material-symbols-outlined">payments</span>
                        <span class="material-symbols-outlined">payments</span>
                    </div>`,
                "Premium": `
                    <div class="flex justify-center mb-2 text-3xl xl:text-4xl 2xl:text-5xl">
                        <span class="material-symbols-outlined">payments</span>
                        <span class="material-symbols-outlined">payments</span>
                        <span class="material-symbols-outlined">payments</span>
                    </div>`
            };

            stepHtml = `
                <h2 class="text-2xl xl:text-4xl 2xl:text-5xl font-heading font-bold mb-4 xl:mb-8 text-primary text-center">¿Cuál es tu presupuesto?</h2>
                <p class="mb-6 xl:mb-10 text-text-secondary text-sm xl:text-lg 2xl:text-xl text-center">Selecciona tus presupuestos preferidos (puedes elegir más de uno).</p>
                <div class="flex flex-wrap justify-center gap-4 xl:gap-8 2xl:gap-10 mb-6 w-full">
                    ${["Popular", "Casual", "Premium"].map(p => `
                        <div class="price-card w-full sm:w-64 xl:w-80 bg-surface-raised border border-border-default rounded-md p-6 xl:p-10 flex flex-col items-center justify-center cursor-pointer hover:border-border-strong hover:-translate-y-1 transition-all ${preciosSeleccionados.includes(p) ? 'border-accent bg-accent-faint scale-[1.02] shadow-sm' : ''}" data-name="${p}">
                            <div class="text-center w-full ${preciosSeleccionados.includes(p) ? 'text-accent' : 'text-primary'}">
                                ${priceIconsMap[p]}
                                <span class="text-sm xl:text-base 2xl:text-lg mt-2 block font-bold">${p}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        } else if (step === 3) {
            stepHtml = `
                <h2 class="text-2xl xl:text-4xl 2xl:text-5xl font-heading font-bold mb-4 xl:mb-8 text-primary text-center">¡Casi listos!</h2>
                <p class="mb-6 xl:mb-10 text-text-secondary text-sm xl:text-lg 2xl:text-xl text-center">Para darte las mejores recomendaciones "cerca de ti", necesitamos conocer tu ubicación.</p>
                <div class="flex flex-col gap-4 xl:gap-6 max-w-md xl:max-w-xl mx-auto mb-6">
                    <button id="btn-location" class="bg-secondary text-white font-bold py-3 xl:py-4 px-4 xl:px-6 rounded hover:bg-secondary-subtle active:scale-95 transition-all w-full flex justify-center items-center gap-2 text-sm xl:text-lg 2xl:text-xl">
                        <svg class="w-5 h-5 xl:w-7 xl:h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                        Usar mi ubicación actual
                    </button>
                    <p id="location-status" class="text-sm xl:text-base text-center h-5 font-bold text-text-secondary"></p>
                </div>
            `;
        }

        // Inyectar estado en el DOM base
        stepContainer.innerHTML = stepHtml;
        progressBar.style.width = step === 1 ? '33.33%' : step === 2 ? '66.66%' : '100%';
        stepIndicator.textContent = `Paso ${step} de 3`;
        
        if (step === 1) prevBtn.classList.add('invisible');
        else prevBtn.classList.remove('invisible');

        if (step === 3) nextBtn.textContent = 'FINALIZAR';
        else nextBtn.textContent = 'SIGUIENTE';

        // Re-vincular eventos para contenido dinámico
        bindDynamicEvents();
    };

    const bindDynamicEvents = () => {
        if (step === 1) {
            document.querySelectorAll('.category-card').forEach(card => {
                card.addEventListener('click', () => {
                    const name = card.dataset.name;
                    if (categoriasSeleccionadas.includes(name)) {
                        categoriasSeleccionadas = categoriasSeleccionadas.filter(n => n !== name);
                    } else {
                        categoriasSeleccionadas.push(name);
                    }
                    renderCurrentStep();
                });
            });
        }

        if (step === 2) {
            document.querySelectorAll('.price-card').forEach(card => {
                card.addEventListener('click', () => {
                    const name = card.dataset.name;
                    if (preciosSeleccionados.includes(name)) {
                        preciosSeleccionados = preciosSeleccionados.filter(n => n !== name);
                    } else {
                        preciosSeleccionados.push(name);
                    }
                    renderCurrentStep();
                });
            });
        }

        if (step === 3) {
            document.getElementById('btn-location').addEventListener('click', async (e) => {
                const btn = e.currentTarget;
                const status = document.getElementById('location-status');
                
                const originalHtml = btn.innerHTML;
                btn.disabled = true;
                btn.innerHTML = `<div class="flex items-center justify-center gap-2"><span class="material-symbols-outlined animate-spin" style="font-size:20px;">progress_activity</span> Obteniendo...</div>`;
                status.textContent = '';
                status.className = 'text-sm xl:text-base text-center h-5 font-bold text-text-secondary';
                
                try {
                    const pos = await new Promise((resolve, reject) => {
                        navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 10000 });
                    });
                    const lat = pos.coords.latitude;
                    const lon = pos.coords.longitude;
                    
                    try {
                        await api.enviarUbicacion(lat, lon);
                    } catch (err) {
                        window.errorHandler.handle(err, 'GeoLocation API');
                        console.warn("Backend error o no disponible, ubicación local guardada", err);
                    }
                    
                    appState.setLocation(lat, lon);
                    status.textContent = '¡Ubicación guardada con éxito!';
                    status.classList.replace('text-text-secondary', 'text-success');
                } catch (err) {
                    status.textContent = 'No se pudo obtener la ubicación (permiso denegado o timeout).';
                    status.classList.replace('text-text-secondary', 'text-accent');
                } finally {
                    btn.disabled = false;
                    btn.innerHTML = originalHtml;
                }
            });
        }
    };

    // Vincular eventos estáticos una vez
    prevBtn.addEventListener('click', () => {
        if (step > 1) { step--; renderCurrentStep(); }
    });

    nextBtn.addEventListener('click', async () => {
        if (step === 1 && categoriasSeleccionadas.length === 0) {
            window.components.Modal.show({ title: 'Selección requerida', message: 'Por favor selecciona al menos una categoría.', type: 'error' });
            return;
        }
        if (step === 2 && preciosSeleccionados.length === 0) {
            window.components.Modal.show({ title: 'Selección requerida', message: 'Por favor selecciona al menos un rango de precio.', type: 'error' });
            return;
        }

        if (step < 3) {
            step++;
            renderCurrentStep();
        } else {
            nextBtn.disabled = true;
            nextBtn.innerHTML = `<div class="flex items-center justify-center gap-2"><span class="material-symbols-outlined animate-spin" style="font-size:20px;">progress_activity</span> Guardando...</div>`;
            try {
                const preferencias = {
                    categorias: categoriasSeleccionadas,
                    precios: preciosSeleccionados
                };
                await api.enviarOnboarding(preferencias);
                if (appState.user) appState.user.perfil_completado = true;
                
                window.components.Modal.show({
                    title: '¡Todo listo!',
                    message: 'Tus preferencias han sido guardadas con éxito.',
                    type: 'success',
                    onClose: () => { window.location.hash = '#/feed'; }
                });
            } catch (err) {
                const userMsg = window.errorHandler.handle(err, 'Onboarding');
                window.components.Modal.show({ title: 'Ocurrió un problema', message: userMsg, type: 'error' });
                nextBtn.disabled = false;
                nextBtn.innerHTML = 'FINALIZAR';
            }
        }
    });

    // Iniciar
    loadCategorias();
};
