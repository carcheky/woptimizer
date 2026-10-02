# Tasks: `2026-10-03-pack-seleccion-por-categoria`

**Tarea:** `TASK-063` · **Estado:** planificado, **sin implementar** (Paso 2 del bucle).
**Contrato de diseño:** `proposal.md` §3 (precedencia) y §4 (invariantes).

> ⚠️ Esta lista **no se ejecuta** en esta pasada. Quien implemente debe leer
> `proposal.md` §1 antes de tocar `src/`: la mitad de lo que parece nuevo ya existe.

---

## Orden de ejecución

El orden **no es negociable**: T-2 antes que T-3, y T-6 antes que T-7. Sacar el
acordeón de la puerta `is_gaming` antes de que exista la puerta común con sus
barreras abre el anti-brick durante la ventana entre ambos commits.

### T-1 · Servicio: la puerta ÚNICA de apagado por pack

- **Fichero:** `src/woptimizer/services/gaming_service.py`
- Añadir `execute_pack(pack)` — la puerta de apagado **general**, sin la guarda
  `is_gaming`. **Conserva íntegros** G4/G5 (líneas 133-143 actuales): blindaje de
  nombres y barrera 🔴 sobre la categoría del snapshot.
- Mover aquí la barrera G1 (líneas 122-128) para que cubra **también** `start_categories`
  cuando se use como criterio de seguridad de arranque.
- `execute_gaming_pack` pasa a **delegar** en `execute_pack` (wrapper de
  compatibilidad). **No** se borra en esta pasada: hay 3 puntos de entrada
  (`src/woptimizer/ui/app.py:119`, `src/woptimizer/ui/views/pack_manager_view.py:546`,
  `src/woptimizer/ui/views/dashboard_view.py:459`) y una prueba que exige el
  `ValueError`. Su retirada se deja declarada, no hecha a medias.
- **Punto de cierre:** la llamada a la matianza sigue siendo **una sola**
  (`src/woptimizer/services/gaming_service.py:164 kill_processes(to_kill)`). Si
  aparece una segunda llamada a `kill_processes`, está mal: el kill recursivo y
  el blindaje viven en esa función y sólo en esa.

### T-2 · Servicio: el catálogo y la resolución de arranque

- **Fichero:** `src/woptimizer/services/process_service.py`
- `categorias_disponibles()` → lista ordenada con `ordenar_categorias` /
  `CATEGORY_ORDER` (`src/woptimizer/config.py:153`). **Fuente única**: sustituye
  tanto el `process_db` que lee la vista (`pack_manager_view.py:365`) como la
  lista de 8 nombres repetida a mano (`pack_manager_view.py:369`).
- `start_pack_categories(categorias)` → nombres candidatos por categoría, luego
  `_resolver_app` (línea 672) por cada uno. **`started += 1` DESPUÉS del `try`**,
  igual que `start_pack_apps` (precedente en la línea 817): lo que no resuelve
  cuenta como `failed`, nunca como iniciado.
- Una categoría 🔴 se filtra con `get_safety_badge(...)["tier"] != "danger"`
  **antes** de resolver nada.
- **Ilogro de capa:** la vista no lee ficheros ni `process_db`. La comprobación es
  por `grep`, igual que la de `gaming_service.py:84`.

### T-3 · Modelo: **un** campo nuevo

- **Fichero:** `src/woptimizer/models.py`, en la clase `Pack`.
- `start_categories: List[str] = Field(default_factory=list)`, colocado junto a
  `target_categories` (línea 37) con un comentario que diga **por qué no se
  renombra** ese campo (proposal.md §3.4). **Nada más.**
- `default_action` **no se toca**: sigue siendo `Literal["start", "kill"]`
  (línea 54) y `"stop"` sigue siendo un error de escritura (`run_tests.py:8176`).
- **Sin migración** de `profiles.json`: `target_categories` conserva su nombre y
  su contenido. Un `profiles.json` viejo tiene que seguir dando el mismo
  Gaming Mode que antes del cambio.

### T-4 · Vista: el acordeón para todos los packs, y la resolución del conflicto

- **Fichero:** `src/woptimizer/ui/views/pack_manager_view.py`
- Quitar el gate `if pack.is_gaming:` de la línea 336 y el comentario «SOLO GAMING»
  de la línea 335.
- Añadir el segundo juego de casillas para `start_categories`, con **una casilla
  espejo deshabilitada** cuando la categoría está en la otra lista (§3.3): el
  conflicto se evita en la UI, no sólo se resuelve en el servicio.
- Al desmarcar, quitar el nombre de la lista y `update_pack()` — el mismo camino
  que ya usa el gaming (`pack_manager_view.py:386-393`). Nada de mutar la copia.
- `apps` sigue siendo la lista manual y sigue mandando sobre las categorías.

### T-5 · Vista: los DOS guards que bloquean un pack sin apps

- **Fichero:** `src/woptimizer/ui/views/pack_manager_view.py`
- Línea 495: `if not pack.is_gaming and not pack.apps:` **bloquea** un pack con 0
  apps y 3 categorías marcadas. Ampliar el criterio a «no tiene apps **ni**
  categorías que apagar».
- `es_pack_inerte` (`src/woptimizer/ui/feedback.py:193`) hoy exige `is_gaming`
  (línea 201). **Decidir y escribir cuál es el criterio**: si una puerta sin apps
  ni categorías es inerte para *cualquier* pack, la firma cambia y hay que
  actualizar los dos llamantes (`pack_manager_view.py:493`,
  `dashboard_view.py:436`). No se deja a medias: o se cambia con sus dos
  llamantes, o se documenta por qué el gaming es especial.
