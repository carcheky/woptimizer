# El fallo de git tiene que salir con un codigo distinto de 0 — y que un test lo demuestre

**Change ID:** `2026-10-04-codigo-salida-fallo-git-s48-2`
**Tarea:** `TASK-061` (superviviente **S48-2** del cierre del ciclo #48)
**Alcance:** `.taskmaster/git_safe_commit.py` (`get_env()`, `validar_repo()`, una puerta nueva de
invocacion), `run_tests.py` (tests), `docs/ai/sandbox-rules.md` (regla 7 y cobertura),
`docs/ai/testing-guide.md`, los cuatro declarantes del recuento, `STATUS.md:89` (cierre de la fila).
**NO toca:** `src/woptimizer/**` — cero cambios de codigo de producto. Y cero cambios en
`.taskmaster/CHANGELOG.md` ni en `mutation-report.md`: los dos guardan la frase original **como
evidencia de lo que se creia**, y corregir ahi seria el mismo fallo que no haberla escrito
(`openspec/changes/2026-10-02-sanear-deuda-status/mutation-report.md:115-116`).

---

## 1. Que cierra esta tarea

Cierra el invariante que el ciclo #11 rompio: **un fallo de git tiene que salir con un codigo de
salida distinto de 0**. Hoy **se cumple en el codigo** y **nadie lo comprueba**. El mutante
`sys.exit(CODE_FAIL)` -> `sys.exit(CODE_OK)` sobrevive a las dos mediciones del toolchain
(`run_tests.py` en verde, `validate_docs.py` en `0 FAIL`), o sea que los dos semi-veredictos lo
dejan pasar.

La victima esta medida y no es hipotetica: el unico consumidor real del codigo es **el agente
orquestador del bucle**, que ramifica por `exit == 0` y despues escribe el changelog "para tener el
hash" (`.agents/agents/architect-review/agent.md:50`, `.agents/skills/id-pipeline/SKILL.md:401`,
plantilla con hashes en `SKILL.md:390-391`).

**Y el dano NO es el del ciclo #11 literal.** `WOPT_NOOP` nunca imprime hash
(`docs/ai/sandbox-rules.md:70`), luego esta puerta no puede devolver a la vida el CHANGELOG con
hashes inventados. El dano real es **ciclo cerrado sin commit**: el panel y el changelog afirman un
versionado que no ocurrio. Misma clase, un grado menos explosivo, y por eso el fix es un test y no
un rediseño del changelog.

---

## 2. Auditoria de la premisa: cuatro puntos del encargo que hay que corregir

El encargo llega con cuatro afirmaciones. **Las cuatro se corrigen**, y dos de ellas son
trampas que habrían producido un veredicto falso en la auditoría.

### 2.1 FALSA — el mutante NO esta en la linea 230

El encargo, `mutation-report.md:73` y `STATUS.md:89` dicen `git_safe_commit.py:230`. Hoy la linea
**230** es `sys.exit(CODE_USAGE)`, la puerta del mensaje que TASK-059 añadió despues de que se midiera
el mutante. El `sys.exit(CODE_FAIL)` del camino de commit esta en **`git_safe_commit.py:410`**
(`print(f"WOPT_FAIL commit ...")` en `:409`).

**Por que esto es una trampa y no un detalle:** si el `mutation-auditor` vuelve a aplicar "la
mutacion del ciclo #48" por numero de linea, lo que muta es la **puerta de uso incorrecto**, no el
fallo de git. Ese mutante **si lo mata** `run_tests.py:16647` (`assert r.returncode == 2`), luego el
auditor reporta "killed" y S48-2 se da por cerrado sin haberlo medido. Un `PASS` sobre el mutante
equivocado.

**Regla que sale de aqui, y es la que ya existe para los hashes** (`mutation-report.md:46-49`): en
este repo, confirmar un mutante por hash no basta, y **anclas por numero de linea tampoco**. El
mutante se localiza **por contenido**: el `sys.exit` inmediatamente posterior a un `print` cuyo texto
contenga `WOPT_FAIL`. Ver seccion 7.

### 2.2 FALSA — `get_env()` no esta en la linea 78

