# AGENTS.md — woptimizer

> **Spec única para agentes IA. Léeme siempre al empezar y al terminar.**
> **Spec rev:** 7 — 2026-09-14
> Sincronizar con `__version__` en `process_manager.py:15` (ambos avanzan juntos, +1 patch cuando se actualice este spec).

---

## 🤖 Agent Role

Eres el asistente que mantiene **woptimizer**, un Process Manager con foco gamer para Windows. Tu priorización es estricta:

1. **Spec-First (regla #1)** — Nunca tocar código sin actualizar este spec primero. El spec describe **QUÉ**; el código describe **CÓMO**.
2. **Validate-Yourself** — Si tienes shell, corre tests tú. "Compila, debería funcionar" es la #1 causa de bugs reportados.
3. **Una feature a la vez** — Cambio mínimo, validado, commit. Siguiente. Si un test falla, revierte.

---

## 📦 Project Overview

- **Stack:** Python 3.x + tkinter (GUI), PowerShell embebido para listar procesos, Windows-only.
- **Entry points:** `ProcessManager.vbs` (doble clic silencioso), `python process_manager.pyw` (sin consola).
- **Persistencia dual:** `saved_processes.json` (legacy v1.1) + `profiles.json` (v2.0+).
- **Versión actual:** `2.0.5` (`process_manager.py:15`).
- **Estado:** ✅ funcional · ✅ perfiles v2.0 · ✅ Trampa #15 gaming keepers · ✅ Bug #2 doble-tap per-button · ✅ `_run_kill()` con verificación post-kill · ❌ Mini App bloqueada por EACCES sandbox (ver `docs/mini-app-status.md`).

---

## ⚡ Commands (copy-paste)

```powershell
# 1. Sintaxis
python -c "import py_compile; py_compile.compile('process_manager.py', doraise=True)"

# 2. Validar GUI abre (sin huérfanos pwsh)
python verify_app.py

# 3. Validar pythonw.exe OK
python verify_pyw.py

# 4. Validar kill real funciona
python test_kill_real.py

# Sincronizar .pyw tras validación (si no tienes EPERM)
Copy-Item process_manager.py process_manager.pyw -Force

# Si tienes EPERM, pedir al usuario:  python sync_pyw.py
```

Tests adicionales según el área tocada: ver [`docs/testing.md`](docs/testing.md).
Tests de regresión por trampa: ver [`docs/known-issues.md`](docs/known-issues.md).

---

## 🚦 Three-Tier Boundaries

### ✅ Always

- **Actualizar AGENTS.md ANTES de tocar código** en cualquier feature nueva (Spec-First).
- Correr los tests pertinentes **antes** de declarar "listo".
- Mantener `__version__` y la spec rev sincronizados (+1 patch cuando bumpees uno, bumpea el otro).
- `CREATE_NO_WINDOW = 0x08000000` en **todos** los `subprocess.run`/`Popen`.
- Usar `taskkill /F /T /PID <pid>` (no `proc.kill()` solo) en cleanup de procesos con hijos.
- Forzar UTF-8 en scripts PowerShell: `$OutputEncoding = [System.Text.Encoding]::UTF8`.
- Doble tap en el mismo botón para acciones destructivas (no `messagebox.askyesno`) — Trampa #14.
- Status label inline para feedback (no `messagebox.showinfo`) — Trampa #14.
- TAB como delimitador Python↔PowerShell (no `-replace "[X]"`).
- Buscar TODOS los call sites antes de cambiar firma de retorno (`grep -rn "func_name("`).

### ⚠️ Ask First

- Cambiar la firma de retorno de `kill_processes` o `relaunch_processes` (Trampa #11 — afecta 4 call sites internos + 2 tests).
- Modificar el script PowerShell embebido en `get_running_processes` (línea 139).
- Añadir nueva categoría gaming (`PROCESS_CATEGORIES` línea 31).
- Eliminar features del código (primero borrarlas del spec).
- Reintentar Mini App publish — bug del sandbox del Host, 6 estrategias ya probadas (ver `docs/mini-app-status.md`).

### 🚫 Never

- `$pid` en PowerShell — variable reservada (Trampa #1).
- `sys.exit(0)` silencioso en auto-elevation (Trampa #2).
- Auto-elevar `pythonw.exe` con `runas` — no funciona (Trampa #4).
- `proc.kill()` en cleanup de tests/CI — deja `pwsh.exe` huérfanos (Trampa #10).
- `messagebox.askyesno`/`showinfo`/`showwarning` en la UI principal (Trampa #14).
- Tests con `notepad.exe` — ventana molesta + race (Trampa #12).
- `-replace "[X]"` en cmdlines — texto raro (Trampa #3).
- Asumir que funciona sin probar (Validate-Yourself).
- Tocar código sin actualizar el spec (Spec-First).
- Múltiples cambios a la vez.
- Auto-elevación de la app sin acción del usuario.

---

## 🗺️ Architecture (referencia rápida)

`process_manager.py` (~1825 líneas) — mapa de líneas:

| Líneas | Contenido |
|---|---|
| 1-17 | Header, `__version__`, paths |
| 18-30 | Constantes (`PS_DELIM`, `MAX_CMDLINE_LEN`) |
| 31-104 | `PROCESS_CATEGORIES` (9 categorías) |
| 105-115 | `CATEGORY_ORDER` |
| 118-127 | `categorize_process()` |
| 130-137 | `is_admin()` |
| 139-210 | `get_running_processes()` ← Trampa #1 |
| 213-233 | `expand_selection_by_name()` ← Trampa #13 |
| 236-313 | `kill_processes()` ← Trampa #11 |
| 316-453 | save/load + `relaunch_processes()` |
| 485-591 | CRUD perfiles (v2.0) |
| 593-1351 | `class ProcessManagerApp` (UI) |
| 1353-1687 | `class ProfilesDialog` |

Profundidad en `docs/architecture.md` · API en `docs/api.md` · extensiones en `docs/extending.md`.

---

## 🌿 Control de versiones (git local)

Repo git local para no perder cambios. **Doble clic** en los scripts (no requiere git CLI en PATH si está instalado Git for Windows).

| Script | Qué hace |
|---|---|
| `init_git.bat` | Inicializa el repo, configura usuario, hace commit inicial v2.0.5 con tag. |
| `commit_version.bat` | Tras cambios: lee `__version__` del código, hace commit con version + mensaje. |
| `test_kill_firefox.bat` | Diagnóstico directo: `taskkill /F /IM firefox.exe /T` con verificación post-kill. |

**Estado actual:** repo no inicializado todavía. **Acción inmediata:** doble clic en `init_git.bat`.

`.gitignore` excluye: `profiles.json`, `saved_processes.json` (datos del usuario), `__pycache__/`, `*.pyc`, `.vscode/`, `.idea/`, `*.log`.

---

## 🐛 Bugs activos a corregir

### Bug #1: La app debería lanzarse siempre como admin
`ProcessManager.vbs` no eleva correctamente. Investigar `ShellExecute ... , , , "runas"` o `Start-Process -Verb RunAs` desde `.ps1`. Cuando se arregle, añadir badge 🛡️ en la barra de título usando `is_admin()` (línea 130-137).

### Bug #2: Mensaje de confirmación sale en todos los botones ✅ **RESUELTO v2.0.4**
El doble tap ("⚠️ PULSA OTRA VEZ") aparecía en TODOS los botones de acción, no solo en el pulsado. Fix aplicado: `_pending_action` ahora guarda `(button, normal_label)`; `_request_confirm` cambia SOLO ese botón; `_reset_pending_action` restaura SOLO ese botón.

---

## 📚 Documentación relacionada

| Doc | Cuándo leerlo |
|---|---|
| [`docs/known-issues.md`](docs/known-issues.md) | **Catálogo completo de las 15 trampas** con síntomas, causas, fix y tests de regresión. **Leer antes** de tocar scripts PowerShell, subprocess, kill, o si algo "no funciona". |
| [`docs/testing.md`](docs/testing.md) | Catálogo de tests, patrones de debug, test_harness E2E. |
| [`docs/api.md`](docs/api.md) | API reference con firmas exactas (qué retorna cada función pública). |
| [`docs/architecture.md`](docs/architecture.md) | Flujo de datos, componentes, decisiones arquitectónicas. |
| [`docs/extending.md`](docs/extending.md) | Cómo añadir features (categoría, botón, atajo, etc.) sin romper nada. |
| [`docs/mini-app-status.md`](docs/mini-app-status.md) | Estado de la Mini App (bloqueada por EACCES del sandbox del Host). |

---

## Changelog del spec

- **rev 8 (2026-09-14)** — Workflow git local: `init_git.bat`, `commit_version.bat`, `.gitignore`. Bug #2 marcado ✅ RESUELTO v2.0.4. Versión actualizada a v2.0.5 (incluye Trampa #15 gaming keepers + `_run_kill()` con verificación post-kill). Spec rev 8.
- **rev 7 (2026-09-14)** — Reestructuración completa siguiendo best practice AGENTS.md (comandos primero, three-tier boundaries, target <200 líneas). Eliminado el catálogo inline de 15 trampas (ahora solo se referencia `docs/known-issues.md`). Spec-First movido a `Always` boundaries. Spec rev 7.
- **rev 6 (2026-09-14)** — Bugs a corregir (#1 admin elevation + indicador 🛡️, #2 confirmación solo en botón pulsado). Trampa #15 (`should_kill_for_gaming`).
- **rev 5 (2026-09-14)** — Trampa #14: doble tap para confirmación, status label inline para feedback.
- **rev 4 (2026-09-14)** — Refactor completo: Spec-First rule, Validate-Yourself, 13 trampas, tabla de tests por área, API pública, mapa de líneas.
- **rev 3** — v2.0 con perfiles y agrupación.
- **rev 2** — Trampas #1-4, modo Simple.
- **rev 1** — Spec inicial (kill_processes / save / relaunch básico).
