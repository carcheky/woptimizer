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

**`STATUS.md` no es fuente, y se rechaza por IDENTIDAD: de ruta y de fichero.**
El panel no puede certificarse a sí mismo y el contrato de `TASK-060` lo dice
textual. MEDIDO el 2026-10-02: **cinco** de las quince filas reales (87, 89, 97,
100 y 101) citan `STATUS.md`, y ninguna se queda sin fuente al rechazarlo — las
cinco tienen además rutas y tareas propias, luego el veredicto no cambia ni una
vez. Lo que NO vale es comparar el **nombre escrito** con el string
`"STATUS.md"`: esa igualdad de cadena deja **cuatro** puertas al mismo panel
(`status.md`, `./STATUS.md`, `docs/../STATUS.md` y `.\STATUS.md`) y las cuatro
con `0 FAIL` y 36 anclas. Se compara `os.path.realpath`, que en Windows llama a
`_getfinalpathname` y devuelve el **nombre real** del fichero: las cinco grafías
(colocando también `STATUS.MD`) colapsan al mismo camino y con la misma caja. La
quinta grafía (`STATUS.MD`) ya no colaba ni antes, y no por esta regla: `_RE_RUTA`
exige la extensión en minúsculas, luego no llega a ser una cita.

**Y la identidad de RUTA no basta: hace falta también la de FICHERO.** Un **enlace
duro** al panel comparte `st_dev` y `st_ino` con él y tiene `st_nlink == 2`, pero
su `realpath` es **otro** —un enlace duro no cambia de nombre, luego no hay nada
que canonicalizar—, y con el filtro de ruta pasaba como ancla legítima con
`36` anclas, `3` por contenido y `0 FAIL`, colando S1 y S2 a la vez. Se añade
`_es_el_mismo_fichero`, que compara `(st_dev, st_ino)` **con guardia de
`st_ino != 0`**: sin el guardia, un sistema de ficheros que no dé índice
declararía el panel idéntico a cualquier fichero del árbol, que es peor que el
agujero que cierra. Detalle y alcance en el límite 22.

**`os.path.normcase` se ha QUITADO, y su justificación anterior era falsa en las
dos plataformas.** Decía ser «segunda garantía para sistemas donde `realpath` no
canonicaliza la caja». MEDIDO contra la stdlib: `posixpath.normcase` es
literalmente `return os.fspath(s)`, con docstring *«Has no effect under Posix»*,
luego en POSIX **no hace nada**. Y en Windows `os.path.realpath("status.md")`
devuelve ya `…\STATUS.md`, luego la comparación por ruta resuelta no necesita más.
El mutante C30 sobrevivía porque **medía la irrealidad de la llamada, no una
garantía**: era una segunda garantía que no existía en ninguna plataforma. El
límite 23 recoge la decisión.

### El marcador de cierre: un VEREDICTO, no una palabra

Una fila está **CERRADA** si se cumplen **cinco** cosas a la vez. Las cinco se miden
sobre las 7 exentas reales del panel, que las cumplen **sin tocar una sola fila**:

1. La **palabra** `CERRADA`/`CERRADO` en mayúsculas **fuera de código inline** (el
   `sub` que ya estaba: la fila que escribe el criterio lleva el token dentro de
   comillas invertidas *porque está escribiendo el criterio*, y sin la limpieza el
   panel se declararía cerrado a sí mismo). Con **final de palabra**
   (`\bCERRAD[OA]\b`): MEDIDO que sin el final de palabra el plural y el
   comparativo se colaban — `**CERRADAS todas en TASK-061**` y
   `**a diferencia de las CERRADAS, esta sigue viva**` dejaban la fila 89 EXENTA
   con `0 FAIL` (variantes V3 y V4 del auditor).
2. El marcador está dentro de un **veredicto en negrita** (`**...**`), que es como el
   panel escribe todos sus veredictos. MEDIDO: hasta esta ronda **ninguna** fila de
   la tabla comprobaba esta condición, y por eso el mutante que la borra
   (`findall` → `[texto]`) sobrevivía con la suite entera en verde.
3. La fila nombra un **id trazable** (`TASK-NNN` o `CYCLE-NNN`) que **existe** en
   `.taskmaster/tasks.json`, en un `CHANGELOG.md` o en el journal.
