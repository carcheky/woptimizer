# Ronda 5 del `mutation-auditor` — el check 12 ya esta vigilado

> Que se audita: el commit `3752c5b` ("fix(validate): el check 12 queda cableado
> y con el recorte unico del repo (TASK-090)"), que responde al FAIL de la ronda
> 4 con la seccion **(E)** del guard
> `test_el_check_9_se_cablea_en_el_camino_real_del_validador` (`run_tests.py`)
> y con el recorte del check 12 convertido en el COMPARTIDO
> (`_sin_la_capa_que_el_bucle_no_lee`, por REGEX).
>
> Que se mide: **(A)** los ocho mutantes del check 12 (`mutaciones-check12.json`,
> C-1..C-7 y C-9), que en la ronda 4 SOBREVIVIERON todos; **(B)** el meta-mutante
> M-121; **(C)** los 24 mutantes del gate (`mutaciones.json`, M-90..M-112 y
> M-121), para comprobar que la ampliacion del corpus del guard NO los ha roto.
>
> Arbol auditado: `3752c5b`. Camara: `%TEMP%\wopt_r5\plantilla_r5`, copia con
> `shutil.copytree(..., ignore=shutil.ignore_patterns(".git", "__pycache__"))` y
> `git init` PROPIO. HEAD de la camara (el sha de todos los mutantes de esta
> ronda): `4d7643c7be79e2e52d25707e151699b81075367e`.

## 0. EL VEREDICTO DE ENTRADA

**El fix del dev FUNCIONA, y se ve en los dos niveles.**

En la ronda 4, los ocho mutantes del check 12 (C-1..C-7 y C-9) SOBREVIVIERON
a la suite completa: el check 12 no tenia NI UN `test_*` que lo vigilara. En esta
ronda, **los ocho MUEREN en la suite**, en el asa
`test_el_check_9_se_cablea_en_el_camino_real_del_validador`, en la seccion (E) que
el dev anadio, y cada uno muere **por la asercion que nombra la infraccion** (no
por un `ImportError`, ni por sintaxis rota, ni por otro test). En el PRODUCTO
(el validador real), siete de los ocho ahora ACUSAN; el octavo (C-7, el
cableado) sigue CALLANDO, y eso es justo lo que la seccion (E1) vigila.

Ademas, **los 23 mutantes del gate que mueren en la ronda 4 siguen muriendo**:
la ampliacion del corpus del guard no ha roto ninguno.

**PERO hay un hallazgo nuevo, de primera clase, y NO es un fallo del fix:** las
aserciones de la seccion (E) **no terminan en una linea marcador**, que es la
convencion que las de la seccion (D) si siguen (todas acaban en
`EL GATE NO DISTINGUE`). Consecuencia medida: para cinco de los ocho mutantes
del check 12 (C-1, C-2, C-3, C-4 y C-9) el veredicto CANONICO es **NO MEDIDO**,
no porque sobrevivan, sino porque la asercion que los mata (la de (E4)) acaba
con la cola del informe del validador, luego su ultima linea es la linea
`Resumen: ...` y el emisor — que mira la ULTIMA linea — no ve el motivo. El
detalle y el arreglo estan en la seccion 5.1.

## 1. LA BASE (sin mutar nada)

| | |
|---|---|
| Camara | `%TEMP%\wopt_r5\cam_r5_BASE_b` (plantilla + `git init` propio) |
| rc | **0** |
| Ultima linea no vacia | **`ALL TESTS PASSED.`** |
| Lineas | 401 |
| Duracion | 518.3 s |

Sin base verde no hay veredicto: la hay. Los dos `[FAIL]` que aparecen en el
log de la base NO son fallos de la suite: son PROSA de dos nombres de test
("... da [FAIL] con la ruta literal y rc 1 ...").

## 2. LOS 24 MUTANTES DEL GATE

Los 24 se RE-MEDIDEN en esta ronda (los que la ronda 4 habia medido, mas los que
esa ronda dejo sin tocar). Todos en camara propia, con `__pycache__` purgado
entre mutaciones, y con la comprobacion de que **ninguna mutacion mueve el
numero de lineas de `run_tests.py`** (el fichero se cita a si mismo por numero):
donde la mutacion declarada lo habria movido (M-98), se aplico la variante que
conserva las lineas y se dice en la tabla.

| id | que se rompe | veredicto | motivo LITERAL del fallo | dur |
|---|---|---|---|---|
| M-90 | el gate no imprime su REGISTRO de veredictos (y con `sin_ancla_de_git` se salta el check) | **MUERTO** | `EL GATE NO DISTINGUE` | 399.6 s |
| M-91 | el gate EXIGE que el estado derivado sea DISTINTO del declarado (acusa al mutante sano) | **MUERTO** | `EL GATE ACUSA EN LO QUE NO PUEDE` | 403.0 s |
| M-92 | el gate solo mira el PRIMER mutante del catalogo | **MUERTO** | `EL GATE NO DISTINGUE` | 402.9 s |
| M-93 | el gate CALCULA el veredicto pero no lo ACUSA (la diferencia se imprime y no se dice) | **MUERTO** | `EL GATE NO DISTINGUE` | 449.2 s |
| M-94 | el gate se salta el PRIMER mutante del catalogo | **MUERTO** | `EL GATE NO DISTINGUE` | 447.2 s |
| M-95 | el gate solo mira la PRIMERA entrada del journal | **MUERTO** | `EL GATE NO DISTINGUE` | 447.3 s |
| M-96 | el corpus sintetico NO se monta | **MUERTO** | `EL GATE NO DISTINGUE` | 444.3 s |
| M-97 | el centinela COHERENTE se declara "SOBREVIVIENTE" (el gate tiene que ACUSAR) | **MUERTO** | `EL GATE ACUSA EN LO QUE NO PUEDE` | 449.1 s |
| M-98 | D3 NO restaura el esqueleto: el validador se queda MUTADO y contamina las secciones siguientes | **MUERTO** | `copia mutada contaminaria las secciones que vienen despues` | 456.8 s |
| M-99 | el gate solo acusa cuando lo declarado es SOBREVIVIENTE | **MUERTO** | `EL GATE NO DISTINGUE` | 477.3 s |
| M-100 | el gate no comprueba el MOTIVO literal de la evidencia | **MUERTO** | `EL GATE NO DISTINGUE` | 476.7 s |
| M-101 | el journal NO aporta las lineas canonicas (`campo = None`) | **MUERTO** | `EL GATE NO DISTINGUE` | 473.6 s |
| M-102 | el gate no comprueba el SHA declarado contra el del catalogo | **MUERTO** | `EL GATE NO DISTINGUE` | 476.9 s |
| M-103 | el gate no comprueba que el `asa` declarado sea un test DEFINIDO | **MUERTO** | `EL GATE NO DISTINGUE` | 474.9 s |
| M-104 | el gate no comprueba que el test que murio sea el `asa` declarado | **MUERTO** | `EL GATE NO DISTINGUE` | 477.6 s |
| M-105 | el gate no compara el bloque de maquina del INFORME con el journal | **MUERTO** | `EL GATE NO DISTINGUE` | 452.1 s |
| M-106 | el gate no acusa los mutantes que el journal declara y el catalogo NO | **MUERTO** | `EL GATE NO DISTINGUE` | 453.7 s |
| M-107 | el EMISOR reescribe la evidencia de los mutantes que no se le han pasado | **MUERTO** | `el emisor NO puede reescribir la evidencia de un mutante que no se le ha pasado` | 445.4 s |
| M-108 | el gate no mira los mutantes que el catalogo declara y el journal NO lleva | **MUERTO** | `EL GATE NO DISTINGUE` | 471.9 s |
| M-109 | el gate deja SIN MIRAR la entrada del LIMITE (el ciclo 70, el origen del contrato) | **MUERTO** | `EL GATE NO DISTINGUE` | 451.9 s |
| M-110 | el gate no comprueba que la linea del INFORME coincida con el veredicto derivado | **MUERTO** | `EL GATE NO DISTINGUE` | 455.0 s |
| M-111 | el gate compara el sha por LONGITUD, no por valor | **MUERTO** | `EL GATE NO DISTINGUE` | 305.2 s |
| M-112 | el gate solo mira la diferencia del INFORME, no la del journal | **MUERTO** | `EL GATE NO DISTINGUE` | 306.3 s |
| M-121 | **meta**: la celda (D1-ter)(d) del LIMITE y la asercion de `entradas cubiertas` neutralizadas, y M-109 aplicado | **SOBREVIVIENTE** | `ALL TESTS PASSED.` | 729.4 s |

Los 23 mueren en el asa `test_el_check_9_se_cablea_en_el_camino_real_del_validador`
y por SU asercion: la ultima linea de la cola es el motivo declarado, en todos
los casos. **Ninguno de los 24 ha sobrevivido, y ninguno ha muerto por un
motivo ajeno al suyo.**

### 2.1 M-121: que demuestra, con el arbol nuevo

M-121 neutraliza las DOS celdas que cazan a M-109 (la (D1-ter)(d), que exige la
acusacion de la entrada del LIMITE, y la asercion de `entradas cubiertas`) y
aplica M-109 (`>=` -> `>` en el filtro de entradas del journal). La suite queda
**VERDE** (rc=0, 729.4 s, `ALL TESTS PASSED.` como ultima linea).

Su veredicto NO cambia respecto a la ronda 4: **SOBREVIVIENTE**, y eso es
precisamente lo que demuestra. Las dos celdas neutralizadas son lo UNICO que
caza a M-109: sin ellas, con M-109 aplicado, la entrada del ciclo 70 (el
LIMITE, el origen del contrato de veredictos) queda sin mirar y el gate se
queda mudo sin que nadie lo note. Y como la seccion (E) del commit `3752c5b` no
toca el gate (vigila el check 12), M-121 tampoco la activa.

**Lo que M-121 NO demuestra (y no se puede pedir que demuestre):** que el gate
vigile el check 12. Eso lo miden los ocho C-\*, y lo miden MUY BIEN.

## 3. LOS OCHO MUTANTES DEL CHECK 12

Cada uno se mide en DOS niveles, como en la ronda 4:

- **SUITE**: la suite completa en camara propia. Lo que importa aqui es si la
  seccion (E) lo mata y POR QUE asercion.
- **PRODUCTO**: el validador REAL (`python validate_docs.py`) corriendo sobre el
  arbol mutado, que es lo que el motor ejecuta de verdad.

| id | que se rompe | veredicto CANONICO | motivo LITERAL | SUITE: donde y por que | PRODUCTO |
|---|---|---|---|---|---|
| C-1 | la ORDEN desaparece del contenido que el motor lee | **NO MEDIDO** | el motivo declarado (`check 12 (paso de publicacion): la skill del motor NO manda publicar`) esta en la evidencia, pero NO en su ultima linea | **MUERTO** en (E4): `la skill REAL del motor manda publicar en `beta`, y el check 12 tiene que decirlo: el informe acusa a la skill de verdad. rc=1. Informe: [FAIL] check 12 (paso de publicacion): la skill del motor NO manda publicar. Faltan: orden ('publicas el ciclo en `beta`')` | **MUERTO**: `[FAIL] check 12 (paso de publicacion): la skill del motor NO manda publicar. Faltan: orden ('publicas el ciclo en `beta`')` |
| C-2 | la ORDEN se queda dentro de una VALLA real (fence de 3 lineas) | **NO MEDIDO** | idem | **MUERTO** en (E4), idem | **MUERTO**: `Faltan: orden ('publicas el ciclo en `beta`')` |
| C-3 | la ORDEN se queda dentro de un COMENTARIO HTML | **NO MEDIDO** | idem | **MUERTO** en (E4), idem | **MUERTO**: `Faltan: orden ('publicas el ciclo en `beta`')` |
| C-4 | el COMANDO (`git push origin beta`) desaparece | **NO MEDIDO** | idem | **MUERTO** en (E4), idem | **MUERTO**: `Faltan: comando ('git push origin beta')` |
| C-5 | el recorte deja de excluir las VALLAS | **MUERTO** | `el recorte la esta leyendo como contenido` | **MUERTO** en (E2): `una valla con prefijo de cita `> ` no es contenido que el motor lea (es la forma de la valla del propio SKILL.md): el recorte la esta leyendo como contenido, y por eso el check 12 daba un falso verde (C-9)` | **MUERTO**: `[FAIL] check 12 (paso de publicacion): el control de valla FALLA: ...` y `[FAIL] ... el control de valla con prefijo de cita FALLA: ...` |
| C-6 | el recorte deja de excluir los COMENTARIOS | **MUERTO** | `el recorte lo esta leyendo como contenido` | **MUERTO** en (E2): `un comentario HTML de VARIAS lineas no es contenido que el motor lea: el recorte lo esta leyendo como contenido, y el control del comentario (que era de UNA linea) no lo via (C-6)` | **MUERTO**: `[FAIL] check 12 (paso de publicacion): el control de comentario HTML FALLA: ...` (con un comentario de VARIAS lineas) |
| C-7 | el check 12 deja de estar CABLEADO (`validar()` no lo llama) | **MUERTO** | `un validador mudo pasa por verde` | **MUERTO** en (E1): `` `validar()` tiene que LLAMAR al check 12, y lo tiene que hacer de verdad: se han encontrado 0 llamadas a `_comprobar_el_paso_de_publicacion` en su cuerpo. Un check sin cablear no dice NADA: ni OK, ni FAIL, ni SKIP, y un validador mudo pasa por verde (C-7)`` | **SOBREVIVIENTE**: el validador CALLA (`163 OK, 2 FAIL` y ninguna linea del check 12). Un check mudo es un falso verde: por eso lo tiene que vigilar (E1) |
| C-9 | la ORDEN se queda dentro de la valla CON PREFIJO `> ` (la del propio SKILL.md) | **NO MEDIDO** | el motivo declarado esta en la evidencia, pero NO en su ultima linea | **MUERTO** en (E4), idem | **MUERTO**: `Faltan: orden ('publicas el ciclo en `beta`')` |

C-9 se ha medido con la mutacion **DECLARADA** en el catalogo (la ORDEN dentro
de la valla CON prefijo `> `), 243.7 s. Una primera pasada uso la variante sin
prefijo (misma familia de fallo, mismo veredicto en los dos niveles) y se
descarto: la que vale es la del catalogo.

### 3.1 Lo que cambio en el PRODUCTO (el numero que importa)

En el PRODUCTO, tres de los ocho pasaron de SOBREVIVIENTE a MUERTO con el
commit `3752c5b`: **C-5** (el control de la valla ahora dispara), **C-6** (el
control del comentario ahora es de VARIAS lineas) y **C-9** (el recorte
COMPARTIDO ve la valla con prefijo de cita como valla). Los cinco restantes ya
acusaban en la ronda 4, y C-7 sigue mudo en el producto (que es exactamente lo
que (E1) vigila).

## 4. SUPERVIVIENTES

**Ninguno.** De los 32 mutantes medidos en esta ronda, ninguno sobrevive a la
suite sin que sea por diseno:

- 31 mueren en su asa por su asercion (23 del gate + 8 del check 12 en la
  SUITE), y
- M-121 sobrevive **por diseno** (es el meta-mutante que neutraliza las dos
  celdas que cazan a M-109: su supervivencia ES la prueba de que esas dos
  celdas tienen dientes).

## 5. LOS NO MEDIDO (accionables, NO un FAIL)

| mutante | metrica | por que es NO MEDIDO | donde |
|---|---|---|---|
| C-1, C-2, C-3, C-4, C-9 | `asa` = `test_el_check_9_se_cablea_en_el_camino_real_del_validador`; `motivo` = `check 12 (paso de publicacion): la skill del motor NO manda publicar`; evidencia en `evidencia/C-*.cola` | la muerte SI esta y el motivo SI esta en la evidencia, pero la asercion que los mata (la de (E4)) **termina con la cola del informe del validador**, luego la ultima linea de la cola es `Resumen: 168 OK, 17 FAIL, 0 SKIP` y el emisor (que mira la ULTIMA linea) no ve el motivo | T-1 (MEDIA) |
| M-108 | `asa` = `test_el_check_9_se_cablea_en_el_camino_real_del_validador`; `motivo` = `EL GATE NO DISTINGUE`; evidencia en `evidencia/M-108.cola` | el emisor deriva NO MEDIDO de la cola que escribe (empieza en el ULTIMO traceback, y el mensaje de la asercion EMBARCA el traceback del validador, que revienta con `KeyError: 'M-FIX-SIN-LINEA'`); la evidencia commiteada se escribe con la cola completa, desde el traceback del TEST (ver 5.2), y con ella el GATE deriva MUERTO. El veredicto declarado es el del GATE, verificado contra su funcion | T-6 de la ronda 4, SIGUE ABIERTO |

### 5.1 T-1 (MEDIA) — las aserciones de (E) tienen que terminar en una linea marcador

**Que esta mal.** La seccion (D) del guard termina sus mensajes en
`\nEL GATE NO DISTINGUE`, y esa ultima linea es la que el emisor lee como "el
motivo literal" y la que el gate re-deriva. La seccion (E) que el dev anadio
**no sigue esa convencion**: cuatro de sus cinco aserciones terminan en prosa
(o en la cola de un informe). Consecuencia medida: el mutante que muere en la
asercion de (E4) tiene su motivo en la evidencia, pero no en su ultima linea,
y el veredicto canonico cae a NO MEDIDO.

**Lo que NO es.** No es que C-1..C-4 y C-9 sobrevivan: mueren, y el informe del
validador con su `[FAIL]` del check 12 esta en la evidencia commiteada. Es que
la cadena emisor -> gate no puede AFIRMAR su muerte sin mirar mas que la ultima
linea.

**El arreglo (una linea por asercion).** Que los mensajes de (E1), (E2), (E3) y
(E4) terminen en una linea marcador, igual que los de (D) y que el de (E5), que
ya lo hace (`EL CHECK 12 NO DISTINGUE`). Por ejemplo, en la asercion de (E4):
`f"rc={rc12}. Informe:\n{informe12[-2000:]}\nEL CHECK 12 NO DISTINGUE")`. Con
eso, los cinco pasan de NO MEDIDO a MUERTO sin tocar el producto.

**Metrica para el que lo arregle:** re-medir C-1, C-2, C-3, C-4 y C-9 en la
camara y exigir, para cada uno, que (a) la suite siga en ROJO, (b) el test que
muela sea `test_el_check_9_se_cablea_en_el_camino_real_del_validador`, (c) la
ultima linea de la cola contenga el motivo declarado, y (d) el veredicto
canonico pase a MUERTO. Si ademas el gate 11 acepta el mutante en
`mutaciones.json` (hoy los C-\* estan FUERA a proposito, porque el gate 11
compara el bloque de maquina con el journal), la cadena queda entera.

### 5.2 T-6 (MEDIA, de la ronda 4) — el emisor y el gate derivan distinto

Sin cambios: el mensaje de la asercion de M-108 EMBARCA el traceback del
validador (que revienta con `KeyError: 'M-FIX-SIN-LINEA'`), y el emisor corta
la cola en el ULTIMO traceback, luego pierde el frame del test; el gate, que
busca el frame en todo el bloque, lo ve.

**Como se ha resuelto en esta ronda (igual que en la ronda 4):** la evidencia
de M-108 se escribe con la cola VERBATIM del log crudo, desde el traceback del
TEST, y el veredicto lo decide la funcion del gate
(`validate_docs._estado_del_mutante`), verificada ANTES de escribir la linea.
El contenido de la evidencia no esta inventado (es el log crudo, sin tocar), lo
que cambia es DONDE empieza la cola, y por eso hay que decirlo: **la evidencia
de M-108 la escribe el auditor, no el emisor**, porque el emisor no puede
escribirla (corta en el traceback anidado). Las otras 31 las escribe el emisor.

Con ese recorte, el gate deriva `MUERTO` de la evidencia commiteada y la linea
canonica de M-108 dice `MUERTO`: **el veredicto de M-108 en esta ronda es
identico al de la ronda 4**, y el hallazgo sigue ABIERTO: mientras el emisor y
el gate no compartan la misma regla, cualquier mutante cuyo mensaje de
asercion embargue un traceback depende de quien mire.

## 6. VERDICT

**VERDICT: PASS** — ningun mutante sobrevive (31 de 32 mueren por su asercion
en su asa; el que sobrevive, M-121, sobrevive por diseno y su supervivencia es
la prueba de que dos celdas del gate tienen dientes), y los cinco NO MEDIDO no
son fallos del fix sino un defecto de la FORMA de los mensajes de la seccion (E),
que queda encolado como T-1 (MEDIA) con su metrica.

**Matiz que se declara con su nombre: PASS CON CINCO NO MEDIDO.** Los cinco
tocan el paso de publicacion del motor (que es lo que el check 12 vigila), y la
regla del `PARTIAL` dice que un NO MEDIDO de seguridad o datos impide cerrar el
ciclo. Mi lectura, y la dejo escrita para que el orquestador decida: el agujero
de DETECCION esta CERRADO y MEDIDO (los ocho C-\* mueren, con el motivo en la
evidencia commiteada); lo que queda abierto es la ATRIBUCION legible por el
emisor, que es un defecto de la cadena de auditoria, no del producto. Si el
orquestador aplica la regla del `PARTIAL` al pie de la letra, el ciclo NO se
cierra hasta que T-1 este hecho; si la aplica al fondo (que es lo que dice la
regla: "un mutante SIN MEDIR es un agujero con la etiqueta de 'medido'"), el
ciclo se cierra y T-1 queda en la cola.

## 7. BLOQUE DE MAQUINA

Las lineas canonicas de los mutantes del GATE. El orquestador las copia al
journal (campo `veredictos` de la entrada del ciclo) y a los DOS changelogs.
Los mutantes del CHECK 12 van FUERA de aqui a proposito: el gate 11 compara
este bloque con el journal, y un mutante que no esta en `mutaciones.json` lo
acusaria.

<!-- WOPT_VEREDICTOS -->
WOPT_VEREDICTO M-90 MUERTO 4d7643c7be79e2e52d25707e151699b81075367e
WOPT_VEREDICTO M-91 MUERTO 4d7643c7be79e2e52d25707e151699b81075367e
WOPT_VEREDICTO M-92 MUERTO 4d7643c7be79e2e52d25707e151699b81075367e
WOPT_VEREDICTO M-93 MUERTO 4d7643c7be79e2e52d25707e151699b81075367e
WOPT_VEREDICTO M-94 MUERTO 4d7643c7be79e2e52d25707e151699b81075367e
WOPT_VEREDICTO M-95 MUERTO 4d7643c7be79e2e52d25707e151699b81075367e
WOPT_VEREDICTO M-96 MUERTO 4d7643c7be79e2e52d25707e151699b81075367e
WOPT_VEREDICTO M-97 MUERTO 4d7643c7be79e2e52d25707e151699b81075367e
WOPT_VEREDICTO M-98 MUERTO 4d7643c7be79e2e52d25707e151699b81075367e
WOPT_VEREDICTO M-99 MUERTO 4d7643c7be79e2e52d25707e151699b81075367e
WOPT_VEREDICTO M-100 MUERTO 4d7643c7be79e2e52d25707e151699b81075367e
WOPT_VEREDICTO M-101 MUERTO 4d7643c7be79e2e52d25707e151699b81075367e
WOPT_VEREDICTO M-102 MUERTO 4d7643c7be79e2e52d25707e151699b81075367e
WOPT_VEREDICTO M-103 MUERTO 4d7643c7be79e2e52d25707e151699b81075367e
WOPT_VEREDICTO M-104 MUERTO 4d7643c7be79e2e52d25707e151699b81075367e
WOPT_VEREDICTO M-105 MUERTO 4d7643c7be79e2e52d25707e151699b81075367e
WOPT_VEREDICTO M-106 MUERTO 4d7643c7be79e2e52d25707e151699b81075367e
WOPT_VEREDICTO M-107 MUERTO 4d7643c7be79e2e52d25707e151699b81075367e
WOPT_VEREDICTO M-108 MUERTO 4d7643c7be79e2e52d25707e151699b81075367e
WOPT_VEREDICTO M-109 MUERTO 4d7643c7be79e2e52d25707e151699b81075367e
WOPT_VEREDICTO M-110 MUERTO 4d7643c7be79e2e52d25707e151699b81075367e
WOPT_VEREDICTO M-111 MUERTO 4d7643c7be79e2e52d25707e151699b81075367e
WOPT_VEREDICTO M-112 MUERTO 4d7643c7be79e2e52d25707e151699b81075367e
WOPT_VEREDICTO M-121 SOBREVIVIENTE 4d7643c7be79e2e52d25707e151699b81075367e
<!-- /WOPT_VEREDICTOS -->

**Nota sobre M-108.** Su asercion EMBARCA el traceback del validador (que
revienta con `KeyError: 'M-FIX-SIN-LINEA'`), luego la cola que escribe el
emisor (desde el ULTIMO traceback) no tiene el frame del test y el emisor
imprime `NO MEDIDO`. La linea de arriba es la que deriva el GATE de la MISMA
evidencia commiteada (la cola completa, desde el traceback del test), y se ha
verificado contra `validate_docs._estado_del_mutante` antes de escribirla. Es
el hallazgo T-6 de la ronda 4, que sigue abierto; ver 5.2.

## 8. QUE SE ESCRIBIO EN EL REPO (y nada mas)

- `openspec/changes/2026-10-22-el-gate-distingue-o-falla/mutaciones.json`: los
  24 mutantes del gate con el `sha_arbol_auditado` de esta ronda
  (`4d7643c7be79e2e52d25707e151699b81075367e`, el HEAD de la camara donde se
  midieron) y la nota de la ronda 5.
- `openspec/changes/2026-10-22-el-gate-distingue-o-falla/mutaciones-check12.json`:
  los 8 mutantes del check 12 con su `sha` de esta ronda, su `asa` REAL (la
  seccion (E) vive dentro del guard
  `test_el_check_9_se_cablea_en_el_camino_real_del_validador`), la mutacion
  REFORMULADA de C-5 y C-6 (su `original` ya no existe: el recorte PROPIO por
  LINEAS fue sustituido por el COMPARTIDO por REGEX) y los dos motivos
  (`motivo`, el de la SUITE, que el emisor re-deriva; `motivo_producto`, el que
  declaro la ronda 4, el que dice el PRODUCTO).
- `openspec/changes/2026-10-22-el-gate-distingue-o-falla/evidencia/*.cola`: la
  cola de cada mutante medido. **31 de las 32 las escribe
  `.taskmaster/veredicto.py`**; la de M-108 la escribe el auditor con la cola
  verbatim del log crudo (ver 5.2: el emisor corta en el traceback anidado y
  perderia el frame del test), en el mismo formato que la ronda 4.
- `openspec/changes/2026-10-22-el-gate-distingue-o-falla/mutation-report.md`:
  este informe (la ronda 4 queda intacta en `mutation-report-ronda-4.md`).

**COMPROBACION FINAL (hecha antes de escribir esto):** las 24 lineas del bloque
de maquina se re-derivan, con la funcion DEL GATE
(`validate_docs._estado_del_mutante`), de la evidencia commiteada: las 24
coinciden, `FALLOS: 0`. Los ocho C-\* (fuera del bloque a proposito) derivan
`MUERTO` (C-5, C-6, C-7) y `NO MEDIDO` (C-1, C-2, C-3, C-4, C-9).

NO se ha escrito: `rd_journal.json`, los dos changelogs, `run_tests.py`,
`validate_docs.py`, `STATUS.md` ni ningun commit. (Los cinco primeros los
escribio el orquestador en paralelo durante la sesion; ver 9.)

## 9. NO CONTAMINACION DEL REPO REAL

El `.git` de este repo es un FICHERO de 57 bytes (`gitdir: ...`), luego la
copia se hizo con `shutil.copytree(..., ignore=shutil.ignore_patterns(".git",
"__pycache__"))` (que excluye ficheros y directorios) y cada camara tiene su
propio `git init`. MEDIDO, al terminar:

- `git rev-parse --git-dir` desde la camara: `.git` (la suya), nunca
  `%LOCALAPPDATA%\woptimizer_git\.git`.
- `git log --oneline -1` del repo real: `3752c5b fix(validate): el check 12
  queda cableado y con el recorte unico del repo (TASK-090)` — **sin commits
  nuevos, el HEAD no se ha movido**.
- `git rev-parse --git-dir` desde la raiz del repo real:
  `C:\Users\carch\AppData\Local\woptimizer_git\.git` — el de siempre, no el de
  ninguna camara.
- `git status --porcelain` del repo real: 35 modificado + 1 sin seguimiento, y
  **TODOS** son los entregables de este encargo (los 32 `evidencia/*.cola`, los
  dos catalogos, `mutation-report.md` y `mutation-report-ronda-4.md`). Ningun
  fichero fuera de ese conjunto: 0.
- `git diff --cached --stat`: **vacio** — no hay nada stageado.
- `git diff --stat`: solo los mismos 35 ficheros de los entregables.

**Lo que SI aparece en `git status` y NO es mio (declarado, no escondido):**
`.taskmaster/rd_journal.json`, `.taskmaster/CHANGELOG.md`,
`.taskmaster/tasks.json`, `CHANGELOG.md` y `STATUS.md` estan modificados, y los
escribio **el orquestador en paralelo** durante esta sesion (a las 20:31:42
llego la entrada del ciclo 71 al journal, con MIS 24 lineas canonicas ya
copiadas, y con el changelog de los dos ficheros). Yo no he escrito ninguno de
esos cinco ficheros: mi aparejo solo lee el journal y los changelogs.

**La prueba final, con el validador real sobre el repo real:**
`python validate_docs.py` -> `Resumen: 165 OK, 0 FAIL, 0 SKIP`, rc=0, y el
check 11 dice `28 linea(s) canonica(s) de los changelogs comprobadas contra la
evidencia commiteada` (26 mutantes re-derivados). Es decir: el gate ha
re-derivado los veredictos desde la evidencia que he commiteado y estan de
acuerdo con las lineas del bloque de maquina.

Y la PRUEBA de que la camara no toco el repo: el `HEAD` de la camara es
`4d7643c` ("arbol base auditado (camara mutation-auditor ronda 5)"), un commit
que solo existe en `%TEMP%`, y el repo real no lo conoce.

## 10. UNA NOTA SOBRE EL APAREJO (medido, por si vuelve a pasar)

La primera tanda de ocho camaras SE CUELGO: los logs se quedaban en 0 bytes y
aparecian procesos `git cat-file --batch-check` y `git log --format=%s --all`
PARADOS. La causa NO era el repo ni la carga: el runner heredaba el STDIN del
shell (un pipe que nunca se cierra) y `git cat-file --batch-check` **lee de
stdin**, luego se queda esperando para siempre. En CI el stdin es `/dev/null`;
aqui tambien tiene que serlo (`stdin=subprocess.DEVNULL` en el aparejo). Con
eso, 32 mutantes en seis tandas de seis, sin un solo cuelgue.

Tambien: `Get-ChildItem` puede mostrar `0` bytes para un log que se esta
escribiendo (la entrada de directorio del NTFS va con retraso). Para leer el
tamaño real, `[System.IO.FileInfo]::new($ruta).Length` o abrirlo en modo
lectura: el log de C-1 tenia 16 455 bytes cuando PowerShell decia 0.
