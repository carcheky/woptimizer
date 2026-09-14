"""
Process Manager para Windows
Permite cerrar procesos seleccionados, guardar la lista y relanzarlos despues.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import json
import os
import shlex
import threading
from datetime import datetime

# Version del producto (bumpear con cada feature/fix)
__version__ = "2.0.5"

# Constante para evitar ventanas de consola en subprocesos (Windows)
CREATE_NO_WINDOW = 0x08000000

# Archivo para guardar la lista de procesos cerrados
PROCESS_LIST_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_processes.json")
# Archivo para perfiles de relanzado (v2.0)
PROFILES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles.json")
# Delimitador unico raro para evitar colisiones con pipes en commandlines
PS_DELIM = "|||DAT|||"
# Maximo commandline que capturamos (evita JSON enorme)
MAX_CMDLINE_LEN = 4000

# Categorias para uso gamer.
# priority: 'high' (matar para gaming), 'medium' (opcional), 'low' (mantener), 'none' (no tocar)
PROCESS_CATEGORIES = {
    '🔴 Navegadores': {
        'priority': 'high',
        'patterns': ['chrome', 'firefox', 'msedge', 'brave', 'opera', 'vivaldi',
                     'iexplore', 'iexplorer', 'arc', 'chromium', 'browser', 'waterfox',
                     'palemoon', 'torbrowser'],
        'description': 'Navegadores web',
    },
    '🔴 Sincronización': {
        'priority': 'high',
        'patterns': ['onedrive', 'dropbox', 'googledrive', 'googledrivefs', 'megasync',
                     'icloud', 'iclouddrive', 'box', 'pcloud', 'nextcloud', 'resilio',
                     'syncthing', 'gdrive', 'sync', 'backup'],
        'description': 'Apps de sincronización en la nube',
    },
    '🟡 Chat y Comunicación': {
        'priority': 'low',
        'patterns': ['discord', 'slack', 'teams', 'telegram', 'skype', 'whatsapp',
                     'zoom', 'signal', 'threema', 'wire', 'element', 'viber',
                     'messenger', 'pidgin'],
        'description': 'Mensajería y comunicación (mantener en gaming - chat con amigos)',
    },
    '🟡 Productividad': {
        'priority': 'medium',
        'patterns': ['office', 'winword', 'excel', 'powerpoint', 'outlook', 'onenote',
                     'notion', 'obsidian', 'evernote', 'todoist', 'trello', 'adobe',
                     'photoshop', 'illustrator', 'premiere', 'afterfx', 'aftereffect',
                     'acrobat', 'reader', 'libreoffice', 'gimp', 'inkscape',
                     'figma', 'canva', 'asana', 'notepad', 'wordpad'],
        'description': 'Ofimática y productividad',
    },
    '🟡 Media': {
        'priority': 'medium',
        'patterns': ['spotify', 'itunes', 'applemusic', 'foobar2000', 'aimp',
                     'musicbee', 'vlc', 'mpv', 'groove', 'wmp', 'wmplayer',
                     'audacity', 'handbrake', 'obsidian'],
        'description': 'Música y video',
    },
    '🟢 Overlays / Streaming': {
        'priority': 'low',
        'patterns': ['obs64', 'obs32', 'obs ', 'streamlabs', 'xsplit', 'nvsphelper',
                     'nvcontainer', 'geforce', 'radeon', 'rtxss', 'rtx', 'rtss',
                     'afterburner', 'rivatuner', 'xboxgamebar', 'gamebar', 'xam',
                     'presentmon', 'frtc'],
        'description': 'Overlays y captura (mantener si los usas)',
    },
    '🟢 Launchers / Anti-cheat': {
        'priority': 'low',
        'patterns': ['steam', 'epicgameslauncher', 'origin', 'eadesktop', 'ealauncher',
                     'battle.net', 'battlenet', 'uplay', 'ubisoft', 'gog', 'riotclient',
                     'easyanticheat', 'eac_service', 'battleye'],
        'description': 'Launchers y anti-cheat (necesarios para jugar)',
    },
    '⚫ Antivirus / Seguridad': {
        'priority': 'none',
        'patterns': ['msmpeng', 'defender', 'antivirus', 'avast', 'avgui', 'avg',
                     'bitdefender', 'norton', 'kaspersky', 'malwarebytes', 'mbam',
                     'mcafee', 'eset', 'sentinel', 'carbon'],
        'description': 'Antivirus (NO TOCAR - puede banearte en juegos online)',
    },
    '⚫ Sistema': {
        'priority': 'none',
        'patterns': ['svchost', 'csrss', 'lsass', 'winlogon', 'dwm', 'explorer',
                     'services', 'smss', 'wininit', 'fontdrvhost', 'taskhost',
                     'taskhostw', 'sihost', 'conhost', 'audiodg', 'wdf', 'wudfrd'],
        'description': 'Sistema Windows (NO TOCAR)',
    },
}

# Categorias visibles en modo simple (gamer-friendly)
SIMPLE_MODE_CATEGORIES = ['🔴 Navegadores', '🔴 Sincronización', '🟡 Chat y Comunicación',
                          '🟡 Productividad', '🟡 Media']

# Orden en que aparecen las categorias en el treeview
CATEGORY_ORDER = [
    '🔴 Navegadores',
    '🔴 Sincronización',
    '🟡 Chat y Comunicación',
    '🟡 Productividad',
    '🟡 Media',
    '🟢 Overlays / Streaming',
    '🟢 Launchers / Anti-cheat',
    '⚫ Antivirus / Seguridad',
    '⚫ Sistema',
]

# Procesos que se MANTIENEN durante "Preparar para Gaming" (Trampa #15).
# Aunque pertenezcan a una categoria que normalmente se mata (ej: discord
# esta en "Chat y Comunicación"), durante gaming se preservan para no
# interrumpir la partida.
GAMING_KEEPERS = {
    'discord',  # chat de voz con amigos durante la partida
}


def should_kill_for_gaming(proc_name):
    """Decide si un proceso debe matarse durante `prepare_for_gaming`.

    Reglas (Trampa #15):
    1. Si el nombre matchea cualquier `GAMING_KEEPERS` → False (se mantiene).
    2. Si prioridad high o medium → True (se mata).
    3. Si prioridad low y categoria Chat → True (override gaming: molesta).
    4. Resto → False (launchers, overlays, antivirus, sistema: se mantienen).

    Devuelve True = matar, False = mantener.
    """
    name_lower = proc_name.lower()
    # Regla 1: keepers (discord) siempre se mantienen
    for keeper in GAMING_KEEPERS:
        if keeper in name_lower:
            return False
    # Regla 2-4: basada en prioridad + override de categoria
    cat = categorize_process(proc_name)
    priority = PROCESS_CATEGORIES.get(cat, {}).get('priority', 'none')
    if priority in ('high', 'medium'):
        return True
    if priority == 'low' and cat == '🟡 Chat y Comunicación':
        return True  # override: gaming mata chat (excepto keepers ya filtrados)
    return False


def _run_kill(name):
    """Mata TODAS las instancias de `name` y verifica el resultado.

    Args:
        name: nombre del proceso sin extension (ej: 'firefox', 'nextcloud').

    Returns:
        dict con keys:
          - 'killed': True si al menos una instancia fue matada.
          - 'already_gone': True si no habia instancias.
          - 'remaining': int con instancias que SIGUEN vivas tras el intento.
          - 'error': str con mensaje de error si fallo, o ''.
    """
    # Asegurar que el nombre tiene .exe para IM (mas robusto en Windows)
    image_name = name if name.lower().endswith('.exe') else name + '.exe'
    result = {
        'killed': False,
        'already_gone': False,
        'remaining': 0,
        'error': '',
    }
    try:
        tk = subprocess.run(
            ["taskkill", "/F", "/IM", image_name, "/T"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            creationflags=CREATE_NO_WINDOW
        )
        # Exit codes:
        #   0   = exito (al menos uno matado)
        #   128 = nada que matar (ya no estaba)
        #   1   = no se encontro / acceso denegado / otro error real
        if tk.returncode == 0:
            result['killed'] = True
        elif tk.returncode == 128:
            result['already_gone'] = True
        else:
            err = (tk.stderr.strip() or tk.stdout.strip() or f"exit {tk.returncode}")
            # Detectar permiso denegado en el mensaje para mensaje claro
            if 'denied' in err.lower() or 'access' in err.lower() or 'permiso' in err.lower():
                result['error'] = 'ACCESO DENEGADO (¿necesitas admin?)'
            else:
                result['error'] = err[:120]
    except Exception as e:
        result['error'] = str(e)[:120]
        return result

    # Verificar con tasklist si realmente desaparecio
    try:
        tl = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {image_name}"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            creationflags=CREATE_NO_WINDOW
        )
        # tasklist imprime lineas con PID + nombre; contar
        lines = [l for l in tl.stdout.splitlines()
                 if l.strip() and image_name.lower() in l.lower() and 'INFO:' not in l]
        result['remaining'] = len(lines)
        # Si dijimos killed pero quedan, es que fallo por permisos / algo no dejo
        if result['killed'] and result['remaining'] > 0:
            result['killed'] = False
            result['error'] = (
                f'TaskKill reporto exito pero {result["remaining"]} sigo(n) vivo(s) '
                f'(probable ACCESO DENEGADO — ejecuta como Admin)'
            )
    except Exception:
        pass

    return result


def categorize_process(proc_name):
    """Devuelve la categoria de un proceso segun su nombre (sin extension)."""
    name_lower = proc_name.lower()
    # Comprobar categorias en orden
    for category in CATEGORY_ORDER:
        info = PROCESS_CATEGORIES[category]
        for pattern in info['patterns']:
            if pattern in name_lower:
                return category
    return '⚪ Otros'


def is_admin():
    """Detecta si el script se esta ejecutando con permisos de administrador."""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def get_running_processes():
    """Obtiene la lista de procesos en ejecucion usando PowerShell."""
    try:
        # Usar TAB como separador (no aparece en commandlines normales)
        # Excluir los propios procesos de PowerShell (su cmdline contiene todo el script)
        # Forzar UTF-8 para tildes/ñ correctas
        ps_script = f'''
        $ProgressPreference = 'SilentlyContinue'
        $OutputEncoding = [System.Text.Encoding]::UTF8
        Get-CimInstance Win32_Process |
            Where-Object {{ $_.Name -notin @('powershell.exe', 'pwsh.exe') -and $_.CommandLine }} |
            ForEach-Object {{
                $name = $_.Name
                # NOTA: NO usar $pid - es variable reservada en PowerShell
                # que contiene el PID del propio proceso PS. Usar $procId.
                $procId = $_.ProcessId
                # Limpiar tab/newline del cmdline (defensa en profundidad)
                $cmd = $_.CommandLine -replace "[`t`r`n]", ' '
                if ($cmd.Length -gt {MAX_CMDLINE_LEN}) {{
                    $cmd = $cmd.Substring(0, {MAX_CMDLINE_LEN}) + "...[truncated]"
                }}
                # Separador TAB - no aparece en cmdlines
                Write-Output "$name`t$procId`t$cmd"
            }}
        '''

        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=30,
            creationflags=CREATE_NO_WINDOW
        )

        # Comprobar errores de PowerShell (WMI puede fallar silenciosamente)
        if result.returncode != 0:
            err = result.stderr.strip() or "PowerShell returned non-zero exit code"
            raise RuntimeError(f"PowerShell fallo (code {result.returncode}): {err[:300]}")

        processes = []
        lines = result.stdout.strip().split('\n')

        for line in lines:
            if line.strip():
                # TAB como separador
                parts = line.split('\t')
                if len(parts) >= 3:
                    name = parts[0].strip()
                    pid = parts[1].strip()
                    cmdline = parts[2].strip()

                    if name and pid:
                        # Limpiar nombre del proceso
                        name_clean = name.replace('.exe', '').strip()
                        processes.append({
                            'name': name_clean,
                            'full_name': name,
                            'pid': pid,
                            'commandline': cmdline
                        })

        # Sin deduplicar por nombre: cada PID es unico, y queremos
        # preservar todas las instancias (varias ventanas de chrome.exe etc.)
        # Ordenar alfabeticamente por nombre, luego por pid
        processes.sort(key=lambda x: (x['name'].lower(), x['pid']))
        return processes

    except Exception as e:
        messagebox.showerror("Error", f"No se pudieron obtener los procesos:\n{str(e)}")
        return []


def expand_selection_by_name(selected, all_procs):
    """Expande la seleccion a TODOS los procesos con el mismo nombre en el sistema.

    Si el usuario selecciona 1 firefox, devuelve TODOS los firefox del snapshot.
    Asi con 1 click + 1 matar mueren todos los firefox (no hay que ir uno a uno).
    La expansion es por 'name' (case-insensitive), NO por PID.

    Args:
        selected: lista de procs seleccionados por el usuario
        all_procs: lista completa de procesos del snapshot (self.processes)

    Returns:
        lista expandida con todos los procs cuyos nombres coincidan
    """
    if not selected:
        return []
    selected_names = {p.get('name', '').lower() for p in selected}
    expanded = [p for p in all_procs if p.get('name', '').lower() in selected_names]
    # Si no se encontro nada en all_procs (caso raro: snapshot vacio),
    # devolvemos al menos la seleccion original para no perder el intent del usuario
    return expanded if expanded else list(selected)


def kill_processes(processes_seleccionados, kill_tree=True, dedupe_by_tree=True):
    """Mata los procesos seleccionados y retorna la info para relanzarlos.

    Args:
        processes_seleccionados: lista de dicts con campos name, pid, commandline
        kill_tree: si True, mata tambien procesos hijos (/T). Si False, solo el PID exacto.
        dedupe_by_tree: si True y kill_tree=True, evita taskkill redundantes:
                        si tienes 5 chrome.exe seleccionados (main + renderers),
                        /T del primero ya mata a todos. Mantenemos solo el primero
                        de cada ejecutable unico (agrupado por args[0] del commandline).
                        NO se aplica con kill_tree=False (alli cada PID es explicito).

    Returns:
        (killed, failed, skipped) - skipped lista los nombres omitidos por dedup
    """
    killed = []
    failed = []
    skipped = []

    # Dedupe por ejecutable (args[0]) si kill_tree=True
    to_kill = processes_seleccionados
    if dedupe_by_tree and kill_tree:
        seen_exes = set()
        deduped = []
        for p in processes_seleccionados:
            cmd = p.get('commandline', '')
            try:
                args = shlex.split(cmd, posix=False)
            except ValueError:
                args = []
            # args[0] es el path del ejecutable (ej: C:\Program Files\Chrome\chrome.exe)
            exe_key = args[0].lower() if args else p.get('name', '').lower()
            if exe_key and exe_key not in seen_exes:
                seen_exes.add(exe_key)
                deduped.append(p)
            elif exe_key:
                skipped.append(p.get('name', '?'))
        to_kill = deduped

    for proc in to_kill:
        try:
            pid = int(proc['pid'])
            # /F fuerza el cierre (sin graceful shutdown)
            # /T mata tambien el arbol de procesos hijos (opcional)
            cmd = ["taskkill", "/F"]
            if kill_tree:
                cmd.append("/T")
            cmd.extend(["/PID", str(pid)])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=CREATE_NO_WINDOW
            )

            # Exit codes:
            #   0   = exito
            #   128 = proceso no encontrado (objetivo cumplido: ya no esta)
            #   1   = acceso denegado u otro error real
            if result.returncode in (0, 128):
                killed.append({
                    'name': proc['name'],
                    'pid': proc['pid'],
                    'commandline': proc['commandline'],
                    'killed_at': datetime.now().isoformat(),
                    'already_gone': result.returncode == 128
                })
            else:
                err = result.stderr.strip() if result.stderr else "permiso denegado o proceso protegido"
                failed.append(f"{proc['name']} (PID {proc['pid']}: {err})")

        except Exception as e:
            failed.append(f"{proc['name']} ({str(e)})")

    return killed, failed, skipped


def save_processes_to_relaunch(processes, session=None):
    """Guarda la lista de procesos para relanzarlos. Dedup por (name, pid).

    Si se pasa session=<tag>, las entradas nuevas se marcan con ese tag y
    las existentes con el MISMO tag se reemplazan (la sesion es un snapshot
    del ultimo estado, no una acumulacion).
    """
    existing = []
    if os.path.exists(PROCESS_LIST_FILE):
        try:
            with open(PROCESS_LIST_FILE, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except Exception:
            existing = []

    # Si estamos guardando una sesion, descartar entradas anteriores de la misma sesion
    if session is not None:
        existing = [ex for ex in existing if ex.get('session') != session]

    # Construir set de claves existentes para dedup O(1)
    existing_keys = {(ex.get('name', ''), str(ex.get('pid', ''))) for ex in existing}

    added = 0
    for p in processes:
        # Filtrar entradas sin commandline: no se pueden relanzar
        if not p.get('commandline'):
            continue

        key = (p.get('name', ''), str(p.get('pid', '')))
        if key not in existing_keys:
            # Etiquetar la entrada con la sesion (si aplica)
            if session is not None:
                p = {**p, 'session': session}
            existing.append(p)
            existing_keys.add(key)
            added += 1

    try:
        with open(PROCESS_LIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo guardar:\n{str(e)}")
        return False


def load_saved_processes():
    """Carga la lista de procesos guardados para relanzar."""
    if not os.path.exists(PROCESS_LIST_FILE):
        return []

    try:
        with open(PROCESS_LIST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def relaunch_processes(processes, group_by_exe=True):
    """Relanza los procesos guardados de forma segura.

    Args:
        processes: lista de dicts con campos name, pid, commandline
        group_by_exe: si True (default), agrupa por ejecutable unico (args[0]
                     del commandline) y lanza UNA instancia por grupo SIN
                     argumentos. Asi 5 chrome.exe guardados -> 1 chrome.exe
                     lanzado. Evita "23423423 firefox" y problemas con
                     renderers/hijos que no pueden lanzarse solos.
                     Si False, comportamiento legacy (lanza cada cmdline tal cual).

    Returns:
        (launched, failed, skipped_count) - skipped_count = cuantos duplicados
        se ignoraron por estar agrupados bajo otro exe.
    """
    launched = []
    failed = []
    skipped_count = 0

    # Agrupar por ejecutable (args[0]) y conservar el primero de cada grupo
    seen_exes = set()
    grouped = []
    for p in processes:
        cmd = p.get('commandline', '')
        if not cmd:
            failed.append(f"{p.get('name', '?')} - Sin commandline, no se puede relanzar")
            continue
        try:
            args = shlex.split(cmd, posix=False)
        except ValueError:
            args = []

        exe_path = args[0] if args else None
        if not exe_path:
            failed.append(f"{p.get('name', '?')} - Sin ejecutable en commandline")
            continue

        if group_by_exe:
            exe_key = exe_path.lower()
            if exe_key in seen_exes:
                skipped_count += 1
                continue
            seen_exes.add(exe_key)
        grouped.append((p, exe_path, cmd))

    for proc, exe_path, original_cmd in grouped:
        try:
            if group_by_exe:
                # Agrupado: lanzar SOLO el ejecutable, sin argumentos.
                # No restauramos tabs/URLs especificas: abrimos la app en blanco.
                # Si el usuario queria URLs concretas, que las abra manualmente.
                subprocess.Popen([exe_path],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL,
                                 creationflags=CREATE_NO_WINDOW)
            else:
                # Legacy: lanzar el commandline ORIGINAL con todos sus args.
                # Usar shlex para parsing seguro; fallback a shell si falla.
                try:
                    args_parsed = shlex.split(original_cmd, posix=False)
                except ValueError:
                    args_parsed = None
                if args_parsed:
                    subprocess.Popen(args_parsed,
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL,
                                     creationflags=CREATE_NO_WINDOW)
                else:
                    subprocess.Popen(original_cmd, shell=True,
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL,
                                     creationflags=CREATE_NO_WINDOW)
            launched.append(proc.get('name', '?'))
        except FileNotFoundError:
            failed.append(f"{proc.get('name', '?')} ({exe_path} no encontrado)")
        except Exception as e:
            failed.append(f"{proc.get('name', '?')} ({str(e)})")

    return launched, failed, skipped_count


def clear_saved_processes():
    """Limpia la lista de procesos guardados."""
    if os.path.exists(PROCESS_LIST_FILE):
        try:
            os.remove(PROCESS_LIST_FILE)
            return True
        except Exception:
            return False
    return True


# ============================================================
# PERFILES DE RELANZADO (v2.0)
# ============================================================
# Estructura en profiles.json:
# {
#   "profiles": {
#     "<nombre>": {"apps": ["chrome.exe", "discord.exe", ...]},
#     ...
#   },
#   "favorite": "<nombre del perfil favorito>"  # o null
# }
#
# Semantica:
# - Un perfil = lista de ejecutables (por nombre, no path absoluto)
# - "Lanzar perfil X" = arrancar cada app del perfil (una instancia por nombre, sin args)
# - "Marcar como favorito" = el perfil que se lanza desde el boton principal
# - Si el favorito no existe o esta vacio, el boton principal no hace nada

def load_profiles():
    """Carga los perfiles desde profiles.json. Devuelve dict con 'profiles' y 'favorite'."""
    if not os.path.exists(PROFILES_FILE):
        return {'profiles': {}, 'favorite': None}
    try:
        with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Normalizar estructura
        if 'profiles' not in data:
            data = {'profiles': data, 'favorite': None}
        return data
    except Exception:
        return {'profiles': {}, 'favorite': None}


def save_profiles(data):
    """Guarda los perfiles en profiles.json."""
    try:
        with open(PROFILES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        messagebox.showerror("Error", f"No se pudieron guardar los perfiles:\n{str(e)}")
        return False


def create_profile(name, apps):
    """Crea un perfil nuevo. Devuelve el dict actualizado o None si ya existe."""
    data = load_profiles()
    if name in data['profiles']:
        return None  # ya existe
    data['profiles'][name] = {'apps': list(apps)}
    if save_profiles(data):
        return data
    return None


def update_profile(name, apps):
    """Actualiza la lista de apps de un perfil existente."""
    data = load_profiles()
    if name not in data['profiles']:
        return None
    data['profiles'][name] = {'apps': list(apps)}
    if save_profiles(data):
        return data
    return None


def delete_profile(name):
    """Borra un perfil. Si era el favorito, lo desmarca."""
    data = load_profiles()
    if name not in data['profiles']:
        return None
    del data['profiles'][name]
    if data.get('favorite') == name:
        data['favorite'] = None
    if save_profiles(data):
        return data
    return None


def set_favorite(name):
    """Marca un perfil como favorito (o None para desmarcar)."""
    data = load_profiles()
    if name is not None and name not in data['profiles']:
        return None
    data['favorite'] = name
    if save_profiles(data):
        return data
    return None


def launch_profile(profile_name, profiles=None):
    """Lanza las apps de un perfil: una instancia por nombre, sin args.

    Devuelve (launched: list, failed: list) con los nombres de las apps.
    """
    if profiles is None:
        profiles = load_profiles().get('profiles', {})
    if profile_name not in profiles:
        return [], [f"Perfil '{profile_name}' no existe"]
    apps = profiles[profile_name].get('apps', [])
    launched = []
    failed = []
    seen = set()
    for app_name in apps:
        # app_name es algo como "chrome.exe". Necesitamos el path completo para Popen.
        # Buscamos en self.processes (que se pasa como parametro si se quiere),
        # o usamos un fallback: el PATH del sistema.
        # Simplificacion v2.0: buscar el exe en la lista de procesos actuales
        # del sistema, o fallback a simplemente el nombre (Windows lo busca en PATH).
        if app_name.lower() in seen:
            continue  # dedupe
        seen.add(app_name.lower())
        try:
            # Popen con solo el nombre: Windows lo busca en PATH
            subprocess.Popen([app_name],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             creationflags=CREATE_NO_WINDOW)
            launched.append(app_name)
        except FileNotFoundError:
            failed.append(f"{app_name} (no encontrado en PATH)")
        except Exception as e:
            failed.append(f"{app_name} ({str(e)})")
    return launched, failed


class ProcessManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Process Manager - Gestor de Procesos")
        self.root.geometry("1000x720")

        # Estilo
        self.bg_color = "#1e1e1e"
        self.fg_color = "#ffffff"
        self.select_color = "#0078d4"
        self.warn_color = "#e81123"
        self.success_color = "#107c10"

        self.root.configure(bg=self.bg_color)

        # Variables
        self.processes = []
        self.saved_processes = load_saved_processes()
        self.program_map = {}  # item_id del tree -> {name, count, procs, ...} (v2.0)
        self.profiles_data = load_profiles()  # v2.0

        # Doble-tap: estado de confirmación pendiente (Trampa #14)
        # Clave: 'kill' / 'gaming' / 'launch_fav'. Valor: 'frozen' cuando la 1ª pulsacion
        # espera la 2ª. Auto-revert en 3s.
        # Bug #2 (rev 6): guardamos el botón exacto que activó el pending para
        # restaurar SOLO ese botón (no todos).
        self._pending_action = None  # None o {'key': str, 'selection_id': id(...), 'after_id': int, 'button': Button, 'normal_label': (str, str)}
        self._PENDING_TIMEOUT_MS = 3000

        self.create_widgets()
        self.load_processes()

    def create_widgets(self):
        """Crea los widgets de la interfaz."""

        # Header
        header = tk.Frame(self.root, bg=self.bg_color, pady=10)
        header.pack(fill=tk.X)

        title = tk.Label(header, text="🔄 Process Manager", font=("Segoe UI", 18, "bold"),
                       bg=self.bg_color, fg=self.fg_color)
        title.pack()

        subtitle = tk.Label(header, text="Selecciona procesos para cerrar o relanzar",
                          font=("Segoe UI", 10), bg=self.bg_color, fg="#888888")
        subtitle.pack()

        # Frame de acciones
        actions_frame = tk.Frame(self.root, bg=self.bg_color, pady=10)
        actions_frame.pack(fill=tk.X, padx=20)

        # Botones de accion (v2.0: modelo "1 fila por programa, kill todo, relanzar via perfiles")
        btn_refresh = tk.Button(actions_frame, text="🔄 Actualizar",
                               command=self.load_processes, bg="#333333", fg="white",
                               font=("Segoe UI", 10), padx=15, pady=8,
                               activebackground="#555555", cursor="hand2")
        btn_refresh.pack(side=tk.LEFT, padx=5)

        self.btn_kill = tk.Button(actions_frame, text="⛔ Matar Programa",
                            command=self.kill_selected, bg=self.warn_color, fg="white",
                            font=("Segoe UI", 10, "bold"), padx=15, pady=8,
                            activebackground="#c42b1c", cursor="hand2")
        self.btn_kill.pack(side=tk.LEFT, padx=5)

        # Botón estrella: preparar para gaming (mata TODOS los high/medium, no guarda)
        self.btn_gaming = tk.Button(actions_frame, text="🚀 Preparar para Gaming",
                              command=self.prepare_for_gaming, bg="#ff6600", fg="white",
                              font=("Segoe UI", 10, "bold"), padx=15, pady=8,
                              activebackground="#cc5200", cursor="hand2")
        self.btn_gaming.pack(side=tk.LEFT, padx=5)

        # Botón principal de relanzado: lanza el perfil favorito
        self.btn_launch_fav = tk.Button(actions_frame, text="★ Lanzar Favorito",
                                       command=self.launch_favorite_profile, bg="#9b59b6", fg="white",
                                       font=("Segoe UI", 10, "bold"), padx=15, pady=8,
                                       activebackground="#7d3f9b", cursor="hand2")
        self.btn_launch_fav.pack(side=tk.LEFT, padx=5)

        # Guardar estado normal de cada boton (para poder restaurar tras doble-tap)
        self._btn_kill_normal = ("⛔ Matar Programa", self.warn_color)
        self._btn_gaming_normal = ("🚀 Preparar para Gaming", "#ff6600")
        self._btn_launch_fav_normal = ("★ Lanzar Favorito", "#9b59b6")
        self._btn_kill_pending = ("⚠️ PULSA OTRA VEZ", "#ffcc00")
        self._btn_gaming_pending = ("⚠️ PULSA OTRA VEZ", "#ffcc00")
        self._btn_launch_fav_pending = ("⚠️ PULSA OTRA VEZ", "#ffcc00")

        # Botón para abrir el gestor de perfiles
        btn_profiles = tk.Button(actions_frame, text="📚 Perfiles",
                                command=self.open_profiles_dialog, bg="#3a6ea5", fg="white",
                                font=("Segoe UI", 10, "bold"), padx=15, pady=8,
                                activebackground="#2d5680", cursor="hand2")
        btn_profiles.pack(side=tk.LEFT, padx=5)

        # Toggle modo Simple / Categorías (segunda fila)
        mode_frame = tk.Frame(self.root, bg=self.bg_color, pady=5)
        mode_frame.pack(fill=tk.X, padx=20)

        self.simple_mode_var = tk.BooleanVar(value=True)  # Simple por defecto (gamer-friendly)
        mode_label = tk.Label(mode_frame, text="Modo:", font=("Segoe UI", 10),
                             bg=self.bg_color, fg=self.fg_color)
        mode_label.pack(side=tk.LEFT, padx=(0, 5))
        simple_rb = tk.Radiobutton(mode_frame, text="Simple (solo categorías gaming)",
                                   variable=self.simple_mode_var, value=True,
                                   command=self.toggle_mode,
                                   bg=self.bg_color, fg=self.fg_color,
                                   selectcolor=self.select_color,
                                   activebackground=self.bg_color,
                                   font=("Segoe UI", 9))
        simple_rb.pack(side=tk.LEFT, padx=5)
        full_rb = tk.Radiobutton(mode_frame, text="Completo (todas las categorías)",
                                variable=self.simple_mode_var, value=False,
                                command=self.toggle_mode,
                                bg=self.bg_color, fg=self.fg_color,
                                selectcolor=self.select_color,
                                activebackground=self.bg_color,
                                font=("Segoe UI", 9))
        full_rb.pack(side=tk.LEFT, padx=5)

        # Contador de guardados
        self.saved_label = tk.Label(actions_frame, text="",
                                   font=("Segoe UI", 10), bg=self.bg_color, fg="#888888")
        self.saved_label.pack(side=tk.LEFT, padx=20)
        self.update_saved_count()

        # Barra de busqueda
        search_frame = tk.Frame(self.root, bg=self.bg_color, padx=20, pady=5)
        search_frame.pack(fill=tk.X)

        tk.Label(search_frame, text="🔍 Buscar:", font=("Segoe UI", 10),
                bg=self.bg_color, fg=self.fg_color).pack(side=tk.LEFT)

        self.search_var = tk.StringVar()
        # Debounce: cancelar pending antes de agendar nuevo
        self._search_after_id = None
        self.search_var.trace('w', lambda *args: self._schedule_filter())
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                               font=("Segoe UI", 10), bg="#2d2d2d", fg="white",
                               insertbackground="white", width=40)
        search_entry.pack(side=tk.LEFT, padx=10)

        # Checkbox para seleccionar todos
        self.select_all_var = tk.BooleanVar(value=False)
        select_all_cb = tk.Checkbutton(search_frame, text="Seleccionar todos",
                                       variable=self.select_all_var,
                                       command=self.toggle_select_all,
                                       bg=self.bg_color, fg=self.fg_color,
                                       selectcolor=self.select_color,
                                       activebackground=self.bg_color,
                                       font=("Segoe UI", 10))
        select_all_cb.pack(side=tk.RIGHT)

        # Checkbox para matar tambien procesos hijos
        self.kill_tree_var = tk.BooleanVar(value=True)
        kill_tree_cb = tk.Checkbutton(search_frame, text="Matar hijos (/T)",
                                      variable=self.kill_tree_var,
                                      bg=self.bg_color, fg="#ffcc00",
                                      selectcolor=self.warn_color,
                                      activebackground=self.bg_color,
                                      font=("Segoe UI", 9))
        kill_tree_cb.pack(side=tk.RIGHT, padx=10)

        # Lista de procesos (Treeview)
        list_frame = tk.Frame(self.root, bg=self.bg_color)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Scrollbars
        vsb = ttk.Scrollbar(list_frame, orient="vertical")
        hsb = ttk.Scrollbar(list_frame, orient="horizontal")

        # Treeview con estilo oscuro
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background="#2d2d2d", foreground="white",
                       fieldbackground="#2d2d2d", rowheight=25)
        style.configure("Treeview.Heading", background="#333333", foreground="white")
        style.map("Treeview", background=[('selected', self.select_color)])

        self.tree = ttk.Treeview(list_frame, yscrollcommand=vsb.set,
                                 xscrollcommand=hsb.set, show='tree')
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        # Columnas
        self.tree['columns'] = ('pid', 'commandline')
        self.tree.column('#0', width=250, stretch=False)
        self.tree.column('pid', width=80, anchor='center')
        self.tree.column('commandline', width=600)

        self.tree.heading('#0', text='Proceso')
        self.tree.heading('pid', text='PID')
        self.tree.heading('commandline', text='Línea de comando')

        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # --- Interacciones mejoradas ---
        # Click izquierdo: toggle seleccion (sin Ctrl)
        self.tree.bind('<Button-1>', self._on_click)
        # Click derecho: menu contextual
        self.tree.bind('<Button-3>', self._show_context_menu)
        # Doble click: toggle categoria entera
        self.tree.bind('<Double-Button-1>', self._on_double_click)

        # Menu contextual (se construye una vez)
        self.context_menu = tk.Menu(self.root, tearoff=0,
                                    bg="#2d2d2d", fg="white",
                                    activebackground=self.select_color,
                                    activeforeground="white",
                                    font=("Segoe UI", 10))
        self.context_menu.add_command(label="⛔ Matar seleccionado(s)",
                                      command=self._ctx_kill)
        self.context_menu.add_command(label="💾 Guardar para relanzar",
                                      command=self._ctx_save)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📋 Copiar PID(s)",
                                      command=self._ctx_copy_pids)
        self.context_menu.add_command(label="📋 Copiar línea de comando",
                                      command=self._ctx_copy_cmdlines)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🔄 Refrescar lista",
                                      command=self.load_processes)

        # Atajos de teclado
        self.root.bind('<Control-a>', lambda e: self._select_all_visible())
        self.root.bind('<Control-A>', lambda e: self._select_all_visible())
        self.root.bind('<Delete>', lambda e: self.kill_selected())
        self.root.bind('<F5>', lambda e: self.load_processes())
        self.root.bind('<Control-r>', lambda e: self.load_processes())
        self.root.bind('<Control-R>', lambda e: self.load_processes())
        # Escape limpia la busqueda
        self.root.bind('<Escape>', lambda e: self.search_var.set(""))

        # Estado
        self.status_label = tk.Label(self.root, text="",
                                    font=("Segoe UI", 9), bg=self.bg_color, fg="#888888",
                                    anchor='w', padx=20, pady=5)
        self.status_label.pack(fill=tk.X)

    def load_processes(self):
        """Carga procesos en background (no bloquea la UI)."""
        if getattr(self, '_loading', False):
            return  # Evitar cargas concurrentes

        self._loading = True
        self.status_label.config(text="🔄 Cargando procesos...")

        def worker():
            """Hilo background que ejecuta PowerShell."""
            try:
                processes = get_running_processes()
                # Programar actualizacion UI en hilo principal
                self.root.after(0, self._on_processes_loaded, processes)
            except Exception as e:
                self.root.after(0, self._on_processes_error, str(e))

        threading.Thread(target=worker, daemon=True).start()

    def _on_processes_loaded(self, processes):
        """Callback cuando el hilo background termina (se ejecuta en hilo UI)."""
        self._loading = False
        self.processes = processes
        self.populate_tree()
        # update_count() ya pone el mensaje final

    def _on_processes_error(self, error_msg):
        """Callback si el hilo background falla."""
        self._loading = False
        self.status_label.config(text=f"❌ Error cargando procesos: {error_msg[:80]}")

    def populate_tree(self):
        """Llena el treeview agrupado por categorias, 1 fila por PROGRAMA unico.

        v2.0: en vez de 1 fila por PID, mostramos 1 fila por nombre unico (ej: 'firefox')
        con el contador de instancias. Matar la fila mata TODAS las instancias.

        Mantiene la seleccion por (name) — ya no por PID porque cada fila es 1 programa.
        """
        # Guardar seleccion actual por nombre de programa
        selected_names = set()
        for item_id in self.tree.selection():
            item = self.tree.item(item_id)
            vals = item['values']
            # Solo guardamos items hoja (programas)
            if vals and vals[0]:
                # El "name" esta guardado en el text, normalizado
                name = item['text'].strip()
                selected_names.add(name.lower())

        # Borrado atomico
        children = self.tree.get_children()
        if children:
            self.tree.delete(*children)

        # Resetear mapeo item_id -> programa
        self.program_map = {}

        search = self.search_var.get().lower()
        is_simple = self.simple_mode_var.get()

        # Agrupar procesos por (categoria, nombre) - 1 fila por programa unico
        by_program = {}  # (cat, name_lower) -> {name, category, count, procs, exe_path}
        for proc in self.processes:
            name = proc['name']
            cat = categorize_process(name)
            # En modo simple, solo mostrar categorias gaming
            if is_simple and cat not in SIMPLE_MODE_CATEGORIES and cat != '⚪ Otros':
                continue
            key = (cat, name.lower())
            if key not in by_program:
                # Sacar el exe path del commandline (primer token)
                cmdline = proc.get('commandline', '') or ''
                try:
                    args = shlex.split(cmdline, posix=False)
                except ValueError:
                    args = []
                exe_path = args[0] if args else name
                by_program[key] = {
                    'name': name,
                    'category': cat,
                    'count': 0,
                    'procs': [],
                    'exe_path': exe_path,
                }
            by_program[key]['count'] += 1
            by_program[key]['procs'].append(proc)

        # Ordenar categorias segun CATEGORY_ORDER, luego 'Otros' al final
        ordered_cats = [c for c in CATEGORY_ORDER if c in {k[0] for k in by_program}]
        if '⚪ Otros' in {k[0] for k in by_program}:
            ordered_cats.append('⚪ Otros')

        new_selection = []

        for cat in ordered_cats:
            programs_in_cat = [p for (c, _), p in by_program.items() if c == cat]
            programs_in_cat = sorted(programs_in_cat, key=lambda x: x['name'].lower())
            priority = PROCESS_CATEGORIES.get(cat, {}).get('priority', 'none')
            icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢', 'none': '⚫'}.get(priority, '⚪')
            # Insertar categoria como item padre (sin values)
            cat_id = self.tree.insert('', 'end',
                                     text=f"  {icon} {cat}  ({len(programs_in_cat)} apps)",
                                     open=True)

            for prog in programs_in_cat:
                # Filtrar por busqueda
                if search:
                    if (search not in prog['name'].lower()
                            and search not in prog['exe_path'].lower()):
                        continue

                count_str = f"{prog['count']} instancia(s)" if prog['count'] > 1 else "1 instancia"
                exe_disp = prog['exe_path']
                if len(exe_disp) > 80:
                    exe_disp = exe_disp[:77] + "..."

                item_id = self.tree.insert(cat_id, 'end',
                                          text=prog['name'],
                                          values=(count_str, exe_disp))

                # Guardar mapeo para kill
                self.program_map[item_id] = prog

                if prog['name'].lower() in selected_names:
                    new_selection.append(item_id)

        # Re-aplicar seleccion
        if new_selection:
            self.tree.selection_set(new_selection)

        self.update_count()

    def filter_processes(self):
        """Filtra los procesos segun la busqueda."""
        self.populate_tree()

    def _schedule_filter(self):
        """Agenda filter_processes con debounce de 150ms (evita lag en cada tecla)."""
        if self._search_after_id is not None:
            self.root.after_cancel(self._search_after_id)
        self._search_after_id = self.root.after(150, self._do_filter)

    def _do_filter(self):
        """Ejecuta el filtro (llamado por el debounce)."""
        self._search_after_id = None
        self.filter_processes()

    def toggle_select_all(self):
        """Selecciona o deselecciona todos los items HOJA visibles."""
        # Solo items hoja (los que tienen values[0] = pid)
        leaf_ids = []
        for cat_id in self.tree.get_children():
            for leaf_id in self.tree.get_children(cat_id):
                leaf_ids.append(leaf_id)

        if not leaf_ids:
            return

        if self.select_all_var.get():
            self.tree.selection_set(leaf_ids)
        else:
            self.tree.selection_remove(leaf_ids)

        self.update_count()

    # --- Interacciones de ratón ---

    def _on_click(self, event):
        """Click izquierdo: toggle seleccion del item clickeado (sin Ctrl)."""
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        # Es un item padre (categoria)?
        is_parent = not self.tree.item(item_id, 'values')
        if is_parent:
            # No toggleamos la categoria en si misma, solo sus hijos
            self._toggle_category_children(item_id)
        else:
            # Es un proceso (hoja): toggle individual
            current = self.tree.selection()
            if item_id in current:
                self.tree.selection_remove(item_id)
            else:
                self.tree.selection_add(item_id)

        # Marcar que ya manejamos el evento
        self.tree.focus(item_id)
        return "break"

    def _on_double_click(self, event):
        """Doble click: selecciona toda la categoria o expande/colapsa."""
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        is_parent = not self.tree.item(item_id, 'values')
        if is_parent:
            # Expandir/colapsar la categoria
            if self.tree.item(item_id, 'open'):
                self.tree.item(item_id, open=False)
            else:
                self.tree.item(item_id, open=True)
        return "break"

    def _toggle_category_children(self, cat_id):
        """Selecciona todos los hijos si la categoria no estaba, o desselecciona si estaba."""
        children = self.tree.get_children(cat_id)
        if not children:
            return

        current = self.tree.selection()
        # Si todos los hijos estan seleccionados, deseleccionar. Si no, seleccionar todos.
        all_selected = all(c in current for c in children)

        if all_selected:
            self.tree.selection_remove(children)
        else:
            self.tree.selection_add(children)

    def _select_all_visible(self):
        """Ctrl+A: selecciona todas las hojas visibles."""
        leaf_ids = []
        for cat_id in self.tree.get_children():
            for leaf_id in self.tree.get_children(cat_id):
                leaf_ids.append(leaf_id)
        if leaf_ids:
            self.tree.selection_set(leaf_ids)
        self.update_count()
        return "break"

    def _show_context_menu(self, event):
        """Click derecho: muestra menu contextual."""
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        # Si el item clickeado no esta seleccionado, seleccionarlo solo
        current = self.tree.selection()
        if item_id not in current:
            self.tree.selection_set(item_id)

        # Mostrar menu
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def _ctx_kill(self):
        """Menu contextual: matar lo seleccionado."""
        self.kill_selected()

    def _ctx_save(self):
        """Menu contextual: guardar lo seleccionado para relanzar."""
        self.save_selected()

    def _ctx_copy_pids(self):
        """Menu contextual: copiar PIDs al portapapeles."""
        selected = self.get_selected_processes()
        if not selected:
            return
        text = "\n".join(str(p['pid']) for p in selected)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_label.config(text=f"📋 {len(selected)} PID(s) copiados al portapapeles")

    def _ctx_copy_cmdlines(self):
        """Menu contextual: copiar lineas de comando al portapapeles."""
        selected = self.get_selected_processes()
        if not selected:
            return
        text = "\n".join(f"{p['name']}: {p['commandline']}" for p in selected)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_label.config(text=f"📋 {len(selected)} cmdline(s) copiados al portapapeles")

    def toggle_mode(self):
        """Cambia entre modo Simple y Completo."""
        self.populate_tree()

    # ========================================================================
    # Doble-tap (Trampa #14): confirmaciones SIN messagebox emergente.
    # ========================================================================

    def _set_status(self, text, color="#888888", bg=None):
        """Actualiza la barra de estado inline (NO messagebox).

        Si se pasa `bg`, la label queda con fondo coloreado para mayor
        visibilidad (verde exito / amarillo parcial / rojo fallo). Si no,
        fondo del tema (oscuro).
        """
        if bg:
            # Calcular fg en funcion del bg (contraste)
            fg = "black" if bg.lower() in ("#ffcc00", "#107c10", "#ffd700") else "white"
            self.status_label.config(text=text, fg=fg, bg=bg)
        else:
            self.status_label.config(text=text, fg=color, bg=self.bg_color)

    def _reset_pending_action(self):
        """Cancela cualquier confirmacion pendiente y restaura SOLO el botón pulsado (Bug #2)."""
        if self._pending_action is None:
            return
        # Cancelar timer
        try:
            if self._pending_action.get('after_id'):
                self.root.after_cancel(self._pending_action['after_id'])
        except Exception:
            pass
        # Restaurar SOLO el botón que activó el pending (Bug #2 fix)
        button = self._pending_action.get('button')
        normal_label = self._pending_action.get('normal_label')
        if button is not None and normal_label is not None:
            try:
                button.config(text=normal_label[0], bg=normal_label[1])
            except Exception:
                pass
        self._pending_action = None

    def _request_confirm(self, key, button, pending_label, summary_text, callback):
        """Maneja el doble-tap: 1ª pulsacion = freeze, 2ª = ejecuta.

        Args:
            key: 'kill' / 'gaming' / 'launch_fav' — identifica la accion.
            button: el widget tk.Button que se pulso (se usa para Bug #2: solo
                    cambia el boton pulsado, no todos).
            pending_label: tupla (texto, color) para el estado pendiente.
            summary_text: mensaje que muestra la status bar explicando que va a pasar.
            callback: funcion a ejecutar en la 2ª pulsacion.
        """
        # Si ya hay un pending de la MISMA key y la MISMA seleccion → CONFIRMAR
        if (self._pending_action is not None
                and self._pending_action['key'] == key
                and self._pending_action.get('selection_id') == id(self.tree.selection())):
            self._reset_pending_action()
            callback()
            return

        # Si hay pending de OTRA cosa o de OTRO boton, resetear y empezar fresco
        if self._pending_action is not None:
            self._reset_pending_action()

        # 1ª pulsacion: freeze SOLO del boton pulsado (Bug #2 fix)
        pending_text, pending_bg = pending_label

        # Determinar el label normal del boton pulsado (para restaurar luego)
        if button is self.btn_kill:
            normal_label = self._btn_kill_normal
        elif button is self.btn_gaming:
            normal_label = self._btn_gaming_normal
        elif button is self.btn_launch_fav:
            normal_label = self._btn_launch_fav_normal
        else:
            normal_label = (button.cget('text'), button.cget('bg'))

        # Aplicar visual cue SOLO al boton pulsado
        button.config(text=pending_text, bg=pending_bg)

        after_id = self.root.after(self._PENDING_TIMEOUT_MS, self._reset_pending_action)
        self._pending_action = {
            'key': key,
            'selection_id': id(self.tree.selection()),
            'after_id': after_id,
            'button': button,
            'normal_label': normal_label,
        }
        # Status label con fondo amarillo para que se vea claramente
        self._set_status(summary_text, "black", "#ffcc00")

    def prepare_for_gaming(self):
        """Mata TODOS los procesos que estorban en gaming (modo rapido, v2.0.3).

        Doble-tap para confirmar (Trampa #14): 1ª pulsacion = freeze,
        2ª = ejecuta. Auto-revert en 3s. Resultado en status label inline.

        Trampa #15: usa `should_kill_for_gaming()` que mata high+medium + chat
        (Telegram, Teams, Signal...) EXCEPTO los `GAMING_KEEPERS` (discord).
        Mantiene: launchers, overlays, antivirus, sistema, discord.
        Por cada nombre unico, hace taskkill /F /IM <name> /T que mata TODAS
        las instancias + sus hijos. NO guarda nada. Exit 128 (ya no estaba) se ignora.
        """
        # Agrupar TODOS los programas unicos que deben morir en gaming
        programs_to_kill = {}  # name -> count (del snapshot)
        kept_examples = []  # para mostrar al usuario que se mantuvo
        for proc in self.processes:
            name = proc['name']
            if should_kill_for_gaming(name):
                programs_to_kill[name] = programs_to_kill.get(name, 0) + 1
            else:
                if len(kept_examples) < 3:
                    kept_examples.append(name)

        if not programs_to_kill:
            self._set_status(
                "ℹ️  No hay procesos que matar para gaming (todo está limpio o son keepers)",
                "#888888",
            )
            return

        total = sum(programs_to_kill.values())
        # Preview corto para el status bar (max 8 programas)
        preview = ", ".join(sorted(programs_to_kill.keys())[:8])
        if len(programs_to_kill) > 8:
            preview += f" ... (+{len(programs_to_kill) - 8})"

        # Doble-tap: callback que ejecuta el kill real
        def do_kill():
            killed_names = []
            failed_details = []  # (name, error, remaining_count)
            for name in programs_to_kill:
                res = _run_kill(name)
                if res['killed']:
                    killed_names.append(name)
                elif res['already_gone']:
                    killed_names.append(name)  # ya no estaba, lo cuento como exito
                else:
                    detail = res['error'] or 'error desconocido'
                    if res['remaining']:
                        detail += f" ({res['remaining']} aun vivo(s))"
                    failed_details.append((name, detail))

            # Resultado inline (NO messagebox)
            if not failed_details and len(killed_names) == len(programs_to_kill):
                color, bg = "black", "#107c10"  # 100% exito
            elif failed_details and not killed_names:
                color, bg = "white", "#c42b1c"  # 100% fallo
            else:
                color, bg = "black", "#ffcc00"  # mixto

            msg = f"🚀 Gaming: {len(killed_names)}/{len(programs_to_kill)} cerrados"
            if failed_details:
                failed_preview = ", ".join(
                    f"{n} ({e[:50]})" for n, e in failed_details[:3]
                )
                if len(failed_details) > 3:
                    failed_preview += f" ... (+{len(failed_details) - 3})"
                msg += f" | ⚠️ fallaron: {failed_preview}"
            if kept_examples:
                msg += f" | mantenidos: {', '.join(kept_examples[:3])}"
            self._set_status(msg, color, bg)

            # Refrescar lista
            self.load_processes()

        kept_str = f" (mantengo {', '.join(kept_examples[:3])})" if kept_examples else ""
        summary_text = (
            f"⚠️ Vas a cerrar {len(programs_to_kill)} programa(s) "
            f"({total} instancias): {preview}{kept_str}. "
            f"Pulsa OTRA VEZ '🚀 Preparar para Gaming' para confirmar."
        )
        self._request_confirm(
            'gaming',
            self.btn_gaming,
            self._btn_gaming_pending,
            summary_text,
            do_kill,
        )

    def get_selected_processes(self):
        """Obtiene los procesos seleccionados (solo items hoja)."""
        selected = []
        for item_id in self.tree.selection():
            item = self.tree.item(item_id)
            vals = item['values']
            # Saltar items padre (sin values[0])
            if not vals or not vals[0]:
                continue

            name = item['text'].strip()
            pid = str(vals[0])

            # Encontrar el proceso completo
            for proc in self.processes:
                if proc['name'] == name and str(proc['pid']) == pid:
                    selected.append(proc)
                    break

        return selected

    def update_count(self):
        """Actualiza el contador de procesos (solo hojas)."""
        total_leaves = 0
        total_cats = len(self.tree.get_children())
        for cat_id in self.tree.get_children():
            total_leaves += len(self.tree.get_children(cat_id))

        selected = len(self.get_selected_processes())
        self.status_label.config(
            text=f"📊 {total_leaves} procesos en {total_cats} categorías | {selected} seleccionados"
        )

    def update_saved_count(self):
        """DEPRECATED v2.0: ya no hay lista de guardados. Reemplazado por Perfiles."""
        # Mantenido para compatibilidad; ya no se usa en la UI
        pass

    def kill_selected(self):
        """Mata TODOS los procesos de cada programa seleccionado.

        v2.0.2: doble-tap para confirmar (Trampa #14). 1ª pulsacion = freeze,
        2ª = ejecuta. Si cambia la seleccion mientras esta pending, el pending
        se invalida (no se ejecuta el kill con la seleccion vieja).

        v2.0.1: cada fila del tree es 1 PROGRAMA unico (no 1 PID). Al matar la fila,
        mueren TODOS los procesos de ese programa en el sistema, sin excepcion.
        Si seleccionas una CATEGORIA entera (ej: "🔴 Navegadores"), mata TODOS
        los programas de esa categoria. NO se filtra por duplicados: cada nombre
        unico recibe su propio taskkill /F /IM /T que mata todas las instancias
        del nombre en el sistema + sus hijos. Errores 'ya no existe' (exit 128)
        se ignoran. NO guarda nada.
        """
        # Recoger TODOS los nombres de programas a matar (dedup automatico por set)
        program_names = set()
        for item_id in self.tree.selection():
            if item_id in self.program_map:
                # Hoja: un programa
                program_names.add(self.program_map[item_id]['name'])
            else:
                # Posible categoria: recoger TODOS los hijos
                for child_id in self.tree.get_children(item_id):
                    if child_id in self.program_map:
                        program_names.add(self.program_map[child_id]['name'])

        if not program_names:
            self._set_status("⚠️ No hay programas seleccionados", "#ffcc00")
            self._reset_pending_action()
            return

        # Si cambio la seleccion desde el 1º click, invalidar pending previo
        current_sel_id = id(self.tree.selection())
        if (self._pending_action is not None
                and self._pending_action.get('selection_id') != current_sel_id):
            self._reset_pending_action()

        # Doble-tap: callback que ejecuta el kill real
        def do_kill():
            killed_names = []
            failed_details = []  # (name, error, remaining_count)
            for name in sorted(program_names):
                res = _run_kill(name)
                if res['killed']:
                    killed_names.append(name)
                elif res['already_gone']:
                    killed_names.append(name)  # ya no estaba, lo cuento como exito
                else:
                    detail = res['error'] or 'error desconocido'
                    if res['remaining']:
                        detail += f" ({res['remaining']} aun vivo(s))"
                    failed_details.append((name, detail))

            # Resultado inline (NO messagebox) con fondo coloreado para visibilidad
            if not failed_details and len(killed_names) == len(program_names):
                color, bg = "black", "#107c10"  # 100% exito
            elif failed_details and not killed_names:
                color, bg = "white", "#c42b1c"  # 100% fallo
            else:
                color, bg = "black", "#ffcc00"  # mixto
            preview = ", ".join(sorted(killed_names)[:5])
            if len(killed_names) > 5:
                preview += f" ... (+{len(killed_names) - 5})"
            msg = f"⛔ {len(killed_names)}/{len(program_names)} cerrados: {preview}"
            if failed_details:
                failed_preview = ", ".join(
                    f"{n} ({e[:50]})" for n, e in failed_details[:3]
                )
                if len(failed_details) > 3:
                    failed_preview += f" ... (+{len(failed_details) - 3})"
                msg += f" | ⚠️ fallaron: {failed_preview}"
            self._set_status(msg, color, bg)

            # NO guardar nada - el relanzado es via Perfiles (v2.0)
            # Recargar la lista
            self.load_processes()

        # Preview corto para el status bar
        preview = ", ".join(sorted(program_names)[:5])
        if len(program_names) > 5:
            preview += f" ... (+{len(program_names) - 5})"
        summary_text = (
            f"⚠️ Vas a cerrar {len(program_names)} programa(s): {preview}. "
            f"Pulsa OTRA VEZ '⛔ Matar Programa' para confirmar (auto-revert en 3s)."
        )
        self._request_confirm(
            'kill',
            self.btn_kill,
            self._btn_kill_pending,
            summary_text,
            do_kill,
        )

    def save_selected(self):
        """DEPRECATED v2.0: el guardado automatico se elimino. Usar Perfiles."""
        self._set_status(
            "ℹ️  Guardado automático eliminado en v2.0. Crea un Perfil desde '📚 Perfiles'.",
            "#888888",
        )

    def relaunch_saved(self):
        """DEPRECATED v2.0: ver launch_favorite_profile()"""
        self.launch_favorite_profile()

    def clear_saved(self):
        """DEPRECATED v2.0: no hay lista de guardados."""
        pass

    def launch_favorite_profile(self):
        """Lanza el perfil marcado como favorito.

        v2.0.2: doble-tap (Trampa #14). Errores van al status label inline,
        no messagebox.
        """
        fav = self.profiles_data.get('favorite')
        if not fav:
            self._set_status(
                "ℹ️  No hay perfil favorito. Abre '📚 Perfiles' para crear uno y marcarlo.",
                "#888888",
            )
            self._reset_pending_action()
            return
        if fav not in self.profiles_data.get('profiles', {}):
            self._set_status(
                f"❌ El perfil favorito '{fav}' ya no existe. Abre '📚 Perfiles' para revisar.",
                self.warn_color,
            )
            self._reset_pending_action()
            return
        apps = self.profiles_data['profiles'][fav].get('apps', [])
        if not apps:
            self._set_status(f"ℹ️  El perfil '{fav}' no tiene apps.", "#888888")
            self._reset_pending_action()
            return

        # Doble-tap: callback que lanza el perfil
        def do_launch():
            launched, failed = launch_profile(fav, self.profiles_data.get('profiles'))
            if not failed and len(launched) == len(apps):
                color, bg = "black", "#107c10"
            elif failed and not launched:
                color, bg = "white", "#c42b1c"
            else:
                color, bg = "black", "#ffcc00"
            preview = ", ".join(launched[:5])
            if len(launched) > 5:
                preview += f" ... (+{len(launched) - 5})"
            msg = f"★ '{fav}': {len(launched)}/{len(apps)} apps lanzadas: {preview}"
            if failed:
                failed_preview = ", ".join(failed[:3])
                if len(failed) > 3:
                    failed_preview += f" ... (+{len(failed) - 3})"
                msg += f" | ⚠️ fallaron: {failed_preview}"
            self._set_status(msg, color, bg)
            # Refrescar para ver los nuevos procesos
            self.load_processes()

        preview = ", ".join(apps[:5])
        if len(apps) > 5:
            preview += f" ... (+{len(apps) - 5})"
        summary_text = (
            f"⚠️ Vas a lanzar el perfil '{fav}' ({len(apps)} apps): {preview}. "
            f"Pulsa OTRA VEZ '★ Lanzar Favorito' para confirmar."
        )
        self._request_confirm(
            'launch_fav',
            self.btn_launch_fav,
            self._btn_launch_fav_pending,
            summary_text,
            do_launch,
        )

    def open_profiles_dialog(self):
        """Abre la ventana de gestion de perfiles."""
        ProfilesDialog(self.root, self)


class ProfilesDialog:
    """Ventana modal para gestionar perfiles de relanzado (v2.0).

    Lista los perfiles, permite crear/editar/borrar/marcar favorito/lanzar.
    Cada perfil es una lista de nombres de ejecutables (ej: ['chrome.exe', 'discord.exe']).
    """

    def __init__(self, parent, app):
        self.app = app
        self.win = tk.Toplevel(parent)
        self.win.title("📚 Perfiles de relanzado")
        self.win.geometry("700x550")
        self.win.configure(bg=app.bg_color)
        self.win.transient(parent)
        self.win.grab_set()  # modal

        # Estado
        self.data = load_profiles()

        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        bg = self.app.bg_color
        fg = self.app.fg_color

        # Header
        tk.Label(self.win, text="📚 Perfiles de relanzado",
                font=("Segoe UI", 16, "bold"), bg=bg, fg=fg).pack(pady=10)

        tk.Label(self.win, text="Crea packs de apps para relanzar con un click. Marca uno como favorito para lanzarlo desde el botón principal.",
                font=("Segoe UI", 9), bg=bg, fg="#888888", wraplength=650).pack(pady=(0, 10))

        # Frame principal: lista + botones
        main_frame = tk.Frame(self.win, bg=bg)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        # Lista de perfiles
        list_frame = tk.Frame(main_frame, bg=bg)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(list_frame, text="Perfiles:", font=("Segoe UI", 11),
                bg=bg, fg=fg).pack(anchor=tk.W)

        listbox_frame = tk.Frame(list_frame, bg=bg)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.profile_listbox = tk.Listbox(
            listbox_frame, yscrollcommand=scrollbar.set,
            bg="#2d2d2d", fg=fg, selectbackground=self.app.select_color,
            font=("Segoe UI", 11), height=10, activestyle='none'
        )
        self.profile_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.profile_listbox.yview)
        self.profile_listbox.bind('<<ListboxSelect>>', self._on_select)

        # Detalle del perfil seleccionado
        detail_frame = tk.Frame(main_frame, bg=bg)
        detail_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(15, 0))

        tk.Label(detail_frame, text="Apps del perfil:", font=("Segoe UI", 11),
                bg=bg, fg=fg).pack(anchor=tk.W)

        apps_list_frame = tk.Frame(detail_frame, bg=bg)
        apps_list_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        apps_scrollbar = tk.Scrollbar(apps_list_frame)
        apps_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.apps_listbox = tk.Listbox(
            apps_list_frame, yscrollcommand=apps_scrollbar.set,
            bg="#2d2d2d", fg=fg, selectbackground=self.app.select_color,
            font=("Consolas", 10), height=10
        )
        self.apps_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        apps_scrollbar.config(command=self.apps_listbox.yview)

        # Indicador de favorito
        self.fav_label = tk.Label(detail_frame, text="", font=("Segoe UI", 10, "bold"),
                                  bg=bg, fg="#ffcc00")
        self.fav_label.pack(anchor=tk.W, pady=(5, 0))

        # Botones de accion
        btn_frame = tk.Frame(self.win, bg=bg, pady=10)
        btn_frame.pack(fill=tk.X, padx=20)

        tk.Button(btn_frame, text="➕ Nuevo", command=self.new_profile,
                  bg=self.app.success_color, fg="white", font=("Segoe UI", 10, "bold"),
                  padx=12, pady=6, cursor="hand2").pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text="✏️ Editar", command=self.edit_profile,
                  bg=self.app.select_color, fg="white", font=("Segoe UI", 10, "bold"),
                  padx=12, pady=6, cursor="hand2").pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text="🗑️ Borrar", command=self.delete_profile,
                  bg="#666666", fg="white", font=("Segoe UI", 10, "bold"),
                  padx=12, pady=6, cursor="hand2").pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text="⭐ Favorito", command=self.toggle_favorite,
                  bg="#ffcc00", fg="black", font=("Segoe UI", 10, "bold"),
                  padx=12, pady=6, cursor="hand2").pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text="▶️ Lanzar", command=self.launch_selected,
                  bg="#9b59b6", fg="white", font=("Segoe UI", 10, "bold"),
                  padx=12, pady=6, cursor="hand2").pack(side=tk.LEFT, padx=3)

        tk.Button(btn_frame, text="Cerrar", command=self.win.destroy,
                  bg="#444444", fg="white", font=("Segoe UI", 10),
                  padx=12, pady=6, cursor="hand2").pack(side=tk.RIGHT, padx=3)

    def _refresh_list(self):
        self.profile_listbox.delete(0, tk.END)
        fav = self.data.get('favorite')
        profiles = self.data.get('profiles', {})
        for name in sorted(profiles.keys()):
            display = f"★ {name}" if name == fav else f"  {name}"
            self.profile_listbox.insert(tk.END, display)

    def _on_select(self, event=None):
        sel = self.profile_listbox.curselection()
        if not sel:
            self.apps_listbox.delete(0, tk.END)
            self.fav_label.config(text="")
            return
        # El nombre real sin el prefijo ★
        display = self.profile_listbox.get(sel[0])
        name = display.lstrip("★ ").strip()
        apps = self.data.get('profiles', {}).get(name, {}).get('apps', [])
        self.apps_listbox.delete(0, tk.END)
        for app in apps:
            self.apps_listbox.insert(tk.END, app)
        if self.data.get('favorite') == name:
            self.fav_label.config(text=f"⭐ '{name}' es el favorito")
        else:
            self.fav_label.config(text="")

    def _selected_name(self):
        sel = self.profile_listbox.curselection()
        if not sel:
            return None
        display = self.profile_listbox.get(sel[0])
        return display.lstrip("★ ").strip()

    def new_profile(self):
        """Dialog para crear un perfil nuevo."""
        name = self._prompt_string("Nuevo perfil", "Nombre del perfil:")
        if not name:
            return
        if name in self.data.get('profiles', {}):
            messagebox.showerror("Error", f"Ya existe un perfil '{name}'", parent=self.win)
            return
        apps = self._prompt_apps(name, initial=[])
        if apps is None:
            return
        self.data = create_profile(name, apps) or self.data
        self.app.profiles_data = self.data
        self._refresh_list()

    def edit_profile(self):
        name = self._selected_name()
        if not name:
            messagebox.showwarning("Aviso", "Selecciona un perfil primero", parent=self.win)
            return
        current_apps = self.data['profiles'][name].get('apps', [])
        apps = self._prompt_apps(name, initial=current_apps)
        if apps is None:
            return
        self.data = update_profile(name, apps) or self.data
        self.app.profiles_data = self.data
        self._refresh_list()
        self._on_select()

    def delete_profile(self):
        name = self._selected_name()
        if not name:
            messagebox.showwarning("Aviso", "Selecciona un perfil primero", parent=self.win)
            return
        if not messagebox.askyesno(
            "Confirmar", f"¿Borrar el perfil '{name}'?", parent=self.win
        ):
            return
        self.data = delete_profile(name) or self.data
        self.app.profiles_data = self.data
        self._refresh_list()
        self._on_select()

    def toggle_favorite(self):
        name = self._selected_name()
        if not name:
            messagebox.showwarning("Aviso", "Selecciona un perfil primero", parent=self.win)
            return
        current = self.data.get('favorite')
        if current == name:
            # Desmarcar
            self.data = set_favorite(None) or self.data
        else:
            self.data = set_favorite(name) or self.data
        self.app.profiles_data = self.data
        self._refresh_list()
        self._on_select()

    def launch_selected(self):
        name = self._selected_name()
        if not name:
            messagebox.showwarning("Aviso", "Selecciona un perfil primero", parent=self.win)
            return
        apps = self.data['profiles'][name].get('apps', [])
        if not apps:
            messagebox.showinfo("Vacío", "Este perfil no tiene apps", parent=self.win)
            return
        launched, failed = launch_profile(name, self.data['profiles'])
        msg = f"Perfil '{name}' lanzado: {len(launched)}/{len(apps)} apps\n"
        if failed:
            msg += "\nFallidos:\n" + "\n".join(failed[:5])
        messagebox.showinfo("Resultado", msg, parent=self.win)
        self.app.load_processes()

    def _prompt_string(self, title, prompt):
        """Dialog simple que pide un string."""
        dlg = tk.Toplevel(self.win)
        dlg.title(title)
        dlg.geometry("350x120")
        dlg.configure(bg=self.app.bg_color)
        dlg.transient(self.win)
        dlg.grab_set()

        result = {"value": None}

        tk.Label(dlg, text=prompt, bg=self.app.bg_color, fg=self.app.fg_color,
                font=("Segoe UI", 10)).pack(pady=(15, 5))
        entry = tk.Entry(dlg, font=("Segoe UI", 11), bg="#2d2d2d", fg="white",
                        insertbackground="white", width=30)
        entry.pack(pady=5)
        entry.focus_set()

        def ok():
            result["value"] = entry.get().strip()
            dlg.destroy()
        def cancel():
            dlg.destroy()

        btn_frame = tk.Frame(dlg, bg=self.app.bg_color)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="OK", command=ok, bg=self.app.select_color, fg="white",
                  padx=15, pady=3).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancelar", command=cancel, bg="#666666", fg="white",
                  padx=15, pady=3).pack(side=tk.LEFT, padx=5)

        entry.bind('<Return>', lambda e: ok())
        entry.bind('<Escape>', lambda e: cancel())

        self.win.wait_window(dlg)
        return result["value"]

    def _prompt_apps(self, profile_name, initial):
        """Dialog para editar la lista de apps de un perfil.

        Una app por linea. Devuelve la lista o None si cancela.
        """
        dlg = tk.Toplevel(self.win)
        dlg.title(f"Editar apps: {profile_name}")
        dlg.geometry("500x450")
        dlg.configure(bg=self.app.bg_color)
        dlg.transient(self.win)
        dlg.grab_set()

        result = {"value": None}

        tk.Label(dlg, text="Una app por linea (ej: chrome.exe, discord.exe):",
                bg=self.app.bg_color, fg=self.app.fg_color,
                font=("Segoe UI", 10)).pack(pady=(10, 5))

        text_frame = tk.Frame(dlg, bg=self.app.bg_color)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=15)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text = tk.Text(text_frame, yscrollcommand=scrollbar.set,
                      bg="#2d2d2d", fg="white", insertbackground="white",
                      font=("Consolas", 10), wrap=tk.WORD)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text.yview)

        # Insertar apps iniciales
        for app in initial:
            text.insert(tk.END, app + "\n")

        # Sugerencias (procesos actualmente corriendo)
        def add_running():
            """Anade los nombres unicos de procesos corriendo al editor."""
            existing = text.get("1.0", tk.END).strip().splitlines()
            existing_set = {a.strip().lower() for a in existing if a.strip()}
            added = 0
            for proc in self.app.processes:
                name = proc['name']
                if name.lower() not in existing_set:
                    text.insert(tk.END, name + "\n")
                    existing_set.add(name.lower())
                    added += 1
            if added == 0:
                messagebox.showinfo("Info", "Todos los procesos ya estan en la lista", parent=dlg)

        btn_frame = tk.Frame(dlg, bg=self.app.bg_color, pady=10)
        btn_frame.pack(fill=tk.X)

        tk.Button(btn_frame, text="📋 Añadir procesos corriendo",
                  command=add_running, bg="#3a6ea5", fg="white",
                  font=("Segoe UI", 9), padx=10, pady=4, cursor="hand2"
                  ).pack(side=tk.LEFT, padx=5)

        def ok():
            content = text.get("1.0", tk.END).strip()
            apps = [line.strip() for line in content.splitlines() if line.strip()]
            # Dedupe case-insensitive
            seen = set()
            deduped = []
            for a in apps:
                if a.lower() not in seen:
                    seen.add(a.lower())
                    deduped.append(a)
            result["value"] = deduped
            dlg.destroy()
        def cancel():
            dlg.destroy()

        tk.Button(btn_frame, text="Guardar", command=ok, bg=self.app.success_color, fg="white",
                  font=("Segoe UI", 10, "bold"), padx=15, pady=4, cursor="hand2"
                  ).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Cancelar", command=cancel, bg="#666666", fg="white",
                  font=("Segoe UI", 10), padx=15, pady=4, cursor="hand2"
                  ).pack(side=tk.RIGHT, padx=5)

        dlg.wait_window(dlg)
        return result["value"]


def main():
    root = tk.Tk()
    app = ProcessManagerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()