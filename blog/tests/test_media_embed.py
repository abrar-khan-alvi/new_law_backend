"""
Regression test for the video-embed XSS fix: a video_url that doesn't match
the YouTube/Vimeo regex must be HTML-escaped before being stored as
embed_html, since that string is served verbatim to every visitor of the
public blog post.
"""
from django.test import SimpleTestCase

from blog.views import BlogMediaUploadView


class VideoEmbedEscapingTests(SimpleTestCase):
    def test_generic_url_is_escaped(self):
        payload = 'https://example.com/x" onerror="alert(1)'
        html = BlogMediaUploadView._embed(payload)
        self.assertNotIn('onerror="alert(1)"', html)
        self.assertIn('&quot;', html)

    def test_youtube_url_uses_safe_iframe(self):
        html = BlogMediaUploadView._embed('https://youtu.be/dQw4w9WgXcQ')
        self.assertIn('youtube.com/embed/dQw4w9WgXcQ', html)
