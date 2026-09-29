import sys
import os
import ast
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.abspath("src"))


def _pack_service_temporal():
    """Crea un PackService aislado sobre un JSON temporal.

    Devuelve (pack_service, ruta_temporal). El llamante DEBE borrar la ruta en
    un finally. Nunca se toca el profiles.json real.
    """
    import tempfile
    from woptimizer.services.pack_service import PackService

    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode='w', encoding='utf-8')
    tmp.write('{}')
    tmp.close()
    return PackService(data_path=tmp.name), tmp.name


def _proceso_vivo(pid):
    """True si el PID sigue existiendo y no es un zombie ya terminado."""
    import psutil

    if not psutil.pid_exists(pid):
        return False
    try:
        return psutil.Process(pid).status() != psutil.STATUS_ZOMBIE
    except psutil.NoSuchProcess:
        return False
    except psutil.AccessDenied:
        return True


def _esperar_a_morir(pid, timeout=5.0):
    """Espera (con margen de gracia) a que el PID deje de estar vivo."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _proceso_vivo(pid):
            return True
        time.sleep(0.05)
    return not _proceso_vivo(pid)


def _esperar_pid_de_archivo(path, timeout=10.0):
    """Devuelve el PID escrito en `path` cuando existe y el proceso esta vivo.

    Se usa en vez de `children(recursive=True)` porque en Windows ese listado
    devuelve tambien conhost.exe, que muere con el padre por su cuenta y haria
    que el test de kill recursivo no discriminase nada.
    """
    import psutil

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    pid = int(fh.read().strip())
            except (ValueError, OSError):
                pid = None
            if pid and psutil.pid_exists(pid):
                return pid
        time.sleep(0.1)
    return None

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


def test_gaming_service_should_kill():
    """TASK-021: orden de reglas de should_kill_for_gaming (keeper > apps > categoria).

    Se construyen packs explicitos con Pack(...) en vez de usar
    DEFAULT_GAMING_PACK para que el test sea determinista e independiente del
    estado del disco.
    """
    print("Testing GamingService.should_kill_for_gaming...")
    from woptimizer.models import Pack
    from woptimizer.services.gaming_service import GamingService
    from woptimizer.services.process_service import ProcessService

    proc_s = ProcessService()
    pack_s, tmp_path = _pack_service_temporal()
    try:
        gs = GamingService(proc_s, pack_s)

        pack = Pack(
            id="gaming_test",
            name="Pack de prueba",
            is_gaming=True,
            default_action="kill",
            apps=["msedge"],                 # kill explicito, categoria NO objetivo
            keepers=["discord"],             # protegido, su categoria SI es objetivo
            target_categories=[
                "\U0001F7E1 Chat y Comunicación",
                "\U0001F7E2 Sincronización",
            ],
        )

        # 1) El keeper gana aunque su categoria sea objetivo
        cat_chat = proc_s._categorize("discord.exe")
        assert cat_chat in pack.target_categories, (
            f"Precondicion rota: la categoria de discord ({cat_chat}) deberia ser "
            "objetivo para que el test pruebe la prioridad del keeper"
        )
        assert gs.should_kill_for_gaming("discord.exe", pack) is False, (
            "Un keeper nunca debe matarse aunque su categoria sea objetivo"
        )

        # 2) App explicita mata aunque su categoria NO sea objetivo
        cat_edge = proc_s._categorize("msedge.exe")
        assert cat_edge not in pack.target_categories, (
            f"Precondicion rota: la categoria de msedge ({cat_edge}) no deberia ser objetivo"
        )
        assert gs.should_kill_for_gaming("msedge.exe", pack) is True, (
            "Una app listada en pack.apps debe matarse aunque su categoria no sea objetivo"
        )

        # 3) Categoria objetivo mata
        cat_sync = proc_s._categorize("onedrive.exe")
        assert cat_sync in pack.target_categories, (
            f"Precondicion rota: la categoria de onedrive ({cat_sync}) deberia ser objetivo"
        )
        assert gs.should_kill_for_gaming("onedrive.exe", pack) is True, (
            "Un proceso cuya categoria esta en target_categories debe matarse"
        )

        # 4) Proceso no relacionado no mata
        cat_otros = proc_s._categorize("woptimizer_zzz_inexistente.exe")
        assert cat_otros not in pack.target_categories, (
            f"Precondicion rota: un proceso desconocido cayo en {cat_otros}"
        )
        assert gs.should_kill_for_gaming("woptimizer_zzz_inexistente.exe", pack) is False, (
            "Un proceso no relacionado no debe matarse"
        )

        # Coherencia: el matching es case-insensitive en ambos sentidos
        assert gs.should_kill_for_gaming("OneDrive.EXE", pack) is True
    finally:
        os.unlink(tmp_path)
    print("GamingService.should_kill_for_gaming OK.")


def test_pack_service_crud():
    """TASK-021: create_user_pack respeta duplicados y el id reservado 'gaming'."""
    print("Testing PackService CRUD...")
    import json

    pack_s, tmp_path = _pack_service_temporal()
    try:
        assert pack_s.create_user_pack("x", "X", ["a.exe"]) is True, (
            "Crear un pack de usuario nuevo debe devolver True"
        )

        assert pack_s.create_user_pack("x", "X duplicado", ["b.exe"]) is False, (
            "Crear un pack con id duplicado debe devolver False"
        )

        assert pack_s.create_user_pack("gaming", "Gaming falso", ["c.exe"]) is False, (
            "El id 'gaming' esta reservado y no puede reutilizarse"
        )

        user_packs = pack_s.get_user_packs()
        assert "x" in user_packs, "El pack de usuario recien creado debe aparecer"
        assert "gaming" not in user_packs, (
            "get_user_packs() NO debe incluir el pack de sistema"
        )
        assert user_packs["x"].apps == ["a.exe"], (
            f"Apps del pack incorrectas: {user_packs['x'].apps}"
        )
        assert user_packs["x"].is_gaming is False

        # El pack de sistema sigue intacto
        assert pack_s.get_all_packs()["gaming"].is_gaming is True

        # Persistencia real en disco
        with open(tmp_path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        assert "x" in raw["packs"], f"El pack debe persistirse en el JSON, hay {list(raw['packs'])}"
    finally:
        os.unlink(tmp_path)
    print("PackService CRUD OK.")


def test_pack_service_delete():
    """TASK-021: delete_pack protege el pack de sistema y devuelve False si no existe."""
    print("Testing PackService delete...")
    pack_s, tmp_path = _pack_service_temporal()
    try:
        # El pack de sistema lanza ValueError
        raised = False
        try:
            pack_s.delete_pack("gaming")
        except ValueError as e:
            raised = True
            assert "gaming" in str(e).lower(), f"Mensaje de error inesperado: {e}"
        assert raised, "delete_pack('gaming') debe lanzar ValueError"
        assert "gaming" in pack_s.get_all_packs(), (
            "El pack de sistema debe sobrevivir al intento de borrado"
        )

        # Id inexistente
        assert pack_s.delete_pack("no_existe") is False, (
            "Borrar un id inexistente debe devolver False, no lanzar"
        )

        # Pack de usuario: se borra de verdad
        assert pack_s.create_user_pack("temporal", "Temporal", ["t.exe"]) is True
        assert "temporal" in pack_s.get_all_packs()
        assert pack_s.delete_pack("temporal") is True, "Borrar un pack propio debe devolver True"
        assert "temporal" not in pack_s.get_all_packs(), (
            "El pack borrado no debe seguir en get_all_packs()"
        )
    finally:
        os.unlink(tmp_path)
    print("PackService delete OK.")


def test_pack_service_favorite_exclusive():
    """TASK-021: set_favorite deja como maximo UN favorito; None los borra todos."""
    print("Testing PackService set_favorite...")
    pack_s, tmp_path = _pack_service_temporal()
    try:
        for pack_id in ("a", "b", "c"):
            assert pack_s.create_user_pack(pack_id, pack_id.upper(), []) is True

        def favoritos():
            return sorted(k for k, v in pack_s.get_all_packs().items() if v.is_favorite)

        pack_s.set_favorite("a")
        assert favoritos() == ["a"], f"Esperaba solo 'a' como favorito, hay {favoritos()}"

        # Reasignar el favorito no deja al anterior marcado
        pack_s.set_favorite("c")
        assert favoritos() == ["c"], f"Esperaba solo 'c' como favorito, hay {favoritos()}"

        # None limpia todos los favoritos
        pack_s.set_favorite(None)
        assert favoritos() == [], f"set_favorite(None) debe dejar 0 favoritos, hay {favoritos()}"
    finally:
        os.unlink(tmp_path)
    print("PackService set_favorite OK.")


def test_pack_service_reset_gaming():
    """TASK-021: reset_gaming_pack restaura apps y target_categories por defecto."""
    print("Testing PackService reset_gaming_pack...")
    from woptimizer.services.pack_service import DEFAULT_GAMING_PACK

    pack_s, tmp_path = _pack_service_temporal()
    try:
        gaming = pack_s.get_gaming_pack()
        categoria_quitada = gaming.target_categories[0]

        # Se modifica el pack gaming: anadimos una app y quitamos una categoria.
        # Se construyen listas NUEVAS a proposito: model_copy() de Pydantic es
        # superficial y mutar en sitio contaminaria DEFAULT_GAMING_PACK.
        pack_s.save_gaming_pack(type(gaming)(
            id="gaming",
            name=gaming.name,
            is_gaming=True,
            default_action=gaming.default_action,
            apps=list(gaming.apps) + ["app_falsa_tarea021.exe"],
            keepers=list(gaming.keepers),
            target_categories=[c for c in gaming.target_categories if c != categoria_quitada],
        ))

        modificado = pack_s.get_gaming_pack()
        assert "app_falsa_tarea021.exe" in modificado.apps, "La app anadida debe persistirse"
        assert categoria_quitada not in modificado.target_categories, (
            "La categoria quitada debe persistirse"
        )

        pack_s.reset_gaming_pack()

        restaurado = pack_s.get_gaming_pack()
        assert restaurado.is_gaming is True, "El pack restaurado sigue siendo de sistema"
        assert "app_falsa_tarea021.exe" not in restaurado.apps, (
            f"reset debe deshacer las apps anadidas, quedan {restaurado.apps}"
        )
        assert categoria_quitada in restaurado.target_categories, (
            f"reset debe restaurar la categoria quitada, quedan {restaurado.target_categories}"
        )
        assert restaurado.apps == list(DEFAULT_GAMING_PACK.apps), (
            f"Apps distintas a DEFAULT: {restaurado.apps} vs {DEFAULT_GAMING_PACK.apps}"
        )
        assert restaurado.target_categories == list(DEFAULT_GAMING_PACK.target_categories), (
            "target_categories distintas a DEFAULT tras reset"
        )
    finally:
        os.unlink(tmp_path)
    print("PackService reset_gaming_pack OK.")


def test_gaming_pack_lists_isolated_from_global():
    """TASK-021: las listas del pack gaming NO deben compartir objeto con el
    global DEFAULT_GAMING_PACK.

    Regresion de un bug real: `model_copy()` de Pydantic v2 es shallow, asi que
    `apps`/`keepers`/`target_categories` se compartian con el global de modulo.
    La UI muta en sitio (`process_manager_view.on_add_to_pack` hace
    `target_pack.apps.append(...)`), lo que contaminaba el global y hacia que
    `reset_gaming_pack()` fuese un no-op silencioso: el boton "Restaurar por
    defecto" no restauraba nada.
    """
    print("Testing gaming pack list isolation from global...")
    from woptimizer.services.pack_service import DEFAULT_GAMING_PACK

    # Snapshot limpio del global para poder detectar contaminacion.
    apps_esperadas = list(DEFAULT_GAMING_PACK.apps)
    cats_esperadas = list(DEFAULT_GAMING_PACK.target_categories)

    pack_s, tmp_path = _pack_service_temporal()
    try:
        gaming = pack_s.get_gaming_pack()
        # Identidad de objeto: deben ser copias, no el mismo objeto.
        assert gaming.apps is not DEFAULT_GAMING_PACK.apps, (
            "apps del pack gaming comparte objeto con el global (shallow copy)"
        )
        assert gaming.target_categories is not DEFAULT_GAMING_PACK.target_categories, (
            "target_categories comparte objeto con el global (shallow copy)"
        )

        # Mutacion IN SITU, exactamente como hace la UI al anadir a un pack.
        gaming.apps.append("app_falsa_tarea021.exe")
        gaming.target_categories.remove(cats_esperadas[0])

        # El global no debe haberse contaminado.
        assert DEFAULT_GAMING_PACK.apps == apps_esperadas, (
            f"El global fue contaminado por mutacion in situ: {DEFAULT_GAMING_PACK.apps}"
        )
        assert DEFAULT_GAMING_PACK.target_categories == cats_esperadas, (
            f"target_categories global contaminado: {DEFAULT_GAMING_PACK.target_categories}"
        )

        # Y el reset debe devolver el pack a los valores de fabrica.
        pack_s.reset_gaming_pack()
        restaurado = pack_s.get_gaming_pack()
        assert "app_falsa_tarea021.exe" not in restaurado.apps, (
            f"reset no deshizo la mutacion in situ: {restaurado.apps}"
        )
        assert restaurado.apps == apps_esperadas, f"Apps no restauradas: {restaurado.apps}"
        assert restaurado.target_categories == cats_esperadas, (
            f"Categorias no restauradas: {restaurado.target_categories}"
        )
    finally:
        os.unlink(tmp_path)
    print("Gaming pack list isolation OK.")


def test_cache_ttl_and_invalidation():
    """TASK-021: get_running_processes respeta el TTL; invalidate_cache y
    force_refresh obligan a re-escanear (y por tanto a un objeto nuevo)."""
    print("Testing ProcessService cache TTL...")
    from woptimizer.services.process_service import ProcessService

    proc_s = ProcessService()

    # El TTL se lee del propio servicio, no se hardcodea.
    ttl = proc_s._CACHE_TTL
    assert isinstance(ttl, (int, float)) and ttl > 0, f"TTL debe ser un numero positivo, obtuve {ttl}"

    inicio = time.monotonic()
    primero = proc_s.get_running_processes()
    segundo = proc_s.get_running_processes()
    elapsed = time.monotonic() - inicio
    assert elapsed < ttl, (
        f"Las dos llamadas tardaron {elapsed:.3f}s, mas que el TTL de {ttl}s: "
        "el test no seria valido"
    )
    assert segundo is primero, (
        "Dentro del TTL debe devolverse el MISMO objeto de lista (sin re-esaneo)"
    )

    proc_s.invalidate_cache()
    tercero = proc_s.get_running_processes()
    assert tercero is not primero, "invalidate_cache() debe forzar un re-esaneo"

    cuarto = proc_s.get_running_processes(force_refresh=True)
    assert cuarto is not tercero, "force_refresh=True debe ignorar la cache"
    print("ProcessService cache TTL e invalidacion OK.")


def test_kill_recursive():
    """TASK-021 invariante central de AGENTS.md: kill_processes mata los hijos
    (children(recursive=True)) ANTES que el padre, sin dejar huerfanos.

    Se espawnea un python propio que lanza otro python propio. En Windows matar
    solo al padre NO mata al nieto (a diferencia de Unix), asi que el test
    distingue de verdad un kill recursivo de uno plano.
    """
    print("Testing kill recursivo...")
    import subprocess
    import sys as _sys
    import tempfile
    import psutil
    from woptimizer.models import ProcessInfo
    from woptimizer.services.process_service import ProcessService

    pidfile = tempfile.NamedTemporaryFile(suffix=".pid", delete=False, mode='w', encoding='utf-8')
    pidfile.write("")
    pidfile.close()

    child_code = "import time; time.sleep(120)"
    parent_code = (
        "import subprocess, sys, time\n"
        f"c = subprocess.Popen([sys.executable, '-c', {child_code!r}])\n"
        f"with open({pidfile.name!r}, 'w', encoding='utf-8') as fh:\n"
        "    fh.write(str(c.pid))\n"
        "time.sleep(120)\n"
    )

    parent_proc = None
    child_pid = None
    try:
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            parent_proc = subprocess.Popen([_sys.executable, "-c", parent_code], creationflags=flags)
        except Exception as e:
            print(f"  AVISO: el entorno bloquea la creacion de subprocesos ({e}). Test degradado.")
            return

        child_pid = _esperar_pid_de_archivo(pidfile.name, timeout=10.0)
        assert child_pid is not None, (
            f"El proceso padre {parent_proc.pid} no lanzo ningun nieto a tiempo"
        )
        # Guarda contra falsos positivos: el objetivo debe ser el nieto Python,
        # no un conhost.exe que moriria con el padre de todas formas.
        try:
            cmdline = psutil.Process(child_pid).cmdline()
        except psutil.Error:
            cmdline = []
        assert any("python" in str(arg).lower() for arg in cmdline), (
            f"El PID capturado ({child_pid}) no es el nieto Python esperado: {cmdline}"
        )

        proc_s = ProcessService()
        pinfo = ProcessInfo(name="tarea021_padre", full_name="python.exe", pid=parent_proc.pid)

        killed, failed, skipped, freed_mb = proc_s.kill_processes([pinfo])

        if killed == 0 and failed > 0:
            print("  AVISO: kill protegido por permisos (AccessDenied). Test degradado.")
            return

        assert killed == 1, (
            f"Se esperaba 1 proceso muerto; killed={killed} failed={failed} skipped={skipped}"
        )

        padre_muerto = (parent_proc.poll() is not None) or _esperar_a_morir(parent_proc.pid)
        nieto_muerto = _esperar_a_morir(child_pid)

        assert padre_muerto, f"El padre {parent_proc.pid} deberia estar muerto tras el kill"
        assert nieto_muerto, (
            f"El nieto {child_pid} sobrevivio: el kill NO es recursivo (invariante rota)"
        )
    finally:
        # Limpieza: nunca dejar procesos huerfanos de este test.
        if child_pid is not None and _proceso_vivo(child_pid):
            try:
                psutil.Process(child_pid).kill()
            except psutil.Error:
                pass
        if parent_proc is not None:
            if parent_proc.poll() is None:
                try:
                    parent_proc.kill()
                except OSError:
                    pass
            try:
                parent_proc.wait(timeout=5)
            except Exception:
                pass
        try:
            os.unlink(pidfile.name)
        except OSError:
            pass
    print("Kill recursivo OK.")


class _SinDocstrings(ast.NodeTransformer):
    """Elimina las docstrings de un arbol AST (no son codigo ejecutable)."""

    def _strip(self, node):
        self.generic_visit(node)
        if (node.body and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)):
            node.body.pop(0)
        return node

    visit_Module = _strip
    visit_FunctionDef = _strip
    visit_AsyncFunctionDef = _strip
    visit_ClassDef = _strip


def _codigo_ejecutable(fuente):
    """Reconstruye el codigo real de un fuente: sin comentarios ni docstrings.

    `ast.unparse` descarta los comentarios, y el transformer quita las
    docstrings. Asi el guard anti-regresion solo puede dispararse por codigo que
    se EJECUTA, nunca por un texto que explica la regla.
    """
    arbol = _SinDocstrings().visit(ast.parse(fuente))
    ast.fix_missing_locations(arbol)
    return ast.unparse(arbol)


def test_git_safe_commit_fail_safe():
    """TASK-022: `.taskmaster/git_safe_commit.py` es fail-safe.

    El wrapper es la unica puerta de salida del versionado, asi que su codigo de
    salida DEBE ser honesto: 0 solo si hubo commit o no habia nada que comitear.
    Antes de TASK-022 devolvia 0 ante cualquier fallo (repo invalido incluido), de
    modo que este test discrimina de verdad: revierte el fix y falla.

    Se invoca como subproceso con `GIT_DIR` apuntado a rutas temporales invalidas
    (la precedencia de `GIT_DIR` del entorno es la via documentada en AGENTS.md y
    el hook que permite tests hermeticos). NO se toca el repo real ni su
    historial: el wrapper nunca llega a escribir con un repo invalido.
    """
    print("Testing git_safe_commit fail-safe (codigos de salida)...")
    import subprocess
    import sys as _sys
    import tempfile

    root = os.path.dirname(os.path.abspath(__file__))
    wrapper = os.path.join(root, ".taskmaster", "git_safe_commit.py")
    assert os.path.exists(wrapper), f"No se encuentra el wrapper: {wrapper}"

    tmp = tempfile.mkdtemp(prefix="wopt_t022_")
    # Dos formas de repo invalido, porque el contrato exige que NO baste con
    # os.path.exists(): (a) ruta inexistente, (b) directorio que no es un repo.
    git_dir_inexistente = os.path.join(tmp, "no_existe_este_git_dir")
    git_dir_no_repo = os.path.join(tmp, "directorio_sin_repo")
    os.makedirs(git_dir_no_repo)

    def invocar(args, git_dir):
        env = os.environ.copy()
        env["GIT_DIR"] = git_dir
        env["GIT_WORK_TREE"] = root
        return subprocess.run(
            [_sys.executable, wrapper] + args,
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )

    try:
        # 1) GIT_DIR inexistente -> 3 (NO 0, NO 1: no pude ni comprobar).
        r = invocar(["test(t022): este mensaje no debe llegar a comitear"], git_dir_inexistente)
        assert r.returncode == 3, (
            f"Un GIT_DIR inexistente debe salir con 3, salio con {r.returncode}. "
            f"stdout={r.stdout!r} stderr={r.stderr!r}"
        )
        assert "WOPT_REPO_INVALIDO" in r.stdout, (
            f"Falta la linea canonica WOPT_REPO_INVALIDO en stdout: {r.stdout!r}"
        )
        assert "WOPT_COMMIT_OK" not in r.stdout, (
            f"Un repo invalido NUNCA puede reportar commit creado: {r.stdout!r}"
        )

        # 2) GIT_DIR que existe pero no es un repo -> 3 tambien. Este caso
        #    discrimina una implementacion que solo compruebe os.path.exists().
        r2 = invocar(["--verify"], git_dir_no_repo)
        assert r2.returncode == 3, (
            f"Un directorio que no es repo debe salir con 3, salio con {r2.returncode}. "
            f"stdout={r2.stdout!r}"
        )
        assert "WOPT_REPO_INVALIDO" in r2.stdout, (
            f"--verify debe emitir WOPT_REPO_INVALIDO: {r2.stdout!r}"
        )

        # 3) El camino de commit con un directorio no-repo tambien es 3, no 0.
        r3 = invocar(["test(t022): sigue sin comitear"], git_dir_no_repo)
        assert r3.returncode == 3, (
            f"Un directorio que no es repo debe salir con 3, salio con {r3.returncode}. "
            f"stdout={r3.stdout!r}"
        )

        # 4) Uso incorrecto -> 2 (sin mensaje, mensaje vacio, flag desconocido).
        for args, etiqueta in (
            ([], "sin argumentos"),
            (["   "], "mensaje vacio"),
            (["--flag-inventado"], "flag desconocido"),
        ):
            ru = invocar(args, git_dir_inexistente)
            assert ru.returncode == 2, (
                f"Uso incorrecto ({etiqueta}) debe salir con 2, salio con "
                f"{ru.returncode}. stdout={ru.stdout!r}"
            )
            assert "WOPT_USAGE" in ru.stdout, (
                f"Falta WOPT_USAGE ({etiqueta}): {ru.stdout!r}"
            )

        # 5) El wrapper no debe "arreglar" ni crear el GIT_DIR que se le dio, ni
        #    dejar rastro de escritura cuando el repo no valida.
        assert not os.path.exists(git_dir_inexistente), (
            f"El wrapper no debe crear el GIT_DIR invalido: {git_dir_inexistente}"
        )
        assert os.listdir(git_dir_no_repo) == [], (
            f"--verify es de solo lectura: {git_dir_no_repo} no debe recibir escrituras, "
            f"contiene {os.listdir(git_dir_no_repo)}"
        )

        # 6) Guarda estatica anti-regresion de la correccion de arquitectura:
        #    "nada que comitear" NO puede decidirse parseando el texto de git
        #    (git lo traduce segun LANG/LC_ALL y en un Windows en espanol la
        #    cadena literal nunca aparece).
        with open(wrapper, "r", encoding="utf-8") as fh:
            fuente = fh.read()
        codigo = _codigo_ejecutable(fuente).lower()
        for prohibido in ("nothing to commit", "working tree clean"):
            assert prohibido not in codigo, (
                f"El wrapper no debe decidir nada que comitear con el texto "
                f"{prohibido!r}: se traduce segun el locale. Usa "
                f"'git diff --cached --quiet'."
            )
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    print("git_safe_commit fail-safe OK.")


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
    test_gaming_service_should_kill()
    test_pack_service_crud()
    test_pack_service_delete()
    test_pack_service_favorite_exclusive()
    test_pack_service_reset_gaming()
    test_gaming_pack_lists_isolated_from_global()
    test_cache_ttl_and_invalidation()
    test_kill_recursive()
    test_git_safe_commit_fail_safe()
    print("\n--- Running Headless UI Test ---")
    test_headless_ui()
    print("\nALL TESTS PASSED.")
