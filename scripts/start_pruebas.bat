@echo off
rem WORLDIVES DISCOVERY - ENTORNO DE PRUEBAS (zip "-pruebas"). Nunca en el servidor real.
rem Puerto 8100, banda "Entorno de pruebas", cuentas de CUENTAS-DE-PRUEBA.md, correos en data\pruebas\correos.
setlocal
cd /d "%~dp0\.."
set "PY=python"
where py >nul 2>nul && set "PY=py -3"
set WOD_DEMO_MODE=1
set WOD_ENV=demo
set WOD_PORT=8100
set WOD_HOST=127.0.0.1
set WOD_PUBLIC_URL=http://127.0.0.1:8100
set "WOD_DB_PATH=%CD%\data\pruebas\worldives.sqlite3"
set "WOD_STORAGE_DIR=%CD%\data\pruebas\storage"
set "WOD_LOG_DIR=%CD%\data\pruebas\logs"
set "WOD_MAIL_FILE_DIR=%CD%\data\pruebas\correos"
set "WOD_BACKUP_DIR=%CD%\data\pruebas\copias"
set WOD_ADMIN_TOTP_REQUIRED=0
set WOD_SMTP_HOST=
set "PYTHONPATH=%CD%\vendor"
if not exist "data\pruebas\correos" mkdir "data\pruebas\correos"
%PY% scripts\reset_demo.py --si-hace-falta
if errorlevel 1 ( echo No se ha podido preparar la demo. & pause & exit /b 1 )
echo Entorno de pruebas en http://127.0.0.1:8100 - cuentas en CUENTAS-DE-PRUEBA.md
start "" /b powershell -NoProfile -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:8100'"
%PY% app\server.py
pause
endlocal
