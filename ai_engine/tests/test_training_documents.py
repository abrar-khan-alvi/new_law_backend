from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from ai_engine.models import DocumentChunk, TrainingDocument

User = get_user_model()


@override_settings(SECURE_SSL_REDIRECT=False)
class TrainingDocumentDeleteTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create(email='admin-datasets@example.com', role='admin')
        self.officer = User.objects.create(email='officer-datasets@example.com', role='officer')
        self.training_doc = TrainingDocument.objects.create(
            doc_type='incident_report',
            title='Unredacted sample',
            original_filename='sample.pdf',
            s3_key='training/incident_report/sample.pdf',
            raw_text='Officer-provided sample text.',
            uploaded_by=self.admin,
            is_indexed=True,
            chunk_count=1,
        )
        DocumentChunk.objects.create(
            training_doc=self.training_doc,
            doc_type='incident_report',
            chunk_index=0,
            text='Officer-provided sample text.',
            embedding=[0.0] * 384,
        )

    @patch('ai_engine.views.delete_upload', return_value=True)
    def test_admin_can_delete_training_document_file_and_chunks(self, mock_delete_upload):
        client = APIClient()
        client.force_authenticate(self.admin)

        response = client.delete(f'/api/ai/training-docs/{self.training_doc.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'deleted': True, 'stored_file_deleted': True})
        self.assertFalse(TrainingDocument.objects.filter(pk=self.training_doc.pk).exists())
        self.assertFalse(DocumentChunk.objects.filter(training_doc_id=self.training_doc.pk).exists())
        mock_delete_upload.assert_called_once_with('training/incident_report/sample.pdf')

    @patch('ai_engine.views.delete_upload')
    def test_non_admin_cannot_delete_training_document(self, mock_delete_upload):
        client = APIClient()
        client.force_authenticate(self.officer)

        response = client.delete(f'/api/ai/training-docs/{self.training_doc.id}/')

        self.assertEqual(response.status_code, 403)
        self.assertTrue(TrainingDocument.objects.filter(pk=self.training_doc.pk).exists())
        self.assertTrue(DocumentChunk.objects.filter(training_doc_id=self.training_doc.pk).exists())
        mock_delete_upload.assert_not_called()

    @patch('ai_engine.views.delete_upload', return_value=False)
    def test_delete_succeeds_when_stored_file_is_already_missing(self, mock_delete_upload):
        client = APIClient()
        client.force_authenticate(self.admin)

        response = client.delete(f'/api/ai/training-docs/{self.training_doc.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'deleted': True, 'stored_file_deleted': False})
        self.assertFalse(TrainingDocument.objects.filter(pk=self.training_doc.pk).exists())
        mock_delete_upload.assert_called_once_with('training/incident_report/sample.pdf')

    def test_delete_missing_training_document_returns_404(self):
        client = APIClient()
        client.force_authenticate(self.admin)

        response = client.delete('/api/ai/training-docs/999999/')

        self.assertEqual(response.status_code, 404)
