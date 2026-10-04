# Marcador de ciclo obligatorio y verificacion de los hashes del journal

**Change ID:** `2026-10-04-marcador-ciclo-y-hashes-journal`
**Tarea:** `TASK-059`
**Alcance:** `.taskmaster/git_safe_commit.py` (puerta de ancla en el mensaje), `validate_docs.py`
(check 9 sobre el campo `commits` de `.taskmaster/rd_journal.json`), `.taskmaster/rd_journal.json`
(saneado del residuo), `run_tests.py` (tests), `.agents/skills/id-pipeline/SKILL.md` y los cuatro
`.agents/agents/*/agent.md` (el bucle tiene que cumplir su propia puerta), `docs/ai/sandbox-rules.md`.
**NO toca:** `src/woptimizer/**` (cero cambios de codigo de producto). NO toca `STATUS.md`: la fila
del residuo se actualiza al cerrar el ciclo, y tocarla en mitad del ciclo romperia el contrato de
anclas del check 8 sin ganar nada (ver seccion 11).

---

## 1. Por que esta tarea no es cosmetica

El ancla de trazabilidad del ciclo #47 es `ciclos_del_journal | ciclos_del_historial`. Deja un punto
ciego declarado en `docs/ai/sandbox-rules.md:216`: si un ciclo se comitea **sin** commit de cierre y
**sin** entrada de journal, no hay tercer testigo y el validador no lo ve. Ese punto ciego no se
cierra con mas validacion: se cierra **con una puerta en el unico sitio por el que se versiona**.

Y en la direccion inversa, el campo `commits` del journal declara los hashes del trabajo de cada
ciclo y **nadie lo comprueba**: `validate_docs.py` no lee ese campo (cero coincidencias de
`commits` como dato; solo lo usa el nombre de la funcion `_ciclos_de_commits` y el termino
"commits" en prosa, `validate_docs.py:238, 350-355`).

---

## 2. Auditoria de la premisa: cuatro puntos del encargo que hay que corregir

El encargo llega con cuatro afirmaciones. **Dos son ciertas, dos son falsas, y una de las falsas es
la que cambia el trabajo.** Se miden antes de decidir nada, con el patron ya establecido
(`git log --format` sobre el `GIT_DIR` desacoplado, extrayendo el **hash** y no el string del
campo — que fue exactamente el bug que produjo la cifra falsa de "41 de 46", registrada en
`docs/ai/sandbox-rules.md:169`).

### 2.1 CIERTO — las cifras del campo `commits`

Medido el 2026-10-04 sobre las **51** entradas de `.taskmaster/rd_journal.json` (el campo `commits`
esta presente en 49; el identificador de la entrada es `cycle`, no `ciclo`):

| Clase | Entradas | Ciclos |
|---|---|---|
| **CONFORME** (lista de hashes cortos, sin texto libre) | **27** | el resto |
| Sin lista de hashes (`null` o `[]`) | **11** | 1, 2, 14, 15, 16, 17, 18, 19, 20, 27, 28 |
| Hash con texto libre pegado (`"617eef8 (architect)"`) | 13 | 3, 8, 9, 10, 11, 12, 21, 22, 23, 24, 25, 26, 50 |
| Pseudo-hash que no es un hash | 1 | 50 (`"<PENDIENTE>"`) |
| **Total que INCUMPLE** | **24** | 1, 2, 3, 8-12, 14-28, 50 |

Los **3 hashes que no resuelven** contra el repo desacoplado son `5623629` (ciclo 30), `ee4b753`
(ciclo 31) y `12b9c3bf` (ciclo 33), y `git cat-file -t` responde **`fatal: Not a valid object
name`** en los tres: los **objetos no existen**, no son commits huerfanos. Confirmado ademas que
**los tres estan dentro de entradas que son CONFORMES**: conformidad y resolubilidad son dos fallos
independientes y un check que las mezcle dara numeros falsos.

### 2.2 FALSO — "registrar las 24 como perdida historica"

**22 de las 24 no estan perdidas: son recuperables hoy, con un commit que resuelve.** Solo **2** son
perdida real. La distincion no es de estilo, es la diferencia entre un registro honesto y uno
falso, y el criterio de este repo ya la escribio: *borrar una fila sin evidencia es el mismo fallo
que no haberla escrito* (`STATUS.md:87`). Declarar como perdida una perdida que el historial
desmiente es **la misma clase de fallo al revés**.

