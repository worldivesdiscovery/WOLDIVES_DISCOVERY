@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PYTHONPATH=%CD%\vendor"
set "WOD_HOST=0.0.0.0"

echo.
echo ================================================================
echo   WORLDIVES DISCOVERY - SERVIDOR PARA PC + TABLET + MOVIL
 echo ================================================================
echo.
for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /R /C:"IPv4.*:"') do (
  for /f "tokens=*" %%B in ("%%A") do echo Acceso desde otros dispositivos: http://%%B:8000
)
echo.
echo En el mismo PC: http://localhost:8000
 echo.
echo IMPORTANTE: PC, tablet y movil deben estar en la misma red Wi-Fi.
echo Si Windows muestra una alerta del Firewall, permite Python en la red privada.
echo.
py -3 app\server.py
if errorlevel 1 python app\server.py
pause
endlocal
