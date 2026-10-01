# Change Proposal: System Tray Gaming Session Restoration and Status Telemetry (TASK-043)

## 1. Contexto y Motivación
En el **Ciclo #33** (Área 2: Gaming & Telemetría UX), se busca conectar la funcionalidad de Restauración Inteligente de Apps (`TASK-038`) directamente con el menú contextual de la bandeja de sistema (`pystray`).
Actualmente, `GamingService.restore_gaming_session()` solo es accesible desde la Portada (`DashboardView`). Al minimizar la aplicación al tray icon durante o después del juego, el usuario carece de la opción de restaurar las aplicaciones cerradas desde el menú contextual del System Tray.

## 2. Cambios Propuestos
1. **Acción de Restauración en System Tray**:
   - Integrar la opción "Reabrir aplicaciones cerradas" en el menú contextual de `pystray` que invoca `GamingService.restore_gaming_session()` en segundo plano.
   - Enviar una notificación nativa (`NotificationService.notify_apps_launched` o `notify`) informando de las aplicaciones restauradas.

2. **Indicador de Estado Contextual**:
   - Desactivar o ajustar la opción del menú cuando no existan aplicaciones cerradas pendientes de restauración (`GamingService.get_last_closed_apps()` vacío).

3. **Pruebas Headless**:
   - Añadir tests en `run_tests.py` que comprueben la integración del menú del tray y el despacho de restauración.

## 3. Criterios de Aceptación
- La opción de menú contextual del tray permite restaurar la sesión gaming de forma asíncrona.
- Se notifica nativamente el resultado de la restauración.
- Suite de `run_tests.py` incrementada a 88+ tests al 100% en verde.
- `verify_ui_syntax.py` y `validate_docs.py` con 0 fallos.
