# Propuesta: Resiliencia del Tooling Git del Pipeline (fail-safe en `git_safe_commit.py`)

- **Change ID**: `2026-09-29-git-tooling-resilience`
- **Ciclo**: #11
- **Área de rotación**: 1 — Resiliencia & Robustez (sin tocar desde el ciclo #6)
- **Taskmaster**: `TASK-022`
- **Subagente de ejecución**: `openspec-dev`
- **Estado**: APROBADO para implementación

## 1. Problema

AGENTS.md §"Cierre Limpio (Cero Cambios Pendientes)" obliga a que **todo** bloque termine con
`python .taskmaster/git_safe_commit.py "..."`. Ese wrapper es, por tanto, la única puerta de
salida del versionado del proyecto, y el pipeline entero depende de que su **código de salida**
sea honesto.

Hoy no lo es. `.taskmaster/git_safe_commit.py` (líneas 71-77) captura **cualquier** fallo de
commit, imprime `AVISO GIT: Commit no completado (...)` y hace `sys.exit(0)`.

### Consecuencias (todas silenciosas)

1. **Pérdida de trabajo sin aviso.** El orquestador y los subagentes interpretan `exit 0` como
   "commit correcto" y avanzan al siguiente paso. Los cambios quedan únicamente en disco.
2. **Trazabilidad falsa.** La sección 6 de `id-pipeline/SKILL.md` es MANDATORY: el changelog
   registra `Commits: <hash>`. Con el wrapper roto, ese hash se inventa o se deja vacío y el
   registro deja de ser verificable.
3. **Invariante indetectable.** `validate_docs.py` valida que el CHANGELOG *exista* y tenga
   entradas, pero **no puede** comprobar que el commit citado exista. Un ciclo puede "completarse"
   sin haber versionado nada y toda la validación pasa en verde.
4. **Staging parcial silencioso.** Si `git add -A` falla (líneas 60-62), solo se emite un warning
   y el `commit` se ejecuta igual: se puede commitear un subconjunto de ficheros creyendo que se
   versionó todo.
5. **Redirección GIT_DIR sin validar.** `get_env()` (líneas 19-24) activa el repo desacoplado de
   `LOCALAPPDATA` **si y solo si la ruta existe**, sin comprobar que sea un repositorio válido.
   Si esa carpeta se corrompe o es otro clon, *todos* los commits se escriben en una historia
   distinta y el árbol real nunca se versiona, sin ningún error.

### Evidencia observada en el ciclo #11

Al inspeccionar el repo, `git status` directo falló con:

```
error: unable to open loose object 585a9da8c312abe03bbc8152c0084f4f6222560c: Function not implemented
fatal: bad object HEAD
```

Es decir, el `.git` **dentro** del árbol de trabajo está corrupto (VFS de Nextcloud), y la única
razón por la que el historial sigue vivo es el repo desacoplado en
`%LOCALAPPDATA%\woptimizer_git\.git` (746 objetos, HEAD `c9e6948`, sano).

**Esto demuestra que el punto ciego del punto 5 no es hipotético: hoy es la condición real del
proyecto.** Un wrapper que activa una redirección sin validarla no puede distinguished entre
"repo correcto" y "repo corrupto": en ambos casos sale con 0.

## 2. Objetivo

Convertir `git_safe_commit.py` en un wrapper **fail-safe**: que solo devuelva 0 cuando el commit
se ha realizado de verdad (o cuando el árbol esté genuinamente limpio), y que emita **código de
salida distinto de cero** ante cualquier fallo real, para que el pipeline se detenga en lugar de
registrar un commit inexistente.

## 3. Alcance

### 3.1 Cambios en `.taskmaster/git_safe_commit.py`

| # | Cambio | Justificación |
|---|--------|---------------|
| 1 | `git add -A` fallido → **error fatal**, no warning | Staging parcial = pérdida silenciosa |
| 2 | Fallo de `commit` → `sys.exit(1)`, no `sys.exit(0)` | Honrar el código de salida |
| 3 | Distinguir "nada que comitear" (benigno, exit 0) de "fallo" (exit 1) | El árbol limpio no es un error |
| 4 | En éxito, imprimir el **hash real** (`git rev-parse --short HEAD`) | Changelog con hash verificable |
| 5 | Validar el GIT_DIR desacoplado antes de usarlo (`rev-parse --verify HEAD`, `--is-inside-work-tree`, `--git-dir`) | Detectar repo corrupto o clonado |
| 6 | Si la redirección es inválida → **error explícito**, nunca fallback silencioso al `.git` corrupto del VFS | Fallar rápido y visible |
| 7 | Nuevo flag `--verify`: autocomprobación del repo, sin modificar nada, exit != 0 si el repo no es sano | Diagnóstico barato y seguro |
| 8 | Respetar un `GIT_DIR` ya definido en el entorno (no sobrescribirlo) | Vía documentada en AGENTS.md + hook de test hermético |
| 9 | Decidir "nada que comitear" con `git diff --cached --quiet`, **nunca** parseando stderr | Ver §3.4: los mensajes de git se traducen según locale |
| 10 | Todas las cadenas de `print()` en ASCII puro | Trampa #16 (consola cp1252) |

### 3.2 Tests

Añadir cobertura headless del contrato del wrapper. Debe verificar lo que de verdad importa:
**que un fallo de git NO produzca exit 0**. Caso obvio a cubrir: repo inexistente o GIT_DIR
apuntando a una ruta inválida → exit distinto de cero.

Ubicación: función `test_git_safe_commit_fail_safe()` en **`run_tests.py`**, porque es el único
gate que AGENTS.md exige ejecutar; un test en otro fichero no se ejecutaría nunca. Se implementa
como test de **subproceso** (el script se invoca con `GIT_DIR` apuntando a una ruta temporal
inválida), sin importar el módulo y sin tocar el repo real.

### 3.3 Documentación (Documentación Viva Obligatoria)

- `docs/ai/sandbox-rules.md`: **crear una sección nueva** "Aislamiento Git en Entornos Cloud
  (VFS)". Corrección importante: ese fichero hoy **no tiene ninguna sección de Git** (solo
  sandbox EPERM, bypass de PyInstaller y el invariante de `dist/woptimizer.exe`). La regla de
  aislamiento Git vive hoy en `AGENTS.md` §3, y el tip de `docs/ai/architecture.md:39`. El
  contrato de códigos de salida y el flag `--verify` se documentan en el sitio nuevo.
