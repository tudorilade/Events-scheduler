import datetime
import random

from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from django.utils import timezone

from events_scheduler.utils import unique_slugify
from users.models import User
from events.models import Event


class Command(BaseCommand):

    def handle(self, *args, **options):

        users = list(User.objects.all())

        self.stdout.write(self.style.SUCCESS(f'Creating events...'))
        for i in range(100000):
            title = f'{get_random_string(10)}'
            description = f'{get_random_string(30)}'
            date = timezone.now() + datetime.timedelta(days=random.randint(-300, 500))
            slug = unique_slugify(title)
            user = random.choice(users)
            event = Event.objects.prefetch_related('participants').create(
                title=title, description=description, slug=slug, date=date, creator=user
            )
            if i % 1000 == 0:
                self.stdout.write(self.style.SUCCESS(f'Iteration: {i}'))

            number_of_participants = random.randint(0, 1000)
            for _ in range(number_of_participants):
                user_rand = random.choice(users)
                event.participants.add(user_rand)

            event.update_participants_number()

        self.stdout.write(self.style.SUCCESS(f'Events created...'))
