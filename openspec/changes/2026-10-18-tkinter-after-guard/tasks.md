# TASK-073 — Plan de ejecución

Contrato: `proposal.md`. Todo lo de aquí lo ejecuta **`openspec-dev`** (Paso 3).
Cero ediciones bajo `src/woptimizer/**` en el Paso 2 (este rol).

Orden obligatorio: **T1 → T2 → T3 → T4**. T3 no se puede hacer antes de T2, y sin T4 la suite queda
en rojo por diseño (F4 de `proposal.md`).

---

## T1 · `src/woptimizer/ui/tk_thread.py` — NUEVO

Una función. Sin estado de clase, sin imports de Tk (`confirmation.py:21-25` prohíbe `tkinter` a
nivel de módulo, y esta función no lo necesita: solo llama a un método del widget que recibe).

- [ ] `publicar_en_bucle(widget, delay_ms, callback, *args) -> Any`
- [ ] `return widget.after(delay_ms, callback, *args)` dentro de `try`
- [ ] `except Exception: return None` — y **el comentario dice las DOS razones**, no una:
      `RuntimeError` sin bucle principal (el caso headless de `run_tests.py`) y `tk.TclError` si la
      vista murió entre la decisión y la llamada.
- [ ] Docstring con las **mediciones** del 2026-10-18, porque el guard que se descartó es el que
      un próximo agente va a proponer otra vez:
      - `winfo_exists()` desde un hilo secundario lanza `RuntimeError: main thread is not in main
        loop` **también con la ventana viva** → un probe de existencia no funciona aquí.
      - con `mainloop()` vivo, `after(400)` programado y la ventana destruida 150 ms después, el
        callback **nunca se ejecuta**: Tk lo descarta con el widget. Por eso no hace falta sonda de
        existencia, y por eso un `try/except` solo es la solución completa.
- [ ] ❌ **NO** añadir `winfo_exists()`. Está medido que no aporta y que puede fallar por sí mismo.

## T2 · `src/woptimizer/ui/confirmation.py` — EDITAR

- [ ] `from woptimizer.ui.tk_thread import publicar_en_bucle` (respetar el estilo de import del
      módulo; cuidado con **import circular**: `tk_thread` no importa nada de `woptimizer`).
- [ ] Método `_publicar_en_el_bucle(self, delay_ms, callback, *args)` junto a `_schedule_ui` (`:273`).
- [ ] Actualizar la autodescripción **"QUE HAY DENTRO (dos capas, y solo dos)"** (`:14-19`): sigue
      siendo cierto, pero hay que decirlo bien — la tercera pieza es una **delegación**, y la lógica
      vive en `tk_thread.py`. Un docstring que miente sobre su propio contenido es la clase de deuda
      que este ciclo vino a cerrar.
- [ ] ❌ **NO** tocar `_schedule_ui` (`:273-288`). Se evaluó reutilizarlo y se descartó: registra el
      handle en `self._timers_ui` (`:287`) y `cancel_on_destroy` lo itera en el hilo principal
      (`:179`), luego hacerlo desde un worker es una mutación de `set` entre dos hilos.

## T3 · Los 10 call sites — EDITAR las TRES vistas

Sustituir `self.after(0, ...)` por `self._publicar_en_el_bucle(0, ...)`. **Los 10**, no los 5:

- [ ] `views/process_manager_view.py:179` — `self._publicar_en_el_bucle(0, self._do_load)`
- [ ] `views/process_manager_view.py:194` — `self._publicar_en_el_bucle(0, _handle_err)`
- [ ] `views/process_manager_view.py:202` — `self._publicar_en_el_bucle(0, _handle_ok)`
- [ ] `views/process_manager_view.py:209` — `self._publicar_en_el_bucle(0, self._apply_load, procs)`
- [ ] `views/process_manager_view.py:407` — `self._publicar_en_el_bucle(0, self._publicar_cierre, ...)`
- [ ] `views/dashboard_view.py:279`
- [ ] `views/dashboard_view.py:491`
- [ ] `views/dashboard_view.py:522`
- [ ] `views/pack_manager_view.py:679`
- [ ] `views/pack_manager_view.py:722`

- [ ] Actualizar el comentario de `process_manager_view.py:26-29`, que hoy afirma el invariante como
      *"un worker solo publica por `self.after(0, ...)`"*. Si no se toca, la documentación miente
      sobre el invariante que este ciclo acaba de cambiar.

## T4 · `run_tests.py` — EDITAR (sin esto la suite queda en ROJO)

### T4.1 · Extender el guard de `run_tests.py:8897` — **OBLIGATORIO, va primero**

`test_los_workers_de_pack_solo_publican_por_after` marca como infracción **todo** lo que no sea
`self.after` (`if raiz != "after":`). Con T3 aplicado, los 10 call sites caen en esa rama y la suite
se pone en rojo. Por diseño, no por error.

