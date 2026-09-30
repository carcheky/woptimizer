# Tasks — `2026-09-30-validate-pack-leaves` (TASK-031)

> Cada criterio nombra **la mutación exacta que debe morir**. Un criterio sin mutación es una opinión.
> Las sondas L1–L7 son las de `proposal.md` §5. Orden de ejecución obligatorio: **§0 primero, §1 después**.
> Motivo: E-1 y E-2 sin los tests que las vigilan pasan en verde y no arreglan nada.

## §0 — Tests primero (todos fallan hoy salvo donde se indica)

- [x] **T-01 · L1 `test_la_rotacion_usa_la_misma_puerta_que_load`**
  Principal **válido como JSON pero ilegible para el servicio** (`{"packs":{"mio":{"id":"mio","name":7}}}`)
  + `.bak` sano con un pack `salvado`. Tras `PackService()`:
  - `PackService._read_json(None, ruta + ".bak")` **no lanza** y devuelve un pack `salvado`.
  - **MATA `L-M1`**: `_rotate_backup()` vuelve a `json.load` (o a `pass`).
  - **Por qué discrimina**: hoy la única guarda de rotación es `json.load` (`pack_service.py:206-207`), así
    que el `.bak` acaba siendo el principal corrupto y la aserción falla con `ValidationError` **dentro de
    la comprobación**, no con una excepción del test. Sin el `try` explícito, el test seguiría verde.

- [x] **T-02 · L2 `test_la_hoja_malformada_se_clasifica`**
  Tabla de **6 hojas** × **2 ramas**: `keepers` str, `target_categories` dict, `apps` int, `name` int,
  `is_favorite` "si", `default_action` "PURGAR". Para cada fila: se clasifica como corrupción
  (`PerfilCorruptoError` en legacy, `ValidationError` en moderna), con `.bak` sano recupera `salvado`, y
  **el mensaje contiene el nombre del campo, el id del pack y el tipo real**.
  - **MATA `L-M2`**: volver a la construcción a mano `Pack(id=k, name=v.get("label"), apps=…, is_favorite=…,
    is_gaming=False, default_action="start")` en la rama legacy; o quitar `traducido["id"] = k`.
  - **Por qué discrimina**: hoy la fila legacy devuelve `OK` y el pack carga con `keepers == []`. La
    aserción del **texto del mensaje** es la que impide que E-2 se "cumpla" dejando que Pydantic hable
    con su diagnóstico de 14 líneas: quien repara el fichero es el usuario.

- [x] **T-03 · L3 `test_load_no_escribe`**
  Con cualquier principal, tras `PackService()`: los bytes del `.bak` son idénticos a los previos y
  `save()` **no se invoca desde `load()`** (doble que cuenta invocaciones, comprobado por el estado
  observable del `.bak`, nunca por un umbral arbitrario).
  - **MATA `L-M3`**: `_ensure_gaming_pack()` vuelve a llamar a `save()`; o `load()` recupera su
    `self.save()` de `load():109`.
  - **Por qué discrimina**: es la **única** sonda que ata E-1 y E-3. Con solo E-1+E-2, el `.bak` se
    seguiría destruyendo, un poco más tarde. Medido: hoy `save()=1` y `_rotate_backup()=1` dentro de
    `load()`.

- [x] **T-04 · L4 `test_la_recuperacion_no_sobrescribe_el_bak`**
  Tras recuperar del `.bak`: los bytes del `.bak` son **byte a byte** los originales y el `.bak` **no**
  contiene la versión recuperada.
  - **MATA `L-M4`**: en la ruta de recuperación, un `save()` antes de leer el `.bak`; o rotar "para dejar
    el backup al día".
  - **Por qué discrimina**: sin comparación de **bytes**, "no sobrescribir" y "sobrescribir con lo mismo"
    son indistinguibles, y L4 no mataría a L-M4.

- [x] **T-05 · L5 `test_sin_bak_legible_no_se_sobrescribe_el_principal`**
  Principal corrupto **sin** `.bak`: los bytes del principal **no cambian**, la app **arranca** y el
  pack `mio` queda **marcado como dañado** (no desaparece en silencio).
  - **MATA `L-M5`**: reponer `AppData()` + `_ensure_gaming_pack()` + `save()` en `load():106-109`.
  - **Por qué discrimina**: hoy el fichero del usuario se reescribe con un solo pack. La aserción que
    muere es "los bytes del principal son los de antes", que no depende de cuántas veces se escriba.

