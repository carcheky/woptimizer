# Tareas — Ciclo 73: `2026-10-24-proteger-y-acciones-claras`

Contrato completo en **`proposal.md`** (mismo directorio). Aquí está el **desglose ejecutable**: quién toca qué, en qué fichero, en qué línea, y cómo se sabe que está hecho.

> **Regla del ciclo:** cada tarea se cierra con su **test** en verde. Ninguna tarea se cierra "a ojo". Si un criterio no tiene test, está marcado como **[REVISIÓN]** y dice POR QUÉ no lo tiene.

> **Prohibido tocar** en este ciclo: `src/woptimizer/services/process_service.py`, `src/woptimizer/ui/confirmation.py`, y cualquier fichero fuera de los listados abajo salvo los 6 del recuento (§T-073.3).

---

## Mapa de dependencias

```
T-094.1 (dropdown + resolver)
   └─> T-094.2 (botón "🔒 Proteger" + trace_add)
          └─> T-094.3 (on_add_to_pack: rama proteger + repintado + aviso)
                 └─> T-094.4 (test del caso límite: proteger y matar sin repintar)

T-095.1 (feedback.py: vocabulario)   ── independiente, se puede hacer primero
   └─> T-095.2 (Gestor de Packs: etiqueta + español)
T-095.3 (dashboard: tarjeta con 2 botones)  ── necesita T-095.1 (ETIQUETA_*)
   └─> T-095.4 (execute_pack: acción explícita + token por acción)
          └─> T-095.5 (test de la Portada)

T-073.3 (recuento de tests: 235 → 239)  ── se hace AL FINAL, cuando los 4 tests existen
```

---

## TASK-094 — Proteger una app desde el Gestor de Procesos

**Prioridad:** alta. **Fichero principal:** `src/woptimizer/ui/views/process_manager_view.py`.

### T-094.1 — El desplegable ofrece el pack de protegidos (al final, y el que el servicio honra)

- **Fichero:** `src/woptimizer/ui/views/process_manager_view.py`
- **Líneas:** **20** (nueva constante `ETIQUETA_PROTEGIDA`), **227-234** (`_update_pack_dropdown`)
- **Qué hace:**
  1. Añadir la constante de módulo `ETIQUETA_PROTEGIDA = "🛡️ Aplicaciones Protegidas"`. **Copiar el glifo de `pack_manager_view.py:229`** (que ya usa 🛡️) — **carácter a carácter**, no de memoria. No reescribir a mano.
  2. `_update_pack_dropdown()` deja de filtrar `if not p.is_protected` (línea 229) y **construye la lista explícitamente**:
     - primero, los packs que **no** son el protegido (los de hoy, en el orden de hoy);
     - después, la etiqueta protegida, **obtenida de `self.pack_service.get_protected_pack()`** (`pack_service.py:1365`) — **el mismo pack que honra `get_protected_apps()`** (`pack_service.py:1372`).
  3. La entrada protegida va **siempre al final**: `values[0]` **no** puede ser el pack protegido, porque la línea 234 (`pack_var.set(values[0])`) cae sobre él cuando la selección vigente deja de estar en la lista.
- **Por qué así:** `get_protected_pack()` devuelve el **primero** con `is_protected=True`; ofrecer "cualquier pack con el flag" sería ofrecer una protección que **el motor ignora** (propuesta R-3).
- **Aceptación:**
  - La lista del desplegable **contiene** `ETIQUETA_PROTEGIDA` **y** la contiene **al final**.
  - El pack que corresponde a esa entrada es `pack_service.get_protected_pack()` (id `protected_apps`), no "alguno con el flag".
  - La lista **sigue** conteniendo los packs normales **y** el pack Gaming (que hoy también está: el filtro de la línea 229 solo excluía `is_protected`).
- **Test:** cubierto por **AC-1** (`test_el_gestor_de_procesos_ofrece_el_pack_de_protegidas_y_lo_protege`), aserto (a).

### T-094.2 — El botón se redibuja: "🔒 Proteger" / "➕ Añadir al Pack"

