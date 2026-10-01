import subprocess
import os
import sys
import time

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
import process_manager as pm

# Lanzar notepad
print("[debug] Lanzando notepad.exe...")
notepad = subprocess.Popen(["notepad.exe"], creationflags=0x08000000)
print(f"[debug] PID local: {notepad.pid}")
time.sleep(2)

# Verificar directamente con tasklist
print("\n[debug] tasklist para notepad:")
r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq notepad.exe"], capture_output=True, text=True)
print(r.stdout)

# Verificar con tasklist por PID
print(f"\n[debug] tasklist filtrando por PID {notepad.pid}:")
r = subprocess.run(["tasklist", "/FI", f"PID eq {notepad.pid}"], capture_output=True, text=True)
print(r.stdout)
print(f"[debug] stderr: {r.stderr}")
print(f"[debug] rc: {r.returncode}")

# Llamar get_running_processes y ver TODOS los notepad
print("\n[debug] get_running_processes - buscando 'note':")
procs = pm.get_running_processes()
for p in procs:
    if 'note' in p['name'].lower():
        print(f"  PID={p['pid']} name={p['name']!r} cmdline={p['commandline'][:100]!r}")

# Comparar con PowerShell directo
print("\n[debug] PowerShell directo (Get-CimInstance Win32_Process):")
ps = '''
Get-CimInstance Win32_Process | Where-Object { $_.Name -like '*notepad*' } | ForEach-Object {
    "PID=$($_.ProcessId) Name=$($_.Name) Cmd=$($_.CommandLine.Substring(0, [Math]::Min(80, $_.CommandLine.Length)))"
}
'''
r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                   capture_output=True, text=True, creationflags=0x08000000)
print("stdout:", r.stdout)
print("stderr:", r.stderr)
print("rc:", r.returncode)

# Cleanup
try:
    notepad.kill()
except:
    pass
