# TASK-073 — Programación segura en el bucle de Tk desde hilos worker

## Why

`run_tests.py` imprime intermitentemente `RuntimeError: main thread is not in main loop`
desde los hilos worker de las vistas. La lectura fácil es "pon un `try/except` alrededor del
`after` de `ProcessManagerView._load`". **Esa lectura es falsa por partida triple**, y las tres
partes se midieron contra Tk real (CustomTkinter 6.0.0) antes de escribir esta spec.

### F1 · El guard que propone el encargo no puede hacer lo que dice (MEDIDO)

`tasks.json` (TASK-073, AC-1) prescribe literalmente:

```python
try:
    if self.winfo_exists():
        self.after(...)
except Exception:
    pass
```

Esa comprobación **nunca llega a responder**. MEDIDO, desde un hilo secundario:

| llamada | ventana VIVA | ventana destruida |
|---|---|---|
| `widget.winfo_exists()` | `RuntimeError: main thread is not in main loop` | `RuntimeError: main thread is not in main loop` |

**1 de 1, y con la ventana perfectamente viva.** `winfo_exists()` es una llamada Tcl, y desde
un hilo que no es el principal se encola igual que `after`. O sea: el `if` no está preguntando
"¿existe la ventana?", está launching la misma excepción que el guard dice evitar, un paso antes.
Funciona *por accidente* (el `except` se traga el `RuntimeError` de la propia comprobación), y en
ese mundo no pasa nada porque **`after` tampoco habría funcionado jamás**. Un guard que nunca se
evalúa no se puede auditar ni mutar.

### F2 · El probe es innecesario: Tk ya descarta lo que la vista destruction mata (MEDIDO)

Con `mainloop()` real en marcha, worker secundario, `after(400, cb)` programado sobre un widget
vivo y la ventana destruida **150 ms después**:

```
worker: after(400) programado
ventana: destruida 150 ms despues de programar
(corriendo el callback) → NUNCA
```

El callback **no se ejecuta y no revienta**. Tk lo descarta junto con el widget, porque el timer
y el comando que invoca pertenecen a la commanded que se borra. Consecuencia directa: **el
`try/except` alrededor de la *programación* es la solución completa y suficiente**, y no existe la
ventana de carrera posterior que el probe pretendería cerrar.

Con mainloop vivo, el resto de la tabla (MEDIDO):

| llamada desde hilo secundario | con `mainloop()` |
|---|---|
| `widget.winfo_exists()` | `OK -> 1` |
| `widget.after(0, ...)` | `OK -> 'after#12'` |

**Conclusión de F1+F2:** el defecto es real, pero vive **solo en el mundo sin bucle principal**
(`run_tests.py`, que usa `update()`, nunca `mainloop()`). En producción, con la app corriendo, un
`after` desde un worker **se atiende**. El fix es un `try/except`; el `winfo_exists()` se cae.

### F3 · No son 5 puntos: son 10, en TRES vistas

| fichero | línea | llamada |
|---|---|---|
| `views/process_manager_view.py` | 179 | `self.after(0, self._do_load)` |
| `views/process_manager_view.py` | 194 | `self.after(0, _handle_err)` |
| `views/process_manager_view.py` | 202 | `self.after(0, _handle_ok)` |
| `views/process_manager_view.py` | 209 | `self.after(0, self._apply_load, procs)` |
| `views/process_manager_view.py` | 407 | `self.after(0, self._publicar_cierre, ...)` |
| `views/dashboard_view.py` | 279 | `self.after(0, self._on_restore_finished, started, failed)` |
| `views/dashboard_view.py` | 491 | `self.after(0, self._show_banner, killed, ...)` |
| `views/dashboard_view.py` | 522 | `self.after(0, self._show_start_banner, ...)` |
| `views/pack_manager_view.py` | 679 | `self.after(0, self._inline_status, texto, color)` |
| `views/pack_manager_view.py` | 722 | `self.after(0, self._inline_status, texto, color)` |

