# Propuesta — El gate tiene que LEER el campo `mutacion` del catalogo

**Ciclo:** 72 · **Rama:** `beta` · **Tarea:** TASK-091
**Arbol medido:** `6fe372d` · **Cero ediciones bajo `src/woptimizer/`.**
**Tooling puro.** El gate vive en `validate_docs.py` (check 11) y el guard en
`run_tests.py`. Nada de UI, nada de servicios, nada de modelos.

---

## 0. El encargo y la respuesta en una frase

El check 11 **re-deriva** el veredicto de mutacion desde la evidencia commiteada
y su **cableado** esta vigilado (el mutante D-A muere por su asercion) y su
**juicio** esta vigilado (el guard de PRODUCTO del ciclo 71, seccion (D)). Lo que
**no** esta vigilado es que el gate **LEA** el campo `mutacion` del catalogo:
`_leer_el_catalogo` (`validate_docs.py:3148`) devuelve solo `(id, asa, motivo,
sha_arbol_auditado)` y el bucle (`validate_docs.py:3328`) itera esos cuatro. La
respuesta son **CUATRO reglas que NO CADUCAN** (forma de la declaracion, existencia
del fichero, `cambio` y `ciclo` del catalogo contra la entrada del journal) **mas
un limite nuevo declarado** (g): el TEXTO declarado no se comprueba, y por tres
motivos MEDIDOS que estan en §4.

---

## 1. La decision de diseno, en una tabla

| # | Decision | Respuesta | Por que (medido) |
|---|---|---|---|
| D-1 | Donde vive la comprobacion | **DENTRO del check 11**, en `_comprobar_veredictos_de_mutacion` | Un check nuevo (12-bis) cambiaria el contrato del `--sin-ancla-de-git`, que son **TRES** saltados (`validate_docs.py:3189-3193`) |
| D-2 | Que reglas | **R1** forma · **R2** el fichero existe y esta dentro del arbol · **R3** `cambio` == `change` · **R4** `ciclo` == `cycle` | Las cuatro son **DERIVADAS** (se comparan dos cosas que el repo ya declara) y **no caducan** con el movimiento del codigo |
| D-3 | El texto declarado (`original` dentro del fichero) | **NO se comprueba**: es el limite **(g)**, con sus tres motivos medidos | Caduca (MEDIDO: 24/26), cuesta **62,3 ms** contra **46,2 ms** disponibles, y la receta que caduca NO invalida el veredicto (§4) |
| D-4 | La contraprueba | El **catalogo real del repo** pasa con **0 FAIL** tras **UNA** migracion (`M-121`) | Es lo que exige el AC-3, y el AC-3 ofrece la via de la migracion con su justificacion |
| D-5 | Donde vive el guard | **Seccion (F)** del test que ya existe (`run_tests.py:22278`), con un **cambio sintetico PROPIO** | El recuento se queda en **235 = 159 + 76** (precedente literal: `run_tests.py:22298-22302`) |
| D-6 | Los dos papeles de `mutacion` | **Un solo mecanismo**: los dos cumplen las mismas cuatro reglas | Los 15 centinelas del corpus declaran un `mutacion` mas ESTRICTO que los mutantes reales (§5) |

---

## 2. El agujero, medido (esta vez por MI, no por el encargo)

### 2.1 Lo que el gate lee HOY

`_leer_el_catalogo` (`validate_docs.py:3148-3166`):

```python
for campo in ("id", "asa", "motivo"):
    if not entrada.get(campo):
        raise ValueError(...)
salida.append((entrada["id"], entrada["asa"], entrada["motivo"],
               entrada.get("sha_arbol_auditado")))
```

El campo `mutacion` **no se lee, no se valida y no se propaga**. El bucle que lo
recorreria es `validate_docs.py:3328`:

```python
for identificador, asa, motivo, sha_del_catalogo in mutantes:
```

**MEDIDO: 26 mutantes vivos** (24 del ciclo 71 + 2 del ciclo 70) y **cero** reglas
sobre su `mutacion`.

### 2.2 El censo de los 26 (MEDIDO, este ciclo)

