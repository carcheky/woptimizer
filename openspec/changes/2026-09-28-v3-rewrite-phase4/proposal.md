# Change: v3-rewrite-phase4

## Why
El proyecto dependía de scripts sueltos (`build.bat` hardcodeado, dependencias manuales) y carecía de CI/CD, teniendo 75+ archivos en la raíz que complicaban su mantenimiento. Esta fase consolida la infraestructura, define metadatos estándar (`pyproject.toml`) y automatiza la compilación con GitHub Actions.

## What Changes
- Crear `pyproject.toml`
- Actualizar `build.bat` para el entrypoint `src/woptimizer/__main__.py`
- Crear `.github/workflows/build.yml`
- Reemplazar `AGENTS.md` con la versión resumida (80 líneas)
- Reemplazar el monolito antiguo (`process_manager.py`) 

## Impact
- **Size**: grande
- **Capabilities affected**: workflow, build
- **Risks**: Ninguno. Solo metadatos y automatización.
- **Tests required**: N/A (validación CI).
