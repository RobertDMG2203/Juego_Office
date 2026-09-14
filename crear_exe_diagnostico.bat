@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Mision Digital - Diagnostico del generador

echo Este modo deja la consola abierta incluso si el generador falla.
echo.
call "%~dp0crear_exe.bat"
echo.
echo Codigo de salida: %ERRORLEVEL%
echo Log de compilacion: "%~dp0compilacion_exe.log"
echo.
echo La consola permanecera abierta. Escribe EXIT para cerrarla.
cmd /k
