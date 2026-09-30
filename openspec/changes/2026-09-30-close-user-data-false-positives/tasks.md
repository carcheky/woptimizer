# Tareas — `2026-09-30-close-user-data-false-positives`

Ciclo 21, iteración 4. Orden fijo: **lo que es dato de usuario, primero**.

## 1. S1 (DATOS) — N1 no exige JSON válido ni manda borrar el fichero del usuario

- [x] 1.1 Sustituir `except ValueError → raise AssertionError(...)` por la rama de **observación**:
      si el documento no se puede leer (inválido, vacío, ilegible, que no es un mapa), la sonda
      **no afirma nada** y avisa por `print()` con ruta y motivo.
- [x] 1.2 Reescribir el mensaje del caso v2 como observación. **Ningún mensaje de sonda termina en
      una instrucción de borrar el fichero del usuario.**
- [x] 1.3 Justificar en el comentario por qué un fichero corrupto **no** es evidencia de que el v2
      haya vuelto (estado local, gitignored, que la app ya tolera).

## 2. S2 (DATOS) — la firma del v2 es la combinación, no un campo suelto

- [x] 2.1 Extraer `_rasgos_del_esquema_v2_retirado(doc) -> (bool, rasgos)`.
- [x] 2.2 Rasgos contados **dentro del mismo registro**, y hacen falta **dos o más**:
      clave `__system_gaming__`, campo `factory`, campo `kill_low_chat`, `kind == "system"`.
- [x] 2.3 Tabla de control **negativo** (detector muerto): el archivado real tiene que detectarse.
- [x] 2.4 Tabla de control **positivo** (detector demasiado amplio): cinco documentos legítimos de
      usuario que **no** pueden disparar la guarda.
- [x] 2.5 Escribir el **riesgo residual** (dos campos v2 en un mismo registro de usuario) en
      `testing-guide.md`, para que no se lea como un olvido.

## 3. S3 (MEDIA) — el logger nombrado dentro de un bloque de módulo cuenta

- [x] 3.1 `_bloques_de_ejecucion()`: `body`/`orelse`/`finalbody` + `handlers` de `try` + `cases` de
      `match`.
- [x] 3.2 `_plano_de_ejecucion(bloque, dentro_de_clase)`: entra en los bloques, **nunca** en el
      cuerpo de una función, en el de una clase anidada ni en el de una lambda.
- [x] 3.3 Recoger los `Assign`/`AnnAssign` con esa vista en la recolección de loggers nombrados.
- [x] 3.4 Sustituir el `ast.walk` por `_NodosEjecutados` (NodeVisitor que no entra en funciones ni
      lambdas, y **sí** en el cuerpo de una clase). Falso positivo encontrado midiendo: una función
      anidada en un `if` de módulo se marcaba como configurada al importar.

## 4. S4 (MEDIA) — el cuerpo de una clase cuenta como `fuera`, y la doc deja de mentir

- [x] 4.1 `ClassDef` se reparte por su cuerpo, no entero a `dentro`.
- [x] 4.2 Corregir el docstring de `_configuraciones_de_logging`: "dentro de una **función**",
      nunca "de una función o una clase".
- [x] 4.3 Corregir `docs/ai/architecture.md` §15 con el criterio válido, escrito explícitamente para
      que no dependa de leer el docstring.
- [x] 4.4 Tablas `ILEGALES`/`LEGALES`: 8/6 → **14/10**, con las filas que fijan lo contrario
      (método de clase legal, función en `if` legal, lambda legal, comprehension ilegal).

## 5. Medición (obligatoria: cada fix muere con su mutación **y no mata de más**)

- [x] 5.1 Copia del repo a `%TEMP%` **excluyendo el fichero `.git`**, con
      `git rev-parse --absolute-git-dir` verificado antes de escribir y `git status --porcelain` del
      repo real comprobado al salir.
- [x] 5.2 Purga de `__pycache__` en cada escritura (Trampa #18: misma longitud + mismo segundo de
      mtime → `.pyc` obsoleto → veredicto falso).
- [x] 5.3 **Cada sonda en un subproceso** (`run_tests.py:8` reemplaza `sys.stdout`; importar la
      suite en el proceso del host cierra su buffer).
- [x] 5.4 **21 escenarios**: 7 controles positivos de dato (VERDE), 3 muertes de N1, 2 mutaciones
      del detector de v2, 2 muertes de S3/S4, 5 controles P de detector, 2 de re-verificación.
- [x] 5.5 Baseline de la copia en verde.

## 6. Documentación

- [x] 6.1 `docs/ai/testing-guide.md`: sección de la iteración 4 con la tabla de muertes **y** de
      controles positivos, la trampa del mutante S3 inválido, y la deuda de lectura de
      `test_headless_ui` (con su SHA-256).
- [x] 6.2 `docs/ai/testing-guide.md`: filas 59 y 64 de la tabla de 65 sondas al día.
- [x] 6.3 `docs/ai/architecture.md` §15: criterio válido + S3/S4.

## 7. Verificación y cierre

- [x] 7.1 `python verify_ui_syntax.py`
- [x] 7.2 `python run_tests.py`
- [x] 7.3 `python validate_docs.py`
- [x] 7.4 Commit con `python .taskmaster/git_safe_commit.py` y código de salida comprobado.

## 8. Lo que NO se hace (y por qué)

- [x] 8.1 `src/` **no se toca** en esta iteración.
- [x] 8.2 La deuda de lectura de `test_headless_ui` **no se arregla**: está medida y documentada.
- [x] 8.3 `M10` sigue como deuda aceptada (`architecture.md` §15).
- [x] 8.4 No se escribe en `rd_journal.json`, `CHANGELOG.md`, `.taskmaster/CHANGELOG.md` ni
      `STATUS.md` (los escribe el orquestador).
