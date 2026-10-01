# Referencia de API (v3)

Referencia arquitectónica y de servicios del core de `woptimizer` (v3).

La versión 3 de `woptimizer` desacopla completamente la interfaz de usuario de las llamadas a sistema operativo mediante la capa de servicios (`src/woptimizer/services/`), tipado estricto con Pydantic v2 (`models.py`) e invocaciones nativas con `psutil`.

---

## 1. Servicios del Backend (`src/woptimizer/services/`)

### `ProcessService` (`process_service.py`)

Servicio central para inspección, categorización, arranque seguro y cierre de procesos.

#### Métodos Principales
- **`get_running_processes() -> List[ProcessInfo]`**
  - Escanea los procesos activos del sistema utilizando `psutil.process_iter(['pid', 'name', 'memory_info'])`.
  - Optimizado para baja latencia (<5 ms en frío, <0.01 ms en lecturas cacheadas con TTL de 2s).
  - Resolución perezosa (*lazy*) de rutas de ejecutables con `get_process_exe_path(pid)`.
- **`kill_processes(pids: List[int]) -> Tuple[int, int, int, float]`**
  - Cierra una lista de PIDs mediante `psutil`.
  - **Kill Recursivo:** Elimina siempre primero los procesos hijos (`parent.children(recursive=True)`) antes de terminar al padre.
  - **Blindaje Anti-Brick:** Filtra y protege de forma indestructible los 34 procesos esenciales del sistema definidos en `SYSTEM_PROTECTED_PROCESSES`.
  - **Retorno:** Tupla `(killed, failed, skipped, freed_mb)`.
- **`kill_pack_apps(apps: List[str]) -> Tuple[int, int, int, float]`**
  - Identifica los procesos activos coincidentes con la lista de nombres o rutas absolutas de `apps` y los cierra de forma segura.
- **`start_pack_apps(apps: List[str]) -> Tuple[int, int]`**
  - Inicia las aplicaciones declaradas en el pack.
  - **Sin `shell=True`:** Toda ruta es normalizada y contenida con `_resolver_app()`. Rechaza traversals, rutas relativas vulnerables a CWD, y junctions no autorizados.
  - **Verificación PE:** Valida la cabecera binaria `MZ` / `PE` (`_es_imagen_pe`), rechazando scripts camuflados como `.exe`.
  - **Retorno:** Tupla `(started, failed)`.
- **`load_db_async(callback=None, on_error=None)`**
  - Descarga asíncrona no bloqueante de la base de datos de procesos desde `DB_REMOTE_URL` (GitHub).
  - Reporta fallos de conectividad u HTTP de forma observable al callback `on_error(err_msg)`.
  - Mantiene fallback local síncrono indestructible (`assets/process_db.json`) preservando la operatividad offline.
- **`invalidate_cache()`**
  - Invalida de forma atómica la caché de procesos activos y metadatos de categorización.

---

### `PackService` (`pack_service.py`)

Gestor de persistencia, CRUD de packs y perfiles de usuario.

#### Métodos Principales
- **`get_all_packs() -> Dict[str, Pack]`**
  - Retorna diccionario de packs activos indexados por ID.
- **`create_user_pack(pack_id: str, name: str, apps: List[str], default_action: str = "kill") -> bool`**
  - Crea un nuevo pack de usuario y persiste a disco.
- **`update_pack(pack: Pack) -> bool`**
  - Actualiza la configuración de un pack existente.
- **`delete_pack(pack_id: str) -> bool`**
  - Elimina un pack propio de usuario. Lanza `ValueError` si se intenta eliminar el pack Gaming (`is_gaming=True`).
- **`set_favorite(pack_id: str, value: bool) -> None`**
  - Modifica el estado de favorito de un pack de forma acumulativa (multi-favoritos).
- **`toggle_favorite(pack_id: str) -> bool`**
  - Lee el estado vivo en memoria, invierte `is_favorite`, persiste atómicamente y retorna el nuevo booleano.
