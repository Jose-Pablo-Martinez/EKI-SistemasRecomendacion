import { api } from '../api.js';
import { appState } from '../state.js';
import { renderView } from '../app.js';
import { errorHandler } from '../utils/errorHandler.js';
import { Modal } from '../components/Modal.js';

export default async function onboardingController() {
    let step = 1;
    let categoriasSeleccionadas = appState.user?.visitante?.vector_preferencias?.categorias_preferidas || [];
    let preciosSeleccionados = appState.user?.visitante?.vector_preferencias?.precios_preferidos || [];
    let isEditing = !!appState.user?.perfil_completado;
    let categoriasData = [];

    const loaded = await renderView('onboarding.html');
    if (!loaded) return;

    const stepContainer = document.getElementById('step-container');
    const progressBar = document.getElementById('progress-bar');
    const stepIndicator = document.getElementById('step-indicator');
    const prevBtn = document.getElementById('btn-prev');
    const nextBtn = document.getElementById('btn-next');
    const cancelBtn = document.getElementById('btn-cancel');

    if (isEditing && cancelBtn) {
        cancelBtn.classList.remove('hidden');
        cancelBtn.addEventListener('click', () => {
            window.location.hash = '#/perfil';
        });
    }

    const loadCategorias = async () => {
        try {
            categoriasData = await api.getCategorias() || [];
        } catch (err) {
            console.error("Error cargando categorías:", err);
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
                        <span class="material-symbols-outlined pointer-events-none">payments</span>
                    </div>`,
                "Casual": `
                    <div class="flex justify-center mb-2 text-3xl xl:text-4xl 2xl:text-5xl">
                        <span class="material-symbols-outlined pointer-events-none">payments</span>
                        <span class="material-symbols-outlined pointer-events-none">payments</span>
                    </div>`,
                "Premium": `
                    <div class="flex justify-center mb-2 text-3xl xl:text-4xl 2xl:text-5xl">
                        <span class="material-symbols-outlined pointer-events-none">payments</span>
                        <span class="material-symbols-outlined pointer-events-none">payments</span>
                        <span class="material-symbols-outlined pointer-events-none">payments</span>
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
            let isLocationActive = false;
            // Check if user has active location in their profile or in the current session
            if (appState.user?.ubicacion_activa || (appState.location && appState.location.lat !== null)) {
                isLocationActive = true;
            }

            if (isLocationActive) {
                stepHtml = `
                    <h2 class="text-2xl xl:text-4xl 2xl:text-5xl font-heading font-bold mb-4 xl:mb-8 text-primary text-center">¡Casi listos!</h2>
                    <div class="flex flex-col gap-4 xl:gap-6 max-w-md xl:max-w-xl mx-auto mb-6 mt-4">
                        <button id="btn-location" class="bg-surface-raised text-accent border border-accent font-bold py-3 xl:py-4 px-4 xl:px-6 rounded hover:bg-accent-faint active:scale-95 transition-all w-full flex justify-center items-center gap-2 text-sm xl:text-lg 2xl:text-xl" data-active="true">
                            <span class="material-symbols-outlined pointer-events-none">location_off</span>
                            Desactivar ubicación
                        </button>
                        <p class="text-text-secondary text-sm xl:text-base text-center px-4">
                            ¿Deseas desactivar el uso de tu ubicación actual?<br>
                            <span class="opacity-80 mt-2 block">Si lo haces, las recomendaciones serán menos precisas y se mostrarán lugares populares de toda la ciudad en lugar de lugares cerca de ti.</span>
                        </p>
                        <p id="location-status" class="text-sm xl:text-base text-center h-5 font-bold text-text-secondary"></p>
                    </div>
                `;
            } else {
                stepHtml = `
                    <h2 class="text-2xl xl:text-4xl 2xl:text-5xl font-heading font-bold mb-4 xl:mb-8 text-primary text-center">¡Casi listos!</h2>
                    <div class="flex flex-col gap-4 xl:gap-6 max-w-md xl:max-w-xl mx-auto mb-6 mt-4">
                        <button id="btn-location" class="bg-secondary text-white font-bold py-3 xl:py-4 px-4 xl:px-6 rounded hover:bg-secondary-subtle active:scale-95 transition-all w-full flex justify-center items-center gap-2 text-sm xl:text-lg 2xl:text-xl" data-active="false">
                            <span class="material-symbols-outlined pointer-events-none">my_location</span>
                            Usar mi ubicación actual
                        </button>
                        <p class="text-text-secondary text-sm xl:text-base text-center px-4">
                            Para darte las mejores recomendaciones "cerca de ti", necesitamos conocer tu ubicación.<br>
                            <span class="opacity-80 mt-2 block">Si decides no compartirla, te mostraremos lugares populares de toda la ciudad.</span>
                        </p>
                        <p id="location-status" class="text-sm xl:text-base text-center h-5 font-bold text-text-secondary"></p>
                    </div>
                `;
            }
        }

        stepContainer.innerHTML = stepHtml;
        progressBar.style.width = step === 1 ? '33.33%' : step === 2 ? '66.66%' : '100%';
        stepIndicator.textContent = `Paso ${step} de 3`;
        
        if (step === 1) prevBtn.classList.add('invisible');
        else prevBtn.classList.remove('invisible');

        if (step === 3) nextBtn.textContent = 'FINALIZAR';
        else nextBtn.textContent = 'SIGUIENTE';

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
                const isActive = btn.dataset.active === "true";
                
                const originalHtml = btn.innerHTML;
                btn.disabled = true;
                btn.innerHTML = `<div class="flex items-center justify-center gap-2"><span class="material-symbols-outlined animate-spin pointer-events-none" style="font-size:20px;">progress_activity</span> Procesando...</div>`;
                status.textContent = '';
                status.className = 'text-sm xl:text-base text-center h-5 font-bold text-text-secondary';
                
                if (isActive) {
                    try {
                        await api.eliminarUbicacion();
                        appState.setLocation(null, null);
                        if (appState.user) appState.user.ubicacion_activa = false;
                        
                        status.textContent = 'Ubicación desactivada con éxito.';
                        status.classList.replace('text-text-secondary', 'text-success');
                        
                        // Re-render to show the inactive state button
                        setTimeout(() => renderCurrentStep(), 1500);
                    } catch (err) {
                        status.textContent = 'Error al desactivar la ubicación.';
                        status.classList.replace('text-text-secondary', 'text-accent');
                        btn.disabled = false;
                        btn.innerHTML = originalHtml;
                    }
                } else {
                    try {
                        const pos = await new Promise((resolve, reject) => {
                            navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 10000 });
                        });
                        const lat = pos.coords.latitude;
                        const lon = pos.coords.longitude;
                        
                        try {
                            await api.enviarUbicacion(lat, lon);
                            if (appState.user) appState.user.ubicacion_activa = true;
                        } catch (err) {
                            errorHandler.handle(err, 'GeoLocation API');
                            console.warn("Backend error o no disponible, ubicación local guardada", err);
                        }
                        
                        appState.setLocation(lat, lon);
                        status.textContent = '¡Ubicación guardada con éxito!';
                        status.classList.replace('text-text-secondary', 'text-success');
                        
                        // Re-render to show the active state button
                        setTimeout(() => renderCurrentStep(), 1500);
                    } catch (err) {
                        status.textContent = 'No se pudo obtener la ubicación (permiso denegado o timeout).';
                        status.classList.replace('text-text-secondary', 'text-accent');
                        btn.disabled = false;
                        btn.innerHTML = originalHtml;
                    }
                }
            });
        }
    };

    prevBtn.addEventListener('click', () => {
        if (step > 1) { step--; renderCurrentStep(); }
    });

    nextBtn.addEventListener('click', async () => {
        if (step === 1 && categoriasSeleccionadas.length === 0) {
            Modal.show({ title: 'Selección requerida', message: 'Por favor selecciona al menos una categoría.', type: 'error' });
            return;
        }
        if (step === 2 && preciosSeleccionados.length === 0) {
            Modal.show({ title: 'Selección requerida', message: 'Por favor selecciona al menos un rango de precio.', type: 'error' });
            return;
        }

        if (step < 3) {
            step++;
            renderCurrentStep();
        } else {
            nextBtn.disabled = true;
            nextBtn.innerHTML = `<div class="flex items-center justify-center gap-2"><span class="material-symbols-outlined animate-spin pointer-events-none" style="font-size:20px;">progress_activity</span> Guardando...</div>`;
            try {
                const preferencias = {
                    categorias: categoriasSeleccionadas,
                    precios: preciosSeleccionados
                };
                
                // Evitar update innecesario
                if (appState.user && appState.user.visitante && appState.user.visitante.vector_preferencias) {
                    const vector = appState.user.visitante.vector_preferencias;
                    const catIguales = JSON.stringify([...categoriasSeleccionadas].sort()) === JSON.stringify([...(vector.categorias_preferidas || [])].sort());
                    const preIguales = JSON.stringify([...preciosSeleccionados].sort()) === JSON.stringify([...(vector.precios_preferidos || [])].sort());
                    if (catIguales && preIguales) {
                        Modal.show({
                            title: '¡Todo listo!',
                            message: 'Tu configuración está guardada y al día.',
                            type: 'success',
                            onClose: () => { window.location.hash = appState.isAdmin ? '#/admin' : '#/feed'; }
                        });
                        return;
                    }
                }

                await api.enviarOnboarding(preferencias);
                if (appState.user) {
                    appState.user.perfil_completado = true;
                    if (!appState.user.visitante) appState.user.visitante = {};
                    appState.user.visitante.vector_preferencias = {
                        categorias_preferidas: categoriasSeleccionadas,
                        precios_preferidos: preciosSeleccionados
                    };
                }
                
                Modal.show({
                    title: '¡Todo listo!',
                    message: 'Tus preferencias han sido guardadas con éxito.',
                    type: 'success',
                    onClose: () => { window.location.hash = appState.isAdmin ? '#/admin' : '#/feed'; }
                });
            } catch (err) {
                const userMsg = errorHandler.handle(err, 'Onboarding');
                Modal.show({ title: 'Ocurrió un problema', message: userMsg, type: 'error' });
                nextBtn.disabled = false;
                nextBtn.innerHTML = 'FINALIZAR';
            }
        }
    });

    loadCategorias();
}
