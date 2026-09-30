# TASK-028 — Saneamiento de deuda técnica (FIX-010 a FIX-020)

**Estado:** DISEÑO APROBADO CON RESERVAS. `openspec-dev` puede implementar el bloque SEGURO.
**Auditoría:** `architect-review`, 2026-09-30. Base verificada: `HEAD=262cdbf`, árbol limpio, `run_tests.py` en verde (57 tests).

---

## 0. Resumen ejecutivo

El encargo mezcla **operaciones triviales** (imports, constantes, literales) con **una migración de datos**
que ya se ejecutó en el ciclo 13 y cuya premisa es falsa. Cinco de los once puntos son **PREMISA FALSA**
o están **ya resueltos**.

| Fix | Veredicto | Riesgo |
|---|---|---|
| FIX-010 logging | VALIDADO CON REDISEÑO | Bajo (pero ver §1: hay un contrato de log que se rompe en silencio) |
| FIX-011 `PROCESS_LIST_FILE` | **PREMISA FALSA** | — (no borrar: 5 consumidores) |
| FIX-012 `is_expanded` | VALIDADO | Nulo |
| FIX-013 CSV → DB | **PREMISA FALSA — BLOQUEADO** | **ALTO (anti-brick)** |
| FIX-014 preservar tests | VALIDADO (es una restricción, no un trabajo) | Nulo |
| FIX-015 JSONs del root | **PREMISA FALSA A MEDIAS** | Bajo |
| FIX-016 `import sys` | VALIDADO | Nulo |
| FIX-017 archivar plan | VALIDADO | Nulo |
| FIX-018 versión | VALIDADO, **es cosmético** | Nulo |
| FIX-020 docs | VALIDADO | Nulo |

**Bloque SEGURO (aprobar):** FIX-010 (con el rediseño de §1), FIX-012, FIX-014, FIX-016, FIX-017, FIX-018, FIX-020.
**Bloque RIESGOSO (NO aprobar tal como está escrito):** FIX-013. **Bloque con premisa falsa:** FIX-011, FIX-015.

---

## 1. FIX-010 — desacoplar `basicConfig` de la importación de `config.py`

### Premisa: CONFIRMADA
`src/woptimizer/config.py:18-22` ejecuta `logging.basicConfig(...)` a nivel de módulo. El efecto colateral
**es real y es de lo que dependen 4 módulos**: `notification_service.py:21`, `pack_service.py:8`,
`process_service.py:7` y `ui/app.py:41,90` hacen `from woptimizer.config import logger`.

### El riesgo que el encargo no menciona: el contrato de `architecture.md` §5
`architecture.md:39` promete que los errores "`se canalizan a `woptimizer.log`". Ese promesse **depende
íntegramente** del `basicConfig` de importación. Si `basicConfig` sale de `config.py` y `setup_logging()`
solo se llama desde `main()`, entonces:

- `run_tests.py` importa los servicios **sin pasar por `__main__`** → la suite entera pierde el
  `FileHandler` y los `logger.warning` caen al `lastResort` de la stdlib (stderr), no al fichero.
- Cualquier consumidor que importe el paquete como librería pierde el log igual.
- **Hoy el coste es medible:** `src/woptimizer/woptimizer.log` pesa **1.799.880 bytes** (1,8 MB) de ruido
  acumulado de la suite. Está en `.gitignore` (`*.log`), así que no ensucia el árbol, pero es la huella
  del efecto colateral.

### Diseño aprobado (corrige la premisa de la spec)
La spec dice "crear `setup_logging()` invocado desde `__main__.py`". **Eso es insuficiente.** La función va
en `config.py` (junto a `logger`, su consumidor natural) y se invoca desde **los dos** puntos:

