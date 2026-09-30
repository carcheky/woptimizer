import os
import psutil
import struct
import time
from typing import List, Tuple, Optional, Dict, Sequence
from woptimizer.models import ProcessInfo
from woptimizer.config import PROCESS_CATEGORIES, CATEGORY_ORDER, logger

# TASK-026 (FIX-005): el centinela de "sin clasificar" es UN literal y se escribe
# con escape para que nadie lo reescriba a ojo. Debe ser EXACTAMENTE el ultimo
# elemento de CATEGORY_ORDER (config.py) y el default de ProcessInfo.category
# (models.py). Antes era "? Otros" (ASCII U+003F) aqui y en el `props.get` de
# _load_local_db: la interrogacion no es el circulo U+26AA, asi que ese proceso
# caia fuera de CATEGORY_ORDER y se ordenaba con el centinela 999 del sort.
# Se usa el escape \u26aa y no el glifo literal a proposito: pegar el emoji a mano
# es justo como se introdujo el defecto (familia de bug del ciclo #9).
_DEFAULT_META = ("\u26aa Otros", "none", "Sin descripción")

# TASK-024 - BLINDAJE ANTI-BRICK.
# Familia A del escaneo medido (openspec/changes/2026-09-29-real-bloatware-scan):
# procesos de nivel sistema cuyo cierre deja Windows inservible (pantalla negra,
# BSOD o perdida de sesion). Matar uno de ellos desde una app de "optimizacion"
# es el peor defecto posible en este producto, asi que no se confiar en que
# nadie los meta por error en `assets/process_db.json`: el blindaje se aplica
# ANTES de construir la lista de matables y por las tres vias (carga de la DB,
# resolucion de metadatos y kill). Coincidencia EXACTA sobre el nombre limpio
# en minusculas y sin extension, porque el matching de este servicio tambien
# acepta subcadenas y un nombre generico bloquearia procesos legitimos.
#
# No confundir con `PROCESS_CATEGORIES['\U0001F534 Sistema de Windows']['patterns']`:
# esa lista es de clasificacion legacy e incluye procesos del usuario (taskmgr,
# cmd, powershell, wsl). Aqui solo van los nombres cuyo cierre ROMPE el SO.
SYSTEM_PROTECTED_PROCESSES = frozenset({
    # Nucleo irrompible
    "csrss", "lsass", "winlogon", "smss", "services", "wininit",
    "registry", "memcompression", "system", "system idle process",
    # Sesion de usuario y escritorio
    "dwm", "sihost", "conhost", "openconsole", "dllhost", "ctfmon",
    "fontdrvhost", "spoolsv", "lsaiso", "ngciso",
    "shellexperiencehost", "startmenuexperiencehost",
    "searchhost", "searchindexer", "runtimebroker", "taskhostw",
    "textinputhost", "systemsettings",
    # Audio y dispositivos
    "audiodg",
    # Seguridad y drivers en modo usuario
    "wudfsvc", "wudfhost",
    "securityhealthsystray", "securityhealthservice", "securityhealthui",
})

# Meta forzado: el nombre se muestra pero jamas se ofrece como cerrable.
_PROTECTED_META = (
    "\U0001F534 Sistema de Windows",
    "none",
    "Proceso critico de Windows: cerrarlo deja el sistema inservible. "
    "No se puede cerrar nunca.",
)

