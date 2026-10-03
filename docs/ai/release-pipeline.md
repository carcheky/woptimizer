# Pipeline de Releases (semantic-release + conventional commits)

> Como se decide la version, como se compila el `.exe` y que se hace cuando algo falla.
> Para el **por que** de cada decision: `openspec/changes/2026-10-03-github-releases-semantic-release/proposal.md`.

---

## 1. La regla de oro

**El mensaje de commit DECIDE la version.** No hay version escrita a mano en ningun sitio.

| Commit | Version |
|---|---|
| `fix(algo): ...` | **patch** (1.0.0 -> 1.0.1) |
| `feat(algo): ...` | **minor** (1.0.0 -> 1.1.0) |
| `BREAKING CHANGE:` en el pie, o `feat!:` / `fix!:` | **major** (1.0.0 -> 2.0.0) |
| `perf(algo): ...` | **patch** |
| `docs:`, `chore:`, `refactor:`, `test:`, `ci:`, `build:`, `style:` | **no publica nada** |

Las reglas viven en `.releaserc.json` (`releaseRules`), **no** en la configuracion por defecto de semantic-release. estan escritas a mano a proposito: una tabla que se lee es una tabla que se puede auditar.

## 2. Ramas

| Rama | Tipo | Tags | Notas |
|---|---|---|---|
| `main` | estable | `v1.0.0`, `v1.0.1` | La unica que publica version final |
| `beta` | prerelease | `v1.1.0-beta.1` | Las Releases salen marcadas **pre-release** en GitHub |
| `1.x`, `1.1.x` | mantenimiento | `v1.0.3` | Solo cuando haya que mantener una linea vieja |

**Ciclo de trabajo normal:**

```bash
# 1. Trabajo en beta: aqui se prueba el pipeline sin tocar la version estable
git switch -c beta
git commit -m "feat(telemonetria): contador de RAM en la Portada"
python .taskmaster/git_safe_commit.py ...   # ver AGENTS.md: nunca `git commit` a pelo
git push origin beta                       # -> Release v1.1.0-beta.N

# 2. Cuando beta vale, se graduated
git switch main
git merge --ff-only beta
git push origin main                       # -> Release v1.1.0
```

> `--ff-only` a proposito: un merge commit con el mensaje `Merge branch 'beta'` **no** es un conventional commit y lo mata el job `commits`.

## 3. Los cuatro jobs

`commits` (ubuntu) -> `verify` (windows) -> `release` (ubuntu) -> `build` (windows)

1. **`commits`** — `commitlint` sobre **el rango del push actual** (`github.event.before..HEAD`). Sin este paso, un mensaje mal escrito no da error: semantic-release lo ignora y no publica nada. Ese es el fallo silencioso que hace poco fiable un pipeline de releases.
2. **`verify`** — `verify_ui_syntax.py` + `run_tests.py` en **windows**, que es donde la app vive.
3. **`release`** — `npx --yes semantic-release@25`. Calcula la version, crea el tag y la Release.
4. **`build`** — PyInstaller **desde el commit etiquetado**, y adjunta `dist/woptimizer.exe` con `softprops/action-gh-release@v2`.

## 4. `validate_docs.py` NO se ejecuta en CI

Su ancla de commits deriva el repo de `%LOCALAPPDATA%\woptimizer_git\.git` (`validate_docs.py:300-302`), una ruta que **solo existe en el host del dueno**. En un runner de GitHub no esta, `git log` falla y el validador reporta `FAIL` con el repo impecable.

**Se ejecuta en el host, antes de empujar. Nunca en CI.**

## 5. Cuando algo falla

| Sintoma | Causa | Que hacer |
|---|---|---|
| `ERELEASEBRANCHES` | La rama no esta en `branches` de `.releaserc.json` | Anadirla. No es un fallo de semantic-release, es una rama no declarada |
| `Git push failed ... 403` | `main` tiene branch protection y `GITHUB_TOKEN` no puede escribir | Publicar desde una GitHub App, o relajar la proteccion para el job `release` |
| La Release sale sin `.exe` | El job `build` fallo ( casi siempre PyInstaller ) | Re-run del job fallido en la pestana Actions. Reconstruye **el mismo tag** |
| `fatal: Invalid revision range <sha>..HEAD` en el job `commits` | `github.event.before` apunta a un commit que ya no es alcanzable: tras un force-push, un squash o un rebase | Ya esta blindado: el job comprueba `git cat-file -e` y cae a `HEAD~1`. Si aun asi falla, revisa que el push no haya reescrito historia |
| Commitlint falla con `header-max-length` | Cabecera de mas de 120 caracteres | Acortala. La regla no se relaja: un guard que se relaja para que pase el que lo escribio ya no guarda |
| No sale ninguna release y el pipeline esta verde | Ningun commit `feat`/`fix`/`perf` en el push | Correcto, no es un fallo. `docs:` y `chore:` no publican |
| El job `build` se salta | No hubo tag nuevo en esta corrida | Correcto: no hay release que adjuntar |
| `run_tests.py` falla en `test_logging_va_a_fichero_y_no_a_stderr` con `WinError 32` | El `.log` esta bloqueado **en el host**, no en CI | Ver abajo |

### El falso positivo del `WinError 32`

`test_logging_va_a_fichero_y_no_a_stderr` falla en el host cuando `src/woptimizer/woptimizer.log` ha superado el tope de rotacion **y** el VFS de Nextcloud lo tiene abierto. El rename del rollover falla, la stdlib manda el aviso a `lastResort` (stderr) y la asercion revienta.

**No es un fallo del producto y no ocurre en CI** (checkout limpio, sin VFS). Se distingue asi:

```bash
Move-Item src\woptimizer\woptimizer.log $env:TEMP\   # si falla con "being used by another process"
# -> es el VFS, no el codigo
```

Remedio en el host: truncar el log a 0 bytes. No se puede **borrar** ni renombrar (el VFS no abre con `FILE_SHARE_DELETE`).

## 6. Ver el estado sin `gh`

No hay `gh` CLI en esta maquina. El estado se lee por API publica (el repo es publico):

```
https://api.github.com/repos/carcheky/woptimizer/releases
https://api.github.com/repos/carcheky/woptimizer/actions/runs
https://api.github.com/repos/carcheky/woptimizer/tags
```

## 7. Invariante para futuros ciclos

> Si anades un test a `run_tests.py`, actualiza **los cuatro** ficheros que declaran el recuento: `STATUS.md`, `AGENTS.md`, `README.md` y la tabla de `docs/ai/testing-guide.md`. El check 7 de `validate_docs.py` lo deriva con `ast` y falla si no cuadra.
