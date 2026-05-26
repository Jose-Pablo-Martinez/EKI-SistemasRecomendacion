# 🐛 Historial de Defectos y Cambios — Revisiones QA

---

## 📋 Primera Revisión

### Defectos encontrados

---

#### 1. Retroalimentación de favoritos no persiste en FEED

La retroalimentación de clickear el icono *añadir a favoritos* para un restaurante no persistía en la pestaña de **FEED**, provocando la ilusión de que un restaurante no había sido marcado como favorito, aunque sí lo estuviera.

> ✅ **Estado: Corregido**
> Se añadió una retroalimentación visual persistente al marcar un restaurante como favorito, que se mantiene en la pestaña de FEED incluso al salir y volver a ella.

---

#### 2. Duplicados al actualizar preferencias

Al actualizar las preferencias desde la pestaña de perfil, los restaurantes recomendados previamente volvían a aparecer en el **FEED** si eran recomendados de nuevo, generando duplicados.

> ✅ **Estado: Corregido**
> Al actualizar las preferencias, se evitan duplicados al recomendar nuevamente un restaurante que ya pertenecía a las recomendaciones del FEED.

---

#### 3. Contadores de favoritos y reseñas no se actualizaban en el perfil

En el perfil no se actualizaban los contadores de *favoritos* ni *reseñas*.

> ✅ **Estado: Corregido**
> En la pestaña de perfil ahora se visualizan correctamente el número de reseñas dejadas y los restaurantes añadidos a *favoritos*.

---

#### 4. Puntos de reseñas no se contabilizaban en gamificación

Al dejar reseñas, los puntos otorgados no se contabilizaban para el sistema de gamificación y rangos, y tampoco se reflejaban en el historial de puntos.

> ✅ **Estado: Corregido**
> Cada reseña otorga **10 puntos** que se contabilizan para el sistema de gamificación y rango, reflejándose en la barra de progreso del siguiente rango, en el contador de puntos totales y en el historial de puntos.

---

#### 5. El logotipo redirige al formulario de registro en sesión activa

Al presionar el logotipo y nombre del sistema (esquina superior izquierda), se redirigía al usuario a la pestaña de **EMPEZAR AHORA**, que a su vez llevaba al formulario de registro, aun cuando el usuario ya tenía una sesión activa.

> ✅ **Estado: Corregido**
> Con sesión activa, hacer clic en el logotipo ya no redirige a ninguna pestaña, eliminando el defecto descrito.

---

#### 6. Mal funcionamiento en recomendaciones personalizadas (no inicio en frío)

Mal funcionamiento al generar recomendaciones basadas en interacciones y preferencias del usuario en sesiones anteriores (fuera del flujo de inicio en frío).

> 🔄 **Estado: Pendiente**
> Aún se está trabajando en la implementación de una solución.

---

### ✨ Cambios adicionales posteriores a la primera revisión

- Las reseñas (comentario y calificación de 1 a 5 estrellas) ahora pueden **modificarse**.
- El historial de puntos también registra cuando el usuario **sube de rango**.
- Se añadió a cada restaurante un **menú de platillos** y un listado completo de **reseñas**.
- Algunos restaurantes ahora cuentan con **horario**.
- Se añadió un **filtro de radio de búsqueda** para filtrar restaurantes por cercanía.
- La presentación de ítems en la pestaña FEED fue reorganizada en **carruseles**.

---

## 📋 Segunda Revisión

### Defectos encontrados

---

#### 1. Carruseles sin flechas de desplazamiento

Los carruseles carecían de flechas de desplazamiento, haciendo imposible navegar los ítems hacia la derecha o izquierda.

> ✅ **Estado: Corregido**
> Se agregaron flechas de desplazamiento para visualizar todos los ítems de un carrusel.

---

#### 2. Flechas en carruseles cortos innecesarias

Se agregaron flechas de desplazamiento incluso a carruseles con pocos ítems que no lo requerían.

> ✅ **Estado: Corregido**
> Los carruseles con pocos ítems ya no muestran flechas de desplazamiento al ser innecesarias.

---

#### 3. Flechas de desplazamiento superpuestas a los ítems

Las flechas de desplazamiento se colocaron encima de los ítems, haciéndolas casi invisibles y afectando la estética del sistema.

> ✅ **Estado: Corregido**
> Las flechas de desplazamiento ya no están sobrepuestas a los ítems de las orillas.

---

#### 4. Carruseles cortados en pantallas móviles pequeñas

Los carruseles no se visualizaban completa ni correctamente en dispositivos móviles con pantallas reducidas.

> ✅ **Estado: Corregido**
> Los carruseles funcionan y se visualizan correctamente en pantallas de dispositivos móviles.

---

#### 5. Carruseles desalineados

Los carruseles no estaban alineados, afectando la estética general del sistema.

> ✅ **Estado: Corregido**
> Se han alineado los carruseles, restaurando la estética del sistema.

---

#### 6. Porcentajes de recomendación erróneos

Los porcentajes que indicaban qué tanto de la recomendación se basaba en preferencias vs. personas afines eran incorrectos y podían superar el 100%.

> ✅ **Estado: Corregido**
> Los porcentajes ahora son precisos y no sobrepasan el 100%.

---

#### 7. Restaurantes duplicados dentro de un mismo carrusel

Se presentó nuevamente el problema de restaurantes duplicados, esta vez dentro de un mismo carrusel.

> ✅ **Estado: Corregido**
> Ya no se duplican restaurantes ni ítems dentro de un mismo carrusel.

---

#### 8. Mal funcionamiento en recomendaciones personalizadas (reincidencia)

Reincidencia del mal funcionamiento al generar recomendaciones basadas en interacciones del usuario en sesiones anteriores.

> ✅ **Estado: Corregido**
> Se mejoró la recomendación de restaurantes, incluyendo las basadas en interacciones del usuario en sesiones previas.

---

*Documento generado a partir del historial de revisiones QA del proyecto.*
