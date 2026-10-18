# TASK-077 · tareas de ejecucion

> Contrato de `openspec/changes/2026-10-18-eol-real-y-exit-de-build/proposal.md`.
> Decisiones medidas, no supuestos. **4 bloques; F4 es separable.**

---

## Orden de ejecución y por qué en ese orden

```
F1 (checkout)  ->  F2 (.gitattributes)  ->  F3 (guard)  ->  F4 (S3)
```

**F1 antes que F3, sin excepción.** El guard F3.1 falla hoy *a propósito*: mide el
drift que F1 limpia. Si se ejecuta F3 antes de F1, `run_tests.py` queda rojo y no
se sabe si es el guard que newly sí mide o un fallo de F4. **F1 no commitea nada**,
así que no se pierde por ir primero.

**F4 al final** porque es el único bloque que **cambia el contenido de `build.bat`**,
y el guard de F3 lee sus bytes. Con F4 ya aplicado, F3 sigue verde (los bytes CRLF
se conservan al reescribir el `.bat`: **hay que escribirlos en CRLF o F3 se pone
rojo solo**).

---

## F1 · Re-materializar los 37 ficheros del árbol local

**Quién:** dev. **Commitea:** nada. **Difiere:** cero.

```powershell
git checkout-index -f -- .commitlintrc.json .github/workflows/commitlint.yml `
  .github/workflows/release.yml .gitignore .releaserc.json `
  .taskmaster/_gh_configure.py .taskmaster/_gh_incert1.py .taskmaster/_gh_probe.py `
  .taskmaster/_gh_protect.py _chk.py _chk2.py assets/process_db.json `
  docs/GITHUB-SETUP-CHECKLIST.md docs/ai/ui-design-system.md `
  docs/archive/legacy-root-data/README.md docs/archive/legacy-root-data/profiles.json `
  docs/archive/legacy-skills/architect/SKILL.md `
  docs/archive/legacy-skills/openspec-dev/SKILL.md `
  docs/archive/legacy-skills/process-db-updater/SKILL.md docs/index.md docs/testing.md `
  force_build.py llms-full.txt `
  openspec/changes/2026-09-28-v3-ui-redesign/tasks.md `
  openspec/changes/2026-09-29-process-db-update/proposal.md `
  openspec/changes/2026-10-03-github-releases-semantic-release/proposal.md `
  openspec/changes/2026-10-03-github-releases-semantic-release/tasks.md `
  openspec/changes/2026-10-03-pack-seleccion-por-categoria/proposal.md `
  openspec/changes/2026-10-03-pack-seleccion-por-categoria/tasks.md `
  openspec/changes/2026-10-04-desbloquear-pipeline-commitlint/proposal.md `
  openspec/changes/2026-10-04-desbloquear-pipeline-commitlint/tasks.md `
  run.py validate_docs.py build.bat `
  src/woptimizer/__init__.py src/woptimizer/__main__.py `
  src/woptimizer/services/gaming_service.py src/woptimizer/ui/confirmation.py
```

**Restricciones, por lo que se midió:**

- **Lista explícita, no `-a`.** El encargo pidió no tocar de más; `-a` reescribiría
  los 256.
- **`checkout-index -f`, no `checkout --`.** `checkout --` depende de que git
  considere el fichero modificado; `-f` escribe siempre desde el índice (§2.3).
- **`build.bat` va en la lista**: es el único que la política quiere en CRLF y es
  el único que hoy está en LF.
- **4 ficheros están bajo `src/woptimizer/**`.** Es normalización de **bytes del
  árbol**, no edición de código: el contenido del índice es idéntico antes y
  después y **no se genera ningún commit**. El arquitecto no lo ejecuta por scope;
  lo ejecuta el dev y lo deja anotado en `STATUS.md`.

**Verificación de F1:**

```
git ls-files --eol | <agrupar>     # solo deben quedar i/lf w/lf, i/none w/none, i/-text w/-text
git ls-files --eol -- build.bat    # i/lf  w/crlf  attr/text eol=crlf   <-- el objetivo
git status --porcelain            # vacio: F1 no debe ensuciar nada
git diff --cached --stat          # vacio: F1 no toca el indice
```

---

## F2 · Corregir la justificación de `.gitattributes` — **el único diff real**

**Quién:** dev. **Commitea:** sí.

Solo el **comentario** de `.gitattributes:18-20`. **Las tres reglas `eol=crlf` se
conservan** (§3.1).

