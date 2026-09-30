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


# TASK-020: los emojis de categoria DEBEN coincidir exactamente con los usados en
# `assets/process_db.json` y con el sistema de diseno de `docs/ai/ui-design-system.md`.
#
# Semantica del semaforo (ver ui-design-system.md, "Semaforo Visual de Seguridad"):
#   🟢 SEGURO     -> verde    = seguro de cerrar (navegadores, nube, productividad)
#   🟡 PRECAUCION -> amarillo = cerrar solo si no se usa (chat, media, launchers)
#   🔴 NO CERRAR  -> rojo     = critico de sistema o hardware (sistema, AV, overlays)
#
# Si un emoji no coincide con el del JSON, el lookup por categoria falla y el
# proceso cae en "⚪ Otros" (U+26AA, NO la interrogacion ASCII "?") perdiendo su
# semaforo de seguridad. El centinela canonico vive en CATEGORY_ORDER[-1] y en
# models.py; si cambia, cambia en los tres sitios a la vez (TASK-026 FIX-005).
PROCESS_CATEGORIES: Dict[str, Dict[str, Any]] = {
    '🟢 Navegadores': {
        'priority': 'high',
        'patterns': ['chrome', 'firefox', 'msedge', 'opera', 'brave', 'vivaldi', 'safari'],
        'description': 'Navegadores web, consumen mucha RAM.'
    },
    '🟢 Sincronización': {
        'priority': 'high',
        'patterns': ['nextcloud', 'onedrive', 'googledrivesync', 'dropbox', 'megasync', 'syncthing'],
        'description': 'Apps de cloud. Causan lag spikes.'
    },
    '🟡 Chat y Comunicación': {
        'priority': 'low', 
        'patterns': ['discord', 'teams', 'slack', 'skype', 'telegram', 'whatsapp', 'signal', 'viber'],
        'description': 'Cerrar salvo el keeper (Discord).'
    },
    '🟢 Productividad': {
        'priority': 'medium',
        'patterns': ['winword', 'excel', 'powerpnt', 'notion', 'obsidian', 'evernote'],
        'description': 'Herramientas de trabajo.'
    },
    '🟡 Media y Streaming': {
        'priority': 'medium',
        'patterns': ['spotify', 'vlc', 'itunes', 'obs32', 'obs64'],
        'description': 'Reproductores.'
    },
    '🔴 Overlays e Info': {
        'priority': 'none',
        'patterns': ['rtss', 'msiafterburner', 'hwinfo32', 'hwinfo64'],
        'description': 'Herramientas de monitorización gaming.'
    },
    '🟡 Launchers Gaming': {
        'priority': 'none',
        'patterns': ['steam', 'epicgameslauncher', 'gog galaxy', 'origin', 'upc', 'riotclient', 'battlenet'],
        'description': 'Launchers de juegos (mantener).'
    },
    '🔴 Antivirus y Seguridad': {
        'priority': 'none',
        'patterns': ['avg', 'avast', 'norton', 'mcshield', 'msmpeng', 'smartscreen', 'vmware'],
        'description': 'Procesos de seguridad y VM.'
    },
    '🔴 Sistema de Windows': {
        'priority': 'none',
        'patterns': ['explorer', 'svchost', 'system', 'registry', 'smss', 'csrss', 'wininit', 'services', 'lsass', 'winlogon', 'fontdrvhost', 'dwm', 'spoolsv', 'taskmgr', 'conhost', 'cmd', 'powershell', 'wsl', 'searchindexer', 'searchui'],
        'description': 'Procesos core.'
    }
}

SIMPLE_MODE_CATEGORIES = [
    '🟢 Navegadores',
    '🟢 Sincronización',
    '🟡 Chat y Comunicación',
    '🟢 Productividad',
    '🟡 Media y Streaming'
]

CATEGORY_ORDER = list(PROCESS_CATEGORIES.keys()) + ['⚪ Otros']


