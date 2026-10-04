## [CYCLE-053] 2026-10-04 - codigo-salida-fallo-git-s48-2

**Area**: Arquitectura & Calidad. **Change**: `openspec/changes/2026-10-04-codigo-salida-fallo-git-s48-2/`
**Estado**: **COMPLETED con veredicto `PASS` en la re-auditoria.** `TASK-061` en `completed`. El Paso 4 dio `FAIL` en la ronda 1 con 6 supervivientes; los 6 se cerraron en `ef67bf8` y la re-auditoria los dio muertos, ademas de 14 mutantes nuevos del auditor.
**Commits**: `9f60e41` (arquitectura), `4879d19` (implementacion T-1..T-6), `ef67bf8` (cierre de los 6 supervivientes + las 2 afirmaciones documentales), `82f52c2` (retirada de `run_tests_out.txt`, que `add -A` se habia tragado en `ef67bf8`).
**Tests**: 132 -> **144** (112 backend + 32 headless). Las 5 sondas del cierre van **antes** del marcador headless (son tooling puro) y las 3 de T-2/T-3/T-4 **despues** (levantan la UI), de modo que "tooling puro" ya no significa "lado headless" y queda avisado en `STATUS.md` y en `testing-guide.md`.

**Decision D1 (arquitecto), y la via descartada.** `get_env()` honra `GIT_WORK_TREE` del entorno igual que honra `GIT_DIR`, y exige **paridad**: llegar con una sola de las dos se rechaza con codigo 2 y `WOPT_USAGE paridad-git` sin escribir nada. La alternativa era que el test mutara el arbol real y su harness lo revirtiera; **ya se hacia** (`run_tests.py:16412-16413`, el "truco declarado del ciclo 52") y su coste medido es el residuo que el proximo `add -A` se lleva. Ademas, meter un test que escribe en un arbol con `.git` corrupto por VFS es pedir el incidente que ya ocurrio dos veces. Compatibilidad medida por enumeracion de las 3 invocaciones vivas del wrapper: las 3 ponen `GIT_DIR` **y** `GIT_WORK_TREE` al mismo valor, luego ninguna queda con una sola variable y el camino normal queda byte a byte igual.

**HALLAZGO CRITICO, y es el que mas valor tiene: el mutante NO estaba en la linea que decía la ficha.** S48-2 apuntaba a `git_safe_commit.py:230`, pero hoy esa linea es `sys.exit(CODE_USAGE)`: la puerta que TASK-059 inserto **despues** de la medicion original. El mutante real esta en `:409-410` (`print` de `WOPT_FAIL commit` + el `sys.exit` que le sigue). Un auditor que hubiera mutado la `:230` reportaria `killed` (el test de TASK-059 la mata) y habria cerrado S48-2 **sin haberlo medido nunca**: un falso verde producido por una mutacion inerte. Segunda premisa falsa propagada: `get_env()` no esta en `:78` (esa es la regex del ancla) sino en `:132`, y la ancla viajo a 4 ficheros. Tercera: el repo ya estaba en 136 tests, no en los 103 del encargo, con el marcador en `run_tests.py:17956`. **Regla que sale de aqui: localizar por CONTENIDO, nunca por linea.**

