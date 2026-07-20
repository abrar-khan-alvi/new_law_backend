"""
Regression tests for the core auth lifecycle (previously zero coverage in
this app):
- registration creates an unverified officer + free subscription.
- login is refused until email is verified.
- email verification via OTP flips the account to verified.
- change-password / password-reset-confirm blacklist prior refresh tokens
  (Phase 2 hardening — a token that leaked, plausibly the reason for the
  reset, must stop working after the reset).
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import EmailOTP
from accounts.otp import generate_otp
from subscriptions.models import Plan

User = get_user_model()


class RegistrationTests(TestCase):
    def setUp(self):
        # accounts.signals.create_free_subscription picks the lowest-priced
        # active plan — without one, it warns and skips, same as every other
        # test file in this repo that exercises user creation.
        Plan.objects.create(name='free', display_name='Free', price_monthly=0)

    def test_register_creates_unverified_officer_with_free_subscription(self):
        client = APIClient()
        resp = client.post('/api/auth/register/', {
            'email': 'newofficer@example.com', 'password': 'S3cure-Pass!23',
            'password2': 'S3cure-Pass!23', 'first_name': 'New', 'last_name': 'Officer',
        }, format='json')
        self.assertEqual(resp.status_code, 201)

        user = User.objects.get(email='newofficer@example.com')
        self.assertEqual(user.role, 'officer')
        self.assertFalse(user.email_verified)
        self.assertTrue(hasattr(user, 'subscription'))
        self.assertEqual(user.subscription.plan.name, 'free')

    def test_password_mismatch_is_rejected(self):
        client = APIClient()
        resp = client.post('/api/auth/register/', {
            'email': 'mismatch@example.com', 'password': 'S3cure-Pass!23',
            'password2': 'Different!23',
        }, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(User.objects.filter(email='mismatch@example.com').exists())


class LoginVerificationGateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(email='gate@example.com', role='officer')
        self.user.set_password('S3cure-Pass!23')
        self.user.save()

    def test_login_refused_until_email_verified(self):
        resp = self.client.post('/api/auth/login/', {
            'email': 'gate@example.com', 'password': 'S3cure-Pass!23',
        }, format='json')
        # CustomTokenObtainPairSerializer.validate() raises a plain
        # ValidationError for this case (not AuthenticationFailed) -> 400.
        self.assertEqual(resp.status_code, 400)

    def test_login_succeeds_once_verified(self):
        self.user.email_verified = True
        self.user.save(update_fields=['email_verified'])
        resp = self.client.post('/api/auth/login/', {
            'email': 'gate@example.com', 'password': 'S3cure-Pass!23',
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)


class EmailVerificationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(email='verify@example.com', role='officer')

    def test_correct_code_verifies_account(self):
        code = generate_otp(self.user, EmailOTP.Purpose.EMAIL_VERIFICATION)
        resp = self.client.post('/api/auth/verify-email/', {
            'email': 'verify@example.com', 'code': code,
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

    def test_wrong_code_is_rejected(self):
        generate_otp(self.user, EmailOTP.Purpose.EMAIL_VERIFICATION)
        resp = self.client.post('/api/auth/verify-email/', {
            'email': 'verify@example.com', 'code': '000000',
        }, format='json')
        self.assertEqual(resp.status_code, 400)
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)


class TokenRevocationTests(TestCase):
    """Phase 2: password change/reset must blacklist outstanding refresh tokens."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(email='revoke@example.com', role='officer', email_verified=True)
        self.user.set_password('OldPass!2345')
        self.user.save()

        login = self.client.post('/api/auth/login/', {
            'email': 'revoke@example.com', 'password': 'OldPass!2345',
        }, format='json')
        self.refresh_token = login.data['refresh']
        self.access_token = login.data['access']

    def _refresh_still_works(self):
        resp = self.client.post('/api/auth/token/refresh/', {'refresh': self.refresh_token}, format='json')
        return resp.status_code == 200

    def test_change_password_blacklists_prior_refresh_token(self):
        self.assertTrue(self._refresh_still_works())

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        resp = self.client.post('/api/auth/change-password/', {
            'old_password': 'OldPass!2345', 'new_password': 'NewPass!6789',
        }, format='json')
        self.assertEqual(resp.status_code, 200)

        self.assertFalse(self._refresh_still_works())

    def test_password_reset_confirm_blacklists_prior_refresh_token(self):
        self.assertTrue(self._refresh_still_works())

        code = generate_otp(self.user, EmailOTP.Purpose.PASSWORD_RESET)
        resp = self.client.post('/api/auth/password-reset/confirm/', {
            'email': 'revoke@example.com', 'code': code, 'new_password': 'NewPass!6789',
        }, format='json')
        self.assertEqual(resp.status_code, 200)

        self.assertFalse(self._refresh_still_works())
