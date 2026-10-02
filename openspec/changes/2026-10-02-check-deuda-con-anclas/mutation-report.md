# Informe de mutacion — check 8 de la Deuda Tecnica Conocida (TASK-060, ciclo #49)

**Change ID:** `2026-10-02-check-deuda-con-anclas`
**Ronda:** 3.ª del ciclo #49 (cierre), tras el **FAIL** del `mutation-auditor` de la
ronda 2 (7 supervivientes, tres de ellos sobre la garantia central del check).
**Fecha de medicion:** 2026-10-02, en Windows.

## 0. EL BASELINE, DECLARADO — y por qué este informe REEMPLAZA al anterior

**Todo lo que hay en este informe se midió contra el commit `eaa9bb1`** (HEAD al
empezar este pase) y contra el árbol de este pase. La versión anterior de este
fichero **no declaraba ni su baseline ni su commit**, y sus cifras no reproducen
sobre el árbol donde se medieron. No es un detalle: un informe de mutación sin
baseline declarado no se puede re-auditar, que es lo único para lo que sirve.

| | Informe anterior | Medido en `eaa9bb1` (esta ronda) |
|---|---|---|
| Anclas del panel intacto | `32` | **`35`** |
| Anclas tras el mutante P4 | `21` | **`22`** |
| Delta de P4 | `11` | **`13`** |
| Mutantes de panel sin un solo FAIL | «cinco» | **siete** (P1, P2, P3, P4, P8, P9, P10) |
| Muerte de C5 | «MUERE con `IndexError`» | **MUERE por la aserción del envoltorio**, que captura el `IndexError` |
| §3.3 y límite 4: «las filas 88 y 89 declaran 🔴» | afirmación | **falso para la 88**: `_gravedad_declarada(fila 88)` devuelve `None` |

Las tres primeras filas no son erratas de redondeo: el informe anterior se midió
sobre **otro árbol**. Y la quinta importa más de lo que parece: la conclusión
—el suelo de gravedad muere— era correcta, la descripción no, y una descripción
falsa en un informe que se cita como evidencia es la forma más barata de perder
un ciclo entero.

**Estado del panel que se mide, y es el mismo en las dos columnas de todas las
tablas:** `115 OK / 0 FAIL`, 15 filas, 7 exentas, 8 vivas, **35 anclas** de ruta
resuelta y 2 por contenido, suite de **104 tests**.

## 1. Como reproducir una fila de este informe

Nada se escribe en el árbol: `git_safe_commit.py` hace `add -A`.

- **Mutantes de panel** — se copia el **repo entero** (sin `.git`, `dist` ni
  caches) a un `tempfile.mkdtemp()` de `%TEMP%`, se sustituye `STATUS.md` por el
  mutado y se mide `validar(temp)`. La copia tiene que ser COMPLETA: MEDIDO que
  con la copia parcial que usa el esqueleto de los tests el recuento de anclas cae
  de **35 a 28** (`.agents/` y `.taskmaster/*.py` no están) y **sin
  `.taskmaster/git_safe_commit.py` el suelo de gravedad no existe**, con lo que
  P6, P7 y G2 morirían por un motivo que no es el suyo. Una campana sobre un árbol
  que no es el repo mide otra cosa.
- **Columna `HEAD`** — el validador de `eaa9bb1` **reconstruido por parche
  inverso** de los cinco puntos que este pase cambia (`_RE_CERRADA` sin final de
  palabra, la ventana de negación, la negación de la prosa, la comparación por
  cadena y el motivo del error). No hay `git` en este entorno, así que el baseline
  se reconstruye; el control es que las dos columnas coincidan exactamente sobre
  el panel intacto (`0 FAIL / 7 exentas / 8 vivas / 35 anclas`).
- **Mutantes de código** — se copia el repo a `%TEMP%`, se aplica el mutante al
  fichero de la **copia** y se ejecuta **solo**
  `test_la_deuda_exige_un_ancla_resoluble_en_toda_fila_viva()` en un subproceso
  limpio. `run_tests.py` devuelve el **primer** test que revienta, luego sin el
  subproceso propio no se puede atribuir la muerte. El original de la copia se
  restaura y se **comprueba byte a byte** al final (medido: `True`).
