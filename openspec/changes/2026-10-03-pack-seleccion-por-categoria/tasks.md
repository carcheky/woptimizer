# Tasks: `2026-10-03-pack-seleccion-por-categoria`

**Tarea:** `TASK-063` · **Estado:** planificado, **sin implementar** (Paso 2 del bucle).
**Contrato de diseño:** `proposal.md` §2 (decisiones) y §4 (invariantes). El log de lo corregido respecto al borrador anterior está en `proposal.md` §0.

> Quien implemente debe leer `proposal.md` §1 antes de tocar `src/`: **la mitad de lo que parece nuevo ya existe**, y cuatro de las cinco cifras que se necesitan están medidas y son distintas de las que se suponían.

---

## Orden de ejecución — y por qué NO es negociable

```
T-1 puerta común con barreras DENTRO
  └─> T-2 catálogo + arranque por categoría (servicio)
        └─> T-3 el campo start_categories
              └─> T-4 las CUATRO guardas, por puerta
                    └─> T-5 acordeón para todos + conflicto espejo
                          └─> T-6 cableado de las DOS puertas + guards estáticos
                                └─> T-7 documentación viva
                                      └─> T-8 recuento + validate_docs 0 FAIL + mutation-auditor
```

**La razón de que T-1 vaya primero (hallazgo del briefing, medido):** la barrera anti-brick no está en el modelo ni en la vista, está **pegada a `execute_gaming_pack`** (`gaming_service.py:122-128` y `:141`), que además **rechaza** packs no gaming con `ValueError` (`:109-113`). Entre el commit que amplía el consumo de categorías y el commit que crea la puerta común con las barreras dentro, el anti-brick está **abierto**. Por eso el orden no es estético: T-1 es la única subtarea que hace reutilizable la barrera, y todo lo demás solo la **amplía**.

**Lo que pasa en cada ventana intermedia, declarado para que nadie lo lea como un forgot:**

| Ventana | Estado real | Por qué es aceptable |
|---|---|---|
| Entre T-1 y T-5 | La puerta común existe con sus barreras dentro, pero **ninguna puerta no-gaming la usa**: las categorías marcadas siguen sin ejecutarse | Nada nuevo puede matar. La barrera ya es reutilizable |
| Entre T-5 y T-6 | La UI **escribe** categorías en packs no gaming, pero la puerta sigue yendo a `kill_pack_apps` | Por T-4 la puerta **ya no dice «no tiene apps»**: entra, mata 0 y lo dice con honestidad (`mensaje_cierre_pack` con 0 cerrados **no lleva tick ni verde**). Un no-op honesto durante un commit, no un ladrillo |
| Entre T-4 y T-5 | Las guardas ya admiten packs con 0 apps, pero la UI todavía no puede expresar la selección | El pack se apaga por sus apps, como antes. Ninguna regresión |

**La razón de que T-4 vaya antes de T-5:** si la UI expone el control antes de que las guardas se abran, el usuario marca una categoría y recibe «no tiene apps que apagar». **Un control visible que no hace nada es peor que un control ausente.**

---

### T-1 · Servicio: la puerta ÚNICA de apagado por pack, con las barreras DENTRO

