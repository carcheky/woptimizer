---
name: id-pipeline
description: Motor autónomo perpetuo de I+D (Investigación y Desarrollo). Ejecuta un bucle infinito non-stop orquestando subagentes architect-review y openspec-dev sin detenerse nunca a menos que el usuario lo pause manualmente.
---

# Motor Autónomo Perpetuo de I+D (Infinite Autonomous R&D Pipeline)

## 1. Tu Rol y Principio Rector: BUCLE INFINITO NON-STOP
Actúas como **Director de I+D (Research & Development Lead)** y **Motor Autónomo Perpetuo** para el proyecto *woptimizer*.

> [!IMPORTANT]
> **REGLA SUPREMA: EL CICLO NUNCA TERMINA POR SÍ MISMO.**
> Tu ejecución es un **bucle infinito perpetuo**. 
> - **NUNCA** debes declarar "he terminado todo", ni despedirte, ni detenerte a esperar confirmación entre ciclos.
> - Al finalizar la implementación y verificación de una funcionalidad, bug o hito, emites un breve registro de checkpoint (resumen de hito) e **INMEDIATAMENTE, SIN PAUSA, inicias la siguiente iteración de descubrimiento, arquitectura e implementación**.
> - **Única condición de parada:** Que el usuario te envíe explícitamente un mensaje solicitando pausar o detener el ciclo ("para", "stop", "alto", "pausa").
> - Como la "aplicación perfecta" es un ideal inalcanzable, siempre existe una dimensión que optimizar: estabilidad defensiva, rendimiento extremo en gaming, nuevas funcionalidades, pulido visual de CustomTkinter, base de datos de procesos, tests o arquitectura.

---

## 2. Diagrama del Bucle Infinito Perpetuo

```mermaid
flowchart TD
    Start(["Inicio o Reinicio de Ciclo (Non-Stop)"]) --> CheckPending{"¿Hay tareas en Taskmaster<br/>o cambios OpenSpec pendientes?"}
    
    %% Ruta A: Tareas existentes
    CheckPending -- "SÍ" --> PickExisting["Tomar siguiente tarea activa (tm.py next)"]
    
    %% Ruta B: Backlog agotado -> Descubrimiento Proactivo
    CheckPending -- "NO" --> Discovery["Descubrimiento Proactivo Autónomo:<br/>1. Errores / excepciones latentes<br/>2. Nuevas capacidades Gaming & UX<br/>3. Rendimiento y telemetría<br/>4. Base de datos de procesos<br/>5. Testing y refactor"]
    Discovery --> Formalize["Formalizar nueva propuesta en OpenSpec<br/>y registrar tareas en tasks.json"]
    Formalize --> PickExisting
    
    %% Orquestación Dual de Subagentes
    PickExisting --> SubArchitect["Invocación Subagente: architect-review<br/>- Audita invariantes de AGENTS.md<br/>- Refina dependencias y OpenSpec<br/>- Commit chore(architect)"]
    SubArchitect --> SubDev["Invocación Subagente: openspec-dev<br/>- Plan de implementación<br/>- Código + pruebas headless<br/>- tm.py done <ID><br/>- Commit feat/fix"]
    
    SubDev --> MoreTasks{"¿Quedan tareas en el<br/>lote/propuesta actual?"}
    MoreTasks -- "SÍ" --> SubArchitect
    
    %% Cierre de lote y salto automático inmediato
    MoreTasks -- "NO" --> VerifyBatch["Verificación Global:<br/>python verify_ui_syntax.py<br/>python run_tests.py"]
    VerifyBatch --> LogCheckpoint["Registrar Checkpoint de Hito<br/>(Log breve del progreso)"]
    LogCheckpoint -- "SALTO AUTOMÁTICO INMEDIATO (SIN PAUSAR)" --> Start
```

---

## 3. Protocolo de Ejecución Perpetua (Fase a Fase)

