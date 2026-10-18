# Informe de auditoria de mutacion - TASK-077 (ciclo 66)

**Rol**: `mutation-auditor` · **HEAD esperado**: `17a9c55` · **HEAD medido**: `17a9c55`
**Suite**: `run_tests.py` = 224 tests (155 backend + 69 headless)
**Camara**: `%TEMP%\wopt_c66_f0974c2e`, con repo git **desechable propio** dentro
(`<camara>\.git`). El gitlink del repo real (`.git` = fichero de 57 bytes que
apunta a `%LOCALAPPDATA%`) **no se copio**; se excluyo con
`shutil.ignore_patterns(".git")`, que cubre ficheros y directorios, a diferencia de
`robocopy /XD`.

> **Informe incremental**: se escribe cada veredicto en cuanto existe, no al final.

---

## 0. Estado de partida de la camara (medido, no supuesto)

La copia limpia **no arranca la suite**: aborta en el test 28 de 224. Motivo
**ambiental**, no del codigo auditado:

```
AssertionError: git no resuelve `--absolute-git-dir` para C:\...\wopt_c66_f0974c2e
con el entorno limpio (rc=128, salida='fatal: not a git repository ...')
```

`test_la_puerta_de_paridad_va_despues_de_validar_repo` (y
`test_un_fallo_de_git_no_sale_con_cero`) llaman a `_entorno_git_del_repo()`, que
exige que la raiz del arbol resuelva `git rev-parse --absolute-git-dir`. Sin un
repo en la camara, esas sondas mueren por un motivo que no es el suyo y
**ningun mutante se podria leer**.

Arreglo de la camara (no toca el repo real, no toca codigo del producto):

1. `git init` **dentro** de la camara -> `.git` pasa a directorio real, propio y
   desechable. `commit --allow-empty`: HEAD existe sin preparar nada.
2. `git add -A` + commit: el indice paso de **0 a 252 ficheros** (el repo real
   tiene 256; la diferencia son ficheros ignorados que la copia no arrastra).
   MEDIDO que `git add` **no toco los bytes del arbol**: `build.bat` sigue con
   55 LF / 55 CR en disco tras el `add`, porque el filtro `clean` solo normaliza
   el blob del indice. Es justo por eso que los guards de bytes siguen siendo
   validos dentro de la camara.

Prueba de aislamiento (obligatoria antes de mutar nada):

```
absolute-git-dir: C:/Users/carch/AppData/Local/Temp/wopt_c66_f0974c2e/.git
dentro de la camara: True
worktree sucio (lineas): 0
reflog real mtime: 1792353553.8755703   (identico al de antes de empezar)
```

---

## 1. N1 - El `call` es load-bearing SI, pero **no** fue la causa de S3

### 1.1 La matriz medida

`build.bat` REAL + stub `python.cmd` con los bytes IDENTICOS a
`_dibujar_stub_de_python` (`run_tests.py:20461-20473`). Se mide el `errorlevel`
real de `cmd /c` **y que se imprime**, porque lo que cambia al quitar el `call`
del paso 3 no es el rc sino la salida.

| variante del `.bat` | stub sano (rc0 + crea exe) | stub sale 7 | stub sale 0 sin crear exe |
|---|---|---|---|
| **A** real, los dos `call` | rc=0, `Construyendo...` **si**, `[EXITO]` si | **rc=7**, `Construyendo...` si, `Fallo la compilacion` **si** | **rc=1**, `Construyendo...` si, `Fallo` si |
| **B** sin `call` en el **paso 1** | rc=0, **`Construyendo...` NO** | **rc=0**, **`Construyendo...` NO** | **rc=0**, **`Construyendo...` NO** |
| **C** sin `call` en el **paso 3** | rc=0, `Construyendo...` si, **`[EXITO]` NO** | **rc=7**, `Construyendo...` si, **`Fallo la compilacion` NO** | **rc=0**, `Construyendo...` si, **`Fallo` NO** |
| **D** sin ninguno | rc=0, `Construyendo...` NO | rc=0, `Construyendo...` NO | rc=0, `Construyendo...` NO |

**El `call` del paso 1 es load-bearing de forma dramatica:** sin el, el `.bat`
**nunca compila** y sale con **0 en las tres celdas**, incluso con el stub sano
que si crea el `.exe`. Compilar es un espejismo y el `.bat` dice "todo bien".
Eso es exactamente lo que el dev afirma.

**El `call` del paso 3 cambia el rc en UNA sola celda**, y no en la que el guard
mira: sin el, la celda "stub sale 7" **sigue dando 7** (el rc se cuela del shim).
Lo que delata al mutante es que **no se imprime** `Fallo la compilacion`. Un
guard que solo mirase el rc dejaria pasar ese mutante: medido, no supuesto.

### 1.2 La segunda afirmacion del dev: REFUTADA

El dev afirma que *"la medicion original de S3 (ciclo 65) daba 0 por el motivo
equivocado"*. **Medido: es falso en este host.**

**(a) En esta maquina el secuestro no puede ocurrir.** `where python`:

```
C:\Users\carch\AppData\Local\Programs\Python\Python313\python.exe
C:\Users\carch\AppData\Local\Microsoft\WindowsApps\python.exe
NINGUN python.cmd/python.bat en el PATH
```

`python` resuelve a `.exe`, y un `.exe` sin `call` **no** secuestra el control en
un `.bat`: `cmd` continua. El secuestro exige un `.cmd`/`.bat` delante en el
`PATH`, y aqui no hay ninguno. El riesgo es real en otras maquinas (shims de
conda/venv), pero **no es el caso de este host**.

**(b) El propio log del ciclo 65 desmente el secuestro.**
`openspec/changes/2026-10-18-paridad-flags-pyinstaller/mutation-report.md:193-202`
pega la salida **real**:

```
  Construyendo...                                         <-- LLEGO al paso 3
  STUB: esto es lo que hace force_build.py si la compilacion falla
  [ERROR] Fallo la compilacion. Revisa el log de PyInstaller.   <-- LLEGO a :fallo
rc de `cmd /c build.bat` = 0          <-- FALLO Propagado
```

Si el shim hubiera secuestrado el control, **`Construyendo...` y
`[ERROR] Fallo la compilacion` no se habrian impreso nunca**. Los dos estan. El
control volvio al `.bat`, se recorrio hasta `:fallo` y el `0` salio del
**`exit /b 0` incondicional** (`build.bat:40` segun aquel informe).

**Conclusion N1.** El `call` es un guard **legitimo y load-bearing** para el caso
que el test construye (un shim `.cmd` en el `PATH`), y la celda E lo mide bien.
Pero **el diagnostico del ciclo 65 era correcto y no hay que corregirlo**: el
`rc=0` lo producia el `exit /b 0`, no el `call` ausente. Lo que **si** queda mal
es el docstring de `run_tests.py:20512-20526`, que ata la frase *"MEDIDO de
extremo a extremo antes de este test"* (que es la medicion del ciclo 65) a la
afirmacion *"La causa era DOBLE"*. La mitad del `call` es cierta; **atribuirla a
esa medicion es lo que no se sostiene**.

---

## 2. N2 - Los 8 mutantes del dev (E1-E5, S1-S3) y la contraprueba

**Metodo.** Baseline: `ALL TESTS PASSED.` (28 937 bytes, 392 lineas), con los
**cuatro** guards de TASK-077 ejecutados. Los mutantes `E1`, `E2` y `E3` se
midieron con la **suite COMPLETA**; el resto con un **corredor dirigido** que
corta el bloque `__main__` de `run_tests.py:28194` y vuelve a llamar solo a los
cinco guards auditados, generados desde el `run_tests.py` **ya mutado**. El
codigo de los guards es byte a byte el del repo mutado; lo que se quita son las
llamadas a tests que no se estan auditando.

### 2.1 Tabla de veredictos

| Id | Que se rompio | Veredicto | Motivo literal |
|---|---|---|---|
| **E1** | borrar `*.bat text eol=crlf` de `.gitattributes` | **MUERE** | `run_tests.py:20347` `assert not fallos` - `cobertura: build.bat esta presente y su regla efectiva es 'lf', no 'crlf'` |
| **E2** | `build.bat` a LF en disco (el que estaba VIVO) | **MUERE** | `run_tests.py:20347` - `bytes: build.bat no tiene ni un CRLF (tiene 55 LF y 0 CR)` + `55 LF SUELTOS` |
| **E3** | CR duro a media linea en `build.bat` | **MUERE** | `run_tests.py:20347` - `normalizado: build.bat conserva un CR DURO tras normalizar... es la clase 3012c48` |
| **E4** | resolvedor de atributos -> constante `crlf` | **MUERE** | `run_tests.py:20277` `assert base == "lf"` - `deriva a 'crlf'`. **Y tambien en F3.2 aislado**: `run_tests.py:20277` |
| **E5** | evaluador de F3.1 vaciado (`return []`) | **MUERE** | `run_tests.py:20400` `assert veredicto_mal` - `un .bat en LF tiene que dar FAIL y el evaluador dio OK` |
| **S1** | `exit /b 0` incondicional al final | **MUERE** | `run_tests.py:20554` `assert r.returncode == 7` - `devolvio 0. Un .bat que devuelve 0 cuando la compilacion fallo es exactamente el bug` |
| **S2** | camara que acepta cualquier codigo de salida | **MUERE** | `run_tests.py:20554` y, en F4.2 aislado, `run_tests.py:20718` `assert r.returncode == 7` - `el .bat SANO, con el mismo stub y en la misma camara, tiene que dar 7 y dio 0` |
| **S3** | borrar el `if errorlevel 1` del paso 1 | **SOBREVIVE** | `ALL GUARDS PASSED.` - ver §2.3 |
| **N3x** | *propio*: homonimo CRLF tapa un `build.bat` en LF | **SOBREVIVE** | `ALL GUARDS PASSED.` - ver §3.3 |
| **N4a** | borrar `basura/` de `.gitignore` | **MUERE** | `run_tests.py:20339` - `basura/ no esta en .gitignore pero este guard lo EXCLUYE... Excluir sin que el .gitignore lo diga es dejar de mirar ficheros sin avisar` |
| **N4b** | sacar `basura` de `_DIRECTORIOS_FUERA_DE_LA_POLITICA` | **MUERE** | `run_tests.py:20347` - `bytes: commit_version.bat no tiene ni un CRLF (tiene 55 LF y 0 CR)` |
| **N5a** | fila `| 0 |` insertada por encima de la 55 | **MUERE** | `run_tests.py:28018` - `la linea 55 tiene que ser la fila del 0 que dice WOPT_COMMIT_OK` |
| **N5b** | fila `| 0 |` insertada por encima de la 53 | **MUERE** | `run_tests.py:28013` - `la linea 53 tiene que ser la cabecera de la tabla de codigos` |
| **N5c** | una linea insertada antes de la cita `run_tests.py:22875` | **MUERE** | `run_tests.py:28037` - `run_tests.py:22875 ya no cita sandbox-rules.md:55-56` |

**7 de los 8 del dev mueren. 1 sobrevive: `S3`.**

### 2.2 Todas las muertes son por la asercion del guard que toca

Ninguna por `FileNotFoundError`, `NameError`, `ValueError` ni sintaxis. Y cada
una muere en una **asercion distinta**, lo que demuestra que el guard discrimina
las tres afirmaciones que dice medir y no una sola:

- E1 muere por **cobertura** (`la regla efectiva es 'lf', no 'crlf'`).
- E2 muere por **bytes** (`no tiene ni un CRLF`).
- E3 muere por **normalizado** (`conserva un CR DURO`).