# ---------------------------------------------------------------------------
# TASK-027 (FIX-003) - ARRANQUE DE APPS: HYGIENE CON CRITERIO
# ---------------------------------------------------------------------------
# `start_pack_apps` usaba `subprocess.Popen(app, shell=True)`. La entrada es
# `Pack.apps`, de `profiles.json`: un fichero que edita el usuario a mano y que
# este producto esta pensado para compartir, asi que el pack es entrada NO
# CONFIABLE y `shell=True` es un vector de ejecucion de comandos.
#
# Quitar `shell=True` NO basta, y esto es lo que se midio antes de escribir una
# linea de este bloque:
#   1. Con `shell=False`, CreateProcess busca el CWD ANTES que el PATH: un
#      `chrome.exe` soltado junto a `woptimizer.exe` se ejecutaria en lugar del
#      Chrome real. Por eso un nombre pelado NUNCA se resuelve con `which()`:
#      buscar en el PATH es buscar en el CWD.
#   2. `os.startfile` delega en ShellExecute, que SI ejecuta `.bat`/`.cmd`/
#      `.ps1`/`.vbs` por su interprete (`cmd.exe /c`). Cambiar `Popen` por
#      `startfile` sin lista blanca de extensiones seria cambiar de hugging por
#      ahorcamiento.
#   3. `os.path.isabs` NO es una validacion de seguridad: da `True` para
#      `C:\Program Files\..\..\Windows\System32\cmd.exe` (traversal) y para
#      `\\servidor\comparte\p.exe` (UNC). Y `commonpath` sobre la ruta CRUDA
#      tambien pasa el filtro de contencion (medido: `commonpath([cruda,
#      'C:\Program Files']) == 'C:\Program Files'`), de modo que la contencion
#      se comprueba SIEMPRE despues de `normpath`.
#
# NO se blacklistean caracteres (`& | ; > < ^`): `C:\Program Files\Rock & Roll\
# game.exe` es una ruta legitima y un filtro de metacarácteres rechaza apps
# reales de Steam y de itch.io. Sin interprete no hay metacarácteres que escapar:
# la validacion es estructural, nunca de caracteres.
#
# HONESTIDAD SOBRE EL MODELO DE AMENAZA: esta lista de raices NO es un sandbox.
# `%APPDATA%` y `%LOCALAPPDATA%` son escribibles por el usuario, asi que un
# atacante local con escritura en disco pasa por aqui. Lo que SI cierra esta
# lista es: nada se ejecuta a traves de un interprete, nada se ejecuta desde una
# comparticion remota (UNC), nada se ejecuta por traversal (contencion
# post-normalizacion) y no se puede colar un argumento (no se pasa ninguno).
# Prometer mas seria falso.
#
# Y una ampliacion que hace falta porque la contencion LEXICA no la daba
# (medido, ver el docstring de `_ruta_real`): la comparacion se hace dos veces,
# sobre la ruta escrita y sobre la ruta REAL. Sin la segunda, un junction de
# un comando metia `C:\Windows\System32\cmd.exe` dentro de `%LOCALAPPDATA%`.
# Y lo que sigue SIN cerrar, corregido con medicion en TASK-027 iteracion 3. La
# version anterior de este bloque decia que un hard link "no es un reparse point
# y ningun filtro de Windows lo ve": la primera mitad es verdad y la segunda es
# FALSA (medido: `os.stat(ruta).st_nlink` vale 2 en un hard link, o sea que si
# lo ve). Y aunque lo viera, no servia: el hard link NO es un caso especial.
#
# MEDIDO, con las dos variantes construidas de verdad en esta maquina:
#   alias hard link -> payload.bat   (st_nlink=2, sin privilegios)
#   alias COPIA PLENA -> payload.bat (st_nlink=1, sin NINGUN enlace)
# `_resolver_app` las ACEPTA LAS DOS, y no por un fallo del filtro de enlaces
# sino porque el filtro de enlaces no es el que decide: el unico dato que mira
# es el NOMBRE. Un rechazo por `st_nlink > 1` habria cerrado el caso exotico y
# habria dejado abierto el trivial, o sea seguridad de teatro. Ademas habria
# roto software de verdad: en las seis raices, de 2273 `.exe`/`.com` instalados,
# **189 (8,32 %) tienen `st_nlink > 1`**, con valores hasta 6, y son programas
# de Microsoft (`msinfo32.exe`, `TabTip.exe`, los auxiliares de Edge, las
# herramientas de Hyper-V). Rechazar "cualquier `st_nlink > 1`" es un
# falso positivo del 8 %.
#
# Lo que SI cierra las dos variantes, y las de cualquier otro tipo, es la regla
# 9 (`_es_imagen_pe`): la lista blanca de extensiones prometia "nada entra por un
# interprete", pero se cumplia mirando el NOMBRE. Lo que el SO exige para
# arrancar es que el fichero sea una imagen PE de verdad, y eso se comprueba en
# el contenido. Medido en esta maquina: 2200 de 2273 `.exe`/`.com` instalados
# llevan `MZ` + firma `PE\0\0` en el offset que dice `e_lfanew`, y **ninguno** de
# los 189 multi-enlazados legitimos falla (0 falsos negativos). Lo unico sin
# cabecera es appx de WindowsApps, la cache de MSI de `%APPDATA%\Microsoft\
# Installer` y un `.COM` DOS de 16 bits: ficheros que no son apps lanzables.
#
# NOTA SOBRE LO QUE ESTO NO ES: esto no es un sandbox. `%APPDATA%` y
# `%LOCALAPPDATA%` son escribibles por el usuario, asi que un atacante local con
# escritura en disco pasa por aqui (y por aqui pasaria con un `.exe` de verdad,
# no con un `.bat` renombrado). Lo que cierra es lo de siempre: nada por
# interprete, nada por UNC, nada por traversal, nada por junction, y ahora nada
# por "fichero que no es un programa". Prometer mas seria falso.
_ALLOWED_APP_EXTS = frozenset({".exe", ".com"})

