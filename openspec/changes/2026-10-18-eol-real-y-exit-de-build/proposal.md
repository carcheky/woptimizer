# TASK-077 · El EOL de `build.bat` no es un bug: la premisa y el fix están mal

> **Veredicto del arquitecto: NO VISTO BUENO a la tarea tal como está escrita.**
> Medido en un clon desechable del HEAD `2decac4` y ejecutando `cmd.exe` de verdad.
> De los tres puntos que pedía el encargo, **los tres estaban planteados sobre una
> premisa que no se sostiene**. Esto no la ejecuta: la reescribe.

---

## 0 · TL;DR para quien decide

| Pregunta del encargo | Respuesta medida |
|---|---|
| ¿Cuántos ficheros incumplen `.gitattributes`? | **CERO en el repo versionado.** `i/crlf` = **0** sobre 256 tracked. El único incumplimiento está en el **árbol local de esta máquina** (37 ficheros) y **lo arregla un checkout, sin commit**. |
| ¿`benchmark.py` incumple? | **No.** Es `.py` → `* text=auto eol=lf` → **LF es lo correcto.** "Normalizarlo" sería **introducir** la violación. Fuera de alcance. |
| ¿`(a)` CRLF o `(b)` cambiar la política? | **Ninguna de las dos: no hay nada que normalizar.** Pero el destino es **(a)**, y por una razón distinta a la que dice `STATUS.md`. |
| ¿`.bat` en LF rompe el parser? | **No.** Medido: salida y código de salida **idénticos byte a byte** en 6 escenarios. La justificación de `.gitattributes:20` es **falsa**. |
| ¿Qué hace `--renormalize .`? | **Nada.** Medido: **0 ficheros staged** en un clon donde el incumplimiento era real. |
| ¿Puede `add -A` colarse 37 ficheros en un commit? | **No.** Medido: `add -A` con el árbol en LF deja el staged **vacío**. El riesgo real es el **opuesto**: el fix **no genera commit**. |

Lo que **sí** sale de aquí: 1 corrección de una afirmación falsa en `.gitattributes`,
1 guard que se puede mutar, y **la 🔴 S3 de `STATUS.md:62` absorbida**, que es el
único bug real que hay en `build.bat`.

---

## 1 · La medición, antes de cualquier cambio

### 1.1 · Estado del repo versionado (índice) — **conforme**

```
$ git ls-files --eol | <agrupar>
  214 i/lf, w/lf      34 i/lf, w/crlf      3 i/lf, w/mixed
    3 i/none, w/none       2 i/-text, w/-text          TOTAL 256 tracked

$ git ls-files --eol | grep -c 'i/crlf'   ->   0
```

**Ni un solo blob del índice lleva un CR.** El índice es la forma *normalizada*
(LF) de todo el texto, que es exactamente lo que `* text=auto eol=lf` exige.
**El repositorio cumple su propia política al 100 %.**

### 1.2 · El índice es correcto, y se prueba con un clon

Clon desechable en `%TEMP%` del mismo HEAD (`2decac4`), sin tocar el repo real:

```
$ git ls-files --eol -- build.bat
i/lf  w/crlf  attr/text eol=crlf   build.bat
build.bat -> 39 CRLF, 0 LF sueltos
$ distribución del clon: 251 i/lf w/lf · 3 i/none w/none · 2 i/-text w/-text
$ ficheros con attr eol=crlf: 1   |   de esos, con w/lf: 0
```

**La política funciona.** El fichero que la política marca como CRLF **llega CRLF
a cualquier clon**. Quien use el repo — un runner, otra máquina, un `git clone`
nuevo — recibe `build.bat` correcto.

### 1.3 · El único que incumple es **este** árbol de trabajo

