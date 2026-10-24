# Ronda 6 — Auditoría de mutación: el gate que lee la mutación (TASK-091) y el guard anti-apagón (TASK-093)

**Ciclo:** 72 · **Rama:** `beta` · **Auditor:** `mutation-auditor` (Sherlock)
**Árbol auditado:** `0f654fc6c79236a95aea5746e84f25f6bedb2386` (311 ficheros; el commit de la cámara desechable)
**Base VERDE NATIVA:** `rc=0`, última línea `ALL TESTS PASSED.`, 365,5 s, y el guard anti-apagón con `55 fichero(s) .py vigilados, 0 vias de apagado y 0 de simulacion de entrada`.
**VERDICT: FAIL** — el fix de TASK-091 está sólido (12 MUERTO, 1 NO MEDIDO y 2 SOBREVIVIENTE de 15 mutantes canonicos), **pero el guard nuevo de TASK-093 se puede desconectar en silencio** (5 supervivientes EN SEGURIDAD, medidos fuera del veredicto canonico) y el veredicto canonico no es capaz de expresar su muerte.

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

<!-- WOPT_VEREDICTOS -->
WOPT_VEREDICTO M-H1 MUERTO 0f654fc6c79236a95aea5746e84f25f6bedb2386
WOPT_VEREDICTO M-H2 MUERTO 0f654fc6c79236a95aea5746e84f25f6bedb2386
WOPT_VEREDICTO M-H3 MUERTO 0f654fc6c79236a95aea5746e84f25f6bedb2386
WOPT_VEREDICTO M-H4 MUERTO 0f654fc6c79236a95aea5746e84f25f6bedb2386
WOPT_VEREDICTO M-92 MUERTO 0f654fc6c79236a95aea5746e84f25f6bedb2386
WOPT_VEREDICTO M-H6 MUERTO 0f654fc6c79236a95aea5746e84f25f6bedb2386
WOPT_VEREDICTO M-H7 MUERTO 0f654fc6c79236a95aea5746e84f25f6bedb2386
WOPT_VEREDICTO M-H8 MUERTO 0f654fc6c79236a95aea5746e84f25f6bedb2386
WOPT_VEREDICTO M-H9 MUERTO 0f654fc6c79236a95aea5746e84f25f6bedb2386
WOPT_VEREDICTO M-90 MUERTO 0f654fc6c79236a95aea5746e84f25f6bedb2386
WOPT_VEREDICTO M-94 MUERTO 0f654fc6c79236a95aea5746e84f25f6bedb2386
WOPT_VEREDICTO M-121-r6 NO MEDIDO 0f654fc6c79236a95aea5746e84f25f6bedb2386
WOPT_VEREDICTO M-121-b SOBREVIVIENTE 0f654fc6c79236a95aea5746e84f25f6bedb2386
WOPT_VEREDICTO M-979a MUERTO 0f654fc6c79236a95aea5746e84f25f6bedb2386
WOPT_VEREDICTO M-979b SOBREVIVIENTE 0f654fc6c79236a95aea5746e84f25f6bedb2386
<!-- /WOPT_VEREDICTOS -->

## 12. VERDICT

**FAIL.**

- **TASK-091 (el gate que lee la mutacion): PASS.** Las cuatro reglas (R1, R2, R3, R4) tienen dientes y mueren por su asercion; el gate no se puede desconectar en silencio (M-92, M-94), no acusa en lo que no puede (M-H6), el limite (g) esta vigilado (M-H7, M-H8) y la migracion de M-121 esta vigilada (M-H9). Los tres mutantes re-declarados del ciclo 71 (M-90, M-92, M-94) mueren tambien.
- **TASK-093 (el guard anti-apagón): FAIL.** Cinco supervivientes, todos en seguridad: el guard puede vigilar cero ficheros sin que nadie lo note, la cuarta via (`taskkill /IM`) no tiene dientes y su contraprueba se puede trivializar. El ciclo **no se cierra** con T-2 abierto.
- **Dos supervivientes mas, documentados:** `M-121-b` (la celda (D1-ter)(d) no la vigila nadie) y `M-979b` (la asercion por propiedad es indistinguible de la por instancias en un host con 2 procesos de sistema vivos).
- **Una tarea estructural (T-1):** el veredicto canonico no sabe expresar un guard que no es un `test_*`, y por eso 5 muertes comprobadas del guard quedan NO MEDIDO.
