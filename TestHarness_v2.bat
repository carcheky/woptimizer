@echo off
chcp 65001 >nul
title Test Harness v2 - Process Manager
cd /d "%~dp0"
echo === Test Harness v2 (python.exe directo, sin wrappers) ===
echo.
python test_harness_v2.py
echo.
echo === Test finalizado. Presiona cualquier tecla para cerrar. ===
pause >nul
