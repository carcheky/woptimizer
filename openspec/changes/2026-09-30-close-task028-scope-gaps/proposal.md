# Propuesta — Cerrar los huecos de alcance del ciclo 21 (TASK-028, iteración 3)

**Fecha:** 2026-09-30 · **Origen:** `mutation-auditor`, tercera vuelta del ciclo 21
**Predecesoras:** `2026-09-30-close-task028-survivors/` (iteración 2, cerró los 16 supervivientes),
`2026-09-30-task028-debt-cleanup/` (diseño de TASK-028)

## 0. Qué NO es esta iteración

Los **16 supervivientes originales del ciclo 21 ya están cerrados**: el auditor ejecutó 25
mutaciones y las 25 mueren por su aserción. **No se rehace nada de eso.** Lo que queda son **huecos
de alcance**, y son pocos y baratos: la promesa de la documentación era más fuerte que lo que la
sonda media. De cinco puntos que trae el encargo, **dos son trabajo real** (N7 y N1), uno es
documentar una decisión (M10), uno es una frase corrupta y uno es una nota en la guía de pruebas.

| # | Punto | Severidad | Destino |
|---|---|---|---|
| 1 | **N7** el detector de "configurar el logging al importar" solo veía `basicConfig` | ALTA-MEDIA | **Se cierra** (§1) |
| 2 | **N1** la norma de archivar vigilaba la raíz, pero la app lee `_app_dir()` | MEDIA | **Se cierra** (§2) |
| 3 | **M10** (categoría) el escáner de versión no pilla un semver sin token de versión | BAJA | **Deuda ACEPTADA** (§3) |
| 4 | Frase corrupta en `architecture.md` §11 (`no elAuditado`) | — | **Se corrige** (§4) |
| 5 | `run_tests.py:8` cierra el `stdout` del host si se importa desde otro proceso | — | **Se anota, no se cambia** (§5) |

## 1. N7 — el detector era más estrecho que la promesa

### El defecto

`architecture.md` §15 afirma que **`config.py` no configura nada al importarse**. El detector AST
(`test_config_no_configura_nada_al_importarse`) buscaba **una sola** forma: una llamada cuyo atributo
o nombre fuera `basicConfig`. Tres formas más del **mismo defecto** pasaban en verde:

| Mutación | Qué hace | Por qué es el mismo defecto |
|---|---|---|
| `logging.getLogger().addHandler(logging.StreamHandler())` | adjunta un handler al **root** | el root queda configurado como efecto colateral de importar |
| `logger.addHandler(logging.StreamHandler())` | idem, sobre el logger nombrado | ídem |
| `logging.config.dictConfig({...})` | reconfigura **todo** el árbol de logging | ídem, y peor |

O sea: **M16 era un nombre de función, no un criterio.** La promesa de la doc era más fuerte que lo
que la sonda media, y eso es exactamente el patrón que este ciclo viene a cerrar.

### El criterio, escrito antes de codificar (por qué no se pasa de amplio)

> **Configurar** = *adjuntar un handler a un logger*, *fijarle nivel o formato*, o *reemplazar su
> lista `handlers`*.
> **Obtener** el logger no es configurar: `logging.getLogger(__name__)` —incluso sin argumentos, que
> devuelve el **root**— es una **asignación** normal.

La segunda mitad es la que cuesta: `logger = logging.getLogger('woptimizer')` lo
importan `notification_service.py:21`, `pack_service.py:8`, `process_service.py:7` y
`ui/app.py:41,90`. Es el **punto de contrato** de §15. Un detector que lo marcase obligaría a moverlo
"para no tener que pensar", que es cambiar el invariante para acomodar al guardián. Tampoco cuenta
**construir** un handler sin adjuntarlo: no emite nada.

Implementación: helper `_configuraciones_de_logging(codigo, nombre)` en `run_tests.py`, con tabla de
nombres (`addHandler`, `removeHandler`, `setLevel`, `setFormatter`, `setHandlers`, `addFilter`,
`captureWarnings` + los de la lista `handlers`) y de funciones (`basicConfig`, `dictConfig`,
`fileConfig`, `disable`), filtradas por cabecera `logging`/`logging.config` para no marcar
`algo.disable()` de otra biblioteca. Los loggers nombrados a nivel de módulo se recogen de los
`X = logging.getLogger(...)` del propio módulo, y `dentro`/`fuera` se separan por `FunctionDef` /
`ClassDef`.

