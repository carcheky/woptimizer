# Proposal: Selección por categoría para TODOS los packs (apagar y arrancar)

**Change ID:** `2026-10-03-pack-seleccion-por-categoria`
**Tarea:** `TASK-063`
**Encargo del propietario (textual):** «todos los packs deben dejar seleccionar apagado por categorías (y arrancado)»
**Paso del bucle:** 2 — PLANEAR. Este documento NO implementa nada.

---

## 1. ESTADO REAL MEDIDO (con `fichero:línea`)

Antes de proponer nada, esto es lo que hay hoy en el árbol.

### 1.1 La categoría YA es un campo persistido del pack

`Pack` **ya tiene** la lista de categorías por las que se apaga:

- `src/woptimizer/models.py:37 target_categories: List[str] = Field(default_factory=list)` — es una **lista de NOMBRES de categoría** (cadenas con emoji delante), no una entidad con id. No hay ninguna noción de «categoría» en el modelo más allá de esa lista.
- `src/woptimizer/models.py:35 apps: List[str] = Field(default_factory=list)` — la lista de apps la escribe el usuario a mano, **una por una**.
- `src/woptimizer/services/pack_service.py:239 target_categories=[...]` — el pack de fábrica `DEFAULT_GAMING_PACK` ya viene con 5 categorías marcadas.

**Consecuencia:** la mitad de la petición («apagar por categorías») **ya tiene su formato en disco**. No es un campo nuevo; es un campo que solo está cableado en una cuarta parte de la app.

### 1.2 La categoría es UNA SOLA por proceso — la ambigüedad «multi-etiqueta» no existe

- `src/woptimizer/services/process_service.py:446 def _categorize(self, name: str) -> str` — devuelve **una única cadena**.
- `src/woptimizer/services/process_service.py:447 cat, _, _ = self._get_process_meta(name)` — desestructura una tupla de exactamente tres elementos de la que se queda con UNO, `cat`.
- `src/woptimizer/services/process_service.py:358 db_map[key] = (props.get('category', ...), props.get('priority', ...), props.get('description', ...))` — la base de datos de procesos mapea `patrón → (categoría, prioridad, descripción)`. **Un patrón, una categoría.**

**Medido, no supuesto:** la resolución categoría es **uno-a-uno con el proceso**. La premisa del encargo de que «una app puede estar en varias categorías a la vez» **es FALSA contra el código**: no hay dónde estarlo. Ver §3.1 para el criterio con el que se decide esto.

### 1.3 `default_action` NO enruta nada, y su literal NO es `"stop"`

- `src/woptimizer/models.py:54 default_action: Literal["start", "kill"] = "start"` — es **UN literal por pack**, y el literal es **`"kill"`**, no `"stop"`.
- `run_tests.py:8176` a `run_tests.py:8179` exige explícitamente que `Pack(default_action="stop")` **levante `ValidationError`**. Escribir `"stop"` es un error de escritura, no una sinonimia.
- `src/woptimizer/ui/feedback.py:190 VERBOS = {"kill": "apagar", "start": "iniciar"}` — el único consumidor de `default_action` es el **verbo del texto**. Es un detalle de presentación, no un enrutador de acción.

**Consecuencia:** hoy **no existe** «acción por categoría». Existe (a) una lista de categorías que solo el Gaming Mode lee, y (b) un literal por pack que solo pinta una frase.

### 1.4 El acordeón de categorías está GATED a Gaming Mode

- `src/woptimizer/ui/views/pack_manager_view.py:335 # --- SECCION ACORDEON CATEGORIAS (SOLO GAMING) ---`
- `src/woptimizer/ui/views/pack_manager_view.py:336 if pack.is_gaming:` — **todo** el acordeón (botón, checkboxes, guardado) está dentro de ese `if`.

