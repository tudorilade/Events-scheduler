from typing import Optional, Dict, Any

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """User manager

    Custom manager used for handling the creation of users and superusers.
    """
    def _create_user(self, email: Optional[str], password: Optional[str], **extra_fields: Dict[Any, Any]) -> "User":
        """Create User

        Method responsible for creating a new user and save it to database having email and password. If
        user is superuser, it creates an UserVerification entry as well.

        Args:
            email (str): the email user has entered at registration step
            password (str): entered password

        Returns:
            user (User): the new instance of user created and saved on database

        Raises:
            ValueError: in case email and password were not provided
        """
        if not email:
            raise ValueError('The Email field must be set')

        if not password:
            raise ValueError('The Password field must be set')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        if user.is_superuser:
            UserVerification.objects.create(user=user)

        return user

    def create_user(
            self, email: str, password: Optional[str] = None, **extra_fields
    ) -> "User":
        """Create User

        Method responsible for creating a normal user
        """
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(
            self, email: str, password: Optional[str] = None, **extra_fields
    ) -> "User":
        """Create superuser

        Method responsible for creating a superuser
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('_is_user_verified', True)
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom User

    Custom user which overwrites the behavior of AbstractUser. It enables registration / login based
    on email. The email must be a valid.
    """
    username = None
    email = models.EmailField(unique=True, verbose_name='Email', db_index=True)
    registration_date = models.DateTimeField(auto_now_add=True, verbose_name='Registration date')
    _is_user_verified = models.BooleanField(default=False, verbose_name='User verified')
    slug = models.SlugField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self) -> str:
        """Representation of user

        Magic method responsible for displaying a user based on his or her email

        Returns:
            first part of the email before @
        """
        return self.email.split('@')[0]

    @property
    def is_verified(self) -> bool:
        """Verified

        Method responsible for determining whether the user has been verified or not

        Returns:
            True - if email is verified. False otherwise.
        """
        return self._is_user_verified

    @is_verified.setter
    def is_verified(self, verified: bool) -> None:
        """Sets the _is_user_verified property

        Args:
            verified (bool): Value to set the _is_user_verified property
        """
        self._is_user_verified = verified
        self.save(update_fields=['_is_user_verified'])


class UserVerification(models.Model):
    """Verification

    This model is used for validation purpose of the user. It is used to store expiration tokens in the
    process of:
        - verify the email
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification')
    token_email = models.CharField(max_length=256, blank=True, null=True)
    expiration_date_email_token = models.DateTimeField(blank=True, null=True)

    def is_email_token_expired(self) -> bool:
        """
        Method responsible for determining if the email token is expired or not
        """
        if self.expiration_date_email_token:
            return self.expiration_date_email_token < timezone.now()

        return True

    def is_reset_password_token_expired(self) -> bool:
        """
        Method responsible for determining if the reset password email token is expired or not
        """
        if self.expiration_date_reset_password_token:
            return self.expiration_date_reset_password_token < timezone.now()

        return True
