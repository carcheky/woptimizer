# Informe de mutacion — ciclo 71 (TASK-090) — **RONDA 3**

**Que se ha auditado:** el guard (seccion (D) de `test_el_check_9_se_cablea_en_el_camino_real_del_validador`,
`run_tests.py:22278`) y el gate que vigila (check 11 de `validate_docs.py`, funcion
`_comprobar_veredictos_de_mutacion`, cuerpo desde `validate_docs.py:3205`), **despues de la ronda 4 del dev**
(commit `c94ef15`, `fix(validate): el gate comprueba sus cinco precondiciones y el guard las vigila (TASK-090)`).

**Que se ha medido:** 23 mutantes. Los 18 del catalogo de la ronda 2, **re-localizados por contenido** (las lineas
se movieron: `run_tests.py` 32208 -> 32435, `validate_docs.py` 3424 -> 3447), y **5 mutantes PROPIOS nuevos**
sobre lo que el dev escribio en la ronda 4 (el corpus ampliado de 10 sentinelas y 4 entradas de journal, las
cinco comprobaciones y las "cinco celdas que exigen el `[FAIL]` de SU razon").

**VERDICT: FAIL** — 19 MUERTO · 4 SOBREVIVIENTE · 0 NO MEDIDO.

Las 4 supervivientes son **mias** y son de la misma clase que las que la ronda 2 encontro: **ramas del gate
que el corpus del guard no ejercita**. Ninguna toca las cinco ramas que el dev arreglo: esas cinco ahora
muerden (M-102..M-106, que en la ronda 2 sobrevivieron, hoy mueren todos).

---

## 0. RESUMEN EJECUTIVO

| | ronda 2 (sobre `35478ec`) | **ronda 3 (sobre `c94ef15`)** |
|---|---|---|
| mutantes medidos | 18 | **23** |
| MUERTO | 13 | **19** |
| SOBREVIVIENTE | 5 | **4** |
| NO MEDIDO | 0 | **0** |
| linea base de la suite | verde (373 s) | **verde (rc=0, 279 s)** |
| donde estaban las 5 ramas | muertas (`validate_docs.py:3302/3308/3048/3360/3337`) | **vivas y mordidas** (`3325/3331/3067/3383/3360`) |

**Lo que el dev afirmaba y lo que he medido con MI aparejo:**

| afirmacion del dev | veredicto de esta auditoria |
|---|---|
| "los 18 mutantes del catalogo del ciclo 71 mueren (antes 13)" | **CIERTO**, medido con mi aparejo (no con el suyo): 18/18 MUERTO |
| "el gate comprueba sus cinco precondiciones" | **CIERTO**: las cinco ramas muerden (M-102..M-106) |
| "el recuento de tests sigue en 235 = 159 + 76" | **CIERTO**: `validate_docs.py` lo deriva con `ast` y lo dice: `235 tests definidos = 235 invocados` y `reparto 159 backend + 76 headless` |
| "el gate sigue dando 0 FAIL sobre los catalogos ya commiteados" | **CIERTO en el estado de HOY**, con un matiz: el check 11 cubre **1 entrada del journal (el ciclo 70) y 2 mutantes**, no los 23 de este ciclo, porque **`rd_journal.json` no tiene todavia la entrada del ciclo 71** (la escribe el orquestador al cerrar). El gate da 0 FAIL; los 2 FAIL que quedan son los preexistentes del residuo del ciclo 71, y no son del check 11 |

---

## 1. EL APAREJO (lo que hace la medicion creible)

**Camara desechable.** `%TEMP%\wopt_c71_r3_camara{1,2,3}`, copia con
`shutil.copytree(..., ignore=shutil.ignore_patterns(".git", "__pycache__"))`. El `.git` del repo es un
**FICHERO** de 57 bytes (`gitdir: C:/Users/carch/AppData/Local/woptimizer_git/.git`): medido en la copia,
**no viaja** (`.git presente? False`), luego la camara no puede descubrir el repo real por el puntero.

**Aislamiento, medido y no supuesto:**

```
git rev-parse --absolute-git-dir (entorno limpio) dentro de la camara
  -> C:/Users/carch/AppData/Local/Temp/wopt_c71_r3_camara1/.git     (la camara, NO el repo real)
git rev-parse --git-dir SIN GIT_DIR                                  -> rc=128, sin salida
remotos de la camara                                                -> (vacio)
```

