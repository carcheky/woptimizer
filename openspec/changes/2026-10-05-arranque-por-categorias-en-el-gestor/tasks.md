# Tasks — Arranque por categorias en el Gestor (`TASK-068`)

Toda cita `archivo:linea` de este documento es de `HEAD` = `ea4ce95` (rama `beta`) y se ha
medido antes de escribir la linea. Cero ediciones bajo `src/` en este documento: esto es
el plan, no la ejecucion.

---

## T-1 — El Gestor arranca SUS DOS listas y las SUMA (el guardian que falta)

**Que:** aserciones discriminantes sobre `PackManagerView.start_pack()` con un pack que
tiene `apps` **y** `start_categories`, por el camino real del Gestor (el `_correr` de
`run_tests.py:9592`, sin Tk).

**Por que discrimina (y por que este es el ladrillo del ciclo):** el doble de test ya
tiene los campos y nadie los lee — `llamadas_categorias` (`run_tests.py:9177`),
`arranque_categorias` (`:9178`), `categorias` (`:9175`) y `target_categories` (`:9193`)
tienen **2, 2, 2 y 1 ocurrencias en todo el fichero y las cuatro son definicion o
incremento**. Y el pack del test, `pack_normal = Pack(..., apps=list(APPS))`
(`run_tests.py:9659`), no tiene `start_categories`, luego el `if categorias:` de
`pack_manager_view.py:666` **nunca se toma** y la unica asercion de la puerta
(`run_tests.py:9889`) solo mira `llamadas_arranque` y `apps`.
**Medido: borrar `pack_manager_view.py:666-671` deja la suite de 183 en verde.** Ese
borrado es exactamente el bug que el encargo da por existente, luego el test tiene que
morir por el, y no por un `assert` de forma.

**Las cuatro filas, y que mutante mata cada una:**

| # | Asercion | Mutante que muere |
|---|---|---|
| 1 | `procs.llamadas_categorias == 1` | borrar `:666-671` (el bug del encargo) |
| 2 | `procs.categorias == [CATEG_INICIO]` | arrancar una lista distinta a la marcada |
| 3 | `procs.target_categories == pack.target_categories` | no pasar la lista de apagado, que es lo que pierde la resolucion del conflicto en el servicio (`process_service.py:908`) |
| 4 | el texto dice la **SUMA**: con `arranque=(2, 0)` y `arranque_categorias=(3, 1)` sale `"⚠️ 'Trabajo': 5 iniciadas, 1 con error."` | sumar mal, o sumar solo una de las dos |

**Contraprueba de la fila 4 (obligatoria, sin ella la fila 4 no discrimina):** con
`arranque_categorias=(0, 0)` el texto tiene que ser **exactamente** el de
`run_tests.py:9885` (`"🚀 3 apps iniciadas · 'Trabajo'."`). Sin esta segunda fila, un
`+0` metido donde no toca passaria por «la suma esta bien», que es el fallo espejo del
que este ciclo viene.

**El mutante del efecto contrario, exigido por el encargo (arrancar de mas).** Una puerta
de arranque arreglada por alguien que copie la de apagado puede arrancar lo que debe
apagar. La fila que lo mata es: `pack.target_categories = [OTRA]` y
`pack.start_categories = [CATEG_INICIO]`, y la asercion es
`procs.categorias == [CATEG_INICIO]` **y** `OTRA not in procs.categorias`. Si alguien
pasa `pack.target_categories` como primer argumento, la fila 2 se vuelve a escribir y
muere. Su gemela de servicio ya existe (`run_tests.py:15092`, conflicto gana `kill`) y no
se toca: lo nuevo es la fila **de vista**, que es donde el encargo situaba el fallo.

**Cierre:** las cuatro filas + la contraprueba verdes, y el `mutation-auditor` confirma
que borrar `pack_manager_view.py:666-671` **muere por la fila 1**, no por otra asercion
del fichero. Reutiliza el `_gestor`/`_correr` de `run_tests.py:9576-9600`; no escribir un
segundo arnes de vista.

---

## T-2 — Lo omitido CUENTA: la mejora que no ocurre se ve como tal, no como un verde