### Mutaciones auditadas (Paso 4)
| Fix | Mutacion | Veredicto | Motivo del fallo |
|---|---|---|---|
| S48-2 (central) | `WOPT_FAIL commit` -> `CODE_OK` | killed x2 | T-2: *"la tabla (marcador, codigo) que produce el codigo REAL no es la que el contrato declara"*; T-3: *"un commit que falla tiene que salir con 1, y salio con 0"* |
| M5 posicion de la puerta | paridad antes de `validar_repo` | killed | *"con un par ASIMETRICO y un repo NO verificable tiene que ganar el 3 ... y salio con 2"* |
| M6 cobertura de `--verify` | `if paridad_rota and not verify:` | killed | *"`--verify` con el par ASIMETRICO tiene que salir con 2 ... y salio con 0"* |
| M7/M8 arbol no-directorio | quitar `isdir` / `isdir`->`exists` | killed | *"el rechazo tiene que venir del PRE-CHEQUEO del arbol ... no de un rc de git"* |
| M9 `is-inside-work-tree` | `!= "true"` -> `!= "false"` | killed | *"que responde FALSE tiene que hacer RECHAZAR el repo ... y `validar_repo` devuelve ok=True"* |
| M10 marcador huerfano | `print WOPT_INVENTADO` sin salida | killed | *"hay 1 marcador(es) WOPT_* impreso(s) en main() que NO estan en la tabla"* |
| M10b reutilizacion | `WOPT_FAIL` reusado en otra salida | killed | segunda mitad: *"NO cierran un `sys.exit` en su bloque"* |
| R2-1/R2-1b control de M9 | `validar_repo` que rechaza / acepta siempre | killed | control no decorativo: puede fallar, y M9 muere por su criterio |
| R3-a/R3-c autoderivacion | tabla de M10 y `esperado` de T-2 derivadas del wrapper | killed | prueba de que **no** se autoderivan: si se derivaran, estos mutantes pasarian |
| R3-b/d tablas a mano | `TABLA` sin `WOPT_REPO_OK` / `WOPT_FAIL` x5 | killed | prueba de que estan escritas a mano |
| R4-h hash en NOOP | `WOPT_NOOP` imprime un hash | killed | *"tras la linea WOPT_NOOP no puede aparecer ningun hash"* (el dano del ciclo #11, otra puerta) |
| P2-real ancla de mentira | `T-\d+` se acepta de verdad | killed | *"'fix(x): T-9' tiene que ser rechazado ... admitirlo es un ancla de mentira"* |
| P5 fail-open | `ids` vacio degrada a forma | killed | dos sondas: *"Devolvio ok=True"* |
| P6 orden de fronteras | puerta del mensaje antes del NOOP | killed | *"el orden de las cuatro fronteras del wrapper es normativo y esta roto"* |
| **R4-k** | **`if paridad_rota:` -> `and ok:`** | **🟡 survived** | ver abajo |

**EL UNICO SUPERVIVIENTE: R4-k.** Con el par asimetrico y el repo no verificable en el **camino de commit**, el codigo real es `2 WOPT_USAGE paridad-git` y con el mutante sale `3 WOPT_REPO_INVALIDO`. **No toca seguridad ni datos**: el `3` es un diagnostico MAS conservador, no una mentira como lo seria un `WOPT_REPO_OK` mintiendo. Pero `sandbox-rules.md:83-85` promete el `2` sin condicionar al repo sano, y con R4-k ese `2` no sale: **una promesa documentada sin guardian**, la misma clase que S48-2 un grado mas abajo. Arreglo que necesita: una fila en la sonda de posicion que exija `2` en el camino de commit con repo no verificable. **Queda como ticket re-auditable, NO se documenta como resuelto.**

### Las dos afirmaciones documentales que NO se sostenian
1. **`sandbox-rules.md:227`** (justificacion de la posicion de la puerta): *"los dos caminos de commit del test existente esperan **3** ... y pasarian a 2"*. **FALSA y no reproducible**: `test_git_safe_commit_fail_safe` pone `GIT_WORK_TREE = root` en **todas** sus invocaciones, luego el par nunca esta roto, la puerta no dispara y el test sigue verde. Reescrita con la combinacion que **si** distingue (`--verify` + par asimetrico + repo no verificable -> 3, y -> 2 con la puerta movida), verificada por ejecucion, y ahora sostenida por un guardian con nombre.
2. **Asercion 1 de T-2** (`proposal.md:239`): *"cada `print` con `WOPT_*` esta en la tabla"*. Prometida y no cumplida: la tabla solo registraba un marcador si detras habia un `sys.exit`, asi que un `WOPT_*` sin salida desaparecia del contador en silencio. El dev decidio **implementarla en el test** en vez de editar el contrato, con dos mitades (conjunto + huerfanos). Correcto: era el mismo fallo que S48-2 un grado mas abajo.

**Comprobado por el auditor, que es lo que mas importa de una re-auditoria:** la asercion 1 **no se autoderiva**. R3-a y R3-c (sustituir las tablas escritas a mano por derivadas del propio wrapper) **mueren**, y R3-b/d (borrar una entrada de la tabla) mueren tambien. Si la expectativa saliera del codigo, esos cuatro mutantes habrian pasado.

**Mutante inerte que confieso (metodo, no resultado):** el primer P2 del auditor cambio la regex de forma incompleta y seguia exigiendo `TASK-`, asi que era inerte y lo reporto mal. Rehecho con el match completo, P2-real muerde y muere. Un mutante que no cambia el comportamiento no es cobertura, y reportarlo como superviviente habria sido ruido de auditoria.

**Ruido que el `add -A` metio y se corrigio:** `ef67bf8` se trago `run_tests_out.txt` (354 lineas, el log de la propia corrida de la sonda) y un fichero literal `$null` de un `2>$null` de PowerShell. Retirados en `82f52c2`. El commit queda con ruido que ya no esta en HEAD; se declara en vez de reescribirse, porque reescribir historia por un log de sonda no compensa.

**Lo que se midio del recuento, por partida triple:** el validador lo deriva, el dev lo declaro, y el auditor lo conto desde cero con `ast`: **144 definidos = 144 invocados = 112 antes del marcador + 32 despues**, sin huerfanos en ningun sentido, cuadrando con los cuatro declarantes y con la tabla de `testing-guide.md`.

## [TASK-065] 2026-10-04 - favoritos en el menu de la bandeja

**Area**: Portada & Packs. **Change**: sin `change-id` propio; es la continuacion de TASK-048 (`is_favorite`) y cierra el hueco que la seccion TASK-025 de `docs/ai/ui-design-system.md` dejo escrito ("si algun dia se le quiere dar confirmacion, hay que anadir antes una superficie de estado al `MenuItem` (o un item de 'confirmar'), nunca un `messagebox`").
**Estado**: **COMPLETED.** `TASK-064` sigue `in_progress` (config de GitHub); esta es independiente.
**Tests**: 132 -> **136** (107 backend + 29 headless), derivado con `ast` por el check 7. Las cuatro sondas van ANTES del marcador headless porque no abren ventana: son estado puro + texto, sin Tk ni `pystray`.

**HALLAZGO PROPIO, y es el importante: la primera version de este cambio TENIA el fallo mortal.** La API inicial era `puede_ejecutar(pack_id) -> bool` y la sonda #1 la mato en la primera corrida: `puede_ejecutar` devolvia `True` **tambien tras la primera pulsacion** (que solo arma), porque `pendiente()` y `consume()` no distinguen "existe una pendiente" de "el usuario ha pulsado Confirmar". Con esa forma, un `if self._tray_state.puede_ejecutar(id):` en el item de apagar mata con UN clic, que es exactamente la excepcion de TASK-025 ampliada de 1 pack a N. **La API se rehizo en dos funciones separadas**: `armar()` NO devuelve nada y `confirmar()` es el unico `True` que significa "mata". Con esa forma el atajo es **inimputable por construccion**: no existe ninguna expresion que valga a la vez para el item de apagar y el de confirmar.

**Diseno de la confirmacion en el menu** (la unica via que la doc senalaba): el menu se **reconstruye entero** con `icon.update_menu()`, porque `pystray` sustituye la referencia y no permite editar el texto de un `MenuItem` in situ. `show_tray` delego en `_menu_tray()` para que no haya dos listas de items que puedan divergir. El item con pendiente viva se dibuja como `✅ Confirmar apagado de 'X'` y su **callback es otro** (`_confirmar_favorito`): texto y accion salen de la MISMA consulta de estado, asi que no pueden divergir.

**`DoubleTapGuard` reutilizado, no reimplementado**: `TrayMenuState` lo envuelve con un `TrayScheduler` sin hilo. El scheduler existe para que el guard conserve su ciclo de vida (cancelar al `reset`), y el reloj inyectado es lo que hace que una pendiente caducada se vea caducada sin que nadie redibuje nada. El caso §3.5 (pulsar otra accion descarta la pendiente) tambien es el del guard, no una regla nueva: por eso un `✅ Confirmar` nunca puede matar un pack que el usuario ya no tiene delante.

**Ventana de 4000 ms, no 2000**: la de la portada no aplica porque ahi el boton sigue ahi con su estado pintado, mientras que en el menu hay que reabrirlo, elegir el item y pulsarlo. Con 2 s la confirmacion caducaba antes de que el usuario llegara.

**Mutacion de control (4 mutantes, 4 muertos, restauracion por SHA256 y arbol intacto)**: M1 `armar` devolviendo `True` (mata por la asercion de que `armar` no devuelve nada), M2 `confirmar` saltandose `pendiente` , M3 caducidad eliminada, M4 `cancelar` que no limpia. Cada uno por SU asercion, no por un fallo de arranque.

**Frontera de capas**: `ui/tray_menu.py` solo importa `typing` y `woptimizer.ui.confirmation`. Prohibido `psutil`, `json`, `os`, `threading`, `pystray`, `woptimizer.services` y `woptimizer.models`. Ni la lectura de packs ni la cuenta de procesos a apagar ocurren ahi: eso lo hacen `WOptimizerApp` y sus servicios.

## [CYCLE-052] 2026-10-04 - marcador-ciclo-y-hashes-journal

**Area**: Arquitectura & Calidad. **Change**: `openspec/changes/2026-10-04-marcador-ciclo-y-hashes-journal/`
**Estado**: **COMPLETED.** `TASK-059` en `completed`. El **Paso 4 dio `FAIL` en la ronda 1** con 10 supervivientes de 40 mutantes; los 10 se cerraron y se re-auditaron en `d1c382a` antes de cerrar el ciclo.
**Models**:

- Paso 1 (Buscar): `inherit` — lectura de `rd_journal.json`, `STATUS.md` y `tasks.json`; la medicion de la linea base la hizo el orquestador
- Paso 2 (Planear): `inherit` — `architect-review`; el encargo con 4 premisas, **2 refutadas por medicion**
- Paso 3 (Ejecutar): `inherit` — `openspec-dev`, dos pasadas (feature + fix de integracion + fix de los 10 supervivientes)
- Paso 4 (Auditar tests): `inherit` — `mutation-auditor`; 40 mutantes en 5 camaras de `%TEMP%`

**HALLAZGO CRITICO, medido por el orquestador antes de propagarlo.** El `mutation-auditor` reporto S8 como un fail-open ("con `tasks.json` ilegible la puerta acepta cualquier `TASK-NNN`"). Es **invertido**: la puerta es **fail-CLOSED**. Medido importando el modulo y llamando `ancla_del_mensaje(msg, set())`, `TASK-059` devuelve `ok=False`. Ademas **tres fuentes** describian el comportamiento contrario (el docstring de `ancla_del_mensaje`, el mensaje de `ids_de_tareas` y D5 de la propuesta), y el codigo hacia una cuarta cosa. La decision de diseno fue **fail-CLOSED**, con la razon escrita: (b) degradar a la forma es exactamente el punto ciego que TASK-059 cierra. Verificar antes de propagar cambio el arreglo entero: no habia que abrir la puerta, sino alinear tres documentos con el codigo y **fijar el comportamiento con un test** (`ids_de_tareas` aparecia **0 veces** en `run_tests.py`).

**Mutaciones auditadas (Paso 4)**: 40 mutantes, 30 muertos por su asercion, 10 supervivientes cerrados en `d1c382a`.

| Fix | Mutacion | Ronda 1 | Cerrado en |
|---|---|---|---|
| S8 fail-closed de `ids_de_tareas` | `return {TASK-001..999}`, `None` | **SUPERVIVE** (0 cobertura) | test 132: fail-closed en los 3 mensajes con `TASK-`, aviso literal e `INFO` antes del rechazo |
| M6 techo de ciclos sin hash | `MAX_CICLOS_SIN_HASH = 999` | **SUPERVIVE** (fixture tautologica) | fixture con literal 3 + `assert` de igualdad del valor |
| M6b techo de hashes perdidos | `MAX_HASHES_PERDIDOS = 2` | **SUPERVIVE** | mismo arreglo que M6 |
| M9 pre-vuelo del repo | borrar `_leer_el_repo_si_lo_hay` | **SUPERVIVE** | fixture de `git init` **sin commits** (rc=0 y `missing` para todo, el caso que fabrica perdidas) |
| M10 linea de informe | `conformes += 7` | **SUPERVIVE** | fila que comprueba `1 conforme(s) a R1` |
| M1c resolubilidad | `search` en `pedidos` | **SUPERVIVE** (fail-open latente) | exigir la forma exacta de la respuesta de `cat-file` |
| S6 ancla sin limite de digitos | quitar el `\b` final | **SUPERVIVE** | asercion sobre `TASK-12345` vs `{TASK-1234}` |
| S9 `INFO` de degradacion | borrarlo | **SUPERVIVE** | cubierto por el test de S8 |
| T4 suelo de plantillas | 5 plantillas -> 1 | **SUPERVIVE** | el suelo se comprueba |
| S4 `_RE_CYCLE_ANCLA` | borrar el patron | **SUPERVIVE = EQUIVALENTE** | barrido 4 grafias x 10 000 numeros, 0 contraejemplos: todo `CYCLE-NNN` casa tambien con el marcador. Documentado como redundante, no como fallo |

**Lo que murio en la ronda 1 y no habria que volver a tocar**: `return True` fail-open, la forma `T-\d+` laxa, `TASK-999` sin resolubilidad, el `search` por `fullmatch` de R1 (el mutante clave: el hash con texto libre resuelve y daria 0 FAIL), la doble acusacion del journal ilegible, el codigo 2 de `WOPT_USAGE`, las **cuatro** colocaciones de la puerta (antes de `validar_repo`, antes del NOOP, tras `add -A`, antes de `--verify`), el `WOPT_*` no-ultimo, la degradacion silenciosa de la verificacion, y el des-cableado del check 9 en `validar()`.

**LO QUE NO SE VERIFICO, declarado y no medido**: el rechazo extremo a extremo con un arbol deliberadamente sucio. `get_env()` impone `GIT_WORK_TREE = REPO_ROOT` (`git_safe_commit.py:78`), luego un `GIT_DIR` temporal hermetiza el repo, **no el arbol**. Eso es `TASK-061`, que sigue `pending` y cuyo bloque es una decision de diseno, no un test que se anada.

### What
- `git_safe_commit.py`: `ancla_del_mensaje()` pura (3 formas), `ids_de_tareas()`, puerta entre el NOOP y `add -A`, codigo `WOPT_USAGE` (2), y el envoltorio de consola movido a `__main__` para que importar el modulo no secuestre `sys.stdout` del proceso de tests.
- `validate_docs.py`: check 9 `_comprobar_hashes_del_journal(root, errors, ok)` con R1 `fullmatch`, R2 resolubilidad, R3 `commits_perdidos` con `causa` en vocabulario cerrado, R4 antidolar y R5 techos leidos del producto. Cableado en `validar(root)`.
- `.taskmaster/rd_journal.json`: 49 entradas conformes (antes 27), 2 `NUNCA_DECLARADO` (ciclos 1 y 2) y 3 `VFS_CORRUPTO` (ciclos 30, 31, 33). Los 3 hashes muertos se verificaron uno a uno: `Not a valid object name`, la perdida es real.
- `SKILL.md` + los 4 `agent.md`: las 5 plantillas literales que fallaban la puerta propia del bucle. Medido: la puerta acepta 153 de 215 subjects (71%) y rechaza 60 (29%), o sea **no para el bucle**.
- Tests: 124 -> **132** (103 backend + 29 headless), derivado con `ast`.

### Outcome
- Commits: `531ac93` (arquitecto), `c900dbc` (feature), `cbf4c3f` (rojo ajeno de `20daaed`), `6420eb4` (una causa, un mensaje), `d1c382a` (los 10 supervivientes)
- Tests: **132/132 PASS** (`ALL TESTS PASSED.`, exit 0, verificado por el orquestador)
- `validate_docs.py`: **122 OK / 0 FAIL**. `verify_ui_syntax.py`: EXITO. `sync_agents.py --check`: 0
- Docs: `docs/ai/sandbox-rules.md` (+regla de la puerta, fila del codigo 2, seccion "UNA CAUSA, UN MENSAJE", 8 limites residuales), `mutation-report.md` con los 10 supervivientes por identificador

### Impact
Cierra el punto ciego que el ciclo #47 declaro: un commit ya no puede versionarse sin ancla por el unico wrapper del proyecto. El coste es deliberado y esta escrito: si `.taskmaster/tasks.json` se corrompe, el versionado se **detiene**. Se corrigio de paso un rojo ajeno que venia de `20daaed` (`llms-full.txt` sin regenerar) y un fallo de entorno que tenia la suite muerta desde antes del ciclo (`pydantic-core` 2.49.0 contra el 2.46.5 que exige `pydantic` 2.13.5).

### incidente
Dos hechos ajenos que afectaron al ciclo. (1) **Un escritor concurrente** commiteo `20daaed` y `1a06b80` a los 16 s de la ultima escritura del arquitecto y se llevo sus ficheros: su wrapper devolvio `WOPT_NOOP` y el trabajo acabo bajo un asunto ajeno. Es una instancia medida del dano del NOOP, y el asunto ajeno no llevaba identificacion, o sea el caso exacto que la puerta nueva rechaza. (2) **`run_tests.py` estaba muerto** por el desajuste de `pydantic-core`; sin el no habia Paso 4 posible, y el primer `openspec-dev` lo esquivo con un arnes temporal que **ocultaba fallos reales** (le tapaba el `NameError` de `json`). Arreglado por el orquestador; de ahi en adelante, suite real siempre.

## [CYCLE-051] 2026-10-03 - pack-seleccion-por-categoria

**Area**: Gaming y Telemetria UX. **Change**: `openspec/changes/2026-10-03-pack-seleccion-por-categoria/`
**Estado**: **COMPLETED.** `TASK-063` en `completed`. El **Paso 4 dio `PASS` en la ronda 11 de once**: el cambio de la FORMA al EFECTO cerro las diez familias de gate de una, y los dos ultimos supervivientes eran de otra clase (cableado cruzado y completitud del catalogo) y quedaron cerrados con E4 y E5.
**LO QUE NO SE VERIFICO, declarado y no medido:** el shell del host cayo en `spawn EPERM` al final de la ronda 11, asi que quedaron sin re-medir `K_CATEGORIA_SOLO_DB`, `PREMISA` y `D_C_ASSERT_GATE`, las regresiones `G_VAR`, `G_ALIAS`, `G_HELPER`, `F_MAP_LAMBDA`, `S1_SOLO` y `Z1` (que el dev midio en la ronda 10, sin cambios desde entonces), y la lectura final de `git status`/`log`/`diff` del arbol real. Ninguna es un punto del encargo ni un rojo.
**Models**:
- Paso 1 (Buscar): orchestrator. `active_task_id` apuntaba a TASK-059; se toma TASK-063 (high, sin dependencias, valor visible para el usuario)
- Paso 2 (Planear): `architect-review`, commit `dc4b430`. **Seis hallazgos medidos** y el orden forzado T-1..T-8. Corrigio la especificacion preexistente en vez de crearla, y el hallazgo H1 (nuevo) es que `_last_closed_apps` se sobrescribe sin mirar quien pide el apagado
- Paso 3 (Ejecutar): `openspec-dev`. `e0f20db` y cinco rondas de fix; T-9 lo escribio el arquitecto en `92368ad` y lo implemento el dev en `9433985`
- Paso 4 (Auditar tests): `mutation-auditor`. **Diez rondas**: las cinco primeras FAIL, la sexta PARCIAL, la septima FAIL de severidad baja, la octava y la novena FAIL bajas, la decima con la via de efecto

### Mutaciones auditadas (Paso 4, resumen de las diez rondas)

| Fix | Mutacion | Veredicto | Motivo del fallo |
|---|---|---|---|
| S1 (barrera roja de `_pack_evaluable`) | borrar el filtro `tier != danger` | **MUERE** (#16) | `solo el verde marcado debe llegar a kill_processes. Llego ['svchost.exe', 'onedrive.exe']` |
| A5 (`.exe` en los candidatos de arranque) | `patron + ".exe"` -> `patron` | **MUERE** (#18) | `los candidatos de una categoria tienen que ser Nombres con extension` |
| S7 (el filtro escribe en el pack original) | `model_copy` -> el pack del usuario | **MUERE** (#17) | `el filtro de la barrera escribio en el pack del usuario` |
| U1 (gate simple) | `if pack.is_gaming:` envuelve el acordeon | **MUERE** (A1, `14326`) | `hay un 'if pack.is_gaming' que CONSTRUYE el acordeon` |
| U1_AND (gate compuesto) | `if pack.is_gaming and pack.default_action == 'kill':` | **MUERE** (A1) | `una condicion que depende de is_gaming CONSTRUYE el acordeon` |
| G_VAR / G_ALIAS / G_GETATTR / G_PRED | variable intermedia, alias, `getattr`, `id !=` | **MUEREN** (A1) | las cuatro, misma asercion |
| G_GUARD2 | `if not pack.is_gaming: return` | **MUERE** (A2, `14599`) | `vuelve en L341 si se cumple 'not pack.is_gaming'` |
| M1 / M2 / M3B / M10 / C5 | lista filtrada a 2 y a 5 saltos | **MUEREN** (A1b, `14530`) | `la lista de categorias que lo alimenta depende de 'is_gaming'` |
| LC | casilla en `ListComp` gateada | **MUERE** (A1b) | `la casilla de L466 ... depende de is_gaming: L476` |
| LC_SOLO_UM / LC_ANIDADA | el mismo filtro, dos formas mas | **MUEREN** (A1b) | la misma asercion |
| ASSERT_GATE | `assert pack.is_gaming` delante | **MUERE** (A3, `14651`) | `el espejo no llega a construirse: la sentencia de L336` |
| 12 formas de la seccion 11.2 | gates, alias, predicados, listas | **MUEREN** | `14326` / `14530` / `14599` |
| S4/S5/S6/V7/V8 (regresion) | invariantes de servicio y vista | **MUEREN** | literales identicos a la ronda 1 |
| Z1 | barrera duplicada en `execute_gaming_pack` | **EQUIVALENTE** (x10) | el codigo ya filtra en `execute_pack`: duplicarla no cambia nada |
| SOLETE | ocho mutaciones que nadie mira | **EQUIVALENTE** | reduccion de la tarea anadida: `se_crean_windows()` ya existe |
| Las nueve familias de gate | las nueve rondas anteriores | **MUEREN en el 3-E** | el invariante se afirmo por EFECTO, no por forma |
| G_CATALOGO_VACIO | catalogo de categorias vacio | **MUERE** (E0) | `el catalogo de categorias ha vuelto vacio en este host (0 categorias)` |
| A_GATE_EN_LA_LLAMADA | gate en `refresh_packs` | **MUERE** (E1) | `la vista dibujo 1 tarjetas para 2 packs` |
| B / F / H | lista filtrada, `map`+lambda, etiqueta renombrada | **MUEREN** (E2) | `hay 0 casilla(s) de APAGAR` / `hay 3 casilla(s) de APAGAR` / `1 de APAGAR y 0 de ARRANCAR` |
| K_CATALOGO_CORTO | una categoria verde sale del catalogo | **MUERE** (E4, ronda 11) | `E4: el catalogo que la vista consume se ha quedado CORTO: le faltan 1 de las 9 categorias que el servicio clasifica` |
| W_VAR_CRUZADA | `variable=arrancar_var` -> `apagar_var` | **MUERE** (E5a, ronda 11) | `E5 (arrancar, 'Media y Streaming'): la casilla esta en 1 y el pack tiene ['Overlays e Info'] en start_categories, o sea esperaba 0` |
| W_SIN_E5A | E5a borrado del test, 33 lineas fuera | **MUERE** (E5b) | `E5 (clic arrancar, 'Antivirus y Seguridad'): el registro quedo en target_categories=[...]` |
| W_ESTADO_SOLO_E5A | E5b borrado, 62 lineas fuera | **MUERE** (E5a sola) | ninguna de las dos mitades depende de que la otra exista |
| T_TAUTOLOGIA | E4 leyendo `set(catalogo)` + el bug de produccion | **VERDE** | la muerte de E4 viene de derivar de dos fuentes, no de casualidad |

### Lo que realmente agrego este ciclo

**El hallazgo de fondo, y por que hubo diez rondas.** El invariante del test #3 (el acordeon de categorias no se esconde tras un gate de solo-Gaming) se reescribio nueve veces. Cada reescritura cerraba una **familia** de formas de escribir el gate y dejaba vivo un miembro de la siguiente. Esa firma es la de una especificacion incompleta, no la de un test malo, y el `openspec-dev` lo dijo sin rodeos: la pregunta que hace el test es **alcanzabilidad**, no decidible en general (Rice); con analisis estatico sobre un unico fichero toda aproximacion es una lista, y las listas no se cierran por dentro.

**La prueba, que es el dato mas util del ciclo:** se pidio anadir `ast.Assert` a la lista de tipos y **no cerro `ASSERT_GATE`**. El dev lo midio antes de decidir nada: una sentencia nunca puede ser antecesor de otra, asi que el `assert` es hermano y la cadena de padres no lo contiene. Anadir un nodo a una lista no acerca al invariante: desplaza el borde.

**La salida: preguntar por el efecto, no por la forma.** El invariante real es "un pack normal ve todas sus casillas" (en este host son nueve categorias y dieciocho casillas por tarjeta), y eso se mide montando la vista real, repintando y contando. Mata las nueve familias de una, porque no le importa como este escrito el codigo. La red estatica A1/A2/A3 **se congela**, y hay prueba medida de que no se solapan: `cb.grid(row=i // (2 if pack.is_gaming else 1))` lo mata el techo (f) estatico y el efecto lo deja pasar **con razon**, porque cambia la fila y no la cantidad. Regla anti-redundancia escrita en los dos docstrings: *una familia solo se anade a una capa si ninguna regla de la otra la mata ya*.

**La premisa falsa que salio de releer la especificacion midiendo.** El docstring del test #3 decia que una casilla de CustomTkinter sin `CTk` ni `root` no se puede instanciar. Es falso: `test_headless_ui` y `test_main_window_navigation_transitions` montan root y vista reales. **Esa frase la puso el orquestador al delegar**, y fue la que provoco las nueve rondas: cada actor la leyo como cierta. Corregida en `run_tests.py:14205-14233`, `:14336`, `:15678` y en la fila 107 de `docs/ai/testing-guide.md`.

**El residuo, declarado y no inventado.** Gatear el `.pack()` de `cat_body` no lo mata ninguna de las dos capas; cerrarlo exigiria identificar el boton en el arbol vivo, o sea dependencia de nombre o de texto, que es exactamente el defecto que las nueve rondas quitaron. Su cierre es otro change-id con entrada por comportamiento.

### Outcome
- Commits: `dc4b430`, `e0f20db`, `d318fef`, `9dcd8ed`, `ae58fc2`, `5f96671`, `9ebeabc`, `72e98dc`, `9b68cc2`, `c3ced1a`, `92368ad`, `9433985`
- Tests: **124 = 95 backend + 29 headless**, 0 fallos. `verify_ui_syntax.py` 9/9. `validate_docs.py` con 0 FAIL una vez escritos el journal y los dos changelogs
- Docs: `docs/ai/architecture.md` (la puerta unica), `docs/ai/data-models.md` (`start_categories` y su contrato), `docs/ai/ui-design-system.md` (las cuatro guardas, el acordeon, el conflicto espejo, la tabla de puertas), `docs/ai/testing-guide.md` (tabla de recuento, filas nuevas, invariante anti-redundancia)
- `src/` sin tocar desde `e0f20db`: los once commits siguientes son tests y documentacion. La feature completa cabe en un commit, y es lo correcto, porque un commit intermedio con la barrera anti-brick abierta es el ladrillo del ciclo 14

### Impact
Cierra el TASK-063 y deja una leccion reutilizable: **un invariante de forma, comprobado con un test de forma, se reescribe indefinidamente; y un limite que no se puede cerrar por dentro hay que declararlo con su tamano real, no disfrazarlo de cerrado.**

---

## [CYCLE-050] 2026-10-03 01:10 - github-releases-semantic-release
**Área**: Infraestructura & Distribución
**Change**: openspec/changes/2026-10-03-github-releases-semantic-release/
**Estado**: COMPLETED - verificado EN VIVO en GitHub (beta -> 1.0.0-beta.1, merge -> 1.0.0), no en local: este host no tiene `node`, así que semantic-release solo puede correr en el runner.
**Models**:
- Paso 1 (Buscar): orchestrator (encargo directo del propietario: "configura actions de github para que publique releases del .exe")
- Paso 2 (Planear): orchestrator - diseño de los cuatro jobs y de las ramas. **Sin `architect-review`**: el encargo es de tooling de CI y no toca `src/`, no hay invariantes de producto en juego y el propio encargo fijaba el resultado esperado (1.0.0 al final). Delegar aquí habría sido gastar una sesión en un plan que ya estaba decidido.
- Paso 3 (Ejecutar): orchestrator - `.releaserc.json`, `package.json`, `.commitlintrc.json`, `release.yml`, `commitlint.yml`, retirada de `build.yml`, docs y los dos changelogs
- Paso 4 (Auditar tests): orchestrator - mutantes del **pipeline** (no de `src/`, que este ciclo no toca). PASS. El detalle está más abajo.

### Mutaciones auditadas (Paso 4)
Este ciclo no toca codigo de producto, asi que los mutantes no son de `src/`: son los cuatro modos de fallo del pipeline, comprobados sobre el workflow en vez de sobre una linea de codigo.

| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| Job `commits` (commitlint del rango del push) | Commit con mensaje no convencional | killed | Falla ANTES de que corra semantic-release. Sin este job, semantic-release IGNORA el mensaje y no publica nada: el fallo silencioso de "no hay release", que es el que hace poco fiable un pipeline |
| Diff de tags en `release` + `if:` en `build` | Push solo con `docs:`/`chore:` | killed (correcto por construccion) | No hay tag nuevo -> `tag` sale vacio -> `build` se salta. Con `git describe` en su lugar habria devuelto el tag VIEJO y reconstruido una release anterior |
| `build` con `ref: <tag>` | Otro push a la rama mientras compila | killed | Compila el commit etiquetado, no HEAD. El binario sigue siendo reproducible respecto al tag que nombra la release |
| `build` con PyInstaller + `softprops/action-gh-release` | El build falla tras publicar la release | survived por diseno, y es lo correcto | La Release queda publicada SIN ejecutable. Se acepta: re-run del job en Actions reconstruye **el mismo tag**. La alternativa (build antes de publicar) dejaria releases sin publicar si PyInstaller falla, que es peor |

### Verificacion
- `python run_tests.py` -> **105/105 PASS** (despues de truncar `src/woptimizer/woptimizer.log`, ver incidente)
- `python verify_ui_syntax.py` -> EXITO, 8 modulos
- `python validate_docs.py` -> **117 OK / 0 FAIL**
- GitHub: `beta` -> Release `1.0.0-beta.1` marcada como pre-release con `woptimizer.exe`; `main` -> Release `1.0.0` con `woptimizer.exe`

### What
- `.releaserc.json`: ramas `main` (estable), `beta` (prerelease) y `+([0-9])?(.{+([0-9]),x}).x` (mantenimiento); `tagFormat` `v${version}`; `releaseRules` explicitas (breaking -> major, feat -> minor, fix/perf -> patch, el resto sin publicar)
- `.github/workflows/release.yml`: `commits` (ubuntu) -> `verify` (windows) -> `release` (ubuntu) -> `build` (windows)
- `.github/workflows/commitlint.yml`: commitlint en PRs. En push directo lo cubre el job `commits`
- `package.json` minimo con `"private": true`: el paquete de producto es Python, esto no se publica en npm
- `.commitlintrc.json` autocontenido, sin `extends`, para que `npx @commitlint/cli` lo resuelva sin instalar un shareable config. **OJO al nombre:** `commitlint.config.json` no existe para commitlint (ver el incidente de la corrida 1)
- **Retirado** `.github/workflows/build.yml`
- Docs: `docs/ai/release-pipeline.md` (nuevo), `openspec/changes/2026-10-03-github-releases-semantic-release/{proposal,tasks}.md`, entrada en el indice de `llms.txt`, seccion de releases en `AGENTS.md`, correccion de `README.md:46` que declaraba un desfase que ya no puede ocurrir

### Outcome
- Commits: `bb50a7a` (+ el commit de estos registros)
- Tests: 105/105 PASS
- Docs: `docs/ai/release-pipeline.md` nuevo; `AGENTS.md`, `README.md`, `llms.txt` actualizados

### Impact
Cierra en la practica la fila viva de `STATUS.md` que declara que **nadie vigila el desfase entre el ejecutable y el codigo**: al compilarse desde el commit etiquetado, ese desfase deja de existir por construccion en el camino de las releases. `validate_docs.py` queda **expresamente fuera de CI** y el motivo esta escrito en el workflow, no en un doc que nadie lee: su ancla de commits deriva `GIT_DIR` de `%LOCALAPPDATA%\\woptimizer_git\\.git` (`validate_docs.py:300-302`), que solo existe en el host del dueno; en el runner daria FAIL con el repo impecable.

### Incidente: el `WinError 32` que NO era del producto
Medir la linea base dio `run_tests.py` en rojo en `test_logging_va_a_fichero_y_no_a_stderr` con `WinError 32`. **Medido, no supuesto:** `Move-Item` sobre `src/woptimizer/woptimizer.log` falla con "being used by another process" **despues** de que `run_tests.py` haya terminado, mientras que el mismo fichero **si** se puede truncar a 0 bytes. Esa asimetria (escribir si, renombrar no) es la firma de un handle abierto sin `FILE_SHARE_DELETE`: el VFS de Nextcloud, no un fallo del codigo. El trigger es el estado: al superar el log el tope de rotacion, `doRollover()` hace `os.rename` sobre un fichero que el VFS tiene abierto, la stdlib manda el aviso a `lastResort` (stderr), y eso es exactamente lo que la asercion del test comprueba que **no** pase. En CI no ocurre: checkout limpio, sin VFS. Truncando a 0 la suite da 105/105 dos veces seguidas. Queda escrito en `docs/ai/release-pipeline.md` con su sintoma y con como diferenciarlo de un fallo real.

### Limpieza de la raiz: `basura/`, y lo que se decidio NO mover
Peticion del propietario: "veo mucha basura en el repo", con carpeta de cuarentena **fuera de Git** para que el borrado en bloque sea una sola operacion suya y segura. `basura/` esta en `.gitignore:79`.

**Metodo, que es la parte importante:** no se movio nada sin medir antes quien lo nombra. `_inventario.py` cruzo `git ls-files` con 20 consumidores (codigo, validadores y `docs/`) y con `tasks.json`. Eso salio:

- **Se movieron 6**: `verify_task1.py`, `verify_task3.py`, `verify_pyw.py`, `test_profiles_task1.json`, `commit_version.bat`, `procesos.csv`. Motivos medidos: los tres verificadores son v2; `verify_task3.py` tiene **cero** referencias en todo el repo; `verify_pyw.py` verifica `process_manager.pyw`, que ya no existe; `test_profiles_task1.json` solo lo consumia `verify_task1.py:12` (se mueven juntos o no vale nada); `commit_version.bat` saca la version con `findstr` sobre un fichero inexistente y ademas contradice semantic-release; `procesos.csv` son 131 filas ya migradas a `assets/process_db.json` en el ciclo 13, y `PROCESS_LIST_FILE` apunta a `saved_processes.json`, no a el (medido en `config.py`).
- **`_matrix_c26.py` se movio y SE DEVOLVIO.** `docs/ai/testing-guide.md` lo cita en 6 sitios como la matriz **reproducible** de 30 mutaciones, con su salida literal. Moverlo deja esas afirmaciones sin forma de comprobarse: es evidencia viva, no basura. Este es el movido/devuelto del que mas conviene acordarse, porque el criterio "esta roto y no lo usa nadie" era verdad y aun asi bylo incorrecto moverlo: lo que lo sostenia no era codigo, era **documentacion**.
- **No se toco `woptimizer.spec`, `build.bat` ni `force_build.py`**: parecen residuo de build y son **contrato con la suite** — `run_tests.py` recorre `("woptimizer.spec", "build.bat", "force_build.py")` en un test y falla si falta alguno.
- **No se toco `saved_processes.json` (38 KB)**: no esta versionado, pero es estado local de la maquina del dueno y es lo que apunta `PROCESS_LIST_FILE`. Borrarlo no seria limpiar el repo, seria tocarle el disco.
- **No se toco `smoke_check.py`** (prueba viviente de que `PROCESS_LIST_FILE` no se borro) ni **`benchmark.py`** (lo usa el bucle para el micro-benchmarking).

**Documentacion reparada en la misma pasada** (si no, quedan 4 documentos afirmando cosas falsas): `docs/ai/data-models.md:722` (nota de `commit_version.bat`), `docs/archive/legacy-root-data/README.md:52` (la fila que decia que `test_profiles_task1.json` "se queda"), `docs/known-issues.md:191` (cita a `verify_pyw.py`) y `docs/testing.md`, que resulto ser un documento **v2 entero** (`process_manager.py`, `ProcessManager.vbs`, cuatro scripts que ya no estan en la raiz) y lleva ahora un aviso al principio que dice cual es la guia vigente.

### Corrida 2 en GitHub: el test de arranque de apps tumbaba el job `verify`
Segundo fallo real, y este **si** era del repo. El job `commits` paso (el renombrado a `.commitlintrc.json` era el arreglo correcto) y fallo `Suite headless`:

```
AssertionError: el temporal C:\Users\RUNNER~1\AppData\Local\Temp\wopt_fix003_fcqy_7g3
cae fuera de las raices de arranque: los casos (b) y (g) se rechazarian por
contencion y no por lo que dicen probar
```

**Causa, MEDIDA y no supuesta.** En el runner `%TEMP%` llega en forma **corta 8.3** (`C:\Users\RUNNER~1\...`) mientras que las variables de las raices de arranque salen del perfil en forma **larga** (`C:\Users\runneradmin\...`). `_dentro_de_alguna` es **lexica por diseno** —para que el rechazo por junction lo haga su propia regla y no la contencion— y `os.path.commonpath` de esas dos formas colapsa a `C:\Users`. El temporal parecia estar fuera de toda raiz y la precondicion del test tumbaba el test entero.

**Reproducido aqui antes de arreglar nada** (el 8.3 esta deshabilitado para el perfil de este host, asi que se fabrico un directorio con alias corto propio y se puso `TEMP`/`TMP` ahi). Con esa `TEMP`, la suite Fallaba en **tres** sitios distintos, no en uno: la contencion del test de arranque, la del test de junction y la del test de hard link. Los tres por la misma razon.

**Arreglo en tres partes, y la que importa es la primera:**
1. **Canonicalizar `%TEMP%` una sola vez** al principio de `run_tests.py` con `os.path.realpath`, que expande el 8.3 al nombre largo **sin resolver junctions** —que es justo lo que hace falta—. Se fija `tempfile.tempdir`, no solo las variables de entorno, porque `tempfile` cachea su directorio y no vuelve a mirar `%TEMP%`. Arregla la clase entera, no el síntoma.
2. Los dos tests de arranque **colocan** su temporal en una raiz escribible (`LOCALAPPDATA` primero, porque las de Program Files piden privilegios) en vez de **asumir** que el TEMP del entorno cae dentro: disposicion, no casualidad de la maquina.
3. La precondicion del test de junction afirmaba un **proxy** (`_ruta_real(tmp) == normpath(tmp)`, o sea "la forma lexica coincide con la real") cuando lo que exige es el **requisito** ("la ruta real del temporal cae dentro de las raices"). Se afirma el requisito: con un ancestro en 8.3 las dos formas difieren sin que el temporal salga de su raiz.

**Verificado en los dos sentidos:** 105/105 con `TEMP` en forma 8.3 y 105/105 con `TEMP` normal. Un arreglo que solo funciona en el caso bueno no es un arreglo.

**Lo que NO se ha tocado y por que:** `src/`. Este es un defecto de **portabilidad de los tests**, no del producto. El producto rechaza por contencion una app expresada en 8.3, que es un falso positivo fail-closed **latente** (`GetLongPathName` lo arreglaria sin seguir junctions), pero arreglar la funcion de seguridad sin la auditoria de mutacion que este repo exige seria exactamente el fallo que el bucledles cierra: cambiar el muro sin comprobar que el test lo vigila. Queda como deuda, no como cambio a escondidas.

### Corrida 3 en GitHub: el `GIT_DIR` de las sondas git estaba fijo al desacople del VFS
El arreglo 8.3 de la corrida 2 **funciono** (los tests de arranque pasaron) y el `verify` cayo despues en `run_tests.py:6373`:

```
AssertionError: CONTROL ROTO: `git check-ignore` deberia responder rc=0 sobre
saved_processes.json y respondio rc=128
("fatal: not a git repository: C:\Users\runneradmin\AppData\Local\woptimizer_git\.git")
```

`_entorno_git_del_repo()` montaba `GIT_DIR` con una ruta **FIJA**,
`%LOCALAPPDATA%\woptimizer_git\.git`. Ese desacople no es una propiedad del
proyecto: es una medida del VFS de Nextcloud en la maquina del dueno. En el
runner no existe, el repo real es el `.git` del checkout y la sonda moria con
rc=128. El test era correcto y la premisa del entorno era falsa.

Arreglo: el `GIT_DIR` se **descubre** (el del entorno si viene, el desacoplado
si existe, el `.git` del arbol) y se **verifica** con `rev-parse --show-toplevel`.
Sin esa verificacion una ruta que no es la correcta daria verde por el motivo
equivocado. Si ninguna candidata es este arbol, falla fuerte y con el motivo a la
vista, en vez de skipear en silencio.

### Corridas 7 a 9: el pipeline metido a prueba por el propio ciclo
Tres hallazgos mas, y estos son los que hacen que el pipeline sea de fiar:

**Corrida 7 — el job `commits` paro MI commit.** La cabecera del commit de documentacion se paso de 120 caracteres, que es justo el limite que fija `.commitlintrc.json`. El guard que escribimos este ciclo cayo sobre quien lo escribio. **El arreglo fue acortar el mensaje, no relajar la regla:** un guard que se relaja para que pase el que lo escribio ya no guarda nada. Queda en la tabla de diagnostico de `docs/ai/release-pipeline.md`.

**Corrida 8 — un unico force-push dejaba el pipeline ROJO PARA SIEMPRE.** Al reescribir la cabecera (commit `9d8fd00`) con `--force-with-lease`, el `github.event.before` del evento siguiente apuntaba al commit viejo, que ya no era alcanzable y que `actions/checkout` con `fetch-depth: 0` no trae:
```
fatal: Invalid revision range d69c06b..HEAD
```
El peligro no es ese fallo: es que `before` habria seguido apuntando al mismo commit huerfano **en cada push posterior**, de modo que reescribir historia dejaba el repositorio sin poder publicar nada hasta el siguiente force-push. Blindado en `79eb136`: el job comprueba `git cat-file -e "${ANTES}^{commit}"` y cae a `HEAD~1`. El mismo fallo aparece con un squash o un rebase, o sea que tarde o temprano.

**Corrida 9 — verificado en vivo el criterio de aceptacion que faltaba.** Con un commit `ci()` (sin tipo publicable): `commits` success, `verify` success, `release` success **sin crear tag**, y `build` **skipped**. Releases tras la corrida: siguen siendo 2, `v1.0.0` y `v1.0.0-beta.1`. Ni un `1.0.1`, ni un `1.0.0.2`. Confirma el M2 de la tabla de mutaciones y confirma que **la 1.0.0 es la ultima version publicada**, que es lo que pedia el encargo.

### Corridas 5 y 6: VERDE. `v1.0.0-beta.1` y `v1.0.0` publicadas
Las dos ultimas corridas salieron los cuatro jobs en `success`, y esto es lo que se habia pedido:

| Release | Rama | `prerelease` | Asset |
|---|---|---|---|
| `v1.0.0-beta.1` | `beta` | `True` | `woptimizer.exe`, 25.673.311 bytes |
| `v1.0.0` | `main` | `False` | `woptimizer.exe`, 25.673.970 bytes |

**La graduacion funciono.** Al fusionar `beta` en `main` con `--ff-only`, semantic-release **no** creo un `1.0.0-beta.2` ni un `1.0.1`: finalizo el prerelease y publico la estable `1.0.0`. Ese era el mecanismo de el que dependia el encargo, y no se verifico por suposicion sino mirando lo que creo GitHub. Las notas de la release se generaron solas desde los mensajes de los commits (`### Bug Fixes`, con enlace a cada hash), o sea que el preset `conventionalcommits` esta leyendo los mensajes como debe.

Los dos `.exe` pesan distinto (25.673.311 vs 25.673.970) y eso es lo correcto: cada uno se compilo desde el commit etiquetado, no desde el HEAD de una rama.

### Corrida 4 en GitHub: `verify` en verde, y el preset no venia de serie
Buen avance: el job `verify` **paso** (los arreglos del 8.3 y del `GIT_DIR`
sirvieron) y el fallo se movio al job `release`:

```
Cannot find module 'conventional-changelog-conventionalcommits'
  at @semantic-release/commit-analyzer/lib/load-parser-config.js:25:63
```

**Causa, y aqui una premisa mia que era falsa.** Habia puesto
`"preset": "conventionalcommits"` a commit-analyzer **asumiendo** que era su
preset por defecto. No lo es: el por defecto es **`angular`**. Verificado en su
documentacion y despues leyendo su propio `load-parser-config.js`, que resuelve
`conventional-changelog-${preset}` con `importFrom(cwd, ...)` y lo invoca con
`presetConfig`. Con `angular` no habria reventado de forma ruidosa: habria
**publicado mal**, que es peor que reventar.

**Arreglo, con la mayor fijada por evidencia y no por costumbre.** El preset se
anade al `npx` (`-p conventional-changelog-conventionalcommits@9`) y se pone
`presetConfig: {}` explicitamente. La mayor es la **9** porque
`@semantic-release/commit-analyzer@13.0.1` depende de `conventional-changelog-writer`
(API clasica) mientras que el preset v10 ya reescrito depende de
`@conventional-changelog/template`: la v10 no es "la ultima", es de otra API. Eso
se comprobo leyendo las dependencias publicadas en npm, no suponiendo.

**Leccion del ciclo:** las cuatro corridas fallidas no fueron cuatro versiones del
mismo error. Tres eran **supuestos sobre el entorno** hechos en el sitio
equivocado —el nombre de un fichero de config, la forma de una ruta temporal, la
localizacion de un repositorio— y la cuarta un supuesto sobre el propio
semantic-release. Todas se resolvieron mirando la fuente: el codigo del plugin,
las dependencias publicadas. Dos se reprodujeron aqui antes de tocar nada.

### Corrida 1 en GitHub: FALLO en el job `commits`, y no era del mensaje de commit
El primer push a `beta` (run #1) cayo en `Comprobar los mensajes con commitlint`, y el mensaje de commit era perfectamente convencional. La causa era el **nombre del fichero de configuracion**: `commitlint.config.json` no esta entre los que commitlint busca. Segun su documentacion oficial, los ficheros que recoge son `.commitlintrc`, `.commitlintrc.json`, `.commitlintrc.yaml/.yml`, `.commitlintrc.js/.cjs/.mjs/.ts/.cts/.mts`, `commitlint.config.js/.cjs/.mjs/.ts/.cts/.mts` y el campo `commitlint` de `package.json` — **`.json` bajo el nombre `commitlint.config` no existe**. Cosmiconfig no lo encuentra, commitlint arranca sin reglas y falla. Renombrado a `.commitlintrc.json`.

**Por que se compta como mutacion y no como descuido:** el guard que existe para detectar un commit mal escrito se **disparo a si mismo** por un motivo que no tenia nada que ver con el commit. Un guard que falla por causas ajenas a lo que vigila entrena a apagar el guard, que es peor que no tenerlo: sin el, un commit malo pasa en silencio.

### Deuda que este ciclo deja escrita
1. `validate_docs.py` no puede correr en CI mientras su ancla dependa de un `GIT_DIR` desacoplado. Arreglo de fondo: que acepte el repo por `argv` o por variable ya presente en el runner.
2. Los flags de PyInstaller estan **duplicados** entre `force_build.py` y `release.yml`, unidos solo por un comentario. Si divergen, el `.exe` publicado deja de ser el mismo producto que el local. Un unico fichero de flags leido por los dos lo cierra.

## [CYCLE-048] 2026-10-02 03:10 - sanear-deuda-status
**Área**: Documentación & Arquitectura
**Change**: openspec/changes/2026-10-02-sanear-deuda-status/
**Estado**: COMPLETED — **VERDICT FINAL: PARTIAL** (4 rondas de auditoría: FAIL, FAIL, FAIL, PARTIAL). Contenido cerrado y verificado por contenido; la supervisión de ese contenido pendiente de TASK-060. La primera ronda escribió aquí `PASS` y era falso: corregido y conservado como registro. La primera ronda escribió aquí `PASS` y era falso. 0 cambios de producto; recuento estable en 103. El `110 OK / 1 FAIL` que se registra más abajo era el residuo (a) de la fila 93 ante el journal sin el ciclo 48, y **ya está resuelto**: el journal lo registró y el validador vuelve a **110 OK / 0 FAIL** (medido el 2026-10-02).
**Models**:
- Paso 1 (Buscar): orchestrator (backlog: `active_task_id` TASK-058)
- Paso 2 (Planear): architect-review — Auditoría fila por fila de las 13 filas de Deuda Conocida; **3 falsas, 2 caducadas, 1 imprecisa** detectadas con evidencia, y 2 premisas del encargo refutadas
- Paso 3 (Ejecutar): openspec-dev — TASK-058 (STATUS.md + docs/index.md + 2 changelogs + tasks.json)
- Paso 4 (Auditar tests): **NO APLICA** — sin cambios en `src/` ni en `validate_docs.py`, y en `run_tests.py` **una sola línea de docstring** («LAS SIETE FILAS» → «LAS OCHO FILAS», el «7» de la cuarta ronda), sin tests añadidos, borrados ni alterados; no hay fix de código que mutar. Sustituido por un comprobador propio que resuelve cada ancla escrita por contenido.

> **Convención de anclas de esta entrada: números de línea FÍSICOS.** El contrato del change numera las filas contando el encabezado de la sección como la 85, así que sus números son estos menos uno (`openspec/changes/2026-10-02-sanear-deuda-status/mutation-report.md:127` lo documenta, en la tabla de su §5 bis; el `:118` de ese fichero es el encabezado de la sección, no la tabla). Todas las filas de la tabla de arriba son líneas reales de `STATUS.md` y se comprueban por contenido, no por memoria. Dos anclas falsas que traía esta entrada y se corrigieron en el cierre: la del `spawn EPERM` llevaba el número de la fila anterior, y la del hito del **ciclo #11** llevaba el del **ciclo #10** (`model_copy`), que está una línea por encima. Ambas se han reescrito contra la línea real del panel y se comprueban por contenido, no por memoria. **Y la REGLA que esta cuarta ronda obliga a escribir, porque se va a repetir: una cita `fichero:línea` a un fichero que crece por arriba se caduca sola.** No hace falta que nadie la toque para que mienta: este fichero inserta cada ciclo al principio, de modo que todo número de línea citado en él envejece con cada entrada nueva, y lo mismo le pasa a cualquier log o informe al que se le prependan entradas. Medido en esta misma ronda sobre 6 citas de `openspec/changes/`: desviaciones reales de **160 a 1270** líneas contra `HEAD~1` y de **198 a 1308** en `HEAD` (las 5 que apuntan a este fichero; la sexta va a `src/`, que este ciclo no toca), y **ninguna** de las 6 se rompió por las **65** líneas que esta entrada añade en los dos changelogs (39 en este y 26 en el de la raíz, medido con `git show --numstat 9a8e952`). Por eso arreglar 6 números no las arregla: son la muestra, no el conjunto.

### Ficheros tocados (y los que NO, por auditoría)
| Fichero | Cambio |
|---|---|
| `STATUS.md:20` | «Ciclo Actual #47 … Completado» -> «Ciclo Actual #48: TASK-058 … En curso». La línea siguiente ya anunciaba este ciclo. |
| `STATUS.md:86` | FALSA x2 (no estaban en la raíz; 10 de 11 morían por el import). Conservada + cierre con `TASK-055`, `docs/archive/legacy-root-tests/README.md:1-7`, guard `run_tests.py:11590`. |
| `STATUS.md:88` | CIERTA, gravedad corregida: `spawn EPERM` causó el falso verde de versionado del ciclo #11 (`STATUS.md:38`). |
| `STATUS.md:89` | FALSA: los ciclos #14-#20 sí están versionados. `--verify` -> `WOPT_REPO_OK` exit 0. Pasa a puntero a la fila del residuo (#47). |
| `STATUS.md:92` | Cola corregida: `TASK-031` está `completed`. Cuerpo intacto con sus tres comprobables. |
| `STATUS.md:93` | CERRADA en CYCLE-047: el ancla es la unión del journal y el historial (`validate_docs.py:238,267`). |
| `STATUS.md:98` | FALSA en su premisa: cerrada en CYCLE-044 por `TASK-054` (`run_tests.py:11478`). Conservada. |
| `STATUS.md:99` (NUEVA, VIVA) | `docs/index.md:25` decía 96 tests y hay 103, y el check del recuento no vigila ese fichero. Nace con ancla, mutante y severidad 🟡. |
| `docs/index.md:25` | 96 -> 103. |
| `STATUS.md:100` (NUEVA, VIVA) | La fila del check que falta (`TASK-060`): el criterio entero, con la cuenta medida de las 5 filas vivas, la trampa del marcador de cierre y la propuesta para que el check no nazca fallando. Nace con ancla y severidad 🟡. |
| Sin cambios | `STATUS.md:87, 90, 91, 94, 95, 96, 97`; `src/**`; `validate_docs.py`; `verify_ui_syntax.py`; `AGENTS.md`; `README.md`. **Única excepción, `run_tests.py`: 1 línea de docstring** («LAS SIETE FILAS» → «LAS OCHO FILAS», el «7» vivo de la cuarta ronda), sin tests añadidos ni alterados y con el recuento en 103. |

### Verificación ejecutada (no supuestos)
- Cada ancla `archivo:línea` escrita en las filas tocadas se comprobó **por contenido**: ruta existente, línea dentro del fichero y snippet esperado presente. Mutar cualquiera de ellas hace fallar el comprobador.
- La redacción original de las 6 filas tocadas se comprobó presente (ninguna fila se borra).
- `python run_tests.py` -> 103 tests **PASS**, exit 0 | `python verify_ui_syntax.py` -> **EXITO**, exit 0 | `python validate_docs.py` -> **110 OK, 1 FAIL, exit 1**.
- **El unico FAIL lo causa este commit, no el panel, y no se maquilla:** el mensaje lleva el marcador `ciclo #48`, y `rd_journal.json` (47 entradas, **lo escribe el orquestador**) todavia no registra el 48. Antes del commit el validador daba 110 OK / 0 FAIL. Es el residuo (a) de la fila 93 declarado en `TASK-059`, apareciendo en su forma honesta: hay un commit del ciclo 48 y el journal no lo sabe. **`.taskmaster/rd_journal.json` no se toco** porque no pertenece a esta tarea; lo registra el orquestador al cerrar el ciclo.

### Decisiones que el contrato debía corregir y se corrigieron antes de ejecutar
1. **El criterio de aceptación de `TASK-058` sobre `docs/api.md`/`docs/index.md` estaba construido sobre un estado del repositorio inexistente.** `TASK-054` cerró ese punto en CYCLE-044. Se conservó la fila como cerrada en vez de "actualizar su severidad real".
2. **La fila de los `test_*.py` no solo mezclaba el recuento del import: también mentía en la ubicación** ("en la raíz"), que es la parte más peligrosa porque manda a un archivo que no existe desde hace 35 días.
3. **Incoherencia de contrato detectada al ejecutar:** la proposal §5 daba por hecha en este ciclo la ampliación de la lista del check del recuento con `docs/index.md`, pero su propia §6 excluía `validate_docs.py` del alcance y esa ampliación está reasignada a `TASK-060`. Se siguió §6: el validador no se tocó.

### Salidas a otro ciclo
- `TASK-060` (check de anclas en la Deuda Conocida, con las filas cerradas exentas) queda `pending` a propósito.
- **`.taskmaster/rd_journal.json` no registra el ciclo 48.** Mientras tanto el validador queda en 110 OK / 1 FAIL. Se reporta tal cual en vez de evitarse quitando el marcador de ciclo del commit: un commit sin marcador seria menos trazable, no mas.
- `STATUS.md:80` («Commits pendientes de los ciclos #14 a #20») arrastra la misma afirmación caducada que se corrigió en la fila 88. **No se reescribió** por quedar fuera del alcance; se señaló desde la fila 88. Decisión pendiente del propietario si se extiende el alcance.
- `STATUS.md:13` cita `ae53be7` como último commit; el HEAD real ya es `96c349f`. No es una falsedad («al día en git» es cierto) y lo rota el orquestador al cerrar el ciclo.


### Ronda de cierre (tras el FAIL de la auditoría)

La auditoría de `mutation-auditor` devolvió **FAIL** sobre la primera ronda de este ciclo, y el
bucle volvió al Paso 3 con el informe. Dos hallazgos, que son los que se arreglan aquí:

| # | Hallazgo | Qué se ha hecho |
|---|---|---|
| **S1** | La fila del `spawn EPERM` (`STATUS.md:88`) tenía la gravedad **bajada a 🟡** «porque la frase ya no era falsa», sin cerrar el problema. Eso es **documentación fail-open**: un panel que infravalora una deuda hace que el bucle la trate como resuelta y la abandone. En el ciclo #11 esa misma intermitencia hizo que `git_safe_commit.py` saliera con **código 0 ante cualquier fallo de commit** | **Vuelta a 🔴**, y **no se cierra**. Con su ancla y su comprobable, medidos (§ abajo) |
| **S2** | **Nada verifica las filas de esta sección.** La propia fila lo admite en su cara: «nadie vigila ese `96`», y a la vez nadie vigila que ella misma diga la verdad | Fila nueva en el panel con el **criterio entero** de `TASK-060`, para que el ciclo #49 se ejecute sin volver a preguntar nada |

**Lo medido de la fila 87, contra el repo y no de memoria** (el detalle entero, con comandos y
salidas, en `openspec/changes/2026-10-02-sanear-deuda-status/mutation-report.md`):

- El **invariante** es que *un fallo de git tiene que salir con un código distinto de 0*. **Se
  cumple hoy en el código**: con un repo temporal cuyo `pre-commit` sale con 1, el wrapper devuelve
  **1** y `WOPT_FAIL commit` (`WOPT_FAIL commit sin detalle`, exit 1, medido dos veces: antes y
  después de mutar).
- **El código que hoy se confunde con el de commit OK es el `0`**: está sobrecargado —
  `WOPT_COMMIT_OK` (commit real) y `WOPT_NOOP` (nada que comitear) salen los dos con `0`
  (`.taskmaster/git_safe_commit.py:13-14`, tabla en `docs/ai/sandbox-rules.md:55-56`). Medido en el repo real
  con el árbol limpio: `WOPT_NOOP arbol limpio (status --porcelain vacio)`, **exit 0**, sin escribir
  nada. Quien solo lea el código de salida no puede distinguir «se ha versionado» de «no había nada
  que versionar».
- **Nadie lo prueba.** `run_tests.py:1352 test_git_safe_commit_fail_safe` solo exige `3` y `2`
  (aserciones en `:1399`, `:1413`, `:1423` y `:1435`); ninguna de sus invocaciones llega a un
  `WOPT_FAIL`. **Mutante medido** sobre el `git_safe_commit.py` real: `sys.exit(CODE_FAIL)` →
  `sys.exit(CODE_OK)` en el camino de commit (`:229-230`) deja la suite **103/103 en verde con exit
  0**. El mutante se confirmó **por hash** (`c248f694…` → `ddac118f…`) **y por comportamiento**, y el
  fichero se restauró byte a byte (hash `c248f694…` de nuevo, y el wrapper volvió a salir 1).
- **Por qué nadie lo escribió, medido también:** `get_env()` respeta un `GIT_DIR` del entorno pero
  **impone `GIT_WORK_TREE = REPO_ROOT` sin condición** (`.taskmaster/git_safe_commit.py:78`), así que una
  invocación con un `GIT_DIR` desechable sigue haciendo `add -A` y `commit` **sobre el árbol de
  trabajo real**. El hook que `docs/ai/sandbox-rules.md:78-80` llama «tests herméticos» es hermético
  **en el repo, no en el árbol de trabajo**, y por eso el test existente solo toca las dos puertas
  que devuelven antes de cualquier `add`. Cerrarlo exige una decisión de diseño y después su test.
  Anotado en `docs/ai/sandbox-rules.md` (regla 7 y «Cobertura»), que hasta ahora afirmaba la
  cobertura sin decir qué **no** prueba.

**Barrido de las demás filas que tocó la primera ronda (S1 en dirección inversa):** **ninguna más
tenía la gravedad rebajada sin cierre**, y **ninguna fila marcada cerrada sigue viva**. Las seis se
volvieron a comprobar contra el repo: 11 `test_*.py` en `docs/archive/legacy-root-tests/` y **0** en
la raíz, con `ast.Import` sobre los 11 · 10 importan `process_manager` y
`test_powershell_direct.py` solo importa `os, subprocess, sys, time` · guard en `run_tests.py:11590`
· `git_safe_commit.py --verify` → `WOPT_REPO_OK` exit 0 · `TASK-031` y `TASK-054` `completed` en
`.taskmaster/tasks.json` · `docs/api.md:1` = «Referencia de API (v3)» con **cero** residuos `is_admin`
y `taskkill`, test en `run_tests.py:11478` · `_ciclos_de_commits` en `validate_docs.py:238` y
`_comprobar_ancla_de_commits` en `:267`.

**Fila nueva del panel (deuda de `TASK-060`, 🔴 → 🟡 preventiva):** el check 8 no existe y
`validate_docs.py` **no contiene ni una coincidencia de `Deuda`** (medido), así que un `0 FAIL`
sobre este panel no prueba nada. Se escribe con el criterio completo: qué filas deben llevar ancla,
por qué la verdad se deriva de **fuera** del panel, por qué las cerradas quedan **exentas**,
`_comprobar_deuda_con_anclas(root, errors, ok)` extraída con `root` y el motivo, los cuatro
escenarios del test (A/B/C/D), los dos mutantes que debe cerrar la auditoría, el **quinto testigo**
(`docs/index.md` declara un número de tests que el check del recuento no vigila) y la única decisión
que queda abierta (dos filas vivas llevan ancla en forma de fichero sin `fichero:línea`; si la regla
exige línea, el check nace fallando).

**Ficheros tocados en el cierre:** `STATUS.md` (fila 88 devuelta a 🔴 + fila nueva del check 8),
`docs/ai/sandbox-rules.md` (regla 7 y «Cobertura»), `openspec/changes/2026-10-02-sanear-deuda-status/mutation-report.md`
(nuevo), `CHANGELOG.md` (raíz) y este fichero. **Cero cambios en `src/` ni en
`validate_docs.py`, y en `run_tests.py` una línea de docstring; suite estable en 103.**

**Dos trampas de medición que casi dieron un veredicto falso (para el próximo):**

1. **El VFS miente si solo miras el hash.** La primera sonda aplicó la mutación y reimprimió el
   SHA-256 del fichero mutado: **salió idéntico al original**, o sea la mutación no llegó al disco
   (este árbol está en un directorio sincronizado con Virtual Files). Iba a imprimir `SOBREVIVE` y a
   dar por bueno un mutante sin medir. Regla que sale de ahí: **en este repo, confirmar un mutante
   por hash no basta — hay que confirmarlo por comportamiento.**
2. **Trampa #16, vivida otra vez:** la consola es `cp1252` y un emoji en un `print()` de sonda
   revienta con `UnicodeEncodeError` (🧬 en el panel). Todo lo que se imprime en una sonda de este
   repo pasa por `.encode("ascii", "replace")`.

**Afirmaciones de la primera ronda corregidas por ser falsas** (esta entrada y la del `CHANGELOG.md`
de la raíz las tenían): el `VERDICT: PASS`, que fue `FAIL`; y la descripción de la bajada de
gravedad de la fila 87 como si fuera un arreglo, que era el problema. También se alineó a 🟡 el
título del bloque de `docs/index.md` en el changelog legible, que decía 🔴 mientras la fila y su
criterio son 🟡.

**Una conclusión de la auditoría que era falsa, medida para que no se repita:** `test_profiles_task1.json`
no es un artefacto de este ciclo: lo añadió **`8efc0ae`** y está en `git ls-files`. Lo mismo
`_matrix_c26.py` (`b7e5f54`). **No se toca ninguno de los dos.**

**Verificaciones del cierre:** `python verify_ui_syntax.py` → EXITO, exit 0 · `python run_tests.py`
→ `ALL TESTS PASSED.`, exit 0 (103) · `python validate_docs.py` → **110 OK / 0 FAIL**, exit 0.
Salida literal completa en `mutation-report.md` §6.
### Ronda de cierre — la reauditoría dio FAIL otra vez, y lo que fallaba era la medición escrita

1. **🔴 Una deuda sin dueño.** El mutante `CODE_FAIL` → `CODE_OK` (`.taskmaster/git_safe_commit.py:230`) sobrevive
   a la suite **y** al validador (`110 OK / 0 FAIL` con el mutante puesto, confirmado por hash y por comportamiento), y
   la fila 88 decía «sin tarea propia todavía». Creada **`TASK-061`** (prioridad alta, `pending`) con la **decisión de
   diseño** que hay que tomar antes: `get_env()` impone `GIT_WORK_TREE = REPO_ROOT` sin condición (`:78`), así que un
   `GIT_DIR` desechable sigue commiteando el árbol real. **El fix NO se implementó aquí**: es diseño y es del
   arquitecto. Cerrar el ciclo con una 🔴 de integridad de versionado sin `TASK-xxx` es la misma forma que S1.
2. **La fila 88, con la víctima nombrada y el matiz del `NOOP`.** El único consumidor real del código de salida es el
   **agente orquestador** (`.agents/agents/architect-review/agent.md:50` le dice que compruebe su salida;
   `.agents/skills/id-pipeline/SKILL.md:382` le manda escribir el changelog tras el commit «para tener el hash», y la plantilla exige hashes en
   `.agents/skills/id-pipeline/SKILL.md:372`). No son consumidores: `run_tests.py:1352` solo mira `3` y `2`, `validate_docs.py:280` es una frase
   de un docstring y `sync_agents.py` tiene contrato propio. Y como **`WOPT_NOOP` nunca imprime hash**
   (`docs/ai/sandbox-rules.md:56` y `:70`), el fallo del ciclo #11 en su forma literal —el CHANGELOG registrando hashes
   que no existen— **no puede recuperar por esta puerta**: el daño real es «ciclo cerrado sin commit».
3. **La fila 100, con la lista real, y una afirmación nueva que era falsa.** Decía «dos filas vivas» y citaba
   `STATUS.md:91` como caso: **esa fila está cerrada** («cerrado en el ciclo #16») y el criterio la exonera. Medido:
   hay **5 filas vivas** (87, 88, 94, 99, 100); lectura estricta (`fichero:línea`) → fallan **87 y 94**; leniente →
   falla **94**, la única con cero referencias a ficheros, ni con línea ni sin ella. Y al implementarlo sale una
   **trampa del propio criterio**: la búsqueda ingenua de `cerrad` marca como cerradas justo la 94 («Declararlo cerrado
   sería…») y la 100 (el criterio describiéndose), con lo que el check dejaría de vigilar las dos filas que más lo
   necesitan. Propuesta en la fila: marcador de cierre estructural, ancla propia para la 87 y fila-tabla para la 94.
4. **Anclas de esta ronda unificadas a línea física** en los dos changelogs, y **segunda medición** del mutante de
   S48-2 añadida a `mutation-report.md` (también sobrevive al validador, que es el otro semi-veredicto del toolchain).

**Cero cambios en `src/`, `validate_docs.py` y `verify_ui_syntax.py`, y en `run_tests.py` una sola línea de docstring** («LAS SIETE FILAS» → «LAS OCHO FILAS», sin tocar ningún test); la suite sigue en **103 tests**.

### Cuarta ronda (con una quinta detrás, de cifras y citas, escrita en `mutation-report.md` §8): el FAIL era documental, y eran tres documentos

La reauditoría volvió a dar **FAIL estrecho**: las tres razones de la ronda anterior están **cerradas** una a una
(`TASK-061` existe con lo afirmado, la fila 88 nombra al dueño, las cinco filas vivas son correctas, la unificación
de anclas funcionó y el aislamiento de la cámara del `mutation-auditor` evitó la contaminación por tercera vez).
Quedan tres hallazgos, **ninguno bloquea** la decisión de diseño de `TASK-061`, y los tres son el mismo defecto:
**una cifra o una cita que no se comprobó contra lo que dice el fichero.**

1. **La especificación de `TASK-060` subcuantificaba su propia trampa, y la fila que la llevaba era la 🔴.** Decía que
   la búsqueda ingenua de `cerrad` marcaba como cerradas «la 94 y la 100». **Medido con ese mismo clasificador sobre
   las cinco filas vivas: marca TRES — la 88, la 94 y la 100.** En la 88 el subradical es «ciclo cerra**do** sin
   commit». Importa más de lo que parece: con la enumeración de dos, quien ejecute `TASK-060` acota el trabajo a 94/100
   y **deja sin cubrir la fila 88, que es la 🔴**. Y en la misma frase había otra cifra falsa del mismo tipo: la fila
   100 decía de sí misma «sus seis apariciones»: **catorce** en el texto que se corrigió y **diecisiete** en el ya reescrito (contadas con `re.findall(r"cerrad", fila, re.I)`), porque **la cuenta es autorreferente** y al reescribir la frase la frase se cuenta a sí misma.
   **Corregido en las tres** —esta entrada, `CHANGELOG.md` y la fila 100— a las tres, y **añadida la explicitación de
   que la enumeración es ILUSTRATIVA y lo que manda es P1** (marcador de cierre estructural): sin depender de buscar
   una palabra, la exención no puede clasificar mal ninguna fila. Así el dato de la enumeración deja de ser crítico
   aunque vuelva a quedarse corto.
2. **Seis citas de ancla falsas en `openspec/changes/`, sin declarar, con causalidad falsa.** Se parchearon a los
   números reales (resueltos por contenido, no por desplazamiento) y se corrigió la causa: **ya apuntaban al mismo
   contenido equivocado en `HEAD~1`**, con diferencias reales de **160 a 1270** líneas contra `HEAD~1` y de **198 a 1308** en `HEAD` (las 5 anclas que apuntan a este fichero, cada una resuelta por contenido con `git show HEAD~1`, no sumando), y no de las **65** líneas que esta entrada añade en los dos changelogs (39 en este y 26 en el de la raíz, con `git show --numstat 9a8e952`; el commit entero son 87 inserciones y 18 borrados, ninguna de `src/`). Caso que no admite discusión: la cita de `multi-favorites` apunta a `src/woptimizer/ui/views/process_manager_view.py`, fichero que este ciclo no toca, luego su desviación es previa por construcción.
   Ver el detalle medido en la raíz del changelog.
3. **El «7» vivo, y se arregla en vez de carve-out.** El encabezado de la tabla de escenarios decía «LAS SIETE FILAS»
   con **ocho** filas reales `(a)`–`(h)`, su propia nota de límite ya decía «las ocho filas», y el panel arrastraba el
   «7». Con esa redacción, la regla «🟡 mientras no haya afirmación falsa viva» **tenía una afirmación falsa viva**:
   el propio 7. Un carve-out para exceptuar una falsehood concreta sería más deuda que la falsehood, así que se
   corrigen las dos cosas y la fila 94 pasa a decir «las ocho filas».

**Deuda de contrato anotada y NO implementada (decisión del arquitecto, no de este agente):** un log que crece por
arriba no se cita por línea. Medido en esta misma ronda: los cuatro ficheros tocados tienen finales distintos
(`STATUS.md`, `CHANGELOG.md`, `run_tests.py` y `.taskmaster/tasks.json` en CRLF; este fichero, `run_tests.py`'s
docstrings neighbours y los `proposal.md` de `openspec/` en LF), y **una única inserción al principio de esta entrada
desplaza todas las anclas que apuntan a las líneas de abajo**. La arreglo semántico sería citar **por ciclo +
encabezado** en vez de por línea física. Queda anotado aquí para que quien lo herede lo decida; no se implementa en
este ciclo porque cambiar la convención de anclas del repo es un cambio de contrato, no una corrección de este ciclo.

**Y no son seis, son una muestra.** Las mismas dos citas rotas (`CHANGELOG.md:91` y `CHANGELOG.md:536`) aparecen además en `openspec/changes/2026-09-29-data-integrity-fixes/tasks.md:47` y en `openspec/changes/2026-09-30-task028-debt-cleanup/proposal.md:173`, y se corrigen por la misma causa y con el mismo método. **Los dos sitios que declaré «sin tocar» no existían como los nombré, y el motivo para no reescribirlos sí se sostiene:** el bloque de `CYCLE-017` de este fichero va de `:1852` a `:1883` y tiene **cero** ocurrencias de `CHANGELOG.md:91` (cero de la cadena `CHANGELOG`), y `TASK-011` **no tiene campo `notes`** —sus claves son `id`, `title`, `description`, `complexity`, `dependencies`, `priority`, `status` y `module`— ni la cita. La cita **sí existe**, pero en otro bloque y otra tarea: `:1747` de este fichero, dentro de **`CYCLE-015`** (`## [CYCLE-015]` en `:1734`), y las dos de `.taskmaster/tasks.json` (`:423` y `:455`) son de **`TASK-026`** («Integridad de datos, copia profunda y resiliencia de servicios»), no de `TASK-011`. Reescribir ese registro sería la misma mentira que se está corrigiendo, así que el motivo se aplica ahí, pero no a objetos que no existen. Y una cita más de la misma familia queda **fuera de este encargo, medida y con dueño**: `openspec/changes/2026-09-30-close-mutation-survivors/proposal.md:17` cita `CHANGELOG.md:57-67` como «sección CYCLE-017»; en el changelog de la raíz `:57` es una fila de la tabla de seis anclas de esta entrada y `:67` es `## CYCLE-047 - 2026-10-01`, y la `CYCLE-017` real está en `:724` de la raíz y `:1852` de este fichero. **No se parchea** (es propuesta de otro change) y **no se crea tarea**: el dueño es `architect-review`, porque el arreglo es de contrato, no una corrección.

---
## [CYCLE-047] 2026-10-01 23:59 - validator-independent-anchor
**Área**: Arquitectura & Calidad
**Change**: openspec/changes/2026-10-01-validator-independent-anchor/
**Estado**: COMPLETED — **VEREDICT FINAL: PASS** (4 rondas: FAIL, FAIL, FAIL, PASS)
**Models**:
- Paso 1 (Buscar): flash (backlog: `active_task_id` TASK-057)
- Paso 2 (Planear): architect-review — DISEÑO ACEPTADO; 2ª invocación: REPLANIFICACIÓN por Circuit Breaker
- Paso 3 (Ejecutar): openspec-dev — 4 pasadas (`dbe720d`, `614e5ff`, `f98cebc`, `2f8c9c2`, `ae53be7`)
- Paso 4 (Auditar tests): mutation-auditor — **FAIL ×3** (28 mut/12 surv · 24 mut/3 surv · 27 mut/6 surv) y **PASS** al cierre

### Mutaciones auditadas (Paso 4, ronda 1 — FAIL)
| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| Parser ciclo ≠ tarea | regex → `TASK-(\d{1,4})` | killed | `obtenido {56}, 2 con marcador y 1 sin` |
| Unión no sustitución | `ciclos_requeridos = set(journal_cycles)` | killed | `tiene que dar DOS errores; hay 1` |
| Ancla ilegible avisa | `errors.append` → `_ = (` | killed | `tiene que haber una linea [FAIL] con el motivo literal` |
| **Dirección del residuo** | invertir `ciclos_historial - ciclos_journal` | **SURVIVED** | acusaba al revés y dejaba el repo rojo |
| **Cableado en `main()`** | borrar la llamada a `_comprobar_ancla_del_changelog` | **SURVIVED** | suite completa verde y validador en `105 OK, 0 FAIL` con el ancla apagada |
| `max()` numérico | `max(str(c) for c in ...)` | killed | `Unknown format code 'd' for object of type 'str'` |
| Respeto del `GIT_DIR` del entorno | ignorarlo | killed | `el otro error tiene que exigir la entrada ## CYCLE-047` |

### Mutaciones auditadas (Paso 4, ronda 2 — FAIL)
| Fix | Mutacion | Veredicto | Motivo del fallo |
|---|---|---|---|
| S1 dirección del residuo | invertir el conjunto | killed | `el residuo son los ciclos que EL HISTORIAL TIENE Y EL JOURNAL NO` |
| S2 cableado en `main()` | borrar la llamada | killed | `el ancla tiene que CORRER dentro de main(): su linea de informe ... no aparece` |
| S5 `except` del journal | estrechar a `json.JSONDecodeError` | killed | `debía devolver un INFORME y tiró PermissionError` |
| S3 fallback `GIT_DIR` | suprimir `expandvars` | killed | `TypeError: environment can only contain strings` |
| S4 rama del parser roto | `if False:` / `if not ciclos:` | killed | `eso es un parser ROTO y tiene que salir como [FAIL]` |
| **A1 `journal_cycles` al ancla** | no pasar el 4º argumento | **SURVIVED** | **validador real en `108 OK / 0 FAIL` con el parser muerto** |
| **A2 `--all`** | quitar `--all` | **SURVIVED** | con un ciclo en rama lateral el residuo se pierde |
| **M1/M2 rama journal vacío** | borrar / invertir | **SURVIVED** | 2 FAIL pasan a 1 FAIL |

### Cambios Clave
- `validate_docs.py`: 3 funciones nuevas (`_ciclos_de_commits`, `_comprobar_ancla_de_commits`, `_comprobar_ancla_del_changelog`), unión de fuentes y cableado en `main()`.
- `run_tests.py`: +4 tests del ciclo (100 → 104).
- `docs/ai/sandbox-rules.md`: regla nueva, alcance medido y LIMITACIÓN RESIDUAL explícita.
- Corrección de la afirmación falsa "41 de 46 hashes" en 5+ ficheros: la cifra real es **1**.

### Mutaciones auditadas (Paso 4, ronda 3 — FAIL) y cierre (ronda 4 — PASS)
| Fix | Mutación | Veredicto | Motivo del fallo | Dónde muere de verdad |
|---|---|---|---|---|
| **P2** `missing_entries` laxo | buscar el número como subcadena | killed | `fila (f): encabezado borrado y número solo en prosa ... Errores: []` | **solo** fila (f) |
| **P3** `has_jentry` laxo | `f"{jlatest}" in rch` | killed | `fila (f): ...` | **solo** fila (f) |
| **H2** guarda muerta | `if not has_jentry:` → `if False:` | killed | `fila (f): ...` el recuento pasa a 1 y la fila exige 2 | **solo** fila (f) |
| **P2b/P3b** | buscar `CYCLE-nnn` sin `## ` | killed | `fila (f)` — la segunda clase de cita protege de verdad | **solo** fila (f) |
| **E2** `except` del git | estrechar a `OSError` | killed | `debía devolver un INFORME y tiró TimeoutExpired` | la tabla, **por el envoltorio compartido** |
| **E3** sin reintento | `for _intento in (1, 2)` → `(1,)` | killed | `NO SE PUEDE LEER ... TimeoutExpired` | **solo** fila (g), por su `juzgar` |
| **G1** plural del parser | quitar el `s?` | killed | `fila (h): el rango 015-020 tiene que exigir sus 7 ciclos` | **solo** fila (h) |
| **G1b/c/d** | no expande / extremo exclusivo / sin tope | killed | `fila (h)` | **solo** fila (h) |

**Supervivientes al cierre: 0.** La fila (f) quedó probada **no tautológica**: al borrar su prosa, P2 y P3 sobreviven a la suite entera. La fila (g) **no contamina**: el doble de `subprocess.run` se restaura limpio (`is` → `True`), así que los veredictos posteriores son válidos. `D2` aislado es **inerte por diseño** (el default no llega a usarse); lo que se mide es `D2+M2`, que muere por la fila (a).

### Cambios Clave
- `validate_docs.py`: `validar(root)` con los checks 1-7, `main()` reducido a llamar/imprimir/salir — **un solo camino de validación**; default `journal_cycles=()` **borrado**; `_marcador_de_ciclo` → `_ciclos_del_asunto` con plural→rango acotado a 50.
- `run_tests.py`: tabla de escenarios de **7 filas** (una copia del esqueleto; los escenarios son filas); suite **99 → 104 → 103** (bajó: dos tests fusionados, ninguno añadido).
- `mutation-report.md` (**nuevo**): registro de mutantes por nombre, que antes no existía en ningún artefacto del repo.
- `docs/ai/sandbox-rules.md`, `docs/ai/testing-guide.md`, `STATUS.md`, `AGENTS.md`, `README.md`: regla, D1–D4 y recuento a 103.
- Corrección de la afirmación falsa "41 de 46 hashes" en 5+ ficheros: la cifra real es **1**.

### Por qué tres FAIL seguidos (nota de proceso)
El patrón que se repitió es el mismo: **los tests llaman a las funciones privadas pasándoles a mano los argumentos, así que el cableado que suministra esos argumentos no se prueba**. Arreglar el hallazgo visible dejaba el mismo agujero un nivel más abajo. Dos aprendizajes que costaron una ronda cada uno: (a) `python run_tests.py` **solo devuelve el primer test que revienta**, así que atribuir la muerte a un test sin aislar es inventarse el dato — tres atribuciones del informe eran falsas por omisión; (b) `validate_docs.py` es **CRLF** y un arnés con `\n` pelado no aplica las mutaciones, así que el auditor pierde media ronda creyendo que son supervivientes.

### Impact
El ancla nueva **sí llegó a morder el repo real**: al aterrizar el commit con marcador `ciclo #47` sin journal, el validador dio 2 FAIL. Es el residuo que la tarea existía para cazar, detectado en producción y cerrado al registrar el ciclo. **A1 está ERRADICADO donde se produjo y DESPLAZADO donde no se buscó**, y así está escrito: cerrar esto declarándolo resuelto sería el mismo fallo que el ciclo vino a matar. `src/` intacto.

---

## [CYCLE-046] 2026-10-01 23:48 — dead-code-guard
**Área**: Arquitectura & Calidad
**Change**: openspec/changes/2026-10-01-dead-code-guard/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): flash (Deuda detectada en revisión / Arquitectura & Calidad)
- Paso 2 (Planear): architect-review → VISTO BUENO Y APROBADO
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO Y DOCUMENTADO
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (4/4 mutaciones eliminadas: M1, M2, M3, M4)

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| Detección de funciones huérfanas en services | Inyectar `funcion_muerta_huerfana_xyz` sin referencias en `process_service.py` | killed | `AssertionError: Se detectaron 1 funciones/métodos sin ninguna referencia: [...] funcion_muerta_huerfana_xyz` |
| Detección de métodos huérfanos en UI | Inyectar `metodo_dashboard_muerto_abc` sin referencias en `dashboard_view.py` | killed | `AssertionError: Se detectaron 1 funciones/métodos sin ninguna referencia: [...] metodo_dashboard_muerto_abc` |
| Verificación de eliminación de `_get_priority` | Reintroducir `_get_priority` en `process_service.py` | killed | `AssertionError: _get_priority` (detectado como unreferenced / no eliminado) |
| Eficacia de la aserción de no-huérfanos | Inyectar `zombie_function_uncalled` en `process_service.py` | killed | `AssertionError: Se detectaron 1 funciones/métodos sin ninguna referencia: [...] zombie_function_uncalled` |

### Cambios Clave
- `src/woptimizer/services/process_service.py`: Eliminados el método muerto `_get_priority` y la propiedad zombie `process_db`.
- `src/woptimizer/ui/views/dashboard_view.py`: Conectada la llamada formal a `self.pack_service.get_favorite_packs()` en `refresh_dashboard()` y `_regrid_favorites()`.
- `run_tests.py`: `test_contrast_wcag_aa` ahora evalúa directamente `theme.is_wcag_aa()`. Creado test #99 `test_dead_code_ast_guard` con análisis estático AST sobre todo el árbol de `src/woptimizer/**`.
- `openspec/changes/2026-10-01-dead-code-guard/`: Formalizada especificación y tareas del cambio.
- `STATUS.md`, `AGENTS.md`, `README.md`, `docs/ai/testing-guide.md`: Sincronización exacta a 99 tests en verde.

---

## [CYCLE-045] 2026-10-01 23:43 — archive-legacy-root-tests
**Área**: Testing & Calidad
**Change**: openspec/changes/2026-10-01-archive-legacy-root-tests/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): flash (Deuda declarada en STATUS.md / Testing & Calidad)
- Paso 2 (Planear): architect-review → VISTO BUENO Y APROBADO
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO Y DOCUMENTADO
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (4/4 mutaciones eliminadas: M1, M2, M3, M4)

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| Guard anti-regresión en raíz | Reintroducir un archivo `test_dummy.py` en la raíz | killed | `AssertionError: Se encontraron archivos test_*.py legacy en la raíz del repositorio` |
| Presencia de documentación de archivo | Eliminar `docs/archive/legacy-root-tests/README.md` | killed | `AssertionError: README.md en ... debe existir y contener documentación descriptiva` |
| Preservación de ficheros requeridos | Omitir `test_powershell_direct.py` del archivo | killed | `AssertionError: Fichero legacy esperado test_powershell_direct.py no encontrado en ...` |
| Verificación de contenido del script crítico | Alterar `test_powershell_direct.py` sustituyendo `notepad.exe` | killed | `AssertionError` (falla la aserción de comprobación de contenido) |

### Cambios Clave
- `docs/archive/legacy-root-tests/`: Traslado de los 11 archivos `test_*.py` que residían en la raíz del proyecto.
- `docs/archive/legacy-root-tests/README.md`: Documentación exhaustiva que clasifica los 10 scripts v2 dependientes de `process_manager` y el script autónomo `test_powershell_direct.py`.
- `run_tests.py`: Incorporado test #98 `test_no_legacy_test_files_in_root` que bloquea la aparición de ficheros `test_*.py` en la raíz e inspecciona el archivo histórico.
- `openspec/changes/2026-10-01-archive-legacy-root-tests/`: Documentación formal de cambio con `proposal.md` y `tasks.md`.
- `STATUS.md`, `AGENTS.md`, `README.md`, `docs/ai/testing-guide.md`: Sincronización exacta a 98 tests en verde.

---

## [CYCLE-044] 2026-10-01 23:38 — align-v3-docs-contracts
**Área**: Documentación & Arquitectura
**Change**: openspec/changes/2026-10-01-align-v3-docs-contracts/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): flash (Deuda Técnica Conocida / Documentación & Arquitectura)
- Paso 2 (Planear): architect-review → VISTO BUENO Y APROBADO
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO Y DOCUMENTADO
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (4/4 mutaciones eliminadas: M1, M2, M3, M4)

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| Ausencia de residuos v2 en docs/api.md | Reintroducir `- is_admin()` en `docs/api.md` | killed | `AssertionError: Residuo v2 prohibido 'is_admin' encontrado en docs/api.md` |
| Veracidad de métodos citados en api.md | Sustituir `get_running_processes` por `metodo_fantasma_no_existe` en `docs/api.md` | killed | `AssertionError: Metodo ProcessService.get_running_processes no esta documentado en docs/api.md` |
| Ausencia de falsas afirmaciones UAC en index.md | Reintroducir `auto-eleva admin con UAC` en `docs/index.md` | killed | `AssertionError: Residuo v2 prohibido 'auto-eleva admin' encontrado en docs/index.md` |
| Integridad del bloque nav en mkdocs.yml | Añadir ruta inexistente `- Roto: no_existe_archivo.md` en `mkdocs.yml` | killed | `AssertionError: Fichero nav 'no_existe_archivo.md' referenciado en mkdocs.yml no existe en disco` |

### Cambios Clave
- `docs/api.md`: Reescritura total alineada con la versión 3 (ProcessService, PackService, GamingService, NotificationService y modelos Pydantic v2). Erradicados todos los rastros de scripts v2 (`is_admin`, `taskkill`, `powershell`, `saved_processes.json`, `ProcessManagerApp`).
- `docs/index.md`: Modernizada la introducción, comandos de inicio rápido, características v3 y árbol de código, eliminando falsas promesas de auto-elevación UAC nativa.
- `run_tests.py`: Añadido test #97 `test_docs_api_and_index_v3_contracts` que valida programáticamente todas las prohibiciones y la correspondencia en runtime con los módulos de `src/woptimizer/`.
- `STATUS.md`, `AGENTS.md`, `README.md`, `docs/ai/testing-guide.md`: Sincronización exacta a 97 tests en verde.

---

## [CYCLE-043] 2026-10-01 23:33 — multi-favorites-and-db-download
**Área**: Testing & Calidad
**Change**: openspec/changes/2026-10-01-multi-favorites-and-db-download/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): flash (Encargos 1-4 Propietario / Área 5)
- Paso 2 (Planear): architect-review → VISTO BUENO Y APROBADO
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO Y DOCUMENTADO
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (4/4 mutaciones eliminadas: M1, M2, M3, M4)

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| Comportamiento acumulativo en Grabador | Restablecer lógica exclusiva en `_Grabador.toggle_favorite` | killed | `AssertionError: el pack 'a' debió desmarcarse: {'a': True, 'b': False}` en `run_tests.py:5865` |
| Inversión correcta de estado | Fijar `self.estado[pack_id] = True` sin invertir en `toggle_favorite` | killed | `AssertionError: el pack 'a' debió desmarcarse: {'a': True, 'b': False}` en `run_tests.py:5865` |
| Preservación de otros favoritos en caso 4 | Reclamar que todos se desmarcan (`{"a": False, "b": False}`) | killed | `AssertionError: con favoritos acumulativos, desmarcar 'b' debe dejar 'a' marcado: {'a': True, 'b': False}` en `run_tests.py:5875` |
| Guard AST contra set_favorite unario | Inyectar llamada `set_favorite("mutant")` con 1 solo argumento | killed | `AssertionError: Llamadas a set_favorite con 1 solo argumento halladas en run_tests.py líneas: [...]` en `run_tests.py:5910` |

### Cambios Clave
- `run_tests.py`: Refactorizado `test_toggle_favorite_desmarca` con semántica acumulativa y guard AST contra llamadas unarias a `set_favorite`.
- `docs/ai/testing-guide.md`, `STATUS.md`, `AGENTS.md`, `README.md`: Sincronización exacta a 96 tests en verde.

---

## [CYCLE-042] 2026-10-01 23:30 — multi-favorites-and-db-download
**Área**: UI & Experiencia de Usuario
**Change**: openspec/changes/2026-10-01-multi-favorites-and-db-download/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): flash (Encargo 2 Propietario / Área 2)
- Paso 2 (Planear): architect-review → VISTO BUENO Y APROBADO
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO Y DOCUMENTADO
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (4/4 mutaciones eliminadas: M1, M2, M3, M4)

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| Glifo de flecha ausente en constante | Reintroducir `▼` en el valor de `PLACEHOLDER_PACK` | killed | `AssertionError: PLACEHOLDER_PACK no debe contener el glifo ▼` en `run_tests.py:11388` |
| Literal centralizado en constante | Duplicar el literal hardcodeado en `self.pack_var = StringVar(value="Seleccionar Pack")` | killed | `AssertionError: El literal 'Seleccionar Pack' debe aparecer exactamente una vez (en la constante), encontrado 2 veces` en `run_tests.py:11400` |
| Comparación vía constante en dropdown | Comparar contra literal `"Seleccionar Pack"` en lugar de `PLACEHOLDER_PACK` | killed | `AssertionError: El literal 'Seleccionar Pack' debe aparecer exactamente una vez (en la constante), encontrado 2 veces` en `run_tests.py:11400` |
| Inicialización correcta de values | Modificar `values=[PLACEHOLDER_PACK]` a `values=["Invalido"]` en `_build_ui` | killed | `AssertionError: Los valores iniciales del dropdown deben ser ['Seleccionar Pack']` en `run_tests.py:11430` |

### Cambios Clave
- `src/woptimizer/ui/views/process_manager_view.py`: Definida constante `PLACEHOLDER_PACK = "Seleccionar Pack"`. Eliminadas 4 apariciones del literal y glifo duplicado `▼`. Refactorizado `_update_pack_dropdown` para usar la constante.
- `run_tests.py`: Añadido test #96 `test_process_manager_pack_dropdown_single_arrow_and_placeholder` blindado contra las 4 mutaciones M1-M4.
- `docs/ai/ui-design-system.md`: Documentada la centralización de `PLACEHOLDER_PACK` y la eliminación de la doble flecha redundante en la sección de ProcessManagerView.
- `docs/ai/testing-guide.md`, `STATUS.md`, `AGENTS.md`, `README.md`: Suite actualizada y sincronizada a 96 tests en verde.

---

## [CYCLE-041] 2026-10-01 23:25 — multi-favorites-and-db-download
**Área**: UI & Experiencia de Usuario
**Change**: openspec/changes/2026-10-01-multi-favorites-and-db-download/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): flash (Encargos 2 y 4 Propietario / Área 2)
- Paso 2 (Planear): architect-review → VISTO BUENO Y APROBADO
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO Y DOCUMENTADO
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (4/4 mutaciones eliminadas: M1, M2, M3, M4)

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| Botón `btn_update_db` conectado | Modificar `command=self._force_update_db` a `command=None` | killed | `AssertionError: ProcessManagerView._build_ui debe contener un botón cuyo command apunte a self._force_update_db` en `run_tests.py:11293` |
| Manejo observable de fallo de red | Omitir parámetro `on_error` en llamada a `load_db_async` | killed | `AssertionError: El fallo de red debe notificarse honestamente en status_label, recibido: ✅ Base de datos actualizada con éxito.` en `run_tests.py:11333` |
| Preservación de banner en `_render_list` | Omitir comprobación `if getattr(self, "_db_update_status", None):` en `_render_list` | killed | `AssertionError: El renderizado de procesos no debe pisar el aviso de fallo de DB` en `run_tests.py:11340` |
| Desacoplamiento de plataforma | Reintroducir literal 'GitLab' en el texto del botón o vista | killed | `AssertionError: process_manager_view.py no debe contener menciones congeladas a 'GitLab'` en `run_tests.py:11299` |

### Cambios Clave
- `src/woptimizer/ui/views/process_manager_view.py`: Añadido botón interactivo `btn_update_db` con token `theme.SURFACE_ALT`. Cableado a `_force_update_db()`, gestión atómica de estados de carga/éxito/fallo honesto, y preservación en `_render_list()`.
- `run_tests.py`: Añadido test #95 `test_process_manager_db_update_button_and_feedback` blindado contra las 4 mutaciones M1-M4.
- `docs/ai/ui-design-system.md`: Documentado el nuevo botón `btn_update_db`, sus tokens visuales y la máquina de estados de feedback honesto en la sección de ProcessManagerView.
- `docs/ai/testing-guide.md`, `STATUS.md`, `AGENTS.md`, `README.md`: Suite actualizada y sincronizada a 95 tests en verde.

---

## [CYCLE-040] 2026-10-01 23:17 — multi-favorites-and-db-download
**Área**: Base de Datos & Procesos
**Change**: openspec/changes/2026-10-01-multi-favorites-and-db-download/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): flash (Encargo 2 Propietario / Área 3)
- Paso 2 (Planear): architect-review → VISTO BUENO Y APROBADO
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO Y DOCUMENTADO
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (4/4 mutaciones eliminadas: M1, M2, M3, M4)

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| Constante de módulo `DB_REMOTE_URL` | Hardcodear URL literal de GitHub dentro del cuerpo de `load_db_async` | killed | `AssertionError: El literal de URL de GitHub no debe estar hardcodeado en load_db_async; debe usar DB_REMOTE_URL` en `run_tests.py:11172` |
| Notificación observable a `on_error` | Omitir invocación a `on_error(err_msg)` ante excepción en `load_db_async` | killed | `AssertionError: load_db_async debió invocar on_error ante fallo de red` en `run_tests.py:11200` |
| Fallback a DB local empaquetada | Omitir `self._load_local_db()` ante fallo de red | killed | `AssertionError: La DB local debe quedar cargada tras fallo de red (fallback local)` en `run_tests.py:11211` |
| Plataforma canónica GitHub | Mutar `DB_REMOTE_URL` apuntando a GitLab u otra plataforma | killed | `AssertionError: DB_REMOTE_URL debe apuntar al endpoint oficial de GitHub, obtenido: ...` en `run_tests.py:11162` |

