import datetime

from django.test import TestCase, Client
from django.utils import timezone

from events_scheduler.utils import unique_slugify
from users.models import User, UserVerification
from events.models import Event


class BaseTestClass(TestCase):
    """Base Test class

    Base test class responsible for setting the environment for testing by pre-populating the database with
    information about users, events etc.
    """
    def setUp(self):
        self.client = Client()

        # create some users
        self.admin = User.objects.create_user(
            email='admin@admin.com', password='pass', slug=unique_slugify('admin')
        )
        self.user = User.objects.create_user(
            email='user@user.com', password='pass', slug=unique_slugify('user')
        )
        self.user_verification = UserVerification.objects.create(user=self.user)
        self.admin_verification = UserVerification.objects.create(user=self.admin)

        self.admin.is_verified = True
        self.user.is_verified = True

        # create some events
        self.event1 = Event.objects.prefetch_related('participants').create(
            title='title1', description='descri1', slug=unique_slugify('title1'),
            date=timezone.now() + datetime.timedelta(days=5), creator=self.admin
        )
        self.event2 = Event.objects.prefetch_related('participants').create(
            title='title2', description='descri2', slug=unique_slugify('title2'),
            date=timezone.now() + datetime.timedelta(days=-3), creator=self.admin
        )
        self.event3 = Event.objects.prefetch_related('participants').create(
            title='title3', description='descri3', slug=unique_slugify('title3'),
            date=timezone.now() + datetime.timedelta(days=10), creator=self.user
        )
        self.event4 = Event.objects.prefetch_related('participants').create(
            title='title4', description='descri4', slug=unique_slugify('title4'),
            date=timezone.now() + datetime.timedelta(days=2), creator=self.user
        )

        self.event1.participants.add(self.admin)
        self.event1.participants.add(self.user)
        self.event2.participants.add(self.user)
        self.event3.participants.add(self.admin)

        self.event1.update_participants_number()
        self.event2.update_participants_number()
        self.event3.update_participants_number()
