# Proposal: Restauración Inteligente de Apps tras Modo Gaming (Cycle 28 - TASK-038)

## Contexto y Motivación
Actualmente, el Modo Gaming (`GamingService.execute_gaming_pack`) escanea y finaliza los procesos pertenecientes a categorías objetivo o apps extra indicadas por el usuario, liberando memoria RAM. Sin embargo, al finalizar la sesión de juego, el usuario debía reabrir manualmente cada una de las aplicaciones cerradas (navegadores, herramientas de trabajo, etc.).

Este ciclo amplía el Modo Gaming con un sistema de **restauración de sesión** (`restore_gaming_session`), capturando las rutas de ejecutables de los procesos terminados antes de su cierre y ofreciendo un mecanismo thread-safe de reapertura mediante un solo clic en la Portada (`DashboardView`) y en el Gestor de Packs.

## Especificación Técnica y Contrato

### 1. Capa de Servicios (`GamingService`)
- **Estado de Sesión:**
  - `self._last_closed_apps: List[str]` almacena la lista única de rutas absolutas (`exe_path`) de los procesos cerrados en la última activación del Modo Gaming.
- **Captura previa al kill en `execute_gaming_pack`:**
  - Antes de invocar `process_service.kill_processes(to_kill)`, se resuelve `p.exe_path` para cada proceso candidato usando `process_service.get_process_exe_path(p.pid)` si `p.exe_path` viene vacía.
  - Se filtran y deduplican las rutas absolutas válidas y se persisten en `self._last_closed_apps`.
- **Métodos Públicos:**
  - `get_last_closed_apps() -> List[str]`: Retorna una copia de la lista de ejecutables pendientes de restauración.
  - `clear_last_closed_apps() -> None`: Limpia el estado de la sesión almacenada.
  - `restore_gaming_session() -> Tuple[int, int]`: Invoca `process_service.start_pack_apps(self._last_closed_apps)` en segundo plano, resetea la lista y retorna `(started, failed)`.

### 2. Capa de Interfaz (`DashboardView` & `PackManagerView`)
- En `DashboardView`, tras ejecutar el Modo Gaming o si `get_last_closed_apps()` contiene elementos, se muestra una barra de acción secundaria o botón `"Restaurar Apps Cerradas (N)"`.
- Al pulsar el botón de restauración, se ejecuta `restore_gaming_session()` en un hilo secundario y la UI se actualiza thread-safe vía `self.after(0, ...)`.

### 3. Invariantes a Mantener
- **Separación de capas:** `GamingService` no llama a `psutil` ni a `subprocess` directamente; delega la validación y lanzamiento en `ProcessService.start_pack_apps` y la resolución de rutas en `ProcessService.get_process_exe_path`.
- **Blindaje de arranque:** Las rutas restauradas son validadas por `ProcessService._resolver_app` (sin shell, sin UNC, dentro de raíces permitidas y extensiones `.exe`/`.com`).
- **Thread safety:** Toda actualización de widgets desde hilos secundarios se despacha vía `self.after(0, ...)`.

## Plan de Verificación y Testing
- Prueba unitaria e integración en `run_tests.py`:
  - `test_gaming_service_session_restoration`: Verifica la captura de `_last_closed_apps`, la consulta con `get_last_closed_apps`, la limpieza con `clear_last_closed_apps` y la ejecución de `restore_gaming_session`.
- `python verify_ui_syntax.py`, `python run_tests.py` y `python validate_docs.py` en verde 100%.
- Auditoría Paso 4 con `mutation-auditor` (PASS).
