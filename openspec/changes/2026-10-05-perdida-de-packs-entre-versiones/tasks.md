# Tareas — la pérdida de packs entre versiones (TASK-069)

Cinco subtareas. **T-1** solo diagnostica (riesgo cero), **T-2 + T-3** son una sola unidad de
entrega (cambiar la ruta sin migrar es peor que hoy), **T-4** cierra el modo de fallo de
seguridad, **T-5** escribe el contrato y su guard.

---

## T-1 · El diagnóstico que no toca un dato

**Qué:** al arrancar, si el destino de datos no existe, mirar el **candidato**
(`dirname(sys.executable)` congelado; `src/woptimizer` en desarrollo) y, **si ahí hay un fichero
legible**, decir la ruta: *"No encuentro tus packs en `<destino>`. Hay packs en `<candidato>`"*, en
el `status_label` que ya existe y en el log. **No escribe, no copia, no mueve, no borra.**

**Por qué primero:** es el instrumento de T-3 (la misma búsqueda, expuesta), y sin él un usuario
cuyo 1.0.0 estaba en una carpeta ya borrada seguiría viendo una app muda con el log en otro
sitio: **el síntoma no mejora nada**.

**Cierre:**

- Una función **pura y sin E/S de escritura** que dada una ruta de destino y una lista de
  candidatos devuelve `(destino_elegido, candidatos_con_datos)`. Pobre en sí, la función se
  prueba sin disco.
- `PackService` gana un atributo observable del caso **ausencia** (hoy `fichero_danado` /
  `recuperado_de_backup` / `motivo_danado`, `pack_service.py:249-251`, solo cubren **corrupción**,
  `pack_service.py:314-325`) y `mensaje_danado()` (`pack_service.py:605`) lo nombra.
- **TEST QUE DISCRIMINA (avisa):** destino inexistente + candidato con un `profiles.json` vago
  ⇒ el mensaje contiene **las dos rutas** y el estado de ausencia es observable. **Por qué
  muere sin el fix:** hoy `load()` con `os.path.exists == False` (`pack_service.py:311`) salta
  todo el bloque de corrupción, no toca ningún atributo y `mensaje_danado()` devuelve `None`; el
  test recibe `None` y falla en la primera aserción.
- **CONTRAPROUEBA (no se overboard):** destino inexistente + **ningún** candidato con datos ⇒
  `mensaje_danado()` es `None`. Mata el mutante `SIEMPRE_AVISAR`, con el que una instalación
  limpia, que es el caso legítimo y mayoritario, avisa de un problema que no tiene.
- **CONTRAPROUEBA (no toca datos):** el fichero del candidato tiene el **mismo `sha256`** antes y
  después de arrancar el servicio, y `os.listdir(candidato)` tiene el mismo número de entradas.
  Mata el mutante `AVISAR_Y_NORMALIZAR` (escribir el `.json` para "asegurarse de que se lee").
- El log nombra el candidato con su ruta absoluta, y `logger.warning` no se traga nada.

---

## T-2 · Destino estable: `%APPDATA%\woptimizer\profiles.json`

**Qué:** en `config.py`, una función de resolución del directorio de datos con override por
variable de entorno, y `PROFILES_FILE` sale de ahí en vez de `_app_dir()`. El **log se queda**
junto al `.exe` (§4 del proposal).

**Los dos tests que no pueden pasar por coincidencia de rutas en ESTA máquina — el requisito
explícito del encargo:**

- **TEST 1 (la ruta no sigue al ejecutable).** Con `sys.frozen` simulado a `True` y
  `sys.executable` apuntado a `<temp>\A\woptimizer.exe`, se resuelve la ruta de datos; después se
  apunta a `<temp>\B\woptimizer.exe` y se vuelve a resolver. **Las dos tienen que ser iguales.**
  **Por qué muere sin el fix:** con `config.py:5-9` la primera devuelve `<temp>\A` y la segunda
  `<temp>\B`; son distintas, luego la aserción falla. Ese aserto **es** el bug, escrito.
- **TEST 2 (pertenencia al destino forzado).** Se fuerzan `%APPDATA%` y `%LOCALAPPDATA%` a un
  `tempfile.mkdtemp()` **antes de importar**, y se exige que la ruta devuelta **esté dentro de ese
  temporal**. **Por qué no puede pasar por coincidencia:** el destino esperado lo decide el test,
  no el host, y `mkdtemp()` es único por corrida. Hoy la función devuelve `<temp>\A`, que está
  **fuera** del temporal forzado, y falla.
- **Los dos se apoyan en un mismo par de exe falsos**, para que ninguna de las dos filas dependa
  de la otra. Y `mkdtemp` se limpia en `finally`.
