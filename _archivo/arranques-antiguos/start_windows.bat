@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

rem WORLDIVES DISCOVERY - lanzador Windows robusto
rem Primero usamos el Python Launcher (py), evitando el alias Microsoft Store.
set "PYTHON_EXE="

where py >nul 2>nul
if not errorlevel 1 (
    py -3 -c "import sys; print(sys.executable)" > "%TEMP%\worlddives_python_path.txt" 2>nul
    if not errorlevel 1 (
        set "PYTHON_EXE=py -3"
    )
)

rem Si no existe py, probar python y comprobar que es un Python real.
if not defined PYTHON_EXE (
    where python >nul 2>nul
    if not errorlevel 1 (
        python -c "import sys; print(sys.version_info[0])" >nul 2>nul
        if not errorlevel 1 set "PYTHON_EXE=python"
    )
)

rem Buscar instalaciones habituales de Python para evitar el alias de Microsoft Store.
if not defined PYTHON_EXE if exist "%LocalAppData%\Programs\Python\Python313\python.exe" set "PYTHON_EXE="%LocalAppData%\Programs\Python\Python313\python.exe""
if not defined PYTHON_EXE if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PYTHON_EXE="%LocalAppData%\Programs\Python\Python312\python.exe""
if not defined PYTHON_EXE if exist "%LocalAppData%\Programs\Python\Python311\python.exe" set "PYTHON_EXE="%LocalAppData%\Programs\Python\Python311\python.exe""
if not defined PYTHON_EXE if exist "%ProgramFiles%\Python313\python.exe" set "PYTHON_EXE="%ProgramFiles%\Python313\python.exe""
if not defined PYTHON_EXE if exist "%ProgramFiles%\Python312\python.exe" set "PYTHON_EXE="%ProgramFiles%\Python312\python.exe""
if not defined PYTHON_EXE if exist "%ProgramFiles%\Python311\python.exe" set "PYTHON_EXE="%ProgramFiles%\Python311\python.exe""

if not defined PYTHON_EXE (
    echo.
    echo ================================================================
    echo   WORLDIVES DISCOVERY - No se ha encontrado una instalacion de Python
    echo ================================================================
    echo.
    echo El proyecto necesita Python para arrancar el servidor local.
    echo.
    echo Windows parece estar usando el alias de Microsoft Store para
    echo el comando "python". Si Python ya esta instalado, comprueba
    echo que el Python Launcher "py" este disponible.
    echo.
    echo Descarga oficial: https://www.python.org/downloads/windows/
    echo.
    pause
    exit /b 1
)

set "PYTHONPATH=%CD%\vendor"

if not exist "app\server.py" (
    echo ERROR: no se encuentra app\server.py.
    echo Ejecuta este archivo desde la carpeta principal de WORLDIVES DISCOVERY.
    pause
    exit /b 1
)

if not exist "data" mkdir "data"
if not exist "storage\documents" mkdir "storage\documents"

echo.
echo ================================================================
echo   WORLDIVES DISCOVERY - Servidor local + SQLite
echo ================================================================
echo.
echo Python: %PYTHON_EXE%
echo Servidor: http://localhost:8000
echo.
echo Abriendo el navegador...
echo Pulsa Ctrl+C para detener el servidor.
echo.

start "WORLDIVES DISCOVERY" /b powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Sleep -Seconds 1; Start-Process 'http://localhost:8000'"
%PYTHON_EXE% app\server.py

set "EXITCODE=%ERRORLEVEL%"
echo.
if not "%EXITCODE%"=="0" (
    echo El servidor se ha detenido con codigo %EXITCODE%.
    echo Revisa el mensaje anterior para ver el motivo.
)
pause
endlocal
