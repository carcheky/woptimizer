#!/usr/bin/env python3
"""
git_safe_commit.py - Wrapper de commit blindado para woptimizer (Windows + Nextcloud/VFS).

En entornos con Virtual Files (Nextcloud/OneDrive) el `.git` que vive dentro del
arbol de trabajo queda corrupto (`fatal: bad object HEAD`), asi que el historial
real vive en un repo desacoplado en `%LOCALAPPDATA%\\woptimizer_git\\.git`. Este
wrapper redirige GIT_DIR ahi ANTES de tocar nada y VALIDA que ese repo sea
utilizable. Nunca hace fallback al `.git` del arbol de trabajo: si el repo
desacoplado no valida, se sale con codigo 3.

CONTRATO DE CODIGOS DE SALIDA (normativo, documentado en docs/ai/sandbox-rules.md):
    0  WOPT_COMMIT_OK <hash-short> <mensaje>   commit creado de verdad
    0  WOPT_NOOP <motivo>                      no hay nada que comitear (benigno)
    1  WOPT_FAIL <operacion> <detalle>         fallo de una operacion de git
    2  WOPT_USAGE <detalle>                    uso incorrecto
    3  WOPT_REPO_INVALIDO <detalle>            repositorio no verificable

`--verify` es un modo diagnostico de solo lectura: reutiliza EXACTAMENTE la misma
validacion, imprime `WOPT_REPO_OK <git_dir>` + 0 si el repo esta sano, o
`WOPT_REPO_INVALIDO <detalle>` + 3 si no. Nunca comitea.

Uso:
    python .taskmaster/git_safe_commit.py "tipo(scope): descripcion"
    python .taskmaster/git_safe_commit.py --verify
"""

import sys
import os
import re
import subprocess
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_GIT_DIR = os.path.expandvars(r"%LOCALAPPDATA%\woptimizer_git\.git")

# Codigos de salida del contrato (no inventar otros).
CODE_OK = 0
CODE_FAIL = 1
CODE_USAGE = 2
CODE_REPO = 3

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def detalle(texto, max_len=240):
    """Normaliza cualquier texto a una unica linea ASCII imprimible.

    La consola es cp1252 (trampa #16) y git puede emitir acentos, codigos de
    color ANSI o saltos de linea. Sin esta normalizacion, un `print()` revienta
    con UnicodeEncodeError justo en el mensaje de error, que es el que mas urge.
    """
    if not texto:
        return "sin detalle"
    limpio = _ANSI_RE.sub("", str(texto))
    limpio = limpio.replace("\r", " ").replace("\n", " ")
    limpio = limpio.encode("ascii", "replace").decode("ascii")
    limpio = " ".join(limpio.split())
    if len(limpio) > max_len:
        limpio = limpio[:max_len].rstrip() + "..."
    return limpio


def get_env():
    """Construye el entorno de git para todos los subprocesos.

    Precedencia: si el entorno YA trae `GIT_DIR` se respeta tal cual (es la via
    documentada en AGENTS.md y ademas el hook que permite tests hermeticos). Si
    no, se fuerza el repo desacoplado de LOCALAPPDATA **aunque no exista**: asi
    la validacion falla con codigo 3 en vez de que git descubra en silencio el
    `.git` corrupto del arbol de trabajo (fallback prohibido por el contrato).
    """
    env = os.environ.copy()
    env["GIT_DIR"] = env.get("GIT_DIR") or LOCAL_GIT_DIR
    env["GIT_WORK_TREE"] = REPO_ROOT
    return env


