import { api } from '../api.js';
import { showToast } from '../utils.js';
import { renderView } from '../app.js';
import { EkiTimePicker } from '../components/timepicker.js';

let form;
let btnGps;
let btnSubmit;
let map;
let marker;
let checkTimeout;

export default async function contribucionController() {
  await renderView('contribucion.html');
  
  const token = localStorage.getItem('eki_token');
  if (!token) {
    showToast('Inicia sesión para contribuir.', 'error');
    window.location.hash = '#/login';
    return;
  }

  form = document.getElementById('contribucion-form');
  btnGps = document.getElementById('btn-gps');
  btnSubmit = document.getElementById('btn-submit');

  await cargarColonias();
  initMapa();
  setupMenuDinamico();
  setupValidations();

  if (btnGps) {
    btnGps.addEventListener('click', handleGPS);
  }

  if (form) {
    form.addEventListener('submit', handleSubmit);
  }

  setupHorariosUI();
}

function setupHorariosUI() {
  const pickerContainers = document.querySelectorAll('.eki-timepicker-container');
  pickerContainers.forEach(container => {
    new EkiTimePicker(container);
    container.addEventListener('change', () => validarFilaHorario(container.closest('tr')));
  });

  const btns = document.querySelectorAll('.btn-estado');
  btns.forEach(btn => {
    btn.addEventListener('click', () => {
      const isAbierto = btn.dataset.abierto === 'true';
      if (isAbierto) {
        btn.dataset.abierto = 'false';
        btn.textContent = 'Cerrado';
        btn.classList.remove('bg-success');
        btn.classList.add('bg-accent');
        
        // Disable timepickers
        const row = btn.closest('tr');
        row.querySelectorAll('.eki-timepicker-container').forEach(c => { 
          c.classList.add('opacity-50', 'pointer-events-none');
          c.querySelectorAll('select').forEach(s => s.disabled = true);
        });
      } else {
        btn.dataset.abierto = 'true';
        btn.textContent = 'Abierto';
        btn.classList.remove('bg-accent');
        btn.classList.add('bg-success');

        // Enable timepickers
        const row = btn.closest('tr');
        row.querySelectorAll('.eki-timepicker-container').forEach(c => { 
          c.classList.remove('opacity-50', 'pointer-events-none');
          c.querySelectorAll('select').forEach(s => s.disabled = false);
        });
        validarFilaHorario(row);
      }
    });
  });
}

function validarFilaHorario(row) {
  const isAbierto = row.querySelector('.btn-estado').dataset.abierto === 'true';
  const apContainer = row.querySelector('.eki-timepicker-container.apertura');
  const ciContainer = row.querySelector('.eki-timepicker-container.cierre');
  
  const selects = row.querySelectorAll('select');
  
  if (!isAbierto) {
    selects.forEach(s => {
      s.classList.remove('border-accent', 'text-accent');
      s.classList.add('border-border-default', 'text-text-primary');
    });
    const errorRow = row.nextElementSibling;
    if (errorRow && errorRow.classList.contains('error-row')) {
      errorRow.classList.add('hidden');
      row.classList.add('border-b');
    }
    return;
  }

  const hAp = apContainer.querySelector('.eki-hour-select').value;
  const mAp = apContainer.querySelector('.eki-minute-select').value;
  const hCi = ciContainer.querySelector('.eki-hour-select').value;
  const mCi = ciContainer.querySelector('.eki-minute-select').value;

  let errorRow = row.nextElementSibling;
  if (!errorRow || !errorRow.classList.contains('error-row')) {
    errorRow = document.createElement('tr');
    errorRow.className = 'error-row hidden border-b border-border-faint';
    errorRow.innerHTML = `<td colspan="4" class="py-1 text-center pb-3"><p class="text-xs text-accent font-medium">La apertura y cierre no pueden ser idénticas.</p></td>`;
    row.parentNode.insertBefore(errorRow, row.nextSibling);
  }

  // Si ambas horas están completamente llenas y son idénticas, es un error visual
  if (hAp && mAp && hCi && mCi && hAp === hCi && mAp === mCi) {
    selects.forEach(s => {
      s.classList.remove('border-border-default', 'text-text-primary');
      s.classList.add('border-accent', 'text-accent');
    });
    row.classList.remove('border-b'); // Quitar borde de la fila original para unirla visualmente con la del error
    errorRow.classList.remove('hidden');
  } else {
    selects.forEach(s => {
      s.classList.remove('border-accent', 'text-accent');
      s.classList.add('border-border-default', 'text-text-primary');
    });
    row.classList.add('border-b');
    errorRow.classList.add('hidden');
  }
}

