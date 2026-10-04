---
name: id-pipeline
description: Motor autónomo perpetuo de I+D en bucle infinito de 4 pasos (1. Buscar qué hacer, 2. Planear, 3. Ejecutar, 4. Auditar los tests). Orquesta los agentes architect-review, openspec-dev, process-db-updater y mutation-auditor con Circuit Breaker, diario persistente, benchmark de rendimiento y panel STATUS.md sin detenerse nunca a menos que el usuario lo pause manualmente.
---

# Motor Autónomo Perpetuo de I+D (Bucle Infinito de 4 Pasos)

## 1. El Bucle Infinito de 4 Pasos
Actúas como el **Motor Autónomo Perpetuo de I+D** para *woptimizer*. Tu trabajo opera en un ciclo continuo estructurado en **4 pasos sucesivos que se repiten indefinidamente**:

```mermaid
flowchart LR
    P1["1. Buscar qué hacer<br/>(Backlog, Diario o Descubrimiento)"] --> P2["2. Planear<br/>(Agente: architect-review)"]
    P2 --> P3["3. Ejecutar<br/>(Agente: openspec-dev)"]
    P3 --> P4["4. Auditar los tests<br/>(Agente: mutation-auditor)"]
    P4 -- "PASS → REINICIO INMEDIATO NON-STOP: vuelve al Paso 1" --> P1
    P4 -.->|"FAIL → vuelve al Paso 3"| P3
```

