# Tareas — Un veredicto de mutación no puede depender de un test no determinista

**Ciclo:** 69 · **Rama:** `beta` · **Tarea:** TASK-083
**Contrato:** `proposal.md` de este directorio.
**Cero ediciones bajo `src/woptimizer/`.**

---

## Qué hay que hacer (TASK-083)

Un único fichero de producción del fallo: el test del pre-vuelo de un hash muerto.

| # | Qué | Dónde | Discrimina porque |
|---|---|---|---|
| 1 | **Clavar el reloj de la fixture** a `2025-01-01T00:00:43+00:00` (`GIT_AUTHOR_DATE` = `GIT_COMMITTER_DATE`) y **afirmar** que su sha tiene `0` en la 8.ª cifra | `run_tests.py:23391` | El código viejo (`hash_real + "0"`) **muere el 100 %** con esa fixture (MEDIDO: `cat-file -e 296cfb20` → rc 0) |
| 2 | **Derivar el hash muerto por construcción**: elegir un dígito hex tal que `<short><d>` no sea prefijo de ningún objeto de la fixture | `run_tests.py:23415` | Con el dígito derivado el `cat-file -e` da rc 128 → `False` → **pasa el 100 %**; y el test lo dice si algún día no hubiera dígito libre |
| 3 | **Tripwire derivado con `ast`**: ninguna construcción "hash real + carácter" en la suite | `run_tests.py` (guard nuevo) | Si alguien devuelve `hash_real + "0"`, el guard **nombra** fichero y línea |
| 4 | **Docstring honesto**: por qué el reloj está clavado (para que la fixture siga siendo ADVERSARIA) y por qué el hash se deriva (para que no dependa de la suerte) | `run_tests.py:23371` | Sin las dos frases el arreglo se puede deshacer sin que nadie lo note |
| 5 | **Medición de cierre**: 200 ejecuciones seguidas del test aislado (**0,56 s** cada una → 112 s) con **0 fallos** | cámara en `%TEMP%` | 200 es el umbral para que el 1/16 no quepa; el arreglo lo deja en 0 sin mirar el número |

## Qué NO hay que hacer

- **NO** repetir la suite N veces: cuesta N × 790,3 s por mutante (N=3 → 8,6 h por
  ciclo) y, sin exigir consistencia, **empeora** el veredicto falso
  (`1-(1-p)^N`: N=3 → 17,6 %).
- **NO** escribir una lista a mano de tests "de evidencia": es la clase que este repo
  lleva dos ciclos persiguiendo.
- **NO** tocar `src/woptimizer/`.

## Encolado aparte (no cabe aquí)

| Tarea | Qué |
|---|---|
| **TASK-087** | El contrato de veredicto en código: killer-check, línea canónica `WOPT_VEREDICTO` y el texto de `proposal.md` §9 en `mutation-auditor/agent.md` |
| **TASK-088** | El guard DERIVADO que vigila la **familia**: las 21 fixtures dependientes del reloj y la regla de que ningún valor bajo prueba se derive de un valor dependiente del reloj |
| **TASK-089** | El guard de **suite** que detecte que el árbol se movió durante la corrida (hoy no existe) |

---

## Avance — TASK-083 implementada (ciclo 69, dev)

**Estado:** HECHO y MEDIDO. Cero ediciones bajo `src/woptimizer/`.