**La camara lleva su PROPIA `.git`, un DIRECTORIO, sin remotos** (`git init` + `git add -A` + commit del
arbol mutado, rehecha por mutante). El entorno de la suite va **sin `GIT_DIR` ni `GIT_WORK_TREE`** (los dos
se limpian antes de cada corrida): con `GIT_DIR` en el entorno, la suite resuelve **otro** repositorio y
`_git_dir_absoluto_de_este_arbol` (`run_tests.py:6603`) muere antes de empezar. Con la `.git` propia, el
arbol queda **versionado y limpio** durante la corrida y el sha identifica **el arbol mutado**.

**La linea base es la puerta.** Sin mutar nada, la suite completa: `rc=0`, 279 s, `ALL TESTS PASSED.`
(log en `%TEMP%\wopt_c71_r3_logs\BASE.log`, log crudo en `BASE.log.crudo`). Sin esa base verde, ningun
mutante de esta tabla valdría.

**Purga de `__pycache__` entre mutaciones** (mismo byte-length + mismo segundo de mtime = `.pyc` obsoleto
= veredicto FALSO).

**El recorte del ruido asíncrono de Tk (instrumento, no mutante).** Los `after` de los tests de UI headless
se ejecutan cuando el interprete ya termino la suite y se imprimen **DESPUES** de `ALL TESTS PASSED.` (32
lineas de ruido en la base, lineas 369-400 de 400). Como el emisor recorta el log **por el final** y el gate
deriva del **final**, un log con ruido encima derivaria NO MEDIDO de un mutante que si se midio. El log que
se commitea se corta por donde acaba la salida de la suite; el **log CRUDO queda aparte** (`*.log.crudo`) y
el recorte solo elimina **grupos COMPLETOS** de 4 lineas de Tk, nunca una linea suelta.

**Una linea base roja habria convertido 23 logs en 23 logs sin valor.** Por eso va primera.

---

## 2. TABLA: mutante -> mutacion -> veredicto -> motivo LITERAL

Las 23 mutaciones se aplican **por contenido** (el `original` es el ancla y tiene que aparecer **exactamente
una vez**; si no, el mutante se aborta y no se mide). `asa` de las 23: `test_el_check_9_se_cablea_en_el_camino_real_del_validador`.

