# Informe de mutacion del ciclo 70 — el killer-check del veredicto (TASK-087)

> **Quien escribe esto:** la parte del **Paso 3** (el dev) del ciclo 70, con el
> caso real **M-3** medido en camara. El **Paso 4** (`mutation-auditor`) escribe
> **su** informe en este mismo fichero cuando audite los fixes de este ciclo, y
> **sustituye** el `mutaciones.json` del cambio por el del ciclo (el catalogo es
> **del ciclo**: si el cambio ya traia uno de otra vuelta, se sustituye, no se
> amplia).
>
> El **bloque de maquina** del final es lo que el gate lee: las lineas
> canonicas del veredicto. Si el Paso 4 escribe otras lineas, el bloque tiene
> que llevar **esas**, no estas.

## 0. Que se cierra en este ciclo

MEDIDO por el arquitecto en camara desechable, antes de este ciclo:

| Qué se borra | Qué pasa |
|---|---|
| el **veredicto** del journal | **0 FAIL** |
| el **`mutation-report.md`** entero | **0 FAIL** |
| una **fila** del journal | 1 FAIL |

O sea: la fila estaba vigilada, **el veredicto y el informe no**. El agujero no
era el mecanismo, era el **conjunto de sujetos**: no era derivable, luego se
podia vaciar sin que nadie lo notase.

Ademas el veredicto **no tenia tres estados** ni «asa esperada»: `agent.md:116`
solo decia `killed`/`survived`, y el instrumento real del auditor sacaba
rc/bytes/ultima linea, **no el nombre del test que murio**.

## 1. Lo que hay ahora

| Pieza | Fichero | Que hace |
|---|---|---|
| Emisor | `.taskmaster/veredicto.py` | del catalogo + las colas de los logs, deriva el estado y escribe la linea canonica |
| Gate | `validate_docs.py`, check 11 | **re-deriva** cada veredicto desde la evidencia commiteada y falla si no cuadra |
| Catalogo | `openspec/changes/<id>/mutaciones.json` | lo declara **quien muta**: el `asa` y el `motivo` |
| Evidencia | `openspec/changes/<id>/evidencia/<mutante>.cola` | la cola del log, commiteada |

La linea canonica:

```
WOPT_VEREDICTO <mutante> <MUERTO|SOBREVIVIENTE|NO MEDIDO> <sha>
```

## 2. El caso real: M-3 (el reloj de la fixture sin clavar)

**La mutacion** (la real del ciclo 69, `run_tests.py:23459-23460`): la fixture
deja de clavar la fecha del commit, luego el sha de la fixture varia y el hash
MUERTO puede coincidir con un objeto real.

```python
# original
    for v in variables:
        os.environ[v] = fecha_iso
# sustituto
    for v in variables:
        os.environ.pop(v, None)
```

**El `asa` declarada** (la declara quien muta, en el catalogo):
`test_el_pre_vuelo_de_un_hash_muerto_distingue_existe_de_no_existe`.
**El `motivo` declarado**: `EL RELOJ DE LA FIXTURE NO ESTA CLAVADO`.

**Las cuatro corridas REALES** (camara nueva de este ciclo, con el indice del
repo real replicado, sha del arbol auditado `e8111158`; cada corrida, la
suite COMPLETA: 200,9 s / 206,8 s / 208,2 s) y lo que diede cada una:

| Corrida | rc | Que murio | Motivo literal | Veredicto de la corrida |
|---|---|---|---|---|
| 1 | 1 | `test_el_pre_vuelo_de_un_hash_muerto_distingue_existe_de_no_existe` | `... y el commit REAL lleva 1792663532 s: EL RELOJ DE LA FIXTURE NO ESTA CLAVADO` | MUERTO |
| 2 | 1 | `test_el_hash_muerto_se_deriva_por_construccion_y_no_por_concatenacion` | `el sha de la fixture (ba26b819...) tiene que tener '0' en la 8.a cifra hexadecimal` | NO MEDIDO |
| 3 | 1 | `test_el_hash_muerto_se_deriva_por_construccion_y_no_por_concatenacion` | `el sha de la fixture (752f585d...) tiene que tener '0' en la 8.a cifra hexadecimal` | NO MEDIDO |
| 4 | 1 | `test_el_hash_muerto_se_deriva_por_construccion_y_no_por_concatenacion` | `el sha de la fixture (aec78c1e...) tiene que tener '0' en la 8.a cifra hexadecimal` | NO MEDIDO |

