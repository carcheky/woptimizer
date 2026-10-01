# Proposed Change: Pruebas de Contratos de Ciclo de Vida y Estados en Mixin Confirmable (Ciclo #36)

- **ID:** `2026-10-01-confirmable-mixin-contracts`
- **Task:** `TASK-046`
- **Área:** Testing & Calidad (Área 5)

## Motivo y Alcance
Aunque la máquina de estados pura `DoubleTapGuard` cuenta con pruebas en `run_tests.py`, el mixin `Confirmable` en `src/woptimizer/ui/confirmation.py` —que orquesta la interacción real con los botones (`text`, `fg_color`, `hover_color`, `state`), el etiquetado en `status_label`, el auto-revert por expiración, el cambio de token entre pulsaciones y la limpieza defensiva en `cancel_on_destroy`— carece de una prueba unitaria headless discriminante que verifique los contratos y transiciones de los widgets sin requerir ventana Tkinter activa.

## Cambios Clave
- Añadir `test_confirmable_mixin_lifecycle_and_widget_contracts` en `run_tests.py` empleando un harness headless ligero con `_FakeScheduler` y widgets mock (`DummyButton`, `DummyLabel`).
- Validar rigurosamente:
  1. Estado inicial e inicialización cooperativa (`_init_confirmable`).
  2. Primera pulsación: captura de estado de reposo, mutación a `PENDIENTE_TEXT` / `PENDIENTE_FG` / `PENDIENTE_HOVER`, y feedback en `status_label` con `AMBAR`.
  3. Segunda pulsación: ejecución confirmada (`True`), restauración de propiedades previas del botón y cancelación de timers.
  4. Inserción de nuevo token antes de confirmar: descarte de intención previa y sustitución por `changed_text`.
  5. Expiración de ventana: disparo de `_on_expirado`, restauración de widget y emisión de `MSG_EXPIRADO`.
  6. Cancelación explícita con `_cancel_confirm()` y destrucción defensiva con `cancel_on_destroy()`.
- Actualizar `docs/ai/testing-guide.md`, `STATUS.md`, `AGENTS.md` y `README.md` sincronizando el nuevo total de 90 tests.
