# Informe de mutacion - ciclo 71 (TASK-090) - **RONDA 4**

> RONDA 4 del `mutation-auditor` ( Sherlock ). Se auditan DOS cosas:
> (1) el GATE de mutacion (check 11 de `validate_docs.py`) con su GUARD en
> `run_tests.py`, y (2) el CHECK 12 NUEVO (commit `ccf59ca`), que verifica que
> la skill del motor mande publicar en `beta`.
>
> La ronda 3 dio FAIL con 4 supervivientes (M-108, M-109, M-110, M-112). El dev
> (ronda 5, commit `110b9ab`) afirmaba haberlos cerrado y haber medido 23/23
> MUERTO. aqui se mide con una arnes PROPIA: el veredicto del dev se
> CONFIRMA para el gate, y el check 12 NO AGUANTA lo que se le pide.

## 0. RESUMEN EJECUTIVO

| | |
|---|---|
| **VERDICT** | **FAIL** (el gate: PASS. el check 12: FAIL) |
| **MUERTO** | 6 (M-108, M-109, M-110, M-112, M-91, M-92) |
| **SOBREVIVIENTE** | 9 (M-121 + los 8 mutantes del check 12) |
| **NO MEDIDO** | 0 |
| **Base** | `rc=0`, 312.3 s, 477 lineas, `ALL TESTS PASSED.` como ULTIMA linea |
| **Arbol auditado** | `4f2f115` (el repo se movio durante la auditoria: `ccf59ca` -> `4f2f115`) |

**Lo que se confirma**: el dev tiene razon en que los cuatro mutantes que la
ronda 3 dejo vivos (M-108, M-109, M-110, M-112) mueren ahora, y mueren por la
ASERCION declarada. Los cuatro sentinelas nuevos (M-FIX-SIN-LINEA,
M-FIX-LIMITE, M-FIX-CHANGELOG, M-FIX-INFORME-CORTO) tienen dientes: M-121 lo
demuestra (neutralizar la celda que caza a M-109 y el gate se queda mudo).

**Lo que NO aguanta**: el CHECK 12 (nuevo en este ciclo) no lo vigila NINGUN
test de la suite. MEDIDO con grep sobre `run_tests.py`: CERO referencias a
`paso_de_publicacion`, `_lineas_que_el_motor_lee`, `_ORDEN_DE_PUBLICACION`,
`"check 12"` o `"publicas el ciclo en"`. Sus ocho mutantes pasan la suite en
verde. Ademas, a NIVEL DE PRODUCTO (el validador real), dos de ellos no los
muerde ni el propio check: **C-9** (la orden escondida en una valla con
prefijo `> `) y **C-7** (el check sin cablear) salen con **0 FAIL**.

## 1. EL APAREJO (lo que hace la medicion creible)

### 1.1 La camara, y por que NO es el repo

El repo tiene el `.git` DESACOPLADO (`%LOCALAPPDATA%\woptimizer_git\.git`) y el
arbol de trabajo se copia a `%TEMP%` con:

- `shutil.copytree(..., ignore=shutil.ignore_patterns(".git", "__pycache__"))`.
  El `.git` de este repo es un FICHERO de 57 bytes (`gitdir: ...`): `robocopy
  /XD` NO lo excluye (solo excluye directorios), y `ignore_patterns` si.
- `git init` PROPIO en la camara (`git rev-parse --git-dir` = `.git` de la
  camara, MEDIDO antes de mutar nada), identidad local, `commit.gpgsign=false`.
- Entorno de corrida SIN `GIT_DIR`, SIN `GIT_WORK_TREE` y SIN `GIT_AUTHOR_*`
  (MEDIDO: esas variables cambian el sha de una fixture y ponen la suite
  entera en rojo por un motivo ajeno).
