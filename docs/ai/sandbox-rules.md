# Reglas de Sandbox, Permisos y Compilación Windows

## El Problema del Sandbox (EPERM)
El entorno de ejecución de agentes en Windows a menudo restringe la creación directa de subprocesos (`Access is denied` / `EPERM`) al invocar `cmd.exe`, `powershell.exe` o comandos que crean forks masivos.

## Patrones Permitidos y Soluciones

### 1. Ejecución de Código Python
- `python script.py` usando `run_command` **SÍ** está permitido siempre que el script no intente hacer llamadas directas no autorizadas a shells externas.
- Siempre inicializar el encoding de consola al inicio de los scripts puente para evitar errores de Windows cp1252:
  ```python
  import sys, io
  sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
  ```

### 2. Bypass de Shell para Compilación (PyInstaller)
- NUNCA llamar a `pyinstaller` mediante comandos de shell si el sandbox bloquea subprocesos.
- Ejecutar mediante el builder nativo síncrono `force_build.py` o mediante la API de Python:
  ```python
  import subprocess, sys
  subprocess.check_call([
      sys.executable, "-m", "PyInstaller",
      "--onefile", "--noconsole", "--uac-admin",
      "--name", "woptimizer", "--clean",
      "src/woptimizer/__main__.py"
  ])
  ```
- O delegar al shell de Windows sin bloqueo de proceso hijo usando `build_trigger.vbs` con `os.startfile()`.

### 3. Invariante de Salida
- El ejecutable siempre debe colocarse en: `dist/woptimizer.exe`.
- Debe incluir el flag `--uac-admin` para poder matar procesos elevados de sistema.

## Aislamiento Git en Entornos Cloud (VFS)

En Windows con unidades virtuales (Nextcloud / OneDrive) el `.git` que vive **dentro** del árbol de
trabajo se corrompe: el filtro VFS no soporta la creación de objetos (`unable to create temporary
file: Invalid argument`, `fatal: bad object HEAD`). En este repositorio esa es la condición real,
no hipotética. La estrategia vigente es **desacoplar el historial** a una ruta local:

```powershell
$env:GIT_DIR = "$env:LOCALAPPDATA\woptimizer_git\.git"
$env:GIT_WORK_TREE = "C:\Users\carch\Nextcloud\Scripts\woptimizer"
```

`.taskmaster/git_safe_commit.py` es la **única puerta de salida del versionado** (AGENTS.md §2 lo
impone en cada ciclo) y automatiza esa redirección. Por eso su código de salida es un contrato
normativo: si el pipeline lee un `0` donde no hubo commit, registra un hash inexistente y el
ciclo se da por versionado sin haberlo estado.

### Contrato de códigos de salida

| Código | Significado | Cuándo | Línea canónica en stdout |
|---|---|---|---|
| `0` | Commit creado de verdad | `git commit` con returncode 0 | `WOPT_COMMIT_OK <hash-short> <mensaje>` |
| `0` | Nada que comitear (benigno) | `git diff --cached --quiet` == 0 tras `add -A` | `WOPT_NOOP <motivo>` (**sin hash**) |
| `1` | Fallo de una operación de git | `git status`, `git add -A` o `git commit` con rc != 0, o excepción al lanzarlos | `WOPT_FAIL <operacion> <detalle>` |
| `2` | Uso incorrecto | sin mensaje, mensaje vacío, más de un posicional o flag desconocido | `WOPT_USAGE <detalle>` |
| `3` | Repositorio no verificable | `GIT_DIR` inexistente, no es un git dir, `HEAD` no resuelve, `is-inside-work-tree` != `true`, o `git` no ejecutable | `WOPT_REPO_INVALIDO <detalle>` |

Reglas duras (TASK-022, `openspec/changes/2026-09-29-git-tooling-resilience/`):

1. **`0` solo aparece en dos casos**: commit creado (con hash real) o nada que comitear. Ningún
   otro desenlace devuelve `0`.
2. **Nunca hay fallback.** Si el `GIT_DIR` desacoplado no valida → `3` sin escribir nada. Nunca
   se intenta el `.git` del árbol de trabajo.
3. **`git add -A` fallido aborta con `1`**, sin ejecutar `commit`: seguir sería staging parcial
   silencioso.
4. **La línea `WOPT_*` va a stdout y es la última que se imprime.** Es la única que el pipeline
   debe leer. `WOPT_NOOP` nunca imprime hash (el agente no inventa hashes en el CHANGELOG).
