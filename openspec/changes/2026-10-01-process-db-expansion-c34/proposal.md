# Proposed Change: Expansión de Base de Procesos de Windows (Ciclo #34)

- **ID:** `2026-10-01-process-db-expansion-c34`
- **Task:** `TASK-044`
- **Área:** Base de Datos & Procesos (Área 3)

## Motivo y Alcance
Ampliación de `assets/process_db.json` para incluir 7 nuevos procesos reales del entorno Windows (herramientas de hardware/OSD, launchers de juegos y software de desarrollo/productividad) manteniendo 0 solapamientos con `SYSTEM_PROTECTED_PROCESSES`.

## Cambios Clave
- Incorporación de `rtss`, `msiafterburner`, `hwinfo64`, `galaxyclient`, `everything`, `gitkraken`, `postman` a `assets/process_db.json` (total: 96 procesos).
- Preservación de invariantes de blindaje anti-brick.
- Actualización de `docs/ai/data-models.md` a 96 procesos.
