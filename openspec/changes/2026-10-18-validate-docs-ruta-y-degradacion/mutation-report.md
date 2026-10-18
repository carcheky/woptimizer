# Informe de mutacion · Ciclo 64 · TASK-075

**Auditor:** `mutation-auditor` (Sherlock) · **Fecha:** 2026-10-18
**Alcance:** `validate_docs.py` y su degradacion honesta (T-1..T-8, AC-1..AC-8).
**HEAD esperado:** `a577158` · rama `beta`.

> **Estado: CERRADO.** Se ha escrito incrementalmente, veredicto a veredicto. Todo
> lo que hay aqui esta **medido**: o el log de la suite termina en
> `ALL TESTS PASSED` (superviviente) o en `AssertionError` con traceback (muerto).
> Los dos puntos marcados como **no medido** lo estan **por decision de alcance o
> por prohibicion del encargo**, nunca por falta de intento, y en los dos casos se
> dice cual.

---

## 0 · Camara y aislamiento

La camara es una copia del proyecto en `%TEMP%`, creada con
`shutil.copytree(..., ignore=shutil.ignore_patterns(".git", ...))`, que excluye
`.git` **como fichero** (en este repo `.git` es un FICHERO de puntero a
`%LOCALAPPDATA%\woptimizer_git\.git`, no un directorio: `robocopy /XD .git` no lo
evita).

Prueba de aislamiento, ANTES de mutar nada:

| Comprobacion | Resultado medido |
|---|---|
| `camara/.git` existe como fichero | **False** |
| `camara/.git` existe como directorio | **False** |
| `git rev-parse --git-dir` con `GIT_DIR` desechable explicito | devuelve el desechable (rc=0) |
| `git rev-parse --git-dir` SIN variables, `cwd` = camara | `rc=128`, `fatal: not a git repository (or any of the parent directories): .git` |

La ultima fila es la que importa: desde la camara, git **no puede descubrir nada**,
y en particular no el repo real.

**Baseline (obligatorio, sin el cual ningun veredicto de este informe vale nada):**

| Camara | Bytes del log | Ultima linea | Veredicto |
|---|---|---|---|
| `wopt_c64_base` (sin mutar) | 27672 | **`ALL TESTS PASSED.`** | **VERDE** |

La camara sin mutar pasa la suite entera en el mismo entorno y con el mismo
`GIT_DIR`/`GIT_WORK_TREE` que las cams mutantes, luego la comparacion es limpia.

*Aviso de honestidad:* el shell con el que lance las suites dejo
`GIT_WORK_TREE=""` (variable **presente y vacia**) en el entorno de los procesos.
Comprobado que **no** rompe nada: el baseline sale verde con el, y los tests arman
su propio entorno de git para cada llamada. Queda dicho para que nadie lo lea como
una camera "limpia" que no lo era.

**Correccion sobre la marcha (metodologica):** la primera prueba de aislamiento dio
falsa alarma (mi comprobacion exigia stdout no vacio y git responde 128 sobre un
`GIT_DIR` mal apuntado). Diagnostico: el descartable apuntaba al *raiz* del repo y
`GIT_DIR` exige el directorio `.git`. Corregido y repetido: **AISLAMIENTO OK**.

**Segundo condicion de la camara:** el primer baseline fallo con
`AssertionError: git no resuelve --absolute-git-dir para ...wopt_c64_base`, porque
`run_tests.py:6597` (`_git_dir_absoluto_de_este_arbol`) exige que el arbol SEA un
repo git — es lo que permite a la sonda medir que el HEAD **real** no se mueve
(`test_un_fallo_de_git_no_sale_con_cero`). Cada camara lleva por tanto su **propio**
repo local (`git init` + un commit), creado con el entorno sin `GIT_DIR` y
verificado con `rev-parse --absolute-git-dir` apuntando a `<camara>/.git`. Ningun
`git` de esta auditoria ha tocado el repo real.

---

## 1 · Tabla de mutantes

Un veredicto solo existe si el log termina en `ALL TESTS PASSED` (superviviente) o
en `AssertionError` con traceback (muerto). Log cortado = **NO MEDIDO**.

