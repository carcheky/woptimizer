import py_compile
import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("Validando sintaxis estatica de la Fase 3...")
files_to_check = [
    'src/woptimizer/ui/app.py',
    'src/woptimizer/ui/main_window.py',
    'src/woptimizer/__main__.py'
]

errors = 0
for f in files_to_check:
    try:
        py_compile.compile(f, doraise=True)
        print(f"OK: {f} compila perfectamente.")
    except py_compile.PyCompileError as e:
        print(f"ERROR SINTAXIS en {f}:\n{e}")
        errors += 1
        
if errors == 0:
    print("EXITO: Todos los modulos UI estan impecables.")
    sys.exit(0)
else:
    sys.exit(1)
