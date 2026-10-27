@echo off
title Flappy Bird Setup
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
  where py >nul 2>&1
  if errorlevel 1 (
    echo Python is required. Install from https://www.python.org/downloads/
    echo Enable "Add Python to PATH" during setup.
    pause
    exit /b 1
  )
  py -3 install_windows.py
  exit /b %ERRORLEVEL%
)

python install_windows.py
if errorlevel 1 pause
