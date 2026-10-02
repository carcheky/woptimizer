# Propuesta OpenSpec: Favoritos Multiples en Portada y Boton de Descarga de DB

- **Change ID**: `2026-10-01-multi-favorites-and-db-download`
- **Area**: UI/UX + Base de Datos (encargos directos del propietario)
- **Agente responsable**: `openspec-dev`
- **Estado**: Propuesto
- **Ciclo**: #37 (arranca sobre `TASK-047` ya registrada; esta propuesta es independiente)

---

## 1. Encargos del propietario (verbatim)

1. *"el boton de favoritos debe dejarme anadir tantos favoritos comoquiera, no hacer toggle, todos los favoritos saldrán en portada, adaptandose a el espacio de la ventana"*
2. *"no veo el boton de descargar base de datos aun"* + pide recomendacion GitHub o GitLab.
3. *"en el boton de seleccionar pack de la ventana de todos los procesos veo dos flechas hacia abajo, basta con una sola."*
4. (derivado) Que el boton de descarga exista de verdad y sea funcional.

---

## 2. Hallazgos verificados contra el codigo (2026-10-01)

Todo lo de esta seccion se **volvio a comprobar leyendo el codigo**, no la descripcion del encargo.

| # | Hecho | Evidencia |
|---|---|---|
| H1 | Los favoritos son **exclusivos por politica de servicio**, no por esquema: `is_favorite` es un `bool` por pack y ya admite multiples | `services/pack_service.py:668-672`, `models.py:52` |
| H2 | La UI llama a un toggle que **desmarca el global** al desmarcar uno | `ui/views/pack_manager_view.py:393-402` |
| H3 | La portada usa un grid **fijo de 2 columnas**, independiente del ancho | `ui/views/dashboard_view.py:319-327` |
| H4 | `_force_update_db()` **no tiene ningun llamador** en todo el repo: el boton nunca se conecto — **CIERTA el 2026-10-01 y FALSA hoy**: `TASK-051` («Boton de Actualizar DB Funcional y Honesto», cuya descripcion decia literalmente «el boton no existe») fue la que lo conecto | el boton **si** lo invoca: `ui/views/process_manager_view.py:136` (`command=self._force_update_db`), definicion en `:183`. El «sin llamador» que la frase afirmaba es de **otra** funcion y vive en `.taskmaster/CHANGELOG.md:1714` (`GamingService.should_kill_for_gaming()`) |
| H5 | La URL esta **hardcodeada en medio del metodo** y apunta a GitLab | `services/process_service.py:376` |
| H6 | **El repo remoto no existe.** `api.github.com/users/carcheky` -> **200** (la cuenta existe); `raw.githubusercontent.com/carcheky/woptimizer/main/assets/process_db.json` -> **404** | verificado en esta sesion |
| H7 | La flecha duplicada es el glifo `"▼"` dentro del placeholder de un `CTkOptionMenu`, que ya dibuja su propio indicador | `ui/views/process_manager_view.py:107, 111, 196, 197` |
| H8 | `get_favorite_pack()` **no tiene ningun llamador en `src/`** y su semántica ("el primero que sea favorito") queda **incorrecta** con multiples | `services/pack_service.py:644-648` |

### 2.1 Tres premisas del briefing que resultaron FALSAS

> La leccion de los ciclos 14 y 15 se repite: un plan conforme vale menos que un plan que senala donde le mentieron a la tarea.

**FP-1 — "el bucle `btn.destroy()` no destruye nada porque `_forget_buttons()` ya vacio el dict". FALSO.**
`Confirmable._forget_buttons()` (`ui/confirmation.py:184-187`) solo hace `cancel_on_destroy()` + `self._reposo.clear()`. **Nunca toca `_buttons_by_pack_id`.** Los bucles de `dashboard_view.py:294-295` y `315-316` destruyen de verdad. No hay widgets zombis hoy, y la tarea NO debe "arreglar" eso.
→ Lo que si es real y si se liquida: ese bloque esta **duplicado literalmente** en las dos ramas (292-296 y 313-317), y es codigo que hay que tocar dos veces para el grid adaptativo.

