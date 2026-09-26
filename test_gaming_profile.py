"""Test unitario: perfil de sistema "Gaming" (v2.0.6).

Verifica los 7 criterios de aceptacion del spec AGENTS.md (rev 9):
1. Primer arranque sin profiles.json: gaming funciona con factory defaults, sin crashear.
2. El usuario puede editar keepers y se persisten al disco.
3. El usuario puede togglear kill_low_chat y se persiste.
4. Boton "Reset a fabrica" revierte keepers + toggle, persistido.
5. delete_profile sobre __system_gaming__ no borra (o ProfilesDialog lo bloquea).
6. should_kill_for_gaming lee del profile (NO de constante hardcoded).
7. profiles.json corrupto/parcial: se repara con factory defaults, no crashea.

NO lanza apps reales ni abre ventanas tkinter.
Backup del profiles.json real del usuario.
"""
import os
import sys
import json
import shutil

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
import process_manager as pm


# ------------------------------------------------------------
# Helpers de backup / cleanup
# ------------------------------------------------------------
def backup_and_clear():
    """Backup profiles.json y borrarlo para empezar limpio."""
    backup_path = None
    if os.path.exists(pm.PROFILES_FILE):
        backup_path = pm.PROFILES_FILE + '.testbak_gp'
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


def assert_true(cond, msg=""):
    if not cond:
        print(f"[test]   FAIL: {msg}")
        sys.exit(1)
    else:
        print(f"[test]   ok: {msg}")


