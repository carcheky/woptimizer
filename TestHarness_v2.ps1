# Test Harness v2 - Lanzador silencioso sin consola
# Doble clic ejecuta el test y muestra resultado en una ventana nueva
$scriptPath = $PSScriptRoot
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "cmd.exe"
$psi.Arguments = "/c `"cd /d `"$scriptPath`" && TestHarness_v2.bat`""
$psi.UseShellExecute = $true
$psi.WindowStyle = "Normal"
[System.Diagnostics.Process]::Start($psi) | Out-Null
