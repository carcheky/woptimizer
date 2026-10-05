# TASK-070 — `validate_docs.py`: deriving the split without re-tokenizing per statement

## What is measured (host, 2026-10-06, not inherited)

Every number below was measured on the repo, not taken from the ticket.

| Claim in `TASK-070` | Measured | Verdict |
|---|---|---|
| A full run takes 8-10 min | **`validate_docs.py` = 12.85 s**, 135 OK / 0 FAIL (`Stopwatch` on the real process, and `validar(root)` = 12.96 s) | **FALSE** |
| ~330 statements in `__main__` | **194** (`ast` over `run_tests.py`, `cuerpo_main`) | **FALSE** |
| Split is `136 + 47 = 183` | **`140 + 49 = 189`** (`_reparto_de_tests` today) | **STALE** |
| `get_source_segment` re-tokenizes 1.1 MB per statement | **TRUE**: `_reparto_de_tests` = 8.7 s of the 12.96 s total (**67 %** of the whole validator) | TRUE |

So the defect is real and it dominates the run, but it is a **13-second** defect, not a ten-minute one. The ticket is wrong about the symptom, right about the cause. **Nothing in this change may be justified by the "8-10 minutes" figure: it does not exist, and a fix that restores the original latency will look successful while having fixed nothing.**

Why the ticket said 8-10 min: `python validate_docs.py` on a cold first read of a 1.2 MB file from the Nextcloud VFS, or a run overlapped with something else. Neither was reproduced.

## Where the time goes (measured per check)

```
_comprobar_recuento_de_tests        10.57 s
_comprobar_reparto_de_tests          7.74 s   <-- get_source_segment
_comprobar_deuda_con_anclas          2.51 s
_comprobar_hashes_del_journal        0.22 s
_comprobar_contrato_de_persistencia  0.00 s
```

`_recuento_de_tests` alone is 2.31 s (a single `ast.parse` of 1.2 MB). The split derivation is the only **per-statement** re-tokenization in the file.

## The defect

`validate_docs.py:1028`:

```python
if MARCADOR_HEADLESS in (ast.get_source_segment(fuente, stmt) or ""):
```

`ast.get_source_segment` calls `tokenize` on the **whole** 1.2 MB `fuente` and throws away every token outside `[lineno, end_lineno]`. It is called once per statement in `cuerpo_main`: 194 tokenizations of 1.2 MB = **O(n^2)** in the size of the file, not in the number of statements.

## Decision

`fuente.splitlines()` **once**, outside the loop, and one slice per statement:

```python
lineas = fuente.splitlines()          # once, O(n)
...
if MARCADOR_HEADLESS in "\n".join(lineas[stmt.lineno - 1:stmt.end_lineno]):
```

Measured: **6.14 s -> 0.0006 s** on the identical loop, and `(140, 49, 189, 23863)` in both. `end_lineno` is guaranteed populated by `ast.parse` since Python 3.8; the project requires 3.11+.

## The second optimizer: DO NOT TOUCH IT

`llamadas = sum(1 for nodo in ast.walk(stmt) ...)` at `validate_docs.py:1020` is **already O(n)**: the statements partition the body, so the sum of `walk(stmt)` over all of them visits each node once. Measured, the whole new loop — `ast.walk` included — is **0.0006 s**. There is no quadratic here to remove, and hoisting the `break` buys microseconds on a check that already takes 0.0006 s. Adding a `break` would trade a real correctness property (the counts after the marker are still needed) for nothing.

## Semantic risk, measured rather than assumed

Three ways a line-slice can diverge from `get_source_segment`:

1. **The marker split across two statements.** Impossible to be found by either implementation. `get_source_segment` returns the statement text verbatim, newlines included, so a marker straddling a statement boundary is not a substring of either. **No divergence.**
2. **A statement starting or ending mid-line** (`a = 1; print(M)`). The slice returns **more** than the statement. Divergence is real but only if two statements share a line, and only in the direction "the slice finds a marker that belongs to the neighbour's line". Measured on the real file: **0 line overlaps** among the 194 statement spans, **0 semicolons** in `__main__`. Not a hypothetical risk: it is a **measured zero** today, and it is a property of the file, not of the algorithm.
3. **The marker in more than one statement.** Measured: the marker appears **2 times in the file**, but only **once in `__main__`**. The other occurrence, `run_tests.py:13553`, is inside `_run_tests_sintetico()` — a function that *emits* a synthetic `run_tests.py`, well above `cuerpo_main` (which starts at line 23606). Both implementations return the **first** `__main__` hit, so a duplicate would behave identically under both.

