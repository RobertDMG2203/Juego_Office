@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

set "DEST=%LOCALAPPDATA%\MisionDigital\codigo_fuente"
echo.
echo Se guardara una copia del codigo en:
echo "%DEST%"
echo.

if exist "%DEST%" (
    attrib -h -s "%DEST%" >nul 2>&1
    rmdir /s /q "%DEST%"
)
mkdir "%DEST%" >nul 2>&1

robocopy "%~dp0" "%DEST%" /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP ^
  /XD ".venv" ".mision_digital_venv" "build" "dist" ".git" "__pycache__" ".pytest_cache" ^
  /XF "*.pyc" "*.pyo" >nul

attrib +h +s "%DEST%" >nul 2>&1

echo Copia creada y marcada como oculta/sistema.
echo NOTA: esto evita acceso casual, pero no cifra ni protege criptograficamente el codigo.
endlocal
