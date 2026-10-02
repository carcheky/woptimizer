# Tasks — Check 8 de `validate_docs.py`: Deuda Tecnica Conocida con anclas resolubles

**Change ID:** `2026-10-02-check-deuda-con-anclas`
**Tarea:** `TASK-060` (ciclo #49)
**Contrato:** `proposal.md` (misma carpeta). Todo lo que sigue es **ejecucion**, no diseno.
**NO toca:** `src/woptimizer/**`. Cero cambios de codigo de producto.

---

## T1 — `_comprobar_deuda_con_anclas(root, errors, ok)` y sus auxiliares

- [ ] T1.1 `_filas_de_deuda(cuerpo) -> [(int, str)]`: seccion desde el encabezado `## ` que contiene `Deuda` hasta el siguiente `## `; filas = lineas que empiezan por `- **`. Si no hay encabezado, se reporta el motivo literal (no `[]` silencioso).
- [ ] T1.2 `_esta_cerrada(fila) -> bool`: `re.search(r"CERRAD", re.sub(r"`[^`]*`", " ", fila))`. **El `sub` es el fix**: sin el, la fila del criterio se autoexime.
- [ ] T1.3 `_anclas_resolubles(root, fila) -> dict` con cinco claves: `rutas` (S1, existencia, **sin linea**), `contenido` (S2, identificador de una palabra presente en el fichero), `tareas` (S3, `status` de `.taskmaster/tasks.json`), `ciclos` (S4, entrada en `CHANGELOG.md` o `rd_journal.json`), `numeros` (S5, el recuento derivado con `ast`).
- [ ] T1.4 `_severidad_minima(anclas) -> str`: `"ROJO"` si algun fichero de S1 sigue declarando `0` para `WOPT_COMMIT_OK` **y** para `WOPT_NOOP`; `""` en otro caso.
- [ ] T1.5 Cuerpo del check: seccion ausente -> FAIL; cero filas -> FAIL; por cada fila cerrada, contador de exentas; por cada fila viva, exigir `>= 1` fuente resoluble **y** `>= 1` fuente que no sea una `TASK` `completed`, y respetar el suelo de gravedad.
- [ ] T1.6 Una sola linea de `ok` con el inventario: filas, exentas, vivas, anclas resueltas, anclas por contenido. Sin ese inventario, un verde no dice que se ha mirado.
- [ ] T1.7 **Todos los `print()` y todos los mensajes en ASCII puro.** La gravedad se escribe `ROJO`/`AMARILLO`/`VERDE`, nunca con simbolo (trampa #16: cp1252 tumba el validador entero).

## T2 — Cableado

- [ ] T2.1 Una llamada a `_comprobar_deuda_con_anclas(root, errors, ok)` en `validar(root)`, entre `_comprobar_recuento_de_tests(root, errors, ok)` (`validate_docs.py:714`) y `return errors, ok` (`validate_docs.py:715`).
- [ ] T2.2 **Sin defaults y sin parametros extra.** Todo se deriva de `root`. Es la misma razon por la que `_comprobar_recuento_de_tests` se extrajo en el ciclo 27: sin `root` la rama solo se despierta lanzando el validador entero contra el repo entero.
- [ ] T2.3 El docstring de `validar` pasa de «Los checks 1-7 enteros» a «1-8».

## T3 — El reparto 93 + 10, en el check 7 (NO en el check 8)

- [ ] T3.1 `_reparto_de_tests(root)`: busca con `ast` la constante `--- Running Headless UI Tests ---` y cuenta las llamadas `test_*()` del `__main__` antes y desde ella. Medido: marcador en `run_tests.py:12919`, **93** antes, **10** desde, **103** totales.
- [ ] T3.2 Si el marcador **no aparece**, se reporta el motivo literal y se falla. Nunca `0 + 0 = 0` en verde.
- [ ] T3.3 Se compara con lo que declara `STATUS.md` («93 backend + 10 headless UI»). Si el reparto no aparece con esa forma, el mensaje lo dice y nombra la forma que el check lee, como hace `validate_docs.py:128-133`.
- [ ] T3.4 El total **sigue** viniendo de `_recuento_de_tests`; el reparto es una segunda derivacion del mismo `ast`, no un segundo total.

## T4 — Nacimiento: tocar 1 fila

- [ ] T4.1 `STATUS.md:91` (`CORRUPTION_ERRORS`): anadir el ancla de `src/woptimizer/services/pack_service.py`, donde vive `CORRUPTION_ERRORS`. **Una fila, una clausula.** Sin reescribir la redaccion original: la fila conserva su texto y gana la prueba que le faltaba.
- [ ] T4.2 **No** exemptar las filas 91, 92 ni 98 poniendoles `CERRADA` en mayusculas. Costaria 0 filas tocadas y dejaria tres filas sin vigilar; la regla del propio panel (fila 98) prohibe el carve-out.
- [ ] T4.3 Corregir el bloque **intra-panel** de la fila 101, que esta desviado **una unidad en sus cinco entradas** (dice 87/88/94/99/100 donde son 88/89/95/100/101) y afirma de la 91 que dice «cerrado en el ciclo #16» cuando dice «Cerrado en el ciclo #18». No es cosmetica: es la unica cita del panel que el check no puede verificar y que ya se propagó a `docs/ai/sandbox-rules.md:120`.
- [ ] T4.4 `validate_docs.py` pasa a **1+** coincidencias de «Deuda» (hoy: **0**), que es la prueba de que la seccion entro en el validador.

## T5 — Un solo test en `run_tests.py`

- [ ] T5.1 `tempfile.mkdtemp()` con un `STATUS.md` sintetico y su arbol. **El total de tests se deriva con `ast` del arbol sintetico**, nunca del repo real: si no, el test no distingue «derive» de «lei el numero correcto a mano».
- [ ] T5.2 Escenario **A**: fila viva sin ancla -> FAIL.
- [ ] T5.3 Escenario **B**: la *misma* fila marcada cerrada -> PASS. Es el que discrimina el fix de un check roto.
- [ ] T5.4 Escenario **C**: fila viva con un numero que contradice el derivado -> FAIL. Mata al mutante «derivar la verdad del panel en vez del codigo».
- [ ] T5.5 Escenario **D**: panel solo de filas cerradas -> PASS. Control negativo: un guard que marca todo no vigila nada.
- [ ] T5.6 Escenario **E**: seccion ausente -> FAIL.
- [ ] T5.7 Escenario **F**: fila que lleva el marcador **fuera** de codigo inline autoeximiéndose -> FAIL.
- [ ] T5.8 Escenario **G**: fila viva cuya unica fuente es una `TASK` `completed` -> FAIL.
- [ ] T5.9 Escenario **H**: fila viva que declara `AMARILLO` con el comprobable del codigo de salida sobrecargado presente -> FAIL.
- [ ] T5.10 Registrar el test en el `__main__` (`defined == invoked`, que exige el check 7) y anadir su fila a la tabla de `docs/ai/testing-guide.md`.

## T6 — Documentacion

- [ ] T6.1 `docs/ai/sandbox-rules.md`: la seccion nueva que describe el check 8, sus cinco fuentes de verdad y **los siete limites residuales** de `proposal.md` seccion 7. La limitacion residual se escribe; no se omite.
- [ ] T6.2 `STATUS.md`: una linea en la seccion del ciclo #49 que enlace este change y el resumen del hallazgo.
- [ ] T6.3 `CHANGELOG.md` (raiz) y `.taskmaster/CHANGELOG.md`: entrada del pase, dos ficheros, como manda `AGENTS.md`.
- [ ] T6.4 `python validate_docs.py` sale en verde **el dia 1**, con el check 8 activo y el panel real sin tocar mas que la fila 91.

## T7 — Muerte de las mutaciones (paso del `mutation-auditor`, no de este contrato)

- [ ] T7.1 Las diez mutaciones de la tabla de `proposal.md` seccion 4 se aplican **una a una** sobre una copia del panel y cada una sale en rojo.
- [ ] T7.2 Mutantes de codigo que deben morir tambien: borrar la excepcion de las cerradas (mata B), sustituir la derivacion con `ast` por una lectura del panel (mata C), borrar el `re.sub` de codigo inline (mata F), borrar la regla de la tarea cerrada (mata G), borrar el suelo de gravedad (mata H), y **quitar el cuarto argumento del cableado** (mata el `TypeError` de la firma, como en el ciclo 47).
- [ ] T7.3 El ciclo no se cierra con `PARTIAL`: o todos mueren, o el superviviente se arregla.
