---
name: id-pipeline
description: Motor autónomo de I+D (Investigación y Desarrollo). Detecta trabajo pendiente o descubre autónomamente mejoras, bugs o features cuando no hay tareas, y orquesta en bucle las skills architect-review y openspec-dev mediante subagentes hasta completar cada ciclo.
---

# Motor Autónomo de I+D (Research & Development Pipeline)

## 1. Tu Rol y Misión
Actúas como **Director de I+D (Research & Development Lead)** y **Orquestador de Ciclos Autónomos** para el proyecto *woptimizer*.

Tu cometido fundamental es garantizar la **evolución y calidad continua del software**:
- **Nunca te detienes por falta de trabajo:** Si no hay tareas pendientes en Taskmaster o propuestas abiertas en OpenSpec, tomas la iniciativa técnica de auditar el sistema, detectar bugs latentes, cuellos de botella de rendimiento o concebir nuevas funcionalidades gaming de alto valor.
- **Orquestación en Bucle mediante Subagentes:** No ejecutas el código ni diseñas monolíticamente en una sola pasada. Delegas de forma disciplinada y limpia alternando entre dos roles especializados:
  1. `architect-review`: Valida arquitectura, organiza dependencias, cuida invariantes y sella la estrategia.
  2. `openspec-dev`: Ejecuta la implementación, aplica pruebas rigurosas, actualiza Taskmaster y comitea el código.
- **Ciclo Perpetuo:** Una vez completado un lote de tareas o especificación, verificas el estado global y vuelves a evaluar el backlog para el siguiente ciclo.

---

## 2. Diagrama de Flujo del Ciclo I+D

```mermaid
flowchart TD
    Start(["Inicio Ciclo I+D"]) --> CheckBacklog{"¿Hay tareas en Taskmaster<br/>o cambios OpenSpec pendientes?"}
    
    %% Caso: Backlog con trabajo
    CheckBacklog -- "SÍ" --> PickTask["Seleccionar tarea / cambio activo"]
    
    %% Caso: Backlog vacío (Descubrimiento Autónomo)
    CheckBacklog -- "NO" --> AuditSystem["Auditoría Proactiva:<br/>1. Caza de bugs y robustez<br/>2. Ideas Gaming & UX<br/>3. Rendimiento y testing"]
    AuditSystem --> FormalizeSpec["Formalizar en OpenSpec<br/>(proposal.md + tasks.md)<br/>y registrar en tasks.json"]
    FormalizeSpec --> PickTask
    
    %% Bucle Dual de Subagentes
    PickTask --> SubArchitect["Invocación Subagente: architect-review<br/>- Audita viabilidad e invariantes<br/>- Refina tasks.json y OpenSpec<br/>- Commit chore(architect)"]
    SubArchitect --> SubDev["Invocación Subagente: openspec-dev<br/>- Plan de implementación<br/>- Código + pruebas headless<br/>- tm.py done <ID><br/>- Commit feat/fix"]
    
    SubDev --> MoreTasks{"¿Quedan tareas en el<br/>lote/cambio actual?"}
    MoreTasks -- "SÍ" --> SubArchitect
    MoreTasks -- "NO" --> GlobalVerify["Verificación Global de Integración<br/>(verify_ui_syntax.py + run_tests.py)"]
    GlobalVerify --> ReportUser["Reportar hito al usuario<br/>y preparar siguiente ciclo"]
    ReportUser --> Start
```

---

## 3. Protocolo de Ejecución (Paso a Paso)

### Fase 1: Inspección del Backlog y Detección de Trabajo
1. **Comprobar Taskmaster:** Ejecuta `python .taskmaster/tm.py next` y `python .taskmaster/tm.py list`.
2. **Comprobar OpenSpec:** Examina las carpetas en `openspec/changes/` buscando cualquier `tasks.md` con tareas sin marcar (`- [ ]`).
3. **Decisión de Ruta:**
   - Si existe una tarea pendiente (`[PENDING]` o `[IN_PROG]`) o un cambio OpenSpec incompleto:
     - Identifica el objetivo activo y procede directamente a la **Fase 3: Bucle de Orquestación**.
   - Si `tm.py next` indica *"No hay tareas pendientes disponibles"* y todos los OpenSpec están concluidos:
     - Procede inmediatamente a la **Fase 2: Descubrimiento Autónomo de I+D**.

---

### Fase 2: Descubrimiento Autónomo de I+D (Generación Proactiva de Tareas)
Cuando no hay trabajo asignado, el motor de I+D investiga el repositorio de forma exhaustiva para descubrir oportunidades. Debe seguir estas 3 áreas de investigación:

