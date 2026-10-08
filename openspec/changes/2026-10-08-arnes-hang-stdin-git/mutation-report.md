# Informe de mutacion — CYCLE-060 / TASK-072 (arnes-hang-stdin-git)

**Fecha**: 2026-10-08
**Auditor**: `mutation-auditor` (Sherlock), ronda independiente
**Commit auditado**: `0864628` — *fix(arnes): stdin heredado en las 37 llamadas de git y dos pre-vuelo tautologicos (TASK-072)*
**Arbol auditado**: rama `beta`, `src/woptimizer/**` **intacto** (fuera de alcance por AC-6)
**VERDICT: FAIL — 11 supervivientes de 21 mutaciones**

---

## 0. Condiciones de la medicion

| | |
|---|---|
| Camara | `%TEMP%\wopt_c60_192849`, creada con `shutil.copytree(..., ignore=shutil.ignore_patterns(".git"))` |
| `.git` en la camara | **ausente como fichero y como directorio** (`isfile=False`, `isdir=False`) |
| `src/` en la camara | **copiado** (`isdir=True`): sin el, los hijos mueren por `ModuleNotFoundError` y no miden nada |
| Aislamiento probado | `git rev-parse --git-dir` con `GIT_DIR` desechable explicito → **rc 128**, `fatal: not a git repository: '...wopt_c60_192849_gitdir_desechable'`. Nunca devuelve una ruta del repo real |
| Repo real | **CERO escrituras.** Verificado al final con `git log`/`status`/`diff`/`rev-parse` (§6). Confesion: el primer script de copia se escribio por error en la raiz del repo y se movio a `%TEMP%` en el minuto siguiente; el arbol quedo limpio (`git status --porcelain` vacio) y no llego a tocarse ningun fichero versionado |
| Arnes | `run_tests.py` completo = **619 s**, asi que **no se ejecuto entero por mutante**. Se ejecutaron subconjuntos, declarados uno por uno en cada fila. La **suite completa se ejecuto UNA vez, al final**, para comprobar que la camara vuelve a verde: RC=0 en 417,2 s (§6) |

**Subconjuntos usados** (todos con purga de `__pycache__` antes de importar y `GIT_DIR` desechable nuevo por intento):

- **RAPIDO** (~5 s): `test_ninguna_llamada_de_cat_file_batch_check_se_queda_sin_input` + `test_el_pre_vuelo_de_un_hash_muerto_distingue_existe_de_no_existe`
- **ENV** (~1 s en verde): `test_el_envoltorio_git_no_hereda_stdin_y_no_cuelga_en_desatendido`
- **CHECK9** (**268,5 s**): `test_el_check_9_de_los_hashes_del_journal_sobre_un_arbol_sintetico`. MEDIDO: llama a `validar()` ~20 veces y `validar` cuesta **10,3 s**, luego este test solo se ejecutó donde hacía falta
- **VALIDADOR**: `validate_docs.py` sobre la camara (para T5)

**Regla de veredicto aplicada**: `killed` solo si el test muere por su `AssertionError` con mensaje;
`survived` solo si todos los tests del subconjunto pasan. Ningun rojo de `ImportError`/`SyntaxError`/
`RecursionError`/`FileNotFoundError` se cuenta como veredicto: son bugs **mios** de instrumentacion y
estan listados como descartados en §5.

---

## 1. Tabla fix → mutacion → veredicto → motivo

### T1 — `stdin=subprocess.DEVNULL` en `_git_de_fixture` (`run_tests.py:12764-12769`)

| ID | Mutacion | Veredicto | Motivo literal |
|---|---|---|---|
| **A1** | Quitar `stdin=subprocess.DEVNULL,` del envoltorio | **killed** | `AssertionError` a los **60,47 s**: *"el envoltorio REAL de git se ha quedado colgado mas de 60 s con un `stdin` heredado que es un pipe abierto sin EOF"*. Subconjunto ENV. **La garantia central del ciclo SI esta verificada** |
| **A2** | `for _intento in (1, 2, 3):` → `for _intento in (1,):` en el envoltorio | **survived** | Subconjunto RAPIDO en verde. Ningun test lee el numero de intentos |
| **A3** | Quitar `stdin=subprocess.DEVNULL` **del helper** `_objeto_existe_en_fixture` | **survived** | Subconjunto RAPIDO en verde. `cat-file -e` no lee stdin, luego el modo de fallo no se manifiesta y solo el hijo del test del envoltorio construye el pipe — y ese hijo llama al ENVOLTORIO, no al helper |

