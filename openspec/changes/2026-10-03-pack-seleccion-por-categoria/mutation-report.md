# Mutation report: `2026-10-03-pack-seleccion-por-categoria` (TASK-063, ciclo 51)

**Rol:** `mutation-auditor` (Paso 4 del bucle). **Pregunta:** *¿el test se enteraría si el código estuviera mal?*
**Commit auditado:** `e0f20db` — "feat(categorias): puerta comun execute_pack con las barreras DENTRO (TASK-063 T-1/T-3)".
**Método:** 22 mutantes, cada uno aplicado sobre una **copia en `%TEMP%`**, uno a uno, purgando `__pycache__` entre mutaciones. El árbol del proyecto **no se ha tocado** (verificado al final, §6).

> **Nada se ha reparado.** Los supervivientes se reportan; los arregla `openspec-dev`.

---

## 0. VEREDICTO

# 🔴 FAIL

**5 supervivientes**, de los cuales **3 son de la zona anti-brick** (la barrera que separa este código de matar procesos del sistema).

| Severidad | Id | Qué se rompe si el código se rompe así |
|---|---|---|
| 🔴 **CRÍTICA** | **S1** | La barrera roja de `_pack_evaluable` se puede **borrar entera** y los 120 tests siguen en verde. Probado en producción: abre de verdad el anti-brick (ver §3) |
| 🔴 **ALTA** | **A5** | `_patrones_de_categoria` deja de añadir `.exe` ⇒ **"arrancar por categoría" no arranca NADA** (9 de 9 nombres rechazados). Ningún test lo ve porque el doble del arnés sobrescribe el método |
| 🟠 **ALTA** | **S7** | El filtro escribe en el pack **original** en vez de en una copia ⇒ el `profiles.json` del usuario se corrompe en memoria. Su propio docstring dice *"NUNCA el original"* |
| 🟠 **MEDIA** | **U1** | El gate `if pack.is_gaming:` vuelve a envolver el acordeón (118 líneas, casillas incluidas) y el test #3 **no lo detecta**: su predicado AST solo mira `text=` que sea `ast.Constant`, y las casillas usan f-strings |
| 🟡 **BAJA** | **Z1** | La barrera se duplica en `execute_gaming_pack` sin cambiar nada. **Equivalente**: el filtro de la puerta común ya la aplica. No es un fallo |

**Los tres mutantes que `tasks.md` declara como "los que más costarían dejar pasar" están medidos, y dos de ellos no los caza el test que el plan nombra:**

| Mutación declarada en `tasks.md` | Quién la caza | Veredicto |
|---|---|---|
| 1. "Quitar la barrera 🔴 de la puerta común dejando la de `execute_gaming_pack`" | **nadie** (S1, S1Z1) | 🔴 **sobrevive** |
| 2. "Comparar los keepers contra el nombre sin extensión" | **#1 y #8**, por su aserción | ✅ **muere** |
| 3. "Dejar `_last_closed_apps` sin condicionar" | **#11**, y mira la lista | ✅ **muere** |

---

## 1. AISLAMIENTO (la trampa del gitlink, medida antes de mutar nada)

Este repo tiene **`.git` como FICHERO** de 57 bytes (`gitdir: C:/Users/carch/AppData/Local/woptimizer_git/.git`). `robocopy /XD .git` **no lo evita**: `-XD` excluye directorios.

Protocolo aplicado: copia con `shutil.copytree(..., ignore=shutil.ignore_patterns(".git"))` —`ignore_patterns` cubre ficheros **y** directorios—, `GIT_DIR` **desechable y explícito** por worker, y prueba de aislamiento **antes** de la primera mutación:

```
prueba_aislamiento_rev_parse = C:\...\Temp\wopt_mut51_git_w1_044946\repo.git
entradas_dotgit dentro de la camara = []   (ninguna)
```

Cuatro cámaras, cuatro `GIT_DIR` nuevos, los cuatro aislados. **Ninguna cámara se commitearon al repo real.**

---

## 2. TABLA COMPLETA: fix → mutación → veredicto → motivo literal

`killed` = algún test muere **por la aserción que dice comprobar**. En la columna "muere" va el número del test de TASK-063 cuando lo mata uno de los quince; si lo mata un test **preexistente** del ciclo anterior, se dice así.

### 2.1 Puerta común y barreras (S)