4. Ni el **veredicto** ni la **prosa** de la fila **niegan** el cierre.
5. Y el id que cierra la fila está **CERRADO**, no pendiente: una `TASK` con
   `status == completed` o un `CYCLE` con entrada en uno de los **dos changelogs**.
   MEDIDO que las 7 exentas la cumplen sin tocar una fila — 87 `TASK-055`/
   `CYCLE-045`, 90 `TASK-057`, 93 `TASK-031`/`TASK-060`, 94 `TASK-057`/`CYCLE-026`/
   `CYCLE-047`, 96 y 97 `TASK-037`/`CYCLE-027`, 99 `TASK-054`/`CYCLE-044` — y que
   con ella puesta el panel intacto sigue en `7 exenta(s) / 8 viva(s) / 35` anclas y
   `0 FAIL`. Un ciclo se **traza** en cuanto se nombra y se **cierra** cuando publica
   su entrada: exigir solo lo primero es lo que dejaba pasar el ataque (límite 19).

**Por qué cinco y no una.** Medido el 2026-10-02 con el marcador de una sola palabra:
la fila 89 —la 🔴 del `spawn EPERM`— se **eximía a sí misma** con cualquier frase
normal que hablara de cierre («y esta fila NO está CERRADA todavía», «(marcada
\*CERRAD\*)» al final), y el validador respondía `115 OK / 0 FAIL`. Una palabra suelta
no es un veredicto.

**La quinta se pregunta DESPUÉS de la autoexención, y eso es una decisión, no un
detalle.** La fila que escribe el criterio no puede declararse cerrada, y con
`CYCLE`/`TASK` **pendiente** en su veredicto la quinta la declararía VIVA: el
mensaje pasaría de «se ha autoeximido» a «VIVA sin ancla resoluble» y el guard que
vigila al vigilante se apagaría a sí mismo. Por eso `_porta_el_marcador_de_cierre`
(las condiciones 1, 2 y 4) se evalúa **por separado** y la autoexención se pregunta
**antes**: «¿esta fila se ha eximido a sí misma?» lo decide la FORMA —que nombre
este check—, no si el trabajo que cita ya estaba hecho. MEDIDO: con el orden
invertido, el escenario (f2) de la suite muere.

**La negación se evalúa sin ventana cortable por puntuación, y en la prosa.**
La regla vieja era `\b(?:NO|NUNCA|JAMAS)\b[^.;:!?]{0,40}CERRAD`: una ventana de
40 caracteres **anteriores** al marcador, cortable por `;` `:` `.`. MEDIDO que deja
pasar cuatro frases más, todas sobre la 89 y todas con `0 FAIL`: la negación
**después** del marcador (`**CERRADA, aunque NO lo parezca (TASK-061)**`), la
negación **fuera** de la negrita (`**CERRADA**. NO lo esta: …`), la negación
cortada por un punto y coma (`**NO: CERRADA en TASK-061**`) y la comparativa
indirecta que el regex no puede conocer. Ahora la negación se busca **en el
veredicto que lleva el marcador y en la prosa**, con la forma `\b(?:NO|NUNCA|JAMAS)\b`
y sin ventana.

**Por qué NO en la fila entera, que es lo que la frase "en la fila" sugiere.**
MEDIDO: la fila 87 (exenta de verdad) lleva **dos** `NO` en mayúsculas dentro de
**otro** veredicto — `**NO lo importaba y NO estaba muerto**` — que es un aserto
sobre el fichero archivado, no sobre el cierre de la fila. Con la negación
buscada en toda la fila, las 7 exentas pasan a **6** y la 87 tendría que exigir
ancla siendo un registro histórico cerrado. La fila del panel es un **catálogo
de asertos**, y la negación de un aserto no niega el otro: prosa + veredicto del
marcador es lo que separa los dos. Lo que queda es un residuo declarado (límite
20): una negación escondida en *otro* veredicto no cuenta.

**Y lo que esa elección cuesta, medido, que antes no estaba escrito en ninguna
parte.** La regla mira la **prosa de la fila entera**, y en castellano `NO` en
prosa es una conjunción corriente. MEDIDO: añadir ` NO es un aserto de cierre.`
a la fila 87 la deja de estar exenta y el panel pasa a `6 exenta(s) /
9 viva(s)` y `39` anclas. Sigue en `0 FAIL` —la 87 demuestra su ancla—, luego no es
un rojo: es una **pérdida de exención**, y una fila de verdad cerrada tiene que
volver a probar su ancla porque escribió «NO» en otra frase. Es el precio de haber
matado V2, y por eso el límite 21.

**Y lo que la caja cuesta, que es la otra mitad del mismo aserto.** El predicado
es **sensible a caja** a propósito: se aplicó `re.IGNORECASE` para medirlo y se
**quitó**, porque lleva las **siete** exentas reales a **cero** y pone el repo en
`1 FAIL`. No es un descuido de la regla: en castellano `no` y `nunca` son prosa
ordinaria, y hay negaciones de cierre **de verdad** que no niegan el cierre — la 93
dice «**CERRADA en la cola, no en el cuerpo**» y la 96 «**CERRADA en
CYCLE-027 (TASK-037) — guardas que no guardaban**». No hay forma que separe
`no en el cuerpo` de `nunca se resolvio`. La caja es la **forma**, por el mismo
argumento que ya fija el punto 1 para `CERRADA`/`cerrada` y el límite 18. Lo que
de esa puerta **sí** muere, por la quinta condición, es el ataque que nombra
trabajo **pendiente**; lo que queda vivo es el caso «id ya cerrado», y va
declarado con el límite 19. Detalle en el límite 21.