**Medido:** un pack normal **no tiene ni el control**. No es que la selección se ignoren: es que no se puede ni expresar. La pregunta «¿qué pasa si un usuario quiere apagar solo las apps de Navegadores?» tiene hoy una respuesta exacta: **no puede**, y además la puerta de apagado le diría que no tiene apps (§1.6).

### 1.5 Las TRES puertas de apagado enrutan por `is_gaming`

| Punto de entrada | `fichero:línea` | Comportamiento con pack no-gaming |
|---|---|---|
| Gestor de packs | `src/woptimizer/ui/views/pack_manager_view.py:545 if pack.is_gaming:` | → `src/woptimizer/ui/views/pack_manager_view.py:548 kill_pack_apps(apps)` |
| Portada | `src/woptimizer/ui/views/dashboard_view.py:458 if p.is_gaming:` | → `src/woptimizer/ui/views/dashboard_view.py:461 kill_pack_apps(p.apps)` |
| Bandeja | `src/woptimizer/ui/app.py:119` | `execute_gaming_pack(gaming_pack)` |

- `src/woptimizer/services/process_service.py:592 def kill_pack_apps(self, apps: List[str])` — **solo recibe una lista de apps**. No recibe el pack, no ve `target_categories`. Para un pack no-gaming, las categorías marcadas son **decorativas**.

### 1.6 Un pack no-gaming con categorías marcadas está ADEMÁS bloqueado por el aviso de inerte

- `src/woptimizer/ui/views/pack_manager_view.py:493 if es_pack_inerte(pack.is_gaming, len(pack.apps), len(pack.target_categories)):`
- `src/woptimizer/ui/feedback.py:201 return is_gaming and n_apps == 0 and n_categorias == 0` — `es_pack_inerte` es **FALSO** para un pack no-gaming, así que no avisa de inerte…
- …pero `src/woptimizer/ui/views/pack_manager_view.py:495 if not pack.is_gaming and not pack.apps:` **sí** salta y devuelve «no tiene apps», que **corta la puerta** en `src/woptimizer/ui/views/pack_manager_view.py:516` y en `:534`.

**Medido:** el camino tiene dosABLED, no uno. Quitar solo el `if pack.is_gaming:` del acordeón no basta: el pack seguiría sin poder apagarse, porque el segundo guard lo frena por `apps` vacío.

### 1.7 La barrera 🔴 vive DENTRO de la única puerta que hoy consulta categorías

- `src/woptimizer/services/gaming_service.py:109 if not gaming_pack.is_gaming:` → `raise ValueError` (líneas 109-113). La puerta **rechaza** explícitamente los packs no-gaming.
- `src/woptimizer/services/gaming_service.py:122 categorias_permitidas = sorted(...)` — barrera G1 sobre `target_categories`, con `get_safety_badge(c)["tier"] != "danger"` (línea 124).
- `src/woptimizer/services/gaming_service.py:141 if get_safety_badge(p.category)["tier"] == "danger":` — barrera G5, sobre la categoría del proceso **del snapshot**.
- `src/woptimizer/services/gaming_service.py:164 kill_processes(to_kill)` — la ÚNICA llamada a la vía de kill, que es la que trae el kill recursivo (`src/woptimizer/services/process_service.py:557 for child in parent.children(recursive=True)`) y el blindaje de nombres (`src/woptimizer/services/process_service.py:33 SYSTEM_PROTECTED_PROCESSES`).

**Ésta es la fila que decide el diseño:** la barrera anti-brick **no está en el modelo ni en la vista**, está **pegada a la función que hoy es la única que lee categorías**. Ampliar el consumo de categorías sin ampliar la barrera es exactamente el ladrillo que se rompió en el ciclo #14 y que dejó `svchost` seleccionable.

### 1.8 Arrancar por categoría no existe, y el arranque tiene una restricción real

