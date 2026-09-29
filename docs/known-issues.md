# Known issues y trampas críticas

> ⚠️ **LEE ESTO ANTES DE MODIFICAR** — Las trampas aquí causaron horas de debugging perdido.

## 🚨 Trampa #1: `$pid` en PowerShell es variable reservada

**Síntoma:** Todos los procesos aparecen con el MISMO PID en la lista. `taskkill /F /PID X` falla porque ese PID no existe o no es lo que esperas.

**Causa:** En PowerShell, `$pid` es una variable automática de solo lectura que contiene el PID del propio proceso PowerShell. Asignar `$pid = $_.ProcessId` falla silenciosamente.

**Fix correcto:**

```powershell
# MAL - $pid es reserved, la asignacion falla silenciosamente
ForEach-Object {
    $pid = $_.ProcessId    # ← BUG
    Write-Output "$name`t$pid`t$cmd"
}

# BIEN - usar $procId u otro nombre
ForEach-Object {
    $procId = $_.ProcessId
    Write-Output "$name`t$procId`t$cmd"
}
```

**Cómo detectar:** Si `get_running_processes()` retorna siempre el mismo PID, este es el bug.

**Test de regresión:** `python test_kill_real.py` lanza notepad y verifica que el PID listado coincide con el real.

---

## 🚨 Trampa #2: `request_admin_elevation` mata el proceso silenciosamente

**Síntoma:** Doble clic en `ProcessManager.vbs` → no aparece nada, no hay error.

**Causa:** Si `request_admin_elevation()` falla (UAC cancelado, excepción), retorna `False` y `__main__` hace `sys.exit(0)`. Nada se muestra.

**Lección:** Nunca uses auto-elevation con `sys.exit` como fallback. Si falla, muestra error o continúa sin admin.

**Fix actual:** Eliminada la auto-elevation. La elevación admin es opcional via click derecho en la UI (futuro).

**Test de regresión:** `python verify_app.py` debe pasar (proceso vivo tras 4s).

---

## Trampa #3: PowerShell `-replace` interpreta `[PIPE]` como regex char class

**Síntoma:** Texto de reemplazo raro en cmdlines que contienen `|`.

**Causa:** PowerShell `-replace` usa regex. `[PIPE]` en el reemplazo se interpreta como clase de caracteres (P, I, E).

**Fix actual:** Ya no se usa `-replace` con `[PIPE]`. Se usa TAB como delimitador y los cmdlines se limpian con `-replace "[\t\r\n]", ' '` (clases de caracteres válidas).

**Cómo evitar:** Si necesitas reemplazar texto en PowerShell, usa `[char[]]` casting o `String.Replace()` (literal, no regex).

---

## Trampa #4: `pythonw.exe` GUI subsystem + `ShellExecuteW runas` falla

**Síntoma:** Cuando `pythonw.exe` intenta auto-elevarse con `ShellExecuteW(None, "runas", ...)`, falla silenciosamente en algunos Windows.

**Fix actual:** Eliminada la auto-elevation. Si se necesita admin, lanzar manualmente con clic derecho → "Ejecutar como administrador".

---

## Trampa #5: MySQL `tkinter` no incluye checkboxes en Treeview por defecto

**Síntoma:** Querías checkboxes para selección múltiple visible, tkinter Treeview no las trae.

**Workaround usado:** Selección múltiple con Ctrl+click estándar + click toggle (sin Ctrl) implementado en `_on_click`. No hay checkboxes reales.

**Alternativa si se necesita:** Usar `ttk.Checkbutton` en una columna custom, pero requiere reimplementar el treeview.

---

## Bloqueo conocido: Mini App publish EACCES

**Síntoma:** `miniapp.publish` retorna `RUNTIME_START_FAILED` con `Error: listen EACCES: permission denied 127.0.0.1:60784`.

**Causa:** El sandbox del proceso Node del Host MiniMax Code bloquea TCP binds al puerto 60784 específicamente. Probado con 6 estrategias diferentes, todas fallan.

**Estado:** `miniapps/process_manager/` queda como referencia. El código está completo y compila. No se puede publicar en este entorno.

**Workarounds intentados (todos fallan):**

| Estrategia | Resultado |
|------------|-----------|
| `listen(60784, '127.0.0.1')` | EACCES |
| `listen(60784, '0.0.0.0')` | EACCES |
| `listen(60784, '::1')` | EACCES |
| `listen(60784, '::')` | EACCES |
| `listen(0, host)` (OS-assigned) | OK pero Host busca en 60784 → timeout |
| `netsh interface portproxy` 60784 → real | Regla añadida pero no enruta (ECONNREFUSED) |