Las cinco fallan **abierto**: lo que no demuestra su cierre queda **VIVA** y tiene que
demostrar su ancla, que es la única dirección en la que un validador puede equivocarse
sin dejar de vigilar nada. Medido al nacer y después del arreglo: **15 filas, 7 exentas
y 8 vivas**, las mismas de antes; de las 8 vivas solo `STATUS.md:91` se quedaba sin
fuente, y por eso el nacimiento tocó **una** fila (ganó el ancla de
`src/woptimizer/services/pack_service.py`, donde vive `CORRUPTION_ERRORS`).

**Opt-out, no opt-in.** Exigir anclas a las filas cerradas las declararía inválidas
para siempre; y borrar el `CERRADA` de una fila cerrada la convierte en **vigilada**,
que es justo el ataque que importa. En opt-in, borrar la declaración la dejaría *sin
vigilar y en verde*.

### El suelo de gravedad: UNO, y derivado

Si un fichero de S1 sigue **declarando** `0` para `WOPT_COMMIT_OK` **y** para
`WOPT_NOOP`, el suelo es `ROJO` y una fila viva que se declare `AMARILLO` sale en
rojo. Bajar la gravedad sin cerrar el problema es documentación *fail-open*, que es lo
que la fila del `spawn EPERM` sufrió en el ciclo #48.

**«Declarar» es una forma, no una mención.** La línea que **empieza** por el token `0`
seguido del nombre es la que declara; así la escribe `.taskmaster/git_safe_commit.py:13-14`.
Medido el 2026-10-02 con el predicado viejo («un `0` antes del nombre en cualquier
línea»): casaba en `validate_docs.py` (su propio docstring), en `run_tests.py` (una
cadena de fixture), en `.taskmaster/tasks.json` y en el propio `STATUS.md`. Una tabla
de markdown que **tabula** el contrato (`docs/ai/sandbox-rules.md:55-56`) lo documenta,
no lo declara.

