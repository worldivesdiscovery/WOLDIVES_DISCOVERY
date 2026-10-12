@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
set "PYTHON_EXE="
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -c "import sys; print(sys.executable)" >nul 2>nul
    if not errorlevel 1 set "PYTHON_EXE=py -3"
)
if not defined PYTHON_EXE (
    where python >nul 2>nul
    if not errorlevel 1 (
        python -c "import sys; print(sys.version_info[0])" >nul 2>nul
        if not errorlevel 1 set "PYTHON_EXE=python"
    )
)
if not defined PYTHON_EXE if exist "%LocalAppData%\Programs\Python\Python313\python.exe" set "PYTHON_EXE="%LocalAppData%\Programs\Python\Python313\python.exe""
if not defined PYTHON_EXE if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PYTHON_EXE="%LocalAppData%\Programs\Python\Python312\python.exe""
if not defined PYTHON_EXE if exist "%LocalAppData%\Programs\Python\Python311\python.exe" set "PYTHON_EXE="%LocalAppData%\Programs\Python\Python311\python.exe""
if not defined PYTHON_EXE (
  echo No se ha encontrado Python. Prueba primero con "py -3" en CMD.
  pause
  exit /b 1
)
set "PYTHONPATH=%CD%\vendor"
echo Python detectado: %PYTHON_EXE%
echo Lanzando servidor en http://localhost:8000
%PYTHON_EXE% app\server.py
pause
endlocal
