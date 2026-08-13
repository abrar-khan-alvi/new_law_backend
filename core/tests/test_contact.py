from django.core import mail
from django.test import TestCase, override_settings
from rest_framework.test import APIClient


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ContactViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_contact_form_sends_email_to_klyvorek(self):
        response = self.client.post('/api/contact/', {
            'firstName': 'Jane',
            'lastName': 'Officer',
            'agency': 'Example PD',
            'email': 'jane@example.gov',
            'message': 'Please contact me.',
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertEqual(sent.to, ['klyvorek@gmail.com'])
        self.assertEqual(sent.reply_to, ['jane@example.gov'])
        self.assertIn('Example PD', sent.body)

    def test_required_fields_are_validated(self):
        response = self.client.post('/api/contact/', {'message': 'Hello'}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)
