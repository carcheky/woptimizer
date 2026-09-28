# OpenSpec Tasks: v3-ux-polish

- [ ] **1. Migración de Base de Datos y Endpoints**
  - [ ] Escribir script o herramienta para convertir el actual `fallback.csv` a `process_db.json`.
  - [ ] Actualizar `ProcessService` para consumir `process_db.json` localmente.
  - [ ] Actualizar endpoint remoto en `ProcessService` apuntando a GitLab (`https://gitlab.com/carcheky/woptimizer/-/raw/main/assets/process_db.json`).

- [ ] **2. Evolución del Pack Gaming (`models.py` y `pack_service.py`)**
  - [ ] Ampliar el modelo `Pack` (o crear subclase `GamingPack`) para incluir `target_categories: List[str]`.
  - [ ] Modificar `GamingService.should_kill_for_gaming` para respetar las `target_categories` elegidas por el usuario en el pack en lugar de usar reglas hardcodeadas.

- [ ] **3. UI: Gestor de Procesos (`views/process_manager_view.py`)**
  - [ ] Añadir botón "🔄 Actualizar Base de Datos" en la cabecera, enlazado al servicio asíncrono.
  - [ ] Renderizar el Semáforo (🟢/🟡/🔴) y la descripción detallada en cada fila de la lista de procesos.

- [ ] **4. UI: Gestor de Packs (`views/pack_manager_view.py`)**
  - [ ] Habilitar la adición y eliminación de `apps` en el Pack Gaming (actualmente capado).
  - [ ] Renderizar una sección de checkboxes en el Pack Gaming para seleccionar/deseleccionar categorías objetivo (ej. `Navegadores`, `Sincronización`).

- [ ] **5. Verificación**
  - [ ] Ejecutar `run_tests.py` para asegurar que el modelo modificado no rompe la persistencia.
  - [ ] Compilación final a `.exe` integrando el nuevo asset `.json`.