### 2.3 S3 SOBREVIVIO, y **no es equivalente**

`test_build_bat_propaga_el_codigo_de_salida_de_force_build` celda D (mutante S3)
exige `assert r.returncode != 0` con PyInstaller ausente. **Medido**, con el
stub que sale 1 siempre:

| variante | rc | `.exe` previo | mensaje |
|---|---|---|---|
| **`build.bat` sano** | 1 | **SOBREVIVE** | `[ERROR] PyInstaller no esta instalado` + `pip install -e ".[dev]"` |
| **mutante S3** (sin el `if errorlevel 1`) | 1 | **DESTRUIDO** | `[ERROR] Fallo la compilacion. Revisa el log de PyInstaller.` |

Sin el chequeo del paso 1, el **paso 2 se ejecuta** (`if exist
"dist\woptimizer.exe" del /f /q`) y **borra el `.exe` que ya funcionaba**; despues
la compilacion falla y el `.bat` se va por `:fallo`. El asercion `rc != 0` lo
cumple **igual**: por eso el guard no lo caza. Lo que cambia es (a) el mensaje,
que pasa de accionable a **falso** (no hay log de PyInstaller que mirar, no hay
PyInstaller), y (b) que el usuario se queda **sin ejecutable**.

**Arreglo**: la celda D tiene que afirmar tambien lo que la distingue - que la
salida contenga `PyInstaller no esta instalado`, o que un `.exe` preexistente
sobreviva. El test ya dispone de `r.stdout` y ya afirma sobre el texto en la
celda A (`assert "EXITO" not in r.stdout`), luego el patron esta a mano.

### 2.4 Trampa de medicion: anadir lineas a `run_tests.py` falsea veredictos

MEDIDO: **cualquier mutacion que anada lineas a `run_tests.py` mueve la cita
`run_tests.py:22875`**, y entonces el mutante muere por
`test_las_citas_de_sandbox_rules_siguen_siendo_ciertas`, que es la asercion de
**otro** guard:

```
AssertionError: run_tests.py:22875 ya no cita `sandbox-rules.md:55-56`
```

Mis dos primeras versiones de `E5` y `S2` salieron asi: las dos
murieron con ese `AssertionError`, que es un **veredicto falso** -
dos muertos que no existen.
`AssertionError`, que es un **veredicto falso** - dos muertos que no existen.
Rehechas conservando el numero de lineas, cada una muere por **su** asercion
(`E5` en `20400`, `S2` en `20718`). A cualquiera que mida sobre `run_tests.py` le
va a pasar: hay que contar las lineas del mutante o se cuentan muertos falsos.

### 2.5 El control positivo de S2 **existe y mide**

Medido en F4.2 aislado (`WOPT_GUARDS=4`): el mutante S2 muere en
`run_tests.py:20718`, que es exactamente la celda de CONTROL POSITIVO que el dev
dice haber anadido, con su motivo literal. **La afirmacion se sostiene.**

## 3. N3 - El guard de bytes y su limite conocido

### 3.1 (a) Es un guard de BYTES de verdad

MEDIDO leyendo el evaluador, no por comentario: `_fallos_de_politica_eol`
(`run_tests.py:20247`) abre cada script **en binario** y cuenta
`b"\r\n"`, `datos.count(b"\n")` y `datos.replace(b"\r\n", b"").count(b"\r")`.
`.gitattributes` se lee como **texto plano** (`run_tests.py:20174`), no con
`git ls-files --eol`. El riesgo que el arquitecto senalo - que en CI
`actions/checkout` ya aplico los atributos y ese comando daria `w/crlf` este sano
o no el repo, o sea un **verde falso** - queda **realmente** sorteado: este guard
depende de lo que hay en disco, no de como hizo el runner su checkout.

Corroboracion independiente: el unico `w/crlf` del repo es `build.bat`
(`attr/text eol=crlf`), y en disco esta en **CRLF PURO**: 55 CRLF, 55 LF,
**0 LF sueltos y 0 CR duros** (`.gitattributes` regido, `run_tests.py`,
`sandbox-rules.md`, los dos `CHANGELOG.md` y `tasks.json`: **LF PURO**, 0 CR).

### 3.2 (b)Puede el guard dar `OK` con un repo roto?

Las tres degradaciones que pregunta el encargo, una a una:

| Degradacion | El guard cae? | Por que |
|---|---|---|
| `build.bat` desaparece del arbol | **SI** | `run_tests.py:20325` exige `"build.bat" in presentes`: sin el, la afirmacion sobre bytes se queda sin sujeto |
| Se borra la regla `*.bat eol=crlf` | **SI** | `run_tests.py:20339` exige que `*.bat` este en el `.gitignore`... no: el mutante **E1** lo mata por cobertura (`run_tests.py:20240`), y **E5** (evaluador vaciado) lo mata en F3.2 |
| El evaluador devuelve `OK` por defecto | **SI** | **E5**: los tres escenarios de F3.2 darian OK y las dos aserciones del test caen |

Las tres estan **cubiertas por asercion propia**, no de rebote: no es accidental
que E1 y E4 las maten, hay un `assert` dedicado a cada degradacion.

### 3.3 Hallazgo propio: el guard indexa por NOMBRE, no por ruta

`_fallos_de_politica_eol` (`run_tests.py:20236`) acumula
`presentes[nombre] = os.path.join(dirpath, nombre)`: un **diccionario por
basename**. Con dos `.bat` homonimos en arboles distintos, el **ultimo que
recorre `os.walk` pisa al primero** y el primero **deja de mirarse**.

Medido como mutante `N3x` (§2, fila `N3x`): un `build.bat` en **CRLF** en un
subdirectorio **tapa** un `build.bat` en **LF** en la raiz, y el guard da **OK**.
Es un agujero real y del mismo genero que los que este repo ya ha pagado
("dato derivado escrito a mano"), aunque de gravedad baja: exige que alguien
meta un `.bat` con el mismo nombre en un subdirectorio.