def ordenar_categorias(cats) -> list:
    """Ordena los NOMBRES de categoria siguiendo CATEGORY_ORDER.

    TASK-027 (FIX-004). Existe porque `sorted()` NO ordena "alfabeticamente"
    cuando la cadena empieza por un emoji: ordena por PUNTO DE CODIGO, y el
    centinela canonico ⚪ Otros es U+26AA (plano BMP) mientras que 🟢🟡🔴 estan
    en el plano suplementario (U+1F7E2, U+1F7E1, U+1F534). Medido sobre la lista
    real: `sorted()` pone ⚪ Otros PRIMERO y los 🔴 "NO CERRAR" antes que los 🟢
    "SEGURO", o sea exactamente el orden contrario al que el semaforo comunica.

    Reglas:
      * manda `CATEGORY_ORDER` (no el color): la fuente de verdad es la misma que
        ya usa `ProcessService.get_running_processes()`;
      * `sorted` es ESTABLE, asi que las categorias desconocidas (centinela 999)
        se quedan al final conservando su ORDEN DE ENTRADA entre ellas;
      * no se deriva de `get_safety_badge`: el orden es presentacion, el
        semaforo es otra frontera con sus propios tests.

    Una sola funcion para los DOS sitios que la necesitan
    (`process_manager_view._render_list` y `pack_manager_view._render_pack_card`):
    con dos implementaciones, el defecto vuelve por la puerta que se olvide.
    """
    idx = {c: i for i, c in enumerate(CATEGORY_ORDER)}
    return sorted(cats, key=lambda c: idx.get(c, 999))


def get_safety_badge(category: str, priority: str = "none") -> dict:
    """Devuelve la recomendación, colores y texto intuitivo para la UI.

    TASK-020: el emoji de CATEGORIA manda sobre la prioridad.
    Antes se evaluaba `priority in [medium, low]` antes que la rama del emoji
    rojo, de modo que una categoria 🔴 con prioridad `low` se pintaba
    🟡 PRECAUCIÓN en lugar de 🔴 NO CERRAR. Ahora la categoria se resuelve
    primero y la prioridad solo actúa como desempate si la categoria es
    desconocida.
    """
    cat_lower = (category or "").lower()
    prio_lower = (priority or "").lower()

    # 1) El emoji de la categoria es la fuente de verdad del semaforo.
    if "🔴" in (category or ""):
        return {
            "text": "🔴 NO CERRAR",
            "recommendation": "Crítico del sistema o hardware",
            "fg_color": "#401616",       # Rojo oscuro fondo
            "text_color": "#ff6b6b",     # Rojo brillante
            "tier": "danger"
        }
    if "🟡" in (category or ""):
        return {
            "text": "🟡 PRECAUCIÓN",
            "recommendation": "Cerrar sólo si no lo usas para jugar",
            "fg_color": "#3d3711",       # Amarillo oscuro fondo
            "text_color": "#fcc419",     # Amarillo brillante
            "tier": "caution"
        }
    if "🟢" in (category or ""):
        return {
            "text": "🟢 SEGURO",
            "recommendation": "Cierre recomendado (libera RAM/CPU)",
            "fg_color": "#163820",       # Verde oscuro fondo
            "text_color": "#40c057",     # Verde brillante
            "tier": "safe"
        }

    # 2) Desempate: categorias sin emoji, resueltas por palabras clave.
    if any(k in cat_lower for k in ["sistema", "antivirus", "overlay"]):
        return {
            "text": "🔴 NO CERRAR",
            "recommendation": "Crítico del sistema o hardware",
            "fg_color": "#401616",
            "text_color": "#ff6b6b",
            "tier": "danger"
        }
    if any(k in cat_lower for k in ["chat", "launcher", "media"]) or prio_lower in ["medium", "low"]:
        return {
            "text": "🟡 PRECAUCIÓN",
            "recommendation": "Cerrar sólo si no lo usas para jugar",
            "fg_color": "#3d3711",
            "text_color": "#fcc419",
            "tier": "caution"
        }
    if prio_lower == "high" or any(k in cat_lower for k in ["sincroniz", "navegador", "productiv"]):
        return {
            "text": "🟢 SEGURO",
            "recommendation": "Cierre recomendado (libera RAM/CPU)",
            "fg_color": "#163820",
            "text_color": "#40c057",
            "tier": "safe"
        }

    # Desconocido
    return {
        "text": "⚪ OTROS",
        "recommendation": "Sin clasificar",
        "fg_color": "#2b2b2b",
        "text_color": "#adb5bd",
        "tier": "unknown"
    }
