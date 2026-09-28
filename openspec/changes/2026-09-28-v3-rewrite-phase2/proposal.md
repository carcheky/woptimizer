# Change: v3-rewrite-phase2

## Why
El monolito de 2400 líneas en `process_manager.py` mezcla UI, lógica de negocio, listado de procesos vía PowerShell y acceso a disco. Esto lo hace frágil. La Fase 2 extrae la capa de datos y la lógica de sistema a módulos dedicados, reemplazando el costoso y propenso a fallos `Get-CimInstance` de PowerShell por `psutil`, y asegurando los perfiles JSON con `Pydantic`.

## What Changes
- Crear estructura de paquetes `src/woptimizer/`
- Extraer `PROCESS_CATEGORIES` y constantes a `config.py`
- Crear modelos de datos en `models.py` usando Pydantic
- Reemplazar funciones globales de listado y kill por `services/process_service.py` (usando `psutil`)
- Extraer la lógica de persistencia de `profiles.json` a `services/profile_service.py`
- Extraer la lógica del gaming system profile a `services/gaming_service.py`
- Migrar y adaptar los tests unitarios existentes para usar la nueva estructura

## Impact
- **Size**: grande
- **Capabilities affected**: woptimizer (backend completo)
- **Risks**: Riesgo de regresión en las reglas de kill o perfiles. 
- **Tests required**: Ejecutar suite de `tests/` completa tras cada servicio.
- **Documentation**: Actualizar guías si cambian las firmas de los servicios.
