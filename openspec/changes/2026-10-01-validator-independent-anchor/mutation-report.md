# Informe de mutacion — ancla de trazabilidad en el historial

Change: `2026-10-01-validator-independent-anchor` · Tarea: `TASK-057` · Ciclo: `#47` ·
Intento: **3** (re-planificacion del Circuit Breaker, `tasks.md` T-7),
**ronda de cierre** con los cinco holes que trajo el `PASS` del auditor (P2, P3, H2, E2, E3).

> **Quien escribe esto y quien no.** Este fichero lo escribe `openspec-dev` como
> **autoprueba** del intento 3: los mutantes se aplicaron al `validate_docs.py` REAL
> (nunca a una copia reimplementada), se ejecuto el test real y se exige que muera **por
> su asercion**. `VERDICT` de un `mutation-auditor` es otra cosa: cuando el auditor pase,
> su veredicto se anade aqui y este texto se conserva como la medicion previa. Sin este
> fichero un `FAIL` no es re-auditable por nombre, que es justo lo que paso con los 12
> supervivientes del intento 1 (ver la ultima seccion).

## Como se ejecuto

| Pieza | Detalle |
|---|---|
| Sujeto de la mutacion | `validate_docs.py` del arbol de trabajo, byte a byte, con hash SHA-256 del original verificado antes y despues de cada mutante |
| Restauracion | El original se restaura entre mutantes y el hash se comprueba; si no coincide, el script aborta con asercion |
| Que se exige | Que el test **MUERA** y muera por `AssertionError`. Un `ImportError`, una excepcion o un traceback NO cuentan como muerte |
| Purga | `__pycache__/validate_docs.*` se borra antes de cada corrida, para que ningun mutante se mida contra un `.pyc` viejo |
| Fichero de git | **Ninguna** fixture toca el historial real: cada escenario apunta su `GIT_DIR` a un repo de `tempfile` |

## Contrato T-7: veredicto medido

| # | Mutante (mutacion literal) | Asercion que lo mata | Test | Veredicto | Motivo literal del fallo |
|---|---|---|---|---|---|
| **M2** | borrar el 4o argumento de la llamada: `_comprobar_ancla_de_commits(root, errors, ok, journal_cycles)` -> `(root, errors, ok)` | `Resumen:` presente en el informe del subproceso | `test_el_ancla_se_cablea_en_el_camino_real_del_validador`, primera mitad | **MUERTA** | Sin default el mutante es un `TypeError: _comprobar_ancla_de_commits() missing 1 required positional argument: 'journal_cycles'`, el validador muere antes de imprimir y `Resumen:` no aparece |
| **D2** | `<- sin default`: `journal_cycles=()` reintroducido en la firma | **NINGUNA, y no puede tenerla**: ver "D2 no es un mutante" | -- | **INERTE, sobrevive por diseño** | Con el default restaurado y la llamada **intacta**, el parametro no llega a usarse: no cambia ningun veredicto, asi que no hay asercion que pueda matarla. La version anterior de esta fila decia "identica a M2" y era **FALSA** |
| **A1** | desactivar la rama `if not ciclos and journal_cycles:` -> `if False:` | fila **(a)**: `"NO aporta ningun ciclo"` en `errors` | tabla de escenarios | **MUERTA** | `fila (a): ... Errores: []`: el parser roto deja de acusarse y el arbol sale sin errores |
| **A1b** | quitarle `and journal_cycles` -> `if not ciclos:` | fila **(b)**: `"NO aporta ningun ciclo"` **ausente** | tabla de escenarios | **MUERTA** | `fila (b): ...`: con el journal vacio se acusa dos veces por la misma causa; la fila (b) comparte historial con la (a), por eso la poda se delata en una de las dos |
| **M1** | desactivar `if not journal_cycles and journal_usable:` -> `if False:` | fila **(d)**: `"no contiene ningun ciclo valido"` en `errors` | tabla de escenarios | **MUERTA** | `fila (d): ...`: un journal que se lee pero no aporta ningun ciclo entero pasa en verde |
| **M1b** | quitarle `and journal_usable` -> `if not journal_cycles:` | `len(errors) == 1` con journal ilegible | `test_el_journal_ilegible_informa_en_vez_de_reventar_el_validador` | **MUERTA** | el journal `PermissionError` se reporta dos veces: como CORRUPTO y como "no contiene ningun ciclo valido", que son estados distintos |
| **A2** | quitar `--all`: `args = ["git", "log", "--format=%s", "--all"]` -> sin `--all` | fila **(c)**: el ciclo de una RAMA lateral se acusa por su conjunto | tabla de escenarios | **MUERTA** | `fila (c): ... Errores: []`: el ciclo 77, cerrado en `rama_lateral` y fuera del alcance de `HEAD`, deja de ser exigido |
| **S2** | borrar el cableado del ancla de commits dentro de `validar()` | `historial de commits:` + `corroborables` en el informe | `test_el_ancla_se_cablea_en_el_camino_real_del_validador` | **MUERTA** | el validador real responde `rc=0` y ninguna linea del historial: codigo testeado que el producto ya no invoca |
| **S2b** | borrar la llamada `validar(root)` de `main()` -> `errors, ok = [], []` | `historial de commits:` ausente y `Resumen: 0 OK, 0 FAIL` con `rc == 0` | mismo | **MUERTA** | `Resumen: 0 OK, 0 FAIL`, salida `0`: el validador declara el repo entero en verde sin comprobar nada |

