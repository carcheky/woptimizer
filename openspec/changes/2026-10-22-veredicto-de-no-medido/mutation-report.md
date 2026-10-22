# Informe de mutación — TASK-083 (ciclo 69)

**Contrato:** `openspec/changes/2026-10-22-veredicto-de-no-medido/proposal.md` (§10 = AC-1..AC-6)
**Artefacto auditado:** commits `a4d2775` y `1894f5d` — *fix(tools): el hash muerto se deriva por construccion y el pre-vuelo deja de depender del reloj (TASK-083)* / *fix(tools): el pre-vuelo falla de forma determinista cuando el reloj se suelta (TASK-083)*
**Auditor:** Sherlock (mutation-auditor) · **Fecha:** 2026-10-22 · **Rama:** `beta`
**Alcance:** `run_tests.py` (tooling) + `validate_docs.py`. **Cero ediciones bajo `src/woptimizer/`.**

> Este informe se escribe **incrementalmente**, sección por sección. Si falta una
> sección, es que la medición de esa parte no llegó a completarse — no que esté
> vacía por descuido.

---

## 0. Ficha de la medición

### 0.1 Cámara

| Dato | Valor |
|---|---|
| Base | `%TEMP%\wopt_c69_aud\` |
| Cámaras | `camara_base_*`, `camara_base2..4`, `camara_m1`, `camara_m2`, `camara_m3`, `camara_trip`, `camara_t1`, `camara_t1d1` (10 cámaras) |
| Copia | `shutil.copytree(..., ignore=ignore_patterns(".git", "__pycache__", "*.pyc"))` → `.git` excluido **como fichero** (en este repo `.git` es un **fichero** de 57 B, no un directorio) |
| `src/woptimizer/` | **real**, copiado |
| Repo de la cámara | `.git` **nuevo** (`git init -b beta`) + **índice replicado del repo real** (267 ficheros, ver I-1) |
| Entorno de la suite | **sin** `GIT_DIR` / `GIT_WORK_TREE` / `GIT_INDEX_FILE`, igual que en el repo real |

### 0.2 Aislamiento del repo real — MEDIDO antes de mutar nada

```
CAMARA: C:\Users\carch\AppData\Local\Temp\wopt_c69_aud\camara_base_20261022_094643
.git presente en la camara tras copiar?  True (es un DIRECTORIO nuevo, no el fichero del repo real)
  .git/HEAD -> ref: refs/heads/beta
rev-parse --git-dir (GIT_DIR desechable) -> ''      (no resuelve el repo real)
devuelve el repo real?                   False
sin GIT_DIR -> rc: 0 | err:              (resuelve el repo PROPIO de la camara)
descubre el repo real?                   False
repo real -> git-dir: C:\Users\carch\AppData\Local\woptimizer_git\.git
AISLAMIENTO OK: True
```

`git rev-parse --git-dir` desde la raíz del repo real devuelve
`C:/Users/carch/AppData/Local/woptimizer_git/.git` (el desacoplado del VFS), que es
un repo **distinto** del de cualquier cámara.

**Nunca** se invocó `python .taskmaster/git_safe_commit.py` desde `%TEMP%` ni desde
un cwd copiado: el wrapper impone `GIT_WORK_TREE = REPO_ROOT` y habría commiteado
en el repositorio real con el árbol de la cámara. Todo `git` de la cámara fue a
 pelo contra el `.git` **de la cámara**, con entorno limpio.

### 0.3 Un fallo de INSTRUMENTO encontrado y reparado (no es veredicto)

| # | Fallo | Por qué era del instrumento | Reparación |
|---|---|---|---|
| **I-1** | Las 7 suites murieron en **17,7 s** (no 735) con `AssertionError: docs/archive/legacy-root-data/profiles.json NO esta versionado (rc=1, "error: pathspec ... did not match any file(s) known to git")` — **idéntico en las 7**, incluidos los 4 baselines | La cámara se montó con `git init` + un commit **vacío**: su índice no tenía **ningún** fichero, y el guard `test_el_archivo_legacy_esta_versionado_y_no_vuelve_a_la_raiz` (`run_tests.py:6728`) exige que ese fichero esté **en el índice** (`git ls-files --error-unmatch`, `run_tests.py:6793`) | Se replicó el **índice exacto del repo real** en las 10 cámaras con `git update-index -z --add --stdin` alimentado por `git ls-files` del repo real (267 ficheros), y se commiteó. **No** se usó `git add -A`, que se habría llevado también lo que el repo real no versiona. Verificado: `git ls-files --error-unmatch docs/archive/legacy-root-data/profiles.json` → rc 0 en las 10 cámaras. El guard, aislado: **2/2 VERDE** |

Los 7 logs de la tanda fallida se conservaron como `suite_*.log` (7 285–7 291 B,
131 líneas) — su última línea era el `AssertionError`, **no** `ALL TESTS PASSED.`,
o sea NO MEDIDOS, no verdes.

### 0.4 Regla de desplazamiento aplicada

Las mutaciones se hicieron por **sustitución exacta** con el **mismo número de
líneas** (`run_tests.py: 31610 → 31610` en M-1, M-2, M-3, T-1, T-2; `-1` en G-1 y
G-3, `+6` en G-2). Consecuencia: **cero desplazamiento** de `run_tests.py:23133`
— la línea que `test_las_citas_de_sandbox_rules_siguen_siendo_ciertas`
(`run_tests.py:29006`) lee **en caliente** (`run_tests.py:29061` exige que
`"sandbox-rules.md:55-56"` siga en esa línea) — ni de `validate_docs.py:1429`
(la otra línea leída en caliente, `run_tests.py:29053`).

### 0.5 La línea canónica del veredicto NO existe todavía

`TASK-087` (el contrato `WOPT_VEREDICTO <mutante> <MUERTO|SOBREVIVIENTE|NO MEDIDO>
<sha>` y el killer-check) está **abierta**. Este informe, por tanto, **no** puede
emitir la línea canónica: la emite el orquestador o TASK-087. Los identificadores
cortos de este informe son propios suyos: `M-1`, `M-2`, `M-3` (los tres del
encargo), `T-1`, `T-1'`, `T-2` (alcance del tripwire), `G-1`, `G-2`, `G-3` (guard
de TASK-072), `D-1`, `D-1'` (derivación del conjunto de sujetos), `I-1` (fallo de
instrumento), `H-A`..`H-D` (agujeros) y `V-1`..`V-3` (vías nuevas).

