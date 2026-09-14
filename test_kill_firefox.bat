@echo off
REM ==============================================================================
REM test_kill_firefox.bat
REM
REM Diagnostico: intenta matar firefox.exe con taskkill directo (sin mi app).
REM Doble clic. Reporta:
REM   - Si eres admin o no
REM   - Si firefox aparece en tasklist
REM   - Exit code de taskkill
REM   - Si firefox SIGUE en tasklist tras el intento
REM ==============================================================================
setlocal enabledelayedexpansion

echo.
echo ============================================
echo  Diagnostico: taskkill contra firefox.exe
echo ============================================
echo.

REM Paso 1: comprobar admin
echo [1/4] ¿Eres admin?
net session >nul 2>&1
if errorlevel 1 (
    echo   [INFO] NO eres admin. ^(Esto puede ser el problema.^)
) else (
    echo   [INFO] Si eres admin.
)

REM Paso 2: ver si firefox esta corriendo
echo.
echo [2/4] Buscando firefox.exe en tasklist...
tasklist /FI "IMAGENAME eq firefox.exe" | findstr /I "firefox"
if errorlevel 1 (
    echo   [INFO] No hay firefox.exe corriendo ahora. Abriendo firefox para probar.
    start firefox.exe
    timeout /t 5 /nobreak >nul
) else (
    echo   [INFO] Firefox corriendo. Procediendo.
)

REM Paso 3: ejecutar taskkill directo
echo.
echo [3/4] Ejecutando: taskkill /F /IM firefox.exe /T
taskkill /F /IM firefox.exe /T
echo.
echo   exit code: %errorlevel%
echo   ^(0=exito, 128=no estaba, 1=acceso denegado u otro^)

REM Paso 4: verificar tras el kill
echo.
echo [4/4] Verificando si firefox SIGUE vivo...
tasklist /FI "IMAGENAME eq firefox.exe" | findstr /I "firefox"
if errorlevel 1 (
    echo   [OK] Firefox YA NO esta en tasklist. Muerte confirmada.
    echo   Si en la app veias verde pero firefox seguia vivo, es un BUG DE LA APP.
    echo   Si veias rojo con mensaje de error, es PERMISOS (necesitas admin).
) else (
    echo   [FALLO] Firefox SIGUE en tasklist. taskkill NO pudo matarlo.
    echo   Probablemente necesitas ejecutar como ADMIN.
)

echo.
echo ============================================
echo  Diagnostico completado.
echo ============================================
echo.
pause
endlocal