## 4. N4 - `basura/commit_version.bat` y la exclusion ciega

MEDIDO en el repo real antes de mutar:
- `.gitignore` tiene la regla **desnuda** `basura/`.
- `basura/commit_version.bat` esta en **LF PURO**: 1344 bytes, **55 LF, 0 CR**.

El guard no se apoya en una lista escrita a mano: contrasta la exclusion contra
el `.gitignore` real dentro del propio test (`run_tests.py:20334-20344`).

| Mutante | Que se rompe | Veredicto |
|---|---|---|
| **N4a** | borrar la linea `basura/` de `.gitignore` | §2 |
| **N4b** | `basura` sale de `_DIRECTORIOS_FUERA_DE_LA_POLITICA` | §2 |

## 5. N5 - P2: las citas de `sandbox-rules.md` atadas por numero de linea

`test_las_citas_de_sandbox_rules_siguen_siendo_ciertas` ata cuatro afirmaciones
por numero de linea: `validate_docs.py:1429`, `validate_docs.py:1924`,
`run_tests.py:22875` y `docs/ai/sandbox-rules.md:1133`, las cuatro citando
`sandbox-rules.md:55-56`.

Estado **hoy**, medido: `run_tests.py:22875` contiene literalmente
`` `validate_docs.py` cita `sandbox-rules.md:55-56` POR NUMERO DE LINEA ``, y
`sandbox-rules.md:55-56` son las dos filas del `0` (`WOPT_COMMIT_OK` y
`WOPT_NOOP`) con la cabecera en la 53. **Esta estable ahora** en los dos
sentidos: la tabla y la cita se corresponden, y el test que las comprueba
(`test_las_citas_de_sandbox_rules_siguen_siendo_ciertas OK.`) paso limpio en la
baseline.

El punto debil que el propio guard declara es otro: la cita de
`run_tests.py:22875` es **autorreferente**. Cada linea que se anada a
`run_tests.py` por encima de la 22875 la desplaza, y eso ya paso DOS VECES en
este ciclo (`22264` -> `22730` -> `22875`). Medido como **N5c**.

Nota sobre el limite, para que no se lea como un agujero que el guard cubre: la
ultima asercion (`min(posiciones) > 61`) **no** detecta una fila insertada por
encima de la 61, porque mover la seccion hacia abajo **mantiene** el `> 61`. Lo
que detecta el desplazamiento de las citas son las cuatro aserciones de
**contenido** de las lineas 53-56.

## 6. N6 - Lo que `.gitattributes` dice ahora sobre el POR QUE

### 6.1 (a) El texto nuevo vuelve a mentir? En la sustancia, NO. En un detalle, SI.

La tesis del documento (`.gitattributes:22-33`) es *"NO porque `cmd.exe` se rompa
con LF"*. **Es cierta y la he vuelto a medir con `cmd.exe` de verdad:**

| escenario | rc con CRLF | rc con LF | stdout identico |
|---|---|---|---|
| sano (rc 0 + crea `.exe`) | 0 | 0 | si |
| compilacion falla con 7 | 7 | 7 | si |
| rc 0 pero sin crear el `.exe` | 1 | 1 | si |

Y las tres formas que el doc nombra por su sintaxis, en **LF puro**:

```
if errorlevel 1 ( multilinea   [CRLF] rc=1 out='FALLO'   [LF] rc=1 out='FALLO'
if exist (...) else (...)      [CRLF] rc=0 out='EXISTE'  [LF] rc=0 out='EXISTE'
goto :etiqueta                 [CRLF] rc=0 out='LLEGUE'  [LF] rc=0 out='LLEGUE'
```

**PERO el mismo parrafo (`:26-28`) afirma:** *"`build.bat` no acaba en `0x0A`,
su ultimo byte es `0x30`"*. **Medido: el ultimo byte de `build.bat` es `0x31`**,
el `1` de `exit /b 1` de la linea 56. El `0x30` era cierto del `.bat`
**anterior**, que terminaba en `exit /b 0`: **el propio arreglo del dev cambio
el byte que su documento cita como prueba.** El documento afirma una medida
sobre un fichero que el mismo ciclo movio, y no se reviso. No rompe el
`cmd.exe` (verificado arriba: el fichero no acaba en `0x0A`, que es lo que el
doc quiere decir), pero el digito es falso.

### 6.2 (b) Explica por que `checkout-index --renormalize` NO funciona

**Si**, y es la parte mas cara que salio descubrir (`.gitattributes:43-51`):
`eol=crlf` actua en el **CHECKOUT** y `git add` **nunca** escribe en el arbol de
trabajo, luego `--renormalize` deja 0 ficheros staged y el fichero sigue en LF;
`-f` a secas **no** reescribe un fichero que git considera limpio (el filtro
`clean` normaliza CRLF->LF, el resultado coincide con el indice y git no lo
toca), y la via que funciona es `git checkout-index -f --temp -- <f>` mas un
`os.replace` encima.

## 7. N7 - Las trampas que el dev reporto de si mismo

### 7.1 (a) `tasks.json` en CRLF tras editarlo con `json.dump`

**MEDIDO en disco: NO quedo en CRLF. El arreglo del dev funciona.**

| fichero | CRLF | LF | LF sueltos | CR duros | veredicto |
|---|---|---|---|---|---|
| `.taskmaster/tasks.json` | **0** | 1747 | 1747 | **0** | **LF PURO** |
| `.taskmaster/CHANGELOG.md` | 0 | 3068 | 3068 | 0 | LF PURO |
| `CHANGELOG.md` | 0 | 1576 | 1576 | 0 | LF PURO |
| `build.bat` | **55** | 55 | **0** | **0** | **CRLF PURO** |
| `run_tests.py` | 0 | 28715 | 28715 | 0 | LF PURO |
| `.gitattributes` | 0 | 64 | 64 | 0 | LF PURO |
| `docs/ai/sandbox-rules.md` | 0 | 1701 | 1701 | 0 | LF PURO |

