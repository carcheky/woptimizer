"""Test unitario: logica de expansion por nombre en kill_selected.

Verifica que expand_selection_by_name():
- 1 firefox seleccionado -> TODOS los firefox del snapshot
- Multiples nombres seleccionados -> ambos nombres expandidos
- Seleccion vacia -> lista vacia
- Snapshot vacio -> devuelve la seleccion original (no se pierde el intent)
- Case-insensitive ('Firefox' == 'firefox')

NO mata procesos reales. Solo verifica la logica pura.
"""
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
import process_manager as pm


def make_fake_proc(name, pid, cmdline=None):
    return {
        'name': name,
        'pid': str(pid),
        'commandline': cmdline or f'C:\\fake\\{name}.exe',
    }


def assert_eq(actual, expected, msg=""):
    if actual != expected:
        print(f"[test]   FAIL: {msg}")
        print(f"[test]     esperado: {expected!r}")
        print(f"[test]     actual:   {actual!r}")
        sys.exit(1)
    else:
        print(f"[test]   ok: {msg}")


def main():
    print("[test] Iniciando test de expand_selection_by_name...")

    # Snapshot simulado del sistema (self.processes)
    all_procs = [
        make_fake_proc('firefox', 1001, 'C:\\Firefox\\firefox.exe'),
        make_fake_proc('firefox', 1002, 'C:\\Firefox\\firefox.exe --new-instance'),
        make_fake_proc('firefox', 1003, 'C:\\Firefox\\firefox.exe --new-instance'),
        make_fake_proc('firefox', 1004, 'C:\\Firefox\\firefox.exe --new-instance'),
        make_fake_proc('chrome', 2001, 'C:\\Chrome\\chrome.exe'),
        make_fake_proc('chrome', 2002, 'C:\\Chrome\\chrome.exe --type=renderer'),
        make_fake_proc('discord', 3001, 'C:\\Discord\\Update.exe'),
        make_fake_proc('Spotify', 4001, 'C:\\Spotify\\Spotify.exe'),  # case mixto
    ]

    # --- Test 1: 1 firefox seleccionado -> TODOS los firefox ---
    print("[test] Test 1: 1 firefox seleccionado -> expansion completa")
    selected = [all_procs[0]]  # solo firefox PID 1001
    expanded = pm.expand_selection_by_name(selected, all_procs)
    assert_eq(len(expanded), 4, "4 firefox devueltos (todos los del snapshot)")
    assert_eq(all(p['name'].lower() == 'firefox' for p in expanded), True, "todos son firefox")
    pids = sorted([p['pid'] for p in expanded])
    assert_eq(pids, ['1001', '1002', '1003', '1004'], "PIDs 1001-1004 incluidos")

    # --- Test 2: Multiples nombres seleccionados (firefox + chrome) ---
    print("[test] Test 2: 1 firefox + 1 chrome -> ambos expandidos")
    selected = [all_procs[0], all_procs[4]]  # 1 firefox + 1 chrome
    expanded = pm.expand_selection_by_name(selected, all_procs)
    assert_eq(len(expanded), 6, "6 procs devueltos (4 firefox + 2 chrome)")
    names = sorted(set(p['name'].lower() for p in expanded))
    assert_eq(names, ['chrome', 'firefox'], "ambos nombres presentes")

    # --- Test 3: Seleccion vacia -> lista vacia ---
    print("[test] Test 3: seleccion vacia -> lista vacia")
    expanded = pm.expand_selection_by_name([], all_procs)
    assert_eq(expanded, [], "lista vacia devuelta")

    # --- Test 4: Snapshot vacio -> devuelve seleccion original ---
    print("[test] Test 4: snapshot vacio (all_procs=[]) -> devuelve seleccion original")
    selected = [make_fake_proc('firefox', 9999)]
    expanded = pm.expand_selection_by_name(selected, [])
    assert_eq(len(expanded), 1, "1 proc devuelto (la seleccion original)")
    assert_eq(expanded[0]['pid'], '9999', "PID 9999 preservado")

    # --- Test 5: Case-insensitive ---
    print("[test] Test 5: case-insensitive (Spotify == spotify)")
    selected = [make_fake_proc('spotify', 9999)]  # lowercase en seleccion
    expanded = pm.expand_selection_by_name(selected, all_procs)
    assert_eq(len(expanded), 1, "1 proc devuelto (Spotify del snapshot matchea spotify)")
    assert_eq(expanded[0]['name'], 'Spotify', "el del snapshot (con S mayuscula)")

    # --- Test 6: Integracion con kill_processes ---
    print("[test] Test 6: integracion - seleccion de 1 firefox -> 4 taskkill calls")
    from unittest.mock import patch, MagicMock

    selected = [all_procs[0]]  # 1 firefox
    expanded = pm.expand_selection_by_name(selected, all_procs)

    with patch.object(pm.subprocess, 'run') as mock_run:
        mock_result = MagicMock(returncode=0, stdout="", stderr="")
        mock_run.return_value = mock_result

        # dedupe_by_tree=False para que mate los 4 (siblings)
        killed, failed, skipped = pm.kill_processes(expanded, kill_tree=True, dedupe_by_tree=False)

    print(f"[test] taskkill fue llamado {mock_run.call_count} vez/veces para 4 firefox")
    assert_eq(mock_run.call_count, 4, "4 taskkill calls (1 por cada firefox sibling)")
    assert_eq(len(skipped), 0, "sin omitir (siblings NO se saltan)")

    print("\n[test] PASS - expansion por nombre funciona correctamente")
    return 0


if __name__ == '__main__':
    sys.exit(main())
