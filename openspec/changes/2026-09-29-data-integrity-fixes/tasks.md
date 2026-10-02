# Tareas OpenSpec: Integridad de datos, copia profunda y resiliencia (TASK-026)

- **Change ID**: `2026-09-29-data-integrity-fixes`
- **Taskmaster**: `TASK-026` (FIX-001, FIX-005, FIX-007, FIX-009)
- **Orden de ejecución por riesgo**: FIX-007 → FIX-009 → FIX-005 → FIX-001 (justificado en `proposal.md` §7)
- **Estado**: AUDITADA por architect-review. Aplicar **en este orden**, no agrupado.
- **Prohibido**: tocar la lógica ya cerrada del ciclo #14 (keepers / `target_categories` / barrera
  roja G-2 / `SYSTEM_PROTECTED_PROCESSES`), reintroducir `messagebox` (Trampa #14) o usar
  `self.master.after` (regla TASK-023).

---

## 1. FIX-007 — `_do_load` publica el estado desde el hilo secundario · **PRIORIDAD 1**

- [ ] **`process_manager_view.py:95-102`**: sacar las dos mutaciones del hilo. El hilo calcula
      `procs = self.process_service.get_running_processes()` y el agrupado en **variables locales**;
      publica con `self.after(0, _apply)`, donde `_apply` asigna `self.processes` y
      `self.grouped_processes` y **después** llama a `_render_list()` y `_update_pack_dropdown()`.
- [ ] **PROHIBIDO `self.master.after`**: la spec heredada (`bugfix-audit-v3/tasks.md:23`) lo pide y
      es incorrecto. `main_window.py:42-45` destruye la vista en toda navegación → callback
      huérfano sobre widgets destruidos (el bug que arregló TASK-023). Usar `self.after`.
- [ ] `self.grouped_processes` se **reemplaza** (rebind), no se hace `.clear()` in situ.
- [ ] `_group_processes()` se refactoriza a una función **pura** que recibe y devuelve el dict
      (`_group(procs) -> dict`), sin leer `self.processes`, para que sea testeable sin Tk.
- [ ] NO tocar `on_kill_selected` (`:272-284`): su patrón ya es correcto desde TASK-023.
- [ ] Revisar si `_filter_list` (`:121`) necesitaSnapshot local en vez de leer `self.grouped_processes`
      durante un refresco.

## 2. FIX-009 — respaldo preventivo + recuperación + `except` honesto · **PRIORIDAD 2**

- [ ] **`pack_service.py:62-65`**: en `save()`, **antes** de `open(..., 'w')` (que trunca), si
      `os.path.exists(self.data_path)`, hacer `shutil.copy2(self.data_path, self.data_path + ".bak")`.
      La copia debe contener la versión **ANTERIOR** (rotación real, no una copia posterior idéntica).
- [ ] **No** crear un `.bak` basura en la primera escritura de una instalación limpia.
- [ ] **`pack_service.py:55-58`**: hoy un JSON corrupto **borra todos los packs del usuario** y
      sobrescribe el archivo con uno que solo tiene el pack Gaming. Implementar recuperación: si el
      JSON principal no parsea, intentar el `.bak` **antes** de regenerar, y registrar el evento con
      `logger.warning` (no en silencio).
- [ ] **`pack_service.py:55`**: `except (json.JSONDecodeError, Exception)` es redundante (es
      `except Exception`) y por eso traga `PermissionError`/`OSError`, que **no** son corrupción y
      **no** deben entrar en la ruta destructiva. Estrechar a `json.JSONDecodeError` +
      `pydantic.ValidationError` (más `OSError` solo para "leer", nunca para "regenerar y escribir").
- [ ] Recomendado: escribir a temporal + `os.replace` (escritura atómica). No bloqueante si los dos
      puntos anteriores están.
- [ ] **Auditoría de deuda**: documentar que TASK-011 figura `status: completed`
      (`tasks.json:126-135`), que `v3.1-quality-of-life/tasks.md:5` tiene el `[x]` puesto y que
      `.taskmaster/CHANGELOG.md:1399` afirma la rotación, y que **ninguno de los tres es cierto**.

## 3. FIX-005 — literal canónico `⚪ Otros` en TRES sitios · **PRIORIDAD 3**

- [ ] `process_service.py:7`: `_DEFAULT_META = ("\u26aa Otros", "none", "Sin descripción")`.
      Hoy es `"? Otros"` (ASCII U+003F). Usar el escape `\u26aa` o el literal, pero **idéntico** a
      `config.py:95` y `models.py:9`.
- [ ] `process_service.py:113`: `props.get('category', '? Otros')` → el mismo literal canónico.
      **Este segundo sitio no está en la spec heredada**; arreglar solo el primero deja el defecto vivo.
- [ ] `pack_manager_view.py:179`: `if "? Otros" not in row.category` → comparar contra el literal
      canónico, para que "⚪ Otros" siga **excluido** del acordeón de `target_categories`.
- [ ] `run_tests.py:1483`: `assert cat != "? Otros"` pasa a `assert cat != "\u26aa Otros"`. Si no se
      toca, la aserción se vuelve **tautológica** (compara contra un literal que ya no existe) y el
      test pasa sin comprobar nada.
- [ ] Comentarios que mienten: `config.py:38` y `process_service.py:163` dicen `"? Otros"`.
- [ ] **Prohibido** reusar `\u26aa` escrito a mano en un sitio y el emoji literal en otro: comparar
      con `CATEGORY_ORDER[-1]` y con `ProcessInfo.model_fields["category"].default` en un test.

## 4. FIX-001 — fallback de `get_gaming_pack()` con copia profunda · **PRIORIDAD 4**

- [ ] `pack_service.py:84`: `DEFAULT_GAMING_PACK.model_copy()` → `.model_copy(deep=True)`.
- [ ] **Contexto obligatorio para quien lo ejecute**: NO es un bug alcanzable. `get_gaming_pack()`
      no tiene llamadores en `src/woptimizer/ui/` ni en `app.py` (todo pasa por `get_all_packs()`),
      y `_ensure_gaming_pack()` (`:60`, `:75`, `:78`) garantiza siempre la clave `"gaming"`. Es
      **deuda latente**: un solo llamador futuro reintroduce la contaminación del global.
- [ ] El ciclo #10 ya cerró la vía alcanzable (`_ensure_gaming_pack:75` y `reset_gaming_pack:94`
      usan `deep=True`) con `test_gaming_pack_lists_isolated_from_global` (`run_tests.py:876-929`),
      que **no** cubre el fallback porque llama con la clave presente.