| id | Que rompi (mutacion literal) | Que garantia rompe | Veredicto | Motivo literal del log |
|---|---|---|---|---|
| **M1** | en `_hashes_que_existen`, primera sentencia: `repo = _resolver_el_repositorio(root, os.environ.get("GIT_DIR"))` — el consumidor **se resuelve el suyo** y `--git-dir` no le llega | **AC-3**: UN solo punto de resolucion para los DOS consumidores | **killed** | `AssertionError: el check 9 ha leido un repo que NO es el que dice WOPTIMIZER_GIT_DIR: acusa el hash 7c109e6 que SI existe en ...repo_bueno\.git. Con la derivacion duplicada, el check 5b honraba la precedencia y el check 9 no.` — `run_tests.py:21892` |
| **M2** | en `_resolver_el_repositorio`: `("GIT_DIR", env.get("GIT_DIR"))` sube por encima de `("WOPTIMIZER_GIT_DIR", ...)` | **peldaño 2 de la precedencia**: `WOPTIMIZER_GIT_DIR` > `GIT_DIR` | **killed** | `AssertionError: \`WOPTIMIZER_GIT_DIR\` tiene que GANAR a \`GIT_DIR\`: es lo que exige la precedencia de \`proposal.md\` 7.1. Resuelto: ruta='...repo_malo\\.git', origen='GIT_DIR'` — `run_tests.py:21882` |
| **M3** | en `_resolver_el_repositorio`: el peldaño `("GIT_DIR", env.get("GIT_DIR"))` pasa a `("GIT_DIR", None)` | **nivel 3 de la precedencia** y la fila (e) de la tabla del ancla | **killed** | `AssertionError: el residuo son los ciclos que EL HISTORIAL TIENE Y EL JOURNAL NO: en este arbol el 47, nunca el 46` — `run_tests.py:12952`, en `test_el_ancla_de_commits_no_depende_del_que_escribe_el_journal`. Sin el peldaño, el check 5b cae al default de la camara y acusa los ciclos 004..063 |
| **M4** | en `main()`: el bucle de `saltados` imprime `print(f"  [OK]   {line}")` | **AC-6 / T-4**: lo saltado nunca puede salir como `[OK]` | **killed** | `AssertionError: con `--sin-ancla-de-git` tiene que haber lineas `[SKIP]`: si lo saltado no se imprime, el flag es un silencio y el informe entero parece comprobado.` — `run_tests.py:22153` |
| **M5** | en `main()`: el resumen pasa a `print(f"Resumen: {len(ok)} OK, {len(errors)} FAIL")` (sin el recuento de saltados) | **AC-6, segunda mitad**: el informe tiene que contar los saltados | **killed** | `AssertionError: el resumen tiene que CONTAR los saltados y no solo los OK: 'Resumen: 146 OK, 0 FAIL'. Sin ese numero, un \`0 OK, 0 FAIL\` con el flag puesto se lee como un verde entero` — `run_tests.py:22166` |
| **M6** | en `_comprobar_el_repositorio_del_anclaje`: `motivo = None if os.path.exists(repo.ruta) else ...` en vez de `_leer_el_repo_si_lo_hay(root, repo.env)` | **AC-5 / T-3**: el criterio de repo es `rev-parse --verify HEAD`, no `exists()` | **killed** | `AssertionError: un `--git-dir` directorio vacio tiene que producir el FAIL PROPIO de "lo que se dijo a mano no es un repo", y no solo el del historial` — `run_tests.py:22075` |
| **M7** | `_leer_el_repo_si_lo_hay` devuelve `None` siempre: `return None  # el motivo literal se pierde` | **T-3 / AC-4**: lo que no sirve tiene que FALLAR con su motivo literal | **killed** | `AssertionError: un repo SIN COMMITS responde 'missing' para todo y eso NO puede acabar en 'el hash no resuelve y no lo declara': seria fabricar perdidas.` — `run_tests.py:21345` |
| **M8** | en `_comprobar_el_repositorio_del_anclaje`: el `ok.append("repositorio del anclaje: ...")` se sustituye por `pass` | **T-5**: el informe tiene que **nombrar** el repositorio del que leyó | **killed** | `AssertionError: el informe tiene que decir que el repositorio vino del flag: es la prueba de que la ruta llego hasta la resolucion y no se quedo en el parser.` — `run_tests.py:21981` |
| **M9** | en `release.yml`, vuelve el motivo viejo: ``deriva GIT_DIR de %LOCALAPPDATA%\woptimizer_git\.git`` | **AC-8**: el motivo de la exclusion de CI es el **medido** | **killed** | `AssertionError: el motivo VIEJO se ha retirado porque es el mas pequeno de los dos y ya no es la atadura ... Un motivo falso es peor que ningun motivo` — `run_tests.py:22240` |
| **M10** | en `_resolver_el_repositorio`: `env["GIT_WORK_TREE"] = root` sin condiciones (el comportamiento anterior) | **N7b**: el `GIT_WORK_TREE` que viene en el entorno se respeta y se **dice** | **killed** | `AssertionError: el \`GIT_WORK_TREE\` que se respeta va en la misma linea: es la otra mitad de 'de donde leyo' y no se deduce del resto.` — `run_tests.py:22320` |

