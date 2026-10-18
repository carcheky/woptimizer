# Desacoplar la ruta del repositorio en `validate_docs.py` y hacer honesta su degradación

**Tarea:** TASK-075 · **Fecha:** 2026-10-18 · **Capa:** tooling de raíz (`validate_docs.py`)

---

## 1. Qué pide la tarea tal como está redactada, y qué mide

La entrada de `tasks.json` dice: *"`validate_docs.py` deriva el repositorio desacoplado
únicamente desde `%LOCALAPPDATA%\woptimizer_git\.git` (`validate_docs.py:300-302`),
impidiendo su ejecución en GitHub Actions CI. Debe aceptar una variable de entorno
`WOPTIMIZER_GIT_DIR` o argumento CLI `--git-dir`."*

La línea citada está corrida: la derivación está **duplicada** en dos sitios, y ninguno
es el 300-302:

| Sitio | Función | Código |
|---|---|---|
| `validate_docs.py:306-308` | `_comprobar_ancla_de_commits` (check 5b, la del historial) | `env["GIT_DIR"] = env.get("GIT_DIR") or os.path.expandvars(r"%LOCALAPPDATA%\woptimizer_git\.git")` |
| `validate_docs.py:481-483` | `_hashes_que_existen` (check 9, R2/R4, la de los hashes del journal) | **idéntico, carácter por carácter** |

Esa duplicación es el hecho central del encargo, y la tarea no lo nombra.

## 2. MEDICIÓN 1 — por qué no corre en CI

**No se invoca, y la exclusión es explícita y deliberada.**
`.github/workflows/release.yml:89-93` lleva, entre el paso de sintaxis de UI y el de la suite:

> `validate_docs.py` NO se ejecuta aqui, y es deliberado: su ancla de commits deriva
> GIT_DIR de `%LOCALAPPDATA%\woptimizer_git\.git`, que solo existe en el host del dueno.

El job `verify` (`:69-95`) tiene tres pasos: `pip install`, `verify_ui_syntax.py` y
`run_tests.py`. Ninguno invoca el validador.

**PERO el motivo que da el comentario es el más pequeño de los tres.** Medido, con cámaras
desechables en `%TEMP%` y el validador real invocado por subproceso:

| Escenario | `GIT_DIR` | Resultado medido |
|---|---|---|
| A. Derivar el default y que no exista (lo que hace hoy el runner) | ruta inexistente | `145 OK, 1 FAIL`, exit 1 |
| B. Repo de **un solo commit** (lo que da el checkout actual del runner) | repo de 1 commit | `145 OK, 154 FAIL`, exit 1 |
| C. Solo `GIT_DIR`, sin `GIT_WORK_TREE` | repo de 1 commit | `145 OK, 154 FAIL`, exit 1 |
| D. Solo `GIT_WORK_TREE`, sin `GIT_DIR` | (default de host) | `145 OK, 0 FAIL` |
| E. Baseline, entorno limpio | (default de host) | `145 OK, 0 FAIL` |

El escenario B es el que importa y **no lo nombra ni el encargo ni el comentario de
`release.yml`**: el job `verify` hace `actions/checkout@v7` **sin `with: fetch-depth: 0`**
(`release.yml:75`), a diferencia de los jobs `commits` (`:32`) y `release` (`:109`), que sí
lo llevan. El runner, por tanto, tiene un clon **shallow de profundidad 1**, y R2 acusa
uno a uno los hashes del journal que un clon de un commit no puede contener.

## 3. MEDICIÓN 2 — qué queda atado, y cuál degrada el resultado

Todo lo que sigue está **medido**, no inferido. Se enumeran las cuatro ataduras:

### A1. `%LOCALAPPDATA%` (la que nombra la tarea) — `validate_docs.py:307` y `:482`

Con el repo ausente el validador **falla en voz alta**: `historial de commits: NO SE PUEDE
LEER ... Motivo literal: git devolvio 128: fatal: not a git repository`, `1 FAIL`, exit 1.