- [ ] `docs/ai/architecture.md:64` extiende la regla `model_copy(deep=True)` a `get_gaming_pack()`.

---

## 5. Tests headless que DISCRIMINAN (registrar en el `__main__` de `run_tests.py`)

Regla: **cada test debe FALLAR sin su fix**. Nada de tests que solo comprueben tipos.

### 5.1 `test_process_manager_view_publishes_on_main_thread` (FIX-007)
Reutiliza el patrón de Tk real de `test_headless_ui` (`run_tests.py:102-122`): `WOptimizerApp` /
`ctk.CTk` con `root.update()`, nunca `sleep`. `ProcessService` stub con un `threading.Event` para
controlar el entrelazado de forma **determinista** (sin flake).

- **A — identidad de hilo**: un `RecordingDict(dict)` instalado como `view.grouped_processes`
  graba `(threading.get_ident(), op)` en `clear`, `__setitem__` y `__delitem__`. Se asserta que
  **toda** mutación ocurre en el ident del hilo principal. Hoy `clear()` y `[k] = []` llegan del
  hilo secundario → **FALLA**. Tras el fix (rebind) el dict se sustituye y no graba nada, así que
  hay que **añadir además** la mitad de consistencia para que el test no pase en vacío.
- **B — consistencia**: lanzar **dos** `_do_load` solapados con snapshots distintos y assertar que
  `view.grouped_processes` es exactamente el agrupado de `view.processes` (no de un snapshot
  obsoleto). Coge el interleave de `:97`/`:98` → **FALLA** hoy.
- **C — camino de crash**: el `RecordingDict` avisa al hilo principal en la **primera** inserción y
  el test llama a `_filter_list()` en ese instante. Hoy dispara
  `RuntimeError: dictionary changed size during iteration` → **FALLA**.
- **D — guarda estática**: parsear `process_manager_view.py` con `ast` y assertar que
  `self.processes` / `self.grouped_processes` solo se asignan dentro de la función destino de un
  `self.after(0, ...)`, y que no hay ningún `self.master.after`.

