# Propuesta: Optimización de Latencia y Throughput en el Escaneo de Procesos

- **ID de Cambio**: `2026-09-30-scan-latency-optimization`
- **Área**: Área 4: Rendimiento & Latencia (Ciclo #24)
- **Tarea**: `TASK-033`
- **Módulo**: `src/woptimizer/services/process_service.py`, `src/woptimizer/ui/views/process_manager_view.py`, `docs/ai/architecture.md`
- **Estado**: DRAFT

---

## 1. Motivación y Diagnóstico

En el ciclo #7 (`TASK-018`) se introdujo la caché TTL de 2 segundos y el hashmap $O(1)$ para metadatos. Sin embargo, en cada expiración de TTL o actualización manual forzada (`force_refresh=True`), `get_running_processes()` realiza un escaneo completo del árbol de procesos del sistema operativo.

El diagnóstico medido con `time.perf_counter()` en Windows 11 sobre ~325 procesos vivos revela:
1. **Sobrecarga de `exe` en `psutil.process_iter`**:
   - `psutil.process_iter(['pid', 'name', 'exe'])`: **31.16 ms**.
   - `psutil.process_iter(['pid', 'name'])`: **3.83 ms** (**~8.1x más rápido**).
   En Windows, pedir `'exe'` para todos los procesos activos fuerza llamadas a `OpenProcess` con descriptores de consulta de seguridad sobre procesos del sistema, servicios y procesos con integridad alta, generando cientos de excepciones internas `AccessDenied` e I/O innecesario.
2. **Uso real de `exe_path`**:
   `exe_path` **únicamente** se utiliza en `process_manager_view.py:372` cuando el usuario pulsa *"Añadir al Pack"* para asociar la ruta absoluta a una app seleccionada. Durante el listado visual en portada, en el Gestor de Procesos y en la comprobación de Gaming Mode, `exe_path` no se lee.
3. **Overhead de validación Pydantic en bucle caliente**:
   Construir ~320 instancias `ProcessInfo(...)` valida 7 campos por instancia (~2.240 validaciones por escaneo). `ProcessInfo.model_construct(...)` reduce la creación de objetos a una asignación directa sin overhead.
4. **Asignación recurrente del diccionario de orden**:
   `cat_idx = {c: i for i, c in enumerate(CATEGORY_ORDER)}` se recrea en cada llamada en lugar de permanecer precalculado a nivel de módulo.

---

## 2. Solución Propuesta

1. **Escaneo Rápido de Procesos**:
   Iterar `psutil.process_iter(['pid', 'name'])`, pasando `exe_path=""` en el snapshot base de `get_running_processes()`.
2. **Resolución On-Demand de Ejecutable**:
   Implementar `ProcessService.get_process_exe_path(pid: int) -> str` con captura fail-safe de `NoSuchProcess`, `AccessDenied`, `ZombieProcess` y `OSError`.
3. **Consumo On-Demand en UI**:
   En `process_manager_view.py:on_add_to_pack`, si `procs[0].exe_path` está vacío y `pid > 0`, consultar `self.process_service.get_process_exe_path(pid)` justo en el momento de la adición. Si la ruta no se resuelve (por permisos o proceso cerrado), degradar limpiamente a `full_name` o `name`.
4. **Construcción Acelerada con `model_construct`**:
   Usar `ProcessInfo.model_construct(...)` en el bucle de `get_running_processes()`.
5. **Precomputación de Índices y Limpieza Segura de Nombre**:
   - Módulo `_CAT_ORDER_IDX = {c: i for i, c in enumerate(CATEGORY_ORDER)}`.
   - Limpieza de sufijo con `name[:-4] if name.lower().endswith('.exe') else name` en lugar de `.replace('.exe', '')`.

---

## 3. Invariantes y Compatibilidad

- **Separación de Capas**: UI sigue consumiendo exclusivamente la API de `ProcessService` (`get_process_exe_path`), sin importar `psutil`.
- **Invariante de Blindaje Anti-Brick**: `SYSTEM_PROTECTED_PROCESSES` y la barrera de seguridad G-2 se mantienen 100% intactas.
- **Compatibilidad con Tests Existentes**: `test_el_gestor_guarda_la_ruta_absoluta` pasa sin cambios porque respeta `exe_path` predefinido si existe.
- **Sin Dependencias Nuevas**: Solo Python estándar y `psutil`.
