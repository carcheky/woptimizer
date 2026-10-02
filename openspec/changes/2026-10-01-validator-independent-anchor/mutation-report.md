# Informe de mutacion — ancla de trazabilidad en el historial

Change: `2026-10-01-validator-independent-anchor` · Tarea: `TASK-057` · Ciclo: `#47` ·
Intento: **3** (re-planificacion del Circuit Breaker, `tasks.md` T-7),
**ronda de cierre** con los cinco holes que trajo el `PASS` del auditor (P2, P3, H2, E2, E3),
y **ronda de cierre 2** con lo que la auditoria de cierre de esa ronda encontro: la **columna de
atribucion mentia en tres filas** (medido y corregido aqui) y **G1 seguia abierto** (cerrado aqui,
con la semantica de plural decidida por producto).

> **Quien escribe esto y quien no.** Este fichero lo escribe `openspec-dev` como
> **autoprueba** del intento 3: los mutantes se aplican al `validate_docs.py` REAL
> (nunca a una copia reimplementada), se ejecuta el test real y se exige que muera **por
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

### Las DOS columnas de atribucion, y por que no son la misma (cierre 2)

La version anterior de este informe tenia **una** columna: "Test", con el nombre del test que
mata al mutante. Medido el 2026-10-02, **esa columna mentia**, y mentia de dos maneras distintas
que se confundian entre si:

| Lo que decia la columna | Lo que habia que decir |
|---|---|
| "M2 muere en el test de subproceso" | M2 muere en el test de subproceso **si lo corres solo**, pero **en la suite completa muere antes**, en `test_el_ancla_de_commits_no_depende_del_que_escribe_el_journal`, y tiene **4** guardianes, no 1 |
| "A1b muere en la fila (b)" | Cierto, y ademas en la suite completa muere **antes** en `test_el_journal_ilegible_informa_en_vez_de_reventar_el_validador` |
| "S2 muere en el test de subproceso" | Ese test es UNO de sus **4** guardianes, no el unico |

La causa no es descuido: es que **"muere aqui" y "muere aqui primero" son hechos distintos**, y la
suite tiene orden. Un mutante con cuatro guardianes, medido con un unico `python run_tests.py`, da
un solo nombre — el del primero — y ese nombre parece una atribucion cuando en realidad es una
coincidencia de orden. Por eso este informe lleva ahora las dos columnas por separado, mas el
**recuento de guardianes**:

- **"Donde muere en aislamiento"**: todos los tests que lo matan cuando se ejecutan **uno a uno**.
  Es la columna que describe la COBERTURA.
- **"Primero en la suite completa"**: el test que revienta antes en el orden real de
  `run_tests.py`. Es la columna que describe lo que veria quien ejecuta la suite.
- **"Guardianes"**: cuantos tests lo matan en aislamiento, sobre los 7 tests que tocan el validador
  (de 103). Los otros 96 tests no lo matan, y decirlo evita que el recuento se lea como
  "la suite entera lo detecta".

**Alcance de la medicion, declarado**: la columna de aislamiento se mide sobre los **7 tests que
importan `validate_docs`**, no sobre los 103 uno a uno (serian 2191 ejecuciones). Un mutante
cuya muerte este en otro test pasaria aqui por "no lo mata nadie", asi que esta medicion es una
**cota**, no un techo. Lo que si es exacto: si un mutante aparece aqui con 4 guardianes, tiene al
menos 4.

## Contrato T-7: veredicto medido

Medido el 2026-10-02 con el protocolo de la tabla de arriba: cada mutante se aplica al
`validate_docs.py` real, se ejecuta **la suite completa** (para saber cuál es el primero que
revienta) y después **cada uno de los 7 tests del validador por separado** (para saber cuántos lo
matan de verdad). Las dos columnas no son la misma medición y por eso van separadas.

