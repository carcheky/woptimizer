# Propuesta de Cambio: Guard de Código Muerto en src/woptimizer/ (TASK-056)

## 1. Contexto y Diagnóstico
Una función o método puede estar formalmente testeado o pasar inadvertido en la base de código pero carecer de llamadores reales en el producto ("el fallo más caro y silencioso que hay", según documenta `mutation-auditor/agent.md:56`). Esto ocurrió históricamente en el proyecto con `get_gaming_pack()` (Ciclo #14) y con `should_kill_for_gaming()` (Ciclo #10), donde el código existía pero no estaba conectado a los puntos de entrada.

En este ciclo se identificaron y resolvieron los siguientes casos de código muerto o desconectado:
1. `_get_priority` en `src/woptimizer/services/process_service.py`: método legacy con 0 referencias. Eliminado.
2. `process_db` en `src/woptimizer/services/process_service.py`: propiedad obsoleta de compatibilidad v2 con 0 referencias. Eliminada.
3. `get_favorite_packs` en `src/woptimizer/services/pack_service.py`: método de servicio desconectado de la UI; `DashboardView` duplicaba manualmente su lógica mediante comprensión de listas. Conectado en `DashboardView.refresh_dashboard` y `_regrid_favorites`.
4. `is_wcag_aa` en `src/woptimizer/ui/theme.py`: helper de contraste sin referencias en la suite de tests. Incorporado con aserciones semánticas directas en `test_contrast_wcag_aa` de `run_tests.py`.
5. `_force_update_db`: verificado que está conectado al botón `btn_update_db` (TASK-051).

## 2. Invariantes y Diseño de la Guarda
- **Alcance Derivado del Árbol:** El detector recorre dinámicamente mediante `ast` todos los módulos `.py` bajo `src/woptimizer/**`, extrayendo las definiciones de funciones y métodos (`FunctionDef`, `AsyncFunctionDef`). No utiliza tuplas estáticas ni rutas cableadas a mano.
- **Conteo de Referencias:** Analiza todos los nodos `Name` y `Attribute` en `src/` y `run_tests.py`, comprobando que cada símbolo definido posee al menos una referencia real.
- **Lista Blanca Justificada:** Se define una lista de exclusión justificada para métodos mágicos (`__*__`), puntos de entrada estándar (`main`), métodos estáticos/decoradores pydantic si aplica, y callbacks nativos de Tkinter (`<Configure>`, eventos de foco o protocolos de ventana).
- **Test Discriminante #99:** `test_dead_code_ast_guard` en `run_tests.py` ejecuta este análisis de forma determinista en < 1 segundo, fallando si se introduce cualquier nueva función o método muerto.

## 3. Plan de Acción
1. Formalizar propuesta y tareas en OpenSpec.
2. Añadir Test #99 `test_dead_code_ast_guard` en `run_tests.py`.
3. Sincronizar recuento de 99 tests en `STATUS.md`, `AGENTS.md`, `README.md` y `docs/ai/testing-guide.md`.
4. Ejecutar validadores y auditoría de mutaciones (`mutation-auditor`).
5. Cerrar Ciclo #46.
