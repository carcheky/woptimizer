# Informe de mutacion — ciclo 71 (TASK-090) — **RONDA 2**

> Re-auditoria del guard de PRODUCTO **despues** de la reparacion del dev
> (`5fed36a`, "el corpus del guard ejercita todas las ramas del gate"). La ronda
> 1 dio **VERDICT FAIL** (4 supervivientes: `M-94`, `M-95`, `M-99`, `M-100`);
> aqui se vuelve a medir, con el arbol reparado, y se anaden 7 mutantes
> **propios** sobre las ramas del gate que el corpus ampliado puede seguir sin
> vigilar.

## 1. QUE SE HA MEDIDO

**18 mutantes, TODOS con la SUITE COMPLETA** (`python run_tests.py`, 32.208
lineas) en camara desechable — no con el test suelto:

* los **11 del catalogo** (`M-90` … `M-100`), que la ronda 1 ya habia medido;
* **7 mutantes PROPIOS** (`M-101` … `M-107`), nuevos.

Todos comparten el mismo **asa**: `test_el_check_9_se_cablea_en_el_camino_real_del_validador`.

**Resultado: 13 MUERTO, 5 SOBREVIVIENTE, 0 NO MEDIDO.**

## 2. EL INSTRUMENTO (y por que sus numeros son creibles)

| pieza | como |
|---|---|
| camara | `%TEMP%\wopt_c71_r2_camara{1,2,3}`, copia con `shutil.copytree(..., ignore=shutil.ignore_patterns(".git"))`: el `.git` del repo real es un **FICHERO** de 57 bytes (`gitdir: ...`) y `robocopy /XD .git` NO lo excluye (esa via ya.contamino el repo real dos veces) |
| aislamiento | **PROBADO antes de mutar nada**: sin `GIT_DIR`, `git rev-parse --git-dir` dentro de la camara devuelve salida vacia y rc=128 → la camara **no descubre el repo real**. Con `GIT_DIR` explicito devuelve la camara, nunca `%LOCALAPPDATA%\woptimizer_git\.git` |
| git por intento | cada camara lleva su PROPIO `.git` (un **directorio**, no un puntero), **recreado en cada mutante**: es el `GIT_DIR` desechable y nuevo de cada intento |
| `__pycache__` | purgado entre mutaciones (un `.pyc` obsoleto es veredicto FALSO) |
| restauracion | cada mutante se aplica **siempre** desde el texto PRISTINO (el del repo real, leido). Un `original` que aparece != 1 vez **ABORTA** el script: no se muta una linea equivocada (y asi se detecto un fallo mio de instrumentacion, §6) |
| shas | `sha_arbol_auditado` = el commit de la camara con el arbol **MUTADO** que produjo la evidencia (uno por mutante). **VERIFICADO** sobre las tres camaras cuyo `.git` sigue en pie (`M-95`, `M-101`, `M-104`): el arbol del commit contiene el `sustituto` y su `HEAD` coincide con el sha del catalogo. **Limite que conviene saber**: como el `.git` de cada camara se recrea en cada intento (protocolo de aislar), solo el sha del **ultimo** mutante de cada camara sigue resolviendo; los demas identifican un arbol que existio en esa camara en ese momento (es el limite (e) del gate: el sha no se resuelve contra ningun objeto) |

**Linea base** (sin mutar, en la camara): **rc=0, 373 s, ultima linea
`ALL TESTS PASSED.`**. Sin ese suelo, un "superviviente" no seria
superviviente, seria una suite que no corrio. Todos los `SOBREVIVIENTE` de
esta tabla tienen la **suite completa** en verde: rc=0, 365-417 s, sin un
solo `[FAIL]`.

## 3. LA TABLA

`motivo` = la **ultima linea literal** de la cola del log (lo que el emisor
re-deriva; el `motivo` declarado en el catalogo es un substring de esa linea).

