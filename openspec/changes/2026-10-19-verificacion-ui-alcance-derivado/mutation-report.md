# Informe de mutacion — TASK-081 / Ciclo 67

**Auditor:** `mutation-auditor` (Sherlock) · **Fecha:** 2026-10-19 · **Rama:** `beta`
**HEAD esperado:** `44fb4e3` · **Camara:** `%TEMP%\sherlock_c67\camara` (copia sin `.git`, con repo sintetico propio)

> Metodo: todo se midio en la camara. Las exits de la matriz de producto son de
> subprocesos reales. Los veredictos de `run_tests.py` son de la suite completa,
> nunca de un fragmento.

---

## 1. N1 — LA PRUEBA DE PRODUCTO (la que decide)

`verify_ui_syntax.py` ejecutado **de verdad** contra el arbol real con un modulo
roto inyectado. Se mide el codigo de salida del proceso y su ultima linea.

| Escenario | Modulo roto | Exit medido | Exit esperado | Veredicto |
|---|---|---|---|---|
| **A0** | — (arbol sano) | **0** | 0 | control |
| **M1** | `ui/theme.py` (antes **no listado**) | **1** | 1 | **MATA** |
| **M2** | `ui/tray_menu.py` (antes **no listado**) | **1** | 1 | **MATA** |
| **M3** | `ui/app.py` (listado) | **1** | 1 | control positivo |
| **M4** | **modulo NUEVO** `views/modulo_nuevo_c67.py` | **1** | 1 | **MATA** |

**M4 es el caso que nadie detecta y ahora se detecta.** El recuento derivado
**sube solo** al anadir el modulo, sin que nadie actualice nada:

```
A0..M3   ALCANCE_DERIVADO=22 modulos revisados bajo src/woptimizer/
M4       ALCANCE_DERIVADO=23 modulos revisados bajo src/woptimizer/
```

Y la salida **nomebra el fichero roto** en los cuatro casos:

```
ERROR SINTAXIS en src/woptimizer/ui/views/modulo_nuevo_c67.py:
```

Tras restaurar, la camara vuelve a `exit 0`. **N1: PASS.**

---

## 2. N4 — CUANTAS ENUMERACIONES HAY DE VERDAD

Barrido **independiente con `ast`** (NO reutilizo `_enumeraciones_de_rutas_de_src`
del repo: medir el guard con su propio detector seria medirlo con su propia
regla). Criterio: todo literal `src/woptimizer/**.py`, por cualquier via
(lista, tupla, set, dict, argumento, `+=`), agrupado por ambito.

| # | Fichero | Ambito | Linea | Rutas | Deriva | (a) | (b) |
|---|---|---|---|---|---|---|---|
| 1 | `run_tests.py` | `test_no_literal_colors_in_views` | **8205** | 4 | no | si | si |
| 2 | `run_tests.py` | `test_hit_targets_minimum` | **8349** | 4 | no | si | si |

**Total: exactamente 2. NO hay una tercera.** La lista del dev esta completa
para el alcance declarado, y el guard R4 las encuentra todas.

### Pero la clase sigue viva FUERA del alcance del guard

El guard R4 prohibe literales bajo `src/woptimizer/**.py`. Con la red amplia
(cualquier literal que parezca ruta de repo) aparecen mas de la misma clase:

| # | Fichero | Linea | Que es | Por que NO lo ve R4 |
|---|---|---|---|---|
| **S1** | `run_tests.py` | **13187** | tupla `ficheros` (11 ficheros de **RAIZ**) | no son `src/**.py` |
| **S1b** | `run_tests.py` | **13188** | tupla `arboles = ("docs","openspec","src")` | idem |
| **S1c** | `run_tests.py` | **13190** | tupla `ocultos` (3 `.taskmaster/*`) | idem |
| **S2** | `validate_docs.py` | **1860** | 3 registros de ciclos (`CHANGELOG.md`, `.taskmaster/CHANGELOG.md`, `.taskmaster/rd_journal.json`) | idem |
| **S3** | `_chk.py` | **2** | 4 rutas, **script suelto TRACKEADO en la raiz** | no esta en los 3 ficheros del alcance, ni bajo `src/` |

`S1` esta **justificada** por escrito (es lo que declara el propio dev) y
`S1b`/`S1c` no. `S3` es un resto ya declarado en `proposal.md` §9.
**El alcance de AC-5 corta en `src/` y por eso la clase se reproduce justo
delante, a cuatro lineas del guard que la denuncia.**

---

## 3. N8 — RESIDUOS Y TRAMPAS PROPIAS

