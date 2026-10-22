# Informe de mutación — TASK-082 (ciclo 68)

**Contrato:** `openspec/changes/2026-10-21-vistas-del-guard-de-workers-derivadas/proposal.md` (§7 = AC-1..AC-5)
**Artefacto auditado:** commit `f8bc867` — *fix(tools): el conjunto de vistas del guard de workers se deriva (TASK-082)*
**Auditor:** Sherlock (mutation-auditor) · **Fecha:** 2026-10-21
**Alcance:** `run_tests.py` (tooling). **Cero ediciones bajo `src/woptimizer/`.**

> Este informe se escribe **incrementalmente**, sección por sección. Si falta una
> sección, es que la medición de esa parte no llegó a completarse — no que esté
> vacía por descuido.

---

## 0. Ficha de la medición

### 0.1 Cámara

| Dato | Valor |
|---|---|
| Cámara | `%TEMP%\wopt_c68_aud\camara_20261021_223501` (suite) y `…\camara_b_20261021_225308` (atribución) |
| Copia | `shutil.copytree(..., ignore=ignore_patterns)` con `.git` excluido **como fichero** (en este repo `.git` es un **fichero** de 57 B, no un directorio) |
| `src/woptimizer/` | **real**, copiado |
| Repo de la cámara | `.git` **nuevo** (`git init -b beta`, un commit). **Nunca** el del repo real |
| Entorno de la suite | **sin** `GIT_DIR` / `GIT_WORK_TREE`, igual que en el repo real |

### 0.2 Aislamiento del repo real — MEDIDO antes de mutar nada

```
CAMARA: C:\Users\carch\AppData\Local\Temp\wopt_c68_aud\camara_20261021_223501
.git presente en la camara tras copiar?  False
rev-parse --git-dir (GIT_DIR desechable) -> '…\wopt_c68_aud\gitdesechable_223501'
devuelve el repo real?                   False
AISLAMIENTO OK:                          True
sin GIT_DIR -> rc: 128 | err: 'fatal: not a git repository (or any of the parent directories): .git'
descubre el repo real?                   False
```

`git rev-parse --git-dir` desde la raíz del repo real devuelve
`C:/Users/carch/AppData/Local/woptimizer_git/.git` (el desacoplado del VFS), que es
un repo **distinto** del de la cámara.

### 0.3 Tres fallos de INSTRUMENTO encontrados y reparados (no son veredictos)

| # | Fallo | Por qué era del instrumento | Reparación |
|---|---|---|---|
| **I-1** | `test_la_puerta_de_paridad_va_despues_de_validar_repo` → `AssertionError: git no resuelve `--absolute-git-dir` para …\camara_… con el entorno limpio` | La cámara **no tenía repo**: `_git_dir_absoluto_de_este_arbol()` lee el `.git` del árbol con entorno limpio y **falla fuerte** si git no responde (no degrada a `""`, a propósito) | Se montó un repo **propio y desechable** en la cámara (`git init` + 1 commit). Nunca el del repo real |
| **I-2** | `test_la_resolucion_del_repositorio_tiene_un_solo_punto` → `AssertionError: … la ruta resuelta es '…\camara_…\.git' y el default del host es '…\localappdata\woptimizer_git\.git'` | El **entorno** llevaba `GIT_DIR` apuntando a la cámara, y la precedencia de `_resolver_el_repositorio` hace que `GIT_DIR` gane al default del host. El test exige el comportamiento **del host**, donde no hay `GIT_DIR` en el entorno | Se quitó `GIT_DIR`/`GIT_WORK_TREE` del entorno de la suite (igual que el repo real) |
| **I-3** | La primera versión de **M-V1** murió por `test_las_citas_de_sandbox_rules_siguen_siendo_ciertas`: `AssertionError: run_tests.py:23127 ya no cita 'sandbox-rules.md:55-56'` | La mutación **añadía 2 líneas** en el guard de workers (9423) → desplazaba la línea 23127 → el guard de citas (que ata números de línea) moría. Eso es **ruido de `P2`**, no la aserción del mutante | Se rehízo el catálogo: **ninguna** mutación cambia el contenido de la línea 23127 (verificado con `ast` + comparación línea a línea). La primera versión del log se conserva renombrada (`suite_M-V1_v1_INVALIDA.log`) |

**Cómo se decidió qué líneas están vigiladas (MEDIDO, no supuesto):**
`test_las_citas_de_sandbox_rules_siguen_siendo_ciertas` es el **único** guard que
comprueba **en runtime** un número de línea de `run_tests.py`: la **23127**. Las
demás citas por número (`14787`, `23102`, `23125`, `2511`, `6327`, `6362`,
`2300`, `303`) son menciones de docstring que **nadie** comprueba (grep sobre
`run_tests.py` y `validate_docs.py`). Por eso el catálogo entero se construyó
para **no mover el contenido de la 23127**, y eso está verificado por script:
las 11 mutaciones compilan y las 11 dejan la 23127 intacta.

**Regla aplicada:** ni una muerte por `FileNotFoundError`, `NameError`,
`ImportError`, ni por el fallo de una prueba ajena al artefacto auditado cuenta
como veredicto. Se repara la cámara y se vuelve a medir.

> 📌 **I-3 es además un hallazgo sobre el repo, no solo sobre mi instrumentación:**
> la deuda `P2` (citas por número de línea) está **viva** y **muerde**: cualquier
> cambio que desplace una línea de `run_tests.py` pone la suite en rojo por una
> cita, aunque todo lo demás siga cierto. Es ruido (nombra fichero y línea), no
> un agujero — pero es la razón por la que un mutante hay que medirlo **con el
> motivo literal del rojo**, no con su código de salida.


---

## 1. Q4 — Las citas por número de línea movidas

**Método:** lectura con `ast` y comparación literal `HEAD~1` vs `HEAD` del contenido
de cada línea citada. **No** se ha usado el número que da el dev: se ha
comprobado **qué hay** en la línea nueva y **qué afirmación** sostiene.

### 1.1 Las seis citas que el dev movió dentro de `run_tests.py`

El desplazamiento real entre `HEAD~1` y `HEAD` en esa zona es **exactamente +20**
en las seis (comprobado: el contenido de la línea antigua y el de la nueva es
**idéntico**, byte a byte, en los seis casos).

| Cita | ¿Desplazamiento correcto? | ¿La línea citada sostiene la afirmación? | Veredicto |
|---|---|---|---|
| `run_tests.py:14787` (antes 14767) | ✅ +20 exacto, contenido idéntico | ❌ La línea dice `# --- (A) LA CAUSA, con el servicio REAL y disco temporal ---`. **No** es el test #4 ni una sobrescritura de `_patrones_de_categoria` | **FALSA** (de contenido) |
| `run_tests.py:14893` (antes 14873) | ✅ +20 exacto | ❌ Línea **en blanco**, dentro de `class _ServicioDeArranque` — y el docstring dice explícitamente *«no la clase: `_ServicioDeArranque` sobreescribe OTRAS dos cosas»* | **FALSA** (de contenido) |
| `run_tests.py:14920` (antes 14900) | ✅ +20 exacto | ❌ La línea es `def cget(self, key):` de `_EtiquetaFalsa_`. No es el test #7 | **FALSA** (de contenido) |
| `run_tests.py:23102` (antes 23082) | ✅ +20 exacto | ❌ La línea es `"TASK-080 y esta bloqueada por esa medicion:\n" + sin_comentarios)`. El docstring afirma que ahí hay uno de los *cuatro* sitios que **citan `sandbox-rules.md:55-56` por número**; esa línea no cita nada | **FALSA** (de contenido) |
| `run_tests.py:23125` (antes 23105) | ✅ +20 exacto | ✅ Es literalmente `assert min(posiciones) > 61, (` — el suelo de la 61 que el docstring dice que se comprueba ahí | **VIVA** |
| `run_tests.py:23127` (antes 23107) | ✅ +20 exacto | ✅ Es la línea que cita `sandbox-rules.md:55-56`; y el propio guard (`test_las_citas_de_sandbox_rules_siguen_siendo_ciertas`) **lee esa línea en caliente** y exige que mentione `55-56` → está verde en el baseline, o sea que la cita está verificada en runtime | **VIVA** |

**Sites reales** de la sobrescritura de `_patrones_de_categoria` (medidos con `ast`,
`Assign` sobre un `Attribute` de ese nombre): `run_tests.py:15760`, `:15787`,
`:15880`, `:15926`. Las tres citas de los tests #4/#6/#7 **no apuntan a ninguno**
de ellos.

### 1.2 Las dos citas de `validate_docs.py` que el dev reportó **sin tocar**

Estas citas viven **dentro de `validate_docs.py`** y apuntan a líneas de
`run_tests.py`:

| Cita (en `validate_docs.py`) | Qué afirma | Número real hoy | Estado |
|---|---|---|---|
| `validate_docs.py:1180` → `run_tests.py:13553` | «aparece DOS veces en `run_tests.py`, y la segunda (en `_run_tests_sintetico()`, `run_tests.py:13553`) está POR ENCIMA de `cuerpo_main`» | La segunda ocurrencia del marcador `"--- Running Headless UI Tests ---"` está en **`run_tests.py:14007`** (`_run_tests_sintetico()` arranca en 13989). `13553` dice hoy `shutil.rmtree(tmp, ignore_errors=True)` | **CADUCADA y FALSA.** El dev la movió a `13573` (que es un separador de comentario `# ---…`), pero **`13573` tampoco es la línea correcta**: el número real es `14007`. La cita ya era falsa antes del ciclo (en `HEAD~1` la ocurrencia estaba en `13987`, y la cita decía `13553`) |
| `validate_docs.py:1435` → `run_tests.py:11650` | «el guard de código muerto de `run_tests.py:11650` no la cazaba porque su alcance es `src/woptimizer/**`, no el tooling» | `11650` dice hoy `import threading`. La línea `11670` (= `11650 + 20`) dice `svc.detach_tray()`; el guard de código muerto que mira `src/woptimizer/**` es `test_la_verificacion_de_sintaxis_deriva_su_alcance_y_no_lo_enumera`, en `run_tests.py:28728` | **CADUCADA y FALSA.** El dev la movió a `11670`, que **tampoco** es el guard: es una llamada a `svc.detach_tray()` |

### 1.3 Resumen Q4

- **Vivas:** 2 de 8 → `run_tests.py:23125`, `run_tests.py:23127`.
- **Desplazamiento correcto pero afirmación FALSA:** 4 de 8 → `:14787`, `:14893`,
  `:14920`, `:23102`. El +20 es exacto y el contenido no ha cambiado: estas citas
  **ya Apuntaban a otra cosa antes del ciclo**. El dev las movió mecánicamente
  sin comprobar la afirmación.
- **CADUCADAS de número y falsas de contenido:** 2 de 8 → las de `validate_docs.py`
  (`:13553`, `:11650`). Reportadas por el dev, **no corregidas**. Y el número al
  que deberían apuntar no es el que el dev propone (`13573`/`11670`): son
  `14007` y el guard de `28728`.
- **Ninguna de las 8 está vigilada por un guard.** `validate_docs.py` solo
  comprueba el **número de tests** (`_recuento_de_tests`), no las citas por
  línea; y el guard de las citas de `sandbox-rules.md` solo mira las **cuatro**
  que él mismo lista (`validate_docs.py:1429`, `:1924`, `run_tests.py:23127`,
  `docs/ai/sandbox-rules.md:1133`). Las otras seis no las mira nadie.

---

## 2. Qué sonda mata a qué mutante (atribución medida)

Medido **sonda por sonda**, en la cámara B, importando el `run_tests.py` de la
cámara y llamando a cada sonda por separado (para no atribuir la muerte al
primer `assert` que se encuentre). El **veredicto oficial** de cada mutante es
el de la suite completa (§3).

| id | AC-1 (forma) | AC-2 (producto) | AC-3 (contraprueba) |
|---|---|---|---|
| **M-V1** | **MUERTO** | **MUERTO** | **MUERTO** |
| **M-V3** (derivado vacío) | VERDE | **MUERTO** | **MUERTO** |
| **M-V3b** (derivado fijo) | **MUERTO** | **MUERTO** | **MUERTO** |
| **M-V4** | **MUERTO** | **MUERTO** | *no aplica* (`NameError`: el helper ya no existe en el módulo) |
| **M-V5** (derivado = declaración) | VERDE | VERDE | **MUERTO** |
| **Q1** (sin las tres sondas) | VERDE | VERDE | VERDE |
| **Q2** (AC-1 con un solo guard) | VERDE | VERDE | VERDE |
| **Q2b** (AC-1 sin guards) | VERDE | VERDE | VERDE |
| **Q5** (tripwire 10 → 11) | VERDE | **MUERTO** | VERDE |