| mutante | donde | que rompe | veredicto | motivo LITERAL (ultima linea de la cola) |
|---|---|---|---|---|
| M-90 | `validate_docs.py:3205` | el CUERPO del gate vaciado (REGISTRO puesto) | **MUERTO** | `EL GATE NO DISTINGUE` |
| M-91 | `validate_docs.py:3350` | la comparacion del veredicto INVERTIDA | **MUERTO** | `EL GATE ACUSA EN LO QUE NO PUEDE` |
| M-92 | `validate_docs.py:3316` | el gate solo mira el PRIMER mutante del catalogo | **MUERTO** | `EL GATE NO DISTINGUE` |
| M-93 | `validate_docs.py:3350` | el veredicto se CALCULA y se TIRA | **MUERTO** | `EL GATE NO DISTINGUE` |
| M-94 | `validate_docs.py:3316` | el gate solo mira el ULTIMO mutante del catalogo | **MUERTO** | `EL GATE NO DISTINGUE` |
| M-95 | `validate_docs.py:3219` | el gate solo mira la PRIMERA entrada del journal | **MUERTO** | `EL GATE NO DISTINGUE` |
| M-96 | `run_tests.py:23026` | el corpus NO se monta | **MUERTO** | `EL GATE NO DISTINGUE` |
| M-97 | `run_tests.py:22750` | el sentinela COHERENTE deja de ser coherente | **MUERTO** | `EL GATE ACUSA EN LO QUE NO PUEDE` |
| M-98 | `run_tests.py:23170` | D3 NO restaura el esqueleto | **MUERTO** | `AssertionError: el validador del esqueleto tiene que quedar como estaba: una copia mutada contaminaria las secciones que vienen despues` |
| M-99 | `validate_docs.py:3350` | el gate decide por la DECLARACION y no por la EVIDENCIA | **MUERTO** | `EL GATE NO DISTINGUE` |
| M-100 | `validate_docs.py:3069` | el motivo literal de la evidencia ya no se comprueba | **MUERTO** | `EL GATE NO DISTINGUE` |
| M-101 | `validate_docs.py:3283` | el gate IGNORA el campo `veredictos` del journal | **MUERTO** | `EL GATE NO DISTINGUE` |
| M-102 | `validate_docs.py:3325` | el gate NO comprueba el sha de la linea | **MUERTO** | `EL GATE NO DISTINGUE` |
| M-103 | `validate_docs.py:3331` | el gate NO comprueba que el `asa` sea un test DEFINIDO | **MUERTO** | `EL GATE NO DISTINGUE` |
| M-104 | `validate_docs.py:3067` | el gate ACEPTA una evidencia cuyo frame es OTRO test | **MUERTO** | `EL GATE NO DISTINGUE` |
| M-105 | `validate_docs.py:3383` | el gate NO comprueba que el informe lleve las MISMAS lineas | **MUERTO** | `EL GATE NO DISTINGUE` |
| M-106 | `validate_docs.py:3360` | el gate NO acusa a un mutante del journal que no esta en el catalogo | **MUERTO** | `EL GATE NO DISTINGUE` |
| M-107 | `.taskmaster/veredicto.py:314` | el emisor vuelve a pisar la evidencia ajena | **MUERTO** | `AssertionError: el emisor NO puede reescribir la evidencia de un mutante que no se le ha pasado: la evidencia de M-3 ha cambiado.` |
| **M-108** | `validate_docs.py:3317` | **el gate NO acusa a un mutante del CATALOGO sin linea en el journal** | **SOBREVIVIENTE** | `ALL TESTS PASSED.` |
| **M-109** | `validate_docs.py:3219` | **el gate deja de mirar la entrada del ciclo 70 (`>` por `>=`)** | **SOBREVIVIENTE** | `ALL TESTS PASSED.` |
| **M-110** | `validate_docs.py:3435` | **el gate deja de comparar los DOS changelogs contra la evidencia** | **SOBREVIVIENTE** | `ALL TESTS PASSED.` |
| M-111 | `validate_docs.py:3325` | el sha se compara POR LONGITUD y no por valor | **MUERTO** | `EL GATE NO DISTINGUE` |
| **M-112** | `validate_docs.py:3383` | **el informe con lineas canonicas DE MAS pasa por sano** | **SOBREVIVIENTE** | `ALL TESTS PASSED.` |

Los shas por mutante estan en `mutaciones.json` (`sha_arbol_auditado`) y en las lineas canonicas: cada uno
es **el commit de la camara con el arbol MUTADO** que produjo esa evidencia (`git init` + `add -A` + commit
por mutante, en la `.git` propia de la camara).

**Los tres estados, con rigor:**

- **MUERTO (19):** el log esta en ROJO (`rc=1`), el test que murio es **exactamente** el `asa` declarado
  (verificado frame a frame, no de palabra) y el **motivo literal nombra la infraccion** (esta en la ultima
  linea de la cola, que es la linea que el gate lee).
- **SOBREVIVIENTE (4):** la suite **completa** termino en VERDE: `rc=0` y la ultima linea del log es
  `ALL TESTS PASSED.`.
- **NO MEDIDO (0):** ningun log cortado, ninguna muerte por excepcion, ningun test distinto del `asa` muerto,
  ninguna discrepancia entre dos corridas (una sola corrida por mutante, salvo donde se dice otra cosa).

**Tres implementaciones, un veredicto.** Cada estado se ha derivado con (1) mi propia implementacion,
(2) la del gate (`validate_docs._estado_de_una_corrida`) y (3) la del emisor (`.taskmaster/veredicto.py`).
**Las tres coinciden en los 23**; 0 discrepancias.

---

## 3. EL ESTADO DE LOS 5 SUPERVIVIENTES DE LA RONDA 2

La ronda 2 dio **FAIL** con 5 supervivientes, todos **ramas muertas DENTRO del gate** (`validate_docs.py`),
y dos de ellos tocaban **SEGURIDAD/DATOS**. La ronda 4 del dev las movio de sitio y las vivio. Medido aqui,
**con mi aparejo**:

| mutante | rama (ronda 2) | rama (ronda 3) | ronda 2 | **ronda 3** | quien lo mata |
|---|---|---|---|---|---|
| M-102 | sha (`3302`) | sha (`3325`) | SOBREVIVIENTE | **MUERTO** | la celda D1-bis del sha (`el mutante M-FIX-SHA cita el sha`) |
| M-103 | asa no definido (`3308`) | asa (`3331`) | SOBREVIVIENTE | **MUERTO** | la celda D1-bis del asa (`el asa declarada por M-FIX-ASA`) |
| M-104 | frame de otro test (`3048`) | frame (`3067`) | SOBREVIVIENTE | **MUERTO** | la celda D1-bis del frame (`el mutante M-FIX-FRAME esta declarado como MUERTO`) |
| M-105 | informe != journal (`3360`) | informe (`3383`) | SOBREVIVIENTE | **MUERTO** | la celda D1-bis del informe (`el bloque de maquina NO lleva las mismas lineas canonicas que el journal del ciclo 73`) |
| M-106 | id fuera del catalogo (`3337`) | catalogo (`3360`) | SOBREVIVIENTE | **MUERTO** | la celda D1-bis del catalogo (`declara el mutante M-FIX-FUERA, que NO esta en el catalogo`) |

**Las cinco están arregladas de verdad.** No es "el guard se ha endurecido": es que **las cinco ramas hacen
lo que dicen**. Y la asimetría que queda es la que mide mi M-111: **el sha se compara POR VALOR**, no por
longitud ni por prefijo (mutar eso a "por longitud" lo caza la celda D1-bis del sha: **MUERTO**).

---

## 4. LOS 5 MUTANTES PROPIOS NUEVOS (M-108..M-112)

Todos van contra **lo que el dev escribio en la ronda 4**. Los cinco estan **declarados** en
`mutaciones.json` con su ancla, su linea y su sha.

### M-108 — SOBREVIVIENTE — la rama del "mutante del catalogo sin linea en el journal"

`validate_docs.py:3317`: `if identificador not in por_mutante:` -> `if False and ...`.
La rama que acusa *"la entrada del ciclo N NO tiene linea canonica para el mutante X, que si esta en el
catalogo del cambio"*.

**Por que sobrevive:** el corpus del guard tiene **cuatro entradas de journal y cuatro+ catalogos** y
**todo mutante del catalogo tiene linea**. El unico caso que el corpus ejercita es el ESPEJO (M-FIX-FUERA:
linea en el journal, mutante que NO esta en el catalogo -> M-106), y ese si esta cubierto. **El espejo
faltante —el mutante del catalogo SIN linea en el journal— no esta en ningun sitio del corpus.**

**Consecuencia en el repo real (SEGURIDAD/DATOS):** con esa rama muerta, un mutante puede estar en
`mutaciones.json` **sin linea canonica en el journal** y el gate no lo acusa. Como el bloque de maquina del
informe tampoco tendria esa linea, el segundo testigo tambien la omitiria sin que nadie lo note: **un
veredicto puede desaparecer de la publicacion sin un solo FAIL**. Es la clase de fallo que el propio gate
dice perseguir ("el journal no puede ser el unico testigo de si un ciclo se cerro") y que aqui queda con un
solo testigo y sin acusacion.

### M-109 — SOBREVIVIENTE — el gate deja de mirar el ciclo 70

`validate_docs.py:3219`: `entradas = [e for e in journal if _ciclo_de(e) >= CICLO_ORIGEN_VEREDICTO]` ->
`> CICLO_ORIGEN_VEREDICTO`. `CICLO_ORIGEN_VEREDICTO = 70` (`validate_docs.py:2917`).

**Por que sobrevive:** el corpus pone su **primera entrada exactamente en el limite** (ciclo 70) y las
contradicciones en las siguientes (71, 72, 73). El unico sentinela del ciclo 70 es el COHERENTE, que el
guard comprueba por el silencio ("el gate CALLA sobre los coherentes"), no por su presencia: si la entrada
del ciclo 70 desaparece, no hay ninguna acusacion que la nombre y el silencio se cumple igual.

**Consecuencia en el repo real:** los veredictos del **ciclo 70 —el origen del contrato— dejan de
re-derivarse**. Su evidencia commiteada ya no se contrasta con nada, y una `.cola` corrupta o manipulada de
ese ciclo pasa sin que el check 11 se entere. Es un **corte de alcance por un caracter**.

### M-110 — SOBREVIVIENTE — los dos changelogs dejan de compararse con la evidencia

`validate_docs.py:3435`: `if m.group("estado") != estados[identificador]:` -> `if False and ...`.

