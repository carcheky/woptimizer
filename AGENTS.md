# AGENTS.md — woptimizer

> **Spec única para agentes IA. Léeme siempre al empezar y al terminar.**
> **Spec rev:** 12 — 2026-09-24
> Sincronizar con `__version__` en `process_manager.py:15` (ambos avanzan juntos, +1 cuando se actualice este spec).

---

## 🤖 Agent Role

Eres el asistente que mantiene **woptimizer**, un Process Manager con foco gamer para Windows. Tu priorización es estricta:

1. **Spec-First (regla #1)** — Nunca tocar código sin actualizar este spec primero. El spec describe **QUÉ**; el código describe **CÓMO**.
2. **Validate-Yourself** — Si tienes shell, corre tests tú. "Compila, debería funcionar" es la #1 causa de bugs reportados.
3. **Una feature a la vez** — Cambio mínimo, validado, commit. Siguiente. Si un test falla, revierte.

---

## 📜 Spec-Driven Development (SDD) — flujo OBLIGATORIO

Cada feature nueva, refactor significativo o bug fix no trivial DEBE seguir este flujo. Es la regla #1 ampliada con OpenSpec (https://openspec.dev/, Fission-AI). Adoptamos el **patrón de carpetas OpenSpec** (no el CLI npm) — sin dependencias externas.

### Flujo canónico (9 pasos)

```
[1]  User pide feature / fix
[2]  Clasificar tamaño del cambio → decision matrix (abajo)
[3]  Leer AGENTS.md  +  llms.txt                ← carga selectiva para agente
[4]  Crear openspec/changes/<id>/proposal.md    ← POR QUÉ y QUÉ (broad)
[5]  Crear openspec/changes/<id>/tasks.md       ← CÓMO, pasos numerados
[6]  Si "grande": añadir openspec/changes/<id>/specs/<cap>/spec.md  ← spec delta
[7]  Actualizar AGENTS.md FIRST                 ← Spec-First: spec rev +1
[8]  Implementar siguiendo tasks.md             ← todowrite para tracking
[9]  Validar → Commit → Mover a archive/
```

### Decision matrix — qué artefactos requiere cada cambio

| Tamaño | Ejemplos | Artefactos requeridos |
|---|---|---|
| **Trivial** | typo en comentario, fix de doc roto, whitespace | (ninguno). Commit directo. NO requiere proposal. |
| **Pequeño** | bug fix de 1-3 archivos, <30 LOC, fix de test, doc rewrite puntual | `proposal.md` corto (1 párrafo Why + bullets What) + `tasks.md`. |
| **Mediano** | 1 feature nueva, refactor de 1 módulo, nueva categoría gaming | `proposal.md` completo + `tasks.md` + commit con archivado. |
| **Grande** | cambio de capability (kill, profiles, gaming, executable), nuevo sub-sistema | `proposal.md` + `tasks.md` + `specs/<cap>/spec.md` delta + commit con archivado. |

**Por qué existe esta matriz:** la sostenibilidad viene de no exigir lo mismo a un cambio de 1 línea que a uno de 1 capability. Si tu cambio es pequeño pero dudas → clasifícalo como pequeño (con proposal corto) y listo. Si dudas entre mediano y grande → probablemente es grande, añade spec delta.

### Anti-burocracia — heurísticas

- ❌ Proposal >1 página → probablemente el cambio está mal acotado. **Decompose.**
- ❌ tasks.md con >20 items → idem, el cambio es demasiado grande, partirlo.
- ❌ Spec delta sin proposal previa → la proposal es el contrato; el delta refina.
- ✅ Proposal corta es OK. 1 párrafo Why + 3-5 bullets What Changes es suficiente para cambios pequeños/medianos.
- ✅ "Cerillas" (`<10` LOC bugfixes sin cambiar API): proposal de 1-2 frases en el cuerpo del commit, sin carpeta `changes/`.

### Estructura del repo (OpenSpec)

```
openspec/
├── README.md                # cómo usamos OpenSpec en este proyecto
├── specs/                   # source of truth: requisitos canónicos (formato SHALL)
│   └── <capability>/
│       └── spec.md
└── changes/                 # propuestas activas
    ├── <change-id>/
    │   ├── proposal.md      # Why + What Changes + Impact
    │   ├── tasks.md         # pasos numerados y áreas tocadas
    │   └── specs/<cap>/spec.md   # ← SOLO para cambios grandes (delta)
    └── archive/             # cambios cerrados (NO borrar, historial inmutable)
```

### Capability spec — formato `SHALL`

Cada capacidad define requisitos verificables. Estilo OpenSpec:

```markdown
# Capability: woptimizer

## Purpose
...

## Requirements

### Requirement: <nombre>
The system SHALL <comportamiento observable y verificable>.

#### Scenario: <caso>
- WHEN <condición>
- THEN <resultado esperado>
```

### Spec delta — formato ADDED/MODIFIED/REMOVED (solo cambios grandes)

Para cambios que afectan una capability, el delta spec vive en `openspec/changes/<id>/specs/<cap>/spec.md`. **NO** se modifica `openspec/specs/<cap>/spec.md` directamente — el merge ocurre al cerrar la propuesta (archivado).

```markdown
# Delta: <id> sobre capability <cap>

## ADDED Requirements

### Requirement: <nombre-nuevo>
The system SHALL <comportamiento nuevo>.

## MODIFIED Requirements

### Requirement: <nombre-existente>
The system SHALL <comportamiento actualizado>.   ← antes era: <viejo>

## REMOVED Requirements

### Requirement: <nombre-viejo>
**Razón**: <por qué se quita>
**Migración**: <cómo se actualizan callers>
```

### Proposal — plantilla

```markdown
# Change: <id-corto>

## Why
[problema u oportunidad, 1-3 parrafos]

## What Changes
- [bullet list concreto: código/spec/docs afectados]

## Impact
- **Size**: [trivial / pequeño / mediano / grande]
- **Capabilities affected**: [woptimizer / gaming / kill / ...]
- **Risks**: [qué puede romperse, mitigación]
- **Tests required**: [qué tests correr + nuevos]
- **Documentation**: [qué docs actualizar]
```

### Tasks — checklist numerado

```markdown
# Tasks for <id>

## 1. <area>
- [ ] paso concreto (verbo + archivo)
- [ ] ...

## N. Validar
- [ ] tests: `<comando>`
- [ ] commit: `<id>: <descripcion>`
- [ ] mover a archive/
```

### `todowrite` ↔ `tasks.md` — reglas de sincronización

- `todowrite` (tool nativa) es el task manager visible para el usuario durante la sesión.
- `tasks.md` es el artefacto persistente en disco (parte del commit).
- **Reglas**:
  1. Si `tasks.md` tiene ≤3 steps → no usar `todowrite`, ejecutar directo.
  2. Si `tasks.md` tiene >3 steps → reflejar la lista en `todowrite` al inicio de la implementación.
  3. Cada `- [ ]` en `tasks.md` = 1 item en `todowrite`.
  4. Marcar item como `completed` SOLO después de haberlo hecho Y verificado.
  5. Al cerrar la propuesta (paso 9), `tasks.md` queda con todo `[x]` → evidencia de progreso.
- **Prohibido** marcar steps completados sin haberlos hecho (no inflar progreso).

### Carga selectiva de documentación

Para minimizar tokens, el agente DEBE leer en este orden:

1. `AGENTS.md` (este archivo) — siempre primero y último.
2. `llms.txt` (raíz) — índice curado con links a docs.
3. Solo si el cambio lo requiere: abrir docs específicos desde los links en `llms.txt`.

NO leer `docs/*.md` a ciegas. Usar `llms.txt` como índice.

### Reglas duras del SDD

- ❌ Tocar código sin proposal previa (excepción: cambios triviales según la matriz).
- ❌ Commit mezclando dos `<change-id>`.
- ❌ Borrar entradas de `openspec/changes/archive/` — es historial inmutable.
- ❌ Modificar `openspec/specs/*.md` directamente sin proposal — los cambios van vía delta specs en `changes/<id>/specs/<capability>/spec.md`.
- ❌ Saltar pasos en `tasks.md` sin marcar completados.
- ✅ Cualquier agente IA que toque este proyecto debe LEER `AGENTS.md` y `llms.txt` antes de empezar.

---

## 📦 Project Overview

- **Stack:** Python 3.x + tkinter (GUI), PowerShell embebido para listar procesos, Windows-only.
- **Entry points:** `ProcessManager.vbs` (doble clic silencioso), `python process_manager.pyw` (sin consola).
- **Persistencia dual:** `saved_processes.json` (legacy v1.1) + `profiles.json` (v2.0+).
- **Versión actual:** `2.1.0` (`process_manager.py:15`).
- **Estado:** ✅ funcional · ✅ perfiles v2.0 · ✅ Trampa #15 gaming keepers · ✅ Perfil de sistema "Gaming" editable y reseteable (v2.0.6) · ✅ Bug #2 doble-tap per-button · ✅ `_run_kill()` con verificación post-kill · ✅ Ejecutable Windows standalone (`woptimizer.exe`) con auto-elevación admin (v2.1.0) · ✅ **Flujo SDD con OpenSpec + llms.txt** (v2.1.1) · ❌ Mini App bloqueada por EACCES sandbox (ver `docs/mini-app-status.md`).

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

# 5. Build del ejecutable (v2.1.0+)
pip install pyinstaller
.\build.bat

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
| 117-220 | Gaming system profile (v2.0.6) — constantes, factory, `should_kill_for_gaming()` |
| 222-345 | `_run_kill()` ← Trampa #15 |
| 348-477 | `categorize_process()`, `is_admin()`, `get_running_processes()` ← Trampa #1 |
| 480-503 | `expand_selection_by_name()` ← Trampa #13 |
| 506-583 | `kill_processes()` ← Trampa #11 |
| 586-723 | save/load + `relaunch_processes()` |
| 725-960 | CRUD perfiles (v2.0) + load/reset gaming profile |
| 962-1720 | `class ProcessManagerApp` (UI) |
| 1722-2056 | `class ProfilesDialog` (+ editor gaming profile v2.0.6) |

Profundidad en `docs/architecture.md` · API en `docs/api.md` · extensiones en `docs/extending.md`.

---

## 🎮 Perfil de sistema "Gaming" (v2.0.6, antes Trampa #15 hardcoded)

`🚀 Preparar para Gaming` deja de ser un comportamiento **hardcoded** y pasa a ser un **perfil de sistema** que el usuario puede editar y resetear.

### Diferencia vs perfil de usuario

| Aspecto | Perfil de usuario | Perfil Gaming (sistema) |
|---|---|---|
| Storage | `profiles.json` | `profiles.json` (mismo archivo) |
| Schema | `{kind: "user", apps: [...]}` | `{kind: "system", keepers: [...], kill_low_chat: bool}` |
| Creable/borrable | ✅ ambos | ❌ siempre presente, **no se puede borrar** |
| Marcable favorito | ✅ | ❌ no aplica (no es relanzable) |
| Editable | ✅ apps list | ✅ keepers list + `kill_low_chat` toggle |
| Reseteable | ❌ | ✅ "Reset a valores de fábrica" |
| Schema versionado | ❌ | ✅ `factory` snapshot embebido para reset |

### Clave interna

- Nombre en `profiles.json`: `"__system_gaming__"`
- Label visible en UI: `🚀 Preparar para Gaming`
- Constante: `SYSTEM_GAMING_PROFILE_KEY = "__system_gaming__"`

### Factory defaults (lo que viene si nunca se ha tocado)

```python
SYSTEM_GAMING_FACTORY = {
    "kind": "system",
    "label": "🚀 Preparar para Gaming",
    "keepers": ["discord"],          # chat de voz con amigos durante la partida
    "kill_low_chat": True,            # matar Telegram, Teams, Signal, etc.
}
```

### Reglas de `should_kill_for_gaming(name, profile)` (acepta profile, no constante)

1. Si el `name` matchea cualquier string en `profile["keepers"]` → **False** (mantener).
2. Si prioridad `high` o `medium` → **True** (matar).
3. Si prioridad `low` y categoría `🟡 Chat y Comunicación` Y `profile["kill_low_chat"]` es True → **True** (override).
4. Resto → **False** (mantener).

### Auto-creación

`load_profiles()` ahora:
- Si el archivo no existe o no contiene `"__system_gaming__"` → lo crea con factory defaults.
- Garantiza que **SIEMPRE** hay un perfil gaming válido al cargar.

### `ProfilesDialog` — comportamiento cuando se selecciona Gaming

- **➕ Nuevo** → habilitado.
- **✏️ Editar** → abre `GamingProfileEditor` (editor especial con keepers + kill_low_chat + Reset a fábrica).
- **🗑️ Borrar** → **deshabilitado** (botón gris, no clickable, tooltip explica).
- **⭐ Favorito** → **oculto** (no aplica).
- **▶️ Lanzar** → **oculto** (no es relanzable).
- Listbox muestra `🔒 🚀 Preparar para Gaming` con icono 🔒 para distinguirlo.

### Acceptance criteria

1. ✅ Al primer arranque sin `profiles.json`, gaming funciona con factory defaults sin crashear.
2. ✅ El usuario puede añadir/quitar keepers desde el editor y se persisten al disco.
3. ✅ El usuario puede togglear `kill_low_chat` y se persiste.
4. ✅ Botón "Reset a valores de fábrica" revierte keepers + toggle a factory, persistido.
5. ✅ Botón "🗑️ Borrar" está deshabilitado para gaming (no se puede borrar).
6. ✅ `should_kill_for_gaming` lee del profile (NO de constante hardcoded).
7. ✅ Si `profiles.json` tiene gaming corrupto/parcial, se repara con factory defaults (no crashea).

### Tests de regresión

- `python test_gaming_profile.py` (nuevo v2.0.6) — cubre los 7 criterios arriba.
- `python test_gaming_session.py` — sigue pasando (la lógica de kill es la misma, ahora lee del profile).
- `python test_profiles.py` — sigue pasando (esquema de perfil de usuario intacto).

---

## 📦 Ejecutable Windows standalone (v2.1.0)

A partir de v2.1.0, woptimizer se distribuye como **un único `.exe`** standalone, sin requerir Python instalado en la máquina del usuario final.

### Comando de build

```powershell
pip install pyinstaller
.\build.bat
```

Genera `dist\woptimizer.exe` (single-file, ~9-12 MB, sin consola, auto-eleva como admin).

### Decisiones técnicas

| Aspecto | Decisión | Por qué |
|---|---|---|
| Empaquetador | **PyInstaller 6.x** `--onefile` | Estándar, simple, soporte nativo para tkinter + stdlib. Nuitka es más rápido pero requiere MSVC y la build es 5x más lenta. |
| Modo ventana | `--noconsole` (`--windowed`) | GUI tkinter no debe mostrar consola. |
| Elevación admin | `--uac-admin` (PyInstaller ≥5.13) | Embe manifest `requireAdministrator` en el PE header. Auto-arregla Bug #1. |
| Nombre | `woptimizer.exe` | Marca del proyecto, corto. |
| Datos del usuario (`profiles.json`, `saved_processes.json`) | Junto al `.exe` (`sys.executable` dir) | Funciona en `--onefile` y `--onedir`. Cero config para el usuario. Si el .exe vive en `C:\Program Files\`, hay que moverlo a una carpeta writable (sigue siendo del usuario). |
| Icono | (placeholder, sin icono por ahora) | Añadir `--icon=assets/icon.ico` cuando se cree. |
| Python runtime | **Embe PyInstaller 3.13** | Empaquetamos el runtime. Usuario final NO necesita instalar Python. |
| PowerShell | **NO embeber — dependencia del sistema** | PowerShell 5.1 viene en Windows 10/11. Embedding pwsh 7 añadiría 80 MB. Si falla, mostrar error claro en status_label. |

### Path handling para frozen mode

En `process_manager.py`, **NO** usar `__file__` directamente para rutas de datos — no apunta al .exe en frozen mode. Usar helper:

```python
def _app_dir() -> str:
    """Devuelve el directorio donde está el ejecutable (frozen o dev)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))
```

`PROCESS_LIST_FILE` y `PROFILES_FILE` pasan a usar `_app_dir()`.

### Acceptance criteria

1. ✅ `dist\woptimizer.exe` existe tras ejecutar `build.bat`.
2. ✅ Doble clic en el `.exe` lanza la GUI sin mostrar consola.
3. ✅ Doble clic en el `.exe` dispara UAC prompt (auto-eleva a admin) — Bug #1 arreglado de paso.
4. ✅ La GUI lista procesos reales (PowerShell funciona).
5. ✅ `profiles.json` se crea junto al `.exe` al primer guardado.
6. ✅ `woptimizer.exe` corre en una máquina Windows SIN Python instalado.
7. ✅ Kill funciona (admin elevation OK).
8. ✅ Sin regresiones: `verify_app.py`, `test_kill_real.py`, `test_gaming_profile.py` siguen pasando con `process_manager.py` (dev mode).

### Anti-patrones (Trampa #17)

- ❌ Embeber `python313.dll` + tkinter separado → PyInstaller ya lo hace, no inventar.
- ❌ Path relativo `os.path.dirname(__file__)` en frozen mode → apunta a `sys._MEIPASS` (temp dir), no al .exe. **Siempre** `sys.executable` cuando `getattr(sys, 'frozen', False)`.
- ❌ Embedder PowerShell 7 → +80 MB, no vale la pena.
- ❌ Generar `--onedir` con assets/ separados → menos portable, mismo tamaño.
- ❌ Asumir que `pythonw.exe` está en PATH en máquina del usuario → con `.exe` ya no importa.

### Tests

- `python verify_exe.py` (nuevo v2.1.0) — verifica que `dist\woptimizer.exe` existe, arranca sin consola, lista procesos.
- `python -c "import PyInstaller; print(PyInstaller.__version__)"` debe ser ≥5.13 (para `--uac-admin`).

---

## 🌿 Control de versiones (git local)

Repo git local para no perder cambios. **Doble clic** en los scripts (no requiere git CLI en PATH si está instalado Git for Windows).

| Script | Qué hace |
|---|---|
| `init_git.bat` | Inicializa el repo (solo la 1ª vez; si ya existe `.git`, sale sin tocar nada), configura usuario, commit inicial + tag con la **versión actual** leída de `__version__`. |
| `commit_version.bat` | Tras cambios: lee `__version__` del código, hace commit con version + mensaje. |
| `test_kill_firefox.bat` | Diagnóstico directo: `taskkill /F /IM firefox.exe /T` con verificación post-kill. |

**Estado actual:** ⚠️ el sandbox del Host bloquea el shell del agente (`spawn EPERM`, 2026-09-15): el agente no puede ejecutar git directamente. **Acción inmediata:** doble clic en `init_git.bat` → init + commit inicial + tag **v2.0.6** (idempotente: si `.git` ya existe, sale sin tocar nada). Verificar: `git log --oneline --decorate` debe mostrar `tag: v2.0.6`.

`.gitignore` excluye: `profiles.json`, `saved_processes.json` (datos del usuario), `*.testbak*` (backups de tests), `__pycache__/`, `*.pyc`, `node_modules/`, `.vscode/`, `.idea/`, `*.log`.

---

## 🐛 Bugs activos a corregir

### Bug #1: La app debería lanzarse siempre como admin
`ProcessManager.vbs` no eleva correctamente. Investigar `ShellExecute ... , , , "runas"` o `Start-Process -Verb RunAs` desde `.ps1`. Cuando se arregle, añadir badge 🛡️ en la barra de título usando `is_admin()` (línea 130-137).

### Bug #2: Mensaje de confirmación sale en todos los botones ✅ **RESUELTO v2.0.4**
El doble tap ("⚠️ PULSA OTRA VEZ") aparecía en TODOS los botones de acción, no solo en el pulsado. Fix aplicado: `_pending_action` ahora guarda `(button, normal_label)`; `_request_confirm` cambia SOLO ese botón; `_reset_pending_action` restaura SOLO ese botón.

### Bug #1: La app debería lanzarse siempre como admin ✅ **RESUELTO v2.1.0**
`ProcessManager.vbs` no eleva correctamente. Resuelto de paso con PyInstaller `--uac-admin` que embebe el manifest `requireAdministrator` en el PE header. La versión `.exe` siempre arranca como admin sin VBS. Para usuarios que sigan usando `process_manager.pyw`, Bug #1 sigue documentado pero aplica solo al launcher VBS legacy.

---

## 📚 Documentación relacionada

| Recurso | Cuándo leerlo |
|---|---|
| [`llms.txt`](llms.txt) | **Índice curado para agentes IA** — punto de entrada LLM-friendly. Lee primero. |
| [`llms-full.txt`](llms-full.txt) | **Texto completo de la documentación** concatenado para contextos grandes. |
| [`docs/known-issues.md`](docs/known-issues.md) | **Catálogo completo de las 17 trampas** con síntomas, causas, fix y tests de regresión. **Leer antes** de tocar scripts PowerShell, subprocess, kill, o si algo "no funciona". |
| [`docs/testing.md`](docs/testing.md) | Catálogo de tests, patrones de debug, test_harness E2E. |
| [`docs/api.md`](docs/api.md) | API reference con firmas exactas (qué retorna cada función pública). |
| [`docs/architecture.md`](docs/architecture.md) | Flujo de datos, componentes, decisiones arquitectónicas. |
| [`docs/extending.md`](docs/extending.md) | Cómo añadir features (categoría, botón, atajo, etc.) sin romper nada. |
| [`docs/mini-app-status.md`](docs/mini-app-status.md) | Estado de la Mini App (bloqueada por EACCES del sandbox del Host). |
| [`openspec/specs/`](openspec/specs/) | **Source of truth** de requisitos (formato `SHALL`). Cambios siempre vía `openspec/changes/`. |
| [`openspec/changes/`](openspec/changes/) | Propuestas activas. Cada una con `proposal.md` + `tasks.md`. |
| [`openspec/changes/archive/`](openspec/changes/archive/) | Cambios cerrados (historial, NO borrar). |

---

## Changelog del spec

- **rev 12 (2026-09-24)** — **Refinamiento del flujo SDD** (sostenibilidad + claridad). Cambios sobre rev 11:
  - **Decision matrix** explícita: trivial / pequeño / mediano / grande, con ejemplos y artefactos requeridos por tamaño.
  - **Spec delta** documentado formalmente con plantilla ADDED/MODIFIED/REMOVED para `openspec/changes/<id>/specs/<cap>/spec.md`.
  - **`todowrite` ↔ `tasks.md`** — reglas de sincronización explícitas (cuándo usar todowrite, qué items, cuándo marcar done).
  - **Anti-burocracia** — heurísticas para evitar sobre-procesar cambios pequeños (decompose si >1 página o >20 items).
  - Tamaño del cambio añadido al campo `Impact` de la plantilla Proposal.
  Spec rev 12, sin bump de código.
- **rev 11 (2026-09-24)** — **Adopción del flujo SDD con OpenSpec + llms.txt** (sin bump de versión de código todavía; se aplicará en el próximo release que lo necesite). Nueva sección "📜 Spec-Driven Development (SDD) — flujo OBLIGATORIO" en AGENTS.md. Estructura del repo: `openspec/{specs,changes,changes/archive}/`. Capacidad canónica: `openspec/specs/woptimizer/spec.md`. Cambio de demo archivado: `openspec/changes/archive/2026-09-24-init-sdd-workflow/`. Carga selectiva habilitada vía `llms.txt` + `llms-full.txt` en raíz. Específico: todo cambio futuro debe seguir este flujo (openspec proposal → plan → código). Spec rev 11.
- **rev 10 (2026-09-24)** — **Ejecutable Windows standalone (v2.1.0)**. PyInstaller `--onefile --noconsole --uac-admin` genera `dist\woptimizer.exe`. Auto-eleva como admin (arregla Bug #1 de paso). Datos del usuario (`profiles.json`, `saved_processes.json`) viven junto al `.exe` via helper `_app_dir()`. Nueva Trampa #17 (path handling frozen mode). Spec rev 10, código v2.1.0.
- **rev 9 (2026-09-14)** — **Perfil de sistema "Gaming" editable y reseteable (v2.0.6)**. Trampa #15 (`GAMING_KEEPERS` hardcoded) reemplazada por perfil en `profiles.json` con clave `__system_gaming__`. Usuario puede editar keepers y toggle `kill_low_chat`, resetear a factory defaults. No borrable. Auto-creado por `load_profiles()` si falta. Schema versionado con `factory` snapshot embebido. Spec rev 9, código v2.0.6.
- **rev 8 (2026-09-14)** — Workflow git local: `init_git.bat`, `commit_version.bat`, `.gitignore`. Bug #2 marcado ✅ RESUELTO v2.0.4. Versión actualizada a v2.0.5 (incluye Trampa #15 gaming keepers + `_run_kill()` con verificación post-kill). Spec rev 8.
- **rev 7 (2026-09-14)** — Reestructuración completa siguiendo best practice AGENTS.md (comandos primero, three-tier boundaries, target <200 líneas). Eliminado el catálogo inline de 15 trampas (ahora solo se referencia `docs/known-issues.md`). Spec-First movido a `Always` boundaries. Spec rev 7.
- **rev 6 (2026-09-14)** — Bugs a corregir (#1 admin elevation + indicador 🛡️, #2 confirmación solo en botón pulsado). Trampa #15 (`should_kill_for_gaming`).
- **rev 5 (2026-09-14)** — Trampa #14: doble tap para confirmación, status label inline para feedback.
- **rev 4 (2026-09-14)** — Refactor completo: Spec-First rule, Validate-Yourself, 13 trampas, tabla de tests por área, API pública, mapa de líneas.
- **rev 3** — v2.0 con perfiles y agrupación.
- **rev 2** — Trampas #1-4, modo Simple.
- **rev 1** — Spec inicial (kill_processes / save / relaunch básico).
