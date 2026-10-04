# Tareas — `2026-10-04-desbloquear-pipeline-commitlint`

**Tarea que abre el plan:** `TASK-064` (`in_progress`, T-1 a T-3) · **tarea que lo hace
resistente:** `TASK-066` (nueva, T-4 y T-5).
**Decision de diseno:** `proposal.md` — leerlo entero antes de empezar. **Las mediciones de su
seccion 2 son la verdad y no se vuelven a medir.**
**NO toca:** `.github/workflows/**`, `.releaserc.json`, `.commitlintrc.json`, la proteccion de `main`
en GitHub, ni `src/woptimizer/**` (cero).

Orden obligatorio: **T-1 -> T-2 -> T-3** (el pipeline esta rojo y no se publica `.exe` mientras tanto;
cada uno depende del anterior porque su criterio de cierre es una medicion del estado de GitHub).
**T-4 -> T-5** (la puerta tiene que existir antes de que el bucle viva en `beta`, y las dos mitadas de
`TASK-066` se escriben en el mismo commit porque `.agents/` y `AGENTS.md` aparecen en las dos).

Medicion previa que NO hay que rehacer (esta en `proposal.md` seccion 2):

```
origin/beta  = 4d86908     los 8 commits largos YA estan publicados aqui
origin/main  = ad9159f
main local   = f3d9f6f     +33 sobre origin/main, +7 sobre origin/beta
worktree     = main        arbol limpio
```

---

## T-1 — Reescribir las DOS cabeceras no publicadas (esto es lo que desbloquea)

**Ficheros:** ninguno. Solo historia de Git, y solo de lo que no esta en ningun remoto.

Los dos responsables, medidos:

| SHA | Header | Longitud |
|---|---|---|
| `ef67bf8` | `fix(tooling): cerrar los seis huecos sin guardian de la puerta de versionado y corregir dos afirmaciones documentales (TASK-061)` | 128 |
| `82f52c2` | `chore(tooling): dejar de versionar el log de la corrida de la suite, que es un artefacto de la sonda y no un fuente del repo (TASK-061)` | 135 |

**Textos de reemplazo** (los dos por debajo de 120, los dos con el ancla que la puerta de TASK-059
exige, y los dos sin mayuscula inicial en el subject):

- `fix(tooling): cerrar los seis huecos de la puerta de versionado (TASK-061)`
- `chore(tooling): no versionar el log de la corrida de la suite (TASK-061)`

**Via, y por que esta:** `git rebase -i` **no esta soportado en este entorno** (ver `AGENTS.md`,
"Seccion 0"; el runtime declara las flags interactivas no soportadas). Ademas los dos commits son
**consecutivos** y son las posiciones 4 y 5 de los 7 del rango, asi que la via no interactiva es
barata y local:

1. `git status --porcelain` **vacio** antes de empezar. Si no lo esta, `git reset --hard` tiraria
   trabajo sin versionar: es la unica operacion destructiva del plan y su unico riesgo real.
2. `git reset --hard` al ancestro comun (`4879d19`, el commit justo anterior a `ef67bf8`).
3. Por cada uno de los dos, en orden: `git cherry-pick --no-commit <sha>` y despues
   `python .taskmaster/git_safe_commit.py "<texto de reemplazo>"`.
4. `git cherry-pick f3d9f6f` para recuperar el commit mas reciente (cambia de SHA por ser el ultimo
   de la cadena; inevitable y sin coste, no esta en ningun remoto).

`git cherry-pick` conserva autor y fecha de autor por defecto: **no se pierde atribucion**, y eso se
comprueba (criterio de cierre 3).

⚠️ **Si `T-4` ya esta instalado cuando se ejecute `T-1`, el wrapper rechazara los dos textos largos
con codigo 2 y no escribira nada.** Es el comportamiento correcto y no es un fallo: por eso el orden
es `T-1` antes que `T-4`, y no al reves.

### Criterios de cierre

