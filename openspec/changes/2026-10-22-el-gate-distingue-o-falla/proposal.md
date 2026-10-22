# Propuesta — El gate tiene que DISTINGUIR: el cuerpo del check 11 no puede quedar vacio

**Ciclo:** 71 · **Rama:** `beta` · **Tarea:** TASK-090
**HEAD medido:** `2116f05` · **Cero ediciones bajo `src/woptimizer/`.**
**Instrumento:** `%TEMP%\wopt_c71_*` (camaras desechables, 3 sondas). Nada de esto se
commitea. **Cero corridas de la suite completa**: el unico test implicado se
extrajo con `ast` y se ejecuto suelto.

---

## 0. El encargo y la respuesta en una frase

El check 11 de `validate_docs.py` **re-deriva** el veredicto de mutacion desde la
evidencia commiteada, y su **cableado** esta vigilado (el mutante D-A muere por su
asercion, `run_tests.py:22400-22432`). Lo que **no** esta vigilado es su
**contenido**: se puede dejar el cuerpo del gate **vacio, con el REGISTRO
intacto**, y el validador sigue dando **0 FAIL** sobre un catalogo que se contradice
a si mismo. La respuesta es **un guard de PRODUCTO**: un corpus sintetico con un
mutante **contradictorio** y otro **coherente**, sobre el cual el gate tiene que
**dar FAIL del primero y 0 FAIL del segundo** — y cuyo vaciado tiene que **hacer
desaparecer** ese FAIL.

---

## 1. La decision de diseno, en una tabla

| # | Decision | Respuesta | Por que (medido) |
|---|---|---|---|
| D-1 | Que hace que el CONTENIDO de un gate no sea vaciable | **Un guard de PRODUCTO**: el gate se ejecuta sobre un corpus **contradicido** y tiene que **acusar**; sobre el mismo corpus con un mutante **coherente** tiene que **callar** | Un guard de FORMA no puede: el mutante **M-93** (calcula el veredicto y lo tira) conserva la forma del cuerpo y solo lo coge un guard de producto (§3.2) |
| D-2 | Donde vive el guard | **En la SUITE**, como **seccion (D)** del test que ya vigila el cableado (`test_el_check_9_se_cablea_en_el_camino_real_del_validador`) | El veredicto de mutacion lo emite un programa que lee el **log de `run_tests.py`** (`mutation-auditor/agent.md`, punto 4). Un guard que viviera solo en `validate_docs.py` dejaria D-B como **SOBREVIVIENTE** por el contrato del repo (§3.3) |
| D-3 | Cuantos `test_*` | **Ninguno nuevo**: el recuento se queda en **235 = 159 + 76** y las **cinco** declaraciones no se mueven | Precedente del ciclo 70 (secciones A/B/C del mismo test) y `docs/ai/testing-guide.md:1430` |
| D-4 | Donde vive el corpus | **En el esqueleto que la seccion (A) ya construye** (`_copiar_el_esqueleto_del_validador`), con el journal **sustituido** por el sintetico | El esqueleto ya se copia: el coste marginal del guard son **dos corridas del validador**, no una copia de 1,7 MB |
| D-5 | D-B (este ciclo) y D-H (TASK-091) | **Ciclos SEPARADOS** | Arreglar D-B **no** arregla D-H, y el arreglo de D-H **hoy daria FAIL sobre el propio catalogo del ciclo 70** (§4) |

---

## 2. El agujero, medido

### 2.1 Lo que el gate hace y lo que nadie vigila

El gate vive en `validate_docs.py:3138` (`_comprobar_veredictos_de_mutacion`) y esta
cableado en `validar()` (`validate_docs.py:2617`). Imprime su **REGISTRO**
(`validate_docs.py:3350-3359`, impreso en `main()`, `validate_docs.py:2789-2795`).

**MEDIDO: las referencias de la suite al check 11 son exactamente DOS, y ninguna
mira el contenido.**