### El control en las DOS direcciones

Un detector que no ve nada y uno que ve de más dan **el mismo verde**. Por eso la sonda se pasa **a
sí misma** código sintético:

- **ILEGALES (8)**: tienen que marcarse todas. `getLogger().addHandler`, `logger.addHandler`,
  `dictConfig`, `fileConfig`, `getLogger().setLevel`, `root.handlers[:] = [...]`,
  `root.handlers.clear()`, `logging.getLogger(__name__).addHandler(h)`.
- **LEGALES (6)**: no puede marcarse ninguna. `logger = logging.getLogger('woptimizer')`,
  `logging.getLogger(__name__)`, `root = logging.getLogger()`, un `StreamHandler()` construido sin
  adjuntar, `basicConfig` **dentro** de una función, y una constante de formato.

Y se conserva el control ya existente de que el detector encuentra algo **dentro** de
`setup_logging` (si no, "no hay ninguna" sería el verde de un detector muerto).

### Matriz medida

`_mutmatrix_t028_iter3.py` (copia del árbol por mutación en `%TEMP%`, **excluyendo el fichero
`.git`**, `git init` + `git add -A` **dentro** de la copia, `__pycache__` purgado, un subproceso por
sonda, el **producto** mutado y nunca la sonda, y el veredicto exige que la muerte sea **por la
aserción prevista**):

**8 mutaciones de producto, 8 muertas** (`M16b`…`M16i`), todas por
`assert not fuera, "… CONFIGURA el logging a NIVEL DE MODULO …"`.

**Mutaciones de la sonda (siempre acompañadas del mutante que deberían matar):**

| # | Mutación de sonda | Veredicto medido | Qué demuestra |
|---|---|---|---|
| **P7a** | detector muerto (`_motivos` no devuelve nada) | **ROJA** por el control `dentro` | sin ese control, un detector roto daría verde siempre |
| **P7b** | detector demasiado amplio (`getLogger` cuenta como configurar) | **ROJA** por la parte A | un detector de más no se cuela en verde |
| **P7c** | parte A anulada **+** detector amplio | **ROJA** por `CONTROL ROTO (falso POSITIVO)` | la tabla LEGALES es la que **diagnostica** el error del detector |
| **P7d** | parte A anulada **+** `M16b` | **VERDE: el mutante escapa** | las tablas son control **del detector**, no del fichero: la parte A lleva el veredicto |

## 2. N1 — la norma de archivar vigilaba la ruta equivocada

### El defecto

`test_el_archivo_legacy_esta_versionado_y_no_vuelve_a_la_raiz` afirma que lo archivado no vuelve a la
**raíz**. Pero la app **no lee la raíz**: `PROFILES_FILE` sale de `_app_dir()`, que en modo
desarrollo devuelve `dirname(config.py)` = **`src/woptimizer/profiles.json`**, y congelado el
directorio del `.exe` (`data-models.md` §Reglas de Persistencia, y el propio README del archivo, que
ya lo decía). El auditor copió el `profiles.json` v2 archivado a **`src/woptimizer/profiles.json`**, la
ruta que la app lee de verdad, y la suite quedó **verde**.

Y no es un fichero inerte ahí: `PackService.load()` tiene **rama legacy**, así que lo cargaría de
verdad, con las claves que `models.py` no define (`__system_gaming__`, `kind`, `label`, `factory`,
`kill_low_chat`) — y con `extra="allow"` ni siquiera se rompe: **se arrastra**.

### La desviación del encargo, y por qué

El encargo pedía `assert not os.path.exists(os.path.join(_app_dir(), "profiles.json"))`, y añadía
*"comprueba tú mismo que el fichero vivo real NO está en esa ruta antes de escribir el assert, o
teclejas una sonda que falla siempre"*. **Comprobado: el fichero vivo real SÍ está en esa ruta.**

```
> Test-Path 'src\woptimizer\profiles.json'   -> True   (670 B, esquema v3 {"packs": …},
                                                     mtime 2026-09-29 2:31, ignorado por git,
                                                     NO versionado)
```

Es el **estado local que escribe la propia app**, y la app funciona sin él (`load()` es de solo
lectura, TASK-031) pero lo regenera en el primer guardado real. La aserción literal habría sido
**una sonda que falla siempre** en la máquina del propietario, que es la Trampa que el propio
encargo advertía.

