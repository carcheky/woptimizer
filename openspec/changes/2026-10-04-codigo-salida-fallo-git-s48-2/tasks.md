# Tareas — `2026-10-04-codigo-salida-fallo-git-s48-2`

**Tarea:** `TASK-061` · **Superviviente que cierra:** S48-2 (`openspec/changes/2026-10-02-sanear-deuda-status/mutation-report.md:69-79`)
**Decision de diseno:** D1 en `proposal.md:97-101` — **honrar `GIT_WORK_TREE` con paridad exigida**.
**Cero cambios en `src/woptimizer/**`.** Los ids `T-1`..`T-5` son **locales de este change**: no
valen como ancla de commit (`docs/ai/sandbox-rules.md:137-141`).

Orden obligatorio: **T-1 antes que T-3 y T-4**. Sin T-1, T-3 y T-4 escriben en el arbol de trabajo
real, que es exactamente lo que este change viene a cerrar.

---

## T-1 — `get_env()` honra `GIT_WORK_TREE` y exige paridad · `.taskmaster/git_safe_commit.py`

**Que:** `get_env()` (`:121-133`) pasa a derivar las dos variables del entorno con la misma
precedencia que ya tiene `GIT_DIR` (`:131`), y marca la asimetria; `validar_repo()` (`:159-192`)
exige ademas que el arbol efectivo sea un directorio; `main()` anade la puerta de paridad **despues
de `validar_repo`** (y por tanto tambien en `--verify`), con `WOPT_USAGE paridad-git` y codigo **2**.

**Criterio discriminante:** la puerta de paridad **falla hoy, sin mutacion ninguna** — con el
codigo actual, `GIT_DIR` temporal **sin** `GIT_WORK_TREE` stagea y commitea el **arbol real** dentro
del repo temporal y sale con `0`; el test de T-4 exige `2` y no-contaminacion a la vez. Ademas, un
mutante que quite la precedencia del entorno (vuelve a imponer `GIT_WORK_TREE = REPO_ROOT`
incondicional) rompe la asercion 3 de T-2, que afirma que la asignacion **no** es incondicional.

**Criterios:**
- El camino normal (sin `GIT_DIR` en el entorno) queda **byte a byte igual**: `GIT_DIR` =
  `%LOCALAPPDATA%\woptimizer_git\.git` y `GIT_WORK_TREE` = `REPO_ROOT`. Medido, no supuesto.
- Paridad: llega `GIT_DIR` **o** `GIT_WORK_TREE`, nunca las dos -> `2`, `WOPT_USAGE paridad-git`,
  **cero escrituras**, y la linea `WOPT_*` va la ultima (regla 4), en **ASCII puro** (regla 8).
- Arbol efectivo que no es un directorio -> `3`, no un `rc` de git sin interpretar.
- El docstring de `get_env()` y el de `validar_repo()` dicen la regla nueva: la hermeticidad del
  hook es **de repo y de arbol**, no solo de repo. Es la frase que `docs/ai/sandbox-rules.md:81-88`
  hoy declara a medias.

---

## T-2 — `test_el_contrato_de_codigos_esta_atado_a_cada_linea_wopt` · `run_tests.py` (`ast`)

**Que:** sobre el wrapper **real** importado (no copiado), derivar con `ast` la tabla
`(marcador WOPT_*, CODE_*)` de los 13 sitios de salida y exigir la tabla de `proposal.md:214-222`
—incluida la **sobrecarga deliberada del `0`** (`WOPT_COMMIT_OK` y `WOPT_NOOP`) y los **seis**
sitios de `WOPT_FAIL`. Ademas: ningun `sys.exit` de `main()` sin marcador canonico, y los valores
de las constantes son 0/1/2/3.

**Criterio discriminante:** el mutante S48-2 cambia el `CODE_*` de la misma sentencia que la tabla
deriva del fuente, luego la tabla y el contrato discrepan y la asercion salta en
`git_safe_commit.py:409-410`. Mata la **familia entera** (los 6 `WOPT_FAIL`) y no un caso: un
mutante que anada un `print` de mentiras para parecer honesto tambien muere, porque la asercion
"todo `exit` tiene marcador" no encuentra su fila.

**Criterios:**
- Sin subproceso, sin escritura, sin ventana. Es la razon de usar `ast` (el mismo patron ya
  establecido en `run_tests.py:16469-16474`).