- **Fichero:** `src/woptimizer/ui/views/process_manager_view.py`
- **Líneas:** **111-131** (`pack_var`, `pack_dropdown`, `btn_add_pack`), **nuevo** justo después de **131** (el `trace_add`), **nuevo** método `_refrescar_texto_del_boton`
- **Qué hace:**
  1. **NO** usar `command=` del `CTkOptionMenu`. Usar `self.pack_var.trace_add("write", ...)` — **el mismo idioma que `search_var`** (`process_manager_view.py:82`). Motivo medido: la línea **234** hace `pack_var.set(...)` **por código** y `command=` **no** se dispara ahí → el botón quedaría diciendo "🔒 Proteger" con un pack normal seleccionado.
  2. Registrar el `trace_add` **después** de que exista `btn_add_pack` (si se registra antes, el trace dispara con el botón inexistente).
  3. `_refrescar_texto_del_boton()`: lee `self.pack_var.get()`; si es la etiqueta protegida → `"🔒 Proteger"`; en cualquier otro caso (incluido `PLACEHOLDER_PACK`) → `"➕ Añadir al Pack"`.
  4. Llamar a `_refrescar_texto_del_boton()` **una vez** al construir, para que el texto inicial sea correcto.
- **Aceptación:**
  - Seleccionar la entrada protegida (por usuario **o** por `pack_var.set()`) → el botón dice `"🔒 Proteger"`.
  - Volver a un pack normal (o al placeholder) → el botón vuelve a `"➕ Añadir al Pack"`.
  - El caso **por código** (`pack_var.set(values[0])`, línea 234) también actualiza el texto. **Este es el discriminante**: es exactamente lo que `command=` no vería.
- **Test:** AC-1 (extensión) — el botón se comprueba con el doble `_Var`/`_Label` que ya existe (`run_tests.py:5984-5996`), **sin Tk**.

### T-094.3 — `on_add_to_pack`: rama de protección (guardar, repintar, avisar con honestidad)

- **Fichero:** `src/woptimizer/ui/views/process_manager_view.py`
- **Líneas:** **435-467**, más un **nuevo** método `_pack_objetivo_de_la_seleccion`
- **Qué hace:**
  1. **Sustituir la búsqueda por nombre** de la **línea 444** (`next((p for p in packs.values() if p.name == pack_name), None)`) por el resolver `_pack_objetivo_de_la_seleccion()`:
     - si la selección es la etiqueta protegida → `self.pack_service.get_protected_pack()`;
     - si no → búsqueda por **nombre exacto** en `get_all_packs()` (el comportamiento de hoy, sin cambios).
     - **Motivo:** el nombre real del pack es `"Aplicaciones Protegidas"` (`pack_service.py:274`) y la etiqueta lleva prefijo → la búsqueda por nombre **falla** sin el resolver (propuesta R-2).
  2. **Rama de protección**: cuando el destino es el pack protegido, guardar `os.path.basename(exe_name).lower()` (**basename en minúsculas**) en vez de la ruta absoluta de la línea 456. Los packs **normales** **siguen** guardando la ruta absoluta (contrato vivo en `run_tests.py:6064`).
     - *Si se decide no meter `os` en la vista*: pedirlo al servicio (`pack_service.añadir_app_protegida`) — es la lectura más limpia de la separación de capas (propuesta R-7). **Es una decisión del dev, pero debe quedar JUSTIFICADA en el changelog del pase.**
  3. Tras `update_pack(target_pack)` (línea **466**), **repintar la lista** (`self._render_list()`): la app protegida **desaparece** de la lista (es lo que ya hace TASK-071 al pintar, líneas 248 y 253-257).
  4. El mensaje de `status_label` **distingue el caso "0 añadidas"** (la app ya estaba protegida) del caso normal → **no** decir "✅ 0 apps" en verde en la rama de protección. **La rama NORMAL no cambia de texto** (`run_tests.py:6094` fija `"✅ 0 apps"` para el duplicado y **no se toca**).
  5. El mensaje de éxito dice que la app **queda protegida** (no "añadida a un pack"), porque la consecuencia es "no se cerrará".