El encargo y `docs/ai/sandbox-rules.md:83` dicen `git_safe_commit.py:78`. La linea **78** es
`_RE_MARCADOR_ANCLA = re.compile(`. La imposicion de `GIT_WORK_TREE` esta en
**`git_safe_commit.py:132`** (`env["GIT_WORK_TREE"] = REPO_ROOT`), dentro de `get_env()` (`:121-133`).
La **sustancia** del encargo es cierta —la imposicion es incondicional y por eso el hook hermetiza
el repo y no el arbol— pero el ancla es falsa y esta propagada en cuatro ficheros
(`.taskmaster/CHANGELOG.md:49, :376, :438`, `docs/ai/sandbox-rules.md:83`,
`.taskmaster/tasks.json:1235`). Ancla corregida en `docs/ai/sandbox-rules.md` por el arquitecto
(seccio 10 de este change); los changelogs se dejan como evidencia.

### 2.3 FALSA — "el test existente solo toca las dos puertas que devuelven antes de cualquier `add`"

Cierto **de un test** y falso **de la suite**. `test_git_safe_commit_fail_safe`
(`run_tests.py:1401-1549`) solo exige 3, 2 y el 0 de `--verify`: ninguna de sus invocaciones llega a
un `WOPT_FAIL`, y ahi S48-2 es exacto. Pero **la suite ya ensucia el arbol real a proposito, lo
declara y lo revierte**: `run_tests.py:16410-16413` ("el truco declarado del ciclo 52") y
`run_tests.py:16590-16642` (fichero `_t059_testigo_stageado.txt` untracked que el test crea y
borra, con `staged() == []` como testigo). O sea: **la via B ya tiene precedente, midiendo su
coste**. Lo que no tiene es justificacion para seguir siendo la unica.

### 2.4 CIERTO, con la cifra correcta — donde esta hoy el codigo 1

`test_git_safe_commit_fail_safe` es `run_tests.py:1401` (no `:1352`). Sus unicas aserciones de
`returncode` son **3**, **3**, **2** y **0** (`--verify` con repo sano). **Cero aserciones de `1` en
todo el fichero**: ese es el agujero, medido y no inferido.

### 2.5 FALSA — el ancla del changelog en `SKILL.md:382`

La frase "para tener el hash" esta en **`.agents/skills/id-pipeline/SKILL.md:401`**; `:382` es el
encabezado de "Mutaciones auditadas". La plantilla que exige hashes son las lineas `:390-391`
(`### Outcome` / `- Commits: <hash1>, <hash2>`). El contenido de la afirmacion es cierto; el numero
de linea no. `agent.md:50` si es exacto.

---

## 3. LA DECISION DE DISENO (D1): paridad de `GIT_DIR` y `GIT_WORK_TREE`

> **`get_env()` honra `GIT_WORK_TREE` del entorno igual que honra `GIT_DIR`, y exige que los dos
> variables lleguen juntas o ninguna: si llega una sola, se rechaza con `2` sin escribir nada.**

En una frase: **o vienen las dos del entorno, o el wrapper usa su par por defecto
(`%LOCALAPPDATA%\woptimizer_git\.git` + `REPO_ROOT`) sin sorpresas; nunca una de las dos.**

### 3.1 Por que esta y no la otra

| | Via A: honra `GIT_WORK_TREE` + paridad | Via B: el test ensucia el arbol real, declarado |
|---|---|---|
| Coste | Cambio de comportamiento del wrapper (3-4 lineas) | **Cero** cambio de producto |
| El test del codigo 1 | Hermetico de verdad: repo **y** arbol temporales | Medible, pero escribe en el arbol del dueno |
| El agujero que creo S48-2 | **Se cierra**: la combinacion "`GIT_DIR` desechable + arbol real" pasa a ser imposible | **Sigue abierto**: es justo el mecanismo que produjo el `add -A` sobre el arbol real medido en `mutation-report.md:192-194` |
| Reversibilidad si el test falla | Ninguna escritura que deshacer | Un fichero huerfano en un arbol cuyo proximo `add -A` es del producto: se cuela en el historial del dueno |
| Compatibilidad | Medida y cerrada (seccion 4) | Perfecta |

**Se elige A** por tres razones, en orden de peso:

1. **B deja vivo el mecanismo que causo el problema.** El Hook "tests hermeticos" de
   `GIT_DIR` sin `GIT_WORK_TREE` fue lo que permitio stagear y commitear el arbol real dentro de un
   repo de sonda (`mutation-report.md:78` y `:192-194`). Con paridad, esa combinacion **deja de ser
   representable**, y con ella desaparece la contaminacion que ya ocurrio dos veces en este repo
   (`STATUS.md:23`).
2. **B pone un test a escribir en el arbol de un VFS con `.git` corrupto.** No es un detalle: es la
   razon de que exista `git_safe_commit.py`. Un residuo de un test que muere a mitad se lo lleva el
   proximo `add -A` del producto, y ese commit ya es el del dueno.
3. **A es mas barato de lo que parece y su superficie de compatibilidad esta medida** (seccion 4):
   todos los que tocan `GIT_WORK_TREE` en el repo lo ponen a `raiz` —el mismo valor que impone el
   wrapper—, luego no cambia una sola asercion viva.

### 3.2 El precio, dicho con su nombre

A es un **cambio de comportamiento de la unica puerta de versionado**, y por eso va con su
_guardia_: sin la paridad, honar `GIT_WORK_TREE` seria un arma de doble filo (basta `GIT_DIR` real +
`GIT_WORK_TREE` ajeno para versionar un arbol extranjero en el historial real). **La paridad no es
un extra: es el precio de la decision.** Sin ella, A seria peor que B.

### 3.3 La paridad es fail-CLOSED y sale con 2, no con 3

`2` = "tu invocacion esta mal" (misma lectura que D3 de TASK-059: la puerta no ejecuta ninguna
operacion de git). Se **extiende la fila "cuando" del `2`** de la tabla de
`docs/ai/sandbox-rules.md:58`; no se anade ningun codigo, y el contrato 0/1/2/3 sigue integro.
Se comprueba **despues** de `validar_repo` (y por tanto **tambien en `--verify`**), porque si el repo
no se puede comprobar, "no pude ni comprobar" (3) gana a "tu invocacion esta mal" (2) — la misma
precedencia que fijo D2 y que esta medida contra el codigo real.

---

## 4. Compatibilidad del cambio de `get_env()`: MEDIDA, no supuesta

Se ha grepado `GIT_WORK_TREE` en **todo** el repo. Estos son todos los que lo tocan:

| Fichero:linea | Que hace | Efecto de honrarlo |
|---|---|---|
| `AGENTS.md:61-62` | La snippet documentada pone **los dos** a las rutas reales | **Ninguno**: `GIT_WORK_TREE` ya es `REPO_ROOT` |
| `run_tests.py:1432-1433` (`test_git_safe_commit_fail_safe`) | `GIT_DIR` temporal + `GIT_WORK_TREE = root` | **Ninguno**: mismo valor |
| `run_tests.py:16422-16423` (INFO de degradacion) | `GIT_DIR` temporal + `GIT_WORK_TREE = raiz` | **Ninguno**: mismo valor |
| `run_tests.py:16626-16627` (puerta e2e) | `GIT_DIR` temporal + `GIT_WORK_TREE = raiz` | **Ninguno**: mismo valor |
| `run_tests.py:6353` (`_entorno_git_del_repo`) | `GIT_WORK_TREE = repo_root` | **Ninguno**: mismo valor |
| `run_tests.py:12095`, `:12303`, `:12754-12756` | Lo **quitan** (o lo restauran) | `REPO_ROOT`, igual que hoy |
| `.github/workflows/release.yml:94-95` | CI corre `run_tests.py`, **no** invoca el wrapper | **Ninguno** |

**Conclusion: no hay nada que migrar.** El camino normal (sin `GIT_DIR` en el entorno) queda
byte a byte igual, y los tres subprocesos de los tests de TASK-059 siguen viendo el mismo arbol.
Lo que cambia es la clase de invocaciones que **hoy nadie usa y que son peligrosas**: "`GIT_DIR` de
otro sitio sin `GIT_WORK_TREE`".

