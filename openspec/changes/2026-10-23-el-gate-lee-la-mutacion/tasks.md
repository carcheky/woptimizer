# Tareas — El gate tiene que LEER el campo `mutacion` del catalogo (TASK-091)

**Ciclo:** 72 · **Rama:** `beta` · **Tarea:** TASK-091
**Contrato:** `proposal.md` de este directorio.
**Cero ediciones bajo `src/woptimizer/`.**
**El recuento de tests NO se mueve: 235 = 159 + 76.**

---

## Que hay que hacer

| # | Que | Donde | Discrimina porque |
|---|---|---|---|
| 1 | **`_leer_el_catalogo` devuelve la `mutacion`** (la tupla pasa de 4 a 5 elementos) y el bucle de `validate_docs.py:3328` itera cinco | `validate_docs.py` | Sin esto el gate no puede mirar el campo: hoy lo **descarta** (`validate_docs.py:3148-3166`) |
| 2 | **R1 (forma)**: `mutacion` es un objeto con `fichero`/`original`/`sustituto` no vacios, `original != sustituto` y `linea` entero `>= 1` | `validate_docs.py`, por mutante | MEDIDO HOY: un catalogo **sin** `mutacion` da **0 FAIL** |
| 3 | **R2 (el fichero existe)**: `mutacion.fichero` resuelve con `_dentro_del_arbol` y es un fichero existente | `validate_docs.py`, por mutante | MEDIDO HOY: `mutacion.fichero = src/woptimizer/NO_EXISTE.py` da **0 FAIL** ← **la trivia medida del encargo** |
| 4 | **R3 (el `cambio` del catalogo es el `change` de la entrada)** | `validate_docs.py`, por entrada del journal | Un catalogo se hace pasar por el de otro cambio sin que nadie lo note |
| 5 | **R4 (el `ciclo` del catalogo es el `cycle` de la entrada)** | `validate_docs.py`, por entrada del journal | MEDIDO HOY: `ciclo: 999` da **0 FAIL** ← **la segunda trivia medida** |
| 6 | **El limite (g) DECLARADO**: el bloque canonico "LO QUE ESTE GATE **NO** PRUEBA" y el docstring de la fonction repiten que el **texto declarado NO se comprueba**, con sus **tres motivos medidos** (caducidad, coste, semantica) | `validate_docs.py` | Un limite que no esta escrito no esta declarado; y el (g) es lo que hace que la comprobacion del texto NO sea una bomba de relojería |
| 7 | **El guard de FORMA (B) se amplia** para exigir `(g)` con su motivo medido | `run_tests.py:22530` (la lista `(a)`..`(f)` pasa a `(a)`..`(g)`) | Sin esto, el limite (g) se puede borrar en silencio |
| 8 | **La seccion (F)**: un cambio sintetico **PROPIO** con `M-FIX-MUTACION-OK` (coherente, **primero**) y `M-FIX-MUTACION-MAL` (coherente en todo lo demas, `mutacion.fichero` inexistente, **segundo**) | `run_tests.py:22278` (el test que ya existe) | Es el **discriminante**: hoy el gate no lee `mutacion`, luego el centinela malo no es acusado (**0 FAIL**) |
| 9 | **La celda F3 (CONTRAPROUEBA)**: con la `mutacion` correcta, **0 FAIL** que nombren a los centinelas | `run_tests.py` | Sin F3, F1 podria cumplirse por un motivo equivocado (la clase **A11** del panel) |
| 10 | **La migracion de `M-121`**: `mutacion.fichero` = `"run_tests.py + validate_docs.py"` -> un fichero real; `linea: 0` -> la linea real; con su nota. **El `sha_arbol_auditado` NO se toca** y el `mutation-report.md` NO se reescribe | `openspec/changes/2026-10-22-el-gate-distingue-o-falla/mutaciones.json` | Sin esto el validador da **1 FAIL sobre el catalogo real** (viola R1 y R2) |
| 11 | **La documentacion viva**: la **fila 130** de la tabla de `docs/ai/testing-guide.md` nombra la seccion (F) y el limite (g), con el coste medido | `docs/ai/testing-guide.md` | Una tabla que no cuenta lo que el test hace se caduca en silencio (la clase **D2/D3/P2**) |
| 12 | **El limite (g) lo declara el `agent.md` del `mutation-auditor`**: la `mutacion` se declara con `fichero`, `linea`, `original` y `sustituto`, y **`fichero` tiene que existir** | `.agents/agents/mutation-auditor/agent.md` (**del orquestador**, no del arquitecto) | Sin eso, el auditor sigue declarando `mutacion` que no aplican: fue justo lo que paso con M-121 y M-A1 |

---

## Que NO hay que hacer

- **NO** anadir un `test_*`: el recuento se queda en **235 = 159 + 76** y las
  **cinco** declaraciones (`AGENTS.md:70`, `README.md:63`, `STATUS.md:12`,
  `STATUS.md:132`, `docs/ai/testing-guide.md:57`) **no se mueven**. El guard va
  como **seccion (F)** del test que ya existe.
- **NO** comprobar que el `original` este EN el fichero: es el **limite (g)**, y
  su motivo esta medido (caduca, cuesta 62,3 ms contra 46,2 ms disponibles, y la
  receta que caduca NO invalida el veredicto). Exigirlo daria FAIL sobre el
  propio catalogo del repo.
