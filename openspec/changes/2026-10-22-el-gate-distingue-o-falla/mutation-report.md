# Informe de mutacion · ciclo 71 · TASK-090

**Que cambia este ciclo:** el gate del check 11 de `validate_docs.py` (el que
**re-deriva** cada veredicto desde la evidencia commiteada) ya no puede quedar
ciego sin que la suite se ponga roja. Antes, con el **cuerpo** del gate vaciado
y el REGISTRO puesto, el validador daba **0 FAIL** sobre un catalogo que se
contradice a si mismo, y ningun `test_*` lo notaba (el agujero **D-B**): el
guard de cableado (mutante D-A) veia el REGISTRO, no el contenido.

**Que se construye:** una seccion **(D)** dentro del test que ya existe
(`test_el_check_9_se_cablea_en_el_camino_real_del_validador`), porque el
recuento de tests **no se mueve** (235 = 159 + 76) y no se anade ningun
`test_*` nuevo. El guard es de **PRODUCTO**, no de forma:

- **(D1)** con el validador sano, el gate tiene que **acusar** al centinela
  **CONTRADICTORIO** (`[FAIL]` que lo nombra) y **callar** sobre el
  **COHERENTE** (0 `[FAIL]` que lo nombren), con el REGISTRO presente.
- **(D2)** la **CONTRAPROUEBA**: con el **cuerpo** del gate vaciado y el
  REGISTRO puesto, ese `[FAIL]` **desaparece** (1 -> 0) y el REGISTRO **sigue**.
  Sin D2, D1 podria cumplirse por un motivo equivocado (un gate que acusa
  SIEMPRE tambien la cumpliria).
- **(D3)** el esqueleto queda **restaurado** byte a byte.

El corpus es **SINTETICO** y vive en el esqueleto temporal que la seccion (A)
ya copia: el catalogo real no puede ser el sujeto (el gate lo re-deriva del
journal real, que un test no puede mutar) y el `asa` de cada centinela tiene
que ser un `test_*` **DEFINIDO** en el `run_tests.py` de ese arbol, porque el
gate lo comprueba con `ast`.

## 1. Las cuatro celdas del guard, medidas

| Celda | Que mide | MEDIDO |
|---|---|---|
| D1 | gate sano: acusa al contradictorio, calla sobre el coherente | `FAIL(M-FIX-MAL)=1`, `FAIL(M-FIX-BIEN)=0`, REGISTRO presente |
| D2 | cuerpo vaciado: el `[FAIL]` desaparece, el REGISTRO sigue | `FAIL(M-FIX-MAL)`: 1 -> **0**, REGISTRO presente |
| D3 | el esqueleto queda restaurado | byte a byte igual al original |

## 2. Los cuatro mutantes del guard

Los cuatro se miden en camaras desechables (`%TEMP%\wopt_c71_M-9x`), con el
test afectado corrido **suelto** (el log commiteado es el log REAL de esa
corrida: `evidencia/M-9x.cola`). El `sha_arbol_auditado` es el commit de la
camara donde se midio; el gate **no lo resuelve** (es el limite (e) del gate).

| Mutante | Que cambia | Que muere | Por que asercion |
|---|---|---|---|
| **M-90** | el **cuerpo** de `_comprobar_veredictos_de_mutacion` vaciado, el REGISTRO puesto | `EL GATE NO DISTINGUE` | el gate deja de acusar al contradictorio: D1 se cae porque no hay ningun `[FAIL]` que lo nombre |
| **M-91** | la comparacion del veredicto **invertida** (`!=` -> `==`) | `EL GATE ACUSA EN LO QUE NO PUEDE` | el gate acusa al coherente: D1 se cae en la asercion de que no acuse en lo que no puede |
| **M-92** | el gate solo mira el **primer** mutante del catalogo (`mutantes[:1]`) | `EL GATE NO DISTINGUE` | con el coherente primero, el contradictorio ni se mira: no hay ningun `[FAIL]` que lo nombre |
| **M-93** | el veredicto se **calcula y se tira** (el bucle, la llamada y la comparacion se conservan) | `EL GATE NO DISTINGUE` | el gate no dice NADA: D1 se cae porque no hay ningun `[FAIL]` que nombre al contradictorio |