| mutante | fichero:linea | que rompe | veredicto | motivo literal |
|---|---|---|---|---|
| M-90 | `validate_docs.py:3182` | el CUERPO del gate vaciado y el REGISTRO puesto | **MUERTO** | `EL GATE NO DISTINGUE` |
| M-91 | `validate_docs.py:3327` | la comparacion del veredicto **invertida** (`!=` → `==`) | **MUERTO** | `EL GATE ACUSA EN LO QUE NO PUEDE` |
| M-92 | `validate_docs.py:3293` | el gate solo mira el **primer** mutante del catalogo (`mutantes[:1]`) | **MUERTO** | `EL GATE NO DISTINGUE` |
| M-93 | `validate_docs.py:3327` | el veredicto se CALCULA y se TIRA (bucle, llamada y comparacion se conservan) | **MUERTO** | `EL GATE NO DISTINGUE` |
| M-94 | `validate_docs.py:3293` | el gate solo mira los mutantes **menos el primero** (`mutantes[1:]`) | **MUERTO** | `EL GATE NO DISTINGUE` |
| M-95 | `validate_docs.py:3196` | el gate solo mira la **primera** entrada del journal (`[:1]`) | **MUERTO** | `EL GATE NO DISTINGUE` |
| M-96 | `run_tests.py:22855` | el corpus NO se monta (el journal sintetico no se escribe) | **MUERTO** | `EL GATE NO DISTINGUE` |
| M-97 | `run_tests.py:22733` | el sentinela **coherente** deja de ser coherente (declarado SOBREVIVIENTE, evidencia MUERTO) | **MUERTO** | `EL GATE ACUSA EN LO QUE NO PUEDE` |
| M-98 | `run_tests.py:22945` | D3 NO restaura el esqueleto (la copia mutada contamina lo que venga) | **MUERTO** | `AssertionError: el validador del esqueleto tiene que quedar como estaba: una copia mutada contaminaria las secciones que vienen despues` |
| M-99 | `validate_docs.py:3327` | el gate decide por la **DECLARACION** y no por la EVIDENCIA | **MUERTO** | `EL GATE NO DISTINGUE` |
| M-100 | `validate_docs.py:3050` | el **motivo literal** de la evidencia ya no se comprueba | **MUERTO** | `EL GATE NO DISTINGUE` |
| M-101 | `validate_docs.py:3260` | el gate **no lee el campo `veredictos`** del journal (las lineas solo salen del `status`) | **MUERTO** | `EL GATE NO DISTINGUE` |
| M-102 | `validate_docs.py:3302` | el gate **no comprueba el sha**: la linea puede apuntar a un arbol que NO es el auditado | **SOBREVIVIENTE** | — (suite completa en VERDE) |
| M-103 | `validate_docs.py:3308` | el gate **no comprueba que el `asa` sea un test definido** | **SOBREVIVIENTE** | — (suite completa en VERDE) |
| M-104 | `validate_docs.py:3048` | el gate **acepta una evidencia cuyo frame es OTRO test** (declara MUERTO una muerte que no fue la del asa) | **SOBREVIVIENTE** | — (suite completa en VERDE) |
| M-105 | `validate_docs.py:3360` | el gate **no compara el bloque del informe con el del journal** (el segundo testigo se desacopla del primero) | **SOBREVIVIENTE** | — (suite completa en VERDE) |
| M-106 | `validate_docs.py:3337` | el gate **no acusa** a un mutante que este en el journal y NO en el catalogo | **SOBREVIVIENTE** | — (suite completa en VERDE) |
| M-107 | `.taskmaster/veredicto.py:314` | el emisor vuelve a **pisar la evidencia ajena** (escribe tambien la de los mutantes sin corrida) | **MUERTO** | `AssertionError: el emisor NO puede reescribir la evidencia de un mutante que no se le ha pasado: la evidencia de M-3 ha cambiado.` |

**Nota sobre el catalogo**: el campo `origen` de `M-94` dice "el gate solo mira
el **ULTIMO** mutante del catalogo (el espejo de M-92)", pero su sustituto real
es `mutantes[1:]` (todos **menos el primero**): la prosa del catalogo no
describe la mutacion que se midio. No lo he cambiado (el catalogo es del
dev y lo reescribo con las lineas y los shas reales); lo dejo dicho porque un
`origen` que no describe su propia mutacion es el mismo genero de fallo que
una cita que no sostiene su frase.

