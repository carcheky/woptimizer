# TASK-072 — Plan de ejecución

Contrato: `proposal.md`. Todo lo de aquí lo ejecuta **`openspec-dev`** (Paso 3).
Cero ediciones bajo `src/woptimizer/**`.

---

## Orden de ejecución

### T1 · `stdin=DEVNULL` en el envoltorio — `run_tests.py:12756`

Añadir `stdin=subprocess.DEVNULL` a la llamada `subprocess.run` de `_git_de_fixture`,
**dentro del bucle de intentos** (no fuera): son 3 llamadas y las 3 heredan.

- [ ] `stdin=subprocess.DEVNULL` en la invocación de `run_tests.py:12754`.
- [ ] Comentario de 2 líneas explicando **por qué**: sin `stdin=`, el descriptor heredado
      decide el comportamiento, y con un pipe sin EOF `cat-file --batch-check` se bloquea
      leyendo. **Medido 2026-10-08** sobre una fixture propia: heredado-TTY 91,9 ms /
      pipe-abierto TIMEOUT a 15 s /
      `DEVNULL` 174 ms. Citar la cifra en el código: es lo que distingue esta fila de un
      comentario que afirma un cuelgue que aquí no ocurre.

### T2 · Helper de existencia — nuevo, junto a `_git_de_fixture`

`_objeto_existe_en_fixture(hash_, cwd) -> bool`, con `git cat-file -e <hash>`:

- [ ] `rc == 0` → `True`.
- [ ] `rc == 128` → `False` (respuesta legítima: el objeto no existe).
- [ ] otro `rc` → reintento (3 intentos) por `spawn EPERM`; agotados, `AssertionError`
      con el `stderr` literal, en la misma clave que el envoltorio: *un fallo de git no
      puedeFadeerse como falso verde*.
- [ ] `stdin=DEVNULL`, `timeout=120`, y la misma purga de `GIT_DIR` / `GIT_WORK_TREE`.
- [ ] Docstring que diga **por qué no se usa `_git_de_fixture`**: respondería 128 con
      `AssertionError` para un hash que sencillamente no existe, que es el caso legítimo
      que el pre-vuelo quiere detectar.

### T3 · Los dos call sites — `run_tests.py:20186` y `:20303`

- [ ] Ambos pasan a `assert not _objeto_existe_en_fixture(<hash>, d_hist)`.
- [ ] **Mensajes corregidos al signo real**: el texto actual dice «existe de verdad»
      mientras la operación afirma que **no**. El nuevo dice «**no** existe en la fixture».
- [ ] **Añadir el caso positivo** (este es el que mata la tautología, AC-3):
      `assert _objeto_existe_en_fixture(HASH_REAL, d_hist) is True`.
- [ ] **NO tocar** `run_tests.py:20189` (`git log --format=%h`): ya comprueba algo real y
      no lee stdin.

### T4 · Los tres tests

- [ ] **`test_el_envoltorio_git_no_hereda_stdin_y_no_cuelga_en_desatendido`** (§7.2 del
      proposal): padre con `os.pipe()` abierto que nunca escribe ni cierra; hijo que
      invoca el envoltorio **real** de `run_tests.py`; `communicate(timeout=10)`.
      El hijo ejecuta **dos** comandos — uno que no lee stdin (`rev-parse`) y otro que sí
      (`cat-file --batch-check`) — y el assert exige que **ambos** voltan.
      Sin el segundo, un arreglo que pase `stdin` solo en un camino sigue verde.
- [ ] **`test_el_pre_vuelo_de_un_hash_muerto_distingue_existe_de_no_existe`** (AC-3): con la
      fixture real de `:20179`, exige `HASH_REAL is True` **y** `HASH_MUERTO is False`.
- [ ] **Guard estructural** (AC-4): `ast` sobre `run_tests.py` real exige **cero** llamadas a
      `cat-file --batch-check` **sin** `input=`. El bucle tiene que distinguir «la llamada
      lleva `input=`» de «no lo lleva», no solo contar coincidencias de texto.

### T5 · Documentación y recuento

- [ ] `STATUS.md:101`: cerrar la fila 🔴 de TASK-072 **conservando la redacción original**
      y corregiendo el verbo; añadir el hallazgo del tautológico (§2 del proposal).
- [ ] Si el check 7 lo exige: actualizar **los cuatro** declarantes del recuento
      (`STATUS.md`, `AGENTS.md`, `README.md`, tabla de `docs/ai/testing-guide.md`) a la
      cifra derivada. **Los cuatro o ninguno** — el check 7 deriva con `ast` y falla si uno
      se queda atrás.
- [ ] `docs/ai/testing-guide.md`: una fila por test nuevo, **al final** de la tabla (las
      nuevas se agregan al final para no renumerar las anteriores).

---

## Verificación de cierre

| Comprobación | Resultado esperado |
|---|---|
| `python run_tests.py` | `ALL TESTS PASSED`, sin congelarse en el check 9 |
| `python validate_docs.py` | `0 FAIL`; el reparto derivado no cambia de par |
| Guard estructural AC-4 | 0 llamadas `--batch-check` sin `input=` |
| `git_safe_commit.py` | exit 0; mensaje **con** `(TASK-072)` |

## Paso 4 — mutantes que tienen que morir (obligatorio)

| # | Mutante | Por qué muere |
|---|---|---|
| **M1** | quitar `stdin=DEVNULL` de `_git_de_fixture` | el test desatendido: `TimeoutExpired` (medido 15 s sin arreglo) |
| **M2** | `cat-file -e` → `cat-file --batch-check` sin `input=` | AC-3: `HASH_REAL` no está en la salida vacía |
| **M3** | el helper devuelve `False` siempre | AC-3: el caso positivo `HASH_REAL is True` |
| **M4** | borrar el guard estructural | AC-4: el `ast` encuentra la llamada sin `input=` |

**M3 es el que justifica el caso positivo**: sin él, «siempre `False`» y «siempre `True`»
son la misma respuesta para un test que solo mira el hash muerto.

---

## Lo que NO se toca (y por qué)

- `validate_docs.py:523` — su `cat-file --batch-check` **lee stdin legítimamente**
  (`input=` con ~100 hashes del journal en una llamada). Cambiarlo sería un desatino contra
  su propio docstring (`validate_docs.py:466`): un `cat-file -t` por hash serían ~100
  subprocesos.
- `timeout=120` — no causa el cuelgue, lo acota. Con T1 y T2 desaparece la causa; bajarlo
  solo añade falsos negativos en un host con VFS. Medido: 90–105 ms reales contra 120 s.
- `run_tests.py:20189` — ya comprueba, no lee stdin.
- `src/woptimizer/**`, `.github/workflows/**`, `dist/`.

## Riesgo asumido, escrito

Al convertir dos decorativos en comprobaciones reales, el check 9 pasa a depender de que la
fixture tenga el commit. **Esa dependencia ya existía** (`run_tests.py:20189` la exigía), pero
ahora hay **dos** comprobaciones donde había un decorativo: si alguien vacía la fixture, el
síntoma pasa a ser de git y no de aserción. Anotado en `STATUS.md` para que no se lea como
riesgo nuevo.