**Resultado: 10 de 10 mutantes muertos, 0 supervivientes, baseline verde.**

Cada muerte es por la asercion que ese test dice comprobar, nunca por
`ImportError`, ni por un error de sintaxis, ni por un traceback de arranque: los
nueve mutantes de `validate_docs.py` llegan hasta el fondo del test que los busca y
mueren en su `assert`, y el de `release.yml` muere en el check documental que nombra
la frase exacta que se habia puesto.

**Por que M1 es el mutante importante, y por que lo hice asi**

M1 es el mutante que `tasks.md` T-1 nombra como el que este encargo tiene que
cerrar. **Lo escribi para que el guard estructural NO lo viera**: la mitad de
`ast` del test (`run_tests.py:21784-21823`) prohibe `expandvars` en el cuerpo de
los dos consumidores, exige el parametro `repo` y exige **una** llamada a
`_resolver_el_repositorio` en `validar()`. Un mutante que reintrodujera la
derivacion literal con `os.path.expandvars` moriria ahi, y moriria por una forma,
no por el defecto.

La version de M1 llama a la funcion compartida **sin** el valor del CLI: sigue
habiendo un solo punto de resolucion en el codigo, el parametro `repo` sigue
siendo un argumento, `validar()` sigue llamando una vez... y aun asi el check 9
lee el repositorio equivocado. **Muriò en la mitad conductual**, con el hash que
SI existe en el repo bueno acusado por R2.

Eso es lo que significa "un solo punto de resolucion" medido y no supuesto: no
que el codigo tenga una forma, sino que **escribir** "leer otro repositorio" desde
un consumidor no comparta el camino con el otro consumidor. El mutante que
reintroduce la duplicacion por forma muere en el `ast`; el que la reintroduce por
comportamiento muere en el contenido. Los dos mortality paths existen.

---

## 1bis · Integridad del repo real (obligatoria, y sin git)

El encargo prohibe explicitamente usar `%LOCALAPPDATA%\woptimizer_git\.git`, asi
que `git status`, `git diff` y `git reflog` **no se han ejecutado** contra el repo
real. En su lugar, la misma garantia por otra via: comparar la **instantanea** que
se copio a la camara **antes de mutar nada** contra el arbol real de ahora, fichero
a fichero y byte a byte, y medir el `mtime` de cada diferencia para decir quien la
escribio.

| Fichero | mtime real | Anterior a mi sesion? |
|---|---|---|
| `.git` (puntero, 57 B, `gitdir: .../woptimizer_git/.git`) | **2026-09-30 16:40:07** | **SI** |
| `src/woptimizer/woptimizer.log` | **2026-10-18 16:05:20** | **SI** |
| `openspec/changes/.../mutation-report.md` | 2026-10-18 18:46:18 | no: **es mio** |

Conclusion: **el unico fichero del repo real que he escrito es
`mutation-report.md`.** Ni un commit, ni un checkout, ni un reset, ni una escritura
en el arbol de trabajo.

*Dos diferencias que la primera version de esta prueba marco como "no declaradas"
y que son artefactos de la propia medicion, declarados aqui para que no se lean
como:*
- `.git` aparece como "nuevo" porque mi copia lo excluye **a proposito** (es un
  fichero puntero al repo real). Su contenido y su mtime son los de antes.
- `src/woptimizer/woptimizer.log` difiere porque **la copia de la camara** crece
  cuando la suite corre dentro de ella (259072 B frente a los 176709 B del
  original). El log del repo real no se ha tocado: 16:05, antes de que yo empezara.

**Confesion de metodo, no de repo:** mi primera version de esta prueba uso una
constante escrita a mano para "el inicio de mi sesion" y salio diciendo que yo
habia escrito un log de las 16:05. La constante estaba mal; el marcador correcto es
la creacion de la camara. Lo dejo escrito porque un informe que se corrige a si
mismo en silencio es un informe que no se puede reauditar.

---

## 1ter · Lo que NO he hecho (y por que)