## 4. LOS CUATRO SUPERVIVIENTES DE LA RONDA 1: **ahora MUERTOS**

La reparacion del dev (`5fed36a`: corpus de **5 sentinelas** + **2 entradas** de
journal) **funciona** para los cuatro que se le escaparon a la ronda 1:

| mutante | ronda 1 | ronda 2 | por que ahora muere |
|---|---|---|---|
| M-94 | SOBREVIVIENTE | **MUERTO** (`EL GATE NO DISTINGUE`) | con 5 sentinelas, dejar fuera el primero (`mutantes[1:]`) deja fuera al **contradictorio**: el gate calla y D1 lo nota |
| M-95 | SOBREVIVIENTE | **MUERTO** (`EL GATE NO DISTINGUE`) | con **2 entradas** de journal, mirar solo la primera (`[:1]`) deja la contradiccion sin examinar |
| M-99 | SOBREVIVIENTE | **MUERTO** (`EL GATE NO DISTINGUE`) | decidir por la declaracion acusa tambien al centinela **invertido** (declarado MUERTO, evidencia verde), y ese `[FAIL]` no es el esperado |
| M-100 | SOBREVIVIENTE | **MUERTO** (`EL GATE NO DISTINGUE`) | sin comprobar el motivo, el centinela del **motivo equivocado** se deriva MUERTO en vez de NO MEDIDO, y el `[FAIL]` sale distinto |

Los 11 mutantes del catalogo del ciclo **mueren todos**. La reparacion del dev
esta **validada**.

## 5. LOS SIETE MUTANTES PROPIOS: dos mueren, cinco sobreviven

* **`M-101` MUERTO** — el guard **ve** que el gate ignore el campo `veredictos`
  del journal: sin sujeto que juzgar, el gate acusa por ESTRUCTURA y no por
  JUICIO, y la asercion de D1 (`EL GATE NO DISTINGUE`) lo caza. El guard
  vigila de verdad **de donde sale el veredicto**.
* **`M-107` MUERTO** — la seccion **(C)** del guard sigue viva: el emisor que
  vuelve a pisar la evidencia ajena muere en
  `el emisor NO puede reescribir la evidencia de un mutante que no se le ha pasado`.
  La proteccion del ciclo 70 no se ha roto con la ampliacion del corpus.

### Los cinco supervivientes: son HALLAZGOS, no ruido

Los cinco caen en la **misma familia**, y el nombre de esa familia lo dice el
propio test: la seccion (D) monta un corpus con centinelas y exige que el gate
**ACUSE al contradictorio y CALLE sobre el coherente**. Es decir, el guard
vigila el **JUICIO** del gate, no su **ESTRUCTURA**. Las cinco ramas
estructurales del gate no las ejercita nadie:

| mutante | rama muerta | por que importa | arreglo que necesita |
|---|---|---|---|
| **M-102** | `if sha_del_catalogo and sha_declarado != sha_del_catalogo:` → `if False and ...` (`:3302`) | **el sha es el ancla del veredicto**: con esta comprobacion muerta, una linea canonica puede apuntar a un arbol que NO es el auditado, y el gate no se entera. El catalogo y el journal pueden discrepar de arboles y el gate calla | que el corpus de la seccion (D) incluya un centinela cuyo sha de la linea **no** sea el del catalogo, y que el gate lo acuse |
| **M-104** | `if muerto != asa:` → `if muerto != asa and asa is None:` (`:3048`) | el gate **fabrica** veredictos: una evidencia que murio en OTRO test se deriva MUERTO y el gate la certifica | un centinela cuya evidencia tenga el frame de otro test, declarada MUERTO, y que el gate la derive NO MEDIDO |
| **M-103** | `if asa not in definidos:` → `if False and ...` (`:3308`) | un `asa` **inventado** (un test que no existe) pasa por bueno: el veredicto apunta a un asa que nadie ejecuta | un centinela con un `asa` que no este en `run_tests.py` |
| **M-105** | `if del_informe != del_journal:` → `if False and ...` (`:3360`) | el **segundo testigo** (el informe del ciclo) se desacopla del primero (el journal): el gate deja de exigir que las dos copias digan lo mismo | dos centinelas, uno con la linea en el journal y la del informe distinta |
| **M-106** | `if identificador not in ids_del_catalogo:` → `if False and ...` (`:3337`) | el **catalogo deja de mandar**: un mutante que este en el journal y no en el catalogo deja de acusarse | un centinela en el journal que no este en el catalogo del cambio |

