# Modelos de Datos y Persistencia (v3)

## Esquema Pydantic (`src/woptimizer/models.py`)

### 1. `ProcessInfo`
Representa un proceso en memoria listado mediante `psutil`:
- `name`: Nombre limpio sin extensión (ej: `chrome`).
- `full_name`: Nombre con extensión (ej: `chrome.exe`).
- `pid`: ID numérico del proceso en Windows.
- `exe_path`: Ruta completa al ejecutable en disco (si es accesible).
- `category`: Categoría asignada (ej: `🔴 Navegadores`).
- `priority`: Nivel de prioridad (`high`, `medium`, `low`, `none`).

### 2. `Pack` (Concepto Unificado)
Reemplaza a los perfiles legacy. Un pack puede ser lanzado (abrir) o cerrado (apagar):
```python
class Pack(BaseModel):
    model_config = ConfigDict(extra="allow")     # TASK-031: ver §4.4
    id: str                                  # Clave única = identidad del pack (§4.5)
    name: str                                # Nombre visible
    apps: List[str] = Field(default_factory=list) # Ejecutables: RUTA ABSOLUTA desde TASK-027,
                                          # o nombre pelado en los packs ya guardados (ver abajo)
    is_favorite: bool = Field(default=False, strict=True)   # Si se muestra en la portada
    is_gaming: bool = Field(default=False, strict=True)     # Si es el preset protegido del sistema
    default_action: Literal["start", "kill"] = "start"  # Acción rápida por defecto
    keepers: List[str] = Field(default_factory=list) # Apps protegidas en gaming (ej: ['discord.exe'])
    target_categories: List[str] = Field(default_factory=list) # Categorías a cerrar dinámicamente en Gaming
```
> `default_action` es un `Literal["start", "kill"]`, no un `str` cualquiera: un valor
> fuera del enumerado es **corrupción**, no un pack válido (§4.4). Su valor por
> defecto es **`"start"`**, no `"kill"`: el que usa el servicio es
> `DEFAULT_GAMING_PACK` (`pack_service.py`, constante `DEFAULT_GAMING_PACK`, líneas
> **231-240**), y el `Literal` va con `strict` implícito en los `bool` de al lado.
> *(Corrección TASK-031 iteración 3: este documento citaba `pack_service.py:70` y
> `pack_service.py:70-79`, líneas que no existen desde la iteración 1; el bloque vive
> en 231-240. Se cita el símbolo además de la línea para que la deriva no vuelva a
> producir una cita falsa.)*

**`strict=True` en los booleanos (TASK-031 iteración 2, sondas fijadas en la 3).**
JSON tiene un tipo booleano propio, así que una cadena en un campo `bool` no es un
valor válido: es un error de escritura. En modo laxo, Pydantic coaccionaba `"true"`,
`"1"` y `"si"` a `True` **sin avisar**, y con `is_gaming` eso convertía un pack normal
en un pack de **sistema invisible e indeletable**: no aparecía en `get_user_packs()` y
`delete_pack` respondía *"No se puede eliminar el pack de sistema"* (medido por el
`mutation-auditor` de la iteración 2). Con `strict=True` es corrupción, se recupera
del `.bak` y el aviso nombra el campo. No rompe nada de lo que escribe la app: un
`grep` de `src/` no encuentra ni un solo booleano no booleano. Sonda: `L2`, filas
`is_gaming: "true"` (solo rama moderna, porque en la legacy `is_gaming` se fuerza a
`False`) e `is_favorite: "true"` / `is_favorite: 1` (las dos ramas).

> ⚠️ **La fila `is_favorite: "si"` era un test que NO PODÍA morir (iteración 3, P5).**
> Pydantic v2 en modo laxo **rechaza** `"si"` igual que en modo estricto: no está en su
> lista de booleanos laxos. Esa fila quedaba verde **con y sin** `strict=True`, así que
> su mutación-sobreviviente era invisible; el `strict=True` de `is_favorite` estaba
> puesto y **nadie lo vigilaba**. Sustituida por `"true"` (que sí coacciona a `True`) y
> por `1` (idéntico, en `int`), que es la fila que mata `L-M4b`. Regla para las
> sondas de coerción: **el valor de la fila tiene que ser un valor que el modo laxo
> coaccione**, o la prueba no distingue nada.

**`extra="allow"` (TASK-031).** Un campo que esta versión **no conoce** no es corrupción:
sobrevive al ciclo carga → guarda en vez de borrarse en el primer `save()`. Es el único
mecanismo que hace el formato **compatible hacia delante**, y es justo cuando más hace
falta (un `.bak` escrito por un build más nuevo tiene que ser legible por uno más viejo).
`ProcessInfo` **no** lleva `extra="allow"`: no se persiste y no lo necesita.