```python
# config.py — sustituye al basicConfig de nivel de módulo
def setup_logging(level=logging.WARNING) -> None:
    """Configura el log en fichero. Idempotente (force=True)."""
    logging.basicConfig(
        filename=os.path.join(_app_dir(), 'woptimizer.log'),
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True,          # CLAVE: BasicConfig() es no-op si root ya tiene handlers
    )
```

`force=True` (Python 3.8+) **cierra y elimina** los handlers previos: sin él, la segunda llamada es un
no-op mudo y si alguien cambia de fichero se crearía el segundo handler en el sitio viejo. Con `force=True`
la llamada es idempotente por construcción y no hay riesgo de `duplicate log message`.

Puntos de llamada: `__main__.py:main()` (antes de instanciar los servicios) **y** `run_tests.py`
(en su `__main__`, junto a las sondas). `logger = logging.getLogger('woptimizer')` **se queda** en
`config.py:23` sin tocar: los 4 importadores siguen funcionando igual.

### Test que discrimina
`test_logging_va_a_fichero_y_no_a_stderr` — falla sin el fix.

> **Por qué discrimina:** el test **elimina** los handlers de `logging.getLogger()` (`root.handlers.clear()`),
> invoca `setup_logging()`, y comprueba que existe un `logging.FileHandler` cuyo `baseFilename` termina en
> `woptimizer.log`. Con el código actual, `setup_logging` ni existe → `AttributeError`; si alguien lo
> implementa sin `force=True` y con un fichero distinto, la aserción sobre `baseFilename` falla.
> Un test que solo compruebe "existe un logger" no distinguiría nada: `getLogger` siempre devuelve uno.

**Control negativo obligatorio en el mismo test:** tras el `clear()`, un `logger.warning("x")` NO debe
llegar a `sys.stderr` (se captura con `contextlib.redirect_stderr`). Sin fichero, `lastResort` lo manda
a stderr — que es exactamente el fallo silencioso que hay que cazar.

---

## 2. FIX-011 — eliminar `PROCESS_LIST_FILE` y purgar `saved_processes.json`

### PREMISA FALSA: la constante NO está sin usar. Está en uso por 5 sitios.
`src/woptimizer/config.py:25` la define, y la consumen:

| Consumidor | Líneas | ¿Protegido? |
|---|---|---|
| `test_gaming_session.py` | 36, 37, 38, 39, 46, 48, 50 | **Sí** (FIX-014) |
| `test_harness.py` | 37 | **Sí** (FIX-014) |
| `test_harness_v2.py` | 64 | **Sí** (FIX-014) |
| `smoke_check.py` | **23** | ❌ **Ninguno: el script está MUERTO** (ver la nota de corrección de abajo) |

> ⚠️ **Corrección del ciclo 21 (hallazgo D1 del `mutation-auditor`, medido el 2026-09-30).**
> Esta tabla daba por hecho que `smoke_check.py` era un cuarto consumidor **vivo**, y que su
> línea 23 era "el caso duro" porque rompía por **texto** y no por `ImportError`. **Las dos
> cosas son falsas.** `smoke_check.py:7-8` lee `process_manager.py`, un fichero que este repo
> ya retiró, y revienta con `FileNotFoundError` **antes de llegar a la línea 23**: el `assert`
> nunca se ejecuta. Los consumidores **reales** son los tres de las filas de arriba (FIX-014),
> y el guardia que hoy vigila la constante es
> `test_process_list_file_sigue_siendo_un_contrato` (`run_tests.py`). La decisión de fondo
> —**no borrar** la constante— sigue siendo correcta, pero por los tres consumidores vivos, no
> por un cuarto que no corre.

`smoke_check.py:23` es el caso duro (así seyardó en su día; **hoy no se ejecuta**):
```python
assert "PROCESS_LIST_FILE = os.path.join(_app_dir()" in code
```
Borrar la constante **rompería** el smoke check por texto si alguien lo ejecutara, no por
ImportError, que es más difícil de ver.

Además FIX-011 **contradice FIX-014** en la misma tarea: uno pide borrar lo que el otro manda preservar.

