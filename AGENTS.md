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
   - ⚠️ **`tm.py` NO es ejecutable en este entorno** (lanza `subprocess` y falla con `spawn EPERM`).
   - Consulta la tarea activa leyendo `.taskmaster/tasks.json`: usa el campo `active_task_id`, o la primera entrada con `"status": "pending"`.
   - Al completar la tarea, pon `"status": "completed"` en su entrada del mismo fichero.
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
   **Nunca comitear a pelo:** usa siempre `python .taskmaster/git_safe_commit.py "..."`. Su código de salida es un contrato normativo (`0` commit o no-op, `1` fallo de git, `2` uso incorrecto, `3` repo no verificable, con línea canónica `WOPT_*` en stdout) documentado en `docs/ai/sandbox-rules.md`; `--verify` diagnostica el repo sin escribir nada.

## Comandos Rápidos
```bash
python run.py                   # Lanzar en modo desarrollo
python run_tests.py             # 28 tests headless (no abre ventanas)
python verify_ui_syntax.py      # Verificar sintaxis estática de la UI
python validate_docs.py         # Validar documentación y changelogs
python .taskmaster/git_safe_commit.py "msg"   # ÚNICA vía de versionado
```
> ❌ `python .taskmaster/tm.py next|done|list` **no funciona aquí** (hace `subprocess`). Lee `.taskmaster/tasks.json`.

## 🛠️ Roles del Pipeline (Agentes + Skill)

> **Distingue los dos mecanismos.** Una *skill* es un fichero de instrucciones en `.agents/skills/`; un *agente* es una sesión propia, con contexto separado, que se delega con la herramienta `task`. Las skills **no** aparecen en el panel de agentes y **no** se pueden delegar con `task`.

| Rol | Tipo | Dónde vive | Cómo se invoca |
|---|---|---|---|
| **Motor de I+D** | Skill | `.agents/skills/id-pipeline/` | `/id-pipeline` — la ejecuta el orquestador en su propia sesión |
| **Arquitecto** | **Agente** | `.agents/agents/architect-review/agent.md` | `task({agent_name: "architect-review"})` |
| **Tech Lead / Dev** | **Agente** | `.agents/agents/openspec-dev/agent.md` | `task({agent_name: "openspec-dev"})` |
| **Analista de procesos** | **Agente** | `.agents/agents/process-db-updater/agent.md` | `task({agent_name: "process-db-updater"})` |
| **Auditor de tests** | **Agente** | `.agents/agents/mutation-auditor/agent.md` | `task({agent_name: "mutation-auditor"})` |

Los agentes son **sesiones independientes** con sus propias directrices en `agent.md`. El orquestador les pasa contexto quirúrgico (tarea, ficheros, restricciones) porque **no heredan esta conversación**.

> ⚠️ **Cada agente tiene DOS copias, y solo una manda.** La del repo (`.agents/agents/`) es la **fuente de verdad**: versionada y portable. La de `~/.minimax/agents/` es un **espejo** que MiniMax Code necesita porque lee de ahí, y que Antigravity no ve. **Edita siempre la del repo** y luego sincroniza:
> ```bash
> python .taskmaster/sync_agents.py --check   # exit 1 si divergen
> python .taskmaster/sync_agents.py           # copia repo -> espejo
> ```
> Editar el espejo es trabajo perdido: no está en git y el siguiente `sync` lo sobrescribe. Detalle en `.agents/agents/README.md`.

### El bucle tiene 4 pasos, no 3

`1. Buscar → 2. Planear → 3. Ejecutar → 4. Auditar los tests → (1)`

El **Paso 4** es obligatorio: `run_tests.py` en verde dice que el código hace lo que el test comprueba, **no** que el test compruebe algo. El `mutation-auditor` rompe cada fix a proposito y confirma que el test lo detecta; un ciclo no se cierra sin su `PASS`. Un superviviente en seguridad o datos se arregla, no se documenta.

> ⚠️ **La forma de delegar depende del runtime donde estés.** El nombre de la
> herramienta no es el mismo: `task` en Minimax Code, `invoke_subagent` en
> Antigravity, `subagent` en OpenCode, `delegate_task` en Hermes. **No inventes
> un nombre ni copies el de otro motor**: mira tus herramientas y usa la que
> exista, y si no hay ninguna, ejecuta un paso por turno leyendo el `agent.md`.
> La tabla completa está en la Sección 0 de `.agents/skills/id-pipeline/SKILL.md`.
>
> Lo que sí es fijo: los cuatro agentes se llaman `architect-review`,
> `openspec-dev`, `process-db-updater` y `mutation-auditor`, y viven en
> `.agents/agents/<nombre>/agent.md`.
> ⚠️ **`tm.py` no es ejecutable aquí** (hace `subprocess` y el entorno lo bloquea con `spawn EPERM`). Lee `.taskmaster/tasks.json` directamente para saber cuál es la tarea activa.
> ⚠️ **Nunca `git` a pelo**: el `.git` del árbol de trabajo está corrupto por el VFS de Nextcloud. Usa `python .taskmaster/git_safe_commit.py "<mensaje>"` y comprueba su código de salida.

**Changelog:** cada pase escribe en **dos** ficheros — `CHANGELOG.md` (raíz, legible por el usuario) y `.taskmaster/CHANGELOG.md` (registro técnico). `validate_docs.py` lo comprueba.

## 🔄 Artefactos del Motor de I+D (`id-pipeline`)

| Artefacto | Path | Rol |
|---|---|---|
| Propuestas activas | `openspec/changes/<id>/` | Contrato de cada cambio. |
| Cambios cerrados | `openspec/changes/archive/<id>/` | Historial inmutable. |
| Tasks pendientes | `.taskmaster/tasks.md` (`.taskmaster/tasks.json`) | Tablero de tareas para el orquestador. |
| Journal por ciclo | `.taskmaster/rd_journal.json` | Machine-readable, datos estructurados. |
| **Changelog por pase** | **`.taskmaster/CHANGELOG.md`** | **Narrativa humano-legible de cada ciclo (MANDATORY)**. |
| Dashboard | `STATUS.md` | Salud del sistema + resumen de hitos. |