- **Aceptación:**
  - Con la entrada protegida seleccionada: lo **persistido** en el pack protegido es el **basename en minúsculas**, y `update_pack()` se llama **una** vez.
  - Tras proteger, la lista **se repinta** y la app **ya no está** en ella.
  - `status_label` dice algo distinto de "✅ 0 apps" cuando no se añadió nada.
  - El pack normal **sigue** guardando la ruta absoluta (no se rompe `test_el_gestor_guarda_la_ruta_absoluta`).
- **Test:** AC-1 — los asertos (b), (c), (d). El doble de `run_tests.py:5998-6029` **devuelve copias defensivas**, así que leer la copia de la vista **NO** vale: hay que leer lo que el doble **persistió**.

### T-094.4 — Test del caso límite: **proteger y matar sin repintar**

- **Fichero:** `run_tests.py` (nuevo `test_*`, después del marcador de `run_tests.py:33375`)
- **Nombre:** `test_proteger_y_matar_sin_repintar_no_mata_la_app`
- **Qué mide:** con un `ProcessService` **real** y un `pack_service` cuyo `get_protected_apps()` devuelve la app protegida: `kill_processes([proceso])` → `killed == 0`, `failed == 0`, **`skipped == 1`**, y **`psutil` no se alcanza**.
- **Por qué no es vaciable:** el discriminante es el aserto **`failed == 0`**. Si la relectura en caliente (`process_service.py:540-543`) desapareciera, el proceso **no** estaría en `protected_apps` → el kill intentaría matarlo → `psutil.Process(pid)` → `NoSuchProcess` → **`failed == 1` en vez de `skipped == 1`**. Con un pid inexistente, que `failed` siga en 0 **prueba** que `psutil` no se alcanzó. **Es seguro**: nunca se mata nada real, porque el proceso se salta **antes** de `psutil.Process`.
- **Qué NO hay que hacer:** **no** tocar `process_service.py`. El kill **ya** respeta la protección; este test **congela** ese comportamiento para que nadie lo rompa sin darse cuenta.

---

## TASK-095 — La acción por defecto se entiende

**Prioridad:** media. **Ficheros:** `src/woptimizer/ui/feedback.py`, `src/woptimizer/ui/views/dashboard_view.py`, `src/woptimizer/ui/views/pack_manager_view.py`.

### T-095.1 — `feedback.py`: el vocabulario de acciones (UNA fuente)

- **Fichero:** `src/woptimizer/ui/feedback.py`
- **Qué hace:** añadir
  ```
  ETIQUETAS_ACCION = {"kill": "Parar", "start": "Iniciar"}
  ETIQUETA_APAGAR  = "⛔ Apagar"
  ETIQUETA_INICIAR = "🚀 Iniciar"

  def etiqueta_accion(accion: str) -> str            # KeyError si la acción no es del dominio
  def accion_desde_etiqueta(etiqueta: str) -> str   # KeyError si la etiqueta no es del dominio
  ```
- **Por qué aquí:** `feedback.py` es **puro** (ni `tkinter`, ni `customtkinter`, ni `psutil`, ni `json`, ni `services`, ni `models` — ver su docstring) y ya centraliza el vocabulario de acciones (`VERBOS`, `feedback.py:199`). Una función de traducción sin dependencias es testeable **sin ventana**.
- **Por qué `KeyError` y no un default:** `feedback.py:244-251` (`_verbo`) ya usa esa disciplina. El dominio es **total** (`models.py:84`), así que una etiqueta desconocida **es un bug**, no un caso de negocio.
- **Glifos:** `ETIQUETA_APAGAR` y `ETIQUETA_INICIAR` se **copian** de `pack_manager_view.py:284` y `pack_manager_view.py:296` (carácter a carácter).
- **Aceptación:**
  - `etiqueta_accion("kill") == "Parar"`, `etiqueta_accion("start") == "Iniciar"`.
  - `accion_desde_etiqueta("Parar") == "kill"`, `accion_desde_etiqueta("Iniciar") == "start"`.
  - Ida y vuelta para las dos.
  - Etiqueta o acción **desconocida** → `KeyError` (no un valor por defecto).
  - El módulo sigue siendo puro: **no** importa nada nuevo.

