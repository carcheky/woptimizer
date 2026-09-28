#!/usr/bin/env python3
"""
git_safe_commit.py - Wrapper de commit blindado para woptimizer en entornos Nextcloud/Windows.
Uso:
    python .taskmaster/git_safe_commit.py "tipo(scope): descripcion"
"""

import sys
import os
import subprocess
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_GIT_DIR = os.path.expandvars(r"%LOCALAPPDATA%\woptimizer_git\.git")

def get_env():
    env = os.environ.copy()
    if os.path.exists(LOCAL_GIT_DIR):
        env["GIT_DIR"] = LOCAL_GIT_DIR
        env["GIT_WORK_TREE"] = REPO_ROOT
    return env

def run_git(args, env):
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
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

def main():
    if len(sys.argv) < 2:
        print("Uso: python .taskmaster/git_safe_commit.py \"mensaje de commit\"")
        sys.exit(1)

    message = sys.argv[1].strip()
    if not message:
        print("Error: El mensaje de commit no puede estar vacio.")
        sys.exit(1)

    env = get_env()

    # 1. Comprobar si hay cambios
    code, out, _ = run_git(["status", "--porcelain"], env)
    if code == 0 and not out:
        print("INFO: No hay cambios pendientes para comitear.")
        sys.exit(0)

    # 2. git add -A
    code, out, err = run_git(["add", "-A"], env)
    if code != 0:
        print(f"ADVERTENCIA en git add: {err or out}. Continuando...")

    # 3. git commit -m
    code, out, err = run_git(["commit", "-m", message], env)
    if code == 0:
        print(f"EXITO COMMIT: {message}")
        print(out.splitlines()[0] if out else "")
        sys.exit(0)
    else:
        # Si falló porque no había cambios o por lock temporal
        combined = f"{out}\n{err}"
        if "nothing to commit" in combined or "working tree clean" in combined:
            print("INFO: Nada que comitear (arbol limpio).")
            sys.exit(0)
        print(f"AVISO GIT: Commit no completado ({err or out}). Cambios persistidos en disco.")
        sys.exit(0)

if __name__ == "__main__":
    main()
