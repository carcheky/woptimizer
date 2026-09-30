# Cierre de los supervivientes del ciclo 21 (TASK-028 iteracion 2)

**Estado:** DISEÑO APROBADO (encargo del `mutation-auditor`, 2026-09-30).
**Auditoría de origen:** `mutation-auditor` sobre `HEAD=060fcc5`, 59 tests verdes, **16 supervivientes**
y **4 afirmaciones documentales falsas**. Este cambio **no reimplementa nada de TASK-028**: solo
cierra los agujeros que la auditoría encontró en lo que TASK-028_affirmó.

---

## 0. El patrón que estos hallazgos comparten

Tres de los hallazgos críticos (M4/M4b, M7, M11) son **la misma clase de defecto**:

> **Un validador que se deduce a sí mismo.** La sonda afirma algo que el propio fichero que
> afirma se deduce a sí mismo, así que ninguna mutación real puede detectarla.

- `run_tests.py` llama a `setup_logging()` en su `__main__` → la suite **se autoconfigurea** y el
  punto de entrada del producto le es invisible.
- La sonda de versión leía `pyproject.toml` + `__init__.py` y **escaneaba** los ficheros de
  empaquetado, pero no leía `.taskmaster/tasks.json`, que es el tercer sitio real.
- `data-models.md` afirmaba "rango 33-48, medido con `ast`" y nadie volvía a medirlo.

La regla que sale de aquí, y que se aplica a las sondas nuevas: **la expectativa se deriva del
código y la afirmación se contrasta con la fuente.** Un test que compara la doc consigo misma no
distingue nada; uno que mide el código y exige que la doc diga lo medido, sí.

---

## 1. M12 (+M13/M14/M15) — el archivo "de mentira" no está vigilado por nada

`git_safe_commit.py` deja constancia de que la regla existe. Lo que **no** existe es nada que la
haga cumplir: la auditoría lo comprobó borrando la línea de excepción y la suite siguió verde.

**Medido, y es el detalle que hace que esto sea crítico:** sin la excepción, `git add -A` se lleva
el fichero por delante y **desaparece del histórico sin error, sin aviso y sin `WOPT_FAIL`**. El
resultado es un directorio `docs/archive/` que existe en el disco de esta máquina y **no en el
histórico**: un archivo de mentira, que es exactamente el fallo que la norma "nunca borrar, siempre
archivar" dice impedir.

### La trampa de `check-ignore` (medida, no supuesta)

`git check-ignore` **por defecto mira el índice**, y un fichero ya versionado nunca se reporta como
ignorado: el test habría pasado **con la excepción borrada**, o sea sin distinguir nada. Y con
`--no-index` + `-v` el código de salida es **0** también para un patrón **negativo** (imprime
`!docs/...`): afirmar `rc == 0` sería afirmar lo contrario de lo que se cree.

Por eso la sonda usa **`-q --no-index`** (sin `-v`), donde el código de salida sí significa
"esta ruta está ignorada", y lleva un **control negativo** (`saved_processes.json`, que sí está
ignorado, debe dar `rc == 0`). Sin ese control, un `check-ignore` que no discrimina nada daría
verde igual: es la forma más silenciosa de test tautológico.

**Entorno:** el `.git` de este repo vive desacoplado en `%LOCALAPPDATA%\woptimizer_git\.git`
(el del árbol de trabajo está corrupto por el VFS). La sonda monta `GIT_DIR`/`GIT_WORK_TREE` con la
**misma precedencia** que `git_safe_commit.get_env()`; sin eso, `check-ignore` preguntaría al repo
 equivocado y daría verde por accidente.

### Qué afirma, y por qué cada afirmación discrimina

| Aserción | Mutación que muere |
|---|---|
| `git check-ignore -q --no-index` → `rc != 0` en los 3 ficheros del archivo | borrar `.gitignore:13` (la excepción) |
| `git ls-files --error-unmatch` → `rc == 0` en el `profiles.json` archivado | desversionarlo: el fichero sale del histórico en silencio |
| los 3 ficheros existen y el `README.md` **no está vacío** | vaciar el README (M14) o borrar el directorio (M15) |
| `inconsistencies_plan.md` **no** ha vuelto a la raíz | "desarchivar" devolviéndolo a la raíz |
| `profiles.json` **no** ha vuelto a la raíz | la copia del v2 muerto en la raíz: `.gitignore:7` la ignora, así que es **invisible a git** y desaparecería sin dejar rastro |
| control: `check-ignore` **sí** dice "ignorado" sobre `saved_processes.json` | una sonda que no puede detectar un ignore no prueba nada |