| Clase | Entradas | Evidencia de recuperacion |
|---|---|---|
| **RECUPERABLE: la lista se rellena** | **9** — ciclos 14, 15, 16, 17, 18, 19, 20, 27, 28 | 14-20 los corrobora `7485f57` (`feat(ciclos 14-20)`, 2026-09-28); el 27, `9cc9582`; el 28, `5e166e1`. Los tres **resuelven**. |
| **SANEABLE: se quita el texto libre** | **13** — ciclos 3, 8-12, 21-26, 50 | Todos los hashes que declaran **resuelven**; lo unico que hay que hacer es dejar el hash desnudo. |
| **PERDIDA REAL** | **2** — ciclos **1** y **2** | `commits: null` y **ninguno de los 209 subjects** del historial nombra el ciclo 1 ni el 2. El commit mas antiguo es `3686a4a` (2026-09-14, `chore: initial commit v2.0.5`) y el primero que nombra un ciclo es de 2026-09-29. |

Ademas, la perdida **parcial** de los 3 hashes (ciclos 30, 31, 33) **no deja a esos ciclos sin
testigo**: el historial los corrobora con `837778a`, `a050ac7` y `34ca4ef`, que **resuelven**. El
hash muerto sigue siendo un hecho (un commit que se hizo y se perdio con el `.git` del VFS) y no
se sustituye por otro: se declara perdido **con su causa**, y se anota que el ciclo sigue anclado
hoy por el historial.

**Consecuencia de diseno:** el registro de perdida no es un campo para las 24, es un **registro de
causas** que solo admite lo que se puede **probar** que se perdio, y el resto se sanea en el mismo
pase. Sin esa distincion, el check 9 se nace con 22 FAIL en el repo real y el bucle gasta un ciclo
explicando un rojo que el propio check produjo.

### 2.3 FALSO — "validate_docs.py no imprime el numero de commits con y sin marcador"

**Ya lo imprime, desde el ciclo #47.** `_ciclos_de_commits(asuntos)` devuelve
`(ciclos, con_marcador, sin_marcador)` (`validate_docs.py:238-264`) y el informe reimprime la
linea viva en `validate_docs.py:350-355`:

```text
historial de commits: 209 subject(s), 73 con marcador de ciclo y 136 SIN marcador
(punto ciego medido); 48 ciclo(s) corroborables frente a los 51 del journal
```

Lo que falta **no** es imprimir el numero: es que **nada lo exige**. Es una medicion sin suelo, y una
medicion sin suelo es una promesa (se relee como verdad y nadie vuelve a mirarla — el mismo
argumento que ya cierra el alcance de `docs/ai/sandbox-rules.md:174-187`). El gap real es doble y
se cierra en la seccion 7: (a) el campo `commits` del journal **no se comprueba en absoluto**, y
(b) el punto ciego del punto 2 del ancla **se mide pero no se puede cerrar desde el validador**,
porque cerrar una puerta de escritura no es cosa de un validador: es cosa de `git_safe_commit.py`.

### 2.4 CIERTO — el wrapper no valida el mensaje

`.taskmaster/git_safe_commit.py` acepta el mensaje tal cual: `parse_args` solo comprueba que no sea
vacio y que no haya mas de un posicional (`git_safe_commit.py:141-160`), y el mensaje llega intacto
a `git commit` (`git_safe_commit.py:227`). Cero mencion de ciclo, cero mencion de tarea.

---

## 3. Decision: la puerta del mensaje en `git_safe_commit.py`

### D1 — Que cuenta como identificador (tres formas, y solo tres)

Un mensaje pasa la puerta si contiene **al menos una** de:

1. `TASK-NNN` (1 a 4 digitos) **que exista en `.taskmaster/tasks.json`**. La resolubilidad se exige
   porque es lo que convierte el identificador en un ancla y no en una decoracion.
2. `CYCLE-NNN` (3 digitos).
3. Marcador de ciclo en el sentido del parser que ya existe: `\b(?:ciclo|cycle)(s?)\b[\s:#-]*#?(\d{1,4})`
   (`validate_docs.py:238-264`), reutilizado **literalmente** para que la puerta y el validador no
   puedan divergir. Es la misma exigencia que ya pagaro el ciclo #47 con el parser de marcadores.

**Lo que NO cuenta: `T-N`.** En este repo `T-1`..`T-9` son ids reales de tarea *dentro de una change*
(`openspec/changes/*/tasks.md`) y `T-9` aparece en commits reales (`9433985`). Un regex laxo que
acepte `T-\d+` admitiria un espacio de ids que **no existe en `tasks.json`** y que nadie puede
resolver: es un ancla de mentira.

