# Informe de mutacion — check 8 de la Deuda Tecnica Conocida (TASK-060, ciclo #49)

**Change ID:** `2026-10-02-check-deuda-con-anclas`
**Ronda:** cierre del ciclo #49, tras el **FAIL** del `mutation-auditor` (30 mutantes: 15 muertas, 14 supervivientes).
**Fecha de medicion:** 2026-10-02.
**Sin este fichero el FAIL no es re-auditable**, y un informe que solo dijera "0 FAIL" volveria a certificar un falso verde: cinco de los mutantes de panel de esta ronda **no producen ni un FAIL**.

---

## 0. Como reproducir una fila de este informe

Todos los mutantes de panel se aplican sobre una **copia del esqueleto en `%TEMP%`** (nada
en el arbol: `git_safe_commit.py` hace `add -A`) y se miden con `validar(root)` sobre esa
copia. El codigo mutado se aplica sobre el fichero real, se ejecuta **solo** el test
concernido en un subproceso limpio, y el original se restaura byte a byte.

```powershell
python validate_docs.py            # 115 OK, 0 FAIL
python run_tests.py                # 104 tests, ALL TESTS PASSED
```

Las cadenas de abajo son **literales de byte** (`repr()` del tramo anterior y posterior al
punto de diferencia), no parafrasis: una parafrasis no es re-auditable.

---

## 1. Mutantes del PANEL (P1-P10) — con la linea `ok` ANTES y DESPUES

**Por que la linea `ok` va en la tabla y no en prosa.** Los mutantes P1, P2, P3 y P8 **no
producen ni un `FAIL`**: o bien el ataque queda neutralizado (la fila sigue viva y con sus
anclas), o bien es un residuo declarado. Sin la linea `ok` antes/despues, un reauditor los
leeria como "0 FAIL = correcto".

### P1 — autoexencion con una frase normal (CRITICA, era el E1 del auditor)

| | |
|---|---|
| Fichero | `STATUS.md`, fila 89 (la 🔴 del `spawn EPERM`) |
| ANTES | `...de shell, incluidos \`tm.py\` y \`git_` (offset 120 de la fila) |
| DESPUES | `...de invocaci` **`" Y esta fila NO esta CERRADA todavia."`** `one` |
| `ok` ANTES | `15 fila(s), 7 exenta(s) CERRADA(s), 8 viva(s) con 32 ancla(s) de ruta resuelta(s) y 2 por contenido` |
| `ok` DESPUES | `15 fila(s), 7 exenta(s) CERRADA(s), 8 viva(s) con 32 ancla(s) de ruta resuelta(s) y 2 por contenido` |
| FAIL | `0 -> 0` |
| **Veredicto** | **NEUTRALIZADO.** Con el marcador de una sola palabra esta fila pasaba a `8 exenta(s) / 7 viva(s)` y el validador respondia `115 OK / 0 FAIL`. Hoy la frase no cambia **un solo numero** de la linea `ok`: el ataque es un no-op. |

### P2 — autoexencion con una mencion en cursiva (era el E2)

| | |
|---|---|
| Fichero | `STATUS.md`, fila 89 |
| ANTES | `...de invocaci` `ones de shell` (offset 120) |
| DESPUES | `...de invocaci` **`" (marcada *CERRAD* en el panel)"`** `ones de s` |
| `ok` ANTES | `15 fila(s), 7 exenta(s) CERRADA(s), 8 viva(s) ... 32 ancla(s) ... 2 por contenido` |
| `ok` DESPUES | **identica** |
| FAIL | `0 -> 0` |
| **Veredicto** | **NEUTRALIZADO**, por la misma causa que P1. |

### P3 — veredicto en negrita que NIEGA el cierre (nuevo, no lo midio el auditor)

| | |
|---|---|
| Fichero | `STATUS.md`, fila 89 |
| ANTES | `...de invocaci` `ones ` (offset 120) |
| DESPUES | `...de invocaci` **`" **NO CERRADA todavia** en TASK-061"`** `ones ` |
| `ok` ANTES | `15 fila(s), 7 exenta(s) CERRADA(s), 8 viva(s) ... 32 ancla(s) ... 2 por contenido` |
| `ok` DESPUES | **identica** |
| FAIL | `0 -> 0` |
| **Veredicto** | **NEUTRALIZADO.** Es el caso que P1 y P2 **no** cubren: aqui hay negrita, hay mayusculas y hay un id que resuelve, y solo lo detiene la regla de negacion. Sin ella, esta fila quedaria exenta. |

