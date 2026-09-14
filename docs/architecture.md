# Architecture

## Flujo de datos

```
[Usuario] --doble clic--> [ProcessManager.vbs] --Run--> [pythonw.exe]
                                                       |
                                                       v
                                            [process_manager.pyw]
                                            |
                                            |-- tk.Tk() --crea--> [GUI tkinter]
                                            |
                                            |-- self.load_processes()
                                            |     |
                                            |     v
                                            |   [threading.Thread]
                                            |     |
                                            |     v
                                            |   subprocess.run([powershell, ...])
                                            |     |
                                            |     v
                                            |   [PowerShell con Get-CimInstance]
                                            |     |
                                            |     v
                                            |   stdout (TAB-separated)
                                            |     |
                                            |     v
                                            |   root.after(0, _on_processes_loaded)
                                            |     |
                                            |     v
                                            |   [populate_tree() con categorías]
                                            |
                                            |-- self.kill_selected()
                                            |     |
                                            |     v
                                            |   [kill_processes()]
                                            |     |
                                            |     v
                                            |   subprocess.run([taskkill, /F, /PID, ...])
                                            |
                                            |-- self.relaunch_saved()
                                                  |
                                                  v
                                                [relaunch_processes()]
                                                  |
                                                  v
                                                subprocess.Popen([...], detached=True)
```

## Componentes principales

### `process_manager.py` (1086 líneas)

Estructura interna:

```
Líneas 1-110    imports + constantes + categorías gaming
Líneas 110-200  funciones helper (categorize_process, get_running_processes, kill_processes, etc.)
Líneas 200-350  funciones de persistencia (save/load/clear saved_processes.json)
Líneas 350-870  class ProcessManagerApp (tkinter UI)
Líneas 870-1100 main(), __main__
```

**Funciones críticas (no renombrar sin actualizar todos los call sites):**

- `get_running_processes()` — usa PowerShell Get-CimInstance, retorna lista de dicts
- `kill_processes(procs, kill_tree=True)` — itera y llama taskkill, retorna (killed, failed)
- `categorize_process(name)` — matchea nombre contra PROCESS_CATEGORIES
- `save_processes_to_relaunch()` / `load_saved_processes()` — JSON persistence

### Categorías gaming

Diccionario `PROCESS_CATEGORIES` con esta estructura:

```python
{
    '🔴 Navegadores': {
        'priority': 'high',     # 'high' | 'medium' | 'low' | 'none'
        'patterns': ['chrome', 'firefox', 'msedge', ...],
        'description': 'Navegadores web',
    },
    ...
}
```

`categorize_process(name)` itera sobre las categorías en orden y matchea si `pattern in name.lower()`. El orden de las categorías en `CATEGORY_ORDER` define el orden de visualización.

### Modos Simple / Completo

- **Simple** muestra solo: 🔴 Navegadores, 🔴 Sincronización, 🟡 Chat, 🟡 Productividad, 🟡 Media
- **Completo** muestra todas + 🟢 Overlays, 🟢 Launchers, ⚫ Antivirus, ⚫ Sistema, ⚪ Otros
- Constante `SIMPLE_CATEGORIES` lista las categorías gaming
- Variable de instancia `self.simple_mode_var` (BooleanVar) controla el toggle

### Async loading

`load_processes()` lanza un thread daemon para no bloquear UI:

```python
def load_processes(self):
    self._loading = True  # evita cargas concurrentes
    
    def worker():
        processes = get_running_processes()
        self.root.after(0, self._on_processes_loaded, processes)
    
    threading.Thread(target=worker, daemon=True).start()
```

`root.after(0, callback)` programa la actualización UI en el hilo principal (tkinter no es thread-safe).

### Persistencia

Archivo `saved_processes.json` (mismo dir que el script):

```json
[
  {
    "name": "chrome",
    "pid": "1234",
    "commandline": "C:\\...\\chrome.exe --type=renderer",
    "killed_at": "2026-09-13T22:00:00",
    "already_gone": false
  }
]
```

`save_processes_to_relaunch()` deduplica por `(name, pid)`.

### Subprocess flags

`CREATE_NO_WINDOW = 0x08000000` se aplica a:
- `subprocess.run()` para PowerShell
- `subprocess.run()` para taskkill
- `subprocess.Popen()` para relaunch

Sin este flag, los procesos hijos abren ventanas de consola visibles.

## Decisiones de diseño

1. **Categorías en código, no en JSON** — Permite iterar con priorities en runtime y validar al inicio.
2. **TAB como delimitador PowerShell → Python** — TAB nunca aparece en cmdlines normales, evita colisiones.
3. **Exit 128 = success** — `taskkill /F /PID X` retorna 128 si X ya no existe (objetivo cumplido). Tratarlo como éxito evita falsos "fallidos".
4. **Dedup por (name, pid)** — Múltiples instancias del mismo proceso (5 chrome.exe) son todas guardables.
5. **Thread daemon** — Si la app se cierra mientras carga PowerShell, el thread muere sin error.

## Lo que NO es

- **No es** un task manager tipo Process Explorer — solo lista y mata, no muestra detalles profundos
- **No es** un monitor en tiempo real — refresh manual (F5) o auto-refresh opcional
- **No es** portable — usa APIs Windows específicas (taskkill, Get-CimInstance)
