# TASK-074 · Informe del `mutation-auditor` (ciclo 63)

> Medición sobre copia en `%TEMP%`; el repo real solo se lee. Wrapper real medido
> por subproceso desde `REPO_ROOT`. HEAD anclado esperado `3e155f5`.
> Escrito incrementalmente: cada sección está medida antes de escribirse.

## 0. Aislamiento de la cámara (por qué esta copia no puede tocar el repo real)

| Comprobación | Medido |
|---|---|
| `.git` del repo real | **FICHERO** de 57 bytes: `gitdir: C:/Users/carch/AppData/Local/woptimizer_git/.git` |
| `.git` en la copia de `%TEMP%` | excluido como **fichero** con `shutil.ignore_patterns(".git")`, no con `robocopy /XD` |
| Repo git de la cámara | `git init` **nuevo**, dentro de la cámara, con su propio commit: no es el repo real ni una copia del puntero |
| `GIT_DIR` del shell | vacío al empezar y al terminar: nunca se honra `%LOCALAPPDATA%\woptimizer_git\.git` |
| Digest del wrapper real | `f47500769381` antes y después de M1: **CUADRA** (no se mutó el original) |

## 1. M1 · la matriz de 8 celdas, medida por subproceso (no leída)

Invocando `python .taskmaster/git_safe_commit.py` con cada combinación y leyendo
su `returncode` y su stdout. `GIT_DIR` sano = un `git init` + un commit en
`%TEMP%`; `GIT_DIR` malo = ruta inexistente; par roto = `GIT_DIR` sin
`GIT_WORK_TREE`. Cero escrituras en el repo real (el par apunta a la cámara).

| modo | paridad | repo | rc medido | línea canónica (última `WOPT_*`) | matriz del arquitecto (`proposal.md` §2.3, columna «reordenado») | ¿Cuadra? |
|---|---|---|---|---|---|---|
| commit | rota | verificable | `2` | `WOPT_USAGE paridad-git …` | `2` | sí |
| commit | rota | **no verificable** | `2` | `WOPT_USAGE paridad-git …` | `2` | sí |
| commit | entera | verificable | `0` | `WOPT_NOOP arbol limpio (status --porcelain vacio)` | `0` | sí |
| commit | entera | no verificable | `3` | `WOPT_REPO_INVALIDO GIT_DIR no existe o no es un directorio: …` | `3` | sí |
| `--verify` | rota | verificable | `2` | `WOPT_USAGE paridad-git …` | `2` | sí |
| `--verify` | rota | **no verificable** | **`2`** | `WOPT_USAGE paridad-git …` | **`2`** (antes `3`) | **sí: es la celda que cambió** |
| `--verify` | entera | verificable | `0` | `WOPT_REPO_OK <git_dir>` | `0` | sí |
| `--verify` | entera | no verificable | `3` | `WOPT_REPO_INVALIDO …` | `3` | sí |

**La celda clave cuadra**: `--verify` + par roto + repo no verificable da
`2 WOPT_USAGE paridad-git`, no `3`. Las otras siete no se han movido respecto al
orden viejo, también medido: el contrato público resultante es **una sola celda
cambiada de ocho**, tal como declara `proposal.md` §2.3 y §3.1.

Las dos celdas del par roto emiten **una sola** línea `WOPT_*` (stdout crudo
pegado en el log `m1_matriz.log`), luego «el 2 no menciona el repo» no es una
promesa del doc: es lo que sale.

## 2. M6 · los dos bugs que el dev encontró en su propia sonda (confirmados)

### M6b · «la línea canónica es la última» era FALSO en el camino de commit

**Medido**, celda `commit` + par **entero** + repo **no verificable**, stdout
completo línea a línea:

```
rc = 3
 1| INFO ancla-arbol: sin declaracion: el repositorio no dice que arbol es, ...
 2| WOPT_REPO_INVALIDO GIT_DIR no existe o no es un directorio: ...\no_existe
 3| INFO no se intenta el .git del arbol de trabajo: fallback prohibido.
```

La última línea no vacía es un `INFO`, **después** de la canónica. El comentario
de la sonda nueva (`run_tests.py:20065-20070`) es, por tanto, cierto y el arreglo
—exigir que la última línea **`WOPT_*`** sea la del código esperado— es correcto.