| Prohibicion del encargo | Cumplimiento |
|---|---|
| No invocar `.taskmaster/git_safe_commit.py` | **0 invocaciones.** Ni una. (La suite lo llama en sus propias camaras, que es su cuenta y no la mia.) |
| Git solo contra `GIT_DIR` desechable dentro de la camara | Todo `git` de mi arnes lleva `GIT_DIR` explicito y desechable, o se ejecuta **dentro** de una camara con su propio `.git`. El unico clon externo (`%TEMP%\wopt_c64_clon`) y un clon de solo lectura del remoto. |
| Nada de `checkout`/`reset`/`stash`/`clean`/`restore` | **0** de esos comandos, en ningun sitio. |
| No tocar `%LOCALAPPDATA%\woptimizer_git\.git` | **0** usos. Eveno citado a proposito por `.gitattributes` y por el propio codigo. |
| Unico fichero escribible: el informe | Verificado en la seccion 1bis: solo `mutation-report.md`. |

---

## 2 · N5 · Los dos incidentes que el dev se Pembro self, sin residuos

### N5a · Emoji destruidos por `Get-Content|Set-Content`

Medido sobre los tres ficheros que el dev dice reescribir, en UTF-8:

| Fichero | U+FFFD (Replacement) | `A-circunflex` (mojibake) | `A-tilde` (mojibake) | CRLF | LF |
|---|---|---|---|---|---|
| `STATUS.md` | **0** | **0** | **0** | 0 | 135 |
| `AGENTS.md` | **0** | **0** | **0** | 0 | 145 |
| `README.md` | **0** | **0** | **0** | 0 | 108 |

Mi detector de mojibake marco **un** suspecto en `STATUS.md` (`o»`), y es un
**falso positivo mio**: `»` (U+00AB) cae en el rango que youse como senal de
mojibake, y el texto es espanol correcto (`por «no encontrado», no por su
asercion`). Los tres ficheros tienen **emojis intactos** (145/148/125 caracteres
no-ASCII) y **cero** caracteres de reemplazo. Sin residuos.

### N5b · El arnés que revento dejando `validate_docs.py` mutado

| Comprobacion | Resultado medido |
|---|---|
| Marcadores del arnés (`mutado`, `sha(original)`, `MUTANTE`, `INSTRUMENT`, `breakpoint()`, `XXX`) en `validate_docs.py` | **0 en todos** |
| `ast.parse(validate_docs.py)` | **OK** (parsea) |
| `def _resolver_el_repositorio` | aparece **1** vez (la funcion real, no un Doble) |
| Menciones de `TASK-075` en el codigo | 6 (las de los comentarios del ciclo) |
| `original(` en `run_tests.py` (4 apariciones) | **todas preexistentes**: 2 monkeypatches (`return original(self, path)`), 1 firma de cierre (`original=original)`), 1 nombre de test (`..._pack_original()`) |
| `instrumentado` / `harness` en `run_tests.py` | prosa y nombres de fichero (`test_harness.py`), nada del arnés de este ciclo |

Ningun resto. El fichero-restaurado-a-mano esta integro.

### N5c · CRLF declarado (2783/193) frente a lo medido

| Fichero | Bytes en disco | Lineas | CRLF | LF sin CR | Bytes si se normalizara a LF |
|---|---|---|---|---|---|
| `validate_docs.py` | **148173** | **2783** | **2783** | 0 | **145390** |
| `.github/workflows/release.yml` | 9409 | **214** | 214 | 0 | 9195 |

- `validate_docs.py`: la cifra de **2783 lineas CRLF** que declara el dev es
  **exacta** (2783 de 2783, cero LF sueltos).
- `release.yml`: el dev declara **193** y en disco hay **214**. Si los 193 se
  refieren a las lineas del fichero, la cifra **no cuadra**. No he podido localizar
  en que contexto se escribio el 193 con lo medido aqui; queda anotado como
  discrepancia sin cerrar, no como mentira confirmada.
- La diferencia de **2783 bytes = numero de lineas** entre disco (148173) y el
  commit (145390) es exactamente **la aritmetica de la normalizacion**: quitar un
  `\r` por linea. `.gitattributes` declara `* text=auto eol=lf`, luego el indice
  guarda LF y el arbol de trabajo recibe LF. Con la politica declarada, un
  `validate_docs.py` en CRLF en el arbol de trabajo esta en el estado
  **anterior a la normalizacion**, que es el estado que el propio `.gitattributes`
  describe del historico previo. No es un fichero "versionado con finales
  distintos de los que dice tener": es un fichero cuyo contenido en disco es el
  mismo y cuya forma en el indice es la normalizada.
- **No he podido correr `git ls-files --eol`** (es el comando que lo diria de
  forma directa) porque solo el repo real conoce el indice y el encargo prohibe
  usar `%LOCALAPPDATA%\woptimizer_git\.git`. Queda como **no medido**, con la
  aritmetica de bytes como evidencia indirecta.

