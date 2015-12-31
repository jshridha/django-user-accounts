from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from account.conf import settings
from account.validators import Validator
from account.models import SignupCode

class SignupResponseSerializer(serializers.Serializer):
    confirmation_email_sent = serializers.BooleanField(default=False)
    email_confirmation_required = serializers.BooleanField(default=False)

class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(label=_("Username"), max_length=30)
    password = serializers.CharField(label=_("Password"), 
                                     style={'input_type': 'password'})
    password_confirm = serializers.CharField(label=_("Password (again)"), 
                                             style={'input_type': 'password'})
    email = serializers.EmailField(label=_("Email"))
    code = serializers.CharField(max_length=64, required=False)

    def validate_code(self, code):
        self.context["signup_code"] = None
        if code:
            try:
                self.context["signup_code"] = SignupCode.check_code(code)
            except SignupCode.InvalidCode:
                raise serializers.ValidationError(_("The code {code} is invalid.").format(**{"code": code}))

    def validate_username(self, username):
        msg = Validator.clean_username(username)

        if msg:
            raise serializers.ValidationError(msg)

        return username

    def validate_email(self, email):
        msg = Validator.clean_email(email)

        if msg:
            raise serializers.ValidationError(msg)

        return email

    def validate(self, data):
        signup_code = self.context.get("signup_code", None)
        if not settings.ACCOUNT_OPEN_SIGNUP and not signup_code:
            raise serializers.ValidationError(_("Signup is currently closed."))

        if data['password'] > data['password_confirm']:
            msg = Validator.compare_passwords(data["password"], 
                                              data["password_confirm"])

            if msg:
                raise serializers.ValidationError(msg)

        return data

class SettingsSerializer(serializers.Serializer):
    email = serializers.EmailField(label=_("Email"))
    timezone = serializers.ChoiceField(
        label=_("Timezone"),
        choices=[("", "---------")] + settings.ACCOUNT_TIMEZONES,
        required=False,
        allow_blank=True
    )
    if settings.USE_I18N:
        language = serializers.ChoiceField(
            label=_("Language"),
            choices=settings.ACCOUNT_LANGUAGES,
            required=False,
            allow_blank=True
        )

    def validate_email(self, email):
        if self.context.get("email") == email:
            return email

        msg = Validator.clean_email(email)

        if msg:
            raise serializers.ValidationError(msg)

        return email
