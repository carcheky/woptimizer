# Propuesta — El veredicto de mutacion tiene que ser una linea canonica, y esa linea tiene que poder volver a comprobarse

**Ciclo:** 70 · **Rama:** `beta` · **Tarea:** TASK-087
**Cero ediciones bajo `src/woptimizer/`.**
**Instrumento:** `%TEMP%\wopt_c70_*` (camara desechable, logs del ciclo 69 reutilizados). Nada de esto se commitea.

---

## 0. El encargo y la respuesta en una frase

El bucle decide PASS/FAIL **leyendo el log de una suite**, y hoy ese veredicto
esta escrito **a mano** en `mutation-report.md` y copiado al journal y a los dos
changelogs: **no hay ninguna forma de volver a comprobarlo**. La respuesta es
**una linea canonica emitida por un programa** (`WOPT_VEREDICTO <mutante>
<MUERTO|SOBREVIVIENTE|NO MEDIDO> <sha>`) **re-derivada despues** desde la
evidencia commiteada, con un gate en `validate_docs.py` que hoy **no existe** y
que se declara **vacio** en sus propias tripping wires.

---

## 1. Las tres decisiones que hay que tomar

| # | Decision | Respuesta | Motivo (medido) |
|---|---|---|---|
| D-1 | Donde vive el killer-check | **Un emisor** (`.taskmaster/veredicto.py`) **+ un gate** (check 10 de `validate_docs.py`) | El gate ya es el que acopla journal e historial: borrar una fila del journal da FAIL medido (§2.5) |
| D-2 | Donde vive el **asa esperada** | **La declara quien muta**, como dato **commiteado** del mutante (`mutaciones.json`) | (b) y (c) son **REFUTADOS** por medicion (§2.2) |
| D-3 | Que hace el bucle con un NO MEDIDO | **PARTIAL + mutante encolado como tarea**; NO MEDIDO **no** es FAIL | El estado PARTIAL ya existe en `SKILL.md:266`, luego no hay que inventar vocabulario |

---

## 2. Las mediciones

### 2.1 Como decide hoy el auditor (y que no puede distinguir)

**El unico texto que se parece a un killer-check** esta en el `agent.md`, y es
prosa:

> `.agents/agents/mutation-auditor/agent.md:68` — «Distingue el motivo del fallo. Un
> test que falla por un `ImportError` o un error de sintaxis **no** prueba nada: hay
> que confirmar que falla **por la asercion que ese test dice comprobar**».

Y el vocabulario del veredicto es **binario**:

> `agent.md:116` — «Cada fix del ciclo tiene su mutacion ejecutada, con el veredicto
> literal (`killed` / `survived`) y el motivo real del fallo».
> `agent.md:121` — «**PASS** = toda mutacion muere por su asercion. **FAIL** = sobrevive
> alguna. **PARTIAL** = el shell impidio ejecutar una comprobacion obligatoria».

Osea: el **tercer estado no existe ni en la prosa** (`killed`/`survived`), y el
PARTIAL que existe significa "el shell me impidio comprobar", **no** "el log no lo
prueba".

