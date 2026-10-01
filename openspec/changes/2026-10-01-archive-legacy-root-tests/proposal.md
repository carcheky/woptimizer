# Propuesta de Cambio: Archivo de tests legacy de la raíz y guard anti-regresión

## 1. Contexto y Diagnóstico
En la raíz del repositorio de `woptimizer` persisten 11 archivos de pruebas con prefijo `test_*.py` procedentes de la arquitectura v2 previa:
1. **10 scripts muertos por import:** `test_categorization.py`, `test_debug_list.py`, `test_gaming_profile.py`, `test_gaming_session.py`, `test_harness_v2.py`, `test_harness.py`, `test_kill_expansion.py`, `test_kill_real.py`, `test_profiles.py`, `test_relaunch_grouping.py`. Todos ellos contienen `import process_manager`, módulo monolítico eliminado durante la reescritura v3 hacia `src/woptimizer/`.
2. **1 script vivo con efectos colaterales destructivos:** `test_powershell_direct.py` no importa `process_manager`; es un script standalone que invoca `subprocess.Popen(["notepad.exe"])`, ejecuta consultas CIM de PowerShell y dispara `taskkill /F`. Su ejecución accidental abre Notepad en la sesión activa del usuario.

## 2. Invariantes y Decisiones del Propietario
- **Invariante de Preservación:** Ningún archivo se elimina del repositorio. Todo el código histórico se mueve a la carpeta de archivo versionado `docs/archive/legacy-root-tests/`.
- **Documentación de Registro:** La carpeta archivada contiene un `README.md` exhaustivo que categoriza los 11 archivos y documenta el riesgo específico de `test_powershell_direct.py`.
- **Suite Única:** `run_tests.py` es y debe seguir siendo la única suite de pruebas headless oficial del proyecto.
- **Guard Anti-Regresión:** Se incorpora en `run_tests.py` una aserción estricta que prohíbe la presencia de cualquier archivo `test_*.py` en la raíz del repositorio (con excepción de `run_tests.py`).

## 3. Plan de Acción
1. Crear el directorio `docs/archive/legacy-root-tests/`.
2. Mover los 11 archivos `test_*.py` de la raíz hacia `docs/archive/legacy-root-tests/`.
3. Redactar `docs/archive/legacy-root-tests/README.md`.
4. Añadir test #98 en `run_tests.py` (`test_no_legacy_test_files_in_root()`).
5. Sincronizar recuento de 98 tests en `STATUS.md`, `AGENTS.md`, `README.md` y `docs/ai/testing-guide.md`.
6. Auditar con `mutation-auditor` y verificar 100% PASS.
