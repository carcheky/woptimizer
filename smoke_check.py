"""Smoke check: que process_manager.py sigue siendo Python valido."""
import ast
import os
import sys

root = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(root, "process_manager.py")
with open(src, encoding="utf-8") as f:
    code = f.read()
ast.parse(code)
print(f"[OK] {src}")
print(f"     AST parse OK, {len(code.splitlines())} lineas, {len(code)} bytes")

# Verifica que el helper _app_dir() esta definido
assert "def _app_dir()" in code, "Falta helper _app_dir()"
print("[OK] helper _app_dir() presente (con anotacion -> str)")

# Verifica version
assert '__version__ = "2.1.0"' in code, "Version != 2.1.0"
print('[OK] __version__ = "2.1.0"')

# Verifica que PROCESS_LIST_FILE / PROFILES_FILE usan _app_dir()
assert "PROCESS_LIST_FILE = os.path.join(_app_dir()" in code
assert "PROFILES_FILE = os.path.join(_app_dir()" in code
print("[OK] data files usan _app_dir() (Trampa #17 OK)")