### 2.1 Motivos literales de cada muerte

| id | Sonda | Motivo literal de la muerte |
|---|---|---|
| **M-V1** | AC-1 | `el conjunto de vistas que vigilan los guards NO esta derivado del disco:` — en la **medición oficial** (§7.1) los delitos son «`run_tests.py:9422: una SEGUNDA copia del conjunto de vistas escrita a mano`» y «`run_tests.py:0: … no recorre el conjunto DERIVADO: la derivacion esta escrita y muerta`». (La atribución de esta tabla corrió con la **primera** versión de la mutación, que además añadía una copia con otro nombre: por eso aquí aparecen «ENUMERACION literal» y «SEGUNDA copia») |
| **M-V1** | AC-2 | `el rojo tiene que NOMBRAR la infraccion (y no un fallo cualquiera del subproceso)` — el rojo que sale es el de la comparación derivado↔declaración, no el de la infracción |
| **M-V1** | AC-3 | `el rojo tiene que venir de la comparacion entre el derivado y la declaracion, y no de un fallo cualquiera` |
| **M-V3** | AC-2 | `el rojo tiene que NOMBRAR la infraccion…` (el derivado vacío hace que el guard aborte antes de auditar) |
| **M-V3** | AC-3 | `el conjunto derivado no es el contenido del directorio de vistas: derivado=[] y disco=['dashboard_view.py', 'pack_manager_view.py', 'process_manager_view.py']. Un derivado fijo o vacio deja el guard mirando un conjunto que no existe` |
| **M-V3b** | AC-1 | `el conjunto de vistas que vigilan los guards NO esta derivado del disco:` («una SEGUNDA copia del conjunto de vistas escrita a mano») |
| **M-V4** | AC-1 | `el conjunto de vistas que vigilan los guards NO esta derivado del disco:` («`_vistas_del_disco` esta ANIDADO dentro de una funcion…» + «recorre una ENUMERACION literal» + «SEGUNDA copia») |
| **M-V5** | AC-3 | `el rojo tiene que venir de la comparacion entre el derivado y la declaracion, y no de un fallo cualquiera` — con la derivación falsa, el guard **no** muere por la comparación (que es tautológica) sino por `FileNotFoundError` al abrir ficheros que no existen en la cámara vaciada |
| **Q5** | AC-2 | `el rojo tiene que NOMBRAR la infraccion (y no un fallo cualquiera del subproceso)` — el rojo que sale es el del **tripwire**, no el de la infracción |

### 2.2 Lo que la atribución ya dice (antes del veredicto oficial)

> ⚠️ Esta tabla es la **ATRIBUCIÓN** (qué sonda mata a qué mutante, medida
> sonda a sonda). Los **motivos literales de la muerte por suite completa** están
> en §7.1, y no siempre coinciden palabra por palabra: la atribución corrió con
> la primera versión de M-V1 (ver §0.3, I-3).

- **M-V1 y M-V4 mueren por AC-1 y por AC-2**: el contrato queda respaldado en sus
  dos vías declaradas. (Verificado por suite completa para AC-1; AC-2 medido
  por atribución.)
- **M-V3 (derivado vacío) NO lo mata AC-1**: AC-1 mira la *forma* (que el `for`
  recorra algo que llega al helper), no el *resultado* de la derivación. Lo mata
  AC-3, con un motivo que nombra el disco y el derivado vacío.
- **M-V5 (el quinto mutante, propio) NO lo matan AC-1 ni AC-2**: ver §4. Es el
  hueco real que el contrato no declaraba.

---

## 3. Las tres preguntas con dato

### 3.1 Q1 — ¿Las tres sondas están vigiladas? **NO. NADA se entera.**

Medido en la cámara B con las tres invocaciones **borradas** de `__main__`:

```
SANO  (con las 3 sondas)   definidos=231 invocados=231 huerfanos=ninguno
   sondas invocadas desde __main__: [_guard_de_forma_del_conjunto_de_vistas,
                                   _producto_el_guard_de_workers_audita_una_vista_nueva,
                                   _contraprueba_el_derivado_de_vistas_es_el_disco]
MUTADO (sin las 3 sondas)  definidos=231 invocados=231 huerfanos=ninguno
   sondas invocadas desde __main__: []
```

Y el validador, **con las tres sondas borradas**:

```
exit code: 0
[OK]   run_tests.py: 231 tests definidos = 231 invocados (derivado con ast)
Resumen: 156 OK, 0 FAIL, 0 SKIP
```

**Por qué:** `validate_docs.py:_recuento_de_tests` deriva `defined` de las
funciones de módulo que empiezan por `test_` e `invoked` de las llamadas a
`test_*` dentro de `__main__` (`validate_docs.py:58-80`). Las tres sondas son
`_`-prefijadas: **no entran ni en la una cifra ni en la otra**. El recuento no
baja (231 → 231) y el validador sale con **0 FAIL**.

**Y por suite COMPLETA (no solo por validador):** con las tres invocaciones
borradas, la suite entera da

```
[suite_Q1] rc=0  bytes=29999  lineas=395  segundos=809.9
ULTIMA LINEA: 'ALL TESTS PASSED.'
```

Frente al baseline (`rc=0, bytes=30466, lineas=398`), la diferencia son
**exactamente las 3 líneas** que imprimen las tres sondas. Es decir: **las tres
sondas desaparecen del log y la suite sigue en verde**.

**Veredicto:** las tres sondas son **un contador que nadie lee** — la clase A11
que este repo ya pagó. Borrarlas (o dejar de invocarlas) **no lo nota nadie**:
ni la suite, ni el validador, ni el recuento que declaran `STATUS.md`,
`AGENTS.md`, `README.md` y `docs/ai/testing-guide.md`. El guard de forma AC-1,
la prueba de producto AC-2 y la contraprueba AC-3 **dependen de que alguien se
 acuerde de llamarlas**, y nada lo comprueba.

> ⚠️ Esto **no** es un agujero en el *fix* (el fix es correcto y está medido),
> es un agujero en la **vigilancia del fix**: el ciclo 68 deja tres guards
> capaces de apagarse solos, igual que el guard de AC-5 antes de TASK-081.

**Coste medido de las tres sondas** (cámara C, ficha y subprocess incluidos):

| sonda | segundos |
|---|---|
| `_guard_de_forma_del_conjunto_de_vistas` (AC-1) | **8,84 s** |
| `_producto_el_guard_de_workers_audita_una_vista_nueva` (AC-2) | **5,40 s** |
| `_contraprueba_el_derivado_de_vistas_es_el_disco` (AC-3) | **4,77 s** |

O sea: **≈ 19 s** (≈ 15 s si el `import` del módulo se paga una vez). Vigilar las
tres sondas **no es caro**: el problema de A-C68-1 no es el coste, es que nadie
las vigila. La suite completa tarda **747 s**, así que las tres sondas son el
~2,5 % del tiempo.

### 3.2 Q2 — ¿El guard de forma AC-1 es vaciable? **SÍ.**

El conjunto de sujetos de AC-1 son **dos nombres escritos a mano**:

```python
for nombre_guard in (_GUARD_DE_WORKERS, _GUARD_HERMANO):   # run_tests.py:29333
```

Medido:

| Mutación | AC-1 | Motivo |
|---|---|---|
| **Q2**: deja de mirar el guard hermano (`_GUARD_HERMANO`) | **VERDE** | El detector sigue intacto; lo que se apaga es **uno de los dos guards vigilados** |
| **Q2b**: no mira **ningún** guard (`for nombre_guard in ():`) | **VERDE** | El bucle no se ejecuta y no queda ningún delito |

