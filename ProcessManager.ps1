# Process Manager - Lanzador SIN consola
# Doble clic y solo aparece la ventana GUI

$scriptPath = $PSScriptRoot
$pythonScript = Join-Path $scriptPath "process_manager.pyw"

# Lanzar PowerShell oculto que a su vez lanza pythonw.exe (sin consola)
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "powershell.exe"
$psi.Arguments = "-NoProfile -NonInteractive -WindowStyle Hidden -Command `"& pythonw.exe '$pythonScript'`""
$psi.UseShellExecute = $false
$psi.WindowStyle = "Hidden"
$psi.CreateNoWindow = $true

try {
    [System.Diagnostics.Process]::Start($psi) | Out-Null
}
catch {
    # Fallback: mostrar mensaje de error visible
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show(
        "No se pudo iniciar Process Manager.`n`nError: $($_.Exception.Message)`n`nAsegurate de que Python este instalado.",
        "Process Manager",
        "OK",
        "Error"
    )
}
