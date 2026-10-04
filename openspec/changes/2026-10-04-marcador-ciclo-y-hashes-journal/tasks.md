# Tareas — `2026-10-04-marcador-ciclo-y-hashes-journal`

**Tarea:** `TASK-059` · **Decision de diseno:** `proposal.md` (leerlo entero antes de empezar; las
cifras de la seccion 2 son la medidad que motiva el diseno y no se vuelven a medir)
**NO toca:** `src/woptimizer/**` (cero). **NO toca:** `STATUS.md` (`proposal.md` seccion 11).

Orden obligatorio: **T-2 antes que T-1** (el bucle tiene que poder commitear antes de que exista una
puerta que le pueda rechazar el commit), y **T-4 antes que T-3** (el residuo se sanea antes de que
exista el check que lo mide, o el check nace en rojo y el bucle aprende a ignorarlo).

---

## T-1 — Las plantillas del bucle pasan la puerta que se va a instalar (AC-C1, AC-C2)

**Ficheros:** `.agents/skills/id-pipeline/SKILL.md` (lineas 152, 180, 280, 300, 332) y los cuatro
`.agents/agents/*/agent.md`.

Las cinco plantillas literales de `git_safe_commit.py "..."` que el bucle tiene escritas **fallan las
cinco** la puerta de D1 (medido: `proposal.md` seccion 6). Reescribirlas **con identificador en la
plantilla**, no con una nota al lado:

| Hoy | Con identificador |
|---|---|
| `SKILL.md:152` `chore(architect): planificar <tarea>` | `chore(architect): planificar <tarea> (TASK-NNN)` |
| `SKILL.md:180` `feat/fix: <tarea>` | `feat/fix: <tarea> (TASK-NNN)` |
| `SKILL.md:280` `chore(architect): planificar [ID_TAREA]` | `chore(architect): planificar [ID_TAREA] (TASK-NNN)` |
| `SKILL.md:300` `feat/fix([COMPONENTE]): [TÍTULO_TAREA]` | `feat/fix([COMPONENTE]): [TÍTULO_TAREA] (TASK-NNN)` |
| `SKILL.md:332` `chore(process-db): actualizar procesos gaming y bloatware` | `chore(process-db): actualizar procesos gaming y bloatware (TASK-NNN)` |

Una sola regla manda en `SKILL.md` y en los cuatro `agent.md`, en una linea: **el mensaje de commit
lleva `TASK-NNN` (existente en `.taskmaster/tasks.json`) o `ciclo N`; sin eso el wrapper lo
rechaza.** Añadir el porque en una frase, no en un parrafo: es la puerta, no una recomendacion.

Editar **el fichero del repo** (`.agents/agents/`) y luego `python .taskmaster/sync_agents.py`
(`--check` debe salir 0).

## T-2 — La puerta del mensaje en `git_safe_commit.py` (AC-A1..A6)

**Fichero:** `.taskmaster/git_safe_commit.py`. Cero cambios en `src/`.

