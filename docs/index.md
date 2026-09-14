# woptimizer — Process Manager con foco gamer

> **Estado actual:** Producto Python funcional. Mini App en `miniapps/process_manager/` queda como referencia (no publicable por bloqueo del sandbox del Host MiniMax Code, ver [`known-issues.md`](known-issues.md)).

## Qué es

App Windows para matar procesos de fondo en categorías gaming (navegadores, sync, chat, productividad, media), guardarlos y relanzarlos después. Pensada para preparar el PC antes de jugar.

## Quick start

```bash
# Lanzar (doble clic en Windows)
ProcessManager.vbs

# O desde línea de comandos (sin consola)
pythonw.exe process_manager.pyw

# Validar que arranca
python verify_app.py
```

## Características

- 9 categorías gaming con prioridades (🔴 matar / 🟡 opcional / 🟢 mantener / ⚫ no tocar)
- Modo Simple (solo categorías gaming) / Completo (todas)
- Búsqueda en nombre + commandline
- Click toggle (sin Ctrl), click derecho = menú contextual
- Atajos: Ctrl+A, Delete, F5, Escape
- Persistencia en `saved_processes.json` (auto-guarda lo matado, relanza cuando quieras)
- Kill robusto (`taskkill /F /T` con exit 128 = success)
- Auto-elevación admin (cuando se necesita matar procesos protegidos)

## Estructura del repo

```
woptimizer/
├── process_manager.py          # Script principal (source)
├── process_manager.pyw         # Mismo, para pythonw.exe (sin consola)
├── ProcessManager.vbs           # Lanzador silencioso (doble clic)
├── ProcessManager.ps1           # Lanzador alternativo PowerShell
├── saved_processes.json        # Estado persistente (auto-creado)
│
├── verify_app.py               # Test que lanza app y verifica que arranca
├── verify_pyw.py               # Igual pero con pythonw.exe
├── test_kill_real.py           # Test que mata notepad de verdad
├── test_harness.py             # Test E2E original (cycle PowerShell→kill→save→relaunch)
│
└── miniapps/process_manager/   # Versión Mini App (no publicable)
    └── BLOCKED.md              # Por qué no funciona
```

## Siguiente paso

Lee [`architecture.md`](architecture.md) para entender el flujo de datos, o [`known-issues.md`](known-issues.md) si vas a modificar el script PowerShell (importante).
