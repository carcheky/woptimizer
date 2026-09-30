# Propuesta: TASK-034 — Expansión de Calidad y Pruebas Headless (Navegación UI y Contratos de Modelos)

## Contexto y Motivación
En el Área 5 (Testing & Calidad), la suite de pruebas headless `run_tests.py` ha alcanzado 73 pruebas. Sin embargo, persisten dos puntos ciegos en la verificación de calidad:
1. **Transiciones de Navegación en `MainWindow` (UI)**:
   La prueba headless existente `test_headless_ui()` únicamente instancia `WOptimizerApp` y espera 1.5 segundos en reposo. En esa ejecución, solo se renderiza la vista por defecto (`DashboardView`). Las funciones `_show_packs()` (`PackManagerView`) y `_show_process_manager()` (`ProcessManagerView`) nunca son invocadas durante la suite. Si una actualización rompe las dependencias de inicialización de estas vistas, sus listeners, la destrucción de la vista previa en `_clear_content()` o los estilos de la barra de navegación (`_set_active_nav`), las pruebas actuales dan un falso verde.
2. **Validación Estricta de Modelos Pydantic (`models.py`)**:
   `test_models()` solo comprueba valores por defecto superficiales. No valida las garantías estructurales introducidas en los ciclos 10, 19 y 22:
   - `strict=True` en `Pack.is_favorite` e `is_gaming` (rechazo de coerciones de strings e enteros).
   - `default_action` restringido a `Literal["start", "kill"]` (rechazo de acciones no soportadas).
   - `ConfigDict(extra="allow")` en `Pack` y `AppData` (supervivencia de metadatos extra y compatibilidad hacia delante).
   - Valores por defecto de `ProcessInfo` (`exe_path=""`, `category="⚪ Otros"`, `priority="none"`).

## Objetivos
1. Crear la prueba `test_models_strict_validation_and_contracts` en `run_tests.py`:
   - Validar que coerciones laxas (`"true"`, `1`, `"si"`) en campos booleanos estrictos levanten `pydantic.ValidationError`.
   - Validar que valores no permitidos en `default_action` levanten `pydantic.ValidationError`.
   - Validar que campos adicionales desconocidos en `Pack` y `AppData` se preserven intactos en `model_dump()`.
   - Validar que los valores por defecto de `ProcessInfo` respeten el contrato de categorización y resolución lazy.
2. Crear la prueba `test_main_window_navigation_transitions` en `run_tests.py`:
   - Montar un `MainWindow` headless con `root.withdraw()` seguro.
   - Probar la transición a `PackManagerView` (`_show_packs()`), verificando destrucción limpia del frame anterior y actualización del estado activo en `btn_nav_packs`.
   - Probar la transición a `ProcessManagerView` (`_show_process_manager()`), verificando destrucción y foco en `btn_nav_procs`.
   - Probar el retorno a `DashboardView` (`_show_home()`), verificando estado activo en `btn_nav_home`.
   - Comprobar que `_clear_content()` no produce fugas ni excepciones en el ciclo de vida de los widgets.
3. Actualizar `docs/ai/testing-guide.md` registrando los dos nuevos tests y elevando la suite a **75 tests** (73 backend + 2 headless UI).

## Criterios de Aceptación
- La suite de `run_tests.py` corre sin ventanas bloqueantes y pasa al 100%.
- `validate_docs.py` pasa con 0 errores.
- Los nuevos tests discriminan activamente regresiones en modelos y navegación.
