import py_compile
import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("Validando sintaxis estatica de la Fase 3...")
files_to_check = [
    'src/woptimizer/ui/app.py',
    'src/woptimizer/ui/main_window.py',
    'src/woptimizer/ui/confirmation.py',
    'src/woptimizer/ui/feedback.py',
    'src/woptimizer/ui/views/dashboard_view.py',
    'src/woptimizer/ui/views/pack_manager_view.py',
    'src/woptimizer/ui/views/process_manager_view.py',
    'src/woptimizer/services/notification_service.py',
    'src/woptimizer/__main__.py'
]

import ast

errors = 0
for f in files_to_check:
    try:
        with open(f, 'r', encoding='utf-8') as src_file:
            ast.parse(src_file.read(), filename=f)
        print(f"OK: {f} compila perfectamente.")
    except SyntaxError as e:
        print(f"ERROR SINTAXIS en {f}:\n{e}")
        errors += 1
    except Exception as e:
        print(f"ERROR al verificar {f}:\n{e}")
        errors += 1
        
if errors == 0:
    print("EXITO: Todos los modulos UI estan impecables.")
    sys.exit(0)
else:
    sys.exit(1)
