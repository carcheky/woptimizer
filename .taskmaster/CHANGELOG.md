## [CYCLE-033] 2026-10-01 15:45 — tray-session-restoration-ux
**Área**: Gaming & Telemetría UX
**Change**: openspec/changes/2026-10-01-tray-session-restoration-ux/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): flash (Área 2)
- Paso 2 (Planear): architect-review → VISTO BUENO Y APROBADO
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO Y DOCUMENTADO
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (+1 test discriminante validado)

### Cambios Clave
- `src/woptimizer/ui/app.py`: Opción `'🔄 Reabrir aplicaciones cerradas'` en el menú contextual de `pystray`. Ejecución asíncrona de restauración de sesión gaming y notificación nativa.
- `run_tests.py`: +1 test discriminante (`test_tray_session_restoration_integration`). Suite elevada a 88 tests al 100% en verde.
- `docs/ai/architecture.md`: Actualización de la documentación viva.

---

## [CYCLE-032] 2026-10-01 15:30 — system-resilience-hardening
**Área**: Resiliencia & Robustez
**Change**: openspec/changes/2026-10-01-system-resilience-hardening/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): flash (Área 1)
- Paso 2 (Planear): architect-review → VISTO BUENO Y APROBADO
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO Y DOCUMENTADO
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (+2 tests discriminantes validados)

### Cambios Clave
- `src/woptimizer/services/notification_service.py`: Reemplazo de `threading.Lock()` por `threading.RLock()` para thread-safety reentrante.
- `src/woptimizer/services/process_service.py`: Captura defensiva de `psutil.ZombieProcess` y `OSError` en `kill_processes` y `kill_pack_apps`.
- `run_tests.py`: +2 tests discriminantes (`test_notification_service_rlock_and_concurrency`, `test_process_service_kill_defensive_zombie_and_oserror`). Suite elevada a 87 tests al 100% en verde.
- `docs/ai/architecture.md`: Actualización de la documentación viva.

---

## [CYCLE-031] 2026-10-01 10:10 — testing-quality-expansion-c31
**Área**: Testing & Calidad
**Change**: openspec/changes/2026-10-01-testing-quality-expansion-c31/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): flash (Área 5)
- Paso 2 (Planear): architect-review → VISTO BUENO Y APROBADO
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO Y DOCUMENTADO
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (100% mutaciones eliminadas)

### Cambios Clave
- `run_tests.py`: +2 tests discriminantes (`test_pydantic_extra_fields_persistence`, `test_freed_mb_calculation_precision`). Suite elevada a 85 tests.
- Re-auditoría con `patch("psutil.Process")` en `test_freed_mb_calculation_precision`: mutaciones en `process_service.py:586` aniquiladas exitosamente.

---

## [CYCLE-030] 2026-10-01 09:50 — ui-filter-and-pack-latency-opt
**Área**: Rendimiento & Latencia
**Change**: openspec/changes/2026-10-01-ui-filter-and-pack-latency-opt/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): flash (Área 4)
- Paso 2 (Planear): architect-review → VISTO BUENO Y APROBADO
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO Y DOCUMENTADO
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (3/3 mutantes supervivientes de la 1ª iteración eliminados)

### Cambios Clave
- `src/woptimizer/services/pack_service.py`: Caché de lectura defensiva en 2 capas (< 0.05 ms) e invalidación atómica.
- `src/woptimizer/ui/views/process_manager_view.py`: Pre-tokenizado y filtrado rápido (< 2.0 ms) para 350+ procesos.
- `run_tests.py`: +2 tests discriminantes (`test_pack_service_cache_invalidation_and_immutability`, `test_process_filter_performance`). Total suite elevando a 83 tests.

---

## [CYCLE-029] 2026-10-01 09:10 — process-db-expansion-c29
**Área**: Base de Datos & Procesos
**Change**: openspec/changes/2026-10-01-process-db-expansion-c29/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): flash (Área 3)
- Paso 2 (Planear): process-db-updater → VERIFICADO
- Paso 3 (Ejecutar): process-db-updater → IMPLEMENTADO
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (89 procesos validados sin omisiones ni solapamientos)

### Cambios Clave
- `assets/process_db.json`: +8 nuevos procesos reales (`89 total`).
- 0 solapamientos con `SYSTEM_PROTECTED_PROCESSES` (34 procesos protegidos).
- `test_process_db_schema_integrity` y `test_category_emoji_alignment` pasando al 100%.

---

## [CYCLE-028] 2026-10-01 08:50 — gaming-session-restoration
**Área**: Gaming & Telemetría UX
**Change**: openspec/changes/2026-10-01-gaming-session-restoration/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): flash (Área 2)
- Paso 2 (Planear): architect-review → VISTO BUENO Y APROBADO
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO Y DOCUMENTADO
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (100% mutaciones eliminadas)

### Cambios Clave
- `GamingService._last_closed_apps`: Captura pre-kill de rutas `.exe` absolutas únicas.
- `GamingService.restore_gaming_session()`: Reabre aplicaciones vía `start_pack_apps`.
- `DashboardView._show_restore_banner`: UI thread-safe con botón "Reabrir Apps".
- `test_gaming_service_session_restoration`: Test unitario registrando suite total de 81 tests.

---

## [CYCLE-027] 2026-10-01 08:15 — guardas-que-no-guardan
**Área**: Resiliencia & Robustez / Deuda Técnica
**Change**: openspec/changes/2026-09-30-guardas-que-no-guardan/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): flash (backlog TASK-037)
- Paso 2 (Planear): architect-review → VISTO BUENO CON DIRECTRICES OBLIGATORIAS
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO
- Paso 4 (Auditar tests): mutation-auditor → **PASS** (9/9 mutaciones aniquiladas por aserción)

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| _recuento_de_tests | M1 except sin SyntaxError | killed | IndentationError no capturado |
| _recuento_de_tests | M2 except sin OSError | killed | FileNotFoundError no capturado |
| _comprobar_recuento | M3 rama muerta | killed | Faltan mensajes [FAIL] |
| _comprobar_recuento | M4 ok.append en vez de error | killed | Falso OK en resumen |
| guard_llamantes | M5 tupla literal fija 3 ficheros | killed | Modulo sintetico 4 no se marca |
| guard_llamantes | M6 descarta ast.Attribute | killed | fb.mensaje_sin_apps no se marca |
| guard_llamantes | M7 marca todo | killed | Marca literales validos 'start'/'kill' |
| guard_llamantes | M8 limita a ui/views/ | killed | Modulo sintetico fuera de views/ no se marca |
| huerfanos | M9 concatena segmento vacio | killed | Se emite 'invocado y NO definido: .' |

### What
- _recuento_de_tests en validate_docs.py emite None ante OSError y SyntaxError de run_tests.py.
- Extraida la funcion _comprobar_recuento_de_tests para hacer testeable el check 7.
- El guard de contrato de llamantes de ui.feedback deriva su alcance con AST en vez de una tupla estatica.
- Soporte para ast.Attribute y ast.Name en las llamadas a feedback.
- Test con arbol sintetico de 4 modulos en run_tests.py.

### Outcome
- Commits: `pending`
- Tests: 80/80 PASS (75 backend + 5 UI headless)
- Docs: STATUS.md, AGENTS.md, README.md, testing-guide.md actualizados

### Impact
Se eliminan tres puntos ciegos de diagnostico y verificacion en el tooling que vigila la calidad del producto. El recuento total de tests asciende a 80 y queda protegido por deriva automatica mediante AST.

---

## [CYCLE-026] 2026-09-30 23:05 — pack-telemetry-feedback
**Área**: Gaming & Telemetría UX
**Change**: openspec/changes/2026-09-30-pack-telemetry-feedback/
**Estado**: COMPLETED — **VERDICT FINAL: PASS**
**Models**:
- Paso 1 (Buscar): heredado del turno (backlog vacío → rotación; `TASK-035` ya `completed` en `tasks.json` pero **sin** entrada en el journal, changelogs ni Paso 4: ciclo a medias heredado de la sesión anterior)
- Paso 2 (Planear): architect-review → VISTO BUENO; además **decisión de producto** en la iteración 4 (`decision-portada-pack-vacio.md`, `TASK-036`, commit `4ce17ea`) con 9 criterios discriminantes y 8 mutaciones exigidas, sin cambios en `src/`
- Paso 3 (Ejecutar): openspec-dev → iteraciones 1 a 6
- Paso 4 (Auditar tests): mutation-auditor → **7 rondas**: FAIL, FAIL, FAIL, PARTIAL, FAIL, FAIL, **PASS**
- Stepper: MiniMax-M3.1 (orquestador)

### Historial de las seis iteraciones
| iter | veredicto | qué encontró |
|---|---|---|
| 1 | FAIL | `kill_pack` pintaba `"<tick> 0 procesos cerrados (0.0 MB liberados)"` en VERDE Gaming con `killed == 0`; la guarda AST era una lista de 3-4 nombres de método |
| 2 | FAIL (80 mutaciones, 58 muertas, **21 supervivientes**) | El fix de la iteración 1 announcementaba lo que hacía pero dejaba **una tercera puerta** (`on_kill_selected`) mintiendo en verde, el bloque de cancelación del temporizador **duplicado byte a byte** con la sonda instrumentando solo una mitad, cuatro ramas sin ejecutar, y cinco afirmaciones documentales falsas |
| 3 | FAIL (3 supervivientes) | La ronda 3 cerró las tres puertas de feedback, el formateador común, los temporizadores de las dos puertas, el umbral `killed == 1`, el orden de la 4-tupla, el alcance de la guarda AST y el alias muerto. Quedaron 3 de severidad ALTA: la **rama `start` sin ejecutar**, la **guarda AST que era una red y el doc la llamaba muro**, y el **sustantivo probado solo en la rama éxito**; más tres afirmaciones documentales falsas más (`len(to_kill)`, la matriz de mutaciones inflada e irreproducible, y "las dos vistas") |
| 4 | PARTIAL → FAIL → FAIL → **PASS** | Cerró las tres de ALTA con test y ejecutó la decisión de producto TASK-036. Las rondas 4 y 5 model's Subsequentaron dos bugs vivos más: **D5** (el verbo de la puerta de apagar salía de `pack.default_action`, así que un pack recién creado decía "iniciar" al pulsar **Apagar** — la primera acción de un usuario recién instalado) y **K-a** (el **segundo** punto de la doble guarda de `kill_pack` sin un solo test, con el doc afirmándolo guardado, y mutarlo lanzaba un apagado con lista vacía tras consumir la doble pulsación). Ronda 6: **P-d** (tarjeta con `"KILL"` congelado), el **default silencioso** de `VERBOS`, y el **nº de tests caducado en tres ficheros sin declarar**. Ronda 7: **PASS**, 43/43 mutaciones de `src/` aniquiladas por `AssertionError`. |

### Iteración 7 — cierre (VIGENTE, amplía la tabla de la iteración 4)
Ronda final del `mutation-auditor`: **46 mutaciones + 15 controles negativos de validador**,
**43 muertes de `src/` por `AssertionError`**, 0 supervivientes de producción.
Clasificación exigida por el Stepper: **0 sin cobertura**, 1 equivalente (mutante propio del
auditor), 2 inertes/manipulación de detector. La matriz del dev (`_matrix_c26.py`) da **30/30**
y fue reproducida con un driver independiente, no aceptada como fuente.

| Foco | Veredicto | Evidencia |
|---|---|---|
| K-a (2º punto de la doble guarda) | **MUERE por aserción** | `llamadas_cierre == 0`: "el pack perdió sus apps ENTRE las dos pulsaciones: la segunda guarda de kill_pack tiene que avisar, no lanzar kill_pack_apps([]) después de haber co…" |
| K-a · control de carga | **VIVE por diseño, y es lo correcto** | con solo 2 lecturas **y** sin la aserción `lecturas == 3` la prueba pasa: esa aserción es lo único que distingue "midió el 2º punto" de "midió el 1º por accidente". Comprobado en las dos direcciones |
| P-d (tarjeta) | **MUERE** × 4 | literal `KILL`/`START`/vacío y `upper()`→`lower()`; vía real `refresh_dashboard` → `cget("text")` |
| `VERBOS` sin default silencioso | **MUERE** × 5 | `.get` con default, verbo cableado en ambas puertas, `KeyError` silenciado, verbo como clave del mapa, default del modelo a `"kill"` |
| Guard del cableado (posición) | **CONFIRMADO** | sin el guard, D5-e muere por `KeyError`; con el guard primero, muere por `AssertionError` nombrando fichero y línea. El dev lo movió al principio por esto y el auditor lo verificó |
| Regresión R5 | **21/21 MUEREN** | 0 crashes, 0 anclas caducadas |
| Call-sites y hilos | **sin sexto lado** | 3 call-sites / 4 invocaciones de la familia `(texto, color)`, 2 de `es_pack_inerte`, 9 `Thread` en `src/` (3 fuera de vistas + 6 en 5 métodos de 3 clases), ninguno fuera de `PERMITIDOS` |
| `validate_docs.py` check 7 | **13/15 controles limpios** | 28 en `AGENTS.md`, invocación borrada, `def` sin invocar, fila de tabla borrada, línea de `README` borrada, fichero ausente, forma alternativa, fila duplicada → todos FAIL con mensaje útil |

**Deuda nueva, no bloqueante** (el auditor la measured y no la considera oculta):
- **MEDIA**: `validate_docs.py` revienta con `SyntaxError`/`FileNotFoundError` si `run_tests.py`
  no se parsea, y su rama `if n_tests is None:` es **código muerto** —`_recuento_de_tests` lanza,
  nunca devuelve `None`. Guarda que no guarda. No produce falso verde (rc=1), es agujero de
  diagnóstico, no de detección.
- **BAJA**: residuo cosmético en el mensaje del check 7 (`invocado y NO definido: .`).
- **BAJA**: el guard AST de los llamantes tiene **lista de ficheros fija**; un tercer módulo que
  cablee un verbo no lo encuentra.
- **BAJA**: el guard AST no tiene prueba de sí mismo (`G-1`, guard→rama muerta, vive con código sano).
- **Anclas caducadas fuera del alcance del dev** (las cierra el orquestador):
  `decision-portada-pack-vacio.md:9-15` —además de caducado, **falso**: afirma una duplicación
  byte a byte que TASK-036 eliminó— y `docs/ai/data-models.md:377-378` (`pack_manager_view.py:100`
  → hoy `:227`; `gaming_service.py:16` → hoy un comentario).

**Correcciones al propio briefing del orquestador** (registradas para que no se repitan):
el conteo de formateadores es **4**, no 5 (el auditor erró en R5/R6; verificado con `ast` sobre
`feedback.py`), y el briefing-guía decía "4 S1-*" cuando el repo tiene 3 (S1-a/b/c).