**Medido que la resolubilidad no cuesta nada al bucle:** de los 209 subjects, 117 llevan `TASK-` y
las **123 menciones resuelven todas** en `tasks.json` (0 no resuelven). La puerta no rechaza nada
que el bucle haya hecho bien.

### D2 — Donde se coloca: despues de `validar_repo` y del NOOP, antes de `add -A`

El orden **no es un detalle**, y las tres frontera se pueden medir contra el codigo real:

| Posicion | Consecuencia medida |
|---|---|
| Antes de `validar_repo` (`git_safe_commit.py:176`) | Rompe el contrato: los dos commit-path del test existente (`run_tests.py:1447` y `:1471`) esperan **3** con un `GIT_DIR` invalido, y pasarian a 2. El 3 significa "no pude ni comprobar" y el 2 "tu invocacion esta mal": confundirlos entrena al orquestador a diagnosticar el repo cuando el problema es su cadena. |
| **Despues de `validar_repo` y del NOOP (`git_safe_commit.py:200-202`), antes de `add -A` (`git_safe_commit.py:206`)** | **Elegida.** Un arbol limpio sigue diciendo `WOPT_NOOP` + `0` (benigno: no hay commit que anclar, y rechazar un no-op seria ruido que el orquestador leeria como "el commit fallo"); un commit que existe lleva SIEMPRE identificador; y la puerta sigue siendo **de solo lectura**, luego testeable sin escribir. |
| Despues de `add -A` | Rechaza **despues** de stagear: muta el arbol real para luego decir que no. Prohibido. |

**Y esto desbloquea una parte de `TASK-061` sin decidarla.** `TASK-061` esta bloqueada porque
`get_env()` impone `GIT_WORK_TREE = REPO_ROOT` sin condiciones (`git_safe_commit.py:78`), luego un
`GIT_DIR` temporal **no** hermetiza el arbol de trabajo. La puerta de D2 es de solo lectura y cae
**antes de la primera escritura**, luego **si** es testeable de forma hermetica: por la funcion
extraida y por una asercion estructural con `ast` (el mismo patron que ya usa
`_reparto_de_tests` con `MARCADOR_HEADLESS`, `validate_docs.py:508-561`). Lo que **no** es testeable
hoy —y se declara como limite, no como sorpresa— es el **rechazo extremo a extremo por subproceso
con un arbol deliberadamente sucio**, porque el arbol de trabajo **no es controlable desde fuera**
del wrapper. Eso es `TASK-061`, y no lo resuelve esta tarea.

### D3 — El codigo de salida es **2** (`WOPT_USAGE`), no 1

El encargo pide 1. **Se recomienda 2, y es una decision, no un descuido.** La tabla contractual de
`docs/ai/sandbox-rules.md:57` define el `1` como *"fallo de una operacion de **git**"* con linea
`WOPT_FAIL <operacion> <detalle>`; la puerta del mensaje **no ejecuta ninguna operacion de git**, y
meterla en `WOPT_FAIL` haria **falsa la tabla documentada**, que es el mismo fallo que paga la
limitation 4 del contrato. El `2` ya significa "uso incorrecto" (`docs/ai/sandbox-rules.md:58`) y
eso es exactamente lo que es: la invocacion no trae lo que la herramienta exige. No se **anade** un
codigo —se **extiende** la fila "cuando" del `2`—, luego el contrato 0/1/2/3 sigue integro, y todo
consumidor que ramifica por `exit == 0` sigue viendo "no hubo commit", que es lo unico que no
puede perderse.

*Si el orquestador insiste en el 1:* el cambio es el nombre de la operacion en la linea `WOPT_*` y
**el mismo test sigue matando el mutante**, porque el criterio afirma "el codigo contratado, el que
sea". Se documenta el coste: con `1`, un `WOPT_FAIL ancla-mensaje` es indistinguible de un fallo de
git, y el unico consumidor real de ese codigo (`.agents/agents/architect-review/agent.md:50`)
ramifica por el codigo, no por el prefijo.

### D4 — El mensaje dice QUE se espera y POR QUE importa

