# Arquitectura y Separación de Capas (v3)

## Stack Tecnológico
- **Python**: 3.11+
- **Motor de Procesos**: `psutil` (reemplaza cualquier llamada externa a PowerShell o WMI).
- **Persistencia y Validación**: `pydantic v2` para esquemas de datos estructurados.
- **Interfaz Gráfica**: `customtkinter` (modo oscuro por defecto, componentes modernos).
- **Empaquetador**: `PyInstaller` con manifiesto UAC admin.

## Invariante de 3 Capas (Three-Tier Rule)
```
┌───────────────────────────────────────────────┐
│ Capa 1: UI (src/woptimizer/ui/)               │
│ - SOLO CustomTkinter y presentación.          │
│ - NUNCA llama a psutil, subprocess ni JSON.   │
└───────────────────────┬───────────────────────┘
                        ▼ Inyección de dependencias
┌───────────────────────────────────────────────┐
│ Capa 2: Servicios (src/woptimizer/services/)  │
│ - process_service: psutil (listar, matar).    │
│ - pack_service: CRUD de perfiles y packs.     │
│ - gaming_service: Reglas automáticas gaming.  │
└───────────────────────┬───────────────────────┘
                        ▼ Modelos y Config
┌───────────────────────────────────────────────┐
│ Capa 3: Modelos & Config (src/woptimizer/)    │
│ - models.py: Pydantic schemas (Pack, Info).   │
│ - config.py: Categorías, prioridades, paths.  │
└───────────────────────────────────────────────┘
```

## Reglas de Arquitectura
1. **Kill Recursivo:** Todo cierre de proceso debe usar `parent.children(recursive=True)` antes de matar al padre para evitar procesos huérfanos.
2. **Punto de Entrada Único:** `python -m woptimizer` o `src/woptimizer/__main__.py`. Los servicios se instancian una sola vez y se inyectan en `WOptimizerApp`.

3. **Base de Datos Dinámica:** `assets/process_db.json` actúa como fuente local precargada de forma síncrona en `ProcessService`. Se actualiza de forma asíncrona desde el repositorio oficial en GitLab sin bloquear la GUI.
4. **Residencia en Bandeja (System Tray):** La aplicación no finaliza al presionar `[X]`; intercepta `WM_DELETE_WINDOW` para ocultarse (`withdraw`) y levantar un icono en la barra de tareas mediante `pystray`. Solo la opción 'Salir' destruye el proceso.
5. **Telemetría y Logs:** Errores de acceso (`AccessDenied`) y avisos del backend se canalizan a `woptimizer.log`.
6. **Entornos de Sincronización en la Nube (Nextcloud/OneDrive):** En Windows con unidades virtuales (VFS), los archivos `.git` pueden marcarse como reparse points. Para operaciones de Git locales se recomienda aislar el repositorio o redirigir `$env:GIT_DIR`.
