# Tareas — El gate tiene que DISTINGUIR (TASK-090)

**Ciclo:** 71 · **Rama:** `beta` · **Tarea:** TASK-090
**Contrato:** `proposal.md` de este directorio.
**Cero ediciones bajo `src/woptimizer/`.**
**El recuento de tests NO se mueve: 235 = 159 + 76.**

---

## Que hay que hacer (TASK-090)

| # | Que | Donde | Discrimina porque |
|---|---|---|---|
| 1 | **El corpus sintetico**: un journal con una entrada `cycle: 70`, un `change` sintetico, un `mutaciones.json` con **DOS** mutantes (`M-FIX-BIEN` coherente **primero**, `M-FIX-MAL` contradictorio **segundo**), la `evidencia/<id>.cola` de los dos y el `mutation-report.md` con el bloque de maquina | dentro del test, sobre el esqueleto | Sin el, no hay nada que discriminar: el gate no tiene ningun sujeto |
| 2 | **La celda D1 (EL AC QUE DISTINGUE)**: el validador **sano** tiene que dar **≥1 `[FAIL]` que nombre al contradictorio** y **0 `[FAIL]` que nombren al coherente**, con el REGISTRO presente | seccion (D) del test existente (`run_tests.py:22278`) | Un guard de FORMA no lo cumple: el mutante **M-93** (calcula el veredicto y lo tira) conserva bucle, llamada y comparacion, y solo lo coge un guard de producto |
| 3 | **La celda D2 (CONTRAPROUEBA)**: con el cuerpo del gate **vacio** y el REGISTRO puesto, el `[FAIL]` del contradictorio **desaparece** y el REGISTRO **sigue** | seccion (D) | Sin esta celda, AC-1 podria cumplirse por un motivo equivocado (la clase **A11** del panel: una comprobacion sin contraprueba no es una comprobacion) |
| 4 | **La celda D3 (restauracion)**: el esqueleto queda con el validador original para las secciones siguientes | seccion (D) | Un esqueleto mutado contaminaría las secciones que vienen despues |
| 5 | **El limite nuevo, DECLARADO**: el bloque «LO QUE ESTE GATE **NO** PRUEBA» de `validate_docs.py` trae el limite **(f)**: *el validador, por si solo, NO detecta un gate ciego; solo la suite lo hace*. El docstring de la funcion lo repite | `validate_docs.py` | Un limite que no esta escrito no esta declarado (y el guard de forma (B) ya exige que la lista diga «NO es exhaustiva») |
| 6 | **La documentacion viva**: la fila **130** de la tabla de `docs/ai/testing-guide.md` describe la seccion (D), y el coste medido va escrito | `docs/ai/testing-guide.md` | Una tabla que no cuenta lo que el test hace se caduca en silencio (la clase **D2/D3/P2**) |
| 7 | **El catalogo del cambio**: `mutaciones.json` con los cuatro mutantes (id, asa, motivo, mutacion, sha_arbol_auditado) y `evidencia/<id>.cola` | `openspec/changes/<id>/` | El contrato del ciclo 70: el veredicto se emite con lineas canonicas y el check 11 las re-deriva |

## Que NO hay que hacer

- **NO** anadir un `test_*`: el recuento se queda en **235 = 159 + 76** y las
  **cinco** declaraciones (`AGENTS.md:70`, `README.md:63`, `STATUS.md:12`,
  `STATUS.md:132`, `docs/ai/testing-guide.md:57`) **no se mueven**. El guard va
  como **seccion (D)** del test que ya existe (`run_tests.py:22278`), con el
  precedente literal del ciclo 70 (`run_tests.py:22298-22302`).
- **NO** tocar `validate_docs.py` para que el gate distinga: el gate **ya**
  distingue (MEDIDO: 1 FAIL sobre un catalogo contradictorio). Lo que falta es el
  guard que lo **comprueba**.
- **NO** meter el guard en `validate_docs.py` (check 12): el veredicto de mutacion
  lo lee del **log de `run_tests.py`** (`mutation-auditor/agent.md`, punto 4), luego
  un guard que viva solo en el validador dejaria el D-B como **SOBREVIVIENTE**.
- **NO** tocar el contrato de la linea canonica (`.taskmaster/veredicto.py`, la
  gramatica, los tres estados): queda **intacto**.
