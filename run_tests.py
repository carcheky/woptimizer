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
    
    # autostart_tray=False: en tests no levantamos pystray (evita hilos y
    # dependencia de un shell de escritorio en runners headless).
    app = WOptimizerApp(ps, pack_s, gs, autostart_tray=False)
    
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


class _FakeTrayIcon:
    """Doble de prueba para pystray.Icon: no toca el sistema operativo."""
    HAS_NOTIFICATION = True

    def __init__(self):
        self.calls = []

    def notify(self, message, title=None):
        self.calls.append((title, message))


class _ExplodingTrayIcon:
    """Emula un backend que falla: el servicio no debe propagar la excepcion."""
    HAS_NOTIFICATION = True

    def notify(self, message, title=None):
        raise RuntimeError("backend de notificaciones caido")


def test_notification_without_tray_degrades():
    """TASK-019: sin bandeja adjunta, notify() retorna False y NO lanza."""
    print("Testing NotificationService sin tray...")
    from woptimizer.services.notification_service import NotificationService

    ns = NotificationService()
    assert ns.has_tray is False, "Sin attach, has_tray debe ser False"

    # No debe lanzar excepcion
    assert ns.notify("titulo", "mensaje") is False
    assert ns.notify_kill_result(3, 0, 120.5) is False
    assert ns.notify_pack_activated("Gaming Mode", 5, 200.0) is False
    assert ns.notify_apps_launched("Trabajo", 2, 0) is False

    stats = ns.stats
    assert stats["dropped"] == 4, f"Esperaba 4 descartadas, obtuve {stats}"
    assert stats["sent"] == 0
    print("NotificationService sin tray OK.")


def test_notification_attach_detach():
    """TASK-019: attach habilita, detach deshabilita; los helpers delegan bien."""
    print("Testing NotificationService attach/detach...")
    from woptimizer.services.notification_service import NotificationService

    ns = NotificationService()
    fake = _FakeTrayIcon()

    ns.attach_tray(fake)
    assert ns.has_tray is True
    assert ns.notify("Titulo X", "Cuerpo Y") is True
    assert fake.calls == [("Titulo X", "Cuerpo Y")], f"Llamada inesperada: {fake.calls}"

    # attach es idempotente (re-asignar no rompe nada)
    ns.attach_tray(fake)
    assert ns.notify("Segundo", "Cuerpo") is True
    assert len(fake.calls) == 2

    ns.detach_tray()
    assert ns.has_tray is False
    assert ns.notify("Tercero", "Cuerpo") is False
    assert len(fake.calls) == 2, "Tras detach no debe emitir nuevas notificaciones"

    stats = ns.stats
    assert stats["sent"] == 2 and stats["dropped"] == 1, f"Contadores inesperados: {stats}"
    print("NotificationService attach/detach OK.")


def test_notification_never_raises():
    """TASK-019: un backend que explota se degrada a log, nunca rompe la UI."""
    print("Testing NotificationService resiliencia...")
    from woptimizer.services.notification_service import NotificationService

    ns = NotificationService()
    ns.attach_tray(_ExplodingTrayIcon())

    # No debe propagar la excepcion
    assert ns.notify("titulo", "mensaje") is False
    assert ns.notify_kill_result(1, 0, 0.0) is False
    assert ns.stats["dropped"] == 2, f"Esperaba 2 descartadas, obtive {ns.stats}"
    print("NotificationService resiliencia OK.")


