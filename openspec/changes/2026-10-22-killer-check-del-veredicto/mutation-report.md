# Informe de mutacion del ciclo 70 — el killer-check del veredicto (TASK-087)

> **Quien escribe esto:** la parte del **Paso 3** (el dev) del ciclo 70, con el
> caso real **M-3** medido en camara. El **Paso 4** (`mutation-auditor`) escribe
> **su** informe en este mismo fichero cuando audite los fixes de este ciclo, y
> **sustituye** el `mutaciones.json` del cambio por el del ciclo (el catalogo es
> **del ciclo**: si el cambio ya traia uno de otra vuelta, se sustituye, no se
> amplia).
>
> El **bloque de maquina** del final es lo que el gate lee: las lineas
> canonicas del veredicto. Si el Paso 4 escribe otras lineas, el bloque tiene
> que llevar **esas**, no estas.

## 0. Que se cierra en este ciclo

MEDIDO por el arquitecto en camara desechable, antes de este ciclo:

| Qué se borra | Qué pasa |
|---|---|
| el **veredicto** del journal | **0 FAIL** |
| el **`mutation-report.md`** entero | **0 FAIL** |
| una **fila** del journal | 1 FAIL |

O sea: la fila estaba vigilada, **el veredicto y el informe no**. El agujero no
era el mecanismo, era el **conjunto de sujetos**: no era derivable, luego se
podia vaciar sin que nadie lo notase.

Ademas el veredicto **no tenia tres estados** ni «asa esperada»: `agent.md:116`
solo decia `killed`/`survived`, y el instrumento real del auditor sacaba
rc/bytes/ultima linea, **no el nombre del test que murio**.

## 1. Lo que hay ahora

| Pieza | Fichero | Que hace |
|---|---|---|
| Emisor | `.taskmaster/veredicto.py` | del catalogo + las colas de los logs, deriva el estado y escribe la linea canonica |
| Gate | `validate_docs.py`, check 11 | **re-deriva** cada veredicto desde la evidencia commiteada y falla si no cuadra |
| Catalogo | `openspec/changes/<id>/mutaciones.json` | lo declara **quien muta**: el `asa` y el `motivo` |
| Evidencia | `openspec/changes/<id>/evidencia/<mutante>.cola` | la cola del log, commiteada |

La linea canonica:

```
WOPT_VEREDICTO <mutante> <MUERTO|SOBREVIVIENTE|NO MEDIDO> <sha>
```

## 2. El caso real: M-3 (el reloj de la fixture sin clavar)

**La mutacion** (la real del ciclo 69, `run_tests.py:23459-23460`): la fixture
deja de clavar la fecha del commit, luego el sha de la fixture varia y el hash
MUERTO puede coincidir con un objeto real.

```python
# original
    for v in variables:
        os.environ[v] = fecha_iso
# sustituto
    for v in variables:
        os.environ.pop(v, None)
```

**El `asa` declarada** (la declara quien muta, en el catalogo):
`test_el_pre_vuelo_de_un_hash_muerto_distingue_existe_de_no_existe`.
**El `motivo` declarado**: `EL RELOJ DE LA FIXTURE NO ESTA CLAVADO`.

**Las cuatro corridas REALES** (camara nueva de este ciclo, con el indice del
repo real replicado, sha del arbol auditado `e8111158`; cada corrida, la
suite COMPLETA: 200,9 s / 206,8 s / 208,2 s) y lo que diede cada una:

| Corrida | rc | Que murio | Motivo literal | Veredicto de la corrida |
|---|---|---|---|---|
| 1 | 1 | `test_el_pre_vuelo_de_un_hash_muerto_distingue_existe_de_no_existe` | `... y el commit REAL lleva 1792663532 s: EL RELOJ DE LA FIXTURE NO ESTA CLAVADO` | MUERTO |
| 2 | 1 | `test_el_hash_muerto_se_deriva_por_construccion_y_no_por_concatenacion` | `el sha de la fixture (ba26b819...) tiene que tener '0' en la 8.a cifra hexadecimal` | NO MEDIDO |
| 3 | 1 | `test_el_hash_muerto_se_deriva_por_construccion_y_no_por_concatenacion` | `el sha de la fixture (752f585d...) tiene que tener '0' en la 8.a cifra hexadecimal` | NO MEDIDO |
| 4 | 1 | `test_el_hash_muerto_se_deriva_por_construccion_y_no_por_concatenacion` | `el sha de la fixture (aec78c1e...) tiene que tener '0' en la 8.a cifra hexadecimal` | NO MEDIDO |

**El veredicto del mutante: NO MEDIDO.** Una corrida muere por el **asa**
(el pre-vuelo, con el motivo que nombra la infraccion) y tres mueren por el
**tripwire** (motivo probabilistico de la 8.ª cifra), luego las cuatro NO
coinciden. Un mutante no determinista no puede aportar la muerte de un
mutante: repetir la medicion N veces SIN exigir consistencia hace la
probabilidad de veredicto falso MAS ALTA (`1-(1-p)^N`: con p=1/16, N=3 ->
17,6 %, N=5 -> 27,5 %), y exigir consistencia cuesta N Suite (N=3 -> 2 205 s
por mutante) sin tapar el agujero de fondo.

**La distribucion es la misma que la del ciclo 69** (1 de 4 en el pre-vuelo y
3 de 4 en el tripwire), con lo que la reproduccion confirma el hallazgo.

**Esto es lo que MATA K-6** (el gate que solo mira «el log esta rojo»): con el
log en ROJO y sin mirar el asa, el gate daria MUERTO. La verdad es NO MEDIDO.

## 3. El gate NO se puede vaciar (AC-7), en camara

