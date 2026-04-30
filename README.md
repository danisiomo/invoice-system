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
git clone <url>
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
Bash

alembic upgrade head
### 5. Запустить сервер

```bash
uvicorn app.main:app --reload --log-level debug
```
Сервер доступен по адресу http://localhost:8000.

API документация
После запуска сервера:

Swagger: http://localhost:8000/docs

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

## Эндпоинты

| Метод | URL | Описание | Авторизация |
|-------|-----|----------|-------------|
| GET | `/health` | Проверка работоспособности | Нет |
| POST | `/api/v1/auth/register` | Регистрация пользователя | Нет |
| POST | `/api/v1/auth/login` | Авторизация, получение JWT | Нет |
| GET | `/api/v1/auth/me` | Текущий пользователь | Bearer token |
| POST | `/api/v1/data-load/standard` | Стандартная загрузка из АБС | Bearer token |
| POST | `/api/v1/data-load/by-date` | Загрузка за конкретный день | Bearer token |
| POST | `/api/v1/data-load/by-account` | Загрузка по счёту | Bearer token |
| GET | `/api/v1/data-load/log` | Журнал загрузок | Bearer token |
| GET | `/api/v1/data-load/log/last` | Последняя успешная загрузка | Bearer token |
| GET | `/api/v1/data-load/log/{id}` | Статус загрузки по ID | Bearer token |
| GET | `/api/v1/references/regional-centers` | Список региональных центров | Bearer token |
| POST | `/api/v1/references/regional-centers` | Создать региональный центр | Bearer token |
| GET | `/api/v1/references/branches` | Список отделений | Bearer token |
| POST | `/api/v1/references/branches` | Создать отделение | Bearer token |
| GET | `/api/v1/references/vat-accounts` | Список счетов НДС | Bearer token |
| POST | `/api/v1/references/vat-accounts` | Добавить счёт НДС | Bearer token |
| GET | `/api/v1/references/vat-accounts/{id}` | Получить счёт НДС по ID | Bearer token |
| PATCH | `/api/v1/references/vat-accounts/{id}` | Редактировать счёт НДС | Bearer token |
| DELETE | `/api/v1/references/vat-accounts/{id}` | Удалить счёт НДС | Bearer token |
| GET | `/api/v1/references/income-accounts` | Список счетов доходов | Bearer token |
| POST | `/api/v1/references/income-accounts` | Добавить счёт доходов | Bearer token |
| GET | `/api/v1/references/income-accounts/{id}` | Получить счёт доходов по ID | Bearer token |
| PATCH | `/api/v1/references/income-accounts/{id}` | Редактировать счёт доходов | Bearer token |
| DELETE | `/api/v1/references/income-accounts/{id}` | Удалить счёт доходов | Bearer token |
| GET | `/api/v1/references/responsibles` | Список ответственных | Bearer token |
| POST | `/api/v1/references/responsibles` | Добавить ответственного | Bearer token |
| GET | `/api/v1/references/responsibles/{id}` | Получить ответственного по ID | Bearer token |
| PATCH | `/api/v1/references/responsibles/{id}` | Редактировать ответственного | Bearer token |
| DELETE | `/api/v1/references/responsibles/{id}` | Удалить ответственного | Bearer token |

## Фильтры журнала загрузки

| Параметр | Значения | Описание |
|----------|----------|----------|
| `period` | `hour` / `day` / `week` / `month` / `three_months` | Период фильтрации |
| `status` | `in_progress` / `success` / `error` | Статус загрузки |
| `load_type` | `standard` / `by_date` / `by_account` | Тип загрузки |
| `page` | число от 1 | Номер страницы |
| `page_size` | число от 1 до 100 | Размер страницы |


## Фильтры справочников

| Справочник | Параметры фильтрации |
|------------|---------------------|
| Счета НДС | `regional_center_id`, `branch_id`, `account_number` |
| Счета доходов | `regional_center_id`, `branch_id`, `account_number` |
| Ответственные | `regional_center_id`, `username` |
| Отделения | `regional_center_id` |


## Статусы загрузки

| Статус | Описание                  |
|--------|---------------------------|
| `in_progress` | Загрузка в процессе    |
| `success` | Загрузка завершена успешно |
| `error` | Загрузка завершена с ошибкой |

## Структура БД

| Таблица | Описание                     |
|---------|------------------------------|
| `users` | Пользователи системы         |
| `roles` | Роли                         |
| `user_roles` | Связь пользователей и ролей  |
| `regional_centers` | Региональные центры          |
| `branches` | Отделения банка              |
| `vat_accounts` | Счета НДС                    |
| `income_accounts` | Счета доходов |
| `responsibles` | Ответственные по СФ |
| `data_load_logs` | Журнал загрузки из АБС       |
| `invoice_drafts` | Проекты счетов-фактур        |
| `invoices` | Оформленные счета-фактуры    |

## Тестовые данные

Все тестовые пользователи логинятся с паролем `Test12345!`

| Логин | Роли |
|-------|------|
| `admin` | Администратор |
| `buhgalter` | Бухгалтер |
| `superadmin` | Администратор + Бухгалтер |
| `factoring1` | Сотрудник факторинга |
| `factoring2` | Сотрудник факторинга |
| `acquiring1` | Сотрудник эквайринга |
| `manager1` | Сотрудник эквайринга |