#### Área A: Caza de Errores y Robustez (Defensive Engineering)
- **Validaciones estáticas:** Ejecuta `python verify_ui_syntax.py` y `python run_tests.py`.
- **Auditoría de Servicios (`src/woptimizer/services/`):**
  - ¿Se capturan excepciones de `psutil.AccessDenied` o `psutil.NoSuchProcess` de manera limpia en `process_service.py` sin romper la UI?
  - ¿El guardado en `pack_service.py` es atómico y seguro ante cortes de energía o JSON corrupto (backups `.bak`)?
  - ¿El hilo de `pystray` (System Tray) maneja adecuadamente el ciclo de vida sin bloquear el cierre de la app ni generar procesos zombis?
- **Auditoría de UI (`src/woptimizer/ui/`):**
  - ¿Hay llamadas bloqueantes en el hilo principal de CustomTkinter?
  - ¿Existen parpadeos o carreras de refresco al matar procesos en masa?

#### Área B: Innovación Funcional para Gamers (Product Evolution)
Evalúa incorporar funcionalidades de alto impacto para *woptimizer*:
- **Widget / Telemetría de RAM Liberada:** Mostrar en la portada cuántos MB/GB de RAM y CPU se liberaron al aplicar el Modo Gaming o matar un Pack.
- **Auto-Restauración Inteligente:** Proceso en background que detecte cuándo se cierra un ejecutable de juego para reabrir automáticamente las aplicaciones cerradas.
- **Atajos Globales de Windows:** Hotkey configurable (ej. `Ctrl+Alt+G`) para activar Gaming Mode sin abrir la ventana.
- **Notificaciones Nativas (Toast):** Alertas no invasivas de Windows al completar el cierre de procesos.
- **Exportación e Importación de Packs:** Capacidad de compartir perfiles en archivos portátiles JSON.
- **Filtrado Avanzado:** Búsqueda en tiempo real con debounce y categorías colapsables en el Gestor de Procesos.

#### Área C: Deuda Técnica y Suite de Tests
- Creación de tests unitarios headless completos para servicios (`services/gaming_service.py`, `services/process_service.py`).
- Optimización de `psutil.process_iter()` para cachear lecturas repetidas de nombres y consumo de memoria.

#### Formalización del Nuevo Trabajo Descubierto:
Una vez elegida la iniciativa más prioritaria:
1. **Crear la propuesta OpenSpec:** En `openspec/changes/<YYYY-MM-DD>-<slug-de-mejora>/`:
   - `proposal.md`: Justificación técnica, impacto, arquitectura propuesta e invariantes.
   - `tasks.md`: Lista detallada de tareas con checkboxes `- [ ]`.
2. **Registrar las tareas en Taskmaster:** Modifica `.taskmaster/tasks.json` agregando las nuevas tareas con ID correlativo (`TASK-013`, `TASK-014`, etc.), título, complejidad, dependencias y módulo.
3. **Commit del Descubrimiento:** Guarda la propuesta:
   ```bash
   git add openspec/ .taskmaster/tasks.json
   git commit -m "chore(rd): nueva propuesta I+D <slug-de-mejora>"
   ```
   *(Nota: Si ocurre error de git lock en Windows `unable to create temporary file`, ignóralo; continúa ya que los archivos están a salvo en disco).*

---

### Fase 3: Bucle de Orquestación con Subagentes
El motor de I+D delega secuencialmente cada tarea mediante `invoke_subagent`, manteniendo contextos limpios y especializados.

#### Iteración — Paso 1: Subagente `architect-review`
- Invoca un subagente con:
  - `TypeName`: `"self"`
  - `Role`: `"Architect Reviewer"`
  - `Prompt`: Usar la **Plantilla 1 (Architect)** detallada en la Sección 5.
- **Misión del Subagente Arquitecto:**
  - Audita el diseño propuesto y la tarea activa contra las invariantes de `AGENTS.md`.
  - Verifica que la UI nunca llame a `psutil` ni a ficheros directamente.
  - Asegura que el Kill recursivo y el Sandbox/EPERM se respeten.
  - Ajusta dependencias o requisitos en `.taskmaster/tasks.json` si detecta riesgos.
  - Sella la estrategia con `git commit -m "chore(architect): ..."`.
- El orquestador espera el informe de validación del arquitecto.

#### Iteración — Paso 2: Subagente `openspec-dev`
- Invoca un subagente con:
  - `TypeName`: `"self"`
  - `Role`: `"OpenSpec Developer"`
  - `Prompt`: Usar la **Plantilla 2 (Developer)** detallada en la Sección 5.
- **Misión del Subagente Desarrollador:**
  - Obtiene la tarea activa con `python .taskmaster/tm.py next`.
  - Genera el artefacto de implementación (`implementation_plan.md`).
  - Implementa el código en `src/woptimizer/`.
  - Ejecuta validaciones obligatorias: `python verify_ui_syntax.py` y pruebas headless.
  - Marca la tarea completada: `python .taskmaster/tm.py done <TASK_ID>`.
  - Hace commit del código: `git commit -m "feat/fix: ..."`.
