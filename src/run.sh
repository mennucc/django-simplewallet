#!/bin/bash

echo Waiting for mysql
while ! python3 django_pursed/helper.py ping ; do
    sleep 2
done

echo Running migrations
python3 django_pursed/manage.py migrate
echo Creating users
python3 django_pursed/helper.py create_fake_users
echo Deposit some money
python3 django_pursed/helper.py deposit foobar 100
echo Startin server
python3 django_pursed/manage.py runserver 0.0.0.0:8000
