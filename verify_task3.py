import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
from woptimizer.services.process_service import ProcessService

print("--- VERIFICANDO TASK-003 (ProcessService Headless Test) ---")
ps = ProcessService()
try:
    ps.kill_pack_apps([])
    print("✅ kill_pack_apps maneja lista vacía correctamente.")
    ps.start_pack_apps([])
    print("✅ start_pack_apps maneja lista vacía correctamente.")
except Exception as e:
    print(f"❌ ERROR: {e}")

# Probando lista con un dummy process (no debería crashear gracias a los try/except)
try:
    ps.kill_pack_apps(["_dummy_process_that_does_not_exist.exe"])
    print("✅ kill_pack_apps maneja dummy app sin crashear.")
    ps.start_pack_apps(["_dummy_process_that_does_not_exist.exe"])
    print("✅ start_pack_apps maneja dummy app sin crashear.")
except Exception as e:
    print(f"❌ ERROR: {e}")