**Que:** las dos ramas `continue` peladas de `ProcessService.start_pack_categories`
(`process_service.py:918-923` la 🔴 y `:924-929` la del conflicto con
`target_categories`) pasan a sumar `failed` antes de continuar. Se hace segun **P-2** de
`proposal.md` §7: el suelo recomendado es (a) `failed += 1` sin cambiar la firma.

**Por que discrimina:** hoy una categoria omitida **no cuenta ni para bien ni para mal**,
o sea que devuelve `(0, 0)`, y `pack_manager_view.py:672-673` responde
`if failed == 0: → VERDE` con `🚀 0 apps iniciadas`. El test de este T tiene que exigir
que un pack con 0 apps y su unica categoria de arranque omitida **no** produzca un toast
`VERDE`. Hoy lo produce, luego el test **falla antes del fix** por la razon correcta: no
porque el formato cambie, sino porque **un rechazo se anuncia como un exito**.

**Las tres filas, con su discriminante:**

| # | Asercion | Por que discrimina |
|---|---|---|
| 1 | `svc.start_pack_categories([ROJA])` → `started == 0 and failed >= 1` | hoy `failed == 0`. El test de servicio que ya existe (`run_tests.py:15049`) mira **solo** `started == 0`, luego no lo distingue: hay que **ampliarlo**, no crear un test paralelo |
| 2 | por la puerta real del Gestor, el toast **no** es `VERDE` y no lleva `✅` | mata el mutante «arreglar el servicio pero no el mensaje», que es el que deja el verde |
| 3 | **control negativo:** una categoria **con** ejecutable resoluble devuelve `started == 1 and failed == 0` | ver nota |

> Nota de la fila 3: la contraprueba es que una categoria **con ejecutable resoluble**
> devuelve `started == 1 and failed == 0`. Sin ella, `failed += 1` metido en el `return`
> en vez de en la rama hace que *todo* falle y las filas 1 y 2 siguen verdes: es el
> mutante «cuenta de mas», y por eso la fila 3 es la que distingue **contar lo omitido**
> de **contar todo**.

**Lo que este T NO arregla:** el *motivo* de la omision. Ese es el destino de **P-2(b)**
(una 3-tupla), que cambia la firma y los tres dobles de test, y queda **condicionado a la
respuesta del dueno**. Con P-2(a) el usuario ve un numero y un ambar, que es el suelo
acordado; con P-2(b) ve ademas «🔴 es una categoria de riesgo».

**Cierre:** filas 1-3 verdes, la fila 1 **ampliando** `run_tests.py:15049` (no duplicando),
y el `mutation-auditor` confirma que volver `continue` pelado **muere por la fila 1**.

---

## T-3 — El recuento nombra lo que conto: ni «apps» donde hay categorias, ni verde donde no hay nada

**Que:** el toast del Gestor (`pack_manager_view.py:673`) dice
`f"🚀 {started} apps iniciadas · '{nombre}'."` con un `started` que ya **mezcla apps y
categorias** (`started += started_cats`, `:670`). Con 0 apps y 3 categorias de arranque el
texto miente en plural y en sustancia. Y con `started == 0 and failed == 0` no puede
existir un tick: hoy ese camino solo es alcanzable por el bug de T-2, y al cerrarlo T-2
debe quedar **inalcanzable**, no solo raro.

**Por que discrimina:** es la misma mentira que el ciclo 26 cerro en la puerta de apagado
—`ui-design-system.md:387-391` la nombra, «el `started` en verde del ciclo 26»— y la
puerta de arranque nunca la recibio. La fila que discrimina: con `arranque=(0, 0)` y
`arranque_categorias=(0, 2)` el texto tiene que **nombrar la categoria** y llevar `AMBAR`,
no `VERDE`. Hoy sale `🚀 2 apps iniciadas` en verde, luego **falla antes del fix**.

**Por que el formato vive en `ui/feedback.py` y no en la vista:** la puerta de apagado
ya tiene ese contrato (`texto_confirmacion_apagado`, invocado por las dos vistas) y el
motivo esta medido en `ui-design-system.md:391`: *«contarlo en la vista seria una segunda
politica de seguridad»*. El recuento de arranque se formatea en el mismo sitio, se invoca
desde **las dos** puertas (`pack_manager_view.py:673-675` y
`dashboard_view.py:510`) y ninguna de las dos escribe su propio literal.

