# Change: v3-rewrite-phase3

## Why
La UI original en `tkinter` raw está anticuada, tiene bugs visuales y mezcla lógica de negocio. Migrar a `CustomTkinter` permite una interfaz moderna con modo oscuro nativo, mejor UX (checkboxes reales, 2 botones de acción principales) y desacopla la vista de los servicios creados en la Fase 2.

## What Changes
- Crear estructura `src/woptimizer/ui/`
- Implementar `app.py` como contenedor principal
- Implementar `main_window.py` con el layout objetivo (botones Gaming / Pack, scroll de procesos)
- Eliminar dependencias de la UI antigua
- Crear el punto de entrada `__main__.py` que une Services y UI

## Impact
- **Size**: grande
- **Capabilities affected**: woptimizer (frontend)
- **Risks**: Fallos de renderizado en CustomTkinter si falta la librería.
- **Tests required**: Ejecución visual de `python -m woptimizer`.
