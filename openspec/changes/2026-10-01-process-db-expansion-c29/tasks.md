# Tareas OpenSpec: Expansión de la Base de Procesos - Ciclo 29 (TASK-039)

- **Change ID**: `2026-10-01-process-db-expansion-c29`
- **Tarea asociada**: `TASK-039`

---

## Tareas

- [x] Escanear procesos del sistema host mediante `psutil` y cruzarlos con `SYSTEM_PROTECTED_PROCESSES` y `assets/process_db.json`. <!-- id: 0 -->
- [x] Registrar 8 nuevos procesos reales en `assets/process_db.json` (`gamingservices`, `gamingservicesnet`, `adobecollabsync`, `filecoauth`, `filesynchelper`, `edgegameassist`, `hass.agent`, `gameinputredistservice`). <!-- id: 1 -->
- [x] Validar que las 89 entradas cumplen estrictamente el esquema y las categorías canónicas con `run_tests.py` (`test_process_db_schema_integrity`). <!-- id: 2 -->
- [x] Ejecutar `python run_tests.py`, `python verify_ui_syntax.py` y `python validate_docs.py`. <!-- id: 3 -->
- [x] Registrar `TASK-039` en `.taskmaster/tasks.json` y actualizar la documentación del sistema. <!-- id: 4 -->
