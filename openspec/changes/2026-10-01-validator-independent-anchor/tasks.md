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
      (37 de 46 ciclos corroborables, 112 de 155 commits sin marcador, medición del 2026-10-02) y
      **la limitacion residual tal cual esta en el §5 del proposal**, sin eupemismos.

## T-5. Verificacion antes de cerrar

- [ ] `python run_tests.py` en verde, 100/100.
- [ ] `python validate_docs.py` -> **`0 FAIL`** (criterio A5: la union no puede poner el repo real
      en rojo, porque los ciclos del historial {4..14, 21..46} son subconjunto de los 46 del journal).
- [ ] `python .taskmaster/git_safe_commit.py --verify` -> `WOPT_REPO_OK` + 0.

## Fuera de alcance (no lo hagas aqui)

- Verificar los hashes del campo `commits` del journal: **medido el 2026-10-02**, 11 de las 46
  entradas no declaran hash alguno y solo **3 de los hashes declarados no resuelven**
  (`5623629` del 30, `ee4b753` del 31, `12b9c3bf` del 33), o sea **1 entrada sin ningún hash
  resoluble**: el check daría 1 FAIL, no los "41 de 46" que este documento afirmaba (era medir el
  string `617eef8 (architect)` en vez del hash). Sigue fuera de alcance y es `TASK-059`, ahora por
  su residuo real y no por una pérdida permanente inexistente.
- Exigir el marcador de ciclo en `git_safe_commit.py`: cambia un contrato de codigos de salida
  normativo con su propio test. Es `TASK-059`.
- La seccion `## Deuda Tecnica Conocida` de `STATUS.md`, incluida la fila del residuo: es
  `TASK-058`, que depende de esta. Aqui solo se actualiza la cifra de recuento.
- `src/woptimizer/**`: cero cambios.

## T-6. Iteracion 2 — cierre de los hallazgos del mutation-auditor (`FAIL`, 12 supervivientes)

El `mutation-auditor` ejecuto 28 mutaciones y dio 16 muertas / 12 vivas. De los 12
supervivientes, estos son los que tocaban a este cambio. El codigo del validador **no se
tocó**: en los cinco casos la cobertura era la que faltaba, no la logica.

- [x] **S1 (CRITICO)**: el residuo se comprueba por su **conjunto**, no por una subcadena laxa.
      La asercion nueva exige que la linea de error nombre el `047` y **no** el `046`, y se anade
      la sonda espejo **A2b** (journal `{46, 47}` con historial `{46}` -> `0` errores), que es el
      unico arbol donde acusar es por construccion acusar al reves. Mata
      `ciclos_historial - ciclos_journal` -> `ciclos_journal - ciclos_historial`.
- [x] **S2 (CRITICO)**: `test_el_ancla_se_cablea_en_el_camino_real_del_validador`. Ejecuta el
      `validate_docs.py` **real** como subproceso contra un arbol temporal (copia del esqueleto
      que `main()` lee) y exige que acuse un residuo real; su mitad mutante corta el cableado y
      exige que el residuo desaparezca. Mata borrar `_comprobar_ancla_del_changelog(root, errors,
      ok)` del cuerpo de `main()` —justo el criterio A5, que era una afirmacion y no un test.
- [x] **S5 (MEDIO)**: `test_el_journal_ilegible_informa_en_vez_de_reventar_el_validador`.
      `PermissionError` inyectado en el `open` del modulo: informe con el motivo y un solo error,
      sin traceback. Mata `(ValueError, OSError)` -> `json.JSONDecodeError`.
- [x] **S3 (MEDIO)**: `test_el_ancla_de_commits_cae_al_git_dir_por_defecto`. Sin `GIT_DIR` en el
      entorno, con repo real en un `%LOCALAPPDATA%` temporal. Mata la supresion del fallback.
- [x] **S4 (MEDIO)**: `test_un_parser_de_marcadores_roto_no_pasa_en_verde`. Dos sondas sobre el
      mismo historial: `[FAIL]` de parser roto si el journal aporta ciclos, silencio si esta
      vacio. Mata desactivar la rama y quitarle `and journal_cycles`.
- [x] **Cifra falsa corregida**: los "41 de 46 hashes no resuelven" no eran ciertos. Remedidos
      con el hash extraido (`\b[0-9a-f]{7,40}\b`): 11 entradas sin hash, 3 hashes que no resuelven,
      1 entrada (ciclo 33) sin ninguno resoluble. Corregido en los cinco sitios que lo
      declaraban: `docs/ai/sandbox-rules.md`, `proposal.md` (x2), este `tasks.md` y
      `.taskmaster/tasks.json` (notas de TASK-057; descripcion, criterios y notas de TASK-059).
