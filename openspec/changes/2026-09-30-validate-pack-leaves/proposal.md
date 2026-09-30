# Propuesta: validar las HOJAS de un pack — y el `.bak` que nunca se consultó

- **Change ID**: `2026-09-30-validate-pack-leaves`
- **Ciclo**: #19
- **Área de rotación**: 1 — Resiliencia & Robustez (integridad de datos)
- **Taskmaster**: `TASK-031`
- **Subagente de ejecución**: `openspec-dev`
- **Estado**: AUDITADA por architect-review — **NO APROBADA tal como está descrita** (§6: tres premisas del briefing son falsas, y el arreglo propuesto es insuficiente)
- **Alcance**: `src/woptimizer/services/pack_service.py`, `src/woptimizer/models.py`,
  `run_tests.py`, `docs/ai/data-models.md`, `docs/ai/testing-guide.md`
- **Prohibido**: tocar `SYSTEM_PROTECTED_PROCESSES`, la barrera de categoría G-1/G-2, la doble
  pulsación, `gaming_service.py`, y ampliar `CORRUPTION_ERRORS` con nada que no esté en §4.1.
- **Baseline medido**: `python run_tests.py` → 36/36 en verde antes de tocar nada.

## 0. Qué es realmente este trabajo

El encargo dice: *"la guarda valida el contenedor, no las hojas"*, y propone *"validar la FORMA
completa contra el modelo Pydantic antes de clasificar"*. **Las dos mitades están mal.**

- La mitad "no se validan las hojas" **es falsa para la rama moderna** (ya pasan por Pydantic).
- La mitad "el `.bak` sano nunca se consulta y un `save()` posterior lo machaca" **es cierta, pero no
  por la razón que se da, y ocurre bastante más veces** de las que el informe cuenta.

La pérdida de datos de este encargo **no la causa el `keepers` mal formado**: la causa
`_rotate_backup()`, que decide "el principal no está corrupto" con `json.load()` en vez de con
`_read_json()`. Hay **dos definiciones distintas de "no corrupto" en el mismo fichero**, y la que
promete el docstring no es la que se ejecuta.

### 0.1 Matriz medida (sonda viva, `%TEMP%\wopt_probe_031*.py`, `src/` intacto)

Escenario: principal con una hoja patada + `.bak` sano con un pack `salvado`.
Se mide si la corrupción se **clasifica** y si el `.bak` sano sobrevive a `PackService()`.

| # | Principal | Rama | ¿Se clasifica como corrupción hoy? | `.bak` sano tras `load()` |
|---|---|---|---|---|
| A | `{"packs":{"mio":{"id":"mio","name":7}}}` | moderna | **SÍ** (`ValidationError`) | **DESTRUIDO** — pasa a ser el principal corrupto, `ILEGIBLE` |
| B | `{"packs":{"mio":{…,"keepers":"steam.exe"}}}` | moderna | **SÍ** | **DESTRUIDO** |
| C | `{"packs":{"mio":{…,"default_action":"PURGAR"}}}` | moderna | **SÍ** | **DESTRUIDO** |
| D | `{"profiles":{"mio":{"label":"Mio","apps":["a.exe"],"keepers":"steam.exe"}}}` | legacy | **NO** | **DESTRUIDO** (y `keepers` queda `[]`) |
| E | `{"packs":{…},"profiles":{"otro":{…}}}` | moderna | **NO** — `profiles` se ignora como clave extra | **DESTRUIDO** y el pack `otro` **desaparece del disco** |
| F | `{"packs":{"mio":{…,"notas":"comprar la caja"}}}` | moderna | **NO** (extra ignorado) | **DESTRUIDO** y `notas` **se borra en el primer `save()`** |
| G | `{"profiles":{"mio":{"label":7}}}` | legacy | **SÍ** | **DESTRUIDO** |
| H | `{"profiles":{"mio":{"label":"Mio","apps":"a.exe"}}}` | legacy | **SÍ** | **DESTRUIDO** |
| H' | `@@no es json@@` (control) | — | **SÍ** | **INTACTO** ← el único caso que la guarda actual cubre |

