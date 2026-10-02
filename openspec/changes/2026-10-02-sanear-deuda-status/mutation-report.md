# Informe de mutacion — saneamiento del panel de Deuda Tecnica Conocida

Change: `2026-10-02-sanear-deuda-status` · Tarea: `TASK-058` · Ciclo: `#48` · **ronda de cierre**
(la implementacion de la ronda anterior quedo comiteada y la auditoria dio **FAIL**; el bucle
volvio al Paso 3 con el informe, y un superviviente se arregla, no se documenta).

> **Quien escribe esto y quien no.** Este fichero lo escribe `openspec-dev` como
> **autoprueba** de su propia ronda de cierre, con la misma funcion que cumplio en el ciclo #47:
> sin el, un `FAIL` **no es re-auditable por nombre**. Ya paso dos veces en este repo —los 12
> supervivientes del ciclo #30 y los del ciclo #47 no se podian ni greppear— y esta vez el
> informe de sesion que los describia **muere con la sesion**. Un `VERDICT` de
> `mutation-auditor` es otra cosa: cuando el auditor pase, su veredicto se anade aqui y este
> texto se conserva como la medicion previa.

## 1. Por que este ciclo necesita un informe y no un `PASS`

Este ciclo **no cambia producto**: cero modifications en `src/`, cero tests nuevos, suite en 103.
No hay, por tanto, un fix de codigo que mutar. El objeto mutado es **el panel mismo**, y sus
supervivientes no son tests que no matan un bug: son **afirmaciones del panel que nada puede
contradecir**. Por eso el informe se estructura por fila y lleva la mutacion literal, porque
"esta fila dice algo falso" no es re-auditable si no se sabe que frase cambiar.

Las tres verificaciones obligatorias quedan en verde con el panel ya saneado (seccion 6). El
`110 OK / 0 FAIL` **no es el veredicto de este informe**: es la prueba de que el panel tampoco
esta verificado, que es justo lo que mide S48-3.

## 2. Como se ejecuto

| Pieza | Detalle |
|---|---|
| Sujeto | El panel (`STATUS.md`) y, para S48-2, el `git_safe_commit.py` del arbol de trabajo **byte a byte**, con SHA-256 del original verificado antes y despues de mutar |
| Que se exige | Que el mutante **MUERA**; un superviviente se declara con su severidad y su razon |
| Restauracion | Original restaurado y SHA-256 re-verificado; si no coincide, el script aborta con asercion |
| Purga | `.taskmaster/__pycache__` se borra antes de la suite, para que ningun mutante se mida contra un `.pyc` viejo |
| Historial real | Ninguna fixture lo toca: cada repo de sonda es un `tempfile` con su propio `GIT_DIR` |

### La trampa del VFS: un hash igual no prueba que el mutante estuviera puesto

**Esto costó una medicion y casi produjo un veredicto falso aqui, asi que queda escrito.**

La primera sonda aplico la mutacion y, acto seguido, reimprimio el SHA-256 del fichero mutado:
**salio identico al del original**. La mutacion **nunca llego al disco** (este arbol vive en un
Directorio de Nextcloud con Virtual Files). El script, tal como estaba, iba a imprimir
`SOBREVIVE` y a dar por bueno un mutante que en realidad no se habia medido.

La regla que sale de ahi, y que es la parte transferible de este informe:

> **En este repo, confirmar un mutante por hash NO basta. Hay que confirmarlo por
> comportamiento.**

La sonda se reescribio para exigir dosconfirmaciones independientes del hash: releer los bytes
en el mismo proceso, y **comportamiento** (con el camino de commit mutado a `0`, el wrapper tiene
que salir con `0`; si sale con `1`, el mutante no esta y la medicion se **aborta** en vez de
inventarse un veredicto). Ese es el unico motivo por que S48-2 es un superviviente creible y no
una conjetura.

## 3. Los tres supervivientes

### S48-1 — La gravedad de una fila se puede rebajar sin que nada lo note · severidad 🔴

