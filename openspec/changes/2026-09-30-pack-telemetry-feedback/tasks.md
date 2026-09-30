# Tareas: TASK-035 — Telemetría y Feedback Visual Unificado en Ejecución de Packs

- [ ] 1. Auditoría arquitectónica previa con `architect-review`.
- [ ] 2. Implementar `_show_start_banner` en `DashboardView` (`src/woptimizer/ui/views/dashboard_view.py`):
  - [ ] Renderizar mensaje de apps iniciadas y fallidas con `theme.ACCENT` o `theme.WARNING`.
  - [ ] Refrescar telemetría de reposo (`_update_resting_bar()`).
  - [ ] Auto-ocultar con `_schedule_ui(5000, self._hide_banner)`.
  - [ ] Enlazar en `_run_start` vía `self.after(0, self._show_start_banner, launched, failed, p.name)`.
- [ ] 3. Implementar feedback inline en `PackManagerView` (`src/woptimizer/ui/views/pack_manager_view.py`):
  - [ ] En `kill_pack._run`: emitir `self.after(0, self._inline_status, f"✅ {killed} procesos cerrados ({freed_mb:.1f} MB liberados) · '{nombre}'.", VERDE)`.
  - [ ] En `start_pack._run`: emitir `self.after(0, self._inline_status, f"🚀 {started} apps iniciadas · '{nombre}'.", VERDE)` (o advertencia con fallidas).
  - [ ] En `start_pack` sin apps: emitir `_inline_status(..., AMBAR)`.
- [ ] 4. Añadir prueba discriminante `test_pack_execution_ui_telemetry_feedback` en `run_tests.py`:
  - [ ] Validar banners de DashboardView (kill y start) con colores semánticos.
  - [ ] Validar actualización de `status_label` en PackManagerView.
  - [ ] Validar mediante AST que ningún hilo secundario toca UI directamente sin `self.after`.
- [ ] 5. Registrar nuevo test en `run_tests.py` elevando la suite a 76 tests.
- [ ] 6. Actualizar `docs/ai/ui-design-system.md` y `docs/ai/testing-guide.md`.
- [ ] 7. Auditar con `mutation-auditor` (Paso 4).