Instrumentación del caso A (el que el repo **dice** proteger):

```
_read_json      : ['ValidationError profiles.json', 'OK profiles.json.bak']
recover()       : 1     save() dentro de load(): 1     _rotate_backup(): 1
.bak al terminar load(): ILEGIBLE (ValidationError)
```

La secuencia exacta es: `load()` detecta la corrupción → **recupera bien** del `.bak` → `_ensure_gaming_pack()`
no encuentra `gaming` → llama a `save()` → `_rotate_backup()` abre el principal, que **es JSON válido**
(`json.load` no se queja de `name: 7`) → **copia el principal corrupto encima del `.bak` sano** → y solo
entonces publica el principal nuevo. La recuperación funciona y **en la línea siguiente se tira la única
copia buena**.

**La fila H' es la clave del argumento**: el `.bak` solo se respeta cuando el principal está *roto a
nivel de JSON*. Todo lo demás —incluido todo lo que TASK-026, FIX-009 y TASK-030 llaman "corrupción" en su
propia documentación— lo destruye. `data-models.md:53-55` afirma hoy:

> *"si el principal está corrupto **NO se rota**: un principal roto pisaría el `.bak` bueno, que es justo
> lo que permite la recuperación de `load()`."*

**Esa frase es falsa y es falsificable con seis líneas.** La fila H' es el único caso en que se cumple.

## 1. Punto 1 — Inventario de campos: qué se valida y qué no

`src/woptimizer/models.py:13-25`. Ocho campos, dos obligatorios, seis con default:

| Campo | Tipo | Obligatorio | ¿Validado hoy en la rama **moderna**? | ¿Validado hoy en la rama **legacy**? |
|---|---|---|---|---|
| `id` | `str` | sí | **SÍ** (implícito, `AppData(**raw_data)`) | **SÍ** (se inyecta `id=k`) |
| `name` | `str` | sí | **SÍ** | **NO como campo**: se lee `v.get("label")`; un `label` int sí lo coge `ValidationError` al construir |
| `apps` | `List[str]` | no | **SÍ** | **SÍ** de rebote (`Pack(apps="a.exe")` falla) |
| `keepers` | `List[str]` | no | **SÍ** | **NO — la rama legacy nunca lo lee** |
| `target_categories` | `List[str]` | no | **SÍ** | **NO — la rama legacy nunca lo lee** |
| `is_favorite` | `bool` | no | **SÍ** | **SÍ** de rebote |
| `is_gaming` | `bool` | no | **SÍ** (forzado a `False` en legacy) | forzado |
| `default_action` | `Literal["start","kill"]` | no | **SÍ** | **forzado a `"start"`** |
| *(clave extra)* | — | — | **NO** (`extra="ignore"` por defecto) | — |

**El agujero es exactamente la diferencia entre las dos columnas, y la causa es que la rama legacy
construye el `Pack` con una lista de campos escrita a mano** (`pack_service.py:161-169`): 5 de 8. Los dos
campos que faltan (`keepers`, `target_categories`) son los dos que se perderían. No es casualidad: es la
firma del defecto.

## 2. Punto 2 — La solución correcta

Se descartan tres opciones. La elegida es la cuarta, que el briefing no nombra.

### (a) Más `isinstance` campo a campo — **RECHAZADA**

Es la lista que **ya está mal**. `keepers` y `target_categories` no están en
`pack_service.py:161-169` porque alguien escribió esa lista a mano y se olvidó de dos entradas. Añadir
`if not isinstance(v["keepers"], list): raise …` es **una quinta entrada en una lista que ya falló dos
veces**, y la MutableList de campos que hay que recordar crece con cada campo nuevo de `Pack`. Además es
indistinguible de (b) en comportamiento (salvo en la clave extra, §3), así que un test no puede decir
cuál de las dos se ha implementado.

### (b) "Validar contra el modelo Pydantic antes de clasificar" — **YA ESTÁ HECHO, en la rama equivocada**