| | |
|---|---|
| **Mutacion literal** | `STATUS.md:88`: `🔴` -> `🟡` en la fila del `spawn EPERM`. Es exactamente lo que hizo la ronda anterior de este mismo ciclo |
| **Estado del repo que lo dispara** | El panel es markdown y `validate_docs.py` **no contiene ni una coincidencia de `Deuda`** (medido), asi que ningun check alcanza los emojis de gravedad |
| **Por que sobrevive** | Las dos versiones son indistinguibles para el toolchain: el validador da `110 OK / 0 FAIL` con 🔴 y con 🟡. Solo un lector puede notar que 🟡 era una **infravaloracion**: un panel que infravalora una deuda hace que el bucle la trate como resuelta y la abandone. Es **documentacion fail-open**, la clase de fallo que este mismo ciclo sana en las demas filas |
| **Severidad** | 🔴 — es la clase que el panel existe para impedir, y occurrio aqui mismo hace dos dias |
| **Donde muere** | **En ninguna parte por herramienta.** La auditoría lo cazó **leyendo**, no mutando. Arreglado en `STATUS.md:88` (vuelta a 🔴, con su ancla y el codigo de salida medido) y documentado en `docs/ai/sandbox-rules.md`, seccion «Cobertura» |

### S48-2 — El codigo de salida del fallo de git no lo comprueba nadie · severidad 🔴

| | |
|---|---|
| **Mutacion literal** | `.taskmaster/git_safe_commit.py:230`: `sys.exit(CODE_FAIL)` -> `sys.exit(CODE_OK)` en el camino de commit (`print(f"WOPT_FAIL commit ...")` en 229) |
| **Estado del repo que lo dispara** | 103 tests en verde y `validate_docs.py` en `110 OK / 0 FAIL` |
| **Medicion** | Mutante confirmado por hash (`c248f694…` -> `ddac118f…`) **y por comportamiento** (el wrapper pasa a salir `0`). Suite completa: **`ALL TESTS PASSED.`, exit 0**. Tras restaurar, el wrapper vuelve a salir `1`. **SEGUNDA MEDICION, independiente y del auditor de cierre:** el mutante **tambien sobrevive a `validate_docs.py`** (`110 OK / 0 FAIL` con el mutante puesto). Se declara aparte porque el validador es **el otro semi-verdicto del toolchain**, no una repeticion de la suite: dos comprobaciones que dan el mismo veredicto sobre la misma linea no son dos testigos, son uno medido dos veces |
| **Por que sobrevive** | `run_tests.py:1352 test_git_safe_commit_fail_safe` solo ejercita las puertas de **uso incorrecto (2)** y de **repo no verificable (3)**: sus aserciones son `returncode == 3` (`:1399`, `:1413`, `:1423`) y `== 2` (`:1435`). **Ninguna de sus invocaciones llega a un `WOPT_FAIL`.** El invariante que el ciclo #11 rompio —*un fallo de git tiene que salir con un codigo distinto de 0`*— es el unico que no tiene test |
| **Severidad** | 🔴 — este wrapper es la unica puerta de versionado del repo; un falso verde ahi pierde commits en silencio, que es literalmente el fallo del ciclo #11 |
| **Por que nadie lo escribio (medido, y no es pereza)** | `get_env()` respeta un `GIT_DIR` del entorno pero **impone `GIT_WORK_TREE = REPO_ROOT` sin condicion** (`.taskmaster/git_safe_commit.py:78`): una invocacion con un `GIT_DIR` desechable sigue haciendo `add -A` y `commit` **sobre el arbol de trabajo real**. Medido: una sonda con `GIT_DIR` temporal stageo y commiteo el arbol real dentro del repo temporal (el historial real quedo intacto). El hook que `docs/ai/sandbox-rules.md:78-80` llama «tests hermeticos» es hermetico **en el repo, no en el arbol de trabajo**, y por eso el test existente solo toca las dos puertas que devuelven antes de cualquier `add` |
| **Donde muere** | **En ninguna parte.** Cerrarla exige una **decision de diseno** antes que un test (honrar `GIT_WORK_TREE` del entorno, o que el test mute el arbol real a proposito y lo declare). Anotado en `STATUS.md:88` y en `docs/ai/sandbox-rules.md`; desde el cierre del ciclo #48 tiene dueno: **`TASK-061`** (prioridad alta, `pending`), cuya primera funcion es **decidir antes de testar** |