Barrido byte a byte de `\ufffd`, soft hyphen, zero-width, BOM, controles bidi,
CJK/Hangul/Kana, y recuento de finales de linea.

| Fichero | Bytes | BOM | CRLF | LF sueltos | Residuos |
|---|---|---|---|---|---|
| `verify_ui_syntax.py` | 3 181 | no | 0 | 77 | **0** |
| `run_tests.py` | 1 541 089 | no | 0 | 29 624 | **0** |
| `STATUS.md` | 22 567 | no | 0 | 148 | **0** |
| `docs/ai/testing-guide.md` | 275 811 | no | 0 | 1 375 | **0** |
| `CHANGELOG.md` | 188 135 | no | 0 | 1 592 | **0** |
| `validate_docs.py` | 145 390 | no | 0 | 2 783 | **0** |
| `proposal.md` / `tasks.md` del ciclo | 15 105 / 4 789 | no | 0 | 305 / 86 | **0** |

**TOTAL: 0 residuos.** Ni mojibake, ni Hangul, ni soft hyphen, ni BOM, ni
C0/C1. Los 8 ficheros de la camara son **byte a byte identicos** al repo real,
asi que esto no es un artefacto de la copia. **N8: PASS.**

---

---

## 4. N5 — LA JUSTIFICACION DE `run_tests.py:13187`, ¿ES CIERTA?

La afirmacion del dev es que esa tupla **no** se derivaria con `rglob` sin perder
nada. Medida, no supuesta: la raiz tiene **31 ficheros**, de los cuales **27** no
ocultos. Un derivado traeria **16 que la tupla NO incluye**:

```
LICENSE, _chk.py, _chk2.py, _matrix_c26.py, benchmark.py, force_build.py,
package.json, pyproject.toml, requirements-mkdocs.txt, run.py,
saved_processes.json, smoke_check.py, verify_app.py, verify_exe.py,
verify_ui_syntax.py, woptimizer.spec
```

⚠️ `saved_processes.json` es un **artefacto de runtime**: derivar lo metería en un
esqueleto de validador. La derivacion no es neutra.

Y la tupla es una **SELECCION**, no un hecho del arbol: `validate_docs.py`
nombra **10 de sus 11** entradas como literal; el que sobra, **`build.bat`**, no
aparece en ningun `.py` del validador (aparece en `verify_exe.py`, `AGENTS.md`,
`STATUS.md`, `CHANGELOG.md`).

**La justificacion (a) del dev es CIERTA: medido, no derivable.**

⚠️ **Pero la (b) es aspiracional, y es la unica de las tres que lo es:**

| Guard | (b) "QUE LA RETIRA" | Accionable? |
|---|---|---|
| `test_no_literal_colors_in_views` | «sustituye la tupla por `views/*.rglob("*.py")` mas `main_window.py`» | **SI**: nombra la expresion de reemplazo |
| `test_hit_targets_minimum` | «el mismo ciclo que derive `test_no_literal_colors_in_views` deriva esta, porque comparten la tupla» | **SI**: nombra el disparador y el acoplamiento |
| `_copiar_el_esqueleto_del_validador` | «solo si el validador deja de depender del conjunto... **no esta medido y no se prejuzga**» | **NO**: no hay ticket, ni ciclo, ni condicion comprobable |

Las tres pasan el guard (≥30 caracteres), pero una **no dice que hacer**. Es
justificacion de tramite en la tercera de tres.

---

## 5. N7 — LAS CIFRAS: DERIVADAS O ESCRITAS

Derivadas por mi con `ast`, sin fiarme de la declaracion del dev:

| Cifra | Declarada | Derivada por mi | ¿Sale de derivar? |
|---|---|---|---|
| `231` tests | `STATUS.md:116`, `run_tests.py:29605` | **`231`** `def test_*` con `ast` | **SI** |
| `231` invocados | — | **`231`** llamadas `test_*()` en `__main__` | **SI** |
| `0` testsDefined-perdidos | — | **0** `def test_*` nunca llamadas | **SI** |
| `22` modulos | `STATUS.md:11`, salida del script | **`22`** `rglob("*.py")` | **SI** |
| `155 + 76 = 231` | `run_tests.py:29608` | `validate_docs.py` lo reparte con `MARCADOR_HEADLESS`, no con una constante | **SI** |

`validate_docs.py::_recuento_de_tests` devuelve `(defined, invoked,
solo_definidos, solo_invocados)` con `ast` y **no contiene ninguna constante
esperada** (`TESTS_ESPERADOS = <n>` no existe). El `231` de `STATUS.md:116` esta
atado por `_RE_CIFRA_DE_TESTS`. **N7: las cifras derivan, no se escriben.**

