# Invoice System

Бэк учётной системы для формирования счетов-фактур по доходным и НДС проводкам на продажи услуг банка

## Стек

- Python 3.12+
- FastAPI
- PostgreSQL 16
- SQLAlchemy 2.0 
- Alembic 
- RabbitMQ 3.13

### 1. Клонировать репозиторий

```bash
git clone https://github.com/danisiomo/invoice-system.git
cd invoice-system
```

### 2. Поднять инфраструктуру
Требуется установленный Docker Desktop

``` bash
docker-compose up -d
```
Это поднимет:

PostgreSQL на порту 5432
RabbitMQ на порту 5672 (UI: http://localhost:15672, логин: rabbit_user / rabbit_pass)

### 3. Установить зависимости

```bash
cd backend
python -m venv venv
```
Активировать виртуальное окружение:

Windows: venv\Scripts\activate

Mac/Linux: source venv/bin/activate

```bash
pip install -r requirements.txt
```

### 4. Применить миграции
```bash
alembic upgrade head
```

### 5. Запустить сервер

```bash
uvicorn app.main:app --reload --log-level debug
```

Swagger документация доступна по адресу http://localhost:8000/docs

### 6. Примеры запросов

Регистрация

```bash
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "user",
  "password": "password123",
  "full_name": "Иванов Иван"
}
```

Авторизация

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user",
  "password": "password123"
}
```

Ответ:

```json
{
  "access_token": "eyJhbGciOiJIUzI1...",
  "token_type": "bearer"
}
```

Получение профиля

```bash
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```
