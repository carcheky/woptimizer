# Checklist de configuracion de GitHub — woptimizer

> Documento de trabajo. Cada casilla se marca solo con **evidencia medida**, no con la
> intension. Si algo quedo a medias, esta marcado como tal y con el motivo.
>
> - Creado: 2026-10-04
> - Repo: `https://github.com/carcheky/woptimizer` (publico)
> - Metodo de lectura/escritura: API de GitHub con el token de `git-credential-manager`
>   (**no hay `gh` CLI en esta maquina**). Sonda: `.taskmaster/_gh_probe.py`.
>   Configurador: `.taskmaster/_gh_configure.py`.
>
> **Leyenda:** `[x]` hecho y verificado · `[~]` a medias / decision pendiente ·
> `[ ]` sin hacer

---

## 0. RESPUESTAS A LAS PREGUNTAS DIRECTAS

### ¿Que rama debe ser la rama por defecto?

**`main`. Ya lo es** — verificado en la API (`default_branch: "main"`). No hay nada que cambiar.

Y es la correcta, pero por una razon que conviene dejar escrita: la rama por defecto de
GitHub es la que se abre cuando alguien entra al repo sin clonar, y la que GitHub Pages
y lasReleases apuntan por defecto. Como `main` es la unica que produce version **sin
sufijo** (`v1.0.0`, no `v1.0.0-beta.3`), tiene que ser la por defecto. Si `beta` fuera
la por defecto, el link "latest release" apuntaria a una beta.

### ¿En que rama se trabaja?

| Rama | Rol | Quien comitea ahi |
|---|---|---|
| `beta` | **Rama de trabajo.** Integracion y pruebas del pipeline. | Todo el trabajo nuevo |
| `main` | **Rama estable.** Solo receives `beta` ya probada. | Solo el `merge --ff-only` |

El ciclo correcto es: `beta` -> push -> `v1.1.0-beta.N` -> `main` -> push -> `v1.1.0`.

> [!WARNING]
> **El repo NO cumple esto hoy.** Hay **15 commits sin pushear en `main`**, y `beta` esta
> 15 commits por detras de `main` (medido: `origin/beta..beta` = 0/0, `origin/main..main` = 0/15).
> El trabajo se ha hecho **directamente sobre `main`**, saltandose `beta` por completo.
> Ver seccion 5, bloque B — es el hallazgo mas serio de esta auditoria.

### ¿Cuando se genera la version?

**En cada push a `main` o `beta` que contenga al menos un commit publicable.** No hay
version manual en ningun sitio.

```
push a main/beta
  -> job commits   (commitlint sobre el rango del push; si falla, para aqui)
  -> job verify    (windows: verify_ui_syntax.py + run_tests.py)
  -> job release   (semantic-release calcula la version, crea el tag y la Release)
  -> job build     (solo si hubo tag nuevo: PyInstaller + adjunta woptimizer.exe)
```

| Tipo de commit | Version que sale | Publica |
|---|---|---|
| `fix(...)` | patch `1.0.0 -> 1.0.1` | si |
| `feat(...)` | minor `1.0.0 -> 1.1.0` | si |
| `perf(...)` | patch | si |
| `feat!:` / `BREAKING CHANGE:` | major `1.0.0 -> 2.0.0` | si |
| `docs` `chore` `refactor` `test` `ci` `build` `style` | — | **no** |

Estado real medido: hay **2 releases** (`v1.0.0-beta.1` y `v1.0.0`, ambas con
`woptimizer.exe` adjunto) y **2 tags**. El pipeline funciona; lo que falla es que se
dispara desde la rama equivocada (seccion 5).

### ¿El flujo de desarrollo esta bien definido en la documentacion?

**Si, con una reserva grande y un hueco pequeno.**

