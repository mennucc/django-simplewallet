#!/bin/bash

echo Waiting for mysql
while ! python3 django_pursed/helper.py ping ; do
    sleep 2
done

echo ======================================================== Running tests
( cd django_pursed ;  ./manage.py test )
echo ======================================================== End of tests
echo ======== Running migrations
python3 django_pursed/manage.py migrate
echo ======== Creating users
python3 django_pursed/helper.py create_fake_users
echo ======== Deposit some money to user foobar
python3 django_pursed/manage.py deposit --username=foobar --amount=100
echo ======== Starting server
python3 django_pursed/manage.py runserver 0.0.0.0:8000
