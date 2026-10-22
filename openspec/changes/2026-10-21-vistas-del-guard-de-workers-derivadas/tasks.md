# Tareas — TASK-082 · el conjunto de vistas del guard de workers se deriva

**Ciclo 68** · rama `beta` · **cero ediciones bajo `src/woptimizer/`**.
Contrato completo en `proposal.md` (§7 = criterios de aceptación).

---

## Orden de ejecución

| # | Tarea | Fichero | Estado |
|---|---|---|---|
| 1 | Hoist de `_vistas_del_disco` a ámbito de módulo, con el directorio **derivado** de la ubicación del módulo | `run_tests.py` | ☐ |
| 2 | `VISTAS_INVENTARIADAS` deja de ser la fuente: el guard abre el **derivado** y la literal queda como **declaración comparada** | `run_tests.py` | ☐ |
| 3 | `_arbol_de` deja de llevar el directorio de vistas escrito a mano | `run_tests.py` | ☐ |
| 4 | `RUTAS_VIGILADAS` se queda solo con `confirmation.py` (las 3 entradas de vista son redundantes: el default del `.get()` ya las aporta) y `ESPERADOS` deja de ser una tercera copia | `run_tests.py` | ☐ |
| 5 | Guard de forma (AC-1): una sola fuente de verdad; el helper **no** puede estar anidado | `run_tests.py` | ☐ |
| 6 | Test de producto (AC-2): vista nueva en `%TEMP%` → ROJO nombrando la infracción; control positivo → VERDE | `run_tests.py` | ☐ |
| 7 | Contraprueba del detector (AC-3): el derivado es el disco y abre ≥1 fichero; derivado vacío → ROJO | `run_tests.py` | ☐ |
| 8 | Cierre (AC-4): suite verde, `verify_ui_syntax.py` verde, `validate_docs.py` 0 FAIL, `git status --porcelain` vacío, commit `(TASK-082)` en `beta` | repo | ☐ |
| 9 | Recuento de citas por número de línea movidas, en el informe de mutación | `mutation-report.md` | ☐ |

> El conjunto de vistas está escrito **cuatro veces**: `VISTAS` (`:27617`), las claves de
> `RUTAS_VIGILADAS` (`:27622`), `ESPERADOS` (`:27631`) y `VISTAS_INVENTARIADAS` (`:9410`, en
> el **otro** guard). **Solo una** de las cuatro está atada al disco.

---

## Detalle de cada una

### 1 · Hoist de la derivación

`_vistas_del_disco` vive **anidada** en `test_ninguna_vista_programa_after_a_mano`
(`run_tests.py:27652`), con sangría de 4 espacios. **Por eso no se puede reutilizar** y el
segundo guard escribe el conjunto a mano.

- Subirla a **ámbito de módulo**, con docstring propio.
- El directorio de vistas sale de la **ubicación del módulo** (`Path(__file__)`), no de
  `os.path.join(raiz_repo, "src", "woptimizer", "ui", "views")` escrito a mano (que hoy
  aparece duplicado en `run_tests.py:9311` y `:27676`).
- `__init__.py` fuera, **a propósito**: no es una vista (misma regla que hoy).

### 2 · La literal pasa a ser declaración

En `test_los_workers_de_pack_solo_publican_por_after` (`run_tests.py:9410`):

- `vistas_en_disco = _vistas_del_disco(...)` → **derivado**.
- `assert set(VISTAS_INVENTARIADAS) == vistas_en_disco` → **rojo que nombra la
  diferencia** (una vista nueva, o una vista que se ha ido).
- el `for` abre **`vistas_en_disco`**, no la literal.
- La cifra `== 10` (`:9416`) **se queda**: es un tripwire deliberado, no un alcance.

> ⚠️ **No** sustituir la literal por el derivado y ya: eso perdería el aviso. Se quiere
> **el rojo que nombra** la vista nueva **Y** que la vista nueva se audite.

### 3 · `_arbol_de`

Hoy abre `os.path.join(raiz_repo, "src", "woptimizer", "ui", "views", nombre)`
(`run_tests.py:9311`). Que reciba la ruta ya resuelta por el caller derivado.

### 4 · AC-1 · guard de forma

Con `ast`, sobre `run_tests.py`:

- el conjunto que el guard de workers abre **no puede** ser una enumeración literal
  escrita dentro del propio guard;