### S48-3 — Una fila viva falsa es indetectable, y hay una instancia medida · severidad 🟡

| | |
|---|---|
| **Mutacion literal** | `docs/index.md:25`: `103` -> `96`. Es literalmente lo que ese fichero decia antes de este ciclo |
| **Estado del repo que lo dispara** | 103 tests reales; el validador en verde con las dos cifras |
| **Por que sobrevive** | El check del recuento vigila **cuatro** testigos: `STATUS.md`, `AGENTS.md`, `README.md` (`validate_docs.py:116-118`) y la tabla de `docs/ai/testing-guide.md` (`:142-160`). **`docs/index.md` es un quinto declarante y no esta en la lista** (medido: `docs/index.md` no aparece en `validate_docs.py`). Ademas no puede entrar con el patron de los otros tres: usa otra forma —`(103 tests)` dentro de un bloque de codigo, no `run_tests.py` + `\d+ tests`—, que es el mismo motivo que da `validate_docs.py:128-133` |
| **Por que la seccion entera es el agujero** | De las 13 filas que audito el ciclo #48, **mintieron tres** (85, 88, 97) y **no las detecto nadie**: el panel es la entrada de mayor palanca del bucle y `validate_docs.py` no lo mira |
| **Severidad** | 🟡 — documento publicado desfasado (`mkdocs.yml:70` lo expone como portada), sin efecto sobre el producto. La fila sube a 🔴 el dia que la afirmacion falsa sea de versionado o de datos |
| **Donde muere** | **En ninguna parte hoy.** El arreglo es `TASK-060` (check 8), cuyo criterio completo esta escrito en la fila del panel para que se ejecute sin volver a preguntar nada |

## 4. Los confirmados: lo que NO hay que re-auditar

Para que el proximo `mutation-auditor` no repita el trabajo ya verificado. Cada uno con su
comprobable y **con el comando que lo re-verifica en segundos**:

| Fila | Que se afirmo | Como se re-verifica |
|---|---|---|
| **85** | 11 `test_*.py` archivados; **10 de 11** morian por `import process_manager` y `test_powershell_direct.py` **no** | `docs/archive/legacy-root-tests/` tiene **11** ficheros, **0** `test_*.py` en la raiz, y el guard vive en `run_tests.py:11590`. Verificado con `ast.Import` sobre los 11: importan `process_manager` los 10 primeros; `test_powershell_direct.py` importa solo `os, subprocess, sys, time` (y su cuerpo menciona `notepad` y `taskkill`) |
| **88** | «Sin commit desde el ciclo #14» era FALSA | `python .taskmaster/git_safe_commit.py --verify` -> `WOPT_REPO_OK …`, **exit 0**. El dato real es «sin commit **anclado**», que vive con su severidad en la fila 93 |
| **91** | La cola apuntaba a `TASK-031`, ya cerrada | `TASK-031.status == "completed"` en `.taskmaster/tasks.json`; cerrada con L1-L12 en `openspec/changes/2026-09-30-validate-pack-leaves/` |
| **92** | El ancla ya no se deduce del journal | `validate_docs.py:238 _ciclos_de_commits(asuntos)` y `validate_docs.py:267 _comprobar_ancla_de_commits(root, errors, ok, journal_cycles)`: el requisito es la **union** journal \| historial. Su residuo vive en la fila 93 |
| **97** | `docs/api.md`/`docs/index.md` documentaban una API v2 | `docs/api.md:1` es «Referencia de API (v3)»; **cero** ocurrencias de `is_admin` y de `taskkill` en ambos; el test que lo impide volver es `run_tests.py:11478 test_docs_api_and_index_v3_contracts` |

## 5. Una conclusion de la auditoria que resulto falsa (para que no se repita)

