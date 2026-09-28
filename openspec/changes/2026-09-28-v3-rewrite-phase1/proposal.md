# Change: v3-rewrite-phase1

## Why
La auditoría senior del 2026-09-28 diagnosticó deuda técnica significativa: monolito de 2400 líneas, ~280 líneas de código muerto, 75+ archivos en raíz (muchos innecesarios), build artifacts commiteados, y documentación desactualizada. La Fase 1 limpia el terreno para la reestructuración posterior.

## What Changes
- Eliminar código muerto de `process_manager.py` (~280 líneas deprecated)
- Eliminar constante `PS_DELIM` (nunca usada)
- Actualizar `.gitignore` (excluir build/, dist/, site/, *.spec)
- Eliminar archivos innecesarios (launchers legacy, miniapps/, sync_pyw.py, scripts manuales)
- Limpiar git de artifacts trackeados (`git rm --cached`)
- Eliminar `process_manager.pyw` (redundante con .exe)

## Impact
- **Size**: mediano
- **Capabilities affected**: ninguna (solo limpieza)
- **Risks**: bajo — solo se elimina código que no se ejecuta y archivos auxiliares
- **Tests required**: `python smoke_check.py`, `python test_gaming_profile.py`, `python test_profiles.py`
- **Documentation**: AGENTS.md se actualizará en fase posterior