- `AGENTS.md` §3: añadir una línea que apunte al contrato en `docs/ai/sandbox-rules.md` (la
  regla de aislamiento se queda ahí como fuente, el detalle operativo pasa al doc).
- `docs/ai/architecture.md` línea 39: ampliar el tip de una línea con el puntero al contrato.
- `.taskmaster/CHANGELOG.md`: entrada `[CYCLE-011]` (obligatoria, sección 6 de la skill).

No hace falta regenerar `llms-full.txt`: `validate_docs.py` solo concatena `docs/*.md`, y los
ficheros tocados viven en `docs/ai/`.

### 3.4 CONTRATO DE CÓDIGOS DE SALIDA (normativo)

El wrapper es la única señal de éxito del versionado. Este contrato es **obligatorio** y
no admite variantes.

| Código | Significado | Cuándo | stdout (línea canónica) |
|---|---|---|---|
| `0` | Commit creado de verdad | `git commit` returncode 0 | `WOPT_COMMIT_OK <hash-short> <mensaje>` |
| `0` | No había nada que comitear (benigno, **no** es error) | `git diff --cached --quiet` == 0 tras `add -A` | `WOPT_NOOP <motivo>` |
| `1` | Fallo de una operación de git | `git add -A` o `git commit` con returncode != 0, o excepción al lanzarlos | `WOPT_FAIL <operacion> <detalle>` |
| `2` | Uso incorrecto | sin mensaje, mensaje vacío o flag desconocido | `WOPT_USAGE <detalle>` |
| `3` | Repositorio no verificable | `GIT_DIR` inexistente, no es un git dir, `HEAD` no resuelve, `is-inside-work-tree` != true, o git no ejecutable | `WOPT_REPO_INVALIDO <detalle>` |

Reglas adicionales, igualmente obligatorias:

1. **`0` solo si el commit ocurrió o si no había nada que comitear.** Cualquier otro desenlace
   es `!= 0`. No existe ningún camino que devuelva `0` por error.
2. **Nunca fallback.** Si el `GIT_DIR` desacoplado falla la validación → `3` y **no** se intenta
   el `.git` del árbol de trabajo (está corrupto por el VFS).
