# Sistema de Diseño y Flujo UI CustomTkinter (v3)

## Arquitectura de Vistas (3 Ventanas/Paneles)

### 1. Ventana Principal (Portada / Dashboard)
- **Propósito:** Ejecución ultra rápida de un solo clic al sentarse a jugar o volver a trabajar.
- **Contenido Central:**
  - Botones gigantes para los packs marcados como `is_favorite = True`.
  - El botón del pack Gaming tiene estilo prioritario (color acentuado rojo `#c22d2d`).
  - Al hacer clic en un favorito, ejecuta su acción principal (apagar para gaming, arrancar para packs de trabajo).
- **Barra de Navegación Inferior:**
  - Botón `📁 Gestor de Packs`: Abre la vista de gestión completa.
  - Botón `⚡ Gestor de Procesos`: Abre la vista de procesos activos.

### 2. Gestor de Packs (`views/pack_manager_view.py`)
- **Propósito:** Crear, editar y ejecutar packs de aplicaciones.
- **Contenido:**
  - Botón superior `➕ Nuevo Pack`.
  - Lista scrollable con tarjetas para cada pack.
  - Cada tarjeta de pack incluye:
    - Nombre del pack y cantidad de apps configuradas.
    - Botón `⭐` para alternar si es favorito (aparece en portada).
    - Botón `⛔ Apagar Apps`: Cierra todos los ejecutables del pack vía `process_service`.
    - Botón `🚀 Arrancar Apps`: Lanza todos los ejecutables configurados vía `subprocess.Popen`.
    - Botón `✏️ Editar`: Abre modal para añadir/quitar apps o keepers.
    - Botón `🗑️ Borrar`: Elimina el pack (deshabilitado si `is_gaming = True`).

### 3. Gestor de Procesos en Vivo (`views/process_manager_view.py`)
- **Propósito:** Explorar qué está consumiendo recursos y agregarlo a packs fácilmente.
- **Contenido:**
  - Botón superior `🔄 Actualizar Lista`.
  - Buscador de texto en tiempo real.
  - Lista agrupada por categorías (`🔴 Navegadores`, `🟡 Chat`, etc.) con checkboxes.
  - Barra de acción inferior fijada:
    - Desplegable `Añadir seleccionados a: [Seleccionar Pack ▼]`.
    - Botón `➕ Añadir al Pack`.
    - Botón `⛔ Cerrar Seleccionados Ahora`.

## Reglas de CustomTkinter
- **Tema:** Modo oscuro forzado (`ctk.set_appearance_mode("Dark")`).
- **Fuentes:** Utilizar familias de sistema estándar (`"Segoe UI"` en Windows).
- **Hilos de Fondo:** Toda operación de listado o kill pesado debe correr en un `threading.Thread(daemon=True)` para que la interfaz nunca se congele, actualizando la UI mediante `master.after(0, callback)`.

## Especificaciones de Pantalla y Responsive (14 Pulgadas)
- **Dimensiones:** Ventana inicial de `860x560` (mínimo `720x460`) optimizada para portátiles de 14" con escalado de Windows de 125% a 150%.
- **Semáforo Visual de Seguridad (`get_safety_badge`):**
  - `🟢 SEGURO`: Verde brillante (`#40c057`) sobre fondo verde oscuro (`#163820`). Cierre recomendado (Browsers, Sync, Productividad).
  - `🟡 PRECAUCIÓN`: Amarillo ámbar (`#fcc419`) sobre fondo amarillo oscuro (`#3d3711`). Apps de juegos/media (Launchers, Discord, Spotify).
  - `🔴 NO CERRAR`: Rojo vibrante (`#ff6b6b`) sobre fondo rojo oscuro (`#401616`). Vitales para el SO o hardware (Windows, drivers, antivirus).
- **Gestor de Packs Compacto:**
  - Toolbar de acciones en tarjetas de pack limitada a ~270px para evitar colisiones con el título.
  - Acordeón plegable para configurar categorías automáticas en el Pack Gaming.
