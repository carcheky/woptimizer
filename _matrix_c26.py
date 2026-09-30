"""Matriz de mutaciones del ciclo 26 (S1-S5, S9). NO forma parte de la suite.

Es una herramienta de diagnostico, no un test: corre por separado
(`python _matrix_c26.py`) y devuelve 0 aunque haya supervivientes, porque su
salida es el veredicto, no un codigo de salida de CI. Se queda en la raiz,
con prefijo `_` como el resto de utillaje, para que el siguiente que audite
pueda reproducir la tabla de `docs/ai/testing-guide.md` sin reconstruirla.

Copia el arbol a %TEMP% (sin `.git`), aplica una mutacion cada vez, purga
`__pycache__` y corre las sondas de TASK-035 en un subproceso. Un mutante
vive = la sonda no discrimina.
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile

ORIGEN = os.path.abspath(".")
DESTINO = os.path.join(tempfile.gettempdir(), "wopt_mut_c26")
RAIZ = "src/woptimizer"

MUTACIONES = [
    ("M1  kill_pack: color siempre VERDE",
     "src/woptimizer/ui/views/pack_manager_view.py",
     "            texto, color = mensaje_cierre_pack(nombre, killed, failed, skipped, freed_mb)",
     "            texto, color = mensaje_cierre_pack(nombre, killed, failed, skipped, freed_mb)\n            color = VERDE"),
    ("M3  kill_pack: vuelve al mensaje incondicional en VERDE",
     "src/woptimizer/ui/views/pack_manager_view.py",
     "            texto, color = mensaje_cierre_pack(nombre, killed, failed, skipped, freed_mb)\n            self.after(0, self._inline_status, texto, color)",
     "            self.after(0, self._inline_status, f\"\\u2705 {killed} procesos cerrados ({freed_mb:.1f} MB liberados) \\u00b7 '{nombre}'.\", VERDE)"),
    ("M4  _show_start_banner sin refrescar la barra de reposo",
     "src/woptimizer/ui/views/dashboard_view.py",
     "        self.process_service.invalidate_cache()\n        self._update_resting_bar()",
     "        self.process_service.invalidate_cache()"),
    ("M5  sin cancelar el temporizador previo del banner",
     "src/woptimizer/ui/views/dashboard_view.py",
     "        if getattr(self, \"_banner_timer\", None):\n            try:\n                self.after_cancel(self._banner_timer)\n                if hasattr(self, \"_timers_ui\"):\n                    self._timers_ui.discard(self._banner_timer)\n            except Exception:\n                pass\n", ""),
    ("M6  auto-ocultado a 60 s en vez de 5 s",
     "src/woptimizer/ui/views/dashboard_view.py",
     "self._schedule_ui(5000, self._hide_banner)",
     "self._schedule_ui(60000, self._hide_banner)"),
    ("M7  el worker de kill_pack toca el widget directamente",
     "src/woptimizer/ui/views/pack_manager_view.py",
     "            texto, color = mensaje_cierre_pack(nombre, killed, failed, skipped, freed_mb)",
     "            self.status_label.configure(text=\"x\")\n            texto, color = mensaje_cierre_pack(nombre, killed, failed, skipped, freed_mb)"),
    ("M8  self.master.after en UNA rama del worker de arranque",
     "src/woptimizer/ui/views/dashboard_view.py",
     "                self.after(0, self._show_start_banner, launched, failed, p.name)",
     "                self.master.after(0, self._show_start_banner, launched, failed, p.name)"),
    ("M9  la portada vuelve a tirar failed/skipped",
     "src/woptimizer/ui/views/dashboard_view.py",
     "                self.after(0, self._show_banner, killed, freed_mb, p.is_gaming, failed, skipped)",
     "                self.after(0, self._show_banner, killed, freed_mb, p.is_gaming)"),
    ("M10 clasificar_cierre dice siempre EXITO",
     "src/woptimizer/ui/feedback.py",
     "    if killed > 0:\n        return PARCIAL if failed else EXITO\n    return FALLO if failed else NADA",
     "    return EXITO"),
    ("M13 kill_pack vuelve a tirar failed/skipped en el mensaje",
     "src/woptimizer/ui/feedback.py",
     "def mensaje_cierre_pack(nombre: str, killed: int, failed: int,\n                        skipped: int, freed_mb: float) -> Tuple[str, str]:",
     "def mensaje_cierre_pack(nombre: str, killed: int, failed: int,\n                        skipped: int, freed_mb: float) -> Tuple[str, str]:\n    killed, failed, skipped, freed_mb = (killed, 0, 0, freed_mb)"),
    ("M11 la guarda ast anulada (return [] siempre)",
     "run_tests.py",
     "        malos = []\n        for call in [n for n in ast.walk(worker) if isinstance(n, ast.Call)]:",
     "        return []\n        malos = []\n        for call in [n for n in ast.walk(worker) if isinstance(n, ast.Call)]:"),
    ("M12 la guarda ast mira solo el PRIMERO de los self.after",
     "run_tests.py",
     "        return malos\n\n    # Control 1:",
     "        return []\n\n    # Control 1:"),
]

MUTACIONES = [m for m in MUTACIONES if m[1] != "ui/views/pack_manager.py"]


def copiar():
    if os.path.exists(DESTINO):
        shutil.rmtree(DESTINO, ignore_errors=True)
    ignorado = shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "dist", "build")
    shutil.copytree(ORIGEN, DESTINO, ignore=ignorado)


def ruta(relative):
    return os.path.join(DESTINO, relative)


def purgar():
    for base, dirs, files in os.walk(DESTINO):
        for d in list(dirs):
            if d == "__pycache__":
                shutil.rmtree(os.path.join(base, d), ignore_errors=True)
                dirs.remove(d)


def correr():
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    p = subprocess.run(
        [sys.executable, "-c",
         "import run_tests; run_tests.test_los_workers_de_pack_solo_publican_por_after(); "
         "run_tests.test_el_feedback_de_pack_dice_la_verdad()"],
        cwd=DESTINO, env=env, capture_output=True, text=True, encoding="utf-8",
        timeout=300)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def primera_linea_util(salida):
    for linea in salida.splitlines():
        t = linea.strip()
        if t.startswith("AssertionError") or t.startswith("Traceback") or "Error" in t:
            return t[:150]
    return salida.strip().splitlines()[-1][:150] if salida.strip() else "(sin salida)"


copiar()
purgar()
rc, salida = correr()
print("CONTROL (sin mutar): rc={} -> {}".format(rc, "VERDE" if rc == 0 else "ROJO"))
if rc != 0:
    print(salida[-2000:])
    sys.exit(1)

supervivientes = []
for nombre, fichero, viejo, nuevo in MUTACIONES:
    with io.open(ruta(fichero), "r", encoding="utf-8") as fh:
        original = fh.read()
    assert viejo in original, "no se encontro el ancla de {}: {!r}".format(nombre, viejo[:70])
    mutado = original.replace(viejo, nuevo)
    with io.open(ruta(fichero), "w", encoding="utf-8", newline="") as fh:
        fh.write(mutado)
    purgar()
    rc, salida = correr()
    veredicto = "MUERE" if rc != 0 else "VIVE"
    if rc == 0:
        supervivientes.append(nombre)
    print("{:52s} {}".format(nombre, veredicto + "  | " + primera_linea_util(salida)))
    with io.open(ruta(fichero), "w", encoding="utf-8", newline="") as fh:
        fh.write(original)
    purgar()

print("")
print("supervivientes:", supervivientes if supervivientes else "ninguno")