**FP-2 — "el mensaje se queda en 'Descargando...' para siempre". IMPRECISO, y el defecto real es peor.**
Con el boton cableado, `_render_list` (`process_manager_view.py:227-231`) sobrescribe el `status_label` con `"N apps distintas en ejecucion."`. O sea: **un fallo y un exito producen exactamente la misma pantalla**. `load_db_async` traga la excepcion (`process_service.py:392-393`) y aun asi recarga y llama al callback (396-402). No es un colgado: es un **fallo silencioso que afirma que funciono**. El diseno de abajo ataca esto, no un spinner.

**FP-3 — el pack Gaming nace favorito, y "limpiar todos" lo deja muerto. NO estaba en el briefing.**
`DEFAULT_GAMING_PACK` nace `is_favorite=True` (`pack_service.py:234`). `_ensure_gaming_pack()` (`pack_service.py:581-590`) **solo lo recrea si falta**; si ya existe solo reafirma `is_gaming = True` y **no restaura `is_favorite`**. Consecuencia: el `set_favorite(None)` actual —al que se llega pulsando la estrella del propio pack Gaming— **borra la tarjeta Gaming de la portada de forma permanente**. Es un bug preexistente, y el paso a acumulativos lo hace más fácil de pulsar.

---

## 3. Decisiones de diseno

### D1 — Favoritos: modelo ACUMULATIVO, una estrella por pack (no "solo anadir")

Se interpreta el encargo asi: **cada pack se marca y se desmarca de forma independiente y acumulativa**. Marcar uno no desmarca los demas.

*Por que no "solo anadir":* si la estrella no pudiera desmarcar, **un favorito añadido no se podría quitar nunca** desde la UI, y la unica salida seria editar `profiles.json` a mano. Es un producto sin reversibilidad.

**DECISION ABIERTA (no bloqueante, el owner ya puede responder):** si lo que queria era "que no se pueda quitar", se cambia el paso (2) de `toggle_favorite` y se documenta la perdida de reversibilidad. La implementacion que se entrega es la acumulativa, que es la unica que permite desmarcar.

### D2 — API del servicio (la UI no decide politica)

`is_favorite` no cambia de tipo. Cambia el contrato del metodo:

```python
def set_favorite(self, pack_id: str, value: bool) -> None:
    """Marca/desmarca UN pack. No toca el resto. pack_id None -> ValueError."""

def toggle_favorite(self, pack_id: str) -> bool:
    """Lee el estado VIVO, lo invierte, persiste y devuelve el nuevo valor."""
```

`toggle_favorite` se resuelve **en el servicio** para respetar el invariante de capas: la UI no decide que hacer, pide el cambio. Se conserva la lectura en vivo (no la instantánea del render) que ya exige el test `test_toggle_favorite_desmarca`.

*Colateral obligatorio:* **`get_favorite_pack()` (H8) se borra o pasa a `get_favorite_packs() -> List[Pack]`.** Sin llamadores, y con multi-favoritos devuelve una respuesta falsa. Dejarlo vivo es dejar una trampa.

### D3 — Portada: columnas calculadas del ancho, y `columnspan` NO hardcodeado