**¿Y no oculta el caso de commit? NO, y está medido por qué:** en esa celda la
sonda sigue exigiendo `rc == 3` y que la última `WOPT_*` sea `WOPT_REPO_INVALIDO`
(celda 4 de la tabla de la sonda). Lo que cambia es el **criterio de «última»**,
de «última línea no vacía» a «última línea canónica», que es el que el pipeline
real lee. Exigir la última-no-vacía habría hecho fallar la celda buena por un
`INFO` que no contradice nada.

## 3. M7 · las afirmaciones documentales del ciclo, derivadas con `ast`

| Afirmación | Medido | Veredicto |
|---|---|---|
| `docs/ai/sandbox-rules.md:55-56` sigue siendo la fila `0` que **TABULA** el contrato | Leídas **por número de línea**: 55 = la fila `0` de `WOPT_COMMIT_OK`, 56 = la fila `0` de `WOPT_NOOP` | **CUADRA**: las dos citas de `validate_docs.py:1278` y `:1773` siguen apuntando a las dos filas del `0` sobrecargado, que es lo que usan para distinguir TABULAR de DECLARAR |
| El documento dice la **precedencia**, no solo los códigos sueltos | Fila `2` (`:59`): «`WOPT_USAGE paridad-git` **PRECEDE** a `WOPT_REPO_INVALIDO` aunque el repositorio tampoco se pueda comprobar (TASK-074)». Fila `3` (`:60`): «no verificable **con el par entero**». Regla 7 (`:85`): «Ese `2` **no se condiciona al repositorio**: precede al `3`» | **CUADRA**, y coincide con las 8 celdas de M1 |
| El párrafo de `--verify` refleja lo medido | `:237-251`, tabla Antes/Ahora con fecha 2026-10-18: repo no verificable `3` → **`2 WOPT_USAGE paridad-git`**; repo verificable `2` → `2` | **CUADRA** celda a celda con M1 |
| El recuento de tests, derivado y no escrito a mano | `validate_docs._reparto_de_tests(raiz)` → `(142, 65, 207, marcador en run_tests.py:26607)`; `207 = 142 + 65`; y `ast` cuenta **207** `def test_*` a nivel de módulo | **CUADRA**: el spec pedía 208 y son 207 de verdad; el dev escribió el número real |
| Los sitios que declaran el número están **atados** al derivado | `python validate_docs.py` → **145 OK, 0 FAIL**, y entre ellos: `run_tests.py: 207 tests definidos = 207 invocados (derivado con ast)`, `STATUS.md/AGENTS.md/README.md declaran los 207`, `docs/ai/testing-guide.md: 207 filas de test, una por test definido`, y `reparto 142 backend + 65 headless derivado con ast` | **CUADRA**: no son cifras a mano sueltas, el validador las deriva con `ast` y compara |

## 4. M8 · la deuda que el dev declaró y no tocó: calibrada

**Medido** en el apartado M6b: el camino de commit imprime su `INFO` **después**
de la línea canónica `WOPT_REPO_INVALIDO`.

**¿Lo admite el documento? NO.** Busqué en `docs/ai/sandbox-rules.md` cualquier
admisión (`no se intenta el .git`, `después de su WOPT`, `canónica … última`):
**cero coincidencias**. Y la regla 4 (`:70`) sigue escrita sin matices:

> **La línea `WOPT_*` va a stdout y es la última que se imprime.**

**Calibración: `baja`, no `alta`.** No es el contrato roto: es el documento más
estricto que el código. Medido también el otro lado —qué exige realmente la suite
—: las sondas de «`WOPT_*` es la ULTIMA» (`run_tests.py:17287`, `:17527`,
`:18098`, `:18248`, `:19341`, `:19931`) comprueban celdas cuyo camino **sí** deja la
canónica al final, y la nueva sonda `..._en_los_dos_modos` exige la última
**`WOPT_*`**, no la última línea. Ninguna probe exige la regla 4 al pie de la letra
sobre la celda `commit + not ok`, porque esa celda **no** la cumple y nadie la
comprueba. El riesgo es de un consumidor futuro que parsee «la última línea», y
la mitigación correcta es una frase en el documento, no un test.

## 5. M2 · los dos mutantes de la puerta de paridad

