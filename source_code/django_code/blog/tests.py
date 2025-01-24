from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core import mail
from .models import Post, Comment
from .forms import EmailPostForm, CommentForm

class BlogTests(TestCase):

    def setUp(self):
        # Create a user
        self.user = get_user_model().objects.create_user(username='testuser', password='12345')

        # Create posts, ensuring pagination
        self.posts = []
        for i in range(1, 6):
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
        self.assertContains(response, self.posts[0].title)
        self.assertNotContains(response, self.posts[1].title)  # Draft post should not appear

    def test_post_list_view_pagination(self):
        response = self.client.get(reverse('blog:post_list') + '?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post/list.html')
        self.assertContains(response, self.posts[4].title)  # Last post on second page
        self.assertNotContains(response, self.posts[0].title)

    def test_post_detail_view(self):
        # Test published post
        response = self.client.get(reverse('blog:post_detail', args=[
            self.posts[0].publish.year,
            self.posts[0].publish.month,
            self.posts[0].publish.day,
            self.posts[0].slug
        ]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post/detail.html')
        self.assertContains(response, self.posts[0].title)

        # Test draft post (should return 404)
        response = self.client.get(reverse('blog:post_detail', args=[
            self.posts[1].publish.year,
            self.posts[1].publish.month,
            self.posts[1].publish.day,
            self.posts[1].slug
        ]))
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

    def test_add_comment_view_get(self):
        response = self.client.get(reverse('blog:post_comment', args=[self.posts[0].id]))
        self.assertEqual(response.status_code, 405)  # GET not allowed

    def test_add_comment_view_post(self):
        data = {
            'name': 'Jane Doe',
            'email': 'jane@example.com',
            'body': 'This is a test comment.'
        }
        response = self.client.post(reverse('blog:post_comment', args=[self.posts[0].id]), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.body, 'This is a test comment.')
        self.assertContains(response, 'Your comment has been added.')

    def test_post_list_view_invalid_page(self):
        response = self.client.get(reverse('blog:post_list') + '?page=999')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post/list.html')
        self.assertContains(response, self.posts[-1].title)  # Last post if page out of range

    def test_post_model(self):
        post = self.posts[0]
        self.assertEqual(str(post), post.title)
        self.assertEqual(post.get_absolute_url(), reverse('blog:post_detail', args=[
            post.publish.year, post.publish.month, post.publish.day, post.slug
        ]))

    def test_comment_model(self):
        comment = Comment.objects.create(
            post=self.posts[0],
            name="Test Commenter",
            email="test@example.com",
            body="This is a test comment.",
        )
        self.assertEqual(str(comment), f"Comment by {comment.name} on {comment.post}")
