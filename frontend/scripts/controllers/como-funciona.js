/**
 * como-funciona.js — Página "Cómo funcionan las recomendaciones"
 * frontend/scripts/controllers/como-funciona.js
 * EkiSystem — Fase 5
 *
 * Ruta: #/como-funciona
 * Explicación educativa del motor híbrido: accesible, sin jerga técnica excesiva.
 * Enlazar desde el feed (#/feed) y desde el footer de la ficha de establecimiento.
 */

window.controllers['como-funciona'] = () => {

  renderPage(`
    <div class="w-full max-w-3xl mx-auto px-4 md:px-8 py-12 fade-in">

      <!-- Back -->
      <a href="javascript:history.back()"
         class="inline-flex items-center gap-1 text-body-sm font-semibold text-text-tertiary
                hover:text-secondary transition-colors mb-8 group">
        <span class="material-symbols-outlined group-hover:-translate-x-1 transition-transform"
              aria-hidden="true" style="font-size:18px;">arrow_back</span>
        Volver
      </a>

      <!-- Header -->
      <div class="mb-10">
        <div class="flex items-center gap-3 mb-3">
          <span class="material-symbols-outlined text-accent" aria-hidden="true" style="font-size:32px;">psychology</span>
          <h1 class="font-heading text-display-md text-primary">¿Cómo funcionan las recomendaciones?</h1>
        </div>
        <p class="text-body-lg text-text-secondary leading-relaxed">
          EkiSystem no usa un algoritmo de caja negra. Aquí te explicamos exactamente
          <strong class="text-primary">por qué</strong> te recomendamos cada lugar.
        </p>
      </div>

      <!-- Diagrama visual del flujo -->
      <div class="bg-surface-raised border border-border-default rounded-md p-6 mb-10">
        <h2 class="font-heading text-headline-sm text-primary mb-5">El modelo en un vistazo</h2>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">

          <!-- Paso 1 -->
          <div class="flex flex-col items-center gap-2">
            <div class="w-14 h-14 rounded-full bg-secondary-faint flex items-center justify-center">
              <span class="material-symbols-outlined text-secondary" aria-hidden="true" style="font-size:28px;">manage_accounts</span>
            </div>
            <p class="font-heading text-headline-sm text-primary">Tus gustos</p>
            <p class="text-body-sm text-text-secondary">Tu vector de preferencias, creado en el onboarding y actualizado con cada interacción.</p>
          </div>

          <!-- Flecha -->
          <div class="hidden sm:flex items-center justify-center text-text-tertiary" aria-hidden="true">
            <span class="material-symbols-outlined text-3xl">add</span>
          </div>

          <!-- Paso 2 -->
          <div class="flex flex-col items-center gap-2">
            <div class="w-14 h-14 rounded-full bg-accent-faint flex items-center justify-center">
              <span class="material-symbols-outlined text-accent" aria-hidden="true" style="font-size:28px;">group</span>
            </div>
            <p class="font-heading text-headline-sm text-primary">Tu comunidad</p>
            <p class="text-body-sm text-text-secondary">Usuarios con gustos parecidos a los tuyos (mismo cluster), agrupados automáticamente.</p>
          </div>

        </div>

        <!-- Resultado -->
        <div class="mt-6 pt-5 border-t border-border-subtle text-center">
          <div class="w-14 h-14 rounded-full bg-primary flex items-center justify-center mx-auto mb-2">
            <span class="material-symbols-outlined text-white" aria-hidden="true" style="font-size:28px;">recommend</span>
          </div>
          <p class="font-heading text-headline-sm text-primary mb-1">Score final</p>
          <p class="text-body-sm text-text-secondary">
            <strong>40% tus gustos</strong> + <strong>35% tu comunidad</strong> + <strong>25% boost contextual</strong>
          </p>
        </div>
      </div>

      <!-- Secciones explicativas -->
      <div class="space-y-8">

        <!-- 1. Filtrado por contenido -->
        <div class="flex gap-5">
          <div class="w-10 h-10 rounded-full bg-secondary-faint flex items-center justify-center flex-shrink-0 mt-1">
            <span class="material-symbols-outlined text-secondary" aria-hidden="true" style="font-size:20px;">favorite</span>
          </div>
          <div>
            <h2 class="font-heading text-headline-sm text-primary mb-2">Basado en tus gustos (40%)</h2>
            <p class="text-body-sm text-text-secondary leading-relaxed">
              Cuando hiciste el onboarding, nos dijiste qué tipo de comida te gusta, a qué distancia
              quieres buscar y otras preferencias. Convertimos esas respuestas en un
              <em>vector de preferencias</em> — una lista de números que representa tu perfil.
            </p>
            <p class="text-body-sm text-text-secondary leading-relaxed mt-2">
              Cada establecimiento también tiene su vector de características. Comparamos qué tan
              similares son usando <strong>similitud coseno</strong>: mientras más cercanos, mejor score.
              Este componente pesa <strong>40%</strong> del score final.
            </p>
            <div class="bg-secondary-faint border border-secondary/20 rounded p-3 mt-3">
              <p class="text-label-md text-secondary font-semibold">¿Qué lo mejora?</p>
              <p class="text-body-sm text-text-secondary mt-1">
                Tus reseñas, las veces que abres Maps o llamas a un lugar actualizan tu vector
                automáticamente.
              </p>
            </div>
          </div>
        </div>

        <div class="border-t border-border-subtle"></div>

        <!-- 2. Filtrado colaborativo -->
        <div class="flex gap-5">
          <div class="w-10 h-10 rounded-full bg-accent-faint flex items-center justify-center flex-shrink-0 mt-1">
            <span class="material-symbols-outlined text-accent" aria-hidden="true" style="font-size:20px;">group</span>
          </div>
          <div>
            <h2 class="font-heading text-headline-sm text-primary mb-2">Tu comunidad (35%)</h2>
            <p class="text-body-sm text-text-secondary leading-relaxed">
              Usamos <strong>K-Means</strong> para agrupar a todos los usuarios según sus perfiles de
              preferencias. Tú quedas en el cluster que más se parece a ti.
            </p>
            <p class="text-body-sm text-text-secondary leading-relaxed mt-2">
              Luego miramos qué lugares visitan (o califican bien) las personas de tu mismo grupo y
              te los recomendamos. Esto se llama <em>filtrado colaborativo ítem-a-ítem</em> y pesa
              <strong>35%</strong> del score final. Se activa cuando tienes al menos 5 interacciones.
            </p>
          </div>
        </div>

        <div class="border-t border-border-subtle"></div>

        <!-- 3. Boost contextual -->
        <div class="flex gap-5">
          <div class="w-10 h-10 rounded-full bg-[#EBF4ED] flex items-center justify-center flex-shrink-0 mt-1">
            <span class="material-symbols-outlined" aria-hidden="true" style="font-size:20px;color:var(--success);">auto_awesome</span>
          </div>
          <div>
            <h2 class="font-heading text-headline-sm text-primary mb-2">Boost contextual (25%)</h2>
            <p class="text-body-sm text-text-secondary leading-relaxed">
              Ajustamos el score final con factores del contexto:
            </p>
            <ul class="mt-2 space-y-2" role="list">
              <li class="flex gap-2 text-body-sm text-text-secondary">
                <span class="material-symbols-outlined text-text-tertiary flex-shrink-0" aria-hidden="true" style="font-size:16px;margin-top:2px;">near_me</span>
                <span><strong class="text-primary">Proximidad</strong> — los lugares más cercanos a tu ubicación reciben un boost.</span>
              </li>
              <li class="flex gap-2 text-body-sm text-text-secondary">
                <span class="material-symbols-outlined text-accent flex-shrink-0" aria-hidden="true" style="font-size:16px;margin-top:2px;">storefront</span>
                <span><strong class="text-primary">Puesto informal</strong> — los negocios informales reciben +0.25 fijo. Es nuestra misión hacerlos visibles.</span>
              </li>
              <li class="flex gap-2 text-body-sm text-text-secondary">
                <span class="material-symbols-outlined text-text-tertiary flex-shrink-0" aria-hidden="true" style="font-size:16px;margin-top:2px;">trending_up</span>
                <span><strong class="text-primary">Popularidad reciente</strong> — lugares con muchas visitas en los últimos 7 días suben en el ranking.</span>
              </li>
            </ul>
          </div>
        </div>

        <div class="border-t border-border-subtle"></div>

        <!-- 4. Cold start -->
        <div class="flex gap-5">
          <div class="w-10 h-10 rounded-full bg-surface-dim flex items-center justify-center flex-shrink-0 mt-1">
            <span class="material-symbols-outlined text-text-tertiary" aria-hidden="true" style="font-size:20px;">explore</span>
          </div>
          <div>
            <h2 class="font-heading text-headline-sm text-primary mb-2">Para empezar (cold start)</h2>
            <p class="text-body-sm text-text-secondary leading-relaxed">
              Si eres nuevo o no tienes suficientes interacciones todavía, te asignamos
              provisionalmente al cluster más parecido a tu perfil del onboarding y te mostramos
              los lugares más populares de ese grupo. Así nunca ves una pantalla vacía.
            </p>
          </div>
        </div>

        <div class="border-t border-border-subtle"></div>

        <!-- 5. Caja blanca -->
        <div class="flex gap-5">
          <div class="w-10 h-10 rounded-full bg-secondary-faint flex items-center justify-center flex-shrink-0 mt-1">
            <span class="material-symbols-outlined text-secondary" aria-hidden="true" style="font-size:20px;">shield</span>
          </div>
          <div>
            <h2 class="font-heading text-headline-sm text-primary mb-2">Transparencia total</h2>
            <p class="text-body-sm text-text-secondary leading-relaxed">
              Cada tarjeta que ves en el feed muestra el desglose real del score:
              cuánto aportó el análisis de tus gustos, cuánto tu comunidad y cuánto el boost.
              No hay magia negra — solo matemáticas que puedes entender.
            </p>
            <div class="bg-secondary-faint border border-secondary/20 rounded p-3 mt-3 flex items-start gap-2">
              <span class="material-symbols-outlined text-secondary" aria-hidden="true" style="font-size:16px;margin-top:2px;">shield</span>
              <div>
                <p class="text-body-sm font-semibold text-secondary">Ejemplo real de un score</p>
                <p class="text-label-md text-text-tertiary mt-1">
                  Contenido <strong>88%</strong> · Comunidad <strong>76%</strong> · Score final <strong>87%</strong>
                </p>
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- CTA -->
      <div class="mt-12 text-center">
        <a href="#/feed"
           class="inline-flex items-center gap-2 bg-accent text-white px-6 py-3 rounded
                  font-semibold text-label-lg hover:bg-accent-hover active:scale-95 transition-all shadow">
          <span class="material-symbols-outlined" aria-hidden="true" style="font-size:18px;">recommend</span>
          Ver mis recomendaciones
        </a>
      </div>

    </div>
  `);
};
