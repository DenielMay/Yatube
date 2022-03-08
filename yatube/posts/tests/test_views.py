from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from ..models import Group, Post, Follow

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='tester')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group)
        cls.index_url = ('posts:index', 'posts/index.html', None)
        cls.group_url = (
            'posts:group_list', 'posts/group_list.html', (cls.group.slug,))
        cls.profile_url = (
            'posts:profile', 'posts/profile.html', (cls.user.username,))
        cls.post_url = ('posts:post_detail', 'posts/post_detail.html',)
        cls.new_post_url = (
            'posts:post_create', 'posts/post_create.html', None)
        cls.edit_post_url = ('posts:post_edit', 'posts/post_create.html',
                             (cls.post.id))
        cls.paginated_urls = (
            cls.index_url,
            cls.group_url,
            cls.profile_url
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        templates_pages_names = {
            'posts/group_list.html': reverse('posts:group_list',
                                             kwargs={'slug': 'test-slug'}),
            'posts/index.html': reverse('posts:index'),
            'posts/post_create.html': reverse('posts:post_edit', kwargs={
                'post_id': self.post.id}),
            'posts/post_detail.html': reverse('posts:post_detail', kwargs={
                'post_id': self.post.id}),
            'posts/profile.html': reverse('posts:profile',
                                          kwargs={'username': self.user})}
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_index_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        context_objects = {
            self.user: first_object.author,
            self.post.text: first_object.text,
            self.group: first_object.group,
            self.post.id: first_object.id}
        for reverse_name, response_name in context_objects.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(response_name, reverse_name)

    def test_posts_groups_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        for post in response.context['page_obj']:
            self.assertEqual(post.group, self.group)

    def test_post_profile_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        for post in response.context['page_obj']:
            self.assertEqual(post.author, self.user)

    def test_post_edit_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.pk}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField}
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_post_detail_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post_pk = response.context['post'].pk
        self.assertEqual(post_pk, self.post.pk)

    def test_post_create_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField}
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Tester')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        for count in range(13):
            cls.post = Post.objects.create(
                text=f'Тестовый пост номер {count}',
                author=cls.user)

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.username = 'tester1'
        cls.username_one = 'tester2'
        cls.username_two = 'tester3'
        cls.user = User.objects.create_user(username=cls.username)
        cls.title = 'Тестовая группа'
        cls.slug = 'test-slug'
        cls.description = 'Тестовое описание'
        cls.group = Group.objects.create(
            title=cls.title,
            slug=cls.slug,
            description=cls.description)
        cls.text = 'Тестовый текст'
        cls.post = Post.objects.create(
            author=cls.user,
            text=cls.text,
            group=cls.group)

    def setUp(self):
        self.guest_client = Client()
        self.user1 = User.objects.create(username=self.username_one)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user1)
        self.user2 = User.objects.create(username=self.username_two)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)

    def test_authorized_client_can_add_follow(self):
        self.authorized_client.post(
            reverse('posts:profile_follow', kwargs={
                'username': self.username}))
        follow_count = Follow.objects.filter(
            user=self.user1,
            author=self.user).count()
        self.assertEqual(follow_count, 1)

    def test_authorized_client_can_delete_follow(self):
        self.authorized_client.post(
            reverse('posts:profile_unfollow', kwargs={
                'username': self.username}))
        follow_count = Follow.objects.filter(
            user=self.user1, author=self.user).count()
        self.assertEqual(follow_count, 0)

    def test_new_post_follow(self):
        self.authorized_client.post(
            reverse('posts:profile_follow', kwargs={
                'username': self.username}))
        self.authorized_client2.post(
            reverse('posts:profile_follow', kwargs={
                'username': self.username_one}))
        text_old = 'Старый пост'
        Post.objects.create(
            author=self.user1,
            text=text_old,
            group=self.group)
        text_new = 'Новый пост'
        post_new = Post.objects.create(
            author=self.user,
            text=text_new,
            group=self.group)
        post_from_context = self.authorized_client.get(
            reverse('posts:follow_index')).context['page_obj'][0]
        self.assertEqual(post_new, post_from_context)
        post_from_context = self.authorized_client2.get(
            reverse('posts:follow_index')).context['page_obj'][0]
        self.assertNotEqual(post_new, post_from_context)


class PageNotFound(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_urls_uses_correct_template_for_404(self):
        templates_url_names = {
            '/unexisting_page/': 'core/404.html',
            '/group/error/': 'core/404.html'}
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)


class CacheTests(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='tester')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index_page(self):
        post = Post.objects.create(
            text='Тестовый пост',
            author=self.user)
        content_new = self.authorized_client.get(
            reverse('posts:index')).content
        post.delete()
        content_delete = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertEqual(content_new, content_delete)
        cache.clear()
        content_delete = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertNotEqual(content_new, content_delete)
