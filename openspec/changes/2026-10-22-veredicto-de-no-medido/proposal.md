# Propuesta — Un veredicto de mutación no puede depender de un test no determinista

**Ciclo:** 69 · **Rama:** `beta` · **Tarea:** TASK-083 · **Módulo:** `run_tests.py` (tooling, suite) y `.agents/agents/mutation-auditor/agent.md`
**Cero ediciones bajo `src/woptimizer/`.**

---

## 0. El encargo y su respuesta en una frase

> ¿Qué debe significar "medido" cuando la suite que mide puede mentir?

**Medido significa: "el test que murió es el asa esperada de la mutación y su motivo
literal nombra la infracción".** Todo lo demás —incluido un rojo que viene de un test
no determinista— es **NO MEDIDO**, y hoy no existe ninguna regla que lo diga ni ningún
código que lo imponga. La causa del flakiness no es el reloj: es que el test construye
el "hash muerto" **a partir del hash real** (`hash_real + "0"`, `run_tests.py:23415`),
y eso existe con probabilidad **1/16** aunque el reloj esté clavado.

---

## 1. La premisa del encargo, medida

`TASK-083` (y el encargo del ciclo 69) parten de: *"el pre-vuelo de un hash falla
11 de 200 fixtures (5,50 %) porque los fixtures comparten sha dentro del mismo
segundo"*, con criterio de cierre *"0 muertes en 1000 corridas"*.

**La parte de la tasa es correcta. La de la causa y la del criterio son falsas, y se
refutan con medición propia (§2, §3, §9).**

---

## 2. La tasa real: DOS distribuciones, DOS cifras, DOS intervalos

Réplica exacta de la fixture del repo (`_repo_temporal_de_un_commit`,
`run_tests.py:13179-13187`): `git init -q` + `git -c user.email=ancla@woptimizer.invalid
-c user.name=ancla -c commit.gpgsign=false commit -q --allow-empty -m <asunto>`, y la
comprobación exacta (`_objeto_existe_en_fixture`, `run_tests.py:13132-13176`):
`git cat-file -e <hash>` con rc 0 = existe, rc 128 = no existe.

| Distribución | Fixtures | Rotos | Tasa | IC 95 % (Wilson) | Teórico 1/16 |
|---|---:|---:|---:|---|---:|
| **A) la mía** — asunto único por fixture, sin compartir segundo | 400 | 23 | **5,75 %** | **[3,86 % ; 8,48 %]** | 6,25 % ✅ dentro |
| **B) el sesgo del repo** — mismo asunto, varias fixtures por segundo | 300 | 25 | 8,33 % | [5,71 % ; 12,01 %] *(binomial: inválido, ver abajo)* | — |
| **B) a nivel de SHA distinto** (144 shas únicos) | 144 | 12 | 8,33 % | **[4,83 % ; 14,00 %]** ← el intervalo honesto | — |

**Las dos cifras coinciden: ~1/16.** La diferencia entre las dos distribuciones NO está
en la tasa, está en **la confianza**:

- En A los 400 sha son **distintos** (400/400): los ensayos son independientes y el
  intervalo binomial es válido.
- En B **293 de 300 fixtures comparten sha con otra** (tamaños de cluster: 1 → 7 shas,
  2 → 118, 3 → 19): los ensayos **correlacionan**. El intervalo binomial de B
  ([5,71 % ; 12,01 %]) **miente por ser estrecho**: el intervalo honesto, a nivel de
  cluster, es **[4,83 % ; 14,00 %]**, ~1,4 veces más ancho con la mitad de shas.
- ⚠️ **Aviso de instrumento:** mi estimador de efecto de diseño devolvió `rho = 96,6`
  (> 1, imposible), así que **no** reporto un DEFF corregido: reporto el intervalo a
  nivel de cluster, que es el que se sostiene. Instrumento roto, cifra buena.

**Consecuencia para el ciclo 68:** el auditor reportó `11/200` con `±3,16 %`
(±1,96·√(p(1-p)/200)). Con **la distribución del propio repo**, 200 fixtures son
~100 shas, no 200 ensayos independientes: ese `±3,16 %` es **demasiado estrecho**, y la
cifra 11/200 (5,50 %) sigue siendo compatible con el 1/16 teórico. **Su tasa era
correcta; su intervalo no.**

---

## 3. La causa raíz exacta (y por qué NO es el reloj)

### 3.1 La aserción

```
run_tests.py:23415
    assert _objeto_existe_en_fixture(hash_real + "0", d_hist) is False, (...)
```