**El instrumento real** (el que el auditor del ciclo 69 uso, medido en
`%TEMP%\wopt_c69_aud\`):

| Fichero | Que extrae | Que NO extrae |
|---|---|---|
| `correr_suite.py:33-36` | `rc`, bytes, lineas, **ultima linea**, y las lineas con `[FAIL]`/`AssertionError` | **el nombre del test que murio** |
| `mutar.py:15-92` (`MUTACIONES`) | el texto original y el sustituto de cada mutacion | **el asa esperada**, el motivo esperado, el sha |

**Lo que NO puede distinguir (4 cosas):**

1. **Que el test que murio sea el asa esperada** o haya muerto **por casualidad**.
   El caso real: el test del pre-vuelo era flaky al 5,50 % (11/200), luego un
   mutante puede morir por un test que **no es el suyo** (deuda S9, ciclo 68).
2. **Un log cortado** de uno verde: hoy es una convencion del runner
   (`correr_suite.py:4`: «Un log cortado (sin linea final) es NO MEDIDO, no verde»),
   **no una regla de codigo**.
3. **Que dos corridas del mismo mutante den veredictos distintos**: no se registra
   ni se compara nada.
4. **Que el motivo literal sea ruido**: el ciclo 69 midio que el motivo que sale en
   el log es el **probabilistico 15/16 de las veces** (via V-2 del informe del
   ciclo 69).

### 2.2 Existe ya algun mecanismo de "asa esperada"? — **NO**

MEDIDO sobre el catalogo que el auditor del ciclo 69 escribio de verdad
(`%TEMP%\wopt_c69_aud\mutar.py:15-92`): las claves son `"M-1": [(original, sustituto)]`.
**No hay ningun campo de test esperado**, ni de motivo, ni de sha.

**Lo que SI es derivable** (prototipo medido sobre los **15 logs reales** del ciclo 69,
`%TEMP%\wopt_c69_aud\suite_*.log`):

| Hecho | MEDIDO |
|---|---|
| El nombre del test que murio se **extrae del log** (el frame del traceback) | **7/7 logs ROJO** → nombre exacto + linea de la asercion + motivo literal |
| El nombre se deriva del **traceback**, no de una lista | el frame es `File "...run_tests.py", line N, in test_...` |
| Coste de parsear un log de 30 KB | mediana **0,267 ms** (max 0,434 ms, 200 corridas) |
| Cuanto hay que **mirar** | la **cola**: **624-961 B** desde `Traceback (most recent call last):` → **3,4-4,8 %** del log |
| Lectura pura del log | **0,075 ms** |

**Lo que NO es derivable: quien DEBE morir.** Ni el log (dice quien murio, no quien
debia), ni la suite (235 tests, **ningun** enlace mecanico de una linea mutada a su
guard), ni la spec (la prosa dice «el pre-vuelo» y la funcion se llama
`test_el_pre_vuelo_de_un_hash_muerto_distingue_existe_de_no_existe`: la union seria
una **transcripcion a mano**, la clase D2/D3/P2).

### 2.3 El coste de repetir N veces — **no se re-litiga**

Dado y medido en el ciclo 69: suite limpia **734,9 s**; **N = 3 → 8,0 h por ciclo**;
y repetir **sin exigir consistencia** **empeora** el veredicto falso:
`1-(1-p)^N` con `p = 1/16` → **6,25 % (N=1) → 17,6 % (N=3) → 27,5 % (N=5)**.
El killer-check cuesta **0 corrida extra** porque el harness **ya captura el log**.

### 2.4 El coste de leer un log — MEDIDO

| Medicion | Resultado |
|---|---|
| Log real de la suite | **30 816-30 966 B** (verde), 18 955-28 002 B (rojo) |
| Leerlo entero | **0,075 ms** |
| Parsearlo entero (decidir) | **0,267 ms** (mediana, 200 corridas) |
| **Caracteres que hay que mirar** | la **cola**: **624-961 B** (3,4-4,8 % del log) |
| Parsear los 13 logs de un ciclo | **3,5 ms** (13 x 0,267 ms) |

**El log es barato de leer. Lo caro era decidir sin saber que mirar** — y eso es
exactamente lo que el killer-check decide.

### 2.5 El killer-check **de verdad**: que verifica hoy el repo de los veredictos — **NADA**

MEDIDO en camara desechable (`%TEMP%\wopt_c70_cam`, copia del repo con `.git`
excluido **como fichero**, `GIT_DIR` desechable, repo real anclado antes y despues:
`HEAD 322f934` sin cambios, `git status --porcelain` vacio):

| Celda | Mutacion de la camara | Resultado de `validate_docs.py` |
|---|---|---|
| **V0** | ninguna (baseline) | **158 OK, 0 FAIL** |
| **V1** | borrar la **ultima** entrada del journal (ciclo 69) | **1 FAIL** — «hay trabajo COMITEADO del/los ciclo/s 069 y rd_journal.json NO lo registra» |
| **V2** | borrar una entrada **intermedia** (ciclo 30) | **1 FAIL** — el mismo check |
| **V3** | **borrar el veredicto** del prose del `status` del ciclo 69 | **0 FAIL** — **NO se detecta** |
| **V4** | **borrar el `mutation-report.md`** entero del ciclo 69 | **0 FAIL** — **NO se detecta** |

⇒ **La fila del journal esta vigilada (2/2). El veredicto que va DENTRO de la fila
(0/2) y el fichero del informe (0/2) no los vigila nadie.** El agujero no es el
mecanismo: es **el conjunto de sujetos**, que hoy **no es derivable**.

**Corpus medido:**

| Artefacto | MEDIDO |
|---|---|
| `openspec/changes/**/mutation-report.md` | **14** ficheros, de los cuales **5** tienen linea `VERDICT:` |
| Entradas del journal | **69**; **0** con `WOPT_VEREDICTO`; **16** con un token PASS/FAIL/PARTIAL en el prose del `status` (**53** no tienen ninguno) |
| Campo estructurado de veredicto | **6/69** entradas, y con **DOS nombres distintos**: `audit` (4) y `mutation_audit` (2) |
| Enlace journal → change (`change`) | **2/69** entradas |
| `CHANGELOG.md` y `.taskmaster/CHANGELOG.md` | **0** con `WOPT_VEREDICTO` |

⇒ Hoy **no existe** un conjunto de veredictos que un guard pueda mirar sin
inventarlo a mano: **la clase exacta** que este repo lleva dos ciclos persiguiendo.

### 2.6 Una regla en `agent.md` vs. una regla en el codigo — el numero, no la impresion

**7 instrucciones escritas incumplidas, 8 eventos documentados:**

| # | Instruccion escrita | Donde | Incidente documentado |
|---|---|---|---|
| 1 | «el bucle comitea y empuja a `beta`, **nunca a `main`**» | `AGENTS.md:59`, `openspec-dev/agent.md:43` | el tramo de 33 commits que tumbaba el job `commits` → **TASK-066** |
| 2 | «el mensaje **LLEVA identificador**» | `AGENTS.md:65`, `mutation-auditor/agent.md:42-43` | el wrapper responde `WOPT_USAGE ancla-mensaje` y sale con **2** → **TASK-059** |
| 3 | «dejando el arbol de Git con **0 cambios pendientes**» | `AGENTS.md:58` | el `run_tests_out.txt` de 354 lineas arrastrado a un commit ajeno (citado en `AGENTS.md:59`) |
| 4 | «TRAMPA DEL GITLINK — **ya ha contaminado el repo real DOS VECES**» | `mutation-auditor/agent.md:50` | **2** eventos |
| 5 | «al mutar, **purga `__pycache__`** entre mutaciones» | `mutation-auditor/agent.md:111` | «y asi es como se cuela un "sobreviviente" que no existe» → **1** evento |
| 6 | la regla del veredicto en **prosa** | `proposal.md` del ciclo 69, **:260-262** | «en prosa **se aplico por suerte y por merito de quien la leyo**» → **1** evento |
| 7 | la cifra de tests **escrita a mano** en 5 sitios | `AGENTS.md:70`, `README.md:63`, `STATUS.md:12`, `STATUS.md:127`, `docs/ai/testing-guide.md:57` | se caduca en silencio (deuda D2, `STATUS.md:99`) |

**La leccion del repo es por eso una regla de diseno, no una opinion:** una
instruccion escrita que se ha incumplido mas de una vez **tiene que meterse en el
codigo, en el punto donde se puede violar**. Por eso el killer-check va **en el
codigo** y el texto del contrato va **ademas** en el `agent.md`.

---

## 3. El diseno

### 3.1 La linea canonica

```
WOPT_VEREDICTO <mutante> <MUERTO|SOBREVIVIENTE|NO MEDIDO> <sha>
```

* `<mutante>`: el identificador corto del catalogo (`M-1`, `M-V2`, `S3`), patron
  `[A-Za-z][A-Za-z0-9_.-]*`.
* `<estado>`: **exactamente** uno de los tres.
* `<sha>`: el sha (7-40 hex) del **arbol auditado** (el `HEAD` de la camara en el
  momento de la auditoria). Es el testigo tercero: un veredicto sin sha no se puede
  re-derivar.

**Regla de escritura:** un veredicto **sin** esa linea **no se puede escribir** en el
journal ni en los changelogs. Igual que un commit sin `WOPT_COMMIT_OK` no es un
commit (`AGENTS.md:65`).

### 3.2 Donde vive el killer-check

**Dos piezas, una sola logica:**

| Pieza | Fichero | Que hace | Coste MEDIDO |
|---|---|---|---|
| **Emisor** | `.taskmaster/veredicto.py` (nuevo, versionado) | dado un catalogo + las colas de los logs, **emite** las lineas canonicas y decide el estado | **3,5 ms** por ciclo de 13 mutantes |
| **Gate** | `validate_docs.py`, **check 10** (nuevo) | **re-deriva** cada veredicto desde la evidencia commiteada y **falla** si la linea no cuadra | **23,7 ms** = **0,21 %** de los 11,28 s actuales |

**Por que el gate va en `validate_docs.py` y NO como un `test_*` de `run_tests.py`:**

1. **Un test de la suite no puede ver el veredicto del ciclo en curso.** El orden
   del bucle lo impide: el journal y los changelogs se escriben **despues** del
   Paso 4 (`SKILL.md:22`, `SKILL.md:231`), luego un `test_*` solo veria el veredicto
   del ciclo **anterior** (un ciclo de retardo) mientras que el gate ve el del
   ciclo **actual**.
2. **El coste del recuento.** Un `test_*` contado obliga a subir la cifra
   (**235 → 236**) y a actualizar **cinco** declaraciones en **cuatro** ficheros
   (`AGENTS.md:70`, `README.md:63`, `STATUS.md:12`, `STATUS.md:127`,
   `docs/ai/testing-guide.md:57`) mas la fila de la tabla de `testing-guide.md`.
   **Decision: NO hay `test_*` nuevo, luego la cifra se queda en 235 = 159 + 76 y
   las cinco declaraciones NO se mueven.** (Si el dev decidiera anadirlo, el
   validador da FAIL hasta que las cinco se actualicen: el recuento se deriva con
   `ast`, luego es auto-exigible.)
3. **El gate ya es el que acopla journal e historial** (V1/V2 → 1 FAIL medido):
   el check nuevo hereda esa proteccion en vez de duplicarla.
4. **El limite, DECLARADO:** `validate_docs.py` **no corre en CI** (deuda
   preexistente, `STATUS.md:84`, **TASK-080**). El gate es local, y se ejecuta en
   el sitio donde hace falta: **despues** de escribir el journal y los changelogs y
   **antes** de empujar. El check 10 **imprime el numero de entradas cubiertas**
   (un REGISTRO, como el `REGISTRO_POR_CONSTRUCCION` del guard de TASK-072), para
   que un conjunto de sujetos vacio **no parezca verde**.

### 3.3 Donde vive el asa esperada — **(a): la declara quien muta, como dato commiteado**

| Opcion | Por que NO | Veredicto |
|---|---|---|
| (b) **derivarla de la suite** | MEDIDO: el log dice **quien murio**, nunca **quien debia**; y en los 235 tests **no hay** ningun enlace mecanico de una linea mutada a su guard. Habria que inventar una convencion de nombres = otra instruccion escrita (la clase que 2.6 cuenta por unidades) | **REFUTADA** |
| (c) **la declara el contrato de la tarea** | el asa es propiedad de la **mutacion** (que el auditor inventa en el ciclo N), y la spec se escribe **antes** de que las mutaciones existan; ademas la prosa no contiene ni el nombre de la funcion («el pre-vuelo» vs. `test_el_pre_vuelo_de_un_hash_muerto_distingue_existe_de_no_existe`), luego la union seria una transcripcion a mano | **REFUTADA** |
| (a) **la declara quien muta** | el catalogo **ya se escribe a mano** en cada ciclo (`mutar.py:15-92` lo demuestra): añadirle 2 campos cuesta **0 corridas extra** y **0** parseo extra | **ADOPTADA** |

**El catalogo pasa a ser un artefacto commiteado**:
`openspec/changes/<id>/mutaciones.json`, con **un objeto por mutante**:

```json
{
  "id": "M-3",
  "asa": "test_el_pre_vuelo_de_un_hash_muerto_distingue_existe_de_no_existe",
  "motivo": "EL RELOJ DE LA FIXTURE NO ESTA CLAVADO",
  "mutacion": {"fichero": "run_tests.py", "linea": 23459,
               "original": "...", "sustituto": "..."},
  "sha_arbol_auditado": "..."
}
```

**El modo de mentir y como se cierra:**

| Trampa | Como se cierra |
|---|---|
| Declarar un asa que **no existe** | el gate lo comprueba con `ast` sobre `run_tests.py`: el asa tiene que ser un `test_*` **definido**. K-7 |
| Declarar un asa **equivocado** (pero real) | el veredicto sale **NO MEDIDO**, nunca MUERTO: el fallo es **fail-safe** |
| **Ajustar** el asa despues de ver el log | el catalogo esta **commiteado**: ajustarlo deja rastro en git, y la linea canonica cita el `sha` del arbol auditado |
| Declarar el asa **despues** de la corrida sin dejar rastro | **LIMITE DECLARADO**: el gate **no puede probar la intencion**. Lo que si puede es que el veredicto sea **re-derivable** desde la evidencia commiteada. Queda escrito en el docstring (§3.6) |

### 3.4 Los artefactos

| Artefacto | Quien lo escribe | Commiteado | Tamano MEDIDO |
|---|---|---|---|
| `openspec/changes/<id>/mutaciones.json` | el auditor (a mano, como hoy) | si | ~2-4 KB por ciclo |
| `openspec/changes/<id>/evidencia/<mutante>.cola` | el emisor (la **cola** del log: desde `Traceback` hasta el final, o las ultimas 200 B si no hay traza, mas `RC=<n>`) | si | **624-961 B** por mutante → **~11,4 KB** por ciclo de 13 |
| `openspec/changes/<id>/mutation-report.md` | el auditor, con un **bloque de maquina** con las lineas canonicas | si | lo de siempre |
| `.taskmaster/veredicto.py` | el dev | si | nuevo |
| `validate_docs.py` check 10 | el dev | si | nuevo |

**La cola y no el log entero:** el log entero de un ciclo son 260-400 KB; la cola
son **11,4 KB** y contiene **todo** lo que hace falta para re-derivar (MEDIDO: el
frame del traceback da el nombre del test y el mensaje de la asercion da el motivo).

### 3.5 El flujo

```
AUDITOR (en la camara de %TEMP%)
  1. escribe mutaciones.json  (asa + motivo + mutacion)
  2. muta, corre la suite, guarda el log
  3. python .taskmaster/veredicto.py emitir --catalogo ... --log ...
        -> lee la cola del log, deriva (estado, test, motivo)
        -> escribe evidencia/<mutante>.cola
        -> escribe el bloque de maquina del mutation-report.md
        -> imprime las lineas WOPT_VEREDICTO
ORQUESTADOR (cierre del ciclo)
  4. copia las lineas al journal (campo `veredictos`) y a los dos changelogs
  5. python validate_docs.py   -> el CHECK 10 re-deriva y falla si no cuadra
```

### 3.6 El texto del contrato (para `mutation-auditor/agent.md`)

El bloque va **literal** en el `agent.md` (AC-4), y su parte automatizable va en el
codigo. Texto propuesto:

```
VEREDICTO DE MUTACION. Hay TRES estados, no dos, y solo el primero cuenta como
deteccion:

  MUERTO        la suite quedo en ROJO, el test que murio es EL ASA ESPERADA de la
                mutacion (el guard que esa mutacion tiene que activar) y el motivo
                literal nombra la infraccion.
  SOBREVIVIENTE la suite completa termino en VERDE (rc=0 y la ultima linea es
                'ALL TESTS PASSED.') sin ningun [FAIL].
  NO MEDIDO     TODO lo demas. En particular:
                  * log cortado (sin linea final o sin el .meta)        -> NO MEDIDO
                  * la suite muere por un test que NO es el asa esperada -> NO MEDIDO
                  * el motivo literal no nombra la infraccion           -> NO MEDIDO
                  * dos corridas del mismo mutante dan veredictos distintos -> NO MEDIDO

  EL ASA ESPERADA LA DECLARA QUIEN MUTA, en el catalogo commiteado
  (mutaciones.json). NO se deduce de la suite: la suite dice quien murio, nunca
  quien debia. El gate comprueba que el asa exista (ast sobre run_tests.py) y que
  el veredicto sea RE-DERIVABLE desde la evidencia commiteada.

  UN TEST NO DETERMINISTA NO PUEDE APORTAR LA MUERTE DE UN MUTANTE. Un rojo que
  viene de un test flaky es NO MEDIDO, jamas MUERTO: repetir la medicion N veces SIN
  exigir consistencia hace la probabilidad de veredicto falso MAS ALTA
  (1-(1-p)^N; con p=1/16: N=3 -> 17,6 %, N=5 -> 27,5 %), y exigir consistencia
  cuesta N Suite (N=3 -> 2 205 s por mutante) sin tapar el agujero de fondo.

  LO QUE ESTE CONTRATO NO PRUEBA: que el asa declarada sea la guard
  SEMANTICAMENTE correcta para esa mutacion. Lo que si prueba es que el veredicto
  es coherente con la evidencia y que no se puede escribir sin la linea canonica.
```

### 3.7 Los tres estados y la transicion del bucle

**Por mutante** (lo que emite el emisor):

| Estado | Condicion MECANICA | Que hace el bucle |
|---|---|---|
| **MUERTO** | el log esta en ROJO **y** el test que murio (derivado del traceback) es **exactamente** el `asa` declarado **y** el motivo literal contiene el `motivo` declarado | el mutante esta cerrado |
| **SOBREVIVIENTE** | el log esta VERDE (rc=0 y ultima linea `ALL TESTS PASSED.`) | **FAIL**: vuelve al **Paso 3** con el informe |
| **NO MEDIDO** | todo lo demas: log cortado, el test que murio no es el asa, el motivo no nombra la infraccion, dos corridas discrepan | **PARTIAL**: el mutante **se encola como tarea** con su metrica |

**Por ciclo** (lo que ya existe: `PASS` / `FAIL` / `PARTIAL`, `agent.md:121` y
`SKILL.md:266`):

```
        ┌─────────────────┐   un mutante SOBREVIVIENTE
        │  mutantos       │──────────────────────────► FAIL ──► Paso 3 (arreglar el test)
        │  del ciclo      │
        └────────┬────────┘
                 │ todos MUERTO (o NO MEDIDO sin riesgo)
                 ▼
              PASS ──► Paso 1 (siguiente ciclo)

        ┌─────────────────┐   un mutante NO MEDIDO
        │  NO MEDIDO      │──► PARTIAL ──┬─► no toca seguridad/datos: se ENCOLA como
        └─────────────────┘              │   tarea y el ciclo sigue a Paso 1
                                         └─► toca seguridad o datos: el ciclo NO se
                                             cierra (SKILL.md:266)
```

**La regla que hace que el tercer estado valga:** **NO MEDIDO no es FAIL.**
Si NO MEDIDO y FAIL se confunden, el bucle pasa el ciclo reintentando un mutante
cuyo log ya no existe, y el tercer estado no aporta nada. Con la transicion de
arriba, un NO MEDIDO **cuesta una tarea encolada** (el mecanismo que el ciclo 69
ya uso para H-A/H-B/H-C) y **no** un ciclo entero de reintentos.

### 3.8 Se puede vaciar el killer-check?

**Hoy: SI, del todo** (V3 y V4 → 0 FAIL medido). **Con el diseno:**

| Vector | Que lo detecta | Medido |
|---|---|---|
| borrar una linea canonica del journal | el check 10 exige **>= 1** linea por entrada cubierta y el RECISTRO imprime cuantas | nuevo |
| borrar el `mutation-report.md` | el check 10 exige que el `change` de la entrada apunte a un directorio **existente** con catalogo y bloque de maquina | nuevo |
| borrar la fila del journal | el check 5b, **hoy** | **1 FAIL medido** (V1, V2) |
| borrar el catalogo o la evidencia | el bloque de maquina cita el `sha` del arbol auditado y la evidencia; sin evidencia, la re-derivacion no cuadra | nuevo |
| **dejar el conjunto de sujetos vacio** (epoch en el futuro, o filtro que no casa) | el **REGISTRO** de entradas cubiertas se imprime: un 0 tiene que ser visible | nuevo |

**El sujeto es DERIVADO**, no enumerado: las entradas cubiertas son las del journal
con `cycle >= CICLO_ORIGEN_VEREDICTO`, y el cambio se localiza por el campo
`change` de la entrada (que hoy existe en **2/69** y pasa a ser **obligatorio** desde
el origen). **El unico dato escrito a mano es la epoca** (un ciclo), con el
precedente del repo (`validate_docs.py:1136`: «2026-10-02: 93 antes y 10 desde»),
y se declara con su motivo. Derivar la epoca seria circular: el primer journal sin
lineas canonicas seria justamente el que el gate no podria ver.

---

## 4. Criterios de aceptacion de la implementacion (TASK-087, CORREGIDOS)

> Los AC originales se **reescriben**: AC-1 (la linea canonica) es insostenible tal
> cual, porque **no hay harness en el repo** (el auditor usa un catalogo escrito a
> mano en `%TEMP%`, `mutar.py:15-92`), y AC-2 mezclaba dos cosas distintas (el
> nombre del test que **murio**, que se deriva, y el **asa esperada**, que hay que
> declarar). El texto nuevo se apoya en las mediciones de §2.

- **AC-1 (linea canonica, gramatica estricta).** El emisor escribe **exactamente**
  `WOPT_VEREDICTO <mutante> <MUERTO|SOBREVIVIENTE|NO MEDIDO> <sha>` y el gate la
  re-deriva. El gate **falla** ante: una linea sin sha, con un estado fuera de los
  tres, con un mutante que no esta en el catalogo, o con un estado que **no** cuadra
  con la evidencia. **MATA K-1** (el emisor dice MUERTO porque el log esta rojo) y
  **K-2** (la gramatica acepta cualquier cosa).
- **AC-2 (MUERTO solo con el asa esperada y el motivo).** El estado es MUERTO **si
  y solo si**: (i) el log esta en ROJO, (ii) el test que murio —**derivado del
  traceback del log**, no de una lista escrita a mano— es **exactamente** el `asa`
  declarado (igualdad exacta, no prefijo ni subcadena), y (iii) el motivo literal
  contiene el `motivo` declarado. En cualquier otro caso, NO MEDIDO. El gate
  comprueba ademas, con `ast` sobre `run_tests.py`, que el `asa` declarado sea un
  `test_*` **definido**. **MATA K-3** (comparar por prefijo), **K-4** (caer el
  chequeo del motivo) y **K-5** (aceptar un asa inexistente).
- **AC-3 (contraprueba con una MUTACION REAL, no con un test de juguete).** El
  mutante **M-3 del ciclo 69** (el reloj de la fixture sin clavar,
  `run_tests.py:23459-23460`) es el caso: sus **4 corridas reales** murieron en el
  **tripwire** 3 veces (con el motivo **probabilistico** de la 8.ª cifra) y en el
  **pre-vuelo** 1 vez (con el motivo **determinista** del INSTANTE). Con el killer-
  check y el asa declarada = el pre-vuelo, **M-3 da NO MEDIDO en 3 de 4** (el test
  que murio no es el asa) y en la cuarta las dos corridas **discrepan**, luego el
  veredicto del mutante es **NO MEDIDO** — que es lo que exige el criterio del
  ciclo 69 («un mutante que muere el 95 % NO cuenta como muerto»). **El dev tiene
  que REPRODUCIRLO** en camara: mutar M-3, correr, y comprobar que el gate dice
  **NO MEDIDO**, no MUERTO. **MATA K-6** (el gate que solo mira «el log esta rojo»).
- **AC-4 (el contrato esta en la prosa Y la parte automatizable en el codigo).** El
  texto de §3.6 esta **literal** en `.agents/agents/mutation-auditor/agent.md`, y la
  parte automatizable (los tres estados, la regla del asa, la regla del test no
  determinista) esta en `.taskmaster/veredicto.py` y en el check 10 de
  `validate_docs.py`. El docstring del gate declara **lo que NO prueba** (§3.3).
  **MATA K-7** (el gate que acepta un asa que no existe en la suite).
- **AC-5 (el docstring dice por que NO se repite N veces).** El docstring del gate
  dice, con las cifras: (i) repetir cuesta **N x 734,9 s** por mutante (N=3 →
  **8,0 h por ciclo**) y (ii) repetir **sin exigir consistencia** **empeora** el
  veredicto falso: `1-(1-p)^N` → **6,25 % (N=1) → 17,6 % (N=3) → 27,5 % (N=5)**.
  Sin las dos frases el arreglo se puede deshacer sin que nadie lo note.
- **AC-6 (el agente se sincroniza al espejo).** `python .taskmaster/sync_agents.py`
  y despues `python .taskmaster/sync_agents.py --check` sale con **0**.
- **AC-7 (el gate no se puede vaciar).** En camara, **cuatro** celdas con control
  positivo: (a) borrar una linea canonica del journal → **FAIL**; (b) borrar el
  `mutation-report.md` → **FAIL**; (c) dejar el filtro de epoca sin entradas
  (conjunto vacio) → el **REGISTRO** dice 0 y el gate **no** da verde por omision;
  (d) con todo en su sitio → **0 FAIL**. El gate imprime el numero de entradas
  cubiertas **y** el numero de mutantes re-derivados.
- **AC-8 (NO MEDIDO es accionable).** El `agent.md` y el `SKILL.md` dicen que un
  NO MEDIDO **no** es un FAIL: el mutante **se encola como tarea** con su metrica y
  el ciclo sigue; y si el NO MEDIDO toca **seguridad o datos**, el ciclo **no se
  cierra** (`SKILL.md:266`). El dev lo deja **escrito**, no solo practicado.
- **AC-9 (coste medido y recuento intacto).** El gate cuesta **<= 0,5 %** de los
  **11,28 s** de `validate_docs.py` (MEDIDO: **23,7 ms** = **0,21 %**) y el emisor
  **<= 10 ms** por ciclo de 13 mutantes (MEDIDO: **3,5 ms**). **Cero** corridas
  extra de la suite (**0 s**). El recuento de tests **NO cambia**: sigue en
  **235 = 159 backend + 76 headless**, y las **cinco** declaraciones
  (`AGENTS.md:70`, `README.md:63`, `STATUS.md:12`, `STATUS.md:127`,
  `docs/ai/testing-guide.md:57`) **no se mueven**. `python run_tests.py` → verde,
  `python validate_docs.py` → **0 FAIL** (con el check 10 activo), `python
  verify_ui_syntax.py` → exit 0.

### 4.1 Los mutantes declarados (los que el auditor tiene que matar)

| id | Que rompe | Que tiene que morir |
|---|---|---|
| **K-1** | el emisor dice MUERTO porque el log esta rojo, sin mirar el asa | el gate re-deriva NO MEDIDO → **FAIL** |
| **K-2** | la gramatica acepta una linea sin sha o con un estado inventado | el gate **FAIL** |
| **K-3** | el asa se compara por prefijo (`test_el_pre_vuelo` casa con `test_el_pre_vuelo_de_un_hash_muerto_...`) | el gate **FAIL** con el par de nombres |
| **K-4** | se cae el chequeo del motivo: basta con que muera el test correcto | el gate **FAIL** |
| **K-5** | el asa declarado no tiene que existir en la suite | el gate **FAIL** |
| **K-6** | el gate solo mira «el log esta rojo» (M-3) | el gate da **NO MEDIDO** → **FAIL** |
| **K-7** | el filtro de epoca se deja en un futuro y el gate no ve a nadie | el **REGISTRO** dice 0 y el gate **no** da verde |

---

## 5. El coste medido (todo)

| Concepto | MEDIDO |
|---|---|
| Emisor: parsear 13 logs | **3,5 ms** |
| Emisor: decidir un mutante | **0,267 ms** (mediana de 200 parseos de un log de 30 KB) |
| Gate (check 10) | **23,7 ms** = **0,21 %** de los 11,28 s de `validate_docs.py` |
| Corridas extra de la suite | **0** (frente a N x 734,9 s) |
| Evidencia commiteada | **624-961 B** por mutante → **~11,4 KB** por ciclo de 13 |
| Recuento de tests | **235 = 159 + 76**, sin cambios |
| Caracteres que hay que mirar por log | **624-961 B** (3,4-4,8 % del log) |
| Veredictos hoy sin vigilancia | **2 de 2 vectores** (V3, V4) → 0 FAIL |

---

## 6. Lo que se refuta del encargo

| Premisa del encargo | MEDIDA | Refutacion |
|---|---|---|
| «AC-2 exige que el harness **derive** el nombre del asa» | §2.2 | El nombre del test que **murio** se deriva (7/7 logs). El **asa esperada** no es derivable de nada: (b) y (c) estan refutadas. Se reescribe el AC: el asa **la declara quien muta**, en un catalogo **commiteado** |
| «AC-3: el ciclo 68 tiene un mutante asi: **M-V2**» | `mutation-report.md` del ciclo 68, **:473** y **:538** | **FALSA**: M-V2 **no es una mutacion de codigo**, es un «**escenario EQUIVALENTE (ruido util)»** cuyo rojo **es la asercion correcta** (el guard nombra la vista nueva). El caso real es **M-3 del ciclo 69** (§4, AC-3), con **4 corridas reales** medidas |
| «en el ciclo 68 un mutante (**S3**) parecio muerto porque un test flaky lo killo por casualidad» | `mutation-report.md` del ciclo 68, **:1024** y **:1217** | **IMPRECISA**: **S3 termino en `ALL TESTS PASSED.`** y esta declarado **SUPERVIVIENTE** («S3 NO cuenta como FAIL, esta decidido y documentado como deuda S9»). El contaminante era el **pre-vuelo al 5,50 %** (deuda S9 / T-C68-B), no S3 |
| «el killer-check puede ser un `test_*` del repo» | §3.2 | Posible pero **peor**: el journal se escribe **despues** del Paso 4 (`SKILL.md:22`), luego un test de la suite solo veria el veredicto del ciclo **anterior**; y obliga a subir la cifra a 236 y a mover **cinco** declaraciones. El gate va en `validate_docs.py` |
| «repetir N veces» | §2.3 | **No se re-litiga**: rechazado (8,0 h/ciclo y veredicto falso **peor**: 17,6 %) |
| «el conjunto de veredictos a comprobar puede derivarse» | §2.5 | **Hoy NO**: 0 `WOPT_VEREDICTO`, el veredicto estructurado existe en **6/69** entradas con **dos** nombres, y el enlace journal→change en **2/69**. El diseno lo hace derivable (epoca + campo `change` obligatorio) |

---

## 7. Lo que NO cabe aqui (encolado con metrica)

| Que | Por que no cabe | Metrica |
|---|---|---|
| **TASK-088** — el guard DERIVADO de la familia de las 21 fixtures dependientes del reloj | es otra guarda, de otro guard | 21 call sites |
| **TASK-089** — el guard de suite que detecte que el arbol se movio durante la corrida | es integridad de la medicion, no del veredicto | `_sin_contaminacion` (`run_tests.py:17889`) |
| **TASK-080** — que `validate_docs.py` corra en CI | el gate que se propone es **local**; el CI es una deuda preexistente y con su propia causa (154 FAIL en el clon shallow) | `STATUS.md:84` |
| Que el gate **verifique la intencion** (que el asa declarada sea la guard semanticamente correcta) | **imposible** sin un analisis semantico; se declara el limite en el docstring | §3.3, §3.6 |

---

## 8. Instrumento: que se uso y que NO se commitea

- Camara: `%TEMP%\wopt_c70_cam` (copia con `shutil.copytree(...,
  ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))` → `.git`
  excluido **como fichero**, que en este repo es un fichero de 57 B), con
  `GIT_DIR` **desechable** y verificacion de aislamiento antes de mutar nada.
  **Nunca** se invoco `git_safe_commit.py` desde `%TEMP%`.
- Logs reutilizados: los **15** logs reales del ciclo 69
  (`%TEMP%\wopt_c69_aud\suite_*.log`, 10 111-30 966 B).
- Prototipos: `%TEMP%\c70_parseo2.py` (parser del log), `%TEMP%\c70_check10.py`
  (prototipo del gate), `%TEMP%\c70_vaciabilidad.py` (V0-V4).
- **Cero ediciones bajo `src/woptimizer/`.** **Cero ediciones en `run_tests.py`.**
- Anclaje del repo real: `HEAD 322f934` **antes y despues**, `git status
  --porcelain` vacio, `git rev-parse --git-dir` → el repo desacoplado de
  `%LOCALAPPDATA%`.
