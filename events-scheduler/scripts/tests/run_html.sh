#!/bin/sh

#  Generates the html with the coverage report in events_coverage dir.

docker-compose exec web coverage html --rcfile=.coveragerc
