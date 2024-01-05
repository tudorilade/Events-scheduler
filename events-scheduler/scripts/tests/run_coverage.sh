#!/bin/sh

#  This command will run all the test of application using custom .coveragerc file
#  It omits files such as migrations, manage.py etc.

docker-compose exec web coverage run --rcfile=.coveragerc manage.py test --keepdb
