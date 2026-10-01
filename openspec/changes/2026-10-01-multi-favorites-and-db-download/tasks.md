# Tareas: `2026-10-01-multi-favorites-and-db-download`

Contrato: `proposal.md` del mismo directorio. Encargos 1-4 del propietario.

> Cada criterio de aceptacion esta escrito para **morir sin el fix**. Un criterio que
> solo comprueba "que devuelve algo" no discrimina y no cuenta.

---

## TASK-048 — Favoritos acumulativos en `PackService`

**Modulo**: `src/woptimizer/services/pack_service.py` · **Depende de**: —

- [ ] **T-1** Anadir `set_favorite(pack_id: str, value: bool) -> None` que marca/desmarca **un solo** pack. `pack_id=None` lanza `ValueError` (la semántica de "limpiar todos" desaparece del contrato del metodo: es lo que causaba la exclusividad).
- [ ] **T-2** Anadir `toggle_favorite(pack_id: str) -> bool` que lee el estado **vivo** de `self._data.packs`, lo invierte, persiste y devuelve el valor nuevo. El servicio decide la politica; la UI solo pide el cambio (invariante de capas).
- [ ] **T-3** Retirar `set_favorite` con firma de 1 argumento. **No** dejar las dos: una API que dice una cosa y hace otra es exactamente el fallo que se quiere cerrar.
- [ ] **T-4** **`get_favorite_pack()` (`:644-648`) se borra o se renombra a `get_favorite_packs() -> List[Pack]`.** No tiene ningun llamador en `src/` y con multi-favoritos devuelve una respuesta falsa.
- [ ] **T-5** (FP-3) `_ensure_gaming_pack()` (`:581-590`) restaura `is_favorite = True` en el pack `gaming` cuando ya existe. Sin esto, un "limpiar todos" deja la tarjeta Gaming muerta en la portada de forma permanente.
- [ ] **T-6** Documentar en `docs/ai/architecture.md` que `is_favorite` es un **bool por pack, acumulativo**, y que ya no existe el favorito único.

**Criterios de aceptacion**
- [ ] `test_pack_service_favorites_acumulan`: marcar `a` y `c` deja `["a","c"]`; desmarcar `a` deja `["c"]` (y `b` sigue `False`). *Falla sin T-1: el codigo vigente en `:668-672` borra `a` al marcar `c`.*
- [ ] `test_pack_service_set_favorite_rechaza_none`: `set_favorite(None, True)` lanza `ValueError`. *Falla sin T-1: hoy `None` es valido y borra todos.*
- [ ] `test_toggle_favorite_devuelve_el_estado_nuevo` sobre el `PackService` real: alterna `True/False/True` y cada `save()` persiste. *Falla sin T-2: `toggle_favorite` no existe.*
- [ ] `test_el_pack_gaming_no_puede_quedarse_sin_favorito`: desmarcar `gaming`, recargar el servicio, y afirmar `is_favorite is True`. *Falla sin T-5: `_ensure_gaming_pack` solo recrea si falta, y hoy la tarjeta Gaming se pierde para siempre.*
- [ ] **Guard `ast`**: `get_favorite_pack` no aparece en ningun fichero de `src/woptimizer/**`. *Falla si T-4 se olvida; sin el, la funcion queda viva y mintiendo.*

---

## TASK-049 — Favoritos en Portada: grid adaptativo al ancho

**Modulo**: `src/woptimizer/ui/views/dashboard_view.py` · **Depende de**: TASK-048

