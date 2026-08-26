from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

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

    def test_free_evaluation_has_one_combined_quota(self):
        user = User.objects.create(email='free-eval-quota@example.com')
        plan = Plan.objects.create(
            name='free', display_name='Free Evaluation', document_limit=10,
            warrant_document_limit=10,
        )
        sub = Subscription.objects.create(
            user=user,
            plan=plan,
            status=Subscription.Status.TRIALING,
            trial_end=timezone.now() + timedelta(days=14),
            documents_generated_this_month=7,
            warrants_generated_this_month=3,
        )
        self.assertFalse(sub.try_reserve_quota('incident_report'))
        self.assertFalse(sub.try_reserve_quota('search_warrant'))
        sub.reset_monthly_usage()
        sub.refresh_from_db()
        self.assertEqual(sub.documents_generated_this_month, 7)
        self.assertEqual(sub.warrants_generated_this_month, 3)


class WarrantQuotaBucketTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='warrant@example.com')
        self.plan = Plan.objects.create(
            name='t-split', display_name='Split', document_limit=5, warrant_document_limit=2,
        )
        self.sub = Subscription.objects.create(user=self.user, plan=self.plan)

    def test_search_and_arrest_warrants_share_one_bucket(self):
        self.assertTrue(self.sub.try_reserve_quota('search_warrant'))
        self.assertTrue(self.sub.try_reserve_quota('arrest_warrant'))
        self.assertFalse(self.sub.try_reserve_quota('search_warrant'))
        self.assertFalse(self.sub.try_reserve_quota('arrest_warrant'))

    def test_warrant_usage_does_not_consume_incident_report_quota(self):
        self.sub.try_reserve_quota('search_warrant')
        self.sub.try_reserve_quota('arrest_warrant')
        self.sub.refresh_from_db()
        self.assertEqual(self.sub.warrants_generated_this_month, 2)
        self.assertEqual(self.sub.documents_generated_this_month, 0)
        self.assertTrue(self.sub.try_reserve_quota('incident_report'))

    def test_unlimited_warrant_bucket_is_never_capped(self):
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
        self.sub.try_reserve_quota('incident_report')
        self.assertFalse(self.sub.try_reserve_quota('incident_report'))

    def test_release_rolls_back_a_failed_generation(self):
        self.sub.try_reserve_quota('incident_report')
        self.sub.release_quota('incident_report')
        self.sub.refresh_from_db()
        self.assertEqual(self.sub.documents_generated_this_month, 4)


@override_settings(SECURE_SSL_REDIRECT=False)
class TrialLifecycleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='trial@example.com')
        self.free = Plan.objects.create(name='free', display_name='Free Evaluation', document_limit=10)
        self.sub = Subscription.objects.create(
            user=self.user,
            plan=self.free,
            status=Subscription.Status.TRIALING,
            trial_end=timezone.now() + timedelta(days=14),
            has_used_trial=True,
        )

    def test_expire_trials_marks_free_evaluation_expired(self):
        self.sub.trial_end = timezone.now() - timedelta(days=1)
        self.sub.save()

        expire_trials()

        self.sub.refresh_from_db()
        self.assertEqual(self.sub.plan.name, 'free')
        self.assertEqual(self.sub.status, Subscription.Status.EXPIRED)

    def test_expire_trials_preserves_evaluation_usage(self):
        self.sub.trial_end = timezone.now() - timedelta(days=1)
        self.sub.documents_generated_this_month = 6
        self.sub.warrants_generated_this_month = 4
        self.sub.search_warrants_generated_this_month = 3
        self.sub.arrest_warrants_generated_this_month = 1
        self.sub.save()

        expire_trials()

        self.sub.refresh_from_db()
        self.assertEqual(self.sub.documents_generated_this_month, 6)
        self.assertEqual(self.sub.warrants_generated_this_month, 4)
        self.assertEqual(self.sub.search_warrants_generated_this_month, 3)
        self.assertEqual(self.sub.arrest_warrants_generated_this_month, 1)
        self.assertFalse(self.sub.has_access_entitlement())

    def test_expire_trials_leaves_unexpired_trials_alone(self):
        expire_trials()

        self.sub.refresh_from_db()
        self.assertEqual(self.sub.plan.name, 'free')
        self.assertEqual(self.sub.status, Subscription.Status.TRIALING)

    def test_start_trial_endpoint_does_not_upgrade_without_payment(self):
        client = APIClient()
        client.force_authenticate(self.user)

        response = client.post('/api/subscriptions/start-trial/', {'plan': 'pro'}, format='json')

        self.assertEqual(response.status_code, 403)
        self.sub.refresh_from_db()
        self.assertEqual(self.sub.plan.name, 'free')
        self.assertEqual(self.sub.status, Subscription.Status.TRIALING)


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


class SubscriptionEntitlementTests(TestCase):
    def test_free_evaluation_is_entitled_without_stripe_until_trial_end(self):
        user = User.objects.create(email='ent-free@example.com')
        plan = Plan.objects.create(name='free', display_name='Free Evaluation')
        sub = Subscription.objects.create(
            user=user,
            plan=plan,
            status=Subscription.Status.TRIALING,
            trial_end=timezone.now() + timedelta(days=14),
        )
        self.assertTrue(sub.has_access_entitlement())

    def test_expired_free_evaluation_is_not_entitled(self):
        user = User.objects.create(email='ent-free-expired@example.com')
        plan = Plan.objects.create(name='free', display_name='Free Evaluation')
        sub = Subscription.objects.create(
            user=user,
            plan=plan,
            status=Subscription.Status.EXPIRED,
            trial_end=timezone.now() - timedelta(days=1),
        )
        self.assertFalse(sub.has_access_entitlement())

    def test_paid_plan_requires_stripe_subscription(self):
        user = User.objects.create(email='ent-paid@example.com')
        plan = Plan.objects.create(name='pro-ent', display_name='Pro')
        sub = Subscription.objects.create(user=user, plan=plan, status=Subscription.Status.ACTIVE)
        self.assertFalse(sub.has_access_entitlement())
        sub.stripe_subscription_id = 'sub_test'
        self.assertTrue(sub.has_access_entitlement())

    def test_trialing_paid_plan_is_not_entitled(self):
        user = User.objects.create(email='ent-trial@example.com')
        plan = Plan.objects.create(name='trial-ent', display_name='Trial')
        sub = Subscription.objects.create(
            user=user, plan=plan, status=Subscription.Status.TRIALING, stripe_subscription_id='sub_test',
        )
        self.assertFalse(sub.has_access_entitlement())
