@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Mision Digital - Inicio seguro

set "VENV=%~dp0.mision_digital_venv"
set "PYVENV=%VENV%\Scripts\python.exe"
set "RUNNER="

if exist "%PYVENV%" goto :run

where py >nul 2>nul
if not errorlevel 1 (
    py -3 -c "import sys; assert sys.version_info >= (3,10)" >nul 2>nul
    if not errorlevel 1 set "RUNNER=py -3"
)
if not defined RUNNER (
    where python >nul 2>nul
    if not errorlevel 1 (
        python -c "import sys; assert sys.version_info >= (3,10)" >nul 2>nul
        if not errorlevel 1 set "RUNNER=python"
    )
)
if not defined RUNNER goto :no_python

echo Creando entorno virtual EXCLUSIVO de Mision Digital...
%RUNNER% -m venv "%VENV%"
if errorlevel 1 goto :error

"%PYVENV%" -m pip install --upgrade pip
if errorlevel 1 goto :error
"%PYVENV%" -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 goto :error

:run
"%PYVENV%" "%~dp0main.py"
set "EXITCODE=%ERRORLEVEL%"
endlocal & exit /b %EXITCODE%

:no_python
echo ERROR: se requiere Python 3.10 o superior para ejecutar desde codigo fuente.
echo La version EXE no necesita Python instalado.
goto :error

:error
echo.
echo No se pudo preparar o iniciar Mision Digital.
echo Ninguna libreria global fue modificada: todas las instalaciones se intentan dentro de .mision_digital_venv.
pause
endlocal & exit /b 1
