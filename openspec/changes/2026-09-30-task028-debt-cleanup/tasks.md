# TASK-028 — Plan de ejecución

Alcance autorizado por `architect-review` el 2026-09-30. Decisión de diseño completa en
[`proposal.md`](proposal.md). Ficheros fuera de `src/woptimizer/` y `run_tests.py`: **prohibidos**
salvo los listados abajo.

---

## BLOQUE SEGURO — aprobado para implementar

### S1. FIX-010 — logging (el único con riesgo de este bloque)
- [ ] `src/woptimizer/config.py`: eliminar el `logging.basicConfig(...)` de nivel de módulo
      (líneas 18-22). **Conservar `logger = logging.getLogger('woptimizer')`** (línea 23) intacto:
      lo importan `notification_service.py:21`, `pack_service.py:8`, `process_service.py:7`,
      `ui/app.py:41,90`.
- [ ] `src/woptimizer/config.py`: añadir `setup_logging(level=logging.WARNING)` con `force=True`
      y el mismo `filename`/`format` que el `basicConfig` actual.
- [ ] `src/woptimizer/__main__.py`: invocar `setup_logging()` al inicio de `main()`, **antes** de
      instanciar los servicios.
- [ ] `run_tests.py`: invocar `setup_logging()` en su `__main__`.
- [ ] `run_tests.py`: añadir `test_logging_va_a_fichero_y_no_a_stderr` (proposal §11, T1).

> `force=True` es obligatorio, no cosmético: sin él la segunda llamada es un no-op mudo.

### S2. FIX-012 — tautema (riesgo nulo, sin test)
- [ ] `src/woptimizer/ui/views/process_manager_view.py:184`:
      `is_expanded = True if search_query else True` → `is_expanded = True`.
- [ ] **SIN test de regresión y SIN sonda de mutación**, deliberadamente: el valor es idéntico antes
      y después. Un test aquí no distinguiría nada (proposal §3).

### S3. FIX-016 — import redundante (riesgo nulo, sin test)
- [ ] `src/woptimizer/ui/app.py:61`: eliminar el `import sys` local de `quit_app()`.
      El de nivel de módulo (`:1`) **se queda**: se usa en `on_window_close` (`:45`).
- [ ] Verificar antes que `quit_app` (`:50-62`) no usa `sys` **antes** de la línea 61: un `import`
      local convierte el nombre en local a toda la función y daría `UnboundLocalError`. Hoy no ocurre.

### S4. FIX-017 — archivar el plan de inconsistencias
- [ ] Crear `docs/archive/` (no existe) y mover allí `inconsistencies_plan.md` **sin tocar su
      contenido**. Es un plan "100% Completado" que describe incidencias ya resueltas y cita un
      `fallback.csv` que ya no existe: por eso se archiva, no se borra.

### S5. FIX-015 (parcial) — archivar el `profiles.json` v2 del root
- [ ] Crear `docs/archive/legacy-root-data/README.md`: qué es cada fichero, su fecha, y por qué se retiró.
- [ ] Mover `profiles.json` (raíz, 420 B, esquema v2 muerto: `__system_gaming__`/`factory`/
      `kill_low_chat`/sin `is_gaming`) a `docs/archive/legacy-root-data/profiles.json`.
- [ ] **NO tocar** `test_profiles_task1.json` (lo consume `verify_task1.py:12`) ni
      `saved_processes.json` (está en `.gitignore:8`; es estado local del usuario, no del repo).

### S6. FIX-018 — versión (cosmético; requiere decisión del propietario)
- [ ] Resolver con el propietario si la release `3.0.1` existe. Si existe → `3.0.1` en
      `pyproject.toml:3` y `src/woptimizer/__init__.py:1`. Si no → unificar en `3.0.0` y **no**
      afirmar una versión publicada que no existe.
- [ ] Verificado: `woptimizer.spec` **no** declara `version` y `build.bat`/`force_build.py` no la
      mencionan. Son exactamente dos ficheros.
- [ ] `run_tests.py`: añadir `test_la_consulta_de_version_no_puede_desincronizarse` (T2), leyendo
      `pyproject.toml` con `tomllib` y `__init__.py` con `ast` (**nunca `import`**, que ejecutaría
      el paquete).