**Decisión: NO se borra.** Se marca como legacy con un comentario de deprecación que nombre a los 5
consumidores, para que el próximo que lea la constante sepa que es un contrato con los tests del root.
Coste: una línea de comentario. Beneficio: no se rompe nada.

### El fichero `saved_processes.json` (37.997 bytes) — no es un cambio de repositorio
Está en `.gitignore:8`. `git status --porcelain` vacío lo confirma: es estado local **no versionado**.
Borrarlo es una operación en la máquina del usuario, no del repo, y el `saved_processes.json` que ve el
usuario es su historial de procesos, no un residuo.
**Decisión: no se toca.** Es exactamente el tipo de "limpieza" que la norma del propietario prohíbe
(NUNCA eliminar entregables). Si el propietario lo pide explícitamente, se archiva con fecha, no se `rm`.

---

## 3. FIX-012 — ternario `is_expanded = True if search_query else True`

VALIDADO. `src/woptimizer/ui/views/process_manager_view.py:184`:
```python
is_expanded = True if search_query else True
```
Ambas ramas son `True`: es un tautema, no una decisión. Se reduce a `is_expanded = True`.

### **Este fix NO admite test de regresión, y hay que decirlo**
El comportamiento observable es **idéntico antes y después**: `True if X else True == True` para todo `X`.
Cualquier test que se escriba aquí pasaría **con y sin el fix** → sería un test tautológico, exactamente lo
que el Paso 4 (mutation-auditor) existe para matar. **Correcto: cero tests, cero sondas de mutación.**
Un fix sin test es aceptable; un fix con test decorativo es un defecto.

---

## 4. FIX-013 — migrar `procesos.csv` → `assets/process_db.json`  ⛔ **BLOQUEADO**

**Este es el único punto del encargo que toca datos, y su premisa es falsa en el marco entero.**
Es el mismo patrón que el ciclo 14 encontró con `get_gaming_pack()`: se pide "arreglar" una migración que
ya se ejecutó, y hacerlo tal cual **revierte una decisión de seguridad deliberada**.

### Estado real (medido, no supuesto)
- `assets/process_db.json` es un **`dict[str, dict]`** de **73 entradas** (no una lista), con claves
  = nombre de proceso y valores `{category, priority, description}`.
- `procesos.csv` tiene **131 filas** con columnas `Proceso,Descripción,Seguridad`, donde `Seguridad` usa
  **palabras** (`Verde`/`Amarillo`/`Rojo`), **no emojis**.
- Los conjuntos **Verde-de-CSV (73)** y **DB (73)** tienen el mismo tamaño y **cero intersección útil**:
  la DB es la curada (navegadores, chat, launchers, media, sync, productividad, 2 de sistema) y el CSV es
  sobre todo bloatware de servicio (`aac3572dramhal_x86`, `aggregatorhost`, `apcent`, `audiodg`...).

**La migración ya se hizo en el ciclo 13 (TASK-024).** `.taskmaster/CHANGELOG.md:530-536` lo documenta:
*"Escaneo real: 131 nombres de proceso únicos, 48 registrados, 122 sin registrar"* y *"**25 entradas
añadidas** (48 → 73)"*. Los 131 nombres del CSV son exactamente el material de aquel escaneo.

### Por qué ejecutarla tal cual es un **vector de anti-brick**
Las decisiones del ciclo 13 **sobreescribieron a propósito** la columna `Seguridad` del CSV. La columna dice
`Verde` para la pila de control de hardware que el arquitecto del ciclo 13 puso en 🔴 **deliberadamente**
(`CHANGELOG.md:536`): *"La pila de control de Armoury Crate (armourycrate, armsvc, asus_framework, ...) a
🔴 none en vez de verde: es el equivalente a icue/razer/lghub, que en esta misma base ya están en 🔴 por
perfiles de ventilación y RGB. Cerrarlos deja el equipo sin perfil de juego."*

