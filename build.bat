@echo off
REM =============================================================================
REM  woptimizer - Build Script (v3)
REM =============================================================================

echo.
echo ===========================================================
echo   woptimizer - Compilando Standalone Executable (PyInstaller)
echo ===========================================================
echo.

REM 1. Validar PyInstaller
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [ERROR] PyInstaller no esta instalado.
    echo Ejecuta: pip install -e ".[dev]"
    pause
    exit /b 1
)

REM 2. Limpiar cache anterior
if exist "build" rmdir /s /q "build"
if exist "dist\woptimizer.exe" del /f /q "dist\woptimizer.exe"

REM 3. Ejecutar PyInstaller
echo Construyendo...
pyinstaller --onefile --noconsole --uac-admin --name woptimizer --clean src/woptimizer/__main__.py

REM 4. Verificar salida
if exist "dist\woptimizer.exe" (
    echo.
    echo ===========================================================
    echo [EXITO] Compilacion terminada. 
    echo Archivo generado: dist\woptimizer.exe
    echo ===========================================================
) else (
    echo.
    echo [ERROR] Fallo la compilacion. Revisa el log de PyInstaller.
)
exit /b 0