### S7. FIX-020 — documentación viva
- [ ] `docs/ai/architecture.md`: **corregir la ubicación de `SYSTEM_PROTECTED_PROCESSES`**. El
      documento (línea 76) lo sitúa en `config.py`; **vive en `process_service.py:23-38`** (34
      nombres). Documentar los 34 o remitir a la línea.
- [ ] `docs/ai/architecture.md`: añadir el contrato de logging de S1 como invariante (§15), para que
      el cambio de FIX-010 no se lea como un refactor invisible.
- [ ] `docs/ai/data-models.md`: sincronizar con la decisión de versión de S6.
- [ ] `CHANGELOG.md` y `.taskmaster/CHANGELOG.md`: entrada del ciclo.

### S8. FIX-014 — restricción (verificación, no trabajo)
- [ ] Confirmar al cierre que los **11** `test_*.py` del root están intactos: `git status --porcelain`
      no debe listarlos. Ninguna prueba nueva fuera de `run_tests.py`.

---

## BLOQUE RIESGOSO — NO APROBADO

### R1. FIX-013 — migración `procesos.csv` → `assets/process_db.json` ⛔
**Fuera de alcance.** Premisa falsa: la migración **ya se ejecutó** en el ciclo 13
(`.taskmaster/CHANGELOG.md:1682`, 48 → 73 entradas). Importar el CSV revertiría decisiones de
seguridad deliberadas (la pila Armoury Crate / ASUS / GIGABYTE volvería de 🔴 a 🟢 killable:
"el equipo se queda sin perfil de RGB y ventilación", `.taskmaster/CHANGELOG.md:1686`), y el CSV tiene **11 de 131
filas malformadas** con la descripción sin comillas.

- [ ] **NO** modificar `procesos.csv` ni `assets/process_db.json` en esta tarea.
- [ ] Abrir **TASK-031** con `process-db-updater` como dueño si el propietario quiere la ampliación.
- [ ] Si se desbloquea: aplicar T3 (`test_la_columna_seguridad_del_csv_no_es_la_fuente_de_verdad`)
      y excluir `applicationframehost`, `widgetboard`, `widgetservice` (no están en
      `SYSTEM_PROTECTED_PROCESSES` y el CSV los marca `Verde`).

### R2. FIX-011 — `PROCESS_LIST_FILE` ⛔
**No borrar.** La usan `test_gaming_session.py:36-50`, `test_harness.py:37`, `test_harness_v2.py:64`
(los tres protegidos por FIX-014) y `smoke_check.py:23`, que hace `assert` sobre el **texto fuente**:
`assert "PROCESS_LIST_FILE = os.path.join(_app_dir()" in code`. Borrarla rompe el smoke check y
contradice FIX-014 en la misma tarea.

> ⚠️ **Corregido el 2026-09-30 (D1).** Los **tres primeros** son consumidores vivos. El cuarto,
> `smoke_check.py`, **está muerto**: lee `process_manager.py` (inexistente) en su línea 8 y nunca
> alcanza la 23. La decisión de no borrar se sostiene en los tres, no en el cuarto.

- [ ] **NO** eliminar la constante. Como mucho, un comentario de deprecación que nombre a los
      4 consumidores.
- [ ] **NO** borrar `saved_processes.json` (37.997 B): está en `.gitignore:8` y es estado local del
      usuario, no del repositorio.

---

## Cierre

- [ ] `python run_tests.py` en verde.
- [ ] `python verify_ui_syntax.py` y `python validate_docs.py` en verde.
- [ ] ~~`python smoke_check.py` en verde **sin haberlo tocado** (criterio 3)~~ — **IMPOSIBLE,
      retirado el 2026-09-30 (D2).** El script lee `process_manager.py` en su línea 8 y ese
      fichero no existe: `FileNotFoundError` antes de llegar a su línea 23. No tiene ruta verde.
      Sustituido por `test_process_list_file_sigue_siendo_un_contrato` (ciclo 21), que sí corre.
- [ ] `python .taskmaster/git_safe_commit.py "chore(task028): ..."` con salida **0**.
- [ ] `mutation-auditor` sobre las 2 sondas nuevas (T1, T2). T3 solo si se desbloquea R1.
- [ ] Marcar `"status": "completed"` en `.taskmaster/tasks.json` (Paso 3, no este agente).
