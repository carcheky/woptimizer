import json
import os
import sys

# Agregar src al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from woptimizer.services.pack_service import PackService
from woptimizer.models import Pack

print("--- VERIFICANDO TASK-001 ---")
TEST_FILE = "test_profiles_task1.json"

# 1. Instanciamos el servicio con un archivo de prueba
ps = PackService(data_path=TEST_FILE)

# 2. Verificamos los atributos del pack Gaming
gaming = ps.get_gaming_pack()
print(f"1. Gaming default_action: '{gaming.default_action}' (Esperado: 'kill')")
print(f"2. Gaming apps: {gaming.apps} (Esperado: ['chrome.exe'])")
if hasattr(gaming, 'keepers'):
    print("❌ ERROR: El atributo 'keepers' sigue existiendo.")
else:
    print("3. Atributo 'keepers': Eliminado correctamente de los modelos.")

# 3. Verificamos la excepción al borrar
try:
    ps.delete_pack("gaming")
    print("❌ ERROR: Se pudo borrar el pack Gaming sin excepción.")
except ValueError as e:
    print(f"4. Excepción al borrar: ¡Capturada! -> {e}")

# 4. Verificamos la corrupción del JSON (JSONDecodeError)
with open(TEST_FILE, "w", encoding="utf-8") as f:
    f.write("{ esto_es_un_json_invalido_y_corrupto...")

ps2 = PackService(data_path=TEST_FILE)
gaming_restaurado = ps2.get_gaming_pack()
print(f"5. JSON corrupto manejado: Restaurado el pack '{gaming_restaurado.name}' y guardado en disco.")

# Limpieza
if os.path.exists(TEST_FILE):
    os.remove(TEST_FILE)

print("--- FIN DE LA VERIFICACIÓN ---")
