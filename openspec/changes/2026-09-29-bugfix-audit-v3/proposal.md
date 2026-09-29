# Propuesta: Bugfix Audit v3 — Correcciones Post-Auditoría Opus 4.6

## Contexto y Motivación

Auditoría completa del codebase realizada el 2026-09-29. Se detectaron **20 issues** (3 críticos, 4 altos, 7 medios, 5 bajos). Esta spec agrupa los fixes en 4 tareas ejecutables independientes y ordenadas por impacto.

**Hallazgo más grave:** `GamingService.should_kill_for_gaming()` existe y está bien implementado, pero **nunca se invoca en runtime**. La feature de categorías automáticas del Gaming Mode es código muerto. Solo mata `apps` (lista manual, tipicamente solo `chrome.exe`).

---

## Decisión Arquitectónica: FIX-006 (Favoritos)

Se opta por **múltiples favoritos** (no single-favorite). Razones:
- La UI del Dashboard ya itera sobre una lista de favoritos con grid de 2 columnas — la intención original era multi-favorito.
- `set_favorite(pack_id)` con radio-button exclusivo fue una implementación incompleta.
- La solución correcta es un toggle puro por pack, independiente del resto.

---

## Decisión Arquitectónica: FIX-003 (start_pack_apps)

Estrategia de lanzamiento en 2 fases:
1. El model `Pack.apps` guarda `exe_path` (ruta completa) cuando la app se añade desde el Process Manager (ya disponible en `ProcessInfo.exe_path`).
2. `start_pack_apps` intenta `subprocess.Popen([exe_path])` si parece ruta, fallback a `os.startfile(app)` para compatibilidad con entradas legacy (nombres sin ruta).
3. Eliminar `shell=True` en todos los casos.

---

## Bloques de Trabajo

### TASK-025: Conectar GamingService al runtime (FIX-002 + FIX-008)
**Scope:** `gaming_service.py`, `app.py`, `dashboard_view.py`, `pack_manager_view.py`
- Añadir `execute_gaming_pack(pack)` a `GamingService` (scan + filter + kill usando `should_kill_for_gaming()`).
- Inyectar `gaming_service` en `DashboardView` y `PackManagerView`.
- `execute_pack()` en Dashboard y `kill_pack()` en PackManager usan la nueva API cuando `pack.is_gaming`.
- `gaming_action` del tray también usa la nueva API.

### TASK-026: Bugfixes Críticos de Datos y Servicio (FIX-001 + FIX-005 + FIX-007 + FIX-009)
**Scope:** `pack_service.py`, `process_service.py`, `process_manager_view.py`
- FIX-001: `get_gaming_pack()` → `model_copy(deep=True)` en fallback.
- FIX-005: `_DEFAULT_META` → `"⚪ Otros"` (con emoji, no `?`).
- FIX-007: Eliminar race condition en `_do_load()` — datos se acumulan en variables locales del hilo y se asignan a `self.*` solo desde el callback `after()`.
- FIX-009: Backup `profiles.json` → `profiles.json.bak` en `PackService.save()`.

### TASK-027: Bugfixes de UI y Comportamiento (FIX-003 + FIX-004 + FIX-006)
**Scope:** `process_service.py`, `process_manager_view.py`, `pack_manager_view.py`, `pack_service.py`
- FIX-003: `start_pack_apps` sin `shell=True`, con rutas absolutas + fallback `os.startfile`.
- FIX-004: Ordenar categorías en `_render_list` por `CATEGORY_ORDER` (no `sorted()` alfabético).
- FIX-006: `set_favorite` → toggle puro por pack (múltiples favoritos simultáneos posibles).

### TASK-028: Limpieza y Deuda Técnica (FIX-010 a FIX-020)
**Scope:** `config.py`, `__main__.py`, root del repo, `docs/ai/data-models.md`
- FIX-010: Mover `logging.basicConfig` a `__main__.py` como `setup_logging()`.
- FIX-011: Eliminar `PROCESS_LIST_FILE` huérfana.
- FIX-012: Simplificar `is_expanded = True`.
- FIX-013: Script de migración `procesos.csv` → `process_db.json` (+84 entradas).
- FIX-014: Crear `tests/` y mover tests válidos.
- FIX-015: Eliminar JSON legacy del root.
- FIX-016: Eliminar `import sys` duplicado.
- FIX-017: Eliminar/archivar `inconsistencies_plan.md`.
- FIX-018: Unificar versión en `3.0.1`.
- FIX-020: Actualizar `data-models.md`.

---

## Criterios de Aceptación (TASK-025, la más crítica)

- `python verify_ui_syntax.py` en verde.
- Test headless: `GamingService.execute_gaming_pack()` con un proceso en `target_categories` → lo incluye; con un proceso en `keepers` → lo excluye.
- Al pulsar "Gaming Mode" en el tray, los procesos de las categorías activas se cierran (no solo `chrome.exe`).
- `gaming_service` ya no es parámetro fantasma en `MainWindow`.

## Notas de Arquitectura

- TASK-025 es bloqueante de TASK-027 (el tray y la UI de dashboard dependen de la nueva API).
- TASK-026 es independiente y puede ir en paralelo con TASK-025.
- TASK-028 va siempre al final.
- FIX-013 (migrar CSV) es la tarea con más valor de datos pero la menos urgente técnicamente.
- Los archivos `test_*.py` del root NO deben eliminarse sin revisar su contenido — algunos cubren casos que aún no están en `tests/`.