### Iteración 3 — mutaciones verificadas a mano (TABLA RETIRADA, ver nota)
Reproducidas con un script temporal que reescribía `src/` **en el sitio del árbol real**. Esa
tabela declaraba "15 mutaciones, 15 muertas, 0 supervivientes" y **no es reproducible**:

* la #13 (`kill_pack` deja de avisar del pack inexistente) murió por un
  `AttributeError: 'NoneType' object has no attribute 'is_gaming'`, es decir por un **crash**,
  no por una aserción: un mutante que revienta el código no demuestra que el test lo detects;
* la #15 (el sustantivo se ignora) sobrevivió en la primera pasada y se dio por cerrada con un
  caso que solo miraba la rama de éxito. La afirmación "el sustantivo se ignora" era cierta
  para **una** de las dos ramas que lo usan;
* el utillaje `_matrix_c26.py` que acompaña al auditor, **reventaba** en la mutación 5 de 12
  (`AssertionError: no se encontró el ancla de M6`) y lanzaba 2 de las 3 sondas, así que la
  tercera puerta nunca estuvo en la tabla que el doc daba por buena.

**Las quince filas NO se conservan aquí.** Una tabla de mutaciones que nadie puede reproducir
es peor que no tenerla: parece cobertura y no lo es. Quedan en el historial (`git log`, commit
de la iteración 3) como registro de lo que se midió entonces; la tabla vigente, con su salida
literal, es la de la iteración 4.

### Iteración 4 — mutaciones verificadas con salida real (VIGENTE)
`python _matrix_c26.py`, que ahora **sí** se puede ejecutar: copia el árbol a `%TEMP%`, aplica
una mutación, purga `__pycache__` y corre **las tres sondas** en un subproceso. Un ancla que
no se encuentra es un **error duro**, no una mutación saltada. Salida literal del 2026-09-30:

```
CONTROL (sin mutar): rc=0 -> VERDE
M-A  execute_pack vuelve al return mudo (el silencio)          MUERE  | un pack no gaming y vacio SE AVISA, no se traga en silencio
M-B  el verbo se cablea a 'apagar' en vez de mapearse          MUERE  | aviso preventivo de pack vacio: "... no tiene apps que apagar"
M-C  el aviso del pack vacio se pinta en el color de marca     MUERE  | el aviso de pack inerte es de ATENCION
M-D  la guarda se queda sin sitio                               MUERE  | un pack no gaming y vacio SE AVISA, no se traga en silencio
M-E  se borra el diagnostico del Gaming Mode inerte            MUERE  | el Gaming Mode inerte se diagnostica
M-F  es_pack_inerte con 'or' en vez de 'and'                   MUERE  | se esperaba 1 worker secundario, se crearon 0
M-G  el aviso reusa _inline_status                             MUERE  | el aviso va sobre SURFACE_ALT, no sobre el fondo CANCEL
M-H  se borra la clausula 'freed_mb <= 0' de clausula_mb       MUERE  | cerrar un proceso sin liberar MB no puede inventar una cifra de RAM
S1-a _run_start intercambia launched y failed                  MUERE  | el worker de arranque tiene que entregar launched y failed sin intercambiarlos
S1-b _run_start arranca start_pack_apps([])                    MUERE  | la rama start arranca SUS apps, no una lista vacia: llego []
S1-c _run_start publica en _show_banner con el NOMBRE          MUERE  | el after debe publicar en _show_start_banner
S2-a la guarda vuelve a no bajar por getattr/setattr            MUERE  | la guarda no ve los accesos dinamicos a la vista
S2-b la guarda vuelve a ignorar ast.Delete                     MUERE  | la guarda no ve los `del` sobre la vista
S2-c la guarda vuelve a mirar solo call.func                   MUERE  | no ve self.<attr> como ARGUMENTO de una llamada permitida
S3   el sustantivo se cablea a 'procesos' en la rama 'nada'    MUERE  | el sustantivo tambien se usa en la rama 'nada'
R-1  clasificar_cierre dice siempre EXITO                      MUERE  | nada que cerrar dice exactamente eso
R-2  _show_banner deja de refrescar la barra de reposo         MUERE  | _show_banner tiene que refrescar la barra de reposo
R-3  se borra la cancelacion del auto-ocultado previo          MUERE  | el banner nuevo debe cancelar el auto-ocultado anterior
R-4  el worker de la portada vuelve a tirar failed/skipped     MUERE  | el worker tiene que entregarle a _show_banner el resultado completo
R-5  la guarda AST anulada (return [] siempre)                 MUERE  | el detector no ve las tres infracciones de control

supervivientes: ninguno
```

**20 mutaciones, 20 muertes, 0 supervivientes** (tabla de la iteración 4; **21** desde la iteración 6,
ver más abajo). Las ocho primeras son las que exige
`decision-portada-pack-vacio.md` §4 (M-A a M-H). Las tres `S1-*` son las de la rama `start` que
no se ejecutaba; las tres `S2-*` son "se devuelve el detector a su versión anterior" y mueren en
sus propios controles sintéticos; `S3` es el sustantivo en la rama `nada`; y las cinco `R-*` son
regresión de lo que las iteraciones 2 y 3 ya cerraron. Las que mueren por aserción y no por
crash se distinguen en la salida: en esta tabla **las veinte mueren por `AssertionError`**, que
es lo que hace que la tabla signifique algo.

### Iteración 6 - el superviviente D5 y el cierre de la tabla (2026-10-01)

**Qué era D5.** El `mutation-auditor` cerró el ciclo con **un solo superviviente**, y no era un
hueco de cobertura sino **un bug vivo en producción**: el espejo exacto del que la iteración 5
cerró en `start_pack`. Esa iteración ató el verbo al **método** (`mensaje_sin_apps(pack.name,
"start")`, `pack_manager_view.py:527`) y dejó el otro lado del **mismo helper** atado al pack.
`_aviso_pack_inerte` es la puerta de **apagar** y la cableaba con `pack.default_action`, así que:

```
pack recien creado: apps=[] is_gaming=False default_action='start'
usuario pulsa [Apagar]  ->  "no tiene apps que INICIAR"
```

Cadena verificada de punta a punta: `on_new_pack` → `create_user_pack(pack_id, name, [])`
(`pack_manager_view.py:432`) → `Pack(...)` sin `default_action` (`pack_service.py:638`) → el
default del modelo `"start"` (`models.py:54`) → tarjeta con **los dos** botones (`:253` ⛔ Apagar /
`:264` 🚀 Iniciar) → `kill_pack` → `_aviso_pack_inerte` → verbo de la puerta equivocada. No era un
caso límite: es la **primera acción de un usuario recién instalado**.

**Por qué la suite no lo veía.** El Gestor se probaba con pack **gaming** inerte (inmune: lo
diagnostica `_aviso_pack_inerte` antes de llegar al aviso de apps) y con un **id inexistente**
(regresa antes de leer el pack). No existía ningún `kill_pack` con pack **no gaming vacío**, que es
la única rama que produce el verbo: la tabla del auditor lo medía así y las dos filas
`default='kill'` / `default='start'` salían idénticas al código correcto salvo en la que el
mutante cambiaba.

**Arreglo.** `_aviso_pack_inerte` cablea `"kill"`, con el argumento que ya estaba escrito para
`start_pack` en el mismo fichero. Y el caso que lo ata: `Pack(id="recien", apps=[],
default_action="start")` en `kill_pack`, con el texto exacto **"no tiene apps que apagar"**. El
pack es **no gaming a propósito**: con `is_gaming=True` el diagnóstico del gaming inerte cortaría
antes y el assert moriría por otra cosa, que es exactamente el falso verde que hay que evitar.

**Los dos veredictos de mutación de `:469`** (medidos sobre copia en `%TEMP%`, `src/` nunca en
sitio, control en verde antes de mutar):

```
D5-a  mutado a pack.default_action  MUERE  | el verbo lo decide la PUERTA que se esta pulsando
                                                (aqui apagar), no el `default_action` del pack:
                                                Texto: "'Mi Pack' no tiene apps que iniciar."
D5-b  mutado a "start" a pelo        MUERE  | (la misma asercion, mismo veredicto)
```

**La tabla del ciclo queda en 21/21, 0 supervivientes** (`python _matrix_c26.py`, 2026-10-01,
`D5` incluida). El recuento de tests **sigue siendo 78**, comprobado **con parser**
(`ast` sobre `run_tests.py`: 78 `def test_` a nivel de módulo, sin duplicados), no supuesto: el
caso nuevo vive **dentro** de `test_el_feedback_de_pack_dice_la_verdad`, como los dos bloques de la
iteración 5.

### Iteración 5 - D1 a D4, medidas aquí y transcritas al `testing-guide.md`

La iteración 5 añadió dos bloques a la sonda (el verbo atado al método en `start_pack` y el
contrato de canal no vacío) y **no dejó su tabla de mutaciones escrita**: `testing-guide.md` seguía
diciendo 20/20 y etiquetaba la fila como "iter 3 / TASK-036 (iter 4)". Medidas ahora sobre copia,
con salida literal, y transcritas a `docs/ai/testing-guide.md`:

```
D1  start_pack vuelve a cablear el verbo al pack (pack.default_action)  MUERE
D2  start_pack cablea el verbo a 'kill' a pelo                          MUERE
D3  el canal inline de la base pinta fondo CANCEL                       MUERE
D4  el aviso del pack vacio pierde su texto (canal vacio)               MUERE
```

**4 mutaciones, 4 muertes, 0 supervivientes.** La lección de D1, generalizable y ya escrita en el
`testing-guide.md`: para afirmar que un valor **no** está cableado a un campo, el fixture tiene que
hacer que ese campo valga **lo contrario**. El pack vacío que ya había traía `default_action="start"`
de serie, así que `"start"` y `pack.default_action` daban el mismo texto y la convención quedaba sin
medir. D5 es el mismo error con la puerta cambiada.


### Pendiente de este pase
- `CHANGELOG.md` y esta entrada cierran el pase, pero **no cierran el ciclo**: el Paso 4 sigue
  siendo del `mutation-auditor` y TASK-036 sigue `pending` en `.taskmaster/tasks.json` a
  propósito (la marca el orquestador según el veredicto).
- **No se ha mutado `src/` en sitio en esta iteración**: todas las mutaciones se aplican a una
  copia en `%TEMP%`.

---

## [CYCLE-025] 2026-09-30 21:08 — testing-quality-expansion
**Área**: Testing & Calidad
**Change**: openspec/changes/2026-09-30-testing-quality-expansion/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): inherit
- Paso 2 (Planear): architect-review → VISTO BUENO CON DIRECTRICES OBLIGATORIAS
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO
- Paso 4 (Auditar tests): mutation-auditor → VERDICT: PASS (7/7 mutantes eliminados)

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| M1 (Strict bools) | Relajar a `is_favorite: bool = Field(default=False)` (permite coerción laxa de `"true"` o `1`) | killed | `test_models_strict_validation_and_contracts capturó coerción de is_favorite` |
| M1b (Strict bools) | Relajar a `is_gaming: bool = Field(default=False)` (permite coerción laxa de `"true"` o `1`) | killed | `test_models_strict_validation_and_contracts capturó coerción de is_gaming` |
| M2 (Literal action) | Cambiar tipo a `default_action: str = "start"` (permite `"purgar"` o `"KILL"`) | killed | `test_models_strict_validation_and_contracts capturó default_action inválida` |
| M3a (Extra allow) | Cambiar a `ConfigDict(extra="ignore")` en `Pack` | killed | `test_models_strict_validation_and_contracts detectó pérdida de meta_custom` |
| M3b (Extra allow) | Cambiar a `ConfigDict(extra="ignore")` en `AppData` | killed | `test_models_strict_validation_and_contracts detectó pérdida de legacy_profiles` |
| M4 (Defaults) | Alterar `exe_path="unknown"` o `category="Otros"` en `ProcessInfo` | killed | `test_models_strict_validation_and_contracts detectó desalineación de defaults` |
| M5 (Destrucción UI) | Omitir `self.current_view.destroy()` en `MainWindow._clear_content` | killed | `test_main_window_navigation_transitions detectó vista previa aún viva con winfo_exists()` |
| M6 (Afordancia nav) | Invertir o alterar tokens de borde en `MainWindow._set_active_nav` | killed | `test_main_window_navigation_transitions detectó fallo de estilos activo/inactivo` |
| M7 (Transición UI) | No instanciar o no reasignar `self.current_view` a la clase esperada | killed | `test_main_window_navigation_transitions detectó clase incorrecta en current_view` |

### What
- Implementación de la prueba discriminante `test_models_strict_validation_and_contracts()` en `run_tests.py`:
  - Valida el rechazo de coerciones laxas (`"true"`, `"false"`, `1`, `0`) en `Pack.is_favorite` e `is_gaming` mediante `strict=True`.
  - Valida la restricción estricta de `default_action` a `Literal["start", "kill"]`, rechazando valores no reconocidos (`"purgar"`, `"KILL"`, `""`, `None`).
  - Valida la supervivencia y retención de metadatos adicionales en `Pack` y `AppData` vía `extra="allow"`.
  - Valida los valores canónicos por defecto de `ProcessInfo` (`exe_path=""`, `category="⚪ Otros"`, `priority="none"`).
- Implementación de la prueba headless de integración `test_main_window_navigation_transitions()` en `run_tests.py`:
  - Instancia `MainWindow` sobre un contenedor headless con `root.withdraw()` y servicio de persistencia aislado (`_pack_service_temporal()`).
  - Verifica la vista inicial `DashboardView` y el estado activo del botón de portada (`theme.ACCENT`, `border_width=2`).
  - Navega a `PackManagerView` (`_show_packs()`), verificando la destrucción física del widget previo (`not winfo_exists()`) y la conmutación de estilos en `btn_nav_packs`.
  - Navega a `ProcessManagerView` (`_show_process_manager()`), verificando destrucción previa, conmutación de estilo y bombeo en mainloop para la carga asíncrona de procesos.
  - Navega de regreso a `DashboardView` (`_show_home()`) y ejecuta el cierre limpio de Tcl/Tk.
- Registro de los nuevos tests en `run_tests.py` elevando la suite oficial a **75 tests** (73 backend + 2 headless UI).
- Actualización de documentación viva en `docs/ai/testing-guide.md`.

### Outcome
- Commits:
  - `d4feeb8` (plan: registrar TASK-034 en tasks.json y openspec)
  - `2bc869e` (feat: pruebas de navegacion UI y contratos Pydantic)
- Tests: 73 backend + 2 headless UI PASS (0 fallos).
- Docs: `validate_docs.py` (70 OK, 0 FAIL).

### Impact
Se eliminan puntos ciegos críticos en la suite de pruebas sin abrir ventanas ni introducir lentitud. La navegación completa entre las tres pantallas principales y el esquema de modelos quedan cubiertos contra regresiones accidentales de tipado o ciclo de vida.

