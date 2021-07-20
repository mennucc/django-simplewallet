#!/bin/bash

echo Waiting for mysql
while ! python3 ./helper.py ping ; do
    sleep 2
done

echo ======================================================== Running tests
python3 ./manage.py test
echo ======================================================== End of tests
echo ======== Running migrations
python3 ./manage.py migrate
echo ======== Creating users
python3 ./helper.py create_fake_users
echo ======== Deposit some money to user foobar
python3 ./manage.py deposit --username=foobar --amount=100
echo ======== Starting server
python3 ./manage.py runserver 0.0.0.0:8000
