# Propuesta — Ciclo 73: proteger desde el Gestor de Procesos + acciones claras en la Portada

- **Change ID:** `2026-10-24-proteger-y-acciones-claras`
- **Tareas:** `TASK-094` (Encargo A, prioridad alta) · `TASK-095` (Encargo B, prioridad media)
- **Estado:** PLANIFICADO. Nadie ha escrito una línea de `src/`. Esto es un contrato, no una implementación.
- **Alcance de este documento:** `src/woptimizer/ui/**` (vistas + `feedback.py`), `run_tests.py`, `validate_docs.py` (solo el arreglo del recuento), `docs/ai/**`.
- **Fichero de tareas:** `tasks.md` (mismo directorio).

> Las líneas citadas son las **reales del árbol actual**, medidas con `read`/`grep` sobre `C:\Users\carch\Nextcloud\Scripts\woptimizer` (rama `beta`). Si el dev mueve una línea, vuelve a medir: **una cita de línea equivocada es un hallazgo falso**.

---

## 0. Resumen

Dos encargos de UI que se tocan, pero no se pisan:

| | Encargo | Puerta | Efecto |
|---|---|---|---|
| **A** | `TASK-094` | Gestor de Procesos | El pack **Aplicaciones Protegidas** entra en el desplegable. Al elegirlo, el botón pasa a **"🔒 Proteger"**. Al proteger: aviso en `status_label` + repintado (la app desaparece de la lista). |
| **B** | `TASK-095` | Portada + Gestor de Packs | La Portada pasa de **un** botón por pack a **dos** (`⛔ Apagar` / `🚀 Iniciar`), con el de la **acción por defecto destacado**. El desplegable del Gestor se queda, pero con **etiqueta** "Acción por defecto:" y **valores en español** ("Parar"/"Iniciar") mapeados a `"kill"`/`"start"` al persistir. |

El dato persistido **no se mueve**: `default_action` sigue siendo `"kill"`/`"start"` en `profiles.json`, y `default_action` sigue siendo `Literal["start", "kill"]` en `models.py:84`.

---

## 1. Hechos verificados (leídos, no copiados del briefing)

### 1.1 — Encargo A (TASK-094)

**A-1. El pack protegido se EXCLUYE del desplegable.** Confirmado.

```
src/woptimizer/ui/views/process_manager_view.py:229
    values = [p.name for p in packs.values() if not p.is_protected]
```

**A-2. El desplegable no tiene callback de cambio.** Confirmado *para este desplegable* (pero ver R-1: el widget sí admite `command=`).

```
src/woptimizer/ui/views/process_manager_view.py:111   self.pack_var = ctk.StringVar(value=PLACEHOLDER_PACK)
src/woptimizer/ui/views/process_manager_view.py:112   self.pack_dropdown = ctk.CTkOptionMenu(
src/woptimizer/ui/views/process_manager_view.py:115       values=[PLACEHOLDER_PACK],
src/woptimizer/ui/views/process_manager_view.py:121   self.btn_add_pack = ctk.CTkButton(
src/woptimizer/ui/views/process_manager_view.py:123       text="➕ Añadir al Pack",
```

`PLACEHOLDER_PACK = "Seleccionar Pack"` (`process_manager_view.py:20`).

**A-3. `on_add_to_pack` busca el pack destino POR NOMBRE.** Este es el punto que rompe el diseño ingenuo (ver D-1.2).

```
src/woptimizer/ui/views/process_manager_view.py:435   def on_add_to_pack(self):
src/woptimizer/ui/views/process_manager_view.py:444       target_pack = next((p for p in packs.values() if p.name == pack_name), None)
src/woptimizer/ui/views/process_manager_view.py:456       exe_name = exe_path or procs[0].full_name or procs[0].name
src/woptimizer/ui/views/process_manager_view.py:466       self.pack_service.update_pack(target_pack)
```

**A-4. La lista se filtra al PINTAR, contra el pack de protegidos.** Confirmado.

```
src/woptimizer/ui/views/process_manager_view.py:239   def _render_list(self, search_query=""):
src/woptimizer/ui/views/process_manager_view.py:248       protected_apps = self.pack_service.get_protected_apps() if hasattr(self.pack_service, "get_protected_apps") else set()
```
(las líneas 253-257 omiten de la lista los procesos cuyo nombre esté en ese conjunto).

**A-5. `kill_processes` RELEE los protegidos EN CALIENTE.** **Confirmado, y es la línea que decide el caso límite.**

```
src/woptimizer/services/process_service.py:540-543
    if protected_apps is None:
        if hasattr(self, "pack_service") and self.pack_service and hasattr(self.pack_service, "get_protected_apps"):
            protected_apps = self.pack_service.get_protected_apps()
```

Y el salto:

```
src/woptimizer/services/process_service.py:555-562
        name_lower = ...
        clean_name = _normalizar_nombre(pinfo.name)
        if name_lower in protected_apps or clean_name in protected_apps or full_lower in protected_apps:
            skipped += 1
            continue
```

**Y el `pack_service` está cableado de verdad en la app real** (esto es lo que convierte A-5 en una garantía y no en una casualidad):

```
src/woptimizer/services/process_service.py:321   self.pack_service = pack_service
src/woptimizer/__main__.py:23                    process_service = ProcessService(pack_service)
```

**A-6. `get_protected_apps()` normaliza a minúsculas y añade basename y basename sin `.exe`.**

```
src/woptimizer/services/pack_service.py:1372-1387   def get_protected_apps(self) -> Set[str]
src/woptimizer/services/pack_service.py:1365-1370   def get_protected_pack(self) -> Optional[Pack]
```

**A-7. La otra puerta de protección (filedialog) guarda el BASENAME en minúsculas.**

```
src/woptimizer/ui/views/pack_manager_view.py:536   def add_app_to_protected(self, pack_id: str)
```
(guarda `os.path.basename(path).lower()`, no la ruta absoluta).

**A-8. `on_kill_selected` llama a `kill_processes` SIN pasar `protected_apps`** → el valor es `None` → se relee en caliente.

```
src/woptimizer/ui/views/process_manager_view.py:377   def on_kill_selected(self):
src/woptimizer/ui/views/process_manager_view.py:404       killed, failed, skipped, freed_mb = self.process_service.kill_processes(to_kill)
```

### 1.2 — Encargo B (TASK-095)

**B-1. La Portada tiene UN botón por pack, y el texto de la tarjeta es el texto del botón.**