### T-095.2 — Gestor de Packs: etiqueta "Acción por defecto:" y valores en español

- **Fichero:** `src/woptimizer/ui/views/pack_manager_view.py`
- **Líneas:** **257-269** (`change_default`), **271-280** (`combo_action`)
- **Qué hace:**
  1. `combo_action`: `values=["Parar", "Iniciar"]` (las **etiquetas**, no las acciones crudas).
  2. Añadir un `CTkLabel` con `text="Acción por defecto:"`, `font=("Segoe UI", theme.FONT_SIZE_TINY)`, empaquetado **justo antes** del combo (`side="left"`).
  3. **Línea 279** `combo_action.set(pack.default_action)` → `combo_action.set(etiqueta_accion(pack.default_action))`. ⚠️ **Sin esto el desplegable muestra "kill"**, un valor que ya no está en `values`. **Es el bug más probable si el cambio se hace a medias.**
  4. `change_default` (línea **257**): `p.default_action = accion_desde_etiqueta(choice)` — **traducir ANTES de asignar**. Si se asignara la etiqueta cruda, `Pack.default_action` (`Literal`, `models.py:84`) **rechazaría** el valor → `ValidationError` al guardar → **el pack se corrompe**.
  5. **Líneas 284 y 296**: los literales `"⛔ Apagar"` / `"🚀 Iniciar"` → `ETIQUETA_APAGAR` / `ETIQUETA_INICIAR` (de T-095.1). Motivo: la Portada añadirá dos copias más; cuatro copias de la misma frase es el defecto que este repo ya pagó con el literal `"KILL"` congelado (`dashboard_view.py:403-408`).
- **Aceptación:**
  - El desplegable muestra **"Parar"/"Iniciar"** y tiene la **etiqueta** "Acción por defecto:".
  - Al abrir un pack, el desplegable muestra la **etiqueta** de su `default_action` ("Parar" si es "kill"), **nunca** el literal crudo.
  - Al elegir "Parar", lo **persistido** es `"kill"`.
  - El `profiles.json` contiene `"default_action": "kill"`.
  - La cabecera no se rompe con la etiqueta nueva → **[REVISIÓN]** visual (el `right_box` de la cabecera es una barra horizontal; si el texto se parte, `theme.FONT_SIZE_TINY` y `wraplength`, o mover el desplegable a una segunda línea).
- **Test:** **AC-4** (`test_la_etiqueta_de_accion_va_y_vuelve_sin_tocar_el_dato_persistido`), asertos (a), (b), (c), (d), (e).

### T-095.3 — La Portada: la tarjeta pasa a ser un frame con etiqueta + 2 botones

