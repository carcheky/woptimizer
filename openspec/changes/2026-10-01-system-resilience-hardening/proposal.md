# Change Proposal: System Resilience and Concurrency Hardening (TASK-042)

## 1. Contexto y Motivación
En el marco del **Ciclo #32** del Motor Autónomo Perpetuo de I+D (Área 1: Resiliencia & Robustez), se aborda el fortalecimiento defensivo de la concurrencia y tolerancia a fallos en `ProcessService`, `NotificationService` y `WOptimizerApp`.
A pesar de la alta resiliencia lograda en ciclos previos, la interacción con la bandeja de sistema (`pystray`), el refresco en segundo plano y la terminación de procesos en Windows bajo escenarios de alta carga o permisos reducidos presentan bordes sutiles:
1. `NotificationService` puede sufrir carreras en multihilo durante el arranque/cierre rápido o reinicio del icono de bandeja de sistema.
2. `ProcessService.get_process_exe_path` y `kill_processes` deben garantizar protección absoluta contra cualquier excepción imprevista de `psutil` (`ZombieProcess`, `AccessDenied`, `NoSuchProcess`, `OSError`) al iterar subprocesos hijos.
3. Cierre ordenado y seguro de hilos demonio y recursos al salir de la aplicación.

## 2. Cambios Propuestos
1. **Thread-Safety en NotificationService**:
   - Garantizar sincronización atómica con RLock en la vinculación (`attach_tray`) y desvinculación (`detach_tray`) del tray icon.
   - Proteger cualquier invocación `notify` ante estados transitorios donde el tray icon esté siendo destruido o reiniciado.

2. **Resiliencia Defensiva en ProcessService**:
   - Reforzar el manejo defensivo en `kill_processes` y `kill_pack_apps` para capturar `psutil.ZombieProcess` y `OSError` en la búsqueda recursiva de hijos sin interrumpir la métrica RSS liberada.

3. **Pruebas Headless Discriminantes**:
   - Añadir tests en `run_tests.py` que simulen concurrencia en `NotificationService` y excepciones de psutil durante el kill recursivo.

## 3. Criterios de Aceptación
- `NotificationService` thread-safe bajo attach/detach concurrente.
- `kill_processes` maneja `ZombieProcess` y `OSError` de psutil sin abortar la operación ni fallar en la suma RSS.
- Suite de `run_tests.py` incrementada a 87+ tests al 100% en verde.
- `verify_ui_syntax.py` y `validate_docs.py` con 0 fallos.