---

## [CYCLE-024] 2026-09-30 20:53 — scan-latency-optimization
**Área**: Rendimiento & Latencia
**Change**: openspec/changes/2026-09-30-scan-latency-optimization/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): inherit
- Paso 2 (Planear): architect-review → VISTO BUENO CONDICIONADO (4 directrices críticas)
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO
- Paso 4 (Auditar tests): mutation-auditor → VERDICT: PASS (6/6 mutantes eliminados)

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| M1 (Escaneo ligero) | Reintroducir `exe` en `psutil.process_iter` y asignar `exe_path` ansiosamente | killed | `test_scan_latency_and_lazy_exe_resolution falló: exe_path no estaba vacío en escaneo general` |
| M2 (Resolución lazy) | Modificar `get_process_exe_path` para retornar siempre `""` | killed | `test_scan_latency_and_lazy_exe_resolution falló: la resolución lazy devolvió cadena vacía para PID propio` |
| M3 (Robustez PID) | Quitar guarda `pid <= 0` o captura de `ValueError` en `get_process_exe_path` | killed | `test_scan_latency_and_lazy_exe_resolution falló: PID negativo levantó excepción sin degradar a ""` |
| M4 (UI on_add_to_pack) | Omitir llamada a `get_process_exe_path` en `on_add_to_pack` | killed | `test_scan_latency_and_lazy_exe_resolution falló: on_add_to_pack no resolvió ruta absoluta` |
| M5 (Blindaje AST) | Desplazar líneas 33-48 de `SYSTEM_PROTECTED_PROCESSES` en `process_service.py` | killed | `test_la_documentacion_del_blindaje_no_puede_desfasarse detectó desplazamiento AST` |
| M6 (Headless View) | Acceso directo a `self.process_service` en vez de `getattr(self, ...)` en UI | killed | `test_el_gestor_guarda_la_ruta_absoluta falló por AttributeError en vista headless` |

### What
- Optimización de latencia en `ProcessService.get_running_processes`: eliminación de la consulta ansiosa de `exe` en `psutil.process_iter` sobre cientos de procesos vivos (la cual disparaba excepciones internas `AccessDenied` e I/O de tokens en Windows).
- Incorporación del método `get_process_exe_path(pid: int) -> str` en `ProcessService`, con captura defensiva de `(psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, OSError, ValueError)` y retorno seguro de `""` ante PIDs inválidos o sin privilegios.
- Consumo defensivo en `ProcessManagerView.on_add_to_pack`: si `exe_path` no viene precargada, se consulta bajo demanda usando `getattr(self, "process_service", None)` para preservar la compatibilidad con harnesses headless.
- Optimización del bucle caliente de escaneo usando `ProcessInfo.model_construct(...)` (ahorrando ~2.200 validaciones de campo Pydantic por escaneo).
- Precomputación de `_CAT_ORDER_IDX` a nivel de módulo colocada después de la línea 56 para respetar la posición estricta (L33-48) de `SYSTEM_PROTECTED_PROCESSES` exigida por la prueba AST de sincronización documental.
- Normalización estricta de nombres con corte de sufijo (`[:-4]` si termina en `.exe`), evitando corrupciones por reemplazo global.
- Incorporación de la prueba discriminante y benchmark `test_scan_latency_and_lazy_exe_resolution` en `run_tests.py`.
- Actualización de documentación técnica en `docs/ai/architecture.md` (§7) y `docs/ai/testing-guide.md` (suite actualizada a 73 tests).

### Outcome
- Commits:
  - `7eb6c5a` (plan: registrar TASK-033 en tasks.json y openspec)
  - `142fdc1` (feat: optimizar latencia de escaneo y resolucion lazy de exe_path)
- Tests: 72 backend + 1 headless UI PASS (0 fallos).
- Docs: `validate_docs.py` (68 OK, 0 FAIL).

### Impact
Reducción drástica del tiempo de escaneo en frío en Windows 11 de más de ~31 ms a tan solo 5.53 ms (~5.6x a ~8x de aceleración), eliminando lag perceptible en la UI durante el refresco de procesos y lanzamiento de Gaming Mode sin comprometer el blindaje anti-brick ni la separación de capas.

---

## [CYCLE-023] 2026-09-30 20:35 — process-db-expansion
**Área**: Base de Datos & Procesos
**Change**: openspec/changes/2026-09-30-process-db-expansion/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): inherit
- Paso 2 (Planear): architect-review / process-db-updater
- Paso 3 (Ejecutar): process-db-updater & openspec-dev → IMPLEMENTADO
- Paso 4 (Auditar tests): mutation-auditor → VERDICT: PASS (11/11 mutantes eliminados)

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| M1a (Anti-brick) | Inyectar `csrss` cerrable (`Productividad`/`high`) | killed | `test_no_system_process_is_killable detectó proceso crítico closable` |
| M1b (Anti-brick) | Inyectar `lsass` con semáforo no-rojo | killed | `test_no_system_process_is_killable detectó proceso vigilado sin rojo` |
| M2a (Categoría) | Modificar categoría de `braveupdate` a `? Otros` | killed | `test_category_emoji_alignment detectó categoría huérfana` |
| M2b (Categoría) | Modificar categoría de `braveupdate` a `⚪ Otros` (espacio erróneo) | killed | `test_category_emoji_alignment detectó categoría no presente en PROCESS_CATEGORIES` |
| M2c (Categoría) | Glifo alterado `🟩 Productividad` | killed | `test_category_emoji_alignment detectó glifo no alineado con config` |
| M3a (Categoría) | Eliminar `category` de `braveupdate` | killed | `test_category_emoji_alignment / test_process_db_schema_integrity detectó campo faltante` |
| M3b (S1, Prioridad) | Eliminar `priority` de `braveupdate` | killed | `test_process_db_schema_integrity detectó ausencia de campo obligatorio 'priority'` |
| M3c (S1, Descripción) | Eliminar `description` de `braveupdate` | killed | `test_process_db_schema_integrity detectó ausencia de campo obligatorio 'description'` |
| M3d (S1, Prioridad) | `priority: "invalido"` en `braveupdate` | killed | `test_process_db_schema_integrity detectó prioridad fuera de {'high','medium','low','none'}` |
| M-KeyExe (Esquema) | Clave con extensión `.exe` | killed | `test_process_db_schema_integrity detectó clave terminada en .exe` |
| M-DescEmpty (Esquema) | `description: ""` vacía | killed | `test_process_db_schema_integrity detectó descripción vacía` |

### What
- Expansión de `assets/process_db.json` con 8 nuevas entradas reales obtenidas por escaneo con `psutil`: `braveupdate`, `xboxgamebarwidgets`, `xboxpcappft`, `whatsapp.root`, `crossdeviceresume`, `lightingservice`, `powertoys.mousewithoutbordershelper`, `acpowernotification` (total: 81 entradas).
- Blindaje anti-brick estricto: cero colisiones con `SYSTEM_PROTECTED_PROCESSES:33-48`. Procesos de hardware y overlays asignados a `🔴 Overlays e Info` (`priority: "none"`), quedando blindados ante Gaming Mode por la barrera roja G-2.
- Detección y erradicación del mutante superviviente S1: implementación de la sonda `test_process_db_schema_integrity()` en `run_tests.py` (L343) que valida estructura de diccionario, claves normalizadas sin `.exe`, categorías cerradas en `PROCESS_CATEGORIES`, prioridades válidas y descripciones no vacías.
- Actualización de documentación técnica en `docs/ai/data-models.md` y `docs/ai/testing-guide.md` (suite actualizada a 72 tests).

### Outcome
- Commits:
  - `f2adf2b` (plan)
  - `3e24a1e` (feat: expandir process_db.json a 81 entradas)
  - `091386c` (fix: cerrar mutante S1 con test_process_db_schema_integrity)
- Tests: 71 backend + 1 headless UI PASS (0 fallos).
- Docs: `validate_docs.py` (66 OK, 0 FAIL).

### Impact
Ampliación segura y verificada de la base de conocimiento local de procesos de Windows sin alterar contratos arquitectónicos ni runtime de ejecución. La nueva sonda de esquema previene corrupciones y omisiones silenciosas de metadatos en futuros ciclos.

---

## [CYCLE-022] 2026-09-30 20:15 — ui-visual-refresh
**Área**: Diseño & UI / Micro-UX
**Change**: openspec/changes/2026-09-29-ui-visual-refresh/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): inherit
- Paso 2 (Planear): architect-review → VISTO BUENO PARA IMPLEMENTAR (Opción A adoptada)
- Paso 3 (Ejecutar): openspec-dev → IMPLEMENTADO
- Paso 4 (Auditar tests): mutation-auditor → VERDICT: PASS (6/6 mutantes eliminados)

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| UI-002a (Cero hex) | Inyectar `fg_color="#123456"` en vista | killed | `test_no_literal_colors_in_views detectó literal hex suelto vía AST` |
| UI-002b (Tokens) | Modificar `FONT_SIZES` o borrar token | killed | `test_theme_tokens_complete detectó token faltante / tupla de fuentes alterada` |
| UI-010 (WCAG AA) | Degradar `TEXT_MUTED` a `#555555` (< 4.5:1) | killed | `test_contrast_wcag_aa detectó ratio 2.50:1 inferior a 4.5:1` |
| UI-007 (Hit targets) | Reducir botón a `width=20` o `height=24` | killed | `test_hit_targets_minimum detectó botón con dimensión menor a 28x28px` |
| UI-012b (Contrato semántico) | Cambiar `GAMING` a `#c22d2d` o contaminar semáforo | killed | `test_semantic_color_contract detectó violación de paleta Gaming/Peligro` |
| UI-006 (Icono real) | Renombrar o corromper `assets/woptimizer.ico` | killed | `test_woptimizer_ico_exists_and_valid detectó archivo ausente o no-ICO` |

### What
- Sistema centralizado de tokens en `src/woptimizer/ui/theme.py`: roles semánticos de color (`SURFACE`, `ACCENT`, `GAMING`, `DANGER`), escala fija de 6 tamaños y 3 radios, funciones de luminancia y contraste WCAG 2.1 AA.
- Resolución de contradicción de marca: adopción de Opción A (Gaming = verde `#1DB954`, peligro exclusivo rojo `#c22d2d`).
- Icono oficial de aplicación `assets/woptimizer.ico` (multi-tamaño: 16 a 256px), cableado en `app.py` (`root.iconbitmap` y `pystray.Icon`).
- Rediseño de barra de navegación (`main_window.py`): altura fija estricta de 44px (`pack_propagate(False)`), hover, y estado activo unificado en `_set_active_nav` con borde de acento y `text_primary`.
- Portada (`DashboardView`): banda de telemetría permanente en reposo sin `psutil` (`process_service.get_running_processes()`), reetiquetado descriptivo (`N apps · M categorías · KILL`) y reutilización de widgets en `refresh_dashboard`.
- Tarjeta de pack Gaming destacada (`pack_manager_view.py`): borde de acento verde `#1DB954` y badge `PRESET` con contraste WCAG AA 7.24:1 (`theme.SURFACE`).
- Sustitución de `CTkInputDialog` huérfano por `NewPackModal` acoplado al toplevel con `grab_set()` y centrado relativo, sin `messagebox`.
- Objetivos de puntero mínimos garantizados a `28x28px`.
- Cabeceras de categorías con fondo `SURFACE_ALT`, hover `SURFACE_HOVER` y contador explícito `(N)`.
- Responsive: `wraplength=380` en descripciones para ancho mínimo de 720px en pantallas de 14".

### Outcome
- Commits: `16ef4dc (feat)`
- Tests: 63 backend + 1 headless UI PASS (0 fallos).
- Docs: `docs/ai/ui-design-system.md` completamente actualizado como sistema de diseño estructurado.

### Impact
Consolidación completa del sistema visual y la ergonomía del frontend. Cero colores literales hardcodeados en vistas, accesibilidad WCAG AA contrast ratio certificada, separación nítida entre marca Gaming y alertas de peligro, e iconos nativos en ventana y bandeja del sistema.

---

## [CYCLE-021] 2026-09-30 18:00 — task028-debt-cleanup
**Área**: Resiliencia & Robustez / Deuda Técnica
**Change**: openspec/changes/2026-09-30-task028-debt-cleanup/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): inherit
- Paso 2 (Planear): inherit
- Paso 3 (Ejecutar): inherit
- Paso 4 (Auditar tests): inherit → VERDICT: PASS

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| FIX-010 (Logging) | `setup_logging` sin `force=True` | killed | `handlers previos no se limpian y avisos van a stderr` |
| FIX-010 (Destino) | log a stderr en lugar de archivo | killed | `test_logging_va_a_fichero_y_no_a_stderr detectó ausencia de handler de archivo` |
| FIX-018 (Versión) | desincronizar pyproject vs __init__ | killed | `test_la_consulta_de_version_no_puede_desincronizarse falló por discrepancia de strings` |
| F1 (Ilegible) | omitir captura de encoding roto | killed | `control de alcanzabilidad falló al verificar recuperación de backup` |
| Legacy root | omitir mover profiles.json v2 | killed | `test_el_archivo_legacy_esta_versionado_y_no_vuelve_a_la_raiz falló` |

### What
- Saneamiento de deuda técnica y consolidación de la suite: FIX-010 a FIX-020.
- `setup_logging` con `force=True` y rotación de log (`woptimizer.log`, max 1MB, 3 backups) invocado en `__main__` y `run_tests.py`.
- Archivo seguro de perfiles legacy v2 en `docs/archive/legacy-root-data/profiles.json` con su README, sin tocar `test_profiles_task1.json`.
- Eliminación de redundancias en `quit_app()` (`import sys`) y `process_manager_view.py` (`is_expanded = True`).
- Sincronización de versión `3.0.1.dev0` entre `pyproject.toml`, `__init__.py` y `tasks.json` con test AST hermético.
- Cierre de supervivientes de mutación y blindaje de perfiles ilegibles (F1) y protección de datos de usuario.

### Outcome
- Commits: `7a421e8`, `060fcc5`, `22464b9`, `3cc33dc`, `41e42e7`, `e35d30e`
- Tests: 57 backend + 1 headless UI PASS (0 fallos).
- Docs: `docs/ai/architecture.md`, `docs/ai/data-models.md`, `docs/ai/testing-guide.md` actualizados.

### Impact
Se liquidó la deuda técnica acumulada de la migración v2->v3. El log no crece descontrolado y no ensucia la consola, la versión está unificada y no puede desincronizarse, y la configuración legacy está documentada y archivada.

---