- **Fichero:** `src/woptimizer/ui/views/dashboard_view.py`
- **Líneas:** **9-13** (imports), **35** (registro), **294-299** (destruir), **326-346** (regrid), **348-397** (`refresh_dashboard`), **399-413** (texto), **415-439** (crear)
- **Qué hace:**
  1. **9-13**: importar `ETIQUETA_APAGAR` e `ETIQUETA_INICIAR` de `feedback`.
  2. **35**: `self._buttons_by_pack_id` **cambia de semántica**: guarda **tarjetas** (frames), no botones. **Renombrar** a `self._cards_by_pack_id` (o documentarlo con claridad): el nombre "buttons" con frames dentro es la trampa que hace que un dev futuro `btn.configure(...)` sobre un frame reviente en runtime.
  3. **294-299**: `_destroy_favorite_buttons()` → sobre un **frame**, `destroy()` destruye también los hijos → **la lógica no cambia**; renombrar y actualizar el comentario.
  4. **326-346**: la **344** `btn = self._buttons_by_pack_id.get(pack.id)` → ahora es la **tarjeta**; la **346** `btn.grid(..., sticky="nsew")` → igual, pero `sticky="nsew"` ahora hace crecer el frame. **Dentro** del frame, los dos botones van en una **sub-rejilla de 2 columnas** (o `pack(side="left", expand=True)`).
  5. **348-397**: las **380-386** registran la **tarjeta**; las **391-397** reconfiguran **los dos** botones (texto, comando y **resaltado**). **Extraer** un helper `_actualizar_tarjeta(pack, tarjeta)` usado por **las dos ramas**, para que no haya dos políticas de texto.
  6. **399-413**: `_get_pack_button_text()` deja de ser el texto del **botón** y pasa a ser el texto de la **etiqueta** de la tarjeta: **se quita** el `· {pack.default_action.upper()}` de las líneas **411-412** y **413**. Reescribir el comentario de **400-408** (explica por qué la tarjeta ya no afirma la acción: ahora la afirma cada botón, uno al lado del otro).
  7. **415-439**: `_create_favorite_button()` → **`_create_favorite_card(pack, row, col) -> ctk.CTkFrame`**: crea el frame, la etiqueta y los **dos** botones (`ETIQUETA_APAGAR` con doble pulsación, `ETIQUETA_INICIAR` sin ella), guarda referencias a ambos en la tarjeta (para poder reconfigurarlos) y devuelve el frame.
     - **Altura**: el `height=120` de la línea **422** era el del botón; con etiqueta + 2 botones la tarjeta necesita más alto (o `height="auto"`).
     - **Ancho**: `theme.ANCHO_MIN_CARD = 280` (`theme.py:52`). Dos botones en paralelo necesitan ~2×130 px → **cabe, pero justa**. Si el texto se parte → apilar verticalmente.
  8. **Orden de los botones: FIJO** `[⛔ Apagar] [🚀 Iniciar]`. El destacado cambia de **aspecto**, no de **posición** (propuesta D-2.8).
  9. **Resaltado (D-2.7):** el de por defecto → `fg_color` = color de su acción (`theme.DANGER` / `theme.ACCENT`), `border_width=2`, `border_color=theme.TEXT_PRIMARY`. El otro → `fg_color=theme.SURFACE_ALT`, `border_width=1`, `border_color=theme.BORDER`. El **grosor de borde** es la pista que **no depende del color** (accesibilidad). **Solo tokens de `theme`**: nada de literales hex (guard `test_no_literal_colors_in_views`, `run_tests.py:1034`).
- **Aceptación:**
  - La tarjeta tiene **exactamente 2** botones.
  - El botón **destacado** es el de `pack.default_action`.
  - La etiqueta de la tarjeta **no** contiene `"KILL"` ni `"START"`.
  - Ambos botones miden **≥ 28×28** (guard `test_hit_targets_minimum`, `run_tests.py:1035`).
  - Ningún color literal en la vista.
- **Test:** **AC-3** (`test_la_portada_tiene_dos_botones_y_el_por_defecto_manda`), asertos (a), (b), (e).

### T-095.4 — `execute_pack`: la acción la decide el **botón pulsado**, y el token es **por acción**

- **Fichero:** `src/woptimizer/ui/views/dashboard_view.py`
- **Líneas:** **457-530**
- **Qué hace:**
  1. Firma: `execute_pack(self, pack, button=None, accion=None)`. Si `accion is None`, se deduce de `pack.default_action` (compatibilidad con cualquier llamada existente).
  2. **Línea 472**: `if pack.default_action == "kill":` → **`if accion == "kill":`**. Este es el cambio de fondo: con dos botones, **el botón decide la acción**.
  3. **Líneas 481 y 505**: `mensaje_banner_sin_apps(pack.name, pack.default_action)` → `mensaje_banner_sin_apps(pack.name, accion)`. Si no, pulsar "Apagar" en un pack sin apps imprimiría "no hay apps que **iniciar**".
  4. **Línea 488**: el token de la doble pulsación → `f"dashboard:{pack.id}:{accion}"`. **Motivo medido**: `confirmation.py:256-264` (`_recordar_reposo`) guarda el estado de reposo **indexado por token** y **solo escribe si el token no está ya** → con un token compartido, el segundo botón **restauraría el estado del primero**.
  5. La rama de inicio (línea **500** `self._cancel_confirm()`) **se queda**: pulsar "Iniciar" **cancela** cualquier confirmación de apagado pendiente.
  6. El comando de cada botón: `lambda p=pack, b=btn, a=accion: self.execute_pack(p, b, a)`.