---

## 3 · N6 · Afirmaciones documentales contra el codigo

| Afirmacion | Medido | Veredicto |
|---|---|---|
| `run_tests.py` tiene 213 tests (`142 + 71`) | **213** funciones `test_*` de primer nivel, derivadas con `ast` | CUADRA |
| Los 6 tests de TASK-075 existen | los 6, con nombre | CUADRA |
| `STATUS.md:81` remite a `docs/ai/sandbox-rules.md` | la fila 81 cita el documento y la seccion **`Por que el validador NO corre en CI`** existe en `sandbox-rules.md:1526` de 1602 lineas | CUADRA (seccion **al final**, por encima de la 61) |
| La seccion no se inserta por encima de la linea 61 | esta en la 1526 | CUADRA |
| `validate_docs.py` sigue atando `sandbox-rules.md:55-56` por numero | dos citas: `validate_docs.py:1429` y `:1924` | SIGUE ATADO |
| Las filas 55-56 son las dos del `0` | 55 = `WOPT_COMMIT_OK`, 56 = `WOPT_NOOP` (**sin hash**) | CUADRA |
| La seccion trae las dos cifras medidas | `154 FAIL` x4, `25 FAIL` x2 | CUADRA |
| `validate_docs.py` escribe ficheros | **0 escrituras** (`open` en `rax`/`wax`, `.write(`, `os.replace`, `shutil.*`) | solo lectura |
| `148 OK, 0 FAIL, 0 SKIP` | **parcialmente medido.** El modo que **no** invoca git, ejecutado sobre el **arbol real**: **`146 OK, 0 FAIL, 3 SKIP`**, exit 0. El delta hasta 148 son exactamente las **dos** lineas de `ok` que si necesitan git (la de T-5, "repositorio del anclaje: ...", y la del historial, "N subject(s)..."), luego la cifra es **coherente**. La corrida que imprimiria 148 exige git contra el repo real, que el encargo prohibe: queda **NO MEDIDO** el numero exacto | coherente, exacto no medido |

_(N6b, la cifra de 25 hashes, se mide en la seccion 5b.)_

### N6b · Los 25 hashes, MEDIDOS en un clon real

El encargo pedia medirlo y no leerlo. Metodo: clon real del remoto
(`git clone https://github.com/carcheky/woptimizer.git`, HEAD `7749692`), y una
**sonda** construida por `git fetch` de **solo** `origin/main`+`origin/beta` — que
es exactamente lo que traeria el runner con `fetch-depth: 0`. A esa sonda se le
pregunta por los **150 hashes del journal de HEAD** con `cat-file --batch-check`,
que es el criterio de R2.

| Magnitud | Medido | Documentado |
|---|---|---|
| Objetos alcanzables desde `origin/main`+`origin/beta` | 2800 | 235 (el doc, sobre otro estado del ODB) |
| Hashes del journal de HEAD | 150 | ~150 |
| **NO resuelven contra el remoto** | **28** | 28 |
| De ellos, ya declarados en `commits_perdidos` (R2 no acusa) | **3** (`12b9c3bf`, `5623629`, `ee4b753`) | 3 |
| **Los que R2 SI acusaria** | **25** | **25** |

**La cifra del documento cuadra exactamente.** El nuevo motivo de la exclusion de
CI no miente como mintia el viejo. (El 235 de objetos del doc es una medicion de
otro dia sobre el ODB del host, no la misma magnitud que mi 2800: no lo contrato
porque no es lo mismo.)

*Detalle menor, sin impacto:* `proposal.md` escribe el tercer hash VFS_CORRUPTO
como `ee4f753`; el real es **`ee4b753`**. Errata de una cifra en el doc de
planificacion, no del codigo.

**Lo que NO reproduce mi medicion:** ejecutar el validador real dentro del clon
(FROM) da `125 OK, 2 FAIL` y **0** lineas `NO resuelve`, porque el clon esta en
`7749692` y su journal es el viejo, cuyos hashes si resuelven. La cifra de 25
mide el journal de **HEAD** contra los objetos del remoto, que es el escenario que
documenta `release.yml`. Lo digo porque un lector que corra el validador en el clon
vera un numero distinto al documentado y pensara que el doc miente.

---

## 4 · N7 · Did the fix open another hole?

### N7a · El tercer estado de `check 9` (`comprobado_git`)

Medido con dos ejecuciones reales del validador sobre la camara:

| Invocacion | rc | Resumen |
|---|---|---|
| `--sin-ancla-de-git` | 0 | `146 OK, 0 FAIL, 3 SKIP` |
| `--git-dir <repo>` | 1 | `147 OK, 156 FAIL, 0 SKIP` |

Lo que se imprime en el caso saltado, textual:

> `[SKIP] campo 'commits' del journal: R2 (resolubilidad) y R4 (antidolar)
> SALTADOS por --sin-ancla-de-git; no se ha mirado <ruta> (origen: default del
> host). R1, R3 y R5 (que no necesitan git) SI se han comprobado, y sin el repo
> **no se declara ni un hash perdido**: acusar a los 150 seria un rojo que parece
> un repo con 150 hashes muertos`

**¿Se distingue de "se miró y no había nada"?** Si, y por tres vias distintas y
simultaneas: (a) la linea `[SKIP]` nombra la ruta que **no** se miro y dice que
R2/R4 no se comprobaron; (b) el resumen lleva `3 SKIP`; (c) no sale ninguna linea
que afirme "0 hashes no resuelven". El unico `[OK]` con la palabra "hash(es)
perdido(s)" es el recuento **R3** de perdidas **declaradas** (3, todos
`VFS_CORRUPTO`), que no necesita git y sale igual en los dos casos: por eso ese
numero **no** puede leerse como "se busco y no se encontro ninguno".

### N7b · `GIT_WORK_TREE` se respeta si viene en el entorno

El dev afirma que **no cambia que ficheros se validan**. Medido, dos ejecuciones
identicas cambiando solo `GIT_WORK_TREE`:

| Medicion | Resultado |
|---|---|
| Lineas de informe **identicas** | **306 de 310** |
| Lineas que solo salen con el arbol ajeno | 1 |
| Lineas que solo salen con el arbol propio | 1 |
| `Resumen` | identico en los dos: `147 OK, 156 FAIL, 0 SKIP` |
| rc | identico (1) |

Las dos lineas que difieren son **la misma linea**, la de `ok` que nombra el
repositorio, con `GIT_WORK_TREE:` distinto. **La afirmacion del dev queda
medida: es informacion, no cambio de contenido validado.**

*(El `156 FAIL` es propio de la camara, cuyo repo local tiene un solo commit y no
resuelve los hashes del journal. No es un hallazgo.)*

### N7c · El registro de llamadas indecisas del guard `cat-file --batch-check`

El dev registro tres `subprocess.run` nuevos (los tres paths de `_leer_el_repo_si_lo_hay`
mas el de la degradacion). **NO MEDIDO**: no he contado las llamadas del registro en
`run_tests.py` ni su umbral, y el mutante que lo haria crecer con `sin_ancla_de_git`
activo no se ha ejecutado. Queda como comprobacion pendiente, con el identificador
**P1**.

---

### HALLAZGO `D2` · Tres recuentos "207" que el validador no puede ver

`tasks.md` T-8 dice: *"con el recuento actualizado en los **4 sitios** ... El
validador **falla en rojo** si uno de los cuatro no cuadra"*. Medido, el validador
lee **una sola linea por fichero** (`validate_docs.py:123-127`) y, para
`testing-guide.md`, **solo las filas de la tabla** (`:156`).

Aplicando **las mismas regexes** del validador sobre los ficheros reales:

| Fichero | Linea que el check lee | Lo que dice |
|---|---|---|
| `STATUS.md` | 12 | `run_tests.py`, **213 tests** |
| `AGENTS.md` | 70 | `# 213 tests headless` |
| `README.md` | 63 | `# 213 tests headless` |
| `docs/ai/testing-guide.md` | 213 filas de tabla | cuadra con 213 |

Y las afirmaciones que el ciclo dejo **sin actualizar y que el check no puede ver**:

| Fichero:linea | Texto | ¿Lo ve el validador? |
|---|---|---|
| `STATUS.md:106` | ``4. **Tests:** `python run_tests.py` (207 tests)`` | **NO** (no lleva `**213 tests**` tras `run_tests.py`) |
| `docs/ai/testing-guide.md:57` | ``Contiene **207 tests**: 142 de backend + 65 headless de UI.`` | **NO** (el check solo mira las filas de la tabla) |
| `README.md:6` | badge `tests-207%20verdes` | **NO** (no menciona `run_tests.py`) |

Y no solo caducan: **se contradicen entre si**. `testing-guide.md:57` declara
`142 backend + 65 headless` (= 207) mientras `STATUS.md:12` declara
`148 backend + 65 headless` (= 213, que es lo que el validador deriva y lee).