**Sustituir** la afirmación de que Windows no tolera LF por la medida:

- `cmd.exe` moderno **ejecuta** un `.bat` en LF: medido idéntico byte a byte en
  6 escenarios, incluidos `if errorlevel 1 (` multilínea, `if exist (…) else (…)`,
  `goto :label` y la **última línea sin salto de terminador** (`build.bat` no
  termina en `0x0A`: último byte `0x30`).
- Se declara CRLF **por convención nativa de Windows y por determinismo del árbol
  de trabajo**, no porque el parser se rompa.
- Anotar **por qué `--renormalize` no sirve** (`STATUS.md:75` lo propone): el
  índice ya está normalizado, y `eol=crlf` actúa en el **checkout**, no en el
  `add`. Medido: 0 ficheros staged.

**No reescribir el bloque de historia** (líneas 1-16), que es correcto.

---

## F3 · Guard de política EOL en `run_tests.py`

**Quién:** dev. **Commitea:** sí. **Añade:** 2 tests.

```
F3.1  test_la_politica_eol_cubre_todo_script_de_consola_que_existe
F3.2  test_el_guard_de_eol_rechaza_lo_mismo_que_acepta      <- CONTRAPRUESTA
```

### F3.1 · Qué afirma, y por qué discrimina

| # | Afirmación | Por qué no es tautológica |
|---|---|---|
| (a) | la regla base se **deriva** de `.gitattributes` y vale `lf` | leída del fichero; una constante la mata el mutante E4 |
| (b) | toda extensión `.bat`/`.cmd`/`.ps1` **presente en el repo** tiene regla `crlf` efectiva, **y el conjunto presente no es vacío** | sin la segunda mitad, borrar `build.bat` vacía el bucle y el test pasa |
| (c) | los **bytes** de cada uno: hay `\r\n` y **no hay ni un `\n` suelto** | **hoy falla**: `build.bat` tiene 0 CRLF. Falla por la aserción |
| (d) | el contenido **normalizado** (`\r\n`→`\n`) **no lleva ningún `\r`** | caza la clase `3012c48` |

**Por qué (c) discrimina hoy:** `build.bat` en disco tiene 39 `\n` y 0 `\r`.
`b.replace(b"\r\n", b"")` deja los 39 `\n` intactos → (c) falla. Con F1 aplicado
pasa. **El test es rojo antes del fix y verde después: eso es lo que lo hace test
y no una descripción.**

### F3.2 · Por qué existe, y por qué discrimina

Es la contraprueba de F3.1, y responde al patrón «una comprobación sin
contraprueba no es una comprobación» (ciclos 60 y 62; aquí, cuarta vez).

Cámara en `%TEMP%` con el **`.gitattributes` real** y tres `.bat` sintéticos:

| Escenario | Resultado exigido |
|---|---|
| `.bat` con CRLF | el evaluador dice **OK** |
| `.bat` con LF | el evaluador dice **FAIL** |
| regla `*.bat` borrada, `.bat` presente | **FAIL** por (b) |

**Si el evaluador devolviera `OK` siempre**, los tres darían `OK` y el test muere.
Sin F3.2, un F3.1 entero se puede vaciar.

### Restricciones de F3

- **Texto puro.** `.gitattributes` se lee como texto (no es YAML) y el escaneo es
  `rglob`. **Sin PyYAML** (no está en el repo, ciclo 64), **sin `subprocess`**
  (no ensuciar la lista de llamadas de P1), **sin ventanas**.
- **Nada de `git ls-files --eol` como aserción.** En CI, `actions/checkout` aplica
  los atributos en el checkout fresco, así que ese comando **reportaría `w/crlf`
  esté o esté el repo sano**: no es un falso rojo, es un **verde falso**. Vale
  como diagnóstico, no como veredicto.

### F3.3 · Recuento de tests (efecto colateral obligatorio)

`validate_docs.py` **deriva** el número con `ast` y lo ata a cuatro sitios. Al
añadir F3.1, F3.2, F4.1 y F4.2 hay que actualizar **a la vez**, o el validador
pasa a rojo:

- `run_tests.py` — los `def test_*` **y** su invocación al final, con el bloque
  `Suite: N -> N+k` y el reparto `backend + headless`.
- `docs/ai/testing-guide.md` — **una fila por test definido**.
- `STATUS.md:12`, `AGENTS.md:70`, `README.md:63` — el número **derivado**.

