# Foodgram

**Адрес сайта:**  
[https://nikita.hopto.org](https://nikita.hopto.org)  
[http://158.160.202.212](http://158.160.202.212)

**Автор:** Филин Никита

---

## Описание

Foodgram — это сайт, где пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное, подписываться на авторов и формировать список покупок с автоматическим суммированием ингредиентов для выбранных блюд.

### Функционал пользователей:
- Публикация рецептов с фото, тегами и ингредиентами
- Фильтрация рецептов по тегам и авторам
- Добавление рецептов в избранное
- Формирование списка покупок с выгрузкой в `.txt`
- Подписка на авторов рецептов
- Личный профиль с аватаром

---

## Как установить и развернуть

### Локальный запуск

1. Клонируй репозиторий:
```bash
git clone https://github.com/click002/foodgram
cd foodgram
```

2. Создай и активируй виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
# или venv\Scripts\activate  # для Windows
```

3. Установи зависимости:
```bash
pip install -r requirements.txt
```

4. Создай файл `.env` в корне проекта:
```env
SECRET_KEY=твой_секретный_ключ
DEBUG=True
USE_SQLITE=False
POSTGRES_DB=foodgram
POSTGRES_USER=food_user
POSTGRES_PASSWORD=foodgram_password
DB_HOST=db
DB_PORT=5432
ALLOWED_HOSTS=127.0.0.1,localhost
```

5. Запусти контейнеры:
```bash
cd infra
docker-compose up -d
```

6. Выполни миграции и собери статику:
```bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py collectstatic --noinput
```

7. Создай суперпользователя:
```bash
docker-compose exec backend python manage.py createsuperuser
```

8. Загрузи ингредиенты:
```bash
docker-compose exec backend python manage.py shell -c "
import json
with open('/app/data/ingredients.json') as f:
    data = json.load(f)
from recipes.models import Ingredient
for item in data:
    Ingredient.objects.get_or_create(
        name=item['name'],
        measurement_unit=item['measurement_unit']
    )
"
```

9. Открой в браузере: `http://localhost`

---

### Деплой на сервер

1. Установи Docker на сервер

2. Скопируй на сервер файлы:
- `docker-compose.production.yml`
- `nginx.conf`
- `.env`

3. Создай `.env` на сервере с настройками:
```env
SECRET_KEY=твой_секретный_ключ
DEBUG=False
USE_SQLITE=False
POSTGRES_DB=foodgram
POSTGRES_USER=food_user
POSTGRES_PASSWORD=foodgram_password
DB_HOST=db
DB_PORT=5432
ALLOWED_HOSTS=158.160.202.212,nikita.hopto.org
```

4. Запусти контейнеры:
```bash
sudo docker-compose -f docker-compose.production.yml up -d
sudo docker-compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker-compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput
```

5. Настрой HTTPS (если есть домен):
```bash
sudo certbot --nginx -d nikita.hopto.org
```

---

### CI/CD

Проект настроен на автоматический деплой через **GitHub Actions** при пуше в ветку `main`.

Для работы CI/CD нужно добавить секреты в GitHub:
- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`
- `HOST`
- `USER`
- `SSH_KEY`
### Для получения уведомлений в Telegram добавьте в Secrets две переменные:

TELEGRAM_TO — ID вашего Telegram-аккаунта. Узнать ID можно у бота @userinfobot.
TELEGRAM_TOKEN — токен вашего бота. Получить токен можно у бота @BotFather.
⚠️ Важно: чтобы бот мог отправлять вам сообщения, сначала напишите ему что-нибудь сами. Ботам запрещено первыми начинать разговор.


---

## Технологии

- Python 3.10
- Django 5.1.4
- Django REST Framework
- PostgreSQL 15
- Nginx 1.25
- Gunicorn
- Docker
- GitHub Actions (CI/CD)

---

## Данные для входа в админ-зону

```
Username: admin
Email: admin@yandex.ru
Password: Admin55555#
```

Админка: `https://nikita.hopto.org/admin/`

---

**Ссылка на репозиторий:** [https://github.com/click002/foodgram](https://github.com/click002/foodgram)
