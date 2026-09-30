# CYCLE-027 — tasks

Contrato: `openspec/changes/2026-09-30-guardas-que-no-guardan/proposal.md`.
Dueño: `openspec-dev`. Cero ediciones bajo `src/`.

- [ ] **T-27.1 — `_recuento_de_tests` puede emitir el estado que su consumidor espera.**
      `try/except OSError` sobre el `open()` y `try/except SyntaxError` sobre el
      `ast.parse()`, ambos devolviendo `None`. El resto de la función intacto.
      **Prohibido** `except IndentationError` (es subclase: estrecharlo reabre el
      agujero por el otro lado). **Prohibido** tocar la rama `if n_tests is None:` de
      `validate_docs.py:332` — ya está escrita para el contrato correcto; el que falta
      es el productor.

- [ ] **T-27.2 — Extraer `_comprobar_recuento_de_tests(root, errors, ok)`.**
      El cuerpo del check 7 (líneas 318-396) se mueve a esa función y `main()` la
      delega. Sin esto, T-27.1 no es testeable: la rama solo se despertaría lanzando
      el validador entero contra el repo entero. `main()` conserva su firma y su
      `sys.exit(0 if not errors else 1)`.

- [ ] **T-27.3 — Test del productor y de la rama viva** (en `run_tests.py`).
      Tres fixtures, todos sobre un árbol temporal mínimo:
      (a) `run_tests.py` con error de **indentación** → el validador emite una línea
      `[FAIL]` que nombra `run_tests.py` y **no** propaga excepción;
      (b) `run_tests.py` **ausente** → igual;
      (c) `run_tests.py` sano → devuelve la 4-tupla, no `None`.
      El (a) se escribe con sangría rota a propósito, porque es el caso que **medido**
      lanza `IndentationError`.
      El fixture (c) es el que obliga a exponer el conteo, y por tanto el que impide
      que M3 (rama muerta) sobreviva.

- [ ] **T-27.4 — Arreglar el mensaje del check 7** (`validate_docs.py:340-342`).
      `huerfanos` solo concatena el segmento de `solo_invocados` si esa lista no está
      vacía. Dos líneas. Se prueba **con el fixture (c) ampliado**: un `run_tests.py`
      con un test definido y no invocado tiene que producir mensaje **sin** el
      segmento `invocado y NO definido: .`.

- [ ] **T-27.5 — El guard de los llamantes pasa a ser función con raíz.**
      Se extrae de `test_el_feedback_de_pack_dice_la_verdad` a una función a nivel de
      módulo que recibe la raíz. El alcance se **deriva**: se recorren
      `src/woptimizer/**/*.py` con `ast` y se seleccionan los módulos cuyo
      `ImportFrom` termina en `feedback`. **Prohibido** dejar una tupla literal de
      ficheros en ninguna parte del guard.

- [ ] **T-27.6 — El guard acepta las DOS formas de llamada.**
      Hoy `getattr(llamada.func, "id", None)` (`run_tests.py:8130`) devuelve `None`
      para un `ast.Attribute` y la llamada se salta en silencio: un
      `fb.mensaje_sin_apps("N", "apagar")` pasa **sin marcar**. Resolver el nombre
      tanto si `func` es `ast.Name` como `ast.Attribute`.

- [ ] **T-27.7 — Control sobre árbol sintético (este es el test que cierra el ciclo).**
      Árbol temporal en `%TEMP%` con **cuatro** módulos:
      - `views/uno.py` e `views/dos.py`: importan `feedback`, conformes.
      - `views/tres.py`: importa `feedback` y cablea un **verbo** → el guard lo marca
        **nombrando fichero y línea**.
      - `panel.py` (fuera de `views/`): **no** importa `feedback` → no se marca.
      Control negativo obligatorio: `pack.default_action` y los literales `"start"` /
      `"kill"` (acciones válidas, `models.py:54`) **no** se marcan. Sin este criterio
      el guard podría marcarlo todo y quedarse "en verde".
      **Por qué árbol sintético y no el repo real**: con el repo real, mutar el
      alcance derivado a la tupla correcta de tres ficheros **no cambia ningún
      resultado** (medido: el tercer importador real solo usa `mensaje_cierre_pack`,
      que el guard no vigila). Solo un cuarto módulo sintético distingue "derivé el
      alcance" de "escribí el alcance correcto a mano". Ver mutante M5.

- [ ] **T-27.8 — Sincronizar el recuento de tests.**
      `validate_docs.py` deriva el número con `ast`, así que añadir tests **obliga** a
      actualizar `STATUS.md`, `AGENTS.md`, `README.md` y la tabla de
      `docs/ai/testing-guide.md` (una fila por test, numeración correlativa). El
      número se escribe en esos cuatro ficheros; **jamás** como constante en el
      validador. Sin esto, el check 7 da FAIL y el ciclo no cierra en verde.

- [ ] **T-27.9 — Mutaciones (Paso 4, `mutation-auditor`).**
      M1, M2, M3, M4, **M5**, M6, M7, M8, M9 de `proposal.md` §4.2, todas por
      `AssertionError`. Más el par combinado **M5+M4**. **El ciclo NO se cierra con M5
      vivo.**

- [ ] **T-27.10 — Higiene.**
      ASCII puro en todo `print()` nuevo. Emojis de categoría como escapes
      (`\U0001F7E1` para 🟡, `\U000026AA` para `⚪ Otros`; **nunca** `?` ASCII) —
      Trampa #16 y §Emojis de `docs/known-issues.md`. Nada de regex ni comillas
      mezcladas por `python -c` desde PowerShell (Trampa #18): fichero temporal.

## Fuera de alcance (deliberadamente, con motivo)

- **Punto (5), smoke test de compilación / `dist/woptimizer.exe`.** No es código, no lo
  puede hacer `openspec-dev`, no es mutation-auditable y `force_build.py` necesita
  `subprocess` en un entorno con `spawn EPERM` documentado. **Decisión de architect**
  (`proposal.md` §5.1): el checkpoint deja de ser un contador de ciclos y pasa a
  dispararse por condición (hay exe released y el código cambió desde el último
  build). Un checkpoint saltado cinco veces seguidas no es un checkpoint, es un 🟡 de
  adorno.
- **Punto (6), el validador no comprueba `docs/ai/`.** Cierto, y es el núcleo del
  **próximo** ciclo (Área 5, Testing & Calidad). **Decisión ya tomada** (§5.2): las
  afirmaciones documentales se verifican en `run_tests.py`, **no** en
  `validate_docs.py`, porque un check del validador no es mutation-auditable. El
  precedente ya existe: `test_la_documentacion_del_blindaje_no_puede_desfasarse`
  re-deriva con `ast` los 34 nombres de `SYSTEM_PROTECTED_PROCESSES` y vive en la
  suite.

## Pregunta al propietario (no bloqueante, respuesta por el orquestador)

¿`dist/woptimizer.exe` se usa a diario o es solo el artefacto que se descarga? Si se
usa a diario, el desfase de 15 ciclos es un riesgo real: el doble tap del ciclo 12 y
el blindaje anti-brick del 13 no están dentro. `architect-review` no puede decidirlo.
