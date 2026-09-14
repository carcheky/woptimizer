"""Test unitario: logica de session= en save_processes_to_relaunch.

Verifica:
1. Guardar sin session: entradas SIN tag
2. Guardar con session='gaming': entradas CON tag
3. Re-guardar con misma sesion: REEMPLAZA (snapshot, no acumula)
4. Distintas sesiones conviven sin pisarse
5. Filter por sesion devuelve solo las de esa sesion

NO mata procesos reales. Solo manipula saved_processes.json con datos
sinteticos (fake procs), y restaura el archivo original al final.
"""
import os
import sys
import json
import shutil
import tempfile

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
import process_manager as pm


def make_fake_proc(name, pid, cmdline="C:\\fake\\app.exe --flag"):
    """Crea un dict de proceso sintetico (no necesita existir realmente)."""
    return {
        'name': name,
        'pid': str(pid),
        'commandline': cmdline,
    }


def backup_and_clear():
    """Hace backup del JSON real y lo deja vacio para que el test no contamine."""
    backup_path = None
    if os.path.exists(pm.PROCESS_LIST_FILE):
        backup_path = pm.PROCESS_LIST_FILE + '.testbak'
        shutil.copy2(pm.PROCESS_LIST_FILE, backup_path)
        os.remove(pm.PROCESS_LIST_FILE)
    return backup_path


def restore_backup(backup_path):
    """Restaura el JSON original desde el backup."""
    if backup_path and os.path.exists(backup_path):
        shutil.copy2(backup_path, pm.PROCESS_LIST_FILE)
        os.remove(backup_path)
    elif os.path.exists(pm.PROCESS_LIST_FILE):
        # El test dejo un archivo -> borrarlo para no contaminar
        os.remove(pm.PROCESS_LIST_FILE)


def assert_eq(actual, expected, msg=""):
    if actual != expected:
        print(f"[test]   FAIL: {msg}")
        print(f"[test]     esperado: {expected!r}")
        print(f"[test]     actual:   {actual!r}")
        sys.exit(1)
    else:
        print(f"[test]   ok: {msg}")


def main():
    print("[test] Iniciando test de session= en save_processes_to_relaunch...")

    # Backup del archivo real del usuario (CRITICO: no destruir sus datos)
    backup_path = backup_and_clear()
    print(f"[test] Backup del JSON original en {backup_path}")

    try:
        # --- Test 1: guardar sin session => SIN tag ---
        print("[test] Test 1: guardar sin session -> entradas SIN tag")
        procs_manual = [
            make_fake_proc('chrome', 1001, 'C:\\chrome.exe'),
            make_fake_proc('discord', 1002, 'C:\\discord.exe'),
        ]
        ok = pm.save_processes_to_relaunch(procs_manual)
        assert_eq(ok, True, "save retorno True")

        loaded = pm.load_saved_processes()
        assert_eq(len(loaded), 2, "2 entradas guardadas")
        for entry in loaded:
            assert_eq(entry.get('session'), None, f"entrada {entry['name']} SIN session")
        print("[test]   ok: 2 entradas sin tag")

        # --- Test 2: guardar con session='gaming' => CON tag ---
        print("[test] Test 2: guardar con session='gaming' -> CON tag")
        procs_gaming_v1 = [
            make_fake_proc('chrome', 2001, 'C:\\chrome.exe'),
            make_fake_proc('spotify', 2002, 'C:\\spotify.exe'),
        ]
        ok = pm.save_processes_to_relaunch(procs_gaming_v1, session='gaming')
        assert_eq(ok, True, "save retorno True")

        loaded = pm.load_saved_processes()
        # Ahora hay 2 manuales (sin tag) + 2 gaming (con tag) = 4 totales
        assert_eq(len(loaded), 4, "4 entradas totales (2 manuales + 2 gaming)")

        gaming_entries = [e for e in loaded if e.get('session') == 'gaming']
        manual_entries = [e for e in loaded if e.get('session') is None]
        assert_eq(len(gaming_entries), 2, "2 entradas gaming")
        assert_eq(len(manual_entries), 2, "2 entradas manuales intactas")

        # --- Test 3: re-guardar con misma session REEMPLAZA snapshot ---
        print("[test] Test 3: re-guardar con session='gaming' REEMPLAZA snapshot anterior")
        procs_gaming_v2 = [
            make_fake_proc('firefox', 3001, 'C:\\firefox.exe'),
            make_fake_proc('vlc', 3002, 'C:\\vlc.exe'),
        ]
        ok = pm.save_processes_to_relaunch(procs_gaming_v2, session='gaming')
        assert_eq(ok, True, "save retorno True")

        loaded = pm.load_saved_processes()
        # 2 manuales (sin tag, intactas) + 2 gaming NUEVAS (chrome/spotify eliminados)
        assert_eq(len(loaded), 4, "4 entradas totales tras reemplazo (2 manuales + 2 gaming nuevas)")

        gaming_entries = [e for e in loaded if e.get('session') == 'gaming']
        manual_entries = [e for e in loaded if e.get('session') is None]
        assert_eq(len(gaming_entries), 2, "2 entradas gaming tras reemplazo")
        assert_eq(len(manual_entries), 2, "2 entradas manuales siguen intactas")

        gaming_names = sorted([e['name'] for e in gaming_entries])
        assert_eq(gaming_names, ['firefox', 'vlc'], "gaming entries son firefox+vlc (chrome+spotify fueron reemplazadas)")

        # --- Test 4: distintas sesiones conviven ---
        print("[test] Test 4: distintas sesiones conviven sin pisarse")
        procs_work = [
            make_fake_proc('outlook', 4001, 'C:\\outlook.exe'),
        ]
        ok = pm.save_processes_to_relaunch(procs_work, session='work')
        assert_eq(ok, True, "save con session='work' retorno True")

        loaded = pm.load_saved_processes()
        work_entries = [e for e in loaded if e.get('session') == 'work']
        gaming_entries = [e for e in loaded if e.get('session') == 'gaming']
        manual_entries = [e for e in loaded if e.get('session') is None]
        assert_eq(len(work_entries), 1, "1 entrada work")
        assert_eq(len(gaming_entries), 2, "2 entradas gaming (intactas)")
        assert_eq(len(manual_entries), 2, "2 entradas manuales (intactas)")

        # --- Test 5: filter por sesion (simulando lo que hace restore_gaming_session) ---
        print("[test] Test 5: filter por sesion funciona")
        gaming_only = [e for e in loaded if e.get('session') == 'gaming']
        assert_eq(len(gaming_only), 2, "filter gaming devuelve 2")
        for e in gaming_only:
            assert_eq(e.get('session'), 'gaming', f"entry {e['name']} tiene session='gaming'")

        print("\n[test] PASS - toda la logica de session= funciona")
        return 0

    finally:
        # SIEMPRE restaurar el archivo original, incluso si el test falla
        restore_backup(backup_path)
        print(f"[test] Backup restaurado / limpiado")


if __name__ == '__main__':
    sys.exit(main())
