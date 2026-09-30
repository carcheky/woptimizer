# Tareas: TASK-035 — Telemetría y Feedback Visual Unificado en Ejecución de Packs

> **Estado: cerrada (ciclo 26, iteración 3).** El `mutation-auditor` dio FAIL dos
> veces sobre esta change. Los literales verdes de abajo se sustituyeron por el
> formateador común tras la primera auditoría; la tercera puerta de feedback
> (`ProcessManagerView.on_kill_selected`) y la rama no-gaming de la portada se
> cerraron en la iteración 3. Detalle en `docs/ai/ui-design-system.md`.

- [x] 1. Auditoría arquitectónica previa con `architect-review`.
- [x] 2. Implementar `_show_start_banner` en `DashboardView` (`src/woptimizer/ui/views/dashboard_view.py`):
  - [x] Renderizar mensaje de apps iniciadas y fallidas con `theme.ACCENT` o `theme.WARNING`.
  - [x] Refrescar telemetría de reposo (`_update_resting_bar()`).
  - [x] Auto-ocultar con `_schedule_ui(AUTOOCULTADO_MS, self._hide_banner)`. **Iter 3:** el cancel + reprograma se extrajo a `_reprogramar_autoocultado()` y lo llaman las dos puertas, con `AUTOOCULTADO_MS = 5000` como constante.
- [x] 3. Implementar feedback inline en `PackManagerView` (`src/woptimizer/ui/views/pack_manager_view.py`):
  - [x] En `kill_pack._run`: publicar `texto, color = mensaje_cierre_pack(nombre, killed, failed, skipped, freed_mb)` y `self.after(0, self._inline_status, texto, color)`. **No** se emite el literal verde: con `killed == 0` mentía.
  - [x] En `start_pack._run`: emitir `self.after(0, self._inline_status, f"🚀 {started} apps iniciadas · '{nombre}'.", VERDE)` (o advertencia con fallidas).
  - [x] En `start_pack` sin apps: emitir `_inline_status(..., AMBAR)`.
- [x] 4. **Iter 3 · tercera puerta de feedback** en `ProcessManagerView` (`src/woptimizer/ui/views/process_manager_view.py`):
  - [x] `on_kill_selected._kill` solo publica por `self.after(0, self._publicar_cierre, ...)`.
  - [x] `_publicar_cierre` formatea con el **mismo** `mensaje_cierre_pack` (sustantivo parametrizable `"procesos"`, nombre `"{N} seleccionadas"`) y programa el refresco de lista a 1000 ms.
  - [x] `_do_load` publica por `self.after(0, self._apply_load, procs)`; la agrupación pura vive en el módulo (`_agrupar`) para que el worker no toque la vista.
- [x] 5. Añadir pruebas discriminantes en `run_tests.py`:
  - [x] `test_el_feedback_de_pack_dice_la_verdad`: cuatro desenlaces por las tres puertas, rama no-gaming de la portada, orden de la 4-tupla, `killed == 1`, `"✅" not in texto` en las ramas `nada` y `fallo`, barra de reposo por texto, temporizadores con reloj simulado en **las dos** puertas del banner, guardas preventivas de `execute_pack` y `kill_pack`.
  - [x] `test_el_gestor_de_procesos_tampoco_miente`: la tercera puerta, entrando por `on_kill_selected` de verdad.
  - [x] `test_los_workers_de_pack_solo_publican_por_after`: pares `(raiz, metodo)`, descenso por `ast.Subscript`, y alcance explícito de los cinco workers de vista.
- [x] 6. Registrar los tests en `run_tests.py` y en la tabla de `docs/ai/testing-guide.md`.
- [x] 7. Actualizar `docs/ai/ui-design-system.md` y `docs/ai/testing-guide.md`, incluidas las afirmaciones que mentían (nombre de test inexistente, cobertura de la guarda, alcance del bloque de temporizadores, y "las dos alimentan el mismo formateador").
- [x] 8. Auditar con `mutation-auditor` (Paso 4) — **3 vueltas**: iteración 1 (FAIL), iteración 2 (FAIL), iteración 3 (cierre). El veredicto final lo da el `mutation-auditor`, no la implementación.
