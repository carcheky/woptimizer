# Informe de mutacion — TASK-076 (ciclo 65)

> `mutation-auditor` / Sherlock. Que pregunta: **si el codigo estuviera mal, ¿los
> tests se enterarian?**
>
> - Ancla del ciclo: rama `beta`, HEAD **`bb33b51`**
>   ("fix(build): fuente unica de los flags de PyInstaller y guard de cobertura
>   desde src (TASK-076)").
> - Planificacion: `123cc25`. Spec: `proposal.md` + `tasks.md` de
>   `openspec/changes/2026-10-18-paridad-flags-pyinstaller/`.
> - Reglas de lectura: un veredicto solo existe si el log termina en
>   `ALL TESTS PASSED` (superviviente) o en `AssertionError` con traceback
>   (muerto). **Log cortado = NO MEDIDO.** Cada mutacion se verifica en disco
>   antes de correr.
> - **No se repara nada.** Este fichero es lo unico escribible del repo, y no
>   se comitea.

---

## 0. Entorno y aislamiento

| Comprobacion | Resultado |
|---|---|
| HEAD al empezar | `bb33b5117efd404d9e2419499ac78f15c3efd479` (`bb33b51`) |
| Rama | `beta` |
| `git status --porcelain` al empezar | vacio |
| Camara | `C:\Users\carch\AppData\Local\Temp\wopt_c65_sherlock` |
| Copia con `shutil.copytree(..., ignore=ignore_patterns(".git", ...))` | `.git` es **fichero** de 57 bytes en el repo real; excluido como fichero, no solo como directorio |
| Prueba de aislamiento: `git rev-parse --absolute-git-dir` con entorno limpio | `C:/Users/carch/AppData/Local/Temp/wopt_c65_sherlock/.git` -> **dentro de la camara** |
| `.git` presente en la camara tras copiar | `False` |
| Huella del repo real TOMADA ANTES de mutar | si (HEAD, status, diff, diff --cached, reflog, count-objects, refs, mtime del git-dir desacoplado) |

**Nota de camara (no es un fallo del ciclo).** La primera linea base fallo en
`test_la_puerta_de_paridad_va_despues_de_validar_repo()` porque la camara no
tenia `.git` y ese guard exige que git resuelva el repo **con entorno limpio**
(`run_tests.py:6597-6623`). Se creo un repo **autocontenido dentro de la
camara** (`git init` en `%TEMP%`), nunca el desacoplado del host. Sin esto
cualquier veredicto posterior seria ruido.

**Anti-`.pyc`:** cada corrida lleva `PYTHONDONTWRITEBYTECODE=1` y
`PYTHONPYCACHEPREFIX` a un directorio **nuevo** por corrida. No se borra nada
(no hay permiso de borrado en este entorno), pero el efecto es el que exige el
`agent.md`: cada ejecucion compila desde el fuente mutado y no puede reutilizar
un `.pyc` obsoleto de la corrida anterior.

### 0.1 Linea base — VERDE, sin la cual ningun veredicto de este informe vale

| | |
|---|---|
| Log | `wopt_c65_sherlock/baseline.log`, **28 671 bytes** |
| Exit code | **0** |
| Ultima linea | `ALL TESTS PASSED.` |
| Duracion | ~75 min **con 13 mutantes compitiendo en paralelo** (no es la duracion nominal de ~10-15 min) |

Los 7 guards nuevos se ejecutan y pasan **antes** del marcador headless
(log:213-228, detalle en §3.4). Una camara en verde es lo que hace que "el
mutante sobrevivio" signifique algo y no "la camara estaba sucia".

---

## 1. Que fixes hay que mutar (AC-1 .. AC-7)

Siete guards nuevos en `run_tests.py:27187-27580`, todos invocados en
`__main__` en `run_tests.py:27880-27886`, **antes** del marcador headless
(`run_tests.py:27887`).

| Guard | Lineas | Que ata |
|---|---|---|
| `test_una_sola_declaracion_de_flags_de_pyinstaller` | 27187-27240 | AC-1 unicidad: ninguna 2ª lista; `python force_build.py` |
| `test_los_assets_que_lee_la_app_llegan_al_ejecutable` | 27243-27312 | **AC-2 cobertura: expectativa sale de `src/`, no de `force_build.py`** |
| `test_la_doc_no_vuelve_a_re_listar_los_flags` | 27315-27367 | AC-3 la doc no re-declara |
| `test_las_citas_de_sandbox_rules_siguen_siendo_ciertas` | 27370-27435 | AC-4 las 4 afirmaciones por numero de linea |
| `test_el_spec_no_vuelve_a_ser_la_fuente_de_verdad` | 27438-27469 | AC-5 nadie compila por `--spec` |
| `test_los_guards_de_flags_no_necesitan_yaml_ni_ejecutan_nada` | 27472-27534 | AC-6 los 7 son de texto, no de YAML ni de proceso |
| `test_la_linea_base_de_flags_se_deriva_del_fichero_real` | 27537-27580 | AC-7 la linea base se deriva del fichero real |

---

## 2. MEDICIONES ESTATICAS (sin mutar): lo que ya se sabe antes de correr

Estas cifras son **derivadas con `ast`/lectura del fichero**, no leidas de un
documento. Se pegan aqui porque acotan severalo de los encargos (N5, N6, N7)
sin necesitar un mutante.

### 2.1 N5a · Respaldo de residuos (U+FFFD / mojibake / CJK)

Busqueda en `run_tests.py`, `validate_docs.py`, `docs/ai/sandbox-rules.md`,
`build.bat`, `force_build.py`, `release.yml`, `STATUS.md`, `README.md`,
`AGENTS.md`:

| Fichero | U+FFFD | mojibake | CJK (`U+4e00-9fff`) |
|---|---|---|---|
| `validate_docs.py` | 0 | 0 | 0 |
| `docs/ai/sandbox-rules.md` | 0 | 0 | 0 |
| `build.bat` / `force_build.py` / `release.yml` | 0 | 0 | 0 |
| `STATUS.md` / `README.md` / `AGENTS.md` | 0 | 0 | 0 |
| **`run_tests.py`** | **2** | 0 | 0 |

**`S1` — hallazgo de residuo (severidad baja, NO de este ciclo).**
`run_tests.py:14105`, dentro del docstring de
`test_la_deuda_exige_un_ancla_resoluble_en_toda_fila_viva` (13954-14688), que es
de **TASK-075 / ciclo 64**, no de TASK-076:

```
14105:      (`if any(c in registro ...)`), que es el agujero central que midi<FFFD><FFFD> el
```

Dos caracteres de reemplazo U+FFFD donde deberia ir un acento (`midió`).
**No esta en ninguno de los 7 guards de este ciclo**, luego no afecta al fix que
se audita. Se reporta porque es exactamente la clase de residuo que se pedia
buscar: es invisible al ejecutar (va en un docstring) y solo aparece al leer el
byte.

### 2.2 N5c · NameError latente en los 7 guards

Recorrido `ast` de cada una de las 7 funciones: todo `ast.Name` en contexto de
carga resuelve a una definicion local, a un import, a un nombre de modulo, o a
un builtin. **0 nombres sin resolver.** El `NameError: name '_tempfile' is not
defined` que el dev se reporto a si mismo (guard R7-a, ahora
`run_tests.py:27568` con `import tempfile as _tempfile` local) **no se repite en
ninguno de los otros 6**.

### 2.3 N5a · Numero de lineas de `sandbox-rules.md`

| Fuente | Cifra |
|---|---|
| **REAL, medida** `len(text.splitlines())` | **1602** |
| `STATUS.md` | **no declara ningun numero de lineas** de este fichero |
| `AGENTS.md` | **no declara ningun numero de lineas** de este fichero |
| `README.md` | **no declara ningun numero de lineas** de este fichero |

**`S2` — el encargo N5a no tiene blanco: NO existe una declaracion que pueda
desviarse.** No hay desfase que medir porque no hay cifra declarada en los tres
paneles. El unico "1339" del repo aparece en `run_tests.py:22199` y en
`docs/ai/testing-guide.md:1324`, y es una afirmacion en **pasado**
("no mencionaba el CI en ninguna de sus 1339 lineas"), es decir, el estado del
documento *antes* del arreglo de TASK-075, no una cifra del estado actual. **No
es una mentira documental** y por eso **no es un hallazgo**.

### 2.4 N4 · Las 4 afirmaciones que el validador NO puede ver

Verificadas contra el fichero real, linea por linea:

| Cita | Linea real | Contiene `sandbox-rules.md:55-56` |
|---|---|---|
| `validate_docs.py:1429` | `# el contrato (`docs/ai/sandbox-rules.md:55-56`) lo documenta, no lo declara.` | **si** |
| `validate_docs.py:1924` | `` `docs/ai/sandbox-rules.md:55-56` lo TABULA y no lo DECLARA. `` | **si** |
| `run_tests.py:22264` | ``"`validate_docs.py` cita `sandbox-rules.md:55-56` POR NUMERO DE LINEA"`` | **si** |
| `docs/ai/sandbox-rules.md:1133` | ``de markdown que **tabula** el contrato (`docs/ai/sandbox-rules.md:55-56`) lo documenta,`` | **si** |

Y el contenido citado sigue siendo el que las cuatro afirmaciones dicen que es:

```
sandbox-rules.md:53  | Codigo | Significado | Cuando | Linea canonica en stdout |
sandbox-rules.md:54  |---|---|---|---|
sandbox-rules.md:55  | `0` | Commit creado de verdad | ... | `WOPT_COMMIT_OK <hash-short> <mensaje>` |
sandbox-rules.md:56  | `0` | Nada que comitear (benigno) | ... | `WOPT_NOOP <motivo>` (**sin hash**) |
```

Las cuatro son ciertas **hoy**. El guard AC-4 lo ata con asercion de
**contenido** sobre esas lineas, no con busqueda de la cadena `55-56`.

### 2.5 N6 · Cifras declaradas, medidas

| Cifra | Declarada | **MEDIDA** | Veredicto |
|---|---|---|---|
| `release.yml` lineas | `STATUS.md:87` (D3): "declarado con 193; tiene **215**" | **215** | **cierta** |
| `build.bat` -> `python force_build.py` | si | `build.bat:27` | cierta |
| `release.yml` -> `python force_build.py` | si | `release.yml:209` | cierta |

> Ojo metodologico: `Get-Content | Measure-Object -Line` devuelve **193** para
> `release.yml`. Miente (cuenta reglas vacias de forma distinta). Con Python,
> `len(splitlines())` = **215**. Quien mida con PowerShell llegara a la
> conclusion contraria que la de D3.

---

## 3. N7 · ¿El arreglo ABRIO otro agujero? (medido, no opinado)

Esta es la cuarta vez que un arreglo cierra un hueco y abre otro. Se auditan los
tres puntos que pedia el encargo.

### 3.1 `build.bat` NO propaga el fallo de `force_build.py` — **MEDIDO, hueco real**

`build.bat:27` invoca `python force_build.py` **sin comprobar nada**, y
`build.bat:40` es `exit /b 0` incondicional.

Medicion de extremo a extremo (no lectura del fichero): se copio el repo a una
camara, se sustituyo `force_build.py` por un stub que hace `sys.exit(1)` — que
es exactamente lo que hace el `force_build.py` real cuando PyInstaller falla,
`force_build.py:23-29` — y se ejecuto el `build.bat` **real, sin tocarlo**:

```
stdout de build.bat:
   ===========================================================
     woptimizer - Compilando Standalone Executable (PyInstaller)
   ===========================================================
  Construyendo...
  STUB: esto es lo que hace force_build.py si la compilacion falla
  [ERROR] Fallo la compilacion. Revisa el log de PyInstaller.
rc de `cmd /c build.bat` = 0          <-- FALLO Propagado
```

**Contraste que demuestra que el `.bat` sabe hacerlo y aqui no lo hace:** el
mismo `build.bat`, con el fallback del paso 1 (validar PyInstaller) rechazado,
sale con **1**:

```
rc de build.bat con el paso 1 fallando = 1
  [ERROR] PyInstaller no esta instalado.
```

**`S3` — severidad MEDIA. No lo introduce TASK-076, pero TASK-076 lo pone en el
camino critico.** El `exit /b 0` ya estaba antes del cambio, cuando la linea 27
era la llamada directa a PyInstaller. Lo que cambia con este ciclo es que la
linea 27 pasa a delegar en un script de Python **cuyo codigo de salida es
informativo**, y ese codigo se tira. Un `if errorlevel 1`, un pipeline, un IDE o
el propio checklist del dueno que mire solo al codigo de salida dara por buena
una compilacion que no ocurrio. Lo que salva al humano es que el paso 4 imprime
`[ERROR] Fallo la compilacion`, y como el paso 2 borra el `.exe` previo, un
fallo deja el arbol sin `.exe`: **el fallo es visible en consola, invisible en
codigo de salida.** No hay ningun guard: `run_tests.py` no menciona `errorlevel`,
`exit /b` ni `LASTEXITCODE` en ninguna parte (busqueda literal, 0 coincidencias).

### 3.2 `release.yml` SI propaga el fallo — **medido contra la fuente del runner**

La asimetria con `build.bat` es real y va en el sentido correcto. En Windows, un
`run:` sin `shell:` usa `pwsh`, y el runner **antepone**
`$ErrorActionPreference = 'stop'` y **anade** al final del script
`if ((Test-Path -LiteralPath variable:\LASTEXITCODE)) { exit $LASTEXITCODE }`
(fuente: `actions/runner`, `Runner.Worker/Handlers/ScriptHandlerHelpers.cs`, y
la seccion "Exit codes and error action preference" de la referencia de
workflow-syntax). Como `release.yml:209` es **una sola sentencia**, nada
resetea `$LASTEXITCODE` despues, luego `force_build.py` saliendo con 1 **tumba
el paso y la release no se publica**. Ese es justo el criterio del encargo: el
`.exe` roto llega aldueño por el camino de `build.bat`, no por el de CI.

### 3.3 Las tres menciones de `--add-data` usan la misma forma — y el guard no acepta una forma rota

| Sitio | Forma literal |
|---|---|
| `force_build.py:16` | `"--add-data", "assets;assets",` |
| `docs/ai/sandbox-rules.md:32` | `--add-data assets;assets` (requisito en prosa, no codigo ejecutable) |
| `release.yml` / `build.bat` | **no la nombran**: delegan en `force_build.py` |

Lo que el predicado `_cubre` acepta y rechaza, ejecutado sobre el helper real
del repo (no reimplementado):

| Forma de `--add-data` | `pares` | ¿cubre `assets/process_db.json`? |
|---|---|---|
| `assets;assets` (la canonica) | `[('assets','assets')]` | **si** |
| `assets:assets` (forma POSIX) | `[]` | **no** |
| `assets` (sin separador) | `[]` | **no** |
| `assets;ASSETS` | `[('assets','ASSETS')]` | **no** |
| `assets;./assets` | `[('assets','./assets')]` | **no** |

**Conclusión medida: el guard NO aceptaría una forma que en Windows no
funciona.** La separacion POSIX `:` se rechaza (que es el error tipico al
copiar flags de la doc de PyInstaller), y `assets;assets` es la unica que pasa.
El `;` es el separador correcto en Windows y coincide en los sitios que lo
nombran. No hay hole aquí.

### 3.4 Los 7 guards antes del marcador headless: la clasificacion no los esconde — **MEDIDO por ejecucion**

`run_tests.py:27880-27886` invoca los 7 y el marcador
`print("\n--- Running Headless UI Tests ---")` esta en `:27887`. Que se
classifiquen como *backend* es correcto porque **no abren ventana**: leen texto,
usan `ast` y escriben a lo sumo en `%TEMP%`.

No es una convencion: **la linea base los ejecuta de verdad** y cada uno imprime
su `OK.` antes del marcador (log de la camara, lineas 213-228):

```
Probando que los flags de PyInstaller tienen una sola declaracion...
test_una_sola_declaracion_de_flags_de_pyinstaller OK.
Probando que los assets que lee la app llegan al ejecutable...
test_los_assets_que_lee_la_app_llegan_al_ejecutable OK.
Probando que la doc no vuelve a listar los flags...
test_la_doc_no_vuelve_a_re_listar_los_flags OK.
Probando que las citas por linea de sandbox-rules.md son ciertas...
test_las_citas_de_sandbox_rules_siguen_siendo_ciertas OK.
Probando que el .spec no vuelve a ser la fuente de verdad...
test_el_spec_no_vuelve_a_ser_la_fuente_de_verdad OK.
Probando que los guards de flags son de texto y no necesitan yaml...
test_los_guards_de_flags_no_necesitan_yaml_ni_ejecutan_nada OK.
Probando que la linea base de flags sale del fichero real...
test_la_linea_base_de_flags_se_deriva_del_fichero_real OK.

--- Running Headless UI Tests ---
```

Recuento derivado con `ast` del bloque `__main__` de `run_tests.py`
(`27583-28085`), con el marcador real localizado **dentro** de ese bloque
(linea 27887) y no en la copia sintetica de la linea 13947:

| | Derivado | Declarado en el codigo | |
|---|---|---|---|
| antes del marcador (backend) | **155** | 155 | coincide |
| desde el marcador (headless) | **65** | 65 | coincide |
| **total** | **220** | 220 | coincide |

Las 7 estan las 7 antes del marcador y las 7 invocadas.

---

## 4. Mutantes ejecutados

Todos sobre copias en `%TEMP%`, con git autocontenido dentro de la camara, con
`PYTHONDONTWRITEBYTECODE=1` + `PYTHONPYCACHEPREFIX` nuevo por corrida, y con la
**mutacion verificada en disco dos veces antes de correr** (`git status
--porcelain` la ve + lectura del texto nuevo y ausencia del viejo).

### 4.1 N1 · AC-2, el guard que discrimina

| id | Que rompi | Veredicto | Motivo LITERAL (pegado del log) |
|---|---|---|---|
| **M1a** | `force_build.py`: borrar la linea `"--add-data", "assets;assets",` (R2-a, **exactamente lo que hacia `build.bat:27` antes del ciclo**) | **killed** | `AssertionError: la app lee ['assets/process_db.json', 'assets/woptimizer.ico'] (`_data_dir()` es `sys._MEIPASS` en frozen, `config.py:11-14`) y la declaracion de `force_build.py` no cubre ['assets/process_db.json', 'assets/woptimizer.ico']: sus `--add-data` son []. Sin eso el ejecutable arranca sin base de datos de procesos y sin icono` — muere en `run_tests.py:27290`, la asercion de AC-2 |
| **M1b** | `"assets;assets"` -> `"assets;data"` (R2-b) | **killed** | el mismo `AssertionError`, con `sus --add-data son [('assets', 'data')]` |
| **M1c** | `"--add-data", "assets;assets"` -> `"--add-data", "assets"` (R2-c, sin `;destino`) | **killed** | el mismo `AssertionError`, con `sus --add-data` son `[]` |
| **M1d** | `_cubre(...)` empieza con `return True`: **el guard se vuelve tautologo** | **killed** | `AssertionError: mutante R2-b: empaquetar en `data` NO es cubrir `assets/`, porque es ahi donde `_data_dir()` lee. Un predicado que lo aceptaria estaria mintiendo` — muere en `run_tests.py:27303`, la contraprueba **interna**, sin tocar el fichero real |
| **M1N1** | **N1: vaciar el escaneo de `src/`** (`os.walk(... "NO_EXISTE_ESTA_CARPETA")`), que es la tautologia del encargo original | **killed** | `AssertionError: el escaner de src/woptimizer/** no ha encontrado NINGUNA ruta bajo assets/. Cero rutas que cubrir sale en verde sin medir nada: o el patron se ha roto, o la app ha dejado de leer a...` — muere en `run_tests.py:27280`, el `assert leidas` |

**Respuesta directa a la pregunta de N1 — ¿se puede vaciar el escaneo de `src/`
y seguir verde? NO.** M1N1 lo responde con la boca del disparo: el guard tiene
una *"Deteccion de CERO sobre CERO"* (`run_tests.py:27280`) que convierte "no
mire nada" en **rojo con motivo a la vista**, no en verde. Ese era el agujero que
el encargo temia y esta cerrado. Los cuatro mutantes mueren **por la asercion
que nombra la ruta leida** (`assets/process_db.json` y `assets/woptimizer.ico`),
no por un `ImportError` ni por un error de sintaxis: los 4 logs tienen
`tracebacks=1` y el ultimo frame es la linea de `assert` del guard.

### 4.2 N2 · AC-6, los guards son de TEXTO y no necesitan PyYAML

| id | Que rompi | Veredicto | Motivo LITERAL |
|---|---|---|---|
| **M2a** | Meter `import yaml` + `yaml.safe_load(...)` en el guard AC-1, **solo** para `release.yml` (R6-a: el error tipico) | **killed** | `AssertionError: test_una_sola_declaracion_de_flags_de_pyinstaller importa yaml: MEDIDO, las dev deps son `pytest` y `pyinstaller`, luego esto revienta en el job `verify` con ModuleNotFoundError` |

**El motivo importa y es el que hay que mirar.** La mutacion se escribio con
`yaml.safe_load(texto) if relativo.endswith(".yml") else None`, o sea **sin
producir ningun error visible**: AC-1 se sigue ejecutando y ACI-1 pasa. El rojo
llega despues, en AC-6 (`run_tests.py:27525`), que recorre con `ast` los SIETE
nombres de `GUARDAS_DE_LOS_FLAGS`. Eso es exactamente el modo de fallo que
justificaba el guard: **verde en el host, `ModuleNotFoundError` en el job
`verify`**, que es donde ya no se puede arreglar.

**Auditoria del resto de los guards por el mismo criterio:** recorrido `ast` de
las 7 funciones buscando `ast.Import`/`ast.ImportFrom`/`ast.Name`/`ast.Attribute`
con raiz `yaml` o `subprocess`, y con atributo en
`(system, popen, startfile, Popen, run, check_call, check_output, call)`.
**Ninguno de los 7 depende de parsear YAML ni de lanzar un proceso.** El unico
`open(..., "w")` que hay (AC-7) escribe en `tempfile.mkdtemp()`, o sea en
`%TEMP%`.

### 4.3 N3 · AC-1 y AC-3, los dos sitios que estaban ROTOS

| id | Que rompi | Veredicto | Motivo LITERAL |
|---|---|---|---|
| **M3a** | `build.bat:27` vuelve a declarar la lista de flags (R1-a, **el defecto original del ciclo**) | **killed** | `AssertionError: build.bat declara ['--onefile', '--noconsole', '--uac-admin', '--name', '--clean']: los flags viven en `force_build.py` y este fichero lo INVOCA. Una segunda lista es la que diverge sin avisar, y la divergencia que ya costo un `.exe` sin `assets/` era exactamente esta.` |
| **M3c** | `build.bat`: `python force_build.py` -> `force_build.py` a secas (R1-c) | **killed** | `AssertionError: build.bat tiene que invocar `python force_build.py`. En Windows `force_build.py` a secas no se ejecuta: el `.bat` necesita el interprete delante y el paso del workflow tambien.` — `run_tests.py:27224` (AC-1) |
| **M3d** | `docs/ai/sandbox-rules.md:24`: la seccion 2 vuelve a la lista CORTA sin `--add-data` (R3-a) | **killed** | `AssertionError: la seccion 2 vuelve a declarar ['--onefile', '--noconsole', '--uac-admin', '--name', '--clean'] como codigo ejecutable. Los flags viven en `force_build.py`; aqui se explica POR QUE se compila asi, y el ejemplo invoca ese fichero` — `run_tests.py:27342` (AC-3) |

### 4.4 N4 · AC-4, las cuatro afirmaciones que el validador NO puede ver

| id | Que rompi | Veredicto | Motivo LITERAL |
|---|---|---|---|
| **M4a** | Insertar una fila `` | `0` | ... | `` **por encima de la 55**, que es el R4-a descrito por el arquitecto: desplaza la tabla que citan las cuatro afirmaciones, y `_declara_el_codigo_sobrecargado` **no se pone rojo** | **killed** | `AssertionError: la linea 55 tiene que ser la fila del `0` que dice `WOPT_COMMIT_OK` y es '| `0` | Fila insertada por el mutante R4-a | x | y | z |'. Las cuatro afirmaciones la citan por numero` — `run_tests.py:27407` (AC-4) |

**Esta es la confirmacion medida del matiz del arquitecto.** El guard AC-4
muerte por **asercion de contenido** sobre las lineas 53-56 (cabecera con
"Significado", separador, fila `WOPT_COMMIT_OK`, fila `WOPT_NOOP`), no por
buscar la cadena `55-56` — que no cambiaria. Y como el guard corre **antes** del
validador en la secuencia, el rojo llega. Y `sandbox-rules.md` **sigue teniendo
1602 lineas** y las 55-56 siguen siendo las dos filas del `0` (§2.4).

### 4.5 N6 · AC-5, `woptimizer.spec` no puede ser la fuente de verdad

| id | Que rompi | Veredicto | Motivo LITERAL |
|---|---|---|---|
| **M6a** | `.gitignore`: quitar `*.spec` (aisla AC-5: nada mas mira esa linea) | **killed** | `AssertionError: `.gitignore` tiene que seguir sin versionar los `.spec`: si aparece el fichero en el checkout, el build de CI puede depender de un artefacto local y la premise de este cambio cambia` — `run_tests.py:27456` (AC-5) |
| **M6b** | `release.yml`: el job `build` compila con `python -m PyInstaller --spec woptimizer.spec --onefile ...` (R5-a literal) | **killed** | `AssertionError: .github/workflows/release.yml declara ['--onefile', '--spec']: los flags viven en `force_build.py` y este fichero lo INVOCA.` — `run_tests.py:27212`, **AC-1**, no AC-5 |

**Honestidad sobre M6b, que no midio lo que el encargo pedia.** Con `--spec` en
el workflow el test se pone rojo (que es lo que se pedia comprobar), pero **lo
mata AC-1 y no AC-5**, porque `--spec` esta en `FLAGS_QUE_SOLO_VIVEN_EN_FORCE_BUILD`
(`run_tests.py:27070`) y AC-1 corre antes (`:27880` frente a `:27884`). Por eso
añadi **M6a**, que si aísla AC-5 y muere por su propia asercion. Las dos rutas
estan cubiertas: reintroducir el `--spec` esta imposible (AC-1) y quitar el
`*.spec` del `.gitignore` tambien (AC-5).

**El `.spec` sigue sin versionarse — MEDIDO:**

```
git ls-files woptimizer.spec        -> ''            (rc 0, vacio)
git check-ignore -v woptimizer.spec -> .gitignore:29:*.spec	woptimizer.spec
el fichero EXISTE en el arbol del dueno: True
```

### 4.6 AC-7 · la linea base se deriva del fichero real (y el R7-a no se repite)

| id | Que rompi | Veredicto | Motivo LITERAL |
|---|---|---|---|
| **M7** | `_argumentos_de_pyiinstaller` ignora la ruta que se le pasa y lee siempre el fichero real | **killed** | `AssertionError: la derivacion de C:\Users\carch\AppData\Local\Temp\wopt_t076_linea_base_eg3aqljr\force_build.py ha dado la MISMA lista que la del fichero real (['sys.executable', '-m', 'PyInstaller', '--onefile', '--noconsole', '--uac-admin', '--name', 'woptimizer', '--clean', '--add-data', 'assets;assets', 'src/woptimizer/__main__.py']): eso significa que no lee el fichero que se le pasa, y un comparador que no lee no mide la linea base` — `run_tests.py:27578` |

Y el punto de N5c, confirmado por ejecucion y no por inspeccion: **M7 muere por
su `assert`, no por `NameError`.** El fallo de la primera pasada del dev
(`NameError: name '_tempfile' is not defined`) viene resuelto con
`import tempfile as _tempfile` en `:27568`, y el log lo demuestra: el traceback
apunta a `:27578`, que es la asercion, y no a la importacion. Ninguno de los 13
mutantes muere por `NameError`, `ImportError` ni error de sintaxis.

### 4.7 Resumen de los 13 mutantes: donde muere cada uno

| id | mutacion | guard | linea del `assert` | veredicto |
|---|---|---|---|---|
| M1a | `force_build.py` sin `--add-data` (R2-a) | **AC-2** | 27290 | **killed** |
| M1b | `assets;data` (R2-b) | **AC-2** | 27290 | **killed** |
| M1c | `--add-data assets` sin `;` (R2-c) | **AC-2** | 27290 | **killed** |
| M1d | `_cubre` devuelve `True` siempre | **AC-2** (contraprueba) | 27303 | **killed** |
| M1N1 | escaneo de `src/` vaciado | **AC-2** (cero sobre cero) | 27280 | **killed** |
| M2a | `import yaml` en un guard (R6-a) | **AC-6** | 27527 | **killed** |
| M3a | `build.bat` vuelve a listar flags (R1-a) | **AC-1** | 27212 | **killed** |
| M3c | `force_build.py` sin `python` (R1-c) | **AC-1** | 27224 | **killed** |
| M3d | doc seccion 2 vuelve a la lista corta (R3-a) | **AC-3** | 27342 | **killed** |
| M4a | fila `| 0 |` insertada sobre la 55 (R4-a) | **AC-4** | 27407 | **killed** |
| M6a | `.gitignore` sin `*.spec` | **AC-5** | 27456 | **killed** |
| M6b | `release.yml` compila por `--spec` (R5-a) | **AC-1** (no AC-5) | 27212 | **killed** |
| M7 | el derivador ignora la ruta (R7-a) | **AC-7** | 27578 | **killed** |

**13 de 13 muertos, cada uno por la asercion que su guard dice comprobar.** Los
cinco mutantes documentados por el propio dev (R1-a, R1-c, R2-a, R2-b, R2-c) y el
R3-a mueren por la puerta que el dev nombro, no por otra.

---

## 5. Supervivientes

**Ninguno.** No hay un solo `ALL TESTS PASSED` entre los 13 mutantes: los 13 logs
terminan en `AssertionError` con traceback.

Y mas importante para el criterio del encargo: **ninguno muere por el motivo
equivocado.** Los 13 tienen `tracebacks=1` y el ultimo frame `in test_...` cae
siempre en una linea de `assert` del guard que toca, nunca en una importacion ni
en un `compile`. La regla de lectura se cumple entera: sin logs truncados, sin
veredictos inventados.

---

## 6. N5 · Los dos defectos que el dev se reporto a si mismo

| Sub-punto | Resultado | Detalle |
|---|---|---|
| **a) Desplazamiento +1 en `sandbox-rules.md`** | **no hay hallazgo** | El fichero tiene **1602 lineas** medidas. Ni `STATUS.md`, ni `AGENTS.md` ni `README.md` **declaran ninguna cifra** de lineas de este documento, luego no existe desvase posible. El unico "1339" del repo (`run_tests.py:22199`, `docs/ai/testing-guide.md:1324`) es una afirmacion **en pasado** ("no mencionaba el CI en ninguna de sus 1339 lineas"): describe el estado *anterior* al arreglo de TASK-075. No es una mentira documental. Y el desplazamiento que el dev se reporto **esta cerrado por AC-4**, que es justo lo que mide M4a (§4.4). |
| **b) "tres erratas", una un identificador en chino y otra una palabra pegada** | **1 residuo, de un ciclo ANTERIOR** | Barrido de `U+FFFD`, mojibake (`Ã©`, `â€`, `Â`, `ï»¿`) y CJK (`U+4e00-9fff`, `U+ff00-9fef`) en `run_tests.py`, `validate_docs.py`, `sandbox-rules.md`, `build.bat`, `force_build.py`, `release.yml`, `STATUS.md`, `README.md`, `AGENTS.md`. **Cero** en los ocho ficheros que no son `run_tests.py`. En `run_tests.py`: **2 x U+FFFD**, ambos en la misma linea y **fuera de los 7 guards** → ver `S1`. **Ni el identificador chino ni la palabra pegada han quedado**: no hay CJK en ningun sitio. |
| **c) `NameError` de R7-a repetido en otros guards** | **no** | Recorrido `ast` de las 7 funciones: todo nombre en contexto de carga resuelve a definicion local, import, nombre de modulo o builtin → **0 sin resolver**. Y por ejecucion: los 13 mutantes mueren en una linea de `assert`, ninguno en una importacion. Un guard que muere por `NameError` en vez de por su asercion **no esta midiendo**, y aqui no hay ninguno asi. |