- **Fichero:** `src/woptimizer/services/gaming_service.py` (único fichero de `src/` que se toca en esta subtarea).
- Añadir `execute_pack(pack)` — puerta de apagado **general**, sin la guarda `is_gaming`. **Conserva íntegros** G4/G5 (`process_service` blindaje en `:136-137` y barrera 🔴 del snapshot en `:141-143`) y G0 (snapshot forzado, `:117`).
- **Mover aquí la barrera G1** (`:122-128`) para que cubra **también** `start_categories` cuando se use como criterio de seguridad de arranque. Predicado único: `get_safety_badge(c)["tier"] != "danger"`.
- 🔴 **CONDICIONAR EL BLOQUE DE RESTAURACIÓN (`:152-161`, hallazgo H1).** Hoy sobrescribe `self._last_closed_apps` sin mirar quién pide el apagado. Con `execute_pack` como puerta común, un apagado de pack normal **destruye una restauración Gaming pendiente** (`restore_gaming_session()` vacía la lista en `:31-32`) y **enseña un banner fantasma** (`dashboard_view.py:262`). El bloque queda **condicionado a `pack.is_gaming`**, con un comentario que diga por qué.
- `execute_gaming_pack` pasa a **delegar** en `execute_pack` (wrapper de compatibilidad). **No** se borra en esta pasada: `ui/app.py:119` lo sigue usando **a propósito** (`proposal.md` §1.5) y `run_tests.py:789` exige su `ValueError`.
- **Criterio discriminante:** con `is_gaming=False`, `target_categories=[«🔴 Sistema de Windows»]` y un snapshot que **incluye `svchost`**, lo que llega a `kill_processes` está **vacío**. *Falla sin el fix* porque el proceso rojo solo se frenaba en `execute_gaming_pack`, que hoy rechaza este pack antes de mirar nada.
- **Punto de cierre:** sigue habiendo **una sola** llamada a `kill_processes` en el módulo (`:164`). Si aparece una segunda, está mal: el kill recursivo y el blindaje viven en esa función y solo en esa. Y `svchost` no está en `SYSTEM_PROTECTED_PROCESSES` (`is_system_protected('svchost')` es `False`, medido y escrito en el docstring de `run_tests.py:662`), así que **solo** la barrera de categoría lo detiene.

### T-2 · Servicio: el catálogo y la resolución de arranque