- **La cámara no toca este host.** `.git` en esta máquina es un **fichero de 57 bytes** con
  `gitdir: C:/Users/carch/AppData/Local/woptimizer_git/.git` (medido), y `robocopy /XD .git` **no**
  lo excluye. La sonda **no copia el repo**: construye un árbol mínimo en `%TEMP%` e **importa**
  `woptimizer.config`. Con eso no puede alcanzar `.git` ni por accidente.

**Cierre:**

- `PROFILES_FILE` sale del resolvedor nuevo y el test `run_tests.py:6643-6649`, que hoy afirma
  `PROFILES_FILE == join(_app_dir(), "profiles.json")`, **se actualiza a la propiedad nueva**
  (mismo destino con dos ejecutables distintos), no se borra. Ese test es el ancla del contrato
  viejo: dejarlo como está sería dejar la regla diciendo lo contrario de lo que hace el código.
- El override por entorno tiene el mismo nombre en el test y en el código, y **sin** él no hay
  forma de probar nada sin `%APPDATA%` de verdad.
- `docs/ai/architecture.md` §13 y `docs/ai/data-models.md` §4.4 dejan de decir "junto al
  ejecutable" — T-5 lo cierra con un guard.

---

## T-3 · Migración: copia, relectura y **prueba de reversión**

**Qué:** en el primer arranque, si el destino **no** existe y hay un candidato con fichero
legible: `shutil.copy2` (nunca `move`, nunca `os.replace`, nunca `unlink`), reabrir el destino,
parsearlo con el **mismo `_read_json()`** del servicio, comparar ids y número de packs, y
**dejar el origen intacto**. Si la relectura falla o no cuadra: no se borra nada y se avisa.

**Cierre — y aquí está la prueba de reversión que la tarea pide:**

- **TEST DE MIGRACIÓN:** origen en `<temp>\legacy\profiles.json` con la **forma real de la 1.0.0**
  (la que se midió en `C:\Users\carch\Downloads\profiles.json`: `gaming` + `8fefbc22` "sync" con
  3 apps absolutas y su `default_action`), destino forzado a `<temp>\datos`. Tras migrar: los ids
  y las apps coinciden, **el Gaming Mode conserva sus 5 `target_categories` y sus 2 `keepers`**,
  y el origen **sigue ahí**.
- **LA FILA QUE MATA LA IRREVERSIBILIDAD:** el `sha256` del **origen** y el de su `.bak` son
  **idénticos antes y después**. **Por qué discrimina:** con el mutante `shutil.move` en vez de
  `copy2` el origen ya no existe, el `sha256` no se puede leer y la fila muere. Un "migró bien"
  FALSO pasa cualquier otro aserto de este test.
- **LA PRUEBA DE REVERSIÓN (explícita, y es un test aparte):** con el destino ya poblado, se lo
  **corrompe a propósito**, se vuelve a resolver y se exige que la resolución **cae al origen** y
  devuelve los mismos packs, con el estado de corrupción observable. **Por qué hace falta
  separada:** sin ella, la mitad de "copió y se olvidó" y la mitad real de "sabe volver
  atrás" dan el mismo veredicto.
- **CONTRAPROUEBA (no toca la casa):** el test **no escribe jamás** en `C:\Users\carch\Downloads`,
  en `dist/`, en la raíz del repo ni en `%APPDATA%`/`%LOCALAPPDATA%` reales. Todo con
  `tempfile.mkdtemp()` y variables de entorno forzadas, y `finally` que limpia. **Por qué
  discrimina:** con el mutante `SIN_OVERRIDE_ENTORNO` el test escribiría en el `%APPDATA%` de
  este host y, en el peor caso, sobre el `profiles.json` del dueño; el guard de hermeticidad
  (ningún path de la operación empieza por `%APPDATA%`/`%LOCALAPPDATA%` sin el temporal) lo mata.
- La rotación del `.bak` sigue decidiéndose por `_es_legible()` (`pack_service.py:504-524`); la
  migración **no** lo usa como criterio y **no** lo pisa.

---

## T-4 · El gaming no se repone en silencio

**Qué:** `_ensure_gaming_pack()` (`pack_service.py:570-591`) convierte hoy "no está" en "está el
de fábrica" **sin dejar rastro**, y el de fábrica tiene **cinco** `target_categories` y **dos**
`keepers` (`pack_service.py:231-240`). La pérdida de datos se traduce en un Gaming Mode **más
agresivo** y en una lista anti-brick que el código **cree puesta y no lo está**.