**Lo que se hace en su lugar, y por qué es MÁS fuerte y no más flojo:** la comprobación es sobre el
**contenido** de la ruta viva. Si hay documento, tiene que ser del esquema **vivo** (`{"packs": …}`) y
no el v2 retirado (`__system_gaming__` / `factory` / `kill_low_chat` en la raíz `profiles`). Eso mata
**las tres** mutaciones, incluida la copia reformateada, que una igualdad de bytes no mataría. Y se
afirma antes que `PROFILES_FILE == _app_dir()/profiles.json`, para que la sonda no se quede vigilando
una ruta que la constante ya no nombra.

### Matriz medida

**3 mutaciones de producto, 3 muertas** (por `assert not encontrados, "… la RUTA VIVA …"`):

| # | Mutación | Por qué está |
|---|---|---|
| **M13c** | copia **byte a byte** del v2 archivado a la ruta viva | la que hizo el auditor y que pasaba en verde |
| **M13d** | el mismo v2 **reformateado** (`indent=1`, claves ordenadas) | demuestra que se mira el **contenido**, no los bytes |
| **M13e** | un v2 que **no** es el archivado (otro nombre de preset, `factory` propia) | el v2-restaurado no depende de ser la misma copia |

**Mutación de sonda:** **P1a** (mirar la raíz `packs` en vez de `profiles`) **+** M13c → **VERDE: el
mutante escapa**. La comprobación es portante, medido, no supuesto.

## 3. M10 (categoría) — DEUDA ACEPTADA, no se arregla

El escáner de versión (`test_la_consulta_de_version_no_puede_desincronizarse`) exige literal semver
**y** token de versión en la misma línea, así que una línea con un semver y **otro** token
(`set TAG=9.9.9` en `build.bat`, `release = "9.9.9"` en el `.spec`) escapa al filtro.

**Dictamen del `mutation-auditor` (2026-09-30): aceptable.** Ya está escrito en `architecture.md` §15
y ahora también aquí. La consecuencia es **desincronización de la versión de empaquetado**, no
seguridad ni datos. **No se arregla en esta iteración.** Queda escrito para que el próximo que lo lea
sepa que es una **decisión** y no un olvido: si algún día se arregla, es por otra razón, no porque
esta iteración lo dejara pendiente.

## 4. Frase corrupta en `architecture.md` §11

Preexistente. Decía `Aquí se transcribe el rango medido, no elAuditado.` — dos palabras pegadas, y
"elAuditado" no se refiere a nada (no hay un "auditado" en el texto; el encargo citaba
`process_service.py:23-38`). Corregido a: se transcribe el rango **medido** (`process_service.py:33-48`,
con `ast`), **no el que venía en el encargo**. Lo mide `test_la_documentacion_del_blindaje_no_puede_desfasarse`,
que sigue verde.

## 5. `run_tests.py:8` — se anota, NO se cambia

`sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')` deja el `sys.stdout` original sin
referencias, y su sustituto **cierra el buffer subyacente al liberarse**. Importar `run_tests` desde
otro proceso dispara eso: cuando el proceso importador termina, el `stdout` del host queda cerrado y
todo lo que el host escriba después sale roto. Le costó un ciclo entero de depuración.

**No se toca** (arriesga tumbar el runner entero y con él las 65 sondas). Se anota en
`docs/ai/testing-guide.md` como trampa para el próximo que escriba un validador que importe la
suite: que lance la sonda en un **subproceso** y no en el propio proceso. Es la mecánica que usa
`_mutmatrix_t028_iter3.py`.

## 6. Qué se toca

| Fichero | Cambio |
|---|---|
| `run_tests.py` | helper `_configuraciones_de_logging` + reescritura de N7 (detector general, 8+6 controles); bloque de ruta viva en N1 |
| `docs/ai/architecture.md` | §11 frase corrupta; §15 criterio del detector + dictamen M10 + nota de la ruta viva |
| `docs/ai/testing-guide.md` | matriz medida de la iteración 3 + la trampa de `run_tests.py:8` |
| `docs/archive/legacy-root-data/README.md` | por qué no se copia a la ruta viva (ya decía cuál es; ahora dice el coste) |
| `openspec/changes/2026-09-30-close-task028-scope-gaps/` | este documento y `tasks.md` |

**Ninguna línea de `src/` cambia en esta iteración.** Los dos puntos son de medición, no de producto.
