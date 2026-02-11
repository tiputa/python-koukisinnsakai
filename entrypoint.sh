#!/bin/bash
export PYTHONPATH=./vendor
python3 manage.py migrate --noinput
python3 -m gunicorn --workers 2 --timeout 60 kouki_sinnsa.wsgi --bind 0.0.0.0:8000