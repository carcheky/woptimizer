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

## 🚨 Trampa #15: un changelog en una carpeta oculta es un changelog que no existe

**Síntoma (ciclo #15):** el owner dice "no veo el changelog". El registro llevaba 15 ciclos
escrito, completo y con formato impecable — en `.taskmaster/CHANGELOG.md`. `.taskmaster/` es una
**carpeta oculta**: no aparece en el explorador de ficheros, ni en la vista por defecto de un IDE,
ni en un `ls` sin `-a`.

**Causa:** el motor escribía su registro donde le resultaba cómodo a la máquina (junto a
`rd_journal.json` y `tasks.json`, que también consumen `tm.py`), sin问一下se quién lo lee.
El agente que lo escribía lo encontraba siempre. El humano, nunca.

**Por qué no lo detectó nadie en 15 ciclos:** la skill decía "es MANDATORY escribir el changelog",
y el validador comprobaba que **existiera**. La regla estaba satisfecha y el objetivo no. Un
`validate_docs.py` que verifica *que el fichero esté* no verifica *que el usuario lo pueda leer*.

**Fix aplicado:**
1. **Doble escritura obligatoria**: `CHANGELOG.md` en la raíz (para el dueño, en lenguaje de
   usuario, con tabla resumen) + `.taskmaster/CHANGELOG.md` (para el pipeline, con decisiones
   técnicas y modelos por paso). La skill lo exige explícitamente y avisa de saltarse el primero.
2. `validate_docs.py` comprueba que el de raíz exista, use secciones legibles (`### Corregido`) y
   tenga entrada propia para el último ciclo.

**Trampa dentro de la trampa — el ancla se auto-referencia y se deja engañar.** La primera versión
de esa comprobación derivaba el ciclo exigido **del propio registro técnico** y buscaba el número
como *substring*. Daba falso verde por partida doble:
- Al borrar la entrada, `"015"` seguía apareciendo dentro de `TASK-015` en otra entrada → verde.
- Al borrarla en **los dos** changelogs, el requisito desaparecía → verde.

Un validador que se deduce a sí mismo no puede detectar que le han mentido. El ancla tiene que
venir de un artefacto **independiente** que se escriba **antes**: aquí, `rd_journal.json`.
Límite conocido y documentado: si el journal falta o está corrupto, el ancla no se comprueba.

**Corolario general:** un guard automático que valida *la existencia de un artefacto* no valida
*que el artefacto cumpla su propósito*. Pregunta siempre "¿quién lee esto y puede encontrarlo?",
y ancla las comprobaciones de consistencia en una fuente que no puedas editar a la vez que lo que
verificas.

## Trampa #16: `sorted()` NO ordena "alfabéticamente" cuando la cadena empieza por un emoji

**Medido en TASK-027 / FIX-004**, sobre la lista real de categorías:

```text
CATEGORY_ORDER : 🟢Nav 🟢Sinc 🟡Chat 🟢Prod 🟡Media 🔴Over 🟡Launch 🔴Anti 🔴Sist ⚪Otros
sorted()       : ⚪Otros 🔴Anti 🔴Over 🔴Sist 🟡Chat 🟡Launch 🟡Media 🟢Nav 🟢Prod 🟢Sinc
primer caracter : 0x26aa 0x1f534 0x1f534 0x1f534 0x1f7e1 0x1f7e1 0x1f7e1 0x1f7e2 0x1f7e2 0x1f7e2
```

`sorted()` de cadenas ordena por **punto de código Unicode**, no por el significado del emoji. El
círculo `⚪ Otros` (U+26AA) vive en el plano Basic Multilingual, mientras que 🟢 🟡 🔴
(U+1F7E2, U+1F7E1, U+1F534) viven en el plano suplementario, que empieza **después**. Resultado: el
bloque rojo «NO CERRAR» se pinta por encima del verde «SEGURO» y el «sin clasificar» sale el primero.

```python
# MAL - ordena por punto de codigo del emoji
for cat in sorted(categories.keys()):
    ...
sorted_cats = sorted(list(all_cats))   # el SEGUNDO sitio del mismo defecto

# BIEN - la politica vive en UN sitio, en config.py
from woptimizer.config import ordenar_categorias
for cat in ordenar_categorias(categories.keys()):
    ...
```

**Corolario para cualquier lista de este proyecto** (categorías, nombres de pack, prioridades): si el
orden tiene un significado, el «alfabético» **no** es una opción neutra. Y si además hay
elementos desconocidos, `sorted(cats, key=idx.get)` los manda al final **gracias a la estabilidad**, no
porque `999` sea especial.

> Nota de numeración: algunos documentos de ciclo se refieren como «Trampa #16» al problema de
> codificación `cp1252` en la consola de Windows, que en este fichero es la **Trampa #6**. Si las dos
> numeraciones se mezclan, manda este fichero.

**Sondas:** `test_orden_de_categorias_no_es_alfabetico` en `run_tests.py` (comportamiento + guarda
`ast` sobre los DOS ficheros, para que el defecto no vuelva por la puerta que se olvide).

## Trampa #17: `normpath` y `commonpath` son LÉXICOS: no atraviesan un junction

**Medido en TASK-027 iteración 2** (el `mutation-auditor` lo encontró aceptando apps), sobre un
junction **real** creado con `mklink /J <TEMP>\jdir C:\Windows\System32`:

```text
ruta                     <TEMP>\jdir\cmd.exe
os.path.normpath(ruta)   <TEMP>\jdir\cmd.exe          <- intacta, no toca el enlace
commonpath([ruta, LOCALAPPDATA])   C:\...\AppData\Local   <- "contiene": FALSO
os.path.isfile(ruta)     True                            <- sigue el enlace
os.stat(ruta).st_file_attributes    0x20                  <- ni reparse: no lo ve
os.path.realpath(ruta)   C:\Windows\System32\cmd.exe      <- la verdad
```

O sea: una comprobación de contención hecha con `normpath` + `commonpath` **dice que un
`cmd.exe` está dentro de `%LOCALAPPDATA%`**, y el filtro de extensiones tampoco ayuda porque la
extensión se mira en el **alias**. Dos ataques en la misma idea:

1. junction/enlace **fuera** de las raíces → se acepta y se ejecuta;
2. `.exe` que es un enlace a un `.bat` **de una raíz permitida** → la contención real lo acepta y
   la lista blanca se esquiva entera, porque `ShellExecute` pasa el `.bat` por `cmd.exe /c`.

**Y la variante de atributo tampoco sirve:** `os.stat`/`os.lstat` sobre la ruta **a través** de un
junction de directorio intermedio devuelven `0x20` (sin `FILE_ATTRIBUTE_REPARSE_POINT`), porque
siguen el enlace. Solo el enlace **final** lo delata (`0x420`, medido). Es decir: el atributo
solo ve el último tramo.

**El arreglo** es resolver por descriptor y repetir las comprobaciones sobre la ruta real. En
Windows eso es `os.path.realpath(ruta, strict=True)` (por debajo `GetFinalPathNameByHandleW`), y
`strict=True` es lo que hace la regla **fail-closed**: si el SO no resuelve, no se arranca. Las
**raíces** se resuelven por el mismo camino, o el criterio se aplica a dos medidas distintas y se
rechazan apps legítimas.

**Corolario para cualquier validación de rutas de este proyecto:** *normalizar* no es *resolver*.
Si la pregunta que responde la comprobación es «¿esto está dentro de la raíz?», y la raíz
puede tener enlaces, hay que preguntar al SO. Y hay que devolver **la ruta por la que se
contesta que sí**, no la que se escribió.

**Lo que seguía SIN cerrar, y cómo se cerró en la iteración 3 de TASK-027.** Este apartado decía que un
**hard link** (`mklink /H`) "no es un reparse point, así que ni `realpath` ni los atributos lo ven" y que
"no es arreglable con esta regla, y no hace falta". **Las dos mitades de esa razón eran falsas:**

1. **"Ningún filtro lo ve" es falso.** `os.stat(ruta).st_nlink` vale **2** en un hard link (medido). Sí lo ve.
2. **Y da igual que lo vea, porque el hard link no era el agujero.** Medido en esta máquina con las dos
   variantes construidas de verdad, el validador acepta el hard link (`alias.exe` → `payload.bat` fuera de
   las raíces, `st_nlink == 2`) **y también una copia plena** del mismo `.bat` con nombre `.exe`
   (`st_nlink == 1`, sin un solo enlace, sin junction, sin symlink, sin privilegios). Rechazar
   `st_nlink > 1` habría cerrado el caso exótico y habría dejado abierto el trivial.
3. **La variante "rechazar solo si el destino no está en las raíces" no es implementable.** Un hard link no
   tiene destino consultable: no hay API en Windows que devuelva los otros nombres de un fichero a partir
   de su ruta. Y aunque la hubiera, sería irrelevante: el atacante elige qué nombre queda dentro de la raíz.
4. **Por qué no se usa `st_nlink` a pelo:** porque el **8,32 % de los ejecutables instalados** tienen
   enlaces duros legítimos. Medido en las seis raíces: de **2273** `.exe`/`.com`, **189** tienen
   `st_nlink > 1` (hasta 6), y son programas de Microsoft (`msinfo32.exe`, `TabTip.exe`, los auxiliares de
   Edge, las herramientas de Hyper-V). "Rechazar cualquier `st_nlink > 1`" es un falso positivo del 8 %.

**El cierre real es la regla 9 (`_es_imagen_pe`): el contenido, no el nombre.** La lista blanca de`.exe`/`.com` siempre quiso expresar que `.exe` significa "imagen PE", no "algo que se arranca", pero se
cumplía mirando el **nombre**, y un hard link (o una copia) tiene el nombre que le pongas. La regla 9
comprueba que el fichero lleva `MZ` y la firma `PE\0\0` en el offset que declara `e_lfanew`, **después** de
la resolución real, sobre el fichero que se va a arrancar de verdad. Coste medido antes de escribirla:
**2200 de 2273** `.exe`/`.com` instalados la cumplen, y **ninguno de los 189 multi-enlazados falla** (0
falsos negativos en justo el caso que se quería cerrar). Los 19 que no la cumplen son appx de WindowsApps,
la caché de MSI de `%APPDATA%\Microsoft\Installer` y un `.COM` DOS de 16 bits: ninguno es una app
lanzable. Fail-closed: lo que no se puede leer, no es un PE y no se arranca.

> **Corolario, y es la parte que más cuesta aprender:** *cerrar un agujero de nombres no es cerrar el
> agujero.* El filtro de rutas miraba el nombre del fichero; el nombre es lo primero que elige el atacante.
> La pregunta que sobrevive a todos los ejemplos de directorios es: **¿el fichero es lo que dice ser?**

**Corolario para las sondas de este repo:** un caso de seguridad que necesita un objeto del
sistema de ficheros (un junction, un hard link, una permisos denegada) **no se puede simular con
un doble**: o se crea el objeto de verdad, o el test pasa por el motivo equivocado. Y si no se
puede crear, el test **falla ruidosamente** (helper `_mklink` en `run_tests.py`), porque un test
que se pone verde por no poder construir su caso es peor que no tener test.

**Y el corolario de los corolarios, medido en esta iteración:** al añadir la regla 9, los fixtures que
hacían de "una app" eran ficheros **vacíos** — y un `.exe` vacío no es un PE, así que la regla nueva los
rechazaba **por el motivo equivocado**. Dos propiedades dejaron de estar probadas sin que ninguna sonda
se quejara: la extensión real (mutación **A3** de la iteración 2) y la lista blanca (caso (b)). Una sonda
que sigue verde puede estar midiendo otra cosa. Se arregla poniendo en las fixtures lo que dicen
representar (`_escribir_pe_minimo`) y, mejor, haciendo que **el mismo contenido** con `.bat` no arranque y
con `.exe` sí: así la diferencia la tiene que hacer la extensión y no el contenido.

**Sondas:** `test_un_junction_no_puede_colar_lo_que_hay_detras`,
`test_la_contencion_no_acepta_un_hermano_de_prefijo`, `test_la_contencion_no_depende_de_la_caja` y
`test_un_hard_link_no_es_una_hoja_y_el_script_no_pasa`
en `run_tests.py`; matriz de mutación en `_mutmatrix_t027_iter2.py` (21 mutaciones, 21 muertas, re-verificada
en la iteración 3) y `_mutmatrix_t027_iter3.py` (5 mutaciones, 5 muertas), y la
tabla en `docs/ai/testing-guide.md`.

## Trampa #18: PowerShell parsea el bloque entero ANTES de ejecutar: una regex inline tumba todo

**Medido en el ciclo 21** (2026-09-30), y lo encontraron tres actores independientes en la misma tarde:
`openspec-dev` ("Shell escaping mangled it"), `mutation-auditor` ("PowerShell quoting is fighting the
regex") y el propio orquestador. No es un incidente aislado: es el fallo por defecto.

```powershell
# FALLA
python -c "import re; print(re.findall(r'\"([a-z]+)\"', 'k=\"v\"'))"
# ParserError: Falta ] al final del atributo o literal de tipo.   (senala el corchete, NO la causa)
```

**Por qué es peor que un error de escapado normal.** PowerShell **analiza el bloque entero antes de
ejecutar ninguna línea**. Un solo `ParserError` aborta *todas* las líneas del comando, incluidas las
correctas: no hay resultados parciales. Y el mensaje apunta a una posición engañosa (el corchete de la
regex), así que depurar el escapado consume iteraciones que vuelven a perder el bloque completo. El
propio mensaje sale con los caracteres de la regex ya reinterpretados, así que ni se lee bien.

**El patrón que funciona** (here-string → fichero → ejecutar):

```powershell
$code = @'
import re
print("findall:", re.findall(r'"([a-z]+)"', 'key="value" other="x"'))
'@
Set-Content -Path probe.py -Value $code -Encoding UTF8
python probe.py
# findall: ['value', 'x']    exit=0
```

**Regla:** en cuanto el inline deje de ser trivial —una regex, dos tipos de comilla, una barra
invertida, un f-string con llaves— pasa a fichero de una vez. No dediques iteraciones al escapado.

**Corolario de la misma clase, en Python:** al mutar código, **purga `__pycache__` entre mutaciones**.
Python reutiliza un `.pyc` obsoleto si el mutante tiene la misma longitud en bytes y el mismo segundo de
mtime, y entonces el veredicto es FALSO. Contamina además el mutante *siguiente*, que es exactamente
como se cuela un "sobreviviente" que no existe. Le costó un lote entero al `mutation-auditor` del ciclo 21.

**No confundir con la Trampa #16** (consola `cp1252`): aquella es Python *escribiendo* emoji y flechas;
esta es PowerShell *parseando* antes de que Python exista. `cp1252` se arregla con ASCII en `print()`;
esta se arregla con ficheros.

## Resumen de reglas para IA que modifique este proyecto

1. **NUNCA uses `$pid` en scripts PowerShell** — usa `$procId` u otro nombre
2. **NUNCA añadas auto-elevation con `sys.exit` silencioso** — debe mostrar error o continuar
3. **SIEMPRE aplica `CREATE_NO_WINDOW`** en todos los subprocess
4. **SIEMPRE valida con `verify_app.py` y `test_kill_real.py`** tras cambios
5. **NUNCA asumas que funciona** — verifica con `poll()` que el proceso sigue vivo
6. **USA `root.after(0, callback)`** para actualizar widgets desde threads
7. **USA TAB como delimitador** entre Python y PowerShell
8. **NO añadas features sin test** — un cambio a la vez, validando cada uno
9. **NUNCA valides rutas de este proyecto solo con `normpath`/`commonpath`** — son léxicos y no
   atraviesan un junction; resuelve con `os.path.realpath(..., strict=True)` y compara la ruta
   real (Trampa #17)
10. **NUNCA des `os.startfile` por confianza**: ejecuta por intérprete lo que sea `.bat`/`.cmd`,
   aunque la ruta esté dentro de la raíz permitida — la extensión se mira en la ruta **real**
11. **NUNCA simules con un doble un caso de seguridad que necesita un objeto real del sistema de
   ficheros** (junction, permisos, hard link): constrúyelo, y si no puedes, falla en voz alta
   (Trampa #17)
12. **NUNCA pases una regex a `python -c` desde PowerShell** — PowerShell parsea el bloque entero
   antes de ejecutar, así que un solo `ParserError` aborta también las líneas correctas y no hay
   resultados parciales. Escribe un fichero `.py` y ejecútalo. Y al mutar código, **purga
   `__pycache__` entre mutaciones**: si el mutante tiene la misma longitud y el mismo segundo de
   mtime, Python reutiliza un `.pyc` obsoleto y el veredicto es falso (Trampa #18)
