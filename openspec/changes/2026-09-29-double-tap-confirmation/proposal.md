# Propuesta: Doble pulsación en acciones destructivas (restaurar la seguridad perdida en la reescritura v3)

- **Change ID**: `2026-09-29-double-tap-confirmation`
- **Ciclo**: #12
- **Área de rotación**: 2 — Gaming & Telemetría UX (sin tocar desde el ciclo #8)
- **Taskmaster**: `TASK-023`
- **Subagente de ejecución**: `openspec-dev`
- **Estado**: AUDITADA por architect-review — **aprobada con correcciones** (ver §9)

## 1. Problema: una regresión silenciosa de la reescritura v2 → v3

En la v2 (`process_manager.py` v2.0.2) existía un patrón de **doble pulsación** para confirmar
acciones destructivas, implementado con los helpers `_request_confirm` y `_reset_pending_action`.
Se introdujo por un incidente concreto y documentado: un `messagebox.askyesno` se abría **por
detrás de la ventana principal**, el usuario pulsaba "Cerrar", no veía nada, empezó a pensar que
la app estaba rota, y reportó "se ha roto, no mata procesos". La conclusión fue: **nunca
`messagebox` en la ventana principal**; la seguridad se consigue exigiendo una segunda pulsación,
no con un diálogo.

Ese patrón se perdió en la reescritura v3. Búsqueda sobre todo `src/woptimizer/` (verificada en
este ciclo, sigue dando cero):

```
messagebox | askyesno | showinfo | showwarning | _request_confirm | "OTRA VEZ" | confirm  (case-insensitive)
-> No matches found
```

Es decir, hoy la v3 **no tiene ninguna confirmación en ninguna parte**, y no es por decisión de
diseño: es un descuido de la reescritura. Peor: `docs/known-issues.md` termina en la **Trampa #13**,
así que ni siquiera quedó documentado el porqué. La próxima reescritura volverá a perderlo.

## 2. Evidencia: las acciones destructivas sin confirmar

Rutas de grep verificadas archivo por archivo durante esta auditoría.

| # | Ubicación | Botón | Qué hace sin confirmar |
|---|-----------|-------|------------------------|
| 1 | `process_manager_view.py:58` → `on_kill_selected` (`:223`) | ⛔ Cerrar Seleccionados | Mata N procesos elegidos a pelo. Un clic de más sobre la fila equivocada y se cierra tu navegador con 40 pestañas sin guardar. |
| 2 | `pack_manager_view.py:85` → `kill_pack` (`:212`) | ⛔ Apagar | Mata todas las apps del pack en un clic. |
| 3 | `pack_manager_view.py:100` → `delete_pack` (`:190`) | 🗑️ | Borra el pack. Ver §9.2: la premisa original sobre el `ValueError` era incorrecta, pero el fallo silencioso real sigue existiendo. |
| 4 | `pack_manager_view.py:117` → `remove_app_from_pack` (`:205`) | ❌ | Quita una app del pack. |
| 5 | `dashboard_view.py:91` → `execute_pack` (`:101`) | botón grande del pack favorito | **Solo cuando `default_action == "kill"`** mata todas las apps del pack; si es `start` arranca, que no es destructivo. |

## 3. Objetivo

Restaurar la doble pulsación con las reglas del incidente original:

1. **Primera pulsación** → el botón pasa a estado de aviso y el `status_label` **inline** explica
   qué va a pasar y a cuántos procesos afecta.
2. **Segunda pulsación** dentro de la ventana de tiempo → ejecuta la acción real y resetea.
3. `after(N ms, reset)` → auto-revierte si el usuario no confirma.
4. Si el usuario **cambia la selección** entre pulsaciones → la confirmación pendiente se
   invalida (no se ejecuta con la intención antigua).
5. Si el usuario pulsa **otra acción distinta** → se resetea la pendiente anterior.
6. **Prohibido `messagebox`**: ni para confirmar ni para el resultado. Todo va al `status_label`
   inline (verde / amarillo / rojo).
7. **Prohibido** dejar un `after()` vivo cuando el widget que reconfigura ya no existe (§9.3).

## 4. Alcance

### 4.1 Código de producción (lo único que se toca bajo `src/`)
- **NUEVO** `src/woptimizer/ui/confirmation.py` — la lógica compartida (ver §5).
- `src/woptimizer/ui/views/process_manager_view.py` — `on_kill_selected` + 1 `status_label` nuevo
  para el caso "no hay nada marcado" (hoy `return` mudo en `:225-226` y `:232-233`).
- `src/woptimizer/ui/views/pack_manager_view.py` — `kill_pack`, `delete_pack`,
  `remove_app_from_pack` + **un `status_label` nuevo en la vista** (hoy `PackManagerView` no
  tiene ninguno: `_build_ui` solo construye header y `scroll_frame`, `pack_manager_view.py:19-30`).
- `src/woptimizer/ui/views/dashboard_view.py` — `execute_pack`, rama `default_action == "kill"`.

Son **3 vistas**, no 4 (corrección de §9.6).

### 4.2 Ficheros de tooling que también hay que tocar
- `verify_ui_syntax.py` → **añadir `src/woptimizer/ui/confirmation.py` a `files_to_check`**
  (lista fija en `:9-17`; un fichero nuevo no se valida solo y el script daría verde en falso).
- `run_tests.py` → registrar el test headless del helper en el bloque `__main__` (`:928+`).

### 4.3 Documentación
- `docs/known-issues.md` → **Trampa #14**, insertada **antes** de
  `## Resumen de reglas para IA que modifique este proyecto` (`:282`), no al final del fichero.
- `docs/ai/ui-design-system.md` → el patrón como norma de UI, sección nueva.

### 4.4 Fuera de alcance
- **NO** tocar `src/woptimizer/services/**`. `services/` no importa nada de `ui/` (verificado) y
  eso se mantiene: el helper vive en la capa `ui/` y solo usa `typing` + `tkinter`, nunca
  `psutil`, nunca JSON.
- **NO** reintroducir `messagebox` en ninguna forma.
- **NO** cambiar la lógica de kill, el semáforo de seguridad ni la protección del pack Gaming.

## 5. Arquitectura del helper: opción recomendada (a) con máquina de estados separada

Se evaluaron las tres opciones:

| Opción | Testeable headless | Sin 4 copias | Veredicto |
|---|---|---|---|
| (a) `ui/confirmation.py` con clase/mixin | Sí, si la máquina de estados no toca Tk | Sí | **GANADORA** |
| (b) clase base/mixin de la que hereden las vistas | No: instanciar una `CTkFrame` exige un root Tk | Sí | Rechazada |
| (c) helper con callbacks inyectados | Sí | No: el arm/reset queda reescrito en las 3 vistas, que es justo el fallo a evitar | Rechazada |

**Recomendación: (a)**, y con un matiz que la hace correcta: dentro de `ui/confirmation.py` hay
que separar **dos cosas** que la propuesta original trataba como una.

- **`DoubleTapGuard`** — máquina de estado ** pura**. No conoce widgets, no importa `customtkinter`.
  Campos: `token: str | None`, `label: str`, `deadline_ns`, y un `scheduler` inyectable
  (`schedule(ms, cb) -> handle` / `cancel(handle)`), con el de Tk (`after`/`after_cancel`) como
  valor por defecto. Métodos: `arm(token, label, on_expire) -> bool` (devuelve `False` si ya había
  una pendiente para ese `token`), `consume(token) -> str | None` (devuelve el label si confirma,
  `None` si no), `reset()`, `is_pending(token) -> bool`.
  **Se testea con un scheduler falso, sin ventana.** Ahí va el test headless que discrimina.
- **`Confirmable`** — mixin *fino* para las vistas. Solo envuelve la máquina: configura `text` /
  `fg_color` / `hover_color` del botón y escribe en el `status_label`. Puede probarse con un doble
  que registre llamadas (`configure` / `winfo_exists`), también sin root.

El mixin **no** es una clase base de widget: heredar de `ctk.CTkFrame` (opción b) obligaría a
tener un root para testear, que es justo lo que se pide evitar. Con un mixin, el test instancia
`DoubleTapGuard(scheduler=FakeScheduler())` en un `self` falso y listo.

El helper expone además:
- `cancel_on_destroy()` — a llamar desde el `destroy()` de cada vista, cancela el `after` vivo.
- Una constante `CANCEL = "#5a4a1e"` y `PENDIENTE_TEXT` para que los 3 botones compartan
  literal de estado (requisito: mismo aspecto en las 5 acciones).

## 6. Decisiones sobre los riesgos abiertos

### 6.1 Refresco o destrucción con confirmación pendiente

**Confirmado, y es el riesgo número uno: no es hipotético, es el flujo normal de la app.**
`MainWindow._clear_content()` (`main_window.py:42-45`) hace `destroy()` de la vista actual y
`_show_home/_show_packs/_show_process_manager` (`:52-83`) crean una **instancia nueva** en cada
cambio de pestaña. Además dentro de `PackManagerView`, `refresh_packs()` (`:33-34`) destruye todos
los hijos de `scroll_frame`, y `remove_app_from_pack` (`:210`), `delete_pack` (`:193`) y
`toggle_favorite` (`:184`) llaman a `refresh_packs()`.

Peor: `process_manager_view.py` programa con `self.master.after(...)` (`:69, 76, 82, 83, 245, 246`)
y `master` es `content_frame` (`main_window.py:77`), que **no** se destruye al cambiar de pestaña.
Ese callback sobrevive a la vista y luego reconfigura widgets ya destruidos.

**Regla para el implementador:**
1. Programar siempre con `self.after(...)` (la vista), nunca con `self.master.after(...)`.
2. Cada vista sobrescribe `destroy()`: cancela el timer pendiente y pone el estado a limpio
   **antes** de llamar a `super().destroy()`.
3. El callback del reset comprueba `self.winfo_exists()` antes de tocar widgets, y envuelve el
   `configure` en `try/except tk.TclError` como red de seguridad.
4. En `PackManagerView`, `refresh_packs()` **cancela la pendiente** al principio: los botones de
   tarjeta se recrean, así que una pendiente sobre ellos no tiene a qué reconfigurarse.
5. En la acción confirmada se **cancela la pendiente antes de ejecutar**, porque la propia acción
   puede destruir el botón (caso 4: `remove_app_from_pack` → `refresh_packs()`).

### 6.2 Congelar o recalcular `to_kill` en `on_kill_selected`

**Decisión: se congela la INTENCIÓN (el conjunto de claves marcadas) y se recalculan los DATOS
(`ProcessInfo`) en la segunda pulsación.**

Congelar la lista de `ProcessInfo` sería un error de seguridad, no de usabilidad: entre las dos
pulsaciones pasan hasta 3 s, `refresh_processes` puede reescribir `self.grouped_processes`
(`:80`), y sobre todo **los PIDs se reciclan**. Matar un `ProcessInfo` congelado cuyo PID ya
repertenece a otro proceso es matar a un inocente. La lista recalculada en el instante de la
confirmación es siempre la realidad vigente.

La coherencia con el criterio "cambiar la selección invalida" queda así, y es decidible sin
ambigüedad:

- 1ª pulsación: `token = claves_marcadas_ahora` (tuple ordenada). Se muestra el count.
- 2ª pulsación: `claves_actuales = claves_marcadas_ahora`. Si `!= token` → **invalidar y re-armar**
  con las claves nuevas (no ejecutar, no dar error). Si `== token` → recalcular `to_kill` desde
  `self.grouped_processes` con esas claves y ejecutar.
- Si el token estaba parcialmente desvanecido (p. ej. el filtro de búsqueda recrea las casillas y
  se pierden claves, `process_manager_view.py:109, 183-184`), se re-arma con la intersección viva.

### 6.3 `execute_pack` en la portada: ¿confirmar o no?

**Decisión: SÍ confirmar, pero solo en la rama `kill`.** El trade-off, con argumentos de las dos
partes:

- *A favor de NO confirmar*: es la acción principal del producto, el botón es enorme y hay que ir
  a la pestaña Portada, marcar el pack como favorito y apuntar a un botón con nombre de pack. Meter
  una segunda pulsación penaliza exactamente el flujo que el usuario vino a hacer.
- *A favor de SÍ*: `refresh_dashboard` coloca los favoritos **de dos en dos** en la misma fila
  (`dashboard_view.py:72-79`, `grid` con `sticky="nsew"`), así que el botón Gaming tiene un botón
  vecino **pegado** que es otro pack distinto. Un dedo gordo mata los procesos del pack que no
  querías. La acción es irreversible y es la de mayor radio de impacto de toda la app.

Pesa más el segundo punto: el error es *irreversible y sobre el objetivo equivocado*, y el coste
de la doble pulsación es ~0,4 s sin diálogo. La objeción de fricción se resuelve con una ventana
más corta en la portada (2000 ms en vez de 3000 ms) y con un texto que nombre el pack.

Matiz adicional que corrige la premisa original: `execute_pack` (`:105-118`) **no** es un botón
"Modo Gaming", es un botón genérico de pack favorito que hace `kill` o `start` según
`default_action`. La confirmación se aplica **solo** a `default_action == "kill"`; pedir
confirmación para arrancar apps sería una bajada de nivel sin motivo.

## 7. Especificación precisa para el implementador

### 7.1 Estados del botón (los 3 estados, literales exactos)

| Estado | `text` | `fg_color` | `hover_color` |
|---|---|---|---|
| Reposo | el literal actual de cada botón (no se toca) | el actual | el actual |
| Pendiente | `"⚠️ ¿SEGURO? PULSA OTRA VEZ"` | `#b8860b` (ámbar) | `#8a6508` |
| Inhabilitado tras confirmar | el literal de reposo, deshabilitado 300 ms y rehabilitado | — | — |

El guard debe **recordar y restaurar** el `text`, `fg_color` y `hover_color` originales de cada
botón; no hardcodear los de uno solo. Para eso, `arm()` debe capturar el estado de reposo en el
primer uso (o el mixin lo registra al construir el botón).

### 7.2 Mensajes del `status_label` (literales exactos, texto plano, sin flechas de consola)

| Momento | Texto |
|---|---|
| 1ª pulsación, procesos | `"⚠️ Segunda pulsación para cerrar {N} apps seleccionadas."` |
| 1ª pulsación, pack kill | `"⚠️ Segunda pulsación para apagar {N} apps de '{pack.name}'."` |
| 1ª pulsación, borrar pack | `"⚠️ Segunda pulsación para borrar el pack '{pack.name}'."` |
| 1ª pulsación, quitar app | `"⚠️ Segunda pulsación para quitar '{app}' de '{pack.name}'."` |
| Selección cambiada | `"⚠️ Selección cambiada. Vuelve a pulsar para confirmar."` |
| Expirada (3 s / 2 s) | `"Cancelado por tiempo de espera."` |
| Kill sin selección | `"⚠️ Selecciona procesos primero."` (mismo literal que ya usa `on_add_to_pack`, `process_manager_view.py:257`) |
| `delete_pack` pack protegido | `"⛔ El pack '{name}' es de sistema y no se puede borrar."` en `text_color="#c22d2d"` |
| `delete_pack` inexistente | `"⚠️ Ese pack ya no existe."` |
| Éxito | reutilizar el `✅ ...` que ya hay, sin tocar |

Color: `text_color` del `status_label` en rojo (`#c22d2d`) para los `⛔` de bloqueo, ámbar
(`#b8860b`) para los avisos, verde (`#1DB954`, el mismo del banner de `dashboard_view.py:49`) para
los `✅`.

### 7.3 Hooks por vista (nombres exactos)

- `ProcessManagerView`: `on_kill_selected()` (`:223`) — se envuelve con el guard. El `to_kill` se
  construye **dentro** de la rama de confirmación (§6.2). Añadir el `⚠️ Selecciona procesos
  primero.` en los dos `return` mudos (`:226` y `:233`). Invalidar en `_render_list` (`:107`) y en
  `refresh_processes` (`:64`).
- `PackManagerView`: `kill_pack(pack)` (`:212`), `delete_pack(pack_id)` (`:190`),
  `remove_app_from_pack(pack_id, app_name)` (`:205`). **Añadir `self.status_label`** al header
  (`_build_ui`, `:19-30`). El token de cada botón debe ser el **id del pack**, no el objeto `Pack`
  (§9.5: `reset_gaming_pack` re-emplaza el objeto por un `model_copy(deep=True)`,
  `pack_service.py:75`, así que una referencia capturada puede quedar obsoleta). Re-obtener el
  pack por id en la segunda pulsación.
- `DashboardView`: `execute_pack(pack)` (`:101`) — guard **solo** en la rama
  `pack.default_action == "kill"` (`:105`), ventana 2000 ms. El token es `f"dashboard:{pack.id}"`,
  **distinto del de la vista de packs**, para que la misma acción en dos vistas no se pise.
- Las 3 vistas: sobrescribir `destroy()` cancelando la pendiente.

### 7.4 Invariante de la frontera de capas

`ui/confirmation.py` solo puede importar `typing` y (en la parte del mixin) `tkinter` /
`customtkinter`. Prohibido `psutil`, `json`, `woptimizer.services` y `woptimizer.models`. La
máquina de estado debe poder importarse en un test sin ninguna dependencia de Tk.

### 7.5 Test headless que debe discriminar

En `run_tests.py`, nueva función `test_double_tap_guard()` registrada en el `__main__` (`:928+`):

- `guard = DoubleTapGuard(scheduler=FakeScheduler())`; `arm("a", "x")` → `True`; segundo `arm("a")`
  sin consumir → `False`; `consume("a")` → `"x"`; `consume("a")` → `None`.
- Ventana: `FakeScheduler` avanza el reloj, `after(3000)` dispara el reset y el guard queda limpio.
- Token distinto: `arm("a")` y luego `consume("b")` → `None` (no se pisa con la anterior).
- `cancel_on_destroy()` con timer vivo → `FakeScheduler` queda sin jobs.
- **Discriminación**: el test debe fallar si alguien renombra o elimina `DoubleTapGuard` /
  `consume` / `arm`. No un test que pase siempre.
- Sin `customtkinter.CTk()` en el test: nada de ventana.

## 8. Criterios de aceptación (actualizados)

- [ ] Las 5 acciones destructivas piden doble pulsación; la de la portada solo en rama `kill`.
- [ ] El helper existe **una sola vez** en `src/woptimizer/ui/confirmation.py` y lo usan las 3 vistas.
- [ ] La máquina de estado se testea headless, sin ventana, y el test discrimina.
- [ ] Auto-revert con `after(3000)` (2000 en portada).
- [ ] Cambiar la selección entre pulsaciones invalida y re-arma.
- [ ] Pulsar otra acción resetea la pendiente anterior.
- [ ] `delete_pack` da feedback inline en los dos casos de fallo (protegido / inexistente) y nada se
      traga en silencio.
- [ ] Cero `messagebox` en `src/` (grep de §1, debe seguir dando cero).
- [ ] `verify_ui_syntax.py` incluye `ui/confirmation.py`.
- [ ] `python verify_ui_syntax.py` y `python run_tests.py` en verde.
- [ ] `Trampa #14` insertada antes del resumen en `known-issues.md`; patrón en `ui-design-system.md`.
- [ ] Cierre limpio: 0 cambios pendientes.

## 9. Hallazgos de la auditoría (errores y huecos de la propuesta original)

### 9.1 El botón de la portada no se llama "🚀 Modo Gaming" — CRÍTICO
La propuesta original (y `tasks.json` TASK-023) lo describían así. El texto real es
`f"{pack.name}\n({len(pack.apps)} apps - {pack.default_action.upper()})"`
(`dashboard_view.py:83`). No existe tal botón: es un botón genérico de pack favorito, y el mismo
handler arranca apps si `default_action != "kill"` (`:114-118`). Implementar "doble pulsación en el
botón Gaming" sin mirar la rama `default_action` habría metido confirmación en acciones de arranque.

### 9.2 La premisa del `except ValueError: pass` es falsa, el fallo real es otro — CRÍTICO
La propuesta afirmaba que el usuario recibe silencio al intentar borrar el pack Gaming protegido.
Es **inalcanzable desde la UI**: `btn_del` solo se crea en la rama `else` de
`if pack.is_gaming:` (`pack_manager_view.py:94-103`), así que el pack Gaming muestra `🔄` y nunca
`🗑️`; y `pack_service.delete_pack` solo lanza `ValueError` si `is_gaming`
(`pack_service.py:117-118`). El fallo silencioso **real** es otro: `delete_pack` devuelve `False`
cuando el pack ya no existe (`pack_service.py:115-116`) y `pack_manager_view.py:190-195` **ignora
el valor de retorno**, además de tragarse la excepción. El arreglo se mantiene, el diagnóstico
cambia.

### 9.3 `PackManagerView` no tiene ningún `status_label` — CRÍTICO
`_build_ui` (`pack_manager_view.py:19-30`) solo crea header y `scroll_frame`. `kill_pack`,
`delete_pack` y `remove_app_from_pack` no producen **ningún** feedback visible (solo el toast
nativo de TASK-019, que no se ve con la ventana oculta en la bandeja). El requisito "feedback
inline" es **implementable solo si antes se añade el label**, cosa que la propuesta original no
contemplaba. Ahora está en §4.1 y §7.3.

### 9.4 El `after()` huérfano no es un riesgo lateral, es el flujo normal — ALTO
Verificado en `main_window.py:42-45` y `:52-83`: **toda** navegación destruye la vista y crea una
instancia nueva. La propuesta lo listaba como un riesgo teórico sin mecanismo. Mecanismo exacto y
regla en §6.1, incluida la razón de usar `self.after` y no `self.master.after`
(`process_manager_view.py:69, 76, 82, 83, 245, 246`; `master` es `content_frame`, que sobrevive).

### 9.5 Capturar el objeto `Pack` en el pending puede quedar obsoleto — MEDIO
`reset_gaming_pack()` re-emplaza el objeto por un `model_copy(deep=True)`
(`pack_service.py:72-75`). Los botones de tarjeta capturan el objeto con `lambda p=pack: ...`
(`pack_manager_view.py:87, 102, 119`). Confirmar contra ese objeto puede operar sobre un pack
clonado. Token por `pack.id` + re-fetch en la segunda pulsación.

### 9.6 "Las 4 vistas" — hay 3 — MENOR
La propuesta repetía "4 vistas" en §3, §4.2, §6 y en los criterios de aceptación, y en
`tasks.json`. Hay 3 ficheros de vista. Un implementador que buscara una cuarta vista daría la
tarea por imposible o inventaría una. Corregido a 3 en todo el documento.

### 9.7 `verify_ui_syntax.py` no valida ficheros nuevos — MENOR
`files_to_check` es una lista fija (`verify_ui_syntax.py:9-17`): un `ui/confirmation.py` nuevo
quedaría fuera y el script daría verde sin comprobarlo. Ahora es paso obligatorio (§4.2).

### 9.8 La Trampa #14 no puede ir al final del fichero — MENOR
`docs/known-issues.md` termina con `## Resumen de reglas para IA que modifique este proyecto`
(`:282`). Añadir la Trampa #14 al final la dejaría **después** del resumen, donde nadie la lee.
Hay que insertarla antes.

### 9.9 Kill con selección vacía sin feedback — MENOR
`on_kill_selected` hace `return` mudo en `process_manager_view.py:225-226` y `:232-233`. Con la
nueva UX el usuario concluiría que el botón está roto. Corregido en §7.3.

## 10. Riesgo

**Medio.** Toca UI real. Los tres riesgos que la propuesta original listaba se han confirmado y
recortado (§9.4, §6.1, §6.2), y se han añadido dos que no estaban (§9.2 diagnóstico erróneo,
§9.3 ausencia de `status_label`). Todos tienen mitigación concreta en §6 y §7.
