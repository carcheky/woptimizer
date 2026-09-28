import subprocess
import sys
import os

try:
    print("Forzando compilación directa saltando el shell de Windows...")
    # Ejecutamos pyinstaller de forma directa y bloqueante sin usar os.startfile
    subprocess.check_call([
        sys.executable,
        "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        "--uac-admin",
        "--name", "woptimizer",
        "--clean",
        "--add-data", "assets;assets",
        "src/woptimizer/__main__.py"
    ])
    
    if os.path.exists("dist/woptimizer.exe"):
        print("EXITO ABSOLUTO: El ejecutable ha sido creado.")
        sys.exit(0)
    else:
        print("ERROR: Pyinstaller termino pero el .exe no esta.")
        sys.exit(1)
        
except Exception as e:
    import traceback
    print(f"ERROR FATAL: {traceback.format_exc()}")
    sys.exit(1)
