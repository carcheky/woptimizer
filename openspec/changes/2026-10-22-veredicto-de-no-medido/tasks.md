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