**Por que sobrevive:** el check de changelogs solo comprueba las lineas cuyo mutante esta en `estados`, y
`estados` lo llena el gate **con los mutantes del corpus**. El changelog de la camara **no lleva lineas de los
sentinelas** (lleva las del repo: `M-3`, `M-A1`), luego esa rama no se ejercita **nunca** en el corpus.

**Consecuencia en el repo real:** la **copia legible** del veredicto —los dos changelogs— puede **contradecir
la evidencia commiteada** (un `MUERTO` donde la evidencia obliga a `SOBREVIVIENTE`) sin que el gate lo note.
El gate dice de si: *"Si NO lleva el bloque, no se dice nada: los dos anclajes del veredicto son el journal y
el informe"*. El changelog es la **tercera copia** y hoy no la vigila nadie.

### M-111 — MUERTO — el sha, por valor (y no por longitud)

`validate_docs.py:3325`: `sha_declarado != sha_del_catalogo` -> `len(sha_declarado) != len(sha_del_catalogo)`.
**MUERTO**, y con el motivo declarado: `EL GATE NO DISTINGUE` (la celda D1-bis del sha deja de encontrar el
`[FAIL]` que exige). Es el control positivo de esta tanda: **el guard SÍ sabe distinguir un sha mal
comparado**, asi que M-108/M-109/M-110 no son fallos del aparejo sino ramas que nadie exercita.

### M-112 — SOBREVIVIENTE — el informe con lineas DE MAS pasa por sano

`validate_docs.py:3383`: `if del_informe != del_journal:` -> `if del_informe - del_journal:`.

**Por que sobrevive:** la diferencia de conjuntos solo se queja de lo que **falta**; lo que **sobra** en el
informe no se acusa. El corpus tiene un caso de lineas que **no cuadran** (el sentinel del informe, con un
sha distinto) y por eso la celda D1-bis del informe se cumple; pero **no hay ningun caso de lineas de mas**.

**Consecuencia en el repo real:** el segundo testigo puede **anadir** lineas canonicas que el journal no
respalda —un veredicto publicado en el informe y en los changelogs que ninguna evidencia sostiene— y el gate
no lo acusa. La comparacion correcta es de conjuntos completos (`!=`), no de diferencia unilateral.

---

## 5. LAS 4 SUPERVIVIENTES: lo que necesitan

| mutante | rama muerta | por que no la ve el guard | arreglo que necesita (NO lo aplico: es del dev) |
|---|---|---|---|
| M-108 | `validate_docs.py:3317` (`identificador not in por_mutante`) | el corpus no tiene un mutante del catalogo SIN linea en el journal | **anadir al corpus un sentinel con linea en el journal y SIN entrada en el catalogo** (el espejo de M-FIX-FUERA) y exigir su `[FAIL]` con su razon |
| M-109 | `validate_docs.py:3219` (`>= CICLO_ORIGEN_VEREDICTO`) | la entrada del ciclo 70 es la primera y el guard solo comprueba su SILENCIO, no su presencia | **exigir que el gate haya mirado la entrada del ciclo 70** (p. ej. que el REGISTRO declare `entradas cubiertas=N` con N = las entradas del corpus) |
| M-110 | `validate_docs.py:3435` (changelogs contra la evidencia) | el corpus no pone lineas canonicas de sentinelas en los changelogs | **meter en el changelog del corpus la linea canonica de un sentinel con estado DISCREPANTE** y exigir el `[FAIL]` |
| M-112 | `validate_docs.py:3383` (`!=` -> `-`) | el corpus no tiene un informe con lineas DE MAS | **meter en el corpus un informe con una linea canonica de mas** y exigir el `[FAIL]` de "las mismas lineas" |

Las cuatro son **del mismo tipo**: no son fallos del gate, son **huecos del corpus**. Por eso el arreglo es
**en el guard (mas sentinelas)**, no en el gate. Las cuatro son de la clase "el gate vigila un caso y el
guard vigila otro" que la ronda 2 ya encontro cinco veces: **el patron se repite**.

**Severidad.** M-108 y M-112 tocan **el contenido de lo que se publica** (un veredicto puede desaparecer
del conjunto publicado, o aparecer sin evidencia que lo respalde): los marco como **SEGURIDAD/DATOS** en el
sentido del contrato (un agujero con la etiqueta de "medido" es peor que un agujero sin etiqueta).
M-109 y M-110 son de **alcance y de copia legible**: M-109 deja un ciclo entero (el del origen del contrato)
sin re-derivar, M-110 deja la tercera copia sin vigilar.

