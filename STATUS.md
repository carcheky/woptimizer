# Cuadro de Mando: Motor Autónomo de I+D (woptimizer)

> Dashboard del pipeline de I+D. Actualizado el 2026-10-11.

---

## 🟢 Salud General

| Indicador | Estado | Detalle |
|---|---|---|
| Sintaxis UI | 🟢 | `verify_ui_syntax.py` — 10 módulos |
| Tests headless | 🟢 | `run_tests.py`, **220 tests** (155 backend + 65 headless UI) |
| Benchmark base | 🟢 | 182 ms init · 4.97 ms escaneo · 0.003 ms cache · 30 MB RSS |
| Process DB | 🟢 | 96 entradas · 8 categorías · 0 huérfanas · 🛡️ 34 protegidas |
| Versionado | 🟢 | Rama `beta` · último commit `4349b10` · `main` publicada `v1.1.0` |
| Build (PyInstaller) | 🟡 | Artefacto de distribución; se regenera al publicar vía CI |

---

## 🔄 Estado de la Ejecución

- **Ciclos completados:** 65 (`rd_journal.json`)
- **Rama de trabajo:** `beta` (nunca commitear a `main` directamente)
- **Último ciclo (#65):** TASK-076 — precedencia de la puerta de paridad (2) sobre la de repo inválido (3) en ambos modos. Veredicto de auditoría: **PASS**
- **Tarea activa (`active_task_id`):** `TASK-077` (siguiente del backlog; la deuda A11 del ciclo 62 y las bajas H1-H3 son candidatas a formalizarse)

---

## 📋 Tareas Pendientes (backlog)

| ID | Estado | Prioridad | Título | Notas clave |
|---|---|---|---|---|
| **TASK-073** | ✅ `completed` | **high** | RuntimeError en `ProcessManagerView._load` tras destrucción | **RESUELTO 2026-10-18:** los 10 `self.after` de `views/` pasan por `self._publicar_en_el_bucle` (`ui/tk_thread.py`); el defecto solo vivía en el mundo headless |
| **TASK-068** | `in_progress` | high | Arranque por categorías revierte TASK-063 | Código hecho, 189→198 tests. **2 decisiones del dueño bloquean cierre (P-1, P-2b)** |
| **TASK-074** | ✅ `completed` | medium | Blindar paridad git tooling (código 2 asimétrico) | **RESUELTO 2026-10-18:** el `2` de `paridad-git` precede al `3` del repo **en los dos modos**. MEDIDO en las ocho celdas: cambia **una**, `--verify` + par roto + repo roto, de 3 a 2. La posición respecto a `validar_repo` era inobservable (no imprime) y ahora la ata una sonda AST |
| **TASK-075** | ✅ `completed` | medium | Desacoplar `validate_docs.py` de `%LOCALAPPDATA%` para CI | **RESUELTO 2026-10-18:** una sola resolución del repositorio (`--git-dir` > `WOPTIMIZER_GIT_DIR` > `GIT_DIR` > `%LOCALAPPDATA%`) usada por los DOS consumidores que leen git; `--git-dir` y `--sin-ancla-de-git` con `[SKIP]` propio. La exclusión de CI **sigue** y su motivo escrito era falso: no es la ruta, son 25 hashes sin pushear |
| **TASK-076** | ✅ `completed` | medium | Desduplicar flags PyInstaller (`force_build.py` vs `release.yml`) | **RESUELTO 2026-10-18:** la premisa del encargo era FALSA —`force_build.py:11-16` y `release.yml:208` ya eran **idénticos** byte a byte—, así que la asimetría real estaba en `build.bat:27` y en el ejemplo de `docs/ai/sandbox-rules.md`, que compilaban SIN `--add-data assets;assets`. Fuente única `force_build.py` (la invocan `build.bat` y el job `build`). **7 guards**, y el que discrimina (AC-2) deriva su expectativa de `src/`: sin él, el bug de `build.bat:27` no lo mataba nadie |
| **TASK-077** | `pending` | low | Normalizar CRLF en `.bat`/`.ps1` (`git add --renormalize`) | |

> **Prioridad de ejecución:** `TASK-074` cerrado el 2026-10-18; siguiente del backlog, `TASK-075` (desacoplar `validate_docs.py` de `%LOCALAPPDATA%`, que hoy impide que corra en CI) → resto por prioridad.
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

- **`build.bat` devuelve "todo bien" aunque la compilación falle (CYCLE-065, `S3`):** **MEDIDO de extremo a extremo**: con un `force_build.py` que sale con 1, `build.bat` sale con **0**. El mismo `.bat` **sí sabe salir con 1** en su paso 1, luego no lo hace en el de compilar. `build.bat:27` invoca `python force_build.py` sin propagar el código, y `build.bat:40` tiene un `exit /b 0` incondicional. **No hay guard**: `errorlevel`, `exit /b` y `LASTEXITCODE` tienen 0 coincidencias en `run_tests.py`. El `.exe` roto llega por aquí, **no por CI** (`release.yml` sí propaga: el runner añade `exit $LASTEXITCODE` a `pwsh`). Fix: propagar el código + guard. Evidencia: `openspec/changes/2026-10-18-paridad-flags-pyinstaller/mutation-report.md`.
- **Shell intermitente (`spawn EPERM`):** El entorno de agentes bloquea subprocesos vía Node. Afecta a `tm.py` y a veces a `.taskmaster/git_safe_commit.py`. Workaround: reintentar. No tiene fix posible desde el repo. Blindado con el contrato de códigos de salida de `.taskmaster/git_safe_commit.py` (`docs/ai/sandbox-rules.md`).
- **`.git` corrupto (VFS Nextcloud):** El historial vive en `%LOCALAPPDATA%\woptimizer_git\.git`. Se acepta y se blinda con `.taskmaster/git_safe_commit.py --verify` (`docs/ai/sandbox-rules.md`).

### 🟢 Baja (CYCLE-063, abiertas y sin riesgo vivo)

- **H1 · el doc es más estricto que el código:** `sandbox-rules.md` (regla 4) exige que la línea `WOPT_*` sea la última impresa, pero el camino de **commit** imprime su `INFO no se intenta el .git…` **después** de `WOPT_REPO_INVALIDO`. El dev lo midió y lo declaró, no lo arregló: es otro cambio de contrato y merece tarea propia. Evidencia: `openspec/changes/2026-10-18-paridad-antes-del-repo-invalido/mutation-report.md`.
- **H2 · rigidez de la sonda AST:** `test_la_puerta_de_paridad_va_despues_de_validar_repo_por_estructura` (`run_tests.py`) exige `verify` como **primer** operando del `and`; `not ok and verify` la mata por «no encontrado», no por su aserción. Fallo ruidoso, no silencioso. Evidencia: `openspec/changes/2026-10-18-paridad-antes-del-repo-invalido/mutation-report.md`.
- **H3 · nombre que miente:** `test_la_puerta_de_paridad_va_despues_de_validar_repo` (`run_tests.py`) ya no mide la posición frente a `validar_repo` (esa posición es inobservable: `validar_repo` no imprime). Declarado en su docstring. Evidencia: `openspec/changes/2026-10-18-paridad-antes-del-repo-invalido/mutation-report.md`.

### 🟡 Media

- **A11 · `exentos = publicados - llamados` sin contraprueba (CYCLE-062, `TASK-079`):** Quitar el ` - llamados` de `_cuerpos_a_medir` (`run_tests.py`) deja el proyecto entero en verde: `ALL TESTS PASSED.`, 26 400 B. **No es alcanzable con el código real** — los únicos nombres publicados son `_handle_ok` y `_handle_err`, únicos y nunca llamados — así que no es un riesgo vivo, pero es una afirmación que la suite no somete a prueba. Es la **tercera** vez en este repo que aparece el patrón "una comprobación sin contraprueba no es una comprobación". Fix: control sintético en el test 205 que exija que esa resta cambie el resultado. Evidencia: `openspec/changes/2026-10-18-tkinter-after-guard/mutation-report.md` §11.
- **`build.bat` en LF (`TASK-077`, `pending`):** Tiene 39 LF y 0 CRLF pese a `.gitattributes eol=crlf`. Fix: `git add --renormalize .`. Verificable con `git ls-files --eol -- build.bat`.
- **11 ficheros `test_*.py` heredados:** **🔴 CERRADA en CYCLE-045 (TASK-055).** Archivados en `docs/archive/legacy-root-tests/`. Guard en `run_tests.py` impide que vuelvan a la raíz.
- **`validate_docs.py` no corre en CI (`TASK-080`, `pending`):** No es `%LOCALAPPDATA%`: MEDIDO el 2026-10-18 que el clon shallow del job `verify` da **154 FAIL** y que, aun con `fetch-depth: 0`, **25 de los ~150 hashes de `rd_journal.json` no son alcanzables desde ninguna rama del remoto** (están sin pushear, no perdidos). La exclusión es correcta; lo que faltaba era el motivo escrito. Detallado en `docs/ai/sandbox-rules.md Por que el validador NO corre en CI`.

### 🔵 Abiertas en CYCLE-064 (documentales, no tocan seguridad ni datos)

- **D1** (media): `validate_docs.py:293` afirma que `WOPTIMIZER_GIT_DIR` tiene "el mismo contrato" que `--git-dir`. MEDIDO: solo `--git-dir` se exige (repo inválido → FAIL propio); los otros tres peldaños caen en el FAIL del historial. Fix: reescribir el comentario con la asimetría real.
- **D2** (media): tres **"207" caducados** en `STATUS.md:106`, `docs/ai/testing-guide.md:57` y el badge de `README.md:6`; `testing-guide.md:57` se contradice además con `STATUS.md:12`. Son **invisibles** al check del recuento porque lee **una sola línea por fichero**. Fix: las tres cifras, y hacer que el check derive de varias líneas o de un marcador único.
- **D3** (baja): `release.yml` declarado con 193 líneas; tiene **215** (MEDIDO en TASK-076, 2026-10-18; eran 214 y este cambio movió una al reescribir el paso `build`). Cifra corregida, **deuda viva**: es un recuento escrito a mano sobre un fichero que se edita, la misma clase que D2, y se caducara otra vez en el siguiente cambio. Fix de fondo: derivarla o marcarla como "se declara al cierre del ciclo que toque el fichero". Evidencia: `openspec/changes/2026-10-18-validate-docs-ruta-y-degradacion/mutation-report.md`.
- **P1** (no medido **por presupuesto**): el registro de llamadas indecisas de `test_ninguna_llamada_de_cat_file_batch_check_se_queda_sin_input` (`run_tests.py`) creció 3 entradas documentadas (los `subprocess.run` de los flags del validador). Falta el mutante que compruebe que ese registro no se puede vaciar sin ponerse rojo. Evidencia: `openspec/changes/2026-10-18-validate-docs-ruta-y-degradacion/mutation-report.md`.

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
4. **Tests:** `python run_tests.py` (207 tests) · `python verify_ui_syntax.py` · `python validate_docs.py`.
5. **Docs vivas:** actualizar `docs/ai/` tras cada cambio arquitectónico.
6. **Carga selectiva:** no leer toda la doc — consultar `llms.txt` como mapa y cargar solo el fichero de `docs/ai/` que necesites.
7. **Pipeline de 4 pasos:** Buscar → Planear → Ejecutar → Auditar tests (mutation-auditor).

---

## 📋 Últimos Hitos (resumen compacto)

| Ciclo | Área | Qué se hizo |
|---|---|---|
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