### 5.2 `test_pack_service_backup_and_recovery` (FIX-009)
Usa `_pack_service_temporal()` (`run_tests.py:11-23`) y `finally: os.unlink`. Nunca toca el
`profiles.json` real.

- **A — copia preventiva**: `create_user_pack` + `save()` → assertar que existe `tmp + ".bak"` y que
  su contenido parseado es el estado **previo** (sin el pack nuevo), mientras `tmp` ya lo tiene.
  Hoy no existe ningún `.bak` → **FALLA**.
- **B — rotación, no copia**: dos `save()` seguidos → `.bak` contiene la versión N-1, no la N. Así
  se descarta una implementación que copia *después* de escribir.
- **C — recuperación (la mitad que la `description` omitía)**: sobrescribir `tmp` con `"{ roto"`,
  construir un `PackService` nuevo → assertar que el pack de usuario **sobrevive** (viene del `.bak`)
  y que `is_gaming is True`. Hoy `load()` lo borra todo → **FALLA**.
- **D — `except` honesto**: `PackService(data_path=<un directorio>)` debe **propagar** el error, no
  regenerar en silencio un fichero por defecto. Hoy `except Exception` se lo traga → **FALLA**.

### 5.3 `test_default_meta_matches_canonical_otros` (FIX-005)
- `_DEFAULT_META[0] == CATEGORY_ORDER[-1] == ProcessInfo.model_fields["category"].default`, y
  además `"\u26aa" in _DEFAULT_META[0]` (caza el `?` ASCII disfrazado). Hoy **FALLA**.
- **Comportamental, no de tipos**: con un `ProcessService` de `_db_map` vacío,
  `ps._get_process_meta("nombre_inexistente_xyz")` debe devolver una categoría que
  `cat_idx.get(cat, 999)` resuelva al **último índice** de `CATEGORY_ORDER` (o sea, participa en el
  orden) y no al centinela 999 de `process_service.py:252`. Hoy **FALLA**.
- **Sitio 3**: escaneo estático con `ast` de `pack_manager_view.py` que asserta que el literal
  comparado en el filtro de la línea 179 es `"\u26aa Otros"`. Hoy **FALLA**.
- **Sitio 2**: una entrada de DB sintética sin clave `category` debe entrar por el literal canónico.

### 5.4 `test_gaming_pack_fallback_is_deep_copy` (FIX-001)
- Forzar el fallback: `del svc._data.packs["gaming"]` y llamar a `get_gaming_pack()`.
- Assertar `g.apps is not DEFAULT_GAMING_PACK.apps`, y lo mismo con `keepers` y
  `target_categories`. Hoy `model_copy()` es shallow → **FALLA**.
- Mutar las tres listas in situ y assertar que el global queda intacto; luego `reset_gaming_pack()`
  y assertar que los valores de fábrica vuelven. (Réplica del test del ciclo #10 pero **sobre el
  fallback**, que es la única ruta sin cobertura hoy.)

---

## 6. Cierre

- [ ] `python verify_ui_syntax.py`, `python run_tests.py` y `python validate_docs.py` en verde.
- [ ] `run_tests.py` registra los 4 tests nuevos en el bloque `if __name__ == "__main__"`
      (`run_tests.py:1487-1514`).
- [ ] **ASCII puro en todos los `print()`** de los tests nuevos (consola Windows cp1252, Trampa #16).
      Para los emojis usar escapes `\u26aa`, nunca el glifo literal en una cadena de `print`.
- [ ] `docs/ai/data-models.md`: contrato de escritura de `profiles.json` (copia preventiva + recuperación
      desde `.bak`), el literal `⚪ Otros` como fuente única, y la corrección de la afirmación falsa de
      TASK-011.
- [ ] `docs/ai/architecture.md`: regla `model_copy(deep=True)` extendida a `get_gaming_pack()`, y
      regla "el estado de una vista solo se publica con `self.after(0, ...)`, nunca desde el hilo".
- [ ] `docs/ai/testing-guide.md`: los 4 tests nuevos y el abandono de la aserción `!= "? Otros"`.
- [ ] Cierre limpio: árbol de git con 0 cambios pendientes.