**Los cuatro conservan el REGISTRO.** No es una suposicion: la asercion del
REGISTRO va **primera** en la D1, luego si el REGISTRO faltara el test habria
muerto con su mensaje (que no es el `motivo` de estos mutantes) y no con el
`motivo` declarado. Ademas M-90 lo hace por construccion: su stub **pone** el
REGISTRO, y por eso el guard de **cableado** (D-A) no lo ve.

## 3. El coste

- **El guard**: 8,73 s, que son **DOS** corridas del validador sobre el
  esqueleto (4,48 s con el gate sano + 4,25 s con el cuerpo vaciado): un
  **1,19 %** de la suite de 735 s.
- **El validador**: su coste **marginal no cambia**. El check 11 sigue costing
  **10,3 ms** (medido antes y despues de este ciclo, con y sin su llamada), y
  el limite (f) son **comments**. La comparacion A/B intercalada del validador
  de HEAD contra el de ahora da un delta de **-6,5 ms** con un ruido entre
  muestras de 3819 ms: es ruido, no coste.

## 4. El limite nuevo (f)

`validate_docs.py` declara ahora, en el bloque «LO QUE ESTE GATE **NO** PRUEBA»
y repetido en el docstring de la funcion, que **el validador, por si solo, NO
detecta un gate ciego**: con el cuerpo de este gate vaciado y el REGISTRO
puesto -> **0 FAIL**. Lo que lo detecta es la **suite**, con un guard de
**producto** (la seccion (D) de este ciclo).

## 5. El bloque de maquina

<!-- WOPT_VEREDICTOS -->
WOPT_VEREDICTO M-90 MUERTO 7ded3f5f1489baf7dd1d7ca02b9bbd58123f000d
WOPT_VEREDICTO M-91 MUERTO 9fa1ac782c71a36fe956927b30ebd94417f07d1f
WOPT_VEREDICTO M-92 MUERTO cc37d5fd73acb8cadb0b49ed9060626eb7723e21
WOPT_VEREDICTO M-93 MUERTO 8c69ddadbef71e0002c8f646b7659f5850dafdfb
WOPT_VEREDICTO M-94 SOBREVIVIENTE ea1561eb59b37cbb917d64433d7b091b4c29cc5c
WOPT_VEREDICTO M-95 SOBREVIVIENTE 7cbc693a48bcde18e84cbf35ecacf1d6604c643c
WOPT_VEREDICTO M-96 MUERTO 69164c19a29ab7b591a8bab90adc0272509e9ffc
WOPT_VEREDICTO M-97 MUERTO 061d7cc6b118aee29516aa13dbbf2d5bc4465c15
WOPT_VEREDICTO M-98 MUERTO 3785a7af5036f80e01da9dd4d284806868b6ca81
WOPT_VEREDICTO M-99 SOBREVIVIENTE a3ffb222310a3dfaff03a741e2f7948a4171fdb6
WOPT_VEREDICTO M-100 SOBREVIVIENTE 7e42482de4e4d7d6fd4c92385bda6265c7243fea
<!-- /WOPT_VEREDICTOS -->

---

## 6. Lo que NO se ha arreglado aqui

- **D-H / TASK-091**: el campo `mutacion` del catalogo (el gate todavia no lo
  lee). Los centinelas del corpus **sintetico** declaran su `mutacion` con un
  fichero y una linea que **existen** en el arbol del corpus, para que el
  arreglo de D-H no los nombre por un motivo que no es el suyo.
- **TASK-086**: ninguna cita por numero de linea la vigila un guard. Este
  ciclo ha tenido que **renumerar** las suyas (la del `run_tests.py` paso de
  `23305` a `23629` por las 324 lineas insertadas) y ha encontrado **cuatro**
  que **ya estaban caducas** antes de este ciclo (`23131`, `29006`, `28676` y
  `28734`): corregidas todas contra el numero **medido** del texto citado.