1. `ancla_del_mensaje(mensaje, ids)` — **pura**: recibe el mensaje y el conjunto de ids, no lee
   ficheros ni llama a `subprocess`. Devuelve `(ok, motivo)`. Motivo **ASCII puro** (trampa #16).
   Acepta `TASK-\d{1,4}` **que este en `ids`**, `CYCLE-\d{3}` y el marcador de ciclo
   `\b(?:ciclo|cycle)(s?)\b[\s:#-]*#?(\d{1,4})`. **Rechaza `T-\d+`**: es otro espacio de ids
   (`T-1`..`T-9` son tareas de change, `openspec/changes/*/tasks.md`) y no existe en `tasks.json`.
2. `ids` se deriva de `.taskmaster/tasks.json` con el `REPO_ROOT` que ya hay
   (`git_safe_commit.py:37`). **Si no se puede leer, se degrada a forma sin resolubilidad y se dice en
   un `INFO`** — nunca a "todo valido".
3. **Colocacion exacta** (D2): despues de `validar_repo` y del NOOP, **antes de `add -A`**. Actualizar
   el docstring del contrato de codigos (`:12-26`) y la tabla de `docs/ai/sandbox-rules.md`.
4. Rechazo: `WOPT_USAGE ancla-mensaje <que se espera> <por que importa>` + `sys.exit(CODE_USAGE)`, y
   la linea `WOPT_*` **la ultima** (regla 4 del contrato). Codigo **2**, no 1 — ver `proposal.md`
   D3 y el porque de por que 1 haria falsa la tabla de `docs/ai/sandbox-rules.md:57`.
5. **`--verify` no pasa por la puerta.**
6. Actualizar `imprimir_uso()` con una linea que diga que el mensaje lleva identificador.

## T-3 — El check 9 del validador (AC-B1..B-B6)

**Fichero:** `validate_docs.py`. Cero cambios en `src/`.

1. `_comprobar_hashes_del_journal(root, errors, ok)` — **tres posicionales, sin defaults**, cableada
   en `validar(root)` entre el check 8 y el `return`. Reutiliza la lectura de commits que ya existe
   (mismo `GIT_DIR`, misma precedencia).
2. R1 `fullmatch` del elemento (no `search`: medir el string entero produjo la cifra falsa de
   "41 de 46", `docs/ai/sandbox-rules.md:169`). R2 resolubilidad. R3 `commits_perdidos` por entrada
   con `causa` en vocabulario cerrado (`VFS_CORRUPTO`, `NUNCA_DECLARADO`) y `nota` libre. **R4
   antidolar**: hash declarado perdido que **resuelve** → FAIL. R5 techos `MAX_HASHES_PERDIDOS = 3` y
   `MAX_CICLOS_SIN_HASH = 2`, comentados con la fecha y la medidad de la que salen.
3. Todo mensaje de `print()` en **ASCII puro**.
4. Anadir su **segundo bloque** a la linea de informe, con cifras **vivas** (no escritas en el
   codigo). El bloque de "con marcador / SIN marcador" **ya existe**
   (`validate_docs.py:350-355`) y **no se toca**: lo que se anade es su suelo y el dato del campo
   `commits`, que hoy no se mide en ninguna parte.
5. El techo se **lee del producto** en el test, no se copia.

## T-4 — Sanear el residuo del journal (prerrequisito de T-3 en verde)

**Fichero:** `.taskmaster/rd_journal.json`. Manual y con evidencia, sin script que regenere a ciegas.

| Que | Cuantos | Como |
|---|---|---|
| Rellenar la lista de los 9 recuperables | 9 — ciclos 14-20 (`7485f57`), 27 (`9cc9582`), 28 (`5e166e1`) | Anadir el hash, que **resuelve** |
| Quitar el texto libre | 13 — ciclos 3, 8-12, 21-26, 50 | Dejar el hash desnudo: `"617eef8 (architect)"` → `"617eef8"` |
| Sustituir el `<PENDIENTE>` | 1 — ciclo 50 | Los 3 hashes que corroboran el ciclo (`4aba876`, `9d8fd00`, `ad9159f`) y el hueco va a `commits_perdidos` con `causa: NUNCA_DECLARADO` y la `nota` que nombre `SKILL.md:382` |
| Declarar la perdida **parcial** | 3 — ciclos 30, 31, 33 | `commits_perdidos: [{hash, causa: VFS_CORRUPTO, nota: el ciclo sigue anclado por <commit corroborante>}]`. **El hash muerto no se sustituye**: es un hecho |
| Declarar la perdida **real** | 2 — ciclos 1 y 2 | `commits_perdidos: [{causa: NUNCA_DECLARADO, nota: ningun subject de los 209 nombra el ciclo; el commit mas antiguo es 3686a4a (2026-09-14) y el primero que nombra un ciclo es de 2026-09-29}]` |

**Ninguna entrada se borra y ninguna fila se deja como estaba.** El criterio de este repo:
*borrar una fila sin evidencia es el mismo fallo que no haberla escrito* (`STATUS.md:87`).

## T-5 — Los tests (AC-A1..A6, AC-B1..B-B6, AC-C1, AC-C2)

**Fichero:** `run_tests.py`. Mover el recuento en `__main__` **y** en `STATUS.md`, `AGENTS.md`,
`README.md` y la tabla de `docs/ai/testing-guide.md` — lo exige el check 7
(`validate_docs.py:116-118`) y el recuento se deriva con `ast`.

1. **Wrapper:** ampliar `test_git_safe_commit_fail_safe` (`run_tests.py:1401`) con el caso de uso
   incorrecto nuevo, y **poner identificador en sus dos mensajes del camino de commit**
   (`:1447`, `:1471`) manteniendo el `3` esperado (AC-C2). Tests nuevos por la funcion extraida con
   `ids` sintetico (AC-A1, A2, A3, A6) y **una asercion estructural con `ast` para el orden**
   (AC-A5) — el patron de `MARCADOR_HEADLESS` de `validate_docs.py:508-561`.
2. **Validador:** arboles sinteticos en `tempfile.mkdtemp()` con **`GIT_DIR` temporal y commits
   REALES** del repo temporal, para que "resuelve" sea un hecho y no una afirmacion. El par de
   AC-B1 (mismo arbol, dos veredictos), el par de AC-B2 (mismo journal con y sin `commits_perdidos`),
   AC-B3, AC-B4 leyendo las constantes del producto y AC-B5 con los numeros fijados **por el
   fixture**. **Ninguna expectativa se deriva del fichero que se valida.**
3. **Cableado (AC-B6):** copiar el `validate_docs.py` **real** a un arbol temporal con el esqueleto
   que `validar()` lee y ejecutarlo **como subproceso**. Sin esto el fix puede ser codigo muerto en el
   camino real, que es lo que paso en los ciclos #47 y #49.
4. **Bucle (AC-C1):** extraer del repo las plantillas literales de `git_safe_commit.py "..."` de
   `.agents/**` y pasarlas por `ancla_del_mensaje` con los ids reales de `tasks.json`. Hoy salen
   **0 de 5**: el test **falla** hasta que T-1 este hecha.

## T-6 — Documentacion (AC-C3)

**Fichero:** `docs/ai/sandbox-rules.md` (`docs/ai/` es de este contrato, no de `openspec-dev`).

- Nueva seccion junto a la del ancla (`:123`): la puerta del mensaje — las tres formas, el **por que**,
  la colocacion exacta y **por que el NOOP queda exento**, el codigo 2 y el porque de no ser 1, la
  degradacion con `tasks.json` ilegible, y el limite de que no cubre `git` a pelo.
- El check 9 con R1-R5, el vocabulario cerrado de `causa`, el techo de perdidas y la linea de informe.
- **Los seis limites residuales de `proposal.md` seccion 9, escritos.**
- Corregir la referencia de `docs/ai/sandbox-rules.md:200-202` (dice que lo que va a `TASK-059` "son
  residuo conocido" sin nombrar la cifra viva) dejandola **sin cifra fija**: las cifras van en la
  linea de informe, que se reimprime viva.
- Actualizar `AGENTS.md` (comando de commit) para que mencione el identificador obligatorio.

## T-7 — Verificacion de cierre

```bash
python run_tests.py            # verde, recuento sincronizado en los cuatro ficheros
python verify_ui_syntax.py
python validate_docs.py        # 0 FAIL, y el bloque del journal con las cifras vivas
python .taskmaster/git_safe_commit.py --verify   # WOPT_REPO_OK, exit 0
python .taskmaster/sync_agents.py --check          # exit 0
```

Comprobar ademas, a mano, las dos puertas del wrapper con un mensaje **con** y **sin** identificador,
en un repo temporal, y que el mensaje sin identificador **no** deja nada stageado.

## T-8 — Mutacion (Paso 4 del bucle, la cierra `mutation-auditor`)

Los mutantes a matar, por criterio, estan en la tabla de `proposal.md` seccion 8 (M1-M14). Los que
**no** puede matar ningun test y hay que decir explicitamente en el informe:

- `except Exception: return True` **antes** del chequeo de forma: lo mata AC-A1, porque la forma se
  exige aunque `ids` sea vacio.
- Cambiar `WOPT_NOOP` por la puerta sin mover la llamada: lo mata AC-A5 por posicion de sentencia.
- Reescribir el helper de `_informe_del_validador_real`: **no lo mata nada**, igual que el punto ciego
  (c) de la limitacion 2 de `docs/ai/sandbox-rules.md:314-317`. Declararlo, no esconderlo.
