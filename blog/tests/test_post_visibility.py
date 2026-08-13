from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from blog.models import BlogPost


class BlogPostVisibilityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email='admin@example.com', password='pass', role=User.Role.ADMIN,
        )
        BlogPost.objects.create(author=self.admin, title='Published', content='Body', is_published=True)
        BlogPost.objects.create(author=self.admin, title='Draft', content='Body', is_published=False)

    def test_public_list_only_shows_published_posts(self):
        response = self.client.get('/api/blog/posts/')
        titles = [item['title'] for item in response.data['results']]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(titles, ['Published'])

    def test_admin_list_shows_drafts_and_published_posts(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get('/api/blog/posts/')
        titles = {item['title'] for item in response.data['results']}

        self.assertEqual(response.status_code, 200)
        self.assertEqual(titles, {'Published', 'Draft'})
