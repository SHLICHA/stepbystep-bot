from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone

User = get_user_model()

class Goal(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='goals'
    )
    title = models.CharField(
        verbose_name='Название',
        max_length=200
    )
    category = models.CharField(
        verbose_name='Категория',
        max_length=50)
    steps = models.JSONField(
        verbose_name='Шаги от ИИ',
        default=list
    )
    deadline = models.DateField(
        verbose_name='Срок выполнения',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )
    is_completed = models.BooleanField(
        verbose_name="Статус выполнения цели",
        default=False
    )
    completed_at = models.DateTimeField(
        verbose_name='Дата завершения',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Цель"
        verbose_name_plural = "Цели"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} (до {self.deadline})" if self.deadline else self.title
    
    def save(self, *args, **kwargs):
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)

    def get_completed_date(self):
        return self.completed_at.strftime('%d.%m.%Y %H:%M') if self.completed_at else "не указана"
    
    def get_deadline_date(self):
        return self.deadline.strftime('%d.%m.%Y') if self.deadline else "не установлен"