- **Aceptación:**
  - Con `default_action == "kill"`, pulsar **"🚀 Iniciar"** **no** mata y **sí** arranca.
  - Con `default_action == "start"`, pulsar **"⛔ Apagar"** **no** arranca y **sí** mata.
  - La doble pulsación sigue **solo** en "Apagar".
  - Los dos botones tienen **tokens distintos**.
- **Test:** **AC-3**, asertos (c) y (d).

### T-095.5 — Test de la Portada

- **Fichero:** `run_tests.py` (nuevo `test_*`, después del marcador de `run_tests.py:33375`)
- **Nombre:** `test_la_portada_tiene_dos_botones_y_el_por_defecto_manda`
- **Qué mide:** los asertos (a)-(e) de T-095.3 y T-095.4, con **dobles** para `pack_service`/`gaming_service`/`process_service` (patrón del repo: `ProcessManagerView.__new__` + dobles, `run_tests.py:5974-6097`; y el montaje headless con Tk de `test_main_window_navigation_transitions`, `run_tests.py:8640`).
- **Por qué no es vaciable:** (a) falla sin el fix (hoy hay **un** botón); (c)/(d) matan la implementación que **mantiene** el `if pack.default_action == "kill"` de la línea 472 (pulsar "Iniciar" en un pack con `default_action="kill"` **mataría**); (e) falla si la etiqueta se queda con `pack.default_action.upper()` de la línea 413.
- **Cómo se comprueba el "destacado":** por el **color/borde del widget** (lo que el usuario ve), no por una suposición sobre la lógica interna.

---

## T-073.3 — El recuento de tests: **235 → 239 = 159 backend + 80 headless**

- **Fichero:** `run_tests.py` (los 4 tests nuevos, **después** del marcador `--- Running Headless UI Tests ---` de la línea **33375** → cuentan como headless) + los 6 sitios escritos a mano.
- **Por qué se mueven y no se congelan:** `validate_docs.py` **no corre en CI** (`AGENTS.md`), y la lección del repo es literal — *"un guard que nadie cuenta se puede borrar sin que nada se entere"* (A-C68-1, `run_tests.py:33372-33373`). Un guard que solo vive en el validador **no lo ejecuta el pipeline ni el `mutation-auditor`** (que muta `run_tests.py`).

### Los 4 tests nuevos (los que mueven el número)

| # | Nombre | Tarea | Asertos |
|---|---|---|---|
| 1 | `test_el_gestor_de_procesos_ofrece_el_pack_de_protegidas_y_lo_protege` | T-094.1/2/3 | (a) la etiqueta protegida está en la lista; (b) lo **persistido** es el basename en minúsculas; (c) `update_pack()` **una** vez; (d) la lista se repinta; (e) el texto del botón sigue a la selección **también** por `pack_var.set()` |
| 2 | `test_proteger_y_matar_sin_repintar_no_mata_la_app` | T-094.4 | `killed == 0`, `failed == 0`, `skipped == 1` |
| 3 | `test_la_portada_tiene_dos_botones_y_el_por_defecto_manda` | T-095.3/4/5 | (a) 2 botones; (b) el destacado es el del default; (c)(d) el botón pulsado decide; (e) la etiqueta no dice KILL/START |
| 4 | `test_la_etiqueta_de_accion_va_y_vuelve_sin_tocar_el_dato_persistido` | T-095.1/2 | (a)(b) ida y vuelta; (c) `KeyError`; (d) lo persistido es `"kill"`; (e) el JSON tiene `"default_action": "kill"` |

### Los 6 sitios a mover (5 declaraciones + 1 comentario)

