# Tareas OpenSpec: v3.1 Quality of Life

- [x] **1. Logging y Backups Automáticos**
  - [x] Añadir configuración de `logging` en `config.py` (archivo `woptimizer.log`).
  - [x] Modificar `PackService.save()` para que cree un archivo `profiles.json.bak` de forma segura.
  - [x] Remplazar los `print` críticos o `pass` silenciosos (ej. fallos en `kill_pack_apps`) por `logger.warning`.

- [x] **2. Integración System Tray (pystray)**
  - [x] Instalar dependencia `pystray` y añadirla a `requirements.txt` (o documentarlo).
  - [x] En `app.py`, interceptar el protocolo de cierre de ventana para ocultarla (`withdraw`).
  - [x] Implementar un hilo secundario que levante el icono en la bandeja usando `pystray.Icon`.

- [x] **3. Interacciones y Cierre Real**
  - [x] Añadir un menú contextual al System Tray con "Mostrar App", "Preparar Gaming Mode" y "Salir".
  - [x] Enlazar el botón "Preparar Gaming Mode" a `ProcessService.kill_pack_apps(gaming_pack)`.
  - [x] Asegurar que el botón "Salir" cierre completamente la app (`destroy` y `sys.exit`).