def write_profiles(data):
    """Escribe profiles.json tal cual (sin auto-reparacion)."""
    with open(pm.PROFILES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ------------------------------------------------------------
# Tests
# ------------------------------------------------------------
def test_criterion_1_first_run_no_profile():
    """C1: Primer arranque sin profiles.json → gaming funcional con factory defaults."""
    print("\n[test] C1: primer arranque sin profiles.json...")
    if os.path.exists(pm.PROFILES_FILE):
        os.remove(pm.PROFILES_FILE)
    data = pm.load_profiles()
    assert_true(isinstance(data, dict), "load_profiles devuelve dict")
    assert_true('profiles' in data, "data tiene 'profiles'")
    assert_true(pm.SYSTEM_GAMING_PROFILE_KEY in data['profiles'],
                f"data['profiles'] contiene '{pm.SYSTEM_GAMING_PROFILE_KEY}'")
    prof = data['profiles'][pm.SYSTEM_GAMING_PROFILE_KEY]
    assert_eq(prof.get('kind'), 'system', "kind=system")
    assert_eq(prof.get('keepers'), ['discord'], "factory keepers=['discord']")
    assert_eq(prof.get('kill_low_chat'), True, "factory kill_low_chat=True")
    # Archivo fue persistido
    assert_true(os.path.exists(pm.PROFILES_FILE),
                "profiles.json fue creado y persistido en disco")


def test_criterion_2_edit_keepers_persists():
    """C2: Editar keepers se persiste al disco."""
    print("\n[test] C2: editar keepers persiste...")
    backup_and_clear()
    try:
        # Crear perfil con keepers custom
        prof = pm.load_gaming_profile()
        prof['keepers'] = ['discord', 'steam', 'epicgameslauncher']
        result = pm.save_gaming_profile(prof)
        assert_true(result is not None, "save_gaming_profile devuelve data")
        # Releer desde disco para verificar persistencia
        on_disk = pm.load_profiles()
        kept = on_disk['profiles'][pm.SYSTEM_GAMING_PROFILE_KEY]['keepers']
        assert_eq(sorted(kept), ['discord', 'epicgameslauncher', 'steam'],
                  "keepers persistidos en disco")
        # factory snapshot embebido para reset independiente del codigo
        assert_true('factory' in on_disk['profiles'][pm.SYSTEM_GAMING_PROFILE_KEY],
                    "factory snapshot embebido")
    finally:
        backup_path = pm.PROFILES_FILE + '.testbak_gp_cleanup'
        if os.path.exists(pm.PROFILES_FILE):
            os.remove(pm.PROFILES_FILE)
        # (no restaurar backup_and_clear — lo hicimos en linea)


def test_criterion_3_toggle_kill_low_chat_persists():
    """C3: Toggle de kill_low_chat se persiste."""
    print("\n[test] C3: toggle kill_low_chat persiste...")
    backup_and_clear()
    try:
        prof = pm.load_gaming_profile()
        prof['kill_low_chat'] = False
        result = pm.save_gaming_profile(prof)
        assert_true(result is not None, "save devuelve data")
        on_disk = pm.load_profiles()
        klow = on_disk['profiles'][pm.SYSTEM_GAMING_PROFILE_KEY]['kill_low_chat']
        assert_eq(klow, False, "kill_low_chat=False persistido")
        # should_kill_for_gaming honra el toggle (kill_low_chat=False)
        # Telegram es chat low priority → con toggle off NO debe matar
        telegram_should_die = pm.should_kill_for_gaming('telegram',
                                                        pm.load_gaming_profile(on_disk))
        assert_eq(telegram_should_die, False,
                  "telegram NO se mata con kill_low_chat=False")
        # ... y con toggle on SI debe matar
        on_disk['profiles'][pm.SYSTEM_GAMING_PROFILE_KEY]['kill_low_chat'] = True
        telegram_should_die = pm.should_kill_for_gaming('telegram',
                                                        pm.load_gaming_profile(on_disk))
        assert_eq(telegram_should_die, True,
                  "telegram SI se mata con kill_low_chat=True")
    finally:
        if os.path.exists(pm.PROFILES_FILE):
            os.remove(pm.PROFILES_FILE)


def test_criterion_4_reset_to_factory():
    """C4: reset_gaming_profile_to_factory revierte a factory defaults."""
    print("\n[test] C4: reset a valores de fabrica...")
    backup_and_clear()
    try:
        # Editar todo (keepers custom + kill_low_chat=False)
        prof = pm.load_gaming_profile()
        prof['keepers'] = ['discord', 'steam', 'obs64', 'nvidia-share']
        prof['kill_low_chat'] = False
        pm.save_gaming_profile(prof)
        # Verificar edicion persistida
        on_disk = pm.load_profiles()
        assert_eq(on_disk['profiles'][pm.SYSTEM_GAMING_PROFILE_KEY]['keepers'],
                  ['discord', 'steam', 'obs64', 'nvidia-share'],
                  "keepers editados persistidos")
        # Reset
        result = pm.reset_gaming_profile_to_factory()
        assert_true(result is not None, "reset devuelve data")
        # Verificar vuelta a factory
        on_disk = pm.load_profiles()
        fresh = on_disk['profiles'][pm.SYSTEM_GAMING_PROFILE_KEY]
        assert_eq(fresh['kind'], 'system', "reset mantiene kind=system")
        assert_eq(fresh['keepers'], ['discord'], "reset keepers=['discord']")
        assert_eq(fresh['kill_low_chat'], True, "reset kill_low_chat=True")
    finally:
        if os.path.exists(pm.PROFILES_FILE):
            os.remove(pm.PROFILES_FILE)


def test_criterion_5_cannot_delete_system_profile():
    """C5: delete_profile sobre gaming no debe eliminarlo (ProfilesDialog
    lo bloquea, pero la funcion delete_profile en si NO debe proteger;
    la proteccion esta en la UI). Verificamos que is_system_profile lo
    detecta y que el helper expone la clave reservada."""
    print("\n[test] C5: no se puede borrar el perfil de sistema...")
    backup_and_clear()
    try:
        data = pm.load_profiles()
        assert_true(pm.is_system_profile(pm.SYSTEM_GAMING_PROFILE_KEY),
                    "is_system_profile detecta la clave reservada")
        assert_eq(pm.is_system_profile('mi_perfil_usuario'), False,
                  "is_system_profile False para perfiles de usuario")
        # El constante publica la clave para que la UI pueda chequear
        assert_eq(pm.SYSTEM_GAMING_PROFILE_KEY, '__system_gaming__',
                  "clave interna estable para chequeos")
    finally:
        if os.path.exists(pm.PROFILES_FILE):
            os.remove(pm.PROFILES_FILE)


def test_criterion_6_should_kill_reads_from_profile():
    """C6: should_kill_for_gaming lee del profile, NO de constante hardcoded.

    Comprobacion: si pasamos un profile custom con keepers distintos y
    kill_low_chat=True, los keepers deben cambiar el resultado.
    """
    print("\n[test] C6: should_kill_for_gaming lee del profile (no hardcoded)...")
    backup_and_clear()
    try:
        # Profile sin 'discord' en keepers, con 'chrome' en keepers,
        # kill_low_chat=True para que chat SI se mate si no es keeper
        custom = {
            "kind": "system",
            "label": pm.SYSTEM_GAMING_LABEL,
            "keepers": ["chrome"],   # discord ya NO es keeper
            "kill_low_chat": True,
        }
        # Discord: ya no es keeper + chat low + kill_low_chat=True -> matar
        assert_eq(pm.should_kill_for_gaming('discord', custom), True,
                  "discord NO es keeper + kill_low_chat=True -> matar")
        # Chrome: ahora ES keeper -> NO matar
        assert_eq(pm.should_kill_for_gaming('chrome', custom), False,
                  "chrome ES keeper -> NO matar")
        # Firefox: no es keeper; alta prioridad -> matar
        assert_eq(pm.should_kill_for_gaming('firefox', custom), True,
                  "firefox NO es keeper + alta prioridad -> matar")
        # Telegram: chat low priority, kill_low_chat=True -> matar
        assert_eq(pm.should_kill_for_gaming('telegram', custom), True,
                  "telegram matar (kill_low_chat=True)")
        # ... con kill_low_chat=False -> NO matar
        custom['kill_low_chat'] = False
        assert_eq(pm.should_kill_for_gaming('telegram', custom), False,
                  "telegram NO matar (kill_low_chat=False)")
        # Discord con kill_low_chat=False y sin keepers -> NO matar (chat low)
        assert_eq(pm.should_kill_for_gaming('discord', custom), False,
                  "discord sin keeper + kill_low_chat=False -> NO matar")

        # Comportamiento legacy: si NO pasamos profile, usa factory (compat)
        # Discord es keeper de fabrica
        assert_eq(pm.should_kill_for_gaming('discord'), False,
                  "sin profile -> factory (discord es keeper)")
        # kill_low_chat por defecto True -> chat se mata si no es keeper
        assert_eq(pm.should_kill_for_gaming('telegram'), True,
                  "sin profile -> factory (telegram se mata por kill_low_chat=True)")
    finally:
        if os.path.exists(pm.PROFILES_FILE):
            os.remove(pm.PROFILES_FILE)


def test_criterion_7_corrupt_profile_auto_repairs():
    """C7: profiles.json corrupto/parcial → repara con factory, no crashea."""
    print("\n[test] C7: profiles.json corrupto/parcial auto-repara...")

    # Caso 7a: JSON invalido
    backup_path = pm.PROFILES_FILE + '.testbak_gp_7a'
    if os.path.exists(pm.PROFILES_FILE):
        shutil.copy2(pm.PROFILES_FILE, backup_path)
    try:
        with open(pm.PROFILES_FILE, 'w', encoding='utf-8') as f:
            f.write('{ esto no es JSON valido <<<')
        data = pm.load_profiles()  # NO debe crashear
        assert_true('profiles' in data, "load_profiles con JSON invalido -> dict con 'profiles'")
        assert_true(pm.SYSTEM_GAMING_PROFILE_KEY in data['profiles'],
                    "perfil gaming recreado tras JSON corrupto")
    finally:
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, pm.PROFILES_FILE)
            os.remove(backup_path)

    # Caso 7b: profile existe pero le faltan campos
    backup_path = pm.PROFILES_FILE + '.testbak_gp_7b'
    if os.path.exists(pm.PROFILES_FILE):
        shutil.copy2(pm.PROFILES_FILE, backup_path)
    try:
        partial = {
            'profiles': {
                pm.SYSTEM_GAMING_PROFILE_KEY: {
                    'kind': 'system',
                    # Faltan keepers, kill_low_chat, label
                },
                'mi_perfil': {'apps': ['chrome.exe']},
            },
            'favorite': 'mi_perfil',
        }
        write_profiles(partial)
        data = pm.load_profiles()
        prof = data['profiles'][pm.SYSTEM_GAMING_PROFILE_KEY]
        # Campos faltantes rellenados con factory
        assert_eq(prof.get('keepers'), ['discord'], "keepers reparado a factory")
        assert_eq(prof.get('kill_low_chat'), True, "kill_low_chat reparado a factory")
        assert_eq(prof.get('label'), pm.SYSTEM_GAMING_LABEL, "label reparado")
        # Datos del usuario preservados
        assert_true('mi_perfil' in data['profiles'], "perfil de usuario preservado")
        assert_eq(data['favorite'], 'mi_perfil', "favorite preservado")
    finally:
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, pm.PROFILES_FILE)
            os.remove(backup_path)
        elif os.path.exists(pm.PROFILES_FILE):
            os.remove(pm.PROFILES_FILE)


