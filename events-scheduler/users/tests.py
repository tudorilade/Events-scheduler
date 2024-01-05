import datetime
from unittest.mock import patch

from django.contrib.auth import get_user
from django.urls import reverse
from django.utils import timezone

from events_scheduler.tests import BaseTestClass
from users.models import User, UserVerification
from users.tasks import send_verification_email


class TestCustomLoginView(BaseTestClass):
    """
    Tests class for the custom login view.
    """

    def setUp(self):
        super().setUp()

    def test_dispatch_authenticated(self):
        """
        If user is already logged in, cannot login again, and we redirect him or her to homepage.
        """
        self.client.force_login(self.user)

        response = self.client.get(reverse('custom_login'), follow=True)

        # user redirected to /
        self.assertRedirects(response, '/')

    def test_dispatch_unauthenticated_no_referer(self):
        """
        Unaunthaicated users can login by following the website logic. If HTTP_REFERER header is not set, he or she
        will not be redirected to login page.
        """
        response = self.client.get(reverse('custom_login'), follow=True)

        # user redirected to /
        self.assertRedirects(response, '/')

        response = self.client.get(reverse('custom_login'), HTTP_REFERER='test.com/', follow=True)

        self.assertEqual(response.request['PATH_INFO'], '/users/login/')


class TestCustomLogoutView(BaseTestClass):
    """Test custom logout

    Class responsible for testing the logout view.
    """
    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)


    def test_dispatch_no_referer(self):
        """
        Similar to login, users cannot logout if REFERER header is not set. They will be redirected to homepage.
        """
        response = self.client.get(reverse('custom_logout'), follow=True)

        # user get redirected to homepage
        self.assertRedirects(response, '/')

        user = get_user(self.client)
        # no logout
        self.assertTrue(user.is_authenticated)

        response = self.client.get(reverse('custom_logout'), HTTP_REFERER='some/referer', follow=True)

        user = get_user(self.client)

        # logout is to homepage here
        self.assertEqual(response.request['PATH_INFO'], '/')
        self.assertFalse(user.is_authenticated)


class TestRegistrationUser(BaseTestClass):
    """Test registration

    Test class responsible for testing the registration process of users
    """

    def setUp(self):
        super().setUp()

    @patch('users.views.messages')
    @patch('users.views.send_verification_email.delay')
    def test_register_new_user(self, mock_send_verification, mock_message):
        """
        Tests if user is successfully created.
        """
        form = {
            'email': 'some_email@newemail.com',
            'password': 'Somepass1',
            'confirm_password': 'Somepass1'
        }

        response = self.client.post(reverse('register'), data=form,  HTTP_REFERER='', follow=True)

        self.assertEqual(response.request['PATH_INFO'], reverse('custom_login'))
        self.assertEqual(mock_message.success.call_count, 1)
        self.assertEqual(mock_send_verification.call_count, 1)

        user = User.objects.select_related('verification').filter(email='some_email@newemail.com')
        self.assertTrue(user.exists())
        self.assertEqual(user.count(), 1)
        user = user[0]
        self.assertFalse(user.is_verified)
        self.assertTrue(UserVerification.objects.filter(user=user).exists())


    @patch('users.views.messages')
    @patch('users.views.send_verification_email.delay')
    def test_register_new_user_with_weak_password(self, mock_send_verification, mock_message):
        """
        Testing the creation of a user with a weak password. Expected behavior is:
            - no creation of the user
            - form in the context with field errors
        """
        form = {
            'email': 'some_email@newemail.com',
            'password': 'somepassss',
            'confirm_password': 'somepasssss'
        }

        response = self.client.post(reverse('register'), data=form,  HTTP_REFERER='', follow=True)

        # verifying that it remained on register page
        self.assertEqual(response.request['PATH_INFO'], reverse('register'))
        self.assertEqual(mock_message.success.call_count, 0)
        self.assertEqual(mock_send_verification.call_count, 0)

        # no user created
        user = User.objects.select_related('verification').filter(email='some_email@newemail.com')
        self.assertFalse(user.exists())

        self.assertEqual(len(response.context['form'].errors), 1)