- Todas las cadenas de abajo son **literales de byte**: una parafrasis no es
  re-auditable. Los `print()` son ASCII puro (trampa #16: consola cp1252).

```powershell
python validate_docs.py            # 115 OK, 0 FAIL
python run_tests.py                # 104 tests, ALL TESTS PASSED
python verify_ui_syntax.py
```

---

## 2. Mutantes del PANEL (25) — `ok` y FAIL antes y despues

**Por que la linea `ok` va en la tabla y no en prosa.** Ocho de estos mutantes **no
producen ni un `FAIL`**: o el ataque queda neutralizado, o es un residuo declarado.
Sin la linea `ok` antes/despues un reauditor los leeria como «0 FAIL = correcto».

Formato de la linea `ok`: `fila(s) / exenta(s) / viva(s) / anclas`.

| id | Fichero y edicion (antes -> despues) | `ok` HEAD | `ok` ARREGL | FAIL | Veredicto |
|---|---|---|---|---|---|
| **P1** | fila 89, tras `de invocaci`: ` " Y esta fila NO esta CERRADA todavia."` | `15 / 7 / 8 / 35` | `15 / 7 / 8 / 35` | `0 -> 0` | **NEUTRALIZADO.** No cambia un solo numero. |
| **P2** | fila 89, tras `ones de shell`: ` (marcada *CERRAD* en el panel)` | `15 / 7 / 8 / 35` | `15 / 7 / 8 / 35` | `0 -> 0` | **NEUTRALIZADO.** |
| **P3** | fila 89, tras `de invocaci`: ` **NO CERRADA todavia** en TASK-061` | `15 / 7 / 8 / 35` | `15 / 7 / 8 / 35` | `0 -> 0` | **NEUTRALIZADO.** Lo detiene la condicion 4. |
| **P4** | fila 89, tras `de invocaci`: ` **CERRADA en CYCLE-999**` | `15 / 8 / 7 / 22` | `15 / 8 / 7 / 22` | `0 -> 0` | **SOBREVIVE, y es el residuo que se declara** (limites 5 y 19). |
| **P5** | fila nueva antes de la 88: `- **Fila que se deriva de si misma (A1):** su unica verdad es \`STATUS.md:9 Deuda Tecnica Conocida\`, que existe.` | `16 / 7 / 9 / 35` | `16 / 7 / 9 / 35` | `0 -> 2` | **MUERE** (ya en HEAD). `STATUS.md Deuda fila 88: VIVA sin ancla resoluble (0 fuentes de 5)` + `ancla NO RESOLUBLE: STATUS.md EXISTE pero es el propio panel` |
| **A1a** | la misma fila con `status.md` (minusculas) | `16 / 7 / 9 / 36` | `16 / 7 / 9 / 35` | `0 -> 2` | **MUERE con este pase.** `ancla NO RESOLUBLE: status.md EXISTE pero es el propio panel` |
| **A1b** | idem con `./STATUS.md` | `16 / 7 / 9 / 36` | `16 / 7 / 9 / 35` | `0 -> 2` | **MUERE con este pase.** |
| **A1c** | idem con `docs/../STATUS.md` | `16 / 7 / 9 / 36` | `16 / 7 / 9 / 35` | `0 -> 2` | **MUERE con este pase.** |
| **A1d** | idem con `.\STATUS.md` | `16 / 7 / 9 / 36` | `16 / 7 / 9 / 35` | `0 -> 2` | **MUERE con este pase.** |
| **A1e** | idem con `STATUS.MD` | `16 / 7 / 9 / 35` | `16 / 7 / 9 / 35` | `0 -> 1` | **MUERE por otra regla**: `_RE_RUTA` exige la extension en minusculas, luego no llega a ser cita. Se deja intacto. |
| **V1** | fila 89, tras `de invocaci`: ` — **CERRADA, aunque NO lo parezca (TASK-061)**` | `15 / 8 / 7 / 22` | `15 / 7 / 8 / 35` | `0 -> 0` | **NEUTRALIZADO con este pase** (la negacion va por veredicto). |
| **V2** | fila 89: ` — **CERRADA**. NO lo esta: sigue pendiente TASK-061.` | `15 / 8 / 7 / 22` | `15 / 7 / 8 / 35` | `0 -> 0` | **NEUTRALIZADO con este pase** (la negacion va por prosa). |
| **V3** | fila 89: ` — **CERRADAS todas en TASK-061**` | `15 / 8 / 7 / 22` | `15 / 7 / 8 / 35` | `0 -> 0` | **NEUTRALIZADO con este pase** (el marcador exige final de palabra). |
| **V4** | fila 89: ` — **a diferencia de las CERRADAS, esta sigue viva (TASK-061)**` | `15 / 8 / 7 / 22` | `15 / 7 / 8 / 35` | `0 -> 0` | **NEUTRALIZADO con este pase** (mismo motivo que V3). |
| **V5** | fila 89: ` — **NO: CERRADA en TASK-061**` | `15 / 8 / 7 / 22` | `15 / 7 / 8 / 35` | `0 -> 0` | **NEUTRALIZADO con este pase** (la ventana cortable por `:` era lo que lo dejaba pasar). |
| **G2f'** | fila 88, tras `sandbox-rules.md\`)`: ` — **CERRADA en TASK-059**` | `15 / 8 / 7 / 33` | `15 / 8 / 7 / 33` | `0 -> 0` | **SOBREVIVE**, y no se puede cerrar: ver limite 19 y §4.6. |
| **G2a'** | fila 89, justo detras de su primer 🔴: ` 🟡 ` | `15 / 7 / 8 / 35` | `15 / 7 / 8 / 35` | `0 -> 0` | **SOBREVIVE**: gana la PRIMERA gravedad del texto (limite 15). |
| **G2b'** | fila 100: 🟡 -> 🟠 | `15 / 7 / 8 / 35` | `15 / 7 / 8 / 35` | `0 -> 0` | **SOBREVIVE**: un glifo fuera del mapa no es gravedad (limite 16). |
| **P6** | fila 88, tras `- **`: `🟡 ` | `15 / 7 / 8 / 35` | `15 / 7 / 8 / 35` | `0 -> 1` | **MUERE.** `STATUS.md Deuda fila 88: declara AMARILLO pero su comprobable SIGUE VIVO: .taskmaster/git_safe_commit.py declara 0 para WOPT_COMMIT_OK y para WOPT_NOOP` |
| **P7** | fila 89, tras `- **`: `🟡 ` | `15 / 7 / 8 / 35` | `15 / 7 / 8 / 35` | `0 -> 1` | **MUERE.** Idem, en la fila 89. |
| **P8** | fila 89, tras `de invocaci`: `` `` y ` ` `` | `15 / 7 / 8 / 35` | `15 / 7 / 8 / 35` | `0 -> 0` | **NEUTRALIZADO**, y el validador imprime INFORME. |
| **P9** | fila 100: `«96 tests»` -> `«42 tests»` | `15 / 7 / 8 / 35` | `15 / 7 / 8 / 35` | `0 -> 0` | **SOBREVIVE por decision** (limite 12: es una CITA atribuida, no una declaracion). |
| **P10** | fila 96: borra `CERRADA en CYCLE-027 (TASK-037) ` | `15 / 6 / 9 / 36` | `15 / 6 / 9 / 36` | `0 -> 0` | **CONTROL negativo**, sobrevive a proposito. |
| **N1a** | fila nueva antes de la 88: `- **Fila que miente sobre el recuento:** segun \`run_tests.py\` la suite tiene 42 tests y sigue viva.` | `16 / 7 / 9 / 36` | `16 / 7 / 9 / 36` | `0 -> 0` | **SOBREVIVE** (limite 17): citar un fichero en la MISMA frase convierte la mentira en cita. |
| **N1b** | la misma mentira con la cita en la frase ANTERIOR | `16 / 7 / 9 / 36` | `16 / 7 / 9 / 36` | `0 -> 1` | **MUERE.** `STATUS.md Deuda fila 88: declara el numero [42] que NO es el derivado con ast de run_tests.py (104)` |

**Recuento del panel: 9 mueren · 8 neutralizados · 8 sobreviven, todos declarados.**

## 3. Mutantes del CODIGO (17) — muerte medida en aislamiento

Se ejecutan **solo** sobre
`test_la_deuda_exige_un_ancla_resoluble_en_toda_fila_viva()` y en la **copia** de
`%TEMP%`, nunca en el árbol.

| id | Edicion (antes -> despues) | Muerte medida |
|---|---|---|
| **C1** | el bucle de veredictos -> `return bool(_RE_CERRADA.search(...))` (la palabra suelta) | **MUERE**: `escenario l: la palabra de cierre en PROSA no exime a nadie: el check NO acuso ['VIVA sin ancla resoluble']` |
| **C2** | `_ruta_de_ancla`: la identidad -> `return real` | **MUERE**: `escenario n: el panel no puede certificarse a si mismo: el check NO acuso ['VIVA sin ancla resoluble', 'ancla NO RESOLUBLE: STATUS.md ...']` |
| **C3** | `if suelo and gravedad and gravedad != "ROJO":` -> `if False and ...` | **MUERE**: `escenario h: la gravedad baja y el problema sigue vivo: el check NO acuso ['declara AMARILLO pero su comprobable SIGUE VIVO']` |
| **C4** | la forma `^[ \t]*0[ \t]+CODIGO\b` -> el predicado viejo `(?<!\d)0\b[^\n]*CODIGO` | **MUERE**: `escenario q: mencionar el contrato no es DECLARAR el contrato: el check acuso ['su comprobable SIGUE VIVO'] y no debia` |
| **C5** | `_citas_de_la_fila`: borrar `if not palabras: continue` | **MUERE por la asercion del envoltorio, NO por el `IndexError`**: `validar(root) debia devolver un INFORME y tiro IndexError: list index out of range`. Es la correccion al informe anterior: el envoltorio captura la excepcion, luego lo que se mide es que el validador **no** entregue informe. |
| **C6** | S5: `elif derivado in anclas["numeros"]` -> `elif False and ...` | **MUERE**: `escenario o: el check acuso ['VIVA sin ancla resoluble', 'NO es el derivado con ast']` |
| **C7** | `derivado in anclas["numeros"]` -> `104 in ...` (constante a mano) | **MUERE**: mismo escenario `o`. El derivado de este arbol es 7, no 104. |
| **C8** | `run_tests.py`: `assert len(FILAS) == 25` -> `== 99` | **MUERE**: `la tabla de escenarios del check 8 tiene 25 filas y su contrato son 25` |
| **C9** | el `ok.append(...)` del check 8 -> `if False: ok.append(...)` | **MUERE**: `escenario a: el check NO imprimio su linea \`ok\` de la seccion` |
| **C13** | `if ids:` -> `if True:` | **MUERE con este pase**: `escenario r: veredicto en negrita con un id que NO resuelve: el check NO acuso ['VIVA sin ancla resoluble']`. Era superviviente en la ronda anterior. |
| **C21** | la memoizacion de los ids (`if ids is None:` -> sin ella) | **SOBREVIVE, y es INERTE**: no cambia ningun veredicto, solo evita un calculo repetido. |
| **C25** | `findall(texto)` -> `[texto]` (la negrita deja de exigirse) | **MUERE con este pase**: `escenario u: el marcador tiene que estar en NEGRITA: la linea \`ok\` dice '... 1 exenta(s) CERRADA(s), 0 viva(s) ...'`. Era superviviente en la ronda anterior. |
| **C26** | `_RE_CERRADA` -> `re.IGNORECASE` | **MUERE con este pase**: `escenario s: el marcador en minusculas no cierra nada: la linea \`ok\` dice '... 1 exenta(s) CERRADA(s), 0 viva(s) ...'`. Era superviviente en la ronda anterior. |
| **C27** | anadir `limpio.replace('**', '')` | **SOBREVIVE, y es INERTE**: `_RE_NEGRITA` ya entrego el texto sin los asteriscos. |
| **C28** | borrar la negacion sobre la **prosa** | **MUERE**: `escenario v: la negacion en la PROSA tambien niega el cierre: la linea \`ok\` dice '... 1 exenta(s) CERRADA(s), 0 viva(s) ...'` |
| **C29** | la identidad -> igualdad de cadena con `"STATUS.md"` | **MUERE**: `escenario w: el panel no se certifica a si mismo con otra GRAFIA: el check NO acuso ['VIVA sin ancla resoluble', 'ancla NO RESOLUBLE: status.md EXISTE pero es el propio panel']` |
| **C30** | quitar `os.path.normcase` de la comparacion | **SOBREVIVE**, y se explica: en Windows `os.path.realpath` llama a `_getfinalpathname` y **devuelve el nombre real** del fichero, luego las cinco grafias colapsan al mismo camino con la misma caja y `normcase` es redundante aqui. Se conserva como segunda garantia para sistemas donde `realpath` no canonicaliza, y se declara que **ninguna fila lo vigila**. |

**Recuento del codigo: 14 mueren · 3 sobreviven (C21 y C27 inertes; C30
redundante en Windows).**

---

## 4. Lo que NO cubre ningun limite (leido como lista de afirmaciones)

Una lista solo de muertes es una lista que afirma cobertura del 100 %, que es
exactamente lo que este repo lleva 49 ciclos corrigiendo. Estas cosas **no** las
mata nadie, y estan escritas para que el proximo que audite no las descubra como
novedad:

1. **P1, P2, P3, V1-V5 no producen un FAIL en el panel real**: quedan
   neutralizados y su unico sintoma es el desplazamiento `7 exenta(s)/8 viva(s)` ->
   `8/7`, que ya no ocurre.
2. **A1 no mueve la linea `ok` en el recuento**: el `35 -> 36` con el panel
   autocertificado solo se ve comparando este informe con el anterior.
3. **El suelo es inerte sobre el panel real**: neutralizarlo entero deja
   `115 OK / 0 FAIL`. MEDIDO ademas que **no hay fila victima ni con un glifo
   fuera del mapa (G2b') ni con una gravedad historica antes de la de hoy (G2a')**
   (limites 15 y 16): el suelo tiene hoy **cero** filas que puedan delatarlo.
4. **La gravedad que cuenta es la primera del texto**, luego una gravedad
   historica tapa la de hoy (G2a').
5. **P8**: el validador ya no muere, pero tampoco distingue el tramo vacio de una
   fila normal; solo se ve en la ausencia de traceback.
6. **G2f' y P4 son el MISMO agujero, y no se puede cerrar** (limites 5 y 19). Lo
   que se afirmaba de G2f' —«una sola frase apaga tres guards»— es correcto para
   la fila y **falso para el suelo**: la fila 88 **no declara ninguna gravedad**
   (`_gravedad_declarada` -> `None`), luego su suelo no podia dispararse ni antes
   ni despues. Lo que se apaga es la fila entera (`8 exenta(s) / 7 viva(s) /
   33` anclas). Y la regla que lo frenaria —el id trazable tiene que estar FUERA
   del veredicto— **rompe la fila 87**, que es CERRADA de verdad y no tiene ningun
   id fuera del suyo: MEDIDO que las filas **87, 96 y 97** tienen todos sus ids
   trazables **dentro** del veredicto, luego la fila 87 y la fila 88+ataque tienen
   la misma forma y no hay regla que las separe sin poner el repo en rojo.
7. **N1a**: una fila nueva puede mentir sobre el recuento y quedar en verde
   citando un fichero **en la misma frase** (limite 17).
8. **La `114 OK / 0 FAIL` de amputar el check 8** lo vigila **una** asercion
   (C9), y el **acoplamiento de `len(errors)`** del esqueleto de tests hace que un
   panel roto haga morir `test_el_journal_ilegible_informa_en_vez_de_reventar_el_validador`,
   cuyo sujeto es el journal: falla **ruido, no verde**. Declarado como limite
   **14** de `docs/ai/sandbox-rules.md`.
9. **C21, C27 y C30 sobreviven y no son agujeros**: los dos primeros no cambian
   ningun veredicto y el tercero es redundante en Windows. Se archivan como
   inertes para que el proximo no los vuelva a medir esperando una muerte.

---

## 5. Controles negativos (NO deben morir)

Se archivan **como tales**: un control que sobrevive es una asercion de cobertura, no
un fallo.

| id | Que hace | Medido por |
|---|---|---|
| **P10** | abrir la fila 96 borrando su cierre | aqui, `0 FAIL` y `6 exenta(s) / 9 viva(s) / 36` anclas |
| **C21, C27, C30** | inertes o redundantes (§4.9) | aqui |
| **E4, A2, G3b, N2, M4b, C11, C14-C17, C20, C22** | controles y mutantes de la ronda anterior del auditor | **el auditor, no remedidos aqui.** Sus ediciones byte a byte **no estan en el repo**, de modo que re-medirlos exige pedirlos al auditor. Se declara en vez de inventarse una medicion |

---

## 6. Lo que este informe deja abierto

- **La fila 100 vive hoy con una cita desfasada**: dice que `docs/index.md:25`
  declara «96 tests» y ese fichero declara hoy `(104 tests)`. **No se corrige
  aqui** porque las filas del panel no se reescriben en este cambio, y porque la
  fila *documenta* el defecto. Queda dicho, medido y sin tocar; es el límite 12.
- **G2f' sobrevive** y no es cerrable sin poner el repo en rojo (limite 19). No es
  un descuido de este pase: es la forma que tienen la fila 87 y el ataque, y la
  diferencia entre ambas no existe.
- **Una negacion escondida en otro veredicto no cuenta** (limite 20). Es el precio
  de no romper la fila 87.
- **Los controles E4, A2, G3b, N2, M4b, C11, C14-C17, C20 y C22** no son
  re-audibles desde el repo (ver §5).
- **El recuento de escenarios del test es 25 y su contrato es 25.** La tabla
  aumento de 19 a 25 en este pase (r, s, t, u, v, w) y **el numero de tests no
  cambio: sigue en 104**, porque los escenarios son filas de una tabla.