- el helper que lo deriva **no puede** estar anidado dentro de una función (si lo está, es
  inaccesible para el otro guard y la copia a mano vuelve);
- una sola fuente de verdad para el conjunto de vistas.

Cada hallazgo se nombra con **fichero y línea**. **SIN lista muda de permitidos**: si hace
falta tolerar algo, va en el docstring del infractor con (a) por qué existe y (b) qué la
retira — la misma regla que AC-5 de TASK-081.

### 5 · AC-2 · producto

En `%TEMP%`: `src/woptimizer/` real + una vista **nueva** cuyo worker toca la vista fuera
de la puerta + la lista de vistas actualizada (como haría el dev) → **ROJO** nombrando la
infracción. **Control positivo**: la misma vista sin tocar la puerta → **VERDE**.

Es el AC que no puede sobrevivir sin el fix. Sin el control positivo, un guard que siempre
da ROJO cumpliría el AC.

### 6 · AC-3 · contraprueba del detector

1. El derivado devuelve **exactamente** los `.py` de `src/woptimizer/ui/views/` menos
   `__init__.py`, y **eso** es lo que el guard abre. Un derivado **vacío** → ROJO.
2. El conjunto abierto y el derivado **coinciden** con la declaración.

### 7 · AC-4 · cierre

```powershell
python run_tests.py            # ALL TESTS PASSED.  exit 0
python verify_ui_syntax.py    # exit 0, ALCANCE_DERIVADO=22
python validate_docs.py       # 0 FAIL
python .taskmaster/git_safe_commit.py "fix(tools): el conjunto de vistas del guard de workers se deriva (TASK-082)"
```

Rama `beta`. **Nunca `main`.** `git status --porcelain` vacío antes de comitear.

### 8 · Recuento de citas movidas

Las citas de `run_tests.py` que usa la propuesta (`:9410`, `:27617`, `:27652`, `:27683`,
`:27715`) **se mueven** al insertar líneas por encima. Medir y **actualizar** las que
sigan vivas, o sustituirlas por derivación. Es el residuo `P2` de `STATUS.md`.

---

## Mutantes declarados

| id | Qué rompe | Veredicto esperado |
|---|---|---|
| **M-V1** | la literal vuelve a ser la fuente | **MUERTO** (AC-1 y AC-2) |
| **M-V2** | vista nueva en disco, literal sin actualizar | **EQUIVALENTE** — rojo por construcción (ruido). Su supervivencia **no** es un fallo |
| **M-V3** | la derivación devuelve una lista vacía o fija | **MUERTO** (AC-3). Si nadie lo mata, el guard vuelve a ser vaciable |
| **M-V4** | el helper no se hoista y la copia a mano vuelve | **MUERTO** (AC-1) |

---

## Fuera de alcance (y por qué)

* `src/woptimizer/**` — invariante del repo.
* El alcance de AC-5 (`run_tests.py:28993`) — **#2** del ranking, agujero **latente**: su
  propio ciclo.
* `_copiar_el_esqueleto_del_validador` (`run_tests.py:13209`) — MEDIDO: todas las celdas
  dan ROJO con fichero y línea → bomba de mantenimiento, no agujero.
* Ampliar la llave del detector AC-5 a basenames — MEDIDO (E3): AC-1 y AC-3 **ya** cazan
  esa forma → es ruido.
* `TASK-080` y `TASK-068` — bloqueadas, no se tocan.
* `STATUS.md` — lo cierra el orquestador: está citado por número de línea en **9 sitios de
  código vivo** y ~19 más en changelogs y journal.

---

# PARTE 2 — reparación tras el FAIL de auditoría (ciclo 68, segunda vuelta)

El fix de TASK-082 está **PASS** (sus 7 mutantes M-V1, M-V3, M-V3b, M-V4, M-V5, M-V6 y
M-V7 mueren todos por su aserción). Lo que el `mutation-auditor` midió y **no** pasa
es la **vigilancia de la vigilancia**: tres mutaciones sobreviven a la suite
completa porque el guard que las vigila se puede vaciar.

## Los tres supervivientes (medidos por el auditor)

| id | Superviviente | Por qué sobrevivía |
|---|---|---|
| **Q1** | Las tres sondas (AC-1, AC-2, AC-3) son funciones `_`-prefijadas que solo se invocan desde `__main__` | `validate_docs.py` solo cuenta `test_*` → borrarlas no baja ningún recuento ni rompe nada (`231 = 231`, validador `156 OK / 0 FAIL`, suite completa `rc=0`) |
| **Q2** | AC-1 deja de mirar el guard hermano | suite **verde** |
| **Q2b** | AC-1 no mira **ningún** guard (`for nombre_guard in ():`) | suite **verde**, log **idéntico** al baseline |

