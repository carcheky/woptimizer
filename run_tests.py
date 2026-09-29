import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.abspath("src"))

def test_models():
    print("Testing models...")
    from woptimizer.models import ProcessInfo, Pack, AppData
    p = ProcessInfo(name="test", full_name="test.exe", pid=123)
    assert p.description == "Sin descripción"
    pack = Pack(id="test", name="Test Pack", apps=["test.exe"])
    assert pack.default_action == "start"
    print("Models OK.")

def test_process_service_signatures():
    print("Testing ProcessService signatures...")
    from woptimizer.services.process_service import ProcessService
    ps = ProcessService()
    
    # Lista vacía
    res_proc = ps.kill_processes([])
    assert len(res_proc) == 4, f"Esperado 4-tupla, obtenido {res_proc}"
    assert res_proc == (0, 0, 0, 0.0)
    assert isinstance(res_proc[3], float)
    
    res_pack = ps.kill_pack_apps([])
    assert len(res_pack) == 4, f"Esperado 4-tupla, obtenido {res_pack}"
    assert res_pack == (0, 0, 0, 0.0)
    assert isinstance(res_pack[3], float)
    
    # Proceso inexistente
    res_dummy = ps.kill_pack_apps(["__non_existent_proc_xyz_123.exe"])
    assert res_dummy == (0, 0, 0, 0.0)
    print("ProcessService signatures OK.")

def test_headless_ui():
    print("Testing headless UI...")
    from woptimizer.ui.app import WOptimizerApp
    from woptimizer.services.process_service import ProcessService
    from woptimizer.services.pack_service import PackService
    from woptimizer.services.gaming_service import GamingService

    ps = ProcessService()
    pack_s = PackService()
    gs = GamingService(ps, pack_s)
    
    app = WOptimizerApp(ps, pack_s, gs)
    
    # After 1.5 seconds, destroy the root to stop mainloop
    app.root.after(1500, app.root.destroy)
    
    print("Starting app mainloop for 1.5s...")
    app.run()
    print("Headless UI test OK.")

if __name__ == "__main__":
    print("--- Running Backend Tests ---")
    test_models()
    test_process_service_signatures()
    print("\n--- Running Headless UI Test ---")
    test_headless_ui()
    print("\nALL TESTS PASSED.")
