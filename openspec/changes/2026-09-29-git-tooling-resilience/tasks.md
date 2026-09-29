# Tasks: `2026-09-29-git-tooling-resilience`

**Ciclo**: #11 | **Área**: 1 — Resiliencia & Robustez | **Taskmaster**: `TASK-022`

## Plan de implementación

- [ ] **1. Leer contexto mínimo**
  - `openspec/changes/2026-09-29-git-tooling-resilience/proposal.md`
  - `.taskmaster/git_safe_commit.py` (el fichero a modificar, 80 líneas)
  - `docs/ai/sandbox-rules.md` (sección de aislamiento Git, a documentar)
  - `run_tests.py` (patrón de tests headless existente)

- [ ] **2. Resolver y validar el repo (sin fallback)**
  - [ ] 2.1 Precedencia: si el entorno ya trae `GIT_DIR`, se respeta y **no** se sobrescribe.
        Si no, usar `%LOCALAPPDATA%\woptimizer_git\.git`. `GIT_WORK_TREE` siempre = `REPO_ROOT`.
  - [ ] 2.2 `validar_repo(env)`: exigir `rev-parse --verify HEAD` (devuelve un commit),
        `rev-parse --is-inside-work-tree` == `true` y `rev-parse --git-dir` resoluble.
        `os.path.exists` **no** basta.
  - [ ] 2.3 Si la validación falla (o `git` no es ejecutable / excepción de Python) → imprimir
        `WOPT_REPO_INVALIDO <detalle>` y salir con **3**, sin escribir nada y **sin** fallback
        al `.git` corrupto del VFS.
  - [ ] 2.4 Imprimir el repo en uso (GIT_DIR efectivo) para diagnóstico.

- [ ] **3. Hacer el wrapper fail-safe**
  - [ ] 3.1 `status --porcelain` fallido → **fatal**, no "hay cambios". (Hoy `code == 0 and not
        out` trata un status fallido como árbol con cambios.)
  - [ ] 3.2 `status --porcelain` vacío → `WOPT_NOOP arbol limpio` + `0` (fast path, sin `add`).
  - [ ] 3.3 `git add -A` fallido → `WOPT_FAIL add <detalle>` + `1`, y **abortar**: nunca ejecutar
        `commit` después (staging parcial silencioso).
  - [ ] 3.4 Decidir con `git diff --cached --quiet`: rc 0 → `WOPT_NOOP nada staged` + `0`;
        rc 1 → commitear; rc > 1 → `WOPT_FAIL` + `1`. **Nunca** parsear "nothing to commit".
  - [ ] 3.5 `commit` fallido → `WOPT_FAIL commit <detalle>` + `1`, nunca `0`.
  - [ ] 3.6 Éxito → `git rev-parse --short HEAD`; solo si rc == 0, imprimir
        `WOPT_COMMIT_OK <hash> <mensaje>` + `0`. Si el hash no se puede resolver → `1`.
  - [ ] 3.7 Sin mensaje, mensaje vacío o flag desconocido → `WOPT_USAGE <detalle>` + `2`.
  - [ ] 3.8 Todas las cadenas de `print()` en ASCII puro (comentarios/docstrings sí admiten
        acentos).

- [ ] **4. Flag `--verify`**
  - [ ] 4.1 Reutiliza **exactamente** `validar_repo()` del paso 2. Sin ruta de código propia.
  - [ ] 4.2 Imprime el resultado y sale con `0` (sano) o `3` (inválido).
  - [ ] 4.3 No escribe nada: solo `status`/`rev-parse`.

- [ ] **5. Test headless que discrimina** (en `run_tests.py`, función
      `test_git_safe_commit_fail_safe`, registrada en el `__main__`)
  - [ ] 5.1 Invocar el wrapper como **subproceso** con `GIT_DIR` apuntando a una ruta temporal
        que no es un repo → exigir returncode **!= 0** (hoy devuelve 0: el test discrimina).
  - [ ] 5.2 Caso `2`: invocarlo sin mensaje → exigir returncode 2.
  - [ ] 5.3 Guardas anti-falso-positivo: comprobar que el código de salida es **exactamente** el
        del contrato (3 en el repo inválido), no un `!= 0` genérico que pasaría por casualidad.
  - [ ] 5.4 No toca el repositorio real ni su historial (el `GIT_DIR` del subproceso se
        sobreescribe; nada escribe en `%LOCALAPPDATA%`).

