from django.contrib.auth.decorators import login_required

from .forms import PostForm, CommentForm
from .models import Post, Group, User, Follow
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator

POSTS_PER_PAGE = 10


def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.all().order_by('-pub_date')
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'posts': post_list,
        'title': 'Последние обновления на сайте',
        'page_obj': page_obj}
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(
        Group.objects.prefetch_related("posts", "author", "comments"),
        slug=slug)
    posts = group.posts.all()[:POSTS_PER_PAGE]
    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'posts': posts,
        'title': f'Записи сообщества {str(group)}',
        'page_obj': page_obj}
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    profile_obj = get_object_or_404(User, username=username)
    number_posts = profile_obj.posts.count()
    posts = profile_obj.posts.order_by('pub_date')
    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = False
    if request.user.is_authenticated:
        follow_list = Follow.objects.filter(user=request.user,
                                            author=profile_obj)
        following = follow_list.exists()
    context = {
        'profile_obj': profile_obj,
        'number_posts': number_posts,
        'posts': posts,
        'page_obj': page_obj,
        'title': f'Профайл пользователя {profile_obj.username}',
        'following': following, }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)
    post_count = post.author.posts.count()
    comments = post.comments.order_by('-created')
    form = CommentForm()
    context = {
        'post': post,
        'comments': comments,
        'form': form,
        'post_count': post_count,
        'title': f'Пост {post.text[:30]}'}
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/post_create.html'
    form = PostForm(request.POST or None, files=request.FILES or None)
    context = {
        'form': form,
        'edit': False,
        'username': request.user}
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user)
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    template = 'posts/post_create.html'
    is_edit = True
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(request.POST or None, instance=post)
    context = {
        'form': form,
        'is_edit': is_edit}
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:post_detail', post_id)
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'index': False,
        'follow': True,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user.id != author.id:
        Follow.objects.get_or_create(user=request.user, author=author)
    else:
        return redirect('posts:profile', username)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user,
                          author=author).delete()
    return redirect('posts:follow_index')