async function cargarColonias() {
  const select = document.getElementById('id_colonia');
  if (!select) return;

  try {
    const colonias = await api.getColonias();
    select.innerHTML = '<option value="" selected>No especificar</option>';
    colonias.forEach(c => {
      const option = document.createElement('option');
      option.value = c.id_colonia;
      option.textContent = c.nombre;
      select.appendChild(option);
    });
  } catch (error) {
    console.error('Error cargando colonias:', error);
    select.innerHTML = '<option value="" selected>No se pudieron cargar</option>';
  }
}

function initMapa() {
  const latInput = document.getElementById('latitud');
  const lngInput = document.getElementById('longitud');

  // Centro de Mérida por defecto
  let initialLat = 20.9674;
  let initialLng = -89.5926;

  map = L.map('mapa-ubicacion').setView([initialLat, initialLng], 13);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap &copy; CARTO'
  }).addTo(map);

  marker = L.marker([initialLat, initialLng], { draggable: true }).addTo(map);

  // Al arrastrar el pin, actualizar inputs
  marker.on('dragend', function (e) {
    const position = marker.getLatLng();
    latInput.value = position.lat.toFixed(6);
    lngInput.value = position.lng.toFixed(6);
    validarCampo(latInput);
  });

  // Al escribir manualmente (poco común pero posible), mover el pin
  const syncMapToInput = () => {
    const lat = parseFloat(latInput.value);
    const lng = parseFloat(lngInput.value);
    if (!isNaN(lat) && !isNaN(lng)) {
      marker.setLatLng([lat, lng]);
      map.panTo([lat, lng]);
    }
  };

  latInput.addEventListener('change', syncMapToInput);
  lngInput.addEventListener('change', syncMapToInput);
}

function handleGPS() {
  if (!navigator.geolocation) {
    showToast('Tu navegador no soporta geolocalización', 'error');
    return;
  }

  const originalText = btnGps.innerHTML;
  btnGps.innerHTML = '<span class="material-symbols-outlined animate-spin">autorenew</span> Localizando...';
  btnGps.disabled = true;

  navigator.geolocation.getCurrentPosition(
    (position) => {
      const lat = position.coords.latitude;
      const lng = position.coords.longitude;
      document.getElementById('latitud').value = lat.toFixed(6);
      document.getElementById('longitud').value = lng.toFixed(6);
      
      marker.setLatLng([lat, lng]);
      map.setView([lat, lng], 17);
      
      showToast('Ubicación obtenida exitosamente', 'success');
      btnGps.innerHTML = originalText;
      btnGps.disabled = false;
      validarCampo(document.getElementById('latitud'));
    },
    (error) => {
      console.error('Error de GPS:', error);
      showToast('No pudimos obtener tu ubicación. Por favor, ingresa las coordenadas o mueve el pin.', 'error');
      btnGps.innerHTML = originalText;
      btnGps.disabled = false;
    },
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
  );
}

function setupMenuDinamico() {
  const container = document.getElementById('platillos-container');
  const btnAdd = document.getElementById('btn-add-platillo');
  let platilloCount = 0;

  btnAdd.addEventListener('click', () => {
    platilloCount++;
    const id = `platillo-${Date.now()}`;
    const row = document.createElement('div');
    row.className = 'flex items-start gap-3 bg-surface-dim p-3 rounded border border-border-default platillo-row fade-in';
    row.innerHTML = `
      <div class="flex-1 grid grid-cols-1 md:grid-cols-2 gap-3">
        <input type="text" placeholder="Nombre del platillo (ej. Torta de Pastor)" required class="w-full bg-surface border border-border-default text-text-primary rounded px-3 py-2 text-sm focus:ring-1 focus:ring-accent platillo-nombre">
        <input type="number" step="0.01" placeholder="Precio ($ MXN)" class="w-full bg-surface border border-border-default text-text-primary rounded px-3 py-2 text-sm focus:ring-1 focus:ring-accent platillo-precio">
      </div>
      <button type="button" class="text-text-tertiary hover:text-red-500 transition-colors p-2 remove-platillo" aria-label="Eliminar platillo">
        <span class="material-symbols-outlined">delete</span>
      </button>
    `;
    
    row.querySelector('.remove-platillo').addEventListener('click', () => {
      row.remove();
    });
    
    container.appendChild(row);
  });
}