`STATUS.md:75` afirma que `build.bat` "tiene 39 LF y 0 CRLF pese a `.gitattributes
eol=crlf`". La primera mitad es cierta **en este árbol y solo en este**. La
segunda insinúa un defecto del repo: **no lo hay**. Es un residuo de un checkout
anterior a que `.gitattributes` existiera (TASK-069) que **nunca se re-materializó**.

Los 37 ficheros desfasados del árbol local (34 `w/crlf` bajo política LF + 3 `w/mixed`):

```
.commitlintrc.json                      .releaserc.json
.github/workflows/commitlint.yml        .taskmaster/_gh_configure.py
.github/workflows/release.yml           .taskmaster/_gh_incert1.py
.gitignore                              .taskmaster/_gh_probe.py
_chk.py                                 .taskmaster/_gh_protect.py
_chk2.py                                assets/process_db.json
docs/GITHUB-SETUP-CHECKLIST.md          docs/ai/ui-design-system.md
docs/archive/legacy-root-data/README.md docs/archive/legacy-root-data/profiles.json
docs/archive/legacy-skills/architect/SKILL.md
docs/archive/legacy-skills/openspec-dev/SKILL.md
docs/archive/legacy-skills/process-db-updater/SKILL.md
docs/index.md                           docs/testing.md
force_build.py                          llms-full.txt
openspec/changes/2026-09-28-v3-ui-redesign/tasks.md
openspec/changes/2026-09-29-process-db-update/proposal.md     <-- w/mixed
openspec/changes/2026-10-03-github-releases-semantic-release/{proposal,tasks}.md
openspec/changes/2026-10-03-pack-seleccion-por-categoria/{proposal,tasks}.md
openspec/changes/2026-10-04-desbloquear-pipeline-commitlint/{proposal,tasks}.md
run.py                                  validate_docs.py
build.bat                               <-- el unico que DEBE ser CRLF y esta en LF
src/woptimizer/__init__.py              src/woptimizer/__main__.py
src/woptimizer/services/gaming_service.py  src/woptimizer/ui/confirmation.py
```

> **`src/woptimizer/**` sale en la lista.** El arquitecto no lo toca (fuera de su
> scope). Es normalización de **bytes en el árbol**, no edición de código, y no
> genera commit: el contenido del índice es idéntico antes y después. Que lo
> ejecute el dev y que quede **auditado** en la fila de `tasks.md`.

**Pérdida de contenido: cero.** Para los 37, `i/lf` significa que lo versionado es
LF puro; el checkout forzado reescribe exactamente eso. Solo se descarta ruido de
EOL sin comitear. Los tres `w/mixed` (`_chk.py`, `_chk2.py`,
`2026-09-29-process-db-update/proposal.md`) pierden su mezcla, no una línea.

---

## 2 · `git add --renormalize .`: la trampa, medida

El fix que propone `STATUS.md:75`. Medido en el clon, con el incumplimiento **real**
presente (`build.bat` a LF en disco):

```
$ git add --renormalize .
$ git status --porcelain            ->  (0 lineas)
$ git ls-files --eol -- build.bat   ->  i/lf w/lf ...   CR en disco = 0
```

**No-op absoluto.** Ni toca el índice (ya estaba normalizado) ni el árbol de trabajo
(`git add` **nunca** escribe en el árbol: `eol=crlf` actúa en el **checkout**, no
en el `add`). El fichero sigue en LF después del comando.

### 2.1 · ¿Y los ficheros ya en CRLF en el índice (la clase `3012c48`)?

**La pregunta no aplica a este repo: `i/crlf` = 0.** No hay ni un fichero con CR
en el índice, luego `--renormalize` no tiene contaminación de esa clase que
arreglar. La têmpora que menciona `.gitattributes:6-8` sePLIcame en un clon, y ahí
el `--renormalize` tampoco habría corregido el **árbol**.

### 2.2 · ¿Y si el wrapper `git add -A` se lo come?

Medido, con `build.bat` en LF y `core.autocrlf=true` en el clon:

```
$ git add -A
$ git diff --cached --name-only   ->  (vacio)
$ git diff --cached --stat        ->  (vacio)
$ git rev-parse :build.bat        ->  f7e076f3...
$ git hash-object build.bat       ->  f7e076f3...     <-- identico tras clean()
```

**`add -A` no puede colar un commit de 37 ficheros.** El filtro *clean* normaliza
LF→LF y el blob resultante **es el mismo objeto** que ya está en el índice.

> ⚠️ **El riesgo real es el inverso al temido.** El fix correcto **no produce ningún
> commit**: es una operación de árbol de trabajo. Si el orquestador lo planifica
> como "un commit que normaliza", **ese commit no va a existir**, y hay que decirlo
> antes de cerrar el ciclo, no después.

### 2.3 · Qué SÍ lo arregla (medido, en el clon, no en el repo real)

| Método | Resultado medido |
|---|---|
| `git add --renormalize .` | ❌ no-op, `w/lf` sigue |
| `git add -A` (el del wrapper) | ❌ staged vacío |
| `git checkout -- build.bat` | ✅ vuelve a `w/crlf` (39 CR) — pero **solo si git lo ve modificado** |
| `git checkout-index -f -- <fichero>` | ✅ **determinista**: fuerza la escritura desde el índice |

`checkout-index -f` es el que se usa: no depende de que git considere el fichero
"sucio", reescribe siempre desde el índice. Sobre la lista explícita de los 37, no
`-a` sobre todo el repo.

---

## 3 · ¿`: LF rompe de verdad `cmd.exe`? **No.** (MEDIDO)

La premisa operativa de la tarea: *"En Windows, scripts por lotes `.bat` en LF
pueden presentar fallos de parsing"*. Ejecutado, no supuesto.

**Banco 1 — el `build.bat` real, verbatim**, con un stub de `python.cmd` en `%PATH%`
que decide el resultado sin depender de PyInstaller:

```
=== lf   / compilacion OK   ===  EXITCODE=0    (salida identica)
=== crlf / compilacion OK   ===  EXITCODE=0
=== lf   / compilacion FALLA (stub sale 7)  ===  EXITCODE=1   (sale por el paso 1)
=== crlf / compilacion FALLA (stub sale 7)  ===  EXITCODE=1
```

**Banco 2 — los constructs que la premisa nombra**, `if errorlevel 1 (` multilínea
(`build.bat:14-19`), `if exist (…) else (…)` (`build.bat:30-39`) y `goto :label`:

```
--- LF ---   Paso1 OK / [ERROR] Fallo la compilacion. / [EXITO] Compilacion terminada.  EXITCODE=0
--- CRLF --- Paso1 OK / [ERROR] Fallo la compilacion. / [EXITO] Compilacion terminada.  EXITCODE=0
```

**Banco 3 — el caso duro**: `build.bat` **no termina en salto de línea** (último
byte `0x30`, la `0` de `exit /b 0`). Cuatro variantes (LF/CRLF × con/sin salto
final): **las cuatro ejecutan la última línea y devuelven lo mismo.**

**`cmd.exe` en este host no se rompe.** Por tanto la frase de `.gitattributes:20` —
*"Los ficheros que Windows NO tolera en LF se declaran al reves"* — es **falsa tal
como está escrita**. Es la cuarta vez en este repo que una justificación se
presenta como dogma y no como medición, y esta es la que manda: **la siguiente
persona que lea esa línea puede borrar las tres reglas `eol=crlf` creyéndolas
decorativas.**

### 3.1 · La decisión: (a), pero por el motivo correcto

El encargo ofrece dos salidas excluyentes. **Ambas parten de que hay algo que
normalizar, y no hay.** Aun así, si hay que elegir el destino del fichero:

**Se mantiene `(a)`: `*.bat` en CRLF.** No porque el parser se rompa —no se
rompe— sino porque `eol=crlf` es lo que hace el árbol de trabajo **determinista y
nativo de Windows**, y ya está declarado, ya funciona (§1.2) y ya se mide en §1.3.
Lo que hay que cambiar es **la razón**, no el destino.

**Y (b) —cambiar la política— queda descartada por el coste, no por laillianada:**
declarar `*.bat` en LF significa aceptar LF en el árbol de trabajo de Windows a
cambio de nada medible, y desalinearse de la convención nativa. Se cambia el
**texto** de la justificación (F2), que es donde está el falsehood.

---

## 4 · Lo que realmente sale de este ciclo

### F1 · Re-materializar los 37 ficheros del árbol local

`git checkout-index -f -- <los 37, explícitos>`.

- **Cero commits.** Cero cambios de índice. Es árbol de trabajo.
- **Es seguro**: para los 37, el índice es LF puro, luego el checkout reescribe
  exactamente lo versionado. No se pierde contenido comiteado.
- **Lo ejecuta el dev**, no el arquitecto, y **4 de los 37 están bajo
  `src/woptimizer/**`**, fuera del scope de planificación.
- **No se abre tarea para el drift de los 34 `w/crlf` bajo política LF**: en un
  clon salen `w/lf` (§1.2), o sea que también son residuo local. No es deuda viva.

### F2 · Corregir la justificación falsa de `.gitattributes` — **esto sí commitea**

Sustituir `«los ficheros que Windows NO tolera en LF»` por la medida de §3:
LF **funciona** en `cmd.exe` moderno para estos constructs (6 escenarios
idénticos), y CRLF se declara **por convención y determinismo del árbol**, no por
rotura del parser. Se **conservan** las tres reglas `eol=crlf`.

Es el único diff de contenido real que produce esta tarea, y es el que blinda la
política contra el siguiente que la borre por falta de fe.

### F3 · Guard de política EOL

**Por qué hace falta, medido:** el guard no protege el repo (el repo ya está bien),
protege **la regla**. `build.bat` vuelve a LF cada vez que un editor lo guarde así,
y ese cambio es **invisible para `git status` y para `add -A`** (§2.2): se pierde
en el checkout sin que nadie lo decida. Si además alguien quita las reglas `eol=crlf`
creyendo la justificación de `:20`, un clon futuro entrega `.bat` en LF y **nadie
lo nota hasta que algo raro pasa en un runner**.

**Por qué NO se construye sobre `git ls-files --eol` (la pregunta del encargo):**
en CI, `actions/checkout` hace un checkout fresco que **aplica los atributos**, así
que `git ls-files --eol` **reportará `w/crlf` esté o esté bien el repo**. Eso no es
un falso rojo: es un **verde falso**, que es la dirección peligrosa. El guard se
arma sobre **bytes**, que es lo único que no depende de cómo el runner hizo el
checkout.

**Sin PyYAML, sin `subprocess`, sin ventana.** `.gitattributes` se lee como **texto**
—no es YAML— y el escaneo es `rglob`. Encaja en `run_tests.py` sin tocar la
cámara de subprocesos que la deuda P1 ya declara sucia.

```
F3.1  test_la_politica_eol_cubre_todo_script_de_consola_que_existe
      (a) la regla base se DERIVA de .gitattributes y vale lf  (no constante)
      (b) toda extension de script de consola PRESENTE en el repo (.bat/.cmd/.ps1)
          tiene regla crlf efectiva; y el conjunto presente NO es vacio
      (c) bytes de cada uno: hay CRLF, y no hay ni un LF suelto
      (d) el contenido NORMALIZADO no lleva ningun CR  (la clase 3012c48)

F3.2  test_el_guard_de_eol_rechaza_lo_mismo_que_acepta     <- CONTRAPRUESTA
      camara en %TEMP% con el .gitattributes REAL y tres .bat sinteticos:
        uno CRLF        -> el evaluador dice OK
        uno LF          -> el evaluador dice FAIL
      y con la regla *.bat borrada, un .bat presente queda SIN cubrir -> FAIL
```

**Por qué F3.1 discrimina:** hoy `build.bat` tiene 0 CRLF, luego (c) falla; con F1
aplicado pasa. Falla por la aserción, no por no encontrar el fichero.

**Por qué F3.2 discrimina:** es lo que impide el patrón «una comprobación sin
contraprueba no es una comprobación» (ciclos 60 y 62, tercera y cuarta vez aquí).
Un evaluador que devolviera `OK` siempre daría `OK` en los tres escenarios y el
test muere. Sin F3.2, F3.1 se puede vaciar entero.

### F4 · 🔴 Absorber S3 (`STATUS.md:62`) — el único bug real de `build.bat`

`STATUS.md:62` declara, en rojo, que **`build.bat` sale con 0 aunque la compilación
falle**, y que **no hay guard**. Es el **mismo fichero** que toca esta tarea, es
**crítico** (un `.exe` roto llega por aquí) y su fix **agranda el `.bat`** con más
bloques `if errorlevel` — o sea, más código del que la justificación falsa decía
que era sensible a LF. Coherente absorberlo.

**Re-medido de forma independiente**, con un stub que **solo** falla en
`force_build.py` (PyInstaller presente → 0; compilación → 7):

```
build.bat en LF, compilacion fallida con 7  ->  EXITCODE=0     <-- confirmado
```

El guard es una **cámara**, no una sonda de texto: copia de `build.bat` + stub
`python.cmd` en `%PATH%` dentro de `%TEMP%`, exactamente como se midió aquí. Sin
PyInstaller, sin red, sin ventana.

```
F4.1  test_build_bat_propaga_el_codigo_de_salida_de_force_build
F4.2  test_la_camara_de_build_bat_detecta_la_regresion          <- CONTRAPRUESTA
```

> **Esto es un bloque separable.** Si el orquestador prefiere no mezclarlo, se
> corta F4 entero y la spec sigue valiendo: F1+F2+F3 no lo necesitan.

---

## 5 · Mutantes (para el `mutation-auditor` del ciclo 66)

| Id | Mutante | Quiere morir en | Por qué muere |
|---|---|---|---|
| **E1** | borrar la línea `*.bat text eol=crlf` de `.gitattributes` | F3.1 (b) | `build.bat` existe y su EOL efectivo pasa a `lf` por herencia de `*` → no está cubierto |
| **E2** | **`build.bat` a LF en disco** | F3.1 (c) | LF suelto sin `\r` antecedente. **Es el mutante vivo hoy** |
| **E3** | CR duro a mitad de línea en `build.bat` | F3.1 (d) | el normalizado conserva el `0x0D` → clase `3012c48` |
| **E4** | resolvedor de atributos reducido a constante | F3.2 | el `.bat` LF tiene que dar FAIL y no lo daría |
| **E5** | guard vaciado (`pass` / `return` temprano) | F3.2 | los tres escenarios dão `OK` y el test exige `FAIL` |
| **S1** | `build.bat` vuelve a `exit /b 0` incondicional | F4.1 | la cámara mide 0 donde exige != 0 |
| **S2** | cámara de F4 que acepta cualquier código | F4.2 | la contraprueba exige que la regresión vuelva a dar 0 |
| **S3** | `if errorlevel 1` de `build.bat:14` eliminado | F4.1 | el stub de PyInstaller ausente tiene que dar != 0 |

**Superviviente aceptable y declarado:** ninguno en seguridad ni datos. Si alguno
sobrevive, se arregla; no se documenta.

---

## 6 · Conteo de tests: efecto colateral obligatorio

`validate_docs.py` **deriva** el recuento con `ast` y lo ata a **cuatro** sitios.
Estado medido hoy: **150 OK, 0 FAIL**, con `220 tests = 155 backend + 65 headless`.

Al añadir F3 (2) y F4 (2), el recuento se mueve y **el validador pasa a rojo** si
no se actualizan a la vez:

- `run_tests.py` — nuevos `def test_*` **y** su invocación explícita al final, con
  el bloque de comentario `Suite: N -> N+k` y el reparto.
- `docs/ai/testing-guide.md` — **una fila por test definido** (el validador las cuenta).
- `STATUS.md:12`, `AGENTS.md:70`, `README.md:63` — el número **derivado**, no escrito a ojo.

> **El número se deriva y se escribe el que salga**, como en TASK-076: el encargo
  pidió 208 y eran 207 de verdad, y el dev escribió el real. Aquí se planifica
  **+4** y el dev escribe lo que `validate_docs.py` mida.

### 6.1 · D2 es una cita más equivocada (cuarta del patrón)

`STATUS.md:82` dice que hay *"tres «207» caducados en `STATUS.md:106`,
`docs/ai/testing-guide.md:57` y el badge de `README.md:6`"*. Medido:

| Lugar | D2 dice | Real |
|---|---|---|
| `STATUS.md:106` | `207` | línea 106 es la instrucción de leer `AGENTS.md`. La cifra vive en **`STATUS.md:12`** y dice **220** ✅ |
| `docs/ai/testing-guide.md:57` | `207` | dice **220** ✅ — ya no está caducado |
| `README.md:6` | `207` | badge `tests-207` ❌ **caducado de verdad** |
| `STATUS.md:109` | — | **`(207 tests)`** ❌ **caducado, y D2 no lo nombra** |

**De tres sitios, uno solo sigue caducado, y hay un cuarto que nadie cuento** —
justo el que se va a pisar otra vez al mover el contador. Se corrige en F2.

---

## 7 · Corrección de la cita de TASK-077

`tasks.json` dice *"DEUDA DE STATUS.md (fila 161)"*. **`STATUS.md` tiene 140 líneas.**
La deuda real está en **`STATUS.md:75`**, y su texto:

> **`build.bat` en LF (`TASK-077`, `pending`):** Tiene 39 LF y 0 CRLF pese a
> `.gitattributes eol=crlf`. Fix: `git add --renormalize .`. Verificable con
> `git ls-files --eol -- build.bat`.

Nótese que **`STATUS.md:75` no menciona `benchmark.py`**: esa mitad de la premisa
la añadió `tasks.json` por su cuenta, y es la que está mal (§0).

---

## 8 · Lo que este documento NO hace

- **No toca `src/woptimizer/**`.** Ni para normalizar bytes ni para nada.
- **No ejecuta `git add --renormalize`**, ni ningún commit de prueba, ni
  `git_safe_commit.py` desde la cámara de medición.
- **No invierte la política.** `*.bat` sigue en CRLF (F2 solo arregla el porqué).
- **No convierte `benchmark.py` a CRLF.** Doing so sería **crear** la violación.