| # | Qué | Dónde | Evidencia medida |
|---|---|---|---|
| 1 | El reloj de la fixture del pre-vuelo queda **clavado** en `2025-01-01T00:00:43+00:00` (`GIT_AUTHOR_DATE` = `GIT_COMMITTER_DATE`) y el test **afirma** que su sha tiene `0` en la 8.ª cifra | `run_tests.py`: `_FECHA_ADVERSARIA`, `_ASUNTO_ADVERSARIO`, `_fixture_con_reloj_clavado` y el pre-vuelo | sha medido `296cfb20fb7030f6f68afdfc508435be7a931b56`; `cat-file -e 296cfb20` → rc 0 → el código viejo muere el 100 % |
| 2 | El hash muerto se **deriva por construcción**: `git cat-file --batch-all-objects --batch-check` y un dígito hex que no sea prefijo de ningún objeto | `run_tests.py`: `_objetos_de_la_fixture`, `_digitos_libres_para_un_hash_muerto`, `_hash_muerto_por_construccion` | 15 dígitos libres de 16; el derivado da rc 128 |
| 3 | **Tripwire derivado con `ast`**, contado como `test_*` | `run_tests.py`: `_hallazgos_de_concatenacion_de_un_hash_real`, `_delitos_de_procedencia_del_hash_muerto`, `test_el_hash_muerto_se_deriva_por_construccion_y_no_por_concatenacion` | 0 hallazgos en la suite real; en cámara desechable: ROJO nombrando `run_tests.py:23605: hash_real + '0'` |
| 4 | Docstring honesto con las dos frases | `run_tests.py`: docstring del pre-vuelo | (a) el reloj clavado mantiene la fixture **ADVERSARIA**; (b) el hash derivado **no depende de la suerte** |
| 5 | Medición de cierre | — | 200 ejecuciones aisladas del pre-vuelo → **0 fallos** (208,3 s; 1,041 s por corrida); guard: 4,67 s = **0,64 %** de la suite de 734,9 s |

### Un guard de otro ciclo tenía una regla FALSA (TASK-072)

`test_ninguna_llamada_de_cat_file_batch_check_se_queda_sin_input` (`run_tests.py:24221`) exige que toda llamada a `git cat-file --batch-check` lleve `input=`, porque esa primitive lee los nombres por **stdin** y sin `input=` responde rc 0 con stdout vacío (el falso verde que el guard vino a matar).

Esa regla era **falsa para la forma documentada `--batch-all-objects`**: con esa opción git **itera por los objetos del repositorio** y no lee stdin. MEDIDO contra el git de este host, con `stdin=DEVNULL` y **sin** `input=`: rc 0 y la lista **completa** de los objetos de la fixture (2: el commit y el árbol vacío) — frente a la forma sin la opción, que con la misma entrada vacía responde rc 0 con stdout vacío.

Y esa forma es la que exige el **AC-2 de esta misma tarea** (derivar el hash muerto por construcción listando los objetos), luego sin corregirlo la llamada válida se trataría como la primitive decorativa. El arreglo **no relaja** la regla: las llamadas de esa forma van a una **cuarta categoría** con su **propio registro** (una cuenta, no una lista de líneas) y su **contraprueba con las dos mitades** — la forma con `--batch-all-objects` cae ahí, y la *misma* llamada sin la opción vuelve a caer en `sin_input`, que es lo que prueba que la excepción no se ha comido la regla entera.

**Recuento:** 234 → **235 = 159 backend + 76 headless** (derivado con `ast`, el mismo algoritmo de `validate_docs.py`). El guard de AC-4 es un `def test_*` **contado** a propósito (lección A-C68-1: un guard que nadie cuenta se puede borrar sin que nada se entere). Las cuatro declaraciones de la cifra quedan actualizadas.

**Mutantes medidos por el dev** (cámara desechable en `%TEMP%`, nunca con el wrapper de commit):

| id | Qué rompe | Motivo literal | Veredicto |
|---|---|---|---|
| **M-1** | vuelve a `hash_real + "0"` | el tripwire: `Hallazgos (fichero:linea): ["run_tests.py:23605: hash_real + '0'"]` | **MUERTO** (tripwire + pre-vuelo) |
| **M-2** | el hash muerto pasa a literal fijo | el tripwire: `la derivacion por construccion `_hash_muerto_por_construccion` no la llama nadie` | **MUERTO** (tripwire + aserción de procedencia) |
| **M-3** | el reloj deja de estar clavado | el pre-vuelo: `el sha de la fixture (...) tiene que tener '0' en la 8.a cifra hexadecimal` | **MUERTO, pero PROBABILÍSTICO**: 61/64 corridas en rojo (95,3 %; teórico 15/16 = 93,75 %), las 3 verdes son las que casan con `0` por suerte |

**Lo que NO se ha cerrado:** `TASK-087`, `TASK-088` y `TASK-089` siguen encoladas. El guard de AC-4 sale **genérico sobre los ficheros de test de la raíz**, pero **no** enumera las 21 fixtures dependientes del reloj: eso es `TASK-088`, y no se cierra aquí.
