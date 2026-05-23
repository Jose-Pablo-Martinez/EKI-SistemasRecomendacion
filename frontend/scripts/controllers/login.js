window.controllers.login = async () => {
    // 1. Cargar Vista HTML mediante fetch
    const loaded = await renderView('login.html');
    if (!loaded) return;

    // 2. Controladores y Lógica de Eventos
    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        const errorDiv = document.getElementById('login-form-error');
        const submitBtn = e.target.querySelector('button[type="submit"]');
        
        errorDiv.classList.add('hidden');
        submitBtn.disabled = true;
        submitBtn.textContent = 'CARGANDO...';
        
        if (!email || !password) {
            errorDiv.textContent = 'Por favor ingresa tu correo y contraseña.';
            errorDiv.classList.remove('hidden');
            submitBtn.disabled = false;
            submitBtn.textContent = 'INGRESAR';
            return;
        }
        
        if (!window.validators.isValidEmail(email)) {
            errorDiv.textContent = 'Por favor ingresa un correo válido.';
            errorDiv.classList.remove('hidden');
            submitBtn.disabled = false;
            submitBtn.textContent = 'INGRESAR';
            return;
        }

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
            errorDiv.textContent = userMsg;
            errorDiv.classList.remove('hidden');
            submitBtn.disabled = false;
            submitBtn.textContent = 'INGRESAR';
        }
    });
};
