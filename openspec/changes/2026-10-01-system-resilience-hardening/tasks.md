# Tasks: System Resilience and Concurrency Hardening (TASK-042)

- [ ] Reforzar `NotificationService` con cerrojos reentrantes (RLock) para attach/detach e invocaciones concurrentes a `notify`
- [ ] Reforzar `ProcessService.kill_processes` y captura de `ZombieProcess`/`OSError` en la eliminación recursiva de procesos hijos
- [ ] Añadir nuevos tests discriminantes en `run_tests.py` para verificar la resiliencia multihilo y captura defensiva
- [ ] Validar sintaxis de UI y suite de tests headless