- **`get_favorite_packs() -> List[Pack]`**
  - Retorna la lista de packs marcados como favoritos.
- **`reset_gaming_pack() -> bool`**
  - Restablece el pack Gaming a sus valores predeterminados de fábrica usando una copia profunda (`model_copy(deep=True)`).
- **`save()` / `load()`**
  - Persistencia segura en `profiles.json` con volcado atómico (`.tmp`), rotación preventiva a copia de respaldo (`profiles.json.bak`) y tolerancia a campos extra.

---

### `GamingService` (`gaming_service.py`)

Coordinador de sesiones de juego y telemetría de optimización.

#### Métodos Principales
- **`execute_gaming_pack(pack: Pack) -> Tuple[int, int, int, float]`**
  - Única puerta autorizada para la ejecución de Gaming Mode.
  - Aplica barreras estrictas de seguridad: exclusión de procesos en `keepers`, evaluación por categoría y bloqueo de procesos de sistema.
  - Guarda en memoria (`_last_closed_apps`) los ejecutables cerrados para su posterior reapertura.
- **`restore_gaming_session() -> Tuple[int, int]`**
  - Sincronizado concurrentemente mediante `threading.RLock()`.
  - Reabre las aplicaciones cerradas durante la sesión de juego y vacía el historial de forma atómica.
- **`should_kill_for_gaming(process_name: str, gaming_pack: Pack) -> bool`**
  - Evalúa si un proceso debe cerrarse según la política de exclusión de keepers, apps explícitas y categorías objetivo.
- **`get_last_closed_apps() -> List[str]`**
  - Retorna una copia defensiva de los ejecutables pendientes de reapertura.

---

### `NotificationService` (`notification_service.py`)

Notificaciones de sistema en segundo plano integradas con la bandeja de Windows (`pystray`).

#### Métodos Principales
- **`attach_tray(icon: Any)`** / **`detach_tray()`**
  - Vincula o desvincula la referencia al icono de bandeja del sistema (`pystray.Icon`).
- **`notify(title: str, message: str) -> bool`**
  - Emite una notificación nativa. Degrada de forma segura a logging si no hay bandeja disponible o el backend del SO no soporta toasts.
- **`notify_pack_activated(pack_name: str, killed: int, freed_mb: float)`**
- **`notify_apps_launched(pack_name: str, launched: int, failed: int)`**
- **`notify_kill_result(killed: int, failed: int, freed_mb: float)`**

---

## 2. Modelos de Datos Pydantic (`src/woptimizer/models.py`)

- **`ProcessInfo`:**
  - `pid: int`
  - `name: str`
  - `full_name: str`
  - `exe_path: str`
  - `memory_mb: float`
  - `category: str`
  - `status: str`
  - `is_system_protected: bool`
- **`Pack`:**
  - `id: str`
  - `name: str`
  - `apps: List[str]`
  - `target_categories: List[str]`
  - `keepers: List[str]`
  - `is_gaming: bool`
  - `is_favorite: bool`
  - `default_action: Literal["kill", "start"]`
- **`AppData`:**
  - `packs: Dict[str, Pack]`
  - Soporta persistencia de campos adicionales mediante `model_config = ConfigDict(extra="allow")`.

---

## 3. Resumen de Ejecución y Sistema Operativo

| Operación | Mecanismo v3 | Garantías de Seguridad |
|---|---|---|
| **Listar procesos** | `psutil.process_iter` | Cero subprocesos; lectura directa de memoria del SO en C. |
| **Cierre de procesos** | `psutil.Process.kill()` | Kill recursivo (árbol de hijos); filtrado indestructible de `SYSTEM_PROTECTED_PROCESSES`. |
| **Arranque de apps** | `os.startfile` / `subprocess.Popen(shell=False)` | Sin intérprete de comandos (`shell=False`); validación de contención y verificación de cabecera PE. |
| **Actualización DB** | `urllib.request.urlopen` (asíncrono) | Timeout de 5s, notificación observable a `on_error` y fallback local empaquetado. |
