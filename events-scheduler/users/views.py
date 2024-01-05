import binascii

from cryptography.fernet import InvalidToken
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, HttpRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, UpdateView

from events_scheduler.limiters import RateLimitedView
from events_scheduler.utils import decrypt_token, unique_slugify
from users.forms import UserRegistrationForm, UserUpdateForm
from users.models import UserVerification, User
from users.tasks import send_verification_email


class CustomLoginView(RateLimitedView, LoginView):

    def dispatch(self, request, *args, **kwargs):
        """
        Users cannot access login page if they are authenticated by simply accessing in browser the login endpoint.
        It applies to anonymous users as well.
        As a result, they will be redirected to homepage.
        """
        if request.user.is_authenticated:
            return redirect(request.META.get('HTTP_REFERER', '/'))

        if not request.user.is_authenticated and 'HTTP_REFERER' not in request.META:
            return redirect('/')

        return super().dispatch(request, *args, **kwargs)


class CustomLogoutView(RateLimitedView, LoginRequiredMixin, LogoutView):

    def dispatch(self, request, *args, **kwargs):
        """
        Users cannot logout by simply accessing in browser the logout endpoint.
        As a result, they will be redirected to homepage.
        """
        if 'HTTP_REFERER' not in request.META:
            return redirect('/')

        return super().dispatch(request, *args, **kwargs)


class RegisterView(RateLimitedView, CreateView):
    """Register view

    A Django CreateView with IP-based rate limiting, responsible for registering new users.
    """
    form_class = UserRegistrationForm

    def dispatch(self, request, *args, **kwargs):
        """
        Users cannot access register page by simply accessing in browser the register endpoint.
        As a result, they will be redirected to homepage.
        """
        if 'HTTP_REFERER' not in request.META:
            return redirect('/')

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: UserRegistrationForm) -> HttpResponseRedirect:
        """
        Method responsible for sending verification email when the form is valid and user ready to be created.

        Args:
            form (UserRegistrationForm): a UserRegistrationForm instance having all the details of the new user.

        Returns:
            HttpResponseRedirect: redirects to login page
        """
        user = form.save(commit=False)
        user.slug = unique_slugify(user.__str__())
        user.save()
        UserVerification.objects.create(user=user)
        send_verification_email.delay(user.email)
        return super().form_valid(form)

    def get_success_url(self):
        """
        Method responsible for sending informative message regarding the successful registration of the user

        Returns:
            reversed path to login page
        """
        messages.success(
            self.request,
            'Congratulations! Your registration has been successful. We have sent you a verification email'
            ' with instructions to validate your email'
        )
        return reverse('custom_login')


class ConfirmEmailView(RateLimitedView, View):
    """Confirm Email View

    A Django View class responsible for email validation based on a token and updates the
    user model accordingly.
    """

    def get(self, request, *args, **kwargs):
        """
        Handles GET request, validates token, updates user verification status, and redirects to homepage.

        Args:
            request: The request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            HttpResponseRedirect: Redirect to the homepage
        """
        token = request.GET.get('token')

        # check if token is valid
        user_verification = self.check_token_is_valid(request, token)
        if not isinstance(user_verification, UserVerification):
            return user_verification

        user = user_verification.user

        # token is valid and not expired
        user.is_verified = True
        user_verification.token_email = None
        user_verification.expiration_date_email_token = None
        user_verification.save(update_fields=['token_email', 'expiration_date_email_token'])
        messages.success(
            request,
            'We have successfully validated your email. Now you can create events !'
        )
        return redirect('homepage')

    def check_token_is_valid(
            self, request: HttpRequest, token: str
    ) -> HttpResponseRedirect | UserVerification:
        """
        Validates the token by decryption and comparison with database, raises exception if invalid.

        Args:
            request (HttpRequest): The request object.
            token (str): The encrypted token string.

        Returns:
            HttpResponseRedirect: In case token has expired, it redirects to homepage
            user_verification (UserVerification): UserVerification in case of valid token

        Raises:
            PermissionDenied: In case token is invalid.
        """
        if not token:
            raise PermissionDenied

        try:
            decrypted_token = decrypt_token(token, settings.ENCRYPT_KEY)
        except (InvalidToken, binascii.Error):
            raise PermissionDenied

        try:
            user_verification = UserVerification.objects.select_related('user').get(token_email=decrypted_token)
        except UserVerification.DoesNotExist:
            raise PermissionDenied

        response = self.check_token_expiration(request, user_verification)
        if response is not True:
            return response

        return user_verification

    def check_token_expiration(
            self, request: HttpRequest, user_verification: UserVerification
    ) -> HttpResponseRedirect | bool:
        """
        Method responsible for checking the expiration of the token. If token is expired, it sends again
        a confirmation email and redirects to homepage.

        Args:
            request (HttpRequest): The request object.
            user_verification (UserVerification): The UserVerification instance for the user.

        Returns:
            HttpResponseRedirect | True: Redirect to homepage if expired or True if it is not expired
        """
        if user_verification.is_email_token_expired():
            send_verification_email.delay(user_verification.user.email)
            message = 'Unfortunately, your token is expired. We have sent you another verification email.'
            messages.success(request, message)
            return redirect('homepage')

        return True


class SendConfirmationEmail(RateLimitedView, LoginRequiredMixin):
    """Send confirmation email

    A Django View responsible for sending a confirmation email in case the sending of email failed at registration time
    (e.g. incorrect email, and it could not be sent) or after the user has updated the email and has to verify the
    updated email again.
    """
    def get(self, request, *args, **kwargs) -> HttpResponseRedirect:
        """Get

        Method responsible for handling GET request by sending a verification email to the authenticated user.

        Args:
            request: the HttpRequest instance

        Returns:
            HttpResponseRedirect: redirects to the user dashboard
        """
        send_verification_email.delay(self.request.user.email)
        message = 'We have sent you a verification email with instructions to verify your email !'
        messages.success(request, message)
        return redirect('user_view')


class UserDetailView(RateLimitedView, LoginRequiredMixin, DetailView):
    """User Detail View

    A Django Detail View class responsible for displaying information about the logged user on View Profile
    dashboard.
    """
    model = User

    def get_object(self, queryset=None) -> User:
        """
        Method responsible for setting the object which DetailView is going to display
        """
        return self.request.user


class UserUpdateView(RateLimitedView, LoginRequiredMixin, UpdateView):
    """UserUpdateView

    A Django UpdateView class with IP-based rate limiting and user authentication. This view is responsible
    for updating the profile of the user. The user can update his or her email. Once an email is updated, it needs
    to be verified again.

    Attributes:
        model (User): User model corresponding to UpdateView
        form_class (UserUpdateForm): The form used for updating the user
    """
    model = User
    form_class = UserUpdateForm

    def get_object(self, queryset=None) -> User:
        """
        Sets the object as authenticated user
        """
        return self.request.user

    def form_valid(self, form: UserUpdateForm) -> HttpResponseRedirect:
        """Form Valid

        Method responsible for finalizing the update of the user. It unverify the user if form has valid data.

        Args:
            form (UserUpdateForm): an instance of UserUpdateForm with valid data

        Returns:
            HttpResponseRedirect: redirects to user_view endpoint with a success message
        """
        user = form.save(commit=False)
        user.is_verified = False
        user.save()
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """
        Method responsible for displaying success message once the form has been validated
        """
        messages.success(
            self.request,
            'Your profile has been successfully updated !'
        )
        return reverse('user_view')
