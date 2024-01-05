import re

from django.core.exceptions import ValidationError


class CustomPasswordValidator:
    """Password validator

    Custom validator to enforce security of the passwords. The password shall:
        - have a minimum length of 8
        - not be common
        - have at least 1 upper case
        - have at least 1 lower case
        - have at least 1 digit
    """

    def validate(self, password: str, user: None=None) -> None:
        """
        Method responsible for validating the password

        Args:
            password (str): users password

        Raises:
            ValidationError: validation error if the password does not comply with constraints
        """
        if not re.findall(r'[A-Z]', password):
            raise ValidationError('The password must contain at least 1 uppercase letter.')
        if not re.findall(r'[a-z]', password):
            raise ValidationError('The password must contain at least 1 lowercase letter.')
        if not re.findall(r'[0-9]', password):
            raise ValidationError('The password must contain at least 1 digit.')

    def get_help_text(self) -> str:
        """
        Method responsible for returning a helping text
        """
        return 'Your password must contain at least 1 uppercase letter, 1 lowercase letter and 1 digit'