### P4 — veredicto completo con un id que NO resuelve (RESIDUAL DECLARADO)

| | |
|---|---|
| Fichero | `STATUS.md`, fila 89 |
| ANTES | `...de invocaci` `ones de shell, ` (offset 120) |
| DESPUES | `...de invocaci` **`" **CERRADA en CYCLE-999**"`** `ones de shell, ` |
| `ok` ANTES | `15 fila(s), 7 exenta(s) CERRADA(s), 8 viva(s) con 32 ancla(s) ... 2 por contenido` |
| `ok` DESPUES | **`15 fila(s), 8 exenta(s) CERRADA(s), 7 viva(s) con 21 ancla(s) ... 1 por contenido`** |
| FAIL | `0 -> 0` |
| **Veredicto** | **SOBREVIVE, y es el residuo que se declara.** La fila se exime. La causa esta medida y escrita: el id trazable se busca **en la fila**, no en el veredicto, porque la fila 90 (CERRADA de verdad) escribe su `TASK-057` **fuera** de su veredicto, y atar el id al veredicto la volveria viva y pondria el repo en rojo sin motivo. Es limite **5** de `docs/ai/sandbox-rules.md`. |

### P5 — el panel se certifica a si mismo (ALTA, era el A1)

| | |
|---|---|
| Fichero | `STATUS.md`, nueva fila antes de la 88 |
| ANTES | `...(\`STATUS.md:96\`).\n- **\`.git\` del` |
| DESPUES | `...(\`STATUS.md:96\`).\n- **Fila que se deriva de si misma:** su uni` |
| `ok` ANTES | `15 fila(s), 7 exenta(s) CERRADA(s), 8 viva(s) con 32 ancla(s) ... 2 por contenido` |
| `ok` DESPUES | `16 fila(s), 7 exenta(s) CERRADA(s), 9 viva(s) con 32 ancla(s) ... 2 por contenido` |
| FAIL | `0 -> 2` |
| **Expectativa literal** | `STATUS.md Deuda fila 88: VIVA sin ancla resoluble (0 fuentes de 5)` y `STATUS.md Deuda fila 88: ancla NO RESOLUBLE: STATUS.md EXISTE pero es el propio panel` |
| **Veredicto** | **MUERE.** Cierra elucido ademas: las **cuatro** filas reales que se citan a si mismas (87, 89, 100, 101) siguen teniendo otra fuente, asi que **ningun veredicto del repo cambia** al rechazar `STATUS.md`. La diferencia en la linea `ok` es solo el recuento de rutas: `39 -> 35`. |

### P6 — bajar la 🔴 de la fila 88 a 🟡 (ALTA, era el G3a del auditor)

| | |
|---|---|
| Fichero | `STATUS.md`, fila 88 |
| ANTES | `\n- **\`.git\` del \xe1rbol de trabajo corrupto` |
| DESPUES | `\n- **\U0001f7e1 \`.git\` del \xe1rbol de trabajo corrupto` |
| `ok` ANTES | `15 fila(s), 7 exenta(s) CERRADA(s), 8 viva(s) ... 32 ancla(s) ... 2 por contenido` |
| `ok` DESPUES | **identica** (el suelo no cambia el recuento de filas) |
| FAIL | `0 -> 1` |
| **Expectativa literal** | `STATUS.md Deuda fila 88: declara AMARILLO pero su comprobable SIGUE VIVO: .taskmaster/git_safe_commit.py declara 0 para WOPT_COMMIT_OK y para WOPT_NOOP` |
| **Veredicto** | **MUERE.** Es el criterio **M5** del contrato, que antes era inalcanzable: la gravedad no se leia. |

### P7 — bajar la 🔴 de la fila 89 a 🟡 (M5 sobre la fila que lo describio)

| | |
|---|---|
| Fichero | `STATUS.md`, fila 89 |
| ANTES | `\n- **Shell intermitente en el entorno de agen` |
| DESPUES | `\n- **\U0001f7e1 Shell intermitente en el entorno de ag` |
| `ok` ANTES / DESPUES | identica en ambas |
| FAIL | `0 -> 1` |
| **Expectativa literal** | `STATUS.md Deuda fila 89: declara AMARILLO pero su comprobable SIGUE VIVO: .taskmaster/git_safe_commit.py` |
| **Veredicto** | **MUERE.** |

### P8 — tramo de codigo inline VACIO (el `IndexError` que encontro el auditor por accidente)

