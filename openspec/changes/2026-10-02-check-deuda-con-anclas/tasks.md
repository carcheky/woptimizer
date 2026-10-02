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

---

## T8 — Ronda de cierre, tras el FAIL del `mutation-auditor`

El auditor dio **FAIL** con 30 mutantes (15 muertas, 14 supervivientes). Tres criterios que
este contrato daba por muertos **no lo estaban**, y el hallazgo central es que el validador
**no producia ni un FAIL** con cuatro de ellos. Todo lo de abajo esta **medido**, con la
linea `ok` antes y despues de cada mutante, en `mutation-report.md` (misma carpeta).

- [x] T8.1 **El marcador de cierre pasa de una palabra a un veredicto** (E1/E2, CRITICA). La fila 89 se eximia a si misma con cualquier frase normal. Ahora son cuatro condiciones: `CERRAD` en mayusculas fuera de codigo inline, **dentro de un veredicto en negrita**, con un **id trazable que exista** en la fila, y **sin negar** el cierre. Las 7 exentas reales las cumplen sin tocar una fila. Muerte medida: P1/P2/P3 dejan la linea `ok` **identica** (antes la movian a `8 exenta(s)/7 viva(s)`).
- [x] T8.2 **`STATUS.md` deja de ser un ancla** (A1, ALTA). Cuatro filas reales (87, 89, 100, 101) se citaban a si mismas y el check lo contaba como ruta valida. Al rechazarlo **ningun veredicto cambia**: las cuatro tienen otras fuentes. Muerte medida: P5 -> `0 FAIL` pasa a `2 FAIL`.
- [x] T8.3 **La gravedad se lee del emoji** y **«declarar» pasa a ser una forma, no una mencion** (G2/G3, ALTA). El emoji se mapea a `ROJO`/`AMARILLO`/`VERDE` al leer (ASCII en el informe, trampa #16) y el predicado exige la linea que empieza por `0 CODIGO`, no cualquier linea que mencione los codigos. **Las dos cosas son obligatorias**: con el mapa y el predicado viejo, las filas 100 y 101 (🟡) salen en rojo hoy. Muerte medida: P6 y P7 (bajar la 🔴 de la 88 o de la 89) salen en `1 FAIL`; M5 del contrato, que antes era inalcanzable, **muere**.
- [x] T8.4 **El `IndexError` de los tramos de codigo inline vacios**, que tumbaba el validador entero sin imprimir informe (la misma clase que `_recuento_de_tests` en el ciclo 27 y el journal en el 47). Se arregla el PRODUCTOR. Muerte medida: el mutante de codigo revienta con `IndexError`.
- [x] T8.5 **S5 acredita la cifra que la fila DECLARA, no la que menciona** (C9, rama positiva sin cobertura; C8, constante escrita a mano). Un escenario nuevo donde la fila declara la cifra derivada y no cita a nadie mas mata las dos.
- [x] T8.6 **La tabla de escenarios cuenta sus filas** (`len(FILAS) == 19`, S1) y **cada escenario asienta el recuento de la linea `ok`** (C1: amputar el check 8 entero daba `114 OK / 0 FAIL`, verde y sin un solo FAIL).
- [x] T8.7 **`mutation-report.md` escrito** con id estable por mutante, edicion a nivel de bytes, linea `ok` antes/despues, expectativa literal, atribucion en aislamiento y la lista de lo que no cubre ningun limite.
- [x] T8.8 **Decisiones tomadas y escritas**, no parchadas en silencio:
  - **N1**: una cifra que la fila **cita** (`docs/index.md` declara «96 tests») no es una afirmacion sobre el recuento, y verificarla contra el contenido actual de ese documento haria **imposible de redactar la fila 100**, que existe para documentar que ese documento declaraba una cifra desfasada. Queda como limite 12 de `docs/ai/sandbox-rules.md`.
  - **El suelo se recorre por `anclas["rutas"]`, no por los asuntos del titulo.** Atado a los asuntos lo dejaria muerto para siempre (ni una fila nombra en su titulo un fichero que declare el contrato) y con el se iria M5. La causa del falso rojo era el **predicado**, no el recorrido.
  - **El limite 4 del contrato estaba mal escrito** y se corrige: no es "el emoji evade el suelo", es "**la palabra de gravedad no existe en el panel**".
- [ ] T8.9 **Pendiente para el `mutation-auditor`:** re-auditar el FAIL con este informe. Los controles negativos **E4, A2, G3b, N2 y M4b** no son re-audibles desde el repo: sus ediciones byte a byte no estaban en ningun fichero, porque el `mutation-report.md` que los contiene es precisamente el que faltaba.