**Se planifica +4 y el dev escribe el número que `validate_docs.py` mida**, como en
TASK-076 (el encargo pidió 208, eran 207, y se escribió el real).

**En la misma pasada**, corregir la fila D2 de `STATUS.md` (§6.1 de la proposal):
de los tres sitios que nombra, **solo `README.md:6` sigue caducado**, y hay un
cuarto que D2 no nombra: **`STATUS.md:109`**, `(207 tests)`.

---

## F4 · 🔴 Absorber S3 (`STATUS.md:62`) — propagar el código de salida

**Quién:** dev. **Commitea:** sí. **Añade:** 2 tests.
**Separable:** si el orquestador prefiere no mezclarlo, se corta F4 entero.

### El bug, re-medido

Stub `python.cmd` en `%PATH%` que sale **0** si los argumentos contienen
`PyInstaller` y **7** si no:

```
build.bat en LF, compilacion fallida con 7  ->  EXITCODE=0     <-- confirmado
```

`build.bat:27` invoca `python force_build.py` sin propagar el código y
`build.bat:40` cierra con `exit /b 0` incondicional. Un `.exe` roto sale por aquí:
`release.yml` sí propaga (el runner añade `exit $LASTEXITCODE`), **`build.bat` no**.

### F4.1 · `test_build_bat_propaga_el_codigo_de_salida_de_force_build`

Cámara: copia de `build.bat` + stub `python.cmd` en `%TEMP%`, ejecutada con
`cmd /c`. **Hoy sale 0** → rojo. Con el fix, sale **7**.

Discrimina porque mide el **código de salida del `.bat`**, no su texto: un
`build.bat` que propagase `errorlevel` pero cerrara con `exit /b 0` seguiría
dando 0 y el test lo mata.

### F4.2 · `test_la_camara_de_build_bat_detecta_la_regresion` — CONTRAPRUESTA

Sobre una **copia** en `%TEMP%`, reponer `exit /b 0` al final tiene que **volver a
dar 0**. Si F4.1 pasara con cualquiera de las dos variantes, la cámara no mide nada.

### Restricción que se cruza con F3

Al reescribir `build.bat` (F4) hay que **escribirlo en CRLF**. Si el dev lo guarda
en LF, F3.1(c) se pone rojo y el ciclo se cierra con dos guards en conflicto.
**Comprobación cruzada obligatoria al cerrar: los 37 de F1 y el `build.bat` de F4.**

---

## Mutantes para el `mutation-auditor`

| Id | Mutante | Test que lo mata | Por qué |
|---|---|---|---|
| **E1** | borrar `*.bat text eol=crlf` de `.gitattributes` | F3.1 (b) | `build.bat` existe y su EOL efectivo pasa a `lf` |
| **E2** | **`build.bat` a LF en disco** | F3.1 (c) | LF sin `\r` antecedente. **Mutante vivo hoy** |
| **E3** | CR duro a mitad de línea en `build.bat` | F3.1 (d) | el normalizado conserva el `0x0D` |
| **E4** | resolvedor de atributos → constante | F3.2 | el `.bat` LF tiene que dar FAIL |
| **E5** | F3.1 vaciado (`pass` / `return`) | F3.2 | los tres escenarios darían OK |
| **S1** | `exit /b 0` incondicional al final | F4.1 | la cámara mide 0 donde exige != 0 |
| **S2** | cámara de F4 que acepta cualquier código | F4.2 | la regresión tiene que volver a dar 0 |
| **S3** | `if errorlevel 1` de `build.bat:14` eliminado | F4.1 | PyInstaller ausente tiene que dar != 0 |

**Ninguno en seguridad ni datos.** Si uno sobrevive, se arregla; no se documenta.

---

## Cierre del ciclo

1. `python run_tests.py` → verde, con el número **derivado** escrito en los 4 sitios.
2. `python validate_docs.py` → **0 FAIL**.
3. `python verify_ui_syntax.py` → verde.
4. `STATUS.md:75` — la fila de deuda de TASK-077: cerrar o reescribir con la
   medida de `proposal.md` §1-§3.
5. `STATUS.md:82` (D2) — corregir la cita, §6.1.
6. Changelog en los **dos** ficheros: `CHANGELOG.md` y `.taskmaster/CHANGELOG.md`.
7. Commit por `python .taskmaster/git_safe_commit.py "<mensaje> (TASK-077)"`,
   **con identificador**, en `beta`. Nunca `main`.