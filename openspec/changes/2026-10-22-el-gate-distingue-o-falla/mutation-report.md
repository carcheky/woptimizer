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
WOPT_VEREDICTO M-90 MUERTO 7bd6bee8b3b811a3965b39a66c595ac925645ce5
WOPT_VEREDICTO M-91 MUERTO 4230906e8d9f6ddabed0172738cc45c7be643621
WOPT_VEREDICTO M-92 MUERTO fa8650e4c7e466ab1ee03a0c9ac0acb35c5e0277
WOPT_VEREDICTO M-93 MUERTO 9a40e93795a3f5c5a8c58d0bf3d3a9aa5cfced64
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