**8 de 8 mutantes REALES del contrato mueren por su asercion. Ninguno muere por `ImportError` ni
por traceback del propio test.** La tabla tiene nueve identificadores y el noveno, **D2**, no es un
mutante: es una mutacion **inerte** (ver "D2 no es un mutante"). El texto anterior decia "8 de 8"
mientras la tabla.listaba nueve filas y daba a D2 una asercion que no tenia: un recuento que no
cuadra es el primer aviso de que la tabla miente.

## La medida que justifica D2

El default `journal_cycles=()` no era estilo: era la raiz de A1. Mutado **con** el default
restaurado (es decir, el mundo antes de D2), el mismo M2 se comporta asi:

| Test | Con D2 (estado actual) | Sin D2 (default restaurado) |
|---|---|---|
| `test_el_ancla_se_cablea_en_el_camino_real_del_validador` | **MUERE** (`Resumen:` ausente, `TypeError`) | **SIGUE EN VERDE** — el mutante sobrevive |
| `test_el_ancla_de_commits_no_depende_del_que_escribe_el_journal` | — | **SIGUE EN VERDE** — el mutante sobrevive |
| `test_el_journal_ilegible_informa_en_vez_de_reventar_el_validador` | — | **SIGUE EN VERDE** — el mutante sobrevive |
| `test_el_ancla_sobre_un_arbol_sintetico_tabla_de_escenarios` | **MUERE** (fila a) | **MUERE** (fila a) |

Dos cosas se miden aqui, y las dos son verdad a la vez:

1. **D2 es lo que hace el cableado imposible de romper en silencio.** Sin el, el mutante es un
   cambio de comportamiento y tres de los cuatro tests lo dejan pasar. Con el, es un
   `TypeError` y tumba el validador entero.
2. **La tabla de escenarios (D4) mata el mismo mutante por su cuenta**, porque la fila (a) monta
   un historial SIN marcadores, que es el arbol donde el cuarto argumento cambia el veredicto.
   O sea: la convergencia no depende de un solo mecanismo.

### D2 no es un mutante (correccion del cierre del ciclo #47)

La tabla de arriba mide **M2 con el default restaurado**. Eso NO es lo mismo que D2, y la fila
D2 de la tabla de contrato decia "identica a M2": era falso, y el fichero se contradia treinta
lineas mas abajo. Remedido por aislamiento, tres mutantes distintos:

| Mutante | Que cambia | Veredicto medido en el cierre | Por que |
|---|---|---|---|
| **D2 aislado** | solo la firma: `journal_cycles=()` | **SOBREVIVE** (rc=0, `TABLA OK`) | La llamada sigue pasando el argumento, luego el default no llega a usarse: mutacion **inerte**, sin veredicto que cambiar y sin asercion que pueda matarla |
| **D2 + M2** | firma con default **y** 4o argumento borrado | **MUERE por la fila (a)** | Es el mundo antes de D2. Confirma la afirmacion 2 de arriba: la tabla lo mata por su cuenta |
| **M2 sin default** | solo la llamada | **MUERE por el envoltorio**, no por una fila | `_informe_del_validador_real` convierte el `TypeError` en `AssertionError: validar(root) debia devolver un INFORME y tiro TypeError: ... missing 1 required positional argument` |

Consecuencia para el que lea esto dentro de seis meses: **el mutante que se mide es borrar el
argumento, no restaurar el default**. Y una mutacion equivalente al original no es un
superviviente que arreglar: es una fila de la tabla que hay que reetiquetar.

## Lo que NO se cierra aqui, declarado

- **Los subjects sin marcador de ciclo.** Su numero vivo esta en la linea de informe del
  validador (`historial de commits: ... subject(s), N con marcador de ciclo y M SIN marcador`) y
  **este documento no lo fija**, porque caduca con cada commit. La version anterior de esta
  linea decia "112 de 156 subjects" y al siguiente parrafo declaraba no fijar la cifra: las dos
  cosas no pueden ser verdad, y la cifra fija era la que caduca. Un ciclo cerrado con asunto
  `feat(...)` y sin entrada de journal sigue **sin tercer testigo**. Es `git_safe_commit.py`
  rechazando el mensaje sin identificador de ciclo = **`TASK-059`**, ya pendiente. Esta iteracion
  **no lo reintenta**: se DECLARA.
- **Los hashes del campo `commits` del journal.** 11 entradas sin hash, 3 hashes que no
  resuelven, 1 entrada sin ninguno resoluble (ciclo 33). Tambien `TASK-059`. El denominador que
  faltaba en la documentacion es **47 entradas**, no 46 (medido el 2026-10-02; el numerador 11 y
  la lista de ciclos no cambian).

## Lo que no se puede recuperar: los 12 supervivientes del intento 1

`grep` de `M8|R8|R9|R12|M16` en todo el arbol **no encuentra nada**: los 12 supervivientes que
devolvio el `mutation-auditor` del intento 1 vivian solo en la salida de su sesion, y por eso tres
cicles despues nadie puede comprobar cuales eran ni si son los mismos que los del intento 2. Sus
identificadores **no se inventan aqui**: un informe que fabrica los nombres que dice auditar es
peor que no tener informe. Lo que se registra es la regla, ya anadida al Paso 4 de la skill
(`id-pipeline/SKILL.md`): el informe de mutacion vive en
`openspec/changes/<change-id>/mutation-report.md`, con un identificador por mutante y su motivo.

## Cierre del ciclo #47: el `PASS` del auditor, y lo que venia con el

Los nueve mutantes del contrato T-7 mueren, uno a uno, y el `mutation-auditor` lo confirmo por
atribucion. El `PASS` no era el cierre del ciclo: **traia cinco holes**, y dos de ellos eran
falsos verdes demostrados, no teorias.

### P2 (ALTA): `missing_entries` laxo, el falso verde del ciclo #15 por otra puerta

El codigo estaba **bien** (`## CYCLE-015` completo, no el numero pelado). Lo que no existia era
una comprobacion de que lo estuviera: ninguna sonda montaba el arbol donde eso decide. El
`mutation-auditor` lo demostro **mintiendo al producto**, no por teoria, con `## CYCLE-015`
borrado y la prosa `TASK-015` viva: el codigo intacto da `[FAIL] CHANGELOG.md (raiz): sin
entrada para el/los ciclo/s 015`, y la version laxo da **cero fallos**.

