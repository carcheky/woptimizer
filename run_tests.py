import sys
import os
import ast
import io
import time
import threading

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


# ---------------------------------------------------------------------------
# TASK-037 (ciclo 27) -- EL CONTRATO DE LOS LLAMANTES, con alcance DERIVADO.
#
# "Quien llama pasa la ACCION, nunca el verbo" es lo que promete el docstring
# de `ui/feedback._verbo`, y este guard es lo que lo hace cumplir. Vive a
# nivel de modulo, con RAIZ como parametro, por dos motivos que son el mismo:
#
#   * su alcance se DERIVA recorriendo el arbol con `ast`, porque lo que un
#     detector promete es "todo lo que hay", y para que eso sea cierto el
#     alcance tiene que salir de medir la realidad y no de una lista escrita a
#     mano (la lista de dos ficheros que llevaba era una apuesta con un
#     fichero mal: hay tres importadores);
#   * con la raiz como parametro, un test puede apuntarlo a un arbol temporal
#     con un CUARTO modulo, que es lo unico que distingue "derive el alcance"
#     de "escribi el alcance correcto a mano" (mutante M5).
# ---------------------------------------------------------------------------
FORMATEADORES_QUE_EXIGEN_ACCION = ("mensaje_sin_apps", "mensaje_banner_sin_apps")


def _raiz_del_paquete():
    """`<repo>/src/woptimizer`, la raiz desde la que se deriva el alcance."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "woptimizer")


def _importa_el_modulo_feedback(nodo):
    """True si el nodo de import trae el MODULO `feedback` al espacio de nombres.

    Las TRES formas que existen de traerlo, y que las tres ponen un
    formateador al alcance del modulo:

      * `from woptimizer.ui.feedback import mensaje_sin_apps` -> `ImportFrom`
        con `module` que acaba en `feedback` (tambien el relativo
        `from .feedback import ...`, donde `module == "feedback"`);
      * `from woptimizer.ui import feedback as fb` -> `ImportFrom` cuyo
        `module` NO acaba en `feedback` pero cuyo ALIAS se llama `feedback`;
      * `import woptimizer.ui.feedback as fb` -> nodo `Import` con el nombre
        cualificado.

    La segunda forma se encontro MIDiendo: el guard solo miraba `node.module`,
    asi que un modulo que importa el modulo entero -- que es la forma
    idiomatica de Python, y la que hace posibles las llamadas `fb.mensaje_...`
    que el guard tampoco veía -- quedaba FUERA del alcance. Dos ceguidas con
    la misma causa: mirar una sola forma de la escritura.
    """
    if isinstance(nodo, ast.ImportFrom):
        modulo = nodo.module or ""
        if modulo == "feedback" or modulo.endswith(".feedback"):
            return True
        return any(alias.name == "feedback" for alias in nodo.names)
    if isinstance(nodo, ast.Import):
        return any(
            alias.name == "feedback" or alias.name.endswith(".feedback")
            for alias in nodo.names
        )
    return False


def _modulos_que_importan_feedback(raiz_paquete):
    """DERIVADO con `ast`: los `.py` de `raiz_paquete` que importan `feedback`.

    Un modulo que NO importa `feedback` no puede llamar a sus formateadores,
    asi que la seleccion es total por construccion: no hay ningun fichero
    escrito a mano en ninguna parte de este guard. Un modulo con un error de
    sintaxis NO se salta en silencio: `ast.parse` propaga, porque un fichero
    que no se puede leer no es un fichero conforme.
    """
    encontrados = []
    for dirpath, dirs, files in os.walk(raiz_paquete):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for nombre in sorted(files):
            if not nombre.endswith(".py"):
                continue
            ruta = os.path.join(dirpath, nombre)
            with open(ruta, encoding="utf-8") as fh:
                arbol = ast.parse(fh.read(), filename=ruta)
            for nodo in ast.walk(arbol):
                if isinstance(nodo, (ast.Import, ast.ImportFrom)):
                    if _importa_el_modulo_feedback(nodo):
                        encontrados.append(ruta)
                        break
    return sorted(encontrados)


def _guardar_contrato_de_llamantes(raiz_paquete, acciones_validas):
    """Falla nombrando FICHERO y LINEA si un llamante cablea un verbo.

    Cubre las DOS formas de escribir la llamada, que antes eran una:

      * `mensaje_sin_apps(n, accion)` tras `from ... import`, que es un
        `ast.Name`;
      * `fb.mensaje_sin_apps(n, accion)` tras `import feedback as fb`, que es
        un `ast.Attribute`. Con `getattr(func, "id", None)` -- lo que habia --
        el nodo `ast.Attribute` no tiene `id`, salia `None` y la llamada se
        saltaba en silencio: un agujero LATENTE, la forma idiomatica de
        Python era invisible para el guard (mutante M6).
    """
    for ruta in _modulos_que_importan_feedback(raiz_paquete):
        assert os.path.isfile(ruta), (
            f"el alcance del guard apunta a un fichero que no existe: {ruta}. Un "
            "alcance que no se puede leer no es un alcance: es una apuesta, y una "
            "apuesta que se salta en silencio es peor que no tener guard"
        )
        with open(ruta, encoding="utf-8") as fh:
            arbol = ast.parse(fh.read(), filename=ruta)
        relativo = os.path.relpath(ruta, raiz_paquete)
        for llamada in ast.walk(arbol):
            if not isinstance(llamada, ast.Call):
                continue
            if isinstance(llamada.func, ast.Name):
                nombre = llamada.func.id
            elif isinstance(llamada.func, ast.Attribute):
                nombre = llamada.func.attr
            else:
                continue
            if nombre not in FORMATEADORES_QUE_EXIGEN_ACCION:
                continue
            arg = llamada.args[1] if len(llamada.args) > 1 else None
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                if arg.value not in acciones_validas:
                    raise AssertionError(
                        f"{relativo}:L{llamada.lineno} {nombre} recibe {arg.value!r}, que no "
                        f"es una ACCION (acciones: {sorted(acciones_validas)}). Quien llama "
                        "pasa la ACCION, nunca el verbo"
                    )
            elif isinstance(arg, ast.Attribute) and arg.attr == "default_action":
                pass
            else:
                raise AssertionError(
                    f"{relativo}:L{llamada.lineno} el segundo argumento de {nombre} no es ni "
                    "una ACCION literal ni `pack.default_action`, asi que el contrato del "
                    f"docstring no se puede comprobar: {arg!r}"
                )


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


def test_process_db_schema_integrity():
    """TASK-032 (S1): verifica la integridad de esquema de assets/process_db.json.

    Mata el mutante superviviente S1 de la auditoria de mutaciones:
    - Toda clave debe estar en minusculas y no terminar en '.exe'.
    - Todo valor debe ser un dict.
    - Campos obligatorios presentes y validos:
      * 'category': debe existir literalmente en PROCESS_CATEGORIES de config.py.
      * 'priority': debe ser uno de {"high", "medium", "low", "none"}.
      * 'description': debe ser str no vacio tras strip().
    """
    print("Testing process_db schema integrity...")
    import json
    from woptimizer.config import PROCESS_CATEGORIES

    valid_priorities = {"high", "medium", "low", "none"}
    db_path = os.path.join(os.path.dirname(__file__), "assets", "process_db.json")
    with open(db_path, "r", encoding="utf-8") as fh:
        db = json.load(fh)

    assert isinstance(db, dict), f"process_db.json raiz debe ser dict, recibido {type(db)}"
    assert len(db) > 0, "process_db.json no puede estar vacio"

    for key, meta in db.items():
        # Regla 1: clave normalizada
        assert key == key.lower(), f"Clave '{key}' debe estar en minusculas"
        assert not key.endswith(".exe"), f"Clave '{key}' no debe incluir extension .exe"

        # Regla 2: meta es dict
        assert isinstance(meta, dict), f"Valor de '{key}' debe ser dict, recibido {type(meta)}"

        # Regla 3: category obligatoria y alineada con config.py
        assert "category" in meta, f"Clave '{key}' carece del campo 'category'"
        assert meta["category"] in PROCESS_CATEGORIES, (
            f"Clave '{key}' tiene categoria invalida '{meta.get('category')}'; "
            f"debe ser una de {list(PROCESS_CATEGORIES.keys())}"
        )

        # Regla 4: priority obligatoria y valida
        assert "priority" in meta, f"Clave '{key}' carece del campo 'priority'"
        assert meta["priority"] in valid_priorities, (
            f"Clave '{key}' tiene prioridad invalida '{meta.get('priority')}'; "
            f"debe ser una de {valid_priorities}"
        )

        # Regla 5: description obligatoria, str y no vacia
        assert "description" in meta, f"Clave '{key}' carece del campo 'description'"
        assert isinstance(meta["description"], str) and len(meta["description"].strip()) > 0, (
            f"Clave '{key}' debe tener una 'description' de texto no vacia"
        )

    print(f"test_process_db_schema_integrity OK ({len(db)} procesos validados sin omisiones).")


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


def test_execute_gaming_pack_integration():
    """TASK-025 (FIX-002 + FIX-008): `execute_gaming_pack` es la puerta real del
    Gaming Mode y consulta de verdad `keepers` y `target_categories`.

    Tres capas, ninguna toca un proceso real del sistema por su nombre:
    - CAPA A: doble que captura la lista que llega a `kill_processes`. Discrimina
      de verdad: sin el fix la ruta sigue llamando a `kill_pack_apps`, la lista
      capturada esta vacia y `svchost` con su categoria roja marcada pasaria
      (el blacklist de NOMBRES no lo detiene: `is_system_protected('svchost')`
      es False). Eso es la via de brick que la barrera G-2 cierra.
    - CAPA B: integracion real contra la via de kill (patron de
      `test_kill_recursive`): el sleeper y su nieto deben morir.
    - Sub-chequeo estatico con `_codigo_ejecutable`: congela la separacion de
      capas, para que solo pueda dispararse por codigo EJECUTADO.
    """
    print("Testing execute_gaming_pack (integracion)...")
    from woptimizer.models import Pack, ProcessInfo
    from woptimizer.services.gaming_service import GamingService
    from woptimizer.services.process_service import ProcessService

    ROJO = "\U0001F534 Sistema de Windows"
    SYNC = "\U0001F7E2 Sincronización"
    CHAT = "\U0001F7E1 Chat y Comunicación"
    PROD = "\U0001F7E2 Productividad"
    OTROS = "⚪ Otros"
    AJENO = "woptimizer_zzz_inexistente.exe"

    class _ProcessServiceSpy(ProcessService):
        """Doble de ProcessService: snapshot fijo y captura de lo que llega a
        `kill_processes`. No mata nada del sistema."""

        def __init__(self):
            super().__init__()
            self.snapshot = []
            self.capturados = None
            self.force_refresh_pedido = None

        def get_running_processes(self, force_refresh=False):
            self.force_refresh_pedido = force_refresh
            return list(self.snapshot)

        def kill_processes(self, processes):
            self.capturados = list(processes)
            return 2, 0, 0, 12.5

    pack_s, tmp_path = _pack_service_temporal()
    try:
        spy = _ProcessServiceSpy()
        gs = GamingService(spy, pack_s)

        # ---------------- CAPA A: la lista que llega a la via de kill
        spy.snapshot = [
            # Categoria objetivo verde -> SI
            ProcessInfo(name="onedrive", full_name="onedrive.exe", pid=1001, category=SYNC),
            # Categoria objetivo Y keeper -> NO (gana el keeper, G-3)
            ProcessInfo(name="discord", full_name="discord.exe", pid=1002, category=CHAT),
            # Solo en apps explicitas -> SI
            ProcessInfo(name="chrome", full_name="chrome.exe", pid=1003, category=OTROS),
            # No aparece en ninguna configuracion -> NO
            ProcessInfo(name="woptimizer_zzz_inexistente", full_name=AJENO, pid=1004, category=OTROS),
            # Categoria roja MARCADA como objetivo -> NO (barrera G-2)
            ProcessInfo(name="svchost", full_name="svchost.exe", pid=1005, category=ROJO),
            # DB envenenada (verde) con nombre irrompible -> NO (blindaje G-4)
            ProcessInfo(name="lsass", full_name="lsass.exe", pid=1006, category=PROD),
        ]
        pack = Pack(
            id="gaming_test",
            name="Gaming de prueba",
            is_gaming=True,
            default_action="kill",
            apps=["chrome.exe"],
            keepers=["discord.exe"],
            target_categories=[SYNC, CHAT, ROJO, PROD],
        )

        # Precondiciones: si el entorno no cumple, el test no discriminaria nada.
        assert spy.is_system_protected("svchost") is False, (
            "Precondicion rota: si svchost estuviera en el blacklist de nombres "
            "este test ya no distinguiria la barrera de categoria G-2"
        )
        assert spy.is_system_protected("lsass") is True, (
            "Precondicion rota: el blindaje de nombres de TASK-024 debe seguir en pie"
        )
        assert spy._categorize("onedrive.exe") == SYNC, (
            "Precondicion rota: onedrive debe caer en la categoria objetivo"
        )
        assert spy._categorize("discord.exe") == CHAT, (
            "Precondicion rota: la categoria de discord debe ser objetivo para "
            "que el test pruebe la precedencia del keeper"
        )
        assert spy._categorize(AJENO) not in pack.target_categories, (
            f"Precondicion rota: el proceso ajeno cayo en {spy._categorize(AJENO)!r}"
        )

        resultado = gs.execute_gaming_pack(pack)

        assert spy.capturados is not None, (
            "execute_gaming_pack no llego a kill_processes: sin el fix la ruta "
            "sigue llamando a kill_pack_apps y la lista capturada esta vacia"
        )
        nombres = sorted(p.full_name for p in spy.capturados)
        assert nombres == ["chrome.exe", "onedrive.exe"], (
            f"Solo deben llegar onedrive (categoria objetivo) y chrome (app "
            f"explicita). Llegaron: {nombres}"
        )
        assert "svchost.exe" not in nombres, (
            "svchost con su categoria roja marcada como objetivo NUNCA debe "
            "llegar a kill_processes: sin la barrera G-2 mataria todos los "
            "svchost.exe y dejaria Windows inservible"
        )
        assert "discord.exe" not in nombres, (
            "El keeper gana aunque su categoria sea objetivo: se evalua con la "
            "extension (`full_name`), no con `name` a secas"
        )
        assert "lsass.exe" not in nombres, (
            "Un nombre irrompible no se mata aunque la DB lo pinte como verde"
        )
        assert AJENO not in nombres, "Un proceso no relacionado no debe matarse"
        assert spy.force_refresh_pedido is True, (
            "G0 es obligatorio: sin force_refresh=True la cache TTL de 2 s puede "
            "dejar fuera lo que el usuario acaba de lanzar"
        )

        killed, failed, skipped, freed_mb = resultado
        assert len(resultado) == 4, f"Se espera una 4-tupla, obtenido {resultado}"
        assert (killed, failed, freed_mb) == (2, 0, 12.5), (
            f"La 4-tupla de kill_processes debe volver sin alterar: {resultado}"
        )
        assert isinstance(freed_mb, float), f"freed_mb debe ser float: {type(freed_mb)}"
        assert skipped == 2, (
            f"skipped debe sumar los descartes del filtro (svchost y lsass): {skipped}"
        )

        # Uso indebido: este metodo es solo del Gaming Mode (spec 4.1).
        try:
            gs.execute_gaming_pack(Pack(id="usuario", name="Pack de usuario", apps=["chrome.exe"]))
        except ValueError:
            pass
        else:
            assert False, "un pack con is_gaming=False debe lanzar ValueError"

        # ---------------- CAPA B: integracion real contra la via de kill
        def _capa_b():
            import psutil
            import subprocess
            import sys as _sys
            import tempfile

            class _SnapshotFijo(ProcessService):
                """El snapshot real incluiria al propio runner (python.exe), asi
                que se fija a un unico objetivo con marca propia."""

                def __init__(self, snap):
                    super().__init__()
                    self.snap = snap

                def get_running_processes(self, force_refresh=False):
                    return list(self.snap)

            pidfile = tempfile.NamedTemporaryFile(suffix=".pid", delete=False, mode='w', encoding='utf-8')
            pidfile.write("")
            pidfile.close()

            marca = "woptimizer_t025_padre.exe"
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
                # Guarda contra falsos positivos: el objetivo debe ser el nieto Python.
                try:
                    cmdline = psutil.Process(child_pid).cmdline()
                except psutil.Error:
                    cmdline = []
                assert any("python" in str(arg).lower() for arg in cmdline), (
                    f"El PID capturado ({child_pid}) no es el nieto Python esperado: {cmdline}"
                )

                pinfo = ProcessInfo(name=marca.replace('.exe', ''), full_name=marca, pid=parent_proc.pid)
                gs_b = GamingService(_SnapshotFijo([pinfo]), pack_s)
                pack_b = Pack(
                    id="gaming",
                    name="Gaming de integracion",
                    is_gaming=True,
                    default_action="kill",
                    apps=[marca],
                )
                killed, failed, skipped, freed_mb = gs_b.execute_gaming_pack(pack_b)

                if killed == 0 and failed > 0:
                    print("  AVISO: kill protegido por permisos (AccessDenied). Test degradado.")
                    return

                assert killed == 1, (
                    f"Se esperaba 1 proceso muerto; killed={killed} failed={failed} skipped={skipped}"
                )
                assert skipped == 0, (
                    f"El objetivo propio no deberia contar como protegido: skipped={skipped}"
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

        _capa_b()

        # ---------------- Sub-chequeo estatico: congelacion de capas
        root = os.path.dirname(os.path.abspath(__file__))
        ruta_servicio = os.path.join(root, "src", "woptimizer", "services", "gaming_service.py")
        with open(ruta_servicio, "r", encoding="utf-8") as fh:
            cod_servicio = _codigo_ejecutable(fh.read()).lower()
        assert "psutil" not in cod_servicio, (
            "G-1: execute_gaming_pack no puede abrir una via propia al sistema; "
            "debe delegar integro en kill_processes"
        )
        assert "import json" not in cod_servicio, (
            "La capa de servicios no lee el JSON de packs directamente"
        )

        for relativo in (
            os.path.join("ui", "app.py"),
            os.path.join("ui", "main_window.py"),
            os.path.join("ui", "confirmation.py"),
            os.path.join("ui", "views", "dashboard_view.py"),
            os.path.join("ui", "views", "pack_manager_view.py"),
            os.path.join("ui", "views", "process_manager_view.py"),
        ):
            with open(os.path.join(root, "src", "woptimizer", relativo), "r", encoding="utf-8") as fh:
                cod_ui = _codigo_ejecutable(fh.read()).lower()
            assert "psutil" not in cod_ui, (
                f"Separacion de capas: la UI no puede tocar el sistema operativo ({relativo})"
            )
            assert "import json" not in cod_ui, (
                f"Separacion de capas: la UI no puede leer el JSON ({relativo})"
            )
    finally:
        os.unlink(tmp_path)
    print("execute_gaming_pack (integracion) OK.")


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


def test_pack_service_favorites_acumulan():
    """TASK-048: set_favorite es acumulativo y no desmarca otros packs."""
    print("Testing PackService favoritos acumulativos...")
    pack_s, tmp_path = _pack_service_temporal()
    try:
        for pack_id in ("a", "b", "c"):
            assert pack_s.create_user_pack(pack_id, pack_id.upper(), []) is True

        def favoritos():
            return sorted(k for k, v in pack_s.get_all_packs().items() if v.is_favorite and k in ("a", "b", "c"))

        # Marcar 'a' como favorito
        pack_s.set_favorite("a", True)
        assert favoritos() == ["a"], f"Esperaba solo 'a' como favorito, hay {favoritos()}"

        # Marcar 'c' como favorito: debe acumularse con 'a', NO desmarcarlo
        pack_s.set_favorite("c", True)
        assert favoritos() == ["a", "c"], f"Esperaba ['a', 'c'] acumulados, hay {favoritos()}"

        # Desmarcar 'a': 'c' sigue siendo favorito y 'b' permanece False
        pack_s.set_favorite("a", False)
        assert favoritos() == ["c"], f"Esperaba ['c'], hay {favoritos()}"
        assert pack_s.get_all_packs()["b"].is_favorite is False
    finally:
        os.unlink(tmp_path)
    print("PackService favoritos acumulativos OK.")


def test_pack_service_favorite_contracts_and_resilience():
    """TASK-048: validación de None en set_favorite, toggle_favorite, blindaje gaming y guard ast."""
    print("Testing PackService favorite contracts and resilience...")
    import ast
    from pathlib import Path
    from woptimizer.services.pack_service import PackService

    # 1. Guard AST: get_favorite_pack no debe aparecer en ningún fichero de src/woptimizer/**
    src_dir = Path(__file__).resolve().parent / "src" / "woptimizer"
    for py_file in src_dir.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "get_favorite_pack":
                raise AssertionError(f"Función obsoleta get_favorite_pack() encontrada en {py_file.name}:{node.lineno}")
            if isinstance(node, ast.Attribute) and node.attr == "get_favorite_pack":
                raise AssertionError(f"Llamada a get_favorite_pack encontrada en {py_file.name}:{node.lineno}")

    pack_s, tmp_path = _pack_service_temporal()
    try:
        # 2. set_favorite(None, ...) y set_favorite("", ...) deben lanzar ValueError
        try:
            pack_s.set_favorite(None, True)
            raise AssertionError("set_favorite(None, True) debió lanzar ValueError")
        except ValueError:
            pass

        try:
            pack_s.set_favorite("", True)
            raise AssertionError("set_favorite('', True) debió lanzar ValueError")
        except ValueError:
            pass

        # 3. toggle_favorite sobre PackService real: alterna True/False/True y persiste en disco
        assert pack_s.create_user_pack("custom", "Custom Pack", []) is True
        assert pack_s.get_all_packs()["custom"].is_favorite is False

        # Toggle 1 -> True
        nuevo_1 = pack_s.toggle_favorite("custom")
        assert nuevo_1 is True, f"Esperaba True tras primer toggle, obtuvo {nuevo_1}"
        assert pack_s.get_all_packs()["custom"].is_favorite is True
        s_disco1 = PackService(tmp_path)
        assert s_disco1.get_all_packs()["custom"].is_favorite is True

        # Toggle 2 -> False
        nuevo_2 = pack_s.toggle_favorite("custom")
        assert nuevo_2 is False, f"Esperaba False tras segundo toggle, obtuvo {nuevo_2}"
        assert pack_s.get_all_packs()["custom"].is_favorite is False
        s_disco2 = PackService(tmp_path)
        assert s_disco2.get_all_packs()["custom"].is_favorite is False

        # Toggle 3 -> True
        nuevo_3 = pack_s.toggle_favorite("custom")
        assert nuevo_3 is True
        assert pack_s.get_all_packs()["custom"].is_favorite is True

        # 4. El pack gaming no puede quedarse sin favorito tras recargar (_ensure_gaming_pack)
        pack_s.set_favorite("gaming", False)
        assert pack_s.get_all_packs()["gaming"].is_favorite is False
        pack_s.save()

        # Al recargar, _ensure_gaming_pack restaura is_favorite=True en gaming
        s_reloaded = PackService(tmp_path)
        assert s_reloaded.get_all_packs()["gaming"].is_favorite is True, (
            "_ensure_gaming_pack debe restaurar is_favorite=True en pack gaming existente"
        )
    finally:
        os.unlink(tmp_path)
    print("PackService favorite contracts and resilience OK.")


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


class _FakeScheduler:
    """Doble de `TkScheduler`: guarda los jobs y dispara el auto-reset sin ventana.

    Es lo que hace testeable la maquina de estados: sin root de Tk, sin `after` real y
    sin esperar 3 s. `fire_due(ms)` hace avanzar el reloj.
    """

    def __init__(self):
        self.jobs = []          # [{"id", "delay", "cb", "cancelled"}]
        self._contador = 0

    def schedule(self, delay_ms, callback):
        self._contador += 1
        handle = f"job{self._contador}"
        self.jobs.append({"id": handle, "delay": delay_ms, "cb": callback, "cancelled": False})
        return handle

    def cancel(self, handle):
        for job in self.jobs:
            if job["id"] == handle:
                job["cancelled"] = True
                return
        raise AssertionError(f"Se cancelo un handle que no existe: {handle!r}")

    def vivos(self):
        return [j for j in self.jobs if not j["cancelled"]]

    def fire_due(self, elapsed_ms):
        """Dispara los jobs de un solo disparo cuyo plazo ya vencio. Devuelve sus ids."""
        vencidos = [j for j in self.jobs if not j["cancelled"] and j["delay"] <= elapsed_ms]
        for job in vencidos:
            job["cancelled"] = True
        for job in vencidos:
            job["cb"]()
        return [j["id"] for j in vencidos]


def test_double_tap_guard():
    """TASK-023: `DoubleTapGuard` exige una segunda pulsacion para ejecutar.

    Sin esto, las 5 acciones destructivas de la v3 matan apps con un solo clic (la
    regresion que elimino el patron `_request_confirm` de la v2). El test discrimina:
    si alguien borra o neutraliza `arm` / `consume` / el auto-reset, falla.
    """
    print("Testing DoubleTapGuard (doble pulsacion, headless)...")
    from woptimizer.ui.confirmation import (
        AMBAR,
        PENDIENTE_FG,
        PENDIENTE_HOVER,
        PENDIENTE_TEXT,
        VENTANA_MS,
        VENTANA_MS_PORTADA,
        Confirmable,
        DoubleTapGuard,
    )

    assert PENDIENTE_TEXT == "⚠️ ¿SEGURO? PULSA OTRA VEZ", (
        f"El estado pendiente debe ser compartido por las 5 acciones: {PENDIENTE_TEXT!r}"
    )
    assert (PENDIENTE_FG, PENDIENTE_HOVER) == ("#b8860b", "#8a6508")
    assert AMBAR == "#b8860b"
    assert VENTANA_MS == 3000 and VENTANA_MS_PORTADA == 2000
    assert Confirmable.__init__ is object.__init__, (
        "El mixin no puede definir __init__: romperia el cooperative __init__ de las vistas"
    )

    # 1) Primera pulsacion arma, la segunda ejecuta.
    sched = _FakeScheduler()
    expiradas = []
    guard = DoubleTapGuard(scheduler=sched, window_ms=VENTANA_MS)
    assert guard.arm("pack_kill:abc", "⚠️ Segunda pulsación para apagar 3 apps de 'Gaming'.",
                     on_expire=lambda: expiradas.append("expirada")) is True, (
        "La primera pulsacion debe armar la pendiente"
    )
    assert guard.is_pending() is True
    assert guard.is_pending("pack_kill:abc") is True
    assert guard.arm("pack_kill:abc", "otra vez") is False, (
        "Un segundo arm() del mismo token sin consumir NO debe re-armar: eso seria "
        "confirmar sin la segunda pulsacion del usuario"
    )
    assert len(sched.vivos()) == 1, "Solo puede haber una ventana viva"
    assert guard.consume("pack_kill:abc") is not None, (
        "La segunda pulsacion debe confirmar y devolver el label"
    )
    assert guard.is_pending() is False
    assert sched.vivos() == [], "Confirmar debe cancelar el after de la ventana"
    assert guard.consume("pack_kill:abc") is None, "La tercera pulsacion no ejecuta nada"
    assert expiradas == [], "Confirmar no es expirar"

    # 2) Auto-revert: la ventana expira sola y ejecuta el on_expire.
    sched = _FakeScheduler()
    expiradas = []
    guard = DoubleTapGuard(scheduler=sched, window_ms=VENTANA_MS)
    guard.arm("a", "x", on_expire=lambda: expiradas.append("expirada"))
    assert sched.fire_due(2999) == [], "La ventana no puede expirar antes de tiempo"
    assert guard.is_pending() is True
    assert sched.fire_due(3000) == ["job1"], "A los 3000 ms debe dispararse el reset"
    assert guard.is_pending() is False, "Tras expirar el guard queda limpio"
    assert expiradas == ["expirada"], "La expiracion debe avisar a la vista"
    assert guard.consume("a") is None, "Expirada la ventana, la pulsacion ya no confirma"

    # 3) Cambiar la intencion entre pulsaciones invalida (y no ejecuta con la vieja).
    sched = _FakeScheduler()
    guard = DoubleTapGuard(scheduler=sched)
    vieja = ("chrome.exe", "steam.exe")
    nueva = ("chrome.exe", "discord.exe")
    guard.arm(vieja, "⚠️ Segunda pulsación para cerrar 2 apps seleccionadas.")
    assert guard.consume(nueva) is None, "Con la seleccion cambiada NO se puede confirmar"
    assert guard.is_pending() is False, "La pendiente vieja se descarta, no se arrastra"
    assert sched.vivos() == []
    # Y la nueva intencion se arma de cero, con su propia ventana.
    assert guard.arm(nueva, "otra") is True
    assert guard.is_pending(nueva) is True

    # 4) destroy() mata el after vivo (si no, sobrevive al cambio de pestaña).
    sched = _FakeScheduler()
    guard = DoubleTapGuard(scheduler=sched)
    guard.arm("dashboard:xyz", "x")
    assert len(sched.vivos()) == 1
    guard.cancel_on_destroy()
    assert sched.vivos() == [], "cancel_on_destroy debe dejar el scheduler sin jobs"
    assert guard.is_pending() is False

    # 5) Frontera de capas: el helper no puede tocar el SO ni el JSON.
    root = os.path.dirname(os.path.abspath(__file__))
    helper = os.path.join(root, "src", "woptimizer", "ui", "confirmation.py")
    assert os.path.exists(helper), f"No se encuentra el helper: {helper}"
    with open(helper, "r", encoding="utf-8") as fh:
        arbol = ast.parse(fh.read(), filename=helper)
    importados = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            importados.update(a.name.split(".")[0] for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            importados.add(nodo.module.split(".")[0])
    prohibido = importados & {"psutil", "json", "subprocess", "services", "models", "woptimizer",
                              "customtkinter", "tkinter"}
    assert not prohibido, (
        f"ui/confirmation.py viola la frontera de capas: importa {sorted(prohibido)}. "
        f"La maquina de estado tiene que importarse sin Tk."
    )
    assert "typing" in importados, "Se esperaba al menos el import de typing"
    print("DoubleTapGuard OK.")


def test_no_system_process_is_killable():
    """TASK-024: los procesos de nivel sistema NUNCA pueden ofrecerse como cerrables.

    Es la mitad Critica de este ciclo: matarlos deja el Windows del usuario
    inservible. El test falla si (a) alguien mete un nombre de la Familia A en
    `assets/process_db.json` con una prioridad != 'none' o sin semaforo rojo, o
    (b) el blindaje del servicio deja de forzar rojo/none aunque el JSON este
    envenenado a proposito.
    """
    print("Testing blindaje anti-brick (procesos de sistema)...")
    import json
    import shutil
    import tempfile
    import woptimizer.config as wopt_config
    from woptimizer.config import CATEGORY_ORDER
    from woptimizer.services.process_service import (
        SYSTEM_PROTECTED_PROCESSES,
        ProcessService,
    )

    rojo = "\U0001F534"

    # 1) El conjunto de proteccion tiene que cubrir el nucleo duro. Si alguien
    #    lo reduce, este test lo dice aunque el JSON este impecable.
    nucleo = {
        "csrss", "lsass", "winlogon", "wininit", "services", "smss",
        "dwm", "system", "system idle process", "registry", "memcompression",
        "fontdrvhost", "ctfmon", "spoolsv", "sihost", "conhost", "dllhost",
        "runtimebroker", "searchhost", "searchindexer", "audiodg", "wudfsvc",
        "securityhealthsystray", "textinputhost", "systemsettings",
        "shellexperiencehost", "startmenuexperiencehost", "taskhostw",
    }
    faltan = nucleo - SYSTEM_PROTECTED_PROCESSES
    assert not faltan, (
        f"El blindaje anti-brick no cubre estos procesos criticos: {sorted(faltan)}"
    )

    # 2) El JSON real no puede ofrecer ninguno de ellos como cerrable. Incluye
    #    tambien los que ya estaban como 🔴 (svchost, explorer) para que nadie
    #    los degraden a verde.
    with open("assets/process_db.json", encoding="utf-8") as fh:
        db = json.load(fh)
    assert isinstance(db, dict), "El esquema del JSON debe seguir siendo dict[str, dict]"
    assert all(isinstance(v, dict) for v in db.values()), "Cada entrada debe ser un dict"

    vigilados = {k.lower() for k in db} & (SYSTEM_PROTECTED_PROCESSES | {"svchost", "explorer"})
    closables = [
        k for k, v in db.items()
        if k.lower() in (SYSTEM_PROTECTED_PROCESSES | {"svchost", "explorer"})
        and v.get("priority") != "none"
    ]
    assert not closables, (
        f"Procesos de nivel sistema registrados como cerrables en el JSON: {closables}. "
        "Ninguno de ellos puede tener prioridad distinta de 'none'."
    )
    sin_rojo = [k for k, v in db.items() if k.lower() in vigilados and rojo not in (v.get("category") or "")]
    assert not sin_rojo, (
        f"Procesos de nivel sistema sin semaforo 🔴 en el JSON: {sin_rojo}"
    )

    # 3) El blindaje del servicio: con el JSON ENVENENADO a proposito (lsass y
    #    winlogon como si fueran bloatware verde), el servicio los sigue
    #    forzando a rojo/none, con extension, en mayusculas y por subcadena.
    tmp = tempfile.mkdtemp(prefix="wopt_t024_")
    _dir_data_original = wopt_config._data_dir
    try:
        os.makedirs(os.path.join(tmp, "assets"))
        envenenado = {
            "lsass": {"category": "\U0001F7E2 Productividad", "priority": "high",
                      "description": "ENTRADA ENVENENADA"},
            "winlogon": {"category": "\U0001F7E2 Productividad", "priority": "high",
                         "description": "ENTRADA ENVENENADA"},
        }
        with open(os.path.join(tmp, "assets", "process_db.json"), "w", encoding="utf-8") as fh:
            json.dump(envenenado, fh, indent=4, ensure_ascii=False)

        wopt_config._data_dir = lambda: tmp
        ps_envenenado = ProcessService()
        assert ps_envenenado.is_db_loaded, "El servicio debe cargar el JSON de prueba"

        # 3a) Saneado en la carga: el mapa ya no contiene la entrada verde.
        for clave in ("lsass", "winlogon"):
            cat, prio, _ = ps_envenenado._db_map[clave]
            assert prio == "none", f"{clave} quedo con prioridad {prio!r} tras la carga"
            assert rojo in cat, f"{clave} quedo con categoria {cat!r} tras la carga"

        # 3b) Resolucion de metadatos por las tres vias de entrada.
        for variante in ("lsass", "lsass.exe", "Lsass.EXE", " winlogon.exe "):
            cat, prio, _ = ps_envenenado._get_process_meta(variante)
            assert prio == "none", f"{variante!r} -> prioridad {prio!r}"
            assert rojo in cat, f"{variante!r} -> categoria {cat!r}"

        # 3c) Tambien para el resto de la Familia A, aunque no este en el JSON.
        for nombre in sorted(SYSTEM_PROTECTED_PROCESSES):
            cat, prio, _ = ps_envenenado._get_process_meta(f"{nombre}.exe")
            assert prio == "none", f"{nombre}.exe -> prioridad {prio!r}"
            assert rojo in cat, f"{nombre}.exe -> categoria {cat!r}"
            assert ProcessService.is_system_protected(nombre) is True, (
                f"is_system_protected({nombre!r}) deberia ser True"
            )

        # 3d) El kill por pack respeta el blindaje: nunca toca un PID de sistema.
        wopt_config._data_dir = _dir_data_original
        k, f, s, mb = ProcessService().kill_pack_apps(["lsass.exe", "winlogon.exe"])
        assert (k, f) == (0, 0), f"kill_pack_apps intento matar un proceso de sistema: {k, f}"
        assert s == 2, f"Los dos procesos de sistema deberian contar como omitidos, s={s}"
        assert mb == 0.0, f"No se debe liberar memoria de un kill que no ocurrio: {mb}"

        # Un nombre legitimo sigue siendo normal (guarda contra un blindaje
        # tan ancho que bloquee el producto entero).
        assert ProcessService.is_system_protected("powertoys.exe") is False, (
            "powertoys no es un proceso de sistema: el blindaje seria demasiado ancho"
        )
        assert ProcessService.is_system_protected("dsaservice.exe") is False
    finally:
        wopt_config._data_dir = _dir_data_original
        shutil.rmtree(tmp, ignore_errors=True)

    # 4) Con la DB real, el bloatware nuevo es verde de verdad.
    ps_real = ProcessService()
    for nombre, prio_esperado in (("powertoys.exe", "high"),
                                  ("unigetui.exe", "high"),
                                  ("language_server.exe", "high"),
                                  ("atkexcomsvc.exe", "medium"),
                                  ("armourycrate.exe", "none"),
                                  ("mpdefendercoreservice.exe", "none")):
        cat, prio, _ = ps_real._get_process_meta(nombre)
        assert prio == prio_esperado, f"{nombre} -> prioridad {prio!r}, esperaba {prio_esperado!r}"
        # TASK-026 (FIX-005): se compara contra el centinela VIVO de config.py,
        # no contra el literal ASCII "? Otros". Con ese literal la comparacion
        # era tautologica (comparaba contra un texto que ya no existia en el
        # codigo) y el test pasaba sin comprobar nada.
        assert cat != CATEGORY_ORDER[-1], (
            f"{nombre} ha caido en la categoria centinela: revisa la clave del JSON"
        )
    print("Blindaje anti-brick OK.")


# ===========================================================================
# TASK-026 - Integridad de datos, copia profunda y resiliencia de servicios.
# Cuatro tests discriminantes: cada uno FALLA sin su fix.
#   FIX-001  test_gaming_pack_fallback_is_deep_copy
#   FIX-005  test_default_meta_matches_canonical_otros
#   FIX-007  test_do_load_publica_sin_tk  (P8, reescrito sin Tk en TASK-030)
#   FIX-009  test_pack_service_backup_and_recovery
# ===========================================================================

# El centinela canonico se construye por codepoint, nunca pegando el glifo: asi
# el propio test no depende de que el editor haya escrito bien el emoji
# (familia de bug del ciclo #9). U+26AA es WHITE CIRCLE, no el ASCII '?' (U+003F).
CENTINELA_OTROS = chr(0x26AA) + " Otros"
CENTINELA_ASCII = "? Otros"


class _RecordingDict(dict):
    """dict que graba (hilo, operacion) en cada mutacion y puede quedarse PARADA.

    Dos usos en el test de FIX-007 (P8, `test_do_load_publica_sin_tk`):
      * demostrar que NINGUNA mutacion llega del hilo secundario;
      * que la mutacion IN SITU sea observable aunque la vista no tenga ventana.
      * reproducible sin azar el "dictionary changed size during iteration":
        la primera mutacion se queda bloqueada hasta que el hilo principal
        tenga el iterador abierto, y sigue cuando el lector sigue avanzando.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ops = []
        self.en_mutacion = threading.Event()   # el hilo secundario entro a mutar
        self.desbloquear = threading.Event()   # el hilo principal lo deja seguir
        self.tras_insertar = threading.Event() # ya metio una clave nueva
        self.bloquear = False

    def _op(self, op):
        self.ops.append((threading.get_ident(), op))
        if self.bloquear:
            self.en_mutacion.set()
            self.desbloquear.wait(20)
            self.bloquear = False

    def clear(self):
        self._op("clear")
        super().clear()

    def __setitem__(self, key, value):
        self._op("setitem")
        super().__setitem__(key, value)
        self.tras_insertar.set()

    def __delitem__(self, key):
        self._op("delitem")
        super().__delitem__(key)


def test_do_load_publica_sin_tk():
    """TASK-030 / P8: el invariante de FIX-007 con un arnés SIN Tk.

    Por que sin ventana: el test anterior montaba un `ctk.CTk()` de verdad y
    por eso necesitaba `faulthandler.dump_traceback_later(150, exit=True)`,
    porque un bloqueo ocurre DENTRO de Tcl, donde ningun timeout de Python
    sirve. Ese `exit=True` mataba el runner entero (y con el todos los tests
    posteriores) y costs 150 s de suite colgada en cada regresion. Aqui no hay
    `CTk`, ni `root`, ni `mainloop`, ni Tcl: NO EXISTE RUTA por la que Tcl
    pueda colgarse, asi que el reloj de guardia sobra y se ha eliminado.

    Como se comprueba lo mismo sin ventana:
      * la vista se construye con `__new__` sobre una subclase en la que
        `processes` y `grouped_processes` son PROPIEDADES que anotan
        `threading.get_ident()`: cada escritura deja escrito de que hilo salio,
        sin cronometrar nada;
      * el `after` de la vista ENCOLA el callback y el TEST hace de bucle de
        eventos: abre las puertas, hace `join(10)` al hilo secundario y ejecuta
        en el principal lo que el secundario entrego;
      * el getter de `grouped_processes` devuelve una `_RecordingDict`, asi que
        una mutacion IN SITU (`.clear()`, `[k] = []`) tambien queda con su hilo.

    MATA: que el secundario vuelva a publicar el estado, o a mutarlo in situ.
    Con el bug, `escrituras` queda con el hilo secundario y el mensaje lo dice.
    Se conservan las dos cargas solapadas (fase B), la puerta por `Event` sin
    `sleep`, el camino de crash (fase C) y la guarda `ast` (fase D, prohibe
    `self.master.after`, TASK-023).
    """
    print("Testing _do_load publica desde el principal, sin Tk (FIX-007/P8)...")
    import collections
    from woptimizer.models import Pack, ProcessInfo
    from woptimizer.ui.views import process_manager_view as pmv_mod
    from woptimizer.ui.views.process_manager_view import ProcessManagerView

    # --- D) guarda estatica, PRIMERO y sin Tk -----------------------------
    # Va antes que las fases A/B/C a proposito: si alguien reintroduce la
    # mutacion desde el hilo secundario, el fallo tiene que ser un mensaje
    # limpio e instantaneo. Sigue siendo una comprobacion DISTINTA de las de
    # abajo: prohibe `self.master.after` (TASK-023) y prohibe publicar fuera de
    # un `self.after(0, ...)`. Ahora es una red, no la unica.
    ruta = os.path.join("src", "woptimizer", "ui", "views", "process_manager_view.py")
    with open(ruta, encoding="utf-8") as fh:
        arbol = ast.parse(fh.read())

    for nodo in ast.walk(arbol):
        if (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)
                and nodo.func.attr == "after"
                and isinstance(nodo.func.value, ast.Attribute)
                and nodo.func.value.attr == "master"):
            raise AssertionError(
                f"{ruta}:{nodo.lineno} usa self.master.after; debe ser self.after "
                "(TASK-023: el master sobrevive a la destruccion de la vista)"
            )

    publicadores = set()
    for nodo in ast.walk(arbol):
        if (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)
                and nodo.func.attr == "after"
                and isinstance(nodo.func.value, ast.Name)
                and nodo.func.value.id == "self"
                and nodo.args and isinstance(nodo.args[0], ast.Constant)
                and nodo.args[0].value == 0
                and len(nodo.args) >= 2):
            # TASK-035 iter 3: el destino puede ser un `def` anidado (nombre) o un
            # metodo de la vista ligado por atributo (`self._apply_load`). Lo que
            # se exige es lo mismo en los dos casos: que se publique por
            # `self.after(0, ...)` y no escribiendo el estado desde el secundario.
            destino = nodo.args[1]
            if isinstance(destino, ast.Name):
                publicadores.add(destino.id)
            elif isinstance(destino, ast.Attribute) and isinstance(destino.value, ast.Name) \
                    and destino.value.id == "self":
                publicadores.add(destino.attr)
    assert publicadores, "no hay ninguna funcion destino de self.after(0, ...)"

    padres = {}
    for padre in ast.walk(arbol):
        for hijo in ast.iter_child_nodes(padre):
            padres[hijo] = padre

    def _cadena(nodo):
        cadena = []
        cur = nodo
        while cur in padres:
            cur = padres[cur]
            if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
                cadena.append(cur.name)
        return cadena

    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Assign):
            objetivos = nodo.targets
        elif isinstance(nodo, (ast.AugAssign, ast.AnnAssign)):
            objetivos = [nodo.target]
        else:
            objetivos = []
        for t in objetivos:
            if (isinstance(t, ast.Attribute) and t.attr in ("processes", "grouped_processes")
                    and isinstance(t.value, ast.Name) and t.value.id == "self"):
                cadena = _cadena(nodo)
                if cadena == ["__init__"]:
                    continue
                assert publicadores.intersection(cadena), (
                    f"{ruta}:{nodo.lineno} asigna self.{t.attr} dentro de {cadena}, "
                    f"que no es destino de ningun self.after(0, ...); el estado de "
                    "una vista solo se publica desde el hilo principal"
                )

    for nodo in ast.walk(arbol):
        if (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)
                and nodo.func.attr in ("clear", "update", "pop", "popitem")
                and isinstance(nodo.func.value, ast.Attribute)
                and nodo.func.value.attr in ("processes", "grouped_processes")
                and isinstance(nodo.func.value.value, ast.Name)
                and nodo.func.value.value.id == "self"):
            raise AssertionError(
                f"{ruta}:{nodo.lineno} muta self.{nodo.func.value.attr} in situ; "
                "el hilo secundario no puede tocar un dict que itera el principal"
            )

    # --- dobles de prueba: control determinista del entrelazado ------------
    class _FakeProcService:
        """Doble de ProcessService con una puerta por llamada.

        `cogido[i]` lo pone el hilo cuando ya tiene su snapshot; si el indice
        esta en `bloquear`, espera a que el principal le de paso en
        `continuar[i]`. Sin sleep en ningun sitio.
        """
        is_db_loaded = True

        def __init__(self, snapshots):
            self._snaps = [list(s) for s in snapshots]
            self._i = 0
            self._lock = threading.Lock()
            self.cogido = [threading.Event() for _ in self._snaps]
            self.continuar = [threading.Event() for _ in self._snaps]
            self.bloquear = set()

        def get_running_processes(self):
            with self._lock:
                i = self._i
                self._i += 1
            snap = list(self._snaps[i])
            self.cogido[i].set()
            if i in self.bloquear:
                self.continuar[i].wait(20)
            return snap

    class _FakePackService:
        def get_all_packs(self):
            return {"gaming": Pack(id="gaming", name="Gaming", is_gaming=True)}

    class _VistaSinTk(ProcessManagerView):
        """`processes` y `grouped_processes` como PROPIEDADES que anotan el hilo.

        `__new__` no ejecuta `CTkFrame.__init__`: no hay root ni widgets. Las
        escrituras se guardan como (atributo, hilo) y el agrupado se guarda
        como una `_RecordingDict`, de modo que una mutacion in situ tambien
        queda con el hilo que la hizo.
        """
        @property
        def processes(self):
            return self._procesos

        @processes.setter
        def processes(self, valor):
            self.escrituras.append(("processes", threading.get_ident()))
            self._procesos = list(valor)

        @property
        def grouped_processes(self):
            return self._agrupado

        @grouped_processes.setter
        def grouped_processes(self, valor):
            self.escrituras.append(("grouped_processes", threading.get_ident()))
            self._agrupado = _RecordingDict(valor)

    p1 = ProcessInfo(name="fake_one", full_name="fake_one.exe", pid=101,
                     category=CENTINELA_OTROS)
    p2 = ProcessInfo(name="fake_two", full_name="fake_two.exe", pid=102,
                     category=CENTINELA_OTROS)
    q1 = ProcessInfo(name="otro_proceso", full_name="otro_proceso.exe", pid=201,
                     category=CENTINELA_OTROS)

    # snapshot 0: la carga de la fase A. 1: la carga de la fase C.
    # 2 y 3: las dos cargas solapadas de la fase B.
    fake = _FakeProcService([[p1, p2], [q1], [p1], [p1, p2]])

    vista = _VistaSinTk.__new__(_VistaSinTk)
    vista.escrituras = []          # (atributo, hilo) de cada publicación
    vista._procesos = []
    vista._agrupado = _RecordingDict()
    vista.process_service = fake
    vista.pack_service = _FakePackService()
    # `_apply` acaba pintando. Sin widgets, el render es un no-op: lo que se
    # comprueba aqui es la PUBLICACION (hilo y coherencia), no el render, que
    # `test_headless_ui` cubre con una ventana de verdad.
    vista._render_list = lambda *a, **k: None
    vista._update_pack_dropdown = lambda *a, **k: None

    cola = collections.deque()
    entregado = threading.Event()
    posts = []                     # (hilo) que encolo cada after(0, ...)

    def after_falso(ms, func=None, *args):
        """`after` de mentira: ENCOLA y no depende de Tcl."""
        cola.append((func, args))
        posts.append(threading.get_ident())
        entregado.set()

    vista.after = after_falso

    # El hilo secundario se crea DENTRO de `_do_load`, asi que para poder hacer
    # `join` hace falta la referencia. Se espia el `Thread` del modulo de la
    # vista (no el `threading` global: el resto de la suite no lo ve).
    hilos = []

    class _HiloEspia(threading.Thread):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            hilos.append(self)

    class _ShimThreading:
        Thread = _HiloEspia
        Event = threading.Event

    principal = threading.get_ident()
    threading_real = pmv_mod.threading
    pmv_mod.threading = _ShimThreading

    def _cargar(indice):
        """Lanza `_do_load`; el hilo secundario queda PARKED en su puerta."""
        fake.bloquear.add(indice)
        entregado.clear()
        vista._do_load()
        assert fake.cogido[indice].wait(20), (
            f"el hilo secundario no llego al snapshot {indice}"
        )
        return hilos[-1]

    def _bucle(hilo, indice):
        """Abre la puerta, espera al hilo y APLICA en el principal lo entregado."""
        fake.continuar[indice].set()
        entregado.wait(10)          # espera acotada: NO es el discriminante
        hilo.join(10)
        assert not hilo.is_alive(), (
            "el hilo secundario no termino: se quedo bloqueado (con Tcl y sin este "
            "arnes eso era un cuelgue de 150 s con exit=True)"
        )
        aplicados = 0
        while cola:
            func, args = cola.popleft()
            aplicados += 1
            func(*args)              # esto corre en el PRINCIPAL: el hilo principal
        return aplicados

    try:
        # --- A) identidad de hilo y publicacion efectiva ------------------
        # El orden de las aserciones importa: primero la IDENTIDAD del hilo (que
        # es el invariante de FIX-007 y el mensaje mas preciso) y despues el
        # recuento de entregas.
        hilo = _cargar(0)
        aplicados = _bucle(hilo, 0)
        assert vista.escrituras, (
            "el estado nunca se publico: el hilo secundario tiene que entregarlo "
            "por un self.after(0, ...) que se ejecute en el principal (FIX-007)"
        )
        for atributo, ident in vista.escrituras:
            assert ident == principal, (
                f"'{atributo}' se publico desde el hilo {ident}, no desde el "
                f"principal ({principal})"
            )
        assert aplicados >= 1, (
            "nadie ejecuto lo que el secundario encolo: el estado se publico sin "
            "pasar por el hilo principal"
        )
        assert posts, "nadie encolo el after(0, ...)"
        for ident in posts:
            assert ident != principal, (
                "el after(0, ...) se encolo desde el principal: entonces el "
                "secundario no ha calculado nada y la vista se queda congelada"
            )
        assert set(vista.grouped_processes) == {"fake_one", "fake_two"}, (
            f"agrupado inesperado tras la carga: {sorted(vista.grouped_processes)}"
        )
        assert dict(vista.grouped_processes) == ProcessManagerView._group(vista.processes), (
            "grouped_processes no es el agrupado de processes: on_kill_selected "
            "materiaria PIDs que no son los que la vista esta mostrando"
        )

        # --- C) el principal ITERA el agrupado mientras el secundario publica
        # Reproduccion determinista del crash de la app real: el principal
        # abre el iterador (como `_render_list` al pulsar el buscador) y el
        # secundario sigue metiendo claves en el MISMO dict.
        vista.grouped_processes = {"otro_proceso": [q1]}
        rec = vista.grouped_processes
        rec.bloquear = True
        iterador = iter(rec.items())
        next(iterador, None)         # iterador ABIERTO
        rec.desbloquear.set()        # si el secundario muta, no se queda parado
        hilo = _cargar(1)
        _bucle(hilo, 1)
        for atributo, ident in vista.escrituras[-2:]:
            assert ident == principal, (
                f"'{atributo}' se publico desde el hilo {ident} en la carga de la "
                f"fase C, no desde el principal ({principal})"
            )
        assert not rec.en_mutacion.is_set(), (
            f"el hilo secundario entro a MUTAR IN SITU el dict que el principal "
            f"itera: {rec.ops}"
        )
        assert rec.ops == [], (
            f"operaciones in situ sobre el agrupado desde {[i for i, _ in rec.ops]}: "
            "el agrupado se REBIND, no se muta"
        )
        crash = None
        try:
            list(iterador)
        except RuntimeError as e:
            crash = e
        assert crash is None, (
            f"la vista revienta al iterar el dict que muta otro hilo: {crash!r}"
        )
        assert set(vista.grouped_processes) == {"otro_proceso"}, (
            f"agrupado inesperado tras la fase C: {sorted(vista.grouped_processes)}"
        )

        # --- B) dos cargas solapadas con snapshots distintos ---------------
        vista.escrituras.clear()
        posts[:] = []
        hilo_a = _cargar(2)         # carga A: se queda parada a mitad
        hilo_b = _cargar(3)         # carga B: entra mientras A sigue viva
        assert len(posts) == 0, (
            "las dos cargas solapadas no llegaron a encolar su after(0, ...): el "
            "hilo secundario no entrego nada"
        )
        assert _bucle(hilo_a, 2) == 1, (
            "la carga A no publico nada por el hilo principal"
        )
        assert _bucle(hilo_b, 3) == 1, (
            "la carga B no publico nada por el hilo principal"
        )
        for atributo, ident in vista.escrituras:
            assert ident == principal, (
                f"'{atributo}' se publico desde el hilo {ident} en la carga solapada, "
                f"no desde el principal ({principal})"
            )
        esperado = ProcessManagerView._group(vista.processes)
        assert dict(vista.grouped_processes) == esperado, (
            "tras dos cargas solapadas, grouped_processes describe un snapshot "
            f"obsoleto respecto de processes: agrupado={sorted(vista.grouped_processes)} "
            f"procesos={sorted(p.name for p in vista.processes)} "
            f"esperado={sorted(esperado)}: el killaria PIDs equivocados"
        )
        assert set(vista.grouped_processes) in ({"fake_one"}, {"fake_one", "fake_two"}), (
            f"el agrupado final no corresponde a ninguno de los snapshots: "
            f"{sorted(vista.grouped_processes)}"
        )
    finally:
        pmv_mod.threading = threading_real
    print("do_load publica desde el principal sin Tk OK (FIX-007/P8).")


def test_pack_service_backup_and_recovery():
    """TASK-026 (FIX-009): backup preventivo, RECUPERACION desde .bak y except honesto.

    Antes `save()` no tenia backup (la "rotacion" de TASK-011 / v3.1-QoL /
    CHANGELOG nunca se escribio) y `load()` hacia `except (json.JSONDecodeError,
    Exception)`, que es `except Exception`: un JSON corrupto BORRABA todos los
    packs del usuario y sobrescribia el archivo con uno que solo tiene el Gaming,
    y un PermissionError tomaba la misma ruta.
    """
    print("Testing PackService backup, recuperacion y except honesto (FIX-009)...")
    import json
    import shutil
    import tempfile
    from woptimizer.services.pack_service import PackService

    svc, tmp_path = _pack_service_temporal()
    bak_path = tmp_path + ".bak"
    tmp_tmp = tmp_path + ".tmp"

    def _leer(ruta):
        with open(ruta, encoding="utf-8") as fh:
            return json.load(fh)

    try:
        # --- A0) instalacion limpia: no hay archivo, no hay backup que rotar ---
        # TASK-031 (E-3) INVIERTE la asercion de este bloque. Antes era "la
        # primera escritura debe crear el archivo", porque `load()` llamaba a
        # `save()` (DOS veces) y dejaba un `profiles.json` con un solo pack en
        # el arranque. Ahora `load()` es de SOLO LECTURA: no se crea el
        # fichero hasta que el usuario hace algo real, y un `profiles.json`
        # vacio solo confunde. Lo que se sigue exigiendo es lo importante: ni
        # un `.bak` basura ni un `.tmp` colgado, y la app arranca con el pack
        # `gaming` en memoria.
        limpio = os.path.join(tempfile.mkdtemp(prefix="wopt_t026_limpio_"), "profiles.json")
        try:
            servicio_limpio = PackService(data_path=limpio)
            assert not os.path.exists(limpio), (
                "load() no puede crear el fichero: es de solo lectura. Un arranque "
                "que escribe se traga la recuperacion del .bak (TASK-031 E-3)"
            )
            assert not os.path.exists(limpio + ".bak"), (
                "una instalacion limpia no debe dejar un .bak basura"
            )
            assert not os.path.exists(limpio + ".tmp"), "la escritura atomica no deja .tmp"
            assert servicio_limpio.get_all_packs()["gaming"].is_gaming is True, (
                "sin fichero en disco la app tiene que funcionar igual: el pack "
                "gaming se asegura EN MEMORIA"
            )
            # Y la primera escritura REAL si crea el fichero, sin .bak de basura.
            servicio_limpio.create_user_pack("primero", "Primero", ["primero.exe"])
            assert os.path.exists(limpio), "la primera escritura real debe crear el archivo"
            assert not os.path.exists(limpio + ".bak"), (
                "la primera escritura no tiene version anterior que rotar"
            )
        finally:
            shutil.rmtree(os.path.dirname(limpio), ignore_errors=True)

        # --- A) copia preventiva -------------------------------------------
        svc.create_user_pack("trabajo", "Trabajo", ["trabajo.exe"])
        assert os.path.exists(bak_path), "save() no creo el .bak preventivo"
        assert "trabajo" not in _leer(bak_path).get("packs", {}), (
            "el .bak debe contener la version ANTERIOR, no la recien guardada"
        )
        assert "trabajo" in _leer(tmp_path)["packs"], (
            "el principal debe contener el pack recien creado"
        )
        assert not os.path.exists(tmp_tmp), "la escritura atomica no debe dejar un .tmp"

        # --- B) rotacion de verdad, no copia posterior ---------------------
        svc.create_user_pack("beta", "Beta", ["beta.exe"])
        svc.delete_pack("beta")
        bak = _leer(bak_path).get("packs", {})
        principal = _leer(tmp_path).get("packs", {})
        assert "beta" in bak, (
            "el .bak debe contener la version N-1 (rotacion), no la recien escrita"
        )
        assert "beta" not in principal

        # --- C) RECUPERACION desde el .bak ante JSON corrupto -------------
        with open(tmp_path, "w", encoding="utf-8") as fh:
            fh.write('{"packs": {"trabajo": ')       # apagon a mitad del json.dump
        servicio = PackService(data_path=tmp_path)
        packs = servicio.get_all_packs()
        assert "trabajo" in packs, (
            f"la recuperacion desde el .bak no devolvio los packs del usuario: {sorted(packs)}"
        )
        assert packs["trabajo"].apps == ["trabajo.exe"], (
            f"los apps del pack recuperado llegaron vacios: {packs['trabajo'].apps}"
        )
        assert packs["gaming"].is_gaming is True, "el pack gaming debe seguir marcado"
        with open(tmp_path, encoding="utf-8") as fh:
            assert fh.read().startswith('{"packs": {"trabajo": '), (
                "recuperar NO debe reescribir el principal corrupto (ni pisar el .bak bueno)"
            )

        # --- D) un error de permisos NO puede entrar en la ruta destructiva -
        # Escenario real: el antivirus bloquea el archivo. Se marca en solo
        # lectura DESPUES de corromperlo (escribir encima de un read-only
        # dari PermissionError antes de poder preparar el escenario).
        os.chmod(bak_path, 0o600)
        os.chmod(tmp_path, 0o400)
        try:
            if os.access(tmp_path, os.W_OK):
                print("  (aviso: el SO no aplica solo-lectura; se omite el caso D)")
            else:
                # D1) hay .bak sano: se recupera sin escribir nada.
                try:
                    servicio_bloqueado = PackService(data_path=tmp_path)
                except PermissionError as e:
                    raise AssertionError(
                        "con un .bak sano, un principal corrupto y solo-lectura se debe "
                        f"RECUPERAR del backup, no reventar: {e}"
                    )
                assert "trabajo" in servicio_bloqueado.get_all_packs()
                with open(tmp_path, encoding="utf-8") as fh:
                    assert fh.read().startswith('{"packs": {"trabajo": '), (
                        "recuperar con el archivo bloqueado no debe reescribir el principal"
                    )

                # D2) sin .bak: el principal corrupto NO se toca. TASK-031 (E-3)
                # cambio el MECANISMO de esta fila, no su invariante: antes
                # `load()` intentaba regenerar, el volcado reventaba por el
                # solo-lectura y el error se propagaba. Ahora `load()` no
                # escribe NADA, asi que no hay nada que reventar: lo que se
                # exige es lo que siempre se quiso (el fichero del usuario no
                # se destruye) y, ademas, que nadie lo reescriba a lo bruto.
                os.unlink(bak_path)
                servicio_sin_bak = PackService(data_path=tmp_path)
                with open(tmp_path, encoding="utf-8") as fh:
                    assert fh.read().startswith('{"packs": {"trabajo": '), (
                        "sin .bak legible el principal se queda EN DISCO tal cual "
                        "(TASK-031 condicion 3 de proposal.md 3): regenerar aqui "
                        "reescribia el fichero del usuario con un solo pack"
                    )
                assert servicio_sin_bak.fichero_danado is True, (
                    "un principal ilegible tiene que quedar MARCADO como dañado, no "
                    "desaparecer en silencio (Trampa #14)"
                )
                assert not os.path.exists(tmp_tmp), "un save fallido no debe dejar un .tmp"
        finally:
            os.chmod(tmp_path, 0o600)

        # --- D2) un OSError al LEER se propaga, no se regenera -------------
        directorio = tempfile.mkdtemp(prefix="wopt_t026_dir_")
        try:
            try:
                PackService(data_path=directorio)
            except OSError:
                pass
            else:
                raise AssertionError(
                    "una ruta que no es un archivo debe fallar, no regenerar un "
                    "profiles.json por defecto encima"
                )
        finally:
            shutil.rmtree(directorio, ignore_errors=True)
    finally:
        for ruta in (tmp_path, bak_path, tmp_tmp):
            if os.path.exists(ruta):
                try:
                    os.chmod(ruta, 0o600)
                except OSError:
                    pass
                os.unlink(ruta)
    print("PackService backup y recuperacion OK (FIX-009).")


def test_default_meta_matches_canonical_otros():
    """TASK-026 (FIX-005): el centinela de categoria es UN literal, en TRES sitios.

    `process_service._DEFAULT_META` y el `props.get('category', ...)` de
    `_load_local_db` usaban "? Otros" (ASCII U+003F) mientras el resto del
    sistema usa "U+26AA Otros" (config.CATEGORY_ORDER y models.ProcessInfo).
    Con el literal equivocado, ese proceso caia FUERA de CATEGORY_ORDER y se
    ordenaba con el centinela 999 del sort, y el filtro de
    `pack_manager_view` (que comparaba contra "? Otros") dejaba de excluir la
    categoria canonica del acordeon de `target_categories`.
    """
    print("Testing centinela de categoria canonico (FIX-005)...")
    import json
    import shutil
    import tempfile
    import woptimizer.config as wopt_config
    from woptimizer.config import CATEGORY_ORDER
    from woptimizer.models import ProcessInfo
    from woptimizer.services import process_service as ps_mod
    from woptimizer.services.process_service import ProcessService

    assert CATEGORY_ORDER[-1] == CENTINELA_OTROS, (
        f"CATEGORY_ORDER[-1] es {CATEGORY_ORDER[-1]!r}, no el circulo U+26AA"
    )
    assert ProcessInfo.model_fields["category"].default == CENTINELA_OTROS
    assert ps_mod._DEFAULT_META[0] == CENTINELA_OTROS, (
        f"_DEFAULT_META[0] es {ps_mod._DEFAULT_META[0]!r}: la interrogacion ASCII "
        "no es el circulo U+26AA"
    )
    assert chr(0x26AA) in ps_mod._DEFAULT_META[0]
    assert CENTINELA_ASCII not in ps_mod._DEFAULT_META[0]
    assert CENTINELA_ASCII not in CENTINELA_OTROS

    # Comportamiento y no solo literales: con la DB vacia, la categoria del
    # fallback tiene que participar en el ORDEN real (ultimo indice), no caer
    # en el 999 de `cat_idx.get(p.category, 999)`.
    ps = ProcessService()
    ps._db_map = {}
    ps._meta_cache.clear()
    cat, prio, _ = ps._get_process_meta("nombre_inexistente_xyz")
    assert cat == CENTINELA_OTROS, f"la DB vacia devolvio {cat!r}"
    cat_idx = {c: i for i, c in enumerate(CATEGORY_ORDER)}
    assert cat_idx.get(cat, 999) == len(CATEGORY_ORDER) - 1, (
        "la categoria centinela debe resolver al ultimo indice de CATEGORY_ORDER, "
        "no al centinela 999 del sort de get_running_processes"
    )

    # Sitio 2: una entrada de DB SIN clave 'category' entra por el mismo literal.
    tmp = tempfile.mkdtemp(prefix="wopt_t026_f005_")
    _dir_data_original = wopt_config._data_dir
    try:
        os.makedirs(os.path.join(tmp, "assets"))
        with open(os.path.join(tmp, "assets", "process_db.json"), "w", encoding="utf-8") as fh:
            json.dump({"sin_clave_app": {"priority": "high",
                                         "description": "ENTRADA SIN CATEGORY"}},
                      fh, ensure_ascii=False)
        wopt_config._data_dir = lambda: tmp
        ps_sin_clave = ProcessService()
        assert ps_sin_clave.is_db_loaded, "el servicio debe cargar el JSON de prueba"
        cat_sin_clave, _, _ = ps_sin_clave._get_process_meta("sin_clave_app")
        assert cat_sin_clave == CENTINELA_OTROS, (
            f"una entrada sin 'category' entro por {cat_sin_clave!r}: el segundo "
            "sitio del literal sigue desalineado"
        )
    finally:
        wopt_config._data_dir = _dir_data_original
        shutil.rmtree(tmp, ignore_errors=True)

    # Sitio 3: el filtro del acordeon de categorias compara contra el canonico.
    ruta = os.path.join("src", "woptimizer", "ui", "views", "pack_manager_view.py")
    with open(ruta, encoding="utf-8") as fh:
        arbol = ast.parse(fh.read())
    literales = [n.value for n in ast.walk(arbol)
                 if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    assert CENTINELA_ASCII not in literales, (
        f"{ruta} sigue usando el literal ASCII {CENTINELA_ASCII!r}"
    )
    def _constantes_de_comparacion(nodo):
        """Literales de un Compare, este en el lado izquierdo o en los comparadores."""
        lados = [nodo.left] + list(nodo.comparators)
        return [o.value for o in lados if isinstance(o, ast.Constant)]

    filtros = [n for n in ast.walk(arbol)
               if isinstance(n, ast.Compare)
               and CENTINELA_OTROS in _constantes_de_comparacion(n)]
    assert filtros, (
        f"el filtro de categorias de {ruta} debe comparar contra {CENTINELA_OTROS!r} "
        "para seguir excluyendo la categoria centinela del acordeon"
    )
    assert any(isinstance(op, ast.NotIn) for n in filtros for op in n.ops)
    print("Centinela de categoria canonico OK (FIX-005).")


def test_gaming_pack_fallback_is_deep_copy():
    """TASK-026 (FIX-001): el FALLBACK de get_gaming_pack() tambien copia hondo.

    `model_copy()` de Pydantic v2 es SHALLOW: sin `deep=True` el fallback
    comparte `apps`/`keepers`/`target_categories` con DEFAULT_GAMING_PACK, y
    cualquier mutacion in situ (la UI las hace al anadir a un pack) contamina
    el global de modulo. Hoy es DEUDA LATENTE: `get_gaming_pack()` no tiene
    llamadores en la UI (todo pasa por `get_all_packs()`) y
    `_ensure_gaming_pack()` siempre inserta la clave "gaming", asi que la
    ruta del fallback nunca se ejecuta en produccion. El ciclo #10 ya cerro la
    via alcanzable y su test llama con la clave PRESENTE, asi que este era el
    unico hueco sin cobertura.
    """
    print("Testing fallback de get_gaming_pack con copia profunda (FIX-001)...")
    from woptimizer.services.pack_service import DEFAULT_GAMING_PACK

    apps_esperadas = list(DEFAULT_GAMING_PACK.apps)
    keepers_esperadas = list(DEFAULT_GAMING_PACK.keepers)
    cats_esperadas = list(DEFAULT_GAMING_PACK.target_categories)

    pack_s, tmp_path = _pack_service_temporal()
    try:
        del pack_s._data.packs["gaming"]        # fuerza el fallback
        g = pack_s.get_gaming_pack()

        assert g.apps is not DEFAULT_GAMING_PACK.apps, "apps comparte objeto (shallow)"
        assert g.keepers is not DEFAULT_GAMING_PACK.keepers, "keepers comparte objeto (shallow)"
        assert g.target_categories is not DEFAULT_GAMING_PACK.target_categories, (
            "target_categories comparte objeto (shallow)"
        )

        # Mutacion IN SITU, igual que hace la UI al anadir a un pack.
        g.apps.append("CONTAMINA.exe")
        g.keepers.append("contamina_keeper.exe")
        g.target_categories.append("CONTAMINA CATEGORIA")

        assert DEFAULT_GAMING_PACK.apps == apps_esperadas, (
            f"El global fue contaminado por el fallback: {DEFAULT_GAMING_PACK.apps}"
        )
        assert DEFAULT_GAMING_PACK.keepers == keepers_esperadas
        assert DEFAULT_GAMING_PACK.target_categories == cats_esperadas

        # Y el reset devuelve los valores de fabrica.
        pack_s.reset_gaming_pack()
        restaurado = pack_s.get_gaming_pack()
        assert restaurado.apps == apps_esperadas, f"Apps no restauradas: {restaurado.apps}"
        assert restaurado.keepers == keepers_esperadas
        assert restaurado.target_categories == cats_esperadas
    finally:
        for sufijo in ("", ".bak", ".tmp"):
            ruta = tmp_path + sufijo
            if os.path.exists(ruta):
                os.unlink(ruta)
    print("Fallback de get_gaming_pack con copia profunda OK (FIX-001).")


# ===========================================================================
# TASK-030 - Cerrar los 3 supervivientes de mutacion del ciclo #17.
# Ocho sondas. Cada una nombra la MUTACION EXACTA que mata (tasks.md sec. 0):
#   P1  test_save_atomic_nunca_toca_el_principal           M1, M3, M4, M10
#   P1b test_publicar_no_trunca_el_principal              M2
#   P2  test_save_no_escribe_si_la_rotacion_no_puede_leer  M6
#   P3  test_corrupcion_sin_backup_intenta_volar           M1, M10
#   P4  test_forma_legacy_no_tumba_la_app                  el bug (AttributeError)
#   P5  test_todas_las_clases_de_corrupcion_se_recuperan   M5
#   P6  test_oserror_de_lectura_no_es_corrupcion           M6, M7
#   P7  test_attribute_error_ajeno_no_es_corrupcion        M7, M9
#   P8  test_do_load_publica_sin_tk                        mutacion de FIX-007
# Prohibido en todas: `sleep`, `subprocess`, abrir una ventana, y afirmar que
# "existe un .tmp" (eso es un artefacto, no la atomicidad).
# ===========================================================================


class _ModuloDoble:
    """Doble de un modulo: sustituye algunos atributos y delega el resto.

    Se usa sobre `pack_service.json` y `pack_service.shutil` en vez de parchear
    la stdlib en global: el servicio resuelve `json.dump` en sus propios
    globales, asi que cambiar la referencia del modulo basta y ningun otro test
    del proceso ve el doble.
    """

    def __init__(self, real, **overrides):
        self._real = real
        self._overrides = overrides

    def __getattr__(self, nombre):
        if nombre in self._overrides:
            return self._overrides[nombre]
        return getattr(self._real, nombre)


def _doble_en(modulo, **overrides):
    """Context manager: sustituye `modulo.<nombre>` por lo que se pase."""
    import contextlib

    @contextlib.contextmanager
    def _ctx():
        originales = {}
        for nombre, valor in overrides.items():
            originales[nombre] = getattr(modulo, nombre)
            setattr(modulo, nombre, valor)
        try:
            yield
        finally:
            for nombre, valor in originales.items():
                setattr(modulo, nombre, valor)

    return _ctx()


def _bytes_de(ruta):
    with open(ruta, "rb") as fh:
        return fh.read()


def _escribir(ruta, contenido):
    """Escribe `str` o `bytes` segun el tipo del contenido."""
    if isinstance(contenido, bytes):
        with open(ruta, "wb") as fh:
            fh.write(contenido)
    else:
        with open(ruta, "w", encoding="utf-8") as fh:
            fh.write(contenido)


def _capturar(fn):
    """Ejecuta `fn` y devuelve la excepcion, o None si no lanzo."""
    try:
        fn()
    except Exception as e:          # noqa: BLE001 - aqui se quiere ver CUALQUIER fallo
        return e
    return None


def _limpiar_perfiles(ruta):
    """Borra principal/.bak/.tmp, tolerando el flag de solo lectura."""
    for sufijo in ("", ".bak", ".tmp"):
        p = ruta + sufijo
        if os.path.exists(p):
            try:
                os.chmod(p, 0o600)
            except OSError:
                pass
            os.unlink(p)


# Un .bak SANO que ya trae el pack gaming: asi `_ensure_gaming_pack()` no
# llama a `save()` y "recuperar" no reescribe el principal. Si el .bak no trae
# el gaming, la recuperacion publica por el `.bak` y el principal SI cambia, y
# el test no podria afirmar que la recuperacion no escribe nada.
_BAK_SANO = {
    "packs": {
        "salvado": {"id": "salvado", "name": "Salvado", "apps": ["salvado.exe"]},
        "gaming": {"id": "gaming", "name": "Gaming", "is_gaming": True,
                   "apps": ["chrome.exe"]},
    }
}


def test_save_atomic_nunca_toca_el_principal():
    """TASK-030 / P1: el volcado NUNCA toca el principal y, si falla, no cambia ni un byte.

    Lo que hay antes (run_tests.py, asserts de `not os.path.exists(...tmp)`)
    NO prueba la atomicidad: es un ARTEFACTO. Si `save()` deja de crear el
    temporal, el assert sigue verde por la razon equivocada.

    Aqui el fallo se inyecta DENTRO de `json.dump`, en el MISMO hilo y con el
    HANDLE REAL: el doble anota a quien le estan dando el fichero, escribe un
    prefijo JSON truncado de verdad, hace `flush()` y lanza `OSError`. Si el
    servicio escribiera sobre el principal, ese prefijo se queda en el archivo
    del usuario, y eso se comprueba por BYTES, no por existencia de ficheros.

    MATA: M1 (`open(w)` directo al principal) por cuatro aserciones, M3 (sin
    `unlink` del temporal) y M4 (`except: pass` que se traga el error), M10
    (el temporal en otro directorio/volumen).

    Orden obligatorio: `antes` se captura DESPUES de construir el servicio, porque
    `__init__` -> `load()` -> `_ensure_gaming_pack()` -> `save()` ya reescribio
    el archivo una vez. Capturarlo antes hace fallar este test con el codigo
    correcto.
    """
    print("Testing escritura atomica: el volcado nunca toca el principal (P1)...")
    import json
    from woptimizer.services import pack_service as ps
    from woptimizer.services.pack_service import PackService

    prefijo = '{\n    "packs": {\n        "trabajo": {\n            "id": "tra'
    svc, ruta = _pack_service_temporal()
    try:
        svc.create_user_pack("previo", "Previo", ["previo.exe"])
        antes = _bytes_de(ruta)          # <- DESPUES de construir el servicio

        visto = {}

        def dump_interrumpido(obj, fp, **kwargs):
            """Anota el estado en el instante del volcado y rompe ahi."""
            nombre = getattr(fp, "name", None)
            visto["nombre"] = nombre
            visto["es_principal"] = os.path.normcase(nombre or "") == os.path.normcase(ruta)
            visto["mismo_directorio"] = os.path.dirname(nombre or "") == os.path.dirname(ruta)
            visto["tmp_existe"] = os.path.exists(ruta + ".tmp")
            visto["principal_intacto"] = os.path.exists(ruta) and _bytes_de(ruta) == antes
            fp.write(prefijo)            # por el HANDLE REAL, no por la ruta
            fp.flush()
            raise OSError("apagon simulado en mitad del volcado")

        fallo = None
        with _doble_en(ps, json=_ModuloDoble(json, dump=dump_interrumpido)):
            try:
                svc.create_user_pack("trabajo", "Trabajo", ["trabajo.exe"])
            except OSError as e:
                fallo = e

        assert fallo is not None, (
            "save() no propago el fallo del volcado: el `except Exception` se "
            "traga el error (M4) y el caller cree que ha guardado lo que no se "
            "ha guardado"
        )
        assert "apagon simulado" in str(fallo), f"el fallo no es el inyectado: {fallo!r}"
        assert not visto["es_principal"], (
            f"el volcado se hizo SOBRE el profiles.json del usuario ({visto['nombre']}): "
            "la escritura no es atomica (M1)"
        )
        assert visto["mismo_directorio"], (
            f"el temporal se escribio en {os.path.dirname(visto['nombre'])} y el "
            f"principal esta en {os.path.dirname(ruta)}: `os.replace` entre volumenes "
            "no es atomico y el temporal sobrevive a un apagón (M10)"
        )
        assert visto["tmp_existe"], (
            "en el instante del volcado no habia temporal: save() no vuelca a un "
            "fichero aparte, lo hace directamente sobre el principal (M1)"
        )
        assert visto["principal_intacto"], (
            "el principal ya no tenia sus bytes cuando empezo el volcado: el "
            "temporal se ha escrito en el sitio equivocado"
        )
        assert _bytes_de(ruta) == antes, (
            "el principal cambio de bytes pese a que el volcado fallo: el prefijo "
            "truncado se quedo en el archivo del usuario (M1)"
        )
        assert not os.path.exists(ruta + ".tmp"), (
            "un volcado fallido dejo el temporal: la limpieza del `except` se perdio "
            "(M3, M4)"
        )

        # Y lo que de verdad importa al usuario: los packs de antes siguen ahi.
        recargado = PackService(data_path=ruta).get_all_packs()
        assert "previo" in recargado, (
            f"los packs anteriores desaparecieron: {sorted(recargado)}"
        )
        assert recargado["previo"].apps == ["previo.exe"], (
            f"los apps del pack previo llegaron vacios: {recargado['previo'].apps}"
        )
        assert "trabajo" not in recargado, (
            "el pack que no se pudo guardar aparece en disco: la escritura fallo "
            "a medias y publico datos parciales"
        )
    finally:
        _limpiar_perfiles(ruta)
    print("Escritura atomica: el volcado nunca toca el principal OK (P1).")


def test_publicar_no_trunca_el_principal():
    """TASK-030 / P1b: publicar NO puede usar un primitivo de COPIA.

    Ciego a M2 (`os.replace` -> `shutil.copyfile`) por construccion: con
    `copyfile` el volcado SI va al temporal, asi que el assert de P1 (bytes del
    principal intactos al cortar el volcado) pasa igual. Lo unico que separa
    los dos casos es COMO se publica, y eso no se ve desde un solo hilo: entre
    el `truncate` del destino y el ultimo byte de la copia hay una ventana que
    ningun test de un hilo puede ver (proposal.md 1.4). La respuesta honesta es
    fallo inyectado: un doble de `copyfile` que trunca el destino y revienta,
    que es exactamente "la publicacion no es atomica y se apago a mitad".

    MATA: M2. Con el codigo correcto `copyfile` no se llama NUNCA y el principal
    queda completo y parseable con el pack nuevo.

    Al final hay una RED estatica (no una prueba): ninguna llamada a
    `copy*`/`move` dentro de `save()`. Se declara como red porque el test de
    runtime es el que manda; la guarda solo aniade una deteccion estatica.
    """
    print("Testing publicacion no truncante (P1b)...")
    import json
    import shutil
    from woptimizer.services import pack_service as ps
    from woptimizer.services.pack_service import PackService

    copiados = []

    def copyfile_hostil(src, dst, *args, **kwargs):
        """Emula una copia interrumpida: `copyfile` real abre el destino en
        'wb', lo TRUNCA antes de copiar y aqui se apaga a mitad."""
        copiados.append((src, dst))
        with open(dst, "wb") as fh:
            fh.write(b"")               # el archivo del usuario queda a cero
        raise OSError("copia interrumpida a mitad")

    svc, ruta = _pack_service_temporal()
    try:
        svc.create_user_pack("previo", "Previo", ["previo.exe"])
        with _doble_en(ps, shutil=_ModuloDoble(shutil, copyfile=copyfile_hostil)):
            fallo = _capturar(
                lambda: svc.create_user_pack("trabajo", "Trabajo", ["trabajo.exe"])
            )
        assert fallo is None, (
            f"save() no publico con un metodo atomico: se llamo a "
            f"{copiados[-1][0] if copiados else '?'} -> {copiados[-1][1] if copiados else '?'} "
            f"y fallo con {fallo!r} (M2: `os.replace` sustituido por `shutil.copyfile`)"
        )
        assert not copiados, (
            f"la publicacion uso un primitivo de COPIA {copiados}: `copyfile` "
            "trunca el destino antes de copiar, asi que un corte de luz deja el "
            "profiles.json del usuario a medias (M2)"
        )
        datos = json.loads(_bytes_de(ruta).decode("utf-8"))
        assert "trabajo" in datos["packs"], (
            f"el pack recien creado no esta en el principal: {sorted(datos['packs'])}"
        )
        assert datos["packs"]["trabajo"]["apps"] == ["trabajo.exe"], (
            f"el principal quedo incompleto: {datos['packs']['trabajo']}"
        )
        assert datos["packs"]["previo"]["apps"] == ["previo.exe"], (
            "el principal no conserva los packs anteriores: quedo truncado"
        )
        assert PackService(data_path=ruta).get_all_packs()["trabajo"].apps == ["trabajo.exe"]

        # --- RED estatica (no es la prueba; la prueba es el doble de arriba) --
        ruta_src = os.path.join("src", "woptimizer", "services", "pack_service.py")
        with open(ruta_src, encoding="utf-8") as fh:
            arbol = ast.parse(fh.read())
        save = next((n for n in ast.walk(arbol)
                     if isinstance(n, ast.FunctionDef) and n.name == "save"), None)
        assert save is not None, f"{ruta_src} ya no tiene save()"
        for nodo in ast.walk(save):
            if (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)
                    and nodo.func.attr in ("copyfile", "copy", "copytree", "move",
                                           "rmtree", "rename")):
                raise AssertionError(
                    f"{ruta_src}:{nodo.lineno} publica con .{nodo.func.attr}(): una copia "
                    "trunca el destino antes de copiar y no es atomica. Publica con "
                    "os.replace sobre un temporal del MISMO directorio (M2)"
                )
        assert any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                   and n.func.attr == "replace" for n in ast.walk(save)), (
            "save() no publica con os.replace: la red estatica no ve ninguna "
            "publicacion atomica")
    finally:
        _limpiar_perfiles(ruta)
    print("Publicacion no truncante OK (P1b).")


def test_save_no_escribe_si_la_rotacion_no_puede_leer():
    """TASK-030 / P2: un error de LECTURA no se convierte en "sigo y sobrescribo".

    El invariante: si `save()` no puede leer el principal para rotar el backup,
    no puede (a) tragarse el error ni (b) publicar nada. El antivirus con el
    fichero bloqueado da `PermissionError` en `_rotate_backup()`; con el estado
    en memoria vacio, "sigo y sobrescribo" deja al usuario con cero packs.

    MATA: M6 (`OSError` readmitido en `CORRUPTION_ERRORS`): entonces
    `_rotate_backup` se traga el error, el volcado va al temporal, `os.replace`
    publica y el archivo del usuario queda con el estado VACIO. Medido: dos
    fallos, `save()` no lanzo y el principal sobrescrito.

    Lo que este test NO puede matar (proposal.md 2.1): el camino D2 es
    INDISTINGUINABLE por construccion con un espia de llamadas - el codigo
    correcto y el mutante llaman a `save()` una vez y vuelcan una vez. Por eso
    aqui no se cuenta ninguna llamada: se mira la CLASIFICACION (lanza o no) y
    la ESCRITURA (los bytes del principal). La mitad de `load()` la matan P6 y
    P7.
    """
    print("Testing save() respeta un OSError de lectura (P2)...")
    import json
    from woptimizer.models import AppData
    from woptimizer.services import pack_service as ps

    def load_bloqueado(*args, **kwargs):
        raise PermissionError("el antivirus tiene el principal bloqueado")

    svc, ruta = _pack_service_temporal()
    try:
        svc.create_user_pack("previo", "Previo", ["previo.exe"])
        antes = _bytes_de(ruta)
        bak_antes = _bytes_de(ruta + ".bak")
        svc._data = AppData()          # si save() no respeta el fallo, publica el vacio

        with _doble_en(ps, json=_ModuloDoble(json, load=load_bloqueado)):
            fallo = _capturar(svc.save)

        assert isinstance(fallo, PermissionError), (
            "save() no lanzo el PermissionError de la rotacion: un error que no es "
            "corrupcion se ha convertido en 'sigo y sobrescribo' (M6: OSError "
            f"readmitido en CORRUPTION_ERRORS). Lo que paso: {fallo!r}"
        )
        assert _bytes_de(ruta) == antes, (
            "el principal cambio de bytes pese a que la rotacion no pudo leer: "
            "los packs del usuario se sustituyen por el estado vacio (M6)"
        )
        assert _bytes_de(ruta + ".bak") == bak_antes, (
            "el .bak sano se toco pese a no poder leerse el principal: la unica "
            "copia buena no puede depender de una lectura fallida"
        )
        assert not os.path.exists(ruta + ".tmp"), (
            "un save() abortado en la rotacion dejo un temporal"
        )
    finally:
        _limpiar_perfiles(ruta)
    print("save() respeta un OSError de lectura OK (P2).")


def test_corrupcion_sin_backup_intenta_volar():
    """TASK-030 / P3 -> TASK-031: `load()` NO vuelca; el volcado REAL va al temporal.

    Este probe NACIO para una situacion que TASK-031 elimino (E-3). Antes
    `load()` llamaba a `save()` DOS veces y con el principal corrupto y sin
    `.bak` intentaba REGENERAR: hacia falta demostrar que se LLEGABA a volcar.
    El doble iba sobre `json.dump` y NO sobre `save()`: con la doble escritura
    de antes la ruta era INDISTINGUIBLE por construccion, y por eso este test
    nunca conto llamadas.

    Con E-3 (`load()` de SOLO LECTURA) esa ruta no existe: la asercion se
    INVIERTE y la discriminacion de M1/M10 se traslada a la escritura real, que
    es la que sigue existiendo. Se queda en el mismo probe porque la costura
    que hay que espiar es la misma.

    MATA: L-M3 (`load()` vuelve a escribir al arrancar: la lista de volcados no
    esta vacia tras construir el servicio) y, en la segunda mitad, M1 y M10.

    NO mata M6 ni M7, y no se presenta como si lo hiciera: con el
    `PermissionError` inyectado los dos caminos son indistinguibles
    (proposal.md 2.1). Complementario: P2 y P6 son las que miran la
    clasificacion.

    Nota de Windows: `os.chmod(0o400)` NIEGA LA ESCRITURA pero la lectura sigue
    permitida, y `os.replace` sobre un principal de solo lectura puede o no
    fallar segun el equipo. Por eso el discriminante NO es el permiso, es el
    doble: si el volcado se dirige alguna vez al principal, el propio doble
    revienta, y la asercion de bytes/directorio sigue valiendo igual.
    """
    print("Testing que load() no vuelca y el volcado real va al temporal (P3)...")
    import json
    import shutil
    import tempfile
    from woptimizer.services import pack_service as ps
    from woptimizer.services.pack_service import PackService

    real_dump = json.dump
    volcados = []

    def dump_contado(obj, fp, **kwargs):
        nombre = getattr(fp, "name", "")
        volcados.append(nombre)
        if os.path.normcase(nombre) == os.path.normcase(ruta):
            raise AssertionError(
                f"el volcado se hizo sobre el principal ({nombre}): save() tiene que "
                "volcar al temporal del mismo directorio y publicar con os.replace (M1)"
            )
        return real_dump(obj, fp, **kwargs)

    directorio = tempfile.mkdtemp(prefix="wopt_t030_p3_")
    ruta = os.path.join(directorio, "profiles.json")
    _escribir(ruta, '{"packs": {"x": ')        # apagón a mitad del json.dump
    try:
        os.chmod(ruta, 0o400)                  # principal bloqueado (D2)
        with _doble_en(ps, json=_ModuloDoble(json, dump=dump_contado)):
            servicio = PackService(data_path=ruta)
            volcados_tras_arrancar = list(volcados)
            # El bloque se levanta para que la escritura REAL del usuario se
            # pueda publicar en Windows (os.replace sobre un principal de solo
            # lectura da PermissionError); a la costura que se espia no le
            # afecta.
            os.chmod(ruta, 0o600)
            servicio.create_user_pack("nuevo", "Nuevo", ["nuevo.exe"])

        assert volcados_tras_arrancar == [], (
            "load() sigue escribiendo al arrancar: se llego a volcar "
            f"{volcados_tras_arrancar} sin que el usuario haya hecho nada. El "
            "arranque es la via por la que se destruye el .bak sano (L-M3, "
            "proposal.md 4 R-2)"
        )
        assert volcados, (
            "no se llego a volcar nada al guardar de verdad: save() tiene que "
            "volcar al TEMPORAL (que si es escribible) y no abrir el "
            "principal en 'w' (M1) ni un temporal que no se puede abrir (M10)"
        )
        for nombre in volcados:
            assert os.path.dirname(nombre) == os.path.dirname(ruta), (
                f"el volcado fue a {nombre}: el temporal tiene que estar en el MISMO "
                f"directorio que {ruta} para que os.replace sea atomico (M10)"
            )
    finally:
        if os.path.exists(ruta):
            try:
                os.chmod(ruta, 0o600)
            except OSError:
                pass
        shutil.rmtree(directorio, ignore_errors=True)
    print("load() no vuelca y el volcado real va al temporal OK (P3).")


def test_forma_legacy_no_tumba_la_app():
    """TASK-030 / P4: `profiles` con la FORMA equivocada no tumba la app.

    Con el codigo anterior, `{"profiles": "texto"}` producia `AttributeError:
    'str' object has no attribute 'items'` DENTRO de `_read_json`, y como
    `AttributeError` no esta en `CORRUPTION_ERRORS` el error salia de
    `PackService.__init__`: la APP NO ARRANCABA. Peor que perder packs.

    Este test falla con el codigo anterior: no es tautologico, es el bug.

    MATA: el reintroducir la desreferencia sin validar la forma. Y fija la
    decision de diseno de `proposal.md` 4.3: solo un error de FORMA propio
    (`PerfilCorruptoError`) puede "lavarse" como corrupcion; `AttributeError` y
    `OSError` NO estan en la tupla, y por eso no se pueden "arreglar" anad them.
    """
    print("Testing la forma legacy no tumba la app (P4)...")
    import json
    import shutil
    import tempfile
    from woptimizer.services import pack_service as ps
    from woptimizer.services.pack_service import (CORRUPTION_ERRORS, PackService,
                                                  PerfilCorruptoError)

    # --- la decision de diseno, antes que el comportamiento ---------------
    assert issubclass(PerfilCorruptoError, ValueError), (
        "PerfilCorruptoError debe ser un ValueError: la rama legacy ya fallaba con "
        "un ValueError de facto y no se cambia el tipo que ve quien llama"
    )
    assert PerfilCorruptoError in CORRUPTION_ERRORS, (
        "un profiles.json con la FORMA equivocada no se recuperaria del .bak"
    )
    assert AttributeError not in CORRUPTION_ERRORS, (
        "AttributeError NO puede estar en CORRUPTION_ERRORS: es un SINTOMA de un "
        "bug, no una clase de fallo. Si se traga, cualquier `None` mal "
        "desreferenciado se convierte en 'el archivo esta roto' y el siguiente "
        "save() borra los packs que el usuario acaba de crear (M9)"
    )
    assert OSError not in CORRUPTION_ERRORS, (
        "OSError (permisos, EIO, antivirus) no es corrupcion y no puede entrar en "
        "la ruta que regenera y sobrescribe (M6)"
    )
    assert Exception not in CORRUPTION_ERRORS and BaseException not in CORRUPTION_ERRORS, (
        "la tupla no puede contener Exception/BaseException: seria el bug del ciclo 15"
    )

    # --- la forma, fila a fila, con .bak sano ------------------------------
    filas = (
        ('{"profiles": "texto"}', "str", "profiles no es un mapa"),
        ('{"profiles": {"x": 123}}', "int", "un valor de profiles no es un mapa"),
        ('{"profiles": {"x": []}}', "list", "un valor de profiles no es un mapa"),
    )
    for contenido, tipo_real, que in filas:
        directorio = tempfile.mkdtemp(prefix="wopt_t030_p4_")
        ruta = os.path.join(directorio, "profiles.json")
        try:
            _escribir(ruta, contenido)
            _escribir(ruta + ".bak", json.dumps(_BAK_SANO, ensure_ascii=False))
            principal_antes = _bytes_de(ruta)
            bak_antes = _bytes_de(ruta + ".bak")

            # 1) el mensaje dice el TIPO REAL, no un AttributeError generico
            fallo = _capturar(lambda: PackService._read_json(None, ruta))
            assert isinstance(fallo, PerfilCorruptoError), (
                f"{contenido}: `_read_json` lanzo {fallo!r} en vez de "
                "PerfilCorruptoError; sin la guarda de forma, ese AttributeError "
                "sale de `PackService.__init__` y la app no arranca"
            )
            assert tipo_real in str(fallo), (
                f"{contenido}: el mensaje {str(fallo)!r} no dice el tipo real "
                f"({tipo_real})"
            )

            # 2) con .bak sano, `PackService()` arranca y recupera
            servicio = PackService(data_path=ruta)
            packs = servicio.get_all_packs()
            assert "salvado" in packs, (
                f"{que} con .bak sano: la recuperacion devolvio {sorted(packs)}"
            )
            assert packs["salvado"].apps == ["salvado.exe"], (
                f"los apps del pack recuperado llegaron vacios: {packs['salvado'].apps}"
            )
            assert packs["gaming"].is_gaming is True, "el pack gaming debe seguir marcado"
            assert _bytes_de(ruta) == principal_antes, (
                f"{que}: recuperar reescribio el principal; la recuperacion no escribe"
            )
            assert _bytes_de(ruta + ".bak") == bak_antes, (
                f"{que}: el .bak sano fue tocado al recuperar"
            )
        finally:
            shutil.rmtree(directorio, ignore_errors=True)
    print("La forma legacy no tumba la app OK (P4).")


def test_todas_las_clases_de_corrupcion_se_recuperan():
    """TASK-030 / P5: las CUATRO clases de `CORRUPTION_ERRORS` se recuperan.

    M5 (reducir la tupla a `JSONDecodeError`) sobrevivio en el ciclo #17 porque
    NINGUN test miraba `ValidationError`, `TypeError` ni `UnicodeDecodeError`:
    las tres YA estaban en `pack_service.py:16`. El arreglo de este punto es de
    test, no de codigo. Cada fila mata su propia eliminacion parcial, asi que la
    tupla queda fijada clase por clase y no "en bloque".

    Cada fila comprueba dos cosas distintas:
      * que el fixture produzca EXACTAMENTE la clase que la fila declara (si no,
        la fila probaria otra cosa y el mutantsuilviviria);
      * que con esa clase el servicio arranque desde el `.bak` sin escribir nada.
    """
    print("Testing las 4 clases de corrupcion (P5)...")
    import json
    import shutil
    import tempfile
    from woptimizer.services import pack_service as ps
    from woptimizer.services.pack_service import PackService

    filas = (
        ("JSONDecodeError", '{"packs": {"x": ', None),
        ("TypeError", "[1, 2, 3]", None),
        ("UnicodeDecodeError", None, b'{\xff\xfe"packs":{}}'),
        # TASK-031 iteracion 2: `"id"` tiene que ser IGUAL a la clave. Antes ponia
        # `"id": "a"` con clave `"x"`, y con la guarda de identidad (L10) esa fila
        # dejaba de producir la clase que declara y producia `PerfilCorruptoError`:
        # la fila probaba otra cosa. El fallo de la fila es `default_action`, asi
        # que el resto del registro tiene que ser valido de verdad.
        ("ValidationError",
         '{"packs": {"x": {"id": "x", "name": "b", "default_action": "BOOM"}}}', None),
    )
    declaradas = {c.__name__ for c in ps.CORRUPTION_ERRORS}
    for nombre, texto, binario in filas:
        assert nombre in declaradas, (
            f"{nombre} no esta en CORRUPTION_ERRORS "
            f"({sorted(declaradas)}); esa clase de fallo regeneraria los packs en "
            "silencio, sin intentar el .bak"
        )
        directorio = tempfile.mkdtemp(prefix="wopt_t030_p5_")
        ruta = os.path.join(directorio, "profiles.json")
        try:
            _escribir(ruta, binario if binario is not None else texto)
            # 1) el fixture tiene que producir la clase que la fila declara
            fallo = _capturar(lambda: PackService._read_json(None, ruta))
            assert fallo is not None, (
                f"el fixture de la fila {nombre} no produce ningun error: "
                "probaria otra cosa y el mutante sobreviviria"
            )
            assert fallo.__class__.__name__ == nombre, (
                f"el fixture declarado como {nombre} produce "
                f"{fallo.__class__.__name__}: {fallo!r}"
            )
            assert fallo.__class__ in ps.CORRUPTION_ERRORS, (
                f"{nombre} no esta en la tupla de clasificacion"
            )

            # 2) con .bak sano, arranca y recupera sin escribir nada
            _escribir(ruta + ".bak", json.dumps(_BAK_SANO, ensure_ascii=False))
            principal_antes = _bytes_de(ruta)
            bak_antes = _bytes_de(ruta + ".bak")
            servicio = PackService(data_path=ruta)
            packs = servicio.get_all_packs()
            assert "salvado" in packs, (
                f"{nombre}: la recuperacion desde el .bak devolvio {sorted(packs)}"
            )
            assert packs["salvado"].apps == ["salvado.exe"], (
                f"{nombre}: los apps del pack recuperado llegaron vacios: "
                f"{packs['salvado'].apps}"
            )
            assert packs["gaming"].is_gaming is True, (
                f"{nombre}: el pack gaming debe seguir marcado tras recuperar"
            )
            assert _bytes_de(ruta) == principal_antes, (
                f"{nombre}: la recuperacion reescribio el principal; recuperar NO "
                "escribe nada (si no, el .bak bueno se pierde en el siguiente save)"
            )
            assert _bytes_de(ruta + ".bak") == bak_antes, (
                f"{nombre}: el .bak sano fue tocado al recuperar"
            )
        finally:
            shutil.rmtree(directorio, ignore_errors=True)
    print("Las 4 clases de corrupcion OK (P5).")


def test_oserror_de_lectura_no_es_corrupcion():
    """TASK-030 / P6: un `OSError` de LECTURA se propaga y no toca el `.bak`.

    Escenario: el antivirus bloquea el principal y hay un `.bak` sano. Lo
    correcto es PROPAGAR el `PermissionError`: el servicio no sabe si el
    principal tiene lo mismo que el backup, y "arrancar con el backup viejo en
    silencio" es exactamente como el usuario pierde la configuracion sin que
    nadie le avise.

    MATA: M6 (`OSError` readmitido en `CORRUPTION_ERRORS`: arrancaba en silencio
    con los datos viejos del backup) y M7 (`except Exception` en `load()`: el
    bug del ciclo 15, la misma perdida de configuracion).

    Por que se inyecta y no se usa el sistema de ficheros: en Windows
    `os.chmod(0o400)` NIEGA LA ESCRITURA pero la LECTURA sigue permitida
    (medido), y negar lectura de verdad exigiria ACL (`icacls` = `subprocess`,
    prohibido por la Trampa #9). Se probaron tres escenarios solo-filesystem y
    ninguno distinguia M6 (proposal.md 2.3). La costura de parseo es la unica
    forma honesta.
    """
    print("Testing que un OSError de lectura no es corrupcion (P6)...")
    import json
    import shutil
    import tempfile
    from woptimizer.services import pack_service as ps
    from woptimizer.services.pack_service import PackService

    real_load = json.load

    def load_bloqueado(fp, *args, **kwargs):
        """Solo el PRINCIPAL: el `.bak` tiene que quedar intacto y legible."""
        if os.path.normcase(getattr(fp, "name", "")) == os.path.normcase(ruta):
            raise PermissionError("el antivirus tiene el principal bloqueado")
        return real_load(fp, *args, **kwargs)

    directorio = tempfile.mkdtemp(prefix="wopt_t030_p6_")
    ruta = os.path.join(directorio, "profiles.json")
    try:
        _escribir(ruta, '{"packs": {"x": ')          # entraria en la ruta de recuperacion
        _escribir(ruta + ".bak", json.dumps(_BAK_SANO, ensure_ascii=False))
        principal_antes = _bytes_de(ruta)
        bak_antes = _bytes_de(ruta + ".bak")

        with _doble_en(ps, json=_ModuloDoble(json, load=load_bloqueado)):
            fallo = _capturar(lambda: PackService(data_path=ruta))

        assert isinstance(fallo, PermissionError), (
            "un OSError de lectura no es corrupcion: con un .bak sano, "
            "PackService() arranco en silencio (con los datos VIEJOS del backup o "
            f"regenerados) y el usuario cree que sus packs se han perdido. "
            f"M6/M7. Lo que paso: {fallo!r}"
        )
        assert _bytes_de(ruta) == principal_antes, (
            "el principal se reescribio pese a no poder leerse: un error de "
            "permisos no puede acabar en la ruta que regenera"
        )
        assert _bytes_de(ruta + ".bak") == bak_antes, (
            "el .bak sano fue tocado al no poder leer el principal: la unica copia "
            "buena no puede depender de una lectura fallida"
        )
        # Sin el doble, el .bak sigue siendo la copia sana: se prueba, no se supone.
        recuperado = PackService(data_path=ruta).get_all_packs()
        assert "salvado" in recuperado and recuperado["salvado"].apps == ["salvado.exe"], (
            f"el .bak dejo de ser recuperable: {sorted(recuperado)}"
        )
    finally:
        shutil.rmtree(directorio, ignore_errors=True)
    print("Un OSError de lectura no es corrupcion OK (P6).")


def test_attribute_error_ajeno_no_es_corrupcion():
    """TASK-030 / P7: un `AttributeError` AJENO se propaga; no es corrupcion.

    Se parchea `_read_json` para que lance un `AttributeError` de bug interno
    (el sintoma, no la forma validada) al leer el PRINCIPAL, con un `.bak` sano
    delante. Lo correcto es que salga: un bug tiene que verse en el log.

    MATA: M7 (`except Exception` en `load()`, el bug del ciclo 15) y **M9**, que
    es el "arreglo ingenuo" de meter `AttributeError` en `CORRUPTION_ERRORS`
    (proposal.md 3.3, salida A): con M9 el servicio se traga el bug, entra en la
    ruta de recuperacion y en el siguiente `save()` los packs que el usuario
    acaba de crear desaparecen.

    Complemento de P4: P4 dice que la FORMA validada SI es corrupcion; P7 dice
    que el sintoma NO lo es. Las dos mitades de la misma decision.
    """
    print("Testing que un AttributeError ajeno no es corrupcion (P7)...")
    import json
    import shutil
    import tempfile
    from woptimizer.services.pack_service import PackService

    directorio = tempfile.mkdtemp(prefix="wopt_t030_p7_")
    ruta = os.path.join(directorio, "profiles.json")
    try:
        _escribir(ruta, '{"packs": {"x": "esto no es un pack"}}')
        _escribir(ruta + ".bak", json.dumps(_BAK_SANO, ensure_ascii=False))
        principal_antes = _bytes_de(ruta)
        bak_antes = _bytes_de(ruta + ".bak")

        original = PackService._read_json

        def _read_json_con_bug(self, path):
            if os.path.normcase(path) == os.path.normcase(ruta):
                raise AttributeError("bug interno: None no tiene .get('packs')")
            return original(self, path)

        PackService._read_json = _read_json_con_bug
        try:
            fallo = _capturar(lambda: PackService(data_path=ruta))
        finally:
            PackService._read_json = original

        assert isinstance(fallo, AttributeError), (
            "un AttributeError que no es la forma validada debe PROPAGAR: tragarselo "
            "convierte un bug de una linea en 'el archivo esta roto' -> recuperacion "
            "desde el .bak -> y el siguiente save() borra los packs del usuario "
            f"(M7, M9). Lo que paso: {fallo!r}"
        )
        assert "bug interno" in str(fallo), f"el fallo no es el inyectado: {fallo!r}"
        assert _bytes_de(ruta) == principal_antes, (
            "el principal se reescribio pese al bug interno: no se entra en la ruta "
            "que regenera"
        )
        assert _bytes_de(ruta + ".bak") == bak_antes, (
            "el .bak sano fue tocado: la unica copia buena no puede depender de una "
            "lectura que fallo"
        )
    finally:
        shutil.rmtree(directorio, ignore_errors=True)
    print("Un AttributeError ajeno no es corrupcion OK (P7).")


# --- TASK-031: sondas L1-L7 -----------------------------------------------
# "JSON valido pero ilegible para el servicio": la fila A de la matriz de
# proposal.md 0.1. `name: 7` lo acepta `json.load` y lo rechaza Pydantic, que es
# exactamente la divergencia entre las DOS puertas que tenia el servicio.
_HOJA_MALFORMADA = '{"packs": {"mio": {"id": "mio", "name": 7}}}'

# Un `.bak` sano que trae `salvado` Y `otro`: para L7, cuya pregunta es si un
# pack que solo existia bajo la clave `profiles` sobrevive al ciclo completo.
_BAK_CON_OTRO = {
    "packs": {
        "salvado": {"id": "salvado", "name": "Salvado", "apps": ["salvado.exe"]},
        "otro": {"id": "otro", "name": "Otro", "apps": ["otro.exe"]},
        "gaming": {"id": "gaming", "name": "Gaming", "is_gaming": True,
                   "apps": ["chrome.exe"]},
    }
}


def test_la_rotacion_usa_la_misma_puerta_que_load():
    """TASK-031 / L1: la rotacion y `load()` tienen que DECIDIR LO MISMO.

    MATA L-M1 (`_rotate_backup()` vuelve a `json.load`, o a `pass`): con la
    guarda puesta solo en `json.load`, un `name: 7` es JSON valido y por tanto
    "sano": la rotacion copia el principal corrupto ENCIMA del `.bak` bueno y la
    unica copia sana desaparece. Medido en el estado previo: el `.bak` sano
    moria en 7 de 8 escenarios de la matriz de `proposal.md` 0.1.

    POR QUE LA ASERCION ES "el `.bak` SIGUE SIENDO LEGIBLE" y no "existe": si el
    mutante lo sustituye, la lectura falla con `ValidationError` DENTRO de la
    comprobacion, que es un fallo del SISTEMA y no una excepcion del test. Un
    `assert not os.path.exists(bak)` seria verde por la razon equivocada: basta
    con que el mutante borre el fichero en vez de pisarlo.

    La escritura que dispara la rotacion es REAL (el usuario crea un pack), y no
    la de `load()`: con E-3 el arranque ya no escribe, asi que un espia del
    arranque no veria la rotacion nunca. Por eso L3 y L1 se necesitan los dos.
    """
    print("Testing que la rotacion usa la misma puerta que load (L1)...")
    import json
    import shutil
    import tempfile
    from woptimizer.services.pack_service import PackService

    directorio = tempfile.mkdtemp(prefix="wopt_t031_l1_")
    ruta = os.path.join(directorio, "profiles.json")
    try:
        _escribir(ruta, _HOJA_MALFORMADA)
        _escribir(ruta + ".bak", json.dumps(_BAK_SANO, ensure_ascii=False))
        bak_antes = _bytes_de(ruta + ".bak")

        servicio = PackService(data_path=ruta)
        assert servicio.recuperado_de_backup is True, (
            "el principal es ilegible para el servicio y hay un .bak sano: no se "
            "recupero, asi que la mitad de la asercion probaria otra cosa"
        )
        assert "salvado" in servicio.get_all_packs(), (
            f"la recuperacion devolvio {sorted(servicio.get_all_packs())}"
        )

        # La rotacion se ejecuta aqui, con el principal corrupto AUN EN DISCO.
        servicio.create_user_pack("nuevo", "Nuevo", ["nuevo.exe"])

        assert _bytes_de(ruta + ".bak") == bak_antes, (
            "el .bak sano cambio de bytes al rotar: se le copio encima el "
            "principal, que es JSON valido pero ilegible para el servicio. "
            "`_rotate_backup()` tiene que usar la MISMA puerta que `load()` "
            "(`_read_json`), no `json.load` (L-M1)"
        )
        fallo = _capturar(lambda: PackService._read_json(None, ruta + ".bak"))
        assert fallo is None, (
            f"el .bak ya no es legible (LEERLO da {fallo!r}): la unica copia "
            "buena se ha perdido y desde ahi no hay de donde recuperar"
        )
        bak = PackService._read_json(None, ruta + ".bak")
        assert "salvado" in bak.packs, (
            f"el .bak deberia seguir teniendo el pack recuperado: {sorted(bak.packs)}"
        )
        assert "nuevo" not in bak.packs, (
            "el .bak se refresco con la version recien escrita: el .bak es la "
            "version ANTERIOR, no un espejo de la actual"
        )
    finally:
        shutil.rmtree(directorio, ignore_errors=True)
    print("La rotacion usa la misma puerta que load OK (L1).")


def test_la_hoja_malformada_se_clasifica():
    """TASK-031 / L2: una hoja que viola el esquema es CORRUPCION. En las DOS ramas.

    MATA L-M2 (volver a la construccion a mano `Pack(id=k, name=v.get("label"),
    apps=..., is_favorite=..., is_gaming=False, default_action="start")` en la
    rama legacy) y L-M2b (quitar `traducido["id"] = k`), ambos Medidos por el
    mutation-auditor de la iteracion 2: el primero es el grande, y el segundo
    NO se ejercia (la fixture traia `"id"` de serie, asi que la linea era codigo
    muerto y su mutacion-sobreviviente era INVISIBLE). La fixture legacy de este
    test ahora quita `id` a proposito, que es como es un registro legacy de
    verdad, y la sonda L10 afirma ademas sobre el CONTENIDO (`pack.id == clave`).

    Medido en el estado anterior: la rama legacy devolvia `AppData` VALIDO y
    cargaba el pack con `keepers == []` en cuatro de las seis filas, y con las
    otras dos lanzaba el Pydantic CRUDO, cuyo texto no nombra el pack. La razon
    de que eso sea un problema de SEGURIDAD y no de cosmos: `keepers` es la
    lista de procesos PROTEGIDOS del Gaming Mode, y normalizarla a `[]` desarma
    la proteccion sin avisar (`gaming_service.py:24`).

    La septima fila es `is_gaming: "true"` y SOLO en la rama moderna, porque en
    la legacy `is_gaming` se FUERZA a `False` por diseño (ahi no puede venir de
    ninguna parte). Esa fila es L-M8d: sin `strict=True` en el campo, Pydantic
    coacciona `"true"` a `True` y el pack desaparece de `get_user_packs()` y de
    `delete_pack` ("No se puede eliminar el pack de sistema"): invisible e
    indeletable, que es la familia de ladrillo que esta tarea evita.

    La asercion del TEXTO (campo + pack + tipo real) es la que impide que E-2 se
    "cumpla" dejando que Pydantic hable con su diagnostico de 14 lineas y una URL
    a la documentacion de Pydantic: quien repara el fichero es el usuario, con el
    bloc de notas delante.
    """
    print("Testing que la hoja malformada se clasifica (L2)...")
    import json
    import shutil
    import tempfile
    from pydantic import ValidationError
    from woptimizer.services.pack_service import (PackService, PerfilCorruptoError)

    # (campo, valor, tipo real, ramas en las que la fila existe). La ultima
    # columna NO es decorativa: en la rama legacy `is_gaming` se fuerza a False,
    # asi que la fila solo puede mirarse en la moderna (L-M8d).
    #
    # TASK-031 iteracion 3 (M4b): el VALOR de la fila tiene que ser un valor que
    # Pydantic COACCIONA en modo laxo, o la fila no puede distinguir `strict=True`
    # de `strict=False`. Medido: `"si"` se RECHAZA igual en los dos modos (no esta
    # en la lista de booleanos laxos de Pydantic v2), de modo que la fila
    # `is_favorite: "si"` era verde CON y SIN `strict=True`: un test que no puede
    # morir, y su mutacion-sobreviviente era invisible. `"true"` y `1` si se
    # coaccionan a `True`, asi que ahora estas dos filas matan `L-M4b`
    # (quitarle el `strict` a `is_favorite`).
    hojas = (
        ("keepers", "steam.exe", "str", ("moderna", "legacy")),
        ("target_categories", {"navegadores": 1}, "dict", ("moderna", "legacy")),
        ("apps", 3, "int", ("moderna", "legacy")),
        ("name", 7, "int", ("moderna", "legacy")),
        ("is_favorite", "true", "str", ("moderna", "legacy")),
        ("is_favorite", 1, "int", ("moderna", "legacy")),
        ("default_action", "PURGAR", "str", ("moderna", "legacy")),
        ("is_gaming", "true", "str", ("moderna",)),
    )
    for rama in ("moderna", "legacy"):
        for campo, valor, tipo_real, ramas in hojas:
            if rama not in ramas:
                continue
            hoja = {"id": "mio", "name": "Mio", "apps": ["a.exe"]}
            hoja[campo] = valor
            if rama == "moderna":
                principal = json.dumps({"packs": {"mio": hoja}}, ensure_ascii=False)
                clase_esperada = ValidationError
            else:
                # El registro legacy llama `name` como `label`; para que la fila
                # `name` rompa el MISMO campo, se mueve el valor ahi. Y `id` se
                # QUITA: un registro legacy no lleva `id` (su identidad es la
                # clave del mapa), asi que la linea `traducido["id"] = k` deja de
                # ser codigo muerto y su mutacion L-M2b pasa a morir aqui (L-M2b).
                registro = dict(hoja)
                if "name" in registro:
                    registro["label"] = registro.pop("name")
                registro.pop("id", None)
                principal = json.dumps({"profiles": {"mio": registro}},
                                       ensure_ascii=False)
                clase_esperada = PerfilCorruptoError
            etiqueta = f"[{rama}/{campo}]"

            directorio = tempfile.mkdtemp(prefix="wopt_t031_l2_")
            ruta = os.path.join(directorio, "profiles.json")
            try:
                _escribir(ruta, principal)
                _escribir(ruta + ".bak", json.dumps(_BAK_SANO, ensure_ascii=False))
                principal_antes = _bytes_de(ruta)
                bak_antes = _bytes_de(ruta + ".bak")

                fallo = _capturar(lambda: PackService._read_json(None, ruta))
                assert isinstance(fallo, clase_esperada), (
                    f"{etiqueta}: `_read_json` dio {fallo!r} en vez de "
                    f"{clase_esperada.__name__}; la hoja se carga como si valiera "
                    "y 'keepers' pasaria a ser una lista de caracteres, con el "
                    "Gaming Mode sin proteger NADA (L-M2)"
                )
                texto = str(fallo)
                assert campo in texto, (
                    f"{etiqueta}: el mensaje {texto!r} no nombra el CAMPO, que es "
                    "lo primero que hay que arreglar en el fichero"
                )
                assert "mio" in texto, (
                    f"{etiqueta}: el mensaje {texto!r} no nombra el PACK: con 20 "
                    "packs en el fichero, el diagnostico no dice cual"
                )
                if rama == "legacy":
                    assert "errors.pydantic.dev" not in texto and "\n" not in texto, (
                        f"{etiqueta}: sale el Pydantic crudo ({texto!r}); hay que "
                        "traducirlo a un mensaje de UNA linea (T-09.1)"
                    )
                    assert f"es {tipo_real}" in texto, (
                        f"{etiqueta}: el mensaje {texto!r} no dice el TIPO REAL "
                        f"({tipo_real})"
                    )
                else:
                    assert f"input_type={tipo_real}" in texto, (
                        f"{etiqueta}: el mensaje de Pydantic {texto!r} no dice el "
                        f"tipo real ({tipo_real})"
                    )

                servicio = PackService(data_path=ruta)
                packs = servicio.get_all_packs()
                assert "salvado" in packs and packs["salvado"].apps == ["salvado.exe"], (
                    f"{etiqueta}: con .bak sano la recuperacion devolvio "
                    f"{sorted(packs)}"
                )
                assert _bytes_de(ruta) == principal_antes, (
                    f"{etiqueta}: recuperar no escribe nada en el principal"
                )
                assert _bytes_de(ruta + ".bak") == bak_antes, (
                    f"{etiqueta}: el .bak sano fue tocado al recuperar"
                )
            finally:
                shutil.rmtree(directorio, ignore_errors=True)
    print("La hoja malformada se clasifica OK (L2).")


def test_load_no_escribe():
    """TASK-031 / L3: `load()` es de SOLO LECTURA en todas sus ramas.

    MATA L-M3 (`_ensure_gaming_pack()` vuelve a llamar a `save()`, o `load()`
    recupera su `self.save()`).

    Esta es la UNICA sonda que ata E-1 y E-3 entre si: con solo E-1 el `.bak` se
    seguiria destruyendo igual, un poco mas tarde, en cuanto `_ensure_gaming_pack()`
    volviera a guardar por un criterio nuevo. Medido en el estado previo: dentro
    de `load()` habia `save()=1` y `_rotate_backup()=1`.

    El contador de `save()` NO se contrasta con ningun umbral (0 es la
    definicion de "solo lectura", no un numero arbitrario): la evidencia de
    verdad son los BYTES del principal y del `.bak`, y el contador esta para que
    el fallo senale la puerta exacta y no "algo escribio".
    """
    print("Testing que load() no escribe (L3)...")
    import json
    import shutil
    import tempfile
    from woptimizer.services.pack_service import PackService

    escenarios = (
        ("regeneracion sin .bak", _HOJA_MALFORMADA, None),
        ("recuperacion con .bak sano", _HOJA_MALFORMADA, _BAK_SANO),
        ("valido sin pack gaming",
         '{"packs": {"salvado": {"id": "salvado", "name": "Salvado", "apps": ["s.exe"]}}}',
         None),
        ("fichero vacio", "{}", None),
    )
    for nombre, principal, bak in escenarios:
        directorio = tempfile.mkdtemp(prefix="wopt_t031_l3_")
        ruta = os.path.join(directorio, "profiles.json")
        try:
            _escribir(ruta, principal)
            if bak is not None:
                _escribir(ruta + ".bak", json.dumps(bak, ensure_ascii=False))
            principal_antes = _bytes_de(ruta)
            bak_antes = _bytes_de(ruta + ".bak") if os.path.exists(ruta + ".bak") else None

            llamadas = []
            original = PackService.save

            def save_contado(self, _original=original):
                llamadas.append(self.data_path)
                return _original(self)

            PackService.save = save_contado
            try:
                servicio = PackService(data_path=ruta)
            finally:
                PackService.save = original

            assert llamadas == [], (
                f"{nombre}: load() escribio {llamadas} sin que el usuario hubiera "
                "hecho nada. El arranque es la via por la que la rotacion machaca "
                "el .bak sano (L-M3)"
            )
            assert _bytes_de(ruta) == principal_antes, (
                f"{nombre}: load() cambio los bytes del principal"
            )
            if bak_antes is not None:
                assert _bytes_de(ruta + ".bak") == bak_antes, (
                    f"{nombre}: load() toco el .bak"
                )
            assert not os.path.exists(ruta + ".tmp"), (
                f"{nombre}: load() dejo un temporal"
            )
            # Y la app arranca igual: el pack gaming se asegura EN MEMORIA.
            assert servicio.get_all_packs()["gaming"].is_gaming is True, (
                f"{nombre}: sin escribir nada, la app tiene que funcionar con el "
                "pack gaming en memoria"
            )
        finally:
            shutil.rmtree(directorio, ignore_errors=True)
    print("load() no escribe OK (L3).")


def test_la_recuperacion_no_sobrescribe_el_bak():
    """TASK-031 / L4: recuperar NO refresca el `.bak`. Ni un byte.

    MATA L-M4 (en la ruta de recuperacion un `save()` antes de leer el `.bak`, o
    rotar "para dejar el backup al dia").

    Sin la comparacion de BYTES, "no sobrescribir" y "sobrescribir con lo mismo"
    son indistinguibles, y L4 no mataria a L-M4. Y sin la segunda mitad
    (`is_favorite` del `.bak`), el mutante que reescribiese el `.bak` con una
    copia IDENTICA del contenido pasaria el test sin que nada se detectara.

    La ultima asercion es la que impide el "verde por la razon equivocada": si la
    escritura real no ocurriera, las dos anteriores serian ciertas por no hacer
    nada.
    """
    print("Testing que la recuperacion no sobrescribe el .bak (L4)...")
    import json
    import shutil
    import tempfile
    from woptimizer.services.pack_service import PackService

    directorio = tempfile.mkdtemp(prefix="wopt_t031_l4_")
    ruta = os.path.join(directorio, "profiles.json")
    try:
        _escribir(ruta, _HOJA_MALFORMADA)
        _escribir(ruta + ".bak", json.dumps(_BAK_SANO, ensure_ascii=False))
        bak_antes = _bytes_de(ruta + ".bak")

        servicio = PackService(data_path=ruta)
        assert "salvado" in servicio.get_all_packs(), (
            f"no se recupero del .bak: {sorted(servicio.get_all_packs())}"
        )
        assert _bytes_de(ruta + ".bak") == bak_antes, (
            "recuperar toco el .bak: la recuperacion no escribe NADA"
        )

        # Escritura REAL del usuario. El principal que hay en disco sigue siendo
        # el corrupto, asi que no hay version anterior sana que rotar.
        servicio.set_favorite("salvado", True)

        assert _bytes_de(ruta + ".bak") == bak_antes, (
            "el .bak cambio de bytes tras guardar: se refresco con el estado en "
            "memoria. El .bak tiene que ser la ultima version BUENA, no un "
            "espejo de la actual (L-M4)"
        )
        bak = PackService._read_json(None, ruta + ".bak")
        assert bak.packs["salvado"].is_favorite is False, (
            "el .bak contiene la version recuperada: se roto 'para dejarlo al "
            "dia' y la ultima copia buena se perdio (L-M4)"
        )

        en_disco = PackService._read_json(None, ruta)
        assert en_disco.packs["salvado"].is_favorite is True, (
            "la escritura real no ocurrio: las aserciones sobre el .bak no "
            "probarian nada (verde por la razon equivocada)"
        )
    finally:
        shutil.rmtree(directorio, ignore_errors=True)
    print("La recuperacion no sobrescribe el .bak OK (L4).")


def test_sin_bak_legible_no_se_sobrescribe_el_principal():
    """TASK-031 / L5: sin `.bak` legible el fichero se queda EN DISCO, como estaba.

    MATA L-M5 (reponer `AppData()` + `_ensure_gaming_pack()` + `save()` en la
    ruta de recuperacion de `load()`).

    No es hipotetico: es la instalacion limpia y tambien un `.bak` ya destruido
    por la fila A de la matriz. Antes, esa ruta reESCRIBIA el fichero del usuario
    con un solo pack: una perdida irreversible y sin aviso. Ahora la perdida es
    REVERSIBLE, y la app arranca igual con el pack `gaming` en memoria.

    La segunda mitad (el pack queda MARCADO) es la que evita que la recuperacion
    siga siendo silenciosa por otro camino: sin marcar, el usuario ve cero packs
    y no puede saber si los perdio o nunca los tuvo (Trampa #14).
    """
    print("Testing que sin .bak legible no se sobrescribe el principal (L5)...")
    import shutil
    import tempfile
    from woptimizer.services.pack_service import PackService

    directorio = tempfile.mkdtemp(prefix="wopt_t031_l5_")
    ruta = os.path.join(directorio, "profiles.json")
    try:
        _escribir(ruta, _HOJA_MALFORMADA)          # sin .bak a proposito
        principal_antes = _bytes_de(ruta)

        servicio = PackService(data_path=ruta)

        assert _bytes_de(ruta) == principal_antes, (
            "el fichero del usuario se reescribio sin .bak legible. Antes load() "
            "hacia AppData() + _ensure_gaming_pack() + save(), y dejaba el "
            "fichero con un SOLO pack y sin avisar. Sin .bak no hay nada con que "
            "sustituirlo: el fichero se queda EN DISCO tal cual para que el "
            "usuario o una version posterior lo reparen (L-M5)"
        )
        assert not os.path.exists(ruta + ".bak"), (
            "se creo un .bak a partir de un principal ilegible: es la unica copia "
            "que tendria el usuario y no vale nada"
        )
        assert not os.path.exists(ruta + ".tmp"), "load() dejo un temporal"

        packs = servicio.get_all_packs()
        assert packs["gaming"].is_gaming is True, (
            "sin nada recuperable la app tiene que arrancar igual: el pack gaming "
            "se asegura en memoria"
        )
        assert servicio.fichero_danado is True, (
            "un principal ilegible tiene que quedar MARCADO: si no, el usuario ve "
            "cero packs y no sabe si los perdio o nunca los tuvo"
        )
        assert servicio.recuperado_de_backup is False, (
            "no habia .bak: no se puede haber recuperado de el"
        )
        mensaje = servicio.mensaje_danado()
        assert mensaje and "mio" in mensaje, (
            f"el aviso para la UI no nombra el pack afectado: {mensaje!r}"
        )
    finally:
        shutil.rmtree(directorio, ignore_errors=True)
    print("Sin .bak legible no se sobrescribe el principal OK (L5).")


def test_un_campo_desconocido_no_es_corrupcion_y_no_se_borra():
    """TASK-031 / L6: un campo desconocido NO es corrupcion, y NO se borra.

    MATA L-M6 (`extra="forbid"`, o la whitelist de `isinstance` de la opcion (a)
    del encargo).

    ESTA ES LA SONDA QUE SEPARA LA OPCION (a) DE LA OPCION (b). Sin ella, "mas
    isinstance campo a campo" y "validar contra el modelo" producen el mismo
    comportamiento y el mutation-auditor no puede decir cual se ha implementado.

    Clasificarlo como corrupcion seria un error de DISENO, no de robustez: es el
    unico mecanismo que hace el formato compatible hacia delante, y es justo
    cuando mas hace falta, porque un `.bak` escrito por un build mas nuevo tiene
    que ser legible por uno mas viejo. Perder el campo, en cambio, es perder
    datos del usuario en silencio.
    """
    print("Testing que un campo desconocido no es corrupcion ni se borra (L6)...")
    import json
    import shutil
    import tempfile
    from woptimizer.services.pack_service import PackService

    directorio = tempfile.mkdtemp(prefix="wopt_t031_l6_")
    ruta = os.path.join(directorio, "profiles.json")
    try:
        hoja = {"id": "mio", "name": "Mio", "apps": ["a.exe"],
                "notas": "comprar la caja"}
        _escribir(ruta, json.dumps({"packs": {"mio": hoja}}, ensure_ascii=False))
        _escribir(ruta + ".bak", json.dumps(_BAK_SANO, ensure_ascii=False))
        bak_antes = _bytes_de(ruta + ".bak")

        servicio = PackService(data_path=ruta)

        assert servicio.fichero_danado is False, (
            "un campo que esta version no conoce se clasifico como corrupcion: "
            "eso hace que el fichero sano de un build mas nuevo se trato como "
            "roto, que es justo el momento en que el .bak hace falta (L-M6)"
        )
        assert servicio.recuperado_de_backup is False, (
            "se recupero del .bak: un campo desconocido no es motivo para tirar la "
            "version del usuario"
        )
        assert "mio" in servicio.get_all_packs(), (
            f"el pack mio desaparecio: {sorted(servicio.get_all_packs())}"
        )
        assert _bytes_de(ruta + ".bak") == bak_antes, "el .bak sano fue tocado"

        # Un guardado REAL: el campo tiene que SEGUIR en el fichero.
        servicio.set_favorite("mio", True)
        with open(ruta, encoding="utf-8") as fh:
            en_disco = json.load(fh)
        assert en_disco["packs"]["mio"].get("notas") == "comprar la caja", (
            f"el campo desconocido se borro en el primer save(): "
            f"{en_disco['packs']['mio']}. Perdio datos del usuario sin avisar (L-M6)"
        )
    finally:
        shutil.rmtree(directorio, ignore_errors=True)
    print("Un campo desconocido no es corrupcion ni se borra OK (L6).")


def test_packs_y_profiles_a_la_vez_es_corrupcion():
    """TASK-031 / L7: `packs` y `profiles` en el MISMO fichero es corrupcion.

    MATA L-M7 (quitar la condicion `'packs' not in raw_data`).

    Medido en el estado previo: con las dos claves se iba a la rama moderna,
    `profiles` se ignoraba como clave extra y el pack `otro` DESAPARECIA DEL
    DISCO en el primer `save()`, sin que nada se hubiera clasificado. Cualquier
    resolucion (migrar o descartar) borra packs en silencio, asi que aqui
    "corrupcion" y "normalizar" cuestan lo mismo y gana la opcion segura.

    La asercion que muere es "el pack `otro` sigue en el fichero DESPUES del
    `save()`", que es donde la perdida es observable.
    """
    print("Testing que packs y profiles a la vez es corrupcion (L7)...")
    import json
    import shutil
    import tempfile
    from woptimizer.services.pack_service import (PackService, PerfilCorruptoError)

    directorio = tempfile.mkdtemp(prefix="wopt_t031_l7_")
    ruta = os.path.join(directorio, "profiles.json")
    try:
        hoja = {"id": "mio", "name": "Mio", "apps": ["a.exe"]}
        perfil = {"label": "Otro", "apps": ["otro.exe"]}
        _escribir(ruta, json.dumps({"packs": {"mio": hoja},
                                    "profiles": {"otro": perfil}},
                                   ensure_ascii=False))
        _escribir(ruta + ".bak", json.dumps(_BAK_CON_OTRO, ensure_ascii=False))
        bak_antes = _bytes_de(ruta + ".bak")

        fallo = _capturar(lambda: PackService._read_json(None, ruta))
        assert isinstance(fallo, PerfilCorruptoError), (
            f"un fichero con 'packs' Y 'profiles' se leyo sin clasificar: {fallo!r}. "
            "La rama moderna ignoraba 'profiles' como clave extra y el pack `otro` "
            "desaparecia DEL DISCO en el primer save(), sin que nada se hubiera "
            "clasificado antes (L-M7)"
        )
        texto = str(fallo)
        assert "packs" in texto and "profiles" in texto, (
            f"el mensaje {texto!r} no nombra las DOS claves en conflicto: sin eso "
            "no se sabe cual sobra"
        )

        servicio = PackService(data_path=ruta)
        packs = servicio.get_all_packs()
        assert "salvado" in packs and "otro" in packs, (
            f"con .bak sano la recuperacion devolvio {sorted(packs)}: los dos "
            "packs tienen que sobrevivir"
        )
        assert _bytes_de(ruta + ".bak") == bak_antes, (
            "el .bak sano fue tocado al recuperar"
        )

        servicio.set_favorite("salvado", True)
        with open(ruta, encoding="utf-8") as fh:
            en_disco = json.load(fh)
        assert "otro" in en_disco["packs"] and "salvado" in en_disco["packs"], (
            f"tras el save() solo quedan {sorted(en_disco['packs'])}: el pack "
            "`otro` se ha perdido del disco (L-M7)"
        )
    finally:
        shutil.rmtree(directorio, ignore_errors=True)
    print("packs y profiles a la vez es corrupcion OK (L7).")


# --- TASK-031 iteracion 2: sondas L8-L10 ------------------------------------
# Un `.bak` con keepers DE VERDAD, para L9: la pregunta no es solo "se clasifica",
# es que clasificar RECUPERE los procesos protegidos en vez de normalizarlos a
# `[]` (que es lo que desarma el anti-brick y lo que `proposal.md` 3 rechazo).
_BAK_CON_KEEPERS = {
    "packs": {
        "salvado": {"id": "salvado", "name": "Salvado", "apps": ["salvado.exe"],
                    "keepers": ["steam.exe", "discord.exe"]},
        "gaming": {"id": "gaming", "name": "Gaming", "is_gaming": True,
                   "apps": ["chrome.exe"]},
    }
}

# Campos extra LEGITIMOS (o plausibles) que la politica de "error de escritura"
# tiene que DEJAR EN PAZ. El mas cercano a una clave real es `note` a distancia 2
# de `name`, asi que este grupo es el que mata un umbral de 2 (mutacion L-M8f).
_EXTRAS_LEGITIMOS = (
    ("notas", "comprar la caja"),
    ("note", "traer el cargador"),
    ("color", "#ff0000"),
    ("tags", ["estudio"]),
    ("hotkey", "ctrl+1"),
    ("version", 2),
    ("emoji", "X"),
    ("orden", 1),
    ("keep", ["steam.exe"]),
    ("description", "notas largas"),
)


def test_la_raiz_mal_escrita_no_destruye_los_packs():
    """TASK-031 iteracion 2 / L8: una RAIZ mal escrita NO puede costar los packs.

    MATA L-M6c (`extra="ignore"` SOLO en `AppData`) y L-M8a (clasificar la raiz
    mal escrita como corrupcion). Las dos son la MISMA perdida de datos vista por
    dos puertas, y el mutation-auditor de la iteracion 1 dio FAIL porque la linea
    `extra="allow"` de `AppData` era PORTANTE y no tenia ni una sonda.

    MEDIDO en el estado anterior (y medido otra vez aqui, con la mutacion puesta):
    un `profiles.json` cuya raiz esta mal escrita (`{"perfiles": ...}`,
    `{"packs2": ...}`) arranca, `load()` ve CERO packs, y el PRIMER `save()` real
    del usuario deja el fichero como `{"packs": ...}`: los packs del usuario
    desaparecen del disco, sin aviso y de forma irreversible.

    POR QUE EL TEST AFIRMA SOBRE BYTES Y NO SOBRE "el pack se ve": con cero packs en
    memoria no hay nada que mirar en memoria. Lo unicoObservable es el FICHERO. Y
    lo que se compara es el subarbol del usuario byte a byte (mismo `json.dumps` con
    `sort_keys` a los dos lados), porque el `indent=4` del escritor es cosa suya y
    no debe formar parte del contrato.

    POR QUE UNA RAIZ MAL ESCRITA NO ES CORRUPCION (la decision, con su coste):
    clasificarla seria PEOR. En la ruta sin `.bak`, `load()` hace
    `self._data = AppData()` (TASK-031, L5), asi que lo legible se tira y el
    siguiente `save()` publicaria `{"packs": {"gaming": ...}}`: los packs del
    usuario se perderian IGUAL y ADEMAS habria un aviso que no evita nada. Con
    `extra="allow"` la raiz desconocida se conserva como dato y sobrevive a todos
    los guardados. El COSTE, declarado y no resuelto: el arranque ve cero packs sin
    avisar (deuda en `data-models.md` 4.4 y `tasks.md` T-18.3). La asercion
    `fichero_danado is False` la fija para que ese coste solo se cambie a proposito.
    """
    print("Testing que la raiz mal escrita no destruye los packs (L8)...")
    import json
    import shutil
    import tempfile
    from woptimizer.services.pack_service import PackService

    packs_del_usuario = {
        "mio": {"id": "mio", "name": "Mio", "apps": ["mio.exe"]},
        "otro": {"id": "otro", "name": "Otro", "apps": ["otro.exe"]},
    }
    for raiz in ("perfiles", "packs2", "paquets", "Packs"):
        for con_bak in (False, True):
            etiqueta = f"[{raiz}/{'con' if con_bak else 'sin'} .bak]"
            directorio = tempfile.mkdtemp(prefix="wopt_t031_l8_")
            ruta = os.path.join(directorio, "profiles.json")
            try:
                _escribir(ruta, json.dumps({raiz: packs_del_usuario},
                                           ensure_ascii=False))
                if con_bak:
                    _escribir(ruta + ".bak",
                              json.dumps(_BAK_SANO, ensure_ascii=False))
                principal_antes = _bytes_de(ruta)
                bak_antes = _bytes_de(ruta + ".bak") if con_bak else None

                servicio = PackService(data_path=ruta)

                assert _bytes_de(ruta) == principal_antes, (
                    f"{etiqueta}: arrancar toco el fichero del usuario"
                )
                assert servicio.fichero_danado is False, (
                    f"{etiqueta}: una raiz mal escrita se clasifico como "
                    f"corrupcion. En la ruta sin .bak eso hace `self._data = "
                    f"AppData()` y el siguiente guardado publica "
                    f"{{'packs': ...}}: los packs del usuario se pierden IGUAL, y "
                    f"con un aviso de encima (L-M8a)"
                )
                assert servicio.recuperado_de_backup is False, (
                    f"{etiqueta}: se consulto el .bak sin que hubiera nada que "
                    f"clasificar: la raiz mal escrita no es corrupcion, asi que el "
                    f"`.bak` sano no se toca (L-M8a)"
                )
                if con_bak:
                    assert _bytes_de(ruta + ".bak") == bak_antes, (
                        f"{etiqueta}: arrancar toco el .bak sano: `load()` es de "
                        f"solo lectura con cualquier principal (L-M3)"
                    )

                # Escritura REAL del usuario. Esta es la que destruye los packs si
                # la raiz desconocida no sobrevive al ciclo carga -> guarda.
                servicio.create_user_pack("nuevo", "Nuevo", ["nuevo.exe"])

                with open(ruta, encoding="utf-8") as fh:
                    en_disco = json.load(fh)
                assert raiz in en_disco, (
                    f"{etiqueta}: la raiz {raiz!r} desaparece del disco tras el "
                    f"save(). En el fichero quedan {sorted(en_disco)}: los packs "
                    f"del usuario se han perdido y no hay forma de recuperarlos "
                    f"(L-M6c)"
                )
                assert (json.dumps(en_disco[raiz], sort_keys=True,
                                   ensure_ascii=False)
                        == json.dumps(packs_del_usuario, sort_keys=True,
                                      ensure_ascii=False)), (
                    f"{etiqueta}: lo que queda bajo {raiz!r} no es lo que el "
                    f"usuario escribio: {en_disco[raiz]}"
                )
                assert "nuevo" in en_disco.get("packs", {}), (
                    f"{etiqueta}: el pack nuevo no se guardo: la escritura real no "
                    f"ocurrio y el resto de aserciones no probarian nada"
                )
                if con_bak:
                    # El principal es LEGIBLE (la raiz mal escrita se lee), asi que
                    # la rotacion si ocurre y lo que copia es la version ANTERIOR
                    # del fichero del usuario, byte a byte. No es un `.bak` del
                    # "estado recuperado": es una rotacion real (L4).
                    assert _bytes_de(ruta + ".bak") == principal_antes, (
                        f"{etiqueta}: tras guardar, el .bak deberia ser la version "
                        f"ANTERIOR del principal, no el estado recien escrito"
                    )
            finally:
                shutil.rmtree(directorio, ignore_errors=True)
    print("La raiz mal escrita no destruye los packs OK (L8).")


def test_un_error_de_escritura_no_es_un_campo_desconocido():
    """TASK-031 iteracion 2 / L9: un campo que PARECE un error de escritura es
    CORRUPCION; un campo que no se parece a nada se queda como compatible hacia
    delante. Las dos mitades del mismo contrato.

    MATA L-M8b (quitar `_colision_de_tecla` / `_vigilar_hojas`) y L-M8f (subir el
    umbral de "una pulsacion" a dos, que es el desbordamiento clasico de un filtro
    de similitud).

    MEDIDO en el estado anterior: con `extra="allow"`, un `"keeper": [...]` se
    aceptaba como campo desconocido y `keepers` se quedaba en `[]` EN SILENCIO. El
    anti-brick queda desarmado: "Preparar Gaming Mode" mata lo que el usuario
    escribio para que lo protegiera. Ese es el ladrillo que `proposal.md` 3 dice
    que es inaceptable, y pasaba por los doce escenarios del auditor.

    POR QUE "parecido" NO es un fuzzy: la lista es CERRADA (los campos que esta
    version conoce) y el umbral es UNA pulsacion (distancia de edicion 1 sobre el
    nombre entero). La segunda mitad del test lo mide con 10 campos extra
    legitimos: el mas cercano a una clave real es `note` a distancia 2 de `name`,
    asi que un umbral de 2 ya rechazaria un campo de verdad (L-M8f).

    Y POR QUE la asercion es "se recupera del .bak CON keepers", no solo "se
    clasifica": la alternativa rechazada era normalizar a `[]`, y eso tambien
    "cargaba" el fichero. Lo que se vigila es que los procesos protegidos VOLVER.
    """
    print("Testing que un error de escritura no es un campo desconocido (L9)...")
    import json
    import shutil
    import tempfile
    from woptimizer.services.pack_service import (PackService, PerfilCorruptoError)

    # (campo escrito por el usuario, clave conocida que queda sin leerse)
    colisiones = (
        ("keeper", "keepers"),
        ("keeppers", "keepers"),
        (" keepers", "keepers"),
        ("app", "apps"),
        ("is_favorit", "is_favorite"),
        ("default_actions", "default_action"),
        ("is_gamingg", "is_gaming"),
        # TASK-031 iteracion 3 (M13): estas dos filas son las que matan la
        # mutacion "`_normalizar_clave` es la identidad". En BRUTO estan a 11 y
        # a 2 de distancia de su clave, asi que sin la normalizacion (minusculas
        # y guiones) no colisionarian por distancia: las agarra el atajo de
        # coincidencia EXACTA sobre la clave normalizada. "El plural y las
        # mayusculas no se detectan" no es una opinion: son 11 y 2 pulsaciones.
        ("IS-FAVORITE", "is_favorite"),
        ("IS_GAMING", "is_gaming"),
    )
    for rama in ("moderna", "legacy"):
        for campo, sombreada in colisiones:
            etiqueta = f"[{rama}/{campo}]"
            registro = {"name": "Mio", "apps": ["a.exe"], campo: ["steam.exe"]}
            if rama == "moderna":
                registro["id"] = "mio"
                principal = json.dumps({"packs": {"mio": registro}},
                                       ensure_ascii=False)
            else:
                registro["label"] = registro.pop("name")
                principal = json.dumps({"profiles": {"mio": registro}},
                                       ensure_ascii=False)

            directorio = tempfile.mkdtemp(prefix="wopt_t031_l9_")
            ruta = os.path.join(directorio, "profiles.json")
            try:
                _escribir(ruta, principal)
                _escribir(ruta + ".bak",
                          json.dumps(_BAK_CON_KEEPERS, ensure_ascii=False))
                principal_antes = _bytes_de(ruta)
                bak_antes = _bytes_de(ruta + ".bak")

                fallo = _capturar(lambda: PackService._read_json(None, ruta))
                assert isinstance(fallo, PerfilCorruptoError), (
                    f"{etiqueta}: {campo!r} se acepto como campo desconocido y "
                    f"{sombreada!r} se queda en su valor por defecto. En el Gaming "
                    f"Mode eso desarma la proteccion sin avisar (L-M8b); se leyo "
                    f"{fallo!r}"
                )
                texto = str(fallo)
                assert campo in texto, (
                    f"{etiqueta}: el mensaje {texto!r} no nombra el campo MAL "
                    f"ESCRITO, que es lo que hay que corregir en el fichero"
                )
                assert sombreada in texto, (
                    f"{etiqueta}: el mensaje {texto!r} no nombra la clave que "
                    f"queda SIN LEER ({sombreada!r}): sin eso el usuario no sabe "
                    f"que proteccion acaba de perder"
                )
                assert "mio" in texto, (
                    f"{etiqueta}: el mensaje {texto!r} no nombra el PACK"
                )
                assert "\n" not in texto and "errors.pydantic.dev" not in texto, (
                    f"{etiqueta}: sale el Pydantic crudo ({texto!r}); el mensaje va "
                    f"a un bloc de notas, no a un terminal"
                )

                servicio = PackService(data_path=ruta)
                assert servicio.fichero_danado is True, (
                    f"{etiqueta}: la clasificacion no es observable por la UI"
                )
                assert servicio.recuperado_de_backup is True, (
                    f"{etiqueta}: con .bak sano tiene que recuperarse"
                )
                packs = servicio.get_all_packs()
                assert "salvado" in packs, (
                    f"{etiqueta}: la recuperacion devolvio {sorted(packs)}"
                )
                assert packs["salvado"].keepers == ["steam.exe", "discord.exe"], (
                    f"{etiqueta}: la recuperacion trae keepers={packs['salvado'].keepers!r}: "
                    f"la eleccion de 'corrupcion' solo vale si los procesos "
                    f"PROTEGIDOS vuelven, no si se normalizan a []"
                )
                assert _bytes_de(ruta) == principal_antes, (
                    f"{etiqueta}: recuperar no escribe nada en el principal"
                )
                assert _bytes_de(ruta + ".bak") == bak_antes, (
                    f"{etiqueta}: el .bak sano fue tocado"
                )
            finally:
                shutil.rmtree(directorio, ignore_errors=True)

    # --- La mitad "no fuzzy": un campo que NO se parece a nada se conserva. ----
    for rama in ("moderna", "legacy"):
        etiqueta = f"[{rama}/extras legitimos]"
        registro = dict(_EXTRAS_LEGITIMOS)
        registro["name"] = "Mio"
        registro["apps"] = ["a.exe"]
        if rama == "moderna":
            registro["id"] = "mio"
            principal = json.dumps({"packs": {"mio": registro}}, ensure_ascii=False)
        else:
            registro["label"] = registro.pop("name")
            principal = json.dumps({"profiles": {"mio": registro}},
                                   ensure_ascii=False)

        directorio = tempfile.mkdtemp(prefix="wopt_t031_l9b_")
        ruta = os.path.join(directorio, "profiles.json")
        try:
            _escribir(ruta, principal)
            _escribir(ruta + ".bak",
                      json.dumps(_BAK_SANO, ensure_ascii=False))
            bak_antes = _bytes_de(ruta + ".bak")

            servicio = PackService(data_path=ruta)
            assert servicio.fichero_danado is False, (
                f"{etiqueta}: un campo que NO se parece a ninguna clave conocida se "
                f"clasifico como corrupcion. Eso hace que el fichero sano de un "
                f"build mas nuevo (un `.nota`, un `.tags`) se trate como roto, "
                f"que es justo el momento en que el .bak hace falta. 'note' esta a "
                f"distancia 2 de 'name': subir el umbral a 2 rompe esto (L-M8f)"
            )
            assert servicio.recuperado_de_backup is False, (
                f"{etiqueta}: no hay motivo para tirar la version del usuario"
            )
            assert _bytes_de(ruta + ".bak") == bak_antes, "el .bak sano fue tocado"

            servicio.create_user_pack("nuevo", "Nuevo", ["nuevo.exe"])
            with open(ruta, encoding="utf-8") as fh:
                en_disco = json.load(fh)
            guardados = en_disco["packs"]["mio"]
            for campo, valor in _EXTRAS_LEGITIMOS:
                assert campo in guardados, (
                    f"{etiqueta}: el campo legitimo {campo!r} desaparecio del "
                    f"fichero: quedan {sorted(guardados)}"
                )
                assert guardados[campo] == valor, (
                    f"{etiqueta}: el campo {campo!r} cambio de valor: "
                    f"{guardados[campo]!r} != {valor!r}"
                )
        finally:
            shutil.rmtree(directorio, ignore_errors=True)
    print("Un error de escritura no es un campo desconocido OK (L9).")


def test_la_clave_del_mapa_es_la_identidad_del_pack():
    """TASK-031 iteracion 2 / L10: la clave del mapa ES el id del pack.

    MATA L-M8c (quitar la guarda de identidad de `_vigilar_hojas`) y L-M2b
    (quitar `traducido["id"] = k`).

    MEDIDO en el estado anterior, y el hallazgo es del mutation-auditor de la
    iteracion 2: `{"packs": {"mi-clave": {"id": "otro-id", ...}}}` se cargaba SIN
    clasificar, y `pack_manager_view.py:100` indexa `get_all_packs()[pack.id]`, de
    modo que el desplegable de "accion por defecto" reventaba con
    `KeyError('otro-id')` y el pack tampoco aparecia en `get_user_packs()`. Un pack
    que la app no puede ni abrir ni borrar, sin un solo aviso.

    Se clasifica en vez de NORMALIZAR a la clave, y el motivo es que normalizar
    reescribiria en silencio un campo que el usuario escribio a mano: la
    recuperacion del `.bak` deja el fichero en disco para que el usuario decida.

    La asercion que mata a L-M2b es de CONTENIDO y no de clase: un registro legacy
    sin `id` (que es como es uno de verdad) tiene que acabar con
    `packs[clave].id == clave`. Sin la linea `traducido["id"] = k`, `Pack(**traducido)`
    lanza `ValidationError` por `id` ausente y el test muere ahi.
    """
    print("Testing que la clave del mapa es la identidad del pack (L10)...")
    import json
    import shutil
    import tempfile
    from woptimizer.services.pack_service import (PackService, PerfilCorruptoError)

    # 1. La modernA con id que NO es la clave: corrupcion, en las dos ramas de
    #    lectura (con y sin .bak) y sin tocar un byte.
    for rama in ("moderna", "legacy"):
        registro = {"id": "otro-id", "name": "Mio", "apps": ["a.exe"]}
        if rama == "moderna":
            principal = json.dumps({"packs": {"mi-clave": registro}},
                                   ensure_ascii=False)
        else:
            registro["label"] = registro.pop("name")
            principal = json.dumps({"profiles": {"mi-clave": registro}},
                                   ensure_ascii=False)
        directorio = tempfile.mkdtemp(prefix="wopt_t031_l10_")
        ruta = os.path.join(directorio, "profiles.json")
        try:
            _escribir(ruta, principal)
            _escribir(ruta + ".bak", json.dumps(_BAK_SANO, ensure_ascii=False))
            principal_antes = _bytes_de(ruta)
            bak_antes = _bytes_de(ruta + ".bak")

            fallo = _capturar(lambda: PackService._read_json(None, ruta))
            assert isinstance(fallo, PerfilCorruptoError), (
                f"[{rama}/id != clave]: se cargo sin clasificar ({fallo!r}). La "
                f"clave del mapa es la identidad del pack: `pack_manager_view` "
                f"indexa por `pack.id` y reventaria con KeyError, y "
                f"`get_user_packs()` no lo enseñaria (L-M8c)"
            )
            texto = str(fallo)
            assert "mi-clave" in texto and "otro-id" in texto, (
                f"[{rama}/id != clave]: el mensaje {texto!r} no nombra las DOS "
                f"identidades, que es lo unico que permite arreglar el fichero"
            )

            servicio = PackService(data_path=ruta)
            assert servicio.recuperado_de_backup is True, (
                f"[{rama}/id != clave]: con .bak sano tiene que recuperarse"
            )
            assert "salvado" in servicio.get_all_packs(), (
                f"[{rama}/id != clave]: la recuperacion devolvio "
                f"{sorted(servicio.get_all_packs())}"
            )
            assert _bytes_de(ruta) == principal_antes, (
                f"[{rama}/id != clave]: recuperar no escribe nada en el principal"
            )
            assert _bytes_de(ruta + ".bak") == bak_antes, (
                f"[{rama}/id != clave]: el .bak sano fue tocado"
            )
        finally:
            shutil.rmtree(directorio, ignore_errors=True)

    # 2. Los ficheros BIEN escritos: la identidad se cumple y la UI puede
    #    encontrar cada pack por `pack.id`, que es su expresion literal.
    for rama in ("moderna", "legacy"):
        directorio = tempfile.mkdtemp(prefix="wopt_t031_l10b_")
        ruta = os.path.join(directorio, "profiles.json")
        try:
            registro = {"name": "Mio", "apps": ["a.exe"]}
            if rama == "moderna":
                registro["id"] = "mi-clave"
                _escribir(ruta, json.dumps({"packs": {"mi-clave": registro}},
                                           ensure_ascii=False))
            else:
                registro["label"] = registro.pop("name")
                _escribir(ruta, json.dumps({"profiles": {"mi-clave": registro}},
                                           ensure_ascii=False))
            servicio = PackService(data_path=ruta)
            packs = servicio.get_all_packs()
            assert servicio.fichero_danado is False, (
                f"[{rama}/bien escrito]: un fichero correcto se clasifico como "
                f"corrupcion: {servicio.motivo_danado!r}"
            )
            assert packs["mi-clave"].id == "mi-clave", (
                f"[{rama}/bien escrito]: un registro legacy sin 'id' (que es como "
                f"es uno de verdad) tiene que heredar la identidad de la clave, y "
                f"llego con id={packs['mi-clave'].id!r}. Sin la linea "
                f"`traducido['id'] = k` la fila legacy ni siquiera llega aqui "
                f"(L-M2b)"
            )
            # La expresion literal de `pack_manager_view.py:100`, sobre todos los
            # packs: si el id y la clave pueden divergir, esto es un KeyError.
            for clave, pack in packs.items():
                assert packs[pack.id] is pack, (
                    f"[{rama}/bien escrito]: el pack {clave!r} no se puede "
                    f"encontrar por su id ({pack.id!r})"
                )
        finally:
            shutil.rmtree(directorio, ignore_errors=True)
    print("La clave del mapa es la identidad del pack OK (L10).")


# --- TASK-031 iteracion 3: sondas L11-L12 ----------------------------------
# Claves EXTRA de la raiz de un profiles.json LEGACY. No son inventadas para el
# test: un `profiles.json` legacy real trae `favorite` en la raiz, que es
# justamente el dato que la rama legacy se llevaba por delante.
_EXTRAS_RAIZ_LEGACY = (
    ("favorite", "mio"),
    ("version", 2),
    ("escrito_por", {"build": 7}),
)


def test_la_raiz_legada_conserva_sus_claves_extra():
    """TASK-031 iteracion 3 / L11: las claves EXTRA de la RAIZ sobreviven al
    ciclo carga -> guarda, TAMBIEN en la rama legacy.

    MATA M8 (la rama legacy reconstruia el `AppData` desde cero y descartaba
    el resto de la raiz) y M8b (conservar tambien `profiles`).

    MEDIDO en el estado anterior: `{"profiles": {...}, "favorite": "mio"}`
    arrancaba SIN clasificar nada y, en el PRIMER `save()` real del usuario, el
    fichero quedaba como `{"packs": {...}}`: `favorite` desaparecia DEL DISCO, en
    silencio, sin aviso y sin `.bak` al que recurrir (el `.bak` que hay es la
    version ANTERIOR, que tambien se acaba de rotar con el dato dentro).

    POR QUE `extra="allow"` NO LO ARREGLA, y por eso el arreglo es de CODIGO y no
    de configuracion: en la rama moderna la raiz desconocida sobrevive porque
    `AppData(**raw_data)` se la guarda. En la legacy el `AppData` se construia
    con `packs` y nada mas, asi que el extra no existia. Un `extra="allow"` que
    no se copia al objeto no conserva NADA: la linea (mutacion L-M6c, sonda L8)
    es necesaria y no suficiente, y por eso M8 y L-M6c son dos puertas distintas
    al mismo bulo.

    Y POR QUE `profiles` SE DESCARTA (M8b): su contenido ya esta traducido en
    `packs`, y conservarlo escribiria un fichero con LAS DOS claves, que la
    lectura siguiente clasifica como corrupcion (L7). Eso no es "sobrar
    informacion": es un landmine que solo explosionaria en el SEGUNDO arranque
    del usuario. Por eso la asercion de M8b no es "la clave no aparece" (que un
    mutante podria cumplir por casualidad) sino RELEER el fichero escrito y
    afirmar que arranca limpio con los packs del usuario dentro.
    """
    print("Testing que la raiz legada conserva sus claves extra (L11)...")
    import json
    import shutil
    import tempfile
    from woptimizer.services.pack_service import PackService

    registros = {"mio": {"label": "Mio", "apps": ["mio.exe"]}}
    raiz = dict(_EXTRAS_RAIZ_LEGACY)
    raiz["profiles"] = registros

    directorio = tempfile.mkdtemp(prefix="wopt_t031_l11_")
    ruta = os.path.join(directorio, "profiles.json")
    try:
        _escribir(ruta, json.dumps(raiz, ensure_ascii=False))
        _escribir(ruta + ".bak", json.dumps(_BAK_SANO, ensure_ascii=False))
        bak_antes = _bytes_de(ruta + ".bak")

        servicio = PackService(data_path=ruta)

        assert servicio.fichero_danado is False, (
            f"un profiles.json legacy con claves extra en la raiz se clasifico "
            f"como corrupcion: {servicio.motivo_danado!r}"
        )
        assert servicio.recuperado_de_backup is False, (
            "se recupero del .bak: una clave raiz que no es de esta version no "
            "es motivo para tirar la version del usuario"
        )
        assert _bytes_de(ruta + ".bak") == bak_antes, "el .bak sano fue tocado"
        packs = servicio.get_all_packs()
        assert packs["mio"].name == "Mio" and packs["mio"].apps == ["mio.exe"], (
            f"los packs legacy no llegaron: {packs['mio']!r}"
        )

        # Escritura REAL del usuario: es aqui donde el dato se perdia.
        servicio.create_user_pack("nuevo", "Nuevo", ["nuevo.exe"])

        with open(ruta, encoding="utf-8") as fh:
            en_disco = json.load(fh)
        for clave, valor in _EXTRAS_RAIZ_LEGACY:
            assert clave in en_disco, (
                f"la clave raiz {clave!r} desaparecio del disco tras el save(): "
                f"en el fichero quedan {sorted(en_disco)}. Un 'profiles.json' "
                f"legacy REAL trae 'favorite' en la raiz, asi que esto es "
                f"perdida de datos del usuario, en silencio (M8)"
            )
            assert en_disco[clave] == valor, (
                f"la clave raiz {clave!r} cambio de valor: {en_disco[clave]!r} "
                f"!= {valor!r}"
            )
        assert en_disco["packs"]["mio"]["apps"] == ["mio.exe"], (
            f"los packs del usuario no llegaron al disco: {en_disco['packs']!r}"
        )
        assert "nuevo" in en_disco["packs"], (
            f"el pack nuevo no se guardo: la escritura real no ocurrio y el "
            f"resto de aserciones no probarian nada. Quedan "
            f"{sorted(en_disco.get('packs', {}))}"
        )
        assert "profiles" not in en_disco, (
            f"'profiles' se ha copiado al fichero escrito: quedan "
            f"{sorted(en_disco)}. El contenido ya esta en 'packs', y un fichero "
            f"con las DOS claves lo clasifica la lectura siguiente como "
            f"corrupcion (L7): el landmine solo explotaria en el segundo "
            f"arranque (M8b)"
        )

        # Y la asercion que de verdad distingue M8b de "no hacer nada": el
        # fichero escrito TIENE que volver a arrancar limpio.
        relectura = PackService(data_path=ruta)
        assert relectura.fichero_danado is False, (
            f"el fichero escrito por la app se clasifica como corrupto al "
            f"volver a leerlo: {relectura.motivo_danado!r}. Lo que la app publica "
            f"tiene que ser leible por ella misma"
        )
        repacks = relectura.get_all_packs()
        assert "mio" in repacks and "nuevo" in repacks, (
            f"la relectura devolvio {sorted(repacks)}"
        )
    finally:
        shutil.rmtree(directorio, ignore_errors=True)

    # CONTROL: una raiz legacy SIN claves extra sigue funcionando igual. Sin
    # esta parte, un arreglo que "funciona" porque no carga nada en verde.
    directorio = tempfile.mkdtemp(prefix="wopt_t031_l11b_")
    ruta = os.path.join(directorio, "profiles.json")
    try:
        _escribir(ruta, json.dumps({"profiles": registros}, ensure_ascii=False))
        servicio = PackService(data_path=ruta)
        assert servicio.fichero_danado is False, (
            f"sin claves extra la rama legacy dejo de funcionar: "
            f"{servicio.motivo_danado!r}"
        )
        assert servicio.get_all_packs()["mio"].name == "Mio", "el pack no llego"
    finally:
        shutil.rmtree(directorio, ignore_errors=True)
    print("La raiz legada conserva sus claves extra OK (L11).")


def test_una_clave_raiz_nunca_es_un_error_de_escritura():
    """TASK-031 iteracion 3 / L12: una clave de la RAIZ NUNCA se declara
    corrupcion por parecerse a un campo de hoja, y sobrevive al guardado.

    MATA M9 (aplicar `_colision_de_tecla` tambien a la raiz) y L-M8a
    (clasificar la raiz mal escrita como corrupcion, con las DOS
    implementaciones plausibles: "la raiz no tiene ninguna clave conocida" y
    "una clave de la raiz colisiona con un campo de hoja").

    La segunda mitad del test (raiz SIN clave valida) existe porque la primera no
    alcanzaba a una de las dos implementaciones: un filtro de colision contra
    campos de HOJA no ve `perfiles` (no se parece a ningun campo de `Pack`), y
    con la primera mitad sola esa variante del mutante pasaba en verde.

    POR QUE NO SE APLICA, y por que NO es "una omision" (la decision, con su
    coste, medida tres veces):

      1. La IDENTIDAD no tiene sentido ahi: no hay ningun `id` al que una clave
         raiz pueda ser distinta.
      2. El ERROR DE ESCRITURA ahi es perdida de datos. En la ruta sin `.bak`,
         clasificar hace `self._data = AppData()` y el siguiente `save()`
         publica `{"packs": {"gaming": ...}}`: los packs del usuario se pierden
         IGUAL que sin clasificar, y con un aviso de encima (asi lo midio L8).
      3. Y ademas es FALSO POSITIVO: `names` esta a distancia 1 de `name` e
         `ids` a distancia 1 de `id`. Una clave raiz que se parece a un campo
         de hoja no es un error de escritura de hoja: es un dato raiz de otro
         build, y clasificarlo lo borra. En la HOJA si que significa algo: alla
         `name` y `names` conviviendo en el mismo registro es un error de
         escritura de verdad, y eso es lo que mide L9.

    El ultimo caso de la lista (`packs2`, `profiless`) es la otra mitad: claves
    raiz que parecen un error de escritura de una clave RAIZ. Tampoco son
    corrupcion, por el punto 2.
    """
    print("Testing que una clave raiz nunca es un error de escritura (L12)...")
    import json
    import shutil
    import tempfile
    from woptimizer.services.pack_service import PackService

    # (clave raiz, valor). Las tres primeras se parecen a un campo de HOJA a una
    # pulsacion; las dos ultimas se parecen a una clave de RAIZ.
    claves_raiz = (
        ("names", ["mio", "nuevo"]),
        ("ids", ["a", "b"]),
        ("favorite", "mio"),
        ("keeper", ["steam.exe"]),
        ("is_favorit", True),
        ("packs2", {"otro": {"id": "otro", "name": "Otro"}}),
        ("profiless", {"otro": {"label": "Otro"}}),
    )
    for clave, valor in claves_raiz:
        etiqueta = f"[raiz/{clave}]"
        hoja = {"id": "mio", "name": "Mio", "apps": ["mio.exe"]}
        principal = json.dumps({"packs": {"mio": hoja}, clave: valor},
                               ensure_ascii=False)

        directorio = tempfile.mkdtemp(prefix="wopt_t031_l12_")
        ruta = os.path.join(directorio, "profiles.json")
        try:
            _escribir(ruta, principal)
            _escribir(ruta + ".bak", json.dumps(_BAK_SANO, ensure_ascii=False))
            bak_antes = _bytes_de(ruta + ".bak")

            servicio = PackService(data_path=ruta)

            assert servicio.fichero_danado is False, (
                f"{etiqueta}: una clave de la RAIZ se declaro error de "
                f"escritura: {servicio.motivo_danado!r}. En la hoja,parecerse a "
                f"un campo conocido significa un campo que se queda SIN LEER "
                f"('keepers' en [] y el Gaming Mode sin proteger nada); en la "
                f"raiz significa que la lectura siguiente arranca con cero packs "
                f"y el siguiente guardado publica {{'packs': {{'gaming': ...}}}}, "
                f"con lo que los packs del usuario se pierden IGUAL y con un "
                f"aviso de encima. Ademas 'names'/'ids' estan a distancia 1 de "
                f"'name'/'id': en la raiz son FALSOS POSITIVOS (M9, L-M8a)"
            )
            assert servicio.recuperado_de_backup is False, (
                f"{etiqueta}: se recupero del .bak sin motivo"
            )
            assert _bytes_de(ruta + ".bak") == bak_antes, (
                f"{etiqueta}: el .bak sano fue tocado"
            )
            assert "mio" in servicio.get_all_packs(), (
                f"{etiqueta}: el pack del usuario no se cargo: "
                f"{sorted(servicio.get_all_packs())}"
            )

            # Escritura REAL: una clave raiz que no se clasifica tampoco puede
            # desaparecer del fichero.
            servicio.create_user_pack("nuevo", "Nuevo", ["nuevo.exe"])
            with open(ruta, encoding="utf-8") as fh:
                en_disco = json.load(fh)
            assert clave in en_disco, (
                f"{etiqueta}: la clave raiz desaparecio del disco tras el "
                f"save(): quedan {sorted(en_disco)} (M9)"
            )
            assert en_disco[clave] == valor, (
                f"{etiqueta}: la clave raiz cambio de valor: "
                f"{en_disco[clave]!r} != {valor!r}"
            )
            assert en_disco["packs"]["mio"]["apps"] == ["mio.exe"], (
                f"{etiqueta}: los packs del usuario no llegaron al disco: "
                f"{en_disco.get('packs')!r}"
            )
        finally:
            shutil.rmtree(directorio, ignore_errors=True)

    # La MISMA regla cuando la raiz NO TIENE una clave valida. Aqui no hay ni un
    # solo pack que perder en memoria, y aun asi la respuesta tiene que ser "no
    # es corrupcion": clasificar haria `self._data = AppData()` y el siguiente
    # guardado publicaria `{"packs": {"gaming": ...}}` encima de UN fichero
    # ajeno. Es la variante que mide L8 con `{"packs2": ...}`, repetida aqui con
    # una clave que ademas se parece a un campo de hoja, que es la combinacion
    # que no habia ninguna sonda que cubriera.
    for raiz in ({"names": ["mio", "nuevo"]}, {"ids": ["a", "b"]},
                 {"packs2": {"otro": {"id": "otro", "name": "Otro"}}},
                 {"profiless": {"otro": {"label": "Otro"}}}):
        etiqueta = f"[raiz sin clave valida/{sorted(raiz)[0]}]"
        directorio = tempfile.mkdtemp(prefix="wopt_t031_l12b_")
        ruta = os.path.join(directorio, "profiles.json")
        try:
            _escribir(ruta, json.dumps(raiz, ensure_ascii=False))
            _escribir(ruta + ".bak", json.dumps(_BAK_SANO, ensure_ascii=False))
            bak_antes = _bytes_de(ruta + ".bak")
            clave, valor = next(iter(raiz.items()))

            servicio = PackService(data_path=ruta)
            assert servicio.fichero_danado is False, (
                f"{etiqueta}: una raiz sin clave valida se declaro corrupcion: "
                f"{servicio.motivo_danado!r}. Clasificar hace `self._data = "
                f"AppData()` y el siguiente guardado publica "
                f"{{'packs': {{'gaming': ...}}}} encima de un fichero que la app "
                f"no sabe leer: los datos ajenos se pierden IGUAL, con un aviso "
                f"de encima (L-M8a, M9)"
            )
            assert servicio.recuperado_de_backup is False, (
                f"{etiqueta}: se recupero del .bak sin motivo"
            )
            assert _bytes_de(ruta + ".bak") == bak_antes, (
                f"{etiqueta}: el .bak sano fue tocado"
            )

            servicio.create_user_pack("nuevo", "Nuevo", ["nuevo.exe"])
            with open(ruta, encoding="utf-8") as fh:
                en_disco = json.load(fh)
            assert clave in en_disco and en_disco[clave] == valor, (
                f"{etiqueta}: el dato de la raiz desaparecio tras el save(): "
                f"quedan {sorted(en_disco)} (M9)"
            )
            assert "nuevo" in en_disco.get("packs", {}), (
                f"{etiqueta}: el pack nuevo no se guardo: la escritura real no "
                f"ocurrio y el resto de aserciones no probarian nada"
            )
        finally:
            shutil.rmtree(directorio, ignore_errors=True)
    print("Una clave raiz nunca es un error de escritura OK (L12).")


# ===========================================================================
# TASK-027: FIX-003 / FIX-004 / FIX-006
# ===========================================================================

class _PopenProhibido(BaseException):
    """BaseException a PROPOSITO (TASK-027 / T-27.1).

    Si el centinela fuese `AssertionError`, el `except Exception` del codigo
    viejo (`Popen(app, shell=True)`) lo digeriria, contaria `failed += 1` y el
    test pasaria en verde con el defecto dentro. Al ser `BaseException` no la
    captura nadie y reintroducir el interprete MUERE en la asercion.
    """


def _hallazgos_shell_true(fuente: str, etiqueta: str) -> list:
    """`(linea, etiqueta)` de cada `Popen(..., shell=<interprete>)` que se vea.

    POR QUE EXISTE COMO FUNCION y no como bucle dentro de un test (TASK-027
    iter 2, hallazgo 3): la guarda anterior miraba `ast.Name` y era CIEGA a la
    grafia exacta del bug original, `subprocess.Popen(app, shell=True)`. Sin
    una sonda que le pase esa grafia, "ampliar el visitor" es una intencion sin
    prueba: el test `test_la_guarda_de_shell_true_ve_atributos_y_aliases` la
    ejercita con snippets sinteticos y con el producto real.

    Tres formas de invocar un `Popen` importado, las tres reales:
      * `Popen(...)`                 -> `ast.Name` (con `from subprocess import Popen`)
      * `subprocess.Popen(...)`      -> `ast.Attribute`  <-- la que no se miraba
      * `sp.Popen(...)` / `abrir(...)` -> atributo o alias, y el alias se
        resuelve mirando los `ImportFrom` del modulo.
    """
    arbol = ast.parse(fuente)
    nombres = {"Popen"}
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ImportFrom) and nodo.module == "subprocess":
            for alias in nodo.names:
                if alias.name == "Popen":
                    nombres.add(alias.asname or alias.name)

    fallos = []
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Call):
            continue
        func = nodo.func
        if isinstance(func, ast.Name):
            nombre = func.id
        elif isinstance(func, ast.Attribute):
            nombre = func.attr
        else:
            continue
        if nombre not in nombres:
            continue
        for kw in nodo.keywords:
            if kw.arg != "shell":
                continue
            # `shell=False` explicito es seguro y NO debe marcarse (falso
            # positivo). Cualquier otro valor es un interprete: `True`, `1`, o
            # una variable que podria valer cualquier cosa.
            if isinstance(kw.value, ast.Constant) and kw.value.value in (False, 0, None):
                continue
            fallos.append((nodo.lineno, etiqueta))
    return fallos


class PrivilegeNotHeldError(Exception):
    pass


def _mklink(args) -> None:
    """Crea un enlace de Windows (`mklink`) y FALLA RUIDOSAMENTE si no puede.

    `mklink` es un INTERNO de `cmd.exe`, no un ejecutable: por eso el `cmd /c`.
    Aqui el interprete es legitimo (esto es codigo de prueba, no produccion) y
    no contradice la guarda anti-shell de mas abajo, que solo prohibe
    `shell=True` en `src/woptimizer`.
    """
    import subprocess as _sp
    r = _sp.run(["cmd", "/c", "mklink"] + list(args),
                capture_output=True, text=True)
    if r.returncode != 0:
        out_err = (r.stdout + " " + r.stderr).lower()
        if "/j" not in [str(a).lower() for a in args] and ("privilegio" in out_err or "privilege" in out_err):
            raise PrivilegeNotHeldError(
                f"enlace de fichero omitido: falta SeCreateSymbolicLink ({r.stdout.strip()} {r.stderr.strip()})"
            )
        raise AssertionError(
            f"no se pudo crear el enlace {list(args)!r} (rc={r.returncode}): "
            f"{r.stdout.strip()} {r.stderr.strip()}. Sin el enlace REAL la sonda "
            "pasaria por el motivo equivocado (lo que se midio es que un junction "
            "de un comando dentro de %LOCALAPPDATA% SI arranca), asi que aqui se "
            "falla en voz alta. Un junction (`mklink /J`) solo necesita NTFS; un "
            "enlace de fichero (`mklink` a secas) necesita SeCreateSymbolicLink, "
            "o sea administrador o Modo Desarrollador."
        )


def _escribir_pe_minimo(ruta: str) -> str:
    """Escribe en `ruta` la IMAGEN PE minima y devuelve la ruta.

    POR QUE EXISTE (TASK-027 iter 3). Desde la regla 9 (`_es_imagen_pe`) un
    `.exe` de verdad tiene que LLEVAR la firma MZ/PE, porque la regla ya no mira
    el nombre del fichero sino su contenido. Las sondas de las iteraciones
    anteriores usaban ficheros VACIOS como atajo de "una app de verdad", y un
    `.exe` vacio no es una app de verdad: `os.startfile` sobre el responde
    WinError 193 (comentario propio de `test_arranque_de_apps_no_usa_shell`).
    O sea que el atajo era una ficcion que la regla nueva deja de tolerar.

    Aqui NO se cambia lo que esas sondas demuestran: siguen probando la
    resolucion real, el junction, la contencion, la caja o la guarda anti-shell.
    Lo unico que cambia es que el atajo "una app" sea ahora una app, con lo que
    ademas estas sondas son MAS fieles que antes (un fichero vacio no se puede
    arrancar ni con todos los permisos del mundo).

    Estructura: DOS bytes `MZ`, `e_lfanew` (offset 0x3C) = 0x40, y la firma
    `PE\\0\\0` en 0x40. Es la misma forma que comprueba `_es_imagen_pe`.
    """
    import struct as _struct
    cabecera = bytearray(0x40)
    cabecera[0:2] = b"MZ"
    _struct.pack_into("<I", cabecera, 0x3C, 0x40)
    cabecera[0x40:0x44] = b"PE\x00\x00"
    with open(ruta, "wb") as fh:
        fh.write(bytes(cabecera))
    return ruta


def test_un_hard_link_no_es_una_hoja_y_el_script_no_pasa():
    """TASK-027 iteracion 3: el hard link (y su hermano, la COPIA) no cuelan.

    EL HALLAZGO. El `mutation-auditor` measo que un hard link secundario
    (`alias.exe` -> `payload.bat` FUERA de las raices) lo aceptaba
    `_resolver_app` y se saltaba las DOS barreras. La version anterior de este
    modulo decia, en tres sitios, que eso no hacia falta cerrarlo porque "un
    hard link no es un reparse point y ningun filtro de Windows lo ve". LAS DOS
    MITADES DE ESA RAZON ESTABAN MAL, y aqui esta el porque, medido:

      1. "Ningun filtro lo ve" es FALSO: `os.stat(ruta).st_nlink` vale 2 en un
         hard link. Si lo ve.
      2. Y da igual que lo vea: el hard link NO es el agujero. La COPIA PLENA
         del mismo `payload.bat` a `alias_copia.exe` -`st_nlink == 1`, sin un
         solo enlace, sin junction, sin symlink, sin privilegios- la acepta
         `_resolver_app` IGUAL. Rechazar `st_nlink > 1` habria cerrado el caso
         exotico y habria dejado abierto el trivial: seguridad de teatro.

    Lo que cierra las DOS variantes (y las de cualquier otro tipo) es que el
    fichero sea de verdad una imagen PE, que es lo que la lista blanca de
    `.exe`/`.com` siempre quiso expresar: `.exe` no significa "algo que se
    arranca", significa "imagen PE". Un `.bat` renombrado no lo es, se llame
    como se llame.

    POR QUE EL ENLACE DURO ES REAL Y NO UN SIMULADO. Se construye con
    `os.link` (la misma llamada que usa `mklink /H`, sin `cmd.exe` y sin
    privilegios: solo exige el mismo volumen). Si el entorno no lo permite, el
    test FALLA en voz alta con `_falla_ruidosamente`: una sonda que se pone
    verde por no poder construir su caso es peor que no tener sonda, porque
    parece que el agujero esta cerrado cuando nadie lo ha mirado.

    MATA, una a una:
      * borrar la regla 9 (`_es_imagen_pe`)            -> (1) y (2) se aceptan;
      * `_es_imagen_pe` que devuelve siempre True      -> (1) y (2) se aceptan;
      * `_es_imagen_pe` que mira solo `MZ` y no `PE`   -> (4);
      * `_es_imagen_pe` sin `strict`/fail-closed, o sea
        `except OSError: return True`                  -> (5);
      * la "solucion" de rechazar `st_nlink > 1` a pelo -> (6), que es el
        control que mata la propia premisa de este test;
      * `_es_imagen_pe` que no lee el fichero de verdad (por ejemplo, que
        acepte cualquier cosa de menos de N bytes)     -> (2) y (3).
    """
    import logging as _logging
    import shutil
    import tempfile
    from woptimizer.services.process_service import (
        ProcessService, _es_imagen_pe, _ruta_real,
    )

    def _falla_ruidosamente(que):
        raise AssertionError(
            f"no se pudo construir el caso de hard link: {que}. Un hard link "
            "(`os.link`, equivalente a `mklink /H`) NO necesita SeCreateSymbolicLink "
            "ni administrador: solo que origen y alias esten en el MISMO volumen "
            "(aqui los dos estan en %TEMP%). Si esto falla, el entorno no deja "
            "crear enlaces duros, y el caso que esta sonda mide NO se ha "
            "medido: la sonda que se auto-declara verde por no poder construir su "
            "caso es peor que no tener sonda (esta es la Trampa #17 de "
            "`known-issues.md`)."
        )

    svc = ProcessService.__new__(ProcessService)
    avisos = []

    class _Captor(_logging.Handler):
        def emit(self, record):
            if record.levelno >= _logging.WARNING:
                avisos.append(record.getMessage())

    logger_wopt = _logging.getLogger("woptimizer")
    captor = _Captor(level=_logging.WARNING)
    logger_wopt.addHandler(captor)
    tmp = tempfile.mkdtemp(prefix="wopt_hl_")
    try:
        # --- precondiciones: sin ellas los casos pasan por el motivo erroneo --
        assert _es_imagen_pe(os.path.normpath(r"C:\Windows\System32\cmd.exe")), (
            "cmd.exe no es una imagen PE segun `_es_imagen_pe`: el resto de la "
            "sonda probaria la maquina y no la regla, porque los controles "
            "positivos fallarian todos"
        )
        _escribir_pe_minimo_real = _escribir_pe_minimo
        # El payload va FUERA de las raices, que es lo que hace peligroso al
        # alias; el alias va DENTRO, que es lo que lo hace alcanzable.
        fuera = os.path.join(os.environ["USERPROFILE"], f"wopt_hl_fuera_{os.getpid()}")
        os.makedirs(fuera, exist_ok=True)
        payload = os.path.join(fuera, "payload.bat")
        with open(payload, "w", encoding="utf-8") as fh:
            fh.write("@echo pwned\n")
        assert not _es_imagen_pe(payload), (
            "el payload deberia ser un guion, no un PE: si sale PE el caso pasaria "
            "por un motivo que no es el que se quiere probar"
        )

        # --- (1) HARD LINK REAL: alias.exe -> payload.bat --------------------
        alias_hard = os.path.join(tmp, "alias_hard.exe")
        try:
            os.link(payload, alias_hard)
        except OSError as e:
            _falla_ruidosamente(f"os.link lanzo {type(e).__name__}: {e}")
        assert os.path.isfile(alias_hard), (
            "el hard link no resuelve como fichero: el caso pasaria por isfile y "
            "no por el contenido"
        )
        nlink = os.stat(alias_hard, follow_symlinks=False).st_nlink
        assert nlink == 2, (
            f"el alias tiene st_nlink={nlink}, no 2: NO es un hard link real y la "
            "sonda no estaria midiendo el caso del hallazgo. Se ha creado otra "
            "cosa (una copia, probablemente) y el caso pasaria por el motivo "
            "equivocado"
        )
        assert _ruta_real(os.path.normpath(alias_hard)) == os.path.normpath(alias_hard), (
            "medido: un hard link NO es un reparse point, asi que realpath devuelve "
            "la MISMA ruta y no lo resuelve. Si aqui se resolviera, el SO de este "
            "entorno se comporta distinto y la regla 8 seria otra cosa"
        )
        avisos.clear()
        assert svc._resolver_app(alias_hard, raices=[tmp]) is None, (
            "un hard link a un .bat de FUERA de las raices se acepto: las reglas "
            "5-8 miran el NOMBRE y el nombre de un hard link es el que le pongas"
        )
        assert any("imagen PE" in m for m in avisos), (
            f"el rechazo por contenido no dice el motivo: {avisos}"
        )

        # --- (2) COPIA PLENA: el hermano que hace inutilizable el nlink -----
        # Si esta asercion falla, la premisa del test (el hard link no es el
        # agujero, la COPIA tambien) ya no se cumple en este entorno.
        alias_copia = os.path.join(tmp, "alias_copia.exe")
        shutil.copyfile(payload, alias_copia)
        nlink_copia = os.stat(alias_copia, follow_symlinks=False).st_nlink
        assert nlink_copia == 1, (
            f"la copia tiene st_nlink={nlink_copia}, no 1: se ha creado un enlace "
            "por error y este caso ya no seria el caso trivial que demuestra que "
            "cerrar el raro no cierra el facil"
        )
        assert svc._resolver_app(alias_copia, raices=[tmp]) is None, (
            "una COPIA PLENA de un .bat con nombre .exe se acepto: es el caso "
            "TRIVIAL (no hace falta ningun enlace) y es el que un filtro por "
            "`st_nlink` no cierra"
        )

        # --- (3) el mismo contenido con extension buena SI arranca -------------
        alias_ok = os.path.join(tmp, "programa.exe")
        _escribir_pe_minimo_real(alias_ok)
        assert svc._resolver_app(alias_ok, raices=[tmp]) == _ruta_real(alias_ok), (
            "un PE de verdad dentro de la raiz debe arrancar: si no, la sonda "
            "estaria probando que nada pasa"
        )

        # --- (4) MZ sin la firma PE NO es un programa ------------------------
        # El caso de margen, y hay que hacerlo con CUIDADO porque aqui se
        # puede pasar por el motivo equivocado (que es lo que hacia la primera
        # version de este caso, que sobrevivia a la mutacion "solo mira MZ").
        # `e_lfanew` tiene que ser PLAUSIBLE: si vale 0xFFFFFFFF, el rechazo lo
        # da el tope de seguridad de la funcion, no la comparacion de la firma,
        # y una funcion que se quedase en `MZ` + "ya vale" pasaria este caso.
        # Asi que aqui `e_lfanew` apunta a 0x40 y en 0x40 hay BASURA, no la firma.
        medio = os.path.join(tmp, "medio.exe")
        with open(medio, "wb") as fh:
            fh.write(b"MZ" + b"\x00" * 0x3C + (0x40).to_bytes(4, "little")
                     + b"NOESPE\x00\x00")
        assert not _es_imagen_pe(medio), (
            "un fichero con cabecera MZ pero SIN la firma PE no es una imagen PE: "
            "la comprobacion tiene que llegar hasta `e_lfanew` y leer ahi"
        )
        assert svc._resolver_app(medio, raices=[tmp]) is None, (
            "un MZ sin PE se acepto: la regla 9 se queda en la cabecera DOS"
        )
        # Y el tope de seguridad es lo que frena un `e_lfanew` manipulado (leer
        # el fichero entero buscando la firma no es una comprobacion, es un
        # negreado). Con este offset, el rechazo lo da EL TOPE, asi que se dice.
        absurdo = os.path.join(tmp, "absurdo.exe")
        with open(absurdo, "wb") as fh:
            fh.write(b"MZ" + b"\x00" * 0x3C + (0xFFFFFFFF).to_bytes(4, "little"))
        assert not _es_imagen_pe(absurdo), (
            "un `e_lfanew` de 4 GiB tiene que rechazarse por el tope: sin el, la "
            "funcion se pasa la vida leyendo el fichero en busca de la firma"
        )

        # --- (5) fail-closed: ilegible NO es un programa ---------------------
        # Se comprueba la FUNCION, no el permiso: hacer el fichero ilegible
        # requiere ACL y no es reproducible en una cuenta normal.
        assert not _es_imagen_pe(os.path.join(tmp, "no_existe.exe")), (
            "un fichero inexistente no es una imagen PE: sin lectura no hay "
            "prueba, y fail-closed significa no arrancar"
        )
        solo_directorio = os.path.join(tmp, "un_directorio.exe")
        os.mkdir(solo_directorio)
        assert not _es_imagen_pe(solo_directorio), (
            "abrir un directorio lanza OSError: eso debe ser False (fail-closed), "
            "no una excepcion que reviente el arranque"
        )

        # --- (6) CONTROL que mata la premisa del nlink ----------------------
        # Aqui esta el porque de NO rechazar `st_nlink > 1` a pelo. Se mide el
        # caso sobre un programa REAL instalado y con enlaces duros REALES, no
        # sobre un fichero de pruebas: la cifra que importa ("los .exe/.com
        # instalados con st_nlink>1 son legitimos y hay que arrancarlos") es una
        # afirmacion sobre el software de la maquina, y una sonda que la
        # comprueba con un `.exe` vacio hecho a mano no la comprueba.
        multi = _primer_multi_enlazado_real()
        if multi is None:
            # Sin ningun multi-enlazado en las raices, el caso (6) no se puede
            # construir. No se falla: seria un entorno sin programas de
            # Microsoft, que es legitimo. Lo que NO se puede es fingir que el
            # caso se probo, asi que se dice en voz alta en el print.
            print("  [aviso] ningun .exe/.com instalado tiene st_nlink>1: el "
                  "control (6) no se pudo construir en esta maquina.")
        else:
            assert _es_imagen_pe(multi), (
                f"{multi} tiene st_nlink>1 y es legitimo, pero `_es_imagen_pe` lo "
                "rechazaria: la regla 9 esta rechazando software de verdad"
            )
            assert svc._resolver_app(multi) == _ruta_real(os.path.normpath(multi)), (
                f"{os.path.basename(multi)} esta INSTALADO, tiene enlaces duros de "
                "verdad (st_nlink>1) y es una imagen PE, y no arranca. Rechazar "
                "'cualquier st_nlink>1' habria hecho justo esto con el 8,32% de "
                "los .exe/.com instalados en las seis raices (msinfo32.exe, "
                "TabTip.exe, los auxiliares de Edge, las herramientas de "
                "Hyper-V). Este control es el que prohibe esa 'solucion'"
            )
    finally:
        logger_wopt.removeHandler(captor)
        shutil.rmtree(tmp, ignore_errors=True)
        try:
            shutil.rmtree(os.path.join(
                os.environ["USERPROFILE"], f"wopt_hl_fuera_{os.getpid()}"),
                ignore_errors=True)
        except Exception:
            pass
    print("Un hard link (y su copia) no cuelan: la regla es el contenido (TASK-027 iter 3).")


def _primer_multi_enlazado_real() -> object:
    """Primer `.exe`/`.com` INSTALADO en las raices con `st_nlink > 1`, o `None`.

    Devuelve la ruta, o `None` si en esta maquina no hay ninguno (o no se puede
    leer lo suficiente para saberlo). Recorre con un presupuesto acotado: esto
    va en la suite de produccion y no puede tardarse un minuto.

    Es el control que hace que "no uses st_nlink" sea un HECHO medido sobre el
    software instalado y no una opinion.
    """
    raices = []
    for var in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432",
                "LOCALAPPDATA", "APPDATA", "ProgramData"):
        valor = os.environ.get(var)
        if valor and os.path.isdir(valor):
            raices.append(valor)
    presupuesto = 4000
    vistos = 0
    for raiz in raices:
        for dirpath, _dirnames, filenames in os.walk(raiz):
            for nombre in filenames:
                if not nombre.lower().endswith((".exe", ".com")):
                    continue
                try:
                    st = os.stat(os.path.join(dirpath, nombre),
                                 follow_symlinks=False)
                except OSError:
                    continue
                if st.st_nlink > 1:
                    return os.path.join(dirpath, nombre)
                vistos += 1
                if vistos >= presupuesto:
                    return None
    return None


def test_un_junction_no_puede_colar_lo_que_hay_detras():
    """TASK-027 iter 2, hallazgo 1 (ALTA): la contencion LEXICA no atraviesa.

    El fallo medido por el mutation-auditor: un junction dentro de
    `%LOCALAPPDATA%` que apunta a `C:\\Windows\\System32\\cmd.exe` era ACEPTADO y
    arrancaba, porque `normpath` y `commonpath` son lexicos. La garantia de
    `architecture.md` era falsa.

    Aqui el junction es REAL (`mklink /J` / `mklink` de verdad), no una
    simulacion: la sonda que se auto-declara verde porque "el caso no se pudo
    construir" es peor que no tener sonda. `_mklink` falla ruidosamente.

    MATA, una a una:
      * borrar la regla 8 (resolucion real) -> (1), (2) y (3) aceptan lo que
        estan en el log como rechazado;
      * `realpath` SIN `strict=True` (fail-closed) -> la sonda de `_ruta_real`;
      * comprobar la extension SOLO en el alias y no en la ruta real -> (3);
      * "solucion" de rechazar TODO reparse point -> (4) y (5), que son los
        controles positivos: un enlace que apunta DENTRO de una raiz permitida
        es una app legitima (es como se instala de todo en Steam) y se
        arranca;
      * devolver la ruta LEXICA en vez de la real -> (4) y (5) comparan la
        ruta real exacta.
    """
    import logging as _logging
    import shutil
    import tempfile
    from woptimizer.services.process_service import (
        ProcessService, _dentro_de_alguna, _ruta_real,
    )

    objetivo_real = os.path.normpath(r"C:\Windows\System32\cmd.exe")
    svc = ProcessService.__new__(ProcessService)
    avisos = []

    class _Captor(_logging.Handler):
        def emit(self, record):
            if record.levelno >= _logging.WARNING:
                avisos.append(record.getMessage())

    logger_wopt = _logging.getLogger("woptimizer")
    captor = _Captor(level=_logging.WARNING)
    logger_wopt.addHandler(captor)
    tmp = tempfile.mkdtemp(prefix="wopt_fix003j_")
    # Destino del junction FUERA de toda raiz permitida, pero en un sitio que
    # este test puede borrar sin riesgo. No se apunta a C:\\Windows\\System32
    # con un junction de DIRECTORIO: si la limpieza fallara, un `rmtree` que
    # siguiera el enlace borraria System32. El caso de `cmd.exe` de verdad se
    # cubre con un enlace de FICHERO, que `os.remove` solo borra a si mismo.
    fuera = os.path.join(os.environ["USERPROFILE"], f"wopt_fuera_{os.getpid()}")
    j_dir = os.path.join(tmp, "jdir")
    j_fich = os.path.join(tmp, "jfile.exe")
    alias_bat = os.path.join(tmp, "alias.exe")
    j_ok = os.path.join(tmp, "jok")
    alias_ok = os.path.join(tmp, "alias_ok.exe")
    raiz_j = os.path.join(tmp, "raiz_j")
    enlaces = (j_dir, j_fich, alias_bat, j_ok, alias_ok, raiz_j)
    try:
        # --- precondiciones: sin ellas los casos pasan por el motivo erroneo -
        assert os.path.isfile(objetivo_real), (
            f"{objetivo_real} no existe: el caso (2) pasaria por 'no existe' y no "
            "por la resolucion real"
        )
        raices = svc._launch_roots()
        assert raices, "este entorno no define ninguna raiz de arranque permitida"
        raices_norm = [os.path.normpath(r) for r in raices]
        assert _dentro_de_alguna(os.path.normpath(tmp), raices_norm), (
            f"el temporal {tmp} cae fuera de las raices: los casos pasarian por "
            "contencion y no por la resolucion real"
        )
        assert _ruta_real(os.path.normpath(tmp)) == os.path.normpath(tmp), (
            f"el temporal {tmp} se resuelve a {_ruta_real(os.path.normpath(tmp))}: "
            "el junction se crearia fuera de las raices y la asercion pasaria por "
            "el motivo equivocado"
        )
        assert not _dentro_de_alguna(os.path.normpath(fuera), raices_norm), (
            f"el destino del junction ({fuera}) esta DENTRO de las raices "
            "permitidas: la sonda probaria el caso bueno, no el malo"
        )

        os.makedirs(fuera, exist_ok=True)
        fuera_cmd = os.path.join(fuera, "cmd.exe")
        # PE de verdad (no vacio): la regla 9 mira el contenido, y este caso
        # tiene que morir por el JUNCTION, no por "no es un PE".
        _escribir_pe_minimo(fuera_cmd)

        # --- (1) junction de DIRECTORIO a un destino fuera de las raices -----
        _mklink(["/J", j_dir, fuera])
        via_dir = os.path.join(j_dir, "cmd.exe")
        assert os.path.isfile(via_dir), (
            "el enlace no resuelve como fichero: el caso pasaria por isfile y no "
            "por la resolucion real"
        )
        assert _dentro_de_alguna(os.path.normpath(via_dir),
                                  [os.path.normpath(tmp)]), (
            "medido: la contencion LEXICA dice 'dentro' para el junction. Si esta "
            "asercion falla, `_dentro_de_alguna` ha cambiado de politica y esta "
            "sonda hay que actualizarla (no es un defecto por si mismo)"
        )
        assert _ruta_real(via_dir) == fuera_cmd, (
            f"el SO no resuelve el junction a {fuera_cmd}: sin esto la sonda no "
            f"probaria nada (resuelve a {_ruta_real(via_dir)})"
        )
        avisos.clear()
        assert svc._resolver_app(via_dir) is None, (
            f"un junction a {fuera_cmd} colado bajo {tmp} se acepto: la "
            "contencion se comprueba SOLO sobre la ruta lexica"
        )
        assert any("junction/symlink" in m for m in avisos), (
            f"el rechazo por junction no dice el motivo: {avisos}"
        )

        # --- (2) enlace de FICHERO a cmd.exe de verdad (el repro del auditor) --
        try:
            _mklink([j_fich, objetivo_real])
            assert _ruta_real(j_fich) == objetivo_real, (
                f"el SO no resuelve el enlace a {objetivo_real} "
                f"(resuelve a {_ruta_real(j_fich)})"
            )
            avisos.clear()
            assert svc._resolver_app(j_fich) is None, (
                f"un enlace de fichero a {objetivo_real} se acepto: la ruta real cae "
                "fuera de las raices y aun asi arranco"
            )
        except PrivilegeNotHeldError:
            pass

        # --- (3) `.exe` que apunta a un `.bat` DENTRO de las raices ----------
        # El caso mas subtil: la extension se miraba en el ALIAS, y el destino
        # es un `.bat` legitimo de una raiz permitida, asi que la contencion
        # real lo acepta y sin mirarla la lista blanca se esquiva entera
        # (ShellExecute lo pasaria por `cmd.exe /c`).
        dentro = os.path.join(tmp, "dentro")
        os.makedirs(dentro, exist_ok=True)
        bat = os.path.join(dentro, "evil.bat")
        # OJO, y es lo que mantiene viva a la mutacion A3 ("comprobar la
        # extension SOLO en el alias"): este `.bat` lleva contenido de PE DE
        # VERDAD. Con un guion vacio, desde la iteracion 3 lo rechazaria la
        # regla 9 ("no es una imagen PE") y la lista blanca de extensiones se
        # dejaria de comprobar sin que nadie lo notase. Con un PE dentro, lo
        # unico que puede rechazarlo es la extension, que es lo que este caso
        # dice que prueba.
        _escribir_pe_minimo(bat)
        try:
            _mklink([alias_bat, bat])
            assert _ruta_real(alias_bat) == os.path.normpath(bat), (
                f"el SO no resuelve el enlace al .bat: {_ruta_real(alias_bat)}"
            )
            avisos.clear()
            assert svc._resolver_app(alias_bat, raices=[tmp]) is None, (
                "un alias .exe a un .bat de una raiz permitida se acepto: la lista "
                "blanca de extensiones se comprueba en el alias y no en el destino"
            )
            assert any("evil.bat" in m for m in avisos), (
                f"el rechazo por extension real no nombra el destino: {avisos}"
            )
        except PrivilegeNotHeldError:
            pass

        # --- (4) CONTROL POSITIVO: junction que apunta DENTRO de las raices ---
        # Manda el "soluciona" de rechazar todo reparse point: un enlace a un
        # destino de una raiz permitida es una app legitima y se arranca.
        destino = os.path.join(tmp, "destino_real")
        os.makedirs(destino, exist_ok=True)
        bien = os.path.join(destino, "bien.exe")
        _escribir_pe_minimo(bien)
        _mklink(["/J", j_ok, destino])
        assert svc._resolver_app(os.path.join(j_ok, "bien.exe"),
                                 raices=[tmp]) == _ruta_real(bien), (
            "un junction que apunta DENTRO de una raiz permitida debe arrancar: "
            "rechazar todo reparse point rompe apps legitimas (Steam, itch.io)"
        )

        # --- (5) CONTROL POSITIVO: enlace de fichero dentro de las raices -----
        try:
            _mklink([alias_ok, bien])
            assert svc._resolver_app(alias_ok, raices=[tmp]) == _ruta_real(bien), (
                "un enlace de fichero a un .exe de una raiz permitida debe arrancar"
            )
        except PrivilegeNotHeldError:
            pass
        # Y se devuelve la ruta REAL, no la lexica: lo que se valida es lo que
        # se arranca, y el log dice la verdad.
        assert svc._resolver_app(bien, raices=[tmp]) == _ruta_real(bien), (
            "la ruta devuelta debe ser la RESUELTA, no la escrita"
        )

        # --- (6) fail-closed: lo que el SO no resuelve, no se arranca ----------
        assert _ruta_real(os.path.join(tmp, "no_existe.exe")) is None, (
            "`realpath` sin `strict=True` devuelve una ruta inventada para un "
            "fichero inexistente: sin resolver, fail-closed significa NO arrancar"
        )

        # --- (7) la RAIZ tambien puede estar detras de un junction ------------
        # El otro modo de fallar, el falso negativo. Con la raiz LEXICA, este
        # caso se rechaza: la ruta real (`...\\destino_real\\bien.exe`) no esta
        # dentro del alias (`...\\raiz_j`), y una app instalada ahi -que es como
        # esta medio mundo tiene las librerias de juegos- no arrancaria nunca.
        raiz_j = os.path.join(tmp, "raiz_j")
        _mklink(["/J", raiz_j, destino])
        assert svc._resolver_app(os.path.join(raiz_j, "bien.exe"),
                                 raices=[raiz_j]) == _ruta_real(bien), (
            "una app bajo una RAIZ que es un junction debe arrancar: las raices "
            "se resuelven por el mismo camino que las candidatas, o el criterio "
            "se aplica a dos medidas distintas y se rechazan apps legitimas"
        )
    finally:
        logger_wopt.removeHandler(captor)
        for enlace in enlaces:
            # El junction de DIRECTORIO se quita con `rmdir` (que quita el
            # enlace, no el destino). `os.remove` sobre un directorio en Windows
            # es un PermissionError, asi que se prueban los dos.
            try:
                os.rmdir(enlace)
            except OSError:
                try:
                    os.remove(enlace)
                except OSError:
                    pass
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(fuera, ignore_errors=True)
    print("Un junction no cuela lo que hay detras (TASK-027 iter 2).")


def test_la_contencion_no_acepta_un_hermano_de_prefijo():
    """TASK-027 iter 2, hallazgo 2 (MEDIA, M10): `commonpath` esta vigilado.

    El mutation-auditor midio que cambiar `commonpath` por `startswith`
    SOBREVIVIA: la suite entera seguía verde. O sea que nadie vigilaba la
    contencion por componentes, y la sustitucion mas obvio de `commonpath` por
    un prefijo de cadena es justo el agujero clasico del hermano:
    `...\\Temp\\wopt_x` como raiz acepta `...\\Temp\\wopt_xEvil\\a.exe`.

    Esta sonda es la que vigila `commonpath`. El hermano se construye de
    verdad, con ficheros reales, para que la asercion no dependa de que exista
    el fichero: asi el rechazo solo puede venir de la contencion.
    """
    import shutil
    import tempfile
    from woptimizer.services.process_service import (
        ProcessService, _dentro_de_alguna, _ruta_real,
    )

    svc = ProcessService.__new__(ProcessService)
    tmp = tempfile.mkdtemp(prefix="wopt_fix003h_")
    hermano = tmp + "Evil"
    try:
        os.mkdir(hermano)
        evil = os.path.join(hermano, "a.exe")
        _escribir_pe_minimo(evil)
        dentro_dir = os.path.join(tmp, "ok")
        os.mkdir(dentro_dir)
        bien = os.path.join(dentro_dir, "a.exe")
        _escribir_pe_minimo(bien)

        # --- el hermano de prefijo, en las dos funciones ----------------------
        assert not _dentro_de_alguna(os.path.normpath(evil), [os.path.normpath(tmp)]), (
            f"{evil} esta FUERA de la raiz {tmp} pero solo comparte PREFIJO de "
            "cadena. Un `startswith` en vez de `commonpath` lo aceptaria: por eso "
            "esta sonda existe"
        )
        assert svc._resolver_app(evil, raices=[tmp]) is None, (
            f"una app de un hermano de prefijo se acepto: {evil} no esta dentro "
            f"de {tmp}"
        )
        # El hermano de la derecha: `C:\a\b` no contiene `C:\a\b2`.
        assert not _dentro_de_alguna(r"C:\a\b2\a.exe", [r"C:\a\b"]), (
            "`C:\\a\\b2\\a.exe` no esta dentro de `C:\\a\\b`: el prefijo de cadena "
            "no es contencion por componentes"
        )
        # --- controles positivos: lo de verdad SI pasa ------------------------
        assert _dentro_de_alguna(os.path.normpath(bien), [os.path.normpath(tmp)]), (
            "un fichero dentro de la raiz tiene que estar contenido: la sonda "
            "estaria probando que nada pasa"
        )
        assert _dentro_de_alguna(os.path.normpath(tmp), [os.path.normpath(tmp)]), (
            "la propia raiz esta contenida en si misma (borde del intervalo)"
        )
        assert _dentro_de_alguna(os.path.normpath(tmp + os.sep),
                                 [os.path.normpath(tmp)]), (
            "la raiz con separador final sigue contenida (borde del intervalo)"
        )
        assert svc._resolver_app(bien, raices=[tmp]) == _ruta_real(bien), (
            "una app de verdad dentro de la raiz debe arrancar: si esta asercion "
            "falla, la sonda no distingue 'contiene' de 'rechaza todo'"
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(hermano, ignore_errors=True)
    print("La contencion no acepta un hermano de prefijo (M10).")


def test_la_contencion_no_depende_de_la_caja():
    """TASK-027 iter 2, hallazgo 4 (MEDIA): `commonpath` normaliza con caja.

    Medido por el auditor: `C:\\PROGRAM FILES\\...` se RECHAZABA. En Windows el
    sistema de ficheros no distingue mayusculas, asi que eso era un falso
    positivo: fail-closed (seguro) pero un bug funcional, porque un programa
    legítimamente instalado con otra caja no arranca nunca.

    DECISION: se normaliza con `os.path.normcase`, y no se documenta como
    limitacion. El argumento para hacerlo y no documentarlo es que `normcase`
    NO ensancha el conjunto aceptado: declara la verdad del SO (que no
    distingue caja), asi que lo que entra es exactamente lo que el SO
    abriria. Y la comprobacion REAL sigue aplicando sobre la ruta resuelta.
    El coste es una llamada por comparacion, y se comprueba en las DOS
    direcciones (raiz en mayusculas y viceversa): si solo se normalizara un
    lado, la mitad de los casos seguiria falling.
    """
    import shutil
    import tempfile
    from woptimizer.services.process_service import (
        ProcessService, _dentro_de_alguna, _ruta_real,
    )

    # --- nivel de la funcion, en las dos direcciones ------------------------
    for raiz, candidata in (
        (r"C:\Program Files", r"C:\PROGRAM FILES\x.exe"),
        (r"C:\PROGRAM FILES", r"C:\Program Files\x.exe"),
        (r"C:\program files", r"C:\PROGRAM FILES\x.exe"),
    ):
        assert _dentro_de_alguna(os.path.normpath(candidata),
                                  [os.path.normpath(raiz)]), (
            f"{candidata} esta dentro de {raiz}: en Windows el sistema de "
            "ficheros no distingue mayusculas, asi que rechazarlo es un falso "
            "positivo que deja apps legitimas sin arrancar"
        )
    # Y la caja no abre la puerta: un camino de verdad ajeno sigue fuera.
    assert not _dentro_de_alguna(r"C:\PROGRAM FILES (x86)\x.exe",
                                  [r"C:\Program Files"]), (
        "`C:\\PROGRAM FILES (x86)` NO esta dentro de `C:\\Program Files`: es un "
        "hermano, no una variante de caja"
    )

    # --- extremo a extremo, con ficheros REALES en otro caso -----------------
    svc = ProcessService.__new__(ProcessService)
    tmp = tempfile.mkdtemp(prefix="wopt_fix003c_")
    try:
        real = os.path.join(tmp, "chrome.exe")
        _escribir_pe_minimo(real)
        mayus = real.upper()
        assert os.path.isfile(mayus), (
            f"este temporal no distingue mayusculas ({mayus} no se ve): la "
            "garantia que se prueba es de NTFS/NTFS-per-directory, y el proyecto "
            "es solo-Windows. Sin esta precondicion el caso pasaria porque el "
            "fichero no existe, no por la caja"
        )
        raiz_mayus = tmp.upper()
        assert svc._resolver_app(mayus, raices=[raiz_mayus]) == _ruta_real(real), (
            "una app escrita en mayusculas dentro de una raiz escrita en "
            "mayusculas debe arrancar: en Windows el SO no distingue caja"
        )
        assert svc._resolver_app(real, raices=[raiz_mayus]) == _ruta_real(real), (
            "y al reves tambien: raiz en mayusculas, app en minusculas"
        )
        # Y fuera sigue siendo fuera, en mayusculas y todo.
        fuera = os.path.join(os.environ["USERPROFILE"], f"wopt_fuera_{os.getpid()}")
        os.makedirs(fuera, exist_ok=True)
        try:
            fuera_exe = os.path.join(fuera, "leak.exe")
            _escribir_pe_minimo(fuera_exe)
            assert os.path.isfile(fuera_exe.upper()), (
                "el temporal de fuera tampoco distingue mayusculas: el caso "
                "negativo pasaria por inexistencia y no por contencion"
            )
            assert svc._resolver_app(fuera_exe.upper(), raices=[tmp]) is None, (
                "un fichero de fuera de la raiz no se arranca por escribirlo en "
                "mayusculas"
            )
        finally:
            shutil.rmtree(fuera, ignore_errors=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("La contencion no depende de la caja de las letras.")


def test_la_guarda_de_shell_true_ve_atributos_y_aliases():
    """TASK-027 iter 2, hallazgo 3 (MEDIA): la guarda anti-`shell=True` era ciega.

    Solo miraba `ast.Name`, asi que `subprocess.Popen(app, shell=True)` -la
    grafia EXACTA del bug original- pasaba sin que la guarda se enterara. Este
    test es el que hace que "ampliar el visitor" sea un hecho y no una
    intencion: le pasa esa grafia, la de un alias de modulo, la de un alias de
    import y la de un `shell` que no es un literal `False`, y exige que las
    cuatro se vean.

    Y exige lo contrario tambien: `shell=False` explicito, `Popen` sin `shell`,
    `subprocess.run` y hasta una CADENA que mencione `shell=True` NO pueden
    marcarse, o la guarda se vuelve un guard que nadie va a querer arreglar
    (y dejaria de leerse).
    """
    deben_ver_se = [
        # La grafia exacta del bug original. Sin `ast.Attribute` esto no se ve.
        "import subprocess\nsubprocess.Popen(app, shell=True)\n",
        "import subprocess as sp\nsp.Popen(app, shell=True)\n",
        "from subprocess import Popen\nPopen(app, shell=True)\n",
        # Alias de import: sin mirar los `ImportFrom` esto tampoco.
        "from subprocess import Popen as abrir\nabrir(app, shell=True)\n",
        # `shell` que no es un literal falso sigue siendo un interprete.
        "import subprocess\nsubprocess.Popen(app, shell=1)\n",
    ]
    for fuente in deben_ver_se:
        assert _hallazgos_shell_true(fuente, "sintetico"), (
            "la guarda anti-shell no vio esta grafia, que es ejecucion por "
            f"interprete:\n{fuente}"
        )

    no_deben_ver_se = [
        "import subprocess\nsubprocess.Popen(app, shell=False)\n",
        "import subprocess\nsubprocess.Popen(app)\n",
        "import subprocess\nsubprocess.run([app], shell=False)\n",
        "import os\nos.startfile(ruta)\n",
        'MENSAJE = "no se usa shell=True en este proyecto"\n',
    ]
    for fuente in no_deben_ver_se:
        assert not _hallazgos_shell_true(fuente, "sintetico"), (
            "falso positivo de la guarda anti-shell: esto no ejecuta nada por "
            f"interprete y marcarla haria que la guarda se ignorara\n{fuente}"
        )

    # Y el PRODUCTO, con la misma guarda, que es la invariante que importa.
    for raiz, _dirs, ficheros in os.walk(os.path.join("src", "woptimizer")):
        for fichero in ficheros:
            if not fichero.endswith(".py"):
                continue
            ruta = os.path.join(raiz, fichero)
            with open(ruta, encoding="utf-8") as fh:
                fallos = _hallazgos_shell_true(fh.read(), ruta)
            assert not fallos, (
                f"{fallos}: vuelve a Popen(..., shell=<interprete>) en {ruta}. El "
                "pack es entrada no confiable (FIX-003)"
            )
    print("La guarda anti-shell ve atributos y alias, y no se equivoca.")


def test_arranque_de_apps_no_usa_shell():
    """TASK-027 / FIX-003: arrancar una app NO es ejecutar un comando.

    Arnés SIN efectos y SIN Tk: `ProcessService.__new__` (no se carga la DB, no
    se toca psutil), `os.startfile` instrumentado y `subprocess.Popen` sembrado.

    Por que el monkeypatch funciona: `os.startfile` y `subprocess.Popen` se
    resuelven como ATRIBUTO DEL MÓDULO en tiempo de llamada, así que
    `setattr(os, "startfile", ...)` es el enganche correcto. Nunca
    `from os import startfile` en producción: eso capturaría la función antes
    del parche y la sonda moriría por un `AttributeError` que solo demostraría
    que el parche no agarró, en vez de por la aserción que importa.

    Hay DOS Popen sembrados porque matan dos mutaciones distintas:
      * `_killer` (BaseException): reintroducir `Popen(app, shell=True)` no es
        digerible por el `except Exception` del código viejo -> sube y mata.
      * `_popen_soniente` (`returncode 1`): aísla el MENTIRO DEL CONTADOR. Con
        `shell=True` un nombre inexistente NO lanza excepción (`cmd.exe`
        responde "no se reconoce como un comando" con código de salida 1), así
        que el código viejo cuenta `started += 1` para una app que no arrancó y
        devuelve (2, 0) donde el contrato exige (1, 1).

    Los ficheros del caso (b) son REALES y vacíos: sin ellos, borrar la lista
    blanca de extensiones no cambiaría nada y la prueba no probaría nada.
    """
    import logging as _logging
    import shutil
    import subprocess
    import tempfile
    from woptimizer.services.process_service import ProcessService, _dentro_de_alguna

    class _ProcesoFalso:
        returncode = 1

    lanzadas = []
    popens = []
    avisos = []

    def _startfile_grabador(ruta, *a, **k):
        lanzadas.append(ruta)

    def _startfile_que_falla(ruta, *a, **k):
        raise OSError("fallo simulado de ShellExecute")

    def _killer(*a, **k):
        raise _PopenProhibido(
            "subprocess.Popen no debe usarse en el arranque de apps: el pack es "
            "entrada no confiable (FIX-003)"
        )

    def _popen_soniente(cmd, *a, **k):
        popens.append(cmd)
        return _ProcesoFalso()

    class _Captor(_logging.Handler):
        def emit(self, record):
            if record.levelno >= _logging.WARNING:
                avisos.append(record.getMessage())

    logger_wopt = _logging.getLogger("woptimizer")
    assert logger_wopt.isEnabledFor(_logging.WARNING), (
        "el logger 'woptimizer' no emite warnings: la asercion (h) no probaria nada"
    )
    captor = _Captor(level=_logging.WARNING)
    logger_wopt.addHandler(captor)

    os_startfile_original = getattr(os, "startfile", None)
    popen_original = subprocess.Popen
    svc = ProcessService.__new__(ProcessService)
    tmp = tempfile.mkdtemp(prefix="wopt_fix003_")
    # El grabador se instala de UNA VEZ y para todo el test: sin esto, (g)
    # llamaria al ShellExecute de verdad sobre un .exe vacio, que responde
    # WinError 193 y mezcla un fallo del SO con la asercion que se quiere probar.
    setattr(os, "startfile", _startfile_grabador)

    def _arrancar(apps, popen_stub=None):
        """`start_pack_apps` con la instrumentación puesta."""
        subprocess.Popen = _killer if popen_stub is None else popen_stub
        try:
            return svc.start_pack_apps(apps)
        except _PopenProhibido as e:
            raise AssertionError(str(e))
        finally:
            subprocess.Popen = popen_original

    try:
        # --- precondiciones: sin ellas los casos de abajo pasan por el motivo
        # equivocado y no prueban la política que dicen probar -----------------
        raices = svc._launch_roots()
        assert raices, "este entorno no define ninguna raiz de arranque permitted"
        assert any(_dentro_de_alguna(os.path.normpath(tmp), raices) for _ in raices), (
            f"el temporal {tmp} cae fuera de las raices de arranque: los casos (b) "
            "y (g) se rechazarian por contencion y no por lo que dicen probar"
        )
        assert os.path.isdir(os.environ.get("ProgramFiles", "")), (
            "ProgramFiles no existe: el caso (c) (traversal) no probaria nada"
        )

        # --- (c) traversal: normalizar ANTES de comprobar la contención ------
        # OJO al ORDEN de los sub-casos: primero las decisiones de
        # `_resolver_app` ((c)-(f)) y despues el efecto ((a), (b), (g), (g2),
        # (h)). Al reves, una mutacion de validacion muere en el primer caso de
        # efecto y la matriz no puede atribuir la muerte a la asercion que la
        # nombra.
        traversal = r"C:\Program Files\..\..\Windows\System32\cmd.exe"
        objetivo = os.path.normpath(traversal)
        assert os.path.isabs(traversal), "el traversal debe ser 'absoluto' para la prueba"
        assert os.path.isfile(objetivo), (
            f"el destino del traversal ({objetivo}) no existe: el caso pasaria "
            "por isfile y no por contencion"
        )
        assert svc._resolver_app(traversal) is None, (
            f"el traversal se normaliza a {objetivo}, que esta FUERA de las "
            "raices permitidas, y aun asi se acepto"
        )

        # --- (d) UNC: ejecución remota por SMB -------------------------------
        unc = r"\\servidor\comparte\p.exe"
        assert os.path.isabs(unc), "una UNC es 'absoluta' para os.path: por eso isabs no vale"
        avisos.clear()
        assert svc._resolver_app(unc) is None, "una ruta UNC jamas se ejecuta"
        assert any("UNC" in m for m in avisos), (
            f"el rechazo UNC no deja el motivo en el log: {avisos}"
        )

        # --- (e) nombre pelado: SOLO dentro de las raices permitidas --------
        chrome = os.path.join(tmp, "chrome.exe")
        _escribir_pe_minimo(chrome)
        assert svc._resolver_app("chrome.exe", raices=[tmp]) == os.path.normpath(chrome), (
            "un nombre pelado solo se resuelve dentro de las raices permitidas, y "
            "nunca por el PATH ni por el CWD (shutil.which busca en el CWD primero)"
        )

        # --- (f) nombre pelado inexistente -----------------------------------
        assert svc._resolver_app("no_existe_en_ningun_site.exe", raices=[tmp]) is None, (
            "un nombre pelado que no esta en las raices permitidas no se arranca"
        )

        # --- (a) metacarácteres con intérprete -------------------------------
        # OJO: `r"...\"` NO es Python valido (una cadena cruda no puede acabar
        # en backslash), por eso el separador final va doblado.
        inyeccion = "C:\\Windows\\notepad.exe & del /q C:\\"
        lanzadas.clear()
        assert _arrancar([inyeccion]) == (0, 1), (
            f"una ruta con '&' debe contar como fallida y no lanzarse: "
            f"quedaron {lanzadas}"
        )
        assert lanzadas == [], f"se lanzo la entrada con metacarácteres: {lanzadas}"

        # --- (b) la lista blanca de extensiones (ficheros REALES) -----------
        # OJO, y es lo importante: estos ficheros llevan CONTENIDO DE PE DE
        # VERDAD a proposito. Si fueran guiones vacios, los rechazaria la regla 9
        # ("no es una imagen PE") y este caso pasaria por el motivo equivocado:
        # la extension se dejaria de comprobar sin que nadie lo notase, que es
        # exactamente como esta sonda se vuelve verde sin estar probando nada.
        # Con un PE dentro, lo UNICO que puede rechazarlos es la lista blanca de
        # extensiones, que es lo que este caso dice que prueba.
        rutas_b = []
        for nombre in ("evil.bat", "evil.ps1", "evil.vbs", "atajo.lnk"):
            p = _escribir_pe_minimo(os.path.join(tmp, nombre))
            rutas_b.append(p)
        lanzadas.clear()
        assert _arrancar(rutas_b) == (0, 4), (
            "una .bat/.ps1/.vbs/.lnk NO se puede arrancar: pasarian por "
            f"ShellExecute -> cmd.exe /c. Se lanzo: {lanzadas}"
        )
        assert lanzadas == [], f"se lanzo un fichero de la lista negra: {lanzadas}"
        # Y la extension se mira de verdad, no de paso: con el mismo contenido PE,
        # un `.exe` SI arranca y un `.bat` no. Sin esta asercion, borrar la lista
        # blanca no cambiaria el resultado del caso (b) y la sonda no lo notaria.
        p_ejecutado = os.path.join(tmp, "mismo_contenido.exe")
        shutil.copyfile(rutas_b[0], p_ejecutado)
        lanzadas.clear()
        assert _arrancar([p_ejecutado]) == (1, 0), (
            f"el MISMO contenido con extension .exe tiene que arrancar: la "
            f"diferencia la hace la extension y no el contenido: {lanzadas}"
        )

        # --- (g) el contador es HONESTO --------------------------------------
        real = os.path.join(tmp, "real.exe")
        _escribir_pe_minimo(real)
        lanzadas.clear()
        popens.clear()
        res = _arrancar([real, "fantasma.exe"], popen_stub=_popen_soniente)
        assert res == (1, 1), (
            f"contador mentiroso: {res}. El codigo viejo devolvia (2, 0) porque "
            "`shell=True` NO lanza con un nombre inexistente y contaba `started`"
        )
        assert lanzadas == [os.path.normpath(real)], (
            f"el grabador recibio rutas que no debian lanzarse: {lanzadas}"
        )
        assert popens == [], f"Popen no debe usarse ni en el camino bueno: {popens}"

        # --- (g2) un ShellExecute que falla cuenta como fallido -------------
        setattr(os, "startfile", _startfile_que_falla)
        avisos.clear()
        try:
            assert _arrancar([real]) == (0, 1), (
                "si ShellExecute lanza OSError, la app cuenta como fallida y no "
                "como arrancada"
            )
            assert any("Failed to launch" in m for m in avisos), (
                f"un OSError de ShellExecute sin log es un fallo invisible: {avisos}"
            )
        finally:
            setattr(os, "startfile", _startfile_grabador)

        # --- (h) un rechazo deja el MOTIVO en el log -------------------------
        # Se mira la linea EXACTA de `start_pack_apps` ("no se arranco"), no un
        # "hubo algún warning": si solo se comprobara `avisos`, el warning del
        # resolutor taparia el de aqui y la mutacion "sin log en el rechazo"
        # pasaria en verde.
        avisos.clear()
        _arrancar([traversal])
        assert avisos, (
            "un rechazo sin log es un rechazo invisible: el usuario edita su "
            "profiles.json a mano y no puede depurar por que su app no arranca"
        )
        assert any("no se arranco" in m for m in avisos), (
            f"start_pack_apps no registro el rechazo en el log: {avisos}"
        )
        # Y el resolutor deja su propio resumen con el MOTIVO. Son dos lineas
        # distintas a proposito: una dice QUE app fallo, la otra POR QUE.
        assert any("Arranque rechazado" in m for m in avisos), (
            f"el resolutor no registro el motivo del rechazo: {avisos}"
        )

        # --- guarda estatica: `shell=True` no vuelve a aparecer en src/ ------
        # Usa la MISMA funcion que `test_la_guarda_de_shell_true_ve_atributos_y
        # alias_es`: una guarda duplicada con distinta cobertura es dos
        # guardingitas, y la anterior solo miraba `ast.Name` (era ciega a
        # `subprocess.Popen(..., shell=True)`, la grafia exacta del bug).
        for raiz, _dirs, ficheros in os.walk(os.path.join("src", "woptimizer")):
            for fichero in ficheros:
                if not fichero.endswith(".py"):
                    continue
                ruta = os.path.join(raiz, fichero)
                with open(ruta, encoding="utf-8") as fh:
                    fallos = _hallazgos_shell_true(fh.read(), ruta)
                assert not fallos, (
                    f"{fallos}: vuelve a Popen(..., shell=True): el pack es "
                    "entrada no confiable (FIX-003)"
                )
    finally:
        subprocess.Popen = popen_original
        if os_startfile_original is not None:
            setattr(os, "startfile", os_startfile_original)
        else:
            try:
                delattr(os, "startfile")
            except AttributeError:
                pass
        logger_wopt.removeHandler(captor)
        shutil.rmtree(tmp, ignore_errors=True)
    print("El arranque de apps no usa shell (FIX-003).")


def test_el_gestor_guarda_la_ruta_absoluta():
    """TASK-027 / FIX-003 (escritor): lo que se guarda en `Pack.apps`.

    Sin Tk: la vista se construye con `__new__` y sus colaboradores son
    dobles. La asercion mira el CONTENIDO de `pack.apps`, no "que se llamo a
    save()": un `save()` que se sigue llamando con el nombre pelado dentro
    pasaría cualquier prueba de llamada.

    MATA, una a una:
      * `procs[0].full_name` (el estado anterior) -> la ruta absoluta no aparece;
      * `procs[0].name` (que es el nombre SIN extensión, `process_service.py:244`)
        -> ni la ruta ni `chrome.exe`;
      * sin degradación cuando `exe_path` está vacía -> se guarda `""` y el pack
        queda inservible sin explicación;
      * sin el `if not in target_pack.apps` -> el mismo proceso se guarda dos
        veces (y el pack de fábrica se hincha con duplicados en cada clic).
    """
    from woptimizer.models import Pack, ProcessInfo
    from woptimizer.ui.views.process_manager_view import ProcessManagerView

    class _Casilla:
        def __init__(self, valor):
            self._valor = valor

        def get(self):
            return self._valor

    class _Var:
        def __init__(self, valor):
            self._valor = valor

        def get(self):
            return self._valor

    class _Label:
        def __init__(self):
            self.textos = []

        def configure(self, **kw):
            self.textos.append(kw.get("text"))

    class _PackServiceGrabador:
        """Doble que modela el CONTRATO de `PackService`, no su codigo (TASK-062).

        El servicio real devuelve **copias defensivas** de `get_all_packs()`
        (`model_copy(deep=True)` sobre una cache de dos capas) y la UNICA via
        que persiste es `update_pack()`, que ademas invalida la cache. Un doble
        que devolviera los mismos objetos haria que `on_add_to_pack` pasara
        **aunque no guardara nada**: la mutacion se veria en memoria y
        `save()` --que serializa el estado interno-- no la veria nunca. Ese fue
        el bug real, y este doble lo hacia invisible.

        `save()` se mantiene a proposito: si alguien vuelve a llamar a `save()`
        en vez de `update_pack()`, el test debe morir por la **asercion** (lo
        guardado esta vacio), no por un `AttributeError`. Un fallo de codigo no
        es una discriminacion.
        """

        def __init__(self, packs):
            self._packs = packs
            self.saves = 0
            self.actualizados = []

        def get_all_packs(self):
            return {k: p.model_copy(deep=True) for k, p in self._packs.items()}

        def update_pack(self, pack):
            self._packs[pack.id] = pack.model_copy(deep=True)
            self.actualizados.append(pack.id)
            self.saves += 1

        def save(self):
            self.saves += 1

    def _guardado(vista, p_id="a"):
        """Lo que el SERVICIO tiene de verdad, no el `pack` que la vista recibio.

        Leer el `pack` original es lo que hacia pasar este test con el bug
        puesto: la vista mutaba la copia, el original nunca cambiaba, y aun asi
        la asercion veia la mutacion en la copia compartida.
        """
        return vista.pack_service._packs[p_id]

    RUTA_CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    def _armar(pack, claves):
        vista = ProcessManagerView.__new__(ProcessManagerView)
        vista.grouped_processes = {
            k: [ProcessInfo(name="chrome", full_name="chrome.exe", pid=100 + i,
                             exe_path=RUTA_CHROME, category="x", priority="none",
                             description="d")]
            for i, k in enumerate(claves)
        }
        vista.checkboxes = {k: _Casilla(True) for k in claves}
        vista.pack_var = _Var("Pack A")
        vista.status_label = _Label()
        vista.pack_service = _PackServiceGrabador({"a": pack})
        return vista

    # --- (1) con exe_path: se guarda la RUTA, no el nombre -------------------
    # TASK-062: las tres aserciones leen `_guardado(vista)`, es decir lo que el
    # servicio PERSISTE. Antes leian el `pack` original, que la vista nunca
    # tocaba (mutaba una copia), asi que el test pasaba con `save()` en vez de
    # `update_pack()`: el falso verde exacto que escondia el bug.
    pack = Pack(id="a", name="Pack A")
    vista = _armar(pack, ["chrome"])
    vista.on_add_to_pack()
    assert _guardado(vista).apps == [RUTA_CHROME], (
        f"lo PERSISTIDO no es la ruta absoluta: {_guardado(vista).apps}. Con el nombre "
        "pelado el arranque lo resuelve adivinando en las raices permitidas y lo rechaza"
    )
    assert vista.pack_service.saves == 1, "update_pack() debe llamarse una vez"

    # --- (2) sin exe_path (AccessDenied): degradación documentada ------------
    pack = Pack(id="a", name="Pack A")
    vista = ProcessManagerView.__new__(ProcessManagerView)
    vista.grouped_processes = {
        "chrome": [ProcessInfo(name="chrome", full_name="chrome.exe", pid=7,
                               exe_path="", category="x", priority="none", description="d")]
    }
    vista.checkboxes = {"chrome": _Casilla(True)}
    vista.pack_var = _Var("Pack A")
    vista.status_label = _Label()
    vista.pack_service = _PackServiceGrabador({"a": pack})
    vista.on_add_to_pack()
    assert _guardado(vista).apps == ["chrome.exe"], (
        f"con exe_path vacia hay que degradar a full_name y PERSISTIRLO, no guardar '': "
        f"{_guardado(vista).apps}"
    )

    # --- (3) duplicado: el `if not in apps` sigue vivo -----------------------
    pack = Pack(id="a", name="Pack A", apps=[RUTA_CHROME])
    vista = _armar(pack, ["chrome", "chrome2"])
    vista.on_add_to_pack()
    assert _guardado(vista).apps == [RUTA_CHROME], (
        f"se duplico la misma app en lo persistido: {_guardado(vista).apps}"
    )
    assert vista.status_label.textos[-1].startswith("✅ 0 apps"), (
        f"el contador de anadidas miente: {vista.status_label.textos[-1]}"
    )
    print("El Gestor PERSISTE la ruta absoluta en el pack (FIX-003 + TASK-062).")


def test_orden_de_categorias_no_es_alfabetico():
    """TASK-027 / FIX-004: el orden de secciones es `CATEGORY_ORDER`, no `sorted()`.

    Por que una guarda `ast` ademas del comportamiento: los dos sitios
    sintomaticos (`_render_list` y `_render_pack_card`) construyen widgets, y
    probarlos exigiría una ventana de Tk. El repo ya usa este patrón
    (TASK-026 lo hizo con `self.master.after`). La guarda corre PRIMERO, sin Tk,
    y falla en <1 s si alguien reintroduce `sorted()` sobre las categorías.

    MATA:
      * `return list(cats)` (la identidad) -> la entrada barajada sigue barajada;
      * `sorted(...)` -> ⚪ (U+26AA, BMP) sale PRIMERO y la aserción `!= sorted`
        falla; es la medición del defecto, no una opinión sobre el orden;
      * el centinela cambiado de signo -> las desconocidas dejan de ir al final;
      * `sorted(categorias.keys())` en CUALQUIERA de los dos sitios -> la guarda;
      * un `key=` en línea en vez de `ordenar_categorias` -> la guarda de uso,
        para que no se "arregle" duplicando la política en cada vista.
    """
    import random
    from woptimizer.config import CATEGORY_ORDER, ordenar_categorias

    # --- comportamiento: entrada barajada con SEMILLA fija -------------------
    entrada = list(CATEGORY_ORDER)
    random.Random(20260930).shuffle(entrada)
    salida = ordenar_categorias(entrada)
    conocidas = [c for c in CATEGORY_ORDER if c in entrada]
    assert salida[:len(conocidas)] == conocidas, (
        "orden de categorias no es CATEGORY_ORDER: "
        f"esperado {conocidas}, obtenido {salida}"
    )
    assert salida != sorted(entrada), (
        "la salida es identica a sorted(): el defecto sigue vivo. Medido: "
        f"sorted() pone {sorted(entrada)[0]!r} primero porque ⚪ Otros es U+26AA "
        "y 🟢🟡🔴 estan en el plano suplementario"
    )
    assert salida[-1] == CATEGORY_ORDER[-1], (
        "el centinela canonico (sin clasificar) va SIEMPRE el ultimo"
    )
    assert list(entrada) != salida or entrada == sorted(entrada, key=lambda c: 0), (
        "ordenar_categorias no debe depender del orden de entrada para las conocidas"
    )

    # --- categorías desconocidas: AL FINAL, en su orden de entrada -----------
    desconocidas = ["ZZZ inventada", "AAA inventada", "MMM inventada"]
    mezcla = desconocidas + CATEGORY_ORDER[:3]
    salida2 = ordenar_categorias(mezcla)
    assert salida2[:3] == CATEGORY_ORDER[:3], (
        f"las conocidas no van primero: {salida2}"
    )
    assert salida2[3:] == desconocidas, (
        f"las desconocidas van al final conservando su orden relativo: {salida2}"
    )

    # --- guarda estatica sobre los DOS sitios -------------------------------
    for nombre in ("process_manager_view.py", "pack_manager_view.py"):
        ruta = os.path.join("src", "woptimizer", "ui", "views", nombre)
        with open(ruta, encoding="utf-8") as fh:
            arbol = ast.parse(fh.read())

        usa_ordenador = False
        for nodo in ast.walk(arbol):
            if (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)
                    and nodo.func.id == "ordenar_categorias"):
                usa_ordenador = True
            if not (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)
                    and nodo.func.id == "sorted"):
                continue
            if any(kw.arg == "key" for kw in nodo.keywords):
                continue  # sorted(categorias[cat], key=...) es legitimo
            texto = ast.unparse(nodo.args[0]).lower() if nodo.args else ""
            if "cat" in texto:
                raise AssertionError(
                    f"{ruta}:{nodo.lineno} vuelve a sorted() sobre categorias "
                    f"({texto!r}): ordena por punto de codigo y saca ⚪ Otros "
                    "primero. Usar config.ordenar_categorias (FIX-004)"
                )
        assert usa_ordenador, (
            f"{ruta} no llama a ordenar_categorias: el orden de secciones debe "
            "salir de CATEGORY_ORDER, no de una key en linea duplicada"
        )
    print("El orden de categorias es CATEGORY_ORDER y no alfabetico (FIX-004).")


def test_toggle_favorite_desmarca():
    """TASK-027 / FIX-006: la segunda pulsacion de la estrella DESMARCA.

    El servicio ya sabia hacerlo: `set_favorite(None)` existe desde TASK-021 y
    esta testeado en `test_pack_service_favorite_exclusive`. El bug era de UNA
    linea en la UI, y por eso esta sonda no toca `PackService`.

    El grabador devuelve INSTANCIAS NUEVAS en cada `get_all_packs()`, como el
    servicio real tras un `model_copy`. Eso es lo que permite matar la lectura
    de una instantánea: `render_pack` es la instancia que el renderiator habría
    capturado, y su `is_favorite` es intencionadamente el VALOR VIEJO.

    MATA:
      * `set_favorite(pack_id)` incondicional (el estado anterior) -> el caso 2
        registra "a" y no `None`;
      * leer el `is_favorite` de la instantánea del render -> el grabador
        devuelve instancias nuevas, la instantánea queda obsoleta y el caso 2
        falla;
      * el atajo `get_favorite_pack()` (el grabador lo tiene, para que la
        mutación sea expresable) -> con DOS favoritos devuelve el primero y el
        caso 4 falla: marcaría "b" en vez de desmarcarlo;
      * quitar la guarda `if pack is None: return` (o, en su forma literal, el
        `pack is not None and` de la guarda) -> el caso 3 registra "z", y con la
        variante sin `and` además revienta con el `AttributeError` del `None`.
    """
    from woptimizer.models import Pack
    from woptimizer.ui.views.pack_manager_view import PackManagerView

    class _Grabador:
        def __init__(self, estado):
            self.estado = dict(estado)
            self.llamadas = []

        def get_all_packs(self):
            return {k: Pack(id=k, name=k.upper(), is_favorite=v)
                    for k, v in self.estado.items()}

        def get_favorite_pack(self):
            for k, v in self.estado.items():
                if v:
                    return self.get_all_packs()[k]
            return None

        def toggle_favorite(self, pack_id):
            self.llamadas.append(pack_id)
            if pack_id in self.estado:
                self.estado[pack_id] = not self.estado[pack_id]
                return self.estado[pack_id]
            return False

        def set_favorite(self, pack_id, value=True):
            self.llamadas.append((pack_id, value))
            if pack_id in self.estado:
                self.estado[pack_id] = value

    def _vista(grabador):
        v = PackManagerView.__new__(PackManagerView)
        v.pack_service = grabador
        v.refresh_packs = lambda: None
        # Instantanea que el render de la tarjeta habria capturado. El codigo
        # real NO debe leerla: se queda obsoleta en cuanto el estado cambia.
        v.render_pack = Pack(id="a", name="A", is_favorite=False)
        return v

    # (2) YA favorito -> se desmarca
    g = _Grabador({"a": True, "b": False})
    v = _vista(g)
    v.toggle_favorite("a")
    assert g.llamadas == ["a"], f"se debe invocar toggle_favorite('a'): {g.llamadas}"
    assert g.estado == {"a": False, "b": False}, f"el pack 'a' debió desmarcarse: {g.estado}"

    # (4) DOS favoritos (TASK-048 / TASK-053): la estrella del segundo lo desmarca a ÉL
    #     y preserva intacto el primero (favoritos acumulativos, no exclusivos).
    g = _Grabador({"a": True, "b": True})
    v = _vista(g)
    v.toggle_favorite("b")
    assert g.llamadas == ["b"], f"se debe alternar 'b': {g.llamadas}"
    assert g.estado == {"a": True, "b": False}, (
        f"con favoritos acumulativos, desmarcar 'b' debe dejar 'a' marcado: {g.estado}"
    )

    # (1) no favorito -> se marca
    g = _Grabador({"a": False, "b": False})
    v = _vista(g)
    v.toggle_favorite("a")
    assert g.llamadas == ["a"], f"una app no favorita debe marcarse: {g.llamadas}"
    assert g.estado == {"a": True, "b": False}, f"el estado debe quedar marcado: {g.estado}"

    # (3) id que no existe: no lanza y no llama al servicio
    g = _Grabador({"a": False})
    v = _vista(g)
    v.toggle_favorite("z")
    assert g.llamadas == [], (
        f"un id inexistente no debe tocar el servicio: {g.llamadas}"
    )

    # TASK-053: Comprobación AST de que no existe ninguna llamada a set_favorite con 1 argumento en run_tests.py
    import ast
    with open(__file__, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())
    single_arg_calls = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "set_favorite"):
            if len(node.args) == 1:
                single_arg_calls.append(node.lineno)
    assert not single_arg_calls, f"Llamadas a set_favorite con 1 solo argumento halladas en run_tests.py líneas: {single_arg_calls}"

    print("La estrella alterna favoritos acumulativamente (FIX-006 / TASK-053).")


def test_logging_va_a_fichero_y_no_a_stderr():
    """FIX-010: el contrato de log de `docs/ai/architecture.md` §5 ("los errores
    se canalizan a woptimizer.log") tiene que cumplirse SIN depender de que
    alguien pase por `__main__`.

    QUE MATA, y por que esta sonda no es tautologica:
      * Hoy `config.py` no expone `setup_logging` -> AttributeError.
      * Una implementacion SIN `force=True` deja vivo un handler ajeno: el aviso
        sigue yendose a su stderr (parte 2 de abajo, con el espia de por medio) y
        ademas quedan DOS handlers en el root.
      * Una implementacion que no escriba a fichero tampoco pasa: sin handler en
        el root, la stdlib manda el aviso a `lastResort` (stderr).
    """
    import contextlib
    import logging
    from woptimizer.config import _app_dir, logger, setup_logging

    root = logging.getLogger()
    handlers_prev = root.handlers[:]
    level_prev = root.level
    log_path = os.path.join(_app_dir(), "woptimizer.log")

    try:
        # (1) Destino: UN handler de fichero, y el aviso ACABA dentro. La
        #     afirmacion es sobre el CONTENIDO del log, no sobre "se llamo".
        root.handlers.clear()
        setup_logging()

        ficheros = [h for h in root.handlers if isinstance(h, logging.FileHandler)]
        assert len(ficheros) == 1, (
            "setup_logging() debe instalar UN handler de fichero, instala "
            f"{[type(h).__name__ for h in root.handlers]}"
        )
        assert os.path.basename(ficheros[0].baseFilename) == "woptimizer.log", (
            f"el log no va a woptimizer.log: {ficheros[0].baseFilename}"
        )
        assert os.path.normcase(ficheros[0].baseFilename) == os.path.normcase(log_path), (
            f"el log deberia ir al lado de la app: {ficheros[0].baseFilename}"
        )

        marca = "Sonda-FIX-010-al-fichero"
        err1 = io.StringIO()
        with contextlib.redirect_stderr(err1):
            logger.warning(marca)
        assert marca not in err1.getvalue(), (
            "sin fichero la stdlib manda el aviso a stderr (lastResort): "
            f"{err1.getvalue()!r}"
        )
        with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
            cola = fh.read()[-8000:]
        assert marca in cola, (
            "el aviso no llego a woptimizer.log: el contrato de architecture.md "
            "se estaria cumpliendo solo a medias"
        )

        # (2) IDEMPOTENCIA REAL, que es lo que hace `force=True` obligatorio. Se
        #     SIEMBRA un handler ajeno a stderr: sin `force=True`, `basicConfig()`
        #     es un no-op mudo, el handler sobrevive y su aviso se escapa por
        #     stderr. Con `force=True` se cierra, se quita y solo queda el
        #     fichero. Por eso NO se cuenta "handlers llamados" sinohandlers
        #     SUPERVIVIENTES: contar llamadas seria tautologico.
        err2 = io.StringIO()
        marca2 = marca + "-idempotente"
        with contextlib.redirect_stderr(err2):
            root.addHandler(logging.StreamHandler(sys.stderr))
            setup_logging()
            supervivientes = list(root.handlers)
            logger.warning(marca2)
        assert marca2 not in err2.getvalue(), (
            "la segunda llamada de setup_logging() dejo vivo un handler previo: "
            f"sin force=True basicConfig es un no-op. Quedan "
            f"{[type(h).__name__ for h in supervivientes]}"
        )
        assert len(supervivientes) == 1, (
            "la segunda llamada debe dejar UN handler en el root, deja "
            f"{[type(h).__name__ for h in supervivientes]}"
        )
        assert isinstance(supervivientes[0], logging.FileHandler) and os.path.basename(
            supervivientes[0].baseFilename
        ) == "woptimizer.log", (
            f"la segunda llamada debe reinstalar el handler de fichero, deja "
            f"{[type(h).__name__ for h in supervivientes]}"
        )
    finally:
        for h in root.handlers:
            if not any(h is p for p in handlers_prev):
                h.close()
        root.handlers[:] = handlers_prev
        root.setLevel(level_prev)

    print("Los avisos van a woptimizer.log y no se escapan a stderr (FIX-010).")


def test_la_consulta_de_version_no_puede_desincronizarse():
    """FIX-018: la version vivia en DOS ficheros y DESINCRONIZADA
    (`pyproject.toml` = "3.0.0", `__init__.py` = "3.0.0.dev0"). Una pregunta que
    la app hace de si misma no puede tener dos respuestas.

    QUE MATA: hoy los dos valores no coinciden, y la asercion de contenido es
    exactamente esa. No es un test de "existe el atributo": compara los dos
    valores leidos de las FUENTES, con la version ya unificada.
    """
    import re
    import tomllib

    raiz = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(raiz, "pyproject.toml"), "rb") as fh:
        v_pyproject = tomllib.load(fh)["project"]["version"]

    # NUNCA `import woptimizer` para leer la version: importarlo EJECUTA el
    # paquete entero. Se parsea el texto con `ast`, que solo mira el literal.
    ruta_init = os.path.join(raiz, "src", "woptimizer", "__init__.py")
    with open(ruta_init, encoding="utf-8") as fh:
        arbol = ast.parse(fh.read(), filename=ruta_init)
    v_init = None
    for nodo in arbol.body:
        if not isinstance(nodo, ast.Assign):
            continue
        for objetivo in nodo.targets:
            if getattr(objetivo, "id", None) == "__version__":
                v_init = ast.literal_eval(nodo.value)

    assert v_init is not None, "src/woptimizer/__init__.py no declara __version__"
    assert v_init == v_pyproject, (
        f"la version esta desincronizada: pyproject.toml dice {v_pyproject!r} y "
        f"__init__.py dice {v_init!r}. Se declara UN solo valor en los dos sitios."
    )

    # M7: el TERCER sitio existia y esta sonda no lo miraba. Con
    # `.taskmaster/tasks.json` a "0.0.1" la suite declaraba los tres sitios
    # coherentes. Un test llamado "no_puede_desincronizarse" que deja vivo un
    # desincronizador real es PEOR que no tener test: da la seguridad que el
    # nombre promete y no existe.
    import json as _json
    with open(os.path.join(raiz, ".taskmaster", "tasks.json"), encoding="utf-8") as fh:
        v_tasks = _json.load(fh).get("version")
    assert v_tasks == v_pyproject, (
        f"la version esta desincronizada: .taskmaster/tasks.json dice {v_tasks!r} y el resto "
        f"dicen {v_pyproject!r}. Los tres sitios declaran el MISMO valor, incluido el tablero "
        "de tareas, que es lo que lee el orquestador."
    )

    # Y que no aparezca un TERCER sitio que vuelva a separarlos. El filtro pasa
    # de "la linea contiene 'version'" a DOS condiciones: la linea lleva un
    # literal semver Y un token de version. Con `\b` no se cuela `Verificar` ni
    # `servicio`; y asi entra `ver = "9.9.9"` en woptimizer.spec, que el filtro
    # viejo noellia porque no decia la palabra "version" (M9).
    semver = re.compile(r"\b\d+\.\d+\.\d+(?:\.dev\d+)?\b")
    token_version = re.compile(r"(\bver\b|\bversions?\b|__version__|--version)", re.IGNORECASE)
    for nombre in ("woptimizer.spec", "build.bat", "force_build.py"):
        ruta = os.path.join(raiz, nombre)
        if not os.path.exists(ruta):
            continue
        with open(ruta, encoding="utf-8", errors="replace") as fh:
            for num, linea in enumerate(fh.read().splitlines(), 1):
                if not token_version.search(linea):
                    continue
                for encontrada in semver.findall(linea):
                    assert encontrada == v_pyproject, (
                        f"{nombre}:{num} declara otra version ({encontrada!r}); la "
                        f"unica buena es {v_pyproject!r}"
                    )

    # M10: un CUARTO sitio de version en cualquier `.py` del paquete. Hoy solo
    # existe `__version__` en `__init__.py`; cualquier otra asignacion a nivel
    # de modulo con nombre de version es un sitio que vuelve a desincronizarse
    # sin que el escaner de arriba la mire (esos ficheros no se escanean).
    import re as _re
    # Que CONTENGA "version" (no que empiece por ella): `APP_VERSION` y `WOPT_VERSION`
    # son el cuarto sitio de version que se_BUSCA_, no solo `__version__`.
    nombre_version = _re.compile(r"^(?:__)?\w*version\w*$|^ver$", _re.IGNORECASE)
    src_dir = os.path.join(raiz, "src", "woptimizer")
    for dirpath, _dirs, files in os.walk(src_dir):
        for fichero in files:
            if not fichero.endswith(".py"):
                continue
            ruta_py = os.path.join(dirpath, fichero)
            rel = os.path.relpath(ruta_py, raiz).replace("\\", "/")
            with open(ruta_py, encoding="utf-8") as fh:
                arbol_py = ast.parse(fh.read(), filename=ruta_py)
            for stmt in arbol_py.body:
                if not isinstance(stmt, (ast.Assign, ast.AnnAssign)):
                    continue
                objetivos = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
                valor = stmt.value
                if not isinstance(valor, ast.Constant) or not isinstance(valor.value, str):
                    continue
                for objetivo in objetivos:
                    nombre = getattr(objetivo, "id", None)
                    if not nombre or not nombre_version.match(nombre):
                        continue
                    assert rel == "src/woptimizer/__init__.py" and nombre == "__version__", (
                        f"{rel} declara {nombre} = {valor.value!r} a nivel de modulo: ese es un "
                        f"CUARTO sitio de version y puede desincronizarse de {v_pyproject!r} sin "
                        "que nada lo note (M10). La unica version del paquete se declara una vez."
                    )

    print("pyproject.toml, __init__.py y tasks.json declaran la MISMA version (FIX-018).")


# --- TASK-028 iteracion 2: cerrar los supervivientes del mutation-auditor --------
# Esta iteracion NO reimplementa nada de TASK-028: vigila lo que TASK-028 AFIRMO.
# Cada sonda lleva escrito que mutacion la mata, porque una guarda sin mutacion
# asociada es un deseo (regla del ciclo #18).


def _entorno_git_del_repo():
    """(repo_root, env) con el MISMO `GIT_DIR` que usa `git_safe_commit.py`.

    El `.git` de este repositorio NO vive en el arbol de trabajo: esta corrupto
    por el VFS de Nextcloud. El historial real esta en
    `%LOCALAPPDATA%\\woptimizer_git\\.git`. Sin montar aqui ese entorno,
    `git check-ignore` responderia por OTRO repo y la sonda pasaria sin haber
    mirado nada: verde por el motivo equivocado, que es el modo de fallo que
    este ciclo esta cazando. La precedencia ("si el entorno ya trae GIT_DIR se
    respeta") es la de `git_safe_commit.get_env()` y la via documentada en
    AGENTS.md.
    """
    repo_root = os.path.dirname(os.path.abspath(__file__))
    env = os.environ.copy()
    env["GIT_DIR"] = env.get("GIT_DIR") or os.path.expandvars(r"%LOCALAPPDATA%\woptimizer_git\.git")
    env["GIT_WORK_TREE"] = repo_root
    return repo_root, env


def _git(args, env, cwd):
    """Ejecuta `git` y devuelve (rc, salida). `rc is None` = no llego a ejecutarse.

    La distincion importa y no es decorativa: "git fallo" y "no pude ni
    comprobar" NO son lo mismo. Una guarda que se salta sola cuando no puede
    comprobar es una guarda que ya no guarda (y por eso N1 no hace `skip`:
    falla fuerte, con el motivo a la vista).
    """
    import subprocess
    try:
        r = subprocess.run(
            ["git"] + args, cwd=cwd, env=env, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=120,
        )
        return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()
    except Exception as e:
        return None, str(e)


def _rasgos_del_esquema_v2_retirado(doc):
    """Esquema v2 RETIRado presente en `doc`. -> (bool, rasgos_que_lo_delatan).

    ITERACION 4. Esto NO es "el fichero tiene una clave rara": `Pack` es
    `extra="allow"`, asi que un campo de usuario llamado `factory` o
    `kill_low_chat` es un documento LEGITIMO que la app abre sin quejarse. La
    sonda anterior hacia `{"factory","kill_low_chat"} & set(registro)` sobre
    CUALQUIER registro, de modo que un solo campo de usuario declaraba que el
    esquema retirado habia vuelto - y el mensaje pedia borrar el fichero del
    usuario. Eso no es un falso positivo de test: es una sonda capaz de matar
    los packs de alguien.

    El criterio, entonces, es la COMBINACION, medido contra el
    `docs/archive/legacy-root-data/profiles.json` real (420 bytes). Los rasgos
    se cuentan **dentro del MISMO registro**, porque en el archivado asi es como
    aparecen: el registro `__system_gaming__` lleva a la vez el nombre de la
    clave, `factory`, `kill_low_chat` y `kind: "system"`. Dos rasgos ya bastan
    para declararlo, y uno solo NO: un discriminante unico es fragil por
    definicion (es exactamente el nombre que un usuario puede elegir).
    """
    if not isinstance(doc, dict) or not isinstance(doc.get("profiles"), dict):
        return False, []
    for nombre, registro in doc["profiles"].items():
        if not isinstance(registro, dict):
            continue
        rasgos = []
        if nombre == "__system_gaming__":
            rasgos.append("la clave de registro se llama '__system_gaming__'")
        if "factory" in registro:
            rasgos.append("el campo 'factory' (el v2 se anidaba a si mismo)")
        if "kill_low_chat" in registro:
            rasgos.append("el campo 'kill_low_chat'")
        if registro.get("kind") == "system":
            rasgos.append("el campo 'kind' con valor 'system'")
        if len(rasgos) >= 2:
            return True, rasgos
    return False, []


def _leer_documento_de_packs(ruta):
    """Lee el `profiles.json` de `ruta`. -> (documento, motivo, crudo).

    Un documento ilegible NO es un fallo: es estado local del usuario, y la app
    lo tolera. Se devuelve `(None, "por que", "")` y el que llama avisa.

    ITERACION 5, F1. El `open()` y el `read()` tienen que estar DENTRO del
    `try`: fuera, el `except (OSError, UnicodeDecodeError)` era codigo muerto
    (medido: `profiles.json` no-UTF8, truncado a mitad de un emoji y sin
    permiso de lectura, los tres con la suite en rojo por traceback). Y el
    ORDEN importa igual: `UnicodeDecodeError` es subclase de `ValueError`, o
    sea que con `ValueError` primero la rama de lectura no se alcanza para la
    decodificacion y el aviso culpa al JSON de un fallo de bytes. Va la de
    lectura primero.

    Vive en una FUNCION, y no en linea dentro de la sonda, por una razon
    concreta: el control de mas abajo tiene que ejercitar ESTE codigo. Un
    control que reescribiera la logica probaria una copia, que es el validador
    que se deduce a si mismo.
    """
    import json
    try:
        with open(ruta, encoding="utf-8") as fh:
            crudo = fh.read()
        documento = json.loads(crudo)
    except (OSError, UnicodeDecodeError) as e:
        return None, f"no se puede leer ({e})", ""
    except ValueError as e:
        return None, f"no se puede leer como JSON ({e})", crudo
    if documento is None:
        # D1: `json.loads("null")` NO lanza y devuelve `None`. Sin esta rama el
        # motivo se queda vacio y el aviso sale con un hueco ("... en X y . La
        # app lo tolera"), que es un texto que se lee.
        return None, ("su contenido es el literal JSON `null`, que no es un "
                      "documento de packs"), crudo
    return documento, "", crudo


def test_el_archivo_legacy_esta_versionado_y_no_vuelve_a_la_raiz():
    """M12/M13/M14/M15: la norma "nunca borrar, siempre archivar" no la vigilaba
    NADA, y su fallo es el peor de los silenciosos: sin la excepcion de
    `.gitignore`, un `git add -A` se lleva el `profiles.json` archivado y este
    **desaparece del historico sin error, sin aviso y sin WOPT_FAIL**. El
    directorio seguiria existiendo en el disco de esta maquina: un archivo de
    mentira, que es justo lo que la norma dice impedir.

    LA TRAMPA DE `check-ignore` (medida, no supuesta). Sin `--no-index`, git
    mira el indice y un fichero YA versionado nunca se reporta como ignorado:
    la sonda pasaria aunque la excepcion este borrada, o sea sin distinguir
    nada. Y con `--no-index -v` el codigo de salida es 0 tambien para un
    patron NEGATIVO (imprime `!docs/...`): afirmar `rc == 0` seria afirmar lo
    contrario de lo que se cree. Por eso va `-q --no-index`, donde rc=1
    significa de verdad "esta ruta NO esta ignorada", y lleva un CONTROL
    NEGATIVO: `saved_processes.json` si esta ignorado y tiene que dar rc=0. Sin
    ese control, un `check-ignore` que no discrimina daria verde igual.

    ITERACION 3. La norma tenia un agujero de RUTA, no de contenido: se
    vigilaba la raiz del repo, pero la ruta que la app LEE es `_app_dir()`, que
    en desarrollo es `src/woptimizer/`. Copiar ahi el v2 archivado dejaba la
    suite en verde (medido por el `mutation-auditor`) y, peor, no es un
    fichero inerte: `load()` tiene rama legacy, o sea que la app lo abriria de
    verdad. El bloque de abajo cierra eso por CONTENIDO, no por inexistencia
    (por la ruta viva vive el `profiles.json` del estado local, escrito por la
    propia app; exigir que no exista seria una sonda que falla siempre).
    """
    repo_root, env = _entorno_git_del_repo()
    rel_dir = "docs/archive/legacy-root-data"
    dir_arch = os.path.join(repo_root, "docs", "archive", "legacy-root-data")
    archivados = ("README.md", "profiles.json", "inconsistencies_plan.md")

    # CONTROL NEGATIVO: demuestra que `check-ignore` sabe decir "ignorado" aqui.
    # Si esto falla, todas las aserciones de "no ignorado" de abajo no valen nada.
    rc_ctrl, sal_ctrl = _git(["check-ignore", "-q", "--no-index", "saved_processes.json"], env, repo_root)
    assert rc_ctrl == 0, (
        "CONTROL ROTO: `git check-ignore` deberia responder rc=0 (SI ignorado) sobre "
        f"saved_processes.json y respondio rc={rc_ctrl} ({sal_ctrl!r}). Sin este control, "
        "las aserciones siguientes no probarian nada: una herramienta que no distingue "
        "tambien daria verde."
    )

    for nombre in archivados:
        ruta_rel = f"{rel_dir}/{nombre}"
        ruta_abs = os.path.join(dir_arch, nombre)
        assert os.path.isfile(ruta_abs), (
            f"el archivo de docs/archive esta incompleto: falta {ruta_rel}. La norma del "
            "propietario es no borrar nada; lo que se perdio no se puede archivar."
        )
        assert os.path.getsize(ruta_abs) > 0, (
            f"{ruta_rel} esta VACIO (0 bytes): el README dice que es lo que se archivo y con "
            "contenido byte a byte. Un archivo vacio es peor que no archivar, porque parece "
            "cumplido (M14)."
        )
        rc, sal = _git(["check-ignore", "-q", "--no-index", ruta_rel], env, repo_root)
        assert rc == 1, (
            f"{ruta_rel} esta IGNORADO (rc={rc}, salida={sal!r}; rc=0 = ignorado, rc=1 = no "
            "ignorado, rc=128 = error). El `.gitignore` lo declara con la regla `profiles.json` "
            "y la UNICA excepcion que lo saca de ahi es la linea con `!`: sin ella el fichero "
            "archivado es invisible para git y `git add -A` lo borra del historico en silencio (M12)."
        )

    # Y no basta con "no ignorado": tiene que estar EN EL INDICE. Son dos
    # estados distintos (ignorado y sin versionar) y el segundo es el que
    # borra el archivo del historico.
    rc, sal = _git(["ls-files", "--error-unmatch", f"{rel_dir}/profiles.json"], env, repo_root)
    assert rc == 0, (
        f"{rel_dir}/profiles.json NO esta versionado (rc={rc}, {sal!r}). Que no este ignorado "
        "no basta: si no esta en el indice, el proximo `git add -A` no lo resurrected, se lo "
        "queda. El archivo existiria solo en esta maquina (M12)."
    )

    # El README no es decorativo: tiene que NOMBRAR lo que archiva.
    with open(os.path.join(dir_arch, "README.md"), encoding="utf-8") as fh:
        readme = fh.read()
    for nombre in ("profiles.json", "inconsistencies_plan.md"):
        assert nombre in readme, (
            f"el README del archivo no menciona {nombre}: un README que no dice que es lo "
            "archivado es el primero que se pierde (M15)"
        )

    # Y la norma es de una direccion: lo archivado no vuelve a la raiz.
    for nombre, por_que in (
        ("profiles.json", "`.gitignore` lo ignora por la regla `profiles.json`, asi que una "
                          "copia en la raiz es INVISIBLE para git y desapareceria sin dejar rastro"),
        ("inconsistencies_plan.md", "es el plan '100% Completado' que describe incidencias ya "
                                    "resueltas y cita un `fallback.csv` que no existe: en la raiz, "
                                    "junto a la documentacion viva, se leia como pendientes"),
    ):
        ruta_raiz = os.path.join(repo_root, nombre)
        assert not os.path.exists(ruta_raiz), (
            f"{nombre} ha vuelto a la raiz del repo: se ha desarchivado. {por_que} (M13)"
        )

    # --- Y LA RUTA VIVA, que no es la raiz (TASK-028 iteracion 3) -----------
    # `PROFILES_FILE` sale de `_app_dir()`, que en modo desarrollo devuelve
    # `dirname(config.py)`, o sea `src/woptimizer/profiles.json`; congelado, el
    # directorio del `.exe`. La app NO lee el `profiles.json` de la raiz: lee
    # ese, que en desarrollo esta DENTRO del arbol de `src/`.
    # Vigilando solo la raiz, el archivo archivado se podia copiar a la ruta que
    # la app SI lee y todo seguia en verde: medido por el `mutation-auditor`
    # (copia del v2 archivado -> `src/woptimizer/profiles.json` -> suite VERDE).
    # Y ahi el esquema retirado no es un fichero inerte: `load()` tiene rama
    # legacy, asi que lo cargaria de verdad, con sus claves que `models.py` no
    # define (`__system_gaming__`, `factory`, `kill_low_chat`).
    #
    # Por eso la asercion NO es "no existe en la ruta viva" (ahi vive el
    # profiles.json del estado local, escrito por la propia app, y exigir que
    # no exista seria una sonda que falla siempre), sino sobre el CONTENIDO: si
    # hay documento, tiene que ser del esquema VIVO, no el v2 retirado.
    import json
    from woptimizer.config import PROFILES_FILE, _app_dir as _app_dir_viva

    assert os.path.normcase(PROFILES_FILE) == os.path.normcase(
            os.path.join(_app_dir_viva(), "profiles.json")), (
        f"PROFILES_FILE vale {PROFILES_FILE!r} y deberia ser "
        f"{os.path.join(_app_dir_viva(), 'profiles.json')!r}. La sonda siguiente mira AHORA "
        "bien la ruta viva, con lo que si la constante se repunta dejaria de mirarla."
    )

    # Claves que el esquema v2 usaba y `models.py` NO define (`extra="allow"`
    # las conservaria, y por eso un fichero v2 no se rompe: se arrastra).
    #
    # ITERACION 4, PARTE (a): la ruta viva es ESTADO LOCAL DEL USUARIO y hay
    # estados que la app SOPORTA y esta sonda se negaba a soportar. Medido por
    # el auditor: con un `profiles.json` invalido, o con uno vacio (0 bytes, lo
    # que deja un corte de luz o un antivirus que lo trunca), la suite salia
    # en ROJA. El propio mensaje reconocia el caso ("la app tampoco lo abriria:
    # lo marcaria como danado y arrancaria con cero packs") y aun asi tumbaba
    # la suite: un estado soportado no puede ser un fallo de test. Y lo grave
    # no era el rojo, era la segunda frase del mensaje, que le decia al usuario
    # que BORRARA su fichero de packs.
    #
    # Por eso a partir de aqui la sonda NO exige JSON valido: si el documento no
    # se puede leer, no hay nada que afirmar (no es evidencia de nada) y se avisa
    # por `print()`. Un fichero corrupto o truncado no puede ser el v2 retirado
    # con forma de v2, y sobre todo no es asunto de la suite.
    viva = PROFILES_FILE
    with open(os.path.join(dir_arch, "profiles.json"), encoding="utf-8") as fh:
        crudo_archivado = fh.read()

    # El detector se prueba CONTRA SI MISMO antes de mirar nada (parte b): una
    # tabla de SI y otra de NO, porque un detector que no ve nada y uno que ve
    # de mas dan el MISMO verde. La fila de SI son los bytes archivados REALES.
    v2_doc = json.loads(crudo_archivado)
    detectado, rasgos = _rasgos_del_esquema_v2_retirado(v2_doc)
    assert detectado, (
        "CONTROL ROTO (falso NEGATIVO): el detector no reconoce el esquema v2 RETIRADO ni "
        "siquiera en el `profiles.json` archivado, que es la copia literal. Entonces "
        "`assert not ...` de mas abajo pasaria SIEMPRE y la asercion no estaria midiendo "
        f"nada. Rasgos que el detector ve en el archivado: {rasgos}"
    )
    for etiqueta, doc in (
        ("campo de usuario 'factory' en su propio pack (extra=allow, documento legitimo)",
         {"profiles": {"streaming": {"name": "Streaming", "factory": True}}}),
        ("campo de usuario 'kill_low_chat' en su propio pack",
         {"profiles": {"streaming": {"name": "Streaming", "kill_low_chat": False}}}),
        ("un pack que se LLAMA '__system_gaming__' pero sin ningun campo del v2",
         {"profiles": {"__system_gaming__": {"name": "Gaming", "apps": ["steam.exe"]}}}),
        ("el esquema VIVO (raiz 'packs', la firma de models.py)",
         {"packs": {"gaming": {"id": "gaming", "name": "Gaming", "is_gaming": True}}}),
        ("el mismo campo de usuario en DOS packs distintos, cada uno por su lado",
         {"profiles": {"a": {"factory": True}, "b": {"kill_low_chat": True}}}),
    ):
        falso, _ = _rasgos_del_esquema_v2_retirado(doc)
        assert not falso, (
            f"CONTROL ROTO (falso POSITIVO): el detector declara que el esquema v2 ha vuelto "
            f"ante «{etiqueta}» ({doc!r}). Eso NO es un v2: es un fichero de usuario "
            "legitimo que `Pack` acepta porque es `extra=\"allow\"`, y con el detector asi la "
            "suite le diria a alguien que su configuracion esta rota y que la borre. Un "
            "discriminante unico (un campo suelto) no puede ser el criterio."
        )

    # ITERACION 5, F1. El `open()` y el `read()` estaban FUERA del `try`, o sea
    # que el `except (OSError, UnicodeDecodeError)` era CODIGO MUERTO: no podia
    # ejecutarse nunca. Medido en tres estados que la app SOPORTA, cada uno con
    # la suite en ROJO por traceback (o sea, sin asercion, que no prueba nada):
    #   * bytes que no son UTF-8       -> `UnicodeDecodeError` en el `read()`
    #   * truncado a mitad de un emoji -> `UnicodeDecodeError` ("bytes in
    #                                     position 34-35: unexpected end of data")
    #   * sin permiso de lectura       -> `PermissionError` en el `open()`
    # El escenario es realista: el `profiles.json` vivo del usuario tiene un
    # U+1F680 (cuatro bytes UTF-8) y un corte de luz o un antivirus que trunca
    # ahi produce exactamente ese fichero.
    #
    # Y la asimetria es grave: `pack_service.py` incluye `UnicodeDecodeError` en
    # `CORRUPTION_ERRORS`, o sea que la app lo detecta, avisa y RECUPERA los
    # packs del `.bak`; la sonda reventaba. Un estado soportado no puede ser un
    # fallo de test, que es lo que promete el `proposal.md` §3.1.
    if os.path.exists(viva):
        doc_vivo, motivo, crudo_vivo = _leer_documento_de_packs(viva)
        if doc_vivo is None:
            # OBSERVACION, no asercion. Se escribe como hecho, nunca como orden.
            print(f"  [aviso] Hay un profiles.json local en {viva} y {motivo}. La app lo "
                  "tolera: lo marca como danado, arranca con cero packs y lo regenera en el "
                  "primer guardado. La suite no afirma nada sobre el (estado local, "
                  "gitignored, y esta sonda no lo lee como evidencia de nada).")
        else:
            es_v2, rasgos = _rasgos_del_esquema_v2_retirado(doc_vivo)
            assert not es_v2, (
                f"el profiles.json de la RUTA VIVA ({viva}) es el esquema v2 RETIRADO: el "
                f"mismo registro acumula {rasgos}, y eso no lo puede inventar un documento "
                "vivo. La app lee esta ruta, no la raiz, y `load()` tiene rama legacy: lo "
                "abiria de verdad y resucitaria el preset de fabrica `__system_gaming__` con "
                "claves que `models.py` no define. Es el archivo de "
                "docs/archive/legacy-root-data copiado al sitio de lectura (medido por el "
                f"mutation-auditor: copia ahi -> suite en rojo). Coincide byte a byte con el "
                f"archivado: {crudo_vivo == crudo_archivado}. "
                "COMO LLEGAR AQUI: `src/woptimizer/profiles.json` es estado local de esta "
                "maquina (lo ignora .gitignore), lo escribe la propia app y la app lo tolera. "
                "Esta sonda no lo borra, no lo renombra y no recomienda borrarlo; lo que dice "
                "es que su contenido coincide con el esquema retirado, y la decision de que "
                "hacer con el es del usuario."
            )

    # CONTROL DE ALCANZABILIDAD (F1). El arreglo de arriba se puede aplicar y la
    # suite seguir en verde con la rama de lectura MUERTA otra vez, si alguien la
    # vuelve a mover. Este control lo delata: escribe de verdad los tres ficheros
    # ilegibles que tumbaban la sonda y exige que `_leer_documento_de_packs`
    # responda con un motivo, sin propagar nada.
    #
    # POR QUE hace falta y no basta con "no revienta": las muertes del auditor
    # fueron TRACEBACKS, o sea que median que el codigo se rompia, no que
    # affirmara lo correcto. Un `try/except` que devuelve `("", "")` en todo
    # pasaria igual: por eso se exige que el motivo NO SEA VACIO y que distinga
    # los tres casos por su TEXTO, no que "se llamo".
    import shutil as _shutil
    import tempfile as _tempfile

    _casos_ilegibles = (
        # (etiqueta, escritor, prefijo que el motivo tiene que llevar)
        ("bytes que no son UTF-8",
         lambda d: open(d, "wb").write(b'{"packs": {"gaming": {"name": "\xff\xfe"}}}'),
         "no se puede leer ("),
        # El U+1F680 son 4 bytes; a 2 el fichero esta truncado a mitad. Es el
        # escenario del docstring, con el byte literal, no con un `errors=`.
        ("truncado a mitad de un emoji de 4 bytes",
         lambda d: open(d, "wb").write(b'{"name": "pre' + b"\xf0\x9f"),
         "no se puede leer ("),
        # Un DIRECTORIO con el nombre del fichero: `PermissionError` REAL del
        # sistema de ficheros. No se usa `os.chmod`, que en Windows no impide
        # la lectura y habria dado un control que no controlaba nada.
        ("sin permiso de lectura (PermissionError real)",
         lambda d: os.mkdir(d),
         "no se puede leer ("),
    )
    for etiqueta, escribir, prefijo_esperado in _casos_ilegibles:
        _d = _tempfile.mkdtemp()
        _ruta = os.path.join(_d, "profiles.json")
        try:
            escribir(_ruta)
            # La llamada va dentro de un `try` PORQUE el fallo que se mide es
            # justo que la lectura propague. Sin capturarlo aqui, la muerte del
            # mutante seria un traceback, y un traceback prueba que el codigo se
            # rompio, no que la rama se alcanzó. Con el `assert` de abajo, la
            # muerte dice QUE paso y POR QUE importa.
            try:
                doc, motivo, _crudo = _leer_documento_de_packs(_ruta)
            except (OSError, UnicodeDecodeError) as e:
                raise AssertionError(
                    f"CONTROL ROTO: la rama ilegible NO existe con «{etiqueta}»: "
                    f"_leer_documento_de_packs PROPAGO {type(e).__name__} ({e}). El "
                    "`open()`/`read()` estan FUERA del `try`, o la rama de lectura no "
                    "cubre esta excepcion. Un `profiles.json` ilegible del usuario no "
                    "puede tumbar la suite: es estado local y la app lo tolera."
                ) from e
            assert doc is None and motivo, (
                f"CONTROL ROTO: la rama ilegible NO se alcanza con «{etiqueta}»: "
                f"_leer_documento_de_packs devolvio documento={doc!r} y motivo={motivo!r}. "
                "El `except (OSError, UnicodeDecodeError)` volvio a ser codigo muerto y esta "
                "sonda lo daria por bueno: el fichero ilegible del usuario solo pasaria por "
                "que nadie mira."
            )
            assert motivo.startswith(prefijo_esperado), (
                f"CONTROL ROTO: con «{etiqueta}» el motivo es {motivo!r} y deberia empezar "
                f"por {prefijo_esperado!r}. Un motivo que blames al JSON de un fallo de BYTES "
                "es el sintoma de tener `except ValueError` antes que "
                "`except (OSError, UnicodeDecodeError)`: `UnicodeDecodeError` es subclase de "
                "`ValueError` y se la come el primero. Con el orden al reves la rama se "
                "declara inalcanzable sin que nada falle."
            )
        finally:
            _shutil.rmtree(_d, ignore_errors=True)

    # CONTROL POSITIVO: el mismo helper tiene que SEGUIR leyendo de verdad. Sin
    # esto, un `_leer_documento_de_packs` que devolviera siempre `(None, "x")`
    # pasaria los tres controles de arriba y dejaria la sonda ciega. Va ANTES
    # del del `null` a proposito: cada control tiene que morir por su propia
    # causa, y si el del `null` fuera primero, un helper muerto por completo
    # moriria ahi y el positivo no se comprobaria nunca.
    _d = _tempfile.mkdtemp()
    _ruta = os.path.join(_d, "profiles.json")
    try:
        with open(_ruta, "w", encoding="utf-8") as _fh:
            _fh.write('{"packs": {"gaming": {"id": "gaming", "name": "Gaming", '
                      '"is_gaming": true}}}')
        doc, motivo, _crudo = _leer_documento_de_packs(_ruta)
        assert isinstance(doc, dict) and not motivo, (
            f"CONTROL ROTO: sobre un documento VIVO valido el helper devolvio {doc!r} / "
            f"{motivo!r}. Un helper que declara ilegible lo legible hace pasar los tres "
            "controles de ilegibilidad sin mirar nada, que es un detector muerto por la "
            "puerta de atras."
        )
        # Y que ademas reconozca el v2 retirado, que es para lo que existe: un
        # helper que leyera bien pero no distinguiera no serviria de nada.
        es_v2, _rasgos = _rasgos_del_esquema_v2_retirado(doc)
        assert not es_v2, (
            "CONTROL ROTO: el helper lee un documento vivo y el detector lo declara v2 "
            "retirado. O la lectura no es la misma que usa la sonda, o el detector se ha "
            "abierto y mataria el fichero de un usuario legitimo."
        )
    finally:
        _shutil.rmtree(_d, ignore_errors=True)

    # D1: el `null` es JSON valido que NO lanza, y sin la rama explicita el aviso
    # sale con el motivo vacio. Se afirma sobre el TEXTO, que es lo que se lee.
    _d = _tempfile.mkdtemp()
    _ruta = os.path.join(_d, "profiles.json")
    try:
        with open(_ruta, "w", encoding="utf-8") as _fh:
            _fh.write("null")
        doc, motivo, _crudo = _leer_documento_de_packs(_ruta)
        assert doc is None, (
            f"CONTROL ROTO: `json.loads('null')` devuelve None sin lanzar, asi que un "
            f"documento nulo tiene que salir como ilegible, no como un perfil. Devolvio "
            f"{doc!r}."
        )
        assert "`null`" in motivo, (
            f"CONTROL ROTO: un `profiles.json` con el literal `null` deja el aviso con el "
            f"motivo {motivo!r}. Se leeria «Hay un profiles.json local en X **y .** La app "
            "lo tolera», que es un texto roto que ademas contradice el criterio de mas "
            "arriba (un documento que no es un mapa no se puede leer como packs)."
        )
    finally:
        _shutil.rmtree(_d, ignore_errors=True)

    print("El archivo de docs/archive esta versionado, completo, sin volver a la raiz "
          "ni a la ruta viva que lee la app. Y la ruta viva ILEGIBLE da aviso, no muerte: "
          "no-UTF8, truncado a mitad de un emoji y sin permiso de lectura los tres se "
          "responden, y el `null` tambien (F1, D1).")


def test_el_punto_de_entrada_declara_el_log_antes_de_los_servicios():
    """M4/M4b: `architecture.md` §15 declara que `setup_logging()` la invoca
    `__main__.main()` ANTES de instanciar los servicios. Borrada esa llamada, la
    app arranca SIN log a fichero: los `logger.warning` caen al `lastResort` de
    la stdlib y salen por stderr. Verde.

    POR QUE NO LO VEIA NADA, y es lo importante: `run_tests.py` se llama a si
    mismo `setup_logging()` en su `__main__`, o sea que la suite se
    autoconfigurea y el punto de entrada del producto le es invisible. Es un
    validador que se deduce a si mismo, que es exactamente el fallo del ciclo
    #15. Por eso esta sonda lee el AST del punto de entrada y no su propio
    entorno de logging.

    NO se ejecuta `main()` (arrancaria la UI y el bucle de eventos): se leen
    los lineno de las llamadas. Dos mutaciones, dos muertes distintas: borrar la
    llamada mata por AUSENCIA; moverla debajo de los servicios mata por ORDEN.
    """
    raiz = os.path.dirname(os.path.abspath(__file__))
    ruta_main = os.path.join(raiz, "src", "woptimizer", "__main__.py")
    with open(ruta_main, encoding="utf-8") as fh:
        arbol = ast.parse(fh.read(), filename=ruta_main)

    main = next((n for n in ast.walk(arbol)
                 if isinstance(n, ast.FunctionDef) and n.name == "main"), None)
    assert main is not None, f"{ruta_main} no define main(): no hay punto de entrada que vigilar"

    def _llamadas(nombre):
        return sorted(n.lineno for n in ast.walk(main)
                      if isinstance(n, ast.Call) and getattr(n.func, "id", None) == nombre)

    servicios = ("ProcessService", "PackService", "GamingService", "WOptimizerApp")
    lineas_log = _llamadas("setup_logging")
    lineas_servicio = sorted(l for s in servicios for l in _llamadas(s))

    assert lineas_servicio, (
        f"main() no instancia ningun servicio de {servicios}: la sonda no tendria contra que "
        "afirmar el orden. Si esto salta, el punto de entrada cambio de forma y esta sonda "
        "hay que reescribirla, no saltarsela."
    )
    assert lineas_log, (
        f"__main__.main() NO llama a setup_logging(): la app arranca sin log a fichero y sus "
        f"avisos salen por stderr (lastResort). El servicio se instancia en la linea "
        f"{lineas_servicio[0]}: el canal se declara DESPUES de que el primer servicio pueda "
        "avisar (M4b)"
    )
    assert min(lineas_log) < lineas_servicio[0], (
        f"setup_logging() se invoca en la linea {min(lineas_log)} y el primer servicio se "
        f"instancia en la {lineas_servicio[0]}: el canal de log se declara TARDE. Todo lo que "
        "avise el servicio antes de esa llamada se pierde hacia stderr (M4b)"
    )

    print("__main__.main() declara el log antes de instanciar ningun servicio.")


def test_process_list_file_sigue_siendo_un_contrato():
    """M18: `PROCESS_LIST_FILE` se conservo con el veto de FIX-011 ("NO esta sin
    usar: la consumen cinco sitios") y **no tenia ni un guard**: borrarla dejaba
    la suite en verde.

    Lo que se afirma, y por que en este orden:
      (a) que la CONSTANTE existe, sobre el AST de `config.py`. Se afirma antes
          de importarla a proposito: borrarla debe dar una ASERCION que lo diga,
          no un `ImportError` que parece un fallo de otra cosa.
      (b) que su VALOR es el que se pretendia, leido del modulo (no del texto:
          el texto podria ser cualquier cosa).
      (c) que los TRES consumidores nombrados la siguen usando, sobre SU propio
          AST. Sin (a), (c) no se puede ni preguntar; sin (c), la constante
          sobrevive por un motivo que nadie puede comprobar.

    NOTA HONESTA (D1): el cuarto "consumidor" que citaba el comentario de
    `config.py` era `smoke_check.py:23`, y ese script esta MUERTO: lee
    `process_manager.py`, que no existe, y revienta en su linea 8 con
    `FileNotFoundError` sin llegar nunca a la 23. Por eso no se cuenta aqui: un
    guardia que no corre no vigila, y fingir que vigila es peor que no tenerlo.
    """
    raiz = os.path.dirname(os.path.abspath(__file__))
    ruta_cfg = os.path.join(raiz, "src", "woptimizer", "config.py")
    with open(ruta_cfg, encoding="utf-8") as fh:
        codigo_cfg = fh.read()
    arbol = ast.parse(codigo_cfg, filename=ruta_cfg)

    nodo = None
    for cand in arbol.body:
        if isinstance(cand, ast.Assign) and any(
            getattr(t, "id", None) == "PROCESS_LIST_FILE" for t in cand.targets
        ):
            nodo = cand
    assert nodo is not None, (
        "PROCESS_LIST_FILE ha desaparecido de config.py. FIX-011 la veto por EN USO: la "
        "consumen test_gaming_session.py, test_harness.py y test_harness_v2.py, los tres "
        "protegidos por FIX-014. Borrarla rompe esos tres y no lo dice nadie."
    )
    segmento = ast.get_source_segment(codigo_cfg, nodo) or ""
    assert "_app_dir(" in segmento and "saved_processes.json" in segmento, (
        f"PROCESS_LIST_FILE ya no se construye con _app_dir()/saved_processes.json: "
        f"{segmento!r}. Apuntar a otro sitio cambia donde esta el historial del usuario."
    )

    from woptimizer.config import PROCESS_LIST_FILE, _app_dir
    esperado = os.path.join(_app_dir(), "saved_processes.json")
    assert os.path.normcase(PROCESS_LIST_FILE) == os.path.normcase(esperado), (
        f"PROCESS_LIST_FILE vale {PROCESS_LIST_FILE!r} y deberia valer {esperado!r}"
    )

    consumidores = ("test_gaming_session.py", "test_harness.py", "test_harness_v2.py")
    archive_dir = os.path.join(raiz, "docs", "archive", "legacy-root-tests")
    for nombre in consumidores:
        ruta = os.path.join(archive_dir, nombre)
        assert os.path.isfile(ruta), f"ha desaparecido el consumidor protegido por FIX-014: {nombre}"
        with open(ruta, encoding="utf-8") as fh:
            arbol_t = ast.parse(fh.read(), filename=ruta)
        nombres = {getattr(n, "id", None) for n in ast.walk(arbol_t)}
        atributos = {getattr(n, "attr", None) for n in ast.walk(arbol_t)}
        assert "PROCESS_LIST_FILE" in nombres or "PROCESS_LIST_FILE" in atributos, (
            f"{nombre} ya no nombra PROCESS_LIST_FILE: el veto de FIX-011 se sostiene en que "
            "estos tres tests la usan, no en que exista una constante (M18)"
        )

    print("PROCESS_LIST_FILE existe, vale lo que debe y la usan sus tres consumidores.")


def test_la_documentacion_del_blindaje_no_puede_desfasarse():
    """M10a/M10b/M10c/M11: FIX-020 dijo "documentacion sincronizada" y no lo
    comprueba nadie. Cuatro mutaciones, cuatro verdes:

      * la doc vuelve a decir `process_service.py:23-38`;
      * una linea de comentario en el codigo desplaza el `frozenset` una linea
        y las dos docs siguen afirmando `33-48` "medido con ast";
      * el codigo pierde un nombre real (`securityhealthservice`, 34 -> 33) y
        la transcripcion queda desfasada sin que se entere nadie.

    La medicion sale del CODIGO con `ast` (rango y conjunto reales) y la
    expectativa se deriva de ahi, NUNCA de la doc: un test que compara la doc
    consigo mismo no distinguiria nada, que es el fallo que se esta corrigiendo.
    """
    import re

    raiz = os.path.dirname(os.path.abspath(__file__))
    ruta_serv = os.path.join(raiz, "src", "woptimizer", "services", "process_service.py")
    with open(ruta_serv, encoding="utf-8") as fh:
        codigo_serv = fh.read()
    arbol = ast.parse(codigo_serv, filename=ruta_serv)

    nodo = None
    for cand in arbol.body:
        if isinstance(cand, ast.Assign) and any(
            getattr(t, "id", None) == "SYSTEM_PROTECTED_PROCESSES" for t in cand.targets
        ):
            nodo = cand
    assert nodo is not None, (
        "SYSTEM_PROTECTED_PROCESSES no aparece a nivel de modulo en process_service.py: "
        "las docs dicen donde vive y la sonda lo mide, asi que si se mueve hay que moverlas"
    )
    assert getattr(nodo.value, "id", None) == "frozenset" or getattr(
        getattr(nodo.value, "func", None), "id", None
    ) == "frozenset", (
        f"SYSTEM_PROTECTED_PROCESSES ya no es un frozenset: el tipo importa porque es la "
        f"frontera que la doc promete ({ast.dump(nodo.value)[:120]})"
    )
    elementos = nodo.value.args[0] if isinstance(nodo.value, ast.Call) else nodo.value
    reales = {ast.literal_eval(e) for e in elementos.elts}

    rango = f"process_service.py:{nodo.lineno}-{nodo.end_lineno}"
    for doc in ("architecture.md", "data-models.md"):
        with open(os.path.join(raiz, "docs", "ai", doc), encoding="utf-8") as fh:
            texto = fh.read()
        assert rango in texto, (
            f"docs/ai/{doc} no dice el rango REAL del frozenset ({rango}, medido con ast). Una "
            "medicion que nadie vuelve a medir no es una medicion: se desincroniza en silencio "
            f"(M10a/M10b/M11). Contexto: el nodo ocupa las lineas {nodo.lineno}-{nodo.end_lineno}."
        )

    with open(os.path.join(raiz, "docs", "ai", "data-models.md"), encoding="utf-8") as fh:
        texto_dm = fh.read()
    ini = texto_dm.index("#### Los 34 nombres")
    fin = texto_dm.index("Los que NO estan")
    transcritos = set()
    for linea in texto_dm[ini:fin].splitlines():
        if linea.strip().startswith("- "):
            transcritos |= set(re.findall(r"`([^`]+)`", linea))

    assert transcritos == reales, (
        "la transcripcion de data-models.md no es el frozenset real: sobran "
        f"{sorted(transcritos - reales)} y faltan {sorted(reales - transcritos)}. La doc "
        "transcribe la lista DE SEGURIDAD del producto: una nombre que sobra o falta es un "
        "proceso de sistema que se puede cerrar (M10c)"
    )

    # El recuento declarado en las dos docs, contrastado con el codigo.
    m_dm = re.search(r"frozenset` de \*\*(\d+)\*\* entradas", texto_dm)
    assert m_dm and int(m_dm.group(1)) == len(reales), (
        f"data-models.md declara {m_dm.group(1) if m_dm else '?'} entradas y el codigo tiene "
        f"{len(reales)}"
    )
    with open(os.path.join(raiz, "docs", "ai", "architecture.md"), encoding="utf-8") as fh:
        texto_ar = fh.read()
    m_ar = re.search(r"`frozenset` de (\d+) nombres", texto_ar)
    assert m_ar and int(m_ar.group(1)) == len(reales), (
        f"architecture.md declara {m_ar.group(1) if m_ar else '?'} nombres y el codigo tiene "
        f"{len(reales)}"
    )

    print(f"Las dos docs dicen el rango {rango} y los {len(reales)} nombres reales.")


def test_el_validador_avisa_en_vez_de_tirar_la_excepcion():
    """TASK-037, ciclo 27 (T-27.1, T-27.2, T-27.3, T-27.4): la rama
    `if n_tests is None:` de `validate_docs.py` era CODIGO MUERTO.

    `_recuento_de_tests` no tenia ni un `return None` en sus 34 lineas:
    propagaba `FileNotFoundError` con el fichero ausente e
    `IndentationError` con la fuente rota, y las dos rutas de la rama salian
    con traceback en vez de con informe. O sea, la proteccion existia escrita y
    el productor no sabia emitir el estado que ella declara: exactamente la
    clase de guarda que este repo ya sufrio dos veces.

    El arreglo es el PRODUCTOR (`try/except OSError` sobre el `open()`,
    `try/except SyntaxError` sobre el `ast.parse()`), NO la rama, que ya
    estaba escrita para el contrato correcto. Y el `except` es `SyntaxError`
    y no `IndentationError` porque este ultimo es subclase: estrecharlo deja
    fuera `TabError` y reabre el mismo agujero por el otro lado.

    T-27.2 (`_comprobar_recuento_de_tests(root, errors, ok)`) es lo que hace
    esto testeable: sin raiz, la rama solo se despertaba lanzando el validador
    entero contra el repo entero.

    Cada llamada va envuelta en un `try/except Exception` que convierte un
    crash en `AssertionError`: los mutantes M1 (se cae `SyntaxError`) y M2 (se
    cae `OSError`) tienen que morir por la AFIRMACION de este test, no por un
    traceback que el runner cuente como muerte sin distinguir el motivo.
    """
    import shutil
    import tempfile
    import validate_docs as vd

    def _sin_excepcion(que, *args):
        try:
            return que(*args)
        except Exception as exc:                       # pragma: no cover
            raise AssertionError(
                f"{que.__name__} debia devolver None con un INFORME y tiro "
                f"{type(exc).__name__}: {exc}. Sin este envoltorio el mutante "
                "muere por traceback y el verificador no puede distinguir un "
                "test que detecta el fallo de un mutante que revienta el codigo"
            )

    def _informe(root):
        errors, ok = [], []
        _sin_excepcion(vd._comprobar_recuento_de_tests, root, errors, ok)
        return errors, ok

    def _clase_de_error_de_sintaxis(fuente):
        """La clase EXACTA que lanza `ast.parse`, o `None` si compila.

        Es el guard de las fixtures de esta sonda. Sin el, un fixture que un
        dia deje de lanzar la clase querowing se esperaba seguiria exercising
        `_recuento_de_tests` yReturning `None` por el motivo equivocado: el
        mutante `except IndentationError` volveria a sobrevivir en silencio.
        Una fixture que no se autocomprueba es una promesa, y este ciclo
        existe para dejar de escribir promesas.
        """
        try:
            ast.parse(fuente, filename="<fixture>")
        except SyntaxError as exc:
            return type(exc).__name__
        return None

    tmp = tempfile.mkdtemp(prefix="wopt_validador_")
    try:
        # (a) LAS TRES CLASES de error de sintaxis que el productor tiene que
        # absorber, con la clase MEDIDA, no la supuesta. La tabla sale de
        # medir `_clase_de_error_de_sintaxis` sobre estas tres fuentes, no de
        # suponerla:
        #
        #   sangria inesperada   -> IndentationError   (subclase de SyntaxError)
        #   tabulador + espacios-> TabError            (subclase de SyntaxError)
        #   dos puntos borrado   -> SyntaxError        (NO es subclase de nada)
        #
        # La tercera fila es la que manda. Estrechar a `IndentationError`
        # (mutante S1/M10) deja fuera el tabulador Y el SyntaxError plano;
        # estrechar a `(IndentationError, TabError)` (mutante S2/M12) deja solo
        # el SyntaxError plano, y ese mutante es PEOR que el codigo de hoy:
        # con el, un dos puntos borrado en run_tests.py vuelve a salir con
        # traceback. Un `SyntaxError` plano es ademas el caso de la vida real
        # (un parentesis descuadrado), no un caso limite como el tabulador.
        FUENTES_ROTAS = (
            ("sangria", "def test_alfa():\n    return 1\n        return 2\n",
             "IndentationError"),
            ("tabulador", "def test_alfa():\n\treturn 1\n        return 2\n",
             "TabError"),
            ("dos_puntos", "def test_alfa()\n    return 1\n",
             "SyntaxError"),
        )
        for etiqueta, fuente, clase in FUENTES_ROTAS:
            assert _clase_de_error_de_sintaxis(fuente) == clase, (
                f"la fixture `{etiqueta}` tiene que lanzar {clase} y lanza "
                f"{_clase_de_error_de_sintaxis(fuente)}. Si la clase cambia, la "
                f"fixture ha perdido la capacidad de matar el mutante que "
                f"estrecha el `except` y el test se cae AQUI, diciendo cual, en "
                f"vez de dejar un mutante vivo con la suite en verde"
            )

        # Se escriben con `newline=""` para que los bytes en disco sean
        # exactamente la fuente: en modo texto de Windows un `\n` se traduce a
        # `\r\n`, y una fixture cuyo resultado dependiera de la traduccion
        # seria una fixture dependiente de como se escribe. Medido en Windows:
        # las tres dan la misma clase con y sin traduccion, y el `newline=""`
        # lo fija en vez de dejarlo al criterio de cada quien.
        rutas_rota = {}
        for etiqueta, fuente, _clase in FUENTES_ROTAS:
            d = os.path.join(tmp, etiqueta)
            os.makedirs(d)
            ruta = os.path.join(d, "run_tests.py")
            with open(ruta, "w", encoding="utf-8", newline="") as fh:
                fh.write(fuente)
            rutas_rota[etiqueta] = (d, ruta)

        d_sangria, ruta_sangria = rutas_rota["sangria"]
        d_tabulador, ruta_tabulador = rutas_rota["tabulador"]
        d_dos_puntos, ruta_dos_puntos = rutas_rota["dos_puntos"]

        # (b) `run_tests.py` AUSENTE: `FileNotFoundError` en el `open()`.
        d_ausente = os.path.join(tmp, "ausente")
        os.makedirs(d_ausente)

        # (c) Sano: un test definido Y invocado.
        d_sano = os.path.join(tmp, "sano")
        os.makedirs(d_sano)
        with open(os.path.join(d_sano, "run_tests.py"), "w", encoding="utf-8") as fh:
            fh.write(
                'def test_alfa():\n    return 1\n\n\n'
                'if __name__ == "__main__":\n    test_alfa()\n'
            )

        # (d) Definido y NO invocado: el caso NORMAL, que ademas es el que
        # produce el mensaje con el segmento huerfano.
        d_huerfano = os.path.join(tmp, "huerfano")
        os.makedirs(d_huerfano)
        with open(os.path.join(d_huerfano, "run_tests.py"), "w", encoding="utf-8") as fh:
            fh.write('def test_alfa():\n    return 1\n\n\nif __name__ == "__main__":\n    pass\n')

        # --- (a) FUENTE ROTA -> INFORME, no traceback, LAS TRES CLASES ------
        # El bucle es lo que hace JUSTOS a S1 y S2: con una sola fixture
        # (la sangria, que es `IndentationError`) el mutante que estrecha el
        # `except` sobrevivia a la suite entera Y al validador, porque la
        # prohibicion de estrechar estaba ESCRITA en el proposal y en el
        # docstring de esta funcion, y no PROBADA en ninguna parte.
        for etiqueta, _fuente, clase in FUENTES_ROTAS:
            raiz, ruta = rutas_rota[etiqueta]
            assert _sin_excepcion(vd._recuento_de_tests, ruta) is None, (
                f"una fuente que no compila (fixture `{etiqueta}`, {clase}) NO es un "
                "recuento de 0: es un recuento que no se puede derivar, que es el "
                "estado que la rama declara"
            )
            errors, ok = _informe(raiz)
            assert any("NO SE PUEDE DERIVAR" in e for e in errors), (
                f"una fuente que no compila (fixture `{etiqueta}`, {clase}) tiene que "
                f"producir una linea [FAIL] que nombre run_tests.py, no un traceback. "
                f"Errors: {errors}"
            )
            assert not any("NO SE PUEDE DERIVAR" in o for o in ok), (
                "el fallo de derivar el recuento no puede contarse como OK: seria un "
                f"OK con rc=0. Fixture: {etiqueta}. OK: {ok}"
            )

        # --- (b) FICHERO AUSENTE -> lo mismo -----------------------------
        assert _sin_excepcion(vd._recuento_de_tests,
                              os.path.join(d_ausente, "run_tests.py")) is None, (
            "un run_tests.py ausente no es un recuento de 0: es un recuento que "
            "no se puede derivar"
        )
        errors, _ok = _informe(d_ausente)
        assert any("NO SE PUEDE DERIVAR" in e for e in errors), (
            f"un run_tests.py ausente tiene que producir una linea [FAIL] que lo "
            f"nombre, no un traceback. Errors: {errors}"
        )

        # --- (c) SANO -> la 4-tupla, y el `else:` sigue contando ---------
        sano = _sin_excepcion(vd._recuento_de_tests, os.path.join(d_sano, "run_tests.py"))
        assert sano == (1, 1, [], []), (
            f"en el camino sano el productor tiene que devolver la 4-tupla, no None: {sano!r}"
        )
        errors, ok = _informe(d_sano)
        assert not any("NO SE PUEDE DERIVAR" in e for e in errors), (
            f"el camino sano no puede entrar en la rama de fallo. Errors: {errors}"
        )
        assert any("1 tests definidos = 1 invocados" in o for o in ok), (
            f"el camino sano tiene que seguir dando su linea [OK]: si la rama se "
            f"convierte en `pass`, el OK tambien desaparece. OK: {ok}"
        )

        # --- (d) DEFINIDO Y NO INVOCADO: el mensaje, sin segmento vacio ---
        errors, _ok = _informe(d_huerfano)
        lineas = [e for e in errors if e.startswith("run_tests.py:")]
        assert len(lineas) == 1, (
            f"un test definido y no invocado da exactamente una linea [FAIL] de "
            f"run_tests.py, y ninguna mas: {errors}"
        )
        assert "definido y NO invocado: test_alfa" in lineas[0], (
            f"el mensaje tiene que decir QUE test no se invoca: {lineas[0]!r}"
        )
        assert "invocado y NO definido" not in lineas[0], (
            "`solo_invocados` esta VACIO, asi que el segmento 'invocado y NO "
            f"definido: .' es ruido que dice que hay un huerfano donde no lo hay. "
            f"Mensaje: {lineas[0]!r} (mutante M9)"
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("Validador: 4 fixtures (sangria rota, ausente, sano, huerfano) con informe.")


def test_el_alcance_del_guard_de_llamantes_se_deriva_del_arbol():
    """TASK-037, ciclo 27 (T-27.5, T-27.6, T-27.7): el guard del contrato de
    los llamantes tenia su alcance ESCRITO A MANO y nadie lo media.

    Antes: `for relativo in ("views/dashboard_view.py", "views/pack_manager_view.py")`.
    Esa tupla no era una lista de ficheros, era una APUESTA sobre que ficheros
    importan `feedback`, y la apuesta tenia un fichero mal: con `ast` se miden
    TRES importadores, no dos. Hoy eso NO da ningun sintoma (el tercero solo
    usa `mensaje_cierre_pack`, que el guard no vigila), y por eso el arreglo
    seria invisible: un mutante que sustituya la derivacion por la tupla
    CORRECTA de tres ficheros reales pasa la suite entera sin cambiar un solo
    resultado (mutante M5).

    De ahi la exigencia de este test: un ARBOL SINTETICO, con un modulo
    CUARTO que el guard tiene que marcar y que ninguna tupla de ficheros del
    repo real puede contener. Un cuarto modulo, ademas, FUERA de `ui/views/`,
    para que "recorrer el arbol" no se pueda convertir en "recorrer las vistas"
    (mutante M8), y con la llamada en forma `fb.mensaje_sin_apps(...)`
    (`ast.Attribute`), que era el agujero LATENTE del guard (mutante M6).

    Y el control NEGATIVO, sin el cual el guard podria marcarlo todo y
    quedarse en verde: `pack.default_action` y las ACCIONES literales `"start"`
    y `"kill"` son las dos formas VALIDAS del contrato y no se pueden marcar
    (mutante M7).
    """
    import shutil
    import tempfile
    from woptimizer.ui import feedback as fb

    acciones_validas = set(fb.VERBOS)

    # (0) El repo real: la derivacion tiene que encontrar los tres importadores
    # medidos en CYCLE-027, y los tres call-sites reales tienen que pasar
    # limpios (criterio B10). Aqui el guard falla con su propio AssertionError
    # nombrando fichero y linea si un call-site real se sale del contrato.
    reales = _modulos_que_importan_feedback(_raiz_del_paquete())
    assert len(reales) >= 3, (
        f"la derivacion solo encuentra {len(reales)} importadores de `feedback` y en "
        f"CYCLE-027 se mideron tres. Si el alcance derivado deja de recorrer algo, el "
        f"guard se acorta solo y nadie se entera: {reales}"
    )
    _guardar_contrato_de_llamantes(_raiz_del_paquete(), acciones_validas)

    # Los cinco modulos del arbol sintetico. La llamada de `panel.py` y la de
    # `widget.py` estan en la linea 6 de cada uno, y eso es lo que el test
    # comprueba: que el guard nombre FICHERO y LINEA, no solo que proteste.
    UNO = [
        '"""CONFORME: ACCION literal, que es la primera forma valida."""',
        "from woptimizer.ui.feedback import mensaje_banner_sin_apps",
        "",
        "",
        "def _uno(pack):",
        '    return mensaje_banner_sin_apps(pack, "start")',
    ]
    DOS = [
        '"""CONFORME: `pack.default_action`, la segunda forma valida."""',
        "from woptimizer.ui.feedback import mensaje_sin_apps",
        "",
        "",
        "def _dos(pack):",
        "    return mensaje_sin_apps(pack, pack.default_action)",
    ]
    LIMPIO = [
        '"""No importa `feedback`: no puede llamar a un formateador y no se marca."""',
        "",
        "",
        "def _limpio(pack):",
        '    return "apagar " + pack.name',
    ]
    PANEL = [
        '"""FUERA de `ui/views/`: el alcance se deriva de TODO el arbol."""',
        "from woptimizer.ui.feedback import mensaje_sin_apps",
        "",
        "",
        "def _panel(n):",
        '    return mensaje_sin_apps(n, "apagar")',
    ]
    WIDGET = [
        '"""FUERA de `ui/views/` y en forma `fb.mensaje_sin_apps(...)`."""',
        "from woptimizer.ui import feedback as fb",
        "",
        "",
        "def _widget(n):",
        '    return fb.mensaje_sin_apps(n, "iniciar")',
    ]

    tmp = tempfile.mkdtemp(prefix="wopt_guard_")
    try:
        def _sembrar(sub, modulos):
            base = os.path.join(tmp, sub)
            for relativo, lineas in modulos:
                destino = os.path.join(base, relativo)
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                with open(destino, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write("\n".join(lineas) + "\n")
            return base

        arbol = _sembrar("arbol", [
            ("views/uno.py", UNO),
            ("views/dos.py", DOS),
            ("limpio.py", LIMPIO),
            ("panel.py", PANEL),
            ("widget.py", WIDGET),
        ])
        conformes = _sembrar("conformes", [
            ("views/uno.py", UNO),
            ("views/dos.py", DOS),
            ("limpio.py", LIMPIO),
        ])
        cableado = _sembrar("cableado", [("panel.py", PANEL)])
        atributo = _sembrar("atributo", [("widget.py", WIDGET)])

        # (1) EL ALCANCE SE DERIVA. Cuatro de los cinco modulos importan
        # `feedback`; `limpio.py` no aparece porque no lo importa. Esta es la
        # asercion que mata al mutante M5 (alcance vuelto a tupla literal).
        alcance = [os.path.relpath(p, arbol).replace(os.sep, "/")
                   for p in _modulos_que_importan_feedback(arbol)]
        assert alcance == ["panel.py", "views/dos.py", "views/uno.py", "widget.py"], (
            f"el alcance del guard tiene que DERIVARSE del arbol, no estar escrito a "
            f"mano: la derivacion devolvio {alcance}. Si se sustituye por una tupla "
            f"de ficheros, un CUARTO modulo (panel.py, y esta FUERA de `ui/views/`) no "
            f"existe para el y el guard se queda mudo en verde"
        )

        # (2) CONTROL NEGATIVO. `pack.default_action`, `"start"` y `"kill"` son
        # las dos formas validas: un guard que las marca no vigila nada, solo
        # protesta (mutante M7).
        try:
            _guardar_contrato_de_llamantes(conformes, acciones_validas)
        except AssertionError as exc:
            raise AssertionError(
                "el guard marco un llamante CONFORME: `pack.default_action` y las ACCIONES "
                f"literales son las dos formas validas del contrato. Marcado: {exc}"
            )

        # (3) EL VERBO CABLEADO, en un modulo FUERA de `ui/views/`. Mutante M5
        # (alcance escrito a mano) y M8 (recorrido recortado a `ui/views/`).
        marca = None
        try:
            _guardar_contrato_de_llamantes(cableado, acciones_validas)
        except AssertionError as exc:
            marca = str(exc)
        assert marca is not None, (
            'un `mensaje_sin_apps(n, "apagar")` con el VERBO cableado tiene que matar el '
            'guard. `panel.py` esta FUERA de `ui/views/` a proposito: con el recorrido '
            "recortado a las vistas, el alcance se acorta en silencio y el verbo cableado "
            "pasa"
        )
        assert "panel.py" in marca and "L6" in marca, (
            f"el guard tiene que nombrar FICHERO y LINEA del cableado: {marca}"
        )

        # (4) LA FORMA `ast.Attribute`. `fb.mensaje_sin_apps(...)` tras
        # `import feedback as fb` es la forma idiomatica de Python, y con
        # `getattr(func, "id", None)` el nodo no tiene `id`: la llamada se
        # saltaba en silencio (mutante M6).
        marca = None
        try:
            _guardar_contrato_de_llamantes(atributo, acciones_validas)
        except AssertionError as exc:
            marca = str(exc)
        assert marca is not None, (
            '`fb.mensaje_sin_apps(n, "iniciar")` es una llamada como cualquier otra. Con '
            '`getattr(func, "id", None)` el `ast.Attribute` devuelve `None` y la llamada se '
            "salta en silencio: es la forma idiomatica de importar y era invisible"
        )
        assert "widget.py" in marca and "L6" in marca, (
            f"el guard tiene que nombrar FICHERO y LINEA del cableado en forma atributo: {marca}"
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"Guard del contrato: {len(reales)} importadores reales derivados, y en el arbol "
          "sintetico 4 de 5 modulos entran con las dos formas de llamada cubiertas.")


def test_el_log_rota_con_el_limite_declarado():
    """M3b: `architecture.md` §15 declara que el log rota, y no lo comprobaba
    nadie. El `isinstance(h, logging.FileHandler)` de la sonda T1 NO lo
    distingue, porque `RotatingFileHandler` **hereda** de `FileHandler`: cambiar
    `RotatingFileHandler` por un `FileHandler` plano (y volver a crecer 1,8 MB)
    dejaba la suite en verde.

    Por eso aqui se afirma el TIPO EXACTO (`type(h) is RotatingFileHandler`, no
    `isinstance`) y los ATRIBUTOS que hacen que rote, contra las constantes
    declaradas en `config.py` (codigo, no doc).
    """
    import logging
    from logging.handlers import RotatingFileHandler
    from woptimizer.config import LOG_BACKUP_COUNT, LOG_MAX_BYTES, setup_logging

    root = logging.getLogger()
    handlers_prev = root.handlers[:]
    level_prev = root.level
    try:
        root.handlers.clear()
        setup_logging()
        tipos = [type(h) for h in root.handlers]
        assert tipos == [RotatingFileHandler], (
            f"el root debe tener EXACTAMENTE un RotatingFileHandler y tiene {tipos}. "
            "isinstance(h, FileHandler) no lo distingue porque RotatingFileHandler hereda de "
            "FileHandler: un FileHandler plano pasaria ese isinstance y el log volveria a "
            "crecer sin limite (M3b)"
        )
        h = root.handlers[0]
        assert h.maxBytes == LOG_MAX_BYTES and h.backupCount == LOG_BACKUP_COUNT, (
            f"la rotacion esta mal ajustada: maxBytes={h.maxBytes} (declarado {LOG_MAX_BYTES}), "
            f"backupCount={h.backupCount} (declarado {LOG_BACKUP_COUNT})"
        )
        assert LOG_MAX_BYTES > 0 and LOG_BACKUP_COUNT > 0, (
            f"rotar con maxBytes={LOG_MAX_BYTES} y backupCount={LOG_BACKUP_COUNT} no rota nada"
        )
    finally:
        for h in root.handlers:
            if not any(h is p for p in handlers_prev):
                h.close()
        root.handlers[:] = handlers_prev
        root.setLevel(level_prev)

    print("El log rota de verdad: tipo exacto y limites medidos contra el codigo.")


# TASK-028 iteracion 3: el detector de "configurar el logging al importar".
#
# EL CRITERIO, que es lo que hace que esto no sea un detector de adivinar:
#   * CONFIGURAR = ADJUNTAR un handler a un logger, FIJARLE nivel o formato, o
#     REEMPLAZAR su lista `handlers`. Las tres cosas hacen que el root cambie
#     como efecto colateral de `import config`, que es el defecto que FIX-010
#     cerro y que §15 promete que no vuelve.
#   * OBTENER no es configurar: `logging.getLogger(__name__)`, incluso sin
#     argumentos (el root), es una ASIGNACION normal. `logger =
#     logging.getLogger('woptimizer')` lo importan cuatro modulos
#     (notification_service, pack_service, process_service, ui/app) y es el
#     punto de contrato: un detector que lo marque obligaria a moverlo para no
#     tener que pensar, y el invariante seria el equivocado.
#   * Construir un handler sin adjuntarlo tampoco configura nada: no emite.
#
# Las dos mitades se comprueban con las tablas ILEGALES y LEGALES de la sonda,
# que son la razon de que el detector no pueda quedarse demasiado estrecho ni
# demasiado amplio: los dos fallos dan el MISMO verde.
_MUTADORES_DE_LOG = {
    "addHandler", "removeHandler", "setLevel", "setFormatter", "setHandlers",
    "addFilter", "captureWarnings",
    # Los de la LISTA, que solo cuentan si el receptor es `<logger>.handlers`:
    "append", "extend", "clear", "insert", "pop", "remove",
}
_FUNCIONES_DE_CONFIG = {"basicConfig", "dictConfig", "fileConfig", "disable"}
# Nombres desnudos que solo valen si vienen de `logging` (o de un import de
# `logging`), para no marcar `algo.disable()` de otra biblioteca.
_FICIONES_DE_LOG = {"logging", "logging.config", "logging.logconfig"}


def _ruta_dotted(nodo):
    """`a.b.c` -> 'a.b.c'; lo que no sea una cadena de nombres, None."""
    if isinstance(nodo, ast.Name):
        return nodo.id
    if isinstance(nodo, ast.Attribute):
        base = _ruta_dotted(nodo.value)
        return f"{base}.{nodo.attr}" if base else None
    return None


def _es_get_logger(nodo):
    return isinstance(nodo, ast.Call) and _ruta_dotted(nodo.func) in (
        "logging.getLogger", "getLogger")


def _bloques_de_ejecucion(stmt):
    """Las listas de sentencias que `stmt` ejecuta cuando el modulo se importa.

    Son `body`/`orelse`/`finalbody` de los compuestos (if, try, for, while,
    with, match) mas los `handlers` de un `try` y los `cases` de un `match`.
    Los dos ultimos no son `ast.stmt`, y por eso se ceden tal cual: quien
    recurse ya sabe bajar a su `.body`.
    """
    for nombre in ("body", "orelse", "finalbody"):
        for sub in getattr(stmt, nombre, None) or ():
            if isinstance(sub, ast.stmt):
                yield sub
    for handler in getattr(stmt, "handlers", None) or ():
        yield handler
    for caso in getattr(stmt, "cases", None) or ():
        yield caso


def _plano_de_ejecucion(bloque, dentro_de_clase=False):
    """`bloque` aplanado en el orden en que se EJECUTA, sin cruzar fronteras.

    ITERACION 4, S3 y S4. El aplanado anterior era `arbol.body` a pelo, y eso
    hacia dos-hole, los dos medidos por el mutation-auditor:

      * (S3) `if __name__ == '__main__': logger = logging.getLogger(__name__)`
        seguido de `logger.addHandler(h)` a nivel de modulo: el `Assign` del
        logger esta anidado en el `if`, no se recogia, el mutador no
        reconocia el receptor y la configuracion PASABA. Es el defecto de
        FIX-010 colandose por una indireccion.
      * (S4) el cuerpo de una CLASE va entero a `dentro`, sin mirar su
        contenido, y el cuerpo de una clase SI se ejecuta al importar el
        modulo. `class X: logging.basicConfig(...)` es tan configurable al
        importar como `logging.basicConfig(...)` en la cima.

    Ahora se entra en `if`/`try`/`for`/`while`/`with`/`match` a cualquier nivel
    de bloque, y en el cuerpo de una clase, pero NUNCA en el de una clase
    anidada (que pertenece a OTRO ambito: se ejecuta al importarla, no al
    importar este modulo).

    ITERACION 5, D3. Un `def` ya no es una frontera ciega: se RECOGE (para que
    `_NodosEjecutados` le mire los decoradores y los argumentos por defecto) pero
    NO se baja a su cuerpo. La distincion no es de estilo, es de lo que ejecuta
    Python, medido en este interprete (`root.handlers` tras importar, sin
    ningun `setup_logging`):

        def f(h=logging.basicConfig(force=True)): ...   -> 1  (SE CONFIGURA)
        class C:
            def m(self, h=logging.basicConfig(...)): ...  -> 1  (SE CONFIGURA)
        f = lambda h=logging.basicConfig(force=True): h   -> 1  (SE CONFIGURA)
        def f(*, h=logging.basicConfig(force=True)): ...  -> 1  (SE CONFIGURA)
        def f(): logging.basicConfig(force=True)          -> 0  (cuerpo: no)

    O sea: el `def` EVALUA sus decoradores, sus valores por defecto y sus
    anotaciones en el momento de la definicion, y el cuerpo no. Antes esta sonda
    se saltaba los tres sin querer (`visit_FunctionDef = pass`), o sea que
    M16 hacia sitio en un `def` con `basicConfig` en el defecto. Se mantiene la
    frontera del CUERPO, que es la que S4 y la iteracion 3 ya Tenian medida.
    """
    for stmt in bloque:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield stmt                            # el `def` se mira (D3)
            continue                              # su cuerpo, no
        if isinstance(stmt, ast.Lambda):
            continue                              # la lambda no se invoca
        if isinstance(stmt, ast.ClassDef):
            if dentro_de_clase:
                continue                          # clase anidada: otro ámbito
            yield from _plano_de_ejecucion(stmt.body, dentro_de_clase=True)
            continue
        yield stmt
        yield from _plano_de_ejecucion(_bloques_de_ejecucion(stmt), dentro_de_clase)


def _usa_anotaciones_lazosas(arbol):
    """True si el modulo tiene `from __future__ import annotations`.

    Con ese `__future__`, las anotaciones se guardan como TEXTO y no se
    evaluan; sin el, se evaluan al definir la funcion. Medido: la misma
    anotacion da `root.handlers == 1` sin el `__future__` y `== 0` con el. Por
    que se decide mirando el `__future__` y no siempre que no: un
    `NamedTuple`/`TypedDict` con una anotacion construida a mano es legal, y sin
    este matiz el detector marcaria documentos que no configuran nada.
    """
    for stmt in arbol.body:
        if isinstance(stmt, ast.ImportFrom) and stmt.module == "__future__":
            if any(alias.name == "annotations" for alias in stmt.names):
                return True
    return False


class _NodosEjecutados(ast.NodeVisitor):
    """Recoge los nodos de lo que se EJECUTA al importar, sin los cuerpos.

    `ast.walk` baja al subarbol ENTERO, de modo que una funcion anidada en un
    `if` de nivel de modulo (`if __name__ == '__main__': def main(): ...`)
    hacia que su cuerpo se escaneara como si se ejecutara al importar. Aqui se
    entra en el cuerpo de una CLASE (que si se ejecuta, S4) pero no en el de
    una funcion ni en el de una lambda (que no se ejecutan hasta que se llamen).
    Una comprehension si se ejecuta, y por eso se recorre: `[logging.
    basicConfig() for _ in (1,)]` configura el root de verdad al importar.

    ITERACION 5, D3. `visit_FunctionDef` ya no es un `pass`: el `def` EVALUA
    decoradores, valores por defecto y anotaciones al definirse (medido en este
    interprete: los cuatro casos dan `root.handlers == 1` al importar), asi que
    se recorren. Lo que NO se toca es el `body`, que es la frontera que S4 y la
    iteracion 3 ya tenian medida.

    ITERACION 5, D4. Un GENERADOR es perezoso y una comprehension no, y la
    diferencia es REAL y no academica (medido):
        g = (logging.basicConfig(force=True) for _ in (1,))  -> 0  (no se ejecuta)
        [logging.basicConfig(force=True) for _ in (1,)]      -> 1  (se ejecuta)
    Marcar el generador era un FALSO POSITIVO: el codigo marcado no configura
    nada al importar, y un detector que marca de mas acaba ignorandose. Se
    recorre, pero solo su ITERABLE DE ENTRADA (lo unico que se evalua al crear
    el generador), no su elemento.
    """

    def __init__(self, anotaciones_lazosas=False):
        self.nodos = []
        self._anotaciones_lazosas = anotaciones_lazosas

    def _visita_firma(self, nodo):
        """Decoradores, valores por defecto y anotaciones: lo que se EVALUA al
        definir la funcion. El `body` no se mira, que es la frontera dura."""
        for deco in getattr(nodo, "decorator_list", ()):
            self.visit(deco)
        args = nodo.args
        for defecto in list(args.defaults) + [d for d in args.kw_defaults if d]:
            self.visit(defecto)
        if self._anotaciones_lazosas:
            return
        # Sin `from __future__ import annotations` las anotaciones SI se
        # evaluan (medido: la misma da handlers==1 sin el y ==0 con el). Con el
        # `__future__` se guardan como texto y marcarlas seria un falso positivo
        # sobre documentos legitimos (un `NamedTuple`/`TypedDict` con una
        # anotacion construida a mano).
        for grupo in (args.posonlyargs, args.args, args.kwonlyargs):
            for a in grupo:
                if a.annotation is not None:
                    self.visit(a.annotation)
        if getattr(nodo, "returns", None) is not None:
            self.visit(nodo.returns)

    def visit_FunctionDef(self, nodo):
        self._visita_firma(nodo)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Lambda(self, nodo):
        # La lambda NO se invoca al importar, pero sus valores por defecto y su
        # anotacion SI se evaluan: `lambda h=logging.basicConfig(...): h` deja el
        # root con un handler (medido). Su `body` no se toca.
        self._visita_firma(nodo)

    def visit_GeneratorExp(self, nodo):
        # Solo el iterable de ENTRADA se evalua al crear el generador; el resto
        # de la cadena y el elemento son perezosos. Medido: el elemento NO
        # configura nada, pero una lista CON `[logging.basicConfig(...)]` en el
        # iterable de entrada SI configura, porque la lista se construye entera.
        if nodo.generators:
            self.visit(nodo.generators[0].iter)

    def generic_visit(self, nodo):
        self.nodos.append(nodo)
        super().generic_visit(nodo)


def _configuraciones_de_logging(codigo, nombre="<memoria>"):
    """Lineas que CONFIGURAN el logging AL IMPORTAR el modulo. -> (fuera, dentro).

    `fuera` son las que se ejecutan al importar, y son las que prohibe §15: a
    nivel de modulo, dentro de un `if`/`try`/`for`/`while`/`with` de nivel de
    modulo, y **dentro del cuerpo de una clase**, porque el cuerpo de una clase
    tambien se ejecuta al importarla (S4).

    `dentro` son las que estan dentro de una **FUNCION**, y eso es lo
    unicamente permitido: `setup_logging()` existe precisamente para configurar
    ahi, y se invoca desde `__main__` y desde la suite. La version anterior de
    este docstring decia "una funcion **o una clase**", que era un criterio
    FALSO y por eso la documentacion mintio junto al detector (S4).

    ITERACION 5, D3/D4. El `def` se RECOGE (sus decoradores, sus valores por
    defecto y sus anotaciones se evaluan al definirlo, medido) pero su CUERPO
    sigue yendo a `dentro`; y un generador perezoso no se marca (su elemento no
    se ejecuta al importar, medido) mientras que una comprehension si.
    """
    arbol = ast.parse(codigo, filename=nombre)

    # (1) Los loggers NOMBRADOS a nivel de modulo: `X = logging.getLogger(...)`,
    #     tambien si la asignacion esta dentro de un `if`/`try`/`for`/`while`
    #     (S3). Sin esto, `if ...: logger = getLogger(__name__)` + un
    #     `logger.addHandler()` al nivel de modulo se escapaba entero.
    loggers = set()
    for stmt in _plano_de_ejecucion(arbol.body):
        if isinstance(stmt, ast.Assign):
            objetivos, valor = stmt.targets, stmt.value
        elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
            objetivos, valor = [stmt.target], stmt.value
        else:
            continue
        if _es_get_logger(valor):
            loggers |= {t.id for t in objetivos if isinstance(t, ast.Name)}

    def _es_logger(nodo):
        return _es_get_logger(nodo) or (isinstance(nodo, ast.Name) and nodo.id in loggers)

    def _es_lista_de_handlers(nodo):
        return (isinstance(nodo, ast.Attribute) and nodo.attr == "handlers"
                and _es_logger(nodo.value))

    def _motivos(bloque):
        # `bloque` son sentencias YA APLANADAS por `_plano_de_ejecucion`, y el
        # recolector `_NodosEjecutados` no entra en el cuerpo de una funcion
        # (ni de una lambda), de modo que lo que llega aqui se EJECUTA al
        # importar. El matiz es real y medido: con un `ast.walk` a pelo,
        # `if True: def main(): logging.basicConfig(...)` marcaba la linea de
        # la funcion, o sea un falso positivo legal que la iteracion 3 arrastraba.
        for sentencia in bloque:
            recolector = _NodosEjecutados(_usa_anotaciones_lazosas(arbol))
            recolector.visit(sentencia)
            for n in recolector.nodos:
                if isinstance(n, ast.Call):
                    func, ruta = n.func, _ruta_dotted(n.func)
                    if ruta:
                        ultimo = ruta.rsplit(".", 1)[-1]
                        cabecera = ruta.rsplit(".", 1)[0] if "." in ruta else None
                        if ultimo in _FUNCIONES_DE_CONFIG and (
                                cabecera in _FICIONES_DE_LOG or not cabecera):
                            yield n.lineno, f"llamada de configuracion {ruta}()"
                            continue
                    if (isinstance(func, ast.Attribute) and func.attr in _MUTADORES_DE_LOG
                            and (_es_logger(func.value) or _es_lista_de_handlers(func.value))):
                        yield (n.lineno,
                               f"mutador .{func.attr}() sobre un logger que se configura al "
                               "importar")
                elif isinstance(n, ast.Assign):
                    for t in n.targets:
                        if _es_lista_de_handlers(t):
                            yield n.lineno, "asignacion a <logger>.handlers"
                        elif isinstance(t, ast.Subscript) and _es_lista_de_handlers(t.value):
                            yield n.lineno, "asignacion a <logger>.handlers[...]"
                elif isinstance(n, ast.AugAssign):
                    if _es_lista_de_handlers(n.target):
                        yield n.lineno, "asignacion a <logger>.handlers"
                    elif (isinstance(n.target, ast.Subscript)
                          and _es_lista_de_handlers(n.target.value)):
                        yield n.lineno, "asignacion a <logger>.handlers[...]"

    fuera, dentro = [], []
    for stmt in arbol.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # D3: el CUERPO de un def de nivel de modulo va a `dentro` (ahi no se
            # ejecuta nada al importar), pero su FIRMA -decoradores, valores por
            # defecto y anotaciones- SI se evalua al definirlo y va a `fuera`.
            # Sin esta linea, `def f(h=logging.basicConfig(force=True))` pasaba
            # entero: el `def` se iba a `dentro` sin que nadie mirase su firma.
            fuera += _motivos([stmt])
            dentro += _motivos(_plano_de_ejecucion(stmt.body))
        else:
            fuera += _motivos(_plano_de_ejecucion([stmt]))
    return fuera, dentro


def test_config_no_configura_nada_al_importarse():
    """M16 (y su hermano, mismo defecto con otro nombre de funcion):
    `architecture.md` §15 afirma que "`config.py` no configura nada al
    importarse". Reinyectar `logging.basicConfig(...)` a nivel de modulo dejaba
    la suite en verde, y no por casualidad: la sonda T1 **limpia los handlers
    DESPUES de importar**, asi que por construccion no puede verlo. Es el
    patron de validador que se deduce a si mismo otra vez, por el otro lado.

    ITERACION 3. El detector anterior buscaba **una sola** llamada,
    `basicConfig`, y las tres que el `mutation-auditor` dejo en verde son el
    MISMO defecto con otro nombre de funcion:
      * `logging.getLogger().addHandler(logging.StreamHandler())`
      * `logger.addHandler(logging.StreamHandler())`
      * `logging.config.dictConfig({...})`
    Las tres configuran el root como efecto colateral de importar, y las tres
    pasaban. O sea: la promesa de la doc era mas fuerte que lo que se media.

    Por eso el criterio esta escrito arriba (configurar = adjuntar/fijar
    nivel/formato/reemplazar `handlers`; obtener el logger NO es configurar) y
    por eso el detector se prueba CONTRA SI MISMO en las dos direcciones, con
    codigo sintetico: ILEGALES tiene que marcar las catorce y LEGALES no puede
    marcar ninguna. Un detector que no ve nada y uno que ve de mas dan el
    MISMO verde, y sin las dos tablas no se sabe cual de los dos se tiene.

    ITERACION 4, S3 y S4 (los dos huecos que dejo el detector de la iteracion 3,
    ambos medidos por el mutation-auditor):
      * (S3) El logger asignado DENTRO de un `if`/`try`/`for`/`while` de nivel
        de modulo no se recognia: `if __name__ == '__main__': logger =
        getLogger(__name__)` + un `logger.addHandler(h)` al nivel de modulo
        PASABA, y es el defecto de FIX-010 por indireccion.
      * (S4) El CUERPO DE UNA CLASE contaba como permitido. No lo es: se ejecuta
        al importar el modulo, igual que la cima. Y el docstring decia "una
        funcion o una clase", o sea: el criterio era FALSO y la doc mintio con
        el. El valido es "dentro de una FUNCION", y las tablas de aqui lo fijan
        en las dos direcciones (metodo de clase = legal, cuerpo de clase = ilegal).
    """
    raiz = os.path.dirname(os.path.abspath(__file__))
    ruta_cfg = os.path.join(raiz, "src", "woptimizer", "config.py")
    with open(ruta_cfg, encoding="utf-8") as fh:
        fuera, dentro = _configuraciones_de_logging(fh.read(), ruta_cfg)

    assert not fuera, (
        f"config.py CONFIGURA el logging a NIVEL DE MODULO en {fuera}: el canal de log vuelve a "
        "configurarse como efecto colateral de importar, que es exactamente el defecto que "
        "FIX-010 cerro. Se rompe en silencio en cuanto alguien importa el paquete sin pasar por "
        "__main__. El criterio esta escrito en el docstring de `_configuraciones_de_logging` "
        "(M16: basicConfig; M16b-M16d: las otras tres formas del mismo defecto)"
    )
    assert dentro, (
        "CONTROL ROTO: el detector no encuentra NI UNA configuracion de logging dentro de "
        "config.py, ni siquiera en setup_logging(). Un detector que no ve nada no puede probar "
        "que no haya nada: la asercion de arriba pasaria siempre."
    )

    ILEGALES = (
        ("getLogger().addHandler() sobre el root",
         "logging.getLogger().addHandler(logging.StreamHandler())"),
        ("addHandler() sobre un logger nombrado",
         "logger = logging.getLogger('woptimizer')\nlogger.addHandler(logging.StreamHandler())"),
        ("logging.config.dictConfig()",
         "import logging.config\nlogging.config.dictConfig({'version': 1})"),
        ("logging.config.fileConfig()",
         "import logging.config\nlogging.config.fileConfig('w.ini', disable_existing_loggers=False)"),
        ("setLevel() sobre el root",
         "logging.getLogger().setLevel(logging.DEBUG)"),
        ("handlers[:] = [...] del root",
         "root = logging.getLogger()\nroot.handlers[:] = [logging.StreamHandler()]"),
        ("handlers.clear() del root",
         "root = logging.getLogger()\nroot.handlers.clear()"),
        ("addHandler() sobre logging.getLogger(__name__)",
         "logger = logging.getLogger(__name__)\nlogger.addHandler(h)"),
        # --- S3: el receptor se NOMBRA dentro de un bloque de nivel de modulo
        ("addHandler() con el logger asignado dentro de un if de modulo (S3)",
         "if __name__ == '__main__':\n    logger = logging.getLogger(__name__)\n"
         "logger.addHandler(h)"),
        ("setLevel() con el logger asignado dentro de un try de modulo (S3)",
         "try:\n    logger = logging.getLogger('woptimizer')\nexcept Exception:\n"
         "    logger = None\nlogger.setLevel(logging.DEBUG)"),
        ("handlers.clear() con el logger asignado en un for de modulo (S3)",
         "for _ in (1,):\n    logger = logging.getLogger()\nlogger.handlers.clear()"),
        # --- S4: el CUERPO DE UNA CLASE se ejecuta al importar, como la cima
        ("basicConfig() en el CUERPO de una clase (S4)",
         "class Instala:\n    logging.basicConfig(force=True)"),
        ("addHandler() en el cuerpo de una clase, logger nombrado en la clase (S4)",
         "class Instala:\n    logger = logging.getLogger('woptimizer')\n"
         "    logger.addHandler(h)"),
        ("basicConfig() DENTRO de una comprehension de modulo (si se ejecuta)",
         "arranque = [logging.basicConfig(force=True) for _ in (1,)]"),
        # --- D3 (iteracion 5): el `def` EVALUA firma, no cuerpo
        ("basicConfig() como ARGUMENTO POR DEFECTO de un def de modulo (D3)",
         "def instalar(h=logging.basicConfig(force=True)):\n    return h"),
        ("basicConfig() como kwonly por defecto de un def de modulo (D3)",
         "def instalar(*, h=logging.basicConfig(force=True)):\n    return h"),
        ("basicConfig() como DEFECTO de un METODO (D3)",
         "class C:\n    def instalar(self, h=logging.basicConfig(force=True)):\n        return h"),
        ("basicConfig() como DEFECTO de una LAMBDA de modulo (D3)",
         "instalar = lambda h=logging.basicConfig(force=True): h"),
        ("basicConfig() como ANOTACION de un def de modulo (D3)",
         "import logging\ndef instalar(h: logging.basicConfig(force=True)):\n    pass"),
        # --- D4 (iteracion 5): el ITERABLE DE ENTRADA del generador SI se
        # evalua al crearlo (la lista se construye entera). Medido: handlers==1.
        ("basicConfig() en el ITERABLE DE ENTRADA de un generador (si se ejecuta)",
         "arranque = (x for x in [logging.basicConfig(force=True)])"),
    )
    for etiqueta, codigo in ILEGALES:
        halladas, _ = _configuraciones_de_logging(codigo, etiqueta)
        assert halladas, (
            f"CONTROL ROTO (falso NEGATIVO): el detector no marca «{etiqueta}» "
            f"({codigo!r}). Esa forma configura el logging al importarse, y es la que "
            "M16b/M16c/M16d dejaron en verde, o la indireccion que S3 y S4 reabrieron. "
            "O el detector se ha quedado estrecho otra vez."
        )

    LEGALES = (
        ("configuracion DENTRO de una funcion",
         "def setup():\n    logging.basicConfig(force=True)"),
        ("logger nombrado", "logger = logging.getLogger('woptimizer')"),
        ("logging.getLogger(__name__)", "import logging\nlogger = logging.getLogger(__name__)"),
        ("el root obtenido y nada mas", "root = logging.getLogger()"),
        ("handler construido sin adjuntar", "import logging\nh = logging.StreamHandler()"),
        ("constantes de formato", "LOG_FORMAT = '%(asctime)s - %(message)s'"),
        # El cuerpo de una clase es ILEGAL, pero lo que hay DENTRO de un metodo
        # sigue siendo legal: ahi no se ejecuta nada al importar (S4).
        ("configuracion DENTRO de un metodo de clase",
         "class Instala:\n    def setup(self):\n        logging.basicConfig(force=True)"),
        ("configuracion DENTRO de una funcion anidada en un if de modulo",
         "if __name__ == '__main__':\n    def main():\n"
         "        logging.basicConfig(force=True)"),
        ("atributo de clase que se LLAMA addHandler (no es el logging)",
         "class T:\n    def addHandler(self, h):\n        pass\nT().addHandler(1)"),
        ("basicConfig() dentro del cuerpo de una lambda (no se ejecuta al importar)",
         "instala = lambda: logging.basicConfig(force=True)"),
        # --- D4 (iteracion 5): el ELEMENTO de un generador NO se ejecuta al
        # importarlo, a diferencia de una comprehension. Medido: 0 vs 1 handler.
        # Sin esta fila, un detector que tratara el generador como la
        # comprehension marcaria codigo que no configura nada.
        ("basicConfig() en el ELEMENTO de un generador perezoso (D4, NO se ejecuta)",
         "arranque = (logging.basicConfig(force=True) for _ in (1,))"),
        ("basicConfig() en un generador anidado en una clase (D4, NO se ejecuta)",
         "class Instala:\n    g = (logging.basicConfig(force=True) for _ in (1,))"),
        # --- D3 (iteracion 5): con `from __future__ import annotations` las
        # anotaciones se guardan como TEXTO y no se evaluan. Medido: 0 handlers.
        ("anotacion con basicConfig() PERO con __future__ annotations (D3, no se evalua)",
         "from __future__ import annotations\nimport logging\n"
         "def instalar(h: logging.basicConfig(force=True)):\n    pass"),
        # D3: el CUERPO de un def sigue sin ejecutarse al importar, que es la
        # frontera que ya estaba medida. Si esta fila se marcara, el detector
        # habria demasiado ancho y no habria forma de configurar el log.
        ("basicConfig() en el CUERPO de un def de modulo (D3, el cuerpo no se ejecuta)",
         "def instalar():\n    logging.basicConfig(force=True)"),
    )
    for etiqueta, codigo in LEGALES:
        halladas, _ = _configuraciones_de_logging(codigo, etiqueta)
        assert not halladas, (
            f"CONTROL ROTO (falso POSITIVO): el detector marca «{etiqueta}» ({halladas}). "
            "Obtener el logger NO es configurarlo: `logger = logging.getLogger(...)` es el "
            "punto de contrato que importan cuatro modulos, y un detector que marca de mas "
            "acaba ignorandose (matar M16b/M16c/M16d no puede ser facil)"
        )

    # El recuento se DERIVA de las tablas, no se escribe a mano: hacia falta
    # actualizarlo cada vez que se anadia una fila y era un numero que mentia
    # en cuanto dejaba de cuadrar (doc. D2: si esto dice 20 y son 19, la sonda
    # de la doc va a mentir en silencio).
    print(f"config.py no configura el logging al importarse (detector probado en las dos "
          f"direcciones: {len(ILEGALES)} ilegales marcados, {len(LEGALES)} legales sin "
          "marcar; S3: el logger asignado dentro de un if/try/for cuenta; S4: el cuerpo de "
          "una clase NO es un refugio; D3: la FIRMA de un def (decoradores, defaults, "
          "anotaciones) se evalua al importarlo pero su cuerpo no; D4: un generador perezoso "
          "no se ejecuta al importarlo y una comprehension si).")


def test_no_literal_colors_in_views():
    """TASK-029 (UI-002a): ninguna vista ni main_window usa literales de color hex.
    
    Verifica que todo color en fg_color, hover_color, text_color o border_color
    provenga de tokens de theme.py (o variables semanticas), nunca strings '#RRGGBB'.
    """
    import ast

    archivos = [
        "src/woptimizer/ui/main_window.py",
        "src/woptimizer/ui/views/dashboard_view.py",
        "src/woptimizer/ui/views/pack_manager_view.py",
        "src/woptimizer/ui/views/process_manager_view.py",
    ]
    color_kwargs = {"fg_color", "hover_color", "text_color", "border_color"}

    def _escanear_literales(codigo: str, nombre_archivo: str = "<prueba>"):
        violaciones = []
        tree = ast.parse(codigo, nombre_archivo)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for kw in node.keywords:
                    if kw.arg in color_kwargs:
                        if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                            if kw.value.value.startswith("#"):
                                violaciones.append((node.lineno, kw.arg, kw.value.value))
                        elif isinstance(kw.value, (ast.List, ast.Tuple)):
                            for elt in kw.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                    if elt.value.startswith("#"):
                                        violaciones.append((node.lineno, kw.arg, elt.value))
        return violaciones

    # Control de discriminacion: verificar que el detector detecta infracciones
    codigo_sucio = 'btn = ctk.CTkButton(fg_color="#123456", hover_color=["#111111", "#222222"])'
    hallazgos_control = _escanear_literales(codigo_sucio)
    assert len(hallazgos_control) == 3, f"Detector no discrimina violaciones de control: {hallazgos_control}"

    total_violaciones = []
    for rel_path in archivos:
        full_path = os.path.join(os.path.dirname(__file__), rel_path)
        with open(full_path, "r", encoding="utf-8") as f:
            contenido = f.read()
        viols = _escanear_literales(contenido, rel_path)
        if viols:
            total_violaciones.extend([(rel_path, lineno, kw, val) for lineno, kw, val in viols])

    assert not total_violaciones, f"Se encontraron literales de color hex en vistas: {total_violaciones}"
    print("test_no_literal_colors_in_views OK (cero literales hex en vistas, detector discriminante probado).")


def test_theme_tokens_complete():
    """TASK-029 (UI-002b): theme.py exporta todos los tokens requeridos.
    
    Verifica los roles semanticos de color, exactamente 6 tamanos de fuente
    y 3 radios de borde declarados.
    """
    from woptimizer.ui import theme

    tokens_color = [
        "SURFACE", "SURFACE_ALT", "SURFACE_SUNKEN", "SURFACE_HOVER", "BORDER",
        "TEXT_PRIMARY", "TEXT_MUTED",
        "GAMING", "GAMING_HOVER",
        "ACCENT", "ACCENT_HOVER",
        "DANGER", "DANGER_HOVER",
        "WARNING", "SUCCESS",
    ]
    for tk in tokens_color:
        assert hasattr(theme, tk), f"Token de color faltante en theme.py: {tk}"
        val = getattr(theme, tk)
        assert isinstance(val, str) and val.startswith("#") and len(val) == 7, (
            f"Token {tk} debe ser hex '#RRGGBB', recibido: {val}"
        )

    # Escala de exactamente 6 fuentes
    assert hasattr(theme, "FONT_SIZES"), "theme.py debe exportar FONT_SIZES"
    assert theme.FONT_SIZES == (9, 11, 13, 14, 18, 24), (
        f"Escala tipografica esperada (9, 11, 13, 14, 18, 24), recibida: {theme.FONT_SIZES}"
    )
    assert len(theme.FONT_SIZES) == 6, f"Se esperaban exactamente 6 fuentes, hay {len(theme.FONT_SIZES)}"

    # Radios de exactamente 3 tamanos
    assert hasattr(theme, "RADII"), "theme.py debe exportar RADII"
    assert theme.RADII == (4, 6, 8), f"Radios esperados (4, 6, 8), recibidos: {theme.RADII}"
    assert len(theme.RADII) == 3, f"Se esperaban exactamente 3 radios, hay {len(theme.RADII)}"

    print("test_theme_tokens_complete OK (15 tokens de color, 6 fuentes, 3 radios exactos).")


def test_contrast_wcag_aa():
    """TASK-029 (UI-010): pares de colores de texto y fondo cumplen WCAG AA (>= 4.5:1, o >= 3.0:1 para texto grande)."""
    from woptimizer.ui import theme

    pares_normales = [
        (theme.TEXT_PRIMARY, theme.SURFACE, "TEXT_PRIMARY / SURFACE"),
        (theme.TEXT_PRIMARY, theme.SURFACE_ALT, "TEXT_PRIMARY / SURFACE_ALT"),
        (theme.TEXT_PRIMARY, theme.SURFACE_SUNKEN, "TEXT_PRIMARY / SURFACE_SUNKEN"),
        (theme.TEXT_PRIMARY, theme.DANGER, "TEXT_PRIMARY / DANGER"),
        (theme.TEXT_MUTED, theme.SURFACE, "TEXT_MUTED / SURFACE"),
        (theme.TEXT_MUTED, theme.SURFACE_ALT, "TEXT_MUTED / SURFACE_ALT"),
        (theme.SURFACE, theme.GAMING, "SURFACE / GAMING"),
        (theme.GAMING, theme.SURFACE_ALT, "GAMING / SURFACE_ALT"),
        (theme.ACCENT, theme.SURFACE_ALT, "ACCENT / SURFACE_ALT"),
    ]

    for fg, bg, etiqueta in pares_normales:
        ratio = theme.contrast_ratio(fg, bg)
        assert ratio >= 4.5, (
            f"Fallo de contraste WCAG AA para {etiqueta}: ratio {ratio:.2f}:1 inferior a 4.5:1 "
            f"(fg={fg}, bg={bg})"
        )
        assert theme.is_wcag_aa(fg, bg, large_text=False), (
            f"is_wcag_aa devolvio False para {etiqueta}"
        )

    # Texto grande o de acento en botones (umbral 3.0:1)
    pares_grandes = [
        (theme.TEXT_PRIMARY, theme.ACCENT, "TEXT_PRIMARY / ACCENT"),
    ]
    for fg, bg, etiqueta in pares_grandes:
        ratio = theme.contrast_ratio(fg, bg)
        assert ratio >= 3.0, (
            f"Fallo de contraste WCAG AA para texto grande {etiqueta}: ratio {ratio:.2f}:1 inferior a 3.0:1 "
            f"(fg={fg}, bg={bg})"
        )
        assert theme.is_wcag_aa(fg, bg, large_text=True), (
            f"is_wcag_aa devolvio False para texto grande {etiqueta}"
        )

    # Discriminacion: comprobar que un par de bajo contraste falla
    par_invalido = theme.contrast_ratio("#777777", "#666666")
    assert par_invalido < 4.5, "El calculador de contraste no detecta contraste insuficiente"
    assert not theme.is_wcag_aa("#777777", "#666666"), "is_wcag_aa no detecta contraste insuficiente"

    print("test_contrast_wcag_aa OK (todos los pares de interfaz cumplen WCAG AA >= 4.5:1 o >= 3.0:1).")


def test_hit_targets_minimum():
    """TASK-029 (UI-007): todos los botones y controles interactivos tienen dimensiones >= 28x28px.
    
    Verifica mediante AST y configuracion estatica que ningun CTkButton especifique width < 28 o height < 28.
    """
    import ast

    archivos = [
        "src/woptimizer/ui/main_window.py",
        "src/woptimizer/ui/views/dashboard_view.py",
        "src/woptimizer/ui/views/pack_manager_view.py",
        "src/woptimizer/ui/views/process_manager_view.py",
    ]

    violaciones = []
    for rel_path in archivos:
        full_path = os.path.join(os.path.dirname(__file__), rel_path)
        with open(full_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), rel_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                is_btn = False
                if isinstance(node.func, ast.Attribute) and node.func.attr == "CTkButton":
                    is_btn = True
                elif isinstance(node.func, ast.Name) and node.func.id == "CTkButton":
                    is_btn = True
                if is_btn:
                    for kw in node.keywords:
                        if kw.arg in ("width", "height") and isinstance(kw.value, ast.Constant):
                            if isinstance(kw.value.value, (int, float)) and kw.value.value < 28:
                                violaciones.append((rel_path, node.lineno, kw.arg, kw.value.value))

    assert not violaciones, f"Botones con hit target menor a 28x28px detectados: {violaciones}"
    print("test_hit_targets_minimum OK (todos los botones interactivos cumplen cota minima de 28x28px).")


def test_semantic_color_contract():
    """TASK-029 (UI-012b): contrato semantico de colores de marca y estados.
    
    Verifica que:
    1. theme.DANGER no se asigne a elementos gaming.
    2. theme.GAMING sea verde (#1DB954) y no rojo (#c22d2d).
    3. config.get_safety_badge no use ni contamine el token GAMING.
    """
    from woptimizer.ui import theme
    from woptimizer.config import get_safety_badge

    # Opcion A: Gaming = Verde
    assert theme.GAMING == "#1DB954", f"Gaming debe ser #1DB954 (Opcion A), recibido: {theme.GAMING}"
    assert theme.DANGER == "#c22d2d", f"Danger debe ser #c22d2d, recibido: {theme.DANGER}"

    # Semáforo de seguridad no contiene theme.GAMING
    for cat in ["🟢 Sincronización", "🟡 Launchers Gaming", "🔴 Sistema de Windows"]:
        badge = get_safety_badge(cat)
        assert badge["fg_color"] != theme.GAMING, f"get_safety_badge contamina GAMING en {cat}"
        assert badge["text_color"] != theme.GAMING, f"get_safety_badge contamina GAMING en {cat}"

    print("test_semantic_color_contract OK (contrato semantico respetado: Gaming verde #1DB954, Peligro rojo #c22d2d).")


def test_woptimizer_ico_exists_and_valid():
    """TASK-029 (UI-006): el icono assets/woptimizer.ico existe y es un fichero ICO valido multi-tamano."""
    from PIL import Image

    ico_path = os.path.join(os.path.dirname(__file__), "assets", "woptimizer.ico")
    assert os.path.exists(ico_path), f"El icono {ico_path} no existe en assets/"

    with Image.open(ico_path) as img:
        assert img.format == "ICO", f"Formato de icono invalido: {img.format}"
        w, h = img.size
        assert w >= 16 and h >= 16, f"Dimensiones de icono insuficientes: {w}x{h}"

    print("test_woptimizer_ico_exists_and_valid OK (assets/woptimizer.ico valido y multi-tamano).")


def test_scan_latency_and_lazy_exe_resolution():
    """TASK-033: Optimizacion de latencia y throughput en ProcessService.

    Discriminadores:
      1. get_running_processes() retorna ProcessInfo con exe_path="" (escaneo lazy de 'exe').
      2. get_process_exe_path(os.getpid()) resuelve la ruta absoluta real (sys.executable).
      3. get_process_exe_path() con PID <= 0 o PID inexistente retorna "" fail-safe sin excepcion.
      4. on_add_to_pack en UI resuelve la ruta on-demand con get_process_exe_path cuando exe_path=="".
      5. Benchmark de latencia de escaneo por debajo de 25 ms.
    """
    print("Testing optimizacion de escaneo y resolucion lazy de exe (TASK-033)...")
    import sys
    import time
    from woptimizer.services.process_service import ProcessService, _CAT_ORDER_IDX
    from woptimizer.config import CATEGORY_ORDER
    from woptimizer.models import Pack, ProcessInfo
    from woptimizer.ui.views.process_manager_view import ProcessManagerView

    # Verificacion de indice precomputado
    assert len(_CAT_ORDER_IDX) == len(CATEGORY_ORDER), "Indice de categorias desincronizado"

    ps = ProcessService()

    # 1) Escaneo lazy: todos los procesos vivos se devuelven con exe_path=""
    procs = ps.get_running_processes(force_refresh=True)
    assert len(procs) > 0, "Debe haber al menos un proceso en ejecucion"
    for p in procs:
        assert p.exe_path == "", (
            f"El escaneo masivo no debe resolver exe_path ansiosamente (pid={p.pid}, exe={p.exe_path})"
        )
        assert p.name != "", "El nombre del proceso no debe estar vacio"

    # 2) Resolucion lazy bajo demanda: PID propio debe resolver a sys.executable
    mi_pid = os.getpid()
    mi_exe = ps.get_process_exe_path(mi_pid)
    assert mi_exe != "", "get_process_exe_path(os.getpid()) no debe ser vacio"
    assert os.path.normcase(os.path.realpath(mi_exe)) == os.path.normcase(os.path.realpath(sys.executable)), (
        f"get_process_exe_path({mi_pid}) devolvio {mi_exe!r}, se esperaba {sys.executable!r}"
    )

    # 3) Degradacion fail-safe para PIDs invalidos o inexistentes
    assert ps.get_process_exe_path(-999) == "", "PID negativo debe retornar ''"
    assert ps.get_process_exe_path(0) == "", "PID 0 debe retornar ''"
    assert ps.get_process_exe_path(99999999) == "", "PID inexistente debe retornar ''"

    # 4) Integracion UI: on_add_to_pack resuelve lazy si exe_path esta vacio
    class _CasillaFalsa:
        def __init__(self, v): self.v = v
        def get(self): return self.v

    class _VarFalsa:
        def __init__(self, v): self.v = v
        def get(self): return self.v

    class _LabelFalso:
        def __init__(self): self.textos = []
        def configure(self, **kw):
            if "text" in kw: self.textos.append(kw["text"])

    class _PackServiceMock:
        """Contrato de `PackService`, no su codigo (TASK-062).

        `get_all_packs()` devuelve COPIAS defensivas como el servicio real, y la
        unica via que persiste es `update_pack()`. `save()` se mantiene para
        que un mutant que vuelva a ella muera por la **asercion** y no por un
        `AttributeError`. Las aserciones de abajo leen `ps_mock._packs`, que es
        lo que el servicio retiene de verdad.
        """
        def __init__(self, packs):
            self.packs = packs
            self._packs = packs
            self.saves = 0
            self.actualizados = []
        def get_all_packs(self):
            return {k: p.model_copy(deep=True) for k, p in self._packs.items()}
        def update_pack(self, pack):
            self._packs[pack.id] = pack.model_copy(deep=True)
            self.actualizados.append(pack.id)
            self.saves += 1
        def save(self): self.saves += 1

    pack_destino = Pack(id="test_lazy", name="Pack Lazy")
    vista = ProcessManagerView.__new__(ProcessManagerView)
    vista.process_service = ps
    vista.grouped_processes = {
        "python_self": [ProcessInfo(
            name="python",
            full_name="python.exe",
            pid=mi_pid,
            exe_path="",  # Vacio como viene de get_running_processes
            category="\U0001F7E2 Productividad",
            priority="none",
            description="Interprete"
        )]
    }
    vista.checkboxes = {"python_self": _CasillaFalsa(True)}
    vista.pack_var = _VarFalsa("Pack Lazy")
    vista.status_label = _LabelFalso()
    vista.pack_service = _PackServiceMock({"test_lazy": pack_destino})

    vista.on_add_to_pack()
    # TASK-062: se lee lo que el SERVICIO retiene, no `pack_destino`. La vista
    # mutaba una copia y `pack_destino` --el objeto del test-- nunca cambiaba,
    # asi que estas aserciones pasaba con `save()` en vez de `update_pack()`.
    persistido = vista.pack_service._packs["test_lazy"]
    assert len(persistido.apps) == 1, f"Se esperaba 1 app PERSISTIDA, obtenido {persistido.apps}"
    assert os.path.normcase(os.path.realpath(persistido.apps[0])) == os.path.normcase(os.path.realpath(sys.executable)), (
        f"on_add_to_pack debio resolver la ruta absoluta on-demand y persistirla: {persistido.apps[0]}"
    )

    # 5) Benchmark de rendimiento: latencia < 25 ms
    ps.get_running_processes(force_refresh=True)  # Calentamiento
    tiempos = []
    for _ in range(5):
        t0 = time.perf_counter()
        ps.get_running_processes(force_refresh=True)
        tiempos.append(time.perf_counter() - t0)
    tiempo_min = min(tiempos)
    assert tiempo_min < 0.025, (
        f"Latencia de escaneo excesiva: {tiempo_min*1000:.2f} ms (limite: 25.0 ms)"
    )
    print(f"Optimizacion de escaneo OK (latencia minima: {tiempo_min*1000:.2f} ms).")


def test_models_strict_validation_and_contracts():
    """TASK-034: Validacion estricta y contratos de modelos Pydantic.

    Discriminadores:
      1. Strict booleans: "true", "false", 1, 0, "si" levantan ValidationError
         en Pack.is_favorite y Pack.is_gaming. Controles positivos con bool reales.
      2. Literal default_action: "purgar", "KILL", "", "stop", None levantan
         ValidationError. "start" y "kill" permitidos y validados.
      3. extra='allow': campos adicionales en Pack y AppData sobreviven a la
         construccion y aparecen en model_dump().
      4. Defaults ProcessInfo: exe_path="", category="\u26aa Otros",
         priority="none", description="Sin descripci\u00f3n".
    """
    print("Testing models strict validation and contracts (TASK-034)...")
    from pydantic import ValidationError
    from woptimizer.models import Pack, AppData, ProcessInfo

    # 1. Strict booleans en Pack (is_favorite e is_gaming)
    valores_invalidos = ["true", "false", 1, 0, "si", "no", 1.0]

    for val in valores_invalidos:
        # is_favorite invalido
        try:
            Pack(id="test_fav", name="Test Fav", is_favorite=val)
            assert False, f"Pack no debe aceptar is_favorite={val!r} (debe ser booleano estricto)"
        except ValidationError:
            pass

        # is_gaming invalido
        try:
            Pack(id="test_game", name="Test Game", is_gaming=val)
            assert False, f"Pack no debe aceptar is_gaming={val!r} (debe ser booleano estricto)"
        except ValidationError:
            pass

    # Controles positivos: booleanos reales
    p_fav_true = Pack(id="fav_t", name="Fav True", is_favorite=True, is_gaming=False)
    assert p_fav_true.is_favorite is True
    assert p_fav_true.is_gaming is False

    p_game_true = Pack(id="game_t", name="Game True", is_favorite=False, is_gaming=True)
    assert p_game_true.is_favorite is False
    assert p_game_true.is_gaming is True

    # 2. Literal default_action en Pack
    acciones_invalidas = ["purgar", "KILL", "", "stop", "START", None, 123]
    for acc in acciones_invalidas:
        try:
            Pack(id="test_act", name="Test Act", default_action=acc)
            assert False, f"Pack no debe aceptar default_action={acc!r} (debe ser 'start' o 'kill')"
        except ValidationError:
            pass

    # Controles positivos: 'start' y 'kill'
    p_act_start = Pack(id="act_s", name="Act Start", default_action="start")
    assert p_act_start.default_action == "start"

    p_act_kill = Pack(id="act_k", name="Act Kill", default_action="kill")
    assert p_act_kill.default_action == "kill"

    # 3. extra='allow' en Pack y AppData
    pack_extra = Pack(
        id="pack_ext",
        name="Pack Extra",
        meta_custom="custom_value_123",
        extra_numeric=42,
        tags=["fast", "gaming"]
    )
    dump_pack = pack_extra.model_dump()
    assert "meta_custom" in dump_pack, "meta_custom debe sobrevivir en Pack con extra='allow'"
    assert dump_pack["meta_custom"] == "custom_value_123"
    assert dump_pack.get("extra_numeric") == 42
    assert dump_pack.get("tags") == ["fast", "gaming"]

    appdata_extra = AppData(
        packs={"p1": p_fav_true},
        legacy_profiles={"legacy_p": {}},
        version_custom="2.5.0"
    )
    dump_appdata = appdata_extra.model_dump()
    assert "legacy_profiles" in dump_appdata, "legacy_profiles debe sobrevivir en AppData con extra='allow'"
    assert "version_custom" in dump_appdata, "version_custom debe sobrevivir en AppData con extra='allow'"
    assert dump_appdata["version_custom"] == "2.5.0"

    # 4. Defaults de ProcessInfo
    proc = ProcessInfo(name="notepad", full_name="notepad.exe", pid=9999)
    assert proc.exe_path == "", f"ProcessInfo.exe_path default debe ser '', obtenido {proc.exe_path!r}"
    assert proc.category == "\u26aa Otros", f"ProcessInfo.category default debe ser '\u26aa Otros', obtenido {proc.category!r}"
    assert proc.priority == "none", f"ProcessInfo.priority default debe ser 'none', obtenido {proc.priority!r}"
    assert proc.description == "Sin descripci\u00f3n", f"ProcessInfo.description default debe ser 'Sin descripci\u00f3n', obtenido {proc.description!r}"

    print("test_models_strict_validation_and_contracts OK.")


def test_main_window_navigation_transitions():
    """TASK-034: Ciclo de vida y transiciones de navegacion headless en MainWindow.

    Discriminadores:
      1. Montaje headless con root = ctk.CTk() y root.withdraw().
      2. Persistencia aislada sobre JSON temporal con _pack_service_temporal().
      3. Vista inicial es DashboardView con btn_nav_home activo (ACCENT, border_width=2).
      4. Transicion _show_packs(): destruccion real de vista anterior (not winfo_exists()),
         current_view es PackManagerView, btn_nav_packs activo.
      5. Transicion _show_process_manager(): destruccion de vista anterior, current_view
         es ProcessManagerView, btn_nav_procs activo, bombeo en mainloop hasta poblar
         procesos de forma asincrona.
      6. Transicion _show_home(): retorno limpio a DashboardView y reactivacion de btn_nav_home.
      7. Limpieza garantizada en finally de root.destroy() y eliminacion de JSON temporal.
    """
    print("Testing MainWindow navigation transitions headless (TASK-034)...")
    import customtkinter as ctk
    from woptimizer.services.process_service import ProcessService
    from woptimizer.services.gaming_service import GamingService
    from woptimizer.services.notification_service import NotificationService
    from woptimizer.ui.main_window import MainWindow
    from woptimizer.ui.views.dashboard_view import DashboardView
    from woptimizer.ui.views.pack_manager_view import PackManagerView
    from woptimizer.ui.views.process_manager_view import ProcessManagerView
    from woptimizer.ui import theme

    def _es_activo(btn):
        bc = btn.cget("border_color")
        color_ok = (bc == theme.ACCENT) or (isinstance(bc, (list, tuple)) and theme.ACCENT in bc)
        return color_ok and btn.cget("border_width") == 2

    def _es_inactivo(btn):
        bc = btn.cget("border_color")
        color_ok = (bc == theme.BORDER) or (isinstance(bc, (list, tuple)) and theme.BORDER in bc)
        return color_ok and btn.cget("border_width") == 1

    pack_s, tmp_path = _pack_service_temporal()
    root = ctk.CTk()
    root.withdraw()

    errores = []
    try:
        ps = ProcessService()
        gs = GamingService(ps, pack_s)
        ns = NotificationService()

        win = MainWindow(root, ps, pack_s, gs, ns)
        win.pack(fill="both", expand=True)

        def paso1():
            try:
                # 1. Estado inicial: DashboardView y btn_nav_home activo
                assert isinstance(win.current_view, DashboardView), (
                    f"Vista inicial esperada DashboardView, obtenido: {type(win.current_view).__name__}"
                )
                assert _es_activo(win.btn_nav_home), "btn_nav_home debe estar activo en la vista inicial"
                assert _es_inactivo(win.btn_nav_packs), "btn_nav_packs debe estar inactivo en la vista inicial"
                assert _es_inactivo(win.btn_nav_procs), "btn_nav_procs debe estar inactivo en la vista inicial"

                # 2. Navegacion a Packs: _show_packs()
                vista_home = win.current_view
                win._show_packs()
                assert not vista_home.winfo_exists(), "La vista DashboardView previa debe destruirse al navegar a Packs"
                assert isinstance(win.current_view, PackManagerView), (
                    f"Vista actual esperada PackManagerView, obtenido: {type(win.current_view).__name__}"
                )
                assert _es_activo(win.btn_nav_packs), "btn_nav_packs debe estar activo al mostrar Packs"
                assert _es_inactivo(win.btn_nav_home), "btn_nav_home debe quedar inactivo"
                assert _es_inactivo(win.btn_nav_procs), "btn_nav_procs debe quedar inactivo"

                # 3. Navegacion a Process Manager: _show_process_manager()
                vista_packs = win.current_view
                win._show_process_manager()
                assert not vista_packs.winfo_exists(), "La vista PackManagerView previa debe destruirse al navegar a Procesos"
                assert isinstance(win.current_view, ProcessManagerView), (
                    f"Vista actual esperada ProcessManagerView, obtenido: {type(win.current_view).__name__}"
                )
                assert _es_activo(win.btn_nav_procs), "btn_nav_procs debe estar activo al mostrar Procesos"
                assert _es_inactivo(win.btn_nav_home), "btn_nav_home debe quedar inactivo"
                assert _es_inactivo(win.btn_nav_packs), "btn_nav_packs debe quedar inactivo"

                # Esperar en mainloop a que el hilo secundario pueble los procesos
                root.after(350, paso2)
            except Exception as e:
                errores.append(e)
                try:
                    root.quit()
                    root.destroy()
                except Exception:
                    pass

        def paso2():
            try:
                assert len(win.current_view.processes) > 0, "ProcessManagerView debe haber cargado al menos un proceso vivo"

                # 4. Retorno a Home: _show_home()
                vista_procs = win.current_view
                win._show_home()
                assert not vista_procs.winfo_exists(), "La vista ProcessManagerView previa debe destruirse al retornar a Home"
                assert isinstance(win.current_view, DashboardView), (
                    f"Vista actual esperada DashboardView tras retorno, obtenido: {type(win.current_view).__name__}"
                )
                assert _es_activo(win.btn_nav_home), "btn_nav_home debe estar activo al retornar a Home"
                assert _es_inactivo(win.btn_nav_packs), "btn_nav_packs debe quedar inactivo"
                assert _es_inactivo(win.btn_nav_procs), "btn_nav_procs debe quedar inactivo"
            except Exception as e:
                errores.append(e)
            finally:
                try:
                    root.quit()
                    root.destroy()
                except Exception:
                    pass

        root.after(50, paso1)
        root.mainloop()

        if errores:
            raise errores[0]

    finally:
        try:
            root.quit()
            root.destroy()
        except Exception:
            pass
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    print("test_main_window_navigation_transitions OK.")


def test_los_workers_de_pack_solo_publican_por_after():
    """TASK-035 / cierre del ciclo 26 (S2, S3): el hilo secundario solo PUBLICA.

    El `mutation-auditor` del ciclo 26 dio FAIL a la guarda anterior y con razon:
    era una lista de 3-4 nombres de metodo, asi que un
    `self.status_label.configure(...)` desde el worker pasaba la suite, y con
    `self.master.after` en UNA sola de las dos ramas del worker Tambien (el guard
    solo miraba los `self.after` que encontraba y con dos ramas bastaba una
    valida). El doc de `ui-design-system.md` afirmaba que el analisis era
    "estricto" y no lo era: la afirmacion tambien era falsa.

    Aqui la lista de lo permitido son PARES `(raiz, metodo)` y todo lo demas que
    cuelgue de `self` es infraccion, incluidos los metodos de widget que nadie
    escribio en la lista y las ESCRITURAS en `self.<attr>`. Se aplica al
    **objetivo real** de cada `threading.Thread(target=...)` de `execute_pack`,
    `kill_pack`, `start_pack`, `ProcessManagerView._do_load` y
    `ProcessManagerView.on_kill_selected`, y exige que CADA `self.after` del
    worker lleve 0 ms y un callback de la lista blanca, no solo el primero.

    LO QUE LA GUARDA CUBRE, DICHO CON SUS LIMITES (iter 4, correccion de una
    promesa que era falsa): toda llamada o escritura que se resuelva sobre `self`
    por `Attribute`, por `Subscript`, por `getattr`/`setattr`/`delattr`, por
    `del`, o **pasada como argumento** de una llamada permitida.

    LO QUE LA GUARDA **NO** CUBRE, dicho sin adornos:

    * los `threading.Thread` de `ui/app.py` (el toast de arranque y el hilo del
      icono de la bandeja), que no son vistas, y ningun worker anadido despues de
      esta lista sin anadirlo aqui (la lista de vistas y metodos esta en el
      bucle de aplicacion, mas abajo, a la vista de todos);
    * un **alias local**: `lbl = self.status_label` y luego `lbl.configure(...)`
      no se resuelve hasta `self` y la guarda no lo ve. Es el agujero que queda
      abierto, y no lo cierra un analisis estatico de este tipo;
    * que el `after` se ejecute de verdad en el hilo principal, ni el resultado
      de la operacion. Eso lo cubren las sondas con hilo secundario real.

    **La guarda se prueba contra si misma** (control del detector, no del
    fichero): ocho infracciones sinteticas que tiene que ver —un metodo de
    widget, `self.master.after`, una escritura en `self`, un `del self.<attr>`,
    `getattr`/`setattr` sobre la vista, `self.<attr>` como argumento de una
    llamada permitida, tres metodos prohibidos de raices permitidas y dos de la
    puerta de atras por `__dict__`—, un worker conforme que no puede marcar, y
    el caso de las DOS ramas, donde el worker tiene una rama buena y otra con
    `self.master.after`: ese es precisamente el agujero que el guard per-nodo no
    veia.
    """
    print("Testing that pack workers only publish via self.after (TASK-035 / cycle 26)...")

    # =================================================================
    # 0. EL DETECTOR CONTRA SI MISMO (S2, S3)
    # =================================================================
    # Lo unico que un worker puede hacer con la vista es PUBLICAR por
    # `self.after(0, ...)`. Lo demas (tocar widgets, escribir en `self`) esta
    # prohibido, y la lista de lo permitido es CORTA A PROPOSITO: cualquier
    # llamada nueva sobre `self` tiene que pasar por esta lista para no ser una
    # infraccion silenciosa.
    #
    # TASK-035 iter 3: la lista es de PARES `(raiz, metodo)`, no de raices. Con
    # raices, `self.pack_service.get_all_packs()` y
    # `self.process_service.get_process_exe_path(1)` colaban: la raiz estaba
    # permitida y el metodo, no. Comparar el par cierra esa puerta y hace que la
    # lista signifique algo.
    PERMITIDOS = {
        ("process_service", "kill_pack_apps"),
        ("process_service", "kill_processes"),
        ("process_service", "start_pack_apps"),
        ("process_service", "get_running_processes"),
        ("gaming_service", "execute_gaming_pack"),
        ("notification_service", "notify_pack_activated"),
        ("notification_service", "notify_kill_result"),
        ("notification_service", "notify_apps_launched"),
    }
    # `_show_kill_banner` salio de aqui porque era un alias MUERTO de
    # `_show_banner` (mismo patron que perdio el ciclo 22): nadie lo llamaba y lo
    # unico que lo sostenia era su propia presencia en esta lista.
    CALLBACKS = {"_inline_status", "_show_banner", "_show_start_banner",
                 "_publicar_cierre", "_apply_load"}

    #: Accesos a la vista que NO son ni `Attribute` ni `Subscript`. Con esta
    #: lista, `getattr(self, 'status_label').configure(...)` y
    #: `setattr(self, '_last_gaming_summary', 'x')` dejan de llevarse el widget
    #: entero por la puerta de atras. Medido en la iteracion 4 del ciclo 26: la
    #: guarda era una RED, no un muro, y por tres agujeros.
    ACCESOS_DINAMICOS = {"getattr", "setattr", "delattr"}

    def _raiz_de_self(expresion):
        """`(raiz, camino)` de una expresion que cuelga de `self`; `(None, [])` si no.

        `camino` va de la raiz al metodo llamado: `self.after` ->
        `("after", ["after"])`; `self.status_label.configure` ->
        `("status_label", ["status_label", "configure"])`; `self.master.after` ->
        `("master", ["master", "after"])`.

        TASK-035 iter 3: baja tambien por `ast.Subscript`. Antes,
        `self.__dict__['status_label'].configure(...)` devolvia `(None, [])` y la
        guarda no lo veia: un `Subscript` no es un `Attribute`. Era la misma
        llamada de widget de siempre, escrita por la puerta de atras.

        TASK-035 iter 4: y por `getattr`/`setattr`/`delattr`, que no son ninguno
        de los dos. `getattr(self, 'status_label').configure(...)` es la MISMA
        llamada de widget de siempre, con el `Attribute` partido en dos.
        """
        ruta = []
        acceso_directo = False
        nodo = expresion
        while True:
            if isinstance(nodo, ast.Attribute):
                ruta.append(nodo.attr)
                nodo = nodo.value
            elif isinstance(nodo, ast.Subscript):
                nodo = nodo.value
            elif (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)
                    and nodo.func.id in ACCESOS_DINAMICOS and nodo.args
                    and isinstance(nodo.args[0], ast.Name) and nodo.args[0].id == "self"):
                ruta.append(nodo.func.id)
                acceso_directo = True
                break
            else:
                break
        if acceso_directo or (ruta and isinstance(nodo, ast.Name) and nodo.id == "self"):
            return ruta[-1], list(reversed(ruta))
        return None, []

    def _infracciones(worker, etiqueta):
        """Todas las violaciones del invariante en UN worker. Lista vacia = conforme."""
        malos = []
        for call in [n for n in ast.walk(worker) if isinstance(n, ast.Call)]:
            # Un `getattr`/`setattr`/`delattr` SOBRE `self` es un acceso entero a
            # la vista. Se marca aqui porque `_raiz_de_self` solo lo veria cuando
            # cuelga de un `Attribute` (`getattr(self, 'x').y`), no cuando la
            # llamada es el nodo mas externo (`setattr(self, 'x', 1)`).
            if (isinstance(call.func, ast.Name) and call.func.id in ACCESOS_DINAMICOS
                    and call.args and isinstance(call.args[0], ast.Name)
                    and call.args[0].id == "self"):
                malos.append(
                    f"{etiqueta}:L{call.lineno} {call.func.id}(self, ...) "
                    f"desde el hilo secundario"
                )
                continue
            raiz, camino = _raiz_de_self(call.func)
            if raiz is None:
                continue
            if raiz != "after":
                if (raiz, camino[-1]) in PERMITIDOS:
                    # `self` como ARGUMENTO de una llamada permitida tambien es
                    # tocar la vista: el widget no se escribe aqui, pero se saca
                    # de la vista para que otro lo escriba.
                    for arg in list(call.args) + [kw.value for kw in call.keywords]:
                        a_raiz, a_camino = _raiz_de_self(arg)
                        if a_raiz is not None:
                            malos.append(
                                f"{etiqueta}:L{call.lineno} pasa "
                                f"self.{'.'.join(a_camino)} como argumento de "
                                f"una llamada permitida"
                            )
                    continue
                malos.append(
                    f"{etiqueta}:L{call.lineno} self.{'.'.join(camino)}(...) "
                    f"desde el hilo secundario"
                )
                continue
            if not call.args or not (isinstance(call.args[0], ast.Constant) and call.args[0].value == 0):
                malos.append(f"{etiqueta}:L{call.lineno} self.after debe ser de 0 ms")
            elif (len(call.args) < 2 or not isinstance(call.args[1], ast.Attribute)
                    or call.args[1].attr not in CALLBACKS):
                malos.append(f"{etiqueta}:L{call.lineno} self.after debe publicar en {sorted(CALLBACKS)}")
        for nodo in ast.walk(worker):
            if isinstance(nodo, ast.Assign):
                objetivos = nodo.targets
            elif isinstance(nodo, (ast.AugAssign, ast.AnnAssign)):
                objetivos = [nodo.target]
            elif isinstance(nodo, ast.Delete):
                # `del self._last_gaming_summary` es tan destructivo como
                # `self._last_gaming_summary = ...`, y la guarda solo miraba
                # escrituras: `ast.Delete` no es `ast.Assign`.
                objetivos = nodo.targets
            else:
                objetivos = []
            for t in objetivos:
                if isinstance(t, (ast.Attribute, ast.Subscript)):
                    raiz, camino = _raiz_de_self(t)
                    if raiz is not None:
                        malos.append(
                            f"{etiqueta}:L{nodo.lineno} escribe "
                            f"self.{'.'.join(camino)} desde el hilo secundario"
                        )
        return malos

    # Control 1: las tres infracciones que la guarda VIEJA no veia.
    codigo_malo = (
        "def _run(self):\n"
        "    self.status_label.configure(text='x')\n"
        "    self.master.after(0, self._show_banner, 1)\n"
        "    self._last_gaming_summary = 'x'\n"
    )
    malos = _infracciones(ast.parse(codigo_malo).body[0], "CONTROL")
    assert len(malos) == 3, f"el detector no ve las tres infracciones de control: {malos}"
    assert any("status_label" in m for m in malos), f"no ve un metodo de widget: {malos}"
    assert any("master" in m for m in malos), f"no ve self.master.after: {malos}"
    assert any("escribe" in m for m in malos), f"no ve una escritura en self: {malos}"

    # Control 2: el worker CONFORME no puede marcar nada (si no, el guard no guardaba nada).
    codigo_bueno = (
        "def _run(self):\n"
        "    killed, failed, skipped, freed = self.process_service.kill_pack_apps([])\n"
        "    texto, color = mensaje_cierre_pack('X', killed, failed, skipped, freed)\n"
        "    self.after(0, self._inline_status, texto, color)\n"
        "    self.notification_service.notify_pack_activated('X', killed, freed)\n"
    )
    assert _infracciones(ast.parse(codigo_bueno).body[0], "CONTROL") == [], (
        "el detector marca de mas: un worker que solo publica por self.after(0, ...) es conforme"
    )

    # Control 3 (S3): con la guarda VIEJA (per-nodo) este worker pasaba. La
    # rama buena no absuelve la rama mala.
    codigo_dos_ramas = (
        "def _run(self):\n"
        "    if algo:\n"
        "        self.after(0, self._show_banner, 1)\n"
        "    else:\n"
        "        self.master.after(0, self._show_banner, 1)\n"
        "        self.after(60000, self._hide_banner)\n"
    )
    malos_ramas = _infracciones(ast.parse(codigo_dos_ramas).body[0], "CONTROL-RAMAS")
    assert len(malos_ramas) == 2, (
        f"la guarda tiene que afirmar sobre TODAS las ramas del worker, no sobre la "
        f"primera que encuentra: {malos_ramas}"
    )

    # Control 4 (iter 3): con la lista de RAICES, estas cuatro llamadas pasaban
    # enteras. Se comparan por pares: la misma raiz puede estar permitida con un
    # metodo y prohibida con otro.
    codigo_pares = (
        "def _run(self):\n"
        "    self.process_service.kill_pack_apps([])\n"
        "    self.process_service.get_process_exe_path(1)\n"
        "    self.pack_service.get_all_packs()\n"
        "    self.gaming_service.should_kill_for_gaming('x', None)\n"
    )
    malos_pares = _infracciones(ast.parse(codigo_pares).body[0], "CONTROL-PARES")
    assert len(malos_pares) == 3, (
        "la guarda tiene que comparar el PAR (raiz, metodo): con la raiz sola, "
        f"pack_service, get_process_exe_path y should_kill_for_gaming colaban: {malos_pares}"
    )
    for prohibido in ("get_process_exe_path", "get_all_packs", "should_kill_for_gaming"):
        assert any(prohibido in m for m in malos_pares), (
            f"la guarda no ve self.<raiz>.{prohibido}: {malos_pares}"
        )
    assert not any("kill_pack_apps" in m for m in malos_pares), (
        "el metodo SI permitido de una raiz permitida no puede marcarse: solo mira al par"
    )

    # Control 5 (iter 3): `self.__dict__['status_label'].configure(...)` es la misma
    # llamada de widget escrita con un `Subscript` por medio, y antes colaba porque
    # un Subscript no es un Attribute. Tambien la escritura por indice.
    codigo_subscript = (
        "def _run(self):\n"
        "    self.__dict__['status_label'].configure(text='x')\n"
        "    self.__dict__['_last_gaming_summary'] = 'x'\n"
    )
    malos_sub = _infracciones(ast.parse(codigo_subscript).body[0], "CONTROL-SUBSCRIPT")
    assert len(malos_sub) == 2, (
        f"la guarda no baja por ast.Subscript y se la esquivan por el indice: {malos_sub}"
    )
    assert any("__dict__" in m and "configure" in m for m in malos_sub), (
        f"no ve la llamada por indice: {malos_sub}"
    )
    assert any("__dict__" in m and "escribe" in m for m in malos_sub), (
        f"no ve la escritura por indice: {malos_sub}"
    )

    # Control 6 (iter 4): `getattr`/`setattr` sobre `self`. La guarda bajaba por
    # `Attribute` y por `Subscript`, pero `getattr(self, 'x')` no es ninguno de
    # los dos, asi que el widget se pasaba entero por la puerta de atras. Se
    # cuentan DOS infracciones en la primera linea: la llamada de widget
    # (`...configure`) y el `getattr` por si mismo, que ya ES un acceso a la
    # vista aunque nadie lo encadene con nada.
    codigo_getattr = (
        "def _run(self):\n"
        "    getattr(self, 'status_label').configure(text='x')\n"
        "    setattr(self, '_last_gaming_summary', 'x')\n"
    )
    malos_getattr = _infracciones(ast.parse(codigo_getattr).body[0], "CONTROL-GETATTR")
    assert len(malos_getattr) == 3, (
        f"la guarda no ve los accesos dinamicos a la vista: {malos_getattr}"
    )
    assert any("getattr" in m and "configure" in m for m in malos_getattr), (
        f"no ve getattr(self, 'widget').metodo(...): {malos_getattr}"
    )
    assert any("setattr(self, ...)" in m for m in malos_getattr), (
        f"no ve setattr(self, 'attr', ...): {malos_getattr}"
    )

    # Control 7 (iter 4): `del self.<attr>` es una escritura destructiva y la
    # guarda no miraba `ast.Delete`, solo `ast.Assign`.
    codigo_del = (
        "def _run(self):\n"
        "    del self._last_gaming_summary\n"
        "    del self.__dict__['status_label']\n"
    )
    malos_del = _infracciones(ast.parse(codigo_del).body[0], "CONTROL-DEL")
    assert len(malos_del) == 2, (
        f"la guarda no ve los `del` sobre la vista: {malos_del}"
    )
    assert any("_last_gaming_summary" in m for m in malos_del), (
        f"no ve del self._last_gaming_summary: {malos_del}"
    )
    assert any("__dict__" in m for m in malos_del), (
        f"no ve del self.__dict__['x']: {malos_del}"
    )

    # Control 8 (iter 4): el `self` que NO se escribe tambien cuenta cuando se
    # entrega a una llamada permitida. Antes solo se miraba `call.func`.
    codigo_argumento = (
        "def _run(self):\n"
        "    self.process_service.kill_pack_apps(self.status_label)\n"
        "    self.notification_service.notify_pack_activated('X', self.killed, 0.0)\n"
        "    self.process_service.kill_pack_apps(p.apps)\n"
    )
    malos_arg = _infracciones(ast.parse(codigo_argumento).body[0], "CONTROL-ARGUMENTO")
    assert len(malos_arg) == 2, (
        f"la guarda no ve self.<attr> como ARGUMENTO de una llamada permitida: {malos_arg}"
    )
    assert any("status_label" in m for m in malos_arg), (
        f"no ve el widget pasado como argumento: {malos_arg}"
    )
    assert not any("p.apps" in m for m in malos_arg), (
        f"un argumento que NO cuelga de self no puede marcarse: {malos_arg}"
    )

    # -----------------------------------------------------------------
    # 1. La guarda aplicada al codigo real
    # -----------------------------------------------------------------
    raiz_repo = os.path.dirname(os.path.abspath(__file__))

    def _arbol_de(nombre_fichero):
        with open(os.path.join(raiz_repo, "src", "woptimizer", "ui", "views", nombre_fichero),
                  "r", encoding="utf-8") as fh:
            return ast.parse(fh.read(), nombre_fichero)

    def _metodo(arbol, clase, nombre):
        for node in ast.walk(arbol):
            if isinstance(node, ast.ClassDef) and node.name == clase:
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == nombre:
                        return item
        return None

    def _anidados(metodo):
        """Los `def` anidados del metodo, a cualquier profundidad de bloques.

        No se baja dentro de uno encontrado: un `def` dentro del worker es cosa
        suya, no un worker de la vista.
        """
        encontrados = {}

        def _bajar(bloque):
            for item in bloque:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    encontrados.setdefault(item.name, item)
                    continue
                for hijo in ast.iter_child_nodes(item):
                    if isinstance(hijo, ast.stmt):
                        _bajar([hijo])

        _bajar(metodo.body)
        return encontrados

    def _workers(metodo, etiqueta):
        """Los workers REALES: los `def` que se pasan a `threading.Thread(target=...)`."""
        anidados = _anidados(metodo)
        nombres = []
        for node in ast.walk(metodo):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "Thread"):
                for kw in node.keywords:
                    if kw.arg == "target" and isinstance(kw.value, ast.Name):
                        nombres.append(kw.value.id)
        assert nombres, f"{etiqueta} no lanza ningun threading.Thread: no hay worker que guardar"
        workers = []
        for nombre in nombres:
            assert nombre in anidados, f"{etiqueta} pasa {nombre!r} a Thread y no es un def anidado"
            workers.append(anidados[nombre])
        return workers

    arbol_dash = _arbol_de("dashboard_view.py")
    arbol_pm = _arbol_de("pack_manager_view.py")
    arbol_proc = _arbol_de("process_manager_view.py")

    exec_pack = _metodo(arbol_dash, "DashboardView", "execute_pack")
    assert exec_pack is not None, "DashboardView.execute_pack no encontrado"
    kill_pack = _metodo(arbol_pm, "PackManagerView", "kill_pack")
    start_pack = _metodo(arbol_pm, "PackManagerView", "start_pack")
    assert kill_pack is not None, "PackManagerView.kill_pack no encontrado"
    assert start_pack is not None, "PackManagerView.start_pack no encontrado"

    # Iter 3: el Gestor de Procesos tambien lanza `threading.Thread` y hasta aqui
    # no lo leia nadie. `_do_load` es el worker de carga de la lista y
    # `on_kill_selected` es la TERCERA puerta de cierre (la que mata uno a uno lo
    # que el usuario marco a mano). Los dos entran en el mismo invariante.
    do_load = _metodo(arbol_proc, "ProcessManagerView", "_do_load")
    on_kill = _metodo(arbol_proc, "ProcessManagerView", "on_kill_selected")
    assert do_load is not None, "ProcessManagerView._do_load no encontrado"
    assert on_kill is not None, "ProcessManagerView.on_kill_selected no encontrado"

    for metodo, etiqueta in ((exec_pack, "DashboardView.execute_pack"),
                             (kill_pack, "PackManagerView.kill_pack"),
                             (start_pack, "PackManagerView.start_pack"),
                             (do_load, "ProcessManagerView._do_load"),
                             (on_kill, "ProcessManagerView.on_kill_selected")):
        for worker in _workers(metodo, etiqueta):
            infracciones = _infracciones(worker, etiqueta)
            assert not infracciones, (
                "el worker toca la vista fuera de self.after(0, ...): " + "; ".join(infracciones)
            )
            publica = [n for n in ast.walk(worker) if isinstance(n, ast.Call)
                       and isinstance(n.func, ast.Attribute) and n.func.attr == "after"
                       and isinstance(n.func.value, ast.Name) and n.func.value.id == "self"]
            assert publica, f"{etiqueta}: el worker no publica nada por self.after(0, ...)"

    print("test_los_workers_de_pack_solo_publican_por_after OK (guarda AST exhaustiva).")


def test_el_feedback_de_pack_dice_la_verdad():
    """TASK-035 / cierre del ciclo 26 (S1, S4, S5, S9): el feedback no miente.

    El `mutation-auditor` del ciclo 26 demostro en RUNTIME que `kill_pack`
    pintaba `"<tick> 0 procesos cerrados (0.0 MB liberados)"` en VERDE Gaming
    aunque no hubiera cerrado NADA (todo en `keepers`, pack vacio, rutas
    muertas). Es la misma clase que el contador `started` del ciclo 20: la UI
    miente en verde. El arreglo es `ui/feedback.py` (texto y color por resultado
    real) y esta sonda afirma sobre **el texto y el color que produjo el codigo**
    en los cuatro desenlaces y en las **dos** puertas de cierre.

    Que esta sonda llame al CODIGO y no a si misma es el punto (S9): antes
    hacia `pm._inline_status("...literal...", VERDE)` y comprobaba que el label
    mostrara ese literal, que es afirmar que el codigo hace lo que el codigo
    acaba de escribir (100% cobertura, 0 verificacion). Ahora entra
    `kill_pack`/`start_pack`/`execute_pack` de verdad, con doble pulsacion, con
    hilo secundario real, y el test hace de bucle de eventos: aplica en el hilo
    principal lo que el secundario encolo por `self.after(0, ...)`.

    Ademas mide lo que las aserciones viejas no miraban:

      * la **barra de reposo** se afirma sobre su TEXTO con un doble cuyo
        snapshot cambia entre llamadas, no sobre el timestamp de cache (que solo
        delata el efecto colateral de `invalidate_cache`);
      * los **temporizadores** se miden con un reloj SIMULADO y no con 5,5 s de
        espera real: t0 primer banner, t=1000 segundo banner, lectura a t=5500
        (el temporizador viejo, sin cancelar, apagaria aqui el banner del
        SEGUNDO mensaje) y auto-ocultado a t=6500 (si desaparece o se va a 60 s,
        salta).
    """
    print("Testing honest pack execution feedback (TASK-035 / cycle 26)...")
    import collections
    import customtkinter as ctk
    from woptimizer.models import Pack
    from woptimizer.services.process_service import ProcessService
    from woptimizer.services.gaming_service import GamingService
    from woptimizer.services.notification_service import NotificationService
    from woptimizer.ui.views import dashboard_view as dash_mod
    from woptimizer.ui.views import pack_manager_view as pmv_mod
    from woptimizer.ui.views.dashboard_view import DashboardView
    from woptimizer.ui.views.pack_manager_view import PackManagerView
    from woptimizer.ui.confirmation import (
        AMBAR, CANCEL, MSG_PACK_INEXISTENTE, ROJO, VERDE, VENTANA_MS, VENTANA_MS_PORTADA,
    )
    from woptimizer.ui import theme

    # -----------------------------------------------------------------
    # 0. ESTATICO Y PRIMERO (TASK-036 iter 7, c-bis): EL CONTRATO DE LOS
    # LLAMANTES. "Quien llama pasa la ACCION, nunca el verbo" es lo que
    # promete el docstring de `_verbo`, y hasta ahora no lo comprobaba NADIE:
    # con `VERBOS.get(accion, VERBOS["kill"])` un verbo cableado en el sitio
    # de la accion caia en silencio a "apagar", que es la respuesta correcta
    # de la puerta de apagar, asi que era invisible.
    #
    # Va PRIMERO y sin Tk por la regla de `testing-guide.md` ("las
    # comprobaciones estaticas van primero, sin Tk, para que una regresion
    # falle en milisegundos con un mensaje legible"): si un llamante cablea un
    # verbo, esto muere nombrando fichero y linea, en vez de dejar que el
    # `KeyError` de `_verbo` reviente mas abajo con un traceback sin contexto.
    # -----------------------------------------------------------------
    import ast as _ast
    from woptimizer.ui import feedback as fb
    acciones_validas = set(fb.VERBOS)
    verbos_del_mapa = set(fb.VERBOS.values())
    assert not (acciones_validas & verbos_del_mapa), (
        "una palabra no puede ser ACCION y verbo a la vez en el mapa de "
        f"`VERBOS`: {acciones_validas & verbos_del_mapa}"
    )
    # El alcance lo DERIVA `_modulos_que_importan_feedback` recorriendo
    # `src/woptimizer/**` con `ast` (TASK-037, ciclo 27). Antes era una tupla
    # literal de dos ficheros, que era una apuesta sobre que ficheros importan
    # `feedback` y la apuesta tenia un fichero mal: `process_manager_view.py`
    # tambien importa. Ver `test_el_alcance_del_guard_de_llamantes_se_deriva_del_arbol`.
    _guardar_contrato_de_llamantes(_raiz_del_paquete(), acciones_validas)

    # -----------------------------------------------------------------
    # 2. Arneses sin Tk para la parte dinamica
    # -----------------------------------------------------------------
    class _Reloj:
        """Doble de `TkScheduler` con reloj ABSOLUTO.

        `_FakeScheduler` dispara por `delay <= elapsed`, que no ordena el reloj:
        el temporizador viejo (5000) y el nuevo (5000) vencerian los dos en el
        mismo `fire_due(5000)` y el bug no se veria. Aqui cada job tiene un
        plazo absoluto, que es lo que reproduce el fallo medido por el auditor
        (t0 primer banner, t=1000 segundo banner, lectura a t=5500).
        """

        def __init__(self):
            self.jobs = []
            self.ahora = 0
            self._contador = 0

        def schedule(self, delay_ms, callback):
            self._contador += 1
            handle = f"job{self._contador}"
            self.jobs.append({"id": handle, "vence": self.ahora + delay_ms, "cb": callback, "vivo": True})
            return handle

        def cancel(self, handle):
            for job in self.jobs:
                if job["id"] == handle:
                    job["vivo"] = False
                    return
            raise AssertionError(f"Se cancelo un handle que no existe: {handle!r}")

        def vivos(self):
            return [j for j in self.jobs if j["vivo"]]

        def avanzar(self, ms):
            self.ahora += ms
            vencidos = [j for j in self.jobs if j["vivo"] and j["vence"] <= self.ahora]
            for job in vencidos:
                job["vivo"] = False
            for job in vencidos:
                job["cb"]()
            return [j["id"] for j in vencidos]

    class _ProcesosConReloj:
        """Doble de `ProcessService` para la vista: snapshot cambiante + contadores."""

        def __init__(self, cuantos):
            self.snapshot = [object() for _ in range(cuantos)]
            self.invalidadas = 0
            self.lecturas = 0

        def get_running_processes(self):
            self.lecturas += 1
            return list(self.snapshot)

        def invalidate_cache(self):
            self.invalidadas += 1

    class _Label:
        """Doble de `status_label`: graba lo que la vista escribe, con su color."""

        def __init__(self):
            self.escrituras = []

        def winfo_exists(self):
            return 1

        def configure(self, **kw):
            self.escrituras.append((kw.get("text"), kw.get("text_color")))

        @property
        def texto(self):
            return self.escrituras[-1][0] if self.escrituras else None

        @property
        def color(self):
            return self.escrituras[-1][1] if self.escrituras else None

    class _ProcesosGestor:
        def __init__(self):
            self.cierre = (0, 0, 0, 0.0)
            self.arranque = (0, 0)
            self.llamadas_cierre = 0
            self.llamadas_arranque = 0
            self.invalidadas = 0
            self.apps = None

        def kill_pack_apps(self, apps):
            self.llamadas_cierre += 1
            self.apps = list(apps)
            return self.cierre

        def start_pack_apps(self, apps):
            self.llamadas_arranque += 1
            self.apps = list(apps)
            return self.arranque

        def invalidate_cache(self):
            self.invalidadas += 1

        def get_running_processes(self):
            # La barra de reposo de la portada lo pide; con lista vacia la
            # telemetria dice 0, que es lo que se espera en el arnés.
            return []

    class _GamingGestor:
        def __init__(self):
            self.cierre = (0, 0, 0, 0.0)
            self.llamadas = 0
            self._last_closed_apps = []

        def execute_gaming_pack(self, pack):
            self.llamadas += 1
            return self.cierre

        def get_last_closed_apps(self):
            return list(self._last_closed_apps)

        def clear_last_closed_apps(self):
            self._last_closed_apps = []

        def restore_gaming_session(self):
            return 0, 0

    class _Notis:
        def __init__(self):
            self.eventos = []

        def notify_pack_activated(self, nombre, killed, freed_mb):
            self.eventos.append(("kill", nombre, killed, freed_mb))

        def notify_apps_launched(self, nombre, started, failed):
            self.eventos.append(("start", nombre, started, failed))

    class _Packs:
        def __init__(self, pack):
            self.pack = pack

        def get_all_packs(self):
            return {self.pack.id: self.pack}

    # -----------------------------------------------------------------
    # 3. Parte dinamica CON ventana real (DashboardView + guarda preventiva)
    # -----------------------------------------------------------------
    pack_s, tmp_path = _pack_service_temporal()
    root = ctk.CTk()
    root.withdraw()
    try:
        ps = ProcessService()
        gs = GamingService(ps, pack_s)
        ns = NotificationService()

        dash = DashboardView(root, ps, pack_s, ns, gs)
        dash.pack()

        # --- S4: la barra de reposo se refresca DE VERDAD, no por efecto colateral
        reloj_procesos = _ProcesosConReloj(3)
        dash.process_service = reloj_procesos
        dash._update_resting_bar()
        antes = dash.resting_label.cget("text")
        assert "3 procesos activos" in antes, f"precondicion del arnes: {antes!r}"
        reloj_procesos.snapshot = [object()]        # el mundo cambio entre llamadas
        reloj_procesos.invalidadas = 0
        dash._show_start_banner(launched=3, failed=0, pack_name="Trabajo")
        assert reloj_procesos.invalidadas == 1, (
            f"_show_start_banner debe invalidar la cache una vez, no "
            f"{reloj_procesos.invalidadas}"
        )
        despues = dash.resting_label.cget("text")
        assert "1 procesos activos" in despues, (
            "la barra de reposo no se refresco: sigue mostrando el snapshot viejo "
            f"(antes={antes!r}, despues={despues!r})"
        )
        assert despues != antes, "el texto de la barra de reposo no cambio"
        assert dash.status_label.cget("text") == "🚀 Pack 'Trabajo' iniciado (3 apps).", (
            f"texto del banner de arranque: {dash.status_label.cget('text')!r}"
        )
        assert dash.status_label.cget("text_color") == theme.ACCENT
        assert dash.lbl_banner.cget("text") == dash.status_label.cget("text")

        dash._show_start_banner(launched=2, failed=1, pack_name="Herramientas")
        assert dash.status_label.cget("text") == (
            "⚠️ Pack 'Herramientas': 2 apps iniciadas, 1 fallaron."
        ), f"texto del banner con fallos: {dash.status_label.cget('text')!r}"
        assert dash.status_label.cget("text_color") == theme.WARNING

        # --- el banner de cierre tampoco puede mentir con 0 cerrados (S1, misma clase)
        dash._show_banner(killed=4, freed_mb=128.5, is_gaming=False)
        assert dash.status_label.cget("text") == "⚡ 4 procesos cerrados · 128.5 MB liberados", (
            f"exito real del banner: {dash.status_label.cget('text')!r}"
        )
        assert dash.status_label.cget("text_color") == theme.ACCENT

        # (iter 3) `_show_banner` tambien refresca la barra de reposo. Sin esta
        # afirmacion, borrar su `_update_resting_bar()` dejaba la suite en verde.
        reloj_procesos.snapshot = [object(), object()]
        antes_reposo = dash.resting_label.cget("text")
        dash._show_banner(killed=4, freed_mb=128.5, is_gaming=False)
        assert "2 procesos activos" in dash.resting_label.cget("text"), (
            "_show_banner tiene que refrescar la barra de reposo: antes "
            f"{antes_reposo!r}, despues {dash.resting_label.cget('text')!r}"
        )

        dash._show_banner(killed=6, freed_mb=256.0, is_gaming=True)
        assert dash.status_label.cget("text") == "⚡ 6 procesos cerrados · 256.0 MB liberados"
        assert dash.status_label.cget("text_color") == theme.GAMING
        # (iter 3) El resumen del Gaming Mode se escribe EN EL TEXTO de reposo, no
        # en un atributo que nadie lee. Sin esta afirmacion, desactivar el
        # `if is_gaming:` pasaba.
        # (iter 4) El resumen usa la MISMA clausula de MB que el texto del
        # banner: con `freed_mb <= 0` no escribe "0.0 MB liberados", igual que
        # ya hace `format_kill_result`.
        assert "Último Gaming Mode: 6 cerrados (256.0 MB liberados)" in dash.resting_label.cget("text"), (
            f"la barra de reposo debe decir como quedo el Gaming Mode: "
            f"{dash.resting_label.cget('text')!r}"
        )

        # (iter 3) UN SOLO cerrado sigue siendo exito: `clasificar_cierre` no puede
        # exigir dos. Sin este caso, `killed > 0` -> `killed > 1` sobrevivia.
        dash._show_banner(killed=1, freed_mb=2.5, is_gaming=False)
        assert dash.status_label.cget("text") == "⚡ 1 procesos cerrados · 2.5 MB liberados", (
            f"cerrar UN proceso es exito: {dash.status_label.cget('text')!r}"
        )
        assert dash.status_label.cget("text_color") == theme.ACCENT, (
            "cerrar un solo proceso da derecho al color de marca"
        )

        # (iter 4) CERRAR UN PROCESO Y NO LIBERAR MEMORIA: la clausula de MB se
        # omite con `freed_mb <= 0`, que es la regla que `format_kill_result`
        # ya aplicaba y que un test fijaba (`run_tests.py:303`). Los dos
        # formateadores de `feedback.py` la escribian siempre, de modo que la
        # misma verdad se decia de dos maneras segun por donde se ejecutara.
        # Sin este caso, borrar el `if freed_mb <= 0` de `clausula_mb` pasaba.
        dash._show_banner(killed=1, freed_mb=0.0, is_gaming=False)
        assert dash.status_label.cget("text") == "⚡ 1 procesos cerrados", (
            "cerrar un proceso sin liberar MB no puede inventar una cifra de RAM: "
            f"{dash.status_label.cget('text')!r}"
        )
        assert "MB" not in dash.status_label.cget("text"), (
            f"la clausula de MB desaparece con freed_mb <= 0: "
            f"{dash.status_label.cget('text')!r}"
        )
        assert dash.status_label.cget("text_color") == theme.ACCENT, (
            "omitir la clausula de MB no degrada el exito a aviso: se cerro de verdad"
        )
        # El resumen del Gaming Mode con la MISMA regla (si `is_gaming`).
        dash._show_banner(killed=1, freed_mb=0.0, is_gaming=True)
        assert "Último Gaming Mode: 1 cerrados" in dash.resting_label.cget("text"), (
            "el resumen del Gaming Mode tampoco puede escribir 0.0 MB: "
            f"{dash.resting_label.cget('text')!r}"
        )
        assert "0.0 MB" not in dash.resting_label.cget("text"), (
            f"0.0 MB liberados es un numero que el usuario no puede cuadrar: "
            f"{dash.resting_label.cget('text')!r}"
        )

        dash._show_banner(killed=0, freed_mb=0.0, is_gaming=True, failed=0, skipped=6)
        texto_banner = dash.status_label.cget("text")
        assert texto_banner == "⚠️ Nada que cerrar: 6 ya cerrados o protegidos.", (
            f"nada que cerrar dice exactamente eso: {texto_banner!r}"
        )
        assert dash.status_label.cget("text_color") == theme.WARNING, (
            "con 0 procesos cerrados la portada no puede pintar su color de marca: "
            f"{dash.status_label.cget('text')!r}"
        )
        assert "✅" not in texto_banner, (
            f"la rama 'nada' del banner no puede llevar tick de exito: {texto_banner!r}"
        )

        dash._show_banner(killed=0, freed_mb=0.0, is_gaming=True, failed=2, skipped=0)
        texto_banner = dash.status_label.cget("text")
        assert texto_banner == "⛔ No se cerró nada: 2 procesos con error.", (
            f"el banner de fallo nombra a los que fallaron: {texto_banner!r}"
        )
        assert dash.status_label.cget("text_color") == theme.WARNING
        assert "✅" not in texto_banner, (
            f"la rama 'fallo' del banner no puede llevar tick: {texto_banner!r}"
        )

        # --- S5: temporizadores con RELOJ SIMULADO (sin 5,5 s de espera real)
        reloj = _Reloj()
        # `after` y `after_cancel` de la vista pasan a ser la MISMA puerta que el
        # planificador: en la app son el mismo `after` de Tk.
        dash.after_cancel = reloj.cancel
        dash._init_confirmable(dash.status_label, window_ms=VENTANA_MS_PORTADA, scheduler=reloj)

        def _banner_visible():
            return dash.status_banner_frame.winfo_manager() != ""

        dash._hide_banner()
        assert not _banner_visible(), "precondicion del arnes: el banner arranca oculto"

        # t0: primer mensaje
        dash._show_start_banner(launched=3, failed=0, pack_name="Trabajo")
        primero = dash._banner_timer
        assert primero is not None, "el banner tiene que programar su auto-ocultado"
        # t = 1000: segundo mensaje, que cancela el temporizador anterior
        reloj.avanzar(1000)
        dash._show_start_banner(launched=2, failed=1, pack_name="Herramientas")
        segundo = dash._banner_timer
        cancelados = [j["id"] for j in reloj.jobs if not j["vivo"]]
        assert primero in cancelados, (
            f"el banner nuevo debe cancelar el auto-ocultado anterior ({primero}); sin "
            f"eso, a los 5000 ms el temporizador viejo apaga el banner del SEGUNDO "
            f"mensaje. Jobs vivos: {reloj.vivos()}"
        )
        # t = 5500: el viejo habria vencido (t0+5000) y el nuevo no (1000+5000)
        vencidos = reloj.avanzar(4500)
        assert not vencidos, (
            f"nada puede vencer a t=5500 con el temporizador viejo cancelado: {vencidos}"
        )
        assert _banner_visible(), (
            "a t=5500 el banner del segundo mensaje tiene que seguir en pantalla"
        )
        assert "Herramientas" in dash.status_label.cget("text")
        # t = 6500: el auto-ocultado nuevo (5000 ms) se cumple
        vencidos = reloj.avanzar(1000)
        assert segundo in vencidos, (
            f"el auto-ocultado de 5000 ms tiene que seguir existiendo (vencidos={vencidos})"
        )
        assert not _banner_visible(), "el banner debe ocultarse solo a los 5000 ms"
        assert dash._banner_timer is None, "_hide_banner debe limpiar _banner_timer"

        # (iter 3) EL MISMO ESCENARIO SOBRE `_show_banner`, que es la puerta que el
        # gamer ve tras pulsar "Apagar". Con el bloque de cancelacion duplicado
        # byte a byte y solo instrumentado en `_show_start_banner`, aqui sobrevivian
        # tres mutaciones: borrar la cancelacion, mover los 5000 ms a 60 000 y quitar
        # el `_timers_ui.discard` (fuga de handle y doble cancelacion al destruir).
        dash._hide_banner()
        assert not _banner_visible(), "precondicion del arnés: el banner arranca oculto"

        # t0: primer mensaje de CIERRE
        dash._show_banner(killed=3, freed_mb=64.0, is_gaming=True)
        primero_cierre = dash._banner_timer
        assert primero_cierre is not None, "el banner de cierre tiene que programar su auto-ocultado"
        # t = 1000: segundo mensaje de cierre
        reloj.avanzar(1000)
        dash._show_banner(killed=1, freed_mb=8.0, is_gaming=False)
        segundo_cierre = dash._banner_timer
        assert segundo_cierre != primero_cierre
        assert primero_cierre not in {j["id"] for j in reloj.jobs if j["vivo"]}, (
            f"el banner de cierre nuevo debe cancelar el auto-ocultado anterior "
            f"({primero_cierre}); sin eso, a los 5000 ms el temporizador viejo apaga "
            f"el banner del SEGUNDO mensaje. Jobs vivos: {reloj.vivos()}"
        )
        assert primero_cierre not in dash._timers_ui, (
            "el handle viejo tiene que salir de `_timers_ui` al reprogramar: si se "
            f"queda, `cancel_on_destroy` lo cancela dos veces. Vivos: {dash._timers_ui}"
        )
        assert dash._timers_ui == {segundo_cierre}, (
            f"debe quedar exactamente un auto-ocultado registrado: {dash._timers_ui}"
        )
        # t = 5500: el viejo habria vencido (t0+5000) y el nuevo no (1000+5000)
        vencidos = reloj.avanzar(4500)
        assert not vencidos, (
            f"nada puede vencer a t=5500 con el temporizador viejo cancelado: {vencidos}"
        )
        assert _banner_visible(), (
            "a t=5500 el banner del segundo cierre tiene que seguir en pantalla"
        )
        assert dash.status_label.cget("text") == "⚡ 1 procesos cerrados · 8.0 MB liberados"
        # t = 6500: el auto-ocultado nuevo (5000 ms) se cumple
        vencidos = reloj.avanzar(1000)
        assert segundo_cierre in vencidos, (
            f"el auto-ocultado de 5000 ms tiene que seguir existiendo (vencidos={vencidos})"
        )
        assert not _banner_visible(), "el banner de cierre debe ocultarse solo a los 5000 ms"
        assert dash._timers_ui == set(), (
            f"al dispararse, el handle tiene que salir de `_timers_ui`: {dash._timers_ui}"
        )

        # --- la guarda preventiva de `start_pack` (ventana real, widget real)
        pm_real = PackManagerView(root, ps, pack_s, ns, gs)
        pm_real.pack()
        # Fondo de REPOSO del label del Gestor, antes de que ningun
        # `_inline_status` lo toque. Lo afirma el bloque de contrato de canal de
        # mas abajo: el canal inline no pinta fondo, solo texto y color.
        fondo_reposo = pm_real.status_label.cget("fg_color")
        pm_real.start_pack(Pack(id="vacio", name="Pack Vacio", apps=[]))
        assert pm_real.status_label.cget("text") == (
            "⚠️ 'Pack Vacio' no tiene apps que iniciar. "
            "Añádelas desde el Gestor de Procesos."
        ), f"aviso preventivo de pack vacio: {pm_real.status_label.cget('text')!r}"
        assert pm_real.status_label.cget("text_color") == AMBAR

        # El MISMO aviso con un pack de la otra familia: gaming, `default_action="kill"`
        # y sin apps. El verbo lo decide el METODO (`start_pack` ES arrancar), no el
        # `default_action` del pack. Sin este caso la suite no distingue las dos
        # cableaciones: el pack de arriba trae `default_action="start"` de serie, asi
        # que "start" y `pack.default_action` dan el mismo texto y la convencion
        # queda sin medir. Con el gaming de apagar, cablear `pack.default_action`
        # devuelve "apagar" y este bloque muere.
        pm_real.start_pack(Pack(id="g_vacio", name="Gaming Vacio Start",
                                is_gaming=True, default_action="kill", apps=[]))
        assert pm_real.status_label.cget("text") == (
            "⚠️ 'Gaming Vacio Start' no tiene apps que iniciar. "
            "Añádelas desde el Gestor de Procesos."
        ), (
            "arrancar dice INICIAR aunque el pack sea de apagar: el verbo lo decide "
            "el metodo que se esta ejecutando, no el default_action del pack. Con la "
            f"otra cableacion sale 'apagar': {pm_real.status_label.cget('text')!r}"
        )
        assert pm_real.status_label.cget("text_color") == AMBAR

        # Contrato de CANAL (deuda 8 del ciclo 26): el diagnostico inline no puede
        # caer sobre el fondo CANCEL. `Confirmable._inline_status` solo configura
        # texto y color; el CANCEL lo pinta el OVERRIDE de la Portada, y el
        # diagnostico no pasa por ahi (la mitad banner se mide en el bloque (f)).
        # Se compara contra el fondo de REPOSO, no contra el anterior: si el
        # canal pintara CANCEL, el color ya seria CANCEL de antes y la comparacion
        # de "antes/despues" seria verde por construccion.
        pm_real._inline_status("⛔ El Gaming Mode de 'Gaming Vacio Start' no tiene "
                               "nada que cerrar.", ROJO)
        assert pm_real.status_label.cget("fg_color") == fondo_reposo, (
            "el canal inline no pinta fondo: el diagnostico ROJO caeria sobre el "
            f"{CANCEL!r} de la confirmacion pendiente. Reposo: {fondo_reposo!r}, "
            f"despues: {pm_real.status_label.cget('fg_color')!r}"
        )
        pm_real.destroy()

        # -----------------------------------------------------------------
        # 4. Los workers REALES de PackManagerView, sin Tk (S1, S9)
        # -----------------------------------------------------------------
        # No se llama a `_inline_status` con un literal y se comprueba que el
        # label lo muestre: eso seria afirmar que el codigo hace lo que el codigo
        # acaba de escribir. Aqui entra `kill_pack`/`start_pack`, pulsa dos veces
        # (contrato de doble pulsacion), el worker corre en un hilo real y el
        # test hace de bucle de eventos.
        cola = collections.deque()
        principal = threading.get_ident()
        hilos = []

        class _HiloEspia(threading.Thread):
            def __init__(self, *a, **k):
                super().__init__(*a, **k)
                hilos.append(self)

        class _ShimThreading:
            Thread = _HiloEspia

        def _gestor(pack, procs, gaming):
            v = PackManagerView.__new__(PackManagerView)
            v.status_label = _Label()
            v.pack_service = _Packs(pack)
            v.process_service = procs
            v.gaming_service = gaming
            v.notification_service = _Notis()
            v.refresh_packs = lambda: None

            def after_falso(ms, func=None, *args):
                cola.append((ms, func, args, threading.get_ident()))

            v.after = after_falso
            v._init_confirmable(v.status_label, window_ms=VENTANA_MS, scheduler=_Reloj())
            return v

        def _correr(v, metodo, *args, doble=False, callback=None):
            """Ejecuta la accion y aplica en el PRINCIPAL lo que el secundario encolo."""
            esperado = callback(v) if callback is not None else v._inline_status
            antes_hilos, antes_cola = len(hilos), len(cola)
            if doble:
                metodo(v, *args)                     # 1a pulsacion: solo arma
                assert len(hilos) == antes_hilos, (
                    "la primera pulsacion no debe lanzar el worker: mata apps de un clic"
                )
                assert len(cola) == antes_cola, "la primera pulsacion no publica feedback de cierre"
                metodo(v, *args)                     # 2a pulsacion: ejecuta
            else:
                metodo(v, *args)
            nuevos = hilos[antes_hilos:]
            assert len(nuevos) == 1, f"se esperaba 1 worker secundario, se crearon {len(nuevos)}"
            nuevos[0].join(20)
            assert not nuevos[0].is_alive(), "el worker secundario no termino"
            pendientes = list(list(cola)[antes_cola:])
            assert pendientes, "el worker no publico feedback por self.after(0, ...)"
            for ms, func, args, ident in pendientes:
                assert ms == 0, f"el after debe ser de 0 ms, no de {ms}"
                assert ident != principal, (
                    "el after se encolo desde el principal: entonces el secundario no publico nada"
                )
                assert func == esperado, f"el after debe publicar en {esperado}, no en {func}"
                func(*args)
            return v

        threading_real = pmv_mod.threading
        threading_real_dash = dash_mod.threading
        pmv_mod.threading = _ShimThreading
        dash_mod.threading = _ShimThreading
        try:
            # (0) El worker REAL de la portada. Sin esto, tirar `failed` y
            # `skipped` en `_run_kill` seria invisible: las aserciones del
            # banner llamaban a `_show_banner` directamente, con los valores
            # puestos a mano, y el worker no contaba para nada.
            procs_portada, gaming_portada = _ProcesosGestor(), _GamingGestor()
            gaming_portada.cierre = (0, 0, 6, 0.0)      # todo en keepers
            dash.process_service = procs_portada
            dash.gaming_service = gaming_portada
            dash.notification_service = _Notis()
            dash.after = lambda ms, func=None, *a: cola.append((ms, func, a, threading.get_ident()))
            # (iter 4) El Gaming Mode con categorias NO es inerte y tiene que
            # seguir entrando por la puerta real. Sin categorias este pack
            # caeria en el diagnostico de TASK-036 y `execute_gaming_pack` no
            # llegaria a llamarse nunca.
            CATEGORIA_MEDIA = "\U0001F7E1 Media y Streaming"
            pack_portada = Pack(id="gaming", name="Gaming Mode", is_gaming=True,
                                default_action="kill",
                                target_categories=[CATEGORIA_MEDIA])
            _correr(dash, DashboardView.execute_pack, pack_portada, doble=True,
                    callback=lambda v: v._show_banner)
            assert gaming_portada.llamadas == 1 and procs_portada.llamadas_cierre == 0, (
                "la portada cierra el pack gaming por la puerta que respeta keepers"
            )
            assert dash.status_label.cget("text_color") == theme.WARNING, (
                "el worker de la portada no puede pintar el color de marca con 0 "
                f"cerrados: {dash.status_label.cget('text')!r}"
            )
            assert "6" in dash.status_label.cget("text"), (
                "el worker de la portada tiene que entregarle a `_show_banner` el "
                f"resultado completo: {dash.status_label.cget('text')!r}"
            )
            del dash.after

            APPS = [r"C:\Juegos\juego.exe"]
            pack_normal = Pack(id="trabajo", name="Trabajo", apps=list(APPS))
            pack_gaming = Pack(id="gaming", name="Gaming Mode", is_gaming=True,
                               target_categories=[CATEGORIA_MEDIA])

            # (iter 3) La rama NO GAMING de la portada no se ejecutaba NUNCA en la
            # suite: con solo el pack gaming, tanto `if p.is_gaming:` ->
            # `if not p.is_gaming:` como `kill_pack_apps(p.apps)` ->
            # `kill_pack_apps([])` pasaban los dos. Es el mismo patron del ciclo 14:
            # una rama sin probar y la otra mirando cosas distintas.
            pack_apagar = Pack(id="apagar", name="Apagar", apps=list(APPS),
                               default_action="kill")
            procs, gaming = _ProcesosGestor(), _GamingGestor()
            procs.cierre = (2, 0, 0, 40.0)
            dash.process_service = procs
            dash.gaming_service = gaming
            dash.notification_service = _Notis()
            dash.after = lambda ms, func=None, *a: cola.append((ms, func, a, threading.get_ident()))
            _correr(dash, DashboardView.execute_pack, pack_apagar, doble=True,
                    callback=lambda v: v._show_banner)
            assert gaming.llamadas == 0, (
                "un pack NO gaming de la portada no puede pasar por la puerta del "
                "Gaming Mode: execute_gaming_pack consulta keepers y solo tiene "
                "sentido en el preset"
            )
            assert procs.llamadas_cierre == 1 and procs.apps == APPS, (
                "un pack NO gaming se cierra con SUS apps, no con una lista vacia: "
                f"llego {procs.apps}"
            )
            assert dash.status_label.cget("text") == (
                "⚡ 2 procesos cerrados · 40.0 MB liberados"
            ), f"banner de la rama no gaming: {dash.status_label.cget('text')!r}"
            assert dash.status_label.cget("text_color") == theme.ACCENT
            del dash.after

            # (iter 3) El ORDEN de la 4-tupla en el worker de la portada. Con
            # `failed == skipped` en todos los casos anteriores, intercambiar
            # `(..., failed, skipped)` por `(..., skipped, failed)` era invisible:
            # los dos numeros se parecian y el texto salia igual.
            procs, gaming = _ProcesosGestor(), _GamingGestor()
            gaming.cierre = (2, 3, 5, 12.0)          # failed != skipped a proposito
            dash.process_service = procs
            dash.gaming_service = gaming
            dash.after = lambda ms, func=None, *a: cola.append((ms, func, a, threading.get_ident()))
            _correr(dash, DashboardView.execute_pack, pack_portada, doble=True,
                    callback=lambda v: v._show_banner)
            assert dash.status_label.cget("text") == (
                "⚠️ 2 procesos cerrados · 12.0 MB liberados · 3 con error."
            ), (
                "el worker de la portada tiene que leer la 4-tupla en el orden "
                "(killed, failed, skipped, freed_mb): si intercambia failed y "
                f"skipped, el texto dirá 5 con error. Dice: {dash.status_label.cget('text')!r}"
            )
            assert dash.status_label.cget("text_color") == theme.WARNING
            del dash.after

            # (iter 4) LA RAMA START DE `execute_pack` NO SE EJECUTABA NUNCA.
            # Tres mutaciones pasaban la suite entera en verde: intercambiar
            # `launched`/`failed` en `_run_start`, arrancar
            # `start_pack_apps([])`, y publicar en `_show_banner` con
            # `(p.name)` en el hueco de `is_gaming` (banner verde Gaming y
            # `_last_gaming_summary` basura, sin crash). Es la misma clase que
            # el ciclo condena: una rama sin ejecutar no es una rama probada. El
            # caso entra por el WORKER REAL, no llamando a `_show_start_banner`
            # con valores puestos a mano (que es el patron "test que se llama a
            # si mismo" que `testing-guide.md` sec. 1 condena).
            pack_arrancar = Pack(id="arrancar", name="Trabajo", apps=list(APPS),
                                 default_action="start")
            procs, gaming = _ProcesosGestor(), _GamingGestor()
            procs.arranque = (3, 0)
            antes_resumen = dash.resting_label.cget("text")
            dash.process_service = procs
            dash.gaming_service = gaming
            dash.notification_service = _Notis()
            dash.after = lambda ms, func=None, *a: cola.append((ms, func, a, threading.get_ident()))
            _correr(dash, DashboardView.execute_pack, pack_arrancar,
                    callback=lambda v: v._show_start_banner)
            assert procs.llamadas_arranque == 1 and procs.apps == APPS, (
                "la rama start arranca SUS apps, no una lista vacia: "
                f"llego {procs.apps!r}"
            )
            assert procs.llamadas_cierre == 0 and gaming.llamadas == 0, (
                "la rama start no cierra nada: no puede pasar por kill_pack_apps "
                "ni por execute_gaming_pack"
            )
            assert dash.status_label.cget("text") == "🚀 Pack 'Trabajo' iniciado (3 apps).", (
                f"el worker de arranque tiene que entregar launched y failed sin "
                f"intercambiarlos: {dash.status_label.cget('text')!r}"
            )
            assert dash.status_label.cget("text_color") == theme.ACCENT
            assert dash.notification_service.eventos == [("start", "Trabajo", 3, 0)], (
                "el toast de arranque lleva los numeros reales, no intercambiados: "
                f"{dash.notification_service.eventos}"
            )
            # El nombre del pack no puede colarse como flag de gaming: publicar en
            # `_show_banner` con `p.name` en el hueco de `is_gaming` deja el
            # resumen del Gaming Mode reescrito con datos de arranque, sin crash.
            assert dash.resting_label.cget("text") == antes_resumen, (
                "arrancar no es ejecutar el Gaming Mode: el resumen del Gaming Mode "
                f"no puede cambiar. Antes {antes_resumen!r}, despues "
                f"{dash.resting_label.cget('text')!r}"
            )

            # El mismo caso con fallos, que es donde intercambiar los dos numeros
            # se ve: 3/0 y 1/2 dan textos distintos.
            procs, gaming = _ProcesosGestor(), _GamingGestor()
            procs.arranque = (1, 2)
            dash.process_service = procs
            dash.gaming_service = gaming
            dash.after = lambda ms, func=None, *a: cola.append((ms, func, a, threading.get_ident()))
            _correr(dash, DashboardView.execute_pack, pack_arrancar,
                    callback=lambda v: v._show_start_banner)
            assert dash.status_label.cget("text") == (
                "⚠️ Pack 'Trabajo': 1 apps iniciadas, 2 fallaron."
            ), (
                "1 iniciada y 2 fallidas no es lo mismo que 2 iniciadas y 1 fallida: "
                f"{dash.status_label.cget('text')!r}"
            )
            assert dash.status_label.cget("text_color") == theme.WARNING
            del dash.after

            # (1) CIERRE NORMAL CON EXITO REAL -> VERDE
            procs, gaming = _ProcesosGestor(), _GamingGestor()
            procs.cierre = (3, 0, 0, 128.5)
            v = _correr(_gestor(pack_normal, procs, gaming), PackManagerView.kill_pack,
                        "trabajo", doble=True)
            assert v.status_label.texto == (
                "✅ 3 procesos cerrados (128.5 MB liberados) · 'Trabajo'."
            ), f"mensaje de exito real: {v.status_label.texto!r}"
            assert v.status_label.color == VERDE
            assert procs.llamadas_cierre == 1 and procs.apps == APPS, (
                "el pack se cierra con SUS apps, no con un atajo"
            )
            assert gaming.llamadas == 0, "un pack normal no pasa por la puerta del Gaming Mode"
            assert v.notification_service.eventos == [("kill", "Trabajo", 3, 128.5)], (
                f"el toast debe llevar el resultado real: {v.notification_service.eventos}"
            )

            # (iter 3) `killed == 1` con `failed == 0` es EXITO, no "nada". Sin este
            # caso, `clasificar_cierre` con `killed > 0` -> `killed > 1` sobrevivia:
            # ningun caso de la puerta del pack cerraba exactamente UN proceso.
            procs, gaming = _ProcesosGestor(), _GamingGestor()
            procs.cierre = (1, 0, 0, 2.5)
            v = _correr(_gestor(pack_normal, procs, gaming), PackManagerView.kill_pack,
                        "trabajo", doble=True)
            assert v.status_label.texto == (
                "✅ 1 procesos cerrados (2.5 MB liberados) · 'Trabajo'."
            ), f"cerrar un solo proceso sigue siendo exito: {v.status_label.texto!r}"
            assert v.status_label.color == VERDE, (
                f"cerrar un proceso da derecho al verde: {v.status_label.color!r}"
            )

            # (2) NADA CERRADO POR LA PUERTA NORMAL (todo en keepers / ya cerrado)
            procs, gaming = _ProcesosGestor(), _GamingGestor()
            procs.cierre = (0, 0, 4, 0.0)
            v = _correr(_gestor(pack_normal, procs, gaming), PackManagerView.kill_pack,
                        "trabajo", doble=True)
            texto, color = v.status_label.texto, v.status_label.color
            assert color != VERDE, (
                f"con 0 procesos cerrados el feedback no puede ser VERDE: {texto!r}"
            )
            assert color == AMBAR, f"sin cierre y sin error, el feedback es de atencion: {color!r}"
            assert "✅" not in texto, (
                f"no se puede poner un tick de exito sin haber cerrado nada: {texto!r}"
            )
            assert "0 procesos cerrados" in texto, f"el mensaje debe decir 0: {texto!r}"
            assert "4" in texto, (
                f"el mensaje debe decir cuantos quedaron intactos, no inventarlos: {texto!r}"
            )

            # (3) LA MISMA MENTIRA POR LA PUERTA GAMING (keepers + categorias)
            procs, gaming = _ProcesosGestor(), _GamingGestor()
            gaming.cierre = (0, 0, 6, 0.0)
            v = _correr(_gestor(pack_gaming, procs, gaming), PackManagerView.kill_pack,
                        "gaming", doble=True)
            texto, color = v.status_label.texto, v.status_label.color
            assert gaming.llamadas == 1 and procs.llamadas_cierre == 0, (
                "un pack gaming se cierra por execute_gaming_pack, que respeta keepers "
                "y la barrera de categoria roja"
            )
            assert color == AMBAR and "✅" not in texto, (
                f"la puerta gaming tampoco puede mentir en verde: {texto!r} / {color!r}"
            )
            assert "0 procesos cerrados" in texto and "6" in texto, (
                f"el gaming tiene que decir lo mismo que la puerta normal: {texto!r}"
            )

            # (4) FALLO: no se pudo cerrar NADA
            procs, gaming = _ProcesosGestor(), _GamingGestor()
            procs.cierre = (0, 2, 0, 0.0)
            v = _correr(_gestor(pack_normal, procs, gaming), PackManagerView.kill_pack,
                        "trabajo", doble=True)
            texto, color = v.status_label.texto, v.status_label.color
            assert color == ROJO, f"un cierre fallido es un bloqueo, no un aviso: {color!r}"
            assert "✅" not in texto and "2" in texto, (
                f"el fallo debe decir cuantos fallaron: {texto!r}"
            )

            # (5) PARCIAL: cerro algo y algo fallo -> ni tick ni verde
            procs, gaming = _ProcesosGestor(), _GamingGestor()
            procs.cierre = (2, 1, 0, 64.0)
            v = _correr(_gestor(pack_normal, procs, gaming), PackManagerView.kill_pack,
                        "trabajo", doble=True)
            texto, color = v.status_label.texto, v.status_label.color
            assert color == AMBAR and "✅" not in texto, (
                f"un cierre parcial no se celebra como exito: {texto!r} / {color!r}"
            )
            assert "2 cerrados" in texto and "1 con error" in texto, f"detalle del parcial: {texto!r}"

            # (6) `start_pack` por el mismo camino real
            procs, gaming = _ProcesosGestor(), _GamingGestor()
            procs.arranque = (3, 0)
            v = _correr(_gestor(pack_normal, procs, gaming), PackManagerView.start_pack, pack_normal)
            assert v.status_label.texto == "🚀 3 apps iniciadas · 'Trabajo'.", (
                f"arranque sin errores: {v.status_label.texto!r}"
            )
            assert v.status_label.color == VERDE
            assert procs.llamadas_arranque == 1 and procs.apps == APPS

            procs.arranque = (2, 1)
            v = _correr(_gestor(pack_normal, procs, gaming), PackManagerView.start_pack, pack_normal)
            assert v.status_label.texto == (
                "⚠️ 'Trabajo': 2 iniciadas, 1 con error."
            ), f"arranque con errores: {v.status_label.texto!r}"
            assert v.status_label.color == AMBAR

            # (iter 3) Las dos guardas PREVENTIVAS. Sin la de `execute_pack`, un pack
            # no gaming y sin apps armaba la doble pulsacion ("para apagar 0 apps")
            # sobre un pack-imposible; sin la de `kill_pack`, un id desaparecido
            # reventaba con AttributeError en `pack.is_gaming`.
            #
            # (iter 4, TASK-036) LA ASERCION DE ARRIBA ESTABA INVERTIDA: afirmaba
            # el SILENCIO, y una asercion que prohibe la verdad nueva se convierte
            # en la especificacion de la mentira. Aqui lo que se mantiene es que no
            # hay worker ni nada encolado; lo que se invierte es que el aviso sale.
            def _sin_confirmacion_pendiente(v):
                # Lo que se afirma es que no hay una pendiente VIVA. El boton
                # marcado no se mira porque en este arnes `button=None`
                # (los workers se disparan sin boton), asi que `_boton_pendiente`
                # nunca se rellena y mirarlo daria un verde por la razon
                # equivocada.
                return not v._guard.is_pending()

            AVISO_VACIO_APAGAR = (
                "⚠️ 'Vacio' no tiene apps que apagar. "
                "Añádelas desde el Gestor de Procesos."
            )
            DIAGNOSTICO_GAMING = (
                "⛔ El Gaming Mode de 'Gaming Vacio' no tiene nada que cerrar: "
                "0 apps y 0 categorías configuradas. Revísalo en el Gestor de Packs."
            )
            pack_vacio = Pack(id="vacio", name="Vacio", apps=[], default_action="kill")
            antes_hilos, antes_cola = len(hilos), len(cola)
            before_text = dash.status_label.cget("text")
            DashboardView.execute_pack(dash, pack_vacio)
            assert len(hilos) == antes_hilos, (
                "un pack no gaming y vacio no puede lanzar el worker de cierre"
            )
            assert len(cola) == antes_cola, (
                "un pack no gaming y vacio no encola feedback por after: el aviso es "
                "sincrono, ya estamos en el hilo principal dentro de un callback"
            )
            assert dash.status_label.cget("text") == AVISO_VACIO_APAGAR, (
                "un pack no gaming y vacio SE AVISA, no se traga en silencio "
                "(ui-design-system.md, Acciones Destructivas). Antes "
                f"{before_text!r}, despues {dash.status_label.cget('text')!r}"
            )
            assert dash.status_label.cget("text_color") == theme.WARNING, (
                "el aviso de pack inerte es de ATENCION: no verde (no hubo exito) ni "
                f"rojo (no hubo error). Color: {dash.status_label.cget('text_color')!r}"
            )
            assert _sin_confirmacion_pendiente(dash), (
                "el aviso no puede ir montado sobre una doble pulsacion: la guarda va "
                "ANTES de `_require_double_tap`, o se arma 'Segunda pulsacion para "
                f"apagar 0 apps'. Estado: {dash._guard.token!r}"
            )

            # (a) `default_action="start"` -> el verbo lo decide el formateador.
            # Sin este caso, un "apagar" cableado a mano pasa la prueba de arriba.
            antes_hilos, antes_cola = len(hilos), len(cola)
            DashboardView.execute_pack(dash, Pack(id="vacio2", name="Vacio",
                                                  apps=[], default_action="start"))
            assert dash.status_label.cget("text") == (
                "⚠️ 'Vacio' no tiene apps que iniciar. "
                "Añádelas desde el Gestor de Procesos."
            ), (
                "con `default_action='start'` el verbo es 'iniciar': el mapa esta "
                f"DENTRO del formateador. Dice: {dash.status_label.cget('text')!r}"
            )
            assert len(hilos) == antes_hilos and len(cola) == antes_cola, (
                "tampoco la rama start puede lanzar worker con un pack vacio"
            )
            assert _sin_confirmacion_pendiente(dash), (
                "la rama start tampoco puede armar la doble pulsacion sobre un pack vacio"
            )

            # (b) El Gaming Mode INERTE es un diagnostico, no un desenlace. Con 0
            # apps y 0 categorias `should_kill_for_gaming` cae a False para todo
            # lo que no este protegido: es inerte por construccion.
            antes_hilos, antes_cola = len(hilos), len(cola)
            pack_gaming_inerte = Pack(id="gin", name="Gaming Vacio", is_gaming=True,
                                      default_action="kill")
            DashboardView.execute_pack(dash, pack_gaming_inerte)
            assert dash.status_label.cget("text") == DIAGNOSTICO_GAMING, (
                "el Gaming Mode inerte se diagnostica: sin este texto caia en la "
                f"puerta real y decia 'Nada que cerrar: 0 ya cerrados'. Dice: "
                f"{dash.status_label.cget('text')!r}"
            )
            assert dash.status_label.cget("text_color") == theme.WARNING, (
                "el diagnostico va en el color de la portada (theme.DANGER sobre "
                f"SURFACE_ALT da 3.07:1 y el design system exige 4.5:1): "
                f"{dash.status_label.cget('text_color')!r}"
            )
            assert len(hilos) == antes_hilos and len(cola) == antes_cola, (
                "el gaming inerte no puede lanzar worker: no hay nada que cerrar"
            )
            assert _sin_confirmacion_pendiente(dash), (
                "el diagnostico va ANTES de la doble pulsacion, no despues"
            )

            # (c) Un gaming CON categorias NO es inerte y NO avisa: cierra de verdad
            # por la via G-2/G-3. Sin este caso, `es_pack_inerte` con `or` en vez
            # de `and` (n_apps == 0 or n_categorias == 0) pasa todo lo anterior.
            antes_texto = dash.status_label.cget("text")
            procs_sano, gaming_sano = _ProcesosGestor(), _GamingGestor()
            gaming_sano.cierre = (1, 0, 0, 12.0)
            dash.process_service = procs_sano
            dash.gaming_service = gaming_sano
            dash.notification_service = _Notis()
            dash.after = lambda ms, func=None, *a: cola.append((ms, func, a, threading.get_ident()))
            _correr(dash, DashboardView.execute_pack, pack_portada, doble=True,
                    callback=lambda v: v._show_banner)
            assert gaming_sano.llamadas == 1, (
                "un gaming CON categorias tiene que cerrar de verdad, no avisar: "
                "diagnosticar como inerte un pack que si puede cerrar es tan mentira "
                f"como el silencio. Banner: {dash.status_label.cget('text')!r}"
            )
            assert dash.status_label.cget("text") == (
                "⚡ 1 procesos cerrados · 12.0 MB liberados"
            ), f"gaming sano: {dash.status_label.cget('text')!r}"
            del dash.after

            # (d) Un gaming con APPS pero sin categorias tampoco es inerte (es el
            # otro lado del mismo `and`).
            antes_hilos, antes_cola = len(hilos), len(cola)
            pack_gaming_con_apps = Pack(id="gapps", name="Gaming Con Apps", is_gaming=True,
                                        default_action="kill", apps=list(APPS))
            procs_sano2, gaming_sano2 = _ProcesosGestor(), _GamingGestor()
            gaming_sano2.cierre = (1, 0, 0, 4.0)
            dash.process_service = procs_sano2
            dash.gaming_service = gaming_sano2
            dash.after = lambda ms, func=None, *a: cola.append((ms, func, a, threading.get_ident()))
            _correr(dash, DashboardView.execute_pack, pack_gaming_con_apps, doble=True,
                    callback=lambda v: v._show_banner)
            assert gaming_sano2.llamadas == 1, (
                "0 categorias no significa inerte si hay apps: el `and` de "
                f"es_pack_inerte no puede ser un `or`. Banner: {dash.status_label.cget('text')!r}"
            )
            del dash.after

            # (e) Las DOS FAMILIAS dicen lo mismo. Si la frase viviera copiada en
            # los dos sitios, el usuario leeria el mismo hecho con dos redacciones
            # segun donde pulse. Se comprueba en las dos familias y en los dos
            # avisos (el de apps vacias y el diagnostico del gaming inerte).
            from woptimizer.ui.feedback import (
                mensaje_banner_gaming_inerte, mensaje_banner_sin_apps,
                mensaje_gaming_inerte, mensaje_sin_apps,
            )
            assert mensaje_sin_apps("Vacio", "kill")[0] == mensaje_banner_sin_apps("Vacio", "kill")[0], (
                "las dos familias del aviso de pack sin apps tienen que decir "
                "exactamente lo mismo"
            )
            assert mensaje_gaming_inerte("G")[0] == mensaje_banner_gaming_inerte("G")[0], (
                "las dos familias del diagnostico del gaming inerte tienen que decir "
                "exactamente lo mismo"
            )
            assert mensaje_sin_apps("Vacio", "kill")[1] == AMBAR, (
                "la familia inline del aviso es AMBAR"
            )
            assert mensaje_banner_sin_apps("Vacio", "kill")[1] == theme.WARNING, (
                "la familia banner del aviso es theme.WARNING"
            )
            assert mensaje_gaming_inerte("G")[1] == ROJO, (
                "el diagnostico inline es ROJO: es un bloqueo, no un aviso"
            )
            assert mensaje_banner_gaming_inerte("G")[1] == theme.WARNING, (
                "el diagnostico en banner no puede ser DANGER: 3.07:1 < 4.5:1"
            )

            # (f) El CANAL del aviso: `_show_aviso_banner` y no `_inline_status`.
            # `_inline_status` pinta el fondo con `CANCEL`, que es la familia del
            # aviso de "confirmacion pendiente", y NUNCA se auto-oculta. Con el
            # reloj simulado del bloque S5 (ya instalado en `dash`) se mide que el
            # aviso se va solo a los 5000 ms.
            dash._hide_banner()
            assert not _banner_visible(), "precondicion del arnes: el banner arranca oculto"
            DashboardView.execute_pack(dash, pack_vacio)
            assert dash.status_banner_frame.cget("fg_color") == theme.SURFACE_ALT, (
                "el aviso va sobre SURFACE_ALT, no sobre el fondo CANCEL de la "
                "confirmacion pendiente (que se lee como 'espera la segunda pulsacion'): "
                f"{dash.status_banner_frame.cget('fg_color')!r}"
            )
            assert dash._banner_timer is not None, (
                "el aviso tiene que programar su auto-ocultado: un aviso pegado en la "
                "portada contradice la regla de _on_expirado"
            )
            assert _banner_visible(), "el aviso se ve en pantalla"
            handle_aviso = dash._banner_timer
            vencidos = reloj.avanzar(dash_mod.AUTOOCULTADO_MS)
            assert handle_aviso in vencidos, (
                f"el aviso tiene que auto-ocultarse a los {dash_mod.AUTOOCULTADO_MS} "
                f"ms, como las otras dos puertas del banner. Vencidos: {vencidos}"
            )
            assert not _banner_visible(), "el aviso es de usar y tirar, como el resto"
            dash._hide_banner()

            # El MISMO canal desde el Gestor de Packs: el gaming inerte se
            # diagnostica tambien ahi, antes de la doble pulsacion.
            v = _gestor(Pack(id="gin", name="Gaming Vacio", is_gaming=True),
                        _ProcesosGestor(), _GamingGestor())
            antes_hilos = len(hilos)
            PackManagerView.kill_pack(v, "gin")
            assert len(hilos) == antes_hilos, "el gaming inerte no lanza worker"
            assert v.status_label.texto == (
                "⛔ El Gaming Mode de 'Gaming Vacio' no tiene nada que cerrar: "
                "0 apps y 0 categorías configuradas. Revísalo en el Gestor de Packs."
            ), f"diagnostico en el Gestor: {v.status_label.texto!r}"
            assert v.status_label.color == ROJO, (
                f"el diagnostico inline del Gestor es ROJO: {v.status_label.color!r}"
            )
            assert not v._guard.is_pending(), (
                "el diagnostico va antes de la doble pulsacion tambien en el Gestor"
            )

            v = _gestor(pack_normal, _ProcesosGestor(), _GamingGestor())
            antes_hilos = len(hilos)
            PackManagerView.kill_pack(v, "no_existe")
            assert len(hilos) == antes_hilos, "un pack inexistente no puede lanzar worker"
            assert v.status_label.texto == MSG_PACK_INEXISTENTE, (
                f"un pack inexistente se avisa, no se revienta: {v.status_label.texto!r}"
            )
            assert v.status_label.color == AMBAR

            # (iter 6) El verbo de la puerta de APAGAR. El pack de aqui nace con
            # `default_action="start"` --que es lo que hace `create_user_pack` en
            # `on_new_pack`-- y no es gaming, asi que cae en el aviso de "no tiene
            # apps" y NO en el diagnostico del gaming inerte: si este assert
            # muriera, seria por el verbo y por nada mas. Sin el, un
            # `pack.default_action` cableado en `_aviso_pack_inerte` decia
            # "iniciar" en la puerta de apagar y la suite no lo notaba, porque
            # arriba solo se probaba el gaming inerte y el id inexistente.
            pack_apagar_vacio = Pack(id="recien", name="Mi Pack", apps=[],
                                     default_action="start")
            v = _gestor(pack_apagar_vacio, _ProcesosGestor(), _GamingGestor())
            antes_hilos = len(hilos)
            PackManagerView.kill_pack(v, "recien")
            assert len(hilos) == antes_hilos, (
                "un pack no gaming y vacio no puede lanzar worker: no hay nada que apagar"
            )
            assert v.status_label.texto == (
                "⚠️ 'Mi Pack' no tiene apps que apagar. "
                "Añádelas desde el Gestor de Procesos."
            ), (
                "el verbo lo decide la PUERTA que se esta pulsando (aqui apagar), no "
                "el `default_action` del pack: un pack recien creado nace con "
                f"'start' y el aviso diria 'iniciar' en la puerta de apagar. "
                f"Texto: {v.status_label.texto!r}"
            )
            assert v.status_label.color == AMBAR, (
                f"el aviso de pack vacio del Gestor es AMBAR: {v.status_label.color!r}"
            )
            assert not v._guard.is_pending(), (
                "el aviso va antes de la doble pulsacion: no se arma 'Segunda "
                "pulsacion para apagar 0 apps' de un pack que no tiene nada"
            )

            # =============================================================
            # (iter 7) LAS CUATRO AFIRMACIONES QUE EL CIERRE DE AUDITORIA
            # ENCONTRO SIN RESPALDO. Las cuatro son la MISMA clase de fallo que
            # motivo este ciclo: el codigo (o el doc) afirma algo que ningun
            # test mide, asi que el siguiente rewrite lo rompe en silencio.
            # El contrato de los llamantes (c-bis) NO esta aqui: se ejecuta al
            # principio de la sonda, antes de nada, para que si un llamante
            # cablea un verbo el fallo nombre el fichero y la linea en vez de
            # dejar que reviente el `KeyError` de `_verbo` mas abajo.
            # =============================================================

            # (iter 7, a) EL SEGUNDO PUNTO DE GUARDA DE `kill_pack`.
            # `_aviso_pack_inerte` se llama en DOS puntos (antes de armar la
            # doble pulsacion y despues del re-fetch por `id`) y el codigo lo
            # afirma: "por eso esta en un metodo y no en dos literales". El
            # `mutation-auditor` lo muto en el SEGUNDO y el mutante vivio: un
            # pack que pierde las apps entre las dos pulsaciones llegaba a
            # `kill_pack_apps([])` DESPUES de haber consumido la doble
            # pulsacion. O sea, la defensa de dos puntos tenia un punto de ancho
            # y el doc decia que no.
            #
            # No vale llamar a `_aviso_pack_inerte` con un pack vacio: eso mide
            # el PRIMER punto (que es lo que hacia la iteracion 6). Aqui entra
            # por `kill_pack` de verdad, con doble pulsacion, y el escenario
            # exige TRES lecturas, que es lo que hace ALCANZABLE el segundo
            # punto: la 1a pulsacion y la cima de la 2a ven el pack CON apps
            # (por eso se arma la confirmacion), y el re-fetch posterior ve el
            # pack SIN ellas.
            class _PacksQuePierdenLasApps:
                """Doble de `PackService`: el pack pierde las apps entre pulsaciones.

                Un `Pack` NUEVO en cada lectura, no una lista mutada en sitio:
                `kill_pack` re-lee por `id` y lo que cambia entre lecturas es lo
                que el usuario quito del pack, no la referencia que el test
                guarda. Ademas lleva la cuenta, porque sin el recuento de
                lecturas el bloque pasaria aunque el arnes no llegara al
                segundo punto (es decir, aunque midiera el primero por
                accidente).
                """

                def __init__(self):
                    self.lecturas = 0

                def get_all_packs(self):
                    self.lecturas += 1
                    apps = list(APPS) if self.lecturas <= 2 else []
                    return {"trabajo": Pack(id="trabajo", name="Trabajo", apps=apps,
                                            default_action="kill")}

            procs, gaming = _ProcesosGestor(), _GamingGestor()
            procs.cierre = (0, 0, 0, 0.0)
            v = _gestor(pack_normal, procs, gaming)
            packs_perdidos = _PacksQuePierdenLasApps()
            v.pack_service = packs_perdidos
            antes_hilos, antes_cola = len(hilos), len(cola)
            PackManagerView.kill_pack(v, "trabajo")          # 1a pulsacion: solo arma
            assert packs_perdidos.lecturas == 1, (
                "la 1a pulsacion lee el pack una vez y solo eso; si lee mas, el "
                f"escenario ya no mide el segundo punto (lecturas={packs_perdidos.lecturas})"
            )
            assert v._guard.is_pending(), (
                "el arnes no llego a la confirmacion: sin la doble pulsacion el "
                "segundo punto de guarda de `kill_pack` no existe que medir"
            )
            assert len(hilos) == antes_hilos, (
                "la 1a pulsacion no puede lanzar el worker: mata apps de un clic"
            )
            PackManagerView.kill_pack(v, "trabajo")          # 2a: consume y ejecuta
            assert packs_perdidos.lecturas == 3, (
                "el arnes no llego al re-fetch por id (3a lectura): sin el, el "
                "bloque estaria afirmando el PRIMER punto de guarda con otro "
                f"nombre. Lecturas: {packs_perdidos.lecturas}"
            )
            assert not v._guard.is_pending(), (
                "la 2a pulsacion tiene que CONSUMIR la confirmacion antes de "
                f"llegar al re-fetch (estado: {v._guard.token!r})"
            )
            assert procs.llamadas_cierre == 0, (
                "el pack perdió sus apps ENTRE las dos pulsaciones: la segunda "
                "guarda de `kill_pack` tiene que avisar, no lanzar "
                f"kill_pack_apps({procs.apps!r}) despues de haber consumido la "
                "doble pulsacion"
            )
            assert len(hilos) == antes_hilos, (
                "el aviso del pack ya vacio no lanza worker: no hay nada que apagar"
            )
            assert len(cola) == antes_cola, (
                "el aviso del pack ya vacio se publica en el hilo principal, sin "
                "encolar feedback de cierre por after"
            )
            assert v.status_label.texto == (
                "⚠️ 'Trabajo' no tiene apps que apagar. "
                "Añádelas desde el Gestor de Procesos."
            ), (
                "el segundo punto de guarda muestra el mismo aviso que el "
                f"primero: {v.status_label.texto!r}"
            )
            assert v.status_label.color == AMBAR, (
                f"el aviso del Gestor es AMBAR: {v.status_label.color!r}"
            )

            # (iter 7, b) LA TARJETA DE LA PORTADA. `_get_pack_button_text` es
            # donde el usuario lee lo que va a hacer el boton ANTES de pulsar, y
            # `execute_pack` decide con `pack.default_action`. Mutar el verbo a
            # un "KILL" literal dejaba TODA la suite en verde: no habia ni un
            # test que atara la tarjeta al dato. Se afirma por la via real
            # (`refresh_dashboard` -> boton real -> `cget("text")`) y en las
            # DOS ramas y en las DOS direcciones, que es lo que distingue "atado
            # al dato" de "acertado hoy".
            class _PacksFavoritos:
                def __init__(self, packs):
                    self.packs = packs

                def get_all_packs(self):
                    return {p.id: p for p in self.packs}

                def get_favorite_packs(self):
                    return [p for p in self.packs if p.is_favorite]

            tarjeta_start = Pack(id="t_start", name="Arranque", is_favorite=True,
                                 apps=list(APPS), default_action="start")
            tarjeta_kill = Pack(id="t_kill", name="Apagado", is_favorite=True,
                                apps=list(APPS), default_action="kill")
            tarjeta_gaming = Pack(id="gaming", name="Gaming Mode", is_favorite=True,
                                  is_gaming=True, apps=list(APPS),
                                  default_action="kill",
                                  target_categories=[CATEGORIA_MEDIA])
            pack_service_real = dash.pack_service
            dash.pack_service = _PacksFavoritos([tarjeta_start, tarjeta_kill,
                                                 tarjeta_gaming])
            dash.process_service = _ProcesosGestor()
            try:
                dash.refresh_dashboard()
                textos_tarjeta = {
                    pid: btn.cget("text")
                    for pid, btn in dash._buttons_by_pack_id.items()
                }
            finally:
                dash.pack_service = pack_service_real
            assert set(textos_tarjeta) == {"t_start", "t_kill", "gaming"}, (
                "la tarjeta tiene que salir del boton REAL que construye "
                f"`refresh_dashboard`: {sorted(textos_tarjeta)}"
            )
            assert "START" in textos_tarjeta["t_start"], (
                "un pack de arrancar no puede anunciarse como 'KILL': la tarjeta "
                f"tiene que decir lo que el boton va a hacer. Dice: "
                f"{textos_tarjeta['t_start']!r}"
            )
            assert "KILL" in textos_tarjeta["t_kill"] and "START" not in textos_tarjeta["t_kill"], (
                f"un pack de apagar no puede anunciarse como 'START': "
                f"{textos_tarjeta['t_kill']!r}"
            )
            assert "KILL" in textos_tarjeta["gaming"] and "START" not in textos_tarjeta["gaming"], (
                "la tarjeta del Gaming Mode sale del MISMO dato que decide la "
                "rama (`default_action`), no de un literal congelado en la "
                f"vista: {textos_tarjeta['gaming']!r}"
            )
            # El control NEGATIVO del arnés: el mismo texto con el otro dato
            # tiene que cambiar. Si `_get_pack_button_text` ignorase el pack,
            # los tres textos serian iguales y las tres aserciones de arriba
            # pasarian por construccion.
            assert textos_tarjeta["t_start"] != textos_tarjeta["t_kill"], (
                "las tarjetas de arrancar y de apagar no pueden decir lo mismo: "
                "el arnés no distinguiria un verbo cableado de uno correcto"
            )
            # Y el gaming de ARRANQUE (posible: `is_gaming` y `default_action`
            # son campos independientes) tiene que decir START, no KILL.
            gaming_de_arranque = Pack(id="g_start", name="Gaming Arranque",
                                      is_favorite=True, is_gaming=True,
                                      apps=list(APPS), default_action="start",
                                      target_categories=[CATEGORIA_MEDIA])
            dash.pack_service = _PacksFavoritos([gaming_de_arranque])
            try:
                dash.refresh_dashboard()
                texto_gaming_arranque = dash._buttons_by_pack_id["g_start"].cget("text")
            finally:
                dash.pack_service = pack_service_real
            assert "START" in texto_gaming_arranque, (
                "un Gaming Mode con `default_action='start'` se INICIA, asi que "
                "su tarjeta no puede prometer 'KILL': "
                f"{texto_gaming_arranque!r}"
            )

            # (iter 7, c) UNA ACCION DESCONOCIDA ES UN FALLO, NO UN "apagar".
            # Con `VERBOS.get(accion, VERBOS["kill"])` un cableado erroneo caia
            # en silencio a "apagar", que es justo la respuesta correcta de la
            # puerta de apagar, asi que el error era invisible (medido: "apagar",
            # "stop" o "Kill" en esa puerta NO mataban la suite). El contrato de
            # los llamantes ya esta comprobado en estatico mas arriba; aqui se
            # comprueba la FRONTERA, que es donde el default silencioso vivía.
            for verbo in sorted(fb.VERBOS.values()):
                try:
                    fb.mensaje_sin_apps("X", verbo)
                except KeyError as exc:
                    assert verbo in str(exc), (
                        "el fallo tiene que NOMBRAR la accion recibida, o el "
                        f"cableado erroneo no se localiza: {exc}"
                    )
                    assert "feedback._verbo" in str(exc), (
                        f"el fallo tiene que nombrar la puerta: {exc}"
                    )
                else:
                    raise AssertionError(
                        f"cablear el VERBO {verbo!r} en la puerta tiene que fallar, "
                        "no devolver un 'apagar' silencioso: ese default es lo que "
                        "hacia invisible el bug del ciclo"
                    )
            for accion_equivoca in ("stop", "Kill", "apagar", "iniciar", ""):
                try:
                    fb._verbo(accion_equivoca)
                except KeyError:
                    pass
                else:
                    raise AssertionError(
                        f"una accion desconocida {accion_equivoca!r} tiene que ser "
                        "un fallo, no un verbo por defecto"
                    )
            # Y el camino bueno no se ha roto al endurecer la puerta.
            assert fb._verbo("kill") == "apagar" and fb._verbo("start") == "iniciar", (
                "las dos acciones validas tienen que seguir dando su verbo"
            )
            assert fb.mensaje_sin_apps("X", "kill")[0].endswith(
                "no tiene apps que apagar. Añádelas desde el Gestor de Procesos."
            ), "el camino bueno de la puerta de apagar cambio de texto"

            # (iter 7, d) LA CADENA CAUSAL, POR LA VIA REAL. El doc y el
            # comentario de la iteracion 6 afirman que "un pack recien creado
            # nace con `default_action='start'`" y que por eso el bug estaba
            # vivo. Esa frase no la media NINGUN test: cambiar el default del
            # modelo a "kill" dejaba los 78 tests en verde. Aqui entra
            # `create_user_pack` DE VERDAD (no un `Pack(...)` con literales) y el
            # pack que devuelve se pasa por la puerta de APAGAR, de modo que la
            # cadena entera queda atada de una vez: si el default del modelo se
            # mueve, el aviso de la puerta de apagar deja de decir "apagar".
            assert pack_s.create_user_pack("recien_real", "Recien Real", []), (
                "precondicion del arnes: el pack recien creado tiene que existir"
            )
            recien_real = pack_s.get_all_packs()["recien_real"]
            assert recien_real.default_action == "start", (
                "un pack recien creado nace con `default_action='start'` (el "
                "default del modelo) y no con 'kill': es lo que hace que "
                "cablear `pack.default_action` en la puerta de apagar diga "
                f"'iniciar'. default_action={recien_real.default_action!r}"
            )
            v = _gestor(recien_real, _ProcesosGestor(), _GamingGestor())
            antes_hilos = len(hilos)
            PackManagerView.kill_pack(v, "recien_real")
            assert len(hilos) == antes_hilos, (
                "un pack recien creado y sin apps no puede lanzar worker"
            )
            assert v.status_label.texto == (
                "⚠️ 'Recien Real' no tiene apps que apagar. "
                "Añádelas desde el Gestor de Procesos."
            ), (
                "cadena completa: `create_user_pack` nace con 'start' y aun asi la "
                "puerta de APAGAR avisa de 'apagar'. Si el texto dice 'iniciar', "
                f"el verbo vuelve a estar cableado al pack: {v.status_label.texto!r}"
            )
            assert v.status_label.color == AMBAR
        finally:
            pmv_mod.threading = threading_real
            dash_mod.threading = threading_real_dash

        dash.destroy()

    finally:
        try:
            root.quit()
            root.destroy()
        except Exception:
            pass
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    print("test_el_feedback_de_pack_dice_la_verdad OK (TASK-035, cierre del ciclo 26).")


def test_el_gestor_de_procesos_tampoco_miente():
    """TASK-035 / ciclo 26 iteracion 3: la TERCERA puerta de feedback.

    El `mutation-auditor` de la iteracion 3 demostro en RUNTIME, con un doble que
    devuelve `(0, 0, 3, 0.0)` (todo en `keepers` o ya muerto), que
    `ProcessManagerView.on_kill_selected` pintaba
    `"<tick> 0 cerrados, 0 fallidos."`: tick de exito, verde, sin haber cerrado
    NADA. Es literalmente el bug que motivo el ciclo 26 entero, en la vista que ni
    el fix de la iteracion 2 ni la guarda AST tocaban, y es la mas grave de las
    tres puertas porque mata UNO A UNO lo que el usuario marco a mano.

    Aqui se entra por `on_kill_selected` DE VERDAD: doble pulsacion, hilo
    secundario real y `after` simulado, y se afirma sobre el TEXTO y el COLOR que
    produjo el codigo en los cuatro desenlaces, incluido `killed == 1` (que
    `clasificar_cierre` con `killed > 1` declaraba "nada").

    Lo que NO comprueba: que `kill_processes` mate de verdad. Aqui no se mata ni un
    proceso; lo que se comprueba es que la vista no se contradiga a si misma
    cuando el servicio le dice lo que ocurrio.
    """
    print("Testing honest kill feedback in ProcessManagerView (TASK-035 / cycle 26 iter 3)...")
    import collections
    from woptimizer.models import ProcessInfo
    from woptimizer.ui.feedback import mensaje_cierre_pack
    from woptimizer.ui.views import process_manager_view as procv_mod
    from woptimizer.ui.views.process_manager_view import ProcessManagerView
    from woptimizer.ui.confirmation import AMBAR, ROJO, VERDE, VENTANA_MS

    # El sustantivo de `mensaje_cierre_pack` NO es decorativo. Con `"procesos"`
    # escrito a pelo dentro del formateador, todo lo de esta seccion seguiria en
    # verde (el unico llamante pasa "procesos") y el parametro seria una mentira mas.
    # Se comprueba con el otro sustantivo, "apps".
    t_apps, c_apps = mensaje_cierre_pack("Trabajo", 2, 0, 0, 8.0, sustantivo="apps")
    assert t_apps == "✅ 2 apps cerrados (8.0 MB liberados) · 'Trabajo'.", (
        f"el sustantivo se usa de verdad, no esta cableado: {t_apps!r}"
    )
    assert c_apps == VERDE
    t_proc, _ = mensaje_cierre_pack("Trabajo", 0, 0, 3, 0.0)
    assert t_proc == "⚠️ 'Trabajo': 0 procesos cerrados, 3 protegidos o ya cerrados.", (
        f"y el valor por defecto sigue siendo 'procesos': {t_proc!r}"
    )
    # (iter 4) El sustantivo tambien se comprueba en la rama NADA, que es la
    # unica de las dos que hoy tiene un llamante de produccion. Cablear
    # `"procesos"` a pelo dentro del formateador dejaba la suite en verde con la
    # comprobacion de arriba, porque los dos llamantes pasan "procesos": es decir,
    # la fila "el sustantivo se ignora" solo era cierta para UNA de las dos ramas
    # que lo usan.
    t_apps_nada, c_apps_nada = mensaje_cierre_pack("Trabajo", 0, 0, 3, 0.0, sustantivo="apps")
    assert t_apps_nada == "⚠️ 'Trabajo': 0 apps cerrados, 3 protegidos o ya cerrados.", (
        f"el sustantivo tambien se usa en la rama 'nada': {t_apps_nada!r}"
    )
    assert c_apps_nada == AMBAR, (
        f"con 0 cerrados y sin error el color es de atencion, sea cual sea el "
        f"sustantivo: {c_apps_nada!r}"
    )

    class _Reloj:
        """Doble de `TkScheduler` con reloj ABSOLUTO (mismo criterio que el de la
        sonda de la portada: `delay <= elapsed` no ordenaria dos plazos iguales)."""

        def __init__(self):
            self.jobs = []
            self.ahora = 0
            self._n = 0

        def schedule(self, delay_ms, callback):
            self._n += 1
            handle = f"job{self._n}"
            self.jobs.append({"id": handle, "vence": self.ahora + delay_ms,
                              "cb": callback, "vivo": True})
            return handle

        def cancel(self, handle):
            for job in self.jobs:
                if job["id"] == handle:
                    job["vivo"] = False
                    return
            raise AssertionError(f"Se cancelo un handle que no existe: {handle!r}")

        def vivos(self):
            return [j for j in self.jobs if j["vivo"]]

        def avanzar(self, ms):
            self.ahora += ms
            vencidos = [j for j in self.jobs if j["vivo"] and j["vence"] <= self.ahora]
            for job in vencidos:
                job["vivo"] = False
            for job in vencidos:
                job["cb"]()
            return [j["id"] for j in vencidos]

    class _Label:
        def __init__(self):
            self.escrituras = []

        def winfo_exists(self):
            return 1

        def configure(self, **kw):
            self.escrituras.append((kw.get("text"), kw.get("text_color")))

        @property
        def texto(self):
            return self.escrituras[-1][0] if self.escrituras else None

        @property
        def color(self):
            return self.escrituras[-1][1] if self.escrituras else None

    class _Casilla:
        def __init__(self, marcado):
            self.marcado = marcado

        def get(self):
            return self.marcado

    class _Procesos:
        """Doble de `ProcessService`: captura lo que llega a `kill_processes` y
        devuelve una 4-tupla fija. No mata nada."""

        def __init__(self):
            self.cierre = (0, 0, 0, 0.0)
            self.recibidos = None
            self.llamadas = 0

        def kill_processes(self, procesos):
            self.llamadas += 1
            self.recibidos = [p.pid for p in procesos]
            return self.cierre

    class _Notis:
        def __init__(self):
            self.eventos = []

        def notify_kill_result(self, killed, failed, freed_mb):
            self.eventos.append((killed, failed, freed_mb))

    cola = collections.deque()
    principal = threading.get_ident()
    hilos = []

    class _HiloEspia(threading.Thread):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            hilos.append(self)

    class _ShimThreading:
        Thread = _HiloEspia

    def _gestor(cierre):
        v = ProcessManagerView.__new__(ProcessManagerView)
        v.status_label = _Label()
        v.btn_kill = None
        # 3 casillas marcadas, pero 4 PIDs: `discord` no esta en `grouped_processes`
        # (puede haber muerto entre el snapshot y la pulsacion). El aviso de
        # confirmacion cuenta CASILLAS y el resultado tambien, asi que el texto
        # dice '3 seleccionadas' aunque se cierren 4 procesos. Con `len(to_kill)`
        # el texto decia '4 seleccionadas' y la confirmacion decia 3.
        v.checkboxes = {"chrome": _Casilla(True), "steam": _Casilla(True),
                        "discord": _Casilla(True)}
        v.grouped_processes = {
            "chrome": [ProcessInfo(name="chrome", full_name="chrome.exe", pid=11),
                       ProcessInfo(name="chrome", full_name="chrome.exe", pid=12)],
            "steam": [ProcessInfo(name="steam", full_name="steam.exe", pid=13),
                      ProcessInfo(name="steam", full_name="steam.exe", pid=14)],
        }
        v.process_service = _Procesos()
        v.process_service.cierre = cierre
        v.notification_service = _Notis()
        v.refreshes = 0
        v.refresh_processes = lambda: setattr(v, "refreshes", v.refreshes + 1)
        v.update_idletasks = lambda: None
        v.reloj = _Reloj()
        v.after = lambda ms, func=None, *a: cola.append((ms, func, a, threading.get_ident()))
        v._init_confirmable(v.status_label, window_ms=VENTANA_MS, scheduler=v.reloj)
        return v

    def _cerrar(v):
        """Pulsa dos veces y aplica en el PRINCIPAL lo que el secundario encolo."""
        antes_hilos, antes_cola = len(hilos), len(cola)
        ProcessManagerView.on_kill_selected(v)          # 1a pulsacion: solo arma
        assert len(hilos) == antes_hilos, (
            "la primera pulsacion no debe matar nada: el usuario marco 3 procesos"
        )
        assert len(cola) == antes_cola, "la primera pulsacion no publica feedback de cierre"
        assert v.status_label.texto == "⚠️ Segunda pulsación para cerrar 3 apps seleccionadas.", (
            f"la primera pulsacion solo arma la confirmacion: {v.status_label.texto!r}"
        )
        assert v.process_service.llamadas == 0, "la primera pulsacion no toca el servicio"

        ProcessManagerView.on_kill_selected(v)          # 2a pulsacion: ejecuta
        nuevos = hilos[antes_hilos:]
        assert len(nuevos) == 1, f"se esperaba 1 worker secundario, se crearon {len(nuevos)}"
        nuevos[0].join(20)
        assert not nuevos[0].is_alive(), "el worker secundario no termino"
        assert v.process_service.llamadas == 1
        assert v.process_service.recibidos == [11, 12, 13, 14], (
            f"se cierran los PIDs de las casillas marcadas, ni uno mas ni uno menos: "
            f"{v.process_service.recibidos}"
        )
        pendientes = list(cola)[antes_cola:]
        assert len(pendientes) == 1, f"el worker debe publicar una sola vez: {pendientes}"
        ms, func, args, ident = pendientes[0]
        assert ms == 0, f"el after debe ser de 0 ms, no de {ms}"
        assert ident != principal, "el after se encolo desde el principal: el secundario no publico nada"
        assert func == v._publicar_cierre, (
            f"el worker debe publicar en _publicar_cierre, no en {func}"
        )
        func(*args)
        return v

    threading_real = procv_mod.threading
    procv_mod.threading = _ShimThreading
    try:
        # (0) NADA CERRADO. Es exactamente el caso que demostro el auditor:
        # (0, 0, 3, 0.0) con tres procesos marcados a mano.
        v = _cerrar(_gestor((0, 0, 3, 0.0)))
        texto, color = v.status_label.texto, v.status_label.color
        assert texto == ("⚠️ '3 seleccionadas': 0 procesos cerrados, "
                         "3 protegidos o ya cerrados."), (
            f"cerrar cero procesos no puede decir '0 cerrados' con tick: {texto!r}"
        )
        assert color != VERDE, f"con 0 cerrados el feedback no puede ser VERDE: {texto!r}"
        assert color == AMBAR, f"sin cierre y sin error, el feedback es de atencion: {color!r}"
        assert "✅" not in texto, f"no hay exito que celebrar: {texto!r}"
        assert "3" in texto, f"el mensaje dice cuantos quedaron intactos: {texto!r}"
        assert v.refreshes == 0, (
            "el refresco de la lista es diferido a 1000 ms, no inmediato"
        )
        pendientes = v.reloj.vivos()
        assert len(pendientes) == 1 and pendientes[0]["vence"] == 1000, (
            f"tras publicar el cierre se programa UN refresco a 1000 ms: {pendientes}"
        )
        v.reloj.avanzar(1000)
        assert v.refreshes == 1, (
            "a los 1000 ms la lista se refresca sola para que el proceso muerto "
            f"desaparezca; hubo {v.refreshes} refrescos"
        )
        assert v.notification_service.eventos == [(0, 0, 0.0)], (
            f"el toast lleva el resultado real: {v.notification_service.eventos}"
        )

        # (1) EXITO REAL. Y `killed == 1` va aqui a proposito: con `failed == 0`
        # sigue siendo exito, y `clasificar_cierre` con `killed > 1` lo degradaba
        # a "nada" sin que ningun caso anterior lo notase.
        v = _cerrar(_gestor((1, 0, 0, 2.5)))
        assert v.status_label.texto == (
            "✅ 1 procesos cerrados (2.5 MB liberados) · '3 seleccionadas'."
        ), f"cerrar un proceso sigue siendo exito: {v.status_label.texto!r}"
        assert v.status_label.color == VERDE

        # (2) PARCIAL: cerro algo y algo fallo -> ni tick ni verde.
        v = _cerrar(_gestor((2, 1, 0, 64.0)))
        texto, color = v.status_label.texto, v.status_label.color
        assert texto == ("⚠️ '3 seleccionadas': 2 cerrados, 1 con error "
                         "(64.0 MB liberados)."), f"detalle del parcial: {texto!r}"
        assert color == AMBAR and "✅" not in texto, (
            f"un cierre parcial no se celebra como exito: {texto!r} / {color!r}"
        )

        # (3) FALLO: no se pudo cerrar NADA.
        v = _cerrar(_gestor((0, 2, 0, 0.0)))
        texto, color = v.status_label.texto, v.status_label.color
        assert texto == "⛔ No se cerró nada de '3 seleccionadas': 2 con error.", (
            f"un cierre fallido es un bloqueo: {texto!r}"
        )
        assert color == ROJO, f"un cierre fallido no se pinta de aviso: {color!r}"
        assert "✅" not in texto

        # (4) `skipped` se cuenta como lo que es: protegidos o ya cerrados, no
        # "fallidos". El mensaje viejo de esta puerta los fundia con `failed`.
        v = _cerrar(_gestor((0, 0, 2, 0.0)))
        texto = v.status_label.texto
        assert "2 protegidos o ya cerrados" in texto and "fallidos" not in texto, (
            f"`skipped` no es `failed`: {texto!r}"
        )

        # (5) Sin seleccion no se mata nada y se dice por que.
        v = _gestor((0, 0, 0, 0.0))
        v.checkboxes = {k: _Casilla(False) for k in v.checkboxes}
        antes_hilos = len(hilos)
        ProcessManagerView.on_kill_selected(v)
        assert len(hilos) == antes_hilos, "sin seleccion marcada no hay worker"
        assert v.status_label.texto == "⚠️ Selecciona procesos primero.", (
            f"sin seleccion hay que decirlo: {v.status_label.texto!r}"
        )
    finally:
        procv_mod.threading = threading_real

    print("test_el_gestor_de_procesos_tampoco_miente OK (TASK-035, ciclo 26 iter 3).")


def test_gaming_service_session_restoration():
    """TASK-038: Valida el registro, consulta, vaciado y restauración de la sesión Gaming."""
    print("Testing GamingService session restoration (TASK-038)...")
    from woptimizer.services.gaming_service import GamingService
    from woptimizer.models import Pack, ProcessInfo

    class DummyProcessService:
        def __init__(self):
            self.started_apps = []
        def _categorize(self, name):
            return "🟢 Navegadores"
        def get_running_processes(self, force_refresh=False):
            return [
                ProcessInfo.model_construct(name="app1", full_name="app1.exe", pid=101, category="🟢 Navegadores"),
                ProcessInfo.model_construct(name="app2", full_name="app2.exe", pid=102, category="🟡 Media"),
            ]
        def get_process_exe_path(self, pid):
            if pid == 101:
                return r"C:\Program Files\App1\app1.exe"
            elif pid == 102:
                return r"C:\Program Files\App2\app2.exe"
            return ""
        def kill_processes(self, procs):
            return len(procs), 0, 0, 50.0
        def start_pack_apps(self, apps):
            self.started_apps = list(apps)
            return len(apps), 0

    class DummyPackService:
        pass

    ps = DummyProcessService()
    gs = GamingService(ps, DummyPackService())

    # Precondición: sin sesión guardada
    assert gs.get_last_closed_apps() == []

    gaming_pack = Pack(id="gaming", name="Gaming", is_gaming=True, target_categories=["🟢 Navegadores", "🟡 Media"])
    killed, failed, skipped, freed_mb = gs.execute_gaming_pack(gaming_pack)
    assert killed == 2

    closed_apps = gs.get_last_closed_apps()
    assert len(closed_apps) == 2
    assert r"C:\Program Files\App1\app1.exe" in closed_apps
    assert r"C:\Program Files\App2\app2.exe" in closed_apps

    # Probando clear_last_closed_apps
    gs_dummy = GamingService(ps, DummyPackService())
    gs_dummy._last_closed_apps = ["test.exe"]
    gs_dummy.clear_last_closed_apps()
    assert gs_dummy.get_last_closed_apps() == []

    # Simular restauración
    started, failed_rest = gs.restore_gaming_session()
    assert started == 2
    assert failed_rest == 0
    assert ps.started_apps == closed_apps
    assert gs.get_last_closed_apps() == []  # debe haberse vaciado

    print("test_gaming_service_session_restoration OK.")


def test_pack_service_cache_invalidation_and_immutability():
    """TASK-040: Valida la caché inmutable de 2 capas en PackService.get_all_packs()
    y su invalidación atómica al mutar packs.
    """
    print("Testing PackService cache invalidation and immutability (TASK-040)...")
    import tempfile, os, time, shutil
    from woptimizer.services.pack_service import PackService
    from woptimizer.models import Pack

    tmp_dir = tempfile.mkdtemp(prefix="wopt_t040_")
    data_path = os.path.join(tmp_dir, "profiles.json")
    try:
        ps = PackService(data_path=data_path)
        
        # 1) Primera lectura llena la caché
        t0 = time.perf_counter()
        packs1 = ps.get_all_packs()
        t1 = time.perf_counter()
        assert ps._cached_all_packs is not None, "La caché interna debe poblarse tras get_all_packs()"
        
        # 1b) Identidad de 1ª capa: _cached_all_packs debe contener copias independientes de _data.packs
        assert ps._data.packs["gaming"] is not ps._cached_all_packs["gaming"], \
            "Los objetos en _cached_all_packs deben ser copias independientes de _data.packs (1ª capa inmutable)"
        
        # 2) Segunda lectura usa la caché (defensiva) y debe ser ultra rápida (< 1.0 ms)
        t2 = time.perf_counter()
        packs2 = ps.get_all_packs()
        t3 = time.perf_counter()
        read_latency_ms = (t3 - t2) * 1000
        assert read_latency_ms < 1.0, f"Latencia de lectura en caché demasiado alta: {read_latency_ms:.3f} ms"
        
        # 3) Inmutabilidad: modificar la copia devuelta NO debe afectar a la caché ni al estado interno
        packs1["gaming"].apps.append("malicious_app.exe")
        assert "malicious_app.exe" not in ps._cached_all_packs["gaming"].apps, \
            "Mutar la lista devuelta por get_all_packs no debe contaminar la caché de 2 capas"
        assert "malicious_app.exe" not in ps._data.packs["gaming"].apps, \
            "Mutar la lista devuelta no debe contaminar el modelo interno en _data"

        # 4) Inmutabilidad del argumento en update_pack() y su invalidación
        custom_pack = Pack(id="custom", name="Custom Pack", apps=["notepad.exe"])
        ps.update_pack(custom_pack)
        assert ps._cached_all_packs is None, "update_pack() debe invalidar la caché (fijar _cached_all_packs a None)"
        
        custom_pack.apps.append("unwanted.exe")
        assert "unwanted.exe" not in ps.get_all_packs()["custom"].apps, \
            "Mutar la instancia enviada a update_pack() no debe contaminar el modelo interno ni la caché"
            
        # 5) load() debe invalidar la caché existente
        ps.get_all_packs()
        assert ps._cached_all_packs is not None
        ps.load()
        assert ps._cached_all_packs is None, "load() debe invalidar la caché existente"
            
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    print("test_pack_service_cache_invalidation_and_immutability OK.")


def test_process_filter_performance():
    """TASK-040: Valida que el filtrado de lista de procesos (< 350 items) tome < 2.0 ms."""
    print("Testing process filter performance (TASK-040)...")
    import time
    from woptimizer.models import ProcessInfo

    # Crear 350 mock processes
    mock_procs = [
        ProcessInfo(
            pid=1000 + i,
            name=f"process_{i}.exe",
            full_name=f"process_{i}.exe",
            category="🎮 Gaming & Launchers" if i % 2 == 0 else "🌐 Navegadores & Web",
            cpu_percent=1.5,
            memory_info={"rss": 50 * 1024 * 1024},
            status="running"
        )
        for i in range(350)
    ]
    
    # Pre-tokenizar nombres
    tokens = {p.pid: f"{p.name} {p.category}".lower() for p in mock_procs}
    query = "process_12"

    t0 = time.perf_counter()
    filtered_pids = [pid for pid, token in tokens.items() if query in token]
    t1 = time.perf_counter()
    
    filter_latency_ms = (t1 - t0) * 1000
    assert len(filtered_pids) > 0, "El filtro debe retornar coincidencias"
    assert filter_latency_ms < 2.0, f"Latencia de filtrado demasiado alta: {filter_latency_ms:.3f} ms"

    print("test_process_filter_performance OK.")


def test_pydantic_extra_fields_persistence():
    """TASK-041 (Ciclo #31): Valida que campos extra no estándar en AppData y Pack
    preserven su valor en disco tras ciclos completos de load() y save().
    """
    print("Testing pydantic extra fields persistence (TASK-041)...")
    import tempfile, os, json, shutil
    from woptimizer.services.pack_service import PackService

    tmp_dir = tempfile.mkdtemp(prefix="wopt_t041_")
    data_path = os.path.join(tmp_dir, "profiles.json")
    try:
        # JSON inicial con campos extra no estándar en la raíz y en el pack gaming
        raw_initial = {
            "version_custom": "3.1.0-alpha",
            "packs": {
                "gaming": {
                    "id": "gaming",
                    "name": "Modo Gaming",
                    "apps": ["steam.exe"],
                    "is_favorite": True,
                    "is_gaming": True,
                    "custom_pack_tag": "high_performance",
                    "launch_arguments": "--novid -high"
                }
            }
        }
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(raw_initial, f)

        # Cargar con PackService y forzar save()
        ps = PackService(data_path=data_path)
        ps.save()

        # Re-leer archivo JSON crudo desde disco para verificar persistencia
        with open(data_path, encoding="utf-8") as f:
            raw_saved = json.load(f)

        assert raw_saved.get("version_custom") == "3.1.0-alpha", \
            "El campo extra 'version_custom' en la raíz no debe ser descartado al guardar"
        assert raw_saved["packs"]["gaming"].get("custom_pack_tag") == "high_performance", \
            "El campo extra 'custom_pack_tag' del pack no debe ser descartado al guardar"
        assert raw_saved["packs"]["gaming"].get("launch_arguments") == "--novid -high", \
            "El campo extra 'launch_arguments' del pack no debe ser descartado al guardar"

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    print("test_pydantic_extra_fields_persistence OK.")


def test_freed_mb_calculation_precision():
    """TASK-041 (Ciclo #31): Valida la precisión aritmética en el cálculo de freed_mb
    en ProcessService.kill_processes (suma RSS de padre e hijos y redondeo a 2 decimales).
    """
    print("Testing freed_mb calculation precision (TASK-041)...")
    from unittest.mock import patch, MagicMock
    from woptimizer.services.process_service import ProcessService
    from woptimizer.models import ProcessInfo

    mock_parent = MagicMock()
    mock_parent.memory_info.return_value = MagicMock(rss=15728640)  # 15.0 MiB
    
    mock_child1 = MagicMock()
    mock_child1.memory_info.return_value = MagicMock(rss=7864320)   # 7.5 MiB
    mock_child2 = MagicMock()
    mock_child2.memory_info.return_value = MagicMock(rss=2621440)   # 2.5 MiB
    
    mock_parent.children.return_value = [mock_child1, mock_child2]

    ps = ProcessService()
    pinfo = ProcessInfo(
        pid=9999,
        name="test_target_proc.exe",
        full_name="test_target_proc.exe",
        category="🌐 Navegadores & Web",
        cpu_percent=0.0,
        memory_info={"rss": 15728640},
        status="running"
    )

    with patch("psutil.Process", return_value=mock_parent):
        killed, failed, skipped, freed_mb = ps.kill_processes([pinfo])

    assert killed == 1, f"Se esperaba 1 proceso matado, obtenido {killed}"
    assert freed_mb == 25.0, f"Se esperaba freed_mb == 25.0 devuelto por ProcessService.kill_processes, obtenido {freed_mb}"

    print("test_freed_mb_calculation_precision OK.")


def test_notification_service_rlock_and_concurrency():
    """TASK-042 (Ciclo #32): Valida que NotificationService usa RLock, soporta reentrancia
    y se comporta de forma segura bajo concurrencia multihilo.
    """
    print("Testing NotificationService RLock y concurrencia (TASK-042)...")
    import threading
    from woptimizer.services.notification_service import NotificationService

    svc = NotificationService()
    assert isinstance(svc._lock, type(threading.RLock())), "NotificationService._lock debe ser RLock"

    # Test de reentrancia
    with svc._lock:
        with svc._lock:
            res = svc.notify("Reentrant", "Testing reentrancy lock")
            assert isinstance(res, bool)

    # Test multihilo
    errors = []

    def worker(idx):
        try:
            for _ in range(20):
                svc.attach_tray(None)
                svc.notify(f"Title {idx}", f"Message {idx}")
                svc.detach_tray()
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(5)

    assert not errors, f"Excepciones durante concurrencia multihilo en NotificationService: {errors}"
    print("test_notification_service_rlock_and_concurrency OK.")


def test_process_service_kill_defensive_zombie_and_oserror():
    """TASK-042 (Ciclo #32): Valida la captura defensiva de psutil.ZombieProcess y OSError
    en kill_processes y kill_pack_apps de ProcessService.
    """
    print("Testing ProcessService kill defensive ZombieProcess y OSError (TASK-042)...")
    import psutil
    from unittest.mock import patch, MagicMock
    from woptimizer.services.process_service import ProcessService
    from woptimizer.models import ProcessInfo

    ps = ProcessService()

    # 1. Simular ZombieProcess al consultar hijos
    mock_parent = MagicMock()
    mock_parent.memory_info.return_value = MagicMock(rss=10485760)  # 10 MiB
    mock_parent.children.side_effect = psutil.ZombieProcess(pid=8888)

    pinfo = ProcessInfo(
        pid=8888,
        name="zombie_app.exe",
        full_name="zombie_app.exe",
        category="🌐 Navegadores & Web",
        cpu_percent=0.0,
        memory_info={"rss": 10485760},
        status="zombie"
    )

    with patch("psutil.Process", return_value=mock_parent):
        killed, failed, skipped, freed_mb = ps.kill_processes([pinfo])
        assert killed == 1
        assert freed_mb == 10.0

    # 2. Simular ZombieProcess en kill() del padre
    mock_parent_zombie = MagicMock()
    mock_parent_zombie.memory_info.return_value = MagicMock(rss=5242880)
    mock_parent_zombie.children.return_value = []
    mock_parent_zombie.kill.side_effect = psutil.ZombieProcess(pid=7777)

    pinfo_zombie = ProcessInfo(
        pid=7777,
        name="zombie_parent.exe",
        full_name="zombie_parent.exe",
        category="🌐 Navegadores & Web",
        cpu_percent=0.0,
        memory_info={"rss": 5242880},
        status="zombie"
    )

    with patch("psutil.Process", return_value=mock_parent_zombie):
        killed, failed, skipped, freed_mb = ps.kill_processes([pinfo_zombie])
        assert skipped == 1
        assert killed == 0

    # 3. Simular OSError en kill() del padre
    mock_parent_oserror = MagicMock()
    mock_parent_oserror.memory_info.return_value = MagicMock(rss=5242880)
    mock_parent_oserror.children.return_value = []
    mock_parent_oserror.kill.side_effect = OSError("WinError 5 Access Denied")

    with patch("psutil.Process", return_value=mock_parent_oserror):
        killed, failed, skipped, freed_mb = ps.kill_processes([pinfo_zombie])
        assert failed == 1
        assert killed == 0

    print("test_process_service_kill_defensive_zombie_and_oserror OK.")


def test_tray_session_restoration_integration():
    """TASK-043 (Ciclo #33): Valida la integración de la opción '🔄 Reabrir aplicaciones cerradas'
    en el menú contextual del system tray y la notificación nativa resultante.
    """
    print("Testing tray session restoration integration (TASK-043)...")
    import time
    from unittest.mock import MagicMock, patch
    from woptimizer.ui.app import WOptimizerApp

    mock_proc_svc = MagicMock()
    mock_pack_svc = MagicMock()
    mock_gaming_svc = MagicMock()

    mock_gaming_svc.restore_gaming_session.return_value = (2, 0)

    with patch("customtkinter.CTk"), patch("woptimizer.ui.app.MainWindow"):
        app = WOptimizerApp(
            process_service=mock_proc_svc,
            pack_service=mock_pack_svc,
            gaming_service=mock_gaming_svc,
            autostart_tray=False
        )

        with patch("pystray.MenuItem") as mock_menu_item, patch("pystray.Icon") as mock_icon_cls:
            mock_icon_instance = MagicMock()
            mock_icon_cls.return_value = mock_icon_instance

            app.show_tray()

            item_titles = [call.args[0] for call in mock_menu_item.call_args_list if call.args]
            assert "🔄 Reabrir aplicaciones cerradas" in item_titles, \
                f"El menú del tray debe incluir '🔄 Reabrir aplicaciones cerradas', obtenidos: {item_titles}"

            restore_cb = None
            for call in mock_menu_item.call_args_list:
                if call.args and call.args[0] == "🔄 Reabrir aplicaciones cerradas":
                    restore_cb = call.args[1]
                    break

            assert restore_cb is not None, "Se debe asociar un callback a '🔄 Reabrir aplicaciones cerradas'"

            with patch("threading.Thread") as mock_thread_cls, \
                 patch.object(app.notification_service, "notify_apps_launched") as mock_notify_launched:
                mock_thread_inst = MagicMock()
                mock_thread_cls.return_value = mock_thread_inst

                def _inline_start():
                    target = mock_thread_cls.call_args.kwargs.get("target") or mock_thread_cls.call_args[1].get("target")
                    target()

                mock_thread_inst.start.side_effect = _inline_start

                restore_cb(mock_icon_instance, None)

                assert mock_thread_cls.called, "restore_cb DEBE instanciar un threading.Thread"
                daemon_flag = mock_thread_cls.call_args.kwargs.get("daemon")
                assert daemon_flag is True, "El hilo de restauración debe crearse con daemon=True"
                assert mock_thread_inst.start.called, "El hilo de restauración debe ser iniciado con start()"

                mock_gaming_svc.restore_gaming_session.assert_called_once()
                mock_notify_launched.assert_called_once_with("Restauración Gaming", 2, 0)

            # Escenario 2: Sin apps pendientes (0, 0) (Discriminación M5)
            mock_gaming_svc.restore_gaming_session.reset_mock()
            mock_gaming_svc.restore_gaming_session.return_value = (0, 0)

            with patch("threading.Thread") as mock_thread_cls, \
                 patch.object(app.notification_service, "notify") as mock_notify_simple:
                mock_thread_inst = MagicMock()
                mock_thread_cls.return_value = mock_thread_inst

                def _inline_start_2():
                    target = mock_thread_cls.call_args.kwargs.get("target") or mock_thread_cls.call_args[1].get("target")
                    target()

                mock_thread_inst.start.side_effect = _inline_start_2

                restore_cb(mock_icon_instance, None)

                mock_gaming_svc.restore_gaming_session.assert_called_once()
                mock_notify_simple.assert_called_once_with(
                    "woptimizer", "No hay aplicaciones pendientes de restauración."
                )

    print("test_tray_session_restoration_integration OK.")


def test_process_categorization_latency_and_memoization():
    """TASK-045: Memoización de categorización de procesos e invalidación atómica.

    Verifica que:
    1. _categorize memoiza el resultado en _meta_cache.
    2. Llamadas posteriores retornan la categoría memoizada O(1) sin consultar _db_map
       (discriminante estricto: al vaciar _db_map, el hit O(1) preserva la categoría
       catalogada y NO cae en el fallback _DEFAULT_META).
    3. Entradas sintéticas inyectadas en _meta_cache se resuelven de inmediato sin pasar por _db_map.
    4. Fallback de proceso desconocido también se memoiza.
    5. _load_local_db() vacía _meta_cache e invalida atómicamente _proc_cache (deja _proc_cache en None).
    """
    from woptimizer.services.process_service import ProcessService, _DEFAULT_META

    svc = ProcessService()
    # 1. Proceso catalogado en DB: debe memoizarse en _meta_cache con su categoría específica
    cat_chrome = svc._categorize("chrome")
    assert cat_chrome != _DEFAULT_META[0], "chrome debe tener categoría catalogada diferente del fallback"
    assert "chrome" in svc._meta_cache

    # 2. Vaciar _db_map para probar que la segunda consulta usa el caché O(1)
    svc._db_map = {}
    cat_chrome_cached = svc._categorize("chrome")
    assert cat_chrome_cached == cat_chrome, (
        f"Debe retornar la categoría desde _meta_cache O(1) incluso con _db_map vacío: {cat_chrome_cached!r}"
    )

    # 3. Discriminación sintética adicional: entrada única que solo existe en _meta_cache
    sentinel_cat = "CATEGORIA_CENTINELA_MEMOIZADA"
    svc._meta_cache["app_sintetica_test"] = (sentinel_cat, "high", "Desc test")
    assert svc._categorize("app_sintetica_test") == sentinel_cat, (
        "La resolución debe devolver el valor memoizado directamente desde _meta_cache"
    )

    # 4. Fallback de proceso desconocido también se memoiza
    cat_unk = svc._categorize("proceso_totalmente_desconocido_xyz")
    assert cat_unk == _DEFAULT_META[0]
    assert "proceso_totalmente_desconocido_xyz" in svc._meta_cache

    # 5. Simular caché de procesos activo y verificar invalidación atómica en _load_local_db
    svc._proc_cache = []
    svc._load_local_db()
    assert len(svc._meta_cache) == 0, "_meta_cache debe vaciarse al recargar la DB"
    assert svc._proc_cache is None, "_proc_cache debe quedar en None tras invalidate_cache() en _load_local_db()"

    print("test_process_categorization_latency_and_memoization OK.")


def test_confirmable_mixin_lifecycle_and_widget_contracts():
    """TASK-046 (Ciclo #36): Contratos de ciclo de vida, widgets y estados en Confirmable mixin.

    Valida:
      1. Inicialización y 1ª pulsación: muta a PENDIENTE_TEXT, PENDIENTE_FG, PENDIENTE_HOVER,
         status_label en AMBAR, retorna False.
      2. 2ª pulsación: retorna True (confirmado), botón restaurado y deshabilitado temporalmente
         (REHABILITAR_MS = 300 ms en _timers_ui). Al avanzar reloj a 300 ms, vuelve a 'normal'.
      3. Sustitución de token (changed_text): nuevo token sin confirmar el anterior actualiza
         status_label con changed_text y rearma la ventana.
      4. Auto-expiración: a los window_ms (3000 ms), dispara _on_expirado, restaura botón
         a reposo y status_label muestra MSG_EXPIRADO.
      5. Cancelación explícita (_cancel_confirm): restaura botón a reposo sin ejecutar.
      6. Limpieza en destrucción (cancel_on_destroy): cancela timers del guard y _timers_ui.
      7. Tolerancia a widgets destruidos: winfo_exists() == False no lanza excepciones.
    """
    print("Testing Confirmable mixin lifecycle and widget contracts (TASK-046)...")
    from woptimizer.ui.confirmation import (
        Confirmable,
        PENDIENTE_TEXT,
        PENDIENTE_FG,
        PENDIENTE_HOVER,
        AMBAR,
        MSG_EXPIRADO,
        REHABILITAR_MS,
    )

    class DummyButton:
        def __init__(self, text="Matar", fg_color="#c22d2d", hover_color="#8a1e1e", state="normal"):
            self.props = {"text": text, "fg_color": fg_color, "hover_color": hover_color, "state": state}
            self.alive = True

        def cget(self, key):
            return self.props[key]

        def configure(self, **kwargs):
            self.props.update(kwargs)

        def winfo_exists(self):
            return self.alive

    class DummyLabel:
        def __init__(self, text="", text_color="gray"):
            self.props = {"text": text, "text_color": text_color}
            self.alive = True

        def cget(self, key):
            return self.props[key]

        def configure(self, **kwargs):
            self.props.update(kwargs)

        def winfo_exists(self):
            return self.alive

    class DummyView(Confirmable):
        def __init__(self, label, sched):
            self._init_confirmable(status_label=label, scheduler=sched, window_ms=3000)

    sched = _FakeScheduler()
    lbl = DummyLabel()
    view = DummyView(lbl, sched)
    btn = DummyButton(text="Eliminar Pack", fg_color="#c22d2d", hover_color="#8a1e1e")

    # 1. Primera pulsación: arma pendiente, no ejecuta (False)
    confirmed = view._require_double_tap("pack:1", button=btn, label="¿Seguro que deseas eliminar?")
    assert confirmed is False, "La primera pulsación debe retornar False (solo armar)"
    assert btn.cget("text") == PENDIENTE_TEXT, f"Botón debe mutar a PENDIENTE_TEXT, got {btn.cget('text')}"
    assert btn.cget("fg_color") == PENDIENTE_FG, f"Botón debe mutar a PENDIENTE_FG, got {btn.cget('fg_color')}"
    assert btn.cget("hover_color") == PENDIENTE_HOVER
    assert lbl.cget("text") == "¿Seguro que deseas eliminar?"
    assert lbl.cget("text_color") == AMBAR
    assert view._guard.is_pending("pack:1") is True

    # 2. Segunda pulsación: confirma (True), restaura propiedades originales y aplica throttling 300ms
    confirmed_2 = view._require_double_tap("pack:1", button=btn)
    assert confirmed_2 is True, "La segunda pulsación debe retornar True (ejecutar acción)"
    assert btn.cget("text") == "Eliminar Pack", "Botón debe restaurar su texto original de reposo"
    assert btn.cget("fg_color") == "#c22d2d", "Botón debe restaurar su fg_color original"
    assert btn.cget("hover_color") == "#8a1e1e"
    assert btn.cget("state") == "disabled", "Botón debe quedar deshabilitado temporalmente (throttling)"
    assert len(view._timers_ui) == 1, "Debe haber 1 timer encolado en _timers_ui para re-habilitar el botón"

    # Avanzar reloj 300 ms para completar rehabilitación
    sched.fire_due(REHABILITAR_MS)
    assert btn.cget("state") == "normal", "Tras REHABILITAR_MS, el botón debe volver a state='normal'"
    assert len(view._timers_ui) == 0, "_timers_ui debe quedar limpio tras expirar el timer de rehabilitación"

    # 3. Sustitución de token con changed_text
    btn_a = DummyButton("Accion A")
    btn_b = DummyButton("Accion B")
    view._require_double_tap("token_A", button=btn_a, label="Pulsaste A")
    assert lbl.cget("text") == "Pulsaste A"
    assert btn_a.cget("text") == PENDIENTE_TEXT

    # Pulsar token_B sin confirmar A
    view._require_double_tap("token_B", button=btn_b, label="Pulsaste B", changed_text="⚠️ Selección cambiada.")
    assert lbl.cget("text") == "⚠️ Selección cambiada.", "Al cambiar token debe presentarse changed_text"
    assert btn_b.cget("text") == PENDIENTE_TEXT
    assert view._guard.is_pending("token_B") is True
    assert view._guard.is_pending("token_A") is False

    # 4. Auto-expiración a los 3000 ms
    sched.fire_due(3000)
    assert view._guard.is_pending() is False, "El guard debe expirar a los 3000 ms"
    assert btn_b.cget("text") == "Accion B", "El botón debe volver a reposo al expirar"
    assert lbl.cget("text") == MSG_EXPIRADO, f"Al expirar debe mostrar MSG_EXPIRADO, got {lbl.cget('text')}"
    assert view._boton_pendiente is None

    # 5. Cancelación explícita (_cancel_confirm)
    btn_c = DummyButton("Accion C")
    view._require_double_tap("token_C", button=btn_c, label="Pulsaste C")
    assert view._guard.is_pending("token_C") is True
    view._cancel_confirm()
    assert view._guard.is_pending() is False
    assert btn_c.cget("text") == "Accion C"
    assert view._boton_pendiente is None

    # 6. Limpieza defensiva en cancel_on_destroy con timers activos (throttling)
    btn_t = DummyButton("Throttle")
    view._require_double_tap("token_T", button=btn_t, label="Pulsaste T")
    view._require_double_tap("token_T", button=btn_t)  # 2ª pulsación: confirmed, encola timer de rehabilitación
    assert len(view._timers_ui) == 1, "Debe haber 1 timer de throttling encolado en _timers_ui"
    vivos_antes = len(sched.vivos())
    assert vivos_antes >= 1, "El scheduler debe tener al menos un timer activo"
    view.cancel_on_destroy()
    assert view._guard.is_pending() is False
    assert view._boton_pendiente is None
    assert len(view._timers_ui) == 0, "cancel_on_destroy debe vaciar _timers_ui"
    assert len(sched.vivos()) < vivos_antes, "cancel_on_destroy debe cancelar los timers pendientes en el scheduler"

    # 7. Resiliencia ante widgets destruidos (winfo_exists() == False)
    btn_dead = DummyButton("Muerto")
    btn_dead.alive = False
    assert view._configurar(btn_dead, text="Nuevo") is False, "Widget destruido debe rechazar configuración sin lanzar excepción"

    # 8. Limpieza completa de reposo en recreación de botones (_forget_buttons)
    btn_f = DummyButton("Accion F")
    view._recordar_reposo("token_F", btn_f)
    assert "token_F" in view._reposo, "_reposo debe contener token_F antes de _forget_buttons"
    view._forget_buttons()
    assert len(view._reposo) == 0, "_forget_buttons() debe limpiar _reposo completamente"
    assert view._guard.is_pending() is False, "_forget_buttons() debe llamar a cancel_on_destroy()"

    print("test_confirmable_mixin_lifecycle_and_widget_contracts OK.")


def test_gaming_service_rlock_and_concurrency():
    """TASK-047 (Ciclo #37): Resiliencia de concurrencia y recuperación en GamingService.

    Valida:
      1. Presencia de RLock reentrante en GamingService._lock.
      2. Thread-safety: 5 hilos concurrentes llamando a restore_gaming_session()
         no duplican ejecuciones de start_pack_apps (exactamente 1 ejecución de lote).
      3. Preservación defensiva de _last_closed_apps ante fallos/excepciones imprevistas.
      4. Aislamiento de excepciones no-OSError en ProcessService.start_pack_apps.
    """
    print("Testing GamingService RLock and concurrency resilience (TASK-047)...")
    import threading
    import time
    from unittest.mock import MagicMock
    from woptimizer.services.gaming_service import GamingService
    from woptimizer.services.process_service import ProcessService
    from woptimizer.services.pack_service import PackService

    # 1. RLock reentrante
    mock_ps = MagicMock(spec=ProcessService)
    mock_packs = MagicMock(spec=PackService)
    gs = GamingService(mock_ps, mock_packs)

    assert hasattr(gs, "_lock"), "GamingService debe poseer un cerrojo _lock"
    assert isinstance(gs._lock, type(threading.RLock())), "GamingService._lock debe ser de tipo threading.RLock"
    # Reentrancia
    with gs._lock:
        with gs._lock:
            pass

    # 1b. Exclusión mutua real en restore_gaming_session (mata M2)
    gs._last_closed_apps = ["C:\\app_lock.exe"]
    lock_held = threading.Event()
    release_lock = threading.Event()

    def hold_lock():
        with gs._lock:
            lock_held.set()
            release_lock.wait(timeout=2.0)

    t_holder = threading.Thread(target=hold_lock, daemon=True)
    t_holder.start()
    assert lock_held.wait(timeout=2.0), "t_holder no pudo adquirir el cerrojo a tiempo"

    t_restore = threading.Thread(target=gs.restore_gaming_session, daemon=True)
    t_restore.start()
    time.sleep(0.02)

    try:
        # Si restore_gaming_session no usa with self._lock:, vaciaría _last_closed_apps de inmediato sin esperar
        assert gs._last_closed_apps == ["C:\\app_lock.exe"], (
            "restore_gaming_session debe respetar self._lock y no vaciar apps mientras el cerrojo está tomado"
        )
    finally:
        release_lock.set()
        t_holder.join(timeout=1.0)
        t_restore.join(timeout=1.0)

    assert gs.get_last_closed_apps() == [], "Tras liberarse el cerrojo, restore_gaming_session debe vaciar apps"

    # 2. Concurrencia de 5 hilos en restore_gaming_session
    gs._last_closed_apps = ["C:\\app1.exe", "C:\\app2.exe"]
    call_count = 0
    call_lock = threading.Lock()

    def delayed_start_pack_apps(apps):
        nonlocal call_count
        with call_lock:
            call_count += 1
        time.sleep(0.03)
        return (len(apps), 0)

    mock_ps.start_pack_apps.side_effect = delayed_start_pack_apps

    results = []
    threads = []
    def worker():
        res = gs.restore_gaming_session()
        results.append(res)

    for _ in range(5):
        t = threading.Thread(target=worker, daemon=True)
        threads.append(t)
        t.start()

    for t in threads:
        t.join(timeout=2.0)

    assert call_count == 1, f"start_pack_apps debió ser invocado exactamente 1 vez, invocado {call_count}"
    assert (2, 0) in results, "Exactamente 1 hilo debió recibir la tupla de éxito (2, 0)"
    assert results.count((0, 0)) == 4, f"4 hilos debieron recibir (0, 0), recibidos: {results}"
    assert gs.get_last_closed_apps() == [], "El historial _last_closed_apps debe quedar vacío tras restauración"

    # 3. Preservación defensiva ante excepciones en start_pack_apps
    gs._last_closed_apps = ["C:\\crash_app.exe", "C:\\save_me.exe"]
    mock_ps.start_pack_apps.side_effect = RuntimeError("Simulated start failure")

    exception_raised = False
    try:
        gs.restore_gaming_session()
    except RuntimeError:
        exception_raised = True

    assert exception_raised is True, "restore_gaming_session debe propagar la excepción hacia el llamante"
    assert gs.get_last_closed_apps() == ["C:\\crash_app.exe", "C:\\save_me.exe"], (
        "Las apps cerradas deben preservarse íntegramente ante fallos imprevistos en start_pack_apps"
    )

    # 4. Aislamiento en ProcessService.start_pack_apps ante excepciones no-OSError
    real_ps = ProcessService()
    launched = []

    def mock_resolver(app):
        if app == "boom.exe":
            raise RuntimeError("Corrupted executable path resolution")
        return f"C:\\dummy\\{app}"

    real_ps._resolver_app = mock_resolver
    real_ps._lanzar = lambda ruta: launched.append(ruta)

    started, failed = real_ps.start_pack_apps(["boom.exe", "ok.exe"])
    assert failed == 1, "La app con fallo no-OSError debe sumarse a failed"
    assert started == 1, "La app válida subsiguiente debe arrancarse exitosamente"
    assert launched == ["C:\\dummy\\ok.exe"]

    print("test_gaming_service_rlock_and_concurrency OK.")


def test_dashboard_favorite_grid_adaptive_contracts():
    """TASK-049: Rejilla adaptativa al ancho de ventana para favoritos en DashboardView."""
    print("Testing DashboardView adaptive favorites grid contracts...")
    import customtkinter as ctk
    from woptimizer.ui import theme
    from woptimizer.ui.views.dashboard_view import DashboardView
    from woptimizer.models import Pack

    # 1. Contrato de token centralizado en theme.py
    assert hasattr(theme, "ANCHO_MIN_CARD"), "theme.py debe exportar ANCHO_MIN_CARD"
    assert theme.ANCHO_MIN_CARD == 280, f"ANCHO_MIN_CARD esperado 280, recibido {theme.ANCHO_MIN_CARD}"

    class _FakePS:
        def get_running_processes(self):
            return []

    class _FakePackS:
        def __init__(self, num_packs=4):
            self.packs = {
                f"pack_{i}": Pack(id=f"pack_{i}", name=f"Pack {i}", is_favorite=True)
                for i in range(num_packs)
            }
        def get_all_packs(self):
            return self.packs
        def get_favorite_packs(self):
            return [p for p in self.packs.values() if p.is_favorite]

    class _FakeGS:
        def get_last_closed_apps(self):
            return []

    class _FakeNS:
        pass

    root = ctk.CTk()
    root.withdraw()
    try:
        pack_service = _FakePackS(4)
        dash = DashboardView(root, _FakePS(), pack_service, _FakeNS(), _FakeGS())

        # 2. Con 4 favoritos y ancho de 1200 px:
        # max_cols = 1200 // 280 = 4 columnas.
        # Todos los botones deben ubicarse en la fila 0: (0, 0), (0, 1), (0, 2), (0, 3)
        dash.buttons_frame.winfo_width = lambda: 1200
        dash.refresh_dashboard()
        assert len(dash._buttons_by_pack_id) == 4

        btn_3 = dash._buttons_by_pack_id["pack_3"]
        info_3 = btn_3.grid_info()
        assert info_3["row"] == 0 and info_3["column"] == 3, (
            f"Con 1200px y 4 favoritos, pack_3 debe estar en row 0 col 3, recibido: row {info_3['row']} col {info_3['column']}"
        )

        # 3. Re-grid adaptativo activado por evento <Configure> (ancho reducido a 600 px):
        # max_cols = 600 // 280 = 2 columnas.
        # Fila 0: (0, 0), (0, 1) | Fila 1: (1, 0), (1, 1).
        dash.buttons_frame.winfo_width = lambda: 600

        class _FakeEvent:
            def __init__(self, widget):
                self.widget = widget

        # Evento desde widget ajeno: NO debe regriddear (pack_3 sigue en col 3)
        dash._on_frame_configure(_FakeEvent(dash.status_label))
        info_3_ignored = btn_3.grid_info()
        assert info_3_ignored["row"] == 0 and info_3_ignored["column"] == 3, (
            "Evento de widget ajeno no debe provocar re-grid de favoritos"
        )

        # Evento desde buttons_frame: DEBE regriddear
        dash._on_frame_configure(_FakeEvent(dash.buttons_frame))
        info_3_regrid = btn_3.grid_info()
        assert info_3_regrid["row"] == 1 and info_3_regrid["column"] == 1, (
            f"Tras reducir a 600px vía <Configure>, pack_3 debe moverse a row 1 col 1, recibido: row {info_3_regrid['row']} col {info_3_regrid['column']}"
        )

        # 4. Las columnas sobrantes sueltan el peso (peso 0 para cols 2 y 3)
        w2 = dash.buttons_frame.grid_columnconfigure(2)["weight"]
        w3 = dash.buttons_frame.grid_columnconfigure(3)["weight"]
        assert w2 == 0, f"Columna 2 debe tener peso 0 al reducir columnas, tiene {w2}"
        assert w3 == 0, f"Columna 3 debe tener peso 0 al reducir columnas, tiene {w3}"

        # 5. Placeholder de estado vacío ocupa todas las columnas calculadas y responde a resize
        pack_service.packs.clear()
        dash.buttons_frame.winfo_width = lambda: 600
        dash.refresh_dashboard()
        assert dash._empty_label is not None, "El placeholder _empty_label debe existir con 0 favoritos"
        empty_span_600 = dash._empty_label.grid_info()["columnspan"]
        assert empty_span_600 == 2, f"_empty_label inicial debe ocupar 2 columnas (600px), recibido {empty_span_600}"

        # Redimensionar a 1200px con empty_label activo vía <Configure>
        dash.buttons_frame.winfo_width = lambda: 1200
        dash._on_frame_configure(_FakeEvent(dash.buttons_frame))
        empty_span_1200 = dash._empty_label.grid_info()["columnspan"]
        assert empty_span_1200 == 4, f"_empty_label debe adaptarse a 4 columnas tras <Configure>, recibido {empty_span_1200}"
    finally:
        root.destroy()
    print("test_dashboard_favorite_grid_adaptive_contracts OK.")


def test_process_service_db_download_contracts():
    """TASK-050: Contratos de sincronización remota de DB, URL centralizada y fallback observable."""
    print("Testing ProcessService remote DB download contracts (TASK-050)...")
    import ast
    import inspect
    import threading
    import urllib.request
    import urllib.error
    from woptimizer.services import process_service
    from woptimizer.services.process_service import (
        ProcessService,
        DB_REMOTE_URL,
        SYSTEM_PROTECTED_PROCESSES,
    )

    # 1. Contrato de constante de módulo DB_REMOTE_URL
    assert hasattr(process_service, "DB_REMOTE_URL"), "process_service debe exportar DB_REMOTE_URL"
    assert DB_REMOTE_URL.startswith("https://raw.githubusercontent.com/"), (
        f"DB_REMOTE_URL debe apuntar al endpoint oficial de GitHub, obtenido: {DB_REMOTE_URL}"
    )

    # 2. Guard AST: el literal de URL no debe estar hardcodeado en el cuerpo de load_db_async
    import textwrap
    fn_source = textwrap.dedent(inspect.getsource(ProcessService.load_db_async))
    fn_tree = ast.parse(fn_source)
    for node in ast.walk(fn_tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            assert "raw.githubusercontent.com" not in node.value, (
                "El literal de URL de GitHub no debe estar hardcodeado en load_db_async; debe usar DB_REMOTE_URL"
            )
            assert "gitlab.com" not in node.value, (
                "El literal obsoleto de GitLab no debe figurar en load_db_async"
            )

    # 3. Contrato de reporte observable en fallo de descarga (on_error)
    ps = ProcessService()
    error_received = []
    callback_called = threading.Event()
    error_event = threading.Event()

    def _mock_urlopen_fail(req, timeout=None):
        raise urllib.error.URLError("Simulated network timeout")

    orig_urlopen = urllib.request.urlopen
    urllib.request.urlopen = _mock_urlopen_fail
    try:
        def _on_err(msg: str):
            error_received.append(msg)
            error_event.set()

        def _on_done():
            callback_called.set()

        ps.load_db_async(callback=_on_done, on_error=_on_err)

        # Esperar a que el hilo secundario termine
        assert error_event.wait(timeout=3.0), "load_db_async debió invocar on_error ante fallo de red"
        assert callback_called.wait(timeout=3.0), "load_db_async debió invocar callback tras intentar descarga"

        assert len(error_received) == 1, f"Se esperaba 1 reporte de error, recibidos {len(error_received)}"
        assert "Fallo descargando DB remota" in error_received[0], (
            f"El mensaje de error debe ser observable y honesto: {error_received[0]}"
        )
    finally:
        urllib.request.urlopen = orig_urlopen

    # 4. Resiliencia y fallback a base de datos local empaquetada
    from woptimizer.config import get_safety_badge
    assert ps.is_db_loaded is True, "La DB local debe quedar cargada tras fallo de red (fallback local)"
    meta = ps._get_process_meta("explorer.exe")
    assert "\U0001f534" in meta[0], f"explorer.exe debe resolverse con categoría de Sistema, obtenido: {meta[0]}"
    badge = get_safety_badge(meta[0], meta[1])
    assert badge["text"] == "🔴 NO CERRAR", f"explorer.exe debe tener badge NO CERRAR, obtenido: {badge['text']}"

    # Blindaje anti-brick intacto: 0 procesos de sistema protegidos son cerrables
    for sys_proc in SYSTEM_PROTECTED_PROCESSES:
        meta = ps._get_process_meta(sys_proc)
        assert meta[0] == "\U0001f534 Sistema de Windows", (
            f"Proceso protegido {sys_proc} debe tener categoría de Sistema"
        )

    # 5. Contrato de descarga exitosa simulada (mock con directorio aislado)
    import tempfile
    import shutil
    from woptimizer import config as wopt_config

    temp_data_dir = tempfile.mkdtemp(prefix="wopt_test_download_")
    orig_data_dir = wopt_config._data_dir
    wopt_config._data_dir = lambda: temp_data_dir

    class _MockSuccessResponse:
        def __init__(self, data: bytes):
            self.data = data
        def read(self):
            return self.data
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_db_json = b'{"test_app": {"category": "\\ud83d\\udfe2 Productividad", "priority": "normal", "description": "App de prueba"}}'
    success_callback_called = threading.Event()
    success_error_called = threading.Event()

    def _mock_urlopen_success(req, timeout=None):
        return _MockSuccessResponse(mock_db_json)

    urllib.request.urlopen = _mock_urlopen_success
    try:
        def _err_unexpected(msg: str):
            success_error_called.set()

        def _success_done():
            success_callback_called.set()

        ps.load_db_async(callback=_success_done, on_error=_err_unexpected)
        assert success_callback_called.wait(timeout=3.0), "load_db_async debió invocar callback tras descarga exitosa"
        assert not success_error_called.is_set(), "on_error NO debe invocarse cuando la descarga es exitosa"
    finally:
        urllib.request.urlopen = orig_urlopen
        wopt_config._data_dir = orig_data_dir
        shutil.rmtree(temp_data_dir, ignore_errors=True)

    print("test_process_service_db_download_contracts OK.")


def test_process_manager_db_update_button_and_feedback():
    """TASK-051: Botón de actualización de DB en ProcessManagerView, reporte honesto y no-congelamiento."""
    print("Testing ProcessManagerView DB update button and feedback contracts (TASK-051)...")
    import ast
    import inspect
    import textwrap
    import customtkinter as ctk
    from unittest.mock import MagicMock
    from woptimizer.ui.views.process_manager_view import ProcessManagerView
    from woptimizer.models import ProcessInfo

    # 1. Guard AST: existe un CTkButton cuyo command apunta a _force_update_db
    view_source = textwrap.dedent(inspect.getsource(ProcessManagerView._build_ui))
    view_tree = ast.parse(view_source)
    found_command = False
    for node in ast.walk(view_tree):
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg == "command":
                    if isinstance(kw.value, ast.Attribute) and kw.value.attr == "_force_update_db":
                        found_command = True
                        break
    assert found_command, "ProcessManagerView._build_ui debe contener un botón cuyo command apunte a self._force_update_db"

    # 2. Desacoplamiento de plataforma: ninguna cadena de process_manager_view.py dice 'GitLab'
    pmv_path = inspect.getfile(ProcessManagerView)
    with open(pmv_path, "r", encoding="utf-8") as f:
        src_text = f.read()
    assert "gitlab" not in src_text.lower(), "process_manager_view.py no debe contener menciones congeladas a 'GitLab'"

    # 3. Contratos en runtime headless
    root = ctk.CTk()
    root.withdraw()
    try:
        mock_ps = MagicMock()
        mock_ps.is_db_loaded = True
        mock_ps.get_running_processes.return_value = [
            ProcessInfo.model_construct(pid=100, name="notepad.exe", exe_path="", memory_mb=25.0, category="🟢 Seguro", status="running", is_system_protected=False)
        ]
        mock_pack_s = MagicMock()
        mock_pack_s.get_all_packs.return_value = {}

        view = ProcessManagerView(root, mock_ps, mock_pack_s)

        # Verificar existencia y texto del botón
        assert hasattr(view, "btn_update_db"), "ProcessManagerView debe instanciar self.btn_update_db"
        assert view.btn_update_db.cget("text") == "🔄 Actualizar DB"

        # Simular fallo de descarga en _force_update_db
        def _mock_load_fail(callback=None, on_error=None):
            if on_error:
                on_error("Error de conexión simulado")
            if callback:
                callback()

        mock_ps.load_db_async = _mock_load_fail
        view._force_update_db()

        # Procesar los eventos after programados
        root.update()

        fail_text = view.status_label.cget("text")
        assert "⚠️ DB no actualizada (sin red o repo no publicado). Se usa la local." in fail_text, (
            f"El fallo de red debe notificarse honestamente en status_label, recibido: {fail_text}"
        )
        assert "Descargando" not in fail_text, "El mensaje no debe quedarse colgado en Descargando"

        # Simular que _render_list se ejecuta: no debe sobreescribir el aviso de error
        view._render_list()
        assert "⚠️ DB no actualizada (sin red o repo no publicado). Se usa la local." in view.status_label.cget("text"), (
            "El renderizado de procesos no debe pisar el aviso de fallo de DB"
        )

        # Simular éxito de descarga en _force_update_db
        def _mock_load_success(callback=None, on_error=None):
            if callback:
                callback()

        mock_ps.load_db_async = _mock_load_success
        view._force_update_db()

        root.update()

        success_text = view.status_label.cget("text")
        assert "✅ Base de datos actualizada con éxito." in success_text, (
            f"El éxito debe notificarse claramente en status_label, recibido: {success_text}"
        )

        # Simular que _render_list se ejecuta tras el éxito: no debe sobreescribir el aviso de éxito
        view._render_list()
        assert "✅ Base de datos actualizada con éxito." in view.status_label.cget("text"), (
            "El renderizado de procesos no debe pisar el aviso de éxito de DB"
        )

        # Distinción estricta de textos
        assert fail_text != success_text, "Las rutas de éxito y de fallo deben emitir textos completamente distintos"

    finally:
        root.destroy()

    print("test_process_manager_db_update_button_and_feedback OK.")


def test_process_manager_pack_dropdown_single_arrow_and_placeholder():
    """TASK-052: Indicador único en desplegable de packs y placeholder centralizado."""
    print("Testing ProcessManagerView pack dropdown single arrow and placeholder (TASK-052)...")
    import ast
    import inspect
    import textwrap
    import customtkinter as ctk
    from unittest.mock import MagicMock
    from woptimizer.ui.views import process_manager_view as pmv_mod
    from woptimizer.ui.views.process_manager_view import ProcessManagerView
    from woptimizer.models import Pack

    # 1. Contrato de la constante: existe y no contiene el glifo ▼
    assert hasattr(pmv_mod, "PLACEHOLDER_PACK"), "process_manager_view debe exportar la constante PLACEHOLDER_PACK"
    assert "\u25bc" not in pmv_mod.PLACEHOLDER_PACK, "PLACEHOLDER_PACK no debe contener el glifo ▼"
    assert "▼" not in pmv_mod.PLACEHOLDER_PACK, "PLACEHOLDER_PACK no debe contener el caracter de flecha ▼"
    assert pmv_mod.PLACEHOLDER_PACK == "Seleccionar Pack", f"PLACEHOLDER_PACK inesperado: {pmv_mod.PLACEHOLDER_PACK}"

    # 2. Análisis AST: el literal 'Seleccionar Pack' aparece exactamente UNA vez en todo el archivo (la definición)
    pmv_path = inspect.getfile(pmv_mod)
    with open(pmv_path, "r", encoding="utf-8") as f:
        src_text = f.read()

    assert src_text.count("Seleccionar Pack") == 1, (
        f"El literal 'Seleccionar Pack' debe aparecer exactamente una vez (en la constante), "
        f"encontrado {src_text.count('Seleccionar Pack')} veces"
    )
    assert "Seleccionar Pack ▼" not in src_text, "No debe quedar ninguna aparición de 'Seleccionar Pack ▼'"

    # 3. Comprobación AST: _update_pack_dropdown compara contra PLACEHOLDER_PACK y no contra un literal
    udp_source = textwrap.dedent(inspect.getsource(ProcessManagerView._update_pack_dropdown))
    udp_tree = ast.parse(udp_source)
    found_const_ref = False
    for node in ast.walk(udp_tree):
        if isinstance(node, ast.Name) and node.id == "PLACEHOLDER_PACK":
            found_const_ref = True
            break
    assert found_const_ref, "_update_pack_dropdown debe referenciar la constante PLACEHOLDER_PACK"

    # 4. Comprobación en Runtime Headless
    root = ctk.CTk()
    root.withdraw()
    try:
        mock_ps = MagicMock()
        mock_ps.is_db_loaded = True
        mock_ps.get_running_processes.return_value = []
        mock_pack_s = MagicMock()
        mock_pack_s.get_all_packs.return_value = {}

        view = ProcessManagerView(root, mock_ps, mock_pack_s)

        # Dropdown inicializado con la constante
        assert view.pack_var.get() == pmv_mod.PLACEHOLDER_PACK, (
            f"El pack_var inicial debe ser {pmv_mod.PLACEHOLDER_PACK}, recibido: {view.pack_var.get()}"
        )
        assert view.pack_dropdown.cget("values") == [pmv_mod.PLACEHOLDER_PACK], (
            f"Los valores iniciales del dropdown deben ser {[pmv_mod.PLACEHOLDER_PACK]}"
        )

        # Cuando hay packs disponibles, el dropdown se actualiza
        mock_pack_s.get_all_packs.return_value = {
            "p1": Pack(id="p1", name="Productividad", apps=[]),
            "p2": Pack(id="p2", name="Streaming", apps=[]),
        }
        view._update_pack_dropdown()
        assert view.pack_dropdown.cget("values") == ["Productividad", "Streaming"]
        # El placeholder inicial se mantiene si no se había seleccionado ningún pack
        assert view.pack_var.get() == pmv_mod.PLACEHOLDER_PACK

        # Si se selecciona un pack y luego se borra, se resetea a values[0] ("Sin packs disponibles")
        view.pack_var.set("PackEliminado")
        mock_pack_s.get_all_packs.return_value = {}
        view._update_pack_dropdown()
        assert view.pack_var.get() == "Sin packs disponibles"

    finally:
        root.destroy()

    print("test_process_manager_pack_dropdown_single_arrow_and_placeholder OK.")


def test_docs_api_and_index_v3_contracts():
    """TASK-054 (ciclo 44): Contratos de veracidad y actualidad en docs/api.md y docs/index.md.

    Verifica:
    1. docs/api.md no contiene residuos v2 eliminados (is_admin, taskkill, powershell, saved_processes.json, ProcessManagerApp).
    2. docs/api.md documenta metodos que existen realmente en los servicios y modelos de src/woptimizer/.
    3. docs/index.md no contiene afirmaciones falsas de auto-elevacion UAC ni scripts legacy (.vbs, .pyw, taskkill).
    4. Todos los ficheros listados en el nav de mkdocs.yml existen en docs/.
    """
    from pathlib import Path
    from woptimizer.services.process_service import ProcessService
    from woptimizer.services.pack_service import PackService
    from woptimizer.services.gaming_service import GamingService
    from woptimizer.services.notification_service import NotificationService
    from woptimizer.models import ProcessInfo, Pack, AppData

    repo_root = Path(__file__).resolve().parent

    api_path = repo_root / "docs" / "api.md"
    assert api_path.exists(), f"docs/api.md no existe en {api_path}"
    api_text = api_path.read_text(encoding="utf-8")

    # 1. Prohibiciones en docs/api.md
    prohibidos_api = [
        "is_admin",
        "taskkill",
        "powershell",
        "saved_processes.json",
        "ProcessManagerApp",
    ]
    for p in prohibidos_api:
        assert p.lower() not in api_text.lower(), f"Residuo v2 prohibido '{p}' encontrado en docs/api.md"

    # 2. Comprobacion de que los metodos y clases de src/ citados en api.md existen
    servicios_metodos = {
        ProcessService: [
            "get_running_processes",
            "kill_processes",
            "kill_pack_apps",
            "start_pack_apps",
            "load_db_async",
            "invalidate_cache",
            "get_process_exe_path",
        ],
        PackService: [
            "get_all_packs",
            "create_user_pack",
            "update_pack",
            "delete_pack",
            "set_favorite",
            "toggle_favorite",
            "get_favorite_packs",
            "reset_gaming_pack",
            "save",
            "load",
        ],
        GamingService: [
            "execute_gaming_pack",
            "restore_gaming_session",
            "should_kill_for_gaming",
            "get_last_closed_apps",
        ],
        NotificationService: [
            "notify",
            "attach_tray",
            "detach_tray",
            "notify_pack_activated",
            "notify_apps_launched",
            "notify_kill_result",
        ],
    }

    for cls, metodos in servicios_metodos.items():
        assert cls.__name__ in api_text, f"{cls.__name__} no esta citado en docs/api.md"
        for m in metodos:
            assert hasattr(cls, m) and callable(getattr(cls, m)), f"Metodo {cls.__name__}.{m} no existe o no es invocable"
            assert m in api_text, f"Metodo {cls.__name__}.{m} no esta documentado en docs/api.md"

    # Verificar modelos en api.md
    for model_cls in (ProcessInfo, Pack, AppData):
        assert model_cls.__name__ in api_text, f"Modelo {model_cls.__name__} no citado en docs/api.md"

    # 3. Prohibiciones en docs/index.md
    index_path = repo_root / "docs" / "index.md"
    assert index_path.exists(), f"docs/index.md no existe en {index_path}"
    index_text = index_path.read_text(encoding="utf-8")

    prohibidos_index = [
        "auto-eleva admin",
        "auto-elevacion uac nativa",
        "process_manager.pyw",
        "ProcessManager.vbs",
        "taskkill",
    ]
    for p in prohibidos_index:
        assert p.lower() not in index_text.lower(), f"Residuo v2 prohibido '{p}' encontrado en docs/index.md"

    # 4. Integridad de navegacion en mkdocs.yml
    mkdocs_path = repo_root / "mkdocs.yml"
    assert mkdocs_path.exists(), f"mkdocs.yml no existe en {mkdocs_path}"
    mkdocs_text = mkdocs_path.read_text(encoding="utf-8")

    for line in mkdocs_text.splitlines():
        line_clean = line.strip()
        if line_clean.endswith(".md"):
            doc_rel = line_clean.split(":")[-1].strip()
            target_doc = repo_root / "docs" / doc_rel
            assert target_doc.exists(), f"Fichero nav '{doc_rel}' referenciado en mkdocs.yml no existe en disco: {target_doc}"

    print("test_docs_api_and_index_v3_contracts OK.")


def test_no_legacy_test_files_in_root():
    """TASK-055 (ciclo 45): Guard anti-regresión y contratos de archivo de scripts test_*.py legacy.

    Verifica:
    1. Cero archivos test_*.py en la raíz del repositorio (run_tests.py es la única suite oficial).
    2. docs/archive/legacy-root-tests/ existe y contiene los 11 archivos históricos trasladados.
    3. docs/archive/legacy-root-tests/README.md existe y documenta los 10 scripts v2 y test_powershell_direct.py.
    4. test_powershell_direct.py archivado contiene referencias a notepad (aislado de la raíz).
    """
    print("Testing absence of legacy test_*.py files in root and archive integrity (TASK-055)...")
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent

    # 1. Guard anti-regresión: la raíz NO debe contener ningún test_*.py
    legacy_in_root = [
        f.name for f in repo_root.iterdir()
        if f.is_file() and f.name.startswith("test_") and f.name.endswith(".py")
    ]
    assert not legacy_in_root, (
        f"Se encontraron archivos test_*.py legacy en la raíz del repositorio: {legacy_in_root}. "
        "Deben archivarse en docs/archive/legacy-root-tests/"
    )

    # 2. Integridad del archivo
    archive_dir = repo_root / "docs" / "archive" / "legacy-root-tests"
    assert archive_dir.is_dir(), f"El directorio de archivo no existe: {archive_dir}"

    readme_file = archive_dir / "README.md"
    assert readme_file.is_file() and readme_file.stat().st_size > 500, (
        f"README.md en {readme_file} debe existir y contener documentación descriptiva"
    )
    readme_text = readme_file.read_text(encoding="utf-8")
    assert "test_powershell_direct.py" in readme_text
    assert "notepad" in readme_text.lower()
    assert "process_manager" in readme_text

    expected_archived = [
        "test_categorization.py",
        "test_debug_list.py",
        "test_gaming_profile.py",
        "test_gaming_session.py",
        "test_harness_v2.py",
        "test_harness.py",
        "test_kill_expansion.py",
        "test_kill_real.py",
        "test_powershell_direct.py",
        "test_profiles.py",
        "test_relaunch_grouping.py",
    ]
    for filename in expected_archived:
        target = archive_dir / filename
        assert target.is_file(), f"Fichero legacy esperado {filename} no encontrado en {archive_dir}"

    ps_direct = archive_dir / "test_powershell_direct.py"
    assert "notepad.exe" in ps_direct.read_text(encoding="utf-8")

    print("test_no_legacy_test_files_in_root OK.")


def test_dead_code_ast_guard():
    """TASK-056 (ciclo 46): Guard AST de código muerto en src/woptimizer/**.

    Verifica que toda función y método definido en los módulos de src/woptimizer
    tenga al menos una referencia real dentro del código de producción o en
    la suite de tests (run_tests.py), evitando funciones zombis o desconectadas.
    """
    print("Testing dead code AST guard across src/woptimizer/** (TASK-056)...")
    import ast
    from collections import Counter
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent
    src_dir = repo_root / "src" / "woptimizer"

    # 1. Derivar el alcance del árbol de módulos en src/woptimizer/**
    src_files = [p for p in src_dir.rglob("*.py")]
    assert len(src_files) >= 10, f"Se esperaban al menos 10 módulos en {src_dir}, hallados {len(src_files)}"

    all_files = list(src_files) + [repo_root / "run_tests.py"]

    # 2. Parsear cada archivo una vez y acumular frecuencias de nombres y atributos
    symbol_counts = Counter()
    definitions = []

    for path in all_files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        is_src = path in src_files
        rel_path = path.relative_to(repo_root)

        for node in ast.walk(tree):
            if is_src and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                definitions.append((rel_path, node.lineno, node.name))
            elif isinstance(node, ast.Name):
                symbol_counts[node.id] += 1
            elif isinstance(node, ast.Attribute):
                symbol_counts[node.attr] += 1

    # 3. Lista blanca justificada: métodos mágicos dunder, entrypoint main
    whitelist = {
        "main",  # Entry point de __main__.py y run.py
    }

    unreferenced = []
    for rel_path, lineno, name in definitions:
        if (name.startswith("__") and name.endswith("__")) or name in whitelist:
            continue
        if symbol_counts[name] == 0:
            unreferenced.append(f"{rel_path}:{lineno} -> {name}")

    assert not unreferenced, (
        f"Se detectaron {len(unreferenced)} funciones/métodos sin ninguna referencia en el producto ni en tests:\n"
        + "\n".join(f"  - {u}" for u in unreferenced)
    )

    # 4. Control negativo: verificar que funciones clave de producto son monitorizadas
    monitored = {name for _, _, name in definitions}
    assert "_force_update_db" in monitored, "_force_update_db debe estar en las funciones analizadas"
    assert "get_favorite_packs" in monitored, "get_favorite_packs debe estar en las funciones analizadas"
    assert "is_wcag_aa" in monitored, "is_wcag_aa debe estar en las funciones analizadas"
    assert "_get_priority" not in monitored, "_get_priority debe haber sido eliminado de process_service.py"

    print("test_dead_code_ast_guard OK (cero código muerto en src/woptimizer/**).")


def test_el_ancla_de_commits_no_depende_del_que_escribe_el_journal():
    """TASK-057: el validador no puede seguir exigiendo los ciclos solo a quien
    escribe el registro.

    El residuo literal: `rd_journal.json` lo escribe el MISMO orquestador que
    despues pide la validacion. Un fichero distinto no es una fuente
    independiente, asi que el requisito de registrar el ciclo N se seguia
    deduciendo de un artefacto de la misma pipeline. Un residuo asi no se ve con
    una revision: se ve con un arbol de mentira.

    El testigo tercero es el HISTORIAL de commits y el requisito pasa a ser la
    UNION:

        ciclos_requeridos = ciclos_del_journal | ciclos_del_historial

    Las cuatro sondas de abajo tienen un arbol que HOY da `0 FAIL`, y cada una
    muere con una union ausente, con una union mal hecha o con un ancla muda:

    - A1. Parser: `ciclo #46 (TASK-056)`. El mutante que parsea `TASK-` devuelve
      `{43, 56}` y ademas pone el repo real en rojo, porque `## CYCLE-056` no
      existe. Ciclo y tarea DIVERGEN: es el discriminante mas barato y el que
      mas dano hace.
    - A2. Residuo: commit `ciclo #47`, journal que solo llega al 46 y changelog
      sin `## CYCLE-047` -> DOS errores, uno que nombra `rd_journal.json` y otro
      el changelog. Sin el historial, el mismo arbol da cero. El residuo se
      comprueba POR SU CONJUNTO (acusa el 047, nunca el 046) y A2b monta el
      arbol espejo, journal {46, 47} con historial {46}, que tiene que dar
      CERO errores: es el unico arbol donde acusar es, por construccion,
      acusar al reves, y por eso mata la diferencia invertida.
    - A3. La union NO es una sustitucion: journal `{3}` + commits `{4}` exige los
      DOS. Sustituyendo, el 3 pierde su unico requisito (sus commits de cierre
      no llevan marcador) y el falso verde del ciclo 15 renacido.
    - A4. `GIT_DIR` que no es un repo -> `errors` NO vacio y NINGUNA excepcion.
      Un `except: return set()` silencioso es la misma clase de bug que la rama
      `if n_tests is None:`, que era codigo muerto (CYCLE-027): una guarda que se
      salta sola cuando no puede comprobar ya no guarda nada.

    NINGUN test toca el historial real: cada fixture tiene su `GIT_DIR` en
    `tempfile`, y `os.environ["GIT_DIR"]` se restaura en el `finally`. Sin ese
    `finally`, un `GIT_DIR` a un temporal ya borrado envenenaria a
    `_entorno_git_del_repo()` (que respeta el `GIT_DIR` del entorno) y el fallo
    apareceria en el test equivocado, dos pasos despues.

    `_comprobar_ancla_del_changelog` se extrajo del cuerpo de `main()` por esto
    mismo: `main()` deriva `root` de `__file__` y no admite argv, asi que sin
    extraccion estas sondas solo se despertarian lanzando el validador entero
    contra el repo entero. El cuerpo vive UNA vez, y el camino real y el de test
    ejecutan el MISMO codigo: nada de un `--verify` con ruta propia.
    """
    import json
    import shutil
    import subprocess
    import tempfile
    import validate_docs as vd

    def _git(args, cwd):
        """`git` con reintentos: el `spawn EPERM` de este host es intermitente."""
        # La fixture se monta SIN el `GIT_DIR` que otra fixture dejo puesto: si
        # se hereda, `git init` y `git commit` operan sobre el repo del caso
        # ANTERIOR y el fallo aparece dos sondas mas tarde, en el sitio
        # equivocado. Aqui solo se monta la fixture; el `git log` del ancla lo
        # lanza el validador con su propio entorno.
        env = os.environ.copy()
        env.pop("GIT_DIR", None)
        env.pop("GIT_WORK_TREE", None)
        ultimo = "(nunca llego a ejecutarse)"
        for _intento in (1, 2, 3):
            r = subprocess.run(
                ["git"] + args, cwd=cwd, env=env, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=120,
            )
            if r.returncode == 0:
                return r.stdout or ""
            ultimo = ((r.stderr or "") + (r.stdout or "")).strip()
        raise AssertionError(
            f"git {' '.join(args)} fallo tres veces en la fixture: {ultimo}. "
            "Sin este envoltorio el fallo de git se pierde como falso verde"
        )

    def _informe(root):
        """(errors, ok) del check 5b, con las excepciones convertidas en asercion."""
        errors, ok = [], []
        try:
            vd._comprobar_ancla_del_changelog(root, errors, ok)
        except Exception as exc:                       # pragma: no cover
            raise AssertionError(
                "el check 5b debia devolver un INFORME y tiro "
                f"{type(exc).__name__}: {exc}. Sin este envoltorio un mutante que "
                "revienta el codigo muere por traceback y el verificador no puede "
                "distinguirlo de un test que detecta el fallo"
            )
        return errors, ok

    tmp = tempfile.mkdtemp(prefix="wopt_ancla_")
    git_dir_previo = os.environ.get("GIT_DIR")
    try:
        def _arbol(nombre, ciclos_journal, entradas_changelog, asunto=None):
            """Raiz temporal con journal, CHANGELOG.md y, si `asunto`, UN commit."""
            raiz = os.path.join(tmp, nombre)
            os.makedirs(os.path.join(raiz, ".taskmaster"))
            with open(os.path.join(raiz, ".taskmaster", "rd_journal.json"),
                      "w", encoding="utf-8") as fh:
                fh.write(json.dumps([{"cycle": c} for c in ciclos_journal]))
            with open(os.path.join(raiz, "CHANGELOG.md"), "w", encoding="utf-8") as fh:
                fh.write("# Changelog\n\n### Corregido\n\n")
                for c in entradas_changelog:
                    fh.write(f"\n## CYCLE-{c:03d}\n\nEntrada del ciclo {c}.\n")
            if asunto is not None:
                _git(["init", "-q", raiz], tmp)
                _git(["-c", "user.email=ancla@woptimizer.invalid",
                      "-c", "user.name=ancla",
                      "-c", "commit.gpgsign=false",
                      "commit", "-q", "--allow-empty", "-m", asunto], raiz)
            return raiz

        # --- A1. EL PARSER: ciclo != tarea ------------------------------------
        subjects = [
            "chore(release): cerrar ciclo #46 (TASK-056) guard AST de codigo muerto",
            "feat(quality): TASK-056 sin marcador de ciclo",
            "docs(cycle-43): cierre de ciclo 43, actualizacion de rd_journal",
        ]
        ciclos, con_marcador, sin_marcador = vd._ciclos_de_commits(subjects)
        assert (ciclos, con_marcador, sin_marcador) == ({43, 46}, 2, 1), (
            "el parser tiene que leer el numero de CICLO y no el de TAREA: "
            f"obtenido {ciclos!r}, {con_marcador} con marcador y {sin_marcador} sin. "
            "El mutante que parsea `TASK-` devuelve {43, 56} y pone el repo real "
            "en rojo, porque `## CYCLE-056` no existe (ciclo 46 = TASK-056)"
        )
        # El `sin` de "sin marcador de ciclo" NO es un ciclo: la palabra sola,
        # sin numero detras, no marca nada. Sin esta asercion un parser que
        # admitiera `ciclo` sin digitos contaria el 56 del subject anterior.
        # G1 (cierre del ciclo #47): la unidad de la funcion paso de UN numero a
        # un CONJUNTO, porque un asunto en plural declara mas de un ciclo. El
        # "vacio = nada" es lo que sigue teniendo que ser falso para esa palabra.
        assert vd._ciclos_del_asunto("feat(quality): TASK-056 sin marcador de ciclo") == set(), (
            "una palabra 'ciclo' sin numero detras no es un marcador de ciclo: "
            "aceptarla fabricaria ciclos que no existen"
        )
        # Y el rango del plural, que es la semantica de G1: `ciclos 14-20`
        # corrobora los SIETE, con los dos extremos dentro. Aqui se fija solo
        # lo que el parser DEVUELVE para un asunto literal; lo que el rango
        # EXIGE (y que un rango absurdo no exija 9999 ciclos) lo mide la fila
        # (h) de la tabla de escenarios, por `validar(root)`. Un invariante con
        # dos guardianes se reporta con los dos, no con el primero que se
        # encuentre.
        assert vd._ciclos_del_asunto("feat(ciclos 14-20): varios ciclos") == set(range(14, 21)), (
            "un asunto en PLURAL con guion declara un RANGO con extremos "
            "incluidos: 'ciclos 14-20' corrobora 14 a 20. Sin esta asercion el "
            "`s?` del plural es decoracion y quitarlo sobrevive a la suite"
        )

        # --- A2. EL RESIDUO: comiteado y NO registrado -----------------------
        raiz_r = _arbol("residuo", [46], [46],
                        "chore(release): cerrar ciclo #47 (TASK-090)")
        os.environ["GIT_DIR"] = os.path.join(raiz_r, ".git")
        errors, _ok = _informe(raiz_r)
        assert len(errors) == 2, (
            "un ciclo 47 COMITEADO, ausente del journal y sin entrada en el "
            f"changelog tiene que dar DOS errores; hay {len(errors)}: {errors}. "
            "Sin el historial como testigo este arbol da 0 FAIL, que es "
            "exactamente el residuo que la tarea persigue"
        )
        # El residuo se acusa POR SU CONJUNTO, no por una subcadena laxa. Con
        # la diferencia INVERTIDA (`ciclos_journal - ciclos_historial`) el
        # mensaje sigue conteniendo "rd_journal.json NO lo registra" pero
        # nombra el 46, que el journal SI registra: el test pasaria en verde y
        # el validador accusing al reves, con el repo real en rojo.
        residuo = [e for e in errors if "rd_journal.json NO lo registra" in e]
        assert len(residuo) == 1, (
            "el residuo tiene que acusarse en UNA linea y nombrar SU conjunto: hay "
            f"{residuo}. Errors: {errors}"
        )
        assert "ciclo/s 047" in residuo[0] and "046" not in residuo[0], (
            "el residuo son los ciclos que EL HISTORIAL TIENE Y EL JOURNAL NO: en este "
            f"arbol el 47, nunca el 46 (el 46 esta en el journal). Errors: {errors}"
        )
        assert any("CHANGELOG.md" in e and "047" in e for e in errors), (
            "el otro error tiene que exigir la entrada `## CYCLE-047` del "
            f"changelog legible. Errors: {errors}"
        )

        # --- A2b. LA DIRECCION DE LA DIFERENCIA ------------------------------
        # El arbol espejo: el journal sabe MAS ciclos (46 y 47) que el historial
        # (solo el 46 comiteado). Aqui NO hay trabajo comiteado sin registrar,
        # asi que la unica linea de error posible es la del residuo: acusar en
        # este arbol es, por construccion, acusar al reves.
        raiz_d = _arbol("direccion", [46, 47], [46, 47],
                        "chore(release): cerrar ciclo #46 (TASK-056)")
        os.environ["GIT_DIR"] = os.path.join(raiz_d, ".git")
        errors_d, _ok_d = _informe(raiz_d)
        assert not errors_d, (
            "journal {46, 47} e historial {46} describen el MISMO conjunto exigido y las "
            "entradas `## CYCLE-046`/`## CYCLE-047` estan: este arbol tiene que dar 0 "
            f"errores. Errors: {errors_d}. La diferencia debe ser "
            "`ciclos_historial - ciclos_journal`: invertida, este arbol acusa un residuo "
            "que no existe y pone el repo real en rojo"
        )

        # --- A3. UNION, NO SUSTITUCION ---------------------------------------
        raiz_u = _arbol("union", [3], [],
                        "chore(release): cerrar ciclo #4 (TASK-091)")
        os.environ["GIT_DIR"] = os.path.join(raiz_u, ".git")
        errors, _ok = _informe(raiz_u)
        faltantes = [e for e in errors if "sin entrada para el/los ciclo/s" in e]
        assert len(faltantes) == 1, (
            f"los ciclos exigidos se enumeran en UNA linea de fallo; hay {errors}"
        )
        assert "003" in faltantes[0] and "004" in faltantes[0], (
            "el journal {3} y el historial {4} exigen LOS DOS: "
            f"obtenido {faltantes[0]!r}. Si se SUSTITUYERA el journal por el "
            "historial, el 3 perderia su unico requisito (sus commits de cierre "
            "no llevan marcador) y seria el falso verde del ciclo 15 renacido"
        )

        # --- A4. ANCLA ILEGIBLE: informe, NUNCA excepcion ni verde ------------
        raiz_s = _arbol("sin_repo", [46], [])
        falso_git = os.path.join(tmp, "no_es_un_repo")
        os.makedirs(falso_git)
        os.environ["GIT_DIR"] = falso_git
        errors4, ok4 = [], []
        assert vd._comprobar_ancla_de_commits(raiz_s, errors4, ok4, [46]) == set(), (
            "un GIT_DIR que no es un repo NO puede aportar ciclos: si devuelve "
            "algo, el parser esta leyendo de otro sitio"
        )
        assert errors4, (
            "un ancla ILEGIBLE no certifica: tiene que haber una linea [FAIL] "
            "con el motivo literal del fallo, no un set() silencioso. Un "
            "`except: return set()` es la misma clase de bug que la rama "
            "`if n_tests is None:` que era codigo muerto (CYCLE-027)"
        )
        assert not any("corroborables" in o for o in ok4), (
            "el historial ilegible no puede entrar en el informe por la via de "
            f"los ciclos corroborables: OK: {ok4}"
        )
        errors, ok = _informe(raiz_s)
        assert any("NO SE PUEDE LEER" in e for e in errors), (
            f"el fallo del ancla tiene que seguir siendo visible en el informe "
            f"del check 5b. Errors: {errors}"
        )
        assert any("CHANGELOG.md" in e and "046" in e for e in errors), (
            "el historial caido NO puede relajar el journal: el ciclo 46 que el "
            f"journal registra tiene que seguir exigiendo su entrada. Errors: {errors}"
        )
    finally:
        if git_dir_previo is None:
            os.environ.pop("GIT_DIR", None)
        else:
            os.environ["GIT_DIR"] = git_dir_previo
        shutil.rmtree(tmp, ignore_errors=True)

    print("Ancla de commits: parser ciclo!=tarea, residuo comiteado sin journal con su "
          "conjunto acusado, arbol espejo que mata la diferencia invertida, union (no "
          "sustitucion) y ancla ilegible con informe.")


# ---------------------------------------------------------------------------
# TASK-057, ITERACION 2 (el mutation-auditor devolvio FAIL con 12 supervivientes).
#
# Los ayudantes de abajo son de MODULO y no anidados dentro de cada test porque
# los comparten cuatro sondas distintas. Cada uno lleva sus TRES intentos: el
# `spawn EPERM` de este host es intermitente, y un unico fallo de `git` en una
# fixture no se distingue de un falso verde, que es el fallo que este ciclo
# existe para matar.
# ---------------------------------------------------------------------------


def _git_de_fixture(args, cwd):
    """`git` de una fixture temporal, sin heredar el `GIT_DIR` de otra sonda."""
    import subprocess

    env = os.environ.copy()
    env.pop("GIT_DIR", None)
    env.pop("GIT_WORK_TREE", None)
    ultimo = "(nunca llego a ejecutarse)"
    for _intento in (1, 2, 3):
        r = subprocess.run(
            ["git"] + args, cwd=cwd, env=env, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=120,
        )
        if r.returncode == 0:
            return r.stdout or ""
        ultimo = ((r.stderr or "") + (r.stdout or "")).strip()
    raise AssertionError(
        f"git {' '.join(args)} fallo tres veces en la fixture: {ultimo}. Sin este "
        "envoltorio el fallo de git se pierde como falso verde"
    )


def _repo_temporal_de_un_commit(directorio, asunto):
    """`git init` + UN commit de `asunto`. Devuelve la ruta de su `.git`."""
    os.makedirs(directorio, exist_ok=True)
    _git_de_fixture(["init", "-q", directorio], os.path.dirname(directorio))
    _git_de_fixture(["-c", "user.email=ancla@woptimizer.invalid",
                     "-c", "user.name=ancla",
                     "-c", "commit.gpgsign=false",
                     "commit", "-q", "--allow-empty", "-m", asunto], directorio)
    return os.path.join(directorio, ".git")


def _copiar_el_esqueleto_del_validador(destino):
    """Copia el esqueleto REAL de ficheros que `validar(root)` lee a `destino`.

    COPIADO y no inventado: si el validador anade una lectura nueva, esta copia
    lo expone como fallo del propio test en vez de dejarlo pasar en silencio.
    Medido: 1,7 MB, y se copia UNA vez por test, no una vez por fila. Eso es lo
    que hace que anadir un escenario cueste una fila y no un test (D4).

    MEDIDO de nuevo en el ciclo #49, y por el mismo motivo: el check 8 lee
    `src/` (para la fila 91, que cita `pack_service.py`) y `.taskmaster/
    tasks.json` (para la fila 95, cuya unica fuente es `TASK-059`). Sin ellos, el
    arbol copiado se queda con dos fallos MAS que no tienen nada que ver con lo que
    el test mide, y los tests que cuentan `len(errors)` --el del journal ilegible--
    mueren por un motivo que no es su sujeto. Ampliar el esqueleto es justo lo que
    este docstring manda: que la copia exponga la lectura nueva.
    """
    import shutil

    raiz_repo = os.path.dirname(os.path.abspath(__file__))
    ficheros = ("llms.txt", "llms-full.txt", "AGENTS.md", "README.md", "STATUS.md",
                "CHANGELOG.md", "mkdocs.yml", "run_tests.py", "validate_docs.py")
    arboles = ("docs", "openspec", "src")
    ocultos = (os.path.join(".taskmaster", "CHANGELOG.md"),
               os.path.join(".taskmaster", "rd_journal.json"),
               os.path.join(".taskmaster", "tasks.json"))
    for nombre in ficheros:
        shutil.copy2(os.path.join(raiz_repo, nombre), os.path.join(destino, nombre))
    for arbol in arboles:
        shutil.copytree(os.path.join(raiz_repo, arbol), os.path.join(destino, arbol),
                        ignore=shutil.ignore_patterns("__pycache__"))
    for relativa in ocultos:
        d = os.path.join(destino, relativa)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy2(os.path.join(raiz_repo, relativa), d)


def _informe_del_validador_real(root):
    """`(errors, ok)` de `validar(root)`, con las excepciones en asercion.

    Este es el UNICO camino contractual del validador para los tests (D3):
    asentar por la funcion que el producto llama, no por una privada a la que se
    le pasan los argumentos a mano. `validar` no imprime y no sale, asi que un
    test puede leer su veredicto sin lanzar un subproceso.
    """
    import validate_docs as vd

    errors, ok = [], []
    try:
        errors, ok = vd.validar(root)
    except Exception as exc:                           # pragma: no cover
        raise AssertionError(
            "validar(root) debia devolver un INFORME y tiro "
            f"{type(exc).__name__}: {exc}. Sin este envoltorio un mutante que "
            "revienta el validador muere por traceback y no se puede distinguir de "
            "un test que detecta el fallo"
        )
    return errors, ok


def test_el_ancla_se_cablea_en_el_camino_real_del_validador():
    """TASK-057 iter 2 (S2, CRITICO): `main()` puede dejar de llamar al ancla y la
    suite entera seguir en verde.

    El agujero que el mutation-auditor demostro: la suite llamaba a las funciones
    PRIVADAS (`_comprobar_ancla_del_changelog`, `_comprobar_ancla_de_commits`) y
    NUNCA a `vd.main()`. Borrada la linea de cableado, los tests de la sonda
    anterior pasan, `python validate_docs.py` responde con su habitual "0 FAIL" y
    el ancla esta apagado: codigo testeado que el producto ya no invoca, la misma
    clase que TASK-056 y en el propio ciclo que debia cerrar el codigo muerto. El
    criterio A5 ("el repo real -> 0 FAIL") no era un test: era una afirmacion.

    Este test cierra el hueco por la via que no duplica NADA: copia el
    `validate_docs.py` REAL a un arbol temporal con el esqueleto de ficheros que
    `main()` lee, y lo ejecuta como SUBPROCESO. Se ejecuta el camino real entero
    -- `main()`, el `if os.path.exists(CHANGELOG.md)`, la linea de cableado y el
    `sys.exit` -- contra un arbol con un residuo real: un commit del ciclo 999
    que `rd_journal.json` no registra.

    Y es de DOS CARAS, no de una: la segunda mitad escribe en la copia el MUTANTE
    (la linea de cableado sustituida por `pass`) y exige que el residuo
    desaparezca del informe. Asi el test demuestra su propia capacidad de matar
    en vez de declararla, y una sonda que dejara de ver el residuo por la razon
    que sea se cae aqui, diciendo cual.
    """
    import shutil
    import subprocess
    import sys
    import tempfile

    def _ejecutar_el_validador_real():
        """`(rc, informe)` del validador real sobre el arbol temporal.

        El informe se lee de stdout Y stderr: un validador que revienta antes de
        imprimir deja el motivo ahi, y un test que solo mirase stdout
        distinguiria "no hay residuo" de "se ha roto", que son cosas distintas.
        """
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        ultimo = (None, "(no llego a ejecutarse)")
        for _intento in (1, 2, 3):
            r = subprocess.run(
                [sys.executable, os.path.join(tmp, "validate_docs.py")],
                cwd=tmp, env=env, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=300,
            )
            ultimo = (r.returncode, (r.stdout or "") + (r.stderr or ""))
            if "rd_journal.json NO lo registra" in ultimo[1]:
                # El ancla ya ha hablado: el reintento solo hacia falta por el
                # `spawn EPERM` intermitente de git, no por el contenido.
                return ultimo
        return ultimo

    tmp = tempfile.mkdtemp(prefix="wopt_validador_real_")
    git_dir_previo = os.environ.get("GIT_DIR")
    try:
        # El esqueleto que `validar(root)` lee, COPIADO y no inventado (helper
        # compartido con la tabla de escenarios: una sola definicion del
        # esqueleto, para que las dos rutas no puedan divergir).
        os.makedirs(tmp, exist_ok=True)
        _copiar_el_esqueleto_del_validador(tmp)

        # El residuo, en el HISTORIAL REAL de esta copia: el ciclo 999 no esta
        # en el journal copiado (llega al 46) ni en el changelog copiado.
        ruta_historial = os.path.join(tmp, "historial")
        os.environ["GIT_DIR"] = _repo_temporal_de_un_commit(
            ruta_historial, "chore(release): cerrar ciclo #999 (TASK-999)")
        # Pre-vuelo del `git log` que hara el validador. Un EPERM aqui debe morir
        # con su motivo, no dejar que un residuo ausente se lea como "el ancla no
        # exige nada".
        assert "ciclo #999" in _git_de_fixture(
            ["log", "--format=%s", "--all"], ruta_historial), (
            "la fixture de git no esta legible: sin este pre-vuelo un EPERM "
            "intermitente se lee como un ancla muda y este test daria un falso verde"
        )

        rc, informe = _ejecutar_el_validador_real()
        assert "Resumen:" in informe, (
            "el validador tiene que LLEGAR AL FINAL y printar su informe, y su ultima "
            "linea es `Resumen:`. Si `Resumen:` no esta, esta asercion esta probando una "
            "excepcion, no el cableado. Medido en el intento 3: este es el motivo por el "
            "que muere el mutante M2 (borrar el cuarto argumento de "
            "`_comprobar_ancla_de_commits`, que con default era un cambio de "
            f"comportamiento y sin default es un `TypeError`). rc={rc}. Informe:\n"
            + informe[-2000:]
        )
        assert "historial de commits:" in informe and "corroborables" in informe, (
            "el ancla tiene que CORRER dentro de validar(): su linea de informe "
            f"(subjects leidos y ciclos corroborables) no aparece. rc={rc}. "
            "Informe:\n" + informe[-2000:]
        )
        assert "rd_journal.json NO lo registra" in informe, (
            "el validador REAL tiene que acusar el ciclo 999 comiteado y ausente del "
            f"journal. rc={rc}. Informe:\n{informe[-2000:]}"
        )
        assert "ciclo/s 999" in informe, (
            "el residuo son los ciclos QUE EL HISTORIAL TIENE Y EL JOURNAL NO, y el "
            f"journal copiado llega al 046: el 999 y nadie mas. Informe:\n{informe[-2000:]}"
        )
        assert "sin entrada para el/los ciclo/s 999" in informe, (
            "y el changelog legible tiene que exigir su entrada `## CYCLE-999`. "
            f"Informe:\n{informe[-2000:]}"
        )
        assert rc == 1, (
            f"el validador tiene que salir con 1 habiendo encontrado fallos; salio con "
            f"{rc}. Informe:\n{informe[-2000:]}"
        )

        # --- LA MITAD MUTANTE: el mismo arbol, el ancla DESCABLEADA ----------
        ruta_validador = os.path.join(tmp, "validate_docs.py")
        with open(ruta_validador, encoding="utf-8") as fh:
            fuente = fh.read()
        cableado = "    _comprobar_ancla_del_changelog(root, errors, ok)"
        assert fuente.count(cableado) == 1, (
            "el cableado del ancla tiene que aparecer EXACTAMENTE una vez en el cuerpo "
            f"de validar(); aparece {fuente.count(cableado)} veces. Con dos, este test "
            "seguiria verde aunque se borrara el cableado que de verdad se ejecuta"
        )
        with open(ruta_validador, "w", encoding="utf-8") as fh:
            fh.write(fuente.replace(cableado, "    pass  # ANCLA DESCABLEADA (mutante)"))
        rc_mutante, informe_mutante = _ejecutar_el_validador_real()
        assert "Resumen:" in informe_mutante, (
            "el mutante tiene que llegar al final y printar su informe: si no, este test "
            "no esta probando el cableado sino una excepcion. Informe:\n"
            + informe_mutante[-2000:]
        )
        assert "rd_journal.json NO lo registra" not in informe_mutante, (
            "al DESCABLEAR el ancla el residuo tiene que desaparecer del informe, que es "
            "justo lo que hacia que el auditor viera el fallo: el validador mudo responde "
            f"{informe_mutante.count('[OK]')} OK y 0 FAIL. Informe:\n{informe_mutante[-2000:]}"
        )
        assert "historial de commits:" not in informe_mutante, (
            "sin la llamada no puede quedar la linea de informe del historial: si queda, "
            "el mutante no estaba descableando el ancla que este test cree que ejecuta"
        )

        # --- SEGUNDO MUTANTE (S2b): `main()` que NO llama a `validar` --------
        # Distinto del anterior y mas cruel: el anterior deja de anclar el
        # changelog DENTRO de una validacion que sigue corriendo; este borra la
        # llamada a la validacion entera. Es el mutante que mide D1 -- con dos
        # rutas de validacion posibles (una en `main()` y otra en el test) cada
        # una podia ser la que el producto no ejecuta. Se escribe desde la
        # fuente INTACTA, no encadenando sobre el mutante anterior, para que cada
        # mitad se pruebe sola.
        llamada = "    errors, ok = validar(root)"
        assert fuente.count(llamada) == 1, (
            "`main()` tiene que llamar a `validar(root)` EXACTAMENTE una vez: aparece "
            f"{fuente.count(llamada)} veces. Sin esta cuenta, el segundo mutante podria "
            "estar borrando una llamada que no es la que se ejecuta"
        )
        sin_validar = (
            "    errors, ok = [], []\n"
            "    # MUTANTE S2b: main() imprime su informe sin\n"
            "    # haber validado NADA. El codigo de salida sale 0\n"
            "    # y el validador declara el repo entero en verde."
        )
        with open(ruta_validador, "w", encoding="utf-8") as fh:
            fh.write(fuente.replace(llamada, sin_validar))
        rc_s2b, informe_s2b = _ejecutar_el_validador_real()
        assert "Resumen:" in informe_s2b, (
            "el mutante S2b tiene que llegar al final y printar un informe: si no, este "
            "test no esta probando el cableado de `main()` sino una excepcion. Informe:\n"
            + informe_s2b[-2000:]
        )
        assert "historial de commits:" not in informe_s2b, (
            "sin la llamada a `validar(root)` no puede ejecutarse NINGUN check, y el "
            "primero en_NOTAR que falta es el del historial. Informe:\n"
            + informe_s2b[-2000:]
        )
        assert "Resumen: 0 OK, 0 FAIL" in informe_s2b and rc_s2b == 0, (
            "esto es lo que hace peligroso al mutante: un `main()` que no valida nada "
            "sigue imprimiendo un informe y sale con 0, o sea, DECLARA EL REPO ENTERO EN "
            f"VERDE sin haber comprobado nada. rc={rc_s2b}. Informe:\n{informe_s2b[-2000:]}"
        )
    finally:
        if git_dir_previo is None:
            os.environ.pop("GIT_DIR", None)
        else:
            os.environ["GIT_DIR"] = git_dir_previo
        shutil.rmtree(tmp, ignore_errors=True)

    print("Ancla cableada en validar(): el validador real, ejecutado como subproceso sobre "
          "un arbol temporal, acusa el ciclo 999; con el ancla descableado no lo acusa, y "
          "con main() sin llamar a validar() declara 0 OK / 0 FAIL y sale con 0.")


def test_el_journal_ilegible_informa_en_vez_de_reventar_el_validador():
    """TASK-057 iter 2 (S5, MEDIO): el `except` del journal no se puede estrechar.

    El `except (ValueError, OSError)` de la lectura de `.taskmaster/rd_journal.json`
    se puede estrechar a `json.JSONDecodeError` -- que es subclase de `ValueError`,
    asi que el mutante parece innocuo -- y sobrevive porque solo se probaba el
    JSON corrupto. Con el estrechado, un `PermissionError` leyendo el journal (un
    antivirus, un OneDrive en pausa, la carpeta `.taskmaster` con otra ACL) sale
    con **traceback** en vez de con informe: el validador se cae entero y no
    comprueba NADA de lo que viene despues, que es el patron que este repo ya
    pago dos veces.

    Aqui la lectura falla con `PermissionError` de verdad, inyectado en el
    `open` del MODULO (`vd.open`), que es la unica pieza que devuelve el journal.
    El `finally` hace `del vd.open`, no `vd.open = open`, y la asercion de
    entrada comprueba que el modulo no define un `open` propio: si algun dia lo
    define, ese `del` le borraria el modulo entero y el test lo dice en vez de
    romperlo en silencio.
    """
    import shutil
    import tempfile
    import validate_docs as vd

    abierto_real = open

    def _open_que_falla_en_el_journal(camino, *args, **kwargs):
        if str(camino).replace("\\", "/").endswith(".taskmaster/rd_journal.json"):
            raise PermissionError(13, "Permiso denegado", str(camino))
        return abierto_real(camino, *args, **kwargs)

    assert not hasattr(vd, "open"), (
        "validate_docs.py define un `open` propio a nivel de modulo: el monkeypatch de "
        "este test lo taparia y el `del vd.open` del finally lo BORRARIA. Sin esta "
        "asercion el test seguiria verde rompiendo el modulo entero"
    )

    tmp = tempfile.mkdtemp(prefix="wopt_journal_")
    git_dir_previo = os.environ.get("GIT_DIR")
    try:
        # El esqueleto REAL de `validar()` (D3: se asienta por la funcion que el
        # producto llama, no por una privada) con el journal de la fixture
        # inyectado encima: es el unico `[FAIL]` posible porque el historial de
        # la fixture no aporta ciclos y el changelog copiado esta completo.
        raiz = os.path.join(tmp, "esqueleto")
        os.makedirs(raiz, exist_ok=True)
        _copiar_el_esqueleto_del_validador(raiz)
        os.environ["GIT_DIR"] = _repo_temporal_de_un_commit(
            os.path.join(tmp, "historial"), "chore: trabajo sin marcador de ciclo")

        vd.open = _open_que_falla_en_el_journal
        try:
            errors, ok = _informe_del_validador_real(raiz)
        finally:
            del vd.open

        assert not hasattr(vd, "open"), (
            "el `del vd.open` del finally tiene que dejar el modulo como estaba"
        )
        assert len(errors) == 1, (
            "un journal ILEGIBLE es un fallo del ancla y solo uno: el historial de la "
            f"fixture no aporta ciclos y el changelog esta completo. Errors: {errors}"
        )
        assert "rd_journal.json" in errors[0] and "CORRUPTO" in errors[0], (
            "el informe tiene que NOMBRAR el journal ilegible: si sale con traceback, el "
            f"validador se cae entero. Errors: {errors}"
        )
        assert "no contiene ningun ciclo valido" not in errors[0], (
            "este es el fallo de ILEGIBLE, no el de journal VACIO: son estados distintos "
            f"con mensajes distintos. Errors: {errors}"
        )
    finally:
        if git_dir_previo is None:
            os.environ.pop("GIT_DIR", None)
        else:
            os.environ["GIT_DIR"] = git_dir_previo
        shutil.rmtree(tmp, ignore_errors=True)

    print("Journal ilegible (PermissionError): informe con el motivo, sin traceback y sin "
          "tumbar el resto del validador.")


# ---------------------------------------------------------------------------
# TASK-057, ITERACION 3 (re-planificacion del Circuit Breaker). UN solo camino
# de validacion (D1-D4) y los escenarios como FILAS, no como tests.
#
# Este test FUSIONA los dos que la iteracion 2 habia separado:
# `test_el_ancla_de_commits_cae_al_git_dir_por_defecto` (S3) y
# `test_un_parser_de_marcadores_roto_no_pasa_en_verde` (S4). La razon por la que
# se fusionan no es economica: los dos median el mismo cableado --el que
# suministra `journal_cycles` y el `GIT_DIR`-- y los dos lo hacian llamando a
# `_comprobar_ancla_de_commits` con los argumentos puestos A MANO. Medido sobre
# el producto real, con el parser de marcadores muerto Y el cuarto argumento sin
# pasar, el validador daba `108 OK / 0 FAIL`: el fix S4 era codigo MUERTO en el
# camino real. Un test mas por hallazgo no converge; esto converge porque los dos
# scenarios son ahora filas de una tabla que se asienta por `validar(root)`.
# ---------------------------------------------------------------------------


def test_el_ancla_sobre_un_arbol_sintetico_tabla_de_escenarios():
    """TASK-057 iter 3 (D1, D3, D4) y cierre del ciclo #47: ocho escenarios
    del ancla, ocho FILAS.

    D1 extrajo `validar(root)` de `main()`, asi que el producto y este test
    ejecutan la MISMA ruta: si una linea de cableado desaparece, este test deja
    de ver el residuo por la misma razon que el validador deja de acusarlo. Eso
    es lo que D3 convierte en regla --todo test contractual del validador se
    asienta por `validar(root)` o por el subproceso--.

    CORRECCION de D3 (cierre del ciclo #47; no es diseno nuevo, es un texto
    que mentia). Declarar las privadas "unitarias-no-contractuales" era
    INCORRECTO y creaba una trampa, porque
    `test_el_ancla_de_commits_no_depende_del_que_escribe_el_journal` asienta
    por las privadas pasandoles los argumentos a mano y aun asi es
    CONTRACTUAL: es el UNICO guardian de tres invariantes que esta tabla NO
    nota (medido por el mutation-auditor, no por opinion):
      U1 la UNION no sustituye al journal: el arbol espejo con journal
         {46,47} e historial {46} tiene que exigir 0 errores, y esa
         construccion no cabe en una tabla que cambia de historial por fila;
      P1 ciclo != tarea: el parser tiene que IGNORAR `TASK-046`, y con ese
         mutante el repo real da `107 OK / 2 FAIL` en vez de `108 OK / 0 FAIL`;
      E1 un ancla ilegible NUNCA da verde: tiene que informar el motivo.
    La regla de D3 es "preferir `validar(root)`", no "las privadas no
    importan": un invariante que solo asienta llamando a la privada con
    argumentos inventados por el test se queda sin guardian si se borra ese
    test, y no lo nota nada mas.

    D4 hace el resto: el esqueleto real (1,7 MB) se copia UNA vez y cada
    escenario es una fila que solo reescribe el journal, el changelog y el
    `GIT_DIR`. Anadir un hallazgo futuro cuesta una fila de esta tabla, no un
    test nuevo de 40 lineas con su propia copia del arbol.

    LAS OCHO FILAS Y EL MUTANTE QUE CADA UNA MATA (esta tabla es el contrato):

    - (a) historial SIN marcadores + journal con ciclos -> `"NO aporta ningun
      ciclo"`. Mata A1: desactivar la rama `if not ciclos and journal_cycles:`.
    - (b) el MISMO historial + journal VACIO -> `"NO aporta ningun ciclo"`
      AUSENTE. Mata A1b: quitarle `and journal_cycles`. Que (a) y (b) compartan
      historial es lo que hace que la poda se delate en una de las dos, la misma
      tecnica que funciono con A2b en la iteracion 1.
    - (c) un ciclo cerrado en una RAMA lateral se acusa. Mata A2: quitar `--all`.
      Tambien mata la diferencia INVERTIDA (`ciclos_historial - ciclos_journal`),
      porque invertida este arbol acusa al reves y el recuento de errores cambia.
    - (d) journal que se lee pero no aporta ningun ciclo entero -> `"no contiene
      ningun ciclo valido"`. Mata M1: desactivar `if not journal_cycles and
      journal_usable:`.
    - (e) sin `GIT_DIR` en el entorno, el anclaje cae al repo de
      `%LOCALAPPDATA%` y lee su ciclo. Mata S3: borrar el fallback, que deja
      `None` en el entorno de `subprocess` y un `TypeError`.
    - (f) el encabezado `## CYCLE-015` BORRADO y el numero vivo solo en PROSA
      (`TASK-015` y `CYCLE-015` citados en un parrafo, sin seccion propia) ->
      dos `[FAIL]`: el de `has_jentry` y el de `missing_entries`. Mata P2 (buscar
      el numero pelado en vez del encabezado completo), P3 (lo mismo en la rama
      de arriba) y H2 (`if not has_jentry:` -> `if False:`). Cierre del ciclo #47.
    - (g) `git` falla UNA vez con `TimeoutExpired` y el ancla se lee igual en el
      segundo intento. Mata E2 (estrechar el `except Exception` a `OSError`, que
      deja el timeout saliendo con traceback y sin comprobar ni el check 6 ni el
      7) y E3 (quitar el reintento del `spawn EPERM`). Cierre del ciclo #47.
    - (h) el historial tiene `feat(ciclos 14-20)` y `feat(calidad): rango
      absurdo ciclos 1-9999`; el journal solo registra el 1 y el 14 y el
      changelog solo tiene `## CYCLE-001` y `## CYCLE-014`. Los DOS errores que
      salen tienen que nombrar EXACTAMENTE 015 a 020. Mata G1 (quitar el `s?` del
      plural: el historial deja de aportar ciclos, el residuo desaparece y los
      errores nombrarian otra cosa) y mata el `MAX_CICLOS_DE_UN_RANGO` si se
      borra (los errores nombrarian 9998 ciclos mas). Cierre del ciclo #47.

    Por que la (h) es la que puede matar a G1 y la (a) no: la (a) mide un
    historial SIN marcadores con un journal que registra, y ahi lo que decide es
    "el parser no aporta NADA". La (h) pone el numero DENTRO del sujeto en
    plural, que es justo lo que se quita al mutar el `s?`.

    LIMITACION CONOCIDA, y hay que decirla en voz alta (cierre del ciclo #47):
    las ocho filas comparten ESQUELETO y comparten helper, luego comparten
    punto ciego. Una fila solo mide la forma de arbol que construye: la (f)
    tapona P2/P3/H2 porque su changelog tiene prosa con el numero y sin el
    `## CYCLE-`; un arbol SIN esa prosa daria el MISMO veredicto a las dos
    versiones del codigo y la fila pasaria sin medir nada. La prosa de la (f)
    esta a proposito, y por eso la fila se documenta con su mutante.

    NINGUN test toca el historial real: cada fila apunta su `GIT_DIR` a un repo
    de `tempfile`, y `GIT_DIR`/`GIT_WORK_TREE`/`LOCALAPPDATA` se restauran en el
    `finally`. Sin ese `finally` un `GIT_DIR` a un temporal ya borrado
    envenenaria a la fila siguiente y el fallo apareceria dos filas mas tarde.
    La fila (g) sustituye `subprocess.run` de la stdlib (no una copia) porque es
    justo la funcion que el modulo del producto llama, y lo restaura en un
    `finally` MAS INTERNO que el del arbol: si una asercion revienta a media
    fila, el doble no puede quedar puesto para las filas siguientes ni para el
    resto de la suite.
    """
    import json
    import re
    import shutil
    import subprocess as _sp_mod
    import tempfile

    # Se captura la `run` DE VERDAD antes de tocar nada, para poder devolverla
    # aunque una fila muera entre instalar y restaurar su doble.
    _SP_RUN_DE_ORIGEN = _sp_mod.run

    # El arbol de la fila (f), con la forma EXACTA que demostro el auditor: el
    # encabezado `## CYCLE-015` borrado y el numero sobreviviendo en la prosa.
    # Cita el numero de DOS maneras a proposito, `TASK-015` y `CYCLE-015`, para
    # que la fila mate tanto el mutante que busca el numero pelado como el que
    # busca la palabra sin su `## ` delante: con un solo genero de cita el otro
    # genero de busqueda laxo pasaria en verde.
    PROSA_SOLO_EN_FILA_F = (
        "Nota de cierre, sin seccion propia: el paquete TASK-015 (CYCLE-015) se "
        "aprobo en su dia y su entrada de seccion se borro por error."
    )

    assert os.name == "nt", (
        "la fila (e) mide el fallback `%LOCALAPPDATA%`, que es la convencion de "
        "Windows que usa `git_safe_commit.get_env()` en el producto. En otro sistema "
        "el codigo del producto tampoco resolveria esa ruta, asi que el fallo seria "
        "real y no de la fixture"
    )

    tmp = tempfile.mkdtemp(prefix="wopt_tabla_ancla_")
    previos = {k: os.environ.get(k)
               for k in ("GIT_DIR", "GIT_WORK_TREE", "LOCALAPPDATA")}
    try:
        # --- El esqueleto, UNA vez (D4) ---------------------------------------
        esqueleto = os.path.join(tmp, "esqueleto")
        os.makedirs(esqueleto, exist_ok=True)
        _copiar_el_esqueleto_del_validador(esqueleto)

        # `%LOCALAPPDATA%` del host apunta a un temporal: el fallback del
        # producto no puede, ni debe, llegar al repo de la maquina.
        os.environ["LOCALAPPDATA"] = os.path.join(tmp, "localappdata")

        def _commit_vacio(directorio, asunto):
            _git_de_fixture(["-c", "user.email=ancla@woptimizer.invalid",
                             "-c", "user.name=ancla",
                             "-c", "commit.gpgsign=false",
                             "commit", "-q", "--allow-empty", "-m", asunto], directorio)

        def _historial(nombre, asunto, asunto_lateral=None):
            """Repo de un commit, o de dos si el segundo va en una RAMA lateral.

            La rama lateral se deja APARTADA (`git checkout -`) a proposito: si
            `HEAD` se quedara en ella, `git log` sin `--all` veria los dos
            commits y la fila (c) no distinguiria nada.
            """
            d = os.path.join(tmp, nombre)
            _repo_temporal_de_un_commit(d, asunto)
            if asunto_lateral is not None:
                _git_de_fixture(["checkout", "-q", "-b", "rama_lateral"], d)
                _commit_vacio(d, asunto_lateral)
                _git_de_fixture(["checkout", "-q", "-"], d)
            return os.path.join(d, ".git")

        # Pre-vuelo de la fila (c): sin esto, una fixture mal montada y un
        # `--all` borrado darian el mismo `errors == []` y no se distinguirian.
        git_lateral = _historial(
            "hist_lateral", "chore(release): cerrar ciclo #46 (TASK-056)",
            "chore(release): cerrar ciclo #77 (TASK-077)")
        con_ramas = _git_de_fixture(["log", "--format=%s", "--all"],
                                    os.path.dirname(git_lateral))
        solo_head = _git_de_fixture(["log", "--format=%s"],
                                    os.path.dirname(git_lateral))
        assert "ciclo #77" in con_ramas and "ciclo #46" in con_ramas, (
            "el repo de la fila (c) tiene que tener el ciclo 77 en una rama lateral "
            f"alcanzable con `--all`: git log --all dio {con_ramas!r}"
        )
        assert "ciclo #77" not in solo_head, (
            "el ciclo 77 tiene que ser INVISIBLE para `git log` sin `--all`, que es "
            f"justo lo que lo hace discriminante: git log dio {solo_head!r}. Si se "
            "ve, la fila (c) seguiria verde con el `--all` borrado"
        )

        sin_marcadores = _historial("hist_sin_marcadores",
                                    "feat(calidad): arreglo sin marcador de ciclo")
        # Historiales de UN ciclo cada uno, para las filas (f) y (g). Con un solo
        # ciclo y el journal que lo registra, la union no anade residuo y la
        # fila mide lo que dice medir y no el ruido de al lado.
        hist_ciclo_15 = _historial("hist_ciclo_15",
                                   "chore(release): cerrar ciclo #15 (TASK-015)")
        hist_ciclo_46 = _historial("hist_ciclo_46",
                                   "chore(release): cerrar ciclo #46 (TASK-056)")
        # Historial de la fila (h): DOS commits en la MISMA rama, porque son dos
        # caloricidades del MISMO asunto de git y por eso tienen que convivir en
        # un solo historial. El primero es el sujeto REAL del repo que depende
        # del plural (G1); el segundo es el rango absurdo, que el parser tiene
        # que ACOTAR y no expandir (si lo expandiera, el conjunto exigido
        # pasaria de 8 a 9999 y el FAIL tendria 40.000 caracteres).
        d_rangos = os.path.join(tmp, "hist_rangos")
        _repo_temporal_de_un_commit(
            d_rangos, "feat(ciclos 14-20): varios ciclos en un solo asunto")
        _commit_vacio(d_rangos, "feat(calidad): rango absurdo ciclos 1-9999")
        hist_rangos = os.path.join(d_rangos, ".git")
        log_rangos = _git_de_fixture(["log", "--format=%s"], d_rangos)
        assert "ciclos 14-20" in log_rangos and "ciclos 1-9999" in log_rangos, (
            "la fila (h) mide el RANGE, y para eso los dos asuntos tienen que "
            f"estar en el historial: `git log` dio {log_rangos!r}. Si la fixture "
            "se montara mal y el validador leyera un historial sin plural, la "
            "fila moriria por la fixture y el mutante pasaria sin ser probado"
        )
        del_fallback = os.path.join(os.environ["LOCALAPPDATA"], "woptimizer_git")
        _repo_temporal_de_un_commit(del_fallback,
                                    "chore(release): cerrar ciclo #46 (TASK-056)")
        # La fixture tiene que estar donde el codigo va a mirar. Sin esta
        # comparacion, un fallback roto y una fixture mal montada darian el
        # mismo error y no se distinguirian.
        assert os.path.expandvars(r"%LOCALAPPDATA%\woptimizer_git\.git") == \
            os.path.join(del_fallback, ".git"), (
            "la fila (e) mide el fallback, y la fixture tiene que estar en la ruta "
            "que el codigo construye. Si el host no expande `%LOCALAPPDATA%` o el "
            "producto cambia de convencion, el fallo es de la fixture y el mutante "
            "S3 pasaria sin ser probado"
        )

        def _registro(entradas_journal, entradas_changelog, prosa=""):
            """Reescribe SOLO el journal y el changelog del esqueleto.

            `prosa` se escribe DESPUES de las entradas, sin encabezado: es lo que
            permite construir el arbol de la fila (f), donde el numero del ciclo
            sigue presente en el fichero pero su seccion `## CYCLE-` ya no
            existe. Sin ese parametro esa forma de arbol no se puede montar.
            """
            with open(os.path.join(esqueleto, ".taskmaster", "rd_journal.json"),
                      "w", encoding="utf-8") as fh:
                fh.write(json.dumps(entradas_journal))
            with open(os.path.join(esqueleto, "CHANGELOG.md"), "w",
                      encoding="utf-8") as fh:
                fh.write("# Changelog\n\n### Corregido\n\n")
                for c in entradas_changelog:
                    fh.write(f"\n## CYCLE-{c:03d}\n\nEntrada del ciclo {c}.\n")
                if prosa:
                    fh.write("\n" + prosa.strip() + "\n")

        def _git_que_no_arranca_una_vez():
            """Doble de `subprocess.run` que falla UNA vez. -> `restaurar()`.

            Falla con `subprocess.TimeoutExpired`, que NO es `OSError`: es
            exactamente la excepcion que el `except Exception` del ancla alcanza
            y `except OSError` no. El docstring de `_comprobar_ancla_de_commits`
            lo afirma; esta fila lo comprueba. El segundo intento se resuelve
            con la `run` DE VERDAD, para que la fila mida el reintento y no un
            doble inventado.

            Se sustituye el atributo del MODULO de la stdlib porque es la misma
            funcion que el producto llama: un doble sobre una copia mediria el
            doble, no el validador.
            """
            import subprocess as _sp
            import validate_docs as _vd

            real = _sp.run
            estado = {"n": 0}

            def _falso(*args, **kwargs):
                estado["n"] += 1
                if estado["n"] == 1:
                    cmd = args[0] if args else "git"
                    raise _sp.TimeoutExpired(cmd=cmd, timeout=120)
                return real(*args, **kwargs)

            _sp.run = _falso
            return lambda: setattr(_sp, "run", real)

        # --- LAS OCHO FILAS -------------------------------------------------
        # Cada fila: (nombre, GIT_DIR o None, journal, entradas del changelog,
        #             doble a instalar antes de asentar (o None), funcion que
        #             juzga `errors` y `ok`).
        # `ok` se juzga tambien porque hay un fallo que NO es un error: un ancla
        # ilegible que en silencio devuelve `set()` deja `errors == []`. Judgar
        # solo `errors` daria verde a ese falso verde, que es la misma clase de
        # bug que la fila (g) existe para tapar.
        FILAS = (
            ("a: historial sin marcadores con journal que si registra",
             sin_marcadores, [{"cycle": 46}], [46], None,
             lambda e, _ok: (
                 len(e) == 1 and "NO aporta ningun ciclo" in e[0],
                 "un historial legible con 0 ciclos con marcador mientras el journal "
                 "registra 46 es un PARSER ROTO y tiene que salir como [FAIL]. Sin esta "
                 "linea el validador da verde con el parser muerto, que es el falso "
                 "verde que toda la union viene a cerrar")),
            ("b: el MISMO historial con el journal vacio",
             sin_marcadores, [], [], None,
             lambda e, _ok: (
                 not any("NO aporta ningun ciclo" in x for x in e),
                 "SIN ciclos en el journal no se puede acusar al parser de roto: el "
                 "fallo que importa ahi es el del journal, y acusar dos veces por la "
                 "misma causa entrena al lector a ignorar el semaforo. Quitarle "
                 "`and journal_cycles` a la rama sobrevive sin esta fila y solo se "
                 "delata en la (a). Errores: " + repr(e))),
            ("c: un ciclo cerrado en una rama lateral se acusa",
             git_lateral, [{"cycle": 46}], [46], None,
             lambda e, _ok: (
                 len(e) == 2
                 and any("ciclo/s 077" in x for x in e)
                 and any("077" in x for x in e if "sin entrada" in x),
                 "el ciclo 77 esta COMITEADO en una rama lateral y rd_journal.json no "
                 "lo registra: eso es un residuo y tiene que salir acusado por su "
                 "conjunto (el 077, nunca el 046, que el journal si registra) mas la "
                 "entrada `## CYCLE-077` del changelog. Con `--all` borrado, o con la "
                 "diferencia de conjuntos invertida, este arbol da 0 o 1 errores")),
            ("d: journal que se lee pero no aporta ningun ciclo entero",
             sin_marcadores, [{"nota": "sin campo cycle"}], [], None,
             lambda e, _ok: (
                 len(e) == 1 and "no contiene ningun ciclo valido" in e[0],
                 "un journal que se LEE pero no tiene ninguna entrada con 'cycle' "
                 "entero es el mismo fallo funcional que no tenerlo, y no debe pasar "
                 "en verde: desactivar la rama entera sobrevive sin esta fila")),
            ("e: sin GIT_DIR en el entorno, el anclaje cae a %LOCALAPPDATA%",
             None, [{"cycle": 1}], [1, 46], None,
             lambda e, _ok: (
                 len(e) == 1 and "ciclo/s 046" in e[0],
                 "sin `GIT_DIR` en el entorno el anclaje tiene que caer al repo de "
                 "%LOCALAPPDATA% y leer su ciclo 46, que el journal (que solo sabe "
                 "del 1) no registra. Con el fallback borrado queda `None` en el "
                 "entorno de `subprocess` y el validador revienta con TypeError "
                 "ANTES de comprobar nada")),
            ("f: encabezado del ciclo borrado y el numero solo en prosa",
             hist_ciclo_15, [{"cycle": 15}], [],
             None,
             lambda e, _ok: (
                 len(e) == 2
                 and any("registra el ciclo 015 pero" in x for x in e)
                 and any("sin entrada para el/los ciclo/s 015" in x for x in e),
                 "este arbol tiene el journal Y el historial de acuerdo en el ciclo 15 "
                 "y el changelog SIN su seccion `## CYCLE-015`: el numero solo "
                 "sobrevive en la prosa. Tapan dos guardas distintas y las dos tienen "
                 "que hablar: `has_jentry` (el ultimo ciclo del journal no tiene "
                 "entrada propia) y `missing_entries` (el conjunto exigido no esta "
                 "cubierto). Si el codigo buscara el numero como subcadena -- '015' "
                 "dentro de 'TASK-015' -- las dos darían el ciclo por cubierto y "
                 "este arbol saldria en 0 errores: es el falso verde del ciclo #15 "
                 "reabierto por otra puerta. Con `if not has_jentry:` desactivado "
                 "cae uno de los dos y el recuento tambien. Errores: "
                 + repr(e))),
            ("g: git no arranca una vez y el ancla se lee en el reintento",
             hist_ciclo_46, [{"cycle": 46}], [46],
             _git_que_no_arranca_una_vez,
             lambda e, _ok: (
                 e == []
                 and any("1 ciclo(s) corroborables" in x for x in _ok),
                 "git fallo una vez con TimeoutExpired -- que NO es OSError, es la "
                 "unica excepcion que el `except Exception` del ancla alcanza y "
                 "`except OSError` no -- y en el segundo intento el ancla tiene que "
                 "LEERSE: cero errores y su linea de informe con los ciclos "
                 "corroborables. Sin el reintento el validador declara el historial "
                 "ilegible y no comprueba ni el check 6 ni el 7; estrechando el "
                 "except, el timeout sale con traceback y no llega a ningun check. "
                 "Errores: " + repr(e))),
            ("h: un asunto en plural declara un RANGO de ciclos, acotado",
             hist_rangos, [{"cycle": 1}, {"cycle": 14}], [1, 14], None,
             lambda e, _ok: (
                 len(e) == 2
                 and any("sin entrada para el/los ciclo/s" in x for x in e)
                 and any("NO lo registra" in x for x in e)
                 # Los tres digitos nombrados por los DOS errores tienen que
                 # ser EXACTAMENTE 015 a 020. Ni uno mas (el 001 esta en el
                 # changelog y el 9999 es un rango que el parser acota), ni uno
                 # menos (los dos extremos del rango entran).
                 and set(re.findall(r"\b\d{3}\b", " ".join(e)))
                 == {"015", "016", "017", "018", "019", "020"},
                 "G1: 'ciclos 14-20' declara SIETE ciclos, no uno. Aqui el journal "
                 "solo registra el 1 y el 14 y el changelog solo tiene sus dos "
                 "entradas, asi que lo unico que puede exigir el 015 al 020 es el "
                 "HISTORIAL: sin la expansion del plural el historial no aporta "
                 "nada, no hay residuo que acusar y este arbol sale con 0 o 1 "
                 "errores. Y 'ciclos 1-9999' tiene que quedar ACOTADO al 1, que es "
                 "la entrada que el changelog tiene: sin el tope de "
                 "MAX_CICLOS_DE_UN_RANGO los errores nombrarian 9998 ciclos mas. "
                 "Errores: " + repr(e)[:600])),
        )

        for nombre, git_dir, journal, changelog, antes, juzgar in FILAS:
            # El entorno se prepara POR FILA: una fila que deja `GIT_DIR` puesto
            # envenena a la siguiente, y el fallo aparece una fila mas tarde.
            os.environ.pop("GIT_DIR", None)
            os.environ.pop("GIT_WORK_TREE", None)
            if git_dir is not None:
                os.environ["GIT_DIR"] = git_dir
            _registro(journal, changelog, PROSA_SOLO_EN_FILA_F
                      if nombre.startswith("f:") else "")

            # El doble se instala justo antes de asentar y se restaura en un
            # `finally` PROPIO: si la asercion de la fila revienta, el doble no
            # puede quedar puesto para la fila siguiente ni para el resto de la
            # suite, que corre en el mismo proceso.
            restaurar = antes() if antes is not None else (lambda: None)
            try:
                errors, ok = _informe_del_validador_real(esqueleto)
                bueno, porque = juzgar(errors, ok)
                assert bueno, (
                    f"fila ({nombre}) del ancla: {porque}. Errores: {errors}")
            finally:
                restaurar()

    finally:
        for clave, valor in previos.items():
            if valor is None:
                os.environ.pop(clave, None)
            else:
                os.environ[clave] = valor
        # Cinturon y tirantes: si una fila se murio entre instalar y restaurar el
        # doble, la suite entera seguiria con `subprocess.run` de mentira.
        _sp_real = getattr(_sp_mod, "run", None)
        if _sp_real is not None and _sp_real is not _SP_RUN_DE_ORIGEN:
            _sp_mod.run = _SP_RUN_DE_ORIGEN
        shutil.rmtree(tmp, ignore_errors=True)

    print("Ancla sobre arbol sintetico, 8 filas por validar(root): parser roto con "
          "journal que si registra, silencio con journal vacio, ciclo de rama lateral "
          "acusado, journal sin ciclo entero, fallback a %LOCALAPPDATA% sin GIT_DIR, "
          "encabezado de ciclo borrado con el numero solo en prosa, git que no "
          "arranca una vez pero cuyo ancla se lee en el reintento, y un asunto en "
          "plural que declara un rango de ciclos acotado.")


def _run_tests_sintetico(n_tests, n_headless, con_marcador=True):
    """`run_tests.py` sintetico con `n_tests` tests, `n_headless` tras el marcador.

    El marcador estructural es el que separa el reparto backend de las headless, y
    `con_marcador=False` construye la forma en la que ese reparto NO se puede
    derivar: la fila (k) lo usa para exigir que se acuse el motivo literal en vez
    de devolver `0 + 0` en verde.
    """
    lineas = ["# Sintetico: este fichero existe para que el validador derive su",
              "# total con `ast` y no lo lea de ningun sitio.", ""]
    for i in range(n_tests):
        lineas.append(f"def test_sintetico_{i}():")
        lineas.append("    pass")
        lineas.append("")
    lineas.append('if __name__ == "__main__":')
    for i in range(n_tests - n_headless):
        lineas.append(f"    test_sintetico_{i}()")
    if con_marcador and n_headless:
        lineas.append('    print("\\n--- Running Headless UI Tests ---")')
        for i in range(n_tests - n_headless, n_tests):
            lineas.append(f"    test_sintetico_{i}()")
    lineas.append('    print("\\nALL TESTS PASSED.")')
    return "\n".join(lineas) + "\n"


def test_la_deuda_exige_un_ancla_resoluble_en_toda_fila_viva():
    """TASK-060 (ciclo #49): el CHECK 8 de `validate_docs.py`, cuarenta y dos escenarios.

    El ciclo #48 sano 13 filas de la seccion `## Deuda Tecnica Conocida` y su
    auditoria cerro PARTIAL por una razon MEDIDA: 8 de 9 mutaciones sobrevivieron
    porque NADA en este repo vigilaba esa seccion (`validate_docs.py` tenia 0
    coincidencias de la palabra `Deuda`). Este test es el guardian de las
    cuarenta y dos filas de la tabla de abajo, y todas asientan por `validar(root)`
    (D3): la MISMA funcion que `main()` llama, sobre el esqueleto REAL copiado
    una vez en un `tempfile.mkdtemp()`. Nada de esto toca el repo real.

    EL TOTAL SE DERIVA CON `ast` DEL ARBOL SINTETICO (6 + 1 = 7), nunca del repo
    real. Si la cifra se leyera del repo, la fila (c) no distinguiria "derive con
    `ast`" de "lei el numero correcto a mano", que es justo el mutante que esa
    fila existe para matar.

    LAS CUARENTA Y DOS FILAS Y EL MUTANTE QUE CADA UNA MATA (esta tabla
    es el contrato, y `len(FILAS) == 42` la cuenta para que borrar una fila no salga
    gratis). DOS de ellas -- (y) y (n2) -- NO matan nada: ARCHIVAN residuos
    declarados como controles negativos, y estan marcadas como tales para que
    nadie las lea como cobertura:

    - (a) fila viva cuya unica cita no existe -> "VIVA sin ancla resoluble" (0 de
      5) y "ancla NO RESOLUBLE". Mata: no exigir ninguna fuente.
    - (b) la MISMA fila marcada CERRADA -> nada. Mata: borrar la exencion de las
      cerradas, que con esta fila sola sale en rojo.
    - (c) el panel DECLARA 42 tests (una cifra que el `ast` desmiente, porque el
      arbol sintetico tiene 7) y una fila viva la repite como verdad -> "NO es el
      derivado con ast". Mata: leer la verdad del panel en vez del codigo. La
      fila (c) declara la cifra EN LA CABECERA del panel a proposito: si solo la
      llevara la fila, un mutante que leyera el numero del panel daria el mismo
      veredicto que el codigo correcto y la fila no mediria nada.
    - (c2) el MISMO panel con un `run_tests.py` de 9 tests y la fila repitiendo la
      cifra vieja de 7 -> "NO es el derivado ... (9)". Mata: escribir el numero a
      mano. Sin esta fila, un mutante con una CONSTANTE que por casualidad vale lo
      mismo que el derivado daria el mismo veredicto que el codigo correcto, y la
      (c) sola no lo distingue: es la razon de que un test que deriva de un solo
      arbol no pueda sellarlo.
    - (d) panel de SOLO filas cerradas -> CERO errores de la seccion. Mata: marcar
      todo, que es un guard que no vigila nada.
    - (e) seccion ausente -> "no existe la seccion". Mata: buscarla por indice fijo
      o tolerar su ausencia.
    - (f1) fila cuyo unico `CERRAD` va DENTRO de codigo inline, sin ancla -> "VIVA
      sin ancla resoluble". Mata: borrar el `re.sub` de codigo inline, que la
      declararia cerrada y la dejaria sin vigilar y en verde.
    - (f2) fila que ESCRIBE el criterio y se marca CERRADA -> "se ha autoeximido".
      Mata: no comprobar que la fila del criterio siga viva.
    - (g) fila viva cuya unica fuente es una `TASK` `completed` -> "su UNICA fuente
      es una TAREA YA CERRADA". Mata: borrar la regla de la tarea cerrada, que es
      lo que haria que reabrir una fila cerrada pasara en verde.
    - (h) fila viva que declara AMARILLO con el codigo de salida sobrecargado
      presente -> "su comprobable SIGUE VIVO". Mata: borrar el suelo de gravedad,
      que es el S1 del ciclo #48.
    - (i) cita que atribuye un identificador a un fichero que existe pero no lo
      contiene -> "NO contiene el identificador que la fila le atribuye". Mata:
      resolver por EXISTENCIA y no por contenido.
    - (j) el panel declara un reparto que el `ast` desmiente -> "separa 6/1". Mata:
      no derivar el reparto, que hoy nadie vigila.
    - (k) el marcador headless NO aparece -> "NO SE ENCUENTRA el marcador". Mata:
      devolver `0 + 0` en verde cuando el reparto no se puede derivar.
    - (l) la palabra `CERRAD` en PROSA, sin veredicto y sin id trazable -> "VIVA
      sin ancla resoluble". Mata: el marcador de una sola palabra, con el que la
      fila 89 del panel se eximia a si misma con cualquier frase normal (E1).
    - (m) veredicto en NEGRITA que NIEGA el cierre ("**NO CERRADA todavia**") con un
      id que resuelve -> la fila sigue VIVA. Mata: la regla de negacion, que sin
      la regla caeria en (l) pero no en este caso: aqui hay negrita y hay id.
    - (n) fila cuya unica verdad es el propio `STATUS.md` -> "ancla NO RESOLUBLE:
      STATUS.md EXISTE pero es el propio panel". Mata: la autocertificacion del
      panel (A1), que hoy ya se da en cuatro filas reales.
    - (o) la fila DECLARA la cifra que el `ast` deriva y no cita a nadie mas -> CERO
      errores. Mata: `elif False` en S5 (la rama positiva no estaba cubierta) y la
      constante escrita a mano (C8), porque el derivado de este arbol es 7 y no 104.
    - (p) un tramo de codigo inline VACIO (`` y ` `) -> el validador devuelve INFORME
      y la fila se cuenta. Mata: el `IndexError` que tumbaba el validador entero
      sin imprimir informe.
    - (q) un fichero que SOLO MENCIONA el contrato en su documentacion, citado por
      una fila que declara AMARILLO -> NINGUN error. Mata: el predicado viejo del
      suelo, que ataba la gravedad a cualquier fichero que hablara de los codigos
      (incluido el propio `validate_docs.py`).
    - (r) veredicto en NEGRITA con un id que NO resuelve -> la fila sigue VIVA.
      Mata: la condicion 3 entera (`if ids:` -> `if True:`), que hasta esta ronda
      NO la probaba nadie: no habia un solo escenario con un veredicto en negrita
      cuyo id no resolviera, y que la condicion funcione era casualidad de
      redaccion. Los 4 controles de P1/P2/P3 ya no la tocan.
    - (s) veredicto en MINUSCULAS, con un id que si resuelve -> la fila sigue VIVA,
      y lo que lo mide es el RECUENTO de la linea `ok`, no un error: la fila tiene
      la `TASK-002` pendiente como fuente, luego sin cierre esta VIVA y en verde,
      que es exactamente el estado que se quiere. DECISION, no descuido: el
      marcador es un token EN MAYUSCULAS y esa es su forma, como la linea que
      empieza por `0` para DECLARAR un codigo de salida. Mata:
      `re.compile(r"CERRAD", re.IGNORECASE)`, que hoy sobrevive. Y fija por que V6
      es un redness ACEPTADA y no un bug: cambiar `CERRADA:` por `cerrada:` en la
      fila 90 pone las 7 exentas en rojo, y esa redness es el precio de que la
      palabra suelta en prosa no cierre nada. Queda como limite escrito.
    - (t) COMPOSICION: una fila con suelo, rebajada a AMARILLO, que se exime al
      final con un veredicto que se NIEGA a si mismo -> el suelo tiene que
      disparar. Mata: la autoexencion que apaga TRES guards con una sola frase
      (silencia la fila, y con ella el suelo), que es la combinacion que midio
      el auditor sobre la fila 88 y que ninguna fila aislada cubria.
    - (u) marcador en la PROSA, con id que resuelve y sin negacion -> la fila
      sigue VIVA. Mata: `for veredicto in _RE_NEGRITA.findall(texto)` ->
      `for veredicto in [texto]`, que es la condicion 2 (el veredicto en negrita)
      sin exigir. MEDIDO: hasta esta ronda NINGUNA fila comprobaba que el marcador
      tivesse que estar en negrita, y por eso ese mutante sobrevivia con la
      suite entera en verde. (l) y (m) no lo cierran porque las dos tienen
      negacion, que es otra guarda.
    - (v) marcador en negrita con la negacion en la PROSA, fuera del veredicto ->
      la fila sigue VIVA. Mata: borrar la comprobacion de negacion sobre la
      prosa (`_RE_NEGRITA.sub(" ", texto)`), que es la mitad de la regla de
      negacion y la que detiene la variante V2 del auditor ("**CERRADA**. NO lo
      esta: sigue pendiente"). La otra mitad --la negacion DENTRO del veredicto--
      la mata (m) y (t).

    - (w) la MISMA autocertificacion que (n) pero con otra GRAFIA del panel
      (`status.md` en minusculas) -> los DOS errores de (n). Mata: volver a
      comparar el NOMBRE ESCRITO con el string `"STATUS.md"` en vez de la
      IDENTIDAD de la ruta resuelta. MEDIDO: con la igualdad de cadena, las
      cuatro grafias (`status.md`, `./STATUS.md`, `docs/../STATUS.md` y
      `.\\STATUS.md`) certificaban al panel con `0 FAIL` y 36 anclas. El
      escenario es especifico de Windows por construccion (`realpath` no
      normaliza a minusculas en Linux), y el producto es Windows: en un sistema
      de ficheros sensible a mayusculas `status.md` NO existiria y el motivo
      seria "no existe en el arbol", que tambien es un FAIL.
    - (x4) el veredicto de cierre apunta a un CYCLE que es PREFIJO de uno
      real -> la fila sigue VIVA. Mata: que `_ciclos_cerrados` resuelva el
      `CYCLE` por SUBCADENA.
    - (x) el veredicto de cierre apunta a una TAREA PENDIENTE -> la fila sigue
      VIVA. Mata: la quinta condicion de `_esta_cerrada` entera (borrar
      `_ids_cerrados`), que es el agujero G2f' del mutation-auditor: MEDIDO
      que anadir ` - **CERRADA en TASK-059**` al final de la fila 88 la dejaba
      muda con `8 exenta(s) / 7 viva(s)`, `33` anclas y `0 FAIL`, y `TASK-059`
      esta `pending`. Lo que mide es el RECUENTO, no un error, porque la fila
      tiene `run_tests.py` como ancla y queda VIVA y en verde, que es
      exactamente el estado que se quiere.
    - (c3) el veredicto de cierre apunta a un CYCLE que solo esta en el JOURNAL
      -> la fila sigue VIVA. Mata: exigir que el ciclo exista (`_ciclos_de_la_
      fila`, que mira tambien el journal) en vez de que este CERRADO
      (`_ciclos_cerrados`, que mira solo los dos changelogs). Un ciclo se
      "traza" en cuanto se nombra y se "cierra" cuando publica su entrada: son
      dos hechos distintos, y medir solo el primero es lo que dejaba pasar al
      ataque.
    - (h2) la MISMA autocertificacion que (n) pero por un ENLACE DURO al panel
      -> los DOS errores de (n). Mata: borrar `_es_el_mismo_fichero`. MEDIDO
      que un hard link a `STATUS.md` comparte `st_dev` y `st_ino` con el panel y
      tiene `st_nlink == 2`, pero su `realpath` es OTRO, luego el filtro por
      ruta resuelta lo aceptaba como ancla legitima con `0 FAIL` de Deuda y
      colaba S1 y S2 a la vez. Un enlace simbolico y una junction SI los cierra
      `realpath`; el duro no cambia de nombre.
    - (x4) el id de la fila tiene que existir COMO ID, no como PREFIJO de otro:
      la MISMA puerta que (x) pero con un `CYCLE` que no es un ciclo de este
      repo. Mata: que `_ciclos_cerrados` resuelva un `CYCLE` por SUBCADENA
      (`if any(c in registro ...)`), que es el agujero central que midi�� el
      mutation-auditor en la ronda 5. MEDIDO: los dos changelogs publican
      `CYCLE-001`..`CYCLE-049`, luego `"CYCLE-04" in changelog` es `True` porque
      esta DENTRO de `CYCLE-045`, y la fila 88 se eximia con `8 exenta(s) /
      7 viva(s)`, `33` anclas y `0 FAIL`; con las citas de ruta de la 88 rotas
      para que no la salve otra fuente, sin el ataque `7/8/33, 1 FAIL` y con el
      `8/7/33, 0 FAIL`, o sea 24 caracteres que convierten un rojo en verde.
      `_RE_CICLOS` ademas acepta `CYCLE-0` (SIETE caracteres), y con el el
      ataque tambien cuela: por eso (x4b) lo mide con ese id truncado.
    - (x4b) el `CYCLE` truncado a SIETE caracteres (`CYCLE-0`) tampoco cierra
      nada. Es la segunda mitad del mismo ataque y mide el otro extremo: con
      solo el fix de la forma, un id de dos digitos tendria que casar contra
      `CYCLE-001` por el mismo prefijo.
    - (m2) la AUTOEXENCION no se apoya en la forma que evalua el estado: la
      fila del criterio con el marcador en la PROSA (no en un veredicto) TAMBIEN
      se acusa. Mata: el ACOPLAMIENTO `NOMBRE in fila and _porta_el_marcador_
      de_cierre(fila)`, con el que el guard que vigila al vigilante se apoyaba
      en la misma funcion que decide si la fila esta cerrada de verdad. MEDIDO
      el 2026-10-02 en la ronda 5: SIETE mutaciones de `_porta_el_marcador_de_
      cierre` (aceptar el marcador en prosa, aceptar el prefijo en vez de la
      palabra, aceptar minusculas, ignorar la negacion del veredicto, ignorar la
      de la prosa, no borrar el codigo inline, y aceptarlo en toda la fila)
      dejan el panel REAL en `7 exenta(s) / 8 viva(s)` y `0 FAIL` y las pasan
      las 42 filas de esta tabla SIN DELATAR NADA. (f2) solo ve la mitad que ya
      funciona: con el marcador en negrita los dos caminos coinciden.
    - (cyc) un `CYCLE` con ENTRADA publicada en los changelogs del arbol CIERRA
      la fila: exenta y sin errores. ES LA MITAD POSITIVA DEL FIX, y antes de
      esta fila no la probaba NADIE. MEDIDO el 2026-10-02: con
      `_ciclos_cerrados` vuelto a `return []` (X3), o con el grupo de captura
      descartado (X1), la suite entera seguia en verde, porque (x), (c3), (x4) y
      (x4b) comprueban que un ciclo NO cierra y ninguna que SI. El `CYCLE` se
      DERIVA de las entradas publicadas del arbol copiado, no se escribe a mano.
    - (p1) marcador en la PROSA con una `TASK` ya `completed` -> la fila sigue
      VIVA. Mata: el respaldo que acepta el marcador fuera del veredicto (P1) y
      `findall(texto)` -> `[texto]` (C25). MEDIDO: las dos sobreviven a la ronda 5
      entera, y la (u) no las cierra porque su id esta PENDIENTE: con un id
      pendiente la fila no se cierra de todos modos, luego esa fila no midia la
      regla que decia medir.
    - (p2) el PLURAL `**CERRADAS todas en TASK-001**` con la tarea `completed` ->
      la fila sigue VIVA. Mata: `CERRAD` en vez de la palabra entera (P2). La (u)
      y la (l) no lo cierran por la misma razon que la (p1).
    - (p3) `**cerrada en TASK-001**` (minusculas) con la tarea `completed` -> la
      fila sigue VIVA. Mata: `re.IGNORECASE` en `_RE_CERRADA` (C26). MEDIDO el
      2026-10-02: `IGNORECASE` SI muere en la suite, pero en otro test del repo y
      no en esta tabla; aqui es su muerte LOCAL, y de primera fila.
    - (p4a) `**CERRADA en TASK-001, NO lo parece**` con la tarea `completed` -> la
      fila sigue VIVA. Mata: ignorar la negacion del VEREDICTO. La (m) es el
      mismo caso con la tarea PENDIENTE, luego no lo distingue.
    - (p4b) `**CERRADA en TASK-001**` con la negacion en la PROSA y la tarea
      `completed` -> la fila sigue VIVA. Mata: borrar la negacion sobre la prosa
      (C28). La (v) es el mismo caso con la tarea PENDIENTE.
    - (p5) el marcador SOLO entre acentes graves dentro del veredicto, con la
      tarea `completed` -> la fila sigue VIVA. Mata: no borrar el codigo INLINE
      del veredicto (P5). La (f1) es el mismo caso sin id ninguno.
    - (m2c) la fila del criterio con el marcador en MINUSCULAS en su prosa NO se
      autoexime. Mata: la AUTOEXENCION insensible a caja (M2C).
    - (m2d) la fila del criterio con el marcador SOLO dentro de codigo inline NO
      se autoexime. Mata: la AUTOEXENCION que no borra el codigo inline (M2D).
    - (y) CONTROL NEGATIVO: el mismo veredicto de (x) pero con una TAREA ya
      `completed` -> la fila SI queda exenta. No mide un fix: ARCHIVA el
      residuo declarado del limite 19 para que el proximo que lo encuentre no
      lo lea como un bug sin explicar. Sin esta fila, "arreglar" el residuo
      (cerrar tambien la fila que nombra un id ya cerrado) seria cambiar la
      semantica del panel sin que nada se quejara.
    - (n2) CONTROL NEGATIVO: el veredicto de (y) con una negacion en MINUSCULA
      ("nunca se resolvio") -> la fila SI queda exenta. Tambien es un residuo
      declarado, y es la fila que hace FALLO a cualquier intento de arreglarlo
      con `re.IGNORECASE`: MEDIDO que el predicado insensible a caja lleva las
      SIETE exentas REALES a CERO y pone el repo en rojo, porque en castellano
      `no` y `nunca` son prosa ordinaria y no una forma ("**CERRADA en la cola,
      no en el cuerpo**", "**guardas que no guardaban**"). La caja es la forma,
      por el mismo argumento que ya fija el limite 18 para `CERRADA`.

    LIMITACION CONOCIDA, y hay que decirla: las cuarenta y dos filas comparten
    esqueleto y comparten helper, luego comparten punto ciego -- una fila solo
    mide la forma de arbol que construye. Las LIMITACIONES que este check tiene
    por DISENO (S1 prueba existencia y no verdad; las filas cerradas quedan
    mudas; el corte de la seccion es por linea; el suelo de gravedad es UNO)
    estan escritas con sus puntos en `docs/ai/sandbox-rules.md`, no aqui.
    """
    import json
    import os
    import shutil
    import tempfile

    tmp = tempfile.mkdtemp(prefix="wopt_deuda_anclas_")
    try:
        _copiar_el_esqueleto_del_validador(tmp)

        def _escribir(relativa, texto):
            destino = os.path.join(tmp, *relativa.split("/"))
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            with open(destino, "w", encoding="utf-8") as fh:
                fh.write(texto)

        # El total del panel se deriva de ESTE `run_tests.py`, no del real: 7
        # tests, 6 antes del marcador headless y 1 desde el.
        _escribir("run_tests.py", _run_tests_sintetico(7, 1))
        # El tablero: una `TASK` cerrada y otra pendiente, que es lo que separa la
        # fila (g) de una fila que si tiene comprobable vivo.
        _escribir(".taskmaster/tasks.json", json.dumps({"tasks": [
            {"id": "TASK-001", "status": "completed"},
            {"id": "TASK-002", "status": "pending"},
        ]}))
        # El UNICO comprobable del que se deriva el suelo de gravedad, con los
        # DOS codigos de salida `0` sobrecargados.
        _escribir(".taskmaster/git_safe_commit.py",
                  "0  WOPT_COMMIT_OK <hash> <mensaje>  commit creado de verdad\n"
                  "0  WOPT_NOOP <motivo>  no hay nada que comitear\n"
                  "1  WOPT_FAIL <operacion> <detalle>  fallo de git\n")
        # Y un fichero que SOLO MENCIONA el contrato en su documentacion. Es el
        # que separa "DECLARA" de "habla de": con el predicado viejo (un 0 antes
        # del nombre en cualquier linea) este fichero ataba el suelo a filas
        # cuya materia prima era otra, y con el de ahora no ata nada.
        _escribir("otro_wrapper.py",
                  '"""Un envoltorio que solo HABLA del contrato, no lo declara."""\n'
                  "# Devuelve 0 para WOPT_COMMIT_OK y para WOPT_NOOP, segun su\n"
                  "# documentacion. No es el contrato de salida de nada.\n")

        def _panel(filas, con_seccion=True, reparto="6 backend + 1 headless",
                   cifra="7"):
            cuerpo = ["# Panel sintetico", "",
                      "- **Suite de Tests Headless:** (`run_tests.py`, **" + cifra
                      + " tests**: " + reparto + " UI)", ""]
            if con_seccion:
                cuerpo += ["## Deuda Tecnica Conocida", ""] + list(filas) + [""]
            return "\n".join(cuerpo) + "\n## Otra Seccion\n\nCierre.\n"

        SIN_ANCLA = ("- **Fila viva sin ancla:** cita `run_testz.py`, que no existe "
                     "en el arbol, y nada mas.")
        CON_ANCLA = ("- **Fila viva con ancla:** cita `run_tests.py` y por ahi "
                     "empieza.")
        # El `CYCLE` de la fila (cyc) se DERIVA de las entradas que publica el
        # ARBOL COPIADO, y no se escribe a mano. MEDIDO el 2026-10-02: las filas
        # (x), (c3), (x4) y (x4b) comprueban que un ciclo NO cierra, y ninguna
        # comprobaba que un ciclo SI cierre, luego `_ciclos_cerrados` podia
        # volver a `return []` y la suite entera seguia en verde (X3). Un id
        # escrito a mano mediria un arbol que este test no construye, y en
        # cuanto el changelog avanzara un ciclo mediria un id que ya no esta.
        import re as _re
        _publicados = []
        for _rel in (os.path.join(".taskmaster", "CHANGELOG.md"), "CHANGELOG.md"):
            with open(os.path.join(tmp, _rel), encoding="utf-8") as _fh:
                _publicados.extend(
                    _re.findall(r"^##[ \t]+\[?(CYCLE-\d+)\]?", _fh.read(),
                                _re.MULTILINE))
        assert _publicados, (
            "el arbol copiado no publica ninguna entrada de ciclo, luego la fila "
            "(cyc) mediria un id que no existe donde el validador mira")
        CICLO_REAL = _publicados[-1]

        FILAS = (
            ("a: fila viva cuya unica cita no existe",
             _panel([SIN_ANCLA]),
             ["VIVA sin ancla resoluble (0 fuentes de 5)",
              "ancla NO RESOLUBLE: run_testz.py no existe en el arbol"], [],
             "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("b: la MISMA fila marcada CERRADA",
             _panel([SIN_ANCLA + " **\U0001f534 CERRADA en TASK-001.**"]),
             [], ["VIVA sin ancla resoluble", "ancla NO RESOLUBLE"],
             "1 exenta(s) CERRADA(s), 0 viva(s)"),
            ("c: la cifra que el panel se deriva a si mismo",
             _panel([CON_ANCLA + " Y repite como si fuera verdad la cifra que "
                     "declara el propio panel: 42 tests."], cifra="42"),
             ["NO es el derivado con ast de run_tests.py (7)"], [],
             "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("c2: el total del arbol cambia y el panel se queda con la cifra vieja",
             _panel([CON_ANCLA + " Y repite la cifra que el panel tiene por "
                     "cierta: 7 tests."]),
             ["NO es el derivado con ast de run_tests.py (9)"], [],
             "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("d: panel de SOLO filas cerradas",
             _panel([CON_ANCLA + " **\U0001f534 CERRADA en TASK-001.**",
                     "- **Fila cerrada sin ancla.** **\U0001f534 CERRADA en "
                     "TASK-001.**"]),
             [], ["Deuda"], "2 exenta(s) CERRADA(s), 0 viva(s)"),
            ("e: seccion ausente",
             _panel([CON_ANCLA], con_seccion=False),
             ["no existe la seccion de Deuda Tecnica Conocida"], [], ""),
            ("f1: el marcador de cierre DENTRO de codigo inline no exime a nadie",
             _panel(["- **Fila que se exime sola:** escribe `CERRAD` en mayusculas "
                     "dentro de codigo inline y no cita ninguna."]),
             ["VIVA sin ancla resoluble"], [],
             "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("f2: la fila que escribe el criterio no puede declararse cerrada",
             _panel(["- **Fila del criterio:** escribe "
                     "`_comprobar_deuda_con_anclas(root, errors, ok)` como la regla "
                     "de toda fila viva y se marca **\U0001f534 CERRADA en TASK-002** "
                     "para no estar vigilada."]),
             ["la fila del criterio se ha autoeximido"], [],
             "1 exenta(s) CERRADA(s), 0 viva(s)"),
            ("g: la unica fuente es una TAREA ya cerrada",
             _panel(["- **Fila reabierta:** su unica prueba es `TASK-001`, que ya "
                     "esta en `completed`."]),
             ["su UNICA fuente es una TAREA YA CERRADA: TASK-001.status == completed"],
             [], "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("h: la gravedad baja y el problema sigue vivo",
             _panel(["- **Fila rebajada:** declara AMARILLO y ancla "
                     "`git_safe_commit.py`, que sigue declarando 0."]),
             ["declara AMARILLO pero su comprobable SIGUE VIVO"], [],
             "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("i: la cita existe pero ya no apunta a lo que dice",
             _panel(["- **Fila con la cita movida:** el identificador "
                     "`notepad.exe` se le atribuye a "
                     "`docs/index.md:25 notepad.exe` y ese fichero no lo tiene."]),
             ["existe pero NO contiene el identificador que la fila le atribuye: "
              "notepad.exe"], [], "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("j: el reparto que el panel declara y el ast desmiente",
             _panel([CON_ANCLA], reparto="5 backend + 2 headless"),
             ["separa 6/1"], [], "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("k: el marcador headless no existe",
             _panel([CON_ANCLA]),
             ["NO SE ENCUENTRA el marcador estructural"], [],
             "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("l: la palabra de cierre en PROSA no exime a nadie",
             _panel(["- **Fila que habla de su cierre:** dice que esta NO esta "
                     "CERRADA todavia, y no cita ancla ninguna."]),
             ["VIVA sin ancla resoluble"], [],
             "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("m: el veredicto en negrita que NIEGA el cierre tampoco exime",
             _panel(["- **Fila que se niega a cerrar:** **NO CERRADA todavia**, "
                     "aunque TASK-002 sigue pendiente."]),
             [], [],
             "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("n: el panel no puede certificarse a si mismo",
             _panel(["- **Fila que se deriva de si misma:** su unica verdad es "
                     "`STATUS.md:9 Deuda Tecnica Conocida`, que existe."]),
             ["VIVA sin ancla resoluble",
              "ancla NO RESOLUBLE: STATUS.md EXISTE pero es el propio panel"], [],
             "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("o: la cifra que la fila DECLARA y que es la verdadera",
             _panel(["- **Fila que dice la verdad:** la suite tiene 7 tests y lo "
                     "dice sin citar a nadie mas."]),
             [],
             ["VIVA sin ancla resoluble", "NO es el derivado con ast"], ""),
            ("p: un tramo de codigo inline VACIO no tumba el validador",
             _panel(["- **Fila con comillas huerfanas:** escribe `` y ` ` en "
                     "medio, y ancla `run_tests.py`."]),
             [], ["VIVA sin ancla resoluble"], ""),
            ("q: mencionar el contrato no es DECLARAR el contrato",
             _panel(["- **Fila que solo lo menciona:** declara "
                     "\U0001f7e1 y ancla `otro_wrapper.py`, que habla del "
                     "contrato en su documentacion pero no lo declara."]),
             [], ["su comprobable SIGUE VIVO"], ""),
            ("r: veredicto en negrita con un id que NO resuelve",
             _panel(["- **Fila que se exime con un id que no existe:** anade al "
                     "final \u2014 **\U0001f534 CERRADA en CYCLE-999** \u2014 y no "
                     "cita ancla ninguna."]),
             ["VIVA sin ancla resoluble"], [],
             "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("s: el marcador en minusculas no cierra nada",
             _panel(["- **Fila que escribe su cierre en minuscula:** se declara "
                     "**cerrada** en TASK-002, que sigue pendiente."]),
             [], [],
             "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("t: la frase que se exime y se rebaja apaga el suelo a la vez",
             _panel(["- **Fila que se exime y se rebaja a la vez:** ancla "
                     "`git_safe_commit.py`, que sigue declarando 0, declara "
                     "\U0001f7e1 y anade al final \u2014 **CERRADA en TASK-002, "
                     "aunque NO lo parezca**."]),
             ["declara AMARILLO pero su comprobable SIGUE VIVO"], [],
             "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("u: el marcador tiene que estar en NEGRITA",
             _panel(["- **Fila que escribe su cierre en la prosa:** dice que "
                     "esta CERRADA en TASK-002, que sigue pendiente."]),
             [], [],
             "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("v: la negacion en la PROSA tambien niega el cierre",
             _panel(["- **Fila que se contradice:** \u2014 **CERRADA** \u2014 y "
                     "NO lo esta: sigue pendiente TASK-002."]),
             [], [],
             "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("w: el panel no se certifica a si mismo con otra GRAFIA",
             _panel(["- **Fila que se deriva de si misma en minusculas:** su "
                     "unica verdad es `status.md:9 Deuda Tecnica Conocida`, que "
                     "existe."]),
             ["VIVA sin ancla resoluble",
              "ancla NO RESOLUBLE: status.md EXISTE pero es el propio panel"], [],
             "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("x: el id que cierra la fila tiene que estar CERRADO",
             _panel(["- **Fila que se exime nombrando trabajo PENDIENTE:** ancla "
                     "`run_tests.py` y anade al final \u2014 **CERRADA en "
                     "TASK-002** \u2014, que sigue `pending` en el tablero."]),
             [], [],
             "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("c3: un CYCLE que solo esta en el journal esta EN VUELO",
             _panel(["- **Fila que se exime con un ciclo sin cerrar:** ancla "
                     "`run_tests.py` y anade al final \u2014 **CERRADA en "
                     "CYCLE-901** \u2014, que esta en el journal pero en ningun "
                     "changelog."]),
             [], [],
             "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("h2: un ENLACE DURO al panel tampoco es un ancla",
             _panel(["- **Fila que se ancla en un enlace duro:** su unica verdad "
                     "es `panel_duro.md:1 Deuda`, que existe y se resuelve."]),
             ["VIVA sin ancla resoluble",
              "ancla NO RESOLUBLE: panel_duro.md EXISTE pero es el propio panel"],
             [],
             "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("x4: un CYCLE que es PREFIJO de uno real no cierra nada",
             _panel(["- **Fila que se exime con un ciclo inexistente:** ancla "
                     "`run_tests.py` y anade al final — **CERRADA en "
                     "CYCLE-04** —, que no es un ciclo de este repo: los "
                     "changelogs publican del 001 al 049 y ese id cae DENTRO "
                     "del 045, luego la busqueda por subcadena lo resolvia. "
                     "NINGUN otro id de esta fila nombra un ciclo real."]),
             [], [],
             "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("x4b: un CYCLE truncado a siete caracteres tampoco cierra nada",
             _panel(["- **Fila que se exime con un id truncado:** ancla "
                     "`run_tests.py` y anade al final — **CERRADA en "
                     "CYCLE-0** —, que es el prefijo de todos."]),
             [], [],
             "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("m2: la fila del criterio con el marcador en la PROSA se acusa",
             _panel(["- **Fila del criterio:** escribe "
                     "`_comprobar_deuda_con_anclas(root, errors, ok)` como la "
                     "regla de toda fila viva y escribe CERRADA en TASK-002 "
                     "en su prosa, sin veredicto, para no estar vigilada."]),
             ["la fila del criterio se ha autoeximido"], [],
             "1 exenta(s) CERRADA(s), 0 viva(s)"),
            ("cyc: un CYCLE con ENTRADA publicada CIERRA la fila de verdad",
             _panel(["- **Fila que se exime con un ciclo REALMENTE cerrado:** ancla "
                     "`run_tests.py` y anade al final \u2014 **CERRADA en "
                     + CICLO_REAL + "** \u2014, que tiene entrada publicada en los "
                     "changelogs de este arbol. NINGUN otro id de esta fila nombra "
                     "trabajo ya hecho."]),
             [], [], "1 exenta(s) CERRADA(s), 0 viva(s)"),
            ("p1: el marcador en la PROSA con un id YA CERRADO tampoco exime",
             _panel(["- **Fila que escribe su cierre en la prosa:** dice que esta "
                     "CERRADA en TASK-001, que esta completed, y no lo escribe en "
                     "negrita."]),
             ["su UNICA fuente es una TAREA YA CERRADA: TASK-001.status == completed"],
             [], "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("p2: el plural CERRADAS no es el marcador de cierre",
             _panel(["- **Fila que se exime con un plural:** **CERRADAS todas en "
                     "TASK-001**, que esta completed."]),
             ["su UNICA fuente es una TAREA YA CERRADA: TASK-001.status == completed"],
             [], "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("p3: el marcador en minusculas con un id YA CERRADO no exime",
             _panel(["- **Fila que escribe su cierre en minuscula:** **cerrada en "
                     "TASK-001**, que esta completed."]),
             ["su UNICA fuente es una TAREA YA CERRADA: TASK-001.status == completed"],
             [], "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("p4a: el veredicto que NIEGA el cierre no exime con un id YA CERRADO",
             _panel(["- **Fila que se niega a cerrar:** **CERRADA en TASK-001, NO lo "
                     "parece**, que esta completed."]),
             ["su UNICA fuente es una TAREA YA CERRADA: TASK-001.status == completed"],
             [], "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("p4b: la prosa que NIEGA el cierre no exime con un id YA CERRADO",
             _panel(["- **Fila que se contradice:** **CERRADA en TASK-001**, que esta "
                     "completed, y NO lo esta de verdad: sigue pendiente de cerrar."]),
             ["su UNICA fuente es una TAREA YA CERRADA: TASK-001.status == completed"],
             [], "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("p5: el marcador dentro de codigo inline no exime con un id YA CERRADO",
             _panel(["- **Fila que escribe el marcador entrecomillado:** **`CERRADA` en "
                     "TASK-001**, que esta completed."]),
             ["su UNICA fuente es una TAREA YA CERRADA: TASK-001.status == completed"],
             [], "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("m2c: la fila del criterio en minusculas NO se autoexime",
             _panel(["- **Fila del criterio:** escribe "
                     "`_comprobar_deuda_con_anclas(root, errors, ok)` como la regla "
                     "de toda fila viva y dice en su prosa que esta cerrada en "
                     "TASK-002, en minusculas y sin veredicto, para no estar "
                     "vigilada."]),
             [], ["se ha autoeximido"],
             "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("m2d: la fila del criterio con el marcador en codigo inline NO se autoexime",
             _panel(["- **Fila del criterio:** escribe "
                     "`_comprobar_deuda_con_anclas(root, errors, ok)` como la regla "
                     "de toda fila viva y escribe `CERRADA en TASK-002` entre "
                     "acentos graves, para no estar vigilada."]),
             [], ["se ha autoeximido"],
             "0 exenta(s) CERRADA(s), 1 viva(s)"),
            ("y: CONTROL NEGATIVO, un id YA CERRADO si cierra la fila",
             _panel(["- **Fila cerrada de verdad:** ancla `run_tests.py` y anade "
                     "al final \u2014 **CERRADA en TASK-001** \u2014, que esta "
                     "`completed`."]),
             [], [],
             "1 exenta(s) CERRADA(s), 0 viva(s)"),
            ("n2: CONTROL NEGATIVO, la negacion en minuscula NO se ve",
             _panel(["- **Fila que se exime y se niega en minuscula:** ancla "
                     "`run_tests.py` y anade al final \u2014 **CERRADA en "
                     "TASK-001, nunca se resolvio** \u2014."]),
             [], [],
             "1 exenta(s) CERRADA(s), 0 viva(s)"),
        )
        # El numero de filas es un CONTRATO, no una consecuencia: sin esta
        # cuenta, borrar tres escenarios deja la suite verde con el mismo
        # recuento de tests (S1 del mutation-auditor, ciclo #49, MEDIDO).
        assert len(FILAS) == 42, (
            "la tabla de escenarios del check 8 tiene "
            f"{len(FILAS)} filas y su contrato son 42. Una fila que se borra sin "
            "su cuenta deja el test en verde midiendo menos de lo que dice medir"
        )

        # Dos escenarios cambian el `run_tests.py` del arbol: (c2) cambia el
        # TOTAL y (k) borra el marcador. Se reescribe en cada iteracion, porque
        # una fila que heredase el arbol de la anterior mediria otra cosa.
        OVERRIDES = {
            "c2: el total del arbol cambia y el panel se queda con la cifra vieja":
                _run_tests_sintetico(9, 1),
            "k: el marcador headless no existe":
                _run_tests_sintetico(7, 0, con_marcador=False),
        }

        # Dos escenarios necesitan tocar el ARBOL, no solo el texto del panel, y
        # por eso no caben en `OVERRIDES`: (h2) tiene que CREAR un enlace duro
        # a `STATUS.md` y (c3) tiene que escribir un journal. Se aplican
        # DESPUES de escribir el panel, que es cuando el enlace duro puede
        # existir, y el estado que meten se RESTAURA en cada iteracion por el
        # mismo motivo por el que se reescribe `run_tests.py`: una fila que
        # heredase el arbol de la anterior mediria otra cosa.
        raiz_repo = os.path.dirname(os.path.abspath(__file__))

        def _journal_con_un_ciclo_en_vuelo(destino):
            # La raiz del journal es una LISTA de ciclos, no un dict.
            #
            # Y el literal `CYCLE-NNN` hay que escribirlo A MANO: MEDIDO que el
            # journal REAL guarda el ciclo como numero (`"cycle": 45`) y no
            # contiene ni una sola vez la forma `CYCLE-045` que buscan
            # `_RE_CICLOS` y `_ciclos_de_la_fila`. O sea que la rama del journal
            # de ese registro esta INERTE en este repo, y esta fila es la
            # unica que la ejecuta de verdad: sin el literal en el `summary`,
            # `CYCLE-901` no resolveria por ningun registro, la fila quedaria
            # VIVA por el motivo de (r) y el mutante de `_ciclos_cerrados`
            # SOBREVIVIRIA sin que nada lo delatara.
            with open(os.path.join(raiz_repo, ".taskmaster", "rd_journal.json"),
                      encoding="utf-8") as fh:
                journal = json.load(fh)
            assert isinstance(journal, list), (
                "el journal cambio de forma y esta fila mediria otra cosa: se "
                f"ha leido {type(journal).__name__} donde se esperaba una lista")
            journal.append({"cycle": 901, "state": "running",
                            "summary": "CYCLE-901 en vuelo, sin changelog"})
            _escribir(".taskmaster/rd_journal.json", json.dumps(journal))

        def _enlace_duro_al_panel(destino):
            # Un enlace DURO y no uno simbolico: `realpath` resuelve el
            # simbolico al panel y lo cerraba, mientras que el duro comparte
            # `st_ino` y NO cambia de nombre, luego es el caso que
            # `_es_el_mismo_fichero` existe para cerrar. MEDIDO: con el solo
            # `realpath` la fila (h2) pasaba con `0 FAIL` y colaba S1 y S2.
            os.link(os.path.join(destino, "STATUS.md"),
                    os.path.join(destino, "panel_duro.md"))

        def _borrar_si_existe(ruta):
            try:
                os.remove(ruta)
            except OSError:
                pass

        PREPARA = {
            "c3: un CYCLE que solo esta en el journal esta EN VUELO":
                _journal_con_un_ciclo_en_vuelo,
            "h2: un ENLACE DURO al panel tampoco es un ancla": _enlace_duro_al_panel,
        }

        for nombre, panel, esperados, prohibidos, recuento_esperado in FILAS:
            _escribir("STATUS.md", panel)
            _escribir("run_tests.py", _run_tests_sintetico(7, 1))
            if nombre in OVERRIDES:
                _escribir("run_tests.py", OVERRIDES[nombre])
            # El estado que meten las filas anteriores se deshace SIEMPRE, no
            # solo cuando la siguiente fila lo necesita: si no, (c3) y (h2)
            # contaminarian a las que vienen despues.
            shutil.copy2(os.path.join(raiz_repo, ".taskmaster", "rd_journal.json"),
                         os.path.join(tmp, ".taskmaster", "rd_journal.json"))
            _borrar_si_existe(os.path.join(tmp, "panel_duro.md"))
            if nombre in PREPARA:
                PREPARA[nombre](tmp)
            errors, ok = _informe_del_validador_real(tmp)
            faltan = [e for e in esperados if not any(e in x for x in errors)]
            assert not faltan, (
                f"escenario {nombre}: el check NO acuso {faltan!r}. Sin el fix esta "
                "fila pasa en verde, que es el falso verde que este check existe "
                "para cerrar. Errores del informe: " + repr(errors))
            sobran = [p for p in prohibidos if any(p in x for x in errors)]
            assert not sobran, (
                f"escenario {nombre}: el check acuso {sobran!r} y no debia. Un guard "
                "que marca de mas entrena al lector a ignorar el semaforo, que es "
                "como se muere un validador. Errores del informe: " + repr(errors))
            # El RECUENTO de la linea `ok` es un contrato y no una decoracion:
            # sin esta asercion una fila que se autoexime (m) deja la suite
            # verde sin mover un solo numero, que es la forma que tenian los
            # autoexencios antes de que el cierre exigiera un veredicto.
            if recuento_esperado:
                linea = [o for o in ok if "Deuda Tecnica Conocida:" in o]
                assert linea, (
                    f"escenario {nombre}: el check NO imprimio su linea `ok` de la "
                    "seccion. Amputar el check 8 entero baja el validador a 114 OK "
                    "y 0 FAIL, que es verde: sin esta asercion nadie vigila el "
                    "recuento. Linea ok: " + repr(ok))
                assert recuento_esperado in linea[0], (
                    f"escenario {nombre}: la linea `ok` dice {linea[0]!r} y el "
                    f"recuento que mide este escenario es {recuento_esperado!r}")

        # --- EL PANEL REAL, QUE HASTA AQUI NO LO EJECUTABA NADIE --------------
        # MEDIDO el 2026-10-02 (ronda 6): los TRES llamantes de `validar` de esta
        # suite apuntaban a un ARBOL TEMPORAL, luego la mitad POSITIVA del fix --
        # la que pregunta si un `CYCLE` de verdad cierra una fila-- solo la
        # ejecutaba `python validate_docs.py`, que es un comando y no un test.
        # Este bloque ata el guardian al repo de verdad, y lo que afirma es la
        # LINEA `ok` de la seccion, no un numero escrito a mano.
        #
        # El recuento de filas es PROPIO y no `_filas_de_deuda`: un guardian que
        # cuenta con la misma funcion que juzga no puede notar que esa funcion
        # dejo de contar, que es justo lo que hace un `return` borrado.
        raiz_real = os.path.dirname(os.path.abspath(__file__))
        errors_real, ok_real = _informe_del_validador_real(raiz_real)
        with open(os.path.join(raiz_real, "STATUS.md"), encoding="utf-8") as fh:
            cuerpo_real = fh.read()
        lineas_real = cuerpo_real.split("\n")
        inicio = None
        for i, linea in enumerate(lineas_real):
            if linea.startswith("## ") and "Deuda" in linea:
                inicio = i
                break
        assert inicio is not None, (
            "el STATUS.md REAL no tiene seccion de Deuda, luego la linea `ok` que "
            "se comprueba a continuacion no existiria y el fallo seria invisible")
        fin = len(lineas_real)
        for j in range(inicio + 1, len(lineas_real)):
            if lineas_real[j].startswith("## "):
                fin = j
                break
        filas_reales = [x for x in lineas_real[inicio + 1:fin]
                        if x.startswith("- **")]
        linea_ok = [o for o in ok_real if "Deuda Tecnica Conocida:" in o]
        assert linea_ok, (
            "el validador NO imprimio su linea `ok` de la seccion sobre el REPO "
            "REAL: amortuar el check 8 entero baja el validador a 114 OK y 0 FAIL, "
            "que es verde. Linea ok: " + repr(ok_real))
        encontrado = _re.search(
            r": (\d+) fila\(s\), (\d+) exenta\(s\) CERRADA\(s\), (\d+) viva\(s\)",
            linea_ok[0])
        assert encontrado, (
            "la linea `ok` del repo real no tiene la forma que este test mide: "
            f"{linea_ok[0]!r}")
        n_filas, exentas, vivas = (int(x) for x in encontrado.groups())
        assert n_filas == len(filas_reales), (
            f"la linea `ok` cuenta {n_filas} fila(s) y el STATUS.md real tiene "
            f"{len(filas_reales)}: el check 8 y el panel ya no hablan de la misma "
            "seccion. Linea ok: " + repr(linea_ok[0]))
        assert exentas + vivas == n_filas, (
            f"la linea `ok` no cuadra: {exentas} exenta(s) + {vivas} viva(s) != "
            f"{n_filas} fila(s). Una fila que se salta uno de los dos bancos deja "
            "el recuento sin cerrar y nadie lo ve")
        assert exentas >= 1 and vivas >= 1, (
            f"el panel real tiene {exentas} exenta(s) y {vivas} viva(s): o el "
            "criterio se apago entero o el panel entero se dio por cerrado, y las "
            "dos son un panel que no vigila. Linea ok: " + repr(linea_ok[0]))
        redness = [e for e in errors_real if e.startswith("STATUS.md Deuda")
                   or "Deuda Tecnica Conocida" in e]
        assert not redness, (
            "el panel REAL esta en rojo y la suite lo daba por bueno: "
            + repr(redness))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("Check 8 de la Deuda Tecnica Conocida, 42 filas por validar(root): ancla "
          "viva rota, la misma cerrada, la cifra autoderivada y la del total "
          "cambiado, panel solo de cerradas, seccion ausente, CERRADA dentro de "
          "codigo inline, la fila del criterio autoeximida, la unica fuente en una "
          "TAREA cerrada, gravedad rebajada con el comprobable vivo, cita que ya "
          "no apunta a lo que dice, reparto y marcador headless que el ast "
          "desmiente, la palabra de cierre en prosa y el veredicto que la niega, "
          "el panel certificandose a si mismo, la cifra declarada que es la "
          "verdad, el tramo de codigo inline vacio, un fichero que solo "
          "menciona el contrato, el veredicto con un id que no resuelve, el "
          "marcador en minusculas, la frase que apaga la fila y el suelo a la "
          "vez, el marcador que tiene que estar en negrita, la negacion que "
          "esta en la prosa, el panel que se cita a si mismo con otra grafia, el "
          "cierre que apunta a una TAREA pendiente, el CYCLE que solo esta en "
          "el journal, el CYCLE que es PREFIJO de uno real, el CYCLE truncado a "
          "siete caracteres, la fila del criterio con el marcador en la prosa, "
          "el ciclo REAL que cierra la fila de verdad, el marcador en la prosa "
          "con un id ya cerrado, el plural que no es la palabra, las minusculas "
          "con un id ya cerrado, la negacion del veredicto y la de la prosa con "
          "un id ya cerrado, el marcador entrecomillado con un id ya cerrado, la "
          "fila del criterio en minusculas y con el marcador entrecomillado, el "
          "panel REAL con su linea `ok` comprobada fila a fila, el enlace DURO "
          "al panel, y los dos controles negativos "
          "que archivan el residuo declarado.")




def test_el_estado_que_elige_el_usuario_se_persiste_de_verdad():
    """TASK-062: la eleccion de "arrancar / matar" no se guardaba. NUNCA.

    **El bug.** `get_all_packs()` devuelve COPIAS defensivas (`model_copy(deep=True)`
    sobre una cache de dos capas) y `save()` serializa `self._data`, que esa copia
    NUNCA toca. Las tres vistas mutaban la copia y guardaban el estado interno, asi
    que la eleccion se perdia entera: el desplegable cambiaba en pantalla, se
    escribia el fichero con el valor viejo y al recargar volvia al anterior. Por eso
    era tan traicionero: *parecia* que funcionaba. Y `save()` ademas no invalida la
    cache, asi que la UI seguia enseñando el valor viejo aunque la mutacion llegara.

    **Por que dos mitades y no un solo assert.** `change_default` vive dentro de
    `_render_pack_card` y solo se alcanza por el `command` de un `CTkOptionMenu`, es
    decir con una ventana de Tk. Este repo no abre ventanas en la suite, asi que la
    mitad A demuestra **la causa** con el `PackService` REAL sobre disco temporal --
    si el servicio dejara de copiar, la mitad B dejaria de ser necesaria--, y la
    mitad B es una guarda `ast` que ata los TRES call sites al metodo que persiste.

    MATA:
      * `update_pack(...)` -> `save()` en cualquiera de los tres sitios -> B;
      * borrar el `update_pack` entero de `change_default` -> B;
      * `get_all_packs()` sin `deep=True` (volver a devolver los mismos objetos) -> A;
      * `save()` que dejara de serializar `_data` -> A;
      * `update_pack()` que dejara de invalidar la cache -> A (el servicio volveria a
        servir el valor viejo aunque el fichero estuviera bien escrito).
    """
    import ast
    import inspect
    import tempfile
    import textwrap
    from woptimizer.services.pack_service import PackService as _PackService
    from woptimizer.ui.views.pack_manager_view import PackManagerView as _PMV
    from woptimizer.ui.views.process_manager_view import ProcessManagerView as _PMProcs

    # --- (A) LA CAUSA, con el servicio REAL y disco temporal -----------------
    with tempfile.TemporaryDirectory() as tmp:
        ruta = os.path.join(tmp, "profiles.json")
        svc = _PackService(data_path=ruta)

        # M1: mutar una copia NO llega al disco, aunque se llame a `save()`.
        # Esta es exactamente la razon por la que el bug no se veia.
        copia = svc.get_all_packs()["gaming"]
        copia.default_action = "start"
        svc.save()
        releido = _PackService(data_path=ruta).get_all_packs()["gaming"]
        assert releido.default_action == "kill", (
            f"`save()` sobre una copia de `get_all_packs()` TIENE que perder el cambio; si lo "
            f"guarda, el servicio dejo de devolver copias defensivas y la mitad B de este test "
            f"habria dejado de ser necesaria. Leido: {releido.default_action!r}"
        )

        # M2: la via que SI persiste, y ademas invalida la cache.
        svc2 = _PackService(data_path=ruta)
        svc2.get_all_packs()                      # calienta la cache de 2 capas
        p = svc2.get_all_packs()["gaming"]
        p.default_action = "start"
        svc2.update_pack(p)
        assert svc2._cached_all_packs is None, (
            "update_pack() debe invalidar la cache: si no, `get_all_packs()` seguiria "
            "sirviendo el valor viejo y la UI no se enteraria del cambio"
        )
        releido2 = _PackService(data_path=ruta).get_all_packs()["gaming"]
        assert releido2.default_action == "start", (
            f"update_pack() tiene que persistir en el fichero; leido del disco: "
            f"{releido2.default_action!r}"
        )

    # --- (B) LOS TRES CALL SITES, por forma ---------------------------------
    def _persistencia(fuente):
        arbol = ast.parse(textwrap.dedent(inspect.getsource(fuente)))
        out = []
        for nodo in ast.walk(arbol):
            f = getattr(nodo, "func", None)
            if (isinstance(f, ast.Attribute) and f.attr in ("update_pack", "save")
                    and isinstance(f.value, ast.Attribute)
                    and f.value.attr == "pack_service"):
                out.append(f.attr)
        return out

    fuente_change = textwrap.dedent(inspect.getsource(_PMV._render_pack_card))
    assert "update_pack(p)" in fuente_change, (
        "`change_default` debe persistir con `update_pack`. Con `save()` el cambio se "
        "pierde: `get_all_packs()` devuelve una copia y `save()` serializa `_data`, que "
        "la copia nunca toca. Es el bug que reporto el usuario."
    )
    assert "self.pack_service.save()" not in fuente_change, (
        "`_render_pack_card` no debe llamar a `save()`: no persiste la copia ni invalida "
        "la cache. Aqui caen DOS call sites --la accion por defecto y las categorias "
        "automaticas--, y el segundo decide que cierra el Gaming Mode. El guard cita "
        "la llamada prohibida, no solo la exigida."
    )
    assert "update_pack(actual)" in fuente_change, (
        "El toggle de categorias automaticas debe releer el pack y persistirlo con "
        "`update_pack`: mutar la copia de la tarjeta y llamar a `save()` no guarda nada."
    )

    ll_remove = _persistencia(_PMV.remove_app_from_pack)
    assert "save" not in ll_remove, (
        f"`remove_app_from_pack` llama a `save()`: quitar una app de un pack no se guarda. "
        f"Llamadas de persistencia: {ll_remove}"
    )
    assert "update_pack" in ll_remove, f"`remove_app_from_pack` debe usar `update_pack`: {ll_remove}"

    ll_add = _persistencia(_PMProcs.on_add_to_pack)
    assert "save" not in ll_add, (
        f"`on_add_to_pack` llama a `save()`: ANADIR apps a un pack no se guarda, y esa es "
        f"la via principal para construir packs. Llamadas: {ll_add}"
    )
    assert "update_pack" in ll_add, f"`on_add_to_pack` debe usar `update_pack`: {ll_add}"

    print("La accion por defecto, y las apps de un pack, SE PERSISTEN de verdad (TASK-062).")


if __name__ == "__main__":
    # TASK-028 (FIX-010): el canal de log se declara aqui, no se hereda de
    # importar `config`. Sin esta llamada, los `logger.warning` de la suite caen
    # al `lastResort` de la stdlib (stderr) en vez de a `woptimizer.log`, que es
    # justo el contrato que promete `docs/ai/architecture.md` §5.
    from woptimizer.config import setup_logging as _setup_logging
    _setup_logging()
    # TASK-062: la accion por defecto de un pack NO se guardaba y ningun test lo miraba.
    # `change_default` es un closure dentro de `_render_pack_card`, alcanzable solo por el
    # `command` de un OptionMenu, asi que su mitad ejecutable es una guarda `ast`; la mitad
    # que SI se ejecuta prueba la CAUSA con el `PackService` real sobre disco temporal.
    # Suite: 104 -> 105.
    test_el_estado_que_elige_el_usuario_se_persiste_de_verdad()

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
    test_process_db_schema_integrity()
    test_safety_badge_category_priority_order()
    test_gaming_service_should_kill()
    test_execute_gaming_pack_integration()
    test_gaming_service_session_restoration()
    test_pack_service_crud()
    test_pack_service_delete()
    test_pack_service_favorites_acumulan()
    test_pack_service_favorite_contracts_and_resilience()
    test_pack_service_reset_gaming()
    test_gaming_pack_lists_isolated_from_global()
    test_cache_ttl_and_invalidation()
    test_kill_recursive()
    test_git_safe_commit_fail_safe()
    test_double_tap_guard()
    test_no_system_process_is_killable()
    # TASK-026: FIX-001 / FIX-005 / FIX-007 / FIX-009
    test_gaming_pack_fallback_is_deep_copy()
    test_default_meta_matches_canonical_otros()
    test_pack_service_backup_and_recovery()
    test_do_load_publica_sin_tk()
    # TASK-030: sondas P1-P8 (cada una con la mutacion exacta que mata)
    test_save_atomic_nunca_toca_el_principal()
    test_publicar_no_trunca_el_principal()
    test_save_no_escribe_si_la_rotacion_no_puede_leer()
    test_corrupcion_sin_backup_intenta_volar()
    test_forma_legacy_no_tumba_la_app()
    test_todas_las_clases_de_corrupcion_se_recuperan()
    test_oserror_de_lectura_no_es_corrupcion()
    test_attribute_error_ajeno_no_es_corrupcion()
    # TASK-031: sondas L1-L7 (hojas validadas, .bak intacto, load() read-only)
    test_la_rotacion_usa_la_misma_puerta_que_load()
    test_la_hoja_malformada_se_clasifica()
    test_load_no_escribe()
    test_la_recuperacion_no_sobrescribe_el_bak()
    test_sin_bak_legible_no_se_sobrescribe_el_principal()
    test_un_campo_desconocido_no_es_corrupcion_y_no_se_borra()
    test_packs_y_profiles_a_la_vez_es_corrupcion()
    # TASK-031 iteracion 2: L8-L10 (raiz mal escrita, error de escritura,
    # identidad clave==id) + L2 con la fila is_gaming y la fixture sin "id"
    test_la_raiz_mal_escrita_no_destruye_los_packs()
    test_un_error_de_escritura_no_es_un_campo_desconocido()
    test_la_clave_del_mapa_es_la_identidad_del_pack()
    # TASK-031 iteracion 3: L11 (la raiz LEGACY conserva sus claves extra) y
    # L12 (una clave raiz nunca es un error de escritura) + L2 con las filas de
    # `is_favorite` que si coaccionan y L9 con las variantes de GRAFIA.
    test_la_raiz_legada_conserva_sus_claves_extra()
    test_una_clave_raiz_nunca_es_un_error_de_escritura()
    # TASK-027: FIX-003 (arranque seguro + escritor), FIX-004 (orden de
    # categorias), FIX-006 (desmarcar favorito)
    test_arranque_de_apps_no_usa_shell()
    # TASK-027 iteracion 2 (el mutation-auditor dio FAIL): junction/symlink,
    # hermano de prefijo (M10), caja de las letras y guarda anti-shell ciega.
    test_un_junction_no_puede_colar_lo_que_hay_detras()
    test_la_contencion_no_acepta_un_hermano_de_prefijo()
    test_la_contencion_no_depende_de_la_caja()
    test_la_guarda_de_shell_true_ve_atributos_y_aliases()
    # TASK-027 iteracion 3: el hard link y su hermano (la COPIA PLENA) no
    # cuelan. El cierre es la REGLA 9 (`_es_imagen_pe`), no `st_nlink`: medido,
    # el 8,32% de los .exe/.com instalados tienen enlaces duros legitimos.
    test_un_hard_link_no_es_una_hoja_y_el_script_no_pasa()
    test_el_gestor_guarda_la_ruta_absoluta()
    test_orden_de_categorias_no_es_alfabetico()
    test_toggle_favorite_desmarca()
    # TASK-028: FIX-010 (el log va a fichero, no a stderr) y FIX-018 (la version
    # no puede desincronizarse entre pyproject.toml y __init__.py).
    test_logging_va_a_fichero_y_no_a_stderr()
    test_la_consulta_de_version_no_puede_desincronizarse()
    # TASK-028 iteracion 2: los 16 supervivientes del mutation-auditor. Cada
    # una con la mutacion que mata escrita en su docstring.
    test_el_archivo_legacy_esta_versionado_y_no_vuelve_a_la_raiz()
    test_el_punto_de_entrada_declara_el_log_antes_de_los_servicios()
    test_process_list_file_sigue_siendo_un_contrato()
    test_la_documentacion_del_blindaje_no_puede_desfasarse()
    # TASK-037 (ciclo 27): la instrumentacion que vigila al producto, no el
    # producto. La rama `n_tests is None` del validador era codigo muerto y el
    # alcance del guard de llamantes estaba escrito a mano y desfasado.
    test_el_validador_avisa_en_vez_de_tirar_la_excepcion()
    test_el_alcance_del_guard_de_llamantes_se_deriva_del_arbol()
    test_el_log_rota_con_el_limite_declarado()
    test_config_no_configura_nada_al_importarse()
    # TASK-029: Sistema de diseno y refresco visual del front (UI-001 a UI-012)
    test_no_literal_colors_in_views()
    test_theme_tokens_complete()
    test_contrast_wcag_aa()
    test_hit_targets_minimum()
    test_semantic_color_contract()
    test_woptimizer_ico_exists_and_valid()
    # TASK-033: Optimizacion de latencia y throughput en el escaneo de procesos
    test_scan_latency_and_lazy_exe_resolution()
    # TASK-034: Validacion estricta y contratos de modelos Pydantic
    test_models_strict_validation_and_contracts()
    # TASK-040: Caché inmutable de packs y optimización de latencia en filtro
    test_pack_service_cache_invalidation_and_immutability()
    test_process_filter_performance()
    # TASK-041: Persistencia de campos extra Pydantic y precisión en freed_mb
    test_pydantic_extra_fields_persistence()
    test_freed_mb_calculation_precision()
    # TASK-042: Robustez de concurrencia y captura defensiva
    test_notification_service_rlock_and_concurrency()
    test_process_service_kill_defensive_zombie_and_oserror()
    # TASK-045: Memoización de categorización e invalidación atómica
    test_process_categorization_latency_and_memoization()
    # TASK-047: Resiliencia de concurrencia y recuperación en GamingService
    test_gaming_service_rlock_and_concurrency()
    # TASK-050: Contratos de descarga remota de DB y fallback observable
    test_process_service_db_download_contracts()
    # TASK-054: Contratos de veracidad y actualidad en docs/api.md y docs/index.md (v3)
    test_docs_api_and_index_v3_contracts()
    # TASK-055: Guard anti-regresión y contratos de archivo de scripts test_*.py legacy
    test_no_legacy_test_files_in_root()
    # TASK-056: Guard AST de código muerto en src/woptimizer/**
    test_dead_code_ast_guard()
    # TASK-057: el validador exige la UNION de journal e historial de commits,
    # para que el registro que se valida no sea el unico testigo de si un ciclo
    # se cerro. Cuatro sondas: parser ciclo!=tarea, residuo comiteado sin
    # journal, union (no sustitucion) y ancla ilegible con informe.
    test_el_ancla_de_commits_no_depende_del_que_escribe_el_journal()
    # TASK-057 iteracion 2 (mutation-auditor: FAIL). Los cuatro hallazgos que
    # devolvio el auditor, cada uno con la mutacion exacta que lo mata:
    #   S2 el validador REAL como subproceso, para que borrar el cableado de
    #      validar() no pueda salir en verde (y con sus dos mitades mutantes),
    #   S5 el journal ilegible con PermissionError: informe, no traceback,
    #   S3 el fallback a %LOCALAPPDATA% cuando el entorno no trae GIT_DIR,
    #   S4 el parser de marcadores roto: [FAIL] solo si el journal aporta ciclos.
    # TASK-057 iteracion 3 (Circuit Breaker: dos intentos con FAIL seguidos).
    # S3 y S4 se FUSIONAN en una tabla de escenarios sobre el esqueleto real, y
    # los tres asientan por `validar(root)` (D1) en vez de llamar a las privadas
    # pasandoles los argumentos a mano (D3). Suite: 104 -> 103.
    #
    # Cierre del ciclo #47: la tabla paso de cinco a SIETE filas (P2/P3/H2 y
    # E2/E3) y de siete a OCHO con la (h) de G1, y la suite NO crecio: un hallazgo se paga con una fila. Ademas se
    # corrige la lectura de D3 de arriba: las privadas no son "unitarias no
    # contractuales", y por eso la fila (f) va aqui y no en el test que las usa.
    test_el_ancla_se_cablea_en_el_camino_real_del_validador()
    test_el_journal_ilegible_informa_en_vez_de_reventar_el_validador()
    test_el_ancla_sobre_un_arbol_sintetico_tabla_de_escenarios()
    # TASK-060 (ciclo #49): el CHECK 8 de `validate_docs.py` vigila la seccion de
    # Deuda Tecnica Conocida de `STATUS.md`, que gobierna el Paso 1 del bucle y no
    # la miraba nadie (`validate_docs.py` tenia 0 coincidencias de `Deuda`). El
    # reparto 94+10 del panel tambien se deriva, en el check 7 y no aqui. Suite:
    # 103 -> 104; trece escenarios en una tabla, sobre arbol sintetico.
    test_la_deuda_exige_un_ancla_resoluble_en_toda_fila_viva()
    print("\n--- Running Headless UI Tests ---")
    test_main_window_navigation_transitions()
    # TASK-035: Telemetria y feedback visual unificado en ejecucion de packs.
    # Ciclo 26: el mutation-auditor dio FAIL y la sonda se partio en dos, la
    # guarda AST por un lado y la honestidad del feedback por otro.
    test_los_workers_de_pack_solo_publican_por_after()
    test_el_feedback_de_pack_dice_la_verdad()
    # Ciclo 26 iteracion 3: la TERCERA puerta de feedback (Gestor de Procesos), que
    # el fix de la iteracion 2 y la guarda AST no tocaban.
    test_el_gestor_de_procesos_tampoco_miente()
    # TASK-043: Restauración de Sesión Gaming desde el tray
    test_tray_session_restoration_integration()
    test_headless_ui()
    # TASK-046: Contratos de ciclo de vida y widgets en Confirmable mixin
    test_confirmable_mixin_lifecycle_and_widget_contracts()
    # TASK-049: Rejilla adaptativa al ancho de ventana para favoritos en DashboardView
    test_dashboard_favorite_grid_adaptive_contracts()
    # TASK-051: Botón de actualización de DB en ProcessManagerView y reporte honesto
    test_process_manager_db_update_button_and_feedback()
    # TASK-052: Indicador único en desplegable de packs y placeholder centralizado
    test_process_manager_pack_dropdown_single_arrow_and_placeholder()
    print("\nALL TESTS PASSED.")
