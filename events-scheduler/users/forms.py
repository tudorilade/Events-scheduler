from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator

from users.models import User


class UserRegistrationForm(forms.ModelForm):
    """User Registration From

    A Django Model Form representing the registration form used for registering new users.
    Validates password strength, checks if confirmed password matches and verifies email format.
    """
    password = forms.CharField(
        widget=forms.PasswordInput,
        help_text='Your password must contain at least 1 uppercase letter, 1 lowercase letter and 1 digit'
    )
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['email']

    def clean_password(self) -> str:
        """
        Method responsible for validating the password. Check validators in settings.py to see the criteria to which
        the password is evaluated.

        Returns:
            cleaned password
        """
        password = self.cleaned_data.get('password')
        if password:
            validate_password(password, self.instance)
        return password

    def clean_confirm_password(self) -> str:
        """
        Method responsible for cleaning the confirm password. If passwords don't match, a validation error
        will be raised

        Returns:
            cleaned confirm password
        """
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')

        if password and password != confirm_password:
            raise forms.ValidationError("Passwords don't match!")

        return confirm_password

    def clean_email(self) -> str:
        """
        Method responsible for cleaning and validate the email. Appropriate error message is returned.

        Returns:
            cleaned email
        """
        email = self.cleaned_data.get('email')
        if email.count('@') != 1:
            self.add_error('email', 'Enter a valid email address. It has multiple @ or none.')

        email_validator = EmailValidator()
        try:
            email_validator(email)
        except ValidationError:
            self.add_error('email', 'Enter a valid email address.')

        return email

    def save(self, commit=True):
        """
        Sets the password to the user instance
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    """User Update Form

    Validates and handles changes in user's email.
    """

    class Meta:
        model = User
        fields = ['email']

    def clean_email(self):
        """
        Method responsible for cleaning the email. If adds an error to email field if
        the form is submitted with the same data.
        """
        email = self.cleaned_data.get('email', '').strip()

        if email == self.instance.email:
            self.add_error('email', 'Cannot update the account with same email')

        return email