function setupValidations() {
  const nombreInput = document.getElementById('nombre');
  nombreInput.addEventListener('blur', () => validarCampo(nombreInput));
  
  // Realtime debounce check for duplicates
  nombreInput.addEventListener('input', () => {
    clearTimeout(checkTimeout);
    checkTimeout = setTimeout(async () => {
      if (nombreInput.value.length < 4) return;
      try {
        const res = await api.autocompletar(nombreInput.value);
        const warning = document.getElementById('duplicate-warning');
        if (res.sugerencias && res.sugerencias.length > 0) {
          warning.classList.remove('hidden');
        } else {
          warning.classList.add('hidden');
        }
      } catch (e) {
        // Ignorar
      }
    }, 800);
  });

  const inputsReq = ['direccion_texto', 'tipo_establecimiento'];
  inputsReq.forEach(id => {
    const el = document.getElementById(id);
    if(el) el.addEventListener('blur', () => validarCampo(el));
  });
}

function validarCampo(el) {
  let hasError = false;
  let msg = '';
  
  if (el.hasAttribute('required') && !el.value.trim()) {
    hasError = true;
    msg = 'Este campo es obligatorio.';
  }

  if (el.id === 'nombre' && el.value.trim()) {
    // Basic anti-XSS y caracteres raros
    const regexMalicious = /[<>]/;
    if (regexMalicious.test(el.value)) {
      hasError = true;
      msg = 'El nombre contiene caracteres no permitidos.';
    }
  }

  const errorEl = document.getElementById(`error-${el.id}`) || document.getElementById(`error-coordenadas`);
  if (errorEl && el.id !== 'latitud' && el.id !== 'longitud') {
    if (hasError) {
      errorEl.textContent = msg;
      errorEl.classList.remove('hidden');
      el.classList.add('border-accent');
    } else {
      errorEl.classList.add('hidden');
      el.classList.remove('border-accent');
    }
  } else if (el.id === 'latitud' || el.id === 'longitud') {
    const lat = document.getElementById('latitud').value;
    const lng = document.getElementById('longitud').value;
    const coordErr = document.getElementById('error-coordenadas');
    if (!lat || !lng || isNaN(lat) || isNaN(lng)) {
      hasError = true;
      if (coordErr) coordErr.classList.remove('hidden');
    } else {
      if (coordErr) coordErr.classList.add('hidden');
    }
  }

  return !hasError;
}

function parseHorarios() {
  const rows = document.querySelectorAll('#tabla-horarios tbody tr');
  const horarios = [];
  let algunCerrado = false;
  let algunAbiertoConHora = false;

  rows.forEach(row => {
    const dia = parseInt(row.dataset.dia);
    const diaNombre = row.querySelector('td').textContent.trim();
    const isAbierto = row.querySelector('.btn-estado').dataset.abierto === 'true';
    
    const apContainer = row.querySelector('.eki-timepicker-container.apertura');
    const ciContainer = row.querySelector('.eki-timepicker-container.cierre');
    
    const hAp = apContainer.querySelector('.eki-hour-select').value;
    const mAp = apContainer.querySelector('.eki-minute-select').value;
    const hCi = ciContainer.querySelector('.eki-hour-select').value;
    const mCi = ciContainer.querySelector('.eki-minute-select').value;

    if (!isAbierto) {
      horarios.push({ dia_semana: dia, cerrado: true });
      algunCerrado = true;
    } else if (hAp && mAp && hCi && mCi) {
      if (hAp === hCi && mAp === mCi) {
        throw new Error(`Incongruencia: La hora de apertura y cierre no pueden ser idénticas el día ${diaNombre}.`);
      }
      horarios.push({
        dia_semana: dia,
        hora_apertura: `${hAp}:${mAp}:00`,
        hora_cierre: `${hCi}:${mCi}:00`,
        cerrado: false
      });
      algunAbiertoConHora = true;
    }
  });

  // Si el usuario no tocó nada (todos abiertos pero sin horas), devolvemos array vacío
  if (!algunCerrado && !algunAbiertoConHora) {
    return [];
  }

  return horarios;
}

