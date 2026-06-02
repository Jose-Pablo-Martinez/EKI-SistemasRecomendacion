export const Modal = {
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
    },

    showConfirm(options) {
        const { title, message, onConfirm, onCancel, confirmText = 'Aceptar', cancelText = 'Cancelar' } = options;
        
        const existingModal = document.getElementById('global-modal');
        if (existingModal) existingModal.remove();

        const modalHtml = `
            <div id="global-modal" class="fixed inset-0 z-50 flex items-center justify-center bg-primary/50 backdrop-blur-sm opacity-0 transition-opacity duration-300">
                <div class="bg-surface-raised p-8 rounded-md shadow-lg border-t-4 border-accent max-w-sm xl:max-w-lg 2xl:max-w-xl w-full mx-4 transform scale-95 transition-transform duration-300">
                    <h2 class="text-2xl xl:text-3xl font-heading font-bold mb-4 text-accent">${title}</h2>
                    <p class="text-text-secondary mb-8 text-base xl:text-lg 2xl:text-xl">${message}</p>
                    <div class="flex gap-4">
                        <button id="global-modal-cancel" class="bg-surface-dim text-text-primary font-bold py-3 px-6 rounded hover:bg-surface transition-colors w-full uppercase tracking-wider">${cancelText}</button>
                        <button id="global-modal-confirm" class="bg-accent text-white font-bold py-3 px-6 rounded hover:bg-accent/90 transition-colors w-full uppercase tracking-wider">${confirmText}</button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modalEl = document.getElementById('global-modal');
        const modalContent = modalEl.querySelector('div');
        
        requestAnimationFrame(() => {
            modalEl.classList.remove('opacity-0');
            modalContent.classList.remove('scale-95');
        });

        const closeModal = () => {
            modalEl.classList.add('opacity-0');
            modalContent.classList.add('scale-95');
            setTimeout(() => {
                modalEl.remove();
            }, 300);
        };

        document.getElementById('global-modal-cancel').addEventListener('click', () => {
            closeModal();
            if (onCancel) onCancel();
        });

        document.getElementById('global-modal-confirm').addEventListener('click', () => {
            closeModal();
            if (onConfirm) onConfirm();
        });
    }
};
