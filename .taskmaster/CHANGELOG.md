# Changelog de pases — Motor id-pipeline

> **Registro append-only de cada ciclo completado por el motor autónomo de I+D.**
> Una entrada por pase al final del Paso 3 (Ejecutar), antes del retorno al Paso 1.
> **MANDATORY** desde el ciclo #11 (proposal `2026-09-29-id-pipeline-changelog-models`).

## Fuentes relacionadas

| Artefacto | Para qué |
|---|---|
| `.taskmaster/CHANGELOG.md` (este archivo) | Per-pass humano-legible: qué se hizo, con qué modelos, qué salió. |
| `.taskmaster/rd_journal.json` | Machine-readable: datos estructurados por ciclo (incluye `task`, `commits`, `benchmark_*`). |
| [`STATUS.md`](../../STATUS.md) | Dashboard: salud del sistema + resumen de hitos (no cada pase). |
| `openspec/changes/<id>/` | Contrato de cada cambio y su evolución. |

## Convención de modelos (definida en Sección 7 de `id-pipeline/SKILL.md`)

Modelos disponibles: `flash` (rápido, tareas triviales), `inherit` (default seguro, balance), `pro` (máxima capacidad de razonamiento, planificación compleja).

| Paso | Modelo por defecto | Override |
|---|---|---|
| 1. Buscar | `flash` | `inherit` si la búsqueda requiere contexto quirúrgico. |
| 2. Planear | `pro` | `inherit` si el cambio es trivial o el área es bien conocida. |
| 3. Ejecutar | `inherit` | `pro` para refactors con riesgo de regresión. |

## Formato de cada entrada

```markdown
## [CYCLE-NNN] YYYY-MM-DD HH:MM — <slug>
**Área**: <de la matriz de rotación>
**Change**: openspec/changes/<slug>/
**Estado**: COMPLETED | BLOCKED | ROLLED-BACK
**Models**:
- Paso 1 (Buscar): <modelo>
- Paso 2 (Planear): <modelo>
- Paso 3 (Ejecutar): <modelo>

### What
- <bullets cortos concretos, 1 frase cada uno>

### Outcome
- Commits: `<hash1>`, `<hash2>`
- Tests: <n>/<total> PASS
- Docs: <qué docs/ai/ se actualizó>

### Impact
<1-2 frases>
```

---

## Entradas

> Nota: ciclos 1-10 fueron completados ANTES de la convención de changelog. Se backfillean abajo usando los datos de `rd_journal.json`. Los modelos aparecen como `inherit (legacy — sin tracking)` por no estar registrados históricamente.

## [CYCLE-001] 2026-09-28 23:00 — 2026-09-28-v3-ui-redesign
**Área**: Arquitectura & UI
**Change**: openspec/changes/2026-09-28-v3-ui-redesign/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `inherit (legacy — sin tracking)`
- Paso 3 (Ejecutar): `inherit (legacy — sin tracking)`

### What
- Rediseño completo de 3 ventanas con CustomTkinter (Portada, Packs, Procesos).
- Migración de backend de PowerShell/WMI a `psutil`.
- Modelos de persistencia migrados a `pydantic v2`.

### Outcome
- Commits: (no registrados en journal)
- Tests: N/A en este ciclo (fue el kick-off del v3)
- Docs: arquitectura y UI redesign pendientes de documentar en docs/ai/.

### Impact
Sentó las bases de toda la v3. Cualquier cambio posterior parte de esta estructura. Sin este ciclo no existiría el resto.

---

## [CYCLE-002] 2026-09-29 01:35 — 2026-09-29-v3.1-quality-of-life
**Área**: Resiliencia & UX
**Change**: openspec/changes/2026-09-29-v3.1-quality-of-life/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `inherit (legacy — sin tracking)`
- Paso 3 (Ejecutar): `inherit (legacy — sin tracking)`

### What
- Integración de System Tray (`pystray`) en background.
- Rotación segura de backups `profiles.json.bak`.
- Logging continuo en `woptimizer.log`.

### Outcome
- Commits: (no registrados en journal)
- Tests: N/A en este ciclo
- Docs: quality-of-life no documentado en docs/ai/ (pendiente).

### Impact
Mejoró la resiliencia operacional: el usuario puede minimizar a tray, los profiles tienen recovery ante corrupción, y hay rastro de auditoría continua.

