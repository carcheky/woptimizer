# Ronda 6 (commiteada en `0894e5c`) — el gate que lee la mutación (TASK-091) y el guard anti-apagón (TASK-093)

**Ciclo:** 72 · **Rama:** `beta` · **Auditor:** `mutation-auditor` (Sherlock)
**Árbol auditado:** `0f654fc6c79236a95aea5746e84f25f6bedb2386` (311 ficheros; el commit de la cámara desechable)
**Base VERDE NATIVA:** `rc=0`, última línea `ALL TESTS PASSED.`, 365,5 s, y el guard anti-apagón con `55 fichero(s) .py vigilados, 0 vias de apagado y 0 de simulacion de entrada`.
**VERDICT de la ronda 6: FAIL** — el fix de TASK-091 está sólido (12 MUERTO, 1 NO MEDIDO y 2 SOBREVIVIENTE de 15 mutantes canonicos), **pero el guard nuevo de TASK-093 se puede desconectar en silencio** (5 supervivientes EN SEGURIDAD, medidos fuera del veredicto canonico) y el veredicto canonico no es capaz de expresar su muerte.

---

## 1. Qué se auditó

| Fix | Commit | Qué promete |
|---|---|---|
| TASK-091 | `54c62a9` | El gate (check 11 de `validate_docs.py`) **lee la mutacion del catalogo**: R1 (forma), R2 (el fichero existe y esta dentro del arbol), R3 (el `cambio`), R4 (el `ciclo`). |
| TASK-091 | `54c62a9` | La suite vigila el gate: celdas (F), (F1-bis), (F2), (F2-bis), (F3), (F4), (F5) y el guard (B) con los limites (a)..(g). |
| TASK-091 | `9798402` | El blindaje anti-brick se comprueba por la **PROPIEDAD** (`s == len(vivos) and s >= 2`) y no por el numero de instancias (`s == 2`). |
| TASK-093 | `cd31f18` | El motor no puede apagar el equipo del dueno: el guard `_la_suite_no_puede_apagar_el_equipo()` ve cuatro vias de apagado y de simulacion de entrada. |

**Lo que NO se auditó** (y por qué): el recuento de tests (235 = 159 + 76) no se toca; el guard de TASK-093 **no es un `test_*`** (se invoca desde `__main__`), luego no cuenta como test ni como mutante canonico (ver §6).

## 2. Cómo se midió

