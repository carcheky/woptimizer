# Releases del `.exe` en GitHub con semantic-release y conventional commits

**Change ID:** `2026-10-03-github-releases-semantic-release`
**Tarea:** `TASK-062` (ciclo #50)
**Alcance:** `.github/workflows/`, `.releaserc.json`, `package.json`, `commitlint.config.json`, `docs/ai/release-pipeline.md`, `README.md`, `AGENTS.md`.
**NO toca:** `src/woptimizer/**`. Cero cambios de codigo de producto.

---

## 1. Que se arregla

`.github/workflows/build.yml` publicaba releases **a mano**: alguien tenia que crear el tag `v*` y empujarlo. Eso tiene tres fallos medidos:

1. **La version no la decide nadie.** El tag lo pone el pulso del teclado, no el contenido del commit. Un `fix:` puede ir a `v9.9.9` y un `feat:` a `v1.0.1` sin que nada se queje.
2. **El `.exe` publicado puede no ser el del codigo.** Nada ata el binario a un commit concreto.
3. **No hay red:** si el build falla, la release queda publicada y sin ejecutable, y reintentarlo es manual.

Ademas hay una fila **viva** en la Deuda Tecnica Conocida que este trabajo **cierra de hecho**: `STATUS.md:81` (checkpoint de distribucion) declara que "el ejecutable es un artefacto de distribucion, no un checkpoint" y que **nadie vigila su desfase con el codigo**. Con este pipeline, cada release se compila **desde el commit etiquetado**, asi que el desfase deja de existir por construccion en el camino de las releases.

## 2. Diseno: cuatro jobs encadenados

Un unico workflow, `release.yml`, con `needs:` explicitos. Cada job hace **una** cosa y falla de forma legible:

```
commits (ubuntu)  ->  verify (windows)  ->  release (ubuntu)  ->  build (windows)
 commitlint          suite + sintaxis      semantic-release      PyInstaller + asset
```

| Job | Runner | Por que ese runner |
|---|---|---|
| `commits` | ubuntu | Node, y el rango de commits es lo unico que necesita |
| `verify` | **windows** | La app es Windows; los tests tocan `psutil`, `taskkill` y rutas |
| `release` | ubuntu | Node puro; es donde vive semantic-release |
| `build` | **windows** | PyInstaller compila un `.exe`: no hay otra opcion |

### Ramas

| Rama | Tipo | Version que produce |
|---|---|---|
| `main` | release estable | `1.0.0`, `1.0.1`, `2.0.0` |
| `beta` | prerelease | `1.1.0-beta.1`, `1.1.0-beta.2` |
| `N.x` / `N.N.x` | mantenimiento | `1.0.3` en su propio canal |

`beta` existe para **probar el pipeline antes de que toque la version estable**: ahi una Release se marca automaticamente como *pre-release* en GitHub, asi que no puede confundirse con la estable.

Al fusionar `beta` en `main`, semantic-release **gradua** el prerelease y publica la version estable que le corresponde. Ese es el mecanismo por el que este ciclo termina en `1.0.0` y no en `1.0.0-beta.3`.

## 3. Decisiones que NO son obvias, y por que

### 3.1 `validate_docs.py` NO corre en CI, y es deliberado

Su ancla de commits deriva el repositorio de `%LOCALAPPDATA%\woptimizer_git\.git` (`validate_docs.py:300-302`), una ruta que **solo existe en el host del dueno**. En un runner de GitHub no esta: `git log` falla y el validador reporta `FAIL` con un repo impecable. Meterlo en el gate seria un rojo permanente que no significa nada.

**Regla:** `validate_docs.py` se ejecuta en el host, antes de empujar. Nunca en CI.

### 3.2 El job `build` compila el **tag**, no el HEAD

`actions/checkout` con `ref: <tag>`. Si alguien empuja mientras compila, la release sigue siendo reproducible respecto al commit que la nombra. Compilar el HEAD de la rama publicaria un binario que no corresponde al tag.

### 3.3 La version se lee por **diff de tags**, no por `git describe`

`git describe --tags --abbrev=0` devuelve **el ultimo tag alcanzado**, tambien cuando esta corrida no publico nada. En ese caso el job `build` reconstruiria y volveria a subir el ejecutable de una release **anterior**. El job congela la lista de tags antes de correr semantic-release y calcula el **diff**; si esta vacio, `tag` sale vacio y `build` se salta (`if: needs.release.outputs.tag != ''`).

### 3.4 Los flags de PyInstaller se copian de `force_build.py`

`--onefile --noconsole --uac-admin --name woptimizer --clean --add-data "assets;assets"`. Si divergen del build local, el `.exe` publicado deja de ser el mismo producto que el que se compila en casa. **Una sola fuente de verdad para los flags**, aunque hoy este en dos sitios y vigilada por comentario.

### 3.5 `build.yml` se retira

Disparaba con `push: tags: ['v*']`. Con semantic-release, **cada tag que crea dispara tambien ese workflow**, que competiria por la misma release. Dos workflows escribiendo el mismo recurso no es un pipeline, es una carrera. Su funcion (compilar el `.exe`) queda absorbida por el job `build`.

### 3.6 `validate_docs.py` obliga a mantener el recuento de tests sincronizado

El check 7 deriva el numero de tests de `run_tests.py` con `ast` y lo compara con **`STATUS.md`, `AGENTS.md`, `README.md`** y la tabla de `docs/ai/testing-guide.md`. Este cambio **no toca `run_tests.py`** precisamente para no arrastrar esa sincronizacion. La regla para futuros ciclos: si anades un test, actualiza los cuatro ficheros o `validate_docs.py` falla.

## 4. Permisos: minimo privilegio

`permissions: contents: read` global. Solo el job `release` sube a `contents: write` (crear tag y release) y solo `build` lo necesita para adjuntar el asset. Los comentarios automaticos de `@semantic-release/github` van **desactivados** (`successComment`, `failComment`, `releasedLabels`), asi que no hace falta `issues: write` ni `pull-requests: write`.

## 5. Criterios de aceptacion

- [x] Push a `beta` con un `feat:` produce una Release marcada como **pre-release** con el `.exe` adjunto.
- [x] Fusionar `beta` en `main` produce la Release estable `1.0.0` con el `.exe` adjunto.
- [x] Un commit `docs:` o `chore:` **no** publica nada (y el job `build` se salta).
- [x] Un mensaje de commit no convencional **falla** el pipeline en vez de publicar en silencio.
- [x] `build.yml` ya no existe.
- [x] `run_tests.py`, `verify_ui_syntax.py` y `validate_docs.py` en verde en el host.
