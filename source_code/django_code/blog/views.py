# Post list
from taggit.models import Tag
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Post

def post_list(request, tag_slug=None):
    # Get all published posts
    post_list = Post.published.all()
    tag = None

    # If a tag_slug is provided, filter posts by that tag
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_list = post_list.filter(tags__in=[tag])

    # Pagination with 3 posts per page
    paginator = Paginator(post_list, 3)
    page_number = request.GET.get('page', 1)

    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        # If page_number is not an integer, get the first page
        posts = paginator.page(1)
    except EmptyPage:
        # If page_number is out of range, get the last page of results
        posts = paginator.page(paginator.num_pages)

    return render(
        request,
        'blog/post/list.html',
        {
            'posts': posts,
            'tag': tag  # Pass the tag to the template
        }
    )

# Post details
from django.db.models import Count

def post_detail(request, year, month, day, post):
    post = get_object_or_404(
        Post,
        status=Post.Status.PUBLISHED,
        slug=post,
        publish__year=year,
        publish__month=month,
        publish__day=day
    )
    
    # List of active comments for this post
    comments = post.comments.filter(active=True)
    
    # Form for users to comment
    form = CommentForm()
    
    # List of similar posts
    post_tags_ids = post.tags.values_list('id', flat=True)  # Get all tag IDs for the current post
    similar_posts = Post.published.filter(
        tags__in=post_tags_ids  # Filter posts that share tags with the current post
    ).exclude(id=post.id)  # Exclude the current post itself
    
    # Annotate similar posts with a count of shared tags
    similar_posts = similar_posts.annotate(
        same_tags=Count('tags')  # Count the shared tags for each post
    ).order_by('-same_tags', '-publish')[:4]  # Order by shared tag count and publish date, limit to 4 posts
    
    return render(
        request,
        'blog/post/detail.html',
        {
            'post': post,
            'comments': comments,
            'form': form,
            'similar_posts': similar_posts  # Pass similar posts to the template
        }
    )


# Email post sharing views
from django.shortcuts import render, get_object_or_404
from django.core.mail import send_mail
from .models import Post
from .forms import EmailPostForm

def post_share(request, post_id):
    # Retrieve post by id
    post = get_object_or_404(
        Post,
        id=post_id,
        status=Post.Status.PUBLISHED
    )
    sent = False
    if request.method == 'POST':
        # Form was submitted
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Form fields passed validation
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} ({cd['email']}) recommends you read {post.title}"
            message = f"Read {post.title} at {post_url}\n\n{cd['name']}'s comments: {cd['comments']}"
            send_mail(
                subject=subject,
                message=message,
                from_email=None,
                recipient_list=[cd['to']]
            )
            sent = True
    else:
        form = EmailPostForm()
    return render(
        request,
        'blog/post/share.html',
        {
            'post': post,
            'form': form,
            'sent': sent
        }
    )

from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from .models import Post, Comment
from .forms import CommentForm

@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(
        Post,
        id=post_id,
        status=Post.Status.PUBLISHED
    )
    comment = None
    # A comment was posted
    form = CommentForm(data=request.POST)
    if form.is_valid():
        # Create a Comment object without saving it to the database
        comment = form.save(commit=False)
        # Assign the post to the comment
        comment.post = post
        # Save the comment to the database
        comment.save()
    return render(
        request,
        'blog/post/comment.html',
        {
            'post': post,
            'form': form,
            'comment': comment
        }
    )

# Search view
from django.contrib.postgres.search import (
    SearchVector,
    SearchQuery,
    SearchRank
)
from .forms import CommentForm, EmailPostForm, SearchForm
from django.contrib.postgres.search import TrigramSimilarity

def post_search(request):
    form = SearchForm()
    query = None
    results = []

    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            results = (
                Post.published.annotate(
                    similarity=TrigramSimilarity('title', query),
                )
                .filter(similarity__gt=0.1)
                .order_by('-similarity')
            )

    return render(
        request,
        'blog/post/search.html',
        {
            'form': form,
            'query': query,
            'results': results
        },
    )