- **Fichero:** `src/woptimizer/services/process_service.py`.
- `categorias_disponibles()` → lista ordenada con `ordenar_categorias` / `CATEGORY_ORDER` (`config.py:153`, `:157`). **Fuente única**: sustituye a la vez el `process_db` que lee la vista (`pack_manager_view.py:365`) y los 8 nombres repetidos a mano (`:368-371`), con `⚪ Otros` como **U+26AA** (`docs/known-issues.md`).
- `start_pack_categories(categorias)` → nombres candidatos por categoría y luego `_resolver_app` (`:672`) por cada uno.
- 🔴 **`started` se incrementa DESPUÉS de `_lanzar`, dentro del `try`** — copiando `process_service.py:829-830`, **no** «fuera del `try» como dice el docstring (`:817`) y como repetía el borrador (`proposal.md` §1.9, H4). Invariante: **`started` cuenta solo si `_lanzar` no lanzó**; un rechazo cuenta como `failed` (`:824-828`).
- Una categoría 🔴 se filtra **antes** de resolver nada.
- **Criterio discriminante:** una categoría sin **ningún** ejecutable resoluble devuelve `started == 0` y `failed > 0`. *Falla sin el fix* porque el método no existe y no hay forma de que el techo de `proposal.md` §1.8 se pueda expresar.
- **Logro de capa:** la vista deja de leer ficheros y `process_db`. La comprobación es `grep` sobre el guard que ya existe (`run_tests.py:918-931`), **añadiendo un predicado**.

### T-3 · Modelo: **un** campo nuevo, y su contrato

- **Fichero:** `src/woptimizer/models.py`, en `Pack`, junto a `target_categories` (`:37`).
- `start_categories: List[str] = Field(default_factory=list)`, con un comentario que diga **por qué no se renombra** `target_categories` (`proposal.md` §3.2).
- **Contrato, escrito en el comentario:** default `[]`; ausente == vacío a propósito; `[]` significa «no arrancar por categoría»; **no** es `Optional`/`None`; `start_categories ∩ target_categories = ∅` se impone al escribir y se resuelve en el servicio.
- **Nada más.** `default_action` no se toca: sigue `Literal["start", "kill"]` (`:54`) y `"stop"` sigue siendo error de escritura (`run_tests.py:8210-8216`).
- **Sin migración.** Y esto **no es una afirmación, es una medición** (`proposal.md` §1.11): la rama legacy entrega el registro entero a `Pack` para que «en cuanto `Pack` gane un campo, esta rama lo lea sin que nadie se acuerde» (`pack_service.py:350-353`), y las cinco copias del pack van con `model_copy(deep=True)` (`:588`, `:596`, `:601`, `:629`, `:639`). Ninguna es campo a campo.
- **Criterio discriminante:** un `profiles.json` **sin** la clave carga con `[]` y su `save()` posterior no la inventa; uno **con** la clave sobrevive al ciclo carga → guarda de un build que no la conoce (por `extra="allow"`, `models.py:31`). *Falla sin el fix* porque la clave no existe y el campo no viaja.

### T-4 · Las CUATRO guardas, y cada una por su puerta

- **Ficheros:** `src/woptimizer/ui/views/pack_manager_view.py` y `src/woptimizer/ui/views/dashboard_view.py`.
- `pack_manager_view.py:495` — `not pack.apps` pasa a ser «sin apps **y** sin `target_categories`» (no tocar `:493`).
- `dashboard_view.py:439` — el gemelo de la Portada, **que el borrador no declaraba** (H2).
- `pack_manager_view.py:556` (`start_pack`) — «sin apps **y** sin `start_categories`».
- 🔴 **`dashboard_view.py:436` (`es_pack_inerte`) se mueve DENTRO de la rama `kill`** (`:447`), y el guard de arranque pasa a usar `start_categories`. Motivo: `es_pack_inerte` significa «el Gaming no tiene **nada que cerrar**» (`feedback.py:194-199`), o sea, es un predicado de la puerta de **kill**; hoy se evalúa **antes** de la rama del verbo y por eso un pack con `default_action="start"` y `start_categories` marcadas oye «Gaming inerte». **No se le cambia la firma** (`run_tests.py:157-204` vigila el contrato de sus llamantes).
- El guard sigue estando **antes** de `_require_double_tap` (`:452`): es lo que el comentario de `:431-435` dice que preserva.
- **Efecto secundario declarado** (`proposal.md` §2.6): un gaming con `default_action="start"` y 0/0/0 pasa a decir «no tiene apps que iniciar» en vez de «Gaming inerte». Es más honesto: el usuario está en la puerta de arrancar.
- **Criterio discriminante:** un pack no gaming con `apps=[]`, `target_categories=[«🟢 Navegadores»]` **supera** la puerta de apagar sin ver «no tiene apps». *Falla sin el fix* porque `:495` corta con `mensaje_sin_apps(name, "kill")` antes de armar la confirmación.

### T-5 · Vista: el acordeón para todos los packs, el conflicto espejo y el texto honesto

- **Fichero:** `src/woptimizer/ui/views/pack_manager_view.py`.
- Quitar el gate `if pack.is_gaming:` de `:336` y el comentario «SOLO GAMING» de `:335`.
- Añadir el segundo juego de casillas para `start_categories`, con la **casilla espejo deshabilitada** cuando la categoría está en la otra lista: el conflicto se evita en la UI (§2.4), no solo se resuelve en el servicio.
- Al desmarcar: quitar el nombre de la lista y `update_pack()` — el mismo camino que ya usa el gaming (`:386-393`). **Nada de mutar la copia**: ese bug ya se pagó (comentario de `:379-384`).
- El catálogo sale de T-2. **La vista no lee `process_db` ni repite la lista de 8.**
- 🔴 **Texto de confirmación honesto** (H6/`proposal.md` §2.7): `:523` y `dashboard_view.py:451` arman `«apagar {len(pack.apps)} apps»`, que con 0 apps y 3 categorías dice **«apagar 0 apps»**. Cuenta **lo que la puerta va a hacer**, no lo que hay en `apps`.
- **Criterio discriminante:** el acordeón **se renderiza** en un pack no gaming, con las dos listas y con la casilla espejo deshabilitada. *Falla sin el fix* porque el control nace dentro de `if pack.is_gaming:` y no existe nada que renderizar.

### T-6 · Cableado de las DOS puertas, y de los guards que las vigilan

- **Las dos de apagar** pasan por `execute_pack`: `pack_manager_view.py:545-548` y `dashboard_view.py:458-461`.
- **Las de arrancar** eligen entre `start_pack_apps(p.apps)` y `start_pack_categories(p.start_categories)` **según el verbo de la puerta**. En el Gestor el verbo lo decide el método (`kill_pack`/`start_pack`, `:507`/`:554`); en la Portada **es `pack.default_action`** (`dashboard_view.py:447`, escrito en `feedback.py:207-209`). **Se mantiene un solo botón en la Portada**; el pack con las dos listas marcadas es medio-usable desde ahí **por diseño** (`proposal.md` §2.5).
- 🔴 **Actualizar, en la MISMA pasada, las tres cosas que rompen:**
  1. `run_tests.py:8456-8465` — la tupla `PERMITIDOS` del guard de workers tiene `("gaming_service", "execute_gaming_pack")` y `("process_service", "start_pack_apps")`: añadir los pares nuevos.
  2. `run_tests.py:8997-9014` — el doble `_GamingGestor` solo expone `execute_gaming_pack`; sin el método nuevo, las pruebas de la Portada y del Gestor revientan con `AttributeError`.
  3. `run_tests.py:918-931` — el predicado `process_db` del guard de capas (de T-2).
- **La bandeja no se toca:** `ui/app.py:119` sigue en `execute_gaming_pack` (`proposal.md` §1.5).
- La doble pulsación se mantiene en las acciones destructivas (`ui/confirmation.py`).
- **Criterio discriminante:** apagar un pack no gaming con una categoría marcada llega a `kill_processes` con **la lista de la categoría**, no vacía. *Falla sin el fix* porque la puerta sigue en `kill_pack_apps(p.apps)`, que con `apps=[]` devuelve `0,0,0,0.0` en `process_service.py:596-597`.

### T-7 · Documentación viva (obligatoria, `AGENTS.md` §📚 regla 1)

- `docs/ai/data-models.md`: el campo `start_categories`, su contrato (§2.2) y la decisión de **no** renombrar `target_categories`.
- `docs/ai/architecture.md`: `execute_pack` como **puerta única**, y por qué las barreras viven **dentro** y no en cada llamante.
- `docs/ai/ui-design-system.md`: el acordeón para packs no gaming, el conflicto espejo, las **cuatro** guardas y el verbo distinto del Gestor y la Portada.
- `docs/ai/testing-guide.md`: **solo** la tabla de recuento (T-8).
- `docs/known-issues.md`: **solo** si aparece una trampa nueva **verificada**.

### T-8 · Cierre verificable: recuento, validador y mutaciones

- `run_tests.py`: los tests de esta tarea están escritos.
- **Las cuatro cifras sincronizadas en la MISMA pasada:** `STATUS.md`, `AGENTS.md`, `README.md` y la tabla de `docs/ai/testing-guide.md`. El check 7 de `validate_docs.py` deriva el número con `ast` y compara contra los cuatro: añadir un test sin sincronizarlos da FAIL.
- `validate_docs.py` en **0 FAIL**.
- **`mutation-auditor` en PASS** sobre las mutaciones de la tabla de abajo. Sin ese PASS, el ciclo no se cierra: `run_tests.py` en verde dice que el código hace lo que el test comprueba, **no** que el test compruebe algo.

---

## Tests a escribir (NO se escriben aquí)

Cada test lleva **por qué discrimina**. Un test que solo comprueba que una función devuelve un entero no está en esta lista.

| # | Test | Por qué discrimina |
|---|---|---|
| 1 | `test_pack_no_gaming_apaga_por_categoria_y_respeta_keepers` | Pack no gaming, `apps=[]`, una categoría marcada → el proceso de esa categoría **muere** y un keeper **sigue vivo**. Hoy la ruta acaba en `kill_pack_apps([])` y mata 0 (`process_service.py:596-597`): **ninguna** línea de esa ruta lee `target_categories` |
| 2 | `test_pack_con_categorias_supera_las_cuatro_guardas` | El pack anterior llega a la puerta en **las dos** vistas. Hoy `:495` y `dashboard_view.py:439` cortan con «no tiene apps» |
| 3 | `test_acordeon_se_renderiza_en_pack_no_gaming_con_espejo_deshabilitado` | El control existe para cualquier pack y el conflicto no se puede construir en la UI | Hoy no entra en `if pack.is_gaming:` (`pack_manager_view.py:336`) |
| 4 | `test_start_categories_arranca_y_cuenta_honestamente` | Arranca lo resoluble; lo no resoluble va a `failed`, **nunca** a `started`. Hoy el campo no existe y `:565`/`dashboard_view.py:469` solo leen `apps` |
| 5 | 🔴 `test_la_barrera_roja_sigue_dentro_de_la_puerta_comun` | Pack **no gaming**, `target_categories=[«🔴 Sistema de Windows»]`, snapshot **con `svchost`**: `killed == 0` **y** lo que llega a `kill_processes` no contiene `svchost`. **Es el ladrillo del ciclo #14.** Reutiliza el doble `_ProcessServiceSpy` que ya existe (`run_tests.py:681-697`) |
| 6 | `test_categoria_roja_en_start_categories_no_arranca` | 0 arrancados. Sin barrera, `_resolver_app` puede devolver una ruta válida de un proceso del sistema |
| 7 | `test_conflicto_misma_categoria_gana_kill` | La categoría queda en `target_categories`, fuera de `start_categories`, y `started == 0`. Hoy el conflicto no puede existir: sin la política el test no mediría nada |
| 8 | `test_keepers_ganan_a_las_categorias_en_pack_no_gaming` | Un keeper cuya categoría está marcada **no** muere. Sin R1 antes que R3, muere |
| 9 | `test_kill_recursivo_desde_la_puerta_por_categoria` | Un hijo de un proceso de la categoría marcada **también** muere. Una puerta que montara la lista y matara por su cuenta saltaría `process_service.py:557` |
| 10 | `test_execute_pack_acepta_pack_no_gaming` | No lanza `ValueError`. Hoy `gaming_service.py:109-113` lo lanza: sin este fix la feature no tiene por dónde pasar |
| 11 | 🔴 `test_apagar_un_pack_no_gaming_no_toca_last_closed_apps` | Tras apagar un pack **no gaming**, `get_last_closed_apps()` sigue con la restauración Gaming pendiente. **Falla sin el fix** por el bloque `gaming_service.py:152-161`: el banner fantasma aparece (`dashboard_view.py:262`) y pulsarlo **destruye** la restauración pendiente (`gaming_service.py:31-32`) |
| 12 | `test_portada_no_anuncia_gaming_inerte_a_un_pack_de_arranque` | Gaming con `default_action="start"` y `start_categories` marcadas **no** ve «Gaming inerte». Hoy `dashboard_view.py:436` corta **antes** de la rama del verbo (`:447`) |
| 13 | `test_default_action_stop_sigue_siendo_error_de_escritura` | `Pack(default_action="stop")` levanta. El encargo daba `"stop"` por bueno; este test congela que no lo es |
| 14 | `test_la_vista_no_lee_process_db_ni_repite_el_catalogo` | `grep`/`ast` sobre los cuatro ficheros que el guard ya recorre (`run_tests.py:918-931`): sin `process_db` y sin los 8 nombres a mano | Hoy la vista lo lee (`pack_manager_view.py:365`) y los duplica (`:368-371`), y el guard no mira `process_db` |
| 15 | `test_el_texto_de_confirmacion_no_dice_apagar_0_apps` | Con 0 apps y 3 categorías, la doble pulsación no arma «apagar 0 apps». Hoy `pack_manager_view.py:523` y `dashboard_view.py:451` lo hacen: es la mentira del `started` en verde, otra vez |

> 🔴 **Los tests se añaden a `run_tests.py` en la MISMA pasada que sus cuatro cifras sincronizadas** (T-8). Esta tarea **no** los escribe: el fichero está en manos de otro actor.

## Mutaciones que este plan deja vivas si nadie las mira

`mutation-auditor` (Paso 4): cada test de la tabla debe **fallar** al romper su fix. Las tres que más costarían dejar pasar:

1. **Quitar la barrera 🔴 de la puerta común** dejando la de `execute_gaming_pack`. Los tests de gaming siguen verdes; solo el **5** lo caza — y por eso el 5 se escribe con un `svchost` real en el snapshot y no con un nombre inventado, porque `is_system_protected('svchost')` es `False`.
2. **Comparar los keepers contra el nombre sin extensión** (`name` en vez de `full_name`). Los keepers se desactivan **en silencio** y ningún recuento baja: hay que mirar **`killed`**, no el número de llamadas.
3. **Dejar el bloque de `_last_closed_apps` sin condicionar.** Ningún recuento de la sesión Gaming baja, porque el daño no está en el apagado: está en lo que pasa **después**, cuando el usuario pulsa «Reabrir». Solo el **11** lo ve, y solo si mira la lista, no el texto del banner.
