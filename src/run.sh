#!/bin/sh

echo Running migrations
python3 django_pursed/manage.py migrate
echo Creating users
python3 django_pursed/helper.py create_fake_users
echo Startin server
python3 django_pursed/manage.py runserver 0.0.0.0:8000