Regla dura de `detalle()`: **ASCII puro** (trampa #16, consola cp1252), y la linea `WOPT_*` va
**la ultima**, siempre (regla 4 del contrato). Forma exacta:

```text
WOPT_USAGE ancla-mensaje este mensaje no lleva identificador de ciclo ni de tarea;
se espera 'TASK-NNN' existente en .taskmaster/tasks.json, 'CYCLE-NNN' o 'ciclo N'.
POR QUE importa: sin identificador este commit no tiene tercer testigo --ni
rd_journal.json ni el historial podran anclarlo despues-- y esa es la ceguera que
TASK-059 cierra. Ancla tu mensaje y repite el commit.
```

### D5 — Sin flag de escape, y por que

Un `--sin-ancla <motivo>` que comitea convierte la puerta en **opt-in** (se usa por defecto, porque
es lo que hay que escribir); uno que se niega es un no-op. El repo ya resolvio esta misma
disyuntiva en el check 8 y lo escribio: *"opt-out, no opt-in"* (`docs/ai/sandbox-rules.md:507`).
La puerta es **opt-out por construccion**: hay 63 ids en `tasks.json` y 48 de los 51 ciclos del
journal se corroboran hoy por el historial, luego **siempre hay un identificador disponible**.

Dos degradaciones deliberadas, ambas explicitas:

- **`tasks.json` ilegible** → la puerta exige la **forma** y **no** la resolubilidad, y lo dice en
  una linea `INFO`. Se degrada solo el paso de resolucion, **nunca el de forma**: un `except` que
  devolviera "todo valido" seria fail-open y dejaria la puerta muerta.
- **Camino `--verify`** → **no** pasa por la puerta: es un diagnostico del repo y no lleva mensaje
  (`run_tests.py:1461`).

---

## 4. Decision: la regla del campo `commits` del journal

**R1 — conformidad de forma.** Cada elemento de `commits` es un hash corto **completo**
(`fullmatch` de `\b[0-9a-f]{7,40}\b`), sin texto libre. Es la medidad que ya se reencontro: el
`"617eef8 (architect)"` **si** contiene el hash `617eef8`, y por eso medir el string entero dio la
cifra falsa de "41 de 46" (`docs/ai/sandbox-rules.md:169`). El `fullmatch` es el fix de esa clase
de bug, no un detalle de estilo.

**R2 — resolubilidad.** Cada hash declarado **resuelve** en el mismo repo desacoplado que ya usa
el ancla (`validate_docs.py:300-302`, que hereda el `GIT_DIR` del entorno o `%LOCALAPPDATA%`).

**R3 — el registro de perdidas vive en el propio journal, y solo admite perdidas probadas.**
Un campo nuevo **por entrada**, `commits_perdidos`, porque la perdida es de *un ciclo* y porque
`rd_journal.json` es una **lista** en la raiz: un campo de raiz obligaria a cambiar la forma del
documento y a tocar a todos sus consumidores. Elementos
`{hash, causa, nota?}`, con `causa` en **vocabulario cerrado**, no prosa:

| `causa` | Significado | Ocurre hoy |
|---|---|---|
| `VFS_CORRUPTO` | el objeto no existe en el repo desacoplado (`cat-file -t` dice `Not a valid object name`); se perdio con el `.git` del arbol | 3 hashes: `5623629` (c.30), `ee4b753` (c.31), `12b9c3bf` (c.33) |
| `NUNCA_DECLARADO` | el ciclo nunca declaro hash y el historial no lo nombra | 2 ciclos: **1** y **2** |

La prosa libre solo cabe en `nota`, porque **una causa redactada en libertad es infalsable**: no se
puede contar, no se puede agrupar y cualquiera puede escribir "se perdio" y cerrar el ciclo. Un
vocabulario cerrado convierte "aparecio una causa nueva" en un valor nuevo visible.

**R4 — antidolar: una perdida que el repo desmiente es un FAIL.** Si un hash declarado en
`commits_perdidos` **resuelve**, el check **falla**: *"declarada perdida una perdida que el
historial desmiente"*. Sin R4, la solucion degenerada es declarar las 24 perdidas y el check queda
verde: exactamente el falso verde que este ciclo existe para matar, y la refutacion de la seccion
2.2 es lo que lo impide.

**R5 — el techo de perdidas, derivado de la medidad de hoy, no de una promesa.** Constantes en el
producto: `MAX_HASHES_PERDIDOS = 3` y `MAX_CICLOS_SIN_HASH = 2`, comentadas con la fecha y el
numero del que salen. Subirlos es un FAIL. Esto convierte "la cobertura del ancla" en un **suelo
ejecutado** y no en una linea de informe que nadie compara con nada.

**Y el punto que hace que todo esto no sea decorativo: borrar una declaracion de perdida no
silencia nada.** El `commits` del ciclo sigue ahi, y sin su `commits_perdidos` la R2 vuelve a
fallar. El registro de perdidas **explica**, nunca **suprime**. Es el mismo criterio que el check 8
aplico a las exenciones, y por eso el opt-out es correcto aqui tambien.

---

## 5. Decision: el ciclo 50 se arregla en este ciclo, no es deuda aparte

El encargo pregunta explicitly. **Se arregla aqui**, por una razon que no es de conveniencia: si no,
**el check 9 nace con un FAIL en el repo real**.

Medido, el `commits` del ciclo 50 es `["bb50a7a", "4aba876", "6a6fb5f", "f447218", "6f7e15d", "41b8061",
"<PENDIENTE>"]`: **seis hashes reales mas un marcador de relleno**, no un `<PENDIENTE>` solo. Los
seis resuelven, y el historial corrobora el ciclo 50 con **tres** commits que resuelven
(`4aba876`, `9d8fd00`, `ad9159f`, los tres de 2026-10-03). O sea: el `<PENDIENTE>` **no es una
perdida, es un campo sin rellenar**, y su causa esta documentada y es culpa del propio bucle:
`SKILL.md:382` manda escribir el changelog **despues** del commit "para tener el hash", y en el
cierre del ciclo 50 ese relleno nunca se hizo.

Se sustituye por los tres hashes corroborantes y el hueco se registra con `causa:
NUNCA_DECLARADO` y una `nota` que nombre la regla que lo produjo. Declararlo perdida historica
habria sido **fabricar una perdida donde hay un hecho recuperable**: la segunda refutacion de la
seccion 2.2 aplicada a un caso concreto.

Los **11 ciclos sin lista** y los **13 con texto libre** se resuelven en el mismo pase, por la misma
razon: un check que nace con 24 FAIL es un check que el bucle aprendio a ignorar.

---

## 6. Impacto medido en el bucle de la puerta de mensajes

**Medido el 2026-10-04 sobre los 209 subjects del historial desacoplado:**

| Forma de la puerta | Pasa | Rechaza |
|---|---|---|
| **`TASK-` O ciclo (la de D1)** | **149 / 209 (71%)** | **60 (29%)** |
| `TASK-` Y ciclo | 41 / 209 (20%) | 168 (**80%**) |
| solo `TASK-` | 117 / 209 (56%) | 92 (44%) |
| solo ciclo | 73 / 209 (35%) | 136 (65%) |

**La puerta NO paraliza el bucle: la rechaza un 29%, no un 100%.** Y de los **25 commits mas
recientes, 8 la fallan** (32%) — el bucle no vive limpio hoy.

**Pero el dato que decide el diseno es otro, y es determinista: las CINCO plantillas literales de
mensaje que el propio bucle tiene escritas fallan las cinco.**

| Plantilla literal | Falla |
|---|---|
| `.agents/skills/id-pipeline/SKILL.md:152` — `"chore(architect): planificar <tarea>"` | SI |
| `.agents/skills/id-pipeline/SKILL.md:180` — `"feat/fix: <tarea>"` | SI |
| `.agents/skills/id-pipeline/SKILL.md:280` — `"chore(architect): planificar [ID_TAREA]"` | SI |
| `.agents/skills/id-pipeline/SKILL.md:300` — `"feat/fix([COMPONENTE]): [TÍTULO_TAREA]"` | SI |
| `.agents/skills/id-pipeline/SKILL.md:332` — `"chore(process-db): actualizar procesos gaming y bloatware"` | SI |

Instalar la puerta **sin** tocar esas plantillas **mata el bucle en su primer commit**, con
certeza y no con probabilidad. Por eso la seccion 7 de `tasks.md` mete la actualizacion de
`SKILL.md` y de los cuatro `agent.md` **en el mismo cambio** que la puerta, y por eso hay un
criterio de aceptacion que extrae esas plantillas del repo y las pasa por la puerta del producto
(AC-C1): la puerta y el bucle se comprueban el uno al otro.

Las dos formas de fallo que ya se ven en el historial y que la puerta habria dejado pasar:
`T-9` en vez de `TASK-063` (`9433985`), y mensajes `ci(release)` / `fix(release)` sin id
(`bb50a7a`, `41b8061`, `6f7e15d`, `f447218`, `6a6fb5f`).

---

## 7. `validate_docs.py`: el check 9 y su linea de informe

`_comprobar_hashes_del_journal(root, errors, ok)`, **tres posicionales y sin defaults**, cableada en
`validar(root)` entre el check 8 y el `return`, por el motivo que ya pago el ciclo #47 (decision D1
de `docs/ai/sandbox-rules.md:275`): un default convierte un cableado roto en un `None` silencioso.
Reutiliza la lectura de commits que ya existe (mismo `GIT_DIR`, misma precedencia) y las reglas R1-R5
de la seccion 4.