```
src/woptimizer/ui/views/dashboard_view.py:35          self._buttons_by_pack_id = {}
src/woptimizer/ui/views/dashboard_view.py:294-299     def _destroy_favorite_buttons(self)
src/woptimizer/ui/views/dashboard_view.py:326-346     def _regrid_favorites(self)          # 344: btn = self._buttons_by_pack_id.get(pack.id)
src/woptimizer/ui/views/dashboard_view.py:348-397     def refresh_dashboard(self)            # 385-386 crea+registra; 391-397 reconfigura
src/woptimizer/ui/views/dashboard_view.py:399-413     def _get_pack_button_text(self, pack) # 413: f"{pack.name}\n({len(pack.apps)} apps · {pack.default_action.upper()})"
src/woptimizer/ui/views/dashboard_view.py:415-439     def _create_favorite_button(...)      # 436-438 crea el CTkButton y lo gritea
src/woptimizer/ui/views/dashboard_view.py:457         def execute_pack(self, pack, button=None)
```

**B-2. `execute_pack` decide POR `default_action`, y el banner también.**

```
src/woptimizer/ui/views/dashboard_view.py:472   if pack.default_action == "kill":
src/woptimizer/ui/views/dashboard_view.py:481       self._show_aviso_banner(*mensaje_banner_sin_apps(pack.name, pack.default_action))
src/woptimizer/ui/views/dashboard_view.py:488       if not self._require_double_tap(f"dashboard:{pack.id}", button, aviso):
src/woptimizer/ui/views/dashboard_view.py:505       self._show_aviso_banner(*mensaje_banner_sin_apps(pack.name, pack.default_action))
```

**B-3. El Gestor de Packs: desplegable sin etiqueta, valores crudos.**

```
src/woptimizer/ui/views/pack_manager_view.py:257   def change_default(choice, p_id=pack.id):
src/woptimizer/ui/views/pack_manager_view.py:271       combo_action = ctk.CTkOptionMenu(
src/woptimizer/ui/views/pack_manager_view.py:272-273       values=["kill", "start"],
src/woptimizer/ui/views/pack_manager_view.py:274           command=change_default,
src/woptimizer/ui/views/pack_manager_view.py:279       combo_action.set(pack.default_action)
```

**B-4. `default_action` es un dominio TOTAL en el modelo.** No hay "inválido" que se cuele en runtime sin ruido.

```
src/woptimizer/models.py:84   default_action: Literal["start", "kill"] = "start"
```

**B-5. El modelo NO admite `default_action` inválido**: `Pack` hereda `AppData`'s `ConfigDict(extra="allow")` pero `Literal` rechaza el valor → `ValidationError` → `pack_service.load()` lo clasifica como **CORRUPCIÓN** y recupera del `.bak` (la rama de corrupción está en `pack_service.py:929`, con el caso literal `default_action: "PURGAR"`).

**B-6. Ya existe el puente entre la Portada y el Gestor: la vista se RECONSTRUYE al navegar.** No hace falta bus de eventos.

```
src/woptimizer/ui/main_window.py:104-107   _clear_content(): current_view.destroy()
src/woptimizer/ui/main_window.py:109-119   _show_home(): crea un DashboardView NUEVO
```

**B-7. Ya existe un vocabulario de acciones centralizado.**

```
src/woptimizer/ui/feedback.py:199   VERBOS = {"kill": "apagar", "start": "iniciar"}
```

`feedback.py` es **puro** (solo `typing` + `ui.confirmation`), sin `tkinter`, sin `services`, sin `models` → es el sitio natural del mapeo nuevo.

---

## 2. Decisiones de diseño

### D-1 — Encargo A

**D-1.1 — El desplegable se construye EXPLÍCITAMENTE, y la entrada protegida va SIEMPRE AL FINAL.**

`_update_pack_dropdown()` deja de ser `packs.values()` filtrado y pasa a ser una lista construida: primero los packs normales (los que hoy ya salen), después la entrada protegida.

Motivo (medido): `pack_service.load()` inserta `"gaming"` (`pack_service.py:511`) y luego `"protected_apps"` (`pack_service.py:512`) al FINAL del dict, así que el orden de `packs.values()` **depende del orden del `profiles.json` del usuario**. Una lista explícita quita ese determinismo del camino.

**D-1.2 — La entrada protegida se ofrece por el `Pack` que el SERVICIO honra, no por "cualquier pack con el flag".**

La listaprotected es `self.pack_service.get_protected_pack()` (`pack_service.py:1365`), **el mismo objeto** whose `get_protected_apps()` (`pack_service.py:1372`) lee. Concreto: `get_protected_pack()` devuelve el **PRIMERO** con `is_protected=True`; si un `profiles.json` editado a mano tuviera dos packs con el flag, ofrecer el segundo en el desplegable sería **ofrecer una protección que el motor ignora**. La UI no puede ofrecer eso.

**D-1.3 — La etiqueta visible del pack protegido lleva prefijo de escudo, y hay un RESOLUTOR etiqueta→pack.**

La etiqueta es `"🛡️ Aplicaciones Protegidas"` (copiar el glifo **carácter a carácter** de `pack_manager_view.py:229`, que ya usa 🛡️; no reescribirlo de memoria — Trampa de emoji en `docs/known-issues.md`).

El prefijo no es decorativo: **el nombre real del pack es `"Aplicaciones Protegidas"`** (`pack_service.py:274`), y `on_add_to_pack` busca por nombre (`process_manager_view.py:444`). Con la etiqueta con prefijo, esa búsqueda por nombre **falla** → hace falta un resolver:

```
def _pack_objetivo_de_la_seleccion(self) -> Optional[Pack]:
    # 1) si la selección es la etiqueta protegida -> pack_service.get_protected_pack()
    # 2) si no -> búsqueda por nombre EXACTO en get_all_packs() (comportamiento de hoy)
```

Se descarta la alternativa "buscar por `is_protected`": con dos packs con el flag, "el primero que encuentre" vuelve a ser el orden del dict.

**D-1.4 — El botón se redibuja con `trace_add("write")` sobre `pack_var`, NO con `command=` del OptionMenu.**

| | `command=` del OptionMenu | `trace_add("write")` sobre `pack_var` |
|---|---|---|
| Dispara al elegir el usuario | sí | sí |
| Dispara cuando el código hace `pack_var.set(...)` | **NO** | sí |
| Sobrevive a `configure(values=...)` | sí | sí |
| Ya está en el repo | no en esta vista | **sí**: `process_manager_view.py:82`, `self.search_var.trace_add("write", ...)` |

El caso que decide: `process_manager_view.py:233-234` hace `self.pack_var.set(values[0])` cuando la selección vigente ya no está en la lista (pasa al cambiar la lista de packs). Con `command=`, el desplegable mostraría el pack nuevo y **el botón seguiría diciendo "🔒 Proteger"**: la UI mentiría sobre lo que hace el botón, que es exactamente la clase de bug que este repo lleva tres ciclos pagando. `trace_add` no tiene ese hueco.

*Corrección de una premisa del briefing:* el `CTkOptionMenu` **sí** admite `command=` (el Gestor de Packs lo usa en `pack_manager_view.py:274`). Lo que es cierto es que **este** desplegable no lo tiene cableado. Aun así se elige `trace_add` por el caso de `pack_var.set()` de la línea 234, que `command=` no ve.