- [ ] **6. Documentación viva**
  - [ ] 6.1 `docs/ai/sandbox-rules.md`: **sección nueva** "Aislamiento Git en Entornos Cloud
        (VFS)" con el contrato de códigos de salida (tabla 3.4) y `--verify`. Ese fichero hoy no
        tiene ninguna sección de Git.
  - [ ] 6.2 `AGENTS.md` §3: una línea que apunte al contrato (la regla se queda; el detalle
        operativo pasa al doc).
  - [ ] 6.3 `docs/ai/architecture.md` línea 39: ampliar el tip con el puntero al contrato.
  - [ ] 6.4 `.taskmaster/CHANGELOG.md`: entrada `[CYCLE-011]` con el hash real que imprima
        `WOPT_COMMIT_OK` (si sale `WOPT_NOOP`, se registra SIN hash, no se inventa).

- [ ] **7. Verificación obligatoria**
  - [ ] 7.1 `python verify_ui_syntax.py`
  - [ ] 7.2 `python run_tests.py`
  - [ ] 7.3 `python validate_docs.py`
  - [ ] 7.4 Commit seguro de los cambios del ciclo (incluye los 5 modificados + 2 sin
        seguimiento que el ciclo #10 dejó pendientes)

- [ ] **8. Tableros**
  - [ ] 8.1 `python .taskmaster/tm.py done TASK-022`
  - [ ] 8.2 `.taskmaster/rd_journal.json` + `.taskmaster/CHANGELOG.md` `[CYCLE-011]`
  - [ ] 8.3 `STATUS.md`

## Notas para el implementador

- **El contrato de la §3.4 del proposal.md es normativo.** Códigos: `0` commit hecho (imprime
  `WOPT_COMMIT_OK <hash>`) o nada que comitear (`WOPT_NOOP`, sin hash); `1` fallo de git; `2`
  uso incorrecto; `3` repo no verificable. No inventes un quinto código ni reutilices uno.
- **No parsees stderr para decidir.** Git localiza sus mensajes según el locale, así que
  `"nothing to commit"` no es detectable en un Windows en español. Usa
  `git diff --cached --quiet` (rc 0 = nada staged, rc 1 = hay staged, rc > 1 = error).
- **`run_git` devuelve `(1, "", str(e))` ante excepción de Python.** Para el paso de validación
  eso significa "no pude comprobar" → código `3`, no `1`.
- El repo **no** es un repo git healthy por defecto: el `.git` del árbol de trabajo está corrupto
  por el VFS de Nextcloud (`fatal: bad object HEAD`). **Usa siempre** el wrapper, nunca `git` a
  pelo. Si necesitas `git` directo, exporta antes:
  ```powershell
  $env:GIT_DIR = "$env:LOCALAPPDATA\woptimizer_git\.git"
  $env:GIT_WORK_TREE = "C:\Users\carch\Nextcloud\Scripts\woptimizer"
  ```
- Para el test, **no** muevas ni copies el repo real: sobreescribe `GIT_DIR` en el entorno del
  subproceso del wrapper y apúntalo a una ruta temporal.
- `AGENTS.md` exige **0 cambios pendientes** al cerrar el bloque. Este ciclo recupera
  precisamente de un ciclo que no lo cumplió.
- Trampa #16 vigente: nada de `→`, `✓`, emoji ni acentos en cadenas de `print()` (consola
  cp1252). Comentarios y docstrings sí pueden llevar acentos.
- Las invariantes de producto (separación UI/services, kill recursivo, pack gaming protegido)
  **no aplican**: este cambio es de tooling y no toca `src/woptimizer/`.

