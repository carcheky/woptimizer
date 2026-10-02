# Informe de mutacion — check 8 de la Deuda Tecnica Conocida (TASK-060, ciclo #49)

**Change ID:** `2026-10-02-check-deuda-con-anclas`
**Ronda:** 4.ª del ciclo #49 (cierre), tras el **FAIL** del `mutation-auditor` de
la ronda 3 (siete correcciones, **las siete de TEXTO**: ni una tocaba `src/` ni
una sola fila del panel).
**Fecha de medicion:** 2026-10-02, en Windows.
**Rondas 5 y 6, más abajo, con su propio §0 cada una.** Este fichero acumula rondas
y **cada una se mide contra su propio commit**, luego los números de las secciones
antiguas son los de su ronda y no los de hoy. La ronda 6 esta al final, y su §0
declara los suyos.

## 0. EL BASELINE, DECLARADO — y por qué este informe REEMPLAZA al anterior

**Todo lo que hay en este informe se midió contra el commit `a31e585`** (HEAD al
empezar este pase) y contra el árbol de este pase. La versión anterior de este
fichero medía contra `eaa9bb1` y no lo decia en su §0; las dos versiones
conviven porque **las dos son ciertas en su commit**, y un informe sin baseline
no se puede re-auditar, que es lo unico para lo que sirve.

| | Informe de la ronda 3 (medido en `eaa9bb1`) | Ronda 4 (medido en `a31e585`) |
|---|---|---|
| Anclas del panel intacto | `35` | **`35`** |
| G2f' con `TASK-059` | `8 exenta(s) / 7 viva(s) / 33`, `0 FAIL` | **idéntico, reproducido** |
| Limite 4: «la 89 es la unica que declara 🔴» | afirmación | **FALSA**, ver abajo |
| Limite 18: «pone las siete exentas en rojo» | afirmación | **FALSA**, ver abajo |
| `normcase` como «segunda garantia» | afirmación | **FALSA en las dos plataformas**, ver abajo |
| Celda de P5: `0 -> 2` con veredicto «MUERE (ya en HEAD)» | `0 -> 2` | **`2 -> 2`**: la cifra no cuadraba con su propio veredicto |

**Las tres afirmaciones falsas que se corrigen aqui, con su medicion:**

1. **Limite 4.** Decía que de las quince filas «la 89 es la única que declara 🔴».
   MEDIDO con `_gravedad_declarada` fila a fila: **`ROJO` en ocho** (87, 89, 90,
   93, 94, 96, 98, 99), `AMARILLO` en dos (100, 101) y **ninguna en cinco** (88,
   91, 92, 95, 97). Entre las **vivas** declaran `ROJO` la **89 y la 98**. La
   conclusion —el suelo no tiene fila victima— **sigue valiendo**, porque el
   suelo solo se dispara por debajo de `ROJO` y las dos vivas ya estan en `ROJO`;
   lo que era falso era la medicion que la sostenia, y estaba **copiada en tres
   sitios** (este informe, el limite 4 y el comentario de `_RE_GRAVEDAD`).
2. **Limite 18.** Decía que `CERRADA:` → `cerrada:` en la fila 90 pone «las
   **siete** exentas en rojo». MEDIDO: `6 exenta(s) / 9 viva(s)`, `35` anclas y
   **un** `FAIL`, el de esa misma fila 90 por «su UNICA fuente es una TAREA YA
   CERRADA». El rojo es real; el número no.
3. **`normcase`.** Su docstring y su linea del informe la llamaban «segunda
   garantia para los sistemas donde `realpath` no canonicaliza la caja». MEDIDO
   contra la stdlib: `posixpath.normcase` es literalmente `return os.fspath(s)`,
   con docstring *«Has no effect under Posix»* — luego en POSIX **no hace nada**.
   Y MEDIDO en Windows que `os.path.realpath("status.md")` devuelve ya
   `…\STATUS.md`, o sea el nombre **real**. No era «redundante en Windows»: era
   **inerte en todas las plataformas**, y announcing era falso.

**Estado del panel que se mide, y es el mismo en las dos columnas de todas las
tablas:** `115 OK / 0 FAIL`, 15 filas, 7 exentas, 8 vivas, **35 anclas** de ruta
resuelta y 2 por contenido, suite de **104 tests** (la tabla de escenarios del
check 8 tenía **30** filas en el commit de esta ronda —`a31e585`—; la ronda 5 la
subió a 33 y la **ronda 6 a 42**, y el numero de tests no cambia en ninguno de los
tres casos, porque los escenarios son filas de una tabla, no tests. El recuento
unico de este informe es el de su propio §0, y el de la ronda que lo firma.).

## 1. Como reproducir una fila de este informe

Nada se escribe en el arbol: `git_safe_commit.py` hace `add -A`.

- **Mutantes de panel** — se copia el **repo entero** (sin `.git`, `dist` ni
  caches) a un `tempfile.mkdtemp()` de `%TEMP%`, se sustituye `STATUS.md` por el
  mutado y se mide `validar(temp)`. La copia tiene que ser COMPLETA: MEDIDO que
  con la copia parcial que usa el esqueleto de los tests el recuento de anclas cae
  de **35 a 28** (`.agents/` y `.taskmaster/*.py` no están) y **sin
  `.taskmaster/git_safe_commit.py` el suelo de gravedad no existe**, con lo que
  P6, P7 y G2 morirían por un motivo que no es el suyo. Una campana sobre un árbol
  que no es el repo mide otra cosa.
- **Columna `HEAD`** — el validador de `a31e585` **tal cual**, sobre el mismo
  banco y el mismo árbol. Se mide el fichero que hay, y el control es que las dos
  columnas coincidan exactamente sobre el panel intacto
  (`0 FAIL / 7 exentas / 8 vivas / 35 anclas`).
  ~~No hay `git` en este entorno, luego no se reconstruye por parche inverso.~~
  **CORREGIDO en la ronda 6, y era FALSO: `git` SÍ está.** MEDIDO
  `git --version` → `git version 2.55.0.windows.5`, y con el `GIT_DIR`
  desacoplado que usa `git_safe_commit.py`
  (`$env:GIT_DIR = "$env:LOCALAPPDATA\woptimizer_git\.git"`) el
  `git rev-parse --short HEAD` reproduce `49083d3` a la primera. O sea que la
  columna `HEAD` de este informe **sí** es reconstruible, y la frase anterior
  convertía una limitación del banco en una afirmación sobre el entorno. No se
  reconstruye igual porque el validador de `a31e585` no está en el árbol de este
  pase, pero la razón es otra y queda escrita.
- **Mutantes de código** — se copia el repo a `%TEMP%`, se aplica el mutante al
  fichero de la **copia** y se ejecuta **solo**
  `test_la_deuda_exige_un_ancla_resoluble_en_toda_fila_viva()` en un subproceso
  limpio. `run_tests.py` devuelve el **primer** test que revienta, luego sin el
  subproceso propio no se puede atribuir la muerte. El original de la copia se
  restaura y se **comprueba byte a byte** al final (medido: `True`).
