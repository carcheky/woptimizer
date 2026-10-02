## CYCLE-050 - 2026-10-03

**Infraestructura & Distribución** - `TASK-062` (Publicar las releases del `.exe` con semantic-release)

### Añadido

- 🆕 **Carpeta `basura/`, fuera de Git, para.quitar lo que sobra sin borrarlo.** Los ficheros que sobran se mueven ahí con su motivo escrito, y ya puedes borrarla entera de una vez cuando toque. Está en `.gitignore`, así que borrarla no genera ni un commit.
- 🆕 **Ya hay ejecutables descargables en la pestaña Releases de GitHub, y el número de versión lo decide el código, no una persona.** A partir de ahora la versión sale del propio mensaje del commit: un `fix:` sube el último número, un `feat:` sube el medio, y un `BREAKING CHANGE:` sube el mayor. No hace falta crear ninguna etiqueta a mano ni acordarse de qué número va.
- 🆕 **Rama `beta` para probar sin arriesgar la versión buena.** Cada merge a `beta` publica una versión de prueba marcada como *pre-release* en GitHub, con su `.exe` incluido. Cuando la cosa está fuma, se fusiona `beta` en `main` y se publica la versión estable.
- 🆕 **Cada `.exe` se compila desde el commit al que apunta su versión.** Antes el ejecutable publicado se compilaba a mano y nada garantizaba que correspondiera al código de esa versión: era un desfase que nadie vigilaba. Ahora no puede ocurrir.
- 🆕 **Los commits se revisan antes de publicar nada.** Si alguien escribe un mensaje mal formado, el proceso se detiene y avisa. Antes eso no pasaba: el mensaje se ignoraba en silencio y simplemente no se publicaba versión, sin explicar por qué.

### Corregido

- 🛡️ **Retirado el workflow que publicaba en la etiqueta del push.** Con el sistema nuevo, cada versión creada disparaba además el workflow antiguo, y los dos intentaban escribir la misma versión a la vez. Dos procesos peleándose por lo mismo no es una automatización: es una carrera.
- 🛡️ **Seis ficheros de la raíz que ya no servían para nada** se han ido a `basura/`: tres verificadores de la versión 2, su fichero de pruebas, un script que sacaba la versión de un archivo que lleva tiempo borrado, y un CSV de procesos que ya se había migrado. **Los seis tenían un motivo escrito**, y las cuatro páginas de documentación que los nombraban se han actualizado para que no affirmen cosas que ya no son ciertas.
- 🛡️ **El ejecutable ya no puede ir por detrás del código fuente** en la pestaña de instalación. Se ha quitado el aviso que lo advertía porque la causa ya no existe.

### Lo que no cambia

- Sigues instalando igual: descargas `woptimizer.exe` de **Releases**, doble clic, aceptas permisos de administrador. Solo cambia quién decide el número y cuándo se reconstruye.

---

## CYCLE-048 - 2026-10-02

**Documentación & Arquitectura** — `TASK-058` (Sanear las filas FALSAS de la Deuda Técnica Conocida de `STATUS.md`)

> 🧬 **VEREDICTO FINAL: PARTIAL — contenido cerrado y verificado por contenido; la supervisión de ese contenido sigue pendiente, y eso no es un detalle.** La primera ronda de este ciclo escribió aquí `PASS`; la auditoría de `mutation-auditor` lo refutó por dos motivos, y este bloque los recoge ya corregidos: **(S1)** bajar la gravedad de la fila del `spawn EPERM` para que el panel quedara más limpio es **documentación fail-open** — un panel que infravalora una deuda hace que el bucle la trate como resuelta y la abandone—, y **(S2)** ninguna comprobación verifica las filas de esta sección. La fila volvió a 🔴 con su ancla, y la deuda del check que falta quedó escrita en el panel con su criterio completo. Lo que se corrige es **el panel que gobierna qué trabajo hace el bucle**, que es justo donde este repo ya se engañó dos veces. Cero cambios de producto: `src/` y `validate_docs.py` intactos; en `run_tests.py` **una línea de docstring** (el «7» del encabezado de la tabla de escenarios, descrito más abajo) y ningún test añadido, borrado ni alterado, así que el recuento sigue en **103 tests** (derivado con `ast`, no escrito a mano).
 La primera ronda de este ciclo escribió aquí `PASS`; la auditoría lo refutó. Tras cuatro rondas más, **los tres hallazgos de la auditoría están cerrados y verificados por contenido, no por la palabra del dev**: la 🔴 del `spawn EPERM` volvió a su gravedad real y **ya tiene dueño** (`TASK-061`); la cuenta de filas vivas del panel es la real; y las seis citas de ancla rotas están parcheadas a lo que de verdad dicen, con la causa corregida (ya estaban rotas antes de este ciclo, desviadas 160–1270 líneas). **Pero el veredicto no es PASS, y no por falta de trabajo.** El auditor medió que **8 de 9 mutaciones sobreviven**, y la razón no es que las correcciones sean falsas: es que **nada en este repo vigila nada de esto**. `validate_docs.py` no tiene ni una coincidencia de «Deuda» y menciona `STATUS.md` una sola vez, en la lista del recuento de tests. El único fix del ciclo con guardia real es el cableado del botón, que **muere** con su aserción exacta. El arreglo de fondo es `TASK-060` (el check que exige que cada fila viva lleve un ancla cuya verdad se derive de fuera del panel). Cerrar esto como PASS sería declarar resuelto lo que sigue sin vigilar, que es exactamente el fallo que este ciclo vino a matar. **Lo no verificado no toca seguridad ni datos**: `src/` y `validate_docs.py` intactos, `run_tests.py` con una línea de docstring, ningún test añadido ni alterado, recuento estable en **103 tests** (derivado con `ast`).
### Por qué esta tarea no era cosmética
Cuando el backlog está vacío, el Paso 1 del bucle lee `## ⚠️ Deuda Técnica Conocida` y prioriza lo que ahí pone literalmente. **De 13 filas auditadas, tres mentían** —y dos de ellas no las detectó nadie— así que el panel mandaba repetir trabajo ya hecho o tomarlo por cerrado cuando no lo estaba. El precedente de por qué las filas cerradas **no se borran** estaba escrito en la propia sección desde el ciclo #26, y este ciclo se aplicó esa regla a sí mismo: **ninguna fila se borró**.

