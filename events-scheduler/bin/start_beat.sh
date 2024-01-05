#!/bin/bash

celery -A events_scheduler beat -l INFO
