# Tasks: Optimización de Latencia en Categorización de Procesos (Ciclo #35)

- [x] Auditar arquitectura y planificar vía `architect-review` subagent
- [x] En `ProcessService._load_local_db()`, invocar `self.invalidate_cache()` tras `self._meta_cache.clear()`
- [x] Añadir `test_process_categorization_latency_and_memoization` en `run_tests.py`
- [x] Actualizar `docs/ai/architecture.md`
- [x] Validar con `run_tests.py` y `validate_docs.py`
- [x] Auditar con `mutation-auditor` (Paso 4)