**El veredicto del mutante: NO MEDIDO.** Una corrida muere por el **asa**
(el pre-vuelo, con el motivo que nombra la infraccion) y tres mueren por el
**tripwire** (motivo probabilistico de la 8.ª cifra), luego las cuatro NO
coinciden. Un mutante no determinista no puede aportar la muerte de un
mutante: repetir la medicion N veces SIN exigir consistencia hace la
probabilidad de veredicto falso MAS ALTA (`1-(1-p)^N`: con p=1/16, N=3 ->
17,6 %, N=5 -> 27,5 %), y exigir consistencia cuesta N Suite (N=3 -> 2 205 s
por mutante) sin tapar el agujero de fondo.

**La distribucion es la misma que la del ciclo 69** (1 de 4 en el pre-vuelo y
3 de 4 en el tripwire), con lo que la reproduccion confirma el hallazgo.

**Esto es lo que MATA K-6** (el gate que solo mira «el log esta rojo»): con el
log en ROJO y sin mirar el asa, el gate daria MUERTO. La verdad es NO MEDIDO.

## 3. El gate NO se puede vaciar (AC-7), en camara

Cada celda monta una camara NUEVA (copia del repo, sin `.git`), deja el arbol
en el estado que la celda describe, y corre `validate_docs.py` AHI. El
conjunto de sujetos lo pone el journal (una entrada del ciclo 70 con su
campo `change` y sus lineas canonicas), y el `## CYCLE-070` de los dos
changelogs, como los escribe el orquestador al cerrar el ciclo.

| Celda | Estado | Resultado |
|---|---|---|
| (d) | todo en su sitio | **0 FAIL** y el REGISTRO: `entradas cubiertas=1, mutantes re-derivados=1` |
| (a) | borrar **una** linea canonica del journal | **2 FAIL**: `la entrada del ciclo 70 NO tiene linea canonica para el mutante M-3` + `el bloque de maquina NO lleva las mismas lineas canonicas que el journal` |
| (b) | borrar el `mutation-report.md` | **1 FAIL**: `mutation-report.md: NO EXISTE. El informe del ciclo es el segundo testigo del veredicto` |
| (c) | el filtro de epoca se queda en el futuro (conjunto VACIO) | **0 FAIL**, el REGISTRO dice `entradas cubiertas=0, mutantes re-derivados=0` y **no hay ninguna linea de `[OK]` del check 11**: no hay verde por omision |

El (c) es el que importa: sin el, un gate sin sujeto se leeria como un gate
que lo comprobo todo.

## 4. Los mutantes del gate (K-1..K-7)

Metodologia: DOS celdas por mutante, con control positivo. La celda **SANO**
es el gate sin mutar con el estado que el mutante dejaria pasar; la celda
**MUTADO** es el gate (o el emisor) con la mutacion aplicada y el MISMO
estado. Si el mutante se cuela, el estado pasa de FAIL a SIN FAIL: ese par es
la prueba de que la guarda que lo pilla es ESA.

