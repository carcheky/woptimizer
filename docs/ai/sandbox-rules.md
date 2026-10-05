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
| `0` | Repo sano (solo diagnóstico) | `--verify` y el par `GIT_DIR`/`GIT_WORK_TREE` es utilizable | `WOPT_REPO_OK <git_dir>` |
| `1` | Fallo de una operación de git | `git status`, `git add -A` o `git commit` con rc != 0, o excepción al lanzarlos | `WOPT_FAIL <operacion> <detalle>` |
| `2` | Uso incorrecto | sin mensaje, mensaje vacío, más de un posicional, flag desconocido, **mensaje sin identificador de ciclo ni de tarea**, **o llega una sola de las dos variables `GIT_DIR`/`GIT_WORK_TREE`**, **o la cabecera pasa de 120 caracteres**, **o la cabecera incumple `type-empty`/`type-enum`/`type-case`/`subject-empty`/`subject-case`** | `WOPT_USAGE <detalle>` / `WOPT_USAGE ancla-mensaje <detalle>` / `WOPT_USAGE paridad-git <detalle>` / `WOPT_USAGE cabecera-larga <que se espera> <medicion>` / `WOPT_USAGE cabecera-regla <regla> <detalle>` |
| `3` | Repositorio no verificable | `GIT_DIR` inexistente, no es un git dir, `GIT_WORK_TREE` que no es un directorio, `HEAD` no resuelve, `is-inside-work-tree` != `true`, o `git` no ejecutable | `WOPT_REPO_INVALIDO <detalle>` |

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
7. **Precedencia de `GIT_DIR` y `GIT_WORK_TREE`, y PARIDAD entre las dos (TASK-061).** Si el
   entorno ya trae cualquiera de las dos, se respeta y no se sobrescribe (es la vía documentada
   arriba y además el hook que permite tests herméticos). Si no, se usa el par por defecto:
   `%LOCALAPPDATA%\woptimizer_git\.git` + el árbol del proyecto. La validación se aplica igual en
   ambos casos. **Y el par llega entero o no llega:** si llega **una sola** de las dos —`GIT_DIR`
   sin `GIT_WORK_TREE`, o al revés— se rechaza con el **código 2** y `WOPT_USAGE paridad-git`, sin
   escribir nada, también en `--verify`.

   *Por qué la hermeticidad es de repo **y** de árbol.* Medido el 2026-10-02 (ciclo #48) y corregido
   el 2026-10-04: «tests herméticos» era media verdad, porque `get_env()` respetaba el `GIT_DIR`
   del entorno pero **imponía `GIT_WORK_TREE = REPO_ROOT` sin condición**, de modo que una sonda
   con un `GIT_DIR` desechable hacía `add -A` y `commit` **sobre el árbol de trabajo real**: se
   midió un `GIT_DIR` temporal que stageó y commiteó el árbol del duño dentro del repo temporal
   (el historial real quedó intacto, porque `GIT_DIR` era el temporal). La contaminación ocurrió
   dos veces en este repo (`STATUS.md:23`).

   *Y ahora el árbol se valida además como DIRECTORIO.* Un `GIT_WORK_TREE` que existe pero no es
   un directorio tiene que salir con `3` y el motivo del **pre-chequeo**
   (`GIT_WORK_TREE no existe o no es un directorio`), no con el `rc` de git que sale de correr
   con un `cwd` que no es un directorio. MEDIDO el 2026-10-05: sin ese pre-chequeo —o con
   `os.path.exists` en vez de `os.path.isdir`— el `3` sigue saliendo pero por otro camino, y su
   texto pasa a ser «git no ejecutable», que es un síntoma y no un diagnóstico. Guardado por
   `test_un_arbol_que_no_es_un_directorio_sale_con_3_y_lo_dice`.

   *Y `is-inside-work-tree` tiene que responder `true`.* Un repo en el que git responde `false`
   es un repo que no se ha podido comprobar, y el `3` tiene que ser eso. MEDIDO el 2026-10-05:
   aceptando `false` el código 3 deja de ser determinista y `--verify` puede imprimir
   `WOPT_REPO_OK` **mintiendo** que el repo y su árbol son usables. Guardado por
   `test_is_inside_work_tree_false_hace_rechazar_el_repo`.

   *Por qué la paridad no es un extra.* Honrar `GIT_WORK_TREE` sin más sería un arma de doble filo:
   basta un `GIT_DIR` real + un árbol ajeno para versionar un árbol extranjero en el historial real.
   La paridad es **el precio** de esa decisión, y hace **no representable** la combinación
   «`GIT_DIR` desechable + árbol real» que produjo la medida. No añade ningún código de salida:
   extiende la fila «cuándo» del `2`, igual que hizo TASK-059 con la puerta del mensaje.

   *Y un detalle que hay que conocer para escribir sondas:* el `cwd` de cada subproceso de git se
   **deriva del `env`** (`GIT_WORK_TREE`), no de un `REPO_ROOT` fijo. Medido: con `cwd` fijo y un
   work tree temporal, `rev-parse --is-inside-work-tree` responde `false` —el directorio de trabajo
   no está dentro del work tree efectivo— y `validar_repo` rechazaba con el `3` la propia
   invocación que se le acababa de pedir. En el camino normal el valor es el de siempre, byte a byte.
8. **Todas las cadenas de `print()` del wrapper son ASCII puro** (trampa #16: la consola es
   cp1252). Los comentarios y docstrings sí llevan acentos. La puerta del mensaje (sección
   siguiente) vive bajo esta misma regla: su motivo de rechazo es el texto que más urge y el que
   menos puede fallar al imprimirse.
9. **LA PUERTA DE LA CABECERA, y el criterio está COPIADO, no inventado (TASK-066).** El
   mensaje tiene que parsear como conventional commit y su cabecera no pasar de 120. El criterio
   sale de **leer el código de commitlint**, no de suponerlo, y las cuatro fuentes quedan citadas
   en el docstring de `clasificar_cabecera` para que un cambio sea rastreable:
   `@commitlint/parse` (headerPattern `/^(\w*)(?:\((.*)\))?!?: (.*)$/` del preset angular),
   `@commitlint/ensure/src/case.ts`, `.../to-case.ts` y
   `@commitlint/rules/src/subject-case.ts`.

   *Por qué está en el wrapper y no en el `.yml`.* El wrapper es la **única puerta de
   versionado** del bucle. Un commit de 135 caracteres no debe poder existir: el día que pueda
   volver a existir, vuelve el rojo.

   *El criterio no se relaja para que pase lo que escribió el guard* (la opción (b) del plan,
   subir `header-max-length` a 220, queda **descartada**): relajar el guard para que pase lo que
   escribió el guard es como un guard deja de guardar. Lo que se.extiende es el **perímetro**,
   con el resolutor de rango que ya está escrito en el `.yml`, y se deja el guard con todo su
   poder sobre lo futuro.

   *`clasificar_cabecera` es PURA y NO lee `.commitlintrc.json` en caliente*, a propósito: leerla
   haría que en un repo sin config la puerta se quedara muda y **verde**, que es la misma clase de
   fallo que la puerta del mensaje suffrió con un `tasks.json` ilegible. El precio son dos copias
   de los números, y lo paga `test_la_puerta_de_cabecera_usa_las_cuentas_de_la_config`, que
   compara `LIMITE_CABECERA`, `TIPOS_ADMITIDOS` y los `subject-case` con la config real.

   *MEDIDO, y corrige la tabla D-4 de `GITHUB-SETUP-CHECKLIST.md`:* `subject-case` **no** es «no
   empezar por mayúscula». Rechaza el subject **entero** en mayúsculas y el PascalCase; uno que
   solo empieza por mayúscula y lleva espacios (`T-9 afirma el invariante`) **pasa**. Con el
   criterio real, el rango histórico `41b8061..4d86908` tiene **siete** commits rojos, **no
   ocho**: el octavo, `92368ad`, no incumple ninguna regla.

   *MEDIDO, y fue un conflicto real:* dos plantillas del bucle eran `feat/fix: ...` y
   `feat/fix([COMPONENTE]): ...`, que **no parsean** (`/` no es carácter de tipo para el
   headerPattern), luego el job `commits` las rechazaba con `type-empty` y `type-enum`. La puerta
   fiel a CI y las plantillas tal como estaban eran **incompatibles**. Se corrigieron las
   plantillas y **no** se relajó la puerta: una puerta más laxa que CI deja pasar justo lo que CI
   va a tumbar, que es el fallo que esta puerta existe para cerrar. La plantilla nunca se usó
   literal en 228 commits, así que el cambio no altera ninguna práctica existente.
10. **LA RAMA ES AVISO, NO RECHAZO (TASK-066).** Estar en `main` imprime un bloque `AVISO` que
    nombra la regla del bucle y **se sigue con código 0**. `INFO rama: <branch>` sale en la salida
    canónica, leído una vez, porque hasta TASK-066 el wrapper era **ciego a la rama** (cero
    coincidencias de `branch`) y el bucle llevaba 52 ciclos comiteando en `main` sin que ninguna
    salida lo dijera.

    *Por qué no se rechaza, con la asimetría deliberada.* La puerta del **mensaje** es un rechazo
    duro porque una cabecera de 135 caracteres no tiene caso legítimo: no hay «pero es que este
    mensaje sí es largo», y quien lo escribe puede arreglarlo en el mismo turno. La **rama** es
    otra cosa: un rechazo duro sobre `main` solo guardaría el camino guardado —el wrapper— y
    **bloquearía el commit legítimo del dueño en la rama de release**, que es justo el caso para
    el que `main` existe (`STATUS.md:95(b)`: una puerta que solo existe en el wrapper no puede
    cerrar un `commit` escrito a mano). El defecto que se cierra aquí es «el bucle no sabe que
    debería estar en `beta`», y un defecto de instrucción se cierra con instrucción **y con un
    test que lee la instrucción**, no con un `sys.exit` que dejaría al bucle sin salida
    documentada. El coste —un `git commit` a mano en `main` no lo caza nadie— queda **declarado**,
    no escondido.

### Flag `--verify`

```bash
python .taskmaster/git_safe_commit.py --verify
```

Autocomprobación **de solo lectura** (solo `rev-parse`): ejecuta **exactamente** la misma función
`validar_repo()` que el camino principal —prohibido darle una ruta de código propia— e imprime
`WOPT_REPO_OK <git_dir>` + `0` si el repositorio está sano, o `WOPT_REPO_INVALIDO <detalle>` + `3`
si no. Es el mecanismo de diagnóstico cuando el pipeline recibe un `!= 0` sin escribir nada.

**`--verify` también pasa por la puerta de paridad (regla 7), y eso es normativo:** si dice
`WOPT_REPO_OK` está afirmando que el repo **y su árbol** son usables, y una asimetría de ese par es
exactamente la mentira que un diagnóstico no debe contar. Con el par entero sale `0`; con una sola
de las dos variables sale `2` con `WOPT_USAGE paridad-git`. MEDIDO el 2026-10-05: el mutante que
se salta la puerta en `--verify` sobrevivía a las 139 pruebas, y ahora muere en
`test_la_puerta_de_paridad_tambien_cubre_el_modo_verify`.

### Cobertura

> **MEDIDO el 2026-10-05, y es la MISMA clase de fallo que la contaminacion de
> `STATUS.md:23`, con un mecanismos distinto: una sonda de mutacion que se
> corrompio a si misma.** Al medir los mutantes de `TASK-066` (T-4) por subproceso, el
> script que los muta tomo su copia de seguridad **despues** de haber aplicado la primera
> mutacion de la tanda. Al matarlo durante la corrida —que dura nueve minutos— su `finally`
> no se ejecuto, porque **un proceso muerto no ejecuta su `finally`**, y el siguiente
> mutante se midio sobre un wrapper al que le faltaba un bloque entero. El sintoma
> aparecio como si fuera de un test: `subject-case` dejo de rechazarse y el fallo se leo
> como una regresion de `TASK-066`, no como contaminacion de la sonda.
>
> Las tres reglas que salen de ahi, y que se aplican a **toda** sonda que mute el repo:
>
> 1. **La copia va ANTES de mutar, y fuera del repo** (`%TEMP%`). Una copia tomada
>    durante el proceso es una copia del estado ya cambiado.
> 2. **El digest se comprueba antes y despues, y el script ABORTA si no cuadra.** Un
>    digest que se imprime y no se comprueba no vigila nada; y hay que **mirar el
>    resultado**: aqui la primera impresion de "restaurado: NO" se tomo por un falso
>    negativo del script y casi se vuelve a medir encima. Era corrupcion real.
> 3. **Un `finally` no es una garantia de restauracion ante la muerte del proceso.** Si
>    la sonda puede durar minutos y se puede cancelar, la fuente de verdad tiene que
>    estar en disco antes de empezar.

`run_tests.py` -> `test_git_safe_commit_fail_safe()` invoca el wrapper como subproceso con
`GIT_DIR` apuntado a rutas temporales inválidas y exige los códigos exactos del contrato
(`3` y `2`). Es un test que **discrimina**: revierte el fix del código de salida y falla. No toca
el repositorio real ni su historial.

**Lo que ese test NO probaba, medido el 2026-10-02 (ciclo #48):** ninguna de sus invocaciones
llega a un `WOPT_FAIL`; sus cuatro aserciones de `returncode` son `3`, `3`, `2` y el `0` de
`--verify` con repo sano, y **ninguna** es `1`. El código `1` —**el del fallo de git**, que es el
invariante que el ciclo #11 rompió devolviendo `0`— **no lo comprobaba nadie.** Mutante medido sobre
el `git_safe_commit.py` real (`sys.exit(CODE_FAIL)` -> `sys.exit(CODE_OK)` en el camino de commit,
el `sys.exit` inmediatamente posterior al `print` con `WOPT_FAIL commit` — **localizado por
contenido, nunca por número de línea**, porque la `:230` que se citaba es hoy la puerta de uso que
TASK-059 añadió después de aquella medición): **la suite entera quedaba en verde con exit 0**, y el
wrapper imprimía `WOPT_FAIL commit` mientras salía con `0`. Segunda medición: el mutante sobrevivía
también a `validate_docs.py`, así que **los dos semi-veredictos del toolchain lo dejaban pasar** —son
un semi-veredicto medido dos veces, no dos testigos.

**Lo que la cubre HOY (TASK-061, cerrado el 2026-10-04).** Tres sondas, y cada una mide una cosa
distinta porque ningún test solo alcanza:

| Sonda | Qué ata | Por qué no es tautológico |
|---|---|---|
| `test_el_contrato_de_codigos_esta_atado_a_cada_linea_wopt` (AST, sin subproceso) | La tabla `(WOPT_*, CODE_*)` de los 15 sitios de salida de `main()`, incluido ningún `sys.exit` sin marcador canónico y los valores 0/1/2/3 | Afirma el código **declarado** |
| `test_un_fallo_de_git_no_sale_con_cero` (subproceso, repo y árbol temporales) | `returncode == 1` ante un `pre-commit` que falla, `WOPT_FAIL commit` como última línea, `WOPT_COMMIT_OK` ausente, y no-contaminación | Afirma el código **ejecutado**, que es lo que lee la víctima |
| `test_el_cero_esta_sobrecargado_por_dos_desenlaces_y_solo_por_esos_dos` | `0` = `WOPT_NOOP` **sin ningún hash** (afirmación negativa y tipada) o `WOPT_COMMIT_OK` con hash que **resuelve**; y el par asimétrico sale con `2` y cero escrituras | La fila de la paridad **fallaba sin mutar nada** |

**Medido el 2026-10-04, con el mutante S48-2 puesto por contenido:** muere en la sonda de AST (la
tabla que produce el código real discrepa de la que declara el contrato) **y** en la de runtime
(sale `0` donde se exige `1`). La familia entera de `WOPT_FAIL` la cubre la tabla, y el mutante que
añada un `print` de mentiras para parecer honesto también muere, porque su fila no está en la tabla.
Re-medido el 2026-10-05 tras la segunda ronda: sigue muerto en las dos, y por partida doble.

### Segunda ronda (2026-10-05): seis huecos que la tabla anterior no cubría

El `mutation-auditor` puso seis mutantes encima del mismo wrapper y **los seis sobrevivieron a las
139 pruebas**. No era que el invariante fuera falso —S48-2 sigue cerrado—: era que las propiedades
que el panel daba por guardadas **no tenían guardián**. Seis son mutantes, ahora los seis muertos:

| Mutante | Qué rompía | Sonda que lo mata |
|---|---|---|
| M5 | La puerta de paridad colocada **antes** de `validar_repo`: el 3 dejaba de ganar al 2 y un `--verify` con par asimétrico y repo malo salía con 2 | `test_la_puerta_de_paridad_va_despues_de_validar_repo` |
| M6 | La paridad saltada en `--verify` (`and not verify`): `--verify` decía `WOPT_REPO_OK` + `0` con el par asimétrico, **mintiendo** | `test_la_puerta_de_paridad_tambien_cubre_el_modo_verify` |
| M7 / M8 | `validar_repo` sin el pre-chequeo de que el árbol es directorio (M7 lo quita, M8 cambia `isdir` por `exists`): el `3` seguía saliendo pero con el motivo de git traducido a la lengua de git | `test_un_arbol_que_no_es_un_directorio_sale_con_3_y_lo_dice` |
| M9 | `is-inside-work-tree` aceptando `false`: el `3` dejaba de ser determinista y el diagnóstico podía mentir | `test_is_inside_work_tree_false_hace_rechazar_el_repo` |
| M10 | Un `print` con `WOPT_*` **nuevo** que no cerraba ninguna salida: el `ast` de T-2 lo descartaba en silencio, porque solo registra un marcador cuando detrás hay un `sys.exit` | `test_toda_linea_wopt_de_main_esta_en_la_tabla_y_cierra_una_salida` |

**La aserción 1 del contrato de T-2, corregida.** La propuesta afirmaba «cada `print` con `WOPT_*`
está en la tabla» y el test **no la implementaba**: por el hueco que M10 midió: el `ast`
solo anotaba un marcador si detrás había un `sys.exit`, y cualquier otra sentencia ejecutable
ponía el marcador a `None`, de modo que un `WOPT_*` suelto desaparecía del contador sin que la
tabla lo notara. La aserción no era falsa: era **prometida y no implementada**, que es el mismo
fallo que S48-2 un grado más abajo. Ahora hay una sonda que la cumple, y con **dos** mitades: el
conjunto de marcadores que `main()` imprime tiene que ser exactamente la tabla, y cada `print` con
`WOPT_*` tiene que cerrar un `sys.exit` en su bloque. La segunda mitad es la que mata a un mutante
que **reutiliza** un marcador ya existente (un `WOPT_FAIL` de más), donde la primera no lo ve.

**Lo que esta sección afirmaba y era FALSO, corregido el 2026-10-05.** La fila «Antes de
`validar_repo`» de la tabla de posiciones daba como justificación que «los dos caminos de commit del
test existente esperan 3 y pasarían a 2». **No se puede reproducir:** `test_git_safe_commit_fail_safe`
pone `GIT_WORK_TREE = root` en todas sus invocaciones, luego el par nunca está roto ahí, la puerta
nunca dispara y el test sigue verde muevas donde la muevas. La fila mandaba a leer un guardián que
no existía. Ahora la consecuencia está medida con la combinación que el test existente **no**
construía y que sí distingue una posición de la otra.

**La víctima, nombrada, y el tamaño real del daño:** el único consumidor real del código de salida
es el **agente orquestador** (`.agents/agents/architect-review/agent.md:50` y
`.agents/skills/id-pipeline/SKILL.md:401`, que escribe el changelog tras el commit «para tener el
hash»), mientras que el validador solo lo menciona. Y el matiz que corrige el tamaño: un `WOPT_NOOP`
**no lleva hash** (regla 4 de esta tabla), luego esta puerta no puede reintroducir el CHANGELOG con
hashes inventados; el daño real era el **ciclo cerrado sin commit** —el panel y el changelog
afirmaban un versionado que no ocurrió—, un grado menos explosivo que el del ciclo #11. Fila del
panel: `STATUS.md:89`, cerrada con su ancla.

**Límites declarados, no omitidos:**
1. La sonda de AST afirma el código **declarado**, no el ejecutado. Por eso hace falta la de runtime.
2. La paridad es más estrecha que «el repo está bien»: valida que no se pueda **mezclar** un repo de
   un sitio con un árbol de otro. El caso «repo sano equivocado» sigue **sin detección**.
3. `test_un_fallo_de_git_no_sale_con_cero` depende de un hook de git, que en Windows corre por el
   `sh` de git. Si `pre-commit` resultara frágil en otro host, la fila se queda sin guardar y el
   invariante queda solo con el AST.
4. La puerta de paridad se comprueba **después** de `validar_repo` (y por tanto también en
   `--verify`): si el repo no se puede comprobar, «no pude ni comprobar» (`3`) gana a «tu invocación
   está mal» (`2`). Es la misma precedencia que fijó D2 de TASK-059, y está medida contra el código.

## La puerta del mensaje: el identificador es obligatorio (TASK-059)

### Qué exige

Un mensaje pasa la puerta si lleva **al menos una** de estas tres formas, y solo tres:

| Forma | Ejemplo | Por qué |
|---|---|---|
| `TASK-NNN` **que exista en `.taskmaster/tasks.json`** | `(TASK-059)` | Es la única que se puede **resolver**, y resolverla es lo que convierte el identificador en ancla y no en decoración |
| `CYCLE-NNN` | `CYCLE-059` | Convención de ciclo, sin dependencia de ficheros |
| Marcador de ciclo | `ciclo 59`, `ciclo #59`, `cycle-59` | El **mismo** patrón que el del validador (`validate_docs.py` -> `_RE_MARCADOR_DE_CICLO`), carácter por carácter |

**`T-\d+` NO cuenta.** `T-1`..`T-9` son ids de tarea *dentro de un change*
(`openspec/changes/*/tasks.md`), no existen en `tasks.json` y nadie puede
resolverlos: aceptar un `T-9` es aceptar un ancla de mentira. MEDIDO: el commit
`9433985` lleva `T-9` donde debía llevar `TASK-063`, y ese es exactamente el caso
que un regex laxo deja pasar.

**Son tres convenciones pero solo DOS formas resolutivas** (S4 del ciclo 52, veredicto
EQUIVALENTE): `CYCLE-NNN` **casa también con el marcador de ciclo**, porque `CYCLE-59`
es `cycle` seguido de un separador y un número, que es justo lo que
`_RE_MARCADOR_ANCLA` (el mismo patrón del validador) acepta. MEDIDO por la auditoría
con un barrido de 4 grafías × 10 000 números: **0 contraejemplos**. Por eso
`_RE_CYCLE_ANCLA` no puede ser nunca la razón de un `True`: está subsumido. Se
conserva la constante **con un trabajo real**, que es el test que demuestra la
equivalencia con un barrido igual, para que nadie lo lea como una tercera puerta
independiente ni lo "simplifique" creyendo que hace falta.

**Medido sobre el historial real (2026-10-04, 212 subjects):** pasan **150
(71 %)** y la rechazan 62 (29 %), y de los 25 commits más recientes la fallan 8
(32 %) — el bucle no vivía limpio. **La puerta no paraliza el bucle: lo rechaza
un 29 %, no un 100 %.** De las 212 menciones de `TASK-`, **todas las que se
resuelven resuelven**: hay 63 ids en `tasks.json` y 48 de los 51 ciclos del
journal se corroboran hoy por el historial, luego **siempre hay un identificador
disponible** y la puerta es *opt-out por construcción*, no *opt-in* (la misma
disyuntiva que ya resolvió el check 8 con las exenciones de la Deuda).

### Dónde está, y por qué ahí

```
parse_args  ->  validar_repo (repo + arbol)  ->  [repo invalido: 3]
             ->  PUERTA DE PARIDAD (WOPT_USAGE paridad-git + 2)
             ->  [--verify]  ->  status --porcelain
             ->  NOOP (WOPT_NOOP + 0, EXENTO)
             ->  INFO rama: <rama>  +  [AVISO si es rama de publicacion, NO rechaza]
             ->  PUERTA DEL MENSAJE  <- aqui
             ->  PUERTA DE LA CABECERA  <- aqui (TASK-066)
             ->  add -A  ->  diff --cached  ->  commit  ->  WOPT_COMMIT_OK
```

El orden **es normativo** y las tres fronteras se pueden medir contra el código real:

| Posición | Consecuencia medida |
|---|---|
| Antes de `validar_repo` | Rompe el contrato, y la consecuencia **medida** es esta: un `--verify` con el par asimétrico (`GIT_DIR` sin `GIT_WORK_TREE`) **y** un repo no verificable saldría con **2** en vez de **3**. El 3 significa «no pude ni comprobar» y el 2 «tu invocación está mal»: confundirlos entrena al orquestador a diagnosticar el repo cuando el problema es su cadena. MEDIDO el 2026-10-05 y guardado por `test_la_puerta_de_paridad_va_despues_de_validar_repo`.<br>**Lo que esta fila DECÍA antes era FALSO y se corrige aquí:** la redacción anterior («los dos caminos de commit del test existente esperan 3 y pasarían a 2») no se puede reproducir, porque `test_git_safe_commit_fail_safe` pone `GIT_WORK_TREE = root` en **todas** sus invocaciones: el par nunca está roto ahí, la puerta nunca dispara y el test sigue verde muevas donde la muevas. Esa era una justificación que mandaba a leer un guardián que no existía. El guardián real es la fila siguiente, y exige la combinación que el test existente **no** construía. |
| **Después de `validar_repo` y del NOOP, antes de `add -A`** | **Elegida.** Un árbol limpio sigue diciendo `WOPT_NOOP` + `0` (benigno: no hay commit que anclar, y rechazar un no-op sería ruido que el orquestador leería como «el commit falló»); un commit que existe lleva **siempre** identificador; y la puerta es de **solo lectura**, luego testeable sin escribir nada. Las dos mitades del criterio las guardan `test_la_puerta_de_paridad_va_despues_de_validar_repo` (repo no verificable → `3`) y `test_el_cero_esta_sobrecargado_por_dos_desenlaces_y_solo_por_esos_dos` (par asimétrico → `2` con el índice y el `HEAD` intactos). |
| Después de `add -A` | Rechaza **después** de stagear: muta el árbol real para luego decir que no. Prohibido. |

### El código de salida es 2, no 1

El rechazo imprime `WOPT_USAGE ancla-mensaje <qué se espera> <por qué importa>` y sale con
**`2`**. No se **añade** un código: se **extiende** la fila «cuándo» del `2`, y el contrato
0/1/2/3 sigue íntegro. La razón es que la puerta **no ejecuta ninguna operación de git**, y
meterla en `WOPT_FAIL` haría **falsa la tabla de más arriba**: un `WOPT_FAIL ancla-mensaje` sería
indistinguible de un fallo de git para el único consumidor real del código, que ramifica por
él (`.agents/agents/architect-review/agent.md`). Todo consumidor que ramifica por `exit == 0`
sigue viendo «no hubo commit», que es lo único que no puede perderse.

La línea `WOPT_*` va **la última**, siempre (regla 4), y es **ASCII puro** (regla 8). El motivo
deja claro que es un **POR QUÉ**, no un «formato inválido»: quien recibe el rechazo tiene que
poder corregir el mensaje sin abrir el contrato.

### Dos degradaciones, las dos explícitas

- **`tasks.json` ilegible** → la puerta es **FAIL-CLOSED**, y esto se corrigió al medirlo
  (auditoría del ciclo 52, que lo había reportado como fail-open: es al revés). **MEDIDO:** con
  `ids=set()`, `"chore: TASK-059"` → `False` y `"chore: TASK-999"` → `False`. **No degrada a la
  forma:** deja de aceptar `TASK-` **por completo**, porque el `in` sobre un conjunto vacío no
  encuentra nada. Las dos convenciones de ciclo siguen pasando, y no dependen de ficheros. O sea:
  con el fichero roto **el bucle se para** (código 2) y el `INFO` lo dice con el motivo literal.

  Se eligió **fail-closed** y no «aceptar `TASK-NNN` por su forma» por una razón concreta: esa
  alternativa es **exactamente el punto ciego que TASK-059 cierra**. Un identificador que nadie
  puede resolver no es un ancla, es una decoración, y aceptarlo por su forma devuelve el proyecto
  al estado previo. El precio del fail-closed —que un `tasks.json` roto detenga el bucle— es
  visible al instante y no deja al bucle sin salida (basta `ciclo N`). Un `except` que devolviera
  «todo válido» sería peor que ambas.

- **`--verify`** → **no** pasa por la puerta: es un diagnóstico del repo y no lleva mensaje.

> **Por qué esto estaba mal en la documentación y ya no lo está:** tres fuentes (el docstring de
> `ancla_del_mensaje`, el aviso de `ids_de_tareas` y D5 de la propuesta) describían degradaciones
> incompatibles, y el código hacía una cuarta cosa. La lección operativa es la del ciclo 47 y la
> del #52 alike: **una afirmación sobre un comportamiento que ningún test comprueba no es
> documentación, es hopescrito**. Ahora hay dos tests que fijan el comportamiento elegido, con el
> valor medido escrito en el mensaje de aserción.

### Por qué el NOOP queda exento, y por qué eso no es un descuido

Un no-op **no tiene commit que anclar**, así que no hay nada que anclar. Lo que sí tiene efectos
—y es intencionado— es esto: **`WOPT_NOOP` nunca imprime hash** (regla 4) y la plantilla del
changelog **exige** hashes (`SKILL.md`, sección «Outcome»), luego el fallo lo detecta el paso
siguiente, tarde pero **sin falso verde**. MEDIDO el 2026-10-04: otro actor commiteó 16 segundos
después de la última escritura de la propuesta (`20daaed`) y se llevó sus tres ficheros; el
wrapper devolvió `WOPT_NOOP arbol limpio` + `0` y el mensaje que iba a llevar `TASK-059` **se
descartó en silencio**. El NOOP es benigno **para el repositorio** —nada se pierde, el contenido
queda versionado— y **no lo es para quien llama**, que creyó haber versionado. Que siga siendo
benigno es exactamente lo que permite que no haya que cambiarlo: un `WOPT_NOOP` que imprimiera un
hash inventado sería mucho peor que un no-op silencioso.

**Y `git_safe_commit.py` no tiene cerrojo.** Dos actores que commitean a la vez se reparten el
resultado y el segundo se lleva su mensaje perdido. No se arregla aquí (un cerrojo en el único
wrapper **bloquearía** al bucle si el proceso muriera con el taken), pero queda medido y con dueño.

### Lo que esta puerta NO cubre

1. **No es independencia de actor.** La escribe el mismo agente que escribe el mensaje: puede
   mentir en el identificador igual que mentía sin él. Lo que se gana es que **omitir** ya no
   sale gratis, no que mentir desaparezca.
2. **No cubre el `git` a pelo.** El bucle tiene prohibido versionar sin el wrapper, pero la puerta
   solo existe en el wrapper. Un commit hecho a mano pasa sin identificador y el validador lo verá
   como `SIN marcador` — que es la cifra que ya se imprime, y por eso sigue viva.
3. **El rechazo extremo a extremo con un árbol deliberadamente sucio ya es hermético
   (cerrado por `TASK-061`).** Antes era falso: `get_env()` imponía
   `GIT_WORK_TREE = REPO_ROOT` sin condiciones (regla 7), luego el árbol de trabajo no era
   controlable desde fuera del wrapper y la cobertura necesitaba «el truco declarado» de ensuciar el
   árbol real con un fichero untracked que la propia sonda creaba y borraba. Con `GIT_WORK_TREE`
   honrado y la paridad exigida, las sondas trabajan sobre un **árbol temporal sucio** y ninguna
   escribe en el árbol del duño: la medida de la hermeticidad es que el índice de la sonda no puede
   contener ni una ruta del árbol real, y eso salta si alguien revierte la paridad.
4. **El patrón de ciclo está DUPLICADO** (el del validador y el de la puerta) porque el wrapper no
   puede depender del validador: es la única puerta de versionado y tiene que valer con el
   validador caído. Lo único que impide que diverjan es un assert que compara las dos cadenas
   carácter a carácter (`run_tests.py`, test 125). Dos copias sin ese assert serían dos puertas.

## Check 9: los hashes del journal y el registro de sus pérdidas (TASK-059)

`.taskmaster/rd_journal.json` declara, por ciclo, los hashes del trabajo de ese ciclo, y hasta
TASK-059 **nadie los comprobaba**: el validador no leía ese campo. `_comprobar_hashes_del_journal(root,
errors, ok)` implementa **cinco** reglas, y cada una es un fallo distinto — mezclarlas daría
números falsos:

| # | Regla | Qué mide | Por qué está escrita así |
|---|---|---|---|
| **R1** | Forma | Cada elemento de `commits` es un hash corto **completo**: `fullmatch` de `[0-9a-f]{7,40}`, sin texto libre | Medir el **string entero** produjo la cifra falsa de «41 de 46 hashes no resuelven» (tabla de opciones descartadas, más arriba): `"617eef8 (architect)"` **contiene** el hash `617eef8` y su búsqueda lo daba por bueno. El `fullmatch` es el fix de esa clase de bug, no un detalle de estilo |
| **R2** | Resolubilidad | Cada hash declarado **resuelve** en el mismo repo desacoplado que usa el ancla, con la misma precedencia de `GIT_DIR` | Sin objeto no hay ancla. La lectura es **un solo** `git cat-file --batch-check` por pasada, no un `--batch-check` —`t` por hash: ~100 subprocesos en el journal real por una cifra que cabe en uno |
| **R3** | Registro de pérdidas | Campo `commits_perdidos` **por entrada** (la pérdida es de *un ciclo*, y el journal es una **lista** en la raíz: un campo de raíz obligaría a cambiar la forma del documento), con `{hash?, causa, nota?}` y `causa` en **vocabulario cerrado**: `VFS_CORRUPTO` (el objeto no existe; se perdió con el `.git` del árbol) y `NUNCA_DECLARADO` (el ciclo nunca declaró hash y el historial no lo nombra) | Una causa redactada en libertad es **infalsable**: no se puede contar, no se puede agrupar, y cualquiera puede escribir «se perdió» y cerrar el ciclo. Con vocabulario cerrado, «apareció una causa nueva» es un **valor nuevo visible** que hay que decidir. La prosa libre cabe solo en `nota` |
| **R4** | **Antidolar** | Un hash declarado perdido que **RESUELVE** es un FAIL | Sin R4 la solución degenerada es declarar como perdidas las entradas que no se quieren sanear y el check queda **verde**: el falso verde que este check existe para matar, **al revés**. Declarar de más es la misma clase de fallo que borrar una fila sin evidencia |
| **R5** | Techos | `MAX_HASHES_PERDIDOS` y `MAX_CICLOS_SIN_HASH`, **medidos el 2026-10-04** y comentados con esa fecha en el propio producto | El techo no es un objetivo a barrer: es un **suelo que avisa si crece**. Bajarlos es una acción, y ese día el check la exige |

**Borrar una declaración de pérdida no silencia nada.** El `commits` del ciclo sigue ahí, y sin su
`commits_perdidos` la R2 vuelve a fallar. El registro **explica**, nunca **suprime** — y por la
misma razón una pérdida declarada de un hash que la entrada **no** declara en `commits` es un
FAIL: es tapar la pérdida sin el hecho que la sostiene.

### Dos formas de «pérdida sin hash», y por qué se cuentan distinto

Una declaración **sin** `hash` es una de dos cosas, y el check las separa porque miden cosas
distintas:

- **El ciclo entero sin hash** → cuenta para `MAX_CICLOS_SIN_HASH`, porque **ahí no hay objeto que
  nadie pueda mirar** y es la forma que puede esconder una pérdida real.
- **Un hueco declarado** en una entrada que **sí** tiene hashes → exige `nota` y **no** cuenta para
  ese techo. Solo existe porque el bucle escribe el changelog **después** del commit «para tener el
  hash» (`SKILL.md`, «Cuándo se escribe») y el relleno se queda sin hacer.

**MEDIDO al implementar:** contar ambas cosas en el mismo contador daba **3 contra un techo de 2**,
o sea que el diseño original trataba como la misma medida dos cosas que no lo son. El techo protege
la forma arriesgada, que es la única sin objeto que comprobar.

### El pre-vuelo que evita fabricar pérdidas

`git cat-file --batch-check` responde `missing` para **todo** lo que se le pide y **sale con 0**
cuando el repositorio está **vacío de commits**, y en ese caso el `returncode != 0` de la lectura
NO lo distingue. Sin el pre-vuelo (`git rev-parse --verify HEAD`, el **mismo criterio** que
`validar_repo` del wrapper, para que los dos componentes no puedan discrepar sobre qué es un repo)
el check acusaría las ~100 entradas del journal como «no resuelven» y **sugeriría declararlas
perdidas**: fabricar una pérdida es la peor dirección en la que se puede equivocar un ancla.

⚠️ **MEDIDO con las tres cifras reales** (la primera versión de este párrafo afirmaba una falsa, y
una medición inventada en un comentario es peor que un comentario sin medición):

| `GIT_DIR` | `rev-parse --verify HEAD` | `cat-file --batch-check` |
|---|---|---|
| directorio vacío (no es repo) | 128 | 128 |
| **`git init` sin commits** | **128** (`Needed a single revision`) | **0 + `missing`** para todo |
| `git init` con un commit | 0 | 0 + `missing` |

El caso del medio es el que obliga al pre-vuelo. Y exigir `HEAD` no recorta ningún caso legítimo:
un journal con hashes viene de commits que existen.

**Y la respuesta se acepta con su forma exacta**, `<sha-completo> <tipo> <tamano>` (40 o 64 hex,
una palabra, un entero), no contando campos: un nombre con espacio se devuelve **tal cual**, luego
`f"{hash} (architect)"` responde `e60d2a0 (architect) missing`, que tiene tres campos y
certificaba como existente un objeto que no existe.

### UNA CAUSA, UN MENSAJE (y lo que sí se degrada: el veredicto, no el registro)

**MEDIDO el 2026-10-04 con la suite real en marcha:** el check 9 acusaba **dos veces** un journal
ilegible que el ancla del changelog de raíz —que lee **el mismo fichero**— ya había acusado con
`ESTA CORRUPTO`, y el test preexistente de TASK-057
`test_el_journal_ilegible_informa_en_vez_de_reventar_el_validador` murió con `assert len(errors) == 1`.
Esa aserción lleva desde el ciclo #47 diciendo lo correcto: **un estado produce un mensaje**. Dos
acusaciones del mismo hecho son ruido que entrena a ignorar el semáforo.

El reparto de responsabilidades queda así, y es el mismo para las **dos** ilegibilidades:

| Estado | Quién acusa | Qué hace el check 9 |
|---|---|---|
| Journal ilegible | `_comprobar_ancla_del_changelog`, que es quien lo lee para el ancla del changelog | **No acusa.** Deja en `ok` una línea `SIN COMPROBAR` con el motivo **literal** (la clase de la excepción) y el nombre de quien ha acusado |
| Repositorio ilegible | `_comprobar_ancla_de_commits`, que es quien lee el historial | **No acusa.** Igual: `ok` con `SIN COMPROBAR` y el motivo literal, y R1/R3 —que no necesitan git— sí se comprueban |

La regla que separa las dos cosas es una sola: **una causa, una acusación; y una verificación que
no se pudo hacer, escrita**. Lo que no se degrada nunca es el **veredicto**: sin esa línea en `ok`,
«cero errores» se cumpliría igual con el check 9 *mudo*, que es el otro extremo del mismo fallo —y
un repo caído y un repo con tres hashes muertos darían el mismo informe, que es justo la confusión
que R5 tiene que evitar. El test que lo fija es
`test_un_journal_ilegible_produce_exactamente_un_error_en_el_validador_real`, sobre el **validador
real ejecutado como subproceso**, con dos formas de ilegibilidad y su mitad mutante.

⚠️ **MEDIDO, y corrige una expectativa fácil:** con un **directorio** donde debería estar el journal
el validador produce **3** `[FAIL]`, no 1. Dos de ellos son otro hecho, con su acusación legítima:
`_ruta_existente` tampoco encuentra el fichero y el check 8 acusa que el ancla de una fila no
resuelve. Un estado puede tener varias consecuencias legítimas; lo que no puede haber es dos voces
sobre la **misma**.

### Cobertura

`run_tests.py` -> `test_el_check_9_de_los_hashes_del_journal_sobre_un_arbol_sintetico` (siete
filas sobre el esqueleto real copiado una vez, con `GIT_DIR` temporal y **commits reales** de ese
repo) y `test_el_check_9_se_cablea_en_el_camino_real_del_validador` (copia el validador real a un
árbol temporal y lo ejecuta como **subproceso**, con su mitad mutante: el cableado sustituido por
`pass` tiene que hacer desaparecer el residuo). Los **techos se leen del producto**, no se copian,
y se exige que su comentario lleve la fecha de la medición. Los números que se comparan son los que
la **fixture** construye: ninguna expectativa se deriva del fichero que se valida.

### LIMITES RESIDUALES de TASK-059 — se escriben, no se omiten

1. **El rechazo extremo a extremo con un árbol *deliberadamente* sucio no es hermético.**
   `get_env()` impone `GIT_WORK_TREE = REPO_ROOT` sin condiciones (regla 7), luego el árbol de
   trabajo **no es controlable desde fuera** del wrapper y un test no puede fabricar «árbol sucio»
   sin mutar el árbol real. La cobertura real va por la función extraída, por una aserción
   estructural con `ast` sobre el orden, y por un subproceso que ensucia el árbol **con un fichero
   untracked que el propio test crea y borra**. La puerta **sí** es hermética en el sentido que
   importa: es de solo lectura y devuelve antes de la primera escritura. **Dueño: `TASK-061`**, cuya
   decisión de diseño sobre `GIT_WORK_TREE` es la que lo desbloquea.
2. **La puerta no es independencia de actor.** La escribe el mismo agente que escribe el mensaje:
   puede mentir en el identificador igual que mentía sin él. Lo que se gana es que **omitir** ya no
   sale gratis, **no** que mentir desaparezca.
3. **La puerta no cubre el `git` a pelo.** El bucle tiene prohibido versionar sin el wrapper, pero
   la puerta solo existe en el wrapper. Un commit hecho a mano pasa sin identificador y el validador
   lo verá como `SIN marcador` — la cifra que ya se imprime, y por eso sigue viva.
4. **El techo de pérdidas congela un residuo que no se puede cerrar, por construcción.** Los hashes
   perdidos con el `.git` del VFS no van a volver. El techo no es un objetivo a barrer: es un suelo
   que avisa si **crece**. El día que se recupere un objeto (un `git fetch` de un clon) el techo
   habrá que bajarlo, y ese día el check exigirá la acción, que es lo que se quiere.
5. **R3 se apoya en un vocabulario cerrado, y un vocabulario se puede ampliar a voluntad.** Si
   alguien añade un valor a `causa` para tapar una pérdida real, R4 sigue sujetando a los **hashes**,
   pero una entrada `NUNCA_DECLARADO` **sin hash** no la sujeta nadie más que el techo. Es la
   costura más blanda del diseño y se declara como tal. Por eso la forma sin hash **exige `nota`**:
   sin hash no hay hecho que comprobar y sin nota no hay nada que leer.
6. **El residuo del journal se saneó a mano, en este mismo cambio.** Los 9 ciclos rellenables, los
   13 con texto libre y el `<PENDIENTE>` del ciclo 50 se corrigieron uno a uno con la evidencia de
   cada hash, no con una migración codificada. Es trabajo de una vez, y por eso esta tarea exigía
   hacerlo **en el mismo cambio**: un check que nace con decenas de FAIL en el repo real es un check
   que el bucle aprende a ignorar, que es el fallo del ciclo #15 en otra forma.
7. **El techo de ciclos sin hash es un suelo, no un veto por entrada** (añadido al implementar, y
   medido). Una entrada sin hashes y **sin** declaración no es un FAIL en sí misma: cuenta, y la
   acota el techo. La razón es medida, no de gusto: el veto por entrada pone en rojo los árboles
   sintéticos con los que las demás reglas se miden —y con ellos buena parte de la cobertura del
   check 8—, y un validador que se pone rojo solo obliga a desactivarlo. El coste se paga en el otro
   lado del saldo: un ciclo nuevo sin hash **no** se acusa hoy, se cuenta, y el conteo se imprime en
   la línea de informe en cada pasada.
8. **La cobertura de la puerta depende de la suite real, no de una sonda que la complete** (MEDIDO
   el 2026-10-04): con `pydantic` roto en el host, los tests de TASK-059 se ejecutaron primero con
   un arnés que inyectaba `json` en el espacio de nombres del módulo, y eso **hizo pasar** un
   `NameError` que la suite real cazó al primer test. La lección no es del arnés —que era una salida
   de emergencia razonable y está borrado—, es que **una sonda que completa el espacio de nombres
   del producto es capaz de tapar justo el fallo que se busca**. Un test que importa el módulo real,
   con sus imports reales, es el único veredicto; y si hace falta un arnés, que no le dé al módulo
   lo que el módulo no declara.

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
- Del campo `commits` del journal: el validador **ya lo comprueba** (check 9, R1-R5, con su línea
  de informe viva). Las entradas que no declaran hash y los hashes que no resuelven son **residuo
  declarado**: cada uno con su `causa` en el vocabulario cerrado, y **sin cifra fija aquí** — las
  cifras están en la línea de informe, que se reimprime en cada pasada, y una cifra caducada escrita
  al lado de la cifra viva es peor que no escribirla.

### LIMITACIÓN RESIDUAL — el problema NO está cerrado

Se documenta sin adornos porque este repo ya pagó una vez por declarar cerrado un problema que
no lo estaba (ciclo #15):

1. **El historial lo escribe el mismo actor que el journal.** La ganancia es de **clase de
   fallo** —reescribir historia frente a editar una clave de un JSON—, **no de independencia de
   actor**. Quien puede mentir en el journal puede mentir en los mensajes de commit.
2. **Más de la mitad de los commits no llevan marcador de ciclo** (son los `feat(...)`, `fix(...)`,
   `test(...)`; la cifra viva —subjects leídos, con marcador y sin él— está en la línea de informe
   del validador que se copia arriba). **MEDIDO el 2026-10-04 (TASK-059): este punto está CERRADO en
   el sitio por el que se versiona.** `git_safe_commit.py` rechaza el mensaje sin identificador
   (`WOPT_USAGE ancla-mensaje`, código 2), de modo que un ciclo comiteado **sin** commit de cierre y
   **sin** entrada de journal ya no puede nacer por el camino del bucle: o lleva `TASK-NNN` que
   resuelve, o lleva marcador de ciclo, o no se versiona. **Lo que queda abierto, y es distinto:**
   un commit hecho a **mano**, saltándose el wrapper, sigue sin identificador y el validador solo lo
   ve como `SIN marcador` — cerrar eso exigiría forbidding `git` a pelo, y el validador no puede
   cerrar una puerta de escritura que no es suya. La puerta tampoco es independencia de actor.
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
   panel escribe todos sus veredictos. MEDIDO: hasta la ronda 5 **ninguna** fila de la
   tabla comprobaba esta condición, y por eso el mutante que la borra
   (`findall` → `[texto]`, C25) sobrevivía con la suite entera en verde. La ronda 6 lo
   cierra con **(p1)**: marcador **en la prosa** + `TASK-001` ya `completed` → la fila
   sigue VIVA. MEDIDO: C25 **MUERE en (p1)**. La (u) —que el informe declaraba su lugar
   de muerte— **NO lo mata**, porque su id está pendiente.
3. ~~La fila nombra un **id trazable** (`TASK-NNN` o `CYCLE-NNN`) que **existe**.~~
   **SUPRIMIDA con su código.** MEDIDO el 2026-10-02: la quinta condición la
   **subsume** (un id cerrado es por definición trazable) y `_ids_trazables` se quedó
   sin un solo llamante, luego se borró en vez de quedarse como decoración. Este punto
   estaba aquí **describiendo código que ya no existe**, que es peor que no
   documentarlo.
4. Ni el **veredicto** ni la **prosa** de la fila **niegan** el cierre. Cubierta por
   (m), (v) y (t) **con id pendiente**, y por **(p4a)** y **(p4b)** con la `TASK-001`
   ya `completed`: MEDIDO el 2026-10-02 que las dos primeras **no** la mataban, porque
   con un id pendiente la fila no se cierra de todos modos.
5. Y el id que cierra la fila está **CERRADO**, no pendiente: una `TASK` con
   `status == completed` o un `CYCLE` con entrada en uno de los **dos changelogs**.
   MEDIDO el 2026-10-02: las condiciones 1, 2 y 4 solo se probaban con un id
   **pendiente**, luego ninguna regla de la FORMA marcaba la diferencia, y (y)/(n2) —las
   únicas dos filas que cerraban de verdad— las dejaban pasar todas. Por eso la ronda 6
   añade (p1), (p2), (p3), (p4a), (p4b) y (p5): **marcador DEFECTUOSO con un id ya
   CERRADO, que es la única combinación en la que la forma decide el veredicto**.
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
validador leía `ROJO`/`AMARILLO`/`VERDE`, luego el suelo **no se ejecutaba nunca**. El
emoji se mapea a la palabra **al leer**, y el informe sigue siendo ASCII puro porque la
consola es cp1252 (trampa #16).

**MEDIDO el 2026-10-02 con `_gravedad_declarada` fila a fila, ya con el mapeo: `ROJO` en
ocho filas (87, 89, 90, 93, 94, 96, 98 y 99), `AMARILLO` en dos (100 y 101) y NINGUNA en
cinco (88, 91, 92, 95 y 97).** La versión anterior de este párrafo decía «14 de las 15
filas no tienen ni una palabra de gravedad, y la única que la tiene (la 98) la usa para
el *color* de un diagnóstico de UI»: es **falso**, y lo era porque se había mirado el
TEXTO sin mapear los glifos que se estaba contando. La 98 usa 🔴 cuatro veces y lo
usa como severidad real de la fila, lo cual no la invalida para este propósito.

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
   las que declaran 🔴 son la **89 y la 98**. MEDIDO el 2026-10-02 (ronda 6) con
   `_severidad_minima` fila a fila: **solo la 88 y la 89 tienen suelo**, porque son las
   **únicas dos** que anclan `git_safe_commit.py`; las otras trece dan `""`.
   - **Rebajar la 89 a 🟡 sale en ROJO** (`1 FAIL`, P7): su suelo es `ROJO` y
     `AMARILLO` está por debajo.
   - **Rebajar la 98 a 🟡 sale en VERDE**: `7 exenta(s) / 8 viva(s) / 35` anclas y
     `0 FAIL`. La versión anterior de esta línea decía «rebajar la 98 **también**», y es
     **FALSA**: la 98 **no ancla `git_safe_commit.py`**, luego su suelo es `""` y el
     `if suelo and …` no llega a evaluarse. No lo delata ni el suelo ni ninguna otra
     regla, y ese mecanismo —**una 🔴 sin suelo no la declara nadie**— es un agujero
     DISTINTO del que este límite enunciaba, con su propio número: el **27**.
   La **88 no declara ninguna gravedad** —`_gravedad_declarada` devuelve
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
   - **MEDIDO el 2026-10-02 (ronda 6), y aisla el mecanismo:** cambiar `CYCLE-999` por
     `CYCLE-998` —un id que **tampoco** existe en ningun registro— en la misma fila 95
     da **exactamente lo mismo**: `8 exenta(s) / 7 viva(s) / 35` anclas y `0 FAIL`. O sea
     que el `CYCLE` de ese veredicto **no aporta nada**: la fila se exime por su
     `TASK-057` (`completed`), que es el residuo ya declarado del limite 19, y no por
     una puerta nueva. Es la prueba de que aqui no hay un agujero de forma sino una
     exencion que ya existia.

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
    declara en vez de eliminarse porque el escenario (c3) la ejecuta de verdad. La
    ronda 6 anade que `_ciclos_cerrados` TAMPOCO la puede usar: el mutante **C3**
    («el registro de ciclos vuelve a mirar el journal») **sobrevivio** a la ronda 6
    entera.** MEDIDO: con el journal entre los registros, `CYCLE-901` sigue sin cerrar
    nada, porque la forma de ENTRADA `^##[ \t]+\[?(CYCLE-\d+)\]?` no casa con nada de
    un `.json` que guarda `"cycle": <int>`. O sea que **mirar el journal o no es
    indistinguible**, y por eso la quinta condicion ya no depende de _que_ registros se
    leen sino de la FORMA de la entrada. El escenario (c3) sigue siendo el que ejecuta
    esa rama, y su valor es el de una asercion de cobertura, no el de un agujero.
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
26. **TRES filas del panel tienen un número IMPAR de `**`, y eso HOY decide si un
    marcador escrito en NEGRITA se ve. MEDIDO el 2026-10-02 (ronda 6) con
    `_RE_NEGRITA.findall` sobre el panel real:** la **89** cuenta **63** asteriscos y
    extrae **31** veredictos, la **96** cuenta **21** y extrae **10**, y la **101** cuenta
    **117** y extrae **58**. Las tres son impares y **ninguna estaba declarada**: solo se
    conocía la 101.

    **El contraste que la versión anterior de este límite citaba NO reproduce.** Decía
    «con los 120 asteriscos pares, `_porta_el_marcador_de_cierre` devuelve `True`». MEDIDO
    con la 101 a **119, 120, 121 y 123** asteriscos: el veredicto bien formado añadido
    **NO aparece entre los extraídos en los cuatro casos**, ni con el recuento par. Y lo
    mismo en la 89 (a 65 y 66) y en la 96 (a 23 y 24). La razón es que el emparejamiento
    de `**…**` es **posicional y de izquierda a derecha**: un `**` suelto empareja con el
    primero del veredicto que se añada, luego a partir de ahí **todo** va desplazado y la
    paridad no lo arregla.

    **Lo que de verdad protege a la 101 no es el formato, y por eso este límite se
    reescribe.** La protege la **autoexención**, que **no usa negrita**: mira el nombre
    del criterio y la palabra de cierre en mayúsculas **fuera de código inline**. MEDIDO:
    añadirle `**CERRADA en TASK-060, cerrada de verdad.**` da `8 exenta(s) / 7 viva(s) /
    27` anclas y **1 FAIL** —«la fila del criterio se ha autoeximido»—, o sea que **falla
    en ROJO y no en verde**. Y cerrar el desbalance (añadir un `**` suelto, 118) no cambia
    nada: `7 exenta(s) / 8 viva(s) / 35` anclas y `0 FAIL`.

    **Y el escenario (m2) NO lo cubre**: usa un árbol **sintético**, luego mide una fila
    formateada por el propio test y no la fila del criterio real. Lo que ahora ata esa
    fila al código es la fase que la ronda 6 añadió **dentro** del test del check 8, que
    ejecuta `validar` contra el **repo real** y exige `0 FAIL` de la sección: un ataque a
    la 101 pasa a ser un fallo de `run_tests.py` y no un `FAIL` que solo ve quien ejecuta
    `validate_docs.py` a mano. **No se corrige el desbalance de las tres filas**: son
    filas de Deuda y su regla es *solo añadir, nunca reescribir*.
27. **TRECE de las quince filas NO TIENEN SUELO, y a una 🔴 sin suelo no la vigila
    nadie.** Es el hermano del límite 4 por el otro lado, y existe porque medir el suelo
    fila a fila dio un número que el límite 4 no recogía. MEDIDO el 2026-10-02 con
    `_severidad_minima` sobre el panel real: el suelo se deriva de si algún ancla de RUTA
    **declara** el código sobrecargado, y **`.taskmaster/git_safe_commit.py` es el único
    fichero del repo que lo declara**; MEDIDO que **solo la 88 y la 89 lo anclan**. Las
    otras trece dan `""`:

    | fila | gravedad | suelo | por qué |
    |---|---|---|---|
    | 87, 90, 93, 94, 96, 99 | 🔴 | `""` | declaran severidad y no anclan el comprobable. Las seis son **exentas**, luego el suelo ni se les pregunta |
    | 91, 92, 95, 97 | ninguna | `""` | no declaran gravedad y no anclan el comprobable |
    | **98** | 🔴 | `""` | **MEDIDO: bajar su primer 🔴 a 🟡 deja el panel en `7/8/35` y `0 FAIL`** |
    | 100, 101 | 🟡 | `""` | declaran `AMARILLO` y no anclan el comprobable, luego tampoco pueden bajar a 🟢 sin que nada lo vea |
    | 88, 89 | ninguna / 🔴 | `ROJO` | las dos únicas con suelo; la 89 está **justo en su suelo**, y por eso bajar su 🔴 a 🟡 sí sale en rojo (P7) |

    O sea que el suelo de gravedad vigila hoy **una sola fila del panel** (la 89). No se
    arregla porque un suelo derivado exigiría escribir a mano la política de gravedad del
    repo, que es la misma mentira un nivel más arriba (límite 3), y porque el fix posible
    —derivar la gravedad de la materia prima de cada fila— no se ha medido. Se declara
    como cobertura ausente **con su número de filas**, que es lo que hace que un
    re-lector no lo descubra como novedad.