Importar el CSV "respetando sus semáforos" **revierte eso**: `aurawallpaperservice`, `armourysocketserver`,
`asus_framework`... volverían a ser verdes y killables → el equipo se queda **sin perfil de RGB y
ventilación durante la partida**. Es la misma clase de fallo que el ciclo 13 rechazó explícitamente.

### Y el test de regresión que YA existe NO lo cazaría
`run_tests.py:1357 test_no_system_process_is_killable` vigila `SYSTEM_PROTECTED_PROCESSES` (34 nombres) ∪
`{svchost, explorer}`. De las 73 filas Verde del CSV, **69 NO están en esa lista negra** y pasarían el
test en verde. Concretamente **`applicationframehost`, `widgetboard` y `widgetservice` no están en
`SYSTEM_PROTECTED_PROCESSES`** (sí lo están `audiodg`, `shellexperiencehost`, `searchhost`) y el CSV los
marca `Verde`: importarlos los vuelve cerrables y **el test actual no se entera**.

> **Este es el ciclo 14 repetido:** un guard por **lista negra** de nombres no es una garantía; la
> garantía es una **barrera de categoría** (G-2 en `architecture.md:76`). Pedir "0 procesos de sistema
> killables" con el test actual es pedir una garantía que el test no da.

### El CSV además está **malformado**
11 de las 131 filas tienen la descripción **sin comillas y con comas**, así que `Seguridad` recibe un
fragmento de texto, no un veredicto (valores medidos: `' iluminación RGB y perfiles de rendimiento.'`,
`'la barra de tareas y las carpetas.'`, `' Scoop o Chocolatey.'`, `' menú inicio y fondos.'`...).
Cualquier migración mecánica asignaría basura como categoría.

### Decisión: **FUERA DE ALCANCE en TASK-028.** Requiere su propia tarea.
No es "un poco más difícil": es un escaneo de 131 procesos contra una taxonomía viva, con decisión
humana por entrada (¿esto es bloatware cerrable o control de hardware?), y con la regla de que **la
columna `Seguridad` del CSV nunca es la fuente de verdad** —la fuente es la taxonomía del ciclo 13 más el
blindaje por categoría. Se propone **TASK-031** con `process-db-updater` como dueño, reusing el escaneo
real que ya hizo el ciclo 13.

Si el propietario insiste en hacerlo dentro de TASK-028, el mínimo es:
1. Clasificar por **categoría**, nunca por la columna del CSV.
2. Toda entrada nueva debe ser `\U0001F7E2`/`\U0001F7E1` con una clave que exista en `PROCESS_CATEGORIES`
   (`config.py:41-87`) **carácter a carácter**.
3. Excluir sin discusión todo nombre de `SYSTEM_PROTECTED_PROCESSES` **y** los componentes de shell
   que no están en ella (`applicationframehost`, `widgetboard`, `widgetservice`).
4. Truncar a las 73 + las aprobadas: **no** importar las 73 filas Verde en bloque.

---

## 5. FIX-014 — preservar los 11 `test_*.py` del root

VALIDADO, y verificado: `(Get-ChildItem test_*.py).Count == 11`. No es trabajo, es una **restricción**:
ningún fichero del root `test_*.py` se toca, borra ni renombra. Toda prueba nueva entra como función en
`run_tests.py`. Es además la razón por la que FIX-011 no puede borrar `PROCESS_LIST_FILE`.

---

## 6. FIX-015 — retirar los JSON residuales del root  ⚠️ PREMISA FALSA A MEDIAS

Hay tres ficheros, con veredictos distintos:

| Fichero | Tamaño | Veredicto |
|---|---|---|
| `profiles.json` (root) | 420 B | **VALIDADO — archivar** |
| `test_profiles_task1.json` | 311 B | **PREMISA FALSA — no tocar** |
| `saved_processes.json` | 37.997 B | ver FIX-011 — no tocar |

