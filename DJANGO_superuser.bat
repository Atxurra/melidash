@echo off
call env\Scripts\activate
echo Entorno virtual 'VENV' activado.
python manage.py createsuperuser
pause