| Referencia | Que mira | Que NO mira |
|---|---|---|
| `run_tests.py:22375` | que el **REGISTRO** aparezca en el informe | que el gate **haga** algo |
| `run_tests.py:22428` | que el **mutante de cableado** borre el REGISTRO | lo mismo |
| `run_tests.py:22434-22475` | el **TEXTO** del bloque «LO QUE ESTE GATE **NO** PRUEBA» | el comportamiento |

⇒ Un cuerpo **vacio** conserva las tres cosas: el REGISTRO sale, el cableado sigue
vivo y el bloque de limites sigue escrito. **El D-B no tiene por donde morir.**

### 2.2 La reproduccion (camara desechable, `%TEMP%\wopt_c71_*`)

El **corpus** es un arbol sintetico con lo que el gate lee:

| Pieza | Contenido |
|---|---|
| `.taskmaster/rd_journal.json` | una entrada, `cycle: 70`, `change:` el cambio sintetico, con las dos lineas canonicas |
| `openspec/changes/<id>/mutaciones.json` | **dos** mutantes: `M-FIX-BIEN` (coherente) **primero** y `M-FIX-MAL` (contradictorio) **segundo** |
| `evidencia/<id>.cola` | `=== WOPT_RUN 1 RC=1 ===` + el frame del `asa` + `AssertionError: MOTIVO DE LA FIXTURE` → la evidencia **obliga a MUERTO** |
| `mutation-report.md` | el bloque de maquina con las dos lineas |
| el journal | declara `M-FIX-MAL` como **SOBREVIVIENTE** (la evidencia obliga a MUERTO → **CONTRADICCION**) y `M-FIX-BIEN` como **MUERTO** (coherente) |

El **orden** importa: el coherente va primero, luego el contradictorio, para que un
gate que solo mire el primer mutante quede cogido.

### 2.3 Las cifras

| id | Medicion | Resultado |
|---|---|---|
| **P1** | el gate **sano** sobre el corpus contradictorio | rc=1 · **1 `[FAIL]`** que nombra `M-FIX-MAL` · **0** que nombran `M-FIX-BIEN` · REGISTRO presente · **4,44 s** |
| **P2** | el **D-B** (cuerpo vaciado, REGISTRO puesto) sobre el MISMO corpus | rc=1 · **0 `[FAIL]`** · REGISTRO **presente** · 4,17 s → **el FAIL DESAPARECE** |
| **P3** | el test existente, con el D-B en el esqueleto | **PASA** → el D-B **sobrevive hoy** a la suite |
| **P4** | recuento de tests derivado del producto (`vd._recuento_de_tests`) | **(235, 235, [], [])** |
| **P5** | coste con un `run_tests.py` **minimo** en el esqueleto | **0,598 s** por corrida (7,5x mas barato); el gate discrimina **igual** (1 / 0 / REGISTRO) |

### 2.4 El modo de reproduccion

1. Copiar el repo a `%TEMP%` (excluyendo `.git` **como fichero**, `__pycache__`).
2. Sustituir el cuerpo de `_comprobar_veredictos_de_mutacion` por el stub que solo
   deja el REGISTRO (**texto**, no `ast`: el resto del fichero queda byte a byte).
3. Montar el corpus sintetico sobre el esqueleto (`_copiar_el_esqueleto_del_validador`).
4. Correr `python validate_docs.py` como **subproceso** con el `GIT_DIR` de la fixture.
5. El informe trae el REGISTRO y **0 `[FAIL]`** que nombren `M-FIX-MAL`.

---

## 3. Las alternativas, razonadas y medidas

### 3.1 La alternativa ingenua: **otro guard de FORMA sobre el texto del gate**

*Ejemplos*: «el cuerpo tiene que tener ≥ N sentencias», «el cuerpo tiene que
mencionar `_estado_del_mutante`», «el cuerpo tiene que contener `errors.append`».

