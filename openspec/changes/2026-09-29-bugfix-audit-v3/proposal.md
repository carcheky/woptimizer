# Propuesta: Bugfix Audit v3 — Correcciones Post-Auditoría Opus 4.6 (Revisión Arquitectónica)

## Contexto y Motivación

Auditoría completa del codebase realizada el 2026-09-29. Se detectaron 20 issues potenciales. Esta spec analiza la viabilidad arquitectónica, previene regresiones con respecto a ciclos anteriores (#10, #12, #13) y agrupa los fixes en 4 tareas ejecutables independientes.

**Hallazgo más grave confirmado:** `GamingService.should_kill_for_gaming()` existe y está testeado, pero **nunca se invoca en runtime**. La feature de categorías automáticas del Gaming Mode es código muerto; ni el tray ni las vistas la llaman.

---

## Decisiones y Blindajes Arquitectónicos

### 1. Resolución de Favoritos (FIX-006) vs Test Invariante TASK-021
- **Riesgo detectado en auditoría:** Opus 4.6 propuso alterar `PackService.set_favorite` para permitir múltiples favoritos. **Esto rompería `test_pack_service_favorite_exclusive()` de `run_tests.py`**, fijado normativamente en el Ciclo 10 (TASK-021) y `get_favorite_pack() -> Optional[Pack]`.
- **Decisión Arquitectónica:** El backend de `PackService` mantiene su contrato exclusivo (`set_favorite(pack_id)` activa uno, `set_favorite(None)` desmarca todos). El bug real residía en la UI (`pack_manager_view.py:toggle_favorite`), que re-enviaba `pack_id` en vez de `None` cuando el pack ya era favorito, impidiendo desmarcarlo.
- **Solución:** Corregir `toggle_favorite` en la vista para alternar entre `pack_id` y `None`.

### 2. Blindaje de Tests Históricos vs FIX-014
- **Regla del Propietario (STATUS.md y docs/ai/testing-guide.md):** Los 11 archivos `test_*.py` heredados de la v2 en la raíz del repo **NO SE BORRAN**. Son referencia histórica protegida.
- **Decisión Arquitectónica:** No se eliminan los 11 archivos de la raíz. La cobertura viva reside única y exclusivamente en `run_tests.py`. Las pruebas de regresión de los fixes de este paquete se añadirán como funciones de prueba directamente dentro de `run_tests.py`.

### 3. Preservación del Blindaje Anti-Brick (Ciclo 13 / TASK-024)
- Al implementar `GamingService.execute_gaming_pack()`, bajo ningún concepto se podrán marcar como candidatos a kill procesos de `SYSTEM_PROTECTED_PROCESSES` (`config.py`), garantizando que la evaluación automática de categorías no mate procesos vitales de Windows.

### 4. Preservación de la Doble Pulsación (Ciclo 12 / TASK-023 / Trampa #14)
- Cualquier modificación a los manejadores de eventos o botones de apagado/ejecución destructiva en `DashboardView` y `PackManagerView` debe respetar el wrapper `DoubleTapGuard` / `Confirmable` de `ui/confirmation.py`.

### 5. Arranque Seguro de Aplicaciones (FIX-003)
- En `process_service.py:start_pack_apps`: suprimir terminantemente `shell=True`. Si la entrada es una ruta ejecutable existente, invocar `subprocess.Popen([app])`. Para nombres genéricos o URIs, utilizar `os.startfile(app)` en Windows con captura de excepciones.
- En `process_manager_view.py:on_add_to_pack`: registrar preferentemente `pinfo.exe_path` en lugar de nombres aislados para packs que se configuren como `start`.

---

## Bloques de Trabajo

### TASK-025: Conectar GamingService al runtime (FIX-002 + FIX-008)
**Scope:** `src/woptimizer/services/gaming_service.py`, `src/woptimizer/ui/app.py`, `src/woptimizer/ui/views/dashboard_view.py`, `src/woptimizer/ui/views/pack_manager_view.py`
- Añadir `execute_gaming_pack(self, gaming_pack: Pack) -> Tuple[int, int, int, float]` en `GamingService`:
  - Obtiene snapshot de procesos activos (`process_service.get_running_processes(force_refresh=True)`).
  - Filtra aquellos donde `should_kill_for_gaming(...)` sea `True` y NO pertenezcan a `SYSTEM_PROTECTED_PROCESSES`.
  - Los finaliza mediante `process_service.kill_processes(...)`.
- Inyectar `gaming_service` en `DashboardView` y `PackManagerView` desde `MainWindow`.
- Conectar `DashboardView.execute_pack()`, `PackManagerView.kill_pack()` y `WOptimizerApp.show_tray -> gaming_action()` a `execute_gaming_pack` cuando `pack.is_gaming` sea `True`.
- Integrar test de validación en `run_tests.py`.

### TASK-026: Integridad de Datos, Copia Profunda y Resiliencia (FIX-001 + FIX-005 + FIX-007 + FIX-009)
**Scope:** `src/woptimizer/services/pack_service.py`, `src/woptimizer/services/process_service.py`, `src/woptimizer/ui/views/process_manager_view.py`
- FIX-001: En `pack_service.py:get_gaming_pack`, cambiar fallback a `DEFAULT_GAMING_PACK.model_copy(deep=True)`.
- FIX-005: En `process_service.py`, corregir `_DEFAULT_META = ("⚪ Otros", "none", "Sin descripción")`.
- FIX-007: Eliminar condición de carrera en `process_manager_view.py:_do_load` acumulando en variables locales del thread y aplicando a `self.processes` / `self.grouped_processes` en el hilo principal (`after(0, ...)`).
- FIX-009: Añadir `shutil.copy(self.data_path, self.data_path + ".bak")` en `PackService.save()` si el fichero existe antes de sobrescribir.
- Añadir tests en `run_tests.py`.

### TASK-027: Robustez de UI y Comportamiento (FIX-003 + FIX-004 + FIX-006)
**Scope:** `src/woptimizer/services/process_service.py`, `src/woptimizer/ui/views/process_manager_view.py`, `src/woptimizer/ui/views/pack_manager_view.py`
- FIX-003: `start_pack_apps` sin `shell=True`, usando `exe_path` y fallback `os.startfile`.
- FIX-004: Ordenar secciones de categoría en `process_manager_view.py:_render_list` según `CATEGORY_ORDER` index en vez de `sorted()` alfabético.
- FIX-006: Corregir `toggle_favorite` en `pack_manager_view.py` alternando entre `pack_id` y `None` para permitir desmarcar favoritos.
- Añadir tests en `run_tests.py`.

### TASK-028: Saneamiento de Deuda Técnica y Limpieza (FIX-010 al FIX-020)
**Scope:** `src/woptimizer/config.py`, `src/woptimizer/__main__.py`, `docs/`, `pyproject.toml`
- FIX-010: Desacoplar `basicConfig` del nivel módulo de `config.py`; crear `setup_logging()` invocado desde `__main__.py`.
- FIX-011: Eliminar constante `PROCESS_LIST_FILE` no utilizada y purgar `saved_processes.json`.
- FIX-012: En `process_manager_view.py`, limpiar ternario redundante `is_expanded = True`.
- FIX-013: Migrar entradas de software y utilidades desde `procesos.csv` a `assets/process_db.json` respetando el blindaje anti-brick.
- FIX-015: Retirar o archivar JSONs residuales del directorio raíz (`profiles.json` v2, `test_profiles_task1.json`).
- FIX-016: Eliminar `import sys` redundante en `app.py:quit_app`.
- FIX-017: Archivar `inconsistencies_plan.md` en `docs/archive/`.
- FIX-018: Unificar versión a `3.0.1` en `pyproject.toml` y `src/woptimizer/__init__.py`.
- FIX-020: Sincronizar `docs/ai/data-models.md` y `docs/ai/architecture.md`.
