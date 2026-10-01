# Propuesta: Resiliencia de Concurrencia y Recuperación en GamingService (Ciclo #37)

## Motivación
En el Ciclo #28 (`TASK-038`) y Ciclo #33 (`TASK-043`), se implementó la restauración de sesiones gaming tanto desde el dashboard como desde el System Tray vía subprocesos asíncronos (`threading.Thread(target=..., daemon=True)`).
Sin embargo, el contenedor de ejecutables cerrados `_last_closed_apps` en `GamingService`:
1. **Condición de carrera multihilo:** `restore_gaming_session()` realiza una lectura `apps_to_restore = list(self._last_closed_apps)` seguida de una asignación `self._last_closed_apps = []` sin ningún mecanismo de sincronización. Si el usuario pulsa repetidamente el item del tray o se dispara simultáneamente desde la portada y el menú contextual, ambos hilos pueden obtener la lista antes de que se limpie, ejecutando `start_pack_apps` en paralelo y provocando el doble arranque de aplicaciones.
2. **Pérdida de estado ante fallos:** Si `ProcessService.start_pack_apps` sufre una excepción no controlada o fallo imprevisto, la lista `_last_closed_apps` ya ha sido vaciada irreversiblemente, impidiendo cualquier reintento por parte del usuario.
3. **Captura defensiva en `start_pack_apps`:** Aunque `start_pack_apps` captura `OSError`, cualquier otra excepción durante la resolución o el arranque abortaría el bucle completo, dejando de intentar las apps restantes del lote.

## Especificación Técnica
1. **`GamingService` Thread-Safety (`threading.RLock`):**
   - Incorporar `self._lock = threading.RLock()` en el constructor de `GamingService`.
   - Proteger con el cerrojo:
     - `get_last_closed_apps()`
     - `clear_last_closed_apps()`
     - Asignación de `self._last_closed_apps` en `execute_gaming_pack()`
     - `restore_gaming_session()`: extracción atómica de las aplicaciones a restaurar bajo el lock.
2. **Recuperación defensiva ante excepciones:**
   - En `restore_gaming_session()`, si `start_pack_apps` lanza una excepción imprevista, restaurar atómicamente bajo el lock las aplicaciones no lanzadas de nuevo en `_last_closed_apps` para permitir su recuperación.
3. **Captura defensiva amplia en `start_pack_apps`:**
   - En `ProcessService.start_pack_apps()`, capturar `(OSError, Exception)` por cada aplicación para aislar fallos individuales sin tumbar el procesamiento de la lista completa.
4. **Verificación & Tests en `run_tests.py`:**
   - Incorporar `test_gaming_service_rlock_and_concurrency` que valide:
     - Presencia y tipo de `RLock` reentrante.
     - Concurrencia entre 5 hilos simultáneos llamando a `restore_gaming_session()`, asegurando que `start_pack_apps` solo se ejecuta una única vez para la tanda y los demás reciben `(0, 0)`.
     - Preservación defensiva de `_last_closed_apps` cuando `start_pack_apps` eleva una excepción simulada.
