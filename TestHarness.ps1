# Test Harness - Doble clic para ejecutar
$scriptPath = $PSScriptRoot
$testScript = Join-Path $scriptPath "test_harness.py"

Write-Host "Process Manager - Test Harness" -ForegroundColor Cyan
Write-Host ""

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "ERROR: Python no encontrado" -ForegroundColor Red
    Read-Host "Enter para salir"
    exit 1
}

& python $testScript
$exitCode = $LASTEXITCODE

if ($exitCode -ne 0 -and $exitCode -ne $null) {
    Write-Host ""
    Write-Host "Test termino con codigo: $exitCode" -ForegroundColor Yellow
}

Read-Host "Enter para salir"