## [CYCLE-020] 2026-09-30 - 2026-09-30-ui-hardening
**Área**: Seguridad & Usabilidad
**Change**: openspec/changes/2026-09-30-ui-hardening/
**Estado**: COMPLETED - implementacion + matriz de mutacion propia (27/27 muertas), REVISADO por
`mutation-auditor` (FAIL: 1 hallazgo ALTA + 3 MEDIUM/LOW), ITERACION 2 cerrada con 21/21 muertas e
ITERACION 3 cerrada con 5/5 (hard link + su hermano, la COPIA) y 21/21 re-verificadas
**Models**:
- Implementacion: `openspec-dev`
- Paso 4 (Pendiente): `mutation-auditor` sobre `openspec/changes/2026-09-30-ui-hardening/tasks.md` § 0

### Decisiones de diseno (normativas, de `proposal.md`)
1. **`_resolver_app(entrada, raices=None)` es decision pura; `_lanzar(ruta)` es el efecto.** El orden de las reglas ES la seguridad: vacio/NUL → UNC → nombre pelado solo dentro de raices → `normpath` → contencion → extension → `isfile`.
2. **Sin blacklists de metacaracteres.** `C:\Program Files\Rock & Roll\game.exe` es legitima. Sin interprete no hay metacarácteres que escapar.
3. **No se resuelve con `shutil.which()`**: con `shell=False`, `CreateProcess` busca el CWD antes que el PATH (`isfile("cmd")` → False, `which("cmd")` → `C:\WINDOWS\system32\cmd.EXE`).
4. **La contencion va SIEMPRE despues de `normpath`**: `commonpath([cruda, 'C:\Program Files']) == 'C:\Program Files'` (medido) deja pasar el traversal.
5. **`os.startfile` se resuelve como atributo del MODULO en tiempo de llamada** (`getattr(os, "startfile", None)`), nunca `from os import startfile`: es lo que permite que la sonda muera por la ASERCION y no por un `AttributeError`.
6. **`ordenar_categorias` en `config.py`**, usada por los DOS sitios (por eso no pueden divergir). No se deriva de `get_safety_badge`.

### Desviaciones respecto a la spec (declaradas, no parcheadas en silencio)
- **`proposal.md` § 3.2 (firma literal de `toggle_favorite`) es INCOMPATIBLE con `tasks.md` T-27.4 caso 3.** Con `if pack is not None and pack.is_favorite: ... else: set_favorite(pack_id)`, un id inexistente cae en el `else` y llama `set_favorite("z")`, que en el servicio real **desmarca todos los favoritos y lo persiste**. Se anadio la guarda `if pack is None: return` (mutacion M23 medida). La decision de diseno (leer en vivo, `set_favorite(None)` en la segunda pulsacion, nada de `get_favorite_pack()`) se mantiene literal.
- **`tasks.md` T-27.1 caso (a) usa `r"C:\Windows\notepad.exe & del /q C:\"`, que no es Python valido** (una cadena cruda no puede acabar en backslash). Se escribio con el separador doblado.
- **El `Popen` sembrado lanza `BaseException`, no `AssertionError`**, porque el codigo viejo lo captura con `except Exception`: con `AssertionError` la reintroduccion de `shell=True` contaria `failed` y pasaria en VERDE.
- **El encargo no declaraba el segundo sitio de FIX-004** (`pack_manager_view._render_pack_card`), que es donde el usuario configura que se mata. Arreglados los dos.
- **El encargo no pedia la lista blanca de extensiones** (`.bat`/`.ps1`/`.vbs`/`.lnk` via `ShellExecute`), que es la pieza que hace aceptable `os.startfile` frente a `Popen(shell=True)`.