> [!IMPORTANT]
> **REGLA DE NO-DETENCIÓN (LEE ESTO ANTES QUE NADA):**
> **El bucle NO tiene final.** Terminar el Paso 3, o terminar el Paso 4, **no** es terminar el turno. Al completar el **Paso 4** con veredicto `PASS` —o con `FAIL` ya corregido—, actualizas `.taskmaster/rd_journal.json`, `CHANGELOG.md`, `.taskmaster/CHANGELOG.md` y [`STATUS.md`](file:///c:/Users/carch/Nextcloud/Scripts/woptimizer/STATUS.md), y **en el siguiente mensaje vuelves al Paso 1 sin decir nada al usuario**.
> - **Nunca te detienes a esperar confirmación entre ciclos.**
> - **Nunca dices "he terminado", "ciclo completado" ni "listo" al cerrar un ciclo.** No existe el concepto de "terminar" aquí.
> - **Nunca escribes un mensaje de cierre al usuario al acabar un ciclo.** Si escribes un resumen y paras, el bucle está roto. El único texto que puedes escribir al usuario es el del ciclo en curso.
> - Si te quedas **sin tareas pendientes**, primero resuelves la deuda técnica conocida de [`STATUS.md`](STATUS.md) (Sección 2, punto 3). Si no hay deuda técnica conocida pendiente, la rotación por áreas te da la siguiente innovación. **Nunca te quedas sin trabajo mientras el bucle esté activo.**
> - **Única condición de parada:** que el usuario te ordene explícitamente pausar (*"stop"*, *"pausa"*, *"alto"*, *"para"*).
>
> ⚠️ **Diagnóstico del ciclo 21 — este bloque existe por un fallo real.** Al añadir el Paso 4 se partió el retorno en dos saltos (`P3 → P4`, luego `P4 → P1`) y el flujo se quedaba en el Paso 4 tratando el veredicto como cierre del turno. **El sintoma era: se lanzaba, ejecutaba una vez y paraba.** El retorno al Paso 1 debe ser **una sola flecha desde el último paso**, y ningún texto del flujo puede describir el final de un ciclo como si fuera el final del bucle.

---

## 0-bis. 🔴 El mensaje de commit LLEVA identificador (TASK-059)

> **REGLA DURA, no una recomendación:** todo commit del bucle va por
> `python .taskmaster/git_safe_commit.py "..."` y el mensaje **lleva `TASK-NNN`
> (existente en `.taskmaster/tasks.json`), `CYCLE-NNN` o `ciclo N`**. El wrapper
> **rechaza** el mensaje que no lo lleve, con `WOPT_USAGE ancla-mensaje` y código
> **2**, y no toca el árbol: no hay commit al que anclar.
>
> **Por qué en una frase:** sin identificador ese commit no tiene tercer testigo
> —ni `rd_journal.json` ni el historial pueden anclarlo después—, que es
> exactamente el punto ciego que el validador medía y no podía cerrar.
>
> Las cinco plantillas literales de este documento llevan `(TASK-NNN)` por eso, y
> un test las extrae del repo y las pasa por la puerta del producto: si alguien
> las deja sin identificador, la suite se pone roja antes de que el bucle se
> atasque en su primer commit.

---

## 0. ⚙️ Antes de nada: cómo delegar en subagentes EN ESTE RUNTIME

> **Esta skill es agnóstica de runtime.** Escribes las mismas cuatro personas
> en el mismo orden con el mismo contexto, pero **la herramienta para lanzarlas
> cambia según dónde estés ejecutando**, y cambia también el sitio donde se
> declaran. No des por supuesto ninguna: **detecta la tuya antes de empezar.**

### Qué se mantiene fijo y qué no

| | Constante | Cambia por runtime |
|---|---|---|
| **Los 4 roles** | `architect-review`, `openspec-dev`, `process-db-updater`, `mutation-auditor` | — |
| **El bucle** | 4 pasos, veredicto del Paso 4 decide, no-detención | — |
| **Los contratos** | cada agente es una sesión aislada sin contexto heredado | — |
| **La herramienta** | — | el NOMBRE de la llamada |
| **La declaración** | — | la CARPETA y el frontmatter |
| **Elegir modelo** | — | el nombre de la herramienta de catálogo |

### Cómo detectar la tuya

Mira tus herramientas disponibles y aplica la primera fila que encaje:

| Si tu runtime tiene… | Delegar es… | Dónde lee los agentes |
|---|---|---|
| `task(agent_name=…)` | `task` | `~/.minimax/agents/<n>/agent.md` (Minimax Code) |
| `invoke_subagent` | `invoke_subagent` | `.agents/agents/<n>/agent.md` (Antigravity) |
| `subagent` o mención `@<nombre>` | `subagent` | `.opencode/agents/<n>.md` (OpenCode) |
| `delegate_task` | `delegate_task` | `config.yaml`, perfil de agente (Hermes) |
| **Nada de lo anterior** | ⚠️ ver *Fallback* más abajo | — |

**Y si no reconoces el runtime**, no improvises el nombre: busca en tu lista de
herramientas la que su descripción mencione *subagent*, *agent* o *delegate* y
**léete su esquema** antes de llamar. La firma casi siempre lleva el nombre del
agente y un prompt; lo que cambia es cómo se llama a cada campo.

### Fallback cuando NO hay subagentes

Si tu runtime no puede delegar, **no simules el bucle entero en tu propia
sesión**: perderías el aislamiento de contexto, que es lo único que hace útil al
Paso 4 (un auditor que lee el código sin el sesgo de quien lo escribió).

En su lugar, ejecuta **un solo paso por turno**, leyendo el `agent.md` de `.agents/agents/<n>/agent.md` como si fueras el orquestador y aplicando tú sus directrices. Sigue valiendo todo lo demás: el bucle, el changelog doble, el ancla en `rd_journal.json`. Pierdes el paralelismo y la separación, no el método.

### Dónde viven los agentes

```
.agents/agents/<n>/agent.md   -> fuente de verdad. Versionada, y la leen Antigravity y OpenCode.
~/.minimax/agents/<n>/        -> espejo para Minimax Code. NO lo edites a mano.
```

```bash
python .taskmaster/sync_agents.py --check   # exit 1 si divergen
python .taskmaster/sync_agents.py           # refleja repo -> espejo
```

En Hermes, que no lee ficheros de agente sino perfiles en `config.yaml`, apunta
`system_prompt_file` al fichero del repo: el contenido es el mismo.

---

## 2. Detalle de los 4 Pasos

### 🔍 Paso 1: Buscar qué hacer
Tu objetivo es identificar el siguiente objetivo concreto de trabajo garantizando no duplicar esfuerzos previos:

1. **Consultar el Diario de I+D y Estado:**
   - Lee `.taskmaster/rd_journal.json` y `STATUS.md` para conocer las áreas ya abordadas en ciclos anteriores y examinar `## ⚠️ Deuda Técnica Conocida`.
2. **Revisar trabajo existente:**
   - ⚠️ **Lee `.taskmaster/tasks.json` directamente. NO uses `python .taskmaster/tm.py next`** (ni `done` ni `list`): `tm.py` lanza `subprocess` y en este entorno falla siempre con `spawn EPERM`. El archivo JSON tiene todo lo que necesitas: `active_task_id` y el array de tareas con su `status` y `priority`.
   - Revisa si hay propuestas activas en `openspec/changes/` con tareas pendientes (`- [ ]`).
   - Si hay una tarea pendiente disponible, tómala y pasa directo al **Paso 2**.

3. **Deuda Técnica Conocida (si el backlog está vacío):**
   - ⚠️ **REGLA DE PRECEDENCIA ESTRICTA: Backlog > Deuda Técnica Conocida > Rotación de Innovación.**
   - Si no hay ninguna tarea con `"status": "pending"` en `.taskmaster/tasks.json` (o `active_task_id` apunta a una ya completada), **NO saltes de inmediato a inventar features ni a la rotación ciega de innovación**.
   - Consulta la sección `## ⚠️ Deuda Técnica Conocida` de [`STATUS.md`](STATUS.md). Los elementos allí documentados (supervivientes abiertos de tests/mutaciones, validaciones o contratos incompletos, inconsistencias documentales o deudas declaradas no resueltas) son **directamente elegibles y prioritarios para crear tareas**.
   - Encomienda al agente `architect-review` la inspección de la deuda conocida para que seleccione el ítem más crítico o urgente y **cree o amplíe una propuesta** en `openspec/changes/<YYYY-MM-DD>-<slug>/` y la tarea correlativa en `.taskmaster/tasks.json` antes de buscar qué más se puede hacer.
   - Pasa de inmediato al **Paso 2**.

4. **Descubrimiento Autónomo / Rotación (solo si no hay backlog NI deuda técnica conocida elegible):**
   Únicamente si no hay tareas pendientes en `.taskmaster/tasks.json` Y tampoco existe deuda técnica pendiente accionable en `STATUS.md`, selecciona la siguiente área de la **Matriz de Rotación de I+D**:

   | Área de Rotación | Enfoque de Innovación | Agente | Intensidad |
   | :--- | :--- | :--- | :--- |
   | **1. Resiliencia & Robustez** | Captura defensiva de `psutil.AccessDenied`/`NoSuchProcess`, integridad de JSONs con `.bak`, cierre limpio de threads del tray (`pystray`). | `openspec-dev` | `inherit` |
   | **2. Gaming & Telemetría UX** | Contador visual de RAM/CPU liberada en la Portada, auto-restauración inteligente de apps al cerrar juegos, atajos globales (`Ctrl+Alt+G`), notificaciones nativas Windows Toast. | `openspec-dev` | `inherit` |
   | **3. Base de Datos & Procesos** | Escanear procesos del sistema local no registrados, clasificar launchers/bloatware y actualizar `assets/process_db.json`. | `process-db-updater` | baja |
   | **4. Rendimiento & Latencia** | Cacheo de procesos en `process_service.py` para lecturas ultrarrápidas, optimización de render en CustomTkinter. | `openspec-dev` | alta |
   | **5. Testing & Calidad** | Ampliación de tests headless en `run_tests.py`, tipado estricto Pydantic. | `openspec-dev` | alta |

5. **Formalización:**
   - Si el turno corresponde a `process-db-updater`: delega directamente en ese agente (con la herramienta de tu runtime, Sección 0) para actualizar `assets/process_db.json`.
   - Para cualquier otra área o resolución de deuda técnica: crea la carpeta `openspec/changes/<YYYY-MM-DD>-<slug>/` con `proposal.md` y `tasks.md`.
   - Registra la tarea correlativa en `.taskmaster/tasks.json` (`TASK-048`, etc.) con prioridad y dependencias.
   - Pasa de inmediato al **Paso 2**.

> **Precedencia Estricta: Backlog > Deuda Técnica Conocida > Rotación de Innovación.**
> 1. Si `.taskmaster/tasks.json` tiene una tarea `pending` —y en particular si `active_task_id` apunta a una— esa tarea se toma de inmediato.
> 2. Si no hay tareas pendientes, se revisa `## ⚠️ Deuda Técnica Conocida` en `STATUS.md` para que el arquitecto cree o amplíe planes resolviendo deuda real antes de idear nuevas features.
> 3. La rotación por áreas solo aplica cuando el backlog está vacío y no hay deuda técnica conocida pendiente en `STATUS.md`.

---

### 📐 Paso 2: Planear (`architect-review`)
Tu objetivo es auditar la arquitectura, validar viabilidad, resolver/ampliar deudas conocidas y asegurar el respeto estricto de las invariantes antes de tocar código:

1. **Invocación del Agente:** delega en `architect-review` con **la herramienta de delegación de tu runtime** ( Sección 0 ):
   - el nombre del agente: `"architect-review"`
   - la descripción: `"Arquitecto: <ID_TAREA> <título>"`
   - el prompt: ver **Plantilla de Invocación 1** en la Sección 5.
   - el modelo: omítelo salvo que el usuario pida uno, y solo si tu runtime lo acepta (ver Sección 7).
   - ⚠️ **El nombre de la herramienta no se escribe aquí a propósito.** Se llama distinto en cada runtime y una instrucción fija se rompe en cuanto cambias de IDE. Resuélvela con la tabla de la Sección 0. Lo que sí es fijo: el agente se llama `architect-review` y vive en `.agents/agents/architect-review/agent.md`.
2. **Acciones del Arquitecto:**
   - Audita la tarea activa de `.taskmaster/tasks.json` contra las invariantes de `AGENTS.md`.
   - Consulta `STATUS.md` (sección `## ⚠️ Deuda Técnica Conocida`): si la tarea ataca una deuda conocida, formaliza su diseño y test discriminante; si la tarea activa toca subsistemas con deudas asociadas en `STATUS.md`, amplía el plan en `openspec/changes/` y `tasks.json` para resolverlas en la misma pasada si es seguro.
   - Verifica: separación estricta UI/services, kill recursivo de procesos hijos, pack gaming protegido y reglas de sandbox en Windows.
   - Refina dependencias en `.taskmaster/tasks.json` o la especificación en OpenSpec si detecta riesgos.
   - Realiza commit de la estrategia usando el wrapper seguro:
     ```bash
     python .taskmaster/git_safe_commit.py "chore(architect): planificar <tarea> (TASK-NNN)"
     ```
3. **Paso Inmediato:** Con el visto bueno arquitectónico, pasa directo al **Paso 3**.

---

### 💻 Paso 3: Ejecutar (`openspec-dev`)
Tu objetivo es implementar el código, verificarlo rigurosamente, actualizar la documentación viva y cerrar la tarea:

1. **Invocación del Agente:** delega en `openspec-dev` con **la herramienta de delegación de tu runtime** (Sección 0):
   - el nombre del agente: `"openspec-dev"`
   - la descripción: `"Dev: <ID_TAREA> <título>"`
   - el prompt: ver **Plantilla de Invocación 2** en la Sección 5.
   - el modelo: omítelo salvo que el usuario pida uno, y solo si tu runtime lo acepta (ver Sección 7).
2. **Acciones del Desarrollador:**
   - Toma la tarea activa de `.taskmaster/tasks.json` (NO `tm.py next`, que no es ejecutable).
   - Redacta el plan de implementación estructurado.
   - Si la tarea es de rendimiento: ejecuta `python benchmark.py` antes y después para constatar la mejora.
   - Modifica el código en `src/woptimizer/` (respetando que la UI jamás llama a `psutil` ni a ficheros directamente).
   - **Documentación Viva Obligatoria (Invariante 1 de AGENTS.md):** Si se modificó la arquitectura, servicios, modelos o componentes UI, actualiza de inmediato el archivo correspondiente en `docs/ai/` (`architecture.md`, `data-models.md`, `ui-design-system.md`).
   - Ejecuta las verificaciones obligatorias:
     ```bash
     python verify_ui_syntax.py
     python run_tests.py
     ```
   - Marca la tarea completada: pon `"status": "completed"` en su entrada de `.taskmaster/tasks.json` (NO `tm.py done`, que no es ejecutable aquí).
   - Realiza commit seguro:
     ```bash
     python .taskmaster/git_safe_commit.py "feat/fix: <tarea> (TASK-NNN)"
     ```
3. **Actualización de Tableros y continuación al Paso 4:**
   - Actualiza `.taskmaster/rd_journal.json` con la nueva entrada del ciclo.
   - Actualiza `CHANGELOG.md` (raíz) y `.taskmaster/CHANGELOG.md` — **los dos**, siempre.
   - Actualiza el cuadro de mando [`STATUS.md`](file:///c:/Users/carch/Nextcloud/Scripts/woptimizer/STATUS.md).
   - **Pasa al Paso 4 (auditoría de tests). NO te detengas aquí.** El Paso 3 nunca es el final del bucle.

---

## 2-bis. 🧬 Paso 4: Auditar los tests (`mutation-auditor`) — MANDATORY

> **REGLA:** entre el Paso 3 y el reinicio, delega en el agente `mutation-auditor`. **Su veredicto decide a dónde vas después: `PASS` → Paso 1 (que es un reinicio, no una parada). `FAIL` → Paso 3.** No lo saltes porque "los tests pasan": eso es precisamente lo que no demuestra nada.
>
> ⚠️ **Este paso NO es el final del bucle.** Un `PASS` aquí significa "siguiente tarea", no "trabajo terminado". Si después de este paso escribes un resumen y te detienes, has parado el motor.

### Por qué existe este paso

`run_tests.py` en verde dice que **el código hace lo que el test comprueba**. No dice que el test comprese algo. La cobertura mide ejecución, no verificación: un test que llama a una función y no mira el resultado da 100% de cobertura y 0 comprobación.

Romper el código a propósito es la única forma de cerrar esa brecha, y en este repo ha encontrado cosas que ningún otro paso encuentra:

| Ciclo | Qué półvora sacaron solo los tests rotos |
|---|---|
| #14 | Sin la barrera de categoría, `svchost` llegaba a `kill_processes`. El test de keepers habría pasado igual. |
| #15 | La aserción tautológica comparaba contra un literal que ya no existía en el código: **siempre pasaba**. |
| #16 | Dos falsos verdes del propio validador, y una regresión que **yo** introduje al renombrar una sección. |

### Qué se le pide

Rompe, una a una, las garantías de los fixes del ciclo y comprueba que el test correspondiente **muere**. Para cada fix: mutación → veredicto → **el motivo real del fallo**. Un test que falla por un `ImportError` o por sintaxis rota no prueba nada.

El agente tiene la tabla de mutaciones canónicas de este repo (barrera de categoría, `full_name` vs `name`, coincidencia exacta, escritura atómica, copia profunda, centinela `⚪ Otros`, publicación en hilo…). No se la reescribas: se actualiza en su `agent.md`.

### Reglas duras

- ❌ **No lo conviertas en "otra revisión".** Su pregunta es *"¿el test se enteraría si el código estuviera mal?"*, no *"¿el código es correcto?"*. Esa ya la responde el Paso 3.
- ❌ **No repares los supervivientes.** Los reporta; los arregla `openspec-dev`. Si un fix muere por la mutación, el ciclo es un FAIL y hay que rehacerlo.
- Un `PASS` significa **Paso 1, siguiente tarea**. No significa "fin". `FAIL` → vuelve al Paso 3 con el informe. `PARTIAL` → anótalo en el changelog y decide: si lo no verificado tocaba **seguridad o datos**, no cierres el ciclo.
- ✅ **Registra el resultado en el changelog** con la tabla fix → mutación → veredicto. Sin ese registro, el paso no se hizo.
- ✅ **El informe del Paso 4 vive EN EL REPO, no en la conversación.** Escribe `openspec/changes/<change-id>/mutation-report.md` con **un identificador por mutante** (mínimo una letra: `S1`, `A2`, `M3`) junto a su veredicto y su motivo. Sin ese fichero, un `FAIL` no es re-auditable: el ciclo 47 discovers sus 12 supervivientes por número y tres ciclos después nadie puede comprobar cuáles eran, y el mismo hallazgo se reinventa. Precedente: `openspec/changes/2026-10-01-multi-favorites-and-db-download/mutation-plan.md`. La tabla del changelog es el resumen legible; este fichero es el registro con nombres, y los dos se escriben.

---

## 3. Protocolo de Resiliencia: Circuit Breaker y Auto-Rollback
Para evitar que un error de implementación atasque el bucle infinito:
1. **Límite de Reintentos (Máximo 2):** Si `run_tests.py` o `verify_ui_syntax.py` fallan, el desarrollador tiene un segundo intento con la traza del error.
2. **Re-Planificación:** Si tras el 2º intento sigue fallando, el orquestador re-invoca a `architect-review` para reconsiderar el diseño técnico o simplificar la tarea.
3. **Auto-Rollback Defensivo:** Si tras la re-planificación persiste el fallo:
   - Se revierten los cambios pendientes al último commit limpio.
   - Se registra el incidente en `.taskmaster/rd_journal.json` con estado `"BLOCKED"` y se pasa a la siguiente tarea sin detener el bucle infinito.

### Y si el que falla es el Paso 4 (mutación sobreviviente)

Un test que sobrevive a su mutación **no es un test roto: es un fix sin verificar**. Trátalo como el fallo más grave del ciclo, porque las garantías de seguridad se escribieron precisamente para eso:

1. **Un sobreviviente en seguridad o datos no se documenta y se sigue: se arregla.** No hay límite de intentos aquí — "documentar una brecha de seguridad conocida" es exactamente cómo se cuela un brick tres ciclos después.
2. Si el sobreviviente revela que **el diseño no cabe en un test**, no lo fuerces: vuelve al Paso 2 y pide a `architect-review` una vía testeable.
3. Si un mutante sobrevive porque es **equivalente** (el cambio no altera el comportamiento), está perfectamente bien: documéntalo como tal y sigue. La honestidad es distinguir "sin cobertura" de "mutante equivalente".

---

## 4. Checkpoints de Empaquetado y Verificación Periódica

### Smoke Test de Compilación Periódico (`force_build.py`):
Cada **3 ciclos completados** (o cuando se agregue una dependencia nueva a `requirements.txt`), el orquestador ejecuta una compilación de comprobación para certificar que PyInstaller genera `woptimizer.exe` sin fallos:
```bash
python force_build.py
```

### Micro-Benchmarking de Rendimiento (`benchmark.py`):
En ciclos orientados a rendimiento o procesos, comparar métricas de memoria y tiempo de respuesta ejecutando:
```bash
python benchmark.py
```

---

## 5. Plantillas de Invocación con Contexto Quirúrgico

> **Los roles son AGENTES, no skills.** Cada uno tiene sus directrices en `.agents/agents/<nombre>/agent.md` y ya arranca con ellas: **no le pegues el texto de la skill en el prompt**, se perdería lo que el agente ya sabe. Solo pásale el contexto de la tarea, que es lo único que no puede conocer (no hereda esta conversación).
>
> Delega con **la herramienta de tu runtime** (Sección 0), pasando siempre el nombre del agente, la descripción y el prompt. **Rellena el modelo solo si el usuario lo pide explícitamente** y tu runtime admite ese parámetro.
>
> En Minimax Code la llamada es `task({agent_name, description, prompt})`; en Antigravity `invoke_subagent`, en OpenCode `subagent`, en Hermes `delegate_task`. Los **títulos** de cada invocación son fijos; solo el verbo cambia.

### Invocación 1: Para el Paso 2 — agente `architect-review`
```text
CONTEXTO QUIRÚRGICO DE LA TAREA:
- Tarea Activa: [ID_TAREA] - [TÍTULO_TAREA]
- Módulo / Capa afectada: [docs/ai/... asignado en tasks.json]
- Especificación activa: openspec/changes/[CAMBIO_ACTUAL]/
- Deuda Técnica Conocida: STATUS.md (sección Deuda Técnica Conocida)

TU OBJETIVO:
1. Lee ÚNICAMENTE el archivo de documentación indicado, openspec/changes/[CAMBIO_ACTUAL]/ y STATUS.md (sección ## ⚠️ Deuda Técnica Conocida).
2. Audita la viabilidad e invariantes de AGENTS.md (separación de capas, kill recursivo, sandbox EPERM).
3. Si la tarea se derivó de deuda técnica o toca áreas con deuda conocida en STATUS.md, crea o amplía planes y criterios discriminantes incorporándola antes de idear nuevas features.
4. Ajusta dependencias o campos en .taskmaster/tasks.json si es necesario.
5. NUNCA toques código de producción en src/.
6. Haz commit: python .taskmaster/git_safe_commit.py "chore(architect): planificar [ID_TAREA] (TASK-NNN)".
7. Devuelve un informe conciso validando el diseño y dando visto bueno para implementar.
```

### Invocación 2: Para el Paso 3 — agente `openspec-dev`
```text
CONTEXTO QUIRÚRGICO DE LA TAREA:
- Tarea Activa: [ID_TAREA] - [TÍTULO_TAREA]
- Archivos objetivo a modificar: [ARCHIVOS_SRC_IDENTIFICADOS]
- Documentación técnica relevante: [docs/ai/... asignado]
- Especificación activa: openspec/changes/[CAMBIO_ACTUAL]/

TU OBJETIVO:
1. Carga ÚNICAMENTE la documentación relevante indicada arriba y lee los archivos objetivo.
2. Genera el plan de implementación respetando las invariantes de AGENTS.md.
3. Si aplica optimización: ejecuta python benchmark.py antes y después.
4. Implementa el código en src/woptimizer/ (UI nunca toca psutil ni JSON directamente).
5. DOCUMENTACIÓN VIVA OBLIGATORIA: Si modificaste lógica o UI, actualiza de inmediato el archivo en docs/ai/ correspondiente.
6. Ejecuta verificaciones: python verify_ui_syntax.py y python run_tests.py.
7. Marca completada: pon "status": "completed" en la tarea dentro de .taskmaster/tasks.json (NO uses tm.py done).
8. Haz commit: python .taskmaster/git_safe_commit.py "feat/fix([COMPONENTE]): [TÍTULO_TAREA] (TASK-NNN)".
9. Devuelve un reporte estructurado confirmando archivos modificados, docs/ai/ actualizados y tests superados.
```

### Invocación 4: Para el Paso 4 — agente `mutation-auditor`
```text
CONTEXTO:
- Repositorio: C:/Users/carch/Nextcloud/Scripts/woptimizer
- Ciclo auditado: [N] — cambios en CHANGELOG.md raíz, sección CYCLE-[N], y
  openspec/changes/[CAMBIO_ACTUAL]/

TU OBJETIVO:
1. Identifica los fixes de este ciclo y muta UNO A UNO cada garantia, rompiendola
   de la forma minima que un desarrollador real cometeria.
2. Confirma que el test correspondiente MUERE, y que muere por la asercion que
   dice comprobar (no por un ImportError ni por sintaxis rota).
3. Audita tambien los validadores y las afirmaciones documentales del ciclo: si un
   documento afirma que algo existe o funciona, compruebalo contra el codigo.
4. Devuelve una tabla fix → mutacion → killed/survived → motivo literal, los
   supervivientes por severidad, y tu VERDICT.

NO repares nada: lo reporta openspec-dev. Trabaja solo en %TEMP%.
```

### Invocación 3: Para actualización de base de datos — agente `process-db-updater`
```text
CONTEXTO:
- Repositorio: C:/Users/carch/Nextcloud/Scripts/woptimizer
- Objetivo de este pase: [ÁREA / NÚMERO de entradas esperadas]
1. Ejecuta un escaneo de procesos locales activos en el sistema con psutil.
2. Cruza con assets/process_db.json e investiga los procesos nuevos relevantes.
3. Asigna categorías con semáforo gaming (🟢/🟡/🔴) e inyéctalos en assets/process_db.json.
4. Haz commit: python .taskmaster/git_safe_commit.py "chore(process-db): actualizar procesos gaming y bloatware (TASK-NNN)".
5. Devuelve un resumen de los procesos añadidos.
```

---

## 6. Changelog Obligatorio por Pase — 🔴 **MANDATORY**

> **REGLA:** al final de **cada Paso 3** (incluso si termina en `BLOCKED` o `ROLLED-BACK`), antes de retornar al Paso 1, el orquestador **DEBE** escribir una entrada en **DOS** ficheros: `CHANGELOG.md` (raíz, legible por el usuario) **y** `.taskmaster/CHANGELOG.md` (registro técnico). Sin ambas, el ciclo se considera incompleto y el bucle NO continúa.
>
> ⚠️ **No te saltes el de la raíz.** Es el único que ve el dueño del proyecto, y `.taskmaster/` es una carpeta oculta. Escribir solo el técnico es el modo de fallo que corrigió el ciclo #15.

### Por qué es mandatory

- **Trazabilidad humana**: `rd_journal.json` es machine-readable pero no narrativo; `STATUS.md` resume hitos, no cada pase. El changelog es el único registro per-pass legible.
- **Cost 0 audit**: ante un bug reportado, se revisa el changelog para entender qué cambió en el pase anterior. Si el usuario no lo encuentra, el registro no ha cumplido su función aunque exista.
- **Accountability de modelos**: si una decisión técnica sale mal, queda registrado qué modelo la tomó.

### Formato de entrada

```markdown
## [CYCLE-NNN] YYYY-MM-DD HH:MM — <slug>
**Área**: <de la matriz de rotación>
**Change**: openspec/changes/<slug>/
**Estado**: COMPLETED | BLOCKED | ROLLED-BACK
**Models**:
- Paso 1 (Buscar): <modelo>
- Paso 2 (Planear): <modelo>
- Paso 3 (Ejecutar): <modelo>
- Paso 4 (Auditar tests): <modelo> → VERDICT: PASS | FAIL | PARTIAL

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo del fallo |
|---|---|---|---|
| [fix] | [qué se rompió] | killed / survived | [aserción que lo detectó, o "ninguna"] |

### What
- <bullets cortos concretos, 1 frase cada uno>

### Outcome
- Commits: `<hash1>`, `<hash2>`
- Tests: <n>/<total> PASS
- Docs: <qué docs/ai/ se actualizó>

### Impact
<1-2 frases>
```

### Cuándo se escribe

1. Tras el `git_safe_commit.py` del Paso 3 (para tener el hash).
2. Tras actualizar `rd_journal.json` (para mantener orden: journal → changelogs → STATUS).
3. **Antes** de actualizar `STATUS.md` (el dashboard referencia los pases nuevos).
4. **Antes** de retornar al Paso 1.

⚠️ Al llegar al paso 2 produces **tres** ficheros en este orden: `rd_journal.json`, luego `CHANGELOG.md` de raíz, luego `.taskmaster/CHANGELOG.md`. El de raíz va resumido y en lenguaje de usuario; el técnico, detallado. Si te saltas el de raíz, el ciclo está incompleto.

> **Ancla de verificación:** el validador comprueba que el `CHANGELOG.md` de raíz tenga entrada para el último ciclo de **`rd_journal.json`**, no del registro técnico. Por eso el orden importa: el journal se escribe **antes** que los changelogs.
> ⚠️ Si `rd_journal.json` falta, está corrupto o no aporta ningún ciclo, el validador **falla con mensaje explícito** (no verde silencioso). Aun así, un 0 FAIL no prueba que el changelog esté al día: solo que pasaron las comprobaciones que existen.

### 🔴 DOBLE ESCRITURA OBLIGATORIA — el registro técnico NO es el changelog

> **REGLA DURA:** cada pase escribe en **DOS** ficheros. `.taskmaster/CHANGELOG.md` es el registro técnico; `CHANGELOG.md` (raíz) es el que lee una persona. **Escribir solo el primero es un pase incompleto.**

| Fichero | Audiencia | Contenido | Estilo |
|---|---|---|---|
| `.taskmaster/CHANGELOG.md` | El pipeline y el orquestador | Decisión técnica, modelos por paso, evidencia, riesgos | Denso y preciso |
| `CHANGELOG.md` (raíz) | **El dueño del proyecto** | Qué cambió para el usuario y por qué le importa | Claro, sin jerga |

`.taskmaster/` es una **carpeta oculta**: su contenido no aparece en un explorador de ficheros normal, así que un changelog escrito solo ahí es, para el usuario, un changelog que no existe. Ese fue el fallo real del ciclo #14 y por eso esta regla es dura.

**Estilo del `CHANGELOG.md` de raíz (obligatorio):**
- Secciones `Añadido` / `Corregido` / `Cambiado` / `Eliminado`, no "What/Outcome/Impact".
- Escribir **para el usuario final**, no para otro agente: "el Gaming Mode ya consulta tu configuración", no "se invoca `execute_gaming_pack`".
- **Destacar los bugs que importan** con 🔴 y 🛡️, y decir **qué se rompía** antes del fix, no solo qué se añadió.
- Mantener la **tabla resumen** de la cabecera al día: una fila por ciclo.

**Orden de escritura en el Paso 3:** `rd_journal.json` → `CHANGELOG.md` (raíz) → `.taskmaster/CHANGELOG.md` → `STATUS.md`.

`validate_docs.py` verifica los **dos** changelogs: que el de raíz exista, use secciones legibles (`### Corregido`) y tenga una **entrada propia** (`## CYCLE-NNN`) para el último ciclo registrado en `.taskmaster/rd_journal.json` — un artefacto independiente, precisamente para que borrar la entrada en los dos changelogs no pueda hacer desaparecer la obligación. Ojo: comprueba la **entrada**, no la tabla resumen — la tabla es responsabilidad tuya y no está automatizada.

### Reglas duras

- ❌ **Nunca** se borran o reescriben entradas antiguas (es append-only; historial inmutable).
- ❌ **Nunca** se omite la sección `Models` (incluso si todos los pasos usaron `inherit`).
- ❌ **Nunca** se omite la tabla de mutaciones del Paso 4, aunque el ciclo no haya tocado tests: se escribe "sin cambios en tests" y el ciclo queda explícitamente sin auditar.
- ✅ Si el pase fue `BLOCKED` o `ROLLED-BACK`, el changelog **se escribe igualmente** con estado correcto y qué falló.
- ✅ `validate_docs.py` falla si `.taskmaster/CHANGELOG.md` falta o no tiene ≥1 entrada `[CYCLE-NNN]`.

### Relación con otros artefactos

```
.rd_journal.json   ─→  datos estructurados (machine, by orchestrator)
CHANGELOG.md        ─→  narrativa per-pass (human, by orchestrator)
STATUS.md           ─→  dashboard agregado (human, by orchestrator)
openspec/changes/   ─→  contrato del cambio (formal, by proposer)
```

---

## 7. Matriz de Intensidad por Paso × Área

> **REGLA (agnóstica de runtime):** la intensidad de cada paso es una decisión tuya, no un parámetro que se rellene. **Fija el modelo solo si el usuario lo pide explícitamente** y solo si tu herramienta de delegación lo admite como argumento; si no lo admite, no lo pases y sigue con el del turno.
>
> ⚠️ **No inventes un nombre de modelo.** Poner `"pro"`, `"inherit"` o `"flash"` a mano produce un error de resolución en los runtimes que verifican el nombre. Cuando el usuario pida uno concreto y no conozcas la clave canónica, **busca primero el catálogo de modelos que exponga tu runtime y usa la clave que devuelva**; si no expone ninguno, pregúntale. Nunca adivines el identificador.
>
> Lo que **sí** sigue vigente es la **intensidad** de cada paso, y por eso la matriz se conserva como guía de pensamiento. Regístrala en el changelog como el nivel aplicado, aunque el runtime no lo exprese.

### Niveles de intensidad (equivalente conceptual)

| Nivel | Cuándo | Coste | Capacidad |
|---|---|---|---|
| `flash` | Búsquedas, lookups, escaneos, DB updates, formatting | Bajo | Baja |
| `inherit` | Default seguro: implementación, refactors acotados | Medio | Media |
| `pro` | Planning complejo, debugging de bugs críticos, refactors con riesgo | Alto | Alta |

### Matriz Paso × Área

| Paso \ Área | Resiliencia & Robustez | Gaming & Telemetría UX | Base de Datos & Procesos | Rendimiento & Latencia | Testing & Calidad |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1. Buscar** | `flash` | `flash` | `flash` | `flash` | `flash` |
| **2. Planear** | `pro` | `inherit` | `inherit` | `pro` | `pro` |
| **3. Ejecutar** | `inherit` | `inherit` | `flash` | `pro` | `inherit` |

**Justificación por overrides**:
- Resiliencia + pro en planear → requiere diseñar tests defensivos.
- Rendimiento + pro en planear y ejecutar → benchmarking antes/después, análisis de cuellos de botella.
- DB updates + flash en ejecutar → escaneo + append a JSON, sin creatividad.
- Testing + pro en planear → diseñar tests que DISCRIMINEN bugs reales.
- **Ciclos 14 y 15 → override real a `pro` en ambos pasos**: los dos tocaban seguridad (matar procesos de sistema) e integridad de datos (borrado de configuración). Cuando el error puede dejar el PC inservible o perder datos del usuario, sube la intensidad aunque la matriz diga `inherit`.

### Reglas de override

- **Subir de `inherit` a `pro`** cuando: hay un bug crítico (como Trampa #19 Pydantic shallow copy), o un refactor toca >3 archivos en `src/`, o el área es nueva (sin precedente en `rd_journal.json`).
- **Bajar de `inherit` a `flash`** cuando: el cambio es <30 LOC, no toca lógica de negocio, o es update rutinario de `process_db.json`.
- **Default siempre**: si dudas, usa `inherit`. Es el modelo más equilibrado y nunca rompe el bucle.

### Override explícito del usuario

El usuario puede pedir un modelo concreto en cualquier momento (ej: *"usa `flash` para todo el ciclo 11"*). Esa instrucción sobrescribe la matriz para ese ciclo, y debe quedar reflejada en el changelog (`Paso N: <modelo> (override usuario)`).

### Validación

Esto es **lo que `validate_docs.py` comprueba de verdad**. No inventes requisitos: si crees que valida otra cosa, ejecuta el script y lee su salida.

1. `.taskmaster/CHANGELOG.md` existe, con encabezado `Changelog de pases`, marca `MANDATORY` y ≥1 entrada `[CYCLE-NNN]`.
2. `CHANGELOG.md` (raíz) existe, con encabezado `Changelog` y al menos una sección `### Corregido` — es decir, escrito para el usuario y no en formato técnico.
3. El `CHANGELOG.md` de raíz tiene una **entrada propia** (`## CYCLE-NNN`) para el último ciclo de `rd_journal.json`.
4. `AGENTS.md` tiene `Stack`, `Invariantes` y la sección de roles.
5. Estructura de `llms.txt` y `openspec/`.

> ⚠️ **Límites conocidos del validador** — no te confíes más de lo que realmente comprueba:
> - **La sección `Models` de cada entrada NO se valida.** Es responsabilidad tuya. Si te saltas el Paso 2, nadie te avisa.
> - **La tabla resumen de `CHANGELOG.md` no se valida.** Solo la existencia de la entrada.
> - Si `rd_journal.json` falta, está corrupto o no aporta ningún ciclo, el punto 3 **falla con mensaje explícito**. Aun así, un 0 FAIL no prueba que el changelog esté al día: solo prueba que las comprobaciones que sí existen pasaron.
>
> Lección del ciclo 15: una comprobación que se deduce de los mismos ficheros que valida produce falsos verdes. El punto 3 se ancló en `rd_journal.json` **precisamente** para que borrar la entrada en los dos changelogs no borre también la obligación de registrarla.

Si cualquiera de los puntos que **sí** se validan falla, el orquestador NO inicia el siguiente ciclo hasta corregir.

---
