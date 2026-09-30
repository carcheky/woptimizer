# Cuadro de Mando: Motor Autónomo de I+D (woptimizer)

> Estado general del pipeline continuo de Investigación y Desarrollo. Actualizado automáticamente al finalizar cada ciclo.

---

## 🟢 Salud General del Sistema
- **Sintaxis Estática UI:** 🟢 Pasa al 100% (`verify_ui_syntax.py`, 8 módulos)
- **Suite de Tests Headless:** 🟢 Pasa al 100% (`run_tests.py`, **57 tests**: 56 backend + 1 headless UI)
- **Micro-Benchmark Base:** 182 ms (Init) | 16.4 ms (Escaneo 326 procs) | 0.003 ms (lectura cacheada) | 30 MB (RAM RSS)
- **Compilación PyInstaller:** 🟡 Al día con el ciclo #11, **pendiente de regenerar** (no incluye los fixes de los ciclos #12, #13 y #14)
- **Base de Datos de Procesos:** 73 entradas | 8 categorías | 0 categorías huérfanas | 🛡️ blindaje anti-brick activo (34 procesos de sistema, 0 cerrables)
- **Versionado:** ⚠️ **Ciclos #14 a #20 SIN COMMIT.** El shell del entorno falló con `spawn EPERM` de forma intermitente y `git_safe_commit.py` requiere `subprocess`. El árbol tiene cambios pendientes de versionar.

---