| | |
|---|---|
| Fichero | `STATUS.md`, fila 89 |
| ANTES | `...de invocaci` `ones de shell, incluidos \`tm.p` |
| DESPUES | `...de invocaci` **`" \`\` y \` \` "`** `ones de shell, incluidos \`tm.p` |
| `ok` ANTES / DESPUES | identica en ambas |
| FAIL | `0 -> 0`, **y el validador imprime INFORME** |
| **Veredicto** | **NEUTRALIZADO.** Antes `palabras[0]` sobre un token vacio reventaba con `IndexError` y **todo el validador moria sin informe**. El mutante de codigo que lo deshace (C6) si muere. |

### P9 — corromper la cifra que la fila DECLARA conservando el derivado (RESIDUAL DECLARADO, era el N1)

| | |
|---|---|
| Fichero | `STATUS.md`, fila 100 |
| ANTES | `declara \xab96 tests\xbb y la verdad son 103` |
| DESPUES | `declara \xab42 tests\xbb y la verdad son 103` |
| `ok` ANTES / DESPUES | identica en ambas |
| FAIL | `0 -> 0` |
| **Veredicto** | **SOBREVIVE por decision, y la decision esta escrita** (limite 12 de `docs/ai/sandbox-rules.md`). La cifra que declara la 100 es una **cita** de `docs/index.md`, no una afirmacion sobre el recuento. Verificarla contra el contenido actual de ese documento haria **imposible de redactar la fila 100**, que existe para documentar que ese documento declaraba una cifra desfasada. Lo que si se arranca: el `ok` antes de este ciclo acreditaba S5 con `re.search(derivado, fila)`, y ahora solo acredita la cifra que la fila **declara** (`derivado in numeros`), que es lo que mata C6 y C7. |

### P10 — abrir la fila 96 borrando su cierre (CONTROL NEGATIVO, M4 del auditor)

| | |
|---|---|
| Fichero | `STATUS.md`, fila 96 |
| ANTES | `\n- **\U0001f534 CERRADA en CYCLE-027 (TASK-037) \u2014 guarda` |
| DESPUES | `\n- **\U0001f534 \u2014 guardas que no guardaban (3 filas):** ` |
| `ok` ANTES | `7 exenta(s) CERRADA(s), 8 viva(s) con 32 ancla(s)` |
| `ok` DESPUES | `6 exenta(s) CERRADA(s), 9 viva(s) con 33 ancla(s)` |
| FAIL | `0 -> 0` |
| **Veredicto** | **CONTROL, y sobrevive a proposito.** El auditor lo declaro ACEPTABLE: exige borrar una palabra explicita, y la fila que reaparece es verificable de verdad (`TASK-037` cerrado **y** `validate_docs.py` presente). No se arregla. |

---

## 2. Mutantes del CODIGO (C1-C10) — muerte medida EN AISLAMIENTO

`run_tests.py` devuelve **el primer** test que revienta, asi que la atribucion de cada
mutante se midio en un subproceso propio que ejecuta **solo**
`test_la_deuda_exige_un_ancla_resoluble_en_toda_fila_viva()`. El original se restaura
byte a byte despues de cada uno.

| id | Fichero y edicion (antes -> despues) | Muerte medida |
|---|---|---|
| **C1** | `validate_docs.py`, `_esta_cerrada`: el bucle de veredictos -> la palabra suelta `return bool(_RE_CERRADA.search(...))` | **MUERE**: `escenario l: la palabra de cierre en PROSA no exime a nadie: el check NO acuso ['VIVA sin ancla resoluble']` |
| **C2** | `validate_docs.py`, `_ruta_de_ancla`: `return None if real == EL_PANEL_NO_ES_ANCLA else real` -> `return real` | **MUERE**: `escenario n: el panel no puede certificarse a si mismo: el check NO acuso ['VIVA sin ancla resoluble', 'ancla NO RESOLUBLE: STATUS.md ...']` |
| **C3** | `validate_docs.py`, `_severidad_minima`: `if suelo and gravedad and gravedad != "ROJO"` -> `if False and ...` | **MUERE**: `escenario h: la gravedad baja y el problema sigue vivo: el check NO acuso ['declara AMARILLO pero su comprobable SIGUE VIVO']` |
| **C4** | `validate_docs.py`, `_declara_el_codigo_sobrecargado`: la forma `^[ \t]*0[ \t]+CODIGO\b` -> el predicado viejo `(?<!\d)0\b[^\n]*CODIGO` | **MUERE**: `escenario q: mencionar el contrato no es DECLARAR el contrato: el check acuso ['su comprobable SIGUE VIVO'] y no debia`. **Medido en dos rondas**: con solo los trece escenarios originales este mutante **SOBREVIVIA**, porque el arbol sintetico no tenia un fichero que *mencionase* el contrato sin declararlo. El escenario (q) se anadio para cerrarlo |
| **C5** | `validate_docs.py`, `_citas_de_la_fila`: borrar `if not palabras: continue` | **MUERE** con `IndexError: list index out of range` |
| **C6** | `validate_docs.py`, S5: `elif derivado in anclas["numeros"]` -> `elif False and derivado in ...` | **MUERE**: `escenario o: el check acuso ['VIVA sin ancla resoluble', 'NO es el derivado con ast ...']` |
| **C7** | `validate_docs.py`, S5: `derivado in anclas["numeros"]` -> `104 in anclas["numeros"]` (constante a mano) | **MUERE**: mismo escenario `o`. Es el C8 del auditor, y muere **solo** porque el escenario deriva de un arbol sintetico de 7 tests |
| **C8** | `run_tests.py`: `assert len(FILAS) == 18` -> `== 99` | **MUERE**: `la tabla de escenarios del check 8 tiene 18 filas y su contrato son 18` |
| **C9** | `validate_docs.py`: `ok.append(...)` del check 8 -> `if False: ok.append(...)` (amputar el check entero) | **MUERE**: `escenario a: el check NO imprimio su linea \`ok\` de la seccion` |

