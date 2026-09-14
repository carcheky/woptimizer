@echo off
REM ==============================================================================
REM commit_version.bat
REM
REM Helper para hacer commit rapido despues de cambios. Lee la version de
REM process_manager.py y hace un commit con la version en el mensaje.
REM
REM Uso: doble clic. Te pedira un mensaje corto.
REM ==============================================================================
setlocal enabledelayedexpansion

cd /d "%~dp0"

if not exist .git (
    echo [ERROR] No hay repo git. Ejecuta init_git.bat primero.
    pause
    exit /b 1
)

REM Extraer version del __version__
set VERSION=desconocida
for /f "tokens=3 delims= " %%v in ('findstr /B "__version__" process_manager.py') do (
    set VERSION=%%~v
)
set VERSION=!_VERSION:"=!

echo.
echo ============================================
echo  Commit version detectado: !VERSION!
echo ============================================
echo.

REM Mostrar diff
echo Cambios pendientes:
git status --short
echo.

REM Pedir mensaje
set /p MSG="Mensaje del commit (Enter vacio = 'wip'): "
if "!MSG!"=="" set MSG="wip"

REM Add + commit
git add .
git commit -m "v!VERSION!: !MSG!"
if errorlevel 1 (
    echo.
    echo [INFO] No hubo cambios que commitear o commit fallo.
) else (
    echo.
    echo [OK] Commit creado. Log reciente:
    git log --oneline -5
)

echo.
endlocal
pause