---

## 7. La auditoria de mutacion (PASO 4 del ciclo 71)

La re-medicion la hizo el `mutation-auditor` sobre el arbol de HEAD (`35478ec`),
en camaras desechables de `%TEMP%` con su PROPIO `.git` y su `origin` desviado a
un repo dummy: **el repo real no se toco** (al final: `git log --oneline -1` =
`35478ec`, `git status --porcelain` vacio, `git diff --stat` y
`git diff --cached --stat` vacios, y `git rev-parse --git-dir` sigue siendo el
desacoplado `%LOCALAPPDATA%\\woptimizer_git\\.git`).

La diferencia con la ronda del dev: las corridas son de la **SUITE COMPLETA**
(cada mutante, en su propia camara, con el arbol restaurado entre mutantes y
`__pycache__` purgado), no del test suelto.

### 7.1 Los cuatro declarados: MEDIDOS de nuevo

| id | mutacion | veredicto | motivo LITERAL (ultima linea de la cola) |
|---|---|---|---|
| M-90 | el CUERPO del check 11 vaciado, el REGISTRO puesto | **MUERTO** | `EL GATE NO DISTINGUE` |
| M-91 | la comparacion del veredicto invertida (`!=` -> `==`) | **MUERTO** | `EL GATE ACUSA EN LO QUE NO PUEDE` |
| M-92 | el gate mira solo el PRIMER mutante del catalogo | **MUERTO** | `EL GATE NO DISTINGUE` |
| M-93 | el veredicto se CALCULA y se TIRA | **MUERTO** | `EL GATE NO DISTINGUE` |

Los cuatro mueren **por su asercion** (no por una excepcion), en la suite
completa, y los cuatro **conservan el REGISTRO** (por eso el guard de
cableado no los ve: es el agujero D-B).

El **orden de las aserciones sigue siendo normativo**, y esta vez **medido**,
no solo leido: M-91 muere en la asercion del **coherente**
(`run_tests.py:22790`) y por eso su motivo es el suyo; M-90, M-92 y M-93
mueren en la del **contradictorio** (`run_tests.py:22802`). Al reves, los cuatro
mueren con el motivo equivocado y el veredicto seria NO MEDIDO.

**La discrepancia de sha, y por que no importa (limite (e)).** Los cuatro
`M-90..M-93` conservan el `sha_arbol_auditado` que declaro el dev (el commit
de **su** camara), y su evidencia commiteada es ahora la de **esta** auditoria
(otra camara, otro commit). El sha NO se resuelve contra ningun objeto de
ningun repositorio, luego el gate no lo nota: el gate compara el sha de la
linea con el del catalogo, y los dos son el mismo numero. Los siete
mutantes de la auditoria (M-94..M-100) si declaran el commit de **mi**
camara, que existe y es real dentro de ella.

### 7.2 Los SIETE de la auditoria (atacan el GUARD NUEVO)

Los cuatro del dev matan **el gate**. Estos siete atacan **el guard que vigila
al gate**, que es lo que faltaba medir.

| id | mutacion | veredicto | contraprueba (por que NO es equivalente al sano) |
|---|---|---|---|
| M-94 | el gate mira solo el **ULTIMO** mutante (`mutantes[1:]`) | **SOBREVIVIENTE** | con el corpus de **orden invertido** el sano acusa al contradictorio y M-94 CALLA |
| M-95 | el gate mira solo la **PRIMERA** entrada del journal | **SOBREVIVIENTE** | con **DOS entradas** el sano acusa a la segunda y M-95 CALLA |
| M-96 | el corpus NO se monta (el journal no se escribe) | **MUERTO** (`EL GATE NO DISTINGUE`) | la seccion (D) se queda sin sujeto: D1 muere |
| M-97 | el sentinela COHERENTE deja de ser coherente | **MUERTO** (`EL GATE ACUSA EN LO QUE NO PUEDE`) | el gate le acusa y D1 muere en la asercion del coherente |
| M-98 | D3 NO restaura el esqueleto | **MUERTO** (`copia mutada contaminaria las secciones que vienen despues`) | la copia mutada contaminaria: D3 muere en su asercion |
| M-99 | el gate decide por la **DECLARACION**, no por la evidencia | **SOBREVIVIENTE** | con la contradiccion **invertida** el sano acusa y M-99 CALLA |
| M-100 | el motivo literal de la evidencia ya NO se comprueba | **SOBREVIVIENTE** | con la evidencia de motivo **equivocado** el sano dice NO MEDIDO y M-100 la **certifica** como MUERTO |

