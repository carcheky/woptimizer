"""Puerta de sintaxis estatica de `src/woptimizer/` -- con el alcance DERIVADO.

TASK-081 (ciclo 67). MEDIDO antes del arreglo: este script enumeraba DIEZ
rutas escritas a mano (las de `verify_ui_syntax.py:9-20` de entonces) mientras
que el arbol tenia mas, y las que faltaban eran `ui/theme.py` y
`ui/tray_menu.py`. MEDIDO en camara desechable, con control positivo:
`theme.py` roto -> exit 0 (VERDE), `tray_menu.py` roto -> exit 0 (VERDE),
`app.py` (si listado) roto -> exit 1, y un modulo NUEVO roto -> exit 0
(VERDE). El guard discriminaba sobre su lista y no veia nada fuera de ella.

LA REGLA (R1/R2): el sujeto se DERIVA con `rglob("*.py")` sobre
`src/woptimizer/`, sin lista y sin lista de exentos. La lista y el conjunto
son dos fuentes de verdad que nadie ata: la lista se caduca el dia que se
anade un modulo, y el agujero ya se documento en
`openspec/changes/2026-09-29-double-tap-confirmation/proposal.md` §9.7 y se
"arreglo" ANADIENDO `confirmation.py` a la lista, que es el arreglo que
degrada el guard.

El derivado cubre tambien los `__init__.py` y cualquier subdirectorio: no
hay nada que excepcionar y, por tanto, no hay excepcion que envejecer. La
cifra que sale por pantalla es la que ha derivado (`ALCANCE_DERIVADO=N`), no
una constante: `STATUS.md` la declara y `test_el_recuento_de_modulos_de_
sintaxis_es_derivado` la compara con lo que este script IMPRIME.

No se tocan `src/woptimizer/**` ni el arbol real: el script solo LEE.
"""

import ast
import io
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
SRC = RAIZ / "src" / "woptimizer"

# El orden de `print` con acentos en una consola Windows cp1252 revienta si no
# se fija la codificacion; en CI el runner tambien es Windows.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def modulos_del_arbol():
    """`[Path]`: los `.py` de `src/woptimizer/`, DERIVADOS del sistema de ficheros.

    Este es EL sujeto del guard. No hay lista, ni de inclusos ni de exentos:
    la funcion que decide que se mira es la que recorre el arbol.
    """
    return sorted(SRC.rglob("*.py"))


def main():
    ficheros = modulos_del_arbol()
    print("Validando sintaxis estatica de src/woptimizer/ (alcance DERIVADO)...")
    errores = 0
    for ruta in ficheros:
        relativo = ruta.relative_to(RAIZ).as_posix()
        try:
            ast.parse(ruta.read_text(encoding="utf-8"), filename=relativo)
            print(f"OK: {relativo} compila perfectamente.")
        except SyntaxError as exc:
            print(f"ERROR SINTAXIS en {relativo}:\n{exc}")
            errores += 1
        except Exception as exc:
            print(f"ERROR al verificar {relativo}:\n{exc}")
            errores += 1

    # El recuento DERIVADO, en una linea estable que los guards leen con una
    # regex: el dia que se anada un modulo, sale distinto y sin que nadie
    # tenga que acordarse de actualizar un numero.
    print(f"ALCANCE_DERIVADO={len(ficheros)} modulos revisados bajo src/woptimizer/")

    if errores == 0:
        print("EXITO: Todos los modulos de src/woptimizer/ estan impecables.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())