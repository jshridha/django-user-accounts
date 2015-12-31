from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django.http import Http404
from django.contrib.sites.shortcuts import get_current_site

from account import signals
from account.conf import settings
from account.serializers import SignupSerializer, SignupResponseSerializer
from account.services import SignupService

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

class SignupRestView(APIView):
    """
    Enable users to signup for an account through a REST api
    """
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        serializer = SignupSerializer(data=request.data)
        
        if serializer.is_valid():
            username = serializer.data["username"]
            email = serializer.data["email"]
            password = serializer.data["password"]
            signup_code = serializer.context.get("signup_code", None)
            response = {}

            user, email_address = SignupService.signup(username, email, password, 
                                                       signup_code)

            self.after_signup(user, serializer.data)

            if settings.ACCOUNT_EMAIL_CONFIRMATION_EMAIL and not email_address.verified:
                self.__send_email_confirmation(request, email_address)
                response["confirmation_email_sent"] = True

            if settings.ACCOUNT_EMAIL_CONFIRMATION_REQUIRED and not email_address.verified:
                response["email_confirmation_required"] = True

            response = SignupResponseSerializer(data=response)
            response.is_valid()
            return Response(response.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def __send_email_confirmation(self, request, email_address):
        email_address.send_confirmation(site=get_current_site(request))

    def after_signup(self, user, data):
        signals.user_signed_up.send(sender=SignupRestView, user=user, form=data)
