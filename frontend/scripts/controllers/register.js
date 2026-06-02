/**
 * Archivo modificado: 2026-05-23
 * Función: Controlador de la vista de registro. 
 * Maneja la creación de nuevas cuentas y auto-login.
 */
import { api } from '../api.js';
import { initState } from '../state.js';
import { saveToken } from '../auth.js';
import { renderView } from '../app.js';
import { errorHandler } from '../utils/errorHandler.js';
import { validators } from '../utils/validators.js';
import { Modal } from '../components/Modal.js';

export default async function registerController() {
    // 1. Cargar Vista HTML
    const loaded = await renderView('register.html');
    if (!loaded) return;

    // 2. Controladores y Lógica de Eventos
    const nombreInput = document.getElementById('nombre');
    const apellidoInput = document.getElementById('apellido');
    const emailInput = document.getElementById('email');
    const passInput = document.getElementById('password');
    const confirmInput = document.getElementById('password_confirm');
    
    const errorDiv = document.getElementById('register-form-error');
    const nombreError = document.getElementById('nombre-error');
    const apellidoError = document.getElementById('apellido-error');
    const emailError = document.getElementById('email-error');
    const passError = document.getElementById('password-error');
    const confirmError = document.getElementById('password_confirm-error');

    // Alternar visibilidad de contraseña
    const setupToggle = (btnId, inputElement, iconId) => {
        const btn = document.getElementById(btnId);
        const icon = document.getElementById(iconId);
        if (!btn || !icon || !inputElement) return;
        btn.addEventListener('click', () => {
            if (inputElement.type === 'password') {
                inputElement.type = 'text';
                icon.textContent = 'visibility';
            } else {
                inputElement.type = 'password';
                icon.textContent = 'visibility_off';
            }
        });
    };
    setupToggle('toggle-password', passInput, 'icon-password');
    setupToggle('toggle-password-confirm', confirmInput, 'icon-password-confirm');

    const clearErrors = () => {
        [errorDiv, nombreError, apellidoError, emailError, passError, confirmError].forEach(el => {
            if(el) el.classList.add('hidden')
        });
        [nombreInput, apellidoInput, emailInput, passInput, confirmInput].forEach(el => {
            if(el) el.classList.remove('border-accent')
        });
    };

    const showError = (element, message, input) => {
        if (!element) return;
        element.textContent = message;
        element.classList.remove('hidden');
        if (input) input.classList.add('border-accent');
    };

    // Validación interactiva de contraseñas
    const validatePasswordsMatch = () => {
        if (confirmInput.value && passInput.value !== confirmInput.value) {
            showError(confirmError, 'Las contraseñas no coinciden.', confirmInput);
        } else {
            if (confirmError) confirmError.classList.add('hidden');
            if (confirmInput) confirmInput.classList.remove('border-accent');
        }
    };

    if (passInput) passInput.addEventListener('input', validatePasswordsMatch);
    if (confirmInput) confirmInput.addEventListener('input', validatePasswordsMatch);

    // Manejo de Formulario
    const form = document.getElementById('register-form');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const nombre = nombreInput.value.trim();
            const apellido = apellidoInput.value.trim();
            const email = emailInput.value.trim();
            const password = passInput.value;
            const passwordConfirm = confirmInput.value;
            const submitBtn = e.target.querySelector('button[type="submit"]');
            
            clearErrors();
            
            let hasError = false;

            if (!nombre) {
                showError(nombreError, 'El nombre es requerido.', nombreInput);
                hasError = true;
            } else if (!validators.isValidName(nombre)) {
                showError(nombreError, 'Nombre inválido.', nombreInput);
                hasError = true;
            }

            if (!apellido) {
                showError(apellidoError, 'El apellido es requerido.', apellidoInput);
                hasError = true;
            } else if (!validators.isValidName(apellido)) {
                showError(apellidoError, 'Apellido inválido.', apellidoInput);
                hasError = true;
            }

            if (!email) {
                showError(emailError, 'El correo es requerido.', emailInput);
                hasError = true;
            } else if (!validators.isValidEmail(email)) {
                showError(emailError, 'Por favor ingresa un correo válido.', emailInput);
                hasError = true;
            }

            if (!password) {
                showError(passError, 'La contraseña es requerida.', passInput);
                hasError = true;
            } else if (password.length < 8) {
                showError(passError, 'La contraseña debe tener al menos 8 caracteres.', passInput);
                hasError = true;
            }

            if (!passwordConfirm) {
                showError(confirmError, 'Confirma tu contraseña.', confirmInput);
                hasError = true;
            } else if (password !== passwordConfirm) {
                showError(confirmError, 'Las contraseñas no coinciden.', confirmInput);
                hasError = true;
            }

            if (hasError) return;

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<div class="flex items-center justify-center gap-2"><span class="material-symbols-outlined animate-spin pointer-events-none">progress_activity</span> Creando cuenta...</div>';

            try {
                await api.registro({ nombre, apellido, email, password, tipo_usuario: 'visitante' });
                
                // Autenticación automática
                const loginData = await api.login(email, password);
                saveToken(loginData.access_token);
                await initState();

                Modal.show({
                    title: '¡Registro Exitoso!',
                    message: 'Tu cuenta ha sido creada. Ahora vamos a personalizar tu experiencia.',
                    type: 'success',
                    onClose: () => {
                        window.location.hash = '#/onboarding';
                    }
                });

            } catch (err) {
                const userMsg = errorHandler.handle(err, 'Registro');
                if (errorDiv) {
                    errorDiv.textContent = userMsg;
                    errorDiv.classList.remove('hidden');
                }
                submitBtn.disabled = false;
                submitBtn.textContent = 'CREAR CUENTA';
            }
        });
    }
}
