from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    '''Кастомная конфигурация для отображения пользователя в админке'''
    fieldsets = (
        (None, {
            'fields': (
                'username', 'password'
            )
        }), 
        ('Персональная информация:', {
            'fields': (
                'first_name', 'last_name', 'email'
            )
        }),
        ('Telegram Info', {
            'fields':
            ('telegram_id',)
        }),
        ('Права:', {
            'fields': (
                'is_pro', 
                'is_active', 
                'is_staff',
                'is_superuser' 
            ),
            'description': 'Внимание! Давайте права осторожно'
        })
    )
    list_display = (
        'username',
        'telegram_id',
        'is_pro',
        'is_staff'
    )
    list_filter = (
        'is_pro',
        'is_staff',
        'is_superuser'
    )