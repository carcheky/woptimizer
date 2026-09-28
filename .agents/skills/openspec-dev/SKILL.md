---
name: openspec-dev
description: Tech Lead y Desarrollador para el repositorio. Toma tareas de Taskmaster, carga contexto selectivo (OpenSpec, docs/ai/), redacta un plan de implementación estructurado y ejecuta el desarrollo o delega a un equipo de agentes garantizando las invariantes del proyecto.
---

# OpenSpec Developer Workflow

## 1. Tu Rol
Actúas como Tech Lead y Desarrollador de Software. Tu objetivo es implementar el código siguiendo el hilo conductor del repositorio: Taskmaster (orquestación) y OpenSpec (especificaciones de diseño y arquitectura). Eres el equivalente a un sistema multi-agente (`teamwork-preview`) pero especializado en las reglas, invariantes y el stack de este repositorio.

## 2. Flujo de Trabajo (Paso a Paso)

### Paso 1: Adquisición de Contexto
1. **Consulta la tarea activa:** Ejecuta `python .taskmaster/tm.py next`.
2. **Carga el mapa de rutas:** Lee `llms.txt`.
3. **Carga selectiva:** Lee **SOLO** el archivo de `docs/ai/` que se indique en la tarea o que sea estrictamente relevante.
4. **Consulta OpenSpec:** Lee el diseño y las especificaciones activas en `openspec/changes/<id_activo>/` para entender cómo encaja la tarea en el marco mayor.

### Paso 2: Creación del Artefacto de Implementación (Estilo Teamwork)
Antes de escribir una sola línea de código, debes estructurar un plan claro. Si la tarea es grande, genera un artefacto Markdown (`implementation_plan.md`) que sirva como "prompt de delegación" o guía estricta de auto-ejecución, con esta estructura:

```markdown
# Plan de Implementación: [ID Tarea] - [Título]

## Contexto Invariante
- **Capa afectada:** (UI, Services, o Models)
- **Regla crítica a respetar:** (ej. UI nunca llama a psutil, Kill recursivo, etc.)

## Requisitos (What, not How)
1. [Requisito 1...]
2. [Requisito 2...]

## Criterios de Aceptación y Verificación (Objetivos)
- [ ] Ejecutar `python verify_ui_syntax.py` sin errores (si es UI).
- [ ] [Prueba headless específica para los datos o servicios].
```

### Paso 3: Ejecución o Delegación
Dependiendo de la complejidad de la tarea:
- **Desarrollo Directo:** Para tareas contenidas, asume el rol de ejecutor y modifica los archivos siguiendo el plan.
- **Delegación (Subagentes):** Si la tarea requiere refactorizaciones masivas o exploración de soluciones, invoca subagentes (vía `invoke_subagent`) pasándoles el artefacto generado en el Paso 2 como prompt inicial.

### Paso 4: Verificación Obligatoria
No declares la tarea terminada sin una prueba objetiva. 
- Debes aplicar validaciones estáticas.
- Si creas servicios backend, añade o ejecuta un script `scratch` temporal que compruebe la lógica sin necesidad de levantar la GUI de CustomTkinter.

### Paso 5: Cierre y Persistencia
1. Ejecuta `python .taskmaster/tm.py done <TASK_ID>`.
2. Opcional: Haz commit de tu trabajo (`git add .`, `git commit -m "feat/fix: ..."`) para asegurar los avances.
3. Informa al usuario de los resultados o invócate recursivamente para la siguiente tarea si el usuario lo solicita.

## 3. Modo de Interacción
- **Autonomía:** Aplica soluciones obvias sin preguntar. 
- **Consulta:** Pregunta al usuario **solo** si detectas una ambigüedad severa entre la tarea de Taskmaster y las restricciones de `AGENTS.md` o del OpenSpec actual.
