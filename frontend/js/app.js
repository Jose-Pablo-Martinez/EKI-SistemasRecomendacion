/**
 * EKI — Esquina Jach ki'
 * Módulo principal de lógica de UI y comunicación con la API REST.
 *
 * Convenciones:
 *  - Variables y funciones en camelCase
 *  - Constantes de módulo en UPPER_SNAKE_CASE
 *  - Solo const y let (nunca var)
 *  - URL del backend centralizada en API_BASE_URL
 */

// Configuración dinámica de la URL del Backend
const API_BASE_URL = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
  ? "http://localhost:8000"
  : "https://esquina-jach-ki.onrender.com";

// ─── Referencias al DOM ───────────────────────────────────────────────────────
const contenedorRecomendaciones = document.getElementById("contenedor-recomendaciones");
const estadoCarga = document.getElementById("estado-carga");

// ─── Funciones de Fetch ───────────────────────────────────────────────────────

/**
 * Obtiene las recomendaciones principales del servidor con boosting aplicado.
 * @param {number} limit - Cantidad máxima de resultados a solicitar.
 * @returns {Promise<Array>} Lista de objetos de recomendación del backend.
 */
async function fetchRecommendations(limit = 10) {
  const response = await fetch(`${API_BASE_URL}/recommendations/?limit=${limit}`);
  if (!response.ok) {
    throw new Error(`Error del servidor: ${response.status} ${response.statusText}`);
  }
  return await response.json();
}

/**
 * Verifica que el backend esté activo antes de hacer peticiones.
 * @returns {Promise<boolean>} true si el backend responde correctamente.
 */
async function checkBackendHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

// ─── Funciones de Renderizado ─────────────────────────────────────────────────

/**
 * Crea la tarjeta HTML de un vendedor recomendado.
 * @param {Object} recomendacion - Objeto de recomendación retornado por la API.
 * @returns {HTMLElement} Elemento article con la tarjeta del vendedor.
 */
function createVendorCard(recomendacion) {
  const { vendor, relevance_score, boosted } = recomendacion;

  const card = document.createElement("article");
  card.setAttribute("role", "listitem");
  card.className = "vendor-card bg-white rounded-2xl shadow-md p-5 flex flex-col gap-3 hover:shadow-lg transition-shadow";

  card.innerHTML = `
    <div class="flex items-start justify-between gap-2">
      <div>
        <h3 class="font-bold text-eki-green text-lg leading-tight">${vendor.name}</h3>
        <span class="text-xs text-white bg-eki-lime px-2 py-0.5 rounded-full font-medium">${vendor.category}</span>
      </div>
      ${boosted ? '<span class="text-xs bg-eki-amber text-eki-dark px-2 py-0.5 rounded-full font-semibold whitespace-nowrap">⬆ Boosted</span>' : ''}
    </div>
    <p class="text-sm text-gray-600 flex-1">${vendor.description ?? "Sin descripción disponible."}</p>
    <div class="flex items-center justify-between text-sm text-gray-500 border-t pt-3">
      <span>📍 ${vendor.location ?? "Ubicación no especificada"}</span>
      <span class="font-semibold text-eki-green">★ ${vendor.rating_avg.toFixed(1)}</span>
    </div>
    <div class="text-xs text-gray-400 text-right">
      Relevancia: <span class="font-medium text-eki-dark">${relevance_score.toFixed(2)}</span>
    </div>
  `;

  return card;
}

/**
 * Muestra un mensaje de estado en la sección de recomendaciones.
 * @param {string} emoji - Emoji representativo del estado.
 * @param {string} mensaje - Texto explicativo del estado actual.
 */
function showStatus(emoji, mensaje) {
  estadoCarga.classList.remove("hidden");
  contenedorRecomendaciones.classList.add("hidden");
  estadoCarga.innerHTML = `<p class="text-5xl mb-4">${emoji}</p><p>${mensaje}</p>`;
}

// ─── Función Principal ────────────────────────────────────────────────────────

/**
 * Carga y renderiza las recomendaciones en la interfaz.
 * Valida primero que el backend esté disponible.
 */
async function loadRecommendations() {
  showStatus("⏳", "Conectando con el servidor...");

  try {
    const backendOk = await checkBackendHealth();
    if (!backendOk) {
      showStatus("🔌", "El servidor no está disponible en este momento. Intenta más tarde.");
      return;
    }

    showStatus("🔍", "Cargando recomendaciones...");

    const recomendaciones = await fetchRecommendations(10);

    if (!recomendaciones || recomendaciones.length === 0) {
      showStatus("🍽️", "No hay recomendaciones disponibles en este momento.");
      return;
    }

    // Renderizar tarjetas
    contenedorRecomendaciones.innerHTML = "";
    for (const recomendacion of recomendaciones) {
      contenedorRecomendaciones.appendChild(createVendorCard(recomendacion));
    }

    estadoCarga.classList.add("hidden");
    contenedorRecomendaciones.classList.remove("hidden");

  } catch (error) {
    console.error("No se pudieron obtener las recomendaciones:", error);
    showStatus("⚠️", "Ocurrió un error al cargar las recomendaciones. Verifica tu conexión.");
  }
}
