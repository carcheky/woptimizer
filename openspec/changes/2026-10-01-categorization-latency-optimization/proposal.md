# Proposed Change: Optimización de Latencia en Categorización de Procesos y Memoización (Ciclo #35)

- **ID:** `2026-10-01-categorization-latency-optimization`
- **Task:** `TASK-045`
- **Área:** Rendimiento & Latencia (Área 4)

## Motivo y Alcance
Refuerzo de la latencia en `ProcessService._categorize` mediante hit O(1) garantizado en `_meta_cache` e invalidación atómica de metadatos y snapshots (`_proc_cache`) al recargar la base de datos local (`_load_local_db`).

## Cambios Clave
- En `ProcessService._load_local_db()`, añadir `self.invalidate_cache()` tras `self._meta_cache.clear()` para expirar atómicamente la caché TTL de 2s.
- Asegurar que `_categorize(name)` / `_get_process_meta(name)` resuelva hits en `_meta_cache` < 0.001 ms para cualquier proceso (exacto, fuzzy o fallback).
- Añadir test discriminante `test_process_categorization_latency_and_memoization` en `run_tests.py` (vaciando `_db_map` para verificar el hit O(1) en caché).
- Actualizar documentación en `docs/ai/architecture.md`.