| Artefacto | Estado | Nota |
|---|---|---|
| `AGENTS.md` | Completo | Stack, invariantes, 4 agentes, releases, comandos. Es el mapa maestro. |
| `docs/ai/release-pipeline.md` | **Desactualizado** | Contradice al `.yml` real en 2 puntos (seccion 5, D-1) |
| `docs/ai/sandbox-rules.md` | Completo | Tabla de codigos de `git_safe_commit.py` |
| `docs/ai/testing-guide.md` | Completo | Guia headless |
| `docs/ai/architecture.md` / `data-models.md` / `ui-design-system.md` | Presentes | Carga selectiva via `llms.txt`, correcto |
| `.agents/skills/id-pipeline/SKILL.md` | Presente | Seccion 0 con la tabla de runtimes |
| `.agents/agents/*/agent.md` (4) | Presentes | Con `README.md` de agentes |
| `STATUS.md` | **Enorme (60 KB) y con deuda abierta** | Gobierna el bucle; ver seccion 6 |

**El hueco pequeno:** ningun documento dice **en que rama se trabaja por defecto**, ni
que `beta` es la rama de integracion. `release-pipeline.md:33-43` lo insinua en un ejemplo
de comandos, pero no hay una regla declarada, y por eso el trabajo se ha ido a `main`.
Este checklist lo arregla: la regla queda escrita aqui y hay que propagarla.

---

## 1. METADATOS DEL REPO — ✅ HECHO

- [x] **Descripcion.** Estaba en `null`. Puesta:
      > Cierra en masa las apps que sobran al jugar y reabre tu setup al volver.
      > Process manager para Windows con perfiles (Packs), semaforo de seguridad
      > protegido y .exe standalone.
- [x] **Topics.** Estaban vacios `[]`. Puestos 11, todos reales (verificados contra el codigo):
      `windows` `python` `process-manager` `gaming` `gui` `customtkinter` `psutil`
      `performance` `system-utility` `pyinstaller` `semantic-release`
- [x] **Rama por defecto.** `main` — ya correcta, sin cambios.
- [x] **Wiki desactivada.** Estaba `true` y vacia. Boton muerto en un repo publico.
- [x] **Projects desactivado.** Estaba `true` y sin usar.
- [x] **Discussions activadas.** Estaba `false`. Es el sustituto natural del wiki para
      preguntas de uso, ahora que el wiki no existe.
- [x] **`delete_branch_on_merge`.** Estaba `false`. Ahora `true`.
- [x] **Visibilidad.** `public` — ya era, sin cambios.
- [x] **Secret scanning + push protection.** Ya `enabled` + `enabled`. Sin tocar.
- [x] **Dependabot security updates.** Ya `enabled`. Sin tocar.
- [ ] **Homepage.** Sigue en `null`. Depende del bloque 4 (no hay docs publicadas).
- [ ] **Avatar / imagen del repo.** No configurado. Opcional, no bloquea nada.

## 2. RAMAS Y PROTECCION — ✅ HECHO (2026-10-04)

- [x] **`beta` existe y esta publicada** en `origin` (`41b8061`).
- [x] **`.releaserc.json` declara las ramas correctas**: `main` (estable), `beta`
      (`prerelease: "beta"`), y el patron `1.x` / `1.1.x` para mantenimiento.
- [x] **`release.yml` dispara en `main` y `beta`.** Correcto.
- [x] **Proteccion BLANDA de `main` aplicada y verificada.** Sin required status checks y
      sin PR obligatorio, para no romper el empuje de tags del job `release`. Verificado
      con una lectura independiente (`GET /branches/main/protection` → 200):
      `allow_force_pushes: false`, `allow_deletions: false`, `enforce_admins: false`,
      `required_status_checks: null`, `required_pull_request_reviews: null`.
      Script reproducible en `.taskmaster/_gh_protect.py` (`apply` / `show`).
- [x] **`beta` sincronizada con `main`.** `beta` estaba 15 commits atras; ahora apunta al
      mismo commit. **La operacion elegida "rebasar `main` sobre `beta`" resulto ser un
      FAST-FORWARD puro**, medido antes de tocar nada: `beta` ya era ancestro de `main`
      (`git merge-base --is-ancestor beta main` → SI) y el rango `beta..main` tiene
      **0 commits de merge**. Rebasar 29 commits sin merges es un no-op destructivo sin
      ganancia: `git branch -f beta main` hace lo mismo sin reescribir un solo SHA.
- [x] **`beta` pusheada primero**, como se decidio, para que el tramo pendiente salga
      como pre-release y la estable se gradu sola al mergear.
