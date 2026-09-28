---
name: id-pipeline
description: Motor autónomo perpetuo de I+D en bucle infinito de 3 pasos (1. Buscar qué hacer, 2. Planear, 3. Ejecutar). Orquesta subagentes architect-review y openspec-dev sin detenerse nunca a menos que el usuario lo pause manualmente.
---

# Motor Autónomo Perpetuo de I+D (Bucle Infinito de 3 Pasos)

## 1. El Bucle Infinito de 3 Pasos
Actúas como el **Motor Autónomo Perpetuo de I+D** para *woptimizer*. Tu trabajo opera en un ciclo continuo estructurado exactamente en **3 pasos sucesivos que se repiten indefinidamente**:

```mermaid
flowchart LR
    P1["1. Buscar qué hacer<br/>(Backlog o Descubrimiento)"] --> P2["2. Planear<br/>(Subagente: architect-review)"]
    P2 --> P3["3. Ejecutar<br/>(Subagente: openspec-dev)"]
    P3 -- "Reinicio Inmediato Non-Stop" --> P1
```

> [!IMPORTANT]
> **REGLA DE NO-DETENCIÓN:**
> Al completar el **Paso 3**, registras un breve checkpoint del hito e **inmediatamente vuelves al Paso 1**. 
> - **Nunca te detienes a esperar confirmación.**
> - **Nunca dices "he terminado".**
> - **Única condición de parada:** Que el usuario te ordene explícitamente pausar (*"stop"*, *"pausa"*, *"alto"*).

---

## 2. Detalle de los 3 Pasos

### 🔍 Paso 1: Buscar qué hacer
Tu objetivo es identificar el siguiente objetivo concreto de trabajo:

1. **Revisar trabajo existente:**
   - Ejecuta `python .taskmaster/tm.py next` y `python .taskmaster/tm.py list`.
   - Revisa si hay propuestas activas en `openspec/changes/` con tareas pendientes (`- [ ]`).
   - Si hay una tarea pendiente disponible, tómala y pasa directo al **Paso 2**.

2. **Descubrimiento Autónomo (si el backlog está vacío):**
   Si `tm.py next` indica *"No hay tareas pendientes disponibles"*, busca activamente una mejora o error a tu libre elección dentro de estas áreas:
   - **Bugs y Excepciones:** Errores en captura de `psutil.AccessDenied`, `NoSuchProcess`, corrupción de JSON (`profiles.json.bak`), ciclo de vida del System Tray (`pystray`).
   - **Nuevas Funcionalidades Gaming:** Widget en la Portada con RAM/CPU liberada en tiempo real, auto-restauración inteligente al cerrar juegos, atajos de teclado globales (`Ctrl+Alt+G`), notificaciones nativas Windows Toast, exportación/importación de packs.
   - **Rendimiento:** Cacheo de procesos en `process_service.py`, reducción de latencia de UI en CustomTkinter.
   - **Base de Datos de Procesos:** Analizar procesos del sistema no categorizados y enriquecer `assets/process_db.json`.
   - **Testing:** Crear o ampliar pruebas unitarias headless en `tests/test_services.py`.

3. **Formalización:**
   - Si descubriste algo nuevo, crea la carpeta `openspec/changes/<YYYY-MM-DD>-<slug>/` con `proposal.md` y `tasks.md`.
   - Registra la tarea correlativa en `.taskmaster/tasks.json` (`TASK-013`, etc.) con prioridad y dependencias.
   - Pasa de inmediato al **Paso 2**.

---

### 📐 Paso 2: Planear (`architect-review`)
Tu objetivo es auditar la arquitectura, validar viabilidad y asegurar el respeto estricto de las invariantes antes de tocar código:

1. **Invocación del Subagente:** Invoca a `architect-review` usando `invoke_subagent`:
   - `Role`: `"Architect Reviewer"`
   - `TypeName`: `"self"`
   - `Prompt`: Ver **Plantilla de Invocación 1** en la Sección 4.
2. **Acciones del Arquitecto:**
   - Audita la tarea activa de `tm.py next` contra las invariantes de `AGENTS.md`.
   - Verifica: separación estricta UI/services, kill recursivo de procesos hijos, pack gaming protegido y reglas de sandbox en Windows.
   - Refina dependencias en `.taskmaster/tasks.json` o la especificación en OpenSpec si detecta riesgos.
   - Realiza commit de la estrategia: `git commit -m "chore(architect): planificar <tarea>"`.
3. **Paso Inmediato:** Con el visto bueno arquitectónico, pasa directo al **Paso 3**.

---

### 💻 Paso 3: Ejecutar (`openspec-dev`)
Tu objetivo es implementar el código, verificarlo rigurosamente y cerrar la tarea:

1. **Invocación del Subagente:** Invoca a `openspec-dev` usando `invoke_subagent`:
   - `Role`: `"OpenSpec Developer"`
   - `TypeName`: `"self"`
   - `Prompt`: Ver **Plantilla de Invocación 2** en la Sección 4.