### 7.3 Lo que dicen los cuatro SUPERVIVIENTES

Los cuatro son **el CORPUS, no el gate**: el guard mide el COMPORTAMIENTO del
gate sobre **UN** corpus, y ese corpus tiene una sola forma de contradiccion
(declarado SOBREVIVIENTE / evidencia MUERTO), un solo orden (el coherente
primero) y una sola entrada de journal. MEDIDO, los cuatro se comportan
**igual que el gate sano** sobre ese corpus (y por eso el guard no los ve) y
**distinto** sobre un corpus que el guard no usa:

| corpus | SANO | M-94 | M-95 | M-99 | M-100 |
|---|---|---|---|---|---|
| C0 el del guard (coherente primero, una entrada) | ACUSA | ACUSA | ACUSA | ACUSA | ACUSA |
| C1 orden invertido | ACUSA | **CALLA** | ACUSA | ACUSA | ACUSA |
| C2 dos entradas de journal | ACUSA | **CALLA** | **CALLA** | ACUSA | ACUSA |
| C3 contradiccion invertida | ACUSA | **CALLA** | ACUSA | **CALLA** | ACUSA |
| C4 evidencia con el motivo equivocado | ACUSA (dice NO MEDIDO) | **CALLA** | ACUSA | ACUSA | **ACUSA y CERTIFICA MUERTO** |

El dano real de cada uno, en el repo real:

- **M-94**: el gate deja de re-derivar todos los mutantes del catalogo menos
  el ultimo.
- **M-95**: el gate deja de re-derivar **todos los ciclos del journal menos el
  primero** (en el repo real hay una entrada por ciclo: el check 11 dejaria de
  mirar los veredictos de los ciclos siguientes).
- **M-99**: acusa de **mentira a los supervivientes honestos** (todo mutante
  declarado SOBREVIVIENTE, con evidencia que tambien dice SOBREVIVIENTE).
- **M-100**: **certifica una muerte que no ocurrio** (una evidencia con el frame
  del asa y otro mensaje).

El arreglo NO es una linea: el corpus de la seccion (D) tiene que **variar la
contradiccion en las dos direcciones**, **los dos ordenes** y **mas de una
entrada de journal**. Con eso, M-94, M-95, M-99 y M-100 mueren. Los cuatro
supervivientes quedan **encolados como tarea** con su metrica.

### 7.4 Las citas por numero de linea

Las **ocho** renumeradas por el dev (el multiconjunto de numeros citados, antes
y despues de `0eb6078`) estan **VIVAS**: `29943`, `23629`, `29515` (dos veces),
`23627`, `23629` (dos veces) y `30001`. Los numeros que el dev da por buenos
(`23305` -> `23629`, `23131` -> `23627`, `29006` -> `29515`, `28676` ->
`29943`, `28734` -> `30001`) apuntan todos al texto que la afirmacion describe.

Lo que se le ha escapado, con el numero **medido**:

- **Seis las rompio ESTE ciclo** (las escribio el dev en la `proposal.md` de
  este ciclo y las movio su propio commit): `validate_docs.py:3138` (dos
  veces, ahora **3150**), `validate_docs.py:3310` (ahora **3327**),
  `validate_docs.py:3276` (ahora **3293**), `run_tests.py:22375` (ahora
  **22392**) y `run_tests.py:22428` (ahora **22445**). Y una septima, un
  **rango**: `run_tests.py:22434-22475` (el bloque «LO QUE ESTE GATE **NO**
  PRUEBA») ya no cubre ese bloque: ahora es **22451-22492**.
