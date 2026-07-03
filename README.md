# 🐾 Kittygram v2.2 — Cat Family Tree

![Django](https://img.shields.io/badge/Django-3.2-092E20?style=for-the-badge&logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/DRF-3.14-A30000?style=for-the-badge&logo=django&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-Gateway-009639?style=for-the-badge&logo=nginx&logoColor=white)

**Kittygram v2.2** — это расширенная версия платформы для учета котиков, их достижений, приютов и семейных связей. Проект представляет собой REST API на Django REST Framework и позволяет строить семейное древо котов: указывать родителей, детей, предков, потомков и родственные связи внутри базы.

## 🚀 Ключевые особенности

*   **🏢 Система приютов (Shelters)**: Создание и управление карточками приютов.
*   **👥 Управление персоналом (Staff Management)**: Назначение сотрудников с разными ролями (Manager, Volunteer).
*   **🌳 Семейное древо котов (Cat Family Tree)**: Создание связей родитель-ребёнок, просмотр родителей, детей, предков, потомков и родственников кота.
*   **🔐 Role-Based Access Control (RBAC)**: Гибкая система прав доступа. Только персонал приюта может редактировать данные своего заведения.
*   **🛡️ Безопасность**:
    *   Аутентификация через **JWT (JSON Web Tokens)**.
    *   Механизмы **Throttling** (ограничение частоты запросов) для защиты от DDoS и перебора паролей.
*   **📊 Продвинутый API**:
    *   Фильтрация, поиск и сортировка данных.
    *   Пагинация ответов.
    *   Автоматическая документация **Swagger** и **Redoc**.
*   **🐳 Полная контейнеризация**: Готовая конфигурация Docker Compose (Django + Gunicorn + PostgreSQL + Nginx).

## 🛠 Технологический стек

*   **Backend**: Python 3.10, Django 4.2, Django REST Framework.
*   **Auth**: Djoser, SimpleJWT.
*   **Database**: PostgreSQL 13.
*   **Gateway**: Nginx (reverse proxy).
*   **Infrastructure**: Docker, Docker Compose.

## 📦 Запуск проекта

### 1. Клонируйте репозиторий:
```bash
git clone https://github.com/Spoontamer13/Kittygram.git
cd Kittygram
```

### 2. Создайте файл `.env` в корне папки по образцу:
```env
POSTGRES_DB=kittygram
POSTGRES_USER=kittygram_user
POSTGRES_PASSWORD=kittygram_password
DB_HOST=db
DB_PORT=5432
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=127.0.0.1,localhost
```

### 3. Запустите проект через Docker Compose:
```bash
docker compose up -d --build
```

### 4. Выполните миграции и соберите статику:
```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic --no-input
```

### 5. Создайте суперпользователя:
```bash
docker compose exec backend python manage.py createsuperuser
```

Проект будет доступен по адресу: [http://localhost:8000/](http://localhost:8000/)
Документация API: [Swagger](http://localhost:8000/api/docs/swagger/) и [ReDoc](http://localhost:8000/api/docs/redoc/)

## 🌳 API семейного древа котов

Основные endpoints:

```text
GET    /api/cat-family-relations/
POST   /api/cat-family-relations/
GET    /api/cat-family-relations/{id}/
PATCH  /api/cat-family-relations/{id}/
DELETE /api/cat-family-relations/{id}/
GET    /api/cats/{id}/family-tree/
GET    /api/cats/{id}/ancestors/
GET    /api/cats/{id}/descendants/
```

Пример создания связи:

```json
{
  "parent": 1,
  "child": 3,
  "relation_type": "mother",
  "note": "Основная линия семейного древа"
}
```

Валидации:

*   кот не может быть родителем самого себя;
*   родитель должен быть старше ребёнка;
*   связь не должна создавать цикл в семейном древе;
*   пара `parent + child` не может повторяться.

## 👨‍💻 Автор
**Панфило Ярослав Валерьевич**
Курсовой проект по разработке масштабируемых веб-сервисов.