El desperfecto que este ciclo vino a cerrar (indice con blob LF y arbol con
fichero CRLF) **no esta**: no hay ni un CR duro ni un LF suelto en ninguna parte
del conjunto regido por `.gitattributes`.

### 7.2 (b) El helper que pisaba los mutantes con el fichero sano

**Verificado.** `_dibujar_build_bat` (`run_tests.py:20477-20487`) esta partido
en dos a proposito y **solo** copia el `build.bat` real; el helper del stub,
`_dibujar_stub_de_python` (`run_tests.py:20443-20474`), **no toca el `.bat`** y lo
declara en su docstring. Las tres celdas que necesitan el mutante en disco usan
el helper del stub y escriben el `.bat` ellas mismas (`:20647`, `:20714`,
`:20728`). El helper de mi harness hace lo mismo: **compara el fichero en disco
con lo que dice haber escrito** antes de correr, y no corre si no coincide.

### 7.3 (c) `U+FFFD` / mojibake / CJK

| fichero | U+FFFD | CJK/Hangul | mojibake |
|---|---|---|---|
| `run_tests.py` | **0** | **0** | **0** |
| `.gitattributes` | **0** | **0** | **0** |
| `build.bat` | **0** | **0** | **0** |
| `docs/ai/sandbox-rules.md` | **0** | **0** | **0** |
| `validate_docs.py` / `.gitignore` / ambos `CHANGELOG.md` / `tasks.json` / `STATUS.md` / `proposal.md` / `tasks.md` del ciclo | 0 | 0 | 0 |

Los **2 `U+FFFD` que el ciclo 65 dejo en `run_tests.py:14105` ya no estan.** Los
cuatro ficheros del encargo estan limpios.

**Hallazgo lateral, FUERA de este ciclo:** `CHANGELOG.md:26` (bloque **CYCLE-064**)
tiene 2 silabas **hangules** que mi barrido de CJK marco: `U+C790` (HANGUL JA) y
`U+B3D9` (HANGUL DONG), dentro de *"la automatizaci?n"*. Residuo de un copiado desde
coreano, no de TASK-077. Severidad **baja**, no lo arregla este ciclo.

---

## 8. Hallazgos, por severidad

### 8.1 ROJO - La suite esta ROJA en el repo real, en HEAD `17a9c55`

`python run_tests.py` **falla**. No es un artefacto de la camara: el test
`test_el_journal_ilegible_informa_envez_de_reventar_el_validador`
(`run_tests.py:13476`) exige `len(errors) == 1` y recibe **2**:

```
['.taskmaster/rd_journal.json: ESTA CORRUPTO. ...',
 'STATUS.md Deuda fila 75: VIVA y su UNICA fuente es una TAREA YA CERRADA:
  TASK-077.status == completed']
```

**Causa raiz, MEDIDA y no supuesta.** `STATUS.md:75`, la fila que **anadio este
ciclo**, se ancla en `build.bat`. `_copiar_el_esqueleto_del_validador`
(`run_tests.py:13169-13171`) copia una lista fija de ficheros y **`build.bat` no
esta en ella**. En el arbol real la ruta resuelve y la fila se exime; en la
fixture no resuelve, la unica fuente que le queda es `TASK-077`, que esta
`completed`, y salta `validate_docs.py:2248` (`fuentes == ["tarea"] and not
tareas_vivas`).

Prueba directa, con el validador real sobre el arbol entero:

```
[build.bat PRESENTE]   errores=159 | fila 75=0
[build.bat AUSENTE]    errores=160 | fila 75=1
   STATUS.md Deuda fila 75: VIVA y su UNICA fuente es una TARETA YA CERRADA
   -> HIPOTESIS CONFIRMADA
```

**Por que el ciclo no lo vio**: el `AssertionError` mata el proceso en el test
~150 de 224, y los **cuatro guards de TASK-077 se llaman despues**
(`run_tests.py:28711-28714`). Es decir: **la tarea 1 del cierre del ciclo
("`python run_tests.py` -> verde") no se cumplio**, y los guards nuevos nunca se
ejecutaron en la suite completa.

**Arreglo**: anadir `build.bat` a la tupla `ficheros` de
`_copiar_el_esqueleto_del_validador`, o reescribir la fila 75 para que no dependa
de una ruta que la fixture no copia.

### 8.2 ALTO - `S3` sobrevive y NO es equivalente

Ver 2.3. Sin el `if errorlevel 1` del paso 1, el `.bat` borra el `.exe` que ya
funcionaba y devuelve un motivo falso, y el guard lo da por bueno porque solo
mira `rc != 0`. Toca datos del usuario (el ejecutable), no solo el codigo.

### 8.3 MEDIO - El guard de EOL indexa por BASENAME: puede dar OK con un repo roto

Ver 3.3 y el mutante `N3x`: un `build.bat` en CRLF en un subdirectorio **tapa**
un `build.bat` en LF en la raiz y el evaluador devuelve `[]`. Medido:

```
raiz build.bat   : 2199 bytes, LF = 55 CR = 0     <- incumplidor, no se mira
subdir build.bat :   30 bytes, LF =  2 CR = 2     <- sano, lo pisa
fallos del evaluador: []
VEREDICTO DEL GUARD : OK (verde FALSO)
sin el homonimo, fallos: ['bytes: build.bat no tiene ni un CRLF ...']
```

**Arreglo**: indexar por ruta relativa, no por basename.

### 8.4 MEDIO - `.gitattributes` cita un byte que su propio ciclo cambio

Ver 6.1: el documento afirma que el ultimo byte de `build.bat` es `0x30`; es
`0x31`. El `0x30` era del `.bat` anterior.

### 8.5 BAJA - `CHANGELOG.md:26` tiene dos silabas hangules

