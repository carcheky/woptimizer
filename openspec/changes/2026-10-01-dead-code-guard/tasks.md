# Tareas de Implementación: Guard de Código Muerto (TASK-056)

## Tareas
- [x] 1. Eliminar `_get_priority` y `process_db` en `src/woptimizer/services/process_service.py`.
- [x] 2. Conectar `get_favorite_packs()` en `src/woptimizer/ui/views/dashboard_view.py`.
- [x] 3. Conectar y verificar `is_wcag_aa` en `test_contrast_wcag_aa` de `run_tests.py`.
- [ ] 4. Implementar test #99 `test_dead_code_ast_guard` en `run_tests.py` con escaneo AST dinámico y lista blanca justificada.
- [ ] 5. Sincronizar recuento de 99 tests en `STATUS.md`, `AGENTS.md`, `README.md` y `docs/ai/testing-guide.md`.
- [ ] 6. Verificar validadores (`validate_docs.py`, `verify_ui_syntax.py`, `run_tests.py`).
- [ ] 7. Auditar con `mutation-auditor` en `%TEMP%` (4/4 mutaciones eliminadas).
- [ ] 8. Cerrar ciclo #46 y pausar ejecución según instrucción del usuario.
