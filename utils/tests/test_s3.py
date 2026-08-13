from django.test import SimpleTestCase, override_settings

from utils.s3 import s3_configured


class S3ConfigurationTests(SimpleTestCase):
    @override_settings(AWS_S3_BUCKET='')
    def test_empty_bucket_disables_s3(self):
        self.assertFalse(s3_configured())

    @override_settings(AWS_S3_BUCKET='replace-with-private-media-bucket')
    def test_placeholder_bucket_disables_s3(self):
        self.assertFalse(s3_configured())

    @override_settings(AWS_S3_BUCKET='klyvorek-private-media')
    def test_real_bucket_enables_s3(self):
        self.assertTrue(s3_configured())
