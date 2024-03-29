# Generated by Django 2.2.16 on 2023-04-10 13:25

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('posts', '0006_auto_20230406_2104'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={
                'ordering': ('-created',),
                'verbose_name': 'комментарий',
                'verbose_name_plural': 'комментарии',
            },
        ),
        migrations.AlterModelOptions(
            name='follow',
            options={
                'verbose_name': 'подписка',
                'verbose_name_plural': 'подписки',
            },
        ),
        migrations.AlterField(
            model_name='follow',
            name='author',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='following',
                to=settings.AUTH_USER_MODEL,
                verbose_name='блогер',
            ),
        ),
        migrations.AlterField(
            model_name='follow',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='follower',
                to=settings.AUTH_USER_MODEL,
                verbose_name='подписчик',
            ),
        ),
    ]