- [ ] **`main` mergeada desde `beta`.** **BLOQUEADA, y no por la configuracion de este
      trabajo:** el pipeline de `beta` salio en ROJO en el job `commits`, y por el orden
      `commits -> verify -> release -> build` **nada despues llego a correr**. Ver D-4.

## 3. FICHEROS QUE FALTAN EN `.github/`

Ninguno existe hoy. Solo hay `workflows/commitlint.yml` y `workflows/release.yml`.

### Bloque 3A — Salud del proyecto (recomendado, bajo coste)

- [ ] **`LICENSE`.** **Ausente, y es lo mas grave de este bloque.** `mkdocs.yml:88` ya
      declara `Released under the MIT License`, es decir, **el pie de la documentacion
      afirma una licencia que no existe en el repo**. Sin LICENSE, GitHub no muestra la
      etiqueta de licencia en la pagina y la afirmacion no es ejecutable.
      *Propuesta: MIT, coherente con lo que ya dice `mkdocs.yml`.*
- [ ] **`CONTRIBUTING.md`.** El flujo de trabajo (commits convencionales, ramas, tests)
      solo existe dentro de `AGENTS.md`, que esta escrito para agentes. Un humano que
      quiera contribuir no tiene puerta de entrada.
- [ ] **`SECURITY.md`.** La app **mata procesos del sistema**. Es la unica clase de
      proyecto aqui donde "reporta una vulnerabilidad" deberia tener un canal explicito.
- [ ] **`CODE_OF_CONDUCT.md`.** Opcional. Para un repo de un solo_dueno, bajo valor.
- [ ] **Templates de issue.** `.github/ISSUE_TEMPLATE/bug_report.yml` con desplegables
      (version de Windows, `.exe` o codigo, que pack, que categoria, salida de consola).
      El "Reporte de fallo" libre produce informes inservibles.
- [ ] **Template de PR.** `.github/PULL_REQUEST_TEMPLATE.md` que exija elConventional
      Commit en el titulo y el resultado de `python run_tests.py`.
- [ ] **`.github/dependabot.yml`.** Ausente. El *Dependency Graph* se actualiza solo
      (workflow dinamico activo, visto en la API), pero **dependabot no abre PRs de
      actualizacion de `pyproject.toml`**. Con `psutil` y `pydantic` en juego, eso es
      un agujero real.
- [ ] **`CODEOWNERS`.** Un solo_dueno: valor practico ~0. Opcional.

### Bloque 3B — Pipelines que faltan

- [ ] **Workflow de PR con tests.** `commitlint.yml` corre en PRs, pero **solo mira el
      mensaje del commit**. `run_tests.py` (124 tests) **no corre en ningun PR**: solo
      corre en `release.yml`, y ese solo dispara en push a `main`/`beta`. Una PR puede
      mergearse con la suite en rojo.
- [ ] **Deploy de `mkdocs.yml` a GitHub Pages.** Hay una config de MkDocs Material
      completa y `has_pages: false`. La documentacion existe pero **no hay forma de
      leerla sin clonar el repo**. De ahi el homepage del bloque 1.
- [ ] **`CODEOWNERS`** — duplicado de 3A, listado aqui por ser tambien configuracion de CI.

## 4. RAMA `beta` / RAMA DE TRABAJO — ⚠️ EL HALLAZGO PRINCIPAL

- [x] **`.releaserc.json` dice lo correcto** (main estable, beta prerelease).
- [x] **`release.yml` dice lo correcto** (dispara en ambas).
- [ ] **La practica no lo cumple.** 15 commits fueron directo a `main`:
      ```
      d318fef fix(categorias): cerrar los 4 supervivientes del mutation-auditor
      e0f20db feat(categorias): puerta comun execute_pack con las barreras DENTRO
      9433985 feat(tests): invariante del acordeon afirmado por efecto
      bf0f5d0 fix(tests): cerrar los dos supervivientes de la seccion 16
      ... (11 mas)
      ```
      Hay **`feat(categorias):`** y **`feat(tests):`** entre ellos. Cuando se pusheen,
      saldra **una** release estable desde `main`: `v1.1.0` (semantic-release calcula
      **un** version por corrida, tomando el tipo mas alto de todos los commits del
      push: hay `feat` -> minor, aunque tambien haya `fix`). Es decir, el trabajo sale
      como estable **sin haber pasado por beta ni un solo dia**.
