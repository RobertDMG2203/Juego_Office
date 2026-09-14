@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Mision Digital - Generador de EXE

cls
echo ============================================================
echo   MISION DIGITAL - GENERADOR DE EJECUTABLE
echo ============================================================
echo.
echo Este proceso crea un entorno aislado .mision_digital_venv.
echo PySide6 y PyInstaller se instalan SOLO dentro de ese entorno.
echo El resultado se guardara como MisionDigital.exe en tu Escritorio.
echo Si ocurre un error, esta ventana NO se cerrara y se creara:
echo compilacion_exe.log
echo.

set "RUNNER="
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

echo Python detectado. Iniciando compilacion...
echo.
%RUNNER% "%~dp0build_exe.py"
set "EXITCODE=%ERRORLEVEL%"

if not "%EXITCODE%"=="0" goto :build_error

echo.
echo ============================================================
echo   LISTO - EL EJECUTABLE FUE CREADO CORRECTAMENTE
echo ============================================================
echo.
echo Revisa tu Escritorio: MisionDigital.exe
echo.
choice /C SN /N /M "Deseas guardar tambien una copia OCULTA del codigo en AppData? [S/N]: "
if errorlevel 2 goto :finish
if exist "%~dp0guardar_codigo_oculto.bat" call "%~dp0guardar_codigo_oculto.bat"
goto :finish

:no_python
echo.
echo ============================================================
echo   ERROR: PYTHON NO FUE ENCONTRADO
echo ============================================================
echo.
echo Instala Python 3.10 o superior desde python.org.
echo IMPORTANTE: durante la instalacion marca "Add Python to PATH".
echo Despues vuelve a ejecutar crear_exe.bat.
set "EXITCODE=2"
goto :finish

:build_error
echo.
echo ============================================================
echo   LA COMPILACION NO PUDO COMPLETARSE
echo ============================================================
echo.
echo Revisa el mensaje mostrado arriba y el archivo:
echo "%~dp0compilacion_exe.log"
echo.
echo Si MisionDigital.exe estaba abierto, cierralo antes de reintentar.

goto :finish

:finish
echo.
echo Presiona una tecla para cerrar esta ventana.
pause >nul
endlocal & exit /b %EXITCODE%
