# Cuadro de Mando: Motor Autónomo de I+D (woptimizer)

> Estado general del pipeline continuo de Investigación y Desarrollo. Actualizado automáticamente al finalizar cada ciclo.

---

## 🟢 Salud General del Sistema
- **Sintaxis Estática UI:** 🟢 Pasa al 100% (`verify_ui_syntax.py`, 7 módulos)
- **Suite de Tests Headless:** 🟢 Pasa al 100% (`run_tests.py`, **21 tests**: 20 backend + 1 headless UI)
- **Micro-Benchmark Base:** 182 ms (Init) | 16.4 ms (Escaneo 326 procs) | 0.003 ms (lectura cacheada) | 30 MB (RAM RSS)
- **Compilación PyInstaller:** 🟢 Listo y **al día** (`dist/woptimizer.exe`, 25.65 MB, incluye los fixes de los ciclos #9, #10 y #11)
- **Base de Datos de Procesos:** 48 entradas | 8 categorías | 0 categorías huérfanas
- **Versionado:** 🟢 El repo desacoplado en `%LOCALAPPDATA%\woptimizer_git\.git` está sano. **El `.git` dentro del árbol de trabajo está corrupto por el VFS de Nextcloud** — nunca uses `git` a pelo, solo `git_safe_commit.py`.

---

## 🔄 Estado de la Ejecución Perpetua
- **Modo:** 🟢 ACTIVO — Bucle Infinito de I+D en marcha.
- **Ciclos Completados:** 11 (`rd_journal.json` actualizado).
- **Ciclo Actual #12:** Listo para Paso 1 — Descubrimiento autónomo.
- **Última Acción:** Ciclo #11 TASK-022 — commits `6048f6f` y `b9a31fa`.

---

## 📋 Resumen de los Últimos Hitos Concluidos
1. **[Ciclo #1 - Arquitectura & UI]:** Rediseño completo de las 3 ventanas con CustomTkinter (Portada, Packs, Procesos), migración de backend a `psutil` y persistencia con `pydantic v2`.
2. **[Ciclo #2 - Resiliencia & UX v3.1]:** Integración de System Tray en background (`pystray`), rotación segura de copias de respaldo `profiles.json.bak` y logging continuo en `woptimizer.log`.
3. **[Ciclo #3 - Gaming & Telemetría UX]:** Banner dinámico en DashboardView que muestra procesos cerrados y MB liberados al activar packs.
4. **[Ciclo #4 - Base de Datos & Procesos]:** 4 procesos nuevos en `process_db.json` (34 total): sharex, crossdeviceservice, esrv_svc, dsaservice.
5. **[Ciclo #5 - Testing & Calidad]:** 3 tests nuevos en `run_tests.py` (7 total): freed_mb, gaming pack protegido, JSON recovery.
6. **[Ciclo #6 - Resiliencia & Robustez]:** Fix tray_icon ref para cierre limpio, gaming_action con logging, start_pack_apps con logging individual.
7. **[Ciclo #7 - Rendimiento & Latencia]:** Hashmap O(1) + meta-cache + TTL 2s en ProcessService. Lectura cacheada 0.003 ms (~5000x).
8. **[Ciclo #8 - Gaming & Telemetría UX]:** `NotificationService` con toasts nativos de Windows vía `pystray.Icon.notify()`. 4 tests nuevos. `pystray` y `Pillow` declarados en `pyproject.toml`. Smoke test de build OK.
9. **[Ciclo #9 - Base de Datos & Procesos]:** 🔴 **Bug crítico corregido** — 6 de 8 categorías del JSON no existían en `config.py` por emojis invertidos, dejando todos esos procesos en "? Otros" sin semáforo. Segundo bug en `get_safety_badge`: la prioridad se evaluaba antes que la categoría. +14 procesos (navegadores, launchers, IA) = 48 total. 2 tests de regresión.
10. **[Ciclo #10 - Testing & Calidad]:** 🔴 **Segundo bug real corregido** — `model_copy()` de Pydantic v2 es *shallow*, así que las listas del pack Gaming se compartían con el global `DEFAULT_GAMING_PACK`. La UI muta in situ (`on_add_to_pack`), contaminando el global y volviendo **"Restaurar por defecto" un no-op silencioso**. Fix: `model_copy(deep=True)`. +8 tests para invariantes sin cobertura tras la migración v2→v3: `GamingService.should_kill_for_gaming`, CRUD de `PackService`, cache TTL y kill recursivo.
11. **[Ciclo #11 - Resiliencia & Robustez]:** 🔴 **El pipeline podía "completar" ciclos sin versionar nada** — `git_safe_commit.py`, la única puerta de versionado, salía con **código 0 ante cualquier fallo de commit**. El CHANGELOG MANDATORY registraba hashes que podían no existir y `validate_docs.py` no podía detectarlo. Rehecho con contrato de 4 códigos de salida y líneas canónicas `WOPT_*`, validación real del repo (sin fallback al `.git` corrupto del VFS) y flag `--verify`. El arquitecto corrigió 3 errores de la propuesta, el más grave: decidir "nada que comitear" buscando `"nothing to commit"` depende de `LANG` y **en un Windows en español ese texto nunca aparece**, lo que habría convertido un árbol limpio en un fallo → ahora se decide con `git diff --cached --quiet`. Checkpoint de empaquetado cerrado: `dist/woptimizer.exe` regenerado (25.65 MB) con los fixes de los ciclos #9 y #10.

---

## 🗂️ Rotación de Áreas (Matriz ID)
| # | Área | Último ciclo | Subagente |
|---|------|:---:|---|
| 1 | Resiliencia & Robustez | **#11** | `openspec-dev` |
| 2 | Gaming & Telemetría UX | #8 | `openspec-dev` |
| 3 | Base de Datos & Procesos | #9 | `process-db-updater` |
| 4 | Rendimiento & Latencia | #7 | `openspec-dev` |
| 5 | Testing & Calidad | #10 | `openspec-dev` |

> **Siguiente en rotación:** Área 2 (Gaming & Telemetría UX) — la más rezagada, sin tocar desde el ciclo #8. Candidatos: auto-restauración inteligente de apps al cerrar juegos, atajos globales (`Ctrl+Alt+G`), contador de RAM/CPU liberada en la Portada.

---

## 📌 Checkpoints Periódicos
- ✅ **Smoke test de compilación:** ejecutado en ciclo #11 (checkpoint de 3 ciclos desde el #8). Próximo tras el ciclo #14 o al añadir dependencias.
- ✅ **`dist/woptimizer.exe` al día:** regenerado en el ciclo #11, incluye los fixes de los ciclos #9, #10 y #11.

---

## ⚠️ Deuda Técnica Conocida
- **11 ficheros `test_*.py` heredados en la raíz están MUERTOS:** hacen `import process_manager` (módulo de la v2 que ya no existe) y mueren en el import. **No se borran por decisión del propietario.** La cobertura viva vive **únicamente en `run_tests.py`**. Detallado en `docs/ai/testing-guide.md`.
- **`.git` del árbol de trabajo corrupto (VFS de Nextcloud):** el historial vive desacoplado en `%LOCALAPPDATA%\woptimizer_git\.git`. No es reparable desde el árbol de trabajo; se acepta y se blinda con `git_safe_commit.py` y su flag `--verify` (ver la sección nueva de `docs/ai/sandbox-rules.md`).

