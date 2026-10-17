@echo off
rem Restaura los datos del entorno de pruebas (para el servidor de pruebas antes).
cd /d "%~dp0\.."
set "WOD_DB_PATH=%CD%\data\pruebas\worldives.sqlite3"
python scripts\reset_demo.py %*
pause
