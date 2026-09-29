# Tareas OpenSpec: Bugfix Audit v3 (20 Issues Auditados)

- [ ] **1. Conectar GamingService al Runtime (TASK-025 - Crítico)**
  - [ ] Implementar `GamingService.execute_gaming_pack(gaming_pack: Pack) -> Tuple[int, int, int, float]`:
    - Obtener snapshot de procesos (`process_service.get_running_processes(force_refresh=True)`).
    - Filtrar procesos que cumplan `should_kill_for_gaming(p.full_name or p.name, gaming_pack)` y NO pertenezcan a `SYSTEM_PROTECTED_PROCESSES`.
    - Matar procesos seleccionados con `process_service.kill_processes(to_kill)`.
    - Retornar tupla `(killed, failed, skipped, freed_mb)`.
  - [ ] Inyectar `gaming_service` en `DashboardView` y `PackManagerView` desde `MainWindow`.
  - [ ] Actualizar `DashboardView.execute_pack`:
    - Permitir ejecución si `pack.is_gaming` aunque `pack.apps` esté vacío (`if not pack.is_gaming and not pack.apps: return`), ya que Gaming Mode actúa sobre `target_categories`.
    - Si `pack.is_gaming`, llamar a `gaming_service.execute_gaming_pack(pack)` en segundo plano y adaptar el texto de `_require_double_tap` a "⚠️ Segunda pulsación para preparar Gaming Mode."
  - [ ] Actualizar `PackManagerView.kill_pack`:
    - Permitir ejecución si `pack.is_gaming` aunque `pack.apps` esté vacío.
    - Si `pack.is_gaming`, llamar a `gaming_service.execute_gaming_pack(pack)` en segundo plano y adaptar el texto de `_require_double_tap` a "⚠️ Segunda pulsación para apagar apps del Pack Gaming."
  - [ ] Actualizar `WOptimizerApp.show_tray -> gaming_action`: llamar a `gaming_service.execute_gaming_pack(gaming_pack)`.
  - [ ] Añadir test de regresión en `run_tests.py` validando que `execute_gaming_pack` mata apps y categorías configuradas respetando keepers y procesos protegidos de sistema.


- [ ] **2. Integridad de Datos, Servicios y Concurrencia (TASK-026 - Crítico/Alto)**
  - [ ] FIX-001: En `pack_service.py:get_gaming_pack`, cambiar fallback a `DEFAULT_GAMING_PACK.model_copy(deep=True)`.
  - [ ] FIX-005: En `process_service.py`, corregir `_DEFAULT_META = ("⚪ Otros", "none", "Sin descripción")`.
  - [ ] FIX-007: En `process_manager_view.py:_do_load`, procesar en variables locales en el hilo de fondo y publicar a `self.processes` y `self.grouped_processes` solo dentro de `self.master.after(0, _apply)`.
  - [ ] FIX-009: En `pack_service.py:save`, crear backup preventivo con `shutil.copy` a `.bak` si el archivo existe antes de sobrescribir.
  - [ ] Añadir tests unitarios en `run_tests.py` para deep copy en fallback, categoría por defecto y backup preventivo.

- [ ] **3. Correcciones de Comportamiento y UX (TASK-027 - Alto)**
  - [ ] FIX-003: En `process_service.py:start_pack_apps`, eliminar `shell=True`. Soportar ejecución de `exe_path` vía `subprocess.Popen` y fallback seguro con `os.startfile` en Windows. En `process_manager_view.py:on_add_to_pack`, guardar `exe_path`.
  - [ ] FIX-004: En `process_manager_view.py:_render_list`, ordenar categorías usando el índice de `CATEGORY_ORDER` en vez de `sorted()` alfabético por código Unicode.
  - [ ] FIX-006: En `pack_manager_view.py:toggle_favorite`, si el pack ya es favorito invocar `set_favorite(None)` para desmarcarlo; en caso contrario invocar `set_favorite(pack_id)`. Mantener intacto el contrato de `PackService` y `test_pack_service_favorite_exclusive()`.
  - [ ] Añadir tests en `run_tests.py` para toggle de desmarcado de favoritos y orden de categorías.

- [ ] **4. Deuda Técnica y Limpieza del Repositorio (TASK-028 - Medio/Bajo)**
  - [ ] FIX-010: Desacoplar `logging.basicConfig` de la importación de `config.py`; mover a función `setup_logging()`.
  - [ ] FIX-011: Eliminar constante `PROCESS_LIST_FILE` no utilizada y purgar `saved_processes.json`.
  - [ ] FIX-012: En `process_manager_view.py`, limpiar ternario `is_expanded = True`.
  - [ ] FIX-013: Migrar procesos relevantes de `procesos.csv` hacia `assets/process_db.json` manteniendo semáforos exactos y blindaje del sistema.
  - [ ] FIX-014: **PRESERVAR los 11 ficheros `test_*.py` del root por regla de propietario.** Integrar todas las nuevas pruebas en `run_tests.py`.
  - [ ] FIX-015: Retirar o archivar archivos json residuales del directorio raíz (`profiles.json` legacy, `test_profiles_task1.json`).
  - [ ] FIX-016: Eliminar `import sys` redundante en `app.py:quit_app`.
  - [ ] FIX-017: Archivar `inconsistencies_plan.md` en `docs/archive/`.
  - [ ] FIX-018: Unificar versión a `3.0.1` en `pyproject.toml` y `src/woptimizer/__init__.py`.
  - [ ] FIX-020: Sincronizar `docs/ai/data-models.md` y `docs/ai/architecture.md`.
