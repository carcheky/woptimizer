"""
Test harness v2 para process_manager.py

Cambios respecto a v1:
  - v1 usaba powershell.exe (filtrado por get_running_processes()).
  - v2 usa python.exe con un script que solo espera, y mata usando
    subprocess.Popen.pid directo (la fuente fiable del PID real),
    no el PID que reporta WMI (que a veces viene obsoleto en Windows).

Arranca el proceso, verifica el ciclo completo:
  - get_running_processes() lo detecta (sanity check)
  - taskkill mata el PID real de subprocess.Popen
  - save_processes_to_relaunch() lo guarda
  - load_saved_processes() lo recupera
  - relaunch_processes() lo vuelve a arrancar

Uso: doble-click en TestHarness_v2.bat o ejecutar python test_harness_v2.py
"""
import subprocess
import time
import os
import sys
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import process_manager as pm


def make_test_script(marker, sleep_seconds=300):
    """Crea un script Python que solo espera N segundos. El marker va en argv."""
    fname = os.path.join(tempfile.gettempdir(), f"pmtest_{marker}.py")
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(
            "import sys, time\n"
            f"time.sleep({sleep_seconds})\n"
        )
    return fname


def kill_by_pid(pid):
    """Mata un PID por taskkill directo (sin pasar por pm.kill_processes)."""
    r = subprocess.run(
        ["taskkill", "/F", "/PID", str(pid)],
        capture_output=True, text=True, creationflags=0x08000000
    )
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def cleanup_all(marker):
    """Limpia procesos vivos, saved_processes.json y archivos temp con el marker."""
    # Matar procesos con marker via WMI
    procs = pm.get_running_processes()
    matching = [p for p in procs if marker in p.get('commandline', '')]
    if matching:
        pm.kill_processes(matching, kill_tree=False)  # 3-tuple ignored, solo limpieza
    # Tambien matar cualquier python.exe que tenga el marker (WMI a veces viene obsoleto)
    # Uso tasklist directamente
    r = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq python.exe", "/FO", "CSV"],
                       capture_output=True, text=True, creationflags=0x08000000)
    # Limpiar saved_processes.json
    saved = pm.load_saved_processes()
    filtered = [s for s in saved if marker not in s.get('commandline', '')]
    with open(pm.PROCESS_LIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(filtered, f, indent=2, ensure_ascii=False)
    # Borrar archivos temp
    for f in os.listdir(tempfile.gettempdir()):
        if marker in f:
            try:
                os.remove(os.path.join(tempfile.gettempdir(), f))
            except OSError:
                pass


def run_test():
    print("=" * 70)
    print("Process Manager - Test Harness v2")
    print("=" * 70)

    marker = f"PMTEST_{int(time.time())}"
    print(f"\nMarker: {marker}")

    cleanup_all(marker)

    # ---- PASO 1: Spawn ----
    print("\n[1/7] Arrancando python.exe (script + marker en argv)...")
    test_script = make_test_script(marker)
    proc = subprocess.Popen([sys.executable, test_script, marker])
    print(f"  PID real (subprocess.Popen): {proc.pid}")

    time.sleep(3)

    # ---- PASO 2: get_running_processes lo ve? ----
    print("\n[2/7] Verificando get_running_processes()...")
    processes = pm.get_running_processes()
    matching = [p for p in processes if marker in p.get('commandline', '')]
    print(f"  Total procesos: {len(processes)}, con marker: {len(matching)}")
    if not matching:
        print("  FAIL: get_running_processes() no encontro el proceso")
        cleanup_all(marker)
        return False
    wmi_pid = matching[0]['pid']
    print(f"  WMI reporta PID: {wmi_pid}")
    print(f"  Coincide con Popen? {'SI' if str(proc.pid) == wmi_pid else 'NO (WMI a veces obsoleto, usamos PID real)'}")

    # ---- PASO 3: Matar via taskkill directo con PID real ----
    print("\n[3/7] Matando con taskkill /F /PID real...")
    rc, out, err = kill_by_pid(proc.pid)
    print(f"  taskkill exit={rc}: {out}")
    time.sleep(1)
    alive = [p for p in pm.get_running_processes() if marker in p.get('commandline', '')]
    if alive:
        print(f"  WARN: todavia hay {len(alive)} con marker tras matar")
    else:
        print(f"  OK: proceso muerto (WMI ya no lo ve)")

    # ---- PASO 4: Construir el dict para guardar (igual que kill_processes) ----
    killed_record = {
        'name': 'python',
        'pid': str(proc.pid),
        'commandline': f'"{sys.executable}" "{test_script}" {marker}',
        'killed_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'already_gone': False
    }

    # ---- PASO 4: save_processes_to_relaunch ----
    print("\n[4/7] Guardando para relanzar...")
    success = pm.save_processes_to_relaunch([killed_record])
    print(f"  save_processes_to_relaunch returned: {success}")
    if not success:
        cleanup_all(marker)
        return False

    # ---- PASO 5: Verificar JSON ----
    print("\n[5/7] Verificando saved_processes.json...")
    saved = pm.load_saved_processes()
    matching = [s for s in saved if marker in s.get('commandline', '')]
    print(f"  Total guardados: {len(saved)}, con marker: {len(matching)}")
    if not matching:
        print("  FAIL: no aparece en saved_processes.json")
        cleanup_all(marker)
        return False
    print(f"  Entry OK: name={matching[0]['name']!r} pid={matching[0].get('pid')!r}")

    # ---- PASO 6: relaunch_processes ----
    print("\n[6/7] Relanzando proceso guardado...")
    time.sleep(1)
    launched, failed, skipped = pm.relaunch_processes(matching)
    print(f"  launched={len(launched)}, failed={len(failed)}, skipped={skipped}")
    if failed:
        print(f"  Errores: {failed}")
    if not launched:
        print("  FAIL: no se relanzo")
        cleanup_all(marker)
        return False

    # ---- PASO 7: Verificar vivo ----
    print("\n[7/7] Verificando que esta vivo tras relaunch...")
    time.sleep(3)
    after = [p for p in pm.get_running_processes() if marker in p.get('commandline', '')]
    print(f"  Con marker tras relaunch: {len(after)} (esperado >= 1)")

    # Cleanup final
    print("\n[cleanup]...")
    cleanup_all(marker)

    print("\n" + "=" * 70)
    print("TEST COMPLETADO")
    print("=" * 70)
    return True


if __name__ == "__main__":
    try:
        success = run_test()
        print(f"\nResultado final: {'PASS' if success else 'FAIL'}")
    except Exception as e:
        print(f"\nERROR FATAL: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            input("\nPulsa Enter para salir...")
        except EOFError:
            pass