**Acciones del usuario si quiere arreglar:**
- Reportar bug al soporte de MiniMax Code
- Esperar actualización del Host
- Empaquetar como Electron/Tauri standalone (no Mini App)

---

## Trampa #6: Encoding cp1252 en consola de Windows

**Síntoma:** `UnicodeEncodeError: 'charmap' codec can't encode character '\u2705'` al hacer `print` con emojis o caracteres especiales.

**Causa:** La consola Windows usa cp1252 por defecto, no UTF-8.

**Fix en scripts de validación:**

```python
import sys
sys.stdout.reconfigure(encoding='utf-8')  # o
print(text.encode('ascii', 'replace').decode())  # evita emojis
```

**En PowerShell:** Setear `$OutputEncoding = [System.Text.Encoding]::UTF8` antes de operaciones que produzcan caracteres no-ASCII.

---

## Trampa #7: Subprocess sin `CREATE_NO_WINDOW` abre consolas visibles

**Síntoma:** Al matar/relaunchar procesos aparecen ventanas de consola parpadeando brevemente.

**Causa:** `subprocess.run()` o `Popen()` en Windows por defecto abre una consola para procesos hijos.

**Fix:** Siempre pasar `creationflags=CREATE_NO_WINDOW` (0x08000000) en `subprocess.run()` y `subprocess.Popen()`.

**Aplicado en:** `get_running_processes()`, `kill_processes()`, `relaunch_processes()`.

---

## Trampa #8: Threading en tkinter requiere `root.after(0, callback)`

**Síntoma:** "RuntimeError: main thread is not in main loop" al actualizar widgets desde un thread.

**Causa:** tkinter no es thread-safe. Solo el hilo principal puede tocar widgets.

**Fix usado:**

```python
def worker():
    result = some_io_call()
    self.root.after(0, self._on_result, result)  # ← clave

threading.Thread(target=worker, daemon=True).start()
```

`daemon=True` permite que el thread muera si la app se cierra.

---

## Trampa #9: Shell restrictions del agente (EPERM)

**Síntoma:** El agente tiene `spawn EPERM` al ejecutar comandos bash/python.

**Causa:** El entorno donde corre el agente tiene restricciones de spawn. Algunos shells están bloqueados.

**Workaround:** Escribir scripts `.py` o `.ps1` que el usuario ejecuta con doble clic. El agente no puede ejecutar directamente.

---

## 🚨 Trampa #10: `proc.kill()` deja procesos hijo huérfanos en Windows

**Síntoma:** Tras `python verify_app.py` (o cualquier test que mata un Python que lanzó `subprocess.run(["powershell", ...])`), queda un `pwsh.exe` o `powershell.exe` vivo en tu sesión. Si abres el Task Manager lo verás consumiendo recursos sin razón aparente.

**Causa:** `proc.kill()` en Windows llama a `TerminateProcess`, que mata SOLO el PID indicado. Los hijos (cualquier `subprocess.run` o `Popen` lanzado por el proceso padre) se quedan huérfanos porque Windows no propaga automáticamente la terminación. Esto difiere de Unix donde señales al líder del grupo a veces cierran hijos.

**MAL — deja huérfanos:**

```python
proc.kill()  # solo mata el Python padre
```

**BIEN — mata el árbol completo:**

```python
import subprocess
CREATE_NO_WINDOW = 0x08000000

def kill_process_tree(pid):
    subprocess.run(
        ["taskkill", "/F", "/T", "/PID", str(pid)],
        capture_output=True,
        creationflags=CREATE_NO_WINDOW,
    )

kill_process_tree(proc.pid)  # /T = tree, mata tambien los hijos
```

**Aplicado en:** `verify_app.py` y `verify_pyw.py` (función `kill_process_tree`).

**Aplicación futura:** Si en algún momento `process_manager.py` lanza procesos `Popen` no-bloqueantes (PowerShell para queries periódicas, watchers de procesos, etc.), el cleanup al cerrar la app debe usar `taskkill /F /T` también. Hoy es seguro porque todos los subprocess son `run()` bloqueantes que mueren al retornar, pero el patrón sigue aplicando.

**Test de regresión:** Tras `python verify_app.py`, el conteo de procesos `pwsh`/`powershell` debe ser IGUAL al de antes del test (no uno más).

---

## Trampa #11: Cambiar return signature de `kill_processes` / `relaunch_processes` rompe todos los call sites