- `__pycache__` purgado ANTES de cada corrida.
- Los ficheros tocados restaurados entre mutantes, y una comprobacion que
  **ABORTA** la mutacion si mueve el numero de lineas. MEDIDO: `run_tests.py`
  se cita a si mismo POR NUMERO (`sandbox-rules.md:55-56`), luego un mutante
  que lo desplaza se cuela un rojo ajeno. Me pasó con M-121 en su primera
  version (murio en `test_las_citas_de_sandbox_rules_siguen_siendo_ciertas`, no
  en el asa) y se re-midio con una sustitucion que conserva las lineas.

### 1.2 LA BASE

| | |
|---|---|
| rc | **0** |
| duracion | **312.3 s** |
| lineas de log | 477 |
| ultima linea | `ALL TESTS PASSED.` |
| `[FAIL]` en el log | 0 |
| parches | **NINGUNO** |

La base es VERDE NATIVA, sin tocar nada. Eso NO fue posible en la primera
medicion, y el motivo es un hallazgo que no estaba en el encargo:

**MEDIDO: el commit `ccf59ca` (el check 12) dejo la suite EN ROJO en HEAD.**
Dos rojos, los dos del check 12 y ninguno del gate:

1. `run_tests.py:24100` — `assert len(skips) == 3`: el `--sin-ancla-de-git`
   imprime **cuatro** `[SKIP]`, porque el check 12 mete el suyo ("este arbol no
   tiene `.agents/skills/id-pipeline/SKILL.md`") en toda fixture minima.
2. `run_tests.py:24268` — `assert not saltados`: ese mismo `[SKIP]` llena el
   canal `saltados` de un fixture que no tiene `.agents/`.

El rojo es REPRODUCIBLE (rc=1, 194.3 s, el primer fallo en
`test_sin_ancla_de_git_no_se_parece_a_un_verde`). El dev lo arreglo durante la
auditoria, en el commit `4f2f115` ("el check 12 calla cuando no hay skill que
verificar"): ahora, sin skill y sin `.agents/`, el check **no dice nada**
(ni OK, ni SKIP, ni FAIL), y la base sale verde sola.

### 1.3 El arbol se movio durante la auditoria

La medicion arranc�� sobre `ccf59ca` y el repo recibio `4f2f115` a mitad. Las
cameras son COPIAS CONGELADAS, luego las mediciones son validas para el arbol
que copiaron; el informe declara cual. La medicion DEFINITIVA es la de
`4f2f115`, con base verde nativa y sin parches:

| camara | arbol | parche de base | uso |
|---|---|---|---|
| A | `ccf59ca` | 2 aserciones (declaradas) | contraprueta del gate |
| B, C | `4f2f115` | 2 aserciones (INCOMPATIBLES) | **descartados**: contaminados |
| E, F, G, H | `4f2f115` | ninguno | **medicion definitiva** |

Las camaras B y C se copiaron DESPUES del fix del dev, luego sus parches de
base (que esperaban 4 `[SKIP]`) ya no cuadraban: su suite estaba en rojo antes
de mutar. Esas corridas se descartan y se repiten en E/F/G/H.

## 2. TABLA: mutante -> mutacion -> veredicto -> motivo LITERAL

El **motivo literal** es la ultima linea de la cola, y el **asa** es el test
que tiene que morir. Los tres estados del contrato: MUERTO, SOBREVIVIENTE,
NO MEDIDO.

### 2.1 EL GATE (check 11) Y SU GUARD

| id | mutacion | asa | veredicto | motivo LITERAL | s |
|---|---|---|---|---|---|
| M-108 | `if identificador not in por_mutante:` -> `if False and ...` | `test_el_check_9_se_cablea_en_el_camino_real_del_validador` | **MUERTO** | `EL GATE NO DISTINGUE` | 160.8 |
| M-109 | `>= CICLO_ORIGEN_VEREDICTO` -> `> CICLO_ORIGEN_VEREDICTO` | el mismo | **MUERTO** | `EL GATE NO DISTINGUE` | 143.8 |
| M-110 | `if m.group("estado") != estados[identificador]:` -> `if False and ...` | el mismo | **MUERTO** | `EL GATE NO DISTINGUE` | 146.0 |
| M-112 | `if del_informe != del_journal:` -> `if del_informe - del_journal:` | el mismo | **MUERTO** | `EL GATE NO DISTINGUE` | 149.5 |
| M-91 | `if estado_derivado != estado_declarado:` -> `==` | el mismo | **MUERTO** | `EL GATE ACUSA EN LO QUE NO PUEDE` | 152.5 |
| M-92 | `for ... in mutantes:` -> `in mutantes[:1]:` | el mismo | **MUERTO** | `EL GATE NO DISTINGUE` | 147.6 |
| M-121 | **meta**: la celda (D1-ter)(d) del LIMITE y la asercion de `entradas cubiertas` neutralizadas, y M-109 aplicado | el mismo | **SOBREVIVIENTE** | `ALL TESTS PASSED.` | 338.9 |

### 2.2 EL CHECK 12 (nuevo)

El check 12 se mide en DOS niveles, porque no son lo mismo: la **SUITE** (lo que
vigila el bucle) y el **PRODUCTO** (lo que dice el validador real). El `asa` de
estos mutantes es **NINGUNO**: no hay ningun test que los pueda matar (ver 4.1).

| id | mutacion | veredicto SUITE | motivo LITERAL | veredicto PRODUCTO | lo que dice el validador |
|---|---|---|---|---|---|
| C-1 | la ORDEN (`publicas el ciclo en \`beta\``) desaparece de la skill | **SOBREVIVIENTE** | `ALL TESTS PASSED.` | **MUERTO** | `[FAIL] ... NO manda publicar. Faltan: orden` |
| C-2 | la ORDEN se queda dentro de una VALLA real | **SOBREVIVIENTE** | `ALL TESTS PASSED.` | **MUERTO** | `[FAIL] ... Faltan: orden` |
| C-9 | la ORDEN se queda dentro de una valla CON PREFIJO `> ` | **SOBREVIVIENTE** | `ALL TESTS PASSED.` | **SOBREVIVIENTE** | **NO LO ACUSA**: `164 OK, 2 FAIL` (falso verde) |
| C-3 | la ORDEN se queda dentro de un COMENTARIO HTML | **SOBREVIVIENTE** | `ALL TESTS PASSED.` | **MUERTO** | `[FAIL] ... Faltan: orden` |
| C-4 | el COMANDO desaparece de sus tres apariciones | **SOBREVIVIENTE** | `ALL TESTS PASSED.` | **MUERTO** | `[FAIL] ... Faltan: comando` |
| C-5 | el recorte deja de excluir las VALLAS | **SOBREVIVIENTE** | `ALL TESTS PASSED.` | **MUERTO** | `[FAIL] ... el control de valla FALLA` |
| C-6 | el recorte deja de excluir los comentarios MULTILINEA | **SOBREVIVIENTE** | `ALL TESTS PASSED.` | **SOBREVIVIENTE** | **NO LO ACUSA** (su control es de una linea: ver 4.3) |
| C-7 | el check 12 deja de estar CABLEADO en `validar()` | **SOBREVIVIENTE** | `ALL TESTS PASSED.` | **SOBREVIVIENTE** | **NO DICE NADA**: ni OK, ni FAIL, ni SKIP |

## 3. EL GATE (check 11) Y SU GUARD: RESISTEN

**PASS.** Los cuatro mutantes que la ronda 3 dejo vivos mueren ahora, cada uno
por la asercion que declara su rama, y con el frame EXACTO del asa declarada:

- **M-108** (el catalogo declara un mutante que el journal NO lleva) ->
  `EL GATE NO DISTINGUE`. El centinela nuevo `M-FIX-SIN-LINEA` lo caza.
- **M-109** (`>=` -> `>`: la entrada del LIMITE, el ciclo 70, queda sin mirar) ->
  `EL GATE NO DISTINGUE`. Lo caza el centinela nuevo `M-FIX-LIMITE`.
- **M-110** (los changelogs con un estado discrepante de la evidencia) ->
  `EL GATE NO DISTINGUE`. Lo caza `M-FIX-CHANGELOG`.
- **M-112** (el informe del ciclo se queda corto) -> `EL GATE NO DISTINGUE`. Lo
  caza `M-FIX-INFORME-CORTO`.

**La afirmacion del dev ("23/23 MUERTO") se CONFIRMA en lo que importa**: los
cuatro que estaban vivos ya no lo estan, y los dos canonicos de siempre
(M-91, la comparacion invertida; M-92, el catalogo truncado) siguen muriendo.

**Y los sentinelas nuevos tienen dientes: MEDIDO (M-121).** M-121 es un
mutante del GUARD: neutraliza la celda (D1-ter)(d) (la que exige la
acusacion de la entrada del LIMITE) y la asercion de `entradas cubiertas`, y
aplica M-109. La suite queda **VERDE** (rc=0, 338.9 s): sin esas dos celdas,
nadie nota que M-109 deja sin mirar el origen del contrato. O sea: esas dos
aserciones son lo UNICO que caza a M-109, y no son decorativas. (M-121 es el
unico SOBREVIVIENTE que NO es un defecto del producto: es un mutante del
test, y su supervivencia es la MEDICION.)

## 4. EL CHECK 12 (nuevo): NO AGUANTA

### 4.1 No hay NINGUN test que lo vigile

MEDIDO con grep sobre `run_tests.py` (32697 lineas): CERO referencias a
`paso_de_publicacion`, `_lineas_que_el_motor_lee`, `_ORDEN_DE_PUBLICACION`,
`_COMANDO_DE_PUBLICACION`, `_COMPROBACION_DE_PUBLICACION`, `"check 12"` o
`"publicas el ciclo en"`. La unica coincidencia de `origin/beta` esta en un
docstring del CI, sin relacion.

O sea: los ocho mutantes del check 12 pasan la suite en VERDE. Esto es
exactamente el limite (f) que el propio ciclo 71 declara para el gate ("el
validador, por si solo, NO detecta un gate ciego; solo la suite lo hace"),
aplicado al check 12: **el validador no lo detecta y la suite no lo vigila**.
El gate 11 se cerro con doce sentinelas; el check 12 se ha anadido sin
ninguno.

**Y no es un tecnicismo de forma: el contrato del gate 11 lo exige.** El gate
deriva el veredicto de cada mutante del catalogo y ACCUSA si el `asa` no es un
test definido en `run_tests.py` ("el asa declarada por X NO es un test
definido en run_tests.py"). Por eso los mutantes del check 12 NO pueden
entrar en `mutaciones.json`: no tienen `asa` que declarar. Su catalogo va
aparte, en `mutaciones-check12.json`, y esa separacion ES la formalizacion
del hueco.

### 4.2 C-9: el recorte no ve las vallas con prefijo `> ` (FALSO VERDE)

MEDIDO, con el mecanismo probedo en isolation (`_lineas_que_el_motor_lee`):

```
trozo = "> ```bash\n> publicas el ciclo en `beta` (`git push origin beta`)\n> ```\n"
recorte del CHECK 12 : la ve? True     <- lee la valla como PROSA
recorte del GUARD DE LA REGLA DE RAMA: la ve? False   <- la excluye
```

El recorte del check 12 decide con `linea.lstrip().startswith("```")`: la valla
tiene que EMPEZAR en la linea. El guard de la regla de rama (`run_tests.py`)
usa una REGEX (`r"```.*?```"`), que no le importa el `> ` de la cita. **No son
el mismo recorte**, contra lo que afirma el docstring del check 12 ("Es el
mismo recorte que usa el guard de la regla de rama").

Y el caso no es hipotetico: **el propio `SKILL.md` usa esa forma** en su
ejemplo de git (lineas 61-68: `> ```bash` ... `> ``` `), con
`git push origin beta` dentro. Una instruccion de publicacion escrita ahi
(como la de C-9) la veria el motor como un EJEMPLO, y el check 12 la
certificaria como operativa: `164 OK, 2 FAIL` y ningun `[FAIL]` del check 12.

### 4.3 C-6: el control interno del comentario no vigila su rama

El check 12 tiene tres controles internos. El de la valla (C-5) MUERDE. El del
comentario HTML **no**: su control usa un comentario de UNA linea
(`<!-- nota: ... -->`), que pasa por la rama del comentario cerrado en la
misma linea, que es OTRA rama del recorte. La rama que C-6 rompe es la del
comentario MULTILINEA, y MEDIDO con la mutacion aplicada:

```
UNA LINEA (la que usa el control): el recorte ve la frase? False
MULTILINEA (la rama que C-6 rompe): el recorte ve la frase? True   <- con C-6
```

O sea: una instruccion de publicacion escondida en un comentario HTML de
varias lineas la ve el check 12 como operativa. Hoy el efecto es nulo (0
comentarios HTML multilinea en el repo, MEDIDO por el propio docstring del
guard de la regla de rama), luego es una guarda que no vigila la rama que dice
vigilar: latente, no activo.

### 4.4 C-7: el check 12 se puede apagar en silencio

`validar()` acaba en `return _comprobar_el_paso_de_publicacion(...)`. Sin esa
llamada el check no dice NADA: ni un `[OK]`, ni un `[FAIL]`, ni un `[SKIP]`, y
el validador sale con el mismo resumen que con el check vivo. El resto del
validador tiene la disciplina D1/D2/D3 (sin defaults, cableado explicito,
"un `None` en esta posicion se lee como 'no hay nada que comprobar'"); el
check 12 no la tiene, porque nadie comprueba que este cableado este.

## 5. LO QUE QUEDA VIVO

| id | donde vive | por que sobrevive | que necesita |
|---|---|---|---|
| C-1..C-9 | suite | el check 12 no tiene ningun test | un test en la suite (o el equivalente), con un corpus que degrade la skill y un centinela por rama |
| C-9 | producto | el recorte no ve las vallas con prefijo `> ` | el recorte tiene que tratar `> ``` ` como valla (o reusar el recorte del guard de la regla de rama) |
| C-6 | producto | el control interno del comentario es de una linea y no toca la rama multilinea | el control tiene que llevar un comentario MULTILINEA |
| C-7 | producto | el cableado del check no lo comprueba nadie | un centinela que exija que el check 12 SUENE (una `[OK]` o un `[FAIL]`) |

## 6. LO QUE SE ENCOLA COMO TAREA

Cada NO MEDIDO es una Tarea, no un veredicto. Aqui no hay NO MEDIDO, pero los
supervivientes que tocan el proceso de versionado y de datos SI son tareas:

- **T-1 (ALTA)** — El check 12 necesita un guard de suite. MEDIDA: con el
  corpus actual, los ocho mutantes del check 12 pasan en verde. El
  `asa` que hay que declarar: el test que tiene que morir. Sin el, el check 12
  es un `[OK]` que nadie vigila.
- **T-2 (ALTA)** — El recorte del check 12 tiene que ver las vallas con
  prefijo `> ` (C-9). MEDIDA: con la orden dentro de la valla que el propio
  `SKILL.md` usa, el check 12 da `164 OK` y ningun `[FAIL]`.
- **T-3 (MEDIA)** — El control interno del comentario HTML tiene que llevar un
  comentario MULTILINEA, o el recorte multilinea queda sin vigilar (C-6).
- **T-4 (MEDIA)** — El cableado del check 12 tiene que ser comprobable: un
  centinela que exija que el check SUENE (C-7).
- **T-5 (BAJA, doc)** — El mensaje del guard enumera "tres de la ronda 3"
  donde la ronda 3 anadio CUATRO sentinelas: no nombra `M-FIX-LIMITE`. El
  recuento "DOCE" cuadra, pero la enumeracion no deja claro que el del LIMITE
  esta. El texto de la guarda es lo que se leeria en un rojo.
- **T-6 (MEDIA, cadena)** — La evidencia que escribe el emisor
  (`.taskmaster/veredicto.py`) no la puede re-derivar el gate para los
  mutantes cuyo mensaje de asercion EMBARCA un traceback (M-108: el validador
  revienta con un `KeyError` y su traceback va dentro del mensaje). MEDIDO: con
  la cola que escribe el emisor (desde el ULTIMO traceback), el gate deriva
  `NO MEDIDO`; con la cola que empieza en el traceback del TEST, deriva
  `MUERTO`. El motivo es doble: (a) el mensaje de la asercion lleva un
  traceback MAS TARDE que el del test, y (b) al redirigir, stdout va
  bufferizado y stderr no, luego la intercalacion pone el traceback de un hilo
  de Tk al final del log. La cadena emisor->gate no puede afirmar MUERTO
  sola: el veredicto de esta ronda se ha escrito con una cola que SI lleva el
  frame del asa, y se ha VERIFICADO contra la funcion del gate antes de
  escribirla (el que escribe la evidencia no puede decidir el veredicto).

## 7. BLOQUE DE MAQUINA

Las lineas canonicas de los mutantes del GATE. El orquestador las copia al
journal (campo `veredictos` de la entrada del ciclo 71) y a los DOS changelogs.
Los mutantes del CHECK 12 van FUERA de aqui a proposito: el gate 11 compara
este bloque con el journal, y un mutante que no esta en `mutaciones.json` lo
acusaria.

<!-- WOPT_VEREDICTOS -->
WOPT_VEREDICTO M-90 MUERTO b88b2ae33530
WOPT_VEREDICTO M-93 MUERTO d7d2b995d878
WOPT_VEREDICTO M-94 MUERTO b0b968047ccd
WOPT_VEREDICTO M-95 MUERTO 3973606dc7dd
WOPT_VEREDICTO M-96 MUERTO 89ddcc7d268a
WOPT_VEREDICTO M-97 MUERTO 074778d2956a
WOPT_VEREDICTO M-98 MUERTO 1dd1e558bce0
WOPT_VEREDICTO M-99 MUERTO ebe692afd206
WOPT_VEREDICTO M-100 MUERTO 0f8030d69dda
WOPT_VEREDICTO M-101 MUERTO 9144057b0b38
WOPT_VEREDICTO M-102 MUERTO f3e94843d979
WOPT_VEREDICTO M-103 MUERTO 309ae523826c
WOPT_VEREDICTO M-104 MUERTO fe09da634cd0
WOPT_VEREDICTO M-105 MUERTO f70bd036c768
WOPT_VEREDICTO M-106 MUERTO 41986f08d7f7
WOPT_VEREDICTO M-107 MUERTO e5f02d611e7c
WOPT_VEREDICTO M-111 MUERTO 7ab54a5181a7
WOPT_VEREDICTO M-108 MUERTO 0f667bdb0600
WOPT_VEREDICTO M-109 MUERTO 0f667bdb0600
WOPT_VEREDICTO M-110 MUERTO 0f667bdb0600
WOPT_VEREDICTO M-112 MUERTO 0f667bdb0600
WOPT_VEREDICTO M-121 SOBREVIVIENTE 0a28b28104c6
WOPT_VEREDICTO M-91 MUERTO 0f667bdb0600
WOPT_VEREDICTO M-92 MUERTO 04ecf0f9573f
<!-- /WOPT_VEREDICTOS -->

## 8. QUE SE ESCRIBIO EN EL REPO (y que NO)

**SI**:

- `mutaciones.json` — las 23 de la ronda 3 (con el `sha_arbol_auditado`
  actualizado en las re-medidas) mas `M-121`.
- `mutaciones-check12.json` — los 8 mutantes del check 12, FUERA del catalogo
  del gate 11 porque no tienen `asa` (ver 4.1).
- `evidencia/<mutante>.cola` — la cola de cada mutante medido en esta ronda.
  La de los mutantes que NO se han re-medido NO se toca.
- `mutation-report.md` — este informe. El de la ronda 3 queda en
  `mutation-report-ronda-3.md` (no se pisa un entregable).

**NO**:

- NO se toca `validate_docs.py`, ni `run_tests.py`, ni
  `.agents/skills/id-pipeline/SKILL.md`, ni `STATUS.md`.
- NO se toca `.taskmaster/rd_journal.json`: la entrada del ciclo 71 con sus
  `veredictos` la escribe el orquestador (seccion 7).
- NO se comitea nada.

## 9. PRUEBA DE NO-CONTAMINACION

El repo real, al terminar:

```
git rev-parse --git-dir  ->  C:\Users\carch\AppData\Local\woptimizer_git\.git
git log --oneline -1      ->  4f2f115 fix(validate): el check 12 calla cuando no hay skill que verificar (CYCLE-071)
git status --porcelain    ->  (vacio)
git diff --stat           ->  (vacio)
git diff --cached --stat  ->  (vacio)
```

La camara tiene su PROPIO `.git` (directorio): `git rev-parse --git-dir` desde
la camara devuelve `.git` (el suyo), nunca `%LOCALAPPDATA%`. Ningun commit de
camara (`arbol base auditado`) aparece en el historial del repo real: MEDIDO
con `git log --all | grep "arbol base"` -> vacio.

### 9.1 La prueba de coherencia (el paso entero del orquestador)

MEDIDO en camara (la copia de `4f2f115` con los artefactos de esta ronda):

| escenario | rc | Resumen |
|---|---|---|
| los artefactos de esta ronda, SIN la entrada de journal | 1 | 164 OK, 2 FAIL, 0 SKIP |
| + la entrada de journal del ciclo 71 con sus 24 lineas | 1 | 163 OK, 2 FAIL, 0 SKIP |
| + los DOS changelogs con su entrada de ciclo y su bloque | **0** | **165 OK, 0 FAIL, 0 SKIP** |

El gate 11 re-deriva **26 mutantes** (los 24 de este cambio + los 2 del ciclo
70) **sin un solo FAIL**: el catalogo, la evidencia commiteada y el bloque de
maquina del informe son COHERENTES entre si, y el gate los lee igual que los
lee el emisor. Los dos FAIL que quedan en los dos primeros escenarios son la
obligacion del changelog (el paso que le toca al orquestador), no una
incoherencia de los artefactos.

## 10. VERDICT

**FAIL.**

- **El GATE (check 11) y su guard: PASS.** Los cuatro supervivientes de la
  ronda 3 mueren por su asercion, los dos canonicos de siempre siguen
  muriendo, y M-121 demuestra que los centinelas nuevos tienen dientes. La
  afirmacion del dev ("23/23 MUERTO") se CONFIRMA.
- **El CHECK 12: FAIL.** No lo vigila ningun test (8 de 8 mutantes pasan la
  suite en verde) y, a nivel de producto, dos de sus controles no lo muerden:
  **C-9** (falso verde con la valla que el propio `SKILL.md` usa) y **C-7**
  (el check se apaga en silencio). El tercero, **C-6**, es un control que no
  vigila la rama que dice vigilar.

El ciclo **NO se cierra** con el check 12 como esta: T-1, T-2 y T-4 son
agujeros de un guard que declara la salud del paso de publicacion del motor, y
un guard que se puede apagar en silencio y certificar como operativo un
ejemplo dentro de una valla es un verde que no es.