Medido: `pack_service.py:171` es `return AppData(**raw_data)`. Eso **ya es** validación contra el
modelo, y las filas A/B/C de §0.1 lo demuestran: `name: 7`, `keepers: "str"` y `default_action: "PURGAR"`
**se detectan y se recuperan hoy**, sin tocar nada. La rama que necesita validación es la que
**se salta el modelo** (`pack_service.py:153-169`, un `Pack(...)` literal con cinco campos). "Validar
contra el modelo" no es una fase que añadir: es **dejar de saltárselo**.

### (c) Distinguir "no se puede leer" de "se puede leer pero está incompleto" — **RECHAZADA como clasificación, ACEPTADA como nombre**

`Pack` es **un** `BaseModel`: o valida o no valida. No existe el estado intermedio que la categoría
propondría, así que "incompleto" acabaría siendo una synonym de "válido" y no cambiaría una sola rama
de código. Y en la rama que importa, "incompleto" no tiene salida: `List[str]` no admite un `str`, así
que "cargarlo con lo que haya" no es una opción, es una metáfora.

Lo que **sí** se conserva de la idea es su **nombre**, porque hace falta para diagnosticar: el mensaje
debe decir *campo*, *pack* y *tipo real* (§3).

### ✅ ELEGIDA — «Una sola puerta, y esa puerta es el modelo»

Cuatro cambios, de los cuales **uno solo es de producción de verdad**:

**E-1 · Una sola definición de "este fichero es legible".**
Extraer `def _es_legible(self, path) -> bool` = `try: self._read_json(path); True except CORRUPTION_ERRORS:
False`, y hacer que **`_rotate_backup()` lo use en vez de `json.load()`**. Hoy el fichero contiene dos
definiciones de "no corrupto" y el docstring (`pack_service.py:200-201`) describe la que no se ejecuta.
Sin este punto, E-2 no sirve de nada.

**E-2 · La rama legacy deja de saltarse el modelo.**
Traducir el registro legacy a un `dict` **moderno** y pasárselo a `Pack`:

```python
traducido = dict(v)                      # copia: no se muta el dato del usuario
traducido["name"] = v.get("label", k)     # el ÚNICO renombrado que existe
traducido["id"] = k
traducido.pop("label", None)
traducido["is_gaming"] = False
packs_dict[k] = Pack(**traducido)        # <- la validacion la hace el MODELO
```

Esto es **estructural, no campo a campo**: en cuanto `Pack` gane un campo, la rama legacy lo empezará a
leer sin que nadie se acuerde. `ValidationError` ya está en `CORRUPTION_ERRORS` (`pack_service.py:40`):
no hace falta ninguna clase de error nueva ni ninguna rama nueva. La rama `__system_gaming__` se deja
como está (es un preset fijo, no dato del usuario).

**E-3 · `load()` deja de escribir.** Ver §4. Es el punto que **sostiene el diseño**: elimina de raíz la
clase de bug "el arranque destruye la copia de seguridad".

**E-4 · Política de campos desconocidos y de la ambigüedad `packs`+`profiles`.** Ver §3.

## 3. Punto 3 — El dilema semántico (decisión de producto)

### La pregunta, sin adornos

Un pack con `keepers` como `str` en vez de `List[str]`: ¿es **corrupción** (recuperable del `.bak`) o es
**un pack válido con un campo raro** (se carga con lo que haya)?

### La trampa de la premisa: la segunda opción no existe

`Pack.keepers` es `List[str]`. **Pydantic rechaza un `str`**, y con razón: si se acepta, `"steam.exe"`
pasa a ser `["s","t","e","a","m",".","e","x","e"]` y `GamingService.should_kill_for_gaming`
(`gaming_service.py:24`) deja de proteger **nada**. La única forma de "cargarlo con lo que hay" es
**normalizar a `[]`**, y eso no es cargar: es **borrar**.

### Y el no-op no es neutro: desarma el anti-brick