**Síntoma:** Tras modificar `kill_processes` o `relaunch_processes` para devolver una tupla más larga (por ejemplo de 2 a 3 elementos), los call sites que hacen `a, b = func(...)` fallan con `ValueError: too many values to unpack (expected 2)`.

**Causa:** Las dos funciones son API pública del módulo. Cualquier script que las usa (incluidos `test_kill_real.py`, `test_harness.py`, `test_harness_v2.py` y los métodos internos de `class ProcessManagerApp`) tiene que actualizarse al unísono.

**Signaturas actuales (v1.2.0):**

```python
def kill_processes(processes_seleccionados, kill_tree=True, dedupe_by_tree=True):
    """Returns: (killed: list, failed: list, skipped: list)"""

def relaunch_processes(processes, group_by_exe=True):
    """Returns: (launched: list, failed: list, skipped_count: int)"""
```

**Regla:** Cuando modifiques el return de una función pública del módulo, **busca TODOS los call sites antes de cambiar**:

```bash
grep -rn "(kill|relaunch)_processes(" --include="*.py"
```

Y actualiza cada `a, b = ...` a `a, b, c = ...` (o usa `_` para los que no te importen).

**Aplicado en:** `process_manager.py` (4 métodos), `test_kill_real.py`, `test_harness.py`, `test_harness_v2.py`.

---

## Trampa #12: Tests que usan apps GUI (notepad, calc, etc.) molestan al usuario

**Síntoma:** Cada vez que se ejecuta `test_kill_real.py`, aparece una ventana de Bloc de notas durante ~3 segundos en el escritorio del usuario. Aunque el test la mata al final, es visualmente molesto y en algunos casos (WMI snapshot desactualizado, race condition) la ventana puede quedarse viva sin que el test lo detecte.

**Causa:** El test original usaba `notepad.exe` como "proceso de prueba" para validar `kill_processes()`. Cualquier GUI app abre su ventana cuando se lanza. `CREATE_NO_WINDOW` (0x08000000) en `subprocess.Popen` solo suprime la **consola** del hijo, no la ventana de una GUI app — para notepad eso es irrelevante porque no tiene consola pero **sí** tiene ventana.

**Fix:** Usar un subprocess Python invisible como objetivo del test:

```python
marker = f"wopt_test_{os.getpid()}"
target = subprocess.Popen(
    [sys.executable, "-c", f"import time; print('{marker}'); time.sleep(60)"],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    creationflags=CREATE_NO_WINDOW,  # sin consola
)
# ...
target_in_list = [p for p in processes if marker in p.get('commandline', '')]
```

**Por qué funciona:**
- `python -c "..."` es un proceso de consola → `CREATE_NO_WINDOW` sí lo esconde
- `time.sleep(60)` mantiene el proceso vivo sin hacer nada (no UI, no output)
- Marker único en el commandline permite identificarlo en el WMI list (más robusto que matchear PID, que puede no aparecer en el snapshot)
- `stdout=subprocess.PIPE` evita que `print()` muestre nada

**Aplicado en:** `test_kill_real.py` (reescrito 2026-09-14). Antes usaba `notepad.exe`.

**Regla:** Para tests que necesitan matar procesos reales, **preferir siempre subprocess headless** (Python, Node, pwsh). Solo usar GUI apps si el test está validando específicamente comportamiento de GUI (no es nuestro caso).

---

## Trampa #13: `taskkill /T` solo mata descendientes, NO siblings

**Síntoma:** El usuario selecciona 5 firefox.exe separados (cada uno su propia ventana) y hace click en "Matar". Solo muere 1. Los otros 4 sobreviven aunque todos tengan el mismo `args[0]` (mismo exe path).

**Causa:** `taskkill /F /T /PID X` mata el proceso X **y todo su árbol descendiente**. Pero "descendiente" significa "hijo, nieto, etc." — NO significa "otros procesos con el mismo nombre". Si tienes 5 firefox.exe que son hermanos (todos hijos de `explorer.exe` pero independientes entre sí), `/T` de uno solo mata ese y sus renderers; los otros 4 sobreviven.

**Fix en woptimizer (v1.3.0):** `kill_selected` ahora:
1. Expande la selección a **TODOS los procesos del mismo nombre** del snapshot (helper `expand_selection_by_name`)
2. Pasa `dedupe_by_tree=False` a `kill_processes` (porque dedup agruparía los 5 firefox en 1 taskkill, dejando 4 vivos)

Resultado: 5 firefox → 5 taskkill calls → 5 firefox + todos sus renderers mueren.