**REFUTADA, y no por doctrina: por medicion.** El mutante **M-93** sustituye el
cuerpo por uno que **calcula el veredicto y lo tira**:

```python
for _entrada in (_leer_el_journal(root) or []):
    _estado_de_una_corrida("cola", 1, "asa", "motivo")
```

Su cuerpo tiene el **mismo numero de sentencias**, el **mismo bucle**, la **misma
llamada** y la **misma comparacion** que el original. **Cualquier** guard de forma
razonable lo acepta. Y aun asi el gate es ciego.

| Mutante | Que rompe | `FAIL(M-FIX-MAL)` | `FAIL(M-FIX-BIEN)` | REGISTRO | Lo que lo mata |
|---|---|---|---|---|---|
| **BASE** | — | **1** | **0** | si | — (el gate sano) |
| **M-90** | cuerpo **vacio**, REGISTRO puesto | **0** | 0 | **si** | la asercion del contradictorio |
| **M-91** | la comparacion `!=` **invertida** | 0 | **1** | si | la asercion del coherente |
| **M-92** | el gate mira **solo el primer** mutante | **0** | 0 | si | la asercion del contradictorio |
| **M-93** | **calcula el veredicto y lo tira** | **0** | 0 | si | la asercion del contradictorio |

⇒ **Un guard de forma no distingue M-93 de un gate sano. Uno de producto, si.**

### 3.2 La alternativa descartada: **el guard dentro del validador** (check 12)

Un check 12 que ejecutase el gate contra el corpus y se autocriticase.

**DESCARTADA, por el instrumento.** El veredicto de mutacion lo produce un programa
que lee el **log de `run_tests.py`** (`mutation-auditor/agent.md`, punto 4: «Ejecuta
`run_tests.py` en la copia»), y sus tres estados estan definidos sobre ese log
(`MUERTO` = «la suite quedo en ROJO, el test que murio es EL ASA ESPERADA»). Un
guard que viviera **solo** en `validate_docs.py` no pondria la suite en rojo: el
D-B seguiria siendo **SOBREVIVIENTE** por el contrato del repo, y el agujero
seguiria abierto **por la metrica que decide PASS/FAIL**.

Ademas, un check 12 SERIA una **segunda implementacion** del mismo guard (dos
sitios donde pudrirse, D1/D3), y **anadiria** coste al validador, cuyo presupuesto
es de **0,5 %** y cuyo margen actual es de **10,2 ms / 0,091 %**.

**Lo que se conserva de esta alternativa:** el limite queda **declarado** (AC-6):
*el validador, por si solo, NO detecta un gate ciego; solo la suite lo hace*.

### 3.3 La alternativa descartada: **un meta-mutador en el bucle**

Que el propio bucle mute el gate y compruebe que la suite se pone roja.

**DESCARTADA por coste y por reparto de papeles:** una suite completa son **735 s**
medidos, y el encargo prohibe **correr la suite extra** (y el meta-mutador seria,
ademas, el trabajo del `mutation-auditor`, no del guard). Lo que se hace es
**declarar los mutantes** (AC-5) para que el auditor los mida.

### 3.4 La alternativa descartada: **exigir mas al REGISTRO**

Que el REGISTRO diga cuantos mutantes se re-derivaron y que un 0 sea FAIL.

**DESCARTADA, MEDIDO:** con el D-B puesto el REGISTRO **sigue imprimiendose**
(P2). Un REGISTRO es un **contador**, no un **juicio**: cuentan lo que se ha
re-derivado, no distinguen si lo re-derivado era cierto. Y un guard sobre el
**texto** del REGISTRO vuelve a ser un guard de forma.

---

## 4. D-H (TASK-091) NO va en este ciclo — y por que

**MEDIDO: el catalogo del ciclo 70, commiteado en el repo, YA ESTA CADUCADO.**