### La excusa del dev sobre `CHANGELOG.md:147` y `:189`: **NO se sostiene**

AC-6 dice literalmente «ni `STATUS.md` **ni `CHANGELOG.md`** con una cifra de
modulos UI escrita a mano». Medido:

* `CHANGELOG.md:147` y `:189` siguen diciendo **«9 de 9 modulos»** (2 ocurrencias,
  las unicas; las de `:615` y `:1580` son falsos positivos de mi regex).
* El test de AC-2 **no abre el `CHANGELOG.md`**: solo lo menciona en su
  docstring. Un `Select-String` sobre `run_tests.py` y `validate_docs.py` por
  lineas que unan `CHANGELOG` con `modul|cifra|recuento|deriv` devuelve
  **UNA sola linea**: la del docstring del propio AC-2.

Es decir: **nada falla si manana alguien escribe «9 de 9 modulos» en el
CHANGELOG, y nada falla porque siga estan las dos de hoy.** Que sean entradas
historicas es cierto y no es la pregunta: la pregunta es si AC-6 esta
cumplido, y la mitad del CHANGELOG **no lo esta y no esta vigilada**. Es
**deuda viva** con nombre: **S4**.

---

## 6. N9 — ¿ABRIO EL ARREGLO OTRO AGUJERO?

### (a) Coste en CI: **medido, no es un problema**

| Metrica | Valor medido |
|---|---|
| Tiempo de ejecucion | **0,13 s** (arbol sano) / 0,12 s (con un roto) |
| Lineas de salida | 22 `OK:` + 1 recuento |
| Bytes de salida | 1 542 |
| Antes (10 ficheros) | ~0,06 s, ~700 B |

Medio segundo de mas en un runner. **Ruido: ninguno.**

Legibilidad del fallo: el `ERROR SINTAXIS en <fichero>:` nombra el fichero. Un
nit menor: **en rojo la ultima linea es `ALCANCE_DERIVADO=N` y no hay linea de
resumen de errores** (la version vieja cerraba con `EXITO: ...` en verde, y en
rojo con `sys.exit(1)` sin nada). Quien lee un fallo ve el nombre del fichero y
el recuento, pero no "1 error de 22". **Nit, no agujero.**

### (b) ¿El alcance anterior excluia algo A PROPOSITO? **NO**

Leido el fichero en `HEAD~1` y en `bbcc472` (el ultimo toque de la lista). Era:

```python
files_to_check = [
    'src/woptimizer/ui/app.py', ... 'src/woptimizer/__main__.py'
]   # diez entradas, SIN UN SOLO COMENTARIO
```

**Ni una linea de justificacion, ni una exclusion, ni un sentinel.** No hay
nada que `rglob` haya traido que estuviera fuera por decision. R2 («sin lista de
exentos») **no ha introducido ningun modulo que antes se excluyera a proposito**,
porque antes no habia ninguna exclusion declarada.

Lo unico que el derivado ha anadido de mas son ficheros que **antes no se
miraban porque nadie los escribio en la lista**: `theme.py`, `tray_menu.py`,
`config.py`, `models.py`, los cuatro `__init__.py`, `utils/__init__.py`,
`gaming_service.py`, `pack_service.py`, `process_service.py`. Todos compilan
(`A0` = exit 0), asi que ninguno es ruido.

**N9: el arreglo no abrio otro agujero de alcance.** El coste es una clase que
sigue viva **fuera** del alcance del guard (§2), que no es lo mismo.

---

---

## 7. N3 — LA TOLERANCIA SIN LISTA MUDA

Medido **in-process** sobre el detector real del repo
(`_delitos_de_enumeracion` / `_justificacion_de_la_enumeracion` importados de la
camara), alimentado con codigo sintetico. Longitud minima: **30**.

| Celda | Entrada | Veredicto del detector |
|---|---|---|
| A | sin justificacion ninguna | **DENUNCIADO** |
| **B** | **las dos marcas PEGADAS Y VACIAS** | **DENUNCIADO** ✅ |
| C | marcas con **29** caracteres | **DENUNCIADO** ✅ (limite juste) |
| D | marcas con **30** caracteres | TOLERADO ✅ (limite juste) |
| E | alcance DERIVADO con `rglob` | TOLERADO ✅ |
| F | la frase real del dev, recortada a 9 y 16 car. | **DENUNCIADO** ✅ |