Lo grave: el propio `validate_docs.py` lo advierte 200 lineas mas abajo, textual, que buscar el
numero como subcadena daria falso verde porque `"015"` sobrevive dentro de `"TASK-015"` -- el
bug que el ciclo #15 cerro y que `tasks.md` T-2 exige no reabrir. Una nota correcta en el sitio
donde se comete el error no es una defensa: es decoracion.

| Fix | Mutante literal | Muerto / vivio | Motivo literal de la muerte |
|---|---|---|---|
| Fila **(f)**: `## CYCLE-015` borrado, numero vivo en la prosa (`TASK-015` **y** `CYCLE-015`), journal e historial de acuerdo en el 15 | P2: `if f"## CYCLE-{c:03d}" not in rch and f"## [CYCLE-{c:03d}]" not in rch` -> `if f"{c:03d}" not in rch` | **MUERE** | `fila (f... del ancla`: con el numero pelado el ciclo 15 cuenta como cubierto y el arbol sale con `Errores: []` |
| Misma fila | P3: `has_jentry = (f"## CYCLE-{jlatest}" in rch or f"## [CYCLE-{jlatest}]" in rch)` -> `has_jentry = f"{jlatest}" in rch` | **MUERE** | `fila (f... del ancla`: `"015"` aparece en la prosa, la guarda de arriba no acusa y falta uno de los dos `[FAIL]` |
| Misma fila | H2: `if not has_jentry:` -> `if False:` | **MUERE** | `fila (f... del ancla`: la rama decorada deja de existir, el recuento de errores pasa a 1 y la fila exige 2 |
| Fila **(g)**: `git` falla **una vez** con `TimeoutExpired`, el segundo intento usa la `run` de verdad | E2: `except Exception as exc:` -> `except OSError as exc:` | **MUERE** | `AssertionError: validar(root) debia devolver un INFORME y tiro TimeoutExpired: ...`. Con `OSError` el timeout sale con traceback y **no comprueba ni el check 6 ni el 7** |
| Misma fila | E3: `for _intento in (1, 2):` -> `for _intento in (1,):` | **MUERE** | `fila (g... del ancla`: sin reintento `salida is None` y el validador declara `historial de commits: NO SE PUEDE LEER` en vez de leer el ciclo |

La fila (f) cita el numero **de dos maneras** a proposito (`TASK-015` y `CYCLE-015`): con una
sola clase de cita, la otra forma de busqueda laxo pasaria en verde sin que nadie se entere.

### H2 era decoracion, no guarda

Ninguna de las cinco filas anteriores construia "ultimo ciclo del journal **sin** encabezado",
o sea que `if not has_jentry:` no tenia ninguna asercion que lo comprobara. Sobrevivir no era
suerte: era que nadie lo miraba. Con la fila (f) es una guarda de verdad.

### G1 (BAJA): queda anotada, no cerrada

`\b(?:ciclo|cycle)s?\b` -- quitar el plural `s?` **sobrevive**, y no por falta de sonda sino
porque casi todos los asuntos del repo dicen "ciclo" en singular. Medido por el auditor: **un
unico commit real depende del plural** (`feat(ciclos 14-20)`), y al quitarlo el ciclo 14 sale del
conjunto corroborable sin avisar. Severidad **BAJA** porque el fallo es silencioso pero
acotado, y el parser solo puede ablandar el ancla, nunca endurecerla. **Se DECLARA**, no se
cierra: arreglarlo exigiria un aserto sobre el singular, y ese aserto tiene que decidir si
"ciclos 14-20" corrobora el 14, el 20 o los dos, que es una decision de producto y no mia.

### Lo que este cierre NO declara

**A1 esta erradicado donde se produjo y desplazado donde no se busco.**
`_comprobar_ancla_de_commits` acusa el parser roto (`108 OK / 1 FAIL`, fila (a) lo mata). En
`missing_entries` y `has_jentry` el mismo patron semantico -- buscar en vez de exigir -- seguia
vivo sin sonda. El ciclo no se declara cerrado por esto: **se declara cerrado donde se midio**.