| Mutante | Declara | La realidad de HOY (`2116f05`) |
|---|---|---|
| `M-3` | `run_tests.py` **linea 23459** | el texto declarado esta en la **23631** (**+172 lineas**) |
| `M-A1` | `src/woptimizer/config.py` **linea 285** | el texto declarado **NO APARECE** en el fichero: `get_safety_badge` se reescribio |

⇒ El **AC-1 de TASK-091**, tal como esta escrito («el fichero existe, la linea
existe y el texto original declarado esta en ella»), **daria FAIL sobre el propio
catalogo del repo** en cuanto se implemente. Y un `mutacion` que se valida contra
el arbol **deriva** con cada ciclo: un gate que exija el texto en la linea
declarada **envejecera** y habra que migrar el catalogo cada vez.

**Decision: ciclos separados.** Ademas de lo anterior:

1. **Son dos mecanismos distintos.** D-B es «el gate **no distingue**»; D-H es «el
   gate **no lee** un campo». Arreglar D-B no hace que el gate lea `mutacion`, y
   arreglar D-H no hace que el gate distinga.
2. **Arreglar D-H dentro de este ciclo **contaminaria** las aserciones del guard
   de D-B**: con el gate leyendo `mutacion`, el corpus sintetico tendria que
   declarar ese campo **correctamente** en los dos centinelas, y un FAIL por el
   `mutacion` **nombraria al centinela** → la asercion del coherente («0 FAIL»)
   se romperia por un motivo que no es el suyo.
3. **La nota de TASK-091 ya lo dice**: «se encolan aparte porque el arreglo de uno
   no arregla el otro».

**Lo que este ciclo deja para TASK-091** (anotado en su `notes`): la deriva
medida, y el hecho de que el `mutacion` del corpus sintetico **debe** declarar un
campo coherente con el arbol **desde ahora**, para que el arreglo de D-H no rompa
el guard de D-B.

---

## 5. El diseno

### 5.1 La seccion (D) del test que ya existe

Se **extiende** `test_el_check_9_se_cablea_en_el_camino_real_del_validador`
(`run_tests.py:22278`), que ya tiene las secciones (A) cableado, (B) limites
declarados y (C) el emisor que no pisa la evidencia ajena. **Ningun `test_*` nuevo**:
el recuento se queda en **235 = 159 + 76** y las cinco declaraciones **no se
mueven** (precedente literal: `run_tests.py:22298-22302` y
`docs/ai/testing-guide.md:1430`).

La seccion (D) tiene **tres** celdas:

| Celda | Que hace | Que aserciona |
|---|---|---|
| **D1** | monta el corpus en el esqueleto y corre el validador **sano** como subproceso | **≥1 `[FAIL]`** que nombre `M-FIX-MAL` (el contradictorio) y **0 `[FAIL]`** que nombren `M-FIX-BIEN` (el coherente), y el **REGISTRO presente** |
| **D2** | **CONTRAPROUEBA**: sustituye el cuerpo del gate por el stub del D-B (REGISTRO puesto) y vuelve a correr | el `[FAIL]` de `M-FIX-MAL` **desaparece** y el **REGISTRO sigue** → el guard **ve** la diferencia |
| **D3** | **restauracion**: deja el validador del esqueleto como estaba | el esqueleto no queda mutado para las secciones siguientes |

**Por que el filtro es por CENTINELA y no por el codigo de salida:** el esqueleto
**no es un repo limpio** — el validador da **3 `[FAIL]`** por otros motivos (P1). El
veredicto del guard se lee de las lineas que **nombran** al centinela, nunca del
`rc` ni del total de FAILs.

### 5.2 Por que el guard va en la suite (otra vez, y con la cifra)

| | en la suite (seccion D) | en el validador (check 12) |
|---|---|---|
| ¿pone la suite en rojo con el D-B? | **si** | **no** |
| ¿el veredicto del auditor lo ve? | **si** (el log de la suite) | **no** |
| coste para el validador | **0** | +N ms en cada corrida |
| sitios donde puede pudrirse | **1** | **2** |

