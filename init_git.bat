@echo off
REM ==============================================================================
REM init_git.bat
REM
REM Inicializa el repo git local de woptimizer y hace el primer commit.
REM Doble clic para ejecutar.
REM
REM Que hace:
REM   1. git init
REM   2. configura user.name/user.email si no estan
REM   3. verifica que .gitignore existe
REM   4. git add . + commit inicial
REM   5. tag v2.0.5 (version actual)
REM ==============================================================================
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo ============================================
echo  Inicializando repo git para woptimizer
echo ============================================
echo.

REM Paso 1: git init
echo [1/5] git init...
if exist .git (
    echo   [SKIP] .git ya existe. No se reinicializa.
) else (
    git init
    if errorlevel 1 (
        echo   [FAIL] git no encontrado. Instala Git for Windows: https://git-scm.com
        goto end
    )
    echo   [OK] repo inicializado
)

REM Paso 2: configurar usuario si no existe
echo.
echo [2/5] Configurando usuario git...
git config user.name >nul 2>&1
if errorlevel 1 (
    git config user.name "carcheky"
    echo   [OK] user.name = carcheky
) else (
    echo   [INFO] user.name ya configurado: 
    git config user.name
)
git config user.email >nul 2>&1
if errorlevel 1 (
    git config user.email "carcheky@local"
    echo   [OK] user.email = carcheky@local
) else (
    echo   [INFO] user.email ya configurado: 
    git config user.email
)

REM Paso 3: verificar .gitignore
echo.
echo [3/5] Verificando .gitignore...
if not exist .gitignore (
    echo   [FAIL] .gitignore no existe. Algo va mal.
    goto end
) else (
    echo   [OK] .gitignore presente
)

REM Mostrar lo que se ignoraria
echo   Archivos ignorados (muestra):
git status --ignored | findstr /V "^$" | findstr /C:"profiles.json" /C:"saved_processes.json" /C:"__pycache__" /C:"Ignorados" >nul
echo   - profiles.json (datos del usuario)
echo   - saved_processes.json (legacy)
echo   - __pycache__/ *.pyc
echo   - .vscode/ .idea/

REM Paso 4: git add + commit
echo.
echo [4/5] git add . + commit inicial...
git add .
if errorlevel 1 (
    echo   [FAIL] git add fallo
    goto end
)
git commit -m "chore: initial commit v2.0.5 (Trampas 1-15 + Bug #2 resuelto + Trampa #15 gaming keepers + double-tap UX + _run_kill verification)"
if errorlevel 1 (
    echo   [FAIL] git commit fallo
    goto end
)
echo   [OK] commit inicial creado

REM Paso 5: tag
echo.
echo [5/5] git tag v2.0.5...
git tag v2.0.5
echo   [OK] tag v2.0.5 creado

REM Resumen
echo.
echo ============================================
echo  Repo git inicializado.
echo.
echo  Comandos utiles a partir de ahora:
echo    - git log --oneline        (ver historial)
echo    - git tag                  (ver versiones)
echo    - commit_version.bat       (commit futuro tras cambios)
echo    - git diff                 (ver cambios no commiteados)
echo ============================================
echo.
git log --oneline --decorate

:end
endlocal
pause