**Sobre el numero con y sin marcador: no se anade, ya existe.** Lo que se anade es su **suelo** y,
en la linea de informe, el **segundo bloque medido** que hoy no existe:

```text
campo 'commits' del journal: 51 entrada(s), 49 con el campo presente, 51 conforme(s),
0 sin hash declarado, 3 hash(es) perdido(s) declarados con causa (2 ciclo(s) sin hash:
NUNCA_DECLARADO, 1 hash: VFS_CORRUPTO)  <- cifras vivas, leidas del repo, no escritas aqui
```

Las cifras **no se escriben fijadas en ningun documento** (la regla de
`docs/ai/sandbox-rules.md:174-187`: una cifra caducada escrita al lado de la cifra viva es peor que
no escribirla). El texto de arriba es la **FORMA** de la linea, no su contenido.

---

## 8. Criterios de aceptacion discriminantes

Cada criterio nombra el mutante que mata. Ninguno deriva su expectativa del fichero que valida: el
validador se prueba sobre arboles sinteticos con `GIT_DIR` temporal y con **commits reales** del repo
temporal (para que "resuelve" sea un hecho y no una afirmacion), y el wrapper por su funcion
extraida.

### A — El wrapper

| # | Criterio | Mutante que mata | Por que FALLA sin el fix |
|---|---|---|---|
| **AC-A1** | `ancla_del_mensaje(mensaje, ids)` existe, es **pura** (sin `os`, sin `subprocess`) y devuelve `(ok, motivo)`. Con `ids` sintetico, `"feat: cosas"` devuelve `ok == False` y el motivo nombra **las tres formas aceptadas**. | Devolver siempre `(True, "")`, o borrar la funcion y que `main()` acepte cualquier mensaje | Sin la funcion no hay nada que llamar, y el mutante "siempre True" hace que el `ok == False` falle en la primera asercion |
| **AC-A2** | `"fix(x): T-9"`, `"T-1"`, `"C-9"` y `"TASK-"` (sin digitos) **no** pasan; `"fix(x): TASK-059 (T-9)"` **si**. | `\bT-?\d+` / `T-\d+` en vez de `TASK-\d{1,4}`: dejaria pasar `T-9`, que **no existe** en `tasks.json` | Los cuatro casos son la forma *deceptiva*: hoy pasan, con el fix no. Un regex laxo los acepta |
| **AC-A3** | El id `TASK-` tiene que **existir** en el conjunto inyectado: `"chore: TASK-999"` falla y nombra que no esta en `tasks.json`. | Dejar el chequeo en forma pura (buscar `TASK-\d+` y nada mas) | El mutante devuelve `ok == True` para `TASK-999` |
| **AC-A4** | El contrato de codigos no se mueve: con `GIT_DIR` inexistente y **cualquier** mensaje, sigue saliendo **3** con `WOPT_REPO_INVALIDO`; sin argumentos, **2** con `WOPT_USAGE`; `--verify` con repo sano, **0**. Los tres casos se ejecutan **como subproceso** (extiendo `test_git_safe_commit_fail_safe`, `run_tests.py:1401`). | Colocar la puerta **antes** de `validar_repo` (`git_safe_commit.py:176`) | Ese mutante convierte el 3 en 2 y `assert r.returncode == 3` (`run_tests.py:1448`) falla |
| **AC-A5** | **Orden, con `ast` sobre el wrapper real**: la llamada a la puerta esta **despues** del `sys.exit` del NOOP (`git_safe_commit.py:200-202`) y **antes** de `run_git(["add"...])` (`git_safe_commit.py:206`). Se afirma con los indices de sentencia, como ya hace `_reparto_de_tests` con `MARCADOR_HEADLESS`. | Mover la llamada por encima del NOOP, o por debajo de `add -A` | Los indices de sentencia cambian y la asercion posicional falla; es el unico modo de probarlo sin un arbol de trabajo controlable (limite de la seccion 9) |
| **AC-A6** | El rechazo imprime la linea `WOPT_USAGE ancla-mensaje` como **ultima** linea de stdout, en **ASCII puro**, y el mensaje contiene "se espera" **y** "importa" (o `POR QUE`). | Acortar el mensaje a `"formato invalido"`, o imprimir la linea `WOPT_*` antes de los `INFO` | La asercion de contenido y la de "es la ultima linea" fallan ambas |