### 5.3 El corpus, pieza a pieza, y por que es **sintetico**

El gate lee **cinco** cosas: el journal, el `change` de la entrada, el catalogo, el
informe del ciclo y la evidencia; y el `asa` tiene que ser un `test_*` **definido**
en el `run_tests.py` **de ese arbol**.

| Pieza | Por que esta como esta |
|---|---|
| el `asa` de cada centinela es un `test_*` **REAL** de la suite (`test_el_check_9_se_cablea_en_el_camino_real_del_validador` y `test_un_journal_ilegible_produce_exactamente_un_error_en_el_validador_real`) | el gate comprueba que el asa exista con `ast` sobre el `run_tests.py` del arbol: si el centinela usase un nombre inventado, el gate lo accusaria por **otra** razon y el guard mediria otra cosa |
| el catalogo declara **los dos** mutantes, el coherente **primero** | un gate que solo mira el primero queda cogido (M-92, medido) |
| la evidencia de los dos es **la misma forma** (`RC=1` + frame + `AssertionError`) | si solo el contradictorio tuviese evidencia, un gate que solo mira el primero pasaria el P1 |
| el journal declara `SOBREVIVIENTE` para el contradictorio y `MUERTO` para el coherente | la contradiccion es **exactamente** la que el gate tiene que ver: la evidencia obliga a MUERTO y el journal dice otra cosa |
| el `mutacion` de cada centinela **declara un fichero y una linea que EXISTEN** en el arbol del corpus | para que el arreglo de **D-H** (TASK-091) no rompa este guard: si el `mutacion` fuese incoherente, el FAIL de D-H **nombraria al centinela** y la celda D1 se romperia por un motivo ajeno |

### 5.4 Lo que este ciclo **no** arregla (declarado)

- **El validador, por si solo, sigue sin detectar un gate ciego.** Solo la suite lo
  detecta. Queda escrito en el bloque «LO QUE ESTE GATE **NO** PRUEBA» como
  limite **(f)** (AC-6).
- **La evidencia commiteada puede no ser el log real** (limite (d) del ciclo 70) y
  **el sha no se resuelve** (limite (e)): siguen siendo limites, no se tocan.
- **D-H**: el gate sigue **sin leer** el campo `mutacion` del catalogo.

---

## 6. Los AC (numerados y verificables)

| # | AC | Como se comprueba |
|---|---|---|
| **AC-1** | **Un guard de PRODUCTO**: sobre el corpus sintetico, el informe del validador tiene que traer **≥1 `[FAIL]` que nombre al mutante CONTRADICTORIO** y **0 `[FAIL]` que nombren al COHERENTE**, con el REGISTRO presente | celda D1; **es el AC que distingue la solucion de la ingenua**: un guard de forma (M-93) no lo cumple |
| **AC-2** | **CONTRAPROUEBA**: con el cuerpo del gate vaciado y el REGISTRO puesto, el `[FAIL]` del contradictorio **desaparece** y el REGISTRO **sigue** | celda D2; sin esta celda, AC-1 podria cumplirse por un motivo equivocado (la clase A11 del panel) |
| **AC-3** | **El recuento NO cambia**: 235 = 159 + 76; **ningun `test_*` nuevo**; las cinco declaraciones (`AGENTS.md:70`, `README.md:63`, `STATUS.md:12`, `STATUS.md:132`, `docs/ai/testing-guide.md:57`) intactas; la **fila 130** de la tabla de `docs/ai/testing-guide.md` actualizada con la seccion (D) | `vd._recuento_de_tests('run_tests.py')` → (235, 235, [], []); el validador lo deriva y lo exige |
| **AC-4** | **El coste se mide y se declara**: el guard cuesta **dos corridas del validador sobre el esqueleto** ≈ **9 s** (medido: 4,44 s + 4,17 s) = **1,2 %** de la suite de 735 s; el **coste marginal del validador no cambia** (10,2 ms / 0,091 %, dentro del 0,5 %) | medicion en camara; el numero va en el docstring del test y en `docs/ai/testing-guide.md` |
| **AC-5** | **Mutantes declarados**: M-90, M-91, M-92 y M-93, cada uno con su **asercion** y su **por que no es EQUIVALENTE** (§7) | el `mutation-auditor` los mide y emite `WOPT_VEREDICTO` |
| **AC-6** | **El limite nuevo, declarado**: el bloque «LO QUE ESTE GATE **NO** PRUEBA» de `validate_docs.py` trae el limite **(f)**: *el validador, por si solo, NO detecta un gate ciego; solo la suite lo hace*, y el docstring de la funcion lo repite | el guard de forma (B) ya exige (a)..(e) y «NO es exhaustiva»: (f) es un limite mas, no una reescritura |
| **AC-7** | **Cero regresiones**: `python run_tests.py` verde, `python validate_docs.py` **0 FAIL** (el check 11 sigue re-derivando el catalogo del ciclo 70: **162 OK / 0 FAIL**), `python verify_ui_syntax.py` verde, `src/` **intacto**, y el **contrato de la linea canonica intacto** (`.taskmaster/veredicto.py` y la re-derivacion no se tocan) | el cierre del ciclo |