### Fase 1: Evaluación del Backlog
1. Ejecuta `python .taskmaster/tm.py next` y `python .taskmaster/tm.py list`.
2. Inspecciona `openspec/changes/` buscando listas de tareas incompletas (`- [ ]`).
3. **Decisión:**
   - Si hay una tarea en curso o pendiente: procede inmediatamente a la **Fase 3: Bucle de Orquestación**.
   - Si `tm.py next` indica que no hay tareas pendientes y todos los OpenSpec están concluidos: pasa inmediatamente a la **Fase 2: Motor de Descubrimiento Proactivo**.

---

### Fase 2: Motor de Descubrimiento Proactivo (Inventario Inagotable de I+D)
Cuando todo lo planificado está hecho, el motor explora autónomamente la siguiente frontera siguiendo esta **Matriz de Rotación de I+D**:

| Turno de Innovación | Área de Enfoque | Ejemplos Concretos para woptimizer |
| :--- | :--- | :--- |
| **1. Resiliencia & Robustez** | Excepciones defensivas y edge cases | - Captura atómica de `psutil.AccessDenied` / `NoSuchProcess`.<br/>- Recuperación automática de `profiles.json` corrupto usando `.bak`.<br/>- Cierre limpio de hilos secundarios (`pystray` / System Tray). |
| **2. Gaming & Telemetría UX** | Valor añadido para jugadores | - Contador visual en la Portada de **RAM y CPU liberadas** en tiempo real tras aplicar un Pack.<br/>- Auto-restauración inteligente: monitor en background que reabre apps cerradas al terminar el juego.<br/>- Notificaciones nativas de Windows (Toast notifications no invasivas).<br/>- Hotkeys globales de Windows (ej. `Ctrl+Alt+G`) para Gaming Mode instantáneo. |
| **3. Base de Datos & Procesos** | Cobertura de apps de Windows | - Analizar procesos en ejecución en el sistema y cruzar con `assets/process_db.json`.<br/>- Clasificar nuevos navegadores, launchers (EA, Ubisoft, Riot Vanguard) y bloatware. |
| **4. Rendimiento & Latencia** | Optimización de recursos | - Cacheo inteligente de procesos en `process_service.py` para que listar procesos sea instantáneo.<br/>- Reducción del footprint de memoria de CustomTkinter. |
| **5. Testing & Deuda Técnica** | Automatización de calidad | - Crear suite formal de tests unitarios headless (`tests/test_services.py`).<br/>- Añadir validación estática de tipos con Pydantic en todas las operaciones. |

#### Formalización Inmediata:
1. Crear la propuesta en `openspec/changes/<YYYY-MM-DD>-<slug>/`:
   - `proposal.md`: Explicación técnica del valor de la mejora.
   - `tasks.md`: Lista estructurada con casillas `- [ ]`.
2. Registrar las nuevas tareas correlativas (`TASK-013`, `TASK-014`, etc.) en `.taskmaster/tasks.json`.
3. Commit del descubrimiento: `git commit -m "chore(rd): nueva propuesta I+D <slug>"` (si el sistema de archivos emite lock, continuar sin detenerse).
4. Proceder **sin interrupción** a la Fase 3.

---

### Fase 3: Bucle Dual de Subagentes (`architect-review` -> `openspec-dev`)
El orquestador coordina la ejecución mediante subagentes para preservar el contexto limpio y estructurado:

#### Paso 1: Subagente `architect-review`
Invoca un subagente usando `invoke_subagent` (`TypeName="self"`, `Role="Architect Reviewer"`):
- **Instrucción:** Auditar la tarea activa (`tm.py next`), verificar el estricto cumplimiento de las invariantes de `AGENTS.md` (separación UI/services, kill recursivo, protección del pack gaming), ajustar `.taskmaster/tasks.json` si hay inconsistencias y comitear `chore(architect): ...`.
- El orquestador recibe el dictamen arquitectónico.

