"""Matriz de mutacion de TASK-027 iteracion 3: UNA SUBPROCESS POR SONDA.

Igual que la iteracion 2 (`_mutmatrix_t027_iter2.py`, que se conserva intacta
porque su 21/21 lo reprodujo el `mutation-auditor`): cada fila copia el arbol
minimo a un temporal, aplica la mutacion al CODIGO DE PRODUCCION (no a la
sonda) y lanza la sonda sola en un subproceso. "SUPERVIVIENTE" es un test que
paso con el defecto dentro, que es justo lo que el mutation-auditor rechaza.

Lo nuevo de esta iteracion son las filas `H*`: la regla 9 (`_es_imagen_pe`),
que es la que cierra el hard link Y su hermano trivial (la copia plena). Las
filas H1-H3 tienen que morir en `test_un_hard_link_no_es_una_hoja_y_el_script_
no_pasa`, y H4-H6 son CRUCES INFORMATIVOS:(header) las sondas de las iteraciones
anteriores, que no declaran esa propiedad.

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

PS = "src/woptimizer/services/process_service.py"

# (etiqueta, fichero, viejo, nuevo)
MUTACIONES = {
    # --- ITERACION 3: la regla 9, el contenido ------------------------------
    # H1: borrar la regla entera. Es la mutacion "el arreglo no esta".
    "H1-borrar-la-regla-9": (
        PS,
        """            if not _es_imagen_pe(real):
                motivo = (f"el fichero no es una imagen PE (no lleva MZ/PE), o sea "
                          f"no es un programa sino un script renombrado: "
                          f"{normalizada} -> {real}")
                continue
