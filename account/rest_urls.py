from __future__ import unicode_literals

from django.conf.urls import url

from account.rest_views import AccountRestView, SignupRestView, SettingsRestView

urlpatterns = [
    url(r"^account/signup$", SignupRestView.as_view(), name="account_signup_api"),
    url(r"^account/settings$", SettingsRestView.as_view(), name="account_settings_api"),
    url(r"^account/$", AccountRestView.as_view(), name="account_delete_api"),
]
