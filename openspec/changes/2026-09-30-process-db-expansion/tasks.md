# Tareas OpenSpec: Expansión de Process DB (TASK-032)

- **Change ID**: `2026-09-30-process-db-expansion`
- **Taskmaster**: `TASK-032`
- **Agente**: `process-db-updater`

---

## Tareas

- [x] **PDB-001 · Escaneo de procesos locales.**
      Escanear procesos vivos con `psutil`, listar nombres y comparar contra las 73 entradas de `assets/process_db.json`.
- [x] **PDB-002 · Filtrado y blindaje anti-brick.**
      Verificar que ningún proceso candidato pertenezca a `SYSTEM_PROTECTED_PROCESSES` ni a la infraestructura del sistema operativo Windows.
- [x] **PDB-003 · Clasificación de candidatos.**
      Investigar y categorizar nuevos candidatos en las categorías canónicas de `config.py` con semáforo de seguridad estricto.
- [x] **PDB-004 · Actualización de `assets/process_db.json`.**
      Añadir las nuevas entradas con formato JSON válido, preservando claves existentes y estructura estándar.
- [x] **PDB-005 · Verificación y tests.**
      Ejecutar `run_tests.py` (especialmente `test_no_system_process_is_killable`, `test_category_emoji_alignment` y `test_safety_badge_category_priority_order`) y `validate_docs.py`.
