# Propuesta — El conjunto de vistas del guard de workers se deriva, no se escribe a mano

**Ciclo:** 68 · **Rama:** `beta` · **Tarea:** TASK-082 · **Módulo:** `run_tests.py` (tooling, suite)
**Cero ediciones bajo `src/woptimizer/`.**

---

## 0. El encargo y su respuesta en una frase

> ¿Dónde MÁS se cumple la propiedad del ciclo 67, cuál es la siguiente más grave, y
> dónde debe vivir el guard de forma AC-5?

**La propiedad se cumple en 41 enumeraciones; 2 de ellas son derivables HOY y son el
MISMO conjunto escrito CUATRO VECES — y solo una tiene contraprueba. La siguiente más grave
es `VISTAS_INVENTARIADAS` (`run_tests.py:9410`): MEDIDO en verde, una vista nueva en disco
no la vigila nadie. Y el guard de forma AC-5 se queda donde está (`run_tests.py`), porque
moverlo a `verify_ui_syntax.py` cuesta +3,59 s medidos y confunde dos contratos en un
código de salida.**

---

## 1. La propiedad (NO se reformula: se aplica)

Del ciclo 67 (`openspec/changes/2026-10-19-verificacion-ui-alcance-derivado/proposal.md`):

> Un guard es **VACIABLE** cuando el conjunto de sujetos que mira está escrito como
> enumeración literal dentro del propio guard, y ese conjunto es un dato **DERIVADO** del
> sistema de ficheros. Enumeración y conjunto son dos fuentes de verdad que nadie ata.

TASK-081 la cerró en **un** sitio (`verify_ui_syntax.py`). Este ciclo la **mide** en los
demás y **cierra una** de las que quedan.

---

## 2. Inventario clasificado — recuento real

