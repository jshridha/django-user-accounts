from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from django.contrib.auth.models import User

from account.models import Account, EmailAddress, SignupCode
from account.services import SignupService

class RESTSignupViewTestCase(APITestCase):

    def test_post(self):
        """
        Ensure we can create a new account object.
        """
        url = reverse('account_signup_api')
        data = {
            "username": "foo",
            "password": "bar",
            "password_confirm": "bar",
            "email": "foobar@example.com",
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.data["confirmation_email_sent"], True)
        self.assertEqual(response.data["email_confirmation_required"], False)

        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, 'foo')

        self.assertEqual(Account.objects.count(), 1)
        self.assertEqual(Account.objects.get().user.username, 'foo')

        self.assertEqual(EmailAddress.objects.count(), 1)
        self.assertEqual(EmailAddress.objects.get().email, 'foobar@example.com')
        self.assertEqual(EmailAddress.objects.get().user.username, 'foo')
        self.assertEqual(EmailAddress.objects.get().verified, False)

    def test_closed(self):
        with self.settings(ACCOUNT_OPEN_SIGNUP=False):
            url = reverse('account_signup_api')
            data = {
                "username": "foo",
                "password": "bar",
                "password_confirm": "bar",
                "email": "foobar@example.com",
            }
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data, {"non_field_errors":["Signup is currently closed."]})

    def test_email_validation_required(self):
        with self.settings(ACCOUNT_EMAIL_CONFIRMATION_REQUIRED=True):
            url = reverse('account_signup_api')
            data = {
                "username": "foo",
                "password": "bar",
                "password_confirm": "bar",
                "email": "foobar@example.com",
            }
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            self.assertEqual(response.data["confirmation_email_sent"], True)
            self.assertEqual(response.data["email_confirmation_required"], True)

            self.assertEqual(EmailAddress.objects.get().verified, False)

    def test_no_email_confirmation(self):
        with self.settings(ACCOUNT_EMAIL_CONFIRMATION_EMAIL=False):
            url = reverse('account_signup_api')
            data = {
                "username": "foo",
                "password": "bar",
                "password_confirm": "bar",
                "email": "foobar@example.com",
            }
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            self.assertEqual(response.data["confirmation_email_sent"], False)
            self.assertEqual(response.data["email_confirmation_required"], False)

            self.assertEqual(EmailAddress.objects.get().verified, False)

    def test_valid_code(self):
        signup_code = SignupCode.create()
        signup_code.save()
        with self.settings(ACCOUNT_OPEN_SIGNUP=False):
            url = reverse('account_signup_api')
            data = {
                "username": "foo",
                "password": "bar",
                "password_confirm": "bar",
                "email": "foobar@example.com",
                "code": signup_code.code,
            }
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            self.assertEqual(response.data["confirmation_email_sent"], True)
            self.assertEqual(response.data["email_confirmation_required"], False)

            self.assertEqual(EmailAddress.objects.get().verified, False)

    def test_valid_code_verified_email(self):
        signup_code = SignupCode.create()
        signup_code.email = "foobar@example.com"
        signup_code.save()
        with self.settings(ACCOUNT_OPEN_SIGNUP=False):
            url = reverse('account_signup_api')
            data = {
                "username": "foo",
                "password": "bar",
                "password_confirm": "bar",
                "email": "foobar@example.com",
                "code": signup_code.code,
            }
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            self.assertEqual(response.data["confirmation_email_sent"], False)
            self.assertEqual(response.data["email_confirmation_required"], False)

            self.assertEqual(EmailAddress.objects.count(), 1)
            self.assertEqual(EmailAddress.objects.get().email, 'foobar@example.com')
            self.assertEqual(EmailAddress.objects.get().verified, True)
            self.assertEqual(EmailAddress.objects.get().user.username, 'foo')

    def test_invalid_code(self):
        with self.settings(ACCOUNT_OPEN_SIGNUP=False):
            url = reverse('account_signup_api')
            data = {
                "username": "foo",
                "password": "bar",
                "password_confirm": "bar",
                "email": "foobar@example.com",
                "code": "abc123",
            }
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data, {"code":['The code abc123 is invalid.']})

class RESTSettingsViewTestCase(APITestCase):
    def test_get_not_logged_in(self):
        url = reverse('account_settings_api')

        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get(self):
        SignupService.signup('foo', 'foobar@example.com', 'bar')
        url = reverse('account_settings_api')
        user = User.objects.get(username='foo')
        self.client.force_authenticate(user=user)

        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], 'foobar@example.com')
        self.assertEqual(response.data["language"], 'en-us')

    def test_put(self):
        SignupService.signup('foo', 'foobar@example.com', 'bar')
        url = reverse('account_settings_api')
        user = User.objects.get(username='foo')
        self.client.force_authenticate(user=user)

        data = {
            "email": "foobar@example.com",
            "timezone": "America/Vancouver",
            "language": "it"
        }

        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], 'foobar@example.com')
        self.assertEqual(response.data["timezone"], 'America/Vancouver')
        self.assertEqual(response.data["language"], 'it')

    def test_put_email_conflict(self):
        SignupService.signup('foo', 'foobar@example.com', 'bar')
        SignupService.signup('foo2', 'foobar2@example.com', 'bar')
        url = reverse('account_settings_api')
        user = User.objects.get(username='foo')
        self.client.force_authenticate(user=user)

        data = {
            "email": "foobar2@example.com",
        }

        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_invalid_timezone(self):
        SignupService.signup('foo', 'foobar@example.com', 'bar')
        url = reverse('account_settings_api')
        user = User.objects.get(username='foo')
        self.client.force_authenticate(user=user)

        data = {
            "email": "foobar@example.com",
            "timezone": "NOT_A_TIMEZONE",
        }

        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'timezone': [u'"NOT_A_TIMEZONE" is not a valid choice.']})

    def test_put_invalid_language(self):
        SignupService.signup('foo', 'foobar@example.com', 'bar')
        url = reverse('account_settings_api')
        user = User.objects.get(username='foo')
        self.client.force_authenticate(user=user)

        data = {
            "email": "foobar@example.com",
            "language": "NOT_A_LANGUAGE"
        }

        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'language': [u'"NOT_A_LANGUAGE" is not a valid choice.']})
        
