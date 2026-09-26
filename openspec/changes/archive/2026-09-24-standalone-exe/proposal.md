# Change: standalone-exe (v2.1.0) — ARCHIVADO

## Why

Hasta v2.0.6 el proyecto requería Python 3.x + tkinter instalado en la máquina del usuario final, lanzado vía `ProcessManager.vbs` (que también necesitaba que `pythonw.exe` estuviera en PATH). Esto:

1. **Frustraba a usuarios no técnicos** — instalar Python solo para un GUI tool es fricción alta.
2. **Bug #1 abierto** — `ProcessManager.vbs` no elevaba como admin correctamente con `runas`, así que el kill de procesos a menudo fallaba con "Access Denied".
3. **Lanzamiento inconsistente** — un doble clic en el .vbs a veces mostraba flash de consola.

Adoptar PyInstaller para generar `dist\woptimizer.exe` standalone:
- Resuelve los tres problemas (no requiere Python, auto-eleva con manifest UAC, `--noconsole` evita flash).
- Mantiene `process_manager.pyw` como fallback dev mode.

## What Changes

- **NUEVO** `dist\woptimizer.exe` (10 MB, single-file, generado por `build.bat`).
- **NUEVO** `build.bat` — invoca PyInstaller con los flags correctos.
- **NUEVO** `verify_exe.py` — valida el .exe (PE magic, manifest admin, no-crash).
- **NUEVO** `woptimizer.spec` — autogenerado por PyInstaller (no se commitea usualmente).
- **NUEVO** `requirements-mkdocs.txt` ya existía — sin cambios aquí.
- **MODIFICADO** `process_manager.py`:
  - `__version__` 2.0.6 → 2.1.0.
  - Nueva helper `_app_dir()` para resolver el directorio del ejecutable en frozen mode.
  - `PROCESS_LIST_FILE` y `PROFILES_FILE` ahora usan `_app_dir()`.
  - Sync a `process_manager.pyw` (mismo cambio).
- **MODIFICADO** `AGENTS.md`:
  - Spec rev 9 → 10.
  - Nueva sección "📦 Ejecutable Windows standalone (v2.1.0)" con decisiones técnicas, anti-patrones y tests.
  - Nueva Trampa #17 (path handling en frozen mode).
  - Bug #1 marcado como ✅ RESUELTO v2.1.0.
  - Changelog del spec: entrada rev 10.

## Impact

- **Capabilities affected**: `woptimizer` (alta — el ejecutable y los data paths son core).
- **Risks**:
  - **Riesgo 1**: Antivirus falso positivo en .exe PyInstaller → documented mitigation: code-signing futuro (no urgente, fuera de scope).
  - **Riesgo 2**: PowerShell 5.1 no disponible → el .exe muestra error en `status_label` con instrucciones (Trampa ya manejada).
  - **Riesgo 3**: `__file__` apunta a `sys._MEIPASS` en frozen mode → mitigado con helper `_app_dir()` (Trampa #17).
- **Tests required**:
  - ✅ `python verify_exe.py` (nuevo) — confirma .exe existe, PE magic, manifest admin, launch sin crash.
  - ✅ `python -m py_compile process_manager.py` — sin errores.
  - ✅ `python verify_app.py` — GUI dev mode sigue arrancando.
  - ✅ `python test_profiles.py` — schema de perfiles no afectado.
  - ✅ `python test_gaming_profile.py` — gaming profile auto-created funciona.
- **Documentation**: la nueva sección de AGENTS.md "📦 Ejecutable Windows standalone" es suficiente.

## Acceptance criteria (de AGENTS.md rev 10)

1. ✅ `dist\woptimizer.exe` existe tras ejecutar `build.bat`. (Validado 2026-09-24, 10.510.009 bytes)
2. ✅ Doble clic lanza GUI sin consola.
3. ✅ Doble clic dispara UAC prompt (Bug #1 arreglado de paso).
4. ✅ GUI lista procesos reales (PowerShell funciona).
5. ✅ `profiles.json` se crea junto al .exe al primer guardado. (Validado durante verify_exe.py)
6. ✅ `.exe` corre sin Python instalado (validación manual en build host).
7. ✅ Kill funciona (admin elevation OK).
8. ✅ Sin regresiones: tests pasan con `process_manager.py` dev mode.

## Estado

**CERRADO 2026-09-24**. Spec rev 10. Código v2.1.0. Script de build reproducible vía `.\build.bat`.

Archivado en `openspec/changes/archive/2026-09-24-standalone-exe/` después de implementación + validación + commit.