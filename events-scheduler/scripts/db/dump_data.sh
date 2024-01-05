#!/bin/bash

file="initial_data.json"

if [[ ! -f "$file" ]] ; then
    # create the initial_data in case it does not exist
    touch "$file"
fi

if [[ "$1" ]] ; then
    file="$1"
fi

if [[ ! -f $file ]] ; then
  echo "Provide an existent file and right path to it."
  exit 1
fi
echo "Database dump starts...."

docker-compose exec web ./manage.py dumpdata events.Event events.Participation users.User users.UserVerification -o "$file" -v 3

echo "Dump successfully done to $file"