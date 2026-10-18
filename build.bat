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
REM `call` NO es cosmetico (MEDIDO el 2026-10-18, TASK-077): sin el, si `python`
REM resuelve a un `.cmd`/`.bat` --un shim en `%PATH%`, o el `python.bat` de una
REM instalacion vieja-- ese `.cmd` SECUESTRA el control y TODO lo que viene
REM debajo no se ejecuta nunca. El `.bat` salia entonces con el codigo del shim
REM y compilar era un espejismo: medido, con un shim que sale 7, el `.bat` se
REM quedaba parado en este paso y devolvia 0.
call python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [ERROR] PyInstaller no esta instalado.
    echo Ejecuta: pip install -e ".[dev]"
    pause
    exit /b 1
)

REM 2. Limpiar cache anterior
if exist "build" rmdir /s /q "build"
if exist "dist\woptimizer.exe" del /f /q "dist\woptimizer.exe"

REM 3. Compilar (los flags viven en force_build.py, no aqui)
echo Construyendo...
call python force_build.py
if errorlevel 1 goto :fallo

REM 4. Verificar salida
if not exist "dist\woptimizer.exe" goto :fallo
echo.
echo ===========================================================
echo [EXITO] Compilacion terminada.
echo Archivo generado: dist\woptimizer.exe
echo ===========================================================
exit /b 0

:fallo
set "RC=%errorlevel%"
echo.
echo ===========================================================
echo [ERROR] Fallo la compilacion. Revisa el log de PyInstaller.
echo ===========================================================
REM  El codigo de salida de la compilacion es el de este .bat: sin esto un
REM  .exe roto salia por aqui con 0 (S3 de STATUS.md, cerrado en TASK-077).
REM  Si se llega aqui con RC 0 --la compilacion "fue bien" pero el .exe no
REM  esta-- tampoco se puede devolver 0, o el .bat volveria a mentir.
if not "%RC%"=="0" exit /b %RC%
exit /b 1