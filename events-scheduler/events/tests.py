import datetime
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone

from events.models import Event
from events.utils import EventListUserTypeEnum
from events_scheduler.tests import BaseTestClass


class TestEventCreate(BaseTestClass):

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)

    def test_create_event_success(self):
        """
        Test if the event is successfully created
        """
        form_data = {
            'title': 'some title',
            'description': 'some description',
            'date': timezone.now() + datetime.timedelta(days=20)
        }

        response = self.client.post(reverse('event_create'), data=form_data)

        self.assertRedirects(response, reverse('user_view'))

        event = Event.objects.filter(creator=self.admin, title='some title')

        self.assertTrue(event.exists())
        self.assertTrue(event.count() == 1)

        event = event.first()

        self.assertEqual(event.title, form_data['title'])
        self.assertEqual(event.description, form_data['description'])
        self.assertEqual(event.date, form_data['date'])
        self.assertIsNotNone(event.slug)

    def test_create_event_user_not_verified(self):
        """
        Test if no event is created when a user is unverified and sends appropiate message
        """
        form_data = {
            'title': 'some title',
            'description': 'some description',
            'date': timezone.now() + datetime.timedelta(days=20)
        }
        self.admin.is_verified = False

        response = self.client.post(reverse('event_create'), data=form_data)
        event = Event.objects.filter(creator=self.admin, title='some title')
        form = response.context['form'].errors
        self.assertEqual(response.request['PATH_INFO'], reverse('event_create'))

        self.assertFalse(event.exists())
        self.assertIn(
            'User is not verified. Verify your account in order to create events',
            form['__all__']
        )

    def test_create_event_not_created_in_the_past(self):
        """
        Test if an event gets created in the past. (for now users are not allowed at the moment
         to create events in the past) Users can create only events in the future.
        """
        form_data = {
            'title': 'some title',
            'description': 'some description',
            'date': timezone.now() - datetime.timedelta(days=20)
        }

        response = self.client.post(reverse('event_create'), data=form_data)
        event = Event.objects.filter(creator=self.admin, title='some title')
        form = response.context['form'].errors
        self.assertEqual(response.request['PATH_INFO'], reverse('event_create'))

        self.assertFalse(event.exists())
        self.assertIn(
            'Cannot create events in a past time',
            form['date']
        )


class TestEventUpdate(BaseTestClass):

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)

    def test_update_event_success(self):
        """
        Test if an event gets updated. Users can update only events in the future.
        """
        date = timezone.now() + datetime.timedelta(days=1)
        form_data = {
            'title': 'some title',
            'description': self.event1.description,
            'date': date
        }

        response = self.client.post(reverse('event_update', kwargs={'slug': self.event1.slug}), data=form_data)
        self.event1.refresh_from_db()

        self.assertRedirects(
            response,
            reverse('event_list', kwargs={'all_or_creator': EventListUserTypeEnum.CREATOR.value})
        )
        self.assertEqual(self.event1.title, form_data['title'])
        self.assertEqual(form_data['date'], date)
        self.assertEqual(self.event1.description, form_data['description'])

    def test_update_event_in_the_past(self):
        """
        Test if an event in the past is updated. Expected result is that the updating should not be performed.
        """
        title, description, date = self.event2.title, self.event2.description, self.event2.date
        form_data = {
            'title': 'new title past event',
            'date': timezone.now() + datetime.timedelta(days=20)
        }

        response = self.client.post(reverse('event_update', kwargs={'slug': self.event2.slug}), data=form_data)
        self.event2.refresh_from_db()

        # remain to same page
        self.assertEqual(response.request['PATH_INFO'], reverse('event_update', kwargs={'slug': self.event2.slug}))
        self.assertNotEqual(self.event2.title, form_data['title'])
        self.assertNotEqual(self.event2.date, form_data['date'])
        self.assertEqual(self.event2.title, title)
        self.assertEqual(self.event2.description, description)
        self.assertEqual(self.event2.date, date)

    def test_update_event_with_past_date(self):
        """
        Test if a future event is updated with a past date.
        Expected result is that the updating should not be performed.
        """
        title, description, date = self.event1.title, self.event1.description, self.event1.date
        form_data = {
            'title': 'new title past event',
            'date': timezone.now() - datetime.timedelta(days=1)
        }

        response = self.client.post(reverse('event_update', kwargs={'slug': self.event1.slug}), data=form_data)
        self.event1.refresh_from_db()

        # remain to same page
        self.assertEqual(response.request['PATH_INFO'], reverse('event_update', kwargs={'slug': self.event1.slug}))
        self.assertNotEqual(self.event1.date, form_data['date'])
        self.assertEqual(self.event1.title, title)
        self.assertEqual(self.event1.description, description)
        self.assertEqual(self.event1.date, date)

        form_errors = response.context['form'].errors
        self.assertIn(
            'Cannot update events in a past time',
            form_errors['date']
        )


