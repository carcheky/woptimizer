# Tareas: Optimización de Latencia y Throughput en el Escaneo de Procesos

- **Change**: `2026-09-30-scan-latency-optimization`
- **Tarea**: `TASK-033`

---

## Tareas de Implementación

- [x] **T-1: Precomputación de `_CAT_ORDER_IDX` y limpieza de sufijos**
  - En `src/woptimizer/services/process_service.py`, definir `_CAT_ORDER_IDX` a nivel de módulo a partir de `CATEGORY_ORDER`.
  - Reemplazar `.replace('.exe', '')` por `name[:-4] if name.lower().endswith('.exe') else name`.

- [x] **T-2: Implementar `get_process_exe_path` en `ProcessService`**
  - Añadir `get_process_exe_path(self, pid: int) -> str` en `ProcessService`.
  - Envolver en `try/except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, OSError, ValueError) -> ""` para garantizar degradación segura.

- [x] **T-3: Optimización del bucle `get_running_processes`**
  - Cambiar `psutil.process_iter(['pid', 'name', 'exe'])` a `psutil.process_iter(['pid', 'name'])`.
  - Pasar `exe_path=""` en el escaneo masivo.
  - Instanciar con `ProcessInfo.model_construct(...)` en lugar de constructor validado completo.
  - Utilizar `_CAT_ORDER_IDX` en la función de ordenamiento.

- [x] **T-4: Adaptación de `on_add_to_pack` en `ProcessManagerView`**
  - En `src/woptimizer/ui/views/process_manager_view.py:372`, si `procs[0].exe_path` está vacío y `procs[0].pid > 0`, llamar a `self.process_service.get_process_exe_path(procs[0].pid)`.
  - Mantener fallback a `full_name` y `name`.

- [x] **T-5: Pruebas discriminantes y benchmark en `run_tests.py`**
  - Añadir prueba `test_scan_latency_and_lazy_exe_resolution()` en `run_tests.py`:
    * Verifica que `get_running_processes()` retorne procesos válidos con nombres limpios y categorías correctas.
    * Verifica que `get_process_exe_path(pid)` devuelva la ruta real para el proceso propio de Python (`os.getpid()`).
    * Verifica que `get_process_exe_path(-999)` degrade a `""` sin lanzar excepción.
    * Verifica que el tiempo medio de escaneo se mantenga por debajo de la cota estricta de 25 ms.
  - Registrar en `__main__` de `run_tests.py`.

- [x] **T-6: Actualización de documentación técnica**
  - Documentar la optimización y la API `get_process_exe_path` en `docs/ai/architecture.md`.
  - Actualizar `docs/ai/testing-guide.md` con la nueva prueba discriminante.
