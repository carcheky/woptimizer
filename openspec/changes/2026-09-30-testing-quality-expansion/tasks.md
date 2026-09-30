# Tareas: TASK-034 — Expansión de Calidad y Pruebas Headless

- [x] 1. Auditoría arquitectónica previa con `architect-review`.
- [x] 2. Implementar `test_models_strict_validation_and_contracts()` en `run_tests.py`:
  - [x] Validar rechazo de tipos no booleanos en `is_favorite` e `is_gaming` (`ValidationError`).
  - [x] Validar restricción literal en `default_action` (`ValidationError`).
  - [x] Validar retención de claves desconocidas en `Pack` y `AppData` (`extra="allow"`).
  - [x] Validar defaults de `ProcessInfo` (`exe_path=""`, `category="⚪ Otros"`, `priority="none"`).
- [x] 3. Implementar `test_main_window_navigation_transitions()` en `run_tests.py`:
  - [x] Instanciar `ctk.CTk()` con `withdraw()`.
  - [x] Instanciar `MainWindow` y verificar estado inicial (`DashboardView`, `btn_nav_home` activo con `theme.ACCENT`).
  - [x] Ejecutar `_show_packs()` y validar tipo `PackManagerView`, destrucción anterior y `btn_nav_packs` activo.
  - [x] Ejecutar `_show_process_manager()` y validar tipo `ProcessManagerView`, destrucción anterior y `btn_nav_procs` activo.
  - [x] Ejecutar `_show_home()` y validar retorno a `DashboardView`.
  - [x] Destruir root de forma limpia sin bloqueos.
- [x] 4. Registrar los 2 nuevos tests en el bloque `if __name__ == '__main__':` de `run_tests.py`.
- [x] 5. Actualizar la documentación viva en `docs/ai/testing-guide.md` (suite actualizada a 75 tests).
- [x] 6. Auditar la suite y nuevos tests con `mutation-auditor` (Paso 4).
