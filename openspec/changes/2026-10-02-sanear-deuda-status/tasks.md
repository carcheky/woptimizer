# tasks.md — Sanear las filas FALSAS de la Deuda Técnica Conocida

Contrato completo en `proposal.md`. Orden estricto: **T-0 antes que T-1**, porque T-0 fija la veracidad
de las cifras que el resto del panel declara.

Trampa del repo que aplica a este bloque: las filas que se tocan llevan emojis (`🧬`, `🔴`, `⚠️`, `🟡`,
`⚪`) y **deben coincidir carácter a carácter** con los que ya están. No se "normaliza" ninguno, y
`⚪ Otros` es U+26AA, no la interrogación ASCII.

---

## T-0. Las cifras del panel, antes que nada

- [ ] `STATUS.md:20`: «Ciclo Actual #47: TASK-057 — ... Completado» -> «**Ciclo Actual #48: TASK-058 —
      Sanear las filas FALSAS de la Deuda Técnica Conocida.** En curso». La linea 21 («Próxima Tarea:
      TASK-058») ya es correcta y no se toca.
- [ ] `docs/index.md:25`: «(96 tests)» -> «(103 tests)». Evidencia: recuento derivado con `ast` por
      `validate_docs.py:75-113` y confirmado en `AGENTS.md:68`.

## T-1. Las cuatro filas que hay que corregir (y la que hay que sustituir)

**Ninguna se borra.** Cada una conserva su redacción original —que es la evidencia de lo que se
creía— y gana el cierre con su comprobable. Precedente escrito en la propia sección, `STATUS.md:96`:
*borrar una fila sin evidencia es el mismo fallo que no haberla escrito*.

- [ ] **`STATUS.md:85`** — conserva «11 ficheros `test_*.py` heredados en la raíz están MUERTOS» como
      registro histórico y añade el cierre:
      (a) **no están en la raíz**, están en `docs/archive/legacy-root-tests/`, retirados por `TASK-055`
      en el ciclo #45 con su README (`docs/archive/legacy-root-tests/README.md:1-7`);
      (b) **10 de 11** morían por `import process_manager`; el único restante,
      `test_powershell_direct.py`, **no lo importa** y no estaba muerto: lanzaba `notepad.exe` y
      ejecutaba `taskkill` (`README.md:38-48`) — un riesgo distinto del que la fila describía;
      (c) «no se borran por decisión del propietario» -> **se archivaron**;
      (d) el guard que lo impide es `run_tests.py:11590 test_no_legacy_test_files_in_root`.
- [ ] **`STATUS.md:88`** — marca **CERRADA**: `python .taskmaster/git_safe_commit.py --verify` ->
      `WOPT_REPO_OK`, exit 0; HEAD `9da0949` + 8 commits del ciclo #47. El dato correcto y comprobable
      no es «sin commit» sino **«sin commit ANCLADO»**, y ese ya vive en `STATUS.md:93` con su
      severidad: esta fila queda como puntero a la 93, no como deuda abierta.
- [ ] **`STATUS.md:91`** — el cuerpo no se toca (tres hallazgos reales, cada uno con su test:
      `run_tests.py:2595`, `run_tests.py:3115`, `src/woptimizer/services/pack_service.py:40-41`).
      Se corrige **solo la cola**: «la ceguidad de las HOJAS es `TASK-031`» -> «cerrada con `TASK-031`
      (L1-L12)», porque `TASK-031.status == "completed"`.
- [ ] **`STATUS.md:92`** — marca **CERRADA en CYCLE-047** (`TASK-057`): el ancla ya no se deduce del
      journal, es la **unión** journal \| historial (`validate_docs.py:238 _ciclos_de_commits`,
      `validate_docs.py:267 _comprobar_ancla_de_commits`). Su residuo vive en `STATUS.md:93`.
