# Auditoría de mutación — Ciclo 62 / TASK-073

**Rol:** `mutation-auditor` (Sherlock). **Ancla del repo real:** `bbcc472417fb09652b2ba0cb9c47f8f1737a4888`.
**Ciclo auditado:** 62. **Commits:** `df294dc` (planificación), `bbcc472` (implementación).
**Superficie del ciclo:** `src/woptimizer/ui/tk_thread.py` (nuevo), la delegación `_publicar_en_el_bucle`
en `ui/confirmation.py`, 10 call sites migrados en 3 vistas, y 2 tests nuevos + la rama nueva del guard
AST en `run_tests.py`.

**Pregunta que se responde:** si el código de este ciclo estuviera mal, ¿los tests se enterarían?

---

## 0. Cámara y aislamiento (por qué el repo real está intacto)

Todo el trabajo se hizo sobre copias en `%TEMP%\wopt_audit_62\`. **Cero escrituras bajo
`C:/Users/carch/Nextcloud/Scripts/woptimizer/`** salvo este fichero.

El protocolo del gitlink se siguió por el orden que obliga (`agent.md` §2):

1. **Copia con `shutil.copytree(..., ignore=shutil.ignore_patterns(".git", ...))`**, que excluye
   `.git` como *fichero* además de como directorio. MEDIDO: `.git` como fichero en la cámara =
   `False`, directorios `.git` en la cámara = `[]`.
2. **`git_safe_commit.py` NO se invocó ni una vez** (prohibición expresa del encargo). Todo
   versionado se hizo con `git` a pelo contra cámaras desechables.
3. **Aislamiento probado antes de mutar nada**, en tres direcciones:
   - con `GIT_DIR` explícito de la cámara → resuelve a la cámara;
   - con **entorno limpio** (discovery) → `fatal: not a git repository`, o sea, la cámara **no**
     alcanza el repo real;
   - el repo real → `%LOCALAPPDATA%\woptimizer_git\.git`, HEAD `bbcc472`.
4. **`GIT_DIR` desechable nuevo por cámara**; las cámaras de mutante se crean por
   `git clone --local --no-hardlinks` desde una base con **el historial real**, nunca por
   `git init` (ver §5, hallazgo de arnés **H1**).

### H1 · Fallo de arnés medido: una cámara con `git init` da veredictos FALSOS

La primera base (copia + `git init` + 1 commit) **murió en el test ~43 de 205**, mucho antes de
llegar a los tests 204/205:

```
AssertionError: un hash REAL mas un caracter tiene que NO existir: `cat-file -e` responde 128
con `fatal: Not a valid object name` y eso se traduce a False, no a un AssertionError.
```

`test_ninguna_llamada_de_cat_file_batch_check_se_queda_sin_input` necesita **objetos reales del
historial**. Un rojo ahí dice del arnés, no del mutante: es el modo "log corto + instrumentación
rota" que el encargo manda leer como **NO MEDIDO**. Toda la tanda se descartó y se rehízo clonando
el historial real. Con la base clonada, la suite termina en `ALL TESTS PASSED.` (rc=0, 25 831 B).

### Aislamiento verificado al cierre

```
git log --oneline -1   -> bbcc472 fix(ui): publicar en el bucle de Tk sin propagar RuntimeError (TASK-073)
git reflog -3          -> bbcc472 / df294dc / ac4006a   (sin entradas nuevas)
git status --porcelain -> (0 líneas)
git rev-parse --git-dir -> C:/Users/carch/AppData/Local/woptimizer_git/.git
git diff --stat        -> (vacío)
git diff --cached --stat -> (vacío)
```

**No se tocó el repositorio real en ningún momento, ni siquiera para reparar un hallazgo.**

---

## 1. Lo que la suite mide de verdad (medido, no leído)

Antes de mutar nada se comprobó el terreno, porque un mutante que sobrevive solo significa algo
si el resto de la red está donde se cree que está.

| Afirmación | Veredicto | Cómo se comprobó |
|---|---|---|
| `run_tests.py` tiene 205 tests | **CIERTO** | 205 `def test_*`, 205 invocadas, **0 definidas-no-invocadas** |
| Reparto **142 backend + 63 headless** | **CIERTO** | `_reparto_de_tests` de `validate_docs.py` → `(142, 63, 205)`, marcador en `run_tests.py:25829`. Declarado igual en `STATUS.md` y `docs/ai/testing-guide.md` |
| Las 3 vistas ya no programan `after` a mano | **CIERTO** | `ast` sobre las 3: **0** `self.after`. Ningún fichero de `src/` lo tiene |
| Los 10 call sites migrados existen | **CIERTO** | 5 + 3 + 2, contados sobre el código, no sobre el `tasks.md` |
| `tk_thread.py` solo importa `typing` | **CIERTO** | `ast` → `['typing']`; único importador: `ui/confirmation.py` |
| `architecture.md` sitúa `tk_thread.py` en su capa | **CIERTO** | `docs/ai/architecture.md:36` lo nombra explícitamente |

---

## 2. Medición D1 · La afirmación "`winfo_exists()` lanza desde un worker" es IMPRECISA

`ui/tk_thread.py:12-18` y `docs/ai/ui-design-system.md:185` afirmar, idéntico texto:

> "`winfo_exists()` desde un hilo secundario lanza `RuntimeError: main thread is not in main loop`
> **incluso con la ventana perfectamente viva**. MEDIDO, 1 de 1."

Eso es lo que sostiene el caso D del test 204. **Se reprodujo contra Tk real. MEDIDO:**

| Escenario | `winfo_exists()` desde worker | `after(0, cb)` desde worker |
|---|---|---|
| A. root + `withdraw()`, **sin** `update()` y **sin** `mainloop()` | `RuntimeError: main thread is not in main loop` | `RuntimeError` |
| B. root + `update()` una vez, **sin** `mainloop()` (el caso de `run_tests.py`) | `RuntimeError: main thread is not in main loop` | `RuntimeError` |
| C. root **visible** + `mainloop()` **vivo** | **`OK -> 1`** (0,1 ms) | `OK -> 'after#4'` (0,1 ms) |
| D. `mainloop()` vivo, widget **ya destruido** | **`OK -> 0`** (0,0 ms) | `OK -> 'after#2'` |
| E. `mainloop()` vivo, principal ocupado 1,5 s | — | `OK -> 'after#6'` en 0,1 ms (**no bloquea**) |

**Lo medido:** el `RuntimeError` ocurre **solo en el mundo sin bucle principal** (A y B). Con
`mainloop()` vivo, `winfo_exists()` **no lanza** y, además, **discrimina correctamente**: devuelve
`1` con la ventana viva y `0` con el widget destruido.

**Consecuencia 1 — la frase escrita es falsa.** "también con la ventana perfectamente viva"
describe justo el escenario C, donde no lanza. La medición correcta es "sin bucle principal", que
es un mundo más estrecho que el que dice el texto.

**Consecuencia 2 — el documento se contradice a sí mismo a 8 líneas.** `ui-design-system.md:193-195`
dice lo correcto: *"Con la app corriendo, un `after` desde un worker **se atiende**: el defecto
solo se manifiesta en el mundo sin bucle principal"*. Las dos afirmaciones no pueden ser ciertas
a la vez, y el caso D del test 204 está cableado a la primera.

**Consecuencia 3 — la conclusión de diseño aguanta, la justificación no.** Descartar la sonda sigue
siendo defendible (en el mundo sin bucle, `after` también lanza, así que el probe no aporta). Pero
quien lea el docstring dentro de seis meses *"para no volver a proponerla"* (**T2 del plan**, que
justifica el docstring) se lleva una medición que no se reproduce.

---

## 3. Hallazgos documentales y de cobertura (todos medidos contra el código)

### F · `run_tests.py:25543` tiene un `NameError` en el mensaje del guard de la frontera

```python
prohibido_tk = importados & {...}          # L25540, correcto
assert not prohibido_tk, (
    f"ui/tk_thread.py viola la frontera de capas: importa {sorted(proibido_tk)}. "   # L25543, TYP0
```

El `f-string` escribe **`proibido_tk`** (sin la "h"). El guard **sí** pone la suite en rojo cuando
la frontera se rompe (mutantes **F1** y **F1b**), pero muere por `NameError`, no por `AssertionError`:

```
File "...run_tests.py", line 25543, in test_ninguna_vista_programa_after_a_mano
    f"ui/tk_thread.py viola la frontera de capas: importa {sorted(proibido_tk)}. "
NameError: name 'proibido_tk' is not defined. Did you mean: 'prohibido_tk'?
```

El propio repo seRoom para esto: `run_tests.py:8953-8956` dice *"El nombre del infractor va en el
mensaje a propósito: un 'debe publicar en [...]' sin decir QUÉ publica obliga a abrir el fichero
para entender el rojo"*. El mensaje que no compila es exactamente ese mensaje.

### M8 · Solo **6 de los 10** call sites migrados están dentro de la red del guard AST — **MEDIDO**

`test_los_workers_de_pack_solo_publican_por_after` recorre 5 métodos
(`DashboardView.execute_pack`, `PackManagerView.kill_pack`/`start_pack`,
`ProcessManagerView._do_load`/`on_kill_selected`) y, dentro de ellos, solo los `def` que se pasan a
`threading.Thread(target=...)`. Resultado sobre los 10 call sites del ciclo:

| Fichero | Call sites dentro de la red | Fuera (solo los ve el test 205) |
|---|---|---|
| `dashboard_view.py` | L495, L526 | **L283** |
| `pack_manager_view.py` | L679, L722 | — |
| `process_manager_view.py` | L211, L409 | **L181, L196, L204** |
| **Total** | **6** | **4** |

**Y no es teórico. Mutante M8a**, sobre `process_manager_view.py:196` (fuera de la red):

```python
- self._publicar_en_el_bucle(0, _handle_err)
+ self._publicar_en_el_bucle(3000, self._inventado, 1)
```

```
test_los_workers_de_pack_solo_publican_por_after : VERDE   <== no lo ve
test_ninguna_vista_programa_after_a_mano        : VERDE   <== no lo ve
```

Publicar a **3000 ms** y a un **callback inventado** pasa los dos guards. El test 205 solo exige
que no haya `self.after`; la exigencia de "0 ms + callback en lista blanca" — que es justo lo que
este ciclo añadió con la rama nueva — no llega a 4 de los 10 call sites que el ciclo migró.

### M7 · `ui/app.py:244` publica desde un hilo y es invisible para los dos guards

```python
def show_action(icon, item):          # callback de pystray: corre en SU hilo
    ...
    self.root.after(0, self.root.deiconify)
```

`test_ninguna_vista_programa_after_a_mano` no lo ve **por dos motivos independientes**: (1) `VISTAS`
solo abre 3 ficheros y `app.py` no está; (2) aunque lo abriera, el detector exige
`ast.Attribute(attr="after")` con `value` siendo `ast.Name("self")`, y aquí `value` es
`ast.Attribute(attr="root")`. MEDIDO: `ast` sobre `app.py` → **0 líneas marcadas**, con L244
publicando desde hilo. El alcance del guard está documentado (`run_tests.py:8783`), pero ese
docstring enumera *"el toast de arranque y el hilo del icono de la bandeja"* y `app.py` tiene **5**
`threading.Thread`, dos de los cuales son los de los favoritos.

### D1 · `README.md` dice dos cifras distintas

`README.md:63` → `python run_tests.py  # 205 tests headless`. `README.md:6` → badge
`tests-203%20verdes`. `validate_docs.py` no lo caza porque su regex
(`run_tests\.py\s*#\s*(\d+)\s+tests`) solo mira la línea de comando, no el badge.

### D2 · `ui-design-system.md` se contradice sobre `self.after` en el worker

L181 declara **`self.after` a mano PROHIBIDO en `ui/views/`**, pero L447, L477, L478, L483 y L488
siguen documentando `self.after(0, ...)` como el patrón de publicación del worker, con ejemplos
literales. El ciclo barrió la sección del contrato y no los ejemplos.

### Trampa de mantenimiento (no es un bug hoy): los docstrings nombran lo que el guard prohíbe

`tk_thread.py` **menciona en prosa** `psutil`, `json`, `woptimizer.services` y `winfo_exists`
— los cuatro términos que `test_ninguna_vista_programa_after_a_mano` prohíbe. MEDIDO: una búsqueda
por subcadena da 4 falsos positivos; el guard real usa `ast` sobre `ast.Import`/`ast.ImportFrom`, así
que hoy acierta. Se deja anotado porque un guard futuro escrito con `in open(...)` daría verde con
la frontera rota.

---

## 4. Tabla fix → mutación → veredicto → motivo

Todas las filas son ejecuciones de **`python run_tests.py` completo** sobre una cámara propia con
el historial real, entorno limpio. Línea base en esa misma cámara: `ALL TESTS PASSED.`, rc=0,
25 831 B. Un veredicto solo existe si el log termina en `ALL TESTS PASSED.` o trae traceback; todos
los logs se leyeron por **tamaño y última línea** antes de aceptarlos.

| id | qué se rompió | veredicto | motivo literal |
|---|---|---|---|
| **S1** | el `try/except RuntimeError` desaparece de `publicar_en_bucle` | **killed** ⚠ | `RuntimeError: main thread is not in main loop` — **muere por excepción propagada, no por aserción** |
| **S2** | `except Exception` → `except BaseException` | **survived** | `ALL TESTS PASSED.` (25 977 B). Mutante **equivalente**: para `RuntimeError` no cambia nada |
| **S3** | `except Exception` → `except RuntimeError` | **survived** | `ALL TESTS PASSED.` (25 977 B). Lo único que distingue es `tk.TclError`, que **el docstring declara y ningún test provoca** |
| **A1** | el helper devuelve `None` sin llamar nunca a `after` | **killed** | `AssertionError: el estado nunca se publico: el hilo secundario tiene que entregarlo por un self.after(0, ...) que se ejecute en el principal (FIX-007)` |
| **A2a** | la puerta vuelve a la puerta vieja: `self.after` directo en `confirmation.py` | **SURVIVED** 🔴 | `ALL TESTS PASSED.` (25 977 B). **Ningún test lo ve** |
| **A2b** | la puerta devuelve siempre `None` | **killed** | `AssertionError: el estado nunca se publico... (FIX-007)` |
| **T1a** | la puerta nueva se degrada a par en `PERMITIDOS` (sin 0 ms ni whitelist) | **killed** | `AssertionError: no ve 'self._publicar_en_el_bucle(3000, ...)': ['CONTROL-PUBLICADOR:L2 pasa self._show_banner como argumento de una llamada permitida', ...]` |
| **T1b** | el requisito de 0 ms se invierte (`== 0` → `!= 0`) | **killed** | `AssertionError: el detector marca de mas: un worker que solo publica por self.after(0, ...) es conforme` |
| **T1c** | la lista blanca se invierte (`not in` → `in`) | **killed** | `AssertionError: el detector marca de mas: un worker que solo publica por self.after(0, ...) es conforme` |
| **T1d** | la puerta nueva cae como "cualquier otra cosa" y no se verifica | **killed** | `AssertionError: no ve 'self._publicar_en_el_bucle(3000, ...)': ['CONTROL-PUBLICADOR:L2 self._publicar_en_el_bucle(...) desde el hilo secundario', ...]` |
| **D1a** | el detector no ve **ningún** `self.after` | **killed** | `AssertionError: la deteccion no ve 'self.after(0, ...)': este guard no mira nada y dejaria volver la deuda sin enterarse` |
| **D1b** | el guard no abre **ningún** fichero de vista (`VISTAS = ()`) | **SURVIVED** 🔴 | `ALL TESTS PASSED.` (25 977 B). **La contraprueba no salva de esta** |
| **D1c** | la deuda vuelve: un worker vuelve a `self.after` a mano | **killed** | `AssertionError: las vistas publican por 'self._publicar_en_el_bucle(0, ...)' (TASK-073), nunca por 'self.after' a mano; este call site vuelve a la puerta de atrás: ['process_manager_view.py:211']` |
| **F1** | `tk_thread.py` importa `psutil` | **killed** ⚠ | `NameError: name 'proibido_tk' is not defined` — **typo del propio test**, no la aserción (ver §3, hallazgo **F**) |
| **F1b** | `tk_thread.py` importa de `woptimizer.services` | **killed** ⚠ | `NameError: name 'proibido_tk' is not defined` — mismo typo |
| **T2** | vuelve el probe `winfo_exists()` en el helper | **killed** | `AssertionError: el estado nunca se publico... (FIX-007)` — **muere en el test de integración, 18 s antes de llegar al caso D** |
| **X1** | el caso A pasa a medir "se intentó y falló" (`registrar_antes=True`) | **killed** | `AssertionError: una vista muerta no puede dejar NADA programado...` — **con el código de producción SIN tocar** |
| **X2** | el `except` devuelve `0` en vez de `None` | **killed** | `AssertionError: sin bucle principal la programacion falla y no hay handle: 0` |
| **M8a** | un call site **fuera** de la red publica a 3000 ms y a un callback inventado | **SURVIVED** 🔴 | los **dos** guards en verde (ver §3, hallazgo **M8**) |

⚠ = muere, pero **no por la aserción que dice comprobar**. Un test que muere por el motivo
equivocado no discrimina: hay que decirlo.

**Recuento: 19 mutantes · 14 killed · 5 survived** (2 equivalentes, 3 sin cobertura real).

### 4.1 · Tres cosas que hay que saber de los "killed"

- **S1 muere por excepción propagada, no por `AssertionError`.** El caso A llama a
  `publicar_en_bucle` con un doble que lanza; sin guard, el `RuntimeError` sube y tumba la suite.
  El test **sí detecta** el defecto (que es "no propaga"), pero la línea que muere no es la que el
  docstring del test describe. Si alguien wants que la garantía se compruebe por aserción, hace
  falta un `pytest.raises`-al revés / `try` explícito alrededor de la llamada.
- **A1, A2b y T2 mueren por un test que este ciclo no escribió** (`FIX-007`, integración con hilo
  real), **no por los casos B/E/D del test 204**. El caso D que el encargo señala como el que mata
  la sonda nunca llega a ejecutarse: la sonda con `winfo_exists()` hace que el callback no se
  agende y el test de integración revienta 18 s antes. **El caso D no es lo que mide lo que dice
  medir.**
- **T1a muere por efecto colateral, no por la comprobación de 0 ms.** Al meter el par en
  `PERMITIDOS`, la rama de "argumento de una llamada permitida" marca `self._show_banner` y
  `self._inventado`, y el control 9 ve 2 infracciones — pero por el motivo equivocado. La degradación
  se detecta; la aserción que dice "no ve el 3000 ms" no es la que salta.

---

## 5. Supervivientes, por severidad

Distinguidos por lo que significan, porque no son lo mismo: *mutante equivalente* = el código no
está mal, la prueba no lo distingue y no debería. *Sin cobertura* = el código **puede** estar mal y
nadie se entera.

### SV1 · ALTA · `A2a` · La puerta de las vistas puede volver a la puerta vieja sin que nadie lo note

`Confirmable._publicar_en_el_bucle` reescrito como `try: return self.after(...) except: return None`
— o sea, la deuda que este ciclo vino a cerrar, reintroducida en el mixin — deja la suite **verde**.

**Por qué no lo ve nadie:**
- el caso E del test 204 usa un doble **vivo**, donde `self.after` directo funciona idéntico a la
  delegación, así que la aserción no puede distinguirlos;
- `test_ninguna_vista_programa_after_a_mano` abre **3 ficheros de `views/`**, y la puerta vive en
  `ui/confirmation.py`, que no está en la lista.

**Arreglo:** el caso E necesita un doble **muerto** (que `after` levante) para separar delegación de
reimplementación; y el guard de la frontera de `confirmation.py` (`test_double_tap_guard`) debería
mirar también que `_publicar_en_el_bucle` **no llama a `self.after`**.

### SV2 · ALTA · `D1b` · El guard anti-regresión puede no abrir ningún fichero y sigue verde

`VISTAS = ()` — el guard de "ninguna vista programa `after` a mano" se queda **sin observar nada** y
la suite termina en `ALL TESTS PASSED.`

**Esto es exactamente el fallo que el propio test dice evitar**, y que el ciclo cita como
justificación para añadir la contraprueba: `test_ninguna_llamada_de_cat_file_batch_check_se_queda_sin_input`,
donde la detección existía, no veía, y `for argumento in []` dejaba todo en verde
(`docs/ai/testing-guide.md:1293`).

**Lo que sí funciona:** la contraprueba (`D1a`) mata al detector ciego. Lo que **no** cubre es al
guard que deja de mirar. La contraprueba prueba que el *detector* funciona; no prueba que se le
*pidan* ficheros.

**Arreglo:** el guard tiene que **exigir que se abrieron los 3 ficheros**
(`assert len(vistos) == 3` sobre una lista acumulada, hoy descartada), igual que el caso C del test
204 exige `len(...) == 1` y no dos.

### SV3 · ALTA · `M8a` · La rama nueva del guard AST no llega a 4 de los 10 call sites migrados

Detallado en §3 (M8). `self._publicar_en_el_bucle(3000, self._inventado, 1)` en
`process_manager_view.py:196` pasa **los dos** guards en verde.

**Arreglo:** o se amplían los 5 métodos de la lista del guard a los workers que realmente publican
(los de `dashboard_view` con `_on_restore_finished`, y los de carga de `process_manager_view`), o el
test 205 —que hoy solo exige "no haya `self.after`"— se le exige también 0 ms y lista blanca.

### SV4 · BAJA · `S3` · `tk.TclError` está en el docstring y en ningún test

`except Exception` → `except RuntimeError` sobrevive. La diferencia entre ambos es exactamente
`tk.TclError`, que `tk_thread.py:53` declara como **la segunda razón** del `except` (*"si la vista
murió entre la decisión y la llamada"*). Ningún test lanza un `TclError`; el doble `_VistaFalsa` solo
sabe lanzar `RuntimeError`.

**Arreglo:** un caso más en el test 204 con un doble que lance `tk.TclError`. Cuesta tres líneas y
convierte una afirmación del docstring en algo verificado.

### SV5 · NINGUNA · `S2` · Mutante equivalente

`except Exception` → `except BaseException` sobrevive, y **debe** sobrevivir: para el `RuntimeError`
que el guard trata no hay diferencia. El código de producción tiene `except Exception`, que es lo
correcto. Se registra solo para que conste que se midió.

---

## 6. Hallazgo fino · la aserción que el encargo llama "LA QUE DISCRIMINA" es tautológica

`proposal.md` ("Criterio discriminante del test") y el docstring del test 204 sostienen que

```python
assert muerta.llamadas == []      # <-- LA ASERCIÓN QUE DISCRIMINA
```

es la línea que separa **"programó"** de **"se tragó"**. **MEDIDO (mutante X1):** cambiando solo el
doble del caso A a `_VistaFalsa(revienta=True, registrar_antes=True)` — **sin tocar una línea de
producción** — esa aserción **falla**:

```
AssertionError: una vista muerta no puede dejar NADA programado, y la lista de llamadas es lo que
lo demuestra: [(0, <function _cb at 0x...DADDD631A0>, (1, 2))]
```

Porque `_VistaFalsa.after` lanza **antes** de registrar cuando `registrar_antes=False`: `llamadas`
queda vacía **con guard y sin guard**. La línea mide **el doble**, no el guard.

**Lo que NO se rompe:** el conjunto del test sí discrimina. S1 muere por propagación y A1 muere en
el caso B. Lo que no se sostiene es la frase: `llamadas == []` no separa "programó" de "se tragó",
porque la información de si se intentó la lleva el otro caso (el C, con `registrar_antes=True`).

**Arreglo:** o el caso A usa `registrar_antes=True` y la aserción pasa a exigir 0 entradas con el
código correcto, o el docstring deja de llamarla "la aserción que discrimina".

---

## 7. Veredicto

# VERDICT: FAIL

**Por qué:** sobreviven **tres mutantes sin cobertura** — **SV1** (`A2a`, la puerta puede volver a
`self.after` sin que nadie lo note), **SV2** (`D1b`, el guard anti-regresión puede no mirar ningún
fichero) y **SV3** (`M8a`, la rama nueva del guard no llega a 4 de los 10 call sites que el ciclo
migró). Los tres son huecos de **verificación**, no de código: el código de producción de este
ciclo es correcto en todo lo que se pudo medir, pero tres de sus garantías **no están guardadas**.

**Lo que sí está bien y merece decirse:** el test 204 tiene contraprueba real y matan A1, A2b y X2;
el control 9 de `test_los_workers_de_pack_solo_publican_por_after` mata las cuatro degradaciones de
la rama nueva (T1a–T1d); la contraprueba del detector mata al detector ciego (D1a); y el guard
anti-regresión detecta la deuda cuando vuelve (D1c). **Esto no es el fallo de un ciclo flojo: es
un ciclo con buenos tests y tres huecos puntuales, todos con nombre.**

### Tickets que deja este informe

| ticket | severidad | qué hay que hacer |
|---|---|---|
| **SV1** | alta | caso E del test 204 con doble **muerto**; y `test_double_tap_guard` que prohíba `self.after` dentro de `_publicar_en_el_bucle` |
| **SV2** | alta | el guard de `test_ninguna_vista_programa_after_a_mano` tiene que **exigir que abrió los 3 ficheros**, no solo que el detector funciona |
| **SV3** | alta | ampliar la red del guard AST a los 4 call sites fuera, o endurecer el test 205 con 0 ms + whitelist |
| **SV4** | baja | un caso con `tk.TclError` en el test 204, para que la segunda razón del `except` sea verificada |
| **F** | media | `run_tests.py:25543`: `proibido_tk` → `prohibido_tk` |
| **D1** | media | corregir `ui/tk_thread.py:12-18` y `ui-design-system.md:185`: el `RuntimeError` es del mundo **sin bucle principal**, no "también con la ventana viva" |
| **D2** | baja | `ui-design-system.md` L447-491 sigue documentando `self.after(0, ...)` como patrón del worker, contradiciendo L181 |
| **D1b** | baja | `README.md:6`: el badge dice 203 y el texto L63 dice 205 |
| **M7** | baja | `ui/app.py:244` publica desde el hilo de pystray y es invisible para los dos guards; el docstring de `run_tests.py:8783` enumera 2 de los 5 `threading.Thread` |

### Estado final del entorno

- **Cámara base `%TEMP%\wopt_audit_62\base_v3`: verde** (`ALL TESTS PASSED.`, rc=0).
- Las 19 cámaras de mutante son desechables por diseño (una por mutante, clonadas de la base).
- **Repositorio real: intacto.** HEAD `bbcc472`, reflog sin entradas nuevas, `git diff` y
  `git diff --cached` vacíos. El único cambio en el árbol es
  `openspec/changes/2026-10-18-tkinter-after-guard/mutation-report.md`, **sin comitear**, que es el
  único fichero que este rol puede escribir.
- **No se reparó nada** de `src/` ni de `run_tests.py`. Reparar es de `openspec-dev`.

---

# 8. Reparación en TASK-078 (rol `openspec-dev`)

**Veredicto de partida que este rol da por bueno, verificado por separado:** el código de producción
de este ciclo es correcto en todo lo medible. Los tres supervivientes sin cobertura eran huecos de
**guard**, no de implementación. Por eso aquí no se rediseña nada: se reparan las pruebas.

Cámara de medición: copia desechable en `%TEMP%\wopt_task78\camara` con `run_tests.py`, `src/` y
`assets/` del repo real, línea base verde medida antes de mutar nada. Cada sonda se ejecuta con el
`run_tests.py` de la cámara y su propio `src/`.

## 8.1 · SV1 · `A2a` — la puerta puede volver a la puerta vieja

**Por qué no lo ve nadie (medido en el informe):** el caso E usaba un doble **vivo**, donde delegar y
reimplementar dan el mismo handle y la misma llamada registrada, y `test_ninguna_vista_programa_after_a_mano`
abría solo `views/`, dejando el mixin `confirmation.py` —donde vive la puerta— sin vigilar.

**Arreglo, las dos mitades:**

1. `run_tests.py::test_ninguna_vista_programa_after_a_mano` abre ahora **cuatro** ficheros (las tres
   vistas más `ui/confirmation.py`) y comprueba **por nombre de método** que
   `Confirmable._publicar_en_el_bucle` no llama a `self.after`, con contraprueba de que el mismo
   detector baja a los cuerpos de los métodos. `tk_thread.py` se sigue mirando **leyéndolo**, nunca
   importándolo: `test_double_tap_guard` (prohíbe cualquier `woptimizer.*` en `confirmation.py`)
   queda intacto.
2. El caso E del test 204 usa un doble que **registra de dónde se llamó al `after`** (`sys._getframe`),
   con contraprueba del propio predicado (el mismo doble, llamado directo desde el test, no registra
   la delegación) y con un segundo caso de la vista **muerta**, que es el que exige que la puerta siga
   pasando por la función pura.

**La frase que ahora hace morir a `A2a`:**

> la puerta tiene que **DELEGAR** en `ui/tk_thread.py::publicar_en_bucle` y no programar por su cuenta:
> el `after` lo llamo `[('run_tests.py', 'after'), ('run_tests.py', 'after'),
> ('confirmation.py', '_publicar_en_el_bucle'), ...]` — **MUEVE, por aserción, en los DOS guards.**

## 8.2 · SV2 · `D1b` — el guard puede dejar de mirar cualquier fichero

**Arreglo:** el guard exige ahora **las dos cosas**: que su conjunto de ficheros vigilados tenga el
tamaño declarado y que sea **exactamente** el declarado (`ESPERADOS`, escrito aparte del diccionario,
para que los dos no se deriven uno del otro), y que **ninguna vista del disco quede fuera** (el
conjunto se deriva con `glob` de `views/*.py` y se compara). La contraprueba del detector sigue ahí
—sigue probando que el detector **detecta**—, pero ya no es lo único que prueba el guard.

**La frase que ahora hace morir a `D1b`:**

> el guard tiene que abrir los cuatro ficheros vigilados y ha abierto `[]`: con la lista vacía o
> incompleta, todo lo que este test afirme se cumple sobre **cero ficheros**.

## 8.3 · SV3 · `M8a` — la rama nueva no llegaba a 4 de los 10 call sites

**Arreglo (sin tocar producción):** la tupla de cinco métodos escrita a mano desaparece. El inventario
recorre **las clases enteras** de las tres vistas y suma (a) el objetivo real de cada
`threading.Thread(target=...)` y (b) los **callbacks que un servicio ejecuta en hilo secundario**
(`load_db_async(callback=…, on_error=…)`, que corren dentro del `Thread` del propio servicio). Los
callbacks pagan **solo** la regla de la puerta (0 ms + callback conocido): su cuerpo corre ya en el
hilo principal cuando toca widgets, que es justo lo que hacen, y aplicarles la invariante del worker
declararía infracción a `_handle_err` por escribir en `status_label`.

Cierre del hueco: el guard **cuenta por separado** las publicaciones que hay en los tres ficheros
(`contados_en_codigo`) y exige que coincidan con las que ha visto en su inventario. MEDIDO en verde:
**10 cuerpos de hilo secundario, 10 publicaciones vigiladas** (7 `Thread` + 3 callbacks), y el
recuento independiente dice 10.

Dos entradas de listas que esta amplitud obliga a **declarar**, no a tolerar: el par
`("gaming_service", "restore_gaming_session")` (el worker de `_on_restore_clicked` entra solo con el
inventario exhaustivo) y los nombres `_handle_err` / `_handle_ok` en la lista blanca de callbacks (las
dos clausuras locales que los callbacks de `load_db_async` publican al principal). **La puerta NO se
metió en `PERMITIDOS`**: degradarla sería el arreglo de una línea que devuelve el guard al-hole en
forma de par sin 0 ms ni lista blanca, que es la degradación que este ciclo vino a cerrar.

**La frase que ahora hace morir a `M8a`:**

> el callback que el servicio ejecuta en un hilo secundario publica fuera de la puerta:
> `ProcessManagerView._force_update_db:L196 self._publicar_en_el_bucle debe ser de 0 ms`.

## 8.4 · Los "killed" que morían por el motivo equivocado

| id | antes | ahora |
|---|---|---|
| **S1** | moría por `RuntimeError` propagada, no por aserción | el caso A envuelve la llamada y convierte la propagación en `AssertionError` con el defecto escrito: "la puerta tiene que tragarse el `RuntimeError` del hilo sin bucle principal, no propagarlo al worker" |
| **F1/F1b** | morían por `NameError` (`proibido_tk` en el mensaje, `run_tests.py:25543`) | el nombre es el correcto; el rojo dice "ui/tk_thread.py viola la frontera de capas: importa `['psutil']`" y muere por `AssertionError` |

## 8.5 · Mutantes EQUIVALENTES: se documentan, no se "arreglan"

- **S2** (`except Exception` → `except BaseException`) y **S3** (`except Exception` →
  `except RuntimeError`): sobreviven y **deben** sobrevivir para el `RuntimeError` que el guard trata.
  La diferencia entre ambos es `tk.TclError`, que el docstring de `publicar_en_bucle` declara como
  segunda razón del `except` y que ningún test provoca. Cambiar el código para matar S3 sería tocar
  producción para tapar una falta de prueba: la nota queda escrita en el propio docstring, que ahora
  dice esto mismo. **Siguen vivos a propósito.**

## 8.6 · La aserción que el informe llama "LA QUE DISCRIMINA"

`assert muerta.llamadas == []` (caso A del test 204) **es tautológica** —mutante X1: falla con
producción sin tocar—, y el mensaje lo dice ahora en la propia aserción: mide **al doble** (que Tcl no
llegara a agendar nada), no al guard. Lo que discrimina el guard en ese caso es `handle is None`, y el
`try` explícito de TASK-078 hace que la ausencia del `except` muera por `AssertionError` y no por
propagación.

## 8.7 · Documentación corregida (lo que la auditoría refutó, no maquillado)

| sitio | qué decía | qué dice ahora |
|---|---|---|
| `ui/tk_thread.py:11-37` y `docs/ai/ui-design-system.md:185` | `winfo_exists()` lanza "**incluso con la ventana perfectamente viva**" | el `RuntimeError` ocurre en el mundo **sin bucle principal**; con `mainloop()` vivo devuelve `1` con la vista viva y `0` con el widget destruido, sin lanzar. El probe **sigue sin ser la solución**, y ahora se dice por qué, con las tres razones medidas |
| `docs/ai/architecture.md:36` (motivo (b)) | la misma afirmación falsa | la misma corrección, y se marca como corrección de TASK-078 |
| `docs/ai/ui-design-system.md:188` | "los **cuatro** de la vista de procesos que no son `threading.Thread`" | son **tres** (`process_manager_view.py:181`, `:196`, `:204`); el reparto 7+3 se exige ahora en el guard |
| `docs/ai/ui-design-system.md:105,447,477-478,483,488` | ejemplos que seguían documentando `self.after(0, …)` como patrón del worker (D2) | los ejemplos usan `self._publicar_en_el_bucle(0, …)`, que es lo que hace el código |
| `docs/ai/ui-design-system.md` §límites | "los `threading.Thread` de `ui/app.py` (el toast y el icono de la bandeja)" | **`ui/app.py:244` es una EXCEPCIÓN CONSCIENTE, decidida en TASK-078**, con sus dos motivos y con el dato medido de que ese fichero tiene **cinco** `threading.Thread`, no dos |
| `README.md:6` | badge `tests-203 verdes` frente a `205` en la línea 63 | badge `tests-205 verdes` |
| `docs/ai/testing-guide.md` filas 76, 204 y 205 | el alcance viejo (cinco métodos, tres ficheros, `llamadas == []` como discriminante) | el alcance nuevo, con el mutante que cada mitad mata |

**Deuda que NO se toca aquí** (fichero del arquitecto, no de este rol):
`openspec/changes/2026-10-18-tkinter-after-guard/proposal.md:28` y `:144` y `tasks.md:24` siguen
repitiendo la medición falsa de `winfo_exists()` y la frase "LA ASERCIÓN QUE DISCRIMINA" sobre
`llamadas == []`. Queda anotado aquí para que el arquitecto lo corrija al archivar el change.

## 8.8 · Verificación ejecutada en la reparación

Los tres comandos, en verde, con `run_tests.py` terminando en `ALL TESTS PASSED.` y el log leído por
tamaño y última línea (no truncado: 26 404 B, y el proceso salió con `rc=0`):

```
> python verify_ui_syntax.py
Validando sintaxis estatica de la Fase 3...
OK: src/woptimizer/ui/app.py compila perfectamente.
...
OK: src/woptimizer/__main__.py compila perfectamente.
EXITO: Todos los modulos UI estan impecables.
rc=0

> python run_tests.py
La accion por defecto, y las apps de un pack, SE PERSISTEN de verdad (TASK-062).
--- Running Backend Tests ---
Testing models...
...
Testing that no view calls self.after by hand (TASK-073)...
test_ninguna_vista_programa_after_a_mano OK.

ALL TESTS PASSED.
rc=0

> python validate_docs.py
============================================================
 validate_docs.py - woptimizer SDD + llms.txt
============================================================
...
  [OK]   docs/ai/data-models.md: declara el contrato de persistencia (...) en una sola unidad de texto
Resumen: 143 OK, 0 FAIL
rc=0
```

Reparto de la suite sin cambios: **205 definidos / 205 invocados / 0 huérfanos**, **142 backend +
63 headless**, derivado con `ast` por el check 7 de `validate_docs.py` (esta reparación **no añade
tests**: extiende tres sondas que ya existían, que es lo que mantiene el recuento y las filas de la
tabla de `testing-guide.md` sin renumerar).

Un efeito secundario que salió al ejecutar y que también es deuda de este ciclo: tocar
`docs/ai/ui-design-system.md` desincroniza `llms-full.txt`, y un test que valida un árbol sintético
(`test_el_journal_ilegible_informa_en_vez_de_reventar_el_validador`) cuenta **un error de más** por
esa desincronización y se pone en rojo. Se arregla con `python build_llms_full.py --write`, que es
el que regenera el agregado; el fichero regenerado va en este mismo commit.