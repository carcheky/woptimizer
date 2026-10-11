# Cuadro de Mando: Motor Autónomo de I+D (woptimizer)

> Dashboard del pipeline de I+D. Actualizado el 2026-10-11.

---

## 🟢 Salud General

| Indicador | Estado | Detalle |
|---|---|---|
| Sintaxis UI | 🟢 | `verify_ui_syntax.py` — 9 módulos |
| Tests headless | 🟢 | `run_tests.py`, **198 tests** (142 backend + 56 headless UI) |
| Benchmark base | 🟢 | 182 ms init · 4.97 ms escaneo · 0.003 ms cache · 30 MB RSS |
| Process DB | 🟢 | 96 entradas · 8 categorías · 0 huérfanas · 🛡️ 34 protegidas |
| Versionado | 🟢 | Rama `beta` · último commit `dbeed31` · `main` publicada `v1.1.0` |
| Build (PyInstaller) | 🟡 | Artefacto de distribución; se regenera al publicar vía CI |

---

## 🔄 Estado de la Ejecución

- **Ciclos completados:** 60 (`rd_journal.json`)
- **Rama de trabajo:** `beta` (nunca commitear a `main` directamente)
- **Último ciclo (#60):** TASK-072 — Hang stdin en `_git_de_fixture` y pre-vuelos tautológicos
- **Tarea activa (`active_task_id`):** `TASK-071` (`pending`, `high`)

---

## 📋 Tareas Pendientes (backlog)

| ID | Estado | Prioridad | Título | Notas clave |
|---|---|---|---|---|
| **TASK-071** | `pending` | **high** | Pack de apps protegidas | Spec en `openspec/changes/2026-10-07-task-071-protected-apps/`. Reutiliza `keepers` |
| **TASK-068** | `in_progress` | high | Arranque por categorías revierte TASK-063 | Código hecho, 189→198 tests. **2 decisiones del dueño bloquean cierre (P-1, P-2b)** |
| **TASK-073** | `pending` | high | RuntimeError en `ProcessManagerView._load` tras destrucción | Race condition ventana destruida |
| **TASK-074** | `pending` | medium | Blindar paridad git tooling (código 2 asimétrico) | |
| **TASK-075** | `pending` | medium | Desacoplar `validate_docs.py` de `%LOCALAPPDATA%` para CI | |
| **TASK-076** | `pending` | medium | Desduplicar flags PyInstaller (`force_build.py` vs `release.yml`) | |
| **TASK-077** | `pending` | low | Normalizar CRLF en `.bat`/`.ps1` (`git add --renormalize`) | |

> **Prioridad de ejecución:** `TASK-071` (activa, feature pedida) → `TASK-073` → resto por prioridad.
> **TASK-068** está bloqueada por decisiones del dueño (P-1 y P-2b, ver más abajo).

---

## 🗂️ Rotación de Áreas

| # | Área | Último ciclo |
|---|---|---|
| 1 | Resiliencia & Robustez | #37 |
| 2 | Gaming & Telemetría UX | #42 |
| 3 | Base de Datos & Procesos | #40 |
| 4 | Rendimiento & Latencia | #35 |
| 5 | Testing & Calidad | #43 |
| 6 | Documentación & Arquitectura | #47 |

---

## ⚠️ Deuda Técnica Conocida

### 🔴 Crítica

- **Shell intermitente (`spawn EPERM`):** El entorno de agentes bloquea subprocesos vía Node. Afecta a `tm.py` y a veces a `.taskmaster/git_safe_commit.py`. Workaround: reintentar. No tiene fix posible desde el repo. Blindado con el contrato de códigos de salida de `.taskmaster/git_safe_commit.py` (`docs/ai/sandbox-rules.md`).
- **`.git` corrupto (VFS Nextcloud):** El historial vive en `%LOCALAPPDATA%\woptimizer_git\.git`. Se acepta y se blinda con `.taskmaster/git_safe_commit.py --verify` (`docs/ai/sandbox-rules.md`).

### 🟡 Media

- **`build.bat` en LF (`TASK-077`, `pending`):** Tiene 39 LF y 0 CRLF pese a `.gitattributes eol=crlf`. Fix: `git add --renormalize .`. Verificable con `git ls-files --eol -- build.bat`.
- **11 ficheros `test_*.py` heredados:** **🔴 CERRADA en CYCLE-045 (TASK-055).** Archivados en `docs/archive/legacy-root-tests/`. Guard en `run_tests.py` impide que vuelvan a la raíz.
- **`validate_docs.py` no corre en CI (`TASK-075`, `pending`):** Depende de `%LOCALAPPDATA%`. Detallado en `docs/ai/sandbox-rules.md`.

---

## ❓ Decisiones pendientes del dueño (TASK-068, bloqueante)

- **P-1:** Con una categoría 🟡 marcada para arrancar, ¿se aceptan N launchers o 🟡 pasa a ser inerte al arrancar (simétrico con 🔴)?
- **P-2b:** ¿El mensaje debe decir POR QUÉ se omite cada categoría, o basta con ver QUÉ se omite?



## 🛡️ Features Planificadas

- **Pack de aplicaciones protegidas** (`TASK-071`, `pending`, alta):
  Apps dentro de este pack **no se matan nunca** por la ejecución de otro pack y **no aparecen** en el listado de procesos ni en otros packs.
  Spec: `openspec/changes/2026-10-07-task-071-protected-apps/`.
  Reutiliza `models.py:40 keepers` y el filtro existente en el motor de apagado.

---

## 📌 Recordatorios para el Agente

1. **Leer AGENTS.md** para invariantes (separación capas, kill recursivo, pack gaming protegido).
2. **Nunca commitear a `main`** — trabajar en `beta`, luego ff-merge.
3. **Commit solo vía** `python .taskmaster/git_safe_commit.py "mensaje (TASK-NNN)"`.
4. **Tests:** `python run_tests.py` (198 tests) · `python verify_ui_syntax.py` · `python validate_docs.py`.
5. **Docs vivas:** actualizar `docs/ai/` tras cada cambio arquitectónico.
6. **Carga selectiva:** no leer toda la doc — consultar `llms.txt` como mapa y cargar solo el fichero de `docs/ai/` que necesites.
7. **Pipeline de 4 pasos:** Buscar → Planear → Ejecutar → Auditar tests (mutation-auditor).

---

## 📋 Últimos Hitos (resumen compacto)

| Ciclo | Área | Qué se hizo |
|---|---|---|
| #60 | Tooling | Hang stdin git fixture solucionado (TASK-072) |
| #59 | Tooling | `validate_docs.py` una vez por fichero (TASK-070) |
| #52 | Tooling | Puerta de ancla obligatoria en commits (TASK-059) |
| #49 | Docs | Check 8 de deuda con anclas resolubles (TASK-060) |
| #47 | Arquitectura | Ancla de trazabilidad de ciclos (TASK-057) |
| #43 | Testing | Sincronización tests favoritos acumulativos (TASK-053) |
| #42 | UX | Placeholder único en desplegable (TASK-052) |
| #41 | UX | Botón actualización DB con feedback (TASK-051) |
| #40 | DB | Sincronización remota + fallback observable (TASK-050) |
| #39 | UX | Grid de favoritos adaptativo (TASK-049) |
| #38 | Core | Favoritos acumulativos en PackService (TASK-048) |
| #37 | Robustez | Concurrencia en GamingService con RLock (TASK-047) |
| #36 | Testing | Contratos ciclo vida Confirmable (TASK-046) |
| #35 | Rendimiento | Memoización categorización O(1) (TASK-045) |

> Historial completo de los 60 ciclos en `.taskmaster/rd_journal.json` y `.taskmaster/CHANGELOG.md`.