- [ ] **Decision del dueno sobre como cerrar el desajuste.** Ver seccion 7, O-1.
- [ ] **NADIE DICE EN QUE RAMA SE TRABAJA, y por ahi estaba el fallo de origen.** La tabla de
      arriba de esta misma seccion lo declara desde el principio y el hueco es real. **Medido el
      2026-10-05:** `grep -i 'beta|branch|rama|push'` da **0 coincidencias** en
      `.agents/skills/id-pipeline/SKILL.md` y en `.agents/agents/openspec-dev/agent.md` (lo unico
      que sale es `mainAgent: false` y `main_window.py`), y `.taskmaster/git_safe_commit.py` no
      tiene **ni una** coincidencia de `branch` ni de `rev-parse --abbrev-ref`.
      **O sea: el bucle no eligio `main`.** El worktree estaba en `main` y ahi fueron 52 ciclos,
      porque nadie salio de la rama y la unica puerta de versionado **es ciega a la rama**. Por eso
      la casilla de arriba —"la practica no lo cumple"— no se arregla moviendo ramas: se arregla
      escribiendo la regla que falta y haciendo que el wrapper diga en que rama escribe.
      Corregirlo es `TASK-066` (T-4 y T-5 del change de O-5), no esta tarea.

## 5. DERIVA Y FICHEROS SUCOS

### D-1. `release-pipeline.md` contradice a `release.yml`

- [ ] **`softprops/action-gh-release@v2` -> real `@v3`** (`release.yml:190`).
      Documentado como `v2` en `release-pipeline.md:54`.
- [ ] **El comando de `semantic-release` esta incompleto en la doc.** La doc dice
      `npx --yes semantic-release@25`; el real es
      `npx --yes -p semantic-release@25 -p conventional-changelog-conventionalcommits@9`.
      Y el **`@9` fijado no es cosmetico**: el `presetConfig` vacio de
      `.releaserc.json` depende de ese paquete, y su mayor importa. Sin documentar, el
      siguiente que lo "simplifique" rompe los releases. El comentario del `.yml:124-137`
      explica por que; la doc no lo recoge.

### D-2. Ficheros sucos versionados

- [ ] **`_matrix_c26.py` (20 KB) en la raiz del repo.** Versionado desde `0dd2d38`.
      No lo referencia nadie; es matriz de medicion de un ciclo. Esta en la raiz publica.
- [ ] **`miniapps/` esta en `.gitignore` Y versionado** (6 ficheros). Las dos cosas a
      la vez: el ignore no aplica a lo ya trackeado, asi que sigue apareciendo en el
      repo publico. O se saca del indice, o se saca del `.gitignore` y se documenta.
- [ ] **`.taskmaster/tmp_measure_t059.py`** sin trackear, en el arbol de trabajo.
      Peligroso: **`git_safe_commit.py` hace `add -A`** (`.taskmaster/git_safe_commit.py:206`),
      asi que el proximo commit se lo lleva. Deberia estar en `.gitignore` con un patron
      `tmp_*.py` / `_matrix_*.py`.
- [ ] **`basura/` (8 ficheros).** Fuera del indice a proposito, por decision del dueno.
      **No tocar** — se borra a mano cuando toque. Dejar como esta.

### D-4. El pipeline de `beta` esta ROJO por 8 mensajes de commit

