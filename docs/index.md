# woptimizer — Process Manager con foco gamer

> **Estado actual:** Producto Python funcional. Mini App en `miniapps/process_manager/` queda como referencia (no publicable por bloqueo del sandbox del Host MiniMax Code, ver [`known-issues.md`](known-issues.md)).

## Qué es

App Windows para matar procesos de fondo en categorías gaming (navegadores, sync, chat, productividad, media), guardarlos y relanzarlos después. Pensada para preparar el PC antes de jugar.

## Quick start

```bash
# Ejecutable standalone (recomendado, auto-eleva admin)
dist\woptimizer.exe

# O en modo desarrollo con Python
pythonw.exe process_manager.pyw

# O lanzador silencioso legacy
ProcessManager.vbs

# Validar estado
python smoke_check.py
python verify_app.py
```

## Características

- 9 categorías gaming con prioridades (🔴 matar / 🟡 opcional / 🟢 mantener / ⚫ no tocar)
- Modo Simple (solo categorías gaming) / Completo (todas)
- Perfil de sistema Gaming (`🚀 Preparar para Gaming`) personalizable y reseteable a fábrica
- Gestión de perfiles de usuario (`profiles.json`) con favoritos y relanzamiento
- Búsqueda en nombre + commandline
- Click toggle (sin Ctrl), click derecho = menú contextual
- Atajos: Ctrl+A, Delete, F5, Escape
- Kill robusto (`taskkill /F /T` con exit 128 = success y verificación post-kill)
- Ejecutable Windows standalone `woptimizer.exe` con auto-elevación UAC nativa
- Flujo Spec-Driven Development (SDD) con OpenSpec y `llms.txt`

## Estructura del repo

```
woptimizer/
├── process_manager.py          # Script principal (source)
├── process_manager.pyw         # Mismo, para pythonw.exe (sin consola)
├── dist/woptimizer.exe         # Ejecutable standalone compilado (PyInstaller)
├── build.bat                   # Script de compilacion del .exe
├── ProcessManager.vbs          # Lanzador silencioso legacy (doble clic)
├── profiles.json               # Perfiles de usuario y sistema Gaming (auto-creado)
├── saved_processes.json        # Estado persistente legacy (auto-creado)
│
├── smoke_check.py              # Smoke test de sintaxis AST y Trampa #17
├── verify_app.py               # Test que lanza app y verifica que arranca
├── verify_pyw.py               # Igual pero con pythonw.exe
├── verify_exe.py               # Verificacion del .exe, PE magic y auto-elevacion
├── test_gaming_profile.py      # Tests unitarios del perfil de sistema Gaming
├── test_kill_real.py           # Test que mata proceso real y verifica muerte
├── test_profiles.py            # Tests de CRUD y favoritos de perfiles
├── validate_docs.py            # Validador de formato llms.txt y SDD OpenSpec
│
├── openspec/                   # Especificaciones y propuestas SDD
├── docs/                       # Documentacion tecnica en Markdown
├── mkdocs.yml                  # Configuracion del portal web de documentacion
└── miniapps/process_manager/   # Version Mini App (de referencia, bloqueada)
```

## Documentación web (MkDocs)

Para previsualizar o compilar la documentación localmente:

```bash
# Servir en local (http://127.0.0.1:8000)
mkdocs serve

# Compilar HTML estático en site/
mkdocs build
```

## Siguiente paso

Lee [`architecture.md`](architecture.md) para entender el flujo de datos, o [`known-issues.md`](known-issues.md) si vas a modificar el script PowerShell (importante).
