# Tasks — `2026-09-30-ui-hardening` (TASK-027)

Cada criterio lleva **la mutación exacta que debe morir**. Sin la línea de la
mutación, el criterio no es un criterio: es una intención.

Todos los tests van en `run_tests.py` y se registran en el bloque `__main__`
(última línea actual: 4319). Reglas del repo que aplican: la UI no importa `psutil`
ni `json`; los tests headless no abren Tcl; `print()` en ASCII puro (Trampa #16,
consola cp1252 — verificado hoy: escribir un 🟢 a stdout lanza
`UnicodeEncodeError`); emojis como escapes `\u26aa` / `\U0001F7E1`, nunca glifos
literales; prohibido `messagebox` (Trampa #14).

---

## §0 — Tests primero (los cuatro fallan hoy)

### T-27.1 `test_arranque_de_apps_no_usa_shell` (FIX-003, seguridad)

Constructor sin efectos: `svc = ProcessService.__new__(ProcessService)` (no se
carga la DB ni se toca psutil). Instrumentación en el módulo `os`, con
`setattr(os, "startfile", ...)`, y **un `subprocess.Popen` sembrado que revienta**
(`def killer(*a, **k): raise AssertionError("Popen no debe usarse")`).

| # | Entrada | Esperado | Por qué muere hoy |
|---|---|---|---|
| a | `r"C:\Windows\notepad.exe & del /q C:\"` | `started == 0`, `failed == 1`, `startfile` no llamado | hoy dispara `killer` por `Popen(shell=True)` |
| b | `C:\...\evil.bat`, `evil.ps1`, `evil.vbs`, `atajo.lnk` (ficheros reales vacíos en un temporal) | las 4 `failed`, `startfile` no llamado | hoy `Popen(shell=True)` las "arranca" y devuelve `started == 4` |
| c | `r"C:\Program Files\..\..\Windows\System32\cmd.exe"` (el destino **existe**) | `_resolver_app(...) is None` | hoy se ejecuta |
| d | `r"\\servidor\comparte\p.exe"` (UNC) | `None` | `isabs` dice `True`: sin la regla UNC se aceptaría |
| e | `"chrome.exe"` con `raices=[tmp]` y `tmp\chrome.exe` existente | devuelve `os.path.join(tmp, "chrome.exe")` | hoy se pasa el nombre pelado a `Popen` |
| f | `"no_existe_en_ningun_site.exe"` con `raices=[tmp]` | `None` | `shutil.which` tampoco lo ve, pero la aserción fija la política |
| g | `["<tmp\real.exe>", "fantasma.exe"]` con `startfile` grabador | **`(1, 1)`** y el grabador recibió **solo** `<tmp\real.exe>` | hoy devuelve **`(2, 0)`**: `Popen(shell=True)` con nombre inexistente devuelve rc=1 y **no lanza** |
| h | tras un rechazo | `logger` de `woptimizer` recibió ≥1 `warning` con el motivo | hoy no hay log de rechazo: solo el `info` de `:410` |

**Aserciones que deben morir, una a una** (esta es la tabla de mutaciones):

| Mutación | Aserción que muere | Por qué no es un `ImportError` |
|---|---|---|
| volver a `Popen(app, shell=True)` | (a) | el `killer` se sustituye por la aserción de `started`/`failed` |
| `Popen([app], shell=False)` en vez de `_resolver_app` | (c), (d) | `isabs` es `True` en los dos: la aserción `is None` falla |
| quitar la regla UNC | (d) | la aserción `is None` falla |
| borrar la regla 5 (contención) | (c) | con `commonpath` sobre la ruta cruda el resultado es `True` (medido) |
| borrar la normalización previa a la contención | (c) | ídem: el falso positivo de `commonpath` deja pasar `cmd.exe` |
| borrar la lista blanca de extensiones | (b) | 4 `failed` esperados vs `4` `started` |
| resolver el nombre pelado con `shutil.which` | (e), (f) | la aserción compara la ruta absoluta exacta, no un bool |
| `started += 1` antes del `try` / antes de validar | (g) | `(1, 1)` vs `(2, 0)` |
| `except` que se traga el motivo sin log | (h) | el handler del test cuenta 0 `warning` |

### T-27.2 `test_el_gestor_guarda_la_ruta_absoluta` (FIX-003, escritor)

`ProcessManagerView.__new__(ProcessManagerView)` con `grouped_processes` como dict
plano, `checkboxes` con `{"chrome": _Casilla(True)}`, `pack_var` con `get()`,
`status_label` como grabador con `configure`, y un `pack_service` grabador
(`get_all_packs` devuelve un `Pack` real; `save()` cuenta).

- Con `exe_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"` y
  `full_name = "chrome.exe"` → lo que se guarda en `pack.apps` es **la ruta
  absoluta**, no `"chrome.exe"`.
- Con `exe_path = ""` → se guarda `full_name` (degradación documentada) y `save()`
  se llama una vez.

**Mutaciones que deben morir:** volver a `procs[0].full_name` (guarda el nombre);
usar `procs[0].name` (que es el nombre *sin* extensión, `process_service.py:244`);
guardar la ruta sin comprobar `if not in apps` (el test lo detecta por el `len` del
duplicado); **no** degradar cuando `exe_path` está vacío (revienta con el
`AttributeError` del `None`, y por eso el caso está explícito en el test).

### T-27.3 `test_orden_de_categorias_no_es_alfabetico` (FIX-004)

`from woptimizer.config import ordenar_categorias, CATEGORY_ORDER` — sin Tk.

- Entrada barajada (barajada con una semilla fija, no con `set`, que en CPython
  tiene orden estable y haría la prueba frágil).
- `salida[:n] == [c for c in CATEGORY_ORDER if c in entrada]` y
  `salida != sorted(entrada)`.
- Una categoría **fuera** de `CATEGORY_ORDER` al principio de la entrada: sale al
  final, y las tres desconocidas conservan su orden relativo.
- Guarda estática con `ast` sobre los **dos** ficheros: prohibido `sorted(` **sin
  `key=`** cuyo argumento mencione `cat` (sin distinguir mayúsculas). Deja pasar
  `sorted(categories[cat], key=...)` (`:177`, legítimo) y `sorted(k for k ...)` (`:277`).

**Mutaciones que deben morir:** la identidad (`return list(cats)`) → la entrada
barajada no vuelve barajada; `sorted(...)` → ⚪ sale primero (medido) y la
aserción `!= sorted` falla; el centinela 999 → 99999 → las desconocidas siguen al
final pero la guarda estática... no: el centinela distinto muere en la aserción de
orden relativo de las tres desconocidas; reintroducir `sorted(categories.keys())`
en cualquiera de los dos sitios → la guarda estática.

> Por qué la guarda estática y no un test de comportamiento: los dos sitios
> sintomaticos (`_render_list:176` y `_render_pack_card:207`) construyen widgets, y
> probarlos exigiria una ventana de Tk. El repo ya usa este patron (TASK-026 lo hizo
> con `self.master.after`).

### T-27.4 `test_toggle_favorite_desmarca` (FIX-006)

`PackManagerView.__new__(PackManagerView)`, `pack_service` grabador cuyo
`get_all_packs()` devuelve **instancias nuevas** en cada llamada (como el servicio
real tras un `model_copy`), `refresh_packs = lambda: None`.

1. `a` no favorito → `set_favorite("a")`.
2. `a` favorito (el grabador cambia el `is_favorite` de la instancia que devuelve) →
   `set_favorite(None)`.
3. `get_all_packs()` sin ese id → **no** lanza y **no** llama a `set_favorite`.
4. **Dos** favoritos (alcanzable editando `profiles.json`): pulsar la estrella del
   segundo lo desmarca a él. Esto es lo que separa la decisión elegida de
   `get_favorite_pack()`.

**Mutaciones que deben morir:** `set_favorite(pack_id)` incondicional (el estado de
producción actual) → la 2 registra `"a"` y no `None`; leer el `is_favorite` de un
`pack` capturado en el render → el grabador devuelve instancias nuevas, la
instantánea queda obsoleta y la 2 falla; el atajo `get_favorite_pack()` → con dos
favoritos devuelve el primero y la 4 falla; `else: set_favorite(pack_id)` sin
comprobar `pack is not None` → la 3 revienta.

### T-27.5 Registro

Los cuatro en el `__main__` de `run_tests.py` (después de la línea 4319) y
`python run_tests.py` en verde, **incluidos** `test_pack_service_favorite_exclusive`
(sin tocarlo), `test_do_load_publica_sin_tk` (TASK-026) y `test_no_system_process_is_killable`
(TASK-024).

---

## §1 — Cambios de producción (en este orden)

1. **FIX-003 servicio** — `process_service.py`: `_ALLOWED_APP_EXTS`, raíces,
   `_resolver_app(entry, raices=None)`, `_lanzar(ruta)`, y `start_pack_apps`
   reescrito (logging del rechazo, `started += 1` después del `try`).
   Sin `subprocess` en el fichero: verificado por grep que `process_service.py:404`
   es su único uso, y desaparece.
2. **FIX-003 vista** — `process_manager_view.py:334`: `exe_path` con degradación a
   `full_name`.
3. **FIX-004** — `config.py`: `ordenar_categorias`; usarla en
   `process_manager_view.py:176` y en `pack_manager_view.py:207`.
4. **FIX-006** — `pack_manager_view.py:213`: estado leído en vivo de
   `get_all_packs()`.
5. **Docs** — `docs/ai/architecture.md` (validación de arranque: sin intérprete, sin
   UNC, contención post-normalización), `docs/ai/ui-design-system.md` (orden de
   secciones = `CATEGORY_ORDER`, y el estado vacío de la portada al desmarcar),
   `docs/known-issues.md` (trampa nueva: `sorted()` sobre cadenas con emoji ordena
   por *code point* y sale al revés).

## §1b — Iteración 2 (el `mutation-auditor` dio **FAIL**)

Cuatro hallazgos. El primero es una **garantía documentada que era falsa**, y por eso esta
iteración empieza midiendo en vez de escribir código.

### El hallazgo 1 (ALTA): la contención léxica no atraviesa un junction

`normpath` y `commonpath` son **léxicos**. Medido con un junction real
(`mklink /J <TEMP>\jdir C:\Windows\System32`):

| comprobación | sobre `<TEMP>\jdir\cmd.exe` |
|---|---|
| `normpath` | intacta |
| `commonpath([ruta, %LOCALAPPDATA%])` | `%LOCALAPPDATA%` → "contiene": **falso** |
| `isfile` | `True` (sigue el enlace) |
| `stat().st_file_attributes` | `0x20` — ni reparse: **tampoco lo ve** |
| `realpath()` | `C:\Windows\System32\cmd.exe` ← la verdad |

**Decisión de estrategia: `os.path.realpath(ruta, strict=True)`, sin `ctypes`.** El encargo
ofrecía `GetFinalPathNameByHandle` por `ctypes` o un `st_file_attributes`; la medición
descarta las dos: el atributo no ve el enlace de un tramo **intermedio** (solo el final), y
`os.path.realpath` **es** el envoltorio de `GetFinalPathNameByHandleW` en la `ntpath` de
CPython, con el resultado medido. Menos código, mismo resultado, y sin `ctypes` en el servicio
(la separación de capas no se mueve: sigue siendo la capa de dominio la que habla con el SO).
**Fail-closed:** `strict=True` levanta si el SO no resuelve → `None` → no se arranca.

Dos consecuencias que no estaban en el encargo y sí son el mismo agujero:

* **La extensión se mira en el alias y en el destino.** Un `.exe` que es un enlace a un `.bat`
  **de una raíz permitida** pasa la contención real y esquivaba la lista blanca entera
  (`ShellExecute` → `cmd.exe /c`). Se comprueba en las dos rutas.
* **Las raíces se resuelven también.** Con la raíz léxica, un junction en algún tramo de
  `%LOCALAPPDATA%` rechazaría apps legítimas: el otro modo de fallar. Sin una sonda para esto, el
  arreglo del "siempre" se cuela por el lado del falso negativo.

Y se devuelve la **ruta real**, no la escrita: lo que se valida es lo que se arranca.

### El hallazgo 2 (MEDIA, M10): la contención por prefijo no estaba vigilada

El auditor midió que `startswith` en vez de `commonpath` **sobrevivía**: la suite entera
seguía verde. Sonda nueva con un hermano de verdad (`<tmp>` y `<tmp>Evil`, con ficheros
reales) en la función y extremo a extremo. Controles positivos en la misma sonda, porque una
sonda que solo sabe rechazar no distingue "contiene" de "no contiene nada".

### El hallazgo 3 (MEDIA): la guarda anti-`shell=True` era ciega

Solo miraba `ast.Name`, así que **`subprocess.Popen(app, shell=True)`** —la grafía exacta del
bug original— pasaba sin que la guarda se enterara. Ampliada a `ast.Attribute` **y** al mapa de
alias de los `ImportFrom` (`from subprocess import Popen as abrir`), y `shell` deja de exigir
`is True` para marcarse (cualquier valor que no sea un literal falso es un intérprete). La
guarda se extrae a `_hallazgos_shell_true(fuente, etiqueta)`, que es la que usan **las dos**
sondas (la vieja y la nueva): dos guarditas con coberturas distintas son cero guardas. La
sonda nueva exige además los **falsos positivos** que no deben marcarse (`shell=False`,
`Popen` sin `shell`, una cadena que mencione `shell=True`), porque una guarda que marca de más
acaba ignorándose.

### El hallazgo 4 (MEDIA): sensibilidad a mayúsculas — **decisión: `os.path.normcase`**

`C:\PROGRAM FILES\...` se rechazaba porque `commonpath` no normaliza caja, y en Windows el
sistema de ficheros **no distingue mayúsculas**. Era fail-closed (seguro) pero un bug funcional:
un programa legítimamente instalado con otro caso no arrancaba nunca.

**Se aplica `normcase` en los dos lados, y no se documenta como limitación.** El argumento para
no documentarlo es que `normcase` **no ensancha el conjunto aceptado**: declara la verdad del
SO, así que lo que entra es exactamente lo que el SO abriría, y encima siguen aplicando la
contención y la extensión **reales**. El coste es una llamada por comparación. Y `normcase`
**no sustituye** a `commonpath` (el hermano de prefijo seguiría entrando), por eso M10 tiene su
propia sonda. La sonda prueba **las dos direcciones** porque con `normcase` solo en un lado la
mitad de los casos sigue fallando.

### Las sondas de esta iteración (una por fix, todas en `run_tests.py`)

| # | Sonda | Qué muere |
|---|---|---|
| 49 | `test_un_junction_no_puede_colar_lo_que_hay_detras` | A1–A10: borrar la resolución real, contención real siempre `True`, extensión solo en el alias, `realpath` sin `strict`, rechazar todo reparse point, devolver la ruta léxica, fail-open, raíces léxicas, sin motivo en el log, comparar la léxica contra las raíces reales |
| 50 | `test_la_contencion_no_acepta_un_hermano_de_prefijo` | M10: `startswith` por `commonpath` |
| 51 | `test_la_contencion_no_depende_de_la_caja` | C1–C3: quitar `normcase`, y quitarlo solo en un lado |
| 52 | `test_la_guarda_de_shell_true_ve_atributos_y_aliases` | G1–G4 y P1/P2: quitar `ast.Attribute`, quitar el mapa de alias, volver a `is True`, marcar de más, y **reintroducir `Popen(..., shell=True)` en el producto** |

**El junction de la sonda es real, y `_mklink` falla ruidosamente si no puede crearlo.** Un test
que se pone verde porque "el caso no se pudo construir" es peor que no tener test. El destino
del junction de directorio es un directorio controlado **fuera** de las raíces y no
`C:\Windows\System32`: si la limpieza fallara, un `rmtree` que siguiera el enlace borraría
`System32`. El `cmd.exe` de verdad se cubre con un enlace de **fichero**, que `os.remove` solo
borra a sí mismo.

### Matriz medida

`_mutmatrix_t027_iter2.py`: copia de `src/` a `%TEMP%` por mutación, **el producto** mutado
(nunca la sonda), **una sonda por subproceso**. **21 mutaciones, 21 muertas.** Además hay
cuatro **cruces informativos** en la salida del script, con su motivo: una mutación tiene que
morir en la sonda que **declara** esa propiedad, y ninguno de esos cuatro pares es un agujero
porque cada propiedad sí muere en su propia sonda (A1 en la del junction, M10 en la del hermano,
G1 en la de la guarda).

**Lo que esta iteración NO arregla (deuda declarada).** Un **hard link** (`mklink /H`) no es un
reparse point: ni `realpath` ni los atributos lo ven. No es arreglable con esta regla y no hace
falta —un hard link es una entrada de directorio más bajo una raíz permitida— pero está escrito
en el módulo, en `architecture.md` §14 y en `known-issues.md` (Trampa #17) para que nadie lea
"nada fuera de las raíces" sin el asterisco.

---

## §2 — Cierre

- `python run_tests.py`, `python verify_ui_syntax.py`, `python validate_docs.py` en
  verde.
- `python .taskmaster/git_safe_commit.py "<msg>"` con código de salida 0, anotando
  el hash real.
- **Paso 4 obligatorio**: `mutation-auditor` ejecuta las 9 mutaciones de la tabla de
  T-27.1 y las 4 de T-27.2/3/4. Un superviviente se arregla, no se documenta.
- `CHANGELOG.md` y `.taskmaster/CHANGELOG.md`.

## Fuera de alcance

`TASK-029` (tokens de diseño), migración de los `apps` ya guardados a ruta
absoluta, y cualquier cambio en `PackService` (su contrato ya soporta `None`).