> ⚠️ **El `extra="allow"` de `AppData` es una LÍNEA PORTANTE contra la pérdida de datos,
> no solo compatibilidad (iteración 2).** Medido: un `profiles.json` con la **raíz mal
> escrita** (`{"perfiles": …}` en vez de `{"packs": …}`, `{"packs2": …}`) arranca, `load()`
> ve **cero packs**, y el **primer `save()` real** del usuario deja el fichero como
> `{"packs": …}`: los packs del usuario desaparecen del disco, sin aviso. Con
> `extra="allow"` la raíz desconocida se conserva como dato y sobrevive a **todos** los
> guardados. Sonda **`L8`** (muta `extra="ignore"` en `AppData` y el fichero se vacía).
> El precio, declarado y **no resuelto** (deuda): el arranque ve cero packs sin avisar.
> Clasificarlo como corrupción sería **peor**, no mejor: en la ruta sin `.bak`, `load()`
> hace `self._data = AppData()` (§4) y el siguiente guardado publicaría
> `{"packs": {"gaming": …}}` — los packs se perderían igual, y con un aviso de encima.

> ⚠️ **Y no bastaba: en la rama legacy el `extra="allow"` no conservaba NADA (iteración 3,
> M8).** La rama moderna hace `AppData(**raw_data)`, así que la raíz desconocida se
> guarda en el objeto y sobrevive. La legacy construía el `AppData` **desde cero**
> (`AppData(packs=packs_dict)`) y se llevaba por detrás **toda** la raíz que no fuese
> `packs`/`profiles`: medido, un `profiles.json` legacy con `favorite` en la raíz
> arrancaba sin clasificar nada y, en el **primer `save()` real**, quedaba como
> `{"packs": …}` — `favorite` **desaparecía del disco, en silencio**. Un `extra="allow"`
> que no se copia al objeto no conserva nada, así que la línea es **necesaria y no
> suficiente**. Arreglo: la rama legacy copia la raíz entera **menos `profiles`** a su
> `AppData` (su contenido ya está traducido en `packs`; conservar `profiles` escribiría
> un fichero con las **dos** claves, que la lectura siguiente clasifica como corrupción,
> `L7`: un landmine que solo explotaría en el **segundo** arranque del usuario). Sonda
> **`L11`**.

### 3. `AppData` (Estructura de `profiles.json`)
```python
class AppData(BaseModel):
    model_config = ConfigDict(extra="allow")     # TASK-031: ver §4.4
    packs: Dict[str, Pack] = Field(default_factory=dict)
```

## Reglas de Persistencia
- Archivo en disco: `profiles.json` ubicado en el directorio de la aplicación (`_app_dir()`).
- Si el archivo **no existe**, `load()` **no lo crea** (TASK-031: `load()` es de solo
  lectura). Se crea con el primer `save()` real, cuando el usuario hace algo. La app
  funciona sin fichero: el pack `gaming` se asegura **en memoria**.
- Si el archivo está **corrupto**, se intenta recuperar del `.bak` (ver §4) y **no se
  regenera nada**: el fichero se queda **en disco tal cual**, marcado como dañado y con
  un aviso para la UI (§4.4). Antes se regeneraba de inmediato el pack protegido
  `gaming` por defecto, lo que **reescribía el fichero del usuario** con un solo pack.
  Los valores reales de ese pack son los de `DEFAULT_GAMING_PACK`
  (`pack_service.py`, líneas **231-240**; antes este documento citaba `70-79`, que
  no existen), y son:
  - `id`: `"gaming"`
  - `name`: `"🚀 Preparar para Gaming"`
  - `is_favorite`: `True`
  - `is_gaming`: `True`
  - `default_action`: `"kill"`
  - `apps`: `["chrome.exe"]`
  - `keepers`: `["steam.exe", "discord.exe"]`
- El pack con `is_gaming = True` **NUNCA** puede ser eliminado por el usuario.
- **`apps`: rutas absolutas y nombres pelados conviven a proposito (TASK-027 / FIX-003).** Desde
  TASK-027, `ProcessManagerView.on_add_to_pack` guarda `ProcessInfo.exe_path` (la ruta real del
  ejecutable) y solo degrada a `full_name` cuando `psutil` no puede dar el `exe` (`AccessDenied`).
  **No hay migracion de los `apps` ya guardados**: el lector
  (`ProcessService._resolver_app`) resuelve el nombre pelado **dentro de las raíces permitidas**
  (`%ProgramFiles%`, `%LOCALAPPDATA%`, ...), nunca por el PATH, así que un pack existente sigue
  arrancando sin tocar el disco. Lo que cambia es que un nombre pelado **se puede rechazar** con un
  motivo en el log: es la degradacion aceptada, no una app perdida sin explicacion.
  Un nombre pelado en un pack nuevo solo significa que el proceso no traia `exe`.

### 4. Contrato de escritura de `profiles.json` (TASK-026 / FIX-009, revisado por TASK-031)

`PackService.save()` sigue tres pasos, en este orden:

1. **Rotación del backup** (`_rotate_backup()`): si el archivo ya existe **y es legible
   para el servicio**, se copia con `shutil.copy2(path, path + ".bak")` **antes** de
   tocarlo. La copia contiene la versión **ANTERIOR** (rotación real, no una copia
   posterior idéntica). En una instalación limpia no se crea un `.bak` basura, y si el
   principal **no** es legible no se rota: un principal roto pisaría el `.bak` bueno, que
   es justo lo que permite la recuperación de `load()`.
   - **"Legible" lo decide `_es_legible()`** (`try: self._read_json(path) / except
     CORRUPTION_ERRORS: False`), es decir **la misma puerta que usa `load()`**.
   - ⚠️ **Corrección de TASK-031 (esta frase era FALSA hasta este ciclo).** La versión
     anterior de este documento afirmaba *"si el principal está corrupto **NO** se rota"*
     como si se cumpliera, y era falsificable con seis líneas: la guarda comparada era
     `json.load()`, que **no** es la misma puerta. Un `{"name": 7}`, un
     `{"keepers": "steam.exe"}` o un `{"default_action": "PURGAR"}` son **JSON válido**,
     así que la rotación los daba por sanos y **copiaba el principal corrupto encima del
     `.bak` sano**. Medido antes del arreglo: el `.bak` sano moría en **7 de 8**
     escenarios, incluidos los que el repositorio afirmaba proteger. El único caso que
     sobrevivía era `@@no es json@@`, que es exactamente el único que `json.load()`
     comprueba. Desde TASK-031 hay **una sola** definición de "no corrupto" en el
     fichero, y el docstring de `_rotate_backup()` describe la que se ejecuta.
     Sondas: `L1` (el `.bak` sigue siendo legible tras rotar) y `L4` (recuperar no lo
     refresca).
2. **Escritura atómica**: se vuelca a `profiles.json.tmp` (mismo directorio) y se publica
   con `os.replace`, así que un corte de luz no deja un `profiles.json` truncado. Si algo
   falla, el temporal se borra (con `contextlib.suppress`, para que la limpieza nunca
   enmascare el error original) y la excepción se propaga: **el archivo anterior queda
   intacto**.
3. Publicación efectiva: `os.replace` es atómico en Windows.

**Recuperación en `load()`** ante un archivo corrupto:

- Se capturan **solo** errores de corrupción: `json.JSONDecodeError`, `pydantic.ValidationError`,
  `TypeError` (el JSON no tiene la forma esperada) y `UnicodeDecodeError` (bytes no UTF-8),
  más `PerfilCorruptoError` (§4.1/§4.2/§4.4). Se registra con `logger.warning` y se
  intenta `_read_json(path + ".bak")`. **La recuperación no escribe nada**: guardar ahí
  rotaría el principal corrupto sobre el backup sano.
- Un `OSError` al leer o escribir (permisos, EIO, bloqueo del antivirus) **no** es corrupción y
  **se propaga**: no entra en la ruta que regenera y sobrescribe los packs del usuario.
- **Si tampoco hay `.bak` recuperable, NO se regenera nada** (TASK-031, era lo contrario):
  se carga lo legible (que puede ser nada), se marca `fichero_danado` y **el fichero se
  queda en disco tal cual** para que el usuario o una versión posterior lo reparen. Antes
  `load()` hacía `AppData()` + `_ensure_gaming_pack()` + `save()` y **reescribía el
  fichero del usuario con un solo pack**: una pérdida irreversible y sin aviso. Sonda: `L5`.