### T2 — `_objeto_existe_en_fixture(hash_, cwd)` y sus reglas de rc

| ID | Mutacion | Veredicto | Motivo literal |
|---|---|---|---|
| **B1** | El helper devuelve `True` siempre | **killed** | *"el hash muerto `deadbee` tiene que NO existir en esa fixture"* |
| **B2** | El helper devuelve `False` siempre | **killed** | *"el hash real `d518eb5` tiene que EXISTIR en su propia fixture"* |
| **B3** | `rc == 128` → `return True` (invertir la regla) | **killed** | *"el hash muerto `deadbee` tiene que NO existir…"* |
| **B4** | Borrar la rama `rc == 128` (128 cae en reintentos → `AssertionError`) | **killed** | *"git cat-file -e deadbee fallo tres veces en la fixture con un rc que NO es 0 (existe) ni 128 (no existe): **fatal: Not a valid object name deadbee**"* |
| **B5** | `raise AssertionError(...)` → `return False` (fail-open ante rc inesperado) | **survived** | Subconjunto RAPIDO en verde. La rama no la ejecuta ningun test (§3, S1) |
| **B6** | `cat-file -e` → `cat-file -t` | **survived** | Subconjunto RAPIDO en verde. La eleccion de primitive no esta verificada: ambos dan rc 0/128 igual |
| **B7** | `for _intento in (1, 2, 3):` → `(1,)` en el helper | **survived** | Subconjunto RAPIDO en verde. Mismo hueco que A2 |

### T3 — los dos pre-vuelo del check 9, migrados al helper

| ID | Mutacion | Veredicto | Motivo literal |
|---|---|---|---|
| **C1** | El pre-vuelo afirma lo contrario: `is False` → `is True` para el hash muerto | **killed** | `AssertionError` en **1,10 s**: *"pre-vuelo: el hash muerto de la fixture `deadbee` tiene que NO existir en ella"*. **El pre-vuelo ya no es decorativo** |
| **C2r** | Borrar el pre-vuelo del hash muerto (4 lineas, del todo) | **survived** | Subconjunto CHECK9: **PASSED en 268,50 s**. Nada vigila que el pre-vuelo siga ahi (§3, S5) |

### T4 — el guard estructural `ast` y los tres tests nuevos

| ID | Mutacion | Veredicto | Motivo literal |
|---|---|---|---|
| **D1r** | La forma prohibida vuelve **por el envoltorio real**: `_git_de_fixture(["cat-file", "--batch-check"], cwd)` | **killed** | *"hay llamadas a `git cat-file --batch-check` SIN `input=` en las lineas [12763]"* |
| **D2** | La forma prohibida como literal: `subprocess.run(["git", "cat-file", "--batch-check"], …)` | **killed** | El mismo `AssertionError`, linea 12763 |
| **D3r** | La misma, escrita como **tupla**: `subprocess.run(("git", "cat-file", "--batch-check"), …)` | **survived** | Subconjunto RAPIDO en verde. El guard solo mira `ast.List` (§3, S2) |
| **D4r** | La misma, con **variable intermedia**: `args = ["git","cat-file","--batch-check"]; subprocess.run(args, …)` | **survived** | Subconjunto RAPIDO en verde |
| **D5r** | La misma, con **concatenacion**: `["git", "cat-file", "--batch" + "-check"]` | **survived** | Subconjunto RAPIDO en verde |
| **D7r** | La misma, como **`["git"] + ["cat-file","--batch-check"]`** | **survived** | Subconjunto RAPIDO en verde. Es la forma que el propio envoltorio usa para construir su comando |
| **D6** | Desactivar la deteccion del guard: `for argumento in []:` | **survived** | Subconjunto RAPIDO en verde. **La contraprueba del propio guard no la ejerce** (§3, S1) |

### T5 — los cuatro declarantes de 194 = 142 + 52

| ID | Mutacion | Veredicto | Motivo literal |
|---|---|---|---|
| **E1r** | Un test **definido y NO invocado** (se borra su llamada del `__main__`) | **killed** | `validate_docs.py` rc=1, tres FAIL que lo nombran: *"194 test(s) definidos y 193 invocado(s) en el `__main__`. definido y NO invocado: `test_ninguna_llamada_de_cat_file_batch_check_se_queda_sin_input`"*, *"el reparto derivado suma 193 y el recuento de tests es 194"* y el reparto de STATUS.md |
| **E2** | `AGENTS.md`: `194 tests headless` → `195 tests headless` | **killed** | *[FAIL] AGENTS.md: declara [195] tests y la verdad son 194 (derivado de run_tests.py con ast)* |