La auditoria reporto que `test_profiles_task1.json` era un «artefacto no versionado creado en este
ciclo». **Es falso, y medido:** `git log --diff-filter=A -- test_profiles_task1.json` -> **`8efc0ae`**
(`feat(ui): implement pack manager view and process service methods`), y `git ls-files` lo lista.
Es un fichero **versionado desde hace ciclos**.

Lo mismo con `_matrix_c26.py`, en la raiz: añadido en **`b7e5f54`** (`fix(ui): honestidad del
feedback inline y guards exhaustivos (TASK-035)`) y tambien versionado.

**Ninguno de los dos se toca.** Borrarlos seria un cambio que nadie ha pedido, y el mismo hueco
que el ciclo #47 sello: una conclusion de auditor que no se mide antes de mover el árbol

## 5 bis. Dos anclas que el contrato daba por buenas y no lo eran

La ronda de cierre tuvo que **resolver por contenido cada ancla `fichero:línea`** que iba a escribir
en las filas tocadas, y dos no resolvieron. Las dos venían **del contrato de este mismo change**
(`openspec/changes/2026-10-02-sanear-deuda-status/proposal.md:36` y `openspec/changes/2026-10-02-sanear-deuda-status/tasks.md:54`), no de esta ronda, y por eso conviene que queden escritas: quien
ejecute ese contrato al pie de la letra reintroduce dos anclas falsas.