Este es el argumento que decide el caso, y sale del código, no del gusto. `keepers` es la lista de
**procesos protegidos** del Gaming Mode (`gaming_service.py:16-24`, y el comentario de
`pack_manager_view.py:19` lo llama explícitamente el patrón defensivo). Un usuario que escribe a mano
`"keepers": "steam.exe"` y pulsa "Preparar Gaming Mode" con `keepers` normalizado a `[]` **mata su
Steam**. Eso no es un problema cosmético de datos: es exactamente el **brick** que
`SYSTEM_PROTECTED_PROCESSES` y la barrera de categoría existen para impedir.

El coste real de cada opción, medido:

| Opción | Qué gana | Qué pierde |
|---|---|---|
| **No es corrupción** → `keepers: []` | El pack carga | **El campo se borra en el primer `save()`, sin aviso, y el Gaming Mode mata lo que debía proteger** (brick) |
| **Es corrupción** → se recupera del `.bak` | El campo sobrevive; el fichero se puede diagnosticar | El usuario puede obtener una **versión distinta** de su configuración (pierde lo escrito desde el último guardado) |

### ✅ DECISIÓN: es corrupción, con tres condiciones que hacen aceptable el coste

> **Criterio (§3.1):** *una hoja que viola el esquema es corrupción si y solo si el servicio no puede
> representarla **sin perder información**.* Y en ese caso la recuperación tiene prohibido sobrescribir
> el `.bak`, y prohibido destruir el principal si no hay nada con qué sustituirlo.

Se elige **corrupción** porque el no-op pierde un campo **anti-brick** de forma invisible e irreversible,
mientras que la recuperación pierde como mucho la última sesión de edición, de forma **visible y
diagnosticable**. Reversibilidad y visibilidad ganan a fidelidad: un keeper se vuelve a escribir en diez
segundos; un fichero borrado no se reconstruye.

Las tres condiciones, que son las que convierten una decisión discutible en un contrato:

1. **El mensaje nombra campo, pack y tipo real.** `PerfilCorruptoError` hoy solo dice el tipo del
   *contenedor* (`pack_service.py:143-144`). Con E-2 el mensaje lo da Pydantic, pero hay que exigir
   explícitamente `keepers`, `mio` y `str` en el texto. Un `ValidationError` crudo de Pydantic (14 líneas
   de diagnóstico interno) **no cumple** este criterio: quien tiene que arreglar el fichero es el
   usuario, delante del bloc de notas, no un programador.
2. **La recuperación es observable, no solo un `logger.warning`.** Hoy "recuperado del `.bak`" vive solo
   en el log, y un usuario no abre el log. `PackService` expone el hecho (p. ej. `pack_dañados` /
   `recuperado_de_backup`) y la UI lo muestra en el `status_label` que la Trampa #14 ya exige para todo
   estado no trivial. Sin esto, "corrupción" sigue siendo silenciosa por otro camino.
3. **Si no hay `.bak` legible, NO se regenera a lo bruto.** Hoy `load():106-109` hace
   `AppData()` + `_ensure_gaming_pack()` + `save()`: **reescribe el fichero del usuario con un solo
   pack**. Ese camino no es hypothetical: se cumple siempre que no haya un `.bak` legible, que es el caso
   de una instalación limpia y también el de un `.bak` ya destruido por la fila A. Con
   E-3 (`load()` read-only) **esa rama desaparece**: se carga lo legible, se marca el fichero como dañado,
   se deja el fichero **en disco tal cual** para que el usuario o una versión posterior lo reparen, y no
   se escribe nada. La pérdida se vuelve **reversible**.

### 3.2 · Campos desconocidos (`extra`): NO son corrupción

Medido (fila F): `{"packs":{"mio":{…,"notas":"comprar la caja"}}}` carga bien y **`notas` desaparece del
disco en el primer `save()`**. Hoy eso es un borrado silencioso.

