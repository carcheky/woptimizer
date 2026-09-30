# Propuesta: TASK-035 — Telemetría y Feedback Visual Unificado en Ejecución de Packs (Portada y Gestor)

## Contexto y Motivación
En el Área 2 (Gaming & Telemetría UX), la ejecución de packs ofrece feedback dispar e incompleto según desde qué vista se invoque y qué acción se ejecute:
1. **Portada (`DashboardView`)**:
   - La acción `kill` (Gaming Mode o packs de apagado) muestra un banner enriquecido en pantalla (`_show_banner`) indicando procesos cerrados y MB de RAM liberados, y actualiza la banda de telemetría permanente en reposo (`resting_bar`).
   - Sin embargo, la acción `start` (packs de lanzamiento de juegos o utilidades) ejecuta `self.process_service.start_pack_apps` en segundo plano, emite un toast en la bandeja del sistema pero **no muestra ningún banner en pantalla ni actualiza la telemetría en reposo**. Si el usuario tiene las notificaciones de Windows silenciadas (Asistente de concentración / Modo Juego), no recibe confirmación visual en pantalla.
2. **Gestor de Packs (`PackManagerView`)**:
   - Tanto `kill_pack` como `start_pack` ejecutan sus acciones en hilos secundarios y emiten toasts nativos, pero **dejan `self.status_label` completamente vacío**.
   - El usuario pulsa "Apagar" (doble pulsación confirmada) o "Iniciar" y no observa ninguna actualización en el texto de estado de la vista (`status_label`), a pesar de que la vista dispone de `Confirmable._inline_status()`.

## Objetivos
1. **En `DashboardView`**:
   - Implementar `_show_start_banner(self, launched: int, failed: int, pack_name: str)` para mostrar feedback inline en `status_banner_frame` con los tokens semánticos correspondientes (`theme.ACCENT` en éxito, `theme.WARNING` ante fallos parciales) y auto-ocultación a los 5 segundos vía `_schedule_ui`.
   - Conectar `_run_start` para invocar `self.after(0, self._show_start_banner, launched, failed, p.name)` y refrescar el contador de telemetría de procesos activos con `_update_resting_bar()`.
2. **En `PackManagerView`**:
   - En `kill_pack`: al finalizar el hilo de kill, emitir feedback al hilo principal vía `self.after(0, self._inline_status, f"✅ {killed} procesos cerrados ({freed_mb:.1f} MB liberados) · '{nombre}'.", VERDE)`.
   - En `start_pack`: al finalizar el arranque, emitir feedback vía `self.after(0, self._inline_status, ...)` informando apps iniciadas o fallidas.
   - En caso de packs sin apps en `start_pack`: mostrar aviso preventivo `⚠️ '{pack.name}' no tiene apps que iniciar.` vía `_inline_status(..., AMBAR)`.
3. **Pruebas y Validación**:
   - Crear `test_pack_execution_ui_telemetry_feedback` en `run_tests.py`:
     - Validar que `DashboardView` renderiza banners para `kill` y `start` con los textos y colores semánticos previstos.
     - Validar que `PackManagerView` actualiza `status_label` tras ejecutar `kill_pack` y `start_pack`.
     - Validar mediante análisis AST que ninguna llamada de UI se realiza directamente desde los hilos secundarios (todas a través de `self.after(0, ...)`).
   - Actualizar `docs/ai/ui-design-system.md` documentando la unificación de telemetría y feedback visual en ejecución de packs.

## Criterios de Aceptación
- La ejecución de packs (start o kill) muestra feedback visual inmediato en pantalla tanto en la Portada como en el Gestor de Packs.
- Seguridad de hilos estricta: UI nunca se muta desde hilos secundarios (siempre vía `self.after(0, ...)`).
- Suite de tests `run_tests.py` (76 tests) y `validate_docs.py` en verde al 100%.