**`S1` — unico hallazgo de N5 (severidad BAJA, ciclo 64, no de TASK-076).**
`run_tests.py:14105`, en el docstring de
`test_la_deuda_exige_un_ancla_resoluble_en_toda_fila_viva` (TASK-075):

```
14105:  (`if any(c in registro ...)`), que es el agujero central que midi<U+FFFD><U+FFFD> el
```

Dos caracteres de reemplazo donde va un acento. Al estar en un docstring **no se
dispara al ejecutar** (no habria NameError ni excepcion): solo aparece al leer el
byte, que es exactamente la clase de residuo que se pedia buscar. **No afecta a
ninguno de los 7 guards de este ciclo.** No se repara aqui: no es mio.

---

## 7. VEREDICT

### 7.1 Tabla fix -> mutacion -> veredicto -> motivo

| Fix del ciclo | Mutacion | Veredicto | Motivo |
|---|---|---|---|
| AC-1 unicidad (una sola declaracion) | M3a `build.bat` re-declara flags / M3c sin `python` / M6b `--spec` en el workflow | **killed x3** | `27212` y `27224`, AC-1 |
| **AC-2 cobertura (el que discrimina)** | **M1a / M1b / M1c / M1d / M1N1** | **killed x5** | `27290` x3, `27303`, `27280` |
| AC-3 la doc no re-lista | M3d | **killed** | `27342` |
| AC-4 las 4 citas por linea | M4a | **killed** | `27407` |
| AC-5 el `.spec` no es la fuente | M6a | **killed** | `27456` |
| AC-6 texto, no YAML | M2a | **killed** | `27527` |
| AC-7 la linea base se deriva del fichero | M7 | **killed** | `27578` |