1. La sonda de `proposal.md` seccion 2 sobre `4d86908..main` devuelve **`0 de 7` incumplen** (hoy
   devuelve `2 de 7`). La sonda se reconstruye si hace falta: seis reglas de nivel 2 de
   `.commitlintrc.json:4-27`, sin red, con `git log`.
2. `git status --porcelain` vacio al terminar.
3. `git log --format='%h %an %ad %s' 4879d19..main` conserva **autor y fecha de autor** de los siete
   commits; se compara contra el registro previo a la reescritura y se pega en el informe.
4. `git branch -r --contains <los dos shas nuevos>` -> **NINGUNA** rama remota. Si aparece alguna,
   se paro: significaria que se estaba a punto de reescribir historia publicada.
5. Ninguna cabecera del rango pasa de 120 y ninguna empieza en mayuscula.

## T-2 — Mover `beta` con fast-forward y ver el pipeline en verde

**Sin `--force`. En ninguna rama.** `beta` no esta protegida y `main` tiene la proteccion blanda de
`release.yml` en pie; ninguna de las dos se toca.

```
git push origin main:beta
```

Fast-forward puro: `beta` ya es ancestro de `main` (medido, `git merge-base --is-ancestor beta main`
-> SI), asi que no hace falta `--force` en ninguna de las dos ramas. La equivalencia
`git branch -f beta main && git push
origin beta` tambien vale; se prefiere el refspec por no mover ramas locales.

El rango que vera el job `commits` es `4d86908..<nuevo>`, que es el que T-1 deja limpio. **Los 8
commits largos de la seccion 2.1 quedan fuera del rango** y no se miran: no porque se haya relajado
la regla, sino porque `release.yml:49-61` los deja como abuelos del rango.

### Criterios de cierre

1. La corrida de `release.yml` sobre `beta` sale **verde en los cuatro jobs** — en especial
   `Commits convencionales`, que es el que hoy tumba los otros tres. Se pega el enlace y el estado.
2. Existe una **pre-release nueva** `v1.1.0-beta.N` con **`woptimizer.exe` adjunto** (job `build` con
   `needs.release.outputs.tag != ''`). Sin el `.exe` la corrida esta a medio hacer aunque salga verde.
3. `git log origin/beta -1` coincide con `git log main -1`.
4. **No se ha tocado** `.commitlintrc.json`, `.releaserc.json`, ningun fichero de
   `.github/workflows/`, ni la proteccion de `main`. `git diff origin/beta..main --stat` sobre esos
   caminos sale vacio.

## T-3 — Graduar a `main` y cerrar la ultima casilla de TASK-064

```
git push origin main:main
```

Cumple O-1: el tramo pendiente salio como pre-release (T-2) y la estable se gradu sola. El job
`release` de `main` calcula **un** version por corrida tomando el tipo mas alto de los 33 commits, asi
que sale `v1.1.0`. Es lo que O-1 acepto y lo que `proposal.md` seccion 6 deja escrito como coste.

### Criterios de cierre

1. Release **estable** `v1.1.0` publicada, con `woptimizer.exe` adjunto.
2. `docs/GITHUB-SETUP-CHECKLIST.md` seccion 2: la casilla de **`main` mergeada desde `beta`** pasa a
   `[x]` con el enlace a la release. Con esto TASK-064 queda cerrable.
3. `origin/main` y `origin/beta` apuntan al mismo commit.

## T-4 — La puerta de cabecera en `git_safe_commit.py` (impide el rojo, no lo arregla)

**Fichero:** `.taskmaster/git_safe_commit.py`. Cero cambios en `src/`.

Es la mitad que evita la recaida: mientras un header de 135 chars pueda existir, el rojo vuelve.
El wrapper es **la unica puerta de versionado** del bucle, asi que ahi es donde va, no en el `.yml`.

1. **`clasificar_cabecera(mensaje) -> (ok, codigo_regla, detalle)`** — **pura**: sin `subprocess`, sin
   ficheros, sin leer `.commitlintrc.json` en caliente. Devuelve el PRIMER fallo de las reglas de
   nivel 2 que el job `commits` va a medir, y **solo esas**: `header-max-length` (120),
   `subject-case` (primer caracter en mayuscula) y `type-enum`/`type-case`/`type-empty` para una
   cabecera que no parsea. **Copia el criterio de `subject-case` de commitlint, que mira el primer
   caracter y no toda la cadena** — es lo que hace que `92368ad` y `c3ced1a` sean rojos, y por eso no
   se inventa una regla mas estricta ni mas laxa.