`hash_real` es `git rev-parse --short HEAD` de la fixture (`run_tests.py:23392-23393`):
**7 caracteres hexadecimales**. `hash_real + "0"` son 8 hex, y `git cat-file -e`
resuelve **cualquier prefijo de 8 hex** de un objeto existente.

La fixture tiene **dos** objetos: el commit y el árbol vacío
(`4b825dc642cb6eb9a060e54bf8d69288fbee4904`). El commit coincide con `hash_real + "0"`
**si y solo si su 8.ª cifra hexadecimal es `0`**. La 8.ª cifra de un SHA-1 es
equiprobable → **P = 1/16 = 6,25 %**.

**MEDIDO: en 400/400 fixtures de la distribución A, la aserción falla si y solo si
`sha_completo[7] == '0'`.** El mecanismo está confirmado al 100 %.

### 3.2 El papel real del reloj

`_repo_temporal_de_un_commit` **no fija la fecha** (`run_tests.py:13179-13187`): el
commit usa el instante actual → el sha es **función del segundo**. Eso hace que dos
fixtures del mismo asunto en el mismo segundo **sean el mismo objeto** (medido: 293/300
en B), y por eso los ensayos correlacionan.

**Pero la probabilidad de fallo NO depende del reloj: es 1/16 para cualquier reloj.**

**MEDIDO con fecha fija** (ocho instantes distintos, `GIT_AUTHOR_DATE` =
`GIT_COMMITTER_DATE`): 8/8 pares de fixtures con la misma fecha producen **el mismo
sha**, y el pre-vuelo **falla SIEMPRE o NUNCA** — nunca "a veces". Ejemplo medido: con
`2026-01-01T00:00:0X` la 8.ª cifra del sha es `c` → el test **nunca** falla.

### 3.3 La pregunta que decide el diseño: ¿el test necesita el reloj?

**NO. El reloj es un efecto secundario**, y además **es contraproducente**:

| Arreglo candidato | ¿Arregla el flakiness? | MEDIDO |
|---|---|---|
| **Inyectar el reloj** (fecha fija) | **NO por sí solo** | Convierte el test en determinista: **falla siempre o nunca**. Con un instante afortunado es un test **100 % verde que ha perdido los dientes en silencio** (ya no ejercita el caso que lo hacía discriminante); con uno desafortunado es **100 % rojo para siempre**. |
| **Valor único por fixture** (asunto único) | **NO** | Distribución A: 400 shas distintos y la tasa **sigue** en 5,75 % ≈ 1/16. Lo único que cambia es que los ensayos dejan de correlacionar. |
| **Derivar el hash muerto POR CONSTRUCCIÓN** + **reloj clavado a un instante adversario** | **SÍ** | p = 0 y el test **sigue discriminando**. Ver §4. |

### 3.4 El instante adversario (MEDIDO y VERIFICADO contra git)

Buscado por fuerza bruta sobre el object id (con la cabecera `commit <len>\0`, que es
lo que git hashea) y **verificado con git de verdad**:

```
ts = 1735689643   ->   GIT_AUTHOR_DATE = GIT_COMMITTER_DATE = 2025-01-01T00:00:43+00:00
sha = 296cfb20fb7030f6f68afdfc508435be7a931b56      (8.ª cifra = '0'  <-- adversario)
short = 296cfb2
git cat-file -e 296cfb20   ->  rc 0   (EXISTE)  ->  el codigo VIEJO FALLA el 100 % de las veces
objetos de la fixture: [296cfb20..., 4b825dc6...]
digitos libres (hash_real+d no es prefijo de NINGUN objeto): 123456789abcdef  (15 de 16)
git cat-file -e 296cfb21   ->  rc 128 (NO existe) ->  el codigo NUEVO PASA el 100 % de las veces
```

> ⚠️ El instante es **estable para siempre**: el contenido del objeto commit depende
> solo del árbol vacío, del autor, del mensaje y del timestamp con offset explícito
> (`+0000`), así que **no depende de la zona horaria ni de la versión de git**. Y el
> `+00:00` explícito es lo que lo hace idéntico en cualquier máquina.

### 3.5 El arreglo, en una frase

**Clavar el reloj al instante adversario (para que el caso que rompe SIEMPRE se dé) Y
derivar el hash muerto por construcción (para que ese caso nunca se dé).** Las dos
mitades son necesarias: con la primera sola el test queda mudo; con la segunda sola el
test sigue siendo una moneda al aire.

---

