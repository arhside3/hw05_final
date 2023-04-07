from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from core.utils import paginate
from posts.forms import CommentForm, PostForm
from posts.models import Follow, Group, Post, User


def group_posts(request: str, slug: str) -> None:
    group = get_object_or_404(Group, slug=slug)
    return render(
        request,
        'posts/group_list.html',
        {
            'group': group,
            'page_obj': paginate(request, group.posts.all()),
        },
    )


def index(request: str) -> None:
    return render(
        request,
        'posts/index.html',
        {
            'page_obj': paginate(
                request, Post.objects.select_related('group', 'author')
            ),
        },
    )


def profile(request: str, username: str) -> None:
    author = get_object_or_404(User, username=username)
    return render(
        request,
        'posts/profile.html',
        {
            'author': author,
            'page_obj': paginate(
                request, author.posts.select_related('group', 'author')
            ),
        },
    )


def post_detail(request: str, pk: int):
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'), pk=pk
    )
    comment_list = post.comments.all().select_related('author')
    form = CommentForm(request.POST or None)
    author = request.user.pk == post.author.pk
    return render(
        request,
        'posts/post_detail.html',
        {
            'post': post,
            'author': author,
            'form': form,
            'comments': comment_list,
        },
    )


@login_required
def create_post(request: str):
    form = PostForm(request.POST or None)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})

    form.instance.author = request.user
    form.save()
    return redirect('posts:profile', request.user)


@login_required
def post_edit(request: str, pk: int):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user:
        return redirect('posts:post_detail', pk)
    form = PostForm(
        request.POST or None,
        instance=post,
        files=request.FILES or None,
    )
    if not form.is_valid():
        return render(
            request,
            'posts/create_post.html',
            {
                'form': form,
                'pk': pk,
                'is_edit': True,
            },
        )

    form.save()
    return redirect('posts:post_detail', pk)


@login_required
def add_comment(request, pk):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, pk=pk)
        comment.save()
    return redirect('posts:post_detail', pk=pk)


@login_required
def follow_index(request):
    post_list = Post.objects.select_related("author", "group").filter(
        author__following__user=request.user
    )
    page_obj = paginate(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)
