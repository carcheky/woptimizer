@echo off
REM ==============================================================================
REM init_git.bat
REM
REM Inicializa el repo git local de woptimizer y hace el primer commit.
REM Doble clic para ejecutar. Solo se ejecuta UNA VEZ: si .git ya existe, sale
REM sin tocar nada (para commits futuros usa commit_version.bat).
REM
REM Que hace:
REM   1. comprueba que no hay repo (si existe, sale sin tocar nada)
REM   2. git init
REM   3. configura user.name/user.email si no estan
REM   4. verifica que .gitignore existe
REM   5. git add . + commit inicial + tag con la version ACTUAL (leida del codigo)
REM ==============================================================================
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo ============================================
echo  Inicializando repo git para woptimizer
echo ============================================
echo.

REM Paso 0: si el repo ya existe, no hacer nada
if exist .git (
    echo [SKIP] .git ya existe. El repo ya esta inicializado.
    echo        Para commits futuros usa commit_version.bat
    echo.
    pause
    exit /b 0
)

REM Leer la version actual del codigo (mismo metodo que commit_version.bat)
set VERSION=desconocida
for /f "tokens=3 delims= " %%v in ('findstr /B "__version__" process_manager.py') do (
    set VERSION=%%~v
)
set VERSION=!VERSION:"=!
if "!VERSION!"=="desconocida" (
    echo   [FAIL] No se pudo leer __version__ de process_manager.py
    pause
    exit /b 1
)
echo   Version detectada: !VERSION!
echo.

REM Paso 1: git init
echo [1/5] git init...
git init
if errorlevel 1 (
    echo   [FAIL] git no encontrado. Instala Git for Windows: https://git-scm.com
    pause
    exit /b 1
)
echo   [OK] repo inicializado

REM Paso 2: configurar usuario si no existe
echo.
echo [2/5] Configurando usuario git...
git config user.name >nul 2>&1
if errorlevel 1 (
    git config user.name "carcheky"
    echo   [OK] user.name = carcheky
) else (
    echo   [INFO] user.name ya configurado
)
git config user.email >nul 2>&1
if errorlevel 1 (
    git config user.email "carcheky@local"
    echo   [OK] user.email = carcheky@local
) else (
    echo   [INFO] user.email ya configurado
)

REM Paso 3: verificar .gitignore
echo.
echo [3/5] Verificando .gitignore...
if not exist .gitignore (
    echo   [FAIL] .gitignore no existe. Algo va mal.
    pause
    exit /b 1
) else (
    echo   [OK] .gitignore presente
)

REM Paso 4: git add + commit
echo.
echo [4/5] git add . + commit inicial v!VERSION!...
git add .
if errorlevel 1 (
    echo   [FAIL] git add fallo
    pause
    exit /b 1
)
git commit -m "chore: initial commit v!VERSION! (perfiles v2.0 + perfil Gaming editable/reseteable + Trampas 1-15)"
if errorlevel 1 (
    echo   [FAIL] git commit fallo
    pause
    exit /b 1
)
echo   [OK] commit inicial creado

REM Paso 5: tag
echo.
echo [5/5] git tag v!VERSION!...
git tag v!VERSION!
echo   [OK] tag v!VERSION! creado

REM Resumen
echo.
echo ============================================
echo  Repo git inicializado (v!VERSION!).
echo.
echo  Comandos utiles a partir de ahora:
echo    - git log --oneline        (ver historial)
echo    - git tag                  (ver versiones)
echo    - commit_version.bat       (commit futuro tras cambios)
echo    - git diff                 (ver cambios no commiteados)
echo ============================================
echo.
git log --oneline --decorate
pause
endlocal
