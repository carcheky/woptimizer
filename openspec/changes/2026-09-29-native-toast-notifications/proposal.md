# Propuesta OpenSpec: Notificaciones Nativas Windows (Toast Balloon vía Tray)

## Contexto y Motivación
Hoy, cuando el usuario activa el pack Gaming desde la Portada, mata procesos manualmente desde el Gestor, o lanza apps desde un pack, **solo obtiene feedback dentro de la propia ventana** (banner en DashboardView o status_label inline). Si la ventana está minimizada al system tray —el modo de uso natural de `woptimizer.exe` tras pulsar `[X]`—, el usuario **no se entera del resultado** hasta que abre la app.

Las **notificaciones nativas Windows (toast balloon)** muestran un popup efímero en la esquina inferior derecha del escritorio, incluso cuando la ventana está oculta. Son el canal estándar para "algo pasó en background, míralo".

## Diseño Técnico
1. **Nuevo servicio `NotificationService` (`src/woptimizer/services/notification_service.py`):**
   - Envuelve `pystray.Icon.notify(message, title)`, que ya está disponible sin dependencias nuevas (`pystray` se añadió en TASK-012).
   - API:
     - `attach_tray(icon: pystray.Icon)` — guarda referencia cuando el tray arranca.
     - `detach_tray()` — limpia referencia al cerrar/reabrir la ventana.
     - `notify(title: str, message: str) -> bool` — muestra balloon. Si no hay tray, escribe al log y retorna `False`. **Nunca lanza excepciones** (try/except + `logger.warning`).
     - Helpers semánticos:
       - `notify_kill_result(killed, failed, freed_mb)` — para `kill_selected` y `kill_pack_apps`.
       - `notify_pack_activated(pack_name, killed, freed_mb)` — al ejecutar un pack desde la Portada.
       - `notify_apps_launched(pack_name, launched, failed)` — al ejecutar packs con `default_action='start'`.
   - Thread-safety: `pystray.Icon.notify()` en Windows es seguro desde cualquier hilo (delega internamente al thread del tray). Si falla, log y a otra cosa.

2. **Inyección de dependencias (respeta invariante de 3 capas):**
   - `WOptimizerApp` crea `NotificationService` una sola vez y la inyecta a `MainWindow`.
   - `MainWindow` la reenvía a `DashboardView`, `PackManagerView`, `ProcessManagerView` en sus constructores.
   - `WOptimizerApp.show_tray()` llama `self.notification_service.attach_tray(self.tray_icon)` tras crear el icono.
   - `WOptimizerApp.show_action()` (clic en "Mostrar App") llama `self.notification_service.detach_tray()` antes de `self.tray_icon = None`.

3. **Auto-arranque del tray siempre (incluso en modo dev):**
   - Hoy, en dev (`python run.py`), el tray **nunca se crea** (porque `on_window_close` sale en vez de ocultar). Esto impide que las notificaciones funcionen al desarrollar.
   - Fix mínimo: instanciar el tray en `__init__` también, en modo daemon, para que `notify()` siempre tenga un icono al que llamar. La ventana sigue mostrándose normal.

4. **Puntos de notificación:**
   - `DashboardView.execute_pack()` → tras `kill_pack_apps`, en el callback del hilo principal, llamar `self.notification_service.notify_pack_activated(...)`.
   - `PackManagerView` → tras ejecutar pack, mismo flujo.
   - `ProcessManagerView` → tras `kill_selected`, llamar `self.notification_service.notify_kill_result(...)`.
   - `app.py` `gaming_action` del tray → tras `kill_pack_apps`, notificar resultado.

5. **Documentación viva:**
   - `docs/ai/architecture.md` añadir regla #8 sobre `NotificationService`.
   - `docs/ai/ui-design-system.md` mencionar cómo se inyecta el servicio a las vistas.

## Invariantes a Respetar
- **Separación de capas:** UI no llama a `pystray` directamente; siempre pasa por `NotificationService`. La UI solo conoce la API `notify_*()`.
- **Cero nuevas dependencias:** se reutiliza `pystray` (ya en `pyproject.toml` transitivamente). Si `pystray` no provee `notify()` en alguna plataforma, fallback silencioso al log.
- **Thread-safety:** las notificaciones se llaman desde callbacks que ya están en el hilo principal (`self.after(0, ...)`) o desde threads daemon que delegan a Windows API; ningún riesgo de tocar widgets desde hilo secundario.
- **No bloquear:** `notify()` retorna inmediatamente (Windows muestra el balloon en background).

## Entregables
- `src/woptimizer/services/notification_service.py` (nuevo, ~60 líneas).
- `src/woptimizer/ui/app.py` modificado: instanciar `NotificationService`, auto-arrancar tray, attach/detach.
- `src/woptimizer/ui/main_window.py` modificado: reenviar el servicio a las vistas.
- `src/woptimizer/ui/views/{dashboard,pack_manager,process_manager}_view.py` modificados: recibir y usar `notification_service`.
- `docs/ai/architecture.md` actualizado con regla #8.
- `tests/test_services.py`: 2-3 tests headless que cubran `notify()` sin tray, `attach/detach`, helpers semánticos.