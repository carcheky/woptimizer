# OpenSpec Tasks: v3-ui-redesign

- [ ] **1. Modelos de Datos (`src/woptimizer/models.py`)**
  - [ ] Definir modelo `Pack` unificado (con soporte para favorito, apps, reglas gaming).
  - [ ] Actualizar `AppData` para persistir packs en `profiles.json`.
  - [ ] Implementar migración automática de perfiles v2/v3 antiguos a la nueva estructura de packs.

- [ ] **2. Servicios (`src/woptimizer/services/`)**
  - [ ] Adaptar `profile_service.py` a `pack_service.py` (CRUD completo de packs).
  - [ ] Implementar en `process_service.py` el lanzamiento masivo de apps de un pack (`launch_pack`).
  - [ ] Implementar en `process_service.py` el cierre masivo de apps de un pack (`kill_pack`).
  - [ ] Preservar la lógica especializada de gaming (cerrar categorías + extras, respetando keepers).

- [ ] **3. Vistas de Usuario (`src/woptimizer/ui/`)**
  - [ ] Crear `views/dashboard_view.py` (Portada con favoritos).
  - [ ] Crear `views/pack_manager_view.py` (Gestor de Packs con CRUD y acciones duales).
  - [ ] Crear `views/process_manager_view.py` (Lista de procesos + selector para añadir a pack).
  - [ ] Integrar las 3 vistas en `app.py` con navegación fluida y sin ventanas huérfanas.

- [ ] **4. Verificación y Empaquetado**
  - [ ] Test unitario de modelos y persistencia JSON.
  - [ ] Validación de imports y sintaxis estática.
  - [ ] Recompilación a `dist/woptimizer.exe`.