class TestListView(BaseTestClass):
    def setUp(self):
        super().setUp()

    def test_unauthenticated_user_browse_all_events(self):
        """
        Test if unauthenticated user can browse all future events
        """
        response = self.client.get(reverse('event_list', kwargs={'all_or_creator': EventListUserTypeEnum.ALL.value}))

        object_list = response.context['object_list']

        self.assertEqual(object_list.count(), 3)  # 3 future events and 1 past event. only 3 should be displayed

    @patch('events.views.messages')
    def test_unauthenticated_try_to_access_creator_endpoint(self, mock_messages):
        """
        Test if guests can access creator endpoint. Expected result is a redirect to login page
        """
        response = self.client.get(
            reverse('event_list', kwargs={'all_or_creator': EventListUserTypeEnum.CREATOR.value}),
            HTTP_REFERER='',
            follow=True
        )

        # redirect to login
        self.assertRedirects(response, reverse('custom_login'))

        # no objects
        self.assertIsNone(response.context.get('object_list'))
        self.assertEqual(mock_messages.info.call_count, 1)
        self.assertEqual(
            mock_messages.info.call_args_list[0][0][1],
            'You have to login first in order to see your events'
        )

    def test_authenticated_user_browse_all_events(self):
        """
        Test if authenticated user can browse all events. Expected answer is yes, he or she can
        """
        self.client.force_login(self.admin)
        response = self.client.get(reverse('event_list', kwargs={'all_or_creator': EventListUserTypeEnum.ALL.value}))

        object_list = response.context['object_list']

        self.assertEqual(object_list.count(), 3)  # 3 future events and 1 past event. only 3 should be displayed

    def test_authenticated_user_can_access_creator(self):
        """
        Test if authenticated user can access creator endpoint. Expected result is yes, he or she can
        """
        self.client.force_login(self.admin)
        response = self.client.get(reverse('event_list', kwargs={'all_or_creator': EventListUserTypeEnum.CREATOR.value}))

        self.assertIsNotNone(object_list := response.context.get('object_list'))

        # all events created by the logged user are displayed
        # self.admin has 2 events, one in the future, one passed
        self.assertEqual(object_list.count(), 2)

    def test_raise_404_if_wrong_endpoint_accessed_irrespective_of_user(self):
        response = self.client.get(reverse('event_list', kwargs={'all_or_creator': 'random'}))

        self.assertEqual(response.status_code, 404)

        self.client.force_login(self.admin)
        response = self.client.get(reverse('event_list', kwargs={'all_or_creator': 'random_again'}))

        self.assertEqual(response.status_code, 404)


class TestEventDeleteView(BaseTestClass):
    """
    Test class responsible for testing the deletion of events
    """

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)

    def test_delete_successfully(self):
        """
        Test successful deletion of events
        """
        old_number = Event.objects.all().count()
        response = self.client.post(reverse('event_delete', kwargs={'slug': self.event2.slug}), follow=True)

        self.assertRedirects(
            response,
            reverse('event_list', kwargs={'all_or_creator': EventListUserTypeEnum.CREATOR.value})
        )

        self.assertEqual(Event.objects.all().count(), old_number - 1)  # one is deleted

    def test_delete_others_creator_events(self):
        """
        Users cannot delete events that are not created by themselves
        """
        old_number = Event.objects.all().count()
        response = self.client.post(reverse('event_delete', kwargs={'slug': self.event3.slug}), follow=True)

        self.assertEqual(response.status_code, 404)  # user cannot delete events not belonging to him or her
        self.assertEqual(Event.objects.all().count(), old_number)  # none is deleted

    @patch('events.views.messages')
    def test_cannot_delete_past_events(self, mock_messages):
        old_number = Event.objects.all().count()
        response = self.client.post(reverse('event_delete', kwargs={'slug': self.event2.slug}), follow=True)

        self.assertEqual(response.status_code, 200)  # no redirect

        self.assertIn(
            mock_messages.info.call_args_list[0][0][1],
            'You cannot delete past events'
        )
        self.assertEqual(Event.objects.all().count(), old_number)  # event is not deleted


class TestEventDetailView(BaseTestClass):
    """
    Test class responsible for testing the DetailView of events
    """

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)

    def test_view_details_of_events_successfully_as_guest(self):
        """
        Test if guests can see the details of events.
        """
        self.client.logout()
        response = self.client.get(reverse('event_detail', kwargs={'slug': self.event2.slug}), follow=True)

        self.assertEqual(response.status_code, 200)

        context = response.context

        # joined is displayed only for authenticated user. In UI is displayed informative message for guests
        self.assertIsNone(context.get('joined'))

    def test_view_details_of_events_successfully_as_authenticated_user(self):
        """
        Test if authenticated users see the details and that the user did not join this event
        """
        response = self.client.get(reverse('event_detail', kwargs={'slug': self.event2.slug}), follow=True)

        self.assertEqual(response.status_code, 200)

        context = response.context

        # this user is not joined to this event so joined is set to False
        self.assertIsNotNone(joined := context.get('joined'))
        self.assertFalse(joined)

    def test_view_details_of_joined_events_successfully_as_authenticated_user(self):
        """
        Test if authenticated users see the details and that the user joined this event
        """
        response = self.client.get(reverse('event_detail', kwargs={'slug': self.event1.slug}), follow=True)

        self.assertEqual(response.status_code, 200)

        context = response.context

        # this user is not joined to this event so joined is set to False
        self.assertIsNotNone(joined := context.get('joined'))
        self.assertTrue(joined)


