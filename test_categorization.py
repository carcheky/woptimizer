"""Test rapido: verifica que procesos clave caen en las categorias correctas."""
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
import process_manager as pm


def assert_eq(actual, expected, msg=""):
    if actual != expected:
        print(f"[test]   FAIL: {msg}")
        print(f"[test]     esperado: {expected!r}")
        print(f"[test]     actual:   {actual!r}")
        sys.exit(1)
    else:
        print(f"[test]   ok: {msg}")


print("[test] Verificando categorizacion...")

# Notepad (Windows 11) debe caer en Productividad
cat = pm.categorize_process('Notepad')
assert_eq(cat, '🟡 Productividad', "Notepad -> Productividad")
assert_eq(cat in pm.SIMPLE_MODE_CATEGORIES, True, "Notepad visible en Simple mode")

# wordpad tambien
cat = pm.categorize_process('wordpad')
assert_eq(cat, '🟡 Productividad', "wordpad -> Productividad")

# Casos que NO deben cambiar (regresion)
assert_eq(pm.categorize_process('chrome'), '🔴 Navegadores', "chrome sigue en Navegadores")
assert_eq(pm.categorize_process('discord'), '🟡 Chat y Comunicación', "discord sigue en Chat")
assert_eq(pm.categorize_process('spotify'), '🟡 Media', "spotify sigue en Media")
assert_eq(pm.categorize_process('svchost'), '⚫ Sistema', "svchost sigue en Sistema")

# Casos con extensiones y case mixto
assert_eq(pm.categorize_process('Notepad.exe'), '🟡 Productividad', "Notepad.exe con extension")
assert_eq(pm.categorize_process('NOTEPAD'), '🟡 Productividad', "NOTEPAD uppercase")

# --- Regla critica: Chat NO debe matarse en gaming ---
# Discord / Teams / Slack son apps gamer-friendly: se mantienen durante el juego
# porque el user quiere chatear con amigos mientras juega.
# Si la prioridad fuera 'medium', prepare_for_gaming() lo mata. Debe ser 'low'.
print("[test] Verificando que Chat NO se mate en gaming (regla gamer)...")
chat_priority = pm.PROCESS_CATEGORIES['🟡 Chat y Comunicación']['priority']
assert_eq(chat_priority, 'low', "Chat y Comunicacion debe tener priority=low (NO matar en gaming)")

# Simulamos el filtro que hace prepare_for_gaming
would_kill_discord = chat_priority in ('high', 'medium')
assert_eq(would_kill_discord, False, "Discord NO debe estar en la lista de kill del gamemode")

# El resto de los procesos del usuario que SÍ queremos matar en gaming:
assert_eq(pm.PROCESS_CATEGORIES['🔴 Navegadores']['priority'], 'high', "Navegadores sigue high (matar)")
assert_eq(pm.PROCESS_CATEGORIES['🔴 Sincronización']['priority'], 'high', "Sincronizacion sigue high (matar)")
assert_eq(pm.PROCESS_CATEGORIES['🟡 Productividad']['priority'], 'medium', "Productividad sigue medium (matar)")
assert_eq(pm.PROCESS_CATEGORIES['🟡 Media']['priority'], 'medium', "Media sigue medium (matar)")
assert_eq(pm.PROCESS_CATEGORIES['🟢 Overlays / Streaming']['priority'], 'low', "Overlays low (mantener)")
assert_eq(pm.PROCESS_CATEGORIES['⚫ Antivirus / Seguridad']['priority'], 'none', "Antivirus none (mantener)")
assert_eq(pm.PROCESS_CATEGORIES['⚫ Sistema']['priority'], 'none', "Sistema none (mantener)")

print("\n[test] PASS - categorizacion correcta")