- **Camara desechable** en `%TEMP%\wopt_r6_20261024\`, con `git init` PROPIO. El `.git` del repo real es un **FICHERO** (57 bytes, gitlink a `%LOCALAPPDATA%`), y se excluyo como fichero (`ignore_patterns(".git")` cubre ficheros y directorios): medido `existe .git en la camara: False`. `git rev-parse --git-dir` desde la camara devuelve la camara, nunca el repo real. **Cero escrituras bajo `src/woptimizer/` en el repo real.**
- **Cada mutacion se aplica con un parcheo EXACTO**: si el texto original no aparece el numero de veces esperado, el script aborta y la corrida NO cuenta (una mutacion que no se aplica mide otra cosa). Las 22 mutaciones se ensayaron antes de correr: `22 mutaciones: todas aplican y compilan`.
- **`__pycache__` purgado entre mutaciones** (un `.pyc` obsoleto puede cambiar el veredicto).
- **El `rc` va ARRIBA del log**: la cola que se commitea como evidencia es la del ultimo traceback, y si el `rc` quedase al final seria su ultima linea y taparia el motivo literal de la asercion.
- **Base verde antes de mutar**: sin base, un verde de mutante no significa nada.
- **El entorno de medicion es parte de la medicion:** la fixture del tripwire del sha (`run_tests.py:25361`) **clava el reloj pero no la identidad de git**, luego su sha depende del `GIT_AUTHOR_*`/`GIT_COMMITTER_*` ambiente y su comprobacion de entorno (la 8.a cifra hexadecimal tiene que ser `0`) **falla** si la identidad no es la esperada. MEDIDO: al exportar `GIT_AUTHOR_NAME=auditor` al entorno de la suite, la suite muere con `AssertionError: el sha de la fixture (8b4d236b...) tiene que tener '0' en la 8.a cifra hexadecimal` — **un fallo de entorno, no de codigo**. Ninguna de las 25 corridas de esta ronda sufrio eso (la identidad ambiente es la de siempre); pero es una precondicion **oculta** de la suite: la fixture deberia clavar la identidad igual que clava el reloj. (T-7)

## 3. La tabla (fix → mutacion → veredicto → motivo)

| Mutante | Que rompe | Mutacion | Veredicto | Motivo |
|---|---|---|---|---|
| **M-H1** | el gate NO comprueba R1 (la FORMA de la `mutacion`) | `validate_docs.py:3488` | **MUERTO** | murio `test_el_check_9_se_cablea_en_el_camino_real_del_validador` por su asercion |
| | | | | ultima linea: `EL GATE NO LEE LA MUTACION` |
| **M-H2** | el gate NO comprueba R2 (que el fichero declarado EXISTA) | `validate_docs.py:3499` | **MUERTO** | murio `test_el_check_9_se_cablea_en_el_camino_real_del_validador` por su asercion |
| | | | | ultima linea: `EL GATE NO LEE LA MUTACION` |
| **M-H3** | el gate NO comprueba R3 (el `cambio` del catalogo) | `validate_docs.py:3432` | **MUERTO** | murio `test_el_check_9_se_cablea_en_el_camino_real_del_validador` por su asercion |
| | | | | ultima linea: `EL GATE NO LEE LA MUTACION` |
| **M-H4** | el gate NO comprueba R4 (el `ciclo` del catalogo) | `validate_docs.py:3423` | **MUERTO** | murio `test_el_check_9_se_cablea_en_el_camino_real_del_validador` por su asercion |
| | | | | ultima linea: `EL GATE NO LEE LA MUTACION` |
| **M-92** (re-declarado) | el gate mira SOLO el primer mutante del catalogo | `validate_docs.py:3482` | **MUERTO** | murio `test_el_check_9_se_cablea_en_el_camino_real_del_validador` por su asercion |
| | | | | ultima linea: `EL GATE NO DISTINGUE` (la celda (D) cae antes que la (F)) |
| **M-H6** | el gate ACUSA en lo que no puede | `validate_docs.py:3540` | **MUERTO** | murio `test_el_check_9_se_cablea_en_el_camino_real_del_validador` por su asercion |
| | | | | ultima linea: `EL GATE ACUSA EN LO QUE NO PUEDE` (la celda F3) |
| **M-H7** | el limite (g) se borra del bloque canonico del gate | `validate_docs.py:2903` | **MUERTO** | murio `test_el_check_9_se_cablea_en_el_camino_real_del_validador` por su asercion |
| | | | | ultima linea: `AssertionError: el limite (g) tiene que decir el COSTE MEDIDO de comprobar el texto declarado (62,3 ms): un limite sin motivo medido es una opinion` |
| **M-H8** | el limite (g) deja de decir QUE es lo que no se comprueba | `validate_docs.py:2907` | **MUERTO** | murio `test_el_check_9_se_cablea_en_el_camino_real_del_validador` por su asercion |
| | | | | ultima linea: `AssertionError: el limite (g) tiene que decir QUE es lo que NO se comprueba: el TEXTO declarado, no la DECLARACION` |
| **M-H9** | la migracion de M-121 (el catalogo real) se rompe | `.../2026-10-22-el-gate-distingue-o-falla/mutaciones.json:339` | **MUERTO** | murio `test_el_check_9_se_cablea_en_el_camino_real_del_validador` por su asercion |
| | | | | ultima linea: `AssertionError: el catalogo REAL del repo tiene que pasar el gate con 0 FAIL: acuso ["mutaciones.json: el mutante M-121 declara ...` |
| **M-90** (re-declarado) | el cuerpo del gate se vacia (solo queda el REGISTRO) | `validate_docs.py:3343` | **MUERTO** | murio `test_el_check_9_se_cablea_en_el_camino_real_del_validador` por su asercion |
| | | | | ultima linea: `EL GATE NO DISTINGUE` |
| **M-94** (re-declarado) | el gate se salta el PRIMER mutante del catalogo | `validate_docs.py:3482` | **MUERTO** | murio `test_el_check_9_se_cablea_en_el_camino_real_del_validador` por su asercion |
| | | | | ultima linea: `EL GATE NO DISTINGUE` |
| **M-121-r6** | la celda (D1-ter)(d) y la asercion de 'entradas cubiertas' se neutralizan (recota **migrada**) | `run_tests.py:23360` | **NO MEDIDO** | murio `test_las_citas_de_sandbox_rules_siguen_siendo_ciertas` y el asa declarada es `test_el_check_9_se_cablea_en_el_camino_real_del_validador` |
| | | | | ultima linea: `AssertionError: run_tests.py:24785 ya no cita 'sandbox-rules.md:55-56': es una de las cuatro afirmaciones que atan la tabla al numero de linea` |
| **M-121-b** | la MISMA receta migrada, con **desplazamiento CERO** (12 lineas → 12) | `run_tests.py:23360` | **SOBREVIVIENTE** | la suite termino en VERDE |
| | | | | ultima linea: `ALL TESTS PASSED.` |
| **M-979a** | el blindaje deja de CONTAR los procesos de sistema que omite (el `+=` quedo debajo del `continue`) | `src/woptimizer/services/process_service.py:637` | **MUERTO** | murio `test_no_system_process_is_killable` por su asercion |
| | | | | ultima linea: `AssertionError: Todos los procesos de sistema vivos deberian contar como omitidos: s=0, vivos=2` |
| **M-979b** | el blindaje cuenta POR NOMBRE y no por instancia | `src/woptimizer/services/process_service.py:624` | **SOBREVIVIENTE** | la suite termino en VERDE |
| | | | | ultima linea: `ALL TESTS PASSED.` |

**Recuento canonico: 12 MUERTO · 2 SOBREVIVIENTE · 1 NO MEDIDO.**

## 4. Los supervivientes (y lo que necesitan)

### 4.1 `M-121-b` — la celda (D1-ter)(d) sigue sin dientes (superviviente **por diseño**, como en el ciclo 71)
La receta migrada de M-121 neutraliza la celda (D1-ter)(d) y la asercion de 'entradas cubiertas'. Aplicada **sin desplazamiento**, la suite queda **VERDE**: nadie vigila que esa celda se neutralice.
**Arreglo que necesita:** una celda (o un `test_*`) que compruebe que la celda (D1-ter)(d) EXISTE y que la asercion de 'entradas cubiertas' tambien (hoy el catalogo puede declararse vacio de efectos). Es el mismo patron que ya usa el guard (B) con los limites (a)..(g) del gate.

### 4.2 `M-979b` — la asercion por PROPIEDAD no se distingue de la por INSTANCIAS **en este host**
MEDIDO en este host: hay **2** procesos de sistema vivos (1 `lsass.exe` + 1 `winlogon.exe`), no 3. Con 2 vivos y un nombre por proceso, `s == len(vivos)` y `s == 2` son **la misma asercion**: un blindaje que contara por NOMBRE en vez de por instancia pasaria las dos. La mejora de `9798402` solo tiene mas poder cuando el host tiene **mas de dos** vivos (o alguno con nombre repetido).
**Arreglo que necesita:** el test debe afirmar la propiedad de una forma que no dependa del numero de instancias, por ejemplo comprobar que el blindaje **salta** cada proceso de sistema vivo **por su PID** (contando PIDs omitidos, no procesos), que es lo que de verdad importa: que al `lsass` no le llegue la muerte.

### 4.3 Los CINCO del guard anti-apagón (TASK-093) — **supervivientes en SEGURIDAD: el ciclo NO se cierra**
Detalle en §6. En corto: **el guard se puede desconectar en silencio** (G-1, G-1b), **la regla del `taskkill` POR NOMBRE no tiene dientes** (G-2) y **la contraprueba interna se puede trivializar** (G-9).

## 5. Los NO MEDIDO

| Mutante | Por que | Metrica para reencolarlo |
|---|---|---|
| **M-121-r6** (la receta migrada, tal cual) | la suite se pone ROJO, pero no en el asa declarada: la receta **reemplaza 12 lineas por 1** y desplaza 11 lineas, con lo que mueve la cita viva `run_tests.py:24785` y mata `test_las_citas_de_sandbox_rules_siegen_siendo_ciertas` | asa declarada: `test_el_check_9_se_cablea_en_el_camino_real_del_validador`; motivo real: `run_tests.py:24785 ya no cita 'sandbox-rules.md:55-56'`; muerte real: `test_las_citas_de_sandbox_rules_siguen_siendo_ciertas`. **La variante de desplazamiento CERO (`M-121-b`) SI se ha medido: SOBREVIVIENTE.** |
| **G-3, G-4, G-5, G-6, G-7** (guard TASK-093) | la suite se pone ROJO en `_la_suite_no_puede_apagar_el_equipo`, que **no es un `test_*`**: la cola no tiene frame de test y el veredicto canonico no puede atribuir la muerte | asa real: `_la_suite_no_puede_apagar_el_equipo` (no es un `test_*`, y no puede serlo sin romper el contrato 235 = 159 + 76); motivo real: el `AssertionError` literal de cada uno, medido en §6 |

**NO MEDIDO no es FAIL**: es "muere, pero el emisor no ve el motivo". Aqui no es un fallo de la medicion: es un **hueco del contrato** (§6.3).

## 6. El guard anti-apagón de TASK-093 (medido FUERA del veredicto canonico)

El guard se invoca desde `__main__` (por eso **no** es un `test_*` y **no** suma al recuento). Sus mutantes se corrieron con el mismo arnes (misma suite, mismos logs, mismo emisor) y se miden ademas **in-process**, para tener el motivo literal.

| Mutante | Via que rompe | Veredicto | Motivo literal medido |
|---|---|---|---|
| **G-1** | el conjunto de ficheros vigilados se vacia (`raiz` apunta a un arbol que no existe) | **SOBREVIVIENTE** | la suite termina en VERDE; el guard imprime `0 fichero(s) .py vigilados` y nadie se queja |
| **G-1b** | el `os.walk` se rompe (`for ... in ()`) | **SOBREVIVIENTE** | la suite termina en VERDE; mismo silencio |
| **G-2** | se borra la regla del `taskkill` POR NOMBRE (`/IM`) | **SOBREVIVIENTE** | la suite termina en VERDE: **la cuarta via no tiene dientes** |
| **G-3** | el guard deja de mirar los lanzadores de procesos | NO MEDIDO (muerre) | `AssertionError: TASK-093: el detector tiene que marcar CUATRO vias en la contraprueba ... Marco 2: [(5, 'una llamada directa a la API de energia'), (2, 'una importacion de simulacion de entrada')]` |
| **G-4** | el guard deja de mirar la llamada directa a la API de energia | NO MEDIDO (muerre) | el mismo `AssertionError` de las cuatro vias, con `Marco 3` |
| **G-5** | el guard deja de mirar la importacion de simulacion de entrada | NO MEDIDO (muerre) | el mismo `AssertionError` de las cuatro vias, con `Marco 3` |
| **G-6** | el guard marca el `taskkill` por PID PROPIO (el caso legitimo) | NO MEDIDO (muerre) | la contraprueba marca 7 vias, entre ellas `subprocess.run(['taskkill', '/F', '/T', '/PID', '1234'])` |
| **G-7** | el guard deja de excluirse a si mismo (la exclusion propia se acorta) | NO MEDIDO (muerre) | `AssertionError: TASK-093: hay una via de APAGADO o de SIMULACION DE ENTRADA en el repo` (se accuse a si mismo) |
| **G-8** | la contraprueba deja de exigir CUATRO marcas (`== 4` → `>= 1`) | **SOBREVIVIENTE** | la suite termina en VERDE |
| **G-9** | la contraprueba se trivializa (cuenta `>= 1` **y** se borra el bucle de motivos) | **SOBREVIVIENTE** | la suite termina en VERDE |

### 6.1 Lo que el encargo pedia medir del guard, contestado

| Pregunta | Respuesta MEDIDA |
|---|---|
| ¿El guard ve las cuatro vias? | **(a) lanzador, (b) API de energia y (c) simulacion de entrada: SI**, tienen dientes (G-3, G-4, G-5 mueren por la contraprueba). **(d) `taskkill /IM`: NO** (G-2 sobrevive): la cuarta via no la vigila nadie, porque la contraprueba **no incluye** un caso de `/IM`. |
| ¿Respeta el caso legitimo (`taskkill /F /T /PID <propio>`)? | **SI**: con G-6 (marcar cualquier `taskkill`) el guard se pone rojo en su propia contraprueba, luego esa exclusion esta vigilada. |
| ¿Se puede desconectar en silencio? | **SI**: G-1 (el conjunto vigilado vacio) y G-1b (`os.walk` roto) dejan la suite VERDE. El guard puede vigilar **cero** ficheros sin que nada se entere. |
| ¿La contraprueba interna se puede trivializar? | **SI**: G-9 (cuenta `>= 1` y sin el bucle de motivos) deja la suite VERDE. |
| ¿El guard se auto-detecta? | **SI**: G-7 (la exclusion propia se acorta) lo pone **ROJO**, no verde: se accuse a si mismo. |

### 6.2 El arreglo que necesitan los cinco supervivientes

1. **G-1 / G-1b (desconexion silenciosa):** el guard tiene que **afirmar** que ha vigilado algo: `assert vistos > 0` y, mejor, que el numero de ficheros vigilados es el que el propio repo declara. El patron ya existe en este repo (el guard de TASK-078 abre cuatro ficheros concretos y exige haberlos abierto).
2. **G-2 (la cuarta via sin dientes):** la contraprueba del guard tiene que incluir un `taskkill /IM` (por ejemplo `subprocess.run(['taskkill', '/F', '/IM', 'lsass.exe'])`) y exigir **cinco** marcas, no cuatro, con el `/PID` propio sin marcar.
3. **G-8 / G-9 (contraprueba trivializable):** la contraprueba necesita un **meta-guard**: que el propio guard compruebe que su texto de contraprueba sigue intacto (`assert len(marcas) == 4` y las cuatro motivaciones), como hace el guard (B) con los limites del gate. Sin eso, la contraprueba se puede vaciar sin que nadie lo note.

### 6.3 El hueco del contrato (por que el guard no puede entrar en el veredicto canonico)

La regla 4 del contrato exige que el `asa` declarada sea **el nombre EXACTO de un `test_*`**, y el gate lo comprueba (`asa not in definidos` → FAIL). El guard de TASK-093 **no es un `test_*`** (a proposito: el recuento 235 = 159 + 76 esta escrito a mano en cinco sitios), luego:

- sus 5 mutantes que MUEREN (G-3..G-7) quedan **NO MEDIDO** en el veredicto canonico aunque mueran con su motivo literal medido;
- sus 5 que sobreviven (G-1, G-1b, G-2, G-8, G-9) **tampoco** pueden declarar su veredicto en el catalogo: declararlos con un `test_*` cualquiera seria **inventar el asa**.

**Tarea encolada (T-1):** el contrato del veredicto canonico necesita una cuarta via para los guards que no son tests (por ejemplo: que el `asa` pueda ser el nombre de un guard declarado, con su propia lista de frames validos, como ya se hace con los `test_*`). Con el contrato actual, un guard con dientes **no puede tener veredicto canonico**, y uno sin ellos tampoco puede declararse sin mentir. Medida: 10 mutantes del guard, 5 con muerte comprobada y 5 con supervivencia comprobada, todos con el motivo literal medido en §6.

## 7. Lo que el limite (g) deja sin vigilar (medido, no opinado)

El limite (g) del gate dice que el TEXTO declarado no se comprueba. Esto no es una opinion: es un hueco, y esta ronda lo ha medido sobre el **catalogo real** del ciclo 71 (24 mutantes):

- **21 de las 24 recetas siguen aplicando** tal cual (bloque contiguo y unico) sobre el arbol de hoy.
- **3 NO aplican**: `M-90`, `M-92` y `M-94` (sus `original` apuntaban al cuerpo del gate y al `for` de cuatro campos, que el fix de TASK-091 cambio a cinco). Las tres se han **re-declarado** en este catalogo con el texto de HOY (`M-90`, `M-92` (re-declarada), `M-94`) y **las tres se han medido**: MUERTO.
- **La receta migrada de M-121 tiene un defecto que el gate no puede ver**: sustituye 12 lineas por 1 y desplaza 11 lineas, con lo que mata el test de las citas vivas. Es el unico mutante de esta ronda cuyo veredicto canonico es NO MEDIDO **por unareason de receta**, no por falta de muerte.
- La linea declarada de M-121 (`run_tests.py:23354`) esta **6 lineas** por detras de la real (23360): el gate no comprueba la linea (limite (g)), asi que el desfase no lo ve nadie. Las recetas de este catalogo declaran la linea **real** de cada bloque.

## 8. La camara: lo que se perdio, y por que no afecta a las mediciones
### 8.0 Lo que el gate ACEPTA (simulado antes de que el orquestador commitee)

La entrada de journal del ciclo 72 todavia no existe (es del orquestador). Para no dejarle una sorpresa, la he **simulado en camara**: se copia el repo, se anade al journal una entrada `cycle=72`, `change=openspec/changes/2026-10-23-el-gate-lee-la-mutacion` con las 15 lineas canonicas de este informe, y se pasa el validador.

La simulacion **atrapo cuatro fallos reales** que ya estan corregidos:

1. **Los ids `979-a` y `979-b` no obedecian la gramatica** (`WOPT_VEREDICTO <mutante> ...` exige que el mutante **empiece por letra**): ahora son `M-979a` y `M-979b`.
2. **`M-121` colisionaba** con el `M-121` del ciclo 71 (que dice SOBREVIVIENTE): el gate lleva un unico estado por identificador, luego la re-declaracion es `M-121-r6` y la variante de desplazamiento CERO es `M-121-b`.
3. **`M-92` re-declara** el `M-92` del ciclo 71: ambos mueren por su asercion, luego los estados coinciden y no hay colision.
4. **`M-H5` era el `M-92` re-declarado** (misma receta): ahora el id es `M-92` y la receta queda en el sitio que le toca.

Con esas correcciones, el validador en la camara deja **solo los 2 FAIL que son del orquestador**: que `CHANGELOG.md` (raiz) y `.taskmaster/CHANGELOG.md` **no tienen todavia la entrada del ciclo 72** con las 15 lineas canonicas. Todo lo demas (el `cambio`, el `ciclo`, los 15 `asa` como `test_*` definidos, la evidencia commiteada de cada mutante y el bloque de maquina) lo acepta el gate.

### 8.1 Lo que se perdio

La camara *pristine* (`cam_r6`) **perdio ~180 ficheros** (entre ellos `src/woptimizer/services/process_service.py`) **despues** de las mediciones. Medido:

- las dos camaras de trabajo (`cam_a`, `cam_b`) estan **intactas** (su propio `git status --porcelain` solo muestra la ultima mutacion pendiente), y **todas las corridas de mutante se hicieron ahi**;
- la base verde (19:58-20:04) y el commit del arbol auditado (19:58) son anteriores a la perdida;
- el **repo real esta intacto** (`git status --porcelain` solo muestra los dos scripts de sondeo del §9);
- la perdida seriu en un solo mutante: `979-b` (primera receta, dos parches), que **no aplico** porque el fichero que necesitaba ya no estaba en la pristine. Se ha vuelto a medir con la receta de un solo bloque (`979-b`, la que declara este catalogo): SOBREVIVIENTE.
- camara por camara, `cam_p2` (la pristine reconstruida a las 20:40) sale **completa** (0 lineas de estado) y **su arbol es IDENTICO al auditado** salvo `.taskmaster/tasks.json` (el tablero del orquestador, un commit mas adelante). El codigo auditado es el mismo byte a byte.
- **La camara final** (`cam_final3`, copia limpia del repo de las 21:45) queda **VERDE** (`rc=0`, `ALL TESTS PASSED.` como ultima linea) y **intacta**: `git status --porcelain` da **0 lineas ANTES y 0 DESPUES** de la suite. Es decir: **la suite NO borra ficheros del arbol en el que corre**; lo que perdio `cam_r6` fue el **copiado** desde el VFS de Nextcloud (T-6), no la medicion.

**Conclusion:** el arbol medido es el que se declara, y el repo real no fue tocado por la camara. Lo que **no** puedo afirmar es la causa de la perdida (no la reproduje de forma controlada): la copia desde el VFS de Nextcloud a `%TEMP%` no es de fiar y hay que **verificar la copia (`git status` de la camara) antes de medir**.

## 9. CONFESION: dos scripts de sondeo mios entraron en el commit `952cfae`

Yo, el auditor, escribi **siete** scripts de sondeo (`probe_journal.py`, `probe_cat.py`, `probe_cat2.py`, `probe_bloque.py`, `probe_vivos.py`, `probe_ids.py`, `probe_m121.py`) **en la raiz del repo** (contra la regla de cero escrituras). De ellos, **dos** (`probe_journal.py`, `probe_cat.py`) los arrastro al commit `952cfae` ("docs(security): el dueno deja Windows Update como esta...") un **`git add -A` paralelo del orquestador**; los otros cinco los borre antes de que entrara en ningun commit. Los dos que quedaron dentro **los he borrado del arbol** (`rm --` via el lanzador de confianza); **el indice del repo real todavia los tiene**, y el siguiente commit que los elimine es del orquestador, no mio. Los dos ficheros no tienen nada que ver con el fix auditado (son scripts de lectura), pero el commit los lleva dentro y eso es culpa mia.

(Los siete scripts estan hoy en `%TEMP%\wopt_r6_tools\`, fuera del repo: a partir de ahi todo lo mio se escribe fuera del arbol.)

## 10. Lo que queda encolado

| # | Que queda | Metrica |
|---|---|---|
| **T-1** | El veredicto canonico no puede expresar un guard que no es `test_*` | 10 mutantes del guard de TASK-093: 5 con muerte comprobada (G-3..G-7, con su `AssertionError` literal) y 5 con supervivencia comprobada (G-1, G-1b, G-2, G-8, G-9). El `asa` que haria falta: `_la_suite_no_puede_apagar_el_equipo` + la lista de frames validos. |
| **T-2** | El guard anti-apagón se puede desconectar en silencio (5 supervivientes EN SEGURIDAD) | G-1 (conjunto vigilado vacio), G-1b (`os.walk` roto), G-2 (regla del `taskkill /IM` sin dientes), G-8 (cuenta `>= 1`), G-9 (contraprueba trivializada). Arreglo en §6.2. |
| **T-3** | La celda (D1-ter)(d) y la asercion de 'entradas cubiertas' no las vigila nadie | `M-121-b` SOBREVIVIENTE (suite VERDE con la celda neutralizada, desplazamiento CERO). |
| **T-4** | La asercion del blindaje depende del numero de instancias que tenga el host | MEDIDO: 2 vivos (`lsass.exe` + `winlogon.exe`), no 3. `M-979b` SOBREVIVIENTE. Laproperty que hay que afirmar es por **PID**, no por numero. |
| **T-5** | La receta migrada de M-121 desplaza 11 lineas y no se puede re-medir | `M-121` NO MEDIDO: muere `test_las_citas_de_sandbox_rules_siguen_siendo_ciertas` (`run_tests.py:24785 ya no cita 'sandbox-rules.md:55-56'`). La variante `M-121-b` (12 → 12 lineas) si se midio. |
| **T-6** | Copiar el repo desde el VFS a `%TEMP%` pierde ficheros | `cam_r6` perdio ~180 ficheros entre las 20:07 y las 20:12, DESPUES de las mediciones. Afecto a un solo mutante (`M-979b`, primera receta de dos parches). MEDIDO que **no es la suite**: la camara final da 0 lineas de estado antes y despues de correr. Hay que **verificar la copia** (`git status` de la camara) antes de medir, y el arbol auditable es el **commit** de la camara, no su arbol de trabajo. |
| **T-7** | La fixture del tripwire del sha clava el reloj pero **no la identidad de git** | MEDIDO: con `GIT_AUTHOR_NAME=auditor` en el entorno, la suite muere con `el sha de la fixture (8b4d236b...) tiene que tener '0' en la 8.a cifra hexadecimal`. La fixture deberia clavar `GIT_AUTHOR_*`/`GIT_COMMITTER_*` igual que clava la fecha, o su comprobacion de entorno sera un fallo de entorno disfrazado de fallo de codigo. Ninguna corrida de esta ronda sufrio esto. |

**Con T-2 abierto (supervivientes en seguridad), el ciclo NO se cierra** (`SKILL.md`: un superviviente en seguridad o datos se arregla, no se documenta).

## 11. Bloque de maquina

### El bloque de maquina de la ronda 6 (estado en `0894e5c`)

El gate compara el CONJUNTO de lineas canonicas del informe con el del journal (`del_informe != del_journal` -> FAIL), luego en este fichero solo puede haber UN bloque canonico: el de la ronda vigente (abajo, seccion 8). El de la ronda 6 se conserva aqui como tabla y en el historial (`git show 0894e5c:openspec/changes/2026-10-23-el-gate-lee-la-mutacion/mutation-report.md`).

| Mutante | Estado en la ronda 6 | sha del arbol auditado |
|---|---|---|
| M-H1 | MUERTO | `0f654fc6c79236a95aea5746e84f25f6bedb2386` |
| M-H2 | MUERTO | `0f654fc6c79236a95aea5746e84f25f6bedb2386` |
| M-H3 | MUERTO | `0f654fc6c79236a95aea5746e84f25f6bedb2386` |
| M-H4 | MUERTO | `0f654fc6c79236a95aea5746e84f25f6bedb2386` |
| M-92 | MUERTO | `0f654fc6c79236a95aea5746e84f25f6bedb2386` |
| M-H6 | MUERTO | `0f654fc6c79236a95aea5746e84f25f6bedb2386` |
| M-H7 | MUERTO | `0f654fc6c79236a95aea5746e84f25f6bedb2386` |
| M-H8 | MUERTO | `0f654fc6c79236a95aea5746e84f25f6bedb2386` |
| M-H9 | MUERTO | `0f654fc6c79236a95aea5746e84f25f6bedb2386` |
| M-90 | MUERTO | `0f654fc6c79236a95aea5746e84f25f6bedb2386` |
| M-94 | MUERTO | `0f654fc6c79236a95aea5746e84f25f6bedb2386` |
| M-121-b | SOBREVIVIENTE | `0f654fc6c79236a95aea5746e84f25f6bedb2386` |
| M-979a | MUERTO | `0f654fc6c79236a95aea5746e84f25f6bedb2386` |
| M-979b | SOBREVIVIENTE | `0f654fc6c79236a95aea5746e84f25f6bedb2386` |


## 12. VERDICT

**FAIL.**

- **TASK-091 (el gate que lee la mutacion): PASS.** Las cuatro reglas (R1, R2, R3, R4) tienen dientes y mueren por su asercion; el gate no se puede desconectar en silencio (M-92, M-94), no acusa en lo que no puede (M-H6), el limite (g) esta vigilado (M-H7, M-H8) y la migracion de M-121 esta vigilada (M-H9). Los tres mutantes re-declarados del ciclo 71 (M-90, M-92, M-94) mueren tambien.
- **TASK-093 (el guard anti-apagón): FAIL.** Cinco supervivientes, todos en seguridad: el guard puede vigilar cero ficheros sin que nadie lo note, la cuarta via (`taskkill /IM`) no tiene dientes y su contraprueba se puede trivializar. El ciclo **no se cierra** con T-2 abierto.
- **Dos supervivientes mas, documentados:** `M-121-b` (la celda (D1-ter)(d) no la vigila nadie) y `M-979b` (la asercion por propiedad es indistinguible de la por instancias en un host con 2 procesos de sistema vivos).
- **Una tarea estructural (T-1):** el veredicto canonico no sabe expresar un guard que no es un `test_*`, y por eso 5 muertes comprobadas del guard quedan NO MEDIDO.

---

# Ronda 7 — Auditoría de mutación: el ARREGLO del guard anti-apagón (TASK-093) y la revalidación del gate que lee la mutación (TASK-091)

**Ciclo:** 72 · **Rama:** `beta` · **Auditor:** `mutation-auditor` (Sherlock)
**Árbol auditado:** `68b97718fb12636d5d9c7aa7f64f59df8e826d60` (344 ficheros; el commit de la cámara desechable)
**Base VERDE NATIVA:** `rc=0`, última línea `ALL TESTS PASSED.`, 315,8 s, y el guard anti-apagón con `55 fichero(s) .py vigilados por dos recorridos que coinciden, 0 vias de apagado y 0 de simulacion de entrada`.
**Encargo:** la ronda 6 (artefactos en `0894e5c`) dio **FAIL** en TASK-093: cinco mutantes del guard anti-apagón sobrevivieron (G-1, G-1b, G-2, G-8, G-9). El orquestador arregló el guard en `0894e5c` y toca **RE-MEDIR**. Nada de esto está cerrado hasta que se mide.

**VERDICT: FAIL (parcial).** Los **cinco** supervivientes de la ronda 6 están **cerrados y medidos MUERTOS**, y TASK-091 sigue en **PASS**. Pero esta ronda ha encontrado un **hueco NUEVO y más estrecho** en el arreglo: el meta-guard que el propio arreglo añadió **vigila la FORMA del texto de la contraprueba, no su semántica** (`G-10` y `G-11` sobreviven, §3.1). Con un superviviente en seguridad abierto, **el ciclo 72 NO se cierra**.

---

## 1. Qué se re-medió

| Fix | Commit | Qué promete |
|---|---|---|
| TASK-093 | `0894e5c` | El guard `_la_suite_no_puede_apagar_el_equipo()` **no se puede desconectar en silencio**: el conjunto vigilado se cuenta por DOS recorridos independientes (`os.walk` + `pathlib.rglob`) que tienen que COINCIDIR y no pueden ser cero; la contraprueba interna incluye el caso `taskkill /IM` y exige un **CONJUNTO de etiquetas** (cuatro vías); y un **meta-guard** lee el texto de la propia contraprueba (centinelas con `find`/`rfind`) y exige que siga diciendo lo que dice. |
| TASK-091 | `54c62a9`, `9798402` | El gate (check 11 de `validate_docs.py`) **lee la `mutacion` del catálogo**: R1 (forma), R2 (el fichero existe y está dentro del árbol), R3 (el `cambio`), R4 (el `ciclo`). Y el blindaje anti-brick se comprueba por la **PROPIEDAD**, no por el número de instancias. |

**Lo que NO se auditó** (y por qué): el recuento de tests (235 = 159 + 76) no se toca; el guard de TASK-093 **no es un `test_*`** (se invoca desde `__main__`, línea 33620), luego no cuenta como test ni como mutante canónico (§6).

## 2. Cómo se midió

- **Cámara desechable** en `%TEMP%\wopt_r7_20261024\cam`, con `git init` PROPIO. El `.git` del repo real es un **FICHERO** (57 bytes, gitlink a `%LOCALAPPDATA%`), y el árbol se puebla con `git archive` del GIT_DIR desacoplado, **sin copiar ficheros del VFS** (T-6: la copia desde Nextcloud pierde ficheros). MEDIDO: 344 ficheros declarados = 344 en disco, `git status --porcelain` vacío, `.git` de la cámara = **directorio** (no el fichero-gitlink) y la config de la cámara **no menciona** `woptimizer_git`.
- **Cada mutación se aplica con un parcheo EXACTO**: si el texto original no aparece el número exacto de veces, el script aborta y la corrida **no cuenta** (una mutación que no se aplica mide otra cosa). Las 29 recetas se ensayaron antes de correr: **todas aplican**.
- **`__pycache__` purgado entre mutaciones** (un `.pyc` obsoleto puede cambiar el veredicto).
- **El `rc` va ARRIBA del log**: la cola que se commitea como evidencia es la del último traceback; si el `rc` quedase al final sería su última línea y **taparía el motivo literal** de la aserción. El `stderr` de este host (el teardown de Tk: `invalid command name ...`) se coloca **delante** del `stdout` en VERDE y **detrás** en ROJO, para que la última línea útil sea la de éxito o la traza.
- **Base verde antes de mutar**: sin base, un verde de mutante no significa nada.
- **Carga del host**: las 29 corridas van **secuenciales**, con `stdin=DEVNULL`.
- **El entorno de medición es parte de la medición**: la fixture del tripwire del sha (`run_tests.py:25361`) **clava el reloj pero no la identidad de git** (T-7). En esta ronda **no se exportó ninguna variable `GIT_*`**: el `rc=0` de la base lo demuestra.
- **El repo real se movió DURANTE la medición** (el orquestador commiteó `2ab91d0`, el plan del ciclo 73). MEDIDO: `git diff --stat 0894e5c 2ab91d0` toca **solo dos ficheros de documentación** (`proposal.md` y `tasks.md` del cambio nuevo). El **código medido** es el del árbol auditado, y la cámara nunca tocó el repo real.

## 3. La tabla: los cinco supervivientes de la ronda 6, RE-MEDIDOS

| Mutante | Que rompe | Veredicto | Motivo literal medido |
|---|---|---|---|
| **G-1** | el conjunto de ficheros vigilados se vacia (`raiz` apunta a un arbol que no existe) | **MUERTO** | la suite se puso ROJO en el guard (fuera del veredicto canonico: no es un `test_*`); motivo literal: AssertionError: TASK-093: el guard NO ha vigilado ningun fichero: si el conjunto vigilado puede quedar vacio, el guard puede vigilar CERO ficheros sin que nada se entere (mutantes G-1 y G-1b). |
| **G-1b** | el `os.walk` se rompe (`for ... in ()`) | **MUERTO** | la suite se puso ROJO en el guard (fuera del veredicto canonico: no es un `test_*`); motivo literal: AssertionError: TASK-093: el guard NO ha vigilado ningun fichero: si el conjunto vigilado puede quedar vacio, el guard puede vigilar CERO ficheros sin que nada se entere (mutantes G-1 y G-1b). |
| **G-1b-func** | el recorrido se vacia SIN tocar el texto que vigila el meta-guard (la asercion `vistos > 0`, no la de forma) | **MUERTO** | la suite se puso ROJO en el guard (fuera del veredicto canonico: no es un `test_*`); motivo literal: AssertionError: TASK-093: el guard NO ha vigilado ningun fichero: si el conjunto vigilado puede quedar vacio, el guard puede vigilar CERO ficheros sin que nada se entere (mutantes G-1 y G-1b). |
| **G-2** | se borra la regla del `taskkill` POR NOMBRE (`/IM`) | **MUERTO** | la suite se puso ROJO en el guard (fuera del veredicto canonico: no es un `test_*`); motivo literal: AssertionError: TASK-093: el detector tiene que marcar las CUATRO vias de la contraprueba (el apagado por lanzador, la llamada directa a la API, la importacion de raton y el taskkill POR NOMBRE) y NO el taskkill por PID propio. Marcadas ['importacion_de_simulacion_de_entrada', 'lanzador_con_argumento_de_apagado', 'llamada_directa_a_la_api'] y esperadas ['importacion_de_simulacion_de_entrada', 'lanzador_con_argumento_de_apagado', 'llamada_directa_a_la_api', 'taskkill_por_nombre'] |
| **G-8** | la contraprueba deja de exigir el CONJUNTO de etiquetas (`etiquetas == ESPERADAS` -> `len >= 1`) | **MUERTO** | la suite se puso ROJO en el guard (fuera del veredicto canonico: no es un `test_*`); motivo literal: AssertionError: TASK-093: la CONTRAPROUEBA ya no dice 'etiquetas == ESPERADAS': alguien la ha trivializerizado (contar menos, o borrar el bucle de motivos) y la suite se quedaria en VERDE. Es lo que encontraron los mutantes G-8 y G-9. |
| **G-9** | la contraprueba se trivializa (cuenta `>= 1` **y** se borra el bucle de motivos) | **MUERTO** | la suite se puso ROJO en el guard (fuera del veredicto canonico: no es un `test_*`); motivo literal: AssertionError: TASK-093: la CONTRAPROUEBA ya no dice 'etiquetas == ESPERADAS': alguien la ha trivializerizado (contar menos, o borrar el bucle de motivos) y la suite se quedaria en VERDE. Es lo que encontraron los mutantes G-8 y G-9. |
| **G-9b** | SOLO se borra el bucle de motivos (aisla el segundo diente del meta-guard) | **MUERTO** | la suite se puso ROJO en el guard (fuera del veredicto canonico: no es un `test_*`); motivo literal: AssertionError: TASK-093: la CONTRAPROUEBA ya no dice '"un lanzador de procesos con el argumento"': alguien la ha trivializerizado (contar menos, o borrar el bucle de motivos) y la suite se quedaria en VERDE. Es lo que encontraron los mutantes G-8 y G-9. |
| **G-10** | la asercion del CONJUNTO de etiquetas se neutra (`or True`) y se conservan los literales | **SOBREVIVIENTE** | la suite termino en VERDE (rc=0, 'ALL TESTS PASSED.' como ultima linea) |
| **G-11** | la asercion del CONJUNTO se neutra Y el bucle de motivos deja de COMPROBAR (conservando sus literales) | **SOBREVIVIENTE** | la suite termino en VERDE (rc=0, 'ALL TESTS PASSED.' como ultima linea) |
| **G-3** | el detector deja de mirar los lanzadores de procesos | **MUERTO** | la suite se puso ROJO en el guard (fuera del veredicto canonico: no es un `test_*`); motivo literal: AssertionError: TASK-093: el detector tiene que marcar las CUATRO vias de la contraprueba (el apagado por lanzador, la llamada directa a la API, la importacion de raton y el taskkill POR NOMBRE) y NO el taskkill por PID propio. Marcadas ['importacion_de_simulacion_de_entrada', 'llamada_directa_a_la_api'] y esperadas ['importacion_de_simulacion_de_entrada', 'lanzador_con_argumento_de_apagado', 'llamada_directa_a_la_api', 'taskkill_por_nombre'] |
| **G-4** | el detector deja de mirar la llamada directa a la API de energia | **MUERTO** | la suite se puso ROJO en el guard (fuera del veredicto canonico: no es un `test_*`); motivo literal: AssertionError: TASK-093: el detector tiene que marcar las CUATRO vias de la contraprueba (el apagado por lanzador, la llamada directa a la API, la importacion de raton y el taskkill POR NOMBRE) y NO el taskkill por PID propio. Marcadas ['importacion_de_simulacion_de_entrada', 'lanzador_con_argumento_de_apagado', 'taskkill_por_nombre'] y esperadas ['importacion_de_simulacion_de_entrada', 'lanzador_con_argumento_de_apagado', 'llamada_directa_a_la_api', 'taskkill_por_nombre'] |
| **G-5** | el detector deja de mirar la importacion de simulacion de entrada | **MUERTO** | la suite se puso ROJO en el guard (fuera del veredicto canonico: no es un `test_*`); motivo literal: AssertionError: TASK-093: el detector tiene que marcar las CUATRO vias de la contraprueba (el apagado por lanzador, la llamada directa a la API, la importacion de raton y el taskkill POR NOMBRE) y NO el taskkill por PID propio. Marcadas ['lanzador_con_argumento_de_apagado', 'llamada_directa_a_la_api', 'taskkill_por_nombre'] y esperadas ['importacion_de_simulacion_de_entrada', 'lanzador_con_argumento_de_apagado', 'llamada_directa_a_la_api', 'taskkill_por_nombre'] |
| **G-6** | el detector marca tambien el taskkill por PID PROPIO (el caso legitimo) | **MUERTO** | la suite se puso ROJO en el guard (fuera del veredicto canonico: no es un `test_*`); motivo literal: AssertionError: TASK-093: el taskkill por PID PROPIO es legitimo (las utilidades matan SU propio hijo) y NO puede marcar, y el case '/IM' tiene que marcar UNA vez. Marcados 2: ['taskkill POR NOMBRE (/IM): matar al lsass o al winlogon APAGA el Windows', 'taskkill POR NOMBRE (/IM): matar al lsass o al winlogon APAGA el Windows'] |
| **G-7** | la auto-exclusion del guard se acorta (el `rfind` pasa a `find`) | **MUERTO** | la suite se puso ROJO en el guard (fuera del veredicto canonico: no es un `test_*`); motivo literal: AssertionError: TASK-093: hay una via de APAGADO o de SIMULACION DE ENTRADA en el repo. Infracciones: [('run_tests.py', 32892, 'lanzador_con_argumento_de_apagado', "un lanzador de procesos con el argumento 'shutdown'"), ('run_tests.py', 32892, 'taskkill_por_nombre', 'taskkill POR NOMBRE (/IM): matar al lsass o al winlogon APAGA el Windows'), ('run_tests.py', 32894, 'lanzador_con_argumento_de_apagado', "un lanzador de procesos con el argumento 'powercfg'"), ('run_tests.py', 32894, 'taskkill_por_nombre', 'taskkill POR NOMBRE (/IM): matar al lsass o al winlogon APAGA el Windows'), ('run_tests.py', 32898, 'taskkill_por_nombre', 'taskkill POR NOMBRE (/IM): matar al lsass o al winlogon APAGA el Windows'), ('run_tests.py', 32896, 'llamada_directa_a_la_api', 'una llamada directa a la API de energia')]. El equipo del dueno se ha apagado DOS veces con el motor de I+D corriendo de noche; ninguna via de esas puede quedarse aqui. |

### 3.1 El hallazgo NUEVO de esta ronda: el meta-guard vigila la FORMA del texto, no su SEMÁNTICA

El arreglo de la ronda 6 añadió un **meta-guard** que lee el texto de la propia contraprueba (delimitado por centinelas) y exige que siga diciendo lo que dice. **MEDIDO: eso vigila la PRESENCIA de los literales, no que las aserciones se EXECUTEN.** Dos recetas lo demuestran:

- **`G-10`** (una sola edición): `assert etiquetas == ESPERADAS, (` → `assert etiquetas == ESPERADAS or True, (`. Los literales siguen en el texto (el meta-guard no se entera) y la aserción del conjunto de etiquetas deja de comprobar. **La suite termina en VERDE** (`ALL TESTS PASSED.`). La consecuencia es **menor**: el bucle de motivaciones sigue exigiendo las cuatro motivaciones, luego las cuatro vías siguen vigiladas por el otro camino.
- **`G-11`** (dos ediciones coordinadas, conservando los literales): la aserción del conjunto se neutra **y** el bucle de motivos pasa a `pass` **conservando su tupla de literales**. El meta-guard ve los literales y no dice nada. **La suite termina en VERDE.** La consecuencia es **REAL**: las tres vías (lanzador, API de energía, simulación de entrada) podrían dejar de detectarse sin que la suite se entere; solo la cuarta (`taskkill /IM`) seguiría vigilada por el `assert len(marks_taskkill) == 1`, que `G-11` no toca.

**Lo que hay que arreglar** (no lo arreglo yo: es de `openspec-dev`): el meta-guard tiene que **fijar el texto EXACTO de las aserciones**, no fragmentos. Hoy exige `"assert etiquetas == ESPERADAS"`; si exigiera `"assert etiquetas == ESPERADAS, ("` (con la coma y el paréntesis) la receta de `G-10` no casaría, y exigir `"assert esperado in motivos, ("` cerraría la de `G-11`. La alternativa más fuerte (y la que este repo ya usa en el guard (B) del check 11) es un **meta-meta-guard**: que el propio guard compruebe que su texto, al que se le neutra la aserción, **deja de ser aceptado** por su propio meta-guard.

### 3.2 Lo que el arreglo SÍ ha cerrado (medido)

- **El guard ya no se puede desconectar en silencio**: `G-1` (el conjunto vigilado vacío) y `G-1b` (el `os.walk` roto) mueren por la aserción `vistos > 0`. Se midió además una **tercera variante** (`G-1b-func`) que rompe el recorrido **sin tocar el texto que vigila el meta-guard**: también muere por `vistos > 0`, luego elArrange no es solo de forma.
- **La cuarta vía (`taskkill /IM`) ya tiene dientes**: `G-2` (se borra la regla del `/IM`) muere por la aserción de las cuatro vías, que ahora es un **conjunto de etiquetas** y no un número.
- **La contraprueba ya no se puede trivializar borrando sus textos**: `G-8` (se exige `>= 1` en vez del conjunto) y `G-9` (se exige `>= 1` **y** se borra el bucle de motivos) mueren por el meta-guard; `G-9b` (solo se borra el bucle) muere por el **segundo** diente del meta-guard (los cuatro literales de motivaciones).
- **Los dientes del detector siguen vivos** (re-medidos en esta ronda, recetas reconstruidas): `G-3` (deja de mirar los lanzadores), `G-4` (deja de mirar la llamada directa a la API), `G-5` (deja de mirar la importación de simulación de entrada), `G-6` (marca el `taskkill` por PID propio, que es legítimo) y `G-7` (la auto-exclusión se acorta y el guard se acusa a sí mismo). Los cinco mueren con su motivo literal.

## 4. La tabla: los quince del catálogo, revalidados sobre el árbol nuevo

| Mutante | Que rompe | Veredicto | Motivo literal medido |
|---|---|---|---|
| **M-H1** | el gate NO comprueba R1 (la FORMA de la `mutacion`) | **MUERTO** | murio `test_el_check_9_se_cablea_en_el_camino_real_del_validador` por su asercion; motivo literal: EL GATE NO LEE LA MUTACION |
| **M-H2** | el gate NO comprueba R2 (que el fichero declarado EXISTA) | **MUERTO** | murio `test_el_check_9_se_cablea_en_el_camino_real_del_validador` por su asercion; motivo literal: EL GATE NO LEE LA MUTACION |
| **M-H3** | el gate NO comprueba R3 (el `cambio` del catalogo) | **MUERTO** | murio `test_el_check_9_se_cablea_en_el_camino_real_del_validador` por su asercion; motivo literal: EL GATE NO LEE LA MUTACION |
| **M-H4** | el gate NO comprueba R4 (el `ciclo` del catalogo) | **MUERTO** | murio `test_el_check_9_se_cablea_en_el_camino_real_del_validador` por su asercion; motivo literal: EL GATE NO LEE LA MUTACION |
| **M-92** | el gate mira SOLO el primer mutante del catalogo | **MUERTO** | murio `test_el_check_9_se_cablea_en_el_camino_real_del_validador` por su asercion; motivo literal: EL GATE NO DISTINGUE |
| **M-H6** | el gate ACUSA en lo que no puede | **MUERTO** | murio `test_el_check_9_se_cablea_en_el_camino_real_del_validador` por su asercion; motivo literal: EL GATE ACUSA EN LO QUE NO PUEDE |
| **M-H7** | el limite (g) se borra del bloque canonico del gate | **MUERTO** | murio `test_el_check_9_se_cablea_en_el_camino_real_del_validador` por su asercion; motivo literal: AssertionError: el limite (g) tiene que decir el COSTE MEDIDO de comprobar el texto declarado (62,3 ms): un limite sin motivo medido es una opinion |
| **M-H8** | el limite (g) deja de decir QUE es lo que no se comprueba | **MUERTO** | murio `test_el_check_9_se_cablea_en_el_camino_real_del_validador` por su asercion; motivo literal: AssertionError: el limite (g) tiene que decir QUE es lo que NO se comprueba: el TEXTO declarado, no la DECLARACION |
| **M-H9** | la migracion de M-121 (el catalogo real) se rompe | **MUERTO** | murio `test_el_check_9_se_cablea_en_el_camino_real_del_validador` por su asercion; motivo literal: AssertionError: el catalogo REAL del repo tiene que pasar el gate con 0 FAIL: acuso ["mutaciones.json: el mutante M-121 declara `mutacion.fichero` = 'src/woptimizer/NO_EXISTE.py' y ese fichero NO EXISTE en el arbol (o se sale de el). Una mutacion que apunta a un fichero que no existe NO es una mutacion: es la DECLARACION de una mutacion"]. O la migracion de un mutante real esta rota, o el gate es mas estricto que lo que el repo declara (y entonces el gate esta midiendo algo que nadie pidio) |
| **M-90** | el cuerpo del gate se vacia (solo queda el REGISTRO) | **MUERTO** | murio `test_el_check_9_se_cablea_en_el_camino_real_del_validador` por su asercion; motivo literal: EL GATE NO DISTINGUE |
| **M-94** | el gate se salta el PRIMER mutante del catalogo | **MUERTO** | murio `test_el_check_9_se_cablea_en_el_camino_real_del_validador` por su asercion; motivo literal: EL GATE NO DISTINGUE |
| **M-121-r6** | la celda (D1-ter)(d) y la asercion de 'entradas cubiertas' se neutralizan (receta migrada, 12 lineas -> 1) | **NO MEDIDO** | murio `test_las_citas_de_sandbox_rules_siguen_siendo_ciertas` y **NO** el `asa` declarada: motivo literal: AssertionError: run_tests.py:24785 ya no cita `sandbox-rules.md:55-56`: es una de las cuatro afirmaciones que atan la tabla al numero de linea |
| **M-121-b** | la MISMA receta migrada, con desplazamiento CERO (12 lineas -> 12) | **SOBREVIVIENTE** | la suite termino en VERDE (rc=0, 'ALL TESTS PASSED.' como ultima linea) |
| **M-979a** | el blindaje deja de CONTAR los procesos de sistema que omite (el `+=` quedo debajo del `continue`) | **MUERTO** | murio `test_no_system_process_is_killable` por su asercion; motivo literal: AssertionError: Todos los procesos de sistema vivos deberian contar como omitidos: s=0, vivos=2 |
| **M-979b** | el blindaje cuenta POR NOMBRE y no por instancia | **SOBREVIVIENTE** | la suite termino en VERDE (rc=0, 'ALL TESTS PASSED.' como ultima linea) |

### 4.1 El catálogo: qué se actualizó y por qué NO hay identificadores nuevos

- **Los 15 identificadores de la ronda 6 se CONSERVAN** (`M-H1`, `M-H2`, `M-H3`, `M-H4`, `M-92`, `M-H6`, `M-H7`, `M-H8`, `M-H9`, `M-90`, `M-94`, `M-121-r6`, `M-121-b`, `M-979a`, `M-979b`): el gate lleva **un único estado por identificador** y su historia está en git (`0894e5c`). Lo que cambia es su **estado**, su **sha del árbol auditado** y la **nota de esta ronda**.
- **NO se han añadido identificadores nuevos** al catálogo canónico, y la razón es **MEDIDA, no de estilo**: los mutantes nuevos de esta ronda (`G-1b-func`, `G-9b`, `G-10`, `G-11`, `G-3`..`G-7`) son **del guard**, y el gate **rechaza** un `asa` que no sea un `test_*` (§6). Declararlos en el catálogo haría que el **validador entero** fallara con *"NO es un test definido en run_tests.py"*. Quedan **fuera** del veredicto canónico, con su veredicto literal, su motivo literal medido y su evidencia en `evidencia/<mutante>-r7.cola` (la de la ronda 6 sigue viva en `evidencia/<mutante>.cola`).
- **`M-H9` sí ha cambiado de receta** (y se declara): el ancla de la ronda 6 (`"fichero": "run_tests.py"`) aparece **CUATRO** veces en el catálogo del ciclo 71, luego la receta se acota con el contexto de la entrada `M-121` (la que declara la migración que R2 tiene que vigilar). Se declara el ancla **real** que se aplicó.

## 5. Las tres deudas de medición

| Deuda | Mutante | Veredicto | Motivo literal medido | Qué falta |
|---|---|---|---|---|
| **T-3** | `M-121-b` | **SOBREVIVIENTE** | la suite termina en VERDE (`rc=0`, `ALL TESTS PASSED.`) con la celda (D1-ter)(d) y la aserción de `entradas cubiertas` neutralizadas (12 líneas → 12, **desplazamiento CERO**) | un meta-guard que compruebe que la celda EXISTE y que se USA (§5.1) |
| **T-4** | `M-979b` | **SOBREVIVIENTE** | la suite termina en VERDE (`rc=0`, `ALL TESTS PASSED.`): en este host el blindaje que cuenta por NOMBRE cuenta lo mismo que el que cuenta por INSTANCIA (2 vivos, 2 nombres distintos) | afirmar la propiedad **por PID**; la diferencia real está medida en aislamiento: 2 contra 1 (§5.3) |
| **T-5** | `M-121-r6` | **NO MEDIDO** | `AssertionError: run_tests.py:24785 ya no cita 'sandbox-rules.md:55-56': es una de las cuatro afirmaciones que atan la tabla al numero de linea` — murió `test_las_citas_de_sandbox_rules_siguen_siendo_ciertas` y **no** el `asa` declarada | la receta es **no medible** en el veredicto canónico (desplaza 11 líneas); la pregunta de fondo ya tiene respuesta medida: `M-121-b` SOBREVIVIENTE (§5.2) |

### 5.1 T-3 (`M-121-b`): la celda (D1-ter)(d) sigue sin dientes — **SOBREVIVIENTE, MEDIDO DE NUEVO**

La receta migrada de M-121 neutraliza la celda (D1-ter)(d) —la que exige que la entrada del journal **en el límite** (el ciclo 70, el origen del contrato) se re-derive— y la aserción de `entradas cubiertas`. Aplicada **sin desplazamiento** (12 líneas por 12), la suite queda **VERDE**: nadie vigila que esa celda se neutralice. Es la **misma** celda que el gate afirma vigilar en su propio corpus (`R2`), luego el hueco no es del gate: es de la suite que lo mira.

**Arreglo que necesita** (no lo arreglo yo): una celda (o un `test_*`) que compruebe que la celda (D1-ter)(d) **EXISTE** y que la aserción de `entradas cubiertas` **se usa**. Es el mismo patrón que ya usa el guard (B) con los límites (a)..(g) del gate.

### 5.2 T-5 (`M-121-r6`): la receta **no es medible** en el veredicto canónico, y la pregunta ya tiene respuesta

La receta **tal como está declarada** (12 líneas → 1) **desplaza 11 líneas**, y al desplazar mueve la cita viva `run_tests.py:24785`: la suite se pone ROJO, pero muere `test_las_citas_de_sandbox_rules_siguen_siendo_ciertas` y **no** el `asa` declarada → **NO MEDIDO**. Es un defecto **de la receta** (un hecho del mutante), no del código.

La pregunta de fondo ("¿tiene dientes la celda (D1-ter)(d)?") **ya tiene respuesta medida**: la variante de **desplazamiento CERO** (`M-121-b`) **sobrevive** (§5.1). O sea que la celda **no** tiene dientes, tanto si se desplaza como si no. Lo que queda abierto de T-5 es el **defecto de la receta**, que hay que arreglar en el catálogo (una receta que desplaza líneas no puede medir una celda), no en el código.

### 5.3 T-4 (`M-979b`): la diferencia ES real, y queda said su magnitud — MEDIDO en aislamiento

La ronda 6 dijo: "en este host hay 2 procesos de sistema vivos, no 3, luego la aserción por PROPIEDAD y la por INSTANCIAS **no se distinguen**". Eso es cierto **como aserción**, pero no dice si la diferencia es real o no. Esta ronda la ha medido **en aislamiento**, sin escribir un test que asuma un número fijo de instancias:

- **Sonda:** dos procesos SINTÉTICOS con el MISMO nombre (`lsass.exe`, PIDs 4242 y 4243), con `psutil.process_iter` parcheado en la cámara. El número de instancias lo pone la sonda, no el host.
- **Código REAL (cuenta por instancia):** `skipped = 2`.
- **MUTANTE `M-979b` (cuenta por NOMBRE):** `skipped = 1`.

**La diferencia es REAL y vale 1 omisión por cada nombre duplicado.** El hueco del test no es teórico: un blindaje que cuenta por nombre **deja de avisar** de un `lsass.exe` duplicado. Y en este host, MEDIDO: hay **2** procesos de sistema vivos (`lsass.exe` PID 1632 y `winlogon.exe` PID 1592) con **2 nombres DISTINTOS**, luego **aquí** el mutante cuenta lo mismo que el código real (2 = 2) y la aserción `s == len(vivos)` no lo distingue: por eso `M-979b` **sobrevive** en este host.

**Lo que hay que arreglar** (no lo arreglo yo: es de `openspec-dev`): el test debe afirmar la propiedad por **PID**, no por número de procesos: que el blindaje salte **cada** proceso de sistema vivo **por su PID** (contando PIDs omitidos, no nombres). Con eso, el hueco se cierra en cualquier host, incluido este.

**Y lo que NO hay que escribir** (regla del repo): un test que asuma "3 procesos de sistema" o "s == 2". En este host son 2, y en otro podrían ser 1 o 5: el número de instancias **no es un contrato**.

## 6. El guard anti-apagón: por qué sigue FUERA del veredicto canónico (T-1, declarado y NO arreglado)

El encargo de esta ronda dice que T-1 está **declarado y no lo arregles**: pero que lo midas y lo documente. MEDIDO:

- El gate (check 11 de `validate_docs.py`) exige que el `asa` declarada sea **un `test_*` DEFINIDO en `run_tests.py`**: `validate_docs.py:3521` (`if asa not in definidos:` → *"el asa declarada por {id} (`{asa}`) NO es un test definido en run_tests.py"*), y `definidos` sale de `_tests_definidos(root)`, que son **las funciones de módulo cuyo nombre empieza por `test_`**.
- El guard `_la_suite_no_puede_apagar_el_equipo()` **no** es un `test_*` **a propósito**: el recuento de tests es un contrato escrito a mano en cinco sitios (**235 = 159 + 76**) y el guard se invoca desde `__main__` (línea 33620), luego no cuenta como test.
- **CONSECUENCIA MEDIDA en esta ronda:** los mutantes del guard **no pueden entrar en el catálogo canónico**. Declararlos ahí (con `asa` = el nombre del guard) haría que el **validador entero** fallara. Por eso se miden **fuera** del veredicto canónico, con su veredicto literal y su motivo literal medido, y su evidencia vive en `evidencia/<mutante>-r7.cola`.
- **Y el hueco del contrato sigue abierto:** con el contrato actual, un guard **con dientes** no puede tener veredicto canónico (su muerte queda NO MEDIDO porque la cola no tiene el frame de un `test_*`), y un guard **sin dientes** tampoco puede declararse sin inventar el `asa`.

**T-1 (medido, no arreglado):** el veredicto canónico necesita una cuarta vía para los guards que no son tests (por ejemplo: que el `asa` pueda ser el nombre de un guard declarado, con su propia lista de frames válidos, como ya se hace con los `test_*`). En esta ronda: **14 mutantes del guard** con veredicto literal medido (5 de ellos los que la ronda 6 dejó sobrevivir) y **0** de ellos con veredicto canónico posible.

## 7. Qué queda encolado

| # | Qué queda | Métrica (medida, no opinada) |
|---|---|---|
| **T-1** | El veredicto canónico no puede expresar un guard que no es `test_*` | 14 mutantes del guard medidos **fuera** del veredicto canónico en esta ronda (5 de ellos los que la ronda 6 dejó sobrevivir), con su motivo literal. El gate lo impide: `validate_docs.py:3521` + `_tests_definidos` (solo `test_*` de módulo). **NO arreglado en esta ronda** (lo declara el encargo): es un hueco del CONTRATO, no del código. |
| **T-8 (NUEVA)** | El meta-guard del guard anti-apagón **vigila la FORMA del texto de la contraprueba, no su semántica**: comprueba que los literales estén, no que las aserciones se ejecuten | `G-10` **SOBREVIVIENTE** (una edición: `assert etiquetas == ESPERADAS or True`; consecuencia menor: el bucle de motivaciones sigue vigilando las cuatro vías) y `G-11` **SOBREVIVIENTE** (dos ediciones coordinadas que conservan los literales: la contraprueba entera se queda sin dientes y **tres de las cuatro vías podrían dejar de detectarse sin que la suite se entere**). Arreglo: fijar el texto EXACTO de las aserciones (`"assert etiquetas == ESPERADAS, ("`, `"assert esperado in motivos, ("`) o un meta-meta-guard. |
| **T-3** | La celda (D1-ter)(d) y la aserción de `entradas cubiertas` **no las vigila nadie** | `M-121-b` **SOBREVIVIENTE** (suite VERDE con la celda neutralizada y **desplazamiento CERO**), re-medido en esta ronda. El arreglo que necesita: un meta-guard como el (B) del gate, que compruebe que la celda EXISTE y que se USA. |
| **T-4** | El blindaje cuenta **POR NOMBRE**, no por instancia | `M-979b` **SOBREVIVIENTE**, re-medido. **Métrica nueva de esta ronda:** con dos instancias del MISMO nombre, el código real cuenta **2** y el mutante **1** (gap = **1 omisión por nombre duplicado**); en este host hay **2** vivos (`lsass.exe` PID 1632, `winlogon.exe` PID 1592) con **2 nombres distintos**, luego aquí son indistinguibles. Arreglo: afirmar la propiedad **por PID**. |
| **T-5** | La receta migrada de M-121 **desplaza 11 líneas** y no se puede re-medir en el veredicto canónico | `M-121-r6` **NO MEDIDO** (muere `test_las_citas_de_sandbox_rules_siguen_siendo_ciertas`, no el `asa` declarada) y `M-121-b` (desplazamiento CERO) **SOBREVIVIENTE**: o sea que la PREGUNTA de T-5 ("¿tiene dientes la celda?") **ya tiene respuesta: NO**. Lo que queda es el defecto de la receta, que es un hecho del mutante, no del código. |
| **T-6** | Copiar el repo desde el VFS a `%TEMP%` pierde ficheros | **ELUDIDA en esta ronda**: el árbol se pobló con `git archive` del GIT_DIR desacoplado (sin copiar ficheros). MEDIDO: 344 ficheros declarados = 344 en disco, `git status --porcelain` vacío. La deuda sigue viva para quien copie ficheros. |
| **T-7** | La fixture del tripwire del sha clava el reloj pero **no la identidad de git** | **ELUDIDA en esta ronda**: no se exportó ninguna variable `GIT_*` (la base sale `rc=0`). La deuda sigue viva: la fixture debería clavar `GIT_AUTHOR_*`/`GIT_COMMITTER_*` igual que clava la fecha. |

## 8. Bloque de máquina

<!-- WOPT_VEREDICTOS -->
WOPT_VEREDICTO M-H1 MUERTO 68b97718fb12636d5d9c7aa7f64f59df8e826d60
WOPT_VEREDICTO M-H2 MUERTO 68b97718fb12636d5d9c7aa7f64f59df8e826d60
WOPT_VEREDICTO M-H3 MUERTO 68b97718fb12636d5d9c7aa7f64f59df8e826d60
WOPT_VEREDICTO M-H4 MUERTO 68b97718fb12636d5d9c7aa7f64f59df8e826d60
WOPT_VEREDICTO M-92 MUERTO 68b97718fb12636d5d9c7aa7f64f59df8e826d60
WOPT_VEREDICTO M-H6 MUERTO 68b97718fb12636d5d9c7aa7f64f59df8e826d60
WOPT_VEREDICTO M-H7 MUERTO 68b97718fb12636d5d9c7aa7f64f59df8e826d60
WOPT_VEREDICTO M-H8 MUERTO 68b97718fb12636d5d9c7aa7f64f59df8e826d60
WOPT_VEREDICTO M-H9 MUERTO 68b97718fb12636d5d9c7aa7f64f59df8e826d60
WOPT_VEREDICTO M-90 MUERTO 68b97718fb12636d5d9c7aa7f64f59df8e826d60
WOPT_VEREDICTO M-94 MUERTO 68b97718fb12636d5d9c7aa7f64f59df8e826d60
WOPT_VEREDICTO M-121-r6 NO MEDIDO 68b97718fb12636d5d9c7aa7f64f59df8e826d60
WOPT_VEREDICTO M-121-b SOBREVIVIENTE 68b97718fb12636d5d9c7aa7f64f59df8e826d60
WOPT_VEREDICTO M-979a MUERTO 68b97718fb12636d5d9c7aa7f64f59df8e826d60
WOPT_VEREDICTO M-979b SOBREVIVIENTE 68b97718fb12636d5d9c7aa7f64f59df8e826d60
<!-- /WOPT_VEREDICTOS -->

## 9. VERDICT

**FAIL (parcial).**

- **TASK-091 (el gate que lee la mutación): PASS.** Revalidado sobre el árbol nuevo: las cuatro reglas (R1, R2, R3, R4) tienen dientes y mueren por su aserción; el gate no se puede desconectar en silencio (M-92, M-94), no acusa en lo que no puede (M-H6), el límite (g) está vigilado (M-H7, M-H8) y la migración de M-121 está vigilada (M-H9). Los tres mutantes re-declarados del ciclo 71 (M-90, M-92, M-94) mueren también. **12 MUERTO · 1 NO MEDIDO · 2 SOBREVIVIENTE** de 15.
- **TASK-093 (el guard anti-apagón): FAIL, pero por un motivo NUEVO y más estrecho.** Los **cinco** supervivientes de la ronda 6 (G-1, G-1b, G-2, G-8, G-9) están **cerrados y medidos MUERTOS**, con su motivo literal; y los cinco dientes del detector (G-3..G-7, re-medidos con recetas reconstruidas) siguen vivos. **PERO** esta ronda ha medido un **hueco nuevo**: el meta-guard que el propio arreglo añadió vigila la **forma** del texto de la contraprueba, no su **semántica** (`G-10` y `G-11` sobreviven: la suite termina en VERDE con la contraprueba neutralizada). Con `G-11`, **tres de las cuatro vías** (lanzador, API de energía, simulación de entrada) podrían dejar de detectarse sin que nada lo note. Es un superviviente **en seguridad**: **el ciclo 72 NO se cierra** hasta que se arregle.
- **Dos supervivientes más, documentados:** `M-121-b` (la celda (D1-ter)(d) no la vigila nadie) y `M-979b` (el blindaje cuenta por nombre; la diferencia es real y medida: 2 contra 1 con dos instancias del mismo nombre, pero en este host los dos vivos tienen nombres distintos).
- **Una tarea estructural (T-1):** el veredicto canónico no sabe expresar un guard que no es un `test_*`, y por eso las 14 muertes del guard quedan fuera del veredicto canónico.

**Qué hace falta para cerrar el ciclo 72** (en orden de gravedad):

1. **T-8 (seguridad):** que el meta-guard fije el texto **EXACTO** de las dos aserciones de la contraprueba (`"assert etiquetas == ESPERADAS, ("` y `"assert esperado in motivos, ("`), o un meta-meta-guard que compruebe que su propio texto, neutralizado, deja de ser aceptado. **Sin esto, el ciclo NO se cierra.**
2. **T-3 y T-4:** el meta-guard de la celda (D1-ter)(d) y la aserción del blindaje **por PID**.
3. **T-1 (estructural):** una cuarta vía en el contrato del veredicto canónico para los guards que no son tests.
