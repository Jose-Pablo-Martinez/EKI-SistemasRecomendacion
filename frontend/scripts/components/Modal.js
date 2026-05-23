window.components = window.components || {};
window.components.Modal = {
    show(options) {
        const { title, message, type = 'info', onClose } = options;
        
        const existingModal = document.getElementById('global-modal');
        if (existingModal) existingModal.remove();

        let iconColor = 'text-primary';
        let borderColor = 'border-border-default';
        
        if (type === 'success') {
            iconColor = 'text-success';
            borderColor = 'border-success';
        } else if (type === 'error') {
            iconColor = 'text-accent';
            borderColor = 'border-accent';
        }

        const modalHtml = `
            <div id="global-modal" class="fixed inset-0 z-50 flex items-center justify-center bg-primary/50 backdrop-blur-sm opacity-0 transition-opacity duration-300">
                <div class="bg-surface-raised p-8 rounded-md shadow-lg border-t-4 ${borderColor} max-w-sm xl:max-w-lg 2xl:max-w-xl w-full mx-4 transform scale-95 transition-transform duration-300">
                    <h2 class="text-2xl xl:text-3xl font-heading font-bold mb-4 ${iconColor}">${title}</h2>
                    <p class="text-text-secondary mb-8 text-base xl:text-lg 2xl:text-xl">${message}</p>
                    <button id="global-modal-close" class="bg-primary-muted text-white font-bold py-3 px-6 rounded hover:bg-primary transition-colors w-full uppercase tracking-wider">Aceptar</button>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modalEl = document.getElementById('global-modal');
        const modalContent = modalEl.querySelector('div');
        
        // Trigger animaciones
        requestAnimationFrame(() => {
            modalEl.classList.remove('opacity-0');
            modalContent.classList.remove('scale-95');
        });

        document.getElementById('global-modal-close').addEventListener('click', () => {
            modalEl.classList.add('opacity-0');
            modalContent.classList.add('scale-95');
            setTimeout(() => {
                modalEl.remove();
                if (onClose) onClose();
            }, 300);
        });
    }
};