---

## 6. NO MEDIDO

**Ninguno.** Los 23 mutantes tienen veredicto firme:

- **Ningun log cortado**: los 23 logs terminan en la linea del veredicto de la suite (la del fallo con su
  traza, o `ALL TESTS PASSED.`), y el rc lo puso el runner en la primera linea (`RC=N`), no inferido.
- **Ninguna muerte por excepcion**: el test que murio es el `asa` en los 19 MUERTO (verificado por el frame).
- **Ninguna discrepancia**: una sola corrida por mutante y las tres implementaciones de derivacion coinciden.
- **La linea base es verde**: sin eso, la tabla entera no valdria.

Los 4 NO MEDIDO que la ronda 2 temia no existen: **las cinco ramas del gate estan vivas y las cinco muerden**.

---

## 7. LAS CITAS: MEDIDAS POR CONTENIDO, NO POR EL NUMERO DECLARADO

El desplazamiento de la ronda 4, medido con `git` (padre `5fed36a` -> `c94ef15`):

```
run_tests.py            +240 / -13   -> neto +227   (32208 -> 32435 lineas)
validate_docs.py        +32  / -9    -> neto +23    (3424  -> 3447 lineas)
docs/ai/testing-guide.md +7  / -5    -> neto +2
STATUS.md               (SIN TOCAR)
```

**Todo lo que esta por debajo de la zona editada se movio +227.** Las cuatro afirmaciones de
`sandbox-rules.md:55-56` que el guard vigila estan vivas: `validate_docs.py:1429`, `validate_docs.py:1924`,
`run_tests.py:23945` (renumerada por el dev) y `docs/ai/sandbox-rules.md:1133`.

**El conjunto de citas del ciclo 71 (las 8 de la tabla B del informe de la ronda 2), medido por contenido:**

| cita | donde se escribe | destino REAL hoy | estado | de quien es la rotura |
|---|---|---|---|---|
| `run_tests.py:23718` | `run_tests.py:24259` | `23945` (`...POR NUMERO DE LINEA`) | **ROTA** | **del dev** (`c94ef15`, +227) |
| `run_tests.py:23718` | `STATUS.md:107` | `23945` | **ROTA** | **del dev** (`c94ef15`, +227; `STATUS.md` no lo toco) |
| `run_tests.py:29604` | `STATUS.md:107` | `29831` (`def test_las_citas_de_sandbox_rules_siguen_siendo_ciertas():`) | **ROTA** | **del dev** (`c94ef15`, +227) |
| `run_tests.py:30032` | `STATUS.md:89` | `30259` (`def _delitos_de_enumeracion(arbol):`) | **ROTA** | **del dev** (`c94ef15`, +227) |
| `run_tests.py:23718` | `run_tests.py:29836` | `23945` | VIVA | renumerada por el dev |
| `run_tests.py:29604` | `docs/ai/testing-guide.md:1364` | `29831` | VIVA | renumerada por el dev (la fila esta en 1364, no en 1362: `testing-guide.md` +2) |
| `run_tests.py:23627` | `run_tests.py:29851` | `23943` | VIVA | renumerada por el dev |
| `run_tests.py:30001` | `validate_docs.py:1435` | `12749` (`def test_dead_code_ast_guard():`) | VIVA | renumerada por el dev |

