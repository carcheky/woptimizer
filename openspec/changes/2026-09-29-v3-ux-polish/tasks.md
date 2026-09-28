# OpenSpec Tasks: v3-ux-polish

- [x] **1. Migración de Base de Datos y Endpoints**
  - [x] Escribir script o herramienta para convertir el actual `fallback.csv` a `process_db.json`.
  - [x] Actualizar `ProcessService` para consumir `process_db.json` localmente.
  - [x] Actualizar endpoint remoto en `ProcessService` apuntando a GitLab (`https://gitlab.com/carcheky/woptimizer/-/raw/main/assets/process_db.json`).

- [x] **2. Evolución del Pack Gaming (`models.py` y `pack_service.py`)**
  - [x] Ampliar el modelo `Pack` (o crear subclase `GamingPack`) para incluir `target_categories: List[str]`.
  - [x] Modificar `GamingService.should_kill_for_gaming` para respetar las `target_categories` elegidas por el usuario en el pack en lugar de usar reglas hardcodeadas.

- [x] **3. UI: Gestor de Procesos (`views/process_manager_view.py`)**
  - [x] Añadir botón "🔄 Actualizar Base de Datos" en la cabecera, enlazado al servicio asíncrono.
  - [x] Renderizar el Semáforo (🟢/🟡/🔴) y la descripción detallada en cada fila de la lista de procesos.

- [x] **4. UI: Gestor de Packs (`views/pack_manager_view.py`)**
  - [x] Habilitar la adición y eliminación de `apps` en el Pack Gaming (actualmente capado).
  - [x] Renderizar una sección de checkboxes en el Pack Gaming para seleccionar/deseleccionar categorías objetivo (ej. `Navegadores`, `Sincronización`).

- [x] **5. Verificación**
  - [x] Ejecutar `run_tests.py` para asegurar que el modelo modificado no rompe la persistencia.
  - [x] Compilación final a `.exe` integrando el nuevo asset `.json`.
