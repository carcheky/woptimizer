# Ancla de trazabilidad en el historial: el validador no se deduce solo de quien escribe el registro

**Change ID:** `2026-10-01-validator-independent-anchor`
**Tarea:** `TASK-057`
**Alcance:** `validate_docs.py` (raiz) + `run_tests.py` + `docs/ai/sandbox-rules.md` + recuento de tests en 4 ficheros.
**NO toca:** `src/woptimizer/**` (cero cambios de codigo de producto).

---

## 1. La premisa de la tarea, corregida

`TASK-057` se escribio como "no hay ancla". **Eso es falso desde el ciclo #16**: el check 5b
ya exige una entrada `## CYCLE-NNN` **por cada ciclo** del journal y falla con mensaje explicito
si el journal falta, esta corrupto o no aporta ciclos (`validate_docs.py:332-417`). Lo que queda
vive no es la ausencia de ancla, es una **propiedad del ancla**: `rd_journal.json` lo escribe el
mismo orquestador que despues pide la validacion. Es un fichero distinto, no una fuente
independiente. El requisito de registrar el ciclo N se sigue deduciendo de un artefacto que
produce la misma pipeline.

Medido en el repo real (2026-10-01), 153 commits, 46 ciclos en el journal, 46 entradas
`## CYCLE-NNN` en `CHANGELOG.md`, `validate_docs.py` en `105 OK, 0 FAIL`.

## 2. Decision de diseno: testigo tercero, no testigo mejor

Se anade el **historial de commits** como tercera fuente del conjunto de ciclos exigidos, y el
requisito pasa a ser la **UNION**:

```
ciclos_requeridos = ciclos_del_journal | ciclos_del_historial
```

El historial esta fuera del arbol de trabajo (`%LOCALAPPDATA%\woptimizer_git\.git`), es
append-only y direccionado por contenido: para que el ciclo N deje de ser exigible hay que
reescribir historia, no editar una clave de un JSON. Es la maxima independencia alcanzable
**dentro de la banda**: sigue siendo el mismo actor, luego la limitacion residual se documenta
en vez de disfrazarse (ver §5).

Por que el historial y no otra cosa: el repo **ya tiene la convencion** de que el commit de
cierre de cada ciclo lleva el numero de ciclo en el asunto. Medido sobre los 153 subjects:

| Forma de asunto | Ejemplo real | Ciclos recuperables |
|---|---|---|
| `chore(release): cerrar ciclo #46 (TASK-056)` | `fbdf0ff` | 46 |
| `docs(cycle-43): cierre de ciclo 43` | `60caa7c` | 43 |
| `docs: registrar ciclo 37 en changelogs, journal y status` | `7923c47` | 37 |

**37 de 46 ciclos** son recuperables asi. Los 9 que no (1, 2, 3, 15, 16, 17, 18, 19, 20) no
restan: son ciclos cuyo commit de cierre no lleva marcador, y para ellos el journal sigue
siendo la fuente. La union no puede ser mas laxa que hoy, solo mas estricta.

## 3. Algoritmo

Tres funciones extraidas, con `root` como parametro, por el mismo motivo que
`_comprobar_recuento_de_tests` (CYCLE-027): `main()` de `validate_docs.py:163` deriva `root`
de `__file__` y no admite argv, asi que sin extraccion el check nuevo **no se puede testear**.

### 3.1 `_marcador_de_ciclo(asunto) -> int | None` (puro)

Regex: `\b(?:ciclo|cycle)s?\b[\s:#-]*#?(\d{1,4})`, case-insensitive, **primera coincidencia**.

**Prohibido** parsear `TASK-\d+`, y no por estilo: medido, el numero de tarea y el de ciclo
**divergen** (ciclo 46 = TASK-056, ciclo 45 = TASK-055, ciclo 44 = TASK-054). Un parser que
confunda ambos demanding `## CYCLE-056` pone el repo real en rojo.

### 3.2 `_ciclos_de_commits(asuntos) -> (set[int], int, int)`

`(ciclos, commits_con_marcador, commits_sin_marcador)`. El tercer numero se imprime en el
informe a proposito: el punto ciego se **mide** en vez de quedar verde.

