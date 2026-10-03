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
- **Los cuatro ficheros de recuento, en la MISMA pasada, y con la cifra que MANDA:** la derivan `validate_docs.py` y el check 7 con `ast` (`validate_docs.py:13-74` y `:508-563`), contando las llamadas `test_*()` alrededor del marcador estructural `run_tests.py:15782`. Hoy son **123 = 95 backend + 28 headless**, declarados en `STATUS.md:9`, `AGENTS.md:69`, `README.md:62` y `docs/ai/testing-guide.md:170`, y la tabla de la guía tiene **una fila por test** (`validate_docs.py:148-158`). T-9 **también** mueve la cifra, y por eso su número es 124 = 95 + 29.
- **Las cuatro cifras sincronizadas en la MISMA pasada:** `STATUS.md`, `AGENTS.md`, `README.md` y la tabla de `docs/ai/testing-guide.md`. El check 7 de `validate_docs.py` deriva el número con `ast` y compara contra los cuatro: añadir un test sin sincronizarlos da FAIL.
- `validate_docs.py` en **0 FAIL**.
- **`mutation-auditor` en PASS** sobre las mutaciones de la tabla de abajo. Sin ese PASS, el ciclo no se cierra: `run_tests.py` en verde dice que el código hace lo que el test comprueba, **no** que el test compruebe algo.

### T-9 · La invariante del acordeón, afirmada por **EFECTO** (cierra el FAIL del ciclo 51)

**Por qué existe esta subtarea.** El test #3 es una red **estática** sobre un único fichero, y lleva nueve rondas de mutación: cada arreglo cerró una FAMILIA de formas de gate y dejó vivo un miembro de la siguiente (`U1` → `U1_AND` → variable/helper/guard/alias/`getattr`/predicado → gate en el lugar de la llamada → lista filtrada a dos saltos → techo declarado → casilla en una comprehension → `assert` delante). El análisis del dev es la razón de fondo y **no se discute**: sobre un solo fichero, "¿puede esta sentencia impedir la construcción?" es **alcanzabilidad**, y toda propiedad semántica no trivial lo es. `_CONDICIONALES` no se puede cerrar por dentro: **añadir un tipo de nodo a una lista no acerca la invariante, solo desplaza el borde.**

**La decisión.** El invariante se deja de preguntar por la **forma** y se pregunta por el **efecto**: *la vista real, montada de verdad, da a cada pack el catálogo completo en las dos direcciones*. Y hay tres hechos medidos que lo sostienen:

1. **La premisa del docstring del #3 es FALSA.** `run_tests.py:14205-14206` justifica el método estático con que «el arnés no abre ventana, y una casilla de CustomTkinter sin `CTk`/`root` no se puede instanciar». Pero `test_headless_ui` (`run_tests.py:268-288`) monta un `WOptimizerApp` real con `app.run()`, y `test_main_window_navigation_transitions` (`run_tests.py:8352-8382`) monta un `ctk.CTk()` real, lo hace `withdraw()` y llega a un `PackManagerView` **de verdad** con `win._show_packs()`. La premisa es superable, y **esa frase es la que ha inviteado nueve rondas**: hay que corregirla en la misma pasada o invita la décima.
2. **El camino hasta las casillas existe y es corto** (medido en una cámara en `%TEMP%`, copia de `src`, repo intacto): `PackService(data_path=tmp)` + `create_user_pack(...)` + `ProcessService()` real → `PackManagerView(root, ps, pack_s)` → `root.update_idletasks()` → `vista.scroll_frame.winfo_children()`. **Sin `mainloop`, sin `after`, sin bombeo.** Destruye en `finally`.
3. **No son seis casillas.** Medido en este host: `categorias_disponibles()` devuelve **9** categorías (`process_service.py:842-866` une `_db_map` con `CATEGORY_ORDER` y quita `⚪ Otros`), y la vista construye **18** casillas por tarjeta (dos tandas espejo). Un test escrito con el «6» del encargo —o con el «6» del arnés sintético del auditor— **falla hoy** en este host, y uno escrito con el número del arnés pasa **por el motivo equivocado**.

**Qué afirma, y con qué variante muere cada una (medido, no supuesto).**