- **Clasificación: NO corrupción.** Es el único mecanismo que hace el formato **compatible hacia
  delante**: un `.bak` escrito por un build más nuevo tiene que ser legible por uno más viejo, que es
  justo el momento en que el `.bak` hace falta. Una regla estricta (y por tanto también la opción (a))
  classificaría como corrupción el fichero sano de una versión más nueva.
- **Pérdida: NO se acepta en silencio.** `model_config = ConfigDict(extra="allow")` en `Pack` y `AppData`
  conserva el campo en el ciclo carga→guarda. Cambio de tres líneas, y es lo que convierte "se pierde
  calladamente" en "sobrevive, aunque esta versión no lo entienda". **No bloqueante**: si el
  mutation-auditor lo ve desestabilizar otra cosa, se documenta como deuda y se deja el `extra="allow"`
  para su propia tarea. Pero el test que lo fija (T6) **sí** es bloqueante, porque fija la decisión.

### 3.3 · `packs` + `profiles` en el mismo fichero: SÍ es corrupción

Medido (fila E): la condición de `pack_service.py:133` exige `'packs' not in raw_data`, así que con
ambas claves se va a la rama moderna, `profiles` se ignora como clave extra, y **los packs legacy
desaparecen del disco en el primer `save()` sin que nada se clasifique**. Cualquier resolución —migrar
o descartar— borra packs en silencio, así que aquí "corrupción" y "normalizar" cuestan lo mismo y gana
la opción segura: se clasifica como corrupción y se nombra el conflicto en el mensaje.

## 4. Punto 4 — El efecto colateral: la rotación **no** cumple (y el hueco es mayor)

**Respuesta directa: no, el código de rotación no cumple, y el hueco no depende de la corrupción de
hoja.** La tabla de §0.1 lo mide: el `.bak` sano se destruye en **7 de 8** escenarios, incluidos A, C, G
y H, que el repositorio **afirma** proteger desde TASK-026.

Dos arreglos, y **los dos hacen falta**:

**R-1 · `_rotate_backup()` valida con `_read_json()`, no con `json.load()`.**
`pack_service.py:206-207` hace `json.load(f)` y solo así puede un `name: 7` pasar por "sano".
Es la fila H' la única que sale bien, y es la única que el código realmente comprueba.

**R-2 · `load()` deja de escribir (E-3).** Es el que **sostiene** el diseño: mientras `load()` pueda
llamar a `save()`, cualquier futuro `_ensure_gaming_pack()` con un criterio nuevo vuelve a abrir la
puerta. Con `load()` read-only, la rotación solo ocurre cuando el usuario hace algo real, y ahí E-1 ya
la hace correcta.

**Coste de E-3, medido antes de proponerlo:** `PROFILES_FILE` (`config.py:26`) tiene **un solo
consumidor**, `PackService.__init__` (`pack_service.py:55`) — verificado por grep, no por suposición. Y
`get_gaming_pack()` (`pack_service.py:258`) cae a `DEFAULT_GAMING_PACK.model_copy(deep=True)` si no hay
pack en memoria, así que la app funciona **sin fichero**. Lo único que cambia es que en una instalación
limpia no se crea un `profiles.json` vacío hasta que el usuario haga algo: estrictamente mejor, porque
un fichero vacío solo confunde. Esto también **elimina la doble escritura** que TASK-030 §4.4 dejó
documentada como deuda (medida: `save()=1, _rotate_backup()=1` dentro de `load()`), y con ella la razón
de que ningún espía de llamadas pueda discriminar.

## 5. Punto 5 — Los tests, y la mutación exacta que debe morir

Criterio: si quito la validación de X, ¿qué aserción se queja? Los que no puedan nombrar aserción, no
entran. Nombres nuevos `L*` para no chocar con la tabla M1–M11 del ciclo 18.