**The measured danger is the optimization one step further.** Replacing the per-statement search with a single global `if MARCADOR_HEADLESS in fuente:` (or any "search once, hoist the check out of the loop") gives **`(0, 189, 189, None)`**: the synthetic-generator occurrence at line 13553 sits *above* `__main__`, so `visto` would be true before the first statement is counted and the entire suite would be declared headless. The total survives — which is exactly why it would go unnoticed. This is the mutation the test suite must kill.

## The no-change criterion

The figure STATUS.md declares (`STATUS.md:9`, `140 backend + 49 headless`) is derived by this function, so "the fix did not move it" is only provable by comparing two derivations of the **same function, on the same file, in the same run**:

```
_derivar_split_viejo(run_tests.py) == _derivar_split_nuevo(run_tests.py)
```

not "the new one gives 189". The latter is satisfied by a broken function that returns zeros. The comparison must be a 4-tuple: `(antes, desde, total, linea_marcador)` — the **split** and not just the total, because a moved split keeps the total intact by construction.

The existing guard `_comprobar_reparto_de_tests` (`validate_docs.py:1036`) already cross-checks the derived split against the literal in STATUS.md and already fails when the two derivations disagree on the total. **It stays as-is and is not duplicated**: it is the alarm that tells a human the number moved. What it cannot do is prevent the move, because it only runs after the code is written.

## Where the discriminating test lives: `run_tests.py`, not `validate_docs.py`

Three reasons, and the third is decisive:

1. `run_tests.py` is what CI executes (`verify` on Windows). `validate_docs.py` **cannot run in CI** — its commit anchor derives the repo from `%LOCALAPPDATA%\woptimizer_git\.git`, a path that exists only on the owner's host (open debt, `STATUS.md:121`). A test placed there would never run outside this machine.
2. A test that only runs where the bug is painful is a test that only runs after the fix is needed. The failure mode of a slow validator is "nobody runs it".
3. `run_tests.py` already owns the contract. The synthetic-fixture test of the split (`_run_tests_sintetico`, `run_tests.py:13535`, scenario **j** "the panel declares a split the `ast` disproves") is where this truth lives today, and `run_tests.py` already imports predicates out of `validate_docs.py` (`violaciones_del_contrato_de_persistencia`, the pattern of D1/D3). Importing `_reparto_de_tests` follows the established seam and adds no new coupling.

### The two tests

**T1 — `test_el_reparto_de_tests_no_re_tokeniza_por_sentencia`.**
Counts real tokenizations, not seconds. Monkeypatch `ast.get_source_segment` (and `tokenize.generate_tokens`) with a counting wrapper, run `_reparto_de_tests` on the **real** `run_tests.py`, and require the count to be **0**. A timing assertion would be flaky and would not survive a slower CI box; a call count is exact and host-independent.
*Fails without the fix*: today it counts **194** calls (one per statement) and the assert demands 0.
*Fails if over-optimized*: re-adding `get_source_segment` for any single statement, or restoring a whole-file scan, moves the count off 0.

**T2 — `test_el_split_derivado_no_cambia_con_el_arreglo`.**
Keeps the reference implementation (`_reparto_de_tests_via_source_segment`, `get_source_segment`, 6 s, **test-only**, never in production) and asserts `ref(root) == _reparto_de_tests(root)` as 4-tuples on the **real** file.
*Fails without the fix*: passes trivially before the change, **fails after any wrong change** — a global scan returns `(0, 189, 189, None)` and the tuples differ. That is the discrimination: T1 kills the quadratic, T2 kills the wrong repair of it.

Synthetic fixtures are **not** sufficient for T2 on their own: a synthetic file has no `_run_tests_sintetico`, hence **one** marker occurrence, so the global-scan mutant that breaks the real file passes on every synthetic. T2 must run against the real `run_tests.py` — and that is precisely what makes the second occurrence (line 13553) dangerous and therefore worth a test.

## Acceptance

- `_reparto_de_tests` returns `(140, 49, 189, 23863)` — measured, and whatever the split is after the change, T2 pins it to the reference.
- `python validate_docs.py` -> `135 OK, 0 FAIL`, unchanged.
- T1 and T2 exist in `run_tests.py`, both in the `__main__` list **before** the headless marker, so the split is regenerated honestly by the very function under change.
- The guard `_comprobar_reparto_de_tests` is untouched.

## Out of scope

- `src/woptimizer/**`: nothing. This is tooling.
- The `ast.walk` micro-optimizer: measured unnecessary.
- `validate_docs.py`'s CI exclusion (`STATUS.md:121`): separate debt, untouched.