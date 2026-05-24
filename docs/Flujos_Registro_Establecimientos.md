# Flujos de Registro de Establecimientos y Roles de Usuario en EkiSystem

El diseño de la base de datos de EkiSystem permite que el mapa de lugares crezca de dos maneras diferentes, fusionando un modelo colaborativo guiado por la comunidad (**Crowdsourced**) con un modelo tradicional de dueños de negocio (**B2B**).

Este documento detalla técnicamente cómo están implementados ambos flujos gracias a la herencia en la base de datos (Table-per-Type).

---

## 1. La Jerarquía de Usuarios (Table-per-Type)
Para entender cómo funciona el registro, primero hay que recordar la estructura de usuarios:

- `Usuario`: Entidad base. Contiene nombre, email y contraseña.
    - `UsuarioVisitante` (Hereda de Usuario): Añade el vector de preferencias, puntos de experiencia y un **Rango de Informador**. Es el comensal común.
        - `UsuarioPropietario` (Hereda de Visitante): Añade RFC y documentos legales. **Como hereda de visitante, un dueño sigue siendo legalmente un "usuario normal"** capaz de usar la app para explorar.

---

## 2. Flujo 1: Crecimiento Colaborativo (El Visitante Informador)
*Inspirado en Google Maps Local Guides o Waze.*

**Escenario:** Un `UsuarioVisitante` va por la calle, descubre un nuevo carrito de tacos delicioso que no está en la aplicación y decide agregarlo para que otros lo conozcan.

**Proceso Técnico:**
1. El usuario usa el endpoint de "Crear Establecimiento".
2. Se inserta el nuevo registro en la tabla `Establecimiento`.
3. La columna `id_usuario_registro` guarda el ID de este visitante.
4. El lugar entra en estado `"pendiente"`. No es visible para la comunidad todavía.
5. El backend le otorga `puntos_experiencia` al visitante, lo cual le permite subir de nivel en su `id_rango` (Rango de Informador).
6. Un `Administrador` revisa la foto/coordenadas, lo cambia a `"aprobado"` y el puesto se vuelve público, entrando a las recomendaciones de los demás bajo la categoría de `descubrimiento`.

---

## 3. Flujo 2: El Dueño Registra su Propio Local (Onboarding B2B)
**Escenario:** Un emprendedor abre un restaurante nuevo, descarga EkiSystem para promocionarse y registra su negocio desde cero.

**Proceso Técnico:**
1. El usuario completa el flujo de verificación subiendo su RFC/INE. Su cuenta se convierte (o nace) en la tabla `UsuarioPropietario`.
2. Utiliza el mismo endpoint de crear establecimiento. La columna `id_usuario_registro` guarda su ID.
3. **El Paso Clave (Superpoderes):** Además de guardar el local, el sistema crea un registro en la tabla pivote N:M **`PropietarioEstablecimiento`** vinculando su cuenta a ese lugar.
4. Una vez que el Administrador aprueba esta vinculación legal, el dueño adquiere permisos administrativos sobre ese local específico, permitiéndole:
   - Modificar el menú oficial (`Platillo`).
   - Definir los `Horarios` rígidos de apertura y cierre.
   - Responder a reseñas de la comunidad.

---

## 4. Flujo 3: Reclamación de un Local (El Híbrido)
**Escenario:** El dueño de una pizzería descubre que alguien de la comunidad de EkiSystem (un Informador del Flujo 1) ya había registrado su pizzería hace 6 meses. La pizzería ya tiene reseñas y calificaciones. El dueño quiere tomar el control sin perder esos datos.

**Proceso Técnico:**
1. El dueño se registra en la app y sube sus documentos legales (`UsuarioPropietario`).
2. En la app, busca su pizzería y presiona un botón de **"Reclamar este Negocio"**.
3. El sistema **NO** crea un establecimiento nuevo. Lo que hace es crear una solicitud en la tabla pivote **`PropietarioEstablecimiento`** asociando el `id_usuario` del dueño con el `id_establecimiento` existente, dejándolo en estado `"pendiente"`.
4. El dueño debe adjuntar un `documento_prueba` (ej. recibo de luz del local).
5. Un Administrador revisa el documento. Si es válido, aprueba la vinculación en la tabla pivote.
6. A partir de ese momento, el `UsuarioPropietario` tiene control total sobre la información de la pizzería, respetando todo el historial, reseñas y el trabajo que originalmente hizo el Informador que la descubrió.