### 7.2 Lo que el guard mas importante hace y no hace

**Hace, y esta medido:** su expectativa sale de `src/woptimizer/**/*.py`, no de
`force_build.py`. Los tres defectos que dejaban el `.exe` sin assets (R2-a, R2-b,
R2-c) mueren nombrando las rutas que la app **lee** (`assets/process_db.json`,
`assets/woptimizer.ico`), y ese par de derivaciones es el que impide que el test
sea tautologo.

**Tambien esta medido — y es la pregunta de N1:** **no se puede vaciar el escaneo
de `src/` y quedarse en verde.** M1N1 (el escaneo apuntado a un directorio
inexistente) muere en el `assert leidas` con el motivo escrito. Y **tampoco se
puede volver tautologo el predicado**: M1d (`_cubre` siempre `True`) muere en su
propia contraprueba. El guard tiene dientes en los dos extremos.

### 7.3 Lo que este ciclo NO cubre (y hay que decirlo)

1. **`S3` (media): `build.bat` sale con 0 aunque `force_build.py` falle** (§3.1).
   Medido de extremo a extremo. Pre-existente, no introducido aqui, pero TASK-076
   lo deja en el camino critico de la fuente unica. **No hay guard.**
2. **El `.exe` de `dist/` ya compilado** no lo arregla un guard de codigo: el
   `.spec` lo declara asi y el guard no lo repara.
