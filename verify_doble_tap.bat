@echo off
REM ==============================================================================
REM verify_doble_tap.bat
REM
REM Valida v2.0.2 (Trampa #14: doble-tap sin messagebox):
REM   1. Sincroniza process_manager.pyw con process_manager.py
REM   2. Compila process_manager.py (chequeo de sintaxis)
REM   3. Verifica que _request_confirm / _reset_pending_action existen
REM   4. Verifica que NO quedan messagebox de confirmacion en la UI principal
REM
REM USO: doble clic en este archivo. Te dira que pasa/falla en cada paso.
REM ==============================================================================
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo ============================================
echo  Verificacion v2.0.2 - Doble Tap
echo ============================================
echo.

REM Paso 1: sincronizar .pyw
echo [1/4] Sincronizando process_manager.pyw...
if exist process_manager.pyw del process_manager.pyw
copy /Y process_manager.py process_manager.pyw >nul
if errorlevel 1 (
    echo   [FAIL] No pude copiar .py a .pyw
    goto end
)
echo   [OK] .pyw sincronizado

REM Paso 2: py_compile
echo.
echo [2/4] Compilando process_manager.py...
python -c "import py_compile; py_compile.compile('process_manager.py', doraise=True); print('  [OK] sintaxis valida')" 2>&1
if errorlevel 1 (
    echo   [FAIL] Error de sintaxis
    goto end
)

REM Paso 3: helpers doble-tap existen
echo.
echo [3/4] Verificando helpers de doble-tap...
findstr /C:"_request_confirm" process_manager.py >nul
if errorlevel 1 (
    echo   [FAIL] _request_confirm no encontrado
    goto end
)
findstr /C:"_reset_pending_action" process_manager.py >nul
if errorlevel 1 (
    echo   [FAIL] _reset_pending_action no encontrado
    goto end
)
findstr /C:"_set_status" process_manager.py >nul
if errorlevel 1 (
    echo   [FAIL] _set_status no encontrado
    goto end
)
echo   [OK] _request_confirm / _reset_pending_action / _set_status presentes

REM Paso 4: NO quedan messagebox de confirmacion en UI principal
echo.
echo [4/4] Verificando que NO hay messagebox de confirmacion en UI principal...
findstr /N "messagebox.askyesno" process_manager.py | findstr /V "ProfilesDialog"
findstr /N "messagebox.showinfo" process_manager.py | findstr /V "ProfilesDialog"
findstr /N "messagebox.showwarning" process_manager.py | findstr /V "ProfilesDialog"
echo   [INFO] Si solo ves lineas de ProfilesDialog (=) o funciones internas, OK.

REM Resumen
echo.
echo ============================================
echo  Resumen:
echo    - .pyw sincronizado
echo    - sintaxis OK
echo    - helpers doble-tap presentes
echo    - version 2.0.2
echo.
echo  Listo. Doble clic en ProcessManager.vbs para probar.
echo ============================================
echo.

:end
endlocal
pause