**`profiles.json` del root:** esquema **v2 muerto** — claves `__system_gaming__`, `kind`, `label` con
mojibake (`"?? Preparar para Gaming"`), `factory`, `kill_low_chat`, `favorite`, y **sin `is_gaming`**. El
fichero vivo es `src/woptimizer/profiles.json` (existe), porque `_app_dir()` en modo dev devuelve
`dirname(config.py)`. Nada de `src/` lo referencia. **Sí es residuo.**

**`test_profiles_task1.json` NO es residuo:** lo consume `verify_task1.py:12`
(`TEST_FILE = "test_profiles_task1.json"`, pasado a `PackService(data_path=TEST_FILE)`). Borrarlo rompe ese
script. No está en `.gitignore`, luego **está versionado**: borrarlo es un cambio real de repo.

### Patrón correcto (norma del propietario: nunca borrar, siempre versionar)
Nada de `rm`. **`docs/archive/legacy-root-data/`** con el fichero conservado **y** un
`README.md` que diga qué es, su fecha y por qué se retiró. `docs/archive/` **no existe todavía** — hay que
crearlo. Se cumple la norma (nada se destruye, nada se sobrescribe) y el repo queda limpio.
Lo que **no** se hace: `git rm`, "borrar el legacy", ni renombrar con sufijo incremental (aquí no hay
versiones que numerar: es un archivo, no un entregable que se revisa).

---

## 7. FIX-016 — `import sys` redundante en `app.py`

VALIDADO. `src/woptimizer/ui/app.py:61` tiene `import sys` dentro de `quit_app()`, y el módulo ya lo
importa en `app.py:1`, que se usa en `app.py:45` (`getattr(sys, 'frozen', False)`).

**Trampa de Python verificada y descartada:** un `import` dentro de una función hace que ese nombre sea
**local a TODA la función**, así que un uso *anterior* al `import` daría `UnboundLocalError`. Aquí
`quit_app` (líneas 50-62) no usa `sys` antes de la línea 61 —los usos de `sys` de las líneas 44-45 están en
otro método (`on_window_close`)—. Se puede borrar la línea 61 sin riesgo. Cero tests (sin cambio de
comportamiento, igual que FIX-012).

---

## 8. FIX-017 — archivar `inconsistencies_plan.md`

VALIDADO, y con una observación: el fichero es un plan **titulado "100% Completado"** que describe
incidencias **ya resueltas** (habla de `fallback.csv`, que ya no existe — hoy es `assets/process_db.json`—;
y del string `'?? Chat y Comunicación'` hardcodeado en `should_kill_for_gaming`, que TASK-020 ya
arregló). Es un documento **engañoso**: si alguien lo lee, Cree que hay trabajo pendiente que no existe.
**Por eso archivar es lo correcto y borrarlo sería un error.** A `docs/archive/` (misma carpeta que FIX-015),
dejando su contenido intacto. Su valor es el de un registro histórico de por qué se hicieron los cambios.

---

## 9. FIX-018 — unificar versión a `3.0.1`

**VALIDADO, pero es cosmético. No lo pases por cambio arquitectónico.**

Estado real, medido en los tres sitios donde puede aparecer:
| Sitios | Valor actual | ¿Lo referencia? |
|---|---|---|
| `pyproject.toml:3` | `version = "3.0.0"` | — |
| `src/woptimizer/__init__.py:1` | `__version__ = "3.0.0.dev0"` | — |
| `woptimizer.spec` | **sin campo `version`** | No lo hardcodea |
| `build.bat` | **sin coincidencia** de versión | No |
| `force_build.py` | **sin coincidencia** | No |

`woptimizer.spec` (leído entero) no declara versión: PyInstaller la toma del `.exe`, así que **no hay un
tercer sitio que sincronizar**. Son exactamente dos ficheros. Ningún test verifica la versión hoy.