**La gravedad se lee del emoji, no de la palabra.** El panel se expresa en 🔴🟡🟢 y el
validador leía `ROJO`/`AMARILLO`/`VERDE`: medido el 2026-10-02, **14 de las 15 filas
no tienen ni una palabra** de gravedad, y la única que la tiene (la 98) la usa para el
*color* de un diagnóstico de UI. El suelo **no se ejecutaba nunca**. El emoji se mapea
a la palabra **al leer**, y el informe sigue siendo ASCII puro porque la consola es
cp1252 (trampa #16).

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
4. **El suelo no tiene fila víctima hoy, y eso es un agujero medido.** El suelo se
   dispara cuando una fila declara **por debajo** de su suelo. MEDIDO el 2026-10-02
   con `_gravedad_declarada` fila a fila: de las quince filas, **cinco no declaran
   ninguna** (88, 91, 92, 95 y 97) y las otras diez sí — **ocho declaran 🔴**
   (87, 89, 90, 93, 94, 96, 98 y 99) y **dos 🟡** (100 y 101). De las **vivas**,
   las que declaran 🔴 son la **89 y la 98**, y como el suelo de ambas es `ROJO`,
   ninguna está por debajo: rebajar la 89 a 🟡 sale en rojo (P7), rebajar la 98
   también. La **88 no declara ninguna gravedad** —`_gravedad_declarada` devuelve
   `None` porque no tiene glifo—, así que su P6 no «rebaja» nada: **añade** una
   gravedad por debajo de un suelo que ya era `ROJO`, y por eso también muere.
   *(La versión anterior de este límite decía «de las quince filas, la 89 es la
   única que declara 🔴». La conclusión —el suelo no tiene víctima— era correcta;
   la medición que la sostenía era falsa, y la misma frase falsa estaba copiada
   en el comentario de `_RE_GRAVEDAD` y en el §0 del informe de mutación. Se
   corrigen los tres sitios.)* Pero **neutralizar el suelo entero deja el panel en
   verde**, porque ninguna fila viva declara una gravedad por debajo de la suya.
   No es un agujero teórico: es la razón por la que este límite se escribe y no se
   omite. Y lo que agrava el agujero es **doble**, no uno: **tampoco hay fila
   víctima con un glifo fuera del mapa de tres** (límite 16) **ni con una gravedad
   histórica antes de la de hoy** (límite 15). El suelo tiene hoy **cero** filas
   que puedan delatarlo.
5. **Un cierre falsificado en la forma del panel sigue eximiendo — y es el MISMO
   residuo del límite 19, no uno aparte.** El id que cierra la fila se busca
   **en la fila**, no solo en el veredicto. Consecuencia medida: añadir
   `**CERRADA en CYCLE-999**` a una fila que **ya cita ids resolubles** la exime,
   y la quinta condición del límite 19 **no lo cierra**.

   **La medición, con su fila y sus cifras, y CORREGIDA respecto a la version
   anterior de este limite (que citaba la 89 y `22` anclas y no reproducia).**
   MEDIDO el 2026-10-02 en la ronda 5 del ciclo #49, sobre el panel de hoy:
   - **La fila 89 NO se exime** y **no puede** servir de ejemplo. Su veredicto
     «🔴 VUELTA A 🔴 Y NO SE CIERRA: bajarla a 🟡 sin cerrar el problema es
     documentación *fail-open*…» lleva un `NO` en mayusculas **dentro** de la
     negrita, y la regla de negacion rechaza el marcador de cualquier veredicto
     asi antes de mirar ningun id. MEDIDO: `_RE_CERRADA` encuentra el marcador
     anadido y `_RE_NEGACION_DEL_CIERRE` lo rechaza en ese mismo veredicto, luego
     anadirle ` - **CERRADA en CYCLE-999**` deja la 89 VIVA y el panel igual:
     `7 exenta(s) / 8 viva(s) / 35` anclas, `0 FAIL`. No es que el `CYCLE-999`
     no cerrara: es que **el veredicto que lo lleva no pasa la regla de negacion**.
   - **La fila 95 SI se exime**, y ahi esta el mecanismo de verdad: `8 exenta(s)`,
     `7 viva(s)`, `35` anclas, `0 FAIL`. Nombra `TASK-057` (`completed`) y
     `TASK-059` (`pending`), luego el `CYCLE-999` —que no existe en ningun
     registro— **hereda el cierre de un id que ya estaba cerrado**.
   - **La linea base de anclas es `35`, no `22`.** El `22` de la version
     anterior de este limite era de una medicion mas antigua; hoy el panel da
     `35` anclas de ruta resuelta y `2` por contenido.

   No es una puerta nueva: es el residuo del límite 19 con otro disfraz, porque
   el veredicto `CYCLE-999` no aporta nada y la fila se cerraba igual. Lo que se
   midió y se descartó como regla es **«el id tiene que estar FUERA del
   veredicto»**, que es lo que este apartado defendía antes. MEDIDO que atar el
   id al veredicto **cambia qué** filas se cerrarían y no las separa del ataque:
   las filas **87, 96 y 97 no escriben ningún id fuera de su veredicto** y están
   CERRADAS de verdad, luego exigírselo las reabre sin motivo mientras el ataque
   sigue entrando. La condición que sí separa es la del **estado** (límite 19).

   **Y con la ronda 5 el residuo declarado es MAS ANCHO de lo que decía aquí.**
   Antes se declaraba solo «nombrar un id **ya cerrado**», que es el caso de la
   95 y el del escenario (y). MEDIDO que hay un segundo caso, más grande: un
   **`CYCLE` que NUNCA EXISTIÓ** y al que se le publica la entrada. Se cerró el
   de subcadena (`CYCLE-04`.counta dentro de `CYCLE-045`), pero **`CYCLE-999` +
   una línea `## [CYCLE-999]` escrita en el changelog sigue eximiendo**, porque
   publicar la entrada de un ciclo **es** el acto legítimo de cerrarlo y un
   validador que lo negara no podría cerrar nunca un ciclo. Ese residuo no es de
   **forma**, es de **acto**: no lo cierra ninguna regla de forma, y por eso se
   declara entero aquí en vez de declararse solo la mitad.
6. **Las filas cerradas quedan mudas por construcción.** Una fila exenta puede quedar
   enteramente falsa y el check no dice nada.
7. **El corte de la sección es por línea.** Una fila escrita como sub-vineta (`  - `)
   no cuenta como fila, y una sección partida en dos encabezados solo se lee la
   primera.
8. **`docs/index.md` lo vigila el check 7, no el 8**, y de hecho no lo vigila ninguno:
   sigue fuera de la lista de `validate_docs.py`. El 8 certifica que la fila *cita*
   ese fichero, no que ese documento no vuelva a mentir. Queda escrito en la fila
   100 de `STATUS.md` con la misma figura vigente.
9. **Una cita rota solo se acusa cuando es decisiva.** Si la fila tiene otra fuente
   viva, la cita que no resuelve no se denuncia (medido: `profiles.json` es dato de
   usuario y no está en el árbol; acusarlo siempre sería un rojo sin motivo).
10. **La regla de la `TASK` cerrada solo muerde cuando la tarea es la única clase de
    fuente.** Reabrir la fila 94 borrando su `CERRADA` la deja en verde, porque esa
    fila tiene además dos rutas resolubles y su `CYCLE-047`. Para que la regla saltara
    haría falta escribir a mano qué citas son "de la historia" y cuáles son "de hoy".
11. **La marca de la fila del criterio es el nombre de la función.** Si se renombra
    `_comprobar_deuda_con_anclas`, la cláusula de autoexención deja de reconocer a la
    fila del criterio hasta que se actualice el literal.
12. **S5 comprueba la cifra que la fila DECLARA, no la que CITA, y esa distinción
    es de FORMA, no de sustancia.** Una cifra `N tests` es una **cita** cuando va
    dentro de código inline (`docs/index.md` declara «96 tests») **o cuando su
    frase cita un fichero**; es una **declaración** cuando va suelta. Solo la
    declaración se contrasta con el derivado por `ast`. MEDIDO el 2026-10-02: la
    misma mentira en las dos formas se comporta distinto — una fila nueva que dice
    «segun `run_tests.py` la suite tiene 42 tests» sale con `0 FAIL` (límite 17),
    y la misma cifra en su propia frase, con la cita en la frase anterior, sale en
    rojo.
    **Por qué no se comprueba la cita contra el documento que la fila acusa.** No
    porque sea físicamente imposible, sino porque esa fila **existe para acusar a
    ese documento de mentir**: la 100 documenta que `docs/index.md` declaraba una
    cifra desfasada, y validar esa cita contra el contenido *actual* de ese mismo
    documento la haría imposible de redactar. Es una decisión de alcance, y por
    eso se declara como tal en vez de disfrazarse de límite físico.
13. **El panel se certifica a sí mismo por la cifra, si la cifra es la única fuente.**
    Con el rechazo de `STATUS.md` como ancla, una fila cuya única verdad es el propio
    panel sale en rojo. Lo que **no** se comprueba es que la cifra que el panel
    declara como verdad la diga también el código: el check deriva `ast` y compara,
    pero no puede saber qué cifra *quiso* escribir el panel.
14. **Acoplamiento inverso del esqueleto de tests.** `_copiar_el_esqueleto_del_validador`
    copia `src/` y `.taskmaster/tasks.json` para que las filas del panel resuelvan. Es
    **portante** (sin `src/` los tests que cuentan `len(errors)` mueren), y crea el
    acoplamiento de que un panel roto hace morir
    `test_el_journal_ilegible_informa_en_vez_de_reventar_el_validador`, cuyo sujeto es
    el journal: **falla ruido, no verde**, pero un `len(errors) == 1` es un conteo
    exacto atado al panel. Queda declarado para que el próximo que lo lea no lo tome
    por un fallo del journal.
15. **La gravedad que cuenta es la PRIMERA del texto, y una gravedad histórica la
    tapa.** `_gravedad_declarada` devuelve el primer `ROJO|AMARILLO|VERDE` que
    aparece tras mapear los glifos. MEDIDO el 2026-10-02: poner un 🟡 **después**
    de un 🔴 que la fila ya traía sale con `0 FAIL` y `35` anclas (mutante G2a'),
    porque el 🔴 histórico gana y la rebaja de hoy no se ve. Sin victimas, esto no
    es un agujero explotable hoy (límite 4) y con ella lo sería: por eso se escribe
    y no se arregla — arreglarlo exigiría decidir qué emoji manda, que es política
    de gravedad escrita a mano, el mismo nivel de mentira que el suelo único.
16. **Un glifo fuera del mapa de tres no es una gravedad.** El mapa es 🔴🟡🟢; un
    🟠 (u otro) deja `gravedad = None` y el suelo **nunca** se dispara. MEDIDO el
    2026-10-02 con la fila 100 (mutante G2b'): `0 FAIL` y `35` anclas, y el emoji
    sigue ahí a la vista. La fila 100 declara además 🟡 de verdad, luego hoy es un
    no-op; lo que se declara es la clase de fallo: **cualquier glifo que no sea
    uno de los tres se le como si no hubiera gravedad**.
17. **Cualquier fila puede mentir sobre el recuento y autoeximirse mencionando un
    fichero en la MISMA frase.** MEDIDO el 2026-10-02: una fila nueva que dice
    «segun `run_tests.py` la suite tiene 42 tests» sale con `0 FAIL` y `36` anclas
    (mutante N1a), y la misma cifra con la cita en la frase **anterior** sí sale en
    rojo (N1b, `1 FAIL`). La atribución por forma es lo que separa los dos casos, y
    es también lo que abre esta puerta: basta mover la cita a la frase de la
    mentira para que el guard no la vea. Es límite 12 aplicado a una fila nueva, no
    a la 100, y por eso se declara aparte.
18. **El marcador es un token EN MAYÚSCULAS, y la MAYÚSULA es forma, no estilo.**
    Decidido y escrito: `CERRADA:` → `cerrada:` en la fila 90 deja el panel en
    `6 exenta(s) / 9 viva(s)` y salta **un** `FAIL`, el de esa misma fila 90 por
    «su UNICA fuente es una TAREA YA CERRADA». *(La versión anterior decía «pone
    las **siete** exentas en rojo»: es falso. MEDIDO el 2026-10-02 — el rojo es
    real y el número no; lo que cambia no es que las otras seis cambien de estado,
    es que la 90 se reabre y su `TASK-057` cerrado se queda como única fuente.)* Ese rojo
    es el precio de que la palabra suelta en prosa no cierre nada (es el mismo
    argumento que declara el código de salida por la línea que empieza por `0`).
    MEDIDO y **aceptado**: el escenario (s) de la suite fija esta decisión.
    Consecuencia: un descuido de caja en el veredicto de una fila cerrada la
    reabre de golpe, y no es un rojo que un guard pueda contener.
    **La misma regla se extiende a la NEGACIÓN, y es lo que hace que un ataque en
    minúscula no se vea**: ver el límite 21.
19. **~~El id trazable puede proceder del propio veredicto de cierre, y eso ya no
    distingue la fila real del ataque.~~ CERRADO en la ronda de cierre del ciclo
    #49. La frase de arriba era el límite **más ancho que el agujero real**, y su
    propia tesis —«no hay regla que separe la fila 87 del ataque sin poner el repo
    en rojo»— era **falsa**: el eje que separa una de otra no es *dentro/fuera del
    veredicto* sino **cerrado/pendiente**. MEDIDO que los ids de las 7 exentas
    están **todos dentro** del veredicto (87 → `TASK-055`/`CYCLE-045`,
    99 → `TASK-054`/`CYCLE-044`, 96 y 97 → `TASK-037`/`CYCLE-027`), luego atar el
    id al veredicto no las separa de nada; y MEDIDO que los **dos únicos ids
    `pending` del tablero** son `TASK-059` y `TASK-061`, que son exactamente los
    que usaba el ataque. `_esta_cerrada` tiene ahora una **quinta condición**: el
    id que cierra la fila tiene que estar **cerrado** —una `TASK` con
    `status == completed`, un `CYCLE` con entrada en uno de los **dos changelogs**—,
    no solo existir. MEDIDO con la condición puesta y el **panel intacto**:
    `7 exenta(s) / 8 viva(s) / 35` anclas y `0 FAIL`, **sin tocar ni una fila**;
    el ataque declarado (`**CERRADA en TASK-059**` y con `TASK-061`) pasa de
    `8/7/33, 0 FAIL` a `7/8/35, 0 FAIL`, y el mismo ataque con su negación en
    minúscula («nunca se resolvio») también.
    **El residuo que sí es real, y hay que declararlo ENTERO, no por la mitad.**
    MEDIDO el 2026-10-02 (ronda 5) que el agujero es **más ancho** que «nombrar un
    id ya cerrado», y declarar solo eso es reincidir en lo que este ciclo lleva
    tres rondas corrigiendo en su propia documentación. Son **DOS** casos, y los dos
    son de **acto**, no de forma:
    1. **Nombrar un id ya cerrado** sobrevive, y sobrevive por la misma puerta
       (`**CERRADA en TASK-055**` o `**CERRADA en CYCLE-045**` en la fila 88 dan
       `8/7/33, 0 FAIL`). El escenario (y) de la suite lo archiva como control
       negativo para que el próximo no lo lea como un bug sin explicar. No es
       cerrable con una regla de forma: una fila que nombra trabajo de verdad
       terminado es indistinguible de una fila real cerrada.
    2. **Nombrar un `CYCLE` que NUNCA EXISTIÓ y publicarle la entrada.** MEDIDO que
       `**CERRADA en CYCLE-999**` más una línea `## [CYCLE-999]` escrita en
       `.taskmaster/CHANGELOG.md` da `8/7/33, 0 FAIL`. **La ronda 5 cerró la
       mitad de este caso y no la otra**: el `CYCLE` se resolví **por la FORMA de
       su entrada** y con el **id literal completo**, con lo que mueren `CYCLE-04`
       (que estaba dentro de `CYCLE-045`), `CYCLE-0`, `CYCLE-09` y `CYCLE-999`
       sin entrada; pero en cuanto la entrada se **publica**, el ciclo queda
       cerrado, y **no puede ser de otra forma**: publicar la entrada de un ciclo
       **es** el acto legítimo de cerrarlo, y un validador que lo negara no podría
       cerrar nunca un ciclo. El residuo que queda es por tanto **intranscendible
       con reglas de forma** y se declara entero. Detalle y medición en el
       docstring de `_ciclos_cerrados`.
    Lo que sí semidió y **no** se puede cerrar así es la distinción *dentro/fuera
    del veredicto*, porque no separa nada (ver arriba). El daño que el auditor
    atribuía al suelo **no ocurre en la 88**: esa fila no declara ninguna
    gravedad (`_gravedad_declarada` → `None`), luego su suelo no podía dispararse
    ni antes ni después. Lo que se apaga es la fila entera.
    **Lo que sí costó el arreglo, y va en su propia línea (límite 21):** la
    condición 5 no se puede preguntar antes que la autoexención sin romper el
    escenario (f2), y se resuelve midiendo la autoexención **por la forma** de la
    fila, no por el estado de su id.
20. **Una negación escondida en OTRO veredicto no cuenta.** La regla de negación
    mira el veredicto del marcador y la prosa de la fila, no los demás veredictos
    (límite del apartado anterior, y la razón medida es la fila 87). MEDIDO: una
    fila cuyo veredicto de cierre es `**CERRADA en TASK-059**` y que dice
    `**NO lo esta**` en otro veredicto se exime. Se declara porque la regla que se
    eligió para no romper la 87 abre esta puerta a cambio.
21. **Un `NO` AJENO en la prosa reabre una fila realmente cerrada, y es el precio
    de matar V2.** La regla de negación mira la **prosa** de la fila entera, y en
    castellano `NO` en prosa es una conjunción corriente. MEDIDO el 2026-10-02:
    añadir ` NO es un aserto de cierre.` a la fila 87 la deja de estar exenta y el
    panel pasa a `6 exenta(s) / 9 viva(s)` y `39` anclas. Sigue en `0 FAIL` —la 87
    tiene rutas y tareas propias y las demuestra—, luego **no es un rojo**, es una
    **pérdida de exención**: una fila de verdad cerrada tiene que volver a probar
    su ancla porque escribió «NO» en otra frase. Ese es el precio, y su forma
    correcta es la del límite 18: en la prosa, la MAYÚSULA es la **forma** del
    aserto deliberado y la minúscula no cuenta; una fila real no lleva `NO` en
    mayúsculas por casualidad.
    **Y el hermano pequeño de este residuo, que NO se arregla y se declara con
    él:** una negación en **minúscula** dentro del veredicto de cierre tampoco se
    ve (`**CERRADA en TASK-055, nunca se resolvio**` se exime). Se aplicó
    `re.IGNORECASE` a propósito para medirlo y se **quitó**: lleva las **siete**
    exentas reales a **cero** y pone el repo en `1 FAIL`, porque hay negaciones de
    cierre escritas de verdad que no lo son — la 93 dice «**CERRADA en la cola, no
    en el cuerpo**» y la 96 «**CERRADA en CYCLE-027 (TASK-037) — guardas que no
    guardaban**», y ahí la negación contrasta dos cosas en vez de negar el cierre.
    No hay forma que separe `no en el cuerpo` de `nunca se resolvio`: las dos son
    negación en minúscula sobre el mismo marcador. El escenario (n2) de la suite
    archiva el residuo como control negativo y **falla en rojo** a cualquiera que
    vuelva a aplicar `re.IGNORECASE`: ese intento tiene que encarar las siete
    filas reales antes de poder pasar, que es justo lo que se le pedia.
    MEDIDO que el ataque que el auditor midió con esta puerta —`— **CERRADA en
    TASK-059, nunca se resolvio**`, que nombra trabajo **pendiente**— muere igual
    con la quinta condición del límite 19: son **el mismo ataque por la misma
    puerta**, y lo que queda vivo es solo el caso «id ya cerrado» del límite 19.
22. **El enlace DURO al panel era una puerta real, y está CERRADA.** El filtro por
    ruta resuelta daba el filtro del panel por cerrado, y un **enlace duro** lo
    esquivaba entero: `docs/panel_hard.md` creado con `os.link` sobre
    `STATUS.md` comparte `st_dev` y `st_ino` con el panel y tiene `st_nlink == 2`,
    pero su `realpath` es **otro**, luego pasaba el filtro como ancla legítima con
    `36` anclas, `3` por contenido y `0 FAIL` de Deuda — **colando S1 y S2 a la
    vez**. MEDIDO también que un enlace **simbólico** y una **junction** sí los
    cierra `realpath`, y que `STATUS.md.` muere por `_RE_RUTA`, no por la
    identidad. La causa es que un enlace duro **no cambia de nombre**, luego no hay
    ruta que canonicalizar: el filtro se ha ampliado con `_es_el_mismo_fichero`,
    que compara `(st_dev, st_ino)` con guardia de `st_ino != 0` — sin el guardia,
    un `st_ino` de `0` declararía el panel idéntico a cualquier fichero del árbol,
    que es peor que el agujero que cierra. MEDIDO que con el arreglo el ataque
    pasa de `0 FAIL` y `36` anclas a **2 FAIL** y `35`. El escenario (h2) de la
    suite lo cubre. Lo que **no** se ha hecho es defenderse de quien ya tiene
    permiso de escritura en el árbol: eso es otro problema, con otra respuesta, y
    se declara aquí solo para que conste el **alcance** de lo cerrado —una acción
    deliberada en el árbol, no un fichero que aparezca solo—.
23. **`os.path.normcase` se ha quitado de la comparación del panel, y su
    justificación anterior era FALSA en las dos plataformas.** Decía ser «segunda
    garantía para los sistemas donde `realpath` no canonicaliza la caja». MEDIDO
    contra la stdlib: `posixpath.normcase` es literalmente `return os.fspath(s)` y
    su docstring dice literalmente *«Has no effect under Posix»*, luego en POSIX
    **no hace nada** y no puede ser una garantía ahí. Y MEDIDO en Windows que
    `os.path.realpath("status.md")` devuelve ya `…\STATUS.md`, luego devuelve el
    nombre REAL y con la caja real: la comparación por ruta resuelta no necesita
    nada más. No era «redundante en Windows»: era **inerte en todas partes**, y lo
    que se ha quitado no era una garantía, era una llamada que anunciaba una.
    Mutante C30: deja de existir como tal, porque el código al que mutaba ya no
    está. En su lugar la identidad se ha ampliado por `(st_dev, st_ino)` (límite
    22), que es donde estaba de verdad el agujero.
24. **La rama del journal de `_ciclos_de_la_fila` es INERTE en este repo, y se
    declara en vez de eliminarse porque el escenario (c3) la ejecuta de verdad.**
    MEDIDO el 2026-10-02 sobre el journal real: **cero** literales `CYCLE-NNN` y
    **49** entradas con `"cycle": <int>` (los ciclos van del `1` al `49`, todos
    enteros). `_RE_CICLOS` busca la forma `CYCLE-\d+`, luego la rama del journal
    **no puede casar con nada** con el journal que este repo escribe hoy. No es un
    agujero: es código que solo un árbol sintético ejecuta, y su valor es
    justo que (c3) sea el ÚNICO escenario que mide esa rama. Por eso se declara
    en lugar de borrarse: borrarla sería borrar el escenario que la mide. Lo que
    **no** se declara es que la rama sirva para el journal real, porque no sirve.
25. **La guardia `st_ino != 0` de `_es_el_mismo_fichero` no tiene test ni
    víctima, y eso se dice con su verdad.** En NTFS `st_ino` vale un entero de
    16 dígitos (MEDIDO: `3940649674545953` para `STATUS.md` en esta medición), luego
    **nunca es `0` aquí** y **quitar la guardia no muere nada**: es una mutación
    inerte en esta plataforma. La guardia **es correcta** en un sistema de
    ficheros sin índice, donde `st_ino` vale `0` para todo y `0 == 0` declararía
    el panel idéntico a cualquier fichero del árbol (límite 22), pero **nadie la
    ha medido y por tanto nadie puede romperla aquí**. Se declara como cobertura
    ausente, no como bug: es un residuo de portabilidad sin banco.
26. **La fila 101 del panel tiene un número IMPAR de `**` y eso HOY decide si su
    marcador se ve.** MEDIDO: la fila 101 cuenta **117** asteriscos (impar) y
    `_RE_NEGRITA` extrae **58** veredictos; al añadirle un veredicto de cierre
    bien formado, el recuento pasa a 59 y **el veredicto nuevo NO está entre los
    extraídos**: `**CERRADA en TASK-001**` añadido a la fila se queda **invisible**
    para el guard. MEDIDO el contraste que lo demuestra: con los 117 asteriscos
    impares `_porta_el_marcador_de_cierre` devuelve `False` y con los 120 pares
    (cerrando el desbalance) devuelve `True`. Es decir, **hoy la fila 101 está
    protegida por un accidente de formato del Markdown, no por la regla**; el
    escenario (f2) usa una fila sintética **balanceada**, luego el comportamiento
    real de la fila del criterio **no estaba cubierto**. La ronda 5 lo cubre con el
    escenario (m2), que pone el marcador **en la prosa** (independiente del
    balance de asteriscos) y exige que la fila del criterio se acuse igual. **No se
    corrige el desbalance de la 101**: es una fila de Deuda y su regla es *solo
    añadir, nunca reescribir*. Se declara el accidente y se cubre por donde el
    Markdown no decide.

