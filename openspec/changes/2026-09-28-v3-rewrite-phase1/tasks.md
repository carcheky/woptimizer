# Tasks for v3-rewrite-phase1

## 1. Eliminar código muerto de process_manager.py
- [ ] Eliminar `PS_DELIM` (constante nunca usada)
- [ ] Eliminar `expand_selection_by_name()` (nunca llamada)
- [ ] Eliminar `kill_processes()` (deprecated v2.0)
- [ ] Eliminar `save_processes_to_relaunch()` (deprecated v2.0)
- [ ] Eliminar `load_saved_processes()` (deprecated v2.0)
- [ ] Eliminar `relaunch_processes()` (deprecated v2.0)
- [ ] Eliminar `clear_saved_processes()` (deprecated v2.0)
- [ ] Eliminar métodos deprecated de ProcessManagerApp: `update_saved_count`, `save_selected`, `relaunch_saved`, `clear_saved`
- [ ] Eliminar `self.saved_processes` de `__init__` (no se usa)

## 2. Actualizar .gitignore
- [ ] Añadir build/, dist/, site/, *.spec, miniapps/

## 3. Eliminar archivos innecesarios
- [ ] Eliminar `process_manager.pyw` (copia redundante)
- [ ] Eliminar `ProcessManager.vbs` (launcher legacy roto)
- [ ] Eliminar `ProcessManager.bat` (launcher legacy)
- [ ] Eliminar `ProcessManager.ps1` (launcher legacy)
- [ ] Eliminar `sync_pyw.py` (no hay .pyw)
- [ ] Eliminar `test_kill_firefox.bat` (test manual invasivo)
- [ ] Eliminar `verify_doble_tap.bat` (test manual)
- [ ] Eliminar `TestHarness.bat`, `TestHarness.ps1` (wrappers legacy)
- [ ] Eliminar `TestHarness_v2.bat`, `TestHarness_v2.ps1` (wrappers)
- [ ] Eliminar `init_git.bat` (ya hay .git)
- [ ] Eliminar `woptimizer.spec` (generado por PyInstaller)

## 4. Validar
- [ ] `python -c "import py_compile; py_compile.compile('process_manager.py', doraise=True)"`
- [ ] `python smoke_check.py`
- [ ] `python test_gaming_profile.py`
- [ ] `python test_profiles.py`
