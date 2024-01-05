from events_scheduler.celery import app
from users.email import EmailVerification
from users.models import User


@app.task(autoretry_for=(Exception, ), max_retries=3, retry_backoff=True)
def send_verification_email(email: str) -> None:
    """Send verification email

    Celery task responsible for sending a verification mail to registered user using
    the registered email. In case of failure, it retries 3 times.

    Args:
        email (str): recipient of verification email
    """
    user = User.objects.select_related('verification').get(email=email)
    EmailVerification(user).send_verification_email()