**Aviso de honestidad contractual:** `3.0.0.dev0` significa "pre-release, sin publicar". Fijar `3.0.1`
afirma una versión publicada que no existe. Si no hay una release real detrás, el valor correcto es
`3.0.0` en ambos sitios (unificar sin inventar), y `3.0.1` solo cuando haya changelog y build de esa
versión. **Decisión que se pide al propietario en el informe.**

---

## 10. FIX-020 — sincronizar `docs/ai/data-models.md` y `docs/ai/architecture.md`

VALIDADO. Además de la sincronización pedida, hay **dos correcciones de contenido** que esta auditoría
descubrió y que son las que de verdad hay que hacer:

1. **`architecture.md:76` y `tasks.json:407` sitúan `SYSTEM_PROTECTED_PROCESSES` en `config.py`.**
   **Es falso: vive en `process_service.py:23-38`** (34 nombres, coincidencia exacta). La lista real:
   `audiodg, conhost, csrss, ctfmon, dllhost, dwm, fontdrvhost, lsaiso, lsass, memcompression, ngciso,
   openconsole, registry, runtimebroker, searchhost, searchindexer, securityhealthservice,
   securityhealthsystray, securityhealthui, services, shellexperiencehost, sihost, smss, spoolsv,
   startmenuexperiencehost, system, "system idle process", systemsettings, taskhostw, textinputhost,
   wininit, winlogon, wudfhost, wudfsvc`. Importa porque quien vaya a tocar el blindaje irá a `config.py`
   y no lo encontrará.
2. **`architecture.md:76` afirma que `svchost`/`explorer` "no figuran en `SYSTEM_PROTECTED_PROCESSES`"** —
   verificado: es cierto, y por eso la barrera de categoría G-2 es necesaria. Se deja como está, porque
   es la justificación de la invariante.

Añadir además un §15 brief sobre el contrato de logging (§1), para que el cambio de FIX-010 quede
documentado como invariante y no como un refactor invisible.

---

## 11. Tests nuevos (los únicos tres, y por qué discriminan)

Todos en `run_tests.py`. **Los fixes de riesgo nulo (012, 016) no llevan test, y eso es deliberado.**

### T1. `test_logging_va_a_fichero_y_no_a_stderr`  (para FIX-010)
Limpia los handlers, llama `setup_logging()`, afirma que hay un `FileHandler` cuyo `baseFilename` acaba en
`woptimizer.log`, y afirma que un `logger.warning` de prueba **no** aparece en `stderr`.
*Falla sin el fix:* hoy `setup_logging` no existe → `AttributeError`; y con la implementación sin
`force=True` ni fichero, la captura de `stderr` lo delata.

### T2. `test_la_consulta_de_version_no_puede_desincronizarse`  (para FIX-018)
Lee `pyproject.toml` con `tomllib` y `src/woptimizer/__init__.py` con `ast` (**nunca con `import`**, que
ejecutaría el paquete), y afirma que el `__version__` y el `version` coinciden.
*Falla sin el fix:* hoy `"3.0.0"` vs `"3.0.0.dev0"` → aserción falsa. Es el discriminador más barato del
paquete y además impide que la desincronización vuelva.

### T3. `test_la_columna_seguridad_del_csv_no_es_la_fuente_de_verdad`  (para FIX-013, **solo si se desbloquea**)
Para cada nombre de `assets/process_db.json` que también aparezca en `procesos.csv`, afirma que la
**categoría del JSON** manda, y que ninguna entrada de hardware/RGB known (`armoury*`, `asus_*`, `icue`,
`razer`, `lghub`, `gigabyte*`, `hercules*`) tiene semáforo distinto de 🔴.
*Falla si alguien importa el CSV:* con la columna `Seguridad` como fuente, `armourycrate` vuelve a verde
y la aserción 🔴 se rompe. Es el test que convierte el hallazgo del ciclo 13 en invariante permanente.