**Decisión de producto que hay que tomar antes de escribir la línea** (y que por eso va
explícitamente en la descripción de la tarea, igual que en `TASK-068`): reponer el gaming
silenciosamente es **incorrecto**, pero **dejar al usuario sin Gaming Mode** también. La propuesta
es reponerlo **declarándolo** en `mensaje_danado()` y en el log, con la lista de lo repuesto
(`"el pack Gaming se ha repuesto por el de fábrica: 5 categorías y los keepers steam/discord"`), y
que el primer `save()` real lo persista como hoy. **Alternativa a discutir con el dueño:** que la
UI muestre el pack repuesto en un color de aviso en vez de en la Portada como uno más.

**Cierre:**

- **TEST QUE DISCRIMINA (la fila que importa):** un `profiles.json` **sin** `gaming` se resuelve y
  el estado de reposición es observable; y el **mensaje nombra las 5 categorías y los 2
  keepers** repuestos. **Por qué muere sin el fix:** hoy `pack_service.py:588` inserta
  `DEFAULT_GAMING_PACK.model_copy(deep=True)` sin tocar ningún atributo, así que el mensaje es
  `None` y el test falla.
- **LA FILA DE SEGURIDAD, que es la que no es de UX:** con el gaming del usuario (2 categorías,
  `keepers: []`) perdido, el test exige que **la lista de keepers efectiva no crezca sola**. Hoy
  pasa de `[]` a `["steam.exe", "discord.exe"]` sin que nadie lo decida, y ese es el daño
  anti-brick. **Por qué discrimina:** con el fix de la reposición declarada el valor sigue siendo
  el del default, luego la fila tiene que exigir **que la diferencia sea visible y no un efecto
  secundario**, no que el valor sea el antiguo (eso sería inventar una función que no existe y que
  no se ha pedido).
- `reset_gaming_pack()` (`pack_service.py:636-640`) y "Restaurar por defecto" siguen siendo
  **explícitos** y los únicos que cambian el gaming a propósito: si T-4 los toca, es un abuso.

---

## T-5 · Contrato escrito y guard de no-recaída

**Qué:** `docs/ai/architecture.md` (§13, invariante 13) y `docs/ai/data-models.md` (§4.4, y el
§4.4 que `models.py:29-30` ya cita) dejan de describir la persistencia como "junto al
ejecutable" y describen el destino, la migración y su **reversión**. Y una sonda que viga que el
documento no vuelve a prometer lo viejo.

**Cierre:**

- El documento dice `%APPDATA%\woptimizer`, dice que la migración es una **copia**, y dice que el
  origen **se queda**. Con la fecha, porque es una cifra de contrato.
- **TEST QUE DISCRIMINA:** una mutación de la copia del documento (volver a "junto al ejecutable")
  produce FAIL. **Por qué discrimina:** el guard muere por **contenido**, no por el nombre del
  fichero, que es exactamente el fallo que el `mutation-auditor` de `TASK-067` acaba de cerrar en
  el agregado `llms-full.txt` (guard por nombre, `validate_docs.py:2153`, y el contenido se
  caducaba al 57,9 %). Con el guard por nombre el documento puede mentir entero y la sonda
  sigue verde.
- `docs/known-issues.md` gana la trampa: **dos `woptimizer.exe` en el host, tres bases de packs,
  un solo dato**. Con su medición, y **con la fecha**, porque los ficheros se mueven.
- `STATUS.md` fila 116 pasa a decir qué se hizo, con la misma regla de las tres cifras.
- `validate_docs.py` en 0 FAIL, `build_llms_full.py --check` en 0 (el agregado incluye
  `docs/ai/`, luego este cambio lo toca), `verify_ui_syntax.py` en exito, `run_tests.py` en verde
  **con los cuatro declarantes actualizados**.

---

## Verificación de cierre del ciclo

- `run_tests.py` en verde, y **el recuento actualizado en los cuatro declarantes** porque este
  ciclo **sí** añade `test_*()`: el check 7 de `validate_docs.py` deriva el reparto con `ast`, y
  cualquier `test_*()` nuevo se ve ahí. No es un ciclo de andamiaje, es el guard que ya existe.
- **Paso 4 obligatorio (`mutation-auditor`), tres mutantes que tienen que morir:**
  `MOVE_EN_VEZ_DE_COPY` (mata la fila del `sha256` del origen), `RUTA_SIGUE_AL_EXE` (mata el
  TEST 1 de T-2), `REPOSICION_SILENCIOSA` (mata la fila de T-4). Los tres, por aserción
  concreta.
- `sync_agents.py --check` en 0, `git_safe_commit.py` **intacto**, y `LIMITE_CABECERA = 120` sin
  relajar.
- **Cero escrituras** bajo `src/woptimizer/` fuera de `config.py` y
  `services/pack_service.py`, y **cero escrituras** en `C:\Users\carch\Downloads`, en `dist/` y en
  la raíz del repo desde cualquier test.
