# 🎯 Taskmaster Board — woptimizer v3

> Sistema de orquestación de tareas atómicas para agentes IA y desarrolladores.
> **Única fuente de verdad estructurada:** [tasks.json](file:///c:/Users/carch/Nextcloud/Scripts/woptimizer/.taskmaster/tasks.json)
> ⚠️ **La CLI `tm.py` NO es ejecutable en este entorno** (`spawn EPERM`). Consulta `.taskmaster/tasks.json` directamente (`active_task_id` o primer `"status": "pending"`).

---

## 📌 Tareas Activas y Prioritarias (Backlog Inmediato)

| ID | Tarea | Complejidad | Prioridad | Estado | Módulo / Spec |
|---|---|:---:|:---:|:---:|---|
| **TASK-073** | Prevenir RuntimeError en ProcessManagerView._load tras destrucción | 3/10 | 🟠 High | ⏳ **PENDING** (Active) | `src/woptimizer/ui/views/process_manager_view.py` |
| **TASK-074** | Blindar paridad de git tooling: código 2 en par asimétrico | 2/10 | 🟡 Medium | ⏳ PENDING | `run_tests.py` / `sandbox-rules.md` |
| **TASK-075** | Desacoplar validate_docs.py de %LOCALAPPDATA% para CI | 4/10 | 🟡 Medium | ⏳ PENDING | `validate_docs.py` |
| **TASK-076** | Desduplicar flags de PyInstaller entre force_build y release.yml | 3/10 | 🟡 Medium | ⏳ PENDING | `force_build.py` / `.github/workflows/` |
| **TASK-077** | Normalizar finales de línea CRLF en scripts Windows (.bat/.ps1) | 1/10 | 🟢 Low | ⏳ PENDING | `build.bat` / `benchmark.py` |
| **TASK-068** | Arranque por categorías en el Gestor (T-4 pendiente decisión dueño) | 6/10 | 🟠 High | 🔄 IN_PROGRESS | `openspec/changes/2026-10-05-arranque-por-categorias-en-el-gestor/` |

---

## 🧭 Flujo de Trabajo para IAs
1. Consultar la tarea activa leyendo `.taskmaster/tasks.json` (`active_task_id`, o la primera con `"status": "pending"`). **No uses `tm.py`**: no es ejecutable aquí.
2. Cargar **únicamente** la documentación indicada en la columna `Documentación Asociada` / `Spec` para no gastar tokens.
3. Completar la tarea respetando las invariantes arquitectónicas.
4. Marcar la tarea como completada poniendo `"status": "completed"` en `.taskmaster/tasks.json`.
5. Ejecutar la batería de verificación: `python run_tests.py`, `python verify_ui_syntax.py`, `python validate_docs.py`.
6. Comitear usando `python .taskmaster/git_safe_commit.py "<tipo>(<alcance>): <descripción> (TASK-NNN)"`.

---

## 📋 Resumen Histórico de Tareas Cerradas Recientes
- **TASK-071** (Ciclo #61): Aplicaciones protegidas: pack no ejecutable e indestructible.
- **TASK-072** (Ciclo #60): Fix hang en run_tests.py: _git_de_fixture sin stdin=DEVNULL.
- **TASK-070** (Ciclo #59): validate_docs.py optimizado de O(n^2) a O(n) tokenización (`splitlines`).
- **TASK-069** (Ciclo #56): Migración y protección de profiles.json a `%APPDATA%\woptimizer` sin pérdida de datos.
- **TASK-067** (Ciclo #55): Re-anclaje de trazabilidad documental y checklists de release.
- **TASK-066** (Ciclo #54): Puerta de cabecera commitlint (<=120 caracteres) y regla de ramas.
- **TASK-065** (Ciclo #51): Menú de favoritos en bandeja del sistema con confirmación.
- **TASK-063** (Ciclo #50): Selección y arranque por categorías unificada para todos los packs.
- **TASK-061** (Ciclo #53): Código 1 y paridad estricta de entorno en `git_safe_commit.py`.
- **TASK-060** (Ciclo #49): Check 8 de anclas sobre Deuda Técnica Conocida en `validate_docs.py`.
- **TASK-059** (Ciclo #52): Ancla obligatoria en mensajes de commit y check 9 de hashes en journal.