- La tabla se deriva del **fichero real**, nunca de una copia del contrato: si las dos Copies
  existen y nadie las contrasta, son dos verdades.
- Asercion propia de `get_env()`: la asignacion de `GIT_WORK_TREE` **no** es incondicional.

---

## T-3 — `test_un_fallo_de_git_no_sale_con_cero` · `run_tests.py` (extremo a extremo)

**Que:** con `GIT_DIR` y `GIT_WORK_TREE` **temporales** (arbol sucio con un fichero), identidad
configurada en el repo temporal reutilizando `_git_de_fixture` (patron de `run_tests.py:16612-16620`)
y un `pre-commit` que sale con 1 (mecanismo **ya medido**, `docs/ai/sandbox-rules.md:120-121`;
alternativa si el bit de ejecucion molesta en Windows: `core.hooksPath` a un temporal con el mismo
hook), exigir `returncode == 1`.

**Criterio discriminante:** es el **unico** test que prueba el *runtime*, que es lo que lee la
victima. Con el mutante `CODE_FAIL -> CODE_OK` sale `0` y la asercion `== 1` salta; con T-1
revertido, el test escribe en el arbol del dueno y salta el testigo de no-contaminacion. Son dos
guardianes en un test y por eso no es tautologico.

**Criterios:**
- `"WOPT_FAIL commit"` en stdout, `"WOPT_COMMIT_OK" not in stdout` (un fallo **nunca** reporta
  commit creado), y la linea `WOPT_*` es la **ultima** impresa (regla 4).
- **Testigo de no contaminacion**: `HEAD` del repo real identico antes y despues, y ningun fichero
  con el prefijo unico de la sonda en la raiz real. Se compara **por contenido y con prefijo
  unico**, no con una igualdad de `git status`: hay otro actor commiteando en este arbol
  (`docs/ai/sandbox-rules.md:223`) y una igualdad estricta fallaria sola.
- El mensaje usa el ancla **`ciclo 999`**, no `TASK-061`: la convencion de ciclo no depende de
  `.taskmaster/tasks.json`, luego el test no se rompe al cerrar la tarea. Ejercita ademas una de las
  dos convenciones que no dependen de ficheros.

---

## T-4 — `test_el_cero_esta_sobrecargado_por_dos_desenlaces_y_solo_por_esos_dos` · `run_tests.py`

**Que:** tres filas de tabla sobre un repo y un arbol temporales:
1. **NOOP**: arbol limpio + mensaje anclado -> `0`, `WOPT_NOOP` presente y **cero hashes** en stdout.
2. **COMMIT_OK**: arbol sucio -> `0` y `WOPT_COMMIT_OK <hash>` cuyo hash **resuelve** en ese repo
   (`git cat-file --batch-check`), no un hash con forma de hash.
3. **Paridad**: `GIT_DIR` temporal **sin** `GIT_WORK_TREE` -> `2`, `WOPT_USAGE paridad-git` y
   **cero** escrituras en el arbol real.

**Criterio discriminante:** la fila 3 **falla hoy sin mutar nada** (hoy sale `0` y commitea el arbol
real). Las filas 1 y 2 matan, respectivamente, al mutante que imprime un hash en el no-op —la forma
exacta de "hashes que no existen", que es el dano del ciclo #11— y al mutante que inventa el hash sin
resolverlo. Sin las tres, el `0` sigue siendo un numero ambiguo sin nadie que lo distinga.

**Criterios:**
- La asercion del no-op es **negativa y tipada**: tras la linea `WOPT_NOOP` no aparece ningun
  `[0-9a-f]{7,40}`. "No hay hash" tiene que ser una afirmacion, no una lectura optimista.
- El hash del commit se **resuelve** en el repo del test. Un hash con la forma correcta y sin objeto
  es la misma clase de mentira que un hash inventado.

---

## T-5 — Los dos tests de TASK-061 dejan de escribir en el arbol del dueno (mismo cambio, mismo `--`)

**Que:** con T-1, `run_tests.py:16419-16420` y `:16640-16641` ya no necesitan el fichero testigo
`_t059_testigo_stageado.txt` **en la raiz real**: basta un arbol temporal sucio. Se conservan
**intactas** sus aserciones (rechazo con `2`, `INFO` antes de la `WOPT_*`, `WOPT_*` ultima,
`staged() == []`).