### B — El check 9 del validador

| # | Criterio | Mutante que mata | Por que FALLA sin el fix |
|---|---|---|---|
| **AC-B1** | Journal sintetico con `commits: ["617eef8 (architect)"]` y un repo temporal donde **`617eef8` existe y resuelve** → **FAIL** nombrando el ciclo y el elemento. Con el elemento conforme → 0 FAIL. | `re.search` en vez de `fullmatch` en el elemento | Con `search` el elemento conforms, sus hashes resuelven y el check da **0 FAIL**: el test exige FAIL. La segunda mitad del par es la que mata el mutante "marca todo" |
| **AC-B2** | Journal con un hash que **no** resuelve y **sin** `commits_perdidos` → FAIL. **El mismo journal** con `commits_perdidos: [{hash, causa: "VFS_CORRUPTO"}]` → 0 FAIL. Y con `causa` vacia o fuera del vocabulario → FAIL. | Aceptar la perdida sin `causa`, o invertir la R2 (fallar cuando si esta declarada) | El par exige los dos veredictos sobre el **mismo** arbol: un mutante que solo sepa fallar, o solo sepa pasar, falla una de las dos mitades |
| **AC-B3** | Journal que declara perdido un hash que **si resuelve** en el repo temporal → **FAIL** ("declarada perdida una perdida que el historial desmiente"). | Borrar la R4 | Sin la R4 el caso da 0 FAIL y el registro de perdidas se vuelve una Machine de perdonar |
| **AC-B4** | `MAX_HASHES_PERDIDOS = 3` y `MAX_CICLOS_SIN_HASH = 2`: un journal sintetico con **4** hashes perdidos declarados → FAIL; con 3 → 0 FAIL. Las constantes se **leen del producto** (no del test) y el test verifica ademas que su comentario lleva la fecha de la medidad. | Subir el techo a 999, o borrarlo | El mutante deja pasar el caso de 4. Y si el test copiara el numero en vez de leerlo, dejaria de compararse con el producto |
| **AC-B5** | La linea de informe del check 9 imprime las **cifras vivas** del journal sintetico (conteos conocidos **por construccion** del fixture: 3 entradas, 1 conforme, 1 hash perdido declarado, 1 ciclo sin hash) y **nunca `0 + 0`**: si el journal no se puede leer, se acusa con el motivo literal. | Devolver ceros cuando no se deriva (`None` -> `0`) | El fixture fija los numeros al construirlo; un `0+0` en verde los contradice |
| **AC-B6** | **Cableado en el camino real**: se copia el `validate_docs.py` **real** a un arbol temporal con el esqueleto que `validar()` lee y se ejecuta **como subproceso**; un journal con un elemento no conforme → salida **distinta de 0**. | Borrar la linea `_comprobar_hashes_del_journal(root, errors, ok)` del cuerpo de `validar()`, o `main()` sin llamar a `validar(root)` | Es el patron que ya pago tres veces (ciclos #47 y #49): los tests privados no probaban el cableado que les pasa los argumentos, y el fix quedaba **codigo muerto en el camino real** |

### C — El bucle cumple su propia puerta

| # | Criterio | Mutante que mata | Por que FALLA sin el fix |
|---|---|---|---|
| **AC-C1** | Se extraen del repo las plantillas literales de `git_safe_commit.py "..."` de `.agents/**` y **todas** pasan `ancla_del_mensaje` con los ids reales de `tasks.json`. | Dejar las plantillas sin id (estado medido hoy: **0 de 5 pasan**) | Hoy falla, y es el unico criterio que detecta "puerta instalada, bucle no actualizado" |
| **AC-C2** | Los dos mensajes del camino de commit del test existente (`run_tests.py:1447` y `:1471`) llevan identificador, y el `3` esperado se conserva. | Borrar el id de esos dos fixtures | Sin el, el test mas antiguo del wrapper estaria violando la politica que el wrapper impone |
| **AC-C3** | `docs/ai/sandbox-rules.md` documenta la puerta (codigo, orden, las tres formas, el `POR QUE`), el check 9 (R1-R5) y el **limite de la seccion 9**; `SKILL.md` y los cuatro `agent.md` **repo** quedan sincronizados con `python .taskmaster/sync_agents.py` (exit 0). | Editar el espejo de `~/.minimax/agents/` en vez del repo | `sync_agents.py --check` sale 1 con el espejo editado |

---

## 9. LIMITES RESIDUALES — se escriben, no se omiten

1. **El rechazo extremo a extremo con arbol sucio no es testeable hermetico hoy.** `get_env()`
   impone `GIT_WORK_TREE = REPO_ROOT` sin condiciones (`git_safe_commit.py:78`), luego el arbol de
   trabajo **no es controlable desde fuera** y un test no puede fabricar "arbol sucio" sin mutar el
   arbol real. Por eso AC-A1..A3 y A6 van por la funcion extraida y AC-A5 por `ast`. **Dueno:
   `TASK-061`**, cuya decision de diseno sobre `GIT_WORK_TREE` es la que lo desbloquea. La puerta
   **si** es hermetica en el sentido que importa: es de solo lectura y devuelve antes de la primera
   escritura.
2. **La puerta no es independencia de actor.** La escribe el mismo agente que escribe el mensaje
   (`docs/ai/sandbox-rules.md:209-211`): puede mentir en el identificador igual que mentia sin el.
   Lo que se gana es que **omitir** ya no sale gratis, no que mentir desaparezca.
3. **La puerta no cubre `git a pelo`.** El bucle tiene prohibido versionar sin el wrapper
   (`AGENTS.md`, y el propio encargo), pero la puerta solo existe en el wrapper. Un commit hecho a
   mano pasa sin identificador y el validador lo vera como `SIN marcador` — que es la cifra que ya
   se imprime, y por eso sigue viva.
4. **El techo de perdidas congela un residuo que no se puede cerrar, por construccion.** Los 3 hashes
   del VFS no van a volver. El techo no es un objetivo a barrer: es un suelo que avisa si **crece**.
   Un dia que se recupere un objeto (un `git fetch` de un clon) el techo habra que bajarlo, y ese
   dia el check exigira la accion, que es lo que se quiere.
5. **R3 se apoya en un vocabulario cerrado, y un vocabulario se puede ampliar a voluntad.** Si alguien
   anade un valor a `causa` para tapar una perdida real, R4 sigue sujetando a los **hashes**, pero una
   entrada `NUNCA_DECLARADO` sin hash no la sujeta nadie mas que el techo `MAX_CICLOS_SIN_HASH`. Es la
   costura mas blanda del diseno y se declara como tal.
6. **Los 11 ciclos sin hash y los 13 con texto libre se corrigen a mano en el journal.** Es
   trabajo de una vez, no una migracion codificada, y por eso **esta propuesta exige que se haga en
   el mismo cambio**: un check que nace con 24 FAIL en el repo real es un check que el bucle
   aprendio a ignorar, que es el fallo del ciclo #15 en otra forma.

---

## 10. Ficheros

**Crea:** `openspec/changes/2026-10-04-marcador-ciclo-y-hashes-journal/` (`proposal.md`, `tasks.md`).

**Modifica (los decide y ejecuta `openspec-dev`, no este contrato):**
`.taskmaster/git_safe_commit.py`, `validate_docs.py`, `.taskmaster/rd_journal.json`, `run_tests.py`,
`.agents/skills/id-pipeline/SKILL.md`, `.agents/agents/*/agent.md` (los **cuatro**, editando el
repo y luego `sync_agents.py`), `docs/ai/sandbox-rules.md`.

**No toca:** `src/woptimizer/**` (cero), `STATUS.md` (ver seccion 11).

## 11. Por que `STATUS.md` no se toca en este contrato

La fila del residuo honesto del ciclo #47 (`STATUS.md:95`) dice en su punto (a) que el ciclo
`feat(...)` sin commit de cierre y sin entrada de journal es `TASK-059`: es un puntero, y un puntero
a la tarea que lo cierra se actualiza **al cerrar el ciclo**, por el orquestador, que es quien
rota el panel. Tocarla aqui exigiria reescribir el residuo **antes** de que exista el check que lo
cierra, y escribir un cierre antes de medirlo es el fallo que este repo ya pago dos veces (ciclos
#15 y #48). Ademas, la seccion que gobierna el trabajo del bucle esta bajo el check 8: anadirle una
fila o reescribir el punto (a) en mitad del ciclo cambia lo que el check 8 deriva, sin ganar nada.
**Lo que este contrato deja escrito para el cierre** esta en la seccion 5 y en el AC-C3.
