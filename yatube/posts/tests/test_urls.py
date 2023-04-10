from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

INDEX_URL = reverse('posts:index_name')
CREATE_URL = reverse('posts:create_post')
USERNAME = 'auth'
ANOTHER_USERNAME = 'auth_2'
SLUG = 'test_group'
GROUP_POSTS_URL = reverse('posts:group_posts', kwargs={'slug': SLUG})
PROFILE_URL = reverse('posts:profile', kwargs={'username': USERNAME})
LOGIN_URL = reverse('users:login')
REDIRECT_CREATE_URL = f'{LOGIN_URL}?next={CREATE_URL}'
FOLLOW_INDEX_URL = reverse('posts:follow_index')
REDIRECT_FOLLOW_INDEX_URL = f'{LOGIN_URL}?next={FOLLOW_INDEX_URL}'
FOLLOW_URL = reverse('posts:profile_follow', args={USERNAME})
REDIRECT_FOLLOW_URL = f'{LOGIN_URL}?next={FOLLOW_URL}'
UNFOLLOW_URL = reverse('posts:profile_unfollow', args={USERNAME})
REDIRECT_UNFOLLOW_URL = f'{LOGIN_URL}?next={UNFOLLOW_URL}'


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.another_user = User.objects.create_user(username=ANOTHER_USERNAME)
        cls.group = Group.objects.create(
            title='заголовок',
            description='описание',
            slug='test_group',
        )
        cls.post = Post.objects.create(
            text='текст',
            author=cls.user,
            group=cls.group,
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', kwargs={'pk': cls.post.pk}
        )
        cls.EDIT_URL = reverse('posts:update_post', kwargs={'pk': cls.post.pk})
        cls.REDIRECT_EDIT_URL = f'{LOGIN_URL}?next={cls.EDIT_URL}'

    def setUp(self):
        self.guest = Client()
        self.author = Client()
        self.author.force_login(self.user)
        self.another = Client()
        self.another.force_login(self.another_user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            INDEX_URL: 'posts/index.html',
            GROUP_POSTS_URL: 'posts/group_list.html',
            PROFILE_URL: 'posts/profile.html',
            self.POST_DETAIL_URL: 'posts/post_detail.html',
            CREATE_URL: 'posts/create_post.html',
            self.EDIT_URL: 'posts/create_post.html',
            FOLLOW_INDEX_URL: 'posts/follow.html',
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                self.assertTemplateUsed(self.author.get(adress), template)

    def test_urls(self):
        url_data = [
            (INDEX_URL, self.guest, 'OK'),
            (GROUP_POSTS_URL, self.guest, 'OK'),
            (self.POST_DETAIL_URL, self.guest, 'OK'),
            (PROFILE_URL, self.guest, 'OK'),
            (CREATE_URL, self.guest, 'FOUND'),
            (self.EDIT_URL, self.guest, 'FOUND'),
            (CREATE_URL, self.author, 'OK'),
            (self.EDIT_URL, self.author, 'OK'),
            (self.EDIT_URL, self.another, 'FOUND'),
            ('/ggwp/', self.guest, 'NOT_FOUND'),
        ]
        for url, client, status in url_data:
            with self.subTest(url=url, client=client, status=status):
                self.assertEqual(
                    client.get(url).status_code, HTTPStatus[status]
                )

    def test_redirects(self):
        url_data = [
            (CREATE_URL, self.guest, REDIRECT_CREATE_URL),
            (self.EDIT_URL, self.guest, self.REDIRECT_EDIT_URL),
            (self.EDIT_URL, self.another, self.POST_DETAIL_URL),
            (FOLLOW_INDEX_URL, self.guest, REDIRECT_FOLLOW_INDEX_URL),
            (FOLLOW_URL, self.guest, REDIRECT_FOLLOW_URL),
            (FOLLOW_URL, self.another, PROFILE_URL),
            (FOLLOW_URL, self.author, PROFILE_URL),
            (UNFOLLOW_URL, self.guest, REDIRECT_UNFOLLOW_URL),
            (UNFOLLOW_URL, self.another, PROFILE_URL),
        ]
        for url, client, redirect_url in url_data:
            with self.subTest(url=url, client=client):
                self.assertRedirects(
                    client.get(url, follow=True),
                    redirect_url,
                )