- [x] **Conteos de la doc viva**: 154/111 -> 155/112 subjects, con la fecha de medicion y la nota
      de que la cifra caduca con cada commit y la reimprime viva el informe del validador.
- [x] **Marcador de ciclo en los commits de este ciclo**: `chore(release): cerrar ciclo #47
      (TASK-057)`, para que el ciclo 47 se corrobore por el historial y no solo por el journal. Los
      dos commits anteriores del ciclo 47 (`9aa7dd5` arquitectura y `dbe720d` codigo) NO lo llevan y
      no se pueden reescribir sin reescribir historia: quedan como punto ciego declarado.
- [x] `run_tests.py` 100 -> 104 y los cuatro ficheros de recuento sincronizados.

## T-7. Iteracion 3 (re-planificacion del Circuit Breaker) - UN solo camino de validacion

El `mutation-auditor` dio `FAIL` dos veces. La segunda mato las 6 declaradas y encontro 3
supervivientes **en el codigo que el propio ciclo anadio**. Midiendo el producto real con
copias mutadas (`validate_docs.py` ejecutado de verdad sobre un arbol copiado), el patron se
cierra en un numero: **con el parser de marcadores muerto Y el 4o argumento sin pasar, el
validador da `108 OK / 0 FAIL`.** El fix S4 es codigo MUERTO en el camino real.

### La leccion, en una frase

`validate_docs.py:371` llama `_comprobar_ancla_de_commits(root, errors, ok, journal_cycles)`
y la funcion declara `journal_cycles=()` por defecto (`validate_docs.py:213`). El test de S4
(`run_tests.py:12357`) llama a la funcion **PRIVADA pasandole `[46]` a mano**, asi que el
cableado que suministra ese argumento no lo prueba nadie. Un test mas por hallazgo no
converge: tapa el mutante visible y deja el mismo agujero un nivel mas abajo. **Se tapa
haciendo el error IMPOSIBLE, no anadiendo una asercion.**

### Decisiones de diseno

- **D1 - Un solo camino.** Se extrae `validar(root) -> (errors, ok)` con TODO el cuerpo de
  los checks 1-7. `main()` solo la llama, imprime y hace `sys.exit`. No hay dos rutas de
  validacion posibles por construccion: si `main()` y los tests ejecutan la misma funcion,
  "el cableado que nadie prueba" deja de ser una categoria de bug.
- **D2 - El default se borra.** `journal_cycles` pasa a **posicional obligatorio**. Con el
  default eliminado, el mutante M2 (no pasar el 4o argumento) deja de ser un cambio de
  comportamiento y pasa a ser un `TypeError` en la llamada: el validador muere con
  traceback y **muere el test de subproceso que ya existe**, sin escribir una linea nueva.
  Un parametro opcional cuyo valor cambia el veredicto es la raiz de A1.
- **D3 - Un solo camino tambien para los tests.** Todo test del validador llega a su asercion
  por `validar(root)`. Las funciones privadas **dejan de ser objetivo de tests nuevos**: se
  declaran unitarias-no-contractuales. El unico test que ejercita `main()` es el de
  subproceso, y existe para probar el `exit` y que `main()` llame a `validar`.
- **D4 - Los escenarios son FILAS, no tests.** Un unico test con tabla de escenarios sobre
  Copies del esqueleto real. Medido: `docs/` 0,4 MB + `openspec/` 0,5 MB + 0,8 MB de
  ficheros raiz = **1,7 MB por copia**, y se copia **UNA vez** por test. Anadir un escenario
  futuro cuesta una fila, no un test: por eso esto converge donde las iteraciones 1 y 2 no.

### Contrato de mutaciones del intento 3

| # | Mutante | Asercion que lo mata | Test |
|---|---|---|---|
| M2 | borrar el 4o arg en la llamada (con default) | `Resumen:` ausente del informe (TypeError) | subproceso, 1a mitad, YA EXISTE |
| D2 | `<- sin default` | identico al anterior | ninguno nuevo |
| A1 | desactivar `if not ciclos and journal_cycles:` (`validate_docs.py:285`) | fila (a): `"NO aporta ningun ciclo"` en `errors` | tabla, fila (a) |
| A1b | quitarle `and journal_cycles` | fila (b): `"NO aporta ningun ciclo"` **ausente** | tabla, fila (b) |
| M1 | desactivar `if not journal_cycles and journal_usable:` (`:360`) | fila (d): `"no contiene ningun ciclo valido"` en `errors` | tabla, fila (d) |
| M1b | quitarle `and journal_usable` | `len(errors) == 1` con journal `PermissionError` | `test_el_journal_ilegible...`, YA EXISTE |
| A2 | quitar `--all` (`:244`) | fila (c): el ciclo de una RAMA lateral se acusa | tabla, fila (c) |
| S2 | borrar el cableado del ancla | mitad mutante del subproceso | YA EXISTE |
| S2b | borrar la llamada `validar(root)` de `main()` | 2o mutante del subproceso (4 lineas) | subproceso, YA EXISTE |

