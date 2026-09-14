import subprocess
import os
import sys
import time

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Lanzar notepad
notepad = subprocess.Popen(["notepad.exe"], creationflags=0x08000000)
print(f"[t] notepad PID={notepad.pid}")
time.sleep(2)

# Llamar directamente al script de PowerShell que usa process_manager.py
ps_script = '''
$ProgressPreference = 'SilentlyContinue'
$OutputEncoding = [System.Text.Encoding]::UTF8
Get-CimInstance Win32_Process |
    Where-Object { $_.Name -notin @('powershell.exe', 'pwsh.exe') -and $_.CommandLine } |
    ForEach-Object {
        $name = $_.Name
        $pid = $_.ProcessId
        $cmd = $_.CommandLine -replace "[`t`r`n]", ' '
        if ($cmd.Length -gt 4000) {
            $cmd = $cmd.Substring(0, 4000) + "...[truncated]"
        }
        Write-Output "$name`t$pid`t$cmd"
    }
'''

print("[t] Llamando PowerShell...")
result = subprocess.run(
    ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='replace',
    timeout=30,
    creationflags=0x08000000
)

print(f"[t] returncode: {result.returncode}")
err_s = result.stderr[:200] if result.stderr else '(empty)'
try:
    print(f"[t] stderr: {err_s.encode('ascii', 'replace').decode()}")
except:
    print(f"[t] stderr len: {len(err_s)}")

# Buscar notepad en stdout
lines = result.stdout.strip().split('\n')
print(f"[t] Total lineas: {len(lines)}")

print("\n[t] Lineas con 'notepad':")
for i, line in enumerate(lines):
    if 'notepad' in line.lower():
        print(f"  [{i}] {repr(line[:200])}")

# Intentar kill directo
print(f"\n[t] Intentando taskkill directo del PID {notepad.pid}...")
r2 = subprocess.run(["taskkill", "/F", "/PID", str(notepad.pid)],
                     capture_output=True, text=True, creationflags=0x08000000)
print(f"[t] rc={r2.returncode}, stdout={r2.stdout!r}, stderr={r2.stderr!r}")

# Cleanup
try:
    notepad.kill()
except:
    pass
