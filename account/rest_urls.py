from __future__ import unicode_literals

from django.conf.urls import url

from account.rest_views import SignupRestView

urlpatterns = [
    url(r"^signup/$", SignupRestView.as_view(), name="account_signup_api"),
]
