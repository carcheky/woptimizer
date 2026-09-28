# 🎯 Taskmaster Board — woptimizer v3

> Sistema de orquestación de tareas atómicas para agentes IA y desarrolladores.
> Archivo de sincronización estructurado: `.taskmaster/tasks.json`
> CLI de consulta rápida: `python .taskmaster/tm.py [list|next|done <id>]`

---

## 📌 Tareas Activas

| ID | Tarea | Complejidad (1-10) | Prioridad | Estado | Dependencias | Documentación Asociada |
|---|---|:---:|:---:|:---:|---|---|
| **TASK-001** | Rediseño de Modelos y Datos para Packs Unificados | 4/10 | High | `PENDING` | - | `docs/ai/data-models.md` |
| **TASK-002** | Implementar Ventana de Gestor de Procesos | 5/10 | High | `PENDING` | TASK-001 | `docs/ai/ui-design-system.md` |
| **TASK-003** | Implementar Ventana de Gestor de Packs (CRUD + Acciones) | 7/10 | Critical | `PENDING` | TASK-001 | `docs/ai/ui-design-system.md` |
| **TASK-004** | Implementar Ventana Principal (Portada con Favoritos) | 4/10 | Critical | `PENDING` | TASK-002, TASK-003 | `docs/ai/ui-design-system.md` |
| **TASK-005** | Pruebas de Integración y Validación de la Suite UI | 3/10 | Medium | `PENDING` | TASK-004 | `docs/ai/testing-guide.md` |
| **TASK-006** | Compilación y Empaquetado de woptimizer.exe v3.0.0 | 4/10 | High | `PENDING` | TASK-005 | `docs/ai/sandbox-rules.md` |

---

## 🧭 Flujo de Trabajo para IAs
1. Consultar la siguiente tarea pendiente ejecutando `python .taskmaster/tm.py next` o leyendo este archivo.
2. Cargar **únicamente** la documentación indicada en la columna `Documentación Asociada` para no gastar tokens.
3. Completar la tarea respetando las invariantes.
4. Marcar la tarea como completada usando `python .taskmaster/tm.py done <ID>`.
