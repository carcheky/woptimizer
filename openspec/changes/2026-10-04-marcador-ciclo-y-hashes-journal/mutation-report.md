# Informe de mutación — TASK-059 (ciclo 52)

**Qué es este fichero.** La auditoría del Paso 4 mutó el trabajo de `TASK-059` a
propósito y encontró supervivientes. Este fichero los nombra **uno a uno**, con su
veredicto y su motivo literal, para que dentro de tres ciclos se pueda volver a
auditar **por nombre** sin releer la conversación. Sin este fichero, «se corrigieron
10 supervivientes» es una afirmación sin dueño.

**Regla del ciclo:** un mutante sobrevive si la suite sigue en verde con el bug
puesto. Un mutante que nadie ha escrito no es un mutante: es una conjetura. Aquí
solo constan los que se **ejecutaron**.

- Fecha: 2026-10-04
- Suite en la auditoría: 131 tests (hoy 132, con el test que fija el fail-closed)
- Veredicto del Paso 4: **FAIL** → Vuelta al Paso 3

---

## Los 10 supervivientes y su cierre

| # | Severidad | Hallazgo del auditor | Veredicto | Cómo se cerró |
|---|---|---|---|---|
| **S8** | MEDIA | `ids_de_tareas` es fail-open: con `tasks.json` ilegible acepta cualquier `TASK-NNN` | **REFUTADO por medición, y corregido igual** | Es **fail-CLOSED**: con `ids=set()`, `TASK-059` → `False`. Peor: el docstring, el aviso y D5 describían degradaciones incompatibles con el código. Se eligió fail-closed (la alternativa es el punto ciego que TASK-059 cierra), se corrigieron las tres fuentes y se añadió `test_los_ids_del_bolsillo_se_leen_y_la_puerta_es_fail_closed` (test 132), que mide el comportamiento sobre una copia del árbol con el tablero corrupto |
| **M6** | MEDIA | La fixture se dimensiona con `MAX_HASHES_PERDIDOS + 1` y `MAX_CICLOS_SIN_HASH + 1`, así que subir el techo a 999 no cambia el veredicto | CIERTO | Literales en la fixture (`TECHO_HASHES = 3`, `TECHO_CICLOS = 2`) y **asertos de igualdad explícita** contra la constante del producto, con la medición (3 hashes muertos, 2 ciclos sin hash) en el mensaje |
| **M6b** | MEDIA | Bajar el techo tampoco lo vigila nadie | CIERTO | El mismo aserto de igualdad: cualquier cambio de valor **falla** el test y obliga a mirar por qué |
| **M9** | MEDIA | El pre-vuelo `_leer_el_repo_si_lo_hay` no está testeado, y su comentario documenta una medición falsa (dice que un `GIT_DIR` no-repo sale con rc=0; son 128) | CIERTO, y la medición era peor de lo que decía | Re-medido con las **tres** cifras reales: directorio vacío → 128/128; **`git init` sin commits → 128 en `rev-parse` pero 0 + `missing` en batch**; con commit → 0/0. El caso del medio es el que obliga al pre-vuelo. Comentario y doc corregidos, y fila (h) del test que lo ejercita con ese repo vacío de commits |
| **M10** | BAJA-MEDIA | La fila que construye 1 ciclo conforme nunca comprueba la línea de informe | CIERTO | Fila añadida: con **un** ciclo conforme la línea tiene que decir `1 conforme(s) a R1`, `0 sin hash declarado` y `0 hash(es) perdido(s) declarados` — la combinación que ninguna otra fila producía |
| **M1c** | BAJA | `_hashes_que_existen` certifica con «≥ 3 campos» y git responde `e60d2a0 (architect) missing` (3 campos): un nombre con espacio se certificaría como existente | CIERTO | Se exige la **forma exacta** `<sha 40|64 hex> <tipo> <tamano>` (`_RESPUESTA_DE_OBJETO`). Fila (i) del test: el nombre con espacio cuenta como **no** resuelto, el patrón rechaza esa línea y acepta la real |
| **S6** | BAJA | El ancla `TASK-12345` contra `{"TASK-1234"}`: el `\b` de salida es lo que lo impide | CIERTO (era un mutante sin cobertura) | Tres aserciones en el test 125: `TASK-12345` con `{"TASK-1234"}` → rechazado; con `{"TASK-12345"}` → aceptado; `TASK-1234` contra `{"TASK-12345"}` → rechazado |
| **S9** | BAJA | El `INFO` de degradación no lo comprueba nadie | CIERTO | Por **subproceso** con la copia degradada: el `INFO ancla-mensaje:` tiene que aparecer, ser **la última** línea `WOPT_*`, ir **antes** de ella, y no dejar nada stageado |
| **T4** | BAJA | El suelo `>= 5` plantillas no vigila nada | CIERTO | Suelo subido al número real, **6**, con mensaje que distingue perder una de ganar una. Además se separó qué es plantilla y qué es mención del comando (`...`, `<mensaje>`), que no lo eran |
| **S4** | — | `_RE_CYCLE_ANCLA` es código muerto: todo `CYCLE-NNN` casa también con el marcador de ciclo | **EQUIVALENTE (no es fallo)** | La **prosa** se corrige: son tres convenciones y solo **dos** formas resolutivas, con la medición del barrido (4 grafías × 10 000 números, 0 contraejemplos). El código no se toca; la constante se queda con un trabajo real: el test reproduce el barrido y demuestra la equivalencia |

---

## Correcciones a la propia auditoría (medidas por el orquestador)

- **S8 no es fail-open.** Es lo contrario, y es **más grave por otro motivo**: con
  `tasks.json` roto el bucle **no puede commitear** un mensaje con `TASK-`. Eso se
  aceptó como decisión de diseño (fail-closed) y se documentó por qué la
  alternativa sería el agujero. Antes de aceptarlo había tres fuentes que se
  contradecían y el código hacía una cuarta cosa; ahora las tres dicen lo que el
  código hace, y un test lo mide.
- **S9 y S4** se cerraron como se propuso: el `INFO` por subproceso, y la prosa en
  vez del código.

## Lo que NO se tocó (y por qué)

- **`RuntimeError: main thread is not in main loop`** al final de la suite, de
  `src/woptimizer/ui/views/process_manager_view.py` (`_load` llama a
  `self.after(0, ...)` desde un hilo sin main loop). Es `src/`, es ajeno a TASK-059
  y no se arregla aquí. **Anotado como deuda viva en `STATUS.md`** con su ancla de
  ruta, porque un `after` sobre una vista destruida es una clase de bug real en
  CustomTkinter, no ruido de test.
- El **agregado `llms-full.txt`** sigue siendo un snapshot viejo (no se regenera en
  cada cambio de docs; el check solo exige el nombre del fichero).

## Re-auditable

| Qué | Dónde |
|---|---|
| Los 10, con motivo literal | este fichero, tabla de arriba |
| El comportamiento fail-closed | `run_tests.py` → test 132 |
| Los techos y su valor medido | `run_tests.py` → test 129, asertos de igualdad |
| El pre-vuelo y sus tres cifras | `run_tests.py` → test 129, fila (h) |
| La forma de la respuesta de git | `run_tests.py` → test 129, fila (i) |
| El `\b` de salida del ancla | `run_tests.py` → test 125, bloque S6 |
| La equivalencia `CYCLE-NNN` | `run_tests.py` → test 125, barrido de 40 000 casos |
| El `INFO` de degradación | `run_tests.py` → test 132, por subproceso |
