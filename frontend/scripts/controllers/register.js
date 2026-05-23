window.controllers.register = async () => {
    // 1. Cargar Vista HTML
    const loaded = await renderView('register.html');
    if (!loaded) return;

    // 2. Controladores y Lógica de Eventos
    const passInput = document.getElementById('password');
    const confirmInput = document.getElementById('password_confirm');
    const errorDiv = document.getElementById('register-form-error');

    // Validación interactiva de contraseñas
    const validatePasswordsMatch = () => {
        if (confirmInput.value && passInput.value !== confirmInput.value) {
            confirmInput.classList.add('border-accent');
            errorDiv.textContent = 'Las contraseñas no coinciden.';
            errorDiv.classList.remove('hidden');
        } else {
            confirmInput.classList.remove('border-accent');
            errorDiv.classList.add('hidden');
        }
    };

    passInput.addEventListener('input', validatePasswordsMatch);
    confirmInput.addEventListener('input', validatePasswordsMatch);

    // Manejo de Formulario
    document.getElementById('register-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const nombre = document.getElementById('nombre').value.trim();
        const apellido = document.getElementById('apellido').value.trim();
        const email = document.getElementById('email').value.trim();
        const password = passInput.value;
        const passwordConfirm = confirmInput.value;
        const submitBtn = e.target.querySelector('button[type="submit"]');
        
        errorDiv.classList.add('hidden');
        
        if (password !== passwordConfirm) {
            errorDiv.textContent = 'Las contraseñas no coinciden.';
            errorDiv.classList.remove('hidden');
            return;
        }

        if (!window.validators.isValidEmail(email)) {
            errorDiv.textContent = 'Por favor ingresa un correo válido.';
            errorDiv.classList.remove('hidden');
            return;
        }

        if (!window.validators.isValidName(nombre) || !window.validators.isValidName(apellido)) {
            errorDiv.textContent = 'Por favor ingresa nombres válidos (sin caracteres especiales ni palabras ofensivas).';
            errorDiv.classList.remove('hidden');
            return;
        }

        submitBtn.disabled = true;
        submitBtn.textContent = 'CREANDO CUENTA...';

        try {
            await api.registro({ nombre, apellido, email, password, tipo_usuario: 'visitante' });
            
            // Auto login
            const loginData = await api.login(email, password);
            saveToken(loginData.access_token);
            await initState();

            window.components.Modal.show({
                title: '¡Registro Exitoso!',
                message: 'Tu cuenta ha sido creada. Ahora vamos a personalizar tu experiencia.',
                type: 'success',
                onClose: () => {
                    window.location.hash = '#/onboarding';
                }
            });

        } catch (err) {
            const userMsg = window.errorHandler.handle(err, 'Registro');
            errorDiv.textContent = userMsg;
            errorDiv.classList.remove('hidden');
            submitBtn.disabled = false;
            submitBtn.textContent = 'CREAR CUENTA';
        }
    });
};
