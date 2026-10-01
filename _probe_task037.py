"""Sonda de determinismo: que clase de error lanza cada fixture de run_tests.py,
escrita en modo texto de Windows (con y sin translate) y leida por ast.parse."""
import ast
import os
import tempfile

CASOS = {
    "sangria": "def test_alfa():\n    return 1\n        return 2\n",
    "tab_vs_espacios": "def test_alfa():\n\treturn 1\n    return 2\n",
    "tab_lado_izq": "def test_alfa():\n\treturn 1\n        return 2\n",
    "falta_dos_puntos": "def test_alfa()\n    return 1\n",
    "parentesis": "def test_alfa():\n    return (1\n",
    "tab_mixto_mismo_nivel": "def test_alfa():\n\treturn 1\n\treturn 2\n",
}

for nombre, fuente in CASOS.items():
    for modo, kwargs in (("text_default", {}), ("newline_empty", {"newline": ""})):
        d = tempfile.mkdtemp(prefix="probe_")
        ruta = os.path.join(d, "run_tests.py")
        with open(ruta, "w", encoding="utf-8", **kwargs) as fh:
            fh.write(fuente)
        with open(ruta, "rb") as fh:
            bytes_en_disco = fh.read()
        try:
            with open(ruta, encoding="utf-8") as fh:
                leida = fh.read()
            ast.parse(leida, filename=ruta)
            got = "OK (compila)"
        except SyntaxError as exc:
            got = type(exc).__name__
        print(f"{nombre:26s} {modo:14s} bytes={bytes_en_disco!r:44s} -> {got}")
    print()
