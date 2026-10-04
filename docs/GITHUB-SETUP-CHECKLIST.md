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

## 2. RAMAS Y PROTECCION — ⚠️ DECISION PENDIENTE

- [x] **`beta` existe y esta publicada** en `origin` (`41b8061`).
- [x] **`.releaserc.json` declara las ramas correctas**: `main` (estable), `beta`
      (`prerelease: "beta"`), y el patron `1.x` / `1.1.x` para mantenimiento.
- [x] **`release.yml` dispara en `main` y `beta`.** Correcto.
- [~] **Proteccion de `main`: SIN APLICAR A PROPOSITO.** No existe (API devuelve 404).
- [ ] **Sincronizar `beta` con `main`.** `beta` esta 15 commits por detras. Sin esto,
      el proximo push a `beta` crearia un tag de beta con una version **anterior** a la
      estable ya publicada, y la graduation automaticaria publicaria una release
      **descendente**. Es un redsistema, no un descuido.
- [ ] **Decision del dueno: proteger `main` o no.**
      - **A favor:** nadie puede publicar una estable sin pasar los tests.
      - **En contra (razon real, no teorica):** el job `release` empuja los **tags** con
        `GITHUB_TOKEN` y `contents: write`. Con `main` protegida, eso falla con **403**
        y **no se publica ninguna release**. El fallo ya esta documentado en
        `release-pipeline.md:67`.
      - **Lo que yo haria:** proteger `main` **sin required status checks**, solo
        `block force pushes` + `require PR to merge` desactivado, y dejar los tests como
        puerta logica en `release.yml` (que ya lo es). Proteccion fuerte +
        `GITHUB_TOKEN` de publicacion = releases rotas.
      - **Pendiente de tu OK.** No lo aplico por mi cuenta porque rompe el pipeline.

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
      Hay **`feat(categorias):`** entre ellos. Cuando se pusheen, **dos releases
      estables** (1.1.0 y 1.0.1) saldaran de un golpe, directo de `main`.
- [ ] **Decision del dueno sobre como cerrar el desajuste.** Ver seccion 7, O-1.

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

### D-3. Deriva menor

- [ ] **README badges caducados.** Dicen `ciclos-20` y `tests-57 verdes`. La realidad es
      ciclo **51** y **124 tests**. `validate_docs.py` check 7 deriva el total de tests
      con `ast` y compara con `AGENTS.md`, `STATUS.md` y `docs/ai/testing-guide.md` —
      **`README.md` no lo incluye**, asi que por eso se ha quedado en 57 sin que nada
      avise. La linea 6 de `README.md` es la unica del repo que miente en voz alta.
- [ ] **Referencia de la doc a `softprops/action-gh-release@v2`** — mismo punto que D-1.

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

Ordenadas por urgencia. Ninguna aplicada por mi cuenta.

- [ ] **O-1. Que se hace con los 15 commits sin pushear en `main`.**
      - (a) **Pushear `main` tal cual** -> salen 2 releases estables de golpe (1.1.0 y
            1.0.1). Simple, pero **nunca pasan por `beta`**.
      - (b) **Rebasar `main` sobre `beta` y pushear `beta` primero** -> pre-releases,
            luego merge a `main`. Cumple el flujo documentado. Cuesta un rebase.
      - (c) **Fusionarlos tal cual y seguir trabajando en `beta` desde ahora**, aceptando
            que este tramo salio sin beta.
      *Yo haria (b) si el historial es lineal y limpio, o (c) si no quieres tocar
      historia ya publicada. (a) es la que menos trabajo da y la que menos cumple el flujo.*
- [ ] **O-2. Proteger `main` o no** (ver seccion 2). Mi propuesta: proteccion **blanda**,
      sin required checks, para no romper el empuje de tags del job `release`.
- [ ] **O-3. Licencia.** Confirmar **MIT** (es lo que `mkdocs.yml` ya afirma) u otra.
- [ ] **O-4. Miniapps dentro o fuera del repo.** Ahora estan a la vez dentro y fuera.

---

## 8. LO QUE SE HA HECHO EN ESTA PASADA

1. Leido `AGENTS.md`, `docs/ai/release-pipeline.md`, `.releaserc.json`, `release.yml`,
   `commitlint.yml`, `README.md`, `mkdocs.yml`, `.gitignore`, la seccion de deuda de
   `STATUS.md`.
2. Auditado el repo en GitHub por API (metadatos, ramas, proteccion, tags, releases,
   workflows, corridas, contenido de `main`).
3. **Aplicado** (bloque 1): descripcion, 11 topics, wiki off, projects off,
   discussions on, `delete_branch_on_merge` on.
4. **Sin aplicar a proposito:** proteccion de ramas (rompe el pipeline de releases, ver
   O-2) y todo lo que requiere crear ficheros nuevos o reescribir historia (bloques 3,
   5 y 6), porque son cambios de producto y los decides tu.
5. **Este documento.**

## 9. COMO SE MARCA

- Sustituye `[ ]` por `[x]` **solo cuando hay evidencia**: salida de la API, salida de un
  comando, o SHA de commit.
- Si algo se deja a medias, `[~]` **y la razon**. Una casilla sin marcar con la razon
  escrita vale mas que una marcada sin comprobar: el bucle trata como cerrada una fila
  que no dice nada.
- Al cerrar una sesion, `python .taskmaster/git_safe_commit.py "docs(github): ..."`.
