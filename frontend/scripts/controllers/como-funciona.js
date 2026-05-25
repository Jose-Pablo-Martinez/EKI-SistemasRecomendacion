/**
 * como-funciona.js — Página "Cómo funcionan las recomendaciones"
 * frontend/scripts/controllers/como-funciona.js
 * EkiSystem — Fase 5
 *
 * Ruta: #/como-funciona
 * Explicación educativa del motor híbrido: accesible, sin jerga técnica excesiva.
 * Enlazar desde el feed (#/feed) y desde el footer de la ficha de establecimiento.
 */

window.controllers['como-funciona'] = async () => {
  await renderView('como-funciona.html');
};
