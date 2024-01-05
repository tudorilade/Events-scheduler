#!/bin/bash

file="initial_data.json"

if [[ "$1" ]] ; then
    echo "Another dump provided for loading data ..."
    file=$1
fi

if [[ ! -f "$file" ]] ; then
    echo "Dump performed or not found. Make sure the file is named initial_data.json and is placed in the root of project"
    exit 1
fi

echo "File found. Loading data..."

docker-compose exec web ./manage.py loaddata "$file" -v 3

mv "$file" "$file.imported"