- `cols = max(1, min(ANCHO_MIN_CARD * n, ancho_disponible // ANCHO_MIN_CARD))`, con `ANCHO_MIN_CARD` en `ui/theme.py` (tokens centralizados, ciclo #22).
- `grid_columnconfigure(i, weight=1, uniform="fav")` para repartir; **hay que poner a 0 el peso de las columnas que sobran** al reducir, si no las columnas fantasma siguen robando ancho.
- `_empty_label` pasa a `columnspan=cols` calculado (hoy `columnspan=2` hardcodeado, `dashboard_view.py:305`).
- **Re-grid al redimensionar:** la rama `else` de `dashboard_view.py:328-335` **solo reconfigura texto, nunca recoloca**. Sin un `<Configure>` que re-emaillere, "adaptarse al espacio de la ventana" no se cumple: al ensanchar la ventana los botones se quedan en la rejilla vieja. Es el nucleo del encargo, no un extra.
- El bloque de destruccion duplicado (FP-1) se **extrae a un metodo** `_destroy_favorite_buttons()` y se llama desde las dos ramas.

### D4 — Descarga de DB: GitHub, con fallo OBSERVABLE (esto es lo que arregla codigo)

Decision ya tomada por el orquestador (**GitHub**), revalidada: la cuenta `carcheky` existe en GitHub y el repo no; GitLab devolvio 404 de proyecto. Razon tecnica: `raw.githubusercontent.com` es URL estable y sin friccion, y permite colgar el `.exe` en Releases.

1. `DB_REMOTE_URL` como **constante de modulo** en `services/process_service.py` (hoy hardcodeada en la linea 376). Cambiar a GitLab = cambiar UNA constante.
2. **`on_error` explicito.** `load_db_async(callback=None, on_error=None)`. El `except` deja de ser un `logger.warning` y avisa a la UI con un mensaje honesto. Firma retrocompatible: `refresh_processes` (`process_manager_view.py:162`) ya la llama con `callback=` y no se toca.
3. **Fallback:** si la descarga falla, la app sigue con el `assets/process_db.json` local empaquetado. El mensaje de UI lo dice: `"DB no actualizada (sin red o repo no publicado). Se usa la local."` — no "todo correcto".
4. El boton se cablea en el footer con `_force_update_db` (H4) — el metodo ya existe y es correcto; lo que faltaba era el `command=`.

### D5 — Fallback UI del boton

Si la descarga falla, `status_label` dice explicitamente que fallo **y en que modo sigue**. Se sigue el precedente de `mensaje_danado()` (`pack_service.py:604-609`, Trampa #14 "nada se traga en silencio"), que ya existe en `PackService` y es el patron de la casa: el dato observable lo produce el **servicio**, no la vista.

### D6 — Una sola flecha: se quita el glifo, no se pelea con la nativa

`CTkOptionMenu` dibuja su propio indicador. El glifo `"▼"` del placeholder es la segunda flecha. Se extrae el literal a **una constante de modulo** (`PLACEHOLDER_PACK = "Seleccionar Pack"`, sin glifo) usada por las 4 apariciones (107, 111, 196, 197). Si tras el cambio el color del indicador no casa con el del placeholder, la correccion sigue siendo **quitar el glifo**, no tocar el widget nativo.

---

## 4. QUE ARREGLA EL CODIGO / QUE NECESITA A UNA PERSONA

Esta es la separacion que el encargo 4 exige, y es la parte que no se puede cerrar con un commit.

### Arregla el codigo (esta propuesta)
- Favoritos acumulativos + estrella por pack.
- Grid adaptativo con re-flow al redimensionar.
- Constante de URL apuntando a GitHub.
- Fallo de descarga **observable** en la UI, con fallback a la DB local.
- Boton "Actualizar DB" cableado y funcional.
- Placeholder del desplegable sin doble flecha.
- Tests discriminantes + recuento de tests al dia en los 4 ficheros que lo declaran.

### Requiere a una persona (NO lo arregla ningun commit)
1. **Crear/pushar el repo `carcheky/woptimizer` en GitHub** (H6). Sin esto la descarga **seguira fallando** y el boton dira "fallo" correctamente, que es el mejor comportamiento posible, pero no descargara nada.
2. **Publicar `assets/process_db.json` en la rama `main`** de ese repo. Si el repo nace sin ese fichero, el 404 persiste aunque el repo exista.
3. Opcional: decidir si el `.exe` va en **Releases** (mismo repo, sin trabajo extra).

> **El contrato es explicito:** hasta que (1) y (2) ocurran, el resultado esperado del boton es **"⚠️ no se pudo actualizar; se usa la DB local"**. Si un test exige que la descarga funcione contra la red, **esta proposition lo veta**: seria un test que depende de una accion humana no realizada, y daria verde un dia y rojo otro sin que cambie el codigo.

---

## 5. Invariantes que este cambio NO puede romper

- **Separacion de capas:** la UI no lee JSON ni hace red. Toda la descarga sigue en `services/process_service.py`; el boton solo llama a `_force_update_db`.
- **Anti-brick:** `load_db_async` **sanea al cargar** (`SYSTEM_PROTECTED_PROCESSES`). El fallback a la DB local mantiene esa garantia; no se toca `_get_process_meta` ni `kill_processes`.
- **Doble pulsacion:** este cambio **no toca ninguna accion destructiva**. La estrella NO es destructiva (es reversible con un segundo clic) y por tanto **no** lleva `DoubleTapGuard`. Anotado para que nadie lo "añada por simetría".
- **Emojis:** la estrella es `⭐` (U+2B50) lleno y `☆` (U+2606) vacio, **caracter a caracter** (`pack_manager_view.py:185`). Nada de `?` ASCII.

---

## 6. Tests que hay que actualizar (verificados, no supuestos)

El recuento actual es **91** (`ast` sobre `run_tests.py`); lo vigila el check 7 de `validate_docs.py`, que lo compara con `STATUS.md`, `AGENTS.md`, `README.md` y `docs/ai/testing-guide.md`. **Anadir tests obliga a los cuatro** o el validador falla.

| Test | Lineas | Que rompe | Que hay que hacer |
|---|---|---|---|
| `test_pack_service_favorite_exclusive` | `run_tests.py:989-1012` | Las 3 aserciones son de **exclusividad**: `:1001` espera `["a"]`, `:1005` espera `["c"]` tras marcar `c`, `:1008-1009` espera `[]` con `None` | **Reescribir** como `test_pack_service_favorites_accumulan`: marcar `a` y `c` -> `["a","c"]`; desmarcar `a` -> `["c"]`. Actualizar el **registro del runner en `:10998`** |
| `test_toggle_favorite_desmarca` | `run_tests.py:5734-5832` | El `_Grabador` (`:5777-5779`) colapsa el estado a un unico favorito (`{k: (k == pack_id)}`) y registra `set_favorite(None)`. Los casos (2) `:5801-5805` y (4) `:5812-5816` asertan `llamadas == [None]` y `{"a": False, "b": False}` — con acumulativos el caso (4) debe dejar **`{"a": True, "b": False}`** | **Reescribir** el grabador a la nueva firma. **CONSERVAR** las 3 propiedades valiosas: lectura en vivo (mata el atajo `get_favorite_pack()`), id inexistente no toca el servicio (caso 3), y la marca de un no-favorito (caso 1). Actualizar el **registro del runner en `:11053`** |
| Semillas en otros tests | `:3518`, `:3651`, `:3717` | Llaman `set_favorite("x")` con **un solo argumento**: con la firma nueva es `TypeError` y tumba la suite entera | Anadir el 2o argumento `, True`. Son 3 lineas, pero si se olvidan **no hay un test rojo: hay una suite muerta** |
| Modelo / JSON | `:3317-3318`, `:7910-7961`, `:10389` | Usan `is_favorite` como bool o como clave de schema | **No se tocan**: el tipo no cambia. Verificar que siguen verdes |

> Nota de riesgo: las 3 semillas de `:3518/:3651/:3717` estan en tests de `.bak` y recuperacion. Un `TypeError` ahi no falla "el test de favoritos", falla el de backup, y el mensaje senala el archivo equivocado. Es la clase de fallo que este repo ya ha pagado dos veces.

---

## 7. Lo que este cambio NO hace

- No arregla la descarga sin publicacion humana (ver §4).
- No toca `_ensure_gaming_pack` mas alla de **restaurar `is_favorite=True` del pack Gaming** si se desmarca (FP-3) — decision minima para que la tarjeta Gaming no se pierda.
- No regenera `dist/woptimizer.exe` (imposible aqui: `force_build.py` necesita `subprocess` → `spawn EPERM`). El ejecutable publicado seguira sin estos fixes hasta que se regenere.

---

## 8. Decision revisable

Plataforma **GitHub** esta tomada y revalidada. Si el owner publica en GitLab en su lugar, el cambio es **una constante** (`DB_REMOTE_URL`); nada mas del plan depende de la eleccion, y el paso de pruebas de red queda vetado en ambos casos por la misma razon.
