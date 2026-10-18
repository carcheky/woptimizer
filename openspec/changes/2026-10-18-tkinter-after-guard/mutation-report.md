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

---

# 9. Re-auditoría (TASK-078) · rol `mutation-auditor`

**Ancla del repo real:** `b326031` ("fix(tests): cerrar los tres huecos de verificacion de
TASK-073 (TASK-078)"). Cámara base `%TEMP%\wopt_audit_62_rea`: **clon con el historial real**
(`git clone --local --no-hardlinks`), HEAD `b326031`.

**Pregunta:** los tres huecos de §5 (SV1, SV2, SV3) y el typo `F` de §3, ¿están **realmente**
cerrados? No se lee el mensaje del dev como prueba: se muta.

## 9.0 · Protocolo, línea base y las tres trampas que casi me cuelan un veredicto falso

**Línea base, medida ANTES de mutar nada:** `python run_tests.py` en la cámara base →
**`ALL TESTS PASSED.`**, 364 líneas, **26 404 B**, rc=0. Con la línea en `test_los_workers...`:
`guarda AST exhaustiva: 10 cuerpos de hilo secundario, 10 publicaciones vigiladas` — la cifra
que el dev declara, **medida sobre el código y no leída**.

`.taskmaster/git_safe_commit.py` **NO se invocó ni una vez**. Todo el versionado de cámaras fue
`git` a pelo contra clones desechables. El repo real, al cierre:

```
git log --oneline -1   -> b326031
git reflog -3          -> b326031 / bbcc472 / df294dc   (sin entradas nuevas; 288 en total)
git status --porcelain -> (0 líneas)
git diff --stat        -> (vacío)     git diff --cached --stat -> (vacío)
git rev-parse --git-dir -> C:/Users/carch/AppData/Local/woptimizer_git/.git
```

Aislamiento probado en las tres direcciones antes de mutar: con `GIT_DIR` explícito de la cámara
resuelve a la cámara; con descubrimiento resuelve a `.git` **de la cámara** (nunca a
`%LOCALAPPDATA%`); el repo real sigue apuntando a `%LOCALAPPDATA%`.

### Trampa T1 (mía) · un `ALL TESTS PASSED.` de una cámara que **nunca se mutó**

`R3_M8a` en su **primera** pasada terminó en `ALL TESTS PASSED.` (rc=0, 26 250 B) y lo registré
como veredicto antes de mirar el fichero. **No valía nada**: la cámara tenía la línea intacta.
Causa: el patrón de sustitución del arnés indentaba la línea con **16 espacios** y la real lleva
**12** (`process_manager_view.py:196`); el sustituto no apareció, el script abortó con `SystemExit`
**antes de escribir**, y la cámara se quedó limpia. Un clon limpio da verde, como da verde la base.

**Arreglo aplicado:** (a) el arnés sustituye y **verifica en disco** cada mutación; (b) una
comprobación posterior independiente (`_verificar_mutaciones.py`) relee los 17 ficheros mutados y
comprueba, porPresence/ausencia, que la mutación está donde debe: **17/17 OK**. Sin esa
comprobación, la primera pasada de `R3` habría reportado "supervive" un mutante que no existía —
y `R3` es **justo** el mutante que el encargo más。重点 pedía medir.

### Trampa T2 (mía) · un rojo del arnés leído como veredicto

`R1_A2a` murió en `test_el_pre_vuelo_de_un_hash_muerto_distingue_existe_de_no_existe`
(`run_tests.py:21538`), que es una prueba de **git**, y **38 líneas antes** de los guards que
miden el mutante. `confirmation.py` no participa en ese test. Sospecha: 14 procesos `git`
simultáneos. **Medido:** ejecutado **aislado** en la misma cámara mutada, ese test pasa en
**1 s** (`rc=0`, `AISLADO-OK`). Es el mismo modo de fallo que **H1** de §0: saturación del arnés
en un test ajeno al mutante. R1 se **relanzó** y su veredicto válido es el de la segunda pasada.

### Trampa T3 (mía) · un mutante que muere por un guard **distinto** del que dice medir

`R3` y `R5b`, tal como los escribí primero, **no midieron lo que creo que medían**. Ambos
terminaron en `AssertionError`, pero el traceback apuntaba a
`test_dead_code_ast_guard` (TASK-056, `run_tests.py:26053`), **no** al guard de TASK-073 (que se
invoca en `:26363`, 310 líneas después). El motivo: al **renombrar o sustituir** la única
referencia a `_handle_err`, el closure quedaba **sin ninguna referencia**, y el guard de código
muerto (que corre ANTES) saltaba primero:

```
File "...run_tests.py", line 26053, in <module>
  test_dead_code_ast_guard()
AssertionError: Se detectaron 1 funciones/metodos sin ninguna referencia...
  - src\woptimizer\ui\views\process_manager_view.py:193 -> _handle_err
```

Un guard de código muerto puede **matar mutantes que el guard de TASK-073 no vería**, y al revés.
Un `AssertionError` sin mirar **de qué aserción** viene no es un veredicto: es una coincidencia.

**Arreglo aplicado:** `R3b`/`R3c` y `R5b2` **no dejan código muerto** (la mutación no toca el
nombre de ningún closure: o cambian el delay de una línea que ya existe, o **añaden** una
publicación sin alterar ninguna referencia), y así el único rojo posible es el del guard de
TASK-073. **R3c** (delay 3000 sobre la línea existente) mata por la aserción que dice, con el
call site nombrado; **R3b** (publicación añadida) mata por el **recuento de 10**, que es otro
discriminante legítimo pero **otro**: por esomake falta R3c para medir lo que el encargo pedía.
La primera versión de `R3` y de `R5b` queda **descartada como NO MEDIDA**, no como "killed".

### Trampa T4 (de producción, no mía) · `test_dead_code_ast_guard` corre antes que el guard de TASK-073

Lo anterior no es solo un descuido de arnés: es un hecho del **orden de la suite**. Los guards de
TASK-073 son los **dos últimos** que se invocan (`:26363` y `:26364`, justo antes de
`print("ALL TESTS PASSED.")`), y `test_dead_code_ast_guard` va en `:26053`. Consecuencia medible:
**cualquier mutación de TASK-073 que tocó el nombre de un closure queda tapada por el guard de
código muerto**, y quien solo lea "rc=1" concluirá que el guard de TASK-073 detectó el defecto.
Vale lo mismo al revés: un guard que murió por el motivo equivocado no discrimina. Es la misma
regla que §3 (F) estableció para el `NameError`, aplicada ahora a un segundo guard.

## 9.1 · Mutantes re-auditados: veredicto y motivo LITERAL

Todos: `python run_tests.py` **completo** en cámara propia clonada con historial, entorno limpio.
Línea base de la misma cámara: `ALL TESTS PASSED.`, 26 404 B, rc=0. Cada log leído por **tamaño y
última línea** antes de aceptar veredicto, y cada cámara **verificada mutada en disco** después.

| id | qué se rompió | veredicto | motivo literal |
|---|---|---|---|
| **R1 / A2a** | la puerta vuelve a `self.after` directo en `confirmation.py:321` | **killed** | `AssertionError: la puerta tiene que DELEGAR en ui/tk_thread.py::publicar_en_bucle y no programar por su cuenta: el after lo llamo [[('run_tests.py','after'), ('run_tests.py','after'), ('confirmation.py','_publicar_en_el_bucle'), ...]]. Un self.after aqui, aunque se trague la excepcion, es exactamente la deuda que TASK-073 cerro` |
| **R2a** | `ESPERADOS = ()` | **killed** | `AssertionError: el guard tiene que abrir los cuatro ficheros vigilados y ha abierto ['confirmation.py','dashboard_view.py','pack_manager_view.py','process_manager_view.py']: con la lista vacia o incompleta, todo lo que este test afirme se cumple sobre cero ficheros` |
| **R2b** | se borra el bloque `glob` que deriva `views/*.py` | **SURVIVED** 🔴 | `ALL TESTS PASSED.` (26 250 B) |
| **R2c** | `ESPERADOS` con una entrada cambiada por otra | **killed** | el mismo `AssertionError` que R2a, con los cuatro ficheros abiertos |
| **R3b** | `M8a` **añadido** (sin tocar la línea buena): una publicación extra a 3000 ms con callback inventado | **killed** | `AssertionError: las tres vistas tienen 11 publicaciones a una puerta autorizada y el invariante de TASK-073 habla de 10 call sites migrados...` — **por el RECUENTO, no por la regla de la puerta** (de ahí que hiciera falta R3c) |
| **R3c** | `M8a` **faithful**: `(0, _handle_err)` → `(3000, _handle_err)` en la línea que ya existe, sin añadir ni quitar publicaciones | **killed** | `AssertionError: el callback que el servicio ejecuta en un hilo secundario publica fuera de la puerta: ProcessManagerView._force_update_db:L196 self._publicar_en_el_bucle debe ser de 0 ms` |
| **R4a** | `tk_thread.py` importa `psutil` | **killed** | `AssertionError: ui/tk_thread.py viola la frontera de capas: importa ['psutil']. La logica de publicar en el bucle es UI pura...` |
| **R4b** | `tk_thread.py` importa `from woptimizer.services import process_service` | **SURVIVED** 🔴 | `ALL TESTS PASSED.` (26 250 B) |
| **R5a** | `_handle_err`/`_handle_ok` fuera de la lista blanca | **killed** | `AssertionError: el callback que el servicio ejecuta en un hilo secundario publica fuera de la puerta: ProcessManagerView._force_update_db:L204 self._publicar_en_el_bucle publica en _handle_ok, y tiene que publicar en ['_apply_load', '_do_load', '_inline_status', '_on_restore_finished', '_publicar_cierre', '_show_banner', '_show_start_banner']` |
| **R5b2** | un callback **local que ya existe** y **no** está en la lista (`_on_success`), añadido sin tocar la línea buena | **killed** | `AssertionError: las tres vistas tienen 11 publicaciones...` — **por el RECUENTO**, no por la lista blanca (y la lista blanca la mata `R5a`, ver nota) |
| **R5c** | fuera el par `("gaming_service","restore_gaming_session")` de `PERMITIDOS` | **killed** | `AssertionError: el worker toca la vista fuera de self.after(0, ...): DashboardView._on_restore_clicked:L282 self.gaming_service.restore_gaming_session(...) desde el hilo secundario` |
| **R5d** | el worker usa **otro** método de `gaming_service` (`purgar_todo_el_juego`) | **killed** | `AssertionError: el worker toca la vista fuera de self.after(0, ...): DashboardView._on_restore_clicked:L282 self.gaming_service.purgar_todo_el_juego(...) desde el hilo secundario` |
| **R5e** | se **borra** una publicación legítima (`callback=lambda: self._do_load()`) | **killed** | `AssertionError: las tres vistas tienen 9 publicaciones a una puerta autorizada y el invariante de TASK-073 habla de 10 call sites migrados. O se movio una publicacion, o esta cifra esta desfasada: decidalo explicitamente en vez de dejar que el guard se adapte solo` |
| **R5f** | un callback de `load_db_async` **toca `status_label`** desde el hilo secundario | **SURVIVED** 🔴 | `ALL TESTS PASSED.` (26 251 B) |
| **R6 / S2** | `except Exception` → `except BaseException` | **survived** | `ALL TESTS PASSED.` (26 400 B). Equivalente, como dice §8.5 |
| **R6 / S3** | `except Exception` → `except RuntimeError` | **survived** | `ALL TESTS PASSED.` (26 400 B). Equivalente, como dice §8.5 |

**Recuento: 17 mutantes medidos · 12 killed · 5 survived** (2 equivalentes declarados, **3 sin
cobertura real**: R2b, R4b, R5f). Más **3 NO MEDIDOS** descartados por arnés (la primera versión de
`R3` y de `R5b`, y la primera pasada de `R1`), explicados en §9.0.

**Los tres huecos del encargo, uno a uno:**

| hueco | mutante | veredicto | ¿cerrado? |
|---|---|---|---|
| **SV1** (la puerta vuelve a `self.after`) | R1 | **killed** | **SÍ**, y por la aserción que dice: nombra QUIÉN llamó al `after` |
| **SV2** (el guard no mira ficheros) | R2a, R2c | **killed** | **SÍ para el conjunto declarado**; **NO** para el `glob` (R2b sobrevive) |
| **SV3** (`M8a` fuera de la red) | R3c | **killed** | **SÍ**, y nombra el call site (`_force_update_db:L196 ... debe ser de 0 ms`) |
| **F** (typo `proibido_tk`) | R4a | **killed** | **SÍ**, y ahora por `AssertionError` nombrando `['psutil']` — ya no por `NameError` |

## 9.2 · Supervivientes, por severidad

### SV1' · ALTA · **R4b** · el guard de la frontera de `tk_thread.py` es ciego a los imports ABSOLUTOS

`from woptimizer.services import process_service` en `tk_thread.py` deja la suite **en verde**.

El guard calcula los importados como `nodo.module.split(".")[0]`, o sea **el primer segmento**.
Para un import absoluto con prefijo de paquete eso es `"woptimizer"`, y `"woptimizer"` **no está**
en la lista de prohibidos `{psutil, json, subprocess, services, models, customtkinter, tkinter}`.
MEDIDO sobre el detector real, línea por línea:

```
import psutil                                   -> ['psutil']      SI   MUERE
import json                                     -> ['json']        SI   MUERE
from woptimizer.services import process_service -> ['woptimizer']  NO   **SOBREVIVE**
import woptimizer.services                      -> ['woptimizer']  NO   **SOBREVIVE**
from woptimizer.models import ProcessInfo       -> ['woptimizer']  NO   **SOBREVIVE**
from woptimizer.ui import app                   -> ['woptimizer']  NO   **SOBREVIVE**
from services import process_service            -> ['services']    SI   MUERE
```

**Por qué importa más que un detalle de forma:** la lista está escrita en términos de **módulo de
primer nivel** (`services`, `models`), pero el repo escribe sus imports **absolutos con prefijo de
paquete** (`woptimizer.services`), que es exactamente como los escribe el propio `AGENTS.md` y
como los nombra el docstring de `confirmation.py` ("PROHIBIDO `psutil`, `json`, `woptimizer.services`
y `woptimizer.models`"). O sea: **el guard no vigila la forma de import que el repo usa**, y el
docstring declara una prohibición más ancha de la que el guard mide.

**Esto además invalida el "killed" que la pasada anterior dio a `F1b`.** En §4, `F1b` (importar de
`woptimizer.services`) figuró como muerto — pero moría por el `NameError` de `proibido_tk`, no por
la aserción, y ya está dicho ahí que "un test que muere por el motivo equivocado no discrimina".
Ahora que el nombre está bien, **`R4b` sobrevive**: el defecto de fondo de `F1b` **nunca estuvo
reparado**, el `NameError` solo tapaba el agujero. Reparar el `NameError` (R4a) fue necesario pero
no suficiente.

**Arreglo:** la lista de prohibidos tiene que compararse contra el **módulo completo**, o
aceptar tanto `services` como `woptimizer.services` (`any(m == p or m.endswith("." + p) for p in
PROHIBIDO)`), y conviene una **contraprueba** que exija que el detector ve un
`from woptimizer.services import ...` sintético (hoy el guard solo tiene contraprueba del
`self.after`, no de su propia lista de imports).

### SV2' · ALTA · **R5f** · la ampliación abrió un agujero nuevo: los callbacks de `load_db_async` solo pagan la regla de la PUERTA, no la del WORKER

Un callback que un servicio ejecuta en hilo secundario (`load_db_async(callback=…, on_error=…)`,
que corren dentro del `Thread(target=_download)` del propio servicio — verificado en
`process_service.py:411/416`) que **toque `status_label`** deja la suite **en verde**. MEDIDO:
`ALL TESTS PASSED.`, rc=0.

**Mecanismo, del propio código del guard:** en el bucle del inventario (`run_tests.py:9392-9399`)
los callbacks se pasan por `_publicaciones_malas(...)` y en cambio los `Thread(target=…)` se pasan
por `_infracciones(...)`, que es el invariante **completo** del worker. Ampliar la red a los
callbacks era lo correcto para matar `M8a` — y el precio es que **un cuerpo que corre en el hilo
secundario ya no paga la regla de "no toques la vista"**, solo la de "publica por la puerta a
0 ms y por un callback conocido". El docstring de `_publicaciones_malas` lo justifica ("dentro de
esos cuerpos tocar widgets es lo correcto, ya están en el hilo principal"), y esa frase es la
**medición equivocada**: esos cuerpos **no** corren en el hilo principal — corren en `_download`,
el hilo del servicio; lo que corre en el principal es lo que ellos *publican*. Con el
`except Exception` de `publicar_en_bucle` tragándose el `RuntimeError`, tocar un widget ahí desde
el secundario **no es detectable ni por Tk ni por el guard**.

**Arreglo:** a los callbacks de `load_db_async` hay que exigirles **las dos** reglas: la de la
puerta **y** la del worker (o, si de verdad corren en el secundario, que no toquen widgets
directamente). Y el docstring de `_publicaciones_malas` tiene que decir que el cuerpo corre en
el secundario, no "ya en el hilo principal".

### SV3' · MEDIA · **R2b** · quitar el `glob` que deriva `views/*.py` deja todo verde

Borrar el bloque que deriva el conjunto de vistas del **directorio** (`glob views/*.py` +
comparación con `VISTAS`) deja la suite en **verde**. `R2b` sobrevive (`ALL TESTS PASSED.`).

O sea: la mitad de SV2 que el dev declara como "ninguna vista del disco queda fuera" **no está
guardada** — es una comprobación que se puede eliminar sin que nadie lo note. `R2a` y `R2c` (que
matan `ESPERADOS`) sí están guardados, porque `ESPERADOS` tiene su propio `assert len(...) == 4`;
pero la **derivación por `glob`** no tiene contraprueba: nadie mide que el guard mire el disco.

**Lo que sí es cierto y sí funciona:** mientras el `glob` esté, la `VISTA` nueva queda marcada
(`self.after` en ella). Lo que **no** tiene defensa es que el `glob` desaparezca. Agrava esto que
`R2c` (cambiar una entrada de `ESPERADOS`) mata porque el recuento y el nombre compara; pero
`R2b` (borrar la derivación) no, porque no hay forma de que un test detecte la **ausencia** de una
comparación.

**Arreglo:** el guard debería exigir que el conjunto vigilado se **deriva** del disco (p. ej. que
`en_el_disco` se compare Y que `ESPERADOS` seignore; o mejor, que el propio test afirme sobre el
disco que toda vista con `self.after` está en el conjunto vigilado). Es el mismo patrón que la
`NameError`/`proibido_tk`: una comprobación sin contraprueba que laBlinden.

## 9.3 · Lo que el dev decidió NO tocar (R6), y por qué sobrevive cada uno

Los tres que §8.5 declara "equivalentes, se documentan, no se arreglan" **siguen sobreviviendo por
la razón que dice**, medido:

- **S2** (`except Exception` → `except BaseException`): sobrevive (26 400 B, `ALL TESTS PASSED.`).
  Equivalente real para el `RuntimeError` que el guard trata. Correcto.
- **S3** (`except Exception` → `except RuntimeError`): sobrevive. Y la premisa que lo hace
  equivalente está **verificada contra el código real**: `tk_thread.py:83` captura `except
  Exception` (MEDIDO leyendo el fichero), así que S2 y S3 son indistinguibles *para `RuntimeError`*
  y su única diferencia es `tk.TclError`, que ningún test provoca. Si el código capturara otra
  cosa (p. ej. `except BaseException`), S2 y S3 **no** serían equivalentes y el argumento se
  desharía — pero no es el caso. La nota de TASK-078 en el propio docstring es correcta.
- **SV4** (`tk.TclError` declarado y sin test): sigue como deuda baja, tal como dice §8.5. No lo
  vuelvo a mutar porque es el mismo S3 por otro nombre.

Estos tres son **mutantes equivalentes, no cobertura faltante**, y está bien que consten.

## 9.4 · R5 · ¿Están justificadas las dos excepciones, o son un agujero con nombre? — SÍ, están justificadas

El encargo pedía auditar si las dos excepciones que la ampliación declara están justificadas por el
código real. **Las dos lo están**, y medido:

1. **`("gaming_service", "restore_gaming_session")`.** El worker `DashboardView._on_restore_clicked`
   lo llama **de verdad** desde su `Thread` (`dashboard_view.py:282`). `R5c` (quitarla de
   `PERMITIDOS`) **mata** con `DashboardView._on_restore_clicked:L282 ... desde el hilo secundario`
   → la excepción existe porque el código real la necesita, no para tapar un agujero.
2. **`_handle_err`/`_handle_ok` en la lista blanca de callbacks.** Los dos son las clausuras
   locales de `process_managerView._force_update_db` que publican al principal
   (`process_manager_view.py:196/204`). `R5a` (quitarlos de la lista) **mata** nombrando
   `_handle_ok` con el mensaje del propio guard → la excepción está **usada** por el código real.
   Y `R5b2` (publicar a un callback **local que ya existe** y que **no** está en la lista)
   también mata → la lista es **estrecha**, no un comodín que acepta cualquier nombre local.

   **Lo que R5b2 NO demuestra, y hay que decirlo:** su rojo lo produce el **recuento de 10
   publicaciones** (`las tres vistas tienen 11 publicaciones...`), no la lista blanca, porque
   `R5b2` **añade** una publicación y eso dispara el assert de recuento antes de llegar a la regla
   de la puerta. El mutante que sí mata la lista blanca por su cuenta es `R5a`. Los dos juntos sí
   dicen lo que hay que decir: la lista está **usada** (`R5a` la necesita) y **es estrecha**
   (`R5b2` no admite un nombre local nuevo) — pero el segundo por el camino del recuento. Con una
   mutación que no altera el número de publicaciones (cambiar `(0, _handle_err)` por
   `(0, _on_success)` sobre la misma línea, sin añadir) el discriminante sería directo; no se
   Lansó porque el par `R5a`+`R5b2` ya cubre las dos preguntas que hace el encargo, y R3c (que sí
   se Lanzó, sin alterar el recuento) confirma que **la regla de la puerta sí se comprueba sobre un
   call site existente**.

**Recuento 10/10 — ¿se puede satisfacer con un conjunto menor? NO.** El encargo lo pregunta
explícitamente ("si mañana alguien borra una publicación legítima, ¿el guard lo nota, o solo se
fija en la igualdad de dos números que bajan juntos?"). MEDIDO: `R5e` borra una publicación
legítima (`process_manager_view.py:181`) y el guard **mata** con
`las tres vistas tienen 9 publicaciones ... el invariante habla de 10 ... decidalo explicitamente
en vez de dejar que el guard se adapte solo`. El `contados_en_codigo == 10` (contado de forma
independiente del recorrido) es lo que impide que los dos números bajen juntos: si borrás una
publicación, el código da 9 y el assert de 10 salta. **El recuento está anclado y aguanta.**

## 9.5 · Veredicto

# VERDICT: FAIL

**Por qué, en una frase:** los tres huecos del encargo (**SV1, SV2, SV3**) **están de verdad
cerrados** — `R1`, `R2a`/`R2c` y `R3c` mueren todos por la aserción que dice, nombrando el fichero y
la línea — **pero la reparación dejó sin cerrar dos cosas más**: el guard de la frontera de
`tk_thread.py` es ciego a los imports absolutos con prefijo de paquete (**R4b**, alta), y la
ampliación a los callbacks de `load_db_async` dejó de exigirles el invariante del worker (**R5f**,
alta). El tercer superviviente (**R2b**, quitar el `glob` sin rojo) es una comprobación sin
contraprueba.

**Lo que merece decirse de este ciclo:** los tres SV del informe anterior están cerrados con
mutantes que mueren **por la aserción correcta y con el síntoma nombrado** (`L196 ... debe ser de
0 ms`, `['psutil']`, "los cuatro ficheros vigilados"). Eso es exactamente lo que se le pedía a un
guard. Y `R3c` — el call site que la pasada anterior escapaba — ahora muere, y muere **por la
regla de la puerta** (`debe ser de 0 ms`), no por un efecto colateral. El trabajo de TASK-078 es
real.

**Pero los dos supervivientes altos son del patrón que este informe lleva tres ciclos marcando:**
una comprobación que **no tiene contraprueba**. `R4b` porque la lista de prohibidos compara el
primer segmento del módulo y el repo importa en absoluto; `R5f` porque un cuerpo que corre en el
hilo secundario quedó exento del invariante del hilo secundario. Los dos eran **verificables** y
no se verificaron.

### Tickets que deja esta re-auditoría

| ticket | severidad | qué hay que hacer |
|---|---|---|
| **R4b / SV1'** | alta | el guard de imports de `tk_thread.py` debe comparar el **módulo completo** (`endswith("." + p)`), no el primer segmento; y añadir **contraprueba** que el detector ve un `from woptimizer.services import ...` sintético |
| **R5f / SV2'** | alta | los callbacks de `load_db_async` deben pagar **también** el invariante del worker (o quedar explícitamente exentos de tocar widgets); corregir el docstring de `_publicaciones_malas` ("ya en el hilo principal" es **falso**: corren en `_download`, el hilo del servicio) |
| **R2b / SV3'** | media | el `glob` que deriva `views/*.py` necesita contraprueba, o el guard debe exigir que el conjunto vigilado se deriva del disco |
| **SV4** | baja | (sin cambio) `tk.TclError` declarado y sin test — mutante equivalente, bien documentado |
| **S2/S3** | — | (sin cambio) mutantes equivalentes, correctos según §8.5; la premisa (`except Exception`) **verificada** |

### Nota de arnés para el orquestador

- La re-auditoría crea **17 cámaras desechables** en `%TEMP%\wopt_muts\`, cada una un clon con
  historial real. La base `%TEMP%\wopt_audit_62_rea` queda **verde** (`ALL TESTS PASSED.`,
  26 404 B).
- **No se reparó nada** de `src/` ni de `run_tests.py`. Reparar es de `openspec-dev`.
- El único cambio en el árbol real es este fichero, **sin comitear**.
- La mutación inicial de `R3_M8a` (Trampa T1) fue **mía** y la detecté mirando el fichero, no el
  log; sin la verificación posterior de "cámara mutada en disco" (17/17) habría reportado un
  "supervive" inexistente. Los veredictos de este informe son de la **segunda** pasada de `R1`, de
  `R3c` y de `R5b2`.
- **T3 (Trampa T4) es un hecho de producción, no mío:** los guards de TASK-073 son los dos
  **últimos** de la suite, y `test_dead_code_ast_guard` va 310 líneas antes. Quien mida TASK-073
  tiene que comprobar **de qué aserción** viene el rojo, porque otro guard puede tapar al que se
  quiere medir.

---

# 10. Reparación (TASK-079) · rol `openspec-dev`

**Qué se repara:** los tres huecos de §9 (`R4b`, `R5f`, `R2b`) y las tres afirmaciones del change que
§8.7 dejó sin corregir. **Solo guardas y documentación: `src/woptimizer/**` no se toca.**

**Línea base, medida ANTES de mutar nada** (repo real, `beta`): `python run_tests.py` →
**`ALL TESTS PASSED.`**, 364 líneas, **26 404 B**, rc=0, **496 s**. Es el mismo byte count que la base
de la re-auditoría, que es lo que tiene que ser: los guards se repararon sin cambiar una sola
línea de salida.

## 10.0 · La armería, y una trampa de arnés que ME pasó aquí

Cada mutante corre en una cámara desechable de `%TEMP%\wopt_t079\<mutante>\`: un
`git clone --local --no-hardlinks` del repo real al que se le copia **encima** el árbol de trabajo
(con los cambios sin comitear de este turno). Antes de lanzar nada, el arnés **comprueba en disco**
(a) que el `git-dir` de la cámara es el de la cámara y no `%LOCALAPPDATA%`, y (b) que la mutación
se escribió. Las tres cosas, porque las tres se pueden dar por buenas sin estar.

**Trampa T5 (mía, y la registro porque casi me cuesta los tres primeros veredictos):** la primera
tanda no hizo `clone`, copió el árbol con `shutil.copytree`. Sin `.git`, las tres cámaras murieron
a los ~3,4 KB en un test de git que no tiene nada que ver con el mutante:

```
AssertionError: git no resuelve `--absolute-git-dir` para ...\wopt_t079\r4b con el entorno limpio
(rc=128, salida='fatal: not a git repository (or any of the parent directories): .git'), luego no hay
referencia contra la que verificar que una candidata sea de este arbol.
```

Es la misma clase que la T2 de §9.0 (un rojo del arnés leído como veredicto) y que la T1 (una cámara
que nunca se mutó sale verde). **Los tres veredictos de esa tanda son NO MEDIDOS, no "killed"**, y no
se cuentan para nada. La tanda buena es la de las cámaras clonadas, que es la de las siete filas de
§10.1.

Lo que sí se respetó de la T3/T4: **todas las mutaciones de `src/` no dejan código muerto**
(una línea nueva, un import nuevo, un fichero de vista nuevo con un método cuyo nombre ya está
referenciado), y `test_dead_code_ast_guard` —que corre 310 líneas antes— pasó en las siete cámaras:
en `r2b_vista_nueva` se ve, porque el log llega a 369 líneas y muere en el guard de TASK-073, no en el
de código muerto.

## 10.1 · Siete mutantes, seis muertos y un verde que es el que tiene que ser verde

Motivo **literal**, pegado del log de cada cámara (`%TEMP%\wopt_t079\<m>.log`):

| mutante | qué se rompió | veredicto | motivo literal |
|---|---|---|---|
| **`r4b`** | `ui/tk_thread.py` importa `from woptimizer.services import process_service` | **killed** | `AssertionError: ui/tk_thread.py viola la frontera de capas: importa ['woptimizer.services', 'woptimizer.services.process_service']. La logica de publicar en el bucle es UI pura: solo llama a un metodo del widget que recibe` |
| **`r4b_control`** | el guard vuelve a comparar el **primer segmento** (el defecto de TASK-078 reinsertado en el propio detector) | **killed** | `AssertionError: CONTROL-PREFIXO-SERVICES: el detector no marca ['woptimizer.services', 'woptimizer.services.process_service'] y solo ve []. Con el primer segmento como criterio, from woptimizer.services import process_service pasaba en verde` |
| **`r5f`** | un callback de `load_db_async` toca `status_label` desde el hilo secundario | **killed** | `AssertionError: el callback que el servicio ejecuta en un hilo secundario toca la vista fuera de la puerta: ProcessManagerView._force_update_db:L193 self.status_label.configure(...) desde el hilo secundario` |
| **`r5f_clausura_llamada`** | una clausura anidada que el callback **llama** (no publica) toca el widget | **killed** | `AssertionError: el callback que el servicio ejecuta en un hilo secundario toca la vista fuera de la puerta: ProcessManagerView._force_update_db:L194 self.status_label.configure(...) desde el hilo secundario` |
| **`r5f_principal`** | la clausura **publicada** (`_handle_ok`) toca el widget: corre en el principal, es correcto | **verde (por diseño)** | `ALL TESTS PASSED.` (26 400 B, 364 líneas) |
| **`r2b_vista_nueva`** | una vista nueva en `ui/views/` que `ESPERADOS` no declara | **killed** | `AssertionError: hay vistas en el disco que este guard no vigila: ['zz_vista_de_prueba.py']. Una vista nueva nace con la deuda de self.after a mano y nadie la mira` |
| **`r2b_sin_derivacion`** | `_vistas_del_disco` deja de mirar el disco (el `R2b` del ciclo 62) | **killed** | `AssertionError: hay vistas en el disco que este guard no vigila: ['dashboard_view.py', 'pack_manager_view.py', 'process_manager_view.py']. Una vista nueva nace con la deuda de self.after a mano y nadie la mira` |

**Recuento: 7 mutantes · 6 killed · 1 verde-y-es-correcto.** Los tres huecos de §9 están cerrados, y
cada uno por la aserción que nombra el defecto.

**Por qué hay siete y no tres.** Tres son los del encargo. Los otros cuatro son lo que hace que una
guarda reparada no sea una guarda *supuesta*:

1. **`r4b_control` mata la CONTRAPRUESTA, no el fichero real.** Si lo único que se comprobara fuera
   `tk_thread.py`, bastaría con que el detector mirara donde le da la gana. Este mutante degrada el
   predicado al primer segmento y muere en el control sintético `CONTROL-PREFIXO-SERVICES`, que es la
   línea que demuestra que el detector ve la forma de import que escribe el repo.
2. **`r5f_clausura_llamada` mide la frontera del corte.** La reparación exime de medir las clausuras
   que el callback **entrega a la puerta**, porque esas corren en el principal. La tentación
   obvious —cortar por "todo lo anidado"— habría abierto un agujero: una clausura que el cuerpo solo
   **llama** sigue corriendo en el secundario. El corte es por los nombres **publicados**
   (`_cuerpos_a_medir`), y este mutante es lo que demuestra que el corte es el correcto y no el
   cómodo.
3. **`r5f_principal` es el control que NO tiene que morir.** La clausura `_handle_ok` se publica, así
   que corre en el hilo principal y tocar el widget ahí es exactamente lo correcto; un guard que la
   marcara estaría prohibiendo el código bueno. Sale verde, y por eso sale verde: es la mitad
   "`r5f` mata lo que tiene que morir" que no se lee sola.
4. **`r2b_sin_derivacion` mata el `R2b` viejo.** Con la derivación convertida en el origen de lo que
   el guard abre, quitarle el `glob` ya no es "una comprobación que desaparece": es `a_abrir` vacío,
   y el nombre de las tres vistas sale en el rojo.

## 10.2 · Qué se cambió, y por qué es la mínima cosa

| sitio | qué hace ahora | por qué |
|---|---|---|
| `run_tests.py` (`test_ninguna_vista_programa_after_a_mano`) | `_modulos_de` + `_importa_prohibido` comparan la **ruta completa** (y `modulo.alias`, para `from woptimizer import services`), con cinco controles sintéticos y un control negativo sobre `typing` | `R4b` era ciego a la forma de import que el repo escribe; la lista estaba escrita en primer nivel y el código escribe rutas con prefijo de paquete |
| ídem (mismo guard) | `a_abrir` sale de `_vistas_del_disco(...)`; `RUTAS_VIGILADAS` pasa a decir solo **dónde** está cada fichero | `R2b`: la derivación era una comparación, no la fuente; sin esto, borrarla salía en verde |
| `run_tests.py` (`test_los_workers_de_pack_solo_publican_por_after`) | los callbacks de `load_db_async` pasan por `_infracciones_en(_cuerpos_a_medir(cuerpo), ...)`; `_publicaciones_malas` **desaparece** | `R5f`: sus cuerpos corren en el secundario; la función entera estava escrita sobre una medición falsa |
| `.taskmaster/tasks.json` | TASK-079 abierta y cerrada en este turno | el encargo |

**La medición previa, antes de escribir una línea (que era lo que el encargo pedía).**
`ProcessService.load_db_async` (`process_service.py:373-416`) llama `on_error(err_msg)` en `:402` y
`callback()` en `:411`, **los dos dentro de `_download`**, que es el cuerpo de
`threading.Thread(target=_download, daemon=True).start()` de `:416`. El hilo que decide el contexto
es el del servicio. **La auditoría tenía razón y el docstring estaba equivocado**: esos cuerpos no
corren en el principal, y el guard se cambió para medirlos en el hilo en el que corren.

**Por qué el corte es por nombres publicados y no "por lo anidado".** `_cuerpos_a_medir` exime solo
los `def` cuyo nombre aparece como argumento de una llamada a `self.after`/`self._publicar_en_el_bucle`
**y no** se llama en el cuerpo. Un nombre que se publica y además se llama queda **fuera** de la
exención (falla cerrado): hoy no existe en el código real, y prefiero un falso positivo a un agujero.
`r5f_clausura_llamada` es la medición de esa frase.

**Lo que NO se tocó, a propósito.** El guard gemelo de `confirmation.py` (`run_tests.py:1851-1853`)
hace lo mismo con `split('.')[0]`, pero lleva `"woptimizer"` en la lista de prohibidos: ahí la red más
gruesa es la **correcta**, porque ese fichero es una máquina de estado que no debe depender de nada
del paquete (importa a su hermano por ruta **relativa**, `from .tk_thread import publicar_en_bucle`,
que da `"tk_thread"` y no choca). Se **documenta** en el propio guard y no se modifica: tocarlo
sería arreglar algo que no está roto.

## 10.3 · Lo que tiene que seguir sobreviviendo, y por qué

`S2` (`except BaseException`) y `S3` (`tk.TclError` declarado y sin provocar) siguen siendo
**mutantes equivalentes**, y este turno **no cambia su premisa**: `ui/tk_thread.py:83` captura
`except Exception`, MEDIDO leyendo el fichero. Si alguien cambiara esa captura, S2 y S3 dejarían de
ser equivalentes y habría que re-auditar; por eso aquí no se toca ese `except`.

`r5f_principal` es el otro que tiene que seguir verde, y esta vez está medido (§10.1).

## 10.4 · Documentación del change corregida con lo MEDIDO

| sitio | qué decía | qué dice ahora |
|---|---|---|
| `proposal.md` §F1 (la tabla) | `winfo_exists()` lanza desde un worker **con la ventana viva** y sin ella, "1 de 1" | tres columnas: **sin bucle principal** lanza; con `mainloop()` vivo **devuelve 1 con la vista viva y 0 con el widget destruido, sin lanzar**. Se dice que la versión anterior reproduce el escenario A/B y le pone el nombre del C |
| `proposal.md` (docstring de `publicar_en_bucle`) | "lanza el mismo RuntimeError que `after`, incluso con la ventana viva" | "en el mundo **sin bucle principal**; con `mainloop()` vivo no lanza y devuelve 1/0" |
| `proposal.md` ("Criterio discriminante") | `llamadas == []` es **LA ASERCIÓN QUE DISCRIMINA** | es **tautológica** (mutante X1 de §6: con `registrar_antes=True` falla sin tocar producción); lo que discrimina el caso A es el `try` explícito y `handle is None`, y el conjunto entero por el caso B |
| `tasks.md` (docstring) | "`winfo_exists()` ... **también con la ventana viva**" | lo mismo que `proposal.md`, con la referencia a §2 del informe |
| `tasks.md` (caso A del test) | "`llamadas == []` es la aserción que hace el test discriminante" | lo que discrimina es el `try` + `handle is None`; `llamadas == []` mide **al doble** |
| `docs/ai/testing-guide.md` filas 76 y 205 | el alcance viejo | R5f, R4b (y por qué el guard de `confirmation.py` **no** se toca) y R2b |

**El recuento de tests no cambia: 205**, y por eso los cuatro sitios que lo derivan con `ast`
(`STATUS.md`, `AGENTS.md`, `README.md`, `docs/ai/testing-guide.md`) **no se tocan** —
`validate_docs.py` lo confirma deriving, no leyéndolo. `llms-full.txt` tampoco cambia:
`build_llms_full.py --check` dice que sus nueve secciones coinciden con su fuente, porque
`docs/ai/testing-guide.md` no es una de ellas.

## 10.5 · Verificación ejecutada en esta reparación

```
> python verify_ui_syntax.py
EXITO: Todos los modulos UI estan impecables.
rc=0

> python run_tests.py
...
guarda AST exhaustiva: 10 cuerpos de hilo secundario, 10 publicaciones vigiladas.
test_ninguna_vista_programa_after_a_mano OK.

ALL TESTS PASSED.
rc=0   (26 404 B, 364 lineas, 496 s)

> python validate_docs.py
Resumen: 143 OK, 0 FAIL
rc=0
```

## 10.6 · Veredicto de esta reparación

# R4b, R5f y R2b: CERRADOS, cada uno por un mutante que muere en su aserción.

Lo que esta reparación **no** hace, y conviene que conste: no cambia el comportamiento de
`src/woptimizer/**`. La producción de TASK-073 era correcta y lo sigue siendo; lo que estaba mal eran
tres guardas que no miraban lo que decían mirar. Y la lección que deja el ciclo, repetida por tercera
vez en este change: **una comprobación sin contraprueba no es una comprobación**. `R4b`, `R5f` y
`R2b` eran tres afirmaciones verdaderas sobre el código que nadie había medido — y `F1b`, el "killed"
que TASK-078 dio por bueno, era exactamente eso: un mutante que murió por el motivo equivocado y dejó
el agujero abierto dos pases.