**Y la prueba definitiva, que no es un grep de nombres de variable:** se han enumerado **todos** los
sitios que invocan `git_safe_commit.py` como subproceso, y son **tres**, y **los tres** ponen las dos
variables: `run_tests.py:1434-1437` (`invocar` de `test_git_safe_commit_fail_safe`),
`:16424-16426` (la copia degradada) y `:16628-16631` (la puerta e2e). Las demas apariciones de
`GIT_WORK_TREE` en el fichero (`:13046`, `:16815`, `:17182-17183`, `:17287`, `:17402`) son de
subprocesos de **git plano** para el validador, no del wrapper, y por tanto no pasan por la puerta.
**Ninguna invocacion viva queda con una sola variable**, luego la paridad no rompe nada.

**Y sale un beneficio no pedido:** los dos tests de TASK-059 dejaran de necesitar el fichero
testigo untracked en el arbol real (tarea T-5).

---

## 5. El algoritmo

### 5.1 `get_env()` (`:121-133`)

```python
def get_env():
    env = os.environ.copy()
    # D1: paridad. Una sola de las dos variables del entorno es una invocacion
    # malformada, y su fallo historico fue commitear el arbol REAL en un repo
    # de sonda. No se degrada en silencio: se rechaza (ver `main`).
    solo_dir = bool(env.get("GIT_DIR")) != bool(env.get("GIT_WORK_TREE"))
    env["GIT_DIR"] = env.get("GIT_DIR") or LOCAL_GIT_DIR
    env["GIT_WORK_TREE"] = env.get("GIT_WORK_TREE") or REPO_ROOT
    env["WOPT_PARIDAD_ROTA"] = "1" if solo_dir else ""
    return env
```

(`WOPT_PARIDAD_ROTA` es una bandera interna; si se prefiere, `get_env()` puede devolver
`(env, solo_dir)`. Lo que **no** puede es callarse.)

### 5.2 `validar_repo()` (`:159-192`)

Anade **una** comprobacion al principio, con el mismo estilo fail-closed: el arbol de trabajo
efectivo tiene que ser un directorio. Sin ella, un `GIT_WORK_TREE` a una ruta inexistente cae en un
`rc` de git que nadie ha medido, y el codigo 3 tiene que ser "no pude ni comprobar" de forma
determinista, no "git dijo algo raro".

### 5.3 La puerta de paridad, en `main()`, DESPUES de `validar_repo`

```
parse_args -> validar_repo (repo efectivo: GIT_DIR + arbol, 3 si no) -> [--verify]
           -> PARIDAD (2, WOPT_USAGE paridad-git, sin escribir)
           -> status --porcelain -> NOOP (0) -> PUERTA DEL MENSAJE (2)
           -> add -A -> diff --cached -> commit -> WOPT_COMMIT_OK (0)
```

`--verify` ** tambien pasa por la paridad: si dice `WOPT_REPO_OK` esta afirmando que el repo y su
arbol son usables, y una asimetria de ese par es exactamente la mentira que `--verify` no debe
contar.

---

## 6. Los tests, y por que cada uno MATA (no tautologicos)

Tres tests nuevos, headless, en Windows, y **sin ninguna escritura en el arbol real** una vez
hecha T-1. Todos en la seccion headless (detras del marcador `MARCADOR_HEADLESS`,
`run_tests.py:12919`) y **definidos e invocados** a la vez, que es lo que deriva el check 7.

### T-2 — `test_el_contrato_de_codigos_esta_atado_a_cada_linea_wopt` (`ast`, sin subproceso)

Extrae del wrapper **real** (importado, no copiado) todos los `print` con un marcador `WOPT_*` y
los `sys.exit(CODE_*)` que los cierran, y exige esta tabla:

| Marcador | Codigo | Sitios hoy |
|---|---|---|
| `WOPT_COMMIT_OK` | `CODE_OK` | 1 (`:422`) |
| `WOPT_NOOP` | `CODE_OK` | 2 (`:359`, `:400`) — **la sobrecarga del 0** |
| `WOPT_FAIL` | `CODE_FAIL` | 6 (`:356`, `:388`, `:397`, `:403`, `:409`, `:415`) |
| `WOPT_USAGE` | `CODE_USAGE` | 2 (`:330`, `:381`) |
| `WOPT_REPO_INVALIDO` | `CODE_REPO` | 2 (`:341`, `:346`) |

