@echo off
title SafeRouteAI System Launcher
cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    python launch.py
) else (
    python launch.py
)
pause