---

## 2. M7 (+M9, M10) — la versión tiene un tercer sitio que la sonda no veía

La garantía del ciclo dice *"TRES sitios, ya no pueden desincronizarse"*. La sonda leía dos y
**escaneaba** los ficheros de empaquetado con el filtro `if "version" not in linea`. Con
`.taskmaster/tasks.json` a `"0.0.1"` la suite declaró los tres sitios coherentes. Un test llamado
`…no_puede_desincronizarse` que deja vivo un desincronizador real es **peor** que no tener test:
da la falsa seguridad que el nombre promete.

### Ampliación del escáner (M9, M10) — sin falsos positivos medidos

El filtro pasa de "la línea contiene `version`" a una **dos condiciones**: la línea contiene un
literal semver **y** un token de versión (`\bver\b`, `\bversion(s)?\b`, `__version__`,
`--version`). Con `\b` no se cuela `Verificar` ni `servicio`. Medido sobre los tres ficheros de
empaquetado: `build.bat` solo contiene `v3` (que no es semver) y `force_build.py` ninguna versión;
el filtro **no produce ningún positivo hoy** y sí captura `ver = "9.9.9"` en `woptimizer.spec`
(M9). Además se añade un **escáner de `src/`** (Gate B): cualquier asignación a nivel de módulo
cuyo nombre case-insensitive termine en `version` o sea `ver`, con valor literal, tiene que estar
en `__init__.py` y llamarse `__version__` (cierra M10, que era un cuarto sitio vivo).

**Fuentes de la versión tras el cambio (medido):** `pyproject.toml:3`, `src/woptimizer/__init__.py:1`,
`.taskmaster/tasks.json:3` — las tres a `3.0.1.dev0`. Ninguna release `3.0.1` publicada existe: por
eso el sufijo `.dev0` y **no** se sube a `3.0.1`.

---

## 3. M4/M4b — el punto de entrada real no se prueba

`architecture.md` §15 declara como invariante que `setup_logging()` la invoca `__main__.main()`
**antes** de instanciar los servicios. Borrada esa llamada, la app arranca **sin log a fichero**:
los `logger.warning` caen al `lastResort` de la stdlib y salen por stderr. Verde.

**La causa no es un descuido, es una estructura:** la suite se llama a sí misma `setup_logging()`,
así que el validador se deduce a sí mismo. Es el ciclo #15 repetido.

La sonda nueva **no ejecuta** `main()` (arrancaría la UI): lee el **AST** de `__main__.py`, localiza
la primera llamada a `setup_logging` y la primera instanciación de servicio, y afirma que la
primera va **antes** que la segunda. Dos mutaciones, dos muertes distintas: *borrar la llamada*
mata por ausencia; *moverla debajo* mata por orden.

---

## 4. M18 + D1 — `PROCESS_LIST_FILE` sin guard vivo, y el comentario que miente

**D1 es la afirmación falsa más peligrosa del ciclo**, porque está en el fichero que el próximo que
abra `config.py` va a leer: el comentario dice que `smoke_check.py:23` "hace `assert` sobre el TEXTO
FUENTE de esta línea". **Verificado: el script muere en `:8` con `FileNotFoundError`** (lee
`process_manager.py`, que no existe) y **nunca alcanza** la línea 23. Uno de los cuatro consumidores
que nombra el comentario está muerto, y la razón que da para **no borrar** la constante es, en una
cuarta parte, falsa.

**D2** va en el mismo paquete: el criterio de aceptación 3 de `proposal.md` §12 de TASK-028 exige
`python smoke_check.py` en verde **sin haberlo tocado**. Es **imposible**: el script no tiene ruta
de ejecución verde. Un criterio que nadie puede cumplir es un criterio muerto, y el que lo "!cumple"
tiene que haber creado `process_manager.py`.