---

## 3. Lo que NO cubre ningun limite (leido como lista de afirmaciones)

Una lista solo de muertes es una lista que afirma cobertura del 100 %, que es
exactamente lo que este repo lleva 49 ciclos corrigiendo. Estas seis cosas **no** las
mata nadie, y estan escritas para que el proximo que audite no las descubra como
novedad:

1. **E1/E2 (P1, P2, P3) no producen un FAIL en el panel real**: quedan neutralizados, y
   solo el escenario sintetico `l` y `m` los detecta. En el panel, el unico sintoma era
   el desplazamiento `7 exenta(s)/8 viva(s)` -> `8/7`, y hoy no hay ni eso.
2. **A1 (P5) deja de mover la linea `ok` en el recuento de rutas**: el `39 -> 35` solo se
   ve comparando el informe antes y despues, no el veredicto.
3. **El suelo es inerte sobre el panel real** (neutralizarlo entero deja `115 OK / 0 FAIL`,
   porque ninguna fila viva declara una gravedad por debajo de su suelo). Solo P6 y P7 lo
   muerden, y solo porque bajan el emoji de una fila cuyo suelo es `ROJO`.
4. **N1 (P9)**: una cifra citada en vez de declarada puede ser falsa sin que nadie lo vea.
5. **El `IndexError` (P8)**: el validador ya no muere, pero tampoco distingue el tramo
   vacio de una fila normal; solo se ve en la ausencia de traceback.
6. **El `114 OK / 0 FAIL` de amputar el check 8** lo vigila **una** asercion (C9), y el
   **acoplamiento de `len(errors)`** del esqueleto de tests hace que un panel roto haga
   morir `test_el_journal_ilegible_informa_en_vez_de_reventar_el_validador`, cuyo sujeto
   es el journal: falla **ruido, no verde**, pero un `len(errors) == 1` es un conteo
   exacto atado al panel. Declarado como limite **14** de `docs/ai/sandbox-rules.md`.

---

## 4. Controles negativos (NO deben morir)

Se archivan **como tales**: un control que sobrevive es una asercion de cobertura, no un
fallo.

| id | Que hace | Medido por |
|---|---|---|
| **P10** | abrir la fila 96 borrando su cierre | aqui, `0 FAIL` y `6 exenta(s)/9 viva(s)` |
| **E4, A2, G3b, N2, M4b** | controles de la ronda anterior del auditor | **el auditor, no remedidos aqui.** Sus ediciones byte a byte **no estan en el repo** (no habia `mutation-report.md`), de modo que re-medirlos exige pedirlas al auditor. Se declara en vez de inventarse una medicion |

---

## 5. Lo que este informe deja abierto

- **La fila 100 vive hoy con una cita desfasada**: dice que `docs/index.md:25` declara
  «96 tests» y ese fichero declara hoy `(104 tests)`. **No se corrige aqui** porque las
  filas del panel no se reescriben en este cambio, y porque la fila *documenta* el defecto
  (una vez corregido, su texto es historicamente cierto y su objeto desaparece). Queda
  dicho, medido y sin tocar.
- **Los controles E4, A2, G3b, N2 y M4b** no son re-audibles desde el repo (ver §4).