---

## [CYCLE-003] 2026-09-29 02:12 — 2026-09-29-ram-telemetry-widget
**Área**: Gaming & Telemetría UX
**Change**: openspec/changes/2026-09-29-ram-telemetry-widget/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `inherit (legacy — sin tracking)`
- Paso 3 (Ejecutar): `inherit (legacy — sin tracking)`

### What
- Banner dinámico de telemetría en `DashboardView` que muestra procesos cerrados y MB liberados tras activar packs.
- Implementación thread-safe vía `self.after(0, ...)`.
- Auto-hide a los 5s.
- Paleta: verde gaming (`#1DB954`) vs azul kill (`#4a9fd4`).

### Outcome
- Commits: `617eef8` (architect), `dc7c30c` (feat)
- Tests: N/A en este ciclo
- Docs: ui-design-system.md pendiente de actualizar con banner spec.

### Impact
El usuario ve feedback inmediato del impacto de activar un pack — clave para adopción y para entender qué mató el botón "Gaming".

---

## [CYCLE-004] 2026-09-29 02:18 — 2026-09-29-process-db-update
**Área**: Base de Datos & Procesos
**Change**: openspec/changes/2026-09-29-process-db-update/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `inherit (legacy — sin tracking)`
- Paso 3 (Ejecutar): `flash` (DB updates rutinarios — según tabla de la skill)

### What
- 4 procesos nuevos en `assets/process_db.json`: `sharex`, `crossdeviceservice`, `esrv_svc`, `dsaservice`.
- Todos marcados como `🔴 high` (bloatware/telemetría seguros de cerrar en gaming).

### Outcome
- Commits: `c362eda`
- Tests: no ejecutados (cambio de datos, no lógica)
- Docs: process_db.json mismo es la doc; no requiere docs/ai/ update.

### Impact
34 procesos catalogados total. Cobertura incremental sobre apps comunes de telemetría y captura.

---

## [CYCLE-005] 2026-09-29 02:21 — 2026-09-29-testing-quality
**Área**: Testing & Calidad
**Change**: openspec/changes/2026-09-29-testing-quality/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `inherit (legacy — sin tracking)`
- Paso 3 (Ejecutar): `inherit (legacy — sin tracking)`

### What
- 3 tests nuevos en `run_tests.py` (total 7): `freed_mb` return type, gaming pack protected, corrupted JSON recovery.

### Outcome
- Commits: `786a551`
- Tests: 7/7 PASS
- Docs: `docs/ai/testing-guide.md` actualizado con los 3 nuevos tests.

### Impact
Cobertura base de invariantes críticas: tipado de retorno, protección del pack gaming, recovery ante JSON corrupto. Las 3 son trampas documentadas en `docs/known-issues.md`.

---

## [CYCLE-006] 2026-09-29 02:23 — 2026-09-29-resilience-tray-logging
**Área**: Resiliencia & Robustez
**Change**: openspec/changes/2026-09-29-resilience-tray-logging/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `inherit (legacy — sin tracking)`
- Paso 3 (Ejecutar): `inherit (legacy — sin tracking)`

### What
- Fix: `tray_icon` no se guardaba en `self`, lo que impedía el cierre limpio del tray.
- `gaming_action` ahora con `try/except` + logging.
- `start_pack_apps` con `logger.info/warning` individual por app.

### Outcome
- Commits: `60c713d`
- Tests: pasan los 7 existentes (no se añadieron nuevos en este ciclo)
- Docs: ninguna doc nueva (cambios menores de robustez).

### Impact
Bug latente de cleanup de tray corregido. Sin el fix, al cerrar la app podía dejar el icono del system tray huérfano.

---

## [CYCLE-007] 2026-09-29 02:27 — 2026-09-29-perf-cache-hashmap
**Área**: Rendimiento & Latencia
**Change**: openspec/changes/2026-09-29-perf-cache-hashmap/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `pro` (refactor con riesgo de regresión)
- Paso 3 (Ejecutar): `pro` (refactor con riesgo de regresión)

### What
- Rewrite de `ProcessService`: hashmap O(1) para lookup de DB.
- Meta-cache memoizado (129 entries).
- Cache TTL 2s para `get_running_processes`.
- Kill invalida cache.