Cada celda monta una camara NUEVA (copia del repo, sin `.git`), deja el arbol
en el estado que la celda describe, y corre `validate_docs.py` AHI. El
conjunto de sujetos lo pone el journal (una entrada del ciclo 70 con su
campo `change` y sus lineas canonicas), y el `## CYCLE-070` de los dos
changelogs, como los escribe el orquestador al cerrar el ciclo.

| Celda | Estado | Resultado |
|---|---|---|
| (d) | todo en su sitio | **0 FAIL** y el REGISTRO: `entradas cubiertas=1, mutantes re-derivados=1` |
| (a) | borrar **una** linea canonica del journal | **2 FAIL**: `la entrada del ciclo 70 NO tiene linea canonica para el mutante M-3` + `el bloque de maquina NO lleva las mismas lineas canonicas que el journal` |
| (b) | borrar el `mutation-report.md` | **1 FAIL**: `mutation-report.md: NO EXISTE. El informe del ciclo es el segundo testigo del veredicto` |
| (c) | el filtro de epoca se queda en el futuro (conjunto VACIO) | **0 FAIL**, el REGISTRO dice `entradas cubiertas=0, mutantes re-derivados=0` y **no hay ninguna linea de `[OK]` del check 11**: no hay verde por omision |

El (c) es el que importa: sin el, un gate sin sujeto se leeria como un gate
que lo comprobo todo.

## 4. Los mutantes del gate (K-1..K-7)

Metodologia: DOS celdas por mutante, con control positivo. La celda **SANO**
es el gate sin mutar con el estado que el mutante dejaria pasar; la celda
**MUTADO** es el gate (o el emisor) con la mutacion aplicada y el MISMO
estado. Si el mutante se cuela, el estado pasa de FAIL a SIN FAIL: ese par es
la prueba de que la guarda que lo pilla es ESA.

| id | Que rompe | Que lo pilla | Motivo literal de la muerte | Veredicto |
|---|---|---|---|---|
| **K-1** | el emisor dice MUERTO porque el log esta rojo, sin mirar el asa | el gate re-deriva desde la evidencia | `el mutante M-3 esta declarado como MUERTO y la evidencia commiteada obliga a NO MEDIDO (dos corridas del mismo mutante dan veredictos distintos)` | **MUERTO** |
| **K-2** | la gramatica acepta cualquier cosa (`match` en vez de `fullmatch`) | la gramatica estricta | `la entrada del ciclo 70 tiene una linea de veredicto que NO obeyece la gramatica: 'WOPT_VEREDICTO M-3 NO MEDIDO <sha> (con coletilla)'` | **MUERTO** |
| **K-3** | el asa se compara por prefijo | la igualdad EXACTA | `el mutante M-3 esta declarado como NO MEDIDO y la evidencia commiteada obliga a MUERTO (murio test_el_pre_vuelo_..._Y_UNO_MAS ...)` | **MUERTO** |
| **K-4** | se cae el chequeo del motivo | el substring del motivo literal | `... y la evidencia commiteada obliga a MUERTO (murio test_el_pre_vuelo_... por su asercion)` | **MUERTO** |
| **K-5** | el asa declarado no tiene que existir en la suite | el `ast` sobre `run_tests.py` | `mutaciones.json: el asa declarada por M-3 (test_que_no_existe_en_la_suite) NO es un test definido en run_tests.py` | **MUERTO** |
| **K-6** | el gate solo mira «el log esta rojo» (el caso REAL M-3) | el asa y el motivo | `el mutante M-3 esta declarado como NO MEDIDO y la evidencia commiteada obliga a MUERTO` | **MUERTO** |
| **K-7** | el filtro de epoca se deja en un futuro y el gate no ve a nadie | el REGISTRO | `REGISTRO entradas cubiertas=0, mutantes re-derivados=0` + **ninguna** linea de `[OK]` del check 11 | **MUERTO** (no verde por omision) |

Los siete se matan. **K-1** y **K-6** son los que importan: los dos son el
mismo agujero (confiar en el ROJO) medido desde los dos lados, y los dos caen
con el corpus REAL de M-3.

## 5. Los costes medidos

| Que | Coste MEDIDO | Presupuesto |
|---|---|---|
| **el emisor** (`.taskmaster/veredicto.py`) | **7,1 ms** para 13 mutantes (escribe 13 evidencias y 13 lineas) | ≤ 10 ms por ciclo |
| **el gate** (check 11) con el arbol ya parseado | **10,2 ms** (min) / 10,4 ms (mediana) de 5 corridas | ≤ 0,5 % de 11,28 s = 56 ms |
| **el gate** por diferencia de dos validadores enteros | **-30 ms**, o sea **por debajo del ruido** de la medicion | idem |
| **el gate EN FRIO** (con el `ast.parse` dentro) | 3 713 ms | el parseo lo pagaba el validador DOS veces (11 401 ms); con la cache por contenido, **UNA** |
| **el validador entero** | de **11 401 ms** a **~4 350 ms** | — |
| **correridas extra de la suite** | **0** | 0 |

El `ast.parse` de `run_tests.py` (1,64 MB) cuesta **3 459 ms** y el validador lo
pagaba dos veces (el recuento y el reparto). El gate necesita el arbol para
comprobar que el `asa` existe, luego con una cache por contenido el parseo se
paga **una** vez y el gate no paga el arbol: su coste marginal son los **10,2
ms** de leer el journal, el catalogo y las 13 evidencias y re-derivar los 13
veredictos.


<!-- WOPT_VEREDICTOS -->
WOPT_VEREDICTO M-3 NO MEDIDO e811115886a8de68bbcd338c11aaa426477caeb5
<!-- /WOPT_VEREDICTOS -->
