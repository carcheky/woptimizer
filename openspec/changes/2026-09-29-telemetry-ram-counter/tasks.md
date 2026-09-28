# Tareas OpenSpec: Telemetría de RAM Liberada

- [ ] **1. Medición de Recursos en Backend (`process_service.py`)**
  - [ ] Añadir cálculo de RAM (`memory_info().rss`) en `kill_pack_apps` antes del cierre recursivo.
  - [ ] Devolver estructura de telemetría `{"freed_ram_mb": float, "killed_processes": int}`.

- [ ] **2. Widget de Telemetría en la Portada (`views/dashboard_view.py`)**
  - [ ] Renderizar un banner destacado en la parte superior con estilo gaming (borde verde/azul o acentuado).
  - [ ] Conectar la ejecución del botón Gaming para actualizar la telemetría dinámicamente vía `.after(0, ...)`.

- [ ] **3. Verificación y Pruebas**
  - [ ] Ejecutar `run_tests.py` y `verify_ui_syntax.py`.
  - [ ] Validar que el cálculo de RAM no lance excepciones con procesos inaccesibles (`psutil.NoSuchProcess`).