---

## 1. Los tres mutantes del encargo

### 1.0 Resumen

| id | Qué rompe | Cómo lo maté | Veredicto |
|---|---|---|---|
| **M-1** | vuelve a `hash_real + "0"` | tripwire (FORMA) **y** el pre-vuelo, cada uno por su aserción | **MUERTO** |
| **M-2** | el hash muerto pasa a literal fijo | tripwire (PROCEDENCIA) **y** el pre-vuelo | **MUERTO** |
| **M-3** | el reloj de la fixture se suelta | el **aserto del INSTANTE** del pre-vuelo, **30/30 ROJO, 0 verde, 0 excepción** | **MUERTO, REPRODUCIBLE** |

### 1.1 M-1 — vuelve a `hash_real + "0"`

**Mutación** (1 línea, **desplazamiento 0**), `run_tests.py:23681`:

```python
-        hash_muerto, digitos_libres = _hash_muerto_por_construccion(d_hist, hash_real)
+        hash_muerto, digitos_libres = (hash_real + "0"), "0123456789abcdef"
```

**Suite completa** (`camara_m1`):

```
[suite_M1] rc=1 bytes=19092 lineas=238 s=958.1
ULTIMA LINEA: 'AssertionError: la suite construye un valor a partir de un hash real
POR CONCATENACION (la construccion que hace que el pre-vuelo dependa de la suerte:
`cat-file -e` resuelve cualquier prefijo de 8 hex, luego `hash_real + '0'` es el
objeto REAL cuando la 8.a cifra del sha es `0`, con P = 1/16). Hallazgos
(fichero:linea): ["run_tests.py:23681: hash_real + \'0\'"]'
```

**Y el pre-vuelo AISLADO** (N = 30: **30/30 ROJO, 0 verde, 0 excepción**, motivo
literal constante):

```
AssertionError: el hash muerto 296cfb20 (derivado; digitos libres 0123456789abcdef)
tiene que NO existir en esa fixture: se deriva por construccion, luego esto no puede
fallar por suerte. Y `cat-file -e` responde 128 con `fatal: Not a valid object name`...
```

**Y el tripwire AISLADO** (N = 30: **30/30 ROJO**, motivo literal constante):

```
AssertionError: la suite construye un valor a partir de un hash real POR CONCATENACION
(...). Hallazgos (fichero:linea): ["run_tests.py:23681: hash_real + '0'"]
```

→ **MUERTO por los dos lados**, y por la razón correcta: con el reloj clavado el
sha es `296cfb20…`, luego `hash_real + "0"` es **el objeto real** (`cat-file -e
296cfb20` → rc 0) y la aserción «tiene que NO existir» revienta. **Ninguna muerte
por excepción.**

### 1.2 M-2 — el hash muerto pasa a un literal fijo

**Mutación** (1 línea, **desplazamiento 0**), `run_tests.py:23681`:

```python
-        hash_muerto, digitos_libres = _hash_muerto_por_construccion(d_hist, hash_real)
+        hash_muerto, digitos_libres = "deadbee", "0123456789abcdef"
```

**Suite completa** (`camara_m2`):

```
[suite_M2] rc=1 bytes=19076 lineas=238 s=958.1
ULTIMA LINEA: "AssertionError: el hash bajo prueba NO viene de la derivacion por
construccion: [(23592, 'la derivacion por construccion `_hash_muerto_por_construccion`
no la llama nadie: el hash bajo prueba ha vuelto a ser un literal y el pre-vuelo
depende de la suerte')]. Sin derivacion el pre-vuelo vuelve a depender de la suerte
(P = 1/16 de que el hash exista)"
```

**Y el pre-vuelo AISLADO** (N = 30: **30/30 ROJO, 0 verde, 0 excepción**, motivo
literal constante):

```
AssertionError: el hash muerto deadbee tiene que VENIR de la derivacion (el hash
corto real 296cfb2 mas un digito): si no, ha vuelto a ser un literal y el pre-vuelo
depende de la suerte otra vez
```

**Y el tripwire AISLADO** (N = 30: **30/30 ROJO**, motivo literal constante):

```
AssertionError: el hash bajo prueba NO viene de la derivacion por construccion:
[(23592, 'la derivacion por construccion `_hash_muerto_por_construccion` no la llama
nadie: el hash bajo prueba ha vuelto a ser un literal y el pre-vuelo depende de la
suerte')]. Sin derivacion el pre-vuelo vuelve a depender de la suerte (P = 1/16 de que
el hash exista)
```

→ **MUERTO por los dos lados**, cada uno por su aserción. La derivación deja de
tener **quien la llame** (lo ve la regla (1) de `_delitos_de_procedencia_del_hash_muerto`)
y el pre-vuelo ve el literal. **Ninguna muerte por excepción.**

### 1.3 M-3 — el reloj de la fixture se suelta

**Mutación** (2 líneas, **desplazamiento 0**), `run_tests.py:23459-23460`: la
fixture deja de clavar `GIT_AUTHOR_DATE` / `GIT_COMMITTER_DATE`.

```python
     for v in variables:
-        os.environ[v] = fecha_iso
+        os.environ.pop(v, None)
```

**El pre-vuelo AISLADO, N = 30** (el criterio del ciclo: ROJO SIEMPRE):

```
[M3_previa_isla] test_el_pre_vuelo_de_un_hash_muerto_distingue_existe_de_no_existe x30 en 29.6s
[M3_previa_isla] VERDES=0 ROJOS(AssertionError)=30 OTRAS-EXCEPCIONES=0
[M3_previa_isla]   x30: AssertionError: el commit de la fixture tiene que llevar el INSTANTE
que la fixture declara (2025-01-01T00:00:43+00:00 = 1735689643 s) y el commit REAL lleva
1792655450 s: EL RELOJ DE LA FIXTURE NO ESTA CLAVADO. Sin esta asercion el pre-vuelo vuelve
a ser una moneda al aire, porque con el reloj suelto el sha es aleatorio y la 8.a cifra
solo acierta con P = 1/16
```

→ **30/30 ROJO, 0 verde, 0 excepciones, y el motivo literal es SIEMPRE el del
INSTANTE** (el número del epoch real cambia en cada corrida — 30 valores
distintos — pero la aserción es la misma). **M-3 muere por la CAUSA, no por la
suerte.** Este es el requisito nuevo del ciclo y se cumple.

