#!/bin/bash

celery -A events_scheduler worker -l INFO