**Arnés.** Las sondas se ejercitan importando `run_tests.py` de la cámara (sin
ejecutar `__main__`) y llamando a cada sonda por su nombre. Contrato de veredicto
idéntico al de la suite: el log termina en `ALL TESTS PASSED.` (superviviente) o
en el traceback de la aserción (muerto). Subconjunto de 10 sondas: las 7 del
ciclo (`fail_safe`, `cero_sobrecargado`, `..._en_los_dos_modos` (nueva),
`..._por_estructura` (nueva), `..._va_despues_de_validar_repo` (reescrita),
`..._tambien_cubre_el_modo_verify`, `puerta_del_mensaje`) más las tres que
vigilan la puerta del mensaje de TASK-059. **CONTROL sin mutar: 10/10 verdes, log
en `ALL TESTS PASSED.`** — sin ese control, un rojo de cámara se lee como muerte
de mutante.

**Antes de cada mutante** el wrapper de la cámara se restaura desde el **wrapper
del repo real** y se comprueba su digest (`f47500769381`), de modo que el punto
de partida es siempre el código real y no el del mutante anterior. Después de
mutar se **relee del disco** y se exige el texto mutado (mi primer arnés no
restauraba nada: por eso `R4-n` hubo que repetirlo, y queda dicho).

| id | qué rompí | veredicto | quién lo mata y por qué |
|---|---|---|---|
| `R4-k` | `if paridad_rota:` → `if paridad_rota and ok:` (línea 891) | **killed** | `..._en_los_dos_modos` (celda `commit + par roto + repo roto`: sale `3`, esperaba `2`), `..._va_despues_de_validar_repo` (sujeto) y `..._por_estructura` (ya no encuentra el `if`) |
| `R4-n` | `if paridad_rota:` → `if paridad_rota and not verify:` | **killed** | `..._en_los_dos_modos`, `..._va_despues_de_validar_repo`, `..._tambien_cubre_el_modo_verify` y `..._por_estructura` |

**Mueren por la aserción que nombra la celda, no por un accidente.** Motivo
literal del log de `R4-n` (última sonda que muere):

> `AssertionError: `--verify` con el par ASIMETRICO tiene que salir con 2 (WOPT_USAGE paridad-git) y salio con 0. Con el mu…`

que es exactamente el `0 WOPT_REPO_OK` que el docstring de esa sonda promete. Y
el de `R4-k`:

> `AssertionError: con un par ASIMETRICO y un repo NO verificable tiene que ganar el 2 (pon las dos variables) y salio con 3…`

Los dos mueren **en las sondas que el encargo nombra**, y no solo ahí: cada uno
muere en más de una, que es lo que hace que la redundancia sea real.

## 6. M3 · `M5'`: la afirmación «es EQUIVALENTE» del dev, verificada

**Medido, no leído.** `M5'` = la puerta de paridad movida **por encima** de
`ok, fallo_repo, git_dir = validar_repo(env)`, dejando el resto igual (digest
cambia, el texto mutado verificado en disco).

| sonda | `M5'` puesto |
|---|---|
| `test_git_safe_commit_fail_safe` | **vive** |
| `test_el_cero_esta_sobrecargado_por_dos_desenlaces_y_solo_por_esos_dos` | **vive** |
| `test_la_paridad_gana_al_repo_invalido_en_los_dos_modos` | **vive** |
| `test_la_puerta_de_paridad_va_despues_de_validar_repo` | **vive** |
| `test_la_puerta_de_paridad_tambien_cubre_el_modo_verify` | **vive** |
| las cuatro de la puerta del mensaje | **viven** |
| `test_la_puerta_de_paridad_va_despues_de_validar_repo_por_estructura` | **MUERE** |

Motivo literal del log:

> `AssertionError: la puerta de paridad (linea 860) tiene que ir DESPUES de `validar_repo` (linea 864): la asimetria se com…`

**Conclusión de M3: la afirmación del dev es CIERTA y el diseño es el correcto.**
`M5'` no cambia ni un byte de stdout ni un código de salida en ninguna de las 9
sondas de comportamiento, y solo la sonda AST lo caza —que es literalmente lo
que `proposal.md` §4 declara. No hay agujero: hay un mutante equivalente con su
cazador.

### M3 · y contra la suite COMPLETA de 207 (no solo mi subconjunto)

Que 9 sondas no vean un mutante no basta para decir «ninguna lo ve». Medí `M5'`
contra las **207**, en la cámara A:

| | control | con `M5'` |
|---|---|---|
| líneas del log | 366 | 368 |
| última línea | `ALL TESTS PASSED.` | traceback de `..._por_estructura` |
| dónde muere | — | `run_tests.py:26804`, la **segunda de las dos** últimas llamadas de `__main__` |