**Suite completa** (`camara_m3`, `camara_m3b`, `camara_m3c`, `camara_m3d` — **4
corridas**):

| Corrida | rc | bytes | líneas | última línea | por qué murió |
|---|---|---|---|---|---|
| M3 | 1 | 18 955 | 238 | `AssertionError: el sha de la fixture (1cbe2213…) tiene que tener '0' en la 8.a cifra…` | el **tripwire** (8.ª cifra) |
| M3b | 1 | 18 957 | 238 | `AssertionError: el sha de la fixture (54b82a5b…) tiene que tener '0' en la 8.a cifra…` | el **tripwire** (8.ª cifra) |
| **M3c** | **1** | **28 002** | **366** | **`AssertionError: el commit de la fixture tiene que llevar el INSTANTE que la fixture declara (2025-01-01T00:00:43+00:00 = 1735689643 s)…`** | el **INSTANTE** (el tripwire pasó por suerte: su sha cayó con `0` en la 8.ª cifra) |
| M3d | 1 | 18 957 | 238 | `AssertionError: el sha de la fixture (ab78d72f…) tiene que tener '0' en la 8.a cifra…` | el **tripwire** (8.ª cifra) |

> ⚠️ **La atribución en la suite completa es distinta de la aislada, y hay que
> decirlo**: en `__main__` el **tripwire corre ANTES** del pre-vuelo
> (`run_tests.py:31366` frente a `run_tests.py:31511`), y el tripwire tiene una
> comprobación **probabilística** (la 8.ª cifra del sha, que con el reloj suelto
> acierta con P = 1/16). MEDIDO **aislado, N = 64**:
>
> ```
> [M3_tripwire_x64] VERDES=4 ROJOS(AssertionError)=60 OTRAS-EXCEPCIONES=0
> ```
>
> **4/64 = 6,25 % de verdes**, exactamente el 1/16 teórico. Y **M3c es la prueba
> empírica en la suite completa**: el tripwire pasó (su sha cayó con `0` en la
> 8.ª cifra por suerte), la suite siguió hasta el pre-vuelo y **murió por el
> aserto del INSTANTE** (366 líneas de log, 128 más que las otras tres: es la
> primera vez que el pre-vuelo habla).
>
> ⇒ **La suite completa es ROJA el 100 % de las veces con M-3** (4/4 corridas
> MEDIDAS), pero **el motivo que aparece en el log es el probabilístico 3 de cada
> 4 veces**. El veredicto es correcto; el *log* es el que hay que leer con la lupa
> del killer-check (TASK-087).

---

### 1.4 Supervivientes

| id | Superviviente | Severidad | Mutación exacta | Lo que hace falta |
|---|---|---|---|---|
| **T-1'** | **El conjunto de ficheros del tripwire se puede vaciar en silencio** | **MEDIA** (vigilancia de tooling, no datos ni seguridad) | `for patron in ("test_*.py", "*_test.py"):` → `for patron in ():` en `run_tests.py:23977` | Un **REGISTRO** (una cuenta, como el `REGISTRO_POR_CONSTRUCCION = 1` del guard de TASK-072) de los ficheros vigilados, derivado del disco: el `glob` no puede quedar en cero sin que la cuenta lo note. Es **TASK-088** (§6.2, H-C) |

**Los tres mutantes del encargo (M-1, M-2, M-3) NO son supervivientes**: mueren
los tres por su aserción, y M-3 **de forma reproducible** (30/30).

---


## 2. El flakiness: ¿es 0 con MI distribución?

### 2.1 El pre-vuelo sano, 200 corridas aisladas

```
[SANO_previa_x200] test_el_pre_vuelo_de_un_hash_muerto_distingue_existe_de_no_existe x200 en 224.2s
[SANO_previa_x200] VERDES=200 ROJOS(AssertionError)=0 OTRAS-EXCEPCIONES=0
```

**0 fallos de 200** (1,12 s por corrida). Con el reloj clavado, la fixture es la
**misma** en cada corrida (sha `296cfb20…`, MEDIDO), luego el hash muerto
derivado es el mismo: no hay ** nada aleatorio** que repartir.

### 2.2 La suite completa sana, 6 corridas

| Corrida | rc | bytes | líneas | última línea | asserts |
|---|---|---|---|---|---|
| base1 | 0 | 30 816 | 399 | `ALL TESTS PASSED.` | 0 |
| base2 | 0 | 30 816 | 399 | `ALL TESTS PASSED.` | 0 |
| base3 | 0 | 30 816 | 399 | `ALL TESTS PASSED.` | 0 |
| base4 | 0 | 30 816 | 399 | `ALL TESTS PASSED.` | 0 |
| base5 | 0 | 30 966 | 403 | `ALL TESTS PASSED.` | 0 |
| base6 | 0 | 30 966 | 403 | `ALL TESTS PASSED.` | 0 |

**0 fallos de 6**: 0 `AssertionError`, 0 `[FAIL]` real, y la última línea
`ALL TESTS PASSED.` en las seis.

> ⚠️ **Los logs NO son byte a byte idénticos, y hay que decirlo bien**: los 4
> primeros dan 30 816 B y base5/base6 dan 30 966 B y 4 líneas más. El diff línea
> a línea de base1 contra base5 (399 vs 403) da **42 líneas distintas**, y
> **TODAS** son de estas tres categorías, **ninguna** es un fallo:
>
> | Ruido | MEDIDO | Por qué varía |
> |---|---|---|
> | `invalid command name "<id>update"` | **8** líneas en base1–base4, **9** en base5/base6 | el **id** del widget de Tkinter lleva el **arranque del proceso en ms** (`2755497664512` vs `2306045640192`) |
> | `Optimizacion de escaneo OK (latencia minima: 3.37 ms)` | 1 línea | una **medida de latencia** en milisegundos |
> | el recuento de esas líneas de ruido | 8 vs 9 | el ruido de Tkinter headless depende del **número de callbacks** que caen tras destruir el widget |
>
> ⇒ **El veredicto de la suite es estable; lo que varía es el RUIDO del log.** Un
> `grep` de `[FAIL]` sobre estos logs da **2** líneas, y **ninguna** es un fallo:
> son los `print()` de dos tests que **verifican que un subproceso SÍ** produce un
> `[FAIL]` (`Journal ilegible OK: un solo [FAIL] en las dos formas…`). Por eso el
> veredicto se lee del **rc** y de la **última línea**, no de un `grep`.