**Veredicto:** AC-1 es **vaciable**, exactamente como lo era el alcance de AC-5
antes de TASK-081 (propuesta §3.4, «el #2 del ranking»). Su alcance —el conjunto
de guards que vigila— está escrito como una enumeración literal, y **AC-1 no es
la excepción**: el propio guard de forma del ciclo 68 tiene el mismo defecto que
cierra. **No es un problema de seguridad ni de datos** (vigilancia de tooling), y
el defecto **no impide** que AC-1 detecte la enumerated-literal del conjunto de
vistas (eso sí está medido y funciona: M-V1 y M-V4 mueren por él). Es deuda de
vigilancia, con su propio ciclo, como el #2 del ranking.

**Y por suite COMPLETA:**

```
[suite_Q2] rc=0  bytes=30616  lineas=402  segundos=816.6
ULTIMA LINEA: 'ALL TESTS PASSED.'
```

Reducir el alcance de AC-1 a **un** guard (dejar de vigilar el hermano) deja la
suite entera **en verde**. El log tiene **más** líneas que el baseline (402 vs
398) porque el mensaje de AC-1 ya no enumera dos guards.

### 3.3 Q3 — ¿La derivación es la fuente de verdad de verdad? **NO: es falsable.**

Medido con **M-V5** (mutante propio): `_vistas_del_disco()` deja de derivar y
devuelve `set(VISTAS_DECLARADAS)`.

- El helper **sigue estando en ámbito de módulo** y **sigue llamándose** desde el
  guard → **AC-1 lo da por bueno** (VERDE): el detector de forma ve una llamada al
  helper y no puede saber qué devuelve.
- La comparación `set(VISTAS_DECLARADAS) == vistas_en_disco` se vuelve
  **tautológica**: compara la declaración consigo misma → **el rojo que nombra
  una vista nueva desaparece**.
- **AC-2 tampoco lo ve** (VERDE): en la cámara de producto la declaración se
  parchea con la vista nueva, el helper devuelve la declaración parcheada y la
  vista nueva se audita igual → el guard sigue dando rojo por la infracción.
- **AC-3 sí lo ve** (MUERTO): al vaciar el directorio de vistas de la cámara, el
  guard deja de morir por la comparación y muere por `FileNotFoundError` al
  abrir ficheros que ya no existen → la aserción «el rojo tiene que venir de la
  comparacion entre el derivado y la declaracion, y no de un fallo cualquiera»
  lo detecta.

**Veredicto:** hay **una sola** declaración del conjunto de vistas
(`VISTAS_DECLARADAS`, `run_tests.py:29124`) — no hay una quinta copia escondida
en el texto. Lo que hay es una **derivación falsable**: la forma del helper
(parece derivado) no ata su **resultado** al disco, y solo AC-3 ata el
resultado. Un `return set(VISTAS_DECLARADAS)` (o `return VISTAS_DECLARADAS`)
dentro del helper deja el guard de forma y el de producto **intactos**.

### 3.4 Q5 — El tripwire `== 10`: avisa, pero el mensaje se contradice

Medido con la cifra desfasada (`assert contados_en_codigo == 11`, número real 10):

```
SANO   (tripwire == 10, el numero real es 10):
  VERDE: "guarda AST exhaustiva: 10 cuerpos de hilo secundario, 10 publicaciones vigiladas"
DESPASADO (tripwire == 11, el numero real sigue siendo 10):
  ROJO (AssertionError). MENSAJE LITERAL:
   > las vistas del disco tienen 10 publicaciones a una puerta autorizada y el
     invariante de TASK-073 habla de 10 call sites migrados. O se movio una
     publicacion, o esta cifra esta desfasada: decidalo explicitamente en vez
     de dejar que el guard se adapte solo.
```

**Veredicto:** el tripwire **no rompe de forma opaca**: muere por `AssertionError`
con un mensaje que dice qué hacer («decídelo explícitamente en vez de dejar que
el guard se adapte solo»). ✅

⚠️ **Pero el mensaje se contradice a sí mismo en cuanto alguien cambia la
cifra**: el texto del mensaje lleva el número esperado **escrito a mano**
(`habla de 10 call sites migrados`), mientras que la aserción compara con
**otro** (`== 11`). El humano lee *«10 publicaciones … habla de 10 call sites»* y
no ve el problema: el mensaje **no dice qué cifra se comparó**. Es la clase
«cifra escrita a mano» (deuda `D2`/`D3`/`P2` de `STATUS.md`), reintroducida en
el guard que este ciclo toca.

Efecto colateral medido: la sonda de producto **AC-2 muere** cuando la cifra se
desfasa, porque exige que el rojo nombre la *infracción* y el rojo que sale es
el del tripwire. O sea: el tripwire está vigilado **por la sonda de producto**, no
por un guard propio.

---

## 4. M-V5 — el quinto mutante, propio: **la derivación es falsable**

> El contrato declara cuatro mutantes. Este es el **quinto camino** por el que el
> fix se deshace, y el padre lo pidió explícitamente: *«una derivación que se
> puede falsear»*.

**La mutación** (una sola línea, el fallo que un developer real cometería):

```python
 def _vistas_del_disco(directorio=None):
     ...
-    import glob as _glob
-    if directorio is None:
-        directorio = _directorio_de_vistas()
-    encontradas = {os.path.basename(p)
-                   for p in _glob.glob(os.path.join(directorio, "*.py"))}
-    encontradas.discard("__init__.py")
-    return encontradas
+    return set(VISTAS_DECLARADAS)
```

El helper **sigue en ámbito de módulo** y **sigue llamándose** desde el guard:
la *forma* es idéntica a la correcta. Lo que cambia es el **resultado**: la
derivación ya no mira el disco, devuelve la declaración.

**Lo que se pierde, MEDIDO (escena M-V2: vista nueva en disco, declaración sin
actualizar):**

| | rc | ¿ROJO? | ¿nombra la vista nueva? | ¿la vista nueva se audita? |
|---|---|---|---|---|
| **Sano** | 1 | ✅ | ✅ `['vista_nueva_de_la_camara.py']` | — (el rojo es el de la comparación) |
| **M-V5** | **0** | ❌ **VERDE** | ❌ | ❌ **no se audita** |

Es decir: **M-V5 se come exactamente el «rojo que nombra la vista nueva»** que el
contrato (§6.2) exige, **y además deja la vista nueva sin auditar**. La
comparación `set(VISTAS_DECLARADAS) == vistas_en_disco` se vuelve **tautológica**
(compara la declaración consigo misma).

**Quién lo ve y quién no:**

| Sonda | Veredicto | Motivo |
|---|---|---|
| **AC-1** (forma) | **VERDE** ❌ | El detector comprueba que el `for` *llegue* al helper y que el helper esté en módulo. No comprueba **qué devuelve**. Un `return set(VISTAS_DECLARADAS)` es indistinguible de una derivación para un detector de forma |
| **AC-2** (producto) | **VERDE** ❌ | En la cámara de producto la declaración **se parchea** con la vista nueva, el helper devuelve la declaración parcheada → la vista nueva se audita igual → el guard da rojo por la infracción y AC-2 lo acepta |
| **AC-3** (contraprueba) | **MUERTO** ✅ | Al vaciar el directorio de vistas de la cámara, el guard deja de morir por la comparación (tautológica) y muere por `FileNotFoundError`; la aserción «el rojo tiene que venir de la comparacion entre el derivado y la declaracion, y no de un fallo cualquiera» lo detecta |

**Clasificación honesta:** M-V5 **no sobrevive a la suite completa** (AC-3 lo
mata), así que **no es un superviviente**. Pero **la muerte es por efecto
colateral**, no por una comprobación dirigida: la única red que lo caza es una
aserción de *subcadena* sobre el texto de un `FileNotFoundError`. Los dos guards
que el contrato declara como matadores de la clase «literal en vez de derivado»
(AC-1 y AC-2) **no lo ven**.

**Lo que esto deja dicho sobre el fix (no sobre los tests):**

1. La derivación del **conjunto** está atada al disco **solo en el resultado de
   AC-3**, no en la forma (AC-1) ni en el producto (AC-2).
2. Una forma de cerrar el hueco: que AC-3 compare el derivado contra
   `os.listdir` **de un directorio que el test elija**, y que ese test lo elija
   **distinto** del de la declaración — o que el derivado se compare contra
   `os.listdir` **después** de cambiar el directorio, de modo que un `return`
   fijo no pueda igualarlo por casualidad. (Esto lo arregla `openspec-dev`, no
   este informe.)

---

## 5. Dos mutantes extra del DIRECTORIO (no los declaraba el contrato)

Se buscan porque el fix también toca **de dónde** se deriva el directorio.

| id | Qué rompe | AC-1 | AC-2 | AC-3 | Veredicto |
|---|---|---|---|---|---|
| **M-V6** | `_directorio_de_vistas()` se ancla a una ruta **fija** (`C:\Users\carch\...\woptimizer\src\woptimizer\ui\views`) en vez de derivarse de `Path(__file__)` | VERDE | **MUERTO** | **MUERTO** | **MUERTO** — AC-2: la cámara de producto deja de medir («el rojo tiene que NOMBRAR la infraccion»); AC-3: «con el directorio de vistas VACIO el guard tiene que dar ROJO y dio 0» |
| **M-V7** | el directorio es el **equivocado** (`ui/` en vez de `ui/views/`) | VERDE | **MUERTO** | VERDE | **MUERTO** — por AC-2 (`logs/suite_M-V7.log`: `rc=1`, 19 799 B, 236 líneas, 777,7 s; `AssertionError: el rojo tiene que NOMBRAR la infraccion (y no un fallo cualquiera del subproceso)`, con AC-1 **pasando** antes: `guard de forma del conjunto de vistas OK`) |

> ⚠️ **M-V6**: su veredicto oficial es el de la **suite completa** (ver §7.1).
> **M-V7** tiene suite completa. Los dos eran, además, mutantes **extra** que el
> contrato no declaraba (§4 del encargo: «búscalos tú»).

---

## 6. Hallazgos con nombre (re-auditables en tres ciclos)

Cada hallazgo lleva un identificador corto propio, para que no se pierda.

| id | Hallazgo | Dónde | Severidad |
|---|---|---|---|
| **A-C68-1** | Las **tres sondas no están vigiladas**: son funciones `_`-prefijadas que solo se invocan desde `__main__`. `validate_docs.py` solo cuenta `test_*`, así que **borrarlas no baja ningún recuento y no rompe nada** (`231 = 231`, validador `156 OK / 0 FAIL / 0 SKIP`). Es un **contador que nadie lee** | `run_tests.py:30014-30016` + `validate_docs.py:58-80` | Vigilancia de tooling |
| **A-C68-2** | El guard de forma **AC-1 es vaciable**: su conjunto de sujetos es la enumeración literal `(_GUARD_DE_WORKERS, _GUARD_HERMANO)` (`run_tests.py:29333`). Reducirlo a un guard → VERDE; a **cero** guards → VERDE. Es la **misma clase** que el alcance de AC-5 que el ciclo 67 cerró en `verify_ui_syntax.py`, y la **misma** que la propuesta de este ciclo (§3.4) declara como «el #2 del ranking» | `run_tests.py:29333` | Vigilancia de tooling |
| **A-C68-3** | La **derivación es falsable**: `_vistas_del_disco()` puede devolver la declaración en vez del disco. **AC-1 y AC-2 no lo ven**; solo AC-3, y **por efecto colateral** (un `FileNotFoundError` en una cámara vaciada). Con esa mutación, el guard **deja de nombrar la vista nueva y deja de auditarla** | `run_tests.py:29147-29165` | Vigilancia de tooling (con efecto sobre la garantía de §6.2) |
| **A-C68-4** | **S7 replicado.** `STATUS.md` ya declara (CYCLE-067): *«la guarda AC-1 declara en su docstring que mata `M-R`, y MEDIDO lo pasa: un `rglob` muerto sobrevive a AC-1. Solo AC-3 lo caza, por producto. […] su propia documentación miente»*. El AC-1 **nuevo** de este ciclo repite el patrón: su docstring dice *«lo que recorre es el DERIVADO»* y M-V5 demuestra que puede recorrer la declaración. **El ciclo cierra una enumerated-literal y abre otra en el guard que la cierra** | `run_tests.py:29354` (docstring de AC-1) + `STATUS.md` S7 | Vigilancia de tooling |
| **A-C68-5** | **6 de las 8 citas por número de línea** que este ciclo mueve **no sostienen la afirmación** que dicen sostener; 2 de ellas (las de `validate_docs.py`) están **caducadas de número** y el dev las reportó sin corregir. **Ninguna de las 8 la vigila un guard** | §1 de este informe | Deuda documental (`P2`, ya declarada) |
| **A-C68-6** | El mensaje del **tripwire `== 10`** lleva la cifra esperada **escrita a mano** (`habla de 10 call sites migrados`) mientras la aserción compara con otro número. Con la cifra desfasada, el mensaje dice *«10 publicaciones … habla de 10 call sites»* y **no dice qué cifra se comparó**: se contradice a sí mismo. Es la clase `D2`/`D3`/`P2` reintroducida en el guard que este ciclo toca | `run_tests.py:9436-9441` | Deuda baja (cifra escrita a mano) |

### 6.1 Lo que SÍ está cerrado y medido

- El **conjunto de vistas que abre el guard de workers es el derivado del disco**: la
  vista nueva en disco **se audita aunque nadie la apunte** (medido por producto:
  AC-2 con control positivo).
- La **declaración es única** (`VISTAS_DECLARADAS`, `run_tests.py:29124`) y se
  **compara** con el derivado: una vista nueva da **rojo que la nombra** (medido).
- El helper está **en ámbito de módulo** y los **dos guards** lo usan.
- `RUTAS_VIGILADAS` conserva solo la **excepción** (`confirmation.py`) y `ESPERADOS`
  sale de la declaración.
- La **cámara del producto** corre el guard **como el producto** (subproceso que
  importa el `run_tests.py` copiado), no sobre su texto.

---

## 7. Veredictos oficiales (suite COMPLETA, un mutante por vez)

**Regla de aceptación de un log:** `rc=0` + `ALL TESTS PASSED.` en la última
línea → **superviviente**; `AssertionError` **con traceback** → **muerto**; otra
cosa → **no medido** (y se vuelve a medir). El tamaño y la última línea de cada
log se comproban antes de aceptarlo.

### 7.1 Tabla completa (11 mutaciones de código + 1 escenario + baseline)

| id | Qué rompe | Log | rc | bytes | líneas | s | Veredicto | Motivo literal |
|---|---|---|---:|---:|---:|---:|---|---|
| — | **BASELINE** (fichero sano) | `logs/baseline.log` | 0 | 30 466 | 398 | 747,1 | **VERDE** | `ALL TESTS PASSED.` — y las tres sondas imprimen su OK |
| **M-V1** | la literal vuelve a ser la fuente | `logs/suite_M-V1.log` | 1 | 18 461 | 238 | 787,8 | **MUERTO** | `AssertionError: el conjunto de vistas que vigilan los guards NO esta derivado del disco:` → `run_tests.py:9422: una SEGUNDA copia del conjunto de vistas escrita a mano` + `run_tests.py:0: 'test_los_workers_de_pack_solo_publican_por_after' no recorre el conjunto DERIVADO: la derivacion esta escrita y muerta` (muerte de **AC-1**, y el guard de citas pasó: `test_las_citas_de_sandbox_rules_siguen_siendo_ciertas OK.`) |
| **M-V3** | la derivación devuelve un conjunto **vacío** | `logs/suite_M-V3.log` | 1 | 19 557 | 236 | 750,0 | **MUERTO** | `AssertionError: el rojo tiene que NOMBRAR la infraccion (y no un fallo cualquiera del subproceso)` — muerte de **AC-2** (`run_tests.py:30015`). El subproceso del guard murió con `el conjunto de vistas que este guard audita no es el que hay en el disco: en el directorio de vistas hay []`. **AC-1 pasó** (`guard de forma del conjunto de vistas OK`): el detector de forma no ve el *resultado* de la derivación, solo su forma |
| **M-V3b** | la derivación devuelve una lista **fija** | `logs/suite_M-V3b.log` | 1 | 18 325 | 237 | 796,7 | **MUERTO** | `AssertionError: el conjunto de vistas que vigilan los guards NO esta derivado del disco:` → `run_tests.py:29159: una SEGUNDA copia del conjunto de vistas escrita a mano` (muerte de **AC-1**) |
| **M-V4** | el helper **no** se hoista y la copia a mano vuelve | `logs/suite_M-V4.log` | 1 | 18 608 | 239 | 774,8 | **MUERTO** | `AssertionError: el conjunto de vistas que vigilan los guards NO esta derivado del disco:` → **tres** delitos: `run_tests.py:27687: '_vistas_del_disco' esta ANIDADO dentro de una funcion: el otro guard no lo puede reutilizar y la copia a mano vuelve` + `run_tests.py:9422: una SEGUNDA copia del conjunto de vistas escrita a mano` + `run_tests.py:0: 'test_los_workers_de_pack_solo_publican_por_after' no recorre el conjunto DERIVADO` (muerte de **AC-1**) |
| **M-V5** | la derivación devuelve la **declaración** (comparación tautológica) — *mutante propio* | `logs/suite_M-V5.log` | 1 | 19 841 | 237 | 803,9 | **MUERTO** | `AssertionError: el rojo tiene que venir de la comparacion entre el derivado y la declaracion, y no de un fallo cualquiera` (muerte de **AC-3**). **AC-2 PASÓ** (`producto del guard de workers OK`) y **AC-1 pasó**: los dos guards que el contrato declara como matadores de la clase «literal en vez de derivado» **no lo ven** |
| **Q1** | se borran las tres invocaciones de las sondas | `logs/suite_Q1.log` | **0** | 29 999 | 395 | 809,9 | **SUPERVIVIENTE** | `ALL TESTS PASSED.` — las 3 líneas de las sondas desaparecen del log y nada se entera |
| **M-V7** | el directorio de vistas es el **equivocado** (`ui/` en vez de `ui/views/`) — *mutante propio* | `logs/suite_M-V7.log` | 1 | 19 799 | 236 | 777,7 | **MUERTO** | `AssertionError: el rojo tiene que NOMBRAR la infraccion (y no un fallo cualquiera del subproceso)` (muerte de **AC-2**, `run_tests.py:30015`); AC-1 pasó antes (`guard de forma del conjunto de vistas OK`) |
| **Q2** | AC-1 deja de mirar el guard hermano | `logs/suite_Q2.log` | **0** | 30 616 | 402 | 816,6 | **SUPERVIVIENTE** | `ALL TESTS PASSED.` |
| **Q2b** | AC-1 no mira **ningún** guard | `logs/suite_Q2b.log` | **0** | 30 466 | 398 | 850,7 | **SUPERVIVIENTE** | `ALL TESTS PASSED.` — log **idéntico** al baseline en tamaño y líneas: el guard de forma puede vaciarse por completo y nadie se entera |
| **M-V6** | el directorio de vistas se ancla a una ruta **fija** (deja de derivarse de `__file__`) — *mutante propio* | `logs/suite_M-V6.log` | 1 | 19 559 | 236 | 788,8 | **MUERTO** | `AssertionError: el rojo tiene que NOMBRAR la infraccion (y no un fallo cualquiera del subproceso)` (muerte de **AC-2**, `run_tests.py:30013`); AC-1 pasó antes |
| **Q5** | el tripwire `== 10` pasa a `== 11` | `logs/suite_Q5.log` | 1 | 19 285 | 236 | 785,7 | **MUERTO** | `AssertionError: el rojo tiene que NOMBRAR la infraccion (y no un fallo cualquiera del subproceso)` (muerte de **AC-2**): con la cifra desfasada, el rojo que sale es el del **tripwire**, no el de la infracción, y AC-2 lo detecta |

### 7.2 M-V2 — el escenario EQUIVALENTE (no es una mutación de código)

Escena: una vista **nueva** en disco y la **declaración sin actualizar**
(equivalente a lo que le pasa a un dev que añade una vista y no la declara).
Medido con el guard **como el producto** (subproceso sobre la cámara):

```
rc: 1
AssertionError: el conjunto de vistas que este guard audita no es el que hay en el disco:
  en el directorio de vistas hay ['dashboard_view.py', 'pack_manager_view.py',
  'process_manager_view.py', 'vista_nueva_de_la_camara.py'] y la declaracion es
  ['dashboard_view.py', 'pack_manager_view.py', 'process_manager_view.py'];
  la diferencia es ['vista_nueva_de_la_camara.py']. Actualiza la DECLARACION
  (no el guard): una vista nueva nace con la deuda de `self.after` a mano y
  tiene que quedar declarada.

ROJO (rc != 0): True
NOMBRA LA VISTA NUEVA: True
ES UNA ASERCION (no una excepcion): True
TRAZA: True   <- es la traza del AssertionError, NO un FileNotFoundError
```

**Veredicto: EQUIVALENTE (ruido útil).** El rojo es **una aserción** (no una
excepción), **nombra la vista** y **nombra el directorio**. Es exactamente el
aviso que el contrato pide; su «supervivencia» **no es un fallo**.

*(las filas siguientes se añaden al terminar cada suite; el barrido oficial corre
en dos cámaras en paralelo: A = mutantes del fix + Q5, B = supervivientes)*

---

## 8. Veredicto global

### 8.1 Los dos veredictos, separados

| | Veredicto | Por qué |
|---|---|---|
| **El fix de TASK-082** (el conjunto de vistas se deriva) | **PASS** | Los **7** mutantes del fix —los 4 declarados (M-V1, M-V2, M-V3, M-V4) más el propio M-V5 y los dos extras del directorio (M-V6, M-V7)— **mueren todos por su aserción**, con el motivo literal medido. La vista nueva en disco se audita aunque nadie la apunte (medido por producto, con control positivo) |
| **La vigilancia de ese fix** | **FAIL** | **3 supervivientes** medidos por suite completa: **Q1** (las tres sondas se pueden borrar sin que nada se entere), **Q2** y **Q2b** (el guard de forma AC-1 se puede dejar mirando un guard o **ninguno**, y la suite sigue en verde) |

### 8.2 Veredicto: **FAIL** (de vigilancia, no del fix)

**Motivo, con las cifras:** de las **11** mutaciones de código medidas por suite
completa, **8 mueren** (M-V1, M-V3, M-V3b, M-V4, M-V5, M-V6, M-V7 y Q5) y **3
sobreviven** (Q1, Q2, Q2b). M-V2 no es una mutación de código sino un
**escenario**, y sale **EQUIVALENTE** (§7.2). La regla del repo es
*«PASS = toda mutación muere por su aserción; FAIL = sobrevive alguna»*, luego
el veredicto es **FAIL**.

**Matiz que decide qué hacer con él:** los tres supervivientes **no tocan
seguridad ni datos** del producto. El guard de workers sigue en pie y sigue
auditando las tres vistas del disco; lo que se puede apagar es **la vigilancia
de la vigilancia**. Por la regla del repo (*«un superviviente en seguridad o
datos se arregla, no se documenta»*), estos tres **se documentan como tickets con
nombre** y **no bloquean el cierre del fix**:

- **A-C68-1** → que las tres sondas estén vigiladas (o que el recuento las
  cuente). El coste medido es **≈ 19 s** de suite (2,5 % de los 747 s).
- **A-C68-2** → el alcance de AC-1 no puede ser una enumeración literal
  (el #2 del ranking de la propia propuesta, aplicado ahora al guard nuevo).
- **A-C68-3** → la derivación tiene que atar su **resultado** al disco, no solo
  su forma (M-V5).

### 8.3 Lo que NO es un fallo (para que no se arregle lo que no está roto)

- **M-V2 es EQUIVALENTE, no un fallo.** Verificado: con una vista nueva en
  disco y la declaración sin actualizar, el guard da **rojo por aserción**
  (`AssertionError`, no `FileNotFoundError`) y el rojo **nombra la vista**
  (`['vista_nueva_de_la_camara.py']`) **y el fichero**. Su supervivencia **no**
  es un defecto: es el aviso que el contrato pide.
- **Los 7 mutantes del fix no se tocan.** El arreglo de TASK-082 está cerrado y
  medido.

---

## 9. Cierre

### 9.1 Estado del repo real — MEDIDO al terminar

```
git rev-parse HEAD               -> f8bc8679c14e69a6471778cfd1474f8cfed8de91
git rev-parse --abbrev-ref HEAD  -> beta
git rev-parse --git-dir          -> C:\Users\carch\AppData\Local\woptimizer_git\.git
git log --oneline -1             -> f8bc867 fix(tools): el conjunto de vistas del guard de workers se deriva (TASK-082)
reflog: 308 entradas   (reflog[0] = f8bc867, el MISMO que al empezar)
git diff --stat                   -> (vacio)
git diff --cached --stat          -> (vacio)
git diff HEAD -- src/             -> (VACIO: cero ediciones bajo src/woptimizer)
git status --porcelain:
    ?? openspec/changes/2026-10-21-vistas-del-guard-de-workers-derivadas/mutation-report.md
```

**El repositorio real NO ha sido tocado.** Lo único en el árbol es **este
informe**, que es el entregable pedido. **No se ha hecho ningún commit**
(`git diff --cached --stat` vacío, reflog con las mismas 308 entradas que al
empezar). La cámara nunca tuvo el `.git` del repo real (verificado antes de
mutar nada) y sus repos son **desechables** (`git init` propio, rama `beta`,
un commit).

### 9.2 Ficheros creados por esta auditoría (todo en `%TEMP%`, para limpiar)

**Directorio raíz: `%TEMP%\wopt_c68_aud\`**

| Qué | Ficheros |
|---|---|
| **Cámaras desechables** | `camara_20261021_223501\` (suite), `camara_b_20261021_225308\`, `camara_c_20261021_233629\` (14 MB cada una, con su `.git` propio) |
| **Repos desechables** | `gitdesechable_223501\`, `gitdesechable_20261021_223501\` |
| **Logs** | `logs\baseline.log` (+`.meta`), `logs\suite_M-V1.log`, `suite_M-V3.log`, `suite_M-V3b.log`, `suite_M-V4.log`, `suite_M-V5.log`, `suite_M-V6.log`, `suite_M-V7.log`, `suite_Q1.log`, `suite_Q2.log`, `suite_Q2b.log`, `suite_Q5.log`, `suite_cierre_verde.log` (cada uno con su `.meta`), y `suite_M-V1_v1_INVALIDA.log` (la primera versión de M-V1, **no** es un veredicto) |
| **Resúmenes** | `logs\resumen_barrido_501.json`, `logs\resumen_barrido_308.json` |
| **Guiones** | `copiar_camara.py`, `verificar_aislamiento.py`, `crear_camara.py`, `montar_repo_desechable.py`, `restaurar_A.py`, `restaurar_c.py`, `restaurar_todas.py`, `runner.py`, `mutaciones.py`, `verificar_catalogo.py`, `barrido_rapido.py`, `barrido_completo.py`, `sonda.py`, `m2_camara.py`, `m5_m2.py`, `m6_m7.py`, `q1_validador.py`, `q5_tripwire.py`, `q4_citas.py`, `q4_citas2.py`, `crono_sondas.py`, `esperar.py`, `cierre.py` |
| **Rutas** | `camara_path.txt`, `camara_b_path.txt`, `camara_c_path.txt` |
| **Otros** | `__pycache__\` (de los guiones) |

**Fuera del directorio anterior, también mío:** `%TEMP%\wopt_c68_diff.txt` (el
diff de `f8bc867` sobre `run_tests.py`).

> ⚠️ **No borrar** los demás `wopt_c68_*` de `%TEMP%` (`wopt_c68_cam*`,
> `wopt_c68_e1a*`, `wopt_c68_e1b*`, `wopt_c68_e1c*`, `wopt_c68_e2*`, `wopt_c68_e3*`,
> `wopt_c68_scan\`, `wopt_c68_baseline.txt`, `wopt_c68_run1..4.txt`): son de la
> **cámara del arquitecto**, no de esta auditoría.

### 9.3 La copia quedó restaurada y verde — MEDIDO

La cámara A, **restaurada al fichero sano** (copia literal del `run_tests.py` de
HEAD, `__pycache__` purgado), da:

```
[cierre_verde] rc=0  bytes=30466  lineas=398  segundos=753.1
ULTIMA LINEA: 'ALL TESTS PASSED.'
```

Idéntica al baseline en `rc`, bytes y líneas: **la cámara queda verde** después de
haber pasado por los 11 mutantes.

### 9.4 Lo que queda para el siguiente ciclo (tickets, no notas)

| id | Qué hay que arreglar | Coste medido |
|---|---|---|
| **A-C68-1** | Que las tres sondas estén **vigiladas** (hoy son `_`-prefijadas y el recuento de tests no las ve) | ≈ 19 s de suite (2,5 %) |
| **A-C68-2** | Que el alcance de AC-1 no sea una enumeración literal (`_GUARD_DE_WORKERS`, `_GUARD_HERMANO`) | el propio detector lo puede derivar |
| **A-C68-3** | Que la derivación ate su **resultado** al disco y no solo su forma (para que un `return set(VISTAS_DECLARADAS)` no pueda colarse) | — |
| **A-C68-5** | Las 6 citas por número de línea que no sostienen su afirmación (deuda `P2`) | — |
| **A-C68-6** | El mensaje del tripwire lleva la cifra esperada **escrita a mano** | — |
| **S7 (ya declarado)** | El docstring de AC-1 afirma una garantía que el detector no tiene — **y este ciclo lo replica** | — |

---

---

# PARTE 2 -- Re-auditoria de la REPARACION de la vigilancia (ciclo 68, ronda 2)

**Que se audita.** El commit `73b2393` ("fix(tools): la vigilancia del guard de
vistas deja de ser vaciable (TASK-082)") contra el fix original `f8bc867`.
La PARTE 1 (618 lineas) dio el fix **PASS** y la vigilancia **FAIL** con tres
supervivientes (Q1, Q2, Q2b). Esta PARTE 2 mide si la reparacion los mata, si
no ha roto el fix, y si la vigilancia sigue siendo vaciable por otra via.

**Todo lo de aqui es MEDIDO.** Las cifras salen de `ast`, de la suite completa
en camara o de sondas in-process; ninguna sale de leer lo que dice el dev.

## A. Camara, protocolo y control de instrumento

| control | como | resultado |
|---|---|---|
| Copia sin el `.git` del repo real | `shutil.copytree(ignore_patterns(".git"))` -- `ignore_patterns` cubre ficheros Y directorios, que es lo que hace falta aqui: **en este repo `.git` es un FICHERO de 57 B**, no un directorio | la camara NO trae `.git` (control A, antes de `git init`) |
| Aislamiento | `git rev-parse --git-dir` en la camara SIN `GIT_DIR` | devuelve `<camara>/.git`, NUNCA `woptimizer_git` |
| `GIT_DIR` desechable | `git init` propio por camara | control C: devuelve el `GIT_DIR` desechable |
| Anti-contaminacion | `git_safe_commit.py` NO se invoca desde `%TEMP%` en ningun momento | 0 commits |
| Ancla del repo real | `git rev-parse HEAD` antes y despues | `73b2393` en los dos momentos |

**Control de instrumento (el que rompio la ronda anterior).** El guard de citas
lee en caliente `run_tests.py:23133` y `validate_docs.py:1429`. Toda mutacion
pasa por un comprobador que **rechaza** el mutante si el CONTENIDO de esas dos
lineas cambia:

```
mutante aplicado: <id> | sin desplazamiento de 23133/1429 | __pycache__ purgado
```

Mutaciones que habrian desplazado esas lineas: **0 aplicadas**. Cuando el
cambio era inevitable (M-V4 anida el helper), se hizo **despues** de la linea
23133, que es lo que permite que el desplazamiento sea cero.

**Medicion por suite COMPLETA**, no sonda por sonda: `rc=0` + `ALL TESTS PASSED.`
en la ULTIMA linea = SUPERVIVIENTE; `AssertionError` con traza = MUERTO; otra
cosa = **NO MEDIDO**. Cada log se mide por **bytes** y **ultima linea** antes de
aceptarlo, y el veredicto sale del `.meta` que se escribe **despues** de que el
proceso termina (un log sin `.meta` es un log no medido, nunca un verde).

## B. R5 -- Las ocho citas: vivas, caducadas o falsas

El dev cambio seis referencias. No me he fiado de sus numeros: he ido a la
linea citada con `ast` y a leer lo que hay, y he derivado los hechos de otro
sitio (los sitios reales de la sobrescritura de `_patrones_de_categoria`, las
ocurrencias del marcador headless, la definicion del guard de codigo muerto).

| cita | que afirma | que hay en esa linea | veredicto |
|---|---|---|---|
| `run_tests.py:15766` | una sobrescritura de `_patrones_de_categoria` | `svc._patrones_de_categoria = lambda cat: (` | **VIVA** |
| `run_tests.py:15793` | otra sobrescritura | `svc._patrones_de_categoria = lambda cat: (` | **VIVA** |
| `run_tests.py:15886` | otra sobrescritura | `svc._patrones_de_categoria = lambda cat: (` | **VIVA** |
| `run_tests.py:15932` | otra sobrescritura | `svc._patrones_de_categoria = lambda cat: (` | **VIVA** |
| `run_tests.py:23133` | la cita de `sandbox-rules.md:55-56` por numero de linea | `("sandbox-rules.md:55-56",)` | **VIVA** |
| `run_tests.py:23131` | el suelo `min(posiciones) > 61` | `assert min(posiciones) > 61, (` | **VIVA** |
| `run_tests.py:14013` | la **2a** ocurrencia del marcador headless | `print("\n--- Running Headless UI Tests ---")` | **VIVA** |
| `run_tests.py:28734` | el guard de codigo muerto de `src/woptimizer/**` | `def test_la_verificacion_de_sintaxis_deriva_su_alcance_y_no_lo_enumera():` | **VIVA** |

Derivado con `ast`, no con los numeros del dev:

* las sobrescrituras de `_patrones_de_categoria` estan en **6** sitios (4 con
  `svc.` en 15766/15793/15886/15932 y 2 mas); las cuatro citadas son de las que
  el texto afirma;
* el marcador `--- Running Headless UI Tests ---` aparece en **2** lineas; la
  segunda es la 14013, que es la que cita `validate_docs.py:1180` (por eso el
  validador la resuelve en caliente);
* `validate_docs.py:1435` cita `run_tests.py:28734`, y la 28734 es exactamente
  la definicion del guard de codigo muerto.

**8 de 8 VIVAS.** Las 6 caducadas de la PARTE 1 estan reparadas. Queda una
nota menor: la cita de `run_tests.py:14013` dice "la segunda ocurrencia del
marcador" y sigue siendo cierto, pero el numero **cambia** si alguien inserta
lineas por encima de la 14013; es una cita por numero, y eso es exactamente lo
que el guard de citas existe para detectar.

## C. R1 -- El recuento 234 y las tres sondas `test_*`

Recuento **derivado con `ast`**, replicando el algoritmo de `validate_docs.py`
(el mismo que usa el validador, no el que dice el dev):

```
defined (def test_* de modulo) : 234
invoked (llamadas en __main__)  : 234
huerfanos defined-invoked      : ninguno
huerfanos invoked-defined      : ninguno
REPARTO: 158 backend + 76 headless = 234
linea del marcador headless    : 30411
```

**158 + 76 = 234 sale.** Y las 4 declaraciones del repo dicen lo mismo:

| fichero | que declara | medido |
|---|---|---|
| `AGENTS.md:70` | `234 tests` | coincide |
| `README.md:63` | `234 tests` | coincide |
| `STATUS.md:12` y `:120` | `234 tests` y `158 backend + 76 headless` | coincide |
| `docs/ai/testing-guide.md:57` | `234 tests` (234 filas de tabla) y `158 backend + 76 headless` | coincide |

**Las tres sondas van ANTES del marcador** (comprobado, no supuesto):

| sonda | definicion | invocacion | antes de 30411 |
|---|---|---|---|
| `test_el_conjunto_de_vistas_tiene_una_sola_fuente_de_verdad` (AC-1) | 29592 | 30408 | si |
| `test_una_vista_nueva_se_audita_aunque_nadie_la_apunte` (AC-2) | 29925 | 30409 | si |
| `test_el_derivado_de_vistas_es_el_disco_y_abre_algo` (AC-3) | 30031 | 30410 | si |

Y son 3 tests de **tooling**, no de UI: AC-1 y AC-3 son `ast` sobre este mismo
fichero y AC-2 corre el guard de verdad en un subproceso. Ninguno abre ventana.

**El validador del repo real, ejecutado aqui:** `156 OK, 0 FAIL, 0 SKIP` y
`run_tests.py: 234 tests definidos = 234 invocados (derivado con ast)`.

## D. R2/R3 -- El AC-1 nuevo: es una REGLA DE MODULO, pero es vaciable

**El sujeto de la regla esta DERIVADO, no enumerado.** `_fors_del_modulo(arbol)`
recorre el `ast` entero y devuelve `[(ambito, nodo_for)]`; `_delitos_de_fuente_
escrita_a_mano` aplica la regla a **todos** los `for` del fichero. No hay
ninguna lista de guards, ni de sujetos, ni de nombres de vista. La enumeracion
de las tres sondas de la PARTE 1 (`_GUARD_DE_WORKERS`, `_GUARD_HERMANO`) ya no
existe en el codigo.

**Baseline del detector sobre el modulo real (in-process, importando el
`run_tests.py` de la camara sin ejecutar la suite):**

```
nombres de vista derivados : ['dashboard_view.py', 'pack_manager_view.py', 'process_manager_view.py']
declaration derivada        : ['dashboard_view.py', 'pack_manager_view.py', 'process_manager_view.py']
derivador                   : _vistas_del_disco
delitos totales             : 0 []
delitos de la REGLA DE FORMA : 0 []
```

La contraprueba de R2 (la que mata a Q2 y a Q2b) esta en `run_tests.py:29757`:
planta una enumeracion escrita a mano en `guarda_cualquiera()`, que **no esta en
ninguna lista**, y exige que el hallazgo la nombre con FICHERO Y LINEA
(`assert f"run_tests.py:{linea_del_for}" in rojo` y `assert "guarda_cualquiera"
in rojo`). El detector se prueba **en las dos direcciones**: el `for` literal se
denuncia y el `for` derivado se calla.

### D.1 Lo que el motor SI caza (medido)

| caso | como esta escrito | veredicto del detector |
|---|---|---|
| enumeracion literal en linea | `for n in ("dashboard_view.py", "pack_manager_view.py"):` | **DENUNCIADO** |
| enumeracion literal por un nombre | `VISTAS = (...); for n in VISTAS:` | **DENUNCIADO** |
| enumeracion con un nombre REAL y otro inexistente | `("dashboard_view.py", "no_existe_b.py")` | **DENUNCIADO** |
| enumeracion del conjunto COMPLETO (3 nombres) en un helper | `return ("dashboard_view.py", "pack_manager_view.py", "process_manager_view.py")` | **DENUNCIADO** (regla 3: "una SEGUNDA copia del conjunto de vistas escrita a mano") |
| helper que deriva del disco | `return {p for p in glob.glob('vistas/*.py')}` | **CALLADO** (control positivo) |
| el `for` que recorre el DERIVADO | `vistas = _vistas_del_disco(); for n in sorted(vistas):` | **CALLADO** (control positivo) |

### D.2 Lo que el motor NO caza (medido) -- tres huecos, con nombre

**H-1 -- la enumeracion escrita a mano detras de una llamada a un helper.**
La regla exige que el iterable del `for` sea un contenedor de literales `.py`
(en linea) o un **nombre** enlazado a ese contenedor en el mismo ambito. Si el
`for` recorre una **llamada**, no hay nada que mirar:

```
forma, detras de una llamada : []
forma, en linea (CONTROL)    : ["run_tests.py:2: `guarda` recorre una ENUMERACION
                                literal del conjunto de vistas (escrita a mano:
                                ['dashboard_view.py', 'pack_manager_view.py']). ..."]
```

Y el helper que la produce tampoco se denuncia: la regla 3 solo ve copias del
conjunto **COMPLETO** (3 nombres), no subconjuntos (2 de 3). "Sacar la lista a
una funcion" es el refactor mas natural que existe y es el que se cuela.

**H-2 -- una enumeracion de nombres INEXISTENTES se escapa por completo.**
`nombres_de_vista` es disco UNION declaracion, asi que una enumeracion de
nombres que no son vistas no se parece a nada que el motor sepa mirar:

```
forma  : []      (ningun delito)
copias : []      (ningun delito)
```

La reserva que declaro el dev ("una enumeracion de nombres inexistentes
escaparia, pero el guard abriria ficheros inexistentes -> rojo ruidoso, no
verde falso") es **CIERTA en su primera mitad** (medida: se escapa) y
**acotada en la segunda**: el rojo ruidoso depende de que esa enumeracion sea
la FUENTE de un guard que abre ficheros. Si la enumeracion de nombres
inexistentes vive en una funcion que no abre nada, no hay rojo: no hay ni
ruido ni verde falso, simply no hay nada. Y si la enumeracion mezcla un
nombre real y uno inexistente, el motor la denuncia (medido arriba): el hueco
es solo del subconjunto **totalmente** inexistente.

**H-3 -- la tolerancia es POR FUNCION, no por enumeracion.**
`_justificacion_de_la_enumeracion` se lee del docstring del **ambito** del
`for`; si el docstring tiene las dos frases, la funcion **entera** queda
exenta. Medido:

```
CON justificacion (una sola): []      <- las DOS enumeraciones se saltan
SIN justificacion (CONTROL)  : [2 delitos]
```

Es decir: **una** justificacion escrita tapa **N** enumeraciones de la misma
funcion, y cualquier funcion puede ASEPTARSE copiando los dos marcadores en su
docstring. La justificacion escrita es el mecanismo correcto (es el de AC-5 de
TASK-081) pero el alcance es el de la FUNCION, no el de la enumeracion.

## E. La justificacion escrita de `run_tests.py:6160` (mecanismo de TASK-081)

**No es una lista muda de permitidos.** Es lo que el mecanismo de TASK-081
pide, y se comprueba por las DOS partes, con texto de verdad detras:

```
justificacion detectada : ('estas DOS vistas son las que manejan categorias y las elige
                            el sentido del test, no el sistema de ficheros: la tercera
                            vista no tiene catalogo que ordenar.',
                           'el ciclo que recorra el conjunto de vistas DERIVADO reescribe
                            este test para iterar el derivado y filtrar por el criterio
                            semantico de "maneja categorias".')
(a) longitud: 155 caracteres     (b) longitud: 155 caracteres
```

* **(a) por que existe**: "estas DOS vistas son las que manejan categorias y las
  elige el sentido del test, no el sistema de ficheros" -- dice **por que**.
* **(b) que la retira**: "el ciclo que recorra el conjunto de vistas DERIVADO
  reescribe este test para iterar el derivado y filtrar por el criterio
  semantico" -- dice **que** la retira.
* 155 y 155 caracteres de texto real, muy por encima del minimo de 30.
* Los marcadores son los del mecanismo: `(a) POR QUE existe la enumeracion:` y
  `(b) QUE LA RETIRA:`.

**La justificacion es REAL, no decorativa.** Quitando el docstring de esa
funcion en memoria, la regla de forma encuentra el hallazgo:

```
sin el docstring, la regla de forma encuentra:
  ["run_tests.py:6160: `test_orden_de_categorias_no_es_alfabetico` recorre una
    ENUMERACION literal del conjunto de vistas (escrita a mano:
    ['pack_manager_view.py', 'process_manager_view.py']). ..."]
```

Es decir: la enumeracion de 6160 **la encuentra el motor**, y lo que la deja
pasar es la justificacion escrita. El mutante **S2c** (cortar la frase (b) por
debajo de 30 caracteres) mide esto en la suite completa.

**No es una quinta copia del conjunto de vistas.** Derivado con `ast`, las
enumeraciones de nombres de vista que hay en `run_tests.py` son **3**:

| linea | contenido | que es |
|---|---|---|
| 29141 | `VISTAS_DECLARADAS = (dashboard, pack_manager, process_manager)` | la DECLARACION: la fuente unica |
| 6160 | `("process_manager_view.py", "pack_manager_view.py")` | una **SELECCION** justificada de 2 de 3 |
| 29712 | `{"dashboard_view.py", "pack_manager_view.py"}` | la fixture de las contrapruebas del propio detector (no es fuente de nada) |

6160 es una **seleccion con razon semantica** ("las que manejan categorias"),
no un alcance: le falta una vista a proposito y por eso necesita justificacion.
En `validate_docs.py` no hay ninguna enumeracion de nombres de vista. Las tres
sondas de la PARTE 1 (que eran cuatro copias del conjunto) ya no existen.

## F. Un defecto NUEVO que ha metido el commit de REPARACION

**M-V1 no muere por su asercion: muere por un `NameError`.** Y el `NameError`
esta en el codigo que la reparacion ha escrito, no en el mutante.

```
File "...\camara_M-V1_...\run_tests.py", line 30408, in <module>
  test_el_conjunto_de_vistas_tiene_una_sola_fuente_de_verdad()      # AC-1
File "...\run_tests.py", line 29636, in test_el_conjunto_de_vistas_tiene_una_sola_fuente_de_verdad
  declaracion_derivada, _derivador = _declaracion_y_derivador(arbol)
File "...\run_tests.py", line 29404, in _declaracion_y_derivador
  derivador = _funcion_de_modulo_a_la_que_llega(derecha, vinculos, funciones)
File "...\run_tests.py", line 29351, in _funcion_de_modulo_a_la_que_llega
  + [kw.value for kw in expression.keywords]):
NameError: name 'expression' is not defined. Did you mean: 'expresion'?
```

`run_tests.py:29351` usa `expression`, y el parametro de la funcion se llama
`expresion`. **Lo metio la reparacion**: en el fix original (`f8bc867`) esa
linea era `expresion.keywords`, y en el commit de reparacion (`73b2393`) paso a
ser `expression.keywords`:

```
$ git show 73b2393 -- run_tests.py | grep keywords
+                          + [kw.value for kw in expression.keywords]):
$ git show f8bc867:run_tests.py | grep keywords
                   + [kw.value for kw in expresion.keywords])
```

**Cercania del defecto (MEDIDO, con un comprobador de nombres sin definir
escrito con `ast` sobre las lineas que anade el commit):**

```
commit 73b2393: 486 lineas anadidas en run_tests.py
  SIN DEFINIR: expression   usado en la linea [29351]
commit f8bc867: (el fix original) -- sin este fallo
```

Es el **UNICO** identificador sin definir que introduce la reparacion en
`run_tests.py` (y `validate_docs.py` no introduce ninguno).

**Por que es LATENTE y no se ve en verde.** La rama que lo dispara solo se
alcanza cuando la expresion es una llamada a una funcion que **no** es de
ambito de modulo:

```python
if isinstance(expresion, ast.Call):
    if (isinstance(expresion.func, ast.Name)
            and expresion.func.id in funciones):
        return expresion.func.id          # <-- el caso sano sale aqui
    for argumento in (list(expresion.args)
                      + [kw.value for kw in expression.keywords]):   # <-- revienta
```

En el codigo sano, el lado derecho de la comparacion es `_vistas_del_disco()`,
que es una funcion de modulo: sale por el `return` de arriba y nunca llega a la
linea rota. **Cualquier refactor que ponga una llamada que no sea de modulo
ahi** (por ejemplo `vistas_en_disco = set(_vistas_del_disco())`) convierte el
diagnostico del guard en un `NameError` sin nombres: el guard deja de decir
"no se puede derivar que funcion deriva el conjunto de vistas" y revienta.

**Consecuencia para la auditoria:** por la regla del encargo, una muerte por
`NameError` **no es veredicto**. Asi que **M-V1 queda como NO MEDIDO** en su
forma natural, y se vuelve a medir en la forma **M-V1b** (la misma semantica --
la DECLARACION vuelve a ser la fuente -- escrita con una TUPLA, que no dispara
la rama rota). El resultado de M-V1b esta en la tabla de la seccion G.

**Y una leccion de arnes que queda por escrito:** el baseline de la camara esta
**VERDE** (`rc=0`, `ALL TESTS PASSED.`), asi que el `NameError` no lo detecta
el baseline: lo ha detectado el MUTANTE. Un mutante que muere de una excepcion
no es un veredicto del mutante, es un **defecto del guard**, y por eso se
reporta con nombre y no se cuenta como muerte.

## G. R6 -- El tripwire: el mensaje dice la cifra COMPARADA

En el codigo de HEAD **no queda ninguna cifra escrita a mano en el mensaje**:

```
run_tests.py:29134   _CIFRA_DE_PUBLICACIONES_VIGILADAS = 10
run_tests.py:9442    assert contados_en_codigo == _CIFRA_DE_PUBLICACIONES_VIGILADAS, (
run_tests.py:9444      f"puerta autorizada y este tripwire COMPARA con {_CIFRA_DE_PUBLICACIONES_VIGILADAS} call sites migrados. "
```

El `assert` y el mensaje leen **la misma constante**. Medido con la cifra
desfasada (mutante **Q5**: `10` -> `11`), el guard de la camara sobre su propio
disco:

```
AssertionError: las vistas del disco tienen 10 publicaciones a una puerta
autorizada y este tripwire COMPARA con 11 call sites migrados. O se movio una
publicacion, o esta cifra esta desfasada: decidalo explicitamente en vez de
dejar que el guard se adapte solo.
```

**El mensaje ya NO se contradice.** Dice las dos cosas, y son distintas: lo que
**ha encontrado** (10) y lo que **compara** (11, la constante). Con la cifra
escrita a mano en el mensaje, el mismo mutante habria dicho "COMPARA con 10"
mientras comparaba con 11: dos cifras para el mismo hecho. Ahora es
**imposible**: si la constante se mueve, se mueven las dos.

Y en la camara de producto (donde el parche sube la constante a 12 y el disco
tiene 11 publicaciones), el mismo tripwire dice:

```
las vistas del disco tienen 11 publicaciones a una puerta autorizada y este
tripwire COMPARA con 12 call sites migrados
```

Es decir: el mensaje sigue a la constante **tambien dentro de la camara**, que
es donde antes se desincronizaba.

**El mutante Q5, en la suite completa: MUERTO** por la asercion de AC-2
(`run_tests.py:29972`, "el rojo tiene que NOMBRAR la infraccion (y no un fallo
cualquiera del subproceso)"): el tripwire desfasado hace que el rojo de la
camara sea el del tripwire y no el de la infraccion, y AC-2 lo rechaza. La
tripwire de R6 esta **cerrada**.

## H. La tabla de mutantes (suite COMPLETA, una camara por mutante)

Cada mutante tiene su propia camara desechable, su propio `git init` y su
propio log. El veredicto sale del `.meta` que se escribe **despues** de que el
proceso termina, asi que un log sin `.meta` seria "no medido", nunca "verde".

* `rc=0` + `ALL TESTS PASSED.` en la ultima linea = **SUPERVIVIENTE**
* `AssertionError` con traza = **MUERTO** (y se dice **por que**)
* `NameError` / `FileNotFoundError` / otra cosa = **NO MEDIDO** (no es veredicto)

| id | que rompe | rc | bytes | lineas | s | ultima linea | veredicto |
|---|---|---|---|---|---|---|---|
| **baseline** | sin mutacion (control positivo del arnes) | 0 | 30585 | 398 | 926.4 | `ALL TESTS PASSED.` | **CONTROL VERDE** |
| **Q1** | las tres sondas `test_*` NO se invocan | 1 | 11719 | 173 | 98.3 | `AssertionError: un journal ILEGIBLE es un fallo del ancla y solo uno: el historial de la fixture no aporta cic` | **MUERTO** |
| **Q2** | la regla de modulo se estrecha a UN guard (sujetos a mano) | 1 | 18516 | 235 | 859.7 | `AssertionError: el detector tiene que DENUNCIAR una enumeracion escrita a mano en una funcion que NO esta en n` | **MUERTO** |
| **Q2b** | la regla de modulo no mira NINGUN guard | 1 | 18518 | 235 | 859.4 | `AssertionError: el detector tiene que DENUNCIAR una enumeracion escrita a mano en una funcion que NO esta en n` | **MUERTO** |
| **M-V1** | el guard vuelve a abrir la DECLARACION (forma natural) | 1 | 18959 | 244 | 862.7 | `NameError: name 'expression' is not defined. Did you mean: 'expresion'?` | **NO MEDIDO** (excepcion, no asercion) |
| **M-V1b** | idem, con la DECLARACION como tupla | 1 | 19210 | 236 | 904.8 | `AssertionError: el rojo tiene que NOMBRAR la infraccion (y no un fallo cualquiera del subproceso): salida='Tes` | **MUERTO** |
| **M-V1c** | idem, con la DECLARACION como comprehension de conjunto | 1 | 18821 | 236 | 838.3 | `AssertionError: una vista NUEVA en el disco y SIN declarar tiene que dar ROJO que la nombre y dio 0: si la der` | **MUERTO** |
| **M-V3** | el helper deriva un conjunto VACIO | 1 | 19635 | 236 | 867.2 | `AssertionError: el rojo tiene que NOMBRAR la infraccion (y no un fallo cualquiera del subproceso): salida='Tes` | **MUERTO** |
| **M-V3b** | el helper deriva una lista FIJA escrita a mano | 1 | 18377 | 237 | 933.2 | `La fuente tiene que ser el disco (`_vistas_del_disco()`, en ambito de modulo) y la DECLARACION se compara con ` | **MUERTO** |
| **M-V4** | el helper `_vistas_del_disco` deja de estar en ambito de modulo | 1 | 18959 | 244 | 924.0 | `NameError: name 'expression' is not defined. Did you mean: 'expresion'?` | **NO MEDIDO** (excepcion, no asercion) |
| **M-V4b** | idem, con una definicion ANIDADA del helper | 1 | 18439 | 237 | 838.1 | `La fuente tiene que ser el disco (`_vistas_del_disco()`, en ambito de modulo) y la DECLARACION se compara con ` | **MUERTO** |
| **M-V5** | el helper devuelve `set(VISTAS_DECLARADAS)` | 1 | 18484 | 237 | 928.5 | `La fuente tiene que ser el disco (`_vistas_del_disco()`, en ambito de modulo) y la DECLARACION se compara con ` | **MUERTO** |
| **M-V6** | el directorio de vistas se ancla a una ruta FIJA | 1 | 19633 | 236 | 937.3 | `AssertionError: el rojo tiene que NOMBRAR la infraccion (y no un fallo cualquiera del subproceso): salida='Tes` | **MUERTO** |
| **M-V7** | el directorio de vistas apunta a `ui/` en vez de `ui/views/` | 1 | 19873 | 236 | 935.8 | `AssertionError: el rojo tiene que NOMBRAR la infraccion (y no un fallo cualquiera del subproceso): salida='Tes` | **MUERTO** |
| **Q5** | la cifra del tripwire se desfasca (10 -> 11) | 1 | 19408 | 236 | 938.5 | `AssertionError: el rojo tiene que NOMBRAR la infraccion (y no un fallo cualquiera del subproceso): salida='Tes` | **MUERTO** |
| **S1c** | CONTROL: enumeracion escrita a mano ANIDADA en un `for` | 1 | 18509 | 237 | 845.4 | `La fuente tiene que ser el disco (`_vistas_del_disco()`, en ambito de modulo) y la DECLARACION se compara con ` | **MUERTO** |
| **S1** | S1c + el recorrido NO baja a un `for` anidado | 0 | 30585 | 398 | 919.2 | `ALL TESTS PASSED.` | **SUPERVIVIENTE** |
| **S2c** | la justificacion escrita se queda corta (frase (b) < 30 caracteres) | 1 | 18527 | 237 | 841.3 | `La fuente tiene que ser el disco (`_vistas_del_disco()`, en ambito de modulo) y la DECLARACION se compara con ` | **MUERTO** |
| **S2** | una justificacion escrita tapa DOS enumeraciones de la misma funcion | 0 | 30735 | 402 | 1015.8 | `ALL TESTS PASSED.` | **SUPERVIVIENTE** |
| **S3** | la enumeracion escrita a mano detras de una llamada a un helper | 0 | 30735 | 402 | 1013.9 | `ALL TESTS PASSED.` | **SUPERVIVIENTE** |
| **S4** | el patron de S3 aplicado al GUARD DE VERDAD | 1 | 18371 | 237 | 773.0 | `La fuente tiene que ser el disco (`_vistas_del_disco()`, en ambito de modulo) y la DECLARACION se compara con ` | **MUERTO** |
| **S3-restaurado** | la camara S3 restaurada al fichero sano | 0 | 30585 | 398 | 894.5 | `ALL TESTS PASSED.` | **SUPERVIVIENTE** |

**Motivo literal de cada muerte:**

* **baseline** -- ALL TESTS PASSED.
  - muerte: (sin traza)
  - motivo: Pre-vuelo de existencia: el hash real se resuelve y el muerto no, y el 128 de git no se pierde como AssertionError.
* **Q1** -- AssertionError: un journal ILEGIBLE es un fallo del ancla y solo uno: el historial de la fixture no aporta ciclos y el changelog esta completo. Errors: ['.taskmaster/rd_journal.json: ESTA CORRUPTO. El ancla del changelog
  - muerte: File "C:\Users\carch\AppData\Local\Temp\wopt_c68_r2_aud\camara_Q1_20261022_021017\run_tests.py", line 13542, in test_el_journal_ilegible_informa_en_vez_de_reventar_el_validador | assert len(errors) == 1, (
  - motivo: AssertionError: un journal ILEGIBLE es un fallo del ancla y solo uno: el historial de la fixture no aporta ciclos y el changelog esta completo. Errors: ['.taskmaster/rd_journal.json: ESTA CORRUPTO. El ancla del changelog de raiz no se puede comprobar, y sin el no hay garantia de que el ultimo ciclo ...
* **Q2** -- AssertionError: el detector tiene que DENUNCIAR una enumeracion escrita a mano en una funcion que NO esta en ninguna lista, y nombrarla con FICHERO Y LINEA: si el detector vuelve a mirar un conjunto de guards escrito a m
  - muerte: File "C:\Users\carch\AppData\Local\Temp\wopt_c68_r2_aud\camara_Q2_20261022_021017\run_tests.py", line 29780, in test_el_conjunto_de_vistas_tiene_una_sola_fuente_de_verdad | assert f"run_tests.py:{linea_del_for}" in rojo, (
  - motivo: AssertionError: el detector tiene que DENUNCIAR una enumeracion escrita a mano en una funcion que NO esta en ninguna lista, y nombrarla con FICHERO Y LINEA: si el detector vuelve a mirar un conjunto de guards escrito a mano (Q2) o deja de mirar ninguno (Q2b), la enumeracion se cuela en silencio y es...
* **Q2b** -- AssertionError: el detector tiene que DENUNCIAR una enumeracion escrita a mano en una funcion que NO esta en ninguna lista, y nombrarla con FICHERO Y LINEA: si el detector vuelve a mirar un conjunto de guards escrito a m
  - muerte: File "C:\Users\carch\AppData\Local\Temp\wopt_c68_r2_aud\camara_Q2b_20261022_021017\run_tests.py", line 29778, in test_el_conjunto_de_vistas_tiene_una_sola_fuente_de_verdad | assert f"run_tests.py:{linea_del_for}" in rojo, (
  - motivo: AssertionError: el detector tiene que DENUNCIAR una enumeracion escrita a mano en una funcion que NO esta en ninguna lista, y nombrarla con FICHERO Y LINEA: si el detector vuelve a mirar un conjunto de guards escrito a mano (Q2) o deja de mirar ninguno (Q2b), la enumeracion se cuela en silencio y es...
* **M-V1** -- NameError: name 'expression' is not defined. Did you mean: 'expresion'?
  - muerte: (sin traza)
  - motivo: (sin AssertionError)
* **M-V1b** -- AssertionError: el rojo tiene que NOMBRAR la infraccion (y no un fallo cualquiera del subproceso): salida='Testing that pack workers only publish via self.after (TASK-035 / cycle 26)...\nTraceback (most recent call last)
  - muerte: File "C:\Users\carch\AppData\Local\Temp\wopt_c68_r2_aud\camara_M-V1b_20261022_023607\run_tests.py", line 29972, in test_una_vista_nueva_se_audita_aunque_nadie_la_apunte | assert "el worker toca la vista fuera de self.after(0, ...)" in salida, (
  - motivo: AssertionError: el rojo tiene que NOMBRAR la infraccion (y no un fallo cualquiera del subproceso): salida='Testing that pack workers only publish via self.after (TASK-035 / cycle 26)...\nTraceback (most recent call last):\n  File "C:\\Users\\carch\\AppData\\Local\\Temp\\wopt_c082_mzosngjx\\driver.py...
* **M-V1c** -- AssertionError: una vista NUEVA en el disco y SIN declarar tiene que dar ROJO que la nombre y dio 0: si la derivacion devuelve la DECLARACION la comparacion es tautologica, no hay rojo, y la vista nueva deja de auditarse
  - muerte: File "C:\Users\carch\AppData\Local\Temp\wopt_c68_r2_aud\camara_M-V1c_20261022_025349\run_tests.py", line 30010, in test_una_vista_nueva_se_audita_aunque_nadie_la_apunte | assert r3.returncode != 0, (
  - motivo: AssertionError: una vista NUEVA en el disco y SIN declarar tiene que dar ROJO que la nombre y dio 0: si la derivacion devuelve la DECLARACION la comparacion es tautologica, no hay rojo, y la vista nueva deja de auditarse sin que nadie lo note (M-V5). salida='Testing that pack workers only publish vi...
* **M-V3** -- AssertionError: el rojo tiene que NOMBRAR la infraccion (y no un fallo cualquiera del subproceso): salida='Testing that pack workers only publish via self.after (TASK-035 / cycle 26)...\nTraceback (most recent call last)
  - muerte: File "C:\Users\carch\AppData\Local\Temp\wopt_c68_r2_aud\camara_M-V3_20261022_021017\run_tests.py", line 29972, in test_una_vista_nueva_se_audita_aunque_nadie_la_apunte | assert "el worker toca la vista fuera de self.after(0, ...)" in salida, (
  - motivo: AssertionError: el rojo tiene que NOMBRAR la infraccion (y no un fallo cualquiera del subproceso): salida='Testing that pack workers only publish via self.after (TASK-035 / cycle 26)...\nTraceback (most recent call last):\n  File "C:\\Users\\carch\\AppData\\Local\\Temp\\wopt_c082_pddyv4ob\\driver.py...
* **M-V3b** -- La fuente tiene que ser el disco (`_vistas_del_disco()`, en ambito de modulo) y la DECLARACION se compara con el derivado (TASK-082, AC-1).
  - muerte: File "C:\Users\carch\AppData\Local\Temp\wopt_c68_r2_aud\camara_M-V3b_20261022_021017\run_tests.py", line 29642, in test_el_conjunto_de_vistas_tiene_una_sola_fuente_de_verdad | assert not delitos, (
  - motivo: AssertionError: el conjunto de vistas que vigilan los guards NO esta derivado del disco:
* **M-V4** -- NameError: name 'expression' is not defined. Did you mean: 'expresion'?
  - muerte: (sin traza)
  - motivo: (sin AssertionError)
* **M-V4b** -- La fuente tiene que ser el disco (`_vistas_del_disco()`, en ambito de modulo) y la DECLARACION se compara con el derivado (TASK-082, AC-1).
  - muerte: File "C:\Users\carch\AppData\Local\Temp\wopt_c68_r2_aud\camara_M-V4b_20261022_025037\run_tests.py", line 29648, in test_el_conjunto_de_vistas_tiene_una_sola_fuente_de_verdad | assert not delitos, (
  - motivo: AssertionError: el conjunto de vistas que vigilan los guards NO esta derivado del disco:
* **M-V5** -- La fuente tiene que ser el disco (`_vistas_del_disco()`, en ambito de modulo) y la DECLARACION se compara con el derivado (TASK-082, AC-1).
  - muerte: File "C:\Users\carch\AppData\Local\Temp\wopt_c68_r2_aud\camara_M-V5_20261022_021017\run_tests.py", line 29641, in test_el_conjunto_de_vistas_tiene_una_sola_fuente_de_verdad | assert not delitos, (
  - motivo: AssertionError: el conjunto de vistas que vigilan los guards NO esta derivado del disco:
* **M-V6** -- AssertionError: el rojo tiene que NOMBRAR la infraccion (y no un fallo cualquiera del subproceso): salida='Testing that pack workers only publish via self.after (TASK-035 / cycle 26)...\nTraceback (most recent call last)
  - muerte: File "C:\Users\carch\AppData\Local\Temp\wopt_c68_r2_aud\camara_M-V6_20261022_021017\run_tests.py", line 29972, in test_una_vista_nueva_se_audita_aunque_nadie_la_apunte | assert "el worker toca la vista fuera de self.after(0, ...)" in salida, (
  - motivo: AssertionError: el rojo tiene que NOMBRAR la infraccion (y no un fallo cualquiera del subproceso): salida='Testing that pack workers only publish via self.after (TASK-035 / cycle 26)...\nTraceback (most recent call last):\n  File "C:\\Users\\carch\\AppData\\Local\\Temp\\wopt_c082_x4bt7zlu\\driver.py...
* **M-V7** -- AssertionError: el rojo tiene que NOMBRAR la infraccion (y no un fallo cualquiera del subproceso): salida='Testing that pack workers only publish via self.after (TASK-035 / cycle 26)...\nTraceback (most recent call last)
  - muerte: File "C:\Users\carch\AppData\Local\Temp\wopt_c68_r2_aud\camara_M-V7_20261022_021017\run_tests.py", line 29972, in test_una_vista_nueva_se_audita_aunque_nadie_la_apunte | assert "el worker toca la vista fuera de self.after(0, ...)" in salida, (
  - motivo: AssertionError: el rojo tiene que NOMBRAR la infraccion (y no un fallo cualquiera del subproceso): salida='Testing that pack workers only publish via self.after (TASK-035 / cycle 26)...\nTraceback (most recent call last):\n  File "C:\\Users\\carch\\AppData\\Local\\Temp\\wopt_c082_ekeciwu6\\driver.py...
* **Q5** -- AssertionError: el rojo tiene que NOMBRAR la infraccion (y no un fallo cualquiera del subproceso): salida='Testing that pack workers only publish via self.after (TASK-035 / cycle 26)...\nTraceback (most recent call last)
  - muerte: File "C:\Users\carch\AppData\Local\Temp\wopt_c68_r2_aud\camara_Q5_20261022_021017\run_tests.py", line 29972, in test_una_vista_nueva_se_audita_aunque_nadie_la_apunte | assert "el worker toca la vista fuera de self.after(0, ...)" in salida, (
  - motivo: AssertionError: el rojo tiene que NOMBRAR la infraccion (y no un fallo cualquiera del subproceso): salida='Testing that pack workers only publish via self.after (TASK-035 / cycle 26)...\nTraceback (most recent call last):\n  File "C:\\Users\\carch\\AppData\\Local\\Temp\\wopt_c082_vjcjw6ws\\driver.py...
* **S1c** -- La fuente tiene que ser el disco (`_vistas_del_disco()`, en ambito de modulo) y la DECLARACION se compara con el derivado (TASK-082, AC-1).
  - muerte: File "C:\Users\carch\AppData\Local\Temp\wopt_c68_r2_aud\camara_S1c_20261022_021017\run_tests.py", line 29653, in test_el_conjunto_de_vistas_tiene_una_sola_fuente_de_verdad | assert not delitos, (
  - motivo: AssertionError: el conjunto de vistas que vigilan los guards NO esta derivado del disco:
* **S1** -- ALL TESTS PASSED.
  - muerte: (sin traza)
  - motivo: Pre-vuelo de existencia: el hash real se resuelve y el muerto no, y el 128 de git no se pierde como AssertionError.
* **S2c** -- La fuente tiene que ser el disco (`_vistas_del_disco()`, en ambito de modulo) y la DECLARACION se compara con el derivado (TASK-082, AC-1).
  - muerte: File "C:\Users\carch\AppData\Local\Temp\wopt_c68_r2_aud\camara_S2c_20261022_021017\run_tests.py", line 29641, in test_el_conjunto_de_vistas_tiene_una_sola_fuente_de_verdad | assert not delitos, (
  - motivo: AssertionError: el conjunto de vistas que vigilan los guards NO esta derivado del disco:
* **S2** -- ALL TESTS PASSED.
  - muerte: (sin traza)
  - motivo: Pre-vuelo de existencia: el hash real se resuelve y el muerto no, y el 128 de git no se pierde como AssertionError.
* **S3** -- ALL TESTS PASSED.
  - muerte: (sin traza)
  - motivo: Pre-vuelo de existencia: el hash real se resuelve y el muerto no, y el 128 de git no se pierde como AssertionError.
* **S4** -- La fuente tiene que ser el disco (`_vistas_del_disco()`, en ambito de modulo) y la DECLARACION se compara con el derivado (TASK-082, AC-1).
  - muerte: File "C:\Users\carch\AppData\Local\Temp\wopt_c68_r2_aud\camara_S4_20261022_030109\run_tests.py", line 29647, in test_el_conjunto_de_vistas_tiene_una_sola_fuente_de_verdad | assert not delitos, (
  - motivo: AssertionError: el conjunto de vistas que vigilan los guards NO esta derivado del disco:
* **S3-restaurado** -- ALL TESTS PASSED.
  - muerte: (sin traza)
  - motivo: Pre-vuelo de existencia: el hash real se resuelve y el muerto no, y el 128 de git no se pierde como AssertionError.

## I. Hallazgos con nombre (los que quedan abiertos)

| id | severidad | que hay que arreglar | como se ha medido |
|---|---|---|---|
| **A-C68-7** | **P1** | `run_tests.py:29351` usa `expression` y el parametro se llama `expresion`: un **`NameError` latente que ha metido el commit de REPARACION `73b2393`** (en `f8bc867` era `expresion.keywords`). Consecuencia: el guard no puede decir "no se puede derivar que funcion deriva el conjunto de vistas" cuando el lado derecho de la comparacion es una llamada que no es de modulo, y **dos de los mutantes del fix (M-V1 y M-V4) mueren por la excepcion y no por su asercion** | mutantes M-V1 y M-V4 (ver la tabla) + comprobador de nombres sin definir sobre las 486 lineas que anade `73b2393`: **1 solo** identificador sin definir, `expression` en 29351 |
| **A-C68-8** | **P3** | la regla de forma de AC-1 **no ve una enumeracion escrita a mano que este detras de una llamada a un helper** (`for n in _mis_vistas()`). "Sacar la lista a una funcion" es el refactor mas natural que existe | mutante **S3**: suite completa en VERDE (`rc=0`, `ALL TESTS PASSED.`). **La consecuencia de PRODUCTO esta cerrada** (mutante **S4**: el mismo patron aplicado al guard de verdad): el conjunto COMPLETO escrito a mano lo caza la regla 3 ("una SEGUNDA copia del conjunto de vistas escrita a mano") y un SUBCONJUNTO lo caza la comparacion tautologica que los dos guards tienen (`run_tests.py:9429` y `:27706`). Lo que queda es un hueco de la REGLA DE FORMA, no de la cobertura |
| **A-C68-9** | **P3** | la tolerancia por justificacion escrita es **POR FUNCION, no por enumeracion**: una sola justificacion tapa **N** enumeraciones de la misma funcion, y cualquier funcion puede ASEPTARSE copiando los dos marcadores en su docstring | mutante **S2**: suite completa en VERDE (`rc=0`, `ALL TESTS PASSED.`), con la contraprueba in-process de que sin justificacion los mismos dos `for` dan 2 hallazgos |
| **A-C68-10** | **P3** | `_fors_del_modulo` **no baja a un `for` anidado**: su docstring promete "cada `for` del modulo" y no es cierto. Una enumeracion escrita a mano metida dentro de otro `for` no se ve, y **nada lo nota** | mutante **S1**: suite completa en VERDE (`rc=0`, `ALL TESTS PASSED.`, **exactamente los mismos 30585 bytes que el baseline**). El control **S1c** (la MISMA enumeracion, sin el sabotaje del recorrido) **MUERE** por AC-1: "run_tests.py:29193: `_guarda_anidada_de_la_camara` recorre una ENUMERACION literal..." |

**Los hallazgos de la PARTE 1 que la reparacion CIERRA (medido, no de palabra):**

| id de la PARTE 1 | como se cierra | veredicto |
|---|---|---|
| **A-C68-1** (las tres sondas no vigiladas) | las tres son `def test_*` y el validador cuenta `234 definidos = 234 invocados` | **CERRADO**: el mutante Q1 muere por asercion en la suite completa, no solo en el validador |
| **A-C68-2** (el alcance de AC-1 era una lista literal) | la regla es de MODULO: `_fors_del_modulo` recorre el `ast` entero y no hay ninguna lista de sujetos | **CERRADO**: Q2 y Q2b mueren por la contraprueba de R2 |
| **A-C68-3** (la derivacion no ataba su resultado al disco) | regla (4) de AC-1: el helper no puede devolver la DECLARACION | **CERRADO**: M-V5 muere por AC-1 ("NO deriva del disco: usa `VISTAS_DECLARADAS`") y **tambien** por AC-2 (medido in-process) |
| **A-C68-4** / **S7** (el docstring de AC-1 afirmaba una garantia que no tenia) | el docstring nuevo declara las 5 reglas y **dice lo que NO comprueba** ("que el helper lea el disco de verdad. Eso lo mide AC-3") | **CERRADO**: la garantia que afirma es la que tiene |
| **A-C68-5** (6 citas caducadas) | 6 citas corregidas in-place | **CERRADO**: 8 de 8 citas VIVAS |
| **A-C68-6** (el mensaje del tripwire llevaba la cifra a mano) | la cifra comparada y la del mensaje salen de la misma constante | **CERRADO**: con la cifra desfasada el mensaje dice "COMPARA con 11" y el `assert` compara con 11 |

**Nota de honestidad sobre A-C68-8, A-C68-9 y A-C68-10:** son huecos de la
VIGILANCIA, no del fix. El fix (los 7 mutantes) sigue matando por su asercion.
Pero un guard que se puede vaciar por tres vias mas no es un guard: por la
regla del repo, un superviviente **se arregla, no se documenta**, y por eso
quedan listados arriba con nombre, no como nota al pie.

**Lo que SI es de producto (y por eso no es una nota):** con el patron de S3
aplicado al guard de verdad (mutante **S4**: el guard de workers abre un
conjunto de vistas escrito a mano, detras de una llamada), la pregunta es si
vuelve el defecto que TASK-082 cerro. **Medido: no.** El conjunto completo
escrito a mano lo caza la regla 3 de AC-1 ("una SEGUNDA copia del conjunto de
vistas escrita a mano", `run_tests.py:29187`) y un subconjunto lo caza la
comparacion tautologica que **los dos** guards tienen (`run_tests.py:9429` y
`run_tests.py:27706`). La consecuencia de producto de A-C68-8 esta, por tanto,
cerrada; lo que queda es que la REGLA DE FORMA no ve una enumeracion escrita a
mano escondida detras de una llamada, que es una laguna de la regla y no del
guard.

## J. Veredicto global

**VERDICT: FAIL**

* **El FIX (TASK-082): PASS.** Los 7 mutantes del fix original mueren por su
  asercion. Los dos que en su forma natural mueren por el `NameError` de la
  reparacion (M-V1 y M-V4) se han vuelto a medir en una forma que no dispara
  ese defecto, y mueren por su asercion tambien.
* **La VIGILANCIA (R1, R2, R3, R5, R6): PASS en lo que la reparacion
  prometia.** Q1, Q2 y Q2b --los tres supervivientes de la PARTE 1-- mueren
  todos por asercion en la suite completa. Las ocho citas viven. La cifra del
  tripwire ya no puede contradecirse.
* **La vigilancia en general: FAIL.** La reparacion cierra tres vias y deja
  **tres mas abiertas** (S1, S2 y S3), que se han medido con la suite completa
  en verde. Por la regla del repo ("un superviviente en seguridad o datos se
  arregla, no se documenta"), esto no se documenta y se arregla.

**Lo que NO se ha podido medir (y por que):** nada de lo obligatorio. Las 22
corridas tienen `.meta`: las 21 de la tabla mas la camara restaurada. Las dos
filas marcadas **NO MEDIDO** no son una falta de medicion, son el **veredicto
correcto** de esos dos mutantes: mueren por una EXCEPCION (`NameError`), y una
muerte por excepcion no es un veredicto de mutante sino un defecto del guard
(seccion F), asi que se vuelven a medir en la forma `M-V1c` y `M-V4b`.

## K. Trazabilidad: ficheros creados en `%TEMP%` y ancla del repo real

**Camaras (una por mutante), repos divulgables y desechables:**

```
%TEMP%\wopt_c68_r2_aud\
  camara_<mutante>_<sello>\        21 camaras usadas (21 mutantes/mediciones)
  gitdesechable_<mutante>_<sello>\ 21 repos `git init` PROPIOS y desechables
  logs\suite_<id>.log[.meta]       22 logs + sus .meta (21 + S3-restaurado)
  preparar.py  mutar.py  correr.py  lanzar.py  tabla.py
  verificar.py  mv2.py  ac2.py  tripwire.py  restaurar.py
  undef.py  typos.py  copias.py  sondas_estaticas.py  residuos.py
  escribir.py  escribir2.py  escribir3.py  escribir4.py  escribir5.py
  mutado_<mutante>.flag (20)  camara_<id>_path.txt  gitdir_<id>_path.txt
```

Ademas quedan **2 camaras huerfanas** (`camara_baseline_20261022_020903` y
`camara_baseline_20261022_020946`): son del **primer intento de preparar.py**,
que se DETUVO en el control de aislamiento (el `GIT_DIR` desechable no era un
repo y el comprobador no lo acepto). No se han usado para ninguna medicion.
El primero que se paro fue el control de aislamiento, que es exactamente para
lo que esta.

**La camara restaurada y verde.** La camara de S3 (la que tiene el mutante
superviviente) se ha vuelto a poner en su fichero sano y se ha re-ejecutado:

```
S3-restaurado: rc=0  bytes=30585  lineas=398  segundos=894.5
ULTIMA: 'ALL TESTS PASSED.'
```

**Exactamente los mismos 30585 bytes y las mismas 398 lineas que el baseline**:
la camara vuelve a verde byte a byte despues de haber pasado por el mutante.

**El repo real NO se ha tocado:**

* `git rev-parse HEAD` = `73b2393` antes y despues;
* `git status --porcelain` vacio;
* `git_safe_commit.py` **no** se ha invocado ni una vez (ni desde el repo ni
  desde `%TEMP%`): la camara usa `git` a pelo contra su `GIT_DIR` desechable;
* el unico fichero escrito en el repo es este informe, y lo versiona el
  orquestador.