- [x] **T-06 · L6 `test_un_campo_desconocido_no_es_corrupcion_y_no_se_borra`** *(decisión §3.2)*
  `{"packs":{"mio":{…,"notas":"comprar la caja"}}}`: arranca **sin** recuperar del `.bak`, y tras un
  `save()` el campo `notas` **sigue en el fichero**.
  - **MATA `L-M6`**: `extra="forbid"`, o la whitelist de `isinstance` de la opción (a) del encargo.
  - **Por qué discrimina**: **es la sonda que separa la opción (a) de la opción (b)**. Sin ella, "más
    isinstance" y "validar contra el modelo" producen el mismo comportamiento y el mutation-auditor no
    puede decir cuál se ha implementado. Y fija que un `.bak` de un build más nuevo no es corrupción.

- [x] **T-07 · L7 `test_packs_y_profiles_a_la_vez_es_corrupcion`** *(decisión §3.3)*
  `{"packs":{"mio":{…}},"profiles":{"otro":{…}}}`: se clasifica como corrupción **nombrando las dos
  claves**; con `.bak` sano no se pierde `salvado` ni `otro`.
  - **MATA `L-M7`**: quitar `'packs' not in raw_data` de la condición de `pack_service.py:133`.
  - **Por qué discrimina**: hoy la rama moderna ignora `profiles` como clave extra y **el pack `otro`
    desaparece del disco en el primer `save()` sin clasificar nada**. La aserción que muere es "el pack
    `otro` sigue ahí después del `save()`".

## §1 — Cambios de producción (en este orden)

- [x] **T-08 · E-1 — `_rotate_backup()` valida con la misma puerta que `load()`**
  Añadir `_es_legible(self, path) -> bool` (`try: self._read_json(path) → True` / `except
  CORRUPTION_ERRORS: False`) y usarla en `_rotate_backup()` **en lugar de** `json.load` (`pack_service.py:206-207`).
  Actualizar el docstring de `_rotate_backup()` para que la promesa de `pack_service.py:200-201` sea la que
  se cumple. **MATA `L-M1`.** No hacer nada más en este paso.

- [x] **T-09 · E-2 — la rama legacy deja de saltarse el modelo**
  Traducir cada registro legacy a un `dict` moderno y construir el `Pack` desde él
  (`proposal.md` §2, E-2), en vez del `Pack(...)` literal de cinco campos de `pack_service.py:161-169`.
  El único renombrado es `label → name`; `apps`, `keepers`, `target_categories` e `is_favorite` **se pasan
  en vez de descartarse**. `ValidationError` ya está en `CORRUPTION_ERRORS`: **no se crea ninguna clase de
  error ni ninguna rama nueva**. La rama `__system_gaming__` se deja como está. **MATA `L-M2`.**
  - [x] T-09.1 · Si el mensaje de `ValidationError` no nombra campo + pack + tipo, envolverlo para que lo
    haga. **Es bloqueante**: es el contrato de `proposal.md` §3, condición 1.