- [ ] **Una rama nueva**, no un par nuevo en `PERMITIDOS`: cuando `raiz == "_publicar_en_el_bucle"`,
      exigir **exactamente lo mismo** que ya se exige a `self.after` (`run_tests.py:8916-8920`):
      delay constante `0` y `call.args[1].attr` dentro de `CALLBACKS`.
- [ ] ❌ **NO** añadir `("_publicar_en_el_bucle", "_publicar_en_el_bucle")` a `PERMITIDOS`. Sería el
      arreglo de una línea, y degradaría el guard: las comprobaciones de 0 ms y de callback en lista
      blanca **solo se aplican a la rama `raiz == "after"`**, luego el helper quedaría publicando a
      3000 ms y a un callback cualquiera sin que nadie lo viera.
- [ ] Contraprueba: mutar la rama para que acepte `3000` tiene que poner el test en rojo.

### T4.2 · `test_publicar_en_el_bucle_no_programa_si_la_vista_ya_murio`

Doble `_VistaFalsa` con `llamadas: list`; `after(...)` **registra y lanza** el `RuntimeError` real.

- [ ] Caso A (vista muerta): `llamadas == []`, `handle is None`, sin excepción.
      **`llamadas == []` es la aserción que hace el test discriminante**: con el guard quitado,
      `after` se invoca, el `except` se traga el error y un test que solo comprobara "no revienta"
      saldría verde.
- [ ] Caso B (vista viva, `after` devuelve `"after#1"`): `llamadas == [(0, cb, (1, 2))]` y
      `handle == "after#1"`. Mata el mutante degenerado que nunca programa nada.
- [ ] Caso C (vista viva, `after` revienta): `handle is None`, sin excepción, `llamadas` con **una**
      entrada.
- [ ] El doble debe ser una **instancia real** de la clase importada del módulo, no una copia de la
      lógica: una réplica no la tocaría al mutar, que es el fallo que este ciclo viene a matar.

### T4.3 · `test_ninguna_vista_programa_after_a_mano` (anti-regresión)

- [ ] `ast` sobre los **tres** ficheros de `src/woptimizer/ui/views/`: cero atributos `self.after`.
- [ ] **Contraprueba, que es la mitad que discrimina**: la misma detección aplicada a un fragmento
      sintético con `self.after(0, f)` tiene que marcarlo, y a uno con
      `self._publicar_en_el_bucle(0, f)` no. Sin esto el test es decorativo: es el fallo exacto de
      `test_ninguna_llamada_de_cat_file_batch_check_se_queda_sin_input`, donde la detección existía,
      no veía, y `for argumento in []` dejaba la suite verde (`docs/ai/testing-guide.md:1293`).
- [ ] **Control negativo**: el guard no puede ser "marca todo". Exigir que un worker conforme queda
      limpio.

### T4.4 · Registro

- [ ] Añadir las 2 invocaciones **detrás del marcador headless** (al final, junto a las de TASK-071).
- [ ] No renumerar a mano las filas de `docs/ai/testing-guide.md`: el reparto se deriva.

---

## T5 · Documentación viva (AGENTS.md §"Documentación Viva Obligatoria")

- [ ] `docs/ai/ui-design-system.md` — contrato de publicación worker→main: `self.after` **prohibido**
      en `views/`; la única puerta es `self._publicar_en_el_bucle`. Con la medición de por qué no hay
      sonda de existencia.
- [ ] `docs/ai/testing-guide.md` — tabla de reparto **203 → 205** (142 backend + **63** headless) y
      las 2 filas nuevas con su columna de "MATA".
- [ ] `STATUS.md` — deuda liquidada en "Últimos Hitos" y **corregir la referencia "fila 122"**: son
      hoy 121 líneas, la Deuda Técnica Conocida está en la **línea 58** y TASK-073 estaba en la tabla
      de backlog, **línea 33** (F6). Ojo a los glifos: 🟡 es `U+1F7E1` y `⚪ Otros` es `U+26AA`, no la
      interrogación ASCII (`docs/known-issues.md`).
- [ ] `CHANGELOG.md` **y** `.taskmaster/CHANGELOG.md` — los dos, o `validate_docs.py` falla.

---

## Comandos de verificación

```bash
python run_tests.py                                   # 205 verde, con T4.1 aplicado
python verify_ui_syntax.py
python validate_docs.py
python .taskmaster/git_safe_commit.py "fix(ui): publicar en el bucle de Tk sin RuntimeError (TASK-073)"
```

> `fix:` → patch en `semantic-release`. El mensaje **lleva identificador** o el wrapper responde
> `WOPT_USAGE` y sale con `2` (TASK-059). Rama `beta`, nunca `main`.

## Lo que NO es de este ciclo

- `get_gaming_pack()` inalcanzable y el guard de `SYSTEM_PROTECTED_PROCESSES`: de otros encargos.
- `validate_docs.py` en CI (TASK-075) y flags de PyInstaller (TASK-076): backlog aparte.