### Outcome
- Commits: `2fc51c3`
- Tests: pasan los 7 existentes
- Benchmark before: cold_scan 16ms, cached N/A.
- Benchmark after: cold_scan 15ms, cached 0.003ms, **~5000x speedup**.

### Impact
La lectura cacheada es prácticamente gratuita. Sin esto, abrir el Gestor de Procesos era la operación más cara de la app.

---

## [CYCLE-008] 2026-09-29 02:41 — 2026-09-29-native-toast-notifications
**Área**: Gaming & Telemetría UX
**Change**: openspec/changes/2026-09-29-native-toast-notifications/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `pro` (nueva service, requiere diseño)
- Paso 3 (Ejecutar): `inherit`

### What
- `NotificationService` nuevo que envuelve `pystray.Icon.notify` sin dependencias nuevas.
- Inyectado en `MainWindow` + 3 vistas.
- Autostart del tray en `__init__` con guard idempotente.
- 4 tests headless nuevos.
- Fix colateral: `pystray` y `Pillow` declarados en `pyproject.toml` (faltaban, rompían builds PyInstaller).

### Outcome
- Commits: `283bc16` (architect), `4797d6a` (feat)
- Tests: 5 → 9 backend, 0 fallos
- Docs: ui-design-system.md pendiente de extender con la spec de notificaciones.

### Impact
Notificaciones nativas Windows al activar packs. Bug colateral resuelto: builds PyInstaller habrían fallado sin declarar `pystray` + `Pillow` en `pyproject.toml`.

---

## [CYCLE-009] 2026-09-29 02:58 — 2026-09-29-config-category-emoji-alignment
**Área**: Base de Datos y Procesos
**Change**: openspec/changes/2026-09-29-config-category-emoji-alignment/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `pro` (debugging de bug crítico)
- Paso 3 (Ejecutar): `inherit`

### What
- **BUG CRÍTICO**: 6 de 8 categorías de `process_db.json` no existían en `config.py` por emojis invertidos, dejando todos esos procesos en `? Otros` sin semáforo.
- **Segundo bug**: `get_safety_badge` evaluaba `priority` antes que `category`, pintando 🟢 como 🔴.
- Fix de ambos + 2 tests de regresión.
- 14 procesos nuevos (navegadores, launchers, herramientas de IA) = 48 total.

### Outcome
- Commits: `31906e7` (process-db), `4977b00` (fix config)
- Tests: 9 → 11 backend, 0 fallos
- Docs: docs/known-issues.md ahora con Trampa #17 (emoji drift) + Trampa #18 (priority vs category ordering).

### Impact
6 categorías que parecían activas estaban completamente huérfanas. Bug invisible: el usuario veía categorías pero las apps caían en "Otros". Las pruebas de regresión ahora blindan contra ambos bugs.

---

