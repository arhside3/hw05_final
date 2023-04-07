import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post, User

CREATE_URL = reverse('posts:create_post')
USERNAME = 'post_author'
PROFILE_URL = reverse('posts:profile', kwargs={'username': USERNAME})
LOGIN_URL = reverse('users:login')
REDIRECT_URL = f'{LOGIN_URL}?next={CREATE_URL}'

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_author = User.objects.create_user(
            username=USERNAME,
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
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', kwargs={'pk': cls.post.pk}
        )
        cls.UPDATE_URL = reverse('posts:update_post', args=[cls.post.pk])
        cls.CREATE_COMMENT_URL = reverse(
            'posts:add_comment', kwargs={'pk': cls.post.pk}
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.nonauthorized_user = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(self.post_author)

    def test_authorized_user_create_post(self):
        Post.objects.all().delete()
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
        self.assertEqual(post.image.name, self.post.image.name)

    def test_authorized_user_edit_post(self):
        old_author = self.post.author
        form_data = {
            'text': 'отредактированный текст',
            'group': self.another_group.pk,
        }
        response = self.authorized_user.post(
            self.UPDATE_URL,
            data=form_data,
            follow=True,
        )
        self.post.refresh_from_db()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(self.post.text, form_data['text'])
        self.assertEqual(self.post.author, old_author)
        self.assertEqual(self.post.group.pk, form_data['group'])
        self.assertEqual(
            self.authorized_user.get(self.POST_DETAIL_URL).status_code,
            HTTPStatus.OK,
        )
        self.assertRedirects(response, self.POST_DETAIL_URL)

    def test_nonauthorized_user_create_post(self):
        """Проверка создания записи не авторизированным пользователем."""
        Post.objects.all().delete()
        form_data = {
            'text': 'текст',
            'group': self.group.pk,
        }
        response = self.nonauthorized_user.post(
            CREATE_URL,
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, REDIRECT_URL)
        self.assertEqual(Post.objects.count(), 0)

    def test_forms_show_correct(self):
        """Проверка корректности формы."""
        forms_field = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
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

    def test_create_comment(self):
        Comment.objects.all().delete()
        form_data = {
            'text': 'Новый комментарий',
        }
        response = self.authorized_user.post(
            self.CREATE_COMMENT_URL, data=form_data, follow=True
        )
        comment = Comment.objects.first()
        self.assertRedirects(response, self.POST_DETAIL_URL)
        self.assertEqual(comment.text, form_data.get('text'))
        self.assertEqual(len(response.context.get('comments')), 1)
        self.assertEqual(
            response.context.get('comments')[0].text, form_data.get('text')
        )
