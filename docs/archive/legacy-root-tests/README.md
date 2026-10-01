# `docs/archive/legacy-root-tests/` — Scripts de prueba legacy retirados de la raíz (TASK-055)

Nada de lo que hay aquí se ejecuta. Es un **registro histórico**: ficheros de prueba con prefijo `test_*.py` que se encontraban en la raíz del repositorio y que se retiraron en **TASK-055 (Ciclo #45)** para sanear la raíz y evitar efectos secundarios o confusiones sobre el punto de entrada de la suite de pruebas.

> **Invariante de Preservación:** Se archivan y **no se borran**. La política del propietario establece que el código preexistente no se destruye sin más: se traslada a este archivo versionado con su contexto histórico documentado.

Fecha del retiro: **2026-10-01**. Especificación: `openspec/changes/2026-10-01-archive-legacy-root-tests/`.

---

## 1. Clasificación de los 11 Ficheros Archivados

Los 11 ficheros responden a dos naturalezas técnicas completamente distintas:

### Grupo A: 10 scripts muertos por importación inexistente (`process_manager`)
Los siguientes 10 scripts pertenecían a la arquitectura previa v2, donde existía un script monolítico `process_manager.py` en la raíz del repositorio:
1. `test_categorization.py`
2. `test_debug_list.py`
3. `test_gaming_profile.py`
4. `test_gaming_session.py`
5. `test_harness_v2.py`
6. `test_harness.py`
7. `test_kill_expansion.py`
8. `test_kill_real.py`
9. `test_profiles.py`
10. `test_relaunch_grouping.py`

**Motivo de retiro:**
- Al migrar a la arquitectura v3 modular (`src/woptimizer/` con separación en `services/`, `models.py` y `ui/`), `process_manager.py` fue eliminado.
- Intentar ejecutar cualquiera de estos 10 archivos fallaba de inmediato con:
  ```text
  ModuleNotFoundError: No module named 'process_manager'
  ```
- Toda su funcionalidad de prueba relevante fue absorbida, superada y formalizada en `run_tests.py`.

---

### Grupo B: 1 script vivo con efectos colaterales (`test_powershell_direct.py`)
El fichero `test_powershell_direct.py` representaba un caso particular crítico:
- **No importaba `process_manager`**, por lo que **no moría al importarse**.
- Era un script autónomo que ejecutaba llamadas reales al sistema:
  1. Lanzaba una ventana viva de `notepad.exe` mediante `subprocess.Popen(["notepad.exe"], creationflags=0x08000000)`.
  2. Ejecutaba un script de PowerShell crudo (`Get-CimInstance Win32_Process`) para consultar la lista de procesos.
  3. Ejecutaba `taskkill /F /PID <pid>` para terminar el proceso de Notepad.

**Motivo de retiro:**
- `woptimizer` migró en el Ciclo #1 de PowerShell/WMI a llamadas en C ultra-rápidas mediante `psutil` (<5 ms).
- Invocar PowerShell crudo y abrir procesos de usuario (Notepad) en segundo plano violaba los invariantes de pruebas headless y representaba un riesgo de efecto colateral si se ejecutaba por error.

---

## 2. La Suite Oficial Única: `run_tests.py`

La única suite oficial y activa del proyecto es `run_tests.py`:
- 100% de pruebas en modo headless (cero ventanas persistentes, cero subprocesos interactivos huérfanos).
- Cobertura exhaustiva de modelos Pydantic, servicios (`ProcessService`, `PackService`, `GamingService`, `NotificationService`), navegación y widgets UI (`Confirmable`, `DoubleTapGuard`).
- El guard anti-regresión `test_no_legacy_test_files_in_root` en `run_tests.py` asegura que ningún fichero `test_*.py` vuelva a ubicarse en la raíz del repositorio.