**La afirmacion del dev es CORRECTA y esta medida: la tolerancia NO se compra con
dos cadenas.** Pegar las dos marcas vacias da **ROJO** con fichero y linea. Es
justo lo contrario de una lista de permitidos.

### S5 — el detector lee la PRIMERA ocurrencia (`doc.find`), no la ultima

Medido. La justificacion se busca con `doc.find(marca)`, luego el detector se
queda con **la primera** aparicion de cada marca en el docstring. Y escribir la
regla *antes* de cumplirla es lo mas natural del mundo: el propio guard nuevo lo
hace (`run_tests.py:28977`: «(a) por que existe la enumeracion y (b) que la
retira»).

| Escenario | Veredicto | Lo que el detector se leyo |
|---|---|---|
| prosa ANTES con **<30** car. + justificacion REAL despues | **DENUNCIADO** ❌ falso positivo | `(None, None)` — **ignoro la justificacion real** |
| prosa ANTES con **>=30** car. | **TOLERADO** ⚠️ | `('porque sin esto el guard se compra con dos cadenas', 'en el docstring del propio guard.')` |

Es decir: **la tolerancia real es «60 caracteres despues de dos cadenas
exactas, en el orden que sea»**, no «una justificacion». El contenido no se
comprueba, y el **orden importa en silencio**.

Severidad: **BAJA-MEDIA**. No es el agujero que este ciclo cierra (no se
compra con dos cadenas vacias: hacen falta 60 caracteres escritos), pero es
una propiedad mal declarada por el guard, que se describe a si mismo como si
mirara la justificacion cuando solo mira su longitud.

Arreglo que necesita: `find` -> `rfind` (o tomar la ultima ocurrencia), y decir
en el docstring que el criterio es longitud, no veracidad.

---

## 8. N6 — EL REGISTRO DE `argv` INDECISABLES

`REGISTRO_INDECISAS` (`run_tests.py:23718`) es **un conjunto escrito a mano**:
**15 celdas** que mapean `(callee, repr(argv))` -> numero de ocurrencias. No se
deriva de nada.

Medido con `_llamadas_cat_file_batch_check` (la funcion real) sobre el sano y
sobre el mutado:

| | SANO | M-N6b (una llamada indecisable AÑADIDA) |
|---|---|---|
| llamadas INDECISAS detectadas | **20** | **21** |
| celdas escritas a mano | 15 | 15 |
| `de mas` | ninguna | **`[('subprocess.run', '[_sys.executable, ruta_fantasma_c67]')]`** |
| `de menos` | ninguna | ninguna |
| **veredicto del guard** | VERDE | **ROJO** |

**La afirmacion del dev queda CONFIRMADA por medicion: su `subprocess.run` se
colo «de mas» y el propio guard lo detecto.** No fue casualidad: lo reproduce
cualquier llamada indecisable nueva, porque la comparacion es de igualdad exacta
y en los dos sentidos.

### Pero es la MISMA CLASE, y eso hay que decirlo

| | La clase que este ciclo cierra | `REGISTRO_INDECISAS` |
|---|---|---|
| Conjunto escrito a mano | SI | **SI** |
| Crece cada vez que anade alguien | SI | **SI** (15 celdas, una por llamada indecisable; la de TASK-081 es la suya) |
| Se puede pudre en **silencio** | SI | **NO** — `de mas` y `de menos` los dos dan rojo |

Es **deuda de crecimiento, no agujero**: no se puede quedar viejo sin que nadie
lo note. Pero **es la misma forma**, y AC-5 **no lo cubre** porque sus literales
son `[sys.executable, 'verify_ui_syntax.py']`, no rutas bajo `src/woptimizer/`.
Nombre: **S6**.

Nota sobre la otra mitad del contrato: `de_menos` esta en el mismo `assert`
(`run_tests.py:23780`), asi que **una entrada sobrante tambien tumba**. Eso lo
leo en el codigo, **no lo mute** (no corria presupuesto para un octavoclone).

---

## 9. N2 — ¿LA PAREJA AC-3 + AC-4 MIDE ALGO?

`M-C` = el script que devuelve `exit 1` **siempre**. Ejecutado de verdad en su
propia camara, guard por guard:

| Guard | Veredicto con M-C | Motivo literal |
|---|---|---|
| **AC-3** (modulo nuevo roto -> exit 1) | **VERDE — sobrevive** | cumple el sujeto |
| **AC-4** (arbol sano -> exit 0) | **ROJO — muere** | «el arbol SANO tiene que dar exit 0 y dio 1. **Si esto falla, AC-3 no mide nada: una puerta que siempre sale con 1 tambien cumpliria AC-3**» |
| **AC-2** (recuento derivado) | **ROJO — muere tambien** | «verify_ui_syntax.py sobre el repo REAL tiene que dar exit 0 y dio 1» |

