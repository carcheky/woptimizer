import os
import sys
from typing import Dict, Any

def _app_dir() -> str:
    """Devuelve el directorio donde está el ejecutable (frozen o dev)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

def _data_dir() -> str:
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

import logging

logging.basicConfig(
    filename=os.path.join(_app_dir(), 'woptimizer.log'),
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('woptimizer')

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


def get_safety_badge(category: str, priority: str = "none") -> dict:
    """Devuelve la recomendación, colores y texto intuitivo para la UI."""
    cat_lower = (category or "").lower()
    prio_lower = (priority or "").lower()
    
    # Verde: Seguro de cerrar para gaming (Browsers, Sync, Productividad)
    if "🟢" in category or prio_lower == "high" or any(k in cat_lower for k in ["sincroniz", "navegador", "productiv"]):
        return {
            "text": "🟢 SEGURO",
            "recommendation": "Cierre recomendado (libera RAM/CPU)",
            "fg_color": "#163820",       # Verde oscuro fondo
            "text_color": "#40c057",     # Verde brillante
            "tier": "safe"
        }
    # Amarillo: Precaución / Útil para gaming (Launchers, Chat, Media)
    elif "🟡" in category or prio_lower in ["medium", "low"] or any(k in cat_lower for k in ["chat", "launcher", "media"]):
        return {
            "text": "🟡 PRECAUCIÓN",
            "recommendation": "Cerrar sólo si no lo usas para jugar",
            "fg_color": "#3d3711",       # Amarillo oscuro fondo
            "text_color": "#fcc419",     # Amarillo brillante
            "tier": "caution"
        }
    # Rojo: Peligro / Sistema / Periféricos (Windows, Antivirus, Overlays/Hardware)
    elif "🔴" in category or any(k in cat_lower for k in ["sistema", "antivirus", "overlay"]):
        return {
            "text": "🔴 NO CERRAR",
            "recommendation": "Crítico del sistema o hardware",
            "fg_color": "#401616",       # Rojo oscuro fondo
            "text_color": "#ff6b6b",     # Rojo brillante
            "tier": "danger"
        }
    # Desconocido
    else:
        return {
            "text": "⚪ OTROS",
            "recommendation": "Sin clasificar",
            "fg_color": "#2b2b2b",
            "text_color": "#adb5bd",
            "tier": "unknown"
        }
