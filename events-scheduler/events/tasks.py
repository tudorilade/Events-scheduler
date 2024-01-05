from celery import group

from events.models import Event
from events_scheduler.celery import app


@app.task(autoretry_for=(Exception, ), max_retries=3, retry_backoff=True)
def process_events_chunk(start: int, stop: int):
    """Process chunk

    Celery task responsible for processing a chunk of Event starting from start and
    finishing to stop

    Args:
        start(int): starting index of the chunk
        stop(int): stop index of the chunk
    """
    events = Event.objects.prefetch_related('participants').all()[start:stop]
    for event in events:
        event.update_participants_number()


@app.task(autoretry_for=(Exception, ), max_retries=3, retry_backoff=True)
def update_number_of_participants():
    """Update number of participants

    Celery cron task which is responsible for splitting the number of Event in chunks and process
    each chunk individually.
    """
    number_of_events = Event.objects.all().count()
    step = 2000

    tasks = []
    for i in range(0, number_of_events, step):
        tasks.append(process_events_chunk.s(i, i+step))

    job = group(tasks)
    job.apply_async()