### 3.3 `_comprobar_ancla_de_commits(root, errors, ok) -> set[int]`

- Entorno espejo de `git_safe_commit.get_env()` (`.taskmaster/git_safe_commit.py:67-79`):
  `GIT_DIR = os.environ["GIT_DIR"] or %LOCALAPPDATA%\woptimizer_git\.git`, `GIT_WORK_TREE = root`.
  El `GIT_DIR` del entorno se respeta **a proposito**: es el hook que permite tests hermeticos.
- Un unico `git log --format=%s --all` (sin limite: 153 subjects hoy; `--all` porque asi un
  ciclo cerrado en una rama tambien cuenta).
- **Un reintento** ante fallo, por el `spawn EPERM` intermitente. Si vuelve a fallar:
  `errors.append(...)` con el motivo literal y `set()` de retorno. Un ancla ilegible **no
  certifica**: es la misma politica que ya aplica al journal en `validate_docs.py:340-349`.
- Si el historial se lee pero **no aporta ningun ciclo** y el journal si: `errors.append(...)`.
  Un parser que no encuentra nada es un parser roto, y un parser roto en verde es el falso
  verde que esta tarea viene a matar.
- `ok.append(...)` con los tres numeros.

### 3.4 Cableado en el check 5b

Por cada ciclo de `ciclos_del_historial - set(journal_cycles)`, un `errors.append` **nombrando
el residuo**: hay trabajo comiteado y el journal no lo registra. Ademas, la lista de entradas
exigidas pasa de `journal_cycles` a la union (sustituye `validate_docs.py:401-405`).

## 4. Opciones evaluadas y DESCARTADAS (con evidencia)

| Opcion | Por que se descarta |
|---|---|
| **Anclar por fecha** (commits mas nuevos que la fecha del ultimo ciclo del journal) | **Medido y decorativo.** Las fechas del journal tienen resolucion de minuto y 5 ciclos comparten `2026-10-01T23:4x`; 152 de 153 commits son del mismo dia. Un ciclo 47 huerfano del mismo dia no se ve. |
| **Verificar que cada hash del campo `commits` del journal exista** (direccion inversa) | **La justificacion de este descarte era una MEDIDA FALSA, y se corrige en la iteracion 2.** Decia "41 hashes de 46 entradas NO resuelven"; remedido el 2026-10-02 extrayendo el hash (`\b[0-9a-f]{7,40}\b`) en vez de medir el string del campo, la realidad es: **11 de las 46 entradas no declaran hash alguno** (ciclos 1, 2, 14-20, 27, 28: `commits` a `null` o `[]`), 12 lo declaran como texto libre (`617eef8 (architect)`, ciclos 3, 8-12, 21-26) y solo 23 como lista limpia; de los hashes declarados **solo 3 no resuelven** (`5623629` del ciclo 30, `ee4b753` del 31 y `12b9c3bf` del 33), de modo que el ciclo 33 es el unico que queda sin ninguno resoluble y el check daria **1 FAIL, no 41**. El error de origen era medir el string entero del campo en vez del hash: los ciclos 3-26 SI corroboran. Sigue yendo a **TASK-059** como hallazgo, pero por su residuo real (11 entradas que no declaran nada que comprobar, 3 hashes perdidos con el `.git` corrupto del VFS) y no por una perdida permanente de 41 hashes que nunca existio. |
| **Encadenado criptografico de entradas del journal** (cada entrada hashea la anterior) | Detecta la reescritura retroactiva, **no** la omision: truncar la cadena al final es trivial. No toca el residuo de esta tarea. |
| **Auto-referencia** (tabla resumen del changelog, o el propio campo `commits` del journal) | Ya demostrado como falso verde en el ciclo #15. |
| **Puerta humana** (aprobacion del propietario por ciclo) | Es la unica independencia real, pero incompatible con la autonomia de coste 0 del proyecto y no automatizable. Se documenta como el unico cierre posible fuera de banda. |
| **Exigir el marcador de ciclo en `git_safe_commit.py`** (exit 1 si el mensaje no lo trae) | Es la unica via que cierra el agujero "nada dice que ciclo es", pero (i) toca un tool cuyo contrato de codigos de salida es norma documentada y tiene su propio test (`test_git_safe_commit_fail_safe`), (ii) queda fuera del alcance declarado de esta tarea, (iii) por si solo no detecta el residuo si el commit se etiqueta con un numero inventado. -> **TASK-059**. |