| Comprobacion | Resultado | Quien falla |
|---|---|---|
| `mutacion` declarada, con `fichero`/`original`/`sustituto` no vacios | **26/26** | — |
| `original != sustituto` | **26/26** | — |
| `mutacion.fichero` **existe** en el arbol | **25/26** | **M-121** (`"run_tests.py + validate_docs.py"`, que no es un fichero; `linea: 0`) |
| `original` presente **como bloque contiguo** en el fichero | **24/26** | **M-A1** (dos `if` que existen pero NO son contiguos) y **M-121** (prosa) |
| `original` presente **en la linea declarada** | **1/26** (solo M-107) | **25/26** |
| `cambio` del catalogo == `change` de la entrada del journal | **2/2** | — |
| `ciclo` del catalogo == `cycle` de la entrada del journal | **2/2** | — |

**La tercera fila es el dato que decide el diseno: la linea declarada NO es un
ancla.** La regla ingenua ("el fichero existe, la linea existe y el texto
original declarado esta en ella") daria FAIL sobre **25 de los 26** mutantes del
propio repo. **Y la cuarta fila dice que la regla "el texto esta EN EL FICHERO"
tampoco es libre: ya falla hoy sobre 2.**

### 2.3 La deriva, medida por mutante

| Mutante | Declara | La realidad de HOY (`6fe372d`) |
|---|---|---|
| **M-3** (ciclo 70) | `run_tests.py` **linea 23459** | el texto declarado esta en la **23631** (**+172 lineas**) |
| **M-A1** (ciclo 70) | `src/woptimizer/config.py` **linea 285** | las dos lineas existen (285 y ~311) pero **NO son contiguas**: el bloque declarado **no aparece** en el fichero |
| **M-90** (ciclo 71) | el **CUERPO ENTERO** del gate | el cuerpo esta hoy en `validate_docs.py:3217-3412`; **cualquier cambio del cuerpo lo invalida** (este ciclo lo cambia) |
| **M-92 / M-94** (ciclo 71) | `validate_docs.py` **linea 3316** | el `for` que declaran esta hoy en la **3328** (el texto sigue ahi, la linea no) |
| **M-121** (ciclo 71) | `fichero` = `"run_tests.py + validate_docs.py"`, `linea: 0` | **no es un fichero** |

---

## 3. LA FORMA CONCRETA

### 3.1 Que lee el gate del campo `mutacion`

`_leer_el_catalogo` pasa a devolver la `mutacion` como **quinto** elemento de la
tupla (de 4 a 5). El bucle de `validate_docs.py:3328` pasa a iterar cinco. ⚠️
**Consecuencia medida:** esa linea es el `original` de **M-92 y M-94**, luego el
fix invalida sus recetas (no su veredicto) y la **ronda 6** del `mutation-auditor`
las re-declara (§8).

### 3.2 Las cuatro reglas, EN ORDEN

**R3 y R4 se comprueban UNA VEZ POR ENTRADA del journal, ANTES del bucle de
mutantes. R1 y R2 se comprueban POR MUTANTE, DENTRO del bucle.**

| # | Regla | Donde | Que exige | FAIL si |
|---|---|---|---|---|
| **R1** | **LA DECLARACION TIENE FORMA** | por mutante | `mutacion` es un objeto con `fichero` (str no vacio), `original` (str no vacio), `sustituto` (str no vacio), `original != sustituto`, y `linea` es un entero `>= 1` | falta o es incompleta |
| **R2** | **EL FICHERO EXISTE Y ESTA DENTRO DEL ARBOL** | por mutante | `mutacion.fichero` resuelve con `_dentro_del_arbol(root, fichero)` (la MISMA funcion que ya protege el `change`, `validate_docs.py:3169`) y es un fichero existente | no existe, o se sale del arbol |
| **R3** | **EL `cambio` DEL CATALOGO ES EL `change` DE LA ENTRADA** | por entrada | `catalogo["cambio"].rstrip("/") == entrada["change"].rstrip("/")` | no coincide |
| **R4** | **EL `ciclo` DEL CATALOGO ES EL `cycle` DE LA ENTRADA** | por entrada | `catalogo["ciclo"] == entrada["cycle"]` | no coincide |

**Por que este orden:** R1 y R2 son las **baratas y graves** (sin `mutacion` no hay
receta; una receta que apunta a un fichero inexistente es ficcion), y R3/R4
comprueban el **ancla** del catalogo, que es lo que impide que un catalogo se
haga pasar por el de otro ciclo. Las cuatro son DERIVADAS: comparan dos
declaraciones que el repo ya hace, sin ninguna lista escrita a mano (la clase que
este repo persigue desde el ciclo 67: enumerar a mano es una bomba).

**Lo que NO hacen:** ninguna regla **lee el contenido** de un fichero. No hay I/O
de texto, no hay busquedas, no hay cache. Solo `os.path.isfile` (26 `stat`).

### 3.3 El texto LITERAL de los FAIL

El estilo es el del check 11 (`validate_docs.py:3300-3400`): prefijo
`mutaciones.json:`, el mutante nombrado, el campo nombrado, el valor que no
cuadra. El validador imprime `  [FAIL] {linea}` (`validate_docs.py:2788`).

**R1** (`{detalle}` es uno de: `falta el campo 'mutacion'` / `el campo 'mutacion' no es un objeto` / `no declara 'fichero'` / `no declara 'original'` / `no declara 'sustituto'` / `'original' y 'sustituto' son el MISMO texto` / `no declara 'linea'` / `'linea' no es un entero >= 1`):

```
mutaciones.json: el mutante {id} NO declara una `mutacion` utilizable: {detalle}.
El campo `mutacion` dice QUE fichero y QUE texto se sustituyen, y sin el no se
puede saber que se rompio para auditar el fix
```

**R2:**

```
mutaciones.json: el mutante {id} declara `mutacion.fichero` = {fichero!r} y ese
fichero NO EXISTE en el arbol (o se sale de el). Una mutacion que apunta a un
fichero que no existe NO es una mutacion: es la DECLARACION de una mutacion
```

**R3:**

```
mutaciones.json: el catalogo declara `cambio` = {cambio!r} y la entrada del
journal del ciclo {ciclo} declara `change` = {change!r}: este catalogo NO es el
del ciclo que dice ser
```

**R4:**

```
mutaciones.json: el catalogo declara `ciclo` = {ciclo_del_catalogo!r} y la
entrada del journal que lo ancla es la del ciclo {ciclo_de_la_entrada!r}: este
catalogo NO es del ciclo que dice ser
```

### 3.4 Lo que el gate NO comprueba, y por que: el limite **(g)**

> **(g) que el TEXTO declarado (`mutacion.original`) este EN el fichero.** El
> gate comprueba que la `mutacion` este DECLARADA, que su fichero EXISTA y que el
> catalogo sea el del ciclo que dice ser, pero **NO** que el texto que se
> declara este en ese fichero. **Motivo medido (caducidad):** el texto declarado
> se mueve con cada ciclo que toca el codigo (M-3 declara `run_tests.py:23459` y
> su texto esta hoy en la **23631**), hay recetas cuyo `original` **nunca existio
> como bloque** (M-A1: dos `if` que existen pero no contiguos) y hay recetas que
> son **el cuerpo entero de una funcion** (M-90), luego **cualquier** cambio del
> codigo las invalida. Una regla que exigiera el texto daria FAIL sobre el propio
> catalogo del repo, y una que lo exigiera en la **linea** daria FAIL sobre **25
> de los 26** mutantes. **Motivo medido (coste):** comprobarlo cuesta **62,3 ms**
> (26 mutantes, 5 ficheros, 1.891 MB leidos, cache por ruta + busqueda `in`) y el
> presupuesto del gate es del **0,5 %** de los 11,28 s del validador = **56,4 ms**,
> con un margen actual de **10,2 ms**: disponibles **46,2 ms**, luego **NO CABE**.
> **Motivo medido (semantica):** la RECETA caduca, el VEREDICTO no. El veredicto
> es un hecho sobre el arbol AUDITADO (`sha_arbol_auditado`), y ese hecho no se
> invalida porque el codigo se haya movido despues; lo que caduca es el
> PROCEDIMIENTO para reproducirlo. Un FAIL por esto convertiria el gate en una
> bomba de relojería (habria que re-declarar mutantes historicos cada vez que se
> mueve el codigo), que es justo lo que este encargo prohibe.

El limite (g) va en el **bloque canonico** de `validate_docs.py` ("LO QUE ESTE
GATE **NO** PRUEBA") y **repetido en el docstring** de la funcion, como el (f).
El guard de FORMA (B) de `run_tests.py:22530` se **amplia** para exigir tambien
`(g)` y su motivo medido: un limite que se puede borrar en silencio no esta
declarado. **El recuento de tests NO se mueve** (235 = 159 + 76): se extiende el
test que ya existe.

---

## 4. Por que el texto declarado NO puede ser un FAIL (la cuenta)

| | la RECETA (`mutacion`) | el VEREDICTO (MUERTO/SOBREVIVIENTE/NO MEDIDO) |
|---|---|---|
| que afirma | que se sustituyo, para poder reproducir la medicion | que se midio, en el arbol AUDITADO |
| de que depende | del codigo **de hoy** | del arbol **de entonces** (`sha_arbol_auditado`) |
| que le pasa cuando el codigo se mueve | **caduca** (la receta ya no se aplica) | **no pasa nada**: el hecho medido sigue siendo cierto |

De ahi sale la regla: **lo que caduca no puede ser un FAIL**, porque el FAIL
atribuiría a la DECLARACION una culpa que no tiene (el veredicto es correcto) y
porque obligaria a re-declarar historicos sin fin. Lo que NO caduca **si** puede
y **debe** ser un FAIL: las cuatro reglas de §3.2.

---

## 5. Los DOS PAPELES del campo `mutacion`, y por que un solo mecanismo basta

| | mutante REAL (catalogo commiteado) | centinela SINTETICO (corpus de la seccion (D)) |
|---|---|---|
| donde vive | `openspec/changes/<id>/mutaciones.json` (commiteado) | `tmp/openspec/changes/<nombre>/mutaciones.json` (dentro del esqueleto temporal, nunca commiteado) |
| que papel tiene el `mutacion` | la RECETA: que se sustituyo para auditar el FIX | el ANCLA: que contradiccion se fabrica en el esqueleto |
| forma | `fichero` + `linea` + `original` + `sustituto` | **exactamente la misma** (`run_tests.py:22879-22890` y `23018-23029`) |
| `original` | un bloque de codigo (a veces el cuerpo ENTERO de una funcion) | **una linea LITERAL** del `mutation-report.md` del corpus |
| `sustituto` | el texto nuevo | la misma linea con el estado cambiado |
| cumple R1? | si (25/26; M-121 hay que migrarlo) | **si, los 15** |
| cumple R2? | si (25/26) | **si, los 15** (el `mutation-report.md` del corpus existe en el esqueleto) |
| cumple R3/R4? | si (2/2) | **si** (`montar_cambio` escribe el `cambio` y el `ciclo` del catalogo con la MISMA variable que la entrada del journal, `run_tests.py:23003` y `23037`) |

**El centinela es MAS ESTRICTO que el mutante real** (su `original` es una linea
exacta del fichero; el del mutante real puede ser un bloque movedo). Por eso
**un solo mecanismo sirve para los dos**, y por eso **no hace falta un campo que
los distinga**: la distincion es del LECTOR (receta vs ancla), no del CONTRATO.

**MEDIDO en los 15 centinelas** (6 cambios sinteticos, 6 entradas de journal):
`mutacion.fichero` = `<cambio>/mutation-report.md` (existe en el esqueleto),
`original` = la linea canonica o la prosa de anclaje (lineas **4, 5, 7, 8** de ese
fichero, verificadas una a una contra como se escribe el informe en
`run_tests.py:23089-23095`), `sustituto` = esa misma linea con el estado
cambiado ⇒ **`original != sustituto` en los 15**.

---

## 6. AC-6: el guard de TASK-090 queda INTACTO, y por que (tres razones)

1. **Los 15 centinelas del corpus pasan R1, R2, R3 y R4** (§5). Ninguno es
   acusado por las reglas nuevas, luego las aserciones de (D) y (E) siguen
   viendo exactamente los mismos `[FAIL]`.
2. **La seccion (F) usa un cambio sintetico PROPIO** (`2026-10-23-corpus-
   sintetico-de-la-mutacion`) y **centinelas PROPIOS** (`M-FIX-MUTACION-OK`,
   `M-FIX-MUTACION-MAL`). **No toca ninguno de los 15**, luego ningun FAIL de (F)
   nombra a un centinela de (D) o (E), y la asercion "0 FAIL que nombren al
   COHERENTE" de (D1) sigue valiendo.
3. **El REGISTRO se puede ampliar sin romper el guard**: el guard lo comprueba por
   SUBSTRING (`"[REGISTRO] check 11 (veredicto de mutacion)"` en
   `run_tests.py:22449` y `f"entradas cubiertas={N}"` en `run_tests.py:23309`),
   luego anadir campos al final no lo rompe. Y el bloque de limites admite un
   limite mas: el guard (B) exige `(a)`..`(f)` y que la lista diga "NO es
   exhaustiva" (`run_tests.py:22530-22548`), luego `(g)` se anade sin reescribir
   nada.

⚠️ **Y el orden de las aserciones importa (lo dice el propio corpus):** las
celdas de (F) tienen que ir **ANTES** del aserto de `"Resumen:"` y su mensaje
tiene que **terminar en una linea marcador**, como las de (D) y (E). Si no, el
veredicto canonico cae a NO MEDIDO (es el hallazgo **T-1** de la ronda 5). ⚠️ Y
**T-6 sigue ABIERTO** (el emisor corta la cola en el ULTIMO traceback y el gate
busca el frame en todo el bloque): este diseno **NO depende de la cola** (las
cuatro reglas salen del CATALOGO y del JOURNAL, no de la evidencia), luego **no
reproduce T-6**; pero la celda (F) tiene que exigir `Resumen:` y el motivo en la
ULTIMA linea de la cola, como hace (D1), para no caer en el NO MEDIDO de T-6.

---

## 7. La seccion (F): el discriminante y su contraprueba

Se **extiende** `test_el_check_9_se_cablea_en_el_camino_real_del_validador`
(`run_tests.py:22278`), que ya tiene las secciones (A) cableado, (B) limites, (C)
emisor, (D) juicio y (E) check 12. **Ningun `test_*` nuevo: el recuento se queda
en 235 = 159 + 76** y las **cinco** declaraciones no se mueven.

| Celda | Que hace | Que aserciona |
|---|---|---|
| **F1** | monta un cambio sintetico **PROPIO** con **DOS** mutantes: `M-FIX-MUTACION-OK` (coherente, `mutacion` correcta) **primero** y `M-FIX-MUTACION-MAL` (coherente en todo lo demas, pero con `mutacion.fichero` = `src/woptimizer/NO_EXISTE.py`) **segundo** | **>=1 `[FAIL]` con la RAZON de R2** que nombre a `M-FIX-MUTACION-MAL`, y **0 `[FAIL]` que nombren a `M-FIX-MUTACION-OK`**. El centinela malo es **coherente en todo lo demas** (asa real, evidencia, journal e informe en regla), luego el unico motivo posible de su acusacion es la `mutacion` |
| **F2** | el mismo catalogo con `ciclo: 999` | **>=1 `[FAIL]` con la RAZON de R4** |
| **F3** | **CONTRAPROUEBA**: el mismo catalogo con la `mutacion` **CORRECTA** | **0 `[FAIL]`** que nombren a sus centinelas, con el REGISTRO presente |
| **F4** | el **catalogo REAL** del repo, sin tocar | **0 FAIL** de `python validate_docs.py` (AC-7) |
| **F5** | el bloque de limites | trae **(g)** con su motivo medido, y el docstring lo repite |

**El criterio discriminante, en una frase:** la celda **F1** FALLA sin el fix
porque hoy el gate **no lee `mutacion` en absoluto** (`_leer_el_catalogo` la
descarta), luego un `mutacion.fichero` inexistente da **0 FAIL**; con el fix, el
mismo catalogo da **1 FAIL que nombra al centinela malo y ninguno que nombre al
bueno**. Y **F3** es lo que impide que F1 se cumpla por un motivo equivocado: si
el gate acusara a los centinelas buenos, F3 lo coge.

**El orden de los centinelas es normativo:** el malo va **SEGUNDO**, para que un
gate que mire solo el primero (el mutante **M-92**, que ya existe en el catalogo)
quede cogido. Y el mutante **M-H5** (el gate que mira solo el primero) tiene que
morir en F1.

---

## 8. Las MIGRACIONES que exige el fix (con su dueño)

| Que | Quien | Por que |
|---|---|---|
| **M-121** (`openspec/changes/2026-10-22-el-gate-distingue-o-falla/mutaciones.json`): `mutacion.fichero` = `"run_tests.py + validate_docs.py"` -> un fichero real, y `linea: 0` -> la linea real | **el dev** (es un fichero de `openspec/`, no de `src/`), con su nota | **Sin esto el validador da 1 FAIL sobre el catalogo real** (viola R1 y R2). El `sha_arbol_auditado` NO se toca (el veredicto no cambia) y el `mutation-report.md` NO se reescribe (es el registro de la ronda 5) |
| **M-90, M-92, M-94** (mismo catalogo): sus `original` apuntan al cuerpo del gate y a la linea del `for` que este fix cambia | **la ronda 6 del `mutation-auditor`**, con su `nota_ronda_6` | Sus **veredictos no cambian** (el texto no se comprueba: limite (g)), pero sus **recetas ya no se aplican**, luego sin re-declarar el auditor no puede re-medirlos |
| **M-A1** (`.../2026-10-22-killer-check-del-veredicto/mutaciones.json`): su `original` es un bloque que nunca existio como contiguo | **nadie** | No es un FAIL (limite (g)). Se declara su cifra en el limite (g), que es lo que lo hace visible |
| El `agent.md` del `mutation-auditor` tiene que decir que la `mutacion` se declara con `fichero`, `linea`, `original` y `sustituto`, y que **`fichero` tiene que existir** | **el orquestador** (`.agents/agents/` no es del arquitecto) | Sin eso, el auditor puede seguir declarando `mutacion` que no aplican (fue justo lo que paso con M-121 y M-A1) |

---

## 9. Los AC (numerados y verificables)

| # | AC | Como se comprueba |
|---|---|---|
| **AC-1** | **RE-ESPECIFICADO:** el gate comprueba el campo `mutacion` con las **cuatro reglas de §3.2**, que **NO CADUCAN** con el movimiento del codigo: R1 (forma), R2 (el fichero existe y esta dentro del arbol), R3 (el `cambio` del catalogo es el `change` de la entrada), R4 (el `ciclo` del catalogo es el `cycle` de la entrada) | celdas F1/F2/F3; el limite (g) declara lo que **no** se comprueba y por que |
| **AC-2** | un catalogo con una `mutacion` incorrecta da **FAIL**, con el **nombre del campo** y el **valor que no cuadra** en el texto | celda F1 (`mutacion.fichero` inexistente) y celda F2 (`ciclo: 999`); los dos mensajes literales de §3.3 |
| **AC-3** | **CONTRAPROUEBA con control positivo:** el catalogo **real** del repo pasa con **0 FAIL** tras **UNA** migracion justificada (`M-121`), con su nota | celda F4 + `python validate_docs.py` -> 0 FAIL; la migracion esta en §8 con su justificacion |
| **AC-4** | el **limite (g)** queda **DECLARADO** en el bloque canonico y repetido en el docstring, con sus **tres motivos medidos** (caducidad, coste, semantica), y el guard de FORMA (B) se **amplia** para exigirlo | celda F5; `run_tests.py:22530` exige ahora `(a)`..`(g)` |
| **AC-5** | el **coste** se mide y se declara en **milisegundos reales** contra `validate_docs.py` | el dev mide el margen ANTES y DESPUES del fix y lo declara; el presupuesto es del **0,5 %** de 11,28 s = 56,4 ms, con 10,2 ms usados |
| **AC-6** | **NO rompe el guard de TASK-090:** los 15 centinelas del corpus siguen dando 0 FAIL, y la seccion (F) usa un cambio sintetico **PROPIO** | celdas F3 y D1; §6 |
| **AC-7** | **CERO regresiones:** `python run_tests.py` verde, `python validate_docs.py` **0 FAIL**, `python verify_ui_syntax.py` verde, `src/` **intacto**, el **contrato de la linea canonica intacto** (`.taskmaster/veredicto.py` y la re-derivacion NO se tocan) | el cierre del ciclo |
| **AC-8** | el **recuento NO cambia**: 235 = 159 + 76, ningun `test_*` nuevo, las **cinco** declaraciones intactas (`AGENTS.md:70`, `README.md:63`, `STATUS.md:12`, `STATUS.md:132`, `docs/ai/testing-guide.md:57`); la **fila 130** de `docs/ai/testing-guide.md` nombra la seccion (F) | `vd._recuento_de_tests('run_tests.py')` -> (235, 235, [], []); el validador lo deriva y lo exige |

---

## 10. Los mutantes declarados (los tiene que medir el `mutation-auditor`)

| id | Que rompe | Que tiene que morir | Por que no es EQUIVALENTE |
|---|---|---|---|
| **M-H1** | el gate **NO comprueba R1** (acepta una `mutacion` ausente o mal formada) | la asercion de F1 sobre `M-FIX-MUTACION-MAL` | MEDIDO HOY: una `mutacion` ausente da **0 FAIL** |
| **M-H2** | el gate **NO comprueba R2** (acepta un `fichero` inexistente) | la asercion de F1 | MEDIDO HOY: `mutacion.fichero = src/woptimizer/NO_EXISTE.py` da **0 FAIL** |
| **M-H3** | el gate **NO comprueba R3** (acepta un `cambio` que no es el suyo) | la asercion de F2-bis | el catalogo pasa a ser el de otro cambio sin que nadie lo note |
| **M-H4** | el gate **NO comprueba R4** (acepta `ciclo: 999`) | la asercion de F2 | MEDIDO HOY: `ciclo: 999` da **0 FAIL** |
| **M-H5** | el gate mira **solo el primer** mutante del catalogo (`mutantes[:1]`) | la asercion de F1 | el centinela malo es el **SEGUNDO** a proposito (es el patron de M-92) |
| **M-H6** | el gate **acusa en lo que no puede**: tambien acusa a los centinelas EN REGLA | la asercion de F3 (0 FAIL sobre el bueno) | un gate que acusa de mas es tan ciego como uno que no acusa nada (el patron de M-91) |

Los seis se aplican **al gate** (`validate_docs.py`), en copia, y se miden con la
suite. **Los cuatro ultimos son los que hacen que el guard de (F) sea de
PRODUCTO y no de FORMA**: M-H5 conserva la forma del bucle y M-H6 conserva la
forma de la rama.

---

## 11. Los riesgos

| Riesgo | Como se acota |
|---|---|
| **El fix invalida recetas vivas** (M-90, M-92, M-94) | el limite (g) NO es FAIL, luego el repo no se pone rojo; las re-declara la ronda 6 (§8) |
| **Un FAIL por `mutacion` nombra a un centinela de (D) y rompe la asercion del coherente** | la seccion (F) usa un cambio sintetico **PROPIO** (§6) |
| **El gate se convierte en una bomba de relojería** | las cuatro reglas no caducan; el texto queda como limite (g) declarado |
| **El coste del validador se dispara** | ninguna regla lee contenido; solo `isfile` (26 `stat`); el presupuesto de 56,4 ms queda intacto |
| **El guard (B) exige `(a)`..`(f)` y no `(g)`** | se amplía (`run_tests.py:22530`), sin anadir ningun `test_*` |
| **El bloque de maquina del informe y el journal tienen que llevar las MISMAS lineas** | el fix **no anade ni quita** lineas canonicas: las reglas nuevas no emiten `WOPT_VEREDICTO` |

---

## 12. Lo que este ciclo NO toca

- **NO** toca `src/woptimizer/**` (es tooling puro).
- **NO** toca `.taskmaster/veredicto.py` (el emisor) ni la gramatica de la linea
  canonica ni los tres estados.
- **NO** reescribe el `mutation-report.md` del ciclo 71 (es el registro de la
  ronda 5).
- **NO** arregla **T-1** (las aserciones de (E) sin linea marcador) ni **T-6**
  (el emisor y el gate derivan distinto): son de `openspec-dev` y de otro ciclo.
  **Lo que este ciclo hace es no depender de la cola**, luego no los reproduce.
- **NO** anade un `test_*`: el recuento se queda en **235 = 159 + 76**.
- **NO** mete la comprobacion en un check 12-bis: el contrato del
  `--sin-ancla-de-git` son **TRES** saltados y no se tocan.
