from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django.http import Http404
from django.contrib.sites.shortcuts import get_current_site

from account import signals
from account.conf import settings
from account.serializers import SignupSerializer, SignupResponseSerializer, SettingsSerializer
from account.services import SignupService, SettingsService
from account.models import EmailAddress

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
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

class SettingsRestView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        data = self.__data_for_user(request.user)

        settings = SettingsSerializer(data=data, context={'email': data["primary_email_address"].email})
        settings.is_valid()

        return Response(settings.data, status=status.HTTP_200_OK)

    def put(self, request, format=None):
        primary_email_address = EmailAddress.objects.get_primary(request.user)
        
        serializer = SettingsSerializer(data=request.data, 
                                        context={'email': primary_email_address.email})

        if serializer.is_valid():
            if "email" in serializer.data:
                email = serializer.data["email"]
                self.update_email(request.user, email, primary_email_address)

            self.update_account(serializer)

            data = self.__data_for_user(request.user)
            data.pop("primary_email_address", None)

            return Response(data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update_email(self, user, email, primary_email_address, confirm=None):
        SettingsService.update_email(user, email, primary_email_address, confirm)
 
    def update_account(self, serializer):
        fields = {}
        if "timezone" in serializer.data:
            fields["timezone"] = serializer.data["timezone"]
        if "language" in serializer.data:
            fields["language"] = serializer.data["language"]
        if fields:
            account = self.request.user.account
            for k, v in fields.items():
                setattr(account, k, v)
            account.save()

    def __data_for_user(self, user):
        data = {}

        data["primary_email_address"] = EmailAddress.objects.get_primary(user)
        data["email"] = data["primary_email_address"].email
        data["timezone"] = user.account.timezone
        data["language"] = user.account.language

        return data

