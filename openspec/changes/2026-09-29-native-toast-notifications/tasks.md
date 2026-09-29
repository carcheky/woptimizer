# Tareas OpenSpec: Notificaciones Nativas Windows (Toast)

- [ ] **1. NotificationService base (TASK-019)**
  - [ ] Crear `src/woptimizer/services/notification_service.py` con clase `NotificationService`.
  - [ ] Métodos: `attach_tray(icon)`, `detach_tray()`, `notify(title, message) -> bool`.
  - [ ] Helpers: `notify_kill_result(killed, failed, freed_mb)`, `notify_pack_activated(name, killed, freed_mb)`, `notify_apps_launched(name, launched, failed)`.
  - [ ] Try/except + `logger.warning` en `notify()` para nunca romper el flujo.
  - [ ] Fallback silencioso al log si no hay tray (modo dev o pre-attach).

- [ ] **2. Inyección y auto-arranque del tray**
  - [ ] `WOptimizerApp.__init__` instancia `self.notification_service = NotificationService()`.
  - [ ] Mover `show_tray()` (o su lógica de creación del icono) a un helper llamado también desde `__init__`, para que el tray exista siempre.
  - [ ] `show_tray()` → tras crear el icono: `self.notification_service.attach_tray(self.tray_icon)`.
  - [ ] `show_action()` → antes de poner `self.tray_icon = None`: `self.notification_service.detach_tray()`.

- [ ] **3. Propagación a las vistas**
  - [ ] `MainWindow.__init__` acepta `notification_service` y lo reenvía.
  - [ ] `DashboardView`, `PackManagerView`, `ProcessManagerView` aceptan `notification_service` en su constructor.
  - [ ] `DashboardView.execute_pack` → tras kill, notificar `notify_pack_activated`.
  - [ ] `PackManagerView` → al ejecutar pack, notificar idem.
  - [ ] `ProcessManagerView` → tras `kill_selected`, notificar `notify_kill_result`.

- [ ] **4. Tests headless**
  - [ ] Añadir a `tests/test_services.py`: `test_notification_no_tray_logs_only`, `test_attach_detach_idempotent`, `test_helpers_format_messages`.
  - [ ] Verificar que ningún test toca pystray real (mock o sin tray).

- [ ] **5. Documentación viva**
  - [ ] `docs/ai/architecture.md` añadir regla #8: NotificationService como servicio transversal inyectado.
  - [ ] `docs/ai/ui-design-system.md` mencionar el nuevo parámetro `notification_service` en constructores de vistas.

- [ ] **6. Commit y verificación**
  - [ ] `python verify_ui_syntax.py` debe pasar.
  - [ ] `python run_tests.py` debe pasar.
  - [ ] Commit: `chore(architect): planificar TASK-019` y luego `feat(notifications): TASK-019 ...`.