3. **`git add -A` fallido aborta inmediatamente con `1`.** No se ejecuta `commit` después: eso es
   staging parcial silencioso.
4. **La línea canónica `WOPT_*` va siempre a stdout** y es la única que el pipeline debe leer
   para el CHANGELOG. Todo el detalle humano va también a stdout (se conserva el flujo único
   actual); stderr queda libre para el detalle de los subprocesos.
5. **`WOPT_NOOP` nunca imprime hash.** El agente no debe inventar uno en el CHANGELOG.
6. **El hash de `WOPT_COMMIT_OK` se obtiene con `git rev-parse --short HEAD` después** del
   commit, y solo se imprime si esa llamada tiene returncode 0.
7. **Strings de `print()` en ASCII puro**: nada de acentos, flechas, checks ni emoji. El wrapper
   re-encoda stdout a UTF-8 pero la consola es cp1252, así que los acentos salen como mojibake.
   Los comentarios y docstrings sí pueden llevar acentos.
8. **Precedencia de `GIT_DIR`:** si el entorno ya trae `GIT_DIR`, se respeta y no se sobrescribe
   (`GIT_WORK_TREE` se sigue fijando a `REPO_ROOT`). Si no, se usa
   `%LOCALAPPDATA%\woptimizer_git\.git`. La validación se aplica **igual** en ambos casos.

## 4. Fuera de alcance

- **NO** tocar `src/woptimizer/**`. Este cambio es de tooling, no de producto. La UI y los
  servicios no se ven afectados y sus invariantes no aplican.
- **NO** reescribir, rebasear ni "arreglar" el `.git` corrupto del árbol de trabajo. La estrategia
  vigente (repo desacoplado en LOCALAPPDATA) es correcta; lo que falla es su validación.
- **NO** eliminar ni "limpiar" el historial de 5 ficheros modificados + 2 sin seguimiento que el
  ciclo #10 dejó sin commitear. Se commitean tal cual: el pipeline perdió su propio cambio, y
  eso es exactamente lo que este ciclo arregla.
- **NO** añadir dependencias nuevas.

## 5. Criterios de aceptación

Cada línea es binaria y se comprueba leyendo el código de salida del wrapper.

- [ ] `0` solo aparece en dos casos, y solo esos: commit creado (con hash real) o nada que
      comitear. Ningún otro desenlace devuelve `0`.
- [ ] `git add -A` fallido devuelve `1` y **no** intenta el `commit` después.
- [ ] `commit` fallido por un motivo real devuelve `1` (nunca `0`).
- [ ] Árbol genuinamente limpio devuelve `0` con `WOPT_NOOP` y **sin** hash. Un mensaje sin
      sentido no es un fallo: es un no-op honesto.
- [ ] Un éxito imprime `WOPT_COMMIT_OK <hash>` y ese hash existe en el historial.
- [ ] `GIT_DIR` desacoplado no válido → `3`, sin escribir nada y sin fallback al `.git` del
      árbol de trabajo.
- [ ] Uso incorrecto (sin mensaje / mensaje vacío / flag desconocido) → `2`.
- [ ] `GIT_DIR` preexistente en el entorno se respeta y no se sobrescribe.
- [ ] `--verify` ejecuta exactamente la misma validación que el camino principal, no escribe
      nada, y devuelve `0` / `3` según el repo esté sano o no.
- [ ] Todas las cadenas de `print()` del wrapper son ASCII puro.
- [ ] Test headless que **discrimina**: con `GIT_DIR` inválido exige `!= 0`, y falla si alguien
      revierte el fix del código de salida.
- [ ] El test no toca el repositorio real ni su historial.
- [ ] `python verify_ui_syntax.py`, `python run_tests.py` y `python validate_docs.py` en verde.
- [ ] `docs/ai/sandbox-rules.md` tiene la sección nueva con el contrato de códigos de salida y
      `--verify`; `AGENTS.md` y `docs/ai/architecture.md` apuntan a ella.
- [ ] Árbol de git limpio al final del ciclo (0 cambios pendientes).

## 6. Riesgo