### 2.3 La familia: ¿hay OTRO test flaky?

MEDIDO con `ast` sobre `run_tests.py` (**no** con una lista escrita a mano):

| Medida | Resultado |
|---|---|
| Call sites de `_repo_temporal_de_un_commit` (sha dependiente del reloj) | **20** (+ el `def` = 21) |
| Usos de `_objeto_existe_en_fixture` (valores bajo prueba) | **11** |
| De esos 11, los que dependen del **sha** | `sha_completo[:8]` (×2, control positivo), `hash_real`, `hash_muerto`, `derivado` → **los tres últimos son del pre-vuelo, y `hash_muerto`/`derivado` se derivan por construcción** |
| Los que son **literales fijos** | `HASH_MUERTO = "deadbee"` (`run_tests.py:21884`), `MUERTOS = ["deadbee","beefbee","cafebabe","badc0de","f00dfeed"]` (`run_tests.py:22011`), `'deadbee'` ×3 (en fuentes sintéticas del guard de TASK-072) |
| Concatenaciones con nombre de hash/sha en **todo** el fichero | **4**, y **ninguna** es «hash + dígito hex»: dos son texto de docstring, una es una concatenación de **listas** (`[{...}] + sin_hash_de_mas`) y la cuarta es `hash_impreso + '^{commit}'` (una **spec** de `rev-parse`, no un prefijo) |

**MEDIDO, 400 fixtures con la distribución DEL REPO** (mismo asunto, varias por
segundo), contradiciendo el reloj:

```
shas DISTINTOS: 287/400  (ensayos independientes: False)
fixtures con '0' en la 8.a cifra (los que rompian al codigo viejo): 16/400 = 4.00%
colisiones de los 5 literales fijos: {'deadbee': 0, 'beefbee': 0, 'cafebabe': 0, 'badc0de': 0, 'f00dfeed': 0}
```

- El **4,00 %** (16/400, IC95 de Wilson **[2,48 % ; 6,40 %]**) contiene el 1/16
  teórico (6,25 %): el mecanismo se reproduce con mi distribución.
- Los **287/400 shas distintos** reproducen la **correlación** que midió el
  arquitecto (293/300): en esta distribución los ensayos **no** son
  independientes, luego un intervalo binomial sobre 400 sería demasiado estrecho.
- **0 colisiones** de los 5 literales fijos en 400 fixtures: los valores bajo
  prueba que quedan en la suite **no dependen del reloj**.

⇒ **El daño era UNA aserción en UN test, y ahora es cero.** No hay otro test
flaky: **6/6** corridas de la suite completa en verde con **0 asserts**, **200/200**
corridas aisladas del pre-vuelo en verde, y **0** colisiones de los literales
fijos en 400 fixtures de la familia. Lo único que varía entre corridas es el
**ruido** del log (ids de widget con el arranque en ms y una latencia), nunca el
veredicto.

---


## 3. El tripwire del AC-4: ¿es viable?

### 3.1 ¿El conjunto de sujetos es DERIVADO o una enumeración escrita a mano?

**DERIVADO del disco, no enumerado.** `run_tests.py:23976-23978`:

```python
ficheros = [ruta_suite]
for patron in ("test_*.py", "*_test.py"):
    ficheros.extend(sorted(glob.glob(os.path.join(raiz, patron))))
```

