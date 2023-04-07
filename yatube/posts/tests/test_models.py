from django.test import TestCase

from posts.models import TEXT_SIZE, Comment, Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='заголовок',
            slug='номер группы',
            description='описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='текст',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(self.post.text[:TEXT_SIZE], str(self.post))


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='заголовок',
            slug='номер группы',
            description='описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='текст',
        )

    def test_group_str(self):
        """Проверка __str__ у group."""
        self.assertEqual(self.group.title, str(self.group))


class CommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='текст поста',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='комментарий',
        )

    def test_comment_model_have_correct_object_names(self):
        self.assertEqual(self.comment.text, str(self.comment))