### La pregunta que SI importa, contestada

> ¿la pareja AC-3+AC-4 mide algo que un script permanentemente roto no cumpliria?

**SI. Medido, no arguido:** `M-C` **cumple AC-3 y falla AC-4**. Un script con
`sys.exit(1)` constante pasa el sujeto entero y no pasa el control. **El
razonamiento del dev es CORRECTO y el diseño es el bueno: el superviviente de
AC-3 es ruido por construccion, no un agujero.** Declarar «M-C sobrevive» como
fallo seria medir mal.

⚠️ **Correccion a la declaracion del dev, pequena pero con nombre:** dice que
M-C «muere en AC-4 pero sobrevive en AC-3». Medido, **M-C muere en AC-2
ADEMAS**, en `run_tests.py:28924`. No cambia el veredicto (M-C esta muerto de
todos modos), pero el recuento de *donde* muere estaba incompleto.

---

## 10. TABLA DE MUTANTES

Todos ejecutados en clones aislados de la camara, con la mutacion **verificada en
disco antes de correr** y `__pycache__` purgado entre mutaciones. Los cinco
guards de TASK-081 se ejecutan **de verdad** (no se simulan): se importa el
`run_tests.py` del clon y se llama a cada funcion de guard.

| id | Que rompi | AC-5/R4 | AC-1 | AC-3 | AC-4 | AC-2 | P1/N6 | **Veredicto** |
|---|---|---|---|---|---|---|---|---|
| **M-L** | tupla literal de 10 rutas de vuelta | ROJO | **ROJO** | **ROJO** | ROJO | ROJO | verde | **MUERTO** |
| **M-R2** | `rglob` **vivo pero muerto** + lista por variable | verde | **VERDE** | ROJO | ROJO | ROJO | verde | **MUERTO por AC-3** (S7) |
| **M-C** | `exit 1` siempre | verde | verde | **VERDE** | **ROJO** | **ROJO** | verde | **MUERTO** |
| **M-S** | `STATUS.md` a «10 modulos» | verde | verde | verde | verde | **ROJO** | verde | **MUERTO** |
| **M-W** | enumeracion de 4 rutas **sin justificacion** | **ROJO** | verde | verde | verde | verde | verde | **MUERTO** |
| **M-J** | las dos marcas **pegadas y vacias** | **ROJO** | verde | verde | verde | verde | verde | **MUERTO** |
| **M-N6b** | una llamada `subprocess.run` indecisable de mas | verde | verde | verde | verde | verde | **ROJO** | **MUERTO** |

### Motivos literales (no parafraseados)

* **M-L / AC-1** (`run_tests.py:28740`):
  `verify_ui_syntax.py vuelve a ENUMERAR su sujeto: linea 47: ['src/woptimizer/__init__.py', ...]`
* **M-L y M-R2 / AC-3** (`run_tests.py:28824`):
  `un modulo NUEVO con error de sintaxis tiene que dar exit 1 y dio 0. Este es el M4 del encargo, el caso que se va a dar el dia que alguien anada una vista.`
* **M-C / AC-4** (`run_tests.py:28865`): el mensaje citado arriba.
* **M-S / AC-2** (`run_tests.py:28952`):
  `STATUS.md declara 10 modulos y el script imprime 22 (derivado de src/woptimizer/ con rglob). Actualiza el numero del panel: es el mismo fallo que el del mutante M-S`
* **M-W y M-J / AC-5** (`run_tests.py:29014`):
  `Enumeraciones de rutas de 'src/woptimizer/**.py' sin derivar el alcance y sin justificacion escrita en el docstring del propio guard`
* **M-N6b / P1** (`run_tests.py:23780`):
  `el REGISTRO de las llamadas cuyo argv NO se ha podido resolver esta desfasado`

**Todos mueren por la ASERCION que su test dice comprobar.** Ninguno muere por
`ImportError`, `NameError` ni sintaxis rota de la camara.

### La linea base y `M-L`, por suite completa, en solitario

| Corrida | Exit | Log | Ultima linea |
|---|---|---|---|
| **camara sana** | **0** | 399 lineas · 30 153 B | **`ALL TESTS PASSED.`** |
| **`M-L`** | **1** | 402 lineas · 30 411 B | `AssertionError` con traceback |

Traza de `M-L` (**la asercion, no un `ImportError` ni una sintaxis rota**):

