from django.db import models

from posts.models import User


class TextModel(models.Model):
    text = models.TextField(verbose_name='текст')

    class Meta:
        abstract = True


class AuthorModel(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='автор',
    )

    class Meta:
        abstract = True
