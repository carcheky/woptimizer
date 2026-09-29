# Tareas OpenSpec: Telemetría de RAM Liberada

- [ ] **1. Medición de RAM en ProcessService (TASK-013)**
  - [ ] Actualizar firma a `Tuple[int, int, int, float]` en `kill_processes` y `kill_pack_apps`.
  - [ ] Capturar memoria física (`proc.memory_info().rss`) de procesos hijos y padre ANTES de matarlos.
  - [ ] Acumular `freed_bytes` únicamente para procesos terminados exitosamente y convertir a `freed_mb` (`round(bytes / (1024 * 1024), 2)`).
  - [ ] Actualizar desempaquetado en `src/woptimizer/ui/views/process_manager_view.py:237` a `killed, failed, skipped, freed_mb = ...` para evitar `ValueError`.
  - [ ] Preservar kill recursivo (`children(recursive=True)`) y aislamiento de psutil en capa de servicios.

- [ ] **2. Banner de Feedback en Portada (DashboardView) (TASK-014)**
  - [ ] Añadir `status_banner` en `dashboard_view.py`.
  - [ ] Conectar la ejecución del pack en segundo plano con actualización thread-safe (`self.after`).
  - [ ] Mostrar mensaje dinámico de éxito con conteo de apps y MB liberados.