**Y la afirmacion positiva de T5 se ha MEDIDO, no supuesto**: `validate_docs` sobre el **arbol real**
devuelve **FAIL=0** y deriva `(142, 52, 194, …)`. El reparto **142 backend + 52 headless** que declaran
`AGENTS.md`, `README.md`, `STATUS.md` y `docs/ai/testing-guide.md` es **cierto** y esta derivado con `ast`, no escrito a mano.

---

## 2. Resumen

| | |
|---|---|
| Mutaciones medidas | **21** |
| `killed` | **10** (A1, B1, B2, B3, B4, C1, D1r, D2, E1r, E2) |
| `survived` | **11** (A2, A3, B5, B6, B7, C2r, D3r, D4r, D5r, D7r, D6) |
| Descartadas por bug **mio** | 5 (ver §5) |
| **VERDICT** | **FAIL** |

El nucleo del ciclo esta bien: quitar el `stdin=DEVNULL` **muere a los 60 s** (A1) y las cuatro reglas del
helper **mueren en su asercion** (B1-B4). Los cinco mutantes que el dev declara cazados los he
reproducido **de forma independiente** y los confirmo. Los 11 supervivientes estan **todos fuera** de los
cinco que el se probo, y tres de ellos (B5, D6, D3r-D7r) son de la clase exacta que este ciclo vino a matar:
**una comprobacion que no puede fallar**.

---

## 3. Supervivientes por severidad

### 🔴 ALTA

**S1 — B5: la rama de git-roto es fail-open y no la ejecuta nadie.**
El helper reimplementa los tres intentos *para eso*: "cualquier rc que no sea 0 ni 128 es un fallo de git o el
`spawn EPERM` intermitente de este host, y tras tres intentos tiene que reventar". Con `return False` en esa
rama, un git roto se traduce a **"el objeto no existe"**: exactamente el falso verde que el ciclo dice matar,
en la unica rama que no tiene test. Y hay un agravante medido en el propio repo: `validate_docs.py:490-493`
documenta que **"directorio vacio (no es repo)" tambien devuelve rc 128**, luego la disyuntiva "existe / no
existe" solo es correcta si git esta vivo.
**Arreglo**: un test que fuerce un rc ∉ {0, 128} (inyectando `subprocess.run` en el modulo o pidiendo un hash
malformado) y exija `AssertionError` con el `stderr` literal. Mientras no exista, la rama se vende en el
docstring y no mide nada.

**S2 — D6: el guard se puede desactivar entero y su contraprueba sigue verde.**
`for argumento in []` deja el guard mirando cero llamadas y el test pasa. La contraprueba del propio guard
(`_tiene_input`) prueba **otra** cosa: que `ast` ve un keyword `input`, no que la deteccion de `--batch-check`
funcione. Es un guard que no se autovigila: a una edicion de estar decorativo.
**Arreglo**: que la contraprueba llame a la **deteccion real** sobre los cuatro fragmentos y compruebe las
dos mitades (`pasa_el_batch` y el veredicto de `input=`), no un predicado auxiliar.

### 🟡 MEDIA

**S3 — D3r, D4r, D5r, D7r: el guard ve 2 de 6 formas de escribir la forma prohibida.**
MEDIDO sobre la copia exacta de la deteccion del guard:

| Forma | La ve el guard |
|---|---|
| `["cat-file", "--batch-check"]` | SI |
| `["git", "cat-file", "--batch-check"]` | SI |
| `("git", "cat-file", "--batch-check")` (tupla) | **NO** |
| variable intermedia | **NO** |
| `["git", "cat-file", "--batch" + "-check"]` | **NO** |
| `["git"] + ["cat-file", "--batch-check"]` | **NO** |
| `f"git cat-file --batch-check"` con `shell=True` | **NO** |

La causa es una linea: el guard exige `isinstance(argumento, ast.List)`. Una tupla es un `ast.Tuple`, un
`BinOp` no es una lista y un `Name` no es una lista. **Lo importante**: el autor ya sabia que la forma
natural varyaba y por eso amplio de una a dos — pero el limite no es "cuantas formas conozco" sino
"reconozco elargumento", y eso sigue sin cumplirse.
**Arreglo**: resolver la lista a texto antes de decidir (`ast.literal_eval` sobre listas, tuplas y concatenaciones
de constantes, mas el caso `["git"] + [...]`), o—a falta de mas— buscar `--batch-check` como **constante**
en cualquier `ast.Constant` del modulo, que es la forma en que la primitive aparece de verdad.

