"""Test unitario: logica de agrupacion (group_by_exe) y dedupe (dedupe_by_tree).

Verifica que:
- kill_processes con kill_tree=True deduplica por ejecutable (1 taskkill por exe)
- kill_processes con kill_tree=False NO deduplica (cada PID es explicito)
- relaunch_processes con group_by_exe=True agrupa por args[0] y lanza SIN args
- relaunch_processes con group_by_exe=False relanza cada cmdline (legacy)

NO mata procesos reales. Mockea subprocess.run y subprocess.Popen para
registrar las llamadas y verificar la logica sin side effects.
"""
import os
import sys
import shlex
from unittest.mock import patch, MagicMock

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
import process_manager as pm


def make_fake_proc(name, pid, cmdline):
    return {'name': name, 'pid': str(pid), 'commandline': cmdline}


def assert_eq(actual, expected, msg=""):
    if actual != expected:
        print(f"[test]   FAIL: {msg}")
        print(f"[test]     esperado: {expected!r}")
        print(f"[test]     actual:   {actual!r}")
        sys.exit(1)
    else:
        print(f"[test]   ok: {msg}")


def main():
    print("[test] Iniciando test de agrupacion y dedupe...")

    # ============================================================
    # PARTE 1: relaunch_processes con group_by_exe=True (default)
    # ============================================================
    print("\n[test] === relaunch_processes(group_by_exe=True) ===")

    # 5 chrome.exe: 1 main + 4 renderers/utility (mismo args[0])
    procs = [
        make_fake_proc('chrome', 1001, '"C:\\Program Files\\Chrome\\chrome.exe"'),
        make_fake_proc('chrome', 1002, '"C:\\Program Files\\Chrome\\chrome.exe" --type=renderer --user-data-dir=/tmp'),
        make_fake_proc('chrome', 1003, '"C:\\Program Files\\Chrome\\chrome.exe" --type=renderer'),
        make_fake_proc('chrome', 1004, '"C:\\Program Files\\Chrome\\chrome.exe" --type=utility'),
        make_fake_proc('chrome', 1005, '"C:\\Program Files\\Chrome\\chrome.exe" --type=gpu-process'),
        make_fake_proc('discord', 2001, '"C:\\Users\\user\\AppData\\Local\\Discord\\Update.exe" --processStart Discord.exe'),
        make_fake_proc('spotify', 3001, '"C:\\Users\\user\\AppData\\Roaming\\Spotify\\Spotify.exe"'),
    ]

    with patch.object(pm.subprocess, 'Popen') as mock_popen:
        # Popen devuelve un mock que no falla
        mock_popen.return_value = MagicMock()
        mock_popen.side_effect = lambda args, **kw: MagicMock(pid=9999)

        launched, failed, skipped = pm.relaunch_processes(procs, group_by_exe=True)

    print(f"[test] Popen fue llamado {mock_popen.call_count} vez/veces")
    print(f"[test]   llamadas: {[call.args[0] for call in mock_popen.call_args_list]}")

    # 7 entradas -> 3 ejecutables unicos (chrome, discord, spotify)
    # Se esperan 3 Popen calls + 4 skipped (4 chrome duplicados)
    assert_eq(len(launched), 3, "3 procesos unicos relanzados")
    assert_eq(skipped, 4, "4 chrome duplicados omitidos")
    assert_eq(len(failed), 0, "0 fallos")

    # Verificar que cada llamada Popen fue SOLO con el path del exe, sin args
    expected_exes = [
        '"C:\\Program Files\\Chrome\\chrome.exe"',
        '"C:\\Users\\user\\AppData\\Local\\Discord\\Update.exe"',
        '"C:\\Users\\user\\AppData\\Roaming\\Spotify\\Spotify.exe"',
    ]
    actual_exes = [call.args[0] for call in mock_popen.call_args_list]
    for actual, expected in zip(actual_exes, expected_exes):
        assert_eq(actual, [expected], f"Popen llamado con solo [{expected}] (sin args adicionales)")

    # ============================================================
    # PARTE 2: relaunch_processes con group_by_exe=False (legacy)
    # ============================================================
    print("\n[test] === relaunch_processes(group_by_exe=False) ===")

    with patch.object(pm.subprocess, 'Popen') as mock_popen:
        mock_popen.return_value = MagicMock()
        mock_popen.side_effect = lambda args, **kw: MagicMock(pid=9999)

        launched, failed, skipped = pm.relaunch_processes(procs[:5], group_by_exe=False)

    print(f"[test] Popen fue llamado {mock_popen.call_count} vez/veces con 5 entradas")

    assert_eq(mock_popen.call_count, 5, "5 Popen calls (legacy: 1 por entrada)")
    assert_eq(skipped, 0, "sin omitir (legacy)")
    assert_eq(len(launched), 5, "5 lanzados")

    # Verificar que en legacy SÍ se mantienen los args (renderer, utility, etc)
    # 4 de los 5 chrome tenian args en su commandline original (renderer/utility/gpu)
    actual_args_list = [call.args[0] for call in mock_popen.call_args_list]
    calls_with_args = [c for c in actual_args_list if len(c) > 1]
    assert_eq(len(calls_with_args), 4, "4 legacy calls mantienen args (renderer/utility/gpu)")
    # Verificar que uno de ellos tiene los args de renderer
    renderer_calls = [c for c in actual_args_list if '--type=renderer' in c]
    assert_eq(len(renderer_calls), 2, "2 calls tienen --type=renderer")

    # ============================================================
    # PARTE 3: kill_processes con kill_tree=True y dedupe_by_tree=True
    # ============================================================
    print("\n[test] === kill_processes(kill_tree=True, dedupe_by_tree=True) ===")

    procs_to_kill = [
        make_fake_proc('chrome', 1001, '"C:\\Program Files\\Chrome\\chrome.exe"'),
        make_fake_proc('chrome', 1002, '"C:\\Program Files\\Chrome\\chrome.exe" --type=renderer'),
        make_fake_proc('chrome', 1003, '"C:\\Program Files\\Chrome\\chrome.exe" --type=renderer'),
        make_fake_proc('discord', 2001, '"C:\\Users\\user\\AppData\\Local\\Discord\\Update.exe"'),
    ]

    # Mockear subprocess.run para registrar taskkill calls
    with patch.object(pm.subprocess, 'run') as mock_run:
        # Simular exito de taskkill (returncode 0)
        mock_result = MagicMock(returncode=0, stdout="", stderr="")
        mock_run.return_value = mock_result

        killed, failed, skipped = pm.kill_processes(procs_to_kill, kill_tree=True, dedupe_by_tree=True)

    print(f"[test] taskkill fue llamado {mock_run.call_count} vez/veces")
    print(f"[test]   llamadas: {[call.args[0] for call in mock_run.call_args_list]}")

    # 4 entradas -> 2 ejecutables unicos (chrome, discord)
    # Se esperan 2 taskkill calls + 2 skipped (2 chrome duplicados)
    assert_eq(mock_run.call_count, 2, "2 taskkill calls (1 por exe unico)")
    assert_eq(len(killed), 2, "2 matados (los 2 roots)")
    assert_eq(len(skipped), 2, "2 omitidos (chrome duplicados)")
    assert_eq(len(failed), 0, "0 fallos")

    # Verificar que cada taskkill tiene /T
    for call in mock_run.call_args_list:
        cmd = call.args[0]
        assert_eq('/T' in cmd, True, f"taskkill lleva /T (tree): {cmd}")
        assert_eq('/F' in cmd, True, f"taskkill lleva /F (force): {cmd}")

    # ============================================================
    # PARTE 4: kill_processes con kill_tree=False NO dedupe
    # ============================================================
    print("\n[test] === kill_processes(kill_tree=False, dedupe_by_tree=True) ===")

    with patch.object(pm.subprocess, 'run') as mock_run:
        mock_result = MagicMock(returncode=0, stdout="", stderr="")
        mock_run.return_value = mock_result

        killed, failed, skipped = pm.kill_processes(procs_to_kill, kill_tree=False, dedupe_by_tree=True)

    # Con kill_tree=False NO debe dedupar (cada PID es explicito del usuario)
    print(f"[test] taskkill fue llamado {mock_run.call_count} vez/veces con kill_tree=False")
    assert_eq(mock_run.call_count, 4, "4 taskkill calls (no dedupe con kill_tree=False)")
    assert_eq(len(skipped), 0, "sin omitir con kill_tree=False")

    print("\n[test] PASS - agrupacion y dedupe funcionan correctamente")
    return 0


if __name__ == '__main__':
    sys.exit(main())