- [ ] **T-7** Anadir `ANCHO_MIN_CARD` a `ui/theme.py` (tokens centralizados, ciclo #22). No magic numbers en la vista.
- [ ] **T-8** Calcular `cols` desde el ancho **real** de `buttons_frame` en `refresh_dashboard` (`:319-327`), sustituyendo el `if col > 1` fijo. `max(1, ...)`.
- [ ] **T-9** `grid_columnconfigure(i, weight=1, uniform="fav")` para las columnas activas y **peso 0 para las que sobran** al reducir, si no las columnas fantasma siguen robando ancho.
- [ ] **T-10** Re-maillar en `<Configure>`: la rama `else` de `:328-335` **solo reconfigura texto y nunca recoloca**. Sin esto, ensanchar la ventana deja los botones en la rejilla vieja y el encargo 1 no se cumple.
- [ ] **T-11** `_empty_label` con `columnspan=cols` calculado (hoy `2` hardcodeado en `:305`).
- [ ] **T-12** Extraer el bloque de destruccion **duplicado** (`:292-296` y `:313-317`) a `_destroy_favorite_buttons()` y llamarlo desde las dos ramas. *(FP-1: hoy destruyen bien —`_forget_buttons` limpia `_reposo`, no `_buttons_by_pack_id`— lo que se liquida es la duplicacion, NO un bug de widgets zombis.)*
- [ ] **T-13** Documentar en `docs/ai/ui-design-system.md` la regla de rejilla de favoritos y el umbral `ANCHO_MIN_CARD`.

**Criterios de aceptacion**
- [ ] `test_columnas_de_favoritos_segun_ancho`: con `n` favoritos y ancho `W` dado, las filas son `ceil(n / cols(W))` y el indice de cada boton es `(i // cols, i % cols)`. *Falla sin T-8: con el grid fijo de 2, un ancho que da 4 columnas produce el doble de filas.*
- [ ] `test_regrid_al_redimensionar`: invocar el re-maillado con el ancho cambiado y afirmar que **todos** los botones cambiaron de `column`. *Falla sin T-10: la rama `else` no toca la rejilla, y con los mismos ids el `current_fav_ids != cached_ids` es falso, asi que no se reconstruye nada.*
- [ ] `test_el_placeholder_ocupa_todas_las_columnas`: `columnspan` del `_empty_label` **igual** a `cols` calculado. *Falla si se deja el `2` hardcodeado de `:305` con 4 columnas.*
- [ ] `test_las_columnas_sobrantes_sueltan_el_peso`: tras calcular 4 columnas y luego 2, las columnas 2 y 3 tienen peso 0. *Falla sin T-9: sin la limpieza de pesos, el ancho se reparte entre columnas fantasma.*

---

## TASK-050 — Descarga de DB: URL en constante, GitHub, y fallo observable

**Modulo**: `src/woptimizer/services/process_service.py` · **Depende de**: —

- [ ] **T-14** Extraer `DB_REMOTE_URL` a **constante de modulo** (hoy hardcodeada en `:376`) apuntando a `https://raw.githubusercontent.com/carcheky/woptimizer/main/assets/process_db.json`. **Cambiar a GitLab = cambiar esta constante y nada mas.**
- [ ] **T-15** `load_db_async(callback=None, on_error=None)`. El `except` de `:392-393` deja de ser un `logger.warning` mudo y **avisa a `on_error` con un mensaje honesto**. Firma retrocompatible: `refresh_processes` (`:162`) ya la llama con `callback=` y **no se toca**.
- [ ] **T-16** Mantener el **fallback**: si la descarga falla, la app sigue con el `assets/process_db.json` local empaquetado y el saneado anti-brick se conserva. **No** se toca `_get_process_meta` ni `kill_processes`.
- [ ] **T-17** Documentar en `docs/ai/architecture.md` que la fuente remota es GitHub, que la DB local es el fallback, y **que la descarga no funciona hasta que el propietario publique el repo** (ver `proposal.md` §4).
- [ ] **T-18** Corregir la afirmacion documental de `docs/ai/architecture.md:37`, que hoy dice que la DB *"se actualiza de forma asincrona desde el repositorio oficial en GitLab"*: eso **nunca ha sido cierto** (repo inexistente, verificado). Un documento que afirma que algo funciona sin que exista es un hallazgo, no una opinion.

**Criterios de aceptacion**
- [ ] `test_la_url_remota_es_una_constante_de_modulo`: `process_service.DB_REMOTE_URL` existe, empieza por `https://raw.githubusercontent.com/`, y el literal **no** aparece dentro del cuerpo de `load_db_async`. *Falla sin T-14: hoy la URL esta en la linea 376 dentro del metodo.*
- [ ] `test_un_fallo_de_descarga_se_reporta`: con `urlopen` lanza `URLError`, `on_error` se invoca **con un mensaje no vacío** y `callback` sigueoproliang (la vista se repinta igual). *Falla sin T-15: hoy el `except` se traga el error y el callback se ejecuta sin avisar — el fallo es invisible (FP-2).*
- [ ] `test_la_db_local_sigue_funcionando_sin_red`: sin red, `get_safety_badge` sigue resolviendo desde el JSON empaquetado y **0 procesos de `SYSTEM_PROTECTED_PROCESSES` son cerrables**. *Falla si alguien "simplifica" T-16 dejando la descarga como unico camino.*
- [ ] **Test de red VETADO por contrato** (`proposal.md` §4): ningun test puede exigir que la descarga funcione contra la URL real. Daria verde un dia y rojo otro **sin que cambie el codigo**, porque depende de una accion humana no realizada.

---

## TASK-051 — El boton de descarga que no existe

**Modulo**: `src/woptimizer/ui/views/process_manager_view.py` · **Depende de**: TASK-050

- [ ] **T-19** Cablear `_force_update_db()` (`:166-169`), hoy **sin ningun llamador**, a un boton real en el `footer`. El metodo ya existe y es correcto: lo que faltaba era el `command=`. Verificado por grep: no hay ningun otro punto de entrada.
- [ ] **T-20** El boton pasa `on_error` a `load_db_async` y pinta el fallo en `status_label`: **"DB no actualizada (sin red o repo no publicado). Se usa la local."** — no un texto que aparente exito. Precedente: `PackService.mensaje_danado()` (`pack_service.py:604-609`, Trampa #14, "nada se traga en silencio").
- [ ] **T-21** El mensaje de exito y el de fallo son **distinguibles** por el usuario sin abrir el log.
- [ ] **T-22** Actualizar el literal `"...desde GitLab..."` de `:167`, que miente sobre la plataforma.

**Criterios de aceptacion**
- [ ] `test_el_boton_de_actualizar_db_existe_y_llama`: guarda `ast` que **existe un `CTkButton`/`CTkOptionMenu` cuyo `command` apunta a `_force_update_db`**. *Falla sin T-19: hoy `_force_update_db` es codigo muerto — el fallo mas caro y silencioso que hay (el `mutation-auditor` lo llama explicitamente).*
- [ ] `test_el_fallo_se_pinta_en_el_status_label`: con `on_error` invocado, el texto del `status_label` **contiene** la marca de fallo y **no** contiene "Descargando". *Falla sin T-20: hoy `_render_list` (`:227-231`) sobrescribe con "N apps distintas en ejecucion." y el fallo y el exito se ven IGUALES (FP-2).*
- [ ] `test_exito_y_fallo_dan_textos_distintos`: dos rutas, dos cadenas distintas. *Falla si alguien unifica ambos mensajes en un texto generico.*
- [ ] `test_el_literal_de_plataforma_no_esta_congelado`: ninguna cadena de `process_manager_view.py` dice "GitLab" cuando la constante dice GitHub. *Falla sin T-22: el mensaje de `:167` sigue congelado en GitLab.*

---

## TASK-052 — Una sola flecha en "Seleccionar Pack"

**Modulo**: `src/woptimizer/ui/views/process_manager_view.py` · **Depende de**: —

- [ ] **T-23** Extraer el placeholder a **una constante de modulo**: `PLACEHOLDER_PACK = "Seleccionar Pack"`, **sin el glifo `▼`**. Sustituir las **4** apariciones del literal (`:107`, `:111`, `:196`, `:197`), que hoy pueden divergir entre si.
- [ ] **T-24** **Quitar el glifo, no pelearse con la nativa.** `CTkOptionMenu` ya dibuja su propio indicador: el `▼` del texto es la segunda flecha. Si el color del indicador no casa con el del placeholder, la correccion sigue siendo quitar el glifo, no tocar el widget.
- [ ] **T-25** La comparacion de `:196` debe usar la constante, no el literal repetido.

**Criterios de aceptacion**
- [ ] `test_el_placeholder_no_lleva_glifo`: `PLACEHOLDER_PACK` no contiene `▼` (`U+25BC`). *Falla sin T-23: hoy el glifo esta 4 veces y el test ve uno vivo.*
- [ ] `test_el_placeholder_esta_centralizado`: el literal aparece **exactamente una vez** en el fichero (la definicion de la constante). *Falla sin T-23/T-25: hoy esta en 4 lineas, y ese es el mecanismo por el que dos de ellas divergen en el futuro.*
- [ ] `test_la_comparacion_usa_la_constante`: la rama de `:196` compara contra la constante. *Falla si queda un literal: es la divergencia silenciosa, no un error visible.*

---

## TASK-053 — Tests existentes, recuento y cierre documental

**Modulo**: `run_tests.py` + 4 ficheros de recuento · **Depende de**: TASK-048, 049, 050, 051, 052

- [ ] **T-26** Reescribir `test_pack_service_favorite_exclusive` (`run_tests.py:989-1012`) como `test_pack_service_favorites_accumulan`. Las 3 aserciones (`:1001`, `:1005`, `:1008-1009`) son de **exclusividad** y las tres invertidas.
- [ ] **T-27** Reescribir `test_toggle_favorite_desmarca` (`run_tests.py:5734-5832`): el `_Grabador` (`:5777-5779`) colapsa el estado a un unico favorito. El caso (4) (`:5812-5816`) debe dejar **`{"a": True, "b": False}`**, no `{"a": False, "b": False}`. **CONSERVAR** las 3 propiedades que hoy matan mutaciones: lectura **en vivo** (mata el atajo `get_favorite_pack()`), id inexistente no toca el servicio (caso 3, `:5825-5831`), y no-favorito se marca (caso 1).
- [ ] **T-28** **Actualizar los registros del runner**: `:10998` y `:11053`. El runner llama por nombre: un rename sin tocar la lista es `NameError`, no un fallo de asercion.
- [ ] **T-29** **Anadir el 2o argumento en las 3 semillas**: `run_tests.py:3518`, `:3651`, `:3717` (`set_favorite("x")` -> `set_favorite("x", True)`). Sin esto no hay un test rojo: hay un `TypeError` **dentro de los tests de `.bak` y recuperacion**, que senala el archivo equivocado.
- [ ] **T-30** Actualizar el **recuento de tests** en los **cuatro** ficheros que lo declaran — `STATUS.md`, `AGENTS.md`, `README.md` y la tabla de `docs/ai/testing-guide.md`. El check 7 de `validate_docs.py` lo deriva con `ast` desde `run_tests.py` y **falla** si cualquiera se queda atras. Base actual: **91**.
- [ ] **T-31** `verify_ui_syntax.py` y `validate_docs.py` en verde; `run_tests.py` en verde al 100%.

**Criterios de aceptacion**
- [ ] `run_tests.py` reporta el recuento nuevo y los 4 ficheros declaran **ese** numero. *Falla por el check 7 si se anaden tests y no se tocan los cuatro.*
- [ ] Test de regresion que comprueba que `set_favorite` con **un** solo argumento ya no existe en `run_tests.py`. *Falla si T-29 se dejo a medias, que es el fallo invisible de este encargo.*
- [ ] `docs/ai/ui-design-system.md` documenta la estrella acumulativa, el grid de favoritos y el placeholder sin glifo; `docs/ai/architecture.md` documenta la API de favoritos y la fuente remota.

---

## Orden de ejecucion

```
TASK-050 ──┬─> TASK-051 ──┐
TASK-052 ──┘              │
TASK-048 ──> TASK-049 ────┼─> TASK-053
                          │
              (accion humana, FUERA del grafo)
              publicar repo + assets/process_db.json en GitHub
```

## Limite de dependencia externa

El unico punto donde el grafo sale del repo es la publicacion del repo (§4). Hasta que ocurra, **el resultado esperado del boton es "⚠️ no se pudo actualizar; se usa la DB local"**. Ninguna tarea puede cerrarse probando que la descarga funciona de verdad, y ninguna tarea puede declarar esto un bloqueante para cerrar el ciclo: el boton existe, es honesto sobre el fallo y degrada con seguridad.