**D-1.5 — El texto del botón depende de UNA fuente: `pack_var`.**

`"🔒 Proteger"` si la selección es la entrada protegida; `"➕ Añadir al Pack"` en cualquier otro caso (incluido el `PLACEHOLDER_PACK` de la línea 20, donde no hay pack elegido y el mensaje de "selecciona un pack válido" sigue igual).

**D-1.6 — Proteger guarda el BASENAME en minúsculas, como la otra puerta.**

`add_app_to_protected` (`pack_manager_view.py:536`) guarda `os.path.basename(path).lower()`. Si el Gestor de Procesos guardara la ruta absoluta (que es lo que hace hoy con los packs normales, línea 456), el **mismo pack** tendría dos formas de dato y el Gestor de Packs mostraría una app como `C:\...\foo.exe` y otra como `foo.exe`. La rama de protección guarda `os.path.basename(exe_name).lower()`; los packs normales **siguen guardando la ruta absoluta** (no se toca: `run_tests.py:6064` fija ese contrato con `test_el_gestor_guarda_la_ruta_absoluta`).

**D-1.7 — El pack protegido NO se puede desproteger desde el Gestor de Procesos.**

`remove_app_from_pack` (`pack_manager_view.py:552`) sigue siendo la única puerta de baja, en el Gestor de Packs. TASK-094 abre la puerta de **entrada**, no la de salida. Que quede escrito para que nadie lo lea como un olvido.

---

### D-2 — Encargo B

**D-2.1 — La tarjeta de la Portada pasa de botón a TARJETA: un `CTkFrame` con una etiqueta y dos botones.**

```
CTkFrame (la tarjeta)
├── CTkLabel   f"{pack.name}\n({len(pack.apps)} apps)"      ← SIN la acción
└── CTkButton  "⛔ Apagar"    (doble pulsación)
    CTkButton  "🚀 Iniciar"   (sin doble pulsación)
```

**La tarjeta deja de imprimir `"KILL"`/`"START"`** (la línea `dashboard_view.py:413` pierde el `· {pack.default_action.upper()}`). Motivo: con dos botones, la acción ya la dice cada botón; imprimirla una tercera vez en la etiqueta es el patrón que `TASK-036` (comentario de `dashboard_view.py:400-408`) vino a matar.

`self._buttons_by_pack_id[pack.id]` **cambia de tipo**: pasa a guardar el **frame**. Es el cambio estructural de más impacto y está enumerado en §3.2.

**D-2.2 — `default_action` pasa de ser una DECISIÓN a ser una PRESENTACIÓN (en la Portada).**

Con dos botones, el botón pulsado **decide la acción**; `default_action` decide **cuál está destacado**. Consecuencias:

- `execute_pack(pack, button, accion)` recibe la acción pulsada y **ramifica sobre `accion`**, no sobre `pack.default_action`.
- Los dos banners (líneas 481 y 505) pasan `accion`, no `pack.default_action`: si no, pulsar "Apagar" en un pack sin apps imprimiría "no hay apps que **iniciar**".
- `default_action` **conserva** su significado de comportamiento **fuera** de la Portada: el **tray** sigue ejecutando la acción por defecto (`app.py:99`, `app.py:188`). Esa coherencia es la que sostiene la frase del dueño: "la acción por defecto" = la que el sistema hace por defecto (tray, un clic); la Portada la **enseña** offering las dos.

**D-2.3 — El doble clic / la doble pulsación: se queda SOLO en "Apagar", y su token pasa a ser POR ACCIÓN.**

`dashboard_view.py:488` hoy es `self._require_double_tap(f"dashboard:{pack.id}", button, aviso)`. Con dos botones, el token **debe** llevar la acción:

```
f"dashboard:{pack.id}:{accion}"
```

Motivo medido, no teórico: `confirmation.py:256-264` (`_recordar_reposo`) guarda el estado de reposo **indexado por token**, y **solo escribe si el token no está ya en `self._reposo`**. Con un token compartido, el primer botón que arma la confirmación graba SU texto de reposo; el segundo botón, al armar con el mismo token, **no vuelve a grabar** → al cancelar, el segundo botón **restaura el texto del primero**. Dos botones, un token: el de "Iniciar" puede acabar mostrando "⚠️ ¿SEGURO?" o restaurando el verbo del otro.

Además, "Iniciar" **no** lleva doble pulsación (arrancar no es destructivo) y su rama llama a `self._cancel_confirm()` (`dashboard_view.py:500`), que **cancela** cualquier confirmación de apagado pendiente. El flujo queda limpio.

**D-2.4 — "La acción por defecto" se ve en la Portada por el botón DESTACADO, y se actualiza sin bus de eventos.**

El mecanismo **ya existe**: `MainWindow._show_home()` (`main_window.py:109-119`) **destruye y recrea** la vista al navegar (`main_window.py:104-107`), y `DashboardView.__init__` llama a `refresh_dashboard()`, que lee `pack_service.get_favorite_packs()` **fresco**. Cambiar `default_action` en el Gestor y volver a la Portada ya repinta con el valor nuevo.

⚠️ La "hay que decidir cómo se refresca la Portada (¿hay un mecanismo de refresco entre vistas?)" tiene respuesta: **no hace falta mecanismo nuevo**, pero la actualización **debe ser explícita en el test**, no accidental. De ahí el test D-2.4 de §6.

**D-2.5 — El desplegable del Gestor se QUEDA, con etiqueta y en español. La traducción vive en `ui/feedback.py` y el dato persistido no se toca.**

```
ETIQUETAS_ACCION = {"kill": "Parar", "start": "Iniciar"}     # en ui/feedback.py

def etiqueta_accion(accion: str) -> str          # "kill" -> "Parar";  ACCION DESCONOCIDA -> KeyError
def accion_desde_etiqueta(etiqueta: str) -> str # "Parar" -> "kill";  ETIQUETA DESCONOCIDA -> KeyError
```

Por qué `feedback.py` y no las vistas: es **puro** (sin Tk, sin `services`, sin `models`), ya centraliza el vocabulario de acciones (`VERBOS`, `feedback.py:199`) y ya es donde viven las frases de las tres puertas. Una función de Traducción sin dependencias es trivialmente testeable sin ventana.

Por qué **KeyError** y no un valor por defecto: `feedback.py:244-251` (`_verbo`) ya usa esa disciplina ("un `default` silencioso es una afirmación que se puede copiar y divergir"). Y el dominio es total (`models.py:84`), así que una etiqueta desconocida **es un bug**, no un caso de negocio.

**El dato persistido no se toca:** `change_default` (`pack_manager_view.py:257`) recibe la etiqueta del desplegable y **traduce antes de asignar**:

```
p.default_action = accion_desde_etiqueta(choice)     # "Parar" -> "kill"
```

Si se asignara la etiqueta cruda, `Pack.default_action` (Literal) **rechazaría el valor** → `ValidationError` al guardar → **el pack se corrompe**. Ese es el riesgo de datos nº 1 de este encargo, y el que justifica el mapa inverso.

**D-2.6 — Las etiquetas de los botones también viven en `feedback.py` (UNA fuente, tres usos).**

Hoy `"⛔ Apagar"` y `"🚀 Iniciar"` están **escritos a mano** en `pack_manager_view.py:284` y `pack_manager_view.py:296`. La Portada añadiría dos copias más. Cuatro copias de la misma frase es exactamente el defecto que este repo ya ha pagado (el literal `"KILL"` congelado en la vista, `dashboard_view.py:403-408`). Por tanto:

```
ETIQUETA_APAGAR  = "⛔ Apagar"     # en ui/feedback.py
ETIQUETA_INICIAR = "🚀 Iniciar"    # en ui/feedback.py
```

y **las dos vistas** los importan. (Los glifos se **copian** de `pack_manager_view.py:284/296`, no se reescriben.)

**D-2.7 — El botón destacado se distingue por color Y por grosor de borde (no solo por color).**

- **Por defecto**: `fg_color` = color de su acción (`theme.DANGER` para Apagar, `theme.ACCENT` para Iniciar), `border_width=2`, `border_color=theme.TEXT_PRIMARY`.
- **No por defecto**: `fg_color=theme.SURFACE_ALT`, `border_width=1`, `border_color=theme.BORDER`.

Contraste: `TEXT_PRIMARY`/`DANGER` y `TEXT_PRIMARY`/`SURFACE_ALT` ya están en la lista blanca de `test_contrast_wcag_aa` (`run_tests.py:8299`), y `TEXT_PRIMARY`/`ACCENT` es el par que la tarjeta actual ya usa (`dashboard_view.py:432-434`). **Sin literales hex en las vistas** (guard `test_no_literal_colors_in_views`, `run_tests.py:1034`): solo tokens de `theme`.

El **grosor de borde** es la pista que no depende del color (accesibilidad): el usuario no tiene que distinguir rojo de azul para saber cuál es el de defecto.

**D-2.8 — El orden de los dos botones es FIJO: `[⛔ Apagar] [🚀 Iniciar]`.** El destacado cambia de aspecto, **no** de posición: si cambiara de sitio, el usuario tendría que reaprender dónde está cada acción en cada tarjeta.

---

## 3. Cambio por fichero

### 3.1 — TASK-094 (Encargo A)

#### `src/woptimizer/ui/views/process_manager_view.py`

| Línea | Qué pasa |
|---|---|
| **20** | `PLACEHOLDER_PACK` se mantiene. **Añadir** `ETIQUETA_PROTEGIDA` como constante de módulo: `"🛡️ Aplicaciones Protegidas"`, con el glifo **copiado** de `pack_manager_view.py:229`. No construir la etiqueta con `f"{p.name}"` en caliente: el prefijo es **fijo**, no depende del nombre persistido. |
| **111** | `self.pack_var` se mantiene. Su valor inicial sigue siendo `PLACEHOLDER_PACK`. |
| **112-119** | `pack_dropdown`: `values` pasa a `[PLACEHOLDER_PACK]` (se rellena luego) **o** directamente a la lista construida. Sin `command=`. |
| **121-131** | `btn_add_pack`: el texto inicial pasa a ser el que dicta D-1.5 (placeholder ⇒ `"➕ Añadir al Pack"`). |
| **nuevo, tras 131** | `self.pack_var.trace_add("write", lambda *a: self._refrescar_texto_del_boton())` — **después** de que exista `btn_add_pack` (si se registra antes, el trace dispara con el botón inexistente). Mismo idioma que `search_var` en la línea 82. |
| **227-234** | `_update_pack_dropdown()`: **deja de filtrar** `is_protected`. Construye la lista explícita: (a) los packs que **no** son el protegido, en el orden de hoy; (b) la etiqueta protegida **al final**, obtenida de `self.pack_service.get_protected_pack()` (D-1.2). La línea 233-234 (`pack_var.set(values[0])`) se queda: con `trace_add` el texto del botón se actualiza solo (D-1.4). ⚠️ `values[0]` ya no puede ser la entrada protegida: por construcción va al final. |
| **435-467** | `on_add_to_pack()`: (a) sustituye la búsqueda por nombre de la **línea 444** por el resolver `_pack_objetivo_de_la_seleccion()` (D-1.3); (b) **rama de protección**: si el destino es el pack protegido, guardar `os.path.basename(exe_name).lower()` (D-1.6) en vez de la ruta; (c) tras `update_pack` (línea 466), **repintar la lista** (`self._render_list()`) para que la app protegida desaparezca — es lo que ya hace TASK-071 al pintar (líneas 248, 253-257); (d) el mensaje de `status_label` **distingue el caso "0 añadidas"** (ya estaba protegida) del caso normal, para no decir "✅ 0 apps" en verde (R-11). La rama normal **no cambia de texto**: `run_tests.py:6094` fija el mensaje `"✅ 0 apps"` para el caso de duplicado y ese test **no se toca**. |
| **nuevo** | `_pack_objetivo_de_la_seleccion(self) -> Optional[Pack]` (D-1.3). |
| **nuevo** | `_refrescar_texto_del_boton(self)` (D-1.5): lee `self.pack_var.get()`, compara con la etiqueta protegida y pone `"🔒 Proteger"` o `"➕ Añadir al Pack"` en `self.btn_add_pack`. |

**No se toca** en este fichero: `_render_list` (239-...), `on_kill_selected` (377-...), `kill_processes` (404). El kill ya respeta la protección; el trabajo es que **la UI llegue a tiempo** y **no mienta**.

#### `src/woptimizer/services/pack_service.py` — **SIN CAMBIOS**

`get_protected_pack()` (1365) y `get_protected_apps()` (1372) ya exponen todo lo que hace falta. Añadir una API aquí sería **API nueva sin consumidor**, que es la clase de deuda que este repo ya tiene registrada (el `get_gaming_pack()` inalcanzable del ciclo 15).

### 3.2 — TASK-095 (Encargo B)

#### `src/woptimizer/ui/views/dashboard_view.py` — **la lista exhaustiva de puntos a tocar**

