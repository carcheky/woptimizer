# Deuda abierta del ciclo #26 — contenedor persistente

**Por qué existe este fichero.** `openspec-dev` declaró **7 incidencias abiertas** en su
informe de handoff y **solo 2** constaban en algún fichero del repo. Las otras 5 vivían
únicamente en un mensaje de agente. Un mensaje no es un sitio donde una incidencia
exista: se pierde en cuanto se pierde el mensaje, y este repo ya pagó ese precio dos
veces (el patrón de seguridad del ciclo 12, y el validador que deriva los ciclos
obligatorios del propio registro que debería auditar — `STATUS.md:78`).

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
| 3 | *(por rellenar — incidencia declarada por `openspec-dev` que no constaba en ningún fichero)* | ? | ? |
| 4 | *(por rellenar)* | ? | ? |
| 5 | *(por rellenar)* | ? | ? |
| 6 | *(por rellenar)* | ? | ? |
| 7 | *(por rellenar)* | ? | ? |

> Las filas 3-7 se rellenan con la **redacción literal** del informe, sin resumir ni
> reinterpretar. Si al verificarlas una ya está arreglada, se marca
> `✅ cerrado en CYCLE-0xx` citando el test que lo demuestra; **no se borra la fila**,
> porque borrar sin evidencia es el mismo fallo que no haberla escrito.

## Reglas de cierre

1. Una fila solo desaparece cuando dice **qué ciclo la cerró y con qué test**.
2. Toda fila nueva nace aquí primero y se refleja después en `STATUS.md`.
3. `validate_docs.py` **no** vigila este fichero: leer un `0 FAIL` no prueba que la
   trazabilidad esté al día. La disciplina es del orquestador.
4. `STATUS.md` y este fichero se leen en el mismo commit: dos listas de deuda que
   divergen son dos verdades, y ese es el defecto que este ciclo vino a cerrar.