""",
        "",
    ),
    # H2: la regla existe pero no hace nada (el "arreglo" decorativo).
    "H2-es-imagen-pe-siempre-True": (
        PS,
        """            if not _es_imagen_pe(real):""",
        """            if False and not _es_imagen_pe(real):""",
    ),
    # H3: mira solo `MZ` y no llega a la firma `PE\\0\\0`. Mata en el caso (4).
    "H3-solo-la-cabecera-MZ": (
        PS,
        """            fh.seek(offset)
            return fh.read(4) == _PE_SIGNATURE""",
        """            fh.seek(offset)
            return True""",
    ),
    # H4: fail-OPEN: si no se puede leer, se acepta.
    "H4-fail-open-al-no-leer": (
        PS,
        """    except OSError:
        # Un fichero que no se puede abrir no es una imagen PE demostrable, y
        # fail-closed significa no arrancar.
        return False""",
        """    except OSError:
        return True""",
    ),
    # H5: la "solucion" que el hallazgo pedia y que la medicion REFUTA:
    # rechazar cualquier st_nlink > 1. Mata en el control (6) de la sonda.
    "H5-rechazar-cualquier-st-nlink-mayor-que-1": (
        PS,
        """            if not _es_imagen_pe(real):""",
        """            if os.stat(real, follow_symlinks=False).st_nlink > 1:
                motivo = "tiene mas de un enlace duro"
                continue
            if not _es_imagen_pe(real):""",
    ),
    # H6 NO EXISTE, y por que: la otra variante que se ofrecio ("rechazar solo
    # si el destino no esta en las raices") no se puede escribir en el producto.
    # Un hard link no tiene destino consultable: no hay API en Windows que
    # devuelva los otros nombres de un fichero a partir de su ruta, asi que
    # "comprobar el destino" no es implementable. Ademas, de ser
    # implementable, seria irrelevante: el atacante elige que nombre queda
    # dentro de la raiz. Por eso la fila que se prueba es H5, no H6.
}

# (mutacion, sonda, debe_morir, por_que)
FILAS = [
    # --- TIENEN QUE MORIR: la sonda declara la regla 9 ----------------------
    ("H1-borrar-la-regla-9",
     "test_un_hard_link_no_es_una_hoja_y_el_script_no_pasa", True, ""),
    ("H2-es-imagen-pe-siempre-True",
     "test_un_hard_link_no_es_una_hoja_y_el_script_no_pasa", True, ""),
    ("H3-solo-la-cabecera-MZ",
     "test_un_hard_link_no_es_una_hoja_y_el_script_no_pasa", True, ""),
    ("H4-fail-open-al-no-leer",
     "test_un_hard_link_no_es_una_hoja_y_el_script_no_pasa", True, ""),
    ("H5-rechazar-cualquier-st-nlink-mayor-que-1",
     "test_un_hard_link_no_es_una_hoja_y_el_script_no_pasa", True, ""),
    # --- CRUCES INFORMATIVOS: sondas de iteraciones anteriores -------------
    # Estas sondas NO declaran la regla 9, asi que no tienen por que morir. Se
    # anotan para que el numero de la matriz signifique algo: si una de ellas
    # muere, es porque la regla 9 se ha colado en una propiedad que ya tenia
    # dueña, y eso tambien habria que mirarlo.
    ("H1-borrar-la-regla-9", "test_un_junction_no_puede_colar_lo_que_hay_detras",
     False, "propiedad del junction, no del contenido"),
    ("H1-borrar-la-regla-9", "test_arranque_de_apps_no_usa_shell",
     False, "propiedad del arranque sin interprete"),
    ("H1-borrar-la-regla-9", "test_la_contencion_no_acepta_un_hermano_de_prefijo",
     False, "propiedad de la contencion por componentes (M10)"),
    ("H1-borrar-la-regla-9", "test_la_contencion_no_depende_de_la_caja",
     False, "propiedad de la caja"),
    ("H1-borrar-la-regla-9", "test_la_guarda_de_shell_true_ve_atributos_y_aliases",
     False, "propiedad de la guarda anti-shell"),
    ("H2-es-imagen-pe-siempre-True", "test_arranque_de_apps_no_usa_shell",
     False, "su propia sonda de runtime (_PopenProhibido) la sostiene"),
    ("H5-rechazar-cualquier-st-nlink-mayor-que-1",
     "test_un_junction_no_puede_colar_lo_que_hay_detras", False,
     "los fixtures de esa sonda tienen st_nlink==1"),
]

CODIGO = ("import sys; sys.path.insert(0, '.');"
          "import run_tests as t; getattr(t, {test!r})()")


def preparar(mutacion, destino):
    # Los .pyc del arbol de trabajo son placeholders del VFS de Nextcloud y no
    # se pueden leer, asi que la copia los excluye.
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
    destino = tempfile.mkdtemp(prefix="wopt_mut3_")
    try:
        preparar(mutacion, destino)
        proc = subprocess.run(
            [sys.executable, "-u", "-c", CODIGO.format(test=test)],
            cwd=destino, capture_output=True, text=True, timeout=300)
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
    print(f"{'MUTACION':<44} {'SONDA':<52} VEREDICTO")
    print("-" * 156)
    deben = [f for f in FILAS if f[2]]
    informativas = [f for f in FILAS if not f[2]]
    supervivientes = []
    for mutacion, test, _debe, _por_que in deben:
        veredicto = ejecutar(mutacion, test)
        print(f"{mutacion:<44} {test:<52} {veredicto}")
        if veredicto.startswith("SUPERVIVIENTE") or veredicto == "TIMEOUT":
            supervivientes.append((mutacion, test))
    print("-" * 156)
    print(f"{len(deben) - len(supervivientes)}/{len(deben)} mutaciones muertas "
          f"por la asercion que las nombra. Supervivientes: {len(supervivientes)}")

    print()
    print("=== CRUCES INFORMATIVOS (esta sonda NO declara esa propiedad) ===")
    print(f"{'MUTACION':<44} {'SONDA':<52} VEREDICTO  POR QUE NO ES UN AGUJO")
    print("-" * 156)
    for mutacion, test, _debe, por_que in informativas:
        veredicto = ejecutar(mutacion, test)
        print(f"{mutacion:<44} {test:<52} {veredicto:<14} {por_que[:46]}")
    print("-" * 156)
    if supervivientes:
        print("ATENCION: hay supervivientes en las filas que TIENEN que morir.")
        for m, t in supervivientes:
            print(f"  - {m} sobrevive a {t}")
    else:
        print("Ninguna mutacion sobrevive a la sonda que declara su propiedad.")


if __name__ == "__main__":
    main()