**Estos cinco NO se arreglan aqui** (no soy el dueño del fix): se encolan como
tarea con su metrica (mutante, rama muerta, y el hecho de que la suite
completa queda en VERDE con la rama muerta). **Dos de los cinco tocan
SEGURIDAD/DATOS** (`M-102`: el sha que ancla el veredicto; `M-104`: la
fabricacion de un veredicto), asi que con ellos el ciclo **no se cierra** como
PASS: la regla de `SKILL.md:266` es que un hallazgo de seguridad sin medir
—o medido y vivo— no se documenta, se arregla.

**Lo que si se puede decir del guard**: con la ampliacion del corpus, el gate
**juzga bien** cuando hay sujeto (acusa al contradictorio, cala sobre el
coherente, deriva NO MEDIDO cuando el motivo no cuadra). Lo que **no** se
puede decir es que el gate *compruebe* sus propias precondiciones: las cinco
ramas de arriba son el gate con una precondicion sin comprobar.

## 6. LOS NO MEDIDO

**Ninguno.** Un NO MEDIDO se declaro y se encolaria; aqui no hay ninguno.

*Lo que casi lo fue*: la primera corrida de `M-104` murio en
`test_el_feedback_de_pack_dice_la_verdad` con
`PermissionError: [WinError 32] El proceso no tiene acceso al archivo porque
esta siendo utilizado por otro proceso` — un **fichero en uso**, la clase flaky
documentada de este repo, **no** el mutante (moria en otro test y por una
excepcion que no es la asercion del asa). Se **repitio en serie**, sin las otras
camaras compitiendo, y salio **rc=0, 376 s, `ALL TESTS PASSED.`** → ese es el
veredicto que cuenta. Un log cortado no es veredicto: es NO MEDIDO.

*Lo que casi lo fue, y es mio*: mi orquestador de la primera tanda **no
restauraba** el fichero entre mutantes, y por eso `M-91` se paro solo con
"el original aparece 0 veces" (el guard de seguridad del propio aparejo, que
funciono: no se muto ninguna linea equivocada) y la primera corrida de `M-97`
hubiera sido invalida (mutacion de `M-96` todavia presente). Corregido
(`aplicar()` aplica SIEMPRE desde el texto pristine), **los mutantes afectados
se repitieron desde cero** y los veredictos de esta tabla son de corridas
limpias. Lo declaro porque un informe que dice "no toque nada" cuando si toco
cosas es peor que uno que confiesa.

## 7. LAS CITAS (localizadas **por contenido**, no por aritmetica)

El desplazamiento de la reparacion del dev esta **MEDIDO** con git: `run_tests.py`
paso de 32.119 a 32.208 lineas (**+89**) y todo lo que esta por debajo del
bloque de la seccion (D) se movio +89. Medido linea a linea:

| texto citado | en el commit 35478ec (ronda 2) | en HEAD (ronda 3) | +89 |
|---|---|---|---|
| `` `validate_docs.py` cita `sandbox-rules.md:55-56` POR NUMERO DE LINEA `` | 23629 | **23718** | si |
| `assert min(posiciones) > 61, (` | 23627 | **23716** | si |
| `def test_las_citas_de_sandbox_rules_siguen_siendo_ciertas():` | 29515 | **29604** | si |
| `def _delitos_de_enumeracion(arbol):` | 29943 | **30032** | si |
| `def test_la_verificacion_de_sintaxis_deriva_su_alcance_y_no_lo_enumera():` | 30001 | **30090** | si |

**Las ocho citas que el dev renumero en la ronda 1 (0eb6378), al estado de hoy:**

