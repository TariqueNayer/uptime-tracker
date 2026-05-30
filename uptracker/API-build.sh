#!/usr/bin/env bash
set -o errexit

pip install uv

uv sync --frozen

python manage.py collectstatic --no-input

python manage.py migrate

python manage.py makesuper