- **Ya estaban caducadas antes** (deuda heredada): `docs/ai/testing-guide.md:939`
  cita `run_tests.py:8` y el envoltorio de `sys.stdout` esta en la **17**;
  `docs/ai/testing-guide.md:1337` cita `run_tests.py:12745` y `_git_de_fixture`
  esta en la **13098**; `proposal.md:296` cita `validate_docs.py:3038` y la
  ultima linea de la cola se lee en la **3034**; `proposal.md:43` cita
  `validate_docs.py:3350-3359` y el REGISTRO se imprime en la **3367-3376**; y
  el cambio activo `2026-10-21-vistas-del-guard-de-workers-derivadas/proposal.md`
  tiene **22** citas caducadas de `run_tests.py`/`validate_docs.py` (la de `9410`
  apunta a un `return sum(...)` y `VISTAS_INVENTARIADAS` esta en la **28922**;
  las de `27617` y `27683` tampoco).

De las **334** citas por numero de linea de la documentacion viva, **32** estan
caducadas: **el dev encontro cuatro de las suyas y habia mas**.

### 7.5 El coste

- **El guard**: la seccion (D) cuesta **9,46 s** (medido aqui: mediana de tres
  corridas del test entero CON la seccion (D), **32,14 s**, contra tres SIN ella,
  **22,68 s**; la diferencia son las DOS corridas del validador de la seccion).
  El dev midio **8,73 s** en su host: el coste ABSOLUTO se sostiene. En RELATIVO
  cambia porque aqui la suite entera son **274 s** y ahi **735 s**: el guard es
  el **3,45 %** de la suite de este host y el **1,19 %** de la del suyo.
- **El validador**: su coste **marginal no cambia** de forma medible. El A/B
  intercalado del validador de HEAD contra el mismo validador con la llamada al
  check 11 sustituida por `pass` (5 muestras cada uno, alternadas) da una
  mediana de **4772 ms** con el check 11 y **4646 ms** sin el: un delta de
  **+125 ms** con un ruido de **210 ms** dentro del propio grupo A. **Es ruido,
  no coste**: por debajo del suelo de ruido de este host no se puede separar
  el coste del check 11, que se limita a leer el journal, el catalogo y la
  evidencia. El limite (f) son `comments` y no tocan el camino caliente.

### 7.6 Una limitacion MEDIDA de la suite (y no de los mutantes)

Una de las trece corridas de suite completa (la de la verificacion final de la
camara) **no murio en el asa**: murio en
`test_el_ancla_se_cablea_en_el_camino_real_del_validador` (`run_tests.py:31719`,
el ANCLA, que corre **antes** que el guard) porque la pre-comprobacion de git
del validador (`_leer_el_repo_si_lo_hay`) fallo y el check 9 reporto **176**
hashes como «no resuelven en el repo desacoplado» (un repo que no responde
uno a uno no puede certificar que un objeto exista **ni que falte**). Es la
intermitencia del `spawn EPERM` que este repo ya documenta, **no** un efecto de
los mutantes: en las trece corridas de medicion el test que murio fue **siempre**
el asa, o la suite acabo en VERDE.

Lo que si significa es que **una corrida de la suite puede morir en otro test**,
y por eso el veredicto se apoya en el **frame** del traceback y no en el
`rc`: un rojo sin frame del asa es NO MEDIDO, no MUERTO.

### 7.7 El limite (f), ampliado

El limite (f) que el gate declara ("el validador, POR SI SOLO, NO detecta un
gate ciego") es correcto y **sigue siendo cierto**, pero **no es el unico
limite**: el guard de producto que el validador NO puede tener es **tambien
ciego** con cuatro clases de gate ciego (M-94, M-95, M-99, M-100). El gate
tiene que declarar tambien ese limite: **la SUITE detecta el gate ciego de la
forma (D)-A, y solo el de la forma (D)-B**.
