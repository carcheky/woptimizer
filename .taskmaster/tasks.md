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
| **TASK-007** | Categorización Automática de Procesos y Filtro de Seguridad | 6/10 | High | PENDING | TASK-002, TASK-004 | docs/ai/architecture.md |
| **TASK-005** | Pruebas de Integración y Validación de la Suite UI | 3/10 | Medium | `PENDING` | TASK-004 | `docs/ai/testing-guide.md` |
| **TASK-006** | Compilación y Empaquetado de woptimizer.exe v3.0.0 | 4/10 | High | `PENDING` | TASK-005 | `docs/ai/sandbox-rules.md` |
| **TASK-008** | Migración de DB a JSON y Endpoint de GitLab | 3/10 | High | `PENDING` | - | `openspec/changes/2026-09-29-v3-ux-polish/tasks.md` |
| **TASK-009** | Evolución Dinámica del Pack Gaming | 6/10 | Critical | `PENDING` | TASK-008 | `openspec/changes/2026-09-29-v3-ux-polish/tasks.md` |
| **TASK-010** | Feedback Visual en el Gestor de Procesos | 4/10 | Medium | `PENDING` | TASK-008 | `openspec/changes/2026-09-29-v3-ux-polish/tasks.md` |

---

## 🧭 Flujo de Trabajo para IAs
1. Consultar la siguiente tarea pendiente ejecutando `python .taskmaster/tm.py next` o leyendo este archivo.
2. Cargar **únicamente** la documentación indicada en la columna `Documentación Asociada` para no gastar tokens.
3. Completar la tarea respetando las invariantes.
4. Marcar la tarea como completada usando `python .taskmaster/tm.py done <ID>`.

---

## 🆕 Tareas del Motor de I+D (Ciclos 4+)

> Estas tareas son las que el motor autónomo `id-pipeline` va cerrando en bucle infinito.
> Cada entrada se corresponde con una fila en `.taskmaster/tasks.json` y un commit dedicado.

| ID | Tarea | Complejidad | Prioridad | Estado | Spec |
|---|---|:---:|:---:|:---:|---|
| **TASK-015** | Actualización Base de Datos de Procesos Gaming | 3/10 | Medium | ✅ DONE | `process-db-update` |
| **TASK-016** | Ampliación Tests Headless + Tipado Pydantic | 4/10 | Medium | ✅ DONE | `testing-quality` |
| **TASK-017** | Robustez System Tray + Logging start_pack_apps | 3/10 | High | ✅ DONE | `resilience-tray-logging` |
| **TASK-018** | Cache TTL + Hashmap O(1) en ProcessService | 6/10 | High | ✅ DONE | `perf-cache-hashmap` |
| **TASK-019** | Notificaciones Nativas Windows (Toast Balloon) | 4/10 | Medium | ✅ DONE | ✅ `2026-09-29-native-toast-notifications` |
| **TASK-020** | Ampliar DB + fix emojis de categoría vs config.py | 3/10 | Medium | ✅ DONE | `assets/process_db.json` + `config.py` |
| **TASK-021** | Cobertura de invariantes: GamingService, PackService, Cache TTL, Kill Recursivo | 5/10 | High | ✅ DONE | `docs/ai/testing-guide.md` |