class TestJoinEvents(BaseTestClass):
    """
    Test class responsible for testing if users can join to events
    """

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)

    @patch('events.views.messages')
    def test_user_join_to_event(self, mock_messages):
        """
        Tests if user successfully joined to the event
        """
        initial_number = self.event2.participants_count
        response = self.client.post(reverse('event_join', kwargs={'slug': self.event2.slug}), follow=True)

        self.assertRedirects(
            response,
            reverse('event_list', kwargs={'all_or_creator': EventListUserTypeEnum.ALL.value})
        )

        self.event2.refresh_from_db()
        qs = self.event2.participants.filter(id=self.admin.id)

        self.assertEqual(self.event2.participants_count, initial_number + 1)  # 2 participants to the event
        self.assertTrue(qs.exists())  # it successfully joined
        self.assertEqual(qs.count(), 1)  # only once
        self.assertEqual(
            mock_messages.success.call_args_list[0][0][1],
            f'You have successfully joined to event: {self.event2}'
        )

    @patch('events.views.messages')
    def test_user_cannot_join_to_same_event_twice(self, mock_messages):
        """
        Tests if user can join to same event twice. Expected result is no, he or she cannot.
        """
        response = self.client.post(reverse('event_join', kwargs={'slug': self.event3.slug}), follow=True)

        self.assertRedirects(
            response,
            reverse('event_list', kwargs={'all_or_creator': EventListUserTypeEnum.ALL.value})
        )

        self.event3.refresh_from_db()
        qs = self.event3.participants.filter(id=self.admin.id)

        self.assertEqual(self.event3.participants_count, 1)  # 1 participants to the event
        self.assertTrue(qs.exists())  # he or she still goes to the event
        self.assertEqual(qs.count(), 1)  # only one registration
        self.assertEqual(
            mock_messages.success.call_args_list[0][0][1],
            f'You have successfully joined to event: {self.event3}'
        )

    def test_user_cannot_join_to_unkown_event(self):
        """
        Tests if user can join unkown events. Expected result is no, he or she cannot.
        """
        response = self.client.post(reverse('event_join', kwargs={'slug': 'random'}), follow=True)

        self.assertEqual(response.status_code, 404)


class TestWithdrawEvents(BaseTestClass):
    """
    Test class responsible for testing if users can withdraw from events
    """

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)

    @patch('events.views.messages')
    def test_user_withdraw_from_event(self, mock_messages):
        """
        Tests if user successfully withdrawn from the event
        """
        initial_number = self.event1.participants_count
        response = self.client.post(reverse('event_withdraw', kwargs={'slug': self.event1.slug}), follow=True)
        self.assertRedirects(
            response,
            reverse('event_list', kwargs={'all_or_creator': EventListUserTypeEnum.ALL.value})
        )

        self.event1.refresh_from_db()
        qs = self.event1.participants.filter(id=self.admin.id)

        self.assertEqual(self.event1.participants_count, initial_number - 1)  # 1 participant remained to the event
        self.assertFalse(qs.exists())  # it successfully joined
        self.assertEqual(
            mock_messages.success.call_args_list[0][0][1],
            f'You have successfully withdrawn from the event: {self.event1}'
        )

    @patch('events.views.messages')
    def test_user_cannot_withdraw_from_same_event_twice(self, mock_messages):
        """
        Tests if user can withdraw from same event twice. Expected result is no, he or she cannot.
        """
        initial_number = self.event2.participants_count
        response = self.client.post(reverse('event_withdraw', kwargs={'slug': self.event2.slug}), follow=True)

        self.assertRedirects(
            response,
            reverse('event_list', kwargs={'all_or_creator': EventListUserTypeEnum.ALL.value})
        )

        self.event2.refresh_from_db()
        qs = self.event2.participants.filter(id=self.admin.id)

        self.assertEqual(self.event2.participants_count, initial_number)  # number of participants unaffacted
        self.assertFalse(qs.exists())  # he or she is not going to the event
        self.assertEqual(
            mock_messages.success.call_args_list[0][0][1],
            f'You have successfully withdrawn from the event: {self.event2}'
        )

    def test_user_cannot_withdraw_from_unkown_event(self):
        """
        Tests if user can withdraw from unkown event. Expected result is a not found error.
        """
        response = self.client.post(reverse('event_withdraw', kwargs={'slug': 'random'}), follow=True)

        self.assertEqual(response.status_code, 404)