Las dos líneas de salida anteriores al fallo son la prueba de que todo lo demás
pasó:

```
Probando que la paridad gana al repo invalido en los DOS modos...
Precedencia OK: par roto + repo roto da 2 en commit y en --verify; par entero + repo roto da 3 en los dos.
Probando que la puerta de paridad va DESPUES de validar_repo (ast)...
AssertionError: la puerta de paridad (linea 860) tiene que ir DESPUES de
`validar_repo` (linea 864) … Este es el mutante `M5'`, y es equivalente (no se ve
en la salida porque `validar_repo` no imprime)
```

**Las 206 sondas que se ejecutan antes pasan con `M5'` puesto.** Esa es la prueba
de equivalencia que el encargo pedía, y no una lectura del código.

## 7. M4 · la sonda AST: ¿mide o parece medir?

Un test AST sobre números de línea se puede auto-satisfacer. Lo medí rompiéndola
de cuatro formas, todas verificadas en disco y todas **parseando**:

| id | qué rompí | veredicto | motivo literal / por qué |
|---|---|---|---|
| `M5p` | la puerta sube por encima de `validar_repo` | **killed** | `AssertionError: la puerta de paridad (linea 860) tiene que ir DESPUES de `validar_repo` (linea 864)…` — muere por la **comparación de orden**, que es lo que dice medir |
| `M4-f` | `if verify and not ok:` → `if not ok and verify:` (reescritura **equivalente** que haría un developer real) | **killed**, pero **por el motivo equivocado** | `AssertionError: NO se ha encontrado en el CUERPO de `main()` el `if verify and not ok:`…` — la forma estructural exige `verify` como **primer** operando del `and`, luego no encuentra el nodo |
| `M4e` | el bloque de la puerta desaparece del cuerpo de `main()` | **killed** (5 sondas) | La contraprueba existe y es real: sin bloque no hay rama que devuelva éxito |
| `M4d` | puerta muda: `if paridad_rota:` con cuerpo `pass` en el orden correcto | **killed** (5 sondas, incluida la AST) | El tercer aserto —«el cuerpo dice `paridad-git`»— hace su trabajo: sin él, una puerta en el sitio correcto que no rechaza nada pasaría |

**Lo que la sonda AST SÍ cumple, medido:** no puede quedarse verde sin mirar
ninguna de las tres cosas que afirma. Las tres contrapruebas (`puerta`,
`validar`, `veredicto` no encontrados) fallan fuerte, y el cuerpo se comprueba.

**Lo que NO cumple, y es la rigidez real de M4:** la forma es **estricta en el
orden de los operandos**. Una reescritura semánticamente idéntica —
`not ok and verify`— la mata, no porque el orden de las puertas sea incorrecto,
sino porque la sonda no la reconoce. Y el mismo rasgo se ve en `R4-k` y `R4-n`
(§5): mueren también en esta sonda, y no por su aserción de orden sino por
«no encuentro el `if`». **Medido y dicho, no supuesto:** el mensaje del fallo dice
exactamente qué reescribir la sonda, luego es un fallo ruidoso y no un falso
verde. Calibración: **baja**, no `alta`.

## 7.bis. M6a del dev · la comparación por texto de `ast.unparse`, medida

El dev afirma que la sonda vieja buscaba `if verify and not ok:` **por texto** y
que eso nunca encontraba la línea. Medido sobre el wrapper real:

```
texto de la CONDICION por unparse: 'verify and (not ok)'
la cadena 'verify and not ok' esta dentro? False
estructura: BoolOp(op=And, values=['Name', 'UnaryOp'])
```

**El diagnóstico del dev es CIERTO.** Y la pregunta de fondo —«¿la forma
estructural cubre también `verify and not ok` escrito SIN paréntesis?» —
también: las dos escrituras producen el **mismo árbol**, medido con `ast.dump`
(`iguales: True`). La cobertura que sí falta es el **orden de los operandos**
(§7, `M4-f`), no los paréntesis.

## 8. M5 · la reescritura de la sonda vieja: ¿tiene contraprueba?

**Sí, y está medida.** La sonda reescrita
(`test_la_puerta_de_paridad_va_despues_de_validar_repo`) tiene el par entero →
`3` **en la misma función**, con las tres aserciones que la hacen una guarda y no
un deseo:

```
assert r_ok.returncode == 3                          # par ENTERO + repo roto -> 3
assert "WOPT_REPO_INVALIDO" in (r_ok.stdout or "")   # y que diga POR QUE
assert "WOPT_USAGE paridad-git" not in (r_ok.stdout or "")
```

