# Tareas OpenSpec: cerrar los 3 supervivientes de mutación (TASK-030)

- **Change ID**: `2026-09-30-close-mutation-survivors`
- **Taskmaster**: `TASK-030`
- **Estado**: AUDITADA por architect-review. **Aprobada con las correcciones de `proposal.md` §6.**
- **Regla que gobierna este change**: *todo criterio nombra la mutación exacta que lo mata*. Un
  criterio sin mutación asociada no es un criterio de aceptación, es un deseo.
- **Prohibido**: `sleep` en cualquier test (Trampa #8 y #12), `subprocess` (Trampa #9 / sandbox EPERM),
  tocar `SYSTEM_PROTECTED_PROCESSES` / keepers / barrera G-2 / doble pulsación, y abrir una ventana
  real en el arnés de FIX-007.

## 0. Mapa sonda → mutación (copia de `proposal.md` §5, es la columna de la derecha la que importa)

| Sonda | Muerte |
|---|---|
| P1 el volcado nunca toca el principal | M1, M3, M4, M10 |
| P1b publicar no trunca el principal | M2 |
| P2 `save()` no escribe si la rotación no puede leer | M6 (**M7 la matan P6/P7, ver §6**) |
| P3 se intentó volcar (espiando `json.dump`, no `save()`) | M1, M10 |
| P4 la forma legacy no tumba la app | — **falla hoy: es el bug** (M12) |
| P5 tabla de clases de corrupción | M5 |
| P6 un `OSError` de lectura no es corrupción | M6, M7 |
| P7 un `AttributeError` ajeno no es corrupción | M7, **M9** |
| P8 arnés sin Tk para FIX-007 | mutación de FIX-007 (M13) |

> Tabla original del arquitecto, con la **corrección medida** en §6. La muerte que cambia es la de
> P2/M7: el código correcto y el mutante son indistinguibles en D2 (`proposal.md` §2.1), así que la
> muerte de M7 no puede ser de P2 sino de las sondas que pasan por `load()`.

---

## 1. Punto 1 — Atomicidad (no toca `src/`) · **PRIORIDAD 1**

- [x] **P1 `test_save_atomic_nunca_toca_el_principal`**: doble de `json.dump` que anota `fp.name`,
      si es el principal, si está en el mismo directorio, si el `.tmp` existe **en ese instante** y
      si el principal conserva sus bytes; escribe un prefijo JSON truncado por el handle real,
      `flush()` y lanza `OSError`. Después: `save()` lanzó, **bytes del principal idénticos**, sin
      `.tmp`, y `PackService(data_path)` todavía carga los packs anteriores.
      **Orden obligatorio**: `antes = read_bytes()` se captura **DESPUÉS** de construir el servicio
      (`__init__` ya escribe una vez). Capturarlo antes produce un fallo con el código correcto.
      **Mata**: M1 (`open(w)` directo) por 4 aserciones, M3 (sin `unlink`), M4 (`except: pass`),
      M10 (`.tmp` en otro volumen).
- [x] **P1b `test_publicar_no_trunca_el_principal`**: `shutil.copyfile` substituido por un doble que
      **trunca el destino** y lanza (emula una copia interrumpida). `save()` debe completarse sin
      llamarlo y el principal debe quedar **completo y parseable** con el pack nuevo.
      **Mata**: M2 (`os.replace` → `shutil.copyfile`), que hoy solo lo mata una aserción de
      artefacto `.tmp` — verde por la razón equivocada.
- [x] **P3 `test_corrupcion_sin_backup_intenta_volar`**: camino D2 (principal corrupto + solo
      lectura + sin `.bak`), con un contador sobre `json.dump` que debe ser `>= 1`.
      **Mata**: M1, M10 (`volcados=0`). **Documentar en el docstring que NO mata M6/M7** y por qué
      (`proposal.md` §2.1).
- [x] Guard estático adicional (no sustituye a P1): ninguna llamada a `shutil.copyfile`/`shutil.move`
      con el principal como destino dentro de `save()`. Declararlo en el docstring como *red*, no
      como prueba.
- [x] **PROHIBIDO**: leer el fichero desde otro hilo, `sleep`, o afirmar solo "existe un `.tmp`".

## 2. Punto 2 — `except` honesto (no toca `src/`) · **PRIORIDAD 1**

- [x] **P2 `test_save_no_escribe_si_la_rotacion_no_puede_leer`**: `json.load` lanza `PermissionError`
      durante `_rotate_backup`; `svc._data` se vacía y se llama `save()`. Debe **lanzar** y el
      principal debe conservar sus bytes.
      **Mata**: M6 (reintroducir `OSError` en `CORRUPTION_ERRORS`; medido: `save() no lanzó` +
      `SOBRESCRIBIÓ el principal`), M7.
- [x] **P6 `test_oserror_de_lectura_no_es_corrupcion`**: principal ilegible + `.bak` sano →
      `PackService()` **propaga** el `PermissionError` y el `.bak` queda intacto byte a byte.
      **Mata**: M6 (arrancaba en silencio con datos viejos), M7.
- [x] **P7 `test_attribute_error_ajeno_no_es_corrupcion`**: `PackService._read_json` parcheado para
      lanzar `AttributeError("bug interno")` en el principal → debe **propagar**, no recuperarse del
      `.bak`. **Mata**: M7 y **M9** (el arreglo ingenuo de meter `AttributeError` en la tupla).
- [x] **Prohibido** un espía que cuente llamadas a `save()`: medido `save()=1, volcados=1` en el
      código correcto **y** en M6/M7. D2 es indiscriminable por construcción (`proposal.md` §2.1).
- [x] **Prohibido** eliminar los casos D1/D2 existentes: siguen siendo valiosos; lo que se añade es
      que ya no son la **única** defensa de esa propiedad.

## 3. Punto 3 — `CORRUPTION_ERRORS` y la forma legacy · **PRIORIDAD 2** (toca `src/`)

- [x] **P5 `test_todas_las_clases_de_corrupcion_se_recuperan`**: tabla de 4 filas con `.bak` sano,
      cada una debe recuperarse del backup y no lanzar. Fuentes de los fixtures, **verificadas**:
      - `JSONDecodeError` → `'{"packs": {"x": '`
      - `TypeError` → `'[1, 2, 3]'` (falla en `AppData(**raw_data)`)
      - `UnicodeDecodeError` → bytes `b'{\xff\xfe"packs":{}}'`
      - `ValidationError` → `{"packs": {"x": {"id": "a", "name": "b", "default_action": "BOOM"}}}`
        (viola el `Literal["start","kill"]` de `models.py:21`; **`Pack` es demasiado tolerante** —
        `id: 1` o `apps: 3` se coercian y NO producen `ValidationError`, verificado)
      **Mata**: M5 (y cada eliminación parcial de la tupla, fila a fila).
- [x] **`pack_service.py`: `class PerfilCorruptoError(ValueError)` definida ANTES de
      `CORRUPTION_ERRORS`** (después ⇒ `NameError` al importar; comprobado) y añadida a la tupla.
- [x] **`pack_service.py` `_read_json` rama legacy**: `isinstance(raw_data['profiles'], dict)` y
      `isinstance(v, dict)` antes de `.items()` / `.get()`, lanzando `PerfilCorruptoError` con el
      tipo real en el mensaje.
      **PROHIBIDO**: añadir `AttributeError` a la tupla, o `except Exception` en `load()`
      (`proposal.md` §3.3; P7 mata ambos).
- [x] **P4 `test_forma_legacy_no_tumba_la_app`**: `{"profiles": "texto"}` y `{"profiles": {"x": 123}}`
      con `.bak` sano → `PackService()` **no revienta** y recupera del backup. **Hoy falla con
      `AttributeError`: este es el bug, no un test tautológico.**
- [x] `pack_service.py:59-61`: **NO** es bloqueante, pero deja anotado en `data-models.md` que la ruta
      de regeneración **escribe dos veces** (`_ensure_gaming_pack` ya llama a `save()`), que es la
      razón mecánica por la que un espía de llamadas no puede funcionar. Si el mutation-auditor lo
      exige, se elimina el `self.save()` redundante **en el mismo commit**.

## 4. Extra FIX-007 — el cuelgue de Tcl · **PRIORIDAD 2**

- [x] **P8 `test_do_load_publica_sin_tk`**: subclase de `ProcessManagerView` con `processes` y
      `grouped_processes` como **propiedades que anotan `threading.get_ident()`**; instancia vía
      `__new__` (sin `__init__`, sin `CTk`, sin `root`, sin `mainloop`), `after` falso que **encola**,
      y doble de `ProcessService`. El test **hace de bucle de eventos**: `join(10)` al hilo y
      ejecución en el principal de lo entregado. Afirmaciones: ninguna escritura desde el secundario,
      al menos una publicación desde el principal, sin mutación in situ del dict que el principal
      itera, y coherencia `grouped == _group(processes)` tras ejecutar lo publicado.
      **Mata**: la reintroducción de la publicación desde el hilo (verificado:
      `'processes' se publicó desde el hilo 24336, no desde el principal (17776)`).
- [x] **Eliminar** el `faulthandler.dump_traceback_later(150, exit=True)` del test de FIX-007: mata
      el runner entero y por tanto todos los tests posteriores. Con el arnés sin Tk no hay bloqueo en
      Tcl, así que el reloj de guardia sobra.
- [x] **Conservar** el guard `ast` de la fase D (prohíbe `self.master.after`, TASK-023): es una
      comprobación distinta y válida. Deja de ser la **única** red que detecta la mutación.
- [x] Conservar las fases de **dos cargas solapadas** y la **puerta por `Event` sin `sleep`**.

## 5. Documentación viva y cierre

- [x] `docs/ai/data-models.md`: contrato de clasificación de `profiles.json` (qué es corrupción, qué
      no, y que solo `PerfilCorruptoError` de forma puede "lavarse" como corrupción) + la nota del
      doble volcado de §3.
- [x] `docs/ai/testing-guide.md`: las sondas P1–P8, **por qué existe cada una** y qué mutación mata.
      Registrar que en Windows `chmod` solo niega escritura, luego toda prueba de permisos por
      filesystem es ciega a la clasificación de `OSError`.
- [x] P1–P8 registradas en el `__main__` de `run_tests.py`, con los `print()` en **ASCII puro**
      (Trampa #6, consola cp1252).
- [x] `python run_tests.py`, `python verify_ui_syntax.py`, `python validate_docs.py` en verde.
- [x] **Reejecutar la matriz de mutación de `proposal.md` §0** con los tests finales: las 8 sondas
      matan su mutación y el escenario ARREGLO sale TODO VERDE. Sin esto, el ciclo no se cierra.
- [x] Cero cambios fuera de `pack_service.py`, `run_tests.py`, los dos `docs/ai/` y este change.

---

## 6. Matriz de mutación MEDIDA con los tests finales

Reejecutada el 2026-09-30 reconstruyendo la matriz desde el **texto** de `src/` y cargando la copia
mutada con `importlib` bajo el nombre real del módulo (nunca se escribe dentro del repo). Cada
escenario es un proceso limpio; `BASE` = el código entregado.

| Escenario | Sondas que lo matan | Veredicto |
|---|---|---|
| **BASE** (código entregado) | ninguna (las 9 verdes) | TODO VERDE |
| M1 `os.replace`+temporal → `open(w)` directo | **P1** (×4) + **P3** | ✅ |
| M2 `os.replace` → `shutil.copyfile` | **P1b** (+ P2 de rebote) | ✅ |
| M3 no borra el `.tmp` al fallar | **P1** | ✅ |
| M4 `except Exception: pass` | **P1** | ✅ |
| M5 `CORRUPTION_ERRORS` → solo `JSONDecodeError` | **P5** (+ P4) | ✅ |
| M6 `OSError` readmitido en la tupla | **P2** + **P6** (+ P4) | ✅ |
| M7 `load()` → `except Exception` (bug del ciclo 15) | **P6** + **P7** | ✅ |
| M9 `AttributeError` en la tupla (arreglo ingenuo) | **P7** (+ P4) | ✅ |
| M10 el `.tmp` en otro volumen/directorio | **P1** + **P3** (+ P1b, P2 de rebote) | ✅ |
| **M12** sin guarda de forma en la rama legacy (**el bug de P4**) | **P4** | ✅ |
| M13 FIX-007: el secundario publica en vez de encolar | **P8** (`'processes' se publico desde el hilo 25080, no desde el principal (29100)`) | ✅ |
| ARREGLO + reintroducir `OSError` (= M6 sobre el código ya arreglado) | **P2** + **P6** | ✅ el arreglo no tapa la regresión |

### Corrección de la tabla de §0, medida

- **P2 mata M6, no M7.** La fila de §0 (y la de `proposal.md` §5) le atribuía M7 a P2, pero la propia
  §2.1 del proposal lo desmiente: en D2 el código correcto y el mutante hacen `save()=1, volcados=1`
  y terminan lanzando el mismo `PermissionError` desde el mismo sitio. **M7 se mata por el lado de
  `load()`**, que es donde está su daño: lo matan **P6** y **P7**. La cobertura de M7 no se pierde,
  cambia de sonda. El docstring de P2 lo dice explícitamente para que nadie lea verde por la razón
  equivocada.
- **P1 no mata M2** (ni puede: con `copyfile` el volcado sí va al temporal, así que sus aserciones
  de bytes pasan). Por eso existe **P1b**, con un `copyfile` hostil.
- M2 y M10 matan además P1b/P2 **de rebote** (`copyfile` no borra el temporal; un temporal en una
  ruta inexistente revienta el `open`). La muerte nombrada de cada mutación es la de su fila.
- **M12** no estaba en la matriz del arquitecto: es la *ausencia* de la guarda de forma de §4.3,
  y es lo que hace que P4 no sea tautológico.
- **M13** se construyó para que **pase** la guarda `ast` de la fase D (`self.after(0, _apply)` →
  `_apply()` deja la asignación dentro de `_apply`, que sigue siendo destino de un
  `self.after(0, ...)`). Así se demuestra que la red de **runtime** de P8 detecta la reintroducción
  por sí sola, y no solo la estática.

### Deuda que queda registrada, no resuelta

- `pack_service.py`: la ruta de regeneración de `load()` **escribe dos veces** (`_ensure_gaming_pack()`
  ya llama a `save()` + el `self.save()` redundante). Documentado en `data-models.md` §4.3 como
  candidato a tarea; no bloqueante, no se ha tocado.
- El mensaje de `save()` en P2 puede no ser el ideal si la mutación que lo mata es colateral (M2
  lo mata por el temporal que `copyfile` deja, no por la rotación). No afecta a la discriminación:
  el test muere y el mutante no pasa.
