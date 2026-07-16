# Foodgram

[![Workflow Status](https://github.com/click002/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/click002/foodgram/actions/workflows/main.yml)

**Сайт:**  
https://nikita.hopto.org  
http://158.160.202.212

**Документация API:**  
https://nikita.hopto.org/api/docs/

**Автор:** Филин Никита

---

# Описание

**Foodgram** — это сервис для публикации рецептов. Пользователи могут создавать собственные рецепты, подписываться на других авторов, добавлять понравившиеся рецепты в избранное и формировать список покупок, в котором автоматически суммируется количество одинаковых ингредиентов.

## Возможности

- Регистрация и авторизация пользователей
- Создание, редактирование и удаление рецептов
- Загрузка изображений блюд
- Добавление рецептов в избранное
- Подписка на авторов
- Формирование списка покупок
- Скачивание списка покупок в формате `.txt`
- Фильтрация рецептов по тегам
- Работа через REST API
- Административная панель Django

---

# Технологии

- Python 3.10
- Django 5.1.4
- Django REST Framework
- PostgreSQL 15
- Gunicorn
- Nginx
- Docker
- Docker Compose
- GitHub Actions (CI/CD)

---

# Структура проекта

```text
foodgram/
├── backend/
├── frontend/
├── infra/
├── data/
├── docs/
├── .github/
├── docker-compose.production.yml
├── README.md
└── requirements.txt
```

---

# Локальный запуск

## 1. Клонирование репозитория

```bash
git clone https://github.com/click002/foodgram.git
cd foodgram
```

---

## 2. Создание виртуального окружения

Linux / macOS

```bash
python -m venv venv
source venv/bin/activate
```

Windows

```powershell
python -m venv venv
venv\Scripts\activate
```

---

## 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

---

## 4. Создание файла `.env`

Создайте файл `.env` в корне проекта.

```env
SECRET_KEY=your_secret_key
DEBUG=True
USE_SQLITE=False

POSTGRES_DB=foodgram
POSTGRES_USER=food_user
POSTGRES_PASSWORD=foodgram_password

DB_HOST=db
DB_PORT=5432

ALLOWED_HOSTS=127.0.0.1,localhost
```

---

## 5. Запуск Docker

Перейдите в каталог `infra`.

```bash
cd infra
docker-compose up -d
```

---

## 6. Выполнение миграций

```bash
docker-compose exec backend python manage.py migrate
```

---

## 7. Сбор статических файлов

```bash
docker-compose exec backend python manage.py collectstatic --noinput
```

---

## 8. Создание суперпользователя

```bash
docker-compose exec backend python manage.py createsuperuser
```

---

## 9. Загрузка ингредиентов

```bash
docker-compose exec backend python manage.py shell -c "
import json
from recipes.models import Ingredient

with open('/app/data/ingredients.json') as f:
    ingredients = json.load(f)

for item in ingredients:
    Ingredient.objects.get_or_create(
        name=item['name'],
        measurement_unit=item['measurement_unit']
    )
"
```

---

## 10. Открыть проект

Главная страница

```
http://localhost
```

Документация API

```
http://localhost/api/docs/
```

Административная панель

```
http://localhost/admin/
```

---

# Деплой на сервер

## 1. Установить Docker и Docker Compose

Например, на Ubuntu:

```bash
sudo apt update
sudo apt install docker.io docker-compose-plugin -y
sudo systemctl enable docker
```

---

## 2. Скопировать на сервер

Необходимо перенести следующие файлы:

- `docker-compose.production.yml`
- `nginx.conf`
- `.env`

---

## 3. Создать `.env`

```env
SECRET_KEY=your_secret_key

DEBUG=False
USE_SQLITE=False

POSTGRES_DB=foodgram
POSTGRES_USER=food_user
POSTGRES_PASSWORD=foodgram_password

DB_HOST=db
DB_PORT=5432

ALLOWED_HOSTS=158.160.202.212,nikita.hopto.org
```

---

## 4. Запустить контейнеры

```bash
sudo docker-compose -f docker-compose.production.yml up -d
```

---

## 5. Выполнить миграции

```bash
sudo docker-compose -f docker-compose.production.yml exec backend python manage.py migrate
```

---

## 6. Собрать статику

```bash
sudo docker-compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput
```

---

## 7. Настроить HTTPS

Если используется доменное имя:

```bash
sudo certbot --nginx -d nikita.hopto.org
```

---

# CI/CD

Проект автоматически проходит сборку и деплой при отправке изменений в ветку **main** с помощью **GitHub Actions**.

Для работы необходимо добавить в **GitHub Secrets** следующие переменные:

```text
DOCKER_USERNAME
DOCKER_PASSWORD

HOST
USER
SSH_KEY

TELEGRAM_TO
TELEGRAM_TOKEN
```

### Telegram

Для получения уведомлений:

- создайте бота через **@BotFather**;
- получите токен;
- узнайте свой Telegram ID через **@userinfobot**;
- отправьте сообщение своему боту (Telegram запрещает ботам писать первыми).

---

# Данные администратора

```text
Username: admin
Email: admin@yandex.ru
Password: Admin55555#
```

Административная панель:

https://nikita.hopto.org/admin/

---

# REST API

Документация доступна по адресу:

Продакшн:

https://nikita.hopto.org/api/docs/

Локально:

```
http://localhost/api/docs/
```

---

# Репозиторий

GitHub:

https://github.com/click002/foodgram

---

# Автор

**Филин Никита**

---

# Что реализовано

- публикация рецептов;
- работа с ингредиентами;
- загрузка изображений;
- избранное;
- подписки;
- список покупок;
- выгрузка списка покупок в TXT;
- REST API;
- Docker-контейнеризация;
- PostgreSQL;
- Gunicorn + Nginx;
- GitHub Actions;
- автоматический деплой;
- HTTPS;
- Swagger/ReDoc документация API.