### Cambios Clave
- `src/woptimizer/services/process_service.py`: Extraída constante `DB_REMOTE_URL` en GitHub. Añadido parámetro `on_error` a `load_db_async` para notificación honesta de excepciones. Garantizado fallback local síncrono ante fallo de red. Preservado rango exacto `33-48` de `SYSTEM_PROTECTED_PROCESSES`.
- `run_tests.py`: Añadido `test_process_service_db_download_contracts` (test #94) con inspección AST, mocks deterministas de red sin peticiones reales y validación de categorías y blindaje offline.
- `docs/ai/architecture.md`: Actualizada regla 3 y añadida sección 18 con detalles arquitectónicos de sincronización remota y fallback local.
- `docs/ai/testing-guide.md`, `STATUS.md`, `AGENTS.md`, `README.md`: Suite actualizada y sincronizada a 94 tests en verde.

---

## [CYCLE-039] 2026-10-01 23:12 — multi-favorites-and-db-download
**Área**: UI & Experiencia de Usuario
**Change**: openspec/changes/2026-10-01-multi-favorites-and-db-download/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): flash (Encargo 1 Propietario / Área 2)
- Paso 2 (Planear): architect-review → VISTO BUENO Y APROBADO
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO Y DOCUMENTADO
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (4/4 mutaciones eliminadas: M1, M2, M3, M4)

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| Cálculo adaptativo de columnas | Forzar `_calculate_columns` a retornar 2 columnas fijas | killed | `AssertionError: Con 1200px y 4 favoritos, pack_3 debe estar en row 0 col 3, recibido: row 1 col 1` en `run_tests.py:11095` |
| Re-grid dinámico en `<Configure>` | Omitir `self._regrid_favorites()` en `_on_frame_configure` | killed | `AssertionError: Tras reducir a 600px vía <Configure>, pack_3 debe moverse a row 1 col 1, recibido: row 0 col 3` en `run_tests.py:11116` |
| Columnspan responsivo en placeholder | Hardcodear `columnspan=2` en `_empty_label.grid` | killed | `AssertionError: _empty_label debe adaptarse a 4 columnas tras <Configure>, recibido 2` en `run_tests.py:11138` |
| Limpieza de pesos en columnas sobrantes | Omitir `grid_columnconfigure(c, weight=0, uniform="")` al reducir cols | killed | `AssertionError: Columna 2 debe tener peso 0 al reducir columnas, tiene 1` en `run_tests.py:11122` |

