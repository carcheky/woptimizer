# TASK-070 — Tasks

Reference: `proposal.md`. Every number was measured on 2026-10-06.

## T1 — Add the two tests to `run_tests.py` BEFORE the fix

- `test_el_reparto_de_tests_no_re_tokeniza_por_sentencia`
  Count `ast.get_source_segment` / `tokenize.generate_tokens` invocations across
  `_reparto_de_tests(root)` on the real `run_tests.py`. Require **0**.
  Saves/restores the real functions in a `finally`. No timing assertion.
  *Measured to fail before the fix: 194 calls, required 0.*
- `test_el_split_derivado_no_cambia_con_el_arreglo`
  Reference implementation `_reparto_de_tests_via_source_segment` (identical loop
  with `get_source_segment`, ~6 s) — **test-only**, never imported by
  `validate_docs.py`. Assert the 4-tuples are equal on the **real** root.
  Run both derivations against `run_tests.py` itself, not only synthetic fixtures.

Both go in the `__main__` call list **before** the headless marker, alongside the
other tooling probes, and both are `print()`-quiet.
Expect: T2 green, T1 red (194 != 0).

## T2 — Replace the re-tokenization in `validate_docs.py:1028`

```python
lineas = fuente.splitlines()          # before the for, once
...
if MARCADOR_HEADLESS in "\n".join(lineas[stmt.lineno - 1:stmt.end_lineno]):
```

Nothing else in `_reparto_de_tests` changes. `MARCADOR_HEADLESS` keeps its
meaning. Do **not** hoist the search out of the loop (see T4, mutant M1).

## T3 — Green + measurements

- `python run_tests.py` -> all pass. T1 green, T2 green.
- `python validate_docs.py` -> `135 OK, 0 FAIL`, exit 0.
- `validate_docs.py` wall clock: expect ~13 s -> **~4 s** (the 8.7 s of the split
  derivation drops to ~0). Record the real number in the changelog; do **not**
  claim a 10-minute fix.
- `_reparto_de_tests` still returns `(140, 49, 189, 23863)`.
- `python verify_ui_syntax.py` untouched (no UI change).

## T4 — Mutation probes the `mutation-auditor` must close

| # | Mutation | Killed by |
|---|---|---|
| M1 | Hoist the marker search out of the loop: `visto = MARCADOR_HEADLESS in fuente` | T2 — returns `(0, 189, 189, None)` |
| M2 | Off-by-one slice: `lineas[stmt.lineno:stmt.end_lineno]` | T2 — drops the statement's first line; marker line 23863 is single-line, so this must be checked against a **multi-line** fixture too |
| M3 | Restore `get_source_segment` for the `antes`/`desde` counts | T1 — 194 calls |
| M4 | `break` after `visto` (the "optimization" rejected in the proposal) | T2 — `desde` truncates |
| M5 | Widen the slice to `lineas[stmt.lineno - 1:stmt.end_lineno + 1]` | **survives today** (0 overlaps, 0 semicolons); must be reported as a residual, not closed |

M5 is the honest one: on the current `run_tests.py` a one-line-too-wide slice is
indistinguishable from the correct one. It is a real property of the file, not a
guard. Document it, do not pretend a test covers it.

## T5 — Close the ticket with the corrected premises

`STATUS.md` debt section + `.taskmaster/tasks.json` TASK-070:
- status `completed`;
- note recording that "8-10 min" was **not reproducible** (12.85 s) and
  "~330 statements" is **194**, so a future reader does not re-derive the fix
  from a wrong number;
- keep the row honest: the validator still cannot run in CI (`STATUS.md:121`),
  untouched here.
- `CHANGELOG.md` and `.taskmaster/CHANGELOG.md`.

## Files

| File | Action |
|---|---|
| `validate_docs.py` | 2 lines: `splitlines()` before the loop, slice instead of `get_source_segment` |
| `run_tests.py` | 2 tests + reference impl + 2 calls in `__main__` |
| `STATUS.md`, `.taskmaster/tasks.json`, both `CHANGELOG.md` | closure |
| `src/woptimizer/**` | **untouched** |