- [x] **T-10 · E-3 — `load()` deja de escribir**
  Quitar el `self.save()` de `load():109` y el `save()` de `_ensure_gaming_pack()` (`pack_service.py:245`);
  el pack `gaming` se asegura **en memoria** y se persiste en el primer `save()` real. **MATA `L-M3`,
  `L-M5`.**
  - [x] T-10.1 · Verificar antes que `PROFILES_FILE` no tiene más consumidores que
    `PackService.__init__` (hoy: uno solo, `config.py:26` → `pack_service.py:55`) y que
    `get_gaming_pack()` (`pack_service.py:258`) cae a `DEFAULT_GAMING_PACK` sin fichero. **Si aparece un
    consumidor nuevo, PARAR y volver al orquestador.**
  - [x] T-10.2 · Exponer la recuperación de forma observable (`pack_dañados` / `recuperado_de_backup`) para
    que la UI pueda mostrarla en el `status_label` (Trampa #14: *"nada se traga en silencio"*). **MATA
    `L-M5`** en su segunda mitad. Bloqueante para el criterio de UX, no para los tests de datos.
  - [x] T-10.3 · No eliminar `AppData()` como valor inicial: se sigue usando, solo deja de **escribirse**.

- [x] **T-11 · E-4 — política de campos desconocidos**
  `model_config = ConfigDict(extra="allow")` en `Pack` y en `AppData` (`src/woptimizer/models.py`), para que
  un campo que esta versión no conoce sobreviva al ciclo carga→guarda. **MATA `L-M6`.**
  **No bloqueante el `extra="allow"` en sí**: si destabiliza otra cosa, se deja el `extra` por defecto y se
  documenta como deuda. Lo que **sí** es bloqueante es que **L6 quede en verde** con una de las dos
  salidas y la elegida esté anotada en `data-models.md`.

- [x] **T-12 · Documentación viva**
  - [x] `docs/ai/data-models.md`: añadir el criterio de `proposal.md` §3.1 como contrato; registrar las
    dos decisiones de §3.2/§3.3; **corregir `data-models.md:53-55`**, que hoy afirma *"si el principal está
    corrupto NO se rota"* y es **falsa** hasta que T-08 esté dentro; actualizar la tabla de
    `data-models.md:78-87` con las filas nuevas; borrar la deuda de la doble escritura de
    `data-models.md:128-133` (T-10 la elimina).
  - [x] `docs/ai/testing-guide.md`: las sondas L1–L7 y **por qué existe cada una**.
  - [x] Actualizar la lista de campos de `data-models.md:17-25` si `models.py` cambia (T-11).

## §2 — Cierre

- [x] **T-13** `python run_tests.py` en verde: **36 → 43**, con L1–L7 registradas en el `__main__`.
- [x] **T-14** `python verify_ui_syntax.py` y `python validate_docs.py` en verde.
- [x] **T-15** **Reejecutar la matriz de `proposal.md` §0.1 con los tests finales**: las 7 mutaciones
  `L-M1`…`L-M7` deben morir, y la columna *".bak sano tras `load()`"* debe quedar en `INTACTO` en **los 8**
  escenarios. **Sin este reejecutado el ciclo no se cierra**: L1 por sí solo no cubre la fila legacy.
- [ ] **T-16** `validate_docs.py` con entrada de CYCLE-019 en `CHANGELOG.md` (raíz) y
  `.taskmaster/CHANGELOG.md` (registro técnico), con la tabla de mutaciones.
- [ ] **T-17** `python .taskmaster/git_safe_commit.py "<mensaje>"` y comprobar el código de salida
  (`0` = commit o no-op, `1` = fallo). **Nunca `git` a pelo.**

## §3 — Iteración 2 (el mutation-auditor dio FAIL: `L-M6c` sobrevivía)

Hallazgo del auditor, medido: `extra="ignore"` **solo en `AppData`** sobrevivía a las 7 sondas.
Con ella, un `profiles.json` con la **raíz mal escrita** arranca, ve cero packs y en el primer
`save()` deja el fichero como `{"packs": …}`: **los packs del usuario desaparecen del disco**.
La línea `extra="allow"` de `AppData` era PORTANTE y no tenía ni una sonda.

> ### Corrección NORMATIVA de `proposal.md` §3.2 (y de T-11)
>
> `proposal.md` §3.2 afirma que el `extra="allow"` es **«no bloqueante»** y que, si
> «el mutation-auditor lo ve desestabilizar otra cosa, se documenta como deuda». **Eso es
> FALSO y esta iteración lo ha medido**: el `extra="allow"` de `AppData` **es** la línea que
> impide la pérdida de datos de `L-M6c`. No es solo "compatibilidad hacia delante": es
> conservación. Y `proposal.md` §3.2 tampoco dice quién vigila el `extra="allow"` de la
> **raíz** (su `L6` solo mira `packs.mio.notas`, una hoja).
>
> **Lo que este documento fija por encima de la redacción de `proposal.md` §3.2** (que es
> del arquitecto y que esta iteración **no** ha editado):
>
> 1. El `extra="allow"` de `AppData` **es bloqueante** y lo vigila `L8`.
> 2. Una **raíz** mal escrita **NO es corrupción** (§4), y el motivo es medido: clasificarla
>    hace `self._data = AppData()` en la ruta sin `.bak` y el siguiente `save()` publica
>    `{"packs": {"gaming": …}}` — los packs se pierden **igual**, con un aviso de encima.
>    Sobreviven al guardado gracias al `extra="allow"`. Sonda: `L8`.
> 3. El **coste** de esa decisión (arranque con cero packs y sin aviso) queda **declarado**
>    en `data-models.md` §4.3 y **fijado** por `L8` (`fichero_danado is False`).
>
> El arquitecto sigue siendo dueño de `proposal.md`: si quiere reescribir §3.2, esta es la
> redacción que la evidencia sostiene.

- [x] **T-18 · L8 `test_la_raiz_mal_escrita_no_destruye_los_packs`**
  Raíces mal escritas (`perfiles`, `packs2`, `paquets`, `Packs`) × (con y sin `.bak`): al
  arrancar los bytes del principal son los de antes, `recuperado_de_backup is False`, y tras un
  `save()` **real** la raíz sigue en el fichero con los packs del usuario **byte a byte**.
  **MATA `L-M6c`** (`extra="ignore"` en `AppData`) y **`L-M8a`** (clasificar la raíz mal
  escrita como corrupción).

- [x] **T-19 · L9 `test_un_error_de_escritura_no_es_un_campo_desconocido`**
  7 campos a una pulsación de una clave conocida × **2 ramas**: `PerfilCorruptoError` que nombra
  el campo mal escrito, la clave que queda sin leer y el pack; al recuperar del `.bak` los
  `keepers` **reales** vuelven. Y 10 campos extra **legítimos** que se tienen que quedar en paz.
  **MATA `L-M8b`** (quitar la colisión) y **`L-M8f`** (umbral 1 → 2).

- [x] **T-20 · L10 `test_la_clave_del_mapa_es_la_identidad_del_pack`**
  `id != clave` es corrupción en las 2 ramas sin tocar un byte; en un fichero bien escrito cada
  pack se encuentra por su `id` (la expresión literal de `pack_manager_view.py:100`) y un
  registro legacy sin `id` hereda la identidad de la clave. **MATA `L-M8c`** y **`L-M2b`**.

- [x] **T-21 · `is_gaming` (y `is_favorite`) con `strict=True`**
  Medido: Pydantic coaccionaba `"true"` a `True`, el pack desaparecía de `get_user_packs()` y
  `delete_pack` decía «No se puede eliminar el pack de sistema»: invisible e indeletable. Con
  `strict=True` es corrupción, recuperable del `.bak`, con el mensaje nombrando el campo.
  **MATA `L-M8d`**, ejercida por la fila `is_gaming: "true"` de `L2` (solo rama moderna: en la
  legacy `is_gaming` se fuerza a `False`).

- [x] **T-22 · `L2` deja de mentir sobre `L-M2b`**
  La fixture legacy **quita `id`** (como un registro legacy de verdad): antes la línea
  `traducido["id"] = k` era **código muerto** y su mutación-sobreviviente era invisible.
  `testing-guide.md` afirmaba lo contrario; corregido.

- [x] **T-23 · Fixture de `P5` corregida**
  La fila `ValidationError` traía `{"x": {"id": "a", …}}`: clave `x` con id `a`. Con la guarda de
  identidad (T-20) esa fila dejó de producir la clase que declaraba (lo cazó la propia sonda) y
  probaba otra cosa. Ahora `"id": "x"` y la fila vuelve a medir lo que dice medir.

- [x] **T-24 · Documentación: afirmaciones falsas corregidas**
  - `data-models.md`: `default_action` era `str = "kill"` (el código es
    `Literal["start","kill"] = "start"`), y los valores del pack `gaming` listados
    (`keepers: ["discord"]`, `apps: []`) no existían (son `["steam.exe", "discord.exe"]` y
    `["chrome.exe"]`).
  - `testing-guide.md`: la fila `L2` afirmaba matar `L-M2b` y no la mataba (§ T-22).
  - `data-models.md` §4.5 (nuevo): las dos reglas del servicio y por qué no son un filtro fuzzy.

- [x] **T-25 · Matriz de mutación de esta iteración: 13/13 mueren**
  `L-M6c`, `L-M8a`, `L-M8b`, `L-M8f`, `L-M8c`, `L-M2b`, `L-M8d` (nuevas) + `L-M1`, `L-M2`, `L-M3`,
  `L-M4`, `L-M5`, `L-M6`, `L-M7` (regresión: ninguna se ha debilitado con los cambios nuevos).
  Medida sobre una **copia** en `%TEMP%` con mutación textual de `src/`. Sin supervivientes.
- [x] **T-26 · `run_tests.py` en verde: 43 → 46** (L8, L9, L10 registradas en la `__main__`).

## §4 — Iteración 3 (el mutation-auditor dejó 3 supervivientes medianos)

Los 4 críticos del FAIL anterior están cerrados y **ningún camino destruye los packs del
usuario**; lo que queda son tres cosas que no son pérdida de datos sino **pruebas que no
pueden morir** y **una afirmación documental falsa**. Ninguna de las tres exige rediseñar
nada: son un hueco de código de una línea, dos filas de sonda y una frase de documentación.

> ### Corrección NORMATIVA de `proposal.md` §3.2, segunda vuelta (y aviso al arquitecto)
>
> `proposal.md:222-226` sigue diciendo que el `extra="allow"` es **«No bloqueante**»: *«si el
> mutation-auditor lo ve desestabilizar otra cosa, se documenta como deuda y se deja el
> `extra="allow"` para su propia tarea. Pero el test que lo fija (T6) **sí** es bloqueante,
> porque fija la decisión»*. **La segunda frase es la única defendible y este ciclo la ha
> falsificado por partida doble, con medición:**
>
> 1. **El `extra="allow"` es bloqueante en los DOS sitios, y no solo por "compatibilidad hacia
>    delante".** En `AppData` es lo único que impide que una raíz mal escrita borre los packs
>    en el primer `save()` (`L8`, mutación `L-M6c`), y en `Pack` es lo único que impide que
>    un campo desconocido de una hoja se borre (`L6`, `L9`). Ninguna de las dos cosas es
>    hipotética: las dos son borrado silencioso de datos del usuario.
> 2. **Y hay un agujero que el propio enunciado de §3.2 no contempla: un `extra="allow"` que
>    no se copia al objeto no conserva NADA** (mutación `M8`, medida en esta iteración). La
>    rama legacy construía el `AppData` desde cero (`AppData(packs=packs_dict)`) y se llevaba
>    por detrás **toda** la raíz que no fuese `packs`/`profiles`; un `profiles.json` legacy
>    real (que trae `favorite` en la raíz) perdía ese `favorite` en el primer `save()`, en
>    silencio. El `extra="allow"` estaba puesto y **no hacía nada** en esa rama. Arreglado
>    copiando la raíz entera menos `profiles` al `AppData` que se construye (`L11`).
> 3. **Lo que la redacción de §3.2 tampoco dice, y que ahora está decidido:** quién vigila
>    las claves de la **raíz**. No es `L6` (que solo mira `packs.mio.notas`, una hoja) ni
>    `L8` (que mira la supervivencia, no la clasificación). Es `L12`, y la respuesta es que
>    **la raíz NO se vigila**, por tres motivos medidos (§4.6 de `data-models.md`).
>
> **Redacción que la evidencia sostiene para §3.2** (el arquitecto sigue siendo dueño de
> `proposal.md`; esto es lo que se ha medido, no una reescritura): *el `extra="allow"` en
> `Pack` y en `AppData` es bloqueante y lo vigilan `L6`/`L9` y `L8`; además **no basta**: en
> cualquier rama que reconstruya el `AppData` hay que copiar la raíz entera, y la raíz no se
> clasifica nunca (`L11`, `L12`).*

- [x] **T-27 · L11 `test_la_raiz_legada_conserva_sus_claves_extra`**
  `{"profiles": {…}, "favorite": "mio", "version": 2, "escrito_por": {"build": 7}}`: arranca
  sin clasificar, el `.bak` sano no se toca, y tras un `save()` **real** las tres claves
  siguen en el fichero **con su valor**, los packs del usuario también, `profiles` **no**
  aparece y el fichero escrito **vuelve a arrancar limpio**.
  **MATA `M8`** (la raíz legacy se pierde) y **`M8b`** (conservar `profiles`).
  Control: una raíz legacy **sin** extras sigue funcionando, para que "funcione" no pueda
  significar "no carga nada".

- [x] **T-28 · L12 `test_una_clave_raiz_nunca_es_un_error_de_escritura`**
  5 claves raíz que se parecen a un campo de hoja a una pulsación (`names`, `ids`, `favorite`,
  `keeper`, `is_favorit`) junto a un `packs` válido, **más** 4 raíces sin clave válida
  (`{"names": …}`, `{"ids": …}`, `{"packs2": …}`, `{"profiless": …}`): ninguna se clasifica,
  ninguna toca el `.bak` sano y todas siguen en el fichero con su valor.
  **MATA `M9`** (el filtro de colisión aplicado a la raíz) y **`L-M8a`** en su segunda
  variante ("la raíz no tiene clave conocida ⇒ corrupción").

- [x] **T-29 · La fila `is_favorite: "si"` de `L2` era un test que no podía morir**
  Medido: Pydantic v2 en modo **laxo** rechaza `"si"` igual que en estricto, así que la fila
  quedaba verde **con y sin** `strict=True` y su mutación-sobreviviente era invisible. El
  `strict=True` estaba puesto y **nadie lo vigilaba**. Sustituida por `"true"` y `1`, que sí
  coaccionan a `True`. **MATA `M4b`.** `is_gaming` ya tenía su fila correcta (`"true"`).

- [x] **T-30 · `M13`: `_normalizar_clave` se queda y se ejerce**
  No se quita (eso sería **reducir** cobertura: la coincidencia exacta sobre la clave
  normalizada es lo único que coge `IS-FAVORITE`, a **11** de distancia en bruto, e
  `IS_GAMING`, a **2**), y se le añade la sonda que lo ejerce: dos filas más en `L9`.
  **MATA `M13`** (`_normalizar_clave` → identidad).

- [x] **T-31 · P5 documental: afirmaciones falsas corregidas**
  - `data-models.md`: `pack_service.py:70` y `:70-79` → `DEFAULT_GAMING_PACK`, líneas
    **231-240** (se cita el símbolo además de la línea para que la deriva no vuelva a
    producir una cita falsa).
  - `data-models.md`: la tabla de `CORRUPTION_ERRORS` listaba **2** causas de
    `PerfilCorruptoError` y el código lanza **5** `raise` más la traducción de
    `ValidationError`. Nueva §4.1.1 con los **seis** orígenes y su sonda.
  - `data-models.md` y el docstring de `_colision_de_tecla`: **«cero falsos positivos» era
    FALSO** (`names`→`name` e `ids`→`id`, a distancia 1). Medido y escrito con su
    consecuencia: la regla es de **hojas**, y §4.6 explica por qué.
  - `testing-guide.md`: filas de `L2` (8 hojas) y de `L9` (9 colisiones) rehechas, sondas
    `L11`/`L12` añadidas con su muerte y su porqué.

- [x] **T-32 · Matriz de mutación de esta iteración: 19 mutaciones / 21 pares, 0 supervivientes**
  **Un subproceso por (mutación, sonda)**: la suite aborta en el primer fallo y un test viejo
  tapa al nuevo. 13 de regresión (L-M1…L-M8f) + 5 nuevas (M4b, M13, M8, M8b, M9) + `L-M8a`
  por su segunda variante, cada una sobre una **copia** en `%TEMP%` con mutación textual.
  El único par que sobrevive es **informativo** y está documentado, no escondido: el filtro
  de colisión *de hoja* aplicado a la raíz no ve `perfiles`, así que esa variante la mata
  `L-M8a` (la otra implementación plausible), no `L8`. Tabla de las dos variantes en
  `data-models.md` §4.6.

- [x] **T-33 · `run_tests.py` en verde: 46 → 48** (L11 y L12 registradas en el `__main__`).

## Fuera de alcance (deliberadamente)
- `gaming_service.py`, la barrera de categoría G-1/G-2, `SYSTEM_PROTECTED_PROCESSES`, la doble pulsación
  (`ui/confirmation.py`): intocables. Esta tarea no toca la política de *qué* se mata, solo la de *cómo se
  lee un fichero*.
- La rama `__system_gaming__` de `_read_json`: es un preset fijo del producto, no dato del usuario.
- Ampliar `CORRUPTION_ERRORS`: ni una clase más. `AttributeError` y `OSError` siguen fuera **a
  propósito** (`proposal.md` 2026-09-30-close-mutation-survivors §3.3) y `L7`/`L8`-style "es corrupción
  porque lo digo" está prohibido.
- **Vigilar la raíz** (identidad o error de escritura): prohibido por §4.6 de `data-models.md`, y los
  dos motivos son pérdida de datos. No es "fuera de alcance por pereza": está medido, y `L12` es la
  sonda que lo impide.
- El aviso de "raíz mal escrita, arrancaste con cero packs": sería el arreglo del coste de §4.3, pero
  exige pintar en la UI, que está fuera de alcance desde TASK-030. Queda como deuda declarada.
