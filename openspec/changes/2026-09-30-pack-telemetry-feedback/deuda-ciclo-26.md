# Deuda del ciclo #26 — contenedor persistente

**Por qué existe este fichero.** `openspec-dev` declaró **7 incidencias abiertas** en su
informe de handoff y **solo 2** constaban en algún fichero del repo. Las otras 5 vivían
únicamente en un mensaje de agente. Un mensaje no es un sitio donde una incidencia
exista: se pierde en cuanto se pierde el mensaje, y este repo ya pagó ese precio dos
veces (el patrón de seguridad del ciclo 12, y el validador que deriva los ciclos
obligatorios del propio registro que debería auditar — `STATUS.md:78`).

> **Estado: las 7 filas están transcritas y las 7 cerradas en `CYCLE-026`** (iteración 4,
> 2026-09-30). Se conservan con su severidad y su redacción porque el registro de que el
> defecto existió es parte del cierre: borrar la fila sin evidencia sería el mismo fallo
> que no haberla escrito. La tabla de cierres, con el test de cada una, está más abajo.

Este fichero es el **sitio al que se transcriben**, y `STATUS.md` (§`⚠️ Deuda Técnica
Conocida`, línea 70) es el panel donde se resumen con severidad. Los dos sitios son
obligatorios: el primero para el detalle, el segundo para que se vea al abrir el repo.

## Escala de severidad (obligatoria en cada fila)

| marca | significado | criterio |
|---|---|---|
| 🔴 | **miente al usuario o pierde datos** | contradice un invariante de `AGENTS.md`, o un `0 FAIL` no lo detecta |
| 🟡 | **inconsistencia o UX** | se ve y molesta, pero no pierde datos ni promete un éxito falso |
| ⚪ | **limpieza** | código muerto, doc desfasado, refactor sin efecto observable |

## Tabla

| # | incidencia | severidad | fichero donde vive |
|---|---|---|---|
| 1 | `feedback.py` / `_show_banner` imprimen siempre `(X.X MB liberados)` aunque `freed_mb == 0.0`; `format_kill_result` sí lo omite (`notification_service.py:133`, fijado por `run_tests.py:303`) | 🟡 | `decision-portada-pack-vacio.md` §5 |
| 2 | `test_el_feedback_de_pack_dice_la_verdad` **afirma** el silencio de la Portada con un pack sin apps (`run_tests.py:8578-8596`): la especificación del test contradice al design system (`ui-design-system.md:301`) | 🔴 | `decision-portada-pack-vacio.md` §3 |
| 3 | **La rama `start` de `execute_pack` no se ejecutaba NUNCA en la suite.** Con los tres casos de la rama `kill` (gaming, no-gaming, orden de la 4-tupla) y las aserciones de `_show_start_banner` hechas **llamando al método directamente** con valores puestos a mano, tres mutaciones pasaban la suite entera en verde: `_run_start` intercambia `launched`/`failed`; `_run_start` arranca `start_pack_apps([])`; `_run_start` publica en `_show_banner` con `(launched→killed, failed→freed_mb, p.name→is_gaming)`, o sea **el nombre del pack como flag de gaming** (banner verde Gaming y `_last_gaming_summary` basura, sin crash). Es la misma clase de "rama sin ejecutar" que el propio ciclo condena. | 🔴 | `run_tests.py::test_el_feedback_de_pack_dice_la_verdad` · `testing-guide.md` §3-ter |
| 4 | **La guarda AST es una RED, no un MURO, y el doc afirmaba que era un muro.** `ui-design-system.md` y `testing-guide.md` prometían en los dos que "todo lo que cuelgue de `self` y no sea un par permitido es infracción". No era cierto: `getattr(self, 'status_label').configure(text='x')`, `del self._last_gaming_summary` y `self.__dict__['status_label']` pasado como **argumento** de una llamada permitida atravesaban la guarda entera. Además el párrafo "Lo que la guarda NO comprueba" solo reconocía dos cosas. | 🔴 | `run_tests.py::test_los_workers_de_pack_solo_publican_por_after` · `ui-design-system.md` §Invariantes de Hilos |
| 5 | **El sustantivo parametrizable solo estaba probado en la rama ÉXITO.** La comprobación con `"apps"` miraba solo `mensaje_cierre_pack(..., killed > 0, ...)` y el valor por defecto solo la rama `nada`, así que cablear `"procesos"` a mano dejaba la suite VERDE. La fila del changelog que decía "el sustantivo se ignora" solo era cierta para una de las dos ramas que lo usan. | 🔴 | `run_tests.py::test_el_gestor_de_procesos_tampoco_miente` |
| 6 | **`ui-design-system.md` decía `len(to_kill)` donde el código dice `len(selected_keys)`** (`process_manager_view.py:361-362`). Es exactamente el bug arreglado en `d3089cc`, reintroducido como documentación: un lector que obedezca el doc reintroduce el descuadre entre "3 apps seleccionadas" del aviso y "4 seleccionadas" del resultado. | 🟡 | `ui-design-system.md` §Feedback y Telemetría |
| 7 | **La tabla de mutaciones no era reproducible.** `docs/ai/testing-guide.md` afirmaba "12 mutaciones, 12 muertes, 0 supervivientes" con `_matrix_c26.py`, pero el auditor lo **ejecutó y revienta** en la mutación 5 de 12 con `AssertionError: no se encontró el ancla de M6`; además `correr()` solo lanzaba **2 de las 3 sondas**, así que la tercera puerta nunca estuvo en esa matriz, y las dos tablas de los changelog ("15 mutaciones, 15 muertas") estaban infladas: la #13 murió por un `AttributeError` (un crash, no una aserción) y la #15 era media verdad. `_matrix_c26.py` estaba **comiteado y roto**. | 🟡 | `_matrix_c26.py` · `testing-guide.md` §Matriz de mutaciones |

