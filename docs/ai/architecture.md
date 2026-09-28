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