| Id | Mutación | Veredicto | Motivo literal / quién muere |
|---|---|---|---|
| **S1** | `_pack_evaluable`: quitar el filtro `get_safety_badge(c)["tier"] != "danger"` de `target_categories` | 🔴 **SOBREVIVE** | `ALL TESTS PASSED` (120/120). Ninguno de los 15 muere. **Probado que no es equivalente**: con la DB recalculando `svchost` a rojo mientras el snapshot dice verde, el control no mata nada y S1 **sí manda `svchost.exe` a `kill_processes`** |
| **Z1** | `execute_gaming_pack`: duplicar la barrera roja ahí | 🟡 **equivalente** | `ALL TESTS PASSED`. El filtro de la puerta común ya la aplica; duplicarla no cambia el comportamiento. **No es un fallo** |
| **S1Z1** | S1 + Z1 (= la mutación #1 tal cual la declara `tasks.md`) | 🔴 **SOBREVIVE** | `ALL TESTS PASSED`. El test #5 **no la caza**; lo que la mata es caer también G5 (§2.5) |
| **S2** | `nombre = p.full_name or p.name` → `nombre = p.name` (G3) | ✅ **MUERE** | **#1 y #8**. `AssertionError: solo onedrive debe morir (categoria marcada); el keeper y el ajeno no. Llegaron: ['discord.exe', 'onedrive.exe']` — el keeper `discord.exe` **murió**: exactamente el fallo silencioso que la mutación declara |
| **S3** | `if pack.is_gaming:` → `if True:` en el bloque de `_last_closed_apps` (H1) | ✅ **MUERE** | **#11**. `AssertionError: apagar un pack NORMAL sobreescribio la sesion Gaming pendiente: el banner 'Reabrir' aparece fantasma y, si se pulsa, restore_gaming_session() la vacia y destruye la restauracion real` |
| **S4** | `_seleccion`: quitar G5 (barrera sobre `p.category` del snapshot) | ✅ **MUERE** | **#5** y preexistente. `AssertionError: skipped debe sumar los descartes del filtro (svchost y lsass): 1` |
| **S5** | `_seleccion`: quitar G4 (`is_system_protected` de nombres) | ✅ **MUERE** | **#5** y preexistente. Mismo aserto que S4, con el blindaje de nombres |
| **S6** | `get_running_processes(force_refresh=True)` → `False` (G0) | ✅ **MUERE** | **#10** y preexistente. `AssertionError: G0 es obligatorio: sin force_refresh=True la cache TTL de 2 s puede dejar fuera lo que el usuario acaba de lanzar` |
| **S7** | `_pack_evaluable`: escribir en `pack` original en vez de `model_copy` | 🟠 **SOBREVIVE** | `ALL TESTS PASSED`. **Probado que no es equivalente**: el control conserva `target_categories` del original; con S7 queda **vaciado** (`[]`), o sea la selección del pack del usuario se pierde en memoria. Ningún test mira el pack tras la puerta |
| **S1S4** | S1 + S4 (las **dos** barreras rojas fuera) | ✅ **MUERE** | **#5, y solo #5**. `AssertionError: solo onedrive debe llegar a kill_processes (categoria verde marcada): llegaron ['svchost.exe', ...]`. Es el ladrillo del ciclo #14, cazado por su aserción |
| **S4S5** | S4 + S5 (barrera de categoría **y** blindaje de nombres fuera) | ✅ **MUERE** | **#5**. `AssertionError: skipped debe sumar los descartes del filtro (svchost y lsass): 0` |

### 2.2 Arranque por categoría (A)

| Id | Mutación | Veredicto | Motivo literal / quién muere |
|---|---|---|---|
| **A1** | `start_pack_categories`: quitar la barrera de categoría roja | ✅ **MUERE** | **#6**. `AssertionError: una categoria roja debe ser INERTE tambien al arrancar: started=1 lanzados=['...\svchost.exe']` — **arrancó el ejecutable de prueba** |
| **A2** | Quitar la resolución del conflicto `start ∩ target` | ✅ **MUERE** | **#7**. `AssertionError: la categoria marcada para apagar no puede arrancar: started=1` |
| **A3** | `ruta is None` → `started += 1` en vez de `failed += 1` (H4: el `started` mentiroso) | ✅ **MUERE** | **#4**. `AssertionError: solo el ejecutable que resuelve debe arrancar: started=2 lanzados=['...\woptimizer_t063_ok.exe']` — el nombre inexistente cuenta como iniciado |
| **A4** | `categorias_disponibles`: no descartar el centinela `\u26aa Otros` | ✅ **MUERE** | Preexistente (`test_default_meta_matches_canonical_otros`). `AssertionError: categorias_disponibles() devolvio el centinela: [... '\u26aa Otros']` — **y aparece en la lista** |
| **A5** | `_patrones_de_categoria`: `nombres.append(f"{patron}.exe")` → `nombres.append(patron)` | 🔴 **SOBREVIVE** | `ALL TESTS PASSED`. **Probado que no es equivalente**: contra la DB real el control devuelve 9/9 nombres **con** `.exe`; con A5, **0/9**. Como `_resolver_app` exige `.exe`/`.com`, **"arrancar por categoría" no arranca nada**. El test #4 no lo ve porque `_ServicioDeArranque` **sobrescribe `_patrones_de_categoria`** con nombres que ya traen `.exe` |

### 2.3 Las cuatro guardas y el cableado (V)

| Id | Mutación | Veredicto | Motivo literal / quién muere |
|---|---|---|---|
| **V1** | Gestor: `if not pack.apps and not pack.target_categories:` → `if not pack.apps:` (G-b) | ✅ **MUERE** | **#2**. `AssertionError: un pack con categorias marcadas tiene algo que apagar; el aviso (no tiene apps que apagar) miente sobre lo que la puerta va a hacer` |
| **V2** | Portada: la misma guarda (G-d) | ✅ **MUERE** | **#2**. `AssertionError: la guarda de la Portada corto con [... 'Trabajo' no tiene apps que a...` |
| **V3** | Portada arranque: `and not pack.start_categories` fuera | ✅ **MUERE** | **#12**. `AssertionError: la puerta de arrancar debe ejecutar start_categories: []` — nunca llegó a arrancar |
| **V4** | `es_pack_inerte` vuelve **antes** de la rama del verbo | ✅ **MUERE** | **#12**. Mismo aserto: el pack de arranque oye el diagnóstico de la otra puerta |
| **V5** | El texto de confirmación vuelve a `len(pack.apps)` | ✅ **MUERE** | **#15**. `AssertionError: el texto debe decir lo que la puerta va a hacer (3 en este snapshot): "Segunda pulsación para apagar 0 procesos de 'Trabajo' (0 apps y ..."` |
| **V6** | `cuenta_a_apagar` → `return len(pack.apps)` | ✅ **MUERE** | **#15**. Mismo aserto: el número del texto sale de otra política |
| **V7** | El Gestor vuelve a `process_service.kill_pack_apps(pack.apps)` (la puerta existe pero **no se usa**) | ✅ **MUERE** | **#2** y preexistente. `AssertionError: el pack se cierra por la puerta comun con SUS apps, no con un atajo ni con una lista vacia (llego ['C:\Juegos\juego.exe'])` — **el "código escrito y nadie lo llama" está cubierto** |
| **V8** | El worker llama a `restore_gaming_session()` (una llamada **no permitida**) | ✅ **MUERE** | **#2** y el guard de workers. `AssertionError: el worker toca la vista fuera de self.after(0, ...): PackManagerView.kill_pack:L636 self.gaming_service.restore_gaming_session(...) desde el hilo` — **la tupla `PERMITIDOS` sigue temiendo lo mismo** |

### 2.4 El acordeón y el modelo (U, M)

| Id | Mutación | Veredicto | Motivo literal / quién muere |
|---|---|---|---|
| **U1** | `if pack.is_gaming:` vuelve a envolver el acordeón entero (**118 líneas**, casillas incluidas) | 🟠 **SOBREVIVE** | `ALL TESTS PASSED`. **Probado que no es equivalente**: el `ast` pasa de 3 gates a 4, y el nuevo (línea 346) tiene `construye_checkbox=true`. Un pack normal se queda **sin dónde elegir categorías** mientras el servicio se las pregunta igual |
| **U2** | El espejo `v_arrancar.set(0)` desaparece | ✅ **MUERE** | **#3**. `AssertionError: el conflicto debe evitarse en la UI deseleccionando la gemela al marcar la otra` |
| **U3** | La vista vuelve a leer `process_db` | ✅ **MUERE** | **#3 y #14**, y el guard de capas. `AssertionError: Separacion de capas: la UI no puede leer la DB de procesos (ui\views\pack_manager_view.py)` |
| **M1** | `start_categories: List[str] = Field(default_factory=list)` → `= None` | ✅ **MUERE** | Preexistente. `AssertionError: update_pack() tiene que persistir en el fichero; leido del disco: 'kill'` |

### 2.5 La mutación que sí representaba el ladrillo

Ni S1 ni S1Z1 —las dos que declara el plan— lo abrían, porque **G5 (la barrera sobre la categoría del snapshot) tapa a G1**. El ladrillo de verdad es **las dos a la vez**, y ese sí lo caza el **#5, y solo el #5**:

```
S1S4  ->  #5 AssertionError: solo onedrive debe llegar a kill_processes
              (categoria verde marcada): llegaron ['svchost.exe', ...]
       ->  #1..#4, #6..#15 todos PASO
```

Es decir: **la cobertura de las dos barreras es asimétrica.** Quitar G5 la caza un test; **quitar G1 no la caza ninguno**.

---

## 3. S1: POR QUÉ ES EL HALLAZGO MÁS GRAVE Y POR QUÉ NO ES UN EQUIVALENTE

Un superviviente solo es «equivalente» si el comportamiento no cambia. Se midió con un doble idéntico al del arnés (hereda `ProcessService`, así que `_categorize` lee la DB de verdad):

| Escenario | Control | **S1** | S1Z1 |
|---|---|---|---|
| Snapshot **ROJO**, DB **ROJO** (el caso de siempre: `svchost` con su categoría real) | `[]` | `[]` | `[]` |
| Snapshot **VERDE**, DB **ROJO** (discrepancia) | `[]` | **`['svchost.exe']`** | **`['svchost.exe']`** |

Medido dos veces, mismo resultado. **S1 cambia el comportamiento**: manda `svchost.exe` a `kill_processes`.

**¿Y es alcanzable en producción?** Sí, y está medido en el código:

- `_seleccion` evalúa G5 con **`p.category`** (del snapshot, `process_service.py:506`).
- `should_kill_for_gaming` recalcula con **`_categorize(nombre)`** (`gaming_service.py:65`), que vuelve a la DB.

Los dos llaman a `_get_process_meta`, pero **no en el mismo instante**: `load_db_async` corre en un **hilo secundario** (`process_service.py:415`) y al aterrizar la descarga hace `self._db_map = db_map` y `self._meta_cache.clear()` (`process_service.py:365-366`). Si la descarga entra **entre** el snapshot y la selección, la misma DB puede reclasificar un nombre como rojo mientras el snapshot todavía dice verde. Con G1 ausente, ese proceso llega a la matanza. La ventana es estrecha, pero **no es un escenario sintético**: es exactamente el motivo por el que el ciclo #14 reservas la barrera dentro de la puerta.

**Consecuencia arquitectónica, y es la grave:** el `proposal.md` §2.4 y `architecture.md` §11.1 explican que las barreras están **dentro** de la puerta "porque un llamante nuevo no puede saltárselas porque no las tiene". Con S1 el código sigue **pareciendo** a prueba de anti-brick (los comentarios, el docstring y los tests #4/#5 siguen ahí), pero **una de las dos redes ya no está** y nada en la suite lo dice. Eso es un falso verde en la zona que este repo ya pagó cara.

**Arreglo que necesita (no aplicado):** un test que mute **solo** G1 con un snapshot cuya categoría **diverja** de la DB, o — más simple y más fuerte — un aserto explícito de que `_pack_evaluable` **vacía** una `target_categories` con categoría roja (hoy nadie mira la lista de salida de esa función).

---

## 4. AUDITORÍA DOCUMENTAL (afirmaciones comprobadas contra el código)

| Documento | Afirmación | Medido |
|---|---|---|
| `docs/ai/testing-guide.md` fila 109 | *"`killed == 1` (el verde)"* | ❌ **FALSO**. El doble `_ProcessServiceSpy.kill_processes` **devuelve siempre `(2, 0, 0, 12.5)`** (`run_tests.py:685`); el propio test lo admite en su comentario (`:14335`). `killed` **no dice nada** sobre la lista |
| `docs/ai/architecture.md` §11.1 | *"`killed == 0`"* para el mismo test | ❌ **FALSO, y además CONTRADICE al otro documento** (0 vs 1). Los dos docs afirman una cifra que el doble no puede dar. El discriminante real es la lista capturada y `skipped`, como el propio test dice |
| `docs/ai/testing-guide.md` fila 109 | *"Si la barrera se queda pegada a `execute_gaming_pack`, **todos** los tests de Gaming siguen verdes y **solo este** cae"* | ❌ **FALSO, medido**: esa mutación (S1Z1) deja los 120 en verde. Lo que la caza es caer **también** G5 (S1S4) |
| `docs/ai/ui-design-system.md`, tabla de las 4 guardas | Las cuatro guardas y sus listas | ✅ **CIERTO** (4/4 verificadas en `pack_manager_view.py:561,563,643` y `dashboard_view.py:441,449`) |
| `docs/ai/data-models.md` §1.1 | Contrato de `start_categories`: default `[]`, ausente == vacío, no es `None`, conflicto resuelto en el servicio | ✅ **CIERTO** contra `models.py:64` y `process_service.py:933-947`. Mutado a `None` (M1) y **muere** |
| `docs/ai/data-models.md` §1.1 | *"las cinco copias del pack van con `model_copy(deep=True)`"* | ✅ CIERTO (no se ha tocado `pack_service.py`) |
| `docs/ai/testing-guide.md` | 120 tests, 95 backend + 25 headless, una fila por test | ✅ **CIERTO y mecánico**: `validate_docs.py` deriva el número con `ast` y compara contra los cuatro ficheros → **119 OK / 0 FAIL** |
| `docs/ai/*` | Rango del blindaje `process_service.py:35-50` | ✅ **CIERTO**: lo mide `ast` un test contra el código real |

### Los cuatro invariantes **migrados, no abiertos** (FIX-005, guard de capas, `PERMITIDOS`, `llamadas_cierre == 1`)

Una migración afloja una garantía para que algo pase. Las cuatro se comprobaron **contra el mutante**, no leyendo el código:

| Invariante | Cómo se migró | Mutante sonda | Veredicto |
|---|---|---|---|
| Centinela (FIX-005) | De la vista al servicio, ejecutando `categorias_disponibles()` de verdad **+** un guard nuevo que prohíbe que la vista vuelva a compararlo | **A4** | ✅ **sigue temiendo lo mismo, y más**: el centinela aparece en la lista y el test lo ve |
| Guard de capas | Se **amplió**: el predicado `process_db` es nuevo y la lista de ficheros pasó de 4 a **6** | **U3** | ✅ **sigue temiendo**: muere por la capa **y** por #3/#14 |
| Tupla `PERMITIDOS` | Se **amplió** con `start_pack_categories` y `execute_pack`; los pares viejos se quedan | **V8** (una llamada no permitida) | ✅ **sigue temiendo**: el guard la acusa |
| `llamadas_cierre == 1` | Migrado a `gaming.llamadas == 1` + `procs.llamadas_cierre == 0` (afirmar **qué** puerta se cruzó, no solo cuántas veces) | **V7** | ✅ **sigue temiendo, y más fuerte**: ahora además muere si el pack entra por la puerta **restringida** |

**Las cuatro migraciones son Netas: ninguna aflojó su garantía.** Es lo contrario de lo que se temería de una migración.

---

## 5. `dist/woptimizer.exe`: MEDIDO, Y LA DECLARACIÓN DEL DEV ES INCORRECTA

El dev declaró que el `.exe` **no** se regeneró. Se midió por contenido, no por fecha:

**Por qué `mtime` no bastaba:** el `.exe` (27.040.542 bytes) es de `2026-10-03 04:49:42`, y `src/` de `04:24`–`04:26`. A primera vista parece *más* nuevo. Pero comparar cadenas sueltas en el `.exe` **no prueba nada**: PyInstaller comprime los `.pyc` dentro de `PYZ`, y un sondeo ingenuo da **0 hits tanto para el código viejo como para el nuevo** (medido: 0/6 y 0/1).

**Medición real:** se extrajo el `PYZ` con `CArchiveReader` y se descomprimieron los **code objects** con `ZlibArchiveReader`, y se buscaron docstrings y literales **dentro** del bytecode.

| Huella | Módulo en el `.exe` |
|---|---|
| `execute_pack`: *"Es la UNICA puerta de apagado por pack del producto"* | ✅ `gaming_service` |
| `_pack_evaluable`: *"G1 - barrera de categoria roja sobre `target_categories`"* | ✅ `gaming_service` |
| `cuenta_a_apagar`: *"Sale del MISMO filtro que"* | ✅ `gaming_service` |
| `execute_gaming_pack`: *"TASK-063: wrapper de compatibilidad"* | ✅ `gaming_service` |
| texto honesto de la doble pulsación (`procesos de '`) | ✅ `feedback` |
| segunda tanda del grid, columna `(arrancar)` | ✅ `pack_manager_view` |
| **PREVIO:** `"Overlays e Info"` (catálogo a mano, ya eliminado) | ❌ ausente |
| **PREVIO:** `para apagar {len(pack.apps)} apps` | ❌ ausente |

**Medido: 6/6 huellas del ciclo 51 dentro, 0/2 del código previo.**

> ⚠️ **Dos falsos negativos míos, declarados para que nadie los repita como evidencia:** (a) `TASK-063` aparece en el `.exe` **solo dentro de un docstring** (`execute_gaming_pack`), porque los comentarios los borra el compilador — buscar `TASK-063` como prueba de build da `NO` en un binario sano; (b) el docstring dice **"UNICA" sin tilde**, y un sondeo con `ÚNICA` no encuentra nada. Ambos "NO" eran fallos del **sondeo**, no del ejecutable.

### Veredicto: NO es deuda viva

El `.exe` **contiene el código del ciclo 51** y **no** contiene el código previo. No hay nada que regenerar: la declaración del dev era incorrecta, y el binario está al día. La prueba de que la puerta común está **en el ejecutable** —y no solo en el árbol— es que `_pack_evaluable`, `_seleccion` y `cuenta_a_apagar` existen dentro del `.pyc` de `gaming_service`.

---

## 6. CONTRATO: EL ÁRBOL DEL PROYECTO NO SE HA TOCADO

Verificado al terminar, desde la raíz del repositorio:

```
git log --oneline -1        e0f20db feat(categorias): puerta comun execute_pack con las barreras DENTRO (TASK-063 T-1/T-3)
git status --porcelain      (vacío)
git diff --stat             (vacío)
git diff --cached --stat    (vacío)
git rev-parse --git-dir     C:\Users\carch\AppData\Local\woptimizer_git\.git
```

**Declaración honesta:** no moví, no borré y no comiteé nada en `C:/Users/carch/Nextcloud/Scripts/woptimizer`. Todo se hizo en cuatro copias de `%TEMP%` con `GIT_DIR` desechables. **No toqué el repo real en ningún momento, ni siquiera para revertir: no hizo falta revertir nada porque nunca escribí en él.**

Las cuatro cámaras quedaron **restauradas y en verde** (cada mutación se revirtió con `git checkout -- .` sobre su propio `GIT_DIR` desechable, y se purgó `__pycache__` entre mutaciones).

---

## 7. LO QUE ESTO LE PIDE AL CICLO

`AGENTS.md` es explícito: *"Sin ese `PASS`, el ciclo no se cierra"*. Por tanto el ciclo 51 **no puede cerrarse** hasta que `openspec-dev` aplique lo que sigue:

| # | Acción | Severidad |
|---|---|---|
| 1 | **T-8 no se cumple.** Añadir cobertura de **G1 sola** (ver §3). Sin esto, borrar la barrera roja de la puerta común es gratis | 🔴 |
| 2 | Arreglar el test #3: su predicado AST solo mira `text=` que sea `ast.Constant`, y **las casillas del acordeón usan f-strings**. Por eso U1 pasa con 118 líneas gateadas. Comprobar `construye_checkbox` (o el rango del gate), no el literal del `text=` | 🟠 |
| 3 | Quitar la sobrescritura de `_patrones_de_categoria` en `_ServicioDeArranque` (#4 y #6 y #7 la hacen), o añadir un test que use la **DB real**. Es lo que tapa A5 | 🔴 |
| 4 | Congelar que `_pack_evaluable` **no** escribe en el pack original (S7). Su docstring ya lo promete; nadie lo comprueba | 🟠 |
| 5 | Corregir las **cuatro** afirmaciones documentales falsas del §4 (dos cifras de `killed` contradictorias entre `architecture.md` y `testing-guide.md`, y la predicción del test #5) | 🟠 |
| 6 | Anotar en `STATUS.md` que el `.exe` **sí** está regenerado (§5), para que nadie lo dé por pendiente | 🟡 |

**Lo que este ciclo hizo bien y conviene decirlo:** las tres mutaciones de `tasks.md` que el plan temía están medidas; dos de las tres mueren **por la aserción exacta que dicen comprobar**; las cuatro migraciones de invariantes **no aflojan nada** (las cuatro Gonmutadas y las cuatro mueren); y el fallo más caro —código escrito y no usado— está **cubierto** por V7.

---

# 8. RONDA 2 - `openspec-dev` responde al FAIL (2026-10-03)

**Motivo:** el veredicto de este informe fue **FAIL** con **dos supervivientes rojos** en la zona
anti-brick (S1 y A5) y dos naranjas (S7 y U1). Por el protocolo del bucle, un superviviente rojo en
seguridad **no se documenta y se sigue: se arregla**. Eso es lo que hace esta ronda.

**Metodo de verificacion:** camara propia en `%TEMP%` (`shutil.copytree` con
`ignore_patterns(".git")`, cero entradas `.git` dentro), un mutante por vez, **`__pycache__` purgado
entre mutaciones**, y la **suite COMPLETA** en cada estado (no solo el test afectado), para saber si
el mutante moria en otro sitio sin querer. El arbol del proyecto **no se ha tocado**: los mutantes
se aplicaron y revirtieron solo dentro de la camara. Suite: **120 -> 123 tests**.

## 8.1 Los cuatro fixes

Ninguno era un fallo de **codigo**: el codigo de produccion estaba correcto en los cuatro casos. Lo
que faltaba era **cobertura**, que es justo lo que significa un verde sin test.

| Mutante | Que se rompia | El fix | Test |
|---|---|---|---|
| **S1** ROJO | La barrera de lista (G1) se podia borrar **sola** y la suite seguia verde | Snapshot y DB **en discrepancia** (snapshot verde, DB roja): G5 no lo frena, asi que solo G1 puede | **#16** nuevo |
| **A5** ROJO | Sin el `.exe` de los patrones, "arrancar por categoria" no arranca **nada**, y el doble del arnes **tapaba** la linea | Nombres pedidos a la DB **de verdad** (`_load_local_db`), sin sobreescribir `_patrones_de_categoria`; afirma el **criterio** (que arranque) | **#18** nuevo |
| **S7** NARANJA | El filtro escribia en el pack **original**: el `Pack` en memoria perdia la seleccion y `update_pack` la persistia | El pack conserva **las dos** listas tras `execute_pack` **y** tras `cuenta_a_apagar` | **#17** nuevo |
| **U1** NARANJA | El gate `if pack.is_gaming:` volvia a envolver el acordeon (117 lineas) y **el test que lo vigilaba era ciego** | El predicado AST miraba `text=` con valor `ast.Constant`, pero las casillas pasan `text=cat` (un `ast.Name`) y el boton `text=_texto_acordeon(...)` (un `ast.Call` con f-string). Ahora mira la **CONSTRUCCION**, no el texto | **#3** arreglado |

**Cero cambios en `src/`.** Un fix que hubiera tocado el codigo de producion aqui habria sido
cambiar el diseño sin necesidad: el codigo ya era correcto en los cuatro casos.

## 8.2 Mutante -> veredicto -> quien muere y por que asercion

| Id | Ronda 1 | Ronda 2 | Quien muere, y por la asercion |
|---|---|---|---|
| **S1** | SOBREVIVIA | **MUERE** | Solo **#16** (`test_barrera_roja_sola_con_el_snapshot_y_la_db_en_discrepancia`), por `assert nombres == ["onedrive.exe"]`: `AssertionError: solo el verde marcado debe llegar a kill_processes. Llego ['svchost.exe', 'onedrive.exe']` - o sea, **el ladrillo del ciclo #14, en la lista capturada** |
| **A5** | SOBREVIVIA | **MUERE** | Solo **#18** (`test_arranque_por_categoria_toma_los_nombres_de_la_db_real`), por `assert nombres == [...]`: `AssertionError: los candidatos de una categoria tienen que ser Nombres con extension, porque _resolver_app rechaza los patrones pelados: salieron ['woptimizer_t063_db', 'woptimizer_t063_otro.com']` |
| **S7** | SOBREVIVIA | **MUERE** | Solo **#17** (`test_el_filtro_de_la_puerta_no_escribe_en_el_pack_original`), por `assert pack.target_categories == objetivos`: `AssertionError: el filtro de la barrera escribio en el pack del usuario: target_categories quedo en ['\U0001f7e2 Sincronizacion'] cuando se marco ['\U0001f534 Sistema de Windows', '\U0001f7e2 Sincronizacion']` |
| **U1** | SOBREVIVIA | **MUERE** | Solo **#3** (`test_acordeon_se_renderiza_en_pack_no_gaming_con_espejo_deshabilitado`), por `assert construccion is None`: `AssertionError: hay un 'if pack.is_gaming' que CONSTRUYE el acordeon (CTkCheckBox): L346. El gate se elimino de la seccion de categorias, no de todo el fichero; devolverlo dejaria un pack normal sin donde elegir categorias, con un servicio que se las pregunta igual` |

Cada mutante muere en **un** test, el que dice comprobar su cosa, y **por la asercion de ese test**
(nunca por `ImportError`, sintaxis o traceback ajeno). Los cuatro se revirtieron y sus tests
volvieron a pasar; con el arbol control la suite da `ALL TESTS PASSED`.

## 8.3 Por que S1 no lo cazaba NINGUN test (el detalle que hace el fix)

El #5 mete `svchost` con la categoria **roja en el snapshot**, asi que la barrera G5 lo descarta por su
cuenta y **G1 es redundante en ese escenario**: quitarla no cambia lo que ocurre. Eso es cobertura
*aparente*, que es peor que no tenerla, porque el test se llama "la barrera roja sigue dentro de la
puerta comun" y **parece** cubrir justo eso.

Lo que si lo caza tiene que poner el snapshot y la DB **en desacuerdo**: el snapshot dice **verde**
(G5 no lo frena) y la DB dice **roja** (que es lo que decide `should_kill_for_gaming`, porque
recalcula con `_categorize`). Esa discrepancia no es un invento del test: `load_db_async` corre en un
hilo y al aterrizar hace `self._db_map = db_map` y `self._meta_cache.clear()`
(`process_service.py:365-366`). El snapshot ya se habia construido. La ventana es estrecha, pero es
la misma que justifica que la barrera viva **dentro** de la puerta.

## 8.4 Correccion documental (el §4, punto por punto)

| Documento | Que decia | Que dice ahora |
|---|---|---|
| `docs/ai/architecture.md` §11.1 | `killed == 0` | El discriminante real es la **lista capturada** y `skipped`; se dice que el doble devuelve **siempre** `(2, 0, 0, 12.5)`. Ademas: ese test **no** caza G1 sola (ver 8.3) |
| `docs/ai/testing-guide.md` fila 109 | `killed == 1` (el verde) | Igual, con nota de que las dos cifras estaban **contradictorias entre si** y ninguna la podia dar el doble |
| `docs/ai/testing-guide.md` fila 109 | "Si la barrera se queda pegada a `execute_gaming_pack`, **todos** los tests siguen verdes y **solo este** cae" | **Se invierte**: ese test **no** caza G1 sola; lo que la caza es caer G1 **y** G5, o el #16 |
| `docs/ai/testing-guide.md` fila 107 | El predicado AST "mira los literales" | Se documenta que era **ciego** (f-strings y `ast.Name`) y por que ahora mira la construccion |
| `docs/ai/testing-guide.md` fila 108 | (sin mention del doble) | Se documenta que el doble **tapaba** `_patrones_de_categoria`, y que la fila 123 lo tapa con la DB real |
| `docs/ai/testing-guide.md` fila 109 | `target_categories=[ROJO]` | `[ROJO, verde]`: el test lleva las dos, y la lista incompleta hacia que la categoria "marcada" no fuera la unica |
| `docs/ai/data-models.md` §1.1 | (sin contrato de la extension) | Anadido: `_patrones_de_categoria` anade `.exe` porque `_resolver_app` exige `.exe`/`.com`; **sin eso, arrancar por categoria no arranca nada** |
| `docs/ai/architecture.md` §11.1 | "sobre una **copia**, nunca sobre el original" (solo docstring) | Ahora lo **congela un test**: el pack conserva las dos listas tras las dos puertas |
| `STATUS.md` | El `.exe` "esta desfasado" (§5 lo desmiente) | Anotado que el `.exe` **si** contenia el codigo del ciclo (6/6 huellas dentro, 0/2 del previo) |

Extra: la tabla de `docs/ai/testing-guide.md` tenia el **numero 105 duplicado** y **sin fila 120**
(la del test de TASK-062 estaba fuera de sitio). Renumerada: 121-123 son los tres tests nuevos.

## 8.5 Lo que NO se toco, y por que

- **`Z1`**: el informe lo declara equivalente; no es un fallo y no se re-midio.
- **Los cuatro invariantes migrados** (centinela, guard de capas, `PERMITIDOS`, `llamadas_cierre`): sus
  sondas (`A4`, `U3`, `V8`, `V7`) siguen vivos y **ninguna migracion aflojo su garantia**.
- **`dist/woptimizer.exe`**: el §5 ya lo deja limpio (6/6 dentro, 0/2 del previo). No es deuda.
- **`CHANGELOG.md`**, **`.taskmaster/CHANGELOG.md`** y **`rd_journal.json`**: son del orquestador.

## 8.6 Verificacion

| Comprobacion | Resultado |
|---|---|
| `python verify_ui_syntax.py` | 9/9 modulos compilan |
| `python run_tests.py` | `ALL TESTS PASSED` - **123 tests** (antes 120) |
| `python validate_docs.py` | **119 OK / 0 FAIL** |
| S1, S7, A5, U1 reintroducidos uno a uno, suite completa | los cuatro **mueren**, cada uno por la asercion de la tabla 8.2 |
| Los cuatro revertidos | vuelven a pasar; el control da `ALL TESTS PASSED` |

## 8.7 Que pide la ronda 3

Los cuatro supervivientes de la ronda 1 estan **cerrados y medidos contra el mutante**. Lo que queda
para que el ciclo pueda cerrarse es una **re-auditoria** de esta ronda con los mismos 22 mutantes
(sin los cuatro arreglados, que ahora deben morir) mas, si el auditor quiere, sondas nuevas sobre los
tres tests que se han anadido: **no** cierres el fix con un test que afirme "se llamo" en vez de contenido.

---

# 9. RONDA 3 - `mutation-auditor` re-audita `d318fef` (2026-10-03)

**Commit auditado:** `d318fef` - "fix(categorias): cerrar los 4 supervivientes del mutation-auditor".
**Metodo:** 15 mutantes de suite completa (83 s cada una) + 4 sondas in-process, en **dos** camaras de
`%TEMP%`, con `GIT_DIR` desechables y la prueba de aislamiento hecha ANTES de la primera mutacion.
`PYTHONDONTWRITEBYTECODE=1` en cada corrida, y restauracion por fichero desde un `pristine`: el contador de
`__pycache__` purgado sale **0** en las 17 corridas, o sea que no se pudo medir bytecode viejo.
**Nada reparado.** El arbol del proyecto no se ha tocado (§9.7).

## 9.0 VEREDICTO

# FAIL

**1 superviviente: `U1_AND`.** Los cuatro de la ronda 1 **mueren de verdad**, por la asercion de su
propio test. Pero el arreglo del #3 abrio un agujero nuevo, y es el mismo fallo de la misma clase:
**el predicado del test sigue siendo ciego, solo que ahora a otra forma de gate**.

| Severidad | Id | Que se rompe si el codigo se rompe asi |
|---|---|---|
| 🟠 **ALTA** | **U1_AND** | El acordeon vuelve a desaparecer, escrito como `if pack.is_gaming and pack.default_action == 'kill':` sobre sus 117 lineas. **123/123 en verde.** Y es *peor* que el U1 de la ronda 1: tambien se lo esconde **al propio pack Gaming** |

| Mutante | Ronda 1 | Ronda 3 |
|---|---|---|
| S1 | SOBREVIVIA (🔴) | ✅ **MUERE** |
| S7 | SOBREVIVIA (🟠) | ✅ **MUERE** |
| A5 | SOBREVIVIA (🔴) | ✅ **MUERE** |
| U1 | SOBREVIVIA (🟠) | ✅ **MUERE** |
| U1_AND | (no existia) | 🔴 **SOBREVIVE** |

## 9.1 AISLAMIENTO (medido antes de mutar nada)

| Camara | Entradas `.git` dentro | `git rev-parse --git-dir` con `GIT_DIR` desechable |
|---|---|---|
| `wopt_mut51_r3_054405504` | `[]` | `C:\...\Temp\wopt_mut51_r3_git_054405504\.git` (la suya) |
| `wopt_mut51_r3b_054918432` | `[]` | `C:\...\Temp\wopt_mut51_r3b_git2\.git` (la suya) |

**Trampa del gitlink confirmada otra vez:** el `.git` del repo es un FICHERO de 57 bytes, asi que
`ignore_patterns(".git")` (que cubre ficheros y directorios) es lo unico que funciona; `robocopy /XD`
no habria servido. **Ademas, dentro de las camaras no se invoco git para nada**: la restauracion es
`copyfile` desde `pristine`, asi que no hay `GIT_DIR` que pueda descubrir nada.

## 9.2 Los cuatro de la ronda 1, contra `d318fef`

Los cuatro mueren por la **asercion del test que dice comprobar su cosa**. Ninguno por `ImportError`,
`IndentationError` ni sintaxis rota (comprobado: la primera excepcion de cada corrida es la del test).

| Id | Mutacion | Veredicto | Motivo literal |
|---|---|---|---|
| **S1** | quitar el filtro `get_safety_badge(c)["tier"] != "danger"` de `target_categories` | ✅ **MUERE** | Solo **#16**. `AssertionError: solo el verde marcado debe llegar a kill_processes. Llego ['svchost.exe', 'onedrive.exe']` |
| **S7** | `_pack_evaluable` escribe en `pack` en vez de en `model_copy` | ✅ **MUERE** | Solo **#17**. `AssertionError: el filtro de la barrera escribio en el pack del usuario: target_categories quedo en ['\U0001f7e2 Sincronizacion'] cuando se marco ['\U0001f534 Sistema de Windows', '\U0001f7e2 Sincronizacion']` |
| **A5** | `_patrones_de_categoria`: `f"{patron}.exe"` → `patron` | ✅ **MUERE** | Solo **#18**. `AssertionError: los candidatos de una categoria tienen que ser Nombres con extension, porque _resolver_app rechaza los patrones pelados: salieron ['woptimizer_t063_db', 'woptimizer_t063_otro.com']` |
| **U1** | `if pack.is_gaming:` vuelve a envolver el acordeon (117 lineas) | ✅ **MUERE** | Solo **#3**. `AssertionError: hay un 'if pack.is_gaming' que CONSTRUYE el acordeon (CTkCheckBox): L346. El gate se elimino de la seccion de categorias, no de todo el fichero; devolverlo dejaria un pack normal sin donde elegir categorias, con un servicio que se las pregunta igual` |

Los cuatro literales coinciden **carácter a carácter** con los que declara `openspec-dev` en §8.2.

### Las declaraciones del dev, comprobadas una a una (no creidas)

| Afirmacion del dev | Medido | |
|---|---|---|
| **"CERO cambios en `src/`"** | `git show --name-only d318fef` **no lista ningun fichero bajo `src/`**. Los 9 ficheros tocados son `run_tests.py`, 3 de `docs/ai/`, `AGENTS.md`, `README.md`, `STATUS.md`, `tasks.json` y este informe | ✅ **CIERTO** |
| "S1 muere con `Llego ['svchost.exe', 'onedrive.exe']`" | literal identico | ✅ |
| "S7 muere con `target_categories quedo en [...]`" | literal identico | ✅ |
| "A5 muere con `salieron [...]`" | literal identico | ✅ |
| "U1 muere con `hay un if pack.is_gaming que CONSTRUYE el acordeon (CTkCheckBox): L346`" | literal identico | ✅ |
| "123 tests (95 backend + 28 headless)" | derivado con `ast`: 123 llamadas `test_*`, 95 antes del marcador de la linea 15276 y 28 despues | ✅ |
| "`run_tests.py` -> ALL TESTS PASSED" | control medido dos veces (antes y despues del lote) | ✅ |
| "`verify_ui_syntax.py` -> EXITO" | 9/9 modulos | ✅ |
| "`validate_docs.py` -> 119 OK / 0 FAIL" | **119 OK / 0 FAIL** con el `GIT_DIR` real. Con un `GIT_DIR` desechable sale **119 OK / 1 FAIL** ("historial de commits: 0 subjects leidos"), y ese FAIL es artefacto del sandbox, no del repo | ✅ con salvedad declarada |
| "encontro 6 afirmaciones documentales falsas" | encontro mas (§9.6): **3 afirmaciones siguen siendo falsas**, y dos de ellas las introduce este mismo commit | ⚠️ |

## 9.3 Sondas nuevas sobre los tests nuevos

Un fix cerrado con un test que solo comprueba lo que ya era verdad es el fallo clasico de este repo.
Seis sondas, cada una por una via distinta a la que midio el dev.

| Id | Sonda | Veredicto | Motivo literal |
|---|---|---|---|
| **S1_INV** | G1 **invertido**: `!= "danger"` → `== "danger"` | ✅ MUERE | Preexistente **#1**. `AssertionError: Solo deben llegar onedrive (categoria objetivo) y chrome (app explicita). Llegaron: ['chrome.exe']` |
| **S7_MITAD** | el filtro escribe en el original **solo** en `start_categories` (la mitad asimetrica) | ✅ MUERE | **#17**, su **segunda** asercion. `AssertionError: ... start_categories quedo en ['\U0001f7e1 Chat y Comunicacion'] cuando se marco [...]` |
| **A5_INV** | la guarda de extension **invertida** (`if not splitext(...)`) - via distinta a la del dev | ✅ MUERE | **#18**. `... salieron ['woptimizer_t063_db', 'woptimizer_t063_otro.com.exe']` |
| **A5_DUP** | se **duplica** la extension (`.com` → `.com.exe`) | ✅ MUERE | **#18**. `... salieron ['woptimizer_t063_db.exe.exe', 'woptimizer_t063_otro.com.exe']` |
| **T16_SIN_DISC** | **muta el propio #16**: se le quita la discrepancia (el snapshot lleva `svchost` **rojo**, igual que la DB) + S1 | 🟡 **equivalente** | `ALL TESTS PASSED`. **No es un fallo**: sin discrepancia, G5 frena a `svchost` igual que G1, asi que el mutante no cambia nada en ese escenario. Ver la advertencia de §9.5 |
| **U1_AND** | el gate vuelve, pero **compuesto** | 🔴 **SOBREVIVE** | `ALL TESTS PASSED` (123/123) |

## 9.4 U1_AND: el agujero que abre el arreglo del #3

`run_tests.py:14215-14218` - el predicado del #3:

```python
def _es_gate_de_gaming(nodo):
    t = nodo.test if isinstance(nodo, ast.If) else nodo
    return (isinstance(t, ast.Attribute) and t.attr == "is_gaming"
            and isinstance(t.value, ast.Name) and t.value.id == "pack")
```

`t` tiene que ser **exactamente** `pack.is_gaming`. Con un `and` (o un `or`, o un `not`) el test del
`if` pasa a ser un `ast.BoolOp` y **el gate entero desaparece del analisis**. El `assert gates` que
añadio el dev no lo salva: los gates legitimos (badge, boton de restaurar, texto) siguen ahi.

La forma `if pack.is_gaming and pack.default_action == "kill":` es la mas **natural** que un
desarrollador escribiria para reintroducir el gate ("solo los packs que apagan muestran esto"), y es
exactamente el motivo por el que el acordeon se gateo en su dia.

**Probado que NO es equivalente** (evaluando la condicion del gate con `ast`, sin abrir ventana):

| | `is_gaming=False, default_action=start` | `is_gaming=False, default_action=kill` | `is_gaming=True, default_action=kill` | `is_gaming=True, default_action=start` |
|---|---|---|---|---|
| **Control** | se renderiza | se renderiza | se renderiza | se renderiza |
| **U1** (gate simple) | **NO** | **NO** | se renderiza | se renderiza |
| **U1_AND** (compuesto) | **NO** | **NO** | se renderiza | **NO** |

Es **peor que U1**: `default_action` es `Literal["start", "kill"] = "start"` (`models.py:83`), o sea
que **un pack recien creado nace en "start"**, y el pack Gaming tambien (`DEFAULT_GAMING_PACK` nace en
"kill" pero el desplegable de TASK-062 deja cambiarlo, y `dashboard_view.py:457` documenta el caso
"gaming con `default_action='start'`" como real). O sea: el gate compuesto **tambien le esconde el
acordeon al pack de Gaming Mode**, y mientras tanto `execute_pack` y `start_pack_categories` siguen
preguntando sus listas. Es el mismo fallo, con un agujero mas.

**Arreglo que necesita (no aplicado):** que `_es_gate_de_gaming` mire si `is_gaming` aparece **en
alguna parte** del test (`ast.walk` del test buscando `pack.is_gaming`), no solo si el test **es**
`pack.is_gaming`. Un gate que solo mire `is_gaming` y ademas no construya el acordeon es el
invariante; como esta, el invariante se puede violar con un `and`.

## 9.5 Lo que el #16 SÍ aguanta (la pregunta del encargo: "si la discrepancia no se puede construir de otra forma")

Se podia, y se construyo **por la via real**: no con el `ProcessInfo(...)` que escribe el test, sino
recargando la DB con `spy._load_local_db()` **despues** de construir el snapshot, que es exactamente lo
que hace el hilo de `load_db_async` al aterrizar (`process_service.py:365-367`: `self._db_map = db_map`
+ `self._meta_cache.clear()`).

| | `_categorize("svchost.exe")` antes | despues de recargar | lo que llega a `kill_processes` |
|---|---|---|---|
| **Control** | 🟢 Sincronizacion | 🔴 Sistema de Windows | `['onedrive.exe']` - **barrera en pie** |
| **S1** | 🟢 Sincronizacion | 🔴 Sistema de Windows | **`['svchost.exe', 'onedrive.exe']`** - **anti-brick abierto** |

**Conclusion: el escenario del #16 no es un artefacto de como el test construye la discrepancia.** El
invariante (G1 frena cuando snapshot y DB discrepan) es real, alcanzable por codigo de produccion, y lo
caza. Eso es lo que la ronda 1 pidio y esta entregado.

**Pero con una advertencia (no es un fallo, es una fragilidad):** `T16_SIN_DISC` muestra que **todo** el
poder discriminante del #16 esta en que los dos fuentes discrepan. El test comprueba sus precondiciones
(`is_system_protected("svchost") is False`, `get_safety_badge(_CAT_SYNC) != danger`,
`spy._categorize("svchost.exe") == ROJO`) pero **no comprueba que el snapshot y la DB discrepan entre
si**. Si alguien "limpia" el test y los deja de acuerdo, el #16 se vuelve decorativo **y sigue en verde
con S1 puesto**: volveria a ser cobertura aparente. **Arreglo de una linea, recomendado:**
`assert spy._categorize("svchost.exe") != spy.snapshot[0].category` al lado de las otras precondiciones.

## 9.6 AUDITORIA DOCUMENTAL (contra el codigo y contra el recuento derivado con `ast`, no contra el dev)

### Lo que el dev **acerto** (todo verificado)

| Documento | Afirmacion | Medido |
|---|---|---|
| `docs/ai/testing-guide.md` | **renumeracion**: el 105 duplicado y el 120 ausente | ✅ **CIERTO y completo**: 123 filas numeradas, **0 duplicados, 0 huecos**, maximo 123, y `validate_docs.py` confirma "123 filas de test, una por test definido" |
| `architecture.md` §11.1 y `testing-guide.md` fila 109 | el doble `_ProcessServiceSpy.kill_processes` devuelve **siempre** `(2, 0, 0, 12.5)`, asi que `killed` no afirma nada | ✅ CIERTO (`run_tests.py:685`) |
| `testing-guide.md` fila 109 | `target_categories=[ROJO, verde]` y `skipped == 1` | ✅ CIERTO contra `run_tests.py:14367-14395` |
| `testing-guide.md` fila 107 | el predicado ahora mira la **construccion** y exige que exista al menos un gate | ✅ CIERTO (`run_tests.py:14237-14266`) |
| `testing-guide.md` fila 109 | "el test 109 NO caza G1 sola; lo que la caza es caer G1 **y** G5, o la fila 121" | ✅ CIERTO: medido en la ronda 1 (S1S4 muere en #5) y re-medido aqui |
| `data-models.md` §1.1 | `_patrones_de_categoria` anade `.exe` porque `_resolver_app` exige `.exe`/`.com` | ✅ CIERTO: sonda con la DB real, `_resolver_app('wopt_r3_real')` → `None` con el log *"extension fuera de la lista blanca .exe/.com"* |
| `STATUS.md` | el `.exe` **si** contenia el codigo del ciclo | ✅ coherente con §5 de la ronda 1 (6/6 huellas dentro, 0/2 del previo) |

### Lo que **sigue siendo falso** (3 afirmaciones, y **dos las introduce `d318fef`**)

| # | Fichero y linea | Afirmacion | Medido |
|---|---|---|---|
| **D1** 🟠 | **`docs/ai/testing-guide.md:170`** | *"el reparto derivado por el check 7 es **95 backend + 25 headless**"* | ❌ **FALSO: son 28** (`ast`: 123 = 95 + 28). Y se contradice **dentro del mismo bloque**, que ahora dice *"Los dieciocho van del lado headless"*. Lo dejo `validate_docs.py` en verde porque solo vigila el reparto declarado en `STATUS.md`, no esta prosa |
| **D2** 🟠 | **`STATUS.md:9`** | *"El salto 10 → 25 headless son los dieciocho tests de TASK-063"* | ❌ **FALSO y contradictorio consigo mismo**: 10 + 18 = **28**, no 25. La primera frase de esa misma linea (123 = 95 + 28) si es cierta |
| **D3** 🟠 | **`run_tests.py:14346-14352`** (docstring del test **#5**) | *"si la barrera se quedase pegada a `execute_gaming_pack` ... **solo este caeria**"* | ❌ **FALSO, medido**: ese fue el mutante S1Z1 de la ronda 1 y dejo 120/120 en verde. El dev lo corrigio en `testing-guide.md` pero **no en el docstring del propio test**, que es donde el que lo depura lo encuentra |
| **D4** 🟡 | `testing-guide.md` fila 123 y `run_tests.py:15033-15034` | *"`_ServicioDeArranque` **sobreescribe** `_patrones_de_categoria`"* | ❌ **atribucion falsa**: la clase **no** lo sobreescribe - su propio docstring dice "Se sobreescriben **DOS** cosas" (`_resolver_app` y `_lanzar`) -. Lo sobrescriben **tres tests**, por instancia: `run_tests.py:14318` (`test_start_categories_arranca_y_cuenta_honestamente`), `:14414` (`test_categoria_roja_en_start_categories_no_arranca`) y `:14441` (`test_conflicto_misma_categoria_gana_kill`), medido con `ast`. Las filas citadas (108, 110 y 111) si son las correctas; el actor no |

**D1 y D2 son el mismo error de renumeracion propagado**: el dev cambio el total a 123 y el reparto de
`STATUS.md` a 95+28, pero dejo sueltas las dos frases que siguen diciendo 25. Un `grep "25 headless"`
los encuentra los dos.

### El resto del encargo, comprobado

- **Todo el codigo del ciclo esta en uso.** Con `ast` sobre `src/`: `_pack_evaluable` (2 llamadas),
  `_seleccion` (2), `execute_pack` (4, dos en `dashboard_view`), `cuenta_a_apagar` (2),
  `start_pack_categories` (2), `categorias_disponibles` (1), `_patrones_de_categoria` (1) y
  **`execute_gaming_pack` (1, desde `ui/app.py:119`)**: el wrapper de compatibilidad sigue teniendo su
  unico llamante real, o sea que la afirmacion de `architecture.md` §11.1 es cierta. **Ninguna funcion
  testeada y no invocada.**

## 9.7 REGRESIONES: el arreglo de los cuatro no rompio nada que antes vigilaban

Los mutantes que ya morian en la ronda 1, repetidos contra `d318fef`. Todos **siguen muriendo**, cada
uno por su asercion. **Cerrar el agujero no abrio ningun otro por este lado.**

| Id | Que se quita | Veredicto | Motivo literal |
|---|---|---|---|
| **S4** | G5: la barrera sobre `p.category` del snapshot | ✅ MUERE | `AssertionError: skipped debe sumar los descartes del filtro (svchost y lsass): 1` |
| **S5** | G4: el blindaje de nombres (`is_system_protected`) | ✅ MUERE | mismo aserto que S4, con el blindaje |
| **S6** | `get_running_processes(force_refresh=True)` → `False` (G0) | ✅ MUERE | `AssertionError: G0 es obligatorio: sin force_refresh=True la cache TTL de 2 s puede dejar fuera lo que el usuario acaba de lanzar` |
| **V7** | el Gestor vuelve a `kill_pack_apps(pack.apps)` (la puerta existe pero no se usa) | ✅ MUERE | `AssertionError: el pack se cierra por la puerta comun con SUS apps, no con un atajo ni con una lista vacia (llego ['C:\Juegos\juego.exe'])` |
| **V8** | el worker llama a `restore_gaming_session()` desde el hilo | ✅ MUERE | `AssertionError: el worker toca la vista fuera de self.after(0, ...): PackManagerView.kill_pack:L638 self.gaming_service.restore_gaming_session(...) desde el hilo secundario` |
| **Z1** | barrera roja duplicada en `execute_gaming_pack` | 🟡 **equivalente** | `ALL TESTS PASSED`. **Re-medido en esta ronda** (el dev no lo toco y `src/` no cambio, pero se midio igual): el filtro de la puerta comun ya la aplica. **No es un fallo** |

Tambien se midio que el #3 **no se ha vuelto demasiado fuerte**: la sonda D enumera los gates que su
predicado ve y comprueba que los **tres legitimos los PERMITE** (badge `PRESET` en L210, boton de
restaurar en L278, texto "preparar el Gaming Mode" en L604: ninguno contiene construccion del acordeon).
No es una asercion que nada pueda violar, y no se ha vuelto "lo que construya el acordeon le sirve" en
la forma simple; **se ha vuelto ciego justo en la forma compuesta**.

## 9.8 QUE PIDE ESTA RONDA AL CICLO

| # | Accion | Severidad |
|---|---|---|
| 1 | **Cerrar `U1_AND`**: que `_es_gate_de_gaming` busque `pack.is_gaming` **dentro** del test del `if` (con `ast.walk`), no solo que el test **sea** `pack.is_gaming`. Re-verificar con `U1`, `U1_AND` y las sondas de gates legitimos | 🟠 |
| 2 | **Congelar la premisa del #16** con una linea: `assert spy._categorize("svchost.exe") != spy.snapshot[0].category`. Sin ella, el test puede volverse decorativo sin que nada se entere (§9.5) | 🟠 |
| 3 | **D1 + D2**: corregir las dos frases que siguen diciendo "25 headless" (`testing-guide.md:170` y `STATUS.md:9`). El numero cierto, derivado con `ast`, es **95 + 28** | 🟠 |
| 4 | **D3**: corregir tambien el docstring de `run_tests.py:14346-14352`, no solo `testing-guide.md` | 🟠 |
| 5 | **D4**: la atribucion de la fila 123 es a tres tests por instancia, no a la clase `_ServicioDeArranque` | 🟡 |

## 9.9 CONTRATO: QUE SE HA TOCADO EN EL ARBOL DEL PROYECTO

Verificado desde la raiz del repositorio, **despues** de las 17 corridas:

```
git log --oneline -2      d318fef fix(categorias): cerrar los 4 supervivientes ...
                          e0f20db feat(categorias): puerta comun execute_pack ...
git status --porcelain    (vacio)
git diff --stat           (vacio)
git diff --cached --stat  (vacio)
git rev-parse --git-dir   C:\Users\carch\AppData\Local\woptimizer_git\.git
```

**Declaracion honesta:** las 17 corridas y las 4 sondas fueron **enteras** en copias de `%TEMP%`. No
escribi, no borre y no comitee nada en `C:/Users/carch/Nextcloud/Scripts/woptimizer`, ni siquiera para
revertir. Las dos camaras quedaron **restauradas y en verde**: el control final, corrido **despues** del
ultimo mutante, da `ALL TESTS PASSED` (123/123).

**Una excepcion, y hay que decirla:** al appendear esta seccion 9 al informe, el arbol deja de estar
limpio en **un unico fichero**, este mismo (`openspec/changes/.../mutation-report.md`), que es el
artefacto de este rol y lo pidio el encargo. **No se ha hecho ningun commit.** `src/`, `run_tests.py` y
los ficheros de documentacion estan **exactamente** como los dejo `d318fef`.

# 10. RONDA 4 - `mutation-auditor` re-audita `9dcd8ed` (2026-10-03)

**Commit auditado:** `9dcd8ed` - "fix(tests): cerrar U1_AND con predicado estructural y congelar la premisa
del #16 (TASK-063 ronda 3)".

**Metodo:** 27 corrida de suite completa (85-95 s cada una) + 8 sondas in-process, repartidas en **seis
camaras** de `%TEMP%` en paralelo, cada una con su `GIT_DIR` desechable, `PYTHONDONTWRITEBYTECODE=1` en
todas, `__pycache__` purgado entre mutaciones (medido: **0** en el control final) y restauracion por
`copyfile` desde un `pristine` propio. **Nada reparado.** El arbol del proyecto **no se ha tocado** (§10.9).

## 10.0 VEREDICTO

# FAIL

**6 supervivientes, todos de la MISMA clase y todos en un UNICO test** (el #3, el que el dev acaba de
arreglar). **Ninguno es de codigo de produccion: el codigo de produccion esta correcto y esta intacto**
(`git show --name-only 9dcd8ed` no lista **ningun** fichero bajo `src/`).

| Severidad | Id | Que se rompe si el codigo se rompe asi |
|---|---|---|
| 🟠 **ALTA** | **G_VAR** | `gaming = pack.is_gaming` + `if gaming:` sobre las 117 lineas del acordeon. **123/123 en verde** |
| 🟠 **ALTA** | **G_HELPER** | `if self._es_gaming(pack):` (el predicado extraido a un metodo). **123/123 en verde** |
| 🟠 **ALTA** | **G_GUARD2** | `if not pack.is_gaming: return` al principio de un metodo propio que dibuja el acordeon. **123/123 en verde** |
| 🟡 **MEDIA** | **G_ALIAS** | `p = pack` + `if p.is_gaming:`. **123/123 en verde** |
| 🟡 **MEDIA** | **G_GETATTR** | `if getattr(pack, "is_gaming", False):`. **123/123 en verde** |
| 🟡 **BAJA** | **G_PRED** | `if pack.id != "gaming":` (el mismo bug escrito con otro predicado). **123/123 en verde** |

**Y dos FALSOS POSITIVOS medidos**, que son la otra mitad del mismo defecto: el #3 **rechaza codigo
legitimo**. No es que el test sea solo ciego; es que comprueba una FORMA y no el INVARIANTE.

| Severidad | Id | Codigo 100% legitimo que el test RECHAZA |
|---|---|---|
| 🟠 **ALTA** | **D_FP1** | Un gate de gaming (el badge `PRESET` de L210) que ademas dibuja su **propia** casilla de opcion del Gaming Mode. Rechazado: *"una condicion que depende de `is_gaming` CONSTRUYE el acordeon (CTkCheckBox): L210"* - y el mensaje **miente**: dice que el gate se elimino de la seccion de categorias, que no es lo que paso |
| 🟠 **ALTA** | **D_FP2** | Un gate de gaming cuyo texto dice *"Va a **arrancar** el Gaming Mode de 'X'"*. Rechazado por la segunda asercion, que busca la palabra "arrancar" - que en esta app es una columna entera del acordeon y el nombre de `start_categories` |

### Lo que esta ronda SI ha entregado, medido

| Mutante | Ronda 1 | Ronda 3 | **Ronda 4** |
|---|---|---|---|
| **S1** (barrera roja de la puerta comun) | SOBREVIVIA (🔴) | MUERE | ✅ **MUERE** |
| **A5** (`.exe` de los patrones) | SOBREVIVIA (🔴) | MUERE | ✅ **MUERE** |
| **S7** (el filtro escribe en el original) | SOBREVIVIA (🟠) | MUERE | ✅ **MUERE** |
| **U1** (gate simple) | SOBREVIVIA (🟠) | MUERE | ✅ **MUERE** |
| **U1_AND** (gate compuesto) | (no existia) | **SOBREVIVA** (🔴) | ✅ **MUERE** |

El agujero que la ronda 3 reporto **esta cerrado**, y el arreglo es real y no cosmético: el predicado paso
de *"el test del `if` **es** `pack.is_gaming`"* (igualdad textual) a *"el test del `if` **contiene** una
lectura de `is_gaming`"* (`ast.walk`). Eso no cierra solo el `and` que se reporto: **mata cinco formas**
(U1, U1_AND, `or`, `is True`, y la seccion colocada en el `else`, porque el `walk` del `If` incluye el
`orelse`). **Las seis afirmaciones del dev se comprobaron una a una y todas son ciertas** (§10.7).

**El defecto que queda no es el que se reporto, es el de la clase del que se reporto**: un test que
reconoce N formas de gate es un test que la forma N+1 ciega, y la ronda 3 lo demostro con `and` y la
ronda 4 lo demuestra con una variable intermedia.

## 10.1 AISLAMIENTO (medido antes de mutar nada)

La trampa del gitlink, confirmada por tercera vez. `git show` del `.git` del arbol: es un **FICHERO** de
57 bytes, asi que `robocopy /XD .git` no lo excluye. Las seis camaras se hicieron con
`shutil.copytree(..., ignore=shutil.ignore_patterns(".git", "dist", "build", "__pycache__", "*.pyc"))`,
que cubre ficheros **y** directorios.

| Camara | Entradas `.git` dentro | `git rev-parse --git-dir` con `GIT_DIR` desechable |
|---|---|---|
| a | `[]` | `C:\...\Temp\wopt_r4\git_desechable.git` (la suya) |
| b, c, e, f | `[]` | (nunca se invoco git dentro de ellas) |
| prueba dedicada | `[]` | `C:\...\Temp\wopt_r4\git_desechable.git`, `aislado = True` |

`git rev-parse --git-dir` **sin** `GIT_DIR`, desde la camara, devuelve `rc=128` y salida vacia: la camara
**no puede descubrir** el repo real. Ademas, dentro de las camaras **no se invoco git para nada** (la
restauracion es `copyfile` desde `pristine`), asi que no hay ningun `GIT_DIR` que pueda derivar a otro
sitio.

## 10.2 LO QUE PIDE EL ENCARGO, PUNTO 1: `U1` y `U1_AND` con el codigo de `9dcd8ed`

Ambos mueren **por la asercion del #3**, no por `ImportError`, ni por `IndentationError`, ni por un
`NameError` ajeno (`"roto": false` en el analizador, que busca esos cuatro strings en la salida entera).

| Id | Mutacion | Veredicto | Motivo literal |
|---|---|---|---|
| **U1** | `if pack.is_gaming:` vuelve a envolver el acordeon (117 lineas) | ✅ **MUERE** | Solo **#3**. `AssertionError: una condicion que depende de 'is_gaming' CONSTRUYE el acordeon (CTkCheckBox): L346. Da igual que la condicion sea 'pack.is_gaming' a secas o 'pack.is_gaming and <algo>': el gate se elimino de la seccion de categorias, no de todo el fichero; devolverlo dejaria un pack normal sin donde elegir categorias, con un servicio que se las pregunta igual` |
| **U1_AND** | el mismo gate con `and pack.default_action == "kill"` | ✅ **MUERE** | El mismo aserto, mismo `L346`. **La declaracion del dev es cierta y el literal coincide** |

## 10.3 LO QUE PIDE EL ENCARGO, PUNTO 2: ONCE FORMAS DE GATE INVENTADAS (esta es la parte central)

### 10.3.1 Primero: **ninguna** de las doce formas es un equivalente

Un superviviente solo es "equivalente" si el comportamiento no cambia. Se midio **evaluando la condicion
de cada forma con `ast`** sobre siete packs reales (gaming/normal x kill/start x favorito x id). `SI` = el
acordeon se renderiza:

| Forma | gaming/kill | gaming/start | normal/kill | normal/start | normal+fav | gaming id=gaming | gaming id=otro | |
|---|---|---|---|---|---|---|---|---|
| **CONTROL (sin gate)** | SI | SI | SI | SI | SI | SI | SI | equivalente |
| `if pack.is_gaming:` | SI | SI | **NO** | **NO** | **NO** | SI | SI | **cambia** |
| `... and default_action == "kill"` | SI | **NO** | **NO** | **NO** | **NO** | SI | SI | **cambia** |
| `... or pack.is_favorite` | SI | SI | **NO** | **NO** | SI | SI | SI | **cambia** |
| `... is True` | SI | SI | **NO** | **NO** | **NO** | SI | SI | **cambia** |
| `if not ...: pass else: <seccion>` | **NO** | **NO** | SI | SI | SI | **NO** | **NO** | **cambia** |
| `gaming = pack.is_gaming; if gaming:` | SI | SI | **NO** | **NO** | **NO** | SI | SI | **cambia** |
| `getattr(pack, "is_gaming", False)` | SI | SI | **NO** | **NO** | **NO** | SI | SI | **cambia** |
| `p = pack; if p.is_gaming:` | SI | SI | **NO** | **NO** | **NO** | SI | SI | **cambia** |
| `self._es_gaming(pack)` | SI | SI | **NO** | **NO** | **NO** | SI | SI | **cambia** |
| `pack.id != "gaming"` | SI | SI | SI | SI | SI | **NO** | SI | **cambia** |
| `if not pack.is_gaming: return` (guard) | SI | SI | **NO** | **NO** | **NO** | SI | SI | **cambia** |

**Las doce esconden el acordeon a algun pack que hoy lo ve.** No hay ningun equivalente que "salvar" al
test: o las mata, o son un agujero de verdad.

### 10.3.2 Y ahora: cuales caza `9dcd8ed`

| Id | Forma | ¿El predicado la ve? | Veredicto de la suite | Motivo literal |
|---|---|---|---|---|
| **U1** | `if pack.is_gaming:` | si | ✅ **MUERE** | #3, `... CONSTRUYE el acordeon (CTkCheckBox): L346` |
| **U1_AND** | `and default_action == "kill"` | si | ✅ **MUERE** | #3, mismo literal |
| **G_OR** | `or pack.is_favorite` | si | ✅ **MUERE** | #3, mismo literal |
| **G_ISTRUE** | `pack.is_gaming is True` | si (es un `ast.Compare`) | ✅ **MUERE** | #3, mismo literal |
| **G_ELSE** | la seccion va en el `else` | si (el `walk` del `If` incluye el `orelse`) | ✅ **MUERE** | #3, mismo literal |
| **G_SELF** | `self.pack.is_gaming` | si (por codigo) | ⚠️ **MUTANTE INVALIDO** | `AttributeError: 'function' object has no attribute 'is_gaming'`: **`self.pack` es el metodo `pack` de Tk**, no el pack. La segunda rama de `_lee_is_gaming` (`base.attr == "pack"`) esta **escrita para una forma que no puede funcionar en esta clase**. No cuenta ni a favor ni en contra |
| **G_VAR** | `gaming = pack.is_gaming` + `if gaming:` | **NO** | 🔴 **SOBREVIVE** | `ALL TESTS PASSED` (123/123). La lectura de `is_gaming` esta en una sentencia **hermana**, no en el arbol del `if` |
| **G_ALIAS** | `p = pack` + `if p.is_gaming:` | **NO** | 🔴 **SOBREVIVE** | `ALL TESTS PASSED` (123/123). `_lee_is_gaming` exige `base.id == "pack"`, y aqui es `"p"` |
| **G_GETATTR** | `getattr(pack, "is_gaming", False)` | **NO** | 🔴 **SOBREVIVE** | `ALL TESTS PASSED` (123/123). El nombre viaja como **string**, no como `ast.Attribute` |
| **G_HELPER** | `self._es_gaming(pack)` | **NO** | 🔴 **SOBREVIVE** | `ALL TESTS PASSED` (123/123). La condicion es una `ast.Call`; el `is_gaming` vive dentro del metodo |
| **G_PRED** | `pack.id != "gaming"` | **NO** | 🔴 **SOBREVIVE** | `ALL TESTS PASSED` (123/123). Ni Mentiona `is_gaming` |
| **G_GUARD** | guard clause en un metodo extraido | **NO** | 🟡 **MUERE, pero por otra cosa** | No la caza el #3: la caza el guard de TASK-062 (`test_el_estado_que_elige_el_usuario_se_persiste_de_verdad`), con `AssertionError: El toggle de categorias automaticas debe releer el pack y persistirlo con 'update_pack'` - porque ese test hace `inspect.getsource(_PMV._render_pack_card)` y la extraccion se llevo el toggle consigo. **El motivo del fallo no es "el acordeon esta gateado"**, es "la seccion se movio de metodo" |
| **G_GUARD2** | el mismo, **mas** el guard ajeno arreglado para que acepte el metodo nuevo | **NO** | 🔴 **SOBREVIVE** | `ALL TESTS PASSED` (123/123). Verificado: cambiar `inspect.getsource(_PMV._render_pack_card)` por `inspect.getsource(_PMV)` devuelve el verde. **Es decir: la muerte del G_GUARD era un accidente, y en cuanto el test ajeno deja de estar atado al nombre del metodo, el gate pasa** |

**Por que esto no es "moverse la lista"**: la ronda 3 reporto la forma `and` porque era *la mas natural
para reintroducir el gate*. Estas seis son las **siguientes** en orden de naturalidad, y tres de ellas
(`gaming = ...`, `self._es_gaming(...)`, guard clause) son tanto o mas naturales que la del `and` que ya
se cerro. Un developer que quiere gatear el acordeon y ya ha visto el docstring del #3 - que enumera las
formas que el test SI cubre - tiene el camino abierto por las que el docstring no nombra.

## 10.4 LO QUE PIDE EL ENCARGO, PUNTO 3: MI PROPIA ENUMERACION, EN LOS DOS SENTIDOS

No se ha repetido la lista de 6 del dev. Se ha replicado el predicado del #3 sobre el fichero y se han
enumerado los gates por cuenta propia, y despues se han medido los dos sentidos.

**Sentido 1 - ¿rechaza algo que deberia permitir? (falso positivo).**

| # | Gate que el predicado ve | Condicion | Veredicto del #3 |
|---|---|---|---|
| 1 | L173 | `pack.is_gaming` (ternario del borde) | PERMITIDO |
| 2 | L174 | `pack.is_gaming` (ternario del borde) | PERMITIDO |
| 3 | L210 | `pack.is_gaming` (badge `PRESET`) | PERMITIDO |
| 4 | L278 | `pack.is_gaming` (boton de restaurar) | PERMITIDO |
| 5 | L561 | `es_pack_inerte(pack.is_gaming, ...)` (argumento) | PERMITIDO |
| 6 | L604 | `pack.is_gaming` (texto del Gaming Mode) | PERMITIDO |

**6 vistos, 6 permitidos, 0 rechazados. Y el fichero no tiene una septima lectura de `is_gaming`**: son
exactamente 6 (`ast` sobre el `Attribute`, las seis). **La afirmacion del dev es cierta, verificada de
forma independiente.**

**Pero "0 falsos positivos HOY" no es "el predicado no es demasiado fuerte".** Medido con dos sondas que
meten codigo legitimo:

| Id | Que se mete | Veredicto | Motivo literal |
|---|---|---|---|
| **D_FP1** | En el gate del badge `PRESET` (L210, legitimo de gaming), una casilla **propia** del Gaming Mode: `_opcion_gaming = ctk.CTkCheckBox(left_box, text="autoarranque", ...)` | 🔴 **RECHAZADO** | `AssertionError: una condicion que depende de 'is_gaming' CONSTRUYE el acordeon (CTkCheckBox): L210. ... el gate se elimino de la seccion de categorias ...` **El mensaje afirma algo que no paso.** El test no distingue "el acordeon" de "cualquier checkbox" |
| **D_FP2** | En el gate de L604 (legitimo), un texto de aviso que dice *"Va a **arrancar** el Gaming Mode de 'X'."* | 🔴 **RECHAZADO** | `AssertionError: una condicion que depende de 'is_gaming' tiene texto del acordeon dentro: L604. Los gates legitimos (badge PRESET, boton restaurar y el texto 'preparar el Gaming Mode') no lo llevan` |

**Consecuencia practica, y es el argumento de peso para la ronda 5:** el predicado es a la vez **ciego y
demasiado estricto**. Eso no es un defecto de cobertura: es un defecto de **enfoque**. `_CONSTRUCCIONES_
DEL_ACORDEON = ("CTkCheckBox", "_texto_acordeon", "create_command")` identifica el acordeon por el
**nombre del constructor**, y la segunda asercion lo identifica por la **palabra "arrancar"**. Un
developer que quiera meter una opcion de solo-Gaming se encuentra con el test en contra y sin forma de
escribir la excepcion; la salida natural es **relajar el predicado** (y con el, abrir de nuevo el
agujero), no abrir un segundo predicado mas fuerte.

**La forma de arreglarlo que si aguanta (no aplicada; es de `openspec-dev`):** dejar de preguntar *"¿la
condicion menciona `is_gaming`?"* y preguntar por el **espacio negativo** del invariante, que es
"el acordeon se dibuja en linea recta, sin condicion ninguna por delante":

1. Para cada construccion del acordeon, recorrer sus **antecedentes** dentro de su funcion y afirmar que
   **ninguno** es un `ast.If` / `ast.IfExp` / `ast.While` / `ast.Try` - sin mirar la condicion. Eso mata
   de raiz `U1`, `U1_AND`, `G_OR`, `G_ISTRUE`, `G_VAR`, `G_ALIAS`, `G_GETATTR`, `G_HELPER` y `G_PRED`,
   porque en las nueve la construccion esta **dentro** de un `If`, sea cual sea su condicion.
2. Afirmar ademas que la **funcion que lo dibuja no tiene un `return` temprano** condicionado por
   `is_gaming`, que es la unica forma de gate que no es un ancestro: el `G_GUARD`.
3. Y **borrar la asercion de la palabra "arrancar"**, que es la que se come el codigo legitimo (D_FP2).

Con (1) y (2) el invariante deja de ser una lista de formas y pasa a ser una propiedad, que es lo unico
que un test de forma no puede cazar.

## 10.5 LO QUE PIDE EL ENCARGO, PUNTO 4: LA PREMISA DEL #16

Las dos mitades, medidas por separado. **La precondicion nueva NO se ha comido el poder discriminante.**

| Escenario | Veredicto | Motivo literal |
|---|---|---|
| **S1 solo**, #16 intacto | ✅ **MUERE por la asercion principal** | `AssertionError: solo el verde marcado debe llegar a kill_processes. Llego ['svchost.exe', 'onedrive.exe']: 'svchost.exe' entro porque la categoria ROJA marcada no se filtro de 'target_categories', y la DB la reclasifico a rojo DESPUES de que el snapshot la trajera verde. Sin esa barrera, un proceso del sistema acaba en la via de kill porque las dos fuentes no coinciden durante un instante` |
| **Premisa rota** (el snapshot lleva `svchost` ROJO, igual que la DB) **+ S1** | ✅ **MUERE por la precondicion** | `AssertionError: preCONDICION ROTA: este test solo mide la barrera de categoria si el snapshot y la DB DISCREPAN. Aqui coinciden en '\U0001f534 Sistema de Windows', y entonces el proceso lo descarta G5 aunque G1 no exista: sin G1 este test pasaria igual, es decir, no mediria nada` |

Las dos salidas coinciden **caracter a caracter** con las que declara el dev, incluido el `\U0001f534` del
mensaje. Un test que muriera siempre por la precondicion y nunca por la asercion principal seria tan
decorativo como uno sin precondicion: **medido, y no es el caso**. Con S1 puesto y la precondicion bien,
la asercion que salta es `nombres == ["onedrive.exe"]`, que es la que el #16 dice medir.

## 10.6 LO QUE PIDE EL ENCARGO, PUNTO 5: REGRESIONES

Los nueve mutantes de la lista del encargo, contra `9dcd8ed`. **Ninguna regresion.**

| Id | Que se rompe | Veredicto | Motivo literal |
|---|---|---|---|
| **S1** | se quita el filtro `get_safety_badge(c)["tier"] != "danger"` de `target_categories` | ✅ **MUERE** | Solo **#16**. `solo el verde marcado debe llegar a kill_processes. Llego ['svchost.exe', 'onedrive.exe']` |
| **S7** | `_pack_evaluable` escribe en el pack original | ✅ **MUERE** | Solo **#17**. `el filtro de la barrera escribio en el pack del usuario: target_categories quedo en ['\U0001f7e2 Sincronizacion'] ...` |
| **A5** | `_patrones_de_categoria` quita el `.exe` | ✅ **MUERE** | Solo **#18**. `los candidatos de una categoria tienen que ser Nombres con extension ...: salieron ['woptimizer_t063_db', 'woptimizer_t063_otro.com']` |
| **U1** | vuelve el gate simple | ✅ **MUERE** | #3, `... CONSTRUYE el acordeon (CTkCheckBox): L346` |
| **S4** | se quita G5 (barrera sobre `p.category`) | ✅ **MUERE** | `skipped debe sumar los descartes del filtro (svchost y lsass): 1` |
| **S5** | se quita G4 (blindaje de nombres) | ✅ **MUERE** | mismo aserto que S4 |
| **S6** | `force_refresh=True` → `False` | ✅ **MUERE** | `G0 es obligatorio: sin force_refresh=True la cache TTL de 2 s puede dejar fuera lo que el usuario acaba de lanzar` |
| **V7** | el Gestor vuelve a `kill_pack_apps(pack.apps)` | ✅ **MUERE** | `el pack se cierra por la puerta comun con SUS apps, no con un atajo ni con una lista vacia (llego ['C:\Juegos\juego.exe'])` |
| **V8** | el worker llama a `restore_gaming_session()` desde el hilo | ✅ **MUERE** | `el worker toca la vista fuera de self.after(0, ...): PackManagerView.kill_pack self.gaming_service.restore_gaming_session(...) desde el hilo secundario` |
| **Z1** | barrera roja duplicada en `execute_gaming_pack` | 🟡 **EQUIVALENTE** | `ALL TESTS PASSED` (123/123). **Tercera vez equivalente.** El filtro de la puerta comun ya la aplica |

> **Z1: por que no salio MUERTO cuando se declaro equivalente en las rondas 1 y 3.** No salio MUERTO: la
> primera medicion de esta ronda si dio `MUERE`, y era **un mutante mio mal hecho** - use
> `get_safety_badge(_CAT_ROJO)`, y `_CAT_ROJO` es una constante de `run_tests.py`, no del modulo de
> produccion, asi que el mutante murio de `NameError` a los 84 s. **No es evidencia de nada** y queda
> declarado como error de sonda, no como hallazgo. Rehecho con la categoria literal, el resultado es
> `ALL TESTS PASSED`: **equivalente, igual que en las rondas 1 y 3.** Lo que no cambio entre rondas es el
> motivo por el que se declaro equivalente: la barrera de `execute_gaming_pack` es redundante porque la
> puerta comun filtra antes. Y `9dcd8ed` no toca `src/`, asi que no **podria** haber cambiado.

## 10.7 LAS DECLARACIONES DEL DEV, COMPROBADAS UNA A UNA (no creidas)

| Afirmacion del dev | Medido | |
|---|---|---|
| "`U1_AND` y `U1` mueren por la asercion del #3" | literales identicos, `roto: false` | ✅ |
| "El mensaje dice 'una condicion que depende de is_gaming CONSTRUYE el acordeon (CTkCheckBox): L336'" | el codigo produce **`L346`** (la linea del gate), que es lo correcto: el gate insertado cae en 346 | ✅ con nota |
| "6 gates que el predicado ve, los 6 permitidos, 0 rechazados" | enumeracion propia: **6 vistos, 6 permitidos, 0 rechazados**, y el fichero no tiene una septima lectura de `is_gaming` | ✅ |
| "El #16 con la premisa rota + S1 muere con `preCONDICION ROTA: ...`" | literal identico | ✅ |
| "Con S1 solo y el #16 intacto sigue muriendo en `run_tests.py:15014` por `nombres`" | literal identico (`solo el verde marcado debe llegar a kill_processes`), y la precondicion **no** se adelanta | ✅ |
| "`testing-guide.md`: 95+25 → **95+28**" | `docs/ai/testing-guide.md:170-172` dice **95 backend + 28 headless** y explica el 25 | ✅ |
| "`STATUS.md:9`: salto 10→25 → **10→28**" | `STATUS.md:9` dice *"El salto 10 → 28 headless son los dieciocho tests de TASK-063 ... (10 + 18 = 28; el 25 era un renumerado a medias que se contradecia con su propia frase, corregido el 2026-10-03 en TASK-063 iteracion 3)"*. **Los dos documentos dicen ahora lo mismo y es lo real** | ✅ |
| "El docstring del #5 ya no dice 'solo este caeria', cita S1Z1" | `run_tests.py:14389-14397` cita S1Z1, el test 121 y el motivo (G5 tapa a G1) | ✅ |
| "La sobreescritura de `_patrones_de_categoria` es de los **tres tests por instancia**" | el **actor** es correcto: son tres, y son los tests de las filas 108, 110 y 111 | ⚠️ el actor bien, **las lineas mal** (ver D4-bis) |
| "123 tests (95 backend + 28 headless)" | derivado con `ast`: 123 llamadas `test_*`, 95 antes del marcador y 28 desde el, **marcador en `run_tests.py:15343`** | ✅ |
| "No anadio ningun test (refuerzo dos aserciones de tests existentes)" | `git show --stat 9dcd8ed`: 123 tests, los mismos; el reparto no ha cambiado | ✅ |
| "`verify_ui_syntax.py` EXITO (9 modulos)" | **9/9 modulos compilan** | ✅ |
| "`run_tests.py` ALL TESTS PASSED (123)" | control medido al inicio y al final de la ronda | ✅ |
| "`validate_docs.py` 119 OK / 0 FAIL" | **119 OK / 0 FAIL** con el `GIT_DIR` real. Con un `GIT_DIR` desechable sale **118 OK / 1 FAIL** ("historial de commits: NO SE PUEDE LEER"), y ese FAIL es el artefacto de sandbox de la ronda 3, no del repo | ✅ con salvedad declarada |

## 10.8 AUDITORIA DOCUMENTAL: LO QUE SIGUE SIENDO FALSO (3 afirmaciones)

Las cuatro de la ronda 3 estan corregidas **en el fondo**. Al corregirlas, esta ronda ha introducido
afirmaciones nuevas que no son ciertas. Las tres son de **documentacion**, ninguna de codigo.

| # | Fichero y linea | Afirmacion | Medido |
|---|---|---|---|
| **D4-bis** 🟡 | **`docs/ai/testing-guide.md:166`** (fila 123) | *"los que la sobreescriben son los tres TESTS (`run_tests.py:14318`, `:14414` y `:14441`, medido con `ast`)"* | ❌ **El actor es correcto y los tres numeros de linea son FALSOS.** Con `ast` sobre `run_tests.py` hay **tres** asignaciones a `<algo>._patrones_de_categoria` y estan en **L14353**, **L14459** y **L14486**. Las lineas citadas (14318, 14414, 14441) son `cod = _codigo_ejecutable(...)`, `target_categories=[...]` y `finally:` - codigo sin relacion. **Ironia medida: el arreglo de D4 introduce la mitad falsa de D4, y `validate_docs.py` no lo ve porque no comprueba numeros de linea** |
| **D5** 🟡 | **`STATUS.md:8`** | *"**Sintaxis Estática UI:** 🟢 Pasa al 100% (`verify_ui_syntax.py`, **8 módulos**)"* | ❌ **FALSO: son 9.** Medido ejecutando el script: compilan 9 modulos (`app.py`, `main_window.py`, `confirmation.py`, `feedback.py`, `dashboard_view.py`, `pack_manager_view.py`, `process_manager_view.py`, `notification_service.py`, `__main__.py`). El dev declaro 9 en su salida; la linea 8 de `STATUS.md` sigue diciendo 8. Se corrigio la linea 9 y no la 8, que esta justo encima |
| **D6** 🟡 | **`docs/ai/architecture.md:77`** | *"`kill_pack_apps` queda **solo** para packs de usuario"* | ❌ **FALSO.** Medido con `ast` sobre `src/`: **`kill_pack_apps` tiene 0 llamantes en todo `src/`**. Las tres rutas de apagado entran por `execute_pack` desde `e0f20db`. Vive solo en `run_tests.py` (22 llamadas) y en `docs/api.md`. Y es una **bomba de relojeria pequena pero real**: es la unica puerta que queda "matar por lista de nombres", y **no lleva la barrera de categoria** (solo el blindaje de nombres). Si alguien la reconecta para "packs de usuario" - que es justo lo que el doc le dice que haga - se salta la red que el ciclo #14 pago |

### El resto del encargo, comprobado

- **Todo el codigo del ciclo esta en uso.** Con `ast` sobre `src/`: `_pack_evaluable` (1), `_seleccion` (2),
  `execute_pack` (5, dos en `dashboard_view`), `cuenta_a_apagar` (2), `start_pack_categories` (2),
  `categorias_disponibles` (1), `_patrones_de_categoria` (1), `execute_gaming_pack` (1, desde
  `ui/app.py:119`), `should_kill_for_gaming` (1), `_resolver_app` (2), `es_pack_inerte` (2),
  `_aviso_pack_inerte` (2). **Ninguna funcion testeada y no invocada** de este ciclo. La unica que
  aparece en la lista de "definidas, testeadas y no invocadas" es `kill_pack_apps` (D6).
- **Las cuatro invariantes migradas siguen temiendo** (V7 y V8 confirmados por mutacion; A4 y U3 no se
  re-midieron porque `src/` no ha cambiado y el cierre del ciclo 14 no esta en juego en esta ronda).

## 10.9 QUE PIDE ESTA RONDA AL CICLO

Ordenado por lo que cuesta. **Ninguno de los tres primeros toca `src/`.**

| # | Accion | Severidad | Coste |
|---|---|---|---|
| 1 | **Cambiar el enfoque del #3**: dejar de preguntar si la condicion *menciona* `is_gaming` y afirmar que la construccion del acordeon **no tiene ningun antecesor condicional**, mas que su funcion no hace un `return` temprano condicionado por `is_gaming`, mas borrar la asercion de la palabra "arrancar". El §10.4 dice que formas mata y por que | 🟠 | **Un test, un commit.** Es lo unico que separa el ciclo de un `PASS` |
| 2 | **D4-bis**: corregir los tres numeros de linea de la fila 123 de `testing-guide.md` a **L14353 / L14459 / L14486** (o, mejor, borrar los numeros y dejar el nombre de los tres tests, que es lo que no se caduca) | 🟡 | Commit de texto |
| 3 | **D5**: `STATUS.md:8`, "8 modulos" → **9** | 🟡 | Commit de texto |
| 4 | **D6**: `architecture.md:77` dice que `kill_pack_apps` sigue vivo para packs de usuario y no lo esta. Decidir: **o** se borra el metodo y su fila de `docs/api.md`, **o** se documenta que es la puerta *sin* barrera de categoria y que no debe reconectarse sin pasarla por `execute_pack` | 🟡 | Commit de texto (+ decision de producto) |
| 5 | Re-auditar **solo** los mutantes `G_VAR`, `G_HELPER`, `G_GUARD2`, `G_ALIAS`, `G_GETATTR`, `G_PRED`, `D_FP1` y `D_FP2`. **No hay que re-auditar los 27**: los otros 19 mueren hoy, el `src/` no ha cambiado y nada de lo que hay que arreglar toca produccion | 🟠 | Una tanda corta |

**Lo que NO hace falta tocar:** `src/` (cero cambios desde `e0f20db` y correcto), las barreras S1/S7/A5
(medidas y cerradas), la precondicion del #16 (correcta y con poder discriminante intacto), y
`Z1` (equivalente, tercera vez).

## 10.10 CONTRATO: QUE SE HA TOCADO EN EL ARBOL DEL PROYECTO

Verificado desde la raiz del repositorio, **despues** de las 27 corridas y las 8 sondas:

```
git log --oneline -1        9dcd8ed fix(tests): cerrar U1_AND con predicado estructural y congelar la premisa del #16 (TASK-063 ronda 3)
git status --porcelain      (vacio)
git diff --stat             (vacio)
git diff --cached --stat    (vacio)
git rev-parse --git-dir     C:\Users\carch\AppData\Local\woptimizer_git\.git
```

**Declaracion honesta:** las 27 corridas y las 8 sondas fueron **enteras** en copias de `%TEMP%`. No
escribi, no borre y no comitee nada en `C:/Users/carch/Nextcloud/Scripts/woptimizer`, ni siquiera para
revertir: no hizo falta, porque nunca escribi en el. **Cero commits.** El unico fichero del arbol del
proyecto que esta modificado es **este mismo** (`openspec/changes/.../mutation-report.md`), que es el
artefacto de este rol y lo pide el encargo; `src/`, `run_tests.py` y los documentos estan **exactamente**
como los dejo `9dcd8ed`. **No he revertido nada porque no he tocado nada que revertir.**

**Estado final de las camaras:** restauradas y **en verde**. Control corrido DESPUES del ultimo mutante en
la camara `f`: `ALL TESTS PASSED`. `__pycache__` dentro de la camara: **0**. Los cuatro ficheros mutados
comparados por `SHA256` contra su `pristine`: **identicos**.

**Dos errores de sonda mios, declarados para que nadie los lea como evidencia:** (a) el `G_GUARD` de la
primera pasada murio de `NameError` porque mi helper quedaba a nivel de clase, y el `G_SELF` de la
primera pasada murio de `AttributeError` porque `self.pack` es el metodo de Tk; (b) el `Z1` de la
primera pasada uso una constante de test. Los tres se detectaron porque `roto`/`assertion` los marcaron,
se corrigieron y se **volvieron a medir**; los veredictos de §10.3 y §10.6 son los de la segunda pasada.

---

# 11. RONDA 5 - `mutation-auditor` re-audita `ae58fc2` (2026-10-03)

**Commit auditado:** `ae58fc2` - "fix(tests): el acordeon se afirma por propiedad y no por forma de gate
(TASK-063 ronda 4)".

**Metodo:** 14 corridas de suite completa declaradas por el dev (confirmadas una a una) + **13 formas
nuevas** + 2 sondas de A0 + 3 falsos positivos + 9 regresiones, en **camaras de `%TEMP%`** con
`PYTHONDONTWRITEBYTECODE=1`, `__pycache__` purgado entre mutaciones (medido: **0** al final) y
restauracion por `copyfile` desde un `pristine` propio. Ademas, una **pantalla rapida** que importa el
test #3 REAL de `run_tests.py` y lo llama contra vistas mutadas en memoria: no replica el predicado, usa
el codigo del test. **Nada reparado.** El arbol del proyecto **no se ha tocado** (§11.10).

## 11.0 VEREDICTO

# FAIL

**Ningun superviviente en la zona anti-brick y ninguno en las barreras**: los DOCE deaths que declara el
dev **mueren todos**, cada uno por su asercion, y las 9 regresiones **siguen muriendo**. (La cuenta era
"13" y era falsa: la tabla de 11.2 tiene **doce** filas de gate mas las dos sondas legitimas, que no son
deaths. Corregido en la ronda 7, §12.9 lo pidio y §13.1 lo mide.) El fallo de esta
ronda es de otro tipo y mas pequeno que el de las cuatro anteriores:

> **Una garantia NOMBRADA por el test nuevo es falsa.** A1b afirma, en su comentario y en su mensaje de
> fallo, que caza "la lista de categorias ya filtrada" y que si se filtra "el acordeon se dibuja vacio
> para un pack normal y este test pasaria por no mirar nada". **Pasa.** Con **una** variable intermedia
> entre el gate y el bucle, A1b no lo ve. Es el mismo fallo de la misma clase que las cuatro rondas
> anteriores, y es de la misma familia que el `U1_AND` que la ronda 3 reporto: **una forma mas de la misma
> cosa**.

| Severidad | Id | Que se rompe si el codigo se rompe asi |
|---|---|---|
| 🟠 **ALTA** | **M1** | `cats_visibles = all_cats if pack.is_gaming else []` y el bucle come `cats_visibles`. Un pack normal se queda **con 0 categorias** y el servicio se las sigue preguntando. **123/123 en verde** |
| 🟠 **ALTA** | **M2** | El mismo bug escrito como `if not pack.is_gaming: all_cats = set()` **antes** del bucle. **123/123 en verde** |
| 🟠 **ALTA** | **M3B** | El gate entero en `refresh_packs` (otra funcion), dejando solo `self._muestra_categorias`. `_render_pack_card` **no menciona `is_gaming` ni una vez** para la lista. **123/123 en verde** |
| 🟡 **MEDIA** | **M8** | `if not pack.is_gaming: cb.destroy()` **despues** de construir la casilla. La construccion y el cableado quedan intactos. **123/123 en verde** |
| 🟡 **MEDIA** | **M4** | `if not pack.is_gaming: acc_btn.pack_forget()`: el boton que abre el acordeon desaparece para los packs normales |
| 🟡 **MEDIA** | **FP1/FP2/FP3** | **NO son fallos: son codigo legitimo RECHAZADO.** A2 prohibe *cualquier* `return` condicionado, y su mensaje afirma que solo prohibe el de `is_gaming` |
| 🟡 **BAJA** | M5, M6, M7B | Dentro del techo que el propio test declara: (b) visibilidad = **M5**; (a) lugar de la llamada = **M6**, y **M7B** es su variante quirurgica (solo el acordeon). **Medidos, no supuestos** |

**Lo que esta ronda SI ha entregado, medido:** el re-enfoque del #3 es **real y no cosmético** - las trece
formas que la ronda 4 dejo vivas **mueren las trece por su asercion**, y las dos sondas de codigo legitimo
que la ronda 4 rechazo por error **pasan ahora la suite completa** (`rc=0`). Los dos falsos positivos de la
ronda 4 (D_FP1, D_FP2) estan **cerrados de verdad**.

## 11.1 AISLAMIENTO (medido antes de mutar nada)

Trampa del gitlink confirmada por cuarta vez: el `.git` del arbol es un **FICHERO**, asi que
`ignore_patterns(".git")` (ficheros **y** directorios) es lo unico que excluye; `robocopy /XD` no serviria.

| Camara | Entradas `.git` dentro | `git rev-parse --git-dir` desde la camara |
|---|---|---|
| cam1..cam5 | `[]` (las cinco) | con `GIT_DIR` desechable: **rc=128, salida vacia**; **sin** `GIT_DIR`: **rc=128, salida vacia** |
| repo real | - | `C:\Users\carch\AppData\Local\woptimizer_git\.git` (la suya) |

`rc=128` y salida vacia con **y** sin `GIT_DIR` es la prueba de que la camara **no puede descubrir** el
repo real. Ademas dentro de las camaras **no se invoco git para nada**: la restauracion es `copyfile` desde
el `pristine`, asi que no hay ningun `GIT_DIR` que pueda derivar a otro sitio. **Ningun commit.**

Las camaras se verificaron **fieles a `ae58fc2`** por `SHA256` de los 4 ficheros que se mutan, y el
control de las cinco dio `ALL TESTS PASSED` antes de la primera mutacion.

## 11.2 LO QUE PIDE EL ENCARGO, PUNTO 1: los DOCE deaths declarados, UNO A UNO

Los DOCE mueren **por la asercion del #3**, no por `ImportError`, `SyntaxError`, `IndentationError` ni
`NameError` (el runner marca `ROTO(...)` si la primera excepcion es de ese tipo: **0 ROTO**). La cuenta
"13" de la 11.0 y de este titulo era falsa y se corrige en la ronda 7 (§13.1): la tabla de abajo tiene
**doce** filas de gate, y las dos filas que vienen despues (`D_FP1` y `D_FP2`) son sondas de codigo
**legitimo** que deben **pasar**, asi que no son deaths.

| Id | Forma | Veredicto | Motivo literal / linea de la asercion |
|---|---|---|---|
| **U1** | `if pack.is_gaming:` sobre la seccion | ✅ **MUERE** | A1. `el espejo (def create_command) (L403) cuelga de una condicion en L336: 'pack.is_gaming'` - `run_tests.py:14325` |
| **U1_AND** | `... and pack.default_action == "kill"` | ✅ **MUERE** | A1, mismo literal, `... (L403) cuelga de una condicion en L336: "pack.is_gaming and pack.default_action == 'kill'"` |
| **G_VAR** | `gaming = pack.is_gaming` + `if gaming:` | ✅ **MUERE** | A1, `... (L404) cuelga de una condicion en L337: 'gaming'` |
| **G_ALIAS** | `p = pack` + `if p.is_gaming:` | ✅ **MUERE** | A1, `... (L404) cuelga de una condicion en L337: 'p.is_gaming'` |
| **G_GETATTR** | `if getattr(pack, "is_gaming", False):` | ✅ **MUERE** | A1, `... (L403) cuelga de una condicion en L336: "getattr(pack, 'is_gaming', False)"` |
| **G_PRED** | `if pack.id != "gaming":` | ✅ **MUERE** | A1, `... (L403) cuelga de una condicion en L336: "pack.id != 'gaming'"` |
| **G_HELPER** | `if self._es_gaming(pack):` (el predicado en un metodo) | ✅ **MUERE** | A1, `... (L406) cuelga de una condicion en L339: 'self._es_gaming(pack)'` |
| **G_OR** | `if pack.is_gaming or pack.is_favorite:` | ✅ **MUERE** | A1, `... (L403) ... : 'pack.is_gaming or pack.is_favorite'` |
| **G_ISTRUE** | `if pack.is_gaming is True:` | ✅ **MUERE** | A1, `... (L403) ... : 'pack.is_gaming is True'` |
| **G_ELSE** | la seccion va en el `else` | ✅ **MUERE** | A1, `... (L405) cuelga de una condicion en L336: 'not pack.is_gaming'` |
| **G_LISTA** | la lista filtrada, sin `if` delante | ✅ **MUERE** | **A1b**. `la casilla de L442 la dibuja el bucle de L439, pero la lista de categorias que lo alimenta depende de 'is_gaming': L437` - `run_tests.py:14382` |
| **G_GUARD2** | metodo propio con `if not pack.is_gaming: return` | ✅ **MUERE** | **A2**. `_seccion_acordeon (L338) dibuja una pieza del acordeon y ademas vuelve en L341 si se cumple 'not pack.is_gaming'` - `run_tests.py:14431` |

**Ninguno muere por una Asercion tautologica ni por un error ajeno: `ROTO = 0`.** Y el detalle que
importa: **A1 mata las once formas por el mismo motivo** - la construccion esta **dentro** de un `If`, sea
cual sea su condicion. Eso es exactamente lo que el dev afirma, y es cierto: el re-enfoque dejo de Yardar
formas.

**Las dos mitades del punto 4 del encargo: los gates legitimos y las dos sondas que la ronda 4 rechazo.**

| Sonda | Que se mete | Veredicto | Motivo literal |
|---|---|---|---|
| **D_FP1** | Una casilla **propia** del Gaming Mode dentro del badge `PRESET` | ✅ **PERMITIDO** | `rc=0`, **123/123 en verde**. La ronda 4 la rechazaba con *"una condicion que depende de is_gaming CONSTRUYE el acordeon"* |
| **D_FP2** | Un texto de aviso legitimo que dice *"va a arrancar y apagar apps"* | ✅ **PERMITIDO** | `rc=0`, **123/123 en verde**. La ronda 4 la rechazaba buscando la palabra "arrancar" |

Los **gates legitimos** del fichero (badge `PRESET` L210, ternarios del borde L173/L174, boton de
restaurar L278, `es_pack_inerte(pack.is_gaming, ...)` L561, texto del Gaming Mode L604) **siguen
permitidos**, y no por la lista del dev: **enumerados por mi cuenta con `ast`** (§11.4), son las **unicas 6
lecturas de `pack.is_gaming`** del fichero, las seis permitidas, y **la septima no existe**.

## 11.3 LO QUE PIDE EL ENCARGO, PUNTO 2: la FORMA 14 y la FORMA 15 (y la 16)

Tres rondas seguidas, cada vez que se cerraba un agujero aparecia otro de la misma familia. Aqui hay
**ocho** formas nuevas. **Ninguna es un equivalente**, y eso se midio antes de gastar las corridas
(§11.3.2).

### 11.3.1 Las ocho, y por que las usa el test

| Id | La forma, tal cual se escribe | Que oculta | Veredicto |
|---|---|---|---|
| **M1** | `cats_visibles = all_cats if pack.is_gaming else []`<br>`sorted_cats = ordenar_categorias(cats_visibles)` | La rejilla entera, a un pack normal | 🔴 **SOBREVIVE** |
| **M2** | `if not pack.is_gaming:`<br>`    all_cats = set()`<br>`sorted_cats = ordenar_categorias(all_cats)` | idem, escrito con un `if` **antes** del bucle | 🔴 **SOBREVIVE** |
| **M3B** | el gate entero en `refresh_packs` (`self._muestra_categorias = p.is_gaming`) y en la vista un `if not self._muestra_categorias: all_cats = set()` | idem, y `_render_pack_card` **no dice `is_gaming`** | 🔴 **SOBREVIVE** |
| **M8** | `cb.grid(...)` y luego `if not pack.is_gaming: cb.destroy()` | Las casillas, **despues** de construirlas | 🟡 **SOBREVIVE** |
| **M4** | `acc_btn.pack(...)` y luego `if not pack.is_gaming: acc_btn.pack_forget()` | El **boton** que abre el acordeon | 🟡 **SOBREVIVE** |
| **M5** | `grid.pack(...)` y luego `if not pack.is_gaming: grid.pack_forget()` | La rejilla visible | 🟡 **SOBREVIVE** (techo declarado (b)) |
| **M6** | en `refresh_packs`: `if p.is_gaming: self._render_pack_card(p)` | La tarjeta entera | 🟡 **SOBREVIVE** (techo declarado (a)) |
| **M7B** | la seccion extraida a un `def _construye_acordeon():` **anidado**, y la llamada `if self._acordeon_visible(pack): _construye_acordeon()` | **Solo el acordeon**, no la tarjeta | 🟡 **SOBREVIVE** |

**Las ocho por su asercion de por que deberian morir, y quien las mata: ninguna.** Las ocho dan
`ALL TESTS PASSED.` (123/123). Ninguna es `ROTO`.

### 11.3.2 Ninguna es un equivalente: medido, no afirmado

Se evalua el **iterable** del bucle de la rejilla con un pack real, control y cada forma
(`categorias_disponibles` = 3 categorias):

| Forma | `is_gaming=True` | `is_gaming=False` | Cambia |
|---|---|---|---|
| **CONTROL** | 3 casillas | 3 casillas | - |
| **M1** (un salto) | 3 | **0** | **SI** |
| **M2** (`if` antes) | 3 | **0** | **SI** |
| `G_LISTA` (la del dev) | 3 | **0** | SI |

O sea: un pack normal pasa de 3 categorias a **0**. Es **exactamente el fallo de U1** - el pack se queda
sin donde elegir categorias mientras `execute_pack` y `start_pack_categories` se las preguntan igual - y
se reproduce con dos lineas que no parecen un gate.

### 11.3.3 POR QUE M1 escapa: la razon tecnica, en cuatro lineas

A1b construye su cadena en `run_tests.py:14370-14381`:

```python
_cadena = [_bucle.iter]
for _s in ast.walk(_bucle.iter):
    ... busca la ultima asignacion a _s.id anterior al bucle ...
    _cadena.append(max(_asignaciones, ...).value)
_filtrada = next((c for c in _cadena if _lee_is_gaming(c)), None)
```

`_cadena` tiene **dos** elementos: el iterable y el valor de la asignacion de cada **nombre que aparece en
el iterable**. **No es transitiva: no vuelve a resolver los nombres de ese valor.** El limite esta a
**exactamente un salto** de la asignacion al bucle.

- `G_LISTA` (la del dev) pone el gate **en la asignacion al nombre que el bucle lee** -> un salto -> se ve.
- `M1` mete **un nombre mas** entre esa asignacion y el bucle -> dos saltos -> **no se ve**.

**Y aqui hay un detalle que importa para juzgar cual de las dos formas es la real:** la sonda que el dev
cerro con A1b es

```python
sorted_cats = ordenar_categorias([c for c in all_cats if pack.is_gaming] if pack.is_gaming else [])
```

que **repite `pack.is_gaming` dos veces** y nadie escribiria eso. `M1` es
`all_cats if pack.is_gaming else []`, que es **lo que escribe un humano**. La sonda quecerraba el agujero
era **menos natural que el agujero**.

**Arreglo que necesita (no aplicado):** hacer la resolucion **transitiva** -Walk recursivo sobre el
valor de cada asignacion, con conjunto de visitados para no ciclar-. Cuatro lineas, y no afloja nada: M1,
M2 y M3B mueren por su misma asercion, y `G_LISTA` sigue muriendo.

### 11.3.4 El techo DECLARADO, medido (y es mas estrecho de lo que el test dice)

El test escribe (en `run_tests.py:14440-14448`) que **no** cubre: "(a) un gate en el LUGAR DE LA LLAMADA
-`if pack.is_gaming: self._render_pack_card(pack)`- [...] (b) gatear la llamada a `.pack()`/`.grid()` que
hace VISIBLE la rejilla". Esas dos las medí y **efectivamente sobreviven** (M6 y M5): **el techo
declarado es real**.

Pero el techo declarado **no cubre** lo que M1, M2, M3B y M8 hacen, y no es un problema de "fuera del
fichero" o de "otra funcion":

- **M1 y M2 estan en el mismo fichero, en la misma funcion, sobre la misma lista** que A1b dice vigilar.
- **M3B esta en otra funcion**, pero **deja rastro en el fichero**, y por eso un arreglo de A1b que busque
  `is_gaming` en la vista **no lo veria**: alli donde hay que mirar, `_render_pack_card`, no aparece.
- **M8** no es ni `.pack()` ni `.grid()`: es un `.destroy()` posterior, y la construccion -la que A1
  vigila- queda intacta.

Por eso M1/M2/M3B/M8 **no son el techo**: son un agujero que el test afirma cubrir y no cubre.

## 11.4 LO QUE PIDE EL ENCARGO, PUNTO 3: ¿A0 es un ancla real o decorativa?

**Es un ancla real.** Se midio quitando cada mitad del ancla por separado, no leyendo el codigo:

| Sonda | Que se quita | Veredicto | Motivo literal |
|---|---|---|---|
| **A0-SIN-ESPEJO** | `create_command` -> `_toggle_categoria` en todo el fichero | ✅ **MUERE** | `no aparece el ESPEJO (def create_command) en la vista: este test dejaria de mirar la seccion de categorias y un acordeon entero desaparecido pasaria por no mirarlo nada` - **exactamente en `run_tests.py:14299`**, que es la linea de su asercion |
| **A0-SIN-CASILLAS** | los dos bucles de la rejilla (las 4 casillas) | ✅ **MUERE** | En la pantalla aislada (#3 solo): `no aparece ninguna casilla de categoria (CTkCheckBox con command=create_command(...)): la rejilla ha desaparecido de la vista y este test no lo veria`. **En la suite completa** la primera asercion que salta es de otro test -`test_orden_de_categorias_no_es_alfabetico` (`run_tests.py:5955`), *"no llama a `ordenar_categorias`"*-, porque borrar los bucles se lleva tambien la llamada. Se declara: **A0 no es decorativa**, pero su segunda asercion queda **sombreada** por un test anterior que detecta el mismo defecto por otra via |

**Y A0 no puede ser vacua:** sin el espejo, A1 y A2 no tendrian nada que mirar, y el test lo dice el
mismo. Medido: quitar el espejo **mata**.

## 11.5 LO QUE PIDE EL ENCARGO, PUNTO 4: ¿el test se ha vuelto demasiado fuerte?

**Si. En A2, y esta medido con tres sondas de codigo 100% legitimo** - las tres **RECHAZADAS**:

| Sonda | Que se mete (y por que es legitimo) | Veredicto | Motivo literal |
|---|---|---|---|
| **FP1** | `if not pack: return` al principio de `_render_pack_card` (guard defensivo estandar) | 🔴 **RECHAZADO** | `_render_pack_card (L167) dibuja una pieza del acordeon y ademas vuelve en L169 si se cumple 'not pack': el guard clause 'if not pack.is_gaming: return' es la unica forma de gate que no es antecesor` - `run_tests.py:14431` |
| **FP2** | `if not sorted_cats: return` (no construir una rejilla vacia) | 🔴 **RECHAZADO** | mismo aserto, `vuelve en L439 si se cumple 'not sorted_cats'` |
| **FP3** | `if categorias: return` - **el patron que la propia clase ya usa** en `pack_manager_view.py:666` | 🔴 **RECHAZADO** | mismo aserto, `vuelve en L438 si se cumple 'categorias'` |

**El mensaje de A2 MIENTE, y por ahi se sabe que el defecto es real:** dice *"el guard clause `if not
pack.is_gaming: return` es la unica forma de gate que no es antecesor"*, o sea que afirma estar midiendo
una sola condicion. **El codigo prohibe CUALQUIER `return` condicionado**, de cualquier clase. Y la
propia clase **ya tiene seis `if pack is None: return`** (L466, L483, L512, L520, L593, L611) y el
`if categorias:` de L666: un desarrollador que aplique a `_render_pack_card` la convencion que el
fichero ya usa se encuentra el test en contra. Es **la misma trampa que la ronda 4 ya diagnostico** -"un
test que obliga a aflojar es un test que garantiza que se afloje"-, aqui en A2 en vez de en A1.

**En A1 no se ha encontrado ningun falso positivo plausible**, y se dice por que: A1 prohibe que la
construccion tenga un **antecesor** condicional, y la unica forma legitima de eso seria "solo pintar la
rejilla si hay categorias", que en una funcion que dibuja una tarjeta entera **solo** se puede escribir
como `if ...: return` - es decir, cae en A2, no en A1.

**Arreglo que necesitan las tres (no aplicado):** que A2 mire la **condicion** del `return` con el
`_lee_is_gaming` que el propio test ya define (`run_tests.py:14340`), en vez de mirar solo que haya un
condicional. **No afloja nada:** `G_GUARD2` sigue muriendo, porque su guard es `not pack.is_gaming`. Y el
mensado deja de ser falso.

## 11.6 LO QUE PIDE EL ENCARGO, PUNTO 5: LAS TRES CORRECCIONES DOCUMENTALES

| Correccion | Afirmacion | Medido |
|---|---|---|
| **D4-bis** | `testing-guide.md:123` cita los **tres NOMBRES** de los tests que sobreescriben `_patrones_de_categoria` **y** sus lineas (`run_tests.py:14489`, `:14595`, `:14622`) | ⚠️ **MEDIO CIERTO.** Los **nombres** y el **actor** (los tres TESTS, por instancia) son correctos. Las **tres lineas siguen siendo FALSAS**: con `ast` las reales son **`L14485`**, **`L14591`** y **`L14618`**, y las tres citadas se quedan **cuatro lineas mas abajo**. Es el **mismo defecto que la ronda 4 reporto**, y ahora el propio texto admite *"los numeros se caducan con cada refactor del fichero, los NOMBRES no"*: la linea que el propio autor declara no fiable es precisamente la que esta mal |
| **D5** | `STATUS.md:8` - 9 modulos | ✅ **CIERTO.** Dice 9 y **los enumera**; `verify_ui_syntax.py` compila 9: `app`, `main_window`, `confirmation`, `feedback`, `dashboard_view`, `pack_manager_view`, `process_manager_view`, `notification_service`, `__main__`. Medido ejecutando el script |
| **D6** | `architecture.md:77` - `kill_pack_apps` esta **MUERTA a proposito y no debe reconectarse**, con **0 llamantes** en `src/` | ✅ **CIERTO, y las dos mitades.** Con `ast` sobre `src/`: `kill_pack_apps` tiene **0** llamantes; `execute_pack` tiene **5**, y son **exactamente** las cinco lineas que cita el documento (`dashboard_view.py:385,427,483`, `pack_manager_view.py:635`, `gaming_service.py:260`); `execute_gaming_pack` tiene **1**, y `ui/app.py:119` es literalmente `self.gaming_service.execute_gaming_pack(gaming_pack)` |

### Y el recuento, derivado con `ast` (no leido)

| Afirmacion | Medido |
|---|---|
| **123 tests = 95 backend + 28 headless** | ✅ CIERTO. Derivado sobre las **LLAMADAS** del bloque `__main__` (no las definiciones: los headless se registran al final). Marcador `print("\n--- Running Headless UI Tests ---")` en **`run_tests.py:15475`**; **95** antes, **28** despues, **123** en total |
| **123 definidos y 123 invocados, ninguno huerfano** | ✅ CIERTO, medido: las dosenas coinciden exactamente, `DEFINIDAS PERO NO LLAMADAS: ninguna` |
| **citar NOMBRES de tests en vez de lineas no rompe el validador** | ✅ **CIERTO.** `validate_docs.py` -> **119 OK / 0 FAIL** con el `GIT_DIR` real, y su check 7 sigue derivando el reparto y **reimprime el marcador vivo** (`run_tests.py:15475`). No comprueba numeros de linea, que es justo por lo que D4-bis se cuela |
| **`verify_ui_syntax.py`** | ✅ EXITO, 9/9 modulos |
| **CERO cambios en `src/`** | ✅ **CIERTO y por encima de lo que declara el dev**: `git show --name-only ae58fc2` **no lista ningun fichero bajo `src/`**, y `git diff e0f20db ae58fc2 -- src/` sale **vacio**. Los cinco commits del ciclo (`e0f20db` -> `d318fef` -> `9dcd8ed` -> `ae58fc2`) **no han tocado produccion ni una linea**: todos los hallazgos de las cinco rondas son de cobertura, no de codigo |

## 11.7 LO QUE PIDE EL ENCARGO, PUNTO 6: LAS REGRESIONES

Las nueve, contra `ae58fc2`. **Ninguna regresion**, y `Z1` por **quinta** vez equivalente.

| Id | Que se rompe | Veredicto | Motivo literal / quien muere |
|---|---|---|---|
| **S1** | el filtro `get_safety_badge(c)["tier"] != "danger"` de `target_categories` | ✅ **MUERE** | `test_barrera_roja_sola_con_el_snapshot_y_la_db_en_discrepancia` (`run_tests.py:15146`): `solo el verde marcado debe llegar a kill_processes. Llego ['svchost.exe', 'onedrive.exe']` |
| **S7** | `_pack_evaluable` escribe en el pack original | ✅ **MUERE** | `test_el_filtro_de_la_puerta_no_escribe_en_el_pack_original` (`:15200`): `el filtro de la barrera escribio en el pack del usuario: target_categories quedo en ['🟢 Sincronización'] cuando se marcó ['🔴 Sistema de Windows', '🟢 Sincronización']` |
| **A5** | `_patrones_de_categoria` sin `.exe` | ✅ **MUERE** | `test_arranque_por_categoria_toma_los_nombres_de_la_db_real` (`:15271`): `los candidatos de una categoria tienen que ser Nombres con extension [...] salieron ['woptimizer_t063_db', 'woptimizer_t063_otro.com']` |
| **S4** | G5: la barrera sobre `p.category` | ✅ **MUERE** | `test_execute_gaming_pack_integration` (`:798`): `skipped debe sumar los descartes del filtro (svchost y lsass): 1` |
| **S5** | G4: el blindaje de nombres | ✅ **MUERE** | mismo aserto, mismo test |
| **S6** | `force_refresh=True` -> `False` | ✅ **MUERE** | mismo test (`:787`): `G0 es obligatorio: sin force_refresh=True la cache TTL de 2 s puede dejar fuera lo que el usuario acaba de lanzar` |
| **V7** | el Gestor vuelve a `kill_pack_apps(pack.apps)` | ✅ **MUERE** | `test_el_feedback_de_pack_dice_la_verdad` (`:9665`): `el pack se cierra por la puerta comun con SUS apps, no con un atajo ni con una lista vacia (llego ['C:\Juegos\juego.exe'])` |
| **V8** | el worker llama a `restore_gaming_session()` | ✅ **MUERE** | `test_los_workers_de_pack_solo_publican_por_after` (`:8871`): `el worker toca la vista fuera de self.after(0, ...)` |
| **Z1** | barrera roja duplicada en `execute_gaming_pack` | 🟡 **EQUIVALE** | `ALL TESTS PASSED`. **Quinta medicion.** El filtro de la puerta comun ya la aplica, y `ae58fc2` no toca `src/`, asi que **no podria** haber cambiado |
| **PREMISA** | el snapshot del #16 lleva `svchost` ROJO (la premisa rota) | ✅ **MUERE** | `preCONDICION ROTA: este test solo mide la barrera de categoria si el snapshot y la DB DISCREPAN [...] sin G1 este test pasaria igual, es decir, no mediria nada` (`:15136`) |

## 11.8 LOS ERRORES DE ESTA SONDA, DECLARADOS PARA QUE NADIE LOS LEA COMO EVIDENCIA

Cinco. Todos se detectaron porque el veredicto no cuadraba con lo esperado, y todos se corrigieron y **se
volvieron a medir**:

1. **El mas grave, y mio: el `pristine` envenenado.** Mi primera pasada llamaba `pristine_de(camara)` en
   cada forma, y esa funcion ** SOBREESCRIBE** el `pristine` con el fichero **ya mutado**: las
   mutaciones se **acumulaban** y la segunda se media sobre la primera. Se manifesto porque la tercera
   forma encontro su ancla **0 veces**. **Invalido cam1, cam2 y cam3 de la primera pasada**; las camaras
   se restauraron desde el repo por `SHA256` y **los tres lotes se volvieron a correr**. (El runner del
   dev lo hace bien: su `main()` solo crea el `pristine` si no existe.)
2. **Consola cp1252 (Trampa #16).** El runner del dev imprime la asercion de S7, que lleva emojis, y
   **CASCA** con `UnicodeEncodeError`. Perdio S7 en la primera pasada. Rehecho con `PYTHONIOENCODING=utf-8`.
3. **El runner del dev se cuelga, y el PowerShell habria perdido los 13 resultados.** Con
   `subprocess.run(capture_output=True)`, en Windows, si el hijo deja nietos con la tuberia abierta,
   `communicate()` **se queda bloqueado para siempre** aunque el hijo este muerto: se quedo **14 minutos**
   con 1,3 s de CPU en `D_FP2` (que solo cambia un string, o sea que el cuelgue es del host y no del
   mutante). Y como el comando era `python ... | Out-String`, **todo lo anterior se habria perdido**.
   Se sustituyo por un runner **sin pipe**: la salida va a un **fichero** y cada forma **anexa** su
   resultado, asi que un cuelgue no borra lo ya medido.
4. **M3 v1, sonda invalida:** `AttributeError` - puse `self._muestra_categorias` sin inicializarlo, y
   `refresh_packs` pinta el pack de Gaming **antes** del bucle. No media nada. Corregido (M3B, con el
   atributo inicializado): **SOBREVIVE**.
5. **M7 v1, sonda invalida:** `UnboundLocalError` - generaba la llamada a `_construye_acordeon()` **antes**
   del `def`. La suite la mato, que es justo su trabajo, pero no media lo que yo queria. Corregido (M7B,
   `def` primero): **SOBREVIVE**.

Ademas, una nota de alcance: **`cam6` del arnes heredado esta incompleta** (le faltan los tres ficheros de
`src/`) y no se ha usado. Las cinco camaras `cam1..cam5` se han verificado una a una contra `ae58fc2`.

## 11.9 QUE PIDE ESTA RONDA AL CICLO

Ninguno de los tres primeros toca `src/` (que no se ha tocado en cinco rondas).

| # | Accion | Severidad | Coste |
|---|---|---|---|
| 1 | **A1b transitivo**: resolver la cadena de asignaciones **recursivamente** (con conjunto de visitados), no a un solo salto. Mata M1, M2 y M3B por su asercion actual y no afloja `G_LISTA` | 🟠 | **Unas 4 lineas en el #3** |
| 2 | **A2 por condicion**: que mire el `return` con el `_lee_is_gaming` que el test ya tiene, en vez de prohibir cualquier `return` condicionado. No afloja `G_GUARD2` y **deja de mentir el mensaje** | 🟠 | **Unas 3 lineas** |
| 3 | **Anadir al techo declarado** del comentario del #3 las dos formas que el texto **no** nombra y que hoy sobreviven: el **`.destroy()` posterior** (M8) y la **lista filtrada a dos saltos** (M1/M2). El techo esta escrito, y esta bien: lo que falta es que sea **completo** | 🟠 | Commit de texto |
| 4 | **D4-bis**: corregir las tres lineas a **L14485 / L14591 / L14618**, o borrar los numeros y dejar solo los nombres, que es lo que el propio texto dice que es lo fiable | 🟡 | Commit de texto |
| 5 | Si se decide que M5/M6/M7B (visibilidad y lugar de la llamada) son formatos **aceptables**, **dejarlo escrito en el repo** y no solo en el informe: es un techo real, y un techo no declarado se vuelve a reportar cada ronda | 🟡 | Commit de texto |

**Lo que NO hace falta tocar:** `src/` (intacto desde `e0f20db`), las barreras S1/S7/A5 (cerradas y
re-medidas), la precondicion del #16 (correcta, con poder discriminante intacto: `PREMISA` muere y `S1`
sigue muriendo por la asercion principal), `D5` y `D6` (ciertos), `Z1` (equivalente, quinta vez), y las
**dos sondas de codigo legitimo** D_FP1 y D_FP2, que ahora pasan y estan **cerradas de verdad**.

## 11.10 CONTRATO: QUE SE HA TOCADO EN EL ARBOL DEL PROYECTO

Verificado desde la raiz del repositorio, **despues** de las 40 corridas y las 4 pantallas:

```
git log --oneline -1        ae58fc2 fix(tests): el acordeon se afirma por propiedad y no por forma de gate (TASK-063 ronda 4)
git status --porcelain      (vacio)
git diff --stat             (vacio)
git diff --cached --stat    (vacio)
git rev-parse --git-dir     C:\Users\carch\AppData\Local\woptimizer_git\.git
```

**Declaracion honesta:** las 40 corridas de suite y las 4 pantallas fueron **enteras** en copias de
`%TEMP%`. **No escribi, no borre y no comitee nada** en
`C:/Users/carch/Nextcloud/Scripts/woptimizer`, ni siquiera para revertir: no hizo falta, porque nunca
escribi en el. **Cero commits.** `src/`, `run_tests.py` y los documentos estan **exactamente** como los
dejo `ae58fc2`; lo unico modificado es **este mismo** fichero, que es el artefacto de este rol. **No he
revertido nada porque no he tocado nada que revertir.**

Lo que **si** se ha ejecutado **contra el repo real** son **tres validadores de solo lectura** -
`validate_docs.py` (que no contiene ni una llamada a `open(...,'w')`, `write`, `remove` ni `shutil`, y se
comprobo con `grep` antes de correrlo) y `verify_ui_syntax.py` -, y cuatro `git log`/`status`/`diff`/
`rev-parse` de lectura.

**Estado final de las camaras:** cam1..cam5 **restauradas y fieles a `ae58fc2` por SHA256**, con su
`pristine` tambien fiel, y **0** ficheros `.pyc` y **0** directorios `__pycache__`. El control final,
corrido **despues** del ultimo mutante en cam1, da **`ALL TESTS PASSED`** (123/123).

# 12. RONDA 6 - `mutation-auditor` re-audita `5f96671` (2026-10-03)

# PARCIAL

**Un hallazgo (a) que NO esta en el techo declarado y que rompe la transitividad que el dev
dice haber arreglado**: cuando la casilla se construye dentro de una **list comprehension**, A1b
deja de mirarla entera, porque su resolucion busca el `For` ancestro de la construccion y una
`ListComp` no es un `ast.For`. Medido, no supuesto. **Todo lo demas que el dev declara esta
bien**: los cuatro deaths mueren por `14493`, la contraprueba de A2 pasa en el orden que declara,
el techo (e) es el precio real de su arreglo y no una excusa, y la cadena transitiva resuelve
cadenas de cinco saltos sin colgarse.

Los tres fallos de la ronda 5 quedan cerrados de verdad: **A1b es transitivo** (M1, M2, M10 y la
cadena de cinco saltos mueren todos por la asercion del #3), y **A2 mira la condicion**, no la
forma del gate (FP1, FP2, FP3 pasan; GG2 y el guard por alias mueren).

Lo que **no** cierra el ciclo es `LC`, y por debajo hay un techo que **se queda corto**.

---

## 12.1 LO QUE PIDE EL ENCARGO, PUNTO 1: los cuatro deaths, en la forma NATURAL

Los cuatro mueren **por la asercion de `run_tests.py:14493`**, no por `ImportError`, `SyntaxError`,
`NameError` ni `AttributeError` (el runner marca `ROTO` si la primera excepcion es de ese tipo:
**0 ROTO** en las 45 formas).

| Mutante | La forma natural aplicada | Veredicto | Motivo literal |
|---|---|---|---|
| **M1** | `cats_visibles = all_cats if pack.is_gaming else []` + `sorted_cats = ordenar_categorias(cats_visibles)` | **killed** | `la casilla de L442 la dibuja el bucle de L439, pero la lista de categorias que lo alimenta depende de `is_gaming`: L439` |
| **M2** | `if not pack.is_gaming:` / `all_cats = set()` antes del `sorted_cats` | **killed** | `la casilla de L443 la dibuja el bucle de L440, pero la lista de categorias que lo alimenta depende de `is_gaming`: L438` |
| **M3B** | el flag lo pone `refresh_packs` leyendo `p.is_gaming` de forma **directa**, y la vista solo mira el flag | **killed** | `la casilla de L440 la dibuja el bucle de L437, pero la lista de categorias que lo alimenta depende de `is_gaming`: L435` |
| **M10** | cadena de **cuatro** saltos: `s1 = all_cats if ... else []` / `s2 = set(s1)` / `s3 = sorted(s2)` / `s4 = list(s3)` | **killed** | `la casilla de L445 la dibuja el bucle de L442, pero la lista de categorias que lo alimenta depende de `is_gaming`: L442` |
| **C5** (extra) | cadena de **cinco** saltos, uno de ellos una comprehension | **killed** | `la casilla de L446 la dibuja el bucle de L443, ...: L443` |

**No son equivalentes**, medido con el bloque de la vista ejecutado y no con una lectura del
codigo: el control da **3/3** categorias para un pack normal, y los cuatro mutantes dan **0**.
Es el fallo de U1 en dos lineas, y el test lo ve.

---

## 12.2 LA CADENA TRANSITIVA: EXACTA, TERMINA Y NO ES PATOLOGICA

El encargo pedia tres cosas y las tres se cumplen, medidas con `ast` sobre el fichero
definitivo y no con el predicado del test:

1. **Es EXACTAMENTE lo que dice.** El punto fijo marca `cats_visibles` (M1), los cuatro eslabones
   `s1..s4` (M10) y los cinco `c1..c5` (C5). Con cinco saltos el TAINT crece de 19 a 25 nombres y
   aun asi el bucle **converge en 7 vueltas**.
2. **No tiene condicion de parada prematura.** Converge en **5 vueltas** con la vista limpia,
   **6** con la cadena de cuatro y **7** con la de cinco, siempre por debajo de la cota
   `len(ESCRITURAS) + 1` (1915 sobre `run_tests.py`, 78-81 sobre la vista). Cada vuelta marca al
   menos un nombre o para, asi que no puede colgarse.
3. **El conjunto de visitados no produce una falsa convergencia.** `_vistos` guarda `id()` de
   nodos **distintos**, y el conjunto se contrasta con `TAINT` (un nombre), no con el `id()` de un
   valor: dos saltos que Repiten el mismo nombre no se confunden con dos saltos que avanzan.

**Coste patologico: ninguno.** El punto fijo completo son **0,008-0,011 s** (1914 escrituras
analizadas). El test entero va 99-110 s, igual que antes del arreglo.

---

## 12.3 LA CONTRAPRUEBA DE A2, EN EL ORDEN QUE EL DEV DECLARA

Este era el punto que pedia medir **en ese orden**, porque es el orden en el que puede salir mal.
Medido por separado y en ese orden, en **suite completa** (`rc=0` los tres primeros):

| # | Forma | Veredicto | Que prueba |
|---|---|---|---|
| 1 | **FP1** `if not pack: return` | **PERMITIDO** (rc=0) | A2 acepta el `return` whose condition no habla del pack |
| 2 | **FP2** `if not sorted_cats: return` | **PERMITIDO** (rc=0) | A2 acepta el guard de "no pintar una rejilla vacia" |
| 3 | **FP3** `if categorias: return` | **PERMITIDO** (rc=0) | A2 acepta el patron que la clase **ya usa** en su L666. Se declaro `categorias` antes para que el codigo sea ejecutable: con un nombre inventado se mediria un `NameError`, no un falso positivo |
| 4 | **GG2** metodo propio con `if not pack.is_gaming: return` | **killed** por `14560` | `dibuja una pieza del acordeon y ademas vuelve en L341 si se cumple 'not pack.is_gaming', que depende de si el pack es el de Gaming` |
| 5 | **ALIAS_GUARD** `p = pack` + `if p.is_gaming: return` | **killed** por `14560` | idem, con el alias declarado, que es como lo escribiria un humano |

**Los dos lados, por separado: el `if not card.winfo_exists(): return` de Tk tambien esta
PERMITIDO** con A2 mirando la lectura directa, y ese es el que hace que la decision sea correcta.

**Nota de sonda, declarada porque el encargo la pide:** mi primera `ALIAS_GUARD` salio `ROTO` con
`NameError: name 'p' is not defined` -- un guard que usa `p` sin haberlo declarado es un
`NameError`, no una forma de gate. Corregida la sonda y **volvio a morir por `14560`**. Un `ROTO`
no cuenta como muerte: si no seMira el motivo, se contabiliza como una forma mas cerrada y no lo
esta.

---

## 12.4 EL TECHO (e): ES EL PRECIO REAL, NO UNA EXCUSA

El dev dice que A2 usa la lectura **directa** porque propagar el taint rechazaba un guard de Tk
legitimo, y que el precio es el guard clause por atributo de otra funcion. **Las dos mitades se
miden:**

| Sonda | Veredicto | Que demuestra |
|---|---|---|
| **LIMITE_E** (el techo (e) literal: `self._flag = p.is_gaming` en `refresh_packs` + `if not self._flag: return` antes de la seccion) | **SOBREVIVE** (rc=0) | **el precio EXISTE**: A2 no ve el guard clause por atributo ajeno, y el acordeon desaparece para el pack normal con los 123 en verde |
| **GUARD_TK** (`if not card.winfo_exists(): return`, con `card` nacido de `border_width=2 if pack.is_gaming else 1`) | **PERMITIDO** (rc=0) | **la justificacion es CIERTA**: con la propagacion ese guard legitimo caia, y no tiene por que caer |

El techo no es mas estrecho que la realidad en su eje. **Lo que si se queda corto esta en otro
sitio, y es el hallazgo de 12.6.**

---

## 12.5 LA FORMA 16: NO ESTA EN EL TECHO, Y ROMPE LA RESOLUCION

### 12.5.1 El mutante que sobrevive: `LC` (comprehension)

La casilla se construye **dentro de una list comprehension** en vez de en un `for`:

```python
_pares = [(c, arranque) for arranque in (False, True)
          for c in all_cats if pack.is_gaming]        # <- filtro con is_gaming
_cbs = [
    ctk.CTkCheckBox(grid, text=..., command=create_command(...))
    for c, arranque in _pares                          # <- la casilla vive AQUI
]
for i, cb in enumerate(_cbs):                          # <- el bucle que se resuelve
    cb.grid(row=i // 2, column=i % 2, ...)
```

**Veredicto: SOBREVIVE** (rc=0, los 123 en verde). Para un pack normal el acordeon se dibuja
**vacio**: 0 de 3 categorias, exactamente el fallo de U1.

**El mecanismo, instrumentado y no supuesto** (reimplementando la resolucion del test sobre el
mutante, linea a linea):

```
casilla L441 -> ancestro de bucle: For (L438)     iter: enumerate(sorted_cats)   depende: False
casilla L454 -> ancestro de bucle: For (L451)     iter: enumerate(sorted_cats)   depende: False
casilla L466 -> ancestro de bucle: FunctionDef (L167)     <-- NO ES UN For
```

La tercera casilla --la unica que lleva el filtro-- **se pierde en la busqueda del `For`
ancestro**: el `while` de `run_tests.py:14454-14457` sube desde la `ListComp` (que no es `ast.For`
ni una funcion) hasta el `FunctionDef`, y `if not isinstance(_bucle, ast.For): continue`
(`:14458-14459`) la descarta **sin mirarla**. No es que la cadena falle por saltos: es que la
cadena **nunca se le pide**.

**Dos controles que separan la causa del sintoma:**

- **`LC_SOLO_UM`: el MISMO filtro de `is_gaming` con la casilla en un `for` normal -> MUERE**
  (`la casilla de L442 ... depende de `is_gaming`: L439`). O sea: **el filtro no es el problema;
  la comprehension si.** Y el filtro con la comprehension es una forma que un humano escribe sin
  pensar (quitar el `for`, meterlo en una lista).
- **`LC_LIMPIA`: la MISMA comprehension SIN filtro de `is_gaming` -> PERMITIDO** (rc=0). El
  defecto es de la **forma**, no de este filtro.

### 12.5.2 Lo que SI esta en el techo, medido (no lo cuento como hallazgo)

El encargo pedia no contar como hallazgo lo que el propio test ya declara. Medidos, y asi quedan:

| Forma | Veredicto | Techo que lo cubre |
|---|---|---|
| `M3B_LLAM` -- el flag lo pone `refresh_packs` pero el valor llega por el **retorno de una llamada** (`self._muestra_categorias = self._es_gaming_de(p)`) | **SOBREVIVE** | **(d)**: "el VALOR que devuelve una llamada, no". Instrumentado: `._muestra_categorias` **no** entra en el TAINT (si entraba con la forma directa, que es la de M3B, y M3B muere) |
| `HELPER_LISTA` -- el filtro entero vive en otro metodo, `self._categorias_de(pack)`, llamado desde la vista | **SOBREVIVE** | **(d)**: "una lista filtrada que llega de OTRA funcion por una llamada" |
| `GG2_METODO` -- guard clause con el predicado en un metodo, `if not self._es_gaming(pack): return` | **SOBREVIVE** | **(e)**, el mismo eje que el techo (e) literal: A2 no sigue el valor del que viene la condicion |

**Honestidad sobre el teto, que es lo que decide el cierre:** (d) y (e) son truthful sobre su
eje --dicen "el valor que devuelve una llamada" y "la condicion cuyo valor viene de otro sitio", y
eso es exactamente lo que no cubren. `LC` **no** es ninguna de las dos: no hay llamada, no hay
guard clause, y el filtro **esta en el fichero que dibuja**. **El techo (a)-(e) no lo nombra, y
por lo tanto el techo es mas estrecho que lo que de verdad no cubre.**

### 12.5.3 Un falsopositivo de mi propia sonda, declarado

`PARAM` (la rejilla entera extraida a un metodo que recibe la lista filtrada **como parametro**)
parecia un superviviente, pero murio a los **0,6 s** por `El toggle de categorias automaticas
debe releer el pack y persistirlo con `update_pack``: otro test lo caza por el **cableado**, no
por el gate. **No es un superviviente**, y declararlo lo habria sido un hallazgo inventado.
Tambien `TRY` salio `ROTO` con `AttributeError: 'Try' object has no attribute 'test'`: es el
propio test #3 el que se rompe con un `try/except` alrededor, porque `_CONDICIONALES` incluye
`ast.Try` y su asercion hace `_condicion.test` sobre un nodo que no lo tiene. Es un defecto real
del test, pero **no es un fallo de cobertura del acordeon** y no lo cuento como (a).

---

## 12.6 LAS CUATRO CUENTAS DEL ENCARGO

### 12.6.1 "Los 13 deaths" NO cuadra: son 12, y el dev lo sabe

La seccion 11.2 tiene **12 filas de gate**, no 13: `U1`, `U1_AND`, `G_VAR`, `G_ALIAS`,
`G_GETATTR`, `G_PRED`, `G_HELPER`, `G_OR`, `G_ISTRUE`, `G_ELSE`, `G_LISTA`, `G_GUARD2`. Las otras dos
filas de la tabla son `D_FP1` y `D_FP2`, sondas de codigo **legitimo** que deben **pasar**: no son
deaths. El dev lo dice en el techo (`run_tests.py:14604-14610`: "De las trece formas que midio el
mutation-auditor, las **DOCE** que envuelven la construccion las mata A1 o A2; la treceava --el
guard clause con el guard de TASK-062 sin desatar-- murio de otro test"). **El techo esta
correcto; el "13 deaths" del informe es mio y esta mal.** Corregido en 12.9.

### 12.6.2 Las tres lineas de D4-bis: las tres cifras declaradas eran falsas

`testing-guide.md:166` declara `14631 / 14740 / 14667` como las lineas donde los tres tests
sobreescriben `_patrones_de_categoria`. Medidas con `ast` sobre el fichero definitivo:

| Declarado | Que hay de verdad en esa linea | Linea real |
|---|---|---|
| `14631` | `def test_start_categories_arranca_y_cuenta_honestamente():` -- el `def` esta donde debe, pero **no** es la asignacion | la asercion G0 esta en **L787/788** |
| `14740` | `def test_categoria_roja_en_start_categories_no_arranca():` | la asercion G4 (blindaje) esta en **L750** |
| `14667` | `f"started={started2} failed={failed2}"` -- una linea de mensaje, no una asignacion | la asercion G5 (barrera roja en `skipped == 1`) esta en **L14731** |

Las tres cifras vienen de la ronda 4 y **las tres** son falsas: apuntan a `def`, a `def` y a un
`f-string`. El propio doc ya lo avisaba ("los numeros se caducan con cada refactor... por eso se
citan los dos" -- los nombres), y es exactamente lo que paso.

### 12.6.3 Los cuatro recuentos: cuadrados

| Recuento | Medido | Estado |
|---|---|---|
| Tests definidos en `run_tests.py` | **123** | - |
| Llamadas a `test_*` dentro del bloque `__main__` (derivado de las **llamadas**, no de las definiciones) | **123** | **cuadrado: 123 = 123 + 0** |
| Definidas y **no** llamadas desde `__main__` | **0** | ninguna huerfana |
| Reparto `95 backend + 28 headless` | validado por `validate_docs.py` (check 7, `[OK] STATUS.md: declara el reparto 95 backend + 28 headless`) | **cuadrado** |

### 12.6.4 Los tres validadores, corridos aqui

| Validador | Resultado | rc |
|---|---|---|
| `verify_ui_syntax.py` | `EXITO: Todos los modulos UI estan impecables` | **0** |
| `run_tests.py` (control final, cam5 restaurada) | `ALL TESTS PASSED` | **0** |
| `validate_docs.py` | **`Resumen: 119 OK, 0 FAIL`** | **0** |

Los tres declados por el dev se reproducen **exactos**.

---

## 12.7 LAS REGRESIONES: 12/12 deaths y las sondas legitimas

Las **doce** formas de las rondas 3-5 **siguen muriendo**, cada una por su asercion, y las dos
mitades de la premisa del #16 tambien:

| Forma | Veredicto | Forma | Veredicto |
|---|---|---|---|
| `U1` | killed | `G_PRED` | killed |
| `U1_AND` | killed | `G_HELPER` | killed |
| `G_VAR` | killed | `S1` | killed |
| `G_ALIAS` | killed | `S7` | killed |
| `G_GETATTR` | killed | `A5` | killed |
| `G_OR` | killed | `S4` | killed |
| `G_ISTRUE` | killed | `S5` | killed |
| `G_ELSE` | killed | `S6` | killed |
| `GG2` / `ALIAS_GUARD` | killed | `V7` / `V8` | killed |
| `PREMISA` / `PREMISA_S1` | killed | `DFP1` / `DFP2` / `FP1` / `FP2` / `FP3` | **PERMITIDO** (rc=0) |

**Z1: VERDE por sexta medicion.** Es el mutante **equivalente** (el filtro de la categoria roja en
`execute_gaming_pack` no cambia el comportamiento observable), asi que un verde es lo que **debe**
darse; lo que importa es que **sigue siendolo**, y no ha cambiado por nada de esta ronda.

---

## 12.8 EL ARNES: UN DEFECTO HEREDADO, DECLARADO Y CORREGIDO

La instrumentacion de `wopt_r5` (que el dev reutilizo tras verificarla) es **correcta en lo
esencial**: restaura desde `pristine` **antes** de aplicar, purga `__pycache__` y `.pyc` entre
mutantes, pone `PYTHONDONTWRITEBYTECODE=1`, escribe a fichero en vez de canalizar y quita
`GIT_DIR`. La use tras comprobarla linea a linea.

**Un defecto de sonda mio, de la misma clase que el de la ronda 5 y mas grave:** mi primera sonda
`LC` se aplicaba con **cero cambios** (`{} or {}` crea un dict nuevo y devuelve el viejo), y
`aplicar()` no distingue "no cambio" de "cambio legitimo": la forma salia `VERDE` como si el
mutante hubiera sobrevivido. Se ve **midiendo el numero de ficheros cambiados antes de correr**,
y hay que hacerlo siempre. Lo mismo con `PARAM`, que parecia un hallazgo y era un falso positivo
(12.5.3).

**Defecto mio de scheduling, declarado:** lance una tanda de 5 mutantes sobre las mismas camaras
que tenian otra tanda en vuelo. Las dos se pisan los ficheros y **sus veredictos no valen**.
**Descarte** los resultados contaminados (guardados con sufijo `.contaminado`), **restaure** las
cinco camaras a `pristine` y verifique fidelidad por **SHA256**, y anadi un **cerrojo por camara**
que falla ruidosamente en vez de medir basura. **Los resultados de este informe son los de las
tandas con cerrojo**, y los resultados que se solaparon (10 de la tanda `a`, completados antes del
solapamiento) se volvieron a medir en la tanda `c`.

---

## 12.9 CORRECCION DE LA CUENTA QUE NO CUADRA

La linea `**Los 13 deaths que declara el dev mueren todos**` de la seccion 11.0 y el titulo
`los 13 deaths declarados, UNO A UNO` de la 11.2 dicen trece donde hay **doce** gates, y el
"los trece mueren por la asercion del #3" es falso para la treceava forma (murio de otro test y
por otro motivo, como el propio techo reconoce). **Corregido aqui; la 11.2 queda con doce filas
de gate mas las dos sondas legitimas.** No he tocado el texto de la 11: es el registro de la ronda 5
y esta seccion es la que lo corrige.

---

## 12.10 LO QUE ESTA EN EL TECHO, LO QUE NO, Y QUE HAY QUE HACER

| # | Forma | Estado |
|---|---|---|
| 🔴 **(a) ALTA** | **`LC`: la casilla construida en una `list comprehension`.** A1b no la mira porque `ListComp` no es `ast.For` y el `continue` de `:14458` la descarta. El acordeon se dibuja vacio para un pack normal con los 123 en verde. **No esta en el techo (a)-(e)** | **FALLO REAL DE COVERAGE** |
| 🟡 (d) | `M3B_LLAM` / `HELPER_LISTA`: el valor (o el filtro) llega de otra funcion por una llamada | techo declarado y medido |
| 🟡 (e) | `GG2_METODO`: guard clause con el predicado en un metodo | techo declarado y medido |
| 🟡 (e) | `LIMITE_E`: guard clause por atributo de otra funcion | techo declarado y medido |
| ⚪ (c) | "los 13 deaths" de 11.0 y 11.2 | correccion de texto (12.9) |
| ⚪ (c) | `14631 / 14740 / 14667` en `testing-guide.md:166` | correccion de texto (12.6.2) |

**El arreglo de `LC` es pequeno y no inventaria ninguna regla:** en el `while` que busca el `For`
ancestro (`:14454-14457`), **`ast.ListComp` y `ast.SetComp` y `ast.DictComp` tambien son bucles**,
porque su `generators` son `ast.comprehension`, y una comprehension **no** se salta con
`continue` como si no hubiera bucle. Con eso, la casilla de la comprehension resolveria su
`ListComp` como bucle, su `iter` seria el de la comprehension y el filtro se veria.

**VERDICT: PARCIAL.** Los tres fallos de la ronda 5 estan **cerrados de verdad** y el techo (e)
resulta ser **el precio real** de su decision, no una excusa. Pero `LC` es un **fallo real de
cobertura** que **no esta en el techo declarado** y que **rompe la transitividad** que el dev
declara haber arreglado: la cadena no es que resuelva mal, es que **nunca se le pide** a la
casilla. Con un rojo vivo asi el ciclo **sigue abierto**, y el mutante exacto que lo mantiene
abierto es `LC` (casilla construida en una `list comprehension`, filtro `if pack.is_gaming` dentro
de la propia comprehension, con los 123 en verde y 0/3 categorias para un pack normal).

---

## 12.11 AISLAMIENTO Y ESTADO FINAL

- **Repo real: `5f96671` intacto.** `git log --oneline -1` = `5f96671`, `git status --porcelain`
  limpio antes de esta seccion, `git diff --stat` y `git diff --cached --stat` vacios, y
  `git rev-parse --git-dir` = `C:/Users/carch/AppData/Local/woptimizer_git/.git`. El `.git` de
  este repo es un **fichero** de 57 bytes (gitlink), asi que las copias se hicieron con
  `shutil.copytree(..., ignore=shutil.ignore_patterns(".git"))`, que cubre ficheros **y**
  directorios, y se **comprobo** que las cinco camaras no contienen ninguna entrada `.git` y que
  `git rev-parse --git-dir` dentro de ellas sale con **rc=128** (no hay repo al que pertenecer).
- **`src/` sin tocar**, `run_tests.py` y los documentos como los dejo `5f96671`. **Cero commits.**
  Lo unico modificado en el arbol es **este mismo fichero**, que es el artefacto de este rol, y no
  he revertido nada porque no he tocado nada que revertir.
- **Validadores de solo lectura** ejecutados contra el repo real: `verify_ui_syntax.py` y
  `validate_docs.py` (comprobado con `grep` que no contienen ninguna llamada a `open(...,'w')`,
  `write`, `remove` ni `shutil`), mas cuatro `git` de lectura.
- **Cam1..cam5 restauradas y fieles a `5f96671` por SHA256** en los cuatro ficheros, con **0**
  ficheros `.pyc` y **0** directorios `__pycache__`. El control final, corrido **despues** del
  ultimo mutante, da **`ALL TESTS PASSED`** (123/123, rc=0).
# 13. RONDA 7 - `openspec-dev` cierra el rojo de LC y el techo (2026-10-03)

`5f96671` + este pase. El rojo de la ronda 6 era `LC`: la casilla construida
dentro de una **list comprehension** no se miraba, porque al buscar el `For`
ancestro una `ListComp` no lo es, el `while` subia hasta el `FunctionDef` y el
`continue` la descartaba sin mirarla. No era que la cadena resolviera mal: nunca
se le preguntaba.

## 13.1 EL ARREGLO, Y POR QUE NO ES EL DEL AUDITOR

El auditor propuso "`ast.ListComp` / `ast.SetComp` / `ast.DictComp` tambien son
bucles" y asi se hizo primero. **Medido, ese arreglo solo pierde una muerte que
el test ya tenia**, y por eso no se shipped:

| Forma | Con el arreglo "solo la comprehension" | Con el que se ha shipped |
|---|---|---|
| `LC` (comprehension con `if pack.is_gaming`) | **MUERE** | **MUERE** |
| `LC_ANIDADA` (comprehension **limpia** dentro de un `for` gateado) | **SOBREVIVE** | **MUERE** |

`LC_ANIDADA` la mataba el test de `5f96671` (`run_tests.py:14493`, lit: *"la
casilla de L441 la dibuja el bucle de L439 ... depende de `is_gaming`: L439"*).
Medido en las DOS direcciones, con una camara que lleva el test de `5f96671`
verificado por SHA256 (`e5b771bd5c0824ad`, 796633 bytes) y otra el de ahora. Perder
una muerte es peor que declarar un limite, asi que el `while` sube por los
**todos** los bucles que envuelven la casilla, del mas interior al mas exterior
(`run_tests.py:14488-14494`).

Con la vista real no cambia nada: sus casillas viven en dos `for` y no hay
ninguna comprehension en el camino, asi que la lista de bucles de cada casilla
tiene **un** elemento y el recorrido es el de antes. El arreglo son **+57 lineas**
en `run_tests.py` entre `5f96671` y `9ebeabc` (15689 -> 15746, marcador 15637 ->
15694; `git diff --numstat` da 114 inserciones y 57 borrados). La cifra de la
primera redaccion de esta linea, "+39", era falsa y la corrigio el
`mutation-auditor` en su seccion 14.6. CRLF preservado (`ast.parse` en verde en
los tres parches).

## 13.2 LO QUE PIDE EL ENCARGO, PUNTO 1: LC Y LOS DOS CONTROLES

| Forma | Que mide | Veredicto | Motivo literal |
|---|---|---|---|
| **`LC`** | la casilla en la comprehension, filtro `if pack.is_gaming` | **MUERE** en `14530` | `la casilla de L466 la dibuja el bucle de L465, pero la lista de categorias que lo alimenta depende de `is_gaming`: L476` |
| **`LC_SOLO_UM`** | el **mismo** filtro con la casilla en un `for` normal | **MUERE** en `14530` | `la casilla de L442 la dibuja el bucle de L439, ... depende de `is_gaming`: L439` |
| **`LC_LIMPIA`** | la **misma** comprehension **sin** filtro | **PERMITIDO** (`rc=0`, 123/123) | - |

Los tres en **suite completa**, no solo en la pantalla. Los dos controles siguen
ciertos: el filtro no es el problema, la comprehension si; y el defecto es de la
**forma**, no de este filtro.

**Equivalencia por construccion, ejecutada y no leida.** Se ejecuta el bloque
real del acordeon contra un `ctk` de mentira y se cuentan las casillas
construidas (`equiv.py`):

| Vista | pack de Gaming | pack normal |
|---|---|---|
| repo sin mutar | **6** | **6** |
| `LC` | **12** | **6** |
| `LC_LIMPIA` | **12** | **12** |

`LC` **no es equivalente**: un pack normal se queda con 6 de las 12 casillas, y
las que pierde son exactamente las de la tanda "arrancar". Con el test de
`5f96671` eso pasaba con los 123 en verde.

**DEFECTO PROPIO, declarado:** la primera version de `equiv.py` cortaba el bloque
en el segundo `cb.grid` y por eso midio `6/6` para `LC` --la tanda que anade el
mutante queda fuera del corte. Corregido para cortar al final de la seccion.

## 13.3 LA CONTRAPRUEBA, EN EL ORDEN QUE EL ENCARGO PIDE

Medida por separado y **en ese orden**, en **suite completa**:

| # | Forma | Veredicto |
|---|---|---|
| 1 | **FP1** `if not pack: return` | **PERMITIDO** (`rc=0`) |
| 2 | **FP2** `if not sorted_cats: return` | **PERMITIDO** (`rc=0`) |
| 3 | **FP3** `if categorias: return` | **PERMITIDO** (`rc=0`) |
| 4 | **D_FP1** casilla propia del Gaming Mode en el badge | **PERMITIDO** (`rc=0`) |
| 5 | **D_FP2** texto de aviso legitimo | **PERMITIDO** (`rc=0`) |
| 6 | **GUARD_TK** `if not card.winfo_exists(): return` | **PERMITIDO** (`rc=0`) |
| 7 | **CONTROL** (camara sin mutar) | **VERDE**, 123/123 |
| 8 | **GG2** metodo propio con `if not pack.is_gaming: return` | **MUERE** en `14599` |
| 9 | **ALIAS_GUARD** `p = pack` + `if p.is_gaming: return` | **MUERE** en `14599` |

Los siete verdes primero y los dos muertos despues, que es el orden en que la
transaccion puede salir mal. No salio.

## 13.4 LA REGRESION: 12/12, LAS 9 INVARIANTES Y LAS DOS MITADES

Las doce formas de gate de la 11.2 **siguen muriendo**, cada una por su asercion:

| Forma | Asercion | Forma | Asercion |
|---|---|---|---|
| `U1` | `14326` | `G_OR` | `14326` |
| `U1_AND` | `14326` | `G_ISTRUE` | `14326` |
| `G_VAR` | `14326` | `G_ELSE` | `14326` |
| `G_ALIAS` | `14326` | `G_GUARD2` | `14599` |
| `G_GETATTR` | `14326` | `G_LISTA` | `14530` |
| `G_PRED` | `14326` | `M1` | `14530` |
| `G_HELPER` | `14326` | `M2` | `14530` |
| `M3B` | `14530` | `M10` | `14530` |
| `C5` (cadena de cinco saltos) | `14530` | | |

Las dos mitades de la premisa del #16 (`PREMISA` y `PREMISA_S1`) mueren con
`preCONDICION ROTA: ... el snapshot y la DB DISCREPAN ... sin G1 este test pasaria
igual, es decir, no mediria nada`. Las nueve del servicio y la vista
(`S1`, `S4`, `S5`, `S6`, `S7`, `A5`, `V7`, `V8`, `Z1`) siguen como estaban:
**ocho mueren** y **`Z1` sigue VERDE por septima medicion**, que es lo que tiene
que pasar: es el mutante equivalente.

## 13.5 EL TECHO: SE AMPLIA A SEIS EJES, CON EL (f) MEDIDO

Los ejes (a) a (e) **siguen siendo ciertos en su eje** y se han vuelto a medir
en vez de heredarlos:

| Eje | Forma | Veredicto | Por que no lo cubre |
|---|---|---|---|
| (d) | `M3B_LLAM` | **SOBREVIVE** | el valor llega por el **retorno de una llamada** |
| (d) | `HELPER_LISTA` | **SOBREVIVE** | la lista filtrada llega de **otra funcion** por una llamada |
| (e) | `GG2_METODO` | **SOBREVIVE** | el predicado del guard esta en un **metodo** |
| (e) | `LIMITE_E` | **SOBREVIVE** | el atributo lo pone **otra funcion** |

Y el **(f) nuevo, que es el precio de contar las comprehensions como bucles**, con
las dos formas de la misma decision medidas:

| Forma | Que es | Veredicto |
|---|---|---|
| **`COSMETICA_FOR`** | `for _n in range(2 if pack.is_gaming else 1):` envolviendo el grid: solo elige el **numero de columnas**, las casillas se dibujan igual para todos | **MUERE** en `14530` |
| **`COSMETICA_IF`** | la misma decision con `if (2 if pack.is_gaming else 1) == 2:` | **MUERE** en `14326` (A1) |

La del `if` **ya la rechazaba A1 antes de este cambio**, asi que el (f) no es una
regla nueva: es la MISMA invariante escrita con la sintaxis del bucle. Se eligio
midiendo, y la alternativa --resolver solo el bucle mas interior-- se midio
peor: deja viva `LC_ANIDADA`, que el test de `5f96671` mataba. El techo ahora
tiene seis ejes y dice el limite real.

**DEFECTO PROPIO #2, declarado:** el primer `COSMETICA_FOR` era
`for _n in (2 if pack.is_gaming else 1):`, que itera un `int` y dio
`ROTO(TypeError): 'int' object is not iterable`. Un `ROTO` no cuenta como muerte,
asi que se corrigio a `range(...)` y se volvio a medir.

**DEFECTO PROPIO #3, declarado:** el primer `HELPER_LISTA` mio insertaba la
llamada donde empieza el **comentario** de la seccion, antes de que `all_cats` se
asigne, y dio `UnboundLocalError`. Corregido para sustituir la linea real de
`sorted_cats`, y entonces **SOBREVIVE**, que es lo que el eje (d) declara.

## 13.6 LAS DOS CORRECCIONES DE TEXTO

**La cuenta de "13 deaths".** La tabla de la 11.2 tiene **DOCE** filas de gate
(`U1`, `U1_AND`, `G_VAR`, `G_ALIAS`, `G_GETATTR`, `G_PRED`, `G_HELPER`, `G_OR`,
`G_ISTRUE`, `G_ELSE`, `G_LISTA`, `G_GUARD2`) mas las dos sondas legitimas
(`D_FP1`, `D_FP2`), que deben **pasar** y no son deaths. Corregidas las tres
citas de la 11.0 y de la 11.2, que decian trece.

**D4-bis, las tres lineas, medidas con `ast` sobre el fichero definitivo:**

| Declarado (ronda 4) | Que hay de verdad ahi | **Medido (ronda 7)** |
|---|---|---|
| `14631` | un `def` | la ASIGNACION esta en **L14704-14707** (`def` en L14688) |
| `14740` | un `def` | la ASIGNACION esta en **L14810-14812** (`def` en L14797) |
| `14667` | un `f-string` de mensaje | la ASIGNACION esta en **L14837-14839** (`def` en L14824) |

Son las **tres** y **no hay una cuarta** en el fichero. El documento cita ahora
la ASIGNACION --que es lo que dice citar-- y el `def` aparte, para que la
confusion de la ronda 4 no se repita.

## 13.7 LOS TRES VALIDADORES, CONTRA EL REPO REAL

| Validador | Salida | rc |
|---|---|---|
| `verify_ui_syntax.py` | `EXITO: Todos los modulos UI estan impecables` | **0** |
| `run_tests.py` | `ALL TESTS PASSED.` (123/123) | **0** |
| `validate_docs.py` | `Resumen: 119 OK, 0 FAIL` | **0** |

Y el reparto, derivado por el check 7: **123 definidos = 123 invocados = 95
backend + 28 headless**, cuadrado.

## 13.8 EL ARNES DEL DEV: CONSTRUIDO DESDE CERO, CON SUS DOS DEFECTOS

No se reutilizo el del auditor (las camaras de la ronda 5 venian de `ae58fc2`,
no de `5f96671`). Se construyo nuevo y se corrigieron los dos fallos que el
auditor declaro en el suyo:

1. **Sonda que aplica CERO cambios.** `aplicar()` mide cuantos ficheros cambian
   de SHA256 frente al `pristine`; si no cambia ninguno devuelve
   `NO_EXISTE_LA_FORMA` y **jamas** `PERMITIDO`. Se autocomprobo con dos sondas
   sin cambios (`SINOPSE_A` con `cambios: {}` y `SINOPSE_B` con una identidad):
   las dos salen `ERROR_DE_SONDA`.
2. **Solapamiento de tandas.** Cerrojo por camara con `O_CREAT|O_EXCL`: una
   segunda tanda sobre la misma camara se **niega** a arrancar. La
   `restaurar()` se verifica por SHA256 y **aborta** si la camara no vuelve a ser
   el `pristine`, y la salida va a **fichero** (en Windows `communicate()` con
   nietos que tienen la tuberia abierta se cuelga aunque el hijo este muerto).

Camaras `r1..r6`, cada una **4/4 SHA256** fiel al repo al crearse, sin ninguna
entrada `.git` dentro (el `.git` de este arbol es un **fichero**, asi que la copia
es `shutil.copytree(ignore=...)` y no `robocopy /XD`).

**46 formas medidas en suite completa** (~100 s cada, 6 camaras en paralelo),
cada una con su `pantalla` --el test #3 **real** importado de la camara, no una
replica del predicado-- y su suite. El `CONTROL` no es una "forma" sino la
camara sin mutar: una sonda con `cambios` vacio no existe, y por eso el arnes la
rechaza en vez de|Verde|la.

## 13.9 ESTADO FINAL

- `src/` **sin tocar**, como en `5f96671`. Lo unico modificado: `run_tests.py`
  (el test #3 y su techo), `docs/ai/testing-guide.md` (filas 107 y 123) y este
  informe.
- `run_tests.py`: **+57 lineas** (no +39: cifra corregida en la ronda 8), CRLF
  preservado (15746 CRLF, 0 LF sueltos), `ast.parse` en verde. Las lineas de las
  aserciones quedan en `14326` (A1), `14530` (A1b) y `14599` (A2).
- **Veredicto de la ronda 7: el rojo de LC esta cerrado y el techo esta
  ampliado, no acortado.** Queda vivo lo que el techo (a)-(f) declara, y queda
  declarado con su forma medida.

---

# 14. RONDA 7 DEL MUTATION-AUDITOR (la que decide el cierre)

Medido sobre `9ebeabc`, en copia de `%TEMP%`, con repo git **propio y
desechable** por camara. **52 mutantes**, todos en suite completa, todos con el
CONTROL verde primero.

## 14.0 EL ARNES, Y SUS TRES DEFECTOS PROPIOS (declarados)

Los declaro porque en las dos ultimas rondas los dos arnes Coventry una muerte
falsa, y este tambien fallo antes de producir un solo numero:

1. **DEFECTO QUE PRODUJO 48 MUERTES FALSAS.** Mi `copytree` llevaba
   `ignore_patterns(".git*")` creyendo que cubria mas variantes del gitlink. Eso
   excluye tambien `.gitignore`. Sin `.gitignore` en la camara, el CONTROL
   NEGATIVO de `test_el_archivo_legacy_esta_versionado_y_no_vuelve_a_la_raiz`
   (`git check-ignore` no puede responder "ignorado") falla **siempre**, y los 48
   mutantes salieron "muertos" con un `AssertionError` ajeno al mutante. Solo se
   excluye `.git` exacto, y ahora se **comprueba que `.gitignore` esta** al crear
   la camara, o `ABORTO`.
2. **El arnes se midio sobre una base roja y no lo savia.** Anadido: si el
   `CONTROL` no sale `PERMITIDO`, el arnes **aborta** y no mide nada. Y si un
   mutante muere con la **misma asercion que el CONTROL**, se marca
   `MUERE_IGUAL_QUE_EL_CONTROL` y no cuenta como muerte.
3. **`comparativa.py` capture mal la variable del mutante** (cargo
   `VISTA_MUTADA` una vez y la reusé para las cuatro filas), asi que las cuatro
   filas de la 14.2 son en realidad **la misma mutacion, `LC_ANIDADA`, medida
   contra los dos test**. La conclusion que sostienen es la que importa y no
   cambia, pero las etiquetas "forma=LC" de esa tabla **no son correctas** y no
   hay que leerlas como si lo fueran.

Ademas: cerrojo por camara con `O_CREAT|O_EXCL` (una segunda tanda se NIEGA),
`restaurar()` verificado por SHA256 con `ABORTO` si no vuelve, `ERROR_DE_SONDA`
si un patron aplica cero cambios, y `PYTHONDONTWRITEBYTECODE=1` + purga de
`__pycache__` entre mutaciones. Los 48 patrones se autocomprobaron **en memoria**
antes de gastar una sola corrida: 8 estaban rotos (asignacion `cb =` dentro de
una comprehension, entre otros) y se corrigieron.

**Por que la camara necesita repo:** sin `.git` propio, la suite cae en
`%LOCALAPPDATA%\woptimizer_git\.git` --**el repo real**-- para las pruebas de
git. Cada camara lleva el suyo (`git init` + `add` + `commit`), y se verifico
que no tiene `alternates` ni `remote` y que sin `GIT_DIR` resuelve a si misma.
El repo real no se toco: `9ebeabc`, arbol limpio, y los cuatro SHA256 de los
ficheros vigilados iguales a los de antes de empezar.

## 14.1 LAS DOS AFIRMACIONES IMPORTANTES, EN LAS DOS DIRECCIONES

**(A) `LC` y `LC_ANIDADA` mueren.** Medido, `rc=1`, por la asercion de `14530`:

| Forma | Veredicto | Asercion |
|---|---|---|
| `LC` casilla en ListComp | **MUERE** | `la casilla de L451 la dibuja el bucle de L450, pero la lista de categorias que lo alimenta depende de is_gaming` |
| `LC_ANIDADA` comprehension limpia dentro de un `for` gateado | **MUERE** | `la casilla de L452 la dibuja el bucle de L450, ...` |
| `LC_SOLO_UM` el mismo filtro en un `for` normal | **MUERE** | `la casilla de L455 la dibuja el bucle de L452, ...` |
| `LC_LIMPIA` comprehension **sin** filtro (codigo legitimo) | **PERMITIDO** | -- |

**(B) El arreglo NO ha perdido ninguna muerte previa.** Esta es la que mas
importaba, y se midio montando cada version del test contra la misma vista
mutada:

| Test | Mutante | Veredicto | Asercion |
|---|---|---|---|
| `5f96671` (el de antes) | `LC_ANIDADA` | **MUERE** | `la casilla de L452 la dibuja el bucle de L450, ...` |
| `9ebeabc` (el nuevo) | `LC_ANIDADA` | **MUERE** | la misma, literal |

**La afirmacion del dev se sostiene: `LC_ANIDADA` la mataba `5f96671` y la sigue
matando el arreglo.** Ademas las **12 de la 11.2** y `M1`, `M2`, `M3B`, `M10`,
`C5` (cinco saltos) **siguen muriendo cada una por su asercion** (vease 14.5),
las dos mitades de la premisa del #16 mueren con `preCONDICION ROTA`, y `Z1` sale
**VERDE por septima medicion**. Cero muertes perdidas.

## 14.2 EL TECHO (f): MEDIDO, Y SI MENTIA

`COSMETICA_FOR` y `COSMETICA_IF` **mueren** los dos, como declara el dev. Pero su
justificacion **no se sostiene tal como esta escrita**, y por un motivo que
refuerza al dev en vez de debilitarlo:

| Forma | Veredicto | Cuantas casillas construye (mi extractor) |
|---|---|---|
| repo sin mutar | -- | gaming **6**, normal **6** |
| `COSMETICA_FOR` `for _n in (2 if pack.is_gaming else 1):` | **MUERE** en `14530` | gaming **9**, normal 6 |
| `COSMETICA_IF` `if (2 if pack.is_gaming else 1) == 2:` | **MUERE** en `14326` | gaming **6**, normal **3** |

El techo dice que el `for` "solo cambia el numero de columnas" y que "las
casillas se dibujan igual para todos". **Eso es falso:** con el `for` el pack de
Gaming construye **9** casillas --la fila entera **duplicada**--, y con el `if`
el pack normal **pierde** las 3 de "arrancar". O sea, **ninguna de las dos formas
es cosmetica**: las dos cambian el comportamiento, y por eso las dos deben morir.
El argumento de simetria ("la del `if` ya la rechazaba A1, asi que no es una
regla nueva") es cierto pero no es el que sostiene el limite. El que lo sostiene
es mas simple y mas fuerte: **un bucle sobre la construccion cuyo iterable
depende de `is_gaming` o la duplica o la deja de dibujar, y no hay version
legitima de el.**

**Y el limite no se ha vuelto demasiado fuerte.** Dos formas de codigo
**legitimo** que la regla nueva podria haber rechazado y **no** rechaza:

| Sonda legitima | Veredicto |
|---|---|
| `FP_COLUMNAS` elijiendo el numero de columnas por el pack **dentro de `.grid()`** (`column=i % (2 if pack.is_gaming else 1)`) | **PERMITIDO** |
| `FP_DOS_TANDAS` la casilla dentro de **dos `for` anidados** (el de fuera sobre la constante `(False, True)`, el de dentro sobre `enumerate(sorted_cats)`) | **PERMITIDO** |

`FP_DOS_TANDAS` es la sonda directa a "todos los bucles que envuelven la casilla":
dos bucles, ninguno manchado, y la regla nueva los mira a los dos y **deja
pasar**. Con eso, **el techo (f) es un techo y no un falso positivo rotulado.**

## 14.3 LA EQUIVALENCIA DE LC, EJECUTADA CON MI PROPIO EXTRACTOR

Sin su `equiv.py` (ya declara un defecto). Extraigo el bloque real del acordeon
por marcadores, lo `exec` contra un `ctk` de mentira y **cuento las casillas
CONSTRUIDAS**:

| Vista | gaming | normal | |
|---|---|---|---|
| repo sin mutar | **6** | **6** | referencia |
| `LC` | 6 | **3** | el pack normal pierde las 3 de "arrancar" |
| `LC_ANIDADA` | 6 | **3** | igual |
| `LC_SOLO_UM` / `GENEXP_GATE` / `SETCOMP_GATE` / `COMPR_TRES` | 6 | **3** | igual |
| `LC_LIMPIA` | 6 | **6** | equivalente |

**La conclusion del dev se reproduce exactamente: `LC` hace que el pack normal
pierda las casillas.** Lo que **no** reproduce son sus cifras absolutas: el
informe dice `LC` = **12/6** y `LC_LIMPIA` = **12/12**; a mi me salen **6/3** y
**6/6**. La razon es la misma en los dos casos (los numeros del informe son el
doble de los mios), lo que ademas implica que su `LC_LIMPIA` --que se presenta
como "la forma legitima de esta misma decision"-- construye **12** casillas donde
el repo construye 6, es decir que **duplica widgets tambien en la forma que se
declara legitima**. Corregir la tabla a 6/3 y 6/6.

## 14.4 LO QUE SI ENCUENTRE: TRES SUPERVIVIENTES, UNA SOLA CAUSA

Todos son el **mismo agujero de anclaje**: una casilla construida dentro de un
`Lambda` **no se reconoce como casilla**, asi que ni A1 ni el A1b nuevo llegan a
mirarla. Medido, y los tres verificados **no equivalentes** con mi extractor
(los tres: gaming 6, **normal 3**):

| Mutante | Forma | Veredicto | En el techo? |
|---|---|---|---|
| `MAP_LAMBDA_FN` | `def _caja(cat): return CTkCheckBox(...)` + `list(map(_caja, sorted_cats if pack.is_gaming else []))` | **PERMITIDO** | **si**, es (a) literal: "la seccion extraida a un `def` anidado cuya llamada se gatea" |
| `MAP_LAMBDA` | la misma cosa con un `lambda` en vez de un `def` | **PERMITIDO** | (a) **por el motivo, no por la palabra**: el techo nombra `def`, y aqui no hay `def` ni "llamada gateada": el gate esta en el **argumento** de `map()` |
| `LISTA_LAMBDA_APLICADA` | `(lambda c: CTkCheckBox(...))(cat)` **dentro de la comprehension**, cuyo iterable si es `sorted_cats if pack.is_gaming else []` | **PERMITIDO** | **no**. No hay `def`, no hay extraccion, y la comprehension **si** es el bucle que alimenta la casilla: es justo lo que el arreglo nuevo dice mirar |
| `MAP_LAMBDA_2` | el `if` metido en el cuerpo del `lambda` de fuera | **MUERE** en `14326` | -- |

**Severidad: BAJA, y conviene decirlo.** El patron`(lambda c: ...)(cat)` dentro
de una comprehension no lo escribe nadie; `MAP_LAMBDA_FN` ya estaba declarado y
`MAP_LAMBDA` es el mismo mecanismo con otra sintaxis. **No toca la barrera
anti-brick**: no hay ningun mutante vivo en `gaming_service.py`, `process_service.py`
ni la barrera de categoria. Lo que queda vivo es "el pack normal pierde 3
casillas de la tanda arrancar" en una forma de codigo que hay que escribir a
propósito.

**Lo mas barato para cerrarlo es una palabra:** en el techo (a), "la seccion
extraida a un **`def` o `lambda`** anidado". Con eso los tres quedan dentro de un
limite **medido** y el ciclo cierra. La otra via es que `_es_casilla_del_acordeon`
reconozca un `CTkCheckBox` dentro de un `Lambda`, y entonces mueren los tres.

## 14.5 LA REGRESION COMPLETA (12 + 5 + 2 + 9), TODAS POR SU ASERCION

| Forma | Asercion que la mato |
|---|---|
| `U1` | `14326` -- `una casilla de categoria (CTkCheckBox) (L455) cuelga de una condicion en L450` |
| `U1_AND` | `14326` |
| `G_VAR` | `14326` (L456) |
| `G_ALIAS` | `14326` (L456) |
| `G_GETATTR` | `14326` (L455) |
| `G_PRED` | `14326` (L455) |
| `G_HELPER` | `14326` (L459) -- `cuelga de una condicion en L454: 'self._es_gaming(pack)'` |
| `G_OR` | `14326` (L455) |
| `G_ISTRUE` | `14326` (L455) |
| `G_ELSE` | `14326` (L457) |
| `G_LISTA` | `14530` (L441 / bucle L438) |
| `G_GUARD2` | `14599` -- `_seccion_acordeon (L439) dibuja una pieza del acordeon` |
| `M1` | `14530` (L442 / L439) |
| `M2` | `14530` (L443 / L440) |
| `M3B` | `14530` (L442 / L439) |
| `M10` (cuatro saltos) | `14530` (L445 / L442) |
| `C5` (cinco saltos) | `14530` (L446 / L443) |
| `PREMISA` | `preCONDICION ROTA: este test solo mide la barrera de categoria si el snapshot y la DB DISCREPAN` |
| `PREMISA_S1` | la misma |
| `S1` | `solo el verde marcado debe llegar a kill_processes. Llego [...]` |
| `S4` / `S5` | `skipped debe sumar los descartes del filtro (svchost y lsass): 1` |
| `S6` | `G0 es obligatorio: sin force_refresh=True la cache TTL de 2 [s]` |
| `S7` | `el filtro de la barrera escribio en el pack del usuario: tar...` |
| `A5` | `los candidatos de una categoria tienen que ser Nombres con e...` |
| `V7` | `el pack se cierra por la puerta comun con SUS apps, no con u...` |
| `V8` | `el worker toca la vista fuera de self.after(0, ...)` |
| `GG2` | `14599` -- `_seccion_acordeon2 (L439)` |
| `ALIAS_GUARD` | `14599` -- `_seccion_acordeon3 (L439)` |
| `Z1` | **PERMITIDO**, septima medicion verde |

**La contraprueba, en el orden pedido:** `FP1`, `FP2`, `FP3`, `D_FP1`, `D_FP2`,
`GUARD_TK` **PERMITIDOS**, `CONTROL` verde 123/123, y despues `GG2` y
`ALIAS_GUARD` **MUERTOS**. No salio.

**Formas nuevas que medi y el arreglo NO debe ver** (ademas de las de la
familia lambda): `GENEXP_GATE` **MUERE**, `SETCOMP_GATE` **MUERE**, `COMPR_TRES`
(tres niveles de comprehension, el gate en el mas exterior) **MUERE**. Los tres
confirman que la resolucion de "todos los bucles que envuelven la casilla" es
**realmente recursiva** y no solo "el siguiente hacia fuera".

## 14.6 LO DOCUMENTAL

**Reproducido con `ast`, sin creerse al dev:**

- Las **tres** lineas de D4-bis: `L14704` (def `L14688`), `L14810` (def
  `L14797`), `L14837` (def `L14824`), y **son tres, no hay una cuarta**. La fila
  123 de `testing-guide.md` las cita ya bien: **esta vez la correccion es
  verdadera.**
- Los cuatro recuentos: **123** definidos = **123** invocados, ninguno huerfano,
  y el reparto **95 backend + 28 headless** con el marcador en
  `run_tests.py:15694`. `validate_docs.py` da **119 OK / 0 FAIL** (`rc=0`) y su
  linea 125 ya dice `(marcador en run_tests.py:15694)`.
- `verify_ui_syntax.py`: **9 modulos, EXITO, rc=0**.
- `src/` sin tocar desde `5f96671`: confirmado, el diff de `9ebeabc` no toca
  `src/`.
- Aserciones en `14326` (A1), `14530` (A1b), `14599` (A2): confirmadas.
- `run_tests.py`: 15746 lineas, 15746 CRLF, 0 LF sueltos: confirmado.

**Tres falsedades, las tres de texto (c):**

1. **"`+39 lineas`" es falso.** `run_tests.py` entre `5f96671` y `9ebeabc` es
   **+57** lineas: 15689 -> 15746, marcador 15637 -> 15694, y `git diff --numstat`
   da **114 inserciones y 57 borrados** (171 lineas tocadas). Ni el neto ni el
   total dan 39.
2. **"`COSMETICA_FOR` solo cambia el numero de columnas"** es falso (14.2): el
   pack de Gaming acaba con 9 casillas en vez de 6, la fila duplicada.
3. **El techo se cuenta a si mismo mal en dos sitios.** `run_tests.py:14612` dice
   "Las cinco se MIDIERON vivas" y `run_tests.py:14657` dice "Ninguno de los
   seis"; `testing-guide.md` fila 107 dice "Ninguno de los **cinco**" con seis
   ejes enumerados. Son seis.

**No he encontrado ninguna falsedad nueva en la 13.** La 13.4, la 13.5, la 13.6 y
la 13.7 se sostienen con lo que he medido, con las tres correcciones de arriba.

## 14.7 VEREDICTO DE LA RONDA 7

**FAIL, y solo por una cosa, y no es una muerte perdida.**

- **(a) Fallo real de cobertura: UNO, `LISTA_LAMBDA_APLICADA`.** Vive, no es
  equivalente (el pack normal pierde 3 casillas de "arrancar") y **no esta en el
  techo declarado**: no hay `def`, no hay extraccion, y la comprehension es
  justamente el bucle que el arreglo nuevo dice mirar. Se cierra con una palabra
  en el techo (a) ("`def` o `lambda`") o haciendo que
  `_es_casilla_del_acordeon` reconozca la casilla dentro de un `Lambda`, y entonces
  mueren los tres de la familia. Es de severidad **baja** y explicito que
  **no toca la barrera anti-brick**: no hay ningun mutante vivo en
  `gaming_service.py`, `process_service.py` ni en la barrera de categoria.
- **(b) Techo declarado y medido: SEIS, y el (f) es honesto.** Los seis estan en
  el propio test con su mutante. Y conteste a la pregunta del encargo: el (f) **no
  prohibe codigo legitimo**. Lo he medido con dos sondas que la regla nueva
  rechazaba o podria rechazar (`FP_COLUMNAS`, `FP_DOS_TANDAS` con dos bucles
  anidados) y **las deja pasar**. La redaccion de (f) esta mal justificada
  (14.2), pero su **contenido es mas estrecho** de lo que el texto sugiere, que es
  la direccion buena.
- **(c) Texto documental: TRES** lineas (14.6).

**Y lo mas importante de la ronda, en una linea: el arreglo del dev NO ha
perdido ninguna muerte.** `LC_ANIDADA` la mataba `5f96671` y la sigue matando; las
12 de la 11.2, `M1`, `M2`, `M3B`, `M10`, `C5`, las dos mitades de la premisa, las
nueve de servicio/vista, `GG2` y `ALIAS_GUARD` siguen muriendo cada una por su
asercion, y `Z1` sigue verde por septima vez. Tras siete rondas, lo que queda no
es un agujero de la barrera: es una palabra en el techo.

**Repo real: NO TOCADO.** `git log --oneline -1` = `9ebeabc`, `git status
--porcelain` vacio, `git diff --stat` y `git diff --cached --stat` vacios,
`rev-parse --git-dir` = `%LOCALAPPDATA%\woptimizer_git\.git`, y los cuatro
SHA256 de los ficheros vigilados iguales a los de antes de empezar. Lo unico que
he escrito en el arbol es **esta seccion 14**, que el dev commiteará. Las 12
camaras de mutacion quedan **restauradas y verificadas 4/4 por SHA256**; las 4
`cmp_*` de la comparativa quedan, por diseno, con la mutacion puesta (son de un
solo uso y asi se nombran).

---

# 15. RONDA 8 DEL `mutation-auditor` (veredicto final del ciclo)

Medido sobre `9b68cc2`, en copia de `%TEMP%`, con repo git **propio y
desechable** por camara. **43 mutantes**: los 37 de la vista en el subconjunto
dirigido (#1, #2, #3, #14, #18), los de render en los tests que **ejecutan** la
vista, y los de la premisa del #16 en su test. **0 ROTO** sobre lo medido, **0
ERROR_DE_SONDA**, y un `ROTO` declarado y descartado (15.0.4).

## 15.0 EL ARNES, Y SUS CUATRO DEFECTOS PROPIOS (declarados antes de los numeros)

Los declaro primero porque **cuatro** mediciones de este informe se apoyaron en
que no los hubiera, y dos de ellas habrían dado un numero falso:

1. **UN VERDE QUE NO SE MIDIO, Y CASI CUENTA COMO MEDICION.** `Z1` salio
   "PERMITIDO" en **1,4 s**. La suite completa tarda **118,7 s**. Motivo: mi
   runner recibia `tests=[]` para `Z1` y lo leia como "cero tests", o sea como
   verde automatico. Ahora `tests=[]` significa "suite COMPLETA", y `Z1` se
   remidio: **118,7 s, verde, octava medicion**. Un verde sobre un mutante que
   no se ejecuto no cuenta, y es el mismo error que motivo las 48 muertes falsas
   de la ronda 7.
2. **UNA EXCEPCION AL IMPRIMIR DEJO LA CAMARA SUCIA.** La Trampa #16 (consola
   cp1252) revento el `print` del literal de la asercion de `PREMISA_S1` con un
   `UnicodeEncodeError` **despues** de mutar y **antes** de restaurar. La tanda
   siguiente arranco con `run_tests.py` todavia mutado y su CONTROL salio rojo
   con `precondicion rota: la DB de la prueba tiene que clasificar svchost...`.
   Lo detecto la guarda de "CONTROL rojo -> ABORTO" sola, que es exactamente
   para lo que existe; el bucle muta->mide->restaura va ahora en un
   `try/finally`, y la camara se restauro copiando el fichero del repo y
   verificandolo por SHA256 antes de reanudar.
3. **`G_ELSE` NO ES LA FORMA DE LA TABLA, y lo digo.** La forma "la seccion va
   en el `else`" exige reescribir el `if` entero; la que monte es
   `if not pack.is_gaming: return` seguido de `if True:` delante de la seccion.
   **MUERE por A1**, que es lo que importa, pero el literal que imprime es
   `'True'` y no el `'not pack.is_gaming'` de la tabla de la 11.2. No lea las dos
   cadenas como la misma medicion.
4. **UN ROTO DECLARADO Y DESCARTADO.** `WITH_GATE` (un `with` cuyo gestor se
   decide por el pack) salio **`ROTO`**: mi patron no sangro la seccion y el
   `IndentationError` lo mato por un motivo ajeno. No cuenta como muerte ni
   como supervivencia. Y ademas lo **descarto por el fondo**: un `with` con
   `nullcontext` contra `suppress` **no deja de construir** nada, o sea que no
   es un gate y su hipotetico superviviente habria sido un equivalente. No es un
   hallazgo que se pueda reportar en ninguno de los dos sentidos.

Ademas, y como en la ronda 7: los **43 patrones se autocomprobaron en memoria**
antes de gastar una sola corrida (los 43 compilan y cambian el SHA), `ERROR_DE_
SONDA` si un patron no aplica el numero exacto de reemplazos, `ROTO` si la
primera excepcion es de las seis que invalidan una muerte, restauracion
verificada por SHA256, `PYTHONDONTWRITEBYTECODE=1` y purga de `__pycache__`
antes de cada corrida. La camara lleva `git init` propio: sin `alternates`, sin
`remote`, y `rev-parse --git-dir` **sin `GIT_DIR`** devuelve `.git` (el suyo).
Sin esto la prueba de git de la suite cairia en
`%LOCALAPPDATA%\woptimizer_git\.git`, que es **el repo real**.

## 15.1 EL TECHO (a): CUBRE EL CASO QUE FALTABA **POR SU MOTIVO**

No me crei el motivo: lo medi sobre el AST de cada mutante, leyendo el padre
DIRECTO de la casilla y la cadena real que A1b recorre (`_CUERPO` en
`run_tests.py:14462`).

| Mutante | padre DIRECTO de la casilla | A1b se para en | camino real | gate antecesor? |
|---|---|---|---|---|
| `MAP_LAMBDA_FN` | `Assign` | `FunctionDef` (`_caja`) | `Assign <- _caja <- _render_pack_card` | **no** |
| `MAP_LAMBDA` | **`Lambda`** | `Lambda` | `Lambda <- Assign <- _render_pack_card` | **no** |
| `LISTA_LAMBDA_APLICADA` | **`Lambda`** | `Lambda` | `Lambda <- Call <- ListComp <- Assign <- _render_pack_card` | **no** |
| `MAP_LAMBDA_2` | `IfExp` | `Lambda` | `IfExp <- Lambda <- Assign <- ...` | **si** |

**Las dos afirmaciones del dev sobre el (a) se sostienen, y la segunda es
ci Certainada:** el `ListComp` que alimenta la casilla esta **en la cadena de
ancestros**, una sola pieza por encima del `Lambda` (`Lambda <- Call <-
ListComp`), y A1b **no llega a preguntarlo** porque la busqueda se para en el
`Lambda`, que es `_CUERPO`. Y el gate -- el `IfExp` del `iter` de la
comprehension -- **no le es antecesor**: es un subarbol **hermano**, igual que
en las otras dos. El invariante que queda declarado, "ninguna pieza del acordeon
se construye dentro de un `Lambda`", es correcto, y **la lista de palabras no se
ha ensanchado**: el texto nombra el TERCER caso, que era el unico que no caia
ya por el motivo de los otros dos.

| Mutante | Veredicto | Asercion |
|---|---|---|
| `MAP_LAMBDA_FN` | **PERMITIDO** (techo a, "la seccion extraida a un `def`") | -- |
| `MAP_LAMBDA` | **PERMITIDO** (techo a, **por el motivo**) | -- |
| `LISTA_LAMBDA_APLICADA` | **PERMITIDO** (techo a, **por el motivo**) | -- |
| `MAP_LAMBDA_2` | **MUERE** | A1 `run_tests.py:14326` -- `una casilla de categoria (CTkCheckBox) (L438) cuelga de una condicion en L438: 'pack.is_gaming'` |

## 15.2 EL TECHO (f): LOS NUMEROS DEL DEV, REPRODUCIDOS CIFRA POR CIFRA

Con **mi** ejecutor de casillas **CONSTRUIDAS** (no `ast`), tres categorias,
extrayendo la seccion entera y ejecutandola contra un `ctk` de mentira:

| Vista | gaming | normal | |
|---|---|---|---|
| repo sin mutar | **6** | **6** | referencia |
| `COSMETICA_FOR` | **9** | **6** | la fila sale **duplicada** |
| `COSMETICA_IF` | **6** | **3** | el normal **pierde** las 3 de "arrancar" |
| `LC` | 6 | **3** | |
| `LC_LIMPIA` | 6 | 6 | equivalente |
| `FP_COLUMNAS` | 6 | 6 | sonda legitima |
| `FP_DOS_TANDAS` | **9** | **9** | sonda legitima |

Coincide **cifra por cifra** con lo que el dev escribe en `run_tests.py:14675`
("repo 6/6, `COSMETICA_FOR` 9/6, `COSMETICA_IF` 6/3") y en `:14697-14698`. Las
dos formas mueren y **las dos sondas legitimas siguen permitidas**: el techo (f)
**no se ha endurecido**.

| Mutante | Veredicto | Asercion |
|---|---|---|
| `COSMETICA_FOR` | **MUERE** | A1b `run_tests.py:14530` -- `la casilla de L442 la dibuja el bucle de L438, ...` |
| `COSMETICA_IF` | **MUERE** | A1 `run_tests.py:14326` -- `... (L442) cuelga de una condicion en L438: '(2 if pack.is_gaming else 1) == 2'` |
| `FP_COLUMNAS` | **PERMITIDO** | -- |
| `FP_DOS_TANDAS` | **PERMITIDO** | -- |

**Una salvedad honesta sobre `FP_DOS_TANDAS`, que NO es una falsedad.** Construye
**9/9**: el `for` exterior **si duplica** la fila (3 -> 6 en esa tanda, 6 -> 9 en
total). Lo que no hace es decidirlo por el pack, y la invariante que el (f)
declara -- "lo que el pack no puede decidir es la CANTIDAD de casillas" -- aguanta,
por eso la sonda es legitima. Pero el texto la presenta como "puede decidir
cuantos BUCLES la envuelven", y un `for _t in (False, True):` que duplica una
fila incondicionalmente no lo escribe nadie: la sonda **prueba que la regla no
come codigo legitimo**, y su realismo como codigo real es bajo. `FP_COLUMNAS` si
es una forma de produccion plausible y tambien pasa.

## 15.3 LA REGRESION: NI UNA MUERTE PERDIDA

Las doce de la 11.2, los cinco saltos, la familia LC, los dos del techo (f),
`GG2` y las dos mitades de la premisa mueren **cada una por su asercion**:

| Forma | Asercion que la mato |
|---|---|
| `U1` / `U1_AND` | `14326` -- `el espejo (def create_command) (L403) cuelga de una condicion en L336` |
| `G_VAR` / `G_ALIAS` | `14326` -- `'gaming'` / `'p.is_gaming'` (L337) |
| `G_GETATTR` | `14326` -- `"getattr(pack, 'is_gaming', False)"` |
| `G_PRED` | `14326` -- `"pack.id != 'gaming'"` |
| `G_HELPER` | `14326` -- `'self._es_gaming(pack)'` (L339) |
| `G_OR` / `G_ISTRUE` | `14326` -- `'pack.is_gaming or pack.is_favorite'` / `'pack.is_gaming is True'` |
| `G_ELSE` | `14326` -- `'True'` (ver 15.0.3: **mi** forma, no la de la tabla) |
| `G_LISTA` | `14530` (A1b) |
| `G_GUARD2` | `14599` (A2) -- `_seccion_acordeon (L341) ... vuelve en L343 si se cumple 'not pack.is_gaming'` |
| `M1` / `M2` / `M3B` | `14530` (A1b) |
| `M10` (cuatro saltos) / `C5` (cinco) | `14530` (A1b) |
| `LC` / `LC_ANIDADA` / `LC_SOLO_UM` | `14530` (A1b) |
| `LC_LIMPIA` | **PERMITIDO** (equivalente: 6/6, medido) |
| `COSMETICA_FOR` | `14530` |
| `COSMETICA_IF` | `14326` |
| `GG2` | `14599` (A2) -- `_seccion_acordeon2 (L341)` |
| `PREMISA` (el snapshot pasa a ROJO) | `15393` -- `preCONDICION ROTA: este test solo mide la barrera de categoria si el snapshot y la DB DISCREPAN` |
| `PREMISA_S1` (la DB pasa a VERDE) | `15379` -- `precondicion rota: la DB de la prueba tiene que clasificar svchost como <ROJO>` |
| `Z1` | **PERMITIDO**, suite completa, **118,7 s**, **octava** medicion |
| `D_FP1` / `D_FP2` | **PERMITIDOS** (las dos sondas legitimas de la 11.2) |

**Correccion a la tabla de la 14.5, y es mia:** decia que las dos mitades de la
premisa mueren "con `preCONDICION ROTA` L15393". **No es asi:** la primera muere
en `15393` y la segunda en **`15379`**, que es OTRA asercion y con otro literal
("precondicion rota", en minusculas, la de la DB de la prueba). Las dos mueren,
que es lo que importa, pero por dos aserciones distintas. Y anadi una tercera
sonda de control, `PREMISA_PID` (cambia solo un PID y **no toca** la premisa):
**PERMITIDO**. Eso es lo que demuestra que las dos muertes vienen de las
aserciones de premisa y no de "cualquier edicion de esas lineas mata".

## 15.4 LO QUE SI ENCONTRE: UN (a) DE VERDAD, Y UN (b) CON EL TEXTO TORCIDO

### (a) `ASSERT_GATE`: VIVE, NO ES EQUIVALENTE, Y NO ESTA EN NINGUN TECHO

Un `assert pack.is_gaming` delante de la seccion entera
(`pack_manager_view.py`, justo antes del comentario
`# --- SECCION ACORDEON CATEGORIAS`). **`ast.Assert` no esta en `_CONDICIONALES`**
(`run_tests.py:14252`: `ast.If, ast.IfExp, ast.While, ast.Try, ast.Match`), y el
`assert` es un statement **HERMANO** del bucle, no un antecesor: no lo ve A1, no
lo ve A1b (mira solo los `iter` de los bucles) y no lo ve A2 (mira `return`).

| Medicion | Resultado |
|---|---|
| Suite dirigida (#1, #2, #3, #14, #18) | **PERMITIDO**, rc=0 |
| **Suite con los tests que EJECUTAN el render** (`test_headless_ui`, `test_main_window_navigation_transitions`, `test_dashboard_favorite_grid_adaptive_contracts`) | **PERMITIDO**, rc=0, y `test_headless_ui` reporta `OK` explicitamente |
| No-equivalencia, con mi ejecutor de casillas construidas | repo **6/6**; con el `assert`, gaming **6** y **normal `AssertionError`**: la seccion no se dibuja **y el render revienta** |

**No es equivalente y no lo cubre ningun techo (a)-(f):** no es una llamada
gateada (a), no es `.pack()`/`.grid()`/`.destroy()` (b), (c), no es una lista
filtrada ni una llamada (d), no es un guard clause (e) y no es un bucle cuya
cantidad decida el pack (f). Es un **(a) de manual**.

**Severidad: MEDIA.** Es la misma clase de dano que el invariante del ciclo --un
pack normal sin donde elegir categorias-- y **no toca la barrera anti-brick**:
no hay ningun mutante vivo en `gaming_service.py`, `process_service.py` ni en la
barrera de categoria. Y dos matices honestos, en las dos direcciones:

* **A favor de que es real:** con `python -O` el `assert` desaparece y la seccion
  no se dibuja **en silencio**, que es peor que reventar. Y la conversion
  `if pack.is_gaming: <seccion>` -> `assert pack.is_gaming; <seccion>` es
  exactamente el gate que **este ciclo borro** (`pack_manager_view.py:338` lo
  recuerda), reintroducido con otra sintaxis.
* **En contra de que es realista:** medido con `grep`, **`src/` no tiene ni un solo
  `assert`** hoy. No es una forma ya presente en el producto, asi que no es un
  refactor que se haya hecho mal: es un "que pasaria si alguien escribiera uno".

**El arreglo mas barato es una entrada:** `ast.Assert` en `_CONDICIONALES`
(`run_tests.py:14252`). **Y la salvedad que hay que dejar escrita al hacerlo:**
`_CONDICIONALES` es una **lista blanca de tipos de nodo**, asi que A1 sigue
siendo, estructuralmente, un test de la FORMA del gate --justo lo que las rondas
4 y 5 cerraron-- y anadir `ast.Assert` tapa esta instancia, no la clase. Si se
quiere el invariante entero ("ninguna sentencia entre el ancla y la construccion
puede abortarla"), es un cambio mas grande y de otro tipo. Lo dejo dicho para que
nadie lea la entrada nueva como una lista completa.

### (b) El eje (e) esta declarado pero su TEXTO es mas estrecho que el eje

Dos formas del **mismo** eje que el techo (e) declara sobreviven, y el texto solo
nombra una:

| Mutante | Forma | Veredicto |
|---|---|---|
| `GUARD_METODO` | `if not self._es_gaming(pack): return` al inicio de la seccion extraida | **PERMITIDO** |
| `ALIAS_GUARD` | `_g = pack.is_gaming` + `if not _g: return`, idem | **PERMITIDO** |

Las dos son el mismo motivo que el (e) declara: **A2 mira la LECTURA DIRECTA de
la condicion, no el valor del que viene** (`run_tests.py:14599`). Lo que pasa es
que el texto del (e) (`run_tests.py:14656-14665`) nombra **un** exponente, "un
atributo que pone otra funcion--`self._flag = p.is_gaming`--", y el eje real
tiene **tres**: ese, un **alias local** y un **predicado en un metodo**. Los dos
ultimos estan vivos y sin nombrar.

**Lo clasifico como (b) con el texto torcido, y por que:** el eje esta
declarado, con su motivo y con su precio explicito, y la ronda 5 ya clasifico
`GG2_METODO` (el predicado en un metodo) como "(e), el mismo eje que el techo
(e) literal". No es un agujero nuevo del invariante: es el techo **diciendo
menos de lo que cubre**. Y **lo digo con las dos lecturas, para que el
arqueto decida con el dato y no con mi criterio**: si el (e) se lee por su
**texto** ("un atributo que pone otra funcion"), `ALIAS_GUARD` y `GUARD_METODO`
son dos (a) mas; si se lee por su **motivo** (que es como esta escrito el
resto del techo), son (b) con el texto incompleto. Con una palabra en el (e) --
"cualquier lectura indirecta: un atributo de otra funcion, un alias local o un
predicado en un metodo" -- la ambiguedad desaparece y las tres quedan nombradas.

**Ademas, una afirmacion del dev que no se reproduce:** el encargo y la 14.5 dan
`ALIAS_GUARD` por **MUERTO en `L14599`**. Con el literal mas natural de ese
nombre --un guard clause de Gaming **aliaseado**-- **sobrevive**. El dev ya
anticipo esta objeccion ("puede que las mutaciones que mato no sean identicas a
las tuyas, aunque sean de la misma forma") y aqui no se trata de la forma: se
trata de que la forma que da nombre al mutante **esta viva**, y lo que el
apartado 14.5 registra como muerte es otra cosa. Con `GG2` si se reproduce
(`_seccion_acordeon2`, `if not pack.is_gaming: return`, `L14599`).

## 15.5 LAS FORMAS NUEVAS QUE INVENTE (encargo, punto 5)

| Forma | Que es | Veredicto |
|---|---|---|
| `LC_DOS_GENERADORES` | la casilla en una comprehension de **dos** generadores, con el gate en el `iter` del **segundo** | **MUERE** `14530` |
| `DICTCOMP_CASILLA` | la casilla construida como **valor** de una `DictComp` con el `iter` gateado | **MUERE** `14530` |
| `LC_IFS_SEGUNDO` | el gate como `if` del **segundo** generador (los dos anteriores lo ponian en el `iter`) | **MUERE** `14530` |
| `ASSERT_GATE` | `assert pack.is_gaming` delante de la seccion | **PERMITIDO** -- ver 15.4 |
| `ALIAS_GUARD` | guard clause con **alias local** | **PERMITIDO** -- ver 15.4 |
| `GUARD_METODO` | guard clause con el predicado en un metodo | **PERMITIDO** -- ver 15.4 |
| `WITH_GATE` | `with` cuyo gestor se decide por el pack | **ROTO, descartado** (15.0.4) |

Las tres primeras confirman que la resolucion de "todos los bucles que envuelven
la casilla" es **realmente recursiva y really transversal**: mira los `iter` Y
los `ifs` de **todos** los generadores, y atraviesa el `DictComp` de una casilla
construida en su valor. **No se ha abierto ningun hueco nuevo en el (f)** mas
alla del `assert`.

## 15.6 LO DOCUMENTAL: LAS AFIRMACIONES DEL DEV, REPRODUCIDAS CON `ast`

| Afirmacion | Veredicto |
|---|---|
| Las seis cifras `14726/14835/14862` (defs) y `14742/14848/14875` (asignaciones) | **CIERTO.** Los tres `def` caen donde dice; con `ast` hay **exactamente tres** asignaciones a `svc._patrones_de_categoria` y **no hay una cuarta** |
| El marcador `L15732` | **CIERTO.** `validate_docs.py` lo **deriva** (`stmt.lineno`, `validate_docs.py:558`) e imprime `marcador en run_tests.py:15732`; la linea es la frontera headless |
| `+57` en los dos sitios de la seccion 13 | **CIERTO** (`mutation-report.md:1574` y `:1752`), y `:1577` deja escrito que el "+39" era falso |
| "los seis" en los tres sitios | **CIERTO**: `run_tests.py:14612` ("Las seis se MIDIERON vivas"), `:14694` ("Ninguno de los seis"), y `testing-guide.md` fila 107 ("las seis formas" / "Ninguno de los seis") |
| Las cifras del docstring del test #18 (`run_tests.py:15486-15488`) | **CIERTO**: cita `14742`/`14848`/`14875`, y las de la ronda 4 (`14318/14414/14441`) **ya no estan** |
| `validate_docs.py` **119 OK / 0 FAIL**, rc=0 | **CIERTO** |
| `verify_ui_syntax.py` 9/9 y suite en 123, reparto 95+28 | **CIERTO** (9 modulos, `123 tests definidos = 123 invocados`, `95 backend + 28 headless`) |
| Cero ficheros bajo `src/` | **CIERTO**: `git diff 5f96671 HEAD -- src/` vacio |

**Busqueda de falsedades NUEVAS, incluida la que pudo introducing el
ensanchamiento del techo al mover lineas: CERO.** Recorri `run_tests.py`,
`docs/ai/testing-guide.md`, `STATUS.md`, `AGENTS.md`, `README.md`,
`validate_docs.py`, los dos changelogs, `tasks.md` y `proposal.md` buscando las
cifras caducadas de las rondas 4 a 7 (`14688 14797 14824 14704 14810 14837
15694 15637 14318 14414 14441 14631 14740 14667`). **Solo aparecen tres, todas
en `testing-guide.md:166`, y las tres son las de la ronda 4 citadas
correctamente como las FALSAS que se corrigieron** ("las cifras de la ronda 4
(`14631 / 14740 / 14667`) eran falsas en las tres"). O sea que la cita cuelga y es
una cita. Ninguna otra.

**Dos cosas que NO cuento como falsedad, y por que lo digo:**

1. `mutation-report.md:1970-1971` (seccion **14**, mia) afirma que "su linea 125
   ya dice `(marcador en run_tests.py:15694)`". Hoy `validate_docs.py` dice
   `15732`. Es el **registro historico** de una medicion hecha sobre `9ebeabc`,
   asi que **no hay que reescribirlo** (reescribir un informe fechado seria
   falsear la historia), pero **no se lea en presente**: es la unica cita del
   informe que envejece con el fichero, y el dev hizo bien en no tocarla.
2. Los dos changelogs siguen en `CYCLE-050`: TASK-063 **no tiene entrada** todavia.
   No es falsedad porque el ciclo sigue abierto (`openspec/changes/2026-10-03-
   pack-seleccion-por-categoria` sin archivar) y `validate_docs.py` da 0 FAIL.

## 15.7 AISLAMIENTO

Camara `%TEMP%\wopt_mut_r8-b40094c7`: copia con
`shutil.copytree(ignore_patterns(".git", "*.pyc", "__pycache__"))` -- **`.git`
exacto**, no `.git*`, para no comerse el `.gitignore` (que es lo que produjo las
48 muertes falsas de la ronda 7) y comprobados `.git` ausente y `.gitignore`
presente antes de hacer nada. `git init` + `add` + `commit` propios, sin
`remote` y sin `alternates`, y `rev-parse --git-dir` **sin `GIT_DIR`** devuelve
`.git`. La VFS de Nextcloud no deja leer los `.pyc` del repo: excluidos de la
copia y `PYTHONDONTWRITEBYTECODE=1` en cada corrida.

**Repo real: NO TOCADO.** `git log --oneline -1` = `9b68cc2`, `git status
--porcelain` vacio, `git diff --stat` y `git diff --cached --stat` vacios,
`rev-parse --git-dir` = `%LOCALAPPDATA%\woptimizer_git\.git`. Camara
**restaurada y verificada por SHA256** en los tres ficheros mutados
(`run_tests.py`, `pack_manager_view.py`, `gaming_service.py`) y `git status
--porcelain` sobre ellos vacio. Lo unico escrito en el arbol es **esta seccion
15**, que el dev commiteara.

## 15.8 VEREDICTO DE LA RONDA 8

**FAIL, y por UNA cosa, y no es una muerte perdida.**

- **(a) Fallo real de cobertura: UNO, `ASSERT_GATE`.** Vive, **no es equivalente**
  (el pack normal se queda sin seccion **y el render revienta**), no lo caza ni
  el test dirigido **ni los tests que ejecutan la vista**, y **no esta en ninguno
  de los seis techos**. Se cierra con `ast.Assert` en `_CONDICIONALES`
  (`run_tests.py:14252`), con la salvedad de 15.4 sobre lo que esa lista es y no
  es. Severidad **media**, y **no toca la barrera anti-brick**.
- **(b) Techo declarado y medido: SEIS, y los dos que se tocaron esta ronda
  aguantan.** El (a) cubre el caso nuevo **por su motivo**, verificado sobre el
  AST y no por la palabra; el (f) dice la verdad sobre su tamano (6/6, 9/6, 6/3,
  reproducidos) y **sus dos sondas legitimas siguen pasando**, o sea que no se ha
  endurecido. Y conteste a la pregunta del encargo sobre `ALIAS_GUARD`: **vive**,
  con el texto del (e) mas estrecho que su eje (15.4).
- **(c) Texto documental: CERO.** Las seis cifras, el marcador, el `+57`, los
  tres "los seis", el docstring del #18 y el 119/0 son ciertos, y el barrido de
  cifras caducadas en documentos vivos no encuentra **ninguna** cita colgando.

**Y lo mas importante de la ronda, en una linea: el arreglo del dev NO ha
perdido ninguna muerte y las tres falsedades de la ronda 7 estan de verdad
corregidas.** Las doce de la 11.2, los cinco saltos, la familia LC, los dos del
techo (f), `GG2` y las dos mitades de la premisa siguen muriendo cada una por
su asercion; `Z1` sigue verde por octava vez; y `FP_COLUMNAS`, `FP_DOS_TANDAS`,
`LC_LIMPIA`, `D_FP1` y `D_FP2` siguen permittingose. Tras ocho rondas sobre la
misma asercion, lo que queda **no es un agujero de la barrera**: es **una
entrada en una lista** y **una frase en el techo (e)**.

Ese es el veredicto, sin rodeos: el ciclo **no puede cerrar en esta ronda**, pero
esta vez lo que falta es lo mas barato que se ha encontrado en ocho rondas, y
las dos cosas que quedan son texto mas un token.

---

# 16. RONDA 10 DEL `mutation-auditor`: EL INVARIANTE POR EFECTO (veredicto del ciclo)

**Commit auditado:** `41b2f88` (registro) sobre `9433985` (T-9, el test de efecto). El unico commit
que toca `src/` sigue siendo `e0f20db`; verificado con `git show --name-only`, **cero ficheros bajo
`src/`** en toda la cadena.

**Que se audita.** Diez rondas sobre la misma asercion, y en la decima el objeto cambio: el invariante
dejo de afirmarse por la FORMA del codigo y paso a afirmarse por su **EFECTO** (la vista real montada
headless, contando casillas por sus etiquetas). La pregunta de siempre: *¿el test se entera si el
codigo esta mal?*

**Metodo:** 20 mutantes, cada uno aplicado sobre una copia en `%TEMP%`, uno a uno. Por mutante se
corrieron **las dos cosas**: el 3-E **dirigido** (para ver su veredicto sin que otro test se adelante)
y la **suite completa** de 124 (para saber si la muerte se pierde en otro sitio). `PYTHONDONTWRITEBYTECODE=1`
en todas las corridas, `__pycache__` = **0** medido al final en las seis camaras. Nada reparado.

---

## 16.0 VEREDICTO

# FAIL

**Y el FAIL es de un tipo que no se ha visto en este ciclo: no es una forma de gate nueva.** El
diagnostico de fondo (alcanzabilidad, Rice) queda **vindicado por medicion**: las diez familias de las
nueve rondas y los cuatro mutantes de T-9 mueren, cada uno **por la asercion del 3-E que dice
comprobar su cosa**. Lo que queda son **dos formas en que las dos direcciones de las casillas estan
intercambiadas o desaparecidas mientras el 3-E sigue en verde**, y ninguna de las dos esta en un techo
declarado.

| Severidad | Id | Que se rompe si el codigo se rompe asi | Medido |
|---|---|---|---|
| 🔴 **ALTA** | **`W_VAR_CRUZADA`** | La casilla de ARRANCAR se cablea a la variable de APAGAR. El usuario marca "arrancar" y **se guarda como APAGAR**. **124/124 en verde** | §16.5.1 |
| 🔴 **ALTA** | **`K_CATALOGO_CORTO`** | Una categoria real se cae del catalogo: **18 -> 16 casillas** y la DB sigue clasificando `chrome.exe` en ella, o sea un proceso del usuario **sin casilla donde marcarlo**. **124/124 en verde** | §16.5.2 |
| 🟡 **BAJA** | `E_COSMETICA_IF` | `cb.grid(row=i // (2 if pack.is_gaming else 1))`: la rejilla pasa a **una casilla por fila**. Cosmético: el conteo no cambia y las 18 se ven. **124/124 en verde**, y E2 tiene razón en dejarlo pasar | §16.6 |

**Lo que esta ronda SI entrega, y es lo que decide si el cambio de enfoque valia la pena:**

| Lo que se afirmaba | Ronda 1-9 | **Ronda 10** |
|---|---|---|
| Las **diez** familias de gate sobre el 3-E | nueve vivas, una por ronda | **10/10 MUEREN por E2** |
| Los **cuatro** mutantes de T-9 | - | **4/4 MUEREN**, cada uno por su asercion (E0/E1/E2) |
| `C_ASSERT_GATE` muere por **E3**, no por un `AssertionError` crudo | - | ✅ **CIERTO, medido** |
| El fixture dibuja casillas **de verdad** | - | ✅ **9 categorias, 18 casillas, 2 tarjetas, 9/9 + 9/9** |
| Riesgo de entorno nuevo | - | ✅ **Ninguno**: `ctk.CTk()` + `withdraw()` ya se usa en **cinco** sitios preexistentes |

**Una linea:** el paso de la FORMA al EFECTO **funciono** y hay que decirlo sin rodeos, porque es la
primera vez en diez rondas que una capa mata una familia entera en vez de desplazar el borde. Lo que
impide cerrar el ciclo ya **no es la pregunta por la forma**: es que el 3-E mira **las etiquetas** y
no mira **a quien estan cableadas** ni **de donde salio el catalogo**.

---

## 16.1 EL ARNES, Y **MIS** CUATRO DEFECTOS PROPIOS (declarados antes de los numeros)

En las nueve rondas los dos actores tuvisteis fallos de sonda. Yo tuve **cuatro**, y dos de ellos
habrian producido evidencia FALSA si no los hubiera detectado:

| # | Defecto mio | Como lo detecte | Que habria pasado sin el control |
|---|---|---|---|
| **1** | **El mutante NO se aplicaba y salia verde.** Los mutantes de tipo `wrap` (los que envuelven un bloque en un `if`) no dejaban la firma `MUT r10`, y mi propio guard los rechazaba con `NO_APLICADO` | El guard propio: si la firma no queda en el fichero, `NO_APLICADO` y **no cuenta como verde ni como muerte** | Habria reportado `U1` y `U1_AND` como "vivos" sin haberlos medido nunca. Es el fallo mas caro posible |
| **2** | **El ejecutor dirigido producia una muerte falsa.** Doble `TextIOWrapper` sobre `sys.stdout` (`run_tests.py:9` ya lo envuelve) -> `ValueError: I/O operation on closed file` al salir | `clasificar` marca `ROTO` si la primera excepcion no es la del test, y el literal impreso delata el `ValueError` | `G_VAR`, `G_ALIAS` y `G_HELPER` habrían muerto "por otra cosa" y yo lo habría apuntado como muerte legitima |
| **3** | **Dos camaras quedaron MUTADAS al morir el runner.** Un `UnicodeEncodeError` de cp1252 (Trampa #16: el emoji 🟢 del mensaje) aborto el harness **entre aplicar y restaurar** | Barrido final: `MUT r10` presente en 2 de 6 camaras | Si hubiera reutilizado esas camaras, el siguiente mutante habria nacido sobre codigo ya mutado. Es el fallo de "un `run_tests.py` que quedo mutado porque una corrida revento antes de restaurar", y lo cometi yo |
| **4** | **Una sonda mia era tautologica.** Comprobei que un texto que yo acababa de escribir no se 교체ara, o sea que mi "fix" no habia hecho nada y asi lo declares como verificado | Lo vi al notar que el `SyntaxError` seguia apareciendo | Habria declarado "arreglado" un archivo intacto |

Las tres comprobaciones propias que si se hicieron, y sus resultados:

| Comprobacion | Resultado |
|---|---|
| `.git` como **FICHERO**: `shutil.copytree(ignore_patterns(".git", "*.pyc", "__pycache__", "dist", "build"))` | **0 entradas `.git`** en las 6 camaras, **`.gitignore` presente** (o sea que el comodin `.git*` no se uso: habria producido las 48 muertes falsas de la ronda 7) |
| Aislamiento con `GIT_DIR` **desechable y explicito** | `git rev-parse --git-dir` -> la camara. **Sin** `GIT_DIR`: `rc=128` y salida vacia, o sea que la camara **no puede descubrir** el repo real. `GIT_DIR` **nuevo** por camara (6) |
| **CONTROL** por camara antes de medir, y **CONTROL FINAL** despues del ultimo mutante | **6/6 `rc=0` antes**, y `rc=0 PASSED` al final en la camara `a`. Y sonda de sonda: `CTRL_PID` (cambia un PID, no toca el invariante) -> **SUITE PASSED**. Sin ese control, "verde" no significa nada |
| `EXECUTED_AFTER` + SHA256 antes/despues | `exec_after=True` y `sha distinta=True` en **los 20** mutantes |
| Restauracion | Las **6** camaras fieles a su `pristine` por SHA256, `__pycache__` = **0** |

---

## 16.2 LOS CUATRO MUTANTES DE T-9, UNO A UNO

Los cuatro mueren **por la asercion del 3-E que dice comprobar su cosa**, confirmado con el
ejecutor **dirigido** (sin que ningun otro test se adelante). `ROTO = 0`.

| Id | Que se rompe | Veredicto | Motivo literal (del 3-E dirigido) |
|---|---|---|---|
| **`G_CATALOGO_VACIO`** | `categorias_disponibles()` devuelve `[]` | ✅ **MUERE por E0** | `AssertionError: el catalogo de \`ProcessService.categorias_disponibles()\` ha vuelto vacio en este host (0 categorias). Sin el, E2 no tiene contra que comparar y este test pasaria en VERDE con el usuario sin una sola casilla que marcar.` |
| **`A_GATE_EN_LA_LLAMADA`** | `refresh_packs`: `if p_id != "gaming" and p.is_gaming:` | ✅ **MUERE por E1** | `AssertionError: la vista dibujo 1 tarjetas para 2 packs (['gaming', 'trabajo']): alguna no llego a dibujarse.` |
| **`B_LISTA_FILTRADA`** | `sorted_cats = ordenar_categorias(all_cats) if pack.is_gaming else []` | ✅ **MUERE por E2 (apagar)** | `AssertionError: E2 (apagar): tarjeta 1 (0 casillas), categoria 'Navegadores': hay 0 casilla(s) de APAGAR y 0 de ARRANCAR.` |
| **`F_MAP_LAMBDA`** | `map`+`lambda` gateado en la 2a tanda (arrancar) | ✅ **MUERE por E2 (arrancar)** | `AssertionError: E2 (arrancar): tarjeta 1 (9 casillas), categoria 'Navegadores': hay 1 casilla(s) de APAGAR y 0 de ARRANCAR.` |
| **`H_RENOMBRAR`** | `" (arrancar)"` -> `" (arrancar mas tarde)"` | ✅ **MUERE por E2 (arrancar)** | `AssertionError: E2 (arrancar): tarjeta 0 (18 casillas), ... hay 1 casilla(s) de APAGAR y 0 de ARRANCAR.` |
| **`C_ASSERT_GATE`** | `assert pack.is_gaming` delante de la seccion | ✅ **MUERE por E3** | `AssertionError: E3: la vista no se pudo construir: AssertionError: . El invariante de TASK-063 es que el catalogo se ofrezca para TODO pack, y una vista que no llega a construirse lo incumple entero: revienta al MONTAR, no despues` |
| **`G_CATALOGO_APLICA`** | el catalogo se filtra por las marcadas **en el pack de Gaming** | ✅ **MUERE por E2 (apagar)** | `AssertionError: E2 (apagar): tarjeta 0 (10 casillas), categoria 'Media y Streaming': hay 0 casilla(s) de APAGAR y 0 de ARRANCAR.` |

### 16.2.1 `C_ASSERT_GATE` por E3, que es lo que se pedia comprobar

El encargo pedia que este mutante muera **por E3** y no por el `AssertionError` sin cualificar. **Es
cierto, y se ve en el propio literal**: el mensaje empieza por `E3: la vista no se pudo construir` y
**conserva el motivo de dentro** (`AssertionError:`) como causa. El `try/except` de `run_tests.py:15730-15739`
hace su trabajo: sin el, la suite abortaria con un `AssertionError` crudo en `_render_pack_card` y
nadie leeria **que** invariante esta roto.

**Un matiz honesto sobre E3, y es de rigor, no de cortesia:** en la **suite completa**, `C_ASSERT_GATE`
lo mata **antes** la entrada `ast.Assert` de `_CONDICIONALES` (el `A3` que anadio `c3ced1a`), con el
literal *"la sentencia de L346 ('assert pack.is_gaming') ABORTA si se cumple algo que depende de si el
pack es el de Gaming"*. O sea: **las dos capas lo matan, y en la suite gana la estatica** porque `3-E`
es la **ultima** llamada del `__main__` (`run_tests.py:16007`). E3 no es redundante, pero **tampoco es
la primera red** para esta forma.

---

## 16.3 LAS DIEZ FAMILIAS DE LAS NUEVE RONDAS, SOBRE EL 3-E

La pregunta que decide el cierre. **Las diez mueren, las diez por E2.** Cada una aplicada como la
escribiria un desarrollador: la seccion entera (118 lineas, casillas incluidas) envuelta en la
condicion.

| Familia | Forma | Veredicto | Motivo literal (3-E dirigido) |
|---|---|---|---|
| **U1** | `if pack.is_gaming:` | ✅ **MUERE** | `E2 (apagar): tarjeta 1 (0 casillas) ... hay 0 casilla(s) de APAGAR y 0 de ARRANCAR` |
| **U1_AND** | `if pack.is_gaming and pack.default_action == "kill":` | ✅ **MUERE** | el mismo literal |
| **G_VAR** | `gaming = pack.is_gaming` + `if gaming:` | ✅ **MUERE** | el mismo literal |
| **G_ALIAS** | `p = pack` + `if p.is_gaming:` | ✅ **MUERE** | el mismo literal |
| **G_GETATTR** | `if getattr(pack, "is_gaming", False):` | ✅ **MUERE** | el mismo literal |
| **G_HELPER** | `if self._es_gaming(pack):` (metodo nuevo) | ✅ **MUERE** | el mismo literal |
| **G_PRED** | `if pack.id != "gaming":` | ✅ **MUERE** | `E2 (apagar): **tarjeta 0** (0 casillas)` -- esta esconde la del **Gaming**, no la de un pack normal |
| **A_GATE_EN_LA_LLAMADA** | el gate en `refresh_packs` | ✅ **MUERE por E1** | `la vista dibujo 1 tarjetas para 2 packs` |
| **B / F / LC** | lista filtrada, `map`+`lambda`, comprehension | ✅ **MUEREN por E2** | §16.2 |
| **`C_ASSERT_GATE`** | `assert` delante | ✅ **MUERE por E3** | §16.2.1 |

**Por que esto no es "la lista siguiente":** las diez mueren por **E2**, que no mira **como** esta
escrito el codigo sino **que etiquetas hay**. Las siete primeras (gate en cualquier sintaxis) mueren
con el **mismo** literal y por la **misma** razon: la tarjeta del pack normal se queda con **0
casillas**. No hay una entrada mas en ninguna lista: un test de efecto no se cierra por dentro
porque no enumera nada.

**Y no es que el 3-E haya sustituido a la capa estatica: las dos siguen verdes y las dos hacen
trabajo.** En la suite completa, `B_LISTA_FILTRADA`, `G_CATALOGO_APLICA` y `C_ASSERT_GATE` los mata
**primero** el estatico, y `H_RENOMBRAR` los mata **solo** el 3-E (ver §16.4).

---

## 16.4 LO QUE EL 3-E APORTA QUE NADA MAS APORTA (la anti-redadura, medida)

La regla anti-redadura del dev dice: *una familia nueva solo se anade a una capa si NINGUNA regla de
la otra la mata ya*. Medida, capa por capa:

| Mutante | Estatico (#3, A1/A1b/A2/A3) | **Efecto (3-E)** | Quien es el duenno |
|---|---|---|---|
| **`H_RENOMBRAR`** (la etiqueta de arrancar cambia) | **no lo ve** | **E2 (arrancar)**, y es la **primera** asercion de la suite | **3-E, solo suyo** |
| **`A_GATE_EN_LA_LLAMADA`** (gate en `refresh_packs`) | **no lo ve** (el acordeon SI se construye) | **E1**, y es la **primera** asercion de la suite | **3-E, solo suyo** |
| `B_LISTA_FILTRADA` | A1b, la primera | E2 tambien | las dos, sin conflicto |
| `C_ASSERT_GATE` | A3, la primera | E3 tambien | las dos |
| `G_CATALOGO_VACIO` | (ver 16.4.1) | E0 | las dos |
| `E_COSMETICA_IF` | no lo ve | **no lo ve, y esta bien** | ninguna, y §16.6 lo explica |

**Es decir: la congelacion de A1/A2/A3 esta justificada por medicion.** El estatico no ve dos de las
cuatro familias de T-9 (`H_RENOMBRAR` y `A_GATE_EN_LA_LLAMADA`), y el 3-E no ve ninguna forma de
gate. Se complementan, y el desacuerdo esta medido en los dos sentidos.

### 16.4.1 E0 es correcta pero **redundante**, y eso hay que decirlo

**`run_tests.py:2511`, preexistente y de TASK-063/FIX-005, ya afirma exactamente lo mismo:**
`assert cats, "el catalogo no puede estar vacio ni con la DB cargada ni sin ella"`, dentro del helper
`categorias_disponibles_excluye_el_centinela()` que usan dos tests. O sea:

- El 3-E **sí** muere por E0 con el mutante puesto (`MUERE:E0`, medido).
- Pero en la **suite completa** la primera asercion que salta es **la de `2511`**, no la de E0. Medido:
  `AssertionError: el catalogo no puede estar vacio ni con la DB cargada ni sin ella`.
- O sea: **E0 duplica una regla que ya existia**, y la tabla de T-9 que dice "MUERE: `G_CATALOGO_VACIO`
  (E0)" es, en la suite, falsa: lo mata una asercion de antes.

**No es un fallo** (E0 es correcta, y su mensaje es mas util que el de `2511`). Pero es el unico punto
donde el 3-E **anade una asercion cuya regla ya tenia el suite**, y por la propia regla anti-redadura
del dev deberia haberse declarado. Se declara aqui.

---

## 16.5 LOS DOS SUPERVIVIENTES: LAS DIRECCIONES, NO LAS FORMAS

Ninguno es un equivalente, y los dos se miden por su **efecto en el estado guardado**, no contando
`ast` ni leyendo codigo.

### 16.5.1 🔴 `W_VAR_CRUZADA` -- el usuario pide ARRANCAR y se guarda APAGAR

**La mutacion (una palabra, `pack_manager_view.py:457`):**
`variable=arrancar_var` -> `variable=apagar_var` en la **segunda tanda** (la de arrancar).

**Lo que ve el 3-E: nada.** Las dos etiquetas siguen siendo `cat` y `cat + " (arrancar)"`, una vez
cada una. **124/124 en verde**, y el 3-E dirigido tambien (`PERMITIDO`).

**Lo que ocurre de verdad**, pulsando la casilla de "🟢 Navegadores (arrancar)" en la tarjeta de un
pack **normal**, con el `PackService` real sobre JSON temporal:

| | `target_categories` (APAGAR) | `start_categories` (ARRANCAR) | |
|---|---|---|---|
| **CONTROL** | `[]` | `['🟢 Navegadores']` | ✅ correcto |
| **`W_VAR_CRUZADA`** | **`['🟢 Navegadores']`** | **`[]`** | 🔴 **BUG** |

El usuario configura "arranca mis navegadores al entrar en el Gaming Mode" y la app **guarda que los
mate**. Peor: el `create_command` de la linea 402 resuelve el conflicto espejo con `if v_apagar.get()
== 1` **primero**, asi que la categoria queda **exclusivamente** en la lista de apagado, sin ambiguedad
posible. Y con `python -O` no cambia nada, porque aqui no hay `assert`: es un fallo de datos puro.

**Por que el 3-E no lo ve, y cual es la regla que falta:** E2 cuenta **etiquetas**
(`widget.cget("text")`). La etiqueta es el **contrato visible**; el **cableado** (`variable=`) es el
que decide que lista se persiste, y **ninguna de las dos capas lo mira**. La red estatica tampoco: A1
vigila la *construccion*, y la construccion es correcta. **El arreglo que necesita (no aplicado):** una
asercion de que las dos casillas de una misma categoria estan atadas a **variables distintas** y de
que la variable de la casilla de ARRANCAR es la que lee la rama `if v_arrancar.get() == 1` del
`create_command`. Se puede afirmarlo por comportamiento (pulsar y mirar la lista, como aqui) sin tocar
el nombre de ningun widget: **es la misma forma de test que el 3-E ya usa.**

### 16.5.2 🔴 `K_CATALOGO_CORTO` -- una categoria entera desaparece y nadie se entera

**La mutacion (`process_service.py:863`):** se descarta del catalogo una categoria **verde** real
(`cats.discard(next(c for c in cats if 'Navegadores' in c))`).

| | CONTROL | `K_CATALOGO_CORTO` |
|---|---|---|
| `len(categorias_disponibles())` | **9** | **8** |
| casillas por tarjeta | **18** | **16** |
| `_categorize("chrome.exe")` | `🟢 Navegadores` | **`🟢 Navegadores`** (la DB no cambia) |
| casilla para `🟢 Navegadores` | **si** | **NO** |

**124/124 en verde.** El usuario tiene `chrome.exe` clasificado en "🟢 Navegadores" y **no tiene ni
una casilla donde marcarlo**, ni para apagarlo ni para arrancarlo. Es exactamente el bug que el
`CHANGELOG.md` del ciclo 51 dice haber cerrado ("*el desfase sale como un proceso en 'Otros' que nadie
sabe donde marcarlo*"), reintroducido por la otra mitad.

**Por que E2 no lo ve, y aqui hay que ser preciso con el alcance:** E2 compara las casillas de la
tarjeta **contra `ps.categorias_disponibles()`**, o sea contra **la misma fuente que consume la
vista**. Sobre el contenido del catalogo, E2 es **tautologico**: si el catalogo pierde una categoria,
la vista pierde sus dos casillas y E2 ve `8/8` y `8/8` y dice que todo esta bien. E0 solo impide el
caso **vacio** (`>= 1`), no el **corto**.

> **Precision con el encargo.** Este **no** es un agujero del mismo invariante que las nueve familias:
> esas preguntan si el pack puede perder casillas, y este pregunta si el catalogo puede ser corto. E2
> cumple su palabra. El invariante de **producto** ("toda categoria que el servicio clasifica tiene
> casilla") no lo afirma **nadie** hoy, y por eso el arreglo es **una asercion nueva** (E4), no un
> relajamiento de E2. Lo que no se puede es declararlo techo, porque **no esta escrito en ningun sitio**.

---

## 16.6 `E_COSMETICA_IF`: SUPERVIVIENTE, PERO LAS DOS CAPAS TIENEN RAZON

La sonda que el dev uso para justificar que A1/A2/A3 se congelan. **La medicion no es la que se
declaro.**

| Lo que se afirmaba (T-9, linea 144) | Medido |
|---|---|
| *"el mutante `E_COSMETICA_IF` (`cb.grid(row=i // (2 if pack.is_gaming else 1), ...)`) **lo mata el techo (f) del estatico** (`run_tests.py:14716-14736`)"* | ❌ **FALSO: 124/124 en verde.** El techo (f) **no** lo mata, y el 3-E tampoco |
| *"E2 lo deja pasar **con razon**, porque esa forma cambia la **fila**, no la **cantidad**"* | ✅ **CIERTO, y verificado**: 18 casillas antes y despues, todas visibles |

**Por que el techo (f) no lo mata, y la razon importa:** el techo (f) declara, textual, *"un bucle
**ENCIMA** de la construccion cuyo **iterable** es una eleccion de `is_gaming`"*, y su propio `COSMETICA_IF`
es **`if (2 if pack.is_gaming else 1) == 2:`** (`run_tests.py:14749-14750`), o sea una condicion que
**cambia la cantidad de widgets** (`repo 6/6, COSMETICA_FOR 9/6, COSMETICA_IF 6/3`, medido alli con el
contador de casillas **construidas**). La forma que escribio el dev es **otra cosa**: el valor de
`row=`, no un gate. **O sea que el dev escribio una sonda distinta de la que el techo cubre y le
atribuyo el veredicto del techo.** Por el texto del propio techo, esa forma esta **fuera** de (f):
"lo que el pack no puede decidir es la **CANTIDAD** de casillas, y en eso esta todo".

**Veredicto: 🟡 superviviente cosmetico, y las dos capas hacen bien en dejarlo pasar.** Con la
mutacion, las 18 casillas siguen construidas, visibles y con sus dos etiquetas: solo la rejilla pasa a
una casilla por fila. Rejectarlo seria el falso positivo del otro lado. No es un (a) ni un (b): es una
**forma cosmetica que cae fuera de todo techo por la razon correcta**, y que ademas **no existe en
`src/`** (medido: la vista tiene **0** ocurrencias de `getattr`, **0** de `assert`, **0** de `or True`).

---

## 16.7 EL RIESGO REAL DE UN TEST DE EFECTO: VACIO O QUE NO LLEGA

El riesgo de un test de efecto es que no mida nada. Medido en las dos mitades.

| Pregunta | Medido |
|---|---|
| **¿Dibuja las casillas de verdad o un doble?** | **De verdad.** `ctk.CTk()` real + `withdraw()` + `PackManagerView` real + `ProcessService` real + `PackService` real sobre JSON temporal. `_etiquetas` cuenta `isinstance(widget, ctk.CTkCheckBox)` de **`CTkCheckBox`**, no de un doble |
| **¿Cuantas hay?** | **catalogo 9, 2 tarjetas (gaming + trabajo), 18 casillas por tarjeta, 9/9 de APAGAR y 9/9 de ARRANCAR.** Las cuatro cifras del dev son **ciertas** |
| **¿Puede fallar en un entorno limpio?** | **No, por tres razones medidas.** (a) `ctk.CTk()` + `withdraw()` **ya se usaba en cinco sitios preexistentes** (`run_tests.py:8353`, `:9152`, `:11387`, `:11610`, `:11722`): el 3-E no anade riesgo de entorno. (b) E0 no puede fallar en limpio: `categorias_disponibles()` mete `set(CATEGORY_ORDER)` siempre y solo descarta **un** centinela. (c) E2 no compara contra una cifra: el total sale de `2 x len(catalogo)` |
| **¿Y no se engaqa con una excepcion para evitar un rojo?** | **No.** `CTRL_PID` (cambia un PID, no toca el invariante) sale **SUITE PASSED**. Un atajo que "tampoco se dejaria pasar sin mutar" habria muerto aqui |
| **La premisa FALSA del docstring del #3, ¿se corrigio?** | ✅ **Si, y bien.** `run_tests.py:14207-14214` dice ahora, textual, *"Decia: 'el arnes no abre ventana...' **No es cierto**, y esta MEDIDO en el propio arnes"*, y cita los dos tests reales. Cerraba la invitacion a la ronda 10 |

**Un fragility que queda, 🟡 y no es un fallo:** `_etiquetas` cuenta sobre **todo** el subarbol de la
tarjeta. Si alguna vez un widget con `text=` igual a un nombre de categoria aparece en la tarjeta (una
app del pack que se llame como una categoria, una etiqueta nueva), `n_apagar` valdra **2** y E2
fallara por un motivo que no es el suyo. Es el precio de contar por etiqueta, y el mensaje de E2 dice
el motivo, que es lo que hacia falta para que aflojar sea una decision y no un reflejo.

---

## 16.8 LO DOCUMENTAL: 4 FALSEDADES, y las cuatro son (c)

### Lo que el dev afirmo y resulto cierto (comprobado, no creido)

| Afirmacion | Medido |
|---|---|
| **124 = 95 backend + 29 headless** en los **cuatro** ficheros | ✅ `STATUS.md:9`, `AGENTS.md:69`, `README.md:62`, `docs/ai/testing-guide.md:171`, los cuatro lo dicen. Derivado con `ast`: **124** `def test_*`, **124** llamadas, marcador en `run_tests.py:15949` |
| **La tabla de la guia tiene una fila por test** | ✅ `validate_docs.py`: "124 filas de test, una por test definido". Fila 124 = `test_todo_pack_ofrece_el_catalogo_completo_en_apagar_y_arrancar` |
| **`verify_ui_syntax.py` 9/9, EXITO** | ✅ 9 modulos, `rc=0` |
| **Cero cambios en `src/`** | ✅ `git show --name-only` en los 12 commits: ninguno lista un fichero bajo `src/` desde `e0f20db` |
| **`D4-bis` cerrado** | ✅ **SI, y bien**: la guia **ya no cita numeros de linea**, cita los **tres tests** (filas 108, 110, 111), y los tres son los que de verdad asignan `._patrones_de_categoria` (medido con `ast`: L14819 en `test_start_categories_arranca_y_cuenta_honestamente` = fila 108, L14925 = fila 110, L14952 = fila 111). La media falsehood de la ronda 8 esta cerrada |
| **`STATUS.md:8` dice 9 modulos** | ✅ (D5 de la ronda 8, corregido) |
| **La premisa falsa del #3 corregida** | ✅ §16.7 |

### Las cuatro que son falsas

| # | Donde | Se afirma | Medido |
|---|---|---|---|
| **C1** 🟡 | **`tasks.md:144`** y los **docstrings** de los dos tests | *"`E_COSMETICA_IF` **lo mata el techo (f)** del estatico (`run_tests.py:14716-14736`)"* | ❌ **FALSO: 124/124 en verde.** El techo (f) declara "bucle ENCIMA de la construccion cuyo **iterable** es una eleccion de `is_gaming`" y su `COSMETICA_IF` es `if (2 if pack.is_gaming else 1) == 2:`, que **cambia la cantidad**. La forma escrita en T-9 cambia el `row=` y no la cantidad: esta **fuera** de (f) por el texto del propio techo (§16.6) |
| **C2** 🟡 | **`run_tests.py:14205-14214`** y `tasks.md:121` | la cita de la premisa superada remite a `test_headless_ui` (`run_tests.py:268-288`) y `test_main_window_navigation_transitions` (`:8352-8382`) | ✅ **las dos existen y hacen lo que se dice** (`:8353` `root = ctk.CTk()` + `:8354` `withdraw()`). **Sin novedad**: no es una falsedad, lo anoto para que conste que se comprobo |
| **C3** 🟡 | **Commit `41b2f88`** | el asunto del commit de registro | ❌ **El asunto esta **corrupto**: `... y el invarianteDigest de forma a efecto`**. La palabra `digest` esta pegada a `invariante`. Es el commit que el encargo llama "el commit de registro", y su primer texto es lo que se lee en `git log` |
| **C4** 🟡 | **`STATUS.md:13`** | *"**Al dia en git (`9433985` ...)"* | ⚠️ El HEAD es **`41b2f88`**, no `9433985`. Se puede defender (el commit de codigo es el ultimo que toca `src/`), pero el panel dice "al dia en git" con un commit que **no** es el HEAD |

### 16.8.1 Cuatro **premisas del encargo** que no se sostienen contra el arbol (no son del dev)

Se declaran aparte porque no son falsedades del ciclo: son del material que llego a esta ronda, y
haberlas usado tal cual habria producido un informe con cosas que no existen.

| Lo que|Division llega | Medido |
|---|---|
| *"**La seccion 16 la escribio el dev con T-9**"* | ❌ **NO EXISTE.** `mutation-report.md` **termina en §15.8** (2380 lineas; los unicos titulos de nivel 1 son 0-15). Lo que el dev escribio con T-9 esta en **`tasks.md:115-156`** (T-9 entero) y en `rd_journal.json`. Se audito eso |
| *"El dev afirma que la mayoria las mata via **`PREMISA_PID`**, que es una asercion de premisa"* | ❌ **`PREMISA_PID` no existe en ningun `.py` del repo.** Es el nombre de un **mutante** del §15.3 de este mismo informe, y pertenece al test **#16**, no al 3-E. La unica asercion de premisa del 3-E es **E0**, y se midio (§16.2): **no es un atajo** |
| *"`GLOSARIO` en `run_tests.py:15602-15611` re-resuelve las etiquetas a cada red de seguridad"* | ❌ **`GLOSARIO` no existe** en `run_tests.py` ni en ningun documento. Las lineas 15602-15611 son `test_el_filtro_de_la_puerta_no_escribe_en_el_pack_original` y la clase `_PackServiceFalso_`. Ojo: **`_PackServiceFalso_` y `shutil_rmtree` (definidos en 15626 y 15636) no los usa nadie** en el 3-E: `shutil_rmtree` si se usa antes (`:15120`, `:15494`) |
| *"`validate_docs.py` **120 OK / 0 FAIL** (subio de 119 a 120 con la entrada del ciclo 51 en el journal)"* | ❌ **FALSO: son 119 OK / 0 FAIL.** Medido con el `GIT_DIR` real. La cadena **`120 OK` no aparece en NINGUN sitio** del repo; las nueve mediciones historicas de este informe dicen 119, y la entrada del journal no anade ninguna comprobacion nueva |

---

## 16.9 TECHOS: LO DECLARADO, MEDIDO

| Techo | Donde | Medido |
|---|---|---|
| **(a)-(f) del estatico** | `run_tests.py:14699-14765+` | Los seis siguen vivos y con su texto fiel. `E_COSMETICA_IF` cae **fuera** de (f) por su texto, no por un descuido (§16.6) |
| **El residuo (b) del 3-E: la VISIBILIDAD** | docstring del 3-E, `run_tests.py:15683-15689` | **Declarado con su precio y es cierto**: gatear el `.pack()` de `cat_body` deja las 18 **construidas**. El cierre exige identificar el boton por nombre o texto, que es el defecto que las nueve rondas quitaron, asi que **no cuenta como (a)** |
| **Los dos falsos positivos deliberados de E2** | docstring, `run_tests.py:15668-15676` | **Declarados y razonados.** (ii) es imposible mientras `process_service.py:863` descarte el centinela: **verificado**. (i) es una decision de contrato, no un descuido |
| **El gaming-only que NO rompe E2** | docstring | ✅ **Cierto**, y por el motivo que dice: la etiqueta no es `c` ni `c + " (arrancar)"` |

---

## 16.10 CONTRATO: QUE SE HA TOCADO EN EL ARBOL DEL PROYECTO

Verificado desde la raiz, **despues** de las 20 corridas y las sondas:

```
git log --oneline -1        41b2f88 docs(ciclo 51): registrar la seleccion por categoria ...
git status --porcelain      (vacio)
git diff --stat             (vacio)
git diff --cached --stat    (vacio)
git rev-parse --git-dir     C:\Users\carch\AppData\Local\woptimizer_git\.git
```

**Declaracion honesta:** las 20 corridas y todas las sondas fueron **enteras** en seis copias de
`%TEMP%`, con `GIT_DIR` **desechables y explicitos** (uno nuevo por camara) y `git init` propio, sin
`remote` ni `alternates`. No escribi, no borre y no comitee nada en
`C:/Users/carch/Nextcloud/Scripts/woptimizer`, ni siquiera para revertir: no hizo falta, porque nunca
escribi en el. `validate_docs.py` se ejecuto con el `GIT_DIR` real pero el **work tree de la camara**,
para que cualquier escritura hubiera caído ahi.

**Lo unico escrito en el arbol es esta seccion 16**, que es el artefacto de este rol. **Ningun commit.**
`src/`, `run_tests.py` y los documentos estan **exactamente** como los dejo `41b2f88`.

**Estado final de las camaras:** las **seis** restauradas y fieles a su `pristine` por SHA256, y
`__pycache__` = **0** en las seis. Dos de ellas quedaron **mutadas** al morir mi runner por el defecto
proprio #3, y lo vi y las restauré antes de volver a usarlas: es exactamente el fallo que este informe
lleva nueve rondas midiendo, y lo cometi yo.

---

## 16.11 QUE PIDE ESTA RONDA AL CICLO

Ordenado por lo que cuesta. **Ninguno de los tres primeros toca `src/`.**

| # | Accion | Severidad | Por que |
|---|---|---|---|
| 1 | **Congelar el cableado de las dos casillas** con una asercion **por comportamiento**: pulsar la casilla de ARRANCAR de una categoria en un pack normal y afirmar que lo que se guarda es `start_categories` y **no** `target_categories`. Es la misma forma que el 3-E ya usa, y es lo que mata `W_VAR_CRUZADA` | 🔴 | El usuario pide arrancar y la app guarda apagar, **en verde** |
| 2 | **Anadir la asercion de catalogo**: afirmar que `categorias_disponibles()` contiene al menos una categoria **verde** conocida, o que su tamano no es menor que el de `CATEGORY_ORDER` menos el centinela. Mata `K_CATALOGO_CORTO` | 🔴 | Un proceso del usuario sin casilla donde marcarlo, **en verde**, y es el bug que el ciclo 51 dice haber cerrado |
| 3 | **C1**: corregir la afirmacion de que el techo (f) mata `E_COSMETICA_IF`, en `tasks.md:144` y en los dos docstrings. **Decir la verdad tambien sobre lo que NO se caza** | 🟡 | Una justificacion de congelar A1/A2/A3 que esta a medias |
| 4 | **E0 declarado redundante**: o se deja como esta y **se dice** que `run_tests.py:2511` ya afirma lo mismo, o se quita E0. No es un fallo, es la unica asercion del 3-E cuya regla ya tenia el suite | 🟡 | La propia regla anti-redadura del dev |
| 5 | **C3**: el asunto de `41b2f88` lleva `invarianteDigest` pegado. No se puede reescribir un commit ya escrito sin reescribir historia; basta con que la seccion 16 lo diga | 🟡 | Es lo primero que se lee en `git log` |
| 6 | **C4**: `STATUS.md:13` dice "al dia en git (`9433985`)" con HEAD en `41b2f88` | 🟡 | El panel debe apuntar al HEAD |

**Lo que NO hace falta tocar:** `src/` (cero cambios desde `e0f20db`, y correcto), el residuo (b) de la
visibilidad (declarado, con su precio, y su cierre es otro `change-id`), los dos falsos positivos
deliberados de E2, y **A1/A2/A3**, cuya congelacion queda **confirmada por medicion** (§16.4).

---

## 16.12 EL VEREDICTO, SIN RODEOS

El paso de la **forma** al **efecto** ha hecho su trabajo, y esta es la prueba y no una opinion: **las
diez familias de las nueve rondas y los cuatro mutantes de T-9 mueren, cada uno por la asercion del
3-E que dice comprobar su cosa**, y el 3-E no se ha vuelto demasiado estricto -- la sonda legitima del
dev (`E_COSMETICA_IF`) la deja pasar, que es lo correcto. El fixture dibuja casillas de verdad, con
las cifras que el dev declaro (9, 18, 2 tarjetas), y no anade riesgo de entorno. **Nada de esto es una
`mujerte perdida` y nada de esto es el hueco de la barrera anti-brick**, que sigue con cero mutantes
vivos.

Pero **no se puede cerrar el ciclo**, por la razon mas simple que han pedido las nueve rondas: hay
**dos supervivientes rojos que no estan en ningun techo declarado**, y uno de ellos rompe
**exactamente el contrato que el mensaje de E2 dice proteger** -- *"las dos etiquetas son el CONTRATO de
las dos direcciones, una apaga, la otra arranca"*. El 3-E cuenta las etiquetas y por eso es ciego a
**a quien estan cableadas**; y compara las casillas contra **la misma fuente que las produce**, y por
eso es ciego a **que el catalogo este corto**.

La buena noticia, y es la que hace este FAIL barato: **el agujero que queda no es una forma de gate**.
No hay una ronda once. Son **dos aserciones mas** en el test que ya existe, y las dos se escriben
pulsando la casilla de verdad.
