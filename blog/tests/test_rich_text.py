from django.contrib.auth import get_user_model
from django.test import TestCase

from blog.models import BlogPost


class RichTextSanitizationTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create(email='cms-editor@example.com')

    def test_tiptap_html_is_preserved_and_dangerous_markup_removed(self):
        post = BlogPost.objects.create(
            author=self.author,
            title='Safe rich article',
            content=(
                '<h2 style="text-align: center; color: red">Heading</h2>'
                '<p><strong>Formatted</strong> article.</p>'
                '<img src="https://example.com/image.jpg" alt="Evidence photo" loading="lazy">'
                '<script>alert(1)</script><a href="javascript:alert(2)">bad link</a>'
            ),
        )
        self.assertIn('<h2 style="text-align: center;">Heading</h2>', post.content_html)
        self.assertIn('<strong>Formatted</strong>', post.content_html)
        self.assertIn('https://example.com/image.jpg', post.content_html)
        self.assertNotIn('<script', post.content_html)
        self.assertNotIn('javascript:', post.content_html)
        self.assertNotIn('color:', post.content_html)

    def test_legacy_markdown_remains_supported(self):
        post = BlogPost.objects.create(
            author=self.author, title='Legacy article', content='## Existing heading\n\nBody text.',
        )
        self.assertIn('<h2>Existing heading</h2>', post.content_html)