```
File "...\m_ML\run_tests.py", line 29619, in <module>
  test_ningun_guard_enumera_el_arbol_de_src_que_ya_esta_en_el_sistema_de_ficheros()  # R4/AC-5
File "...\m_ML\run_tests.py", line 29014, in test_ningun_guard_enumera_el_arbol_de_src_...
  assert not violaciones, (
AssertionError: Enumeraciones de rutas de `src/woptimizer/**.py` sin derivar el alcance
y sin justificacion escrita en el docstring del propio guard (TASK-081, R4):
  - verify_ui_syntax.py:47 (en `modulos_del_arbol`): ['src/woptimizer/__init__.py',
    'src/woptimizer/__main__.py', 'src/woptimizer/config.py', 'src/woptimizer/models.py',
    'src/woptimizer/ui/app.py', 'src/woptimizer/ui/main_window.py',
    'src/woptimizer/ui/theme.py', 'src/woptimizer/ui/tray_menu.py',
    'src/woptimizer/ui/views/dashboard_view.py', 'src/woptimizer/ui/views/pack_manager_view.py']
```

⚠️ En la suite **completa** el primero en caer es AC-5 (la forma); en la corrida
por guard, AC-3 (el producto) tambien lo mata. **Los dos caminos cierran.**

⚠️ Una primera tanda de **ocho** suites en PARALELO se atasco toda en el mismo
punto (179 lineas) y la base fallo en `run_tests.py:23389`, fontaneria de git ajena
a TASK-081. Reproduje ese test **aislado** sobre la camara: `existe(h+'0') =
False`, o sea **pasa**; el rojo era contencion, no codigo. En solitario, verde.

### El primer M-R estaba mal mutado, y se rehizo

La primera version de M-R construia las rutas como `RAIZ / base / n`, que **no
resuelven a ningun fichero**, asi que el script salia 1 por `FileNotFoundError` y
AC-3 moria **por el motivo equivocado**: un rojo que no es atribuible al
supuesto. Se rehizo como `SRC / base / n` (rutas correctas) y se volvio a
ejecutar: ahora si muere con `exit 0` en vez de `1`, que es el motivo que
importa. **Un rojo por `FileNotFoundError` no es veredicto.**

---

## 11. S7 — EL AGUJERO DE AC-1 (MEDIDO, Y EL GUARD SE PASSA)

`M-R2` = `rglob` **escrito y vivo** pero **nunca usado**, y el alcance real
construido con una variable (para que no haya literales de ruta que el detector
vea):

```python
_derivado_muerto = sorted(SRC.rglob("*.py"))   # <- vivo, muerto de hecho
base = "ui"
nombres = ["app.py", "main_window.py"]
return [SRC / base / n for n in nombres]       # <- 2 ficheros de 22
```

| Assert de AC-1 | Lo que el guard **dice** hacer | Lo que **hace** |
|---|---|---|
| `_enumeraciones_de_rutas_de_src` == [] | mata la lista | VERDE (no hay literales) |
| `_deriva_el_alcance_del_arbol` | detecta la derivacion | VERDE (el `rglob` esta, vivo o muerto) |
| **`_bucle_sobre_el_alcance_derivado`** | «sin esta segunda mitad, el mutante **M-R** pasaria» | **VERDE — NO lo mata** |

El `_bucle_sobre_el_alcance_derivado` sigue **un salto** por helper, y por eso
`ficheros = modulos_del_arbol()` cuenta como derivado aunque lo que
`modulos_del_arbol` devuelva **no** sea el `rglob`. Ese salto, que existe para no
dar falso rojo en un refactor legitimo, es exactamente por donde pasa el `rglob`
decorativo.

**Mitigacion real: AC-3 lo mata por producto** (`exit 0` en vez de `1`, con el
modulo nuevo roto). El agujero existe en AC-1 y **no es explotable en el
producto**, pero el docstring de AC-1 afirma una cosa y hace otra.

Severidad: **MEDIA como afirmacion falsa del guard**, **BAJA como riesgo**
(R4/AC-3 cobre el caso). Arreglo: que `_bucle_sobre_el_alcance_derivado` verifique
que el valor que la funcion **devuelve** es el que produce la derivacion, no que
su nombre este enlazado.

---

## 12. HALLAZGOS, POR SEVERIDAD

### Sin severidad de seguridad ni de datos

Ninguno. Los siete mutantes mueren por su asercion; `src/woptimizer/**` no se
toco y el alcance derivado no trae nada que se haya roto en produccion.

### MEDIA — `S7`: AC-1 dice que mata M-R y no lo mata

`run_tests.py:28746` (docstring) afirma que sin `_bucle_sobre_el_alcance_derivado`
el mutante M-R pasaria. Medido: **pasa**. El salto por helper lo deja pasar.
Lo salva AC-3 por producto, luego el riesgo es bajo; lo que es alto es que el
guard **documenta una propiedad que no tiene**, y este repo acaba de gastar dos
cicios en que las justificaciones sean verdad.

### BAJA — `S4`: `CHANGELOG.md:147` y `:189` («9 de 9 modulos»), sin vigilancia

AC-6 los prohibe literalmente y **nadie los mira**: el unico guard de cifras abre
`STATUS.md`. No es un agujero (no hay forma de que el codigo este mal y salga
verde por esto), es **deuda de documentacion con la consigna incumplida a la
vista**.

⚠️ **La excusa del dev no se sostiene tal como esta escrita.** Dice que las deja
porque son entradas historicas «y son del orquestador». La primera mitad es
cierta; la segunda, medida con `git log -L`, **no**:

| Linea | Commit que la escribio | Fecha | Que es |
|---|---|---|---|
| `CHANGELOG.md:147` | `0864628` | 2026-10-08 | `fix(arnes): ... (TASK-072)` |
| `CHANGELOG.md:189` | `328237f` | 2026-10-06 | `docs(ciclo 59): cerrar TASK-070 ...` |

Los dos los escribio **el bucle** (autor `auditor`), no el usuario. No hay texto
humano que «no se toque»: son la misma clase de entrada que el propio ciclo
escribe. Por tanto no es «el orquestador lo dejo», es **la misma deuda de este
ciclo, puesta hace 11 y 13 dias**.

Arreglo (no reparo, solo digo cual es el que vale): **no reescribir el
historico** — un changelog es un registro y «9 de 9» fue verdad el 2026-10-06 —
sino **anadir en el changelog de TASK-081 que las dos lineas son historicas**, o
**reescribir AC-6 para que solo nombre `STATUS.md`** y deje de prometer lo que no
vigila. Lo que **no** se sostiene es dejarlas y decir que AC-6 se cumple.

### BAJA — `S5`: la tolerancia de N3 mide longitud, no justificacion

`_justificacion_de_la_enumeracion` usa `doc.find`, o sea la **primera**
ocurrencia, y solo exige 30 caracteres detras. Medido en §7: escribir la regla
antes de cumplirla hace que el detector lea la prosa, y con >=30 caracteres de
prosa la enumeracion queda **TOLERADA** con un motivo que no es el suyo. Arreglo:
`find` -> `rfind`, y decir en el docstring que el criterio es longitud.

### BAJA — `S6`: `REGISTRO_INDECISAS` es la misma clase y no la cubre AC-5

15 celdas escritas a mano que crecen con cada llamada indecisable nueva. **No se
puede pudre en silencio** (medido: `de mas` y `de menos` los dos dan rojo), asi
que es deuda de crecimiento, no agujero. AC-5 no lo ve porque sus literales no
son rutas bajo `src/`.

### BAJA — `S1`, `S2`, `S3`: la clase sigue viva FUERA del alcance del guard

`run_tests.py:13187/13188/13190`, `validate_docs.py:1860` y `_chk.py:2`. El guard
AC-5 corta en `src/woptimizer/**.py`, y las tres enumeraciones de `13187` estan a
**cuatro lineas** de un guard que denuncia enumeraciones. **Quinta vez en este
repo que cerrar una clase deja la misma clase delante.**

### NIT — la (b) de `_copiar_el_esqueleto_del_validador` es aspiracional

De las tres justificaciones, dos (b) nombran el reemplazo; esta dice «solo si el
validador deja de depender del conjunto... no esta medido y no se prejuzga». Pasa
los 30 caracteres y no dice que hacer. Arreglo: nombrarla o bajar el liston de las
otras dos.

---

## 13. VEREDICT

### Mutantes declarados por el encargo

| Mutante | Veredicto |
|---|---|
| **M-L** | **MUERTO** — en AC-1 (AST) **y** en AC-3 (producto), como se declaraba |
| **M-R** | **MUERTO** — pero **no por AC-1**, que se lo pasa; por AC-3 (S7) |
| **M-C** | **MUERTO** — en AC-4 y tambien en AC-2 |
| **M-S** | **MUERTO** — en AC-2, unica asercion, motivo correcto |
| **M-W** | **MUERTO** — en AC-5 |
| **M-J** | **MUERTO** — en AC-5; la tolerancia NO se compra con dos cadenas |

### Los cinco AC, uno por uno

| AC | Medido |
|---|---|
| **AC-1** (deriva, no enumera) | **PARCIAL**: mata la lista literal; **no** mata el `rglob` muerto por helper (S7) |
| **AC-2** (recuento derivado) | **PASS**: mata M-S con el motivo exacto; 22 y 231 salen de derivar |
| **AC-3** (modulo nuevo detectado) | **PASS**: es el que mata M-L **y** M-R por producto |
| **AC-4** (control positivo) | **PASS**: mata M-C, que es exactamente para lo que existe |
| **AC-5** (guard de forma) | **PASS** en su alcance declarado: encuentra las **2** enumeraciones que existen, y ninguna mas |
| **AC-6** (cierre sin cifras a mano) | **PARCIAL**: `STATUS.md` limpio y atado al derivado; `CHANGELOG.md` con «9 de 9» sin vigilancia (S4) |

### Lo que decide

Los **seis mutantes que importan mueren todos**, cada uno por la asercion que su
test dice comprobar. El encargo central —que M4, un modulo nuevo que nadie
lista, se detecte— esta **medido por producto** y es cierto: A0=0, M1=1, M2=1,
M3=1, **M4=1**, con el recuento subiendo solo a 23.

No hay ningun **agujero** que se manifestaria si el codigo estuviera mal: todo lo
que sobrevive esta cubierto por otro guard del mismo ciclo (S7 lo cubre AC-3) o
es deuda de documentacion sin efecto en el producto (S4, S5, S6).

**VERDICT: PASS**

Con cinco tickets nombrados y medidos (S4, S5, S6, S7 y las enumeraciones S1/S2/S3),
que son **deuda**, no fallo del encargo.

---

## 14. AISLAMIENTO DE LA CAMARA

* Copia hecha con `shutil.copytree(..., ignore=ignore_patterns(".git"))`, que
  cubre **ficheros** y directorios — `robocopy /XD .git` no habria servido,
  porque aqui `.git` es un **fichero** de 57 bytes.
* `git rev-parse --git-dir` desde la camara, con `GIT_DIR` desechable explicito,
  devuelve la camara. **Comprobado antes de mutar nada.**
* Cada clon de mutante tiene su propio `.git` (`.../m_XX/.git`), comprobado uno
  a uno antes de mutar.

### Repo real, al terminar

| Comprobacion | Resultado |
|---|---|
| `git rev-parse --short HEAD` | **`44fb4e3`** — el esperado, sin mover |
| `git log --oneline -1` | `44fb4e3 fix(tools): el alcance de la puerta de sintaxis UI se deriva, no se enumera (TASK-081)` |
| `git reflog -6` | cima: `44fb4e3` (el commit del dev). **Ninguna entrada nueva mia** |
| `git status --porcelain` | **solo** `?? openspec/.../mutation-report.md` (este informe) |
| `git diff --stat` | vacio |
| `git diff --cached --stat` | vacio |
| `.git` del repo real | sigue siendo un **fichero**: `gitdir: C:/Users/carch/AppData/Local/woptimizer_git/.git` |

**No toque el repositorio.** Lo unico escrito bajo
`C:/Users/carch/Nextcloud/Scripts/woptimizer/` es este `mutation-report.md`, y no
esta comiteado. Todo lo demas vivio en `%TEMP%\sherlock_c67\`.

### Lo que NO se midio, dicho con su nombre

1. **La rama `de_menos` del registro de N6** no se mute (hubo que rehacer M-R y no
   cabia otro clon). Se lee en el codigo: esta en el **mismo `assert`**, luego
   daria rojo. **No medido.**
2. **Las ocho suites en paralelo** se descartaron: se atascaron por contencion y
   la base fallo en fontaneria de git. Los veredictos de la tabla salen de
   ejecutar **cada guard de verdad**; la suite completa confirma la linea base
   (verde) y `M-L` (rojo por su asercion).
3. **La reparte 155+76** no la recalcule desde cero: verifique que las dos mitadas
   derivan con `ast` (231 defs, 231 invocadas, 0 huerfanas) y que
   `validate_docs._recuento_de_tests` no contiene ninguna constante esperada. El
   corte concreto en el marcador, no.
4. **M-C, M-S, M-W, M-J, M-N6b y M-R2 por suite COMPLETA**, no: se detuvieron las
   ocho paralelas y se relanzaron solo la base y `M-L`. Los otros seis tienen
   veredicto por **ejecucion real del guard correspondiente** (con su traceback y
   su asercion, mostrados arriba), que es donde vive la comprobacion; lo que no
   midio es el recorrido completo de los otros 226 tests con esos mutantes puestos.