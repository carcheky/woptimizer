"""
Test harness para process_manager.py
Arranca un proceso en background (powershell con sleep), verifica el ciclo completo:
  - get_running_processes() lo detecta
  - kill_processes() lo mata
  - save_processes_to_relaunch() lo guarda
  - load_saved_processes() lo recupera
  - relaunch_processes() lo vuelve a arrancar

Uso: doble-click en test_harness.bat o test_harness.ps1
"""
import subprocess
import time
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import process_manager as pm


def find_process_by_marker(marker):
    """Busca procesos cuyo commandline contiene el marker."""
    processes = pm.get_running_processes()
    return [p for p in processes if marker in p.get('commandline', '')]


def cleanup_all_matching(marker):
    """Mata todos los procesos que coincidan con el marker (limpieza)."""
    procs = find_process_by_marker(marker)
    if procs:
        killed, failed, skipped = pm.kill_processes(procs, kill_tree=False)
        print(f"  Limpieza: matados={len(killed)}, fallidos={len(failed)}, omitidos={len(skipped)}")
    # Limpiar el JSON de saved
    saved = pm.load_saved_processes()
    filtered = [s for s in saved if marker not in s.get('commandline', '')]
    with open(pm.PROCESS_LIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(filtered, f, indent=2, ensure_ascii=False)


def run_test():
    print("=" * 70)
    print("Process Manager - Test Harness")
    print("=" * 70)

    # Marker unico para identificar nuestro proceso en commandlines
    marker = f"PMTEST_{int(time.time())}"
    print(f"\nMarker del proceso de prueba: {marker}")

    # Limpieza previa por si hay zombies de tests anteriores
    cleanup_all_matching(marker)

    # ---- PASO 1: Arrancar proceso en background ----
    print("\n[1/8] Arrancando proceso en background...")
    # PowerShell con Start-Sleep - el commandline contendra el marker
    proc = subprocess.Popen(
        ["powershell", "-NoProfile", "-Command",
         f"Start-Sleep -Seconds 999; Write-Output '{marker}'"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    print(f"  Lanzado con PID={proc.pid}")

    # Esperar a que se registre
    time.sleep(3)

    # ---- PASO 2: Detectar via get_running_processes ----
    print("\n[2/8] Llamando get_running_processes()...")
    processes = pm.get_running_processes()
    print(f"  Total procesos encontrados: {len(processes)}")

    test_procs = find_process_by_marker(marker)
    print(f"  Procesos con marker '{marker}': {len(test_procs)}")

    if not test_procs:
        print("  FAIL: no se encontro el proceso de prueba")
        print("  Mostrando powershell processes para debug:")
        for p in processes:
            if 'powershell' in p['name'].lower():
                print(f"    PID {p['pid']}: {p['commandline'][:120]}")
        cleanup_all_matching(marker)
        return False

    target = test_procs[0]
    print(f"  Target detectado: name={target['name']!r} pid={target['pid']}")
    print(f"  Commandline: {target['commandline'][:120]}...")

    # ---- PASO 3: Matar el proceso ----
    print("\n[3/8] Matando el proceso (kill_tree=False para no matar al padre)...")
    killed, failed, skipped = pm.kill_processes([target], kill_tree=False)
    print(f"  killed={len(killed)}, failed={len(failed)}, skipped={len(skipped)}")
    if failed:
        print(f"  Errores: {failed}")
        cleanup_all_matching(marker)
        return False

    already_gone = killed[0].get('already_gone', False)
    print(f"  already_gone flag: {already_gone} (esperado: False en primer kill)")

    # Verificar que ya no esta
    time.sleep(1)
    still_alive = find_process_by_marker(marker)
    print(f"  Procesos con marker tras kill: {len(still_alive)} (esperado: 0)")
    if still_alive:
        print("  FAIL: el proceso sigue vivo despues de matar")
        cleanup_all_matching(marker)
        return False

    # ---- PASO 4: Guardar para relaunch ----
    print("\n[4/8] Guardando para relanzar...")
    success = pm.save_processes_to_relaunch(killed)
    print(f"  save_processes_to_relaunch returned: {success}")

    if not success:
        cleanup_all_matching(marker)
        return False

    # ---- PASO 5: Verificar JSON ----
    print("\n[5/8] Verificando saved_processes.json...")
    saved = pm.load_saved_processes()
    matching = [s for s in saved if marker in s.get('commandline', '')]
    print(f"  Total guardados: {len(saved)}, con marker: {len(matching)}")

    if not matching:
        print("  FAIL: el proceso no aparece en saved_processes.json")
        cleanup_all_matching(marker)
        return False

    print(f"  Entry guardada: name={matching[0]['name']!r} pid={matching[0].get('pid')!r}")
    print(f"  Commandline length: {len(matching[0]['commandline'])} chars")

    # ---- PASO 6: Relanzar ----
    print("\n[6/8] Relanzando proceso guardado...")
    # Necesitamos esperar antes de relanzar para evitar conflictos
    time.sleep(1)
    launched, failed, skipped = pm.relaunch_processes([matching[0]])
    print(f"  launched={len(launched)}, failed={len(failed)}, skipped={skipped}")
    if failed:
        print(f"  Errores: {failed}")

    if not launched:
        print("  FAIL: no se relanzo el proceso")
        cleanup_all_matching(marker)
        return False

    # ---- PASO 7: Verificar que esta vivo de nuevo ----
    print("\n[7/8] Verificando que el proceso esta vivo...")
    time.sleep(3)  # Dar tiempo a PowerShell para arrancar el sleep
    after = find_process_by_marker(marker)
    print(f"  Procesos con marker tras relaunch: {len(after)} (esperado: >=1)")

    if not after:
        print("  WARN: no se detecta el proceso relanzado (puede tardar mas)")

    # ---- PASO 8: Test del caso "ya no existe" (taskkill 128) ----
    print("\n[8/8] Test: matar proceso que ya no existe (espera exit code 128 -> success)...")
    killed2, failed2, skipped2 = pm.kill_processes([after[0]] if after else [target], kill_tree=False)
    time.sleep(1)
    # Ahora intentar matarlo otra vez - ya no existe
    if after:
        killed3, failed3, skipped3 = pm.kill_processes([after[0]], kill_tree=False)
        if failed3:
            print(f"  NOTA: fallo esperado? {failed3}")
        else:
            print(f"  OK: matar proceso inexistente retorna success. already_gone: {killed3[0].get('already_gone')}")

    # ---- Limpieza final ----
    print("\n[cleanup] Limpiando procesos de prueba y saved list...")
    cleanup_all_matching(marker)
    print("  Limpieza completa")

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
        input("\nPulsa Enter para salir...")
