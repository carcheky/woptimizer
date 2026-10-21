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
