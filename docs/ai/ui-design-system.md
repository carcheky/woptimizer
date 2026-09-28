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