**Criterio discriminante:** no es un guardian, es la **medida del beneficio** de D1 — la prueba de
que la hermeticidad del arbol es real y no nominal. Si alguien revierte T-1 y no puede poner
`GIT_WORK_TREE` a un temporal, estos dos tests vuelven a necesitar el testigo y el fallo se ve.

**Criterio:**
- Los dos tests siguen midiendo lo mismo: un arbol **sucio** (el untracked temporal lo sigue siendo)
  y el indice intacto tras el rechazo.
- El `finally` que borra el testigo se conserva o se sustituye por el `shutil.rmtree` del temporal,
  pero **no se borra a mano nada**: un resto de test en el arbol del dueno lo recoge el proximo
  `add -A` del producto.

---

## T-6 — Contadores, documentacion y cierre (el repo se pone rojo sin esto)

**Que:** el recuento pasa de **136 a 139** y el reparto de **107 backend + 29 headless** a
**107 backend + 32 headless** (cifras medidas el 2026-10-04 con `validate_docs.py` en verde; **no**
usar las del encargo, que dicen 103/93+10 y caducaron). Los cuatro declarantes que mira
`validate_docs.py` —`STATUS.md`
(`:116`, total **y** reparto), `AGENTS.md` (`:117`), `README.md` (`:118`) y la tabla de
`docs/ai/testing-guide.md` (`:148-158`, **una fila por test**)— mas `docs/index.md`, que **no lo
vigila** nadie (S48-3 / `TASK-060`) y se actualiza por uniformidad. Los tres tests nuevos van en la
seccion headless, **detras** del marcador `MARCADOR_HEADLESS` (que hoy esta en
`run_tests.py:17956`), y se **definen e invocan** a la vez, que es lo que el check 7 deriva con `ast`.

Ademas: reescribir la **regla 7** de `docs/ai/sandbox-rules.md` con la paridad, actualizar la
seccion «Cobertura» (hoy dice que el codigo `1` no lo comprueba nadie, y eso deja de ser cierto al
cerrar este change) y cerrar la fila `STATUS.md:89` con su ancla. Changelogs en **los dos**
ficheros (`CHANGELOG.md` y `.taskmaster/CHANGELOG.md`).

**Criterio discriminante:** `validate_docs.py` en `0 FAIL` **con el mutante puesto**, no despues: es
el segundo semi-veredicto del toolchain y ya se midio que pasa por el mismo agujero que la suite.

---

## Lo que NO se hace (y por que)

- **No se reescribe el criterio de TASK-022** en `.taskmaster/tasks.json:322` ("`GIT_WORK_TREE`
  siempre = `REPO_ROOT`"): describe el contrato vigente hasta hoy y **se supera**, no se falsifica.
- **No se corrigen los numeros de linea en los changelogs** (`.taskmaster/CHANGELOG.md:49, :376,
  :438`) ni en `mutation-report.md:73`: son el registro de lo que se creia el 2026-10-02, y la
  doctrina del repo es conservarlos como evidencia (`mutation-report.md:115-116`). La correccion
  vive en la regla 7 y en el panel.
- **No se anade ningun codigo de salida.** El contrato sigue siendo 0/1/2/3; la paridad extiende la
  fila "cuando" del `2`, igual que hizo TASK-059 con la puerta del mensaje.
- **No hay cerrojo entre dos actores que commitean a la vez** (`docs/ai/sandbox-rules.md:231-233`):
  sigue declarado y sin dueño. No se arregla aqui porque bloquearía al bucle si el proceso muriera
  con el cerrojo tomado.
- **Cero `src/`.**

---

## Verificacion (comandos y salida esperada, no "se verificó")

```text
python run_tests.py            -> "ALL TESTS PASSED."  y exit 0, con 136 -> 139 tests
python validate_docs.py        -> exit 0 y "0 FAIL" (hoy "Resumen: 124 OK, 0 FAIL")
python verify_ui_syntax.py     -> exit 0 (sin cambios en src/: es el control de que no toco producto)
python .taskmaster/git_safe_commit.py --verify  -> "WOPT_REPO_OK ..." y exit 0
```

**Y el guard que de verdad importa (Paso 4, `mutation-auditor`):** con el mutante
`WOPT_FAIL commit` -> `CODE_OK` puesto **por contenido, nunca por linea**
(`proposal.md:281-295`), `run_tests.py` tiene que **morir**. Si pasa, la tarea no se cierra.
