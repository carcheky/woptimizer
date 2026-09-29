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
Ejecutar con `python run_tests.py`. Contiene 7 tests:

| # | Test | Qué valida |
|---|------|-----------|
| 1 | `test_models` | Instanciación de `ProcessInfo`, `Pack`, `AppData` y valores por defecto Pydantic |
| 2 | `test_process_service_signatures` | `kill_processes` y `kill_pack_apps` retornan 4-tupla `(killed, failed, skipped, freed_mb)` |
| 3 | `test_freed_mb_return_type` | `freed_mb` es `float >= 0.0` en todos los casos (vacío, inexistente) |
| 4 | `test_gaming_pack_protected` | `delete_pack("gaming")` lanza `ValueError` — invariante de pack protegido |
| 5 | `test_corrupted_json_recovery` | JSON corrupto → auto-recovery con pack gaming restaurado |
| 6 | `test_headless_ui` | UI completa se instancia y destruye en 1.5 s sin errores de runtime |

### Notas de Aislamiento
- Los tests de `PackService` usan `tempfile.NamedTemporaryFile` para no modificar `profiles.json` real.
- Los tests de `ProcessService` operan contra listas vacías o nombres inexistentes.
- El test headless requiere un display Windows (falla en CI headless puro).