- `src/woptimizer/ui/views/pack_manager_view.py:565 apps = list(pack.apps)` → `src/woptimizer/ui/views/pack_manager_view.py:567 start_pack_apps(apps)`. Igual en `src/woptimizer/ui/views/dashboard_view.py:469`.
- `src/woptimizer/services/process_service.py:810 def start_pack_apps(self, apps: List[str])` → `src/woptimizer/services/process_service.py:823 ruta = self._resolver_app(app)`.
- `src/woptimizer/services/process_service.py:672 def _resolver_app(self, entrada, raices=None)` — sólo busca dentro de las raíces permitidas (`_launch_roots`, línea 660) y rechaza UNC.
- **La base de datos NO guarda ruta de ejecutable**: `src/woptimizer/services/process_service.py:340 """Carga la base de datos local como hashmap {pattern: (cat, prio, desc)}."""` — tres campos, ninguno es una ruta.

**Consecuencia medible:** «arrancar por categoría» **no puede arrancar cualquier cosa de la categoría**. Una categoría sin ejecutable resoluble bajo las raíces (p. ej. `🟢 Sincronización`, que agrupa procesos de fondo) **no da ni una app arrancable**. El diseño tiene que poder decir eso con honestidad en vez de reportar successes en verde, y el precedente ya existe: `src/woptimizer/services/process_service.py:817` documenta que `started += 1` va **después** del `try` porque un rechazo tiene que contar como `failed`, no como iniciado.

### 1.9 Conclusión del estado real

| Pedido del propietario | Estado medido |
|---|---|
| Apagar por categorías, en **todos** los packs | El **campo** existe (`models.py:37`); el **control** no (`pack_manager_view.py:336`); la **ejecución** no (`pack_manager_view.py:548`) |
| Arrancar por categorías | **No existe en ninguna capa** |

---

## 2. DISEÑO DEL MODELO DE DATOS

### 2.1 Un campo nuevo. Solo uno.

```python
class Pack(BaseModel):
    ...
    target_categories: List[str] = Field(default_factory=list)  # YA EXISTE (models.py:37)
    start_categories:  List[str] = Field(default_factory=list)  # NUEVO
```

**Y sólo ese.** La decisión de **no** renombrar `target_categories` a `stop_categories` está resuelta con el criterio del §3.4.

### 2.2 Significado exacto de cada campo

| Campo | Tipo | Significado | Accidental hoy |
|---|---|---|---|
| `apps` | `List[str]` | Apps **explícitas** que el usuario eligió a mano. Las gobierna `default_action`. | Sí, en las 3 puertas |
| `target_categories` | `List[str]` | Categorías cuyas apps se **apagan** cuando el verbo de la puerta es `kill`. | **No**, salvo Gaming Mode |
| `start_categories` | `List[str]` | Categorías cuyas apps se **arrancan** cuando el verbo de la puerta es `start`. | No existe |
| `keepers` | `List[str]` | Nombres **protegidos**: nunca se apagan. | Sí |

### 2.3 Catálogo de categorías: una sola fuente

`src/woptimizer/ui/views/pack_manager_view.py:369` a `:371` **repiten a mano** la lista de 8 categorías como *fallback* cuando el `process_db` está vacío, y `src/woptimizer/ui/views/pack_manager_view.py:365` lee `self.process_service.process_db` para construir el resto. El orden canónico ya existe y es otro:

- `src/woptimizer/config.py:153 CATEGORY_ORDER = list(PROCESS_CATEGORIES.keys()) + ['⚪ Otros']`
- `src/woptimizer/config.py:157 def ordenar_categorias(...)` — ordena por `CATEGORY_ORDER`, no por el color.

El diseño exige que **la vista deje de construir el catálogo** y lo pida a un servicio. Motivo: la lista de fallback duplicada **no está en `CATEGORY_ORDER`** de forma garantizada, y en cuanto se añada una categoría al config el acordeón de dos sitios puede divergir sin que nada lo note. Es también lo que hace falta para poder **Ofrecer las categorías de arranque** (las arrancables son un subconjunto) sin que la vista adivine.

