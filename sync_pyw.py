"""Script one-shot: sincroniza process_manager.pyw con process_manager.py.

USO: Ejecutar UNA vez desde PowerShell o doble clic:
    python sync_pyw.py

El sandbox del agente no puede hacer Copy-Item (EPERM), asi que el usuario
lo ejecuta manualmente. Despues de esto, doble-click en ProcessManager.vbs
usara el codigo nuevo.

Tras sincronizar, puedes borrar este script.
"""
import shutil
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(script_dir, "process_manager.py")
dst = os.path.join(script_dir, "process_manager.pyw")

if not os.path.exists(src):
    print(f"[ERROR] No existe {src}")
    raise SystemExit(1)

shutil.copy2(src, dst)
src_size = os.path.getsize(src)
dst_size = os.path.getsize(dst)
print(f"[ok] {dst} sincronizado ({dst_size} bytes, source: {src_size} bytes)")