Por que A1b muere con una fila y no con una asercion nueva: las filas (a) y (b) comparten el
**mismo** historial sin marcadores y solo cambian el journal, asi que podar la condicion se
delata en una de las dos. Es la misma tecnica que A2b en la iteracion 1, que ya funciono.

### Ficheros a tocar

1. `validate_docs.py` - extraer `validar(root)`, `main()` adelgaza, **borrar el default** de
   `journal_cycles`, y corregir el comentario mentiroso de `:254-258`.
2. `run_tests.py` - **fusionar** `test_un_parser_de_marcadores_roto_no_pasa_en_verde` +
   `test_el_ancla_de_commits_cae_al_git_dir_por_defecto` en
   `test_el_ancla_sobre_un_arbol_sintetico_tabla_de_escenarios` (5 filas). Anadir 4 lineas al
   subproceso para el mutante S2b. **0 tests nuevos, 1 fusion: 104 -> 103.**
3. Los cuatro ficheros de recuento si baja a 103: `STATUS.md:9`, `AGENTS.md:68`, `README.md`
   y la tabla de `docs/ai/testing-guide.md` (una fila menos), mas el `__main__` de
   `run_tests.py`. El check 7 de `validate_docs.py` los deriva con `ast` y avisa si no.
4. `docs/ai/sandbox-rules.md:149` - la cifra de subjects caduca con cada commit (ver abajo).

### Lo que CIERRA y lo que se DECLARA

- **CIERRA**: el residuo "ciclo comiteado sin journal" se acusa en el camino real, con el
  parser vivo o muerto, con o sin `--all`, y el fallo de git es un informe con motivo.
- **SE DECLARA residual, no se HPEa mas**: 112 de 156 subjects no llevan marcador de ciclo,
  asi que un ciclo cerrado con asunto `feat(...)` y sin entrada de journal sigue sin tercer
  testigo. El cierre de eso es `git_safe_commit.py` rechazando el mensaje sin identificador
  de ciclo = **TASK-059**, ya pendiente. Esta tarea NO lo reintenta.
- **Cierra sucio que el intento 3 debe arreglar**: el repo esta **en rojo ahora mismo**
  (`107 OK / 2 FAIL`) acusando el ciclo **047** comiteado y ausente de `rd_journal.json` y de
  `CHANGELOG.md`. Es el ancla mordiendo por primera vez el repo real. Registra el ciclo 47 en
  el journal y en los dos changelogs, o el validador no puede volver a verde.
- `src/woptimizer/**`: cero cambios.

### Los tres puntos sueltos (verificados, todos de correccion inmediata)

- **`validate_docs.py:254-258` esta mal escrito.** Medido: `FileNotFoundError.__mro__[1]` es
  `OSError` y `PermissionError.__mro__[1]` es `OSError`. **Las dos SON subclases de OSError**,
  asi que no justifican un `except Exception`. La justificacion honesta del `except Exception`
  es `subprocess.TimeoutExpired` -> `SubprocessError` -> `Exception`, alcanzable por el
  `timeout=120` de la linea 252. Reescribe el comentario; **el `except` no se estrecha**.
- **`docs/ai/sandbox-rules.md:149` dice "43 de 155 subjects"**. Medido hoy: **156 subjects,
  44 con marcador, 112 sin**. Dos de las tres cifras caducadas. Decision: **dejar de afirmar
  la cifra fija**, decir que el validador la reimprime viva en su linea de informe y que hay
  que mirar ahi. Una cifra con fecha de medicion tambien caduca.
- **El informe de mutación no queda en ningun artefacto.** `openspec/changes/2026-10-01-validator-independent-anchor/`
  solo tiene `proposal.md` y `tasks.md`; los 12 supervivientes del intento 1 no son
  re-audiables por nombre. Ya hay precedente (`mutation-plan.md` en
  `2026-10-01-multi-favorites-and-db-download`). Cerrado en la skill (ver `SKILL.md`).
