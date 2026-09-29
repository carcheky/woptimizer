# Reglas de Sandbox, Permisos y Compilación Windows

## El Problema del Sandbox (EPERM)
El entorno de ejecución de agentes en Windows a menudo restringe la creación directa de subprocesos (`Access is denied` / `EPERM`) al invocar `cmd.exe`, `powershell.exe` o comandos que crean forks masivos.

## Patrones Permitidos y Soluciones

### 1. Ejecución de Código Python
- `python script.py` usando `run_command` **SÍ** está permitido siempre que el script no intente hacer llamadas directas no autorizadas a shells externas.
- Siempre inicializar el encoding de consola al inicio de los scripts puente para evitar errores de Windows cp1252:
  ```python
  import sys, io
  sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
  ```

### 2. Bypass de Shell para Compilación (PyInstaller)
- NUNCA llamar a `pyinstaller` mediante comandos de shell si el sandbox bloquea subprocesos.
- Ejecutar mediante el builder nativo síncrono `force_build.py` o mediante la API de Python:
  ```python
  import subprocess, sys
  subprocess.check_call([
      sys.executable, "-m", "PyInstaller",
      "--onefile", "--noconsole", "--uac-admin",
      "--name", "woptimizer", "--clean",
      "src/woptimizer/__main__.py"
  ])
  ```
- O delegar al shell de Windows sin bloqueo de proceso hijo usando `build_trigger.vbs` con `os.startfile()`.

### 3. Invariante de Salida
- El ejecutable siempre debe colocarse en: `dist/woptimizer.exe`.
- Debe incluir el flag `--uac-admin` para poder matar procesos elevados de sistema.

## Aislamiento Git en Entornos Cloud (VFS)

En Windows con unidades virtuales (Nextcloud / OneDrive) el `.git` que vive **dentro** del árbol de
trabajo se corrompe: el filtro VFS no soporta la creación de objetos (`unable to create temporary
file: Invalid argument`, `fatal: bad object HEAD`). En este repositorio esa es la condición real,
no hipotética. La estrategia vigente es **desacoplar el historial** a una ruta local:

```powershell
$env:GIT_DIR = "$env:LOCALAPPDATA\woptimizer_git\.git"
$env:GIT_WORK_TREE = "C:\Users\carch\Nextcloud\Scripts\woptimizer"
```

`.taskmaster/git_safe_commit.py` es la **única puerta de salida del versionado** (AGENTS.md §2 lo
impone en cada ciclo) y automatiza esa redirección. Por eso su código de salida es un contrato
normativo: si el pipeline lee un `0` donde no hubo commit, registra un hash inexistente y el
ciclo se da por versionado sin haberlo estado.

### Contrato de códigos de salida

| Código | Significado | Cuándo | Línea canónica en stdout |
|---|---|---|---|
| `0` | Commit creado de verdad | `git commit` con returncode 0 | `WOPT_COMMIT_OK <hash-short> <mensaje>` |
| `0` | Nada que comitear (benigno) | `git diff --cached --quiet` == 0 tras `add -A` | `WOPT_NOOP <motivo>` (**sin hash**) |
| `1` | Fallo de una operación de git | `git status`, `git add -A` o `git commit` con rc != 0, o excepción al lanzarlos | `WOPT_FAIL <operacion> <detalle>` |
| `2` | Uso incorrecto | sin mensaje, mensaje vacío, más de un posicional o flag desconocido | `WOPT_USAGE <detalle>` |
| `3` | Repositorio no verificable | `GIT_DIR` inexistente, no es un git dir, `HEAD` no resuelve, `is-inside-work-tree` != `true`, o `git` no ejecutable | `WOPT_REPO_INVALIDO <detalle>` |

Reglas duras (TASK-022, `openspec/changes/2026-09-29-git-tooling-resilience/`):

1. **`0` solo aparece en dos casos**: commit creado (con hash real) o nada que comitear. Ningún
   otro desenlace devuelve `0`.
2. **Nunca hay fallback.** Si el `GIT_DIR` desacoplado no valida → `3` sin escribir nada. Nunca
   se intenta el `.git` del árbol de trabajo.
3. **`git add -A` fallido aborta con `1`**, sin ejecutar `commit`: seguir sería staging parcial
   silencioso.
4. **La línea `WOPT_*` va a stdout y es la última que se imprime.** Es la única que el pipeline
   debe leer. `WOPT_NOOP` nunca imprime hash (el agente no inventa hashes en el CHANGELOG).
5. **Nada que comitear se decide con `git diff --cached --quiet`** (rc 0 = nada staged, rc 1 =
   hay staged, rc > 1 = error), **nunca** parseando stderr: git traduce sus mensajes según
   `LANG`/`LC_ALL`, así que `"nothing to commit"` no aparece nunca en un Windows en español y un
   árbol limpio se clasificaría como fallo.
6. **Un `git status` fallido es un error, no "hay cambios".** Se valida el repositorio con
   `rev-parse --git-dir`, `rev-parse --is-inside-work-tree` y `rev-parse --verify HEAD`;
   `os.path.exists()` no basta.
7. **Precedencia de `GIT_DIR`:** si el entorno ya lo trae, se respeta y no se sobrescribe (es la
   vía documentada arriba y además el hook que permite tests herméticos). Si no, se usa
   `%LOCALAPPDATA%\woptimizer_git\.git`. La validación se aplica igual en ambos casos.
8. **Todas las cadenas de `print()` del wrapper son ASCII puro** (trampa #16: la consola es
   cp1252). Los comentarios y docstrings sí llevan acentos.

### Flag `--verify`

```bash
python .taskmaster/git_safe_commit.py --verify
```

Autocomprobación **de solo lectura** (solo `rev-parse`): ejecuta **exactamente** la misma función
`validar_repo()` que el camino principal —prohibido darle una ruta de código propia— e imprime
`WOPT_REPO_OK <git_dir>` + `0` si el repositorio está sano, o `WOPT_REPO_INVALIDO <detalle>` + `3`
si no. Es el mecanismo de diagnóstico cuando el pipeline recibe un `!= 0` sin escribir nada.

### Cobertura

`run_tests.py` -> `test_git_safe_commit_fail_safe()` invoca el wrapper como subproceso con
`GIT_DIR` apuntado a rutas temporales inválidas y exige los códigos exactos del contrato
(`3` y `2`). Es un test que **discrimina**: revierte el fix del código de salida y falla. No toca
el repositorio real ni su historial.
