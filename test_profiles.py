"""Test unitario: gestion de perfiles de relanzado (v2.0).

Verifica:
- load_profiles / save_profiles (CRUD basico)
- create_profile (unicidad)
- update_profile (preserva estructura)
- delete_profile (limpia favorite si era el)
- set_favorite (None desmarca)
- launch_profile (mockeado, sin procesos reales)

NO lanza apps reales. Mockea subprocess.Popen.
Backup del profiles.json real del usuario.
"""
import os
import sys
import json
import shutil
from unittest.mock import patch, MagicMock

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
import process_manager as pm


def backup_and_clear():
    """Backup profiles.json y dejarlo vacio."""
    backup_path = None
    if os.path.exists(pm.PROFILES_FILE):
        backup_path = pm.PROFILES_FILE + '.testbak'
        shutil.copy2(pm.PROFILES_FILE, backup_path)
        os.remove(pm.PROFILES_FILE)
    return backup_path


def restore_backup(backup_path):
    if backup_path and os.path.exists(backup_path):
        shutil.copy2(backup_path, pm.PROFILES_FILE)
        os.remove(backup_path)
    elif os.path.exists(pm.PROFILES_FILE):
        os.remove(pm.PROFILES_FILE)


def assert_eq(actual, expected, msg=""):
    if actual != expected:
        print(f"[test]   FAIL: {msg}")
        print(f"[test]     esperado: {expected!r}")
        print(f"[test]     actual:   {actual!r}")
        sys.exit(1)
    else:
        print(f"[test]   ok: {msg}")


def main():
    print("[test] Iniciando test de perfiles (v2.0)...")
    backup_path = backup_and_clear()
    print(f"[test] Backup del JSON original en {backup_path}")

    try:
        # --- Test 1: load_profiles vacio ---
        # v2.0.6: load_profiles ahora garantiza el perfil de sistema 'Gaming'.
        # Sin profiles.json, devuelve ese perfil auto-creado + favorite=None.
        print("[test] Test 1: load_profiles con archivo inexistente")
        data = pm.load_profiles()
        assert_eq(data.get('favorite'), None, "favorite=None inicial")
        assert_eq(pm.SYSTEM_GAMING_PROFILE_KEY in data['profiles'], True,
                  f"perfil de sistema '{pm.SYSTEM_GAMING_PROFILE_KEY}' auto-creado")
        # El resto de profiles debe estar vacio (solo el del sistema)
        user_profiles = [k for k in data['profiles'] if not pm.is_system_profile(k)]
        assert_eq(user_profiles, [], "no hay perfiles de usuario")

        # --- Test 2: create_profile ---
        print("[test] Test 2: create_profile")
        result = pm.create_profile("Trabajo", ["chrome.exe", "discord.exe", "slack.exe"])
        assert_eq(result is not None, True, "create retorno data")
        assert_eq("Trabajo" in result['profiles'], True, "Trabajo en profiles")
        assert_eq(result['profiles']['Trabajo']['apps'], ["chrome.exe", "discord.exe", "slack.exe"], "apps correctas")

        # --- Test 3: create duplicado -> None ---
        print("[test] Test 3: create duplicado -> None")
        result2 = pm.create_profile("Trabajo", ["x.exe"])
        assert_eq(result2, None, "duplicado retorna None")

        # --- Test 4: update_profile ---
        print("[test] Test 4: update_profile")
        result3 = pm.update_profile("Trabajo", ["chrome.exe", "outlook.exe"])
        assert_eq(result3 is not None, True, "update retorno data")
        assert_eq(result3['profiles']['Trabajo']['apps'], ["chrome.exe", "outlook.exe"], "apps actualizadas")

        # --- Test 5: update de perfil inexistente -> None ---
        print("[test] Test 5: update de perfil inexistente -> None")
        result4 = pm.update_profile("NoExiste", ["x.exe"])
        assert_eq(result4, None, "update inexistente retorna None")

        # --- Test 6: set_favorite ---
        print("[test] Test 6: set_favorite")
        result5 = pm.set_favorite("Trabajo")
        assert_eq(result5['favorite'], "Trabajo", "Trabajo es favorito")

        # --- Test 7: set_favorite a None desmarca ---
        print("[test] Test 7: set_favorite(None)")
        result6 = pm.set_favorite(None)
        assert_eq(result6['favorite'], None, "favorito desmarca a None")

        # --- Test 8: set_favorite de perfil inexistente -> None ---
        print("[test] Test 8: set_favorite perfil inexistente")
        result7 = pm.set_favorite("Fantasma")
        assert_eq(result7, None, "set_favorite inexistente retorna None")

        # --- Test 9: delete_profile ---
        print("[test] Test 9: delete_profile")
        result8 = pm.delete_profile("Trabajo")
        assert_eq(result8 is not None, True, "delete retorno data")
        assert_eq("Trabajo" in result8['profiles'], False, "Trabajo borrado")

        # --- Test 10: delete_profile que es favorite limpia el favorite ---
        print("[test] Test 10: delete_profile limpia favorite si era el")
        pm.create_profile("Gaming", ["steam.exe"])
        pm.set_favorite("Gaming")
        result9 = pm.delete_profile("Gaming")
        assert_eq(result9['favorite'], None, "favorite se limpia si el perfil borrado era favorito")

        # --- Test 11: launch_profile con mock ---
        print("[test] Test 11: launch_profile (mockeado)")
        pm.create_profile("TestLaunch", ["chrome.exe", "discord.exe"])
        with patch.object(pm.subprocess, 'Popen') as mock_popen:
            mock_popen.return_value = MagicMock(pid=9999)
            launched, failed = pm.launch_profile("TestLaunch")
        assert_eq(len(launched), 2, "2 lanzados")
        assert_eq(len(failed), 0, "0 fallos")
        assert_eq(mock_popen.call_count, 2, "2 Popen calls (1 por app)")

        # Verificar que se llamo SIN args (solo el exe name)
        actual_args = [call.args[0] for call in mock_popen.call_args_list]
        for args in actual_args:
            assert_eq(len(args), 1, f"Popen llamado con solo [exe_name], no args: {args}")

        # --- Test 12: launch_profile inexistente ---
        print("[test] Test 12: launch_profile de perfil inexistente")
        launched, failed = pm.launch_profile("Fantasma")
        assert_eq(len(launched), 0, "0 lanzados")
        assert_eq(len(failed), 1, "1 fallo")

        # --- Test 13: load_profiles refleja los cambios ---
        print("[test] Test 13: load_profiles ve los datos persistidos")
        data13 = pm.load_profiles()
        assert_eq("TestLaunch" in data13['profiles'], True, "TestLaunch persistido")

        print("\n[test] PASS - gestion de perfiles funciona correctamente")
        return 0

    finally:
        restore_backup(backup_path)
        print(f"[test] Backup restaurado / limpiado")


if __name__ == '__main__':
    sys.exit(main())