---

## 7. El plan de mutacion

Los cuatro mutantes se aplican **al gate** (`validate_docs.py`), en copia, y se
miden con la **suite**. Los cuatro **conservan el REGISTRO**: por eso el guard de
cableado (D-A) **no** los ve y hace falta el de contenido.

| id | Mutacion (receta textual) | Que rompe | Por que **no** es EQUIVALENTE | Asercion por la que muere | Contraprueba |
|---|---|---|---|---|---|
| **M-90** | sustituir el cuerpo de `_comprobar_veredictos_de_mutacion` (`validate_docs.py:3138`) por el stub que **solo deja el REGISTRO** | el gate **no comprueba nada** | **MEDIDO**: el `[FAIL]` que nombraba `M-FIX-MAL` **desaparece** (P1 → P2): el veredicto sobre el corpus **cambia** | la de la celda D1 sobre el contradictorio: *«... EL GATE NO DISTINGUE ...»* | D2: el guard exige que ese FAIL **desaparezca** cuando el cuerpo se vacia, y que el REGISTRO **siga** |
| **M-91** | `validate_docs.py:3310`: `if estado_derivado != estado_declarado:` → `if estado_derivado == estado_declarado:` | el gate **acusa en lo que no puede** (da FAIL del coherente) | **MEDIDO**: `FAIL(M-FIX-BIEN)` pasa de **0** a **1** (P6): el veredicto sobre el corpus cambia | la de la celda D1 sobre el coherente: *«... EL GATE ACUSA EN LO QUE NO PUEDE ...»* | la misma celda D1: el coherente tiene que dar **0** FAIL |
| **M-92** | `validate_docs.py:3276`: `for ... in mutantes:` → `for ... in mutantes[:1]:` | el gate mira **solo el primer** mutante del catalogo | **MEDIDO**: `FAIL(M-FIX-MAL)` pasa de **1** a **0** (P7): el contradictorio es el **segundo** a proposito | la de la celda D1 sobre el contradictorio | la celda D1 con el coherente **primero** y el contradictorio **segundo** |
| **M-93** | sustituir el cuerpo por uno que **calcula el veredicto y lo tira** (`_estado_de_una_corrida(...)` sin comparar) | el gate **calcula bien y no dice nada** | **MEDIDO**: `FAIL(M-FIX-MAL)` pasa de **1** a **0** (P8). **Es el mutante que refuta el guard de FORMA**: su cuerpo conserva bucle, llamada y comparacion | la de la celda D1 sobre el contradictorio | M-93 es, precisamente, la **contraprueba del AC-1** frente a un guard de forma |