| id | Que rompe | Que lo pilla | Motivo literal de la muerte | Veredicto |
|---|---|---|---|---|
| **K-1** | el emisor dice MUERTO porque el log esta rojo, sin mirar el asa | el gate re-deriva desde la evidencia | `el mutante M-3 esta declarado como MUERTO y la evidencia commiteada obliga a NO MEDIDO (dos corridas del mismo mutante dan veredictos distintos)` | **MUERTO** |
| **K-2** | la gramatica acepta cualquier cosa (`match` en vez de `fullmatch`) | la gramatica estricta | `la entrada del ciclo 70 tiene una linea de veredicto que NO obeyece la gramatica: 'WOPT_VEREDICTO M-3 NO MEDIDO <sha> (con coletilla)'` | **MUERTO** |
| **K-3** | el asa se compara por prefijo | la igualdad EXACTA | `el mutante M-3 esta declarado como NO MEDIDO y la evidencia commiteada obliga a MUERTO (murio test_el_pre_vuelo_..._Y_UNO_MAS ...)` | **MUERTO** |
| **K-4** | se cae el chequeo del motivo | el substring del motivo literal | `... y la evidencia commiteada obliga a MUERTO (murio test_el_pre_vuelo_... por su asercion)` | **MUERTO** |
| **K-5** | el asa declarado no tiene que existir en la suite | el `ast` sobre `run_tests.py` | `mutaciones.json: el asa declarada por M-3 (test_que_no_existe_en_la_suite) NO es un test definido en run_tests.py` | **MUERTO** |
| **K-6** | el gate solo mira «el log esta rojo» (el caso REAL M-3) | el asa y el motivo | `el mutante M-3 esta declarado como NO MEDIDO y la evidencia commiteada obliga a MUERTO` | **MUERTO** |
| **K-7** | el filtro de epoca se deja en un futuro y el gate no ve a nadie | el REGISTRO | `REGISTRO entradas cubiertas=0, mutantes re-derivados=0` + **ninguna** linea de `[OK]` del check 11 | **MUERTO** (no verde por omision) |

Los siete se matan. **K-1** y **K-6** son los que importan: los dos son el
mismo agujero (confiar en el ROJO) medido desde los dos lados, y los dos caen
con el corpus REAL de M-3.

## 5. Los costes medidos

| Que | Coste MEDIDO | Presupuesto |
|---|---|---|
| **el emisor** (`.taskmaster/veredicto.py`) | **7,1 ms** para 13 mutantes (escribe 13 evidencias y 13 lineas) | ≤ 10 ms por ciclo |
| **el gate** (check 11) con el arbol ya parseado | **10,2 ms** (min) / 10,4 ms (mediana) de 5 corridas | ≤ 0,5 % de 11,28 s = 56 ms |
| **el gate** por diferencia de dos validadores enteros | **-30 ms**, o sea **por debajo del ruido** de la medicion | idem |
| **el gate EN FRIO** (con el `ast.parse` dentro) | 3 713 ms | el parseo lo pagaba el validador DOS veces (11 401 ms); con la cache por contenido, **UNA** |
| **el validador entero** | de **11 401 ms** a **~4 350 ms** | — |
| **correridas extra de la suite** | **0** | 0 |

El `ast.parse` de `run_tests.py` (1,64 MB) cuesta **3 459 ms** y el validador lo
pagaba dos veces (el recuento y el reparto). El gate necesita el arbol para
comprobar que el `asa` existe, luego con una cache por contenido el parseo se
paga **una** vez y el gate no paga el arbol: su coste marginal son los **10,2
ms** de leer el journal, el catalogo y las 13 evidencias y re-derivar los 13
veredictos.


<!-- WOPT_VEREDICTOS -->
WOPT_VEREDICTO M-3 NO MEDIDO e811115886a8de68bbcd338c11aaa426477caeb5
<!-- /WOPT_VEREDICTOS -->

---

## 6. AUDITORÍA DEL `mutation-auditor` — ciclo 70 (TASK-087)

