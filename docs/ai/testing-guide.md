# Guía de Pruebas y Validación para Agentes IA

## Desafío en Entornos Headless
En muchos entornos de IA no existe un monitor o display activo de Windows conectado directamente al proceso del agente. Si un script ejecuta `app.mainloop()` de CustomTkinter, el script se quedará bloqueado de forma indefinida esperando interacción humana.

## Patrones de Prueba Obligatorios

### 1. Validación Estática de Sintaxis e Imports (`py_compile`)
Antes de dar por terminada cualquier edición de UI o servicios, compilar los archivos a bytecode:
```python
import py_compile
py_compile.compile('src/woptimizer/ui/app.py', doraise=True)
py_compile.compile('src/woptimizer/models.py', doraise=True)
```

### 2. Prueba de Inicialización Headless de la UI
Para verificar que los widgets cargan y los componentes se instancian sin errores de runtime:
```python
app = WOptimizerApp(process_service, pack_service, gaming_service)
# Programar cierre automático tras 1000ms para no bloquear la consola
app.root.after(1000, app.root.destroy)
app.run()
```

### 3. Pruebas Unitarias de Backend
Probar `process_service` y `pack_service` con tests independientes en `run_tests.py` sin levantar Tkinter.

## Suite de Tests Actual (`run_tests.py`)
Ejecutar con `python run_tests.py` (PowerShell: `$env:PYTHONIOENCODING="utf-8"`). Contiene **20 tests**: 19 de backend + 1 headless de UI.

| # | Test | Qué valida |
|---|------|-----------|
| 1 | `test_models` | Instanciación de `ProcessInfo`, `Pack`, `AppData` y valores por defecto Pydantic |
| 2 | `test_process_service_signatures` | `kill_processes` y `kill_pack_apps` retornan 4-tupla `(killed, failed, skipped, freed_mb)` |
| 3 | `test_freed_mb_return_type` | `freed_mb` es `float >= 0.0` en todos los casos (vacío, inexistente) |
| 4 | `test_gaming_pack_protected` | `delete_pack("gaming")` lanza `ValueError` — invariante de pack protegido |
| 5 | `test_corrupted_json_recovery` | JSON corrupto → auto-recovery con pack gaming restaurado |
| 6 | `test_notification_without_tray_degrades` | Sin bandeja: `notify()` retorna `False` y no lanza; contadores de descartes |
| 7 | `test_notification_attach_detach` | `attach_tray` habilita, `detach_tray` deshabilita y es idempotente |
| 8 | `test_notification_never_raises` | Un backend que explota se degrada a log, nunca rompe la UI |
| 9 | `test_notification_message_formatting` | Helpers en español con plurales correctos y MB condicionales |
| 10 | `test_category_emoji_alignment` | Toda categoría de `assets/process_db.json` existe literalmente en `config.py` |
| 11 | `test_safety_badge_category_priority_order` | La categoría manda sobre la prioridad en `get_safety_badge` (regresión 🟡/🔴) |
| 12 | `test_gaming_service_should_kill` | Orden de reglas de `should_kill_for_gaming`: keeper > apps > categoría objetivo |
| 13 | `test_pack_service_crud` | `create_user_pack` rechaza duplicados y el id reservado `gaming`; persiste en disco |
| 14 | `test_pack_service_delete` | `delete_pack`: `ValueError` en gaming, `False` si no existe, `True` en pack propio |
| 15 | `test_pack_service_favorite_exclusive` | `set_favorite` deja como máximo 1 favorito; `set_favorite(None)` deja 0 |
| 16 | `test_pack_service_reset_gaming` | `reset_gaming_pack` restaura apps y `target_categories` de `DEFAULT_GAMING_PACK` |
| 17 | `test_gaming_pack_lists_isolated_from_global` | Las listas del pack gaming **no** comparten objeto con `DEFAULT_GAMING_PACK` (regresión de `model_copy()` shallow) |
| 18 | `test_cache_ttl_and_invalidation` | Dentro del TTL se devuelve el **mismo objeto**; `invalidate_cache()` y `force_refresh=True` re-escanean |
| 19 | `test_kill_recursive` | Kill recursivo: el nieto Python muere junto al padre (invariante de AGENTS.md) |
| 20 | `test_headless_ui` | UI completa se instancia y destruye en 1.5 s sin errores de runtime |

### Notas de Aislamiento
- Los tests de `PackService` usan `tempfile.NamedTemporaryFile` (helper `_pack_service_temporal()`) para no modificar `profiles.json` real.
- Los tests de `ProcessService` operan contra listas vacías o nombres inexistentes.
- `test_kill_recursive` espawnea solo procesos Python propios y los limpia siempre en un `finally`; si el entorno bloquea subprocesos o el kill está protegido por permisos, degrada con un `print` en vez de reventar la suite.
- El test headless requiere un display Windows (falla en CI headless puro).
- Los `print()` deben quedar en **ASCII puro**: la consola de PowerShell es `cp1252` y revienta con `UnicodeEncodeError`. Para mencionar un emoji usa escapes (`\U0001F7E1`), nunca el carácter literal dentro de un `print()`.

## Deuda técnica: tests heredados v2
En la raíz del repo conviven **11 ficheros `test_*.py` heredados** que están **muertos**:

`test_categorization.py`, `test_debug_list.py`, `test_gaming_profile.py`, `test_gaming_session.py`, `test_harness.py`, `test_harness_v2.py`, `test_kill_expansion.py`, `test_kill_real.py`, `test_powershell_direct.py`, `test_profiles.py`, `test_relaunch_grouping.py`.

- Los 11 hacen `import process_manager as pm` a nivel de módulo. `process_manager` es un módulo de la **v2** que ya no existe en `src/woptimizer/`, así que todos fallan con `ModuleNotFoundError` en la línea de import, antes de ejecutar un solo test.
- La suite actual usa `services/process_service.py` (psutil) y `services/pack_service.py`; no hay equivalente de `process_manager` en v3. Existe `ui/views/process_manager_view.py`, pero es una vista de UI y no el módulo que esos tests necesitan.
- **No se borran por decisión expresa del propietario**: son referencia histórica y retirarlos no aporta valor frente al riesgo de perder contexto.
- **No se ejecutan** y **no se modifican**. No forman parte de la CI ni de la verificación de calidad.
- **No cuentan como cobertura.** La cobertura real y viva del proyecto vive **únicamente en `run_tests.py`**.

Consecuencia práctica: al añadir cobertura, **editar siempre `run_tests.py`**. Un `test_*.py` nuevo en la raíz no se ejecutará y dará una falsa sensación de cobertura.

