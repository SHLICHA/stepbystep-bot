db: goal_bot_db
user: bot_user
pass: sun_from_tai_2025

sudo service postgresql start - запуск базы данных
Перенести все пароли и коды в .env
Перестало работать редактирование, цель сохраняется без даты

# StepByStep Bot - Менеджер целей

🤖 Telegram-бот для управления личными целями с функциями:
- Создание целей по категориям
- Установка сроков выполнения
- Просмотр активных и завершенных целей
- Гибкая система напоминаний

## Технологии
- Python 3.10+
- Django 4.2+
- Aiogram 3.0+
- PostgreSQL (опционально)

## Установка

1. Клонировать репозиторий:
```bash
git clone https://github.com/ваш-username/stepbystep-bot.git