| Sonda | Invariante | Mutación que debe morir | Por qué esa aserción y no otra |
|---|---|---|---|
| **L1** `test_la_rotacion_usa_la_misma_puerta_que_load` | con principal **válido como JSON pero ilegible para el servicio** + `.bak` sano: tras `PackService()`, `PackService._read_json(None, ruta + ".bak")` **no lanza** y devuelve el pack `salvado` | **L-M1**: `_rotate_backup` → `json.load` otra vez (o `pass`) | Sin la aserción "el `.bak` sigue siendo legible" el test pasa hoy. Hoy el `.bak` acaba siendo el principal corrupto: **la aserción falla con `ValidationError`, no por una excepción del test** |
| **L2** `test_la_hoja_malformada_se_clasifica` | tabla de 6 hojas (`keepers` str, `target_categories` dict, `apps` int, `name` int, `is_favorite` "si", `default_action` "PURGAR") **en las dos ramas**: cada una da `PerfilCorruptoError` (legacy) o `ValidationError` (moderna), y con `.bak` sano recupera `salvado` **sin** que el mensaje sea un `ValidationError` crudo de 14 líneas | **L-M2**: volver a la construcción a mano de `Pack(...)` en la rama legacy; o quitar `traducido["id"] = k` | Hoy la fila legacy devuelve `OK` y el pack carga con `keepers == []`. La aserción que muere dice `keepers`/`mio`/`str` en el texto: sin ella, E-2 podría "cumplirse" dejando que Pydantic hable y nadie lo entendería |
| **L3** `test_load_no_escribe` | tras `PackService()` con **cualquier** principal: los bytes del `.bak` son los de antes, y `save()` no se invocó desde `load()` (comprobado por un doble que cuenta, **no** por umbral) | **L-M3**: `_ensure_gaming_pack` vuelve a llamar a `save()`; o `load()` vuelve a tener su `self.save()` de `load():109` | Sin este test, E-1 y E-2 pueden "^implementarse^" y L1 seguir verde: el `.bak` se destroye igual, un poco más tarde. **Es la única sonda que ata E-1 y E-3 entre sí** |
| **L4** `test_la_recuperacion_no_sobrescribe_el_bak` | tras recuperar, `bytes(.bak)` es **byte a byte** el `.bak` original, y el `.bak` **no** contiene la versión recuperada | **L-M4**: en la ruta de recuperación, `save()` antes de leer el `.bak`; o rotar "para dejar el backup al día" | Sin la comparación de bytes, "no sobrescribir" y "sobrescribir con lo mismo" son indistinguibles. Es la aserción que hace letal a L-M4 |
| **L5** `test_sin_bak_legible_no_se_sobrescribe_el_principal` | principal corrupto **sin** `.bak`: los bytes del principal **no cambian**, la app **arranca**, y el pack `mio` aparece marcado como dañado (no desaparece en silencio) | **L-M5**: reponer `AppData()` + `_ensure_gaming_pack()` + `save()` en `load():106-109` | Hoy el fichero del usuario se reescribe con un solo pack. La aserción que muere es "los bytes del principal son los de antes" |
| **L6** `test_un_campo_desconocido_no_es_corrupcion_y_no_se_borra` | `packs.mio.notas = "comprar la caja"`: arranca **sin** recuperar del `.bak`, y tras un `save()` el campo **sigue en el fichero** | **L-M6**: `extra="forbid"`, o el `isinstance` de whitelist de la opción (a) | **Esta es la sonda que separa (a) de (b)**: sin ella, "más isinstance" y "validar contra el modelo" son indistinguibles y el mutation-auditor no puede decir cuál se ha implementado |
| **L7** `test_packs_y_profiles_a_la_vez_es_corrupcion` | `{"packs":{…},"profiles":{"otro":{…}}}`: se clasifica como corrupción **nombrando las dos claves**, y con `.bak` sano no se pierde `salvo` ni `otro` | **L-M7**: quitar `'packs' not in raw_data` de la condición de `pack_service.py:133` | Hoy `otro` desaparece del disco sin que nada se clasifique. La aserción que muere es "el pack `otro` sigue ahí después del `save()`" |

**L6 y L7 son hallazgos de esta auditoría, no estaban en el encargo.** Sin ellos, L2 y L3 se pueden
cumplir dejando dos vías de pérdida silenciosa abiertas.