Barrido **independiente** con `ast` (NO se reutiliza el detector del repo: medir el guard
con su propia regla sería medirlo con su propia regla). Criterio: todo literal de cadena
que parece una ruta, agrupado en el contenedor literal (`List`/`Tuple`/`Set`/**`Dict`**) que
lo contiene. Se escanean los `.py` **versionados** del repo; `basura/` queda fuera (está en
`.gitignore:79` y es la cuarentena del dueño).

**Recuento: 41 contenedores con ≥2 literales de ruta.**

| Clase | Nº | Qué es |
|---|---:|---|
| **(a) DERIVABLE HOY** — el conjunto es el contenido de un directorio que el sistema de ficheros ya conoce; `rglob` lo devuelve **sin perder nada** | **2** | `run_tests.py:9410` · `run_tests.py:27617` |
| **(b) SELECCIÓN / NO DERIVABLE** — el conjunto es una *elección* dentro de un directorio, o mezcla directorios, o son nombres históricos | **22** | ver tabla abajo |
| **(c) OTRA COSA** — argv, flags, regex, rutas falsas de fixture, código sintético | **17** | 5 de ellas en `docs/archive/legacy-root-tests/` (código archivado) |

### Las dos de la clase (a) — el hallazgo

| # | Fichero:línea | Ambito | Conjunto | ¿Contraprueba derivada? |
|---|---|---|---|---|
| A1 | `run_tests.py:9410` | `test_los_workers_de_pack_solo_publican_por_after` | `("dashboard_view.py", "pack_manager_view.py", "process_manager_view.py")` | ❌ **NINGUNA** |
| A2 | `run_tests.py:27617` | `test_ninguna_vista_programa_after_a_mano` | **el mismo conjunto, otra vez** | ✅ `run_tests.py:27683` (`assert en_el_disco == set(VISTAS)`) |

**El mismo conjunto, escrito dos veces, en dos funciones distintas, y solo una de las dos
veces está atada al disco.** El helper que deriva (`_vistas_del_disco`, `run_tests.py:27652`)
está **anidado dentro** de la función A2 (sangría de 4 espacios), luego **no se puede
reutilizar** desde A1: esa es la razón *mecánica* de que la segunda copia se escriba a mano.

### Y son **CUATRO** copias, no dos — una de ellas ya es redundante

El conjunto de vistas está escrito **cuatro veces** en el repo:

| # | Dónde | Forma | ¿Atada al disco? | ¿Redundante? |
|---|---|---|---|---|
| 1 | `run_tests.py:27617` `VISTAS` | tupla de 3 | ✅ `:27683` | — |
| 2 | `run_tests.py:27622` `RUTAS_VIGILADAS` | **dict** de 4 (3 vistas + `confirmation.py`) | ❌ | **SÍ, sus 3 entradas de vista** |
| 3 | `run_tests.py:27631` `ESPERADOS` | `frozenset(VISTAS) \| {"confirmation.py"}` | ❌ (derivada de 1) | deriva de la 1 |
| 4 | `run_tests.py:9410` `VISTAS_INVENTARIADAS` | tupla de 3, **en el OTRO guard** | ❌ **NINGUNA** | — |

⚠️ **La entrada 2 es ruido muerto, MEDIDO por lectura:** el guard usa
`RUTAS_VIGILADAS.get(nombre, os.path.join("views", nombre))` (`run_tests.py:27697`), y el
**default ya es exactamente** `os.path.join("views", nombre)`, que es lo que aportan las
tres entradas de vista. Las tres solo se diferencian de `confirmation.py`, que sí está en
`ui/` y no en `ui/views/`. Es decir: **tres de las cuatro copias del conjunto no aportan
información que el código no derive ya**.

> Y el comentario que acompaña a la copia 3 lo dice sin verlo:
> `run_tests.py:27628-27630` — *«si las dos listas se derivan una de la otra, cambiar el
> alcance es cambiar la verdad, y la verdad es lo que el guard no puede mover solo.»*
> La frase describe el problema exacto que la copia 4 (`VISTAS_INVENTARIADAS`) sigue
> teniendo sin resolver.

### La clase (b), las que importan

| Fichero:línea | Conjunto | Por qué NO es derivable |
|---|---|---|
| `run_tests.py:13209` | 11 ficheros de raíz (esqueleto del validador) | **Selección**: un `rglob` traería 16 más, incluido `saved_processes.json` (artefacto de runtime). MEDIDO en el ciclo 67. **Bomba de mantenimiento, ya declarada (A12).** |
| `run_tests.py:28993` | `("run_tests.py", "validate_docs.py", "verify_ui_syntax.py")` — **el alcance del propio AC-5** | Selección de qué scripts son *guards*. Ver §3: es **vacuable** (MEDIDO). |
| `run_tests.py:17677` | 5 ficheros de raíz (testigos de no-contaminación) | Selección: el conjunto no es "lo que hay en la raíz" |
| `run_tests.py:12700` · `:7180` | 11 y 3 nombres de tests legacy | **Históricos**: están en `docs/archive/legacy-root-tests/`, no en el árbol vivo |
| `run_tests.py:8204` · `:8348` | 4 rutas de `src/woptimizer/ui/**` | Selección de 4 de 22. **Ya justificadas por escrito** (TASK-081 AC-5) |
| `run_tests.py:6154` | 2 de las 3 vistas | Subconjunto con una razón semántica ("las que manejan categorías") |
| `validate_docs.py:1303` | 5 prefijos de ancla | Selección de prefijos, no espejo de un directorio |
| `validate_docs.py:1698` · `:1862` | 2 y 3 registros de ciclos | Registros, no ficheros del árbol |
| `validate_docs.py:2429` · `:2470` | ficheros base de OpenSpec | **Contrato**, no espejo: `proposal.md`/`tasks.md` son lo que la spec exige |
| `validate_docs.py:2699` · `run_tests.py:7239` · `:26126` | `architecture.md`, `data-models.md` | 2 de los 7 ficheros de `docs/ai/` |
| `_chk.py:2` | 7 rutas en 3 directorios | Script suelto **trackeado** en la raíz (resto declarado en el ciclo 67) |

### La clase (c)

`run_tests.py:20692` · `:20826` (`/c` + `build.bat`: argv), `run_tests.py:7605`
(sintético dentro de un test), `run_tests.py:12074` · `:12107` · `:12117` · `:21379` ·
`:25450` (rutas falsas de fixture), `validate_docs.py:124` · `:125` · `:126` (**regex**,
no rutas), `verify_app.py:22` (argv de PowerShell), y 5 en `docs/archive/legacy-root-tests/`.

---

## 3. ¿Dónde debe vivir el guard de forma AC-5? — DECISIÓN MEDIDA

La pregunta del encargo: si la regla viviera en el propio `verify_ui_syntax.py`,
"quien deriva sería quien vigila". **Medido, la respuesta es NO: se queda en `run_tests.py`.**

### 3.1 El coste, medido

| Medición | Valor | Cómo |
|---|---:|---|
| `ast.parse` de `run_tests.py` (1 540 260 B) | **3 586,7 ms** | `ast.parse` medido sobre el fichero real |
| `ast.parse` de `validate_docs.py` (145 355 B) | **33,7 ms** | ídem |
| `ast.parse` de `verify_ui_syntax.py` (3 180 B) | **0,3 ms** | ídem |
| `python verify_ui_syntax.py` hoy | **0,111 · 0,114 · 0,155 s** | 3 corridas reales |

Si el guard de forma viviera en `verify_ui_syntax.py`, ese script tendría que parsear
`run_tests.py`: **+3,59 s**, o sea **×25** sobre su runtime actual, en el comando que
`AGENTS.md:71` le pide al usuario (`python verify_ui_syntax.py`).

### 3.2 Por qué el coste NO es lo único (tres razones más)

1. **Contrato.** `release.yml:86-87` nombra el paso *"Sintaxis estatica de la UI"*. Hoy su
   código de salida significa una sola cosa: *los módulos de `src/woptimizer/` no parsean*.
   Si el guard de forma viviera ahí, el mismo código de salida significaría además
   *"algún script del toolchain tiene una enumeración escrita a mano"*: dos contratos en
   un `exit`, y la puerta de sintaxis pasaría a ser guard de forma de `run_tests.py` y
   `validate_docs.py`, que no son suyos.
2. **El invariante de que un guard lo vigila OTRO.** La disposición actual del repo ya lo
   cumple: `verify_ui_syntax.py` es el sujeto de AC-1 (`run_tests.py:28711`), que lo vigila
   desde `run_tests.py`. Si el guard de forma viviera en `verify_ui_syntax.py`, ese fichero
   llevaría dentro su propio conjunto de sujetos (una literal) y tendría que vigilarse a
   sí mismo: **la clase que el guard existe para cazar se mudaría un nivel arriba, al
   guard**.
3. **El orden en CI es latencia, no agujero.** `release.yml:87` (sintaxis) y
   `release.yml:116` (`run_tests.py`) están **en el mismo job**. Que el rojo salga un paso
   antes o después cambia *cuándo* se ve, no *si* se ve.

### 3.3 El acoplamiento, medido

- `run_tests.py` **no importa** `verify_ui_syntax.py`: lo **parsea con `ast`**
  (`run_tests.py:28735-28737`). **No hay dependencia circular**, hoy ni después: nadie
  importa a nadie, los dos leen texto.
- Si el guard se mudara, `verify_ui_syntax.py` parsearía `run_tests.py` y `validate_docs.py`,
  y `run_tests.py` seguiría parseando `verify_ui_syntax.py`: mutual, pero **no circular**.

### 3.4 Lo que la medición sí destapa (y NO se arregla aquí)

**El alcance del propio AC-5 es una literal y nadie lo deriva.**
`run_tests.py:28993` → `ficheros = ("run_tests.py", "validate_docs.py", "verify_ui_syntax.py")`.

**MEDIDO (E2):** reduciendo ese conjunto a dos ficheros, el guard **sigue en VERDE** y
imprime `0 violaciones en 2 ficheros`. El guard de forma **se puede vaciar en silencio**
editando una línea, y ningún assert lo nota. Hoy no pierde nada (no hay enumeraciones de
`src/` en `validate_docs.py`), luego es **agujero latente**, no verde falso: es el **#2 del
ranking**, y se formaliza en su propio ciclo.

> ⚠️ La trampa que el repo ya ha pagado dos veces: **no** se arregla metiendo
> `validate_docs.py` en una lista muda de permitidos. Se arregla derivando o declarando el
> alcance, como se explica en §4.

---

## 4. El ítem elegido y su lugar en el ranking

### 4.1 El criterio, aplicado

> *«¿Se manifestaría si el código o el documento estuvieran mal?»*
> Un fallo que da **ruido** (rojo con fichero y línea nombrados) es **bomba de
> mantenimiento**, no agujero. Un fallo que da **verde falso** es **agujero** y va primero.

### 4.2 Ranking MEDIDO

| # | Candidato | ¿Verde falso o ruido? | MEDIDO |
|---|---|---|---|
| **1** | **`VISTAS_INVENTARIADAS` (`run_tests.py:9410`)** | **VERDE FALSO** | E1a/E1c **VERDE**, E1b **ROJO** (§5) |
| 2 | El alcance de AC-5 (`run_tests.py:28993`) | **agujero latente** (hoy no pierde nada) | E2 **VERDE** al reducirlo a 2 ficheros |
| 3 | El esqueleto del validador (`run_tests.py:13209`) | **RUIDO** — todas las celdas dan ROJO con fichero y línea | MEDIDO en el ciclo 66 (A12) |
| 4 | Re-enumerar `verify_ui_syntax.py` por **basenames** | **RUIDO** — AC-1 **y** AC-3 dan ROJO | E3 (§5) |
| 5 | `validate_docs.py:1862` (registros de ciclos) | **RUIDO** — quitar uno deja la fila sin ancla → ROJO | lectura de código |
| 6 | `validate_docs.py:1303` (prefijos de ancla) | **RUIDO/latent** — la ruta tal cual resuelve igual | lectura de código |
| 7 | `_chk.py:2` · `_chk2.py` · `_matrix_c26.py` | **RESTO**: scripts sueltos trackeados en la raíz; su enumeración se pudre en silencio porque **nadie los ejecuta** | raíz del repo |

**Se formaliza el #1.** Los #3–#7 son ruido o restos y se declaran, no se arreglan aquí:
formalizarlos sería **un error de diagnóstico**.

### 4.3 El defecto, en una frase

> `test_los_workers_de_pack_solo_publican_por_after` abre **los ficheros que alguien
> escribió a mano**, y ese conjunto es **el contenido de `src/woptimizer/ui/views/`**, que el
> sistema de ficheros ya conoce y que **el guard hermano ya deriva** — pero el helper que
> lo deriva está **anidado en la función del hermano** y no se puede reutilizar.
>
> Y el conjunto está escrito **cuatro veces**: `VISTAS`, `RUTAS_VIGILADAS`, `ESPERADOS` y
> `VISTAS_INVENTARIADAS`. **Una sola** de las cuatro está atada al disco.

---

## 5. La prueba: verde falso MEDIDO, con control positivo

Cámara desechable en `%TEMP%`, copia del repo sin `.git`, `src/` real. La vista falsa es
una vista cuyo worker **toca un widget desde el hilo secundario y no publica por la
puerta**: es exactamente lo que el guard prohíbe.

| Experimento | Escena | Resultado MEDIDO |
|---|---|---|
| **E1a** | Vista mala **en disco** y en `VISTAS` (`:27617`), **NO** en `VISTAS_INVENTARIADAS` (`:9410`) | guard de workers → **VERDE** («10 cuerpos, 10 publicaciones vigiladas») — **no la ve** |
| **E1b — CONTROL POSITIVO** | La **misma** vista entra en `VISTAS_INVENTARIADAS` | guard de workers → **ROJO**: `el worker toca la vista fuera de self.after(0, ...): VistaMala.cargar:L9 self.status_label.configure(...) desde el hilo secundario` |
| **E1c — FLUJO REAL** | El dev añade la vista a `VISTAS` y arregla el `== 4` → `== 5` (que es lo que le **fuerza** el guard hermano) y **no toca** `VISTAS_INVENTARIADAS` | **los dos guards en VERDE** y la vista con la infracción **sin auditar** |
| **E2** | El alcance de AC-5 reducido de 3 a 2 ficheros | AC-5 → **VERDE** («0 violaciones en 2 ficheros») |
| **E3** | `verify_ui_syntax.py` enumera su sujeto **por basenames** | AC-1 → **ROJO** (por la aserción de «deriva»), AC-5 → **VERDE** (su llave es `src/woptimizer/**.py`, no ve basenames), AC-3 → **ROJO** → **ruido, no agujero** |

**El guard discrimina sobre la LITERAL, no sobre el DISCO.** Eso es el agujero.

---

## 6. Diseño

### 6.1 La decisión

**El conjunto que el guard abre se deriva; la literal se queda como DECLARACIÓN que se
compara con el derivado.** Es el patrón que el repo ya probó en TASK-079 (R2b) y que
funciona: `run_tests.py:27674-27687` deriva, abre lo derivado y **exige** que la
declaración coincida.

> No se sustituye la literal por el derivado y ya: eso **perdería el aviso**. Si una vista
> nueva aparece en disco, el guard tiene que **nombrarla en rojo** (ruido útil) y
> **además auditarla** (que es el agujero que se cierra).

### 6.2 El algoritmo

1. **Hoist** de `_vistas_del_disco` (`run_tests.py:27652`) a **ámbito de módulo**, con su
   docstring. Deja de estar anidado en `test_ninguna_vista_programa_after_a_mano` y pasa a
   ser la **única** fuente de verdad del conjunto de vistas para **los dos** guards.
   - El directorio se deriva de la **ubicación del propio módulo** (`Path(__file__)`), no de
     una literal de ruta escrita a mano: hoy está escrito como
     `os.path.join(raiz_repo, "src", "woptimizer", "ui", "views")` en dos sitios
     (`run_tests.py:9311` y `:27676`).
2. **`VISTAS_INVENTARIADAS` deja de ser la fuente.** En `run_tests.py:9410`:
   - `vistas_en_disco = _vistas_del_disco(...)` → **derivado**.
   - `assert set(VISTAS_INVENTARIADAS) == vistas_en_disco` → **el rojo que nombra la
     diferencia** (ruido: una vista nueva o una vista que se ha ido).
   - el `for` abre **`vistas_en_disco`**, no la literal → **la vista nueva se audita aunque
     nadie la haya apuntado en ninguna lista**.
3. **`_arbol_de` (`:9310`) deja de tener el directorio escrito a mano**: recibe la ruta
   absoluta ya resuelta, o recibe el directorio derivado.
4. **`RUTAS_VIGILADAS` (`:27622`) se queda solo con lo que carga con información.** Sus
   tres entradas de vista son **redundantes**: el default del `.get()`
   (`os.path.join("views", nombre)`, `:27697`) ya devuelve exactamente eso. Solo
   `confirmation.py` —que vive en `ui/` y no en `ui/views/`— aporta algo. El diccionario
   pasa a ser **una excepción** ("este fichero no está en `views/`"), no una segunda copia
   del conjunto. `ESPERADOS` (`:27631`) deja de ser una tercera copia: sale de la
   declaración que ya se compara con el derivado.
5. La cifra `== 10` (`:9416`) **se queda**: es un tripwire deliberado («O se movió una
   publicación, o esta cifra está desfasada: decídelo explícitamente»), no un alcance. Si
   el conjunto derivado cambia, la cifra tiene que cambiar **a mano y de forma visible** —
   que es lo que se quiere de un tripwire.

### 6.3 Lo que NO se hace (y por qué)

| No se hace | Por qué |
|---|---|
| Meter las enumeraciones en una **lista muda de permitidos** | La trampa del repo: degrada el guard y las comprobaciones específicas solo se aplican a la rama principal. Ya ha pasado dos veces. |
| Ampliar la **llave** del detector AC-5 a basenames | MEDIDO (E3): la re-enumeración por basenames **ya la cazan** AC-1 y AC-3 → es ruido, no agujero. Ampliar la llave añadiría ruido y riesgo de falsos positivos (`/F`, `/T`, regexes). |
| Arreglar `_copiar_el_esqueleto_del_validador` | MEDIDO en el ciclo 66: todas las celdas dan ROJO con fichero y línea → bomba de mantenimiento. |
| Tocar `src/woptimizer/**` | Invariante del repo. Todo el cambio es de tooling. |
| Cambiar el alcance de AC-5 | Es el **#2** del ranking, con su propio ciclo. |

---

## 7. Criterios de aceptación y mutantes nombrados

> **Declaración por adelantado:** el mutante **M-V2** es **EQUIVALENTE** (su rojo es ruido
> por construcción, como el `M-C` del ciclo 67) y el mutante **M-V3** es el que **NO PUEDE
> QUEDAR SIN COBERTURA** (si nadie lo mata, el guard puede volverse vacuo otra vez).

| id | Mutante | Qué rompe | Quién lo mata |
|---|---|---|---|
| **M-V1** | `VISTAS_INVENTARIADAS` vuelve a ser **la fuente** (la `for` recorre la literal) | una vista nueva en disco no la vigila el guard de workers | **AC-1** (forma: la fuente tiene que ser el derivado) y **AC-2** (producto: la vista falsa da ROJO) |
| **M-V2** | una vista nueva aparece en disco y la literal **no** se actualiza | el guard da ROJO nombrando la vista | **EQUIVALENTE**: es ruido por construcción (rojo con fichero nombrado). Su supervivencia **no** es un fallo — igual que `M-C` en el ciclo 67 |
| **M-V3** | la derivación devuelve una **lista vacía** (o el helper devuelve una lista fija) | el guard abre 0 ficheros → «cero infracciones sobre cero ficheros» | **AC-3** (contraprueba: el guard tiene que abrir ≥1 fichero y el derivado tiene que ser el conjunto del disco) |
| **M-V4** | el helper `_vistas_del_disco` **no** se hoista y la copia a mano **vuelve** | dos fuentes de verdad otra vez | **AC-1** (forma: una sola fuente de verdad para el conjunto) |

### AC-1 — FORMA: una sola fuente de verdad para el conjunto de vistas

Con `ast`, en `run_tests.py`: el conjunto de vistas que el guard de workers abre **no puede
ser una enumeración literal escrita dentro del propio guard**, y el helper que lo deriva
**no puede estar anidado dentro de una función** (si lo está, es inaccesible para el otro
guard y la copia a mano vuelve). El guard tiene que exigir **una** fuente de verdad y
**una** declaración comparada contra ella.

- MATA **M-V1** y **M-V4**.
- Cada hallazgo se nombra con **fichero y línea**.
- **SIN lista muda de permitidos** (misma regla que AC-5 de TASK-081): la tolerancia, si la
  hay, va en el docstring del infractor con (a) por qué existe y (b) qué la retira.

### AC-2 — PRODUCTO: la vista nueva se audita aunque nadie la apunte

En `%TEMP%`: árbol con `src/woptimizer/` real + una vista **nueva** cuyo worker toca la
vista fuera de la puerta + la lista de vistas **actualizada** (como haría el dev) →
el guard tiene que dar **ROJO** nombrando la infracción. Y el **control positivo**: la
**misma** vista **sin** tocar la puerta → **VERDE**.

- MATA **M-V1** por la vía del producto. Es el AC que no puede sobrevivir sin el fix.
- El control positivo es lo que impide que un guard que siempre da ROJO cumpla el AC.

### AC-3 — CONTRAPRUEBA DEL DETECTOR: el derivado es el disco, y abre algo

1. El helper derivado devuelve **exactamente** los `.py` de `src/woptimizer/ui/views/`
   menos `__init__.py`, y **eso** es lo que el guard abre (control positivo: sobre el árbol
   sano abre ≥1 fichero; **un derivado vacío da ROJO**).
2. El guard abierto y el conjunto derivado **coinciden** con la declaración.

- MATA **M-V3** (derivación vacía / lista fija).

### AC-4 — CIERRE

`python run_tests.py` → `ALL TESTS PASSED.` (exit 0) · `python verify_ui_syntax.py` →
exit 0 con `ALCANCE_DERIVADO=22` · `python validate_docs.py` → 0 FAIL ·
**cero ediciones bajo `src/woptimizer/`** · commit por el wrapper con identificador
`(TASK-082)`, rama `beta`, `git status --porcelain` vacío. **Nunca `main`.**

### AC-5 — IMPACTO MEDIDO EN LAS CITAS POR NÚMERO DE LÍNEA

Toda cita por número de línea que este ciclo mueva tiene que estar **actualizada o
sustituida por derivación**, y el recuento tiene que ir en el informe de mutación.

---

## 8. ¿Necesita PRODUCTO? — SÍ, y la reproducción rápida SUSTITUYE al incidente

**No hay incidente real**: no ha entrado ninguna vista nueva con la infractions. Así que el
incidente **no se puede reproducir** y no hace falta intentarlo.

Lo que sí se puede reproducir es **el defecto**, y es un **test de producto** (el guard
corriendo sobre un árbol real, no su texto). El comando exacto, medido:

```powershell
python "$env:TEMP\wopt_c68_scan\exp.py" e1c
```

**4,5 s** medidos (copia del repo a `%TEMP%` + mutación + llamada a los dos guards reales
importando el `run_tests.py` de la cámara). Es **más rápido que los 8 s de TASK-081** y no
toca ni un byte del árbol real.

> El script de la cámara es de este ciclo y **no se versiona**: la versión que se
> versionará es el **test** del AC-2, dentro de `run_tests.py`.

---

## 9. Impacto en las citas por número de línea — MEDIDO

**Este ciclo (el arquitecto) NO toca `run_tests.py`, ni `validate_docs.py`, ni
`verify_ui_syntax.py`, ni `STATUS.md`.** Los ficheros que toca son:

| Fichero | ¿Toca líneas citadas? |
|---|---|
| `openspec/changes/2026-10-21-vistas-del-guard-de-workers-derivadas/proposal.md` | nuevo |
| `openspec/changes/2026-10-21-vistas-del-guard-de-workers-derivadas/tasks.md` | nuevo |
| `.taskmaster/tasks.json` | **NO**: la tarea nueva se **añade al final** del array y solo se cambian dos valores **en la misma línea** (`active_task_id`, `updated_at`). Las 1 768 líneas existentes **no se mueven**. |
| `.taskmaster/tasks.md` | **NO**: no hay ninguna cita a `tasks.md:N` en el repo (MEDIDO). Se añade una fila. |

**MEDIDO, y por eso `STATUS.md` NO se toca:** `STATUS.md` está citado **por número de
línea en 9 sitios de código vivo** (`run_tests.py` ×5, `validate_docs.py` ×1,
`.taskmaster/git_safe_commit.py` ×2, más 2 auto-citas) y en ~19 sitios más de
`CHANGELOG.md`, `.taskmaster/CHANGELOG.md`, `.taskmaster/rd_journal.json` y
`.taskmaster/tasks.json`. Editarlo **mueve 28+ citas vivas**. El panel lo cierra el
orquestador, no el arquitecto.

⚠️ Las citas de `run_tests.py` que usa esta propuesta (`:9410`, `:27617`, `:27652`,
`:27683`, `:27715`, `:28993`, `:13209`) **se moverán** cuando el dev implemente el AC-1
(la implementación inserta líneas por encima). **El informe de mutación del ciclo 68 tiene
que volver a medir las citas vivas** — es el residuo `P2` de `STATUS.md`, ya declarado.

---

## 10. Lo que este ciclo NO arregla, y por qué

| Residuo | Por qué no aquí |
|---|---|
| El alcance de AC-5 (`run_tests.py:28993`) es una literal y el guard se puede vaciar (E2) | **Es el #2 del ranking**: agujero **latente**, no verde falso. Su propio ciclo. |
| `_copiar_el_esqueleto_del_validador` (`run_tests.py:13209`) | MEDIDO: todas las celdas dan ROJO con fichero y línea → **bomba de mantenimiento** (A12, ya declarado) |
| La llave del detector AC-5 no ve basenames | MEDIDO (E3): AC-1 y AC-3 **ya lo cazan** → **ruido**, no agujero |
| `REGISTRO_INDECISAS` (15 celdas) | Deuda de crecimiento, no se puede pudre en silencio (S6) |
| `_chk.py` · `_chk2.py` · `_matrix_c26.py` en la raíz | Restos declarados; borrarlos es otra tarea |
| `TASK-080` (activar el validador en CI) | Su propia medición lo bloquea (25 hashes sin pushear). **No se activa.** |
| `TASK-068` | Decisión del dueño (P-1, P-2b). **No se formaliza.** |
| `S7` (el docstring de AC-1 afirma una garantía que no tiene) | Guard de otro ciclo; se arregla cuando se toque AC-1 |
| `S5` (`doc.find` lee la primera marca, no la última) | Ídem; mismo guard |
| `D2`/`D3`/`P2` (cifras escritas a mano) | Deuda baja, ya declarada |

---

## 11. Referencias

* Propiedad y guard AC-5: `openspec/changes/2026-10-19-verificacion-ui-alcance-derivado/` (`proposal.md`, `mutation-report.md`)
* Deuda técnica: `STATUS.md` §🔵 y §🟡 (filas S1/S2/S3, S6, S7, D2/D3/P2, A12)
* Sujeto derivado y contador: `run_tests.py:27652-27688`, `run_tests.py:28711-28796`
* Guard de forma: `run_tests.py:28964-29075`
* Ejecución en CI: `.github/workflows/release.yml:86-87` y `:116`
* Reglas de git: `AGENTS.md:59-65`, `docs/ai/sandbox-rules.md:55-56`
