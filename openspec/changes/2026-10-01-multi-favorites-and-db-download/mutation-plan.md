# Plan de verificacion — Paso 4 (mutacion)

Target: `2026-10-01-multi-favorites-and-db-download`. Agente: `mutation-auditor`.
Tabla canonica del repo: `.agents/agents/mutation-auditor/agent.md:37-50`.

Regla del repo que se aplica aqui: **una mutacion que sobrevive no se documenta, se
arregla**. No se admite "riesgo aceptado" en acumulacion de favoritos ni en seguridad.

---

## M1 — Favoritos acumulativos (TASK-048)

| Mutacion | Por que es la que haría un dev real | Test que debe morir |
|---|---|---|
| `set_favorite` vuelve a `v.is_favorite = (k == pack_id)` (el bucle de `pack_service.py:668-672`) | Volver al exclusivo es el refactor más tentador: "simplifica" el método | `test_pack_service_favorites_accumulan` |
| `toggle_favorite` hace siempre `value=True` (se le "olvida" el else) | El bug del toggle clásico: marcar es fácil, desmarcar se forgets | `test_toggle_favorite_devuelve_el_estado_nuevo` |
| `toggle_favorite` lee `self.render_pack.is_favorite` (la **instantánea** del render) en vez del estado vivo | Es EXACTAMENTE el bug de FIX-006 que ya rompió este repo una vez (`run_tests.py:5749-5751`) | `test_toggle_favorite_desmarca` caso (2) |
| Se conserva el atajo `get_favorite_pack()` en el grabador | La mutación ya catalogada en `agent.md:52` | `test_toggle_favorite_desmarca` caso (4) |
| `_ensure_gaming_pack` deja de restaurar `is_favorite` | Borrar la línea que "no hacía nada visible" | `test_el_pack_gaming_no_puede_quedarse_sin_favorito` |
| Se olvida `pack_id=None -> ValueError` | Aceptar `None` es el atajo para no tocar llamadores | `test_pack_service_set_favorite_rechaza_none` |

## M2 — Grid adaptativo (TASK-049)

| Mutacion | Por que | Test que debe morir |
|---|---|---|
| `cols` vuelve a la constante `2` (`if col > 1`) | El código original, que es "lo que ya funcionaba" | `test_columnas_de_favoritos_segun_ancho` |
| `cols = ancho // ANCHO_MIN_CARD` **sin** `max(1, ...)` | Con ventana estrecha sale 0 columnas → `ZeroDivisionError` o bucle infinito | `test_columnas_de_favoritos_segun_ancho` |
| Quitar el re-maillado del `<Configure>` (T-10) | Es lo que "no hace falta" si solo se prueba el arranque | `test_regrid_al_redimensionar` |
| `grid_columnconfigure` sin `uniform=`, o sin poner a 0 las columnas sobrantes | El reparto queda desigual y **parece** funcionar | `test_las_columnas_sobrantes_sueltan_el_peso` |
| Dejar `columnspan=2` hardcodeado en el `_empty_label` | Copiar-pegar de la linea 305 | `test_el_placeholder_ocupa_todas_las_columnas` |

**Nota de atribucion:** `test_regrid_al_redimensionar` debe construirse con un grabador
de `grid` que registre `(row, column)` por llamada, **no** leyendo `grid_info()` de un
widget real. Sin eso, el test no distingue "recoloco" de "no recoloco" si el ancho
calculado coincide por casualidad con el anterior.

## M3 — Descarga y boton (TASK-050, TASK-051)

