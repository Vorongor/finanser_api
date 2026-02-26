# Sart rebuild Finanser into REST API and React application
```
Моделі та БД
Міграція моделей: Перепиши моделі Django на SQLAlchemy або Tortoise-ORM.

Pydantic схеми: Створи схеми для валідації вхідних даних та серіалізації вихідних (заміна Django Forms та Serializers).

Міграції: Налаштуй Alembic (аналог makemigrations/migrate).

Логіка та Auth
Authentication: Заміни сесії Django на JWT-токени (OAuth2). Це стандарт для розділеного фронту і беку.

Business Logic: Винеси "товсту логіку" з Django Views у окремі сервіси (Service Layer) у FastAPI.

Middleware: Налаштуй CORS (Cross-Origin Resource Sharing), щоб твій Next.js міг робити запити до API.

Ендпоінти
RESTful Routes: Перепиши всі URL-адреси. Замість рендерингу шаблонів (render(request, 'index.html')), повертай лише JSON.

Dependency Injection: Використовуй систему залежностей FastAPI для підключення БД до роутів.
```

## Structure:
```
finanser_api/
├── src/
│   ├── alembic/                # Alembic (створиться автоматично)
│   │   ├── vesions/            # Migrations files 
│   │   └── env.py              # Migrator config 
│   ├── api/                    # Ендпоінти (v1, v2...)
│   │   ├── api.py     # Migrations files 
│   ├── config/                 # Конфігурація (config.py, security.py)
│   │   ├── dependencies.py     # Migrations files 
│   │   └── settings.py         # Migrator config 
│   ├── models/         # SQLAlchemy моделі
│   ├── schemas/        # Pydantic схеми
│   ├── db/             # Сесія БД та базовий клас
│   └── main.py         # Точка входу
├── alembic.ini
├── pyproject.toml      # setups uv та ruff
└── .env                # variables
```