# Firma minima de una imagen PE. `MZ` es el DOS header y `PE\0\0` la firma que el
# campo `e_lfanew` (offset 0x3C) declara. Se comprueran LOS DOS porque un fichero
# puede llevar `MZ` y no ser una imagen valida: medido, en las raices hay 0
# ficheros con `MZ` sin `PE\0\0`, asi que la segunda comprobacion no cuesta
# ningun programa legitimo y quita un caso mas de alias.
_PE_DOS_MAGIC = b"MZ"
_PE_SIGNATURE = b"PE\x00\x00"
_PE_E_LFANEW_OFFSET = 0x3C

# Raices permitidas por defecto. Las que no existan en el entorno se descartan;
# si no queda ninguna, no se arranca nada (fail-closed).
_LAUNCH_ROOT_VARS = (
    "ProgramFiles",
    "ProgramFiles(x86)",
    "ProgramW6432",
    "LOCALAPPDATA",
    "APPDATA",
    "ProgramData",
)


def _dentro_de_alguna(una: str, raices: Sequence[str]) -> bool:
    """`una` (YA normalizada) esta dentro de al menos una raiz normalizada.

    `commonpath` levanta ValueError cuando las rutas no comparten raiz (unidades
    distintas, o una UNC frente a una local). Eso no es una excepcion de
    programacion: es la respuesta correcta, "no hay contencion posible", y por
    eso se traduce a `False` en vez de subir por el arranque de una app.

    POR QUE `normcase` EN LOS DOS LADOS (TASK-027 iter 2, hallazgo 4): medido,
    `commonpath(['C:\\PROGRAM FILES\\x.exe', 'C:\\Program Files'])` devuelve
    `'C:\\PROGRAM FILES'`, que es distinto de la raiz, asi que un programa
    legítimamente instalado con otra caja se rechazaba. En Windows el
    sistema de ficheros NO distingue mayusculas, de modo que eso era un falso
    positivo (fail-closed, seguro, pero un bug funcional). `normcase` es la
    funcion que declara esa verdad del SO, no una concession: lo que acepta es
    exactamente el conjunto de rutas que el SO abriria. NO sustituye a
    `commonpath`: un `startswith` abriria la puerta al hermano de prefijo
    (`...\\Temp\\wopt_x` acepta `...\\Temp\\wopt_xEvil\\a.exe`), y esa
    contencion la vigila `test_la_contencion_no_acepta_un_hermano_de_prefijo`.
    """
    for raiz in raices:
        try:
            comun = os.path.commonpath([una, raiz])
        except ValueError:
            continue
        if os.path.normcase(comun) == os.path.normcase(raiz):
            return True
    return False


def _ruta_real(ruta: str) -> Optional[str]:
    """Resuelve la ruta REAL en el sistema de ficheros, o `None` si no puede.

    ESTA ES LA REGLA QUE FALTABA (TASK-027 iter 2, hallazgo 1). `normpath` y
    `commonpath` son LEXICOS: no atraviesan un enlace de directorio. Medido en
    esta maquina, antes de escribir una linea de este bloque:

        junction `<TEMP>\\jdir` -> `C:\\Windows\\System32` (creado con `mklink /J`)
        ruta                   `<TEMP>\\jdir\\cmd.exe`
        normpath               `<TEMP>\\jdir\\cmd.exe`      (intacta)
        commonpath([ruta, LOCALAPPDATA])  `C:\\...\\AppData\\Local`  (contiene: falso)
        os.path.isfile(ruta)   True
        os.stat(ruta).st_file_attributes   0x20  (ni reparse: isfile sigue el enlace)
        os.path.realpath(ruta) `C:\\Windows\\System32\\cmd.exe`  <-- la verdad

    Asi que un junction de un solo comando metia `C:\\Windows\\System32\\cmd.exe`
    dentro de las raices permitidas y lo arrancaba. Y la variante
    `st_file_attributes & FILE_ATTRIBUTE_REPARSE_POINT` sobre el FICHERO tampoco
    lo ve (0x20, medido arriba): `os.stat`/`os.lstat` siguen el enlace en el
    camino intermedio. Solo la ruta final por descriptor lo resuelve, y en
    Windows eso es exactamente lo que hace `os.path.realpath` (por debajo
    llama a `GetFinalPathNameByHandleW`; medido tambien con un enlace de
    FICHERO, que devuelve el target). No hace falta `ctypes` aqui: mismo
    resultado, menos codigo que mantener.

    FAIL-CLOSED: `strict=True` levanta si el SO no puede resolver la ruta, y
    aqui eso se traduce a `None` = "no se arranca". Sin resolver no se ejecuta.

    LO QUE ESTA FUNCION NO PUEDE VER, y por que: un HARD LINK (`mklink /H`) no
    es un reparse point, asi que `realpath` devuelve la ruta MISMA (medido:
    `realpath(alias) == alias`) y el atributo tampoco lo delata. Eso NO es
    "no lo ve nadie": `os.stat(ruta).st_nlink` lo ve (vale 2, medido). Lo que
    pasa es que `st_nlink` no sirve para decidir, y por eso el hard link se
    cierra en `_es_imagen_pe` y no aqui. El detalle, con la medicion que lo
    justifica, esta en el docstring de `_es_imagen_pe` y en la regla 9 de
    `_resolver_app`.
    """
    try:
        real = os.path.realpath(ruta, strict=True)
    except (OSError, ValueError):
        # ValueError: rutas con NUL incrustado en algunas versiones.
        return None
    if not real:
        return None
    return os.path.normpath(real)


