import subprocess
import sys
import os
import time

script_dir = os.path.dirname(os.path.abspath(__file__))
script_pyw = os.path.join(script_dir, "process_manager.pyw")

# Constante para evitar ventanas de consola en subprocesos (Windows)
CREATE_NO_WINDOW = 0x08000000


def kill_process_tree(pid):
    """Mata el proceso Y todos sus hijos (powershell.exe / pwsh.exe huerfanos).

    proc.kill() solo hace TerminateProcess del PID -> los hijos quedan zombis.
    taskkill /F /T mata el arbol entero.
    """
    try:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True,
            creationflags=CREATE_NO_WINDOW,
        )
    except Exception as e:
        print(f"[verify_pyw] WARN: taskkill fallo para PID {pid}: {e}")


# Buscar pythonw.exe
python_exe = sys.executable
python_dir = os.path.dirname(python_exe)
pythonw_exe = os.path.join(python_dir, "pythonw.exe")

if not os.path.exists(pythonw_exe):
    print(f"[verify_pyw] pythonw.exe no encontrado en {python_dir}")
    sys.exit(1)

print(f"[verify_pyw] Lanzando: {pythonw_exe} {script_pyw}")

proc = subprocess.Popen(
    [pythonw_exe, script_pyw],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=script_dir
)

print("[verify_pyw] Esperando 4s...")
time.sleep(4)

if proc.poll() is None:
    print(f"[verify_pyw] PASS - pythonw.exe mantiene GUI viva (PID={proc.pid})")
    # Matar el ARBOL entero para no dejar PowerShell huerfano
    kill_process_tree(proc.pid)
    try:
        stdout, stderr = proc.communicate(timeout=3)
        if stdout:
            print(f"[verify_pyw] stdout: {stdout.decode('utf-8', errors='replace')[:300]}")
        if stderr:
            print(f"[verify_pyw] stderr: {stderr.decode('utf-8', errors='replace')[:300]}")
    except subprocess.TimeoutExpired:
        kill_process_tree(proc.pid)
    sys.exit(0)
else:
    rc = proc.returncode
    try:
        stdout, stderr = proc.communicate(timeout=3)
        out_s = stdout.decode('utf-8', errors='replace')[:500]
        err_s = stderr.decode('utf-8', errors='replace')[:500]
    except:
        out_s = err_s = ""
    print(f"[verify_pyw] FAIL - proceso murio rc={rc}")
    print(f"  stdout: {out_s}")
    print(f"  stderr: {err_s}")
    sys.exit(1)
