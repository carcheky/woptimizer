"""Matriz de mutacion de TASK-027 iteracion 2: UNA SUBPROCESS POR SONDA.

Cada fila copia el arbol minimo a un directorio temporal, aplica la mutacion
al CODIGO DE PRODUCCION (no a la sonda), y lanza la sonda sola en un
subproceso. "SUPERVIVIENTE" significa que el test paso con el defecto dentro,
que es exactamente lo que el mutation-auditor rechaza.

Fichero temporal de trabajo: se borra al terminar el pase.
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# (etiqueta, fichero, viejo, nuevo)
MUTACIONES = {
    # --- ALTA: la resolucion real -------------------------------------------
    "A1-borrar-la-resolucion-real": (
        "src/woptimizer/services/process_service.py",
        """            if not os.path.isfile(normalizada):
                continue
            real = _ruta_real(normalizada)""",
        """            if not os.path.isfile(normalizada):
                continue
            real = normalizada
            if True:
                return real
            real = _ruta_real(normalizada)""",
    ),
    "A2-contencion-real-siempre-True": (
        "src/woptimizer/services/process_service.py",
        "            if not _dentro_de_alguna(real, raices_reales):",
        "            if False:",
    ),
    "A3-extension-solo-en-el-alias": (
        "src/woptimizer/services/process_service.py",
        """            ext_real = os.path.splitext(real)[1].lower()
            if ext_real not in _ALLOWED_APP_EXTS:""",
        """            ext_real = os.path.splitext(real)[1].lower()
            if False:""",
    ),
    "A4-realpath-sin-strict": (
        "src/woptimizer/services/process_service.py",
        "        real = os.path.realpath(ruta, strict=True)",
        "        real = os.path.realpath(ruta)",
    ),
    "A5-rechazar-todo-reparse-point": (
        "src/woptimizer/services/process_service.py",
        "            if not _dentro_de_alguna(real, raices_reales):",
        "            if real != normalizada:",
    ),
    "A6-devolver-la-ruta-lexica": (
        "src/woptimizer/services/process_service.py",
        "            return real\n\n        logger.warning",
        "            return normalizada\n\n        logger.warning",
    ),
    "A7-fail-open-al-no-resolver": (
        "src/woptimizer/services/process_service.py",
        """    try:
        real = os.path.realpath(ruta, strict=True)
    except (OSError, ValueError):
        # ValueError: rutas con NUL incrustado en algunas versiones.
        return None""",
        """    try:
        real = os.path.realpath(ruta, strict=True)
    except (OSError, ValueError):
        return ruta""",
    ),
    "A8-raices-lexicas-comparadas-contra-la-real": (
        "src/woptimizer/services/process_service.py",
        "        raices_reales = [r for r in (_ruta_real(raiz) for raiz in raices_norm) if r]",
        "        raices_reales = list(raices_norm)",
    ),
    "A9-sin-motivo-en-el-log": (
        "src/woptimizer/services/process_service.py",
        'f"(junction/symlink): {normalizada} -> {real}")',
        'f"(motivo): {normalizada} -> {real}")',
    ),
    "A10-comparar-la-lexica-contra-las-raices-reales": (
        "src/woptimizer/services/process_service.py",
        "            if not _dentro_de_alguna(real, raices_reales):",
        "            if not _dentro_de_alguna(normalizada, raices_reales):",
    ),
    # --- MEDIA M10: contencion por prefijo -----------------------------------
    "M10-startswith-en-vez-de-commonpath": (
        "src/woptimizer/services/process_service.py",
        """            comun = os.path.commonpath([una, raiz])
        except ValueError:
            continue
        if os.path.normcase(comun) == os.path.normcase(raiz):""",
        """            comun = os.path.commonpath([una, raiz])
        except ValueError:
            continue
        if os.path.normcase(una).startswith(os.path.normcase(raiz)):""",
    ),
    # --- MEDIA: caja de las letras -------------------------------------------
    "C1-sin-normcase": (
        "src/woptimizer/services/process_service.py",
        "        if os.path.normcase(comun) == os.path.normcase(raiz):",
        "        if comun == raiz:",
    ),
    "C2-normcase-solo-en-la-comun": (
        "src/woptimizer/services/process_service.py",
        "        if os.path.normcase(comun) == os.path.normcase(raiz):",
        "        if os.path.normcase(comun) == raiz:",
    ),
    "C3-normcase-solo-en-la-raiz": (
        "src/woptimizer/services/process_service.py",
        "        if os.path.normcase(comun) == os.path.normcase(raiz):",
        "        if comun == os.path.normcase(raiz):",
    ),
    # --- MEDIA: guarda anti-shell ---------------------------------------------
    "G1-guarda-sin-ast-Attribute": (
        "run_tests.py",
        """        elif isinstance(func, ast.Attribute):
            nombre = func.attr
        else:
            continue""",
        """        else:
            continue""",
    ),
    "G2-guarda-sin-mapa-de-alias": (
        "run_tests.py",
        """    nombres = {"Popen"}
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ImportFrom) and nodo.module == "subprocess":
            for alias in nodo.names:
                if alias.name == "Popen":
                    nombres.add(alias.asname or alias.name)""",
        """    nombres = {"Popen"}""",
    ),
    "G3-guarda-solo-is-True": (
        "run_tests.py",
        "            if isinstance(kw.value, ast.Constant) and kw.value.value in (False, 0, None):",
        "            if isinstance(kw.value, ast.Constant) and kw.value.value is True:",
    ),
    "G4-guarda-marca-todo-lo-que-diga-shell": (
        "run_tests.py",
        "            if isinstance(kw.value, ast.Constant) and kw.value.value in (False, 0, None):",
        "            if False:",
    ),
    # --- reintroducir el bug original en el PRODUCTO ------------------------
    "P1-Popen-shell-True-de-vuelta": (
        "src/woptimizer/services/process_service.py",
        "        startfile(ruta)",
        "        import subprocess\n        subprocess.Popen(ruta, shell=True)",
    ),
    "P2-Popen-shell-True-con-alias": (
        "src/woptimizer/services/process_service.py",
        "        startfile(ruta)",
        "        import subprocess as sp\n        sp.Popen(ruta, shell=True)",
    ),
}

# (mutacion, test, DEBE_MORIR, POR_QUE_SI_NO_ES_UN_AGUJO)
# La regla: una mutacion tiene que morir en la sonda que DECLARA vigilar esa
# propiedad. Cruzarla con otra sonda que no la declara no encuentra un agujero,
# y si lo encuentra, casi siempre es que la otra sonda afirma algo distinto.
FILAS = [
    # --- ALTA: resolucion real (junction/symlink) ---------------------------
    ("A1-borrar-la-resolucion-real", "test_un_junction_no_puede_colar_lo_que_hay_detras", True, ""),
    ("A2-contencion-real-siempre-True", "test_un_junction_no_puede_colar_lo_que_hay_detras", True, ""),
    ("A3-extension-solo-en-el-alias", "test_un_junction_no_puede_colar_lo_que_hay_detras", True, ""),
    ("A4-realpath-sin-strict", "test_un_junction_no_puede_colar_lo_que_hay_detras", True, ""),
    ("A5-rechazar-todo-reparse-point", "test_un_junction_no_puede_colar_lo_que_hay_detras", True, ""),
    ("A6-devolver-la-ruta-lexica", "test_un_junction_no_puede_colar_lo_que_hay_detras", True, ""),
    ("A7-fail-open-al-no-resolver", "test_un_junction_no_puede_colar_lo_que_hay_detras", True, ""),
    ("A8-raices-lexicas-comparadas-contra-la-real", "test_un_junction_no_puede_colar_lo_que_hay_detras", True, ""),
    ("A9-sin-motivo-en-el-log", "test_un_junction_no_puede_colar_lo_que_hay_detras", True, ""),
    ("A10-comparar-la-lexica-contra-las-raices-reales", "test_un_junction_no_puede_colar_lo_que_hay_detras", True, ""),
    ("A1-borrar-la-resolucion-real", "test_la_contencion_no_acepta_un_hermano_de_prefijo", False,
     "esta sonda declara la contencion POR COMPONENTES; borrar la resolucion real no la afecta"),
    ("M10-startswith-en-vez-de-commonpath", "test_un_junction_no_puede_colar_lo_que_hay_detras", False,
     "el junction sigue rechazado: la contencion REAL se sigue aplicando (por prefijo), y esta sonda no construye un hermano"),
    # --- MEDIA M10: contencion por prefijo -----------------------------------
    ("M10-startswith-en-vez-de-commonpath", "test_la_contencion_no_acepta_un_hermano_de_prefijo", True, ""),
    ("M10-startswith-en-vez-de-commonpath", "test_la_contencion_no_depende_de_la_caja", False,
     "muerre igualmente, pero por el caso (x86) y no por el hermano de prefijo"),
    # --- MEDIA: caja de las letras -------------------------------------------
    ("C1-sin-normcase", "test_la_contencion_no_depende_de_la_caja", True, ""),
    ("C2-normcase-solo-en-la-comun", "test_la_contencion_no_depende_de_la_caja", True, ""),
    ("C3-normcase-solo-en-la-raiz", "test_la_contencion_no_depende_de_la_caja", True, ""),
    # --- MEDIA: guarda anti-shell ---------------------------------------------
    ("G1-guarda-sin-ast-Attribute", "test_la_guarda_de_shell_true_ve_atributos_y_aliases", True, ""),
    ("G2-guarda-sin-mapa-de-alias", "test_la_guarda_de_shell_true_ve_atributos_y_aliases", True, ""),
    ("G3-guarda-solo-is-True", "test_la_guarda_de_shell_true_ve_atributos_y_aliases", True, ""),
    ("G4-guarda-marca-todo-lo-que-diga-shell", "test_la_guarda_de_shell_true_ve_atributos_y_aliases", True, ""),
    ("G1-guarda-sin-ast-Attribute", "test_arranque_de_apps_no_usa_shell", False,
     "su propia sonda de RUNTIME (_PopenProhibido) sigue matando el bug de todas formas (ver fila P1)"),
    # --- reintroducir el bug original en el PRODUCTO ------------------------
    ("P1-Popen-shell-True-de-vuelta", "test_la_guarda_de_shell_true_ve_atributos_y_aliases", True, ""),
    ("P1-Popen-shell-True-de-vuelta", "test_arranque_de_apps_no_usa_shell", True, ""),
    ("P2-Popen-shell-True-con-alias", "test_la_guarda_de_shell_true_ve_atributos_y_aliases", True, ""),
]

CODIGO = ("import sys; sys.path.insert(0, '.');"
          "import run_tests as t; getattr(t, {test!r})()")


def preparar(mutacion, destino):
    # Los .pyc del arbol de trabajo son placeholders del VFS de Nextcloud y no
    # se pueden leer ("WinError -2145452027"), asi que el copia los excluye.
    shutil.copytree(os.path.join(RAIZ, "src"), os.path.join(destino, "src"),
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(os.path.join(RAIZ, "run_tests.py"),
                 os.path.join(destino, "run_tests.py"))
    fichero, viejo, nuevo = MUTACIONES[mutacion]
    ruta = os.path.join(destino, fichero)
    with open(ruta, encoding="utf-8") as fh:
        fuente = fh.read()
    if fuente.count(viejo) != 1:
        raise SystemExit(f"{mutacion}: el ancla aparece {fuente.count(viejo)} veces")
    with open(ruta, "w", encoding="utf-8") as fh:
        fh.write(fuente.replace(viejo, nuevo))


def ejecutar(mutacion, test):
    """Copia, muta el PRODUCTO, y lanza la sonda sola en un subproceso."""
    destino = tempfile.mkdtemp(prefix="wopt_mut_")
    try:
        preparar(mutacion, destino)
        proc = subprocess.run(
            [sys.executable, "-u", "-c", CODIGO.format(test=test)],
            cwd=destino, capture_output=True, text=True, timeout=180)
        if proc.returncode == 0:
            return "SUPERVIVIENTE  <<<<<<"
        ultima = [l for l in proc.stderr.strip().splitlines() if l.strip()]
        asercion = ""
        for linea in ultima:
            if linea.startswith("AssertionError") or "Error:" in linea:
                asercion = linea.split("AssertionError:")[-1].strip()[:70]
                break
        return f"muerta ({asercion or (ultima[-1] if ultima else '?')[:70]})"
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    finally:
        shutil.rmtree(destino, ignore_errors=True)


def main():
    print("=== FILAS QUE TIENEN QUE MORIR (la sonda DECLARA esa propiedad) ===")
    print(f"{'MUTACION':<48} {'SONDA':<46} VEREDICTO")
    print("-" * 150)
    deben = [f for f in FILAS if f[2]]
    informativas = [f for f in FILAS if not f[2]]
    supervivientes = []
    for mutacion, test, _debe, _por_que in deben:
        veredicto = ejecutar(mutacion, test)
        print(f"{mutacion:<48} {test:<46} {veredicto}")
        if veredicto.startswith("SUPERVIVIENTE") or veredicto == "TIMEOUT":
            supervivientes.append((mutacion, test))
    print("-" * 150)
    print(f"{len(deben) - len(supervivientes)}/{len(deben)} mutaciones muertas "
          f"por la asercion que las nombra. Supervivientes: {len(supervivientes)}")

    print()
    print("=== CRUCES INFORMATIVOS (esta sonda NO declara esa propiedad) ===")
    print(f"{'MUTACION':<48} {'SONDA':<46} VEREDICTO  POR QUE NO ES UN AGUJO")
    print("-" * 150)
    for mutacion, test, _debe, por_que in informativas:
        veredicto = ejecutar(mutacion, test)
        print(f"{mutacion:<48} {test:<46} {veredicto:<12} {por_que[:60]}")
    print("-" * 150)
    if supervivientes:
        print("ATENCION: hay supervivientes en las filas que TIENEN que morir.")
        for m, t in supervivientes:
            print(f"  - {m} sobrevive a {t}")
    else:
        print("Ninguna mutacion sobrevive a la sonda que declara su propiedad.")


if __name__ == "__main__":
    main()
