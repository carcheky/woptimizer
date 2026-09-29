# Propuesta: Actualización Base de Datos de Procesos Gaming (TASK-015)

## Área
Base de Datos & Procesos — Ciclo #4 de I+D

## Objetivo
Escanear los procesos activos en el sistema, cruzar con ssets/process_db.json e identificar 3-4 procesos nuevos que no estén catalogados. Asignar categoría y semáforo gaming.

## Criterios de Aceptación
- Al menos 3 procesos nuevos añadidos a process_db.json
- Cada entrada tiene: 
ame, category, gaming_safe (🟢/🟡/🔴), description
- Commit realizado con git_safe_commit.py
"@
Set-Content "openspec/changes/2026-09-29-process-db-update/tasks.md" -Encoding UTF8 @"
# Tareas OpenSpec: Actualización Process DB (TASK-015)

- [ ] **1. Escanear procesos activos con psutil**
  - [ ] Listar todos los procesos corriendo en el sistema.
  - [ ] Filtrar los que no están en ssets/process_db.json.

- [ ] **2. Investigar y clasificar 3-4 procesos nuevos**
  - [ ] Asignar categoría (Gaming, Launcher, Bloatware, System, etc.).
  - [ ] Asignar semáforo: 🟢 seguro cerrar, 🟡 precaución, 🔴 no cerrar.

- [ ] **3. Inyectar en process_db.json y hacer commit**
  - [ ] Ejecutar git_safe_commit.py "chore(process-db): actualizar procesos gaming y bloatware".