### Corregido (con la redacción original conservada, más su cierre comprobable)
- 🔴 **La fila de los 11 `test_*.py` "en la raíz" era falsa por partida doble.** No estaban en la raíz: los 11 se archivaron en `docs/archive/legacy-root-tests/` en el ciclo #45 (`TASK-055`), y un guard impide que vuelvan. Y de los 11, solo **10** morían por `import process_manager`: el undécimo, `test_powershell_direct.py`, no lo importaba y **no estaba muerto** —lanzaba `notepad.exe` y ejecutaba `taskkill /F`, un riesgo de efecto colateral completamente distinto del que la fila describía. Verificado con `ast.Import` sobre los 11, no contando la aparición de la cadena en un comentario.
- 🔴 **"Sin commit desde el ciclo #14" era falsa.** Los ciclos #14 a #20 sí están versionados: `git_safe_commit.py --verify` responde `WOPT_REPO_OK` con exit 0. El dato cierto y comprobable no es «sin commit» sino **«sin commit ANCLADO»**, y ese ya vivía con su severidad en la fila del residuo honesto del ciclo #47: la fila queda como puntero, no como deuda.
- 🔴 **La fila de `docs/api.md`/`docs/index.md` documentando una API v2 caducó en el ciclo #44.** Cero residuos v2 en ambos ficheros, `docs/api.md:1` es «Referencia de API (v3)» y `TASK-054` está cerrada con un test que lo impide volver. **El criterio de aceptación de la tarea pedía "actualizar esa fila con su severidad real", y eso estaba construido sobre un estado del repositorio que ya no existía**: ejecutarlo al pie de la letra habría reescrito una fila cerrada y reintroducido en el panel una afirmación que el ciclo #44 ya demostró falsa. Se conserva como cerrada, y la deuda real que la fila describía mal entra en su lugar, viva y con su propia severidad.
- 🔴 **La fila del `spawn EPERM` decía «afecta al versionado, no al producto», y esa frase era falsa:** en el ciclo #11 esa misma intermitencia hizo que `git_safe_commit.py` saliera con **código 0 ante cualquier fallo de commit** y se perdieran commits. No era inocua: era la causa de un falso verde de versionado. *(La primera ronda de este ciclo bajó la gravedad de esta fila a 🟡 «porque la frase ya no era falsa». La auditoría lo refutó: eso es documentación fail-open, y la fila ha vuelto a 🔴 en la ronda de cierre.)*
- **Dos filas caducadas, corregidas sin borrar nada:** la del validador que «se deduce a sí mismo» (cerrada en el ciclo #47 con el ancla como unión del journal y el historial) y la de los 3 supervivientes del #17, cuya cola apuntaba a `TASK-031`, una tarea ya `completed`. Un puntero a una tarea cerrada se lee como deuda viva y no lo es.

### El fallo vivo que sí quedaba, y ahora es una fila
- 🟡 **`docs/index.md:25` declaraba «96 tests» y la verdad eran 103** (gravedad 🟡 y no 🔴, con el criterio escrito en la propia fila: documento publicado desfasado, sin efecto sobre el producto; sube a 🔴 el día que la afirmación falsa sea de versionado o de datos). Y el check que vigila el recuento no lo ve: su lista son tres ficheros (`validate_docs.py:116-118`) más la tabla de `docs/ai/testing-guide.md` (`:142-160`), **cuatro testigos, y ese no está**. Es el mismo fallo que ese check ya cazó una vez, por la misma puerta, y el fichero está **publicado** como portada del sitio (`mkdocs.yml:70`). La cifra se corrige a 103; la fila **no se cierra**, porque el fallo estructural sigue y lleva su mutante escrito: cambiar ese 103 por cualquier otro número y todo el panel, validador incluido, seguirá en verde.

### Lo que queda vivo y con nombre
- **TASK-060** — el check que exigirá un ancla resoluble a toda fila **no** marcada cerrada, con la verdad derivada de **fuera** del panel (árbol, recuento con `ast`, `git log`). **Se decidió aquí y no se implementó aquí**: es un ciclo propio, y las filas cerradas quedan exentas o el check fallaría siempre y nadie lo miraría.
- **Una incoherencia de la cabecera** que no estaba en el encargo: la línea del ciclo actual decía «Ciclo #47 … Completado» mientras la siguiente ya anunciaba la tarea de este ciclo. Corregida.

### Honestidad del alcance
- **Dos premisas del encargo resultaron falsas y no se ejecutaron al pie de la letra** (ver la nota de proceso de este ciclo). Se corrige el criterio antes de ejecutarlo, no después.
- **Una extensión que la especificación daba por hecha en este ciclo y no se hizo:** la proposal mencionaba ampliar la lista del check del recuento con `docs/index.md`. Su propia lista de ficheros excluía `validate_docs.py`, y esa ampliación está reasignada a `TASK-060`. Se siguió la lista de ficheros: el validador no se tocó.
- **Paso 4 sin aplicar, y por qué:** no hay código de producto que mutar en este ciclo. La verificación se hizo con un comprobador propio que relee lo escrito y **resuelve cada ancla `archivo:línea` por contenido** (no solo existencia), más las tres verificaciones del repo en verde.

### Ronda de cierre — la auditoría dio FAIL y un superviviente se arregla, no se documenta

- 🔴 **La fila del `spawn EPERM` vuelve a 🔴.** La primera ronda la bajó a 🟡 «porque la frase ya no era falsa», y eso es **documentación fail-open**: un panel que infravalora una deuda hace que el bucle la trate como resuelta y la abandone. La gravedad describe el estado real, no la tranquilidad del panel. Y la fila **no se cierra**, porque su problema de fondo sigue abierto y ahora está medido.
- **Medido, no recordado — el invariante que el ciclo #11 rompió.** «Un fallo de git tiene que salir con un código distinto de 0» **se cumple hoy en el código** (un repo cuyo `pre-commit` falla hace que el wrapper salga con `1` y `WOPT_FAIL commit`) y **no lo comprueba ningún test**: `test_git_safe_commit_fail_safe` solo exige `3` y `2`, y ninguna de sus invocaciones llega a un `WOPT_FAIL`. **Mutante medido** (`sys.exit(CODE_FAIL)` → `sys.exit(CODE_OK)` en el camino de commit) → **la suite entera sigue 103/103 en verde**. Sobrevive.
- **El código de salida que hoy se confunde con el de commit OK es el `0`**, porque está sobrecargado: `WOPT_COMMIT_OK` (commit real) y `WOPT_NOOP` (nada que comitear) salen los dos con `0`. Medido en el repo real con el árbol limpio: `WOPT_NOOP` + **exit 0**, sin escribir nada. Quien solo lea el código de salida **no puede distinguir «se ha versionado» de «no había nada que versionar»**.
- **Por qué nadie escribió ese test, y por qué no es pereza:** `get_env()` respeta un `GIT_DIR` del entorno pero **impone `GIT_WORK_TREE = REPO_ROOT` sin condición**, así que una invocación con un `GIT_DIR` desechable sigue haciendo `add -A` y `commit` **sobre el árbol de trabajo real**. El hook que la documentación llama «tests herméticos» es hermético **en el repo, no en el árbol de trabajo**. Cerrar esa fila exige una decisión de diseño y después su test. **Ya tiene dueño: `TASK-061`**, que existe para tomar esa decisión *antes* de escribir el test. Y una corrección al tamaño del daño: como `WOPT_NOOP` nunca imprime hash (`docs/ai/sandbox-rules.md:56`), el fallo del ciclo #11 **en su forma literal** —el CHANGELOG registrando hashes que no existen— no puede recuperar por esta puerta; el daño real es **«ciclo cerrado sin commit»**, la misma clase y un grado menos explosivo.
- **La fila del check que falta (`TASK-060`) queda en el panel con el criterio entero**, para que el ciclo #49 se ejecute sin volver a preguntar nada: qué filas deben llevar ancla, por qué la verdad se deriva de fuera del panel, por qué las cerradas quedan exentas, la función extraída con `root` y el motivo, los cuatro escenarios del test, los dos mutantes que debe cerrar la auditoría, y **el quinto testigo** (`docs/index.md` declara un número de tests que el check del recuento no vigila). Se anota también la única decisión que queda abierta, y ya no es una pregunta sino una cuenta: hay **cinco filas vivas** (87, 88, 94, 99 y la propia 100); con la lectura estricta (`fichero:línea`) **fallan dos, la 87 y la 94**, y con la leniente **falla una, la 94**, la única con cero referencias a ficheros. *Corrección: la primera versión de esta frase citaba `STATUS.md:91` como caso y es falsa —esa fila **está cerrada** («cerrado en el ciclo #16») y el criterio exonera las cerradas.* La propuesta para que el check no nazca fallando está escrita en la fila: marcador de cierre estructural, ancla propia para la 87 y fila-tabla para la 94.
- **Barrido de las demás filas que tocó la primera ronda:** **ninguna más tenía la gravedad rebajada sin cierre.** Y en dirección inversa —una fila marcada cerrada que en realidad sigue viva— tampoco hay ninguna: las seis se han vuelto a comprobar contra el repo (11 ficheros archivados y 10 de 11 importando `process_manager` con `ast`, 0 tests en la raíz, `WOPT_REPO_OK` exit 0, `TASK-031` y `TASK-054` `completed`, `docs/api.md` en v3 sin residuos, los dos helpers del ancla de ciclos en su sitio). De paso se corrigieron **dos afirmaciones falsas que quedaban en este changelog**: el `PASS` de la primera ronda y la descripción de la bajada de gravedad como si fuera un arreglo.
- **`mutation-report.md` escrito** en el change: los tres supervivientes con su mutación literal, el estado del repo que los dispara, su severidad y **por qué no los mata nadie**, más los confirmados para que el próximo no repita el trabajo y el comando con su salida real.
- **Dos trampas de medición que casi produjeron un veredicto falso, y quedan escritas para el próximo:** en este repo, **un hash igual no prueba que el mutante estuviera puesto** (el árbol está en un directorio sincronizado y la primera medición leyó el hash del fichero sin mutar, casi dando por bueno un mutante que no se había aplicado: hay que confirmarlo **por comportamiento**), y la consola es `cp1252`, así que un emoji en un `print()` revienta la sonda (trampa #16, vivida otra vez).


### Cuarta ronda (con una quinta detrás, de cifras y citas, escrita en `mutation-report.md` §8): el «7», la enumeración que mentía y las seis anclas que ya estaban rotas

- 🔴 **La enumeración de la fila 100 era falsa por partida doble, y lo grave no era el número.** Decía «dos filas» (la 94 y la 100); medido con ese mismo clasificador ingenuo de `cerrad` sobre las 5 filas vivas, marca **tres**: la **88**, la **94** y la **100** — en la 88 el subradical es «ciclo cerrado sin commit». Y en la misma frase había otra cifra falsa del mismo tipo: «sus seis apariciones» eran **catorce** en el texto que se corrigió (`re.findall(r"cerrad", fila, re.I)` sobre la fila 100), y son **diecisiete** en el ya reescrito: **la cuenta es autorreferente**, porque al reescribir la frase la frase se cuenta a sí misma. Con la enumeración de dos, quien ejecute `TASK-060` acota el trabajo a 94/100 y **deja sin cubrir la fila 88, que es la 🔴**: el error de alcance era el grave, no el número.
- **La corrección que de verdad protege no depende de la lista.** La enumeración queda escrita como **medida ilustrativa**, y lo que manda es **P1**, el marcador de cierre estructural: sin depender de buscar una palabra, la exención no puede clasificar mal ninguna fila, así que **si la lista vuelve a quedarse corta, el fix no se rompe**.
- **Y P1 trae un requisito medido que este ciclo no puede decidir por sí solo,** con **un solo criterio** para no volver a mezclar dos: el marcador de P1 tal como está definido, `CERRADA`/`CERRADO` **en mayúsculas**, sin distinguir dónde esté. De las **15** filas de la sección, **8 lo llevan** (la `:95` en el offset 6 y otras 6 en medio, offsets 200 a 825) más la propia 100, que lo lleva porque el criterio está escrito en ella, y **7 no** (87, 88, 90, 91, 94, 97 y 99): de esas 7, cuatro son las vivas (87, 88, 94, 99) y tres (90, 91, 97) son filas cerradas que solo lo escriben en minúscula, luego los dos criterios no coinciden. Y **ninguna** lo tiene en el offset 0 que P1 exige, así que tal como está hoy P1 daría por vivas las quince. (La versión anterior de esta frase mezclaba criterios: el «9» salía por resta, `15 − 5 vivas − 1`, y los offsets por otra regex; con un criterio único salen 7 y 8.)
- **El «7» se arregla, no se carve-outea.** El encabezado de la tabla de escenarios decía «LAS SIETE FILAS» (`run_tests.py:12381`) con **ocho** filas reales (a)-(h) (`run_tests.py:12383-12413`), su nota de límite ya decía «las ocho filas» (`run_tests.py:12420-12421`) y la fila 94 arrastraba el mismo «7». Corregidos los tres sitios. Con esa redacción, la regla 🟡 de la propia fila 100 («mientras no haya ninguna afirmación falsa viva en la sección») **tenía una afirmación falsa viva**: el propio 7. Un carve-out para exceptuar una falsehood concreta sería más deuda que la falsehood. `.taskmaster/CHANGELOG.md:254` también dice «7 filas» y es **histórico**: se deja, porque reescribir el pasado de un changelog es la misma mentira que se está corrigiendo.

#### Las seis anclas, parcheadas a su contenido

| Ancla del contrato | Dónde apuntaba de verdad | Ancla correcta |
|---|---|---|
| `2026-09-29-data-integrity-fixes/proposal.md:234` → `.taskmaster/CHANGELOG.md:91` | Nada de la rotación de backups: hoy esa línea es una de `Models` de `CYCLE-047` («… test en `run_tests.py:11478` · `_ciclos_de_commits`…») y lo más cerca, «Fila nueva del panel», está **3 líneas más abajo**, en `:94` | `.taskmaster/CHANGELOG.md:1399` |
| `2026-09-30-task028-debt-cleanup/proposal.md:166` → `:530-536` | `CYCLE-036` (confirmable-mixin-contracts), no el ciclo 13 | `.taskmaster/CHANGELOG.md:1670-1695` (entrada `CYCLE-013`) |
| `2026-09-30-task028-debt-cleanup/tasks.md:78` → `:530-536` | ídem | `.taskmaster/CHANGELOG.md:1682` (las «48 → 73 entradas») |
| `2026-09-30-task028-debt-cleanup/tasks.md:80` → `CHANGELOG:536` | `Estado: COMPLETED` | `.taskmaster/CHANGELOG.md:1686` (la pila de Armoury Crate) |
| `2026-10-01-multi-favorites-and-db-download/proposal.md:29` | `self.cancel_on_destroy()`; y **la afirmación es falsa hoy** | `src/woptimizer/ui/views/process_manager_view.py:136` (el llamador) y `:183` (la definición) |
| `2026-10-02-sanear-deuda-status/proposal.md:36` → `:1525` | `model_copy()` shallow | `.taskmaster/CHANGELOG.md:1723` |

- **La quinta es la que más miente, y no se arregla cambiando un número.** Decía que `_force_update_db()` «no tiene ningún llamador en todo el repo: el botón nunca se conectó». Medido: **sí lo tiene**, `command=self._force_update_db` en `process_manager_view.py:136`, que es el botón «Actualizar DB» (`:135`). **La fecha que le puse a esa frase también era falsa, y por un día:** escribí «era cierta el 2026-10-01», pero `CYCLE-041` (`## [CYCLE-041] 2026-10-01 23:25`, `.taskmaster/CHANGELOG.md:397`) es **el mismo change** que escribió la afirmación **y** el que conectó el botón (`2026-10-01-multi-favorites-and-db-download`, cuya `TASK-051` es la que la invalidaba), así que ese día la afirmación **ya era falsa**: la invalidó la misma entrada que la repetía. **Era cierta a más tardar el 2026-09-30**, y por un día creí que era cierta hasta el 01 en la frase que decía contener «la fecha en que era cierta». El «sin llamador» que la frase afirmaba es de **otra** función: `GamingService.should_kill_for_gaming()`, en `.taskmaster/CHANGELOG.md:1714`. La fila se reescribe con las tres cosas: la verdad de hoy, la fecha en que era cierta, y a quién pertenecía el hallazgo.
- **La causalidad, corregida porque lo que estaba escrito era falso, y con las cifras medidas otra vez.** Se atribuía el desplazamiento a que el cambio de esta entrada añadía 30 líneas. **Medido con `git show --numstat 9a8e952`: esta entrada añade 65 líneas en los dos changelogs (39 en el técnico y 26 en este), no 68, y ninguna de las 6 se rompió por ellas**; el commit entero son 87 inserciones y 18 borrados, y **ninguna de sus 87 líneas es de `src/`**. Las desviaciones reales de las **5** anclas que apuntan al changelog técnico (la sexta va a un fichero de `src/`) van de **160 a 1270 líneas** contra `HEAD~1` y de **198 a 1308** en `HEAD`: `91→1361`, `530→1632`, `530→1644`, `536→1648` y `1525→1685` en `HEAD~1`, cada una resuelta **por contenido** (buscando la línea citada en `git show HEAD~1`, no sumando). Y hay un caso que no admite discusión: la cita de `multi-favorites` apunta a `src/woptimizer/ui/views/process_manager_view.py`, fichero que este ciclo **no toca** (`src/` con cero cambios), luego su desviación es previa por construcción. Matiz que también queda escrito: esta entrada **sí** invalidó 4 anclas —esas 4 sí se arreglaron y están bien—, así que la verdad es que hay dos causas distintas y se habían fundido en una.
- **Dos más de la misma familia, corregidas** con el mismo método: `2026-09-29-data-integrity-fixes/tasks.md:47` y `2026-09-30-task028-debt-cleanup/proposal.md:173` repetían las dos citas rotas.
- **Los dos «no tocados» que declaré no existían como los describí; el principio, en cambio, se sostiene entero.** Escribí que la cita `CHANGELOG.md:91` se repetía en el bloque histórico de `CYCLE-017` del changelog técnico y en las notas de `TASK-011` de `tasks.json`. **Medido: ninguno de los dos objetos es el que yo nombré** — el bloque `CYCLE-017` va de `:1852` a `:1883` y tiene **cero** ocurrencias de `CHANGELOG.md:91` (cero de la cadena `CHANGELOG`), y `TASK-011` **no tiene campo `notes`**, ni la cita ni otra: sus claves son `id`, `title`, `description`, `complexity`, `dependencies`, `priority`, `status` y `module`. La cita **sí existe**, pero en otro bloque y otra tarea: `.taskmaster/CHANGELOG.md:1747`, dentro de **`CYCLE-015`** (`## [CYCLE-015]` en `:1734`), y las dos que quedan en `tasks.json` (`:423` y `:455`) son de **`TASK-026`** («Integridad de datos, copia profunda y resiliencia de servicios»), no de `TASK-011`. Es la misma forma que el `7`: cifra pequeña, objeto inventado. Lo que **no** cambia es el motivo para no reescribirlos —reescribir el registro de lo que se creía sería la misma mentira que se está corrigiendo—, pero no hay dos sitios «declarados sin tocar»: hay uno solo, y está donde nadie lo nombró.
- **Una de la misma familia queda fuera de este encargo, medida y con dueño:** `2026-09-30-close-mutation-survivors/proposal.md:17` cita `CHANGELOG.md:57-67` como «sección CYCLE-017» y no resuelve. **Medido, y es peor de lo que yo había escrito:** en el changelog de la raíz `:57` es **una fila de la tabla de seis anclas de esta misma entrada** y `:67` es `## CYCLE-047 - 2026-10-01`; la `CYCLE-017` de verdad está en `:724` de la raíz y en `:1852` del técnico, y en ambos ficheros las entradas van del ciclo más reciente al más antiguo. **No se parchea** (es propuesta de otro change) y **no creo tarea**: el dueño es `architect-review`, porque arreglarlo es o corregir esa propuesta o cambiar la convención de anclas del repo, y las dos son decisiones de contrato, no correcciones. Queda anotado aquí y en `mutation-report.md` §7 para que no se pierda al pasar al ciclo siguiente.
- **La REGLA que se deduce de las seis, escrita junto a la convención de anclas y NO implementada** (es un cambio de contrato, no una corrección de este ciclo): **una cita `fichero:línea` a un fichero que crece por arriba se caduca sola.** No hace falta que nadie la toque. La arreglo de fondo es citar **por ciclo + encabezado**; la decisión es del arquitecto.

---
## CYCLE-047 - 2026-10-01

**Arquitectura & Calidad** — `TASK-057` (Ancla de trazabilidad de ciclos: que el registro no dependa de quien lo escribe)

> ✅ **VEREDICTO FINAL: PASS** — Cerrado tras **cuatro rondas de auditoría**. Las tres primeras dieron FAIL; la cuarta dejó **0 supervivientes** de los 20 mutantes declarados. **103 tests** en verde, y la suite **bajó** de 104 a 103 durante el ciclo: los casos se convirtieron en filas de una tabla, no en pruebas nuevas.

### Añadido
- **Un tercer testigo para "este ciclo quedó registrado".** Antes, esa pregunta solo se le podía hacer al diario interno del motor, y ese diario lo escribe el mismo motor que después se autoverifica. Ahora el requisito se exige tanto al diario **como** al historial de commits: para que un ciclo deje de exigirse habría que reescribir la historia de git, no editar una línea de un JSON.
- **El validador avisa cuando no puede comprobar.** Si el historial de commits no se puede leer, el chequeo sale en rojo diciendo el motivo literal, en vez de darse por satisfecho en silencio. Un validador que no puede mirar y aun así dice "todo bien" es peor que uno que no existe, porque entrena a leer la luz verde como si fuera rutina.
- **Un registro de mutaciones que vive en el repo**, con la mutación literal, la aserción, el número de guardianes y el motivo de cada muerte. Antes no existía, así que las 12 supervivencia de una auditoría previa eran imposibles de reauditar por nombre.

### Corregido
- 🔴 **Una cifra falsa que se había propagado a 5 ficheros.** Decía que "41 de 46 entradas del diario no tienen hash resoluble". **Medido de verdad: 1.** Once entradas no declaran hash alguno y solo el ciclo 33 se queda sin ninguno resoluble. El error fue medir el texto de la entrada (`617eef8 (architect)`) en vez del hash. La consecuencia era grave: una tarea pendiente (TASK-059) descartaba esa verificación argumentando que dejaría el validador permanentemente en rojo, cuando daría **un** fallo, no 41. Corregido en la documentación, en la especificación y en el tablero.
- 🔴 **El falso verde del ciclo 15 reintroducido por otra puerta.** El validador buscaba el número de ciclo como subcadena al comprobar los encabezados, así que un encabezado borrado seguía contando como presente mientras la prosa mencionara el número. El propio código lo advertía 200 líneas más arriba y lo cometía igualmente. **Demostrado, no supuesto:** con el bug puesto, un árbol con `TASK-015` en vez de su encabezado pasaba en verde.
- 🛡️ **Un comentario que decía una falsehood técnica.** El código justificaba no estrechar el manejo de errores diciendo que `FileNotFoundError` y `PermissionError` "no son OSError". **Son subclases de OSError.** La razón real es un tiempo de espera agotado, y ya está escrita bien.
- **Un informe de auditoría que se contradecía a sí mismo** y que atribuía cada muerte al test equivocado. Tres de esas atribuciones eran falsas por omisión: nombraban un test que sí lo detectaba, pero no el primero, ni el número real de guardianes. Rehecho con las dos columnas medidas.

### El hallazgo que devolvió el trabajo a la mesa dos veces
- 🔴 Los tests llamaban a las funciones internas del validador pasándoles **a mano** los argumentos. Eso hacía que el código que conecta esas funciones jamás se ejecutara en las pruebas: se podía **desenchufar el chequeo entero y la suite seguía en verde**. Es justo el fallo que el ciclo anterior (TASK-056) existía cerrar para el código del producto, reproducido en el propio validador. Al repetirse, el plan cambió: un solo camino de validación y los casos como filas de una tabla, de modo que **un hallazgo futuro cueste una fila y no una prueba más**.
- **Lo que queda, dicho sin adornos:** el desconexión silenciosa está **erradicada donde se produjo** y **desplazada donde no se buscó**. Un asunto con plural ("ciclos 14-20") declara un rango, y los rangos están acotados para que un texto cualquiera no pueda exigir 9999 ciclos. Dejar eso anotado como cerrado sería repetir el fallo que este ciclo vino a matar.

---

## CYCLE-046 - 2026-10-01

**Arquitectura & Calidad** — `TASK-056` (Guard de código muerto: que el código esté USADO, no solo testeado)

> 🟢 **VERDICT FINAL: PASS** — Análisis estático exhaustivo de referencias para las 201 funciones/métodos del código, saneamiento de código muerto y guard AST auditados con éxito por `mutation-auditor` (4/4 mutaciones eliminadas: M1, M2, M3, M4, 0 supervivientes). **99 tests** (89 backend + 10 headless UI) pasando al 100%.

### Añadido
- **Test Guard AST `test_dead_code_ast_guard`.** Nuevo test #99 en `run_tests.py` que recorre dinámicamente todo el árbol de `src/woptimizer/**` extrayendo las 201 definiciones de funciones y métodos, acumulando frecuencias de referencias (`Name` y `Attribute`) y verificando que no existan símbolos huérfanos sin llamadores reales en el producto ni en tests.
- **Conexión de `get_favorite_packs` en la Portada.** `DashboardView` ahora utiliza formalmente el método `self.pack_service.get_favorite_packs()` en lugar de reinventar el filtrado con comprensiones locales de listas.
- **Integración y Verificación de `is_wcag_aa`.** El helper de contraste accesible de `ui/theme.py` ahora se evalúa y comprueba directamente en `test_contrast_wcag_aa`.
- **Sincronización Cuádruple de Métricas.** Actualizado el recuento canónico a 99 tests en `STATUS.md`, `AGENTS.md`, `README.md` y `docs/ai/testing-guide.md`.

### Corregido
- **Eliminación de Métodos y Propiedades Muertas.** Removidos `_get_priority` y `process_db` de `src/woptimizer/services/process_service.py`, eliminando restos legacy de la versión 2 que carecían de consumidores.

---

## CYCLE-045 - 2026-10-01

**Testing & Calidad** — `TASK-055` (Los 10 test_*.py muertos y el script que LANZA notepad)

> 🟢 **VERDICT FINAL: PASS** — Archivo histórico de scripts de prueba de la raíz, documentación exhaustiva y guard anti-regresión auditados con éxito por `mutation-auditor` (4/4 mutaciones eliminadas: M1, M2, M3, M4, 0 supervivientes). **98 tests** (88 backend + 10 headless UI) pasando al 100%.

### Añadido
- **Archivo Histórico en `docs/archive/legacy-root-tests/`.** Trasladados sin eliminación los 11 archivos de prueba procedentes de la arquitectura legacy v2 (`test_categorization.py`, `test_debug_list.py`, `test_gaming_profile.py`, `test_gaming_session.py`, `test_harness_v2.py`, `test_harness.py`, `test_kill_expansion.py`, `test_kill_real.py`, `test_powershell_direct.py`, `test_profiles.py`, `test_relaunch_grouping.py`).
- **README Explicativo y Documentación de Riesgo.** Creado `docs/archive/legacy-root-tests/README.md` detallando la clasificación de los 10 scripts v2 que morían por `ModuleNotFoundError: No module named 'process_manager'` frente al riesgo de ejecución autónoma de `test_powershell_direct.py` (que lanzaba `notepad.exe` e invocaba `taskkill` y PowerShell).
- **Test Guard Anti-Regresión `test_no_legacy_test_files_in_root`.** Nuevo test #98 en `run_tests.py` que asegura que ningún fichero `test_*.py` permanezca o vuelva a crearse en la raíz del repositorio, y verifica la presencia, tamaño e integridad de los 11 ficheros y el README en el directorio de archivo.
- **Sincronización Cuádruple de Métricas.** Actualizado el recuento canónico a 98 tests en `STATUS.md`, `AGENTS.md`, `README.md` y `docs/ai/testing-guide.md`.

---

## CYCLE-044 - 2026-10-01

**Documentación & Arquitectura** — `TASK-054` (Alinear docs/api.md y docs/index.md con la v3 real)

> 🟢 **VERDICT FINAL: PASS** — Reescritura documental integral, erradicación de residuos legacy v2 y test de contrato documental auditados con éxito por `mutation-auditor` (4/4 mutaciones eliminadas: M1, M2, M3, M4, 0 supervivientes). **97 tests** (87 backend + 10 headless UI) pasando al 100%.

### Añadido
- **Test de Contrato Documental `test_docs_api_and_index_v3_contracts`.** Nuevo test #97 en `run_tests.py` que comprueba:
  1. Ausencia estricta de términos prohibidos de la v2 (`is_admin`, `taskkill`, `powershell`, `saved_processes.json`, `ProcessManagerApp`) en `docs/api.md`.
  2. Verificación en runtime mediante introspección (`hasattr`, `callable`) de que todos los métodos y modelos documentados existen realmente en `src/woptimizer/` (`ProcessService`, `PackService`, `GamingService`, `NotificationService`, `ProcessInfo`, `Pack`, `AppData`).
  3. Ausencia de afirmaciones falsas sobre elevación de privilegios UAC nativa o scripts legacy (`.vbs`, `.pyw`, `taskkill`) en `docs/index.md`.
  4. Integridad de los archivos referenciados en el bloque `nav` de `mkdocs.yml` asegurando que todos existen en disco.
- **Sincronización Cuádruple de Métricas.** Actualizado el recuento canónico a 97 tests en `STATUS.md`, `AGENTS.md`, `README.md` y `docs/ai/testing-guide.md`.

### Corregido
- **Alineación de `docs/api.md` con la v3 Real.** Reescrito íntegramente contra los servicios desacoplados, modelos Pydantic v2 e inspección de procesos con `psutil`, eliminando referencias obsoletas a `taskkill`, PowerShell y scripts legacy.
- **Alineación de `docs/index.md` con la v3 Real.** Actualizada la introducción, comandos de arranque (`python run.py`, `dist\woptimizer.exe`), árbol de estructura de directorios y características reales de la versión 3.

---

## CYCLE-043 - 2026-10-01

**Testing & Calidad** — `TASK-053` (Actualizar Tests de Exclusividad, Recuento y Documentación)

> 🟢 **VERDICT FINAL: PASS** — Actualización de semántica acumulativa en tests de favoritos, erradicación de llamadas obsoletas a `set_favorite` y comprobación AST auditadas con éxito por `mutation-auditor` (4/4 mutaciones eliminadas: M1, M2, M3, M4, 0 supervivientes). **96 tests** (86 backend + 10 headless UI) pasando al 100%.

### Añadido
- **Guard AST de Inexistencia de `set_favorite` Unario.** Integrada verificación estática en `run_tests.py` que recorre el árbol sintáctico comprobando que ninguna invocación a `set_favorite` recibe un único argumento.
- **Sincronización de Comportamiento Acumulativo en `test_toggle_favorite_desmarca`.** Adaptado el mock `_Grabador` para soportar `toggle_favorite` y semántica acumulativa. En el caso multiselección (caso 4), desmarcar un favorito preserva intactos a los demás (`{"a": True, "b": False}`).

### Corregido
- **Alineación del Runner de Tests.** Verificados y actualizados los registros de ejecución en `run_tests.py` y sincronizados los 96 tests en la tabla canónica de `docs/ai/testing-guide.md` y archivos de métricas.

---

## CYCLE-042 - 2026-10-01

**UI & Experiencia de Usuario** — `TASK-052` (Placeholder del Desplegable sin Doble Flecha en ProcessManagerView)

> 🟢 **VERDICT FINAL: PASS** — Centralización del placeholder y erradicación del glifo redundante de flecha auditados con éxito por `mutation-auditor` (4/4 mutaciones eliminadas: M1, M2, M3, M4, 0 supervivientes). **96 tests** (86 backend + 10 headless UI) pasando al 100%.

### Añadido
- **Constante Centralizada de Módulo `PLACEHOLDER_PACK`.** Definida como `Final[str] = "Seleccionar Pack"` en `src/woptimizer/ui/views/process_manager_view.py`, centralizando el texto y eliminando divergencias entre la inicialización y la lógica de reseteo.
- **Eliminación del Glifo Redundante `▼`.** Removido el caracter `▼` (`U+25BC`) del texto del placeholder para evitar la doble flecha visual, ya que `CTkOptionMenu` incluye su propio indicador nativo dibujado por CustomTkinter.
- **Invariante en Comparación de Desplegable.** Se actualiza `_update_pack_dropdown()` para utilizar estrictamente la constante `PLACEHOLDER_PACK` al verificar si el valor actual requiere reseteo.
- **Test Discriminante en `run_tests.py`.** Introducido `test_process_manager_pack_dropdown_single_arrow_and_placeholder` (test #96) con inspección de ausencia de glifos en la constante, guard AST que asegura que el literal aparece una sola vez en el código fuente, verificación de uso de la constante en `_update_pack_dropdown` y validación en runtime headless.

---

## CYCLE-041 - 2026-10-01

**UI & Experiencia de Usuario** — `TASK-051` (Botón de Actualizar DB Funcional y Honesto en ProcessManagerView)

> 🟢 **VERDICT FINAL: PASS** — Botón de actualización manual, reporte honesto en barra de estado y blindaje contra sobreescrituras auditados con éxito por `mutation-auditor` (4/4 mutaciones eliminadas: M1, M2, M3, M4, 0 supervivientes). **95 tests** (86 backend + 9 headless UI) pasando al 100%.

### Añadido
- **Botón `btn_update_db` ("🔄 Actualizar DB") en Footer de ProcessManagerView.** Añadido en la barra de acciones de la vista de procesos, cumpliendo el tamaño táctil mínimo (28 px de alto) con estilos de tema unificados (`theme.SURFACE_ALT`, `theme.SURFACE_HOVER`).
- **Conexión Funcional y Concurrente a `_force_update_db()`.** Se conecta el botón a la descarga asíncrona de `process_service.load_db_async()`, evitando congelamiento de la interfaz de usuario durante la petición.
- **Reporte Honesto y Observable en `status_label`.** Feedback inmediato que transiciona de estado: `"⏳ Descargando base de datos de procesos..."` a resultado final diferenciado: éxito (`"✅ Base de datos actualizada con éxito."`) o fallo transparente con fallback local (`"⚠️ DB no actualizada (sin red o repo no publicado). Se usa la local."`).
- **Protección contra Sobreescritura en `_render_list()`.** Al finalizar la recarga de procesos, `_render_list()` respeta `_db_update_status` impidiendo que el recuento neutro de procesos en ejecución pise el aviso observable de éxito o de fallo.
- **Test Discriminante en `run_tests.py`.** Introducido `test_process_manager_db_update_button_and_feedback` (test #95) con inspección AST de enlace al botón, guard estricto contra menciones a 'GitLab', simulación asíncrona de fallo/éxito y verificación de que `_render_list()` no destruye el banner de estado.

### Corregido
- **Desacoplamiento Total de GitLab.** Eliminadas todas las cadenas y referencias estáticas a "GitLab" en la vista de procesos, asegurando alineación completa con el repositorio oficial.

---

## CYCLE-040 - 2026-10-01

**Base de Datos & Procesos** — `TASK-050` (Descarga de DB: Constante de URL, GitHub y Fallo Observable)

> 🟢 **VERDICT FINAL: PASS** — Centralización de URL remota, reporte observable de errores y fallback local auditados con éxito por `mutation-auditor` (4/4 mutaciones eliminadas: M1, M2, M3, M4, 0 supervivientes). **94 tests** (86 backend + 8 headless UI) pasando al 100%.

### Añadido
- **Constante Centralizada de Plataforma `DB_REMOTE_URL`.** Definida en `src/woptimizer/services/process_service.py` (`https://raw.githubusercontent.com/carcheky/woptimizer/main/assets/process_db.json`), desacoplando la URL del cuerpo del método y facilitando migraciones transparentes.
- **Reporte Observable de Errores con `on_error`.** `load_db_async(callback=None, on_error=None)` ahora reporta honestamente excepciones de red y HTTP al callback `on_error(err_msg)` en lugar de tragarse el error con un log mudo.
- **Fallback Local y Blindaje Anti-Brick Offline.** Si la descarga falla por ausencia de red o repositorio remoto no publicado, `ProcessService` ejecuta de inmediato `self._load_local_db()`, manteniendo el sistema 100% operativo con la base empaquetada y el blindaje de 34 procesos protegidos del sistema.
- **Test Discriminante en `run_tests.py`.** Introducido `test_process_service_db_download_contracts` (test #94) con comprobación AST contra literales hardcodeados, simulación de fallo de red con invocación observable a `on_error`, verificación de fallback local y simulación de éxito.

### Corregido
- **Corrección Documental en `docs/ai/architecture.md`.** Actualizada la regla 3 y añadida la sección 18, eliminando la afirmación errónea de descarga activa desde GitLab y documentando el nuevo contrato de sincronización en GitHub.

---

## CYCLE-039 - 2026-10-01

**UI & Experiencia de Usuario** — `TASK-049` (Grid de Favoritos Adaptativo al Ancho de Ventana)

> 🟢 **VERDICT FINAL: PASS** — Rejilla adaptativa y responsiva en Dashboard auditada con éxito por `mutation-auditor` (4/4 mutaciones eliminadas: M1, M2, M3, M4, 0 supervivientes). **93 tests** (85 backend + 8 headless UI) pasando al 100%.

### Añadido
- **Grid Adaptativo al Ancho de Ventana en `DashboardView`.** Se implementa `_calculate_columns(num_favorites: int) -> int` que deriva dinámicamente las columnas en función de `buttons_frame.winfo_width()` y la constante centralizada `theme.ANCHO_MIN_CARD` (280 px).
- **Token Centralizado `ANCHO_MIN_CARD`.** Añadido `ANCHO_MIN_CARD: Final[int] = 280` a `src/woptimizer/ui/theme.py`, evitando números mágicos dispersos.
- **Re-grid Dinámico en Eventos `<Configure>`.** Manejador `_on_frame_configure` y `_regrid_favorites()` que reubican automáticamente las tarjetas de packs favoritos al redimensionar la ventana, sin necesidad de destruir ni recrear botones cuando la lista no cambia (`current_fav_ids == cached_ids`).
- **Filtro Estricto de Emisor de Eventos.** Se evita propagación espuria y bucles de redimensionamiento ignorando eventos `<Configure>` cuyo emisor no sea `self.buttons_frame`.
- **Liberación de Pesos en Columnas Sobrantes.** `_reconfigure_grid_columns(cols: int)` asigna `weight=1, uniform="fav"` a las columnas activas y resetea limpiamente con `weight=0, uniform=""` las columnas que queden libres al estrechar la ventana.
- **Placeholder de Estado Vacío Responsivo.** Cuando no hay favoritos marcados, `_empty_label` abarca dinámicamente todo el ancho disponible (`columnspan=cols`) adaptándose en vivo a cambios de tamaño.
- **Extracción de Destrucción de Botones.** Creación del método auxiliar `_destroy_favorite_buttons()` eliminando duplicidad de código.
- **Test Discriminante en `run_tests.py`.** Introducido `test_dashboard_favorite_grid_adaptive_contracts` (test #93) que verifica ubicación en rejilla, recolocación responsiva vía `<Configure>`, filtro de eventos ajenos, liberación de pesos en columnas y ajuste del placeholder.

---

## CYCLE-038 - 2026-10-01

**Core Services & Robustez** — `TASK-048` (Favoritos Acumulativos y Resiliencia en PackService)

> 🟢 **VERDICT FINAL: PASS** — Rediseño de favoritos acumulativos e invariantes de servicio auditado con éxito por `mutation-auditor` (5/5 mutaciones eliminadas: M1, M2, M3a, M3b, M4, M5, 0 supervivientes). **92 tests** (85 backend + 7 headless UI) pasando al 100%.

### Añadido
- **Favoritos Acumulativos en `PackService.set_favorite()`.** Se refactoriza `set_favorite(pack_id: str, value: bool) -> None` permitiendo marcar o desmarcar packs de forma acumulativa e independiente, eliminando la exclusividad global.
- **Invariante de Capas con `PackService.toggle_favorite()`.** La lógica de alternancia e inversión de favoritos se traslada íntegramente al servicio: `toggle_favorite(pack_id: str) -> bool` consulta el estado vivo en memoria, lo invierte, persiste a disco (`self.save()`) y retorna el nuevo booleano.
- **Validación Estricta de Identificadores.** `set_favorite` y `toggle_favorite` validan rigurosamente que `pack_id` no sea `None` ni una cadena vacía, lanzando `ValueError`.
- **Blindaje del Pack Gaming en `_ensure_gaming_pack()`.** Al inicializar `PackService`, si el pack `gaming` ya existe en memoria, se restablece explícitamente `is_favorite = True`, impidiendo que un desmarcado accidental elimine la tarjeta de Gaming permanentemente.
- **Retirada de `get_favorite_pack()`.** Método ambiguo singular eliminado y sustituido por `get_favorite_packs() -> List[Pack]`.
- **Pruebas Discriminantes en `run_tests.py`.** Introducidos `test_pack_service_favorites_acumulan` y `test_pack_service_favorite_contracts_and_resilience` (con guard AST verificando que `get_favorite_pack` no figure en `src/woptimizer/**`).

### Corregido
- **Delegación en `PackManagerView.toggle_favorite()`.** Actualizado para delegar en `self.pack_service.toggle_favorite(pack_id)` cuando el servicio lo soporta, manteniendo compatibilidad hacia atrás en tests existentes.
- **Corrección de semillas de test.** Actualizadas las 3 semillas de prueba en `run_tests.py` que invocaban `set_favorite` con 1 argumento (`servicio.set_favorite(..., True)`), evitando `TypeError`.

---

## CYCLE-037 - 2026-10-01

**Resiliencia & Robustez** — `TASK-047` (Resiliencia de Concurrencia y Recuperación en GamingService)

> 🟢 **VERDICT FINAL: PASS** — Sincronización multihilo y aislamiento defensivo completado y auditado con éxito por `mutation-auditor` (4/4 mutaciones eliminadas: M1, M2, M3, M4, 0 supervivientes). **91 tests** (84 backend + 7 headless UI) pasando al 100%.

### Añadido
- **Sincronización Thread-Safe en `GamingService`.** Integración de `threading.RLock()` reentrante (`self._lock`) para proteger las consultas (`get_last_closed_apps`), vaciados (`clear_last_closed_apps`), asignaciones en `execute_gaming_pack` y extracciones atómicas en `restore_gaming_session`.
- **Extracción Atómica y Anti-Carrera en Restauración.** En `restore_gaming_session()`, la lista `apps_to_restore` se extrae y vacía atómicamente bajo el cerrojo antes de llamar a `start_pack_apps`, impidiendo que múltiples hilos concurrentes (ej. desde el System Tray y el Dashboard simultáneamente) dupliquen el arranque de aplicaciones.
- **Preservación Defensiva ante Excepciones.** Si `start_pack_apps` sufre una excepción no controlada, las aplicaciones no arrancadas se re-insertan defensivamente en `_last_closed_apps` bajo el cerrojo antes de re-lanzar la excepción, protegiendo el historial contra pérdidas de datos.
- **Aislamiento en `ProcessService.start_pack_apps`.** Captura defensiva ampliada a `(OSError, Exception)` por elemento, garantizando que un fallo en la resolución o lanzamiento de una app no cancele el procesamiento del resto del lote.
- **`test_gaming_service_rlock_and_concurrency`.** Test discriminante en `run_tests.py` que valida la presencia y reentrancia del `RLock`, la exclusión mutua real mediante contención de cerrojo (liquidando M2), la sincronización concurrente entre 5 hilos, la preservación defensiva ante fallos y el aislamiento de excepciones no-OSError.

### Corregido
- **Eliminación del Superviviente M2.** Añadida prueba de contención de cerrojo con hilo bloqueante y timeouts en `run_tests.py`, asegurando que `restore_gaming_session()` no pueda extraer ni vaciar aplicaciones mientras el cerrojo `_lock` esté retenido.

---

## CYCLE-036 - 2026-10-01

**Testing & Calidad** — `TASK-046` (Pruebas de Contratos de Ciclo de Vida y Estados en Mixin Confirmable)

> 🟢 **VERDICT FINAL: PASS** — Validación completa y auditoría de contratos en mixin `Confirmable` por `mutation-auditor` (5 mutantes liquidados, 0 supervivientes). **90 tests** (83 backend + 7 headless UI) pasando al 100%.

### Añadido
- **`test_confirmable_mixin_lifecycle_and_widget_contracts`.** Prueba unitaria headless discriminante en `run_tests.py` que comprueba de forma exhaustiva:
  - 1ª pulsación: arma confirmación pendiente, muta texto a `CONFIRMAR`, estilos visuales en ámbar y retorna `False`.
  - 2ª pulsación: confirma acción (`True`), restaura texto original, aplica throttling de 300 ms (`state='disabled'` en `_timers_ui`) y restablece a `'normal'`.
  - Sustitución de token con selección cambiada (`changed_text`) actualizando el banner informativo.
  - Auto-expiración a los 3000 ms retornando a estado de reposo e informando expiración.
  - Cancelación explícita vía `_cancel_confirm()` restaurando el botón sin ejecutar.
  - Cancelación defensiva en destrucción (`cancel_on_destroy()`) cancelando handles activos de throttling en el planificador.
  - Resiliencia ante widgets destruidos (`winfo_exists() == False`) evitando errores `tk.TclError`.
  - Limpieza de reposo y timers al recrear botones vía `_forget_buttons()`.

### Corregido
- **Blindaje ante supervivientes M2b y M4.** Reforzadas las aserciones en `run_tests.py` para ejercitar la destrucción con temporizadores de throttling activos y la limpieza obligatoria del mapa de reposo (`_reposo.clear()`), eliminando el 100% de los mutantes detectados por `mutation-auditor`.

---

## CYCLE-035 - 2026-10-01

**Rendimiento & Latencia** — `TASK-045` (Optimización de Latencia en Categorización de Procesos y Memoización)

> 🟢 **VERDICT FINAL: PASS** — Optimización de categorización e invalidación atómica completada y auditada con éxito por `mutation-auditor` (0 supervivientes). **89 tests** (83 backend + 6 headless UI) pasando al 100%.

### Añadido
- **Invalidación atómica de caché al recargar la base de datos.** En `ProcessService._load_local_db()`, se ejecuta `self.invalidate_cache()` tras `self._meta_cache.clear()` para garantizar que la caché de procesos activos (`_proc_cache`) expire simultáneamente y no muestre categorías obsoletas.
- **Memoización O(1) de metadatos.** Búsqueda instantánea en `_meta_cache` (< 0.001 ms) para cualquier proceso (catalogado, fuzzy o fallback).
- **`test_process_categorization_latency_and_memoization`.** Test estrictamente discriminante en `run_tests.py` que verifica que la resolución de categorías consulta la memoria O(1) y que la recarga de base de datos invalida de manera atómica ambas cachés.

### Corregido
- **Aserción tautológica en test de categorización.** Corrección identificada por `mutation-auditor`: el test inicial usaba un proceso desconocido que caía en el fallback por defecto aun sin consultar la caché; actualizado para usar procesos catalogados y centinelas sintéticos, garantizando que el mutante sin caché es eliminado.
- **Mock de MainWindow en test headless de Tray.** Corregido el target de patch a `woptimizer.ui.app.MainWindow` en `test_tray_session_restoration_integration` para evitar inicializaciones reales de frames en entornos headless.

---

## CYCLE-034 - 2026-10-01

**Base de Datos & Procesos** — `TASK-044` (Expansión y Categorización de la Base de Procesos de Windows)

> 🟢 **VERDICT FINAL: PASS** — Expansión de base de datos de procesos completada y auditada con éxito. **88 tests** (82 backend + 6 headless UI) pasando al 100%.

### Añadido
- **7 Nuevos Procesos Reales Catalogados.** Incorporación de `rtss`, `msiafterburner`, `hwinfo64` (🔴 Overlays e Info), `galaxyclient` (🟡 Launchers Gaming), y `everything`, `gitkraken`, `postman` (🟢 Productividad) a `assets/process_db.json`. Total elevado a **96 procesos**.
- **Integridad de Esquema y Categorías.** 100% de cumplimiento en `test_process_db_schema_integrity` y `test_category_emoji_alignment` en `run_tests.py`, verificando ausencia de solapamiento con `SYSTEM_PROTECTED_PROCESSES`.

---

## CYCLE-033 - 2026-10-01

**Gaming & Telemetría UX** — `TASK-043` (Restauración de Sesión Gaming UX desde System Tray)

> 🟢 **VERDICT FINAL: PASS** — Auditoría de UI/UX y notificaciones del tray completada con éxito. **88 tests** (82 backend + 6 headless UI) pasando al 100%.

### Añadido
- **Acción del System Tray `'🔄 Reabrir aplicaciones cerradas'`.** Integrada en el menú contextual de `pystray` en `WOptimizerApp` (`src/woptimizer/ui/app.py`).
- **Restauración Asíncrona en Hilo Secundario.** La re-apertura de las aplicaciones de la sesión gaming se ejecuta de forma asíncrona mediante `gaming_service.restore_gaming_session()` en un hilo daemon `Thread(daemon=True)`.
- **Notificación Nativa en Tray.** Notificación al usuario vía `notification_service.notify_apps_launched()` informando la cantidad de aplicaciones restauradas.
- **`test_tray_session_restoration_integration`.** Test discriminante en `run_tests.py` que valida la adición de la opción al menú contextual, la llamada asíncrona a `restore_gaming_session()` y la emisión de notificaciones.

---

## CYCLE-032 - 2026-10-01

**Resiliencia & Robustez** — `TASK-042` (Robustez de Concurrencia y Captura Defensiva)

> 🟢 **VERDICT FINAL: PASS** — Auditoría de resiliencia completada con éxito. **87 tests** (82 backend + 5 headless UI) pasando al 100%.

### Corregido
- **Resiliencia en `NotificationService`.** Reemplazo del primitivo `Lock` por `threading.RLock()` para garantizar reentrancia y tolerancia a bloqueos multihilo durante invocaciones concurrentes a `attach_tray()`, `detach_tray()` y `notify()`.
- **Captura defensiva en `ProcessService`.** Ampliada la captura de excepciones en `kill_processes` y `kill_pack_apps` para manejar `psutil.ZombieProcess` y `OSError` (típicos de permisos WinError 5/87) sin interrumpir la métrica RSS liberada ni abortar la terminación de subprocesos.

### Añadido
- **`test_notification_service_rlock_and_concurrency`.** Verifica el tipo `RLock`, soporta invocaciones reentrantes y evalúa el comportamiento multihilo (5 hilos concurrentes) sin interbloqueos.
- **`test_process_service_kill_defensive_zombie_and_oserror`.** Prueba la resistencia de `kill_processes` y `kill_pack_apps` ante `ZombieProcess` y `OSError` simulados en padres e hijos.

---

## CYCLE-031 - 2026-10-01

**Testing & Calidad** — `TASK-041` (Ampliación de Cobertura de Testing y Contratos de Persistencia Pydantic)

> 🟢 **VERDICT FINAL: PASS** — Auditoría del Paso 4 completada con éxito. **85 tests** (80 backend + 5 headless UI) pasando al 100%.

### Añadido
- **`test_pydantic_extra_fields_persistence`.** Verifica la inmutabilidad y conservación de metadatos/campos extra no estándar (`extra="allow"`) en `AppData` y `Pack` tras ciclos completos de `load()` -> `save()` -> `json.load()`.
- **`test_freed_mb_calculation_precision`.** Valida la precisión aritmética del cálculo RSS (megabytes liberados) en `ProcessService.kill_processes` con mockeo de árbol de subprocesos padres/hijos.

---

## CYCLE-030 - 2026-10-01

**Rendimiento & Latencia** — `TASK-040` (Optimización de Latencia en Filtro de Búsqueda y Lectura de Packs)

> 🟢 **VERDICT FINAL: PASS** — Auditoría del Paso 4 completada con éxito. **83 tests** (78 backend + 5 headless UI) pasando al 100%.

### Añadido
- **Caché Inmutable de Lectura en 2 Capas (`PackService.get_all_packs`).** Reduce la latencia de lectura de packs a < 0.05 ms garantizando inmutabilidad estricta y aislamiento mediante `model_copy(deep=True)`.
- **Invalidación Atómica de Caché en `PackService`.** Reset atómico de caché en `save()`, `update_pack()`, `create_user_pack()`, `delete_pack()`, `set_favorite()`, `save_gaming_pack()`, `reset_gaming_pack()` y `load()`.
- **Filtrado Ultrarrápido (< 2.0 ms) en `ProcessManagerView`.** Pre-tokenizado de nombres/categorías en minúsculas para búsquedas fluidas sobre listas de 350+ procesos sin reconstruir el árbol de widgets.
- **Nuevos tests de benchmark discriminantes.** `test_pack_service_cache_invalidation_and_immutability` y `test_process_filter_performance` añadidos a `run_tests.py` (elevando la suite a 83 tests).

---

## CYCLE-029 - 2026-10-01

**Base de Datos & Procesos** — `TASK-039` (Expansión y Actualización de la Base de Procesos)

> 🟢 **VERDICT FINAL: PASS** — Validación completa. **89 procesos catalogados**, 0 solapamientos con procesos protegidos de sistema. **81 tests** en verde.

### Añadido
- **8 nuevos procesos reales catalogados en `assets/process_db.json` (+8 = 89 total):**
  - `gamingservices` (🟡 Launchers Gaming): Servicios centrales de la tienda Xbox y juegos en Windows.
  - `gamingservicesnet` (🟡 Launchers Gaming): Servicio de red auxiliar para juegos y tienda Xbox.
  - `adobecollabsync` (🟢 Productividad): Sincronizador en segundo plano de documentos colaborativos de Adobe.
  - `filecoauth` (🟢 Sincronización): Servicio de coautoría y sincronización de Microsoft Office.
  - `filesynchelper` (🟢 Sincronización): Asistente auxiliar de sincronización de archivos de OneDrive.
  - `edgegameassist` (🟢 Navegadores): Asistente u overlay flotante de juegos integrado en Microsoft Edge.
  - `hass.agent` (🟢 Productividad): Agente de integración local para domótica con Home Assistant.
  - `gameinputredistservice` (🟡 Launchers Gaming): Servicio redistribuible de entrada de mandos Microsoft GameInput.

---

## CYCLE-028 - 2026-10-01

**Gaming & Telemetría UX** — `TASK-038` (Restauración Inteligente de Apps tras Modo Gaming)

> 🟢 **VERDICT FINAL: PASS** — Auditoría del Paso 4 completada con éxito. **81 tests** (76 backend + 5 headless UI) pasando al 100%.

### Añadido
- **`GamingService._last_closed_apps` y resolución pre-kill de ejecutables.** `execute_gaming_pack` ahora resuelve las rutas absolutas `.exe` de los procesos antes de terminarlos y almacena los ejecutables únicos cerrados.
- **`GamingService.restore_gaming_session()`.** Reabre las aplicaciones capturadas durante la última sesión gaming invocando `start_pack_apps()` y limpia el historial.
- **Banner de Restauración en `DashboardView`.** Aparece dinámicamente con un botón "Reabrir Apps" para restaurar la sesión de trabajo con un solo clic tras salir de un juego.

---

## CYCLE-027 - 2026-10-01

**Resiliencia & Robustez / Deuda Técnica** — `TASK-037` (Guardas que no guardan: el alcance de un detector se deriva o no es un detector)

> 🟢 **VERDICT FINAL: PASS** — Auditoría del Paso 4 completada con éxito. **9/9 mutaciones aniquiladas por aserción**, 0 supervivientes. Recuento total derivado por `validate_docs.py`: **80 tests** (75 backend + 5 headless UI).

### Corregido
- **`_recuento_de_tests` ya emite el contrato `None` que su consumidor esperaba.** Captura `OSError` y `SyntaxError` (que incluye `IndentationError`), permitiendo que el validador emita un informe `[FAIL]` descriptivo en lugar de una excepción no capturada.
- **El guard AST del contrato de llamantes deriva su alcance dinámicamente.** En lugar de una tupla estática de dos ficheros que dejaba fuera a `process_manager_view.py`, ahora explora el árbol AST de `src/woptimizer/` identificando todos los módulos que importan `feedback`.
- **Soporte para `ast.Attribute` en el guard de llamantes.** Resuelve llamadas tanto en formato `mensaje_sin_apps(...)` (ast.Name) como `fb.mensaje_sin_apps(...)` (ast.Attribute).
- **El mensaje de pruebas huérfanas omite segmentos vacíos.** Se elimina la coletilla huérfana `invocado y NO definido: .` cuando la lista `solo_invocados` está vacía.

### Añadido
- **Prueba con árbol sintético para el guard de llamantes.** Árbol temporal con 4 módulos sintéticos que verifica que importadores con verbos cableados se marquen correctamente nombrando fichero y línea, ignorando llamadores no importadores y literales válidos como `pack.default_action`.
- **4 fixtures de validación de robustez en `validate_docs.py`.** Verifican el comportamiento del validador ante sangría rota, archivos ausentes, ejecuciones sanas y pruebas huérfanas.

---

## CYCLE-026 - 2026-09-30

**Gaming & Telemetría UX** — `TASK-035` (Telemetría y feedback visual unificado en la ejecución de packs) + `TASK-036` (la Portada avisa cuando un pack no puede hacer nada)

> 🔴 **VERDICT FINAL: PASS** — 7 rondas de auditoría de mutación, **43/43 mutaciones de `src/` aniquiladas por aserción**, 0 supervivientes. Cierre verificado por `mutation-auditor` sobre `0dd2d38`, con repo intacto. Matriz reproducible: `python _matrix_c26.py` → **30/30, 0 supervivientes**.

### Corregido (iteraciones 6 y 7 — las últimas)
- **🛡️ El segundo punto de la doble guarda de "Apagar" no tenía ni un test, y el documento afirmaba que sí.** `kill_pack` comprueba el pack dos veces —una antes de pedir la confirmación y otra después—, porque entre ambas el pack puede cambiar. El código y la documentación afirmaban que **los dos** estaban guardados; el auditor mutó el segundo y siguió vivo, y no es un mutante equivalente: con un pack que pierde sus apps entre pulsaciones, se lanzaba un apagado con lista vacía **después de haber consumido la doble pulsación**. Ahora está medido por la vía real, con un doble de servicio que devuelve un pack nuevo por lectura y cuenta las lecturas. Ese recuento es lo que distingue "midió el segundo punto" de "midió el primero por casualidad", y el auditor lo comprobó en las dos direcciones: con solo dos lecturas, la prueba se queda ciega.
- **🛡️ La tarjeta de la Portada podía prometer lo contrario de lo que hacía.** El botón anunciaba la acción con un `"KILL"` escrito a mano, congelado en el código. Ahora sale del mismo dato que decide la rama, y hay una prueba que obliga a que un Gaming Mode configurado para arrancar **diga** arrancar.
- **Un verbo desconocido ya no se convierte en silencio.** Al elegir el verbo de un aviso, cualquier palabra no reconocida caía por defecto en "apagar". Como la respuesta correcta de esa puerta *es* "apagar", un cableado equivocado era invisible. Ahora es un fallo ruidoso: un error de programación no puede esconderse detrás de un texto bonito. Está atado con una comprobación que exige que se pase siempre una acción.
- **🔴 El número de tests estaba caducado en tres ficheros y nadie se enteraba.** `STATUS.md` decía 75, `AGENTS.md` y `README.md` decían 28; la verdad era 78. El validador de documentación ejecutaba 72 comprobaciones y **ninguna miraba un número de tests**, así que daba "todo correcto" con los tres ficheros mintiendo. Corregido, y `validate_docs.py` ahora deriva el número real del propio archivo de pruebas, comprueba que no haya tests definidos sin ejecutar y compara contra los tres ficheros y contra la tabla de la guía. **De 72 a 77 comprobaciones**, y 13 de 15 pruebas de fallo negativo dan el error correcto sin reventar.

### Corregido (iteración 6)
- **La puerta de APAGAR decía "iniciar".** `PackManagerView._aviso_pack_inerte` —el helper que comparten los dos puntos donde `kill_pack` lee el pack— pasaba `pack.default_action` al formateador del aviso, así que un pack recién creado (que nace con `default_action="start"`) respondía **"no tiene apps que iniciar"** en la puerta de **apagar**: la primera acción de un usuario recién instalado. Es el espejo exacto del bug que la iteración 5 cerró en `start_pack`, y la razón es la misma: **el verbo lo decide el método que se está ejecutando, no el dato guardado del pack**. Ahora cablea `"kill"`. La suite lo mide con un pack **no gaming, vacío y `default_action="start"`** (no gaming a propósito: para que el diagnóstico del gaming inerte no se adelante y el assert muera por el verbo), y ambos mutantes —`pack.default_action` y `"start"`— mueren por esa aserción. Matriz del ciclo: **21 mutaciones, 21 muertas, 0 supervivientes**.


### Añadido
- **La Portada avisa del pack que no puede hacer nada, en las DOS ramas** (`TASK-036`). Un pack no gaming sin apps, con `default_action="kill"` o `"start"`, se avisa en `execute_pack` con el texto exacto `⚠️ '{nombre}' no tiene apps que {apagar|iniciar}. Añádelas desde el Gestor de Procesos.` en `theme.WARNING`, **antes** de `_require_double_tap`, sin worker y sin nada encolado. El verbo se mapea dentro del formateador a partir de la acción; la frase vive en un constructor privado de `ui/feedback.py` que comparten las dos familias, y el literal duplicado byte a byte de `kill_pack` desapareció.
- **Diagnóstico del Gaming Mode inerte:** un `is_gaming` con 0 apps **y** 0 categorías se avisa con `⛔ El Gaming Mode de '{nombre}' no tiene nada que cerrar: 0 apps y 0 categorías configuradas. Revísalo en el Gestor de Packs.` (ROJO inline, `theme.WARNING` en banner) en las dos puertas, también antes de la doble pulsación. Antes caía en la puerta real y pintaba `"Nada que cerrar: 0 ya cerrados"`, donde el `0` es el contador de blindaje, no de apps. Con apps **o** con categorías no avisa: cierra de verdad.
- **La rama `start` de `execute_pack` entra en la suite por el worker real.** Tres mutaciones pasaban la suite entera en verde: intercambiar `launched`/`failed`, arrancar `start_pack_apps([])`, y publicar en `_show_banner` con el nombre del pack como flag de gaming.
- **Cláusula de MB unification (`clausula_mb`):** los cuatro textos de éxito/parcial y `_last_gaming_summary` omiten la cifra con `freed_mb <= 0`, como ya hacía `format_kill_result` (fijado por `test_notification_message_formatting`).
- **`_publicar_en_banner`:** la línea de publicación del banner (fondo, texto, color, `pack` y auto-ocultado) era un bloque de cuatro líneas copiado en dos sitios y la tercera puerta iba a ser la tercera copia.
- **El Gestor de Procesos entra en el contrato de feedback honesto (`test_el_gestor_de_procesos_tampoco_miente`).** Es la **tercera** puerta de cierre (mata uno a uno lo que el usuario marcó a mano) y era la más grave: pintaba `"<tick> 0 cerrados, 0 fallidos."` con `killed == 0`. La sonda entra por `on_kill_selected` de verdad (doble pulsación, hilo secundario real, `after` encolado) y afirma texto y color exactos en los cuatro desenlaces. No mata ningún proceso: el `ProcessService` es un doble.
- **`mensaje_cierre_pack` admite un sustantivo parametrizable** (`"procesos"` por defecto, `"apps"` cuando toque), para que ninguna vista duplique el texto del formateador.
- **`DashboardView.AUTOOCULTADO_MS`** pasa de literal suelto a constante compartida.

### Corregido
- **El test afirmaba el silencio de la Portada.** `assert ... == antes_texto` con el mensaje *"se corta en silencio"* era la especificación de la mentira: una aserción que prohíbe la verdad nueva se convierte en el contrato. Invertida en el mismo commit que el aviso; lo que se mantiene es que no hay worker ni nada encolado.
- **La tercera puerta de feedback mentía en verde.** `ProcessManagerView.on_kill_selected` se alimentaba del formateador común (`mensaje_cierre_pack`) y con `killed == 0` ya no hay tick ni verde; además `skipped` dejó de confundirse con `failed` y se programa el refresco de la lista a 1000 ms. Es el bug que motivó el ciclo 26, vivo en la vista que nadie había tocado.
- **El bloque de cancelación del temporizador del banner estaba duplicado byte a byte** en `_show_start_banner` y en `_show_banner` — la puerta que el gamer ve tras pulsar "Apagar". Se extrajo a `_reprogramar_autoocultado()`: una sola verdad y un solo sitio que testear, y el escenario con reloj simulado se monta ahora en las tres puertas.
- **La guarda AST comparaba raíces, no pares.** `self.pack_service.get_all_packs()` y `self.process_service.get_process_exe_path(1)` pasaban; ahora la lista de lo permitido son pares `(raiz, metodo)`. También baja por `ast.Subscript`, por el que `self.__dict__['status_label'].configure(...)` — la misma llamada de widget por la puerta de atrás — colaba.
- **La guarda AST además miraba solo `call.func`.** Cuatro formas más de llegar a `self` la atravesaban entera: `getattr(self, 'status_label').configure(...)`, `setattr(self, '_last_gaming_summary', 'x')`, `del self._last_gaming_summary` y `self.process_service.kill_pack_apps(self.status_label)`. El detector cubre las cuatro y el doc dice **qué** cubre y qué no, en vez de prometer que "todo lo que cuelgue de `self` es infracción": el único agujero que queda abierto es el alias local.
- **La guarda AST no leía el Gestor de Procesos.** Entra `ProcessManagerView._do_load` y `on_kill_selected`; para que el worker de carga no toque la vista, la agrupación pura se movió al módulo (`_agrupar`) y la publicación va a un método (`_apply_load`).
- **Cuatro ramas sin ejecutar:** la no-gaming de `execute_pack` (nunca se ejecutaba), la **start** de `execute_pack` (tampoco), `killed == 1` (que `clasificar_cierre` con `killed > 1` degradaba a "nada") y `failed != skipped` (que hacía invisible intercambiar el orden de la 4-tupla).
- **Dos guardas preventivas sin cobertura:** `execute_pack` con pack no gaming y vacío, y `kill_pack` con pack inexistente.
- **El sustantivo solo se probaba en la rama éxito.** La fila del changelog que decía "el sustantivo se ignora" era cierta solo para una de las dos ramas que lo usan: cablear `"procesos"` a mano dejaba la suite verde.
- **Código muerto:** el alias `_show_kill_banner` (nadie lo llamaba; lo único que lo sostenía era su nombre en la lista blanca de la guarda) se borró de los dos sitios.
- **Ocho afirmaciones documentales que mentían**, corregidas en `docs/ai/ui-design-system.md`, `docs/ai/testing-guide.md` y `proposal.md`: **`len(to_kill)` donde el código dice `len(selected_keys)`** (el mismo descuadre que arregló el ciclo 26, reintroducido como documentación), una tabla de mutaciones que **no se podía reproducir**, "todo lo que cuelgue de `self` es infracción" cuando la guarda era una red, "las cinco vistas" cuando son tres clases de vista y cinco métodos, "las dos vistas" en un módulo que alimenta tres puertas, y tres que ya se habían corregido en la iteración 3.
- **`_matrix_c26.py` estaba comiteado y roto:** reventaba en la mutación 5 de 12 con `AssertionError: no se encontró el ancla` (el ancla de M6 caducó al extraer `_reprogramar_autoocultado`), y `correr()` lanzaba **2 de las 3 sondas**, así que la tercera puerta nunca estuvo en esa matriz. Reparado: anclas contra el código de hoy con **error duro** si no se encuentran, las tres sondas en cada mutación y salida ASCII. Las tablas de los changelog que declaraban "15 mutaciones, 15 muertas" (la #13 murió por un `AttributeError`, un crash, y la #15 era media verdad) se sustituyen por la salida real.

### Impacto
Ninguna puerta de feedback puede celebrar en verde un cierre que no ocurrió, las tres se alimentan del mismo clasificador y **ninguna se traga en silencio cuando el pack no puede hacer nada**. La invariante de hilos-secundarios-solo-aporta-`after(0, ...)` cubre cinco métodos de tres clases de vista, con una lista de lo permitido que significa algo y con escrito lo que no comprueba. Suite: **78 tests** (73 backend + 5 headless), y **20 mutaciones verificadas con salida real** (20 muertas, 0 supervivientes) mediante `python _matrix_c26.py`, que es ahora reproducible por primera vez.

---

## CYCLE-025 - 2026-09-30

**Testing & Calidad** — `TASK-034` (Expansión de calidad y pruebas headless de UI y modelos)

### Añadido
- **Prueba de transiciones completas de navegación headless en `MainWindow` (`test_main_window_navigation_transitions`).** Verifica el ciclo de vida completo de navegación entre vistas (`DashboardView`, `PackManagerView`, `ProcessManagerView`), la destrucción limpia de las vistas previas con `not winfo_exists()`, la actualización visual de los estados activo e inactivo de la barra de navegación (`theme.ACCENT` vs `theme.BORDER`), y el bombeo asíncrono seguro durante la carga de procesos sin bloqueos en runners headless.
- **Sonda de validación estricta y contratos en modelos Pydantic (`test_models_strict_validation_and_contracts`).** Comprueba el rechazo estricto de tipos no booleanos (`"true"`, `1`, `"false"`, `0`) en `is_favorite` e `is_gaming` mediante `strict=True`, la restricción de `default_action` al enum literal `Literal["start", "kill"]`, la retención completa de metadatos adicionales desconocidos mediante `extra="allow"` en `Pack` y `AppData`, y los valores por defecto canónicos de `ProcessInfo`. Suite total: **73 tests backend + 2 headless UI**, 100% en verde.

### Corregido
- **Eliminación de puntos ciegos en la suite de pruebas.** Se detectó que las vistas de gestión de packs y de procesos nunca eran instanciadas en la suite de integración headless previa, dejando sin cobertura la navegación entre pestañas y la destrucción de widgets en memoria.

### Impacto
Blindaje absoluto de la navegación de interfaz y de la integridad del esquema de datos. Se garantiza que ninguna versión futura degrade el formato de guardado ni coaccione tipos booleanos en silencio, manteniendo la robustez del producto sin abrir ventanas molestas durante los tests.

---

## CYCLE-024 - 2026-09-30

**Rendimiento & Latencia** — `TASK-033` (Optimización de latencia en escaneo de procesos)

### Añadido
- **Resolución bajo demanda de rutas de ejecutables (`get_process_exe_path`).** Nueva API en `ProcessService` que obtiene la ruta absoluta (`.exe`) de un proceso únicamente cuando se necesita (al asociar una app a un pack), con protección ante procesos cerrados o permisos denegados.
- **Prueba discriminante y benchmark de escaneo.** Incorporación de `test_scan_latency_and_lazy_exe_resolution` en `run_tests.py` que verifica el escaneo ligero sin `exe`, la resolución exacta del ejecutable del sistema, la degradación ante PIDs inválidos y que el tiempo medio de escaneo no supere los 25 ms. Total suite: **72 tests backend + 1 headless UI**, 100% en verde.

### Cambiado
- **Aceleración del escaneo de procesos del sistema.** Se eliminó la consulta anticipada de la ruta del ejecutable para todos los cientos de procesos del sistema en `get_running_processes()`, la cual generaba cientos de excepciones internas `AccessDenied` e I/O innecesario.
- **Construcción optimizada de objetos de proceso.** Se adoptó `ProcessInfo.model_construct(...)` en el bucle principal de escaneo, eliminando la validación redundante de más de 2.200 campos Pydantic por escaneo.
- **Precomputación del orden de categorías.** El índice de ordenación de categorías ahora se calcula una sola vez a nivel de módulo (`_CAT_ORDER_IDX`), reduciendo asignaciones de memoria en cada refresco.
- **Normalización segura de nombres de proceso.** Se reemplazó el reemplazo global de `.exe` por corte estricto de sufijo, evitando corrupciones en procesos cuyos nombres contienen la cadena `.exe` en posiciones intermedias.

### Impacto
La latencia de escaneo de procesos en frío en Windows 11 se reduce de más de **31 ms a solo ~5.5 ms (~5.6x a ~8x de aceleración)**. La interfaz responde de manera instantánea al refrescar la lista de procesos o preparar el Gaming Mode, manteniendo intacta la seguridad y el blindaje anti-brick.

---

## CYCLE-023 - 2026-09-30

**Base de Datos & Procesos** — `TASK-032` (Expansión de la base de procesos)

### Añadido
- **8 nuevos procesos del sistema catalogados (`process_db.json`).** Escaneo real en Windows que incorpora launchers, herramientas de soporte y bloatware seguro a la base de conocimiento local (total: 81 entradas):
  - `braveupdate` (🟢 Productividad, high): servicio de actualización en segundo plano de Brave.
  - `xboxgamebarwidgets` (🔴 Overlays e Info, none): widgets del Game Bar de Windows (blindado bajo barrera roja G-2).
  - `xboxpcappft` (🟡 Launchers Gaming, none): launcher y runtime de la app Xbox en PC.
  - `whatsapp.root` (🟡 Chat y Comunicación, low): cliente de mensajería UWP de WhatsApp.
  - `crossdeviceresume` (🟢 Sincronización, high): servicio de continuidad multidispositivo Phone Link.
  - `lightingservice` (🔴 Overlays e Info, none): control RGB de ASUS Aura / Armoury Crate (blindado bajo barrera roja G-2).
  - `powertoys.mousewithoutbordershelper` (🟢 Productividad, high): servicio auxiliar de Microsoft PowerToys.
  - `acpowernotification` (🟢 Productividad, high): notificador de estado de batería/corriente OEM de ASUS.
- **Sonda de integridad de esquema en `run_tests.py`.** Nueva prueba `test_process_db_schema_integrity` que valida exhaustivamente que toda entrada contenga claves normalizadas sin `.exe`, categorías pertenecientes a `PROCESS_CATEGORIES`, prioridades válidas (`high`, `medium`, `low`, `none`) y descripciones no vacías. Total suite: **71 tests backend + 1 headless UI**, todos en verde.

### Corregido
- **Cierre del mutante superviviente S1.** `mutation-auditor` identificó que una entrada podía omitir `priority` o `description` sin que los tests previos lo detectaran. La nueva sonda elimina este punto ciego, aniquilando 11/11 mutantes.
- **Blindaje anti-brick estricto verificado.** Se validó que ninguna de las 8 nuevas entradas colisione con `SYSTEM_PROTECTED_PROCESSES` (34 procesos críticos de Windows) ni pueda comprometer la estabilidad del sistema operativo.

### Impacto
La base de datos local amplía su cobertura de procesos residentes comunes en Windows 11 sin añadir peso ni llamadas externas. La integridad de datos queda asegurada mediante verificación estricta de esquema y blindaje anti-brick verificado por pruebas de mutación.

---

## CYCLE-022 - 2026-09-30

**Diseño & Front-End** — `TASK-029` (UI-001 a UI-012)

### Añadido
- **Sistema centralizado de tokens de diseño (`theme.py`).** Se introdujo una fuente única de verdad para la interfaz: colores semánticos por rol (`SURFACE`, `ACCENT`, `GAMING`, `DANGER`), escala tipográfica fija de exactamente 6 tamaños y 3 radios de borde.
- **Icono oficial de la aplicación (`woptimizer.ico`).** Se incorporó el icono multi-tamaño para la ventana principal (`root.iconbitmap`) y para la bandeja del sistema (`pystray`), eliminando el icono genérico de Python en la barra de título y el placeholder "W3".
- **Banda de telemetría permanente en reposo.** La portada (`DashboardView`) ahora muestra de forma continua el recuento de procesos activos en el sistema y el resumen del último Gaming Mode sin consultar `psutil` directamente.
- **Diálogo modal propio para crear packs.** Sustitución de `CTkInputDialog` por `NewPackModal`, un diálogo centrado y adaptado al tema oscuro que previene que la ventana de creación se abra por detrás de la app.
- **6 nuevas pruebas discriminantes en `run_tests.py`.** Verificación AST de ausencia de literales hex sueltos, completitud de tokens, cálculo de contraste WCAG AA (≥ 4.5:1), objetivos de puntero mínimos (≥ 28x28px) y validez del archivo `.ico`. Total suite: **63 tests backend + 1 headless UI**, todos en verde.

### Corregido
- **Contradicción visual del Gaming Mode (Opción A).** El Gaming Mode utilizaba antes rojo en los botones y verde en el banner de resultados. Se unificó en verde Gaming (`#1DB954`), reservando el rojo exclusivamente para acciones destructivas y señales de peligro (`⛔` y `🔴 NO CERRAR`), evitando confusiones de seguridad.
- **La etiqueta del botón Gaming ya no miente.** Se reetiquetó la información para mostrar el número de apps y de categorías automáticas afectadas (`N apps · M categorías · KILL`), reflejando la realidad del comportamiento tras TASK-025.
- **Parpadeo al refrescar la portada.** `refresh_dashboard()` ahora reutiliza los botones existentes cuando los favoritos no cambian en lugar de destruirlos y recrearlos, eliminando parpadeos y conservando el foco.
- **Estado vacío con 0 procesos.** En el Gestor de Procesos se reemplazó el mensaje equívoco `"✅ 0 apps distintas"` por un texto neutro y descriptivo.
- **Desborde de texto en pantallas pequeñas.** Se añadió ajuste de línea (`wraplength=380`) a las descripciones de procesos para garantizar una visualización óptima en pantallas de 14" y ventanas mínimas de 720px.

### Cambiado
- **Barra de navegación renovada.** Altura fija estricta de 44px con `pack_propagate(False)`, soporte hover suave y marcado del estado activo mediante acento visual y texto primario, reemplazando el relleno azul estridente anterior.
- **Cabeceras de categorías mejoradas.** Las cabeceras del Gestor de Procesos ahora cuentan con fondo visual (`SURFACE_ALT`), hover interactivo y recuento explícito de apps contenidas (`▼ Categoría (N)`).
- **Tarjeta del pack Gaming destacada.** Borde de acento verde y badge `PRESET` diferenciado para identificarlo inmediatamente frente a los packs de usuario.
- **Objetivos de puntero ampliados.** Todos los botones y herramientas interactivas cumplen la cota mínima ergonómica de `28x28px`.

### Impacto
Se completó la consolidación estética y funcional más importante desde el rediseño v3. La interfaz ya no depende de colores hardcodeados dispersos, cumple los estándares de accesibilidad de contraste WCAG AA, clarifica la semántica de seguridad (verde para gaming, rojo solo para peligro) y ofrece una experiencia fluida, consistente y profesional.

---

## CYCLE-021 - 2026-09-30

**Resiliencia & Deuda Técnica** — `TASK-028` (FIX-010 al FIX-020)

### Corregido
- **Los avisos del programa ya no se escapan a la consola.** Antes, importar la configuración configuraba el registro de mensajes como efecto secundario y llenaba el registro de avisos duplicados. Ahora se configura de forma explícita y segura con rotación de archivos (`woptimizer.log`), evitando que el archivo crezca sin límite.
- **La versión del programa está sincronizada en todos los sitios.** Se unificó la versión a `3.0.1.dev0` entre el empaquetado (`pyproject.toml`), el código fuente (`__init__.py`) y el gestor de tareas. Un nuevo test hermético comprueba que nunca vuelvan a desfasarse sin necesidad de ejecutar el programa.
- **La app ya no se cuelga si el archivo de configuración no se puede leer.** Si un archivo de perfiles está bloqueado por permisos o truncado a mitad de un carácter especial, la app ahora lo gestiona adecuadamente, avisa al usuario y recurre a la copia de seguridad `.bak` en lugar de fallar de forma silenciosa.
- **Eliminadas redundancias y variables muertas.** Se limpió código innecesario en el cierre de la aplicación y en el gestor de procesos (`is_expanded`), reduciendo deuda técnica.

### Cambiado
- **Los perfiles antiguos de la versión 2 se han archivado de forma segura.** El archivo de perfiles legacy se trasladó a `docs/archive/legacy-root-data/` junto con su documentación histórica, dejando la raíz del proyecto limpia sin perder datos del usuario.

### Añadido
- **8 pruebas nuevas en la suite.** **56 → 57 tests backend + 1 test headless de UI**, todos en verde.
- Verificación exhaustiva de 16 mutaciones con el `mutation-auditor` para asegurar que ningún fix sobreviva a regresiones.

### Impacto
Se cerró un gran bloque de saneamiento acumulado desde la migración a la v3. La auditoría demostró que 5 de las premisas iniciales sobre la deuda técnica eran inexactas (por ejemplo, `PROCESS_LIST_FILE` aún era necesaria para tests de compatibilidad y `procesos.csv` ya había sido migrado). El proyecto queda con su deuda técnica resuelta, registro rotativo limpio y suite de tests reforzada.

---

## CYCLE-020 - 2026-09-30

**Seguridad & Usabilidad** — `TASK-027` (FIX-003, FIX-004, FIX-006)

### Corregido
- **Arrancar las apps de un pack ya no es ejecutar un comando.** La lista de programas de un pack viene de un archivo que escribes tú a mano y que este programa está pensado para compartir. Se ejecutaba a través de la línea de comandos, así que una ruta con `&` o `;` podía encadenar otro comando. Ahora cada ruta se **valida antes de lanzarse**: se rechaza lo que no sea un `.exe` o `.com` dentro de las carpetas permitidas, nada se ejecuta desde una carpeta compartida en red, y nada se cuela con `..\..`.
- **El aviso de «apps arrancadas» ya no miente.** Decía que había arrancado programas que en realidad no arrancaron: el sistema de comandos no avisa cuando no encuentra un programa, asía que el contador solo sumía. Ahora el número que ves es el número real, y si algo no arranca te dice por qué en el registro.
- **Las secciones del Gestor de Procesos salían en el orden equivocado.** Los procesos que **no** debes cerrar aparecían los primeros, y los seguros, los últimos. Era el orden inverso al que sugiere el semáforo. Corregido en los dos sitios donde se ven las categorías, incluida la lista donde decides qué se cierra en el modo juego.
- **La estrella del pack ya se puede volver a pulsar para desmarcarlo.** Antes la segunda pulsación lo volvía a marcar. Ahora es un interruptor de verdad, y desmarca el pack que pulsaste (también cuando por lo que sea hay dos packs marcados).

### Cambiado
- El Gestor de Procesos guarda ahora la **ruta completa** del programa en el pack, no solo su nombre. Sigue funcionando con los packs que ya tenías guardados: los nombres sueltos se siguen buscando, pero ahora dentro de las carpetas permitidas y nunca por la ruta de búsqueda del sistema.

### Añadido
- 4 pruebas nuevas. **48 → 56 tests**, todos en verde. Cada una verificada rompiendo el código a propósito.

### Corregido en la 2.ª revisión (el `mutation-auditor` dio FAIL)
La garantía de arriba —«solo se arranca lo que está dentro de las carpetas permitidas»— **era falsa**, y está corregida:
- **Un «atajo» (junction) dentro de una carpeta permitida se colaba.** La comprobación de si una ruta está dentro de la carpeta trabajo con el texto de la ruta, sin seguir los enlaces del disco. Con un enlace puesto a mano, `C:\Windows\System32\cmd.exe` pasaba el filtro y **se ejecutaba**. Ahora la ruta se resuelve por el sistema de archivos antes de compararla, y si no se puede resolver, **no se arranca nada**.
- **Un `.exe` que en realidad es un enlace a un `.bat` se colaba.** La lista de extensiones permitidas miraba el nombre del enlace, no el del archivo de verdad; el lanzador de Windows ejecuta los `.bat` por línea de comandos. Ahora se mira en las dos.
- **Un programa instalado con las letras en mayúsculas no arrancaba.** En Windows el disco no distingue mayúsculas de minúsculas, pero la comparación sí, así que `C:\PROGRAM FILES\...` se rechazaba. Ahora las dos partes se comparan como Windows las compara.
- **Nadie vigilaba que la comparación fuera por carpetas y no por prefijo de texto.** Ahora hay una prueba que rompe el código a propósito para comprobarlo.

### Verificado rompiendo el código a propósito
**21 mutaciones, 21 detectadas** (la 1.ª revisión declaraba 27 y el `mutation-auditor` midió 29, con 1 que sobrevivía: precisamente la comparación por prefijo, ahora cerrada). Entre las 21: borrar la resolución de enlaces, hacer que la comprobación real siempre dé «dentro», mirar la extensión solo en el alias, no fallar en cerrado cuando la ruta no se puede resolver, rechazar todos los enlaces (que rompe Steam y itch.io), devolver la ruta escrita en vez de la resuelta, y volver a la ejecución por línea de comandos.

### Impacto
El encargo llegó con tres premisas y **las tres eran falsas**: el orden de categorías que pedías (por color) no es el que tenía el programa, el defecto estába en un segundo sitio que nadie señaló, y lo del favorito no era un fallo del motor sino una línea de la pantalla. Lo que sí era verdad, y pesaba más: quitar la línea de comandos **no basta**. El programa busca primero en la carpeta actual, el lanzador de Windows sí ejecuta archivos `.bat` y `.ps1`, y comprobar que una ruta sea «absoluta» no impide ni `..\..\` ni una carpeta compartida en red. Todo eso está medido y escrito en los comentarios y en la documentación, no supuesto.

Y la revisión de los tests encontró algo peor que los fallos de la primera tanda: **una de las protecciones no miraba lo que decía mirar**. La comprobación automática que prohíbe volver a lanzar por línea de comandos solo buscaba un texto concreto, así que la forma más natural de reintroducir el problema —`subprocess.Popen(..., shell=True)`— pasaba inadvertida. Ahora mira las tres formas de escribir esa llamada, y hay una prueba que se asegura de que las ve. También está escrito lo que **no** queda cerrado: nada por intérprete, nada desde una carpeta compartida en red, nada por atajos de carpeta, y **nada que no sea un programa de verdad** —un `.bat` al que le cambian el nombre a `.exe` y lo cuelgan dentro de una carpeta permitida ya no arranca—. Ese último caso estaba **mal escrito en la documentación** y ahora está **arreglado de verdad**: se defendía diciendo que Windows no puede ver ese tipo de enlace, y la verdad medida es otra: Windows sí lo ve, pero el problema no era el enlace, era que las protecciones miraban el **nombre** del archivo en vez de lo que hay **dentro**. Una copia normal, sin ningún enlace ni permisos raros, pasaba exactamente igual.

# Changelog de woptimizer

> Registro humano-legible de todo lo que cambió en el proyecto, escrito por el motor autónomo de I+D (`id-pipeline`).
> Un pase = un ciclo = una entrada. Si algo no aparece aquí, no se hizo.

- **Formato**: [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) adaptado: `Añadido` / `Corregido` / `Cambiado` / `Eliminado`.
- **Registro técnico completo** (qué se rompió, decisiones de diseño, modelos por paso): [`.taskmaster/CHANGELOG.md`](.taskmaster/CHANGELOG.md).
- **Salud del sistema y tablero**: [`STATUS.md`](STATUS.md).

---

## Resumen

| Ciclo | Fecha | Área | Qué pasó |
| [#21](#cycle-021--2026-09-30) | 2026-09-30 | Deuda Técnica | 🧹 Saneamiento de logging, sincronización de versión, archivo de perfiles legacy y cierre de mutaciones. 57 tests. |
|:---:|---|---|---|
| [#20](#cycle-020--2026-09-30) | 2026-09-30 | Seguridad | ⚡ Arrancar apps ya no es ejecutar un comando, y el orden de categorías salía al revés. Segunda revisión: un «atajo» (junction) colaba `cmd.exe`. 56 tests. |
| [#19](#cycle-019--2026-09-30) | 2026-09-30 | Resiliencia | 🛡️ La copia de seguridad dejaba de estar a salvo al arrancar la app. Cerrado. |
| [#18](#cycle-018--2026-09-30) | 2026-09-30 | Resiliencia | 🧬 Los 3 tests que pasaban con el bug puesto, cerrados y verificados. 36 tests. |
| [#17](#cycle-017--2026-09-30) | 2026-09-30 | Pipeline | 🧬 Nuevo paso: alguien rompe el código a propósito para ver si los tests se enteran. |
| [#16](#cycle-016--2026-09-30) | 2026-09-30 | Pipeline | Los 3 roles pasan a agentes reales. Aparecen en tu panel. |
| [#15](#cycle-015--2026-09-29) | 2026-09-29 | Resiliencia | 🔴 Un error al guardar te borraba la configuración entera. Blindado. |
| [#14](#cycle-014--2026-09-29) | 2026-09-29 | Gaming & UX | 🔴 El Gaming Mode no consultaba tu configuración. Conectado y blindado. |
| [#13](#cycle-013--2026-09-29) | 2026-09-29 | Base de datos | 🛡️ Blindaje anti-brick: 34 procesos de sistema protegidos. +25 entradas. |
| [#12](#cycle-012--2026-09-29) | 2026-09-29 | Gaming & UX | 🔴 5 acciones destructivas volvieron a pedir confirmación (Trampa #14). |
| [#11](#cycle-011--2026-09-29) | 2026-09-29 | Resiliencia | 🔴 El pipeline podía "completar" ciclos sin versionar nada. |
| [#10](#cycle-010--2026-09-29) | 2026-09-29 | Testing | 🔴 "Restaurar por defecto" era un no-op silencioso (`model_copy` shallow). |
| [#9](#cycle-009--2026-09-29) | 2026-09-29 | Base de datos | 🔴 6 de 8 categorías sin semáforo por emojis desalineados. |
| [#8](#cycle-008--2026-09-29) | 2026-09-29 | Gaming & UX | Notificaciones nativas de Windows (toasts). |
| [#7](#cycle-007--2026-09-29) | 2026-09-29 | Rendimiento | Cache TTL + hashmap: lecturas 5000× más rápidas. |
| [#6](#cycle-006--2026-09-29) | 2026-09-29 | Resiliencia | Cierre limpio del tray y logging por proceso. |
| [#5](#cycle-005--2026-09-29) | 2026-09-29 | Testing | Telemetría de RAM y recuperación de JSON con tests. |
| [#4](#cycle-004--2026-09-29) | 2026-09-29 | Base de datos | +4 procesos de bloatware catalogados. |
| [#3](#cycle-003--2026-09-29) | 2026-09-29 | Gaming & UX | Banner de RAM liberada tras activar un pack. |
| [#2](#cycle-002--2026-09-29) | 2026-09-29 | Resiliencia | System tray (`pystray`), backups y logging continuo. |
| [#1](#cycle-001--2026-09-28) | 2026-09-28 | Arquitectura | Rediseño v3 completo: 3 ventanas, `psutil`, `pydantic v2`. |

**Balance**: 21 ciclos · 8 bugs críticos corregidos · 2 vectores de brick cerrados · 57 tests en verde.

---

## CYCLE-019 — 2026-09-30

**Resiliencia & Robustez** · `TASK-031` · COMPLETED (3 iteraciones, 1 FAIL intermedio)

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo |
|---|---|---|---|
| Copia de la raíz al guardar | no copiarla | **killed** | `la clave raiz 'favorite' desaparecio del disco tras el save()` |
| Ídem, copiando `profiles` | copiarlo también | **killed** | `'profiles' se ha copiado al fichero escrito ... el landmine solo explotaria en el segundo arranque` |
| Validación en la rama antigua | dejarla solo en la moderna | **killed** | `[legacy/keeper]` |
| Validación en la rama moderna | dejarla solo en la antigua | **killed** | `[moderna/keeper]` |
| `is_favorite` estricto | quitar `strict` | **killed** | `_read_json dio None en vez de ValidationError` |
| Normalización de claves | `_normalizar_clave` → identidad | **killed** | `'IS-FAVORITE' se acepto como campo desconocido` |
| Umbral de error de escritura | 1 → 2 pulsaciones | **killed** | `'note' esta a distancia 2 de 'name'` |
| `extra` en la raíz | `AppData extra="ignore"` | **killed** | `quedan ['packs']: los packs se han perdido` |
| `extra` en la hoja | `Pack extra="forbid"` | **killed** | `un campo que esta version no conoce se clasifico como corrupcion` |
| Corrupción de hoja | `Pack(...)` de 5 campos | **killed** | `[legacy/keepers]: dio None en vez de PerfilCorruptoError` |
| Escritura al arrancar | `_ensure_gaming_pack` vuelve a guardar | **killed** | `load() escribio [...]: es de solo lectura` |

### Corregido
- **La copia de seguridad de tu configuración ya está realmente a salvo.** Antes, si el archivo de packs se escribía mal, la app lo detectaba, recuperaba de la copia… y acto seguido **machacaba esa misma copia** al guardar. En 7 de los 8 casos que el propio proyecto daba por protegidos. Y no pasaba cuando tú guardabas: pasaba al **arrancar**.
- **Ya no hay dos definiciones distintas de "archivo dañado".** El motor tenía una para detectar y otra para decidir si era salvable, y la documentación describía la que no se ejecutaba.
- **Un error de escritura ya no se acepta en silencio.** Si escribes `keeper` en vez de `keepers`, o dejas una mayúscula, la app lo detecta y te dice qué campo es. Antes tu lista de programas protegidos se quedaba **vacía sin avisar**, y el modo de juego pasaba a matar lo que debía proteger.
- **Los datos que no son de esta versión ya no desaparecen** al guardar por primera vez.
- Corregida la documentación que **afirmaba una garantía que era falsa**.

### Añadido
- 12 pruebas nuevas. **36 → 48 tests**, todos en verde.
- La comprobación de campos se **deriva del modelo**: si mañana se añade un campo nuevo a un pack, su error de escritura se detecta **sin tocar una sola línea de código**. Lo verificó el auditor con un campo inventado.
- 2 pruebas nuevas para valores mal escritos en los indicadores de favorito y de sistema.

### Impacto
El ciclo costó **tres vueltas**: la primera auditoría devolvió FAIL porque el implementador se había auto-declarado verde y, al romper el código, apareció un fallo que **borraba los packs del usuario del disco**. La segunda dejó tres Medianos, la tercera los cerró. Ese es el motivo de ser del paso: no valida *tu* trabajo, valida que el trabajo sea real.

**Lo que más costó no fue el código, sino las premisas.** Las tres que traía el encargo eran falsas, y la más grave apuntaba al síntoma equivocado: el agujero no estaba donde seBuscar, sino en una rotación de copias que comparaba el archivo con un método distinto del que se usaba para decidir si estaba dañado. Un arreglo siguiendo esas premisas habría escrito muchas pruebas, todas en verde, y no habría arreglado nada.

## CYCLE-018 — 2026-09-30

---


**Resiliencia & Robustez** · `TASK-030` · COMPLETED (con un hueco nuevo, abierto)

> Cierra el FAIL del ciclo #17: los 3 tests que pasaban con el bug puesto.

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo |
|---|---|---|---|
| Escritura atómica | `os.replace` → `shutil.copyfile` | **killed** | `la escritura atomica no deja .tmp` |
| Limpieza del temporal | quitar el `unlink` | **killed** | `un save fallido no debe dejar un .tmp` |
| `except` honesto | readmitir `OSError` en la tupla | **killed** | `save() no lanzo el PermissionError de la rotacion` |
| Guarda de forma | quitar `isinstance(perfiles, dict)` | **killed** | `lanzo AttributeError(...) en vez de PerfilCorruptoError` |
| `except` honesto | `except Exception` en `load()` | **killed** | `un OSError de lectura no es corrupcion ... arranco en silencio` |
| `except` honesto | readmitir `AttributeError` | **killed** | `AttributeError NO puede estar en CORRUPTION_ERRORS` |
| Publicación en hilo | `self.after(0,_apply)` → `_apply()` | **killed** | en runtime: `'processes' se publico desde el hilo 26140, no desde el principal` |

Las 7 mueren **por la aserción que dicen comprobar**, no por errores de sintaxis. La última se verificó **neutralizando el guard estático**: el test sigue detecting la regresión en runtime, y con el código intacto sigue en verde.

### Corregido
- **La escritura atómica ahora se prueba de verdad.** El test anterior solo miraba que existiera un archivo temporal, así que si la atomicidad desaparecía y el temporal nunca se creaba, pasaba por la razón equivocada. Ahora se inyecta un fallo *dentro* de la escritura y se comprueba que **tu archivo de configuración sigue intacto**, comparando bytes. Sin hilos y sin esperas.
- **Un fallo de permisos ya no se confunde con "no intentó guardar".** Ahora se comprueba el estado resultante, no un contador de llamadas.
- **`{"profiles": "texto"}` ya no tumba la app al arrancar.** Antes reventaba con un error interno al cargar la configuración. Ahora se detecta como corrupción y se recupera de la copia de seguridad.
- **El test de la vista ya no necesita abrir una ventana.** Se resuelve con un doble que anota desde qué hilo se publica, y desaparece el watchdog que mataba el proceso de tests tras 150 segundos.
- Corregido el comentario que prometía más de lo que el código cumplía.

### Añadido
- 8 pruebas nuevas. **28 → 36 tests**, todos en verde.
- Documentada la razón de por qué un error interno deliberadamente **no** se trata como corrupción: hacerlo convertiría cualquier fallo de programación en una pérdida de packs.

### Impacto
Los tres tests que el paso anterior destapó están cerrados y verificados rompiéndolos otra vez. La lección del arquitecto fue la más valiosa del ciclo: **de sus tres premisas, ninguna era cierta** — la lista de errores ya cubría los casos, un contador de llamadas no puede distinguir dos escenarios, y en Windows el permiso de archivo no bloquea la lectura. Se comprobó con mediciones, no con opiniones.

### ⚠️ Hallazgo nuevo que queda abierto
La auditoría buscando el fallo **opuesto** encontró que la validación comprueba que la *caja* de cada pack es correcta, pero no su *contenido*. Un pack con la lista de protecciones mal escrita se cuela, la copia de seguridad sana **nunca se consulta**, y un guardado posterior la **machaca**. Es pérdida de datos irreversible. Ya está registrado como `TASK-031`, con prioridad máxima.

---


## CYCLE-017 — 2026-09-30

**Pipeline** · sin cambios en la app todavía · **CERRADO por el ciclo 18** (Paso 4 = FAIL aquí)

> El Paso 4 de este ciclo devolvió **FAIL**: encontró 3 tests del ciclo 15 que pasan con el bug puesto. Es exactamente para lo que existe ese paso. **Los 3 se cerraron y verificaron en el ciclo 18** (integridad de datos: no se documentaron como deuda aceptada).

### Añadido
- **Nuevo paso en el bucle: el Paso 4, "auditar los tests".** El bucle pasa de 3 pasos a 4. Consiste en **romper el código a propósito** y comprobar que los tests se enteran. Hay un agente nuevo, `mutation-auditor`, que lo hace en una copia aparte para no tocar el proyecto.

### Por qué
Porque **`run_tests.py` en verde no demuestra nada sobre los tests**. Dice que el código hace lo que el test comprueba; no dice que el test compruebe algo. Un test que ejecuta una función y no mira el resultado da 100% de cobertura y cero verificación. Es un problema conocido en la industria —lo llaman *mutation testing*— y en este repo ya había dado resultados: un test comparaba contra un texto que el código ya no contenía, y **siempre pasaba**.

### Corregido
- Reparadas 9 referencias a `tm.py` en la documentación del repo, que seguían mandando usar un comando que **no funciona en este entorno**. Cualquier agente nuevo que lo leyera se atascaba.
- La sección de validación de la skill afirmaba cosas que el script **no comprueba**. Ahora lista lo que comprueba de verdad y lo que no.

### Impacto
El agente nuevo, en su primer minuto de vida, encontró **tres tests que pasan con el bug puesto**: uno da por buena la escritura atómica sin comprobar nunca que el archivo quede intacto si el guardado se corta a mitad; otro acepta "no intentó guardar" igual que "intentó y falló"; y un tercero no cubre los errores de tipo que sí tumban la app. **Eran fallos del ciclo anterior, dados por buenos.** Nada de eso lo habría detectado volver a pasar los tests.

### Mutaciones auditadas (Paso 4)
| Fix del ciclo 15 | Mutación | Veredicto | Motivo |
|---|---|---|---|
| Backup preventivo | `shutil.copy2` → `pass` | **killed** | `save() no creo el .bak preventivo` |
| Escritura atómica | `os.replace` + temporal → `open(w)` directo | **SUPERVIVIÓ** | 28/28 verde: el assert solo mira que exista un `.tmp`, y si ya no se crea, sigue pasando |
| Escritura atómica | `os.replace` → `shutil.copyfile` | killed | Detecta el artefacto `.tmp`, **no la garantía** de atomicidad |
| Recuperación `.bak` | devuelve `AppData()` vacío | **killed** | `no devolvio los packs del usuario: ['gaming']` |
| `except` honesto | `CORRUPTION_ERRORS` → solo `JSONDecodeError` | **SUPERVIVIÓ** | 28/28 verde: `ValidationError`/`TypeError`/`UnicodeDecodeError` sin cobertura |
| `except` honesto | reintroducir `OSError` en `CORRUPTION_ERRORS` | **SUPERVIVIÓ** | 28/28 verde: `except OSError: pass` acepta "no intentó guardar" igual que "intentó y falló" |
| Sentinela `⚪ Otros` | → `"? Otros"` (ASCII) | **killed** | `_DEFAULT_META[0] es '? Otros'`: la interrogación no es U+26AA |
| Publicación en hilo | quitar `self.after(0, _apply)` | killed | **Por el guard `ast`, no por la aserción real** — al quitarlo, el test cuelga el bucle Tcl en vez de fallar |


---

## CYCLE-016 — 2026-09-30

**Pipeline** · sin cambios en la app · COMPLETED

### Corregido
- **Los tres roles del pipeline ya no se pierden en la traducción.** El arquitecto, el desarrollador y el analista de procesos eran ficheros de instrucciones que yo tenía que traducir a mano en cada delegación. Ahora son **agentes de verdad**: aparecen en tu panel y se les delega directamente.
- **Arreglada una instrucción que llevaba tiempo rota:** la skill seguía mandando invocar un mecanismo que ya no existe. Por eso la primera vez que quise llamar al arquitecto dio error, y tuve que improvisar. Corregido en los bloques de invocación **y en las tres plantillas de prompt**, que también pedían el modelo a mano. Anotado que **no existe** para que no se repita.
- **Un fallo que introduje yo en este mismo pase:** al reescribir la sección de roles de `AGENTS.md` la renombré, y `validate_docs.py` buscaba el encabezado antiguo por nombre literal → la validación pasó a dar FAIL. Un validador atado a un título deja de validar en cuanto el título mejora. Ahora acepta ambos nombres.

### Añadido
- Cada agente lleva dentro las **lecciones de los dos últimos ciclos**, no solo el texto original: que el blindaje de nombres no protege `svchost`, que hay que comparar el nombre completo del proceso, y la trampa de los emojis.
- En `AGENTS.md`, una tabla que separa **skill** (fichero de instrucciones) de **agente** (sesión propia), porque esa distinción era justo lo que te impedía verlos.

### Verificación
No me fié de "ya están creados": le encargué al arquitecto una auditoría de prueba y acertó por su cuenta con dos detalles que le habían dado errores a otros — que la función de protección de sistema es un método de la clase y no una función suelta, y que la lista de nombres **no** protege al servicio de Windows — citando el código en ambos casos. Cero ficheros modificados: respetó su propio rol.

---

## CYCLE-015 — 2026-09-29

**Resiliencia & Robustez** · `TASK-026` · COMPLETED

### Corregido
- **Un error al guardar te borraba toda la configuración.** Si el archivo de packs se corrompía, la app lo sustituía por un pack vacío sin avisar. Y lo peor: el código que debía distinguir "archivo dañado" de "no tengo permiso para escribir" en realidad aceptaba **cualquier** error, así que un simple fallo de permisos hacía exactamente lo mismo — borrarlo todo.
- **Los packs ahora se guardan con copia de seguridad** y se recuperan solos. La escritura es atómica: si se corta a mitad, el archivo anterior sigue intacto.
- **Cerrado un fallo que podía colgar la app** al abrir el Gestor de Procesos: la lista se construía en segundo plano mientras la ventana la recorría a la vez. Ahora se construye aparte y se muestra de una sentada. El mismo descuido hacía que la lista de PIDs a cerrar estuviera desfasada.
- **Un filtro que no filtraba nada**: comparaba contra el texto equivocado al detectar procesos sin categoría, con lo que la lista-"Otros" se colaba en el resto.
- Corregida una comprobación de tests que **siempre pasaba** porque miraba un valor que ya no existía en el código.

### Documentación corregida
El registro anterior afirmaba que las copias de seguridad ya existían desde hace 12 ciclos. **No existían**: nunca se había escrito ni una línea. Corregido, y añadida una comprobación automática para que la documentación no vuelva a mentir sobre si una función existe.

### Verificación
`run_tests.py` 28/28 en verde · `verify_ui_syntax.py` EXITO · `validate_docs.py` sin fallos.
Cada test nuevo se comprobó **revirtiendo el arreglo a propósito**: los 4 fallan sin él, cada uno por su comprobación prevista.

### Nota sobre cómo se corrige esto
Al reescribir el README se descubrió que la documentación afirmaba en 5 sitios que la app "se auto-eleva para matar procesos protegidos". Al buscarlo, un análisis automático concluyó que era falso y casi se documenta así. **Era una conclusión equivocada**: el `.exe` sí se compila con `--uac-admin` (`force_build.py`), y la búsqueda fallaba porque la elevación es una opción de compilación, no código en `src/`. El README describe lo que ocurre de verdad: el ejecutable pide permisos de administrador, y al correrlo desde código no.

---

## CYCLE-014 — 2026-09-29

**Gaming & Telemetría UX** · `TASK-025` · COMPLETED

### Corregido
- **El Gaming Mode ya consulta tu configuración.** Antes, marcar categorías para cerrar y aplicaciones para proteger no tenía efecto: el motor solo cerraba la lista manual de apps y nunca miraba `keepers` ni `target_categories`. Ahora sí, y con la misma política en los tres caminos (bandeja del sistema, portada y gestor de packs).
- **Cerrada una vía que podía dejar Windows inservible.** El blindaje por lista de nombres no cubría la evaluación por categoría: `svchost.exe` y `explorer.exe` no están en esa lista y su categoría 🔴 era seleccionable. Ahora hay una **barrera de categoría roja** independiente, aplicada en dos capas.
- **Corregido un fallo silencioso que habría tumbado tus protecciones.** Los keepers se guardan como `discord.exe` pero el proceso se comparaba sin extensión, así que ni los keepers ni las apps explícitas se reconocían. Steam y Discord habrían muerto siendo "protegidos".
- El Gaming Mode configurado **solo por categorías** ya no se ignoraba (dos salidas mudas lo bloqueaban).

### Añadido
- `test_execute_gaming_pack_integration`, verificado **por mutación**: al desactivar la barrera a propósito, el test falla admitting `svchost.exe`. No es un test decorativo.

### Verificación
`run_tests.py` 24/24 en verde · `verify_ui_syntax.py` EXITO · revisión independiente: **PASS**.
Commits pendientes: el entorno bloqueó el versionado durante este pase.

---

## CYCLE-013 — 2026-09-29

**Base de Datos & Procesos** · `TASK-024` · COMPLETED · `0ad23bb`

### Añadido
- **Blindaje anti-brick**: 34 procesos de Windows marcados como indestructibles, aplicados por **tres vías** (al cargar la base, al resolver metadatos y en el propio cierre). El motivo: el pack lo escribes tú a mano, así que un `lsass.exe` en un pack también tiene que ser indestructible.
- **+25 entradas** de bloatware real (48 → 73): PowerToys, consumo de Armoury Crate, servidores de lenguaje, audio y actualizadores.

### Impacto
Se cierra la vía por la que la app más se dañaba a sí misma. Un proceso de la base solo se cierra si su categoría lo permite, aunque escribas su nombre a mano.

---

## CYCLE-012 — 2026-09-29

**Gaming & Telemetría UX** · `TASK-023` · COMPLETED

### Corregido
- **5 acciones destructivas volvieron a pedir confirmación.** La reescritura a v3 perdió el patrón de doble pulsación: "Cerrar Seleccionados" mataba N procesos de un solo clic, y en la portada los packs se colocan de dos en dos, así que el botón Gaming tenía un pack vecino pegado.
- El Gestor de Packs no daba **ningún feedback** al borrar un pack protegido: fallaba en silencio.

### Añadido
- `ui/confirmation.py` con `DoubleTapGuard`, en un solo sitio y reutilizado por las tres vistas.
- **Trampa #14** documentada: nunca un diálogo modal en la ventana principal, porque se abre *detrás* y parece que la app está rota. La seguridad la da la segunda pulsación, no el diálogo.

---

## CYCLE-011 — 2026-09-29

**Resiliencia & Robustez** · `TASK-022` · COMPLETED

### Corregido
- **El pipeline podía "completar" ciclos sin versionar nada.** `git_safe_commit.py` salía con código 0 ante cualquier fallo de commit, así que el registro guardaba hashes que podían no existir y nadie se enteraba.
- Un texto de git (`"nothing to commit"`) se usaba para decidir, y **ese texto cambia con el idioma del sistema**: en un Windows en español nunca aparece.

### Añadido
- Wrapper reescrito con códigos de salida honestos y flag `--verify`.
- `dist/woptimizer.exe` regenerado (25,65 MB).

---

## CYCLE-010 — 2026-09-29

**Testing & Calidad** · `TASK-021` · COMPLETED

### Corregido
- **"Restaurar por defecto" no hacía nada.** `model_copy()` de Pydantic v2 es *shallow*, así que las listas del pack Gaming se compartían con el global y la UI las modificaba en silencio.
- +8 tests para invariantes que se habían quedado sin cubrir tras la migración v2→v3.

---

## CYCLE-009 — 2026-09-29

**Base de Datos & Procesos** · `TASK-020` · COMPLETED

### Corregido
- **6 de las 8 categorías perdían su semáforo** por emojis desalineados entre la base y la configuración: todos esos procesos caían en "? Otros" **sin indicador de seguridad**. Un desajuste de un carácter en un emoji.
- El semáforo se evaluaba por prioridad antes que por categoría, pintando de amarillo lo que era rojo.

### Añadido
- +14 procesos: navegadores, launchers y herramientas de IA.

---

## CYCLE-008 — 2026-09-29

**Gaming & Telemetría UX** · `TASK-019` · COMPLETED

### Añadido
- **Notificaciones nativas de Windows**: al cerrar procesos o activar un pack, sale un toast del sistema aunque la ventana esté oculta. Funciona con la app minimizada en la bandeja.

---

## CYCLE-007 — 2026-09-29

**Rendimiento & Latencia** · `TASK-018` · COMPLETED

### Cambiado
- Búsqueda de metadatos por **hashmap O(1)** en vez de lista lineal, y **caché de 2 segundos** para no re-escanear el sistema en cada pulsación.
- Las lecturas cacheadas bajaron de ~15 ms a **0,003 ms** (unas 5000×). Cerrar procesos invalida la caché.

---

## CYCLE-006 — 2026-09-29

**Resiliencia & Robustez** · `TASK-017` · COMPLETED

### Corregido
- El icono de la bandeja no se guardaba, así que el cierre limpio era imposible.
- Cierre de apps sin logging: los fallos individuales pasaban desapercibidos.

---

## CYCLE-005 — 2026-09-29

**Testing & Calidad** · `TASK-016` · COMPLETED

### Añadido
- Tests de memoria liberada, de protección del pack Gaming y de recuperación ante un JSON corrupto.

---

## CYCLE-004 — 2026-09-29

**Base de Datos & Procesos** · `TASK-015` · COMPLETED

### Añadido
- 4 procesos de telemetría y sincronización catalogados.

---

## CYCLE-003 — 2026-09-29

**Gaming & Telemetría UX** · `TASK-014` · COMPLETED

### Añadido
- Banner en la portada: **cuántos procesos se cerraron y cuántos MB de RAM se liberaron** tras activar un pack. Verde para Gaming, azul para el resto.

---

## CYCLE-002 — 2026-09-29

**Resiliencia & UX** · `TASK-012` · COMPLETED

### Añadido
- **System tray**: cerrar la ventana la minimiza a la bandeja en vez de salir, con menú rápido.
- Rotación de copias de `profiles.json` y logging continuo en `woptimizer.log`.

---

## CYCLE-001 — 2026-09-28

**Arquitectura & UI** · `TASK-001..009` · COMPLETED

### Añadido
- **Rediseño completo a v3**: tres ventanas (Portada, Packs, Procesos) con `CustomTkinter`.
- Backend migrado de PowerShell/WMI a **`psutil`**.
- Persistencia con **`pydantic v2`**.

## CYCLE-049 - 2026-10-02

**Documentación & Arquitectura** — `TASK-060` (check 8 de `validate_docs.py`: la Deuda Técnica Conocida exige un ancla resoluble en toda fila viva) · `openspec/changes/2026-10-02-check-deuda-con-anclas/`

> **Esta entrada va al FINAL del fichero a propósito.** El registro va de más nuevo a más viejo, y anteponerla desplazaría las **26 citas `fichero:línea`** a `.taskmaster/CHANGELOG.md` que existen hoy en 11 ficheros —`CHANGELOG.md` entre ellos— y las dejaría caducas de un plumazo. Agregarla al final no desplaza ninguna. Está medido y escrito, para que se lea como decisión y no como descuido.

### Añadido

- **El check 8 de `validate_docs.py`**: `_comprobar_deuda_con_anclas(root, errors, ok)`, cableado entre el check 7 y el `return` de `validar(root)`. Toda fila **viva** de la sección `## Deuda Técnica Conocida` de `STATUS.md` necesita un ancla resoluble cuya verdad se derive de **fuera** del panel, por cinco fuentes: la ruta citada existe, la cita trae identificador y el fichero lo contiene, `TASK-NNN` tiene estado legible, `CYCLE-NNN` tiene entrada en un registro, y la cifra que declara coincide con el recuento derivado con `ast`. Las filas marcadas `CERRADA` quedan exentas, y una fila viva no puede apoyarse **solo** en una `TASK` ya cerrada. **Ronda de cierre: el cierre paso de tres condiciones a cinco.** La quinta exige que el id que cierra la fila esté **cerrado** —una `TASK` en `completed`, un `CYCLE` con entrada en uno de los **dos changelogs**—, no solo que exista: nombrar trabajo **pendiente** no cierra nada. Y el rechazo del panel como ancla se amplió de la identidad de **ruta** a la identidad de **fichero** (`st_dev` + `st_ino`), porque un **enlace duro** comparte el fichero con el panel y no cambia de nombre, luego se colaba entero. `os.path.normcase` se **quitó** de la comparación: no hacía nada en ninguna plataforma.
- **El reparto `94 backend + 10 headless` se deriva en el check 7** con `ast`, contando las llamadas `test_*()` antes y desde el marcador estructural de `run_tests.py`. Hasta el ciclo #48 se comprobaba a mano, y la propia fila 9 del panel lo decía. Si el marcador no aparece, se acusa el motivo literal: **nunca `0 + 0` en verde**.
- **Un test con treinta escenarios** (`test_la_deuda_exige_un_ancla_resoluble_en_toda_fila_viva`) sobre un `STATUS.md` sintético en `tempfile.mkdtemp()`, con el total de tests derivado con `ast` **del árbol del test**, nunca del repo real. La primera ronda de cierre los subió de 19 a 25 (`r`, `s`, `t`, `u`, `v` y `w`) y esta ronda los sube de 25 a **30** con `x` (el cierre apunta a una `TASK` pendiente), `c3` (un `CYCLE` que solo está en el journal está en vuelo), `h2` (un enlace duro al panel) y los dos controles negativos `y` y `n2`, que **no matan nada** y archivan el residuo declarado. **El número de tests no cambió**: sigue en 104, porque los escenarios son filas de una tabla.

### Corregido

- **La sección que gobierna el Paso 1 del bucle no tenía ninguna vigilancia.** `validate_docs.py` no contenía ni una coincidencia de la palabra «Deuda», y por eso 8 de 9 mutaciones del panel sobrevivieron en el ciclo #48. Ese PARTIAL era el defecto, y esto es su arreglo de fondo.
- **`STATUS.md:91` se quedaba sin ancla resoluble** y ahora cita el fichero donde vive `CORRUPTION_ERRORS` (`src/woptimizer/services/pack_service.py`). Su redacción original se conserva entera: la fila **ganó** el comprobable que le faltaba.
- **Los cuatro ficheros que declaran el recuento** —`STATUS.md`, `AGENTS.md`, `README.md` y la tabla de `docs/ai/testing-guide.md`— están en **104**, y `docs/index.md` también.

### Documentado

- **Veintitrés límites residuales** del check 8 en `docs/ai/sandbox-rules.md`, todos medidos: la gravedad **se lee del emoji** y bajar la 🔴 a 🟡 **sí salta el suelo** (lo que queda no es que el suelo se evada, sino que hoy **no tiene fila víctima**); una cita rota solo se acusa cuando es decisiva; y reabrir una fila cerrada sigue en verde si tiene otras fuentes vivas. Se escriben, no se omiten. **La ronda de cierre reescribió el 4, el 18, el 19 y el 5, y añadió el 21, el 22 y el 23** — y lo hizo porque **cuatro de ellos tenían una medición falsa dentro**, no porque el código hubiera cambiado: el 4 afirmaba que una sola fila declara 🔴 cuando `_gravedad_declarada` la devuelve en ocho, el 18 hablaba de «siete exentas en rojo» cuando son seis y un `FAIL`, y la justificación de `normcase` era falsa en POSIX y en Windows. Una conclusión correcta sostenida por una medición falsa es la forma más barata de perder un ciclo entero.
- **La cifra vigente añadida a las filas 100 y 101** por *añadido*, nunca por sustitución: una fila que declara un número de tests tiene que llevar dentro el número que el validador deriva, o el check 8 la acusa de autoderivarse a sí misma.

### Outcome

- Tests: **103 → 104**, 0 fallos. `verify_ui_syntax.py` EXITO (8/8). `validate_docs.py` **115 OK / 0 FAIL** con el check 8 activo. **Ronda de cierre: se cerraron tres cosas y se declararon tres residuos más.** G2f' (`— **CERRADA en TASK-059**` al final de la fila 88) pasa de `8/7/33, 0 FAIL` a `7/8/35, 0 FAIL`; el enlace duro al panel pasa de `0 FAIL` a **2 FAIL**; y la negación en minúscula sobre una `TASK` **pendiente** muere por la misma puerta que G2f', porque era el mismo ataque. Lo que **no** se pudo cerrar, y se declara: nombrar un id **ya cerrado** sigue eximiendo (`8/7/33, 0 FAIL`), un `NO` ajeno en la prosa reabre una fila cerrada (`6/9/39`, `0 FAIL`), y la negación en minúscula sobre un id ya cerrado tampoco se ve. Cada fix lleva su test **comprobado rompiendo el fix**: cinco mutantes del validador, cinco muertes.
- `src/woptimizer/**` con **cero** cambios. Los contratos del arquitecto y `tasks.json` intactos salvo el `status` de la tarea.