2. **Colocacion exacta, y es la de la puerta de ancla**: en `main()`, **despues** de `validar_repo` y
   del NOOP, **antes de `add -A`** (el mismo sitio que `git_safe_commit.py:460-469`, que es de solo
   lectura y cae antes de la primera escritura). El criterio: un rechazo nunca deja el arbol
   modificado. Este es el error que ya se cometio una vez con la puerta de ancla y por eso esta dicho
   con su sitio.
3. Rechazo: `WOPT_USAGE cabecera-larga <que se espera> <medicion>` + `sys.exit(CODE_USAGE)`, con la
   linea `WOPT_*` **la ultima** (regla 4 del contrato) y **codigo 2, no 1** — por el mismo motivo que
   TASK-059 fijo: un `WOPT_FAIL` seria indistinguible de un fallo de git para el unico consumidor
   real, que ramifica por el codigo.
4. `--verify` **no** pasa por la puerta.
5. **`INFO rama: <branch>` en la salida canonica** — `git rev-parse --abbrev-ref HEAD` leido una vez.
   Con la rama hoy **ciega** (`git_safe_commit.py` no tiene ni una coincidencia de `branch`), la
   pregunta "en que rama estoy escribiendo" no tiene respuesta en la salida.
6. **La rama es AVISO, no rechazo.** Si la rama esta en la lista de publicacion (`main`), se imprime
   un bloque `AVISO` que nombra la regla de `T-5` y **se sigue con codigo 0**. Motivo en
   `proposal.md` seccion 3.2, y es el mismo criterio de `STATUS.md:95(b)`: un `sys.exit` aqui solo
   guardaria el wrapper y bloquearia el commit legitimo del dueno en la rama de release.
7. `imprimir_uso()` gana una linea con la regla del mensaje. Actualizar el docstring del contrato de
   codigos (`:12-26`) y la tabla de `docs/ai/sandbox-rules.md`.

### Criterios de cierre

1. **Test de rechazo**: subproceso con `GIT_DIR` a una temporal y el header real de `82f52c2`
   (135 chars) -> codigo **2**, `WOPT_USAGE cabecera-larga` en stdout, y **cero commits creados**.
2. **Test de no-stageo**: tras ese rechazo, `git diff --cached --quiet` sigue en 0 y
   `git status --porcelain` no ha cambiado respecto a antes de la invocacion.
3. **CONTRAPRUEBA**: las **cinco** plantillas literales de `SKILL.md` pasan la puerta. Sin este test
   una puerta demasiado fuerte atasca el bucle y ningun otro lo ve.
4. **Test de `subject-case`**: cabecera de longitud valida que empieza en mayuscula -> rechazada, con
   la regla `subject-case` en el mensaje. Mata al mutante "solo compruebo la longitud".
5. **Test de corpus compartido**: el clasificador, sobre la fixture congelada de las **ocho**
   cabeceras largas reales (con su SHA citado en un comentario) mas cinco limpias reales, acepta las
   cinco y rechaza las ocho. Congelado, **no derivado de `git log`**: la historia se mueve y el test
   debe seguir signifcando lo mismo dentro de tres ciclos.
6. **Test de rama**: `INFO rama:` sale en la salida canonica con el valor real de la rama.
7. `python run_tests.py` en verde con el recuento sincronizado en los **cuatro** ficheros
   (`STATUS.md`, `AGENTS.md`, `README.md`, tabla de `docs/ai/testing-guide.md`), y
   `python validate_docs.py` en **0 FAIL**.

## T-5 — El bucle trabaja en `beta`, y la regla esta escrita donde se lee