**Decisión:** el comentario de `config.py` se corrige para decir la verdad (3 consumidores vivos,
1 muerto) y se reemplaza la razón: la constante se conserva porque **la usan tres tests del root
protegidos por FIX-014**, no porque un script la vigile. El criterio D2 se marca muerto por escrito.

**Guard nuevo:** la sonda afirma, sobre el AST, (a) que `PROCESS_LIST_FILE` existe en `config.py` y
que su valor es `os.path.join(_app_dir(), 'saved_processes.json')` leído **del módulo**, y (b) que
los **tres** consumidores nombrados la referencian en su propio AST. Sin (a) la constante se puede
borrar en verde; sin (b), la constante sobrevive por(custom) 이유로 nadie puede verificar.

---

## 5. M10a-c / M11 — FIX-020 ("documentación sincronizada") no tenía ni una prueba

Cuatro mutaciones, cuatro verdes: la doc vuelve a decir `23-38`; la transcripción de 33 nombres se
desfasa; **una línea de comentario en el código invalida el rango `33-48`** que ambas docs afirman
como "medido con `ast`"; el código pierde un nombre real (`securityhealthservice`, 34→33).

**La sonda mide con `ast` y exige que las dos docs digan lo medido:**

- `ast` → `lineno`/`end_lineno` reales del `frozenset` → se exige que la cadena
  `process_service.py:<inicio>-<fin>` aparezca **en las dos** docs. (M10a, M10b, M11)
- `ast` → conjunto real de nombres → se compara **elemento a elemento** con los tokens
  entrecomillados de la transcripción de `data-models.md`. (M10c)
- El recuento declarado ("**34** entradas") se compara con `len(frozenset)`.

> **La expectativa se deriva del CÓDIGO, nunca de la doc.** Si se derivara de la doc, el test
> compararía la doc consigo misma y volvería a ser el validador que se deduce a sí mismo.

---

## 6. M3b — `RotatingFileHandler` → `FileHandler` plano sobrevive

`RotatingFileHandler` **hereda** de `FileHandler`, así que el `isinstance(h, logging.FileHandler)` de
la sonda T1 es cierto en los dos casos: la rotación no está probada y `architecture.md` §15 la
documenta como invariante. La sonda nueva afirma el **tipo exacto** (`type(h) is
RotatingFileHandler`) y los **atributos** (`maxBytes`, `backupCount`) contra las constantes
declaradas en `config.py`.

## 7. M16 — "config.py no configura nada al importarse" no se prueba

