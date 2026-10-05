# La app pierde los packs del usuario entre versiones

**Change ID:** `2026-10-05-perdida-de-packs-entre-versiones`
**Área:** Servicios / persistencia
**Origen:** `TASK-069` (`pending`, `high`, complejidad `high`), fila 🔴 de `STATUS.md:116` y
**REPORTADO por el dueño el 2026-10-05**, no un hallazgo de agente.

**Estado:** PLAN. `HEAD 375ff45` en `beta`, `validate_docs.py` en 129 OK / 0 FAIL, suite en
**159** = **112 backend + 47 headless** (medido en la pasada anterior, no remedido aquí).

> **Regla del turno: cero ediciones bajo `src/`.** Este documento es la especificación; el
> código es del Paso 3 (`openspec-dev`).

---

## 1. El diagnóstico: tres hipótesis, una gana y dos se descartan con medición

El encargo nombraba tres diagnósticos y decía —correctamente— que **arreglar el equivocado es
peor que no arreglar nada**. Los tres se han medido contra los ficheros de este host.

### 1.1 (a) MIGRACIÓN DE FORMA DEL FICHERO — **DESCARTADO**

Los **tres** `profiles.json` vivos de esta máquina usan la forma moderna
`{"packs": {<id>: <Pack>}}`, que es exactamente la que declara `AppData`
(`models.py:99`, `packs: Dict[str, Pack]`), la que construye `_read_json()` y la que consume el
`save()` de `pack_service.py:560` (`json.dump(self._data.model_dump(), …)`). No hay ni una
instancia de la forma legacy en producción.

La única forma legacy `{"profiles": …, "favorite": …}` está en
`docs/archive/legacy-root-data/profiles.json` (420 B, 2026-09-26), **archivada** por TASK-028, y
ya tiene guard: `run_tests.py:6626-6671` afirma que el fichero de la **ruta viva** no es el v2
retirado. Es decir: la migración de forma **funciona y está vigilada**, y no es la causa.

### 1.2 (b) INSTALACIÓN EN PARALELO — **DESCARTADO, con una medición que lo dice**

`setup_logging()` (`config.py:38-60`) construye un `RotatingFileHandler` **sin `delay`**, o sea
que **arrancar la app crea el fichero de log aunque no haya ni un solo aviso**. Eso convierte el
log en un testigo de arranque fiable, y por eso se puede medir si el ejecutable descargado hoy se
ha ejecutado alguna vez:

| Fichero | Bytes | mtime | Lectura |
|---|---|---|---|
| `C:\Users\carch\Downloads\woptimizer.exe` | 25.689.614 | **2026-10-05 09:29** | la 1.1.0, **descargada hoy** |
| `C:\Users\carch\Downloads\woptimizer.log` | **0** | **2026-10-03 16:00** | **creado por un arranque, nunca escrito** |
| `C:\Users\carch\Downloads\profiles.json` | 1.205 | 2026-10-03 16:01 | datos de la 1.0.0 |
| `C:\Users\carch\Downloads\profiles.json.bak` | 1.301 | 2026-10-03 16:01 | rotación de la 1.0.0 |

El log de `Downloads` **sigue con la marca del 10-03**. Si el `.exe` de las 09:29 se hubiera
ejecutado, `config.py:48-53` habría reabierto ese fichero y le habría puesto la marca de hoy. No lo
tiene. **La 1.1.0 descargada no se ha ejecutado ni una vez.**

Y los dos ejecutables son binarios distintos, no la misma imagen en dos carpetas:
`f15a069dcfbfa921…` (25.689.614 B, 10-05 09:29, en `Downloads`) contra `43be1cce4f21b71b…`
(27.040.542 B, 10-03 04:49, en `dist/`), **1,35 MB de diferencia**.

Cronología reconstruida, toda con marca de tiempo:

| Cuándo | Qué | Testigo |
|---|---|---|
| 2026-10-03 00:47 | sesión de **desarrollo** (`run.py`) | `src/woptimizer/profiles.json` |
| 2026-10-03 04:49 | se compila el build de trabajo | `dist/woptimizer.exe` (27.040.542 B) |
| 2026-10-03 16:00 | **arranque de la 1.0.0 desde `C:\Users\carch\Downloads\`** | `Downloads\woptimizer.log` (0 B, creado) |
| 2026-10-03 16:01 | la 1.0.0 guarda el pack `8fefbc22` "sync" | `Downloads\profiles.json` + `.bak` |
| 2026-10-05 09:29 | **descarga** de la 1.1.0 a `Downloads` | `Downloads\woptimizer.exe` |
| 2026-10-05 09:30-09:31 | **arranque del build de `dist/`** | `dist\woptimizer.log` (sus únicas marcas: 09:31:05 y 09:31:07), `dist\profiles.json`, `dist\profiles.json.bak` |

**No hubo dos instalaciones: hubo dos carpetas.** La 1.0.0 del dueño vivía (y vive) en
`C:\Users\carch\Downloads\`; la 1.1.0 se ha probado desde `…\woptimizer\dist\`. Son rutas
distintas, y por eso son bases de packs distintas.

### 1.3 (c) RUTA DE DATOS ATADA AL DIRECTORIO DEL EJECUTABLE — **CONFIRMADO**

Y no es un evento: es un **estado estacionario**. La causa es `config.py:5-9`:

```python
def _app_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))
```

`_app_dir()` es la raíz de **`profiles.json`** (`config.py:82`), de **`saved_processes.json`**
(`config.py:67`) y del **log** (`config.py:49`). Congelado, significa **al lado del `.exe`**.
Medido: en este host hay **cuatro** `profiles.json` con datos y el mismo concepto de pack —"sync"—
tiene **tres UUID distintos**:

| # | Ruta | B | mtime | gaming (tc / keepers) | Pack de usuario |
|---|---|---|---|---|---|
| 1 | `C:\Users\carch\Downloads\profiles.json` | 1.205 | 10-03 16:01 | 5 / 2 | `8fefbc22` "sync" — **3 apps absolutas** |
| 2 | `…\woptimizer\dist\profiles.json` | 898 | **10-05 09:31** | **2 / 0** | `4a74a322` "sync" — **0 apps**, 1 `start_category` |
| 3 | `…\woptimizer\src\woptimizer\profiles.json` | 1.309 | 10-03 00:47 | 5 / 2 | `7559c83a` "SYNC" — **4 apps absolutas** |
| 4 | `…\woptimizer\docs\archive\legacy-root-data\profiles.json` | 420 | 09-26 12:44 | — | forma legacy, archivada en TASK-028 |

Las apps absolutas del pack del dueño (`Downloads\profiles.json:42-46`): `GoogleDriveFS.exe`,
`nextcloud.exe`, `OneDrive.exe`. Es el historial real de 50 sincronizadores que el dueño fue
seleccionando uno por uno.

**La medición que lo distingue de (a) y de (b), en una frase:** los tres ficheros tienen la
misma forma y cargan bien, luego no hay migración; el `.exe` nuevo no ha corrido, luego no hay
instalación paralela; y **lo que cambia entre ellos no es el contenido sino el directorio desde
el que se arrancó**, luego es la ruta.

**Lo que NO se puede afirmar, y hay que declarar:** cuál de las tres bases es la que el dueño vio
"perdida". Eso no lo dice ningún fichero, lo dice él, y es una línea. **El plan no depende de esa
respuesta** —los tres diagnósticos convergen en el mismo arreglo— y **T-1 existe precisamente
para que la app se lo pregunte al usuario con una ruta en la mano** en vez de quedarse muda.

### 1.4 Lo que el encargo temía y es **peor** de lo que pensaba

El briefing dice: *"si los datos de `gaming` desaparecen, el invariante 'el pack gaming está
protegido' se queda sin pack"*. **Es falso**, y la verdad es más grave.

`_ensure_gaming_pack()` (`pack_service.py:570-591`) **no deja al gaming ausente**: si no está, lo
repone con `DEFAULT_GAMING_PACK.model_copy(deep=True)` (`pack_service.py:588`), y ese default es
(`pack_service.py:231-240`):

- `apps=["chrome.exe"]`
- `keepers=["steam.exe", "discord.exe"]` ← **la lista anti-brick de TASK-023/030**
- `target_categories` = **cinco**: 🟢 Sincronización, 🟢 Navegadores, 🟢 Productividad,
  🟡 Chat y Comunicación, 🟡 Launchers Gaming
- `default_action="kill"`

Y el pack reponido **se persiste en el primer `save()` real** (`pack_service.py:574-576`), sin
avisar. El gaming que el dueño tiene en `dist\profiles.json` tiene `keepers: []` y **2**
categorías. Si ese fichero se pierde:

> **La pérdida de datos no se traduce en "packs vacíos": se traduce en un Gaming Mode MÁS
> agresivo y en la desaparición de la lista de keepers que protege `steam` y `discord`.** Cinco
> categorías donde el usuario escogió dos, y una lista anti-brick que el código cree puesta y no
> lo está. Sin un solo aviso.

Es un modo de fallo de **seguridad**, no de molestia, y por eso va en **T-4**, con su propio
criterio de aceptación y no como nota al pie de la migración.

---

## 2. Decisión: adónde van los datos

### 2.1 Lo que se descarta y por qué

| Opción | Por qué no |
|---|---|
| **Seguir al lado del `.exe`** | Es la causa. Un destino que se mueve con el binario pierde los datos cada vez que el binario se mueve, y esta app vive en un repo sincronizado por Nextcloud con un `dist/` dentro. |
| **Buscar en una lista de candidatos en cada arranque** | No cierra nada: dos rutas que se leen es dos bases que se divergent. El síntoma se repite cada vez que el usuario cambia de carpeta. Solo sirve **una vez**, como paso previo a la migración (T-1). |
| **`%LOCALAPPDATA%`** | Sirve, pero `%APPDATA%` es la sede canónica de "configuración de usuario que no es caché" y **ya está en la lista de raíces permitidas** de la política de arranque (`architecture.md` §14, regla 7: `%APPDATA%` entre las seis). No abre ninguna raíz nueva. |

### 2.2 La decisión

> **Destino único: `%APPDATA%\woptimizer\profiles.json`, con override por variable de entorno
> para poder testearlo. La migración es una COPIA, nunca un traslado, y el origen se queda donde
> está.**

Tres razones, en orden de peso:

1. **Es la única que hace imposible que la pérdida se repita.** Con un destino estable, el
   problema deja de ser un bug recurrente y pasa a ser un incidente único de migración.
2. **Es la que Windows garantiza.** `%APPDATA%` sobrevive a reinstalar el `.exe`, a moverlo, a
   volver a descargarlo y a cambiar de carpeta. La 1.1.0 de `Downloads` habría encontrado los
   datos de la 1.0.0 aunque el ejecutable estuviera en `D:\`.
3. **Es lo que hace el dato recuperable sin ayuda.** Con el destino actual, recuperar un pack
   significa que el usuario sepa en qué carpeta está el `.exe` viejo. Con `%APPDATA%`, significa
   copiar un fichero.

**El coste honesto, declarado:** un usuario que ya tiene `profiles.json` al lado del `.exe` **tiene
que arrancar una vez con la build nueva** para que sus datos lleguen al destino. Si esa migración
falla, no ve nada hasta que se resuelva. De ahí las tres condiciones de §3.

### 2.3 La restricción dura, y cómo se cumple

> **MOVER DATOS DE USUARIO SIN COPIA ES IRREVERSIBLE.** Un fallo a mitad de una migración destruye
> lo que el usuario tenía, que es exactamente lo que esta tarea denuncia.

La migración se especifica con **cuatro** condiciones, y la cuarta es la que la hace reversible:

1. **Nunca `move`, nunca `os.replace`, nunca `unlink`.** `shutil.copy2` —que preserva el mtime—,
   y **el origen se queda donde está**. Precedente en el propio repo: `_rotate_backup()`
   (`pack_service.py:546`) ya usa `shutil.copy2` para el caso hermano de la rotación del `.bak`.
2. **Destino primero, y solo si el destino se relee.** Se copia, se reabre el destino, se parsea
   con el **mismo `_read_json()`** que usa el resto del servicio, y se comparan los ids y el
   número de packs. Si la relectura falla o no cuadra, **no se borra nada** y se avisa.
3. **El origen intacto es un criterio, no una intención.** Se comprueba con `sha256` del origen
   **antes y después**, y también del `.bak` del origen. Sin esa fila, un `shutil.move`
   disfrazado de migración pasa el suite entero.
4. **Reversión:** con el destino ilegible, la resolución **cae al origen** y devuelve los mismos
   packs, con `fichero_danado` observable. Es la respuesta al "y si la migración se corrompe a
   mitad", y es la prueba que la tarea pide explícitamente.

---

## 3. Primer paso sin riesgo: T-1, el diagnóstico que no toca un dato

**Hoy, cuando la app no encuentra `profiles.json`, no dice absolutamente nada.** Y la ausencia es
precisamente el caso de esta tarea:

- `load()` es de **solo lectura** por diseño (`architecture.md` §13, regla 2), correcto para una
  instalación limpia.
- `fichero_danado` / `recuperado_de_backup` / `motivo_danado` (`pack_service.py:249-251`) y
  `mensaje_danado()` (`pack_service.py:605`) solo se activan con **corrupción**
  (`pack_service.py:314-325`), nunca con **ausencia** (`pack_service.py:311`).

O sea: "el usuario perdió sus packs" es hoy **indistinguible de "instalación limpia"**. Eso es
el diseño correcto para la segunda y el peor para la primera, y es la mitad del daño.

**T-1 no escribe nada y no mueve nada:** al arrancar, si el destino no existe, se mira el
candidato (`dirname(sys.executable)` y, en desarrollo, `src/woptimizer`) y **si hay datos ahí se
dice la ruta**: *"No encuentro tus packs en `<destino>`. Hay packs en `<candidato>`"*, en el
`status_label` que ya existe vía `motivo_danado`, y en el log.

**Cuánto valor da, y su límite honesto:** convierte *"perdidos"* en *"están aquí"*, que es la
mitad del valor con **0% de riesgo**. **No** los recupera: el usuario tiene que actuar. Y su
limite real es que **no arregla nada del gaming**, que es la mitad gravísima de §1.4.

**Por qué T-1 tiene que ir PRIMERO, y no es por el valor:** porque es **el instrumento de
medición** de T-3. La migración necesita saber qué candidatos existen; el diagnóstico es esa misma
búsqueda, expuesta. Y porque si se empieza por la ruta sin T-1, hay un caso en que la migración no
encuentra nada (el usuario cuya 1.0.0 estaba en una carpeta ya borrada), la app **arranca igual de
vacía y de muda** que hoy, solo que con el log en otro sitio: **el síntoma no mejora nada** y el
dueño sigue pensando que perdió sus datos.

---

## 4. Orden y agrupamiento

| Sub | Qué | Riesgo de datos |
|---|---|---|
| **T-1** | Diagnóstico honesto: nombrar el candidato sin escribir | **cero** |
| **T-2** | Destino estable en `%APPDATA%` + los dos tests de ruta | **alto** |
| **T-3** | Migración con copia, relectura y reversión | **alto** |
| **T-4** | El gaming no se repone en silencio | **medio** |
| **T-5** | Contrato documentado y guard de no-recaída | **cero** |

**Orden: T-1 → (T-2 + T-3) → T-4 → T-5.**

**T-2 y T-3 son una sola unidad de entrega, y esta es la invariante más importante del plan:**
cambiar la ruta **sin** migrar deja al usuario **sin packs de forma definitiva**, que es peor que
hoy. La ruta nueva y la migración se entregan juntas o no se entregan.

**A diferencia de CYCLE-054, este ciclo SÍ mueve el recuento de tests.** El check 7 de
`validate_docs.py` deriva el reparto con `ast`, luego hay que actualizar los cuatro declarantes
(`STATUS.md`, `AGENTS.md`, `README.md` y la tabla 1..159 de `docs/ai/testing-guide.md`). Se dice
aquí para que no salga como sorpresa en el Paso 3.

### Fuera de alcance, y por qué

- **`PROCESS_LIST_FILE` y `saved_processes.json`.** MEDIDO: la única coincidencia de
  `PROCESS_LIST_FILE` en `src/` es **su propia definición** en `config.py:67`. Los tres
  "consumidores" que cita el comentario de `config.py:68-70` son los `test_*.py` heredados de la
  raíz que **TASK-021 declaró muertos** por importar `process_manager`, que no existe. El
  `saved_processes.json` de 37 KB con 50 procesos (2026-09-14, en la raíz del repo) **no lo lee
  nadie**. Peor: `run_tests.py:6965-6975` lo **ancla por texto**
  (`PROCESS_LIST_FILE == join(_app_dir(), "saved_processes.json")`), luego tocarlo **rompe** un
  test sin ganar nada. Es un ticket propio, no esta tarea.
- **El log se queda junto al `.exe`.** Es diagnóstico *de esta* instalación y es lo que permite
  que T-1 diga "están aquí" y que el usuario mande el log si algo falla. Solo lo que el usuario
  *ha creado* (packs) cambia de sitio.
- **`TASK-068`.** Es el otro bug —el de las categorías— y es una decisión de producto que el
  dueño tiene que tomar antes. Se deja como está.
- **La calidad de `build/` y `basura/`.** No se toca nada de `dist/` ni de `basura/`.

---

## 5. Lo que este ciclo NO puede hacer, y hay que decirlo al dueño

1. **No sabe cuál de las tres bases es la buena.** El plan **conserva las tres**: la migración
   copia, no mueve, y nada borra. Recuperar el pack `8fefbc22` de `Downloads` es una operación
   manual que el dueño puede hacer cuando quiera, y T-5 deja la instrucción escrita.
2. **La 1.1.0 de `Downloads` no se ha probado.** Se ha **descargado** nada más. Cuando se ejecute
   desde `Downloads` verá los 3 packs de `Downloads\profiles.json`; cuando se ejecute desde
   `dist/` verá los de `dist\profiles.json`. Los de `src\woptimizer\` (4 apps, incluido
   `OneDrive.Sync.Service.exe`) no los ve nadie más que el modo desarrollo.
3. **No repara el gaming de `dist\`** con 2 categorías y `keepers: []`: reponer el de fábrica es
   justo el daño de §1.4. T-4 impide que se reponga **en silencio**, no que se reponga.