**Sherlock**, 2026-10-22. Auditoría demutación del fix `f5bec54` ("el veredicto de
mutación se vuelve comprobable"): el **emisor** (`.taskmaster/veredicto.py`) y el
**gate** (check 11 de `validate_docs.py`).

### 6.0 Las reglas con las que he medido (y por qué hacen falta)

1. **Cámara desechable en `%TEMP%`**, copia del repo **sin** `.git`. Este repo
   tiene el `.git` como **FICHERO puntero** de 57 bytes (`gitdir: …`), y
   `robocopy /XD .git` **no** lo excluye: lo excluye `shutil.ignore_patterns`
   (cubre ficheros y directorios). El aislamiento se **comprueba antes de mutar
   nada**: `git rev-parse --git-dir` con un `GIT_DIR` desechable tiene que
   devolver una ruta **dentro** de la cámara. En todas las cámaras: `GIT_DIR`
   desechable y explícito, nunca descubierto.
2. **Cero escrituras en el repo real.** Ancla antes y después: `HEAD` =
   `f5bec54db57e65295ee4870afefbf6a8a0988c94`, `git status --porcelain` vacío,
   y la entrada más nueva del reflog sigue siendo el commit del dev (317
   entradas, ninguna mía). **Nada commiteado**: lo versiona el orquestador.
3. **Dos celdas por mutante del gate**, sobre el MISMO estado: **SANO** (el gate
   sin mutar tiene que FALLAR: la guarda existe) y **MUTADO** (con la mutación,
   ese FAIL tiene que **desaparecer**: la guarda discriminaba). Si el FAIL
   sigue, el mutante **se cuela**. Los mutantes del **emisor** se miden al revés:
   el emisor mutado emite su línea y el gate tiene que **cazarla**.
4. **Una muerte por sintaxis rota, `NameError` o `FileNotFoundError` NO es
   veredicto.** Todo rojo de una celda se ha leído: el motivo literal nombra la
   infracción o la celda es **NO MEDIDO**.
5. Las dos líneas sensibles (`run_tests.py:23133` y `validate_docs.py:1429`)
   **MEDIDAS y vigentes**; ninguna mutación las desplaza (todas las mutaciones
   del gate están por debajo de `validate_docs.py:2800`, y ninguna toca
   `run_tests.py`).

### 6.1 La tabla de mutantes

| id | qué rompe | cómo lo maté | veredicto |
|---|---|---|---|
| **K-1** | el emisor dice MUERTO porque el log está rojo, sin mirar el asa | emisor mutado (2 condiciones) → emite MUERTO → el gate lo caza (3 FAIL) | **MUERTO** |
| **K-2** | la gramática acepta cualquier cosa (`match` en vez de `fullmatch`) | línea malformada en las 3 piezas → SANO 4 FAIL / MUTADO 0 | **MUERTO** |
| **K-3** | el asa se compara por prefijo | evidencia con el asa+`_Y_UNO_MAS` → SANO 3 FAIL / MUTADO 0 | **MUERTO** |
| **K-4** | se cae el chequeo del motivo | evidencia que muere por el asa sin el motivo → SANO 3 FAIL / MUTADO 0 | **MUERTO** |
| **K-5** | el asa declarado no tiene que existir en la suite | asa inexistente → SANO 1 FAIL / MUTADO 0 | **MUERTO** |
| **K-6** | el gate solo mira «el log está rojo» | corpus **real** de M-3 → SANO 3 FAIL / MUTADO 0 | **MUERTO** |
| **K-7** | el filtro de época se deja en un futuro (999) | base → 0 FAIL, pero el REGISTRO dice `entradas cubiertas=0` y **no** hay `[OK]` del check 11 | **MUERTO** (no verde por omisión) |
| **K-8** | **`validar()` deja de llamar al check 11** | base → **0 FAIL y SIN REGISTRO**: el guard desaparece y **nada lo nota** | ⚠️ **SOBREVIVIENTE** |
| **K-9a** | el campo `change` apunta a otro sitio | → 1 FAIL (el directorio no existe) | **GUARDA VIVA** |
| **K-9b** | la entrada no declara `change` | → 1 FAIL | **GUARDA VIVA** |
| **K-9c** | el gate deja de recorrer las entradas | → 0 FAIL, pero el REGISTRO dice `mutantes re-derivados=0` | **MUERTO** (visible) |
| **K-10a** | la evidencia está recortada antes del frame | → 3 FAIL (la evidencia obliga a NO MEDIDO) | **GUARDA VIVA** |
| **K-10b** | **el frame del traceback es de otro fichero** | evidencia fabricada con `File "…\otro_fichero.py"` → **0 FAIL** | ⚠️ **GUARDA MUERTA** |
| **K-11** | el cross-check de los changelogs no compara el estado | changelog con MUERTO y evidencia NO MEDIDO → SANO 2 FAIL / MUTADO 0 | **MUERTO** |
| **K-12** | **el sha del árbol auditado no existe en ningún repo** | sha inventado (`deadbee000…`) en las 3 piezas → **0 FAIL** | ⚠️ **GUARDA MUERTA** |
| **K-14** | un mutante fuera del catálogo no se acusa | → SANO 1 FAIL / MUTADO 0 | **MUERTO** |
| **K-15** | el bloque del informe no tiene que llevar las mismas líneas | → SANO 1 FAIL / MUTADO 0 | **MUERTO** |
| **K-17** | el emisor declara MUERTO si **alguna** corrida muere por el asa | emisor mutado → emite MUERTO → el gate lo caza (3 FAIL) | **MUERTO** |

**Catorce de dieciséis mueren por su aserción.** Los dos que no, y las dos guardas
muertas, están en 6.3 y 6.4.

> **Por qué los K-\* no están en `mutaciones.json`:** el contrato exige que el
> `asa` sea el nombre **EXACTO** de un `test_*` **definido** en `run_tests.py`, y
> el gate lo comprueba con `ast`. Los mutantes del **gate** y del **emisor** no
> matan ningún `test_*` de la suite (el gate vive en el validador, que la suite
> no ejecuta), luego **el contrato no tiene forma de expresarlos**: son
> mutantes *del vigilante*. Es una limitación con nombre, no un olvido: se
> miden con el diferencial de dos celdas y se documentan aquí.

### 6.2 La prueba de que el gate NO hereda del emisor

El gate **no importa** al emisor (`validate_docs.py` no lo menciona fuera de
los comentarios; verificado con grep) y re-deriva con **propia**
implementación. Medido, no supuesto: con el emisor mutado (K-1/K-17) la línea
que emite es `WOPT_VEREDICTO M-3 MUERTO e8111158…` y el gate la **caza** con
3 FAIL (journal + los dos changelogs): *"el mutante M-3 esta declarado como
MUERTO y la evidencia commiteada obliga a NO MEDIDO"*. **La mentira del emisor
no se cuela.**

Además, **fidelidad del emisor, medida**: alimentado con las 4 colas
commiteadas de M-3, el emisor **reproduce byte a byte** la evidencia commiteada
(`evidencia/M-3.cola` regenerada == commiteada: **True**) y vuelve a derivar
`NO MEDIDO`. El emisor y el corpus no divergen.

### 6.3 ⚠️ K-8: el guard se puede apagar sin que nada se entere

**MEDIDO**: sustituir la llamada `_comprobar_veredictos_de_mutacion(…)` por
`pass` deja el validador en **160 OK, 0 FAIL** y **sin REGISTRO**: no hay
`[OK]` del check 11, no hay `entradas cubiertas=0`, no hay nada. **Ni la suite
ni el validador se enteran.**

**Por qué no lo caza la suite:** el repo **ya tiene el patrón** para esto —
`run_tests.py:22298` ("Check 9 en el camino real del validador, con su mutante
de cableado") exige que **desenchufar el check 9** haga desaparecer el residuo.
**El check 11 no tiene ese test**: no hay ningún `test_*` que vigile su
cableado (grep de `check 11`, `_comprobar_veredictos` y `WOPT_VEREDICTO` en
`run_tests.py`: 0 resultados).

**Decisión: no bloquea el cierre, y se encola.** Motivo: el fix **sí** hace lo
que promete —el veredicto se vuelve comprobable y las mentiras se cazan
(K-1…K-7, K-11, K-14, K-15, K-17)—; K-8 es un ataque **al cableado del propio
vigilante**, de la familia que el repo ya conoce y ya tiene registrada
(STATUS.md: *"la vigilancia deja de ser vaciable"*, TASK-082). Y el arreglo
**no obliga a mover el recuento**: basta **extender el test de cableado que ya
existe** (o el guard de forma que ya vigila al validador) para que el check 11
cobre su propio mutante de cableado, con el recuento en **235 = 159 + 76**.
Tarea encolada con su métrica en 6.9.

### 6.4 ¿El gate verifica la **verdad** o solo la **coherencia**? (y lo que el docstring NO dice)

**Solo la coherencia.** El gate comprueba que la línea escrita **cuadre con la
evidencia commiteada**. La evidencia **la escribe quien muta**, y el gate no
puede saber si es el log real. **MEDIDO**:

- **K-10b**: una evidencia **fabricada** cuyo frame del traceback está en
  `otro_fichero.py` (nunca en `run_tests.py`) → el gate la acepta y deriva
  MUERTO → **0 FAIL**. El gate **no comprueba el fichero del frame**.
- **K-12**: un `sha_arbol_auditado` **inventado** (`deadbee000…`, que no existe
  en ningún repo) → **0 FAIL**. El gate **no resuelve el sha** contra ningún
  objeto: el "tercer testigo" es **decorativo**. (El sha commiteado de M-3,
  `e8111158…`, **tampoco existe en el repo real**: `git cat-file -t` →
  `fatal: could not get object info`.)

**El docstring declara tres límites** —(a) el `asa` no es la guarda
semánticamente correcta, (b) el `asa` no se ajustó después de ver el log,
(c) la **ausencia** de los changelogs no es un FAIL— y **NO declara los dos
que he medido**: que **la evidencia commiteada puede no ser el log real** y que
**el sha no se resuelve contra nada**. El docstring dice, en voz alta, lo que
el gate no prueba; le faltan estos dos. **No es una mentira** (no afirma lo
contrario), es una **laguna en una lista que se presenta como exhaustiva**:
quien lo lea puede suponer que "la evidencia commiteada" es el log.

**Encolado** (6.9): que el docstring declare estos dos límites.

### 6.5 El validador 2,6× más rápido: **no es un check saltado**

Comparación con **la misma entrada** (el árbol de `f5bec54`), el mismo
`GIT_DIR` desechable y salida COMPLETA:

| | `[OK]` | `[FAIL]` | `[SKIP]` | `[REGISTRO]` | tiempo |
|---|---|---|---|---|---|
| **antes** (validador de `ba28261`) | **160** | 0 | 0 | 0 | **11 461 – 11 779 ms** |
| **después** (validador de `f5bec54`) | **160** | 0 | 0 | **1** | **4 459 – 5 067 ms** |
| **después**, con la entrada del ciclo 70 en el journal | **162** | 0 | 0 | 1 | ~4 500 ms |

- **Ningún check dejó de correr**: 160 `[OK]` en los dos, los mismos 160
  (comparados uno a uno por clave), 0 FAIL y 0 SKIP en los dos. El gate **no
  añade `[OK]`** con el conjunto de sujetos vacío: solo imprime el REGISTRO.
- Los **+2** que se ven al final (160 → 162) son del gate con la entrada del
  ciclo 70: el `[OK]` del check 11 y el `[OK]` de su cross-check de changelogs.
  Los **158 → 160** del dev son del **árbol** (el `tasks.md` del cambio y las
  anclas de `STATUS.md`), **no** del fix: el validador de `ba28261` sobre el
  árbol de `f5bec54` da también **160**.
- **La causa del speedup, medida**: `ast.parse` de `run_tests.py` **3 veces**
  antes (11 461 ms) y **1 vez** después (4 459 ms), por `validar()`. El
  `ast.parse` cuesta 3 459 ms y el validador lo pagaba **tres** veces, no dos.
- **La cache no puede quedar obsoleta**: la clave es
  `(nombre, hash(fuente))` (`validate_docs.py:2922`), o sea **el contenido**.
  MEDIDO in-process: tras **modificar** `run_tests.py` (un `test_*` nuevo al
  final, **cero desplazamiento**), la segunda llamada a `validar()` **vuelve a
  parsear** y `_tests_definidos` **ve el test nuevo** (236). La cache tiene
  dos entradas (contenido viejo y nuevo).

### 6.6 El contrato en prosa: ¿se puede seguir? (sí)

- El bloque del contrato (los tres estados, la regla del asa, la regla del
  test no determinista, el límite de lo que no prueba) es **LITERAL** en
  `.agents/agents/mutation-auditor/agent.md` y en `proposal.md` §3.6:
  **1 517 caracteres, idénticos byte a byte** (comparados).
- El agent.md dice **qué escribes y dónde** (las dos cosas: `mutaciones.json`
  **y** `mutation-report.md`, con las **mismas** líneas) y **qué hacer con un
  NO MEDIDO** (encolarlo como tarea; si toca seguridad o datos, el ciclo no se
  cierra). Los tres estados y la transición aparecen también en
  `.agents/skills/id-pipeline/SKILL.md` y en `docs/ai/testing-guide.md`.
- **Prueba de fuego (hecho, no supuesto)**: he producido el catálogo y la
  evidencia de una mutación real **con el emisor**, he escrito la línea
  canónica en el journal, el informe y los dos changelogs **como hará el
  orquestador**, y he ejecutado el gate sobre ella → **162 OK, 0 FAIL**. El
  flujo se puede seguir **sin inventar un paso**.

### 6.7 La prueba de fuego, en cifras

| paso | resultado |
|---|---|
| mutación real `M-A1` (`src/woptimizer/config.py`: la prioridad vuelve a ganar a la categoría — el bug de TASK-020) | la suite **muere por el asa** en la 13.ª llamada: `AssertionError: Overlays prio=low -> 🟡 PRECAUCIÓN` |
| el emisor sobre el log real | `M-A1: MUERTO (todas las corridas mueren por el asa)` → evidencia de 574 B escrita por el emisor |
| evidencia de M-3 regenerada por el emisor | **byte a byte igual** a la commiteada |
| las tres piezas con las mismas líneas | **162 OK, 0 FAIL** |
| roto: la línea de `M-A1` fuera del **journal** | **4 FAIL** |
| roto: la línea de `M-A1` fuera del **informe** | **2 FAIL** |
| roto: la **evidencia** de `M-A1` borrada | **2 FAIL** |
| roto: la línea de `M-A1` fuera de los **changelogs** | **0 FAIL** — por diseño (límite (c)): se comprueban **si están**, su ausencia no es un FAIL. Lo que sí falla es su **incoherencia** (K-11: el changelog en MUERTO con la evidencia en NO MEDIDO → 2 FAIL) |

**Dos cosas que la prueba de fuego destapó del emisor** (herramienta, no fix):

1. **El emisor pisa la evidencia de los mutantes que NO le pasas.** Con el
   catálogo de 2 mutantes y un solo `--log`, escribe `evidencia/M-3.cola` con
   *"no hay ninguna corrida"*. Lo he medido: **destruye la evidencia
   commiteada** de M-3. Con un mutante declarado `MUERTO` el gate lo canta
   (FAIL); con uno declarado `NO MEDIDO` (el caso de M-3) **no se nota**: el
   green pasa. Por eso el flujo correcto es pasar **todos** los logs.
2. **`--log` se repite, no se acumula**: `--log A=x --log A=y` es la forma
   (una sola bandera con varios valores la rechaza `argparse`).

### 6.8 Higiene

| | resultado |
|---|---|
| identificadores sin definir (`symtable`, control positivo que **detecta** el nombre inyectado) | `run_tests.py`: 0 (63 falsos positivos de `__file__`), `validate_docs.py`: 0 (1 de `__file__`), **`.taskmaster/veredicto.py`: 0** |
| recuento, derivado por el propio validador | `defined=235 invoked=235`, `solo_definidos=[]`, `solo_invocados=[]`; **235 = 159 + 76** |
| las **cinco** declaraciones | `AGENTS.md:70`, `README.md`, `STATUS.md:12`, `STATUS.md:127`, `docs/ai/testing-guide.md:57`: las cinco dicen **235**; las dos que detallan el reparto, **159 + 76** |
| residuos en los 10 ficheros del commit | **0** CJK, 0 hangul, 0 `U+FFFD`, 0 soft hyphen, 0 cirílico |
| `git diff HEAD~1 HEAD -- src/ run_tests.py` | **vacío (0 bytes)** |
| las dos líneas sensibles | `run_tests.py:23133` y `validate_docs.py:1429`, **MEDIDAS y vigentes** |

### 6.9 Veredicto de cierre del ciclo 70

| criterio | se cumple | por qué |
|---|---|---|
| **(a) el fix aguanta** | ✅ | el gate caza las mentiras del emisor (K-1, K-17), la gramática, el prefijo, el motivo, el asa inexistente, el changelog, el catálogo y el bloque del informe; el corpus real de M-3 es el que se usa |
| **(b) los mutantes declarados y los añadidos mueren por su aserción** | ⚠️ **con una excepción** | 14 de 16 mueren; **K-8 sobrevive** (el guard se puede desenchufar sin que nada lo note) → **limitación acotada, encolada** (6.3): el arreglo no obliga a mover el recuento y la familia del guard vaciable ya está registrada en `STATUS.md` |
| **(c) 0 identificadores sin definir** | ✅ | 0 en los tres ficheros, con control positivo que detecta |
| **(d) los docstrings no mienten** | ⚠️ **con un hueco declarado** | no mienten (no afirman lo contrario), pero la lista de límites **no incluye** los dos medidos: que la evidencia puede no ser el log real (K-10b) y que el sha no se resuelve (K-12) → **encolado** (6.4) |
| **(e) higiene, recuento y citas** | ✅ | 0 sin definir, 235 = 159 + 76, las cinco declaraciones, 0 residuos, `src/` y `run_tests.py` intactos |

**VERDICT: PARTIAL.** El fix **funciona** y lo que promete se cumple; los dos
huecos que quedan son **del guard sobre sí mismo** (K-8) y **de la lista de
límites del docstring** (K-10b, K-12). Ninguno invalida el fix, y **ninguno es
mío**: los reparo `openspec-dev`. No reabro el ciclo: van como tarea, con su
métrica.

**Tareas encoladas por esta auditoría** (nombre y métrica, para que se puedan
re-auditar en tres ciclos):

1. **`TASK-088` (sugerida) — el check 11 necesita su mutante de cableado.**
   Métrica: con la llamada a `_comprobar_veredictos_de_mutacion` sustituida
   por `pass`, el validador da **160 OK, 0 FAIL y sin REGISTRO**, y **ningún
   `test_*` lo nota**. El patrón ya existe para el check 9
   (`run_tests.py:22298`). Arreglo **sin mover el recuento** (235 = 159 + 76):
   extender un test existente.
2. **`TASK-089` (sugerida) — el docstring del gate declara sus dos límites
   que faltan.** Métrica: hoy declara (a), (b) y (c); le faltan *"la evidencia
   commiteada la escribe quien muta y el gate no puede saber si es el log real"*
   (MEDIDO: una evidencia con el frame en `otro_fichero.py` → 0 FAIL) y *"el sha
   no se resuelve contra ningún objeto"* (MEDIDO: sha inexistente → 0 FAIL).
3. **`TASK-090` (sugerida) — el emisor no pisa la evidencia de los mutantes
   que no le pasas.** Métrica: con el catálogo de 2 mutantes y **un** `--log`,
   `evidencia/M-3.cola` se reescribe con *"no hay ninguna corrida"*; si el
   mutante pisado está declarado `NO MEDIDO`, **el gate no se entera**.

<!-- WOPT_VEREDICTOS -->
WOPT_VEREDICTO M-3 NO MEDIDO e811115886a8de68bbcd338c11aaa426477caeb5
WOPT_VEREDICTO M-A1 MUERTO f5bec54db57e65295ee4870afefbf6a8a0988c94
<!-- /WOPT_VEREDICTOS -->