| # | Fichero:línea | Nuevo |
|---|---|---|
| 1 | `AGENTS.md:70` | `# 239 tests headless (no abre ventanas)` |
| 2 | `README.md:63` | `# 239 tests headless (no abre ventanas)` |
| 3 | `STATUS.md:12` | `**239 tests** (159 backend + 80 headless UI)` |
| 4 | `STATUS.md:133` | `4. **Tests:** `python run_tests.py` (239 tests)` |
| 5 | `docs/ai/testing-guide.md:59` | `Contiene **239 tests**: 159 de backend + 80 headless de UI.` |
| 6 | `validate_docs.py:2967-2969` (comentario) | Reescribir: el recuento **sube** a 239 = 159 + 80, y **por qué** (4 tests nuevos, *counted*) |

⚠️ `validate_docs.py:1248-1249` exige que `STATUS.md` declare el reparto con la forma `\d+ backend + \d+ headless` y que **coincida con el derivado por `ast`**. Si se mueve el reparto y no se mueve `STATUS.md:12`, el validador **falla**.

### Cómo se comprueba que la cifra no se mueve por accidente

1. `python validate_docs.py` → verde (check 7: total definido == total invocado; reparto derivado == lo declarado).
2. `python run_tests.py` → verde y el recuento impreso = **239**.
3. `grep -n "235" AGENTS.md README.md STATUS.md docs/ai/testing-guide.md` → **cero** coincidencias.
4. `grep -n "235" validate_docs.py` → la **única** mención es el comentario reescrito del punto 6, que ya habla de 239.

---

## T-073.4 — Documentación del ciclo

- **`docs/ai/ui-design-system.md`**: la tarjeta de la Portada (frame + etiqueta + 2 botones), el orden fijo, el resaltado (color + grosor de borde), por qué la etiqueta ya no afirma la acción, el **token por acción** de la doble pulsación y por qué, el desplegable del Gestor de Procesos construido explícitamente (entrada protegida al final, con prefijo, resolver etiqueta→pack) y la regla **`trace_add` en vez de `command=`** con el caso de `pack_var.set()` por código, y la etiqueta "Acción por defecto:" del Gestor de Packs.
- **`docs/ai/data-models.md`**: `default_action` = "la acción por defecto" = la que ejecuta el **tray** y la que se **destaca** en la Portada; el valor persistido **sigue siendo** `"kill"`/`"start"` y **no cambia**; el vocabulario "Parar"/"Iniciar" es **estrictamente presentacional** y nunca se persiste; `default_action` **ausente** ⇒ `"start"`; **inválido** ⇒ corrupción (`.bak`); `create_user_pack` nace con `"start"`.
- **`docs/ai/architecture.md`**: **nada** (no cambia ninguna frontera de capa), salvo que se opte por `pack_service.añadir_app_protegida` (R-7) → entonces se documenta el método nuevo.
- **`CHANGELOG.md`** y **`.taskmaster/CHANGELOG.md`**: los **dos**, en el pase del ciclo 73. **El changelog debe declarar** que la tarjeta de Gaming gana un botón "🚀 Iniciar" que arranca `chrome.exe` (riesgo R-8), porque es una **capacidad nueva y visible**.

---

## Checklist de cierre del ciclo

- [ ] Los **4** tests nuevos existen, están **contados** (llamados en `__main__`) y **verdes**.
- [ ] `python run_tests.py` → verde, **239 tests**.
- [ ] `python validate_docs.py` → verde (check 7 + reparto).
- [ ] `grep -rn "235" AGENTS.md README.md STATUS.md docs/ai/` → **cero**.
- [ ] `docs/ai/ui-design-system.md` y `docs/ai/data-models.md` actualizados.
- [ ] `CHANGELOG.md` + `.taskmaster/CHANGELOG.md` escritos (**ambos**).
- [ ] `verify_ui_syntax.py` → verde (las vistas han cambiado de estructura).
- [ ] **Cero** cambios bajo `src/woptimizer/services/process_service.py` y `src/woptimizer/ui/confirmation.py`.
- [ ] El commit lo hace el bucle con `python .taskmaster/git_safe_commit.py "<mensaje> (TASK-094)"` — **con identificador**, o el wrapper responde `WOPT_USAGE ancla-mensaje` y sale con **2**.
- [ ] Rama `beta`. **`main` no se toca.**
