"""
Regression tests for async document generation (Phase 3: generation moved off
the request thread onto a Celery task, closing the stuck-GENERATING problem
left by worker timeouts):
- GenerateDocumentView returns 202 immediately with status=GENERATING and
  enqueues generate_document_task instead of running inline.
- generate_document_task runs the same generation logic and correctly
  releases a reserved quota slot on failure.
- reclaim_stuck_generating_documents sweeps abandoned GENERATING documents.
"""
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from documents.models import GeneratedDocument
from documents.tasks import generate_document_task, reclaim_stuck_generating_documents
from documents.views import GenerateDocumentView
from subscriptions.models import Plan, Subscription

User = get_user_model()


def _make_subscribed_user(email, **plan_kwargs):
    user = User.objects.create(email=email, role='officer')
    plan = Plan.objects.create(
        name=f'plan-{email}', display_name='Test Plan',
        can_incident_report=True, can_search_warrant=True, can_arrest_warrant=True,
        **plan_kwargs,
    )
    Subscription.objects.filter(user=user).delete()
    sub = Subscription.objects.create(user=user, plan=plan, status='active')
    return user, sub


class GenerateDocumentAsyncTests(TestCase):
    def setUp(self):
        self.user, self.sub = _make_subscribed_user('async@example.com', document_limit=5)
        self.factory = APIRequestFactory()

    @patch('documents.views.generate_document_task.delay')
    def test_returns_202_and_enqueues_task(self, mock_delay):
        req = self.factory.post('/api/documents/generate/', {
            'doc_type': 'incident_report', 'narrative_style': 'first_person',
            'form_data': {'facts': {'what': 'theft'}},
        }, format='json')
        force_authenticate(req, user=self.user)
        resp = GenerateDocumentView.as_view()(req)

        self.assertEqual(resp.status_code, 202)
        self.assertEqual(resp.data['status'], GeneratedDocument.Status.GENERATING)
        self.assertEqual(resp.data['ai_narrative'], '')
        mock_delay.assert_called_once()
        doc_id_arg = mock_delay.call_args[0][0]
        doc = GeneratedDocument.objects.get(pk=doc_id_arg)
        self.assertEqual(doc.status, GeneratedDocument.Status.GENERATING)

    @patch('documents.views.generate_document_task.delay')
    def test_quota_reserved_before_task_is_enqueued(self, mock_delay):
        self.sub.documents_generated_this_month = 5  # already at the limit
        self.sub.save(update_fields=['documents_generated_this_month'])

        req = self.factory.post('/api/documents/generate/', {
            'doc_type': 'incident_report', 'narrative_style': 'first_person',
            'form_data': {'facts': {'what': 'theft'}},
        }, format='json')
        force_authenticate(req, user=self.user)
        resp = GenerateDocumentView.as_view()(req)

        self.assertEqual(resp.status_code, 402)  # QuotaExceeded
        mock_delay.assert_not_called()


class GenerateDocumentTaskTests(TestCase):
    def setUp(self):
        self.user, self.sub = _make_subscribed_user('task@example.com', document_limit=5)

    def test_success_completes_document_and_logs_usage(self):
        doc = GeneratedDocument.objects.create(
            user=self.user, doc_type='incident_report', case_number='LE-1',
            form_data={'facts': {'what': 'theft', 'who': 'Officer X'}},
            status=GeneratedDocument.Status.GENERATING,
        )
        self.sub.try_reserve_quota('incident_report')

        generate_document_task.run(
            str(doc.id), 'first_person', sub_id=self.sub.id, reserved_quota=True,
        )

        doc.refresh_from_db()
        self.assertEqual(doc.status, GeneratedDocument.Status.COMPLETED)
        self.assertTrue(doc.ai_narrative)
        from subscriptions.models import UsageLog
        self.assertTrue(UsageLog.objects.filter(subscription=self.sub, doc_type='incident_report').exists())

    @patch('documents.generation.ModelClient')
    def test_failure_releases_reserved_quota(self, MockClient):
        MockClient.return_value.generate.side_effect = RuntimeError('model unreachable')
        doc = GeneratedDocument.objects.create(
            user=self.user, doc_type='incident_report', case_number='LE-2',
            form_data={'facts': {'what': 'theft'}},
            status=GeneratedDocument.Status.GENERATING,
        )
        self.sub.try_reserve_quota('incident_report')
        self.sub.refresh_from_db()
        reserved_count = self.sub.documents_generated_this_month
        self.assertEqual(reserved_count, 1)

        generate_document_task.run(
            str(doc.id), 'first_person', sub_id=self.sub.id, reserved_quota=True,
        )

        doc.refresh_from_db()
        self.assertEqual(doc.status, GeneratedDocument.Status.FAILED)
        self.assertIn('model unreachable', doc.error_message)
        self.sub.refresh_from_db()
        self.assertEqual(self.sub.documents_generated_this_month, 0)


class ReclaimStuckGeneratingTests(TestCase):
    def setUp(self):
        self.user, self.sub = _make_subscribed_user('stuck@example.com', document_limit=5)

    def test_reclaims_abandoned_generating_document_and_releases_quota(self):
        self.sub.try_reserve_quota('incident_report')
        doc = GeneratedDocument.objects.create(
            user=self.user, doc_type='incident_report', case_number='LE-3',
            form_data={}, status=GeneratedDocument.Status.GENERATING,
        )
        # Backdate updated_at past the reclaim threshold (auto_now overrides a
        # plain .save(), so update the row directly).
        GeneratedDocument.objects.filter(pk=doc.pk).update(
            updated_at=timezone.now() - timedelta(minutes=30))

        result = reclaim_stuck_generating_documents(minutes=15)

        doc.refresh_from_db()
        self.assertEqual(doc.status, GeneratedDocument.Status.FAILED)
        self.assertIn('1', result)
        self.sub.refresh_from_db()
        self.assertEqual(self.sub.documents_generated_this_month, 0)

    def test_leaves_recent_generating_documents_alone(self):
        doc = GeneratedDocument.objects.create(
            user=self.user, doc_type='incident_report', case_number='LE-4',
            form_data={}, status=GeneratedDocument.Status.GENERATING,
        )
        reclaim_stuck_generating_documents(minutes=15)
        doc.refresh_from_db()
        self.assertEqual(doc.status, GeneratedDocument.Status.GENERATING)

    def test_admin_user_document_reclaimed_without_touching_quota(self):
        admin = User.objects.create(email='admin-stuck@example.com', role='admin')
        doc = GeneratedDocument.objects.create(
            user=admin, doc_type='incident_report', case_number='LE-5',
            form_data={}, status=GeneratedDocument.Status.GENERATING,
        )
        GeneratedDocument.objects.filter(pk=doc.pk).update(
            updated_at=timezone.now() - timedelta(minutes=30))

        reclaim_stuck_generating_documents(minutes=15)

        doc.refresh_from_db()
        self.assertEqual(doc.status, GeneratedDocument.Status.FAILED)