---

## 3. POLÍTICA DE PRECEDENCIA RESUELTA

### 3.1 «Una app en varias categorías» — PREMISA FALSA, y el criterio

**Criterio que uso:** *una selección por categoría sólo es ambigua si la resolución «proceso → categoría» es de many-to-one. Si es de uno-a-uno, un proceso pertenece a una sola categoría y la ambigüedad no se puede construir.*

**Medido:** `src/woptimizer/services/process_service.py:446` devuelve una cadena y `src/woptimizer/services/process_service.py:358` mapea un patrón a una categoría. Es **uno-a-uno**. Por tanto:

- ❌ **DESCARTADO: multi-etiqueta** (`Dict[str, Set[str]]` de categorías por app). No hay dato que la justifique: obligaría a cambiar `_get_process_meta`, la DB, `ProcessInfo.category` (`src/woptimizer/models.py:9`) y todos los consumidores, para representar un estado que el sistema no tiene. Coste alto, beneficio nulo.
- ❌ **DESCARTADO: categoría canónica impuesta al usuario.** No hace falta arbitrar nada: el proceso trae la suya.

### 3.2 La precedencia que SÍ está resuelta, y que se reusa

La política de decisión **ya existe, está escrita y está probada** para el Gaming Mode:

`src/woptimizer/services/gaming_service.py:47` a `:51` — «1. Si está en keepers -> False; 2. Si está explícitamente en apps -> True; 3. Si la categoría está en target_categories -> True; 4. Resto -> False».

**Se reusa tal cual, sin reordenar** (misma norma que `src/woptimizer/services/gaming_service.py:146` G6). Es decir, el orden normativo es:

| # | Regla | Ámbito | Por qué en esa posición |
|---|---|---|---|
| R0 | Blindaje de nombres (`SYSTEM_PROTECTED_PROCESSES`) + barrera 🔴 sobre la categoría del proceso | **kill** | Irrenunciable: es el anti-brick del ciclo #14. Va antes de todo lo configurable porque no depende de la configuración del usuario |
| R1 | `keepers` → proteger | kill | Un keeper es una promesa explícita del usuario de «esto no se toca» |
| R2 | `apps` explícitas | ambas | Precedencia ya normativa: una app nombrada a mano gana al barrido por categoría |
| R3 | `target_categories` / `start_categories` | ambas | El barrido coge «el resto», nunca pisa lo explícito |

### 3.3 El conflicto real (no era multi-etiqueta, era **stop ∩ start**)

El conflicto de verdad es **la misma categoría en las dos listas**, y sí tiene que resolverse:

- **Criterio:** *ante un conflicto, gana la acción cuyo fallo es irreversible.* Apagar destruye estado y puede romper el SO; arrancar, como mucho, abre una ventana que el usuario cierra. El coste asimétrico manda.
- **Resolución: en el conflicto, gana `kill`.** La categoría queda en `target_categories` y se **quita** de `start_categories`.
- **Defensa en la UI:** al marcar una categoría como «apagar», la casilla espejo en «arrancar» queda deshabilitada, y al revés. No se depende de que la resolución sea correcta: se evita que el conflicto se construya.

### 3.4 Por qué NO se renombra `target_categories` a `stop_categories`

**Criterio:** *el coste de un campo mal nombrado es recuperable; el coste de perder la lista de categorías del pack de fábrica en el `profiles.json` de los usuarios, no.*