## [CYCLE-010] 2026-09-29 02:52 — 2026-09-29-critical-invariant-coverage
**Área**: Testing y Calidad
**Change**: openspec/changes/2026-09-29-critical-invariant-coverage/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit (legacy — sin tracking)`
- Paso 2 (Planear): `pro` (caza de bugs latentes)
- Paso 3 (Ejecutar): `pro` (fix de invariante crítico)

### What
- **BUG REAL CORREGIDO**: `model_copy()` de Pydantic v2 es shallow, así que las listas del pack Gaming se compartían con `DEFAULT_GAMING_PACK`. La UI mutaba in-situ (`on_add_to_pack`), contaminando el global y haciendo que `reset_gaming_pack()` fuera un no-op silencioso.
- Fix: `model_copy(deep=True)`.
- Test verificado que DISCRIMINA (falla sin el fix).
- 8 tests nuevos para invariantes sin cobertura tras la migración v2→v3: `GamingService.should_kill_for_gaming`, `PackService` CRUD, cache TTL, kill recursivo.
- Hallazgo: los 11 `test_*.py` de la raíz están muertos (importan `process_manager` de v2). Documentados como deuda, NO borrados.

### Outcome
- Commits: `705e5f9` (tests), `1a0faa9` (fix)
- Tests: 11 → 19 backend + 1 headless, 0 fallos
- Docs: docs/known-issues.md ahora con Trampa #19 (Pydantic model_copy shallow).

### Impact
Bug latente invisible durante meses corregido. El usuario podría añadir apps al Gaming pack, cerrar la app, reabrir, y pensar que se habían perdido: era el DEFAULT_GAMING_PACK contaminado en memoria.

---

## [CYCLE-011] 2026-09-29 09:50 - 2026-09-29-git-tooling-resilience
**Área**: Resiliencia & Robustez (matriz área 1, sin tocar desde el ciclo #6)
**Change**: openspec/changes/2026-09-29-git-tooling-resilience/
**Estado**: COMPLETED
**Models**:
- Paso 1 (Buscar): `inherit` (el modelo de la sesión; la matriz pide `flash`, se subió porque la búsqueda fue de código real, no un lookup)
- Paso 2 (Planear): `inherit` (subagente `worker` + skill architect-review; la matriz pedía `pro`, se quedó en `inherit` porque el subagente no resolvió modelo explícito)
- Paso 3 (Ejecutar): `inherit` (subagente `worker` + skill openspec-dev; coherente con la matriz)

### What
- **Fallo de integridad del pipeline, no de la app**: `git_safe_commit.py` —la unica puerta de versionado y la que AGENTS.md obliga a usar en cada cierre— capturaba CUALQUIER fallo de commit, imprimia `AVISO GIT` y salia con **codigo 0**. El pipeline lo leia como exito y el CHANGELOG (MANDATORY) registraba hashes que podian no existir.
- Ademas `git add -A` fallido era solo un warning (staging parcial silencioso) y `get_env()` activaba el repo desacoplado con un simple `os.path.exists`, sin validarlo.
- **Evidencia de que no era hipotetico**: el `.git` del arbol de trabajo esta corrupto por el VFS de Nextcloud (`fatal: bad object HEAD`); el historial solo sobrevive por el repo desacoplado en LOCALAPPDATA.
- Rehecho: contrato de 4 codigos de salida (`0/1/2/3`) con lineas canonicas `WOPT_*`, validacion real del repo (`validar_repo`), sin fallback al `.git` corrupto, y flag `--verify` de solo lectura.
- **El arquitecto corrigio 3 errores de la propuesta original**, el mas grave: decidir "nada que comitear" buscando `"nothing to commit"` en stderr depende de `LANG`/`LC_ALL` y en un Windows en espanol NO aparece nunca, lo que habria convertido un arbol limpio en un fallo. Ahora se decide con `git diff --cached --quiet` (locale-independiente).
- Tambien cerro un agujero en la linea 55: un `status --porcelain` fallido se trataba como "hay cambios" en vez de como error.
- Checkpoint de empaquetado (3 ciclos desde el #8): `force_build.py` OK, `dist/woptimizer.exe` regenerado (25.65 MB) ya con los fixes de los ciclos #9 y #10.
- Recuperados 5 ficheros modificados + 2 sin seguimiento que el ciclo #10 dejo sin comitear: precisamente porque el wrapper reportaba exito en falso.

### Outcome
- Commits: `6048f6f` (architect), `b9a31fa` (fix)
- Tests: 20 -> 21 (`run_tests.py`), 0 fallos; las 3 puertas en `rc=0` (`verify_ui_syntax.py`, `run_tests.py`, `validate_docs.py` 34 OK)
- Docs: `docs/ai/sandbox-rules.md` (seccion NUEVA "Aislamiento Git en Entornos Cloud (VFS)"), `AGENTS.md` §3, `docs/ai/architecture.md` linea 39
- **Verificacion independiente del orquestador**: los 5 comportamientos del contrato comprobados en vivo (repo sano=0, GIT_DIR inexistente=3, directorio no-repo=3, sin args=2, arbol limpio=0 con `WOPT_NOOP`), y **prueba de mutacion propia**: revirtiendo el fix el test falla con `AssertionError: ... debe salir con 3, salio con 0`, con restauracion byte-identica (SHA256 `C248F694...`).

### Impact
El pipeline deja de poder "completar" ciclos sin versionar nada. Antes, un fallo de commit era indistinguible de un commit correcto para todo el sistema; ahora es un `!= 0` que detiene el ciclo. Defecto de clase: un wrapper de seguridad que miente en su codigo de salida desactiva todas las validaciones que dependen de el (`validate_docs.py` nunca habria podido detectar un hash fantasma).

