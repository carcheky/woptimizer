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

**Estado:** HECHO. Todo lo de arriba esta implementado, medido en camara y
committeado en `beta`.

### Lo que hay

| # | Que | Donde | Hecho |
|---|---|---|---|
| 1 | Emisor | `.taskmaster/veredicto.py` (nuevo) | si. Escribe la linea canonica y la evidencia. **MEDIDO: 7,1 ms** para 13 mutantes (presupuesto: 10 ms) |
| 2 | Catalogo (`asa` + `motivo`) | `openspec/changes/2026-10-22-killer-check-del-veredicto/mutaciones.json` | si. Lo declara quien muta |
| 3 | Evidencia commiteada | `openspec/changes/2026-10-22-killer-check-del-veredicto/evidencia/M-3.cola` | si. **3 395 B** por mutante (4 corridas), ~11 KB por ciclo de 13 |
| 4 | Gate | `validate_docs.py`, **check 11** | si. Re-deriva, falla si no cuadra e imprime el REGISTRO. **MEDIDO: 27,2 ms** de coste marginal |
| 5 | El contrato en la prosa | `.agents/agents/mutation-auditor/agent.md` | si. El texto de `proposal.md` §3.6 va **LITERAL** |
| 6 | NO MEDIDO accionable | `mutation-auditor/agent.md` + `.agents/skills/id-pipeline/SKILL.md` | si. Se encola como tarea; si toca seguridad o datos el ciclo no se cierra |
| 7 | Sincronizacion del agente | `python .taskmaster/sync_agents.py` + `--check` | si. `--check` sale con **0**. **OJO: `sync_agents.py` NO cubre los skills** (solo los cuatro `agent.md`), y `~/.minimax/skills` no existe: el `SKILL.md` vive **solo en el repo** |

### Desviaciones del encargo, y por que

- **El gate es el check 11, no el check 10.** El 10 ya estaba ocupado por el
  contrato de persistencia (`validate_docs.py:2600`). Numerarlo 11 no cambia
  el diseno: lo pedido era «el gate va en `validate_docs.py` y no en la suite».
- **El gate no anade nada a la lista de saltados, ni en el caso del conjunto
  de sujetos VACIO.** MEDIDO en la suite: `test_el_informe_nombra_el_repositorio_del_anclaje`
  exige `assert not saltados` en una corrida SIN `--sin-ancla-de-git`, y
  `test_sin_ancla_de_git_no_se_parece_a_un_verde` exige **exactamente 3** saltados
  con el flag. El conjunto vacio se anuncia con un **REGISTRO impreso**
  (`entradas cubiertas=0, mutantes re-derivados=0`) y **sin** linea de `[OK]`,
  que es lo que haria verde por omision.
- **El `ast.parse` de `run_tests.py` (3 459 ms) se paga UNA vez.**
  MEDIDO: el validador lo parseaba DOS veces (el recuento y el reparto) y el
  gate lo necesitaba una tercera. Con una cache por contenido, el validador
  entero baja de **11 401 ms a ~4 400 ms** y el gate no paga el arbol.

### La reproduccion real de M-3 (AC-3)

Camara nueva de este ciclo (indice del repo real replicado), mutacion REAL
aplicada (`run_tests.py:23459-23460`, el reloj de la fixture sin clavar), la
suite COMPLETA cuatro veces: **1 de 4 muere por el asa** (el pre-vuelo, con el
motivo que nombra la infraccion) y **3 de 4 por el tripwire**. El veredicto del
mutante es **NO MEDIDO**, y el gate lo dice (K-6 lo mata).

### Lo que falta (y es de otro ciclo)

`TASK-088` (el guard DERIVADO de la familia de las 21 fixtures) y `TASK-089`
(el guard de suite que detecte que el arbol se movio durante la corrida) siguen
abiertos: no son de este encargo.


---

## Ronda de cierre — TASK-087 (ciclo 70), los TRES huecos de la auditoria

