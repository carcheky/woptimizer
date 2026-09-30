# Tareas — cerrar F1 (ruta viva ilegible) y las deudas D1–D4

- **Change ID:** `2026-09-30-close-f1-unreadable-profile`
- **Alcance:** `run_tests.py` + `docs/ai/`. **`src/` intacto.**

## Bloque 1 — F1 (el arreglo principal, severidad DATOS DEL USUARIO)

- [x] **F1.1** Medir el estado de partida: los tres estados ilegibles, con el bloque sin tocar.
      *Salida:* 3 de 3 en ROJO por traceback (`UnicodeDecodeError` ×2, `PermissionError` ×1).
- [x] **F1.2** Medir la asimetría contra la app con el mismo fichero.
      *Salida:* la app arranca y recupera del `.bak` en los tres casos; la sonda moría en dos.
- [x] **F1.3** Extraer la lectura a `_leer_documento_de_packs()` (fuera de la sonda) para que el
      control pueda ejercitar **el mismo código** y no una copia.
- [x] **F1.4** Mover `open()`/`read()` **dentro** del `try`.
- [x] **F1.5** Invertir el **orden** de las ramas: `except (OSError, UnicodeDecodeError)` primero,
      porque `UnicodeDecodeError` es subclase de `ValueError`. *(Sin esto, la rama sigue muerta
      para la decodificación: medido como mutante `M-F1c`.)*
- [x] **F1.6** Añadir el control de alcanzabilidad: los tres ficheros ilegibles de verdad, con
      aserción sobre el **texto** del motivo y `PermissionError` real (directorio, no `chmod`).
- [x] **F1.7** Capturar la excepción en el control y convertirla en `AssertionError`, para que la
      muerte del mutante diga qué pasó en vez de dejar un traceback.

## Bloque 2 — deudas menores

- [x] **D1** `json.loads("null")` no lanza y devuelve `None`: cerrar el motivo vacío.
- [x] **D3** `visit_FunctionDef = pass` se saltaba defaults y decoradores, que **sí** se evalúan al
      importar. Medir cada forma contra el intérprete antes de decidir; recoger la firma, dejar el
      cuerpo; saltar anotaciones con `from __future__ import annotations`.
- [x] **D4** Un generador perezoso se marcaba como comprehension. Añadir `visit_GeneratorExp` que
      recorre solo el iterable de entrada.
- [x] **D3/D4** Filas nuevas en las tablas `ILEGALES` y `LEGALES`, **en las dos direcciones**, con
      el control positivo de que el cuerpo de un `def` y el `__future__` siguen sin marcarse.
- [x] **D2** `testing-guide.md`: decir que el detector solo mira la raíz `profiles` y por qué es
      correcto (la rama legacy de `pack_service.py:403/420` solo se engancha ahí).

## Bloque 3 — recuento que no miente

- [x] El `print` de la sonda llevaba `14 ilegales / 10 legales` escritos a mano. Derivar el
      recuento de `len(ILEGALES)` / `len(LEGALES)`, que es lo que lo mantiene cierto al añadir filas.

## Bloque 4 — verificación

- [x] `python run_tests.py` en verde, con el recuento de sondas subido.
- [x] `python verify_ui_syntax.py` en verde.
- [x] `python validate_docs.py` en verde.
- [x] Matriz de mutación F1/D1 **con control positivo** en cada fila.
- [x] Matriz de mutación D3/D4 con control positivo.
- [x] `__pycache__` purgada entre mutaciones (Trampa #18 de `docs/known-issues.md`).
- [x] Copias a `%TEMP%` excluyendo el puntero `.git`; backup explícito, nunca `git checkout` de un
      fichero gitignored.
- [x] Commit por `.taskmaster/git_safe_commit.py`, con el código de salida comprobado.

## Fuera de alcance — declarado, no arreglado

- [ ] **`test_headless_ui` sigue muriendo con un `PermissionError` en la ruta viva.** No es la sonda:
      es `pack_service.py:379`, que abre el fichero sin proteger frente a `OSError`, y
      `CORRUPTION_ERRORS` **no** incluye `PermissionError`. Es decir: **la app no tolera un
      `PermissionError`**, a diferencia de la corrupción de bytes. Requiere tocar `src/`, que este
      encargo prohíbe. Queda en `docs/ai/testing-guide.md` como hallazgo abierto con su medición.
