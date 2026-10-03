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
