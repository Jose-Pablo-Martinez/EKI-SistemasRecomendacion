/**
 * Archivo modificado: 2026-05-23
 * Función: Controlador de la vista de inicio de sesión. 
 * Maneja la validación de credenciales y la autenticación.
 */
window.controllers.login = async () => {
    // 1. Cargar Vista HTML mediante fetch
    const loaded = await renderView('login.html');
    if (!loaded) return;

    // 2. Controladores y Lógica de Eventos
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const errorDiv = document.getElementById('login-form-error');
    const emailError = document.getElementById('email-error');
    const passwordError = document.getElementById('password-error');
    
    // Toggle Password Visibility
    const togglePasswordBtn = document.getElementById('toggle-password');
    const iconPassword = document.getElementById('icon-password');
    togglePasswordBtn.addEventListener('click', () => {
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            iconPassword.textContent = 'visibility';
        } else {
            passwordInput.type = 'password';
            iconPassword.textContent = 'visibility_off';
        }
    });

    const clearErrors = () => {
        errorDiv.classList.add('hidden');
        emailError.classList.add('hidden');
        passwordError.classList.add('hidden');
        emailInput.classList.remove('border-accent');
        passwordInput.classList.remove('border-accent');
    };

    const showError = (element, message, input) => {
        element.textContent = message;
        element.classList.remove('hidden');
        if (input) input.classList.add('border-accent');
    };

    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = emailInput.value.trim();
        const password = passwordInput.value;
        const submitBtn = e.target.querySelector('button[type="submit"]');
        
        clearErrors();
        
        let hasError = false;
        
        if (!email) {
            showError(emailError, 'El correo es requerido.', emailInput);
            hasError = true;
        } else if (!window.validators.isValidEmail(email)) {
            showError(emailError, 'Por favor ingresa un correo válido.', emailInput);
            hasError = true;
        }
        
        if (!password) {
            showError(passwordError, 'La contraseña es requerida.', passwordInput);
            hasError = true;
        }

        if (hasError) return;

        submitBtn.disabled = true;
        submitBtn.innerHTML = '<div class="flex items-center justify-center gap-2"><span class="material-symbols-outlined animate-spin">progress_activity</span> Cargando...</div>';

        try {
            const data = await api.login(email, password);
            saveToken(data.access_token);
            await initState(); // Reload user state
            
            if (appState.user && appState.user.perfil_completado) {
                window.location.hash = '#/feed';
            } else {
                window.location.hash = '#/onboarding';
            }
        } catch (err) {
            const userMsg = window.errorHandler.handle(err, 'Login');
            if (err.status === 401) {
                showError(emailError, userMsg, emailInput);
                showError(passwordError, '', passwordInput); // Solo borde para password
            } else {
                errorDiv.textContent = userMsg;
                errorDiv.classList.remove('hidden');
            }
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'INGRESAR';
        }
    });
};