Las **tres** aserciones que la hacen discriminate, y las tres importan:
1. Cada `print` con `WOPT_*` esta en la tabla.
2. **Cada `sys.exit` de `main()` esta en la tabla** — ningun `exit` sin marcador canónico. Esto
   mata al mutante aunque le añadan un `print` de mentiras para parecer honesto.
3. Los valores de `CODE_OK/FAIL/USAGE/REPO` son 0, 1, 2, 3 (mata el mutante que intercambia dos
   constantes sin tocar ningun `exit`).

**Por que falla sin el fix:** el mutante cambia el `CODE_*` de la MISMA sentencia que la tabla
deriva del fuente, luego la tabla y el contrato discrepan y la asercion 1 salta en `:409-410`.
Ademas comprueba que `get_env()` **no** asigna `GIT_WORK_TREE` de forma incondicional (mata la
regresion de T-1 sin necesidad de subproceso).

### T-3 — `test_un_fallo_de_git_no_sale_con_cero` (extremo a extremo, el testigo del codigo 1)

Es el **unico** test que prueba el *runtime*, que es lo que lee la victima. Con `GIT_DIR` temporal,
`GIT_WORK_TREE` temporal (arbol sucio con un fichero), identidad configurada en el repo temporal
(reutilizar `_git_de_fixture`, patron ya establecido en `run_tests.py:16612-16620`) y un
`pre-commit` que sale con 1 (mecanismo **ya medido**, `docs/ai/sandbox-rules.md:120-121`; si en
Windows el bit de ejecucion estorba, `core.hooksPath` a un directorio temporal con el mismo hook):

- `returncode == 1` — **MATA el mutante**: con `CODE_OK` sale 0.
- `"WOPT_FAIL commit"` en stdout y **la linea `WOPT_*` es la ultima** (regla 4).
- `"WOPT_COMMIT_OK" not in stdout`: un fallo **nunca** puede reportar commit creado.
- **No contaminacion**: el `HEAD` del repo real es identico antes y despues, y no queda ningun
  fichero con el prefijo unico de la sonda en `raiz`.

El ancla del mensaje es **`ciclo 999`**, no `TASK-061`: la convencion de ciclo no depende de
`.taskmaster/tasks.json` (`git_safe_commit.py:261-264`), luego el test no se rompe cuando la tarea
se cierre. Y de paso ejercita una de las dos convenciones que no dependen de ficheros.

### T-4 — `test_el_cero_esta_sobrecargado_por_dos_desenlaces_y_solo_por_esos_dos`

Dos filas de tabla, un repo y un arbol temporales:
- **NOOP**: arbol limpio + mensaje anclado -> `rc == 0`, `WOPT_NOOP` presente, y **ningun hash**
  en stdout: se exige que tras el marcador no aparezca ningun `[0-9a-f]{7,40}`. Discrimina contra
  el mutante que imprime un hash en el no-op, que es la forma exacta de "hashes que no existen".
- **COMMIT_OK**: arbol sucio -> `rc == 0` y `WOPT_COMMIT_OK <hash>` con hash que **resuelve** en ese
  repo (`git cat-file --batch-check`), no un hash con forma de hash.
- **Paridad**: `GIT_DIR` temporal **sin** `GIT_WORK_TREE` -> `rc == 2`, `WOPT_USAGE paridad-git`, y
  **cero** escrituras en el arbol real.

**Por que esta fila no es tautologica:** es la unica que **falla hoy, sin mutacion ninguna**. Con el
codigo actual, `GIT_DIR` solo + `GIT_WORK_TREE` impone commitear el arbol real dentro del repo
temporal y sale con 0: falla el `== 2` y falla el testigo de no-contaminacion a la vez. Es un
criterio de correccion, no un guardian de mutante.

---

## 7. Protocolo de mutacion (obligatorio para el Paso 4)

1. **Localizar el mutante por CONTENIDO, nunca por numero de linea.** Se busca el `sys.exit` que
   sigue a un `print` con `WOPT_FAIL` (seccion 2.1). Si se vuelve a citar `git_safe_commit.py:230`,
   lo que se muta es la puerta de uso y el veredicto sera falso.
2. **Se miden los DOS semi-veredictos** — mutante -> `run_tests.py` **y** `validate_docs.py`
   (los dos semi-veredictos, que ya se demostro que no son dos testigos sino uno medido dos veces),
   y el mutante tiene que morir en ambos. La cifra nueva del recuento (`106`) va en los cuatro
   declarantes **con el mutante puesto**, no despues.
