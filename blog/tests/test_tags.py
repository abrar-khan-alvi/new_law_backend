from django.test import TestCase

from accounts.models import User
from blog.models import BlogPost, Tag
from blog.serializers import BlogPostCreateSerializer


class BlogTagTests(TestCase):
    def test_existing_slug_is_reused_for_different_tag_casing(self):
        author = User.objects.create_user(email='admin@example.com', password='pass')
        existing = Tag.objects.create(name='AI Law Enforcement', slug='ai-law-enforcement')
        serializer = BlogPostCreateSerializer(data={
            'title': 'Test Article',
            'content': '<p>Body</p>',
            'tags': ['AI-Law Enforcement'],
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)
        post = serializer.save(author=author)

        self.assertEqual(BlogPost.objects.count(), 1)
        self.assertEqual(Tag.objects.count(), 1)
        self.assertEqual(list(post.tags.all()), [existing])