| # | cita | donde | declarada | real | estado | de quien es la rotura |
|---|---|---|---|---|---|---|
| 1 | `run_tests.py:23718` | `run_tests.py:24032` | 23718 | 23718 | **VIVA** | — |
| 2 | `run_tests.py:23718` | `run_tests.py:29609` | 23718 | 23718 | **VIVA** | — |
| 3 | `run_tests.py:23718` | `STATUS.md:107` | 23718 | 23718 | **VIVA** | — |
| 4 | `run_tests.py:29604` | `STATUS.md:107` | 29604 | 29604 | **VIVA** | — |
| 5 | `run_tests.py:29604` | `docs/ai/testing-guide.md:1362` | 29604 | 29604 | **VIVA** | — |
| 6 | `run_tests.py:30032` | `STATUS.md:89` | 30032 | 30032 | **VIVA** | — |
| 7 | `run_tests.py:23627` | `run_tests.py:29624` (docstring del propio guard) | 23627 | **23716** | **ROTA** | **DE ESTE CICLO**: la reparacion (+89) movio la linea y la renumeracion del dev toco las dos menciones de `23629 → 23718` pero **se dejo esta**. El destino es `run_tests.py:23716` (el `assert min(posiciones) > 61, (` dentro de `test_el_motivo_de_la_exclusion_de_ci_esta_medido_y_escrito`, def en 23647) |
| 8 | `run_tests.py:30001` | `validate_docs.py:1435` | 30001 | **12749** | **ROTA** (y la renumeracion del dev la llevo a un guard **equivocado**) | la rotura de fondo es **PREEXISTENTE**: en `2116f05` (base de este ciclo) la `28734` era literalmente `    )`; el destino real es `run_tests.py:12749` (`def test_dead_code_ast_guard():`, docstring "Guard AST de codigo muerto en src/woptimizer/**", que es exactamente lo que afirma la frase) y **no se movió** (esta por encima de la zona de insercion). La renumeracion MECANICA del dev (`28734 → 30001`) la llevo a `run_tests.py:30090` = `test_la_verificacion_de_sintaxis_deriva_su_alcance_y_no_lo_enumera`: **otro guard, de otro alcance y de otro nombre**, que no sostiene la frase. Es el "renumerar no es sumar" del ciclo 68 aplicado a una cita que ya estaba rota: el arreglo mechanical no la arregla, **le cambia de rotura** |

**El `23305` viejo ya no existe** como numero vivo: la linea que la sustaining
(`POR NUMERO DE LINEA`) paso de 23305 → 23629 → **23718**, y `STATUS.md:107`
documenta las dos renumeraciones ✓.

### Dos citas mas, medidas por mi (una de ellas, con matiz)

| cita | donde | declarada | estado MEDIDO |
|---|---|---|---|
| `run_tests.py:23718` (afirmando `REGISTRO_INDECISAS`) | `openspec/changes/2026-10-19-verificacion-ui-alcance-derivado/mutation-report.md:269` | 23718 | **ROTA** (y el numero hoy **si** apunta a una linea viva, pero de OTRO texto: `REGISTRO_INDECISAS` esta hoy en `run_tests.py:25057`). **PREEXISTENTE**: la rompio `f8bc867`, antes del ciclo 68; el simbolo se movio 23718 → 23738 → 23744 → 24333 → 24472 → 24644 → 25057. Al ser un cambio ya cerrado, **se encola**, no se corrige |
| `run_tests.py:23605` | `docs/ai/testing-guide.md:1380` | 23605 | **NO es una cita del repo**: el propio texto dice "el `23605` es la linea de la **CAMARA**, no la del repo: en el repo ese patron ya no existe porque el arreglo esta aplicado", y la afirmacion de la fila es sobre el tripwire del **hash muerto** (`hash_real + '0'`). Lo que hoy ocupa la 23605 en el repo es otra cosa ("el validador tiene que llegar al final...") → el numero **colisiona** con una linea viva y puede confundir, pero la fila se autolimita. **Matiz con el encargo**: el destino propuesto `run_tests.py:24018` (`_fixture_con_reloj_clavado`, "con el RELOJ CLAVADO") **no sostiene esta afirmacion** — la fila no habla del reloj (medido: la fila no contiene la palabra), y las citas que si hablan del reloj clavado estan en **cambios cerrados** (`2026-10-22-veredicto-de-no-medido`, `2026-10-22-killer-check-del-veredicto`) → **se encolan** |

