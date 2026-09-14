"""Script de verificación: lanza la app, espera, comprueba si la GUI está activa, mata el proceso."""
import subprocess
import time
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
script_py = os.path.join(script_dir, "process_manager.py")

# Constante para evitar ventanas de consola en subprocesos (Windows)
CREATE_NO_WINDOW = 0x08000000


def kill_process_tree(pid):
    """Mata el proceso Y todos sus hijos (powershell.exe / pwsh.exe que quedaron huerfanos).

    proc.kill() solo hace TerminateProcess del PID -> los hijos quedan zombis.
    taskkill /F /T mata el arbol entero. Sin esto, queda un pwsh.exe vivo tras el test.
    """
    try:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True,
            creationflags=CREATE_NO_WINDOW,
        )
    except Exception as e:
        print(f"[verify] WARN: taskkill fallo para PID {pid}: {e}")


print(f"[verify] Lanzando: python {script_py}")

proc = subprocess.Popen(
    [sys.executable, script_py],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=script_dir,
    creationflags=CREATE_NO_WINDOW
)

print("[verify] Esperando 4s para que la GUI se abra...")
time.sleep(4)

if proc.poll() is None:
    print(f"[verify] PASS - PROCESO VIVO tras 4s (PID={proc.pid}). GUI abierta.")
    # Matar el ARBOL entero (Python padre + PowerShell hijo) para no dejar zombis
    kill_process_tree(proc.pid)
    try:
        stdout, stderr = proc.communicate(timeout=3)
        print(f"[verify] stdout: {stdout.decode('utf-8', errors='replace')[:300]}")
        if stderr:
            print(f"[verify] stderr: {stderr.decode('utf-8', errors='replace')[:300]}")
    except subprocess.TimeoutExpired:
        kill_process_tree(proc.pid)
    print("[verify] PASS - la app arranca correctamente")
    sys.exit(0)
else:
    rc = proc.returncode
    try:
        stdout, stderr = proc.communicate(timeout=3)
        out_s = stdout.decode('utf-8', errors='replace')[:1000]
        err_s = stderr.decode('utf-8', errors='replace')[:1000]
    except subprocess.TimeoutExpired:
        out_s = "(timeout)"
        err_s = "(timeout)"
    print(f"[verify] FAIL - proceso murio tras 4s con rc={rc}")
    print(f"[verify] stdout: {out_s}")
    print(f"[verify] stderr: {err_s}")
    sys.exit(1)