`U+C790` (HANGUL JA) y `U+B3D9` (HANGUL DONG) dentro de *"la automatizaci?n"*,
en el bloque **CYCLE-064**. Residuo de un copiado desde coreano. No es de este
ciclo.

### 8.6 P2 (deuda declarada, no tocada) - las citas por numero de linea

Ver 5: estable hoy, y `N5c` demuestra que se rompe **ruidosamente** (rojo, con el
motivo literal). No es un verde falso: es una bomba de mantenimiento que ya ha
explotado dos veces en este ciclo.

---

## 9. Estado de la camara y del repo real

La camara termino **byte a byte igual al repo real** en los 10 ficheros
verificados (`build.bat`, `.gitattributes`, `.gitignore`, `force_build.py`,
`validate_docs.py`, `sandbox-rules.md`, `STATUS.md`, `CHANGELOG.md`,
`tasks.json`, `rd_journal.json`), con **una sola** diferencia deliberada:
`run_tests.py` lleva **+13 bytes** en la camara, que son exactamente
`, "build.bat")` - el parche de la fixture de 8.1, sin el cual la suite no
llegaria a los guards auditados.

**Verde final, suite COMPLETA, DESPUES de los 13 mutantes y de restaurar entre
ellos:**

```
SIZE=28787 bytes  LINEAS=388
--- ULTIMA LINEA ---
ALL TESTS PASSED.
Probando que las citas por linea de sandbox-rules.md son ciertas...
Probando que la politica EOL cubre los scripts de consola que existen...
Probando que el guard de EOL rechaza lo mismo que acepta...
Probando que build.bat propaga el codigo de salida de force_build...
Probando que la camara de build.bat detecta la regresion...
```

Los cinco guards auditados se ejecutaron en la corrida completa.

Las tres camaras usadas tienen **`.git` propio y desechable**, y el aislamiento
se probo antes de mutar nada:

```
absolute-git-dir: C:/Users/carch/AppData/Local/Temp/wopt_c66_f0974c2e/.git
dentro de la camara: True
```

El `.git` del repo real es un **fichero** de 57 bytes
(`gitdir: C:/Users/carch/AppData/Local/woptimizer_git/.git`) y **no se copio** a
ninguna camara: se excluyo con `shutil.ignore_patterns(".git")`, que cubre
ficheros y directorios, a diferencia de `robocopy /XD`, que es como se han
contaminado las dos veces anteriores.

**Prueba de no-contaminacion del repo real, al terminar:**

```
reflog : termina en 17a9c55, mtime 2026-10-18T19:59:13.8755702Z (sin cambio)
indice : mtime 2026-10-18T20:00:13.1419064Z (sin cambio)
.git   : sigue siendo el fichero de 57 bytes
ficheros del repo con mtime posterior a mi inicio:
  openspec\changes\2026-10-18-eol-real-y-exit-de-build\mutation-report.md
```

**Fichero escrito en el repo**: solo este informe. **No se ha hecho ningun
commit, ni `checkout`, ni `reset`, ni `stash`, ni `clean`, ni `restore`, ni se ha
invocado `git_safe_commit.py` ni una vez.**

---

## 10. VERDICT: **FAIL**

**7 de los 8 mutantes del dev mueren, y 1 sobrevive: `S3`.** No es un mutante
equivalente - medido: sin el `if errorlevel 1` del paso 1, `build.bat` **borra el
`.exe` que ya funcionaba** y devuelve un motivo falso, y el asercion
`assert r.returncode != 0` lo acepta igual. Eso es exactamente el criterio de
entrada: *si queda algo que se manifestaria si el codigo o el doc estuvieran
mal, es FAIL*.

Se anade un segundo superviviente propio, `N3x`, por el mismo motivo: el guard
puede devolver `OK` con un `.bat` en LF en la raiz si hay un homonimo sano en un
subdirectorio.

**No es PARTIAL**: todas las comprobaciones obligatorias se han ejecutado y
tienen veredicto. Es **FAIL**, y no por los mutantes del dev en si - E1 a E5 y
S1, S2 mueren todos por la asercion correcta, incluido el control positivo de
S2, que existe y mide - sino porque **S3 sobrevive sin ser equivalente** y porque
la **suite esta roja en el repo real** y nadie lo vio.

### Lo que el dev acierta y lo que no

| Afirmacion del dev | Veredicto |
|---|---|
| E1-E5 y S1, S2 mueren (7 de 8) | **CIERTA** |
| "8 de 8 mueren" | **FALSA**: S3 sobrevive |
| E2 era el mutante vivo y ahora muere | **CIERTA** (muere por `bytes`, no por cobertura) |
| S2 lo mata el control positivo que anadio | **CIERTA** (`run_tests.py:20718`, verificado en aislamiento) |
| El `call` no es cosmetico | **CIERTA en su caso** (medido), pero **no** fue la causa de S3 |
| La medicion del ciclo 65 daba 0 "por el motivo equivocado" | **FALSA** |
| El guard contrasta la exclusion de `basura/` contra el `.gitignore` real | **CIERTA**: `N4a` y `N4b` mueren, en las dos direcciones |
| El guard de EOL es de bytes, no de `git ls-files --eol` | **CIERTA**, con el limite de `N3x` |
| Las 4 citas de `sandbox-rules.md` estan estables | **CIERTA hoy**; rompen con ruido (rojo), no en silencio |
| `tasks.json` quedo en LF | **CIERTA** (0 CR, 0 CRLF, 1747 LF) |
| Sin residuos U+FFFD / mojibake / CJK | **CIERTA en los cuatro ficheros del encargo**; hay 2 hangules en `CHANGELOG.md:26`, de CYCLE-064 |
| `run_tests.py` en verde | **NO SE CUMPLIO**: ver 8.1 |

### El punto que el encargo mandaba no suavizar