- [ ] **`STATUS.md:97`** — conserva la fila como **CERRADA en CYCLE-044** por `TASK-054`
      (`run_tests.py:11478 test_docs_api_and_index_v3_contracts` la impide volver: cero residuos v2,
      métodos citados existentes en runtime, integridad del `nav`). **En su lugar entra una fila nueva
      y viva**: `docs/index.md:25` declara 96 tests y hay 103, y el check 7 no lo vigila porque su
      lista es de cuatro ficheros que no incluye ese (`validate_docs.py:115-119`). La fila nueva se
      escribe con su evidencia y su severidad, al nivel del estándar de la línea 93.

**Sin cambios:** `STATUS.md:86` (verificada hoy), `87` (solo se le añade que la intermitencia ya
costó un falso verde de versionado en el ciclo #11, `STATUS.md:37`), `89`, `93`, `94`, `95`, `96`.

## T-2. Lo que NO se toca y por qué (para que nadie lo «arregle»)

- [ ] `verify_exe.py:92` afirma auto-elevación y es **cierto**: `force_build.py:13`, `build.bat:27` y
      `.github/workflows/build.yml:21` compilan con `--uac-admin`. `CHANGELOG.md:729` ya registra que
      un análisis anterior concluyó lo contrario y estaba equivocado. **No hay deuda aquí.**
- [ ] `docs/index.md` ya no menciona la elevación porque el test #97 lo prohíbe, aunque el ejecutable
      sí la pide. Es una **omisión**, no una falsedad, y decidirlo es del propietario: no es una fila de
      deuda y no se escribe como tal.

## T-3. Registro y cierre

- [ ] `python run_tests.py` en verde (103 tests; el recuento no cambia en este ciclo).
- [ ] `python verify_ui_syntax.py` y `python validate_docs.py` en verde. Si `validate_docs.py` falla
      tras reescribir el panel, **es que una fila afirma algo que el validador puede comprobar**: eso
      es información, no un obstáculo a sortear.
- [ ] Entrada MANDATORY en `CHANGELOG.md` (raíz) **y** en `.taskmaster/CHANGELOG.md`.
- [ ] `.taskmaster/tasks.json`: `TASK-058` a `completed` con sus notas; **`TASK-060` queda `pending`**
      (el check 8, que se decide en `proposal.md` §5 y **no** se implementa aquí).
- [ ] Commit con `python .taskmaster/git_safe_commit.py "<mensaje>"` y línea `WOPT_*` + exit anotados.

---

# TASK-060 — check 8: la Deuda Técnica Conocida exige ancla en toda fila viva

**Se decide aquí, se implementa en su propio ciclo.** Especificación completa en `proposal.md` §5.

## El criterio, en una frase

> Toda fila de `## ⚠️ Deuda Técnica Conocida` que **no** esté marcada cerrada debe llevar al menos un
> ancla resoluble, y la verdad de su afirmación debe derivarse de **fuera** del panel: el árbol de
> ficheros, el recuento derivado con `ast` de `run_tests.py`, o `git log`. Las filas marcadas cerradas
> son registros históricos y quedan exentas.

- [ ] `_comprobar_deuda_con_anclas(root, errors, ok)` — **extraída con `root`**, por el motivo que ya
      pagó `TASK-037`: `main()` deriva `root` de `__file__` y no admite `argv`, así que sin
      extracción el check solo se despierta lanzando el validador entero contra el repo entero.
- [ ] Un solo test en `run_tests.py`, sobre `STATUS.md` sintético en `tempfile.mkdtemp()`:
      **A** fila viva con ancla no resoluble -> FAIL; **B** la *misma* fila marcada cerrada -> PASS
      (discrimina el fix de un check roto); **C** fila viva con número que contradice el recuento
      derivado con `ast` -> FAIL (mata el mutante «derivar del panel en vez del código»);
      **D** panel con solo filas cerradas -> PASS (control negativo: un guard que marca todo no vigila
      nada).
- [ ] Extender la lista del check 7 con `docs/index.md` y el patrón que ese fichero usa de verdad.
- [ ] Mutantes a cerrar por `mutation-auditor`: quitar la exención de cerradas (muere B), y sustituir la
      derivación `ast` por una lectura del propio `STATUS.md` (muere C).