**Bajo.** Fichero aislado de 80 líneas, sin dependencias, sin impacto en la app. El riesgo real
no es técnico: es que el fix sea *demasiado tímido* (mantener exit 0 "por compatibilidad"). Por eso
el criterio de aceptación exige explícitamente el test que discrimina.

## 7. Revisión de arquitectura (correcciones al diseño original)

**Veredicto: viable**, con 3 correcciones obligatorias y 2 recortes de sobre-ingeniería.

### 7.1 Corrección 1 (ERROR): no se puede decidir con el texto de stderr

El diseño original proponía mantener el `if "nothing to commit" in combined` (línea 73 del
script actual). **Eso no es fiable**: git traduce sus mensajes según `LANG`/`LC_ALL`, así que
en un locale no inglés la cadena literal no aparece nunca, y el "árbol limpio" se clasificaría
como fallo → `1` en un caso que debe ser `0`. Al revés también duele: un fallo de identidad de
usuario puede producir texto parecido.

La comprobación autoritativa es **`git diff --cached --quiet`**:
- returncode `0` → no hay nada staged → `WOPT_NOOP` + `0`.
- returncode `1` → hay staged → se puede commitear.
- returncode `>1` → error real de git → `1`.

Es locale-independiente y no depende de parsear texto. El `status --porcelain` inicial se
conserva solo como fast path para saltarse el `add` cuando el árbol está limpio, pero **su
fallo debe ser fatal**: hoy `if code == 0 and not out` (línea 55) trata un `status` fallido
como "hay cambios" y sigue adelante. Eso se invierte.

### 7.2 Corrección 2 (ERROR): falta el hook de test

Sin una vía para apuntar a otro repo, el test del criterio "repo inválido" tendría que tocar el
repo real. La solución elegida no es un flag nuevo sino respetar el `GIT_DIR` preexistente del
entorno, que además es la convención estándar de git y la vía que ya documenta `AGENTS.md` §3.
Cero flags nuevos, tests herméticos.

### 7.3 Corrección 3 (ERROR): `run_git` mezcla excepción con fallo de git

`run_git` devuelve `(1, "", str(e))` cuando la excepción es del propio Python (git no
instalado, `OSError`). Para el paso de validación esa ambigüedad importa: "no puedo ni
comprobar" es `3`, no `1`. Especificado en el contrato 3.4.

### 7.4 Recorte 1: `--verify` se queda, pero sin ruta de código propia

**Recomendación: mantenerlo, sin sobre-ingeniería.** El razonamiento: la validación del repo
tiene que existir igual en el camino principal (si no, el fix del punto ciego no está), así que
el flag cuesta ~4 líneas: validar, imprimir, `sys.exit(0)`. Y aporta algo que ningún otro
mecanismo da: cuando el pipeline recibe un `!= 0`, necesita diagnosticar **sin escribir nada**.
Se prohíbe explícitamente que `--verify` tenga comportamiento distinto del validado normal.

### 7.5 Recorte 2: NO comprobar identidad "repo == proyecto"

**Recomendación: descartarlo como sobre-ingeniería.** El wrapper fuerza `GIT_WORK_TREE =
REPO_ROOT`, así que `git rev-parse --show-toplevel` siempre devolverá `REPO_ROOT`: la
comparación no puede fallar, es teatro. Y no hay marcador barato y no ambiguo de "este
proyecto" (el repo desacoplado es local, sin remote). Lo que de verdad detecta los fallos reales
—repo corrupto, clon equivocado, HEAD roto— ya lo cubren `rev-parse --verify HEAD`,
`--is-inside-work-tree` y `--git-dir`, que están en el contrato 3.1 #5.

### 7.6 Invariantes de AGENTS.md: cuáles aplican y cuáles no

**No aplican** (el cambio no toca `src/woptimizer/`): separación UI/services, kill recursivo,
pack gaming protegido. No hay ninguna tensión que inventar ahí.

**Sí aplican**:
- *Documentación Viva Obligatoria* → §3.3, con la corrección de ubicación.
- *Cierre limpio con 0 cambios pendientes* → criterio de aceptación final. Ironía útil: este
  ciclo existe precisamente porque un ciclo anterior no lo cumplió.
- *Aislamiento Git en cloud* (`AGENTS.md` §3) → es la regla que este cambio blinda, no la rompe.
  El `GIT_DIR` desacoplado se mantiene; lo que cambia es que ahora se valida.