| Mutacion | Por que | Test que debe morir |
|---|---|---|
| `except Exception: pass` (o volver a solo `logger.warning`) sin `on_error` | El `except` mudo es lo que hay HOY en `process_service.py:392-393` | `test_un_fallo_de_descarga_se_reporta` |
| Quitar el boton, o su `command=_force_update_db` | Revertir el cableado: es el fallo de "código testeado y no usado" | `test_el_boton_de_actualizar_db_existe_y_llama` |
| `on_error` invocado pero el `status_label` no se pinta | Separar la señal del servicio de su reflejo en la UI (es lo que pasa hoy) | `test_el_fallo_se_pinta_en_el_status_label` |
| Un solo texto para exito y fallo | "Simplificar" los dos mensajes | `test_exito_y_fallo_dan_textos_distintos` |
| La URL vuelve a estar hardcodeada en el cuerpo de `load_db_async` | Dejar la constante y seguir usandola en el sitio viejo | `test_la_url_remota_es_una_constante_de_modulo` |
| Bajar la DB local, o saltarse el saneado anti-brick en la carga | "Optimizar" la ruta de fallback | `test_la_db_local_sigue_funcionando_sin_red` |

**Prohibido para este bloque:** ninguna mutacion ni test puede tocar la red real. El
repo remoto **no existe** (verificado: `api.github.com/users/carcheky` -> 200, el repo
-> 404). Un test de red daria verde un dia y rojo otro sin que cambie el codigo, y
`run_tests.py` debe seguir siendo **determinista y offline**.

## M4 — Flecha unica (TASK-052)

| Mutacion | Por que | Test que debe morir |
|---|---|---|
| Volver a poner `"Seleccionar Pack ▼"` en una de las 4 lineas | Revertir solo una copia: es el fallo que produce "dos flechas otra vez" sin tocar el resto | `test_el_placeholder_no_lleva_glifo` + `test_el_placeholder_esta_centralizado` |
| Dejar la comparacion de `:196` con el literal, no con la constante | La divergencia silenciosa: el placeholder del `StringVar` y el de `values` dejan de ser el mismo | `test_la_comparacion_usa_la_constante` |

**Trampa de emojis (Trampa #16 y la de `⚪ Otros`):** el glifo es `▼` = **U+25BC**,
**no** un triangulo ASCII ni U+25B6 (`▶`). El test debe comparar contra el code
point explicito, no contra un glifo escrito a mano en el propio test: si el test
comparase "el mismo caracter que escribio el dev", la mutacion pasaria porFilters.
`⭐` (U+2B50) y `☆` (U+2606) de `pack_manager_view.py:185` se comprueban igual.

## M5 — Validadores y guardas (regla de `agent.md:54`)

| Objetivo | Prueba |
|---|---|
| Guard `ast` de `get_favorite_pack` ausente en `src/` | **Borrar** el guard entero: debe fallar. Si el guard no se puede hacer fallar, no verifica nada |
| Guard `ast` del boton (`command` -> `_force_update_db`) | **Borrar** el boton: debe fallar |
| Check 7 de `validate_docs.py` (recuento de tests) | Cambiar el recuento en **uno solo** de los 4 ficheros: debe fallar |
| Test de "no queda ninguna `set_favorite` de 1 argumento" | Dejar una llamada de 1 argumento: debe fallar |

## M6 — Documentacion (regla de `agent.md:55`)

Comprobar contra el codigo, no contra el texto:
- `docs/ai/architecture.md:37` afirma que la DB *"se actualiza de forma asincrona desde
  el repositorio oficial en GitLab"*. **Hoy es falso**: el repo no existe. Si tras T-18
  el documento vuelve a afirmar que la descarga funciona, es un hallazgo.
- `openspec/changes/2026-09-29-v3-ux-polish/tasks.md:6` esta marcado `[x]` "Endpoint
  remoto actualizado a GitLab" — se marco hecho algo que nunca funciono. No reescribir
  un cambio **archivado**; annotate el estado real en el changelog del ciclo.

---

## Criterio de cierre

- [ ] Cada mutacion M1-M5 ejecutada, con veredicto literal `killed` / `survived` y el **motivo real** del fallo (no `ImportError`, no error de sintaxis).
- [ ] `__pycache__` purgado entre mutaciones (`agent.md:73`).
- [ ] Copia de `%TEMP%` restaurada y en verde; repo del arbol **sin tocar**.
- [ ] `VERDICT: PASS | FAIL | PARTIAL` explicito.

**Supervivientes de este ciclo que NO se aceptan:** cualquier `survived` en
acumulacion de favoritos, en el fallback de la DB, o en el existence check del boton.
