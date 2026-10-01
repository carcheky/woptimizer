# Tasks: Resiliencia de Concurrencia y Recuperación en GamingService (Ciclo #37)

- [ ] Auditar arquitectura e invariantes vía subagente `architect-review`
- [ ] Implementar `threading.RLock()` y atomicidad en `GamingService` (`src/woptimizer/services/gaming_service.py`)
- [ ] Reforzar captura defensiva en `ProcessService.start_pack_apps` (`src/woptimizer/services/process_service.py`)
- [ ] Implementar `test_gaming_service_rlock_and_concurrency` en `run_tests.py`
- [ ] Actualizar recuento de tests en documentación viva (`docs/ai/architecture.md`, `testing-guide.md`, `STATUS.md`, `AGENTS.md`, `README.md`)
- [ ] Validar con `run_tests.py`, `verify_ui_syntax.py` y `validate_docs.py`
- [ ] Auditar mutaciones con `mutation-auditor` (Paso 4)