| Línea | Qué pasa |
|---|---|
| **9-13** | `import` de `feedback`: añadir `ETIQUETA_APAGAR`, `ETIQUETA_INICIAR` (D-2.6). |
| **35** | `self._buttons_by_pack_id = {}` — **cambia de semántica**: ahora guarda **frames** (tarjetas), no botones. Actualizar el nombre o el comentario para que no engañe: el nombre `buttons` con frames dentro es la trampa que hace que un dev futuro `btn.configure(...)` sobre un frame reviente en runtime. **Recomendación**: renombrar a `self._cards_by_pack_id`. |
| **36** | `self._empty_label = None` — **sin cambios**. |
| **294-299** | `_destroy_favorite_buttons()`: el bucle hace `btn.destroy()` (297). Sobre un **frame**, `destroy()` destruye también los hijos → **funciona sin cambios de lógica**. Actualizar el nombre/comentario (`_destroy_favorite_cards`). Ojo: la línea 299 (`self._buttons_by_pack_id.clear()`) sigue igual. |
| **326-346** | `_regrid_favorites()`: la línea **336** filtra por `pack.id in self._buttons_by_pack_id` (sin cambios de forma); la línea **344** `btn = self._buttons_by_pack_id.get(pack.id)` → ahora es la **tarjeta**; la línea **345** `btn.winfo_exists()` → igual; la línea **346** `btn.grid(row=..., column=..., padx=10, pady=10, sticky="nsew")` → igual, pero **`sticky="nsew"` ahora hace crecer el frame**, y dentro del frame los dos botones van en una **sub-rejilla de 2 columnas** (o en `pack(side="left", expand=True)`). |
| **348-397** | `refresh_dashboard()`: la **línea 354** (`cached_ids = set(self._buttons_by_pack_id.keys())`) sin cambios de forma; las **líneas 380-386** (crear + registrar) pasan a registrar la **tarjeta**; las **líneas 391-397** (rama "mismos ids") re-configuran el widget — con dos botones hay que reconfigurar **los dos** (texto, comando, y **resaltado**). Extraer un helper `_actualizar_tarjeta(pack, tarjeta)` usado por **las dos ramas**, para que no haya dos políticas de texto. |
| **399-413** | `_get_pack_button_text()`: deja de ser el texto del **botón** y pasa a ser el texto de la **etiqueta** de la tarjeta. Se **quita** el `· {pack.default_action.upper()}` de la línea 413 y de la línea 411-412 (rama gaming). El comentario de 400-408 se reescribe: explica por qué la tarjeta ya **no** afirma la acción (ahora la afirma cada botón, uno al lado del otro). **Este cambio es obligatorio**: si la etiqueta sigue diciendo "KILL" y hay dos botones, la tarjeta miente (es el mismo defecto que TASK-036 vino a matar). |
| **415-439** | `_create_favorite_button()` → **`_create_favorite_card(pack, row, col) -> ctk.CTkFrame`**: crea el frame, la etiqueta (texto de `_get_pack_button_text`) y los **dos** botones (`ETIQUETA_APAGAR` con doble pulsación, `ETIQUETA_INICIAR` sin ella), los registra en la tarjeta para poder reconfigurarlos, y devuelve el frame. **Altura**: el `height=120` de la línea 422 era el del botón; con etiqueta + 2 botones la tarjeta necesita más alto (o `height=auto`). `theme.ANCHO_MIN_CARD = 280` (`theme.py:52`): dos botones en paralelo necesitan ~2×130 px → **cabe, pero justa**; si el texto se parte, apilar verticalmente. |
| **457-530** | `execute_pack(self, pack, button=None, accion=None)`: (a) `accion` **explícito**; si es `None`, se deduce de `pack.default_action` (compatibilidad con cualquier llamada existente); (b) la **línea 472** `if pack.default_action == "kill":` → `if accion == "kill":`; (c) la **línea 481** y la **línea 505** `mensaje_banner_sin_apps(pack.name, pack.default_action)` → `mensaje_banner_sin_apps(pack.name, accion)`; (d) la **línea 488** el token pasa a `f"dashboard:{pack.id}:{accion}"` (D-2.3); (e) la rama de inicio (línea 500 `self._cancel_confirm()`) se queda. El **comando** de cada botón pasa a `lambda p=pack, b=btn, a=accion: self.execute_pack(p, b, a)`. |

#### `src/woptimizer/ui/views/pack_manager_view.py`

| Línea | Qué pasa |
|---|---|
| **257-269** | `change_default(choice, p_id=pack.id)`: `choice` ahora es una **etiqueta** ("Parar"/"Iniciar"). Sustituir `p.default_action = choice` por `p.default_action = accion_desde_etiqueta(choice)` (D-2.5). El `update_pack(p)` y el `refresh_packs()` **se quedan** (no hay más cambios aquí: el dato persistido sigue siendo "kill"/"start"). |
| **271-280** | `combo_action`: `values=["Parar", "Iniciar"]` (las **etiquetas**, no las acciones crudas); **añadir** un `CTkLabel` con `text="Acción por defecto:"` **justo antes** del combo, con `font=("Segoe UI", theme.FONT_SIZE_TINY)`, `pack(side="left")`. La **línea 279** `combo_action.set(pack.default_action)` → `combo_action.set(etiqueta_accion(pack.default_action))`. ⚠️ **Sin este cambio el desplegable mostraría "kill"** (un valor que ya no está en `values`) → es el bug más probable de este encargo si se implementa a medias. |
| **284** | El literal `"⛔ Apagar"` → `ETIQUETA_APAGAR` (D-2.6). |
| **296** | El literal `"🚀 Iniciar"` → `ETIQUETA_INICIAR` (D-2.6). |
| **536 / 552** | `add_app_to_protected` / `remove_app_from_pack` — **SIN CAMBIOS**. Son la puerta de entrada/salida del pack protegido en el Gestor de Packs y no se tocan en este ciclo. |

#### `src/woptimizer/ui/feedback.py` — **nuevo contenido**

```
ETIQUETAS_ACCION = {"kill": "Parar", "start": "Iniciar"}
ETIQUETA_APAGAR  = "⛔ Apagar"
ETIQUETA_INICIAR = "🚀 Iniciar"

def etiqueta_accion(accion: str) -> str            # KeyError si la acción no es del dominio
def accion_desde_etiqueta(etiqueta: str) -> str   # KeyError si la etiqueta no es del dominio
```

El módulo **sigue siendo puro**: ni `tkinter`, ni `customtkinter`, ni `psutil`, ni `json`, ni `services`, ni `models`. Las funciones no importan nada nuevo.

---

## 4. Invariantes que se tocan (y cómo se conservan)