### 5.1 Orden de ejecución

1. **L6, L7** (solo test; fijan dos decisiones de §3.2/§3.3 y deben **fallar** con el código actual).
2. **L1** (solo test; falla hoy — es la fila A de §0.1).
3. **L3, L4, L5** (solo test; fallan hoy).
4. **E-1** (`_rotate_backup` → `_read_json`) + **L1** en verde.
5. **E-2** (rama legacy por el modelo) + **L2** en verde.
6. **E-3** (`load()` read-only) + **L3, L4, L5** en verde.
7. **E-4** (`extra="allow"`) + **L6** en verde.
8. Documentación viva: `data-models.md` (§3.1 como contrato, y **corregir la frase falsa de
   `data-models.md:53-55`**) y `testing-guide.md` (las sondas y por qué existe cada una).

## 6. Correcciones obligatorias al encargo de TASK-031

1. **"La guarda valida el contenedor, no las hojas" → FALSO para la rama moderna.** `AppData(**raw_data)`
   (`pack_service.py:171`) ya valida las hojas: `name: 7`, `keepers: "str"` y `default_action: "PURGAR"`
   se detectan y se recuperan **hoy** (filas A–C). La rama sin validar hojas es **solo la legacy**, y la
   causa es que se salta el modelo con un `Pack(...)` de 5 campos (`pack_service.py:161-169`).
2. **"La solución es validar la forma completa contra el modelo Pydantic antes de clasificar" → ya se
   hace, y no es lo que falta.** Falta **que la rama legacy deje de saltarse el modelo**, y falta que
   `_rotate_backup()` use la misma puerta que `load()`. Con la solución tal como está escrita, el `.bak`
   **sigue muriendo**: medido con la guarda de hoja puesta, los 14 escenarios siguen machacando el
   `.bak` sano.
3. **"Un `save()` posterior machaca ese `.bak`" → understated.** No es un `save()` posterior del usuario:
   es el **`save()` que `_ensure_gaming_pack()` hace dentro del propio `load()`**, y ocurre en 7 de 8
   escenarios, incluidos los que el repo dice proteger. `load()` es read-only, no el usuario.
4. **"Pérdida silenciosa e irreversible" → el "irreversible" era mérito del bug, no un supuesto.** La
   fila E (packs+profiles) y la fila F (campo desconocido) son pérdidas **independientes de la
   corrupción de hoja** y ninguna de las dos la arregla E-2.
5. **La premisa implícita "un `keepers` mal formado es alcanzable desde la app" → no verificada.**
   Grep de `src/`: `keepers` y `target_categories` solo se escriben como `list`, en
   `pack_service.py:50-51` y `DEFAULT_GAMING_PACK`. **Ningún código de la app puede producir** un
   `str` ahí. La vía real es un `profiles.json` editado a mano —y `data-models.md:155-158` **asume
   explícitamente** que el usuario lo edita a mano—, un `.bak` de otro build, o un archivo truncado. La
   severidad **se mantiene** (la pérdida de `keepers` es un brick, §3), pero el escenario hay que
   enunciarlo así y no como "la app puede escribirlo mal".

## 7. Verificación de cierre

- `python run_tests.py` en verde, con L1–L7 registradas en el `__main__` (**36 → 43**).
- `python verify_ui_syntax.py` y `python validate_docs.py` en verde.
- **Reejecutar la matriz de §0.1 con los tests finales**: las 7 mutaciones L-M1…L-M7 deben morir y la
  columna ".bak sano tras `load()`" debe quedar en `INTACTO` en **los 8** escenarios. Sin ese reejecutado
  el ciclo no se cierra, porque L1 por sí solo no cubre la fila legacy.
- `data-models.md:53-55` corregida: la promesa de "no se rota si el principal está corrupto" es cierta
  a partir de este cambio, y hasta entonces era falsa.
- Cero ediciones fuera de: `pack_service.py`, `models.py`, `run_tests.py`, los dos `docs/ai/` y este
  change.
