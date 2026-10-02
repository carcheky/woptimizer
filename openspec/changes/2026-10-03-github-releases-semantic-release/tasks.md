# Tasks — `2026-10-03-github-releases-semantic-release`

**Tarea:** `TASK-062` (ciclo #50)

## Implementado

- [x] T1. `.releaserc.json` con ramas `main` (estable), `beta` (prerelease) y `N.x`/`N.N.x` (mantenimiento), `tagFormat` `v${version}` y `releaseRules` explicitas.
- [x] T2. `package.json` minimo y `private: true` (el paquete de producto es Python; esto no se publica en npm).
- [x] T3. `commitlint.config.json` autocontenido (sin `extends`, para que `npx @commitlint/cli` lo resuelva sin instalar un shareable config).
- [x] T4. `.github/workflows/release.yml` con los cuatro jobs encadenados `commits -> verify -> release -> build`.
- [x] T5. `.github/workflows/commitlint.yml` para PRs (en push directo lo cubre el job `commits`).
- [x] T6. Retirado `.github/workflows/build.yml`.
- [x] T7. `docs/ai/release-pipeline.md` + seccion en `README.md` + comandos en `AGENTS.md`.

## Verificacion en GitHub (no se cierra hasta verla)

- [x] V1. Push a `beta` -> Release **pre-release** con `woptimizer.exe` adjunto.
- [x] V2. `git merge --ff-only beta` + push a `main` -> Release estable **`1.0.0`** con `woptimizer.exe` adjunto.
- [x] V3. El tag remoto final es `v1.0.0` y es el ultimo.

## Fuera de alcance (y por que)

- **Publicar en PyPI.** El producto se distribuye como `.exe` de GitHub Releases; anadir PyPI meteria un registry mas sin pedir que nadie lo pidio.
- **`@semantic-release/git` (commit `chore(release):` en `main`).** Exige que el token pueda escribir en la rama de release. Si `main` tiene branch protection, ese commit falla y tumba la release entera. El `CHANGELOG.md` de este repo lo escribe el orquestador a mano, asi que el plugin solo anadiria un commit automatico que nadie lee.
- **`validate_docs.py` en CI.** Ver seccion 3.1 de `proposal.md`: su ancla deriva un `GIT_DIR` que solo existe en el host del dueno.