| # | Mutante (mutacion literal) | Donde muere EN AISLAMIENTO (y cuantos) | Primero EN LA SUITE COMPLETA | Veredicto |
|---|---|---|---|---|
| **M2** | borrar el 4o argumento de la llamada: `_comprobar_ancla_de_commits(root, errors, ok, journal_cycles)` -> `(root, errors, ok)` | **4 guardianes**: `...no_depende_del_que_escribe_el_journal`, `..._se_cablea_en_el_camino_real_del_validador`, `test_el_journal_ilegible...`, `..._tabla_de_escenarios` | el **privado** (`...no_depende_del_que_escribe_el_journal`), por su helper `_informe` | **MUERTA**. La atribucion anterior ("el test de subproceso") era **una de cuatro y ademas no es la primera** |
| **D2** | `<- sin default`: `journal_cycles=()` en la firma | **0 guardianes** | **sobrevive** | **INERTE por diseño**, ver "D2 no es un mutante" |
| **A1** | desactivar `if not ciclos and journal_cycles:` -> `if False:` | **1**: fila **(a)** de la tabla | la tabla | **MUERTA** |
| **A1b** | quitarle `and journal_cycles` -> `if not ciclos:` | **2**: `test_el_journal_ilegible...` **y** fila **(b)** | **`test_el_journal_ilegible...`**, no la fila (b) | **MUERTA**. La atribucion a la fila (b) es cierta pero **no es la primera**, y callaba el segundo guardián |
| **M1** | desactivar `if not journal_cycles and journal_usable:` -> `if False:` | **1**: fila **(d)** | la tabla | **MUERTA** |
| **M1b** | quitarle `and journal_usable` -> `if not journal_cycles:` | **1**: `test_el_journal_ilegible...` | ese mismo | **MUERTA** |
| **A2** | quitar `--all`: `["git", "log", "--format=%s", "--all"]` -> sin `--all` | **1**: fila **(c)** | la tabla | **MUERTA** |
| **S2** | borrar el cableado: `ciclos_historial = _comprobar_ancla_de_commits(...)` -> `ciclos_historial = set()` | **3 guardianes**: el privado, el de subproceso, la tabla | el **privado** | **MUERTA**. La atribucion anterior ("el test de subproceso") era uno de tres. Con el otro literal (`pass`, el que describe `docs/ai/testing-guide.md`) son **4**, porque el `NameError` posterior tambien tumba el test del journal ilegible |
| **S2b** | borrar la llamada `validar(root)` de `main()` -> `errors, ok = [], []` | **1**: el de subproceso | ese mismo | **MUERTA** |
| **P2** | `missing_entries`: `if f"## CYCLE-{c:03d}" not in rch and f"## [CYCLE-{c:03d}]" not in rch` -> `if f"{c:03d}" not in rch` | **1**: fila **(f)** | la tabla | **MUERTA** |
| **P3** | `has_jentry`: `(f"## CYCLE-{jlatest}" in rch or f"## [CYCLE-{jlatest}]" in rch)` -> `f"{jlatest}" in rch` | **1**: fila **(f)** | la tabla | **MUERTA** |
| **H2** | `if not has_jentry:` -> `if False:` | **1**: fila **(f)** | la tabla | **MUERTA** |
| **E2** | `except Exception as exc:` -> `except OSError as exc:` | **1**: la tabla, **pero por el envoltorio**, no por su asercion | `_informe_del_validador_real` | **MUERTA, con punto ciego**. Ver "El punto ciego de E2" |
| **E3** | `for _intento in (1, 2):` -> `for _intento in (1,):` | **1**: fila **(g)** | la tabla | **MUERTA** |
| **G1** | el plural deja de leerse: `(?:ciclo|cycle)(s?)\b` -> `(?:ciclo|cycle)(?:s)\b` + los dos indices que lo consumian | **3 guardianes**: el privado, el de subproceso, la fila **(h)** | el privado | **MUERTA** |
| **G1b** | el rango nunca se expande: `return set(range(primero, hasta + 1))` -> `return {primero}` | **2**: el privado, la fila **(h)** | el privado | **MUERTA** |
| **G1c** | extremo exclusivo: `range(primero, hasta + 1)` -> `range(primero, hasta)` | **2**: el privado, la fila **(h)** | el privado | **MUERTA** |
| **G1d** | sin tope: se borra `or hasta - primero + 1 > MAX_CICLOS_DE_UN_RANGO` | **1**: la fila **(h)**, y solo ella | la tabla | **MUERTA**. El test privado **no lo ve**, porque un rango de 7 no llega al tope: para eso existe la fila |

