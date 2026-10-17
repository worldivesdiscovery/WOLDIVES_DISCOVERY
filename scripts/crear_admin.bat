@echo off
rem Crea la primera cuenta de administracion (pide la contrasena sin mostrarla).
rem Uso: scripts\crear_admin.bat --email tu@dominio --username admin --name "Tu Nombre"
cd /d "%~dp0\.."
python app\server.py --create-admin %*
