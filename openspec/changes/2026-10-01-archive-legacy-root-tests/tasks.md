# Tareas de Implementación: Archivo de tests legacy de la raíz (TASK-055)

## Tareas
- [ ] 1. Mover los 11 ficheros `test_*.py` de la raíz a `docs/archive/legacy-root-tests/`.
- [ ] 2. Crear `docs/archive/legacy-root-tests/README.md` documentando el motivo del retiro de los 10 scripts y el caso especial de `test_powershell_direct.py`.
- [ ] 3. Añadir test #98 `test_no_legacy_test_files_in_root` en `run_tests.py`.
- [ ] 4. Sincronizar recuento de 98 tests en `STATUS.md`, `AGENTS.md`, `README.md` y `docs/ai/testing-guide.md`.
- [ ] 5. Verificar validadores (`validate_docs.py`, `verify_ui_syntax.py`, `run_tests.py`).
- [ ] 6. Auditar con `mutation-auditor` y cerrar ciclo #45.
