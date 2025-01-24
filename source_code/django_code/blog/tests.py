from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core import mail
from taggit.models import Tag
from .models import Post, Comment
from .forms import EmailPostForm, CommentForm

class BlogTests(TestCase):

    def setUp(self):
        # Create a user
        self.user = get_user_model().objects.create_user(username='testuser', password='12345')

        # Create posts dynamically based on their publish status
        self.published_posts = []
        self.draft_posts = []
        for i in range(1, 6):
            post = Post.objects.create(
                title=f'Test Post {i}',
                slug=f'test-post-{i}',
                body=f'This is test post {i}.',
                author=self.user,
                status=Post.Status.PUBLISHED if i != 2 else Post.Status.DRAFT,
                publish=timezone.now()
            )
            post.tags.add(f'tag{i}')  # Assigning tags to each post dynamically
            if post.status == Post.Status.PUBLISHED:
                self.published_posts.append(post)
            else:
                self.draft_posts.append(post)

    def test_post_list_view(self):
        response = self.client.get(reverse('blog:post_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post/list.html')

        # Test that published posts appear, and draft posts do not
        for post in self.published_posts:
            self.assertContains(response, post.title)
            for tag in post.tags.all():
                self.assertContains(response, tag.name)
        for post in self.draft_posts:
            self.assertNotContains(response, post.title)

    def test_post_list_view_pagination(self):
        response = self.client.get(reverse('blog:post_list') + '?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post/list.html')

        # Ensure that the last post of the published posts appears on the second page
        self.assertContains(response, self.published_posts[-1].title)

    def test_show_latest_posts_tag(self):
        response = self.client.get(reverse('blog:post_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post/list.html')

        # Test that the latest posts are displayed in the sidebar
        for post in self.published_posts[:3]:  # Assuming you want to display the top 3
            self.assertContains(response, post.title)

    def test_post_detail_view(self):
        post = self.published_posts[0]
        response = self.client.get(reverse('blog:post_detail', args=[
            post.publish.year, post.publish.month, post.publish.day, post.slug
        ]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post/detail.html')
        self.assertContains(response, post.title)
        
        # Ensure that tags are shown on the post detail page
        for tag in post.tags.all():
            self.assertContains(response, tag.name)

        # Test draft post (should return 404)
        draft_post = self.draft_posts[0]
        response = self.client.get(reverse('blog:post_detail', args=[
            draft_post.publish.year, draft_post.publish.month, draft_post.publish.day, draft_post.slug
        ]))
        self.assertEqual(response.status_code, 404)

    def test_post_share_view_get(self):
        response = self.client.get(reverse('blog:post_share', args=[self.published_posts[0].id]))
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
        response = self.client.post(reverse('blog:post_share', args=[self.published_posts[0].id]), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post/share.html')
        self.assertTrue(response.context['sent'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f"John Doe (john@example.com) recommends you read {self.published_posts[0].title}")

    def test_add_comment_view_post(self):
        data = {
            'name': 'Jane Doe',
            'email': 'jane@example.com',
            'body': 'This is a test comment.'
        }
        response = self.client.post(reverse('blog:post_comment', args=[self.published_posts[0].id]), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.body, 'This is a test comment.')
        self.assertContains(response, 'Your comment has been added.')

    def test_post_list_view_invalid_page(self):
        response = self.client.get(reverse('blog:post_list') + '?page=999')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post/list.html')
        # Test that if the page is out of range, it defaults to the last post
        self.assertContains(response, self.published_posts[-1].title)

    def test_post_model(self):
        post = self.published_posts[0]
        self.assertEqual(str(post), post.title)
        self.assertEqual(post.get_absolute_url(), reverse('blog:post_detail', args=[
            post.publish.year, post.publish.month, post.publish.day, post.slug
        ]))

    def test_comment_model(self):
        comment = Comment.objects.create(
            post=self.published_posts[0],
            name="Test Commenter",
            email="test@example.com",
            body="This is a test comment.",
        )
        self.assertEqual(str(comment), f"Comment by {comment.name} on {comment.post}")

    def test_tag_model(self):
        # Test the Tag model to ensure the tagging functionality is working as expected
        tag = Tag.objects.create(name="testtag")
        post = self.published_posts[0]
        post.tags.add(tag)
        self.assertIn(tag, post.tags.all())
