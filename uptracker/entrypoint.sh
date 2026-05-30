#!/bin/bash

# Start Celery Beat in the background
celery -A your_project_name beat --loglevel=info &

# Start Celery Worker in the foreground (keeps the container alive)
exec celery -A your_project_name worker --loglevel=info