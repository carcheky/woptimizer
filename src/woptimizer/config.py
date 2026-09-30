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
from logging.handlers import RotatingFileHandler

# TASK-028 (FIX-010): el contrato de log de `docs/ai/architecture.md` §5 dice que
# los errores "se canalizan a woptimizer.log". Antes ese contrato se cumplia por
# un `logging.basicConfig(...)` de NIVEL DE MODULO, o sea como efecto colateral
# de importar `config`. Eso se rompe en silencio en cuanto alguien importa el
# paquete sin pasar por `__main__` (la suite `run_tests.py` es el caso real: la
# huella son 1,8 MB de avisos acumulados en `woptimizer.log`). Por eso ahora
# el canal se declara, se invoca (idempotente) y se puede comprobar.
#
# `force=True` NO es cosmetico: `basicConfig()` es un no-op mudo si el root ya
# tiene handlers, asi que sin el la segunda llamada no reinstala el fichero y
# un handler ajeno sobrevive (y sus avisos se siguen yendo a stderr).
LOG_FILE_NAME = 'woptimizer.log'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# El log crecia sin limite (1,8 MB medidos, casi todo de la propia suite). Se
# rota: el destino y el formato no cambian, solo deja de crecer sin control.
LOG_MAX_BYTES = 1_048_576
LOG_BACKUP_COUNT = 3


def setup_logging(level: int = logging.WARNING) -> None:
    """Canaliza los avisos a `woptimizer.log`. Idempotente: se puede llamar
    desde `__main__`, desde la suite y desde quien importe el paquete.

    `force=True` cierra y elimina los handlers previos del root, de modo que
    la segunda llamada no duplica ni deja vivos los de una configuracion
    anterior. Se declara aqui y no en el `__main__` porque `logger` vive aqui
    y porque el contrato de `architecture.md` §5 no puede depender de que se
    importe por un camino concreto.
    """
    handler = RotatingFileHandler(
        os.path.join(_app_dir(), LOG_FILE_NAME),
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8',
    )
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        handlers=[handler],
        force=True,
    )


# Lo importan notification_service.py:21, pack_service.py:8, process_service.py:7
# y ui/app.py:41,90. NO se mueve ni se elimina: es el punto de contrato.
logger = logging.getLogger('woptimizer')

PROCESS_LIST_FILE = os.path.join(_app_dir(), 'saved_processes.json')
# FIX-011 NO se aplica (TASK-028, veto del arquitecto): `PROCESS_LIST_FILE` NO
# esta sin usar. La consumen `test_gaming_session.py:36-50`, `test_harness.py:37`
# y `test_harness_v2.py:64`, los tres protegidos por FIX-014. Se queda.
#
# CORRECCION (TASK-028 iteracion 2, hallazgo D1 del mutation-auditor): este
# comentario decia ademas que `smoke_check.py:23` hacia `assert` sobre el TEXTO
# FUENTE de esta linea, y **eso era falso**. Ese script esta MUERTO: lee
# `process_manager.py`, que no existe, y revienta en su linea 8 con
# `FileNotFoundError` sin llegar nunca a la 23. O sea que el cuarto "consumidor"
# no existe, y la razon que se daba para no borrar la constante era, en una
# cuarta parte, inventada. Los consumidores VIVOS son los tres de arriba, y el
# guardia de verdad es `test_process_list_file_sigue_siendo_un_contrato` en
# `run_tests.py` (afirma que la constante existe, vale lo que debe y la nombran
# los tres), no un script que nadie ejecuta.
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