Reinyectar `logging.basicConfig(...)` a nivel de módulo deja la suite verde: la sonda T1 **limpia los
handlers después de importar**, así que por construcción no puede verlo. La sonda nueva mira el AST
de `config.py` y afirma que **no hay ninguna llamada a `basicConfig` fuera de una función**, con un
**control** que demuestra que el detector sí la encuentra dentro de `setup_logging` (si no, "no hay
ninguna" sería un verde por detector muerto).

---

## 8. M17a/M17b — mutantes EQUIVALENTES: no se testean

El arquitecto decidió no testearlos y la auditoría lo **confirma con medición**:

- **M17a (FIX-012):** `True if X else True == True` para todo `X`. Un test ahí sería decorativo.
- **M17b (FIX-016):** el `import sys` local de `quit_app()` se usa una sola vez, después del import.

Se dejan documentados como **equivalentes** en `docs/ai/testing-guide.md`. La diferencia entre "sin
cobertura" y "no hace falta" es exactamente esta frase.

---

## 9. Correcciones documentales (D1-D4)

| # | Fichero | Afirmación falsa | Corrección |
|---|---|---|---|
| **D1** | `src/woptimizer/config.py:68-71` | `smoke_check.py:23` "hace `assert` sobre el TEXTO FUENTE" | El script **muere en `:8`** con `FileNotFoundError` (lee `process_manager.py`, inexistente) y nunca llega a la 23. Consumidores **vivos**: los 3 tests del root. El guardia nuevo es la sonda, no el script. |
| **D2** | `openspec/changes/2026-09-30-task028-debt-cleanup/proposal.md` §12, criterio 3 | "`python smoke_check.py` en verde **sin haberlo tocado**" | Criterio **muerto**: no tiene ruta de ejecución verde. Se sustituye por el que sí se puede cumplir (y que ahora vigila una sonda viva). |
| **D3** | `docs/archive/legacy-root-data/README.md:44` | "`verify_task1.py:12` … pasado a `PackService(data_path=.)`" | `:12` define `TEST_FILE`; la instanciación es `verify_task1.py:15`, `PackService(data_path=TEST_FILE)`. El comportamiento afirmado es cierto; la **línea** no. |
| **D4** | `architecture.md` §11 y `data-models.md` | `is_system_protected('svchost')` como **función de módulo** | Es un **`@staticmethod` de `ProcessService`** (`process_service.py:330-336`): la forma escrita lanzaría `NameError` si alguien copiara la línea. El comportamiento afirmado es cierto; la **forma** no. |

---

## 10. Sondas nuevas (y por qué cada una discrimina)

Todas en `run_tests.py` (FIX-014: ningún `test_*.py` nuevo en la raíz).

| # | Sonda | Hallazgo | Por qué no es tautológica |
|---|---|---|---|
| **N1** | `test_el_archivo_legacy_esta_versionado_y_no_vuelve_a_la_raiz` | M12, M13, M14, M15 | Usa `check-ignore -q --no-index` (el que discrimina) y lleva control negativo; afirma sobre `rc`, no sobre "existe el fichero". |
| **N2** | `test_la_consulta_de_version_no_puede_desincronizarse` (ampliada) | M7, M9, M10 | Compara **tres** valores leídos de tres ficheros distintos, más un escáner con dos condiciones y un escáner de `src/`. |
| **N3** | `test_el_punto_de_entrada_declara_el_log_antes_de_los_servicios` | M4, M4b | Afirma sobre el **orden** de dos lineno del AST, no sobre "se chamou a `setup_logging`". |
| **N4** | `test_process_list_file_sigue_siendo_un_contrato` | M18 | Afirma que la constante **existe** (con su valor leído del módulo) y que los 3 consumidores la nombran. Sin la existencia, "los consumidores la usan" no se puede ni preguntar. |
| **N5** | `test_la_documentacion_del_blindaje_no_puede_desfasarse` | M10a, M10b, M10c, M11 | Mide con `ast` y compara contra la doc. La expectativa sale del **código**. |
| **N6** | `test_el_log_rota_con_el_limite_declarado` | M3b | `type(h) is RotatingFileHandler`, no `isinstance` (que distingue nada). |
| **N7** | `test_config_no_configura_nada_al_importarse` | M16 | AST + control que demuestra que el detector encuentra `basicConfig` dentro de `setup_logging`. |

**No se añade sonda** para M17a/M17b (§8) ni para M10 como categoría aparte (queda absorbido en N2).

---

## 11. Criterios de aceptación

1. `python run_tests.py` en verde, **65 sondas** (59 + 6 nuevas; N2 amplía una que ya
   existía, no la duplica) — o más, nunca menos.
2. `python verify_ui_syntax.py` y `python validate_docs.py` en verde.
3. **Cada** sonda nueva **muere con su mutación**, verificado en `%TEMP%` (copia del repo, árbol real
   intacto) y con `__pycache__` purgado entre mutaciones: sin purgar, Python reutiliza un `.pyc`
   obsoleto cuando el mutante tiene la misma longitud en bytes y el mismo segundo de mtime, y el
   veredicto sale **falso**. La muerte se confirma **por la aserción prevista**, nunca por
   `ImportError` ni por `FileNotFoundError`. **Medido: 21 mutaciones, 21 muertas, 0 supervivientes**
   (tabla en `docs/ai/testing-guide.md`).
4. `.gitignore:13` sigue ahí, y N1 lo vigila con el repo desacoplado correcto.
5. `.taskmaster/tasks.json` con `"version": "3.0.1.dev0"` y `TASK-028` en `"status": "completed"`.
6. `docs/ai/architecture.md`, `docs/ai/data-models.md`, `docs/ai/testing-guide.md` y el README del
   archivo reflejan lo implementado; **D1-D4 corregidos**.
7. `python .taskmaster/git_safe_commit.py "test(task028): cerrar supervivientes del ciclo 21"` con
   código de salida **0**.