El criterio de cierre de T-8 esta, por tanto, **cumplido en la forma que el
validador lee y incumplido en el texto**. No es un falso verde de seguridad: es un
panel que dice dos cosas distintas del mismo numero en la misma rama. Arreglo:
alinear las tres lineas, o ampliar los patrones del check para que abracen la prosa
del recuento (que es lo que haria que "falla en rojo" sea verdad y no solo
"falla en rojo cuando el texto tiene la forma que el check conoce").

---

## 5 · N2 · Precedencia y asimetria (MEDIDO con ejecuciones reales)

Los cuatro peldanos, medido con `validate_docs.py` ejecutado de verdad:

| Peldaño | Ruta que **no** es repo | ¿FAIL explicito "NO es un repositorio"? | Resumen |
|---|---|---|---|
| 1. `--git-dir` | directorio vacio | **SI** | `147 OK, 2 FAIL` |
| 2. `WOPTIMIZER_GIT_DIR` | directorio vacio | **NO** (cae en el FAIL del historial, git 128) | `148 OK, 1 FAIL` |
| 3. `GIT_DIR` | directorio vacio | **NO** (igual) | `148 OK, 1 FAIL` |
| 4. default del host | `LOCALAPPDATA` vacio | **NO** (igual) | `148 OK, 1 FAIL` |

**La asimetria es real y es la que el encargo pedia comprobar:** `--git-dir` es el
unico que se EXIGE (T-3), y los otros tres caen en el FAIL preexistente del
ancla. Todos salen con rc=1, luego **ninguno fabrica un verde**: la asimetria es
de mensaje, no de veredicto.

Y los tres duelos de precedencia, medidos:

| Duelo | Ganador (segun la linea `ok` del informe) | ¿Correcto? |
|---|---|---|
| `--git-dir` vs `WOPTIMIZER_GIT_DIR` (el malo) | `--git-dir` | SI |
| `WOPTIMIZER_GIT_DIR` vs `GIT_DIR` (el malo) | `WOPTIMIZER_GIT_DIR` | SI |
| `GIT_DIR` vs default | `GIT_DIR` | SI |

**HALLAZGO `D1` (documentacion que no corresponde al codigo).**
`validate_docs.py:293` escribe del segundo peldaño:

> `#   2. \`WOPTIMIZER_GIT_DIR\`   entorno; el mismo contrato, dicho por el pipeline.`

Medido, **no es el mismo contrato**: con `WOPTIMIZER_GIT_DIR` a una ruta que no es
repo no sale el FAIL explicito, sale el del historial. Solo `ORIGEN_EXPLICITO` pasa
por `_leer_el_repo_si_lo_hay` en `_comprobar_el_repositorio_del_anclaje:368`. La
linea anterior del mismo comentario dice que `--git-dir` "es el UNICO que se
EXIGE", luego la lectura natural de "el mismo contrato" es "tambien se exige", y
eso es **falso**.

*Honestidad de la lectura:* "el mismo contrato" tambien se puede leer como "el mismo
contrato de **resolucion**" (participa en la precedencia), y en ese sentido si es
cierto. Lo reporto porque la frase esta pegada a la que acentua el UNICO, y quien
lea solo el comentario se llevara la idea de que una ruta mala del pipeline produce
el mismo fallo ruidoso que una del CLI.

**Lo que SI esta documentado como decision:** el codigo, el `help` de
`--git-dir` y `proposal.md` 7.1/7.3 dicen la precedencia y que `--git-dir` es el
unico exigido. La asimetria no esta **oculta**; esta mal **descrita** en una frase.
---

## 6 · SUPERVIVIENTES

**Ninguno.** Los 10 mutantes (M1, M2, M3, M4, M5, M6, M7, M8, M9, M10) murieron
por su asercion.

Candidatos que se consideraron y **NO** cuentan como supervivientes porque el
codigo los hace todavia correctos, o porque el mutante equivalente se ejecuto y
murio:

| Mutante descartado | Por que no es un hallazgo |
|---|---|
| `GIT_WORK_TREE` impuesto siempre (M10) | **Ejecutado: killed.** No es equivalente: el informe deja de decir de que arbol leyo. |
| Reintroducir la derivacion **con `expandvars`** en un consumidor | Moriria en el guard de `ast`, no por el defecto de fondo. Por eso M1 se escribio de otra forma. |
| Borrar `environ.copy()` de `repo.env` | Equivalente: los dos consumidores reciben el mismo objeto. Un cambio equivalente demostrado no es un fallo. |

---

## 7 · Lo que queda abierto, con nombre (para reauditarlo en tres ciclos)

