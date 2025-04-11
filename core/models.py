from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Кастомная модель пользователя с поддержкой Telegram.
    Наследуемся от AbstractUser для сохранения стандартной аутентификации Django.
    """
    telegram_id = models.BigIntegerField(
        verbose_name='Telegram ID',
        unique=True,
        null=True,
        blank=True,
        help_text='Уникальный идентификатор пользователя в Telegram'
    )
    is_pro = models.BooleanField(
        verbose_name='Pro-статус',
        default=False,
        help_text='Доступ к премиум-функциям'
    )
    username = models.CharField(
        verbose_name='Логин',
        max_length=150,
        unique=True,
        null=True,
        blank=True,
        help_text='Не обязательно для Telegram-пользователей'
    )
    first_name = models.CharField(
        verbose_name='Имя пользователя',
        max_length=255
    )
    USERNAME_FIELD = 'telegram_id' #Основной идентефикатор
    REQUIRED_FIELDS = [] #Убираем обязательное требование username

    def __str__(self):
        '''Строковое представление пользователя'''
        if self.telegram_id:
            return f'TG-пользователь #{self.telegram_id}'
        return f"Пользователь {self.username}"