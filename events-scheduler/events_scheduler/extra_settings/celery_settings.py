from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'update-number-of-participants': {
        'task': 'events.tasks.update_number_of_participants',
        'schedule': crontab(minute='*/30'),
    },
}
