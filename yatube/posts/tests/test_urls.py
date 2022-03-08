from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Group, Post

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
            author=PostURLTests.user,
            text='Тестовый пост')
        cls.post_url = f'/posts/{cls.post.id}/'
        cls.post_edit_url = f'/{cls.user.username}/{cls.post.id}/edit/'
        cls.public_urls = (
            ('/', 'posts/index.html'),
            (f'/group/{cls.group.slug}/', 'posts/group_list.html'),
            (f'/{cls.user.username}/', 'posts/profile.html'),
            (cls.post_url, 'posts/post_detail.html'))
        cls.private_urls = (
            ('/create/', 'posts/create_post.html'),
            (cls.post_edit_url, 'posts/create_post.html'))

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def check_public_urls(self):
        for address, template in self.public_urls:
            with self.subTest(adress=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def check_private_urls(self):
        for address, template in self.private_urls:
            with self.subTest(adress=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def check_public_urls_status(self):
        for address in self.public_urls:
            with self.subTest(adress=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def check_private_urls_status(self):
        for address in self.private_urls:
            with self.subTest(adress=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_url_redirect_anonymous_on_admin_login(self):
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/')

    def test_post_edit_url_redirect_anonymous_on_admin_login(self):
        response = self.guest_client.get(
            f'/posts/{PostURLTests.post.id}/edit/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/posts/1/edit/')

    def test_unexisting_page_url_exist(self):
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': '/group/test-slug/',
            'posts/profile.html': '/profile/tester/',
            'posts/post_detail.html': f'/posts/{PostURLTests.post.id}/',
            'posts/post_create.html': '/create/'}
        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