**Ficheros:** `.agents/skills/id-pipeline/SKILL.md`, `.agents/agents/openspec-dev/agent.md`,
`AGENTS.md`, `docs/ai/release-pipeline.md`. Editar **el fichero del repo** y luego
`python .taskmaster/sync_agents.py` (`--check` sale 0).

Medido: los tres primeros ficheros tienen **cero** ocurrencias de `beta`, `rama`, `branch` o `push`.
**No hay ninguna instruccion que corregir: hay una instruccion que falta.** El bucle no eligio
`main`; nunca se salio de la rama en la que estaba el worktree y la puerta de versionado es ciega a
la rama (`proposal.md` seccion 2.5).

1. **Una sola regla, en los tres ficheros, con el mismo texto:** el bucle comitea y empuja a
   **`beta`**; **`main` es rama de publicacion y solo recibe `beta` por fast-forward**, nunca un
   commit del bucle. Con el **porque en una frase**: `main` es la rama cuya proteccion bloquea el
   force-push, y publicar estable sin pasar por `beta` es lo que produjo el tramo de 33 commits.
2. **Punto de insercion en `SKILL.md`**: junto al bloque "REGLA DURA" de la seccion **0-bis**
   (`SKILL.md:33-48`), que es donde ya vive la otra regla dura del mensaje, y como bloque hermano
   suyo — no como nota al pie de la seccion 2. Se anade **despues** del parrafo de `:45-48`, que es
   donde el documento ya explica que un test extrae sus plantillas.
3. **`openspec-dev/agent.md`**: en el bloque de "Entorno" (`:39-43`), junto al parrafo del mensaje
   con identificador, que es el otro contrato de git que ese agente ya conoce.
4. **`AGENTS.md`**: en la seccion "Reglas de Documentacion Continua y Persistencia", punto 2
   ("Cierre Limpio"), que hoy dice que hay que commitear **todo** sin decir donde. Anadir la misma
   regla ahi, porque `AGENTS.md` es lo que lee el dueno y lo que copian los agentes.
5. **`docs/ai/release-pipeline.md`**: la seccion 2 ya declara el ciclo `beta` -> `main`; se le anade
   que ese ciclo **no lo puede hacer el bucle sobre `main`**, y que el paso de grado es
   `git merge --ff-only beta` **con el arbol limpio**.
6. **La topologia, en este orden, para que `main` no quede nunca 7 commits atras sin querer:**
   ```
   git switch beta            # el bucle trabaja aqui
   # ... ciclos ...
   git switch main
   git merge --ff-only beta
   git push origin main
   git switch beta
   ```
   Es el ciclo que ya esta escrito en `release-pipeline.md:30-43`; lo que faltaba era que el
   worktree estuviera en `beta`. **T-3 deja `main` y `beta` en el mismo commit**, que es el punto de
   partida correcto: `main` se queda quieto mientras `beta` avanza, y el `--ff-only` de siempre
   funciona.
7. **`git status --porcelain` antes de cada `git push`**, y se dice por que: `add -A` se lleva lo
   que haya suelto, y en este turno arrastro un `run_tests_out.txt` de 354 lineas a un commit ajeno.

### Criterios de cierre

1. **Test de la regla, mitad positiva**: los tres ficheros contienen la regla y la nombran a los dos
   (`beta` y `main`), extraidos del repo con el mismo criterio que el test de las cinco plantillas
   que ya existe.
2. **Test de la regla, mitad negativa** — la que de verdad discrimina: **ninguna** plantilla literal
   de commit de los tres ficheros nombra `main` como destino. Sin esta mitad, el test pasa con un
   comentario nuevo que no cambia nada: mata al mutante `REGLA_EN_UN_COMENTARIO`.
3. El worktree queda en `beta` y `git rev-parse --abbrev-ref HEAD` lo dice.
4. `python .taskmaster/sync_agents.py --check` sale **0**.
5. `python validate_docs.py` en **0 FAIL** y `python run_tests.py` en verde.
6. **Comprobacion de no recaida, y es la que cierra el plan**: un commit nuevo con cabecera de 135
   chars **no llega a existir** — el wrapper lo rechaza con codigo 2. Se ejecuta de verdad, no se
   razona.