Causa raíz de Q2/Q2b: el conjunto de sujetos de AC-1 era la enumeración literal
`(_GUARD_DE_WORKERS, _GUARD_HERMANO)`. Es **la misma clase** que el guard que este
ciclo cierra: un guard cuyo conjunto de sujetos está escrito a mano y es un dato
derivado.

## Las 6 reparaciones

| id | Qué se repara | Dónde | Estado | Por qué |
|---|---|---|---|---|
| **R1** (A-C68-1 / Q1) | Las tres sondas dejan de ser `_`-prefijadas y pasan a ser `test_*` de módulo, invocadas desde el bloque de tests del `__main__` | `run_tests.py` (las tres `def` y sus tres invocaciones) | **HECHO** | `validate_docs.py` las cuenta: si desaparecen, `defined != invoked` y el validador da FAIL. El recuento sube de 231 a **234** y el reparto DERIVADO con `ast` pasa a **158 backend + 76 headless** (las tres sondas van ANTES del marcador headless: no abren ventana). Las cuatro declaraciones (AGENTS.md, README.md, STATUS.md, tabla de `docs/ai/testing-guide.md`) se actualizan a la cifra medida |
| **R2** (A-C68-2 / Q2+Q2b) | AC-1 pasa a ser una **regla de MÓDULO**: el detector recorre TODO `run_tests.py` con `ast` y aplica la regla a **todas** las funciones. La DECLARACIÓN y la función que deriva se **DERIVAN** (`_declaracion_y_derivador`): la declaración es la enumeración **comparada con el derivado**; el derivador es la función de módulo a la que llega esa comparación. Ninguna enumeración de nombres de guards queda en el detector | `run_tests.py`: `_declaracion_y_derivador`, `_fors_del_modulo`, `_delitos_de_fuente_escrita_a_mano`, `_delitos_de_forma_del_conjunto_de_vistas` | **HECHO** | Con la lista de guards, el detector se puede vaciar mirando dos guards (Q2) o ninguno (Q2b). Contraprueba obligatoria añadida: una enumeración literal escrita a mano en una función **que no está en ninguna lista** tiene que ser **denunciada con fichero y línea** |
| **R3** (A-C68-3 / M-V5) | Dos saltos: (1) AC-1 comprueba que el cuerpo del helper que deriva **no referencia ninguna enumeración** (su `return` sale del disco, no de la declaración); (2) AC-2 gana un **segundo escenario**: vista **nueva en disco y NO declarada** → el guard tiene que dar ROJO **que nombre la vista nueva** | `run_tests.py`: `_delitos_del_helper_que_no_deriva` + la celda (3) de `test_una_vista_nueva_se_audita_aunque_nadie_la_apunte` | **HECHO** | Con M-V5 la comparación es tautológica: el rojo que nombra la vista nueva desaparece y la vista nueva deja de auditarse. Antes solo AC-3 lo cazaba, y **por efecto colateral** (un `FileNotFoundError` en una cámara vaciada) — que es la clase que el ciclo 67 declaró como deuda **S7**. Ahora **M-V5 muere por AC-1 y por AC-2**, no por efecto colateral. El carácter EQUIVALENTE de M-V2 se conserva: con el código sano, ese escenario da el rojo de la COMPARACIÓN (el aviso esperado), y lo que tiene que morir es el mutante |
| **R4** (A-C68-4) | El docstring de AC-1 se reescribe para que describa lo que **realmente** vigila, y dice explícitamente lo que **NO** comprueba (que el helper lea el disco de verdad: eso es AC-3) | `run_tests.py`: docstring de `test_el_conjunto_de_vistas_tiene_una_sola_fuente_de_verdad` | **HECHO** | El patrón que STATUS.md ya declaraba como deuda **S7** (CYCLE-067): "su propia documentación miente". El docstring anterior decía "recorre el DERIVADO" y M-V5 demostraba que se podía recorrer la DECLARACIÓN |
| **R5** (A-C68-5) | Las seis citas por número de línea que **no sostenían** su afirmación, corregidas **in-place** (sin añadir ni quitar líneas) | `run_tests.py` (la docstring de los tests #4/#6/#7 y la del guard de `sandbox-rules.md`), `validate_docs.py` (las dos) | **HECHO** | Ver la tabla de la sección siguiente |
| **R6** (A-C68-6) | El mensaje del tripwire **no lleva la cifra a mano**: la cifra comparada y la del mensaje salen de la MISMA constante (`_CIFRA_DE_PUBLICACIONES_VIGILADAS`), y el mensaje dice **qué cifra se comparó** | `run_tests.py`: la constante, el `assert` del guard de workers y el parche de la cámara | **HECHO** | El mensaje decía «10 publicaciones … habla de 10 call sites» y no decía **qué** cifra se comparó: se contradecía en cuanto una de las dos se movía. La cifra sigue siendo un **tripwire deliberado** (escrita a mano, no derivada) |

### R5 · Las seis citas corregidas (todas medidas con `ast`, no a ojo)

| Cita | Antes | Después | Por qué la de antes no sostenía su afirmación |
|---|---|---|---|
| `run_tests.py` (docstring de los tests #4/#6/#7) | `:14787`, `:14893`, `:14920` | `:15766` y `:15793` (del #4), `:15886` (del #6), `:15932` (del #7) | `:14787` decía `# --- (A) LA CAUSA …`, `:14893` estaba **en blanco** y `:14920` era `def cget(self, key):`. Los sitios REALES de la sobrescritura de `_patrones_de_categoria` (medidos con `ast`, `Assign` sobre `Attribute`) son esos cuatro |
| `run_tests.py` (docstring del guard de `sandbox-rules.md`) | `:23102` | `:23133` | `:23102` no citaba nada: el que cita `sandbox-rules.md:55-56` es `:23133` |
| `run_tests.py` (docstring del mismo guard) | `:23125` | `:23131` | `:23125` era `cabecera = "Por que el validador NO corre en CI"`; el suelo `assert min(posiciones) > 61` está en `:23131` |
| `validate_docs.py:1180` | `run_tests.py:13553` | `run_tests.py:14013` | `:13553` era `shutil.rmtree(tmp, ignore_errors=True)`: la **2ª** ocurrencia de `"--- Running Headless UI Tests ---"` está en `:14013` |
| `validate_docs.py:1435` | `run_tests.py:11650` | `run_tests.py:28734` | `:11650` decía `import threading`: el guard de código muerto que mira `src/woptimizer/**` es `test_la_verificacion_de_sintaxis_deriva_su_alcance_y_no_lo_enumera`, en `:28734` |

Además, el guard `test_las_citas_de_sandbox_rules_siguen_siendo_ciertas` **lee en
caliente** su propia línea (`run_tests.py:23133`) y la lista de `validate_docs.py`
(`:1429` y `:1924`): las cuatro se recalcularon al final, porque los cambios de
este ciclo las desplazan.

## Una enumeración que hay que justificar (y por qué se justifica)

`run_tests.py:6160` (el test `test_orden_de_categorias_no_es_alfabetico`) recorre
una enumeración de **dos** nombres de vista escritos a mano: las dos vistas que
**manejan categorías**. No es derivable del sistema de ficheros (la tercera vista
no tiene catálogo que ordenar), así que es una SELECCIÓN con razón semántica, y
la regla de módulo lo tolera con la **justificación escrita** en su docstring
—(a) por qué existe y (b) qué la retira— que es el mecanismo de AC-5 de TASK-081,
**no** una lista muda de permitidos.

## Lo que NO se ha tocado

* `src/woptimizer/**` — invariante duro del repo (cero ediciones).
* `mutation-report.md` — lo escribe el auditor en la re-auditoría.
* `.taskmaster/rd_journal.json`, `CHANGELOG.md` y `.taskmaster/CHANGELOG.md` — los
  escribe el orquestador.
* `docs/ai/sandbox-rules.md`, `docs/ai/architecture.md`, `docs/ai/data-models.md` y
  `docs/ai/ui-design-system.md` — fuera de alcance.

# PARTE 3 — cierre del ciclo 68 (tercera vuelta)

La re-auditoría (`mutation-report.md`, **PARTE 2**) confirmó que el **fix** de
TASK-082 es PASS (sus 7 mutantes mueren por su aserción) y que las tres
**vigilancias** ya mueren (Q1 por la suite, Q2 y Q2b por la contraprueba de R2),
pero dejó el **veredicto global en FAIL** por cuatro cosas. Esta parte las
cierra tres y declara la cuarta con nombre.

| id | Qué se repara | Dónde | Estado | Por qué |
|---|---|---|---|---|
| **R7** (A-C68-7) | El `NameError` latente: el parámetro se llama `expresion` y el código usaba `expression` | `run_tests.py:29363` (`_funcion_de_modulo_a_la_que_llega`) | **HECHO** | Con el nombre mal, la función reventaba **por excepción** —no por su aserción— en cuanto una `ast.Call` tenía argumentos con nombre. Por eso M-V1 y M-V4 morían "por la puerta de atrás": el mutante no probaba el fix, probaba el crash. Ahora **M-V1 y M-V4 en su forma ORIGINAL mueren por su propia aserción** |
| **R8** (A-C68-8 / S1) | El recorrido de AC-1 baja a **todos** los bucles anidados (`for` y `while`, a cualquier profundidad), de forma **explícita** | `run_tests.py:29278` (`_fors_del_modulo`, docstring y `_bajar`) | **HECHO** | Un recorrido que se queda en el bucle exterior deja pasar una enumeración escrita a mano metida dentro, y la suite completa queda en **VERDE** sin que nadie lo note (mutante S1). Se baja explícitamente al cuerpo y al `orelse`, y se baja en cada nivel |
| **R9** (A-C68-9 / S2) | La tolerancia escrita es **POR ENUMERACIÓN**, no por función: cada enumeración necesita **su** justificación, y una justificación no puede tapar dos | `run_tests.py:29518` (`_bloques_de_justificacion`), `:29540` (`_nombres_de_vista_en_una_frase`), `:29545` (`_enumeracion_justificada`), `:29580` (`_delitos_de_fuente_escrita_a_mano`) | **HECHO** | Con la tolerancia por función, **una** justificación tapaba **dos** enumeraciones de la misma función (mutante S2) y cualquier función se podía aseptar copiando los dos marcadores en su docstring. Ahora la justificación tiene que **nombrar** la enumeración que tolera (los nombres de sus vistas, y solo esa) |
| **R4 bis** (A-C68-10) | El docstring de AC-1 dice lo que el guard **NO** vigila, con la medición que lo acota | `run_tests.py:29682` (docstring de AC-1) y `:29637` (docstring de `_delitos_de_forma_del_conjunto_de_vistas`) | **HECHO** | Mismo criterio que R4 (A-C68-4): un docstring que miente es deuda. El guard no puede afirmar más de lo que vigila |

## R7 · el `NameError` latente, y cómo se ha comprobado que no queda ninguno

La entrega anterior (`73b2393`) añadió `_funcion_de_modulo_a_la_que_llega` con
una línea que usaba un identificador **que no existía** (`expression` en vez de
`expresion`). Era un `NameError` **latente**: solo reventaba cuando la
expresión era una `ast.Call` **con argumentos con nombre**.

Cómo se ha comprobado que no queda **ningún** identificador sin definir (el
método, no la afirmación):

1. Se escribió un comprobador de ámbitos (`ast`): cada ámbito —módulo,
   función, clase, `lambda` y *comprehension*— tiene sus enlaces, y un nombre
   cargado se resuelve por la cadena local → cierre → módulo → `builtins`
   (las clases no cierran sobre su ámbito, que es la regla de Python). Sin esa
   regla, el comprobador da **541 falsos positivos** (una función anidada ve
   los nombres de la que la contiene).
2. Se comparó el fichero **actual** con el de `HEAD` (`73b2393`).
3. Resultado medido: **`HEAD` → 1 nombre sin definir** (`expression`, uso en
   `:29351`) y **actual → 0**. Los **nuevos** (los que no estaban en HEAD):
   **0**.

## R8 · el recorrido baja a los bucles anidados

El recorrido `_bajar` de `_fors_del_modulo` baja ahora **de forma explícita**
al cuerpo y al `orelse` de los bucles (`for` y `while`), y sigue bajando en
cada nivel. No es un efecto colateral del recorrido genérico: está escrito, y
el docstring lo afirma.

La contraprueba que lo ata (celda nueva dentro de AC-1,
`run_tests.py:29893`): una enumeración escrita a mano metida en un `for`
dentro de un `for` dentro de un `while` tiene que ser **denunciada con
fichero y línea**. Sin esa celda, R8 sería una declaración y no un cierre: el
mutante S1 (el recorrido que no baja al `for` anidado) **sobrevive a la suite
completa** —que es exactamente lo que midió la re-auditoría.

## R9 · la tolerancia es por enumeración

El mecanismo **sigue siendo el del ciclo 67**: la justificación es **prosa** en
el docstring del infractor, con (a) por qué existe y (b) qué la retira. No hay
lista muda de permitidos. Lo que cambia es **a qué** se aplica:

- Antes: la justificación del docstring de la función toleraba **todas** las
  enumeraciones de esa función.
- Ahora: la justificación tiene que **nombrar** la enumeración que tolera (los
  nombres de sus vistas), y **solo tolera esa**. El nombre tiene que ser
  **exacto**: una justificación que nombra de más no tolera nada, que es lo que
  impide que una justificación pueda tapar dos enumeraciones.

Las dos frases van en **una línea** cada una y con 30 caracteres o más (la
misma regla del mecanismo de TASK-081).

Las contrapruebas que lo atan (celdas nuevas dentro de AC-1,
`run_tests.py:29923` y `:29955`):

- Una función con **una** justificación y **dos** enumeraciones → la segunda
  tiene que salir en rojo. (Con la tolerancia por función, no salía.)
- **Control positivo**: una justificación que **nombra** su enumeración la
  tolera. Sin esta celda, "una justificación no tapa dos" se cumpliría con
  "una justificación no tapa ninguna" y el guard no toleraría nada.

La enumeración justificada que ya existía en el repo
(`run_tests.py:6118-6122`, el test de orden de categorías) **se ha tenido que
nombrar**: su frase (a) ahora dice cuáles son las dos vistas. Sin nombrarlas,
la enumeración queda sin justificar y el guard la delata —que es lo que tiene
que pasar.

## La deuda con nombre: S3 (A-C68-10) — hueco de la HEURÍSTICA, no del guard

**No se arregla en este ciclo, y la razón está medida.** S3 es una enumeración
escrita a mano escondida **detrás de una llamada** (`for n in _mis_vistas()`):
la regla de forma solo mira el iterable del `for` cuando es un contenedor de
literales o un nombre enlazado a él, y una llamada no tiene nada que mirar.

Lo que lo acota, medido:

- **S3 sobrevive como mutante del detector**: la suite completa queda en verde.
- **S4 demuestra que el guard real lo caza**: con ese patrón aplicado al guard
  de verdad, el conjunto **completo** lo caza la regla 3 y un subconjunto lo
  caza la comparación tautológica de los dos guards. Es decir: el hueco es de
  la **heurística** del detector, no un verde falso del guard.

Riesgo real bajo (escribir un conjunto de rutas a mano detrás de un `list(...)`
no es una forma en que un dev escriba eso) y el arreglo **degradaría** el
detector (aceptar literales en cualquier expresión → más falsos positivos).
Queda como deuda **S3 (A-C68-10)**, con nombre, para su ciclo.

Lo que sí se ha hecho con ella: **documentarla** en el docstring de AC-1 y en
el de `_delitos_de_forma_del_conjunto_de_vistas`, para que el guard **no
afirme** más de lo que vigila.

## Dos deudas más que han salido al medir (declaradas, no arregladas)

**S8 — la tolerancia por función sigue viva en el guard de AC-5 (TASK-081).**
`_delitos_de_enumeracion` (`run_tests.py:28676`) calcula la justificación **una
vez por ámbito** y salta **todas** las enumeraciones de ese ámbito: es la
misma clase que S2. No se arregla aquí porque su enumeración justificada vive
bajo `src/woptimizer/**` y este ciclo tiene **cero ediciones** ahí. Queda
declarada.

**S9 — `test_el_pre_vuelo_de_un_hash_muerto_distingue_existe_de_no_existe` es
FLAKY por construcción, y su muerte no dice nada del sujeto.**
El test hace `hash_real = rev-parse --short HEAD` (7 hex) y comprueba que
`hash_real + "0"` (8 hex) **no** existe. Pero si el octavo dígito del sha
completo es "0", ese prefijo **sí** existe y el test revienta. **Medido:**
3/60 fixtures (5,0 %, teórico 1/16 = 6,25 %) tienen `short + "0"` como prefijo
del sha. Es decir: ~1 de cada 16 corridas de la suite puede morir ahí, en un
test que no va de TASK-082. En este ciclo lo pilló la cámara de **S3**:
S3 pasó las tres sondas de AC y murió en el pre-vuelo, así que **su muerte NO
era un veredicto** (S3 es un superviviente, como está documentado).

## Lo que NO se ha tocado

- **`src/woptimizer/**`: cero ediciones** (invariante duro).
- `mutation-report.md`, `.taskmaster/rd_journal.json`, `CHANGELOG.md`,
  `.taskmaster/CHANGELOG.md`, `STATUS.md`, `AGENTS.md`, `README.md`,
  `docs/ai/**`, `validate_docs.py`, `force_build.py`, `build.bat`,
  `docs/ai/sandbox-rules.md`.
- **Ninguna función `test_*` nueva**: el recuento sigue en **234** y las cuatro
  declaraciones del repo (AGENTS.md, README.md, STATUS.md y la tabla de
  `docs/ai/testing-guide.md`) siguen siendo ciertas. Las contrapruebas nuevas
  son **celdas** dentro de AC-1, que ya es un `test_*` del módulo.
- **Cero desplazamiento** de las dos líneas que el guard de citas lee en
  caliente (`run_tests.py:23133` y `validate_docs.py:1429`): comprobado en
  cada mutación, con el contenido de esas líneas comparado antes y después.

## La tabla de mutantes medidos (suite COMPLETA en cámara, 22 corridas)

Método: cámara desechable en `%TEMP%` (copia del repo **sin** `.git`, `git init
-beta` **propio**, un commit), `python run_tests.py` entero, y el veredicto sale
del log: `rc=0` + `ALL TESTS PASSED.` en la **última** línea = superviviente;
`AssertionError` con traza = muerto. **Cero desplazamiento** de `run_tests.py:23133`
y `validate_docs.py:1429` comprobado en cada mutación (contenido de esas dos
líneas comparado antes y después). `git_safe_commit.py` **no** se invocó ni una
vez desde la cámara.

| id | Qué rompe | Motivo **literal** de la muerte | Veredicto |
|---|---|---|---|
| **baseline** | — (control positivo) | `ALL TESTS PASSED.` (398 líneas, 30 641 B, rc=0) | **VERDE** |
| **M-V1** (forma ORIGINAL) | la DECLARACION vuelve a ser la fuente: `set(VISTAS_DECLARADAS)` | `AssertionError: una vista NUEVA en el disco y SIN declarar tiene que dar ROJO que la nombre y dio 0` (AC-2, `run_tests.py:30197`) | **MUERTO por su aserción** (antes moría por `NameError`) |
| **M-V4** (forma ORIGINAL) | el helper `_vistas_del_disco` deja de estar en ambito de modulo | `AssertionError: el conjunto de vistas que vigilan los guards NO esta derivado del disco: - run_tests.py:29166: `_vistas_del_disco` esta ANIDADO dentro de una funcion... - run_tests.py:0: no se puede derivar la DECLARACION...` (AC-1) | **MUERTO por su aserción** (antes moría por `NameError`) |
| **M-V3** | el derivado devuelve un conjunto vacio | `AssertionError: el rojo tiene que NOMBRAR la infraccion (y no un fallo cualquiera del subproceso)` (AC-2) | MUERTO |
| **M-V3b** | el helper devuelve la DECLARACION escrita a mano | `AssertionError: el conjunto de vistas que vigilan los guards NO esta derivado del disco: - run_tests.py:29182: una SEGUNDA copia del conjunto de vistas escrita a mano` (AC-1) | MUERTO |
| **M-V5** | el `return` del helper sale de la DECLARACION | `AssertionError: el conjunto de vistas que vigilan los guards NO esta derivado del disco: - run_tests.py:29164: `_vistas_del_disco` NO deriva del disco: usa `VISTAS_DECLARADAS`...` (AC-1) | MUERTO |
| **M-V6** | la raiz del repo esta escrita a mano | `AssertionError: el rojo tiene que NOMBRAR la infraccion...` (AC-2) | MUERTO |
| **M-V7** | el directorio de vistas esta escrito a mano | `AssertionError: el rojo tiene que NOMBRAR la infraccion...` (AC-2) | MUERTO |
| **Q5** | la cifra de publicaciones vigiladas se mueve | `AssertionError: el rojo tiene que NOMBRAR la infraccion (y no un fallo cualquiera del subproceso): salida='Testing that pack workers only publish via self.after (TASK-035 / cycle 26)...` (AC-2) | MUERTO |
| **Q1** | las tres sondas `test_*` dejan de invocarse | `AssertionError: un journal ILEGIBLE es un fallo del ancla y solo uno: el historial de la fixture no aporta ciclos y el changelog esta completo. Errors: ['.taskmaster/rd_journal.json: ESTA CORRUPTO...']` (`run_tests.py:13542`) | MUERTO |
| **Q2** | AC-1 deja de mirar el guard hermano | `AssertionError: el detector tiene que DENUNCIAR una enumeracion escrita a mano en una funcion que NO esta en ninguna lista, y nombrarla con FICHERO Y LINEA: si el detector vuelve a mirar un conjunto de guards escrito a mano (Q2)...` (AC-1, `run_tests.py:29881`) | MUERTO |
| **Q2b** | AC-1 no mira **ningún** guard | la misma asercion que Q2 (AC-1, `run_tests.py:29879`) | MUERTO |
| **S1** | el recorrido **no baja** al cuerpo de un `for` | `AssertionError: el detector tiene que DENUNCIAR una enumeracion escrita a mano metida en un bucle ANIDADO, y nombrarla con FICHERO Y LINEA: si el recorrido no baja a los bucles anidados, la enumeracion se cuela en silencio (S1) y este AC no mide nada` (AC-1, `run_tests.py:29924`) | **MUERTO por la celda nueva de R8** |
| **S1b** | el recorrido **no baja** al cuerpo de un `while` | `AssertionError: el conjunto de vistas que vigilan los guards NO esta derivado del disco: - run_tests.py:29193: `_guarda_anidada_de_la_camara` recorre una ENUMERACION literal...` (AC-1) | MUERTO |
| **S1c** | el control positivo de S1 (la enumeracion anidada, sin sabotaje) | `AssertionError: el conjunto de vistas que vigilan los guards NO esta derivado del disco: - run_tests.py:29193: `_guarda_anidada_de_la_camara` recorre una ENUMERACION literal...` (AC-1) | MUERTO |
| **S2** | **una** justificacion escrita tapa **dos** enumeraciones | `AssertionError: el conjunto de vistas que vigilan los guards NO esta derivado del disco: - run_tests.py:29194: `_guarda_con_justificacion` recorre una ENUMERACION literal... - run_tests.py:29197: ...` (AC-1) | **MUERTO** (con la tolerancia por funcion sobrevivía) |
| **S2d2** | la justificacion **nombra** la primera enumeracion: la segunda sigue sin justificacion | `AssertionError: el conjunto de vistas que vigilan los guards NO esta derivado del disco: - run_tests.py:29195: `_guarda_con_justificacion_nombrada` recorre una ENUMERACION literal (escrita a mano: ['dashboard_view.py', 'process_manager_view.py'])` (AC-1) | **MUERTO**: sale **solo** la segunda enumeración, que es exactamente la propiedad de R9 |
| **S2c** | la justificacion real pierde su frase (b) | `AssertionError: el conjunto de vistas que vigilan los guards NO esta derivado del disco:` (AC-1) | MUERTO |
| **S4** | el patron de S3 aplicado al **guard de verdad** | `AssertionError: el conjunto de vistas que vigilan los guards NO esta derivado del disco:` (AC-1) | MUERTO: el guard real **sí** lo caza |
| **S3** | la enumeracion escrita a mano detras de una **llamada** | `ALL TESTS PASSED.` (398 líneas, 30 641 B, rc=0) | **SUPERVIVIENTE por decision documentada** (deuda S3). Su log es **identico al baseline** salvo 17 lineas de ruido de tiempos/ids (latencia en ms y nombres con marca de tiempo) |
| **M-V2** | no es un mutante: es el **escenario** (vista nueva en disco, sin declarar) | con el codigo sano da el rojo de la COMPARACION, que es el comportamiento esperado; lo que tiene que morir es el mutante (M-V1, que muere en AC-2) | **EQUIVALENTE** (se conserva) |

**Nota sobre S3 en el lote 1:** la primera corrida de S3 murió en
`test_el_pre_vuelo_de_un_hash_muerto_distingue_existe_de_no_existe`, que **no
va de TASK-082**: es un test **flaky por construcción** (medido: 3/60 fixtures,
5,0 %, tienen `short + "0"` como prefijo del sha; teórico 1/16 = 6,25 %). La
segunda corrida de S3 dio `rc=0`. Esa muerte **no era un veredicto** y queda
declarada como deuda **S9**.