| Aserción | Qué mide | Mutante | Medido |
|---|---|---|---|
| **E0** | `len(catálogo) >= 1` antes de assertar nada | `G_CATALOGO_VACIO` (`categorias_disponibles()` devuelve `[]`) | **MUERE**: sin esto, un catálogo vacío hace que E2 sea vacuo y el usuario no ve nada con el test en verde |
| **E3** | la construcción de la vista **no revienta**; se re-lanza como `AssertionError` nombrando la invariante | `C_ASSERT_GATE` (`assert pack.is_gaming` delante de `:391`) | **MUERE por aserción**, no por excepción cruda: medido, el render del pack normal revienta con `AssertionError` dentro de `_render_pack_card`, y sin el `try/except` la suite aborta sin que ninguna aserción haya dicho **por qué** está rota la invariante |
| **E1** | `len(tarjetas) == len(packs)` | `A_GATE_EN_LA_LLAMADA` (`refresh_packs`: `if p_id != "gaming" and p.is_gaming:`) | **MUERE por E1**: 1 tarjeta de 2 |
| **E2** | por **cada** tarjeta y por **cada** categoría `c` del catálogo: exactamente una casilla con texto `c` y exactamente una con texto `f"{c} (arrancar)"` | `B_LISTA_FILTRADA` (`sorted_cats = ordenar_categorias(all_cats) if pack.is_gaming else []`) | **MUERE por E2**: 0 casillas / 9 faltan en la tarjeta normal |
| **E2** | ídem | `F_LAMBDA_MAP` (`def _caja` + comprehension gateada) | **MUERE por E2**: 27 casillas / 9 faltan |
| **E2** | ídem | `H_RENOMBRAR` (`" (arrancar)"` → `" (arrancar más tarde)"`) | **MUERE por E2**: la etiqueta **es** el contrato con el usuario |

Base: `REPO` → E1=E2=True, 18 casillas y 0 faltan en las dos tarjetas.

**Por qué esto cierra la familia y no solo la siguiente forma.** E2 no mira **cómo** está escrito el código: mira **qué etiquetas hay**. Con eso mueren de golpe el `if` delante, el guard clause, la lista filtrada en la asignación o en cualquier salto de la cadena, la comprehension filtrada, el `map`/`lambda`, el `assert` delante y la lista que llega de otra función por una llamada — las familias de las nueve rondas, sin una entrada más en ninguna lista. Y el coste es **un test**, no un tipo de nodo.

**El número es un invariante, no una cifra mágica.** E2 **no** comprueba un total. Comprueba, por categoría, `exactamente una` y `exactamente una`: así (a) una lista filtrada a tres de seis **no** pasa por tener menos, (b) una tanda duplicada **no** pasa por tener más, y (c) un control legítimo nuevo **sí** pasa, porque su etiqueta es otra cadena. El total sale solo (`2 × len(catálogo)`) y **no se escribe en el test**: escribirlo reintroduce el número mágico, que es lo que hace que la suite dependa del host.

**El falso positivo, mirado ANTES de escribir el test (es la mitad del trabajo).** El riesgo real de un test de efecto es rechazar código legítimo, y aquí está medido: el falso positivo que forzó a reescribir el estático en la ronda 4 —*una casilla propia del Gaming Mode dentro del acordeón*— **no rompe E2**, porque su etiqueta no es `c` ni `c + " (arrancar)"`; el estático sí lo rechaza. Los dos que **sí** quedan son: (i) una tercera tanda espejo que **reutilice** las dos etiquetas (se rechaza a propósito: son el contrato de las dos direcciones, y quien quiera una tercera le da su propio sufijo), (ii) una categoría del catálogo que se llamara exactamente `otra + " (arrancar)"` (imposible mientras `⚪ Otros` no se ofrezca, y `process_service.py:863` lo impide). **El mensaje de E2 tiene que decir el motivo** —el contrato de las dos direcciones— y el remedio, porque un aserción sin motivo obliga a aflojar y eso garantiza que se afloje.

