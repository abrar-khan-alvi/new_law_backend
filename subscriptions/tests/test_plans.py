"""
Regression tests for the subscription-plan fixes:
- document_limit / warrant_document_limit are real nullable fields (unlimited),
  not magic numbers, and are independent quota buckets.
- quota reservation is atomic per bucket (closes the check-then-increment race).
- trial start/expiry lifecycle.
- Stripe price IDs are read from the Plan row, not a settings dict.

Users are created before any Plan exists in each test, so the post_save signal
that auto-assigns a free subscription (accounts.signals.create_free_subscription)
finds no active plan and skips — leaving us free to create the Subscription
explicitly with the exact plan/usage state each test needs.
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from subscriptions.models import Plan, Subscription
from subscriptions.tasks import expire_trials

User = get_user_model()


class DocumentLimitTests(TestCase):
    def test_none_means_unlimited(self):
        user = User.objects.create(email='dl@example.com')
        plan = Plan.objects.create(name='t-unlimited', display_name='Unlimited', document_limit=None)
        sub = Subscription.objects.create(user=user, plan=plan, documents_generated_this_month=999_999)
        self.assertTrue(sub.try_reserve_quota('incident_report'))

    def test_numeric_limit_still_enforced(self):
        user = User.objects.create(email='dl2@example.com')
        plan = Plan.objects.create(name='t-limited', display_name='Limited', document_limit=2)
        sub = Subscription.objects.create(user=user, plan=plan, documents_generated_this_month=2)
        self.assertFalse(sub.try_reserve_quota('incident_report'))


class WarrantQuotaBucketTests(TestCase):
    """Incident reports and warrants must draw from independent buckets."""

    def setUp(self):
        self.user = User.objects.create(email='warrant@example.com')
        self.plan = Plan.objects.create(
            name='t-split', display_name='Split', document_limit=5, warrant_document_limit=2,
        )
        self.sub = Subscription.objects.create(user=self.user, plan=self.plan)

    def test_search_and_arrest_warrants_share_one_bucket(self):
        self.assertTrue(self.sub.try_reserve_quota('search_warrant'))
        self.assertTrue(self.sub.try_reserve_quota('arrest_warrant'))
        # Bucket is now at 2/2 — a third warrant of either type must be refused.
        self.assertFalse(self.sub.try_reserve_quota('search_warrant'))
        self.assertFalse(self.sub.try_reserve_quota('arrest_warrant'))

    def test_warrant_usage_does_not_consume_incident_report_quota(self):
        self.sub.try_reserve_quota('search_warrant')
        self.sub.try_reserve_quota('arrest_warrant')
        self.sub.refresh_from_db()
        self.assertEqual(self.sub.warrants_generated_this_month, 2)
        self.assertEqual(self.sub.documents_generated_this_month, 0)
        # Incident report quota (5) is untouched by the 2 warrants generated above.
        self.assertTrue(self.sub.try_reserve_quota('incident_report'))

    def test_unlimited_warrant_bucket_is_never_capped(self):
        # setUp already created an active Plan, so the post_save signal will
        # auto-assign a free subscription to any new User here — fetch and
        # repoint it rather than fighting the signal with a second create().
        unlimited_plan = Plan.objects.create(
            name='t-unlimited-warrants', display_name='Unlimited Warrants',
            document_limit=50, warrant_document_limit=None,
        )
        user2 = User.objects.create(email='warrant2@example.com')
        sub2 = user2.subscription
        sub2.plan = unlimited_plan
        sub2.warrants_generated_this_month = 10_000
        sub2.save()
        self.assertTrue(sub2.try_reserve_quota('search_warrant'))


class QuotaAtomicityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='quota@example.com')
        self.plan = Plan.objects.create(name='t-quota', display_name='Quota', document_limit=5)
        self.sub = Subscription.objects.create(user=self.user, plan=self.plan, documents_generated_this_month=4)

    def test_reserve_succeeds_under_quota_and_increments(self):
        self.assertTrue(self.sub.try_reserve_quota('incident_report'))
        self.sub.refresh_from_db()
        self.assertEqual(self.sub.documents_generated_this_month, 5)

    def test_reserve_fails_at_quota(self):
        self.sub.try_reserve_quota('incident_report')  # now at 5/5
        self.assertFalse(self.sub.try_reserve_quota('incident_report'))

    def test_release_rolls_back_a_failed_generation(self):
        self.sub.try_reserve_quota('incident_report')
        self.sub.release_quota('incident_report')
        self.sub.refresh_from_db()
        self.assertEqual(self.sub.documents_generated_this_month, 4)


class TrialLifecycleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='trial@example.com')
        self.free = Plan.objects.create(name='free', display_name='Free', document_limit=5)
        self.pro = Plan.objects.create(name='pro', display_name='Pro', document_limit=None)
        self.sub = Subscription.objects.create(user=self.user, plan=self.free, status='active')

    def test_expire_trials_reverts_to_free(self):
        self.sub.plan = self.pro
        self.sub.status = 'trialing'
        self.sub.trial_end = timezone.now() - timedelta(days=1)
        self.sub.save()

        expire_trials()

        self.sub.refresh_from_db()
        self.assertEqual(self.sub.plan.name, 'free')
        self.assertEqual(self.sub.status, 'active')

    def test_expire_trials_resets_usage_so_downgrade_isnt_immediately_over_limit(self):
        # Generated 80 docs during an unlimited Pro trial — must not land back
        # on Free (limit 5) already locked out.
        self.sub.plan = self.pro
        self.sub.status = 'trialing'
        self.sub.trial_end = timezone.now() - timedelta(days=1)
        self.sub.documents_generated_this_month = 80
        self.sub.save()

        expire_trials()

        self.sub.refresh_from_db()
        self.assertEqual(self.sub.documents_generated_this_month, 0)
        self.assertTrue(self.sub.try_reserve_quota('incident_report'))

    def test_expire_trials_leaves_unexpired_trials_alone(self):
        self.sub.plan = self.pro
        self.sub.status = 'trialing'
        self.sub.trial_end = timezone.now() + timedelta(days=5)
        self.sub.save()

        expire_trials()

        self.sub.refresh_from_db()
        self.assertEqual(self.sub.plan.name, 'pro')
        self.assertEqual(self.sub.status, 'trialing')


class StripePriceResolutionTests(TestCase):
    def test_price_to_plan_reads_from_plan_rows_not_settings(self):
        from payments.webhooks import _price_to_plan

        Plan.objects.create(
            name='t-stripe', display_name='Stripe Test', is_active=True,
            stripe_price_id_monthly='price_test_monthly',
            stripe_price_id_yearly='price_test_yearly',
        )
        mapping = _price_to_plan()
        self.assertEqual(mapping.get('price_test_monthly'), ('t-stripe', 'monthly'))
        self.assertEqual(mapping.get('price_test_yearly'), ('t-stripe', 'yearly'))