## 5. LIMITACION RESIDUAL (se documenta, no se disfraza)

Sigue siendo cierto, y hay que decirlo en `docs/ai/sandbox-rules.md`:

1. El historial es escrito por el mismo actor que el journal. La ganancia es de **clase de fallo**
   (reescribir historia frente a editar una clave), no de independencia de actor.
2. **112 de 155 commits no llevan marcador de ciclo** (los `feat(...)`, `fix(...)`, `test(...)`;
   medición del 2026-10-02, la cifra viva la reimprime el informe del validador).
   Si un ciclo se comitea **sin** commit de cierre y **sin** entrada de journal, no hay tercer
   testigo y el validador no lo ve. Cerrar esto es la tarea 059, no esta.
3. Un parser de marcador es una convencion leida, no una verdad: un asunto que mencione
   "ciclo 15" por hablar de el corrobora el 15. Solo puede **ablandar** el ancla, nunca
   endurecerla, asi que no puede producir un FAIL falso.

## 6. Criterios de aceptacion DISCRIMINANTES

Todos con `GIT_DIR` apuntado a un repo temporal: **ningun test toca el historial real**.

| # | Criterio | Por que el test MUERE sin el fix |
|---|---|---|
| A1 | `_ciclos_de_commits(["chore(release): cerrar ciclo #46 (TASK-056) x", "feat(quality): TASK-056 sin marcador", "docs(cycle-43): cierre de ciclo 43"])` -> `({43, 46}, 2, 1)` | El mutante que parsea `TASK-` devuelve `{43, 56}`: falla aqui **y** pone el repo real en rojo, porque `## CYCLE-056` no existe. |
| A2 | Repo temporal con un commit `chore(release): cerrar ciclo #47 (TASK-090)`, journal con solo el 46 y changelog sin `## CYCLE-047` -> **dos** `errors`, uno nombrando `rd_journal.json` (**por su conjunto: el 047, nunca el 046**) y otro el changelog; y su arbol espejo, journal `{46, 47}` con historial `{46}`, -> **cero** `errors` | Es el residuo literal de la tarea. Hoy el mismo arbol da `0 FAIL` porque el requisito sale del journal. Sin la union, el test ve `0` errors y muere. El arbol espejo es lo que mata la diferencia **invertida**: la asercion laxa por subcadena la dejaba pasar en verde mientras el validador accuse al reves (S1 del mutation-auditor). |
| A3 | La union no es una sustitucion: journal `{3}` + commits `{4}` -> se exigen **los dos** | Si se reemplaza journal por commits, el ciclo 3 pierde su requisito: es el falso verde del ciclo #15 renacido. |
| A4 | `GIT_DIR` a un directorio que no es repo -> `errors` no vacio, **sin excepcion**, y el requisito del journal sigue exigiendose | `except: return set()` silencioso es la misma clase de bug que la rama `if n_tests is None:` que era codigo muerto (CYCLE-027). |
| A5 | `python validate_docs.py` sobre el repo real -> `0 FAIL` | Un regex mal anclado que demande ciclos inexistentes rompe el repo real. Medido hoy: commits {4..14, 21..46} es subconjunto del journal, luego la union no anade requisito. |
| A6 | `run_tests.py` 99 -> 100, y los cuatro ficheros de recuento (STATUS.md, AGENTS.md, README.md, docs/ai/testing-guide.md) a 100 | El check 7 deriva el numero con `ast`; sin los cuatro, `validate_docs.py` falla. La iteracion 2 lo lleva a **104** por los cuatro tests de abajo. |
| A7 | `main()` REAL ejecutado como subproceso sobre un arbol temporal con un commit del ciclo 999 ausente del journal -> el informe acusa el 999, exige `## CYCLE-999` y sale con `1`; y el mismo validador con el cableado sustituido por `pass` **deja de acusarlo** | Sin este criterio, borrar la linea `_comprobar_ancla_del_changelog(root, errors, ok)` del cuerpo de `main()` deja la suite entera en verde y el validador mudo responde `0 FAIL`: es codigo testeado que el producto ya no invoca (S2 del mutation-auditor, la misma clase que TASK-056). La segunda mitad del test es la que demuestra que el test detecta ese fallo y no solo que hoy lo detecta. |
| A8 | `.taskmaster/rd_journal.json` que lanza `PermissionError` al leerse -> informe con el motivo y **un solo** error, sin excepcion | Estrechar `except (ValueError, OSError)` a `json.JSONDecodeError` deja el `PermissionError` fuera y el validador sale con traceback, sin comprobar nada de lo que viene despues (S5). |
| A9 | Sin `GIT_DIR` en el entorno, con un repo de verdad en un `%LOCALAPPDATA%` temporal -> el anclaje lo lee y devuelve su ciclo | El fallback `env.get("GIT_DIR") or expandvars(...)` no lo recorre ninguna sonda hermetica; borrarlo deja `None` en el entorno de `subprocess` y `TypeError: environment can only contain strings` (S3). |
| A10 | Historial legible con 0 ciclos con marcador: `[FAIL]` de parser roto si el journal aporta ciclos, y **silencio** si el journal esta vacio | La rama `if not ciclos and journal_cycles` no tenia cobertura: desactivarla entera o quitarle la condicion del journal sobrevivian cada una por su lado (S4). |

