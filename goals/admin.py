from django.contrib import admin

from .models import Goal

@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    '''Управление целями пользователей'''
    # Отображение в списке
    list_display = (
        'title',
        'user',
        'deadline',
        'is_completed'
    )
    # Фильтры
    list_filter = (
        'category',
        'is_completed'
    )
    # Поиск
    search_fields = (
        'title',
        'user__telegram_id'
    )
    # Иерархия по датам
    date_hierarchy = 'deadline'

    @admin.display(description='Дата завершения')
    def completed_date(self):
        return self.get_completed_date()
    
    @admin.display(description='Срок выполнения')
    def deadline_date(self, obj):
        return obj.deadline.strftime('%d.%m.%Y') if obj.deadline else "Не установлен"