> Las filas 3-7 se rellenaron con la **redacción del informe de handoff de `openspec-dev`
> (iteración 3)**, tal como exigía el §6 de la decisión. Si al verificarlas una ya estaba
> arreglada, se marca `✅ cerrado en CYCLE-0xx` citando el test que lo demuestra; **no se
> borra la fila**, porque borrar sin evidencia es el mismo fallo que no haberla escrito.

## Estado tras la iteración 4 (2026-09-30)

Las siete filas están **cerradas en `CYCLE-026`**, cada una con el test que lo demuestra.
Ninguna se borra: la fila es el registro de que el defecto existió y de qué lo cerró.

| # | severidad | cierre | test que lo demuestra |
|---|---|---|---|
| 1 | 🟡 | ✅ `clausula_mb(freed_mb)` omite la cláusula con `freed_mb <= 0` en los cuatro textos de éxito/parcial y en `_last_gaming_summary` | `test_el_feedback_de_pack_dice_la_verdad`: `_show_banner(killed=1, freed_mb=0.0)` → `"⚡ 1 procesos cerrados"`, sin `"MB"`; y la ausencia de `"0.0 MB"` en la barra de reposo |
| 2 | 🔴 | ✅ aserción **invertida**: el pack vacío se avisa con texto y color exactos, sin worker, sin nada encolado y sin doble pulsación armada | `test_el_feedback_de_pack_dice_la_verdad` (bloque "iter 4, TASK-036") |
| 3 | 🔴 | ✅ caso nuevo que entra por el **worker real** de la rama `start` (hilo secundario + `after` encolado), con dos resultados distintos y el toast comprobando que la barra de reposo no cambia | `test_el_feedback_de_pack_dice_la_verdad`; mutantes S1-a, S1-b y S1-c de `_matrix_c26.py` |
| 4 | 🔴 | ✅ el detector cubre `getattr`/`setattr`/`delattr`, `ast.Delete` y los **argumentos** de las llamadas permitidas; el doc enumera las cinco formas y el agujero que queda (alias local) | `test_los_workers_de_pack_solo_publican_por_after` (controles 6, 7 y 8); mutantes S2-a, S2-b y S2-c |
| 5 | 🔴 | ✅ el sustantivo se comprueba en las **dos** ramas que lo nombran (`éxito` y `nada`) | `test_el_gestor_de_procesos_tampoco_miente`; mutante S3 |
| 6 | 🟡 | ✅ el doc dice `len(selected_keys)` y explica por qué no es `len(to_kill)` | `ui-design-system.md` §Feedback y Telemetría; el descuadre lo mide `test_el_gestor_de_procesos_tampoco_miente` ("se cierran los PIDs de las casillas marcadas… texto con 4 would say 4 seleccionadas") |
| 7 | 🟡 | ✅ `_matrix_c26.py` reparado (anclas contra el código de hoy, error duro si no se encuentran, **las tres** sondas en cada mutación, salida ASCII) y la tabla del §Matriz reescrita con la salida real | `python _matrix_c26.py` → **20 mutaciones, 20 muertes, 0 supervivientes** (2026-09-30) |

## Reglas de cierre

1. Una fila solo desaparece cuando dice **qué ciclo la cerró y con qué test**.
2. Toda fila nueva nace aquí primero y se refleja después en `STATUS.md`.
3. `validate_docs.py` **no** vigila este fichero: leer un `0 FAIL` no prueba que la
   trazabilidad esté al día. La disciplina es del orquestador.
4. `STATUS.md` y este fichero se leen en el mismo commit: dos listas de deuda que
   divergen son dos verdades, y ese es el defecto que este ciclo vino a cerrar.