def test_notification_message_formatting():
    """TASK-019: los helpers formatean mensajes en español, con plurales correctos."""
    print("Testing NotificationService message formatting...")
    from woptimizer.services.notification_service import (
        NotificationService, format_kill_result
    )

    # Singular
    assert format_kill_result(1, 0) == "1 cerrada"
    # Plural
    assert format_kill_result(5, 0) == "5 cerradas"
    # Con MB
    assert "150.5 MB liberados" in format_kill_result(3, 0, 150.5)
    # Sin MB si freed_mb es 0
    assert "MB liberados" not in format_kill_result(3, 0, 0.0)
    # Fallos incluidos
    assert "2 fallidas" in format_kill_result(3, 2)
    assert "1 fallida" in format_kill_result(3, 1)

    # El nombre del pack viaja en el cuerpo del toast
    ns = NotificationService()
    fake = _FakeTrayIcon()
    ns.attach_tray(fake)
    ns.notify_apps_launched("Pack Trabajo", 2, 1)
    title, body = fake.calls[0]
    assert "Pack Trabajo" in body
    assert "2 apps iniciadas" in body
    assert "1 fallaron" in body
    print("NotificationService message formatting OK.")


def test_category_emoji_alignment():
    """TASK-020: cada categoría del JSON DEBE existir literalmente en config.py.

    Si un emoji no coincide exactamente, el lookup por categoría falla y el
    proceso cae en "? Otros", perdiendo su semáforo de seguridad.
    """
    print("Testing category emoji alignment...")
    import json
    from woptimizer.config import PROCESS_CATEGORIES

    with open("assets/process_db.json", encoding="utf-8") as fh:
        db = json.load(fh)

    db_cats = {meta.get("category") for meta in db.values()}
    cfg_cats = set(PROCESS_CATEGORIES.keys())

    orphans = db_cats - cfg_cats
    assert not orphans, f"Categorias del JSON ausentes en config.py: {orphans}"

    # Toda categoría de config.py usada por el JSON debe tener badge coherente
    print(f"Category emoji alignment OK ({len(db_cats)} categorias, 0 huerfanas).")


def test_safety_badge_category_priority_order():
    """TASK-020: la categoría manda sobre la prioridad en get_safety_badge.

    Regresión del bug donde `priority in [medium, low]` se evaluaba antes que
    el emoji de categoría, pintando 🔴 como 🟡 PRECAUCIÓN.
    """
    print("Testing safety badge category/priority order...")
    from woptimizer.config import get_safety_badge

    # 🔴 debe ganar a cualquier prioridad
    for prio in ("low", "medium", "high", "none"):
        r = get_safety_badge("\U0001F534 Overlays e Info", prio)
        assert r["text"].startswith("\U0001F534"), f"Overlays prio={prio} -> {r['text']}"
        r = get_safety_badge("\U0001F534 Sistema de Windows", prio)
        assert r["text"].startswith("\U0001F534"), f"Sistema prio={prio} -> {r['text']}"

    # 🟢 y 🟡 con sus prioridades esperadas
    assert "SEGURO" in get_safety_badge("\U0001F7E2 Navegadores", "high")["text"]
    assert "SEGURO" in get_safety_badge("\U0001F7E2 Sincronización", "high")["text"]
    assert "SEGURO" in get_safety_badge("\U0001F7E2 Productividad", "medium")["text"]
    assert "PRECAUCI" in get_safety_badge("\U0001F7E1 Chat y Comunicación", "low")["text"]
    assert "PRECAUCI" in get_safety_badge("\U0001F7E1 Media y Streaming", "medium")["text"]
    assert "PRECAUCI" in get_safety_badge("\U0001F7E1 Launchers Gaming", "none")["text"]
    print("Safety badge category/priority order OK.")


if __name__ == "__main__":
    print("--- Running Backend Tests ---")
    test_models()
    test_process_service_signatures()
    test_freed_mb_return_type()
    test_gaming_pack_protected()
    test_corrupted_json_recovery()
    test_notification_without_tray_degrades()
    test_notification_attach_detach()
    test_notification_never_raises()
    test_notification_message_formatting()
    test_category_emoji_alignment()
    test_safety_badge_category_priority_order()
    print("\n--- Running Headless UI Test ---")
    test_headless_ui()
    print("\nALL TESTS PASSED.")