### Ficheros tocados
`src/woptimizer/services/process_service.py`, `src/woptimizer/config.py`,
`src/woptimizer/ui/views/process_manager_view.py`,
`src/woptimizer/ui/views/pack_manager_view.py`, `run_tests.py`,
`docs/ai/architecture.md` (§ 14 nuevo), `docs/ai/ui-design-system.md`,
`docs/ai/data-models.md`, `docs/known-issues.md` (Trampa #16), `CHANGELOG.md`,
`.taskmaster/CHANGELOG.md`.

### Mutaciones medidas (subproceso POR SONDA)
27 mutaciones, **27 muertas**, 0 supervivientes. Las 9 de la tabla de T-27.1
mueren en la asercion que nombra la spec; las 4 de T-27.2 en el caso 1/2/3; las
4 de T-27.3 (identidad, `sorted`, centinela, guarda estatica de los dos sitios);
las 4 de T-27.4 (incondicional, instantanea, `get_favorite_pack()`, id
inexistente). Detalle en el informe del dev.

### ITERACION 2 — el `mutation-auditor` dio FAIL (4 hallazgos, 1 ALTA)

**El hallazgo grave no era un fallo de codigo sino una garantia documentada que era FALSA.**
`architecture.md` §14 decia "solo se arranca lo que esta bajo las raices permitidas", y un
junction de un comando colado en `%LOCALAPPDATA%` la incumplia. El alias
`commonpath([<TEMP>\\jdir\\cmd.exe, LOCALAPPDATA])` devuelve `LOCALAPPDATA`: "contiene". Y
`os.stat(...).st_file_attributes` tampoco lo ve (`0x20`, medido) porque sigue el enlace en el
tramo intermedio.

**Arreglo: regla 8 nueva en `_resolver_app`** — resolver la ruta real (fail-closed) y repetir
contained + extension sobre ella; devolver la ruta REAL. Decisiones:
- **`os.path.realpath(ruta, strict=True)`, SIN `ctypes`.** El encargo ofrecia
  `GetFinalPathNameByHandle` por `ctypes` o `st_file_attributes`; la medicion descarta las dos: el
  atributo no ve el enlace intermedio, y `ntpath.realpath` **ya es** el envoltorio de
  `GetFinalPathNameByHandleW` (resultado medido, tambien con enlace de fichero). Menos codigo,
  mismo resultado, y la separacion de capas no se mueve: sigue siendo `services/` la que habla
  con el SO, y la UI sigue sin importar nada nuevo.
- **Extension en el alias Y en el destino.** `.exe` -> enlace a un `.bat` **de una raiz
  permitida** pasaba la contencion real y esquivaba la lista blanca entera (`ShellExecute` ->
  `cmd.exe /c`). Este agujero NO venia en el encargo y es de la misma familia.
- **Las raices se resuelven tambien.** Con la raiz lexica, un junction en un tramo de
  `%LOCALAPPDATA%` rechazaria apps legitimas: el falso negativo. Sin sonda para esto, el arreglo
  del "siempre" se colaba por el otro lado.
- **Se devuelve la ruta real, no la escrita**: lo que se valida es lo que se arranca.
- **M10 (contencion por prefijo)**: sonda nueva con hermano real + ficheros reales.
- **Guarda anti-`shell=True`**: era CIEGA a `ast.Attribute` —`subprocess.Popen(app, shell=True)`,
  la grafia EXACTA del bug original, pasaba. Ampliada a atributo + mapa de alias de `ImportFrom`,
  y `shell` ya no exige `is True` (cualquier valor que no sea literal falso es interprete).
  Extraida a `_hallazgos_shell_true(fuente, etiqueta)`, usada por las DOS sondas: dos guarditas
  con coberturas distintas son cero guardas. La sonda nueva exige tambien los falsos positivos
  que NO deben marcarse.
- **Mayusculas: `os.path.normcase` en los dos lados, y NO se documenta como limitacion.**
  `normcase` no ensancha el conjunto aceptado: declara la verdad del SO, asi que lo que entra es
  exactamente lo que el SO abriria, y encima siguen aplicando la contencion y la extension
  REALES. No sustituye a `commonpath` (el hermano de prefijo entraria igual), por eso M10 tiene
  sonda propia. La sonda prueba las DOS direcciones: con `normcase` solo en un lado, la mitad
  de los casos sigue fallando.

**Ficheros tocados (iter 2)**: `src/woptimizer/services/process_service.py`, `run_tests.py`,
`docs/ai/architecture.md` (§14, garantia corregida), `docs/ai/testing-guide.md` (56 tests + tabla
de sondas), `docs/known-issues.md` (Trampa #17), `openspec/changes/2026-09-30-ui-hardening/tasks.md`
(§1b), `CHANGELOG.md`, `.taskmaster/CHANGELOG.md`, `_mutmatrix_t027_iter2.py` (nuevo, la sonda
ejecutable de la matriz).

**Mutaciones medidas (iter 2, subproceso POR SONDA)**: `_mutmatrix_t027_iter2.py` copia `src/` a
`%TEMP%` por mutacion, muta el **producto** y lanza **una sonda por subproceso**.
**21 mutaciones, 21 muertas, 0 supervivientes.** A1-A10 (junction: borrar la resolucion real,
contencion real siempre True, extension solo en el alias, `realpath` sin `strict`, rechazar todo
reparse point, devolver la ruta lexica, fail-open, raices lexicas, sin motivo en el log,
comparar la lexica contra las raices reales), M10 (`startswith`), C1-C3 (`normcase`), G1-G4 (la
guarda) y P1/P2 (reintroducir `Popen(..., shell=True)` en el producto). Hay ademas 4 **cruces
informativos** en la salida, con su motivo: una mutacion tiene que morir en la sonda que DECLARA
esa propiedad, y ninguno de esos pares es un agujero porque cada propiedad si muere en su propia
sonda.

**Deuda declarada en la iteracion 2, CERRADA en la iteracion 3 (y la DEUDA ESTABA MAL FUNDADA).**
La iteracion 2 decio, aqui, en el modulo, en `architecture.md` §14 y en `known-issues.md` (Trampa #17),
que un **hard link** (`mklink /H`) "no es un reparse point, asi que ni `realpath` ni los atributos lo
ven" y que "no es arreglable con esta regla y no hace falta". **Las dos mitades de esa razon eran
falsas**, y el hallazgo del `mutation-auditor` de la iteracion 3 es que el caso **era** cerrable:

* **"Ningun filtro de Windows lo ve" es FALSO**: `os.stat(ruta).st_nlink` vale **2** en un hard link
  (medido). Si lo ve.
* **Y da igual que lo vea, porque el hard link NO era el agujero.** Medido en esta maquina con las dos
  variantes construidas de verdad: `_resolver_app` acepta el hard link (`alias.exe` -> `payload.bat`
  fuera de las raices, `st_nlink == 2`) **y tambien una COPIA PLENA** del mismo `.bat` con nombre
  `.exe` (`st_nlink == 1`, sin un solo enlace, sin junction, sin symlink y sin privilegios). Cerrar
  solo el caso exotico habria sido seguridad de teatro: el trivial seguia abierto.
* **La variante que se ofrecio como alternativa ("rechazar solo si el destino no esta en las
  raices") NO ES IMPLEMENTABLE**: un hard link no tiene destino consultable (no hay API en Windows
  que devuelva los otros nombres de un fichero a partir de su ruta), y aunque la hubiera seria
  irrelevante, porque el atacante elige que nombre queda dentro de la raiz.
* **Y `st_nlink > 1` a pelo es un error, medido**: de **2273** `.exe`/`.com` instalados en las seis
  raices, **189 (8,32 %) tienen `st_nlink > 1`** (hasta 6), y son programas de Microsoft
  (`msinfo32.exe`, `TabTip.exe`, los auxiliares de Edge, las herramientas de Hyper-V). Rechazar
  "cualquier `st_nlink > 1`" habria roto el 8 % del software instalado. Por eso NO se ha hecho, y el
  control (6) de la sonda nueva lo prohibe explicitamente.

**El cierre es la REGLA 9 (`_es_imagen_pe`): el CONTENIDO, no el nombre.** La lista blanca de
`.exe`/`.com` siempre quiso expresar que *`.exe` significa "imagen PE", no "algo que se arranca"*, pero
se cumplia mirando el NOMBRE, y un hard link (o una copia) tiene el nombre que le pongas. La regla 9
comprueba que el fichero lleva `MZ` y la firma `PE\0\0` en el offset que declara `e_lfanew`, DESPUES de
la resolucion real, sobre el fichero que se va a arrancar de verdad. **Coste medido antes de escribirla**:
2200 de 2273 `.exe`/`.com` instalados la cumplen y **ninguno de los 189 multi-enlazados falla** (0 falsos
negativos en justo el caso que se queria cerrar); los 19 que no son appx de WindowsApps, la cache de MSI
y un `.COM` DOS de 16 bits, ninguno lanzable. Fail-closed.

**Mutaciones medidas (iter 3, subproceso POR SONDA)**: `_mutmatrix_t027_iter3.py`, **5 mutaciones, 5
muertas, 0 supervivientes** (H1 borrar la regla 9, H2 la regla que no hace nada, H3 solo `MZ`, H4
fail-open al no leer, H5 rechazar cualquier `st_nlink > 1`). Sonda:
`test_un_hard_link_no_es_una_hoja_y_el_script_no_pasa`, con **hard link real** (`os.link`, sin
privilegios) y que **falla en voz alta** si el entorno no deja construirlo.

**Y un hallazgo propio sobre las sondas, que es lo importante de este pase**: al anadir la regla 9, los
fixtures que hacian de "una app" eran ficheros **VACIOS**, y un `.exe` vacio no es un PE, asi que la
regla nueva los rechazaba **por el motivo equivocado**. Dos propiedades dejaron de estar probadas sin
que ninguna sonda se quejara: la extension real (mutacion **A3**) y la lista blanca (caso (b)). Se
detecto porque se **re-ejecuto la matriz de la iteracion 2** (no porque la suite se rompiera: la suite
estaba en verde). Corregido con el helper `_escribir_pe_minimo` y con el caso (b) ampliado: el **mismo
contenido** con `.bat` no arranca y con `.exe` si, de modo que la diferencia la tiene que hacer la
extension y no el contenido. La matriz de la iteracion 2 queda **21/21 muertas, 0 supervivientes**,
re-verificada; la de la iteracion 3 es **5/5**.

**Correccion de una afirmacion previa de este mismo changelog**: la iteracion 1 declaraba "27
mutaciones, 27 muertas" y el `mutation-auditor` midio **29 mutaciones, 28 muertas** (el
superviviente era M10, la contencion por prefijo, cerrada aqui). El numero de 27 estaba mal y
esta corregido en el sitio. Y la iteracion 2 daba por cerrada una deuda cuya **razon era falsa**: una
afirmacion de seguridad que no se sostiene no es una deuda declarada, es una garantia mal escrita.

**Nota de entorno**: los 19 directorios `wopt_mut_*` de `%TEMP%` que hay en esta maquina son de
un pase anterior (layout plano, `pack_service.py` en la raiz), no de este. Este pase no deja
residuos: ni en `%TEMP%` ni en `%USERPROFILE%`.

### Pendiente para el Paso 4
`mutation-auditor` debe repetir las 9 mutaciones de T-27.1 sobre una copia de
`src/`. Nota: si se cambia `os.startfile` por `subprocess.Popen([ruta], shell=False)`,
la lista blanca de extensiones se vuelve innecesaria **y el caso (b) debe volver a morir**.

# Changelog de pases — Motor id-pipeline

> **Registro append-only de cada ciclo completado por el motor autónomo de I+D.**
> Una entrada por pase al final del Paso 3 (Ejecutar), antes del retorno al Paso 1.
> **MANDATORY** desde el ciclo #11 (proposal `2026-09-29-id-pipeline-changelog-models`).

## Fuentes relacionadas

| Artefacto | Para qué |
|---|---|
| `.taskmaster/CHANGELOG.md` (este archivo) | Per-pass humano-legible: qué se hizo, con qué modelos, qué salió. |
| `.taskmaster/rd_journal.json` | Machine-readable: datos estructurados por ciclo (incluye `task`, `commits`, `benchmark_*`). |
| [`STATUS.md`](../../STATUS.md) | Dashboard: salud del sistema + resumen de hitos (no cada pase). |
| `openspec/changes/<id>/` | Contrato de cada cambio y su evolución. |

## Convención de modelos (definida en Sección 7 de `id-pipeline/SKILL.md`)

Modelos disponibles: `flash` (rápido, tareas triviales), `inherit` (default seguro, balance), `pro` (máxima capacidad de razonamiento, planificación compleja).

| Paso | Modelo por defecto | Override |
|---|---|---|
| 1. Buscar | `flash` | `inherit` si la búsqueda requiere contexto quirúrgico. |
| 2. Planear | `pro` | `inherit` si el cambio es trivial o el área es bien conocida. |
| 3. Ejecutar | `inherit` | `pro` para refactors con riesgo de regresión. |

## Formato de cada entrada

```markdown
## [CYCLE-NNN] YYYY-MM-DD HH:MM — <slug>
**Área**: <de la matriz de rotación>
**Change**: openspec/changes/<slug>/
**Estado**: COMPLETED | BLOCKED | ROLLED-BACK
**Models**:
- Paso 1 (Buscar): <modelo>
- Paso 2 (Planear): <modelo>
- Paso 3 (Ejecutar): <modelo>

### What
- <bullets cortos concretos, 1 frase cada uno>

### Outcome
- Commits: `<hash1>`, `<hash2>`
- Tests: <n>/<total> PASS
- Docs: <qué docs/ai/ se actualizó>

### Impact
<1-2 frases>
```

---

## Entradas

> Nota: ciclos 1-10 fueron completados ANTES de la convención de changelog. Se backfillean abajo usando los datos de `rd_journal.json`. Los modelos aparecen como `inherit (legacy — sin tracking)` por no estar registrados históricamente.

## [CYCLE-001] 2026-09-28 23:00 — 2026-09-28-v3-ui-redesign
**Área**: Arquitectura & UI
**Change**: openspec/changes/2026-09-28-v3-ui-redesign/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `inherit (legacy — sin tracking)`
- Paso 3 (Ejecutar): `inherit (legacy — sin tracking)`

### What
- Rediseño completo de 3 ventanas con CustomTkinter (Portada, Packs, Procesos).
- Migración de backend de PowerShell/WMI a `psutil`.
- Modelos de persistencia migrados a `pydantic v2`.

### Outcome
- Commits: (no registrados en journal)
- Tests: N/A en este ciclo (fue el kick-off del v3)
- Docs: arquitectura y UI redesign pendientes de documentar en docs/ai/.

### Impact
Sentó las bases de toda la v3. Cualquier cambio posterior parte de esta estructura. Sin este ciclo no existiría el resto.

---

## [CYCLE-002] 2026-09-29 01:35 — 2026-09-29-v3.1-quality-of-life
**Área**: Resiliencia & UX
**Change**: openspec/changes/2026-09-29-v3.1-quality-of-life/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `inherit (legacy — sin tracking)`
- Paso 3 (Ejecutar): `inherit (legacy — sin tracking)`

### What
- Integración de System Tray (`pystray`) en background.
- Rotación segura de backups `profiles.json.bak`.
- Logging continuo en `woptimizer.log`.

### Outcome
- Commits: (no registrados en journal)
- Tests: N/A en este ciclo
- Docs: quality-of-life no documentado en docs/ai/ (pendiente).

### Impact
Mejoró la resiliencia operacional: el usuario puede minimizar a tray, los profiles tienen recovery ante corrupción, y hay rastro de auditoría continua.

---

## [CYCLE-003] 2026-09-29 02:12 — 2026-09-29-ram-telemetry-widget
**Área**: Gaming & Telemetría UX
**Change**: openspec/changes/2026-09-29-ram-telemetry-widget/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `inherit (legacy — sin tracking)`
- Paso 3 (Ejecutar): `inherit (legacy — sin tracking)`

### What
- Banner dinámico de telemetría en `DashboardView` que muestra procesos cerrados y MB liberados tras activar packs.
- Implementación thread-safe vía `self.after(0, ...)`.
- Auto-hide a los 5s.
- Paleta: verde gaming (`#1DB954`) vs azul kill (`#4a9fd4`).

### Outcome
- Commits: `617eef8` (architect), `dc7c30c` (feat)
- Tests: N/A en este ciclo
- Docs: ui-design-system.md pendiente de actualizar con banner spec.

### Impact
El usuario ve feedback inmediato del impacto de activar un pack — clave para adopción y para entender qué mató el botón "Gaming".

---

## [CYCLE-004] 2026-09-29 02:18 — 2026-09-29-process-db-update
**Área**: Base de Datos & Procesos
**Change**: openspec/changes/2026-09-29-process-db-update/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `inherit (legacy — sin tracking)`
- Paso 3 (Ejecutar): `flash` (DB updates rutinarios — según tabla de la skill)

### What
- 4 procesos nuevos en `assets/process_db.json`: `sharex`, `crossdeviceservice`, `esrv_svc`, `dsaservice`.
- Todos marcados como `🔴 high` (bloatware/telemetría seguros de cerrar en gaming).

### Outcome
- Commits: `c362eda`
- Tests: no ejecutados (cambio de datos, no lógica)
- Docs: process_db.json mismo es la doc; no requiere docs/ai/ update.

### Impact
34 procesos catalogados total. Cobertura incremental sobre apps comunes de telemetría y captura.

---

## [CYCLE-005] 2026-09-29 02:21 — 2026-09-29-testing-quality
**Área**: Testing & Calidad
**Change**: openspec/changes/2026-09-29-testing-quality/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `inherit (legacy — sin tracking)`
- Paso 3 (Ejecutar): `inherit (legacy — sin tracking)`

### What
- 3 tests nuevos en `run_tests.py` (total 7): `freed_mb` return type, gaming pack protected, corrupted JSON recovery.

### Outcome
- Commits: `786a551`
- Tests: 7/7 PASS
- Docs: `docs/ai/testing-guide.md` actualizado con los 3 nuevos tests.

### Impact
Cobertura base de invariantes críticas: tipado de retorno, protección del pack gaming, recovery ante JSON corrupto. Las 3 son trampas documentadas en `docs/known-issues.md`.

---

## [CYCLE-006] 2026-09-29 02:23 — 2026-09-29-resilience-tray-logging
**Área**: Resiliencia & Robustez
**Change**: openspec/changes/2026-09-29-resilience-tray-logging/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `inherit (legacy — sin tracking)`
- Paso 3 (Ejecutar): `inherit (legacy — sin tracking)`

### What
- Fix: `tray_icon` no se guardaba en `self`, lo que impedía el cierre limpio del tray.
- `gaming_action` ahora con `try/except` + logging.
- `start_pack_apps` con `logger.info/warning` individual por app.

### Outcome
- Commits: `60c713d`
- Tests: pasan los 7 existentes (no se añadieron nuevos en este ciclo)
- Docs: ninguna doc nueva (cambios menores de robustez).

### Impact
Bug latente de cleanup de tray corregido. Sin el fix, al cerrar la app podía dejar el icono del system tray huérfano.

---

## [CYCLE-007] 2026-09-29 02:27 — 2026-09-29-perf-cache-hashmap
**Área**: Rendimiento & Latencia
**Change**: openspec/changes/2026-09-29-perf-cache-hashmap/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `pro` (refactor con riesgo de regresión)
- Paso 3 (Ejecutar): `pro` (refactor con riesgo de regresión)

### What
- Rewrite de `ProcessService`: hashmap O(1) para lookup de DB.
- Meta-cache memoizado (129 entries).
- Cache TTL 2s para `get_running_processes`.
- Kill invalida cache.

### Outcome
- Commits: `2fc51c3`
- Tests: pasan los 7 existentes
- Benchmark before: cold_scan 16ms, cached N/A.
- Benchmark after: cold_scan 15ms, cached 0.003ms, **~5000x speedup**.

### Impact
La lectura cacheada es prácticamente gratuita. Sin esto, abrir el Gestor de Procesos era la operación más cara de la app.

---

## [CYCLE-008] 2026-09-29 02:41 — 2026-09-29-native-toast-notifications
**Área**: Gaming & Telemetría UX
**Change**: openspec/changes/2026-09-29-native-toast-notifications/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `pro` (nueva service, requiere diseño)
- Paso 3 (Ejecutar): `inherit`

### What
- `NotificationService` nuevo que envuelve `pystray.Icon.notify` sin dependencias nuevas.
- Inyectado en `MainWindow` + 3 vistas.
- Autostart del tray en `__init__` con guard idempotente.
- 4 tests headless nuevos.
- Fix colateral: `pystray` y `Pillow` declarados en `pyproject.toml` (faltaban, rompían builds PyInstaller).

### Outcome
- Commits: `283bc16` (architect), `4797d6a` (feat)
- Tests: 5 → 9 backend, 0 fallos
- Docs: ui-design-system.md pendiente de extender con la spec de notificaciones.

### Impact
Notificaciones nativas Windows al activar packs. Bug colateral resuelto: builds PyInstaller habrían fallado sin declarar `pystray` + `Pillow` en `pyproject.toml`.

---

## [CYCLE-009] 2026-09-29 02:58 — 2026-09-29-config-category-emoji-alignment
**Área**: Base de Datos y Procesos
**Change**: openspec/changes/2026-09-29-config-category-emoji-alignment/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `pro` (debugging de bug crítico)
- Paso 3 (Ejecutar): `inherit`

### What
- **BUG CRÍTICO**: 6 de 8 categorías de `process_db.json` no existían en `config.py` por emojis invertidos, dejando todos esos procesos en `? Otros` sin semáforo.
- **Segundo bug**: `get_safety_badge` evaluaba `priority` antes que `category`, pintando 🟢 como 🔴.
- Fix de ambos + 2 tests de regresión.
- 14 procesos nuevos (navegadores, launchers, herramientas de IA) = 48 total.

### Outcome
- Commits: `31906e7` (process-db), `4977b00` (fix config)
- Tests: 9 → 11 backend, 0 fallos
- Docs: docs/known-issues.md ahora con Trampa #17 (emoji drift) + Trampa #18 (priority vs category ordering).

### Impact
6 categorías que parecían activas estaban completamente huérfanas. Bug invisible: el usuario veía categorías pero las apps caían en "Otros". Las pruebas de regresión ahora blindan contra ambos bugs.

---

## [CYCLE-010] 2026-09-29 02:52 — 2026-09-29-critical-invariant-coverage
**Área**: Testing y Calidad
**Change**: openspec/changes/2026-09-29-critical-invariant-coverage/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `pro` (caza de bugs latentes)
- Paso 3 (Ejecutar): `pro` (fix de invariante crítico)

### What
- **BUG REAL CORREGIDO**: `model_copy()` de Pydantic v2 es shallow, así que las listas del pack Gaming se compartían con `DEFAULT_GAMING_PACK`. La UI mutaba in-situ (`on_add_to_pack`), contaminando el global y haciendo que `reset_gaming_pack()` fuera un no-op silencioso.
- Fix: `model_copy(deep=True)`.
- Test verificado que DISCRIMINA (falla sin el fix).
- 8 tests nuevos para invariantes sin cobertura tras la migración v2→v3: `GamingService.should_kill_for_gaming`, `PackService` CRUD, cache TTL, kill recursivo.
- Hallazgo: los 11 `test_*.py` de la raíz están muertos (importan `process_manager` de v2). Documentados como deuda, NO borrados.

### Outcome
- Commits: `705e5f9` (tests), `1a0faa9` (fix)
- Tests: 11 → 19 backend + 1 headless, 0 fallos
- Docs: docs/known-issues.md ahora con Trampa #19 (Pydantic model_copy shallow).

### Impact
Bug latente invisible durante meses corregido. El usuario podría añadir apps al Gaming pack, cerrar la app, reabrir, y pensar que se habían perdido: era el DEFAULT_GAMING_PACK contaminado en memoria.

---

## [CYCLE-011] 2026-09-29 09:50 - 2026-09-29-git-tooling-resilience
**Área**: Resiliencia & Robustez (matriz área 1, sin tocar desde el ciclo #6)
**Change**: openspec/changes/2026-09-29-git-tooling-resilience/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit` (el modelo de la sesión; la matriz pide `flash`, se subió porque la búsqueda fue de código real, no un lookup)
- Paso 2 (Planear): `inherit` (subagente `worker` + skill architect-review; la matriz pedía `pro`, se quedó en `inherit` porque el subagente no resolvió modelo explícito)
- Paso 3 (Ejecutar): `inherit` (subagente `worker` + skill openspec-dev; coherente con la matriz)

### What
- **Fallo de integridad del pipeline, no de la app**: `git_safe_commit.py` —la unica puerta de versionado y la que AGENTS.md obliga a usar en cada cierre— capturaba CUALQUIER fallo de commit, imprimia `AVISO GIT` y salia con **codigo 0**. El pipeline lo leia como exito y el CHANGELOG (MANDATORY) registraba hashes que podian no existir.
- Ademas `git add -A` fallido era solo un warning (staging parcial silencioso) y `get_env()` activaba el repo desacoplado con un simple `os.path.exists`, sin validarlo.
- **Evidencia de que no era hipotetico**: el `.git` del arbol de trabajo esta corrupto por el VFS de Nextcloud (`fatal: bad object HEAD`); el historial solo sobrevive por el repo desacoplado en LOCALAPPDATA.
- Rehecho: contrato de 4 codigos de salida (`0/1/2/3`) con lineas canonicas `WOPT_*`, validacion real del repo (`validar_repo`), sin fallback al `.git` corrupto, y flag `--verify` de solo lectura.
- **El arquitecto corrigio 3 errores de la propuesta original**, el mas grave: decidir "nada que comitear" buscando `"nothing to commit"` en stderr depende de `LANG`/`LC_ALL` y en un Windows en espanol NO aparece nunca, lo que habria convertido un arbol limpio en un fallo. Ahora se decide con `git diff --cached --quiet` (locale-independiente).
- Tambien cerro un agujero en la linea 55: un `status --porcelain` fallido se trataba como "hay cambios" en vez de como error.
- Checkpoint de empaquetado (3 ciclos desde el #8): `force_build.py` OK, `dist/woptimizer.exe` regenerado (25.65 MB) ya con los fixes de los ciclos #9 y #10.
- Recuperados 5 ficheros modificados + 2 sin seguimiento que el ciclo #10 dejo sin comitear: precisamente porque el wrapper reportaba exito en falso.

### Outcome
- Commits: `6048f6f` (architect), `b9a31fa` (fix)
- Tests: 20 -> 21 (`run_tests.py`), 0 fallos; las 3 puertas en `rc=0` (`verify_ui_syntax.py`, `run_tests.py`, `validate_docs.py` 34 OK)
- Docs: `docs/ai/sandbox-rules.md` (seccion NUEVA "Aislamiento Git en Entornos Cloud (VFS)"), `AGENTS.md` §3, `docs/ai/architecture.md` linea 39
- **Verificacion independiente del orquestador**: los 5 comportamientos del contrato comprobados en vivo (repo sano=0, GIT_DIR inexistente=3, directorio no-repo=3, sin args=2, arbol limpio=0 con `WOPT_NOOP`), y **prueba de mutacion propia**: revirtiendo el fix el test falla con `AssertionError: ... debe salir con 3, salio con 0`, con restauracion byte-identica (SHA256 `C248F694...`).

### Impact
El pipeline deja de poder "completar" ciclos sin versionar nada. Antes, un fallo de commit era indistinguible de un commit correcto para todo el sistema; ahora es un `!= 0` que detiene el ciclo. Defecto de clase: un wrapper de seguridad que miente en su codigo de salida desactiva todas las validaciones que dependen de el (`validate_docs.py` nunca habria podido detectar un hash fantasma).

---

## [CYCLE-012] 2026-09-29 10:30 - 2026-09-29-double-tap-confirmation
**Área**: Gaming & Telemetría UX (matriz área 2, sin tocar desde el ciclo #8)
**Change**: openspec/changes/2026-09-29-double-tap-confirmation/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit`
- Paso 2 (Planear): `inherit` (subagente `worker` + skill architect-review)
- Paso 3 (Ejecutar): `inherit` (subagente `worker` + skill openspec-dev)

### What
- **REGRESION SILENCIOSA DE LA REESCRITURA v2->v3**: la v2 tenia doble pulsacion para confirmar acciones destructivas, introducida tras un incidente real (un `messagebox.askyesno` se abria POR DETRAS de la ventana, el usuario pulsaba, no veia nada y reporto "se ha roto, no mata procesos"). El patron se perdio al reescribir: grep de `messagebox|askyesno|showinfo|showwarning|_request_confirm|confirm` sobre `src/` daba **cero coincidencias**. 5 acciones destructivas-operaban sin confirmar nada.
- La mas grave: **"Cerrar Seleccionados" mata N procesos a pelo** con un solo clic; y en la portada, `refresh_dashboard` coloca los favoritos **de dos en dos** en la misma fila, asi que el boton Gaming tenia un pack vecino pegado y un dedo gordo podia matar los procesos del pack equivocado.
- Segundo fallo: `PackManagerView` **no tenia `status_label`**, o sea que sus acciones no podian dar feedback inline. Se creo.
- Implementado en **un solo sitio**: `ui/confirmation.py` con dos capas — `DoubleTapGuard` (maquina de estado pura, sin `customtkinter`, con `scheduler` inyectable, testeable headless) y `Confirmable` (mixin fino que solo toca widgets).
- Auto-revert a los ~3 s, invalidacion si cambia la seleccion entre pulsaciones, y `destroy()` en las 3 vistas para matar el `after` vivo.
- `on_kill_selected` dejo de hacer `return` mudo sin seleccion (el usuario iba a pensar que el boton estaba roto).
- Documentada la **Trampa #14** en `docs/known-issues.md`, que cierra la laguna #13 -> #14: el porque del patron ya no se pierde en la proxima reescritura.
- **El arquitecto encontro 3 errores CRITICOS en la propuesta, y 6 mas**: el boton de la portada no se llamaba "Modo Gaming" (era `f"{pack.name}\\n(...)"` y ademas *arranca* apps si la accion no es `kill`, asi que confirmar a ciegas habria metido confirmacion en acciones de arranque); el `except ValueError: pass` era **inalcanzable** desde la UI y el fallo silencioso real era que se ignoraba el retorno `False`; y `PackManagerView` no tenia `status_label`. Ademas: congelar los `ProcessInfo` habria sido un fallo de seguridad (los PIDs se reciclan en 3 s), y habia "4 vistas" cuando son 3.

### Outcome
- Commits: `fcd4f73` (architect), `30c0f11` (fix)
- Tests: 21 -> 22 (`run_tests.py`), 0 fallos; gates: `verify_ui_syntax.py` EXITO (8/8, incluido el modulo nuevo), `run_tests.py` ALL TESTS PASSED, `validate_docs.py` 35 OK / 0 FAIL
- Docs: `docs/known-issues.md` (Trampa #14), `docs/ai/ui-design-system.md` (seccion nueva), `verify_ui_syntax.py` (el helper nuevo estaba en su lista fija, si no daba verde en falso)
- **Verificacion independiente del orquestador**: commit y arbol limpios, cero `messagebox` en `src/`, Trampa #14 en la linea 282, y **prueba de mutacion propia**: anulando `arm()` el test revienta con `AssertionError` y `rc=1`, con restauracion byte-identica (SHA256 `3BAE03FB...`).
- Criterio de aceptacion corregido: "cero `confirm` en `src/`" era imposible de cumplir (el modulo se llama `confirmation.py`); acotado al grep real `messagebox|askyesno|showinfo|showwarning`.

### Impact
Se recupera una proteccion que el usuario pidio expresamente y que la reescritura borro sin dejar rastro. El patron es ahora una norma documentada con su porque, asi que la siguiente reescritura ya no lo pierde. Y el riesgo mayor que se cierra es el peor de todos en esta app: matar por error los procesos equivocados, sin aviso y sin vuelta atras.

---

## [CYCLE-013] 2026-09-29 11:00 - 2026-09-29-real-bloatware-scan
**Área**: Base de Datos & Procesos (matriz área 3)
**Change**: openspec/changes/2026-09-29-real-bloatware-scan/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit` (escaneo real con psutil, no un lookup)
- Paso 2 (Planear): `inherit` (la propuesta se auto-revisó durante la ejecución)
- Paso 3 (Ejecutar): `flash` (subagente `worker` + skill process-db-updater: escaneo + append a JSON, sin creatividad)

### What
- **Escaneo real**: 131 nombres de proceso únicos en el sistema, 48 registrados, **122 sin registrar**. Se clasificaron en tres familias con consecuencias opuestas, y confundirlas es el peor defecto posible en esta app.
- **Familia A (procesos de sistema)**: NO se registró ninguno. Matar `csrss`, `lsass` o `winlogon` deja Windows inservible.
- **Familia B (bloatware real)**: **25 entradas añadidas** (48 → 73). PowerToys, el consumo de Armoury Crate de ASUS (telemetría, fondo dinámico, sockets, debug web), language servers, actualizadores, audio enhance y varios servicios de terceros.
- **BLINDAJE ANTI-BRICK** (la mitad del trabajo): `SYSTEM_PROTECTED_PROCESSES` con 34 nombres de nivel sistema, coincidencia **exacta** sobre el nombre normalizado —nunca por subcadena, que bloquearía procesos legítimos—, aplicado en **tres puntos y por las tres vías**: saneado al cargar la DB (también protege contra `load_db_async()`, que descarga el JSON de GitLab por encima), en `_get_process_meta()` **antes** que la DB y que el fuzzy match, y en `kill_processes()` / `kill_pack_apps()`, porque el pack lo escribe el usuario a mano: un `lsass.exe` en un pack se cuenta como `skipped` y no mata nada.
- **Desviaciones deliberadas del subagente respecto a la propuesta, todas a mejor**:
  - Servicios de audio (`atkexcomsvc`, `dtsapo4service`) a **🟡 medium** en vez de 🟢 high: tocan la ruta de audio y un verde prometería audio espacial durante la partida. Además 🟡 Media no está en las `target_categories` del pack gaming, así que nunca se auto-cierran.
  - La pila de control de Armoury Crate (`armourycrate`, `armsvc`, `asus_framework`, ...) a **🔴 none** en vez de verde: es el equivalente a `icue`/`razer`/`lghub`, que en esta misma base ya están en 🔴 por perfiles de ventilación y RGB. Cerrarlos deja el equipo sin perfil de juego. Los 4 de consumo sí van en verde, que es donde está el bloatware real.
  - `mpdefendercoreservice` a 🔴 none: el proposal lo listaba como utilidad de terceros, pero el nombre es la plataforma Defender.
  - Descartados 9: `keepassxc` (matarlo con la base sin cifrar en disco la puede corromper), `lightingservice`/`telemetry_agent`/`nodoze-1.1` (origen no verificable: la descripción habría sido inventada), redundantes por fuzzy match, y `calendarapp.gui.win10` (recortado para no pasar de 25).
- **Ambigüedad resuelta**: `sihost` estaba en las listas A y C del proposal a la vez. Se resuelve como **Familia A**: es infraestructura del shell de Windows, no del entorno de trabajo. Es la lectura segura.

### Outcome
- Commit: `0ad23bb`
- Tests: 22 -> 24 (`run_tests.py`), 0 fallos; `verify_ui_syntax.py` EXITO
- Docs: `docs/ai/data-models.md` con la sección de blindaje
- **Verificacion independiente del orquestador**: 73 entradas, 34 nombres protegidos, **0 procesos de sistema registrados como cerrables** y **0 coincidencias exactas** con nombres de sistema. Un "services" que saltó en la primera comprobación resultó ser `riotclientservices` (launcher legítimo, `priority: none`) por la imprecisión de mi propio grep por subcadena, no un fallo.
- El test discrimina: con el blindaje desactivado falla.

### Impact
Se cierra la via por la que la app mas(score Real peligro: no es solo lo que la lista ofrece, sino lo que el usuario puede escribir a mano en un pack. Ademas se documenta el criterio de NO registrar procesos de sistema, que no estaba escrito en ninguna parte y que la proxima expansion de la base iba a reevaluar sin saberlo.


---

## [CYCLE-014] 2026-09-29 20:55 - 2026-09-29-gaming-service-runtime
**Área**: Gaming & Telemetría UX (matriz área 2)
**Change**: openspec/changes/2026-09-29-gaming-service-runtime/
**Estado**: COMPLETED (sin commit: el entorno bloqueó el versionado, ver Outcome)
**Models**:
- Paso 1 (Buscar): `inherit` (el backlog tenía `active_task_id`; la búsqueda fue contrastar el bug contra el código real)
- Paso 2 (Planear): `pro` (override sobre `inherit`: riesgo de regresión de seguridad — una barrera mal puesta permite matar procesos de sistema)
- Paso 3 (Ejecutar): `inherit` (implementación acotada en 7 ficheros, siguiendo una spec ya auditada)

### What
- **Configuración muerta conectada al runtime**: `GamingService.should_kill_for_gaming()` existía y estaba testeado desde el ciclo #10, pero **nunca se invocó en runtime**. Las 3 rutas de Gaming Mode (tray, portada, gestor de packs) llamaban solo a `kill_pack_apps(pack.apps)`, así que `keepers` y `target_categories` eran decorativos: el usuario marcaba qué proteger y qué cerrar, y el motor nunca lo consultaba. Es la promesa central del producto, desconectada.
- **La raíz era más profunda que el briefing**: `MainWindow` guardaba `gaming_service` (`main_window.py:15`) pero **no se lo pasaba a las vistas** (`:55-71`). El campo estaba muerto en dos niveles, no en uno.
- **VECTOR DE BRICK detectado en planificación**: el guard heredado de `bugfix-audit-v3` ("filtrar los que NO estén en `SYSTEM_PROTECTED_PROCESSES`") es insuficiente. `svchost` y `explorer` están en la categoría `🔴 Sistema de Windows` y **no** en el blacklist de nombres, y esa categoría se ofrece como casilla activable en el acordeón del gestor de packs. Marcarla cerraba **todos los `svchost.exe`**: `is_system_protected('svchost')` es `False`, así que el blindaje de nombres no lo detiene. La garantía correcta no es ampliar el blacklist —que exige acordarse de cada nombre nuevo— sino una **barrera de categoría roja** independiente, aplicada dos veces (sobre `target_categories` y sobre la categoría de cada proceso).
- **Segundo fallo silencioso, del mismo tipo**: `should_kill_for_gaming` compara por subcadena y los keepers se guardan como `"discord.exe"`, pero `get_running_processes` quita la extensión del campo `name`. Evaluar con `p.name` habría **desactivado keepers y apps en silencio** (Steam y Discord morirían siendo "keepers"). La suite no lo cubría porque sus aserciones pasan nombres con `.exe`.
- **Implementado**: `execute_gaming_pack()` en `services/` como **única puerta de kill** —delega íntegro en `kill_processes`, no importa `psutil` ni `json`, y por tanto no puede abrir una vía al SO que las otras no tengan—. `force_refresh=True` (la cache TTL de 2 s devuelve procesos obsoletos), y los dos `if not pack.apps: return` que bloqueaban un Gaming Mode configurado solo por categorías.
- **Contrato de UI**: se inyecta `GamingService` en las vistas con fallback defensivo, **no** se añade un método a `ProcessService` (que es el adaptador de `psutil` y no debe conocer el modelo `Pack`). Las 2 rutas de ventana siguen pasando por el `_require_double_tap` existente; el ítem del tray queda documentado como la **única** excepción, porque un `MenuItem` de pystray no es un widget y un diálogo está prohibido por la Trampa #14.

### Outcome
- Tests: **23 -> 24, 0 fallos** (`run_tests.py`); `verify_ui_syntax.py` EXITO (8/8 módulos)
- **Commits: ninguno.** El shell del entorno falló con `spawn EPERM` de forma intermitente (~3 de 12 intentos pasaron) y `git_safe_commit.py` requiere `subprocess`. Los cambios quedan en el árbol sin versionar: `feat: conecta GamingService.execute_gaming_pack a las 3 rutas de Gaming Mode (TASK-025)`.
- Docs: `docs/ai/architecture.md` (regla 11: ruta, contrato y garantías G-1..G-6) y `docs/ai/ui-design-system.md` (excepción del tray)
- **El test discrimina, y está PROBADO por mutación**: un verificador neutralizó las dos barreras G-2 en una copia temporal y el test falló con `Llegaron: ['chrome.exe', 'onedrive.exe', 'svchost.exe']`. No es un test que "devuelve un int": captura la lista que llega a `kill_processes` y asserta sobre su contenido, con precondición explícita que verifica que `svchost` **no** está en el blacklist (si lo estuviera, el test dejaría de distinguir y lo dice).
- Bug real encontrado y corregido durante la validación: `is_system_protected` es un `@staticmethod` de `ProcessService`, no una función de módulo. El `ImportError` del primer `run_tests.py` lo delató.
- Verificación independiente: veredicto **PASS**, sin hallazgos críticos, altos ni medios.

### Impact
El Gaming Mode por fin hace lo que el usuario le configura, y —más importante— la nueva ruta no puede cerrar procesos de sistema aunque el usuario marque la categoría equivocada. La lección reutilizable queda en la spec: **una evaluación por categoría no se puede blindar con un blacklist de nombres**, porque el blacklist depende de que alguien se acuerde de añadir cada nombre nuevo. Aquí la defensa es la categoría, y el blacklist sigue siendo la segunda capa, no la primera.

---

## [CYCLE-015] 2026-09-29 21:40 - 2026-09-29-data-integrity-fixes
**Área**: Resiliencia & Robustez (ejecutada como tarea de backlog, prioridad sobre rotación)
**Change**: openspec/changes/2026-09-29-data-integrity-fixes/
**Estado**: COMPLETED (sin commit: el entorno bloqueó el versionado)
**Models**:
- Paso 1 (Buscar): `inherit` (el backlog tenía la siguiente tarea; no hizo falta descubrimiento)
- Paso 2 (Planear): `pro` (override: los 4 puntos tocaban integridad de datos y concurrencia en Tk)
- Paso 3 (Ejecutar): `inherit` (spec ya auditada, 4 fixes acotados)

### What
- **FIX-007, riesgo máximo**: `process_manager_view._do_load` mutaba `self.processes` y `self.grouped_processes` **desde el hilo secundario**, mientras el hilo principal recorría ese mismo dict en el render → `RuntimeError: dictionary changed size during iteration`, y un set de PIDs desalineado entregado a `on_kill_selected`, que es el camino que mata procesos reales. Además dos `_do_load` solapados dejaban `grouped_processes` desfasado de `processes`. Ahora el hilo **solo calcula** y publica con un único `self.after(0, _apply)`.
  - **La spec heredada era incorrecta**: `bugfix-audit-v3/tasks.md:23` pedía `self.master.after`, que está prohibido (`main_window.py:42-45` destruye la vista en toda navegación; `master` es `content_frame`, que sobrevive).
- **FIX-009, y la premisa de la tarea era FALSA**: no faltaba "añadir un backup". El hallazgo real es mayor: `load()` ante un JSON corrupto **borraba todos los packs y sobrescribía con uno solo-Gaming**, y `except (json.JSONDecodeError, Exception)` es literalmente `except Exception`, así que un `PermissionError` tomaba **la misma ruta destructiva**. Ahora: backup preventivo, recuperación desde `.bak` **antes** de regenerar, `OSError` propagado sin escribir nada, rotación que **no** pisa un backup sano con un principal corrupto, y escritura atómica (`tmp` + `os.replace`).
  - **Documentación que mentía**: `tasks.json` (TASK-011 `completed`), `v3.1-quality-of-life/tasks.md:5` (`[x]`) y `CHANGELOG.md:91` afirmaban que la rotación de backups existía desde el ciclo #2. No existía: `save()` era `open(...,'w')` + `json.dump` pelado. Grep de `.bak|shutil|copy2|os.replace` en `src/` → **cero coincidencias**.
- **FIX-005**: `_DEFAULT_META` usaba la interrogación ASCII (U+003F) donde `config.py` y `models.py` usan el círculo (U+26AA). El efecto llegaba a **3 sitios**, no 1; el peor era un filtro de la UI (`pack_manager_view.py:179`) que comparaba contra el literal equivocado y por tanto **no filtraba nada**. También una aserción de `run_tests.py` (~1483) que era **tautológica**: afirmaba que una categoría no era un literal que ya no existía en el código.
- **FIX-001, redefinido**: `get_gaming_pack()` usaba `model_copy()` shallow, pero la auditoría lo demostró **inalcanzable** — no tiene ningún llamador (todo va por `get_all_packs()`) y `load()` siempre termina en `_ensure_gaming_pack()`. El ciclo #10 ya cerró la vía real. Queda como deuda latente de 1 carácter, arreglada igualmente.

### Outcome
- Tests: **24 -> 28, 0 fallos** (`run_tests.py`); `verify_ui_syntax.py` EXITO (8/8); `validate_docs.py` 42 OK / 0 FAIL
- **Commits: ninguno** (mismo bloqueo de shell que en el ciclo #14)
- Docs: `data-models.md` (§4 contrato de escritura, §5 literal canónico, §6 backups, y corrección de la afirmación falsa de TASK-011), `architecture.md`, `ui-design-system.md`, `testing-guide.md` (tabla a 28, notas de concurrencia en Tk)
- **Los 4 tests discriminan, verificado por mutación** en copia temporal, cada uno por su aserción prevista: FIX-001 `apps comparte objeto (shallow)`, FIX-005 `_DEFAULT_META[0] es '? Otros'`, FIX-009 `save() no creo el .bak preventivo` y, por separado, la recuperación. Para FIX-007 se probó además una **5ª mutación opaca** (`grouped_processes.clear()` desde el hilo, invisible al guard `ast`): también falla, así que el test no es solo lint estático.
- Verificación independiente: **PASS**. Un bug del propio implementador lo delató la validación: importó `is_system_protected` como función de módulo cuando es un `@staticmethod` de `ProcessService`.
- Hallazgo abierto (MEDIUM, no corregido): `CORRUPTION_ERRORS` no incluye `AttributeError`, así que **3 de 7 formas** de JSON malformado propagan y tumban el arranque. No hay pérdida de datos —no se escribe nada— pero es disponibilidad y contradice el docstring de `load()`.

### Impact
Dos de las cuatro premisas de la tarea resultaron falsas, y el hallazgo útil vino de auditarlas en vez de implementarlas tal cual: el problema de integridad de datos real no era "falta un backup" sino que **el archivo de configuración del usuario se borraba entero ante cualquier error, incluidos los de permisos**. La lección: `except (json.JSONDecodeError, Exception)` es `except Exception` — el contexto de la tupla sugiere dos categorías y no lo es.

---

## [CYCLE-019] 2026-09-30 09:10 - 2026-09-30-validate-pack-leaves
**Área**: Resiliencia & Robustez
**Change**: openspec/changes/2026-09-30-validate-pack-leaves/
**Estado**: COMPLETED — **3 iteraciones del Paso 3, 1 FAIL y una re-auditoría intermedias**
**Models**:
- Paso 1 (Buscar): `inherit` — `TASK-031` era la `active_task_id` y `critical`
- Paso 2 (Planear): `inherit` (con override: integridad de datos)
- Paso 3 (Ejecutar): `inherit` ×3 (cada iteración con el informe del auditor)
- Paso 4 (Auditar tests): `inherit` (`mutation-auditor`) ×3 → **FAIL, FAIL, PASS**

### What — lo que el arquitecto REFUTÓ (ninguna premisa del encargo era cierta)
1. *"La guarda valida el contenedor, no las hojas"* es **FALSO en la rama moderna**: `pack_service.py:171` es `return AppData(**raw_data)`, que ya detecta `keepers:"str"`. La rama ciega es **solo la legacy**, por un `Pack(...)` literal de **5 de 8 campos** (`pack_service.py:161-169`); los dos que faltaban eran `keepers` —la lista **anti-brick**— y `target_categories`.
2. *"La solución es validar contra Pydantic"* **ya se hace**, y con esa guarda los 14 escenarios **siguen machacando el `.bak`**.
3. *"Un `save()` posterior machaca el `.bak`"* es una **subestimación grave**: la causa es `_rotate_backup()` (`:206-207`) validando con `json.load` en vez de `_read_json`. **Dos definiciones de "no corrupto"** y el docstring describía la que no se ejecuta. Medido: el `.bak` sano moría en **7 de 8 escenarios**, incluidos los que el repo **afirmaba proteger**, y **no era un `save()` del usuario** sino el de `_ensure_gaming_pack()` **dentro de `load()`**. `data-models.md:53-55` afirmaba esa garantía: falsa.
4. *Bonus:* `{"packs":…,"profiles":…}` borraba los packs legacy sin clasificar nada; y un campo raíz desconocido (`notas`) se perdía en el primer `save()`.

### Decisión de producto (§3)
**Una hoja mal formada es CORRUPCIÓN**, no un pack válido con un campo raro. Motivo: `keepers` es la lista anti-brick (`gaming_service.py:24`) y normalizarla a `[]` desarma el Gaming Mode de forma **invisible e irreversible**. Recuperar del `.bak` puede devolver otra versión, pero eso es **visible y diagnosticable**; un fichero borrado no se reconstruye. Se acepta con tres condiciones: mensaje con campo+pack+tipo, recuperación observable, y **sin `.bak` legible no se regenera a lo bruto**.

### Las tres iteraciones del Paso 3
- **Iteración 1** → el dev se auto-declaró 13/13 verde. **Auditoría: FAIL.** Encontró que `AppData.extra="allow"` era *load-bearing* contra la pérdida de datos y **ningún test la vigilaba**: con `extra="ignore"`, una raíz mal escrita (`perfiles`) hacía que el primer `save()` publicase `{"packs":…}` y **los packs del usuario desapareciesen del disco** (medido). Además: typo `keeper` aceptado en silencio → **anti-brick desarmado**; e `is_gaming:"true"` coercionado a `True` → pack **invisible e indeletable** (`delete_pack` lanza *"No se puede eliminar el pack de sistema"*).
- **Iteración 2** → **Auditoría: FAIL** con 3 supervivientes medianos: **M8** (los extras de raíz, incluido `favorite` que existe en un `profiles.json` legacy real, se destruían en el primer `save()`), **M4b** (`is_favorite` laxo, hermano sin fijar del que sí se arregló) y **M13** (`_normalizar_clave` sin sonda). Además, falsos positivos: `names`→`name` e `ids`→`id` a distancia 1 se declaraban corrupción, lo que hacía **falsa** la afirmación documental de "cero falsos positivos".
- **Iteración 3** → **Auditoría: PASS.** 19 mutaciones vigiladas, ningún superviviente en el rango declarado.

### Mutaciones auditadas (Paso 4, iteración final)
| Fix | Mutación | Veredicto | Motivo |
|---|---|---|---|
| Copia de la raíz | no copiarla | killed | `la clave raiz 'favorite' desaparecio del disco tras el save()` |
| Copia de la raíz | copiar `profiles` también | killed | `el landmine solo explotaria en el segundo arranque` |
| Vigilancia de hoja | solo en la moderna | killed | `[legacy/keeper]` |
| Vigilancia de hoja | solo en la legacy | killed | `[moderna/keeper]` |
| `is_favorite` | sin `strict` | killed | `_read_json dio None en vez de ValidationError` |
| Normalización | `_normalizar_clave`→identidad | killed | `'IS-FAVORITE' se acepto como campo desconocido` |
| Umbral | 1→2 pulsaciones | killed | `'note' esta a distancia 2 de 'name'` |
| `extra` raíz | `AppData extra="ignore"` | killed | `quedan ['packs']: los packs se han perdido` |
| `extra` hoja | `Pack extra="forbid"` | killed | `un campo desconocido se clasifico como corrupcion` |
| `extra="allow"` raíz | raíz sin clave conocida | killed | `una clave de la RAIZ se declaro error de escritura` |

### Outcome
- Tests: **36 → 48**, 0 fallos. `verify_ui_syntax.py` EXITO. `validate_docs.py` 0 FAIL.
- **VERDICT final: PASS.** Ningún camino destruye datos; ningún test decorativo.
- **Propiedad estructural CONFIRMADA por medición** (el logro de diseño): `CLAVES_DE_PACK` se deriva de `Pack.model_fields`, así que añadir un campo nuevo al modelo hace que su error de escritura se clasifique **sin tocar una línea de la guarda**. El auditor lo verificó con un campo inventado, dos veces.
- **La decisión de NO vigilar la raíz se sostiene con datos, no con opinión:** clasificarla haría `self._data = AppData()` y el siguiente `save()` publicaría `{"packs":{"gaming":…}}` → pérdida igual **y con un aviso encima**.
- **El arreglo de M8 no abre un agujero nuevo:** 18 nombres reservados de Pydantic (`model_config`, `copy`, `model_dump`…) probados; ninguno tumba el arranque ni pierde el dato.
- **Commits: ninguno** (persiste el bloqueo de shell).
- Deuda menor, declarada y **no** certificate: 2 supervivientes de normalización que requieren **2+ pulsaciones** (fuera del umbral declarado de 1), y 2 citas documentales erróneas (`config.py:95` → `CATEGORY_ORDER` está en 97; `proposal.md:222-226` sigue diciendo "No bloqueante" para `extra="allow"`, refutado en `tasks.md` §3/§4).

### Impact
El ciclo más caro en tiempo hasta ahora —3 vueltas— y el que más justificó el Paso 4. La secuencia importa: el implementador se Declaró verde, el auditor lo refutó y encontró la pérdida de packs, la segunda iteración arregló eso pero abrió otra ruta, la tercera la cerró. **Sin el paso de auditoría, el `.bak` habría seguido destruyéndose y el ciclo habría publicado "48 tests en verde" tres veces.**

La lección de diseño: **el fallo no estaba donde apuntaba el encargo, sino en una rotación de copias que usaba un criterio distinto del que se usaba para decidir si un archivo estaba dañado**. Dos definiciones de la misma pregunta, en el mismo fichero, es exactamente el tipo de divergencia que sobrevive a años de revisión.

**Nota de proceso (autorrelevada):** el dev se salió de su lista de ficheros en `models.py` y lo declaró, con el motivo (`extra="forbid"` es la mutación que la sonda clave debe matar, y `extra="forbid"` es el default). Salidas justificadas y declaradas se pueden aceptar; salidas silenciosas no.

---

## [CYCLE-016] 2026-09-30 00:32 - roles-como-agentes
**Área**: infraestructura del pipeline (a petición explícita del propietario)
**Change**: ninguno (no toca `src/`); modifica `AGENTS.md` y `.agents/skills/id-pipeline/SKILL.md`
**Estado**: COMPLETED (sin commit: persiste el bloqueo de shell)
**Models**:
- Paso 1 (Buscar): `inherit` (el dueño preguntó por qué no veía las skills; el trabajo salió de esa pregunta)
- Paso 2 (Planear): `inherit` (sin cambios de arquitectura de producto; decisión de mecanismo)
- Paso 3 (Ejecutar): `inherit` (traducción de 3 skills a 3 `agent.md` + reparación de referencias rotas)

### What
- **Los tres roles del pipeline pasaron de skills a agentes reales**: `architect-review`, `openspec-dev` y `process-db-updater` viven ahora en `~/.minimax/agents/<name>/agent.md` y aparecen en el panel del runtime.
- **Causa raíz de "no veo las skills":** `.agents/skills/` es un mecanismo **distinto** del panel de agentes. Una skill es un fichero de instrucciones que carga el orquestador; un agente es una sesión propia delegable con `task`. Las cuatro estaban donde correspondía, pero el panel solo lista la segunda clase.
- **Referencia rota en `id-pipeline`:** los pasos 2, 3 y la invocación de `process-db-updater` seguían mandando usar `invoke_subagent` con `Role` y `TypeName`, un mecanismo que **ya no existe** en este runtime. Consecuencia real: la primera invocación de `architect-review` falló con *"Unknown agent"*, y el orquestador tuvo que delegar a `worker` copiando las directrices a mano en el prompt — exactamente la traducción que los agentes reales eliminan.
- **Sección 7 reescrita:** la matriz de modelos pedía `flash` / `inherit` / `pro`, valores que el runtime actual **no acepta** en `task` (rellenar `model` a mano produce error de resolución). Conservada como guía de **intensidad**, con la instrucción de resolver el modelo solo si el usuario lo pide.
- **`AGENTS.md` actualizado** con una tabla que separa explícitamente skill de agente, y las tres trampas del entorno (`tm.py` no ejecutable, `git` a pelo prohibido, doble escritura de changelog).
- **Cada `agent.md` incorpora las lecciones de los ciclos 14 y 15**, no solo el texto de la skill: la barrera de categoría roja frente al blacklist, el fallo de `p.name` sin extensión, `is_system_protected` como `@staticmethod`, el emoji `⚪ Otros` (U+26AA) y la reescritura de `print()` en ASCII.

### Outcome
- **Prueba de arranque real, no una aserción:** se delegó a `architect-review` un audit de humo. Respondió los 5 puntos con `archivo:línea`, identificó **sin pista** que `is_system_protected` es un `@staticmethod` de `ProcessService` y no una función de módulo (el mismo error que tumbó al implementador del ciclo 14), y razonó por su cuenta que el blacklist **no** protege `svchost` porque su categoría 🔴 no está en el frozenset. Cero ficheros modificados, cero git: respetó su propio scope.
- Tests: sin cambios en `src/`, la suite sigue en 28/28.
- **Commits: ninguno** (persiste el bloqueo de shell de los ciclos 14 y 15).
- **Dos regresiones que introduje yo en este pase, ambas encontradas por el verificador:**
  1. Al renombrar la sección de roles de `AGENTS.md` a "Roles del Pipeline", `validate_docs.py` seguía buscando el encabezado antiguo por nombre literal y pasó a dar FAIL. Un validador atado a un título deja de validar en cuanto el título mejora → ahora acepta ambos nombres.
  2. **Falso verde en el ancla:** mi primer arreglo convertía el salto silencioso en FAIL, pero solo para el journal **corrupto**. El **ausente** seguía en verde, porque el `errors.append()` vivía dentro del `except` y el `if os.path.exists()` saltaba la rama entera. Y había un cuarto caso silencioso: journal válido pero con la lista vacía. Los tres fallan ahora con mensaje explícito, verificado con los 3 escenarios más un control.
- Referencias rotas restantes en `id-pipeline/SKILL.md` reparadas: 5 usos de `tm.py next/done/list` (no ejecutable aquí → leer `tasks.json`), la columna "Modelo Recomendado" (valores no soportados → "intensidad") y la sección de validación, que **afirmaba** que el script comprobaba la sección `Models` de cada entrada cuando no lo hace. Documentados los límites reales del validador.
- Los 3 skills de rol llevan ahora un banner **SUSTITUIDA POR UN AGENTE** con su contenido plegado en `<details>`. Motivo: eran una segunda fuente de verdad que divergía del agente y arrastraba referencias rotas.

### Impact
El pipeline deja de depender de que el orquestador recuerde traducir skills a prompts. Con los tres roles como agentes, la independencia es real: el arquitecto audita en su propia sesión sin ver la conversación, lo que hace que su "visto bueno" valga como criterio y no como rubber stamp. Antes esa separación era nominal.

---

## [CYCLE-017] 2026-09-30 01:15 - paso-4-mutation-auditor
**Área**: Pipeline (petición explícita del propietario: "añade un paso que aporte mucho")
**Change**: ninguno en `src/`; modifica `id-pipeline/SKILL.md`, `AGENTS.md` y crea el agente `mutation-auditor`
**Estado**: **ABIERTO** — el Paso 4 devolvió FAIL (3 supervivientes). Sin `PASS` el ciclo no se cierra; el trabajo de infraestructura de este pase sí está hecho y verificado. (sin commit: persiste el bloqueo de shell)
**Models**:
- Paso 1 (Buscar): `inherit` (la pregunta del propietario *era* el encargo)
- Paso 2 (Planear): `inherit` (decisión de proceso, no de arquitectura de producto)
- Paso 3 (Ejecutar): `inherit` (nuevo agente + skill + AGENTS.md)
- Paso 4 (Auditar los tests): `inherit` (`mutation-auditor`) → **VERDICT: FAIL**, ver abajo

### What
- **El bucle pasa de 3 a 4 pasos.** El nuevo **Paso 4** es "auditar los tests": un agente rompe el código a propósito y comprueba que los tests lo detecten. Sin su `PASS`, el ciclo no se cierra.
- **Nuevo agente `mutation-auditor`** (`~/.minimax/agents/mutation-auditor/agent.md`). Trabaja **solo sobre copias en `%TEMP%`**, tiene prohibido escribir en el repo y prohibido reparar lo que encuentra. Lleva una **tabla de 12 mutaciones canónicas** de este repo, que es el conocimiento que costó tres ciclos descubrir.
- **Regla dura añadida:** un sobreviviente en **seguridad o datos no se documenta como deuda, se arregla**. Documentar una brecha conocida es exactamente cómo se cuela un brick tres ciclos después.
- **Reparadas 9 referencias a `tm.py`** en todo el repo (`AGENTS.md`, `id-pipeline/SKILL.md`, `tasks.md`, `docs/ai/INDEX.md`, `llms.txt` y un change activo) que seguían mandando ejecutar un comando **no funcional** en este entorno. Cualquier agente nuevo que leyera esas guías se atascaba en el paso 1. Nota: en el ciclo 16 se repararon las de la skill; aquí las del resto de la documentación.
- La sección de validación de la skill afirmaba que el script comprobaba la sección `Models` de cada entrada: **no lo hace**. Reescrita con lo que comprueba de verdad y sus límites.

### Outcome
- **El primer arranque del agente nuevo encontró 3 supervivientes reales en los fixes del ciclo 15**, dados por cerrados:
  1. **Atomicidad sin verificar.** El test comprueba que exista un `.tmp`, así que si la escritura deja de ser atómica y **nunca** crea el `.tmp`, el assert sigue pasando **por la razón equivocada**. Nadie prueba que `profiles.json` quede intacto si el `json.dump` se corta a mitad.
  2. **`except OSError` acepta dos cosas distintas.** El caso D2 arma el escenario con `os.chmod(0o400)`: la escritura falla **por el mismo permiso que se quiere detectar**, y `except OSError: pass` acepta igual "no intentó escribir" que "intentó y reventó". Un mutante que reintroduce `OSError` en `CORRUPTION_ERRORS` **sobrevive con 28/28 en verde**.
  3. **`CORRUPTION_ERRORS` sigue incompleto.** `ValidationError`, `TypeError` y `UnicodeDecodeError` no están cubiertos, y los tres **tumban `PackService()`** — se confirmó que `{"profiles": "texto"}` lanza `AttributeError`. Es el hallazgo que ya estaba abierto desde el ciclo 15, ahora con confirmación empírica.
- Extras detectados: el guard `ast` del test de FIX-007 mata **antes** de que se compruebe la carrera real (al quitarlo, el test cuelga el bucle Tcl en lugar de fallar con `AssertionError`); y `get_gaming_pack()` / `_force_update_db()` siguen **sin ningún llamador** en `src/`.
- El agente verificó por SHA-256 y mtime que **no escribió en el repo**, y declaró un incidente propio: dos mutaciones concurrentes contaminaron su copia, las detectó y repitió **en serie**.
- Tests: sin cambios en `src/`; suite intacta en 28/28.
- **Commits: ninguno** (persiste el bloqueo de shell desde el ciclo 14).

### Impact
El bucle ganó su paso más valioso justo cuando menos confianza había: los tests del ciclo 15 se habían marcado como discriminantes **porque el implementador lo afirmó**, y el mutation-auditor refutó esa afirmación en su primer minuto. La lección de fondo es la misma que sostiene el paso: **`run_tests.py` en verde no es evidencia de nada sobre la calidad del test**. Lo único que convierte un test en evidencia es romper el código y verlo morir.

---

## [CYCLE-018] 2026-09-30 02:10 - 2026-09-30-close-mutation-survivors
**Área**: Resiliencia & Robustez
**Change**: openspec/changes/2026-09-30-close-mutation-survivors/
**Estado**: COMPLETED (cierra el FAIL del #17; deja TASK-031 abierta por hallazgo nuevo)
**Models**:
- Paso 1 (Buscar): `inherit` — el FAIL abierto del #17 manda sobre el backlog; TASK-027/028/029 siguen pendientes
- Paso 2 (Planear): `inherit` (diseño de tests de fault-injection; el modelo caro se reservó al análisis de seguridad)
- Paso 3 (Ejecutar): `inherit` (spec ya auditada, 2 ficheros de producción)
- Paso 4 (Auditar tests): `inherit` (`mutation-auditor`) → **VERDICT: PASS** (7/7 mutaciones muertas)

### What
- **Cierra el FAIL del ciclo #17.** Los 3 tests que pasaban con el bug puesto están arreglados: (a) atomicidad probada por fault-injection dentro de `json.dump` afirmada sobre **bytes** del principal, sin hilos ni `sleep`; (b) el caso de permisos comprueba el **estado resultante**, no un contador de llamadas; (c) `AttributeError` ya no tumba `PackService()` al arrancar.
- **El arquitecto refutó las TRES premisas del encargo, con mediciones:**
  1. `CORRUPTION_ERRORS` **ya cubría** `ValidationError`/`TypeError`/`UnicodeDecodeError` (`pack_service.py:16`). El mutante sobrevivía porque **ningún test las miraba**: el arreglo era de test, no de código. El agujero real era `AttributeError` en la rama legacy (`pack_service.py:79`, `:90`), que **tumbaba `PackService()` al arrancar** con `{"profiles":"texto"}` — peor que el bug perseguido.
  2. *"Falta un espía que afirme que `save()` NO se llamó"*: **falso por construcción.** Medido `save()=1, volcados=1` en el código correcto **y** en el mutante. Además `load()` escribe dos veces (`pack_service.py:59-61` + `:173`).
  3. En Windows `chmod` solo niega **escritura**: la lectura sigue permitida, así que toda la familia con `chmod` es **ciega**. Tres escenarios probados, ninguno distingue.
- **`AttributeError` excluido de `CORRUPTION_ERRORS` a propósito:** incluirlo convertiría cualquier bug interno en pérdida de packs. Y `except Exception` sigue rechazado por ser el bug del ciclo 15. Se valida la **forma** con `PerfilCorruptoError(ValueError)`.
- **FIX-007 sin Tk:** arnés con `__new__` + propiedades que anotan el hilo. Permitió **quitar `faulthandler.dump_traceback_later(150, exit=True)`**, que hoy mataba el runner. El test de la vista ya no abre una ventana.
- **El dev se salió de su lista de ficheros** en `docs/ai/architecture.md` (2 líneas) y lo declaro: su cambio dejaba falsas una referencia al watchdog eliminado y el nombre del test. Documentación que miente es peor que ninguna.

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo |
|---|---|---|---|
| Atomicidad | `os.replace` → `copyfile` | killed | `la escritura atomica no deja .tmp` |
| Limpieza | sin `unlink` del temporal | killed | `un save fallido no debe dejar un .tmp` |
| `except` | readmitir `OSError` | killed | `save() no lanzo el PermissionError de la rotacion` |
| Guarda de forma | sin `isinstance(perfiles, dict)` | killed | `lanzo AttributeError(...) en vez de PerfilCorruptoError` |
| `except` | `except Exception` en `load()` | killed | `un OSError de lectura no es corrupcion ... arranco en silencio` |
| `except` | readmitir `AttributeError` | killed | `AttributeError NO puede estar en CORRUPTION_ERRORS` |
| Hilo | `self.after(0,_apply)` → `_apply()` | killed | runtime: `'processes' se publico desde el hilo 26140, no desde el principal (19000)` |

Ninguna muerte por ImportError o sintaxis. **La del hilo se verificó neutralizando el guard `ast`**: sigue roja en runtime y verde con el código intacto, o sea no tautológica.

### Outcome
- Tests: **28 → 36**, 0 fallos. `verify_ui_syntax.py` EXITO (8/8). `validate_docs.py` 50 OK / 0 FAIL.
- **VERDICT del Paso 4: PASS.** El arbitrage del `except` dio bien: `null`, `[]`, `{"a":1}`, `0`, `true`, valor `null` y `label` no-str → los 7 se clasifican como corrupción y recuperan del `.bak` sano con cero escritura.
- **Commits: ninguno** (persiste el bloqueo de shell).
- **Hueco nuevo, abierto como `TASK-031` (critical):** la guarda valida el **contenedor**, no las **hojas**. Un pack con `keepers` o `target_categories` mal formados pasa, la rama legacy nunca lee esos campos, el `.bak` sano **nunca se consulta** y un `save()` posterior **lo machaca**. Pérdida silenciosa e irreversible. Pre-existente y no regresión de TASK-030, pero ningún test lo veía.

### Impact
El paso de auditoría no solo confirmó el arreglo: lo hizo **refutando el encargo**. Tres premisas que parecían verdad eran falsas, y la más grave (`AttributeError` tumbando el arranque) era **peor que el bug que se perseguía**. Un plan que hubiera seguido esas premisas habría escrito tests que pasan y no arreglado nada.

**Nota de proceso (autorrelevada):** rompí dos veces `tasks.json` con ediciones por regex sobre JSON. La causa es siempre la misma —mi editor no entiende la estructura—, y la lección es usar un script de Python con `json.load`/`json.dump` para cualquier edición estructural, nunca sustitución de texto. Recuperado ambas veces sin pérdida.

