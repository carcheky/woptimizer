# Tasks for v3-rewrite-phase2

## 1. Crear estructura y configuración base
- [ ] Crear directorio `src/woptimizer/` y subdirectorios
- [ ] Crear `src/woptimizer/config.py` con constantes y `_app_dir()`
- [ ] Crear `src/woptimizer/models.py` (Pydantic models)
- [ ] Actualizar imports en tests para que apunten al nuevo `config` y `models`

## 2. Process Service (`psutil`)
- [ ] Instalar `psutil`
- [ ] Crear `src/woptimizer/services/process_service.py`
- [ ] Implementar `get_running_processes()` con `psutil.process_iter()`
- [ ] Implementar `kill_processes()` con `psutil.Process.kill()`
- [ ] Testear y verificar que `test_kill_real.py` funciona con el nuevo servicio

## 3. Profile & Gaming Services
- [ ] Instalar `pydantic`
- [ ] Crear `src/woptimizer/services/profile_service.py`
- [ ] Crear `src/woptimizer/services/gaming_service.py`
- [ ] Refactorizar carga/guardado de perfiles
- [ ] Verificar que `test_profiles.py` y `test_gaming_profile.py` pasan correctamente

## 4. Conexión y Limpieza
- [ ] Modificar `process_manager.py` (App UI) para consumir los nuevos `services` en lugar de funciones locales
- [ ] Eliminar las funciones antiguas de `process_manager.py`
- [ ] Ejecutar todos los tests unitarios