3. **`--add-data assets;assets` solo se ata por `_cubre` y por la lista literal
   de AC-7.** Ningun guard mide que PyInstaller en Windows lo interprete asi; se
   audito la coherencia de las tres menciones (§3.3) y es **coherente**, pero no
   se compilo para probarlo. El control del orquestador
   (exe de 26 MB con `process_db.json` y `woptimizer.ico` embebidos) es la unica
   prueba end-to-end, y es **del orquestador, no de la suite**.

---

## 8. Integrity del repo real — con una confesion

Huella TOMADA ANTES de mutar y comparada DESPUES:

| Clave | Resultado |
|---|---|
| `head` | **OK** — `bb33b5117efd404d9e2419499ac78f15c3efd479` |
| `reflog` | **OK** — la ultima entrada sigue siendo `bb33b51 HEAD@{2026-10-18 19:52:37}` |
| `refs` (todas) | **OK** — identicas |
| `count_objects` | **OK** — `891` sueltos, `2486` en pack, `3` packs: identico |
| `diff --stat` / `diff --cached --stat` | **OK** — ambos vacios |
| `git_dir` | **OK** — `%LOCALAPPDATA%\woptimizer_git\.git` |
| `status` | **DIFIERE, y esta explicado** — el unico cambio es `?? openspec/changes/2026-10-18-paridad-flags-pyinstaller/mutation-report.md`, que es **el informe de este encargo y el unico fichero que me estaba permitido escribir**. No esta comiteado. |
| mtime del **directorio** `.git` | **DIFIERE, y esta explicado** |