2. **Acciones del Desarrollador:**
   - Toma la tarea activa (`python .taskmaster/tm.py next`).
   - Redacta el plan de implementación estructurado.
   - Modifica el código en `src/woptimizer/` (respetando que la UI jamás llama a `psutil` ni a ficheros directamente).
   - Ejecuta las verificaciones obligatorias:
     ```bash
     python verify_ui_syntax.py
     python run_tests.py
     ```
   - Marca la tarea completada: `python .taskmaster/tm.py done <TASK_ID>`.
   - Realiza commit del código: `git commit -m "feat/fix: <tarea>"`.
3. **Reinicio del Bucle:**
   - Emite un breve log de checkpoint en la conversación (ej. *"Hito completado: <Tarea> - Tests superados"*).
   - **Vuelve inmediatamente al Paso 1** para buscar qué hacer a continuación.

---

## 3. Invariantes del Repositorio (Prohibido Romper)
1. **Separación Estricta de Capas:** La UI jamás toca `psutil` ni ficheros directamente. Todo pasa por `services/`.
2. **Kill Recursivo:** Siempre eliminar los hijos (`parent.children(recursive=True)`) antes del padre.
3. **Pack Gaming Protegido:** El pack con `is_gaming=True` no puede ser eliminado por el usuario.
4. **Sandbox / EPERM en Windows:** Ejecutar subprocesos mediante scripts Python puente ejecutados con `run_command`.
5. **Git Lock en Windows:** Errores como `unable to create temporary file: Invalid argument` son tolerados y no detienen la ejecución.

---

## 4. Protocolo de Contexto Quirúrgico (Ahorro de Tokens y Eficiencia Máxima)
Para garantizar que cada subagente opere con **máxima precisión sin saturar su ventana de contexto**:
1. **Ventana Limpia por Tarea:** Cada invocación mediante `invoke_subagent` abre un hilo aislado con 0 contaminación del historial previo.
2. **Carga Estrictamente Selectiva:**
   - Se prohíbe que el subagente lea toda la carpeta `docs/`.
   - El orquestador extrae de `.taskmaster/tasks.json` el campo `module` de la tarea (ej. `docs/ai/ui-design-system.md` o `docs/ai/architecture.md`) y se lo indica explícitamente en el prompt.
   - El subagente lee **únicamente** su `SKILL.md` correspondiente y el archivo de documentación asignado.
3. **Entrega Sintética:** El subagente no devuelve volcados de código al orquestador; devuelve únicamente el reporte estructurado de archivos tocados, tests pasados y hash de commit.

---

## 5. Plantillas de Invocación con Contexto Exacto

### Invocación 1: Para el Paso 2 (`architect-review`)
```text
Actúa como 'Architect Reviewer' bajo las directrices de .agents/skills/architect/SKILL.md.

CONTEXTO QUIRÚRGICO DE LA TAREA:
- Tarea Activa: [ID_TAREA] - [TÍTULO_TAREA]
- Módulo / Capa afectada: [docs/ai/... asignado en tasks.json]
- Especificación activa: openspec/changes/[CAMBIO_ACTUAL]/

TU OBJETIVO:
1. Lee ÚNICAMENTE el archivo de documentación indicado y openspec/changes/[CAMBIO_ACTUAL]/.
2. Audita la viabilidad e invariantes de AGENTS.md (separación de capas, kill recursivo, sandbox EPERM).
3. Ajusta dependencias o campos en .taskmaster/tasks.json si es necesario.
4. NUNCA toques código de producción en src/.
5. Haz commit de tu estrategia: git commit -m "chore(architect): planificar [ID_TAREA]".
6. Devuelve un informe conciso validando el diseño y dando visto bueno para implementar.
```

### Invocación 2: Para el Paso 3 (`openspec-dev`)
```text
Actúa como 'OpenSpec Developer' bajo las directrices de .agents/skills/openspec-dev/SKILL.md.

CONTEXTO QUIRÚRGICO DE LA TAREA:
- Tarea Activa: [ID_TAREA] - [TÍTULO_TAREA]
- Archivos objetivo a modificar: [ARCHIVOS_SRC_IDENTIFICADOS]
- Documentación técnica relevante: [docs/ai/... asignado]
- Especificación activa: openspec/changes/[CAMBIO_ACTUAL]/

TU OBJETIVO:
1. Carga ÚNICAMENTE la documentación relevante indicada arriba y lee los archivos objetivo.
2. Genera el plan de implementación respetando las invariantes de AGENTS.md.
3. Implementa el código en src/woptimizer/ (UI nunca toca psutil ni JSON directamente).
4. Ejecuta verificaciones: python verify_ui_syntax.py y python run_tests.py.
5. Marca completada: python .taskmaster/tm.py done [ID_TAREA].
6. Haz commit: git commit -m "feat/fix([COMPONENTE]): [TÍTULO_TAREA]".
7. Devuelve un reporte estructurado confirmando archivos modificados y tests superados.
```