### Cambios Clave
- `src/woptimizer/ui/theme.py`: Añadida constante `ANCHO_MIN_CARD: Final[int] = 280`.
- `src/woptimizer/ui/views/dashboard_view.py`: Implementados `_calculate_columns()`, `_reconfigure_grid_columns()`, `_on_frame_configure()`, `_regrid_favorites()` y `_destroy_favorite_buttons()`. Refactorizado `refresh_dashboard()` para layout responsivo y gestión limpia de columnas sobrantes.
- `run_tests.py`: Añadido `test_dashboard_favorite_grid_adaptive_contracts` (test #93) probando distribución espacial, recolocación adaptativa ante eventos `<Configure>`, filtrado de emisor y span dinámico de placeholder.
- `docs/ai/ui-design-system.md`: Documentada la rejilla adaptativa de favoritos, constante `ANCHO_MIN_CARD` y ciclo de vida del layout responsive.
- `docs/ai/testing-guide.md`, `STATUS.md`, `AGENTS.md`, `README.md`: Suite actualizada y sincronizada a 93 tests en verde.

---

## [CYCLE-038] 2026-10-01 23:05 — multi-favorites-and-db-download
**Área**: Core Services & Robustez
**Change**: openspec/changes/2026-10-01-multi-favorites-and-db-download/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): flash (Encargo 1 Propietario / Área 2)
- Paso 2 (Planear): architect-review → VISTO BUENO Y APROBADO
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO Y DOCUMENTADO
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (5/5 mutaciones eliminadas: M1, M2, M3a, M3b, M4, M5)

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| Favoritos acumulativos (no exclusividad) | Revertir a comportamiento exclusivo al marcar un favorito | killed | `AssertionError: Esperaba ['a', 'c'] acumulados, hay ['c']` en `run_tests.py:1006` |
| Validación estricta de `pack_id` | Omitir `if not pack_id: raise ValueError(...)` permitiendo `None` o `""` | killed | `AssertionError: set_favorite(None, True) debió lanzar ValueError` en `run_tests.py:1039` |
| Alternancia booleana en `toggle_favorite` | No invertir el valor booleano actual | killed | `AssertionError: Esperaba True tras primer toggle, obtuvo False` en `run_tests.py:1055` |
| Persistencia a disco en `toggle_favorite` | Omitir `self.save()` tras actualizar en memoria | killed | `AssertionError` al recargar desde disco en `run_tests.py:1058` |
| Restauración de favorito en pack gaming | Omitir `self._data.packs["gaming"].is_favorite = True` en `_ensure_gaming_pack` | killed | `AssertionError: _ensure_gaming_pack debe restaurar is_favorite=True en pack gaming existente` en `run_tests.py:1079` |
| Erradicación total de `get_favorite_pack` | Reintroducir `def get_favorite_pack(self):` en `pack_service.py` | killed | `AssertionError: Función obsoleta get_favorite_pack() encontrada` en `run_tests.py:1030` |

### Cambios Clave
- `src/woptimizer/services/pack_service.py`: Refactorizado `set_favorite(pack_id, value)` a semántica acumulativa sin desmarcar otros packs. Añadido `toggle_favorite(pack_id) -> bool` que lee estado vivo, invierte, persiste y retorna el nuevo valor. Retirado `get_favorite_pack` e incorporado `get_favorite_packs() -> List[Pack]`. En `_ensure_gaming_pack()`, restaurado `is_favorite = True` defensivo. Validación `ValueError` ante `pack_id` nulo/vacío.
- `src/woptimizer/ui/views/pack_manager_view.py`: Delegado `toggle_favorite(pack_id)` al método del servicio manteniendo fallback de retrocompatibilidad.
- `run_tests.py`: Sustituido `test_pack_service_favorite_exclusive` por `test_pack_service_favorites_acumulan` y añadido `test_pack_service_favorite_contracts_and_resilience`. Actualizadas las 3 semillas con 2º argumento booleano en `set_favorite`.
- `docs/ai/architecture.md`: Añadida sección 17 sobre semántica acumulativa e invariantes de favoritos.
- `docs/ai/testing-guide.md`, `STATUS.md`, `AGENTS.md`, `README.md`: Suite elevada y sincronizada a 92 tests en verde.

---

## [CYCLE-037] 2026-10-01 22:50 — gaming-session-concurrency-resilience
**Área**: Resiliencia & Robustez
**Change**: openspec/changes/2026-10-01-gaming-session-concurrency-resilience/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): flash (Área 1)
- Paso 2 (Planear): architect-review → VISTO BUENO Y APROBADO
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO Y DOCUMENTADO
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (4/4 mutaciones eliminadas: M1, M2, M3, M4)

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| RLock reentrante en `GamingService` | En `__init__`, asignar `self._lock = threading.Lock()` o no asignarlo | killed | `AssertionError: GamingService._lock debe ser de tipo threading.RLock` en `run_tests.py:10871` |
| Exclusión mutua en `restore_gaming_session` | Extraer `apps_to_restore` sin `with self._lock:` | killed | `AssertionError: restore_gaming_session debe respetar self._lock y no vaciar apps mientras el cerrojo está tomado` en `run_tests.py:10901` |
| Preservación defensiva de estado ante fallo | Omitir bloque de rescate en `except Exception:` | killed | `AssertionError: Las apps cerradas deben preservarse íntegramente ante fallos imprevistos en start_pack_apps` en `run_tests.py:10948` |
| Aislamiento de excepciones no-OSError en lote | En `start_pack_apps`, capturar solo `except OSError:` | killed | `RuntimeError: Corrupted executable path resolution` en `run_tests.py:10964` |

### Cambios Clave
- `src/woptimizer/services/gaming_service.py`: Inicializado `threading.RLock()` en `__init__`. Protegidos `get_last_closed_apps`, `clear_last_closed_apps`, `execute_gaming_pack` y `restore_gaming_session` bajo el cerrojo con extracción atómica y re-inserción defensiva en caso de excepción.
- `src/woptimizer/services/process_service.py`: Ampliada captura en `start_pack_apps` a `(OSError, Exception)` aislando fallos por aplicación sin interrumpir el lote.
- `run_tests.py`: Añadido `test_gaming_service_rlock_and_concurrency` (test #91) con prueba de contención de cerrojo, concurrencia de 5 hilos, preservación de estado y aislamiento no-OSError.
- `docs/ai/architecture.md`: Añadida sección 16 sobre invariantes de concurrencia y resiliencia en `GamingService`.
- `docs/ai/testing-guide.md`, `STATUS.md`, `AGENTS.md`, `README.md`: Suite elevada a 91 tests en verde.

---

## [CYCLE-036] 2026-10-01 18:50 — confirmable-mixin-contracts
**Área**: Testing & Calidad
**Change**: openspec/changes/2026-10-01-confirmable-mixin-contracts/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): flash (Área 5)
- Paso 2 (Planear): architect-review → VISTO BUENO Y APROBADO
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO Y DOCUMENTADO
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (5/5 mutaciones eliminadas: M1, M2a, M2b, M3, M4)

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| Throttling 300 ms (`disabled` temporal) | En `Confirmable._restaurar_boton()`, omitir `self._configurar(button, state="disabled")` | killed | `AssertionError: Botón debe quedar deshabilitado temporalmente (throttling)` en `run_tests.py:10780` |
| Cancelación del guard en destrucción | En `Confirmable.cancel_on_destroy()`, omitir `self._guard.cancel_on_destroy()` | killed | `AssertionError` en `run_tests.py:10826` |
| Cancelación y vaciado de `_timers_ui` | En `Confirmable.cancel_on_destroy()`, omitir la cancelación y vaciado de `_timers_ui` | killed | `AssertionError: cancel_on_destroy debe vaciar _timers_ui` en `run_tests.py:10828` y `AssertionError: cancel_on_destroy debe cancelar los timers pendientes en el scheduler` en `run_tests.py:10829` |
| Captura de texto original en reposo | En `Confirmable._recordar_reposo()`, no almacenar en `self._reposo[token]` | killed | `AssertionError: Botón debe restaurar su texto original de reposo` en `run_tests.py:10777` |
| Limpieza total de `_reposo` al recrear botones | En `Confirmable._forget_buttons()`, omitir `self._reposo.clear()` | killed | `AssertionError: _forget_buttons() debe limpiar _reposo completamente` en `run_tests.py:10841` |

### Cambios Clave
- `run_tests.py`: +1 test estrictamente discriminante (`test_confirmable_mixin_lifecycle_and_widget_contracts`) que evalúa la máquina de estados de `Confirmable` en `src/woptimizer/ui/confirmation.py` sin requerir Tkinter ni ventanas vivas. Aserciones reforzadas para liquidar mutantes M2b y M4. Suite elevada a 90 tests headless al 100% en verde.
- `docs/ai/testing-guide.md`: Actualizada fila 90 de tests y documentación viva.
- `README.md`, `STATUS.md`, `AGENTS.md`: Actualizados a 90 tests.

---

## [CYCLE-035] 2026-10-01 18:35 — categorization-latency-optimization
**Área**: Rendimiento & Latencia
**Change**: openspec/changes/2026-10-01-categorization-latency-optimization/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): flash (Área 4)
- Paso 2 (Planear): architect-review → VISTO BUENO Y APROBADO
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO Y DOCUMENTADO
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (5/5 mutaciones eliminadas: M1, M2, M3a, M3b, M4)

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| Invalidación atómica de `_proc_cache` en `_load_local_db()` | Eliminar `self.invalidate_cache()` | killed | `AssertionError: _proc_cache debe quedar en None tras invalidate_cache() en _load_local_db()` |
| Vaciado de `_meta_cache` en `_load_local_db()` | Eliminar `self._meta_cache.clear()` | killed | `AssertionError: _meta_cache debe vaciarse al recargar la DB` |
| Persistencia en `_meta_cache` de exact match | Eliminar `self._meta_cache[name_clean] = hit` | killed | `assert "chrome" in svc._meta_cache` |
| Persistencia en `_meta_cache` de fallback | Eliminar `self._meta_cache[name_clean] = _DEFAULT_META` | killed | `assert "proceso_totalmente_desconocido_xyz" in svc._meta_cache` |
| Hit O(1) de memoización en `_meta_cache` | Desconectar lookup: `cached = self._meta_cache.get(name_clean)` | killed | `AssertionError: Debe retornar la categoría desde _meta_cache O(1) incluso con _db_map vacío: '⚪ Otros'` |

### Cambios Clave
- `src/woptimizer/services/process_service.py`: En `_load_local_db()`, añadida llamada atómica a `self.invalidate_cache()` tras `self._meta_cache.clear()`.
- `run_tests.py`: +1 test estrictamente discriminante (`test_process_categorization_latency_and_memoization`) y fix en target de mock para `test_tray_session_restoration_integration`. Suite elevada a 89 tests al 100% en verde.
- `docs/ai/architecture.md` y `docs/ai/testing-guide.md`: Actualizada documentación viva y tabla de 89 tests.

---

## [CYCLE-034] 2026-10-01 16:05 — process-db-expansion-c34
**Área**: Base de Datos & Procesos
**Change**: openspec/changes/2026-10-01-process-db-expansion-c34/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): process-db-updater (Área 3)
- Paso 2 (Planear): process-db-updater → ESPECIFICACIÓN Y PROPOSAL REDACTADOS
- Paso 3 (Ejecutar): process-db-updater → 7 PROCESOS REALES INTEGRADOS (96 TOTAL)
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (Esquema estricto validado por test_process_db_schema_integrity)

### Cambios Clave
- `assets/process_db.json`: +7 nuevos procesos (`rtss`, `msiafterburner`, `hwinfo64`, `galaxyclient`, `everything`, `gitkraken`, `postman`). Total: 96 entradas.
- `docs/ai/data-models.md`: Actualizada documentación de modelos.
- `openspec/changes/2026-10-01-process-db-expansion-c34/`: Creados `proposal.md` y `tasks.md`.

---

## [CYCLE-033] 2026-10-01 15:45 — tray-session-restoration-ux
**Área**: Gaming & Telemetría UX
**Change**: openspec/changes/2026-10-01-tray-session-restoration-ux/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): flash (Área 2)
- Paso 2 (Planear): architect-review → VISTO BUENO Y APROBADO
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO Y DOCUMENTADO
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (+1 test discriminante validado)

### Cambios Clave
- `src/woptimizer/ui/app.py`: Opción `'🔄 Reabrir aplicaciones cerradas'` en el menú contextual de `pystray`. Ejecución asíncrona de restauración de sesión gaming y notificación nativa.
- `run_tests.py`: +1 test discriminante (`test_tray_session_restoration_integration`). Suite elevada a 88 tests al 100% en verde.
- `docs/ai/architecture.md`: Actualización de la documentación viva.

---

## [CYCLE-032] 2026-10-01 15:30 — system-resilience-hardening
**Área**: Resiliencia & Robustez
**Change**: openspec/changes/2026-10-01-system-resilience-hardening/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): flash (Área 1)
- Paso 2 (Planear): architect-review → VISTO BUENO Y APROBADO
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO Y DOCUMENTADO
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (+2 tests discriminantes validados)

### Cambios Clave
- `src/woptimizer/services/notification_service.py`: Reemplazo de `threading.Lock()` por `threading.RLock()` para thread-safety reentrante.
- `src/woptimizer/services/process_service.py`: Captura defensiva de `psutil.ZombieProcess` y `OSError` en `kill_processes` y `kill_pack_apps`.
- `run_tests.py`: +2 tests discriminantes (`test_notification_service_rlock_and_concurrency`, `test_process_service_kill_defensive_zombie_and_oserror`). Suite elevada a 87 tests al 100% en verde.
- `docs/ai/architecture.md`: Actualización de la documentación viva.

---

## [CYCLE-031] 2026-10-01 10:10 — testing-quality-expansion-c31
**Área**: Testing & Calidad
**Change**: openspec/changes/2026-10-01-testing-quality-expansion-c31/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): flash (Área 5)
- Paso 2 (Planear): architect-review → VISTO BUENO Y APROBADO
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO Y DOCUMENTADO
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (100% mutaciones eliminadas)

### Cambios Clave
- `run_tests.py`: +2 tests discriminantes (`test_pydantic_extra_fields_persistence`, `test_freed_mb_calculation_precision`). Suite elevada a 85 tests.
- Re-auditoría con `patch("psutil.Process")` en `test_freed_mb_calculation_precision`: mutaciones en `process_service.py:586` aniquiladas exitosamente.

---

## [CYCLE-030] 2026-10-01 09:50 — ui-filter-and-pack-latency-opt
**Área**: Rendimiento & Latencia
**Change**: openspec/changes/2026-10-01-ui-filter-and-pack-latency-opt/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): flash (Área 4)
- Paso 2 (Planear): architect-review → VISTO BUENO Y APROBADO
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO Y DOCUMENTADO
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (3/3 mutantes supervivientes de la 1ª iteración eliminados)

### Cambios Clave
- `src/woptimizer/services/pack_service.py`: Caché de lectura defensiva en 2 capas (< 0.05 ms) e invalidación atómica.
- `src/woptimizer/ui/views/process_manager_view.py`: Pre-tokenizado y filtrado rápido (< 2.0 ms) para 350+ procesos.
- `run_tests.py`: +2 tests discriminantes (`test_pack_service_cache_invalidation_and_immutability`, `test_process_filter_performance`). Total suite elevando a 83 tests.

---

## [CYCLE-029] 2026-10-01 09:10 — process-db-expansion-c29
**Área**: Base de Datos & Procesos
**Change**: openspec/changes/2026-10-01-process-db-expansion-c29/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): flash (Área 3)
- Paso 2 (Planear): process-db-updater → VERIFICADO
- Paso 3 (Ejecutar): process-db-updater → IMPLEMENTADO
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (89 procesos validados sin omisiones ni solapamientos)