| Invariante | Impacto | Cómo se conserva |
|---|---|---|
| **Separación de capas** (la UI no llama a OS/psutil ni lee JSON) | **Ninguno**. Las vistas siguen hablando solo con `pack_service`/`process_service`. | El resolver D-1.3 usa `get_protected_pack()`/`get_all_packs()`, ambos del servicio. No se añade `json` ni `os` a las vistas… **excepción**: `os.path.basename` es una operación de **ruta**, no de SO ni de persistencia. Si el revisor lo considera caducado, la alternativa es pedirle al servicio un método `añadir_app_protegida(nombre)`. **Decisión recomendada: pedirlo al servicio** (`pack_service.añadir_app_protegida`) — es la lectura más limpia de la separación y evita `os` en la vista. Ver R-7. |
| **Kill recursivo** (hijos antes que el padre) | **Ninguno**. No se toca `kill_processes`. | — |
| **Pack Gaming no se puede eliminar** | **Ninguno**. No se toca el borrado de packs. | — |
| **Blindaje anti-brick (`SYSTEM_PROTECTED_PROCESSES`, coincidencia EXACTA)** | **Ninguno**. No se toca `process_service.py:35`. | — |
| **Doble pulsación en acciones destructivas** | **Se toca, a propósito**: se mantiene en "Apagar" y **se añade por acción** en el token (D-2.3). | El test D-2.3. |
| **Recuento de tests 235 = 159 + 76** | **Se mueve**: 4 tests nuevos → **239 = 159 + 80**. | §6 y `tasks.md`: los **seis** sitios escritos a mano. |
| **Regla de Git: el bucle empuja a `beta`, nunca a `main`** | **Ninguno** en este ciclo (el dev no hace commit; lo hace el bucle). | — |

---

## 5. Riesgos

### R-1 — El `command=` del OptionMenu solo ve al usuario (corregido por `trace_add`)
`CTkOptionMenu` **sí** admite `command=` (usado en `pack_manager_view.py:274`), así que la premisa "no tiene callback" era **parcialmente falsa**. Aun así `command=` es peor que `trace_add` porque `process_manager_view.py:234` hace `pack_var.set(...)` **por código** y ese cambio no dispara `command=`: el botón se quedaría con el texto del pack anterior. **Mitigación: `trace_add`.**

### R-2 — `on_add_to_pack` busca por NOMBRE (línea 444) y el pack protegido tiene etiqueta con prefijo
Sin resolver, la búsqueda falla y el usuario recibe "⚠️ Selecciona un pack válido" **aunque haya elegido el pack protegido**. **Mitigación: D-1.3** (resolver etiqueta→pack).

### R-3 — `get_protected_pack()` devuelve el **PRIMERO** con `is_protected`
Si un `profiles.json` editado a mano tiene **dos** packs con el flag, un desplegable que ofrezca "los packs con `is_protected`" ofrecería **una protección que el motor no aplica** (el motor solo lee el primero). **Mitigación: D-1.2** — el desplegable ofrece `get_protected_pack()`, el mismo que honra `get_protected_apps()`.

### R-4 — La forma del dato en el pack protegido
La puerta del filedialog guarda el basename en minúsculas (`pack_manager_view.py:536`); la del Gestor de Procesos guardaría hoy la ruta absoluta (línea 456). El mismo pack con dos formas → el Gestor de Packs muestra una app como `C:\...\foo.exe` y otra como `foo.exe`, y `remove_app_from_pack` las trata como entradas distintas. **Mitigación: D-1.6** (basename en la rama de protección).

### R-5 — El pack **Gaming ya está hoy en el desplegable**
El filtro de la línea 229 solo excluye `is_protected`: el pack Gaming (y cualquier pack de usuario) son destinos válidos hoy. Añadir el protegido **no cambia eso**, pero conviene saberlo: "Añadir al Pack" sobre la tarjeta Gaming **escribe en `gaming.apps`**, que para el pack de fábrica es `["chrome.exe"]`. **No es alcance de este ciclo**, pero es un ruido preexistente que conviene no confundir con este cambio.

### R-6 — El token de la doble pulsación **compartido** entre los dos botones
Con un token compartido, `_recordar_reposo` (`confirmation.py:256-264`) graba el estado de reposo **del primer botón** y el segundo lo restaura: el botón "Iniciar" puede acabar mostrando "⚠️ ¿SEGURO?" o el verbo del otro. **Mitigación: D-2.3** (token por acción).

### R-7 — `os.path.basename` en la vista vs. separación de capas
D-1.6 mete `os` en la vista. `os.path.basename` no es "leer JSON" ni "llamar a OS", pero **la lectura más limpia** es que el servicio exponga `añadir_app_protegida(nombre) -> bool`. **Decisión de este plan: la frase va al servicio** (fichero nuevo o método en `pack_service.py`), porque (a) el servicio ya es el dueño de la forma del dato del pack protegido, y (b) evita duplicar la regla de normalización en dos sitios. Si el owner del repo prefiere no tocar `services/`, la alternativa es `os.path.basename` en la vista, **documentada**.

### R-8 — La tarjeta de Gaming gana un botón "🚀 Iniciar" que **arranca `chrome.exe`**
El pack Gaming de fábrica tiene `apps=["chrome.exe"]` y `start_categories=[]`. La rama de inicio de `execute_pack` arranca `pack.apps` → **"🚀 Iniciar" en la tarjeta Gaming abriría Chrome**. Hoy esa acción solo es alcanzable si el usuario cambia `default_action` a "start" en el Gestor; con dos botones pasa a ser **un clic**. **No es un bug del código** (es la misma rama que ya existe), pero **es una capacidad nueva y visible**. **Mitigación propuesta**: mantener el botón (la decisión del owner es "dos botones por pack") y **declararlo en el changelog**; si el owner lo no quiere, la alternativa es ocultar "Iniciar" en las tarjetas `is_gaming` — **pero eso contradice la decisión fijada**, así que **pregunta al owner, no lo decidas tú**.

### R-9 — `refresh_dashboard` reconfigura los widgets y **pisaría una confirmación pendiente**
Las líneas 394-397 reconfiguran texto y comando. Si hubiera una doble pulsación armada, el texto "⚠️ ¿SEGURO?" se perdería. **Preexistente**, pero con dos widgets por tarjeta la superficie se duplica. Si el dev toca esa rama, que **no** reconfigure el texto de un botón con confirmación pendiente.

### R-10 — `combo_action.set(pack.default_action)` (línea 279) mostraría **"kill"**
Si solo se cambian los `values` y no el `set`, el desplegable muestra un valor **fuera de la lista**. **Mitigación: D-2.5** y es el primer aserto del test D-2.5.

### R-11 — "✅ 0 apps" en verde cuando no se añadió nada
Hoy el mensaje de la línea 466-467 dice "✅ {added} apps añadidas a {pack}" incluso con `added == 0` (y `run_tests.py:6094` **c fixa ese texto** para el caso de duplicado). Para la **rama de protección** el plan exige un texto honesto ("ya estaba protegida"). La rama normal **no se cambia** en este ciclo (rompería ese test).

### R-12 — La **etiqueta** del desplegable puede quedar **apretada**
`right_box` (`pack_manager_view.py:262-280`) es una barra horizontal a la derecha de la cabecera. Añadir "Acción por defecto:" ensancha la cabecera. Si el texto se parte, usar `theme.FONT_SIZE_TINY` y `wraplength`, o mover el desplegable a una segunda línea. **Comprobar en el smoke visual.**