> **La premisa del encargo "un validador que en CI da `0 FAIL` porque no encuentra nada
> no es un validador que pasa" es FALSA, y está medida en las dos direcciones.** Hoy el
> validador no puede dar falso verde por repo ausente. Lo que produce es un **falso rojo**:
> rojo que no significa "el repo está mal".

### A2. El historial shallow del runner — `release.yml:75` — **es la atadura mayor**

Sin `fetch-depth: 0`, el clon del runner tiene un commit. Medido (escenario B): **154 FAIL**,
uno por hash del journal que R2 no resuelve. El motivo que da `release.yml` ("el repositorio
este impecable") es correcto pero **incompleto**: el rojo seguiría existiendo aunque el runner
tuviera el repo desacoplado.

### A3. El historial que el ancla certifica **no está en el remoto** — la tercera, y la que decide

Medido sobre el repo real (`%LOCALAPPDATA%\woptimizer_git\.git`, HEAD `dc5b44a`, remoto
`origin = https://github.com/carcheky/woptimizer.git`), con los **150 hashes** de
`rd_journal.json`:

| Objetos alcançables | Hashes del journal que NO resolverían |
|---|---|
| `--all` (274 objetos; incluye `beta` local y `mirror-local/master`) | **0** sin declarar → baseline `0 FAIL` |
| `origin/main` + `origin/beta` (235 objetos; lo que traería `fetch-depth: 0`) | **28** |

De esos 28, descompuestos con `git cat-file --batch-check`:

- **25 son objetos que existen en el ODB local pero no son alcanzables desde ninguna rama
  del remoto.** Un clon de GitHub, shallow o completo, no los trae.
- **3 no existen en ningún sitio**: `12b9c3bf`, `5623629`, `ee4f753`, los VFS_CORRUPTO, que sí
  están declarados en `commits_perdidos` y por tanto R2 no los acusa.

**Consecuencia: el red de `fetch-depth: 0` daría 25 FAIL de R2.** Es un rojo que no significa
"el repositorio está mal" sino "el historial que el journal ancla vive en el host del dueño".
Y esos 25 **no son pérdidas**: no están perdidos, están sin pushear, y el vocabulario cerrado
`CAUSAS_DE_PERDIDA` (`validate_docs.py:401`) no tiene un valor para eso, ni debe añadirse:
declararlos perdidos sería escribir una mentira en el registro que el ancla existe para
certificar.

### A4. La paridad `GIT_DIR`/`GIT_WORK_TREE` no está en el validador — divergencia medida

`validate_docs.py:309` y `:484` **imponen** `GIT_WORK_TREE = root` sin condiciones, mientras
que `git_safe_commit.get_env()` (`git_safe_commit.py:298-302`) **rechaza** el par roto.

Medido: `validate_docs.py` **no importa ni invoca `git_safe_commit.py`** (0 coincidencias de
`import`/`subprocess` hacia él; solo lo cita en comentarios, `:286`, `:439`, `:502`).

## 4. MEDICIÓN 3 — la trampa de la precedencia de códigos: NO puede ocurrir, y hay una divergencia que sí

**Pregunta:** ¿puede `validate_docs.py` invocado desde CI caer en `2 WOPT_USAGE paridad-git`
por tener solo una de las dos variables?

**Respuesta: NO, y es estructural.** Ese código es del contrato de `git_safe_commit.py`
(`git_safe_commit.py:129`, `CODE_USAGE = 2`), y el validador nunca lo invoca. Medido en los
escenarios C y D:

- Solo `GIT_DIR` → el validador **lo acepta** y le impone `GIT_WORK_TREE = root` → `154 FAIL`,
  no `2`.
- Solo `GIT_WORK_TREE` → el validador impone `GIT_DIR = %LOCALAPPDATA%` y da `0 FAIL`.

**Lo que sí hay es la divergencia:** dos consumidores del mismo `GIT_DIR` con dos políticas
opuestas. El wrapper rechaza el par roto con `2`; el validador lo acepta en silencio. Y el
escenario D muestra el caso simétrico: un `GIT_WORK_TREE` ajeno **no cambia qué ficheros se
validan** (`root` sale de `__file__`, `validate_docs.py:2546`), así que es benigno para el
veredicto, pero **no queda registrado en ninguna parte**: un informe que no dice de qué
repositorio leyó no es auditable.

## 5. La cita de `STATUS.md` que trae el encargo no apunta a lo que dice

- El encargo y `tasks.json` dicen **"fila 121"**. La fila real está en **`STATUS.md:81`**,
  dentro de la sección **🟡 Media** (`:76`).
- `STATUS.md:121` es otra cosa: el hito `| #59 | Tooling | validate_docs.py una vez por
  fichero (TASK-070) |`.
- **`STATUS.md:81` afirma "Detallado en `docs/ai/sandbox-rules.md`" y es FALSO.** Medido:
  `sandbox-rules.md` no menciona el CI en ningún punto — los patrones `no corre en CI`,
  `release.yml` y `verify_ui_syntax` dan **0 coincidencias** en sus 1339 líneas. La exclusión
  vive solo en el comentario de `release.yml`, que es donde nadie la busca.

Mismo patrón que en TASK-074: **el ancla textual de la tarea estaba caducada.**

## 6. DECISIÓN

Ni "desacoplar" ni "documentar la exclusión". Las dos salidas que planteaba el encargo son
incompletas, y la medición dice cuál pesa más:

**Se hace (TASK-075):**

1. **Desacoplar la ruta**, extrayendo la resolución a **UNA función compartida** que sea
   `GIT_DIR`. Sin esa extracción, un `--git-dir` implementado en uno de los dos sitios deja
   el check 5b leyendo un repo y el check 9 otro: el flag "funciona" y el validador da 154
   FAIL. **Es el mutante que este encargo debe cerrar.**
2. **Hacer honesta la degradación**: que el validador pueda correr **sin** repositorio y que
   eso sea **indistinguible de un verde** — nunca. Checks saltados se imprimen como `[SKIP]`,
   nunca como `[OK]`, y el informe cuenta cuántos.
3. **Arreglar la documentación que miente**: el motivo real de la exclusión en
   `release.yml:89-93` (no es `%LOCALAPPDATA%`, es que el historial que el ancla certifica no
   está en el remoto) y la remisión falsa de `STATUS.md:81`.

**NO se hace, y por qué (TASK nueva, TASK-080):**

Añadir el paso al job `verify`. Aunque se desacople la ruta y se ponga `fetch-depth: 0`, los
**25 hashes sin pushear** seguirían dando 25 FAIL de R2. La exclusión en CI **es correcta**;
lo que estaba mal era su motivo escrito. Activarla requiere primero empujar o cambiar el
contrato del ancla, que es una decisión de producto, no de tooling.

## 7. Diseño

### 7.1 Precedencia de resolución, una sola y explícita

```
1. --git-dir <ruta>          (CLI; gana sobre todo)
2. WOPTIMIZER_GIT_DIR        (entorno)
3. GIT_DIR                   (entorno; la precedencia ya documentada y YA ATADA por test)
4. %LOCALAPPDATA%\woptimizer_git\.git
```

El nivel 3 **no se mueve**: `run_tests.py:13523-13525` (fila (e) de la tabla del ancla) ata
hoy el fallback y muere si se borra. Ese test debe seguir verde **y** pasar a través de la
función compartida, para que mutar la función compartida rompa algo.

### 7.2 `GIT_WORK_TREE`

Se respeta si viene en el entorno; si no, `root` (comportamiento actual, no se cambia).
Si `GIT_DIR` llega **suelto**, el validado **no falla** — cambiarlo a fallo tumbaría el bucle
— pero **lo dice en `ok`**, nombrando el repositorio que usó. Un validador que no dice de
dónde leyó no es auditable, y ese `ok` es lo que convierte el silencio de hoy en evidencia.

### 7.3 Fail-loud: qué hay y qué falta

| Estado | Hoy | Decisión |
|---|---|---|
| `--git-dir` no dicho, default no existe | `1 FAIL` con motivo literal (medido) | **se conserva** |
| `GIT_DIR` del entorno no es repo | `1 FAIL` (A4 de `run_tests.py:12806`) | **se conserva** |
| `--git-dir` dicho y **no** es repo | **no existe**: no hay forma de decirlo | **FALLA**, con la ruta literal en el mensaje |
| `--git-dir` dicho y es un directorio vacío | indistinguible de lo anterior | **FALLA** (mismo criterio que `git_safe_commit.validar_repo`: `rev-parse --verify HEAD`) |
| sin repositorio, wanting correr los otros checks | **imposible**: sale rojo siempre | **`--sin-ancla-de-git`**: salta los checks de git, los imprime como `[SKIP]`, y el informe cuenta los saltados |

El criterio de repo es `rev-parse --verify HEAD`, **no** `os.path.exists()`: ya está medido
que un directorio vacío responde `128` y un repo sin commits responde `0` (`validate_docs.py:490-494`),
y un `exists()` no los distingue.

### 7.4 Restricción documental medida

`validate_docs.py:1277-1278` y `:1772` citan **`docs/ai/sandbox-rules.md:55-56` por número
de línea** (las dos filas del `0` de la tabla de códigos). **Añadir filas o líneas por encima
de la línea 61 de ese fichero desplaza esas dos citas sin avisar.** La sección nueva va al
final del documento, y no se inserta ninguna fila en la tabla de códigos.

## 8. Criterios discriminantes

Un test que solo comprueba que `--git-dir` se acepta no mide nada: pasa aunque la ruta derive
igual y aunque el validador dé falso verde. Cada criterio nombra **qué tiene que morir**:

| # | Comportamiento | Mutante que debe morir | Por qué ese mutante lo mata |
|---|---|---|---|
| AC-1 | El default se usa cuando no se pasa nada | borrar el fallback `expandvars` de la función compartida | deja `None` en el entorno de `subprocess` → `TypeError`. **Ya lo mata la fila (e); el AC exige que ahora lo mate la función compartida** |
| AC-2 | `--git-dir` **se honra** | parsear el flag y **no usarlo** (`args.git_dir` sin leer) | los dos repos de la tabla dan el mismo veredicto → el test muere al cambiar el flag |
| AC-3 | **Un solo punto de resolución** | honoured `--git-dir` en el check 5b y **no** en el 9 | el check 9 sigue con el default → 154 FAIL. Es el fallo que la duplicación de `:307`/`:482` hace posible |
| AC-4 | `--git-dir` a un repo con el ciclo anclado da `0` de ancla | el mismo mutante de AC-2, por el otro lado | sin el flag el default no tiene ese commit → FAIL distinto |
| AC-5 | `--git-dir` a ruta **inexistente** → FAIL con la ruta literal | `motivo = None`, o `except: return set()` | el error desaparece y el validador sale `0 FAIL`: el falso verde |
| AC-6 | `--git-dir` a un **directorio que existe y no es repo** → FAIL | `os.path.exists()` en vez de `rev-parse --verify HEAD` | el `exists()` da verde sobre un directorio vacío. Mismo criterio que `run_tests.py:1632-1634` |
| AC-7 | `--sin-ancla-de-git` **no puede** parecerse a un verde | imprimir `[SKIP]` como `[OK]` | con el flag no hay un solo `[OK]` de un check saltado; el mutante los convierte en `OK` y el recuento de saltados no cuadra |

## 9. Fuera de alcance

- **TASK-080**: añadir el validador al job `verify`. Bloqueada por los 25 hashes sin pushear.
- **`fetch-depth: 0`** en `release.yml:75`: correcto y necesario para cuando exista TASK-080, pero
  solo no arregla nada (`:25` seguiría dando 25 FAIL).
- **`CAUSAS_DE_PERDIDA`**: no se toca. Los 25 hashes sin pushear **no están perdidos**, y el
  vocabulario cerrado es lo que hace la cuenta falsable.
- **`STATUS.md:81`**: la corrección de la cita es del dev, en el mismo cambio (ver AC-8).