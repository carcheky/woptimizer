@echo off
chcp 65001 >nul
title Process Manager
cd /d "%~dp0"
python process_manager.py
pause