def _es_imagen_pe(ruta: str) -> bool:
    """True si `ruta` es una imagen PE de verdad, no un script con extension .exe.

    ESTA ES LA REGLA QUE CIERRA EL HARD LINK (TASK-027 iter 3). El hallazgo era
    que un hard link secundario (`alias.exe` -> `payload.bat` FUERA de las
    raices) se aceptaba y se saltaba las dos barreras. La version anterior de
    esta funcion decia que un hard link "no lo ve ningun filtro de Windows" y que
    por eso no hacia falta cerrar nada. LAS DOS PARTES ESTAN MAL, y la segunda es
    la que importa:

      * Si lo ve: `os.stat(ruta).st_nlink` vale 2 en un hard link (medido).
      * Y da igual: el hard link NO es lo que hay que mirar. Medido en esta
        maquina con las DOS variantes construidas de verdad, `_resolver_app`
        acepta el hard link Y una COPIA PLENA del mismo `.bat` a `.exe`
        (`st_nlink == 1`, sin un solo enlace, sin junction, sin privilegios).
        Las dos se saltan las barreras porque las barreras miran el NOMBRE del
        fichero, y un hard link tiene el nombre que lepongas. Un rechazo por
        `st_nlink > 1` habria cerrado el caso raro y habria dejado abierto el
        facil.

    Que el fichero sea "una imagen PE" es, en cambio, la propiedad que de verdad
    distingue un programa de un script, y es la que la lista blanca de
    extensiones siempre quiso EXPRESAR sin decirlo: `.exe` no significa "algo
    que se arranca", significa "imagen PE". Un `.bat` renombrado a `.exe` sigue
    sin ser un PE por mucho que se llame asi, y eso no depende de COMO se
    enlazara el fichero.

    MEDIDO antes de escribirla, para no rechazar programas de verdad: de 2273
    `.exe`/`.com` instalados en las seis raices, 2200 llevan `MZ` y la firma
    `PE\\0\\0`, y **ninguno de los 189 con `st_nlink > 1` falla** (0 falsos
    negativos en justamente el caso que se queria cerrar). Los 19 sin cabecera
    son appx de WindowsApps, la cache de MSI de `%APPDATA%\\Microsoft\\Installer`
    y un `.COM` DOS de 16 bits: ninguno es una app lanzable.

    FAIL-CLOSED: si el fichero no se puede abrir, no es una imagen PE. Sin
    lectura no hay prueba, y sin prueba no se arranca.
    """
    try:
        with open(ruta, "rb") as fh:
            if fh.read(2) != _PE_DOS_MAGIC:
                return False
            fh.seek(_PE_E_LFANEW_OFFSET)
            bruto = fh.read(4)
            if len(bruto) != 4:
                return False
            (offset,) = struct.unpack("<I", bruto)
            if offset <= 0 or offset > 0x10000000:
                # Absurdo: un PE de mas de 256 MiB de cabecera no existe, y sin
                # este tope un `e_lfanew` manipulado haria que se leyera el
                # fichero entero buscando la firma.
                return False
            fh.seek(offset)
            return fh.read(4) == _PE_SIGNATURE
    except OSError:
        # Un fichero que no se puede abrir no es una imagen PE demostrable, y
        # fail-closed significa no arrancar.
        return False


def _normalizar_nombre(name: str) -> str:
    """Clave de comparacion: minusculas, sin extension y sin espacios sobrantes."""
    return (name or "").lower().replace('.exe', '').strip()


