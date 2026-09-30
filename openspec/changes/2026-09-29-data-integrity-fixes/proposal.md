# Propuesta: Integridad de datos, copia profunda y resiliencia de servicios (FIX-001, FIX-005, FIX-007, FIX-009)

- **Change ID**: `2026-09-29-data-integrity-fixes`
- **Ciclo**: #15
- **Área de rotación**: 1 — Resiliencia & Robustez
- **Taskmaster**: `TASK-026`
- **Subagente de ejecución**: `openspec-dev`
- **Estado**: AUDITADA por architect-review — **aprobada con correcciones obligatorias** (ver §6)
- **Alcance**: `src/woptimizer/services/pack_service.py`, `src/woptimizer/services/process_service.py`,
  `src/woptimizer/ui/views/process_manager_view.py`, `src/woptimizer/ui/views/pack_manager_view.py`,
  `run_tests.py`, `docs/ai/data-models.md`

## 0. Resumen del veredicto de la auditoría

| # | Corrección | Veredicto | Riesgo real |
|---|---|---|---|
| FIX-001 | `get_gaming_pack()` fallback shallow | **REDEFINIDA** — el bug es real pero **inalcanzable desde la UI** | Bajo (deuda latente) |
| FIX-005 | `_DEFAULT_META` con `"? Otros"` | **CONFIRMADA — y son 3 sitios, no 1** | Medio (familia de emojis) |
| FIX-007 | Race en `_do_load` | **CONFIRMADA — riesgo más alto del lote** | **Alto** (crash + set de PIDs incoherente) |
| FIX-009 | `save()` sin backup | **CONFIRMADA como FALTA — la premisa "ya hay rotación" es FALSA** | **Alto** (pérdida de datos) |

Orden de ejecución por riesgo: **FIX-007 → FIX-009 → FIX-005 → FIX-001** (justificación en §7).

## 1. FIX-001 — copia profunda en el fallback de `get_gaming_pack()`

### 1.1 Qué dice el código

`pack_service.py:83-84`:

```python
def get_gaming_pack(self) -> Pack:
    return self._data.packs.get("gaming", DEFAULT_GAMING_PACK.model_copy())
```

Sí es un fallback (el segundo argumento de `dict.get`), y sí es **shallow**: `model_copy()` de
Pydantic v2 sin `deep=True` comparte los objetos de `apps`, `keepers` y `target_categories` con el
global de módulo. Verificado empíricamente:

```
2 fallback_shares_apps True
3 global_contaminated True
```

(Se borró `gaming` de `svc._data.packs`, se llamó al fallback, se hizo
`g.apps.append('CONTAMINA.exe')` y el global quedó contaminado.)

### 1.2 Por qué NO es un bug alcanzable hoy — tres capas lo cierran

1. **`get_gaming_pack()` no tiene ningún llamador en producción.** El grep sobre
   `src/woptimizer/ui/` y `app.py` devuelve **cero** llamadas. Toda lectura de packs pasa por
   `get_all_packs()`: `app.py:92`, `pack_manager_view.py:60, 100, 217, 249, 257, 270, 292`,
   `process_manager_view.py:113, 294`, `dashboard_view.py:97`. Los únicos llamadores son
   `run_tests.py:162, 833, 849, 857, 896, 919` y `verify_task1.py:18, 38`.
2. **El fallback es código muerto por construcción.** `load()` termina siempre con
   `_ensure_gaming_pack()` (`pack_service.py:60`), que inserta `"gaming"` si falta (`:75`) y, si
   existe, fuerza `is_gaming = True` (`:78`). Verificado: `gaming_present_after_load True`.
   `delete_pack()` además **rechaza** el pack de sistema (`:117-118`).
3. **El ciclo #10 ya cerró la contaminación alcanzable.** `_ensure_gaming_pack()` (`:75`) y
   `reset_gaming_pack()` (`:94`) ya usan `model_copy(deep=True)`, con la regresión cubierta por
   `test_gaming_pack_lists_isolated_from_global` (`run_tests.py:876-929`).

### 1.3 Redefinición

No es "el bug que hace que *Restaurar por defecto* no haga nada" (ese fue el del ciclo #10 y está
cerrado). Es **deuda latente / defensa en profundidad**: un solo llamador futuro en la UI
reintroduce el no-op silencioso. El arreglo es de un carácter (`deep=True`) y el coste es nulo, así
que **se mantiene, pero baja a última prioridad**.

Dos hallazgos colaterales que hacen el arreglo mejor de lo que dice la spec:

