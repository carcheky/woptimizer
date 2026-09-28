# Plan de Inconsistencias (woptimizer v3) - Análisis Final Post-Implementación (100% Completado)

Tras haber completado exhaustivamente todas las tareas del plan (`openspec` y `.taskmaster`), incluyendo la programación completa de la UI (añadir/quitar apps de packs), tests y binarios, estas son las inconsistencias y deudas técnicas identificadas en la base del proyecto final:

## 1. Contaminación del Repositorio (Git)
- **Falta de `.gitignore`:** El ejecutable `dist/woptimizer.exe`, la carpeta `build/` y el archivo `woptimizer.spec` se han generado y se están incluyendo en el control de versiones (o corren el riesgo de serlo), lo que engordará el repositorio con binarios y basura generada de PyInstaller.
- **Residuos de PyInstaller:** El script `force_build.py` utiliza la flag `--clean`, pero esto solo limpia la caché interna de Pyinstaller; no borra `woptimizer.spec` ni el directorio `build/` al terminar, dejando el *working directory* sucio tras la compilación.

## 2. Inconsistencias de Servicios (Acoplamiento de Strings)
- **Reglas Hardcodeadas en `GamingService`:** El método `should_kill_for_gaming` verifica explícitamente el string `'🟡 Chat y Comunicación'`. Dado que ahora tenemos un sistema asíncrono con `fallback.csv` para las categorías de procesos, si en el futuro se modifica la categoría (ej. se quita el emoji o se renombra a `Chat`), la regla de gaming fallará silenciosamente. Debería depender exclusivamente de la propiedad `priority` del modelo `ProcessInfo`.

## Recomendaciones para el Próximo Plan
1. Crear un archivo `.gitignore` estricto en la raíz del proyecto y eliminar `dist/` de la historia si ha sido commiteado por error.
2. Añadir sentencias `os.remove` y `shutil.rmtree` al final de `force_build.py` para limpiar la basura de compilación.
3. Refactorizar `GamingService` para usar invariantes estructurales en lugar de strings de texto exactos para las categorías.
