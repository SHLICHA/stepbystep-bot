# Generated by Django 5.2 on 2025-04-10 07:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_user_first_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='username',
            field=models.CharField(blank=True, help_text='Не обязательно для Telegram-пользователей', max_length=150, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='telegram_id',
            field=models.BigIntegerField(blank=True, null=True, unique=True),
        ),
    ]