**Medido con el mutante `M4d` y con `M5e` (`if True:` en el sitio de la puerta,
que devuelve `2` a todo):** el control de par entero es el que salta. Es
decir, un wrapper que devolviera `2` **siempre** no puede pasar esta sonda: en la
celda de control tiene que dar `3`. El agujero que el encargo sospechaba no
existe.

## 9. Tabla completa: un mutante por fila

Instrumento: subconjunto de 10 sondas (`subset.py`), salvo donde dice «suite
completa» (las 207). Cada mutante se restaura desde el wrapper real, se verifica
en disco y se le pasa **`ast.parse` antes de correr**: un mutante que no parsea no
mide nada.

| id | qué rompí | veredicto | quién muere y por qué |
|---|---|---|---|
| `CONTROL` | nada | **verde** | 10/10; log de 44 líneas que acaba en `ALL TESTS PASSED.` |
| `R4-k` | `if paridad_rota and ok:` | **killed** | 3 sondas; la primera aserción es la celda `commit + par roto + repo roto` (sale `3`) |
| `R4-n` | `if paridad_rota and not verify:` | **killed** | 4 sondas; `..._tambien_cubre_el_modo_verify` muere con «salio con **0**», el `WOPT_REPO_OK` mintiendo que el dev promete |
| `M5'` (`M5p`) | la puerta por encima de `validar_repo` | **killed, solo por la AST** | las 9 sondas de comportamiento **viven**; la AST muere por la comparación de orden |
| `M4-f` | `not ok and verify` (reescritura equivalente) | **killed** | la AST, por «no se ha encontrado el nodo» (rigidez, §7) |
| `M4d` | puerta muda: cuerpo `pass` | **killed** | 5 sondas, incluida la AST por el aserto de `paridad-git` |
| `M4e` | la puerta fuera del cuerpo de `main()` | **killed** | 5 sondas, incluida la AST por la contraprueba de «no encontrado» |
| `M5e` | `if True:` → `2` siempre | **killed** | **7 de 10**, empezando por el control de par entero de la sonda reescrita |
| `K1` | la puerta del mensaje acepta `T-\d+` | **killed** | 2 sondas: «`chore: T-061 (algo)` tiene que RECHAZARSE: `T-NNN` es OTRO espacio de ids» |
| `K2` | la puerta del mensaje antes del NOOP | **killed** | `test_la_puerta_se_coloca_despues_del_noop_y_antes_de_add`: «el orden de las cuatro fronteras del wrapper es normativo y esta roto» |
| `M4d` (v1) | `pass` **insertado** delante del `print` | **NO MEDIDO** | mutante **no-op**: +13 bytes, la puerta seguía rechazando igual. No puede matar nada; se rehízo |
| `K2` (v1) | puerta movida dejando el cuerpo colgando | **NO MEDIDO** | mutante **roto**: `IndentationError` en el wrapper. Descartado y rehecho por líneas |

## 10. Supervivientes, por severidad

**Ninguno que sea un fallo del contrato.** El único superviviente es `M5'` frente
a las 9 sondas de comportamiento, y es un mutante **EQUIVALENTE demostrado**
(§6): no cambia stdout ni código de salida en ninguna celda. Sobrevive
legítimamente y muere donde debe, en la sonda AST.

Hallazgos que **no** son fallos del ciclo, calibrados y con su Medida:

| # | severidad | hallazgo | evidencia |
|---|---|---|---|
| H1 | **baja** | El documento (`sandbox-rules.md:70`, regla 4) afirma que la línea `WOPT_*` «es la última que se imprime», y el camino de commit imprime un `INFO` **después** de su `WOPT_REPO_INVALIDO`. El documento **no lo admite** en ningún sitio (buscado: cero coincidencias) | §2 (M6b) y §4 (M8) |
| H2 | **baja** | La sonda AST es estricta en el **orden de los operandos** del `and`: `not ok and verify` la mata por «no encontrado», no por su aserción. Fallo ruidoso, nunca verde | §7 (`M4-f`) |
| H3 | **informativa** | El nombre `..._va_despues_de_validar_repo` ya **no** describe lo que mide (mide precedencia del `2` sobre el `3`, no posición frente a `validar_repo`). El docstring lo dice y declara qué no puede medir | §8 |

## 11. Límites de esta medición, dichos antes del veredicto