## 4. El arreglo, con su coste medido

**Coste del arreglo: 1 llamada a git más (`cat-file --batch-all-objects --batch-check`),
MEDIDA en 0,077 s por fixture**, y el reloj clavado (0 s). Contra una suite de 735 s
es el **0,01 %**.

**La derivación nunca se queda sin digito: MEDIDO en 400/400 fixtures hay 15 de 16
digitos libres.** El caso "no hay digito libre" es imposible con esta fixture (2
objetos) pero el código tiene que **decirlo** si algún día lo hubiera.

**Y el test tiene que SEGUIR SIENDO discriminante:** tiene que **afirmar** que su
fixture sigue siendo adversaria (`sha[7] == '0'`). Sin esa aserción, un cambio futuro
del formato de commit de git dejaría el test verde **midiendo un caso que ya no
ocurre** — el guard que se apaga solo, la clase que este repo lleva dos ciclos
persiguiendo.

---

## 5. La extensión del daño: UN test, no una familia

| Medida | Resultado | Dónde |
|---|---|---|
| Tests que crean una fixture de git (sha dependiente del reloj) | **21** call sites de `_repo_temporal_de_un_commit` | `run_tests.py:1675, 13358, 13530, 13727, 13769, 13781, 17371, 17586, 17769, 21244, 21308, 21542, 21879, 22311, 22428, 22606, 23271, 23391, 23991, 24095` (+ el `def` en 13179) |
| Aserciones cuyo **sujeto** se deriva de un hash **real** | **1** | `run_tests.py:23415` |
| Hashes muertos **literales** (fijos) | 5 (`deadbee`, `beefbee`, `cafebabe`, `badc0de`, `f00dfeed`) | `run_tests.py:22011`, `run_tests.py:21884`, `run_tests.py:23394` |
| Colisiones de esos literales | **0 en 400 fixtures** (P por literal = 16⁻⁷ ≈ 3,7·10⁻⁹) | MEDIDO |
| `datetime.now()` / `time.time()` en la suite | **0** | barrido con `grep` |
| `time.monotonic()` | 4 usos, **deadlines**, no valores | `run_tests.py:83-87`, `:234-244` |
| `time.sleep` | sincronización | `run_tests.py:12085`, `:12108` |
| `random` | **con semilla** (`random.Random(20260930).shuffle`), determinista | `run_tests.py:6129` |
| `mtime` | comparación **antes/después** y un `utime` **fijo** (`1577934245_000000000`) | `run_tests.py:25573`, `:25600`, `:25757-25759`, `:25770` |

**Veredicto: el daño es UNA aserción en UN test. No es una familia.** El arreglo es
local y barato. Lo que sí es una familia son las **21 fixtures** que dependen del
reloj: hoy son inocuas porque nadie deriva de su sha salvo `23415`, y por eso hay que
**vigilar la familia**, no solo el miembro (→ TASK-088).

---

## 6. Las otras dos vías por las que el log puede mentir (MEDIDO, no supuesto)

### 6.1 El "guard de HEAD quieto" — **la premisa del encargo es FALSA en su dirección**

`run_tests.py:18115` **no es** un guard de HEAD quieto: es la aserción de que
`GIT_WORK_TREE` no se asigna de forma incondicional, dentro de
`test_el_contrato_de_codigos_esta_atado_a_cada_linea_wopt` (`run_tests.py:17937+`).

El guard real es **`_sin_contaminacion` (`run_tests.py:17889-17934`)**, con tres
testigos: (1) el índice de la sonda y su árbol de `HEAD` no contienen ninguna ruta del
repo real; (2) **el HEAD del repo real no se ha movido** (`run_tests.py:17924-17927`,
comparado **por contenido**); (3) no quedan ficheros de sonda en la raíz real.

**¿Puede dar verde con un árbol que ha cambiado? SÍ**, y **por diseño**: compara el
**HEAD por contenido**, no el *working tree*. Una modificación **sin commitear** de un
fichero del repo real es invisible para él. El docstring lo dice: *"hay otro actor
commiteando en este arbol ... y la igualdad estricta fallaria sola"*.

**Y no hay guard de SUITE que detecte que el árbol se movió durante la corrida**
(→ TASK-089). Ojo: `test_un_fallo_de_git_no_sale_con_cero` (`run_tests.py:18145`)
**no** comprueba eso: es el contrato del código de salida 1 del wrapper. La premisa
del encargo sobre ese guard también es falsa.

### 6.2 El recuento derivado con `ast` — **SÍ tiene dientes**

