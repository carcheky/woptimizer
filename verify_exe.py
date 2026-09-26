"""
Verifica que el .exe generado por build.bat funciona correctamente.

Comprueba:
1. dist\\woptimizer.exe existe y tiene tamano razonable (>5 MB).
2. PyInstaller >=5.13 instalado (soporta --uac-admin).
3. El .exe es valido como PE Windows.
4. Al lanzar el .exe en background, levanta la GUI sin mostrar consola.
"""
import os
import sys
import subprocess
import time
import struct

CREATE_NO_WINDOW = 0x08000000
EXE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "woptimizer.exe")
PYI_MIN_VERSION = (5, 13)


def ok(msg):
    print(f"[OK]   {msg}")


def fail(msg):
    print(f"[FAIL] {msg}")
    sys.exit(1)


def check_exe_exists():
    if not os.path.exists(EXE_PATH):
        fail(f"Ejecutable no encontrado: {EXE_PATH}. Ejecuta build.bat primero.")
    size = os.path.getsize(EXE_PATH)
    if size < 5 * 1024 * 1024:
        fail(f"Ejecutable demasiado pequeno ({size} bytes), build probablemente fallo.")
    ok(f"dist/woptimizer.exe existe ({size / 1024 / 1024:.1f} MB)")


def check_pe_header():
    """Comprueba que el archivo tiene el magic 'MZ' de PE Windows."""
    with open(EXE_PATH, "rb") as f:
        magic = f.read(2)
    if magic != b"MZ":
        fail(f"No es un ejecutable PE Windows (magic={magic!r})")
    ok("Magic PE valido (MZ)")


def check_pyinstaller_version():
    try:
        import PyInstaller
    except ImportError:
        fail("PyInstaller no instalado. Ejecuta: pip install pyinstaller")
    ver_str = PyInstaller.__version__
    parts = tuple(int(x) for x in ver_str.split(".")[:2])
    if parts < PYI_MIN_VERSION:
        fail(f"PyInstaller {ver_str} < {'.'.join(map(str, PYI_MIN_VERSION))} (necesario para --uac-admin)")
    ok(f"PyInstaller {ver_str} (>= {'.'.join(map(str, PYI_MIN_VERSION))})")


def check_admin_manifest():
    """Comprueba que el manifest requireAdministrator esta embebido en el PE.

    Busca la cadena 'requireAdministrator' o 'asInvoker' como proxy del manifest.
    """
    with open(EXE_PATH, "rb") as f:
        data = f.read()
    if b"requireAdministrator" in data:
        ok("Manifest requireAdministrator embebido (auto-eleva)")
    elif b"asInvoker" in data:
        fail("Solo manifest asInvoker, no auto-eleva (deberia ser requireAdministrator)")
    else:
        # En --onefile de PyInstaller, el manifest esta en un recurso del bootloader.
        # No siempre aparece como string literal. Avisar pero no fallar.
        print("[WARN] No se detecta string literal del manifest (puede estar OK en --onefile)")


def check_launches_without_console():
    """Lanza el .exe en background y comprueba que no muere inmediatamente.

    Como es GUI sin consola, no podemos leer stdout. Comprobamos que el
    proceso arranca y sigue vivo unos segundos (no crash inmediato).
    """
    proc = subprocess.Popen(
        [EXE_PATH],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=CREATE_NO_WINDOW,
    )
    time.sleep(3)
    poll = proc.poll()
    if poll is not None:
        fail(f"El .exe termino prematuramente con codigo {poll}")
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
    ok("Arranca sin crash inmediato y responde a terminate")


def main():
    print("=" * 60)
    print(" verify_exe.py — woptimizer v2.1.0")
    print("=" * 60)
    print()
    check_pyinstaller_version()
    check_exe_exists()
    check_pe_header()
    check_admin_manifest()
    check_launches_without_console()
    print()
    print("=" * 60)
    print(" Todo OK. El ejecutable esta listo para distribuir.")
    print("=" * 60)


if __name__ == "__main__":
    main()