# Tareas OpenSpec: Telemetría de RAM Liberada

- [ ] **1. Medición de RAM en ProcessService**
  - [ ] Actualizar `kill_processes` para sumar `memory_info().rss` de hijos y padre y retornar `(killed, failed, skipped, freed_mb)`.
  - [ ] Actualizar `kill_pack_apps` para calcular memoria física liberada y retornar la misma 4-tupla.
  - [ ] Asegurar compatibilidad hacia atrás si algún llamador espera desempaquetar solo 3 valores o adaptarse cleanly.

- [ ] **2. Banner de Feedback en Portada (DashboardView)**
  - [ ] Añadir `status_banner` en `dashboard_view.py`.
  - [ ] Conectar la ejecución del pack en segundo plano con actualización thread-safe (`self.after`).
  - [ ] Mostrar mensaje dinámico de éxito con conteo de apps y MB liberados.
