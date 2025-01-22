from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Post

class PostTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.post1 = Post.objects.create(
            title='Test Post 1',
            slug='test-post-1',
            body='This is a test post.',
            author=self.user,
            status=Post.Status.PUBLISHED
        )
        self.post2 = Post.objects.create(
            title='Test Post 2',
            slug='test-post-2',
            body='This is another test post.',
            author=self.user,
            status=Post.Status.DRAFT
        )

    def test_post_list_view(self):
        response = self.client.get(reverse('blog:post_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post/list.html')
        self.assertContains(response, self.post1.title)
        self.assertNotContains(response, self.post2.title)

    def test_post_detail_view(self):
        response = self.client.get(reverse('blog:post_detail', args=[self.post1.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post/detail.html')
        self.assertContains(response, self.post1.title)
        self.assertContains(response, self.post1.body)

        # Test for a draft post (should return 404)
        response = self.client.get(reverse('blog:post_detail', args=[self.post2.id]))
        self.assertEqual(response.status_code, 404)