- **Mismo criterio en la puerta de ARRANCAR** (`pack_manager_view.py:556`): hoy
  `if not pack.apps` impide arrancar por categoría.

### T-6 · Cableado de las tres puertas

- Las tres de apagado pasan por `execute_pack`: `src/woptimizer/ui/app.py:119`,
  `src/woptimizer/ui/views/pack_manager_view.py:546`,
  `src/woptimizer/ui/views/dashboard_view.py:459`.
- Las de arrancar (`pack_manager_view.py:567`, `dashboard_view.py:469`) eligen
  entre `start_pack_apps(p.apps)` y `start_pack_categories(p.start_categories)`
  **según el verbo de la puerta**, no según `default_action` guardado: hoy ya
  está escrito que el verbo lo decide el método
  (`pack_manager_view.py:496-503`, `feedback.py:204-209`). Esa convención se
  respeta y no se cambia «para arreglar» nada.
- La doble pulsación se mantiene en las acciones destructivas (`confirmation.py`).

### T-7 · Documentación viva (obligatoria, `AGENTS.md` §📚 regla 1)

- `docs/ai/data-models.md`: el campo `start_categories` y la decisión de **no**
  renombrar `target_categories`.
- `docs/ai/architecture.md`: `execute_pack` como **puerta única** y por qué las
  barreras viven dentro y no en cada llamante.
- `docs/ai/ui-design-system.md`: el acordeón para packs no gaming, el conflicto
  mirrored y los dos guards.
- `docs/known-issues.md`: sólo si aparece una trampa nueva verificada.

---

## Tests a escribir (NO se escriben aquí)

Cada test lleva **por qué falla sin el fix**. Un test que sólo comprueba que una
función devuelve un entero no está en esta lista.

| # | Test | Por qué discrimina |
|---|---|---|
| `test_pack_no_gaming_apaga_por_categoria_deja_el_resto` | Pack no gaming, `apps=[]`, una categoría marcada → el proceso de esa categoría **muere** y un proceso de otra **sigue vivo** | Hoy la ruta acaba en `kill_pack_apps([])` (`pack_manager_view.py:548`) y mata 0: **ninguna** línea de esa ruta lee `target_categories` |
| `test_pack_con_categorias_no_pasa_el_guard_de_sin_apps` | El pack del caso anterior **supera** los dos guards | Hoy `pack_manager_view.py:495` corta la puerta con «no tiene apps» |
| `test_acordeon_de_categorias_se_renderiza_en_pack_no_gaming` | El control existe en un pack no gaming | Hoy no entra en `if pack.is_gaming:` (`pack_manager_view.py:336`) |
| `test_start_categories_arranca_y_cuenta_honestamente` | Arranca lo resoluble; lo no resoluble va a `failed`, **no** a `started` | Hoy `start_categories` ni existe y sólo se lee `apps` |
| `test_categoria_roja_en_target_categories_no_mata_en_pack_no_gaming` | 0 matados; `svchost` sobrevive | **Es el ladrillo del ciclo #14.** Sin la barrera en la puerta común, el rojo llega a `kill_processes` y la regresión es un Windows inservible |
| `test_categoria_roja_en_start_categories_no_arranca` | 0 arrancados | Sin barrera, `_resolver_app` puede devolver una ruta válida del sistema |
| `test_conflicto_misma_categoria_gana_kill` | La categoría queda en `target_categories`, fuera de `start_categories`, y `started == 0` | Sin la política el conflicto sería un no medible (hoy no puede existir) |
| `test_keepers_ganan_a_las_categorias_en_pack_no_gaming` | Un keeper cuya categoría está marcada **no** muere | Sin el orden R1 antes que R3, el keeper muere |
| `test_kill_recursivo_desde_la_puerta_por_categoria` | Un hijo de un proceso de la categoría marcada **también** muere | Una puerta que montara la lista y matara por su cuenta saltaría el `children(recursive=True)` de `process_service.py:557` |
| `test_execute_pack_acepta_pack_no_gaming` | No lanza `ValueError` | Hoy `gaming_service.py:110` lo lanza: sin este fix la feature no tiene por dónde pasar |
| `test_default_action_stop_sigue_siendo_error_de_escritura` | `Pack(default_action="stop")` levanta | El encargo daba `"stop"` por bueno; este test congela que no lo es |
| `test_catalogo_de_categorias_viene_de_un_servicio` | `grep`: la vista no lee `process_db` ni repite la lista de 8 | Hoy la vista lo lee (`pack_manager_view.py:365`) y duplica los nombres (`:369`) |

> 🔴 **Los tests se añaden a `run_tests.py` en la MISMA pasada que sus cuatro
> cifras sincronizadas**: `STATUS.md`, `AGENTS.md`, `README.md` y la tabla de
> `docs/ai/testing-guide.md`. El check 7 de `validate_docs.py` deriva el número con
> `ast` y compara contra los cuatro; añadir un test sin sincronizarlos da FAIL.
> Esta tarea **no** los escribe: el fichero está en manos de otro actor.

## Mutaciones que este plan deja vivas si nadie las mira

`mutation-auditor` (Paso 4): cada test de la tabla debe **fallar** al romper su fix.
Las dos que más costarían dejar pasar:

1. **Quitar la barrera 🔴 de la puerta común** dejando la de `execute_gaming_pack`.
   Los tests de gaming siguen verdes; sólo T5/T6 lo cazan.
2. **Comparar los keepers contra el nombre sin extensión** (`name` en vez de
   `full_name`, el fallo ya medido en `gaming_service.py:144-145`). Los keepers se
   desactivan **en silencio** y ningún recuento baja: hay que mirar `killed`.
