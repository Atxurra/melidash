@echo off
call env\Scripts\activate
if exist requirements.txt (
    echo Instalando librerias desde requirements.txt...
    pip install -r requirements.txt
)
echo Fin del script.
pause