def run_git(args, env):
    """Ejecuta `git` y devuelve (rc, out, err, exc).

    `rc` es None cuando git NO llego a ejecutarse (excepcion de Python: no
    instalado, OSError, sandbox...). Esa distincion importa: "git fallo" es
    codigo 1, pero "no pude ni comprobar" es codigo 3. Colapsar los dos casos en
    el mismo 1 era el agujero que el contrato 3.4 corrige.
    """
    try:
        res = subprocess.run(
            ["git"] + args,
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        return res.returncode, res.stdout.strip(), res.stderr.strip(), None
    except Exception as e:
        return None, "", "", str(e)


def validar_repo(env):
    """Valida el repo efectivo. Devuelve (ok, detalle_error, git_dir_real).

    Es la UNICA validacion del wrapper: la usan igual el camino principal y
    `--verify`, de modo que el diagnostico nunca puede divergir del comportamiento
    real. Es de solo lectura (solo `rev-parse`) y no acepta una excepcion como
    "repo valido": `os.path.isdir` no basta, hay que preguntar a git.
    """
    git_dir = env.get("GIT_DIR") or LOCAL_GIT_DIR
    if not os.path.isdir(git_dir):
        return False, f"GIT_DIR no existe o no es un directorio: {git_dir}", git_dir

    rc, out, err, exc = run_git(["rev-parse", "--git-dir"], env)
    if exc is not None:
        return False, f"git no ejecutable: {detalle(exc)}", git_dir
    if rc != 0 or not out:
        return False, f"rev-parse --git-dir fallo (rc={rc}): {detalle(err or out)}", git_dir
    git_dir_real = out

    rc, out, err, exc = run_git(["rev-parse", "--is-inside-work-tree"], env)
    if exc is not None:
        return False, f"git no ejecutable: {detalle(exc)}", git_dir
    if rc != 0 or out.strip().lower() != "true":
        return False, (
            f"is-inside-work-tree no es true (rc={rc}, out='{detalle(out)}'): {detalle(err)}"
        ), git_dir_real

    rc, out, err, exc = run_git(["rev-parse", "--verify", "HEAD"], env)
    if exc is not None:
        return False, f"git no ejecutable: {detalle(exc)}", git_dir
    if rc != 0 or not out:
        return False, f"HEAD no resuelve (rc={rc}): {detalle(err or out)}", git_dir_real

    return True, "", os.path.abspath(git_dir_real)


def parse_args(argv):
    """Devuelve (verify, mensaje, error_de_uso)."""
    verify = False
    posicionales = []
    for arg in argv:
        if arg == "--verify":
            verify = True
        elif arg.startswith("-"):
            return False, None, f"flag desconocido: {arg}"
        else:
            posicionales.append(arg)

    if verify and posicionales:
        return False, None, "--verify no admite un mensaje de commit"
    if len(posicionales) > 1:
        return False, None, "se esperaba un unico mensaje entrecomillado"
    mensaje = posicionales[0].strip() if posicionales else ""
    if not verify and not mensaje:
        return False, None, "falta el mensaje de commit (o esta vacio)"
    return verify, mensaje, None


def imprimir_uso():
    print('Uso: python .taskmaster/git_safe_commit.py "tipo(scope): descripcion"')
    print("     python .taskmaster/git_safe_commit.py --verify")


def main():
    verify, mensaje, error_uso = parse_args(sys.argv[1:])
    if error_uso:
        imprimir_uso()
        print(f"WOPT_USAGE {detalle(error_uso)}")
        sys.exit(CODE_USAGE)

    env = get_env()
    ok, fallo_repo, git_dir = validar_repo(env)

    if verify:
        # Modo diagnostico: misma validacion, cero escrituras.
        if ok:
            print(f"WOPT_REPO_OK {git_dir}")
            sys.exit(CODE_OK)
        print(f"WOPT_REPO_INVALIDO {detalle(fallo_repo)}")
        sys.exit(CODE_REPO)

    if not ok:
        # Sin fallback: el .git del arbol de trabajo esta corrupto en VFS.
        print(f"WOPT_REPO_INVALIDO {detalle(fallo_repo)}")
        print("INFO no se intenta el .git del arbol de trabajo: fallback prohibido.")
        sys.exit(CODE_REPO)

    print(f"INFO git_dir en uso: {git_dir}")

    # 1. status --porcelain como fast path. Un status FALLIDO es un error, no
    #    "hay cambios": la version anterior hacia justo eso y segua hacia add.
    rc, out, err, exc = run_git(["status", "--porcelain"], env)
    if exc is not None or rc != 0:
        print(f"WOPT_FAIL status {detalle(exc or err or out)}")
        sys.exit(CODE_FAIL)
    if not out:
        print("WOPT_NOOP arbol limpio (status --porcelain vacio)")
        sys.exit(CODE_OK)

    # 2. add -A. Si falla, ABORTAR: comitear despues seria staging parcial
    #    silencioso (solo se versionaria una parte de los cambios).
    rc, out, err, exc = run_git(["add", "-A"], env)
    if exc is not None or rc != 0:
        print(f"WOPT_FAIL add {detalle(exc or err or out)}")
        sys.exit(CODE_FAIL)

    # 3. Hay algo staged? Se decide con `diff --cached --quiet`, NO parseando el
    #    texto de git: "nothing to commit" se traduce segun LANG/LC_ALL y en un
    #    Windows en espanol no aparece nunca, lo que convertiria un arbol limpio
    #    en un fallo. rc 0 = nada staged, rc 1 = hay staged, rc > 1 = error.
    rc, out, err, exc = run_git(["diff", "--cached", "--quiet"], env)
    if exc is not None:
        print(f"WOPT_FAIL diff {detalle(exc)}")
        sys.exit(CODE_FAIL)
    if rc == 0:
        print("WOPT_NOOP nada staged tras add -A")
        sys.exit(CODE_OK)
    if rc != 1:
        print(f"WOPT_FAIL diff (rc={rc}) {detalle(err or out)}")
        sys.exit(CODE_FAIL)

    # 4. commit. Cualquier fallo real es codigo 1, nunca 0.
    rc, out, err, exc = run_git(["commit", "-m", mensaje], env)
    if exc is not None or rc != 0:
        print(f"WOPT_FAIL commit {detalle(exc or err or out)}")
        sys.exit(CODE_FAIL)

    # 5. Hash real y solo si resuelve: sin hash no se inventa nada en el CHANGELOG.
    rc, out, err, exc = run_git(["rev-parse", "--short", "HEAD"], env)
    if exc is not None or rc != 0 or not out:
        print(f"WOPT_FAIL hash-no-resoluble {detalle(exc or err or out)}")
        sys.exit(CODE_FAIL)

    primera_linea = out.splitlines()[0].strip() if out else ""
    if primera_linea:
        print(f"INFO commit: {detalle(primera_linea)}")
    # La linea canonica va SIEMPRE la ultima: es la unica que lee el pipeline.
    print(f"WOPT_COMMIT_OK {out.splitlines()[0].strip()} {detalle(mensaje, 120)}")
    sys.exit(CODE_OK)


if __name__ == "__main__":
    main()