- `target_categories` **ya está en disco** en el `profiles.json` de quien tenga el pack Gaming (`src/woptimizer/services/pack_service.py:239`). Renombrarlo exige una migración que lea el campo viejo, y un fallo de esa migración deja el Gaming Mode **cerrando de más** o **sin cerrar nada**, en silencio.
- Los dos nombres no son equivalentes ni se confunden: `target_categories` es «a las que apunta este pack», `start_categories` es «a las que arranca». La asimetría es el precio de no romper datos, y el precio es de **naming**, no de comportamiento.
- **Descartado** el enfoque «añadir `stop_categories` y migrar `target_categories`»: eso son **dos verdades** sobre lo mismo, y lainvariant de `src/woptimizer/models.py:31 model_config = ConfigDict(extra="allow")` haría que las dos coexistieran en silencio.
- **Descartado** el enfoque «borrado explícito de selección heredada»: **no hay herencia que borrar**. No hay campo derivado, ni valor por defecto que se propague, ni sincronización entre listas. Desmarcar una casilla quita el nombre de la lista (`src/woptimizer/ui/views/pack_manager_view.py:391`), y eso es todo. La pregunta se descarta por medición: `Pack` no tiene ningún campo computed.

### 3.5 La política de «qué se puede arrancar»

- Una categoría **🔴** es **inerte en las DOS listas**, con el mismo criterio que ya usa `src/woptimizer/services/gaming_service.py:124`: `get_safety_badge(c)["tier"] != "danger"`. Un solo helper, dos listas, cero deriva.
- Una categoría es **arrancable** sólo si la resolución `categoría → nombres → _resolver_app` produce al menos una ruta válida bajo las raíces permitidas. Lo que no resuelva **cuenta como `failed`**, nunca como iniciado (`src/woptimizer/services/process_service.py:817`).

---

## 4. INVARIANTES DE `AGENTS.md` — VERIFICACIÓN

| Invariante (`AGENTS.md`) | Riesgo de esta feature | Cómo no se rompe |
|---|---|---|
| **Separación de capas** (`:50`, UI nunca toca psutil ni JSON) | Alto: la vista calcula la lista de categorías (`:365`) y habrá que decidir «qué se arranca» | El catálogo **y** el cálculo de qué es arrancable los devuelve un **servicio**. La vista solo pinta checkboxes y llama a un método. El test de grep que hoy vigila el módulo (`src/woptimizer/services/gaming_service.py:84`) se.extiende |
| **Kill recursivo** (`:52`, hijos antes que padre) | Si la puerta nueva matara por su cuenta | La puerta nueva **no mata**: delega en la **misma** `kill_processes` (`src/woptimizer/services/gaming_service.py:164`), que es la única que hace `children(recursive=True)` (`src/woptimizer/services/process_service.py:557`). Un solo camino a la matanza, con test |
| **Blindaje anti-brick** (`SYSTEM_PROTECTED_PROCESSES`) | **El riesgo real de esta tarea.** Sacar las categorías del `if is_gaming` multiplica por N las puertas que matan | Las barreras **no se mueven de sitio**: se convierten en la **única razón** por la que un servicio **común** existe, no se duplican por puerta. Un test con `svchost` en pack no-gaming es **obligatorio** y no es negociable |
| **Pack Gaming protegido** (`:53`) | Ninguno | No se toca `delete_pack`. El pack Gaming pasa a ser **editable en la misma UI** que los demás, que es justamente lo que se pide |
| **Doble pulsación** (`ui/confirmation.py`) | Ninguno nuevo | Las acciones destructivas siguen por `_require_double_tap` (`src/woptimizer/ui/views/pack_manager_view.py:524`, `src/woptimizer/ui/views/dashboard_view.py:452`) |

---

## 5. TABLA DE CASOS QUE UN TEST TIENE QUE CUBRIR

Cada fila dice **por qué falla sin el fix**. Un test que sólo comprueba que una función devuelve un int no está en esta tabla.