- **NO** arreglar **D-H** (TASK-091) aqui: es un ciclo aparte (propuesta §4).
- **NO** correr la suite completa de mas: el unico test implicado se mide suelto.
- **NO** tocar `src/woptimizer/`.

## Encolado aparte (no cabe aqui)

| Tarea | Que |
|---|---|
| **TASK-091** | **D-H**: el gate ignora el campo `mutacion` del catalogo. MEDIDO HOY: el catalogo del ciclo 70 **ya esta caducado** (`M-3` declara `run_tests.py:23459` y el texto esta en la **23631**; `M-A1` declara `src/woptimizer/config.py:285` y el texto **NO APARECE**), luego su AC-1, tal como esta escrito, daria FAIL sobre el propio catalogo del repo |
| **TASK-088** | El guard DERIVADO que vigila la **familia**: las 21 fixtures con sha dependiente del reloj |
| **TASK-089** | El guard de **suite** que detecte que el arbol se movio durante la corrida |
| **TASK-080** | Que `validate_docs.py` corra en CI (hoy el gate es **local**) |

## Mutantes declarados (los tiene que matar el `mutation-auditor`)

| id | Que rompe | Que tiene que morir | Por que no es EQUIVALENTE (MEDIDO) |
|---|---|---|---|
| **M-90** | el **CUERPO** del check 11 vaciado, el REGISTRO puesto | la asercion del contradictorio («EL GATE NO DISTINGUE») | `FAIL(M-FIX-MAL)`: **1 → 0** |
| **M-91** | la comparacion del veredicto **invertida** (`!=` → `==`) | la asercion del coherente («EL GATE ACUSA EN LO QUE NO PUEDE») | `FAIL(M-FIX-BIEN)`: **0 → 1** |
| **M-92** | el gate mira **solo el primer** mutante del catalogo | la asercion del contradictorio | `FAIL(M-FIX-MAL)`: **1 → 0** |
| **M-93** | el gate **calcula el veredicto y lo tira** (misma forma, ciego) | la asercion del contradictorio | `FAIL(M-FIX-MAL)`: **1 → 0**. **Es el que refuta el guard de forma** |

Los cuatro **conservan el REGISTRO**: por eso el guard de cableado (D-A) no los ve
y hace falta el de contenido.

---

## Criterios de aceptacion, tarea por tarea

| # | Criterio | Estado |
|---|---|---|
| **1** | La seccion (D) monta el corpus sintetico y corre el validador **sano**: **≥1 `[FAIL]`** que nombre `M-FIX-MAL`, **0** que nombren `M-FIX-BIEN`, REGISTRO presente (AC-1) | ⬜ pendiente |
| **2** | La celda D2 exige que el `[FAIL]` del contradictorio **desaparezca** con el cuerpo vaciado y que el REGISTRO **siga** (AC-2) | ⬜ pendiente |
| **3** | El recuento derivado del producto sigue siendo **235 = 159 + 76** y las **cinco** declaraciones estan intactas; la fila 130 de `docs/ai/testing-guide.md` nombra la seccion (D) (AC-3) | ⬜ pendiente |
| **4** | El coste medido y declarado: **dos corridas del validador ≈ 9 s** (1,2 % de la suite de 735 s); el coste marginal del **validador** no cambia (10,2 ms / 0,091 %, dentro del 0,5 %) (AC-4) | ⬜ pendiente |
| **5** | El catalogo del cambio declara los cuatro mutantes con `id`, `asa`, `motivo`, `mutacion` y `sha_arbol_auditado`, y su `evidencia/<id>.cola` (AC-5) | ⬜ pendiente |
| **6** | El bloque «LO QUE ESTE GATE **NO** PRUEBA» declara el limite **(f)** y el docstring de la funcion lo repite (AC-6) | ⬜ pendiente |
| **7** | `python run_tests.py` verde, `python validate_docs.py` **0 FAIL** (162 OK), `python verify_ui_syntax.py` verde, `src/` intacto (AC-7) | ⬜ pendiente |
| **8** | `.taskmaster/tasks.json`: TASK-090 a `completed` con las notas del hallazgo | ⬜ pendiente |

---

## Avance — TASK-090 (ciclo 71, dev)

**Estado:** PENDIENTE.