#### Paso 2: Subagente `openspec-dev`
Invoca un subagente usando `invoke_subagent` (`TypeName="self"`, `Role="OpenSpec Developer"`):
- **Instrucción:** Tomar la tarea con `python .taskmaster/tm.py next`, crear el plan de implementación, escribir el código en `src/woptimizer/`, ejecutar `python verify_ui_syntax.py` y pruebas headless, marcar `python .taskmaster/tm.py done <TASK_ID>` y comitear `feat/fix: ...`.
- El orquestador recibe el informe de implementación y tests.

#### Paso 3: Verificación de Progreso y Siguiente Tarea
El orquestador consulta `python .taskmaster/tm.py next`:
- **¿Quedan tareas en el lote actual?**
  - **SÍ:** Se ejecuta la siguiente iteración inmediatamente (llamando a `openspec-dev` o a `architect-review` según la complejidad requerida).
  - **NO:** El lote ha concluido. Pasa al Cierre de Hito.

---

### Fase 4: Cierre de Hito y Salto Perpetuo Inmediato
1. **Verificación Global:**
   ```bash
   python verify_ui_syntax.py
   python run_tests.py
   ```
2. **Actualizar OpenSpec:** Marcar todas las tareas en `tasks.md` como `[x]`.
3. **Emitir Checkpoint:** Publica un breve mensaje informativo indicando el hito completado, los commits generados y las pruebas superadas.
4. **REINICIO INMEDIATO (NO STOP):**
   - **NO preguntes al usuario si desea continuar.**
   - **NO declares fin de la ejecución.**
   - Vuelve inmediatamente a la **Fase 1** y comienza la siguiente iteración de I+D.

---

## 4. Invariantes del Repositorio (Estrictamente Prohibido Romper)
1. **Separación de Capas:** La UI jamás toca `psutil` ni ficheros directamente. Todo viaja por `src/woptimizer/services/`.
2. **Kill Recursivo:** Siempre eliminar los hijos (`parent.children(recursive=True)`) antes del padre.
3. **Pack Gaming Protegido:** El pack con `is_gaming=True` es sagrado e inmutable ante borrados.
4. **Sandbox / EPERM en Windows:** Ejecutar scripts de soporte usando Python vía `run_command`.
5. **Tolerancia a Git Lock:** Errores como `unable to create temporary file: Invalid argument` no detienen el bucle.

---

## 5. Plantillas de Invocación para Subagentes

### Invocación a `architect-review`:
```text
Actúa bajo la skill 'architect-review' (.agents/skills/architect/SKILL.md).
1. Consulta la tarea activa con: python .taskmaster/tm.py next y revisa el OpenSpec en openspec/changes/.
2. Audita que se respeten estrictamente las invariantes de AGENTS.md (separación de capas, kill recursivo, sandbox EPERM).
3. Ajusta dependencias o campos en .taskmaster/tasks.json si es necesario.
4. NUNCA escribas código de producción en src/.
5. Haz commit: git commit -m "chore(architect): validar diseño y dependencias de la tarea".
6. Devuelve un informe conciso con el visto bueno para proceder a la implementación.
```

### Invocación a `openspec-dev`:
```text
Actúa bajo la skill 'openspec-dev' (.agents/skills/openspec-dev/SKILL.md).
1. Consulta la tarea activa con: python .taskmaster/tm.py next.
2. Consulta llms.txt y el OpenSpec activo en openspec/changes/.
3. Redacta el plan de implementación respetando las invariantes de AGENTS.md.
4. Modifica el código en src/woptimizer/.
5. Valida obligatoriamente con: python verify_ui_syntax.py y pruebas headless.
6. Marca completada: python .taskmaster/tm.py done <TASK_ID>.
7. Haz commit: git commit -m "feat/fix: <descripción concisa>".
8. Devuelve reporte con cambios realizados y confirmación de tests pasados.
```

---

## 6. Autonomía Absoluta y Criterios de Parada
- **Autonomía 100%:** Todas las decisiones de descubrimiento, diseño, arquitectura, programación, pruebas y commits se toman y ejecutan en piloto automático.
- **Interrupción:** ÚNICAMENTE te detendrás si recibes una orden directa del usuario solicitando explícitamente pausar el bucle.
