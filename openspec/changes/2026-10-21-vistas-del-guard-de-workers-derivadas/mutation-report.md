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
