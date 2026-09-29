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

def test_freed_mb_return_type():
    """TASK-013/014: kill_pack_apps y kill_processes deben retornar freed_mb como float >= 0."""
    print("Testing freed_mb return type...")
    from woptimizer.services.process_service import ProcessService
    ps = ProcessService()
    
    # Con lista vacía
    k, f, s, mb = ps.kill_pack_apps([])
    assert isinstance(mb, float), f"freed_mb debe ser float, got {type(mb)}"
    assert mb >= 0.0, f"freed_mb debe ser >= 0, got {mb}"
    
    # Con proceso inexistente
    k2, f2, s2, mb2 = ps.kill_pack_apps(["__completamente_inexistente_xyzzy_42.exe"])
    assert isinstance(mb2, float), f"freed_mb debe ser float, got {type(mb2)}"
    assert mb2 == 0.0, f"freed_mb para proc inexistente debe ser 0.0, got {mb2}"
    
    # kill_processes con lista vacía también
    k3, f3, s3, mb3 = ps.kill_processes([])
    assert isinstance(mb3, float)
    assert mb3 == 0.0
    print("freed_mb return type OK.")


def test_gaming_pack_protected():
    """Invariante: el pack con is_gaming=True NO puede ser eliminado."""
    print("Testing gaming pack deletion protection...")
    import tempfile, os
    from woptimizer.services.pack_service import PackService
    
    # Usar un archivo temporal para no tocar profiles.json real
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode='w', encoding='utf-8')
    tmp.write('{}')
    tmp.close()
    
    try:
        ps = PackService(data_path=tmp.name)
        
        # Verificar que el gaming pack existe
        gaming = ps.get_gaming_pack()
        assert gaming.is_gaming is True, "Gaming pack debe tener is_gaming=True"
        
        # Intentar eliminar debe lanzar ValueError
        raised = False
        try:
            ps.delete_pack("gaming")
        except ValueError as e:
            raised = True
            assert "Gaming" in str(e) or "gaming" in str(e).lower()
        
        assert raised, "delete_pack('gaming') debe lanzar ValueError"
        
        # Verificar que sigue existiendo
        assert "gaming" in ps.get_all_packs(), "Gaming pack debe seguir existiendo tras intento de borrado"
        print("Gaming pack protection OK.")
    finally:
        os.unlink(tmp.name)


def test_corrupted_json_recovery():
    """Resiliencia: profiles.json corrupto debe auto-recuperarse con el pack Gaming."""
    print("Testing corrupted JSON recovery...")
    import tempfile, os
    from woptimizer.services.pack_service import PackService
    
    # Crear un archivo con JSON corrupto
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode='w', encoding='utf-8')
    tmp.write('{ESTO NO ES JSON VALIDO!!!')
    tmp.close()
    
    try:
        # PackService debe recuperarse sin explotar
        ps = PackService(data_path=tmp.name)
        
        # Debe tener al menos el gaming pack restaurado
        packs = ps.get_all_packs()
        assert "gaming" in packs, "Tras JSON corrupto, gaming pack debe regenerarse"
        assert packs["gaming"].is_gaming is True
        print("Corrupted JSON recovery OK.")
    finally:
        os.unlink(tmp.name)


if __name__ == "__main__":
    print("--- Running Backend Tests ---")
    test_models()
    test_process_service_signatures()
    test_freed_mb_return_type()
    test_gaming_pack_protected()
    test_corrupted_json_recovery()
    print("\n--- Running Headless UI Test ---")
    test_headless_ui()
    print("\nALL TESTS PASSED.")
