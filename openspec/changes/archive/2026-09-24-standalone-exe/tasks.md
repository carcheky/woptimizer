# Tasks for standalone-exe (v2.1.0) — ARCHIVADO

## 1. Preparación

- [x] Verificar Python 3.13.8 disponible
- [x] Leer AGENTS.md rev 9 (estado pre-cambio)
- [x] Listar archivos a tocar en la sección de mapa de líneas

## 2. Implementar helper `_app_dir()` en process_manager.py

- [x] Añadir `import sys` (línea 9)
- [x] Bumpear `__version__` 2.0.6 → 2.1.0 (línea 15)
- [x] Crear helper `_app_dir()` que devuelve `sys.executable` dir en frozen mode, `__file__` dir en dev mode
- [x] Cambiar `PROCESS_LIST_FILE` para usar `_app_dir()`
- [x] Cambiar `PROFILES_FILE` para usar `_app_dir()`

## 3. Crear scripts de build y validación

- [x] Crear `build.bat` que invoca `pyinstaller --onefile --noconsole --uac-admin --name woptimizer process_manager.pyw`
- [x] Crear `verify_exe.py` con checks: PyInstaller ≥5.13, .exe existe >5MB, PE magic MZ, manifest requireAdministrator, launch sin crash
- [x] Sincronizar `process_manager.pyw` ← `process_manager.py` (Copy-Item)

## 4. Build

- [x] `pip install pyinstaller` (instalado v6.22.3)
- [x] `.\build.bat` → genera `dist\woptimizer.exe` (10.510.009 bytes)

## 5. Validación (Validate-Yourself)

- [x] `python -c "import py_compile; py_compile.compile('process_manager.py', doraise=True)"` → OK
- [x] `python verify_exe.py` → 5/5 checks PASS
- [x] `python verify_app.py` → GUI arranca OK (sin tocar código)
- [x] `python test_profiles.py` → 13/13 tests OK
- [x] `python test_gaming_profile.py` → tests OK, factory defaults auto-created en dist/ junto al .exe (Trampa #17 funcionando)

## 6. Spec-First

- [x] AGENTS.md: spec rev 9 → 10
- [x] Sección nueva "📦 Ejecutable Windows standalone (v2.1.0)" con decisiones técnicas y anti-patrones
- [x] Nueva Trampa #17
- [x] Bug #1 marcado ✅ RESUELTO v2.1.0
- [x] Changelog del spec: entrada rev 10

## 7. Notas post-implementación

- ⚠️ PyInstaller protesta por correr como admin (`DEPRECATION: Running PyInstaller as admin`). Build funciona pero PyInstaller 7.0 bloqueará. Acción futura: ejecutar build.bat desde terminal no-admin.
- ⚠️ El .exe generado NO está firmado digitalmente → algunos antivirus harán flag. Out of scope para esta versión.
- ✅ `_app_dir()` verificado funcionando: durante verify_exe.py, `profiles.json` se auto-creó junto al .exe con gaming profile factory defaults.