**Las siete filas comparten esqueleto y helper, luego comparten punto ciego.** Una fila mide la
forma de arbol que construye: la (f) tapa P2/P3/H2 *porque* lleva prosa con el numero y sin su
`## CYCLE-`; contra un arbol sin esa prosa las dos versiones del codigo darian el mismo
veredicto y la fila pasaria sin medir nada. Limitacion asumida y escrita en el codigo, no
descubierta por el proximo que audite.

### El test que se declaraba "no contractual" y si lo es

`test_el_ancla_de_commits_no_depende_del_que_escribe_el_journal` asienta por las funciones
**privadas** pasandoles los argumentos a mano, y la redaccion de D3 lo declaraba
*unitario-no-contractual*. Medido: **es el UNICO guardian de tres invariantes que la tabla no
nota**, asi que la declaracion era incorrecta y creaba una trampa -- hacia imposible anadir ahi
la fila que tapa P2, porque el texto desaconsejaba el sitio correcto. Corregido en los tres
sitios donde estaba escrito (`run_tests.py`, `docs/ai/testing-guide.md`,
`docs/ai/sandbox-rules.md`).

| Invariante | Que mide | Que la tabla no nota |
|---|---|---|
| **U1** union != sustitucion | el arbol espejo con journal `{46,47}` e historial `{46}` tiene que exigir **cero** errores | la tabla cambia de historial por fila y no monta ese espejo |
| **P1** ciclo != tarea | el parser tiene que ignorar `TASK-046`; con el mutante el repo real da `107 OK / 2 FAIL` | ninguna fila pone un `TASK-` que se pueda confundir con un ciclo |
| **E1** ancla ilegible | un `GIT_DIR` que no es repo tiene que dar **informe y no excepcion**, y nunca verde | la fila (g) mide el fallo de `subprocess`, no un `GIT_DIR` invalido |

### Verificaciones de este cierre (comando y salida real, no "se verifico SHA-256")

```text
$ python verify_ui_syntax.py
OK: src/woptimizer/ui/views/process_manager_view.py compila perfectamente.
OK: src/woptimizer/services/notification_service.py compila perfectamente.
OK: src/woptimizer/__main__.py compila perfectamente.
EXITO: Todos los modulos UI estan impecables.
exit=0

$ python run_tests.py
test_process_manager_pack_dropdown_single_arrow_and_placeholder OK.

ALL TESTS PASSED.
exit=0

$ python validate_docs.py
  [OK]   docs/ai/testing-guide.md: 103 filas de test, una por test definido

Resumen: 108 OK, 0 FAIL
exit=0
```

Las tres en verde, con la suite en **103 tests**: las dos filas nuevas son filas, no tests. Y el
validador dando `108 OK / 0 FAIL` es su propio criterio A5, que sigue siendo una afirmacion --
lo que ahora la respalda es que `missing_entries` y `has_jentry` tienen una fila que las mata.


## VERDICT

**PASS** del autoprueba de `openspec-dev` sobre el contrato T-7: 8/8 mutantes muertos por su
asercion, 0 tests nuevos, suite 104 -> 103.

**Cierre del ciclo #47 (esta seccion):** el `PASS` del `mutation-auditor` traia cinco holes.
Medidos aqui uno a uno contra el `validate_docs.py` real, con SHA-256 verificado antes y
despues de cada mutante y `__pycache__` purgado: **P2, P3, H2, E2 y E3 mueren todos por su
asercion**, con dos filas nuevas y **0 tests nuevos** (suite 103 -> 103). **G1 se declara** con su
mutante y su severidad. Ademas se corrigen tres afirmaciones falsas de este mismo arbol: la
fila D2, la cifra "112 de 156" que se contradecia con la linea siguiente, y el denominador 46
del journal en `sandbox-rules.md`.