- La recuperación es **observable**, no un `logger.warning` invisible: `PackService`
  expone `fichero_danado`, `recuperado_de_backup`, `motivo_danado` y
  `mensaje_danado() -> Optional[str]`, que la UI pinta en su `status_label`
  (Trampa #14: *nada se traga en silencio*). El **estado observable es en el servicio**;
  el pintado en la vista es de la capa de UI y sigue pendiente de cablear.
- **`load()` es de SOLO LECTURA** (TASK-031). Antes escribía dos veces (una desde
  `_ensure_gaming_pack()` y otra desde `load()`), y era el `save()` de `_ensure_gaming_pack()`
  —no un `save()` posterior del usuario— lo que machacaba el `.bak` sano. Ahora la
  rotación solo ocurre cuando el usuario hace algo real, que es donde E-1 ya la hace
  correcta. Sonda: `L3`.

### 4.1 Contrato de clasificación de `profiles.json` (TASK-030)

`CORRUPTION_ERRORS` es la **única** lista de clases que `load()` considera "el archivo está roto",
y por tanto la única que puede entrar en la recuperación desde el `.bak` y, si no hay backup
recuperable, en la regeneración que **reescribe** el archivo del usuario:

| Clase | Qué es | Por qué entra (o no) |
|---|---|---|
| `json.JSONDecodeError` | JSON a medias (apagón durante el `json.dump`) | Es corrupción de verdad. |
| `pydantic.ValidationError` | El JSON parsea pero un `Pack` viola su esquema (p. ej. `default_action` fuera del `Literal["start","kill"]`) | Es dato roto, no un bug. |
| `TypeError` | El JSON no tiene la forma de un mapeo (`[1,2,3]`, una lista donde se espera un dict) | Idem. |
| `UnicodeDecodeError` | El fichero no es UTF-8 | Es corrupción de verdad. |
| **`PerfilCorruptoError`** | **Las seis formas que la propia clase declara como "el archivo está roto"** (§4.1.1) | Es dato roto, pero **deliberadamente detectado antes de desreferenciar** (§4.2) o en la puerta de identidad / error de escritura (§4.5). |
| `OSError` | Permisos, EIO, fichero bloqueado por el antivirus | **FUERA.** No es corrupción y no puede entrar en la ruta que sobrescribe. Se propaga. |
| `AttributeError`, `KeyError`, `NameError` | Bugs internos | **FUERA, a propósito.** Ver abajo. |
| `Exception` / `BaseException` | — | **PROHIBIDO.** Fue el bug del ciclo 15. |

#### 4.1.1 Los seis orígenes de `PerfilCorruptoError` (iteración 3, P5)

Esta tabla listaba **dos** causas para `PerfilCorruptoError` y el código lanza
**cinco** (más una sexta que llega como excepción ya traducida). Todas son
corrupción de verdad y todas son clasificables; lo que cambia con la lista
completa es que **ninguna otra forma del fichero queda sin cubrir por escrito**:

| # | Origen | Qué detecta | Sonda |
|---|---|---|---|
| 1 | `_vigilar_hojas` — **identidad** | `packs[clave].id != clave` | `L10` |
| 2 | `_vigilar_hojas` — **error de escritura** | Un campo de hoja a una pulsación (o con otra grafía) de una clave conocida | `L9` |
| 3 | `_read_json` — **las dos claves** | `packs` **y** `profiles` en el mismo fichero | `L7` |
| 4 | `_read_json` — **forma legacy** | `profiles` no es un mapa | `P3` |
| 5 | `_read_json` — **valor legacy** | un registro de `profiles` no es un mapa | `P3` |
| 6 | `_hoja_ilegible` — **traducción** | El `ValidationError` de `Pack` de una hoja legacy, traducido a una línea que nombra campo + pack + tipo real | `L2` |

**Por qué `AttributeError` NO está en la tupla (y por qué no se "arregla" añadiéndolo).**
Es un **síntoma**, no una clase de fallo. Antes de TASK-030, `{"profiles": "texto"` (o
`{"profiles": {"x": 123}}`) reventaba dentro de `_read_json` con
`AttributeError: 'str' object has no attribute 'items'`, y como no estaba en la tupla salía de
`PackService.__init__` **y la app no arrancaba**. La salida "ingenua" es ampliar la tupla con
`AttributeError`; está **rechazada** porque cualquier desreferencia a `None` dentro de
`_read_json` (o un `.get` sobre algo que cambió) se convertiría en "el archivo está roto" →
recuperación desde el `.bak` → y en el siguiente `save()` **los packs que el usuario acaba de
crear desaparecen**. Un bug de una línea se convierte así en pérdida de datos. La regla es:

> La **forma** se valida explícitamente y se lanza un error **propio** (`PerfilCorruptoError`);
> el **síntoma** se propaga para que se vea en el log.

`PerfilCorruptoError` hereda de `ValueError` (la rama legacy ya fallaba con un `ValueError` de
hecho, así que no cambia el tipo que ve quien llama) y **se define antes que la tupla**, porque la
tupla la referencia al construir el módulo.

### 4.2 Guarda de forma en la rama legacy (TASK-030)

`_read_json` valida **antes** de desreferenciar:

```python
perfiles = raw_data['profiles']
if not isinstance(perfiles, dict):
    raise PerfilCorruptoError(f"'profiles' deberia ser un mapa de perfiles y es {type(perfiles).__name__}")
...
for k, v in perfiles.items():
    if not isinstance(v, dict):
        raise PerfilCorruptoError(f"el perfil {k!r} deberia ser un mapa y es {type(v).__name__}")
```

El mensaje lleva el **tipo real**: sin eso, el diagnóstico de un fichero roto es
`AttributeError` genérico y no se distingue un `str` de un `int` de un `list`.

### 4.3 Lo que `load()` NO promete, y deuda conocida

- **No es un `load()` "a prueba de todo".** Un bug interno en `_read_json` sigue tumbando el
  arranque: es el precio de no perder configuración en silencio. El docstring de `load()` lo dice
  explícitamente para que nadie lo "arregle" ampliando la tupla.
- ~~**La ruta de regeneración escribe DOS veces.**~~ **DEUDA CERRADA por TASK-031 (E-3).**
  `load()` ya no escribe nada, así que la doble escritura (`_ensure_gaming_pack()` + un
  `self.save()` redundante) desapareció. Con ella desapareció la razón mecánica por la que
  ningún espía de llamadas podía discriminar: ahora la ruta es única y un test puede contar
  `save()` sin que el umbral sea arbitrario. La prohibición de contar llamadas que seguía
  vigente en `testing-guide.md` (ciclo #18) **queda anulada para `load()`**: la sonda `L3`
  cuenta invocaciones y además afirma sobre los **bytes**, que es la prueba real.
- **El pintado del aviso en la UI está pendiente.** `PackService.mensaje_danado()` existe y
  está probado, pero ninguna vista lo pinta todavía (`ui/**` fuera del alcance de TASK-031).
  Hasta que se cablee, la recuperación es observable **para el código y para el log**, no
  para el usuario.
- **Una RAÍZ mal escrita arranca con cero packs y SIN aviso (DEUDA ABIERTA, iteración 2,
  reaffirmada en la 3).** `{"perfiles": …}` no es corrupción (§4.4) y sus datos sobreviven
  a todos los guardados (sonda `L8`), pero el usuario ve una lista vacía y no tiene forma
  de saber que sus packs siguen en el fichero. Lo que **no** se puede hacer es clasificarla
  como corrupción: en la ruta sin `.bak` eso destruye los packs en el siguiente guardado
  (§4.6, motivo 2, medido). El arreglo correcto (un aviso que **no** cambia la
  clasificación) pertenece a otra tarea, porque el pintado del aviso en la UI sigue
  pendiente de cablear. Lo que sí está fijado con un test es el **coste**: `L8` afirma
  `fichero_danado is False`, así que cambiar la clasificación requiere cambiar el test a
  propósito.
- ~~**La raíz legacy perdía sus claves extra**~~ **DEUDA CERRADA en la iteración 3 (M8).**
  `AppData(packs=packs_dict)` se llevaba por detrás toda la raíz que no fuese
  `packs`/`profiles`, así que un `profiles.json` legacy con `favorite` en la raíz perdía ese
  dato en el primer `save()`, en silencio — y el `extra="allow"` de `AppData` no podía
  hacer nada, porque el extra no existía. Ahora la raíz se copia al `AppData` que se
  construye (§4.6). Sonda: `L11`. **Lo que NO lo arregla:** el precio de §4.3 sigue igual,
  porque una raíz que no se clasifica tampoco puede avisar por sí sola.
- Si `save()` falla, el temporal se limpia en su `except` y el error original se propaga sin
  enmascararse.

> **Corrección de la documentación heredada:** `tasks.json` marca TASK-011 (`auto-backup de
> perfiles al guardar`) como `completed`, `openspec/changes/2026-09-29-v3.1-quality-of-life/tasks.md:5`
> tiene el `[x]` puesto y `.taskmaster/CHANGELOG.md:91` afirma la "rotación segura de backups". **Ninguna
> de las tres era cierta**: no existía `shutil`, ni `.bak`, ni escritura atómica en `src/`. Es
> una feature documentada que nunca se escribió. Si alguna vez se cita TASK-011 como precedente,
> este es el commit que la implementa de verdad (TASK-026).

### 4.4 Hojas mal formadas: son CORRUPCIÓN (TASK-031, decisión de producto)

> **Criterio:** una hoja que viola el esquema es **corrupción** si y solo si el servicio **no
> puede representarla sin perder información**. Y en ese caso la recuperación tiene
> **prohibido** sobrescribir el `.bak` y **prohibido** destruir el principal si no hay nada
> con qué sustituirlo.

**Por qué corrupción y no "un pack válido con un campo raro".** La segunda opción no existe:
`Pack.keepers` es `List[str]` y Pydantic rechaza un `str`. Aceptarlo convertiría
`"steam.exe"` en `["s","t","e","a","m",".","e","x","e"]` y
`GamingService.should_kill_for_gaming` (`gaming_service.py:24`) dejaría de proteger **nada**.
La única forma de "cargarlo con lo que hay" es **normalizar a `[]`**, y eso no es cargar: es
**borrar**, en el primer `save()`, sin aviso.

**Y el borrado no es neutro: desarma el anti-brick.** `keepers` es la lista de **procesos
protegidos** del Gaming Mode (`gaming_service.py:16-24`). Un `profiles.json` editado a mano
con `"keepers": "steam.exe"` y normalizado a `[]` hace que "Preparar Gaming Mode" **mate lo
que debía proteger**: el brick que `SYSTEM_PROTECTED_PROCESSES` y la barrera de categoría
existen para impedir. La recuperación, en cambio, puede devolver una versión **distinta** de
la configuración: se pierde como mucho la última sesión de edición, de forma **visible y
diagnosticable**. Reversibilidad y visibilidad ganan a fidelidad: un keeper se reescribe en
diez segundos, un fichero borrado no se reconstruye.

**Las tres condiciones** que convierten una decisión discutible en un contrato:

1. **El mensaje nombra campo, pack y tipo real.** Un `ValidationError` crudo de Pydantic
   (14 líneas de diagnóstico interno más una URL a su documentación) **no cumple**: quien
   tiene que arreglar el fichero es el usuario, delante del bloc de notas. La rama legacy
   traduce el error a un `PerfilCorruptoError` de **una línea** con la forma
   `el pack 'mio' no se puede leer: el campo 'keepers' es str ('steam.exe')`. La rama
   moderna deja el `ValidationError` de Pydantic, que ya contiene `packs.mio.keepers` y
   `input_type=str` (sonda `L2`).
2. **La recuperación es observable.** §4, arriba: `fichero_danado` / `recuperado_de_backup` /
   `mensaje_danado()`. Sin esto, "corrupción" seguiría siendo silenciosa por otro camino.
3. **Si no hay `.bak` legible, NO se regenera a lo bruto.** El fichero se queda en disco
   (§4). La pérdida se vuelve **reversible**.

**La rama legacy deja de saltarse el modelo (E-2).** Antes construía el `Pack` con una lista
de campos escrita a mano (**5 de 8**), y los dos que faltaban eran `keepers` y
`target_categories`: la firma del defecto. Ahora traduce el registro a un `dict` moderno y se
lo pasa a `Pack` (`traducido["name"] = v.get("label", k)`, `traducido["id"] = k`, se pasa
`label → name` y se descarta `label`), de modo que **en cuanto `Pack` gane un campo, la rama
legacy lo empezará a leer sin que nadie se acuerde**. `ValidationError` ya estaba en
`CORRUPTION_ERRORS`: no se creó ninguna clase de error ni ninguna rama nueva. La rama
`__system_gaming__` se deja como está (es un preset fijo del producto, no dato del usuario).

**Dos decisiones de política, que NO son corrupción:**

- **Campo desconocido (`notas`): NO es corrupción.** Es el único mecanismo que hace el
  formato compatible hacia delante. Se conserva con `extra="allow"` (§2/§3): sobrevive al
  ciclo carga → guarda. Antes se **borraba en silencio** en el primer `save()`. Sonda: `L6`,
  que es la que **separa** "más `isinstance` campo a campo" de "validar contra el modelo".
- **Raíz desconocida (`perfiles`): NO es corrupción, y por una razón medida.** Sobrevive
  al `save()` gracias al `extra="allow"` de `AppData`; clasificarla destruiría los packs en
  la ruta sin `.bak` (ver el aviso de §2). Sonda: `L8`.
- **Clave raíz desconocida junto a un `packs` válido (`names`, `ids`, `favorite`): NO es
  corrupción tampoco**, y por la misma razón más una que es propia de la raíz: a una
  pulsación de un campo de hoja (`names`/`name`, `ids`/`id`) es un **dato de otro build**,
  no un error de escritura de hoja (§4.6). Sobrevive al `save()`. Sonda: `L12`.
- **`packs` **y** `profiles` en el mismo fichero: SÍ es corrupción**, y el mensaje nombra las
  dos claves. Antes la condición era `'packs' not in raw_data`, así que se iba a la rama
  moderna, `profiles` se ignoraba como clave extra y **los packs legacy desaparecían del
  disco** en el primer `save()` sin que nada se clasificara. Cualquier resolución (migrar o
  descartar) borra packs en silencio, así que aquí "corrupción" y "normalizar" cuestan lo
  mismo y gana la opción segura. Sonda: `L7`.

**Cómo se llega al fichero roto** (para no exagerar la severidad): ningún código de la app
puede escribir un `str` en `keepers` —`grep` de `src/`: solo se escriben listas—. La vía real
es un `profiles.json` **editado a mano** (§6 lo asume explícitamente), un `.bak` de otro
build, o un fichero truncado. La severidad **se mantiene** (la pérdida de `keepers` es un
brick), pero el escenario es ese.

### 4.5 Las DOS reglas del servicio (TASK-031 iteración 2): identidad y error de escritura

`Pack` es el dueño de los **tipos** y de los **enumerados** (E-2). `_vigilar_hojas()`
(`pack_service.py`) es el dueño de exactamente **dos** cosas más, y son reglas, no una
lista de campos: parten de `Pack.model_fields`, así que en cuanto `Pack` gane un campo las
cubren sin que nadie se acuerde (verificado con un campo inventado `ventilador`).

| Regla | Qué es corrupción | Por qué no se "normaliza" |
|---|---|---|
| **Identidad**: `packs[clave].id == clave` | `{"packs": {"mi-clave": {"id": "otro-id", …}}}` | Medido: se cargaba sin clasificar, `get_user_packs()` no lo enseñaba y `pack_manager_view.py:100` (que indexa `get_all_packs()[pack.id]`) reventaba con `KeyError('otro-id')`. Un pack que la app no puede ni abrir ni borrar. Normalizar a la clave reescribiría **en silencio** un campo que el usuario escribió a mano. |
| **Error de escritura**: un campo a **una pulsación** de distancia (`Levenshtein == 1`, más la variante con espacios o guiones) de una clave conocida **es corrupción**; cualquier otro campo desconocido se queda como extra y sobrevive | `"keeper"`, `"keeppers"`, `" keepers"`, `"app"`, `"is_favorit"`, `"default_actions"`, `"is_gamingg"` | Un `keeper` no es una ampliación del formato: es un campo del usuario escrito mal. Aceptarlo deja `keepers` en `[]` **y desarma el anti-brick en silencio** (`gaming_service.py:16-24`). Es el mismo ladrillo que §3.1 rechaza para una hoja mal formada, aquí con una hoja bien formada y **mal nombrada**. |

**Por qué esto NO es un filtro "fuzzy" que rechaza campos legítimos**: la lista es **cerrada**
(los campos que esta versión conoce) y el umbral es **una pulsación** (distancia de edición
1 sobre el nombre entero). Medido contra los 10 campos extra plausibles que usa la sonda
`L9` (`notas`, `note`, `color`, `tags`, `hotkey`, `version`, `keep`, `orden`, `emoji`,
`description`): ninguno colisiona, y el más cercano es `note` a distancia **2** de `name`.
Subir el umbral a 2 ya rechazaría un campo de verdad: la sonda `L9` incluye la lista
legítima por eso (mutación `L-M8f`).

> ⚠️ **"CERO falsos positivos" era una afirmación FALSA (iteración 3, P5).** Es lo que
> pasa con **esos 10 campos**, no lo que garantiza el filtro: `names` está a distancia
> **1** de `name` e `ids` a distancia **1** de `id`. Cualquier filtro de este tipo
> clasifica esos dos nombres como error de escritura, y la afirmación anterior
> (`_colision_de_tecla` included, que decía "CERO falsos positivos" con 18 campos que
> además no eran los de la sonda) no se sostiene. No es un defecto que se pueda
> arreglar subiendo el umbral: es la **definición** de "a una pulsación de una clave
> conocida". La solución es de **ámbito**, no de parámetro — y es §4.6: esta regla se
> aplica **solo a las hojas**.

Además hay un segundo camino, el de la **misma intención con otra grafía**
(`" keepers"`, `"is-favorite"`, `"IS-FAVORITE"`): se resuelve por **coincidencia exacta**
sobre la clave normalizada (minúsculas, sin espacios, `-` → `_`), antes que por
distancia. Sin esa normalización, `IS-FAVORITE` está a **11** de distancia de
`is_favorite` y `IS_GAMING` a **2**, y se colarían sin clasificar. Sonda: `L9`
(mutación `M13`, que convierte `_normalizar_clave` en la identidad).

Sondas: **`L9`** (error de escritura) y **`L10`** (identidad). `L9` afirma además que la
recuperación **devuelve los `keepers` reales** (`["steam.exe", "discord.exe"]`): elegir
"corrupción" solo vale si la protección vuelve, y no si se normaliza a `[]`.

### 4.6 La RAÍZ: qué se vigila y qué NO (TASK-031 iteración 3)

Las dos reglas de §4.5 son afirmaciones **sobre las hojas**, y `_vigilar_hojas()` recibe
el mapa de packs, nunca el objeto entero. **No hay una variante "para la raíz"**, y no es
una omisión: es una decisión medida, con su sonda (`L12`) y su código.

**Lo que NO se hace, y por qué (tres motivos, todos medidos):**

1. **La identidad no tiene sentido en la raíz.** No hay ningún `id` al que una clave raíz
   pueda ser distinta: la regla dice "la clave del mapa de packs **es** el id del pack", y
   la raíz no es un mapa de packs.
2. **El error de escritura en la raíz es pérdida de datos, no una molestia.** Clasificar una
   raíz mal escrita (`{"packs2": …}`, `{"profiless": …}`) hace que, en la ruta sin `.bak`,
   `load()` haga `self._data = AppData()` y el siguiente `save()` publique
   `{"packs": {"gaming": …}}`: los packs del usuario se pierden **igual** que sin
   clasificar, **y con un aviso de encima** (medido por `L8`, mutación `L-M8a`). En una
   hoja, aceptar un `keeper` deja `keepers` en `[]`; en la raíz, aceptar un `packs2` deja
   el fichero entero en manos de otro build.
3. **Además es falso positivo** (§4.5): `names` a distancia 1 de `name`, `ids` a distancia
   1 de `id`. Una clave raíz que se parece a un campo de hoja **no es un error de escritura
   de hoja**: es un dato raíz legítimo de un build que esta versión no conoce, y
   clasificarlo lo **borra** (misma ruta que el punto 2). En la hoja, en cambio, `name` y
   `names` conviviendo en el mismo registro **sí** es un error de escritura de verdad.

**Lo que sí se hace, y es un contrato de dos cláusulas:**

| Cláusula | Rama moderna | Rama legacy | Sonda |
|---|---|---|---|
| Una clave raíz desconocida **no se clasifica** | `AppData(**raw_data)` conserva la extra; no hay puerta | `_vigilar_hojas(perfiles, …)` mira solo las hojas | `L8`, `L12` |
| Una clave raíz desconocida **no se borra** en el ciclo carga → guarda | `extra="allow"` de `AppData` | la raíz se **copia** al `AppData` que se construye (menos `profiles`) | `L8` (moderna), **`L11`** (legacy) |

`L11` mide además el otro lado de la rama legacy: `profiles` **se descarta** al copiar,
porque su contenido ya está traducido en `packs` y conservarlo escribiría un fichero con
las dos claves, que la lectura siguiente clasifica como corrupción (`L7`). Por eso la
aserción de `L11` no es "la clave no aparece" (que un mutante cumpliría por casualidad)
sino **releer el fichero escrito** y afirmar que arranca limpio con los packs dentro.

**Las dos implementaciones plausibles de "vigilar la raíz" y qué sonda las mata.** No es
teoría: la matriz de mutación de la iteración 3 midió las dos, porque la primera redacción
de la matriz usó solo una y la otra pasó en verde.

| Mutante | Qué hace | Sonda que lo mata |
|---|---|---|
| `L-M8a` | "la raíz no tiene ninguna clave conocida ⇒ corrupción" | **`L8`** (muere) y **`L12`** (también muere, por la segunda mitad de `L12`) |
| `M9` | "una clave raíz que colisiona con un campo de hoja ⇒ corrupción" | **`L12`** (muere). **No** muere en `L8`, y no es un agujero: un filtro contra campos de *hoja* no ve `perfiles` (no se parece a ningún campo de `Pack`). Está medido y documentado en la matriz, no escondido. |

**Deuda que queda (no resuelta aquí, y declarada):** una raíz mal escrita arranca con
**cero packs y sin aviso** (§4.3). Arreglarlo exige un aviso que **no** cambie la
clasificación, y el pintado de avisos en la UI sigue pendiente de cablear.

### 5. Literal canónico de categoría sin clasificar (TASK-026 / FIX-005)

`⚪ Otros` (U+26AA WHITE CIRCLE) tiene **una sola fuente de verdad**:
`CATEGORY_ORDER[-1]` (`config.py:95`) y el default de `ProcessInfo.category` (`models.py:9`).
`process_service._DEFAULT_META[0]` y el `props.get('category', ...)` de `_load_local_db` deben
ser **idénticos**: un literal distinto saca el proceso de `CATEGORY_ORDER` y lo manda al
centinela `999` del sort, y rompe el filtro que lo excluye de `target_categories` en
`pack_manager_view.py`.

### 6. Respaldo preventivo (Backups) — ver §4
- `profiles.json.bak` es una **rotación de la versión anterior**, creada por `save()` antes de
  sobrescribir. Es lo que permite recuperar los packs del usuario tras un JSON corrupto; sin
  él, un apagón durante el guardado destruye irreversiblemente la única configuración que el
  usuario ha escrito a mano.
- Solo se rota cuando el principal **es legible para el servicio** (`_es_legible()`, §4
  punto 1). Por eso el `.bak` es de fiar **como copia sana**: nunca es el resultado de copiar
  un fichero que el servicio no sabe leer.
- **El arranque no rota nada** (TASK-031: `load()` es de solo lectura). Antes sí, y esa era
  la vía por la que el `.bak` sano moría en 7 de 8 escenarios de corrupción.

## Base de Datos de Procesos (`assets/process_db.json`)

### Esquema
`dict[str, dict]`. La clave es el **nombre del proceso en minúsculas y sin extensión**
(`chrome`, no `chrome.exe`) y el valor es un `dict` con exactamente tres campos:

```json
"powertoys": {
    "category": "🟢 Productividad",
    "priority": "high",
    "description": "PowerToys de Microsoft. Reconstruye unos 20 procesos al iniciar sesion..."
}
```

- `category`: tiene que existir **literalmente** (emoji incluido) como clave de
  `PROCESS_CATEGORIES` en `config.py`. Si no coincide, el lookup falla y el proceso cae en
  `? Otros` perdiendo su semáforo. Lo cubre `test_category_emoji_alignment` con un diff de
  conjuntos entre ambos ficheros.
- `priority`: `high` | `medium` | `low` | `none`. El semáforo visible lo manda la categoría
  (emoji 🔴/🟡/🟢); la prioridad solo desempata categorías desconocidas.

### Blindaje anti-brick (TASK-024)

Los procesos de nivel sistema cuyo cierre deja Windows inservible (`csrss`, `lsass`,
`winlogon`, `wininit`, `services`, `smss`, `dwm`, `System`, `Registry`, `fontdrvhost`,
`audiodg`, `RuntimeBroker`…) **no pueden ofrecerse nunca como cerrables**, ni siquiera si
alguien los registra por error en el JSON.

- Lista canónica: `SYSTEM_PROTECTED_PROCESSES` (un `frozenset`) en
  `src/woptimizer/services/process_service.py`. Coincidencia **exacta** sobre el nombre
  normalizado (`_normalizar_nombre`: minúsculas, sin `.exe`), nunca por subcadena: el
  matching del servicio acepta subcadenas y un nombre genérico bloquearía procesos
  legítimos. No confundir con los `patterns` legacy de `PROCESS_CATEGORIES['🔴 Sistema de
  Windows']`, que incluyen procesos del usuario (`taskmgr`, `cmd`, `powershell`, `wsl`).
- Se comprueba en **tres puntos**, todos antes de tocar el sistema operativo:
  1. `_load_local_db()` sanea el hashmap al cargar: una entrada de la Familia A se fuerza a
     `("🔴 Sistema de Windows", "none", ...)` aunque el JSON diga `🟢/high`.
  2. `_get_process_meta()` la consulta **antes** que la DB y que el fuzzy match, así que un
     proceso de sistema no puede heredar la categoría de otro patrón.
  3. `kill_processes()` y `kill_pack_apps()` la comprueban sobre el PID/nombre recibido: un
     pack escrito a mano con `lsass.exe` se cuenta como `skipped` y no mata nada.
- Cobertura: `test_no_system_process_is_killable` en `run_tests.py` falla si (a) alguien
  degrada una entrada de la Familia A a cerrable en el JSON, (b) la lista de protección deja
  de cubrir el núcleo duro, o (c) el blindaje deja de forzar 🔴/`none` con un JSON
  envenenado a propósito.

### Qué entra y qué no
- **Sí**: bloatware y telemetría de terceros (PowerToys, procesos de consumo de Armoury Crate,
  mejoras de audio, language servers, actualizadores de drivers). Van a `🟢 Productividad`
  (`high`) o `🟡 Media y Streaming` (`medium`) cuando tocan la ruta de audio.
- **No**: el entorno de trabajo del usuario (`pwsh`, `python`, `wsl`, terminales) — cerrarlos
  rompería su propia sesión; y las pilas de control de hardware (`armsvc`, `asus_framework`,
  `rogliveservice`) van a `🔴 Overlays e Info` / `none`, igual que `icue`, `razer` o `lghub`,
  porque cerrarlas deja el equipo sin perfil de ventilación o RGB.

