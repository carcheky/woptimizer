# Proposal: Selección por categoría para TODOS los packs (apagar y arrancar)

**Change ID:** `2026-10-03-pack-seleccion-por-categoria`
**Tarea:** `TASK-063`
**Encargo del propietario (textual):** «todos los packs deben dejar seleccionar apagado por categorías (y arrancado)»
**Paso del bucle:** 2 — PLANEAR. Este documento NO implementa nada: **cero ediciones bajo `src/`**.

---

## 0. LOG DE REVISIÓN: este documento sustituye a un borrador previo, y por qué

Ya existía un borrador de esta carpeta. Se conserva aquí **lo que se corrigió**, porque borrar la evidencia de lo que se creía es el mismo fallo que no haberlo escrito (regla escrita en la Deuda Técnica Conocida de `STATUS.md`).

| # | Lo que afirmaba el borrador | Lo que se ha medido |
|---|---|---|
| B1 | La barrera 🔴 vive dentro de la única puerta que consulta categorías; sus garantías son G0–G9 | **Incompleto**: la enumeración G0–G9 **se salta el bloque TASK-038** (`gaming_service.py:152-161`), que sobrescribe `_last_closed_apps` **sin condición**. Ver H1, §1.7 |
| B2 | «Hay dos guards bloqueantes, no uno» | **Son cuatro, en dos ficheros**: `pack_manager_view.py:493` y `:495`, `dashboard_view.py:436` y `:439`. Ver H2, §1.6 |
| B3 | «Las TRES puertas de apagado enrutan por `is_gaming`», y las tres se cablean | La tercera (`ui/app.py:119`) **no es una puerta de packs**: lee `get_all_packs().get("gaming")` (`app.py:110`) y su ítem de menú se llama literalmente «🚀 Preparar Gaming Mode» (`app.py:155`). Son **dos** puertas genéricas. Ver H3, §1.5 |
| B4 | «`started += 1` DESPUÉS del `try`, igual que `start_pack_apps` (precedente en la línea 817)» | El precedente está **dentro** del `try` e **inmediatamente después de `_lanzar`**: `process_service.py:829-830`. Implementado literal, contaría como iniciado un arranque fallido. Ver H4, §1.9 |
| B5 | «El test de grep que hoy vigila el módulo (`gaming_service.py:84`)» | `gaming_service.py:84` es una línea de **docstring**. El guard real está en `run_tests.py:903-931` y ya recorre cuatro ficheros de UI. Ver H5, §1.10 |
| B6 | «El verbo lo decide el método, no `default_action` guardado» | Cierto en el Gestor; **falso en la Portada**, donde el verbo **es** `pack.default_action` (`dashboard_view.py:447`, escrito literalmente en `feedback.py:207-209`). Ver H6, §2.5 |

---

## 1. ESTADO REAL MEDIDO (con `fichero:línea`)

### 1.1 La categoría YA es un campo persistido del pack

- `src/woptimizer/models.py:37 target_categories: List[str] = Field(default_factory=list)` — lista de **nombres de categoría** (cadenas con emoji delante). No hay entidad «categoría» en el modelo más allá de esa lista.
- `src/woptimizer/models.py:35 apps: List[str]` — las apps las elige el usuario **una por una**.
- `src/woptimizer/services/pack_service.py:239 target_categories=[...]` — `DEFAULT_GAMING_PACK` ya viene con 5 categorías marcadas, y ese valor viaja al `profiles.json` del usuario.

**Consecuencia:** la mitad del encargo («apagar por categorías») **ya tiene su formato en disco**. No falta un campo: falta el cableado.

### 1.2 La categoría es UNA SOLA por proceso

- `src/woptimizer/services/process_service.py:446-448 def _categorize` — devuelve **una sola cadena** (`cat, _, _ = self._get_process_meta(name)`).
- `src/woptimizer/services/process_service.py:358` — la DB mapea `patrón → (categoría, prioridad, descripción)`: **un patrón, una categoría**.

**Medido:** la resolución es uno-a-uno. La premisa del encargo de que «una app puede estar en varias categorías» es **FALSA contra el código**: no hay dónde estarlo. Ver §3.1 para el criterio.

### 1.3 `default_action` NO enruta nada, y su literal NO es `"stop"`

