from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core import mail
from .models import Post
from .forms import EmailPostForm

class PostTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='12345')
        self.posts = []
        for i in range(1, 6):  # Create 5 posts to ensure pagination
            post = Post.objects.create(
                title=f'Test Post {i}',
                slug=f'test-post-{i}',
                body=f'This is test post {i}.',
                author=self.user,
                status=Post.Status.PUBLISHED if i != 2 else Post.Status.DRAFT,
                publish=timezone.now()
            )
            self.posts.append(post)

    def test_post_list_view(self):
        response = self.client.get(reverse('blog:post_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post/list.html')
        print(response.content)  # Debug output to see the response content
        self.assertContains(response, self.posts[0].title)
        self.assertNotContains(response, self.posts[1].title)

    def test_post_list_view_pagination(self):
        response = self.client.get(reverse('blog:post_list') + '?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post/list.html')
        print(response.content)  # Debug output to see the response content
        self.assertContains(response, self.posts[4].title)
        self.assertNotContains(response, self.posts[0].title)
        self.assertNotContains(response, self.posts[1].title)
        self.assertNotContains(response, self.posts[2].title)
        self.assertNotContains(response, self.posts[3].title)

    def test_post_detail_view(self):
        response = self.client.get(reverse('blog:post_detail', args=[self.posts[0].publish.year, self.posts[0].publish.month, self.posts[0].publish.day, self.posts[0].slug]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post/detail.html')
        self.assertContains(response, self.posts[0].title)
        self.assertContains(response, self.posts[0].body)

        # Test for a draft post (should return 404)
        response = self.client.get(reverse('blog:post_detail', args=[self.posts[1].publish.year, self.posts[1].publish.month, self.posts[1].publish.day, self.posts[1].slug]))
        self.assertEqual(response.status_code, 404)

    def test_post_share_view_get(self):
        response = self.client.get(reverse('blog:post_share', args=[self.posts[0].id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post/share.html')
        self.assertIsInstance(response.context['form'], EmailPostForm)
        self.assertFalse(response.context['sent'])

    def test_post_share_view_post(self):
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'to': 'friend@example.com',
            'comments': 'Check out this post!'
        }
        response = self.client.post(reverse('blog:post_share', args=[self.posts[0].id]), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post/share.html')
        self.assertTrue(response.context['sent'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f"John Doe (john@example.com) recommends you read {self.posts[0].title}")