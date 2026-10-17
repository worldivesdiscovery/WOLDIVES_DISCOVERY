@echo off
rem WORLDIVES DISCOVERY - ENTORNO DE PRUEBAS (zip "-DEMO"), puerto 8100. Nunca en el servidor real.
cd /d "%~dp0"
call iniciar.bat --pruebas %*
