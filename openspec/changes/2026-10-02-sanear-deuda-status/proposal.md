# Sanear las filas FALSAS de la Deuda Técnica Conocida de `STATUS.md`

**Change ID:** `2026-10-02-sanear-deuda-status`
**Tarea:** `TASK-058` (ciclo #48)
**Alcance:** `STATUS.md` (seccion `## ⚠️ Deuda Tecnica Conocida` + cabecera de ejecucion) y `docs/index.md:25`.
**NO toca:** `src/woptimizer/**` (cero cambios de codigo de producto). `validate_docs.py` y `run_tests.py`
quedan para `TASK-060`: aqui solo se **decide** si el check debe existir.

---

## 1. Por que esta tarea no es cosmetica

El Paso 1 del bucle lee `## ⚠️ Deuda Tecnica Conocida` cuando el backlog esta vacio y prioriza lo
que ahi pone. Una fila falsa es la clase de fila que manda hacer un trabajo ya hecho. Ya ha pasado
dos veces en este repo, y las dos por la misma via:

- `STATUS.md:88` («Sin commit desde el ciclo #14») manda ejecutar `git_safe_commit.py` desde hace
  mas de treinta ciclos, con el repositorio ya versionado.
- El propio arquitecto, al replanificar `TASK-057`, encontro que la fila que la justificaba
  describia un estado que `TASK-057` acababa de cerrar.

El precedente de por que **no** se borran las filas ya cerradas esta escrito en la propia seccion,
linea 96, y es la regla que este contrato aplica a si mismo: *borrar una fila sin evidencia es el
mismo fallo que no haberla escrito*.

---

## 2. Auditoria fila por fila (13 filas, `STATUS.md:85-97`)

Cada veredicto lleva su evidencia. Una fila sin evidencia no se reescribe: se deja como estaba.

| L | Fila | Veredicto | Evidencia |
|---|------|-----------|-----------|
| 85 | 11 ficheros `test_*.py` **en la raiz** muertos por `import process_manager` | **FALSA** (por partida doble) | (a) No estan en la raiz: estan en `docs/archive/legacy-root-tests/` (11 ficheros), retirados por `TASK-055` en el ciclo #45 — `docs/archive/legacy-root-tests/README.md:1-7`, `run_tests.py:11590 test_no_legacy_test_files_in_root` (guard anti-regresion que exige cero `test_*.py` en la raiz). (b) Solo **10** de los 11 mueren por el import; `test_powershell_direct.py:1-5` **no** importa `process_manager`: lanzaba `notepad.exe` y ejecutaba `taskkill` (`README.md:38-48`). (c) «No se borran por decision del propietario» quedo caduco: **se archivaron**. |
| 86 | `.git` del arbol corrupto (VFS de Nextcloud) | **CIERTA** | `python .taskmaster/git_safe_commit.py --verify` -> `WOPT_REPO_OK C:\Users\carch\AppData\Local\woptimizer_git\.git`, exit 0 (2026-10-02). |
| 87 | Shell intermitente `spawn EPERM` | **CIERTA**, con su gravedad corregida | `AGENTS.md:16,114`, `docs/known-issues.md:155`, `.taskmaster/CHANGELOG.md:1723`, `.agents/agents/openspec-dev/agent.md:39`. Lo que hay que corregir es «Afecta al versionado, no al producto»: en el ciclo #11 esa misma intermitencia hizo que `git_safe_commit.py` saliera **con codigo 0 ante cualquier fallo de commit** y se perdieran commits (`STATUS.md:37`). No era inocua: era la causa de un falso verde de versionado. |
| 88 | **Sin commit desde el ciclo #14** | **FALSA** | `git log --oneline` sobre el historial desacoplado: `9da0949` (HEAD, cierre del #47) + `ae53be7`, `2f8c9c2`, `f98cebc`, `f10d9b4`, `614e5ff`, `dbe720d`, `9aa7dd5`. `git_safe_commit.py --verify` -> `WOPT_REPO_OK`, exit 0. |
| 89 | `CORRUPTION_ERRORS` no cubre `AttributeError` | **CIERTA** (cerrada) | `src/woptimizer/services/pack_service.py:37-41`: `AttributeError` entra por la guarda de forma `PerfilCorruptoError`, que si esta en la tupla. |
| 90 | El validador no comprueba la tabla resumen ni la seccion `Models` | **IMPRECISA** (una mitad cierta, otra a medias) | La mitad `Models` es **CIERTA**: cero coincidencias de `Models` en `validate_docs.py`. La mitad de la tabla resumen esta a medias: el encabezado `## CYCLE-NNN` si se exige y se avisa del enlace muerto de la tabla (`validate_docs.py:480-497`). El contenido de las filas de la tabla sigue sin comprobarse. |
| 91 | 3 SUPERVIVIENTES ABIERTOS (ciclo #17) | **CADUCADA en la cola** | El cuerpo esta cerrado con test discriminante: (a) `run_tests.py:2595 test_save_atomic_nunca_toca_el_principal`; (b) `run_tests.py:3115 test_oserror_de_lectura_no_es_corrupcion`; (c) `src/woptimizer/services/pack_service.py:40-41`. Y la cola «la ceguidad de las HOJAS es `TASK-031`» **apunta a una tarea cerrada**: `TASK-031.status == "completed"` en `.taskmaster/tasks.json`, cerrada con L1-L12 en `openspec/changes/2026-09-30-validate-pack-leaves/`. Un puntero a una tarea completada se lee como deuda viva y no lo es. |
| 92 | El validador deduce los ciclos obligatorios de los mismos ficheros que valida (ciclo #26) | **CADUCADA** | Cerrada en CYCLE-047 (`TASK-057`). El ancla ya no se deduce del journal: `validate_docs.py:238 _ciclos_de_commits(asuntos)` y `validate_docs.py:267 _comprobar_ancla_de_commits(root, errors, ok, journal_cycles)` hacen que el requisito sea la **union** journal \| historial. Su residuo vive, y con la severidad correcta, en la linea 93. |
| 93 | RESIDUO HONESTO del ciclo #47 | **CIERTA** — no se toca | Coherente con `validate_docs.py:238-267`. Es el estandar al que deben elevarse las demas filas. |
| 94 | CERRADA en CYCLE-027 (guardas que no guardaban) | **CIERTA** (cerrada) | Se conserva con su redaccion. |
| 95 | El recuento de tests iba por detras | **CIERTA** (cerrada) | El que vigila es el check 7, `validate_docs.py:115-158`: deriva el numero con `ast` y compara contra `STATUS.md`, `AGENTS.md`, `README.md` y la tabla de `docs/ai/testing-guide.md`. |
| 96 | Deuda del ciclo #26 transcrita y cerrada (8 filas) | **CIERTA** (cerrada) | El contenedor existe: `openspec/changes/2026-09-30-pack-telemetry-feedback/deuda-ciclo-26.md`. |
| 97 | `docs/api.md` y `docs/index.md` documentan una API de la v2 | **FALSA en su premisa** | Cero coincidencias de `is_admin`, `taskkill` o `elevacion` en ambos ficheros. `docs/api.md:1` es «Referencia de API (v3)» y describe `psutil`. Cerrada en **CYCLE-044** por `TASK-054`, con test discriminante en `run_tests.py:11478 test_docs_api_and_index_v3_contracts`. |

### Hallazgo adyacente, fuera de la seccion pero de la misma clase

- **`STATUS.md:20` dice «Ciclo Actual #47: TASK-057 — Completado»** mientras la linea 21 dice
  «Proxima Tarea: TASK-058», que es el ciclo #48. El ciclo actual es **#48**. Es exactamente el
  defecto que el check 7 impidio en el recuento de tests y que nadie vigila en la cabecera.

### Lo que vive debajo de la fila 97 (la deuda real que la fila describia mal)

`test_docs_api_and_index_v3_contracts` (`run_tests.py:11478`) prohibe residuos v2 y verifica el `nav`
de `mkdocs.yml`, pero **no vigila el recuento de tests**. Y hay un fallo vivo, del mismo tipo que el
que el check 7 ya cazó una vez:

- **`docs/index.md:25` declara «(96 tests)» y la verdad son 103.** El check 7 no lo ve porque su
  lista es de cuatro ficheros y `docs/index.md` no esta en ella (`validate_docs.py:115-119`).
- **Descartado con evidencia, no por opinion:** `verify_exe.py:92` afirma auto-elevacion y es
  **cierto** — `force_build.py:13`, `build.bat:27` y `.github/workflows/build.yml:21` compilan con
  `--uac-admin`. `CHANGELOG.md:729` ya registra que un analisis anterior concluyo lo contrario y
  estaba equivocado. No hay deuda aqui. Lo que si es una **omision** de `docs/index.md`: la portada
  ya no dice que el ejecutable pide administrador. Decision del propietario, no fila de deuda.

---

## 3. Las tres premisas del briefing que no se sostienen

1. **«La fila de los 11 `test_*.py` muertos mezcla dos casos: no todos mueren por `import process_manager`.»**
   Cierta, pero incompleta: la fila tambien dice **«en la raiz»**, y hace treinta y cinco dias que no
   estan ahi. Sin el dato de la ubicacion, la correccion propuesta deja en pie la parte mas
   peligrosa de la fila.
2. **«La fila de `docs/api.md` y `docs/index.md` tiene su severidad mal puesta.»** La severidad mal
   puesta era la de ciclo #44 (`mkdocs.yml:70,72` los publica como `Inicio` y `API reference`), y
   **ese punto ya se consumio**: `TASK-054` esta `completed`, reescribio ambos documentos y dejo el
   test que lo impide volver. Lo que queda no es una fila que «poner al dia»: es una fila **caducada**
   mas un fallo vivo y distinto (`docs/index.md:25`).
3. **El criterio de aceptacion de `TASK-058` que pide «actualizar la fila de `docs/api.md` con su
   severidad real» esta construido sobre un estado del repo que ya no existe.** Si `openspec-dev` lo
   ejecuta tal cual, va a reescribir una fila cerrada y a reintroducir en el panel una afirmacion que
   el ciclo #44 demostro falsa. Hay que reescribir el criterio antes de ejecutarlo.

---

## 4. Que se hace con cada fila FALSA o CADUCADA

**Ninguna se borra.** Las cuatro se conservan con su redaccion original —que es evidencia de lo que
se creia— y se les anade el cierre con su comprobable. Es el mismo trato que reciben las filas 94, 95
y 96, y la razon ya esta escrita en la linea 96 de la propia seccion.

| L | Accion | Como queda |
|---|--------|------------|
| 85 | **CORREGIR conservando el registro** | Se conserva «11 ficheros `test_*.py` heredados en la raiz estaban MUERTOS» como registro historico, y se anade el cierre: **archivados** (no «conservados en la raiz») en `docs/archive/legacy-root-tests/` por `TASK-055` en el ciclo #45, vigilado por `run_tests.py:11590`; y de los 11, **10** morian por `import process_manager` y el unico restante (`test_powershell_direct.py`) no: lanzaba `notepad.exe` y `taskkill`, un riesgo distinto del que la fila describia. |
| 88 | **CORREGIR conservando el registro** | Se conserva la afirmacion y se marca **CERRADA** con `WOPT_REPO_OK` exit 0 y HEAD `9da0949`. El dato correcto y comprobable no es «sin commit» sino **«sin commit ANCLADO»**, y ese ya vive, con su severidad, en la linea 93. La fila queda como puntero a la 93, no como deuda. |
| 91 | **CORREGIR solo la cola** | El cuerpo no se toca (son tres hallazgos reales con su test). Se corrige «la ceguidad de las HOJAS es `TASK-031`» por «cerrada con `TASK-031` (L1-L12)». |
| 92 | **CORREGIR** | Se marca **CERRADA en CYCLE-047** con `validate_docs.py:238,267` y se remite a la linea 93 para el residuo, que es donde vive con su severidad. |
| 97 | **SUSTITUIR conservando el registro** | Se conserva como **CERRADA en CYCLE-044** por `TASK-054` (test en `run_tests.py:11478`). Y en su lugar entra una fila **nueva y viva** con la deuda real: `docs/index.md:25` declara 96 tests y hay 103, y el check 7 no vigila ese fichero. Esa fila nace con su mutante y su severidad, como la 93. |

La fila nueva no es una invencion del arquitecto: es un fallo medido, en un fichero que `mkdocs.yml:70`
publica como la portada del sitio, que ningun check cubre.

---

## 5. La pregunta de fondo: ¿debe `validate_docs.py` vigilar este panel?

**Veredicto: SI, pero no en este ciclo, y no como «comprobar las filas» sino como «exigir ancla a las
filas vivas».**

### Coste

Una funcion extraida con `root` (~40 lineas) mas un test en `run_tests.py` sobre arbol sintetico. Es
exactamente la forma del check 7, que ya existe, ya esta probado y ya ha cazado un fallo real de este
mismo tipo. El precedente no es una conjetura: es codigo en el repo. La extraccion con `root` es
**obligatoria** por el motivo que ya pago `TASK-037`: `main()` deriva `root` de `__file__` y no admite
`argv`, asi que un check que solo se despierta lanzando el validador entero contra el repo entero es un
check que nadie ejecuta.

### Beneficio

El panel es la **entrada de mayor palanca del bucle**: cuando el backlog esta vacio, el Paso 1 prioriza
literalmente lo que dice esa seccion. En las 13 filas auditadas **mintieron tres** (85, 88, 97) y dos de
ellas no las detecto nadie. Un `0 FAIL` sobre este panel no prueba hoy absolutamente nada, que es
literalmente lo que la propia linea 92 denuncia del validador del ciclo #26 y lo que la linea 90 dice
de si misma.

### El criterio discriminante

> **Toda fila de `## ⚠️ Deuda Tecnica Conocida` que NO este marcada cerrada debe llevar al menos un
> ancla resoluble, y la verdad de su afirmacion debe derivarse de FUERA del panel**: el arbol de
> ficheros, el recuento derivado con `ast` de `run_tests.py`, o `git log`. Las filas marcadas cerradas
> son registros historicos, no afirmaciones vivas, y quedan exentas.

La exencion de las cerradas es lo que hace el check utilizable: sin ella habria que exigir anclas a las
filas 94, 95 y 96, que son deliberadamente narrativas, y el check fallaria siempre, luego nadie lo
miraria. Un guard que marca todo no vigila nada — es la misma leccion de `test_el_alcance_del_guard_de_llamantes_se_deriva_del_arbol`.

Y la regla de «derivar de fuera» es la que impide repetir el fallo de la linea 92: si el check dedujera
la verdad del propio panel, seria el mismo validador que se audita a si mismo.

### Los tres fallos que tiene que cazar

1. Una fila que nombre una ruta que ya no esta ahi (85: «en la raiz»).
2. Una fila cuya afirmacion contradiga un testigo externo (88: commits; 97: contenido del documento).
3. Una fila que apunte a una tarea cerrada como si siguiera viva (91 -> `TASK-031`).

### El test que lo prueba (y por que discrimina)

Un solo test en `run_tests.py`, sobre un `STATUS.md` sintetico en `tempfile.mkdtemp()`, con cuatro
escenarios:

- **A** fila viva con un ancla que no resuelve -> **FAIL**.
- **B** la **misma** fila marcada cerrada -> **PASS**. Este es el que discrimina: sin el, el check
  pasa por exigir anclas a todo y B no distingue el fix de un check roto.
- **C** fila viva con un numero que contradice el recuento derivado con `ast` -> **FAIL**. Mata al
  mutante «derivar del panel en vez del codigo».
- **D** panel sintetico con solo filas cerradas -> **PASS** (control negativo: un guard que marca todo
  no vigila nada).

Mutantes esperados: quitar la exencion de cerradas (muere A/B), sustituir la derivacion por `ast` por
una lectura del propio `STATUS.md` (muere C).

### Ademas, y esto si cabe en este ciclo

`docs/index.md:25` se corrige a 103, y el criterio de la lista del check 7 se extiende para que
`docs/index.md` entre en ella con el patron que ese fichero usa de verdad — el mismo principio que ya
esta escrito en `validate_docs.py:128-133`: *un validador que no encuentra lo que valida no es un
validador*. La extension del check 7 es de una linea; el check 8 completo es `TASK-060`.

---

## 6. Ficheros que toca el Paso 3 (`openspec-dev`)

| Fichero | Cambio |
|---------|--------|
| `STATUS.md:85` | Corregir conservando el registro: archivados en `docs/archive/legacy-root-tests/` (`TASK-055`, ciclo #45), 10 de 11 por `import process_manager`, el 11o lanzaba `notepad.exe`; guard `run_tests.py:11590`. |
| `STATUS.md:88` | Marcar CERRADA con `WOPT_REPO_OK` exit 0 y HEAD `9da0949`; remitir el dato real («sin commit ANCLADO») a la linea 93. |
| `STATUS.md:91` | Corregir solo la cola: `TASK-031` esta cerrada. |
| `STATUS.md:92` | Marcar CERRADA en CYCLE-047 con `validate_docs.py:238,267`; remitir el residuo a la linea 93. |
| `STATUS.md:97` | Conservar como CERRADA en CYCLE-044 (`TASK-054`, test `run_tests.py:11478`) y sustituir por la fila viva de `docs/index.md:25`. |
| `STATUS.md:20` | «Ciclo Actual #47» -> «Ciclo Actual #48: TASK-058». |
| `docs/index.md:25` | 96 -> 103 tests. |
| `.taskmaster/CHANGELOG.md` + `CHANGELOG.md` | Entrada MANDATORY del ciclo, en los dos. |
| `.taskmaster/tasks.json` | `TASK-058` a `completed` con sus notas; `TASK-060` (check 8) queda `pending`. |

Sin cambios: `STATUS.md:86, 89, 93, 94, 95, 96`. Sin cambios en `src/woptimizer/**`.
