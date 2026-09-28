import os
import sys
from typing import Dict, Any

def _app_dir() -> str:
    """Devuelve el directorio donde está el ejecutable (frozen o dev)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

PROCESS_LIST_FILE = os.path.join(_app_dir(), 'saved_processes.json')
PROFILES_FILE = os.path.join(_app_dir(), 'profiles.json')


PROCESS_CATEGORIES: Dict[str, Dict[str, Any]] = {
    '🔴 Navegadores': {
        'priority': 'high',
        'patterns': ['chrome', 'firefox', 'msedge', 'opera', 'brave', 'vivaldi', 'safari'],
        'description': 'Navegadores web, consumen mucha RAM.'
    },
    '🔴 Sincronización': {
        'priority': 'high',
        'patterns': ['nextcloud', 'onedrive', 'googledrivesync', 'dropbox', 'megasync', 'syncthing'],
        'description': 'Apps de cloud. Causan lag spikes.'
    },
    '🟡 Chat y Comunicación': {
        'priority': 'low', 
        'patterns': ['discord', 'teams', 'slack', 'skype', 'telegram', 'whatsapp', 'signal', 'viber'],
        'description': 'Cerrar salvo el keeper (Discord).'
    },
    '🟡 Productividad': {
        'priority': 'medium',
        'patterns': ['winword', 'excel', 'powerpnt', 'notion', 'obsidian', 'evernote'],
        'description': 'Herramientas de trabajo.'
    },
    '🟡 Media y Streaming': {
        'priority': 'medium',
        'patterns': ['spotify', 'vlc', 'itunes', 'obs32', 'obs64'],
        'description': 'Reproductores.'
    },
    '🟢 Overlays e Info': {
        'priority': 'none',
        'patterns': ['rtss', 'msiafterburner', 'hwinfo32', 'hwinfo64'],
        'description': 'Herramientas de monitorización gaming.'
    },
    '🟢 Launchers Gaming': {
        'priority': 'none',
        'patterns': ['steam', 'epicgameslauncher', 'gog galaxy', 'origin', 'upc', 'riotclient', 'battlenet'],
        'description': 'Launchers de juegos (mantener).'
    },
    '⚫ Antivirus y Seguridad': {
        'priority': 'none',
        'patterns': ['avg', 'avast', 'norton', 'mcshield', 'msmpeng', 'smartscreen', 'vmware'],
        'description': 'Procesos de seguridad y VM.'
    },
    '⚫ Sistema de Windows': {
        'priority': 'none',
        'patterns': ['explorer', 'svchost', 'system', 'registry', 'smss', 'csrss', 'wininit', 'services', 'lsass', 'winlogon', 'fontdrvhost', 'dwm', 'spoolsv', 'taskmgr', 'conhost', 'cmd', 'powershell', 'wsl', 'searchindexer', 'searchui'],
        'description': 'Procesos core.'
    }
}

SIMPLE_MODE_CATEGORIES = [
    '🔴 Navegadores',
    '🔴 Sincronización',
    '🟡 Chat y Comunicación',
    '🟡 Productividad',
    '🟡 Media y Streaming'
]

CATEGORY_ORDER = list(PROCESS_CATEGORIES.keys()) + ['⚪ Otros']
