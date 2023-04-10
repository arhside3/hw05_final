from django.contrib.auth import get_user_model
from django.db import models

from yatube.settings import UPLOAD_TO

User = get_user_model()
TEXT_SIZE = 15
MY_FOLLOW = '{} подписан на {}'


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name='заголовок')
    slug = models.SlugField(
        max_length=30,
        unique=True,
        verbose_name='читаемая часть URL',
    )
    description = models.TextField(verbose_name='описание')

    class Meta:
        verbose_name = 'группа статей '
        verbose_name_plural = 'группы статей'
        ordering = ('-title',)

    def __str__(self) -> str:
        return self.title[:TEXT_SIZE]


class Post(models.Model):
    text = models.TextField(verbose_name='текст')
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата публикации',
        db_index=True,
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='группа',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name='автор',
    )
    image = models.ImageField(
        verbose_name='картинка',
        upload_to=UPLOAD_TO,
        blank=True,
    )

    class Meta:
        ordering = ('-pub_date',)
        default_related_name = 'posts'
        verbose_name = 'статья'
        verbose_name_plural = 'статьи'

    def __str__(self) -> str:
        return self.text[:TEXT_SIZE]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='пост',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='автор',
    )
    text = models.TextField(verbose_name='текст')
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата публикации',
        db_index=True,
    )

    class Meta:
        ordering = ('-created',)
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'

    def __str__(self) -> str:
        return self.text[:TEXT_SIZE]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='блогер',
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'подписки'
        constraints = [
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='user_author_check',
            ),
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_following'
            ),
        ]

    def __str__(self):
        return MY_FOLLOW.format(self.user.username, self.author.username)