function parsePlatillos() {
  const rows = document.querySelectorAll('.platillo-row');
  const platillos = [];
  rows.forEach(row => {
    const nombre = row.querySelector('.platillo-nombre').value.trim();
    const precio = row.querySelector('.platillo-precio').value;
    if (nombre) {
      platillos.push({
        nombre: nombre,
        precio: precio ? parseFloat(precio) : null,
        disponible: true
      });
    }
  });
  return platillos;
}

async function handleSubmit(event) {
  event.preventDefault();

  // Validar todos
  const isValidNombre = validarCampo(document.getElementById('nombre'));
  const isValidDir = validarCampo(document.getElementById('direccion_texto'));
  const isValidTipo = validarCampo(document.getElementById('tipo_establecimiento'));
  const isValidCoord = validarCampo(document.getElementById('latitud'));

  if (!isValidNombre || !isValidDir || !isValidTipo || !isValidCoord) {
    showToast('Por favor corrige los errores del formulario.', 'error');
    return;
  }

  const formData = new FormData(form);
  const data = {
    nombre: formData.get('nombre').trim(),
    descripcion: formData.get('descripcion').trim() || null,
    tipo_establecimiento: formData.get('tipo_establecimiento'),
    direccion_texto: formData.get('direccion_texto').trim(),
    latitud: parseFloat(formData.get('latitud')),
    longitud: parseFloat(formData.get('longitud')),
    id_colonia: formData.get('id_colonia') ? parseInt(formData.get('id_colonia')) : null
  };

  let horarios = [];
  try {
    horarios = parseHorarios();
  } catch (err) {
    showToast(err.message, 'error');
    return;
  }
  
  const platillos = parsePlatillos();

  // Bloquear UI y mostrar progreso
  document.getElementById('form-actions').classList.add('hidden');
  const progressDiv = document.getElementById('submit-progress');
  const progressBar = document.getElementById('progress-bar');
  const progressText = document.getElementById('progress-text');
  progressDiv.classList.remove('hidden');

  try {
    // 1. Crear Establecimiento
    progressText.textContent = 'Creando establecimiento...';
    progressBar.style.width = '30%';
    const est = await api.crearEstablecimiento(data);
    const id = est.id_establecimiento;

    // 2. Horarios
    if (horarios.length > 0) {
      progressText.textContent = 'Guardando horarios...';
      progressBar.style.width = '60%';
      // Inyectar el id del establecimiento a cada horario
      horarios.forEach(h => h.id_establecimiento = id);
      await api.actualizarHorarios(id, horarios);
    }

    // 3. Menú
    if (platillos.length > 0) {
      progressText.textContent = 'Guardando platillos...';
      const steps = 40 / platillos.length;
      let currentW = 60;
      for (const platillo of platillos) {
        platillo.id_establecimiento = id;
        await api.agregarPlatillo(id, platillo);
        currentW += steps;
        progressBar.style.width = `${currentW}%`;
      }
    }

    progressBar.style.width = '100%';
    progressText.textContent = '¡Todo listo!';
    showToast('¡Contribución enviada con éxito! Está en revisión.', 'success');
    
    // Redirect después de un segundito
    setTimeout(() => {
      window.location.hash = '#/perfil';
    }, 1500);

  } catch (error) {
    console.error('Error orquestando contribución:', error);
    showToast(error.message || 'Error al guardar la contribución', 'error');
    
    // Restore UI
    progressDiv.classList.add('hidden');
    document.getElementById('form-actions').classList.remove('hidden');
  }
}
