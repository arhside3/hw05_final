from django.test import TestCase

from posts.models import (
    MY_FOLLOW,
    TEXT_SIZE,
    Comment,
    Follow,
    Group,
    Post,
    User,
)


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='блогер')
        cls.user = User.objects.create_user(username='подписчик')
        cls.follow = Follow.objects.create(user=cls.user, author=cls.author)
        cls.group = Group.objects.create(
            title='заголовок',
            slug='номер группы',
            description='описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='текст',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='комментарий',
        )

    def test_model_str(self):
        models_str = [
            (self.post, self.post.text[:TEXT_SIZE]),
            (self.group, self.group.title),
            (self.comment, self.comment.text),
            (
                self.follow,
                MY_FOLLOW.format(self.user.username, self.author.username),
            ),
        ]

        for model, text in models_str:
            with self.subTest(model=model, text=text):
                self.assertEqual(str(model), text)