El `glob` recorre el **disco**; lo escrito a mano son dos **patrones**, no una
lista de ficheros. MEDIDO (D-1'): con un fichero **vivo** en la raíz
(`sonda_test.py`, que casa con `*_test.py` y contiene `hash_real + '0'`), el
guard pasa a **ROJO** nombrando fichero y línea:

```
AssertionError: la suite construye un valor a partir de un hash real POR
CONCATENACION (...). Hallazgos (fichero:linea): ["sonda_test.py:3: hash_real + '0'"]
```

→ **D-1': el conjunto de sujetos se DERIVA y alcanza a los ficheros de test de la
raíz. No es la enumeración que este repo lleva dos ciclos persiguiendo.**

> ⚠️ **PERO el conjunto derivado es, hoy, un SINGLETON.** MEDIDO:
>
> | Hecho | Dónde | Consecuencia |
> |---|---|---|
> | el repo **prohíbe** los `test_*.py` en la raíz | guard `run_tests.py:12704-12711` (`f.name.startswith("test_") and f.name.endswith(".py")`) | el **primer patrón es MUERTO por construcción**: ningún `test_*.py` puede vivir en la raíz |
> | la raíz **no tiene** hoy ningún `test_*.py` **ni** ningún `*_test.py` | MEDIDO (13 `.py` en la raíz, ninguno casa) | el `glob` **no encuentra nada**: el conjunto derivado es `{run_tests.py}` |
>
> Es decir: la derivación es **real**, pero **su alcance vivo es de un solo
> fichero**. Eso no invalida el AC-4 (el fichero que importa es `run_tests.py`), y
> por eso el arreglo es **correcto**; pero sí fija el tamaño real del agujero de
> §3.2.

### 3.2 Mutar su alcance (dos formas)

| id | Mutación | Veredicto | Motivo literal |
|---|---|---|---|
| **T-1** | el `glob` de los ficheros de test se vacía (`for patron in ():`) → el tripwire solo mira `run_tests.py` | **EQUIVALENTE** en el repo real (hoy el `glob` no encuentra nada: vaciarlo **no cambia** el veredicto) — y **SOBREVIVIENTE** en cuanto hay un fichero que sí casa | con `sonda_test.py` presente: el guard queda **VERDE** y la concatenación **no se ve** |
| **T-1'** | T-1 **con** `sonda_test.py` en la raíz (la concatenación **existe**) | **SOBREVIVIENTE**, y confirmado **por suite COMPLETA** | suite completa: `rc=0`, 30 816 B, 399 líneas, última línea **`ALL TESTS PASSED.`**, 0 asserts — con la concatenación `hash_real + '0'` **presente en la suite** |
| **T-2** | el detector deja de recorrer los bucles anidados (`ast.walk(arbol)` → `list(arbol.body)`) | **MUERTO** | `AssertionError: el detector tiene que ver la concatenacion en la fuente sintetica:vio []` — lo mata la **contraprueba** del propio guard, no el detector |

> ⚠️ **T-1/T-1' es un agujero real y NO reabre el ciclo**: el conjunto de ficheros
> que vigila el tripwire **se puede vaciar en silencio**, y con él **se apaga la
> vigilancia de AC-4 fuera de `run_tests.py`**. La clase es la de A-C68-1 (un guard
> con un alcance que nadie cuenta) y la de D2/D3/P2 (un dato escrito a mano), pero
> en su versión más fina: **una lista de patrones**. Se encola como tarea nueva
> (§6.2), no como agujero de este fix.
>
> ⚠️ **Y un hallazgo de INSTRUMENTO que es también un dato del repo**: el primer
> intento de sonda (un `test_sonda_del_tripwire.py` en la raíz) murió en la
> **suite completa** por el guard de archivos legacy
> (`AssertionError: Se encontraron archivos test_*.py legacy en la raiz del
> repositorio: ['test_sonda_del_tripwire.py']`), **no** por el tripwire. Ese log
> (10 111 B) está **INVALIDADO** como veredicto y se conserva solo como dato: la
> sonda tiene que usar un nombre `*_test.py`, no `test_*.py`.

### 3.3 La contraprueba: las tres mitades

| Mitad | Qué exige | MEDIDO |
|---|---|---|
| (1) un sha+dígito que **sí** existe tiene que quedar **fuera** | `"0" not in libres` con la lista de objetos de la fixture | ✅ `libres=123456789abcdef`, el `0` fuera. Contra git: `cat-file -e 296cfb20` → **rc 0 (EXISTE)**, `296cfb21` → **rc 128** |
| (2) uno que **no** existe → **0 hallazgos** | `_hallazgos_de_concatenacion_de_un_hash_real(fuente_limpia) == []` | ✅ VERDE |
| (3) sin dígito libre → **reventar**, no lista vacía | `_digitos_libres_para_un_hash_muerto` con los 16 dígitos ocupados → `AssertionError` | ✅ `sin_digito=True` (la lista vacía en silencio está cerrada) |

Además, la contraprueba **mata a T-2** (§3.2) y detecta la concatenación por la
**IZQUIERDA** (`'0' + hash_real` → 1 hallazgo). El detector **tiene dientes**.

### 3.4 Su coste

| Medición | Resultado |
|---|---|
| Tripwire aislado, `ast.parse` instrumentado | **1 sola vez** sobre el fuente grande (`FUENTE-LARGA x1`) + 4 fuentes sintéticas ⇒ **no re-parsea por test** |
| Coste aislado, **máquina en reposo** | **4,52 s / 4,57 s / 4,56 s** (3 corridas) — el dev midió 4,50 s: **replicado** |
| Coste aislado, **con 7 suites en paralelo** | 6,08 s (la carga de CPU se nota) |
| Porcentaje de la suite | **0,62 %** de una suite de 735 s (4,55 s) — el dev dijo 0,61 % |
| Escala | O(ficheros del `glob`) y **no** O(tests): añadir un test al suite no encarece el guard |

> El `ast.parse` de `run_tests.py` (3,5 s según el dev) se paga **una vez**, al
> entrar en el guard, y su resultado no se cachea para otros guards — pero eso es
> coste de una sola suite, no un problema de escala.

---

## 4. La corrección del guard de TASK-072

La regla «toda llamada a `git cat-file --batch-check` necesita `input=`» era FALSA
para la forma `--batch-all-objects` (que no lee stdin). El arreglo mete esa forma
en una **cuarta categoría** (`por_construccion`) con **REGISTRO = 1** (una cuenta,
no una lista de líneas).

### 4.1 ¿La regla INTACTA sigue intacta?

| id | Mutación | Veredicto | Motivo literal |
|---|---|---|---|
| **G-1** | la excepción se **borra** (`if any(... "--batch-all-objects" ...)` → `if False:`) | **MUERTO** | `AssertionError: hay llamadas a `git cat-file --batch-check` SIN `input=` en las lineas [23549]` — la llamada real de `_objetos_de_la_fixture` vuelve a caer en `sin_input` |
| **G-2** | una llamada **prohibida nueva** en el fichero real (`subprocess.run(['git','cat-file','--batch-check'])`) | **MUERTO** | `AssertionError: hay llamadas a `git cat-file --batch-check` SIN `input=` en las lineas [31044]` — la regla **muerde** una infracción nueva |

→ **La regla intacta sigue verde-verde: una llamada a `cat-file --batch-check` sin
`input=` da ROJO, y la excepción no se ha comido la regla.**

### 4.2 ¿La contraprueba de dos mitades distingue las dos formas?

MEDIDO in-process (sonda sobre `_llamadas_cat_file_batch_check`, las dos formas
sintéticas):

| Estado | Forma CON `--batch-all-objects` | Forma SIN la opción | Mitad 1 | Mitad 2 |
|---|---|---|---|---|
| **Sano** | `sin_input=[] con_input=[] por_construccion=[1]` | `sin_input=[1] con_input=[] por_construccion=[]` | **OK** | **OK** |
| **G-3** (la excepción se come la regla: `if True:`) | `por_construccion=[1]` | `sin_input=[]` , `por_construccion=[1]` | OK | **ROTA** |

| id | Mutación | Veredicto | Motivo literal |
|---|---|---|---|
| **G-3** | la excepción de la cuarta categoría **se come la regla entera** (toda llamada a `--batch-check` cae en `por_construccion`) | **MUERTO** | `AssertionError: la deteccion real tiene que ver 15 llamadas en total y el bucle ha acumulado 1...` (el guard de TASK-072 ronda 3) — y la **contraprueba de dos mitades lo ve por su cuenta**: la mitad 2 pasa de `sin_input=[1]` a `sin_input=[]` |

→ **La contraprueba de dos mitades tiene dientes y distingue las dos formas.**

---

## 5. Higiene y citas

### 5.1 Identificadores sin definir (comprobador de ámbitos con `ast`)

| Estado | Resultado |
|---|---|
| **ACTUAL** `run_tests.py` | **0** |
| **ACTUAL** `validate_docs.py` | **0** |
| ANTERIOR (`a4d2775~1`) `run_tests.py` | **0** |
| **CONTROL POSITIVO** (nombre inyectado en el estado anterior) | **1** → `(2, 'nombre_que_no_existe_xyz', 'Load')` |

> ⚠️ El control que pedía el encargo («el estado anterior debe dar ≥1») **NO es
> satisfacible contra este historial**: el estado anterior (`a4d2775~1`) también
> estaba limpio, luego no hay ≥1 que sacar de ahí. El control **exigible** es el
> positivo, y pasa: el comprobador **detecta** un nombre inexistente. El
> criterio (c) se cumple igual: **0 identificadores sin definir**.

### 5.2 El recuento, derivado con `ast` (mismo algoritmo que `validate_docs.py`)

```
235 definidos = 235 invocados | reparto: 159 backend + 76 headless (suma 235)
solo_definidos=[]  solo_invocados=[]
```

Las **cuatro declaraciones** dicen lo mismo:

| Fichero | 235 | 159 + 76 |
|---|---|---|
| `AGENTS.md:70` | ✅ `# 235 tests headless (no abre ventanas)` | — (no declara el reparto) |
| `README.md` | ✅ `# 235 tests headless (no abre ventanas)` | — (no declara el reparto) |
| `STATUS.md` | ✅ | ✅ `**235 tests** (159 backend + 76 headless UI)` |
| `docs/ai/testing-guide.md` | ✅ | ✅ `**235 tests**: 159 de backend + 76 headless de UI` |

Las cuatro coinciden en la cifra; el **reparto** lo declaran las dos que lo
detallan (y las otras dos no lo declaraban antes del ciclo tampoco).

### 5.3 Citas por número de línea

| Cita | Qué dice | Estado |
|---|---|---|
| `run_tests.py:13235` | la tupla `ficheros` del guard de `llms.txt` | **VIVA** |
| `run_tests.py:17889` | `def _sin_contaminacion(d_repo, head_antes):` | **VIVA** |
| `run_tests.py:23133` | la línea que cita `sandbox-rules.md:55-56` (leída **en caliente**) | **VIVA** |
| `validate_docs.py:1429` | `# el contrato (`docs/ai/sandbox-rules.md:55-56`) lo documenta, no lo declara.` (leída **en caliente**) | **VIVA** |
| **`docs/ai/testing-guide.md:1362` → `run_tests.py:22264`** | la fila afirma que `run_tests.py:22264` es `test_las_citas_de_sandbox_rules_siguen_siendo_ciertas` | **FALSA** |

**MEDIDO el número real** (lo corrige el orquestador; el auditor **no** lo arregla):

- `run_tests.py:22264` **hoy** dice: `f"{sha_completo} commit 120") is not None, (`
- El test `test_las_citas_de_sandbox_rules_siguen_siendo_ciertas` está en
  **`run_tests.py:29006`** (MEDIDO con `ast`: `def` en la línea 29006, y es el
  único con ese nombre).

→ La cita de `docs/ai/testing-guide.md:1362` debe decir **`run_tests.py:29006`**.

### 5.4 Residuos

`run_tests.py`, `validate_docs.py`, `AGENTS.md`, `README.md`, `STATUS.md`,
`docs/ai/testing-guide.md`, `openspec/changes/2026-10-22-veredicto-de-no-medido/tasks.md`
y `.taskmaster/tasks.json`: **LIMPIOS** (0 CJK, 0 hangul, 0 `U+FFFD`, 0 soft
hyphen, 0 cirílico).

### 5.5 Docstrings: ¿mienten?

**NO. Verificado contra el código y contra git de verdad:**

| Afirmación del docstring | Verificación |
|---|---|
| «el reloj está **CLAVADO** … para que la fixture siga siendo **ADVERSARIA**» | ✅ `GIT_AUTHOR_DATE = GIT_COMMITTER_DATE = 2025-01-01T00:00:43+00:00` (`run_tests.py:23457-23460`), y el sha medido es `296cfb20fb7030f6f68afdfc508435be7a931b56` con **8.ª cifra `0`** |
| «el código viejo (`hash_real + "0"`) **MUERE el 100 %** con esta fixture» | ✅ `git cat-file -e 296cfb20` → **rc 0 (EXISTE)** |
| «el hash muerto se **DERIVA** … `cat-file -e` da rc 128 **POR CONSTRUCCIÓN**» | ✅ `cat-file -e 296cfb21` → **rc 128**; 15 de 16 dígitos libres, el `0` **fuera** |
| «la aserción de la 8.ª cifra **NO se afloja** … queda como la COMPROBACIÓN DEL ENTORNO» | ✅ está en `run_tests.py:23709-23717`, **detrás** de la del INSTANTE (`23693`), con su motivo escrito |
| «30/30 corridas en ROJO, las 30 con ESTE motivo literal y ninguna por excepción» | ✅ **remediado por el auditor**: 30/30 ROJO con el motivo del INSTANTE, 0 excepciones (§1.3) |
| «el codigo sano, 30/30 sin fallos» | ✅ **remediado**: **200/200** sin fallos (§2.1) |

---

## 6. El alcance del ciclo: qué NO tiene que estar resuelto

### 6.1 Lo que este ciclo **no** ha hecho (y sigue abierto)

MEDIDO sobre `.taskmaster/tasks.json` y sobre el diff de los dos commits
(`git diff --name-only a4d2775~1 1894f5d`):

| Tarea | Estado | Ficheros que este ciclo TOCÓ |
|---|---|---|
| **TASK-087** (contrato de veredicto en código: killer-check, `WOPT_VEREDICTO`, el texto de `proposal.md` §9 en `agent.md`) | **pending** | `.agents/agents/mutation-auditor/agent.md` **NO se ha tocado** (el `AGENTS.md` que aparece en el diff es el de la raíz, no el del agente) |
| **TASK-088** (guard derivado de la familia: las 21 fixtures con sha dependiente del reloj) | **pending** | — |
| **TASK-089** (guard de suite que detecte que el árbol se movió durante la corrida) | **pending** | — |

→ **Ninguna de las tres se ha implementado ni se declara cerrada aquí.** La
línea canónica `WOPT_VEREDICTO <mutante> <MUERTO|SOBREVIVIENTE|NO MEDIDO> <sha>`
**no existe todavía**, y por eso este informe no la emite (ver §0.5).

### 6.2 Los agujeros que deja el fix, y quién los puede cerrar

| # | Agujero | MEDIDO | ¿Quién lo cierra? | ¿El bucle puede pisarlo? |
|---|---|---|---|---|
| **H-A** | **El killer-check no existe.** El veredicto «MUERTO» sigue dependiendo de que el auditor lea el motivo literal del log. Con M-3 el log lleva **15/16** el motivo **probabilístico** (la 8.ª cifra del tripwire) y **1/16** el determinista (el INSTANTE): el veredicto es correcto, pero **el motivo del log es ruido 15/16 de las veces** | §1.3 | **TASK-087** (única) | **SÍ, en cualquier ciclo**: cada mutante se juzga por su log |
| **H-B** | **La familia no está vigilada.** El tripwire vigila la **concatenación**, no la **dependencia del reloj**. Un test nuevo que derive un valor bajo prueba del sha de una de las 20 fixtures (`hash_real[7]`, `sha[:8]`, …) **pasa** el tripwire | §2.3 | **TASK-088** (única) | **SÍ**: cualquier test nuevo que use `_repo_temporal_de_un_commit` |
| **H-C** | **El conjunto de ficheros del tripwire se puede vaciar en silencio** (T-1'): con `sonda_test.py` presente, el glob vacío deja pasar la concatenación sin que nadie lo note | §3.2 | **TASK-088** (o un guard nuevo con **REGISTRO**) | **SÍ**: cualquier commit que añada un `*_test.py` a la raíz |
| **H-D** | No hay guard de **suite** que detecte que el árbol se movió durante la corrida | — | **TASK-089** (única) | **SÍ**, pero es deuda de otro guard, no de este fix |

### 6.3 Vías nuevas que este ciclo descubre (se encolan, NO reabren el ciclo)

| id | Vía | Métrica | Por qué no reabre el ciclo |
|---|---|---|---|
| **V-1** | **El patrón `test_*.py` del tripwire es MUERTO por construcción**: el repo prohíbe los `test_*.py` en la raíz (`run_tests.py:12704`), luego ese patrón no puede encontrar nada jamás | MEDIDO: 0 `test_*.py` en la raíz; el patrón `*_test.py` **sí** es alcanzable (D-1' lo prueba) | El arreglo de TASK-083 es **correcto** y el AC-4 se cumple sobre `run_tests.py`. La limpieza de un patrón muerto es **higiene de un guard**, no un agujero del fix |
| **V-2** | **El tripwire del AC-4 tiene una comprobación PROBABILÍSTICA** (la 8.ª cifra del sha) que corre **antes** que el aserto determinista del INSTANTE (`run_tests.py:31366` vs `:31511`), y con el reloj suelto es VERDE **1 de cada 16** veces (MEDIDO 4/64) | 4/64 = 6,25 % verdes | La **muerte** del mutante es 100 % (la suma de las dos), pero el **motivo** del log es ruido 15/16. Es un problema de **killer-check** (H-A), o sea de TASK-087 |
| **V-3** | **La aserción de la 8.ª cifra es la que hace de "comprobación del ENTORNO"**, y depende del **formato del objeto commit de git** (autor, mensaje, versión). Si git cambiara ese formato, el pre-vuelo moriría **siempre** por un motivo que no es del mutante | MEDIDO: el sha `296cfb20…` se reproduce en este host con git real (`cat-file -e 296cfb20` → rc 0) | Es una **comprobación de entorno** legítima y explícita en el docstring; su coste es que una mudanza de git rompe la suite (ruido, no agujero) |

> **Regla aplicada:** una vía nueva **no reabre el ciclo**. Se encola con nombre y
> métrica y se reporta. La razón es la del panel: *un guard de forma sobre código
> propio nunca es perfectible, y un bucle que se queda indefinidamente en el
> mismo guard deja de producir hallazgos en cualquier otra parte.*

---

## 7. Veredicto de cierre del ciclo 69

### 7.1 El criterio, punto por punto

> **PASS** si: (a) el fix de TASK-083 aguanta; (b) M-1, M-2 y M-3 mueren por su
> aserción y de forma REPRODUCIBLE (M-3 con N ≥ 30, sin una sola verde);
> (c) 0 identificadores sin definir; (d) los docstrings no mienten;
> (e) higiene y recuento y citas.

| | Criterio | MEDIDO | ¿Se cumple? |
|---|---|---|---|
| **(a)** | El fix aguanta | M-1, M-2 y M-3 mueren **por su aserción**; el código sano **6/6** en verde y **200/200** aislado | ✅ **SÍ** |
| **(b)** | M-1, M-2, M-3 mueren por su aserción y de forma **reproducible** (M-3 con N ≥ 30, sin una sola verde) | M-1: pre-vuelo **30/30 ROJO** + tripwire **30/30 ROJO**; M-2: pre-vuelo **30/30 ROJO** + tripwire **30/30 ROJO**; M-3: pre-vuelo **30/30 ROJO**, 0 verde, 0 excepción, motivo siempre el del INSTANTE; y **suite completa 4/4 en ROJO** | ✅ **SÍ** |
| **(c)** | 0 identificadores sin definir | **0** en `run_tests.py` y en `validate_docs.py` (comprobador de ámbitos con `ast`; control positivo: detecta un nombre inyectado) | ✅ **SÍ** |
| **(d)** | Los docstrings no mienten | las 6 afirmaciones numéricas del docstring **verificadas contra git de verdad** (§5.5) | ✅ **SÍ** |
| **(e)** | Higiene, recuento y citas | 0 residuos; **235 = 235 = 159 + 76**; las 4 declaran 235; **una cita falsa** medida y su número real dado | ✅ **SÍ** |

### 7.2 Los tres mutantes, tabla final

| id | Qué rompe | Cómo lo maté | Veredicto |
|---|---|---|---|
| **M-1** | vuelve a `hash_real + "0"` | tripwire (FORMA: `run_tests.py:23681: hash_real + '0'`) **y** el pre-vuelo («el hash muerto 296cfb20 … tiene que NO existir») — 30/30 ROJO cada uno | **MUERTO** |
| **M-2** | el hash muerto pasa a literal fijo | tripwire (PROCEDENCIA: «la derivacion por construccion `_hash_muerto_por_construccion` no la llama nadie») **y** el pre-vuelo («el hash muerto deadbee tiene que VENIR de la derivacion») — 30/30 ROJO cada uno | **MUERTO** |
| **M-3** | el reloj de la fixture se suelta | el **aserto del INSTANTE** del pre-vuelo: «EL RELOJ DE LA FIXTURE NO ESTA CLAVADO» — **30/30 ROJO, 0 verde, 0 excepción** | **MUERTO, REPRODUCIBLE** |

### 7.3 Lo que este ciclo NO declara cerrado

- **TASK-087, TASK-088 y TASK-089 siguen `pending`** y **no** se han implementado.
- La **línea canónica `WOPT_VEREDICTO`** no existe todavía: este informe **no**
  puede emitirla (es lo que TASK-087 es).
- Los agujeros **H-A, H-B, H-C** (§6.2) y las vías **V-1, V-2, V-3** (§6.3) se
  **encolan**, no reabren el ciclo.
- **Un superviviente medido**: **T-1'** (el conjunto de ficheros del tripwire se
  puede vaciar en silencio; la suite completa queda **VERDE** con una
  concatenación `hash_real + '0'` **presente**). No es un agujero del fix de
  TASK-083 —es un agujero de **vigilancia** del AC-4— y su cierre natural es
  **TASK-088** (un REGISTRO derivado del disco, como el `REGISTRO_POR_CONSTRUCCION`
  del guard de TASK-072).

### 7.4 VERDICT

**VERDICT: PASS**

El fix de TASK-083 aguanta, los tres mutantes mueren **por su aserción** y M-3
muere **de forma reproducible** (30/30, sin una sola verde), y la higiene, el
recuento y las citas están medidos. El flakiness **medido** del pre-vuelo es
**0 de 200** y el de la suite completa es **0 de 6** con el único ruido medido
(ids de widget y una latencia).

> **El dato que este ciclo deja escrito para el bucle**: un mutante que muere el
> **95 %** **no cuenta como muerto**. MEDIDO aquí: el guard que se adelanta en
> `__main__` (el tripwire, con su comprobación de la 8.ª cifra) es **VERDE 4 de
> cada 64 veces** con el reloj suelto (6,25 %, el 1/16 exacto). La **muerte** del
> mutante no depende de eso —la suma de los dos guards es 100 %— pero el
> **motivo** que aparece en el log es ruido 15/16 de las veces. Un veredicto que
> lee un log tiene que exigir **el asa esperada**, no solo el rojo.

---

## 8. Inventario y verificación del repo real

### 8.1 Ficheros creados en `%TEMP%` (fuera del repo, ninguno commiteado)

Raíz: `%TEMP%\wopt_c69_aud\` (38 ficheros + 14 cámaras).

**Instrumento (scripts y sondas):**

| Fichero | Para qué |
|---|---|
| `setup_camara.py` | monta la cámara (`copytree` con `.git` excluido **como fichero**) + **prueba de aislamiento** |
| `reparar_indice.py` | replica el **índice del repo real** en la cámara (I-1) |
| `mutar.py` | catálogo de mutaciones (M-1, M-2, M-3, T-1, T-2, G-1, G-2, G-3) con **sustitución exacta** y purga de `__pycache__` |
| `lote.py` | corre N suites completas **en paralelo**, una por cámara |
| `correr_suite.py` | corrida suelta de la suite completa |
| `aislado.py` | ejecuta **un** test aislado N veces (subproceso nuevo por corrida) |
| `higiene.py` | identificadores sin definir (ast), recuento derivado, citas, residuos |
| `familia.py` | los 20 call sites con sha dependiente del reloj + 400 fixtures y colisiones |
| `verificar_docstring.py` | las cifras del docstring contra git de verdad |
| `coste_tripwire.py` + `sonda_coste.py` | coste del tripwire y **cuenta de `ast.parse`** |
| `sonda_mitades.py` | la contraprueba de dos mitades del guard de TASK-072, in-process |
| `viaje_tripwire.py` / `viaje_tripwire2.py` | el viaje de mutar → medir → restaurar |
| `apartar_sondas.py` | aparta los ficheros de sonda y re-verifica las cámaras |
| `resumir_logs.py` / `ruido_logs.py` / `reordenar.py` / `tareas.py` | resumen de logs, cuantificación del ruido, orden del informe, estado de tareas |

**Logs de suite (15):** `suite_base1..6.log` (30 816–30 966 B, VERDE),
`suite_M1/M2/M3/M3b/M3c/M3d.log` (18 955–28 002 B, ROJO), `suite_T1.log` y
`suite_T1p.log` (30 816 B, VERDE), `suite_T1_D1.log` (10 111 B, **INVALIDADO**:
murió por el guard de archivos legacy, no por el tripwire).

**Cámaras (14):** `camara_base*` (4), `camara_m1/m2/m3/m3b/m3c/m3d`,
`camara_trip`, `camara_t1`, `camara_t1d1`, `camara_t1p` — cada una con su
`.git` **propio** y desechable.

### 8.2 El repo real: NO ha sido tocado

Anclado **antes** de mutar nada y comprobado **al terminar**:

```
git rev-parse HEAD               -> 1894f5d08d8f332c741f6e33dff917916bad9aa2  (igual que el ancla)
git rev-parse --abbrev-ref HEAD  -> beta
git rev-parse --git-dir          -> C:\Users\carch\AppData\Local\woptimizer_git\.git
git diff --stat                  -> (vacio)
git diff --cached --stat         -> (vacio)
git reflog                       -> 314 lineas, ultima: 1894f5d HEAD@{0}: commit: fix(tools): ...
git status --porcelain           -> ?? openspec/changes/2026-10-22-veredicto-de-no-medido/mutation-report.md
```

- El **reflog no ha crecido** (314 antes, 314 después) y su última entrada sigue
  siendo el commit `1894f5d`: **ninguna cámara escribió en el historial real**.
- Lo único que aparece en `git status` es el **entregable de este informe**
  (fichero nuevo, sin trackear). **Cero escrituras** en `src/woptimizer/`, en
  `run_tests.py`, en `validate_docs.py` o en cualquier otro fichero versionado.
- **Nunca** se invocó `python .taskmaster/git_safe_commit.py` desde `%TEMP%` ni
  desde un cwd copiado (el wrapper impone `GIT_WORK_TREE = REPO_ROOT` y habría
  commiteado en el repo real con el árbol de la cámara).
- Las cámaras quedan **restauradas y verdes**: `camara_trip` con su `run_tests.py`
  **byte a byte igual** al original (SHA-256 idéntico) y el tripwire y el guard de
  TASK-072 **VERDES**; `camara_base` con el pre-vuelo y el tripwire **VERDES**.

---


