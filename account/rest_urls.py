from __future__ import unicode_literals

from django.conf.urls import url

from account.rest_views import AccountDeleteRestView, SignupRestView
from account.rest_views import SignupCodeRestView, SettingsRestView

urlpatterns = [
    url(r"^signup$", SignupRestView.as_view(), name="account_signup_api"),

    url(r"^invite$", SignupCodeRestView.as_view(), name="account_invite_api"),

    url(r"^settings$", SettingsRestView.as_view(), name="account_settings_api"),
    url(r"^delete$", AccountDeleteRestView.as_view(), name="account_delete_api"),
]