| # | Caso | Por qué **falla** sin el fix |
|---|---|---|
| T1 | Pack **no gaming**, `apps=[]`, `target_categories=["🟢 Navegadores"]` → al apagar **muere** el navegador y el `keeper` sobrevive | Hoy va a `src/woptimizer/ui/views/pack_manager_view.py:548 kill_pack_apps([])` → mata 0. Ninguna línea de esa ruta mira `target_categories` |
| T2 | El mismo pack **supera** los dos guards de la puerta de apagar | Hoy `src/woptimizer/ui/views/pack_manager_view.py:495 if not pack.is_gaming and not pack.apps` corta antes de confirmar: el usuario ve «no tiene apps» con 1 categoría marcada |
| T3 | El acordeón de categorías **se renderiza** en un pack no gaming | Hoy `src/woptimizer/ui/views/pack_manager_view.py:336 if pack.is_gaming:` no entra: no existe el control |
| T4 | Pack no gaming con `start_categories` → arranca lo resoluble y `started` es **honesto** | Hoy `src/woptimizer/ui/views/pack_manager_view.py:565` sólo lee `pack.apps`; el campo ni existe |
| T5 | Una categoría 🔴 en `target_categories` de un pack **NO gaming** → **0 matados** | Sin la barrera movida a la puerta común, el proceso rojo llega a `kill_processes`. Es el ladrillo del ciclo #14, reintroducido por ampliación |
| T6 | Una categoría 🔴 en `start_categories` → **0 arrancados** | Sin barrera, `_resolver_app` puede devolver una ruta válida de un proceso del sistema y lo arranca |
| T7 | La misma categoría en `target_categories` y `start_categories` → **gana `kill`**, y el recuento de `started` es 0 | Hoy no hay conflicto posible porque sólo existe una lista; sin la política el test no mide nada |
| T8 | `keepers` ganan en un pack no gaming con categoría marcada | Sin el orden R1 antes que R3, un keeper con categoría marcada muere |
| T9 | Un proceso **hijo** de uno de la categoría marcada también muere (kill recursivo) | Una puerta que construyera la lista y matara por su cuenta saltaría el `children(recursive=True)` de `src/woptimizer/services/process_service.py:557` |
| T10 | La puerta común **no** lanza `ValueError` con un pack no gaming | Hoy `src/woptimizer/services/gaming_service.py:110 raise ValueError` lo hace; sin el fix la feature no tiene por dónde pasar |
| T11 | `Pack(default_action="start")` + `start_categories` → el verbo del texto sigue siendo «iniciar», y `default_action="stop"` **sigue levantando** | Guarda contra la tentación de meter `"stop"` (que el encargo daba por bueno) y contra la de reescribir el verbo |
| T12 | El catálogo de categorías de los **tres** sitios sale del mismo servicio y la vista **no** lee `process_db` | Hoy `src/woptimizer/ui/views/pack_manager_view.py:365` lo lee en la vista y `:369` duplica 8 nombres a mano |

---

## 6. FUERA DE ALCANCE

- **No** se implementa nada en este cambio (Paso 2 del bucle). Los ficheros de `src/` **no** se tocan.
- **No** se multi-etiqueta (§3.1, descartado por medición).
- **No** se renombra `target_categories` (§3.4) ni se migra `profiles.json`.
- **No** se toca el kill recursivo, el blindaje de nombres ni el orden de reglas de `should_kill_for_gaming`: se **reusan**.
- **No** se guarda la ruta de arranque en la DB de procesos (§1.8). «Arrancar por categoría» arranca lo que **resuelve**; el resto se cuenta como `failed` y se dice en la UI.
- **No** se toca la persistencia de `is_gaming` ni la protección del pack Gaming ante borrado.
- **No** se añaden tests a `run_tests.py` en esta pasada: el check 7 de `validate_docs.py` deriva el número de tests con `ast` y lo compara contra `STATUS.md`, `AGENTS.md`, `README.md` y la tabla de `docs/ai/testing-guide.md`. Añadir tests sin sincronizar los cuatro da FAIL. Los tests se **describen** en `tasks.md`; quien implemente los escribe **y** sincroniza las cuatro cifras en la misma pasada.
- **No** se toca `CHANGELOG.md` ni `rd_journal.json`: los escribe el orquestador.