**Cierre:** con T-2 cerrado, la fila «0 y 0» es **inalcanzable** y hay un test que lo dice
con un guard de contrato, no con un `if` de runtime: es el mismo patron que el ya existente
en `run_tests.py:8980-8999` para los workers. El nombre de la categoria en el mensaje sale
de la lista que la vista **ya tiene** (`categorias`, `pack_manager_view.py:658`), no de una
consulta nueva a la DB.

---

## T-4 — Respuestas del dueno: P-1 (el techo de 🟡) y P-2 (que se ve)

**Que:** `proposal.md` §7 deja dos preguntas cerradas. Cada respuesta es trabajo distinto
y **ninguna es bloqueante** para T-1..T-3, que se ejecutan con P-2(a) como suelo.

- **P-1(b)**, si el dueno elige que 🟡 sea inerte al arrancar: el predicado de
  `process_service.py:918` pasa a ser `tier in ("danger", "caution")` y el grid deja de
  pintar la casilla `(arrancar)` de 🟡, o la pinta deshabilitada. **Tarea propia si se
  elige (b)**: toca la politica de las dos listas y su doc, y no pertenece a este ciclo.
- **P-1(a)**, si elige que se acepte: es el texto de T-3, que ya nombra la categoria. **No
  crea trabajo nuevo.**
- **P-2(b)**, si elige el tercer estado: cambia la firma de `start_pack_categories`, los
  dos llamantes, los tres dobles de test y `ui/feedback.py`. **Tarea propia**, y T-2(a) es
  su suelo y comprometido, no su sustituto.

**Cierre:** las dos respuestas quedan escritas en la `description` de `TASK-068` con la
opcion elegida y su fecha, y si alguna abre tarea nueva se crea aqui con su id. **Sin
respuesta, T-1..T-3 se cierran igual y `TASK-068` queda con la decision de techo
pendiente de forma explicita**, que es mejor que cerrarla sin decidir.

---

## T-5 — Cerrar la premisa en la fila que la deja viva, y en el panel

**Que:** la fila 115 de `STATUS.md` y la `description` de `TASK-068` **afirman un bug que
no existe**. Nombran `pack_service.start_pack()` (que no existe),
`pack_service.py:447 filter` (que no existe: cero coincidencias de `filter` en el fichero,
y la linea 447 es un docstring de `TASK-069`) y una puerta de arranque que ignora el campo
(que ya suma, `pack_manager_view.py:665-671`).

**Por que no es cosmetico:** es la fila 🔴 que el Paso 1 del bucle leeria para elegir
trabajo, y su unica fuente viva es `TASK-068`. Sin corregirla, el siguiente ciclo vuelve a
planificar un arreglo a codigo que ya esta bien — que es exactamente la clase de fallo que
este ciclo midio y que `STATUS.md:101` ya declara como el riesgo mayor del panel (una
fila que se cree verdadera y no lo es).

**`STATUS.md` NO es de la ownership del arquitecto**, asi que T-5 se entrega como **texto de
reemplazo** para que lo aplique quien lo posea. Texto propuesto para la fila 115:

> - **🟡 `TASK-068` — la premisa de la fila 115 del 2026-10-05 era FALSA, medida el 2026-10-05
>   (SEGUNDA VEZ en este panel, y por el mismo motivo: una fila que se cree un bug vivo).**
>   Las tres afirmaciones eran falsas: (a) `PackManagerView.start_pack()` **ya suma**
>   `start_categories` (`pack_manager_view.py:665-671`, con su comentario citando TASK-063),
>   igual que la Portada; (b) **`PackService.start_pack()` no existe** —`grep 'def start_pack'`
>   devuelve `start_pack_apps` y `start_pack_categories`, los dos en `process_service.py`—,
>   luego no hay ninguna puerta de servicio que ignorar el campo; (c) **`PackService` no
>   tiene ningun `filter`** (cero coincidencias) y `pack_service.py:447` es un docstring de
>   `TASK-069`, o sea que la cita caducó al cerrarse esa tarea. **Lo que sí era verdad es
>   otra cosa, y es lo vivo:** el `continue` pelado de las dos ramas de omisión
>   (`process_service.py:918-929`) no cuenta ni para `started` ni para `failed`, y con eso
>   `pack_manager_view.py:672-673` pinta `🚀 0 apps iniciadas` en **VERDE**: la mejora que no
>   ocurre, anunciada como un éxito. Y **la premisa era un mutante que sobrevivía a la suite
>   de 183**: el doble de test tenía `llamadas_categorias` y `arranque_categorias`
>   (`run_tests.py:9177-9178`) y **ningún test los leía**, y `pack_normal`
>   (`run_tests.py:9659`) no tenía `start_categories`, luego `if categorias:` no se tomaba
>   nunca — borrar `pack_manager_view.py:666-671` dejaba los 183 en verde.
>   Especificacion: `openspec/changes/2026-10-05-arranque-por-categorias-en-el-gestor/`.
>   **Cierra cuando T-1..T-3 esten verdes y el `mutation-auditor` mate ese borrado por
>   asercion.** Regla que deja este hallazgo: *una puerta sin asercion se lee como una puerta
>   sin comportamiento*, y el andamiaje de un doble de test que nadie lee es la misma promesa
>   sin guardian que ya flota en `validate_docs.py:2153` y en la fila de `docs/index.md`.

**Cierre:** la fila 115 y la `description` de `TASK-068` dicen lo que el código hace, con
`archivo:linea` derivable del arbol, y la seccion «Deuda Tecnica Conocida» no vuelve a
apuntar a un bug inexistente.

---

## Orden y cierre del ciclo

1. **T-1** (guardian) — es lo que cierra la premisa, y es lo que impide que vuelva.
2. **T-2** (el omitido cuenta) — es el sintoma que el dueno reporto, en su forma real.
3. **T-3** (el texto nombra lo que conto) — la misma mentira del ciclo 26, en la otra puerta.
4. **T-4** (decisiones) — en paralelo, no bloquea nada.
5. **T-5** (fila y panel) — al cerrar, con las mediciones ya binders.

**Verificacion de cierre:** `run_tests.py` en verde; `verify_ui_syntax.py` en exito;
`validate_docs.py` en **0 FAIL**; `build_llms_full.py --check` en 0 (este cambio toca
`docs/ai/` y el agregado incluye esa carpeta); `sync_agents.py --check` en 0.
**Ojo con el recuento:** si el ciclo anade tests, los **cuatro declarantes** hay que
actualizarlos (`STATUS.md`, `AGENTS.md`, `README.md` y la tabla de `docs/ai/testing-guide.md`),
porque el check 7 de `validate_docs.py` lo deriva con `ast` y falla si se quedan atras.

**Paso 4 obligatorio. Mutantes que tienen que morir por asercion concreta:**

| Mutante | Asercion que lo mata |
|---|---|
| `BORRA_LA_SUMA` (borrar `pack_manager_view.py:666-671`) | T-1 fila 1 |
| `ARRANCA_LAS_QUE_MATA` (pasar `target_categories` como lista a arrancar) | T-1 fila 2 |
| `NO_PASA_LA_LISTA_DE_APAGADO` | T-1 fila 3 |
| `SUMA_MAL` (`started = started_cats` en vez de `+=`) | T-1 fila 4 |
| `CONTAR_TODO` (`failed += 1` en el `return`) | T-2 fila 3 |
| `OMITIR_SIN_CONTAR` (volver al `continue` pelado) | T-2 fila 1 |
| `VERDE_SIEMPRE` (dejar el toast en `VERDE` con 0) | T-2 fila 2 |
| `TEXTO_CON_LITERAL_EN_LA_VISTA` | T-3 guard de contrato |

**NO toca:** `.github/workflows/**`, `.releaserc.json`, `.commitlintrc.json`, `dist/`,
`basura/`, `docs/archive/`, ni nada de datos del dueno. `src/` solo lo toca `openspec-dev`.