5. **Nada que comitear se decide con `git diff --cached --quiet`** (rc 0 = nada staged, rc 1 =
   hay staged, rc > 1 = error), **nunca** parseando stderr: git traduce sus mensajes según
   `LANG`/`LC_ALL`, así que `"nothing to commit"` no aparece nunca en un Windows en español y un
   árbol limpio se clasificaría como fallo.
6. **Un `git status` fallido es un error, no "hay cambios".** Se valida el repositorio con
   `rev-parse --git-dir`, `rev-parse --is-inside-work-tree` y `rev-parse --verify HEAD`;
   `os.path.exists()` no basta.
7. **Precedencia de `GIT_DIR`:** si el entorno ya lo trae, se respeta y no se sobrescribe (es la
   vía documentada arriba y además el hook que permite tests herméticos). Si no, se usa
   `%LOCALAPPDATA%\woptimizer_git\.git`. La validación se aplica igual en ambos casos.
   **Matiz medido el 2026-10-02 (ciclo #48), porque «tests herméticos» era media verdad:** ese
   hook hermetiza **el repositorio, no el árbol de trabajo**. `get_env()` respeta el `GIT_DIR`
   del entorno pero **impone `GIT_WORK_TREE = REPO_ROOT` sin condición** (`git_safe_commit.py:78`),
   así que una invocación con un `GIT_DIR` desechable sigue haciendo `add -A` y `commit`
   **sobre el árbol de trabajo real**. Medido: una sonda con `GIT_DIR` temporal stageó y
   commiteó el árbol real dentro del repo temporal (el historial real quedó intacto, porque
   `GIT_DIR` era el temporal). Por eso el test de la sección siguiente solo ejercita las dos
   puertas que devuelven **antes de cualquier `add`**.
8. **Todas las cadenas de `print()` del wrapper son ASCII puro** (trampa #16: la consola es
   cp1252). Los comentarios y docstrings sí llevan acentos.

### Flag `--verify`

```bash
python .taskmaster/git_safe_commit.py --verify
```

Autocomprobación **de solo lectura** (solo `rev-parse`): ejecuta **exactamente** la misma función
`validar_repo()` que el camino principal —prohibido darle una ruta de código propia— e imprime
`WOPT_REPO_OK <git_dir>` + `0` si el repositorio está sano, o `WOPT_REPO_INVALIDO <detalle>` + `3`
si no. Es el mecanismo de diagnóstico cuando el pipeline recibe un `!= 0` sin escribir nada.

### Cobertura

`run_tests.py` -> `test_git_safe_commit_fail_safe()` invoca el wrapper como subproceso con
`GIT_DIR` apuntado a rutas temporales inválidas y exige los códigos exactos del contrato
(`3` y `2`). Es un test que **discrimina**: revierte el fix del código de salida y falla. No toca
el repositorio real ni su historial.

**Lo que esta cobertura NO prueba, medido el 2026-10-02 (ciclo #48):** ninguna de las invocaciones
del test llega a un `WOPT_FAIL`; sus aserciones son `returncode == 3` (`run_tests.py:1399`,
`:1413`, `:1423`) y `== 2` (`:1435`). El código `1` —**el del fallo de git**, que es el invariante
que el ciclo #11 rompió devolviendo `0`— **no lo comprueba nadie.** Mutante medido sobre el
`git_safe_commit.py` real (`sys.exit(CODE_FAIL)` -> `sys.exit(CODE_OK)` en el camino de commit,
líneas 229-230): **la suite entera queda 103/103 en verde con exit 0**, y el wrapper imprime
`WOPT_FAIL commit` mientras sale con `0`, así que un consumidor que lee el código de salida —que
es lo que el contrato declara normativo— se lleva el falso verde. El invariante **se cumple hoy en
el código** (medido: repo temporal con un `pre-commit` que sale con 1 -> `WOPT_FAIL commit` + exit
1), pero **nadie lo ata a un test**: por eso vive como 🔴 en la fila del `spawn EPERM` de
`STATUS.md:88`. **SEGUNDA MEDICIÓN (cierre del ciclo #48):** el mutante sobrevive también a `validate_docs.py` (`110 OK / 0 FAIL` con el mutante puesto), así que los dos semi-veredictos del toolchain lo dejan pasar. **La víctima, nombrada:** el único consumidor real del código de salida es el **agente orquestador** (`.agents/agents/architect-review/agent.md:50` y `.agents/skills/id-pipeline/SKILL.md:382`, que escribe el changelog tras el commit «para tener el hash»), mientras que `run_tests.py` solo mira `3` y `2` y `validate_docs.py` solo lo menciona. Y el matiz que corrige el tamaño del daño: un `WOPT_NOOP` **no lleva hash** (regla 4 de esta tabla), luego esta puerta no puede reintroducir el CHANGELOG con hashes inventados; el daño real es el ciclo cerrado sin commit. Desde el cierre del ciclo #48 tiene dueño: **`TASK-061`**. Cerrarla exige decidir antes qué se hace con `GIT_WORK_TREE` (regla 7) y después
escribir su test.

## Ancla de trazabilidad en el historial (TASK-057, ciclo 47)

### La regla

El requisito de registrar el ciclo N **exige una entrada de changelog por ciclo, y el conjunto
exigido es la UNIÓN de dos fuentes**:

```
ciclos_requeridos = ciclos_del_journal | ciclos_del_historial
```

`validate_docs.py` -> `_comprobar_ancla_del_changelog()` implementa las dos mitades:

- **`.taskmaster/rd_journal.json`**, que el orquestador escribe antes que los changelogs.
- **El historial de commits** (`git log --format=%s --all`), del que se derivan los ciclos con
  `_ciclos_del_asunto()`, que devuelve un **conjunto** y no un número: regex
  `\b(?:ciclo|cycle)(s?)\b[\s:#-]*#?(\d{1,4})(?:\s*-\s*(\d{1,4}))?`, case-insensitive, primera
  coincidencia. El **plural declara más de un ciclo** (G1, cerrado en el ciclo #47):
  `ciclos 14-20` corrobora los ciclos 14 a 20 con ambos extremos, y `ciclos 47` —plural con un
  número suelto— corrobora solo ese. El rango se expande **solo en plural** y hasta
  `MAX_CICLOS_DE_UN_RANGO = 50`; por encima del tope, o invertido (`ciclos 20-14`), degrada al
  primer número, que es exactamente lo que hacía el parser sin rango: acota el daño, no lo inventa.
  Medido el 2026-10-02 sobre los **159 subjects** reales: **un único commit** depende del plural,
  `feat(ciclos 14-20)`, y con él el historial corroboraría 6 ciclos más (los 15 a 20).

Es una **unión y no una sustitución**, y la diferencia no es de estilo. Medido: los commits de
cierre de los ciclos 1, 2, 3 y 15 a 20 **no llevan marcador de ciclo**, así que si el historial
sustituyera al journal, esos ciclos perderían su único requisito y el falso verde volvería por
la puerta de atrás.

El historial se lee con el **mismo `GIT_DIR` desacoplado** que usa `git_safe_commit.get_env()`
(`GIT_DIR` del entorno si ya viene —es el hook que permite tests herméticos—, si no
`%LOCALAPPDATA%\woptimizer_git\.git`; `GIT_WORK_TREE` = raíz del repo).

### Por qué el historial y no otra cosa

Porque está **fuera del árbol de trabajo**, es **append-only** y **direccionado por contenido**.
Para que el ciclo N deje de ser exigible hay que **reescribir historia**, no editar una clave de
un JSON. Es la máxima independencia alcanzable dentro de la banda de autonomía del proyecto.

Opciones **descartadas con medición**, no con opinión (detalle en
`openspec/changes/2026-10-01-validator-independent-anchor/proposal.md` §4):

| Opción | Por qué se descartó |
|---|---|
| Anclar por fecha (commits más nuevos que la fecha del último ciclo) | **Decorativo.** El journal tiene resolución de minuto y 5 ciclos comparten `2026-10-01T23:4x`; casi todos los commits son del mismo día. Un ciclo 47 huérfano del mismo día no se ve. |
| Verificar que cada hash del campo `commits` del journal exista | **Era `41 de 46 hashes no resuelven`, y era FALSO.** Remedido el 2026-10-02 extrayendo el hash (`\b[0-9a-f]{7,40}\b`) y no el string del campo: **11 de las 47 entradas no declaran hash alguno** (ciclos 1, 2, 14-20, 27, 28: `commits` a `null` o `[]`), y de las 36 que sí lo declaran solo **3 hashes no resuelven** (`5623629` del ciclo 30, `ee4b753` del 31 y `12b9c3bf` del 33) —los ciclos 30 y 31 resuelven por su segundo y tercer hash—, así que solo el **ciclo 33** queda sin ninguno resoluble: el check daría **1 FAIL, no 41**. El error de origen era medir el STRING (`617eef8 (architect)`) en vez del hash, la misma clase de bug que este ciclo existe para matar. Sigue yendo a `TASK-059`, pero por el residuo real (11 entradas que no declaran nada y 3 hashes perdidos con el `.git` corrupto del VFS), no por una cifra que nunca fue cierta. **Denominador medido el 2026-10-02 (cierre del ciclo #47): 47 entradas, no 46; el numerador 11 y la lista de ciclos no cambian.** Una cifra caducada escrita junto a la cifra viva es peor que no escribirla: por eso el resto del apartado sí remite al informe del validador, que reimprime los números en cada pasada. |
| Encadenado criptográfico de entradas del journal | Detecta la **reescritura** retroactiva, no la **omisión**: truncar la cadena por el final es trivial. No toca este residuo. |
| Auto-referencia (tabla resumen del changelog, campo `commits`) | Ya demostrado como falso verde en el ciclo #15. |
| Puerta humana (aprobación del propietario por ciclo) | Es la única independencia real, pero incompatible con la autonomía de coste 0 y no automatizable. |

### Alcance: lo que es estable, y donde hay que leer la cifra

Este apartado **no** afirma una cifra fija de subjects, y es deliberado. La cifra caduca con cada
commit, y una cifra caducada escrita en la documentación es peor que no escribirla: se relee como
verdad y nadie vuelve a medirla. El dato vive en la línea de informe del validador, que lo
reimprime **viva en cada pasada**:

```text
historial de commits: N subject(s), M con marcador de ciclo y K SIN marcador
(punto ciego medido); C ciclo(s) corroborables frente a los J del journal
```

Esa línea es el único sitio donde el número es de fiar. Si este documento y el informe no
coinciden, **el que caduca es este documento**.

Lo que sí es estable, y por eso se afirma sin cifra ni fecha de medición:

- La **unión no es una sustitución**: los commits de cierre de los ciclos 1, 2, 3 y 15 a 20 no
  llevan marcador de ciclo, así que si el historial sustituyera al journal, esos ciclos perderían
  su único requisito.
- **Más de la mitad de los subjects del repo no llevan marcador de ciclo** (son los `feat(...)`,
  `fix(...)`, `test(...)`). La proporción es estable; el número absoluto no. Por eso un ciclo
  cerrado con asunto `feat(...)` y sin entrada de journal sigue sin tercer testigo (punto 2 de la
  limitación residual de más abajo).
- `ciclos_del_historial - ciclos_del_journal = ∅` **hoy**: la unión no pone el repo en rojo. Es una
  propiedad del estado actual, no una garantía, y la vigila el validador en cada pasada.
- Del campo `commits` del journal: la mayoría de las entradas lo declaran como lista limpia de
  hashes y unas pocas lo dejan vacío; los hashes que no resuelven son residuo conocido y van a
  `TASK-059` (tabla de opciones de más arriba, con su medición del día en que se hizo).

### LIMITACIÓN RESIDUAL — el problema NO está cerrado

Se documenta sin adornos porque este repo ya pagó una vez por declarar cerrado un problema que
no lo estaba (ciclo #15):

1. **El historial lo escribe el mismo actor que el journal.** La ganancia es de **clase de
   fallo** —reescribir historia frente a editar una clave de un JSON—, **no de independencia de
   actor**. Quien puede mentir en el journal puede mentir en los mensajes de commit.
2. **Más de la mitad de los commits no llevan marcador de ciclo** (son los `feat(...)`, `fix(...)`,
   `test(...)`; la cifra viva —subjects leídos, con marcador y sin él— está en la línea de informe
   del validador que se copia arriba). Si un ciclo se comitea **sin** commit de cierre y **sin**
   entrada de journal, no hay tercer testigo y el validador **no lo ve**. Cerrar eso es
   `git_safe_commit.py` rechazando el mensaje sin identificador de ciclo = **`TASK-059`**, no esta
   tarea. Aquí **no** se HPEa más.
3. **Un parser de marcador es una convención leída, no una verdad**: un asunto que mencione
   "ciclo 15" por hablar de él corrobora el 15. Solo puede **ablandar** el ancla, nunca
   endurecerla, así que no puede producir un FAIL falso — pero tampoco puede cerrar el punto 2.
   Con G1 hay un matiz que conviene no esconder: el plural **sí** puede endurecer el ancla,
   porque `ciclos 14-20` declara de forma explícita siete ciclos y exigir sus siete entradas es
   leer el commit, no inventarlo. Ese endurecimiento solo ocurre con un rango acotado
   (`MAX_CICLOS_DE_UN_RANGO`) y en plural; en singular, y más allá del tope, el parser se
   comporta como antes.
4. La independencia real de actor **no existe dentro de la banda**: solo la puerta humana la da,
   y el proyecto es explícitamente autónomo.

El número de commits sin marcador se imprime en el informe del validador a propósito, para que
el punto ciego se **mida** en cada pasada en lugar de quedar verde.

### Cobertura del ancla

**Iteración 1** — `run_tests.py` -> `test_el_ancla_de_commits_no_depende_del_que_escribe_el_journal()`
monta cuatro árboles temporales con `GIT_DIR` en `tempfile` (**nunca** el historial real): el
parser que debe leer ciclo y no `TASK-`, el residuo de un ciclo comiteado y ausente del journal
(dos errores, uno que nombra `rd_journal.json` y otro el changelog), la unión que no sustituye al
journal, y un `GIT_DIR` que no es repo, que tiene que producir **informe y no excepción**.

**Iteración 2** (el `mutation-auditor` devolvió `FAIL` con 12 supervivientes; estos cuatro tests
son la respuesta a los que sobrevivieron y están registrados en
`openspec/changes/2026-10-01-validator-independent-anchor/tasks.md` T-6):

| Test | Qué sobrevivía | Mutante que muere |
|---|---|---|
| `test_el_ancla_de_commits_no_depende_del_que_escribe_el_journal` (sondas A2 y **A2b**) | El residuo se comprobaba por una **subcadena laxa** (`"rd_journal.json NO lo registra"` + un `047` en cualquier error), así que la diferencia `ciclos_historial - ciclos_journal` invertida seguía verde mientras el validador accuse al revés | `ciclos_historial - ciclos_journal` -> `ciclos_journal - ciclos_historial` |
| `test_el_ancla_se_cablea_en_el_camino_real_del_validador` | `main()` podía **dejar de llamar** al ancla: la suite solo invocaba las funciones privadas, y el criterio A5 era una afirmación, no un test | borrar la línea `_comprobar_ancla_del_changelog(root, errors, ok)` del cuerpo de `main()` |
| `test_el_journal_ilegible_informa_en_vez_de_reventar_el_validador` | `except (ValueError, OSError)` estrechado a `json.JSONDecodeError`: un `PermissionError` salía con traceback | `(ValueError, OSError)` -> `json.JSONDecodeError` |
| `test_el_ancla_de_commits_cae_al_git_dir_por_defecto` | El fallback a `%LOCALAPPDATA%` no lo recorría ninguna sonda: al borrarlo, `None` en el entorno de `subprocess` y `TypeError` | `env.get("GIT_DIR") or expandvars(...)` -> `env.get("GIT_DIR")` |
| `test_un_parser_de_marcadores_roto_no_pasa_en_verde` | La rama `if not ciclos and journal_cycles` no tenía cobertura: desactivarla, o quitarle la condición del journal, sobrevivían | borrar la rama; o `and journal_cycles` |

El primero de esa tabla **acusa el conjunto concreto** (el 047, nunca el 046) y añade el árbol
espejo con journal `{46, 47}` e historial `{46}`, que tiene que dar **cero** errores: es el único
árbol donde acusar es, por construcción, acusar al revés.

`test_el_ancla_se_cablea_en_el_camino_real_del_validador` **no duplica la ruta de validación**: copia
el `validate_docs.py` real a un árbol temporal con el esqueleto de ficheros que `validar()` lee y lo
ejecuta como subproceso, de modo que se ejercitan `main()`, `validar()`, el
`if os.path.exists(CHANGELOG.md)`, la línea de cableado y el `sys.exit` contra un residuo real (un commit del ciclo 999 que el journal
no registra). Sus **dos mitades mutantes**, cada una escrita desde la fuente intacta, exigen que el
residuo desaparezca: el cableado del ancla sustituido por `pass`, y `main()` sin llamar a
`validar(root)` (que declara `0 OK / 0 FAIL` y sale con `0`). El test demuestra su capacidad de
matar en vez de declararla.

**Iteración 3** (el `mutation-auditor` devolvió `FAIL` dos veces seguidas y el Circuit Breaker
replanificó: `tasks.md` T-7). El hallazgo no era un hueco de cobertura sino una **categoría de
bug**: los tests llamaban a las funciones privadas **pasándoles a mano los argumentos**, así que el
cableado que suministra esos argumentos no lo probaba nadie. Medido sobre el producto real, con el
parser de marcadores muerto *y* el cuarto argumento sin pasar, `validate_docs.py` daba
`108 OK / 0 FAIL`: el fix de la iteración 2 era **código muerto en el camino real**. Un test más
por hallazgo no convergía; la iteración 3 converge por construcción:

| Decisión | Qué hace | Por qué converge donde 1 y 2 no |
|---|---|---|
| **D1** — un solo camino | `validar(root) -> (errors, ok)` con los checks 1-7; `main()` solo llama, imprime y hace `sys.exit` | Producto y tests ejecutan la **misma** función, así que "el cableado que nadie prueba" deja de ser una categoría de bug: no hay dos rutas que puedan divergir |
| **D2** — el default se borra | `journal_cycles` pasa a **posicional obligatorio** | Borrar el cuarto argumento deja de ser un cambio de comportamiento y pasa a ser un `TypeError` en la llamada: el validador muere con traceback y muere el test de subproceso que ya existía, **sin escribir una línea de test nueva**. Matiz medido al cerrar el ciclo: **restaurar el default en solitario, con la llamada intacta, es una mutación inerte** y ningún test puede matarla, porque no cambia ningún veredicto. Lo que el default decide es si borrar el argumento es un `TypeError` o un silencio |
| **D3** — un solo camino también para los tests | Todo test contractual se asienta por `validar(root)` o por el subproceso; las privadas dejan de ser **objetivo de tests nuevos** | Una función privada a la que se le pasan los argumentos a mano no prueba nada del producto *mientras su cableado no se pruebe*, y esa era la falsa cobertura. **Matiz medido en el cierre del ciclo #47 (la redacción anterior decía "unitarias-no-contractuales" y era falsa):** `test_el_ancla_de_commits_no_depende_del_que_escribe_el_journal` sí asienta por las privadas y **es contractual de todos modos**, porque es el único guardián de **U1** (unión ≠ sustitución), **P1** (ciclo ≠ tarea: con el parser leyendo `TASK-046` el repo real da `107 OK / 2 FAIL`) y **E1** (ancla ilegible nunca en verde). La regla es *prefiera `validar(root)`*, no *las privadas no importan* |
| **D4** — los escenarios son FILAS | `test_el_ancla_sobre_un_arbol_sintetico_tabla_de_escenarios`: **ocho** escenarios sobre el esqueleto real copiado **una vez** | Medido: 1,7 MB y una copia por test, así que un hallazgo futuro cuesta **una fila**, no un test de 40 líneas con su propia copia. Límite conocido: las filas comparten esqueleto, luego comparten punto ciego — cada fila mide la forma de árbol que construye |

La suite **bajó** de 104 a 103: `test_el_ancla_de_commits_cae_al_git_dir_por_defecto` (S3) y
`test_un_parser_de_marcadores_roto_no_pasa_en_verde` (S4) se fusionaron en la tabla de
escenarios, y sus mutantes mueren ahora por `validar(root)`. El informe de mutación de esta
iteración vive en `openspec/changes/2026-10-01-validator-independent-anchor/mutation-report.md`.

### Cierre del ciclo #47 (el `PASS` del auditor llegó con cinco holes)

Los nueve mutantes del contrato T-7 mueren, uno a uno, y el auditor lo confirmó por atribución.
Lo que vino después no era un fallo del ancla sino **el falso verde del ciclo #15 por otra
puerta**: `missing_entries` y `has_jentry` buscaban el encabezado completo —correcto—, pero
**ninguna sonda construía el árbol donde eso importa**, así que la versión laxo de esas dos
líneas pasaba en verde. Demostrado contra el producto, no por teoría: con `## CYCLE-015` borrado
y la prosa `TASK-015` viva, el código intacto da `[FAIL]` y la versión laxo da **cero fallos**.

Lo grave no era el hueco: era que **el propio código lo advertía a 200 líneas de distancia**.
`validate_docs.py` dice, textual, que buscar el número como subcadena daría falso verde porque
`"015"` sobrevive dentro de `"TASK-015"` (el bug que cerró el ciclo #15), y acto seguido el
mismo fichero no tenía ninguna comprobación de que esa advertencia se cumpliera. Una nota
correcta en el sitio donde se cometió el error no es una defensa.

- **A1 está erradicado donde se produjo y desplazado donde no se buscó.** En `_comprobar_ancla_de_commits`
  el parser roto se acusa (`108 OK / 1 FAIL`, la fila (a) lo mata). En `missing_entries`/`has_jentry`
  el mismo patrón semántico —buscar en vez de exigir— seguía vivo sin sonda. **El ciclo no se
  declara cerrado por esto**: se declara cerrado *donde se midió*.
- **Cerrado con filas, no con tests:** (f) encabezado borrado con el número solo en la
  prosa → mata P2, P3 y H2; (g) `git` que falla una vez con `TimeoutExpired` → mata E2 y E3;
  (h) un asunto en plural que declara un rango → mata G1 y el tope del rango. La suite sigue en
  **103 tests**: un hallazgo nuevo cuesta una fila.
- **G1 cerrado, no solo anotado.** El `s?` del plural era decorativo y sobrevivía a la suite
  entera. Con la semántica de rango escrita arriba (decisión de producto) y la fila (h) como
  prueba, quitar el plural mata la fila, y `MAX_CICLOS_DE_UN_RANGO` impide que un
  `ciclos 1-9999` escrito en cualquier párrafo exija 9999 entradas de changelog. Es el primer
  sitio donde el ancla puede endurecerse: la expansión **solo añade requisitos** que el sujeto
  del commit declara de forma explícita, y nunca relaja los del journal.
- **Punto ciego declarado, no escondido:** la fila (g) mata a E2, pero **no por su propia
  aserción** — E2 sale por el envoltorio compartido `_informe_del_validador_real`, que convierte
  el `Traceback` en `AssertionError`. Si ese envoltorio cambiara, la cobertura de E2 desaparecería
  sin que nadie lo notase. Detalle y medición en `mutation-report.md`.
- **Limitación asumida:** las ocho filas comparten esqueleto y helper, luego comparten punto
  ciego. Una fila mide la forma de árbol que construye, y por eso cada una se documenta con el
  mutante que mata en lugar de solo con su nombre.
- **Dos documentaciones eran falsas y se han corregido:** `sandbox-rules.md` decía "11 de las **46** entradas" del journal
  —el numerador y la lista eran correctos, el denominador había caducado: son **47**— y el informe de mutación fijaba "112 de
  **156** subjects" justo después de declarar que no fija esa cifra, y daba por muerta una fila
  cuya muerte no había medido. Un informe de mutación que afirma algo falso es peor que no
  tenerlo: es la materia prima de la siguiente auditoría.

## Check 8: la Deuda Técnica Conocida exige ancla resoluble (TASK-060, ciclo #49)

La sección `## Deuda Técnica Conocida` de `STATUS.md` **gobierna qué trabajo hace el
bucle** cuando el backlog está vacío: el Paso 1 la lee y prioriza lo que pone ahí.
Hasta el ciclo #48 eso no lo miraba nadie — `validate_docs.py` tenía **0**
coincidencias de la palabra `Deuda` — y la auditoría de aquel ciclo cerró en
**PARTIAL** por una razón medida: 8 de 9 mutaciones sobrevivieron.

### Qué hace y dónde está cableado

`_comprobar_deuda_con_anclas(root, errors, ok)`, llamada desde `validar(root)` entre
el check 7 y el `return`. **Tres posicionales, sin defaults y sin parámetros extra**:
todo se re-deriva de `root`, igual que `_comprobar_recuento_de_tests` (ciclo 27) y
`_comprobar_ancla_del_changelog` (ciclo 47). Un default convertiría un cableado roto
en un `None` silencioso, que es la clase de fallo que D1 cerró en el ciclo #47.

El **check 7** deriva también su reparto: `_reparto_de_tests(root)` cuenta con `ast` las llamadas
`test_*()` del `__main__` antes y desde el marcador estructural
`--- Running Headless UI Tests ---`, y lo compara con lo que declara `STATUS.md`. Va
ahí y no en el 8 porque es la **misma derivación** sobre el mismo fichero, y mezclar
dos derivaciones en un check hace que un rojo no diga *qué* está mal. Si el marcador no
aparece, se acusa el motivo literal: **nunca `0 + 0` en verde**.

### Las cinco fuentes de verdad, todas fuera del panel

| Id | Fuente | Resuelve por |
|---|---|---|
| **S1** | Ruta citada | el fichero **existe** (raíz, `.taskmaster/`, `docs/`, `docs/ai/`, `docs/archive/`). **Sin número de línea** |
| **S2** | Identificador | la cita trae identificador (`fichero:línea identificador`) y el fichero lo contiene |
| **S3** | `TASK-NNN` | existe en `.taskmaster/tasks.json` con `status` legible. **`completed` no basta solo** |
| **S4** | `CYCLE-NNN` | hay entrada en `CHANGELOG.md` o en `rd_journal.json` |
| **S5** | Cifra | la fila declara un número de tests y el derivado con `ast` de `run_tests.py` aparece en ella |

Una fila viva necesita **≥1** fuente resoluble **y ≥1** que no sea una `TASK`
`completed`. Una fila marcada cerrada queda exenta.

### El marcador de cierre, y por qué lleva un `sub`

Una fila está **CERRADA** si, **tras eliminar los tramos de código inline** (`` `...` ``),
contiene el literal `CERRAD` en mayúsculas. El `sub` **es el fix**: la fila que escribe
el criterio lleva el token dentro de comillas invertidas *porque está escribiendo el
criterio*, y sin la limpieza el panel se declararía cerrado a sí mismo. Medido al
nacer: **15 filas, 7 exentas y 8 vivas**; de las 8 vivas solo `STATUS.md:91` se quedaba
sin fuente, y por eso el nacimiento tocó **una** fila (ganó el ancla de
`src/woptimizer/services/pack_service.py`, donde vive `CORRUPTION_ERRORS`).

**Opt-out, no opt-in.** Exigir anclas a las filas cerradas las declararía inválidas
para siempre; y borrar el `CERRADA` de una fila cerrada la convierte en **vigilada**,
que es justo el ataque que importa. En opt-in, borrar la declaración la dejaría *sin
vigilar y en verde*.

### El suelo de gravedad: UNO, y derivado

Si un fichero de S1 sigue declarando `0` para `WOPT_COMMIT_OK` **y** para
`WOPT_NOOP`, el suelo es `ROJO` y una fila viva que se declare `AMARILLO` sale en
rojo. Bajar la gravedad sin cerrar el problema es documentación *fail-open*, que es lo
que la fila del `spawn EPERM` sufrió en el ciclo #48. La gravedad se lee con
**palabras** (`ROJO`/`AMARILLO`/`VERDE`) porque la consola es cp1252 (trampa #16) y un
símbolo en el `print()` tumba el validador entero.

### LIMITACIONES RESIDUALES — lo que este check NO cubre

Se escriben, no se omiten. Todas medidas el 2026-10-02.

1. **S1 solo prueba existencia, no verdad.** Una fila cuya única prueba es S1 pasa
   aunque el fichero exista y diga lo contrario. Solo S2 ata la fila a lo que afirma.
2. **S2 solo mira la atribución EXPLÍCITA** (`fichero:línea identificador`), que es la
   única forma que el panel escribe. Una cita de fichero desnuda se resuelve por
   existencia, y no se intenta emparejarla con los identificadores sueltos de la
   fila: medido, eso produce falsos rojos de una fila a otra.
3. **El suelo de gravedad es UNO.** Solo el código de salida sobrecargado de
   `git_safe_commit.py` deriva gravedad. Una 🔴 rebajada sobre cualquier otro ancla
   sobrevive: derivarla exigiría escribir a mano la política de gravedad, que es la
   misma mentira un nivel más arriba.
4. **La severidad se lee por palabra, no por emoji.** Un panel que bajase la
   severidad cambiando el 🔴 por 🟡 **evade el suelo**. Es un agujero medido, no
   teórico: la mutación M5 sobre la fila del `spawn EPERM` sobrevive.
5. **Las filas cerradas quedan mudas por construcción.** Una fila exenta puede quedar
   enteramente falsa y el check no dice nada.
6. **El corte de la sección es por línea.** Una fila escrita como sub-vineta (`  - `)
   no cuenta como fila, y una sección partida en dos encabezados solo se lee la
   primera.
7. **`docs/index.md` lo vigila el check 7, no el 8**, y de hecho no lo vigila ninguno:
   sigue fuera de la lista de `validate_docs.py`. El 8 certifica que la fila *cita*
   ese fichero, no que ese documento no vuelva a mentir. Queda escrito en la fila
   100 de `STATUS.md` con la misma figura vigente.
8. **Una cita rota solo se acusa cuando es decisiva.** Si la fila tiene otra fuente
   viva, la cita que no resuelve no se denuncia (medido: `profiles.json` es dato de
   usuario y no está en el árbol; acusarlo siempre sería un rojo sin motivo).
9. **La regla de la `TASK` cerrada solo muerde cuando la tarea es la única clase de
   fuente.** Reabrir la fila 94 borrando su `CERRADA` la deja en verde, porque esa
   fila tiene además dos rutas resolubles y su `CYCLE-047`. Para que la regla saltara   haría falta escribir a mano qué citas son "de la historia" y cuáles son "de hoy".
10. **La marca de la fila del criterio es el nombre de la función.** Si se renombra
    `_comprobar_deuda_con_anclas`, la cláusula de autoexención deja de reconocer a la
    fila del criterio hasta que se actualice el literal.

