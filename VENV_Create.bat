@echo off
setlocal enabledelayedexpansion

:: Crear Entorno Virtual "env"
python -m venv env
if not exist "env\Scripts\activate" (
    echo No se pudo crear el entorno virtual.
    exit /b
)
echo Entorno virtual 'env' creado.
pause
