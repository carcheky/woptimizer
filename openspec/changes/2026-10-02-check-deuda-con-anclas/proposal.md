# Check 8 de `validate_docs.py`: las filas VIVAS de la Deuda Tecnica Conocida con ancla resoluble

**Change ID:** `2026-10-02-check-deuda-con-anclas`
**Tarea:** `TASK-060` (ciclo #49)
**Alcance:** `validate_docs.py` (check 8 nuevo + reparto en el check 7), `run_tests.py` (un test), `docs/ai/sandbox-rules.md`, y **una fila** de `STATUS.md`.
**NO toca:** `src/woptimizer/**`. Cero cambios de codigo de producto.

---

## 1. Que se arregla

El ciclo #48 sano 13 filas de `## ⚠️ Deuda Tecnica Conocida` y las tres falsas las corrigio **conservando su redaccion**. El `mutation-auditor` cerro el ciclo con **PARTIAL**, y la razon es medida, no supuesta: **8 de 9 mutaciones sobreviven porque nada en este repo vigila esa seccion**. `validate_docs.py` tiene **0** coincidencias de la palabra `Deuda` y menciona `STATUS.md` **una sola vez** (`validate_docs.py:116`, la lista del recuento de tests).

`TASK-060` es el arreglo de fondo de ese PARTIAL.

---

## 2. Tres premisas del encargo que la medicion REFUTA

Medido el 2026-10-02 con `ast` y con lectura directa del panel. No son opiniones:

| Premisa del criterio escrito en `STATUS.md:101` | Medido | Veredicto |
|---|---|---|
| «De las 15 filas, 8 llevan `CERRADA` y 7 no: **87, 88, 90, 91, 94, 97 y 99** no lo llevan» | Las 7 que **no** lo llevan son **88, 89, 91, 92, 95, 98, 100 y 101** (8 filas, no 7) | **FALSA en 6 de 14 entradas.** La lista escrita mete como «sin marcador» a 87, 90, 94 y 97, que si lo llevan, y se come a 89 (la 🔴 del `spawn EPERM`), 92, 95, 98, 100 y 101. La propia fila lo admite («esta enumeración es ILUSTRATIVA, no normativa»): el save estaba bien, la cuenta no |
| «Bajo la lectura estricta fallan dos: la **87** y la **94**; la 94 es la única con cero referencias a fichero» | La 87 cita **4 ficheros que existen**; la 94 cita `validate_docs.py:238` y `:267`, y **ambos son exactos hoy** (`_ciclos_de_commits` y `_comprobar_ancla_de_commits` siguen esas lineas) | **FALSA.** La unica fila viva sin ninguna ruta que resuelve es la **91** (su unico nombre de fichero es `profiles.json`, que es dato de usuario y no esta en el arbol). Ademas la 95 no cita ruta alguna pero si cita `TASK-059` |
| «una cita `fichero:linea` a un fichero que crece por arriba se caduca sola» (**6 citas desviadas, 160-1270 lineas**) | De las 49 citas de la seccion, las que nombran una funcion o un test son **exactas**: `run_tests.py:12348` = `def test_el_ancla_sobre_un_arbol_sintetico_tabla_de_escenarios():`, `:12381` = la linea de «LAS OCHO FILAS», `docs/index.md:25` = «(103 tests)», `validate_docs.py:238`/`:267` exactas. Lo que **si** esta desviado es el bloque **intra-panel** de la fila 101, y esta desviado **por una unidad**: dice que la fila del `.git` es la 87, que el `spawn EPERM` es la 88, que el residuo es la 94 y que `docs/index.md` es la 99, cuando son **88, 89, 95 y 100** | **La regla se confirma y se corrige la causa**: no caduca por crecimiento, caduca por **insercion**. Y el error **ya salio del panel**: `docs/ai/sandbox-rules.md:120` cita «la fila del `spawn EPERM` de `STATUS.md:88`», y esa fila esta en la **89**. El numero de linea es informacion para el humano; verificarlo es garantizarse un rojo sin motivo |

Las tres premisas caidas en el mismo sitio: **el panel se cita a si mismo por numero de linea, y el numero de linea es la parte que caduca.**

---

## 3. Diseno del check 8

**Nombre:** `_comprobar_deuda_con_anclas`
**Firma:** `_comprobar_deuda_con_anclas(root, errors, ok)` — tres posicionales, **sin defaults** y **sin parametros extra**: todo se vuelve a derivar de `root`, igual que hacen `_comprobar_recuento_de_tests` (ciclo 27) y `_comprobar_ancla_del_changelog` (ciclo 47). Es lo que permite construir el residuo en un test con un arbol sintetico en `tempfile.mkdtemp()`, y con un default un cableado roto se convierte en un `None` silencioso (la clase de fallo que D1 ya cerro una vez).

**Cableado:** una linea, en `validar(root)`, justo **despues** de `_comprobar_recuento_de_tests(root, errors, ok)` (`validate_docs.py:714`) y **antes** de `return errors, ok` (`validate_docs.py:715`). Es el **check 8** por orden de llamada, y su linea de `ok` imprime el recuento de filas que el resto del informe puede contrastar.

**Auxiliares con raiz** (mismo motivo que los dos de arriba: una guarda que solo se despierta lanzando el validador entero contra el repo entero es una guarda que nadie ejecuta):

- `_filas_de_deuda(cuerpo) -> [(int, str)]` — porcion desde el encabezado `## ` que contiene `Deuda` hasta el siguiente `## `; filas = lineas que empiezan por `- **`.
- `_esta_cerrada(fila) -> bool` — `re.search(r"CERRAD", re.sub(r"`[^`]*`", " ", fila))`.
- `_anclas_resolubles(root, fila) -> dict` — `{"rutas": [...], "contenido": [...], "tareas": {id: status}, "ciclos": [...], "numeros": [...]}`.
- `_severidad_minima(anclas) -> str` — `""` o `"ROJO"`.

### 3.1 El marcador de cierre (P1 corregida, y endurecida tras el FAIL)

Una fila esta **CERRADA** si, **tras eliminar los tramos de codigo inline** (`` `...` ``), contiene el literal `CERRAD` en **mayusculas**.

Medido: **7 exentas** (87, 90, 93, 94, 96, 97, 99) y **8 vivas** (88, 89, 91, 92, 95, 98, 100, 101).

**Lo que resuelve el bucle de autorreferencia** es precisamente quitar el codigo inline antes de buscar: la fila 101 lleva `CERRAD` **solo dentro de comillas invertidas**, porque esta *escribiendo* el criterio. Sin esa limpieza el panel se declararia cerrado a si mismo. Con ella, la fila del criterio se declara **VIVA**, que es lo correcto: declara `TASK-060`.

**ENDURECIDO en el cierre del ciclo #49, y el motivo es un FAIL medido.** Con el marcador de una sola palabra, la fila 89 se **eximia a si misma** con cualquier frase normal que hablara de cierre -- "y esta fila NO esta CERRADA todavia", o un `(marcada *CERRAD*)` al final -- y el validador respondia `115 OK / 0 FAIL`. Una palabra suelta no es un veredicto. Ahora son **cuatro** condiciones a la vez, y las cuatro se cumplen en las 7 exentas reales **sin tocar ninguna fila**: (1) `CERRAD` en mayusculas **fuera de codigo inline**; (2) dentro de un **veredicto en negrita**; (3) la fila nombra un id **trazable** (`TASK-NNN` o `CYCLE-NNN`) que existe; (4) el veredicto **no niega** el cierre. Las cuatro fallan ABIERTO: lo que no demuestra su cierre queda VIVA y tiene que demostrar su ancla. El residuo que queda, medido y escrito, es el **5 de `docs/ai/sandbox-rules.md`**: un cierre falsificado con la forma completa del veredicto sigue eximiendo si la fila ya cita ids resolubles.

**Descartado, con numero:**

| Candidato | Medido | Por que se cae |
|---|---|---|
| Prefijo en el offset 0 (P1 tal como esta escrita) | **0 de 15 filas** lo tienen | Obligaria a reescribir las 15 filas. No se adopta |
| Buscar `cerrad` sin distinguir mayusculas | **13 de 15** filas casan, incluidas las tres vivas mas importantes | Marca cerrada la 88 («ciclo cerrado sin commit»), la 94 («Declararlo cerrado seria repetir el fallo») y la propia 101. Un check que exime tres filas vivas nace verde sobre lo que tiene que vigilar |
| Opt-in por fila | — | Ver seccion 5 (c) |

### 3.2 Que es un ancla resoluble

Cinco fuentes de verdad, **todas fuera del panel**. Una fila viva es valida si resuelve **al menos una** y **ninguna de las que resuelve es una `TASK` ya cerrada**:

| Id | Fuente | Resuelve por | Medido hoy |
|---|---|---|---|
| **S1** | Ruta citada | el fichero **existe** en el arbol (raiz, `.taskmaster/`, `docs/`, `docs/ai/`, `docs/archive/`). **Sin numero de linea** | 6 de las 8 filas vivas ya tienen una |
| **S2** | Identificador | un token de una palabra entre acentos graves de la fila **existe dentro de ese fichero**. Esto es lo que distingue «apunta a algo» de «apunta a lo que dice» | 4 filas (89, 99, 100, 101) |
| **S3** | `TASK-NNN` | existe en `.taskmaster/tasks.json` con `status` legible. **`completed` NO computa como comprobable de fila viva** | `TASK-059`/`TASK-061` pendientes sostienen la 89 y la 95 |
| **S4** | `CYCLE-NNN` | la entrada existe en `CHANGELOG.md` o en `.taskmaster/rd_journal.json` | la 98 (CYCLE-026) |
| **S5** | Numero | coincide con el recuento **derivado con `ast`** de `run_tests.py` (**103**). El panel no es fuente de verdad de si mismo | la 100 |

### 3.3 La regla que se audita a si misma

Ademas del marcador: **ninguna fila viva puede apoyarse solo en una tarea cerrada.** Es la regla que escribe la propia fila 93 («Un puntero a una tarea completada se lee como deuda viva y no lo es») y la que hoy no vigila nadie. Sin esta clausula, reabrir una fila cerrada borrando su `CERRADA` la dejaria en verde si su unica fuente es `TASK-057`.

### 3.4 El suelo de gravedad (S1 del ciclo #48)

`_severidad_minima(anclas)` deriva **un** suelo, y solo uno, porque es el unico comprobable de gravedad que existe en el repo de forma estable: si un ancla de la fila resuelve a un fichero que **sigue declarando `0` para `WOPT_COMMIT_OK` y para `WOPT_NOOP`**, el suelo es `ROJO`. Una fila viva que se declare `AMARILLO` con ese comprobable presente sale en rojo: **bajar la gravedad sin cerrar el problema es documentacion fail-open**, que es exactamente lo que la fila 89 dejo escrito tras sufrirlo una vez.

**CORREGIDO en el cierre del ciclo #49 tras medir el FAIL, y las dos correcciones son obligatorias.** (i) **La gravedad se lee del EMOJI**: el panel se expresa en 🔴🟡🟢 y el validador leia palabras, luego la condicion no se cumplia ni una vez (medido: `gravedad-palabra: NINGUNA` en 14 de 15 filas). Se mapea el glifo a la palabra **al leer**, y el informe sigue siendo ASCII puro (trampa #16). (ii) **"Declarar" es una FORMA y no una mencion**: la linea que **empieza** por el token `0` seguido del nombre. Con el predicado viejo ("un `0` antes del nombre en cualquier linea") casaba en `validate_docs.py`, en `run_tests.py`, en `tasks.json` y en el propio panel, y mapear el emoji sin arreglarlo **ponia el repo en rojo hoy** con las filas 100 y 101. Sin el predicado, el suelo esta atado a las citas y no a los asuntos: se recorre `anclas["rutas"]` y se declara la decision en el codigo y en el limite 4 de `docs/ai/sandbox-rules.md`.

---

## 4. Criterios discriminantes: que mutacion del panel pone el check en rojo

Cada fila dice **por que** el test discriminaria, no solo que falla. Los mensajes son **ASCII puro** (trampa #16: la consola es cp1252 y los emoji revientan el `print()`; la gravedad se imprime como `ROJO`/`AMARILLO`/`VERDE` en palabras, nunca como simbolo).

| # | Mutacion del panel (no del codigo) | Que se rompe | Mensaje literal |
|---|---|---|---|
| **M1** | Borrar el unico ancla de una fila viva (la 91 sin `pack_service.py`) | 0 fuentes resueltas | `STATUS.md Deuda fila 91: VIVA sin ancla resoluble (0 fuentes de 5). Una fila de la seccion que gobierna el bucle sin prueba fuera del panel es la que manda hacer un trabajo ya hecho` |
| **M2** | Apuntar un ancla a un fichero inexistente (`run_tests.py` -> `run_testz.py`) | S1 | `...ancla NO RESOLUBLE: run_testz.py no existe en el arbol` |
| **M3** | Mover una cita para que ya no apunte a lo que dice (la 87 citingo `test_powershell_direct.py:10` cuando el `Popen` esta en otra linea) | S2 | `...fichero existe pero NO contiene el identificador que la fila le atribuye: notepad.exe` |
| **M4** | **Reabrir una fila cerrada sin decirlo** (borrar `CERRADA` de la 94) | la fila pasa a viva y su unica fuente es una tarea cerrada | `...VIVA y su UNICA fuente es una TAREA YA CERRADA: TASK-057.status == completed. Una fila cerrada reabierta sin decirlo es el fallo que el criterio describe` |
| **M5** | **Rebajar la 🔴 de la 89 a 🟡 sin cerrarla** (fue el S1 del ciclo #48) | suelo de gravedad | `...declara AMARILLO pero su comprobable SIGUE VIVO: .taskmaster/git_safe_commit.py declara 0 para WOPT_COMMIT_OK y para WOPT_NOOP. La gravedad solo baja si el problema se cierra` |
| **M6** | Que el panel se autoderive (cambiar el `103` de la 100 por `96`) | S5 | `...numero 96 que NO es el derivado con ast de run_tests.py (103). El panel no es fuente de verdad de si mismo` |
| **M7** | Autoeximirse (poner `CERRADA` en mayusculas **fuera** de comillas invertidas en la 101) | clasificacion | `...la fila del criterio se ha autoeximido: lleva el marcador de cierre en un veredicto y es la fila que escribe este check` |
| **M8** | Borrar o renombrar el encabezado de la seccion | seccion ausente | `STATUS.md: no existe la seccion de Deuda Tecnica Conocida. Sin seccion no hay bucle que priorizar, y un validador que no encuentra lo que valida no es un validador` |
| **M9** | Vaciar la seccion (dejar el encabezado y cero filas) | inventario | `...0 fila(s). La seccion que gobierna el Paso 1 vaciada es indistinguible de la que aun no existe` |
| **M10** | *(check 7, no el 8)* Mover una llamada `test_*()` al otro lado del marcador de `run_tests.py` | reparto | `run_tests.py: declara 93 backend + 10 headless; el marcador de run_tests.py:12919 separa 94/9. El total puede seguir dando 103 mientras el reparto miente` |

**Por que cada uno discrimina y no es tautologico:** sin el fix, M1/M2/M9 no existen como codigo (no hay check); M3 muere si se resuelve por **existencia** y no por contenido; M4 y M7 mueren si se busca el marcador sin quitar el codigo inline; M5 muere si no hay suelo derivado; M6 muere si el numero se lee del panel; M8/M9 mueren si la seccion se encuentra por indice fijo. Ninguno pasa con el fix puesto: los nueve son, uno a uno, el fallo que el ciclo #48 demostro que sobrevive.

---

## 5. Los tres dilemas, resueltos

### (a) ¿El check 8 incluye el reparto 93 + 10? — **NO. Va en el check 7.**

Medido: el marcador estructural `print("\n--- Running Headless UI Tests ---")` esta en `run_tests.py:12919`; con `ast` salen **93** llamadas `test_*()` antes y **10** desde el, **103** exactas, que es el total que el check 7 ya vigila (`validate_docs.py:116-118` + la tabla de `docs/ai/testing-guide.md`).

Va como segunda derivacion **de `_comprobar_recuento_de_tests`**, no como parte del check 8, por dos razones concretas: (i) es la **misma derivacion** (`ast` sobre `run_tests.py`) contra los mismos ficheros que declaran cifras, y el check 8 tiene otro sujeto —las filas de una seccion—; (ii) mezclar dos derivaciones en una funcion hace que un rojo no diga **que** esta mal, y el coste de un falso rojo es que nadie mire el validador. Si el marcador no aparece en `run_tests.py`, se reporta el motivo literal (nunca verde por omision).

### (b) ¿Resolver por contenido o por linea? — **POR CONTENIDO. El numero de linea no se verifica nunca.**

La regla del repo lo anticipa («una cita `fichero:linea` a un fichero que crece por arriba se caduca sola») y la medicion da el dato que faltaba: **no caduca por crecimiento, caduca por insercion**, y solo donde el panel se cita a si mismo. El bloque intra-panel de la fila 101 esta desviado **una unidad en sus cinco entradas**, y el mismo error ya salio del panel a `docs/ai/sandbox-rules.md:120`. Las citas que nombran una funcion o un test estan **exactas** hoy.

Verificar la linea seria fabricar un rojo sin motivo en cuanto alguien inserte una fila arriba —que es lo que hace este bucle cada ciclo—, y ese es el rojo que entrena a ignorar el validador. El numero se queda en el texto como comodidad del humano; **la verdad se comprueba por identificador dentro del fichero**.

### (c) ¿Opt-in o opt-out? — **OPT-OUT.** La sospecha del encargo se evaluo en serio y no se sostiene.

1. **Opt-in no abarata el trabajo, cambia el agujero.** Hace falta un marcador igual (una fila que «declara» querer ser vigilada), luego el numero de filas tocadas no baja: baja porque deja de mirar filas. Y medido: las filas 91, 92 y 98 estan **cerradas de verdad** escritas en minuscula («Cerrado en el ciclo #18», «cerrado en el ciclo #16», «transcrita y cerrada»). Con opt-in serian las tres **ciegas para siempre**.
2. **Opt-out se cierra solo ante el ataque que importa.** Borrar el `CERRADA` de una fila cerrada la convierte en **vigilada**: si no trae ancla, el check grita. En opt-in, borrar la declaracion la deja **sin vigilar y en verde**. Ese es el fallo que el PARTIAL del ciclo #48 describe con otras palabras.
3. **Coste medido:** opt-out = **1 fila tocada**; opt-in = 1 fila declarada + 3 filas ciegas + la misma falta de teeth. Opt-out gana por goleada y no es mas caro.

---

## 6. El nacimiento: cuantas filas hay que tocar

Medido con el criterio final (`CERRAD` en mayusculas fuera de codigo inline): **15 filas, 8 vivas**.

| Fila | Estado medido | Anclas resolubles hoy | Toque |
|---|---|---|---|
| 88 `.git` del VFS | VIVA | 2 (S1: `docs/ai/sandbox-rules.md`, `.taskmaster/git_safe_commit.py`) | — |
| 89 `spawn EPERM` | VIVA 🔴 | 15 rutas + `TASK-059`/`TASK-061` pendientes | — |
| 91 `CORRUPTION_ERRORS` | VIVA | **0** — su unico nombre de fichero es `profiles.json`, que no esta en el arbol | **1 fila: anadir `src/woptimizer/services/pack_service.py`** |
| 92 tabla resumen del changelog | VIVA | 1 (S1: `rd_journal.json`) | — |
| 95 RESIDUO HONESTO #47 | VIVA | `TASK-059` `pending` (S3) | — |
| 98 deuda del ciclo #26 | VIVA | 2 (S1) | — |
| 100 `docs/index.md` | VIVA | 8 rutas + 103 derivado (S5) | — |
| 101 el criterio | VIVA | 9 rutas + `TASK-059`/`TASK-060` pendientes | — |

**TOTAL: 1 fila de 15.** `STATUS.md:91` recibe un ancla y nada mas: se le anade la ruta de `pack_service.py`, donde vive `CORRUPTION_ERRORS`, y con eso el check nace en verde.

**Y no se hace el atajo de gratis:** las filas 91, 92 y 98 se pueden exemptar en mayusculas con un cambio de una palabra cada una y el coste pasaria a **0 filas**. Se rechaza, y por la regla que el propio panel escribe en la fila 98: *un carve-out para exceptuar una falsehood concreta seria mas deuda que la falsehood*. Anclar las tres cuesta tres clausulas y deja tres filas bajo vigilancia.

---

## 7. Limite residual DECLARADO

La regla del repo es que lo que el check no cubre se escribe, no se omite. Esto es lo que **no** cubre:

1. **S1 solo prueba existencia, no verdad.** Una fila cuya unica fuente es S1 pasa aunque el fichero exista y diga lo contrario. Solo las filas con S2 quedan atadas a lo que afirman.
2. **El suelo de gravedad es UNO.** Solo el codigo de salida sobrecargado de `git_safe_commit.py` deriva gravedad. Una 🔴 rebajada a 🟡 sobre cualquier otro ancla sobrevive al check: no hay forma de derivar la gravedad de un texto sin escribir a mano la politica, y una politica escrita a mano en el validador es la misma mentira un nivel mas arriba.
3. **Las filas cerradas quedan mudas.** Por construccion (es el criterio del encargo). Una fila exenta puede quedar enteramente falsa y el check no dice nada.
4. **El corte de la seccion es por linea.** Una fila de deuda escrita como sub-vinetas (`  - `) no se cuenta como fila, y una seccion partida en dos encabezados solo se lee la primera.
5. **El check no juzga la semantica del ancla.** Que un fichero exista y contenga el identificador no demuestra que la fila diga la verdad sobre el.
6. **`docs/index.md` lo vigila el check 7, no el 8.** Si el Paso 3 no extiende la lista de `validate_docs.py:116-118` con ese fichero y su forma real (`(103 tests)`, no `run_tests.py` + `\d+ tests`), la 🟡 de la fila 100 queda **sin ancla de verdad** aunque este check la de por buena: el 8 certifica que la fila cita `docs/index.md`, no que ese documento no vuelva a mentir.
7. **Lo que queda del emoji, escrito con la verdad (CORREGIDO en el ciclo #49 tras el FAIL del auditor).** Este punto decia que "los emoji se comprueban como palabras" y que un panel que bajase la severidad cambiando el emoji **evadiria el suelo**. **Medido, esa afirmacion era falsa en sus dos partes**, y no hacia falta inventar un agujero nuevo para encontrarla: el emoji **se mapea** a `ROJO`/`AMARILLO`/`VERDE` al leer, porque el problema **no era el emoji: era que la palabra no existia en el panel**. Medido el 2026-10-02, 14 de las 15 filas no tienen ni una palabra de gravedad y la unica que la tiene (la 98) la usa para el *color* de un diagnostico de UI. El limite REAL que queda escrito es el **4 de `docs/ai/sandbox-rules.md`**: el suelo no tiene fila victima hoy, porque ninguna fila viva declara una gravedad por debajo de su suelo, asi que neutralizarlo entero deja el panel verde aunque M5 (bajar la 🔴 de la 88 o de la 89) si muera.

---

## 8. Criterios de aceptacion (resumen normativo)

1. `_comprobar_deuda_con_anclas(root, errors, ok)` existe, sin defaults, y se llama desde `validar(root)` una vez, entre el check 7 y el `return`.
2. Toda fila viva necesita **una** fuente resoluble y **ninguna** de las que resuelve puede ser una `TASK` `completed`.
3. El marcador de cierre se busca en mayusculas **fuera de codigo inline**; la fila del criterio no se autoexime.
4. **Ningun numero de linea se verifica.** La resolucion de S2 es «el identificador existe en el fichero».
5. Existe suelo de gravedad derivado para el comprobable del codigo de salida sobrecargado.
6. Los 10 mensajes son ASCII puro y citan la fila, el fallo y la causa.
7. Un unico test en `run_tests.py` sobre `STATUS.md` sintetico en `tempfile.mkdtemp()` cubre A-H (fila viva sin ancla -> FAIL; la misma fila cerrada -> PASS; numero que contradice el derivado -> FAIL; panel solo de cerradas -> PASS; seccion ausente -> FAIL; autoexencion -> FAIL; gravedad rebajada -> FAIL; separacion de la seccion) y **deriva el total con `ast` del arbol sintetico**, no del repo real.
8. El reparto 93+10 se deriva en el check 7 con `ast` y falla si el marcador de `run_tests.py` no aparece.
9. `STATUS.md` cambia en **una** fila (la 91, un ancla anadida) y en la cifra de `docs/index.md` si el reparto entra.
10. `src/woptimizer/**` con cero cambios.