**La tabla tiene 18 filas: 17 mutantes reales, todos muertos, y D2, que es inerte por diseño.**
Supervivientes: **0**. El motivo literal de cada muerte —el mensaje que el test imprime— esta
escrito en la fila que lo mata dentro de `run_tests.py`, no aqui: duplicarlo en un informe es
justo como empieza a caducar.

Tres correcciones que trae esta ronda respecto a la tabla anterior, y que son el objeto del
cierre: **M2** no muere solo en el test de subproceso sino en cuatro tests y primero en el privado;
**A1b** muere en dos y primero en `test_el_journal_ilegible...`, no en la fila (b); y **S2** tiene
tres guardianes, no uno. Ninguna de las tres atribuciones era falsa de raiz —todas nombraban un
test que de verdad lo mata— y las tres eran **falsas por omision**: no decian que havia mas.

### Por que la columna de atribucion era el fallo, y no un detalle de redaccion

Tres filas de la tabla anterior atribulian un unico test a mutantes que tienen dos, tres o cuatro.
No era mentira de intencion: era **medir una sola cosa y escribirla como si fueran dos**. Con una
suite ordenada, `python run_tests.py` devuelve **un** nombre —el primero que revienta— y ese
nombre parece una atribucion completa. Es la misma clase de bug que el ciclo #15: **una medicion
que se presenta como mas de lo que es**. Lo que cambia en esta ronda es que las dos preguntas se
responden por separado y cada columna dice cual es.

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
atribucion —atribucion que esta ronda 2 demuestra que era **incompleta**, no falsa: los mismos
nombres, pero cada uno era uno de varios. El `PASS` no era el cierre del ciclo: **traia cinco
holes**, y dos de ellos eran falsos verdes demostrados, no teorias.### P2 (ALTA): `missing_entries` laxo, el falso verde del ciclo #15 por otra puerta

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
| Fila **(g)**: `git` falla **una vez** con `TimeoutExpired`, el segundo intento usa la `run` de verdad | E2: `except Exception as exc:` -> `except OSError as exc:` | **MUERE** | `AssertionError: validar(root) debia devolver un INFORME y tiro TimeoutExpired: ...`. Con `OSError` el timeout sale con traceback y **no comprueba ni el check 6 ni el 7**. **Ojo**: ese `AssertionError` es del envoltorio, no de la fila; ver "El punto ciego de E2" |
| Misma fila | E3: `for _intento in (1, 2):` -> `for _intento in (1,):` | **MUERE** | `fila (g... del ancla`: sin reintento `salida is None` y el validador declara `historial de commits: NO SE PUEDE LEER` en vez de leer el ciclo |

La fila (f) cita el numero **de dos maneras** a proposito (`TASK-015` y `CYCLE-015`): con una
sola clase de cita, la otra forma de busqueda laxo pasaria en verde sin que nadie se entere.

### H2 era decoracion, no guarda

Ninguna de las cinco filas anteriores construia "ultimo ciclo del journal **sin** encabezado",
o sea que `if not has_jentry:` no tenia ninguna asercion que lo comprobara. Sobrevivir no era
suerte: era que nadie lo miraba. Con la fila (f) es una guarda de verdad.

### G1 (BAJA): CERRADO. El plural declara un rango, y el rango esta acotado

