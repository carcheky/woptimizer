# CYCLE-028 — Tasks: Restauración Inteligente de Apps tras Modo Gaming

Contrato: `openspec/changes/2026-10-01-gaming-session-restoration/proposal.md`.
Dueño: `openspec-dev`.

- [ ] **T-28.1 — Captura de ejecutable e historial de sesión en `GamingService`.**
      Añadir `self._last_closed_apps: List[str]` en `GamingService.__init__`. En `execute_gaming_pack()`, resolver la ruta ejecutable de cada proceso en `to_kill` con `get_process_exe_path(p.pid)` si `p.exe_path` está vacía, y guardar las rutas válidas sin duplicados en `self._last_closed_apps`.
      Añadir `get_last_closed_apps() -> List[str]` y `clear_last_closed_apps() -> None`.

- [ ] **T-28.2 — Método `restore_gaming_session` en `GamingService`.**
      Añadir `restore_gaming_session() -> Tuple[int, int]`: llama a `self.process_service.start_pack_apps(self._last_closed_apps)`, resetea `self._last_closed_apps = []` y retorna `(started, failed)`.

- [ ] **T-28.3 — Integración de botón/banner de restauración en `DashboardView`.**
      Añadir método `_show_restore_banner` y botón de acción `"Restaurar Apps Cerradas ({N})"` en la Portada cuando `gaming_service.get_last_closed_apps()` contenga ejecutables. Ejecutar `restore_gaming_session()` en hilo secundario y publicar resultado vía `self.after(0, ...)`.

- [ ] **T-28.4 — Pruebas unitarias discriminantes en `run_tests.py`.**
      Añadir `test_gaming_service_session_restoration` cubriendo la acumulación de rutas, consulta, vaciado y reapertura.

- [ ] **T-28.5 — Actualización de documentación viva y sincronización de tests.**
      Actualizar `docs/ai/architecture.md`, `docs/ai/ui-design-system.md`, `docs/ai/testing-guide.md`, `STATUS.md`, `AGENTS.md` y `README.md`.

- [ ] **T-28.6 — Auditoría de mutación (Paso 4, `mutation-auditor`).**
      Verificar que las mutaciones sobre `_last_closed_apps` y `restore_gaming_session` sean aniquiladas por aserción con veredicto PASS.