- **NO** exigir el texto en la **linea** declarada: MEDIDO, **25 de los 26**
  mutantes del repo fallan esa regla.
- **NO** meter la comprobacion en un **check 12-bis**: el contrato del
  `--sin-ancla-de-git` son **TRES** saltados (`validate_docs.py:3189-3193`) y un
  check nuevo los cambiaria a cuatro.
- **NO** tocar `.taskmaster/veredicto.py` (el emisor), la gramatica de la linea
  canonica ni los tres estados: el contrato queda **intacto**.
- **NO** reescribir el `mutation-report.md` del ciclo 71: es el **registro de la
  ronda 5**.
- **NO** tocar `src/woptimizer/`.
- **NO** arreglar **T-1** ni **T-6** (son de otro ciclo): este diseno **no
  depende de la cola**, luego no los reproduce. Pero la seccion (F) tiene que
  exigir `Resumen:` y el motivo en la **ULTIMA** linea de la cola, como (D1).
- **NO** tocar los **15 centinelas** del corpus de (D): la seccion (F) usa un
  cambio sintetico **PROPIO**, y tocar los de (D) contaminaria sus aserciones.

---

## Mutantes declarados (los tiene que matar el `mutation-auditor`)

| id | Que rompe | Que tiene que morir | Por que no es EQUIVALENTE (MEDIDO) |
|---|---|---|---|
| **M-H1** | el gate **NO comprueba R1** | la asercion de F1 sobre `M-FIX-MUTACION-MAL` | hoy una `mutacion` ausente da **0 FAIL** |
| **M-H2** | el gate **NO comprueba R2** | la asercion de F1 | hoy un `fichero` inexistente da **0 FAIL** |
| **M-H3** | el gate **NO comprueba R3** | la asercion de F2-bis | el catalogo pasa a ser el de otro cambio sin que nadie lo note |
| **M-H4** | el gate **NO comprueba R4** | la asercion de F2 | hoy `ciclo: 999` da **0 FAIL** |
| **M-H5** | el gate mira **solo el primer** mutante del catalogo | la asercion de F1 | el centinela malo es el **SEGUNDO** a proposito (el patron de M-92) |
| **M-H6** | el gate **acusa en lo que no puede** (tambien acusa a los centinelas en regla) | la asercion de F3 (0 FAIL sobre el bueno) | el patron de M-91: acusar de mas es tan ciego como no acusar |

---

## Criterios de aceptacion, tarea por tarea

| # | Criterio | Estado |
|---|---|---|
| **1** | Las cuatro reglas (R1, R2, R3, R4) estan en el gate, en el orden de la proposal §3.2, con los **textos literales** de §3.3 (AC-1, AC-2) | ⬜ pendiente |
| **2** | La seccion (F) monta el cambio sintetico PROPIO: **>=1 `[FAIL]` con la RAZON de R2** que nombre a `M-FIX-MUTACION-MAL` y **0** que nombren a `M-FIX-MUTACION-OK`; y con `ciclo: 999`, **>=1 `[FAIL]` con la RAZON de R4** (AC-1, AC-2) | ⬜ pendiente |
| **3** | F3: con la `mutacion` correcta, **0 FAIL** que nombren a los centinelas, con el REGISTRO presente (AC-3) | ⬜ pendiente |
| **4** | El catalogo **real** pasa con **0 FAIL** tras la migracion de `M-121`, con su nota; `sha_arbol_auditado` y `mutation-report.md` intactos (AC-3) | ⬜ pendiente |
| **5** | El limite **(g)** esta en el bloque canonico y en el docstring, con sus tres motivos medidos, y el guard (B) lo exige (AC-4) | ⬜ pendiente |
| **6** | El **coste medido y declarado** en ms reales contra `validate_docs.py`, con el margen antes y despues; el presupuesto del 0,5 % (56,4 ms) intacto (AC-5) | ⬜ pendiente |
| **7** | Los **15 centinelas** del corpus de (D) siguen dando 0 FAIL; la seccion (F) usa un cambio PROPIO (AC-6) | ⬜ pendiente |
| **8** | `python run_tests.py` verde, `python validate_docs.py` **0 FAIL**, `python verify_ui_syntax.py` verde, `src/` intacto, el contrato de la linea canonica intacto (AC-7) | ⬜ pendiente |
| **9** | El recuento sigue en **235 = 159 + 76**, las cinco declaraciones intactas, la fila 130 de `docs/ai/testing-guide.md` nombra la seccion (F) (AC-8) | ⬜ pendiente |
| **10** | `.taskmaster/tasks.json`: TASK-091 a `completed` con las notas del hallazgo | ⬜ pendiente |

---

## Encolado aparte (no cabe aqui)

| Tarea | Que |
|---|---|
| **TASK-092** | T-1 de la ronda 5: las aserciones de la seccion (E) tienen que terminar en una linea marcador, o el emisor no ve el motivo y cinco mutantes caen a NO MEDIDO |
| **T-088** | la familia de fixtures con sha dependiente del reloj |
| **TASK-089** | el guard de suite que detecte que el arbol se movio durante la corrida |
| **TASK-080** | que `validate_docs.py` corra en CI (hoy el gate es **local**) |
| **T-6** | el emisor y el gate derivan distinto cuando el mensaje de la asercion embarga un traceback: este ciclo **no lo reproduce** (las reglas no dependen de la cola), pero sigue abierto |

---

## Avance — TASK-091 (ciclo 72, dev)

**Estado:** PENDIENTE.
