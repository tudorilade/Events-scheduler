#!/bin/bash

python manage.py collectstatic --no-input
python manage.py migrate

gunicorn events_scheduler.asgi:application --bind 0.0.0.0:8000 -k uvicorn.workers.UvicornWorker --workers 2 --log-level debug