**Medido el 2026-10-04, primer push de este trabajo.** La corrida
[37228601320](https://github.com/carcheky/woptimizer/actions/runs/37228601320) fallo en
`Commits convencionales`; los otros tres jobs quedaron `skipped`. **No se publico
ninguna release y no se compilo ningun `.exe`.**

Causa: **8 de los 29 commits del rango incumplen `.commitlintrc.json`**, medidos
reproduciendo las seis reglas activas en Python (`.commitlintrc.json:4-27`):

| # | Commit | Incumplimiento |
|---|---|---|
| 4 | `docs(ciclo 52): cerrar TASK-059 ... (TASK-059)` | cabecera de 125 (max 120) |
| 5 | `fix(validador): cerrar los diez supervivientes ...` | 138 |
| 6 | `fix(validador): el check 9 ya no acusa ...` | 127 |
| 7 | `fix(docs): agregar al agregado llms-full.txt ...` | 188 |
| 14 | `docs(ciclo 51): registrar la seleccion ...` | 142 |
| 15 | `feat(tests): invariante del acordeon afirmado por efecto ...` | 212 |
| 16 | `chore(architect): T-9 afirma el invariante ...` | subject en mayuscula |
| 17 | `fix(tests): A3 cierra ASSERT_GATE ...` | 134 + mayuscula |

**Ninguno de los 8 es de este trabajo.** Son de los ciclos 51 y 52 del bucle
`id-pipeline`, que escriben subjects descriptivos y se pasan de 120.

> **Por que no se relaja la regla.** `header-max-length: 120` esta a proposito, y asi lo
> dice `release-pipeline.md:70`: «un guard que se relaja para que pase el que lo escribio
> ya no guardar». Subirla a 220 dejaria pasar los 8 y **anularia la unica regla que hoy
> detecta un mensaje mal formado antes de que semantic-release lo ignore en silencio**.
> El fallo silencioso que ese job existe para evitar es peor que 8 cabeceras largas.

- [ ] **Decidir como se resuelve. Opciones:**
  - **(a) Rebasear los 29 commits con cabeceras cortas** y pushear `beta` con `--force**.
        Exige relajar `allow_force_pushes` en `beta` (hoy no esta protegida) y reescribe
        historia ya publicada en `beta`. **Es la unica que deja el pipeline verde sin
        tocar reglas.**
  - **(b) Subir `header-max-length` a 220** y arreglar solo el `subject-case` — que no es uno
        sino **dos** commits, el #16 y el #17. Sin reescritura, pero desactiva el guard.
  - **(c) Anadir `ci(github):` con commits de correccion** — **NO FUNCIONA**: commitlint
        mira el **rango del push**, y los 8 commits siguen dentro del rango hasta que
        `beta`receba un tag y el rango se recorra desde ahi. No se puede "borrar" un
        commit del rango sin reescribir.
  - **(d) Mover la rama de trabajo a una rama nueva** (p. ej. `develop`), pushear ahi y
        dejar `beta`/`main` para lo ya publicado. Desacopla el problema de raiz.

  > [!IMPORTANT]
  > **CORRECCION DEL 2026-10-05, y el diagnostico de arriba apuntaba al commit mas caro
  > de arreglar cuando el barato estaba sin mirar.** Las cuatro opciones estan mal planteadas
  > en su premisa, y la medicion lo dice (`openspec/changes/2026-10-04-desbloquear-pipeline-commitlint/proposal.md`
  > seccion 2). Al reproducir las seis reglas de `.commitlintrc.json:4-27` sobre el rango que
  > llevaria **un push nuevo**, `4d86908..main`, sale **2 de 7**, no 8 de 29: los ocho de la
  > tabla **ya estan publicados en `origin/beta` (`4d86908`)**, y `release.yml:49-61` resuelve
  > el rango como `github.event.before..HEAD`, luego en todo push posterior **quedan fuera del
  > rango** — son abuelos, no miembros. El guard **no se relaja**: sigue teniendo el mismo poder
  > sobre todo commit futuro.
  >
  > El bloqueante real son **`ef67bf8` (128 chars) y `82f52c2` (135 chars)**, ambos de
  > `TASK-061`, y **ninguno esta en ninguna rama remota** (`git branch -r --contains` no devuelve
  > ninguna para los dos). Se reescriben sus cabeceras sin `--force` a ninguna rama.
  >
  > Esto hunde la razon de **(c)**: no es que los commits correctores no funcionen, es que no
  > **arreglan** el rojo, porque el rojo lo causan esos dos commits y hay que reescribirlos igual.
  > Y hunde **(d)**: `release.yml:8-11` y `commitlint.yml:9-13` solo disparan en `main`, `beta` y
  > el patron de mantenimiento, luego **una rama `develop` no corre ni commitlint, ni verify, ni
  > release, ni `.exe`**. Un rojo que desaparece no es un bug que deja de existir.
  >
  > **Elegido: (a') + (d')** — reescribir solo lo no publicado, `beta` por fast-forward sin
  > `--force`, y el bucle trabajando en `beta` (que ya es la rama de integracion declarada)
  > en vez de en una rama nueva. Ver O-5.

### D-5. Deriva menor

- [x] **README badges corregidos.** Decian `ciclos-20` y `tests-57 verdes`; ahora
      `ciclos-52` y `tests-132 verdes`, que es lo que el repo declara en los otros tres
      ficheros. **Por que se habia quedado en 57 sin que nada avise:**
      `validate_docs.py:118` vigila `README.md` con el patron
      `run_tests\.py\s*#\s*(\d+)\s+tests` — o sea, la linea del **comando**, no la del
      **badge**. La linea 6 era la unica del repo que miente en voz alta y ningun
      guard la alcanzaba. Corregido en `4d86908`.
- [ ] **Anadir el badge al check 7 de `validate_docs.py`**, para que no vuelva a caducar
      solo. Es el mismo agujero que ya cambio una vez por el mismo motivo.

## 6. ESTADO DEL PIPELINE Y DEL PROYECTO

- [x] **Releases existentes.** `v1.0.0-beta.1` (pre-release, 2026-10-02) y `v1.0.0`
      (estable, 2026-10-02). **Ambas con `woptimizer.exe` adjunto.** El pipeline funciona.
- [x] **Ultimas corridas en verde.** Las 2 ultimas en `main` (00:14 y 00:19 del
      2026-10-03) salen `success`.
- [x] **`release.yml` bien endurecido:** rango de commits resuelto con
      `git cat-file -e` (evita el `Invalid revision range` tras force-push),
      `cancel-in-progress: false`, `fetch-depth: 0`, build **desde el tag** y no desde
      HEAD, `permissions` minimas por job. Esta mejor de lo habitual.
- [ ] **Deuda tecnica abierta en `STATUS.md`** (seccion `## ⚠️ Deuda Tecnica Conocida`).
      Bloqueante para el bucle, no para este trabajo. Lo mas relevante:
      - `.git` corrupto por el VFS de Nextcloud — **aceptado y blindado** con
        `git_safe_commit.py`. No es reparable desde el arbol de trabajo.
      - `git_safe_commit.py` sale con codigo `0` tanto si commitea (`WOPT_COMMIT_OK`)
        como si no hace nada (`WOPT_NOOP`), y su unico consumidor ramifica por
        `exit == 0`. **Falso verde de versionado**: un fallo de git puede pasar por
        commit correcto. Esta anotado como deuda viva desde el ciclo #48.
      - Shell intermitente (`spawn EPERM`) en el entorno de agentes.
- [ ] **`validate_docs.py` no corre en CI** (deliberado, y bien justificado en el
      `.yml:89-93`): deriva `GIT_DIR` de `%LOCALAPPDATA%`, que no existe en el runner.
      Se ejecuta en el host. **Hay que acordarse de ejecutarlo antes de cada push.**

## 7. DECISIONES QUE TE TOCAN A TI

Resueltas el 2026-10-04; queda una abierta.

- [x] **O-1. Que se haces con los commits sin pushear.** **Elegido: (b), pasar por `beta`
      primero.** Hecho: `beta` movida al HEAD de `main` y pusheada
      (`41b8061..4d86908`, FF puro). **El "rebase" resulto no ser reescritura**: `beta`
      ya era ancestro de `main` y el rango tiene 0 merges, asi que `git branch -f beta
      main` produce el mismo estado sin tocar un solo SHA.
      **Consecuencia medible: el pipeline salio ROJO (D-4) y `main` sigue sin mergear.**
- [x] **O-2. Proteger `main`.** **Elegido: proteccion blanda.** Aplicada y verificada
      (ver seccion 2). Sin required checks, sin PR obligatorio, con force-push y borrado
      bloqueados.
- [x] **O-3. Licencia.** **Elegido: MIT.** `LICENSE` creado en `79039e9`. La afirmacion
      de `mkdocs.yml:88` ya es ejecutable.
- [ ] **O-4. Miniapps dentro o fuera del repo.** Ahora estan a la vez dentro y fuera.
- [x] **O-5. NUEVA y urgente: como se desbloquea el pipeline de `beta`.** **Resuelta el
      2026-10-05, al planificarla y no al aplicarla.** Ver D-4 y
      `openspec/changes/2026-10-04-desbloquear-pipeline-commitlint/`.
      **Elegido: (a') + (d').** Reescribir las cabeceras de los **dos** commits que
      incumplen y que **no estan en ninguna rama remota** (`ef67bf8`, 128 chars, y `82f52c2`,
      135 chars), empujar `beta` con **fast-forward y sin `--force`**, y que el bucle trabaje en
      `beta` en vez de en una rama nueva.
      **Por que, en tres frases medidas:** (1) los 8 commits del diagnostico original **ya no
      bloquean nada**, porque estan publicados en `origin/beta` y el rango del push los excluye;
      (2) los 2 que si bloquean son **locales**, luego el arreglo no cuesta un `--force` ni tocar
      la proteccion de `main`; (3) `beta` **ya es** la rama de integracion que declara la
      documentacion, asi que (d') consigue lo que (d) buscaba sin apagarse el CI.
      **Lo que NO se toca:** `.commitlintrc.json`, `.releaserc.json`, `.github/workflows/` y la
      proteccion de `main`. Es paso 3, y es cambio de producto.
      **Lo que se acepta como precio, escrito para no leerlo como resuelto:** los 8 commits
      largos se quedan en la historia de `beta` y saldran enteros en las notas de la release
      (semantic-release los parsea bien: el limite de 120 es de commitlint, no del parser), y
      `beta` sigue sin proteccion.

---

## 8. LO QUE SE HA HECHO EN ESTA PASADA

1. Leido `AGENTS.md`, `docs/ai/release-pipeline.md`, `.releaserc.json`, `release.yml`,
   `commitlint.yml`, `.commitlintrc.json`, `README.md`, `mkdocs.yml`, `.gitignore`, la
   seccion de deuda de `STATUS.md` y `rd_journal.json`.
2. Auditado el repo en GitHub por API (metadatos, ramas, proteccion, tags, releases,
   workflows, corridas, contenido de `main`).
3. **Metadatos aplicados y verificados por lectura:** descripcion, 11 topics, wiki off,
   projects off, discussions on, `delete_branch_on_merge` on.
4. **Proteccion blanda de `main` aplicada y verificada** con una segunda llamada
   independiente. Script reproducible: `.taskmaster/_gh_protect.py`.
5. **`LICENSE` MIT creado.**
6. **Ramas:** `beta` FF a HEAD de `main` y pusheada primero, como se decidio.
7. **README badges corregidos** a los valores reales (132 tests, 52 ciclos).
8. **Puertas ejecutadas antes de publicar, todas en verde:** `run_tests.py` ->
   `ALL TESTS PASSED` (132); `verify_ui_syntax.py` -> exito; `validate_docs.py` ->
   **122 OK, 0 FAIL**.
9. **Diagnostico del pipeline rojo:** 8 de los 29 commits incumplen `.commitlintrc.json`,
   medido reproduciendo las seis reglas activas. Ninguno es de este trabajo.
10. **Tarea TASK-064 creada** en `.taskmaster/tasks.json` con las tres decisiones y su
    justificacion, para que el commit tenga tercer testigo.
11. **Este documento.**

**Commits de esta pasada:** `20daaed`, `79039e9` (LICENSE + proteccion), `4d86908`
(badges), mas el amend de `20daaed` que corrigio el mensaje para declarar los artefactos
ajenos que `add -A` arrastro.

**Lo que NO se ha hecho y por que:** `main` no se ha mergeado (el pipeline de `beta` esta
rojo, D-4); no se ha reescrito historia (O-5 es decision tuya); los ficheros que faltan
en `.github/` (bloque 3) siguen sin crearse porque son cambios de producto, no de
configuracion.

## 9. COMO SE MARCA

- Sustituye `[ ]` por `[x]` **solo cuando hay evidencia**: salida de la API, salida de un
  comando, o SHA de commit.
- Si algo se deja a medias, `[~]` **y la razon**. Una casilla sin marcar con la razon
  escrita vale mas que una marcada sin comprobar: el bucle trata como cerrada una fila
  que no dice nada.
- Al cerrar una sesion, `python .taskmaster/git_safe_commit.py "docs(github): ..."`.