- `src/woptimizer/models.py:54 default_action: Literal["start", "kill"] = "start"` — un literal por pack, y el literal es **`"kill"`**.
- `run_tests.py:8210-8216` itera `acciones_invalidas = ["purgar", "KILL", "", "stop", "START", None, 123]` y exige `ValidationError` en cada una. (`"stop"` está también enunciado en el docstring, `run_tests.py:8171`.)
- `src/woptimizer/ui/feedback.py:190 VERBOS = {"kill": "apagar", "start": "iniciar"}` — el mapa es **total por construcción**, y `_verbo` **no lleva `default` a propósito** (`feedback.py:211-216`).

**Consecuencia:** hoy existe (a) una lista de categorías que solo el Gaming Mode lee, y (b) un literal que, en la Portada, **elige la rama del botón** (`dashboard_view.py:447`). No existe «acción por categoría».

### 1.4 El acordeón de categorías está GATED a Gaming Mode, y el catálogo está duplicado en la vista

- `src/woptimizer/ui/views/pack_manager_view.py:335-336` — **todo** el acordeón (botón, casillas, guardado) nace dentro de `if pack.is_gaming:`.
- `pack_manager_view.py:365` — la vista **lee `self.process_service.process_db`** para construir el catálogo.
- `pack_manager_view.py:368-371` — y si queda vacío, **repite a mano los 8 nombres**, incluido `⚪ Otros` como U+26AA (`docs/known-issues.md`, Trampa: nunca `?` ASCII).
- El orden canónico ya existe y es otro: `src/woptimizer/config.py:153 CATEGORY_ORDER` y `:157 ordenar_categorias`.

**Medido:** un pack normal **no tiene ni el control**. No es que las categorías se ignoren: es que no se pueden ni expresar.

### 1.5 Las puertas de apagado: DOS genéricas y UNA solo-gaming (corrección B3)

| Punto de entrada | `fichero:línea` | Realidad |
|---|---|---|
| Gestor de packs | `pack_manager_view.py:545` → `:548 kill_pack_apps(apps)` | Puerta genérica de **cualquier** pack |
| Portada | `dashboard_view.py:458` → `:461 kill_pack_apps(p.apps)` | Puerta genérica de **cualquier** pack |
| Bandeja | `app.py:110` `get_all_packs().get("gaming")` → `:119 execute_gaming_pack(...)` | **No es una puerta de packs.** Está cableada al pack `"gaming"` por construction y su ítem de menú es «🚀 Preparar Gaming Mode» (`app.py:155`) |

`ProcessService.kill_pack_apps` (`process_service.py:592`) recibe **solo una lista de apps**: no ve `target_categories`. Para un pack no-gaming, las categorías marcadas son decorativas.

**Decisión de alcance:** `app.py` **no se toca**. Meterlo en la puerta común no cambia nada para el usuario y arrastra la bandeja a un door que por diseño solo es de Gaming. Se cablean **dos** puertas.

### 1.6 CUATRO guards bloqueantes, en dos ficheros (corrección B2)

| # | `fichero:línea` | Qué corta |
|---|---|---|
| G-a | `pack_manager_view.py:493 es_pack_inerte(pack.is_gaming, len(pack.apps), len(pack.target_categories))` | Solo si `is_gaming` (`feedback.py:201`) → **nunca** corta un pack normal |
| G-b | `pack_manager_view.py:495 if not pack.is_gaming and not pack.apps:` | Corta «no tiene apps que apagar» con 0 apps y N categorías marcadas |
| G-c | `dashboard_view.py:436 es_pack_inerte(...)` | Igual que G-a, pero **antes de la rama del verbo** (`:447`), así que también afecta al botón de **arrancar** |
| G-d | `dashboard_view.py:439 if not pack.is_gaming and not pack.apps:` | Corta la Portada con el mismo problema que G-b |

Quitar solo el `if pack.is_gaming:` del acordeón no basta: **G-b y G-d** seguirían diciendo que el pack no puede hacer nada.

### 1.7 La barrera anti-brick vive pegada a `execute_gaming_pack` — y hay un segundo bloque pegado que nadie miró (H1, **hallazgo crítico**)

`execute_gaming_pack` (`gaming_service.py:76`) **rechaza** packs no-gaming con `ValueError` (`:109-113`) y dentro tiene:

- **G1** barrera de categoría roja sobre `target_categories` (`:122-128`).
- **G4** blindaje de nombres `SYSTEM_PROTECTED_PROCESSES` (`:136-137`).
- **G5** barrera roja sobre la categoría **del snapshot** (`:141-143`).
- **G8** la **única** llamada a `kill_processes` (`:164`).

**La barrera NO está en el modelo ni en la vista.** Ampliar el consumo de categorías sin mover la barrera a una puerta común es exactamente el ladrillo del ciclo #14, que dejó `svchost` seleccionable.

> **H1 — el bloque que el borrador se saltó.** `gaming_service.py:152-161` (TASK-038) resuelve los `exe_path` de lo que se va a matar y **sobrescribe `self._last_closed_apps` sin mirar quién pidió el apagado**. Y esa lista:
> - **se consume y se vacía** en `restore_gaming_session()` (`:31-32`),
> - **pone el banner** «🔄 Restaurar Apps Cerradas» en `dashboard_view.py:258-267` (su condición es `if closed_apps:`, `:262`),
> - **y tiene un segundo consumidor**: el ítem de bandeja «🔄 Reabrir aplicaciones cerradas» (`app.py:137`).
>
> Si `execute_pack` se vuelve la puerta común y hereda ese bloque, entonces **apagar un pack normal por categoría**: (a) hace aparecer el banner de restauración sin que haya ninguna sesión Gaming que restaurar, y (b) si el usuario lo pulsa, **destruye una restauración Gaming pendiente de verdad**, porque `restore_gaming_session()` vacía la lista antes de arrancar (`:31-32`).
>
> No es un ladrillo: es pérdida de sesión del usuario, y es la misma clase que este repo ya pagó dos veces (el `model_copy()` shallow del ciclo #10 y el `save()` que machacaba el `.bak` en el ciclo #15). **T-1 lo condiciona** (`gaming_service.py:160-161` queda condicionado a `pack.is_gaming`).

### 1.8 Arrancar por categoría tiene techo real

- `process_service.py:340` — la DB se carga como `{patrón: (categoría, prioridad, descripción)}`. **Ninguna ruta de ejecutable.**
- `process_service.py:672 _resolver_app` — sólo busca bajo las raíces permitidas (`_launch_roots`) y rechaza UNC.
- `start_pack_apps` (`process_service.py:810-835`) cuenta `failed` cuando `ruta is None` (`:824-828`).

**Consecuencia medible:** hay categorías sin **ni un** ejecutable resoluble («🟢 Sincronización» agrupa procesos de fondo). El diseño tiene que poder decirlo con honestidad en vez de reportar successes en verde.

### 1.9 El precedente del contador está mal citado (H4)

`run_tests.py` y el borrador dicen «`started += 1` va **después** del `try`». El código dice otra cosa:

```python
# process_service.py:822-831
try:
    ruta = self._resolver_app(app)
    if ruta is None:
        failed += 1; continue
    self._lanzar(ruta)      # :829
    started += 1            # :830  <- DENTRO del try, DESPUÉS de _lanzar
```

El invariante real es **«`started` cuenta solo si `_lanzar` no lanzó»**, no «está fuera del `try`». Escrito como lo dice el borrador, un arranque fallido cuenta como iniciado: es la mentira que el docstring (`:813-818`) existe para matar, reintroducida por copiar la frase.

### 1.10 Lo que la suite YA vigila, y qué guard hay que tocar (H5)

- **Guard de capas, real:** `run_tests.py:903-931`. Aplica `_codigo_ejecutable` (reconstruye el código sin comentarios ni docstrings, `:1363-1369`) y afirma que no hay `psutil` ni `import json` en `services/gaming_service.py` **y en cuatro ficheros de UI** (`:918-923`). **No comprueba `process_db`.**
- **Guard de los workers:** `run_tests.py:8456-8465`. Lo permitido son **pares `(raiz, método)`**, y hoy incluye `("gaming_service", "execute_gaming_pack")` (`:8461`) y `("process_service", "start_pack_apps")` (`:8459`). Se aplica al **objetivo real** de cada `threading.Thread` de `kill_pack`, `start_pack` y `DashboardView.execute_pack`.
- **Doble de prueba del Gestor:** `run_tests.py:8997-9014` — la clase `_GamingGestor` solo expone `execute_gaming_pack`.

**Consecuencia:** cablear las puertas (T-6) **rompe dos guards y un doble** si no se actualizan en la misma pasada. No es un detalle: son las tres cosas que convierten «funciona» en «está verificado».

### 1.11 Lo que ya está resuelto de más (riesgo retirado)

- **No hace falta migración.** La rama legacy de `load()` pasó a traducir el registro y **entregarlo entero** a `Pack` justamente para esto: *«en cuanto `Pack` gane un campo, esta rama lo leera sin que nadie se acuerde»* (`pack_service.py:350-353`).
- **Ninguna copia es campo a campo.** `get_all_packs` (`pack_service.py:596-597`), `update_pack` (`:601`), `_ensure_gaming_pack` (`:588`), `get_gaming_pack` (`:629`) y `reset_gaming_pack` (`:639`) van con `model_copy(deep=True)`. El campo nuevo viaja solo, y «Restaurar por defecto» lo borra porque restaura el pack de fábrica, que es lo correcto.

---

## 2. DECISIONES DE DISEÑO

### 2.1 El modelo: **un** campo nuevo, y solo uno

| Campo | Tipo | Significado | Estado |
|---|---|---|---|
| `apps` | `List[str]` | Apps **explícitas** que eligió el usuario a mano | Ya funciona en las 3 puertas |
| `target_categories` | `List[str]` | Categorías cuyas apps se **apagan** | **Ya existe** (`models.py:37`); solo cableada en Gaming |
| `start_categories` | `List[str]` | Categorías cuyas apps se **arrancan** | **NUEVO** |
| `keepers` | `List[str]` | Nombres **protegidos**: nunca se apagan | Ya funciona |

### 2.2 Contrato de `start_categories` (decisión explícita, sin ambigüedad)

- **Nombre:** `start_categories`. Simétrico con `target_categories`.
- **Tipo:** `List[str] = Field(default_factory=list)`, colocado **junto a `target_categories`** (`models.py:37`) con un comentario que diga por qué **no** se renombra ese campo (§3.4).
- **Valor por defecto:** `[]`. **Ausente y vacío son indistinguibles a propósito** — es lo que hace que un `profiles.json` viejo siga cargando sin migración y sin aviso.
- **`[]` significa «no arrancar por categoría»**, igual que `target_categories=[]` significa hoy «no apagar por categoría».
- **No es `Optional[List]` / `None`.** Un `None` crea un tercer estado (ausente / vacío / nulo) que ningún llamante necesita y que el `extra="allow"` de `models.py:31` dejaría pasar sin avisar.
- **Compatibilidad en las dos direcciones:** un build viejo lee un `profiles.json` nuevo gracias a `extra="allow"` (la clave desconocida sobrevive al ciclo carga → guarda); un build nuevo lee un `profiles.json` viejo porque el default cubre la clave ausente.
- **Invariante de disjunción:** `start_categories ∩ target_categories = ∅`. Se **impone al escribir** (casilla espejo deshabilitada, §3.3) y se **resuelve en el servicio** por si un `profiles.json` escrito a mano trae el conflicto.
- **No se toca `default_action`**: sigue siendo `Literal["start", "kill"]` (`models.py:54`) y `"stop"` sigue siendo error de escritura (`run_tests.py:8210-8216`).

### 2.3 El catálogo sale de un servicio, y la vista no lee `process_db`

`categorias_disponibles()` en `ProcessService` devuelve la lista ordenada con `ordenar_categorias`/`CATEGORY_ORDER` (`config.py:153`, `:157`). **Sustituye las dos fuentes de la vista**: el `process_db` leído en `pack_manager_view.py:365` y los 8 nombres repetidos a mano en `:368-371`. Es además lo que hace falta para ofrecer «qué es arrancable» sin que la vista adivine.

**El guard se amplía, no se crea:** se añade el predicado `process_db` al bucle que ya existe en `run_tests.py:918-931`. *Recomendado además*: derivar el alcance de los cuatro ficheros con `ast`, como ya hace `_modulos_que_importan_feedback` (`run_tests.py:131-154`), porque una tupla literal de alcance es una apuesta (TASK-037 lo cerró así: `run_tests.py:171-175`).

### 2.4 Precedencia: se reusa, sin reordenar

La política ya existe, está escrita y está probada (`gaming_service.py:47-51`, `should_kill_for_gaming`; test en `run_tests.py:580`). Orden normativo:

| # | Regla | Ámbito | Por qué en esa posición |
|---|---|---|---|
| R0 | Blindaje de nombres + barrera 🔴 sobre la categoría del proceso | kill | Irrenunciable: es el anti-brick del ciclo #14. Va antes de lo configurable porque no depende de la configuración del usuario |
| R1 | `keepers` → proteger | kill | Promesa explícita del usuario |
| R2 | `apps` explícitas | ambas | Ya normativa: lo nombrado a mano gana al barrido |
| R3 | `target_categories` / `start_categories` | ambas | El barrido coge «el resto», nunca pisa lo explícito |

**El conflicto real** (no era multi-etiqueta): la misma categoría en las dos listas.

- **Criterio:** *ante un conflicto, gana la acción cuyo fallo es irreversible.* Apagar destruye estado y puede romper el SO; arrancar, como mucho, abre una ventana que el usuario cierra.
- **Resolución: gana `kill`.** La categoría queda en `target_categories` y se quita de `start_categories`, **en el servicio**, no solo en la UI.
- **Defensa en la UI:** la casilla espejo de la otra lista queda deshabilitada. No se depende de que la resolución sea correcta: se evita que el conflicto se construya.

Una categoría 🔴 es **inerte en las dos listas**, con el mismo predicado que ya usa `gaming_service.py:124`: `get_safety_badge(c)["tier"] != "danger"`. Un helper, dos listas, cero deriva.

### 2.5 Verbos: el Gestor y la Portada NO funcionan igual, y hay que escribirlo (H6)

- **Gestor:** `kill_pack` es **siempre** apagar (`pack_manager_view.py:507`) y `start_pack` es **siempre** arrancar (`:554`). El verbo lo decide el método, y el comentario de `:496-503` lo dice para que nadie lo cambie «para arreglar» nada.
- **Portada:** hay **un solo botón** y su verbo **es `pack.default_action`** (`dashboard_view.py:447`). No es una carelessness: está escrito en `feedback.py:207-209` («en la Portada es `pack.default_action` (que es lo que decide la rama)»).

**Decisión:** la Portada **mantiene un botón** cuyo verbo es `default_action`. Con `"kill"` apaga `apps` + `target_categories`; con `"start"` arranca `apps` + `start_categories`. **Un pack con las dos listas marcadas es, desde la Portada, medio-usable por diseño** — y queda escrito aquí para que quien implemente no invente un segundo botón: el sitio donde están las dos puertas es el Gestor. Esto además da sentido real a `default_action` como selector de verbo de la Portada, que el usuario elige con `change_default`.

### 2.6 Las guardas son POR PUERTA, y `es_pack_inerte` no se ensancha

- `es_pack_inerte` (`feedback.py:193-201`) significa «el Gaming no tiene **nada que cerrar**»: 0 apps **y** 0 categorías. Su docstring lo justifica por `should_kill_for_gaming`, es decir, **por la puerta de kill**. **No se le cambia la firma**: es total, está testeada, y `run_tests.py:157-204` vigila el contrato de sus llamantes.
- **Kill:** `pack_manager_view.py:493` se queda, y `:495` pasa a ser «sin apps **y** sin `target_categories`».
- **Arrancar:** `pack_manager_view.py:556` pasa a ser «sin apps **y** sin `start_categories`»; en la Portada, el guard equivalente pasa a usar `start_categories`.
- **G-c se mueve dentro de la rama `kill`** de `dashboard_view.py`, para que la puerta de arrancar no anuncie «Gaming inerte» cuando lo que hay son categorías de arranque. Sigue estando **antes** de `_require_double_tap` (`:452`), que es lo que el comentario de `:431-435` pretende preservar.
- **Efecto secundario declarado:** un pack gaming con `default_action="start"` y 0/0/0 pasó a decir «Gaming inerte» en la Portada y pasará a decir «no tiene apps que iniciar». Es **más honesto**: el usuario está en la puerta de arrancar.

### 2.7 El texto de confirmación tiene que dejar de mentir

`pack_manager_view.py:523` y `dashboard_view.py:451` arman `« Segunda pulsación para apagar {len(pack.apps)} apps »`. Con 0 apps y 3 categorías marcadas, la confirmación dice **«apagar 0 apps»**. No es un ladrillo, es la clase exacta que este repo sanciona (el `started` en verde del ciclo #26). El texto cuenta **lo que la puerta va a hacer**, no lo que hay en `apps`.

---

## 3. CRITERIOS DE DESCARTE

### 3.1 Multi-etiqueta: DESCARTADO por medición

**Criterio:** *una selección por categoría sólo es ambigua si la resolución «proceso → categoría» es many-to-one.* Es uno-a-uno (§1.2), así que la ambigüedad no se puede construir. `Dict[str, Set[str]]` obligaría a cambiar `_get_process_meta`, la DB, `ProcessInfo.category` (`models.py:9`) y todos los consumidores, para representar un estado que el sistema no tiene.

### 3.2 `stop_categories` + migración: DESCARTADO

`target_categories` **ya está en disco** (`pack_service.py:239`). Renombrarlo exige una migración cuyo fallo silencioso deja el Gaming Mode cerrando de más o sin cerrar nada. Y «añadir `stop_categories` y migrar» son **dos verdades** sobre lo mismo que el `extra="allow"` de `models.py:31` dejarían coexistir en silencio. La asimetría de nombres es el precio de no romper datos, y es un precio de *naming*.

### 3.3 «Borrado de selección heredada»: NO HAY NADA QUE BORRAR

No hay campo derivado, ni valor por defecto que se propague, ni sincronización entre listas. Desmarcar quita el nombre de la lista (`pack_manager_view.py:387-393`) y ya está. `Pack` no tiene ningún campo computed: se descarta por medición.

---

## 4. INVARIANTES DE `AGENTS.md` — VERIFICACIÓN

| Invariante | Riesgo de esta feature | Cómo no se rompe |
|---|---|---|
| **Separación de capas** (UI nunca toca psutil ni JSON) | **Alto**: hoy la vista lee `process_db` (`pack_manager_view.py:365`) y habría que decidir «qué es arrancable» | El **catálogo** y la **resolución de arranque** los devuelve un servicio (§2.3). El guard de `run_tests.py:903-931` ya recorre los cuatro ficheros de UI: se le **añade un predicado**, no se crea uno nuevo |
| **Kill recursivo** (hijos antes que padre) | Que la puerta nueva matara por su cuenta y saltara `children(recursive=True)` (`process_service.py:557`) | La puerta nueva **no mata**: delega en `kill_processes` (`gaming_service.py:164`), la única que lo hace. «Una sola llamada a `kill_processes`» es criterio de cierre, y por construcción **no** puede haber una segunda en el módulo |
| **Blindaje anti-brick** (`SYSTEM_PROTECTED_PROCESSES`) | **El riesgo real de la tarea**: sacar las categorías del `if is_gaming` multiplica las puertas que matan | Las barreras **no se mudan de sitio**: pasan a ser **la razón de que exista** una puerta común, y no se duplican por llamante. El test con `svchost` en pack no-gaming es obligatorio y no negociable |
| **Pack Gaming protegido** | Ninguno | No se toca `delete_pack` (`pack_service.py`). El pack Gaming pasa a ser editable en la misma UI que los demás, que es lo que se pide |
| **Doble pulsación** (`ui/confirmation.py`) | Que se pierda al ampliar las puertas | Las acciones destructivas siguen por `_require_double_tap` (`pack_manager_view.py:524`, `dashboard_view.py:452`) y la bandeja conserva su excepción documentada (`app.py:115-118`) |

---

## 5. TABLA DE CASOS QUE UN TEST TIENE QUE CUBRIR

Cada fila dice **por qué falla sin el fix**. Un test que solo comprueba que una función devuelve un entero no está en esta tabla.

| # | Caso | Por qué **falla** sin el fix |
|---|---|---|
| T1 | Pack **no gaming**, `apps=[]`, `target_categories=[«🟢 Navegadores»]` → al apagar **muere** el navegador y el `keeper` sobrevive | Hoy acaba en `kill_pack_apps([])` (`pack_manager_view.py:548`), que devuelve `0,0,0,0.0` en `process_service.py:596-597`: mata 0 |
| T2 | Ese pack **supera** las cuatro guardas | G-b/G-d (`pack_manager_view.py:495`, `dashboard_view.py:439`) cortan con «no tiene apps» |
| T3 | El acordeón **se renderiza** en un pack no gaming | No entra en `if pack.is_gaming:` (`pack_manager_view.py:336`) |
| T4 | `start_categories` arranca lo resoluble y `started` es **honesto** | El campo ni existe; `:565` y `dashboard_view.py:469` solo leen `apps` |
| T5 | Una categoría 🔴 en `target_categories` de un pack **NO gaming** → **0 matados**, y `svchost` **no llega** a `kill_processes` | Sin la barrera dentro de la puerta común, el rojo llega a la matanza. Es el ladrillo del ciclo #14 |
| T6 | Una categoría 🔴 en `start_categories` → **0 arrancados** | Sin barrera, `_resolver_app` puede devolver una ruta válida de un proceso del sistema |
| T7 | La misma categoría en las dos listas → **gana `kill`** y `started == 0` | Hoy el conflicto no puede existir; sin la política el test no mide nada |
| T8 | `keepers` ganan en un pack no gaming con categoría marcada | Sin R1 antes que R3, el keeper muere |
| T9 | Un **hijo** de uno de la categoría marcada también muere | Una puerta que montara la lista y matara por su cuenta saltaría `process_service.py:557` |
| T10 | `execute_pack` **no** lanza `ValueError` con pack no gaming | `gaming_service.py:109-113` lo lanza hoy |
| T11 | Apagar un pack **no gaming** **no** toca `_last_closed_apps` | El bloque `gaming_service.py:152-161` no mira quién pide el apagado → banner fantasma y restauración Gaming pendiente destruida (§1.7, H1) |
| T12 | Un gaming con `default_action="start"` y `start_categories` en la Portada **no** dice «Gaming inerte» | `dashboard_view.py:436` corta **antes** de la rama del verbo (`:447`) |
| T13 | `Pack(default_action="stop")` sigue levantando `ValidationError` | El encargo daba `"stop"` por bueno; este test congela que no lo es |
| T14 | El catálogo sale de un servicio y la vista **no** lee `process_db` ni repite los 8 nombres | Hoy la vista lo lee (`:365`) y los duplica (`:368-371`); el guard de `:918-931` no mira `process_db` |

---

## 6. FUERA DE ALCANCE

- **No** se implementa nada aquí (Paso 2 del bucle). Los ficheros de `src/` **no se tocan**.
- **No** se multi-etiqueta (§3.1) ni se renombra `target_categories` (§3.2), ni se migra `profiles.json` (§1.11: no hace falta).
- **No** se toca el kill recursivo, el blindaje de nombres ni el orden de `should_kill_for_gaming`: se **reusan**.
- **No** se guarda la ruta de arranque en la DB (§1.8). Lo que no resuelve cuenta como `failed` y se dice en la UI.
- **No** se toca `ui/app.py:119`: la bandeja sigue siendo la puerta del Gaming Mode (§1.5).
- **No** se añade un segundo botón en la Portada (§2.5).
- **No** se tocan `CHANGELOG.md` ni `rd_journal.json`: los escribe el orquestador.

## 7. CRUCE CON OTRAS TAREAS PENDIENTES

- **TASK-059** (marcador de ciclo + hashes del journal, módulo `.taskmaster/git_safe_commit.py`): **sin cruce de código con `src/`**. Se cruza solo en la cadena de versionado.
- **TASK-061** (código de salida de git ante fallo, mismo módulo): **sin cruce de código con `src/`**. Comparte **superficie de validación** con esta tarea: ambos escriben en `run_tests.py` y los dos tocan `validate_docs.py`.
- **Consecuencia práctica, anotada:** las dos Aquinas añadirán tests, así que el recuento derivado con `ast` de `run_tests.py` cambia en cada una. Quien implemente TASK-063 **re-deriva** el número con el validador y sincroniza los cuatro ficheros (`STATUS.md`, `AGENTS.md`, `README.md`, tabla de `docs/ai/testing-guide.md`) **en la misma pasada**. No se copian cifras de memoria: es la lección que el panel de `STATUS.md` ya cobra.
