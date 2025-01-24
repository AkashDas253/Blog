from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.timezone import now as Now
from django.urls import reverse

class PublishedManager(models.Manager):
    def get_queryset(self):
        return (
            super().get_queryset().filter(status=Post.Status.PUBLISHED)
            )

class Post(models.Model):

    class Status(models.TextChoices):
        DRAFT = 'DF', 'Draft'
        PUBLISHED = 'PB', 'Published'

    # Post manager
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blog_posts'
        )
    objects = models.Manager() # The default manager
    published = PublishedManager() # Our custom manager

    # Post contents
    title = models.CharField(max_length=250)
    slug = models.SlugField(
        max_length=250,
        unique_for_date='publish'
        )
    body = models.TextField()

    # Time
    # publish = models.DateTimeField(db_default=Now()) # For DB timezone
    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # Status
    status = models.CharField(
        max_length=2, 
        choices=Status, 
        default=Status.DRAFT
        )

    class Meta:
        ordering = ['-publish']
        indexes = [
            models.Index(fields=['-publish']),
        ]

    def __str__(self):
        return self.title
    
    # Returns the canonical URL for a post
    def get_absolute_url(self):
        return reverse(
            'blog:post_detail',
            args=[
                self.publish.year,
                self.publish.month,
                self.publish.day,
                self.slug
            ]
        )