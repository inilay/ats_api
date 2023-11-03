python3 manage.py collectstatic --no-input


python3 manage.py makemigrations
python3 manage.py migrate

# Start server

python3 manage.py runserver 0.0.0.0:8000
# gunicorn automatic_tournament_system.wsgi:application --bind 0.0.0.0:49088