**Qué pasa con A1/A2/A3: se CONGELAN, no se tocan ni se borran.** Y no son una copia de E2: **(a) no afirman lo mismo** —lo estático afirma «ninguna construcción del acordeón depende de `is_gaming`» (espacio negativo, y caza minas de comportamiento neutro como `if pack.is_gaming or True:`, que E2 deja pasar **y está bien que deje pasar**), lo de efecto afirma «cada tarjeta ofrece el catálogo completo en las dos direcciones»; **(b) borrarlas porque otra cosa también pasa sería el movimiento de «relajar» en su forma más pura**; y **(c) hay prueba medida de que no se solapan**, aunque la prueba que se citaba estaba **mal medida y era FALSA**, y el motivo importa más que la cifra (corregido en la ronda 11): se afirmaba que el mutante `E_COSMETICA_IF` (`cb.grid(row=i // (2 if pack.is_gaming else 1), ...)`) lo mata el techo (f) del estático. **Medido con la suite entera: NO lo mata, y el 3-E tampoco.** El techo (f) declara, textual, «un bucle **ENCIMA** de la construcción cuyo **iterable** es una elección de `is_gaming`», y su propio `COSMETICA_IF` es `if (2 if pack.is_gaming else 1) == 2:`, que **cambia la cantidad** de widgets; la forma escrita cambia el `row=` y no la cantidad, así que está **fuera** de (f) por el texto del propio techo. La sonda que se escribió era **otra** que la que el techo cubre, y se le atribuyó el veredicto del techo. La mitad que **sí** era cierta es la que concierne a E2: esa forma cambia la **fila**, no la **cantidad**, y el motivo que el propio techo declara es «lo que el pack no puede decidir es la CANTIDAD de casillas». **Los dos tienen razón en dejarla pasar** —con ella las 18 casillas se siguen viendo, una por fila, y rechazarla sería el falso positivo del otro lado—, y se declara viva en las dos capas y con su motivo. Para que la no solapación se sostenga hay que citar los casos que sí las separan, medidos en la ronda 9: `A_GATE_EN_LA_LLAMADA` (lo ve solo el efecto, por el recuento de tarjetas) y `C_ASSERT_GATE` (lo ve solo el estático, por A3).

> 🔴 **LA REGLA ANTI-RODADURA, que es lo que impide la ronda 10** (va en el docstring de los dos tests, no aquí): *una familia nueva solo puede añadirse a una capa si NINGUNA regla de la otra capa la mata ya, y el techo se re-reparte de modo que cada eje declarado diga qué capa lo posee.* Sin esa frase, las dos capas se separan y la más difícil de mantener muere sola sin que nadie lo note.

**El residuo, declarado y NO arreglado: el eje (b).** Medido: gatear el `.pack()`/`pack_forget()` de `cat_body` (`pack_manager_view.py:362-368`) deja las 18 casillas **construidas** y E1/E2 **en verde** (`D_PACK_FORGET` → PASA). No se cierra en esta pasada, y el motivo es de arquitectura, no de pereza: para afirmar la **visibilidad** hay que **pulsar** el botón del acordeón, y en el árbol vivo ese botón se identifica **por su nombre o por su texto** — que es exactamente el defecto que las nueve rondas quitaron del test estático. La forma honesta de cerrarlo es **darle al acordeón un punto de entrada identificable por comportamiento** (un método público de la vista que alterne el cuerpo de un `pack_id`), que es un cambio en `src/` y por tanto **otro `change-id`**, no esta tarea. Queda escrito como eje (b) con su precio.

**Los cuatro ficheros de recuento, en la misma pasada** (T-8 los nombra; aquí van los números): `123 → 124` y `28 → 29` headless, `95` backend sin cambio; la tabla de `docs/ai/testing-guide.md` gana la **fila 124**. Y la fila `STATUS.md` del recuento (`STATUS.md:9`) tiene que decir el reparto nuevo, porque el check 7 deriva con `ast` y compara contra los cuatro.

**Test a escribir (NO se escribe aquí):**

| # | Test | Por qué discrimina |
|---|---|---|
| 3-E | `test_todo_pack_ofrece_el_catalogo_completo_en_apagar_y_arrancar` | Vista **real** montada headless, con `PackService` temporal: por cada tarjeta y por cada categoría del catálogo hay exactamente una casilla de apagar y exactamente una de arrancar. *Falla sin el fix* en las seis familias medidas (gate en la llamada, lista filtrada, comprehension, `map`/`lambda`, guard clause, `assert` delante), y sin la vista real ninguna de ellas se puede construir. Va **después** del marcador `run_tests.py:15782`, o no cuenta como headless |

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
