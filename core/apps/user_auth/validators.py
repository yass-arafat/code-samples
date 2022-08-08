import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class MaximumLengthValidator:
    """Checks if password is longer than expected maximum length"""

    def __init__(self, max_length=20):
        self.max_length = max_length

    def validate(self, password, user=None):
        if len(password) > self.max_length:
            raise ValidationError(
                _("This password must contain at least %(max_length)d characters."),
                code="password_too_long",
                params={"max_length": self.max_length},
            )

    def get_help_text(self):
        return _(
            "Your password can not contain more than %(max_length)d characters."
            % {"max_length": self.max_length}
        )


class SymbolValidator(object):
    """Checks if the password contains at least one of the required symbols"""

    def validate(self, password, user=None):
        if not re.findall("[#?!@$%^&*-]", password):
            raise ValidationError(
                _("The password must contain at least 1 symbol: " + "#?!@$%^&*-"),
                code="password_no_symbol",
            )

    def get_help_text(self):
        return _("Your password must contain at least 1 symbol: " + "#?!@$%^&*-")


class UppercaseValidator(object):
    """Checks if the password contains at least one uppercase letter"""

    def validate(self, password, user=None):
        if not re.findall("[A-Z]", password):
            raise ValidationError(
                _("The password must contain at least 1 uppercase letter, A-Z."),
                code="password_no_upper",
            )

    def get_help_text(self):
        return _("Your password must contain at least 1 uppercase letter, A-Z.")
