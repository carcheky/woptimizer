# tasks.md — Ancla de trazabilidad en el historial

Contrato completo en `proposal.md`. Orden estricto: T-1 antes que T-3, porque el cableado usa
las funciones que T-1 extrae.

## T-1. Las tres funciones, extraidas y testeables

**Por que `root` es parametro:** `validate_docs.py:163` hace
`root = os.path.dirname(os.path.abspath(__file__))` y `main()` no admite argv. Sin extraccion,
el check nuevo solo se despierta lanzando el validador entero contra el repo entero, que es
justo lo que `TASK-037`/`CYCLE-027` pago por no extraer `_comprobar_recuento_de_tests`.

- [ ] `_marcador_de_ciclo(asunto) -> int | None` — puro. Regex
      `\b(?:ciclo|cycle)s?\b[\s:#-]*#?(\d{1,4})`, case-insensitive, primera coincidencia.
      **No** puede leer `TASK-\d+` (ciclo 46 = TASK-056, medido).
- [ ] `_ciclos_de_commits(asuntos) -> (set[int], int, int)` — `(ciclos, marcados, sin_marcar)`.
- [ ] `_comprobar_ancla_de_commits(root, errors, ok) -> set[int]` — entorno espejo de
      `git_safe_commit.get_env()` (`.taskmaster/git_safe_commit.py:67-79`): `GIT_DIR` del entorno
      si existe, si no `%LOCALAPPDATA%\woptimizer_git\.git`; `GIT_WORK_TREE = root`.
      Un `git log --format=%s --all`. Un reintento ante fallo. Si no se puede leer: `errors.append`
      con el motivo literal y `set()` (**nunca** verde por omision). Si se lee y no aporta ciclos
      mientras el journal si: `errors.append` (parser roto != parser que no encuentra nada).
- [ ] Todas las cadenas de `print()` que se anadan, ASCII puro (trampa #16, consola cp1252).

## T-2. Union en el check 5b

- [ ] `ciclos_requeridos = ciclos_del_journal | ciclos_del_historial`.
- [ ] Por cada ciclo de `historial - journal`: `errors.append` nombrando el residuo
      ("hay trabajo COMITEADO y rd_journal.json NO lo registra").
- [ ] Sustituir la lista `missing_entries` (`validate_docs.py:401-405`) para que use la union.
- [ ] No tocar el resto del check 5b: la politica de journal ausente/corrupto/sin ciclos
      (`:340-379`) ya es correcta y ya esta probada.

## T-3. El test que discrimina

`run_tests.py`, un unico test, `GIT_DIR` a un repo temporal en `tempfile` (**nunca** el historial real).

- [ ] A1 subjects sinteticos con `ciclo #46 (TASK-056)` / `TASK-056` sin marcador / `cycle-43`
      -> `({43, 46}, 2, 1)`. Mata el mutante que parsea `TASK-`.
- [ ] A2 repo temporal con `chore(release): cerrar ciclo #47 (TASK-090)`, journal con el 46 y
      changelog sin `## CYCLE-047` -> dos `errors`, uno del journal y otro del changelog.
- [ ] A3 journal `{3}` + commits `{4}` -> se exigen los dos (union, no sustitucion).
- [ ] A4 `GIT_DIR` a un directorio que no es repo -> `errors` no vacio, sin excepcion, y el
      requisito del journal sigue exigiendose.
- [ ] Registrar el test en el `__main__` de `run_tests.py`.

## T-4. Recuento y documentacion

- [ ] `run_tests.py` 99 -> 100 en los cuatro ficheros de recuento: `STATUS.md`, `AGENTS.md`,
      `README.md`, `docs/ai/testing-guide.md`. El check 7 deriva la cifra con `ast`: si uno se
      queda atras, `validate_docs.py` falla.
- [ ] `docs/ai/sandbox-rules.md`: seccion nueva tras "### Cobertura" — la regla, el alcance
      (37 de 46 ciclos corroborables, 110 de 153 commits sin marcador) y **la limitacion
      residual tal cual esta en el §5 del proposal**, sin eupemismos.

## T-5. Verificacion antes de cerrar

- [ ] `python run_tests.py` en verde, 100/100.
- [ ] `python validate_docs.py` -> **`0 FAIL`** (criterio A5: la union no puede poner el repo real
      en rojo, porque los ciclos del historial {4..14, 21..46} son subconjunto de los 46 del journal).
- [ ] `python .taskmaster/git_safe_commit.py --verify` -> `WOPT_REPO_OK` + 0.

## Fuera de alcance (no lo hagas aqui)

- Verificar los hashes del campo `commits` del journal: **41 de 46 entradas no resuelven** y
  como FAIL deja el validador permanentemente rojo. Es `TASK-059`.
- Exigir el marcador de ciclo en `git_safe_commit.py`: cambia un contrato de codigos de salida
  normativo con su propio test. Es `TASK-059`.
- La seccion `## Deuda Tecnica Conocida` de `STATUS.md`, incluida la fila del residuo: es
  `TASK-058`, que depende de esta. Aqui solo se actualiza la cifra de recuento.
- `src/woptimizer/**`: cero cambios.
