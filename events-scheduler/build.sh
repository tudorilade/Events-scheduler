#!/bin/bash

chmod +x bin/entrypoint.sh bin/start_celery.sh bin/start_beat.sh

(
  pip install --upgrade pip setuptools pip-tools
  pip-compile --generate-hashes --upgrade --annotation-style=line \
		--resolver=backtracking --no-emit-index-url --verbose \
		--output-file requirements.txt pyproject.toml &&
	pip install -r requirements.txt
) ||
{ echo "Installation of requirements have failed. Please revise your setup."; exit 1; }

docker-compose up --build