### 🔄 Estado de la Ejecución Perpetua
- **Modo:** 🟢 ACTIVO — Bucle Infinito de I+D en marcha.
- **Ciclos Completados:** 21 (`rd_journal.json` actualizado).
- **Ciclo Actual #22:** Paso 1 — la tarea activa es `TASK-029` (sistema de diseño y refresco visual del front).
- **Última Acción:** Ciclo #21 TASK-028 — saneamiento de deuda técnica (logging, versión, archivo legacy, F1). **57 tests backend + 1 UI en verde, Paso 4 = PASS.**

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
10: 10. **[Ciclo #10 - Testing & Calidad]:** 🔴 **Segundo bug real corregido** — `model_copy()` de Pydantic v2 es *shallow*, así que las listas del pack Gaming se compartían con el global `DEFAULT_GAMING_PACK`. La UI muta in situ (`on_add_to_pack`), contaminando el global y volviendo **"Restaurar por defecto" un no-op silencioso**. Fix: `model_copy(deep=True)`. +8 tests para invariantes sin cobertura tras la migración v2→v3: `GamingService.should_kill_for_gaming`, CRUD de `PackService`, cache TTL y kill recursivo.
11. **[Ciclo #11 - Resiliencia & Robustez]:** 🔴 **El pipeline podía "completar" ciclos sin versionar nada** — `git_safe_commit.py`, la única puerta de versionado, salía con **código 0 ante cualquier fallo de commit**. El CHANGELOG MANDATORY registraba hashes que podían no existir y `validate_docs.py` no podía detectarlo. Rehecho con contrato de 4 códigos de salida y líneas canónicas `WOPT_*`, validación real del repo (sin fallback al `.git` corrupto del VFS) y flag `--verify`. El arquitecto corrigió 3 errores de la propuesta, el más grave: decidir "nada que comitear" buscando `"nothing to commit"` depende de `LANG` y **en un Windows en español ese texto nunca aparece**, lo que habría convertido un árbol limpio en un fallo → ahora se decide con `git diff --cached --quiet`. Checkpoint de empaquetado cerrado: `dist/woptimizer.exe` regenerado (25.65 MB) con los fixes de los ciclos #9 y #10.
12. **[Ciclo #12 - Gaming & Telemetría UX]:** 🔴 **Regresión silenciosa de la reescritura v2→v3** — el patrón de doble pulsación para acciones destructivas (nacido de un incidente real: un `messagebox` que se abría *detrás* de la ventana) se perdió al reescribir, y **5 acciones destructivas quedaron sin confirmar nada**. La grave: "Cerrar Seleccionados" mata N procesos de un solo clic, agravada porque `refresh_dashboard` coloca los packs de dos en dos en la misma fila, así que el botón Gaming tenía un pack vecino pegado. Implementado **en un solo sitio**: `ui/confirmation.py` con `DoubleTapGuard` (máquina de estado pura, testeable headless) y `Confirmable` (mixin). `PackManagerView` recibió su `status_label`, que no tenía. Documentada la **Trampa #14**, que cierra la laguna #13 → #14.
13. **[Ciclo #13 - Base de Datos & Procesos]:** 🛡️ **Blindaje anti-brick** — el escaneo real encontró 122 procesos sin registrar de 131. Se clasificaron en tres familias: los de sistema (prohibidos), el bloatware real (**+25 entradas**, 48 → 73: PowerToys, Armoury Crate, language servers, audio) y los del usuario (fuera). Añadido `SYSTEM_PROTECTED_PROCESSES` (34 nombres) aplicado por **tres vías**: al cargar la DB, al resolver metadatos, y en el propio kill —porque un `lsass.exe` escrito a mano en un pack también debe ser indestructible—. **Verificado: 0 procesos de sistema registrados como cerrables.**
14. **[Ciclo #14 - Gaming & Telemetría UX]:** 🔴 **La configuración central del producto estaba desconectada** — `GamingService.should_kill_for_gaming()` existía y estaba testeado desde el ciclo #10, pero **nunca se invocó**: las 3 rutas de Gaming Mode solo llamaban a `kill_pack_apps(pack.apps)`, así que `keepers` y `target_categories` eran decorativos. La raíz era doble: `MainWindow` guardaba el servicio y **no se lo pasaba a las vistas**. Lo grave lo encontró la planificación: el guard heredado por blacklist de nombres **no protege** una evaluación por categoría, porque `svchost`/`explorer` no están en el blacklist y su categoría 🔴 era una casilla activable — marcarla cerraba todos los `svchost.exe` y dejaba Windows inservible. Implementada `execute_gaming_pack()` como **única puerta de kill** en `services/`, con **barrera de categoría roja** en dos capas, y corregido el fallo silencioso que habría desactivado los keepers (se comparaba contra el nombre sin extensión). Test **probado por mutación**: sin la barrera, `svchost` llega a `kill_processes`. 24 tests en verde.
15. **[Ciclo #15 - Resiliencia & Robustez]:** 🔴 **Un error al guardar borraba toda la configuración del usuario** — `load()` ante un JSON corrupto sustituía el archivo por un pack vacío, y el `except (json.JSONDecodeError, Exception)` era en realidad `except Exception`, así que un `PermissionError` tomaba la misma ruta destructiva. **La documentación afirmaba que el backup existía desde el ciclo #2: nunca existió.** Implementados backup preventivo con recuperación desde `.bak`, `OSError` propagado, rotación que no pisa un backup sano, y escritura atómica. Además se cerró una race condition en `ProcessManagerView._do_load` (mutaba desde el hilo secundario mientras la ventana recorría el dict → `RuntimeError` y sets de PIDs desfasados) y se alineó el centinela `⚪ Otros` que usaba `?` ASCII en 3 sitios, uno de ellos un filtro de UI que no filtraba nada. **Dos de las cuatro premisas de la tarea resultaron falsas** (ver nota de proceso en el changelog). 28 tests en verde, los 4 verificados por mutación.
16. **[Ciclo #16 - Pipeline]:** 🔧 **Los tres roles del pipeline pasaron de skills a agentes reales** (`architect-review`, `openspec-dev`, `process-db-updater`), así que aparecen en el panel del runtime y se delegan con `task` en vez de que el orquestador traduzca sus directrices a mano. La causa de que el propietario no los viera: `.agents/skills/` y el panel de agentes son **mecanismos distintos**, y la skill además pedía `invoke_subagent`, un mecanismo ya inexistente que rompía la primera invocación. Reparadas 5 referencias a `tm.py` (no ejecutable en este entorno) y la matriz de modelos, que pedía valores no soportados. Cerrados **dos falsos verdes del propio validador** introducidos en este y el ciclo anterior, y una regresión mía: al renombrar la sección de roles de `AGENTS.md`, el validador —que buscaba el encabezado por nombre literal— pasó a dar FAIL. Sin cambios en `src/`.
17. **[Ciclo #17 - Pipeline]:** 🧬 **El bucle pasa de 3 a 4 pasos: alguien rompe el código a propósito para ver si los tests se enteran.** `run_tests.py` en verde dice que el código hace lo que el test comprueba, **no** que el test compruebe algo — la cobertura mide ejecución, no verificación. Nuevo agente `mutation-auditor` con una tabla de 12 mutaciones canónicas de este repo, que trabaja solo sobre copias y tiene prohibido reparar lo que encuentra. **Su primer arranque devolvió FAIL**: encontró 3 tests de los ciclos 14-15 que pasan con el bug puesto, incluido el de escritura atómica (mira que exista un `.tmp`, así que si la atomicidad desaparece y el `.tmp` nunca se crea, el assert sigue verde) y el de errores de permisos (acepta igual "no intentó guardar" que "intentó y falló"). También reparadas 5 referencias a `tm.py` en `AGENTS.md` que mandaban usar un comando no funcional. Sin cambios en `src/`.
18. **[Ciclo #21 - Resiliencia & Deuda Técnica]:** 🧹 **Saneamiento de deuda técnica (TASK-028, FIX-010 al FIX-020)** — `setup_logging` explícito con `force=True` y rotación de archivo sin ensuciar stderr; sincronización de versión `3.0.1.dev0` con test AST; perfiles legacy v2 archivados en `docs/archive/legacy-root-data/` con README; limpias redundancias en `quit_app` e `is_expanded`. 57 tests backend + 1 UI en verde y mutaciones auditadas con PASS.

---

## 🗂️ Rotación de Áreas (Matriz ID)
| # | Área | Último ciclo | Subagente |
|---|------|:---:|---|
| 1 | Resiliencia & Robustez | **#21** | `openspec-dev` |
| 2 | Gaming & Telemetría UX | #20 | `openspec-dev` |
| 3 | Base de Datos & Procesos | #13 | `process-db-updater` |
| 4 | Rendimiento & Latencia | #7 | `openspec-dev` |
| 5 | Testing & Calidad | #10 | `openspec-dev` |

> **Tarea activa: `TASK-029`** (sistema de diseño y refresco visual del front). Es la última tarea pendiente del backlog de la auditoría `bugfix-audit-v3` y tiene prioridad sobre la rotación. `TASK-025`, `TASK-026`, `TASK-027` y `TASK-028` están cerrados.

---

## 📌 Checkpoints Periódicos
- ⏳ **Smoke test de compilación:** próximo tras el ciclo #14 (ya han pasado 3 desde el #11). `dist/woptimizer.exe` **no** incluye aún los fixes de los ciclos #12, #13 y #14.
- ⚠️ **Commits pendientes de los ciclos #14 a #20:** el shell del entorno dio `spawn EPERM` intermitente y el versionado no pudo ejecutarse.

---

## ⚠️ Deuda Técnica Conocida
- **11 ficheros `test_*.py` heredados en la raíz están MUERTOS:** hacen `import process_manager` (módulo de la v2 que ya no existe) y mueren en el import. **No se borran por decisión del propietario.** La cobertura viva vive **únicamente en `run_tests.py`**. Detallado en `docs/ai/testing-guide.md`.
- **`.git` del árbol de trabajo corrupto (VFS de Nextcloud):** el historial vive desacoplado en `%LOCALAPPDATA%\woptimizer_git\.git`. No es reparable desde el árbol de trabajo; se acepta y se blinda con `git_safe_commit.py` y su flag `--verify` (ver la sección nueva de `docs/ai/sandbox-rules.md`).
- **Shell intermitente en el entorno de agentes:** `spawn EPERM` en el envoltorio de Node bloquea la mayoría de invocaciones de shell, incluidos `tm.py` y `git_safe_commit.py`. Los subagentes pueden reintentar hasta conseguir ejecutar; el orquestador no tiene Bash utilizable. Afecta al versionado, no al producto.
- **Sin commit desde el ciclo #14:** los ciclos #14 a #20 están en disco pero sin versionar, por el bloqueo de shell anterior. Hay que ejecutar `python .taskmaster/git_safe_commit.py "<mensaje>"` en cuanto el entorno lo permita.
- **`CORRUPTION_ERRORS` no cubre `AttributeError`:** 3 de 7 formas de `profiles.json` malformado propagan y tumban el arranque. No hay pérdida de datos (no se escribe nada), pero contradice el docstring de `load()`. **Cerrado en el ciclo #18** (guarda de forma con `PerfilCorruptoError`).
- **El validador no comprueba la tabla resumen ni la sección `Models`** de cada entrada del changelog: son responsabilidad del orquestador y no están automatizadas. Si `rd_journal.json` falta, está corrupto o no aporta ciclos, el ancla **falla con mensaje explícito** (no verde silencioso) — cerrado en el ciclo #16. Aun así, un `0 FAIL` solo prueba que pasaron las comprobaciones que existen, no que el changelog esté al día.
- **🧬 3 SUPERVIVIENTES ABIERTOS (ciclo #17):** tests que pasan con el bug puesto, encontrados rompiendo el código a propósito. **No son deuda aceptada: son integridad de datos sin verificar.** (a) El test de escritura atómica solo mira que exista un `.tmp`, así que si la atomicidad desaparece y el `.tmp` nunca se crea, el assert sigue verde por la razón equivocada — falta probar que el principal queda intacto si el guardado se corta a mitad. (b) `except OSError: pass` acepta igual "no intentó guardar" que "intentó y falló" — un mutante que reintroduce `OSError` sobrevive con 28/28 verdes. (c) `CORRUPTION_ERRORS` no cubre `ValidationError`, `TypeError` ni `UnicodeDecodeError`, y los tres tumban `PackService()`. Resuelto en el ciclo #18; la ceguidad de las HOJAS es `TASK-031`.
- **`docs/api.md` y `docs/index.md` documentan una API de la v2** (`is_admin()`, `taskkill`, auto-elevación) que ya no existe en el código. No son documentos de arranque, pero están desfasados.

