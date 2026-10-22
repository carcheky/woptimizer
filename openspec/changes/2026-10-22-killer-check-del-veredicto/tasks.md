# Tareas — El veredicto de mutacion tiene que ser una linea canonica comprobable

**Ciclo:** 70 · **Rama:** `beta` · **Tarea:** TASK-087
**Contrato:** `proposal.md` de este directorio.
**Cero ediciones bajo `src/woptimizer/`.**

---

## Que hay que hacer (TASK-087)

| # | Que | Donde | Discrimina porque |
|---|---|---|---|
| 1 | **Emisor**: dado un catalogo + las colas de los logs, decide el estado de cada mutante y escribe la linea `WOPT_VEREDICTO <mutante> <MUERTO\|SOBREVIVIENTE\|NO MEDIDO> <sha>` | `.taskmaster/veredicto.py` (nuevo) | Sin el, el veredicto sigue escrito a mano. El estado sale de la **cola** del log, no de la prosa |
| 2 | **El asa esperada la declara quien muta**: campo `asa` (nombre exacto del `test_*`) y `motivo` (substring del mensaje de la asercion) por mutante, en un catalogo **commiteado** | `openspec/changes/<id>/mutaciones.json` | Sin el, no hay forma de distinguir «murio por su asa» de «murio de paso». El gate comprueba con `ast` que el asa **exista** |
| 3 | **Evidencia commiteada**: la **cola** del log (desde `Traceback` hasta el final, o las ultimas 200 B si no hay traza) mas `RC=<n>` | `openspec/changes/<id>/evidencia/<mutante>.cola` | Sin el, el veredicto no se puede **re-derivar**: nadie podria comprobarlo. MEDIDO: **624-961 B** por mutante (**~11,4 KB** por ciclo de 13) frente a 260-400 KB de los logs enteros |
| 4 | **Gate**: check 10 de `validate_docs.py`. Re-deriva cada veredicto desde la evidencia y **falla** si la linea no cuadra, si le falta el sha, si el estado no es uno de los tres, si el asa no existe o si el conjunto de sujetos sale vacio. Imprime el **REGISTRO** de entradas cubiertas y de mutantes re-derivados | `validate_docs.py` | MEDIDO: **23,7 ms** = **0,21 %** de los 11,28 s actuales. El gate **no** es un `test_*`: el journal se escribe **despues** del Paso 4 (`SKILL.md:22`), luego un test de la suite solo veria el ciclo anterior |
| 5 | **El contrato en la prosa**: los tres estados, la regla del asa, la regla del test no determinista y **lo que el contrato NO prueba** | `.agents/agents/mutation-auditor/agent.md` | Sin el texto, el codigo no se entiende; con el texto solo, la regla se cumple «por merito de quien la lea» (proposal.md del ciclo 69, **:260-262**) |
| 6 | **El bucle sabe que hacer con un NO MEDIDO**: no es FAIL; se **encola como tarea** con su metrica, y si toca seguridad o datos el ciclo no se cierra | `.agents/agents/mutation-auditor/agent.md` + `.agents/skills/id-pipeline/SKILL.md` | Si NO MEDIDO y FAIL se confunden, el tercer estado no vale nada |
| 7 | **Sincronizacion del agente al espejo** | `python .taskmaster/sync_agents.py` y `--check` sale con **0** | El espejo es lo que lee el runtime; editar el espejo es trabajo perdido |

## Que NO hay que hacer

- **NO** repetir la suite N veces: cuesta **N x 734,9 s** por mutante (N=3 → **8,0 h
  por ciclo**) y, sin exigir consistencia, **empeora** el veredicto falso
  (`1-(1-p)^N`: 6,25 % → **17,6 %** con N=3, 27,5 % con N=5).
- **NO** anadir un `test_*` a la suite: el recuento se queda en **235 = 159 + 76** y
  las **cinco** declaraciones (`AGENTS.md:70`, `README.md:63`, `STATUS.md:12`,
  `STATUS.md:127`, `docs/ai/testing-guide.md:57`) **no se mueven**. El gate va en
  `validate_docs.py`.
- **NO** escribir a mano una lista de tests «de evidencia» ni de veredictos: es la
  clase que este repo lleva dos ciclos persiguiendo (D2, D3, P2, A-C68-1).
- **NO** tocar `src/woptimizer/`.

## Encolado aparte (no cabe aqui)

| Tarea | Que |
|---|---|
| **TASK-088** | El guard DERIVADO que vigila la **familia**: las 21 fixtures con sha dependiente del reloj |
| **TASK-089** | El guard de **suite** que detecte que el arbol se movio durante la corrida |
| **TASK-080** | Que `validate_docs.py` corra en CI (hoy el gate es **local**; el CI es deuda preexistente) |

## Mutantes declarados (los tiene que matar el `mutation-auditor`)

| id | Que rompe | Que tiene que morir |
|---|---|---|
| **K-1** | el emisor dice MUERTO porque el log esta rojo, sin mirar el asa | el gate re-deriva NO MEDIDO → FAIL |
| **K-2** | la gramatica acepta una linea sin sha o con un estado inventado | el gate FAIL |
| **K-3** | el asa se compara por prefijo | el gate FAIL con el par de nombres |
| **K-4** | se cae el chequeo del motivo | el gate FAIL |
| **K-5** | el asa declarado no tiene que existir en la suite | el gate FAIL |
| **K-6** | el gate solo mira «el log esta rojo» (M-3 del ciclo 69) | el gate da NO MEDIDO → FAIL |
| **K-7** | el filtro de epoca se deja en un futuro y el gate no ve a nadie | el REGISTRO dice 0 y el gate NO da verde |

---

## Avance — TASK-087 (ciclo 70, dev)

**Estado:** PENDIENTE.