`validate_docs.py:21-80` deriva `defined` (funciones `test_*` de módulo) e `invoked`
(llamadas `test_*` del `__main__`) y `validate_docs.py:104-121` exige
`solo_definidos == solo_invocados == []`.

MEDIDO end-to-end sobre una raíz temporal:

| Escenario | `_recuento_de_tests` | Veredicto del validador |
|---|---|---|
| sano | `(234, 234, [], [])` | 0 errores de recuento |
| **borrada la invocación de un `test_*`** del `__main__` | `(234, 233, ['test_el_pre_vuelo_de_un_hash_muerto_distingue_existe_de_no_existe'], [])` | **3 errores nuevos**: recuento + 2 de reparto |

⇒ **NO puede dar verde con una suite que no invoca un `test_*`.** Lo que **no** ve:
las **126** funciones de módulo con prefijo `_` (el recuento no las mira). Los tres
probes del ciclo 68 eran `_`-prefijados y por eso no los contaba nadie; **hoy están
renombrados a `test_*`** (`run_tests.py:30599-30601`) y **sí** cuentan. Ese agujero
(A-C68-1) **está cerrado**.

Y lo que **tampoco** puede hacer ningún recuento: **detectar que un test es no
determinista**. Un recuento de tests no es un detector de flakiness.

---

## 7. Las opciones con su coste MEDIDO

Sea **S = el coste de una corrida de la suite, MEDIDO en este host: 734,9 s** en una
corrida **limpia** (`python run_tests.py` → rc 0, 30 645 bytes, `ALL TESTS PASSED.`);
con la medición de la tasa corriendo en paralelo la misma suite dio 734,9 s, y el
rango del repo en el ciclo 68 fue 747 / 809,9 / 816,6 s. Con 13 mutantes,
una pasada = **2,7 h**.

| Opción | Coste | Efecto sobre el veredicto FALSO (mutante vivo que muere por el flaky) | Veredicto |
|---|---|---|---|
| **(a) Determinismo en la fuente** | **0,077 s** (una llamada a git) + reloj clavado | p = 0 para esa aserción, **para siempre** | **GANADORA** |
| **(b) Repetir N veces** | **N × 734,9 s por mutante**: N=3 → **2 205 s (36,7 min)**; N=5 → 3 675 s; ×13 mutantes → **8,0 h (N=3)** | ⚠️ ** depende de la forma: si se exige **consistencia** (el mutante tiene que morir en **todas**), p^N = **0,024 % (N=3)**; si solo se exige "0 fallos" (que es lo que suena a "repetir"), la probabilidad de veredicto falso **SUBE**: `1-(1-p)^N` = **6,25 % (N=1) → 17,6 % (N=3) → 27,5 % (N=5)** | **Rechazada en su forma ingenua** |
| **(c) Lista a mano de tests "de evidencia"** | Mantener la lista | No generaliza; y es **exactamente la clase** que este repo lleva dos ciclos persiguiendo (D2, D3, P2, A-C68-1): un dato derivado escrito a mano, que se caduca en silencio | **Rechazada** |
| **(d) Que la suite mida y declare su propio flakiness** | N × S (la suite tiene que correr N veces) | El dato acaba en un artefacto escrito a mano | Rechazada en esa forma; **parcialmente recuperada** abajo |

### 7.1 El dato que mata a (b)

**Repetir sin exigir consistencia hace PEOR el problema.** Con p = 1/16, repetir N
veces da N oportunidades al test flaky de disparar: la probabilidad de **falso
"MUERTO"** pasa de 6,25 % (N=1) a **17,6 % (N=3)** y **27,5 % (N=5)**. Repetir solo
ayuda si además se exige que el veredicto sea **consistente** entre las N corridas
—y eso obliga a distinguir "el mutante murió" de "murió el flaky", que es
justo la regla que falta.

### 7.2 La variante que sí sale (y es la que se adopta)

