# AGENTS.md — woptimizer

## Qué es
Process manager gaming para Windows. Cierra apps en masa (gaming mode) y las reabre usando perfiles ("Packs") y persistencia JSON.

## Stack
- Python 3.11+
- UI: CustomTkinter
- Core Backend: `psutil` (reemplaza legacy powershell wmi)
- Persistencia: `pydantic v2`
- Build: PyInstaller (`force_build.py` / `build.bat`)
- Entry point: `python run.py`, `python -m woptimizer` o `dist/woptimizer.exe`.

## 🧭 Flujo de Trabajo para Agentes (Taskmaster + OpenSpec + Docs Selectivos)
1. **Orquestación de Tareas (Taskmaster):**
   - Consulta la tarea activa ejecutando: `python .taskmaster/tm.py next` (o lee `.taskmaster/tasks.md`).
   - Al completar la tarea, márcala con: `python .taskmaster/tm.py done <TASK_ID>`.
2. **Especificaciones y Cambios (OpenSpec):**
   - Todo cambio arquitectónico o de interfaz debe estar documentado en `openspec/changes/<change-id>/`.
   - Consulta activa: `openspec/changes/2026-09-28-v3-ui-redesign/`.
3. **Carga Selectiva de Documentación (Ahorro de Tokens):**
   - **NO leas toda la documentación junta.**
   - Lee `llms.txt` como mapa de rutas y carga **solo** el archivo relevante de `docs/ai/`:
     - `docs/ai/architecture.md` (capas y backend)
     - `docs/ai/data-models.md` (esquemas Pydantic y JSON)
     - `docs/ai/ui-design-system.md` (CustomTkinter y las 3 ventanas)
     - `docs/ai/sandbox-rules.md` (EPERM y builds)
     - `docs/ai/testing-guide.md` (pruebas headless)

## Estructura del Código
```text
src/woptimizer/
├── __init__.py
├── __main__.py          # Entry Point
├── config.py            # Categorías, constantes
├── models.py            # Pydantic: ProcessInfo, Pack, AppData
├── services/            # Capa de lógica (NO tocar UI aquí)
│   ├── process_service.py  # psutil: listar, matar, arrancar
│   └── pack_service.py     # CRUD de packs y persistencia
└── ui/                  # Capa de CustomTkinter (NO lógica de negocio)
    ├── app.py              # Clase raíz y navegación de vistas
    ├── main_window.py      # Contenedor principal
    └── views/              # Vistas: Portada, Gestor de Packs, Gestor de Procesos
```

## Invariantes (nunca romper)
- **Separación de capas**: UI nunca llama a OS/psutil ni lee archivos JSON directamente; **siempre** vía `services/`.
- **Sandbox/EPERM**: El entorno Host puede bloquear la creación de subprocesos. Usa scripts Python puente (`run_command`) o los builders dedicados.
- **Kill Recursivo**: Kill siempre debe matar los procesos hijos (`parent.children(recursive=True)`) antes del padre.
- **Pack Gaming Protegido**: El pack con `is_gaming=True` no puede ser eliminado por el usuario.


## 📚 Reglas de Documentación Continua y Persistencia
1. **Documentación Viva Obligatoria:** Toda modificación arquitectónica, de modelos de datos, servicios o componentes de UI debe documentarse inmediatamente en el archivo correspondiente de `docs/ai/` (`architecture.md`, `data-models.md`, `ui-design-system.md`). No se cierra un ciclo de desarrollo sin actualizar la documentación.
2. **Cierre Limpio (Cero Cambios Pendientes):** Al terminar cualquier bloque o solicitud del usuario, debes comitear todos los cambios pendientes de forma lógica y estructurada (`feat`, `fix`, `docs`, `refactor`), dejando el árbol de Git con 0 cambios pendientes.
3. **Aislamiento de Git en Entornos Cloud (Nextcloud / OneDrive):** Si el repositorio está ubicado en una carpeta de sincronización con Virtual Files (VFS), el filtro del sistema puede bloquear la creación de objetos en `.git` (`unable to create temporary file: Invalid argument`). Para resolverlo, redirige temporalmente el almacenamiento de git a una ruta local desacoplada:
   ```powershell
   $env:GIT_DIR = "$env:LOCALAPPDATA\woptimizer_git\.git"
   $env:GIT_WORK_TREE = "C:\Users\carch\Nextcloud\Scripts\woptimizer"
   ```

## Comandos Rápidos
```bash
python run.py                   # Lanzar en modo desarrollo
python .taskmaster/tm.py next   # Ver siguiente tarea pendiente
python .taskmaster/tm.py list   # Ver estado de todas las tareas
python verify_ui_syntax.py      # Verificar sintaxis estática de la UI
```

## 🛠️ Skills Disponibles (.agents/skills/)
- `id-pipeline`: Motor autónomo de I+D. Busca trabajo o crea nuevas propuestas y orquesta `architect-review` y `openspec-dev` en bucle mediante subagentes.
- `architect-review`: Arquitectura, auditoría de invariantes y planificación de Taskmaster / OpenSpec.
- `openspec-dev`: Tech Lead e implementación con validación estática y headless.
- `process-db-updater`: Analista de procesos y actualización de `assets/process_db.json`.