### Cambios Clave
- `assets/process_db.json`: +8 nuevos procesos reales (`89 total`).
- 0 solapamientos con `SYSTEM_PROTECTED_PROCESSES` (34 procesos protegidos).
- `test_process_db_schema_integrity` y `test_category_emoji_alignment` pasando al 100%.

---

## [CYCLE-028] 2026-10-01 08:50 — gaming-session-restoration
**Área**: Gaming & Telemetría UX
**Change**: openspec/changes/2026-10-01-gaming-session-restoration/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): flash (Área 2)
- Paso 2 (Planear): architect-review → VISTO BUENO Y APROBADO
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO Y DOCUMENTADO
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (100% mutaciones eliminadas)

### Cambios Clave
- `GamingService._last_closed_apps`: Captura pre-kill de rutas `.exe` absolutas únicas.
- `GamingService.restore_gaming_session()`: Reabre aplicaciones vía `start_pack_apps`.
- `DashboardView._show_restore_banner`: UI thread-safe con botón "Reabrir Apps".
- `test_gaming_service_session_restoration`: Test unitario registrando suite total de 81 tests.

---

## [CYCLE-027] 2026-10-01 08:15 — guardas-que-no-guardan
**Área**: Resiliencia & Robustez / Deuda Técnica
**Change**: openspec/changes/2026-09-30-guardas-que-no-guardan/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): flash (backlog TASK-037)
- Paso 2 (Planear): architect-review → VISTO BUENO CON DIRECTRICES OBLIGATORIAS
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (9/9 mutaciones aniquiladas por aserción)

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| _recuento_de_tests | M1 except sin SyntaxError | killed | IndentationError no capturado |
| _recuento_de_tests | M2 except sin OSError | killed | FileNotFoundError no capturado |
| _comprobar_recuento | M3 rama muerta | killed | Faltan mensajes [FAIL] |
| _comprobar_recuento | M4 ok.append en vez de error | killed | Falso OK en resumen |
| guard_llamantes | M5 tupla literal fija 3 ficheros | killed | Modulo sintetico 4 no se marca |
| guard_llamantes | M6 descarta ast.Attribute | killed | fb.mensaje_sin_apps no se marca |
| guard_llamantes | M7 marca todo | killed | Marca literales validos 'start'/'kill' |
| guard_llamantes | M8 limita a ui/views/ | killed | Modulo sintetico fuera de views/ no se marca |
| huerfanos | M9 concatena segmento vacio | killed | Se emite 'invocado y NO definido: .' |

### What
- _recuento_de_tests en validate_docs.py emite None ante OSError y SyntaxError de run_tests.py.
- Extraida la funcion _comprobar_recuento_de_tests para hacer testeable el check 7.
- El guard de contrato de llamantes de ui.feedback deriva su alcance con AST en vez de una tupla estatica.
- Soporte para ast.Attribute y ast.Name en las llamadas a feedback.
- Test con arbol sintetico de 4 modulos en run_tests.py.

### Outcome
- Commits: `pending`
- Tests: 80/80 PASS (75 backend + 5 UI headless)
- Docs: STATUS.md, AGENTS.md, README.md, testing-guide.md actualizados

### Impact
Se eliminan tres puntos ciegos de diagnostico y verificacion en el tooling que vigila la calidad del producto. El recuento total de tests asciende a 80 y queda protegido por deriva automatica mediante AST.

---

## [CYCLE-026] 2026-09-30 23:05 — pack-telemetry-feedback
**Área**: Gaming & Telemetría UX
**Change**: openspec/changes/2026-09-30-pack-telemetry-feedback/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): heredado del turno (backlog vacío → rotación; `TASK-035` ya `completed` en `tasks.json` pero **sin** entrada en el journal, changelogs ni Paso 4: ciclo a medias heredado de la sesión anterior)
- Paso 2 (Planear): architect-review → VISTO BUENO; además **decisión de producto** en la iteración 4 (`decision-portada-pack-vacio.md`, `TASK-036`, commit `4ce17ea`) con 9 criterios discriminantes y 8 mutaciones exigidas, sin cambios en `src/`
- Paso 3 (Ejecutar): openspec-dev → iteraciones 1 a 6
- Paso 4 (Auditar tests): mutation-auditor → **7 rondas**: FAIL, FAIL, FAIL, PARTIAL, FAIL, FAIL, **PASS**
- Stepper: MiniMax-M3.1 (orquestador)

### Historial de las seis iteraciones
| iter | veredicto | qué encontró |
|---|---|---|
| 1 | FAIL | `kill_pack` pintaba `"<tick> 0 procesos cerrados (0.0 MB liberados)"` en VERDE Gaming con `killed == 0`; la guarda AST era una lista de 3-4 nombres de método |
| 2 | FAIL (80 mutaciones, 58 muertas, **21 supervivientes**) | El fix de la iteración 1 announcementaba lo que hacía pero dejaba **una tercera puerta** (`on_kill_selected`) mintiendo en verde, el bloque de cancelación del temporizador **duplicado byte a byte** con la sonda instrumentando solo una mitad, cuatro ramas sin ejecutar, y cinco afirmaciones documentales falsas |
| 3 | FAIL (3 supervivientes) | La ronda 3 cerró las tres puertas de feedback, el formateador común, los temporizadores de las dos puertas, el umbral `killed == 1`, el orden de la 4-tupla, el alcance de la guarda AST y el alias muerto. Quedaron 3 de severidad ALTA: la **rama `start` sin ejecutar**, la **guarda AST que era una red y el doc la llamaba muro**, y el **sustantivo probado solo en la rama éxito**; más tres afirmaciones documentales falsas más (`len(to_kill)`, la matriz de mutaciones inflada e irreproducible, y "las dos vistas") |
| 4 | PARTIAL → FAIL → FAIL → **PASS** | Cerró las tres de ALTA con test y ejecutó la decisión de producto TASK-036. Las rondas 4 y 5 model's Subsequentaron dos bugs vivos más: **D5** (el verbo de la puerta de apagar salía de `pack.default_action`, así que un pack recién creado decía "iniciar" al pulsar **Apagar** — la primera acción de un usuario recién instalado) y **K-a** (el **segundo** punto de la doble guarda de `kill_pack` sin un solo test, con el doc afirmándolo guardado, y mutarlo lanzaba un apagado con lista vacía tras consumir la doble pulsación). Ronda 6: **P-d** (tarjeta con `"KILL"` congelado), el **default silencioso** de `VERBOS`, y el **nº de tests caducado en tres ficheros sin declarar**. Ronda 7: **PASS**, 43/43 mutaciones de `src/` aniquiladas por `AssertionError`. |

### Iteración 7 — cierre (VIGENTE, amplía la tabla de la iteración 4)
Ronda final del `mutation-auditor`: **46 mutaciones + 15 controles negativos de validador**,
**43 muertes de `src/` por `AssertionError`**, 0 supervivientes de producción.
Clasificación exigida por el Stepper: **0 sin cobertura**, 1 equivalente (mutante propio del
auditor), 2 inertes/manipulación de detector. La matriz del dev (`_matrix_c26.py`) da **30/30**
y fue reproducida con un driver independiente, no aceptada como fuente.

| Foco | Veredicto | Evidencia |
|---|---|---|
| K-a (2º punto de la doble guarda) | **MUERE por aserción** | `llamadas_cierre == 0`: "el pack perdió sus apps ENTRE las dos pulsaciones: la segunda guarda de kill_pack tiene que avisar, no lanzar kill_pack_apps([]) después de haber co…" |
| K-a · control de carga | **VIVE por diseño, y es lo correcto** | con solo 2 lecturas **y** sin la aserción `lecturas == 3` la prueba pasa: esa aserción es lo único que distingue "midió el 2º punto" de "midió el 1º por accidente". Comprobado en las dos direcciones |
| P-d (tarjeta) | **MUERE** × 4 | literal `KILL`/`START`/vacío y `upper()`→`lower()`; vía real `refresh_dashboard` → `cget("text")` |
| `VERBOS` sin default silencioso | **MUERE** × 5 | `.get` con default, verbo cableado en ambas puertas, `KeyError` silenciado, verbo como clave del mapa, default del modelo a `"kill"` |
| Guard del cableado (posición) | **CONFIRMADO** | sin el guard, D5-e muere por `KeyError`; con el guard primero, muere por `AssertionError` nombrando fichero y línea. El dev lo movió al principio por esto y el auditor lo verificó |
| Regresión R5 | **21/21 MUEREN** | 0 crashes, 0 anclas caducadas |
| Call-sites y hilos | **sin sexto lado** | 3 call-sites / 4 invocaciones de la familia `(texto, color)`, 2 de `es_pack_inerte`, 9 `Thread` en `src/` (3 fuera de vistas + 6 en 5 métodos de 3 clases), ninguno fuera de `PERMITIDOS` |
| `validate_docs.py` check 7 | **13/15 controles limpios** | 28 en `AGENTS.md`, invocación borrada, `def` sin invocar, fila de tabla borrada, línea de `README` borrada, fichero ausente, forma alternativa, fila duplicada → todos FAIL con mensaje útil |

**Deuda nueva, no bloqueante** (el auditor la measured y no la considera oculta):
- **MEDIA**: `validate_docs.py` revienta con `SyntaxError`/`FileNotFoundError` si `run_tests.py`
  no se parsea, y su rama `if n_tests is None:` es **código muerto** —`_recuento_de_tests` lanza,
  nunca devuelve `None`. Guarda que no guarda. No produce falso verde (rc=1), es agujero de
  diagnóstico, no de detección.
- **BAJA**: residuo cosmético en el mensaje del check 7 (`invocado y NO definido: .`).
- **BAJA**: el guard AST de los llamantes tiene **lista de ficheros fija**; un tercer módulo que
  cablee un verbo no lo encuentra.
- **BAJA**: el guard AST no tiene prueba de sí mismo (`G-1`, guard→rama muerta, vive con código sano).
- **Anclas caducadas fuera del alcance del dev** (las cierra el orquestador):
  `decision-portada-pack-vacio.md:9-15` —además de caducado, **falso**: afirma una duplicación
  byte a byte que TASK-036 eliminó— y `docs/ai/data-models.md:377-378` (`pack_manager_view.py:100`
  → hoy `:227`; `gaming_service.py:16` → hoy un comentario).

**Correcciones al propio briefing del orquestador** (registradas para que no se repitan):
el conteo de formateadores es **4**, no 5 (el auditor erró en R5/R6; verificado con `ast` sobre
`feedback.py`), y el briefing-guía decía "4 S1-*" cuando el repo tiene 3 (S1-a/b/c).

### Iteración 3 — mutaciones verificadas a mano (TABLA RETIRADA, ver nota)
Reproducidas con un script temporal que reescribía `src/` **en el sitio del árbol real**. Esa
tabela declaraba "15 mutaciones, 15 muertas, 0 supervivientes" y **no es reproducible**:

* la #13 (`kill_pack` deja de avisar del pack inexistente) murió por un
  `AttributeError: 'NoneType' object has no attribute 'is_gaming'`, es decir por un **crash**,
  no por una aserción: un mutante que revienta el código no demuestra que el test lo detects;
* la #15 (el sustantivo se ignora) sobrevivió en la primera pasada y se dio por cerrada con un
  caso que solo miraba la rama de éxito. La afirmación "el sustantivo se ignora" era cierta
  para **una** de las dos ramas que lo usan;
* el utillaje `_matrix_c26.py` que acompaña al auditor, **reventaba** en la mutación 5 de 12
  (`AssertionError: no se encontró el ancla de M6`) y lanzaba 2 de las 3 sondas, así que la
  tercera puerta nunca estuvo en la tabla que el doc daba por buena.

**Las quince filas NO se conservan aquí.** Una tabla de mutaciones que nadie puede reproducir
es peor que no tenerla: parece cobertura y no lo es. Quedan en el historial (`git log`, commit
de la iteración 3) como registro de lo que se midió entonces; la tabla vigente, con su salida
literal, es la de la iteración 4.

### Iteración 4 — mutaciones verificadas con salida real (VIGENTE)
`python _matrix_c26.py`, que ahora **sí** se puede ejecutar: copia el árbol a `%TEMP%`, aplica
una mutación, purga `__pycache__` y corre **las tres sondas** en un subproceso. Un ancla que
no se encuentra es un **error duro**, no una mutación saltada. Salida literal del 2026-09-30:

```
CONTROL (sin mutar): rc=0 -> VERDE
M-A  execute_pack vuelve al return mudo (el silencio)          MUERE  | un pack no gaming y vacio SE AVISA, no se traga en silencio
M-B  el verbo se cablea a 'apagar' en vez de mapearse          MUERE  | aviso preventivo de pack vacio: "... no tiene apps que apagar"
M-C  el aviso del pack vacio se pinta en el color de marca     MUERE  | el aviso de pack inerte es de ATENCION
M-D  la guarda se queda sin sitio                               MUERE  | un pack no gaming y vacio SE AVISA, no se traga en silencio
M-E  se borra el diagnostico del Gaming Mode inerte            MUERE  | el Gaming Mode inerte se diagnostica
M-F  es_pack_inerte con 'or' en vez de 'and'                   MUERE  | se esperaba 1 worker secundario, se crearon 0
M-G  el aviso reusa _inline_status                             MUERE  | el aviso va sobre SURFACE_ALT, no sobre el fondo CANCEL
M-H  se borra la clausula 'freed_mb <= 0' de clausula_mb       MUERE  | cerrar un proceso sin liberar MB no puede inventar una cifra de RAM
S1-a _run_start intercambia launched y failed                  MUERE  | el worker de arranque tiene que entregar launched y failed sin intercambiarlos
S1-b _run_start arranca start_pack_apps([])                    MUERE  | la rama start arranca SUS apps, no una lista vacia: llego []
S1-c _run_start publica en _show_banner con el NOMBRE          MUERE  | el after debe publicar en _show_start_banner
S2-a la guarda vuelve a no bajar por getattr/setattr            MUERE  | la guarda no ve los accesos dinamicos a la vista
S2-b la guarda vuelve a ignorar ast.Delete                     MUERE  | la guarda no ve los `del` sobre la vista
S2-c la guarda vuelve a mirar solo call.func                   MUERE  | no ve self.<attr> como ARGUMENTO de una llamada permitida
S3   el sustantivo se cablea a 'procesos' en la rama 'nada'    MUERE  | el sustantivo tambien se usa en la rama 'nada'
R-1  clasificar_cierre dice siempre EXITO                      MUERE  | nada que cerrar dice exactamente eso
R-2  _show_banner deja de refrescar la barra de reposo         MUERE  | _show_banner tiene que refrescar la barra de reposo
R-3  se borra la cancelacion del auto-ocultado previo          MUERE  | el banner nuevo debe cancelar el auto-ocultado anterior
R-4  el worker de la portada vuelve a tirar failed/skipped     MUERE  | el worker tiene que entregarle a _show_banner el resultado completo
R-5  la guarda AST anulada (return [] siempre)                 MUERE  | el detector no ve las tres infracciones de control

supervivientes: ninguno
```

**20 mutaciones, 20 muertes, 0 supervivientes** (tabla de la iteración 4; **21** desde la iteración 6,
ver más abajo). Las ocho primeras son las que exige
`decision-portada-pack-vacio.md` §4 (M-A a M-H). Las tres `S1-*` son las de la rama `start` que
no se ejecutaba; las tres `S2-*` son "se devuelve el detector a su versión anterior" y mueren en
sus propios controles sintéticos; `S3` es el sustantivo en la rama `nada`; y las cinco `R-*` son
regresión de lo que las iteraciones 2 y 3 ya cerraron. Las que mueren por aserción y no por
crash se distinguen en la salida: en esta tabla **las veinte mueren por `AssertionError`**, que
es lo que hace que la tabla signifique algo.

### Iteración 6 - el superviviente D5 y el cierre de la tabla (2026-10-01)

**Qué era D5.** El `mutation-auditor` cerró el ciclo con **un solo superviviente**, y no era un
hueco de cobertura sino **un bug vivo en producción**: el espejo exacto del que la iteración 5
cerró en `start_pack`. Esa iteración ató el verbo al **método** (`mensaje_sin_apps(pack.name,
"start")`, `pack_manager_view.py:527`) y dejó el otro lado del **mismo helper** atado al pack.
`_aviso_pack_inerte` es la puerta de **apagar** y la cableaba con `pack.default_action`, así que:

```
pack recien creado: apps=[] is_gaming=False default_action='start'
usuario pulsa [Apagar]  ->  "no tiene apps que INICIAR"
```

Cadena verificada de punta a punta: `on_new_pack` → `create_user_pack(pack_id, name, [])`
(`pack_manager_view.py:432`) → `Pack(...)` sin `default_action` (`pack_service.py:638`) → el
default del modelo `"start"` (`models.py:54`) → tarjeta con **los dos** botones (`:253` ⛔ Apagar /
`:264` 🚀 Iniciar) → `kill_pack` → `_aviso_pack_inerte` → verbo de la puerta equivocada. No era un
caso límite: es la **primera acción de un usuario recién instalado**.

**Por qué la suite no lo veía.** El Gestor se probaba con pack **gaming** inerte (inmune: lo
diagnostica `_aviso_pack_inerte` antes de llegar al aviso de apps) y con un **id inexistente**
(regresa antes de leer el pack). No existía ningún `kill_pack` con pack **no gaming vacío**, que es
la única rama que produce el verbo: la tabla del auditor lo medía así y las dos filas
`default='kill'` / `default='start'` salían idénticas al código correcto salvo en la que el
mutante cambiaba.

**Arreglo.** `_aviso_pack_inerte` cablea `"kill"`, con el argumento que ya estaba escrito para
`start_pack` en el mismo fichero. Y el caso que lo ata: `Pack(id="recien", apps=[],
default_action="start")` en `kill_pack`, con el texto exacto **"no tiene apps que apagar"**. El
pack es **no gaming a propósito**: con `is_gaming=True` el diagnóstico del gaming inerte cortaría
antes y el assert moriría por otra cosa, que es exactamente el falso verde que hay que evitar.

**Los dos veredictos de mutación de `:469`** (medidos sobre copia en `%TEMP%`, `src/` nunca en
sitio, control en verde antes de mutar):

```
D5-a  mutado a pack.default_action  MUERE  | el verbo lo decide la PUERTA que se esta pulsando
                                                (aqui apagar), no el `default_action` del pack:
                                                Texto: "'Mi Pack' no tiene apps que iniciar."
D5-b  mutado a "start" a pelo        MUERE  | (la misma asercion, mismo veredicto)
```

**La tabla del ciclo queda en 21/21, 0 supervivientes** (`python _matrix_c26.py`, 2026-10-01,
`D5` incluida). El recuento de tests **sigue siendo 78**, comprobado **con parser**
(`ast` sobre `run_tests.py`: 78 `def test_` a nivel de módulo, sin duplicados), no supuesto: el
caso nuevo vive **dentro** de `test_el_feedback_de_pack_dice_la_verdad`, como los dos bloques de la
iteración 5.

### Iteración 5 - D1 a D4, medidas aquí y transcritas al `testing-guide.md`

La iteración 5 añadió dos bloques a la sonda (el verbo atado al método en `start_pack` y el
contrato de canal no vacío) y **no dejó su tabla de mutaciones escrita**: `testing-guide.md` seguía
diciendo 20/20 y etiquetaba la fila como "iter 3 / TASK-036 (iter 4)". Medidas ahora sobre copia,
con salida literal, y transcritas a `docs/ai/testing-guide.md`:

```
D1  start_pack vuelve a cablear el verbo al pack (pack.default_action)  MUERE
D2  start_pack cablea el verbo a 'kill' a pelo                          MUERE
D3  el canal inline de la base pinta fondo CANCEL                       MUERE
D4  el aviso del pack vacio pierde su texto (canal vacio)               MUERE
```

**4 mutaciones, 4 muertes, 0 supervivientes.** La lección de D1, generalizable y ya escrita en el
`testing-guide.md`: para afirmar que un valor **no** está cableado a un campo, el fixture tiene que
hacer que ese campo valga **lo contrario**. El pack vacío que ya había traía `default_action="start"`
de serie, así que `"start"` y `pack.default_action` daban el mismo texto y la convención quedaba sin
medir. D5 es el mismo error con la puerta cambiada.


### Pendiente de este pase
- `CHANGELOG.md` y esta entrada cierran el pase, pero **no cierran el ciclo**: el Paso 4 sigue
  siendo del `mutation-auditor` y TASK-036 sigue `pending` en `.taskmaster/tasks.json` a
  propósito (la marca el orquestador según el veredicto).
- **No se ha mutado `src/` en sitio en esta iteración**: todas las mutaciones se aplican a una
  copia en `%TEMP%`.

---

## [CYCLE-025] 2026-09-30 21:08 — testing-quality-expansion
**Área**: Testing & Calidad
**Change**: openspec/changes/2026-09-30-testing-quality-expansion/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): inherit
- Paso 2 (Planear): architect-review → VISTO BUENO CON DIRECTRICES OBLIGATORIAS
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO
- Paso 4 (Auditar tests): mutation-auditor → VERDICT: PASS (7/7 mutantes eliminados)

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| M1 (Strict bools) | Relajar a `is_favorite: bool = Field(default=False)` (permite coerción laxa de `"true"` o `1`) | killed | `test_models_strict_validation_and_contracts capturó coerción de is_favorite` |
| M1b (Strict bools) | Relajar a `is_gaming: bool = Field(default=False)` (permite coerción laxa de `"true"` o `1`) | killed | `test_models_strict_validation_and_contracts capturó coerción de is_gaming` |
| M2 (Literal action) | Cambiar tipo a `default_action: str = "start"` (permite `"purgar"` o `"KILL"`) | killed | `test_models_strict_validation_and_contracts capturó default_action inválida` |
| M3a (Extra allow) | Cambiar a `ConfigDict(extra="ignore")` en `Pack` | killed | `test_models_strict_validation_and_contracts detectó pérdida de meta_custom` |
| M3b (Extra allow) | Cambiar a `ConfigDict(extra="ignore")` en `AppData` | killed | `test_models_strict_validation_and_contracts detectó pérdida de legacy_profiles` |
| M4 (Defaults) | Alterar `exe_path="unknown"` o `category="Otros"` en `ProcessInfo` | killed | `test_models_strict_validation_and_contracts detectó desalineación de defaults` |
| M5 (Destrucción UI) | Omitir `self.current_view.destroy()` en `MainWindow._clear_content` | killed | `test_main_window_navigation_transitions detectó vista previa aún viva con winfo_exists()` |
| M6 (Afordancia nav) | Invertir o alterar tokens de borde en `MainWindow._set_active_nav` | killed | `test_main_window_navigation_transitions detectó fallo de estilos activo/inactivo` |
| M7 (Transición UI) | No instanciar o no reasignar `self.current_view` a la clase esperada | killed | `test_main_window_navigation_transitions detectó clase incorrecta en current_view` |

### What
- Implementación de la prueba discriminante `test_models_strict_validation_and_contracts()` en `run_tests.py`:
  - Valida el rechazo de coerciones laxas (`"true"`, `"false"`, `1`, `0`) en `Pack.is_favorite` e `is_gaming` mediante `strict=True`.
  - Valida la restricción estricta de `default_action` a `Literal["start", "kill"]`, rechazando valores no reconocidos (`"purgar"`, `"KILL"`, `""`, `None`).
  - Valida la supervivencia y retención de metadatos adicionales en `Pack` y `AppData` vía `extra="allow"`.
  - Valida los valores canónicos por defecto de `ProcessInfo` (`exe_path=""`, `category="⚪ Otros"`, `priority="none"`).
- Implementación de la prueba headless de integración `test_main_window_navigation_transitions()` en `run_tests.py`:
  - Instancia `MainWindow` sobre un contenedor headless con `root.withdraw()` y servicio de persistencia aislado (`_pack_service_temporal()`).
  - Verifica la vista inicial `DashboardView` y el estado activo del botón de portada (`theme.ACCENT`, `border_width=2`).
  - Navega a `PackManagerView` (`_show_packs()`), verificando la destrucción física del widget previo (`not winfo_exists()`) y la conmutación de estilos en `btn_nav_packs`.
  - Navega a `ProcessManagerView` (`_show_process_manager()`), verificando destrucción previa, conmutación de estilo y bombeo en mainloop para la carga asíncrona de procesos.
  - Navega de regreso a `DashboardView` (`_show_home()`) y ejecuta el cierre limpio de Tcl/Tk.
- Registro de los nuevos tests en `run_tests.py` elevando la suite oficial a **75 tests** (73 backend + 2 headless UI).
- Actualización de documentación viva en `docs/ai/testing-guide.md`.

### Outcome
- Commits:
  - `d4feeb8` (plan: registrar TASK-034 en tasks.json y openspec)
  - `2bc869e` (feat: pruebas de navegacion UI y contratos Pydantic)
- Tests: 73 backend + 2 headless UI PASS (0 fallos).
- Docs: `validate_docs.py` (70 OK, 0 FAIL).

### Impact
Se eliminan puntos ciegos críticos en la suite de pruebas sin abrir ventanas ni introducir lentitud. La navegación completa entre las tres pantallas principales y el esquema de modelos quedan cubiertos contra regresiones accidentales de tipado o ciclo de vida.

---

## [CYCLE-024] 2026-09-30 20:53 — scan-latency-optimization
**Área**: Rendimiento & Latencia
**Change**: openspec/changes/2026-09-30-scan-latency-optimization/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): inherit
- Paso 2 (Planear): architect-review → VISTO BUENO CONDICIONADO (4 directrices críticas)
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO
- Paso 4 (Auditar tests): mutation-auditor → VERDICT: PASS (6/6 mutantes eliminados)

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| M1 (Escaneo ligero) | Reintroducir `exe` en `psutil.process_iter` y asignar `exe_path` ansiosamente | killed | `test_scan_latency_and_lazy_exe_resolution falló: exe_path no estaba vacío en escaneo general` |
| M2 (Resolución lazy) | Modificar `get_process_exe_path` para retornar siempre `""` | killed | `test_scan_latency_and_lazy_exe_resolution falló: la resolución lazy devolvió cadena vacía para PID propio` |
| M3 (Robustez PID) | Quitar guarda `pid <= 0` o captura de `ValueError` en `get_process_exe_path` | killed | `test_scan_latency_and_lazy_exe_resolution falló: PID negativo levantó excepción sin degradar a ""` |
| M4 (UI on_add_to_pack) | Omitir llamada a `get_process_exe_path` en `on_add_to_pack` | killed | `test_scan_latency_and_lazy_exe_resolution falló: on_add_to_pack no resolvió ruta absoluta` |
| M5 (Blindaje AST) | Desplazar líneas 33-48 de `SYSTEM_PROTECTED_PROCESSES` en `process_service.py` | killed | `test_la_documentacion_del_blindaje_no_puede_desfasarse detectó desplazamiento AST` |
| M6 (Headless View) | Acceso directo a `self.process_service` en vez de `getattr(self, ...)` en UI | killed | `test_el_gestor_guarda_la_ruta_absoluta falló por AttributeError en vista headless` |

### What
- Optimización de latencia en `ProcessService.get_running_processes`: eliminación de la consulta ansiosa de `exe` en `psutil.process_iter` sobre cientos de procesos vivos (la cual disparaba excepciones internas `AccessDenied` e I/O de tokens en Windows).
- Incorporación del método `get_process_exe_path(pid: int) -> str` en `ProcessService`, con captura defensiva de `(psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, OSError, ValueError)` y retorno seguro de `""` ante PIDs inválidos o sin privilegios.
- Consumo defensivo en `ProcessManagerView.on_add_to_pack`: si `exe_path` no viene precargada, se consulta bajo demanda usando `getattr(self, "process_service", None)` para preservar la compatibilidad con harnesses headless.
- Optimización del bucle caliente de escaneo usando `ProcessInfo.model_construct(...)` (ahorrando ~2.200 validaciones de campo Pydantic por escaneo).
- Precomputación de `_CAT_ORDER_IDX` a nivel de módulo colocada después de la línea 56 para respetar la posición estricta (L33-48) de `SYSTEM_PROTECTED_PROCESSES` exigida por la prueba AST de sincronización documental.
- Normalización estricta de nombres con corte de sufijo (`[:-4]` si termina en `.exe`), evitando corrupciones por reemplazo global.
- Incorporación de la prueba discriminante y benchmark `test_scan_latency_and_lazy_exe_resolution` en `run_tests.py`.
- Actualización de documentación técnica en `docs/ai/architecture.md` (§7) y `docs/ai/testing-guide.md` (suite actualizada a 73 tests).

### Outcome
- Commits:
  - `7eb6c5a` (plan: registrar TASK-033 en tasks.json y openspec)
  - `142fdc1` (feat: optimizar latencia de escaneo y resolucion lazy de exe_path)
- Tests: 72 backend + 1 headless UI PASS (0 fallos).
- Docs: `validate_docs.py` (68 OK, 0 FAIL).

### Impact
Reducción drástica del tiempo de escaneo en frío en Windows 11 de más de ~31 ms a tan solo 5.53 ms (~5.6x a ~8x de aceleración), eliminando lag perceptible en la UI durante el refresco de procesos y lanzamiento de Gaming Mode sin comprometer el blindaje anti-brick ni la separación de capas.

---

