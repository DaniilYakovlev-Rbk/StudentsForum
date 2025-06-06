@echo off
echo Activating virtual environment...
call venv\Scripts\activate

echo Setting up Django environment...
SET DJANGO_SETTINGS_MODULE=student_forum.settings
SET PYTHONPATH=%CD%

echo Running database migrations...
python manage.py migrate

echo Collecting static files...
python manage.py collectstatic --noinput

echo Starting Daphne server...
echo Link: http://localhost:8000
daphne -b 0.0.0.0 -p 8000 student_forum.asgi:application