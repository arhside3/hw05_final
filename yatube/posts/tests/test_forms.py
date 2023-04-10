import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post, User
from yatube.settings import UPLOAD_TO

CREATE_URL = reverse('posts:create_post')
USERNAME = 'post_author'
ANOTHER_USERNAME = 'another user'
PROFILE_URL = reverse('posts:profile', args={USERNAME})
LOGIN_URL = reverse('users:login')
REDIRECT_URL = f'{LOGIN_URL}?next={CREATE_URL}'
IMAGE_FORM_DATA = '{}{}'

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
small_gif = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_author = User.objects.create_user(
            username=USERNAME,
        )
        cls.another_user = User.objects.create_user(
            username=ANOTHER_USERNAME,
        )
        cls.group = Group.objects.create(
            title='заголовок',
            slug='slug',
            description='описание',
        )
        cls.post = Post.objects.create(
            author=cls.post_author,
            text='текст поста',
            group=cls.group,
        )
        cls.another_group = Group.objects.create(
            title='test-заголовок',
            slug='test-slug',
            description='test-описание',
        )
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args={cls.post.pk})
        cls.UPDATE_URL = reverse('posts:update_post', args=[cls.post.pk])
        cls.REDIRECT_UPDATE_URL = f'{LOGIN_URL}?next={cls.UPDATE_URL}'
        cls.CREATE_COMMENT_URL = reverse(
            'posts:add_comment', args={cls.post.pk}
        )
        cls.REDIRECT_CREATE_COMMENT_URL = (
            f'{LOGIN_URL}?next={cls.CREATE_COMMENT_URL}'
        )
        cls.nonauthorized_user = Client()
        cls.authorized_user = Client()
        cls.authorized_user.force_login(cls.post_author)
        cls.another_client = Client()
        cls.another_client.force_login(cls.another_user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_authorized_user_create_post(self):
        Post.objects.all().delete()
        uploaded = SimpleUploadedFile(
            name='small.gif', content=small_gif, content_type='image/gif'
        )
        form_data = {
            'text': 'новый текст поста',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_user.post(
            CREATE_URL,
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            PROFILE_URL,
        )
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.post_author)
        self.assertEqual(self.post.group.pk, form_data['group'])
        self.assertEqual(
            post.image, IMAGE_FORM_DATA.format(UPLOAD_TO, form_data['image'])
        )

    def test_nonauthorized_user_create_post(self):
        """Проверка создания записи не авторизированным пользователем."""
        Post.objects.all().delete()
        uploaded = SimpleUploadedFile(
            name='small.gif', content=small_gif, content_type='image/gif'
        )
        form_data = {
            'text': 'текст',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.nonauthorized_user.post(
            CREATE_URL,
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, REDIRECT_URL)
        self.assertEqual(Post.objects.count(), 0)

    def test_authorized_user_edit_post(self):
        old_author = self.post.author
        uploaded = SimpleUploadedFile(
            name='smaller.gif', content=small_gif, content_type='image/gif'
        )
        form_data = {
            'text': 'отредактированный текст',
            'group': self.another_group.pk,
            'image': uploaded,
        }
        response = self.authorized_user.post(
            self.UPDATE_URL,
            data=form_data,
            follow=True,
        )
        post = Post.objects.get(pk=self.post.pk)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, old_author)
        self.assertEqual(post.group.pk, form_data['group'])
        self.assertEqual(post.image, f'{UPLOAD_TO}smaller.gif')
        self.assertEqual(
            self.authorized_user.get(self.POST_DETAIL_URL).status_code,
            HTTPStatus.OK,
        )
        self.assertRedirects(response, self.POST_DETAIL_URL)

    def test_nonauthorized_user_edit_post(self):
        uploaded = SimpleUploadedFile(
            name='smaller.gif', content=small_gif, content_type='image/gif'
        )
        form_data = {
            'text': 'отредактированный текст',
            'group': self.another_group.pk,
            'image': uploaded,
        }
        clients = [
            self.nonauthorized_user,
            self.another_client,
        ]
        for client in clients:
            response = client.post(
                self.UPDATE_URL,
                data=form_data,
                follow=True,
            )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), 1)

    def test_forms_show_correct(self):
        """Проверка корректности формы."""
        forms_field = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        urls = [CREATE_URL, self.UPDATE_URL]

        for url in urls:
            form = self.authorized_user.get(url).context['form']
            for field, instance in forms_field.items():
                with self.subTest(url=url, field=field):
                    self.assertIsInstance(
                        form.fields[field],
                        instance,
                    )

    def test_authorized_create_comment(self):
        Comment.objects.all().delete()
        form_data = {
            'text': 'Новый комментарий',
        }
        response = self.authorized_user.post(
            self.CREATE_COMMENT_URL, data=form_data, follow=True
        )
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.first()
        self.assertRedirects(response, self.POST_DETAIL_URL)
        self.assertEqual(comment.text, form_data.get('text'))
        self.assertEqual(comment.author, self.post_author)
        self.assertEqual(comment.post, self.post)

    def test_nonauthorized_create_comment(self):
        Comment.objects.all().delete()
        form_data = {
            'text': 'Новый комментарий',
        }
        response = self.nonauthorized_user.post(
            self.CREATE_COMMENT_URL, data=form_data, follow=True
        )
        self.assertRedirects(response, self.REDIRECT_CREATE_COMMENT_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), 0)