**(d') La muerte tiene que venir del ASA ESPERADA.** El harness de mutación **ya**
captura el log; sólo hay que **extraer de él qué test murió** y compararlo con el
guard que esa mutación tenía que activar.

- Coste: **0 corridas extra**. Se apoya en el log que ya se lee.
- Efecto: un test flaky **no puede aportar la muerte de un mutante**: su rojo cae en
  "test que NO es el asa" → **NO MEDIDO**.
- Es la regla que el ciclo 68 aplicó **a mano** ("ningun veredicto de este informe se
  acepta con una sola corrida si su motivo puede ser el pre-vuelo"), y que por estar
  en prosa **se aplicó por suerte y por mérito de quien la leyó**.

---

## 8. La decisión

**Se adopta (a) + (d'):**

1. **Se arregla la fuente** (§4): el test del pre-vuelo deja de ser una moneda al
   aire. Con el instante adversario **sigue discriminando** (el código viejo muere el
   100 % de las veces) y con la derivación por construcción **pasa el 100 % de las
   veces**. El flakiness **deja de existir**, no solo de medirse.
2. **El contrato de veredicto vive en el CÓDIGO del harness** (la muerte tiene que
   venir del asa esperada) **y en la prosa** (`mutation-auditor/agent.md`, para el
   humano). El motivo está medido, no opinado: *el guard en código que obliga a
   repetir* cuesta N × 734,9 s y, sin la regla de consistencia, **empeora** el
   veredicto; *la regla escrita* depende de que el agente la lea, y este repo ya
   tiene la lección de que una instrucción escrita que se ha incumplido más de una
   vez tiene que meterse **en el código**. La única forma de tener las dos cosas sin
   pagar N × S es **meter en el código la parte que no cuesta** (el killer-check) y
   dejar en la prosa la parte que es consejo.

> Lo que **no** se hace: repetir la suite N veces por mutante (8,0 h por ciclo), ni
> mantener una lista a mano de tests de evidencia.

---

## 9. El contrato de veredicto (texto para el `agent.md` y para el código)

```
VEREDICTO DE MUTACION. Hay TRES estados, no dos, y solo el primero cuenta como
deteccion:

  MUERTO        la suite quedo en ROJO, el test que murio es EL ASA ESPERADA de la
                mutacion (el guard que esa mutacion tiene que activar) y el motivo
                literal nombra la infraccion.
  SOBREVIVIENTE la suite completa termino en VERDE (rc=0 y la ultima linea es
                'ALL TESTS PASSED.') sin ningun [FAIL].
  NO MEDIDO     TODO lo demas. En particular:
                  * log cortado (sin linea final o sin el .meta)        -> NO MEDIDO
                  * la suite muere por un test que NO es el asa esperada -> NO MEDIDO
                  * el motivo literal no nombra la infraccion           -> NO MEDIDO
                  * dos corridas del mismo mutante dan veredictos distintos -> NO MEDIDO

  UN TEST NO DETERMINISTA NO PUEDE APORTAR LA MUERTE DE UN MUTANTE. Un rojo que
  viene de un test flaky es NO MEDIDO, jamas MUERTO: repetir la medicion N veces SIN
  exigir consistencia hace la probabilidad de veredicto falso MAS ALTA
  (1-(1-p)^N; con p=1/16: N=3 -> 17,6 %, N=5 -> 27,5 %), y exigir consistencia
  cuesta N Suite (N=3 -> 2 205 s por mutante) sin tapar el agujero de fondo.
```

**Dónde vive cada parte:**

| Parte | Dónde | Por qué |
|---|---|---|
| Los tres estados y el killer-check | **código** del harness de mutación (repo) | Es lo que no cuesta y es lo que un humano no puede saltarse por descuido |
| La línea canónica del veredicto | **código** (`WOPT_VEREDICTO <mutante> <estado> <sha>`) | Es lo que el journal y el changelog citan: un veredicto sin esa línea no es un veredicto, igual que un commit sin `WOPT_COMMIT_OK` no es un commit |
| El texto de arriba, para el agente | **`mutation-auditor/agent.md`** | Es la prosa que acompaña al código; el código la hace cumplir |
| La lista de tests no deterministas | **NO se escribe a mano** | Es la clase que este repo lleva dos ciclos pagando |

---

## 10. Criterios de aceptación de la implementación (TASK-083, CORREGIDOS)

> El criterio original ("0 muertes en 1000 corridas") queda **REFUTADO**:
> 1000 corridas de la suite son **1000 × 734,9 s = 8,5 días**; y, sobre todo, **no
> mide lo que dice medir**: el criterio correcto es **cero dependencia del reloj y
> cero construcción por concatenación**, que es lo que hace el flakiness imposible.

- **AC-1 (DISCRIMINANTE).** El test del pre-vuelo clava el reloj de su fixture en
  `GIT_AUTHOR_DATE = GIT_COMMITTER_DATE = 2025-01-01T00:00:43+00:00` (ts 1735689643)
  y **afirma** que el sha de esa fixture tiene `0` en la 8.ª cifra
  (`296cfb20fb7030f6f68afdfc508435be7a931b56`). Con el código viejo
  (`hash_real + "0"`) el test **muere el 100 % de las veces** (MEDIDO:
  `git cat-file -e 296cfb20` → rc 0); con el código nuevo **pasa el 100 %**.
  *Si alguien revierte el arreglo, este test muere: por eso discrimina.*
- **AC-2.** El hash muerto **se deriva por construcción** de los objetos de la
  fixture (`git cat-file --batch-all-objects --batch-check`): se elige un dígito
  hex tal que `<short><d>` **no** sea prefijo de ningún objeto. El test **afirma**
  que existe tal dígito y **nombra** el sha y el dígito si alguna vez no lo hubiera.
  **Cero** construcciones del tipo "hash real + carácter" quedan en la suite.
- **AC-3.** El test del pre-vuelo **no depende del reloj**: MEDIDO, 200 ejecuciones
  seguidas del test aislado (**0,56 s** cada una → **112 s** en total, no 9 días)
  dan **0 fallos** y **0** variaciones entre corridas. El criterio es **cero
  dependencia del reloj**, no "un número de corridas": 200 es el umbral para que el
  1/16 (6,25 %) NO pueda esconderse (`P(0 fallos en 200) = 1,4·10⁻⁶` si el arreglo no
  estuviera), y el arreglo lo deja en **0** sin mirar el número.
- **AC-4 (tripwire).** Un guard DERIVADO con `ast` encuentra en la suite toda
  construcción de un valor bajo prueba **a partir de un hash real por concatenación**
  (p. ej. `hash_real + "0"`). Con el arreglo: **0 hallazgos**. Si alguien devuelve
  esa construcción, el guard **muerre nombrando el fichero y la línea**. El guard se
  deriva de la suite, no de una lista escrita a mano.
- **AC-5.** `python run_tests.py` sigue en **VERDE** y el recuento de tests derivado
  no cambia (234) — el arreglo no añade ni quita tests.
- **AC-6.** El docstring del test dice, en una frase, **por qué** el reloj está clavado
  (para que la fixture siga siendo ADVERSARIA) y **por qué** el hash muerto se deriva
  (para que no dependa de la suerte). Sin las dos frases, el arreglo puede deshacerse
  sin que nadie lo note.

---

## 11. Lo que NO cabe aquí (encolado con métrica)

| Tarea | Qué es | Por qué no cabe en TASK-083 |
|---|---|---|
| **TASK-087** | El **contrato de veredicto en código**: el killer-check (la muerte tiene que venir del asa esperada), la línea canónica `WOPT_VEREDICTO` y el texto de §9 en `mutation-auditor/agent.md` | Es trabajo de **método del bucle**, no de un test: toca el harness y el agente, y tiene su propia auditoría |
| **TASK-088** | Un guard DERIVADO con `ast` que vigila la **familia** de las 21 fixtures dependientes del reloj (hoy inocuas) y que exige que ningún valor bajo prueba se derive de un valor dependiente del reloj | La **extensión** es de otra tarea: AC-4 de TASK-083 vigila una construcción; esta vigila la familia |
| **TASK-089** | Un guard de **suite** que detecte que el árbol se movió durante la corrida (hoy no existe: `_sin_contaminacion` solo compara HEAD por contenido y solo dentro de las sondas) | Es deuda **de otro guard**, y tocarlo exige medir su coste en la suite |

---

## 12. Instrumento: qué se usó y qué NO se commitea

- Las mediciones de este documento salen de **tres prototipos en `%TEMP%`** (fuera del
  repo, **sin commitear**): `wopt_c69_medir.py` (tasas y mecanismo), `wopt_c69_recuento.py`
  y `wopt_c69_valid.py` (recuento derivado), `wopt_c69_adv2.py` (instante adversario),
  `wopt_c69_coste.py` (costes). Todos replican la fixture del repo y **verifican
  contra `git` de verdad**, nunca contra un modelo.
- **Cero ediciones bajo `src/woptimizer/`.** **Cero ediciones en `run_tests.py`.**
- El coste de la suite se midió DOS veces: **734,9 s** en una corrida limpia y
  **734,9 s** con la medición de la tasa corriendo en paralelo. Los dos logs tienen
  **30 645 bytes** idénticos: lo que cambia entre corridas es el reloj, no el
  veredicto.
- El repositorio real no se tocó durante las mediciones: `git rev-parse HEAD` =
  `ee0d299da70e57f557f20d6f83e9387d02ec6ed9` antes y después, rama `beta`.