- `dict.get(k, default)` evalúa el default **siempre**, incluso cuando la clave existe. Hoy cada
  llamada a `get_gaming_pack()` paga un `model_copy()` inútil. Corregir a deep no empeora esto.
- `test_gaming_pack_lists_isolated_from_global` (`:896`) llama a `get_gaming_pack()` con la clave
  **presente**, así que **no cubre el fallback**. El defecto lleva un ciclo entero sin test.

## 2. FIX-005 — `_DEFAULT_META` desalineado: son TRES sitios, no uno

### 2.1 Confirmación del desalineamiento

`process_service.py:7` usa la interrogación ASCII `?` (U+003F) donde el resto del sistema usa el
círculo `⚪` (U+26AA):

```python
_DEFAULT_META = ("? Otros", "none", "Sin descripción")
```

Verificado empíricamente (con `PYTHONIOENCODING=utf-8`; el `repr` falla en cp1252, Trampa #16):

```
DEFAULT_META_0 '? Otros'
ORDER_LAST   '⚪ Otros'
MATCH False
```

Las dos fuentes canónicas son `config.py:95` (`CATEGORY_ORDER = ... + ['⚪ Otros']`) y
`models.py:9` (`category: str = "⚪ Otros"`).

### 2.2 El segundo sitio que la spec original pasó por alto

`process_service.py:113`, en `_load_local_db()`:

```python
db_map[key] = (
    props.get('category', '? Otros'),      # <-- mismo literal ASCII
    ...
)
```

Cualquier entrada de `assets/process_db.json` sin clave `category` entra por aquí con el literal
equivocado. Arreglar solo la línea 7 deja la mitad del defecto viva.

### 2.3 El tercer sitio, y es el que hace peligroso al arreglo parcial

`pack_manager_view.py:179`, dentro del acordeón de categorías:

```python
for row in getattr(self.process_service, 'process_db', []):
    if "? Otros" not in row.category:
        all_cats.add(row.category)
```

El filtro de la UI está escrito contra el literal **equivocado**. Hoy no dispara por casualidad:
`process_db` (la property de `process_service.py:79-83`) itera `_db_map`, que nunca contiene la
categoría de fallback, así que el filtro es un no-op inofensivo.

**El peligro**: arreglar `process_service.py:7` y `:113` sin tocar `:179` deja el filtro comparando
`"? Otros"`, que ya no puede aparecer — es decir, **neutro**. Pero si además entra en la DB una
entrada con la categoría canónica `⚪ Otros`, el filtro actual (`"? Otros" not in row.category`)
**no la excluiría** y ofrecería "⚪ Otros" como casilla activable de `target_categories`. Con la
barrera roja de G-2 (TASK-025) el buckete no es mortal, pero es basura seleccionable.

**Los tres sitios deben cambiarse en el mismo commit**: `process_service.py:7`,
`process_service.py:113` y `pack_manager_view.py:179`.

### 2.4 Cuarto sitio: un test que se volvería tautológico

`run_tests.py:1483` afirma `assert cat != "? Otros"`. Tras el cambio, la comparación nunca puede
fallar porque el literal ya no existe en el código: el test pasa sin comprobar nada. Debe pasar a
`"\u26aa Otros"`.

### 2.5 Riesgo

**Bajo en cuanto a lo visible** (una etiqueta distinta y un agrupado al final de la lista, ambos ya
así) pero **alto en cuanto a precedente**: es exactamente la familia de defecto que costó un bug
crítico en el ciclo #9. El coste del arreglo es ridículo; el coste de la omisión es otro bug de
emoji desalineado. Además, `config.py:38` y `process_service.py:163` mencionan `"? Otros"` en
comentarios y quedan como documentación mentirosa.

## 3. FIX-007 — race condition en `ProcessManagerView._do_load` (riesgo más alto)

### 3.1 Confirmación: sí, es una mutación desde el hilo secundario

`process_manager_view.py:95-102`:

```python
def _do_load(self):
    def _load():
        self.processes = self.process_service.get_running_processes()   # 97  MUTACION
        self._group_processes()                                        # 98  MUTACION
        self.after(0, self._render_list)                              # 99  correcto
        self.after(0, self._update_pack_dropdown)                     # 100 correcto
    threading.Thread(target=_load, daemon=True).start()
```

Atributos tocados y desde dónde:

| Atributo | Escritura | Hilo |
|---|---|---|
| `self.processes` | `:97` | secundario |
| `self.grouped_processes` | `:105` (`clear()`), `:109` (`[k] = []`), `:110` (`append`) vía `_group_processes()` | secundario |
| `self.checkboxes` | `:133`, `:205` (dentro de `_render_list`) | principal — correcto |

Las líneas 99-100 ya usan el patrón correcto (publicar con `self.after(0, ...)`). El defecto está
solo en 97-98.

### 3.2 Tres fallos concretos, no uno

**(a) `RuntimeError: dictionary changed size during iteration`.** El hilo principal recorre
`self.grouped_processes` en `_render_list` (`:137`, `for name_key, procs in self.grouped_processes.items()`)
y en `_filter_list` (`:122`), que dispara con **cada pulsación del buscador** por el trace de
`search_var` (`:45`). El hilo secundario hace `.clear()` (`:105`) y `[k] = []` (`:109`) sobre ese
mismo dict. La excepción sube por el trace de la variable de Tk y **mata la app**.

**(b) `self.processes` y `self.grouped_processes` dejan de describir lo mismo.** La línea 97
asigna la lista y la 98 la agrupa leyendo `self.processes` (`:106`). Con dos `_do_load` solapados
—el botón de refrescar, o el `after(1000, self.refresh_processes)` de `:279` mientras el anterior
sigue vivo— el segundo hilo puede reasignar `self.processes` entre 97 y 98, y `grouped_processes`
queda describiendo un snapshot distinto del almacenado.

**(c) El set de PIDs que se mata queda desalineado.** `on_kill_selected` lee
`self.grouped_processes.get(k, [])` (`:263`) en el hilo principal y lo entrega a `kill_processes`
en un hilo secundario (`:272-273`). Con un agrupado a medio aplicar, `to_kill` puede salir vacío
con casillas marcadas (el aviso de "sin procesos" es engañoso) o contener procesos de un snapshot
obsoleto. **Este producto mata procesos reales de Windows**: un `ProcessInfo` obsoleto es un riesgo
de seguridad, no solo de UX.

### 3.3 El patrón correcto ya existe en el proyecto

`dashboard_view.py:152-163`: el hilo calcula en variables locales y lo único que publica es
`self.after(0, self._show_banner, killed, freed_mb, p.is_gaming)` (`:159`). La vista de procesos
debe hacer lo mismo.

### 3.4 Corrección obligatoria a la spec heredada

`bugfix-audit-v3/tasks.md:23` pide publicar con **`self.master.after(0, _apply)`**. Eso es
**incorrecto** y reintroduce el bug de TASK-023: `main_window.py:42-45` (`_clear_content`) destruye
la vista en **toda** navegación, así que un `after` colgado en el `master` sobrevive al cambio de
pestaña y reconfigura widgets ya destruidos. El publicador debe ser **`self.after(0, _apply)`**, y
la vista ya sobrescribe `destroy()` con `cancel_on_destroy()` (`:74-78`).

Además, `on_kill_selected` (`:272-284`) tiene el mismo patrón correcto desde el ciclo #12 y debe
quedarse como está; la corrección es local a `_do_load`.

## 4. FIX-009 — backup preventivo en `PackService.save()`

### 4.1 La premisa de la tarea ("ya hay rotación, ciclo #2 / TASK-011") es FALSA

`pack_service.py:62-65`:

```python
def save(self) -> None:
    with open(self.data_path, 'w', encoding='utf-8') as f:
        json.dump(self._data.model_dump(), f, indent=4, ensure_ascii=False)
```

Sin `shutil`, sin `.bak`, sin escritura atómica. El grep de `\.bak|shutil|copy2|os\.replace|NamedTemporary`
sobre `src/` devuelve **cero coincidencias**. Verificado empíricamente: tras construir un
`PackService` y guardar, el directorio temporal contiene solo `['p.json']`.

Y sin embargo el proyecto **afirma tres veces** que la rotación existe:

- `tasks.json:126-135` — TASK-011 `"status": "completed"`, descripción *"auto-backup de perfiles al guardar"*.
- `openspec/changes/2026-09-29-v3.1-quality-of-life/tasks.md:5` — `- [x] Modificar PackService.save() para que cree un archivo profiles.json.bak de forma segura`.
- `.taskmaster/CHANGELOG.md:91` — *"Rotación segura de backups `profiles.json.bak`"*.

**No es redundante: es una feature documentada que nunca se escribió** (o que se perdió en la
reescritura v3). El único código `.bak` del repo está en los ficheros de test legacy muertos
(`test_gaming_session.py:37`, `test_gaming_profile.py:32`), que además respaldan para **restaurar**,
no para rotar.

### 4.2 La mitad que TASK-026 se ha dejado en el camino (y es la que vale)

`bugfix-audit-v3/tasks.md:24` pide dos cosas; la `description` de TASK-026 solo conserva la primera.
La segunda es la importante:

> "En `load()`, si el JSON principal está corrupto, intentar cargar `.bak` antes de regenerar con pack gaming por defecto."

Hoy `load()` hace exactamente lo contrario (`pack_service.py:55-58`):

```python
except (json.JSONDecodeError, Exception):
    self._data = AppData()
    self._ensure_gaming_pack()
    self.save()
```

Un JSON truncado — un apagón durante `json.dump` es suficiente — **destruye todos los packs del
usuario y sobrescribe el archivo con uno que solo contiene el pack Gaming.** No hay aviso, no hay
log, no hay `.bak` al que recurrir. Los packs son lo único que el usuario ha configurado a mano.

Y el `except (json.JSONDecodeError, Exception)` es redundante (es `except Exception`) y por eso
**también** traga `PermissionError` y `OSError`: un fallo transitorio de escritura o un archivo
bloqueado por el antivirus **dispara la misma ruta destructiva**. Ese es el tercer punto.

### 4.3 Redefinición

FIX-009 son tres cambios, no uno:

1. **Copia preventiva** en `save()`: `shutil.copy2(self.data_path, self.data_path + ".bak")`
   **antes** de `open(..., 'w')`, que trunca. Solo si el archivo ya existe (no crear un `.bak`
   basura en la primera escritura). La copia debe ser de la versión **anterior** (rotación real, no
   una copia posterior idéntica).
2. **Recuperación** en `load()`: si el JSON principal falla al parsear, intentar el `.bak` antes de
   regenerar, y **registrar el evento con `logger.warning`** en vez de perderlo en silencio.
3. **Estrechar el `except`** para que un error que **no** es corrupción (permisos, EIO) **no**
   entre en la ruta que sobrescribe los datos del usuario: debe propagar o al menos no escribir.

Recomendable además: escribir el JSON nuevo a un temporal y `os.replace` (atómico), para que un
corte de luz no deje un `profiles.json` truncado. No es bloqueante si (1) y (2) están.

## 5. Qué NO se toca

- `src/woptimizer/ui/confirmation.py` y el resto de TASK-023: intactos.
- Los `keepers`/`target_categories` y la barrera roja G-2 de TASK-025: cerrados en el ciclo #14.
- Los 11 `test_*.py` legacy de la raíz: se conservan (FIX-014, norma del propietario).
- Nada de `messagebox` (Trampa #14), nada de `self.master.after` (§3.4).

## 6. Correcciones obligatorias a la `description` de TASK-026

1. FIX-005 pasa de "1 sitio" a **3 sitios** (`process_service.py:7`, `process_service.py:113`,
   `pack_manager_view.py:179`) + actualizar la aserción tautológica de `run_tests.py:1483`.
2. FIX-009 pasa de "backup preventivo" a **backup preventivo + recuperación desde `.bak` +
   estrechar el `except`**, y se documenta que TASK-011 está marcado `completed` sin código.
3. FIX-007 debe usar `self.after(0, _apply)`, **nunca** `self.master.after` como dice la spec heredada.
4. FIX-001 se degrada a deuda latente con nota explícita de que el ciclo #10 ya cerró la vía
   alcanzable y de que hoy **no tiene test**.

## 7. Orden de ejecución por riesgo real

1. **FIX-007** — único defecto que puede tumbar la app en uso normal (una pulsación en el buscador
   durante un refresco) y el único que puede producir un set de PIDs incoherente en un `kill`.
2. **FIX-009** — pérdida silenciosa e irreversible de la configuración del usuario ante un JSON
   corrupto. Mitad de la spec original, omitida por la `description` heredada.
3. **FIX-005** — cosmético hoy, pero tres sitios y la familia de defecto que ya produjo un bug
   crítico. Barato, y debe ir acompañado del test que deja de ser tautológico.
4. **FIX-001** — un carácter, inalcanzable, sin test. Último.

## 8. Documentación viva afectada

- `docs/ai/data-models.md`: contrato de escritura/respaldo de `profiles.json` (nuevo §), literal
  canónico `⚪ Otros` como fuente única, y la corrección de la afirmación de backups de TASK-011.
- `docs/ai/architecture.md`: la regla `model_copy(deep=True)` (ya en `:64`) debe **extenderse** a
  `get_gaming_pack()`; y documentar la regla "publicar estado de vista solo con `self.after(0, ...)`".
- `docs/ai/testing-guide.md`: los 4 tests nuevos y el abandono de la aserción `!= "? Otros"`.