**Estado:** HECHO. La auditoria del Paso 4 dio **PARTIAL** (14 de 16 mutantes
muertos) y dejo **tres** cosas abiertas. Ninguna era un rediseno: eran tres
arreglos acotados, y aqui esta lo que se midio de cada uno.

### A · K-8, el guard se puede desenchufar (superviviente)

`validar()` podia dejar de llamar al check 11 y el validador daba **160 OK,
0 FAIL y SIN REGISTRO**: nadie lo notaba. El repo ya tenia el patron para el
check 9 (un test de «mutante de cableado»); **el check 11 no lo tenia**.

**Reparacion:** el test de cableado del check 9 (`run_tests.py`, fila 130 de
`docs/ai/testing-guide.md`) crece y exige **ademas** que el check 11 este
cableado y que su **REGISTRO** se imprima, con su propia mitad mutante (la
llamada sustituida por `pass`). El **recuento NO se mueve**: sigue en
**235 = 159 + 76** y las **cinco** declaraciones siguen donde estaban, porque
no se anade ningun `test_*` nuevo.

**MEDIDO en camara** (`%TEMP%\wopt_c71_k8`, arbol copiado del repo, sin
`.git`): con todo cableado el test sale **rc = 0**; con el check 11
desenchufado sale **rc = 1** con `AssertionError: el check 11 tiene que
CORRER dentro de \`validar()\`: su REGISTRO no aparece en el informe`. O sea:
K-8 **muere**, y el control positivo esta.

### B · El docstring del gate declaraba 3 limites y le faltaban 2

Faltaban los dos limites que la auditoria midio como **GUARDA MUERTA**: la
**evidencia fabricada** (K-10b: el frame del traceback en otro fichero ->
**0 FAIL**) y el **sha inexistente** (K-12 -> **0 FAIL**). Los dos estan
escritos **con su motivo medido**, y la lista declara que **NO es
exhaustiva**: es la de los limites **medidos** hasta ahora (K-1..K-17). Lo
que si es exhaustivo es la lista de lo que el gate **prueba**, que sale del
codigo.

**MEDIDO ademas la consecuencia que pedia el encargo:** el sha de la camara
(`e8111158…`, el del arbol auditado, que no existe en ningun arbol del repo)
**no** hace fallar el gate — en las celdas del harness del auditor la entrada
del journal lleva ese sha y no hay ni un FAIL por el sha — y la **coherencia
entre catalogo, journal, changelog e informe si se exige**: K-9c, K-11, K-14 y
K-15 siguen muertas cada una por su asercion.

### C · El emisor pisaba la evidencia de los mutantes que no le pasabas

Emitir el veredicto de un mutante **destruia** la evidencia commiteada de los
otros (la reescribia con «no hay ninguna corrida»), y con el mutante pisado
declarado NO MEDIDO el gate no se enteraba: era un verde por omision.

**Reparacion:** el emisor escribe la evidencia **solo** de los mutantes con
corrida, y no toca la de los demas. El mutante sin corridas sigue recibiendo
su linea canonica (NO MEDIDO: sin evidencia no hay veredicto), pero **sin**
evidencia escrita: el gate exigira la evidencia commiteada y su ausencia es
un FAIL, que es lo correcto.

**MEDIDO** (catalogo de DOS mutantes, un solo `--log`): la evidencia ajena
queda **IDENTICA byte a byte** (161 B antes y despues, mismo sha1
`1e59ac381b8110e5`) y la del mutante que si se le pasa se escribe (167 B, con
el frame del log).

### Los 14 mutantes que el auditor dio por muertos, siguen muertos

Reejecutadas **todas** las celdas del harness del auditor contra el codigo de
esta ronda (arbol `pristine` rehecho con el repo actual): K-1, K-2, K-3, K-4,
K-5, K-6, K-7, K-9a/b, K-9c, K-10a, K-11, K-14, K-15 y K-17 mantienen su
veredicto (diferencial SANO/MUTADO con la guarda que dispara en la celda sana
y NO en la mutada). K-10b y K-12 siguen siendo **GUARDA MUERTA**, que es
justo lo que el docstring declara ahora.
