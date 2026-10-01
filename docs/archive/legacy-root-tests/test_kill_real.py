"""Test real: lanza un proceso, lo lista, lo mata, verifica que murio.

Usa un subprocess Python invisible (no abre ventanas) en lugar de notepad.exe.
Antes este test abria un Bloc de notas cada ejecucion - muy molesto para el
usuario. El proceso Python de prueba se identifica por un marker unico en su
commandline y se mata igual de bien que cualquier otro.
"""
import subprocess
import time
import os
import sys
import shlex

script_dir = os.path.dirname(os.path.abspath(__file__))

# Cargar modulo process_manager para usar sus funciones
sys.path.insert(0, script_dir)
import process_manager as pm

# Constante para evitar ventanas de consola en subprocesos (Windows)
CREATE_NO_WINDOW = 0x08000000


def kill_process_tree(pid):
    """Mata el proceso Y todos sus hijos (huerfanos en Windows).
    Mismo patron que verify_app.py y verify_pyw.py - ver Trampa #10.
    """
    try:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True,
            creationflags=CREATE_NO_WINDOW,
        )
    except Exception as e:
        print(f"[test] WARN: taskkill fallo para PID {pid}: {e}")


print("[test] Iniciando test real de kill_processes...")

# 1. Lanzar un subprocess Python invisible como proceso de prueba.
#    Marker unico en el commandline para identificarlo sin confusion.
marker = f"wopt_test_{os.getpid()}"
print(f"[test] Lanzando Python sleeper (marker={marker})...")
target = subprocess.Popen(
    [sys.executable, "-c", f"import time; print('{marker}'); time.sleep(60)"],
    stdout=subprocess.PIPE,  # capturamos para que no haya console
    stderr=subprocess.PIPE,
    creationflags=CREATE_NO_WINDOW,
)
test_pid = target.pid
print(f"[test] Python sleeper lanzado con PID={test_pid}")

# Esperar a que arranque
time.sleep(2)

# 2. Verificar que aparece en get_running_processes (buscando por marker, NO por PID
#    - mas robusto porque el PID puede no aparecer en WMI snapshot)
print("[test] Listando procesos...")
processes = pm.get_running_processes()
print(f"[test] Total procesos listados: {len(processes)}")

target_in_list = [p for p in processes if marker in p.get('commandline', '')]
if not target_in_list:
    print(f"[test] FAIL: Python sleeper con marker '{marker}' NO encontrado")
    print("[test]   No se puede continuar el test sin objetivo")
    kill_process_tree(test_pid)
    sys.exit(1)

proc = target_in_list[0]
print(f"[test] sleeper ENCONTRADO: name={proc['name']}, pid={proc['pid']}")
print(f"[test]   cmdline: {proc['commandline'][:80]}")

# 3. Matarlo via pm.kill_processes (es lo que estamos testeando)
print("[test] Llamando kill_processes con kill_tree=False...")
killed, failed, skipped = pm.kill_processes(target_in_list, kill_tree=False)
print(f"[test] killed={len(killed)}, failed={len(failed)}, skipped={len(skipped)}")
if killed:
    k = killed[0]
    print(f"[test]   killed: {k['name']} (already_gone={k.get('already_gone', False)})")
if failed:
    print(f"[test]   failed: {failed}")

# 4. Verificar que murio via poll() (subprocess handle)
time.sleep(1)
print("[test] Verificando que el proceso murio...")
poll_result = target.poll()
if poll_result is None:
    print(f"[test] ERROR: sleeper SIGUE VIVO (poll={poll_result})")
else:
    print(f"[test] sleeper murio con codigo: {poll_result}")

# 5. Verificar tambien que NO esta en la lista del sistema
processes2 = pm.get_running_processes()
still_alive = [p for p in processes2 if marker in p.get('commandline', '')]
if still_alive:
    print(f"[test] ERROR: sleeper SIGUE EN LA LISTA")
else:
    print(f"[test] sleeper NO esta en la lista - confirmado muerto")

# 6. Cleanup final defensivo (por si poll() miente en algun edge case)
kill_process_tree(test_pid)
try:
    target.kill()
except Exception:
    pass

# Resumen
if poll_result is not None and not still_alive:
    print("\n[test] PASS - kill_processes funciona correctamente")
    sys.exit(0)
else:
    print("\n[test] FAIL - kill_processes NO mata el proceso")
    sys.exit(1)
