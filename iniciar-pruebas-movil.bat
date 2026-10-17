@echo off
rem WORLDIVES DISCOVERY - ENTORNO DE PRUEBAS para la app WORLDIVES Pruebas (v50.48). Nunca en el servidor real.
rem Ensena la direccion que hay que escribir en el movil (el movil y este ordenador, en la misma wifi).
rem Si Windows pregunta por el cortafuegos, marca "Redes privadas" y pulsa "Permitir acceso".
cd /d "%~dp0"
call iniciar.bat --pruebas --red-local %*