## [CYCLE-023] 2026-09-30 20:35 — process-db-expansion
**Área**: Base de Datos & Procesos
**Change**: openspec/changes/2026-09-30-process-db-expansion/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): inherit
- Paso 2 (Planear): architect-review / process-db-updater
- Paso 3 (Ejecutar): process-db-updater & openspec-dev → IMPLEMENTADO
- Paso 4 (Auditar tests): mutation-auditor → VERDICT: PASS (11/11 mutantes eliminados)

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| M1a (Anti-brick) | Inyectar `csrss` cerrable (`Productividad`/`high`) | killed | `test_no_system_process_is_killable detectó proceso crítico closable` |
| M1b (Anti-brick) | Inyectar `lsass` con semáforo no-rojo | killed | `test_no_system_process_is_killable detectó proceso vigilado sin rojo` |
| M2a (Categoría) | Modificar categoría de `braveupdate` a `? Otros` | killed | `test_category_emoji_alignment detectó categoría huérfana` |
| M2b (Categoría) | Modificar categoría de `braveupdate` a `⚪ Otros` (espacio erróneo) | killed | `test_category_emoji_alignment detectó categoría no presente en PROCESS_CATEGORIES` |
| M2c (Categoría) | Glifo alterado `🟩 Productividad` | killed | `test_category_emoji_alignment detectó glifo no alineado con config` |
| M3a (Categoría) | Eliminar `category` de `braveupdate` | killed | `test_category_emoji_alignment / test_process_db_schema_integrity detectó campo faltante` |
| M3b (S1, Prioridad) | Eliminar `priority` de `braveupdate` | killed | `test_process_db_schema_integrity detectó ausencia de campo obligatorio 'priority'` |
| M3c (S1, Descripción) | Eliminar `description` de `braveupdate` | killed | `test_process_db_schema_integrity detectó ausencia de campo obligatorio 'description'` |
| M3d (S1, Prioridad) | `priority: "invalido"` en `braveupdate` | killed | `test_process_db_schema_integrity detectó prioridad fuera de {'high','medium','low','none'}` |
| M-KeyExe (Esquema) | Clave con extensión `.exe` | killed | `test_process_db_schema_integrity detectó clave terminada en .exe` |
| M-DescEmpty (Esquema) | `description: ""` vacía | killed | `test_process_db_schema_integrity detectó descripción vacía` |

### What
- Expansión de `assets/process_db.json` con 8 nuevas entradas reales obtenidas por escaneo con `psutil`: `braveupdate`, `xboxgamebarwidgets`, `xboxpcappft`, `whatsapp.root`, `crossdeviceresume`, `lightingservice`, `powertoys.mousewithoutbordershelper`, `acpowernotification` (total: 81 entradas).
- Blindaje anti-brick estricto: cero colisiones con `SYSTEM_PROTECTED_PROCESSES:33-48`. Procesos de hardware y overlays asignados a `🔴 Overlays e Info` (`priority: "none"`), quedando blindados ante Gaming Mode por la barrera roja G-2.
- Detección y erradicación del mutante superviviente S1: implementación de la sonda `test_process_db_schema_integrity()` en `run_tests.py` (L343) que valida estructura de diccionario, claves normalizadas sin `.exe`, categorías cerradas en `PROCESS_CATEGORIES`, prioridades válidas y descripciones no vacías.
- Actualización de documentación técnica en `docs/ai/data-models.md` y `docs/ai/testing-guide.md` (suite actualizada a 72 tests).

### Outcome
- Commits:
  - `f2adf2b` (plan)
  - `3e24a1e` (feat: expandir process_db.json a 81 entradas)
  - `091386c` (fix: cerrar mutante S1 con test_process_db_schema_integrity)
- Tests: 71 backend + 1 headless UI PASS (0 fallos).
- Docs: `validate_docs.py` (66 OK, 0 FAIL).

### Impact
Ampliación segura y verificada de la base de conocimiento local de procesos de Windows sin alterar contratos arquitectónicos ni runtime de ejecución. La nueva sonda de esquema previene corrupciones y omisiones silenciosas de metadatos en futuros ciclos.

---

## [CYCLE-022] 2026-09-30 20:15 — ui-visual-refresh
**Área**: Diseño & UI / Micro-UX
**Change**: openspec/changes/2026-09-29-ui-visual-refresh/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): inherit
- Paso 2 (Planear): architect-review → VISTO BUENO PARA IMPLEMENTAR (Opción A adoptada)
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO
- Paso 4 (Auditar tests): mutation-auditor → VERDICT: PASS (6/6 mutantes eliminados)

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| UI-002a (Cero hex) | Inyectar `fg_color="#123456"` en vista | killed | `test_no_literal_colors_in_views detectó literal hex suelto vía AST` |
| UI-002b (Tokens) | Modificar `FONT_SIZES` o borrar token | killed | `test_theme_tokens_complete detectó token faltante / tupla de fuentes alterada` |
| UI-010 (WCAG AA) | Degradar `TEXT_MUTED` a `#555555` (< 4.5:1) | killed | `test_contrast_wcag_aa detectó ratio 2.50:1 inferior a 4.5:1` |
| UI-007 (Hit targets) | Reducir botón a `width=20` o `height=24` | killed | `test_hit_targets_minimum detectó botón con dimensión menor a 28x28px` |
| UI-012b (Contrato semántico) | Cambiar `GAMING` a `#c22d2d` o contaminar semáforo | killed | `test_semantic_color_contract detectó violación de paleta Gaming/Peligro` |
| UI-006 (Icono real) | Renombrar o corromper `assets/woptimizer.ico` | killed | `test_woptimizer_ico_exists_and_valid detectó archivo ausente o no-ICO` |

### What
- Sistema centralizado de tokens en `src/woptimizer/ui/theme.py`: roles semánticos de color (`SURFACE`, `ACCENT`, `GAMING`, `DANGER`), escala fija de 6 tamaños y 3 radios, funciones de luminancia y contraste WCAG 2.1 AA.
- Resolución de contradicción de marca: adopción de Opción A (Gaming = verde `#1DB954`, peligro exclusivo rojo `#c22d2d`).
- Icono oficial de aplicación `assets/woptimizer.ico` (multi-tamaño: 16 a 256px), cableado en `app.py` (`root.iconbitmap` y `pystray.Icon`).
- Rediseño de barra de navegación (`main_window.py`): altura fija estricta de 44px (`pack_propagate(False)`), hover, y estado activo unificado en `_set_active_nav` con borde de acento y `text_primary`.
- Portada (`DashboardView`): banda de telemetría permanente en reposo sin `psutil` (`process_service.get_running_processes()`), reetiquetado descriptivo (`N apps · M categorías · KILL`) y reutilización de widgets en `refresh_dashboard`.
- Tarjeta de pack Gaming destacada (`pack_manager_view.py`): borde de acento verde `#1DB954` y badge `PRESET` con contraste WCAG AA 7.24:1 (`theme.SURFACE`).
- Sustitución de `CTkInputDialog` huérfano por `NewPackModal` acoplado al toplevel con `grab_set()` y centrado relativo, sin `messagebox`.
- Objetivos de puntero mínimos garantizados a `28x28px`.
- Cabeceras de categorías con fondo `SURFACE_ALT`, hover `SURFACE_HOVER` y contador explícito `(N)`.
- Responsive: `wraplength=380` en descripciones para ancho mínimo de 720px en pantallas de 14".

### Outcome
- Commits: `16ef4dc (feat)`
- Tests: 63 backend + 1 headless UI PASS (0 fallos).
- Docs: `docs/ai/ui-design-system.md` completamente actualizado como sistema de diseño estructurado.

### Impact
Consolidación completa del sistema visual y la ergonomía del frontend. Cero colores literales hardcodeados en vistas, accesibilidad WCAG AA contrast ratio certificada, separación nítida entre marca Gaming y alertas de peligro, e iconos nativos en ventana y bandeja del sistema.

---

## [CYCLE-021] 2026-09-30 18:00 — task028-debt-cleanup
**Área**: Resiliencia & Robustez / Deuda Técnica
**Change**: openspec/changes/2026-09-30-task028-debt-cleanup/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): inherit
- Paso 2 (Planear): inherit
- Paso 3 (Ejecutar): inherit
- Paso 4 (Auditar tests): inherit → VERDICT: PASS

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| FIX-010 (Logging) | `setup_logging` sin `force=True` | killed | `handlers previos no se limpian y avisos van a stderr` |
| FIX-010 (Destino) | log a stderr en lugar de archivo | killed | `test_logging_va_a_fichero_y_no_a_stderr detectó ausencia de handler de archivo` |
| FIX-018 (Versión) | desincronizar pyproject vs __init__ | killed | `test_la_consulta_de_version_no_puede_desincronizarse falló por discrepancia de strings` |
| F1 (Ilegible) | omitir captura de encoding roto | killed | `control de alcanzabilidad falló al verificar recuperación de backup` |
| Legacy root | omitir mover profiles.json v2 | killed | `test_el_archivo_legacy_esta_versionado_y_no_vuelve_a_la_raiz falló` |

### What
- Saneamiento de deuda técnica y consolidación de la suite: FIX-010 a FIX-020.
- `setup_logging` con `force=True` y rotación de log (`woptimizer.log`, max 1MB, 3 backups) invocado en `__main__` y `run_tests.py`.
- Archivo seguro de perfiles legacy v2 en `docs/archive/legacy-root-data/profiles.json` con su README, sin tocar `test_profiles_task1.json`.
- Eliminación de redundancias en `quit_app()` (`import sys`) y `process_manager_view.py` (`is_expanded = True`).
- Sincronización de versión `3.0.1.dev0` entre `pyproject.toml`, `__init__.py` y `tasks.json` con test AST hermético.
- Cierre de supervivientes de mutación y blindaje de perfiles ilegibles (F1) y protección de datos de usuario.

### Outcome
- Commits: `7a421e8`, `060fcc5`, `22464b9`, `3cc33dc`, `41e42e7`, `e35d30e`
- Tests: 57 backend + 1 headless UI PASS (0 fallos).
- Docs: `docs/ai/architecture.md`, `docs/ai/data-models.md`, `docs/ai/testing-guide.md` actualizados.

### Impact
Se liquidó la deuda técnica acumulada de la migración v2->v3. El log no crece descontrolado y no ensucia la consola, la versión está unificada y no puede desincronizarse, y la configuración legacy está documentada y archivada.

---

## [CYCLE-020] 2026-09-30 - 2026-09-30-ui-hardening
**Área**: Seguridad & Usabilidad
**Change**: openspec/changes/2026-09-30-ui-hardening/
**Estado**: COMPLETED - implementacion + matriz de mutacion propia (27/27 muertas), REVISADO por
`mutation-auditor` (FAIL: 1 hallazgo ALTA + 3 MEDIUM/LOW), ITERACION 2 cerrada con 21/21 muertas e
ITERACION 3 cerrada con 5/5 (hard link + su hermano, la COPIA) y 21/21 re-verificadas
**Models**:
- Implementacion: `openspec-dev`
- Paso 4 (Pendiente): `mutation-auditor` sobre `openspec/changes/2026-09-30-ui-hardening/tasks.md` § 0

### Decisiones de diseno (normativas, de `proposal.md`)
1. **`_resolver_app(entrada, raices=None)` es decision pura; `_lanzar(ruta)` es el efecto.** El orden de las reglas ES la seguridad: vacio/NUL → UNC → nombre pelado solo dentro de raices → `normpath` → contencion → extension → `isfile`.
2. **Sin blacklists de metacaracteres.** `C:\Program Files\Rock & Roll\game.exe` es legitima. Sin interprete no hay metacarácteres que escapar.
3. **No se resuelve con `shutil.which()`**: con `shell=False`, `CreateProcess` busca el CWD antes que el PATH (`isfile("cmd")` → False, `which("cmd")` → `C:\WINDOWS\system32\cmd.EXE`).
4. **La contencion va SIEMPRE despues de `normpath`**: `commonpath([cruda, 'C:\Program Files']) == 'C:\Program Files'` (medido) deja pasar el traversal.
5. **`os.startfile` se resuelve como atributo del MODULO en tiempo de llamada** (`getattr(os, "startfile", None)`), nunca `from os import startfile`: es lo que permite que la sonda muera por la ASERCION y no por un `AttributeError`.
6. **`ordenar_categorias` en `config.py`**, usada por los DOS sitios (por eso no pueden divergir). No se deriva de `get_safety_badge`.

### Desviaciones respecto a la spec (declaradas, no parcheadas en silencio)
- **`proposal.md` § 3.2 (firma literal de `toggle_favorite`) es INCOMPATIBLE con `tasks.md` T-27.4 caso 3.** Con `if pack is not None and pack.is_favorite: ... else: set_favorite(pack_id)`, un id inexistente cae en el `else` y llama `set_favorite("z")`, que en el servicio real **desmarca todos los favoritos y lo persiste**. Se anadio la guarda `if pack is None: return` (mutacion M23 medida). La decision de diseno (leer en vivo, `set_favorite(None)` en la segunda pulsacion, nada de `get_favorite_pack()`) se mantiene literal.
- **`tasks.md` T-27.1 caso (a) usa `r"C:\Windows\notepad.exe & del /q C:\"`, que no es Python valido** (una cadena cruda no puede acabar en backslash). Se escribio con el separador doblado.
- **El `Popen` sembrado lanza `BaseException`, no `AssertionError`**, porque el codigo viejo lo captura con `except Exception`: con `AssertionError` la reintroduccion de `shell=True` contaria `failed` y pasaria en VERDE.
- **El encargo no declaraba el segundo sitio de FIX-004** (`pack_manager_view._render_pack_card`), que es donde el usuario configura que se mata. Arreglados los dos.
- **El encargo no pedia la lista blanca de extensiones** (`.bat`/`.ps1`/`.vbs`/`.lnk` via `ShellExecute`), que es la pieza que hace aceptable `os.startfile` frente a `Popen(shell=True)`.

