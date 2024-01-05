import datetime
import secrets

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from events_scheduler.utils import encrypt_token
from users.models import User


class EmailVerification:
    """Email verification class

    Class responsible for sending a verification email to a user using the registered email

    Attributes:
        user (User): user instance used for accessing user verification to store the token and expiration time
    """
    def __init__(self, user: User):
        """Initializes the EmailVerification class with a User instance

            Args:
                user (User): The User instance to verify
        """
        self.user: User = user
        self.html: str = 'users/email.html'

    def generate_encrypted_key(self) -> str:
        """Generates and saves an encrypted key for the User

        Returns:
            str: The encrypted key as a string
        """
        email_token = secrets.token_hex(128)
        self.user.verification.token_email = email_token
        self.user.verification.expiration_date_email_token = timezone.now() + datetime.timedelta(hours=1)
        self.user.verification.save(update_fields=[
                'token_email', 'expiration_date_email_token'
            ]
        )
        return encrypt_token(email_token, settings.ENCRYPT_KEY)

    def prepare_html_context(self) -> str:
        """Prepares the HTML context for the verification email

        Returns:
            str: The rendered HTML as a string
        """
        token = self.generate_encrypted_key()
        context = {
            'title': 'Verification email',
            'header': 'User validation',
            'instruction_message': 'Please click the below button to activate your account',
            'link': f'{settings.CONFIRMATION_EMAIL_LINK}{token}',
            'action_message': 'Validate your account ',
            'extra_info': 'No reply'
        }
        html_message = render_to_string(self.html, context)
        return html_message

    def send_verification_email(self) -> None:
        """Sends the verification email to the user

        The email includes a token that the user can use to verify their account.
        """
        html_message = self.prepare_html_context()
        send_mail(
            subject="Validate your email",
            message="Reset password. See the HTML for further information",
            from_email=None,  # user default email specified in settings.py
            recipient_list=[self.user.email],
            html_message=html_message,
            fail_silently=False,
        )