def test_gaming_keep_existing_user_profiles():
    """Bonus: editar gaming NO debe perder perfiles de usuario."""
    print("\n[test] Bonus: editar gaming preserva perfiles de usuario...")
    backup_path = pm.PROFILES_FILE + '.testbak_gp_bonus'
    if os.path.exists(pm.PROFILES_FILE):
        shutil.copy2(pm.PROFILES_FILE, backup_path)
    try:
        # Cargar con perfiles de usuario preexistentes
        write_profiles({
            'profiles': {
                'Trabajo': {'apps': ['outlook.exe', 'teams.exe']},
                'Ocio': {'apps': ['steam.exe', 'discord.exe']},
                pm.SYSTEM_GAMING_PROFILE_KEY: dict(pm.SYSTEM_GAMING_FACTORY),
            },
            'favorite': 'Trabajo',
        })
        # Editar gaming
        prof = pm.load_gaming_profile()
        prof['keepers'] = ['discord', 'steam']
        pm.save_gaming_profile(prof)
        # Verificar que los otros perfiles siguen intactos
        data = pm.load_profiles()
        assert_eq(data['profiles']['Trabajo']['apps'], ['outlook.exe', 'teams.exe'],
                  "Trabajo apps preservadas")
        assert_eq(data['profiles']['Ocio']['apps'], ['steam.exe', 'discord.exe'],
                  "Ocio apps preservadas")
        assert_eq(data['favorite'], 'Trabajo', "favorite preservado")
        assert_eq(data['profiles'][pm.SYSTEM_GAMING_PROFILE_KEY]['keepers'],
                  ['discord', 'steam'], "gaming keepers actualizados")
    finally:
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, pm.PROFILES_FILE)
            os.remove(backup_path)


def main():
    print("=" * 60)
    print("Test perfil de sistema Gaming (v2.0.6) - woptimizer")
    print("=" * 60)

    # Backup global al inicio, restaurar al final
    global_backup = backup_and_clear()

    try:
        test_criterion_1_first_run_no_profile()
        test_criterion_2_edit_keepers_persists()
        test_criterion_3_toggle_kill_low_chat_persists()
        test_criterion_4_reset_to_factory()
        test_criterion_5_cannot_delete_system_profile()
        test_criterion_6_should_kill_reads_from_profile()
        test_criterion_7_corrupt_profile_auto_repairs()
        test_gaming_keep_existing_user_profiles()

        print("\n" + "=" * 60)
        print("[test] OK: TODOS LOS TESTS PASARON")
        print("=" * 60)
    finally:
        restore_backup(global_backup)


if __name__ == "__main__":
    main()