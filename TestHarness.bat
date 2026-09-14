@echo off
chcp 65001 >nul
title Process Manager - Test Harness
cd /d "%~dp0"
python test_harness.py
pause
