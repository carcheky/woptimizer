@echo off
REM Build del ejecutable Windows standalone de woptimizer (v2.1.0+)
REM Genera dist\woptimizer.exe (single-file, sin consola, auto-eleva como admin).

setlocal EnableDelayedExpansion

echo.
echo ===========================================================
echo  woptimizer build script (v2.1.0)
echo ===========================================================
echo.

REM 1. Verificar PyInstaller instalado
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PyInstaller no esta instalado.
    echo         Ejecuta primero:  pip install pyinstaller
    exit /b 1
)

REM 2. Verificar version de PyInstaller (necesitamos >=5.13 para --uac-admin)
for /f "tokens=2" %%v in ('pyinstaller --version 2^>^&1') do set PYI_VERSION=%%v
echo [OK] PyInstaller !PYI_VERSION!

REM 3. Sincronizar .pyw desde .py (la GUI real vive en .pyw para no abrir consola)
if not exist "process_manager.pyw" (
    echo [WARN] process_manager.pyw no existe, copiando desde .py
    copy /Y process_manager.py process_manager.pyw >nul
)

REM 4. Build
echo.
echo [BUILD] Compilando woptimizer.exe ... esto tarda 30-60 segundos
echo.

pyinstaller ^
    --onefile ^
    --noconsole ^
    --uac-admin ^
    --name woptimizer ^
    --clean ^
    process_manager.pyw

if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller fallo. Revisa los logs arriba.
    exit /b 1
)

REM 5. Resultado
echo.
echo ===========================================================
echo  Build completado
echo ===========================================================
echo.
if exist "dist\woptimizer.exe" (
    for %%A in ("dist\woptimizer.exe") do echo [OK] dist\woptimizer.exe  ^(%%~zA bytes^)
    echo.
    echo " Para ejecutar: doble clic en dist\woptimizer.exe"
    echo " (UAC pedira confirmacion la primera vez - es normal)"
) else (
    echo [ERROR] dist\woptimizer.exe no se genero
    exit /b 1
)

endlocal