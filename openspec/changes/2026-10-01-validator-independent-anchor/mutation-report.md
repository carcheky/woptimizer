# Informe de mutacion — ancla de trazabilidad en el historial

Change: `2026-10-01-validator-independent-anchor` · Tarea: `TASK-057` · Ciclo: `#47` ·
Intento: **3** (re-planificacion del Circuit Breaker, `tasks.md` T-7).

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
| **D2** | `<- sin default`: `journal_cycles=()` reintroducido en la firma | identica a M2 | mismo | **MEDIDO, no es un mutante** | Ver "La medida que justifica D2" |
| **A1** | desactivar la rama `if not ciclos and journal_cycles:` -> `if False:` | fila **(a)**: `"NO aporta ningun ciclo"` en `errors` | tabla de escenarios | **MUERTA** | `fila (a): ... Errores: []`: el parser roto deja de acusarse y el arbol sale sin errores |
| **A1b** | quitarle `and journal_cycles` -> `if not ciclos:` | fila **(b)**: `"NO aporta ningun ciclo"` **ausente** | tabla de escenarios | **MUERTA** | `fila (b): ...`: con el journal vacio se acusa dos veces por la misma causa; la fila (b) comparte historial con la (a), por eso la poda se delata en una de las dos |
| **M1** | desactivar `if not journal_cycles and journal_usable:` -> `if False:` | fila **(d)**: `"no contiene ningun ciclo valido"` en `errors` | tabla de escenarios | **MUERTA** | `fila (d): ...`: un journal que se lee pero no aporta ningun ciclo entero pasa en verde |
| **M1b** | quitarle `and journal_usable` -> `if not journal_cycles:` | `len(errors) == 1` con journal ilegible | `test_el_journal_ilegible_informa_en_vez_de_reventar_el_validador` | **MUERTA** | el journal `PermissionError` se reporta dos veces: como CORRUPTO y como "no contiene ningun ciclo valido", que son estados distintos |
| **A2** | quitar `--all`: `args = ["git", "log", "--format=%s", "--all"]` -> sin `--all` | fila **(c)**: el ciclo de una RAMA lateral se acusa por su conjunto | tabla de escenarios | **MUERTA** | `fila (c): ... Errores: []`: el ciclo 77, cerrado en `rama_lateral` y fuera del alcance de `HEAD`, deja de ser exigido |
| **S2** | borrar el cableado del ancla de commits dentro de `validar()` | `historial de commits:` + `corroborables` en el informe | `test_el_ancla_se_cablea_en_el_camino_real_del_validador` | **MUERTA** | el validador real responde `rc=0` y ninguna linea del historial: codigo testeado que el producto ya no invoca |
| **S2b** | borrar la llamada `validar(root)` de `main()` -> `errors, ok = [], []` | `historial de commits:` ausente y `Resumen: 0 OK, 0 FAIL` con `rc == 0` | mismo | **MUERTA** | `Resumen: 0 OK, 0 FAIL`, salida `0`: el validador declara el repo entero en verde sin comprobar nada |

**8 de 8 mutantes del contrato mueren por su asercion. Ninguno muere por `ImportError` ni por
traceback del propio test.**

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

## Lo que NO se cierra aqui, declarado

- **Los 112 de 156 subjects sin marcador de ciclo** (la cifra viva esta en la linea de informe
  del validador; este documento no la fija porque caduca con cada commit). Un ciclo cerrado con
  asunto `feat(...)` y sin entrada de journal sigue **sin tercer testigo**. Es
  `git_safe_commit.py` rechazando el mensaje sin identificador de ciclo = **`TASK-059`**, ya
  pendiente. Esta iteracion **no lo reintenta**: se DECLARA.
- **Los hashes del campo `commits` del journal.** 11 entradas sin hash, 3 hashes que no
  resuelven, 1 entrada sin ninguno resoluble (ciclo 33). Tambien `TASK-059`.

## Lo que no se puede recuperar: los 12 supervivientes del intento 1

`grep` de `M8|R8|R9|R12|M16` en todo el arbol **no encuentra nada**: los 12 supervivientes que
devolvio el `mutation-auditor` del intento 1 vivian solo en la salida de su sesion, y por eso tres
cicles despues nadie puede comprobar cuales eran ni si son los mismos que los del intento 2. Sus
identificadores **no se inventan aqui**: un informe que fabrica los nombres que dice auditar es
peor que no tener informe. Lo que se registra es la regla, ya anadida al Paso 4 de la skill
(`id-pipeline/SKILL.md`): el informe de mutacion vive en
`openspec/changes/<change-id>/mutation-report.md`, con un identificador por mutante y su motivo.

## VERDICT

**PASS** del autoprueba de `openspec-dev` sobre el contrato T-7: 8/8 mutantes muertos por su
asercion, 0 tests nuevos, suite 104 -> 103. El veredicto del `mutation-auditor` (Paso 4) se
anade a este mismo fichero cuando pase.
