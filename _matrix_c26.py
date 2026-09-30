"""Matriz de mutaciones del ciclo 26 (TASK-035 / TASK-036). NO forma parte de la suite.

Es una herramienta de diagnostico, no un test: corre por separado
(`python _matrix_c26.py`) y devuelve 0 aunque haya supervivientes, porque su
salida es el veredicto, no un codigo de salida de CI. Se queda en la raiz, con
prefijo `_` como el resto de utillaje, para que el siguiente que audite pueda
reproducir la tabla de `docs/ai/testing-guide.md` sin reconstruirla.

POR QUE ESTA VERSION (iteracion 4 del ciclo 26)
La version anterior **estaba rota y su tabla no era reproducible**:

* el ancla de M6 (`self._schedule_ui(5000, ...)`) ya no existia porque la
  iteracion 3 extrajo `_reprogramar_autoocultado()` y dejo
  `AUTOOCULTADO_MS` como constante. El script reventaba en la mutacion 5 de 12
  con `AssertionError: no se encontro el ancla`;
* `correr()` lanzaba **2 de las 3 sondas** del ciclo: la tercera puerta
  (`test_el_gestor_de_procesos_tampoco_miente`) no estaba en la matriz;
* varias anclas usaban saltos de linea que no coincidian con el fichero real.

Ademas, una tabla de mutaciones que nadie puede reproducir es peor que no
tenerla: parece cobertura y no lo es. Aqui cada mutacion se ancla al codigo de
HOY, y un ancla que no encuentra el fichero es un ERROR DURO (no una mutacion
saltada en silencio), que es la unica forma de que la tabla no vuelva a caducar
sin que nadie se entere.

Copia el arbol a %TEMP% (sin `.git`), aplica una mutacion cada vez, purga
`__pycache__` y corre las TRES sondas de TASK-035 en un subproceso. Un mutante
vive = la sonda no discrimina. NUNCA se muta el arbol de trabajo: la copia es la
unica que se toca, y el original se restaura con `shutil.rmtree` al terminar.

La salida es ASCII puro a proposito (Trampa #16: la consola de Windows es
cp1252 y un emoji en un `print` lanza `UnicodeEncodeError`).
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

#: Las TRES sondas del ciclo, las tres en cada mutacion. Faltar una es lo que
#: hizo que la version anterior no midiera la tercera puerta.
SONDAS = (
    "test_los_workers_de_pack_solo_publican_por_after",
    "test_el_feedback_de_pack_dice_la_verdad",
    "test_el_gestor_de_procesos_tampoco_miente",
)

# (nombre, fichero, ancla_vieja, ancla_nueva)
MUTACIONES = [
    # ------------------------------------------------------------------
    # TASK-036: el aviso del pack inerte (M-A..M-H, las que exige la decision)
    # ------------------------------------------------------------------
    ("M-A  execute_pack vuelve al return mudo (el silencio)",
     "src/woptimizer/ui/views/dashboard_view.py",
     "            self._show_aviso_banner(*mensaje_banner_sin_apps(pack.name, pack.default_action))",
     "            return  # M-A: silencio"),

    ("M-B  el verbo se cablea a 'apagar' en vez de mapearse",
     "src/woptimizer/ui/feedback.py",
     "no tiene apps que {_verbo(accion)}. ",
     "no tiene apps que apagar. "),

    ("M-C  el aviso del pack vacio se pinta en el color de marca",
     "src/woptimizer/ui/feedback.py",
     "    return _frase_sin_apps(nombre, default_action), theme.WARNING",
     "    return _frase_sin_apps(nombre, default_action), theme.GAMING"),

    ("M-D  la guarda se queda sin sitio (equivale a ir DESPUES de la doble pulsacion)",
     "src/woptimizer/ui/views/dashboard_view.py",
     "        if es_pack_inerte(pack.is_gaming, len(pack.apps), len(pack.target_categories)):\n"
     "            self._show_aviso_banner(*mensaje_banner_gaming_inerte(pack.name))\n"
     "            return\n"
     "        if not pack.is_gaming and not pack.apps:\n"
     "            # El silencio no es la opcion neutra: la pulsacion no dejaba ni\n"
     "            # rastro, y con `default_action=\"start\"` el usuario creia que se\n"
     "            # abrian programas que nunca se abren. Sin hilo, sin `after` y sin\n"
     "            # worker: ya estamos en el hilo principal dentro de un callback.\n"
     "            self._show_aviso_banner(*mensaje_banner_sin_apps(pack.name, pack.default_action))\n"
     "            return\n",
     "        if False:  # M-D: sin guarda\n"
     "            pass\n"),

    ("M-E  se borra el diagnostico del Gaming Mode inerte",
     "src/woptimizer/ui/views/dashboard_view.py",
     "        if es_pack_inerte(pack.is_gaming, len(pack.apps), len(pack.target_categories)):",
     "        if False:  # M-E"),

    ("M-F  es_pack_inerte con 'or' en vez de 'and'",
     "src/woptimizer/ui/feedback.py",
     "    return is_gaming and n_apps == 0 and n_categorias == 0",
     "    return is_gaming and (n_apps == 0 or n_categorias == 0)"),

    ("M-G  el aviso reusa _inline_status (fondo CANCEL y sin auto-ocultado)",
     "src/woptimizer/ui/views/dashboard_view.py",
     "        self._publicar_en_banner(texto, txt_color)\n",
     "        self._inline_status(texto, txt_color)\n"),

    ("M-H  se borra la clausula 'freed_mb <= 0' de clausula_mb",
     "src/woptimizer/ui/feedback.py",
     "    if freed_mb <= 0:\n        return \"\"\n",
     ""),

    # ------------------------------------------------------------------
    # S1: la rama START de execute_pack no se ejecutaba nunca
    # ------------------------------------------------------------------
    ("S1-a  _run_start intercambia launched y failed",
     "src/woptimizer/ui/views/dashboard_view.py",
     "                self.after(0, self._show_start_banner, launched, failed, p.name)",
     "                self.after(0, self._show_start_banner, failed, launched, p.name)"),

    ("S1-b  _run_start arranca start_pack_apps([])",
     "src/woptimizer/ui/views/dashboard_view.py",
     "                launched, failed = self.process_service.start_pack_apps(p.apps)",
     "                launched, failed = self.process_service.start_pack_apps([])"),

    ("S1-c  _run_start publica en _show_banner con el NOMBRE como is_gaming",
     "src/woptimizer/ui/views/dashboard_view.py",
     "                self.after(0, self._show_start_banner, launched, failed, p.name)",
     "                self.after(0, self._show_banner, launched, failed, p.name)"),

    # ------------------------------------------------------------------
    # S2: la guarda AST era una RED, no un muro (se muta el DETECTOR)
    # ------------------------------------------------------------------
    ("S2-a  la guarda vuelve a no bajar por getattr/setattr",
     "run_tests.py",
     "            if (isinstance(call.func, ast.Name) and call.func.id in ACCESOS_DINAMICOS\n"
     "                    and call.args and isinstance(call.args[0], ast.Name)\n"
     "                    and call.args[0].id == \"self\"):\n"
     "                malos.append(\n"
     "                    f\"{etiqueta}:L{call.lineno} {call.func.id}(self, ...) \"\n"
     "                    f\"desde el hilo secundario\"\n"
     "                )\n"
     "                continue\n",
     ""),

    ("S2-b  la guarda vuelve a ignorar ast.Delete",
     "run_tests.py",
     "            elif isinstance(nodo, ast.Delete):\n"
     "                # `del self._last_gaming_summary` es tan destructivo como\n"
     "                # `self._last_gaming_summary = ...`, y la guarda solo miraba\n"
     "                # escrituras: `ast.Delete` no es `ast.Assign`.\n"
     "                objetivos = nodo.targets\n",
     ""),

    ("S2-c  la guarda vuelve a mirar solo `call.func` y no los argumentos",
     "run_tests.py",
     "                    for arg in list(call.args) + [kw.value for kw in call.keywords]:\n"
     "                        a_raiz, a_camino = _raiz_de_self(arg)\n"
     "                        if a_raiz is not None:\n"
     "                            malos.append(\n"
     "                                f\"{etiqueta}:L{call.lineno} pasa \"\n"
     "                                f\"self.{'.'.join(a_camino)} como argumento de \"\n"
     "                                f\"una llamada permitida\"\n"
     "                            )\n",
     ""),

    # ------------------------------------------------------------------
    # S3: el sustantivo solo se probaba en la rama EXITO
    # ------------------------------------------------------------------
    ("S3   el sustantivo se cablea a 'procesos' en la rama 'nada'",
     "src/woptimizer/ui/feedback.py",
     "    return (f\"⚠️ '{nombre}': 0 {sustantivo} cerrados, \"",
     "    return (f\"⚠️ '{nombre}': 0 procesos cerrados, \""),

    # ------------------------------------------------------------------
    # Lo que ya estaba cerrado y se sigue sosteniendo (regresion)
    # ------------------------------------------------------------------
    ("R-1  clasificar_cierre dice siempre EXITO",
     "src/woptimizer/ui/feedback.py",
     "    if killed > 0:\n        return PARCIAL if failed else EXITO\n    return FALLO if failed else NADA",
     "    return EXITO"),

    ("R-2  _show_banner deja de refrescar la barra de reposo",
     "src/woptimizer/ui/views/dashboard_view.py",
     "            self._last_gaming_summary = f\"{killed} cerrados{clausula_mb(freed_mb)}\"\n        self._update_resting_bar()",
     "            self._last_gaming_summary = f\"{killed} cerrados{clausula_mb(freed_mb)}\""),

    ("R-3  se borra la cancelacion del auto-ocultado previo",
     "src/woptimizer/ui/views/dashboard_view.py",
     "        if getattr(self, \"_banner_timer\", None):\n"
     "            try:\n"
     "                self.after_cancel(self._banner_timer)\n"
     "                if hasattr(self, \"_timers_ui\"):\n"
     "                    self._timers_ui.discard(self._banner_timer)\n"
     "            except Exception:\n"
     "                pass\n",
     ""),

    ("R-4  el worker de la portada vuelve a tirar failed/skipped",
     "src/woptimizer/ui/views/dashboard_view.py",
     "                self.after(0, self._show_banner, killed, freed_mb, p.is_gaming, failed, skipped)",
     "                self.after(0, self._show_banner, killed, freed_mb, p.is_gaming)"),

    ("R-5  la guarda AST anulada (return [] siempre)",
     "run_tests.py",
     "        malos = []\n        for call in [n for n in ast.walk(worker) if isinstance(n, ast.Call)]:",
     "        return []\n        malos = []\n        for call in [n for n in ast.walk(worker) if isinstance(n, ast.Call)]:"),
]


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


def _leer(path):
    with io.open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def _escribir(path, texto):
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(texto)


def _normalizar(texto):
    return texto.replace("\r\n", "\n")


def correr():
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    programa = "import run_tests; " + "; ".join(
        "run_tests.{}()".format(s) for s in SONDAS
    )
    p = subprocess.run(
        [sys.executable, "-c", programa],
        cwd=DESTINO, env=env, capture_output=True, text=True, encoding="utf-8",
        timeout=300)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def _ascii(texto, limite=110):
    limpio = "".join(c if 32 <= ord(c) < 127 else "?" for c in texto)
    return limpio[:limite]


def primera_linea_util(salida):
    """La asercion que muere, en una linea y en ASCII.

    Se busca el `AssertionError:` con su mensaje (que es lo que dice QUE se
    rompio) y, si no hay ninguno, la ultima linea con "Error". Un mutante puede
    morir por un crash en vez de por una asercion: eso tambien se imprime, pero
    se distingue, porque un crash no es una prueba.
    """
    lineas = salida.splitlines()
    for i, linea in enumerate(lineas):
        t = linea.strip()
        if t.startswith("AssertionError") and ":" in t:
            return _ascii(t.split(":", 1)[1].strip() or t)
    for linea in lineas:
        t = linea.strip()
        if t.startswith("AssertionError") or t.startswith("Traceback") or "Error" in t:
            return _ascii(t)
    if salida.strip():
        return _ascii(salida.strip().splitlines()[-1])
    return "(sin salida)"


try:
    copiar()
    purgar()
    rc, salida = correr()
    print("CONTROL (sin mutar): rc={} -> {}".format(rc, "VERDE" if rc == 0 else "ROJO"))
    if rc != 0:
        print(_ascii(salida[-2500:]))
        sys.exit(1)

    supervivientes = []
    for nombre, fichero, viejo, nuevo in MUTACIONES:
        path = ruta(fichero)
        original = _leer(path)
        nl = "\r\n" if "\r\n" in original else "\n"
        plano = _normalizar(original)
        # ERROR DURO, no "mutacion saltada": un ancla caducada es una tabla que
        # ya no mide lo que dice medir.
        assert viejo in plano, (
            "no se encontro el ancla de {}: {!r}".format(nombre, viejo[:70]))
        _escribir(path, plano.replace(viejo, nuevo).replace("\n", nl))
        purgar()
        rc, salida = correr()
        veredicto = "MUERE" if rc != 0 else "VIVE"
        if rc == 0:
            supervivientes.append(nombre)
        print("{:62s} {}  | {}".format(nombre, veredicto, primera_linea_util(salida)))
        _escribir(path, original)
        purgar()

    print("")
    print("supervivientes:", supervivientes if supervivientes else "ninguno")
finally:
    shutil.rmtree(DESTINO, ignore_errors=True)