**Cuentas: 4 vivas / 4 rotas del conjunto del ciclo 71, y las 4 rotas son del dev** (la ronda 4 movio los
destinos +227 y renumero 4 de las 8 citas, pero no las 3 de `STATUS.md` ni la del docstring de
`run_tests.py:24259`). **La cita de `docs/ai/testing-guide.md:1382` a `run_tests.py:23605` NO es una cita
rota**: es una cita **autolimitada** y lo dice de su propio texto ("el `23605` es la linea de la CAMARA, no
la del repo"). Y `run_tests.py:23133` (citada en `.taskmaster/CHANGELOG.md:71`) esta viva **por casualidad**:
en el padre el stub estaba en `22907` y el +226 lo ha vuelto a poner en `23133`; no es un arreglo, es una
coincidencia de numeracion.

Ademas, **una cita rota preexistente** que no es de este ciclo:
`openspec/changes/2026-10-19-verificacion-ui-alcance-derivado/mutation-report.md:269` cita
`run_tests.py:23718` para `REGISTRO_INDECISAS`, que hoy esta en `run_tests.py:25284`. Es de un cambio
**cerrado** y no lo arregla nadie desde entonces.

**Esto NO lo vigila ningun guard**: el unico guard de citas (`test_las_citas_de_sandbox_rules_siguen_siendo_ciertas`,
`run_tests.py:29831`) mira **cuatro** afirmaciones concretas (las de `sandbox-rules.md:55-56`) y nada mas.
Las 4 rotas que quedan son, otra vez, **dato derivado escrito a mano**.

---

## 8. LO QUE ESTA Y LO QUE NO ESTA RESUELTO

**Resuelto y medido:** las cinco ramas del gate que la ronda 2 dejo muertas estan vivas y **muerden**; el
guard de la ronda 4 (10 sentinelas, 4 entradas de journal, 5 celdas con su propia razon) detecta las cinco;
el sha se compara por valor; el emisor ya no pisa la evidencia ajena; el recuento de tests es el declarado
(235 = 159 + 76) y el check 11 da 0 FAIL.

**Sin resolver (4 ramas, todas del gate, ninguna vista por el corpus):** M-108, M-109, M-110 y M-112. Cada
una con su metrica de arriba y con el arreglo en el **corpus del guard**, no en el gate.

**Un apunte de alcance que el orquestador tiene que tener en cuenta:** el check 11, en el estado del repo de
hoy, cubre **1 entrada del journal (el ciclo 70) y 2 mutantes**, porque **`rd_journal.json` no tiene todavia
la entrada del ciclo 71**. En cuanto el orquestador copie estas 23 lineas canonicas al journal (campo
`veredictos`) y al changelog del ciclo 71, el gate empezara a re-derivar estos 23 mutantes **contra las 23
`.cola` que quedan commiteadas aqui**. Si las lineas del journal y las del bloque de maquina de este informe
no coinciden exactamente, el gate acusara el bloque de maquina (`validate_docs.py:3383`): **las lineas de
este informe tienen que ser byte a byte las que se copien al journal**.

---

## 9. BLOQUE DE MAQUINA

<!-- WOPT_VEREDICTOS -->
WOPT_VEREDICTO M-90 MUERTO b88b2ae33530
WOPT_VEREDICTO M-91 MUERTO c5247b8fc599
WOPT_VEREDICTO M-92 MUERTO 92d44a408dcb
WOPT_VEREDICTO M-93 MUERTO d7d2b995d878
WOPT_VEREDICTO M-94 MUERTO b0b968047ccd
WOPT_VEREDICTO M-95 MUERTO 3973606dc7dd
WOPT_VEREDICTO M-96 MUERTO 89ddcc7d268a
WOPT_VEREDICTO M-97 MUERTO 074778d2956a
WOPT_VEREDICTO M-98 MUERTO 1dd1e558bce0
WOPT_VEREDICTO M-99 MUERTO ebe692afd206
WOPT_VEREDICTO M-100 MUERTO 0f8030d69dda
WOPT_VEREDICTO M-101 MUERTO 9144057b0b38
WOPT_VEREDICTO M-102 MUERTO f3e94843d979
WOPT_VEREDICTO M-103 MUERTO 309ae523826c
WOPT_VEREDICTO M-104 MUERTO fe09da634cd0
WOPT_VEREDICTO M-105 MUERTO f70bd036c768
WOPT_VEREDICTO M-106 MUERTO 41986f08d7f7
WOPT_VEREDICTO M-107 MUERTO e5f02d611e7c
WOPT_VEREDICTO M-108 SOBREVIVIENTE 64881b8b6317
WOPT_VEREDICTO M-109 SOBREVIVIENTE 4e0d8d6cad47
WOPT_VEREDICTO M-110 SOBREVIVIENTE 97b380f3f6f8
WOPT_VEREDICTO M-111 MUERTO 7ab54a5181a7
WOPT_VEREDICTO M-112 SOBREVIVIENTE 46b3e095b4d9
<!-- /WOPT_VEREDICTOS -->

---

## 10. QUE SE ESCRIBIO EN EL REPO (y que NO)

**Escrito (lo unico permitido):**

- `openspec/changes/2026-10-22-el-gate-distingue-o-falla/mutaciones.json` — 23 mutantes con `id`, `asa`,
  `motivo`, `mutacion` (`fichero`, `linea` REAL, `original`, `sustituto`), `sha_arbol_auditado` y `origen`.
- `openspec/changes/2026-10-22-el-gate-distingue-o-falla/evidencia/*.cola` — 23 ficheros, escritos por
  `.taskmaster/veredicto.py` (no a mano).
- `openspec/changes/2026-10-22-el-gate-distingue-o-falla/mutation-report.md` — este informe.

**NO escrito:** ni un commit, ni el journal, ni los changelogs, ni `validate_docs.py`, ni `run_tests.py`, ni
`STATUS.md`. **El orquestador copia las 23 lineas de §9 al journal (campo `veredictos`) y a los dos
changelogs.**

**NO tocado el repo real:** las tres camaras vivieron en `%TEMP%`, con su propia `.git` y sin `GIT_DIR` en el
entorno. La prueba esta en §11.

---

## 11. PRUEBA DE NO-CONTAMINACION

```
$ git log --oneline -1
c94ef15 fix(validate): el gate comprueba sus cinco precondiciones y el guard las vigila (TASK-090)

$ git status --porcelain
 M openspec/changes/2026-10-22-el-gate-distingue-o-falla/evidencia/M-90.cola   ... M-107.cola
 M openspec/changes/2026-10-22-el-gate-distingue-o-falla/mutaciones.json
 M openspec/changes/2026-10-22-el-gate-distingue-o-falla/mutation-report.md
?? openspec/changes/2026-10-22-el-gate-distingue-o-falla/evidencia/M-108.cola  ... M-112.cola
(25 lineas: SOLO los tres artefactos de esta auditoria. Ni una linea de codigo.)

$ git diff --stat
 ... 18 .cola + mutaciones.json + mutation-report.md | 841 insertions(+), 418 deletions(-)
(sin cambios de codigo: solo los tres artefactos)

$ git diff --cached --stat
(vacio: no hay nada en el indice, y NO se ha hecho ningun commit)

$ git rev-parse --git-dir
C:/Users/carch/AppData/Local/woptimizer_git/.git      (el repo real, desde la raiz del proyecto)
```

**Confesion de instrumentacion (por si acaso):** dos scripts auxiliares mios (`cmp.py`, `fixrep.py`) se
quedaron un momento en la raiz del repo por un `cd` mal puesto; los he borrado (a la papelera) y el estado
de arriba es el estado FINAL. **No se ha tocado ni un fichero de codigo del repo real, ni el journal, ni los
changelogs, ni `STATUS.md`.**

La prueba de que las camaras no tocaron el repo: dentro de la camara,
`git rev-parse --absolute-git-dir` (entorno **sin** `GIT_DIR` ni `GIT_WORK_TREE`) devuelve
`C:/Users/carch/AppData/Local/Temp/wopt_c71_r3_camaraN/.git`, **no** el repo real; y el `.git` de 57 bytes
del proyecto **no viaja** en la copia (`ignore_patterns(".git")` lo excluye como FICHERO, que es lo que es).
Ninguna camara ha hecho `git add -A` ni `commit` contra el arbol real: el `add -A` de cada mutante se hizo
con `GIT_DIR` = la `.git` de la camara y `GIT_WORK_TREE` = la camara.

---

## 12. VERDICT

**VERDICT: FAIL**

23 mutantes medidos con aparejo propio: **19 MUERTO · 4 SOBREVIVIENTE · 0 NO MEDIDO**.

El FAIL **no es** por el arreglo del dev: **las cinco ramas que la ronda 2 dejo muertas ahora mueren todas**
(M-102..M-106) y las 18 del catalogo mueren las 18. El FAIL es por **cuatro ramas nuevas que mi aparejo
encuentra y el corpus del guard no cubre** (M-108, M-109, M-110, M-112), las cuatro del mismo tipo: un
comportamiento del gate que **nadie mira**. Dos de ellas (M-108, M-112) permite que **lo que se publica se
desincronice de la evidencia sin un solo FAIL**.

**Lo que hay que hacer (es del `openspec-dev`, no mio):** ampliar el **corpus del guard** con cuatro
sentinelas mas —el mutante del catalogo sin linea en el journal, la entrada del ciclo 70, los changelogs con
una linea discrepante, y el informe con una linea de mas— y exigir el `[FAIL]` de cada razon. Con eso, estas
cuatro ramnas pasan a muerte y el FAIL de la ronda 3 se cierra con otra ronda.