**Recuento**: de las citas del ciclo 71, **6 VIVAS, 2 ROTAS** (una por este
ciclo, una preexistente con el/url de este ciclo). Las rotas que estan en
ficheros vivos (`run_tests.py`, `validate_docs.py`, `STATUS.md`, `docs/ai/*.md`)
las arregla el orquestador en el cierre; las de cambios cerrados y changelogs
**se encolan**. La ronda 1 medio ademas **26 citas preexistentes rotas** en la
doc: ese numero no lo he re-medido (fuera del encargo de esta ronda), y sigue
sin caducar solo.

## 8. BLOQUE DE MAQUINA

Las 18 lineas canonicas, tal cual las emitio `.taskmaster/veredicto.py`. El
**journal** (entrada del ciclo 71, campo `veredictos`) y los **dos changelogs**
tienen que llevar **estas mismas 18 lineas**: el gate (check 11) re-deriva cada
veredicto desde la evidencia commiteada y exige que informe y journal digan lo
mismo.

<!-- WOPT_VEREDICTOS -->
WOPT_VEREDICTO M-90 MUERTO a7e3ed98882d
WOPT_VEREDICTO M-91 MUERTO 3bbdc7a8ecc2
WOPT_VEREDICTO M-92 MUERTO 7646bc8de2a0
WOPT_VEREDICTO M-93 MUERTO ee9caa58ec05
WOPT_VEREDICTO M-94 MUERTO 7ede3bb371d9
WOPT_VEREDICTO M-95 MUERTO 4431f8606e65
WOPT_VEREDICTO M-96 MUERTO c9bf0f7f7eec
WOPT_VEREDICTO M-97 MUERTO 3312138b8971
WOPT_VEREDICTO M-98 MUERTO 864ebd090f5a
WOPT_VEREDICTO M-99 MUERTO 8bae55c39239
WOPT_VEREDICTO M-100 MUERTO 1613d9b1dcdc
WOPT_VEREDICTO M-101 MUERTO 51fec48d400f
WOPT_VEREDICTO M-102 SOBREVIVIENTE 2a51db2dadee
WOPT_VEREDICTO M-103 SOBREVIVIENTE 554e4c6ac5d8
WOPT_VEREDICTO M-104 SOBREVIVIENTE 708fe8485891
WOPT_VEREDICTO M-105 SOBREVIVIENTE 2508d6bdd2ee
WOPT_VEREDICTO M-106 SOBREVIVIENTE d3d3c1a2b985
WOPT_VEREDICTO M-107 MUERTO a80c2cdbdbae
<!-- /WOPT_VEREDICTOS -->

## 9. VERDICT

**VERDICT: FAIL**

* Los **11 mutantes del catalogo del ciclo**: **11 MUERTOS**. La reparacion del
  dev (`5fed36a`) funciona: los cuatro que se escaparon en la ronda 1 ahora
  mueren por su asercion. **El encargo del ciclo 71 esta cumplido.**
* Los **7 mutantes propios**: **2 MUERTOS, 5 SOBREVIVIENTES**. Los cinco
  supervivientes son **hallazgos de primera clase** sobre el gate reparado: el
  guard vigila el **juicio** del gate y **no** sus **cinco precondiciones
  estructurales** (sha, `asa` definido, frame de la evidencia, bloque del
  informe, mutante fuera de catalogo). Dos de ellos tocan la seguridad del
  veredicto (`M-102`, `M-104`).
* **0 NO MEDIDO**. Nada se queda sin medir, luego no hay nada que encolar por
  falta de medicion.

Un FAIL, no un PARTIAL: no hubo ninguna comprobacion que el shell impidiera.
Lo que falla es el **sujeto**: el guard no vigila cinco ramas del gate, y las
cinco son las que hacen que un veredicto sea *fiable* y no solo *emitido*.
