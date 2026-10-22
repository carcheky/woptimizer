# Cuadro de Mando: Motor Autónomo de I+D (woptimizer)

> Dashboard del pipeline de I+D. Actualizado el 2026-10-22.

---

## 🟢 Salud General

| Indicador | Estado | Detalle |
|---|---|---|
| Sintaxis UI | 🟢 | `verify_ui_syntax.py` — alcance **DERIVADO** con `rglob`, 22 módulos bajo `src/woptimizer/` (cifra atada a la que el script imprime: `test_el_recuento_de_modulos_de_sintaxis_es_derivado` la compara, no se mantiene a mano) |
| Tests headless | 🟢 | `run_tests.py`, **235 tests** (159 backend + 76 headless UI) |
| Benchmark base | 🟢 | 182 ms init · 4.97 ms escaneo · 0.003 ms cache · 30 MB RSS |
| Process DB | 🟢 | 96 entradas · 8 categorías · 0 huérfanas · 🛡️ 34 protegidas |
| Versionado | 🟢 | Rama `beta` · último commit `423a96e` (ciclo 70) · `main` publicada `v1.1.0` |
| Build (PyInstaller) | 🟡 | Artefacto de distribución; se regenera al publicar vía CI |

---

## 🔄 Estado de la Ejecución

- **Ciclos completados:** 70 (`rd_journal.json`)
- **Rama de trabajo:** `beta` (nunca commitear a `main` directamente)
- **Último ciclo (#70):** TASK-087 — el veredicto de mutación se vuelve **comprobable**: un emisor escribe la línea canónica `WOPT_VEREDICTO <mutante> <MUERTO|SOBREVIVIENTE|NO MEDIDO> <sha>` y un gate (check 11 de `validate_docs.py`) la **re-deriva** desde la evidencia commiteada. El gate va en el validador y **no** como `test_*`, así que el recuento queda **intacto** (235 = 159 + 76). Veredicto de auditoría: **PASS**
- **Tarea activa (`active_task_id`):** `TASK-087` — el veredicto de mutación era **prosa sin vigilancia**: borrar el veredicto del journal o el informe entero daba **0 FAIL**. Evidencia: `openspec/changes/2026-10-22-killer-check-del-veredicto/`.
- **`TASK-080` NO se activa:** su propia medicion dice que CI no puede dar verde todavia (25 hashes de `rd_journal.json` sin pushear). Activarlo hoy rompe el pipeline.

---

## 📋 Tareas Pendientes (backlog)

| ID | Estado | Prioridad | Título | Notas clave |
|---|---|---|---|---|
| **TASK-073** | ✅ `completed` | **high** | RuntimeError en `ProcessManagerView._load` tras destrucción | **RESUELTO 2026-10-18:** los 10 `self.after` de `views/` pasan por `self._publicar_en_el_bucle` (`ui/tk_thread.py`); el defecto solo vivía en el mundo headless |
| **TASK-068** | `in_progress` | high | Arranque por categorías revierte TASK-063 | Código hecho, 189→198 tests. **2 decisiones del dueño bloquean cierre (P-1, P-2b)** |
| **TASK-074** | ✅ `completed` | medium | Blindar paridad git tooling (código 2 asimétrico) | **RESUELTO 2026-10-18:** el `2` de `paridad-git` precede al `3` del repo **en los dos modos**. MEDIDO en las ocho celdas: cambia **una**, `--verify` + par roto + repo roto, de 3 a 2. La posición respecto a `validar_repo` era inobservable (no imprime) y ahora la ata una sonda AST |
| **TASK-075** | ✅ `completed` | medium | Desacoplar `validate_docs.py` de `%LOCALAPPDATA%` para CI | **RESUELTO 2026-10-18:** una sola resolución del repositorio (`--git-dir` > `WOPTIMIZER_GIT_DIR` > `GIT_DIR` > `%LOCALAPPDATA%`) usada por los DOS consumidores que leen git; `--git-dir` y `--sin-ancla-de-git` con `[SKIP]` propio. La exclusión de CI **sigue** y su motivo escrito era falso: no es la ruta, son 25 hashes sin pushear |
| **TASK-076** | ✅ `completed` | medium | Desduplicar flags PyInstaller (`force_build.py` vs `release.yml`) | **RESUELTO 2026-10-18:** la premisa del encargo era FALSA —`force_build.py:11-16` y `release.yml:208` ya eran **idénticos** byte a byte—, así que la asimetría real estaba en `build.bat:27` y en el ejemplo de `docs/ai/sandbox-rules.md`, que compilaban SIN `--add-data assets;assets`. Fuente única `force_build.py` (la invocan `build.bat` y el job `build`). **7 guards**, y el que discrimina (AC-2) deriva su expectativa de `src/`: sin él, el bug de `build.bat:27` no lo mataba nadie |
| **TASK-082** | ✅ `completed` | high | El conjunto de vistas del guard de workers se deriva del disco, y su vigilancia deja de ser vaciable | **RESUELTO 2026-10-22:** el guard abre el **derivado** (`_vistas_del_disco()`) y la literal queda como **declaración comparada**; tres rondas de reparación (vigilancia no contada · `NameError` latente · dos vías del detector). Auditoría **PASS**: 13/13 mutantes declarados, 0 identificadores sin definir. Spec: `openspec/changes/2026-10-21-vistas-del-guard-de-workers-derivadas/` |
| **TASK-083** | ✅ `completed` | high | Un test FLAKY puede fabricar falsos veredictos: el hash muerto se construye a partir del hash REAL (1/16), no por el reloj | **RESUELTO 2026-10-22:** la causa no era el reloj sino la **construcción** — el hash muerto era `hash_real + "0"` y `cat-file -e` resuelve cualquier prefijo de 8 hex, así que coincidía con el objeto real cuando la 8.ª cifra del sha era `0` → 1/16 = 6,25 %. Arreglado con reloj clavado, hash muerto **derivado por construcción** y un **tripwire derivado con `ast`**. Auditoría **PASS**: M-3 **30/30 en rojo y reproducible**, 0 fallos de 200, y **no hay otro test flaky**. Spec: `openspec/changes/2026-10-22-veredicto-de-no-medido/` |
| **TASK-087** | ✅ `completed` | high | El veredicto de mutación se vuelve **comprobable**: falta el tercer estado, NO MEDIDO | **RESUELTO 2026-10-22:** un **emisor** (`.taskmaster/veredicto.py`) escribe la línea canónica `WOPT_VEREDICTO <mutante> <MUERTO|SOBREVIVIENTE|NO MEDIDO> <sha>` y un **gate** (check 11 de `validate_docs.py`) la **re-deriva** desde la evidencia commiteada. El gate va en el validador y **no** como `test_*`: el journal se escribe después del Paso 4 y el recuento queda **intacto** (235 = 159 + 76). Auditoría **PASS** (D-A, D-D, D-E, D-F, D-G y los 14 previos muertos). Spec: `openspec/changes/2026-10-22-killer-check-del-veredicto/` |

> **Prioridad de ejecución:** `TASK-087` cerrado el 2026-10-22. Siguiente del backlog: **`TASK-090`** (el cuerpo del check 11 se puede vaciar y el guard sigue verde) → `TASK-091` (el gate ignora el campo `mutacion` del catálogo) → `TASK-088` (la familia de fixtures y el conjunto del tripwire) → `TASK-089` (el árbol que se mueve durante la corrida) → `TASK-084` → `TASK-085` → `TASK-086`; y `TASK-068` en cuanto el dueño decida.
> **TASK-068** está bloqueada por decisiones del dueño (P-1 y P-2b, ver más abajo).

---

## 🗂️ Rotación de Áreas

| # | Área | Último ciclo |
|---|---|---|
| 1 | Resiliencia & Robustez | #37 |
| 2 | Gaming & Telemetría UX | #42 |
| 3 | Base de Datos & Procesos | #40 |
| 4 | Rendimiento & Latencia | #35 |
| 5 | Testing & Calidad | #43 |
| 6 | Documentación & Arquitectura | #47 |

---

## ⚠️ Deuda Técnica Conocida

### 🔴 Crítica

- **✅ CERRADA en TASK-081 (ciclo 67): el alcance de `verify_ui_syntax.py` estaba VACÍO y corría en CI (MEDIDO).** **MEDIDO antes del arreglo:** `verify_ui_syntax.py` enumeraba **DIEZ** rutas escritas a mano; el árbol real tiene **12** `.py` bajo `src/woptimizer/ui/` y las que faltaban eran `theme.py` y `tray_menu.py`. Cámara desechable **con control positivo**: los dos no listados rotos → **exit 0, VERDE**; `app.py` (listado) roto → **exit 1**; un módulo **nuevo** roto → **exit 0, VERDE**. Ya había fallado **dos veces de hecho** (`theme.py` `2b81978` 2026-10-01, `tray_menu.py` `a8b2a89` 2026-10-04), y el hallazgo ya estaba documentado en `openspec/changes/2026-09-29-double-tap-confirmation/proposal.md` §9.7 y se "arregló" **añadiendo `confirmation.py` a la lista**. **LO QUE HIZO ESTA FILA:** `verify_ui_syntax.py` deriva el alcance con `rglob("*.py")` sobre `src/woptimizer/`, sin lista y **sin lista de exentos**, e imprime `ALCANCE_DERIVADO=N`; la cifra de la fila 11 es esa y `test_el_recuento_de_modulos_de_sintaxis_es_derivado` la ata a lo que el script **imprime**. **5 sondas**: dos de forma con `ast` (ninguna enumeración de rutas de `src/` en `run_tests.py`, `validate_docs.py` ni `verify_ui_syntax.py`; y que la derivación esté **usada**, que es lo que mata el `rglob` decorativo con la lista de vuelta), dos de **producto** (un módulo **nuevo** roto en `%TEMP%` → exit 1 nombrándolo, y su **control positivo**: árbol sano → exit 0), y una de recuento. **Clase, no caso — y lo que queda VIVO:** R4 **denuncia, no repara**. MEDIDO que hay **DOS** tuplas de cuatro rutas en `run_tests.py` (`test_no_literal_colors_in_views` y `test_hit_targets_minimum`, la segunda no venía en el encargo), y las dos llevan ahora en su docstring (a) por qué existe la enumeración y (b) qué la retira; **no** entran en una lista muda de permitidos, que es la misma trampa por la que este guard llevaba fallando desde octubre. Reparar su cobertura es un ciclo propio. Detalle: `openspec/changes/2026-10-19-verificacion-ui-alcance-derivado/proposal.md`.
- **✅ CERRADA en TASK-077 (ciclo 66): `build.bat` propagaba el código de salida de la compilación.** **MEDIDO de extremo a extremo antes del fix**: con un `force_build.py` que sale con 7, `build.bat` salía con **0**. La causa era **DOBLE, y las dos se midieron** con `cmd.exe` de verdad y una matriz de 5 celdas: **(i)** el `exit /b 0` incondicional del cierre, sin propagar nada; **(ii)** ⚠️ **el `call` que faltaba en las invocaciones** — si `python` resuelve a un `.cmd`/`.bat` (un shim en `%PATH%`, o el `python.bat` de una instalación vieja) ese `.cmd` **secuestra el control** y todo lo de debajo no se ejecuta nunca: el `.bat` se quedaba en el paso 1 y salía con **0**, y compilar era un espejismo. El `.exe` roto llegaba por aquí, **no por CI** (`release.yml` sí propaga: el runner añade `exit $LASTEXITCODE` a `pwsh`), o sea que **el build local mentía y el de GitHub no**. `build.bat` ahora lleva `call` en las dos invocaciones y una etiqueta `:fallo` que devuelve el código de la compilación, y devuelve 1 (no 0) si se llega a ella con RC 0 — la compilación "fue bien" pero el `.exe` no está. **Guard de cinco celdas** (`test_build_bat_propaga_el_codigo_de_salida_de_force_build`, AC-3) con el `.bat` real y un stub de `python.cmd` en `%PATH%`, más su **contraprueba** (AC-4), que repone el `exit /b 0` en una copia de `%TEMP%` y exige que vuelva a dar 0 — con **control positivo**, porque MEDIDO el mutante `S2` (una cámara que devuelve 0 siempre) **sobrevivió** sin él. Evidencia: `openspec/changes/2026-10-18-eol-real-y-exit-de-build/`.
- **Shell intermitente (`spawn EPERM`):** El entorno de agentes bloquea subprocesos vía Node. Afecta a `tm.py` y a veces a `.taskmaster/git_safe_commit.py`. Workaround: reintentar. No tiene fix posible desde el repo. Blindado con el contrato de códigos de salida de `.taskmaster/git_safe_commit.py` (`docs/ai/sandbox-rules.md`).
- **`.git` corrupto (VFS Nextcloud):** El historial vive en `%LOCALAPPDATA%\woptimizer_git\.git`. Se acepta y se blinda con `.taskmaster/git_safe_commit.py --verify` (`docs/ai/sandbox-rules.md`).

### 🟢 Baja (CYCLE-063 y CYCLE-066, abiertas y sin riesgo vivo)

- **P2 · cita autorreferente por número de línea (`CYCLE-066`):** `test_las_citas_de_sandbox_rules_siguen_siendo_ciertas` ata 4 afirmaciones **por número de línea**. MEDIDO sobre 114 commits: se movió **2 de 3** transiciones (`22875`→`23082`). Rompe **con ruido** (nombra fichero y línea), así que no es agujero. El fix de fondo es que el guard **derive** los números con `ast`, y eso es rediseño del guard de `TASK-076`.
- **S1 · `build.bat` borrado del repo da rojo por `FileNotFoundError` (`CYCLE-066`):** 2 guards revientan por ruta inexistente en vez de por su aserción. Ruidoso, no silencioso. Evidencia: `openspec/changes/2026-10-18-eol-real-y-exit-de-build/mutation-report.md` PARTE 3.
- **H1 · el doc es más estricto que el código:** `sandbox-rules.md` (regla 4) exige que la línea `WOPT_*` sea la última impresa, pero el camino de **commit** imprime su `INFO no se intenta el .git…` **después** de `WOPT_REPO_INVALIDO`. El documento es más estricto que el código. Evidencia: `openspec/changes/2026-10-18-paridad-antes-del-repo-invalido/mutation-report.md`.
- **H2 · rigidez de la sonda AST:** `test_la_puerta_de_paridad_va_despues_de_validar_repo_por_estructura` (`run_tests.py`) exige `verify` como **primer** operando del `and`; `not ok and verify` la mata por «no encontrado», no por su aserción. Fallo ruidoso, no silencioso. Evidencia: `openspec/changes/2026-10-18-paridad-antes-del-repo-invalido/mutation-report.md`.
- **H3 · nombre que miente:** `test_la_puerta_de_paridad_va_despues_de_validar_repo` (`run_tests.py`) ya no mide la posición frente a `validar_repo` (esa posición es inobservable: `validar_repo` no imprime). Declarado en su docstring. Evidencia: `openspec/changes/2026-10-18-paridad-antes-del-repo-invalido/mutation-report.md`.

### 🟡 Media

- **A12 · `_copiar_el_esqueleto_del_validador` es BOMBA DE MANTENIMIENTO, no agujero — y el ciclo 66 lo trato al reves (`run_tests.py`).** Su tupla `ficheros` es la misma clase que la de `verify_ui_syntax.py` (enumeracion escrita a mano que espeja lo que el validador lee), asi que por forma deberia ser agujero. **MEDIDO el 2026-10-19 en 8 celdas** (esqueleto real menos un fichero, pasado por `validar()` de verdad): quitar `STATUS.md` → 2 errores; `mkdocs.yml` → 1; `CHANGELOG.md` → 1; `README.md` → 1; `llms-full.txt` → 1; **`build.bat` → 1** (y ese es el incidente del ciclo 66, reproducido en 20 s **sin incidente real**: el ancla de `build.bat` no resuelve en la copia y la fila se queda con `fuentes == ["tarea"]` con la tarea ya cerrada). Solo `AGENTS.md` y `llms.txt` dan `FileNotFoundError` sin asercion, que es el residuo **S1** ya declarado. **Veredicto: TODAS las celdas dan ROJO**, con fichero y linea nombrados. Que se manifestaria si el codigo o el documento estuvieran mal: **si**. No es un agujero y no se arregla aqui; queda **denunciado por forma** por el guard AC-5 de `TASK-081`, no reparado.

- **A11 · `exentos = publicados - llamados` sin contraprueba (CYCLE-062, `TASK-079`):** Quitar el ` - llamados` de `_cuerpos_a_medir` (`run_tests.py`) deja el proyecto entero en verde: `ALL TESTS PASSED.`, 26 400 B. **No es alcanzable con el código real** — los únicos nombres publicados son `_handle_ok` y `_handle_err`, únicos y nunca llamados — así que no es un riesgo vivo, pero es una afirmación que la suite no somete a prueba. Es la **tercera** vez en este repo que aparece el patrón "una comprobación sin contraprueba no es una comprobación". Fix: control sintético en el test 205 que exija que esa resta cambie el resultado. Evidencia: `openspec/changes/2026-10-18-tkinter-after-guard/mutation-report.md` §11.
- **✅ CERRADA en TASK-077 (ciclo 66): el EOL de `build.bat` NO era un defecto del repo, era drift del árbol local.** **MEDIDO** el 2026-10-18 sobre el HEAD `2decac4`: `i/crlf` = **0** sobre 256 tracked, y un clon desechable del mismo HEAD entrega `build.bat` como **`w/crlf`, 39 CRLF / 0 LF** — la política `*.bat text eol=crlf` **funciona**. Los 37 ficheros que incumplían (34 `w/crlf` bajo política LF + 3 `w/mixed`) estaban **en el árbol de trabajo de esta máquina**, no en el repo. **`git add --renormalize .`, el fix que decía esta misma fila, es NO-OP**: medido 0 ficheros staged, porque `eol=crlf` actúa en el **checkout** y `git add` nunca escribe en el árbol; el `add -A` del wrapper tampoco podía colarlos, porque el filtro *clean* devuelve el mismo objeto. **Y la premisa de los "fallos de parsing" en `.bat` con LF es FALSA**: `cmd.exe` ejecuta el fichero en LF con salida y código de salida idénticos byte a byte en 6 escenarios medidos. **Lo corregido, en tres partes.** (1) Los 37 re-materializados con `git checkout-index` sobre lista explícita — **cero commits, cero cambios de índice**, verificado: `git status --porcelain` vacío. ⚠️ **MEDIDO en esta maquina y NO esta en el encargo**: `checkout-index -f -- <f>` **NO** reescribe un fichero que git considera limpio (el filtro `clean` normaliza CRLF→LF, el resultado coincide con el índice y git no lo toca): la vía que funciona es `checkout-index -f --temp -- <f>`, que deja el contenido exacto en un temporal para sustituirlo encima. Con `-f` a secas la lista entera se aplicó a **cero** ficheros. (2) La justificación **falsa** de `.gitattributes:20` sustituida por la medida, conservando las tres reglas `eol=crlf` — no porque `cmd.exe` se rompa, sino por convención nativa y determinismo del árbol. (3) Guard nuevo **por bytes** (`test_la_politica_eol_cubre_todo_script_de_consola_que_existe`, AC-1) con su contraprueba en `%TEMP%` (AC-2). ⚠️ **MEDIDO al escribir el guard**: `basura/` (la cuarentena del dueño, **fuera del índice a propósito** por `.gitignore:75-79`) tiene un `commit_version.bat` en **LF puro**, y está **bien** que lo esté: la política gobierna lo que el repo **contiene**. El guard **excluye `basura/`** y **contrasta esa exclusión contra el `.gitignore` real dentro del propio test**: si `basura/` deja de estar ignorado, el test lo dice, pero nunca deja de mirar en silencio. Un guard que grita por un fichero que nadie ha pedido versionar deja de que lo escuchen. **El guard NO puede apoyarse en `git ls-files --eol`**: en CI, `actions/checkout` aplica los atributos en el checkout fresco y ese comando reportaría `w/crlf` esté sano o no el repo — un **verde falso**. Evidencia: `openspec/changes/2026-10-18-eol-real-y-exit-de-build/`.
- **11 ficheros `test_*.py` heredados:** **🔴 CERRADA en CYCLE-045 (TASK-055).** Archivados en `docs/archive/legacy-root-tests/`. Guard en `run_tests.py` impide que vuelvan a la raíz.
- **`validate_docs.py` no corre en CI (`TASK-080`, `pending`):** No es `%LOCALAPPDATA%`: MEDIDO el 2026-10-18 que el clon shallow del job `verify` da **154 FAIL** y que, aun con `fetch-depth: 0`, **25 de los ~150 hashes de `rd_journal.json` no son alcanzables desde ninguna rama del remoto** (están sin pushear, no perdidos). La exclusión es correcta; lo que faltaba era el motivo escrito. Detallado en `docs/ai/sandbox-rules.md Por que el validador NO corre en CI`.

- **✅ CERRADA en TASK-083 (ciclo 69): un test FLAKY puede fabricar un veredicto.** MEDIDO el 2026-10-22: la causa **no era el reloj** sino la **construcción** — el hash muerto era `hash_real + "0"`, y `git cat-file -e` resuelve cualquier prefijo de 8 hex, así que coincidía con el objeto real cuando la **8.ª cifra del sha era `0`** → **1/16 = 6,25 %**. El reloj solo hacía que el sha variase. **Arreglado**: reloj **clavado** en la fixture, hash muerto **derivado por construcción** (`cat-file --batch-all-objects --batch-check` → 15 de 16 dígitos libres) y un **tripwire derivado con `ast`** que detecta toda concatenación de un hash real. **Verificado**: 0 fallos de 200 en el pre-vuelo sano, M-3 **30/30 en rojo y reproducible**, y **no hay otro test flaky** (0 de 6 suites completas; 400 fixtures de la familia → 0 colisiones de los 5 literales). El ruido que queda en los logs de la suite son 42 líneas de ids de widget con marca de tiempo, no fallos. Lo que queda **encolado**: el killer-check del veredicto (`TASK-087`), la familia y el conjunto del tripwire (`TASK-088`) y el árbol que se mueve (`TASK-089`); los dos primeros **los puede pisar el bucle en cualquier ciclo**. Evidencia: `openspec/changes/2026-10-22-veredicto-de-no-medido/mutation-report.md`. el test del pre-vuelo de un hash falla ~**5,5 %** (11 de 200 fixtures medidos; teórico 6,25 %) porque los fixtures comparten sha dentro del mismo segundo. Con 17 cámaras en paralelo, **P(que una medición se contamine) = 61 %**. Ya pasó: en la ronda 3 del ciclo 68 un mutante **pareció muerto** por eso, y lo detectaron el dev y el auditor porque el log no cuadraba. Un guard que a veces no vigila es un guard que a veces da verde falso. Criterio de cierre: 0 muertes en 1000 corridas. Evidencia: `openspec/changes/2026-10-21-vistas-del-guard-de-workers-derivadas/mutation-report.md`.

- **S8 · la tolerancia del guard AC-5 de TASK-081 sigue siendo POR FUNCIÓN (`TASK-084`):** `_delitos_de_enumeracion` (`run_tests.py:30032`) calcula la justificación **una vez por ámbito**, así que una segunda enumeración en una función ya justificada queda **tapada** sin querer. La reparación de este ciclo (**R9**) lo arregló **en el guard de forma de AC-1** (la tolerancia pasó a ser **por enumeración**), pero **el guard AC-5 del ciclo 67 conserva la tolerancia por función**. MEDIDO: su enumeración justificada vive bajo `src/woptimizer/**`, luego **no es un agujero del fix de este ciclo**. Evidencia: `openspec/changes/2026-10-21-vistas-del-guard-de-workers-derivadas/mutation-report.md`.

- **S10 · el detector de forma de AC-1 no ve enumeraciones escondidas detrás de una llamada (`TASK-085`):** una enumeración metida en una llamada no la ve, porque la heurística busca literales en posicion de asignacion. MEDIDO: el mutante **sobrevive 3/3** (log byte a byte = baseline). **Pero el guard real sí lo caza**: el control **S4** muere por la regla «una SEGUNDA copia». Es un hueco de la **heuristica**, no un verde falso del guard, y su arreglo exigiría aceptar literales en cualquier expresion (mas falsos positivos). Decisión del orquestador: **no se persigue en este ciclo**; queda **encolado** con su métrica. Evidencia: `openspec/changes/2026-10-21-vistas-del-guard-de-workers-derivadas/mutation-report.md`.

- **D-B · el CUERPO del check 11 se puede vaciar y el guard sigue verde (`TASK-090`):** MEDIDO el 2026-10-22 en el ciclo 70: si el cuerpo del gate se vacía pero **el REGISTRO sigue imprimiéndose**, la suite da **rc=0 verde**. El cableado está vigilado (D-A muere), pero **el contenido del gate no**. El repo ya tiene el patrón para el check 9 (el «mutante de cableado» que lo vigila, en `run_tests.py`); el check 11 solo tiene el cableado. Evidencia: `openspec/changes/2026-10-22-killer-check-del-veredicto/mutation-report.md`.

- **D-H · el gate ignora el campo `mutacion` del catálogo (`TASK-091`):** MEDIDO el 2026-10-22 en el ciclo 70: el gate lee `id`, `asa`, `motivo` y `sha_arbol_auditado`, pero **no** lee el campo `mutacion` (qué se sustituye y por qué). Un catálogo con una `mutacion` **incorrecta** pasa el gate sin que nada lo note (0 FAIL). Límite **nuevo**, declarado en el docstring del gate como «la lista de límites NO es exhaustiva». Evidencia: `openspec/changes/2026-10-22-killer-check-del-veredicto/mutation-report.md`.

### 🔵 Abiertas en CYCLE-064, CYCLE-066 y CYCLE-067 (documentales, no tocan seguridad ni datos)

- **S7 · un docstring afirma una garantía que NO tiene (CYCLE-067):** la guarda AC-1 (`run_tests.py`, "los ficheros de `src/` no se enumeran a mano") **declara en su docstring que mata `M-R`, y MEDIDO lo pasa**: un `rglob` muerto sobrevive a AC-1. Solo AC-3 lo caza, por producto. El guard **sí** funciona en conjunto, pero su propia documentación miente. Fix: corregir el docstring. Evidencia: `openspec/changes/2026-10-19-verificacion-ui-alcance-derivado/mutation-report.md`.
- **S4 · cifras caducadas en el changelog de raíz (CYCLE-067):** `CHANGELOG.md:147` y `:189` dicen «9 de 9 módulos» y **nada las vigila** (el check del recuento lee una sola línea por fichero). **DECISIÓN DEL ORQUESTADOR: no se reescriben** — están bajo `## CYCLE-060`, en un apartado `### Verificado`, y eran **ciertos en su momento**; la regla de append-only prohíbe reescribir entradas antiguas. (La excusa del dev de que "son del orquestador" era **falsa**: los escribieron `0864628` y `328237f`.) El patrón hacia adelante ya está cerrado: TASK-081 hace que el recuento sea **derivado**.
- **S6 · `REGISTRO_INDECISAS` tiene 15 celdas manuales (CYCLE-067):** la **misma clase** que TASK-081 cierra, pero **no el mismo agujero**: añadir una llamada indecisable lo pone en **ROJO** (`de más` confirmado). Deuda baja y consciente. Evidencia: `openspec/changes/2026-10-19-verificacion-ui-alcance-derivado/mutation-report.md`.
- **S1/S2/S3 · enumeraciones literales fuera del alcance de AC-5 (CYCLE-067):** `run_tests.py:13235-13237` (ficheros de raíz), `validate_docs.py:1860` y `_chk.py:2`. MEDIDO el 2026-10-22 en el ciclo 68: de las **19** citas por número de línea verificadas, **18** están vivas y **1** era falsa de ordinal (corregida en este cierre), y **ninguna de las 19 la vigila un guard** (`TASK-086`). Las tres que no sostienen su afirmación (una en Salud, una en Ejecución y una línea en blanco de la Crítica) son **preexistentes** a este ciclo. AC-5 solo cubre literales de `src/woptimizer/**.py`. La de `_copiar_el_esqueleto_del_validador` **debe seguir enumerando**: un `rglob` traería 16 ficheros de raíz, incluido `saved_processes.json`. Las tres llevan justificación escrita con *(a) por qué* y *(b) qué la retira* — salvo la (b) de la del esqueleto, que es **aspiracional**: no dice qué hacer.
- **D1** (media): `validate_docs.py:293` afirma que `WOPTIMIZER_GIT_DIR` tiene "el mismo contrato" que `--git-dir`. MEDIDO: solo `--git-dir` se exige (repo inválido → FAIL propio); los otros tres peldaños caen en el FAIL del historial. Fix: reescribir el comentario con la asimetría real.
- **D2** (baja, MEDIDO de nuevo en TASK-077 el 2026-10-18): **las tres citas de esta fila ya no son las que están, y hay una cuarta caducada que no nombra.** De los tres sitios que decía, **solo el badge de `README.md:6` seguía caducado** (`tests-207`), y **`corregido en TASK-077` a `tests-224` junto con `STATUS.md:109`, `(207 tests)`**, que era el cuarto caducado que esta fila no nombraba y que se volvía a pisar al mover el contador. `STATUS.md:106` es la instrucción de leer `AGENTS.md` —la cifra vive en `STATUS.md:12`— y `docs/ai/testing-guide.md:57` ya decía la verdadera. ⚠️ **Lo que SIGUE VIVO, y es la parte de fondo:** el check del recuento lee **una sola línea por fichero**, así que cualquier otra línea con una cifra de tests (la instrucción, una tabla, un badge) queda **fuera de su alcance** y se caduca en silencio — es exactamente lo que pasó aquí dos veces. Fix de fondo: que el check derive de **varias líneas** o de un **marcador único**, no de una línea elegida a mano.
- **D3** (baja): `release.yml` declarado con 193 líneas; tiene **215** (MEDIDO en TASK-076, 2026-10-18; eran 214 y este cambio movió una al reescribir el paso `build`). Cifra corregida, **deuda viva**: es un recuento escrito a mano sobre un fichero que se edita, la misma clase que D2, y se caducara otra vez en el siguiente cambio. Fix de fondo: derivarla o marcarla como "se declara al cierre del ciclo que toque el fichero". Evidencia: `openspec/changes/2026-10-18-validate-docs-ruta-y-degradacion/mutation-report.md`.
- **P1** (no medido **por presupuesto**): el registro de llamadas indecisas de `test_ninguna_llamada_de_cat_file_batch_check_se_queda_sin_input` (`run_tests.py`) creció 3 entradas documentadas (los `subprocess.run` de los flags del validador). Falta el mutante que compruebe que ese registro no se puede vaciar sin ponerse rojo. Evidencia: `openspec/changes/2026-10-18-validate-docs-ruta-y-degradacion/mutation-report.md`.
- **P2** (MEDIDO en TASK-077 el 2026-10-18, **deuda VIVA y NO arreglada**): `test_las_citas_de_sandbox_rules_siguen_siendo_ciertas` ata **cuatro** afirmaciones por **número de línea** (`validate_docs.py:1429`, `validate_docs.py:1924`, `run_tests.py:23718` y `docs/ai/sandbox-rules.md:1133`). **Cualquier línea que se inserte por encima de una de ellas desplaza la cita y el guard se pone rojo**, aunque la afirmación siga siendo cierta: TASK-077 lo rompió **dos veces** en la misma tarea (la cita de `run_tests.py` pasó de `22264` a `22730` y luego a `22875`, y las dos correcciones fueron solo mover el número) y **una vez más en la reparación** (pasó a `23133`, otra vez solo moviendo el número; MEDIDO el 2026-10-22, la cita que el panel señalaba apuntaba a una línea que decía literalmente `nada.`). Es la **misma clase** que D2 (una cifra escrita a mano que se caduca) y que el `release.yml` de D3: **dato derivado, escrito a mano**. Fix de fondo: que el guard **derive** los números con `ast` en vez de citarlos, o que las afirmaciones citen el **fichero y el texto** y no la línea. ⚠️ **No se ha arreglado aquí** porque es un guard de otro ciclo (TASK-076) y rehacerlo es rediseño, no ejecución. MEDIDO el 2026-10-22 en el ciclo 69: **una cita más era falsa** — `docs/ai/testing-guide.md` apuntaba a `run_tests.py:22264`, que hoy dice otra cosa (el test real está en `run_tests.py:29604`); corregida en este cierre. Las vivas (`13235`, `17889`, `23718` y `validate_docs.py:1429`) confirmadas una a una. MEDIDO el 2026-10-22 en el ciclo 70: **la cita de `run_tests.py` de esta fila quedó CADUCADA** cuando el ciclo 70 insertó líneas por encima de ella (la viva pasó de `23133` a `23305`), y **ningún guard lo avisa**: se corrige en cada cierre, pero el hecho de que una cita pueda caducar sin que nada lo note **es** el agujero de `TASK-086`. MEDIDO el 2026-10-22 en el ciclo 71: **volvió a caducar** (este ciclo insertó 324 líneas por encima en la primera vuelta y 89 más en la segunda —la ampliación del corpus del guard (D)—: la viva pasó de `23305` a `23629` y luego a `23718`) y **cuatro** citas más del panel **ya estaban caducas ANTES de este ciclo** (`23131`, `29006`, `28676` y `28734`): corregidas todas contra el número MEDIDO del texto que citan. **Ninguna** de ellas la vigila un guard (`TASK-086`).

---

## ❓ Decisiones pendientes del dueño (TASK-068, bloqueante)

- **P-1:** Con una categoría 🟡 marcada para arrancar, ¿se aceptan N launchers o 🟡 pasa a ser inerte al arrancar (simétrico con 🔴)?
- **P-2b:** ¿El mensaje debe decir POR QUÉ se omite cada categoría, o basta con ver QUÉ se omite?



## 🛡️ Features Planificadas

- **Pack de aplicaciones protegidas** (`TASK-071`, `pending`, alta):
  Apps dentro de este pack **no se matan nunca** por la ejecución de otro pack y **no aparecen** en el listado de procesos ni en otros packs.
  Spec: `openspec/changes/2026-10-07-task-071-protected-apps/`.
  Reutiliza `models.py:40 keepers` y el filtro existente en el motor de apagado.

---

## 📌 Recordatorios para el Agente

1. **Leer AGENTS.md** para invariantes (separación capas, kill recursivo, pack gaming protegido).
2. **Nunca commitear a `main`** — trabajar en `beta`, luego ff-merge.
3. **Commit solo vía** `python .taskmaster/git_safe_commit.py "mensaje (TASK-NNN)"`.
4. **Tests:** `python run_tests.py` (235 tests) · `python verify_ui_syntax.py` · `python validate_docs.py`.
5. **Docs vivas:** actualizar `docs/ai/` tras cada cambio arquitectónico.
6. **Carga selectiva:** no leer toda la doc — consultar `llms.txt` como mapa y cargar solo el fichero de `docs/ai/` que necesites.
7. **Pipeline de 4 pasos:** Buscar → Planear → Ejecutar → Auditar tests (mutation-auditor).

---

## 📋 Últimos Hitos (resumen compacto)

| Ciclo | Área | Qué se hizo |
|---|---|---|
| #70 | Tooling / Testing | El veredicto de mutación se vuelve comprobable: emisor + gate que lo re-deriva (TASK-087) |
| #69 | Tooling / Testing | Un test flaky que fabricaba falsos veredictos: el hash muerto se derivaba del hash real (1/16) (TASK-083) |
| #68 | Tooling / Testing | El conjunto de vistas del guard de workers se deriva del disco, y su vigilancia deja de ser vaciable (TASK-082) |
| #67 | Tooling | El alcance de la puerta de sintaxis UI se deriva, no se enumera (TASK-081) |
| #66 | Tooling / Build | El EOL no era un defecto del repo; build.bat deja de morir en silencio (TASK-077) |
| #65 | Tooling / Build | Fuente unica de los flags de PyInstaller y guard derivado de src/ (TASK-076) |
| #64 | Tooling | Una sola resolucion del repositorio del anclaje en el validador (TASK-075) |
| #63 | Tooling | Precedencia paridad (2) antes que repo invalido (3) en ambos modos (TASK-074) |
| #62 | UI / Testing | Publicación segura en el bucle de Tk desde hilos (TASK-073/078/079) |
| #61 | Core / UI | Aplicaciones protegidas no ejecutables e indestructibles (TASK-071) |
| #60 | Tooling | Hang stdin git fixture solucionado (TASK-072) |
| #59 | Tooling | `validate_docs.py` una vez por fichero (TASK-070) |
| #52 | Tooling | Puerta de ancla obligatoria en commits (TASK-059) |
| #49 | Docs | Check 8 de deuda con anclas resolubles (TASK-060) |
| #47 | Arquitectura | Ancla de trazabilidad de ciclos (TASK-057) |
| #43 | Testing | Sincronización tests favoritos acumulativos (TASK-053) |
| #42 | UX | Placeholder único en desplegable (TASK-052) |
| #41 | UX | Botón actualización DB con feedback (TASK-051) |
| #40 | DB | Sincronización remota + fallback observable (TASK-050) |
| #39 | UX | Grid de favoritos adaptativo (TASK-049) |
| #38 | Core | Favoritos acumulativos en PackService (TASK-048) |
| #37 | Robustez | Concurrencia en GamingService con RLock (TASK-047) |
| #36 | Testing | Contratos ciclo vida Confirmable (TASK-046) |
| #35 | Rendimiento | Memoización categorización O(1) (TASK-045) |

> Historial completo de los 61 ciclos en `.taskmaster/rd_journal.json` y `.taskmaster/CHANGELOG.md`.