### 8.1 El mtime del directorio `.git`: explicado, no oculto

La diferencia de mtime **no es una escritura de historial**, y esta medido con
un experimento controlado sobre un repo espejo en `%TEMP%`:

```
repo espejo tras `git status --porcelain` (solo lectura):
  mtime del DIRECTORIO .git  antes=1792348453.020620  despues=1792348453.107640  CAMBIADO
  mtime de `index`            (no lo reescribe: el indice ya estaba al dia)
  ficheros tras el status: ['COMMIT_EDITMSG','HEAD','config','description',
                            'hooks','index','info','objects','refs']   (sin lock)
```

`git status` crea y borra `.git/index.lock`, y **eso** actualiza el mtime del
directorio. Lo hizo mi propio `fingerprint.py`, que corre `git status` para
tomar la huella. Ademas se descarto que fuera otra cosa: `ORIG_HEAD`, que es lo
que primero salio a la vista, tiene mtime **2026-10-08**, diez dias antes de esta
sesion, y ninguna de las 18 camaras de los mutantes tiene `ORIG_HEAD`. Ademas se
comprobaron uno a uno (`status`, `rev-parse --absolute-git-dir`, `for-each-ref`,
`count-objects`, `reflog`, `diff`, `log`, `check-ignore`) contra un repo espejo:
**ninguno crea `ORIG_HEAD`**. Y el `index` del repo real conserva su mtime de
`19:52:37`, el del commit.