class ProcessService:
    """Servicio de procesos con hashmap O(1) y cache TTL.

    Optimizaciones (TASK-018):
    - _db_map: dict hashmap en lugar de lista lineal para lookups O(1).
    - _meta_cache: memoize de fuzzy matches para evitar re-escaneos de la DB.
    - _proc_cache + TTL: cache temporal de get_running_processes (2s por defecto).
    """

    def __init__(self):
        # Hashmap O(1): pattern -> (category, priority, description)
        self._db_map: Dict[str, Tuple[str, str, str]] = {}
        # Memoize fuzzy matches: cleaned_name -> (category, priority, description)
        self._meta_cache: Dict[str, Tuple[str, str, str]] = {}
        self.is_db_loaded = False
        # Cache de procesos con TTL
        self._proc_cache: Optional[List[ProcessInfo]] = None
        self._proc_cache_ts: float = 0.0
        self._CACHE_TTL: float = 2.0  # segundos
        self._load_local_db()

    @property
    def process_db(self) -> list:
        """Compatibilidad: devuelve una lista de ProcessInfo desde el hashmap.
        Solo se usa si algún código externo accede a process_db directamente."""
        return [
            ProcessInfo(name=k, full_name=k, pid=0,
                        category=v[0], priority=v[1], description=v[2])
            for k, v in self._db_map.items()
        ]

    @staticmethod
    def is_system_protected(name: str) -> bool:
        """TASK-024: True si el nombre es de nivel sistema y jamas cerrable.

        Acepta el nombre con o sin extension y en cualquier caja.
        """
        return _normalizar_nombre(name) in SYSTEM_PROTECTED_PROCESSES

    def _load_local_db(self):
        """Carga la base de datos local como hashmap {pattern: (cat, prio, desc)}."""
        import json, os
        try:
            from woptimizer.config import _data_dir
            local_path = os.path.join(_data_dir(), "assets", "process_db.json")
            if os.path.exists(local_path):
                with open(local_path, "r", encoding="utf-8") as f:
                    db_dict = json.load(f)
                    db_map: Dict[str, Tuple[str, str, str]] = {}
                    for pattern, props in db_dict.items():
                        key = _normalizar_nombre(pattern)
                        # TASK-024: el blindaje se aplica AL CARGAR, antes de
                        # que la entrada exista en el mapa. Aunque el JSON
                        # registre un proceso de sistema como cerrable, aqui
                        # queda forzado a rojo / priority none.
                        if key in SYSTEM_PROTECTED_PROCESSES:
                            db_map[key] = _PROTECTED_META
                            continue
                        db_map[key] = (
                            props.get('category', _DEFAULT_META[0]),
                            props.get('priority', 'none'),
                            props.get('description', 'Sin descripción')
                        )
                    self._db_map = db_map
                    self._meta_cache.clear()
                    self.is_db_loaded = True
        except Exception as e:
            logger.warning(f"Error cargando DB local: {e}")

    def load_db_async(self, callback=None):
        def _download():
            import json, urllib.request, os
            url = "https://gitlab.com/carcheky/woptimizer/-/raw/main/assets/process_db.json"
            try:
                from woptimizer.config import _data_dir
                assets_dir = os.path.join(_data_dir(), "assets")
            except Exception:
                assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

            os.makedirs(assets_dir, exist_ok=True)
            local_path = os.path.join(assets_dir, "process_db.json")

            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = response.read().decode('utf-8')
                    with open(local_path, "w", encoding="utf-8") as f:
                        f.write(data)
            except Exception as e:
                logger.warning(f"Fallo descargando DB de GitLab: {e}")

            # Recargar en memoria
            self._load_local_db()

            if callback:
                try:
                    callback()
                except Exception as e:
                    logger.warning(f"Error ejecutando callback de load_db_async: {e}")

        import threading
        threading.Thread(target=_download, daemon=True).start()

    def _get_process_meta(self, name: str) -> Tuple[str, str, str]:
        """Lookup O(1) con fallback a fuzzy match cacheado."""
        name_clean = _normalizar_nombre(name)

        # TASK-024: el blindaje se comprueba PRIMERO, antes que la DB y antes que
        # el matching por subcadenas. Un nombre de sistema nunca puede heredar la
        # categoria de otro patron ni quedar en la categoria centinela
        # ("\u26aa Otros") como cerrable.
        if name_clean in SYSTEM_PROTECTED_PROCESSES:
            return _PROTECTED_META

        # Check memoize cache first
        cached = self._meta_cache.get(name_clean)
        if cached is not None:
            return cached

        # O(1) exact match
        hit = self._db_map.get(name_clean)
        if hit:
            self._meta_cache[name_clean] = hit
            return hit

        # Fuzzy: check if any DB pattern is substring of name or vice versa
        for pattern, meta in self._db_map.items():
            if pattern in name_clean or name_clean in pattern:
                self._meta_cache[name_clean] = meta
                return meta

        self._meta_cache[name_clean] = _DEFAULT_META
        return _DEFAULT_META

    def _get_priority(self, category: str) -> str:
        for meta in self._db_map.values():
            if meta[0] == category:
                return meta[1]
        return 'none'

    def _categorize(self, name: str) -> str:
        cat, _, _ = self._get_process_meta(name)
        return cat

    def invalidate_cache(self) -> None:
        """Fuerza el re-escaneo en la próxima llamada a get_running_processes."""
        self._proc_cache = None
        self._proc_cache_ts = 0.0

    def get_running_processes(self, force_refresh: bool = False) -> List[ProcessInfo]:
        """Lista todos los procesos activos usando psutil, ordenados por categoría.

        Incorpora un cache con TTL para evitar re-escaneos costosos
        cuando la UI pide el listado repetidamente en intervalos cortos.
        El TTL por defecto es 2 segundos (configurable vía self._CACHE_TTL).
        Pasar force_refresh=True ignora el cache.
        """
        now = time.monotonic()
        if (not force_refresh
                and self._proc_cache is not None
                and (now - self._proc_cache_ts) < self._CACHE_TTL):
            return self._proc_cache

        result = []
        seen = set()

        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                info = proc.info
                name = info['name']
                if not name:
                    continue

                name_lower = name.lower()
                if name_lower in ('idle', 'system'):
                    continue

                pid = info['pid']
                if (name_lower, pid) in seen:
                    continue
                seen.add((name_lower, pid))

                clean_name = name.replace('.exe', '')
                cat, priority, desc = self._get_process_meta(clean_name)

                result.append(ProcessInfo(
                    name=clean_name,
                    full_name=name,
                    pid=pid,
                    exe_path=info['exe'] or "",
                    category=cat,
                    priority=priority,
                    description=desc
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # Ordenar por el orden definido en CATEGORY_ORDER, luego alfabético, luego PID
        cat_idx = {c: i for i, c in enumerate(CATEGORY_ORDER)}
        result.sort(key=lambda p: (cat_idx.get(p.category, 999), p.name.lower(), p.pid))

        # Guardar en cache
        self._proc_cache = result
        self._proc_cache_ts = time.monotonic()

        return result

    def kill_processes(self, processes: List[ProcessInfo]) -> Tuple[int, int, int, float]:
        """
        Mata una lista de procesos (y sus hijos).
        Retorna (killed, failed, skipped, freed_mb).
        """
        killed = 0
        failed = 0
        skipped = 0
        freed_bytes = 0

        for pinfo in processes:
            try:
                # TASK-024: ultima linea de defensa. La UI solo ofrece lo que ve
                # en la lista, pero un pack guardado a mano podria traer un PID de
                # sistema: aqui se cuenta como omitido y no se toca el proceso.
                if self.is_system_protected(pinfo.name) or self.is_system_protected(pinfo.full_name):
                    skipped += 1
                    continue

                parent = psutil.Process(pinfo.pid)

                # Capturar memoria del padre ANTES de matar
                try:
                    parent_rss = parent.memory_info().rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    parent_rss = 0

                # Obtener hijos y capturar memoria física ANTES de matar
                children_data = []
                try:
                    for child in parent.children(recursive=True):
                        try:
                            c_rss = child.memory_info().rss
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            c_rss = 0
                        children_data.append((child, c_rss))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    children_data = []

                # Matar hijos recursivamente primero (evita procesos huérfanos)
                for child, c_rss in children_data:
                    try:
                        child.kill()
                        freed_bytes += c_rss
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                # Matar el padre
                parent.kill()
                freed_bytes += parent_rss
                killed += 1

            except psutil.NoSuchProcess:
                # El proceso ya no existe, objetivo cumplido indirectamente
                skipped += 1
            except psutil.AccessDenied:
                logger.warning(f"Access denied killing {pinfo.name}")
                failed += 1

        # Invalidar cache tras matar procesos
        self.invalidate_cache()

        freed_mb = round(freed_bytes / (1024 * 1024), 2)
        return killed, failed, skipped, freed_mb

    def kill_pack_apps(self, apps: List[str]) -> Tuple[int, int, int, float]:
        """Mata todos los procesos cuyos nombres o rutas coincidan con la lista apps."""
        import os

        if not apps:
            return 0, 0, 0, 0.0

        killed, failed, skipped = 0, 0, 0
        freed_bytes = 0
        apps_lower = [a.lower() for a in apps]

        for proc in psutil.process_iter(['name', 'exe']):
            try:
                info = proc.info
                name = (info.get('name') or '').lower()
                exe = (info.get('exe') or '').lower()

                if name in apps_lower or exe in apps_lower:
                    # TASK-024: blindaje tambien en la via de packs. El pack lo
                    # escribe el usuario a mano, asi que no basta con lo que
                    # muestra la lista de la UI: aqui se cuenta como omitido y
                    # no se toca el proceso.
                    if (self.is_system_protected(name)
                            or self.is_system_protected(os.path.basename(exe))):
                        skipped += 1
                        continue

                    # Capturar memoria del padre ANTES de matar
                    try:
                        proc_rss = proc.memory_info().rss
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        proc_rss = 0

                    # Capturar hijos y su memoria ANTES de matar
                    children_data = []
                    try:
                        for child in proc.children(recursive=True):
                            try:
                                c_rss = child.memory_info().rss
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                c_rss = 0
                            children_data.append((child, c_rss))
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        children_data = []

                    # Matar hijos recursivamente primero
                    for child, c_rss in children_data:
                        try:
                            child.kill()
                            freed_bytes += c_rss
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                    # Matar el padre
                    proc.kill()
                    freed_bytes += proc_rss
                    killed += 1
            except psutil.AccessDenied:
                failed += 1
            except (psutil.NoSuchProcess, psutil.ZombieProcess):
                skipped += 1

        # Invalidar cache tras matar procesos
        self.invalidate_cache()

        freed_mb = round(freed_bytes / (1024 * 1024), 2)
        return killed, failed, skipped, freed_mb

    def _launch_roots(self) -> List[str]:
        """Raices permitidas por defecto; las que no existan se descartan."""
        roots = []
        for var in _LAUNCH_ROOT_VARS:
            valor = os.environ.get(var)
            if not valor:
                continue
            norm = os.path.normpath(valor)
            if os.path.isdir(norm):
                roots.append(norm)
        return roots

    def _resolver_app(self, entrada: str,
                      raices: Optional[Sequence[str]] = None) -> Optional[str]:
        """Devuelve la ruta ABSOLUTA validada, o None si no se puede arrancar.

        `raices` tiene valor por defecto para que el test pueda pasar un
        directorio temporal controlado. Nunca se consulta el PATH ni el CWD.

        El orden de las reglas ES la seguridad, asi que no se reordena:
          1. entrada no vacia tras `strip()`, sin `\\x00`.
          2. rechazo UNC (`\\\\host\\share` es ejecucion remota por SMB, el
             vector mas valioso de los tres y el que nadie audita).
          3. si no es absoluta, el nombre pelado se busca SOLO dentro de las
             raices permitidas (`os.path.join(raiz, entrada)` + `isfile`): asi
             sobrevive el `apps=["chrome.exe"]` de fabrica sin tocar el PATH.
             Si es absoluta, la unica candidata es ella misma.
          4. `normpath` ANTES de cualquier comparacion (si no, el traversal pasa
             las dos comprobaciones, medido).
          5. contencion LEXICA: dentro de al menos una raiz (raiz tambien
             normalizada).
          6. extension LEXICA en `_ALLOWED_APP_EXTS` (minusculas, con punto).
          7. `os.path.isfile`.
          8. RESOLUCION REAL (`_ruta_real`, fail-closed) y las MISMAS dos
             reglas sobre la ruta real: contencion real y extension real.
             Sin esto, `normpath` y `commonpath` son LEXICOS y un junction
             cuela lo que sea (medido en el docstring de `_ruta_real`): un
             enlace a `C:\\Windows\\System32\\cmd.exe` colgado de
             `%LOCALAPPDATA%` salia "contenido" y arrancaba. Y un enlace
             `.exe` a un `.bat` de una raiz permitida esquivaba la lista
             blanca de extensiones, porque la extension se miraba en el ALIAS
             y no en el destino (medido: `realpath` devuelve `...\\evil.bat`).
          9. CONTENIDO: la ruta real tiene que ser una imagen PE de verdad
             (`_es_imagen_pe`, fail-closed). Las reglas 5-8 miran el NOMBRE, y
             el nombre no es el contenido: un `.bat` renombrado a `.exe` pasa
             las cuatro. La regla 9 es la que cierra el HARD LINK (TASK-027
             iter 3) y, con el, la COPIA PLENA del mismo `.bat`, que se
             colaba igual y sin un solo enlace. Va DESPUES de la resolucion
             real a proposito: se comprueba el fichero que se va a arrancar de
             verdad, no el que se escribio.
         10. se devuelve la ruta REAL, no la lexica: lo que se valida es
             exactamente lo que se arranca, y en el log sale la verdad.

        Las raices se resuelven por el MISMO camino que las candidatas. Con la
        raiz LEXICA, un junction en algun tramo de `%LOCALAPPDATA%` haria que
        la comparacion real fallara y rechazaria apps legitimas: el otro modo
        de fallar (falso negativo) y no una garantia.

        Cada rechazo deja un `warning` con el MOTIVO: el usuario edita su
        `profiles.json` a mano y sin log no puede depurar por que su app no
        arranco. El mutador obligatorio ("todo pasa") que hace morir el test de
        arranque es este `logger.warning`, no un `import` que reviente.
        """
        if not isinstance(entrada, str):
            logger.warning("Arranque rechazado: la entrada no es texto.")
            return None

        raw = entrada.strip()
        if not raw or "\x00" in raw:
            logger.warning(f"Arranque rechazado: entrada vacia o con NUL ({entrada!r}).")
            return None

        if raw.startswith("\\\\") or raw.startswith("//"):
            logger.warning(f"Arranque rechazado (UNC / ruta remota, no se ejecuta "
                           f"desde una comparticion): {raw}")
            return None

        if raices is None:
            raices = self._launch_roots()
        raices_norm = [os.path.normpath(r) for r in raices if r]
        if not raices_norm:
            # Fail-closed: sin raices no se arranca nada.
            logger.warning("Arranque rechazado: no hay ninguna raiz permitida en "
                           "este entorno, no se arranca nada.")
            return None

        # Una raiz que el SO no puede abrir no puede tener nada debajo que si
        # se pueda abrir, asi que se descarta en vez de compararse a ciegas.
        raices_reales = [r for r in (_ruta_real(raiz) for raiz in raices_norm) if r]
        if not raices_reales:
            logger.warning("Arranque rechazado: ninguna raiz permitida se resuelve "
                           "en el sistema de ficheros, no se arranca nada.")
            return None

        candidatas = ([raw] if os.path.isabs(raw)
                      else [os.path.join(r, raw) for r in raices_norm])

        # Un solo `warning` por rechazo, con el motivo MAS ESPECIFICO que se
        # haya podido determinar (si la candidata paso la contencion y fallo
        # por la extension, el log dice eso y no "no existe").
        motivo = "no existe, o esta fuera de las raices permitidas"
        for cand in candidatas:
            normalizada = os.path.normpath(cand)
            if not _dentro_de_alguna(normalizada, raices_norm):
                continue
            if os.path.splitext(normalizada)[1].lower() not in _ALLOWED_APP_EXTS:
                motivo = (f"extension fuera de la lista blanca .exe/.com, no se "
                          f"pasa por un interprete: {normalizada}")
                continue
            if not os.path.isfile(normalizada):
                continue
            real = _ruta_real(normalizada)
            if real is None:
                # Fail-closed: sin ruta real resuelta no se arranca.
                motivo = (f"el sistema de ficheros no resuelve la ruta real, "
                          f"fail-closed: {normalizada}")
                continue
            if not _dentro_de_alguna(real, raices_reales):
                motivo = (f"la ruta real apunta fuera de las raices permitidas "
                          f"(junction/symlink): {normalizada} -> {real}")
                continue
            ext_real = os.path.splitext(real)[1].lower()
            if ext_real not in _ALLOWED_APP_EXTS:
                motivo = (f"la ruta real acaba en {ext_real or '(sin extension)'} y "
                          f"no en la lista blanca .exe/.com: {normalizada} -> {real}")
                continue
            if not _es_imagen_pe(real):
                motivo = (f"el fichero no es una imagen PE (no lleva MZ/PE), o sea "
                          f"no es un programa sino un script renombrado: "
                          f"{normalizada} -> {real}")
                continue
            return real

        logger.warning(f"Arranque rechazado ({motivo}): {raw}")
        return None

    def _lanzar(self, ruta: str) -> None:
        """Lanza UNA ruta ya validada, sin interprete y sin argumentos.

        `os.startfile` se resuelve como ATRIBUTO DEL MODULO en tiempo de llamada,
        nunca `from os import startfile`: asi la sonda puede sustituirlo por un
        grabador y morir por la ASERCION, en vez de por un `AttributeError` que
        solo demostraria que el monkeypatch no agarro.
        """
        startfile = getattr(os, "startfile", None)
        if startfile is None:
            # Fuera de Windows no hay ShellExecute: fail-closed, no hay fallback.
            raise OSError("os.startfile no disponible en esta plataforma")
        startfile(ruta)

    def start_pack_apps(self, apps: List[str]) -> Tuple[int, int]:
        """Arranca las apps del pack y devuelve (started, failed) HONESTOS.

        El contador es un criterio de aceptacion, no un detalle: medido, con
        `shell=True` un nombre inexistente NO lanza excepcion (`cmd.exe` responde
        "no se reconoce como un comando" con codigo de salida 1), asi que el
        `except` de antes nunca se disparaba y `started` contaba apps que no
        arrancaron: el toast de exito miente en verde. Por eso `started += 1`
        va DESPUES del `try`, y un rechazo de validacion cuenta como `failed`.
        """
        started, failed = 0, 0
        for app in apps:
            ruta = self._resolver_app(app)
            if ruta is None:
                failed += 1
                logger.warning(f"App '{app}' no se arranco: la ruta no supera la "
                               f"validacion de arranque.")
                continue
            try:
                self._lanzar(ruta)
                started += 1
                logger.info(f"Launched app: {ruta}")
            except OSError as e:
                failed += 1
                logger.warning(f"Failed to launch app '{ruta}': {e}")
        return started, failed
