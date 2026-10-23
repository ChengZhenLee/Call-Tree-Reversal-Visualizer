@echo off
rem Reads input.json from this folder and writes output.tex next to it.
cd /d "%~dp0"

where py >nul 2>nul && (set PYTHON=py -3) || (set PYTHON=python)

%PYTHON% main.py %*
if errorlevel 1 (
    echo.
    echo Failed. Check that Python 3 is installed and input.json is valid.
) else (
    echo Wrote output.tex
)
pause