### Invariante que se hereda sin escribir nada
`test_no_system_process_is_killable` (`run_tests.py:1357`) y `test_category_emoji_alignment`
(`run_tests.py:320`) **ya cubren** la capa 1 del blindaje y la coincidencia de emojis. Si FIX-013 llegara a
tocarse, ambos deben seguir en verde **y** hay que añadir T3, porque ninguno de los dos vigila la
proveniencia de la categoría. No se duplican.

---

## 12. Criterios de aceptación (los que discriminan; los tautológicos se descartan)

1. `config.py` **no** ejecuta `basicConfig` a nivel de módulo; existe `setup_logging()` con `force=True`,
   invocado desde `__main__.py:main()` **y** desde `run_tests.py`.
2. `test_logging_va_a_fichero_y_no_a_stderr` pasa, y **falla** si `force=True` se sustituye por un
   `basicConfig` sin `force` (se elimina el test, no la guarda).
3. ~~`smoke_check.py` sigue en verde **sin tocarlo**~~ — **CRITERIO MUERTO, retirado el
   2026-09-30** (ciclo 21, hallazgo **D2** del `mutation-auditor`). Es **imposible**: el script
   lee `process_manager.py` en su línea 8, ese fichero no existe, y revienta con
   `FileNotFoundError` **sin llegar nunca a su línea 23**, que es donde estaba el `assert` sobre
   el texto fuente. No tiene ruta de ejecución verde, y el único modo de "cumplirlo" sería
   recrear `process_manager.py` (resucitar el programa legacy que este repo ya retiró).
   **Sustituido por:** `test_process_list_file_sigue_siendo_un_contrato` en `run_tests.py`
   (`openspec/changes/2026-09-30-close-task028-survivors/`), que afirma lo que el criterio
   quería afirmar — que `PROCESS_LIST_FILE` no se borró — con un guardia que **se ejecuta**:
   existencia y valor de la constante, y los tres consumidores reales nombrados.
   El §2 de este documento ("`smoke_check.py:23` es un `assert` sobre el texto fuente") queda
   igualmente **refutado**, y así se corrigió también en el comentario de `config.py`.
4. Los 11 `test_*.py` del root siguen ahí, byte a byte (`git status` no los lista).
5. `procesos.csv` **no se ha modificado** y `assets/process_db.json` sigue con **73 entradas**
   (FIX-013 fuera de alcance; si alguien lo toca, este criterio salta).
6. `docs/archive/legacy-root-data/` contiene `profiles.json` (v2) con su README, e
   `inconsistencies_plan.md`. `docs/archive/legacy-root-data/` **no** contiene `test_profiles_task1.json`
   ni `saved_processes.json`, y `verify_task1.py` sigue ejecutándose.
7. `test_la_consulta_de_version_no_puede_desincronizarse` en verde.
8. `architecture.md` sitúa `SYSTEM_PROTECTED_PROCESSES` en `process_service.py:23-38`, con los 34
   nombres, no en `config.py`.
9. `python run_tests.py` en verde (57 tests + los nuevos), `verify_ui_syntax.py` y `validate_docs.py`
   en verde, `git_safe_commit.py` con salida **0**.

---

## 13. Nota de inglés (and the one idiom that matters)

Two phrasings in this repo's own vocabulary are worth keeping straight, because they are *not*
interchangeable:

- **"premisa falsa"** — a false premise: the brief states something the code no longer satisfies.
  (*The premise is false: the migration already happened in cycle 13.*)
- **"barrera de categoría" vs "lista negra"** — a category barrier vs a blacklist. This repo has
  already paid for confusing the two once (cycle 14, `svchost`). In English the trap is calling both
  "filter": *"filter by protected list"* and *"filter by red category"* are **not** the same operation.
  Say *barrier* for the former's absence.

Se dice *"visto bueno"* (approval), no *"visto bueno parcial"*: si es parcial, es un **no** con alcance.