### 8.2 CONFESION: escribi un fichero fuera de mi encargo y lo borre

Un `Set-Content` mio se quedo **antes** de un `cd` y creo
`C:\Users\carch\Nextcloud\Scripts\woptimizer\probe_og2.py` en la **raiz del repo
real**. Lo vi en el `git status` siguiente, lo borre con la via recuperable
(`rm --`, que lo llevo a la papelera) y volvi a comprobar:

```
git status --porcelain  ->  ?? openspec/changes/.../mutation-report.md
git rev-parse --short HEAD -> bb33b51
```

Queda **un unico cambio** en el repo real: el informe que me dijeron que
escribiera. No se comiteo nada, no se movio el HEAD, no se toco ningun fichero
de `src/`, ni `run_tests.py`, ni los docs, ni el workflow. **No se invoco
`.taskmaster/git_safe_commit.py` ni una sola vez**, y no se uso nunca
`checkout`, `reset`, `stash`, `clean` ni `restore` sobre el repo real.

---

## 9. VERDICT FINAL

# PASS

- Los **13 mutantes mueren**, cada uno por la asercion que su guard declara
  comprobar (linea de `assert` identificada en los 13). **0 supervivientes.**
- El guard central **AC-2 discrimina de verdad**: su expectativa sale de `src/`,
  y tanto sus tres mutantes de flags como los dos que la volverian tautologia
  (`_cubre` siempre `True`, escaneo de `src/` vacio) mueren.
- **No hay logs truncados ni "no medido"**: la regla de lectura se cumple en los
  13.
- No se repara nada de `src/`, ni de `run_tests.py`, ni de los docs, ni del
  workflow. Este informe es el unico cambio en el repo.

### Lo que un ciclo PASS **no** significa

`PASS` es "si el codigo estuviera mal, los tests se enterarian" para **los siete
guards de este ciclo**. No cubre lo que el ciclo no toco, y hay dos cosas
medidas que quedan fuera y que conviene no perder de vista:

1. **`S3` (media)** — `build.bat` no propaga el fallo de `force_build.py` (§3.1).
   Es el unico hallazgo con el producto en juego. Pre-existente, no introducido aqui,
   y **sin guard**: nadie mide hoy que el build local falle de verdad.
2. **`S1` (baja)** — dos `U+FFFD` en `run_tests.py:14105`, residuo de TASK-075
   en un docstring, invisible al ejecutar.

Ninguno de los dos lo introduce TASK-076, y ninguno lo he reparado: no es mio.