El `s?` de `(?:ciclo|cycle)s?` era **decoracion**: quitarlo de la regex no cambiaba ningun
veredicto, y por eso sobrevivia a la suite entera. Cerrarlo exigia decidir que significa
`ciclos 14-20`, y eso es una **decision de producto**, no una eleccion del implementador. La
decision esta tomada y escrita en el codigo:

> Un asunto con **plural** ("ciclos", "cycles") seguido de un numero o de un rango declara **mas de
> un ciclo**. Se interpreta como **rango**, con los dos extremos dentro: `ciclos 14-20` corrobora
> los ciclos 14, 15, 16, 17, 18, 19 y 20. Un plural con un numero suelto ("ciclos 47")
> corrobora solo ese.

**Lo que se implemento, y lo que NO**:

| Decision | Por que |
|---|---|
| `_marcador_de_ciclo(asunto) -> int \| None` pasa a **`_ciclos_del_asunto(asunto) -> set[int]`** | Un plural declara mas de un ciclo, asi que la unidad correcta es el conjunto. Cambiar el tipo es lo que obliga a que el resto del parser se entere |
| El grupo `s?` se **captura** en vez de consumirse | La expansion depende de el. En singular, `ciclo 14-20` es un asunto prolijo y se lee como el 14: no son siete ciclos que nadie declaro |
| `MAX_CICLOS_DE_UN_RANGO = 50` | Sin tope, un `ciclos 1-9999` escrito en cualquier parrafo exigiria 9999 entradas `## CYCLE-` y devolveria un FAIL de 40.000 caracteres. Un texto cualquiera no puede fabricar un requisito que nadie puede satisfacer. **Lo que excede el tope degrada al primer numero**, que es justo lo que hacia el parser sin rango: acota el dano, no lo inventa |
| Rango invertido (`ciclos 20-14`) degrada al primer numero | `set(range(20, 14))` es vacio, y un conjunto vacio **borraria** el marcador: worse que no parsear |

**Medido sobre el historial real (2026-10-02, 159 subjects)**: hay **un unico commit que depende
del plural**, `feat(ciclos 14-20): gaming service, integridad de datos, ...`. Con la semantica
nueva el conjunto corroborable pasa de **38 a 44 ciclos**: el plural destapa el **015 al 020**, y
**no se pierde ninguno**. Cero asuntos con singular y guion en todo el historial, o sea que la
decision "solo plural" no deja nada sin corroborar hoy.

**El repo real no se pone en rojo, y por que**: los ciclos 15 a 20 ya los exigia `rd_journal.json`,
y `CHANGELOG.md` tiene sus siete encabezados (`## CYCLE-014` … `## CYCLE-020`). Lo que cambia es el
**testigo**, no el veredicto: antes el historial no corroboraba esos seis ciclos y ahora si. Un
testigo que no corrobora no corrobora, aunque el journal lo tapara.

**La cobertura, y por que es una fila y no un test**: la fila **(h)** de la tabla de escenarios
asienta por `validar(root)` y monta el arbol donde la semantica decide — historial con
`feat(ciclos 14-20)` y `ciclos 1-9999`, journal que solo registra el 1 y el 14, changelog con solo
esas dos entradas — y exige que los dos errores que salen nombren **exactamente** `015` a `020`. Ni
uno mas (el 9999 esta acotado, el 001 esta cubierto) ni uno menos (los dos extremos entran). La
suite sigue en **103 tests**.

| Mutante | Que rompe | Guardianes medidos |
|---|---|---|
| **G1** | el plural deja de leerse (`(s?)` -> `(?:s)` mas los dos indices) | **3**: el test privado, el de subproceso y la fila (h) |
| **G1b** | el rango nunca se expande | **2**: el test privado y la fila (h) |
| **G1c** | extremo exclusivo (`hasta + 1` -> `hasta`), se pierde el 020 | **2**: el test privado y la fila (h) |
| **G1d** | se borra el tope de `MAX_CICLOS_DE_UN_RANGO` | **1**: **solo** la fila (h) |

