from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()
TEXT_SIZE = 15


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
        'Картинка',
        upload_to='posts/',
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
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'

    def __str__(self) -> str:
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Блогер',
    )

    def __str__(self):
        return str(f'{self.user} подписан на {self.author}')