**S4 — A2 y B7: "tres intentos" no lo verifica nadie, en los dos envoltorios.**
AC-1 dice "son 3 llamadas y las 3 heredan" y el mensaje de error dice "fallo tres veces"; con `for _intento in (1,)`
todo sigue en verde. El motivo declarado del reintento es el **`spawn EPERM` intermitente de este host**, o sea
justo el fallo para el que existe: un unico intento convierte un EPERM transitorio en una respuesta falsa.
**Arreglo**: un test que inyecte dos `rc` no-cero seguidos y uno bueno, y exija que la llamada devuelve la
correcta; hoy nadie mide ni un reintento.

### 🟢 BAJA

- **A3** — el `stdin=DEVNULL` **del helper** no esta verificado por nada. Hoy es inocuo (`cat-file -e` no lee stdin), pero es la mitad del patron y nadie lo sostiene.
- **B6** — `cat-file -t` en vez de `-e`: verde. No es un defecto (ambos son correctos), pero **la eleccion de la primitive no esta verificada** y el docstring afirma una medicion que el test no reproduce.
- **C2r** — se puede borrar el pre-vuelo del check 9 y la suite sigue verde (268,50 s). Exposicion contenida: el caso positivo que se anadio al lado seguiria delatando una fixture rota, pero **la asercion del pre-vuelo en si no esta vigilada**.
- **Contador decorativo** — el guard imprime `f"…({len(CON_INPUT)} con input= …)"` y ese numero es **0**; ninguna asercion lo lee. Un contador que nadie lee no mide.

---

## 4. Afirmaciones documentales comprobadas contra el codigo

| # | Afirmacion | Veredicto |
|---|---|---|
| **DOC-1** | `CHANGELOG.md` y `STATUS.md:101`: *"37 llamadas a git que salen todas por el mismo envoltorio"* | **FALSA en presente.** MEDIDO por `ast`: en el padre eran **36 call-sites + 1 definicion** (de ahi el 37); hoy hay **35** por el envoltorio y **6** por un envoltorio nuevo, `_objeto_existe_en_fixture`: **41 llamadas de git, y 6 no salen por el mismo sitio** |
| **DOC-2** | `STATUS.md:9`: *"el validador entero baja de 12,27 s a 7,14 s"* y *"la derivacion del reparto […] baja a la practica cero"* | **NO REPRODUCE HOY.** MEDIDO en el **arbol real**: `validar` = **10,28 s** (FAIL=0) y `_reparto_de_tests` = **3,14 s**. El reparto no es "practica cero": son 3 s. El panel se mide a si mismo y el numero no cuadra |
| **DOC-3** | `tasks.json` AC-2: *"… y `communicate(timeout=10)`"* | **NO SE CUMPLE TAL COMO ESTA ESCRITA.** El codigo usa **60 s**, con justificacion medida en el docstring del test, pero el AC no se actualizo. Quien lea el AC al pie de la letra lo dara por fallido. (Medido: A1 muere a los **60,47 s**, no a los 10) |
| **DOC-4** | Los cuatro declarantes: **194 = 142 + 52** | **CIERTO Y VIGILADO.** Derivado con `ast` por el validador; E1r y E2 demuestran que se rompe en rojo si se desincroniza |
| **DOC-5** | El unico `--batch-check` legitimo esta en `validate_docs.py` | **CIERTO.** `validate_docs.py:519-524` lo escribe con `input="\n".join(pedidos)+"\n"`; grep de todo el repo: no hay ninguna otra |

**Colateral, fuera de TASK-072** (no loAccounting como fallo del ciclo, pero explica el presupuesto):
`test_el_check_9_…` tarda **268,5 s** porque llama a `validar()` ~20 veces y `validar` cuesta **10,3 s**.
Con 194 filas de test en `__main__` y un `ast.parse` del fichero entero (1,27 MB) por llamada, cada test que
toca el validador paga los 10 s completos. Es la razon de los 619 s de suite.

---

## 5. Lo que NO son hallazgos (bugs mios de instrumentacion)

Se listan porque un informe que se calla un rojo suyo parece mas limpio de lo que es:

| ID | Que paso | Que hice |
|---|---|---|
| C2 (v1) | Borre solo la primera linea del `assert` multilinea → **SyntaxError** en el harness | Mutacion reformulada como **C2r** (bloque completo), que si se midio |
| D1/D3/D4/D5 (v1) | Escribi las sondas con `"cat-file"` como ejecutable → **FileNotFoundError**; y D1 recursaba infinitamente | Reescritas con `"git"` delante (**D1r/D3r/D4r/D5r/D7r**) |
| E1r (v1) | Ancla ambigua: el nombre del test aparece **2 veces** (`def NAME():` contiene `NAME()`) → el corredor aborta sin medir | Ancla a la linea de invocacion completa; medida |
| — | `test_el_check_9_…` "colgado" | No lo estaba: 268,5 s de llamadas legitimas a `validar`. Confirmado con `faulthandler` |

Ningun veredicto de este informe procede de uno de estos cuatro casos.

---

## 6. Estado final de la camara y del repo real

**Camara: verde.** `run_tests.py` restaurado byte a byte tras cada mutacion (`RESTAURADO-FINAL: True` en los cuatro lotes) y **suite completa ejecutada al terminar**:

```
RC=0   segundos=417,2   lineas=404
...
Envoltorio de git sin stdin heredado: los dos comandos vuelven en un padre desatendido con el pipe abierto.
Pre-vuelo de existencia: el hash real se resuelve y el muerto no, y el 128 de git no se pierde como AssertionError.
Guard estructural de cat-file: 0 llamadas sin input= (0 con input= en run_tests.py, todas legitimas).

ALL TESTS PASSED.
```

Los tres tests del ciclo se ejecutaron y pasaron dentro de esa corrida completa.

**Dos apuntes de honestidad sobre esa corrida:**

1. El **primer** intento de suite completa en la camara **no termino en `ALL TESTS PASSED`**: se detuvo en `test_la_puerta_de_paridad_va_despues_de_validar_repo` (`run_tests.py:19718`) con `AssertionError: git no resuelve --absolute-git-dir … fatal: not a git repository`. Eso **NO es un hallazgo del ciclo**: es la consecuencia directa del protocolo de aislamiento, que niega a la camara el `.git` del repo real. Se resolvio dando a la camara un **repo desechable propio** (`git init` dentro de `%TEMP%`, un unico commit, 234 ficheros, `git-dir` = `…/wopt_c60_192849/.git`, comprobado que **no** es `woptimizer_git` ni el arbol de Nextcloud) y relanzando. La cifra de 417,2 s es menor que los 619,3 s del repo real porque el historial de la camara tiene un commit en vez de ~60.
2. La camara se midio tambien contra el **arbol real** para no acusar al panel con una cifra de `%TEMP%`: `validate_docs` da **10,28 s** en el real y **10,30 s** en la camara. El entorno de medicion es comparable.

**Repo real: sin escrituras.** Al terminar:

```
git log --oneline -1  -> 0864628 fix(arnes): stdin heredado en las 37 llamadas de git ...
git status --porcelain-> ?? openspec/changes/2026-10-08-arnes-hang-stdin-git/mutation-report.md
git diff --stat       -> (vacio)
git diff --cached --stat -> (vacio)
git rev-parse --git-dir -> C:\Users\carch\AppData\Local\woptimizer_git\.git
```

El unico cambio es **este informe**, que es la entrega que el encargo autoriza. Sin commits, sin staging, sin
modificaciones. Confesion ya hecha en §0: el primer script de copia se escribio por error en la raiz del repo
y se movio a `%TEMP%` de inmediato; no llego a tocar ningun fichero versionado.

---

## 7. Lo que pido a `openspec-dev` (por orden)

1. **S1** — test que fuerce un rc ∉ {0,128} y exija el `AssertionError` con `stderr` literal. Sin el, el fail-open sigue vivo.
2. **S2** — que la contraprueba del guard ejerza la deteccion real y no un predicado auxiliar.
3. **S3** — que el guard resuelva el argumento a texto (tupla, `BinOp`, variable, concatenacion) en vez de exigir `ast.List`.
4. **S4** — test de reintentos: dos rc no-cero y uno bueno.
5. **DOC-1 / DOC-3** — corregir "37 llamadas" (hoy 41 por dos envoltorios) y el `timeout` de AC-2 (10 s escrito, 60 s implementado).
6. **DOC-2** — remedir o marcar la cifra de 7,14 s: hoy el validador cuesta 10,28 s en el arbol real.