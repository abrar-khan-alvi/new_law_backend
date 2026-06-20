from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """
    Token for confirming a user's email address.
    Including `email_verified` in the hash invalidates the token once used.
    """

    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{timestamp}{user.email_verified}"


email_verification_token = EmailVerificationTokenGenerator()
# Password reset uses Django's built-in default_token_generator, which already
# invalidates when the password (or last_login) changes.