- Todas las cadenas de abajo son **literales de byte**: una parafrasis no es
  re-auditable. Los `print()` son ASCII puro (trampa #16: consola cp1252).

**UNA TRAMPA DEL BANCO, medida en este pase, y se escribe porque es facil volver
a caer en ella.** `STATUS.md` es **CRLF PURO** (MEDIDO: 121 CRLF, 0 LF a secas,
0 CR sueltas). Anadir texto **al final de la linea** lo deja **detras del `\r`**,
y al releer con newlines universales el `\r` se come el resto: la fila mutada
**deja de existir** y el ataque se evapora solo, dando un falso «neutralizado»
—que es exactamente como se mediría mal una fila sin querer. Hay que insertar
**antes** del `\r`, y el banco **comprueba su propia inyeccion** antes de contar
nada: si el literal no aparece en lo que lee el validador, aborta en vez de
informar.

```powershell
python validate_docs.py            # 115 OK, 0 FAIL
python run_tests.py                # 104 tests, ALL TESTS PASSED
python verify_ui_syntax.py
```

---

## 2. Mutantes del PANEL (31) — `ok` y FAIL antes y despues

**Por que la linea `ok` va en la tabla y no en prosa.** Varios de estos mutantes
**no producen ni un `FAIL`**: o el ataque queda neutralizado, o es un residuo
declarado. Sin la linea `ok` antes/despues un reauditor los leeria como
«0 FAIL = correcto».

Formato de la linea `ok`: `fila(s) / exenta(s) / viva(s) / anclas / contenido`.

### 2.1 Lo que la ronda 4 CIERRA

| id | Fichero y edicion (antes -> despues) | `ok` HEAD | `ok` ARREGL | FAIL | Veredicto |
|---|---|---|---|---|---|
| **G2f'** | fila 88, tras `sandbox-rules.md\`)`: ` — **CERRADA en TASK-059**` | `15 / 8 / 7 / 33` | `15 / 7 / 8 / 35` | `0 -> 0` | **NEUTRALIZADO.** El id que cierra la fila tiene que estar CERRADO y `TASK-059` esta `pending`. |
| **G2f'b** | la misma fila con `TASK-061` (el otro unico `pending`) | `15 / 8 / 7 / 33` | `15 / 7 / 8 / 35` | `0 -> 0` | **NEUTRALIZADO.** No dependia de un id concreto sino del estado. |
| **G2f'c** | la misma fila con ` — **CERRADA en TASK-059, nunca se resuelvio**` | `15 / 8 / 7 / 33` | `15 / 7 / 8 / 35` | `0 -> 0` | **NEUTRALIZADO por la MISMA puerta**: la negacion en minuscula es residual, pero el id pendiente ya no cierra. Ver §4.7. |
| **H1** | fila nueva antes de la 88: `- **Fila que se ancla en un enlace DURO (H1):** su unica verdad es \`docs/panel_hard.md:1 Deuda\`, que existe y se resuelve.` + `os.link("STATUS.md", "docs/panel_hard.md")` en la COPIA | `16 / 7 / 9 / 36` (3 por contenido) | `16 / 7 / 9 / 35` (2 por contenido) | `0 -> 2` | **MUERE con este pase.** `VIVA sin ancla resoluble` + `ancla NO RESOLUBLE: docs/panel_hard.md EXISTE pero es el propio panel` |

### 2.2 Lo que sobrevive, y por que se declara

| id | Edicion | `ok` HEAD | `ok` ARREGL | FAIL | Veredicto |
|---|---|---|---|---|---|
| **G2f'd** | fila 88, ` — **CERRADA en TASK-055**` (id **ya cerrado**) | `15 / 8 / 7 / 33` | `15 / 8 / 7 / 33` | `0 -> 0` | **SOBREVIVE, y es EL residuo** (limite 19). Una fila que nombra trabajo de verdad terminado es indistinguible de una fila real cerrada. |
| **G2f'e** | fila 88, ` — **CERRADA en CYCLE-045**` (ciclo ya cerrado) | `15 / 8 / 7 / 33` | `15 / 8 / 7 / 33` | `0 -> 0` | **SOBREVIVE**, misma clase que G2f'd. |
| **G2f'f** | fila 88, ` — **CERRADA en TASK-055, nunca se resolvio**` | `15 / 8 / 7 / 33` | `15 / 8 / 7 / 33` | `0 -> 0` | **SOBREVIVE**, misma clase: el id cerrado y la negacion en minuscula. Ver §4.7. |
| **G2f'g** | fila 88, ` — **CERRADA en CYCLE-045, nunca se resuelvio**` | (no medido en HEAD) | `15 / 8 / 7 / 33` | `0 -> 0` | **SOBREVIVE**, misma clase. |
| **P4** | fila 89, tras `de invocaci`: ` **CERRADA en CYCLE-999**` | `15 / 8 / 7 / 22` | `15 / 8 / 7 / 22` | `0 -> 0` | **SOBREVIVE, y es G2f'd con otro disfraz**: MEDIDO que la 89 nombra `TASK-061` y `TASK-059` (los dos `pending`) **y `TASK-060` (`completed`)**, luego el `CYCLE-999` hereda el cierre de un id que sí estaba cerrado. El `CYCLE-999` no aporta nada. |
| **NO-ajeno** | fila 87, al final: ` NO es un aserto de cierre.` | `15 / 6 / 9 / 39` | `15 / 6 / 9 / 39` | `0 -> 0` | **SOBREVIVE, y es el PRECIO** (limite 21): una fila realmente cerrada deja de estar exenta por escribir `NO` en otra frase. Sigue en `0 FAIL` —la 87 demuestra su ancla—, luego es perdida de exencion, no rojo. |
| **G2a'** | fila 89, justo detras de su primer 🔴: ` 🟡 ` | `15 / 7 / 8 / 35` | `15 / 7 / 8 / 35` | `0 -> 0` | **SOBREVIVE**: gana la PRIMERA gravedad del texto (limite 15). |
| **G2b'** | fila 100: 🟡 -> 🟠 | `15 / 7 / 8 / 35` | `15 / 7 / 8 / 35` | `0 -> 0` | **SOBREVIVE**: un glifo fuera del mapa no es gravedad (limite 16). |
| **P9** | fila 100: `«96 tests»` -> `«42 tests»` | `15 / 7 / 8 / 35` | `15 / 7 / 8 / 35` | `0 -> 0` | **SOBREVIVE por decision** (limite 12: es una CITA atribuida, no una declaracion). |
| **P10** | fila 96: borra `CERRADA en CYCLE-027 (TASK-037) ` | `15 / 6 / 9 / 36` | `15 / 6 / 9 / 36` | `0 -> 0` | **CONTROL negativo**, sobrevive a proposito. |

### 2.3 Los que ya estaban neutralizados y NO han regresionado

La quinta condicion y el filtro por identidad de fichero se anaden al marcador
existente, y un guard anadido puede reanimar lo que otro apagaba. MEDIDO que no:
las nueve variantes que la ronda 3 dio por neutralizadas siguen dando exactamente
el panel intacto, con `0 FAIL`.

| id | Edicion | `ok` | FAIL | Veredicto |
|---|---|---|---|---|
| **P1** | fila 89, tras `de invocaci`: ` " Y esta fila NO esta CERRADA todavia."` | `15 / 7 / 8 / 35` | `0` | **NEUTRALIZADO.** |
| **P2** | fila 89, tras `ones de shell`: ` (marcada *CERRAD* en el panel)` | `15 / 7 / 8 / 35` | `0` | **NEUTRALIZADO.** |
| **P3** | fila 89, tras `de invocaci`: ` **NO CERRADA todavia** en TASK-061` | `15 / 7 / 8 / 35` | `0` | **NEUTRALIZADO.** |
| **V1** | fila 89, tras `de invocaci`: ` — **CERRADA, aunque NO lo pareca (TASK-061)**` | `15 / 7 / 8 / 35` | `0` | **NEUTRALIZADO.** |
| **V2** | fila 89: ` — **CERRADA**. NO lo esta: sigue pendiente TASK-061.` | `15 / 7 / 8 / 35` | `0` | **NEUTRALIZADO.** |
| **V3** | fila 89: ` — **CERRADAS todas en TASK-061**` | `15 / 7 / 8 / 35` | `0` | **NEUTRALIZADO.** |
| **V4** | fila 89: ` — **a diferencia de las CERRADAS, esta sigue viva (TASK-061)**` | `15 / 7 / 8 / 35` | `0` | **NEUTRALIZADO.** |
| **V5** | fila 89: ` — **NO: CERRADA en TASK-061**` | `15 / 7 / 8 / 35` | `0` | **NEUTRALIZADO.** |

**Y nueve que mueren por su propia asercion**, sin cambio respecto a la ronda 3:
**P5** (`2 -> 2`, ya en HEAD), **A1/A1a/A1b/A1c** (`2 -> 2`), **A1e** (`1 -> 1`),
**P6/P7** (`1 -> 1`), **N1b** (`1 -> 1`).

**La celda de P5, corregida.** La ronda 3 escribia `0 -> 2` en las dos columnas y
en la misma celda un veredicto que decia «MUERE (ya en HEAD)». **Las dos cosas no
pueden ser ciertas**: si ya muere en HEAD, la columna HEAD es `2`. MEDIDO en
`a31e585`: **2 FAIL**. La celda correcta es **`2 -> 2`**, y el veredicto se queda.

### 2.4 Recuento del panel

- **4 mueren** con este pase: G2f', G2f'b, G2f'c (por la quinta condicion) y H1
  (por la identidad de fichero).
- **9 ya morian** y siguen muriendo por su propia asercion.
- **8 quedan neutralizados**: no producen un `FAIL` **ni mueven un solo numero**.
- **10 sobreviven**, todas declaradas: G2f'd, G2f'e, G2f'f, G2f'g, P4, NO-ajeno,
  G2a', G2b', P9 y P10 — de las cuales **cuatro son la misma clase** (el residuo
  del limite 19), una es el **precio** de la regla de negacion (NO-ajeno) y una es
  un control negativo (P10).

---

## 3. Mutantes del CODIGO (22) — muerte medida en aislamiento

Se ejecutan **solo** sobre
`test_la_deuda_exige_un_ancla_resoluble_en_toda_fila_viva()` y en la **copia** de
`%TEMP%`, nunca en el árbol.

### 3.1 Los cinco que exige este pase, con su discriminacion medida

Cada fix lleva su test y el test se **comprueba rompiendo el fix**: se aplica el
mutante al validador de la copia y se exige que el test MUERA. Un test que
sobrevive a su propio fix roto no mide el fix.

| id | Mutante sobre el ORIGINAL | Muerte medida |
|---|---|---|
| **X** | `_esta_cerrada`: `return bool(_ids_cerrados(root, fila))` -> `return _porta_el_marcador_de_cierre(fila)` | **MUERE**, pero **no en el (x)**: la versión anterior de esta tabla decía «escenario (x)» y la §5 de la ronda 5 lo corrigió al **(r)**. MEDIDO el 2026-10-02 (ronda 6) contra la suite COMPLETA: **MUERE**, y el motivo es el que la §5 daba —el bucle de escenarios aborta en el PRIMERO que falla y `r` va antes que `x`—. Se escribe con la medición aislada, no con la esperada. |
| **C3** | `_ciclos_cerrados`: el registro pasa a mirar tambien `.taskmaster/rd_journal.json` | **MUERE en la ronda 4 y SOBREVIVE desde la ronda 5**, y el cambio es medido: con la capa (b) —la forma de ENTRADA `^##[ \t]+\[?(CYCLE-\d+)\]?`— puesta, esa forma no casa con nada de un journal que guarda `"cycle": <int>`, luego **mirar el journal o no es indistinguible**. La fila (c3) sigue ejecutando esa rama, pero ya no la ata. Ver RONDA 6 §2 y el límite 24. |
| **H2** | `_es_el_propio_panel`: `return _es_el_mismo_fichero(panel, otra)` -> se borra | **MUERE**: escenario (h2). El enlace duro volveria a colar |
| **F2** | el bucle: `if _esta_cerrada(root, fila) or autoeximida:` -> `if _esta_cerrada(root, fila):` | **MUERE**: escenario (f2). La autoexencion se preguntaria DESPUES del estado |
| **N2** | `_RE_NEGACION_DEL_CIERRE` -> `re.IGNORECASE` | **MUERE a proposito**, y es la fila que hace FALLO a un arreglo que nadie aplico: lleva las exentas a `0 exenta(s)` |

**El banco casi no discrimina C3 y hay que decirlo, porque es la clase de fallo
que un banco esconde.** En la primera pasada de esta ronda C3 **SOBREVIVIO**: el
test lo pasaba igual con la quinta condicion rota. Motivo MEDIDO: la fila de test
escribia el ciclo en el journal como `{"cycle": 901}` —un **numero**—, y lo que
`_RE_CICLOS` busca es el literal `CYCLE-901`, luego el id no resolvia por
**ningun** registro y la fila quedaba VIVA por el motivo del escenario (r), con
independencia del mutante. Y el hallazgo de fondo es que **el journal real
tampoco contiene ni un solo literal `CYCLE-NNN`**: guarda `"cycle": 45`. O sea
que la rama del journal de `_ciclos_de_la_fila` esta **inerte en este repo**, y
la fila (c3) es la unica que la ejecuta de verdad. Se escribe porque un banco que
reporta «el test no discrimina» sin decir **por que** es un banco a medias.

**Y una pieza de CODIGO que este pase borra, que se declara porque un borrado
tampoco es gratis.** La quinta condicion sustituyo a la tercera, y `_ids_cerrados`
**subsume** a `_ids_trazables` —exigir que un id este cerrado implica exigir que
exista—, luego `_ids_trazables` se queda **sin un solo llamante**. MEDIDO con
`grep` sobre todo el arbol: su unica aparicion era su propia definicion. Se
**borra** en vez de dejarse como decoracion, y no se nota ninguna perdida de
comportamiento: la tercera condicion era implicita en la quinta. Un mutante suyo
no figura en §3.1 porque **no hay codigo al que mutar**, que es el mismo caso que
C30 y por el mismo motivo.

### 3.2 Los trece de la ronda 3, sin cambio

| id | Edicion (antes -> despues) | Muerte medida |
|---|---|---|
| **C1** | el bucle de veredictos -> `return bool(_RE_CERRADA.search(...))` (la palabra suelta) | **MUERE**: `escenario l: la palabra de cierre en PROSA no exime a nadie: el check NO acuso ['VIVA sin ancla resoluble']` |
| **C2** | `_ruta_de_ancla`: la identidad -> `return real` | **MUERE**: `escenario n: el panel no puede certificarse a si mismo: el check NO acuso ['VIVA sin ancla resoluble', 'ancla NO RESOLUBLE: STATUS.md ...']` |
| **C3-b** | `if suelo and gravedad and gravedad != "ROJO":` -> `if False and ...` | **MUERE**: `escenario h: la gravedad baja y el problema sigue vivo: el check NO acuso ['declara AMARILLO pero su comprobable SIGUE VIVO']` |
| **C4** | la forma `^[ \t]*0[ \t]+CODIGO\b` -> el predicado viejo `(?<!\d)0\b[^\n]*CODIGO` | **MUERE**: `escenario q: mencionar el contrato no es DECLARAR el contrato: el check acuso ['su comprobable SIGUE VIVO'] y no debia` |
| **C5** | `_citas_de_la_fila`: borrar `if not palabras: continue` | **MUERE por la asercion del envoltorio, NO por el `IndexError`**: `validar(root) debia devolver un INFORME y tiro IndexError: list index out of range`. Es la correccion al informe anterior: el envoltorio captura la excepcion, luego lo que se mide es que el validador **no** entregue informe. |
| **C6** | S5: `elif derivado in anclas["numeros"]` -> `elif False and ...` | **MUERE**: `escenario o: el check acuso ['VIVA sin ancla resoluble', 'NO es el derivado con ast']` |
| **C7** | `derivado in anclas["numeros"]` -> `104 in ...` (constante a mano) | **MUERE**: mismo escenario `o`. El derivado de este arbol es 7, no 104. |
| **C8** | `run_tests.py`: `assert len(FILAS) == <N>` -> `== 99` | **MUERE**: `la tabla de escenarios del check 8 tiene <N> filas y su contrato son <N>` |
| **C9** | el `ok.append(...)` del check 8 -> `if False: ok.append(...)` | **MUERE**: `escenario a: el check NO imprimio su linea \`ok\` de la seccion` |
| **C13** | `if ids:` -> `if True:` | **MUERE**: `escenario r: veredicto en negrita con un id que NO resuelve: el check NO acuso ['VIVA sin ancla resoluble']` |
| **C25** | `findall(texto)` -> `[texto]` (la negrita deja de exigirse) | **SOBREVIVIO en el commit de esta ronda: MEDIDO el 2026-10-02 que la fila (u) NO lo mata** (`RESULTADO: PASA`, suite entera en verde). El motivo, medido: la (u) tiene el id **pendiente** (`TASK-002`), luego con el marcador en la prosa la fila no se cierra de todos modos y el recuento no se mueve. **La ronda 6 lo cierra con la fila (p1)** —marcador en la prosa con la `TASK-001` ya `completed`— y ahí **MUERE en (p1)**. Ver RONDA 6 §2. |
| **C26** | `_RE_CERRADA` -> `re.IGNORECASE` | **SOBREVIVIO a la tabla del check 8: MEDIDO el 2026-10-02 que la fila (s) NO lo mata** (`RESULTADO: PASA`), por la misma razón que C25: la (s) tiene el id pendiente. La **ronda 6 lo cierra con la fila (p3)** y ahí **MUERE en (p3)**. Y sobre el panel REAL `IGNORECASE` no es verde: MEDIDO `10 exenta(s) / 5 viva(s) / 24` anclas y **1 FAIL**, porque la 101 tiene «cerrada» en minúsculas en su prosa y la autoexención, insensible a caja, la acusa de autoeximirse. |
| **C28** | borrar la negacion sobre la **prosa** | **SOBREVIVIO en el commit de esta ronda: MEDIDO el 2026-10-02 que la fila (v) NO lo mata** (`RESULTADO: PASA`), misma razón: la (v) tiene el id pendiente. **La ronda 6 lo cierra con la fila (p4b)** y ahí **MUERE en (p4b)**. |
| **C29** | la identidad -> igualdad de cadena con `"STATUS.md"` | **MUERE**: `escenario w: el panel no se certifica a si mismo con otra GRAFIA: el check NO acuso ['VIVA sin ancla resoluble', 'ancla NO RESOLUBLE: status.md EXISTE pero es el propio panel']` |

**C27** (`limpio.replace('**','')`) y **C21** (la memoizacion de los ids)
**SOBREVIVEN y son INERTES**: no cambian ningun veredicto, solo evitan un calculo
repetido. Se archivan para que el proximo no los vuelva a medir esperando una
muerte.

**C30 ha dejado de existir como mutante.** Era «quitar `os.path.normcase` de la
comparacion» y **SOBREVIVIA, con una justificacion falsa** (ver §0). Decision de
este pase: **quitar la llamada**, porque lo que anunciaba no existia en ninguna
plataforma. Con la llamada fuera, el mutante no tiene a qué aplicarse y la
comparacion se ha ampliado por `(st_dev, st_ino)`, que es donde estaba de verdad el
agujero (H1). Lo que **no** se ha hecho es defender el panel de quien ya puede
escribir en el arbol, y su alcance queda escrito en el limite 22.

**Recuento del codigo: 19 mueren · 2 sobreviven (C21 y C27, inertes) · 1 mutante
retirado (C30) por decision, con su justificacion corregida.**

---

## 4. Lo que NO cubre ningun limite (leido como lista de afirmaciones)

Una lista solo de muertes es una lista que afirma cobertura del 100 %, que es
exactamente lo que este repo lleva 49 ciclos corrigiendo. Estas cosas **no** las
mata nadie, y estan escritas para que el proximo que audite no las descubra como
novedad:

1. **P1, P2, P3, V1-V5 no producen un FAIL en el panel real**: quedan
   neutralizados y su unico sintoma es el desplazamiento `7 exenta(s)/8 viva(s)` ->
   `8/7`, que ya no ocurre. MEDIDO de nuevo en esta ronda: los nueve dan el panel
   intacto, luego la quinta condicion no ha reanimado a ninguno.
2. **A1 no mueve la linea `ok` en el recuento**: el `35 -> 36` con el panel
   autocertificado solo se ve comparando este informe con el anterior.
3. **El suelo es inerte sobre el panel real**: neutralizarlo entero deja
   `115 OK / 0 FAIL`. MEDIDO ademas que **no hay fila victima ni con un glifo
   fuera del mapa (G2b') ni con una gravedad historica antes de la de hoy (G2a')**
   (limites 15 y 16): el suelo tiene hoy **cero** filas que puedan delatarlo.
   Y la medicion que lo sostenia **estaba mal escrita**: `_gravedad_declarada` da
   `ROJO` en **ocho** filas, no en una (ver §0).
4. **La gravedad que cuenta es la primera del texto**, luego una gravedad
   historica tapa la de hoy (G2a').
5. **P8**: el validador ya no muere, pero tampoco distingue el tramo vacio de una
   fila normal; solo se ve en la ausencia de traceback.
6. ~~**G2f' y P4 son el MISMO agujero, y no se puede cerrar.**~~ **CORREGIDO y
   CERRADO en esta ronda.** La frase era **más ancha que el agujero** y su tesis
   —«no hay regla que separe la fila 87 del ataque sin poner el repo en rojo»—
   era **falsa**. MEDIDO que los ids de las 7 exentas estan **todos dentro** del
   veredicto (87 → `TASK-055`/`CYCLE-045`, 99 → `TASK-054`/`CYCLE-044`,
   96 y 97 → `TASK-037`/`CYCLE-027`), luego «el id tiene que estar fuera del
   veredicto» no las separa de nada; y MEDIDO que los **dos unicos ids
   `pending`** del tablero son `TASK-059` y `TASK-061`, que son los que usaba el
   ataque. El eje que separa una cosa de otra es **cerrado/pendiente**. Con la
   quinta condicion puesta y el **panel intacto**: `7 exenta(s) / 8 viva(s) /
   35` anclas, `0 FAIL` y **ni una fila tocada**. Ver limite 19.
7. **Lo que de G2f' sobrevive, y es TODO lo que queda de este agujero:** nombrar
   un id **ya cerrado** (`TASK-055`, `CYCLE-045`) da `8/7/33, 0 FAIL`. No es
   cerrable con una regla de forma: una fila que nombra trabajo de verdad
   terminado es indistinguible de una fila real cerrada. El escenario (y) de la
   suite lo archiva como control negativo.
   ~~y P4 (`CYCLE-999` en la fila 89) tambien, porque la 89 nombra `TASK-060`
   `completed`.~~ **CORREGIDO en la ronda 6: es FALSO, y lo medí.** Anadir
   ` - **CERRADA en CYCLE-999**` a la fila 89 da `7 exenta(s) / 8 viva(s) / 35`
   anclas y `0 FAIL`, o sea que **la 89 NO se exime** y no puede ser ejemplo de
   nada. Motivo medido: su veredicto «🔴 VUELTA A 🔴 Y NO SE CIERRA» lleva un `NO`
   en mayusculas DENTRO de la negrita, y la regla de negacion rechaza el
   marcador de cualquier veredicto antes de mirar ningun id. El ejemplo que sí
   funciona es la **95**, y con el aislamiento del `CYCLE-998` (RONDA 6, §3) queda
   demostrado que su exención no viene del `CYCLE` sino del `TASK-057`.
8. **La negacion en MINUSCULA no se ve, y no se arregla.** MEDIDO que
   `re.IGNORECASE` lleva las **siete** exentas reales a **cero** y pone el repo en
   `1 FAIL`: en castellano `no` y `nunca` son prosa ordinaria, y hay negaciones
   de cierre **de verdad** que no niegan el cierre — la 93 dice «**CERRADA en la
   cola, no en el cuerpo**» y la 96 «**CERRADA en CYCLE-027 (TASK-037) — guardas
   que no guardaban**». No hay forma que separe `no en el cuerpo` de `nunca se
   resolvio`. El escenario (n2) lo archiva y **falla en rojo** a quien lo intente.
   Ver limite 21.
9. **Un `NO` ajeno en la prosa reabre una fila cerrada** (`15 / 6 / 9 / 39`,
   `0 FAIL`): es el **precio** de haber matado V2, y no se habia escrito. No es un
   rojo —la 87 demuestra su ancla—, es perdida de exencion. Ver limite 21.
10. **N1a**: una fila nueva puede mentir sobre el recuento y quedar en verde
    citando un fichero **en la misma frase** (limite 17).
11. **La `114 OK / 0 FAIL` de amputar el check 8** lo vigila **una** asercion
    (C9), y el **acoplamiento de `len(errors)`** del esqueleto de tests hace que un
    panel roto haga morir `test_el_journal_ilegible_informa_en_vez_de_reventar_el_validador`,
    cuyo sujeto es el journal: falla **ruido, no verde**. Declarado como limite
    **14** de `docs/ai/sandbox-rules.md`.
12. **C21 y C27 sobreviven y no son agujeros**: no cambian ningun veredicto. Se
    archivan como inertes para que el proximo no los vuelva a medir esperando una
    muerte.
13. **La rama del journal de `_ciclos_de_la_fila` es INERTE en este repo.**
    MEDIDO que `.taskmaster/rd_journal.json` guarda el ciclo como numero
    (`"cycle": 45`) y no contiene **ni una sola vez** la forma `CYCLE-045` que
    busca `_RE_CICLOS`. O sea que el journal **no** es un registro de ciclos
    consultable, aunque figure en la lista. La unica fila que lo ejecuta de verdad
    es la (c3), y lo hace escribiendo el literal a mano. No se arregla porque no
    es un agujero —no hay ningun `CYCLE-NNN` que resolver por ahi—: es una
    entrada de la lista que no hace nada, y se declara.

---

## 5. Controles negativos (NO deben morir)

Se archivan **como tales**: un control que sobrevive es una asercion de cobertura,
no un fallo. Y una de estas filas **tiene que morir**, que es al reves y tambien
es una asercion.

| id | Que hace | Medido por |
|---|---|---|
| **P10** | abrir la fila 96 borrando su cierre | aqui, `0 FAIL` y `6 exenta(s) / 9 viva(s) / 36` anclas |
| **(y)** | el mismo veredicto de (x) pero con una `TASK` ya `completed`: la fila SI se exime | aqui, `1 exenta(s) CERRADA(s), 0 viva(s)`. Archiva el residuo del limite 19 |
| **(n2)** | el veredicto de (y) con una negacion en minuscula: la fila SI se exime | aqui, `1 exenta(s) CERRADA(s), 0 viva(s)`, y **FALLA en rojo** a cualquiera que aplique `re.IGNORECASE` |
| **C21, C27** | inertes (§4.12) | aqui |
| **E4, A2, G3b, N2, M4b, C11, C14-C17, C20, C22** | controles y mutantes de rondas anteriores | **el auditor, no remedidos aqui.** Sus ediciones byte a byte **no estan en el repo**, de modo que re-medirlos exige pedirlos al auditor. Se declara en vez de inventarse una medicion |

---

## 6. Lo que este informe deja abierto

- **La fila 100 vive hoy con una cita desfasada**: dice que `docs/index.md:25`
  declara «96 tests» y ese fichero declara hoy `(104 tests)`. **No se corrige
  aqui** porque las filas del panel no se reescriben en este cambio, y porque la
  fila *documenta* el defecto. Queda dicho, medido y sin tocar; es el límite 12.
- **G2f' esta CERRADO y su residuo esta declarado**: nombrar un id ya cerrado
  sobrevive (§4.7) y no es cerrable con una regla de forma. Es una clase
  distinta y mas estrecha que la que las rondas anteriores declaraban, y esa
  diferencia es el resultado de este pase.
- **Dos residuos mas, ambos del mismo par de limites 20 y 21**: la negacion en
  minuscula (§4.8) y el `NO` ajeno en la prosa (§4.9). Los dos estan escritos
  con su medicion y con el motivo por el que **no** se arreglan.
- **La rama del journal de los ciclos es inerte** (§4.13): el journal no
  contiene la forma que se le busca. Declarado, no corregido.
- **El panel no se defiende de quien puede escribir en el arbol.** Un enlace duro
  —una accion deliberada, no un fichero que aparezca solo— queda cerrado por
  identidad de fichero (limite 22), y un atacante con permiso de escritura sigue
  estando fuera del alcance de este check.
- **Los controles E4, A2, G3b, N2, M4b, C11, C14-C17, C20 y C22** no son
  re-audibles desde el repo (ver §5).
- **El recuento de escenarios del test:** la tabla tiene hoy **42** filas y su
  contrato es `assert len(FILAS) == 42`. Su historia, para que se vea que el
  número es un **contrato y no una consecuencia**: 25 al nacer, **30** en la ronda
  4 (+ x, c3, h2, y, n2), **33** en la ronda 5 (+ x4, x4b, m2 y las que ya estaban
  a medio escribir) y **42** en la ronda 6 (+ cyc, p1, p2, p3, p4a, p4b, p5, m2c y
  m2d). **El numero de tests no cambio ni una vez: sigue en 104**, porque los
  escenarios son filas de una tabla y no tests. *(Las tres primeras frases de este
  párrafo decían «30» como si fuera el número del día, y era el número de una ronda
  ya cerrada; el `print()` de `run_tests.py` y la aserción de contratoaban de 30
  con 33 filas. Los seis sitios quedan unificados y el único número vigente es el
  que firma su propia ronda.)*

---

# RONDA 5 - el `CYCLE` se resolvia por SUBCADENA

**Medido contra `2229c12`** (HEAD al empezar este pase; el commit de la ronda 4,
`a31e585`, es el que midio la seccion anterior y lo declara en su `0`). Sin
`2229c12` en el informe, dentro de seis meses no se sabe contra que se midio la
columna HEAD, y un informe sin baseline no se puede re-auditar.

## 0. EL HALLAZGO, y por que la ronda 4 no lo podia ver

`_ciclos_cerrados` cerra un ciclo con `if any(c in registro for registro in
registros)`: una **SUBCADENA**. Los dos changelogs publican `CYCLE-001` a
`CYCLE-049`, luego `"CYCLE-04" in changelog` es `True` porque esta **dentro** de
`CYCLE-045`, y `"CYCLE-04]" in changelog` es `False`. `CYCLE-04` **no es un ciclo
de este repo** y el validador lo contaba como cerrado.

| id | Edicion, sobre el panel real | `ok` HEAD (ronda 4) | `ok` con el FIX (ronda 6) | Que mutacion muere y donde |
|---|---|---|---|---|
| **N1** | fila 88 + ` - **CERRADA en CYCLE-04**` | `15 / 8 / 7 / 33`, `0 FAIL` | `15 / 7 / 8 / 35`, `0 FAIL` | **MUERE.** El prefijo `CYCLE-04` dentro de `CYCLE-045` ya no exime, y el sitio de su muerte es el escenario **(x4)** |
| **N2** | fila 88 + ` - **CERRADA en CYCLE-0**` (siete caracteres) | `15 / 8 / 7 / 33`, `0 FAIL` | `15 / 7 / 8 / 35`, `0 FAIL` | **MUERE.** Mismo camino que N1, en el mismo escenario **(x4)**: el truncado es un prefijo |
| **N3** | fila 88 + ` - **CERRADA en CYCLE-999**` + una linea `## [CYCLE-999]` en el changelog tecnico | `15 / 8 / 7 / 33`, `0 FAIL` | `15 / 8 / 7 / 33`, `0 FAIL` | **NO es un agujero: es el fix funcionando.** Con la entrada **publicada**, exime y debe eximir. Lo que se declara es el residuo del limite 19 («nombrar un id ya cerrado»), y su control negativo es **(y)** |
| **N4** | fila 88 + ` - **CERRADA en CYCLE-04, nunca se resolvio**` | `15 / 8 / 7 / 33`, `0 FAIL` | `15 / 7 / 8 / 35`, `0 FAIL` | **MUERE**, pero por un motivo distinto: la negacion es un residuo declarado (limite 21) y el **prefijo** de N1 ya no cuela. Sin la negacion, N4 seria N1 |

**Las cuatro filas de esta tabla se MEDEN en las DOS columnas y por eso la tabla
tenia una fila fuera de la rejilla y una contradiccion**: la columna «`ok` HEAD» es
la de `2229c12`, **antes** del fix, y la de «con el FIX» es la de este commit. N1,
N2 y N4 sobreviven al estado **anterior** y mueren al **actual**; N3 sobrevive a los
dos, y no porque quede un agujero sino porque es el comportamiento correcto. La
version anterior de esta tabla decia «SOBREVIVE» en la columna unica y luego, tres
lineas mas abajo, que la 88 **no** quedaba exenta con N3: las dos cosas no podian ser
ciertas, y era la tabla la que estaba rota, no las mediciones.

**N3, aislado, con el FIX puesto:** con la fila 88 (la que usa el resto de la tabla) y
`CYCLE-999` **sin** entrada publicada da `7 exenta(s) / 8 viva(s) / 35`, `0 FAIL`; y
**con** la entrada `## [CYCLE-999]` publicada da `8 exenta(s) / 7 viva(s) / 33`,
`0 FAIL`. O sea que **el `CYCLE-999` solo cuenta si su entrada existe**, que es
justo lo que el fix decide. El ataque de N3 **no** se reproduce en la 95 como puerta
nueva: MEDIDO que cambiar `CYCLE-999` por `CYCLE-998` —que tampoco existe en ningun
registro— en la 95 da **exactamente lo mismo** (`8/7/35`, `0 FAIL`), luego su
exención viene del `TASK-057` `completed`, que es el residuo ya declarado del limite
19 con su escenario (y). Lo que sí era nuevo y sí se ha cerrado es el **prefijo**:
`CYCLE-04` dentro de `CYCLE-045`, que la 88 sí sufría y que era el agujero central.

**El dano medido con la fila 88 sin NINGUNA otra fuente** (rotas todas sus citas
de ruta, para que el ataque no tenga un salvavidas): sin el ataque
`7/8/33, 1 FAIL` (`VIVA sin ancla resoluble`), y con N1 `8/7/33, 0 FAIL`.
**Veinticuatro caracteres que nombran un ciclo inexistente convierten un rojo en
verde.** Y N1 sobrevive a los 104 tests: `ALL TESTS PASSED`, rc 0.

N1 y N4 son el mismo caso (la negacion en minuscula es el residuo ya declarado),
y **N2 no es lo que el auditor dijo**: `CERCADA` no es el marcador de cierre
(`_RE_CERRADA` es `\bCERRAD[OA]\b`), luego `**CERCADA en CYCLE-0**` deja la fila
VIVA, `7 exenta(s) / 8 viva(s) / 35`, `0 FAIL`. El id truncado que **si** cuela
es `**CERRADA en CYCLE-0**`, y es el que mide el escenario (x4b).

## 1. EL FIX, en dos capas, y por que dos

- **(a) literal completo**: `re.escape(c) + r"\b"`. MEDIDO que mata `CYCLE-04` y
  `CYCLE-0`, porque `4` y `5` son los dos caracteres de palabra y no hay limite
  entre ellos.
- **(b) la forma de la ENTRADA**, `^##[ \t]+\[?(CYCLE-\d+)\]?` en `MULTILINE`,
  con el id **capturado entero** y comparado como token.

(a) sola no basta: MEDIDO que un `CYCLE-045` citado en **prosa** ("La fila cita
CYCLE-045 al pasar") ya contaria como cerrado, porque basta con que el token
APAREZCA. (b) sola tampoco: un regex **sin grupo de captura** casa `CYCLE-04`
contra `## [CYCLE-045]` porque el `5` que sigue no se mira. Es el mismo fallo de
subcadena un nivel mas adentro.

MEDIDO con las dos: los 49 ids publicados siguen resolviendo, y `CYCLE-04`,
`CYCLE-0`, `CYCLE-09` y `CYCLE-999` **mueren los cuatro**, con el panel intacto
(`7 exenta(s) / 8 viva(s) / 35` y `0 FAIL`) y **sin tocar una sola fila de Deuda**.
Las dos grafias que el repo escribe de verdad (`## CYCLE-048` en el de raiz y
`## [CYCLE-048]` en el tecnico) las cubre el corchete opcional; exigir solo una
pondria el repo en rojo.

## 2. M2: el guard que vigila al vigilante estaba atado al vigilante

Si la autoexencion se preguntaba con `_porta_el_marcador_de_cierre` --la misma
funcion que decide si la fila esta cerrada de verdad--, entonces **si esa funcion
se debilita, el guard se debilita con ella**. MEDIDO: **siete** mutaciones suyas
(aceptar el marcador en prosa, aceptar el prefijo en vez de la palabra, aceptar
minusculas, ignorar la negacion del veredicto, ignorar la de la prosa, no borrar
el codigo inline, y aceptarlo en toda la fila) dejan el panel real en
`7 exenta(s) / 8 viva(s)` y `0 FAIL` y **no las delata ninguna de las 42 filas de
la tabla**.

Se **des-acopla**: la autoexencion pregunta la forma MAS AMPLIA que tiene
sentido --la fila se nombra a si misma y lleva `CERRAD[OA]` en mayusculas fuera de
codigo inline--, sin exigir negrita, sin mirar la negacion y sin mirar el estado,
porque esas tres son preguntas de EVALUACION. MEDIDO que **no cambia ningun
veredicto de las 15 filas reales** (la 101 nombra el check pero no lleva marcador
en mayusculas fuera de codigo inline), luego el des-acoplamiento no compra nada a
cambio de un falso positivo. Cuesta **3 lineas**, y su unico escenario nuevo es
el (m2), que **MUERE al volver al acoplamiento** (`MUERE:m2`) y **pasa** con el
des-acoplamiento.

**Lo que NO se declara, medido:** el des-acoplamiento **no** hace que la tabla
mate las mutaciones de `_porta_el_marcador_de_cierre`. MEDIDO que tres de ellas
(aceptar el marcador en prosa, aceptar el prefijo en vez de la palabra, aceptar
minusculas) **siguen pasando** la tabla con el fix puesto. Lo que cambia es que
la **autoexencion** deja de seguirlas, que es justo el acoplamiento que se
pretendia cerrar. Afirmar lo contrario seria escribir un informe mas ancho que su
fix.

**CORREGIDO en la ronda 6, y la afirmacion era correcta en su momento pero
incompleta de un modo que la hacia inutil como informacion:** esos tres
supervivientes, y **siete mas**, no estaban «acoplados a la autoexencion»: estaban
**invisibles** porque toda su cobertura —(u), (l), (m), (s), (v), (f1)— usaba un
`**id pendiente**`, y con un id pendiente la fila no se cierra de **ninguna** de las
dos maneras, luego la forma del marcador no podia mover un solo numero. La ronda 6
anade las seis filas `p*`, que son **marcador DEFECTUOSO con un id YA CERRADO**:
la unica combinacion en la que la forma decide el veredicto. Ver RONDA 6 §1 y §2.

## 3. LO QUE SE BORRA, y lo que no

- `_RE_ID_TRAZABLE`: **borrada**. La condicion de trazabilidad que describia ya no
  existe --la quinta la subsume-- y la constante estaba definida y nunca leida.
- `_RE_DECLARACION_DE_CODIGO`: **reconectada**, no borrada. `_declara_el_
  sobrecargado` construia su patron en linea, luego la forma estaba **definida dos
  veces** en el mismo fichero. Ahora la constante es la definicion unica.
  MEDIDO y escrito en el codigo: componiendo solo `.pattern` se **pierden los
  flags** de la constante compilada y el escenario (h) muere; se recompila con
  `re.MULTILINE` explicito.
- El bloque de comentario que describia la condicion de trazabilidad: **borrado**,
  porque describia algo que el codigo ya no hace.

El guard de codigo muerto (`run_tests.py:11650`) mira `src/woptimizer/**` y por
eso no caza nada de esto: es TASK-056 repetido en el tooling.

## 4. LIMITE 5, REESCRITO CON SU MEDICION REAL

La version anterior citaba la **fila 89** y **`22` anclas**, y **no reproduce**.
MEDIDO hoy, con el panel de este commit:

| donde | edicion | resultado | reproduce lo que decia |
|---|---|---|---|
| fila 89 | ` - **CERRADA en CYCLE-999**` | `7 exenta(s) / 8 viva(s) / 35`, `0 FAIL` | **NO** |
| fila 95 | ` - **CERRADA en CYCLE-999**` | `8 exenta(s) / 7 viva(s) / 35`, `0 FAIL` | **SI** |

**Por que la 89 no sirve de ejemplo**, que es lo que el limite no decia: su
veredicto «VUELTA A ROJA Y **NO** SE CIERRA: bajarla a 🟡 sin cerrar el problema
es documentacion *fail-open*» lleva un `NO` en mayusculas **dentro de la
negrita**, y la regla de negacion rechaza el marcador de cualquier veredicto asi
**antes de mirar ningun id**. El mecanismo existe, pero en la 95. Y la linea base
es **35** anclas, no `22`.

## 5. FILA X, CORREGIDA CON LA MEDICION AISLADA

La tabla de §3.1 decia que el mutante X (quitar la quinta condicion) **MUERE en el
escenario (x)**. **Realmente muere en el (r)**, y la leccion es la que ya se
aplico a la ronda 4: **el bucle de escenarios aborta en el PRIMERO que falla**, y
`r` va antes que `x` en la tabla. El mutante muere igual, pero **el sitio de
muerte declarado no era el medido**, que es justo lo que viene a comprobar un
re-auditor. Anotado aqui con su medicion, no con la esperada.

## 6. LOS TRES RESIDUOS QUE EL INFORME TENIA QUE DECIR

1. **La rama del journal de `_ciclos_de_la_fila` es INERTE**: el journal real
   tiene **cero** literales `CYCLE-NNN` y **49** `"cycle": <int>`. C3 esta cerrado
   y cubierto, y el diagnostico era el correcto, pero el residuo **no figuraba en
   la lista de limites**. Ahora es el limite **24**.
2. **La guardia `st_ino != 0` no tiene test ni victima**: en NTFS `st_ino` vale un
   entero de 16 digitos, **nunca `0`**, luego **quitar la guardia no muere nada**.
   Es correcta en un sistema de ficheros sin indice, pero nadie la ha medido y por
   tanto nadie puede romperla aqui. Ahora es el limite **25**.
3. **La fila 101 tiene 117 `**` (impar)**: MEDIDO que `_RE_NEGRITA` extrae 58
   veredictos y que un veredicto bien formado anadido a la fila **no aparece entre
   los extraidos**. O sea que hoy la 101 esta **protegida por un accidente de
   formato, no por la regla**, y el escenario (f2) usa una fila sintetica
   **balanceada**, luego el comportamiento real de la fila del criterio no estaba
   cubierto. El escenario **(m2)** lo cubre por donde el Markdown no decide
   (marcador en la prosa). **No se corrige el desbalance**: es una fila de Deuda y
   su regla es *solo anadir, nunca reescribir*. Ahora es el limite **26**.
   ~~(impar: `False`; par: `True`)~~ **CORREGIDO en la ronda 6: el contraste
   «par: `True`» NO reproduce.** MEDIDO que con la fila a 119, 120, 121 y 123
   asteriscos el veredicto anadido **no aparece en ninguno** de los cuatro casos, y
   que lo que de verdad protege a la 101 es la **autoexencion**, que no usa
   negrita y **falla en ROJO** (`8/7/27` y `1 FAIL`). Ademas **la 89 tiene 63 `**` y
   la 96 tiene 21**, las dos impares y **ninguna declarada**. Todo ello, con su
   tabla, en el limite **26** reescrito y en RONDA 6 §4.

## 7. LO QUE ESTA CERRADO Y NO SE HA TOCADO

La separacion del (f2), el enlace duro y la quinta condicion contra una `TASK`
pendiente estaban cerrados **y con test que los distingue**; esta ronda no los
ha tocado. El ataque de panel a la autoexencion sigue sin colar (`7/8/35, 0 FAIL`),
el enlace duro reproduce `0 FAIL / 36` -> `2 FAIL / 35`, y M3, M5, M6 y las cuatro
mutaciones literales de §3.1 siguen muriendo con su asercion.

---

# RONDA 6 - LA MITAD POSITIVA DEL FIX NO LA MEDIA NADIE

**Medido contra `49083d3`** (HEAD al empezar este pase; el commit de la ronda 5,
`2229c12`, es el que midio la seccion anterior). Sin cambios en `src/`: este pase
toca `run_tests.py`, `validate_docs.py`, `docs/ai/sandbox-rules.md`, `STATUS.md` y
este informe.

## 0. EL BASELINE, DECLARADO

- `python validate_docs.py` -> **`115 OK, 0 FAIL`**. Panel: **15 filas, 7 exentas,
  8 vivas, 35 anclas** de ruta resuelta y **2** por contenido.
- `python run_tests.py` -> **`ALL TESTS PASSED`**, **104 tests**. El numero de
  tests **no cambia** en esta ronda: los nueve escenarios nuevos son **filas de la
  tabla** del test del check 8, no tests.
- La tabla de escenarios del check 8 pasa de **33** a **42** filas, y su contrato
  pasa de `assert len(FILAS) == 33` a `== 42`. El `print()` de `run_tests.py`
  decia «30 filas» con 33 en el fichero, y los tres numeros convivian.
- `validar(REPO real)`: **3,70 s**, `0` errores, `115` `ok`. Y `git` **si** esta:
  `git version 2.55.0.windows.5`, y con el `GIT_DIR` desacoplado
  `git rev-parse --short HEAD` reproduce `49083d3`. Ver §7, donde se corrige la
  afirmacion contraria que hacia la ronda 4.
- El informe anterior daba por muertas tres mutaciones con un escenario y un
  mensaje. **Las tres sobreviven.** Ver §3.

### 0.1 EL ORDEN DE LAS MEDICIONES, y lo que NO se ha podido re-verificar

Esta ronda se ejecutó en el orden siguiente, y las salidas literales de cada paso
son las que da este mismo §0.1 punto por punto:

1. Las **catorce** sustituciones de codigo en `run_tests.py` y `validate_docs.py` (doce
   y tres) se hicieron con un script de bytes que **comprueba cada literal antes de
   escribir** y **aborta sin escribir** si un literal no aparece el numero exacto de
   veces. Despues se releyeron los ficheros de vuelta y `ast.parse` respondio
   `AST OK`. Ese script **aborto y dejo el fichero intacto** una vez, cuando un
   literal mio traia un caracter roto, que es exactamente para lo que existe la
   comprobacion.
2. `python run_tests.py` -> `ALL TESTS PASSED`, **RC=0**, ya con las catorce.
   (Hubo un `m2c`/`m2d` en rojo en el intento anterior: las dos filas tienen la
   `TASK-002` **pendiente** como fuente, luego no son «VIVA sin ancla» sino filas
   **no autoeximidas**, y la expectativa correcta es la **ausencia** del error de
   autoexención más el recuento. Anotado porque es el mismo error de criterio que
   produjo trece supervivientes: exigir el motivo equivocado.)
3. `python validate_docs.py` -> `115 OK, 0 FAIL`, **RC=0**, y
   `python verify_ui_syntax.py` -> `EXITO`, **RC=0**.
4. Despues se escribieron **solo ficheros de texto**: `docs/ai/sandbox-rules.md`,
   `STATUS.md` y este informe. Las seis sustituciones de `STATUS.md` son **dentro de
   linea**, asi que no pueden haber introducido ni perdido un `\r` (el fichero es
   CRLF y anadir texto detras de un `\r` lo deja invisible: la trampa).
5. **Lo que NO se ha podido hacer:** repetir las cuatro verificaciones **despues**
   de esas ediciones de texto, ni commitear. MEDIDO que el shell del entorno dejo de
   poder crear subprocesos (`spawn EPERM` del propio runtime, que falla incluso con
   un `Write-Output`) y no se recupero en ~30 intentos a lo largo de tres turnos.
   Como la regla de este repo es que un informe sin verificacion final es un
   informe sin cerrar, **queda pendiente y asi se dice**: las cuatro verificaciones
   literales y la linea `WOPT_*` del commit las tiene que ejecutar quien recoja el
   arbol. Lo que si consta por escrito es el estado del arbol en el momento del
   bloqueo, y los dos ultimos verdes literales son los del punto 3, anteriores a las
   ediciones de texto.

## 1. EL HALLAZGO DE FONDO, y por que es estructural

**Los tres llamantes de `validar` que tenia la suite apuntaban a un ARBOL
TEMPORAL.** MEDIDO: los tres son llamadas a `_informe_del_validador_real(...)` con
un `tmp`/`esqueleto` construido con `_copiar_el_esqueleto_del_validador`. O sea que
**ningun test validaba el repo real**, y por eso la mitad positiva del fix --la que
pregunta si un `CYCLE` de verdad cierra una fila-- solo la ejecutaba
`python validate_docs.py`, que es un comando y no un test.

De ahi salia todo lo demas, y ahora se ve por que eran tantos supervivientes:

1. **X3** (`_ciclos_cerrados` -> `return []`): la mitad positiva **anulada**, y
   **SUITE ENTERA EN VERDE**. Motivo medido: las filas (x), (c3), (x4) y (x4b)
   comprueban que un ciclo **NO** cierra, y **ninguna** que **SI**. Un invariante
   del que solo se mide el lado negativo no esta medido.
2. **X1** (el id capturado se descarta, grupo no capturante): la capa (b) inutil, y
   suite entera en verde por lo mismo.
3. **X2** (busqueda por prefijo del id, con el grupo de captura fuera): aqui **si**
   lo mata, en **(x4)**. MEDIDO: `MUERE en (x4)`, con la definicion de bytes exacta
   en la tabla de §2. Lo dejo escrito porque el `mutation-auditor` de la ronda 5 lo
   declaro vivo con otra definition del mismo nombre —`findall` de un patron sin
   grupo de captura, que es el mutante **X1** de arriba—, y con esa otra
   definition **si** sobrevive. Dos mutantes con el mismo nombre y distinta
   definicion se distinguen por los bytes, no por la etiqueta.

Y el motivo por el que la cobertura estaba tan repartida: **las filas (u), (l),
(m), (s), (v) y (f1) usaban todas un id PENDIENTE**. Con un id pendiente la fila no
se cierra de **ninguna** de las dos maneras, luego la forma del marcador no puede
mover un solo numero y el mutante pasa por lo que sea. Solo (y) y (n2) cerraban de
verdad, y las dos usan una `TASK`.

## 2. LOS NUEVE ESCENARIOS, y que mutante mata cada uno

El criterio es uno solo, y es el que faltaba: **marcador DEFECTUOSO con un id YA
CERRADO**. Es la unica combinacion en la que la FORMA decide el veredicto.

| fila | que mide | mutante nominal | sitio de muerte MEDIDO |
|---|---|---|---|
| **(cyc)** | un `CYCLE` con **entrada publicada** en los changelogs del arbol CIERRA la fila | X3, X1 | el propio (cyc) |
| **(p1)** | el marcador en la **prosa** con la `TASK-001` ya `completed` | P1, **C25** | el propio (p1) |
| **(p2)** | el **plural** `**CERRADAS todas**` con la `TASK-001` ya `completed` | P2 | el propio (p2) |
| **(p3)** | el marcador en **minusculas** con la `TASK-001` ya `completed` | **C26** | el propio (p3) |
| **(p4a)** | el veredicto que **niega** el cierre (`NO lo parece`) | P4a | el propio (p4a) |
| **(p4b)** | la **prosa** que niega el cierre | **C28** | el propio (p4b) |
| **(p5)** | el marcador solo entre **acentos graves** dentro del veredicto | P5 | el propio (p5) |
| **(m2c)** | la fila del criterio en **minusculas** NO se autoexime | M2C | el propio (m2c) |
| **(m2d)** | la fila del criterio con el marcador **entrecomillado** NO se autoexime | M2D | el propio (m2d) |

**El `CYCLE` de (cyc) se DERIVA de las entradas publicadas del arbol copiado**, no
se escribe a mano: un id fijo mediria un arbol que el test no construye, y en
cuanto el changelog avanzara un ciclo mediria un id que ya no esta. Es la misma
leccion que el `CYCLE-901` de la ronda 4, escrita al reves. MEDIDO que con este
arbol el id derivado es `CYCLE-049`, y que es el **ultimo** publicado por los dos
changelogs, luego la fila se exime por la misma razon por la que lo haria cualquier
otro: tener **entrada**.

**La tabla tiene 42 filas y el contrato es 42**, y las nueve nuevas estan **todas**
en la zona de la capa positiva: las que comprueban que un marcador **DEFECTUOSO**
no cierra y la que comprueban que un marcador **correcto** si. Antes solo estaba
la segunda clase, con id pendiente, que es la combinacion donde nada decide nada.

**MEDIDO, con el codigo de este commit, contra la tabla del check 8 (17 mutantes,
uno por subproceso limpio):**

| mutante | veredicto | donde |
|---|---|---|
| X3 (capa positiva anulada) | **MUERE** | (cyc) |
| X1 (id capturado descartado) | **MUERE** | (cyc) |
| X2 (prefijo en la capa (b)) | **MUERE** | (x4) |
| C25 / P6 (`findall` -> `[texto]`) | **MUERE** | (p1) |
| C26 / P3 (`re.IGNORECASE`) | **MUERE** | (p3) |
| C28 (negacion de la prosa) | **MUERE** | (p4b) |
| P1 (marcador en la prosa) | **MUERE** | (p1) |
| P2 (prefijo de palabra) | **MUERE** | (p2) |
| P4a (negacion del veredicto) | **MUERE** | (p4a) |
| P5 (codigo inline no borrado) | **MUERE** | (p5) |
| M2C (autoexencion sin caja) | **MUERE** | (m2c) |
| M2D (autoexencion con inline) | **MUERE** | (m2d) |
| S2 (autoexencion sin exigir el criterio) | **MUERE** | (d) |
| H2 (enlace duro) | **MUERE** | (h2) |
| F2 (orden de la pregunta) | **MUERE** | (f2) |
| **P4c** (la negacion se busca en la fila entera) | **SOBREVIVE** | dueno: limites 20 y 21 |
| **C3** (el registro vuelve a mirar el journal) | **SOBREVIVE** | dueno: limite 24 |

**Los dos supervivientes que quedan son inertes, y por eso se declaran en vez de
inventarles una muerte:**

- **P4c**: MEDIDO que pone el panel real en `6 exenta(s) / 9 viva(s) / 39` anclas y
  `0 FAIL` -- reabre la **87**, cuyo veredicto de cierre lleva un `NO` en OTRO
  veredicto. Es exactamente el residuo ya declarado del limite 21 («una negacion
  escondida en otro veredicto reabre una fila cerrada»), con su medicion y su
  dueno. No es un agujero de forma: es el **precio** de haber matado la regla que
  si distingue el `NO` propio.
- **C3**: desde que la capa (b) exige la forma de ENTRADA
  `^##[ \t]+\[?(CYCLE-\d+)\]?`, esa forma **no casa con nada** de un `.json` que
  guarda `"cycle": <int>`, luego **mirar el journal o no es indistinguible**.
  Anadido al limite 24, que ya declaraba la rama inerte de `_ciclos_de_la_fila`.

## 3. LAS TRES MUERTES QUE EL INFORME DECLARABA Y NO REPRODUCEN

Con la medicion aislada de cada mutante, y aplicando la leccion de la ronda 4
--**anotar el PRIMERO que falla, no el que se espera**--, la tabla queda asi:

| mutante | lo que decia el informe | MEDIDO antes de este pase | MEDIDO ahora |
|---|---|---|---|
| **C25** (`findall(texto)` -> `[texto]`) | «MUERE: escenario (u)» | **SOBREVIVE**: la (u) tiene el id **pendiente**, luego el recuento no se mueve | **MUERE en (p1)**, con la `TASK-001` ya `completed` |
| **C26** (`re.IGNORECASE`) | §3.1 decia «MUERE: escenario (s)» y §5 decia «muere en el (r)»: **las dos vivas** | **NO muere en la tabla del check 8**; en la suite entera si, en otro test | **MUERE en (p3)**, con la `TASK-001` ya `completed` |
| **C28** (borrar la negacion de la prosa) | «MUERE: escenario (v)» | **SOBREVIVE**: la (v) tiene el id **pendiente** | **MUERE en (p4b)**, con la `TASK-001` ya `completed` |

**La contradiccion de C26 era real y su resolucion es «en ninguno de los dos»:** la
fila (s) tiene `TASK-002` pendiente, luego con `IGNORECASE` el marcador minusculo la
exime, pero sin marcador la fila tampoco se cierra, luego el recuento es identico y
la asercion pasa igual. La muerte de `IGNORECASE` en la suite entera esta en otro
test y no en esta tabla; la de la ronda 6 es **local y de primera fila**, que es lo
que un re-auditor puede comprobar sin leer el resto del repo.

**C25 y C28 NO se declaran muertas a la ligera:** se ha medido que sobreviven al
estado anterior con `RESULTADO: PASA` y que mueren en el estado de este commit con
un escenario concreto. Lo que se retira es la afirmacion de que morian antes.

## 4. LAS MEDICIONES DE PANEL DE ESTE PASE

### 4.1 Mutantes de PANEL, sobre una copia completa del repo (sin `.git`)

Con la inyeccion comprobada byte a byte en lo que el validador lee —una fila mal
insertada detras de un `\r` se evaporaria y mediria otra cosa—:

| edicion | panel | FAIL |
|---|---|---|
| sin ataque | `15 / 7 / 8 / 35` + 2 | `0` |
| fila 88 + `**CERRADA en CYCLE-04**` (N1) | `15 / 7 / 8 / 35` | `0` |
| fila 88 + `**CERRADA en CYCLE-0**` (N2) | `15 / 7 / 8 / 35` | `0` |
| fila 88 + `**CERRADA en CYCLE-999**` sin entrada publicada (N3b) | `15 / 7 / 8 / 35` | `0` |
| fila 88 + `**CERRADA en CYCLE-999**` **con** entrada publicada (N3) | `15 / 8 / 7 / 33` | `0` |
| fila 88 + `**CERRADA en CYCLE-04, nunca se resolvio**` (N4) | `15 / 7 / 8 / 35` | `0` |
| fila 89 + `**CERRADA en CYCLE-999**` | `15 / 7 / 8 / 35` | `0` |
| fila 95 + `**CERRADA en CYCLE-999**` | `15 / 8 / 7 / 35` | `0` |
| fila 95 + `**CERRADA en CYCLE-998**` (id que tampoco existe) | `15 / 8 / 7 / 35` | `0` |
| fila 98, primer ROJO -> AMARILLO | `15 / 7 / 8 / 35` | `0` |
| fila 101 + `**CERRADA en TASK-060, cerrada de verdad.**` | `15 / 8 / 7 / 27` | **`1`** |
| fila 101 + `**CERRADA en TASK-059, cerrada de verdad.**` | `15 / 8 / 7 / 27` | **`1`** |
| fila 101 + un `**` suelto (118) | `15 / 7 / 8 / 35` | `0` |

Cuatro cosas se leen aqui, y las cuatro se corrigen en los limites:

1. **La 89 NO se exime** (§4.7 de la ronda 5 decia que si). Su veredicto lleva un
   `NO` en mayusculas DENTRO de la negrita, luego la regla de negacion rechaza el
   marcador antes de mirar ningun id.
2. **La 95 se exime, pero por su `TASK-057`**: con `CYCLE-998`, que tampoco existe
   en ningun registro, sale **exactamente igual**. O sea que el `CYCLE` de ese
   veredicto no aporta nada, y el limite 5 queda con su medicion de aislamiento.
3. **Bajar la 98 a AMARILLO sale en VERDE** (§7), y **cerrar el desbalance de la 101
   no cambia nada** (§6).
4. **Ninguna de las nueve filas nuevas se apoya en el panel real**: son las de
   §4.1, sobre copias con el panel intacto. Las que si lo hacen son las de §4.2.

### 4.2 El PANEL REAL con cada MUTANTE DE CÓDIGO aplicado

`validar(REPO)` con el validador mutado en memoria y `root` = el repo de verdad, o
sea que se juzga el panel que hay y el codigo es el mutado. **Esta es la tabla que
justifica las nueve filas**: la mitad de los mutantes son **invisibles** al panel
real, luego ningún test sobre el panel real podría detectarlos.

| mutante | panel real con el mutante | FAIL |
|---|---|---|
| sin mutante | `15 / 7 / 8 / 35` | `0` |
| X3 (capa positiva anulada) | `15 / 7 / 8 / 35` | `0` |
| X1 (id capturado descartado) | `15 / 7 / 8 / 35` | `0` |
| X2 (prefijo en la capa (b)) | `15 / 7 / 8 / 35` | `0` |
| C25 (`findall` -> `[texto]`) | `15 / 6 / 9 / 39` | `0` — **reabre una exenta real** |
| C26 (`re.IGNORECASE`) | `15 / 10 / 5 / 24` | **`1`** |
| C28 (negacion de la prosa) | `15 / 7 / 8 / 35` | `0` |
| P1 (marcador en la prosa) | `15 / 7 / 8 / 35` | `0` |
| P2 (prefijo de palabra) | `15 / 7 / 8 / 35` | `0` |
| P4a (negacion del veredicto) | `15 / 7 / 8 / 35` | `0` |
| P4c (negacion en la fila entera) | `15 / 6 / 9 / 39` | `0` — reabre la 87 |
| P5 (codigo inline no borrado) | `15 / 7 / 8 / 35` | `0` |
| M2C (autoexencion sin caja) | `15 / 8 / 7 / 27` | **`1`** |
| M2D (autoexencion con inline) | `15 / 8 / 7 / 27` | **`1`** |
| S2 (autoexencion sin el criterio) | `15 / 7 / 8 / 35` | **`7`** |
| C3 (el registro mira el journal) | `15 / 7 / 8 / 35` | `0` |

**Lo que dice esta tabla y es el motivo de existir de las nueve filas:** nueve
mutantes dejan el panel real **exactamente igual**. Un test que solo mirase el
panel real —por muy bueno que fuera— no los veria. Los que el panel real **si**
delata son C26, M2C, M2D y S2, y los delata en **rojo** (`1`, `1`, `1` y `7` `FAIL`),
que es justo lo que ahora exige la fase contra el repo real de §5.

## 5. EL TEST QUE VALIDA EL REPO REAL

Ademas de las nueve filas, el test del check 8 ejecuta ahora `validar` **contra el
repo de verdad** y afirma la **linea `ok`** de la seccion, no un numero escrito a
mano. Lo que comprueba, en este orden:

- que la linea `ok` **exista** (amputar el check 8 entero la hace desaparecer y el
  validador baja a `114 OK / 0 FAIL`, que es verde);
- que su `N fila(s)` **cuadre con las filas `- **` de la seccion real del
  `STATUS.md`**, contadas con un conteo **PROPIO** y no con `_filas_de_deuda`: un
  guardian que cuenta con la misma funcion que juzga no puede notar que esa funcion
  dejo de contar, que es justo lo que hace un `return` borrado;
- que `exentas + vivas == filas`, y que **las dos** sean `>= 1` (o el criterio se
  apago entero, o el panel entero se dio por cerrado: las dos son un panel que no
  vigila);
- que la seccion este en **ROJO con cero `FAIL`**.

**MEDIDO: 3,70 s**, y el numero de tests **sigue en 104** porque la fase va dentro
del test del check 8 y no es un test nuevo. La alternativa --un test aparte-- habria
costado ademas subir el recuento declarado a 105 en `AGENTS.md`, `README.md`,
`STATUS.md` y la tabla de `docs/ai/testing-guide.md`, que es exactamente la cascata
que hace que un informe se quede a medias.

## 6. EL LIMITE 26, REESCRITO, Y LAS DOS FILAS QUE FALTABAN

El limite 26 afirmaba que la 101 esta «protegida por un accidente de formato» y lo
sustentaba en un contraste que **no reproduce**: MEDIDO que anadiendo un veredicto
bien formado a la 101 a **119, 120, 121 y 123** asteriscos, el veredicto **no aparece
entre los extraidos en los cuatro casos**, ni con el recuento par. El emparejamiento
de `**...**` es posicional: un `**` suelto empareja con el primero del veredicto
nuevo y a partir de ahi todo va desplazado, luego **la paridad no lo arregla**.

Lo que de verdad protege a la 101 es la **autoexencion**, que **no usa negrita**: y
eso **falla en ROJO**, con `8/7/27` y `1 FAIL`, no en verde. El escenario (m2) **no lo
cubria** porque usa un arbol sintetico; ahora lo ata al codigo la fase contra el
repo real de §5.

**Las dos filas que faltaban, declaradas:** la **89 tiene 63 `**`** y extrae 31
veredictos, y la **96 tiene 21** y extrae 10. Las tres impares, ninguna declarada.

## 7. LO QUE SE CORRIGE EN EL INFORME ANTERIOR

- **§1 «No hay `git` en este entorno»**: es **falso**. MEDIDO `git version
  2.55.0.windows.5` y, con el `GIT_DIR` desacoplado, `HEAD` reproduce `49083d3`. La
  columna `HEAD` **si** es reconstruible; lo que no esta en este arbol es el
  validador de `a31e585`, y son dos cosas distintas.
- **§4.7 «la 89 sobrevive»**: es **falso**, y esta corregido en §4 de esta ronda.
- **El 30/33**: unificado. El unico numero vigente es el que firma su ronda, y el
  contrato del codigo es `assert len(FILAS) == 42`.
- **La tabla N1-N4**: reconstruida con una columna de **que mutacion muere y donde**,
  con las dos columnas medidas (antes del fix y con el fix) y con N3 declarado como
  residuo declarado y no como agujero.
- **El limite 4**: «rebajar la 98 a AMARILLO sale en rojo» es **falso**; sale en
  verde, y el motivo --que la 98 no ancla `git_safe_commit.py` y su suelo es ninguno--
  es un agujero mas ancho que el enunciaba, con su propio limite, el **27**.

## 8. EL MENSAJE QUE MENTIA

El validador acusaba a la fila del criterio «lleva el marcador de cierre **en un
veredicto**», y **MEDIDO que el marcador esta en la PROSA**: la autoexencion no usa
negrita, y la 101 lo lleva ahi. Un semaforo que acusa con un motivo falso entrena a
ignorar el semaforo, asi que el mensaje dice ahora lo que mide: «lleva el marcador
de cierre en **MAYUSCULAS y FUERA de codigo inline**».

## 9. LO QUE ESTA SIN CERRAR

- **P4c** y **C3** sobreviven, con dueno (limites 20/21 y 24) y con su medicion.
- **El limite 27** declara que trece de las quince filas **no tienen suelo** de
  gravedad, y que el suelo vigila hoy **una sola** (la 89). No se arregla porque un
  suelo derivado exigiria escribir a mano la politica de gravedad del repo.
- **El escenario (m2)** sigue sin cubrir la 101 real por si mismo; lo que la ata es
  la fase contra el repo real.
- **La guardia `st_ino`** y el resto de limites abiertos de la ronda 5 siguen como
  estaban.
- **La medicion de `X`, `P4c` y `C3` contra la suite COMPLETA** (no solo la tabla del
  check 8) no se pudo terminar: el shell dejo de crear subprocesos. Lo que si consta
  es que `P4c` y `C3` **pasan la tabla del check 8** con su codigo actual, y que la
  tabla va dentro de la suite, luego un muerte-alli es un muerte-en-la-suite; lo que
  no se ha medido es si **alguno de los dos los mata otro test mas adelante**, que es
  la unica forma que tendria de dejar de ser superviviente.
- **Las cuatro verificaciones finales y el commit**, pendientes por lo mismo. Ver
  §0.1 punto 5. Quien recoja el arbol las tiene que ejecutar y pegar su salida, y
  el commit tiene que llevar el marcador `ciclo #49`.