**El diagnostico del ciclo 65 era CORRECTO y no hay que corregirlo.** El `call`
es un guard legitimo y load-bearing para el caso que el test construye (un shim
`.cmd` en el `PATH`), y la celda E lo mide bien: sin el `call` del paso 1 el
`.bat` no compila nunca y sale con **0 en las tres celdas**. Pero en **este**
host `python` resuelve solo a `python.exe` y no hay ningun `python.cmd`/`.bat` en
el `PATH`, luego el secuestro no puede ocurrir aqui; y el log del ciclo 65
(`2026-10-18-paridad-flags-pyinstaller/mutation-report.md:193-202`) pega una
salida en la que `Construyendo...` y `[ERROR] Fallo la compilacion` **si** se
imprimieron: el control volvio al `.bat` y el `0` vino del `exit /b 0`
incondicional. El dev no invento el bug del `call`; lo que hizo fue **atribuirle**
el sintoma que ya estaba medido y explicado. Lo que habria que corregir es el
docstring de `run_tests.py:20512-20526`, que ata la frase *"MEDIDO de extremo a
extremo antes de este test"* (que es la medicion del ciclo 65) a la afirmacion
*"La causa era DOBLE"*.


---

# PARTE 2 -- REPARACION (openspec-dev, 2026-10-18)

El veredicto de arriba es **FAIL** y no se ha tocado: este apartado **anade**, no
reescribe. Lo que hace es cerrar los tres huecos que el informe abrio (8.1 rojo,
8.2 `S3` superviviente, 8.3 `N3x`, 8.4 la cita del byte) y dejar measured por que
cada arreglo esta sujeto por un mutante que muere.

## 11. Que estaba roto y que se arrglo

| # | Hueco | Arreglo | Fichero |
|---|---|---|---|
| R1 | suite **ROJA** en `17a9c55` | `build.bat` entra en el esqueleto del validador | `run_tests.py:13186` |
| R2 | `S3b` sobrevivia y **no era equivalente** | precondicion antes de borrar + 3 salidas, una por causa | `build.bat` |
| R3 | `N3x` indexaba por `basename` | indice por **ruta relativa** | `run_tests.py:20241-20270` |
| R4 | `.gitattributes` cita un byte falso | digito derivado y **guard** que lo contrasta | `.gitattributes:27-36` |

**R1.** `_copiar_el_esqueleto_del_validador` copia una lista fija de ficheros y
`build.bat` no estaba. `STATUS.md:75` --la fila que anadio el ciclo 66-- se ancla
en ese fichero: en el arbol real la ruta resuelve y la fila queda eximida, en la
copia NO resuelve, se queda con `fuentes == ["tarea"]` y `TASK-077` ya cerrada, y
salta `validate_docs.py:2248`. Firma: `run_tests.py` rojo y `validate_docs.py` en
0 FAIL, que es la combinacion que hace creer que el problema es del comando.

**Antes de anadirlo se MIDIO que no falta solo ese**, porque el encargo manda
ensanchar y no solo tapar: se paso por el validador real la lista completa de
ficheros de raiz, uno a uno. `build.bat` fue el **UNICO** que resuelve un error de
mas (1) y no introduce ninguno (0). Los otros ocho candidatos --`force_build.py`,
`run.py`, `verify_ui_syntax.py`, `pyproject.toml`, `woptimizer.spec`,
`.gitattributes`, `.gitignore`, `requirements.txt`-- deram 0 errores resueltos y 0
nuevos. El ensanchado se hizo con esa medida.

**R2.** Lo que el auditor medio era exacto: sin el `if errorlevel 1` del paso 1,
`build.bat` **borra el `dist\woptimizer.exe` que ya funcionaba** y sale con un
motivo que no es el real. El arreglo tiene dos mitades y las dos hacen falta:

* **el orden**: la precondicion (`call python -c "import PyInstaller"`) va antes
  de `rmdir`/`del`, y su salida es la suya, `:sin_pyinstaller`, que **no puede
  caer en `:fallo`**. Antes los tres caminos terminaban en el mismo `:fallo`, o
  sea que "no habia PyInstaller" y "la compilacion fallo" imprimian la misma
  frase.
* **el motivo**: tres salidas, una por causa --`:sin_pyinstaller` (precondicion),
  `:sin_salida` (salio 0 pero no hay `.exe`) y `:fallo` (la compilacion fallo de
  verdad). El motivo impreso describe **lo que paso**. Es lo que el encargo
  pedia: el motivo que imprime tiene que tener relacion con la causa.

**R3.** `presentes[nombre] = ruta` es un diccionario por `basename`. Con dos
`.bat` homonimos el ultimo que recorre `os.walk` pisa al primero y el primero
**deja de mirarse**. Ahora la clave es la ruta relativa, con `/` porque es como
git escribe las rutas en `.gitattributes`.

**R4.** El digito se corrige a `0x31` **medido**, y sobre todo se **deriva**: el
nuevo guard extrae el hex de la frase `su ultimo byte es \`0xNN\`` y lo compara
con el byte real del fichero. Anadir una linea al `.bat` pone el guard en rojo en
vez de dejar el documento mintiendo en silencio.

**De paso, y porque el propio informe lo senala en su §1.2 y §2.4**, se corrigio
el docstring de `test_build_bat_propaga_...`, que atribuia el `rc=0` del ciclo 65
a "la causa era DOBLE". No es cierto: lo producia el `exit /b 0` incondicional.
Los dos `call` siguen siendo un guard load-bearing y los mide la celda E.

## 12. La camara y como se midio

Copia en `%TEMP%\wopt_repar77_<id>_<sello>` con `.git` **propio y desechable**
(`git init` + un commit + `add -A`). El `.git` del repo real es un **fichero** de
57 bytes que apunta a `%LOCALAPPDATA%` y se excluye con `ignore_patterns`.

Corredor dirigido generado desde el `run_tests.py` **ya mutado**, que es lo que
hacia el auditor y lo que evita medir el fichero sano.

