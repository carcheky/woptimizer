# Change Proposal: v3-ui-redesign

## Contexto y Por Qué
La versión V3 inicial desacopló la lógica a `psutil` y `CustomTkinter`, pero redujo drásticamente la funcionalidad de usuario al eliminar la gestión de perfiles (CRUD) y presentar una ventana monolítica sin capacidad de personalización.

El usuario requiere un sistema ágil basado en el concepto unificado de **"Packs"**, con acciones simétricas (apagar/encender), favoritos en portada y un gestor de procesos en vivo para enriquecer packs.

## Alcance del Cambio
1. **Modelo de Datos:**
   - Unificar perfiles bajo el concepto `Pack`.
   - Cada pack tiene: `id`, `name`, `apps` (lista de nombres o rutas), `is_favorite` (bool), `is_gaming` (bool).
   - El pack "Gaming" es un preset del sistema imborrable. Cierra apps de sincronización, navegadores y chats (excepto Discord) y permite añadir/quitar exclusiones o procesos extra.

2. **Arquitectura de Interfaz (3 Ventanas):**
   - **Ventana 1: Portada (Dashboard):**
     - Muestra accesos directos gigantes a los packs marcados como **Favoritos** (Gaming por defecto).
     - Cada botón favorito ejecuta la acción principal del pack.
     - Botones de navegación inferior: "📁 Gestor de Packs" y "⚡ Gestor de Procesos".
   - **Ventana 2: Gestor de Packs:**
     - Lista todos los packs existentes.
     - Botón de crear nuevo pack.
     - Por cada pack: botón "⛔ Apagar Apps", botón "🚀 Arrancar Apps", botón "⭐ Favorito" y botón "🗑️ Borrar" (deshabilitado en Gaming).
     - Vista de edición de aplicaciones incluidas en cada pack.
   - **Ventana 3: Gestor de Procesos en Vivo:**
     - Lista en tiempo real los procesos del sistema con `psutil`.
     - Filtros y checkboxes de selección múltiple.
     - Desplegable con packs existentes + botón "➕ Añadir seleccionados al Pack".

## Criterios de Aceptación
- El usuario puede alternar favoritos y ver reflejados los cambios en la portada inmediatamente.
- El pack "Gaming" no se puede borrar ni renombrar destructivamente.
- Se pueden matar o lanzar los ejecutables de cualquier pack con un clic.
- Se pueden añadir procesos desde la lista en vivo a cualquier pack sin escribir a mano los nombres de los ejecutables.