3. **Hash y comportamiento** (regla ya escrita en `mutation-report.md:46-49`): el hash solo no
   prueba que el mutante estuviera en disco, porque el VFS a veces no escribe.
4. **Seis sitios, no uno**: `WOPT_FAIL` aparece en 6. Mutar uno y no los otros cinco demuestra que
   existe un guardian, no que la familia esta muerta. El guardian de T-2 los cubre todos; el
   e2e de T-3 cubre el de `commit`.
5. **Sin tocar el historial real en ninguna sonda.** Con T-1 hecha, ninguna sonda necesita
   `GIT_WORK_TREE = REPO_ROOT`.

---

## 8. Lo que el validador obliga a sincronizar (si no, el repo se pone rojo)

Anadir 3 tests cambia el recuento y `validate_docs.py` mira **cuatro** declarantes, no uno:

| Declarante | Que exige | Patron |
|---|---|---|
| `STATUS.md` | el total **y el reparto** `N backend + M headless` | `validate_docs.py:116`, `:161` |
| `AGENTS.md` | el total | `validate_docs.py:117` |
| `README.md` | el total | `validate_docs.py:118` |
| `docs/ai/testing-guide.md` | **una fila por test** (`^\|\s*\d+\s*\|\s*`test_``) | `validate_docs.py:148-158` |

Ademas `run_tests.py` exige **definidos = invocados** (derivado con `ast`). Total previsto:
**136 -> 139**, reparto **107 backend + 29 headless -> 107 backend + 32 headless** (medido el
2026-10-04 con `validate_docs.py` en `124 OK / 0 FAIL`; el marcador `MARCADOR_HEADLESS` esta hoy en
`run_tests.py:17956`). Y `docs/index.md`
NO lo vigila el check (es S48-3, `TASK-060`), así que se actualiza por uniformidad — no por
descuido, sino porque ahí está la cifra de un quinto declarante que nadie comprueba.

---

## 9. Limites declarados, no omitidos

1. **T-2 afirma el codigo declarado, no el ejecutado.** Por eso hace falta T-3: el AST ata la
   sentencia al contrato, el subproceso ata el contrato a la realidad. Un test solo no alcanza.
2. **La paridad es mas estrecha que "el repo esta bien".** No valida que el par apunte al proyecto
   correcto: valida que no se puede mezclar un repo de un sitio con un arbol de otro. El caso
   "repo sano equivocado" sigue sin deteccion, y se declara.
3. **No hay cerrojo.** Dos actores que commitean a la vez se reparten el resultado
   (`docs/ai/sandbox-rules.md:231-233`). No lo arregla este change.
4. **T-3 depende de un hook de git**, que en Windows corre por el `sh` de git. Si `pre-commit`
   resultara fragil en otro host, la fila se queda sin guardar y el invariante queda solo con T-2.
   Se declara en vez de esconderse.
5. **Cero cambios en `src/woptimizer/**`.**

---

## 10. Lo que hace el arquitecto en este paso (fuera del trabajo de `openspec-dev`)

- **Ancla falsa corregida** en `docs/ai/sandbox-rules.md`: `git_safe_commit.py:78` -> **`:132`**,
  y las cuatro aserciones de `run_tests.py` citadas por numero de linea -> por rango, mas el
  mutante `229-230` -> **`:409-410`**. Es un fichero que me pertenece y la frase era falsa; dejarla
  seria propagar el error a la regla 7 que este change va a reescribir.
- **NO** se corrigen los mismos numeros en `.taskmaster/CHANGELOG.md:49, :376, :438` ni en
  `mutation-report.md:73`: son el registro de lo que se creia el 2026-10-02, y la doctrina del repo
  (y el mismo informe, `:115-116`) es conservarlos. La correccion vive aqui y en el panel.
- **NO** se reescribe el criterio de TASK-022 en `.taskmaster/tasks.json:322` ("`GIT_WORK_TREE`
  siempre = `REPO_ROOT`"): describe el contrato vigente hasta hoy y se supera, no se falsifica. Lo
  dice el `notes` de TASK-061.