| Ancla del contrato | Donde apunta de verdad | Ancla correcta |
|---|---|---|
| `STATUS.md:37` (el hito del ciclo #11) | `STATUS.md:37` es el hito del **ciclo #10** (`model_copy()` shallow). El del ciclo #11 esta **una linea mas abajo** | `STATUS.md:38` |
| `.taskmaster/CHANGELOG.md:1525` (evidencia del `spawn EPERM`) | Esa linea es una de **benchmark** («cold_scan 15ms, cached 0.003ms»), asi que no habla ni de `spawn EPERM` **ni** de `model_copy()`: el `model_copy()` shallow esta en `:1593-1594`. La entrada que documenta el fallo intermitente del shell esta mucho mas abajo | `.taskmaster/CHANGELOG.md:1723` |

**Y las dos tienen causas DISTINTAS, que es lo que faltaba.** El de `STATUS.md:37` a `:38` SI
viene de que el contrato numera las filas contando el encabezado de la seccion como la fila 85,
mientras que el numero de linea real del panel es esa cifra mas uno: un off-by-one de esa
convencion, y solo de ahi. El de `.taskmaster/CHANGELOG.md` **no**, y ninguna convencion de
numeracion de filas del panel lo explica: ese fichero inserta cada ciclo al principio, de modo
que una cita de linea envejece por si sola con cada entrada nueva (**160** lineas de desviacion:
el contenido real de esa entrada esta en `.taskmaster/CHANGELOG.md:1685` de `HEAD~1` y la cita del
contrato decia `:1525`, medido con `git show` de solo lectura). **Las filas de `STATUS.md` que se
citan aqui son numeros de linea reales del fichero**, y todas las anclas de esta tabla se
comprueban por contenido, no por memoria.

## 6. Verificaciones (comando y salida real, no «se verifico»)

```text
$ python verify_ui_syntax.py
Validando sintaxis estatica de la Fase 3...
OK: src/woptimizer/ui/app.py compila perfectamente.
OK: src/woptimizer/ui/main_window.py compila perfectamente.
OK: src/woptimizer/ui/confirmation.py compila perfectamente.
OK: src/woptimizer/ui/feedback.py compila perfectamente.
OK: src/woptimizer/ui/views/dashboard_view.py compila perfectamente.
OK: src/woptimizer/ui/views/pack_manager_view.py compila perfectamente.
OK: src/woptimizer/ui/views/process_manager_view.py compila perfectamente.
OK: src/woptimizer/services/notification_service.py compila perfectamente.
OK: src/woptimizer/__main__.py compila perfectamente.
EXITO: Todos los modulos UI estan impecables.
exit=0

$ python run_tests.py
Testing DashboardView adaptive favorites grid contracts...
test_dashboard_favorite_grid_adaptive_contracts OK.
Testing ProcessManagerView DB update button and feedback contracts (TASK-051)...
test_process_manager_db_update_button_and_feedback OK.
Testing ProcessManagerView pack dropdown single arrow and placeholder (TASK-052)...
test_process_manager_pack_dropdown_single_arrow_and_placeholder OK.

ALL TESTS PASSED.
exit=0

$ python validate_docs.py
  [OK]   run_tests.py: 103 tests definidos = 103 invocados (derivado con ast)
  [OK]   STATUS.md: declara los 103 tests que run_tests.py tiene de verdad
  [OK]   AGENTS.md: declara los 103 tests que run_tests.py tiene de verdad
  [OK]   README.md: declara los 103 tests que run_tests.py tiene de verdad
  [OK]   docs/ai/testing-guide.md: 103 filas de test, una por test definido

Resumen: 110 OK, 0 FAIL
exit=0
```

Las tres en verde con la suite en **103 tests** (no crece: este ciclo no anade ninguno). Y una
lectura que hay que hacer bien: ese `110 OK / 0 FAIL` sale **con el panel ya saneado y con
`docs/index.md` en 103**, y **saldria igual con `docs/index.md` en 96**. Es S48-3 Medido.

## 7. Lo que este informe NO declara

- **La unica medicion de muerte que hay aqui es S48-2, y se hizo contra la suite completa.** No
  se midi mutante por mutante contra los 103 tests uno a uno (serian 309 ejecuciones), asi que
  «sobrevive» aqui es una **cota**: si S48-2 aparece sin guardianes, tiene **cero**, que es lo
  que se midio.
- **S48-1 y S48-3 no se «mataron»**: se corrigieron. Su muerte depende de `TASK-060`, que aun no
  existe. Hasta entonces son supervivientes vivos, y por eso estan en la seccion 3 y no en la 4.
- **Las sondas sobre este wrapper no son libres de efectos secundarios.** `GIT_WORK_TREE` se
  impone al arbol real (S48-2): quien repita la medicion debe saber que va a stagear y commitear
  el arbol de trabajo real **dentro de un repo desechable**, y que el historial real no se toca.
  Por eso el protocolo de la seccion 2 exige repo nuevo por sonda y hash verificado.
- **Esto no es un `PASS`.** Es la autoprueba de la ronda de cierre de `openspec-dev`. El
  veredicto de `mutation-auditor` sobre esta ronda se anadira aqui cuando exista, y este texto se
  conservara como la medicion previa.

## 8. Quinta ronda: cifras y citas que no se habian medido (2026-10-02)

La reauditoria de la cuarta ronda dio FAIL otra vez, y esta vez sobre el contenido y no sobre el
codigo: los tres hallazgos de la ronda anterior estaban cerrados y verificados por contenido, pero
**ocho afirmaciones que este ciclo habia escrito no se sostenian**. Todas son de la misma clase
--una cifra o una cita que nadie contrasto contra el fichero-- y todas se corrigen en los dos
changelogs y en el panel.

| # | Que se afirmo | Medido | Donde se corrige |
|---|---|---|---|
| 1 | «diecises», en 3 sitios | Era `diecisis`: la `e` y el acento en el sitio equivocado, y **0** ocurrencias de la forma correcta en el repo | `STATUS.md`, `CHANGELOG.md`, `.taskmaster/CHANGELOG.md` |
| 2 | Este informe, `:128` col. 2: «esa linea habla de `model_copy()` shallow» | `:1525` es una linea de **benchmark** («cold_scan 15ms, cached 0.003ms»); el `model_copy()` shallow esta en `:1593-1594` | este informe |
| 3 | `STATUS.md:9`: «93 backend + 10 headless» | **Es derivable y sale exacto**: marcador `run_tests.py:12919`, 93 llamadas `test_*()` antes y 10 desde el, contado con `ast` | `STATUS.md:9`, con su ancla y con su limite |
| 4 | «dos sitios sin tocar»: el bloque `CYCLE-017` y las notas de `TASK-011` | `CYCLE-017` va de `:1852` a `:1883` y tiene **cero** ocurrencias de `CHANGELOG.md:91`; `TASK-011` **no tiene campo `notes`**. La cita esta en `:1747` (dentro de `CYCLE-015`) y las dos de `tasks.json` (`:423` y `:455`) son de `TASK-026` | ambos changelogs |
| 5 | «cero cambios en `run_tests.py`», en 5 sitios, uno de ellos del commit que lo escribio | Falso desde ese mismo commit: `run_tests.py` cambio en **1 linea de docstring** (`git show 9a8e952 -- run_tests.py`) | `CHANGELOG.md`, `.taskmaster/CHANGELOG.md` (3), `STATUS.md` |
| 6 | «esta entrada anade 68 lineas» y «desviaciones de 130 a 1240» | **65** lineas (39 + 26 con `git show --numstat 9a8e952`; el commit entero son 87 inserciones y 18 borrados). Desviaciones de **160 a 1270** contra `HEAD~1` y de **198 a 1308** en `HEAD`, cada una resuelta por contenido | ambos changelogs y este informe |
| 7 | P1: «9 cerradas, offsets 37 a 825» | **Dos criterios en una frase**: el 9 salia por resta (`15 - 5 vivas - 1`) y los offsets por otra regex. Con un criterio unico (marcador `CERRADA`/`CERRADO` en mayusculas): **8 filas lo llevan** (la 95 en el offset 6, otras 6 en offsets 200-825, y la propia 100, que lo lleva porque el criterio esta escrito en ella) y **7 no** (87, 88, 90, 91, 94, 97, 99). **Ninguna** lo tiene en el offset 0 que P1 exige | `STATUS.md:100` y `CHANGELOG.md` |
| 8 | «era cierta el 2026-10-01» | Falsa ese mismo dia: `CYCLE-041` (`.taskmaster/CHANGELOG.md:397`, 2026-10-01 23:25) es **el mismo change** que escribio la frase y el que conecto el boton. Era cierta **a mas tardar el 2026-09-30** | `CHANGELOG.md` |

**Dos mas, que aparecieron al re-medir y no estaban en el encargo.** Dos citas de
`.taskmaster/CHANGELOG.md` envejeceron **38 lineas** con este mismo commit: la regla que escribe la fila
100, visas ocurrir aqui. `STATUS.md:88` apuntaba a `:1685` (hoy la entrada del `spawn EPERM` esta en
`:1723`) y `docs/ai/data-models.md:291` apuntaba a `:1361` (hoy la linea de la rotacion esta en
`:1399`). Las dos, corregidas al contenido. Y al medir la desviacion de las seis citas se confirmo lo
que ya se afirmaba, ahora con las cifras que lo sostienen: **ninguna de las 6 se rompio por las lineas
de este ciclo**, porque el `numstat` de `9a8e952` no tiene ninguna linea de `src/`.

**La decision del punto 3, y por que se deriva en vez de retirarse:** sale exacta del marcador
estructural de `run_tests.py` con `ast` (93 antes, 10 desde), y el total ya se deriva con el mismo
metodo. Lo que queda escrito en `STATUS.md:9` es la cifra **con su ancla y con su limite declarado**: el
total lo vigila el check 7 de `validate_docs.py`, **el reparto no lo vigila nada**. Anadir esa
comprobacion al validador es `TASK-060`, no de este ciclo.

**Lo que esta ronda NO arregla:** la convencion de anclas por `fichero:linea` sigue en pie y sigue
caducando sola; se anota con su medida y **sin parcheo**, porque es contrato de otro change.
`openspec/changes/2026-09-30-close-mutation-survivors/proposal.md:17` cita `CHANGELOG.md:57-67` como
«seccion CYCLE-017», y en el changelog de la raiz `:57` es una fila de la tabla de seis anclas de este
ciclo y `:67` es `## CYCLE-047 - 2026-10-01`; la `CYCLE-017` real esta en `:724` de la raiz y `:1852`
del tecnico. El dueno es de `architect-review`: el arreglo es cambiar la convencion, no un numero.
