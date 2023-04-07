import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post, User
from yatube.settings import PAGE_SIZE

USERNAME = 'auth'
PROFILE_URL = reverse('posts:profile', kwargs={'username': USERNAME})
INDEX_URL = reverse('posts:index_name')
SLUG = 'testing-slug'
ANOTHER_SLUG = "test_group_2"
ANOTHER_GROUP_POSTS_URL = reverse(
    'posts:group_posts', kwargs={'slug': ANOTHER_SLUG}
)
GROUP_POSTS_URL = reverse('posts:group_posts', kwargs={'slug': SLUG})
CREATE_URL = reverse('posts:create_post')
USERNAME_FOLLOWER = 'post_follower'
FOLLOW_URL = reverse(
    'posts:profile_follow', kwargs={'username': USERNAME_FOLLOWER}
)
POSTS_ON_SECOND_PAGE = 3

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание группы',
            slug=SLUG,
        )
        cls.another_group = Group.objects.create(
            title="Тестовая групаа_2",
            slug=ANOTHER_SLUG,
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif', content=small_gif, content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user,
            group=cls.group,
            image=uploaded,
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', kwargs={'pk': cls.post.pk}
        )
        cls.UPDATE_URL = reverse('posts:update_post', args=[cls.post.id])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.nonauthorized_user = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def check_post_info(self, post):
        with self.subTest(post=post):
            self.assertEqual(post, self.post)
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group, self.post.group)

    def test_posts_context_index_template(self):
        page_obj = self.authorized_client.get(INDEX_URL).context['page_obj']
        self.assertEqual(len(page_obj), 1)
        self.check_post_info(page_obj[0])
        self.assertEqual(page_obj[0].image, self.post.image)

    def test_groups_page_show_correct_context(self):
        """Шаблон group_list.html сформирован с правильным контекстом."""
        page_obj = self.authorized_client.get(GROUP_POSTS_URL).context[
            'page_obj'
        ]
        group = self.authorized_client.get(GROUP_POSTS_URL).context['group']
        self.assertEqual(len(page_obj), 1)
        self.check_post_info(page_obj[0])
        self.assertEqual(group, self.group)
        self.assertEqual(group.pk, self.group.pk)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.description, self.group.description)
        self.assertEqual(page_obj[0].image, self.post.image)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile.html сформирован с правильным контекстом."""
        page_obj = self.authorized_client.get(PROFILE_URL).context['page_obj']
        self.assertEqual(len(page_obj), 1)
        self.check_post_info(page_obj[0])
        self.assertEqual(page_obj[0].image, self.post.image)

    def test_profile_author_show_correct_context(self):
        page_obj = self.authorized_client.get(PROFILE_URL).context['page_obj']
        self.assertEqual(
            self.authorized_client.get(PROFILE_URL).context['author'],
            self.user,
        )
        self.assertEqual(page_obj[0].image, self.post.image)

    def test_detail_page_show_correct_context(self):
        """Шаблон post_detail.html сформирован с правильным контекстом."""
        page_obj = self.authorized_client.get(self.POST_DETAIL_URL).context[
            'post'
        ]
        self.check_post_info(
            page_obj,
        )
        self.assertEqual(page_obj.image, self.post.image)

    def test_post_another_group(self):
        self.assertNotIn(
            self.post,
            self.authorized_client.get(ANOTHER_GROUP_POSTS_URL).context[
                "page_obj"
            ],
        )

    def test_cache(self):
        """Проверка работы функции кэширования. Удаленный пост продолжает
        показываться и исчезает после очистки кэша.
        """
        post = Post.objects.create(
            author=self.user, text='пост для тестирования кэша'
        )
        post.delete()
        response_afterdelete = self.client.get(INDEX_URL)
        self.assertEqual(
            self.client.get(INDEX_URL).content, response_afterdelete.content
        )
        cache.clear()
        response_after_clear_cash = self.client.get(INDEX_URL)
        self.assertNotEqual(
            response_afterdelete.content, response_after_clear_cash.content
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='auth',
        )
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            description='Тестовое описание группы',
            slug=SLUG,
        )
        cls.post = Post.objects.bulk_create(
            Post(text=f'Пост #{i}', author=cls.user, group=cls.group)
            for i in range(PAGE_SIZE + POSTS_ON_SECOND_PAGE)
        )

    def setUp(self):
        self.unauthorized_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_paginator_on_pages(self):
        url_pages = [
            (INDEX_URL, PAGE_SIZE),
            (INDEX_URL + '?page=2', POSTS_ON_SECOND_PAGE),
            (PROFILE_URL, PAGE_SIZE),
            (PROFILE_URL + '?page=2', POSTS_ON_SECOND_PAGE),
            (GROUP_POSTS_URL, PAGE_SIZE),
            (GROUP_POSTS_URL + '?page=2', POSTS_ON_SECOND_PAGE),
        ]
        for url, expected_count in url_pages:
            with self.subTest(url=url):
                self.assertEqual(
                    len(
                        self.unauthorized_client.get(url).context.get(
                            'page_obj'
                        )
                    ),
                    expected_count,
                )


PROFILE_UNFOLLOW_URL = reverse(
    'posts:profile_unfollow', kwargs={'username': USERNAME}
)
FOLLOW_INDEX_URL = reverse('posts:follow_index')


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username=USERNAME)
        cls.user_following = User.objects.create_user(
            username=USERNAME_FOLLOWER
        )
        cls.user_without_post = User.objects.create_user(
            username='test_user_2'
        )
        cls.group = Group.objects.create(
            title='Заголовок для 1 тестовой группы', slug='test_slug'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись для создания 1 поста',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.client_auth_following = Client()
        self.authorized_client.force_login(self.user)
        self.client_auth_following.force_login(self.user_following)

    def test_follow_authorized(self):
        """Авторизованный пользователь может подписываться"""
        self.authorized_client.get(FOLLOW_URL)
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_follow_guest(self):
        """не Авторизованный пользователь  не может подписываться"""
        self.guest_client.get(FOLLOW_URL)
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_unfollow(self):
        """
        Авторизованный пользователь отписаться от автора
        """
        self.client_auth_following.get(PROFILE_UNFOLLOW_URL)
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_subscription_feed(self):
        """запись появляется в ленте подписчиков"""
        self.assertEqual(
            self.client_auth_following.get(FOLLOW_INDEX_URL)
            .context['page_obj'][0]
            .text,
            self.post.text,
        )

    def test_subscription_feed(self):
        """Запись не появляется у неподписанных пользователей"""
        self.assertNotContains(
            self.authorized_client.get(FOLLOW_INDEX_URL), self.post.text
        )