**Dos veredictos FALSOS se desperdiciaron antes de tener la tabla**, y se
documentan porque son la trampa de este patron:

1. `M-D` con el nombre del test mal escrito --> murio por
   `NO EXISTE la funcion en el run_tests.py mutado`. No es una muerte, es un
   *typo*. El nombre real es
   `test_el_journal_ilegible_informa_en_vez_de_reventar_el_validador`.
2. `M-D` con la camara recortando `docs/` y `openspec/` --> murio por
   `FileNotFoundError` en `shutil.copytree`, porque `_copiar_el_esqueleto_del_
   validador` copia esos dos arboles. **Ninguna muerte por `FileNotFoundError` es
   un veredicto**: es exactamente lo que el §2.2 del informe de arriba advertia.
   La camara copia de mas, nunca de menos.

## 13. Tabla de mutantes

| Id | Mutacion | Veredicto | Motivo LITERAL |
|---|---|---|---|
| **M-D** | `build.bat` fuera del esqueleto | **MUERE** | `run_tests.py:13491` `assert len(errors) == 1` - `Errors: [..., 'STATUS.md Deuda fila 75: VIVA y su UNICA fuente es una TAREA YA CERRADA: TASK-077.status == completed...']`. **Es el rojo real del informe, reproducido por mutacion.** |
| **M-A** | `build.bat` sin el `if errorlevel 1` del paso 1 | **MUERE** | `run_tests.py:20808` `assert os.path.exists(exe_previo)` - `sin PyInstaller, build.bat NO COMPILABA, y aun asi se llevo el dist\woptimizer.exe que ya funcionaba: el paso 2 (el del) se ejecuto porque el paso 1 no corto el flujo`. Su stdout imprime `Construyendo...` y `[ERROR] Fallo la compilacion. Revisa el log de PyInstaller.`: compilacion y motivo falsos, los dos. |
| **M-B** | el evaluador vuelve a indexar por `basename` | **MUERE** | `run_tests.py:20528` `assert fallos` - `el build.bat de la RAIZ esta en LF y el de herramientas/ en CRLF. Indexando por nombre de fichero, el sano pisa al incumplidor y el evaluador devuelve la lista vacia: el guard daria OK con el repositorio en LF, que es un verde FALSO (mutante N3x)` |
| **M-C** | `.gitattributes` vuelve a citar `0x30` | **MUERE** | `run_tests.py:20589` `assert citado == ultimo` - `.gitattributes:27 afirma que el ultimo byte de build.bat es 0x30 y en disco es 0x31` |

**4 de 4 mueren, cada uno por SU asercion y en una linea distinta.** Los cuatro
motivos son de `AssertionError` sobre **contenido** (un `.exe` que sobrevive, un
`fallos` no vacio, un hex que no cuadra, un `len(errors)` que no cuadra), no de
"se llamo".

### La pregunta que el encargo hacia sobre B, contestada con medida

> *el mutante de B: tu guard sigue detectando un `build.bat` en LF si hay tambien
> uno en CRLF en un subdirectorio?*

**NO antes, SI ahora.** `M-B` es exactamente esa pregunta y **murio**: con el
indice por `basename`, `fallos == []` y el guard daba OK. Con el indice por ruta,
el `build.bat` de la raiz se mira y se acusa. El CONTROL POSITIVO va al lado en el
mismo test (los dos en CRLF tiene que dar OK), para que lo que se afirma sea "falla
el que esta en LF" y no "falla siempre".

## 14. Verificacion de la reparacion, con salida real

```
python run_tests.py       -> EXIT=0
   Probando que la politica EOL cubre los scripts de consola que existen...
   Probando que el guard de EOL rechaza lo mismo que acepta...
   Probando que build.bat propaga el codigo de salida de force_build...
   Probando que la camara de build.bat detecta la regresion...
   Probando que un .bat homonimo no tapa a otro en el guard de EOL...
   Probando que la cita del ultimo byte de build.bat no se caduca...

   ALL TESTS PASSED.

python validate_docs.py   -> EXIT=0
   Resumen: 152 OK, 0 FAIL, 0 SKIP
   [OK]   STATUS.md: declara los 226 tests que run_tests.py tiene de verdad
   [OK]   docs/ai/testing-guide.md: 226 filas de test, una por test definido
   [OK]   run_tests.py: reparto 155 backend + 71 headless derivado con ast

python verify_ui_syntax.py -> EXIT=0
   EXITO: Todos los modulos UI estan impecables.
```

**224 -> 226 tests**, y el reparto lo DERIVA `validate_docs.py` con `ast`, no se
ha escrito a mano: `155 backend + 71 headless = 226`. Los cinco sitios que
declaran la cifra se movieron a la vez (`run_tests.py`, `docs/ai/testing-guide.md`
--resumen y dos filas de tabla--, `STATUS.md:12`, `STATUS.md:110`, `AGENTS.md:70`,
`README.md:63` y el badge de `README.md:6`).

## 15. La bomba de mantenimiento que Task-077 ha vuelto a detonar

`run_tests.py:22875` **era una cita por numero de linea** y las reparaciones de
este apartado anaden lineas por encima: la cita se movio a `23082`. Se corrigio en
los tres sitios que la nombran --el texto de la linea, la tupla del guard de
`test_las_citas_de_sandbox_rules_siguen_siendo_ciertas` y `STATUS.md:85`--, otra
vez **solo moviendo el numero**. Es la **tercera** vez en la misma tarea
(`22264` -> `22730` -> `22875` -> `23082`), y la deuda P2 de `STATUS.md:85` sigue
**VIVA y sin arreglar**: el fix de fondo sigue siendo que el guard **derive** los
numeros con `ast` en vez de citarlos. No se ha hecho aqui porque es un guard de
otro ciclo (TASK-076) y rehacerlo es rediseño, no ejecución.
