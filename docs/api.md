# API Reference

Funciones principales que un agente IA podría necesitar llamar o extender.

## Funciones de `process_manager.py` (módulo)

### `get_running_processes() -> list[dict]`

Retorna lista de procesos en ejecución.

**Returns:** Lista de dicts con esta estructura:

```python
{
    'name': 'chrome',           # nombre sin extensión
    'full_name': 'chrome.exe',  # nombre con extensión
    'pid': '1234',              # string (de PowerShell)
    'commandline': 'C:\\...\\chrome.exe --type=renderer'
}
```

**Side effects:** Muestra messagebox de error si PowerShell falla.

**Performance:** 1-3 segundos (PowerShell Get-CimInstance).

### `kill_processes(processes_seleccionados, kill_tree=True) -> tuple[list, list]`

Mata procesos via `taskkill /F`.

**Args:**
- `processes_seleccionados`: list of dicts (mismo formato que `get_running_processes`)
- `kill_tree`: si True, añade `/T` para matar hijos también

**Returns:** `(killed, failed)`:
- `killed`: list of dicts con `{name, pid, commandline, killed_at, already_gone}`
- `failed`: list of strings con mensaje de error por proceso

**Exit codes de taskkill:**
- 0 = success
- 128 = proceso ya no existe (tratado como success)
- 1 = acceso denegado u otro error

### `categorize_process(proc_name) -> str`

Matchea nombre contra `PROCESS_CATEGORIES`, retorna nombre de categoría o `'⚪ Otros'`.

**Args:** `proc_name` (str) — nombre del proceso (sin .exe o con .exe)

**Returns:** String con el nombre de categoría.

### `save_processes_to_relaunch(processes) -> bool`

Añade procesos al JSON con dedup por `(name, pid)`.

**Args:** `processes`: list of dicts con al menos `name`, `pid`, `commandline`

**Returns:** True si escribió OK.

### `load_saved_processes() -> list`

Lee `saved_processes.json`, retorna lista (vacía si no existe o corrupto).

### `clear_saved_processes() -> bool`

Borra el archivo JSON.

### `relaunch_processes(processes) -> tuple[list, list]**

Relanza procesos via `subprocess.Popen` con `shlex.split` o fallback shell.

**Returns:** `(launched, failed)`

### `is_admin() -> bool`

Detecta si el proceso actual corre con permisos admin via `ctypes`.

## Constantes

### `PROCESS_CATEGORIES` (dict)

```python
{
    '🔴 Navegadores': {
        'priority': 'high',     # 'high' | 'medium' | 'low' | 'none'
        'patterns': ['chrome', 'firefox', ...],
        'description': '...',
    },
    ...
}
```

### `CATEGORY_ORDER` (list)

Orden de visualización de categorías en el treeview.

### `SIMPLE_CATEGORIES` (list)

Categorías que se muestran en modo Simple (gamer-friendly).

### `PROCESS_LIST_FILE` (str)

Path absoluto a `saved_processes.json` (mismo dir que el script).

### `MAX_CMDLINE_LEN` (int)

4000 — commandlines más largos se truncan.

### `CREATE_NO_WINDOW` (int)

0x08000000 — flag de Windows para subprocess sin ventana de consola.

## Clase `ProcessManagerApp`

Métodos principales (sin self):

| Método | Propósito |
|--------|-----------|
| `__init__(root)` | Configura ventana, llama `create_widgets` y `load_processes` |
| `create_widgets()` | Construye toda la UI (botones, treeview, etc.) |
| `load_processes()` | Async, lanza thread que llama `get_running_processes` |
| `_on_processes_loaded(processes)` | Callback UI: actualiza treeview |
| `populate_tree()` | Llena treeview con categorías |
| `filter_processes()` / `_schedule_filter()` / `_do_filter()` | Búsqueda con debounce |
| `toggle_select_all()` | Selecciona/deselecciona todas las hojas |
| `kill_selected()` | Mata procesos seleccionados (con confirmación) |
| `save_selected()` | Guarda seleccionados para relaunch |
| `relaunch_saved()` | Relanza procesos guardados |
| `prepare_for_gaming()` | Mata high+medium priority (botón Gaming) |
| `clear_saved()` | Limpia lista guardada |
| `update_count()` | Actualiza contador en status bar |
| `_on_click(event)` | Handler click izquierdo (toggle) |
| `_on_double_click(event)` | Handler doble click (expand/collapse categoría) |
| `_show_context_menu(event)` | Muestra menú click derecho |
| `_ctx_kill()`, `_ctx_save()`, `_ctx_copy_pids()`, `_ctx_copy_cmdlines()` | Acciones del menú |

## Atajos de teclado

| Atajo | Acción |
|-------|--------|
| `Ctrl+A` | Seleccionar todas las hojas |
| `Delete` | Matar seleccionados |
| `F5` / `Ctrl+R` | Refrescar lista |
| `Escape` | Limpiar búsqueda |

## Subprocess calls (resumen)

| Operación | Comando | Flags |
|-----------|---------|-------|
| Listar procesos | `powershell -NoProfile -NonInteractive -Command <script>` | `CREATE_NO_WINDOW` |
| Matar proceso | `taskkill /F [/T] /PID X` | `CREATE_NO_WINDOW` |
| Relanzar proceso | `subprocess.Popen(args, detached=True, windowsHide=True)` | (windowsHide) |

## Estados de la app

- `self.processes`: list of dicts (procesos actuales)
- `self.saved_processes`: list of dicts (cargado de JSON al inicio)
- `self.simple_mode_var`: BooleanVar — toggle Simple/Completo
- `self.kill_tree_var`: BooleanVar — checkbox `/T`
- `self._loading`: bool — evita cargas concurrentes