### Ficheros tocados
`src/woptimizer/services/process_service.py`, `src/woptimizer/config.py`,
`src/woptimizer/ui/views/process_manager_view.py`,
`src/woptimizer/ui/views/pack_manager_view.py`, `run_tests.py`,
`docs/ai/architecture.md` (§ 14 nuevo), `docs/ai/ui-design-system.md`,
`docs/ai/data-models.md`, `docs/known-issues.md` (Trampa #16), `CHANGELOG.md`,
`.taskmaster/CHANGELOG.md`.

### Mutaciones medidas (subproceso POR SONDA)
27 mutaciones, **27 muertas**, 0 supervivientes. Las 9 de la tabla de T-27.1
mueren en la asercion que nombra la spec; las 4 de T-27.2 en el caso 1/2/3; las
4 de T-27.3 (identidad, `sorted`, centinela, guarda estatica de los dos sitios);
las 4 de T-27.4 (incondicional, instantanea, `get_favorite_pack()`, id
inexistente). Detalle en el informe del dev.

### ITERACION 2 — el `mutation-auditor` dio FAIL (4 hallazgos, 1 ALTA)

**El hallazgo grave no era un fallo de codigo sino una garantia documentada que era FALSA.**
`architecture.md` §14 decia "solo se arranca lo que esta bajo las raices permitidas", y un
junction de un comando colado en `%LOCALAPPDATA%` la incumplia. El alias
`commonpath([<TEMP>\\jdir\\cmd.exe, LOCALAPPDATA])` devuelve `LOCALAPPDATA`: "contiene". Y
`os.stat(...).st_file_attributes` tampoco lo ve (`0x20`, medido) porque sigue el enlace en el
tramo intermedio.

**Arreglo: regla 8 nueva en `_resolver_app`** — resolver la ruta real (fail-closed) y repetir
contained + extension sobre ella; devolver la ruta REAL. Decisiones:
- **`os.path.realpath(ruta, strict=True)`, SIN `ctypes`.** El encargo ofrecia
  `GetFinalPathNameByHandle` por `ctypes` o `st_file_attributes`; la medicion descarta las dos: el
  atributo no ve el enlace intermedio, y `ntpath.realpath` **ya es** el envoltorio de
  `GetFinalPathNameByHandleW` (resultado medido, tambien con enlace de fichero). Menos codigo,
  mismo resultado, y la separacion de capas no se mueve: sigue siendo `services/` la que habla
  con el SO, y la UI sigue sin importar nada nuevo.
- **Extension en el alias Y en el destino.** `.exe` -> enlace a un `.bat` **de una raiz
  permitida** pasaba la contencion real y esquivaba la lista blanca entera (`ShellExecute` ->
  `cmd.exe /c`). Este agujero NO venia en el encargo y es de la misma familia.
- **Las raices se resuelven tambien.** Con la raiz lexica, un junction en un tramo de
  `%LOCALAPPDATA%` rechazaria apps legitimas: el falso negativo. Sin sonda para esto, el arreglo
  del "siempre" se colaba por el otro lado.
- **Se devuelve la ruta real, no la escrita**: lo que se valida es lo que se arranca.
- **M10 (contencion por prefijo)**: sonda nueva con hermano real + ficheros reales.
- **Guarda anti-`shell=True`**: era CIEGA a `ast.Attribute` —`subprocess.Popen(app, shell=True)`,
  la grafia EXACTA del bug original, pasaba. Ampliada a atributo + mapa de alias de `ImportFrom`,
  y `shell` ya no exige `is True` (cualquier valor que no sea literal falso es interprete).
  Extraida a `_hallazgos_shell_true(fuente, etiqueta)`, usada por las DOS sondas: dos guarditas
  con coberturas distintas son cero guardas. La sonda nueva exige tambien los falsos positivos
  que NO deben marcarse.
- **Mayusculas: `os.path.normcase` en los dos lados, y NO se documenta como limitacion.**
  `normcase` no ensancha el conjunto aceptado: declara la verdad del SO, asi que lo que entra es
  exactamente lo que el SO abriria, y encima siguen aplicando la contencion y la extension
  REALES. No sustituye a `commonpath` (el hermano de prefijo entraria igual), por eso M10 tiene
  sonda propia. La sonda prueba las DOS direcciones: con `normcase` solo en un lado, la mitad
  de los casos sigue fallando.

**Ficheros tocados (iter 2)**: `src/woptimizer/services/process_service.py`, `run_tests.py`,
`docs/ai/architecture.md` (§14, garantia corregida), `docs/ai/testing-guide.md` (56 tests + tabla
de sondas), `docs/known-issues.md` (Trampa #17), `openspec/changes/2026-09-30-ui-hardening/tasks.md`
(§1b), `CHANGELOG.md`, `.taskmaster/CHANGELOG.md`, `_mutmatrix_t027_iter2.py` (nuevo, la sonda
ejecutable de la matriz).

**Mutaciones medidas (iter 2, subproceso POR SONDA)**: `_mutmatrix_t027_iter2.py` copia `src/` a
`%TEMP%` por mutacion, muta el **producto** y lanza **una sonda por subproceso**.
**21 mutaciones, 21 muertas, 0 supervivientes.** A1-A10 (junction: borrar la resolucion real,
contencion real siempre True, extension solo en el alias, `realpath` sin `strict`, rechazar todo
reparse point, devolver la ruta lexica, fail-open, raices lexicas, sin motivo en el log,
comparar la lexica contra las raices reales), M10 (`startswith`), C1-C3 (`normcase`), G1-G4 (la
guarda) y P1/P2 (reintroducir `Popen(..., shell=True)` en el producto). Hay ademas 4 **cruces
informativos** en la salida, con su motivo: una mutacion tiene que morir en la sonda que DECLARA
esa propiedad, y ninguno de esos pares es un agujero porque cada propiedad si muere en su propia
sonda.

**Deuda declarada en la iteracion 2, CERRADA en la iteracion 3 (y la DEUDA ESTABA MAL FUNDADA).**
La iteracion 2 decio, aqui, en el modulo, en `architecture.md` §14 y en `known-issues.md` (Trampa #17),
que un **hard link** (`mklink /H`) "no es un reparse point, asi que ni `realpath` ni los atributos lo
ven" y que "no es arreglable con esta regla y no hace falta". **Las dos mitades de esa razon eran
falsas**, y el hallazgo del `mutation-auditor` de la iteracion 3 es que el caso **era** cerrable:

* **"Ningun filtro de Windows lo ve" es FALSO**: `os.stat(ruta).st_nlink` vale **2** en un hard link
  (medido). Si lo ve.
* **Y da igual que lo vea, porque el hard link NO era el agujero.** Medido en esta maquina con las dos
  variantes construidas de verdad: `_resolver_app` acepta el hard link (`alias.exe` -> `payload.bat`
  fuera de las raices, `st_nlink == 2`) **y tambien una COPIA PLENA** del mismo `.bat` con nombre
  `.exe` (`st_nlink == 1`, sin un solo enlace, sin junction, sin symlink y sin privilegios). Cerrar
  solo el caso exotico habria sido seguridad de teatro: el trivial seguia abierto.
* **La variante que se ofrecio como alternativa ("rechazar solo si el destino no esta en las
  raices") NO ES IMPLEMENTABLE**: un hard link no tiene destino consultable (no hay API en Windows
  que devuelva los otros nombres de un fichero a partir de su ruta), y aunque la hubiera seria
  irrelevante, porque el atacante elige que nombre queda dentro de la raiz.
* **Y `st_nlink > 1` a pelo es un error, medido**: de **2273** `.exe`/`.com` instalados en las seis
  raices, **189 (8,32 %) tienen `st_nlink > 1`** (hasta 6), y son programas de Microsoft
  (`msinfo32.exe`, `TabTip.exe`, los auxiliares de Edge, las herramientas de Hyper-V). Rechazar
  "cualquier `st_nlink > 1`" habria roto el 8 % del software instalado. Por eso NO se ha hecho, y el
  control (6) de la sonda nueva lo prohibe explicitamente.

**El cierre es la REGLA 9 (`_es_imagen_pe`): el CONTENIDO, no el nombre.** La lista blanca de
`.exe`/`.com` siempre quiso expresar que *`.exe` significa "imagen PE", no "algo que se arranca"*, pero
se cumplia mirando el NOMBRE, y un hard link (o una copia) tiene el nombre que le pongas. La regla 9
comprueba que el fichero lleva `MZ` y la firma `PE\0\0` en el offset que declara `e_lfanew`, DESPUES de
la resolucion real, sobre el fichero que se va a arrancar de verdad. **Coste medido antes de escribirla**:
2200 de 2273 `.exe`/`.com` instalados la cumplen y **ninguno de los 189 multi-enlazados falla** (0 falsos
negativos en justo el caso que se queria cerrar); los 19 que no son appx de WindowsApps, la cache de MSI
y un `.COM` DOS de 16 bits, ninguno lanzable. Fail-closed.

**Mutaciones medidas (iter 3, subproceso POR SONDA)**: `_mutmatrix_t027_iter3.py`, **5 mutaciones, 5
muertas, 0 supervivientes** (H1 borrar la regla 9, H2 la regla que no hace nada, H3 solo `MZ`, H4
fail-open al no leer, H5 rechazar cualquier `st_nlink > 1`). Sonda:
`test_un_hard_link_no_es_una_hoja_y_el_script_no_pasa`, con **hard link real** (`os.link`, sin
privilegios) y que **falla en voz alta** si el entorno no deja construirlo.

**Y un hallazgo propio sobre las sondas, que es lo importante de este pase**: al anadir la regla 9, los
fixtures que hacian de "una app" eran ficheros **VACIOS**, y un `.exe` vacio no es un PE, asi que la
regla nueva los rechazaba **por el motivo equivocado**. Dos propiedades dejaron de estar probadas sin
que ninguna sonda se quejara: la extension real (mutacion **A3**) y la lista blanca (caso (b)). Se
detecto porque se **re-ejecuto la matriz de la iteracion 2** (no porque la suite se rompiera: la suite
estaba en verde). Corregido con el helper `_escribir_pe_minimo` y con el caso (b) ampliado: el **mismo
contenido** con `.bat` no arranca y con `.exe` si, de modo que la diferencia la tiene que hacer la
extension y no el contenido. La matriz de la iteracion 2 queda **21/21 muertas, 0 supervivientes**,
re-verificada; la de la iteracion 3 es **5/5**.

**Correccion de una afirmacion previa de este mismo changelog**: la iteracion 1 declaraba "27
mutaciones, 27 muertas" y el `mutation-auditor` midio **29 mutaciones, 28 muertas** (el
superviviente era M10, la contencion por prefijo, cerrada aqui). El numero de 27 estaba mal y
esta corregido en el sitio. Y la iteracion 2 daba por cerrada una deuda cuya **razon era falsa**: una
afirmacion de seguridad que no se sostiene no es una deuda declarada, es una garantia mal escrita.

**Nota de entorno**: los 19 directorios `wopt_mut_*` de `%TEMP%` que hay en esta maquina son de
un pase anterior (layout plano, `pack_service.py` en la raiz), no de este. Este pase no deja
residuos: ni en `%TEMP%` ni en `%USERPROFILE%`.

### Pendiente para el Paso 4
`mutation-auditor` debe repetir las 9 mutaciones de T-27.1 sobre una copia de
`src/`. Nota: si se cambia `os.startfile` por `subprocess.Popen([ruta], shell=False)`,
la lista blanca de extensiones se vuelve innecesaria **y el caso (b) debe volver a morir**.

# Changelog de pases — Motor id-pipeline

> **Registro append-only de cada ciclo completado por el motor autónomo de I+D.**
> Una entrada por pase al final del Paso 3 (Ejecutar), antes del retorno al Paso 1.
> **MANDATORY** desde el ciclo #11 (proposal `2026-09-29-id-pipeline-changelog-models`).

## Fuentes relacionadas

| Artefacto | Para qué |
|---|---|
| `.taskmaster/CHANGELOG.md` (este archivo) | Per-pass humano-legible: qué se hizo, con qué modelos, qué salió. |
| `.taskmaster/rd_journal.json` | Machine-readable: datos estructurados por ciclo (incluye `task`, `commits`, `benchmark_*`). |
| [`STATUS.md`](../../STATUS.md) | Dashboard: salud del sistema + resumen de hitos (no cada pase). |
| `openspec/changes/<id>/` | Contrato de cada cambio y su evolución. |

## Convención de modelos (definida en Sección 7 de `id-pipeline/SKILL.md`)

Modelos disponibles: `flash` (rápido, tareas triviales), `inherit` (default seguro, balance), `pro` (máxima capacidad de razonamiento, planificación compleja).

| Paso | Modelo por defecto | Override |
|---|---|---|
| 1. Buscar | `flash` | `inherit` si la búsqueda requiere contexto quirúrgico. |
| 2. Planear | `pro` | `inherit` si el cambio es trivial o el área es bien conocida. |
| 3. Ejecutar | `inherit` | `pro` para refactors con riesgo de regresión. |

## Formato de cada entrada

```markdown
## [CYCLE-NNN] YYYY-MM-DD HH:MM — <slug>
**Área**: <de la matriz de rotación>
**Change**: openspec/changes/<slug>/
**Estado**: COMPLETED | BLOCKED | ROLLED-BACK
**Models**:
- Paso 1 (Buscar): <modelo>
- Paso 2 (Planear): <modelo>
- Paso 3 (Ejecutar): <modelo>

### What
- <bullets cortos concretos, 1 frase cada uno>

### Outcome
- Commits: `<hash1>`, `<hash2>`
- Tests: <n>/<total> PASS
- Docs: <qué docs/ai/ se actualizó>

### Impact
<1-2 frases>
```

---

## Entradas

> Nota: ciclos 1-10 fueron completados ANTES de la convención de changelog. Se backfillean abajo usando los datos de `rd_journal.json`. Los modelos aparecen como `inherit (legacy — sin tracking)` por no estar registrados históricamente.

## [CYCLE-001] 2026-09-28 23:00 — 2026-09-28-v3-ui-redesign
**Área**: Arquitectura & UI
**Change**: openspec/changes/2026-09-28-v3-ui-redesign/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `inherit (legacy — sin tracking)`
- Paso 3 (Ejecutar): `inherit (legacy — sin tracking)`

### What
- Rediseño completo de 3 ventanas con CustomTkinter (Portada, Packs, Procesos).
- Migración de backend de PowerShell/WMI a `psutil`.
- Modelos de persistencia migrados a `pydantic v2`.

### Outcome
- Commits: (no registrados en journal)
- Tests: N/A en este ciclo (fue el kick-off del v3)
- Docs: arquitectura y UI redesign pendientes de documentar en docs/ai/.

### Impact
Sentó las bases de toda la v3. Cualquier cambio posterior parte de esta estructura. Sin este ciclo no existiría el resto.

---

## [CYCLE-002] 2026-09-29 01:35 — 2026-09-29-v3.1-quality-of-life
**Área**: Resiliencia & UX
**Change**: openspec/changes/2026-09-29-v3.1-quality-of-life/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `inherit (legacy — sin tracking)`
- Paso 3 (Ejecutar): `inherit (legacy — sin tracking)`

### What
- Integración de System Tray (`pystray`) en background.
- Rotación segura de backups `profiles.json.bak`.
- Logging continuo en `woptimizer.log`.

### Outcome
- Commits: (no registrados en journal)
- Tests: N/A en este ciclo
- Docs: quality-of-life no documentado en docs/ai/ (pendiente).

### Impact
Mejoró la resiliencia operacional: el usuario puede minimizar a tray, los profiles tienen recovery ante corrupción, y hay rastro de auditoría continua.

---

## [CYCLE-003] 2026-09-29 02:12 — 2026-09-29-ram-telemetry-widget
**Área**: Gaming & Telemetría UX
**Change**: openspec/changes/2026-09-29-ram-telemetry-widget/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `inherit (legacy — sin tracking)`
- Paso 3 (Ejecutar): `inherit (legacy — sin tracking)`

### What
- Banner dinámico de telemetría en `DashboardView` que muestra procesos cerrados y MB liberados tras activar packs.
- Implementación thread-safe vía `self.after(0, ...)`.
- Auto-hide a los 5s.
- Paleta: verde gaming (`#1DB954`) vs azul kill (`#4a9fd4`).

### Outcome
- Commits: `617eef8` (architect), `dc7c30c` (feat)
- Tests: N/A en este ciclo
- Docs: ui-design-system.md pendiente de actualizar con banner spec.

### Impact
El usuario ve feedback inmediato del impacto de activar un pack — clave para adopción y para entender qué mató el botón "Gaming".

---

## [CYCLE-004] 2026-09-29 02:18 — 2026-09-29-process-db-update
**Área**: Base de Datos & Procesos
**Change**: openspec/changes/2026-09-29-process-db-update/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `inherit (legacy — sin tracking)`
- Paso 3 (Ejecutar): `flash` (DB updates rutinarios — según tabla de la skill)

### What
- 4 procesos nuevos en `assets/process_db.json`: `sharex`, `crossdeviceservice`, `esrv_svc`, `dsaservice`.
- Todos marcados como `🔴 high` (bloatware/telemetría seguros de cerrar en gaming).

### Outcome
- Commits: `c362eda`
- Tests: no ejecutados (cambio de datos, no lógica)
- Docs: process_db.json mismo es la doc; no requiere docs/ai/ update.

### Impact
34 procesos catalogados total. Cobertura incremental sobre apps comunes de telemetría y captura.

---

## [CYCLE-005] 2026-09-29 02:21 — 2026-09-29-testing-quality
**Área**: Testing & Calidad
**Change**: openspec/changes/2026-09-29-testing-quality/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `inherit (legacy — sin tracking)`
- Paso 3 (Ejecutar): `inherit (legacy — sin tracking)`

### What
- 3 tests nuevos en `run_tests.py` (total 7): `freed_mb` return type, gaming pack protected, corrupted JSON recovery.

### Outcome
- Commits: `786a551`
- Tests: 7/7 PASS
- Docs: `docs/ai/testing-guide.md` actualizado con los 3 nuevos tests.

### Impact
Cobertura base de invariantes críticas: tipado de retorno, protección del pack gaming, recovery ante JSON corrupto. Las 3 son trampas documentadas en `docs/known-issues.md`.

---

## [CYCLE-006] 2026-09-29 02:23 — 2026-09-29-resilience-tray-logging
**Área**: Resiliencia & Robustez
**Change**: openspec/changes/2026-09-29-resilience-tray-logging/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `inherit (legacy — sin tracking)`
- Paso 3 (Ejecutar): `inherit (legacy — sin tracking)`

### What
- Fix: `tray_icon` no se guardaba en `self`, lo que impedía el cierre limpio del tray.
- `gaming_action` ahora con `try/except` + logging.
- `start_pack_apps` con `logger.info/warning` individual por app.

### Outcome
- Commits: `60c713d`
- Tests: pasan los 7 existentes (no se añadieron nuevos en este ciclo)
- Docs: ninguna doc nueva (cambios menores de robustez).

### Impact
Bug latente de cleanup de tray corregido. Sin el fix, al cerrar la app podía dejar el icono del system tray huérfano.

---

## [CYCLE-007] 2026-09-29 02:27 — 2026-09-29-perf-cache-hashmap
**Área**: Rendimiento & Latencia
**Change**: openspec/changes/2026-09-29-perf-cache-hashmap/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `pro` (refactor con riesgo de regresión)
- Paso 3 (Ejecutar): `pro` (refactor con riesgo de regresión)

### What
- Rewrite de `ProcessService`: hashmap O(1) para lookup de DB.
- Meta-cache memoizado (129 entries).
- Cache TTL 2s para `get_running_processes`.
- Kill invalida cache.

### Outcome
- Commits: `2fc51c3`
- Tests: pasan los 7 existentes
- Benchmark before: cold_scan 16ms, cached N/A.
- Benchmark after: cold_scan 15ms, cached 0.003ms, **~5000x speedup**.

### Impact
La lectura cacheada es prácticamente gratuita. Sin esto, abrir el Gestor de Procesos era la operación más cara de la app.

---

## [CYCLE-008] 2026-09-29 02:41 — 2026-09-29-native-toast-notifications
**Área**: Gaming & Telemetría UX
**Change**: openspec/changes/2026-09-29-native-toast-notifications/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `pro` (nueva service, requiere diseño)
- Paso 3 (Ejecutar): `inherit`

### What
- `NotificationService` nuevo que envuelve `pystray.Icon.notify` sin dependencias nuevas.
- Inyectado en `MainWindow` + 3 vistas.
- Autostart del tray en `__init__` con guard idempotente.
- 4 tests headless nuevos.
- Fix colateral: `pystray` y `Pillow` declarados en `pyproject.toml` (faltaban, rompían builds PyInstaller).

### Outcome
- Commits: `283bc16` (architect), `4797d6a` (feat)
- Tests: 5 → 9 backend, 0 fallos
- Docs: ui-design-system.md pendiente de extender con la spec de notificaciones.

### Impact
Notificaciones nativas Windows al activar packs. Bug colateral resuelto: builds PyInstaller habrían fallado sin declarar `pystray` + `Pillow` en `pyproject.toml`.

---

## [CYCLE-009] 2026-09-29 02:58 — 2026-09-29-config-category-emoji-alignment
**Área**: Base de Datos y Procesos
**Change**: openspec/changes/2026-09-29-config-category-emoji-alignment/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `pro` (debugging de bug crítico)
- Paso 3 (Ejecutar): `inherit`

### What
- **BUG CRÍTICO**: 6 de 8 categorías de `process_db.json` no existían en `config.py` por emojis invertidos, dejando todos esos procesos en `? Otros` sin semáforo.
- **Segundo bug**: `get_safety_badge` evaluaba `priority` antes que `category`, pintando 🟢 como 🔴.
- Fix de ambos + 2 tests de regresión.
- 14 procesos nuevos (navegadores, launchers, herramientas de IA) = 48 total.

### Outcome
- Commits: `31906e7` (process-db), `4977b00` (fix config)
- Tests: 9 → 11 backend, 0 fallos
- Docs: docs/known-issues.md ahora con Trampa #17 (emoji drift) + Trampa #18 (priority vs category ordering).

### Impact
6 categorías que parecían activas estaban completamente huérfanas. Bug invisible: el usuario veía categorías pero las apps caían en "Otros". Las pruebas de regresión ahora blindan contra ambos bugs.

---

## [CYCLE-010] 2026-09-29 02:52 — 2026-09-29-critical-invariant-coverage
**Área**: Testing y Calidad
**Change**: openspec/changes/2026-09-29-critical-invariant-coverage/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `pro` (caza de bugs latentes)
- Paso 3 (Ejecutar): `pro` (fix de invariante crítico)

### What
- **BUG REAL CORREGIDO**: `model_copy()` de Pydantic v2 es shallow, así que las listas del pack Gaming se compartían con `DEFAULT_GAMING_PACK`. La UI mutaba in-situ (`on_add_to_pack`), contaminando el global y haciendo que `reset_gaming_pack()` fuera un no-op silencioso.
- Fix: `model_copy(deep=True)`.
- Test verificado que DISCRIMINA (falla sin el fix).
- 8 tests nuevos para invariantes sin cobertura tras la migración v2→v3: `GamingService.should_kill_for_gaming`, `PackService` CRUD, cache TTL, kill recursivo.
- Hallazgo: los 11 `test_*.py` de la raíz están muertos (importan `process_manager` de v2). Documentados como deuda, NO borrados.

### Outcome
- Commits: `705e5f9` (tests), `1a0faa9` (fix)
- Tests: 11 → 19 backend + 1 headless, 0 fallos
- Docs: docs/known-issues.md ahora con Trampa #19 (Pydantic model_copy shallow).

### Impact
Bug latente invisible durante meses corregido. El usuario podría añadir apps al Gaming pack, cerrar la app, reabrir, y pensar que se habían perdido: era el DEFAULT_GAMING_PACK contaminado en memoria.

---

## [CYCLE-011] 2026-09-29 09:50 - 2026-09-29-git-tooling-resilience
**Área**: Resiliencia & Robustez (matriz área 1, sin tocar desde el ciclo #6)
**Change**: openspec/changes/2026-09-29-git-tooling-resilience/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit` (el modelo de la sesión; la matriz pide `flash`, se subió porque la búsqueda fue de código real, no un lookup)
- Paso 2 (Planear): `inherit` (subagente `worker` + skill architect-review; la matriz pedía `pro`, se quedó en `inherit` porque el subagente no resolvió modelo explícito)
- Paso 3 (Ejecutar): `inherit` (subagente `worker` + skill openspec-dev; coherente con la matriz)

### What
- **Fallo de integridad del pipeline, no de la app**: `git_safe_commit.py` —la unica puerta de versionado y la que AGENTS.md obliga a usar en cada cierre— capturaba CUALQUIER fallo de commit, imprimia `AVISO GIT` y salia con **codigo 0**. El pipeline lo leia como exito y el CHANGELOG (MANDATORY) registraba hashes que podian no existir.
- Ademas `git add -A` fallido era solo un warning (staging parcial silencioso) y `get_env()` activaba el repo desacoplado con un simple `os.path.exists`, sin validarlo.
- **Evidencia de que no era hipotetico**: el `.git` del arbol de trabajo esta corrupto por el VFS de Nextcloud (`fatal: bad object HEAD`); el historial solo sobrevive por el repo desacoplado en LOCALAPPDATA.
- Rehecho: contrato de 4 codigos de salida (`0/1/2/3`) con lineas canonicas `WOPT_*`, validacion real del repo (`validar_repo`), sin fallback al `.git` corrupto, y flag `--verify` de solo lectura.
- **El arquitecto corrigio 3 errores de la propuesta original**, el mas grave: decidir "nada que comitear" buscando `"nothing to commit"` en stderr depende de `LANG`/`LC_ALL` y en un Windows en espanol NO aparece nunca, lo que habria convertido un arbol limpio en un fallo. Ahora se decide con `git diff --cached --quiet` (locale-independiente).
- Tambien cerro un agujero en la linea 55: un `status --porcelain` fallido se trataba como "hay cambios" en vez de como error.
- Checkpoint de empaquetado (3 ciclos desde el #8): `force_build.py` OK, `dist/woptimizer.exe` regenerado (25.65 MB) ya con los fixes de los ciclos #9 y #10.
- Recuperados 5 ficheros modificados + 2 sin seguimiento que el ciclo #10 dejo sin comitear: precisamente porque el wrapper reportaba exito en falso.

### Outcome
- Commits: `6048f6f` (architect), `b9a31fa` (fix)
- Tests: 20 -> 21 (`run_tests.py`), 0 fallos; las 3 puertas en `rc=0` (`verify_ui_syntax.py`, `run_tests.py`, `validate_docs.py` 34 OK)
- Docs: `docs/ai/sandbox-rules.md` (seccion NUEVA "Aislamiento Git en Entornos Cloud (VFS)"), `AGENTS.md` §3, `docs/ai/architecture.md` linea 39
- **Verificacion independiente del orquestador**: los 5 comportamientos del contrato comprobados en vivo (repo sano=0, GIT_DIR inexistente=3, directorio no-repo=3, sin args=2, arbol limpio=0 con `WOPT_NOOP`), y **prueba de mutacion propia**: revirtiendo el fix el test falla con `AssertionError: ... debe salir con 3, salio con 0`, con restauracion byte-identica (SHA256 `C248F694...`).

### Impact
El pipeline deja de poder "completar" ciclos sin versionar nada. Antes, un fallo de commit era indistinguible de un commit correcto para todo el sistema; ahora es un `!= 0` que detiene el ciclo. Defecto de clase: un wrapper de seguridad que miente en su codigo de salida desactiva todas las validaciones que dependen de el (`validate_docs.py` nunca habria podido detectar un hash fantasma).

---

## [CYCLE-012] 2026-09-29 10:30 - 2026-09-29-double-tap-confirmation
**Área**: Gaming & Telemetría UX (matriz área 2, sin tocar desde el ciclo #8)
**Change**: openspec/changes/2026-09-29-double-tap-confirmation/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit`
- Paso 2 (Planear): `inherit` (subagente `worker` + skill architect-review)
- Paso 3 (Ejecutar): `inherit` (subagente `worker` + skill openspec-dev)

### What
- **REGRESION SILENCIOSA DE LA REESCRITURA v2->v3**: la v2 tenia doble pulsacion para confirmar acciones destructivas, introducida tras un incidente real (un `messagebox.askyesno` se abria POR DETRAS de la ventana, el usuario pulsaba, no veia nada y reporto "se ha roto, no mata procesos"). El patron se perdio al reescribir: grep de `messagebox|askyesno|showinfo|showwarning|_request_confirm|confirm` sobre `src/` daba **cero coincidencias**. 5 acciones destructivas-operaban sin confirmar nada.
- La mas grave: **"Cerrar Seleccionados" mata N procesos a pelo** con un solo clic; y en la portada, `refresh_dashboard` coloca los favoritos **de dos en dos** en la misma fila, asi que el boton Gaming tenia un pack vecino pegado y un dedo gordo podia matar los procesos del pack equivocado.
- Segundo fallo: `PackManagerView` **no tenia `status_label`**, o sea que sus acciones no podian dar feedback inline. Se creo.
- Implementado en **un solo sitio**: `ui/confirmation.py` con dos capas — `DoubleTapGuard` (maquina de estado pura, sin `customtkinter`, con `scheduler` inyectable, testeable headless) y `Confirmable` (mixin fino que solo toca widgets).
- Auto-revert a los ~3 s, invalidacion si cambia la seleccion entre pulsaciones, y `destroy()` en las 3 vistas para matar el `after` vivo.
- `on_kill_selected` dejo de hacer `return` mudo sin seleccion (el usuario iba a pensar que el boton estaba roto).
- Documentada la **Trampa #14** en `docs/known-issues.md`, que cierra la laguna #13 -> #14: el porque del patron ya no se pierde en la proxima reescritura.
- **El arquitecto encontro 3 errores CRITICOS en la propuesta, y 6 mas**: el boton de la portada no se llamaba "Modo Gaming" (era `f"{pack.name}\\n(...)"` y ademas *arranca* apps si la accion no es `kill`, asi que confirmar a ciegas habria metido confirmacion en acciones de arranque); el `except ValueError: pass` era **inalcanzable** desde la UI y el fallo silencioso real era que se ignoraba el retorno `False`; y `PackManagerView` no tenia `status_label`. Ademas: congelar los `ProcessInfo` habria sido un fallo de seguridad (los PIDs se reciclan en 3 s), y habia "4 vistas" cuando son 3.

### Outcome
- Commits: `fcd4f73` (architect), `30c0f11` (fix)
- Tests: 21 -> 22 (`run_tests.py`), 0 fallos; gates: `verify_ui_syntax.py` EXITO (8/8, incluido el modulo nuevo), `run_tests.py` ALL TESTS PASSED, `validate_docs.py` 35 OK / 0 FAIL
- Docs: `docs/known-issues.md` (Trampa #14), `docs/ai/ui-design-system.md` (seccion nueva), `verify_ui_syntax.py` (el helper nuevo estaba en su lista fija, si no daba verde en falso)
- **Verificacion independiente del orquestador**: commit y arbol limpios, cero `messagebox` en `src/`, Trampa #14 en la linea 282, y **prueba de mutacion propia**: anulando `arm()` el test revienta con `AssertionError` y `rc=1`, con restauracion byte-identica (SHA256 `3BAE03FB...`).
- Criterio de aceptacion corregido: "cero `confirm` en `src/`" era imposible de cumplir (el modulo se llama `confirmation.py`); acotado al grep real `messagebox|askyesno|showinfo|showwarning`.

### Impact
Se recupera una proteccion que el usuario pidio expresamente y que la reescritura borro sin dejar rastro. El patron es ahora una norma documentada con su porque, asi que la siguiente reescritura ya no lo pierde. Y el riesgo mayor que se cierra es el peor de todos en esta app: matar por error los procesos equivocados, sin aviso y sin vuelta atras.

---

## [CYCLE-013] 2026-09-29 11:00 - 2026-09-29-real-bloatware-scan
**Área**: Base de Datos & Procesos (matriz área 3)
**Change**: openspec/changes/2026-09-29-real-bloatware-scan/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit` (escaneo real con psutil, no un lookup)
- Paso 2 (Planear): `inherit` (la propuesta se auto-revisó durante la ejecución)
- Paso 3 (Ejecutar): `flash` (subagente `worker` + skill process-db-updater: escaneo + append a JSON, sin creatividad)

### What
- **Escaneo real**: 131 nombres de proceso únicos en el sistema, 48 registrados, **122 sin registrar**. Se clasificaron en tres familias con consecuencias opuestas, y confundirlas es el peor defecto posible en esta app.
- **Familia A (procesos de sistema)**: NO se registró ninguno. Matar `csrss`, `lsass` o `winlogon` deja Windows inservible.
- **Familia B (bloatware real)**: **25 entradas añadidas** (48 → 73). PowerToys, el consumo de Armoury Crate de ASUS (telemetría, fondo dinámico, sockets, debug web), language servers, actualizadores, audio enhance y varios servicios de terceros.
- **BLINDAJE ANTI-BRICK** (la mitad del trabajo): `SYSTEM_PROTECTED_PROCESSES` con 34 nombres de nivel sistema, coincidencia **exacta** sobre el nombre normalizado —nunca por subcadena, que bloquearía procesos legítimos—, aplicado en **tres puntos y por las tres vías**: saneado al cargar la DB (también protege contra `load_db_async()`, que descarga el JSON de GitLab por encima), en `_get_process_meta()` **antes** que la DB y que el fuzzy match, y en `kill_processes()` / `kill_pack_apps()`, porque el pack lo escribe el usuario a mano: un `lsass.exe` en un pack se cuenta como `skipped` y no mata nada.
- **Desviaciones deliberadas del subagente respecto a la propuesta, todas a mejor**:
  - Servicios de audio (`atkexcomsvc`, `dtsapo4service`) a **🟡 medium** en vez de 🟢 high: tocan la ruta de audio y un verde prometería audio espacial durante la partida. Además 🟡 Media no está en las `target_categories` del pack gaming, así que nunca se auto-cierran.
  - La pila de control de Armoury Crate (`armourycrate`, `armsvc`, `asus_framework`, ...) a **🔴 none** en vez de verde: es el equivalente a `icue`/`razer`/`lghub`, que en esta misma base ya están en 🔴 por perfiles de ventilación y RGB. Cerrarlos deja el equipo sin perfil de juego. Los 4 de consumo sí van en verde, que es donde está el bloatware real.
  - `mpdefendercoreservice` a 🔴 none: el proposal lo listaba como utilidad de terceros, pero el nombre es la plataforma Defender.
  - Descartados 9: `keepassxc` (matarlo con la base sin cifrar en disco la puede corromper), `lightingservice`/`telemetry_agent`/`nodoze-1.1` (origen no verificable: la descripción habría sido inventada), redundantes por fuzzy match, y `calendarapp.gui.win10` (recortado para no pasar de 25).
- **Ambigüedad resuelta**: `sihost` estaba en las listas A y C del proposal a la vez. Se resuelve como **Familia A**: es infraestructura del shell de Windows, no del entorno de trabajo. Es la lectura segura.

### Outcome
- Commit: `0ad23bb`
- Tests: 22 -> 24 (`run_tests.py`), 0 fallos; `verify_ui_syntax.py` EXITO
- Docs: `docs/ai/data-models.md` con la sección de blindaje
- **Verificacion independiente del orquestador**: 73 entradas, 34 nombres protegidos, **0 procesos de sistema registrados como cerrables** y **0 coincidencias exactas** con nombres de sistema. Un "services" que saltó en la primera comprobación resultó ser `riotclientservices` (launcher legítimo, `priority: none`) por la imprecisión de mi propio grep por subcadena, no un fallo.
- El test discrimina: con el blindaje desactivado falla.

### Impact
Se cierra la via por la que la app mas(score Real peligro: no es solo lo que la lista ofrece, sino lo que el usuario puede escribir a mano en un pack. Ademas se documenta el criterio de NO registrar procesos de sistema, que no estaba escrito en ninguna parte y que la proxima expansion de la base iba a reevaluar sin saberlo.


---

## [CYCLE-014] 2026-09-29 20:55 - 2026-09-29-gaming-service-runtime
**Área**: Gaming & Telemetría UX (matriz área 2)
**Change**: openspec/changes/2026-09-29-gaming-service-runtime/
**Estado**: COMPLETED (sin commit: el entorno bloqueó el versionado, ver Outcome)
**Models**:
- Paso 1 (Buscar): `inherit` (el backlog tenía `active_task_id`; la búsqueda fue contrastar el bug contra el código real)
- Paso 2 (Planear): `pro` (override sobre `inherit`: riesgo de regresión de seguridad — una barrera mal puesta permite matar procesos de sistema)
- Paso 3 (Ejecutar): `inherit` (implementación acotada en 7 ficheros, siguiendo una spec ya auditada)

### What
- **Configuración muerta conectada al runtime**: `GamingService.should_kill_for_gaming()` existía y estaba testeado desde el ciclo #10, pero **nunca se invocó en runtime**. Las 3 rutas de Gaming Mode (tray, portada, gestor de packs) llamaban solo a `kill_pack_apps(pack.apps)`, así que `keepers` y `target_categories` eran decorativos: el usuario marcaba qué proteger y qué cerrar, y el motor nunca lo consultaba. Es la promesa central del producto, desconectada.
- **La raíz era más profunda que el briefing**: `MainWindow` guardaba `gaming_service` (`main_window.py:15`) pero **no se lo pasaba a las vistas** (`:55-71`). El campo estaba muerto en dos niveles, no en uno.
- **VECTOR DE BRICK detectado en planificación**: el guard heredado de `bugfix-audit-v3` ("filtrar los que NO estén en `SYSTEM_PROTECTED_PROCESSES`") es insuficiente. `svchost` y `explorer` están en la categoría `🔴 Sistema de Windows` y **no** en el blacklist de nombres, y esa categoría se ofrece como casilla activable en el acordeón del gestor de packs. Marcarla cerraba **todos los `svchost.exe`**: `is_system_protected('svchost')` es `False`, así que el blindaje de nombres no lo detiene. La garantía correcta no es ampliar el blacklist —que exige acordarse de cada nombre nuevo— sino una **barrera de categoría roja** independiente, aplicada dos veces (sobre `target_categories` y sobre la categoría de cada proceso).
- **Segundo fallo silencioso, del mismo tipo**: `should_kill_for_gaming` compara por subcadena y los keepers se guardan como `"discord.exe"`, pero `get_running_processes` quita la extensión del campo `name`. Evaluar con `p.name` habría **desactivado keepers y apps en silencio** (Steam y Discord morirían siendo "keepers"). La suite no lo cubría porque sus aserciones pasan nombres con `.exe`.
- **Implementado**: `execute_gaming_pack()` en `services/` como **única puerta de kill** —delega íntegro en `kill_processes`, no importa `psutil` ni `json`, y por tanto no puede abrir una vía al SO que las otras no tengan—. `force_refresh=True` (la cache TTL de 2 s devuelve procesos obsoletos), y los dos `if not pack.apps: return` que bloqueaban un Gaming Mode configurado solo por categorías.
- **Contrato de UI**: se inyecta `GamingService` en las vistas con fallback defensivo, **no** se añade un método a `ProcessService` (que es el adaptador de `psutil` y no debe conocer el modelo `Pack`). Las 2 rutas de ventana siguen pasando por el `_require_double_tap` existente; el ítem del tray queda documentado como la **única** excepción, porque un `MenuItem` de pystray no es un widget y un diálogo está prohibido por la Trampa #14.

### Outcome
- Tests: **23 -> 24, 0 fallos** (`run_tests.py`); `verify_ui_syntax.py` EXITO (8/8 módulos)
- **Commits: ninguno.** El shell del entorno falló con `spawn EPERM` de forma intermitente (~3 de 12 intentos pasaron) y `git_safe_commit.py` requiere `subprocess`. Los cambios quedan en el árbol sin versionar: `feat: conecta GamingService.execute_gaming_pack a las 3 rutas de Gaming Mode (TASK-025)`.
- Docs: `docs/ai/architecture.md` (regla 11: ruta, contrato y garantías G-1..G-6) y `docs/ai/ui-design-system.md` (excepción del tray)
- **El test discrimina, y está PROBADO por mutación**: un verificador neutralizó las dos barreras G-2 en una copia temporal y el test falló con `Llegaron: ['chrome.exe', 'onedrive.exe', 'svchost.exe']`. No es un test que "devuelve un int": captura la lista que llega a `kill_processes` y asserta sobre su contenido, con precondición explícita que verifica que `svchost` **no** está en el blacklist (si lo estuviera, el test dejaría de distinguir y lo dice).
- Bug real encontrado y corregido durante la validación: `is_system_protected` es un `@staticmethod` de `ProcessService`, no una función de módulo. El `ImportError` del primer `run_tests.py` lo delató.
- Verificación independiente: veredicto **PASS**, sin hallazgos críticos, altos ni medios.

### Impact
El Gaming Mode por fin hace lo que el usuario le configura, y —más importante— la nueva ruta no puede cerrar procesos de sistema aunque el usuario marque la categoría equivocada. La lección reutilizable queda en la spec: **una evaluación por categoría no se puede blindar con un blacklist de nombres**, porque el blacklist depende de que alguien se acuerde de añadir cada nombre nuevo. Aquí la defensa es la categoría, y el blacklist sigue siendo la segunda capa, no la primera.

---

## [CYCLE-015] 2026-09-29 21:40 - 2026-09-29-data-integrity-fixes
**Área**: Resiliencia & Robustez (ejecutada como tarea de backlog, prioridad sobre rotación)
**Change**: openspec/changes/2026-09-29-data-integrity-fixes/
**Estado**: COMPLETED (sin commit: el entorno bloqueó el versionado)
**Models**:
- Paso 1 (Buscar): `inherit` (el backlog tenía la siguiente tarea; no hizo falta descubrimiento)
- Paso 2 (Planear): `pro` (override: los 4 puntos tocaban integridad de datos y concurrencia en Tk)
- Paso 3 (Ejecutar): `inherit` (spec ya auditada, 4 fixes acotados)

### What
- **FIX-007, riesgo máximo**: `process_manager_view._do_load` mutaba `self.processes` y `self.grouped_processes` **desde el hilo secundario**, mientras el hilo principal recorría ese mismo dict en el render → `RuntimeError: dictionary changed size during iteration`, y un set de PIDs desalineado entregado a `on_kill_selected`, que es el camino que mata procesos reales. Además dos `_do_load` solapados dejaban `grouped_processes` desfasado de `processes`. Ahora el hilo **solo calcula** y publica con un único `self.after(0, _apply)`.
  - **La spec heredada era incorrecta**: `bugfix-audit-v3/tasks.md:23` pedía `self.master.after`, que está prohibido (`main_window.py:42-45` destruye la vista en toda navegación; `master` es `content_frame`, que sobrevive).
- **FIX-009, y la premisa de la tarea era FALSA**: no faltaba "añadir un backup". El hallazgo real es mayor: `load()` ante un JSON corrupto **borraba todos los packs y sobrescribía con uno solo-Gaming**, y `except (json.JSONDecodeError, Exception)` es literalmente `except Exception`, así que un `PermissionError` tomaba **la misma ruta destructiva**. Ahora: backup preventivo, recuperación desde `.bak` **antes** de regenerar, `OSError` propagado sin escribir nada, rotación que **no** pisa un backup sano con un principal corrupto, y escritura atómica (`tmp` + `os.replace`).
  - **Documentación que mentía**: `tasks.json` (TASK-011 `completed`), `v3.1-quality-of-life/tasks.md:5` (`[x]`) y `CHANGELOG.md:91` afirmaban que la rotación de backups existía desde el ciclo #2. No existía: `save()` era `open(...,'w')` + `json.dump` pelado. Grep de `.bak|shutil|copy2|os.replace` en `src/` → **cero coincidencias**.
- **FIX-005**: `_DEFAULT_META` usaba la interrogación ASCII (U+003F) donde `config.py` y `models.py` usan el círculo (U+26AA). El efecto llegaba a **3 sitios**, no 1; el peor era un filtro de la UI (`pack_manager_view.py:179`) que comparaba contra el literal equivocado y por tanto **no filtraba nada**. También una aserción de `run_tests.py` (~1483) que era **tautológica**: afirmaba que una categoría no era un literal que ya no existía en el código.
- **FIX-001, redefinido**: `get_gaming_pack()` usaba `model_copy()` shallow, pero la auditoría lo demostró **inalcanzable** — no tiene ningún llamador (todo va por `get_all_packs()`) y `load()` siempre termina en `_ensure_gaming_pack()`. El ciclo #10 ya cerró la vía real. Queda como deuda latente de 1 carácter, arreglada igualmente.

### Outcome
- Tests: **24 -> 28, 0 fallos** (`run_tests.py`); `verify_ui_syntax.py` EXITO (8/8); `validate_docs.py` 42 OK / 0 FAIL
- **Commits: ninguno** (mismo bloqueo de shell que en el ciclo #14)
- Docs: `data-models.md` (§4 contrato de escritura, §5 literal canónico, §6 backups, y corrección de la afirmación falsa de TASK-011), `architecture.md`, `ui-design-system.md`, `testing-guide.md` (tabla a 28, notas de concurrencia en Tk)
- **Los 4 tests discriminan, verificado por mutación** en copia temporal, cada uno por su aserción prevista: FIX-001 `apps comparte objeto (shallow)`, FIX-005 `_DEFAULT_META[0] es '? Otros'`, FIX-009 `save() no creo el .bak preventivo` y, por separado, la recuperación. Para FIX-007 se probó además una **5ª mutación opaca** (`grouped_processes.clear()` desde el hilo, invisible al guard `ast`): también falla, así que el test no es solo lint estático.
- Verificación independiente: **PASS**. Un bug del propio implementador lo delató la validación: importó `is_system_protected` como función de módulo cuando es un `@staticmethod` de `ProcessService`.
- Hallazgo abierto (MEDIUM, no corregido): `CORRUPTION_ERRORS` no incluye `AttributeError`, así que **3 de 7 formas** de JSON malformado propagan y tumban el arranque. No hay pérdida de datos —no se escribe nada— pero es disponibilidad y contradice el docstring de `load()`.

### Impact
Dos de las cuatro premisas de la tarea resultaron falsas, y el hallazgo útil vino de auditarlas en vez de implementarlas tal cual: el problema de integridad de datos real no era "falta un backup" sino que **el archivo de configuración del usuario se borraba entero ante cualquier error, incluidos los de permisos**. La lección: `except (json.JSONDecodeError, Exception)` es `except Exception` — el contexto de la tupla sugiere dos categorías y no lo es.

---

## [CYCLE-019] 2026-09-30 09:10 - 2026-09-30-validate-pack-leaves
**Área**: Resiliencia & Robustez
**Change**: openspec/changes/2026-09-30-validate-pack-leaves/
**Estado**: COMPLETED — **3 iteraciones del Paso 3, 1 FAIL y una re-auditoría intermedias**
**Models**:
- Paso 1 (Buscar): `inherit` — `TASK-031` era la `active_task_id` y `critical`
- Paso 2 (Planear): `inherit` (con override: integridad de datos)
- Paso 3 (Ejecutar): `inherit` ×3 (cada iteración con el informe del auditor)
- Paso 4 (Auditar tests): `inherit` (`mutation-auditor`) ×3 → **FAIL, FAIL, PASS**

### What — lo que el arquitecto REFUTÓ (ninguna premisa del encargo era cierta)
1. *"La guarda valida el contenedor, no las hojas"* es **FALSO en la rama moderna**: `pack_service.py:171` es `return AppData(**raw_data)`, que ya detecta `keepers:"str"`. La rama ciega es **solo la legacy**, por un `Pack(...)` literal de **5 de 8 campos** (`pack_service.py:161-169`); los dos que faltaban eran `keepers` —la lista **anti-brick**— y `target_categories`.
2. *"La solución es validar contra Pydantic"* **ya se hace**, y con esa guarda los 14 escenarios **siguen machacando el `.bak`**.
3. *"Un `save()` posterior machaca el `.bak`"* es una **subestimación grave**: la causa es `_rotate_backup()` (`:206-207`) validando con `json.load` en vez de `_read_json`. **Dos definiciones de "no corrupto"** y el docstring describía la que no se ejecuta. Medido: el `.bak` sano moría en **7 de 8 escenarios**, incluidos los que el repo **afirmaba proteger**, y **no era un `save()` del usuario** sino el de `_ensure_gaming_pack()` **dentro de `load()`**. `data-models.md:53-55` afirmaba esa garantía: falsa.
4. *Bonus:* `{"packs":…,"profiles":…}` borraba los packs legacy sin clasificar nada; y un campo raíz desconocido (`notas`) se perdía en el primer `save()`.

### Decisión de producto (§3)
**Una hoja mal formada es CORRUPCIÓN**, no un pack válido con un campo raro. Motivo: `keepers` es la lista anti-brick (`gaming_service.py:24`) y normalizarla a `[]` desarma el Gaming Mode de forma **invisible e irreversible**. Recuperar del `.bak` puede devolver otra versión, pero eso es **visible y diagnosticable**; un fichero borrado no se reconstruye. Se acepta con tres condiciones: mensaje con campo+pack+tipo, recuperación observable, y **sin `.bak` legible no se regenera a lo bruto**.

### Las tres iteraciones del Paso 3
- **Iteración 1** → el dev se auto-declaró 13/13 verde. **Auditoría: FAIL.** Encontró que `AppData.extra="allow"` era *load-bearing* contra la pérdida de datos y **ningún test la vigilaba**: con `extra="ignore"`, una raíz mal escrita (`perfiles`) hacía que el primer `save()` publicase `{"packs":…}` y **los packs del usuario desapareciesen del disco** (medido). Además: typo `keeper` aceptado en silencio → **anti-brick desarmado**; e `is_gaming:"true"` coercionado a `True` → pack **invisible e indeletable** (`delete_pack` lanza *"No se puede eliminar el pack de sistema"*).
- **Iteración 2** → **Auditoría: FAIL** con 3 supervivientes medianos: **M8** (los extras de raíz, incluido `favorite` que existe en un `profiles.json` legacy real, se destruían en el primer `save()`), **M4b** (`is_favorite` laxo, hermano sin fijar del que sí se arregló) y **M13** (`_normalizar_clave` sin sonda). Además, falsos positivos: `names`→`name` e `ids`→`id` a distancia 1 se declaraban corrupción, lo que hacía **falsa** la afirmación documental de "cero falsos positivos".
- **Iteración 3** → **Auditoría: PASS.** 19 mutaciones vigiladas, ningún superviviente en el rango declarado.

### Mutaciones auditadas (Paso 4, iteración final)
| Fix | Mutación | Veredicto | Motivo |
|---|---|---|---|
| Copia de la raíz | no copiarla | killed | `la clave raiz 'favorite' desaparecio del disco tras el save()` |
| Copia de la raíz | copiar `profiles` también | killed | `el landmine solo explotaria en el segundo arranque` |
| Vigilancia de hoja | solo en la moderna | killed | `[legacy/keeper]` |
| Vigilancia de hoja | solo en la legacy | killed | `[moderna/keeper]` |
| `is_favorite` | sin `strict` | killed | `_read_json dio None en vez de ValidationError` |
| Normalización | `_normalizar_clave`→identidad | killed | `'IS-FAVORITE' se acepto como campo desconocido` |
| Umbral | 1→2 pulsaciones | killed | `'note' esta a distancia 2 de 'name'` |
| `extra` raíz | `AppData extra="ignore"` | killed | `quedan ['packs']: los packs se han perdido` |
| `extra` hoja | `Pack extra="forbid"` | killed | `un campo desconocido se clasifico como corrupcion` |
| `extra="allow"` raíz | raíz sin clave conocida | killed | `una clave de la RAIZ se declaro error de escritura` |

### Outcome
- Tests: **36 → 48**, 0 fallos. `verify_ui_syntax.py` EXITO. `validate_docs.py` 0 FAIL.
- **VERDICT final: PASS.** Ningún camino destruye datos; ningún test decorativo.
- **Propiedad estructural CONFIRMADA por medición** (el logro de diseño): `CLAVES_DE_PACK` se deriva de `Pack.model_fields`, así que añadir un campo nuevo al modelo hace que su error de escritura se clasifique **sin tocar una línea de la guarda**. El auditor lo verificó con un campo inventado, dos veces.
- **La decisión de NO vigilar la raíz se sostiene con datos, no con opinión:** clasificarla haría `self._data = AppData()` y el siguiente `save()` publicaría `{"packs":{"gaming":…}}` → pérdida igual **y con un aviso encima**.
- **El arreglo de M8 no abre un agujero nuevo:** 18 nombres reservados de Pydantic (`model_config`, `copy`, `model_dump`…) probados; ninguno tumba el arranque ni pierde el dato.
- **Commits: ninguno** (persiste el bloqueo de shell).
- Deuda menor, declarada y **no** certificate: 2 supervivientes de normalización que requieren **2+ pulsaciones** (fuera del umbral declarado de 1), y 2 citas documentales erróneas (`config.py:95` → `CATEGORY_ORDER` está en 97; `proposal.md:222-226` sigue diciendo "No bloqueante" para `extra="allow"`, refutado en `tasks.md` §3/§4).

### Impact
El ciclo más caro en tiempo hasta ahora —3 vueltas— y el que más justificó el Paso 4. La secuencia importa: el implementador se Declaró verde, el auditor lo refutó y encontró la pérdida de packs, la segunda iteración arregló eso pero abrió otra ruta, la tercera la cerró. **Sin el paso de auditoría, el `.bak` habría seguido destruyéndose y el ciclo habría publicado "48 tests en verde" tres veces.**

La lección de diseño: **el fallo no estaba donde apuntaba el encargo, sino en una rotación de copias que usaba un criterio distinto del que se usaba para decidir si un archivo estaba dañado**. Dos definiciones de la misma pregunta, en el mismo fichero, es exactamente el tipo de divergencia que sobrevive a años de revisión.

**Nota de proceso (autorrelevada):** el dev se salió de su lista de ficheros en `models.py` y lo declaró, con el motivo (`extra="forbid"` es la mutación que la sonda clave debe matar, y `extra="forbid"` es el default). Salidas justificadas y declaradas se pueden aceptar; salidas silenciosas no.

---

## [CYCLE-016] 2026-09-30 00:32 - roles-como-agentes
**Área**: infraestructura del pipeline (a petición explícita del propietario)
**Change**: ninguno (no toca `src/`); modifica `AGENTS.md` y `.agents/skills/id-pipeline/SKILL.md`
**Estado**: COMPLETED (sin commit: persiste el bloqueo de shell)
**Models**:
- Paso 1 (Buscar): `inherit` (el dueño preguntó por qué no veía las skills; el trabajo salió de esa pregunta)
- Paso 2 (Planear): `inherit` (sin cambios de arquitectura de producto; decisión de mecanismo)
- Paso 3 (Ejecutar): `inherit` (traducción de 3 skills a 3 `agent.md` + reparación de referencias rotas)

### What
- **Los tres roles del pipeline pasaron de skills a agentes reales**: `architect-review`, `openspec-dev` y `process-db-updater` viven ahora en `~/.minimax/agents/<name>/agent.md` y aparecen en el panel del runtime.
- **Causa raíz de "no veo las skills":** `.agents/skills/` es un mecanismo **distinto** del panel de agentes. Una skill es un fichero de instrucciones que carga el orquestador; un agente es una sesión propia delegable con `task`. Las cuatro estaban donde correspondía, pero el panel solo lista la segunda clase.
- **Referencia rota en `id-pipeline`:** los pasos 2, 3 y la invocación de `process-db-updater` seguían mandando usar `invoke_subagent` con `Role` y `TypeName`, un mecanismo que **ya no existe** en este runtime. Consecuencia real: la primera invocación de `architect-review` falló con *"Unknown agent"*, y el orquestador tuvo que delegar a `worker` copiando las directrices a mano en el prompt — exactamente la traducción que los agentes reales eliminan.
- **Sección 7 reescrita:** la matriz de modelos pedía `flash` / `inherit` / `pro`, valores que el runtime actual **no acepta** en `task` (rellenar `model` a mano produce error de resolución). Conservada como guía de **intensidad**, con la instrucción de resolver el modelo solo si el usuario lo pide.
- **`AGENTS.md` actualizado** con una tabla que separa explícitamente skill de agente, y las tres trampas del entorno (`tm.py` no ejecutable, `git` a pelo prohibido, doble escritura de changelog).
- **Cada `agent.md` incorpora las lecciones de los ciclos 14 y 15**, no solo el texto de la skill: la barrera de categoría roja frente al blacklist, el fallo de `p.name` sin extensión, `is_system_protected` como `@staticmethod`, el emoji `⚪ Otros` (U+26AA) y la reescritura de `print()` en ASCII.

### Outcome
- **Prueba de arranque real, no una aserción:** se delegó a `architect-review` un audit de humo. Respondió los 5 puntos con `archivo:línea`, identificó **sin pista** que `is_system_protected` es un `@staticmethod` de `ProcessService` y no una función de módulo (el mismo error que tumbó al implementador del ciclo 14), y razonó por su cuenta que el blacklist **no** protege `svchost` porque su categoría 🔴 no está en el frozenset. Cero ficheros modificados, cero git: respetó su propio scope.
- Tests: sin cambios en `src/`, la suite sigue en 28/28.
- **Commits: ninguno** (persiste el bloqueo de shell de los ciclos 14 y 15).
- **Dos regresiones que introduje yo en este pase, ambas encontradas por el verificador:**
  1. Al renombrar la sección de roles de `AGENTS.md` a "Roles del Pipeline", `validate_docs.py` seguía buscando el encabezado antiguo por nombre literal y pasó a dar FAIL. Un validador atado a un título deja de validar en cuanto el título mejora → ahora acepta ambos nombres.
  2. **Falso verde en el ancla:** mi primer arreglo convertía el salto silencioso en FAIL, pero solo para el journal **corrupto**. El **ausente** seguía en verde, porque el `errors.append()` vivía dentro del `except` y el `if os.path.exists()` saltaba la rama entera. Y había un cuarto caso silencioso: journal válido pero con la lista vacía. Los tres fallan ahora con mensaje explícito, verificado con los 3 escenarios más un control.
- Referencias rotas restantes en `id-pipeline/SKILL.md` reparadas: 5 usos de `tm.py next/done/list` (no ejecutable aquí → leer `tasks.json`), la columna "Modelo Recomendado" (valores no soportados → "intensidad") y la sección de validación, que **afirmaba** que el script comprobaba la sección `Models` de cada entrada cuando no lo hace. Documentados los límites reales del validador.
- Los 3 skills de rol llevan ahora un banner **SUSTITUIDA POR UN AGENTE** con su contenido plegado en `<details>`. Motivo: eran una segunda fuente de verdad que divergía del agente y arrastraba referencias rotas.

### Impact
El pipeline deja de depender de que el orquestador recuerde traducir skills a prompts. Con los tres roles como agentes, la independencia es real: el arquitecto audita en su propia sesión sin ver la conversación, lo que hace que su "visto bueno" valga como criterio y no como rubber stamp. Antes esa separación era nominal.

---

## [CYCLE-017] 2026-09-30 01:15 - paso-4-mutation-auditor
**Área**: Pipeline (petición explícita del propietario: "añade un paso que aporte mucho")
**Change**: ninguno en `src/`; modifica `id-pipeline/SKILL.md`, `AGENTS.md` y crea el agente `mutation-auditor`
**Estado**: **ABIERTO** — el Paso 4 devolvió FAIL (3 supervivientes). Sin `PASS` el ciclo no se cierra; el trabajo de infraestructura de este pase sí está hecho y verificado. (sin commit: persiste el bloqueo de shell)
**Models**:
- Paso 1 (Buscar): `inherit` (la pregunta del propietario *era* el encargo)
- Paso 2 (Planear): `inherit` (decisión de proceso, no de arquitectura de producto)
- Paso 3 (Ejecutar): `inherit` (nuevo agente + skill + AGENTS.md)
- Paso 4 (Auditar los tests): `inherit` (`mutation-auditor`) → **VERDICT: FAIL**, ver abajo

### What
- **El bucle pasa de 3 a 4 pasos.** El nuevo **Paso 4** es "auditar los tests": un agente rompe el código a propósito y comprueba que los tests lo detecten. Sin su `PASS`, el ciclo no se cierra.
- **Nuevo agente `mutation-auditor`** (`~/.minimax/agents/mutation-auditor/agent.md`). Trabaja **solo sobre copias en `%TEMP%`**, tiene prohibido escribir en el repo y prohibido reparar lo que encuentra. Lleva una **tabla de 12 mutaciones canónicas** de este repo, que es el conocimiento que costó tres ciclos descubrir.
- **Regla dura añadida:** un sobreviviente en **seguridad o datos no se documenta como deuda, se arregla**. Documentar una brecha conocida es exactamente cómo se cuela un brick tres ciclos después.
- **Reparadas 9 referencias a `tm.py`** en todo el repo (`AGENTS.md`, `id-pipeline/SKILL.md`, `tasks.md`, `docs/ai/INDEX.md`, `llms.txt` y un change activo) que seguían mandando ejecutar un comando **no funcional** en este entorno. Cualquier agente nuevo que leyera esas guías se atascaba en el paso 1. Nota: en el ciclo 16 se repararon las de la skill; aquí las del resto de la documentación.
- La sección de validación de la skill afirmaba que el script comprobaba la sección `Models` de cada entrada: **no lo hace**. Reescrita con lo que comprueba de verdad y sus límites.

### Outcome
- **El primer arranque del agente nuevo encontró 3 supervivientes reales en los fixes del ciclo 15**, dados por cerrados:
  1. **Atomicidad sin verificar.** El test comprueba que exista un `.tmp`, así que si la escritura deja de ser atómica y **nunca** crea el `.tmp`, el assert sigue pasando **por la razón equivocada**. Nadie prueba que `profiles.json` quede intacto si el `json.dump` se corta a mitad.
  2. **`except OSError` acepta dos cosas distintas.** El caso D2 arma el escenario con `os.chmod(0o400)`: la escritura falla **por el mismo permiso que se quiere detectar**, y `except OSError: pass` acepta igual "no intentó escribir" que "intentó y reventó". Un mutante que reintroduce `OSError` en `CORRUPTION_ERRORS` **sobrevive con 28/28 en verde**.
  3. **`CORRUPTION_ERRORS` sigue incompleto.** `ValidationError`, `TypeError` y `UnicodeDecodeError` no están cubiertos, y los tres **tumban `PackService()`** — se confirmó que `{"profiles": "texto"}` lanza `AttributeError`. Es el hallazgo que ya estaba abierto desde el ciclo 15, ahora con confirmación empírica.
- Extras detectados: el guard `ast` del test de FIX-007 mata **antes** de que se compruebe la carrera real (al quitarlo, el test cuelga el bucle Tcl en lugar de fallar con `AssertionError`); y `get_gaming_pack()` / `_force_update_db()` siguen **sin ningún llamador** en `src/`.
- El agente verificó por SHA-256 y mtime que **no escribió en el repo**, y declaró un incidente propio: dos mutaciones concurrentes contaminaron su copia, las detectó y repitió **en serie**.
- Tests: sin cambios en `src/`; suite intacta en 28/28.
- **Commits: ninguno** (persiste el bloqueo de shell desde el ciclo 14).

### Impact
El bucle ganó su paso más valioso justo cuando menos confianza había: los tests del ciclo 15 se habían marcado como discriminantes **porque el implementador lo afirmó**, y el mutation-auditor refutó esa afirmación en su primer minuto. La lección de fondo es la misma que sostiene el paso: **`run_tests.py` en verde no es evidencia de nada sobre la calidad del test**. Lo único que convierte un test en evidencia es romper el código y verlo morir.

---

## [CYCLE-018] 2026-09-30 02:10 - 2026-09-30-close-mutation-survivors
**Área**: Resiliencia & Robustez
**Change**: openspec/changes/2026-09-30-close-mutation-survivors/
**Estado**: COMPLETED (cierra el FAIL del #17; deja TASK-031 abierta por hallazgo nuevo)
**Models**:
- Paso 1 (Buscar): `inherit` — el FAIL abierto del #17 manda sobre el backlog; TASK-027/028/029 siguen pendientes
- Paso 2 (Planear): `inherit` (diseño de tests de fault-injection; el modelo caro se reservó al análisis de seguridad)
- Paso 3 (Ejecutar): `inherit` (spec ya auditada, 2 ficheros de producción)
- Paso 4 (Auditar tests): `inherit` (`mutation-auditor`) → **VERDICT: PASS** (7/7 mutaciones muertas)

### What
- **Cierra el FAIL del ciclo #17.** Los 3 tests que pasaban con el bug puesto están arreglados: (a) atomicidad probada por fault-injection dentro de `json.dump` afirmada sobre **bytes** del principal, sin hilos ni `sleep`; (b) el caso de permisos comprueba el **estado resultante**, no un contador de llamadas; (c) `AttributeError` ya no tumba `PackService()` al arrancar.
- **El arquitecto refutó las TRES premisas del encargo, con mediciones:**
  1. `CORRUPTION_ERRORS` **ya cubría** `ValidationError`/`TypeError`/`UnicodeDecodeError` (`pack_service.py:16`). El mutante sobrevivía porque **ningún test las miraba**: el arreglo era de test, no de código. El agujero real era `AttributeError` en la rama legacy (`pack_service.py:79`, `:90`), que **tumbaba `PackService()` al arrancar** con `{"profiles":"texto"}` — peor que el bug perseguido.
  2. *"Falta un espía que afirme que `save()` NO se llamó"*: **falso por construcción.** Medido `save()=1, volcados=1` en el código correcto **y** en el mutante. Además `load()` escribe dos veces (`pack_service.py:59-61` + `:173`).
  3. En Windows `chmod` solo niega **escritura**: la lectura sigue permitida, así que toda la familia con `chmod` es **ciega**. Tres escenarios probados, ninguno distingue.
- **`AttributeError` excluido de `CORRUPTION_ERRORS` a propósito:** incluirlo convertiría cualquier bug interno en pérdida de packs. Y `except Exception` sigue rechazado por ser el bug del ciclo 15. Se valida la **forma** con `PerfilCorruptoError(ValueError)`.
- **FIX-007 sin Tk:** arnés con `__new__` + propiedades que anotan el hilo. Permitió **quitar `faulthandler.dump_traceback_later(150, exit=True)`**, que hoy mataba el runner. El test de la vista ya no abre una ventana.
- **El dev se salió de su lista de ficheros** en `docs/ai/architecture.md` (2 líneas) y lo declaro: su cambio dejaba falsas una referencia al watchdog eliminado y el nombre del test. Documentación que miente es peor que ninguna.

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo |
|---|---|---|---|
| Atomicidad | `os.replace` → `copyfile` | killed | `la escritura atomica no deja .tmp` |
| Limpieza | sin `unlink` del temporal | killed | `un save fallido no debe dejar un .tmp` |
| `except` | readmitir `OSError` | killed | `save() no lanzo el PermissionError de la rotacion` |
| Guarda de forma | sin `isinstance(perfiles, dict)` | killed | `lanzo AttributeError(...) en vez de PerfilCorruptoError` |
| `except` | `except Exception` en `load()` | killed | `un OSError de lectura no es corrupcion ... arranco en silencio` |
| `except` | readmitir `AttributeError` | killed | `AttributeError NO puede estar en CORRUPTION_ERRORS` |
| Hilo | `self.after(0,_apply)` → `_apply()` | killed | runtime: `'processes' se publico desde el hilo 26140, no desde el principal (19000)` |

Ninguna muerte por ImportError o sintaxis. **La del hilo se verificó neutralizando el guard `ast`**: sigue roja en runtime y verde con el código intacto, o sea no tautológica.

### Outcome
- Tests: **28 → 36**, 0 fallos. `verify_ui_syntax.py` EXITO (8/8). `validate_docs.py` 50 OK / 0 FAIL.
- **VERDICT del Paso 4: PASS.** El arbitrage del `except` dio bien: `null`, `[]`, `{"a":1}`, `0`, `true`, valor `null` y `label` no-str → los 7 se clasifican como corrupción y recuperan del `.bak` sano con cero escritura.
- **Commits: ninguno** (persiste el bloqueo de shell).
- **Hueco nuevo, abierto como `TASK-031` (critical):** la guarda valida el **contenedor**, no las **hojas**. Un pack con `keepers` o `target_categories` mal formados pasa, la rama legacy nunca lee esos campos, el `.bak` sano **nunca se consulta** y un `save()` posterior **lo machaca**. Pérdida silenciosa e irreversible. Pre-existente y no regresión de TASK-030, pero ningún test lo veía.

### Impact
El paso de auditoría no solo confirmó el arreglo: lo hizo **refutando el encargo**. Tres premisas que parecían verdad eran falsas, y la más grave (`AttributeError` tumbando el arranque) era **peor que el bug que se perseguía**. Un plan que hubiera seguido esas premisas habría escrito tests que pasan y no arreglado nada.

**Nota de proceso (autorrelevada):** rompí dos veces `tasks.json` con ediciones por regex sobre JSON. La causa es siempre la misma —mi editor no entiende la estructura—, y la lección es usar un script de Python con `json.load`/`json.dump` para cualquier edición estructural, nunca sustitución de texto. Recuperado ambas veces sin pérdida.


## [CYCLE-049] 2026-10-02 - check-deuda-con-anclas

**Área**: Documentación & Arquitectura
**Change**: openspec/changes/2026-10-02-check-deuda-con-anclas/
**Estado**: IMPLEMENTADO (TASK-060) — la palabra final la tiene el `mutation-auditor`. Rondas 2, 3 y 4: `FAIL`, `FAIL`, `FAIL`; esta cuarta responde a las siete correcciones del auditor y las siete eran **de texto**: ninguna tocaba `src/` ni una sola fila del panel.
**Models**:
- Paso 1 (Buscar): orchestrator (backlog: `active_task_id` TASK-060)
- Paso 2 (Planear): architect-review — contrato con el diseño de las cinco fuentes de verdad, el reparto reubicado en el check 7 y la medición que refutó tres premisas del encargo
- Paso 3 (Ejecutar): openspec-dev — TASK-060 (`validate_docs.py`, `run_tests.py`, `STATUS.md`, `docs/ai/sandbox-rules.md`, `docs/ai/testing-guide.md`, `AGENTS.md`, `README.md`, `docs/index.md` y los dos changelogs)
- Paso 4 (Auditar tests): `mutation-auditor` — tres rondas, las tres `FAIL`. La cuarta devuelve el ciclo al auditor con las siete correcciones aplicadas y medidas; el veredicto final no es de este pase.

> **Por qué esta entrada va al FINAL y no arriba:** el registro va de más nuevo a más viejo, y anteponerla desplazaría las 26 citas `fichero:línea` a `.taskmaster/CHANGELOG.md` que existen en 11 ficheros. Al agregarla al final no se desplaza ninguna. Escrito para que se lea como decisión y no como descuido.

### Lo implementado

- `_comprobar_deuda_con_anclas(root, errors, ok)` en `validate_docs.py`: tres posicionales, **sin defaults** y sin parámetros extra, cableada entre el check 7 y el `return` de `validar(root)`. Un default convertiría un cableado roto en un `None` silencioso.
- Cinco fuentes de verdad, todas fuera del panel: S1 la ruta existe, S2 la atribución `fichero:línea identificador` contiene el identificador, S3 `TASK-NNN` con `status` legible, S4 `CYCLE-NNN` con entrada en un registro, S5 la cifra que coincide con el recuento derivado con `ast`. El marcador de cierre se busca **después** de borrar el código inline, y hay una regla que impide que la fila del criterio se marque cerrada. **Ronda 2, endurecido sobre cuatro cosas medidas:** la palabra exige final de palabra (`\bCERRAD[OA]\b`), la negación se evalúa **en el veredicto y en la prosa y sin ventana cortable por puntuación**, el panel se rechaza como ancla por **identidad de la ruta resuelta**, y el marcador se acepta **en mayúsculas** por decisión explícita. **Ronda 4, tres cosas más medidas, y las tres nacen de que el `mutation-auditor` *midiera* lo que este informe afirmaba sin medirlo:** (i) `_esta_cerrada` tiene una **quinta** condición —el id que cierra la fila tiene que estar **cerrado**, no solo existir—, que es la que cierra G2f' sin tocar el panel; (ii) el filtro del panel se amplía de identidad de **ruta** a identidad de **fichero** (`st_dev`+`st_ino`), porque un enlace duro no cambia de nombre; y (iii) `os.path.normcase` se **quita**: se llamaba «segunda garantía» y no hacía nada en ninguna plataforma. La autoexención de la fila del criterio se evalúa **antes y por separado** del estado de los ids, porque si no el escenario (f2) se rompe y el guard que vigila al vigilante se apaga a sí mismo.
- `_reparto_de_tests(root)` + `_comprobar_reparto_de_tests(root, errors, ok, defined)`: el reparto `94 + 10` derivado con `ast` en el **check 7**, no en el 8, y con el motivo literal obligatorio cuando el marcador estructural no aparece.
- Un único test con **treinta** escenarios, todos por `validar(root)`, sobre el esqueleto real copiado una vez y con el total derivado con `ast` del árbol sintético. La ronda 2 los subió de 19 a 25 (`r` a `w`) y la ronda 4 de 25 a **30** con `x` (id pendiente), `c3` (ciclo en vuelo), `h2` (enlace duro) y los controles negativos `y` y `n2`. **El número de tests no cambió**, porque los escenarios son filas de una tabla. Dos filas nesta ronda necesitan tocar el **árbol**, no solo el texto (`PREPARA`): una crea el enlace duro y otra escribe el journal, y el estado que meten se restaura en cada iteración para que una fila no mida el árbol de la anterior.

### Outcome

- Tests: **103 → 104**, 0 fallos. `verify_ui_syntax.py` EXITO (8/8). `validate_docs.py` **115 OK / 0 FAIL** con el check 8 activo.
- **Autocomprobación de la ronda 4, medida contra `a31e585` y con el validador de ese commit tal cual**: del panel, **4 ataques que este pase cierra** (G2f' con `TASK-059`, con `TASK-061` y con la negación en minúscula, y el enlace duro `H1`) y **9 que sobreviven, todos declarados**; del código, **5 mutantes del validador y 5 muertes**, una por fix. **El baseline de la ronda anterior queda en el informe y con su commit**, porque sin eso un informe de mutación no se puede re-auditar. Sobreviven `C21` y `C27`, **inertes**. **C30 se ha retirado como mutante**: era «quitar el `normcase`» y sobrevivía con una justificación **falsa** —en POSIX `normcase` es `return os.fspath(s)` y en Windows `realpath` ya devuelve el nombre real—, así que la llamada se ha quitado en vez de defenderla. Y el residuo de G2f' se ha **reducido**: el informe anterior declaraba «no hay regla que separe la fila 87 del ataque sin poner el repo en rojo», y eso es falso —los ids de las 7 exentas están **todos dentro** del veredicto, y lo que separa la fila 87 del ataque es que ella nombra trabajo **cerrado** y el ataque nombraba trabajo **pendiente**—.
- El panel cambió en **una** fila en el ciclo (`STATUS.md:91`), más dos cláusulas de cifra **añadidas** por añadido. **En esta ronda de cierre: CERO filas tocadas** — las cinco correcciones son de `validate_docs.py`, `run_tests.py` y documentación, y se comprobó que el panel intacto sigue en `7 exenta(s) / 8 viva(s) / 35` anclas y `0 FAIL` con la quinta condición puesta. Ninguna fila se borró ni se reescribió.
- `src/woptimizer/**` con **cero** cambios.