### R-13 — Vocabulario **doble**: el desplegable dice "Parar" y el botón dice "Apagar"
La decisión fijada por el owner usa "Parar" en el desplegable y "⛔ Apagar" en los botones. Son **dos palabras para la misma acción**, y este repo tiene una regla explícita contra eso ("una frase escrita en la vista es una frase que se puede copiar y divergir"). **Mitigación adoptada**: los dos vocabularios están **centralizados** en `feedback.py` (`ETIQUETAS_ACCION` y `ETIQUETA_APAGAR`), así que la divergencia es **visible y de un solo sitio**. **Se deja constancia** para que el owner decida en un ciclo posterior si unifica a "Apagar" o a "Parar".

### R-14 — El **tray** sigue ejecutando `default_action`
`app.py:99` y `app.py:188` no cambian. La coherencia ("la acción por defecto" = la del tray) es **intencionada**, pero significa que `default_action` conserva un significado **de comportamiento** fuera de la Portada. Si alguien lee "la Portada ya no usa `default_action`" como "`default_action` ha muerto", se equivocará. **Documentarlo en `docs/ai/data-models.md`.**

### R-15 — El recuento de tests es un **contrato escrito a mano en seis sitios**
235 está en `AGENTS.md:70`, `README.md:63`, `STATUS.md:12`, `STATUS.md:133`, `docs/ai/testing-guide.md:59` y en el **comentario** de `validate_docs.py:2967-2969`. Añadir tests sin tocar los seis = `validate_docs.py` en rojo (o, peor, un recuento que miente en verde).

---

## 6. Criterios de aceptación y **cómo se mide cada uno**

Decisión de este plan: **SÍ se añaden tests**, y son **`test_*` contados** (no checks de `validate_docs.py`).

**Por qué counted y no un check del validador:**
1. `validate_docs.py` **no corre en CI** (`AGENTS.md`, sección Releases: "⚠️ `validate_docs.py` NO corre en CI"). Un guard que solo vive ahí **no lo ejecuta nadie** en el pipeline.
2. La lección del repo es literal: *"un guard que nadie cuenta se puede borrar sin que nada se entere"* (lección A-C68-1, citada en `run_tests.py:33372-33373`). Un check del validador **no está contado** por la suite ni por el `mutation-auditor` (que muta `run_tests.py`).
3. El precedente de **no** mover el recuento (TASK-087, check 11 en `validate_docs.py`) estaba justificado porque aquel guard verificaba **la existencia de un artefacto** (un hash), no un comportamiento. Aquí hay **comportamiento**, y el repo tiene el patrón headless justo para eso (`ProcessManagerView.__new__` + dobles, `run_tests.py:5974-6097`).

**Recuento nuevo: 235 + 4 = 239 = 159 backend + 80 headless.**
Los 4 tests nuevos van **DESPUÉS** del marcador `--- Running Headless UI Tests ---` (`run_tests.py:33375`) → cuentan como headless (el reparto lo deriva `validate_docs.py:1131-1201` con `ast`).

### Los 6 sitios a mover (5 declaraciones + 1 comentario)

| # | Fichero:línea | Texto actual | Nuevo |
|---|---|---|---|
| 1 | `AGENTS.md:70` | `# 235 tests headless (no abre ventanas)` | `# 239 tests headless (no abre ventanas)` |
| 2 | `README.md:63` | `# 235 tests headless (no abre ventanas)` | `# 239 tests headless (no abre ventanas)` |
| 3 | `STATUS.md:12` | `**235 tests** (159 backend + 76 headless UI)` | `**239 tests** (159 backend + 80 headless UI)` |
| 4 | `STATUS.md:133` | `4. **Tests:** `python run_tests.py` (235 tests)` | `(239 tests)` |
| 5 | `docs/ai/testing-guide.md:59` | `Contiene **235 tests**: 159 de backend + 76 headless de UI.` | `**239 tests**: 159 de backend + 80 headless de UI.` |
| 6 | `validate_docs.py:2967-2969` | comentario que dice *"El recuento se queda en 235 = 159 + 76"* | reescribir: el recuento **sube** a 239 = 159 + 80, y **por qué** (4 tests nuevos, counted) |

⚠️ `STATUS.md` está **prohibido** en el encargo de *este* ciclo (arquitecto). Lo edita el **dev del ciclo 73**. `validate_docs.py:1248-1249` exige que `STATUS.md` declare el reparto con la forma `\d+ backend + \d+ headless` y que coincida con el derivado → si se mueve el reparto y no se mueve `STATUS.md:12`, el validador **falla**.

### Los 4 tests nuevos

| ID | Nombre del test | Qué mide | Por qué **NO** es vaciable |
|---|---|---|---|
| **AC-1** | `test_el_gestor_de_procesos_ofrece_el_pack_de_protegidas_y_lo_protege` | (a) La lista del desplegable **contiene** la etiqueta protegida. (b) Con esa etiqueta seleccionada, `on_add_to_pack()` **persiste** el basename en minúsculas en el pack protegido (leído del **doble**, no de la copia de la vista — el doble de `run_tests.py:5998-6029` ya devuelve copias defensivas). (c) `update_pack()` se llama **una** vez. (d) Tras proteger, la lista **se repinta**. | Sin el fix, (a) falla: el filtro de la **línea 229** saca el pack protegido. Un implementario que **añada la etiqueta pero no persista** pasa (a) y muere en (b) — porque el doble solo ve lo que `update_pack` escribió. Un implementario que persista la **ruta** en vez del basename muere en (b) por la forma del dato (D-1.6). Un implementario que no repinte muere en (d). |
| **AC-2** | `test_proteger_y_matar_sin_repintar_no_mata_la_app` | **El caso límite.** Con un `ProcessService` REAL y un `pack_service` cuyo `get_protected_apps()` devuelve la app protegida: `kill_processes([proceso])` → `killed == 0`, `failed == 0`, **`skipped == 1`**, y **`psutil` no se toca**. | Es el discriminante central: **si la relectura en caliente (`process_service.py:540-543`) desapareciera** — o si la UI dejara de releer — el proceso **no** estaría en `protected_apps` → el kill **intentaría** matarlo → `psutil.Process(pid)` → `NoSuchProcess` → **`failed == 1` en vez de `skipped == 1`**. El aserto **`failed == 0`** es el que prueba que `psutil` **no se alcanzó** (con un pid inexistente, si se alcanzara, `failed` subiría). **Es seguro**: nunca se mata nada real, porque el proceso se salta **antes** de `psutil.Process`. |
| **AC-3** | `test_la_portada_tiene_dos_botones_y_el_por_defecto_manda` | (a) La tarjeta de un pack tiene **exactamente 2** botones. (b) El botón **destacado** es el de `pack.default_action` (se comprueba por el color/borde del widget, no por una suposición). (c) Con `default_action == "kill"`, pulsar **"🚀 Iniciar"** **no** mata y **sí** arranca (se comprueba con dobles, sin procesos reales). (d) Con `default_action == "start"`, pulsar **"⛔ Apagar"** **no** arranca y **sí** mata. (e) La etiqueta de la tarjeta **no** contiene `"KILL"` ni `"START"`. | (a) falla sin el fix (hoy hay **un** botón). (c)/(d) matan la implementación ingenua que **mantiene** el `if pack.default_action == "kill"` de la **línea 472**: con `default_action="kill"`, pulsar "Iniciar" mataría. (e) falla si la etiqueta se queda con `pack.default_action.upper()` de la **línea 413**. |
| **AC-4** | `test_la_etiqueta_de_accion_va_y_vuelve_sin_tocar_el_dato_persistido` | (a) `etiqueta_accion("kill") == "Parar"`, `etiqueta_accion("start") == "Iniciar"`. (b) `accion_desde_etiqueta("Parar") == "kill"` (ida y vuelta para las dos). (c) Una etiqueta **desconocida** lanza `KeyError` (**no** devuelve un valor por defecto). (d) Tras `change_default("Parar")`, lo **persistido** en el pack es `"kill"` — **el literal del dominio**, no "Parar". (e) El `profiles.json` escrito contiene `"default_action": "kill"`. | (d)/(e) matan el bug de datos: si `change_default` asignara la etiqueta cruda, `Pack.default_action` (`models.py:84`, `Literal`) **rechazaría** el valor → `ValidationError` al guardar → **el pack se corrompe**. (c) mata el `default` silencioso, que convertiría un typo en un dato persistido equivocado. (a)/(b) son tautológicos **solos**, pero no solos: (d)/(e) son los que discriminan. |

