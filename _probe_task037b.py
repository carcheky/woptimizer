"""Sonda: que hace el guard con cada forma de IMPORTAR `feedback` y de
ESCRIBIR el segundo argumento. El doc va a afirmar esto, asi que se mide."""
import ast
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_tests import (  # noqa: E402
    _guardar_contrato_de_llamantes,
    _modulos_que_importan_feedback,
)

ACCIONES = {"start", "kill"}

FORMAS = {
    "A ImportFrom modulo (forma 1)": (
        "from woptimizer.ui.feedback import mensaje_sin_apps",
        'mensaje_sin_apps(n, "encender")',
    ),
    "B ImportFrom alias (forma 2)": (
        "from woptimizer.ui import feedback as fb",
        'fb.mensaje_sin_apps(n, "encender")',
    ),
    "C Import cualificado (forma 3)": (
        "import woptimizer.ui.feedback as fb",
        'fb.mensaje_sin_apps(n, "encender")',
    ),
    "D relativo from .feedback": (
        "from .feedback import mensaje_sin_apps",
        'mensaje_sin_apps(n, "encender")',
    ),
    "E relativo from ..ui import feedback as fb": (
        "from ..ui import feedback as fb",
        'fb.mensaje_sin_apps(n, "encender")',
    ),
    "F import sin alias, llamada cualificada": (
        "import woptimizer.ui.feedback",
        'woptimizer.ui.feedback.mensaje_sin_apps(n, "encender")',
    ),
    "G dos niveles de atributo": (
        "import woptimizer.ui.feedback as fb",
        'fb.sub.mensaje_sin_apps(n, "encender")',
    ),
    "H alias de MODULO (fb2 = fb)": (
        "import woptimizer.ui.feedback as fb",
        'fb2 = fb\n    fb2.mensaje_sin_apps(n, "encender")',
    ),
    "I alias de ACCION (p = pack.default_action)": (
        "from woptimizer.ui.feedback import mensaje_sin_apps",
        'p = pack.default_action\n    mensaje_sin_apps(n, p)',
    ),
    "J palabra clave accion=...": (
        "from woptimizer.ui.feedback import mensaje_sin_apps",
        'mensaje_sin_apps(n, accion="iniciar")',
    ),
    "K ACCION literal valida (control negativo)": (
        "from woptimizer.ui.feedback import mensaje_sin_apps",
        'mensaje_sin_apps(n, "start")',
    ),
    "L pack.default_action (control negativo)": (
        "from woptimizer.ui.feedback import mensaje_sin_apps",
        "mensaje_sin_apps(n, pack.default_action)",
    ),
    "M import que NO es feedback": ("import os", "os.getcwd()"),
}

print("forma                                         en_alcance  veredicto")
for nombre, (import_line, cuerpo) in FORMAS.items():
    d = tempfile.mkdtemp(prefix="probe_forma_")
    with open(os.path.join(d, "mod.py"), "w", encoding="utf-8", newline="") as fh:
        fh.write(import_line + "\n\n\ndef _f(n, pack):\n    " + cuerpo + "\n")
    alcance = _modulos_que_importan_feedback(d)
    try:
        _guardar_contrato_de_llamantes(d, ACCIONES)
        veredicto = "no protesta"
    except AssertionError as exc:
        primera = str(exc).split(". ")[-1]
        veredicto = "PROTESTA: " + primera[:58]
    print(f"{nombre:46s} {str(bool(alcance)):11s} {veredicto}")