1. **Instrumento.** Diez de las 207 sondas se ejercitan por importación directa
   (`subset.py`), no por la suite completa. Es suficiente para un veredicto de
   **muerte** (una aserción que salta no depende del orden) y para uno de
   **supervivencia dentro del subconjunto**, pero no para afirmar «ninguna de las
   207 lo caza» sin medirlo. Por eso el único superviviente (`M5'`) se midió
   además contra la **suite completa**.
2. **La suite completa necesita un arreglo de cámara para correr.** La primera
   pasada murió en `test_el_archivo_legacy_esta_versionado_y_no_vuelve_a_la_raiz`
   (`rc=1`, el fichero no está en el índice): es un artefacto de la cámara —su
   repo desechable no tiene ese `git add` del repo real—, **no un defecto del
   código**. Con `git add -A` en la cámara la suite completa da **366 líneas y
   `ALL TESTS PASSED.`**. Sin ese arreglo, un rojo de cámara se habría leído como
   una muerte de mutante que no ocurrió.
3. **Lo que NO he medido** y por tanto no afirmo: nada sobre `src/`, sobre los
   guards de `src/woptimizer/**`, ni el resto de la suite con mutantes distintos
   de `M5'`. Este ciclo toca `.taskmaster/git_safe_commit.py` y las sondas de
   tooling, y ahí está la medición.
4. **Confesión de arnés.** Dos veredictos de la tabla salieron **NO MEDIDOS** y se
   rehicieron: un `pass` insertado delante del `print` (mutante no-op) y una puerta
   movida a medias (mutante que no parseaba). Los dos fallos eran míos, no del repo,
   y quedan en la tabla para que se puedan reauditar.

## 12. Prueba final de que el repo real no se tocó

| comprobación | resultado al terminar |
|---|---|
| `git log --oneline -1` | `3e155f5 fix(tooling): el 2 de la paridad precede al 3 del repo en los dos modos (TASK-074)` — **el HEAD anclado, sin mover** |
| `git status --porcelain` | una sola línea: `?? openspec/changes/2026-10-18-paridad-antes-del-repo-invalido/mutation-report.md` |
| `git diff --stat` / `git diff --cached --stat` | **vacíos los dos** |
| `git reflog -2` | `3e155f5` y `83a79ad`: **ninguna entrada nueva**, luego no hubo ningún commit mío |
| `git rev-parse --git-dir` desde la raíz | el desacoplado del host (lectura) |
| digest del wrapper **real** | `F47500769381`, **idéntico** al de antes de empezar y al que uso para restaurar entre mutantes |
| `git rev-parse --absolute-git-dir` dentro de cada cámara | la cámara **A** y la **B** apuntan a sus propios `.git` de `%TEMP%` |

Confieso lo que sí hice, porque es parte del encargo: creé dos copias en `%TEMP%`
(`wopt_t074_camara_A` y `…_B`), inicialicé en cada una un repo **nuevo** (para
que `_entorno_git_del_repo()` tuviera algo que leer), las muté y las dejé como
están. **Nunca invoqué `git_safe_commit.py` como versionador**, ni `checkout`,
`reset`, `stash`, `clean` ni `restore` sobre el repo real. El único fichero
escrito en el repo es este informe, y **no está commiteado**.

## 13. VERDICT

# PASS

Los ocho mutantes con derecho a morir, mueren, **por la aserción que nombra la
celda**: `R4-k`, `R4-n`, `M5'`, `M4-f`, `M4d`, `M4e`, `M5e`, `K1`, `K2`. El único
superviviente, `M5'`, es un **equivalente demostrado** —las 206 sondas de la suite
completa pasan con él puesto— y muere en la sonda AST que existe exactamente para
eso. No queda nada que se pondría de manifiesto si el contrato estuviera mal.

Los tres hallazgos abiertos (H1 regla 4 / `INFO` tras la canónica, H2 rigidez de
la forma AST con los operandos del `and`, H3 nombre de la sonda reescrita) son
**baja o informativa**, ninguno rompe contrato, y los tres están medidos con su
motivo.

> Lo único que este informe **no** sostiene: que las 197 sondas fuera del
> subconjunto mueren también con `R4-k`, `R4-n`, `M5e`, `K1` o `K2`. Afirmarlo
> pediría cinco corridas más de la suite entera. No se afirma: se midió el
> subconjunto de 10, con `CONTROL` verde y cada muerte con su traceback.