@echo off
REM =============================================================================
REM  woptimizer - Build Script (v3)
REM =============================================================================

echo.
echo ===========================================================
echo   woptimizer - Compilando Standalone Executable (PyInstaller)
echo ===========================================================
echo.

REM 1. PRECONDICION: PyInstaller tiene que estar ANTES de tocar nada.
REM `call` NO es cosmetico (MEDIDO el 2026-10-18, TASK-077): sin el, si `python`
REM resuelve a un `.cmd`/`.bat` --un shim en `%PATH%`, o el `python.bat` de una
REM instalacion vieja-- ese `.cmd` SECUESTRA el control y TODO lo que viene
REM debajo no se ejecuta nunca. El `.bat` salia entonces con el codigo del shim
REM y compilar era un espejismo: medido, con un shim que sale 7, el `.bat` se
REM quedaba parado en este paso y devolvia 0.
REM
REM Y el `if errorlevel 1` de este paso es lo que impide el fallo mas caro de
REM todos, MEDIDO el 2026-10-18 (mutante `S3`, reproducido por el
REM `mutation-auditor`): sin el, un PyInstaller ausente NO paraba aqui, el paso
REM de debajo corria y `del` BORRABA el `.exe` que ya funcionaba, y luego el
REM `.bat` salia diciendo "Fallo la compilacion. Revisa el log de PyInstaller"
REM sin que hubiera compilado nada. Dos danos de golpe: el usuario se queda
REM sin ejecutable y el motivo que lee no tiene relacion con la causa. Por eso la
REM precondicion va PRIMERO y con un motivo PROPIO, y por eso hay tres salidas
REM distintas en vez de una: un unico `:fallo` hacia que cualquier causa
REM imprimia el mismo motivo, y el motivo impreso era la mitad del bug.
call python -c "import PyInstaller" 2>nul
if errorlevel 1 goto :sin_pyinstaller

REM 2. Limpiar cache anterior. Solo se llega aqui con la precondicion EN PIE:
REM nada de lo de este paso, ni `build\` ni el `.exe` de `dist\`, se toca antes
REM de saber que hay con que compilar.
if exist "build" rmdir /s /q "build"
if exist "dist\woptimizer.exe" del /f /q "dist\woptimizer.exe"

REM 3. Compilar (los flags viven en force_build.py, no aqui)
echo Construyendo...
call python force_build.py
if errorlevel 1 goto :fallo

REM 4. Verificar salida
if not exist "dist\woptimizer.exe" goto :sin_salida
echo.
echo ===========================================================
echo [EXITO] Compilacion terminada.
echo Archivo generado: dist\woptimizer.exe
echo ===========================================================
exit /b 0

REM --- Salidas, una por causa. El motivo de cada una describe LO QUE PASO ---
REM Un solo `:fallo` imprimia "Revisa el log de PyInstaller" tambien cuando no
REM habia compilacion, y ahi no hay ningun log que mirar.
:sin_pyinstaller
echo.
echo ===========================================================
echo [ERROR] PyInstaller no esta instalado. NO SE HA COMPILADO NADA
echo         y no se ha tocado ni build\ ni dist\woptimizer.exe.
echo Ejecuta: pip install -e ".[dev]"
echo ===========================================================
pause
exit /b 1

:sin_salida
echo.
echo ===========================================================
echo [ERROR] La compilacion salio con 0 pero no dejo dist\woptimizer.exe
echo ===========================================================
exit /b 1

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