```python
# En kill_selected:
expanded = expand_selection_by_name(selected, self.processes)
killed, failed, skipped = kill_processes(
    expanded, kill_tree=True, dedupe_by_tree=False  # ← False es CLAVE
)
```

**Diferencia con `prepare_for_gaming`:** ahí SÍ queremos dedup, porque al matar "todos los high/medium", el browser main + sus renderers son un solo árbol → 1 taskkill los maneja. La expansión por nombre solo aplica a `kill_selected` (selección manual del usuario).

**Test de regresión:** `python test_kill_expansion.py` valida la lógica del helper y la integración.

## Trampa #14: la reescritura v3 perdio la doble pulsacion (y con ella, la seguridad)

**Síntoma:** Un clic de más y se cierran 40 pestañas del navegador. En la v3 las 5 acciones destructivas (`on_kill_selected`, `kill_pack`, `delete_pack`, `remove_app_from_pack` y `execute_pack` en rama `kill`) ejecutan **a pelo**, sin pedir nada.

**Causa:** Regresión silenciosa de la reescritura v2 -> v3, no una decisión de diseño. El patrón existía en `process_manager.py` v2.0.2 con los helpers `_request_confirm` / `_reset_pending_action`, y se había instaurado tras un incidente concreto: un `messagebox.askyesno` se abría **por detrás** de la ventana principal, el usuario pulsaba "Cerrar", no veía nada y reportó "se ha roto, no mata procesos". Conclusión registrada: **nunca `messagebox` en la ventana principal**; la seguridad se consigue exigiendo una segunda pulsación, no con un diálogo. Al reescribir la UI se copiaron los botones y no el patrón, y como la v2 ya no está en el repo, nadie lo notó.

**Cómo se comprueba que sigue ahí** (si algún día vuelve a dar cero, se ha perdido otra vez):

```
messagebox | askyesno | showinfo | showwarning | _request_confirm | "OTRA VEZ" | confirm
```

Debe seguir dando cero en `src/`. Si aparece un `messagebox`, es que alguien ha resuelto el problema por la puerta prohibida.

**Fix en woptimizer (v3.1, TASK-023):** toda la lógica vive **una sola vez** en `src/woptimizer/ui/confirmation.py`, en dos capas:
1. `DoubleTapGuard` — máquina de estados ** pura, sin `customtkinter` ni `tkinter`, con un `scheduler` inyectable. Es la que se testea headless en `run_tests.py::test_double_tap_guard`.
2. `Confirmable` — mixin fino que solo configura widgets (estado ámbar del botón) y escribe en el `status_label`.

Las tres vistas la usan y sobrescriben `destroy()` para matar el `after` vivo.

**Reglas que no se pueden romper:**
- **Congelar la INTENCIÓN, recalcular los DATOS.** En `on_kill_selected` el token es el conjunto de claves marcadas; los `ProcessInfo` se recalculan en la segunda pulsación. Congelar la lista sería un fallo de seguridad: entre pulsaciones el **PID se recicla** y matarías a un inocente.
- **Programar con `self.after(...)`, nunca con `self.master.after(...)`.** `master` es `content_frame`, que sobrevive al cambio de pestaña, y toda navegación destruye la vista y crea una instancia nueva: el callback huérfano reconfigura widgets ya destruidos.
- **Nada se traga en silencio.** `delete_pack` devolvía `False` cuando el pack no existía y la vista ignoraba el retorno; ahora los tres estados (armado, error, éxito) salen por el `status_label` inline.
- La portada **solo** confirma en la rama `default_action == "kill"`, con ventana de 2000 ms; arrancar apps no pide nada.

**Trampa dentro de la trampa:** `PackManagerView` no tenía ningún `status_label` (solo header y `scroll_frame`). Sin él, el requisito de "feedback inline" es literalmente inimplementable. Si añades una vista nueva y quieres usar el patrón, primero créale el label.

## Resumen de reglas para IA que modifique este proyecto

1. **NUNCA uses `$pid` en scripts PowerShell** — usa `$procId` u otro nombre
2. **NUNCA añadas auto-elevation con `sys.exit` silencioso** — debe mostrar error o continuar
3. **SIEMPRE aplica `CREATE_NO_WINDOW`** en todos los subprocess
4. **SIEMPRE valida con `verify_app.py` y `test_kill_real.py`** tras cambios
5. **NUNCA asumas que funciona** — verifica con `poll()` que el proceso sigue vivo
6. **USA `root.after(0, callback)`** para actualizar widgets desde threads
7. **USA TAB como delimitador** entre Python y PowerShell
8. **NO añadas features sin test** — un cambio a la vez, validando cada uno
