@echo off
rem WORLDIVES DISCOVERY - arranque en Windows (doble clic).
rem   iniciar.bat                la web en http://localhost:8000
rem   iniciar.bat --red-local    tambien desde otros dispositivos de tu red
rem   iniciar.bat --depuracion   muestra cada peticion en esta ventana
setlocal EnableExtensions
cd /d "%~dp0"
set "PY="
where py >nul 2>nul && py -3 -c "import sys" >nul 2>nul && set "PY=py -3"
if not defined PY ( where python >nul 2>nul && python -c "import sys; assert sys.version_info>=(3,11)" >nul 2>nul && set "PY=python" )
if not defined PY if exist "%LocalAppData%\Programs\Python\Python313\python.exe" set "PY="%LocalAppData%\Programs\Python\Python313\python.exe""
if not defined PY if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY="%LocalAppData%\Programs\Python\Python312\python.exe""
if not defined PY if exist "%LocalAppData%\Programs\Python\Python311\python.exe" set "PY="%LocalAppData%\Programs\Python\Python311\python.exe""
if not defined PY (
  echo.
  echo  WORLDIVES DISCOVERY necesita Python 3.11 o superior.
  echo  Descargalo de https://www.python.org/downloads/windows/ y marca "Add python.exe to PATH".
  echo.
  pause
  exit /b 1
)
%PY% scripts\iniciar.py %*
if errorlevel 1 (
  echo.
  echo  El servidor se ha detenido con un error. Revisa el mensaje de arriba.
)
pause
endlocal