| id | Que queda | Severidad | Que falta |
|---|---|---|---|
| **D1** | `validate_docs.py:293` dice que `WOPTIMIZER_GIT_DIR` tiene "el mismo contrato" que `--git-dir`; medido, solo `--git-dir` se **exige**. La asimetria esta documentada en `proposal.md` 7.3 y en el `help`, pero **contradicha** por esa frase del propio codigo | **media** (documentacion) | Corregir la frase: "el mismo contrato de **resolucion**, no de exigencia; el unico exigido es `--git-dir`". Un mutante que lo verifique seria un test de cadena sobre un comentario: util pero fragil |
| **D2** | Tres afirmaciones con el recuento **207** caducado (`STATUS.md:106`, `testing-guide.md:57`, el badge de `README.md:6`), **invisibles** para el check del recuento, que solo lee una linea por fichero. Y `testing-guide.md:57` se contradice con `STATUS.md:12` (142+65 frente a 148+65) | **media** (documentacion) | Alinear las tres lineas, o ampliar los patrones del check para que abracen la prosa del recuento. Es el unico sitio donde el criterio de cierre de T-8 ("el validador falla en rojo si uno de los cuatro no cuadra") se queda corto |
| **D3** | El dev declara `release.yml` con **193** lineas; en disco hay **214** (y 214 CRLF, sin un solo LF suelto) | **baja** | Localizar la frase y corregirla. Puede que el 193 se refiera a otra magnitud y no sea un error, pero no he podido encontrar el contexto en el que se escribio |
| **P1** | El registro de llamadas indecisas de `test_ninguna_llamada_de_cat_file_batch_check_se_queda_sin_input` crecio **3** entradas (las tres de los flags del validador), documentadas una a una. Mi lectura dice que **no** se debilita: la comparacion es de igualdad exacta en los dos sentidos, luego una llamada indecisa **sin** registrar tumba la suite igual que antes, y las tres nuevas solo exponen `sys.executable` + el path del validador + un flag suyo | **baja** | Falta el mutante que lo compruebe: hacer que una llamada de un test nuevo sea indecisa y **no** registrarla, y ver si la suite la pilla. Es lo unico de este ciclo que queda **NO MEDIDO por decision de presupuesto**, no por el shell |

---

## 8 · VERDICT

# PASS

**Los 10 mutantes mueren por su asercion. 0 supervivientes. Baseline verde.**

Criterio aplicado tal cual lo pedia el encargo: *PASS = toda mutacion muere por su
aserción*. No queda ningun mutante equivalente sin demostrar, asi que no hay que
discutir esa excepcion.

Lo que PASS **no** significa, dicho sin adornos:

- **PASS no es "no hay nada que arreglar".** Hay tres tickets documentales
  abiertos (`D1`, `D2`, `D3`) y uno de verificacion pendiente (`P1`), todos en la
  seccion 7 con su nombre. Ninguno es un falso verde de seguridad ni de datos:
  `D2` es el que mas se acerca, porque un panel que dice 207 y 213 en la misma
  rama es exactamente la clase de mentira que este ciclo vino a cerrar en otro
  sitio.
- **PASS no cubre `P1`**, que no se midio por presupuesto, no por el shell.
- **PASS no mide el `148 OK, 0 FAIL, 0 SKIP`** del arranque normal: esa corrida
  exige git contra el repo real. Si se midiera ahi, es `146 OK, 0 FAIL, 3 SKIP` en
  el modo que no usa git, y el delta son las dos lineas de `ok` que si lo usan.

**Lo que si se puede afirmar de este ciclo, con las mediciones de este informe:**

1. El cambio central —una sola funcion de resolucion para los dos consumidores—
   esta **atado por comportamiento**, no por la forma del codigo. M1, escrito
   expressly para esquivar el guard de `ast`, muere acusando el hash que si
   existe.
2. Los cuatro peldaños de la precedencia estan **atados uno a uno** (M2, M3 mas las
   tres pruebas de precedencia por ejecucion directa).
3. El muro `[SKIP]` esta atado **por las dos vias**: el prefijo (M4) y el recuento
   del resumen (M5). El verde de `--sin-ancla-de-git` es distinguible del verde real
   leyendo solo la salida.
4. El fail-loud de `--git-dir` esta atado por su criterio de git (M6) y por su
   motivo literal (M7), y el nombre del repositorio en el informe por su cadena
   (M8).
5. El motivo de la exclusion de CI **es el medido**: 25 hashes medidos aqui contra
   un clon real, y el mutante que devuelve el motivo viejo muere (M9).