Los **10** son publicaciones desde `threading.Thread(..., daemon=True)`. Planear solo
`ProcessManagerView` deja 7 vivos, y el aviso del encargo ("la deuda vuelve en la siguiente
vista") se cumple por el método exacto que propone: un `try/except` copiado a mano.

### F4 · El arreglo ROMPE un test que existe (no es hipótesis, es aritmética)

`run_tests.py:8747` `test_los_workers_de_pack_solo_publican_por_after` recorre cada `ast.Call` del
worker y aplica `_raiz_de_self` (`run_tests.py:8840`). La rama que decide está en
**`run_tests.py:8897`**:

```python
raiz, camino = _raiz_de_self(call.func)
if raiz is None:
    continue
if raiz != "after":            # <-- TODO lo que no sea `self.after` cae aqui
    if (raiz, camino[-1]) in PERMITIDOS:
        ...
    malos.append(f"... self.{'.'.join(camino)}(...) desde el hilo secundario")
```

Para `self._publicar_en_el_bucle(0, self._apply_load, procs)`, `_raiz_de_self` devuelve
`("_publicar_en_el_bucle", ["_publicar_en_el_bucle"])`: `raiz != "after"`, el par no está en
`PERMITIDOS` → **infracción, suite en rojo**.

Y el arreglo fácil —añadir el par a `PERMITIDOS`— es **peor que no hacer nada**: las comprobaciones
de `run_tests.py:8916-8920` (`self.after` debe ser **de 0 ms** y publicar en un callback de
`CALLBACKS`) solo se aplican a la rama `raiz == "after"`. Meter el helper en `PERMITIDOS` **degrada
la guarda**: a partir de ese momento, un worker podría publicar a 3000 ms y a un callback
cualquiera sin que nadie lo viera. Esa lista se construyó a base de que un guard que no mide es
peor que no tener guard (`run_tests.py:8750-8756`).

### F5 · No existe clase base común de las vistas

`MainWindow(ctk.CTkFrame)` (`ui/main_window.py:11`) es un **contenedor**, no la base de las vistas.
Las tres vistas cuelgan de `(Confirmable, ctk.CTkFrame)`:

- `views/dashboard_view.py:22`
- `views/pack_manager_view.py:100`
- `views/process_manager_view.py:38`

La **única superficie compartida real** es el mixin `Confirmable` (`ui/confirmation.py:158`), que ya
es dueño del ciclo de vida de los timers de Tk: `TkScheduler` (`:57`), `cancel_on_destroy` (`:176`) y
`_schedule_ui` (`:273`).

### F6 · Referencia documental desfasada

`tasks.json` (descripción y notas de TASK-073) cita **"STATUS.md (fila 122)"**. MEDIDO:
`STATUS.md` tiene **121 líneas**, su sección `## ⚠️ Deuda Técnica Conocida` está en la **línea 58**,
y **TASK-073 no está en ella**: está en la tabla de backlog, **línea 33**. La referencia apunta a una
versión anterior del fichero. Se corrige al escribir STATUS.md en el Paso 3.

---

## Decisión de diseño

### Elegido: función pura a nivel de módulo + delegación de una línea en `Confirmable`

**Fichero NUEVO `src/woptimizer/ui/tk_thread.py`** — una función, sin estado, sin imports de Tk:

```python
def publicar_en_bucle(widget, delay_ms, callback, *args):
    """Programa `callback` en el bucle de Tk y devuelve el handle, o None.

    Unico punto autorizado para publicar desde un hilo secundario. Sin mainloop
    (los tests headless) o con el widget ya destruido, `widget.after` lanza y se
    devuelve None: el retorno se distingue de un handle real porque None no es
    un id de Tcl. MEDIDO 2026-10-18: `winfo_exists()` desde un hilo secundario
    lanza el MISMO RuntimeError que `after`, incluso con la ventana viva, asi que
    un probe de existencia aqui no compra nada. Y con mainloop vivo Tk ya
    descarta los `after` pendientes del widget destruido, de modo que el cuerpo
    del callback no llega a ejecutarse nunca.
    """
    try:
        return widget.after(delay_ms, callback, *args)
    except Exception:   # RuntimeError sin mainloop; tk.TclError si la vista murio
        return None
```

**Y en `Confirmable`** (`ui/confirmation.py`), una delegación de una línea junto a `_schedule_ui`:

```python
def _publicar_en_el_bucle(self, delay_ms, callback, *args):
    """Única puerta de las vistas al bucle de Tk desde un hilo secundario."""
    return publicar_en_bucle(self, delay_ms, callback, *args)
```

### Por qué esta y no las otras dos

| Opción | Veredicto |
|---|---|
| Método de instancia en cada vista | **Descartada.** 3 copias de un `try/except` de 4 líneas. Es literalmente la deuda que el encargo quiere evitar. |
| Clase base común de las vistas | **Descartada (no existe).** F5: no hay tal clase, y crear una jerarquía nueva para un fix de 4 líneas es un refactor desproporcionado que además toca la navegación de `main_window`. |
| Método en el mixin `Confirmable` (sin más) | **Descartada por dos razones concretas.** (1) `confirmation.py:14` se autodescribe como *"QUE HAY DENTRO (dos capas, y solo dos)"*; meterle una tercera contradice una promesa escrita del propio módulo. (2) Su frontera de importación (`:21-25`) es strictísima — solo `typing`, prohibido `tkinter` a nivel de módulo. La función pura vive en su propio fichero y **no necesita ese permiso**. |
| **Función pura + delegación de 1 línea** | **ELEGIDA.** La lógica queda en un módulo `typing`-only testeable sin Tk; la vista conserva **una sola superficie Tk** que el guard AST puede nombrar; y `Confirmable` sigue siendo "dos capas" porque su método es una delegación, no la implementación. |

### Por qué NO se reutiliza `_schedule_ui` (rechazado, con motivo)

`Confirmable._schedule_ui` (`ui/confirmation.py:273`) **ya tiene** su `try/except` (`:282-285`), luego
`self._schedule_ui(0, lambda: self._apply_load(procs))` parecería Bastar sin escribir nada. Se
descarta por dos razones medibles:

1. **Carrera de hilos.** `_schedule_ui` registra el handle en `self._timers_ui` (`:287`), y
   `cancel_on_destroy` lo itera en el hilo principal (`:179`). Hacer eso **desde un worker** es una
   mutación de `set` compartida entre dos hilos. Además hoy no ocurre porque en el `except` se
   devuelve antes (`:284-285`), y eso es casualidad, no diseño.
2. **Contratos distintos.** `_schedule_ui` es un timer **cancelable** con `scheduler` inyectable
   para tests, y siempre se llama desde el hilo principal. La publicación worker→main no se cancela
   (0 ms: cuando el bucle la atienda ya no hay nada que cancelar) y no necesita inyección. Son dos
   funciones de una línea cada una, con contratos distintos, y **esa es la duplicación sana**.

---

## What Changes

### CERO ediciones de código de producción en el Paso 2. Esto es lo que toca el Paso 3.

| fichero | acción | detalle |
|---|---|---|
| `src/woptimizer/ui/tk_thread.py` | **NUEVO** | `publicar_en_bucle` + docstring con las mediciones. Solo `typing`. |
| `src/woptimizer/ui/confirmation.py` | EDITAR | import de `publicar_en_bucle`; método `_publicar_en_el_bucle` junto a `_schedule_ui` (`:273`); actualizar la autodescripción "dos capas" (`:14`) para que mencione la tercera por delegación. |
| `src/woptimizer/ui/views/process_manager_view.py` | EDITAR | líneas 179, 194, 202, 209, 407 → `self._publicar_en_el_bucle(0, ...)` |
| `src/woptimizer/ui/views/dashboard_view.py` | EDITAR | líneas 279, 491, 522 → ídem |
| `src/woptimizer/ui/views/pack_manager_view.py` | EDITAR | líneas 679, 722 → ídem |
| `run_tests.py` | EDITAR | 2 tests nuevos + **extender el guard de `run_tests.py:8897`** (F4) + la lista de invocaciones al final |
| `docs/ai/ui-design-system.md` | EDITAR | contrato de publicación worker→main |
| `docs/ai/testing-guide.md` | EDITAR | tabla de reparto: **203 → 205** (142 backend + 63 headless) y las 2 filas nuevas |
| `STATUS.md` | EDITAR | debt sanedada, y corregir la referencia "fila 122" → línea 33 (F6) |
| `CHANGELOG.md` + `.taskmaster/CHANGELOG.md` | EDITAR | entrada del pase |

**Invariante de capas (AGENTS.md): intacto.** `tk_thread.py` no importa `psutil`, `json`, ni
`woptimizer.services`; solo llama a un método del widget. Programar en el bucle de Tk **es** una
operación de UI, y sigue siendo UI lo que la hace. Lo que AGENTS.md prohíbe es que la UI toque el
SO o el JSON, y eso no ocurre.

---

## Criterio discriminante del test (obligatorio)

El defecto que hay que cazar es **"se tragó la excepción"**, no "saltó una excepción". Un test que
comprueba que no revienta pasa **verde con el guard quitado**, porque el `except` hace exactamente
eso: tragarse el error y seguir como si nada. Por eso la aserción central **no es sobre la
excepción, es sobre si el callback llegó a PROGRAMARSE**.

### Test 1 — `test_publicar_en_el_bucle_no_programa_si_la_vista_ya_murio`

Doble `_VistaFalsa` con `llamadas: list` donde `after(...)` **registra y lanza**
`RuntimeError("main thread is not in main loop")` — el síntoma literal medido.

**Caso A — la vista murió (el defecto).** Tras la llamada:

```python
assert vista.llamadas == []      # <-- LA ASERCIÓN QUE DISCRIMINA
assert handle is None
```

`llamadas == []` es la que separa **programó** de **se tragó**: con el guard ausente, `after` se
invoca (y por tanto la lista tiene un elemento), el `RuntimeError` lo absorbe el `except`, y el test
que solo mirara "no revienta" saldría **verde**. Con esta línea, ese mismo mutante sale **rojo**.

**Caso B — la vista vive (mata el mutante degenerado).** `after` devuelve el centinela `"after#1"`:

```python
assert vista.llamadas == [(0, callback, (1, 2))]
assert handle == "after#1"
```

Sin el caso B, un helper que **nunca programa nada** y devuelve siempre `None` pasaría el caso A:
es el otro extremo de "tragarse todo", y es el que hace que un guard sin contraprueba se vuelva
inofensivo.

**Caso C — la vista vive pero `after` revienta (la ventana murió en el microsegundo intermedio).**
`handle is None`, sin excepción, y `llamadas` tiene **una** entrada: se intentó, y el fallo se
tragó. Distingue "no se intentó por estar muerta" de "se intentó y falló".

### Test 2 — `test_ninguna_vista_programa_after_a_mano` (anti-regresión)

`ast` sobre los **tres** ficheros de `src/woptimizer/ui/views/`: **cero** atributos `self.after`.
Es el guard que impide que la deuda vuelva por la puerta que el encargo quiere cerrar.

**Y con contraprueba, que es la mitad que de verdad discrimina.** Un guard de "cero ocurrencias"
puede no ver nada y quedar verde para siempre — que es exactamente lo que **`ast` no vio** en
`test_ninguna_llamada_de_cat_file_batch_check_se_queda_sin_input`: la detección existía, no veía, y
`for argumento in []` dejaba la suite entera en verde (`docs/ai/testing-guide.md:1293`). Por tanto
este test aplica **su propia detección** a un fragmento sintético con `self.after(0, f)` y exige que
lo marque, y a un fragmento conforme con `self._publicar_en_el_bucle(0, f)` y exige que no lo
marque. Sin esa contraprueba, este test 2 es decorativo.

### Test 3 — integración con el guard existente (F4)

`test_los_workers_de_pack_solo_publican_por_after` (`run_tests.py:8747`) **tiene que seguir verde**
con los 10 call sites migrados, y para eso `_infracciones` necesita **una rama nueva**, no un par
nuevo en `PERMITIDOS`. Debe exigir **exactamente lo mismo** que ya exige a `self.after`: delay `0`
y callback dentro de `CALLBACKS` (`run_tests.py:8830-8831`, `:8916-8920`). Comprobación cruzada
obligatoria: mutar esa rama para que acepte 3000 ms debe poner el test en rojo.

---

## Impact

- **Riesgo de datos:** ninguno. El cambio solo decide *si* se programa un callback que ya no tenía
  destino; no cambia qué se calcula ni qué se guarda.
- **Riesgo de threading:** eliminado, no introducido. El helper no toca estado compartido (§
  "Por qué NO se reutiliza `_schedule_ui`").
- **Riesgo de suite:** **real y obligatorio** — F4. Sin extender el guard de `run_tests.py:8897`,
  el Paso 3 deja la suite en rojo y parece un fallo del fix.
- **Suite:** 203 → 205 (142 backend + 63 headless).