# OpenSpec Tasks: v3-ui-redesign

- [x] **1. Modelos de Datos (`src/woptimizer/models.py`)**
  - [x] Definir modelo `Pack` unificado (con soporte para favorito, apps, reglas gaming).
  - [x] Actualizar `AppData` para persistir packs en `profiles.json`.
  - [x] Implementar migración automática de perfiles v2/v3 antiguos a la nueva estructura de packs.

- [x] **2. Servicios (`src/woptimizer/services/`)**
  - [x] Adaptar `profile_service.py` a `pack_service.py` (CRUD completo de packs).
  - [x] Implementar en `process_service.py` el lanzamiento masivo de apps de un pack (`launch_pack`).
  - [x] Implementar en `process_service.py` el cierre masivo de apps de un pack (`kill_pack`).
  - [x] Preservar la lógica especializada de gaming (cerrar categorías + extras, respetando keepers).

- [x] **3. Vistas de Usuario (`src/woptimizer/ui/`)**
  - [x] Crear `views/dashboard_view.py` (Portada con favoritos).
  - [x] Crear `views/pack_manager_view.py` (Gestor de Packs con CRUD y acciones duales).
  - [x] Crear `views/process_manager_view.py` (Lista de procesos + selector para añadir a pack).
  - [x] Integrar las 3 vistas en `app.py` (shell principal `main_window.py`) con navegación fluida y sin ventanas huérfanas.

- [x] **4. Verificación y Empaquetado**
  - [x] Test unitario de modelos y persistencia JSON.
  - [x] Validación de imports y sintaxis estática.
  - [x] Recompilación a `dist/woptimizer.exe`.
