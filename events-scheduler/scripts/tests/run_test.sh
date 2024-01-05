#!/bin/bash

# Execute a test. It will be used only when testing individual python files / classes / methods.
# For running the test of the entire application, please run: run_coverage.sh

if [[ ! "$1" ]] ; then
  echo "Provide the path to the testing file."
  exit 1
fi

docker-compose exec web ./manage.py test "$1" --keepdb