### AC-0 — Los criterios que **no** se miden con un test (y por qué)

| AC | Cómo se mide | Por qué no hace falta un test |
|---|---|---|
| El desplegable **muestra** la etiqueta protegida con el glifo exacto | Revisión visual (smoke) + el aserto (a) de AC-1 sobre la **cadena**, no sobre el render | Un test de renderizar un emoji es un test de Tk, no de la lógica. El **carácter a carácter** se comprueba en la revisión (Trampa de emoji). |
| El botón cambia a "🔒 Proteger" al elegir el pack protegido | AC-1 (extensión) comprueba que `_refrescar_texto_del_boton()` pone la etiqueta correcta **para las dos** selecciones, y que un `pack_var.set()` **por código** también la actualiza (el caso de la **línea 234** que `command=` no vería) | Es comportamiento de vista: se comprueba con el doble de `_Var`/`_Label` que ya existe (`run_tests.py:5984-5996`), sin Tk. |
| La cabecera del Gestor no se rompe con la etiqueta nueva | Revisión visual | Es maquetación. |
| `default_action` inválido o ausente en un pack guardado | **Ya está cubierto por el modelo** (`models.py:84` + la rama de corrupción de `pack_service.load()`, `pack_service.py:929`) → **no hace falta un test nuevo**: un valor inválido es `ValidationError` → corrupción → recuperación del `.bak`; un valor **ausente** toma el default `"start"`. **Lo que SÍ hay que documentar** es que `create_user_pack` (`pack_service.py:1400`) **no pasa `default_action`** → todo pack creado por el usuario nace con `"start"`. | El dominio es **total por construcción**; el riesgo no es "aceptar un inválido", es **no saber qué hacer con un inválido**, y eso ya está resuelto en el servicio. |

### Cómo se comprueba que el recuento **no se mueve por accidente**

1. `python validate_docs.py` (check 7: total definido == total invocado; y el reparto derivado con `ast` contra lo que declara `STATUS.md`).
2. `python run_tests.py` — la suite **verde** y el recuento impreso = **239**.
3. `grep -n "235" AGENTS.md README.md STATUS.md docs/ai/testing-guide.md` → **cero** coincidencias (o solo las históricas justificadas).
4. `grep -n "235\|159 + 76" validate_docs.py` → la **única** mención es el comentario reescrito del punto 6, que ya habla de 239.

---

## 7. Plan de documentación

| Fichero | Qué se documenta |
|---|---|
| `docs/ai/ui-design-system.md` | (1) La tarjeta de la Portada: **frame + etiqueta + 2 botones**, el Fixed order, el resaltado del de por defecto (color + grosor de borde) y por qué el texto de la etiqueta ya **no** afirma la acción. (2) El **token por acción** de la doble pulsación y por qué (el `_reposo` indexado por token). (3) El Gestor de Procesos: el desplegable **construido explícitamente**, la entrada protegida **al final** y con prefijo, el resolver etiqueta→pack, y la regla "el botón se redibuja con `trace_add`, no con `command=`" **con el caso de `pack_var.set()` por código**. (4) La etiqueta "Acción por defecto:" del Gestor de Packs. |
| `docs/ai/data-models.md` | (1) `default_action`: **significado nuevo** = "la acción por defecto" = la que ejecuta el **tray** y la que se **destaca** en la Portada; el valor persistido **sigue siendo** `"kill"`/`"start"` y **no** cambia. (2) El **vocabulario** de la capa de presentación (`ETIQUETAS_ACCION`, "Parar"/"Iniciar") y que es **cap strictly presentacional**: nunca se persiste. (3) `default_action` **ausente** ⇒ `"start"`; **inválido** ⇒ corrupción (`.bak`). (4) `create_user_pack` nace con `"start"`. |
| `docs/ai/architecture.md` | **Nada**: no cambia ninguna frontera de capa (salvo que se opte por `pack_service.añadir_app_protegida`, en cuyo caso se documenta el método nuevo). |
| `CHANGELOG.md` + `.taskmaster/CHANGELOG.md` | Los **dos** ficheros, en el pase del ciclo 73 (los escribe el bucle, no el dev de este encargo). |

---

## 8. Lo que este encargo **NO** toca

- `src/woptimizer/services/process_service.py` — el kill **ya** relee en caliente y **ya** salta los protegidos. **Cero cambios.** Es el hallazgo que hace que TASK-094 sea **una puerta de UI**, no un fix de motor.
- `src/woptimizer/services/pack_service.py` — **cero cambios**, salvo que se opte por `añadir_app_protegida` (R-7), que es **opcional** y debe quedar justificado.
- `src/woptimizer/ui/confirmation.py` — el token cambia en el **llamador**, no aquí.
- `run_tests.py` — solo **añadir** 4 tests (no tocar los existentes: `run_tests.py:6064` y `run_tests.py:6094` fijan contratos vivos).
- `.taskmaster/tasks.json`, `STATUS.md`, `CHANGELOG.md`, `.taskmaster/CHANGELOG.md`, `.taskmaster/rd_journal.json` — **los escribe el bucle**, no este encargo.