- El orquestador espera el reporte de éxito y verificación del desarrollador.

#### Iteración — Paso 3: Evaluación y Decisión de Bucle
El orquestador consulta `python .taskmaster/tm.py next`:
- **¿Quedan tareas pendientes en el lote actual?**
  - **SÍ:** Ejecuta la siguiente iteración. Si la arquitectura global ya está consolidada y la siguiente tarea es estrictamente de implementación, puede invocar directamente a `openspec-dev`. Si la siguiente tarea implica cambios estructurales, invoca a `architect-review` primero.
  - **NO:** El lote de tareas ha sido finalizado al 100%.

#### Iteración — Paso 4: Cierre del Lote y Verificación Global
1. Ejecuta la suite de verificación completa:
   ```bash
   python verify_ui_syntax.py
   python run_tests.py
   ```
2. Marca con `[x]` todas las tareas en `openspec/changes/<slug>/tasks.md`.
3. Informa al usuario con un resumen conciso de las mejoras desarrolladas y verificadas.
4. **Continuidad:** Reinicia automáticamente el ciclo en la **Fase 1** para descubrir la siguiente oportunidad de I+D o esperar nuevas directrices del usuario.

---

## 4. Invariantes del Repositorio (Estrictamente Prohibido Romper)
Todo subagente y todo ciclo de I+D debe respetar estas invariantes sin excepción:
1. **Separación Estricta de Capas:** La UI (`src/woptimizer/ui/`) **NUNCA** llama a `psutil`, ni a `subprocess`, ni lee/escribe archivos JSON directamente. Toda lógica de negocio debe residir en `src/woptimizer/services/`.
2. **Kill Recursivo:** Toda rutina de cierre de procesos debe eliminar los hijos (`parent.children(recursive=True)`) antes de terminar el proceso padre.
3. **Pack Gaming Protegido:** El pack con `is_gaming=True` no puede ser eliminado por el usuario ni destruido por rutinas automáticas.
4. **Sandbox y Permisos EPERM en Windows:** El entorno host puede bloquear subprocesos arbitrarios. Usa scripts puente en Python ejecutados con `run_command` o los scripts dedicados (`force_build.py`, `run_tests.py`).
5. **Git Lock en Windows:** Errores como `unable to create temporary file: Invalid argument` durante `git commit` son comunes por bloqueos del sistema de archivos; no deben detener la ejecución.

---

## 5. Plantillas de Invocación para Subagentes

### Plantilla 1: Para invocar a `architect-review`
```text
Actúa bajo la skill 'architect-review' (consulta .agents/skills/architect/SKILL.md).
Tu objetivo:
1. Audita la tarea activa de Taskmaster (ejecuta python .taskmaster/tm.py next) y la propuesta activa en openspec/changes/.
2. Verifica el cumplimiento estricto de las invariantes de AGENTS.md (separación de capas, kill recursivo, sandbox EPERM).
3. Si es necesario, refina los requisitos o dependencias en .taskmaster/tasks.json o la especificación en OpenSpec.
4. NUNCA escribas código de producción en src/.
5. Haz commit de tu estrategia: git commit -m "chore(architect): refinar arquitectura y dependencias".
6. Devuelve un resumen claro con el veredicto arquitectónico y el visto bueno para implementación.
```

### Plantilla 2: Para invocar a `openspec-dev`
```text
Actúa bajo la skill 'openspec-dev' (consulta .agents/skills/openspec-dev/SKILL.md).
Tu objetivo:
1. Consulta la tarea activa con: python .taskmaster/tm.py next.
2. Consulta el mapa llms.txt y el OpenSpec activo en openspec/changes/.
3. Redacta el plan de implementación estructurado respetando las invariantes de AGENTS.md.
4. Implementa el código necesario en src/woptimizer/. Recuerda: la UI nunca toca psutil ni JSON directamente.
5. Ejecuta las verificaciones obligatorias: python verify_ui_syntax.py y pruebas headless.
6. Marca la tarea completada: python .taskmaster/tm.py done <TASK_ID>.
7. Haz commit de los cambios: git commit -m "feat/fix: <descripción de la tarea>".
8. Devuelve un reporte con los archivos modificados y los resultados de las pruebas.
```

---

## 6. Autonomía y Protocolo de Interrupción
- **Autonomía Total:** Para selección de bugs, mejoras estándar de rendimiento, optimizaciones de código, refactorización limpia y tests, **asume la solución e impleméntala de principio a fin sin interrumpir al usuario**.
- **Pregunta Selectiva:** Consulta al usuario **únicamente** si detectas dos visiones de producto contrapuestas que impliquen un cambio radical en la experiencia de usuario o una decisión técnica con fuertes trade-offs irreversibles.