## 7. Ficheros a tocar

| Fichero | Cambio |
|---|---|
| `validate_docs.py` | `import subprocess`; `_marcador_de_ciclo`; `_ciclos_de_commits`; `_comprobar_ancla_de_commits`; union en el check 5b. Sin tocar el resto. |
| `run_tests.py` | `test_el_ancla_de_commits_no_depende_del_que_escribe_el_journal` + registro en `__main__`. **Iteracion 2** (mutacion-auditor dio `FAIL`): misma sonda con la sonda espejo A2b, mas `test_el_ancla_se_cablea_en_el_camino_real_del_validador`, `test_el_journal_ilegible_informa_en_vez_de_reventar_el_validador`, `test_el_ancla_de_commits_cae_al_git_dir_por_defecto` y `test_un_parser_de_marcadores_roto_no_pasa_en_verde`. |
| `docs/ai/sandbox-rules.md` | Seccion nueva "Ancla de trazabilidad en el historial" con la regla, el alcance y la limitacion residual del §5. **Iteracion 2**: tabla fix -> mutante -> veredicto, y las cifras del §4 corregidas (los "41 de 46 hashes no resuelven" eran una medicion falsa). |
| `AGENTS.md`, `README.md`, `docs/ai/testing-guide.md`, `STATUS.md` | Solo la **cifra** 99 -> 100. En `STATUS.md` **no** se toca la seccion `## Deuda Tecnica Conocida`: esa es de `TASK-058`. |
| `.taskmaster/CHANGELOG.md` + `CHANGELOG.md` + `rd_journal.json` | Los escribe el orquestador al cerrar el ciclo (paso 3 de la skill), no este cambio. |

## 8. Coordinacion

- `TASK-058` (saneamiento del panel) **depende** de `TASK-057`: la fila `STATUS.md:90` describe
  el estado previo ("deriva los ciclos de rd_journal.json") y quedara desfasada justo al cerrar
  esta. Serializado, sin colision: 057 toca la cifra de recuento, 058 las filas de deuda.
- `TASK-059` (nueva): direction inversa (hashes del journal) + marcador de ciclo obligatorio en
  `git_safe_commit.py`. Su evidencia se **corrige en la iteracion 2**: no son 41 hashes
  irrecuperables, son 3 hashes que no resuelven (`5623629`, `ee4b753`, `12b9c3bf`, el ultimo el
  unico de una entrada sin ninguno resoluble) y 11 entradas que no declaran hash alguno. Ver §4.