**Los cuatro mueren por una ASERCION, no por una excepcion**: el guard lee el
informe impreso (un `str`), no una estructura que pueda romperse. El unico modo de
morir por excepcion seria que el validador **reviente**, y en ese caso el informe
no traeria `Resumen:` → la celda D1 tiene que distinguirlo **explicitamente**
(la asercion exige `Resumen:` y el REGISTRO, y su mensaje lo dice).

**El `motivo` que se declara en el catalogo** es el **substring** del mensaje de la
asercion (contrato del ciclo 70):

| mutante | `asa` | `motivo` |
|---|---|---|
| M-90, M-92, M-93 | `test_el_check_9_se_cablea_en_el_camino_real_del_validador` | `EL GATE NO DISTINGUE` |
| M-91 | el mismo | `EL GATE ACUSA EN LO QUE NO PUEDE` |

⚠️ Los dos mensajes tienen que **terminar** en esa frase: la re-derivacion mira la
**ULTIMA** linea de la cola del log (`validate_docs.py:3038`).

---

## 8. Los riesgos

| Riesgo | Por que importa | Como se acota |
|---|---|---|
| **El guard se acopla al esqueleto**: si el validador anade una lectura nueva, el esqueleto se queda corto | el propio `_copiar_el_esqueleto_del_validador` lo avisa (A12) | el guard **filtra por centinela**, no por el total de FAILs: los FAILs de otros checks no le affectan |
| **El filtro por centinela puede enmascarar un FAIL real** | un FAIL que no nombre al centinela pasaria | el guard exige **las dos** mitades (contradictorio y coherente) y el REGISTRO; ademas, la celda D2 exige que el FAIL **desaparezca** con el cuerpo vaciado → si el filtro no mirara nada, D2 no podria distinguir |
| **El corpus depende de la forma del catalogo** (que el gate lee `mutaciones`, `mutation-report.md`, `evidencia/<id>.cola`) | un cambio de formato del contrato rompe el guard | el guard **falla** (no se calla) si el formato cambia: el centinela no aparece → la asercion de D1 muere |
| **El coste**: dos corridas del validador ≈ 9 s | 1,2 % de la suite | declarado en AC-4; y se puede bajar a **1,2 s** con un `run_tests.py` minimo en el esqueleto (P5), **si** se acepta que el esqueleto deje de ser el real — decision del dev, con la cifra a la vista |
| **D-H puede romper este guard** | al leer el campo `mutacion`, un `mutacion` incoherente **nombraria al centinela** | el corpus declara un `mutacion` **coherente** con su arbol desde ahora (§5.3) |
| **Un `test_*` nuevo seria mas limpio** | un `asa` dedicado | el recuento **no puede** moverse (AC-3) y el precedente del ciclo 70 ya extiende este test |

---

## 9. Fuera de alcance

- **D-H / TASK-091**: el campo `mutacion` del catalogo. Ciclo aparte (§4).
- **TASK-088** (la familia de fixtures), **TASK-089** (el arbol que se mueve),
  **TASK-080** (`validate_docs.py` en CI): deuda encolada, no tocada.
- **El contrato de la linea canonica** (`.taskmaster/veredicto.py`, la gramatica,
  los tres estados): **intacto**.
- **`src/woptimizer/`**: cero ediciones.
- **El `REGISTRO`**: no se cambia su formato; solo se le exige que siga presente.

---

## 10. La cifra del encargo, revisada

El encargo de este turno cita `STATUS.md:127` como la quinta declaracion del
recuento. La linea viva es **`STATUS.md:132`** («4. **Tests:** `python run_tests.py`
(235 tests)»); la 127 es ahora el encabezado «Recordatorios para el Agente» (la de «TASK-068 está bloqueada» es la 44). Es la misma clase que
**P2** del panel (una cita por numero de linea que se caduca): la fifth declaracion
es `STATUS.md:132`, y las cinco son `AGENTS.md:70`, `README.md:63`,
`STATUS.md:12`, `STATUS.md:132`, `docs/ai/testing-guide.md:57`.