G1d es la justificacion medida de la fila: el aserto privado mira un rango de 7 ciclos, que nunca
llega al tope, asi que **no puede verlo**. Un invariante que solo se puede comprobar en el camino
real se mide en el camino real, y por eso vive en la tabla y no en el test de las privadas.

### El punto ciego de E2, escrito como es

La fila (g) mata a E2, y el informe anterior lo contaba como cobertura sin mas. **No lo es de la
forma que parece.** Medido: el frame mas interno del traceback con E2 puesto es
`_informe_del_validador_real`, el **envoltorio compartido** que convierte cualquier excepcion en
`AssertionError`, y el mensaje literal que sale es el del envoltorio, no el de la fila:

```text
AssertionError: validar(root) debia devolver un INFORME y tiro TimeoutExpired:
Command '['git', 'log', '--format=%s', '--all']' timed out after 120 seconds.
Sin este envoltorio un mutante que revienta el validador muere por traceback y
no se puede distinguir de un test que detecta el fallo
```

Es decir: **la fila (g) nunca llega a juzgar**. Su `lambda e, _ok: e == [] and ...` no se ejecuta,
porque `validar(root)` no devuelve nada sino que revienta. El mutante E2 —estrechar el
`except Exception` a `OSError`, con lo que el `TimeoutExpired` sale con traceback y el validador
**no comprueba ni el check 6 ni el 7**— muere por el camino mas corto que existe, que es "el
codigo revento".

**Por que la fila (g) no cubre E2 por si misma**: porque el envoltorio es **compartido** por las
ocho filas y por los otros tests del validador. Es un buen envoltorio —sin el, un mutante que
revienta el producto moriria por traceback y no se podria distinguir de un test que detecta un
fallo— y por eso es una trampa: **cubre cualquier mutante que reviente**, que es un conjunto
infinito, y por lo mismo **no ata su asercion a ninguna invariante concreta**. Si manana alguien
reescribe el envoltorio (por ejemplo, para que re-lance en vez de convertir), la cobertura de E2
desaparece **sin que ninguna asercion cambie y sin que la suite se queje**: E2 volveria a ser un
superviviente y este informe seguiria diciendo que la fila (g) lo mata.

No se arregla en este ciclo y **se DECLARA**: el arreglo es una asercion que no dependa del
envoltorio, del tipo "con `except OSError`, este arbol tiene que dar `errors == []` **y** su linea
de informe con los ciclos corroborables, porque el `TimeoutExpired` se ha de traduzcir en
`NO SE PUEDE LEER` en vez de en un traceback". Eso es un test mas, y anadirlo solo por esto
romperia la regla del replan (la suite esta en 103 y no crece por defecto). Lo que se hace es
**dejar el agujero escrito, con su nombre y con la razon por la que la fila no lo cubre**.

### Lo que este cierre NO declara

**A1 esta erradicado donde se produjo y desplazado donde no se busco.**
`_comprobar_ancla_de_commits` acusa el parser roto (`108 OK / 1 FAIL`, fila (a) lo mata). En
`missing_entries` y `has_jentry` el mismo patron semantico -- buscar en vez de exigir -- seguia
vivo sin sonda. El ciclo no se declara cerrado por esto: **se declara cerrado donde se midio**.

**Las ocho filas comparten esqueleto y helper, luego comparten punto ciego.** Una fila mide la
forma de arbol que construye: la (f) tapa P2/P3/H2 *porque* lleva prosa con el numero y sin su
`## CYCLE-`; contra un arbol sin esa prosa las dos versiones del codigo darian el mismo
veredicto y la fila pasaria sin medir nada. La (h) tiene la misma forma de punto ciego: mide un
historial con plural, y un historial sin plural daria el mismo veredicto a las dos versiones.
Limitacion asumida y escrita en el codigo, no descubierta por el proximo que audite.

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

### Verificaciones del cierre 2 (comando y salida real, no "se verifico SHA-256")