class TestVerifyEmail(BaseTestClass):
    """Test verify email

    Tests the verification process after the email is sent to the user and wants to verify the account.
    """

    def setUp(self):
        super().setUp()

    @patch('users.views.messages')
    @patch('users.views.decrypt_token')
    def test_confirm_email_view_success(self, mock_decrypt_token, mock_message):
        """
        Testing that the confirmation email is successfully received
        """
        token = 'some_token'
        self.admin.is_verified = False
        self.admin.verification.token_email = token
        self.admin.verification.expiration_date_email_token = timezone.now() + datetime.timedelta(hours=1)
        self.admin.verification.save()

        mock_decrypt_token.return_value = token

        url = reverse('confirm_email') + f'?token={token}'
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)

        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_verified)

        self.admin.verification.refresh_from_db()
        self.assertIsNone(self.admin.verification.token_email)
        self.assertIsNone(self.admin.verification.expiration_date_email_token)

        self.assertEqual(mock_message.success.call_count, 1)

    @patch('users.views.send_verification_email.delay')
    @patch('users.views.messages')
    @patch('users.views.decrypt_token')
    def test_confirm_email_view_token_expired(self, mock_decrypt_token, mock_message, mock_send_verification_email):
        """
        Tests if another email is sent to the user with new token and new expiration time.
        """
        token = 'some_token'
        self.admin.is_verified = False
        self.admin.verification.token_email = token
        self.admin.verification.expiration_date_email_token = timezone.now() - datetime.timedelta(hours=1)
        self.admin.verification.save()

        mock_decrypt_token.return_value = token

        url = reverse('confirm_email') + f'?token={token}'
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)

        self.admin.refresh_from_db()
        self.assertFalse(self.admin.is_verified)

        self.admin.verification.refresh_from_db()
        self.assertEqual(mock_send_verification_email.call_count, 1)
        self.assertEqual(mock_message.success.call_count, 1)
        self.assertRedirects(response, reverse('homepage'))

    @patch('users.email.send_mail')
    def test_send_confirmation_email(self, mock_send_email):
        """
        Test if email is sent correctly and tokens generated
        """
        send_verification_email(self.admin.email)

        self.admin.refresh_from_db()
        self.admin.verification.refresh_from_db()

        self.assertEqual(mock_send_email.call_count, 1)

        self.assertIsNotNone(self.admin.verification.token_email)
        self.assertAlmostEqual(
            self.admin.verification.expiration_date_email_token,
            timezone.now() + datetime.timedelta(hours=1),
            delta=datetime.timedelta(seconds=10)
        )


class TestUpdateUserView(BaseTestClass):
    """Test update user

    Test class responsible for testing the UpdateUserView.
    """
    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)

    def test_update_user_success(self):
        """
        Tests if user is successfully updated and set verified on false.
        """
        form_data = {
            'email': 'other@admin.com'
        }

        response = self.client.post(reverse('user_update'), data=form_data)

        self.admin.refresh_from_db()

        # redirects to user_view
        self.assertRedirects(response, reverse('user_view'))

        # email changed and user is unverified
        self.assertEqual(self.admin.email, 'other@admin.com')
        self.assertFalse(self.admin.is_verified)


    def test_update_user_failure(self):
        """
        Tests if user is successfully updated and set verified on false.
        """
        form_data = {
            'email': 'admin@admin.com'
        }

        response = self.client.post(reverse('user_update'), data=form_data)
        form = response.context['form']
        self.admin.refresh_from_db()

        # remains to same page
        self.assertEqual(response.request['PATH_INFO'], reverse('user_update'))

        # user details unchanged
        self.assertEqual(self.admin.email, 'admin@admin.com')
        self.assertTrue(self.admin.is_verified)

        # one error: same email cannot be used to update the user
        self.assertEqual(len(form.errors), 1)
        self.assertIn('Cannot update the account with same email', form.errors['email'])