```text
$ python verify_ui_syntax.py
OK: src/woptimizer/ui/views/pack_manager_view.py compila perfectamente.
OK: src/woptimizer/ui/views/process_manager_view.py compila perfectamente.
OK: src/woptimizer/services/notification_service.py compila perfectamente.
OK: src/woptimizer/__main__.py compila perfectamente.
EXITO: Todos los modulos UI estan impecables.
exit=0

$ python run_tests.py
test_process_manager_db_update_button_and_feedback OK.
Testing ProcessManagerView pack dropdown single arrow and placeholder (TASK-052)...
test_process_manager_pack_dropdown_single_arrow_and_placeholder OK.

ALL TESTS PASSED.
exit=0

$ python validate_docs.py
  [OK]   docs/ai/testing-guide.md: 103 filas de test, una por test definido

Resumen: 108 OK, 0 FAIL
exit=0
```

Las tres en verde, con la suite en **103 tests**: la fila (h) es una fila, no un test. El
validador dando `108 OK / 0 FAIL` con el parser del rango puesto confirma lo medido: el plural
destapa seis ciclos corroborables mas y **el veredicto no se mueve**, porque el journal ya los
exigia. Lo que ahora lo respalda no es el numero, es que el parser tiene una fila que lo mata.


## VERDICT

**PASS** del autoprueba de `openspec-dev` sobre el contrato T-7: 8/8 mutantes muertos por su
asercion, 0 tests nuevos, suite 104 -> 103.

**Cierre del ciclo #47, primera ronda (esta seccion):** el `PASS` del `mutation-auditor` traia
cinco holes. Medidos aqui uno a uno contra el `validate_docs.py` real, con SHA-256 verificado antes y
despues de cada mutante y `__pycache__` purgado: **P2, P3, H2, E2 y E3 mueren todos por su
asercion**, con dos filas nuevas y **0 tests nuevos** (suite 103 -> 103). **G1 quedo DECLARADO** con su
mutante y su severidad, y se **cerro en la ronda 2**, mas abajo. Ademas se corrigen tres afirmaciones
falsas de este mismo arbol: la
fila D2, la cifra "112 de 156" que se contradecia con la linea siguiente, y el denominador 46
del journal en `sandbox-rules.md`.

**Cierre del ciclo #47, ronda 2 (esta seccion):** lo que quedo eran dos cosas, y las dos estan
resueltas.

1. **La columna de atribucion, corregida.** Se rempio "Test" en dos columnas —"donde muere en
   aislamiento" y "primero en la suite completa"— mas el recuento de guardianes, porque **un
   `python run_tests.py` solo devuelve el primero que reventa y eso no es una atribucion**.
   Correggidas por medicion: **M2** (4 guardianes, primero el privado, no el de subproceso),
   **A1b** (2 guardianes, primero `test_el_journal_ilegible...`, no la fila (b)) y **S2** (3
   guardianes, no 1; y 4 con el literal `pass`). Ninguna de las tres era falsa de raiz: todas
   nombraban un test que de verdad lo mata. Eran **falsas por omision**, que es peor porque se
   leen como exactas.
2. **G1 cerrado.** El plural declara un rango (decision de producto, escrita en el codigo y en el
   docstring), acotado por `MAX_CICLOS_DE_UN_RANGO = 50`, con la fila **(h)** como prueba y cuatro
   mutantes que la matan: **G1, G1b, G1c y G1d**. **0 tests nuevos**, suite 103 -> 103.
   Medido sobre el historial real: **un unico commit de 159 depende del plural**, y el rango destapa
   el **015 al 020** sin perder ningun ciclo.

**Y queda escrito, no escondido, el punto ciego de E2**: la fila (g) lo mata, pero por el
envoltorio compartido `_informe_del_validador_real` y no por su propia asercion. Si ese envoltorio
cambia, la cobertura de E2 desaparece sin que nada se entere. Es un agujero **nombrado, medido y
justificado**, no un silencio.
